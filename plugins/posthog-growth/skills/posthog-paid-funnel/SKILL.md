---
name: posthog-paid-funnel
description: Judge a paid campaign or channel (Google Ads, Meta, TikTok, Apple Search Ads, ChatGPT Ads, Reddit, newsletters, influencers…) by what its visitors actually do in the product, using PostHog filtered on utm_source / utm_campaign - visitors, CTA clicks, signups, paywall, checkout, paying customers, cost per signup and per customer - and read the replays of paid visitors who dropped. Use it whenever the user asks "is this campaign converting", "how many signups / customers come from the ads", "why do clicks give nothing", "was it worth it", "should I kill this campaign", including when the ad platform already shows conversions - platform numbers are flattering, only the product analytics follow people to the payment. For a broad "what happened this week" across all sources, use posthog-investigation.
---

# Paid traffic funnel in PostHog

Ad platforms count "conversions" that are usually a click on a landing page
button, or a pixel event far from money. The founder's real question is
always the same: of the people I paid for, how many signed up, saw the
price, and paid, and what did each of those cost?

Read `.claude/posthog-funnel-map.md` first (run `posthog-funnel-map` if it
doesn't exist): it holds the step events, the UTM conventions, the noise
filter and the blind spots. Tool conventions are the same as in that skill.

**Project conventions** in the map (report language and style, report location, spend sources, extra context sources) override this skill's defaults.

## 1. Check what is measurable before measuring

- **UTMs reach PostHog?** `read-data-schema` `event_property_values` on
  `utm_campaign` for the landing event: the campaign value must be there
  exactly as in the ad's URL. If not, stop and fix the tagging first.
- **UTMs survive the jump** from marketing site to app? If the site and the
  app are on different domains or the app starts a new anonymous id, the
  campaign disappears at signup. Check that people with `utm_campaign` on the
  landing also have the signup event under the same `person_id`. When the
  numbers drop by more than half between CTA clicks and app entries, say so.
- **Blind spots:** a mobile CTA that opens the App Store or Play Store leaves
  PostHog; those people come back as untagged app installs. Measure the share
  of CTA clicks going to stores vs web, and report the funnel as covering
  only the web share. For store installs, point the user to App Store
  Connect campaign links (`ct=`) or the store's own attribution.
- **Landing events sent without the SDK** (server-side, beacon) can be
  classified as bots and hidden by insights that filter bots. SQL on
  `events` sees them.
- **Tracking start date:** a landing event added recently makes older periods
  look empty. Check `min(timestamp)` of the landing event.

## 2. The query

One SQL query, filtered on the campaign (or `utm_source` for a whole
channel), counting unique people per step, with the step events from the
funnel map:

```sql
SELECT
  properties.utm_campaign AS camp,
  uniqIf(person_id, event = '<landing_viewed>')        AS landing,
  uniqIf(person_id, event = '<cta_clicked>')           AS cta,
  uniqIf(person_id, event = '<app_entered>')           AS app,
  uniqIf(person_id, event = '<signed_up>')             AS signup,
  uniqIf(person_id, event IN ('<paywall_viewed>'))     AS paywall,
  uniqIf(person_id, event IN ('<checkout_started>'))   AS checkout,
  uniqIf(person_id, event IN ('<paid>'))               AS paid
FROM events
WHERE timestamp >= toDateTime('<campaign start>')
  AND properties.utm_source = '<source>'
  -- noise filter
GROUP BY camp ORDER BY landing DESC
```

UTMs are often only on the first events of a person. If later steps come out
empty while the landing isn't, attribute at person level: first find the
people whose first touch carries the campaign, then count their steps
without the UTM filter:

```sql
WITH paid_people AS (
  SELECT person_id, argMin(properties.utm_campaign, timestamp) AS camp
  FROM events
  WHERE timestamp >= toDateTime('<campaign start>')
    AND properties.utm_source = '<source>'
  GROUP BY person_id
)
SELECT p.camp,
       uniq(e.person_id) AS people,
       uniqIf(e.person_id, e.event = '<signed_up>') AS signup,
       uniqIf(e.person_id, e.event IN ('<paid>'))   AS paid
FROM events e INNER JOIN paid_people p ON e.person_id = p.person_id
WHERE e.timestamp >= toDateTime('<campaign start>')
GROUP BY p.camp
```

Compare `landing` with the clicks billed by the platform: 10 to 20 % loss
is normal (bounces before the page loads, blockers). More than half lost
means broken tagging, a slow page, or bot clicks.

## 3. Quality, not just volume

Put the campaign next to the other sources over the same dates (recipe H of
the investigation skill) and judge it on three axes at once: volume,
engagement (pages per session, median duration, share reaching the second
step) and conversion to the map's "converted" event. High volume with ~1 page
per session and a median under 10 seconds is vanity traffic, or bots: check
`$virt_traffic_type` and the country mix before blaming the product.

Compare each step rate with the expected drop-off for that step type and
with the other sources of the same product, which is the fairest benchmark.
External benchmarks, the sample-size table and the channel matrix are in
[references/benchmarks.md](references/benchmarks.md): quote them with their
source and only as orders of magnitude. Never state a rate without its
sample size: with 100 people at a step, it is known to about ±10 points.

## 4. Cost

Spend comes from the ad platform: an ads skill or API if one is installed,
otherwise ask the user for spend per campaign over the same dates. Report
cost per landing visitor, per signup and per paying customer. With zero
customers, report spend per signup and say how many signups the product
usually needs for one sale, so the founder can tell "too early" from "not
working".

## 5. Why paid visitors drop

- **Errors:** people who reached checkout without paying, with their error
  events and messages (`recipe F` in the investigation skill). A
  user-cancelled purchase is a choice; any other message is a bug to report
  as a separate task, not to fix on the spot.
- **Replays:** `query-session-recordings-list` with a session property
  filter on the UTM (`{"type": "event", "key": "utm_campaign", "operator":
  "exact", "value": ["<camp>"]}`) and `visited_page` on the step where they
  drop; read 3 of them as described in the investigation skill's
  `references/replays.md` (never an unfiltered list). Paid visitors often behave differently from
  organic ones: they skim, they're on mobile, they didn't ask for the
  product. Look for the message mismatch between the ad and the first
  screen.
- **Heatmap** of the ad's landing page, desktop and mobile separately: is the
  CTA above the point where paid visitors stop scrolling?
- **Mix:** split by country and device. A campaign whose budget flows to the
  cheapest clicks (one country, one placement) can look fine on CPC and be
  worthless on customers.

## 6. What to return

A vertical table of the steps with people counts and step rates, the biggest
drop named in one sentence ("39 CTA clicks, 5 start the onboarding"), the
sample size (5 people at the paywall prove nothing), the share of spend
PostHog can actually follow, costs per step, 1 to 3 replay links, and one
recommendation: keep, cut, or change one precise thing. Not a list of
options.
