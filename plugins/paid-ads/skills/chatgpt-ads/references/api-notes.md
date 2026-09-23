# OpenAI Advertiser API, field notes

Official docs: `https://developers.openai.com/ads/llms.txt` (index); every
page has a Markdown twin by appending `.md`. Useful references:
`ads/api-reference/{campaigns,ad-groups,ads,insights,conversion-setup}.md`,
`ads/location-targeting.md`, `ads/bidding-and-budgets.md`.

## Access

- Base `https://api.ads.openai.com/v1`, header `Authorization: Bearer <key>`.
  It is NOT `api.openai.com` (404 on everything).
- Cloudflare answers `error code: 1010` to requests without a `User-Agent`:
  bare Python `urllib` fails, any UA works; `curl` works out of the box.
- A non-admin key gets 403 on `GET /ad_account/spend_limit_windows`: account
  spend caps and billing are only visible in the UI.
- `GET /ad_account`: name, currency, timezone, status.

## Objects

Campaign → ad group → ad. Amounts in micros (15.00 = 15 000 000).

- `POST /campaigns`: `name`, `status` (`paused` recommended), `bidding_type`
  `clicks`, `budget.daily_spend_limit_micros` (the docs say `lifetime_…`;
  daily is accepted, minimum 15 000 000), `targeting.locations.include`
  `[{id}]`, `conversion_event_setting_ids`.
- Update = `POST /campaigns/{id}` (not PATCH). `bidding_type` is immutable:
  optimizing for conversions needs a new campaign (`bidding_type:
  conversions` + exactly one event setting).
- State: `POST /campaigns/{id}/activate|pause|archive`. `GET /campaigns`
  (list) can return a stale status right after; re-read `GET /campaigns/{id}`.
- `POST /campaigns` rejects `user_external_id` (filled automatically from the
  `Idempotency-Key` header). `POST /ad_groups` in `maximize_clicks` without
  `max_bid` requires an `Idempotency-Key` header (the script sends one on
  every create).
- `GET /ads?campaign_id=` is not filtered (returns everything); the filter
  that works is `ad_group_id`.
- `POST /ad_groups`: `campaign_id`, `bidding_config` `{billing_event_type:
  click, strategy: maximize_clicks}`,
  `landing_page_configuration.query_string_template` for UTMs.
  `max_bid_micros` is not required with `maximize_clicks`.
- `POST /ads`: `creative` `{type: chat_card, title ≤ 50, body ≤ 100,
  target_url, file_id}`. An uploaded image `file_id` can be reused across
  ads (keep it in the config). `POST /ads/{id}/preview` returns an iframe;
  its `src` URL opens in a browser.
- Countries: `GET /geo_lookup/search?q=Spain` (search by name; there is no
  filter by ISO code, keep the row with `type: country`).

## Reporting

- `/v1/insights` does not exist. Use `GET /ad_account/insights?aggregation_level=campaign`
  or `GET /campaigns/{id}/insights`, with
  `time_ranges[]={"type":"date_range","since":"YYYY-MM-DD","until":"YYYY-MM-DD"}`
  (JSON-encoded in the query), `time_granularity` `none|hourly|daily`,
  `fields[]` among `campaign.impressions|clicks|spend|ctr|cpc` and
  `metadata.readable_time` (rejected when granularity is `none`).
- Row ids contain `entity_id=cmpn_…`; parse it to get the campaign.
- Attributed conversions: `POST /conversions/insights` body
  `{aggregation_level: campaign, time_ranges: ["<json>"], entity_ids: [...]}`.
  No split by event type.
- Pixel: `GET /conversions/events?pid=<pixel id>` = raw stream of the last
  15 minutes (`page_viewed`, `lead_created`, `registration_completed`,
  `subscription_created`, `openai::sdk_init`).
- Event settings: `GET /conversions/event_settings`. Attaching = `POST
  /campaigns/{id}` with the full `conversion_event_setting_ids` list (it
  replaces, it doesn't merge).

## Site side

Typical setup: the pixel snippet in the landing `<head>` (and any redirect
pages, SEO pages and the web app), `page_viewed` on load, `lead_created` on
the landing CTA click, `registration_completed` and `subscription_created`
from the web app. Adding `?oaiq_debug=1` to a page URL shows the pixel's
events firing in production. Note in the project config which files hold
the pixel.
