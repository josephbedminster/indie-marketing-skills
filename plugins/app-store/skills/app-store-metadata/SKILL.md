---
name: app-store-metadata
description: Write, translate, check and publish the text of an iOS App Store listing (app name, subtitle, keywords field, description, promotional text, release notes / whatsNew, marketing, support and privacy URLs) for every locale, from one JSON file per locale kept in the repo, with a dependency-free script that checks Apple's limits and ASO rules offline, diffs against App Store Connect, pushes only after an explicit OK, and verifies. Use it whenever the user wants to change the App Store title or subtitle, rewrite the description, add or translate a store language, update promo text or release notes, "push the metadata", "sync the listing", prepare the listing for a new version, or asks why an App Store Connect edit is refused, even if they never say "metadata" or "App Store Connect API". Not for screenshots (app-store-screenshots), keyword research (aso-keywords), builds or submitting for review.
---

# App Store metadata

The listing text is code: one JSON file per App Store locale, committed, reviewed,
checked by a script, pushed by a script. Editing it by hand in App Store Connect
across 10+ languages drifts within a week and nobody can say what is live.

## Step 0: read the project config

Read `.claude/app-store-config.md` in the user's project. It holds the app id,
locales, where the JSON lives, how to run the push, the house copy rules, and
anything that overrides this skill. **The project config wins over this file.**

Missing? Ask the questions of `references/config-template.md` in one message
(propose defaults from what you see in the repo), write the file from that
template, then continue. If `.claude/posthog-funnel-map.md` exists, read its
**Business profile** (price, trial or not: never promise "free" if the app is
paid) and **Project conventions** (language, style bans like the em dash).

## Files: the source of truth

One file per locale in the metadata folder (default `./appstore-metadata/`):

```json
{
  "locale": "en-US",
  "name": "Acme: Habit Tracker & Goals",
  "subtitle": "Daily Routine, Streaks, Focus",
  "keywords": "planner,reminder,journal,mood,water,sleep,workout,todo,discipline,motivation,self care,calendar",
  "description": "Build one habit at a time…",
  "promotionalText": "…",
  "whatsNew": "…",
  "marketingUrl": "https://example.com/en/",
  "supportUrl": "https://example.com/support",
  "privacyPolicyUrl": "https://example.com/en/privacy"
}
```

Limits, what each field does, and the writing rules: `references/fields-and-rules.md`.
Read it before writing or translating any field.

The three things people get wrong most:
- **Only name, subtitle and the keywords field are indexed** by App Store search.
  Description, promo text and screenshot captions sell, they do not rank.
- **A word already in the name or subtitle is wasted in the keywords field.** Use
  94 to 100 of the 100 characters, commas without spaces, no competitor brands
  (guideline 2.3.7).
- **Each storefront gets its own vocabulary**, not a word-for-word translation
  (school levels, exams, local words for "homework").

## The script

`scripts/asc-metadata.mjs` (Node 18+, no dependencies). Copy it into the project
or run it from the plugin folder.

| Command | Network | What it does |
|---|---|---|
| `check` | none | limits, missing fields, keyword waste, forbidden patterns, stray English, URLs |
| `diff --version X` | GET only | before (App Store Connect) / after (JSON), per locale and field |
| `push --version X --yes` | **writes** | check, then PATCH/POST localizations, then verify |
| `verify --version X` | GET only | re-reads App Store Connect and lists any field that differs |

Common options: `--dir <folder>`, `--locales en-US,fr-FR`, `--fields promotionalText`,
`--rules <file.json>`, `--forbid <regex>`, `--competitors a,b`. Without `--yes`,
`push` only prints what it would write and exits with code 2.

**Credentials are read from the process environment only**, on the command line:

```bash
APP_STORE_ISSUER_ID=… APP_STORE_KEY_ID=… APP_STORE_APP_ID=… \
APP_STORE_PRIVATE_KEY_PATH=/path/to/AuthKey_XXXX.p8 \
node scripts/asc-metadata.mjs diff --version 1.4.0 --dir ./appstore-metadata
```

The script never loads a `.env` on purpose: in many repos (a mobile app plus
its backend) a `.env` also carries an `APP_STORE_PRIVATE_KEY` for StoreKit or server
notifications, a different key that would silently sign the requests. Keep the
App Store Connect key file out of git and out of any `.env` that is committed.
Take the values from where the project config says they live; never ask the
user to paste a private key in the chat, never print it.

House rules (em dash ban, "free" wording, competitor list, required fields) go
in a rules file: `scripts/rules.example.json` shows the format. Built-in rules
(always on unless `--no-default-rules`): AI preambles ("Here is the optimized
description…", "Hier ist die…"), placeholders (TODO, lorem ipsum, `{{`), and a
warning on markdown syntax, which the App Store shows raw.

## The flow (never skip a step)

1. **Edit the JSON files**, all the locales concerned, not just the primary one.
2. **`check`.** Fix every error. Read the warnings (stray English, short keywords).
3. **Check the version state** (the diff prints it). See `references/asc-states.md`:
   name and subtitle need an app info in `PREPARE_FOR_SUBMISSION`; keywords,
   description, release notes and URLs lock once the version is submitted;
   promotional text can change any time.
4. **`diff`** and show the user, per locale: short fields before / after in full,
   the changed lines of description and release notes, and lengths (name x/30,
   subtitle x/30, keywords x/100, promo x/170). The push sends **every field in
   the file**, so a locale touched only for its release notes also re-sends its
   name and keywords: the diff is how nobody gets surprised.
5. **Wait for an explicit OK.** The push changes a public listing. "Looks good"
   about a draft in the chat is not an OK to push.
6. **`push --yes`** (or the project's own push command if the config names one).
   It re-reads App Store Connect at the end and prints `matches local metadata`
   or the fields that differ.
7. **Report:** files changed, locales, version and its state, pushed or not,
   verify result, and what the user still has to do in App Store Connect
   (screenshots, build, submit). This skill never submits for review.

If the push fails halfway (network, a locale Apple rejects), fix and re-run: it
reads before it writes, so it is idempotent.

## Adding a language

Add `<locale>.json` with every field, using Apple's locale code (`it`, `pl` and
a few others have no region). The push creates the app info localization, which
makes App Store Connect create the version localization too; the script re-reads
before writing, so it works on the first run. New locales show the primary
locale's screenshots until their own are uploaded.

## Release notes and promotional text

Rules in `references/fields-and-rules.md`. In short: write the primary language
first and get it validated, then adapt to each locale; only mention what this
build (or the live web backend) really ships; no rating request unless the
project config says otherwise; promo text is the one field you can refresh
between releases (seasonal hooks, exam periods, holidays).

## Related skills

- `aso-keywords`: find which words to put in name, subtitle and keywords.
- `app-store-screenshots`: the visual half of the listing.
