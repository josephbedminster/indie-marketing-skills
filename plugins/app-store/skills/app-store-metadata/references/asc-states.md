# App Store Connect: what can be edited when

App Store Connect splits the listing into two objects, each with its own state.

## App info (per app): name, subtitle, privacy policy URL

- `GET /v1/apps/{appId}/appInfos` returns one or two app infos: the live one
  (`READY_FOR_DISTRIBUTION`) and, while a new version is being prepared, an
  editable one (`PREPARE_FOR_SUBMISSION`).
- **Name, subtitle and privacy URL can only change on the editable app info.**
  No version in preparation means no editable app info: create the next version
  in App Store Connect first (a version number is enough, no build needed).
- Once the version is submitted (`WAITING_FOR_REVIEW`, `IN_REVIEW`), the app info
  is locked until the review ends. A push at that moment is refused: move the
  change to the next version.
- A rejected version (`DEVELOPER_REJECTED`, `REJECTED`, `METADATA_REJECTED`)
  unlocks it again.

## Version localizations: keywords, description, whatsNew, URLs, promo text

- `GET /v1/apps/{appId}/appStoreVersions?filter[versionString]=X` gives the
  version and its `appVersionState`.
- Editable while `PREPARE_FOR_SUBMISSION` (or after a rejection). Locked in
  `WAITING_FOR_REVIEW`, `IN_REVIEW`, `PENDING_DEVELOPER_RELEASE`,
  `READY_FOR_DISTRIBUTION`.
- **Exception: `promotionalText`** can be patched on the live version at any
  time. The script allows `push --fields promotionalText` on a live version and
  refuses any other field there.
- `whatsNew` cannot be set on the first version of an app.

## New locales

- Creating an app info localization (POST) makes App Store Connect create the
  matching version localization by itself. A script that then POSTs the version
  localization gets a conflict. `asc-metadata.mjs` re-reads the version
  localizations after each creation and PATCHes instead: the push is idempotent
  and can be re-run after a partial failure.
- A new locale needs all its fields at once (name at least for the app info).
- It shows the primary locale's screenshots until its own are uploaded.

## Locales on App Store Connect without a local file

The script leaves them untouched and `diff` lists them. Removing a locale is
done by hand in App Store Connect, never by the script.

## Reading what is live

- `diff` / `verify` on the live version number compare the JSON with what is
  online (the live app info is used when none is editable).
- Search tools (aso-mcp, the public store) read the **published** listing only.
  Metadata pushed on a version still in preparation is invisible to them.

## API key

- App Store Connect > Users and Access > Integrations > App Store Connect API.
  A team key with the App Manager role is enough for metadata.
- The `.p8` file downloads once. Store it outside git (a `keys/` folder in
  `.gitignore`, or a password manager), never in a committed `.env`.
- The issuer id, key id and app id are identifiers, not secrets, but keep them
  out of public repos anyway.
