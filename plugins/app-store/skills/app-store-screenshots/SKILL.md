---
name: app-store-screenshots
description: Plan, produce, translate and check iPhone and iPad App Store screenshot sets that App Store Connect accepts - the right pixel sizes (6.5-inch 1284x2778 or 1242x2688, iPad 13-inch 2048x2732), locale coverage and inheritance, translated captions checked visually per language, and no unverifiable claims that App Review can reject. Use it whenever the user talks about App Store screenshots, store slides, captions, "redo the screenshots in Italian", an upload refused for its size, or a new screenshot series, even if they don't say "screenshots". If the project has its own screenshot pipeline, this skill follows it. Not for the app preview video or for the listing text (app-store-metadata).
---

# App Store screenshots

## Step 0: context

Read `.claude/app-store-config.md`. If it describes a screenshot pipeline
(a studio, a design tool export, a render script), **follow it**: its commands,
source of truth and pitfalls win over this file. Missing config: follow
`../app-store-metadata/references/config-template.md`. If
`.claude/posthog-funnel-map.md` exists, read **Project conventions** (copy
style bans apply to captions too).

## Sizes App Store Connect accepts

| Slot | Accepted sizes (portrait) | Notes |
|---|---|---|
| iPhone 6.5" | **1284×2778** or **1242×2688** | the slot most listings fill |
| iPhone 6.9" | 1290×2796 (and 1320×2868) | **refused where 6.5" is expected** |
| iPad 13" | **2048×2732** | required if the app runs on iPad |

A design canvas at 1290×2796 must be exported to 1284×2778 for the 6.5" slot:
scale X and Y separately rather than cropping. After export, check each file
(`sips -g pixelWidth -g pixelHeight file.png` on macOS): exact size, no white
band, nothing cropped on the four edges.

Up to 10 per set. The first 3 show in search results: put the strongest
promise and the core job there.

## Locales

- Every store locale can have its own set. **A locale without screenshots
  shows the primary locale's set**, so regional variants (en-GB, en-AU,
  es-MX, fr-CA, pt-BR…) inherit until you upload theirs.
- Translate captions **from English** for non-primary locales when the source
  language is not English (a French source translated straight to Polish
  loses more than French to English to Polish). Validate the source and the
  English first, then the rest.
- Adapt, do not translate: school levels, exams, currencies, local examples,
  as in the listing text.
- **Look at every locale rendered.** German, Polish and Dutch run 20 to 40 %
  longer and overflow onto mockups; models reintroduce banned characters (em
  dashes) and English words; numbers need local formats.
- Translation with an LLM costs credits per screen and locale: translate one
  slide, check, then batch.

## Captions

- Captions are not indexed by search; they confirm the visitor is in the right
  place. Put the ASO keyword in a small kicker and a concrete gain in the title.
- Short: one line of kicker, two of title.
- **No number you cannot prove** ("100,000 users", "4.9 stars", "1M courses")
  while the listing shows a handful of ratings: App Review guideline 2.3.1
  (accurate metadata) risk. Flag every new unverifiable number to the owner and
  let them decide.
- Same rules as the listing: no competitor names, no "free" if the app is paid.

## Upload

Uploads are done by the user in App Store Connect (version in preparation,
per locale and per size). Give them the list: which locale gets which folder,
which slots. Offer an API upload script (`appScreenshotSets`,
`appScreenshots` with reserve / upload / commit) only if they ask for one.

Read what is already online (GET only) with the App Store Connect API
(`/v1/appStoreVersionLocalizations/{id}/appScreenshotSets?include=appScreenshots`)
before replacing a set, when credentials are set up for app-store-metadata.

## Report

Series and locales exported, sizes checked, locales still inheriting the
primary set, numbers flagged, and what the user must upload where.
