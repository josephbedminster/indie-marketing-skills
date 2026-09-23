#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyjwt", "cryptography", "requests"]
# ///
"""Read-only CLI for the Apple Search Ads Campaign Management API v5.

Run with uv (deps resolved from the header above, no venv to maintain):
  ./report.py status     or     uv run --script report.py status
Configuration from environment variables; any variable not set is read from the
first `.env.local` then `.env` found walking up from the current working directory:
  APPLE_ADS_ORG_ID             org id (X-AP-Context header)
  APPLE_ADS_CLIENT_ID          client id, SEARCHADS-prefixed (= teamId)
  APPLE_ADS_KEY_ID             key id registered with Apple
  APPLE_ADS_PRIVATE_KEY_PATH   path to the EC P-256 private key (.pem); relative = relative to cwd
  APPLE_ADS_TIMEZONE           report timezone, default ORTZ (the org's timezone)
Auth: JWT ES256 signed with the private key, exchanged for a 1-hour OAuth token kept
in memory only (never written to disk, never printed).

Commands (all read-only, nothing here changes a campaign):
  auth                                  check that the key still yields a token, show ACL
  status                                campaigns: status, serving, reasons, budget, countries, supply
  report [--since --until] [--daily]    per-campaign impr / taps / installs / spend / CPT / CPI
  adgroups CAMPAIGN                     ad groups: status, serving, default bid, search match
  keywords CAMPAIGN [--since --until] [--all]  keyword report (text, match, bid); --all adds 0-impression ones
  terms CAMPAIGN [--since --until]      search terms report (what users actually typed)
  countries [--since --until]           per-country totals across campaigns
  negatives CAMPAIGN                    campaign-level negative keywords
CAMPAIGN = campaign id, or a case-insensitive substring of its name.
Columns: inst = totalInstalls (tap + view-through), tapI = tapInstalls, CPI = spend / inst,
TTR = taps / impressions, CR = inst / taps. Dates are YYYY-MM-DD in the report timezone.
Default range: last 7 days up to yesterday.

For writes (after the user's explicit yes), `call()` can be imported from this module so the
token stays in memory: see references/api-notes.md.
"""
import argparse, datetime, json, os, sys, time

import jwt
import requests

BASE = 'https://api.searchads.apple.com/api/v5'  # Apple Ads Campaign Management API v5
_ENV_LOADED = False
_TOKEN = None


def load_env():
    """Fill os.environ with APPLE_ADS_* keys missing from it, from .env.local / .env walking up from cwd."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    d = os.path.abspath(os.getcwd())
    while True:
        for name in ('.env.local', '.env'):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                try:
                    lines = open(p, encoding='utf-8').read().splitlines()
                except OSError:
                    continue
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    if line.startswith('export '):
                        line = line[7:]
                    k, v = line.split('=', 1)
                    k = k.strip()
                    if k.startswith('APPLE_ADS_') and k not in os.environ:
                        os.environ[k] = v.strip().strip('"\'')
        parent = os.path.dirname(d)
        if parent == d:
            return
        d = parent


def env(name, default=None):
    load_env()
    v = os.environ.get(name) or default
    if v is None:
        sys.exit(f'{name} is not set (environment, .env.local or .env). See references/api-notes.md > Auth.')
    return v


def org_id():
    return env('APPLE_ADS_ORG_ID')


def tz():
    return env('APPLE_ADS_TIMEZONE', 'ORTZ')


def token():
    global _TOKEN
    if _TOKEN:
        return _TOKEN
    client_id, key_id = env('APPLE_ADS_CLIENT_ID'), env('APPLE_ADS_KEY_ID')
    key_path = os.path.abspath(os.path.expanduser(env('APPLE_ADS_PRIVATE_KEY_PATH')))
    if not os.path.isfile(key_path):
        sys.exit(f'private key file not found at APPLE_ADS_PRIVATE_KEY_PATH ({key_path})')
    key = open(key_path).read()
    now = int(time.time())
    secret = jwt.encode(
        {'sub': client_id, 'iss': client_id, 'aud': 'https://appleid.apple.com',
         'iat': now, 'exp': now + 3600},
        key, algorithm='ES256', headers={'kid': key_id})
    r = requests.post('https://appleid.apple.com/auth/oauth2/token', data={
        'grant_type': 'client_credentials', 'client_id': client_id,
        'client_secret': secret, 'scope': 'searchadsorg'}, timeout=30)
    if r.status_code != 200:
        sys.exit(f'auth failed {r.status_code}: {r.text[:300]}')
    _TOKEN = r.json()['access_token']
    return _TOKEN


def call(method, path, body=None):
    h = {'Authorization': 'Bearer ' + token(), 'X-AP-Context': f'orgId={org_id()}',
         'Content-Type': 'application/json'}
    r = requests.request(method, BASE + path, headers=h, json=body, timeout=60)
    try:
        d = r.json()
    except ValueError:
        sys.exit(f'{method} {path} -> {r.status_code} {r.text[:300]}')
    if r.status_code >= 300 or d.get('error') or d.get('errors'):
        sys.exit(f'{method} {path} -> {r.status_code} {json.dumps(d)[:600]}')
    return d.get('data')


def get(path):
    return call('GET', path)


def post(path, body):
    # POST is used by this CLI only for /reports and /…/find, which are read-only.
    return call('POST', path, body)


def campaigns():
    return get('/campaigns?limit=200') or []


def resolve(q):
    cs = campaigns()
    if q.isdigit():
        for c in cs:
            if str(c['id']) == q:
                return c
    hits = [c for c in cs if q.lower() in c['name'].lower()]
    if len(hits) != 1:
        names = ', '.join(c['name'] for c in hits) or 'none'
        sys.exit(f'"{q}" matches {len(hits)} campaigns: {names}')
    return hits[0]


def dates(a):
    y = datetime.date.today() - datetime.timedelta(days=1)
    until = a.until or y.isoformat()
    since = a.since or (datetime.date.fromisoformat(until) - datetime.timedelta(days=6)).isoformat()
    return since, until


def report_body(since, until, daily=False, group_by=None):
    b = {'startTime': since, 'endTime': until, 'timeZone': tz(),
         'selector': {'orderBy': [{'field': 'impressions', 'sortOrder': 'DESCENDING'}],
                      'pagination': {'offset': 0, 'limit': 1000}},
         'returnRecordsWithNoMetrics': False, 'returnRowTotals': True,
         'returnGrandTotals': not daily}
    if daily:
        b['granularity'] = 'DAILY'
        b['returnRecordsWithNoMetrics'] = True
    if group_by:
        b['groupBy'] = group_by
    return b


def amt(x):
    return float((x or {}).get('amount') or 0)


def metrics(t):
    impr, taps = t.get('impressions', 0), t.get('taps', 0)
    inst = t.get('totalInstalls', 0)  # tap + view-through installs
    tapi = t.get('tapInstalls', 0)
    spend = amt(t.get('localSpend'))
    cpt = spend / taps if taps else 0
    cpi = spend / inst if inst else 0
    ttr = 100 * taps / impr if impr else 0
    cr = 100 * inst / taps if taps else 0
    return impr, taps, inst, tapi, spend, cpt, cpi, ttr, cr


def fmt_row(label, t, width=44):
    impr, taps, inst, tapi, spend, cpt, cpi, ttr, cr = metrics(t)
    return (f'{label[:width]:<{width}} {impr:>7} {taps:>5} {inst:>5} {tapi:>5} {spend:>8.2f} '
            f'{cpt:>6.2f} {cpi:>6.2f} {ttr:>5.1f}% {cr:>5.0f}%')


HEADER = f'{"":<44} {"impr":>7} {"taps":>5} {"inst":>5} {"tapI":>5} {"spend":>8} {"CPT":>6} {"CPI":>6} {"TTR":>6} {"CR":>6}'


def rows_of(d):
    return ((d or {}).get('reportingDataResponse') or {}).get('row') or []


def cmd_auth(a):
    token()
    print('token OK (kept in memory, not printed)')
    for o in get('/acls') or []:
        print(o['orgId'], o['orgName'], o['currency'], o['timeZone'], o['roleNames'])


def cmd_status(a):
    tot, cur = 0.0, ''
    for c in sorted(campaigns(), key=lambda c: c['name']):
        b = amt(c.get('dailyBudgetAmount'))
        cur = (c.get('dailyBudgetAmount') or {}).get('currency', cur)
        if c['status'] == 'ENABLED':
            tot += b
        print(f"{c['id']}  {c['status']:<8} {c.get('displayStatus',''):<8} {b:>5.0f}/day  "
              f"{','.join(c['countriesOrRegions']):<14} {c['supplySources'][0]:<30} {c['name']}"
              + (f"  reasons={c['servingStateReasons']}" if c.get('servingStateReasons') else ''))
    print(f'Total daily budget of ENABLED campaigns: {tot:.0f} {cur}/day (Apple can overspend it by 30-60 % on a given day)')


def cmd_report(a):
    since, until = dates(a)
    d = post('/reports/campaigns', report_body(since, until, daily=a.daily))
    print(f'Campaigns {since} .. {until} ({tz()}), spend in account currency')
    if a.daily:
        for r in rows_of(d):
            print('\n' + r['metadata']['campaignName'])
            print(HEADER)
            for g in r.get('granularity') or []:
                print(fmt_row('  ' + g['date'], g))
        return
    print(HEADER)
    for r in rows_of(d):
        m = r['metadata']
        print(fmt_row(f"{m['campaignName']} [{m['campaignStatus'][:1]}]", r['total']))
    gt = ((d or {}).get('reportingDataResponse') or {}).get('grandTotals')
    if gt:
        print(fmt_row('TOTAL', gt['total']))


def cmd_adgroups(a):
    c = resolve(a.campaign)
    for g in get(f"/campaigns/{c['id']}/adgroups?limit=200") or []:
        print(f"{g['id']}  {g['status']:<8} {g.get('servingStatus',''):<12} "
              f"bid {amt(g.get('defaultBidAmount')):.2f}  searchMatch={g.get('automatedKeywordsOptIn')}  "
              f"{g['name']}" + (f"  reasons={g['servingStateReasons']}" if g.get('servingStateReasons') else ''))


def cmd_keywords(a):
    c = resolve(a.campaign)
    since, until = dates(a)
    body = report_body(since, until)
    body['returnRecordsWithNoMetrics'] = a.all  # --all: keywords with 0 impression too
    d = post(f"/reports/campaigns/{c['id']}/keywords", body)
    print(f"{c['name']}: keywords {since} .. {until}")
    print(HEADER + '    bid')
    for r in rows_of(d):
        m = r['metadata']
        lab = f"{m.get('keyword')} [{(m.get('matchType') or '')[:1]}] {(m.get('keywordStatus') or '')[:1]}"
        print(fmt_row(lab, r['total']) + f"  {amt(m.get('bidAmount')):.2f}")


def cmd_terms(a):
    c = resolve(a.campaign)
    since, until = dates(a)
    d = post(f"/reports/campaigns/{c['id']}/searchterms", report_body(since, until))
    print(f"{c['name']}: search terms {since} .. {until}")
    print(HEADER)
    for r in rows_of(d):
        m = r['metadata']
        lab = f"{m.get('searchTermText') or '(low volume, hidden by Apple)'} <{m.get('searchTermSource','')}>"
        print(fmt_row(lab, r['total']))


def cmd_countries(a):
    since, until = dates(a)
    d = post('/reports/campaigns', report_body(since, until, group_by=['countryOrRegion']))
    agg = {}
    for r in rows_of(d):
        cc = r['metadata'].get('countryOrRegion')
        t = agg.setdefault(cc, {'impressions': 0, 'taps': 0, 'totalInstalls': 0, 'tapInstalls': 0, 'localSpend': {'amount': 0}})
        for k in ('impressions', 'taps', 'totalInstalls', 'tapInstalls'):
            t[k] += r['total'].get(k, 0)
        t['localSpend']['amount'] = amt(t['localSpend']) + amt(r['total'].get('localSpend'))
    print(f'Countries {since} .. {until}')
    print(HEADER)
    for cc, t in sorted(agg.items(), key=lambda kv: -amt(kv[1]['localSpend'])):
        print(fmt_row(str(cc), t))


def cmd_negatives(a):
    c = resolve(a.campaign)
    ks = get(f"/campaigns/{c['id']}/negativekeywords?limit=1000") or []
    print(f"{c['name']}: {len(ks)} negative keywords")
    for k in ks:
        print(f"  {k['text']} [{k['matchType']}] {k.get('status','')}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest='cmd', required=True)

    def rng(s):
        s.add_argument('--since')
        s.add_argument('--until')
        return s

    sp.add_parser('auth')
    sp.add_parser('status')
    rng(sp.add_parser('report')).add_argument('--daily', action='store_true')
    sp.add_parser('adgroups').add_argument('campaign')
    kw = rng(sp.add_parser('keywords'))
    kw.add_argument('campaign')
    kw.add_argument('--all', action='store_true', help='include keywords with no impression')
    rng(sp.add_parser('terms')).add_argument('campaign')
    rng(sp.add_parser('countries'))
    sp.add_parser('negatives').add_argument('campaign')
    a = p.parse_args()
    globals()['cmd_' + a.cmd](a)


if __name__ == '__main__':
    main()
