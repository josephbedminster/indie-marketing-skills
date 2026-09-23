---
name: paid-ads-setup
description: Create or refresh the project's paid-ads config, a short private markdown file (.claude/paid-ads-config.md) that holds everything the ads skills need to know about this project - which ad platforms are used, account / org / app / pixel ids, landing URL and locales, UTM conventions, budgets and approval rules, copy rules, the campaign table and its history, cost benchmarks already observed, and where credentials live (never the secrets themselves). Use it the first time someone asks anything about their ChatGPT Ads, Apple Search Ads or TikTok Ads in a project that has no such file, when the user says "set up my ads", "configure paid ads", "connect my ad accounts", or when another ads skill finds a missing fact. The chatgpt-ads, apple-search-ads and tiktok-ads-manager skills read this file instead of guessing.
---

# Paid ads config

Ads skills go wrong in two ways: they guess identifiers (the wrong account,
a campaign that no longer exists), or they judge numbers without history
("0.50 per click is expensive" when the home market already runs at 0.30).
The config file fixes both. It lives in the user's project at
`.claude/paid-ads-config.md`, is private to that project, and is edited by
the user as much as by you.

It may contain identifiers (account ids, org id, app id, pixel id, campaign
ids). It must **never** contain secrets: API keys, private keys, tokens,
passwords, card numbers. Those stay in environment variables or files the
user controls (`.env.local`, a `keys/` folder ignored by git), and the config
only says where they are.

If the file exists, read it and stop here unless the user asked to refresh it
or a skill found a fact missing.

## Also read the funnel map

If `.claude/posthog-funnel-map.md` exists (from the `posthog-growth` plugin),
read its **Business profile** and **Project conventions** first: model,
price, what "converted" means, report language and style, where spend comes
from. Don't ask again what it already answers.

## Step 1: ask, with defaults

One message, at most six questions, each with a default you guessed from the
repo (landing page, `.env*` variable names, existing scripts, locale folders):

1. **Platforms** in use or planned: ChatGPT Ads (OpenAI Ads Manager), Apple
   Search Ads, TikTok Ads, others.
2. **Product and landing:** app or SaaS, landing URL, which locales exist as
   paths (`/es/`, `/de/`…), App Store id if there is an iOS app.
3. **Money rules:** currency, the most the user wants spent per day across all
   platforms, and confirmation that nothing that spends money happens without
   their explicit yes in chat (this is not optional, but say it).
4. **Copy rules:** words or punctuation the founder bans (for example "free"
   when there is no free plan, em dashes), tone, languages.
5. **Attribution:** UTM convention (`utm_source`, `utm_medium`,
   `utm_campaign` pattern), which analytics tool follows paid visitors.
6. **Where history goes:** the History section of this file (default), a
   memory or notes file, a changelog.

## Step 2: discover what can be discovered

Without asking the user:

- Environment variable **names** present in `.env.local` / `.env` walking up
  from the working directory (`grep -oE '^[A-Z_]+=' .env.local`): never print
  values. The scripts expect the names listed in the template.
- ChatGPT Ads: if `OPENAI_ADS_API_KEY` is set, run
  `scripts/ads.py status` from the chatgpt-ads skill folder: it prints the
  account name, currency, timezone, campaigns and conversions attached.
- Apple Search Ads: if the `APPLE_ADS_*` variables are set, run
  `scripts/report.py auth` then `status` from the apple-search-ads skill
  folder: org, role, campaigns, budgets.
- TikTok: there is no API here. Ask for the advertiser id (`aadvid` in the
  Ads Manager URL) or read it from an open Ads Manager tab.

## Step 3: write the file

Copy `references/config-template.md` (in this skill's folder) to
`.claude/paid-ads-config.md`, fill what you know, leave `?` where you don't,
delete the sections of platforms the project doesn't use. Show the user the
filled platform sections in a short table and ask them to correct it.

Keep it under ~250 lines: campaign tables and dated benchmarks, not prose.
Move old history lines to an "Archive" section at the bottom when it grows.

## Keeping it alive

Every ads skill appends to **History** each change of state, budget, bid or
structure, with the date and who decided, and updates the benchmarks after
each review. The user comes back days later and asks "where are we": this
file is the answer.
