# Paid ads config
Project: <product name>. Updated: <YYYY-MM-DD>. Currency: <EUR>. Timezone: <Europe/Paris>.
Private file: identifiers are fine here, secrets never (keys and tokens stay in env vars / key files).

## General
Product: <iOS app + web SaaS / web only>. Landing: <https://example.com>, locales as paths: <en (root), /es/, /de/…>.
App Store id (adamId): <1234567890 or none>.
Max total spend per day, all platforms: <…>. Every action that spends money needs the user's explicit yes in chat.
Analytics for paid visitors: <PostHog project / other>, judged with `posthog-growth:posthog-paid-funnel`.
Env vars live in: <path of .env.local relative to the repo root>. Key files live in: <keys/ (git-ignored)>.

## Copy rules (validated by the founder)
- Banned words: <"free" if there is no free plan…>. Punctuation: <no em dash…>.
- Tone and person: <informal "you"…>. Languages: <…>.
- Reference ad texts: <title / body that performed>.

## ChatGPT Ads (OpenAI Advertiser API)
Account: <name> (<ad account id>), <currency>, <timezone>.
Env: OPENAI_ADS_API_KEY (secret), OPENAI_ADS_PIXEL_ID=<…>, OPENAI_ADS_LANDING_URL=<…>,
OPENAI_ADS_UTM_SOURCE=<chatgpt>, OPENAI_ADS_UTM_CAMPAIGN_PREFIX=<brand_>, OPENAI_ADS_DEFAULT_FILE_ID=<file_…>,
OPENAI_ADS_CONVERSION_EVENTS=<lead_created,registration_completed,subscription_created>.
Pixel event-setting source id: <…>. Pixel installed in: <files>. Debug: <?oaiq_debug=1>.
UTM: `utm_source=<…>&utm_medium=cpc&utm_campaign=<prefix><lang>`.

| Campaign | id | Status | Geo | Budget/day | Notes |
|---|---|---|---|---|---|
| <name> | <cmpn_…> | <active/paused> | <FR> | <15> | <…> |

Benchmarks (date, market, CPC, CTR, real funnel): <…>.

## Apple Search Ads (Campaign Management API v5)
Org: <name> (<orgId>), role <API Campaign Manager / read only>. App adamId: <…>.
Env: APPLE_ADS_ORG_ID, APPLE_ADS_CLIENT_ID (the SEARCHADS-prefixed client id), APPLE_ADS_KEY_ID, APPLE_ADS_PRIVATE_KEY_PATH, APPLE_ADS_TIMEZONE=<ORTZ>.
Default product page creative id: <…>. Custom product pages: <none / list>.
Write helpers (if any): <path, how to run, what to clean up after>.

| id | Campaign | Placement | Countries | Budget/day | Bid | Targeting |
|---|---|---|---|---|---|---|
| <…> | <Country - Search - Intent> | <Results / Search tab / Product pages> | <…> | <…> | <…> | <…> |

Keyword lists: <file or inline>. Benchmarks (7 days to <date>): <spend, taps, installs, CPT, CPI per campaign>.

## TikTok Ads (Ads Manager, browser)
Advertiser: <account name>, aadvid <…>. Business Center: <…>.
App: App Store id <…>, TikTok App ID <…>, SDK <…>, status <Verified>.
Payment method on file: <type only, never numbers>. Identity: <TikTok identity name>, "Only show as ads".

| Campaign / Ad group | id | Ad | Videos | Budget |
|---|---|---|---|---|
| <…> | <…> | <…> | <…> | <…> |

Ad texts: <…>. Benchmarks (date, market, CPM, CTR, 6-second view rate, CPC): <…>.

## Project conventions
Report language and style: <…>. Where reports go: <…>.
How to run the scripts here: <cwd = repo root; env vars loaded from …>.
Where changes are logged: <History below / memory file / changelog>.
Neighbour skills or tools: <creative production, app release, ASO…>.
Machine pitfalls: <shell quirks…>.

## History
- <YYYY-MM-DD>: <what changed, who decided, why>.
