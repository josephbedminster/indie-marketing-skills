# SQL recipes (HogQL) for the investigation

Run with `execute-sql`. Replace the `<…>` placeholders with the event names
from `.claude/posthog-funnel-map.md`, paste its noise filter where marked,
and set the window (`INTERVAL 24 HOUR`, `72 HOUR`, `14 DAY`). Results are
capped at 100 rows by default; add `LIMIT` explicitly.

Conventions used below:

- `<step1>` … `<paid>`: one event, or `IN (...)` for several events that mean
  the same step.
- Count people (`uniq(person_id)`), never raw events: duplicate firing is
  common.

## A. Funnel by country and device

```sql
SELECT properties.$geoip_country_code AS cc,
       properties.$device_type AS device,
       uniq(person_id) AS people,
       uniqIf(person_id, event = '<step1>') AS s1,
       uniqIf(person_id, event = '<step2>') AS s2,
       uniqIf(person_id, event = '<step3>') AS s3,
       uniqIf(person_id, event IN ('<paywall_viewed>')) AS paywall,
       uniqIf(person_id, event IN ('<checkout_started>')) AS checkout,
       uniqIf(person_id, event IN ('<purchase_error>')) AS errors,
       uniqIf(person_id, event IN ('<paid>')) AS paid
FROM events
WHERE timestamp >= now() - INTERVAL 72 HOUR
  -- noise filter
GROUP BY cc, device ORDER BY people DESC LIMIT 40
```

## B. Daily funnel (entries vs completions)

```sql
SELECT toDate(timestamp) AS d,
       uniqIf(person_id, event = '<step1>') AS s1,
       uniqIf(person_id, event = '<step2>') AS s2,
       uniqIf(person_id, event IN ('<paywall_viewed>')) AS paywall,
       uniqIf(person_id, event IN ('<paywall_cta_clicked>')) AS cta,
       uniqIf(person_id, event IN ('<paid>')) AS paid
FROM events
WHERE timestamp >= now() - INTERVAL 14 DAY
  -- noise filter
GROUP BY d ORDER BY d
```

Read it as entries vs completions: if step N-1 is steady while step N falls,
the problem is at step N; if everything falls from the top, look upstream
(traffic, tracking). Drop the last day when it is still in progress.

## C. Before / after a cut point

```sql
SELECT if(timestamp < toDateTime('<YYYY-MM-DD HH:MM:SS>'), 'before', 'after') AS period,
       uniqIf(person_id, event IN ('<paywall_viewed>')) AS saw,
       uniqIf(person_id, event IN ('<paywall_cta_clicked>')) AS clicked,
       round(clicked / nullIf(saw, 0) * 100, 1) AS rate_pct
FROM events
WHERE timestamp >= toDateTime('<cut>') - INTERVAL 7 DAY
  AND timestamp <  toDateTime('<cut>') + INTERVAL 7 DAY
  -- noise filter
GROUP BY period ORDER BY period DESC
```

Use the same length on both sides and the same weekdays when possible.
Under ~20 people in `saw` per period, report it as noise.

Time before dismissing a screen, and how often it is shown per person:

```sql
SELECT substring(toString(person_id), 1, 8) AS p,
       countIf(event = '<paywall_viewed>') AS shown,
       dateDiff('second',
         minIf(timestamp, event = '<paywall_viewed>'),
         minIf(timestamp, event = '<paywall_dismissed>')) AS secs_to_dismiss,
       countIf(event = '<paywall_cta_clicked>') AS cta
FROM events
WHERE timestamp >= now() - INTERVAL 72 HOUR
  -- noise filter
GROUP BY person_id HAVING shown > 0 ORDER BY shown DESC LIMIT 60
```

A huge negative `secs_to_dismiss` means no dismiss event (empty `minIf`):
read it as "left or still open".

## D. One line per visitor

```sql
SELECT substring(toString(person_id), 1, 8) AS p,
       any(properties.$geoip_country_code) AS cc,
       any(properties.$os) AS os,
       any(properties.$device_type) AS device,
       anyIf(properties.utm_source, properties.utm_source IS NOT NULL) AS src,
       anyIf(properties.utm_campaign, properties.utm_campaign IS NOT NULL) AS camp,
       any(properties.$referring_domain) AS ref,
       min(timestamp) AS first_ts,
       dateDiff('second', min(timestamp), max(timestamp)) AS span_s,
       uniq(properties.$session_id) AS sessions,
       countIf(event = '<paywall_viewed>') AS paywalls,
       countIf(event = '<paywall_cta_clicked>') AS cta,
       countIf(event = '$rageclick') AS rage,
       countIf(event = '$exception') AS exc,
       argMax(event, timestamp) AS last_event,
       argMax(properties.$pathname, timestamp) AS last_path
FROM events
WHERE timestamp >= now() - INTERVAL 72 HOUR
  -- noise filter
GROUP BY person_id ORDER BY first_ts LIMIT 100
```

Reading hints: several sessions with a huge span = someone coming back, not a
bug. Same screen 3+ times = loop. Last path on login or signup with a span
under a minute = bounce on the auth wall.

## E. Timeline of a few visitors

Get full `person_id`s from D without `substring`.

```sql
SELECT substring(toString(person_id), 1, 8) AS p,
       formatDateTime(timestamp, '%m-%d %H:%i:%S') AS t,
       event,
       properties.$pathname AS path,
       properties.$el_text AS clicked_text,
       properties.$session_id AS session
FROM events
WHERE timestamp >= now() - INTERVAL 72 HOUR
  AND toString(person_id) IN ('<uuid1>', '<uuid2>')
  AND event NOT IN ('$pageleave', '$web_vitals', '$feature_flag_called', '$set')
ORDER BY person_id, timestamp LIMIT 400
```

`$el_text` on `$autocapture` / `$rageclick` gives the text the person
clicked. Keep the `session` values: they are the recording ids for the
replay step.

## F. Errors on the leaking steps

```sql
SELECT event, toString(properties.error_message) AS msg,
       any(properties.$os) AS os, any(properties.$browser) AS browser,
       uniq(person_id) AS people, count() AS n
FROM events
WHERE timestamp >= now() - INTERVAL 7 DAY
  AND event IN ('<purchase_error>', '$exception')
  -- noise filter
GROUP BY event, msg ORDER BY people DESC LIMIT 40
```

Adapt the property name (`error_message`, `$exception_message`…) to what the
map says. Complement with `query-error-tracking-issues-list` for the period.

## G. Feature flag split per day

```sql
SELECT toDate(timestamp) AS d, properties.$feature_flag AS flag,
       toString(properties.$feature_flag_response) AS variant,
       uniq(person_id) AS people
FROM events
WHERE timestamp >= now() - INTERVAL 7 DAY AND event = '$feature_flag_called'
GROUP BY d, flag, variant ORDER BY d, flag, variant LIMIT 200
```

For experiments, `experiment-results-get` gives the official result: prefer
it to your own split when it exists.

## H. Sources

```sql
SELECT coalesce(properties.utm_source, '(none)') AS src,
       coalesce(properties.utm_campaign, '') AS camp,
       coalesce(properties.$referring_domain, '') AS ref,
       uniq(person_id) AS people,
       uniqIf(person_id, event = '<step2>') AS s2,
       uniqIf(person_id, event IN ('<paid>')) AS paid
FROM events
WHERE timestamp >= now() - INTERVAL 7 DAY
  -- noise filter
GROUP BY src, camp, ref ORDER BY people DESC LIMIT 60
```

`query-web-stats` gives the same breakdown with bounce rate for the
marketing site, when web analytics is enabled.
