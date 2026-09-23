---
name: posthog-experiment-reader
description: Read a PostHog A/B test or feature flag split honestly at indie-hacker volumes - "can I call it?", "did the variant win?", "should I ship this paywall / pricing / onboarding change?", "is the new version better than the old one?" - by checking the setup (exposures per variant, sample ratio mismatch, people in both arms), pulling per-variant exposures and conversions, computing absolute and relative lift with its margin of error, flagging peeking, short runs and mix-shift, reading replays per variant, and returning a verdict (ship, wait until N, redesign, investigate) instead of a false positive. Also use it for informal before/after comparisons of two versions when the user asks whether a change "worked". Not for designing a new experiment from scratch.
---

# Reading an experiment honestly

Indie experiments die from small numbers, not from bad ideas. 300 people per
variant can show "+49 %" that is pure noise. The job is to say which of
these is true: the variant wins, it loses, it makes no measurable
difference, or it's too early and here is when it won't be.

Read `.claude/posthog-funnel-map.md` first (run `posthog-funnel-map` if it
doesn't exist) for the conversion events, noise filter and business
baseline. Tool conventions are the same as in that skill. Everything here is
read-only: never stop, ship or edit an experiment or flag without the
user's explicit yes.

## 1. Resolve the experiment

- A PostHog experiment: `experiment-get-all` (or `system.experiments`), then
  `experiment-get`. Note the flag key, variants and their split, overall
  rollout, start date, status, exposure event, test-account filtering, and
  stats method (Bayesian by default, or frequentist).
- A plain feature flag used as a test: `feature-flag-get-all`, then the flag's
  variants and rollout. The exposure is `$feature_flag_called` with
  `$feature_flag = '<key>'`.
- An informal "before vs after" (no randomization): say upfront that it is
  not an experiment, then compare two windows of equal length and the same
  weekdays with the investigation skill's recipe C, and treat any
  difference as a hypothesis, never a proof.

## 2. Check the setup before reading any result

```sql
SELECT toString(properties.$feature_flag_response) AS variant,
       uniq(person_id) AS people
FROM events
WHERE event = '$feature_flag_called'
  AND properties.$feature_flag = '<flag key>'
  AND timestamp >= toDateTime('<start>')
  -- noise filter
GROUP BY variant ORDER BY people DESC
```

- **Exposures in every arm.** One arm at ~0: assignment is broken (a
  release condition pinning everyone to one variant, the flag not evaluated
  on that platform). Stop there.
- **Sample ratio mismatch.** For a 50/50 test, 60/40 is a bug, not a result:
  exposure fires unevenly, or some people are excluded in one arm. Stop and
  report it.
- **People in both arms:**

  ```sql
  SELECT countIf(n > 1) AS in_both, count() AS exposed
  FROM (
    SELECT person_id, uniq(toString(properties.$feature_flag_response)) AS n
    FROM events
    WHERE event = '$feature_flag_called' AND properties.$feature_flag = '<flag key>'
      AND timestamp >= toDateTime('<start>')
    GROUP BY person_id
  )
  ```

  More than a few percent means identity problems (anonymous then logged-in
  users, web vs app ids).
- **Mid-run changes:** split, rollout, metric or targeting edited after the
  start make the before and after periods different experiments. Check the
  flag's activity log; read only the stable period.

For a PostHog experiment, `experiment-results-get` gives the official
result: use it as the headline, and your own SQL only to check and explain.
When the two disagree (PostHog excludes people exposed to several variants,
applies its own conversion window and test-account filter), say why.

## 3. The four numbers per variant

Exposed people, and exposed people who converted after their first exposure:

```sql
WITH exposed AS (
  SELECT person_id,
         argMin(toString(properties.$feature_flag_response), timestamp) AS variant,
         min(timestamp) AS first_exposure
  FROM events
  WHERE event = '$feature_flag_called' AND properties.$feature_flag = '<flag key>'
    AND timestamp >= toDateTime('<start>')
    -- noise filter
  GROUP BY person_id
  HAVING uniq(toString(properties.$feature_flag_response)) = 1
)
SELECT x.variant,
       count() AS exposed,
       countIf(c.first_conv IS NOT NULL
               AND c.first_conv >= x.first_exposure
               AND c.first_conv <= x.first_exposure + INTERVAL <window> DAY) AS converted
FROM exposed x
LEFT JOIN (
  SELECT person_id, min(timestamp) AS first_conv
  FROM events
  WHERE event IN ('<conversion event>') AND timestamp >= toDateTime('<start>')
  GROUP BY person_id
) c ON c.person_id = x.person_id
GROUP BY x.variant ORDER BY x.variant
```

The conversion must happen **after** exposure and within a window that fits
the product (same session for a CTA click, 7 days for a trial start, more
for a payment). Exclude people exposed less than one window ago, or they
drag the rate down in whichever arm grew fastest.

## 4. Lift, with its margin

- Rate per variant = converted / exposed.
- Absolute lift in points, and relative lift in %. Always both: 4 % → 5 % is
  "+25 %" relative and +1 point absolute.
- Margin of error on each rate at 95 %: about `1.96 × sqrt(p × (1 − p) / n)`.
  Rough guide at the smaller arm's size: 100 people ±10 points, 400 ±5,
  1,000 ±3.
- If the absolute lift is smaller than the smaller arm's margin, it's
  noise. Say "inconclusive at this size", not "slightly better".
- With PostHog's Bayesian output: "96 % chance to win" is not "96 % sure
  it's worth shipping". Look at the credible interval of the lift too; if it
  spans from clearly negative to clearly positive, it's too early.

**How long until it's readable?** People needed per variant to detect an
absolute lift `d` on a base rate `p` (95 % confidence, 80 % power) ≈
`16 × p × (1 − p) / d²`. For a 5 % base rate and a 2-point lift: ≈ 1,900
per variant. Divide by the daily exposures per variant to give a date. If
that date is months away, say so: at this traffic the test can only detect
big effects, and a bolder variant is a better use of the traffic.

## 5. Traps to check

- **Peeking.** Checking daily and stopping the first day it looks
  significant inflates false positives far above 5 %. If the user has been
  watching, don't stop on a threshold crossing: extend by at least a full
  week and see whether it holds, or use PostHog's sequential or Bayesian
  output as it's designed.
- **Run length.** Under 7 days, day-of-week effects are mixed in. Cover full
  weeks.
- **Mix-shift.** Compare the source, device and country mix per variant
  (only when a variant looks like a winner; slicing everything multiplies
  false positives). A "win" driven by one arm getting more desktop traffic
  is not a win.
- **Many metrics.** With 10 secondary metrics, one will be "significant" by
  chance. Decide on the primary metric; treat secondaries as guardrails.
- **Guardrails.** A variant that lifts the paywall click but lowers the
  payment, or increases refunds and cancellations, is a loser.
- **A/A sanity.** If a test between identical versions shows a winner, the
  setup is broken, not the users.

## 6. Why: replays per variant

For the arm that wins or loses, list recordings of exposed people on the
tested screen with a flag filter (`{"type": "flag", "key": "<flag key>",
"operator": "flag_evaluates_to", "value": "<variant>"}`) plus `visited_page`,
and read 2 or 3 per arm as described in the investigation skill's
`references/replays.md`. Behavior differences (people scroll past the new
copy, nobody opens the plan picker) explain the number and give the next
variant.

## 7. Verdict

```
VERDICT: <ship / keep control / inconclusive, wait until ~<date> (<N> per arm) / setup broken: <what>>

NUMBERS
- control: n=<exposed>, converted=<k>, rate=<r> % (±<m>)
- <variant>: n=<exposed>, converted=<k>, rate=<r> % (±<m>)
- absolute lift: <+x> points, relative: <+y> %
- PostHog result: <chance to win / p-value, interval>

CHECKS
- split <a/b> vs expected <…>, people in both arms <x %>, run <d> days
- mix per arm: <same / differs on …>
- guardrails: <payment, cancellations…>

WHY (replays): <one sentence per arm, with links>

NEXT: <one action>
```

"No difference" is a real result: the change doesn't matter for this metric,
so ship whichever is simpler, or test something bolder. Never turn
"inconclusive" into "slightly better".
