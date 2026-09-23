# Benchmarks and sample sizes

Use these to sanity-check orders of magnitude, never as targets. Always
qualify with the business profile from the funnel map (consumer app vs B2B,
price, trial or not) and say where the number comes from. A benchmark
without context is worse than none.

Several tables below are summarized from
[clamp-sh/analytics-skills](https://github.com/clamp-sh/analytics-skills)
(MIT), which cites the original reports.

## Margin of error before trusting a rate

Approximate 95 % margin on a proportion, by number of people in the smaller
group:

| People | Margin |
|--------|--------|
| 100 | ±10 points |
| 400 | ±5 points |
| 1,000 | ±3 points |
| 10,000 | ±1 point |

If the difference you want to report is smaller than the margin, it is
noise. Under ~20 people at a step, don't compute a rate at all: give the
counts.

## Channel quality: volume × engagement × conversion

A channel is judged on the three at once. Default sorting, not a verdict:

| Channel | Volume | Engagement | Conversion | Default move |
|---------|--------|------------|------------|--------------|
| Direct | high | high | high | defend |
| Organic search | high | high | medium-high | keep investing, it compounds |
| Referral | medium | high | medium-high | cultivate |
| Email | medium | high | very high | grow the list |
| Paid search | medium | medium | medium | scale only if cost per customer allows |
| Paid social | high | low | low | vanity unless tightly targeted |
| Affiliates | varies | low-medium | low-medium | audit for fraud |
| Bots | high | very low | zero | exclude, not a channel |

### Vanity traffic fingerprints

- Pages per session close to 1.0.
- Median session under ~10 seconds.
- Near-zero rate to any downstream event.
- Heavy concentration in a country you don't serve.
- One browser version or device dominating in a way humans don't.
- Suspicious referrers (SEO spam, crypto, fake referral domains).

Filter it first, then re-read the channel table: it usually changes a lot.

## Landing page conversion by source

Unbounce Conversion Benchmark Report 2024 (57M conversions). "Conversion" =
the landing page action (form, download, signup start), **not** a payment,
so these are much higher than paid conversion.

| Source | Median |
|--------|--------|
| Email | 19.3 % |
| Paid social (blended) | 12 % |
| Paid search | 10.9 % |
| All sources | 6.6 % |

## Lead conversion by source

Ruler Analytics 2025 (100M+ data points, 14 industries). Average 2.9 %.
Direct 3.3 %, paid search 3.2 %, referral 2.9 %, organic 2.7 %, email
2.6 %, paid social 2.0 %, organic social 1.5 %. B2B tech is much lower
(~1.5 % across sources, organic social ~0.3 %).

## Paid ads averages

WordStream 2025: Google Ads conversion 7.5 %, cost per lead ~$70; Meta Ads
conversion 7.7 %, cost per lead ~$28. Huge variance by industry.

## Ecommerce

Littledata Shopify benchmarks 2023: conversion 1.4 % (top 20 % above 3.2 %),
mobile 1.2 % vs desktop 1.9 %, checkout completion ~45 %.

## Activation

Mixpanel product benchmarks: new-user activation ~25 % median, above 65 %
top quartile, under 10 % bottom quartile. Fix activation before scaling a
channel.

## Expected drop-off by step type

| Step | Typical share that continues |
|------|------------------------------|
| Landing → pricing page | 15-40 % |
| Pricing → start signup | 10-30 % |
| Start signup → finish signup | 50-85 % (below that, friction) |
| Signup → first key action | 20-70 % (depends most on the product) |
| Trial → paid (self-serve SaaS) | 10-30 % |
| Cart → checkout (ecommerce) | 30-50 % |

## Field notes from a solo consumer app (2026)

Not benchmarks, one real case, useful as a reality check:

- A chatbot ad platform reported dozens of "conversions" on a campaign; in
  product analytics: 104 visitors, 39 CTA clicks, 5 signups, 0 customers.
  The platform's conversions were landing CTA clicks.
- About 85 % of that paid traffic was mobile and left for the App Store: the
  web funnel covered only ~15 % of spend.
- Apple Search Ads installs carry no UTM and arrive as untagged app sessions:
  compare the platform's daily installs with new app users per day instead.
