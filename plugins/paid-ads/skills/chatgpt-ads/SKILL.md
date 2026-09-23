---
name: chatgpt-ads
description: Run ChatGPT Ads (OpenAI Ads Manager) campaigns through the OpenAI Advertiser API with a bundled stdlib Python CLI - campaign status, spend, impressions, clicks, CPC, attributed conversions, pixel health, pause, activate, daily budget, attach conversion events, and create a per-country campaign with localized ad copy and UTMs. Use it whenever the user mentions ChatGPT ads, OpenAI Ads, Ads Manager, sponsored answers in ChatGPT, the oaiq pixel, CPC or budget on ChatGPT, "pause / relaunch / lower / prepare the campaign", or asks what their ads cost this week, even if they don't say "OpenAI" or "API". Not for Apple Search Ads or TikTok (sibling skills), not for installing the pixel in site code, and not for judging the funnel in analytics (posthog-growth:posthog-paid-funnel). There is no OpenAI Ads MCP server; don't look for one.
---

# ChatGPT Ads (OpenAI Advertiser API)

There is no MCP server: everything goes through `https://api.ads.openai.com/v1`
(not `api.openai.com`). `scripts/ads.py` in this skill's folder (Python
stdlib only) covers the everyday operations and already handles the API's
traps: use it rather than hand-written `curl`. Read
`references/api-notes.md` (in this skill's folder) only when you need
something the script doesn't do.

## Before anything: the project config

1. Read `.claude/paid-ads-config.md` in the user's project. If it is missing,
   run the `paid-ads-setup` skill of this plugin (template in
   `../paid-ads-setup/references/config-template.md` relative to this
   skill's folder), asking only the questions the ChatGPT section needs.
2. If `.claude/posthog-funnel-map.md` exists, read its **Business profile**
   and **Project conventions**: report language and style, what "converted"
   means, where reports go. They override this skill's defaults.
3. The script reads its settings from environment variables, falling back to
   the first `.env.local` then `.env` found walking up from the current
   directory. Run it from the project root. Never print a secret value.

| Variable | Needed for | Default |
|---|---|---|
| `OPENAI_ADS_API_KEY` | everything (secret) | |
| `OPENAI_ADS_PIXEL_ID` | `pixel-events` | |
| `OPENAI_ADS_LANDING_URL` | `create` without `--url` | |
| `OPENAI_ADS_UTM_SOURCE` | `create` | `chatgpt` |
| `OPENAI_ADS_UTM_CAMPAIGN_PREFIX` | `create` without `--utm` | empty |
| `OPENAI_ADS_DEFAULT_FILE_ID` | `create` without `--file-id` | |
| `OPENAI_ADS_CONVERSION_EVENTS` | `attach-conversions`, `create` | `lead_created,registration_completed,subscription_created` |

```bash
S=<this skill's folder>/scripts/ads.py
python3 $S status                         # campaigns, budgets, geo, conversions attached, ad review
python3 $S insights --since 2026-01-10    # impressions / clicks / spend / CPC per day and campaign
python3 $S insights --granularity hourly "FR" --since 2026-01-12 --until 2026-01-12
python3 $S conversions --since 2026-01-01 # attributed conversions per campaign
python3 $S pixel-events                   # is the pixel still sending? (last 15 min)
python3 $S pause "ES" "IT"                # id, id prefix, or name substring
python3 $S activate "FR"                  # MONEY: explicit yes first
python3 $S budget "FR" 15                 # MONEY if it goes up: explicit yes first
python3 $S attach-conversions             # attach the standard events to every campaign
python3 $S create --country NL --name "Brand NL" --lang nl --title "…" --body "…" --dry-run
python3 $S geo "Belgium"
python3 $S ad-preview <ad_id>             # URL of a rendered preview
```

## What spends money: ask first

`activate`, a `budget` increase, and `create` without `--dry-run` followed by
activation spend the user's money. Show a recap first (campaign, countries,
budget per day, realistic spend per day, ad text, landing URL) and wait for an
explicit yes in chat. A yes covers the action described, not the next one.
`pause`, every read, `create` (it creates paused) and `attach-conversions`
cost nothing and can be done without asking when the user requested them.
After a pause the script re-reads the status; tell the user a few clicks in
flight can still be billed within the hour.

## Field notes to tell the user without being asked

From one small consumer app's account, in EUR, over a few weeks:

- **The daily budget is a floor, not a cap.** The API refuses anything under
  15 per day, and real spend was exactly 2x the budget (30 for 15), burnt in
  the hour after midnight in the account's timezone. To spend less than about
  30 a day, the only levers are pausing, an `end_time`, or a lifetime budget
  (`lifetime_spend_limit_micros`, untested combined with a daily one).
- **~2 h reporting latency at start.** A campaign just activated shows 0
  impressions for 2 to 3 hours. Don't conclude "it doesn't deliver" before
  that: poll in the background, then `insights --granularity hourly`.
- **Cost benchmarks:** home market 0.29 then 0.51 per click, CTR ~3 %; other
  European countries 0.82 to 1.34 per click with CTR ~1 %. Expect the
  cheapest clicks where the product's language and brand are native.
- **One campaign per country or language, never one global campaign.** The
  budget flows to the cheapest clicks and you lose the cost per market. Each
  country campaign points to the localized landing (`/es/`, `/de/`…).
- **Platform "conversions" are flattering.** The API sums every attached event
  with no per-event split; most of them are usually `lead_created`, a click on
  the landing CTA, not a signup or a payment. Real example: 60 spent, 104
  visitors, 39 CTA clicks, 5 in-app profiles, 0 paying. Judge campaigns in
  product analytics by `utm_campaign` (`posthog-growth:posthog-paid-funnel`).
- **Every campaign needs its conversions attached.** A campaign created in the
  UI came with `conversion_event_setting_ids: []`, hence "0 conversions" for
  weeks. `create` attaches them; `status` prints "NONE (attach them!)"
  otherwise.
- **A UI-created campaign can stop delivering after a re-activation** with no
  visible cause (healthy config; its only difference was
  `enable_dynamic_creative: true`). A clone created through the API delivered
  immediately. When that happens, cloning via API is faster than debugging.
- **Mobile traffic leaves web analytics.** Traffic was ~85 % mobile; when the
  mobile CTA sends people to an app store, product analytics only follow the
  desktop share and the rest arrives as unattributed installs (use App Store
  Connect campaign links with `ct=<utm_campaign>`). Say which share of the
  spend is actually measured.

## Create a country campaign

1. Check the localized landing exists (`curl -sI <landing>/<lang>/`).
2. Write title (≤ 50 characters) and body (≤ 100) in the language, from the
   reference ad in the config. Apply the config's copy rules (banned words,
   punctuation) and have them validated.
3. `create … --dry-run`, show the plan, then without `--dry-run`: the campaign
   is born paused, the ad goes to review (usually approved within minutes),
   UTMs `utm_source=<source>&utm_medium=cpc&utm_campaign=<prefix><lang>`.
4. Activate only after an explicit yes, then check delivery and CPC 2-3 h
   later.

## Review ("how are the ads doing?")

`status` + `insights` over the period + `conversions`, then hand the funnel
judgement to `posthog-growth:posthog-paid-funnel` with the active campaigns'
`utm_campaign` values (don't rewrite its queries here). Answer with a short
table per campaign (impressions, clicks, CPC, spend), the real funnel
(visitors, CTA, signups, paywall, purchases), the share of spend analytics can
follow, total spend since the user's last decision, and end with one
recommendation (cut, keep, change one thing), not a list of options.

## Keep the history

Append each change of state, budget or structure, with the date, to the
config's **History** (or wherever its Project conventions say), and update
the campaign table and benchmarks after a review. The user comes back days
later and asks "where are we".

## Neighbour skills

- `apple-search-ads`, `tiktok-ads-manager`: the other platforms, same approval rule.
- `posthog-growth:posthog-paid-funnel`: what paid visitors do in the product.
- `posthog-growth:posthog-investigation`: broad investigation when a number worries.
