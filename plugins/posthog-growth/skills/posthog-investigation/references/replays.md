# Session replays and heatmaps

## The one rule

Never hand back an unfiltered list of recordings. Either filter on the goal
(the page or event where the funnel leaks) or sort by a signal (errors,
activity), and return a shortlist of 3 to 5 with the reason each one is
worth a look. A raw list buries the useful sessions in noise.

## Find the right recordings

`query-session-recordings-list`, always with `"filter_test_accounts": true`
(the tool defaults to false), a `date_from` matching the investigation window,
a deliberate `order` and `"limit": 10`.

| Goal | Filter |
|------|--------|
| Friction on a page (pricing, paywall, signup, checkout) | `{"type": "recording", "key": "visited_page", "operator": "icontains", "value": "/pricing"}` (confirm the real path with `read-data-schema` first), order `start_time` or `console_error_count` |
| People who did (or reached) a given event | Two steps, see below |
| Rage clicks, frustration | Two steps on `$rageclick` |
| Something broken | `{"type": "recording", "key": "console_error_count", "operator": "gt", "value": 0}`, order `console_error_count` |
| A flag variant or experiment arm | `{"type": "flag", "key": "<flag>", "operator": "flag_evaluates_to", "value": "<variant>"}` |
| A segment | `person_uuid`, a `person` property, a cohort (`{"type": "cohort", "key": "id", "value": <id>, "operator": "in"}`) |
| Mobile | `{"type": "event", "key": "$device_type", "operator": "exact", "value": ["Mobile"]}` |
| Paid visitors | `{"type": "event", "key": "utm_campaign", "operator": "exact", "value": ["<camp>"]}` |
| No goal, "show me good ones" | No filter, order `activity_score` |

### Two steps: sessions where an event happened

The recordings query filters on event properties, not event names. Collect
session ids first:

```sql
SELECT $session_id
FROM events
WHERE event = '<event>'
  AND timestamp > now() - INTERVAL 7 DAY
  AND $session_id != ''
  -- noise filter
GROUP BY $session_id
ORDER BY max(timestamp) DESC
LIMIT 100
```

Then `query-session-recordings-list` with `{"date_from": "-7d",
"session_ids": [...]}`. Pass the **same** `date_from` as the SQL: with only
`session_ids`, the tool falls back to its default of 3 days and silently drops
older sessions. Some session ids have no recording: that's expected.

For "people who reached step N-1 but not step N", take the session ids of
the drop-offs from `query-funnel-actors` or from recipe D.

## Read a recording

Run in parallel:

1. `session-recording-get` with the recording id: duration, active vs
   inactive seconds, clicks, keypresses, console errors, start URL, person.
   A 40-second recording with 0 clicks on a paywall says a lot.
2. The session's events (the recording id is the `$session_id`):

   ```sql
   SELECT timestamp, event, properties.$current_url AS url,
          properties.$el_text AS clicked_text,
          if(event = '$exception', properties.$exception_values[1], null) AS error
   FROM events
   WHERE $session_id = '<recording id>'
     AND event NOT IN ('$pageleave', '$web_vitals', '$feature_flag_called', '$set')
   ORDER BY timestamp ASC LIMIT 200
   ```

   No rows? The events were ingested without the session id. Look for the
   person's events between `start_time - 100 s` and `end_time + 100 s`,
   grouped by `properties.$session_id`, and use one only if it clearly matches.
3. Errors: group the session's `$exception` events by
   `$exception_fingerprint` and look them up with
   `query-error-tracking-issues-list`.

Tell each session as a short story: who (country, device, source, new or
returning), what (pages and key actions in order), where it broke (errors,
rage clicks, loops, long inactivity), and how it ended.

## AI summaries (Replay Vision)

Needs the `replay_scanner:read` scope; running a scan needs
`replay_scanner:write`. Check before you scan: a scanner observes a given
session only once, and scans are slow and use quota.

1. `vision-observations-list` with the session id: an observation from a
   `summarizer` scanner with `status: succeeded` already holds `title`,
   `summary`, `intent`, `outcome`, `friction_points`. Done.
2. Otherwise `vision-scanners-list` filtered on `scanner_type: summarizer`,
   and `vision-scanners-scan-session` with it. Or
   `vision-scanners-inline-scan-create` with the session ids, `scanner_type:
   "summarizer"` and a prompt focused on the question ("What was the user
   trying to do before the pricing step, did they succeed, what friction did
   they hit?").
3. No summarizer exists: **ask the user** before creating one. Create it with
   `"enabled": false` so it never sweeps sessions on a schedule, scan the
   chosen sessions on demand, then ask whether to keep or delete it (the
   summaries survive the deletion).

Launch scans early and keep working on SQL; read the results at the end by
polling `vision-observations-list`.

If the scopes are missing, say which ones in the report so the user can
re-authorize the MCP, and rely on metadata plus timelines.

## No recordings?

Widen the window and loosen the filter first. Still empty, diagnose capture:

```sql
SELECT properties.$recording_status AS status,
       properties.$session_recording_start_reason AS reason,
       properties.$replay_sample_rate AS sample_rate,
       count() AS n
FROM events
WHERE timestamp >= now() - INTERVAL 2 DAY
GROUP BY status, reason, sample_rate ORDER BY n DESC LIMIT 20
```

Usual causes: replay off in project settings, sampling, a minimum duration,
an ad blocker blocking the recorder script, a mobile app or WebView that
doesn't record, URL or flag triggers that exclude the funnel pages. The
official PostHog skill `diagnosing-missing-recordings` goes deeper.

## Heatmaps

For a page that leaks (landing, pricing, paywall, signup form), when
heatmaps are on (`search heatmap` for the tool; needs `heatmap:read`):

- `click` with `unique_visitors` aggregation: what draws attention.
- `rageclick`: the strongest "broken or misleading" signal on a page.
- `scrolldepth`: where people stop. A primary CTA below the point where most
  visitors stop scrolling is a finding.
- Read the fold summary when the tool returns one (share of clicks below the
  initial viewport, median viewport height), and split desktop from mobile
  with the viewport width filters: their folds are different pages.
- Name the hot elements by crossing coordinates with `$autocapture` events on
  the same URL (`$el_text`, selector).

| Signal | Likely meaning |
|--------|----------------|
| Rage clicks on an element | Broken, slow, or looks clickable but isn't |
| Many clicks on plain text or an image | People expect a link there |
| Primary CTA gets few clicks | Buried, low contrast, or out-competed |
| Scroll cliff before key content | The CTA or proof sits where nobody arrives |
| Hot navigation, cold body | The page doesn't deliver; people bail |

Heatmaps return nothing on a page with traffic: capture is probably off or
the URL is wrong. Check both before concluding "no engagement".

## In the report

For each recording used: the deep link
`<posthog host>/project/<project id>/replay/<recording id>` (never
`/replay/home?sessionRecordingId=`), one sentence of what happens, and its
source (Vision summary, timeline, metrics). For heatmaps, name the page,
window and device band. Never write "I watched" or "I saw the page".
