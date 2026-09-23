---
name: aso-keywords
description: App Store keyword research (ASO) with the free, open-source aso-mcp MCP server - where the app ranks for each query and country, who leads and with how many ratings, keyword gaps against competitors, off-intent queries to drop, and concrete swaps for the name, subtitle and 100-character keywords field, then measuring the effect a few weeks after release. Use it whenever the user asks "what keywords should I use", "why doesn't my app show up in search", "analyze my competitors on the App Store", "ASO audit", "which title / subtitle", "are my keywords good", wants to enter a new country, or is about to change the listing text, even if they never say "ASO". Not for writing and pushing the listing itself (app-store-metadata) nor for Apple Search Ads bidding.
---

# ASO keyword research

Goal: decide which words go in the three indexed fields (name 30, subtitle 30,
keywords 100) of each storefront, with evidence, and know how to tell later
whether it worked.

## Step 0: context

Read `.claude/app-store-config.md` (app id, locales, priority markets,
competitors, previous rankings, where research notes go). Missing: follow
`../app-store-metadata/references/config-template.md`, ask, write it. If
`.claude/posthog-funnel-map.md` exists, read **Business profile** (who buys,
which countries bring users) and **Project conventions**.

Priority markets come from data (analytics users per country over 30 days,
countries where ads run), not from the list of locales.

## Tool: aso-mcp

Open source, MIT, no account: `claude mcp add -s user aso-mcp -- npx -y aso-mcp`.
It scrapes the public App Store (search results, app pages, ratings). First
start is slow (npx plus a native SQLite build, a 30 s connection timeout can
happen once), fast afterwards. Tools are often deferred: load them in one
ToolSearch call (`select:mcp__aso-mcp__search_keywords,mcp__aso-mcp__analyze_competitors,mcp__aso-mcp__keyword_gap,mcp__aso-mcp__localized_keywords,mcp__aso-mcp__analyze_reviews`).

| Tool | Use | Trust |
|---|---|---|
| `search_keywords` | top apps for a query in a country, your position | positions and rating counts are real; traffic / difficulty scores are estimates |
| `analyze_competitors` | a competitor's listing, ratings, title words | good |
| `keyword_gap` | words a competitor ranks on and you don't | good |
| `localized_keywords` | one query across storefronts | good |
| `analyze_reviews` | complaints and wishes in reviews (copy ideas) | good |
| `track_ranking`, `get_ranking_history` | follow positions over time | check the output before relying on it |
| `suggest_keywords`, `discover_keywords` | ideas | noisy (stop words, "https"): brainstorm only |
| `connect_*`, anything that writes | App Store Connect writes | **never.** Do not give it App Store Connect keys; writes go through app-store-metadata's diff + OK + push |

Scores marked "estimated" are orders of magnitude (Apple's popularity endpoint
rarely answers). Reason on positions and on the rating counts of the top 5.

## Method

1. **Candidates.** 10 to 20 queries per priority market: words of the current
   name, subtitle and keywords field, the job the app does in users' words,
   competitors' title words, local school / trade vocabulary.
2. **Positions.** `search_keywords` for each query and country. Record your
   position (or "absent from top 100"), the top 5, and the leader's rating count.
3. **Gaps.** `analyze_competitors` and `keyword_gap` on 3 to 5 direct
   competitors. `localized_keywords` for a query that matters in several
   countries.
4. **Drop off-intent queries.** Read the top 5 for each query: if they are not
   apps like yours, the traffic is not yours either. Typical traps: a short
   word shared with a game ("bac" is also a word game in French), "exam prep"
   owned by professional certifications, "study notes" owned by note-taking
   apps.
5. **Decide.** Favour queries where the top 5 have few ratings (weak
   competition) and the intent matches. A query whose leaders have 100k+
   ratings is a long-term goal, not a keyword-field swap.
6. **Propose swaps** as a table per locale: current field, proposed field,
   character count x/100 (and x/30 for name and subtitle), what goes out and
   why. No word duplicated with name or subtitle, no competitor brand. Nothing
   is pushed from here: hand over to `app-store-metadata` (check, diff, OK,
   push).
7. **Save the raw results** (JSON per country and date) and a short summary
   where the project config says (for example `docs/aso/<date>-<country>.json`
   and `docs/aso/<date>.md`), and add a History line to the config. The next
   round compares against it.

## Reading results honestly

- aso-mcp reads the **published** listing. Metadata pushed on a version still in
  preparation does not show; say so when presenting positions.
- Measure a title or keyword change **2 to 3 weeks after the version is live**,
  on the same queries and countries, not the day after.
- Rankings move with ratings, downloads and conversion, not only with words.
  Changing keywords cannot fix a ratings gap.

## The review gap

For a young app, the usual finding is not a keyword problem. Anonymized field
notes from one run:

- A new app ranked only on words of its title (position 2 to 4 on its core
  query in two countries), and was absent from the top 100 on every generic
  query around it.
- The gap was reviews: about 10 ratings against 700 to 70,000 for the apps in
  the top 5.
- The cheapest market was the one where competitors on a local-language query
  had 2 to 4 ratings: winnable within weeks.
- A seasonal exam query had weak competition outside two apps: a good target
  for the promo text and keywords during the exam months only.
- A competitor ranked on a "tutor" query the app did not cover: adding the word
  closed a clear gap.

So the report should say it plainly when it applies: the next lever is ratings
(native review prompt after a success moment, never in release notes), then
keywords.

## Report

Per market: a table query / your position / leader and its ratings / verdict
(keep, add, drop, long-term), then the proposed field changes with counts, the
risks (off-intent, brand terms), and the date to re-measure. Cite estimated
scores only as "estimated".
