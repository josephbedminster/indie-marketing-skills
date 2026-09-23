---
name: posthog-investigation
description: Investigate what happened to a product's funnel over a period with PostHog, and name the one bottleneck with evidence. Reads the dashboards and goals the founder already built, rules out false alarms (incomplete period, normal variance), walks a list of causes (deploy, flag, traffic mix, tracking bug, new vs returning users, device, outage), finds who dropped and where they went instead, reads event timelines, session replays and heatmaps of representative visitors, compares before and after a deploy, cross-checks on a control segment, and writes a prioritized report with a confidence level. Use it whenever the user asks "why no conversions / no sales / no signups", "what happened in the last 24-72 h", "conversion dropped", "analyze my sessions / replays / dashboard / traffic", "is the new onboarding working", "did the deploy break something", or has just turned on ads, even if they never say "funnel". For one paid campaign judged by its UTMs, use posthog-paid-funnel; for an A/B test, posthog-experiment-reader.
---

# PostHog funnel investigation

The user is usually a solo founder who shipped things, turned on ads and saw
a number they don't like. They want a reconstruction, not a data dump: what
changed, what the real volume is once the noise is removed, where people
drop, why (with evidence), and what to do first. One bottleneck, named,
with numbers and a confidence level.

**Before anything:** read `.claude/posthog-funnel-map.md`. If it doesn't
exist, run the `posthog-funnel-map` skill first. Never query an event name
that is not in the map or confirmed with `read-data-schema`. Calibrate every
judgment on the map's business profile (baseline sales per week, traffic,
read window).

Tool conventions (MCP tool names, `info` before first use, `search` when a
name changed) are the same as in `posthog-funnel-map`. Every call in this
skill is a read, except creating an annotation or a replay scanner, which
needs the user's yes.

## Step 0: what changed (in parallel, before any analytics)

Numbers without context lead to wrong stories. Collect:

1. **Code shipped.** In the repo: `git log --since="<date>" --pretty='%h %ad %s'
   --date=iso` on the main branch, and `gh pr list --state merged --search
   "merged:>=<date>"` if GitHub is available. Keep the timestamp of each
   change that touches onboarding, pricing, paywall, signup or checkout:
   these are the cut points for before/after. If the project writes deploy
   annotations, `annotations-list` with `{"search": "deploy"}` gives when a
   commit actually went live, which can be hours after the merge.
2. **Changes inside PostHog.** `annotations-list` for the period,
   `feature-flag-get-all` (flags whose `updated_at` is near the change),
   `experiment-get-all` (start and end dates). A flag going from 50 % to
   100 % explains many "sudden" changes.
3. **Traffic changes.** Ask, or read from the ad platform if an ads skill or
   API is available: which campaigns started, stopped or changed budget, and
   when. A new low-intent source can halve every rate without any product
   problem.
4. **Past decisions.** The map's "decisions not to re-open", plus CLAUDE.md
   or the project's notes. A recommendation that contradicts one is framed as
   an experiment behind a flag, not as a fix.

## Step 1: start from what the founder already watches

Open the dashboards listed in the map with `dashboard-get` and read their
tiles for the period and the previous one. If a saved funnel insight exists,
run it with `insight-query` for both periods: its definition is the one the
founder trusts. When your numbers differ from their dashboard, explain why
(noise filter, unique people vs events, timezone) instead of silently
disagreeing.

## Step 2: is it even real?

Two false alarms explain a large share of "conversion dropped":

- **Incomplete last period.** If the latest bucket is younger than the
  conversion window (people who signed up yesterday haven't had 7 days to
  pay), the drop is mechanical. Tells: the drop is uniform across all
  segments, first-step volume is stable, the previous bucket sits on the
  usual level. Fix: end the window one conversion window in the past.
- **Normal variance.** Widen to 3 or 4 times the period and compare with the
  same weekdays (weekends and Mondays differ). At small volumes, check the
  margin of error: with 100 people at a step, a rate is known to about
  ±10 points; with 400, ±5; with 1,000, ±3. A drop inside that margin is
  noise: say so and stop, or keep going only on the user's request.

## Step 3: measure, from general to specific

Queries in [references/sql-recipes.md](references/sql-recipes.md); paste the
map's noise filter into every one.

1. **Funnel by country and device** (recipe A). Real volume and where it
   breaks. For official conversion rates prefer `query-funnel` with the map's
   steps (it handles ordering and conversion windows); run it twice with
   windows of equal length, since funnels have no built-in comparison.
2. **Entries or completions?** Trend of people reaching step N-1 and step N
   (recipe B). Steady entries with falling completions: the problem is at
   step N. Falling entries: the problem is upstream (usually traffic).
3. **Before / after** the cut points from step 0 (recipe C). A weekly
   comparison often shows what the daily view hides (for example paywall CTA
   clicks falling from 27 % to 9 % after a "small" redesign).
4. **Who dropped and where they went.** `query-funnel-actors` on the
   leaking step lists the people who dropped; `query-paths` with the failing
   step as end point shows what they did instead (back to home, pricing,
   login wall, quit).
5. **One line per visitor** (recipe D): country, device, source, duration,
   sessions, key step counts, rage clicks, exceptions, last event, last page.
   This is how you "see" 50 sessions without watching 50 videos.
6. **Event timeline** of 2 or 3 representative visitors (recipe E), with the
   clicked text (`$el_text`): the furthest non-converter, an early drop, one
   who saw the same screen many times.
7. **Errors** (recipe F) on the leaking steps, and
   `query-error-tracking-issues-list` for the period. A user-cancelled
   purchase is a choice; any other message is a bug.
8. **Flags and experiments** (recipe G), **sources** (recipe H).

## Step 4: walk the causes

Go through the list in [references/causes.md](references/causes.md) and give
each cause a verdict: confirmed, ruled out, or not checkable. The usual ones:
release or flag, traffic mix, tracking regression, new vs returning mix,
seasonality, one device or browser, outage or third party (payment
provider, app store), and mix-shift. Beware mix-shift: a rate can fall
overall while rising in every segment, because the traffic moved toward a
segment that converts less. Always check the rate per source and per device
before blaming the product.

## Step 5: evidence from replays and heatmaps

Replays turn a hypothesis into a finding. How to find and read them is in
[references/replays.md](references/replays.md). In short: never list
recordings without a filter; target the sessions where the leak happens (by
session ids from SQL, by page, by flag variant); pick 3 to 5; read each one
through an existing Replay Vision summary, or recording metrics plus the
event timeline. Give the user deep links (`<host>/project/<id>/replay/<id>`)
for the ones worth watching.

If the leak is on a page (landing, pricing, paywall, signup form) and
heatmaps are on, read that page's click, rage-click and scroll-depth data
(same reference file): a primary CTA below the scroll cliff, or rage clicks
on something that isn't clickable, is a finding in itself.

Be honest about what you saw: the agent cannot watch video or see the page.
A finding comes from a Vision summary, the event timeline, recording
metrics or heatmap coordinates. Say which.

## Step 6: cross-check on a control segment

Pick a segment the suspected cause should **not** have touched (the other
platform for a web-only deploy, organic traffic for an ad problem, the
control variant for a flag) and rerun the leaking step there. Stable in the
control: strong hypothesis. Moved too: the cause is elsewhere, go back to
step 4.

## Step 7: interpret and report

- **Volume.** Under ~20 people at a step, call it noise. Zero purchases out of
  20 signups is normal for a product that sells one plan a week; click-through
  rate and time-to-dismiss say more than a zero.
- **Loops.** The same screen shown more than twice per session is the product
  reopening it, not a hesitating visitor.
- **Time to dismiss.** A median of a few seconds on a paywall or pricing modal
  means nobody reads it.
- **Blind spots.** Traffic that leaves for an app store or an external
  checkout is not lost, it is unmeasured. Give the share you can follow.
- **Confidence.** High: several independent signals agree (the segment
  isolates the drop, and a deploy or flag lines up, and replays or errors
  show the mechanism). Medium: one corroborating signal, or a strong pattern
  without the control check. Low: a pattern that fits but no corroboration,
  or the data only rules causes out.

Write the report with
[references/report-template.md](references/report-template.md): TL;DR with
confidence, real traffic after noise, the main problem with its before/after
table and replay links, causes ruled out, other leaks, what shipped,
numbered recommendations by priority, data gaps. End with one sentence
offering to tackle the top items, without starting to code.

Afterwards:

- A tracking bug found (duplicate event, missing property, event that
  stopped): add it to the **History** of the funnel map.
- A cause found with no annotation marking it: offer to create one
  (`annotation-create`, needs `annotation:write`), so the next chart
  explains itself.
- A useful replay filter: offer to save it as a playlist.
- If the user says "fix 1 to 3": re-read the decisions from step 0.4, check
  on the latest main branch that each problem still exists, work on a
  branch, and list what you did not verify.
