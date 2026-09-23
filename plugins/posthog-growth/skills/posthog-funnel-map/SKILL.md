---
name: posthog-funnel-map
description: Build or refresh the funnel map of a PostHog project, a short markdown file (.claude/posthog-funnel-map.md) that holds the business profile (model, price, traffic, what "converted" means), the real event names of each funnel step, the goals, dashboards and insights that already exist, the UTM conventions, the feature flags, the noise to exclude (bots, app reviewers, internal accounts) and what PostHog cannot see. Use it the first time someone asks for any PostHog funnel, conversion, replay, experiment or paid-traffic analysis in a project that has no funnel map yet, when the user says "set me up", "map my funnel", "set up PostHog analysis", "what are my events", or when an investigation finds an event missing from the map. Every other skill of this plugin reads this file instead of guessing.
---

# PostHog funnel map

Every analysis goes wrong the same two ways: the agent guesses event names
(`signup`, `purchase`) and reports zero, or it judges numbers without knowing
the business ("2 % conversion is bad" for a product sold at 300 € a year to
parents). The funnel map fixes both, once per project. It is a file the user
owns and edits, committed with their code, at `.claude/posthog-funnel-map.md`.

If the file exists and is less than 30 days old, read it and stop here unless
the user asked to refresh it.

## Tools

The PostHog MCP server (`https://mcp.posthog.com/mcp`). Depending on the
client, tools are exposed one by one (`execute-sql`, `read-data-schema`…) or
through a single `exec` tool that takes `call <tool> <json>`. Same tools,
same names. Run `info <tool>` before the first call of a tool you have not
used in this session, and follow its `hint` fields instead of guessing a
schema. When a tool name here doesn't exist, `search <keyword>`: PostHog
renames tools. All calls in this skill are read-only.

Check the active project first (the MCP says which one is active). A user
with several projects, or a second PostHog connector pointing at an empty
project, is a common source of "no data".

If the official PostHog plugin is installed (`PostHog/ai-plugin`), its
`querying-posthog-data` skill has the HogQL reference: read it before writing
non-trivial SQL.

## Step 1: the business profile (a short interview)

Ask at most five questions, in one message, and propose a default for each
from what you can see (landing page, pricing page in the repo, Stripe or
RevenueCat code):

1. **Model:** subscription (monthly / yearly, trial or not), one-time
   purchase, freemium, B2B with sales, marketplace, ads.
2. **Price and what "converted" means:** trial started, first payment,
   yearly plan only? Paying customers per week today, even roughly.
3. **Traffic:** visitors per day, and the main sources (SEO, ads, social,
   App Store, word of mouth).
4. **Surfaces:** marketing site, web app, iOS / Android app, WebView; which
   of them send events to this PostHog project.
5. **Decisions already taken** that an analysis must not re-open (for
   example "the paywall stays right after onboarding"), and the project's
   conventions: report language, where reports go, where ad spend can be
   read.

The answers calibrate everything downstream: the sample size under which a
number is noise, which benchmark row applies, the analysis window (a
consumer app reads in days, a B2B funnel needs 30 to 90 days).

## Step 2: inventory what the user already built

Run these in parallel. Dashboards and saved insights tell you which events the
founder cares about, often better than the raw event list.

1. `dashboards-get-all`, then `dashboard-get` on the 1 to 3 that look like
   funnels, growth, revenue or onboarding. Note each tile's events.
2. Saved insights: `execute-sql` on `system.insights` (check its columns with
   `system.information_schema.columns` first, as the MCP requires), filter
   `query::text ILIKE '%FunnelsQuery%'` (then Retention, Lifecycle), and
   `insight-get` the funnels. A saved funnel is the best source for the step
   order: a human already decided it matters.
3. Actions: `actions-get-all`. Actions are often the "goal" events.
4. Conversion goals: `marketing-analytics-conversion-goals` if the key has
   the `marketing_analytics:read` scope. If the call fails on scope, note it
   and move on.
5. Events: `read-data-schema {"query": {"kind": "events"}}`, paginate.
6. Feature flags and experiments: `feature-flag-get-all`, `experiment-get-all`
   (or `system.feature_flags`, `system.experiments`).
7. Replay and heatmaps: `query-session-recordings-list` with
   `{"date_from": "-7d", "limit": 5}`; zero results means replay is off,
   sampled out or blocked. Try the heatmap tool (`search heatmap`) on the
   landing page. Note both: the investigation skill adapts to them.

No saved funnel at all? Infer **one** activation flow with `query-paths`
from the landing or signup event, and mark it `inferred` in the map: the
user must confirm it, since nobody chose it.

## Step 3: volumes, to separate live events from dead code

```sql
SELECT event, count() AS n, uniq(person_id) AS people,
       min(timestamp) AS first_seen, max(timestamp) AS last_seen
FROM events
WHERE timestamp >= now() - INTERVAL 30 DAY
  AND event NOT IN ('$pageleave','$web_vitals','$feature_flag_called','$set','$autocapture')
GROUP BY event ORDER BY people DESC LIMIT 200
```

An event in the code or in an old insight with `last_seen` weeks ago is dead:
mark it as such, never use it as a funnel step. An event whose `first_seen`
is recent explains why older periods look empty.

If you have access to the codebase, grep the capture calls
(`posthog.capture(`, `capture('`, `track(`) to confirm names and the
properties sent. Code wins over guesses; data wins over code.

## Step 4: find the noise

**Bots.** PostHog classifies traffic from the user agent at query time:
virtual properties `$virt_is_bot`, `$virt_traffic_type` (`Regular`,
`AI Agent`, `Bot`, `Automation`), `$virt_bot_name`, and HogQL functions
`isLikelyBot(ua)`, `getTrafficType(ua)`. Measure the share first:

```sql
SELECT getTrafficType(coalesce(nullIf(properties.$raw_user_agent, ''), properties.$user_agent)) AS traffic,
       uniq(person_id) AS people, count() AS events
FROM events
WHERE timestamp >= now() - INTERVAL 14 DAY
GROUP BY traffic ORDER BY people DESC
```

Trap: an event **without a user agent** is classified `Automation`. Events
sent server-side or by a hand-written beacon (a landing page tracking
script, a webhook) have no user agent and would all be dropped as bots.
Check which events the classifier flags before applying it:

```sql
SELECT event, uniq(person_id) AS people, count() AS n
FROM events
WHERE timestamp >= now() - INTERVAL 7 DAY
  AND isLikelyBot(coalesce(nullIf(properties.$raw_user_agent, ''), properties.$user_agent))
GROUP BY event ORDER BY people DESC LIMIT 30
```

If it only flags your own beacon events and PostHog internals, the
classifier is useless here: exclude the internal events by name instead and
keep the beacons.

**Other noise**, not caught by the user agent:

```sql
SELECT properties.$geoip_country_code AS cc, properties.$geoip_city_name AS city,
       any(properties.$os) AS os, any(properties.$browser) AS browser,
       uniq(person_id) AS people, count() AS events
FROM events
WHERE timestamp >= now() - INTERVAL 14 DAY
GROUP BY cc, city ORDER BY people DESC LIMIT 40
```

- PostHog's own scanners: people with no OS and no browser, events like
  `$scout_report_*` or `$recording_observed`, from one datacenter city.
- App Store review: iOS sessions from Cupertino right after a build
  submission. They often carry the only native purchase attempts of the day.
- The founder and testers: ask for their email or person id, or find them as
  the people with the most events over 30 days. Use `filter_test_accounts`
  where a tool supports it, and a person id prefix filter in SQL.
- Duplicated events: an event fired twice per view inflates `count()`.
  Always count `uniq(person_id)` or `uniq($session_id)`.

## Step 5: attribution

```sql
SELECT properties.utm_source AS src, properties.utm_medium AS med,
       properties.utm_campaign AS camp, uniq(person_id) AS people
FROM events
WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.utm_source IS NOT NULL
GROUP BY src, med, camp ORDER BY people DESC LIMIT 60
```

Note every place where a visitor leaves PostHog's sight: a CTA that opens the
App Store or Play Store, a checkout on another domain, a landing page tracked
in another tool, an anonymous id that resets between site and app.

## Step 6: write the map, then confirm with the user

Write `.claude/posthog-funnel-map.md` from the template below, fill every
section, and show the funnel steps to the user in one short table. Ask them to
correct the step order and the "converted" definition before any analysis
relies on it. Keep the file under 150 lines.

```markdown
# PostHog funnel map
Project: <name> (<id>), <region host>. Timezone: <tz>. Updated: <YYYY-MM-DD>.

## Business profile
Model: <subscription yearly+monthly, 7-day trial>. Price: <…>.
Converted = <first payment>. Baseline: <~N paying customers / week>.
Traffic: <~N visitors / day>, mainly <sources>. Read windows in <days / weeks>.
Decisions not to re-open: <…>.

## Funnel steps (count people, in this order)
| # | Step | Events (any of) | Key properties |
|---|------|-----------------|----------------|
| 1 | Visit | `$pageview` on marketing site | utm_* |
| 2 | Signup | `user_signed_up` | method |
| … | Paid | `subscription_activated`, `purchase_completed` | plan, price |

## Goals already defined in PostHog
Dashboards: <name → url>. Funnel insights: <name → short_id> (inferred: <yes/no>).
Actions: <name → events>. Conversion goals: <list or "none / no scope">.

## Errors and friction events
`purchase_error` (prop `error_message`), `$exception`, `$rageclick`, `$dead_click`…

## Attribution
UTM conventions: <source/campaign values>. Surfaces: <$lib values>.
Blind spots: <store CTAs, external checkout, other analytics tool>.

## Noise filter (paste in every WHERE)
AND (NOT isLikelyBot(coalesce(nullIf(properties.$raw_user_agent, ''), properties.$user_agent))
     OR event IN ('<events sent without user agent>'))
AND NOT startsWith(toString(person_id), '<founder prefix>')

## Feature flags and experiments live
<flag key → variants, what it changes in the funnel>

## Replay and heatmaps
<replay enabled / sample rate / not on mobile…; heatmaps on or off>

## Project conventions
Report language and style: <French, no em dash…>. Reports saved to: <reports/…>.
Spend and campaign sources: <ads skill / script / "ask me">.
Other context sources: <other agent sessions, changelog, Slack…>.
Repo for PR links: <owner/repo>. Memory or decision notes to read: <files>.

## History
<YYYY-MM-DD: event X added, event Y fired twice until …>
```

**Project conventions** is where a project keeps its own habits (language,
report location, where spend comes from, which other tools or notes hold
context). The other skills follow it over their defaults, so a project
never needs to fork them.

Add a line to **History** each time an investigation discovers a tracking
change or bug: the next investigation needs it to avoid comparing apples
with oranges.
