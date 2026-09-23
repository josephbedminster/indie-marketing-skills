# Causes to walk, with the query that confirms each

Give every cause a verdict in the report: confirmed, ruled out (with the
number that rules it out), or not checkable (and why). Rank the confirmed
ones by how many independent signals support them.

## 1. Release, deploy or flag rollout

Something shipped near the start of the change.

- Before/after around the deploy time (recipe C), with the live time from
  deploy annotations when available rather than the merge time.
- Breakdown by `$app_version` / `$lib_version` (mobile, SDK): a change
  concentrated in one version is strong evidence.
- For a flag: breakdown by `$feature/<flag_key>` separates exposed people
  from the others.

Suggest reverting or pausing the flag only as an option; the founder decides.

## 2. Traffic source shift

A campaign started or stopped, a post went viral, SEO moved.

- Breakdown by `utm_source`, `utm_campaign`, `$referring_domain`,
  `$channel_type` (recipe H).
- The count of visitors can stay flat while the mix changes: always break the
  **conversion rate** down by source, not only the volume.
- A source with many visitors, ~1 page per session, a median duration under
  10 seconds and no downstream event is vanity traffic (or bots): judge the
  rest of the funnel without it.

## 3. Tracking regression

The measurement changed, not the behavior.

- Events vs unique people: stable people with falling events means the fire
  condition changed.
- A neighboring event stays stable while the target falls: the target's
  tracking changed.
- Duplicate firing: `count() / uniq(person_id)` jumping from ~1 to ~2.
- An event renamed or removed: compare `read-data-schema` with the code
  (`git log -S '<event name>'`).
- Bot filter hiding real events: events sent without a user agent are
  classified `Automation` (see the funnel map).

## 4. New vs returning mix

Same product, different users. An influx of new visitors pulls every rate
down.

- `query-lifecycle` on the key event (new, returning, resurrecting, dormant).
- Split the conversion rate between first-time and returning people.

## 5. Seasonality and calendar

Weekend dip, school holidays, end of month, public holidays in the main
country. Compare with the same weekdays of previous weeks, and with the same
period last year when history allows.

## 6. One platform, device or browser

A JavaScript error on one Safari version, a mobile layout that hides the CTA,
an Android WebView that blocks the checkout.

- Breakdown by `$os`, `$browser`, `$browser_version`, `$device_type`,
  `$screen_width` bands, `$geoip_country_code`.
- Cross-check with errors (recipe F) and `query-error-tracking-issues-list`
  filtered to that platform.

## 7. Outage or third party

Payment provider, app store review, auth provider, email delivery, an API
quota.

- Trend of error events and `$exception` per hour around the change.
- Checkout started without checkout completed, with error messages.
- Status pages of the providers for that time.

## 8. Mix-shift (Simpson's paradox)

The overall rate falls while every segment is stable or rising, because
traffic moved toward a segment that converts less (more mobile, more of one
country, more of one ad). Before concluding "the product got worse", show
the rate per segment side by side for both periods. If each segment is
stable, the answer is the mix, and the fix is on acquisition, not product.

## 9. Upstream data

For warehouse or revenue data (Stripe, RevenueCat synced to PostHog): a
stale sync or a broken join makes revenue look flat. The tools can't prove
this directly: flag it as a candidate when no product-side cause fits, and
point the user to the source's sync status.
