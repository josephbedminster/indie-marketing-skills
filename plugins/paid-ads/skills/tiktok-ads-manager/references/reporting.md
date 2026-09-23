# Read and analyze results

## TikTok side

1. Open `/i18n/manage/ad?aadvid=<aadvid>&st=<start>&et=<today>` (without
   `st/et` the default period excludes today and shows 0).
2. Columns: columns icon > All templates > "Video views (6-second)" for
   6-second views and their rate; default columns give spend, CPM, CPC,
   impressions, clicks, CTR, conversions (SKAN).
3. Click the ▸ arrow of an ad for the **per-video** detail (that is where a
   hook test is compared).
4. Ad group tab for the split between audiences.

Field benchmarks (one education app, one European country, 20 per day):
CPM ≈ 2, CTR 0.3-0.4 %, 6-second view rate ≈ 2 %, CPC ≈ 0.6. SKAN
conversions arrive 24-72 h late and stay aggregated: don't conclude on
installs before D+3.

## Product analytics side (PostHog)

Use the event names and noise filter of `.claude/posthog-funnel-map.md`.
Queries through the PostHog MCP (`execute-sql`), timezone from the map:

New profiles per day:
```sql
SELECT toDate(toTimeZone(created_at, '<tz>')) AS day, count()
FROM persons WHERE created_at >= now() - INTERVAL 9 DAY GROUP BY day ORDER BY day
```

iOS first opens and funnel (compare with the previous week):
```sql
SELECT toDate(toTimeZone(timestamp, '<tz>')) AS day,
  uniqIf(person_id, event = '<app_first_open>') AS app_first_open,
  uniqIf(person_id, event = '<profile_or_signup>') AS signup,
  uniqIf(person_id, event = '<activation>') AS activated,
  uniqIf(person_id, event = '<paywall_viewed>') AS paywall,
  uniqIf(person_id, event = '<purchase_clicked>') AS clicked_buy,
  uniqIf(person_id, event = '<purchase_success>') AS purchase
FROM events
WHERE timestamp >= now() - INTERVAL 9 DAY AND properties.$os = 'iOS'
  -- noise filter from the funnel map
GROUP BY day ORDER BY day
```

Hour by hour on launch day (`toStartOfHour`, filter on
`$geoip_country_code`) to see whether the rise starts at publishing time.

Filter on `$os = 'iOS'` for installs: landing-page visitors tracked in the
same project are not app installs.

## What the report must contain

Table per campaign and per video (spend, impressions, CPM, clicks, CTR,
6-second views), SKAN conversion status, the rise in iOS first opens in
analytics with an estimated cost per install (day's spend / extra installs
vs the previous average) and the attribution caveat, the day's funnel, then
3-4 concrete recommendations: don't touch anything during the learning
phase, new hook variants if the 6-second view rate is < 3 %, cut a video if
CTR < 0.15 % after 3 days, remind that the paywall stays the ceiling.
