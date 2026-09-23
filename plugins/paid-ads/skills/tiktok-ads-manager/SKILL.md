---
name: tiktok-ads-manager
description: Drive TikTok Ads Manager from a browser tool (the built-in browser pane or Claude in Chrome) for an indie app - register the app in Events Manager, create or edit an iOS app-install campaign, add videos to an existing ad for a hook test, go through a pre-publish checklist, publish only after an explicit yes, read results per video (6-second view rate, CTR, CPM, SKAN installs) and cross them with product analytics. Use it whenever the user talks about TikTok ads, launching / updating / analyzing TikTok campaigns, adding a creative to an ad, TikTok budget or results, "how are the TikTok ads doing", even if they don't say "Ads Manager". No TikTok API or MCP is assumed; everything happens in the browser where the user is already signed in.
---

# TikTok Ads Manager (browser playbook)

No API, no MCP: everything happens in a browser tool where the user is
already signed in to Ads Manager. The UI is built from web components
(shadow DOM) and designed for a wide screen, hence the tricks in
`references/ui.md` (in this skill's folder): read them before the first
action, they save half an hour.

## Before anything: the project config

1. Read `.claude/paid-ads-config.md` in the user's project: advertiser id
   (`aadvid`), app ids, identity, campaign and ad group ids, ad texts, copy
   rules, benchmarks. If it is missing, run the `paid-ads-setup` skill of
   this plugin (template in `../paid-ads-setup/references/config-template.md`
   relative to this skill's folder), asking only what the TikTok section needs.
2. If `.claude/posthog-funnel-map.md` exists, read its **Business profile**
   and **Project conventions** (report language and style, funnel events,
   noise filter); they override this skill's defaults.

## Safety rules that apply here

- The user types passwords, verification codes, phone numbers, payment
  methods and billing details themselves. When a page asks for them, stop and
  tell them what to do.
- No file upload from the browser tool (no upload tool, and TikTok's CSP
  blocks a local server). Ask the user to drop the MP4s in Tools > Creative
  library, then resume.
- **Publish**, **Submit** and the **"AI-generated content"** checkbox
  (irreversible) are clicked only after an explicit OK in chat, with a recap
  first. Drafts save themselves: you can stop right before without losing
  anything.
- An edited ad goes back to review (and can restart the learning phase): say
  so before submitting.

## Prerequisites of an iOS app-install campaign

1. App declared in Events Manager > Data sources (TikTok SDK or an MMP, App
   Store id), a TikTok App ID assigned, status **Verified**. Verification
   needs SDK events arriving from a released build.
2. A payment method on file (the user adds it).
3. The full version of Ads Manager (simplified mode has no "App promotion").

If the app falls back to "Pending verification" or TikTok greys it out in the
iOS 14 selector, no SDK event is arriving: check the app (SDK init, access
token, release) before searching in the campaign.

## Structure that works for a small budget

App install objective, Smart+ off (otherwise no manual targeting), "iOS 14
dedicated campaign" on, campaign budget (e.g. 20 per day), bid strategy
Maximum results, automatic placements, one ad group per audience (e.g.
students 18-24, parents 35-54) with one ad each holding several videos.

To test creatives: **add them to the existing ad** (TikTok splits delivery
and you compare per video), not a new ad group. Count 4-5 days at ~20 per day
to separate 5 videos.

## Before every Publish / Submit

Read `references/publish-checklist.md`. In short: the brand's TikTok
identity + "Only show as ads", recommended / auto-generated creatives on
"Don't add", AI label checked with every video selected, "Automatic
enhancements" reduced to CTA enhancement (TikTok turns Generate ad card,
Translate and dub, Video quality and Music refresh back on by default, and
Music refresh would replace the soundtrack), text checked against the
config's copy rules, recap to the user, explicit OK, click.

## Read the results

`references/reporting.md`: URL with a period (`&st=YYYY-MM-DD&et=YYYY-MM-DD`,
otherwise the period stops yesterday), the "Video views (6-second)" column,
per-video detail via the ▸ arrow of an ad, and product-analytics queries to
see iOS first opens before SKAN reports (24-72 h delay). Always give numbers
per video, the 6-second view rate (= hook quality) and the day's in-app
funnel, and say that attribution is only proven by SKAN. For the paid funnel
in depth, hand off to `posthog-growth:posthog-paid-funnel`.

## Keep the history

Note new campaign, ad group and ad ids, budget changes and videos added,
with the date, in the config's **History** and tables (or wherever its
Project conventions say).

## Neighbour skills

- `chatgpt-ads`, `apple-search-ads`: the other platforms, same approval rule.
- `posthog-growth:posthog-paid-funnel` / `posthog-growth:posthog-investigation`:
  fine analysis of paid traffic when the question goes beyond a D+1 report.
