---
name: posthog-weekly-brief
description: Produce a short recurring growth brief from PostHog (daily or weekly) for a solo founder - traffic, signups, paying customers, funnel rates, sources, errors, experiments - scored against the product's own recent baseline, reporting only what moved beyond normal variance, with links to the replays that explain it. Keeps a watchlist of flows and baselines in a file so each run is cheaper and compares like with like. Use it when the user asks for "a weekly brief / morning brief / growth report", "what moved this week", "keep an eye on my funnel", or wants a scheduled task or routine that reports on PostHog. If a number looks alarming, it hands off to posthog-investigation instead of speculating.
---

# PostHog growth brief

A brief that lists 30 numbers gets ignored by the third week. This one says
what moved beyond normal, why it probably moved, and what (if anything) to
do, in under a screen. Everything else is "as usual".

Read `.claude/posthog-funnel-map.md` first (run `posthog-funnel-map` if it
doesn't exist). Tool conventions are the same as in that skill. The brief is
read-only: it never changes flags, experiments or campaigns.

## State: the watchlist file

Keep `.claude/posthog-brief-state.md` next to the funnel map. Create it on the
first run, update it at the end of each run:

```markdown
# Brief state
Cadence: weekly (Monday, covers the previous Monday-Sunday). Last run: <YYYY-MM-DD>.

## Watchlist
| Flow | Kind | Source | Baseline (last 4 complete periods) | Last value |
|------|------|--------|------------------------------------|------------|
| Visit → signup | funnel step | map steps 1-2 | 7.1 % (6.2-8.0) | 6.8 % |
| Signup → paid | funnel step | insight <short_id> | 3.0 % (1.9-4.1) | 2.2 % |
| Paying customers | count | map "Paid" | 4 / week (2-6) | 3 |
| Visitors | count | $pageview on site | 1,900 / week (1,600-2,300) | 2,050 |
| Top error | errors | error tracking | … | … |

## Already reported
- <YYYY-MM-DD>: <signal>, re-report only if <it gets worse / comes back>.

## Ruled out
- <signal>: <why it's noise here, e.g. Monday dip every week>.
```

Seed the watchlist with the saved funnel, retention and lifecycle insights
the founder already has (they chose them), plus the map's funnel steps,
visitors, signups and paying customers. At most 8 rows: a watchlist that
watches everything watches nothing. Retire rows whose insight was deleted.

## A run

1. **Only complete periods.** A weekly brief covers the last full week; a
   daily one covers yesterday. The period in progress always looks like a
   drop.
2. **Score each watchlist row** against its baseline: the same metric over the
   previous 4 complete periods (same weekdays). For rates, compare with the
   baseline range and with the margin of error at this volume (about ±10
   points at 100 people, ±5 at 400). For funnels, use `query-funnel` or the
   saved insight via `insight-query`; for counts, `query-trends` or SQL with
   the noise filter.
3. **Attribute before reporting.** For a row that moved outside its range,
   break it down by source, device and country and check the entrant volume
   of the step. A drop confined to one source that was paused is expected; a
   drop across all segments with steady entrants is a real regression.
4. **Context of the period.** Merged changes (`git log`, merged PRs),
   annotations, flag and experiment changes, campaigns started or stopped.
   Attach each moved row to the most likely change, labelled as a
   hypothesis.
5. **Experiments running:** one line each from `experiment-results-get`
   (exposures per arm, current result, "readable around <date>" using the
   estimate in `posthog-experiment-reader`).
6. **Errors:** new or growing issues from `query-error-tracking-issues-list`
   that touch funnel pages (checkout, signup, paywall).
7. **One or two replays** for the most important moved row, found and read
   as in the investigation skill's `references/replays.md`, with links.
8. **Update the state file:** last values, baselines, what was reported,
   what was ruled out as noise and why.

## The brief

```markdown
**<Week of …>: <one sentence: the single thing that matters most, or "a normal week">.**

| Metric | This period | Usual range | |
|--------|-------------|-------------|---|
| Visitors | | | ↑ / ↓ / = |
| Signups | | | |
| Paying customers | | | |
| <key funnel step> | | | |

## What moved
- <metric>: <value vs range>, concentrated in <segment>. Likely cause:
  <change, with date>. Evidence: <number, replay link>.

## Running experiments
- <name>: <n per arm>, <result>, readable around <date>.

## To look at
- <one or two actions at most, or "nothing">.
```

Everything inside its usual range goes in the table with "=", no comment.
If nothing moved, say so in one line: a calm brief is a useful brief. When a
move is large, unexplained, or hits paying customers, don't speculate in the
brief: flag it and offer to run `posthog-investigation`.

## Scheduling

When the user wants it recurring, set it up with the client's scheduler (a
scheduled task or routine in Claude Code, cron, or CI), weekly on Monday
morning or daily before work, writing the brief to
`reports/briefs/YYYY-MM-DD.md` and optionally sending it where they read
things. Run it once manually first: a scheduled run can't answer a
permission prompt or the business-profile questions.
