---
name: apple-search-ads
description: Run Apple Search Ads (Apple Ads, ASA) campaigns through the Campaign Management API v5 with a bundled read-only CLI - campaign status and serving reasons, impressions / taps / installs / spend, CPT and CPI, per-country and per-day reports, keyword and search-term reports, negatives, plus documented payloads to create manual campaigns (exact / broad keywords, Search Match discovery, Search tab, product pages), pause, relaunch, change budgets and bids after an explicit yes. Use it whenever the user mentions Apple Ads, Search Ads, ASA, App Store ads, an auto campaign that doesn't deliver, Apple keywords, CPT, paid installs, "pause / relaunch / raise / lower the Apple campaign", or asks what their App Store ads cost, even if they don't say "API". Not for ChatGPT or TikTok ads (sibling skills), not for the App Store listing's own ASO keywords, and not for judging the in-app funnel (posthog-growth:posthog-paid-funnel). There is no Apple Ads MCP server; don't look for one.
---

# Apple Search Ads (Campaign Management API v5)

There is no MCP server: everything goes through the Apple Ads Campaign
Management API v5 (base URL in `scripts/report.py`). Auth is a JWT ES256 signed with the
user's private key, exchanged for a one-hour OAuth token. Endpoints, payloads
and observed behaviours are in `references/api-notes.md` (in this skill's
folder).

## Before anything: the project config

1. Read `.claude/paid-ads-config.md` in the user's project. If it is missing,
   run the `paid-ads-setup` skill of this plugin (template in
   `../paid-ads-setup/references/config-template.md` relative to this
   skill's folder), asking only what the Apple section needs.
2. If `.claude/posthog-funnel-map.md` exists, read its **Business profile**
   and **Project conventions**; they override this skill's defaults (report
   language, style, where reports go).
3. The script reads `APPLE_ADS_ORG_ID`, `APPLE_ADS_CLIENT_ID`,
   `APPLE_ADS_KEY_ID`, `APPLE_ADS_PRIVATE_KEY_PATH` and `APPLE_ADS_TIMEZONE`
   (default `ORTZ`, the org's timezone) from the environment, falling back to
   the first `.env.local` then `.env` found walking up from the current
   directory. Run it from the project root. The private key is the only
   secret: never print it, copy it or commit it.

If the user has no API access yet: in Apple Ads, Account settings > API,
they create an API user (role "API Campaign Manager" for read and write,
"API Account Read Only" to only report), generate a key pair locally
(`references/api-notes.md` > Auth), paste the **public** key themselves, and
copy the client id, team id and key id shown.

## Read: the skill's script (read-only)

`scripts/report.py` in this skill's folder keeps the token in memory (nothing
written to disk) and only reads. It runs with `uv`, which installs pyjwt,
cryptography and requests on the fly (no venv to maintain): call it directly,
its shebang is `uv run --script`.

```bash
S=<this skill's folder>/scripts/report.py
$S auth                                   # does the key yield a token? org, role
$S status                                 # campaigns, status, reasons, budget/day, countries, placement
$S report                                 # last 7 days to yesterday, per campaign + total
$S report --since 2026-01-12 --until 2026-01-12
$S report --daily --since 2026-01-06      # day by day, per campaign
$S countries --since 2026-01-06           # per country, all campaigns
$S adgroups Discovery                     # ad groups, default bid, Search Match
$S keywords Competitors --all             # keywords, bid, metrics (--all: even with 0 impression)
$S terms Discovery                        # what people actually typed
$S negatives Discovery
```

`CAMPAIGN` = id or name substring (case-insensitive). Columns: `inst` =
`totalInstalls` (taps + view-through), `tapI` = installs after a tap, `CPI` =
spend / inst, `TTR` = taps / impressions, `CR` = installs / taps.

## Write: propose, recap, wait for the yes

Activating, relaunching, creating, raising a budget or a bid spends the
user's money. Before each write, show a recap (campaign, countries,
placement, budget per day, bid, keywords, total daily budget of active
campaigns after the change, and the realistic overspend) and wait for an
explicit yes in chat. A yes covers the action described, not the next one.
Pausing costs nothing but is still a campaign change: say what you pause and
why, and do it when the user asked for it.

Writes use the payloads in `references/api-notes.md`, sent either through
the project's own helper scripts if the config lists some, or through
`report.py`'s `call()` so the token never touches the disk:

```bash
# from the project root, so .env.local is found
uv run --quiet --with pyjwt --with cryptography --with requests python - <<'EOF'
import sys; sys.path.insert(0, '<this skill folder>/scripts')
import report
print(report.call('PUT', '/campaigns/<cid>', {'campaign': {'status': 'PAUSED'}}))
EOF
```

After every write, re-read with `$S status` or `$S adgroups …`: the campaign
must be `ENABLED` / `RUNNING` without `servingStateReasons`, or `PAUSED` /
`PAUSED_BY_USER`. If a helper writes a token file, delete it after use and
make sure it is git-ignored.

## Shell pitfalls (zsh is the macOS default)

- `R="uv run …"; $R` fails in zsh (no word splitting): call `report.py`
  directly.
- `set -- $range` doesn't split either: empty dates, and Apple answers
  `Start date and end date should be in the format: YYYY-MM-DD`. For date
  loops use `bash <<'EOF' … EOF`.
- `echo ===` prints `=== not found` in zsh: quote separators.
- Never name a script `token.py`: it shadows the stdlib `token` module and
  breaks `venv`, `logging`, etc.

## Diagnose a campaign ("why so few taps?")

1. `$S status`: status, `servingStateReasons` (`NO_AVAILABLE_ADS`,
   `NO_AVAILABLE_AD_GROUPS`, `PAUSED_BY_USER`…), budget, countries, placement.
2. `$S report --daily`: days at zero impressions, spend vs budget.
3. `$S countries`: one country absorbing everything means the bid is too low
   elsewhere.
4. `$S terms <campaign>`: off-topic terms to add as negatives, good Discovery
   terms to promote to exact in the right campaign. A term with no text is a
   "low volume" group Apple hides.
5. `$S keywords <campaign> --all`: keywords at 0 impressions (bid too low or
   no volume), taps without installs (cut them).
6. `$S adgroups <campaign>`: default bid, Search Match on or off.

Field case, an automatic campaign: target CPA 0.20, ten countries in one
campaign, no keywords. Apple bid around 0.03 per tap, lost nearly every
auction, and served in the one country where that bid passed, on unrelated
terms (a university portal, a school platform): 289 impressions, 5 taps,
0 installs, 0.16 spent in 16 days, 9 days out of 17 at zero. Fix: manual
campaigns per country and per intent (below).

## Review ("how are the Apple ads doing?")

`$S status` + `$S report` (yesterday and 7 days) + `$S keywords` / `$S terms`
on the biggest spenders. Answer with a short table per campaign (budget/day,
spend, impressions, taps, CPT, installs, CPI) and the total spend since the
user's last decision. Flag:

- yesterday's spend > 130 % of the daily budget (observed: 156 %, and 120 %
  the next day on another campaign);
- an enabled campaign at 0 impressions (typical: brand keywords nobody
  searches yet, small countries with a low bid, the Search tab);
- more than 30 taps over 7 days without an install;
- CPT well above the others, or a CPI far above the search campaigns
  (observed: product-page placement at 2.91 per install vs 0.66 to 1.02 for
  search results, over the same week).

End with one quantified recommendation (which campaign, which bid or
budget), never executed without a yes.

Apple installs carry no UTM: in product analytics they arrive as untagged
native sessions, mixed with other installs. Compare the day's Apple installs
with the day's new native visitors and profiles (field example: 43 Apple
installs, 53 native visitors, 42 profiles on the same day). For the funnel
down to purchase, hand off to `posthog-growth:posthog-paid-funnel`; don't
rewrite its queries here. Installs without purchases have no value while the
funnel doesn't convert: say so.

Field benchmark, one week, ten manual campaigns in five European countries,
education app: 134.73 spent for 320 taps and 148 installs, CPT 0.42, CPI 0.91.
Competitor and discovery campaigns had the best CPI (0.66 to 0.91);
product-page placement had cheap taps (0.33) but an 11 % tap-to-install rate.

## Create campaigns

1. Keywords: from the user's lists in the config, their App Store listing,
   and an ASO tool if one is installed (keyword popularity scores are
   estimates: orders of magnitude only).
2. Structure that works: **one campaign per country (or language group) and
   per intent** (brand, generic, competitors, discovery), `EXACT` keywords in
   the targeted campaigns, and a **Discovery** campaign (Search Match +
   `BROAD`) that excludes, as exact negatives, every keyword of the other
   campaigns, so Discovery only finds new terms.
3. Search tab (`APPSTORE_SEARCH_TAB`, `DISPLAY`): also create an ad on the
   default product page creative (`GET /creatives`), otherwise
   `NO_AVAILABLE_ADS`. Today tab: requires a **custom product page** in App
   Store Connect; without one it is impossible.
4. Show the plan, create everything `PAUSED`, re-read `status`, activate only
   after an explicit yes. First review after 3 or 4 days: below a few hundred
   impressions per campaign, numbers say nothing. Starting bids are guesses;
   adjust them on data.

## Keep the history

Append each change of state, budget or bid, with the date and who decided,
to the config's **History** (or wherever its Project conventions say), and
refresh the campaign table and benchmarks after each review. Trust
`$S status` over any note: notes go stale.

## Neighbour skills

- `chatgpt-ads`, `tiktok-ads-manager`: the other platforms, same approval rule.
- `posthog-growth:posthog-paid-funnel`: what installs do in the app.
- `posthog-growth:posthog-investigation`: broad investigation when a number worries.
