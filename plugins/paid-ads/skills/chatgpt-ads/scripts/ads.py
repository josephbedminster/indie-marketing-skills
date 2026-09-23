#!/usr/bin/env python3
"""CLI for the OpenAI (ChatGPT) Ads Advertiser API.

Stdlib only. Configuration comes from environment variables; any variable not
set is read from the first `.env.local` then `.env` found walking up from the
current working directory. Secret values are never printed.

  OPENAI_ADS_API_KEY              required, Advertiser API key (secret)
  OPENAI_ADS_PIXEL_ID             pixel id, for `pixel-events`
  OPENAI_ADS_LANDING_URL          landing root, for `create` (ad URL = <root>/<lang>/ unless --url)
  OPENAI_ADS_UTM_SOURCE           default "chatgpt"
  OPENAI_ADS_UTM_CAMPAIGN_PREFIX  default "" (utm_campaign = <prefix><lang> unless --utm)
  OPENAI_ADS_DEFAULT_FILE_ID      image file id reused by `create` unless --file-id
  OPENAI_ADS_CONVERSION_EVENTS    comma list, default lead_created,registration_completed,subscription_created

A User-Agent header is required (Cloudflare error 1010 otherwise).

Commands (run `ads.py <command> -h` for options):
  status                       campaigns, budgets, targeting, attached conversions, ads review
  insights [IDS] [--since --until --granularity]   impressions / clicks / spend / cpc per campaign
  conversions [--since --until]                    attributed conversions per campaign
  pixel-events                                     pixel events received in the last 15 minutes
  pause IDS / activate IDS                         change campaign state, re-read to confirm
  budget ID AMOUNT                                 set the daily budget (account currency, API minimum 15)
  attach-conversions [IDS]                         attach the standard conversion events
  create --country CC [--country CC] --name --lang --title --body [--dry-run]
  geo QUERY                                        look up location IDs
  ad-preview AD_ID                                 preview URL of an ad
IDS accept a campaign id, an id prefix, or a case-insensitive name substring.
Money-moving commands (activate, budget increase, create then activate) need the user's explicit yes.
"""
import argparse, json, os, sys, urllib.request, urllib.parse, urllib.error, datetime, re, uuid

BASE = 'https://api.ads.openai.com/v1'
USER_AGENT = 'paid-ads-cli/0.1'
DEFAULT_EVENTS = 'lead_created,registration_completed,subscription_created'
_ENV_LOADED = False


def load_env():
    """Fill os.environ with keys missing from it, from .env.local / .env walking up from cwd."""
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
                    if k.startswith('OPENAI_ADS_') and k not in os.environ:
                        os.environ[k] = v.strip().strip('"\'')
        parent = os.path.dirname(d)
        if parent == d:
            return
        d = parent


def env(name, default=None, required_for=None):
    load_env()
    v = os.environ.get(name) or default
    if v is None and required_for:
        sys.exit('%s is not set (environment, .env.local or .env); needed for %s' % (name, required_for))
    return v


def api_key():
    return env('OPENAI_ADS_API_KEY', required_for='every API call')


def standard_events():
    return [e.strip() for e in env('OPENAI_ADS_CONVERSION_EVENTS', DEFAULT_EVENTS).split(',') if e.strip()]


def call(method, path, body=None, query=None, idem=None):
    url = BASE + path
    if query:
        url += '?' + urllib.parse.urlencode(query, doseq=True)
    headers = {'Authorization': 'Bearer ' + api_key(), 'User-Agent': USER_AGENT}
    data = None
    if body is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(body).encode()
    if idem:
        headers['Idempotency-Key'] = idem
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        try:
            msg = json.loads(raw).get('error', {}).get('message', raw)
        except Exception:
            msg = raw[:300]
        sys.exit('HTTP %s on %s %s: %s' % (e.code, method, path, msg))


def list_all(path, **query):
    out, after = [], None
    while True:
        q = dict(limit=100, **query)
        if after:
            q['after'] = after
        d = call('GET', path, query=q)
        out += d.get('data', [])
        if not d.get('has_more'):
            return out
        after = d.get('last_id')


def campaigns():
    # The list endpoint can return a stale status right after pause/activate:
    # re-read each campaign individually.
    return [call('GET', '/campaigns/' + c['id']) for c in list_all('/campaigns')]


def resolve(ids, camps):
    if not ids:
        return camps
    out = []
    for token in ids:
        t = token.lower()
        m = [c for c in camps if c['id'].lower().startswith(t) or t in c['name'].lower()]
        if len(m) != 1:
            sys.exit('"%s" matches %d campaigns: %s' % (token, len(m), ', '.join(c['name'] for c in m)))
        out.append(m[0])
    return out


def money(micros):
    return '%.2f' % (micros / 1e6)


def countries(c):
    inc = (c.get('targeting') or {}).get('locations', {}).get('include', [])
    return ','.join(l.get('country_code') or l.get('name', '?') for l in inc) or 'ALL'


def event_settings():
    return [e for e in list_all('/conversions/event_settings') if not e.get('archived')]


def standard_setting_ids():
    wanted = standard_events()
    ids = [e['id'] for e in event_settings() if e['event_type'] in wanted]
    if len(ids) != len(wanted):
        sys.exit('Expected event settings for %s, found %d (check OPENAI_ADS_CONVERSION_EVENTS)' % (wanted, len(ids)))
    return ids


# ---------- commands ----------

def cmd_status(a):
    camps = campaigns()
    groups = list_all('/ad_groups')
    ads = list_all('/ads')
    settings = {e['id']: e['event_type'] for e in event_settings()}
    acct = call('GET', '/ad_account')
    print('Account %s (%s, %s), status %s' % (acct['name'], acct['currency_code'], acct['timezone'], acct['status']))
    print()
    print('%-14s %-8s %-10s %-8s %s' % ('campaign', 'status', 'budget/day', 'geo', 'conversions attached'))
    for c in camps:
        conv = ', '.join(settings.get(i, i) for i in c.get('conversion_event_setting_ids', [])) or 'NONE (attach them!)'
        b = c.get('budget') or {}
        budget = money(b['daily_spend_limit_micros']) if 'daily_spend_limit_micros' in b else 'total ' + money(b.get('lifetime_spend_limit_micros', 0))
        print('%-14s %-8s %-10s %-8s %s' % (c['name'][:14], c['status'], budget, countries(c), conv))
        print('   id %s  bidding %s  created %s' % (c['id'], c.get('bidding_type'), datetime.date.fromtimestamp(c['created_at'])))
    print()
    print('Ads (review status must be "approved" to deliver):')
    for ad in ads:
        cr = ad.get('creative', {})
        print('  %-10s %-8s %-10s %s -> %s' % (ad['name'][:10], ad['status'], ad.get('review_status'), cr.get('title'), cr.get('target_url')))
    inactive_groups = [g for g in groups if g['status'] != 'active']
    if inactive_groups:
        print('\nAd groups not active:', ', '.join('%s (%s)' % (g['name'], g['status']) for g in inactive_groups))


def date_args(a, default_days=7):
    until = a.until or datetime.date.today().isoformat()
    since = a.since or (datetime.date.fromisoformat(until) - datetime.timedelta(days=default_days)).isoformat()
    return since, until


def cmd_insights(a):
    since, until = date_args(a)
    camps = resolve(a.ids, campaigns())
    names = {c['id']: c['name'] for c in camps}
    q = {
        'aggregation_level': 'campaign',
        'time_granularity': a.granularity,
        'limit': 2000,
        'time_ranges[]': json.dumps({'type': 'date_range', 'since': since, 'until': until}),
        'fields[]': ['campaign.impressions', 'campaign.clicks', 'campaign.spend', 'campaign.ctr', 'campaign.cpc'],
    }
    if a.granularity != 'none':
        q['fields[]'].insert(0, 'metadata.readable_time')  # rejected when granularity is none
    rows = call('GET', '/ad_account/insights', query=q).get('data', [])
    print('Insights %s -> %s (%s), spend in account currency. Note: a campaign just activated shows 0 for ~2 h (reporting latency).' % (since, until, a.granularity))
    print('%-19s %-14s %9s %7s %9s %6s' % ('time', 'campaign', 'impr', 'clicks', 'spend', 'cpc'))
    totals = {}
    for r in sorted(rows, key=lambda r: (r.get('readable_time') or '', r['id'])):
        m = re.search(r'entity_id=(cmpn_[0-9a-f]+)', r['id'])
        cid = m.group(1) if m else None
        if cid not in names:
            continue
        if a.granularity == 'hourly' and r['impressions'] < 5:
            continue
        t = totals.setdefault(cid, [0, 0, 0.0])
        t[0] += r['impressions']; t[1] += r['clicks']; t[2] += r['spend']
        print('%-19s %-14s %9d %7d %9.2f %6s' % (r.get('readable_time') or 'total', names[cid][:14], r['impressions'], r['clicks'], r['spend'], r.get('cpc', '')))
    if a.granularity != 'none':
        print('--- totals')
        for cid, (i, k, s) in totals.items():
            print('%-19s %-14s %9d %7d %9.2f %6s' % ('', names[cid][:14], i, k, s, '%.2f' % (s / k) if k else '-'))


def cmd_conversions(a):
    since, until = date_args(a, 30)
    camps = campaigns()
    d = call('POST', '/conversions/insights', body={
        'aggregation_level': 'campaign',
        'time_ranges': [json.dumps({'type': 'date_range', 'since': since, 'until': until})],
        'entity_ids': [c['id'] for c in camps],
    })
    names = {c['id']: c['name'] for c in camps}
    print('Attributed conversions %s -> %s (all attached event types summed; the API gives no per-event split,' % (since, until))
    print('so most of these are usually landing CTA clicks, not signups. Check product analytics for the real funnel).')
    for r in d.get('data', []):
        print('  %-14s click-through %4d   view-through %d' % (names.get(r['entity_id'], r['entity_id'])[:14], r['conversions'], r.get('view_through_conversions', 0)))


def cmd_pixel_events(a):
    pid = env('OPENAI_ADS_PIXEL_ID', required_for='pixel-events')
    d = call('GET', '/conversions/events', query={'pid': pid})
    ev = d.get('data', [])
    counts = {}
    for e in ev:
        counts[e['event_type']] = counts.get(e['event_type'], 0) + 1
    print('%d pixel events in the last 15 min: %s' % (len(ev), counts or 'none'))


def set_state(a, action):
    if not a.ids:
        sys.exit('Give at least one campaign id or name.')
    camps = resolve(a.ids, campaigns())
    for c in camps:
        call('POST', '/campaigns/%s/%s' % (c['id'], action))
        fresh = call('GET', '/campaigns/' + c['id'])
        print('%-14s -> %s' % (fresh['name'], fresh['status']))
    if action == 'activate':
        print('Reminder: the daily budget is a floor, not a cap: real spend has reached 2x the daily budget, '
              'mostly within ~1 h after midnight. Check `insights` in 2-3 h (reporting latency).')
    else:
        print('Note: a few clicks in flight can still be billed within the hour.')


def cmd_pause(a):
    set_state(a, 'pause')


def cmd_activate(a):
    set_state(a, 'activate')


def cmd_budget(a):
    c = resolve([a.id], campaigns())[0]
    old = (c.get('budget') or {}).get('daily_spend_limit_micros')
    micros = int(round(a.amount * 1e6))
    d = call('POST', '/campaigns/' + c['id'], body={'budget': {'daily_spend_limit_micros': micros}})
    print('%s budget/day %s -> %s' % (d['name'], money(old) if old else '?', money(d['budget']['daily_spend_limit_micros'])))
    print('Reminder: observed spend can reach 2x the daily budget.')


def cmd_attach_conversions(a):
    ids = standard_setting_ids()
    for c in resolve(a.ids, campaigns()):
        d = call('POST', '/campaigns/' + c['id'], body={'conversion_event_setting_ids': ids})
        print('%-14s conversions attached: %d' % (d['name'], len(d['conversion_event_setting_ids'])))


def cmd_geo(a):
    d = call('GET', '/geo_lookup/search', query={'q': a.query, 'limit': 10})
    for r in d.get('results', []):
        print('%-9s %-8s %s' % (r['id'], r['type'], r['canonical_name']))


def country_id(cc):
    # geo_lookup has no filter by code: search by country name and keep the country row.
    names = {'FR': 'France', 'ES': 'Spain', 'IT': 'Italy', 'DE': 'Germany', 'AT': 'Austria', 'BE': 'Belgium',
             'CH': 'Switzerland', 'NL': 'Netherlands', 'PT': 'Portugal', 'PL': 'Poland', 'GB': 'United Kingdom',
             'IE': 'Ireland', 'LU': 'Luxembourg', 'US': 'United States', 'CA': 'Canada', 'AU': 'Australia'}
    q = names.get(cc.upper(), cc)
    for r in call('GET', '/geo_lookup/search', query={'q': q, 'limit': 10}).get('results', []):
        if r['type'] == 'country' and r['country_code'] == cc.upper():
            return r['id']
    sys.exit('No country found for %s (try `geo <country name>`)' % cc)


def cmd_create(a):
    if len(a.title) > 50 or len(a.body) > 100:
        sys.exit('title max 50 chars (%d), body max 100 chars (%d)' % (len(a.title), len(a.body)))
    url = a.url or '%s/%s/' % (env('OPENAI_ADS_LANDING_URL', required_for='create without --url').rstrip('/'), a.lang)
    utm = a.utm or env('OPENAI_ADS_UTM_CAMPAIGN_PREFIX', '') + a.lang
    source = env('OPENAI_ADS_UTM_SOURCE', 'chatgpt')
    file_id = a.file_id or env('OPENAI_ADS_DEFAULT_FILE_ID', required_for='create without --file-id')
    geo = [{'id': country_id(cc)} for cc in a.country]
    plan = {
        'campaign': {'name': a.name, 'status': 'paused', 'bidding_type': 'clicks',
                     'budget': {'daily_spend_limit_micros': int(a.budget * 1e6)},
                     'conversion_event_setting_ids': standard_setting_ids(),
                     'targeting': {'locations': {'include': geo}}},
        'ad_group': {'name': 'Ad group ' + a.name, 'status': 'active',
                     'bidding_config': {'billing_event_type': 'click', 'strategy': 'maximize_clicks'},
                     'landing_page_configuration': {'query_string_template': 'utm_source=%s&utm_medium=cpc&utm_campaign=%s' % (source, utm)}},
        'ad': {'name': 'Ad ' + a.name + ' 1', 'status': 'active',
               'creative': {'type': 'chat_card', 'title': a.title, 'body': a.body, 'target_url': url, 'file_id': file_id}},
    }
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    if a.dry_run:
        print('\n(dry run, nothing created)')
        return
    tag = uuid.uuid4().hex[:8]
    c = call('POST', '/campaigns', body=plan['campaign'], idem='cmp-' + tag)
    g = call('POST', '/ad_groups', body=dict(plan['ad_group'], campaign_id=c['id']), idem='grp-' + tag)
    ad = call('POST', '/ads', body=dict(plan['ad'], ad_group_id=g['id']), idem='ad-' + tag)
    print('\nCreated PAUSED: campaign %s, ad group %s, ad %s (review: %s).' % (c['id'], g['id'], ad['id'], ad.get('review_status')))
    print('Activate with: ads.py activate %s   (only after the user explicitly confirms the budget)' % c['id'])


def cmd_ad_preview(a):
    d = call('POST', '/ads/%s/preview' % a.ad_id)
    m = re.search(r'src="([^"]+)"', d['data'][0]['body'])
    print(m.group(1) if m else d)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest='cmd', required=True)
    sp.add_parser('status').set_defaults(f=cmd_status)
    s = sp.add_parser('insights'); s.add_argument('ids', nargs='*'); s.add_argument('--since'); s.add_argument('--until')
    s.add_argument('--granularity', default='daily', choices=['none', 'daily', 'hourly']); s.set_defaults(f=cmd_insights)
    s = sp.add_parser('conversions'); s.add_argument('--since'); s.add_argument('--until'); s.set_defaults(f=cmd_conversions)
    sp.add_parser('pixel-events').set_defaults(f=cmd_pixel_events)
    s = sp.add_parser('pause'); s.add_argument('ids', nargs='*'); s.set_defaults(f=cmd_pause)
    s = sp.add_parser('activate'); s.add_argument('ids', nargs='*'); s.set_defaults(f=cmd_activate)
    s = sp.add_parser('budget'); s.add_argument('id'); s.add_argument('amount', type=float, help='daily budget in account currency'); s.set_defaults(f=cmd_budget)
    s = sp.add_parser('attach-conversions'); s.add_argument('ids', nargs='*'); s.set_defaults(f=cmd_attach_conversions)
    s = sp.add_parser('create'); s.add_argument('--country', action='append', required=True, help='ISO code, repeatable')
    s.add_argument('--name', required=True); s.add_argument('--lang', required=True, help='landing locale path, e.g. es, de')
    s.add_argument('--title', required=True); s.add_argument('--body', required=True); s.add_argument('--url')
    s.add_argument('--utm', help='utm_campaign value (default <OPENAI_ADS_UTM_CAMPAIGN_PREFIX><lang>)')
    s.add_argument('--budget', type=float, default=15, help='daily budget, API minimum 15')
    s.add_argument('--file-id'); s.add_argument('--dry-run', action='store_true'); s.set_defaults(f=cmd_create)
    s = sp.add_parser('geo'); s.add_argument('query'); s.set_defaults(f=cmd_geo)
    s = sp.add_parser('ad-preview'); s.add_argument('ad_id'); s.set_defaults(f=cmd_ad_preview)
    a = p.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
