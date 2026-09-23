# Investigation report template

Write it in the conversation, in the user's language. If they want a file,
save it as `reports/investigations/YYYY-MM-DD-<topic>.md`. Answer first, then
evidence. One idea per bullet, a number in every bullet, observations kept
apart from hypotheses.

```markdown
**TL;DR:** two sentences: the real volume after noise, and the main
bottleneck with its likely cause. **Confidence:** low | medium | high, with
the one-line reason.

## Real traffic over <window>
- Real people, split by country and device.
- Noise removed (bots, app reviewers, internal accounts) and what it carried.
- Traffic changes: campaigns started or paused, spend if known, how many
  tagged visitors actually reached the product.
- Share of traffic PostHog can follow to the end (store CTAs and external
  checkouts are blind spots).

## Main problem: <name>
- The change that moved behavior (commit, flag rollout, campaign), with the
  time it went live.
- Before / after table:

| Period | Reached step | Did next step | Rate |
|--------|--------------|---------------|------|
| before | | | |
| after  | | | |

- Mechanism: who dropped, where they went instead, time to dismiss, repeats
  per session.
- Control segment: <segment> stayed at <rate>, so <conclusion>.
- Replays: 2 or 3 links, one sentence each, with the source (Vision summary,
  timeline, metrics). Heatmap finding if any.
- Perspective: the historical baseline, so a zero is not over-read.

## Causes ruled out
- <cause>: <the number that rules it out>.

## Other leaks
- 3 to 5 bullets max, each with a number and an example visitor (first 8
  characters of the person id) or replay link.

## What shipped
- Merged changes over the period and what they touch.

## Recommendations, by priority
1. The biggest leak first, written as one precise product change.
2. …
N. Tracking and instrumentation last.

## Data gaps
- Checks skipped and why (missing scope, replay off, step not tracked,
  volume too low).

Anything that contradicts a past decision is labelled "experiment behind a
flag". End with: "I can take on points X and Y in <files>, tell me."
```
