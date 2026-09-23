# indie-marketing-skills

Claude Code skills for indie hackers who do their own growth. Built while
growing a real consumer app solo, then stripped of everything specific to it.

| Plugin | For |
|---|---|
| [`posthog-growth`](#posthog-growth) | Funnel investigations, paid funnels, A/B tests, weekly brief on PostHog |
| [`paid-ads`](#paid-ads) | ChatGPT Ads and Apple Search Ads from the terminal, TikTok Ads Manager in the browser |
| [`app-store`](#app-store) | App Store metadata as code, ASO keyword research, screenshot sets |
| [`ugc-content`](#ugc-content) | AI personas, photoreal image prompts, 9:16 UGC video ads |
| [`seo`](#seo) | Programmatic SEO internal linking, cheap massive yes/no classification |

**How project specifics work.** Skills are generic. Everything about your
product (accounts, IDs, paths, copy rules, decisions you already took) lives
in small files in your repo that the skills write on first use and read every
time: `.claude/posthog-funnel-map.md`, `.claude/paid-ads-config.md`,
`.claude/app-store-config.md`, `.claude/ugc-config.md`,
`.claude/seo-config.md`. Secrets stay in environment variables or your
`.env.local`, never in those files.

## posthog-growth

Five skills that turn Claude into the analyst you don't have, on top of the
[PostHog MCP server](https://posthog.com/docs/model-context-protocol).

| Skill | Ask Claude… | What it does |
|---|---|---|
| `posthog-funnel-map` | "set me up", "map my funnel" (runs automatically the first time) | Short interview about your business (model, price, traffic, what "converted" means), then reads your dashboards, saved insights, actions, goals, events, flags, replay and heatmap settings, finds the noise (bots with PostHog's own classifier, App Store reviewers, you) and writes `.claude/posthog-funnel-map.md`. The other skills never guess an event name again. |
| `posthog-investigation` | "why zero sales this week?", "analyze my sessions", "did the deploy break onboarding?" | Reconstructs what changed (commits, deploys, flags, annotations, campaigns), rules out false alarms, walks a list of causes including mix-shift, finds who dropped and where they went, reads replays and heatmaps of the sessions that matter, cross-checks on a control segment. Ends with one bottleneck, a confidence level, causes ruled out and prioritized fixes. |
| `posthog-paid-funnel` | "is my TikTok campaign converting?", "should I kill the Google Ads?" | Follows paid visitors by UTM from landing to payment, checks tagging and blind spots (store CTAs, external checkout), judges quality vs volume with sourced benchmarks and margins of error, computes cost per signup and per customer, reads replays and heatmaps of paid visitors who dropped. |
| `posthog-experiment-reader` | "can I call my A/B test?", "did the new paywall win?" | Checks the setup (split, sample ratio mismatch, people in both arms), computes lift with its margin, flags peeking, short runs and mix-shift, estimates when the test becomes readable at your traffic, reads replays per variant, returns a verdict. |
| `posthog-weekly-brief` | "give me a weekly growth brief", "keep an eye on my funnel" | Keeps a watchlist of up to 8 flows with baselines in a file, reports only what moved beyond normal, attributes it, lists running experiments, and hands off to the investigation when something looks bad. Schedulable. |

### Lessons baked in

- Ad platforms' "conversions" are usually landing-page clicks. On one
  campaign: 104 visitors, 39 CTA clicks, 5 signups, 0 customers, while the
  platform reported dozens of conversions.
- On mobile, most paid traffic leaves for the App Store and comes back
  untagged: the web funnel may cover only 15 % of your spend. Say it.
- PostHog's own scanners, Apple's App Review and your own test accounts can
  be the only "purchase attempts" of the day. Filter them.
- A before/after around a deploy found what the daily funnel hid: paywall CTA
  clicks falling from 27 % to 9 % after a "small" UI change.

## paid-ads

| Skill | Ask Claude… | What it does |
|---|---|---|
| `paid-ads-setup` | runs automatically the first time | Writes `.claude/paid-ads-config.md`: accounts, landing, UTM conventions, budget rules, copy rules. |
| `chatgpt-ads` | "how are my ChatGPT ads doing?", "launch a campaign in Spain" | Stdlib Python CLI for the OpenAI Advertiser API: status, insights, attributed conversions, pixel events, pause, budget, campaign creation (paused, dry run first). Knows the traps: the daily budget is a floor and spend reached 2x, reporting lags ~2 h, "conversions" are mostly CTA clicks, conversions must be attached to every campaign. |
| `apple-search-ads` | "why does my Apple campaign get no taps?" | Read-only CLI for the Apple Ads Campaign Management API (campaigns, daily reports, keywords with 0 impressions, search terms, countries, negatives) plus documented write payloads. Campaign structure that works: one campaign per country and intent, a Discovery campaign with negatives. |
| `tiktok-ads-manager` | "add these 3 videos to my TikTok ad", "results per video" | Browser playbook for TikTok Ads Manager (no API): UI tricks for its shadow DOM, a pre-publish checklist (AI-generated label, auto enhancements that swap your music), per-video reporting and SKAN delays. |

Every action that spends money waits for your explicit yes, with a recap.

## app-store

| Skill | Ask Claude… | What it does |
|---|---|---|
| `app-store-metadata` | "update my subtitle in 12 languages", "push the release notes" | One JSON per locale as source of truth, and a dependency-free Node script: `check` (limits, duplicates between name, subtitle and keywords, forbidden words), `diff` against App Store Connect, `push` (only with `--yes`, after you saw the diff), `verify`. |
| `aso-keywords` | "which keywords should I target in Italy?" | Method on top of the open-source [aso-mcp](https://github.com/KenanAtmaca/aso-mcp): real positions, gaps, off-intent queries to drop, swaps with the 100-character count. |
| `app-store-screenshots` | "redo my screenshots in German" | Accepted sizes (and the 6.9" size that gets refused as 6.5"), translation order, per-locale visual checks, App Review risks. |

## ugc-content

| Skill | Ask Claude… | What it does |
|---|---|---|
| `ai-persona` | "make her less like a model", "new face for this account" | A consistent AI face across images: dense face description plus reference portrait, calibrated "plain but pretty" (too beautiful reads as AI), 2 options to pick from, a test shot before use. |
| `image-prompt-porting` | "use the style of this prompt I found on X" | Port a photoreal JSON prompt into your pipeline: keep the structure, swap the content, add invariants, keep the JSON valid. |
| `ugc-video-ad` | "make a TikTok ad with a student persona" | 9:16 ad without a video SaaS: persona photos, image-to-video clips, an HTML timeline rendered frame by frame, music and synthesized sound design with ffmpeg. Creative rules learned the hard way: nobody talks, no breathing (AI steam), product only at the end, 3 hooks per persona. |

## seo

| Skill | Ask Claude… | What it does |
|---|---|---|
| `pseo-internal-linking` | "link my new programmatic pages together" | Candidates found in code, a decision model answers two closed questions per link, code decides with thresholds; links only on anchors already in the text, rendered at build time. 3,600 pages cost about $1. |
| `decision-model-batch` | "classify these 10,000 items" | Exact call format and calibration method for a typed decision model (Jev via OpenRouter), 40 to 200 times cheaper than a text LLM for yes/no, choice and score questions. |

## Install

In Claude Code:

```
/plugin marketplace add josephbedminster/indie-marketing-skills
/plugin install posthog-growth@indie-marketing-skills
/plugin install paid-ads@indie-marketing-skills
/plugin install app-store@indie-marketing-skills
/plugin install ugc-content@indie-marketing-skills
/plugin install seo@indie-marketing-skills
```

Install only the ones you need.

For `posthog-growth`, connect the PostHog MCP server (`https://mcp.posthog.com/mcp`, OAuth).
For replay summaries, grant the `replay_scanner:read` and
`replay_scanner:write` scopes; for conversion goals, `marketing_analytics:read`.
Without them the skills still work and tell you what they couldn't see.

Everything the `posthog-growth` skills do in PostHog is read-only, except creating an annotation, a replay scanner or a saved replay filter, which they only do after asking you.

Works best next to PostHog's official plugin (`claude plugin install
posthog`): these skills bring the method and the founder context, the
official ones cover every PostHog product in depth.

## Credits

Built on ideas from, and partly adapted from (all MIT):

- [PostHog/ai-plugin](https://github.com/PostHog/ai-plugin): replay
  shortlisting and investigation, metric investigation playbooks, bot
  traffic classification, heatmap reading, experiment diagnostics.
- [clamp-sh/analytics-skills](https://github.com/clamp-sh/analytics-skills):
  the business profile, the channel quality matrix, benchmarks, experiment
  reading discipline.

## License

MIT
