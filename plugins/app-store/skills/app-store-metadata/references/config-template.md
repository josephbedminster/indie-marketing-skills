# Project config template: `.claude/app-store-config.md`

All three skills of this plugin (app-store-metadata, aso-keywords,
app-store-screenshots) read this file first. It is private to the project: it
holds identifiers, paths and house rules, never secret values. Commit it only
if the repo is private.

## Questions to ask when the file is missing (one message, propose defaults)

1. **App:** App Store app id (the number in the App Store Connect URL), bundle id,
   primary locale, and the store locales you publish (or "read them from App
   Store Connect").
2. **Metadata files:** where the per-locale JSON files live (default
   `./appstore-metadata/`), and whether a project script already pushes them
   (then it stays the canonical push; this plugin's script can still `check`
   and `diff`).
3. **Credentials:** where the App Store Connect API values live (password
   manager, a private note, CI secrets) and the path of the `.p8` file. Never
   paste the key content in the chat.
4. **Copy rules:** tone (formal or informal "you"), banned characters or words
   (em dash, "free", exclamation marks), rating request in release notes or not,
   paid from day one or free tier / trial.
5. **Markets and competitors:** priority countries, direct competitors (for
   research only: never in keywords), and whether a screenshot pipeline exists.

## Template

```markdown
# App Store config
Updated: <YYYY-MM-DD>

## App
App id: <1234567890>. Bundle id: <com.example.app>. Primary locale: <en-US>.
Store name: <Brand: Main Keyword>. Categories: <EDUCATION / PRODUCTIVITY>.
Store locales (<N>): <en-US, en-GB, fr-FR, …>.

## Metadata
Files: <./appstore-metadata/<locale>.json>.
Canonical push: <plugin script | project command `npm run …`>.
Plugin script run: <node <path>/asc-metadata.mjs check --dir … --rules …>.
Rules file: <path or "defaults">.
Credentials: <where the values live>; key file <path, outside git>. Env on the
command line only: <why, e.g. a .env holds another APP_STORE_PRIVATE_KEY>.
Current version: <X.Y.Z, state, date>.

## Copy rules (validated by the owner)
- Tone: <…>. Bullets: <•>. Name format: <Brand: …>.
- Banned: <em dash, "free" wording, …>.
- Release notes: <structure, closing line, rating request yes/no>.
- Pricing: <paid from day one / free tier / trial length>; subscription block <…>.

## Markets and keywords
Priority markets: <FR, US, …> (source: <analytics, date>).
Competitors to watch (research only, never in keywords): <…>.
Reference rankings: <table or path to the latest research notes>.
Research notes saved to: <docs/aso/…>.

## Screenshots
Pipeline: <none, uploads by hand | tool, command, source of truth>.
Sizes exported: <iPhone 6.5" 1284×2778, iPad 13" 2048×2732>.
Locales with their own screenshots: <…>; the others inherit the primary.
Pitfalls: <…>.

## Related tools and skills
<release skill, preview video, ads skills pointing at the listing, design tool>.

## History
<YYYY-MM-DD: version X pushed, what changed>
```

Keep it under 150 lines. Add a **History** line after each push or research
round: the next change needs to know what was tried and when.
