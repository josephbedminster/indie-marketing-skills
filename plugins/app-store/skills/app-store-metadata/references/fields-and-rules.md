# Fields, limits and writing rules

## Fields

| Field | Limit | Lives on | Indexed by search | Editable when |
|---|---|---|---|---|
| `name` | 30 | app info localization | yes | app info in `PREPARE_FOR_SUBMISSION` |
| `subtitle` | 30 | app info localization | yes | same |
| `privacyPolicyUrl` | 255 | app info localization | no | same |
| `keywords` | 100 | version localization | yes | version not yet submitted |
| `description` | 4000 | version localization | no | version not yet submitted |
| `whatsNew` | 4000 | version localization | no | version not yet submitted (not on the very first version) |
| `marketingUrl`, `supportUrl` | 255 | version localization | no | version not yet submitted |
| `promotionalText` | 170 | version localization | no | **any time**, even on the live version |

`scripts/asc-metadata.mjs check` enforces the limits and the mechanical rules
below. It cannot judge tone, translation quality or truthfulness: you do.

## Name and subtitle

- Brand plus the main query: `Brand: Main Keyword Phrase`, 25 to 30 characters.
  A name that only says the brand ranks on the brand only.
- Keep the same structure across locales, translated to the query people type
  in that market (not a literal translation of the English query).
- Punctuation follows the language (French puts a space before the colon).
- No price, no "free", no "best", no "#1", no competitor names.

## Keywords field

- 94 to 100 characters used out of 100. Every unused character is lost reach.
- Commas, **no spaces** (`tutor,exam,math`). A space after a comma costs a
  character.
- **No word already in the name or subtitle**: they are indexed already.
  Apple combines words across the three fields, so `math` in keywords plus
  `Homework Helper` in the name also covers "math homework helper".
- Singular or plural, not both, unless the market searches both differently.
- Keep accents and native spelling (`révision`, `prüfung`).
- **No competitor brands** (App Review guideline 2.3.7): a rejection, and
  sometimes a warning on the account.
- No category names or generic words Apple adds anyway (`app`, `iphone`).
- One storefront can index several locales (in the US, Spanish (Mexico) is
  indexed alongside English (U.S.)). Use the secondary locale's keywords field
  for **different** words, not a copy.
- Local vocabulary per storefront: school levels and exams differ by country
  (examples: GCSE / A level in the UK, ATAR / HSC in Australia, ENEM /
  vestibular in Brazil, bachillerato / ESO in Spain, Abitur in Germany,
  matura in Poland, maturità in Italy, cégep in Québec). Same for money,
  measures, seasons and the everyday word for the core job.

## Description

- The first 2 or 3 lines are all a visitor sees before "more": the hook goes
  there, not a blank line and not the brand history.
- Then feature bullets (`•`), why it works, who else it is for (parents,
  teams), coverage (levels, countries, platforms).
- **Subscription block** for auto-renewable subscriptions: plans, prices shown
  in the app before purchase, auto-renewal unless cancelled at least 24 hours
  before the end of the period, managed in the Apple account settings, links to
  terms and privacy policy.
- **Never promise free if the app is paid from the start** (no "free plan",
  "free trial" if there is none, "gratis", "kostenlos"). App Review rejects it
  (2.3.1) and users leave 1-star reviews. Put the ban in the rules file.
- No markdown: `**bold**`, `#` headings and `---` show as raw characters.
- Pick one voice (addressing the user, or their parent / manager) and keep it
  in every field and every locale.

## Translation checklist (every non-primary locale)

- **No stray English sentences.** Machine-translated descriptions often keep
  English SEO phrases ("revision notes for exams", "daily study planner"). The
  check warns when a non-English description contains many common English
  words; read it anyway.
- **No AI preamble.** "Here is the optimized description:" (or "Hier ist
  die…", "Voici…") followed by `---` has shipped to live listings. The default
  rules reject it.
- House style bans (em dash, exclamation marks…) survive translation badly:
  models add them back. Keep them in the rules file so the check catches them.
- Adapt, do not translate: levels, exams, examples, and the query people type.
- Same facts in every locale: prices, trial, feature list.

## URLs

- Open every URL once before pushing. A marketing URL without a trailing slash
  (`https://example.com/fr`) can 404 while `https://example.com/fr/` works; the
  check warns about missing trailing slashes.
- Privacy policy URL is required. Point it at the locale's page if it exists.
- After a rebrand or a domain change, grep the JSON for the old domain.

## Release notes (whatsNew)

- Written for users, not a changelog: a one-line hook, then 3 to 6 bullets of
  what they can now do, then an optional "also improves stability" line.
- Only what this version really ships. If the app shows web content (WebView),
  a feature deployed on the web is visible without a build, a native feature is
  not: check the git log of both before listing a feature.
- Default: no rating request in release notes ("Enjoying the app? Leave a
  review"). It reads as begging and belongs in the in-app review prompt.
- Primary language first, validated by the owner, then adapted to each locale.
  "In all languages" means every store locale, not only the ones with
  screenshots.
- Not accepted on the first version of an app.

## Promotional text

- 170 characters, shown above the description, not indexed.
- Changeable without a new version: use it for seasons (exam period, back to
  school, holidays), a launch, or a new feature. Push it alone with
  `--fields promotionalText`.

## Categories

The push can set the secondary category (`--secondary-category PRODUCTIVITY`,
IDs are Apple's category IDs). A secondary category puts the app in a second
chart; pick one the app genuinely fits.
