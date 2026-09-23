# Apple Search Ads Campaign Management API v5, field notes

Base URL: `https://api.searchads.apple.com/api/v5`. Every call carries
`Authorization: Bearer <token>`, `X-AP-Context: orgId=<ORG_ID>` and
`Content-Type: application/json`. `X-AP-Context` selects the org.

Placeholders below: `<ORG_ID>`, `<ADAM_ID>` (the app's App Store id),
`<CREATIVE_ID>` (default product page creative), `<cid>` campaign id, `<gid>`
ad group id. Take the real values from `.claude/paid-ads-config.md`.

## Auth

Identifiers (not secret): client id (SEARCHADS-prefixed, = team id) and key id,
shown in Apple Ads > Account settings > API once the public key is uploaded.
Only the private key is secret; keep it in a git-ignored folder and point
`APPLE_ADS_PRIVATE_KEY_PATH` to it.

1. Client secret = JWT ES256, header `kid = keyId`, claims `iss = sub =
   clientId`, `aud = https://appleid.apple.com`, `iat`, `exp` (≤ 180 days;
   the script uses 1 h).
2. `POST https://appleid.apple.com/auth/oauth2/token`, form-encoded:
   `grant_type=client_credentials`, `client_id`, `client_secret`,
   `scope=searchadsorg`. Returns `access_token`, valid 1 h.
3. Check with `GET /acls`: org name, currency, timezone, role.

Key pair generation (the user uploads the public part themselves):

```bash
openssl ecparam -genkey -name prime256v1 -noout -out keys/apple-ads-private-key.pem
openssl ec -in keys/apple-ads-private-key.pem -pubout   # paste this in Apple Ads > Account settings > API
```

Errors seen:
- `400 {"error":"invalid_client"}`: the private key doesn't match the public
  key registered at Apple. An App Store Connect `.p8` key is a different pair
  and doesn't work here. Regenerate as above; client id and key id stayed the
  same after a regeneration.
- `ModuleNotFoundError: jwt`: no persistent venv. Use `uv run --with pyjwt
  --with cryptography --with requests python …`, or `report.py`'s shebang.

## Reads

| Need | Call |
|---|---|
| Campaigns | `GET /campaigns?limit=200` |
| One campaign | `GET /campaigns/{cid}` |
| Ad groups | `GET /campaigns/{cid}/adgroups?limit=200` |
| Ads of a group | `GET /campaigns/{cid}/adgroups/{gid}/ads` |
| Keywords of a group (ids) | `GET /campaigns/{cid}/adgroups/{gid}/targetingkeywords?limit=1000` |
| Campaign negatives | `GET /campaigns/{cid}/negativekeywords?limit=1000` |
| Creatives | `GET /creatives?limit=20` (usually one `DEFAULT_PRODUCT_PAGE`) |
| Custom product pages | `GET /apps/<ADAM_ID>/product-pages` |
| Eligibility per placement | `POST /apps/<ADAM_ID>/eligibilities/find` `{"conditions":[],"pagination":{"offset":0,"limit":200}}` |
| Campaign report | `POST /reports/campaigns` |
| Ad group report | `POST /reports/campaigns/{cid}/adgroups` |
| Keyword report | `POST /reports/campaigns/{cid}/keywords` |
| Search terms report | `POST /reports/campaigns/{cid}/searchterms` |

`POST /reports/…` and `…/find` are reads.

A report body that works:

```json
{"startTime":"2026-01-06","endTime":"2026-01-12","timeZone":"ORTZ",
 "selector":{"orderBy":[{"field":"impressions","sortOrder":"DESCENDING"}],
             "pagination":{"offset":0,"limit":1000}},
 "returnRecordsWithNoMetrics":false,"returnRowTotals":true,"returnGrandTotals":true}
```

- Dates `YYYY-MM-DD` only. An empty date or one with a time gives
  `INVALID_INPUT … Start date and end date should be in the format: YYYY-MM-DD`.
- `"granularity":"DAILY"`: rows per day in `row[].granularity[]` (grand
  totals must then be off; `report.py --daily` does that).
- `"groupBy":["countryOrRegion"]`: one row per campaign and country.
- `returnRecordsWithNoMetrics: true` on the keyword report includes keywords
  with 0 impressions (`report.py keywords … --all`).
- Response: `data.reportingDataResponse.row[]` with `metadata` and `total`.
  On error `data` is `null` and the error is in `error` or `errors[]`: don't
  chain `.get('data').get(…)` without a guard.

`total` fields (v5): `impressions`, `taps`, `ttr`, `localSpend`, `avgCPT`,
`avgCPM`, `totalInstalls`, `tapInstalls`, `viewInstalls`,
`totalNewDownloads`, `totalRedownloads`, `totalAvgCPI`, `tapInstallCPI`,
`totalInstallRate`, `tapInstallRate`. There is no `avgCPA`: cost per install
is `totalAvgCPI`. `totalInstalls` includes view-through installs (a brand
campaign showed 2 installs for 0 taps over 7 days).

Useful metadata: campaign `campaignName`, `campaignStatus`, `servingStatus`,
`servingStateReasons`, `dailyBudget`, `targetCpa`, `countriesOrRegions`,
`supplySources`; keyword `keyword`, `matchType`, `bidAmount`,
`keywordStatus`; term `searchTermText` (null = hidden low-volume group),
`searchTermSource` (`AUTO` = Search Match, `TARGETED` = via a keyword).

## Writes (only after the user's explicit yes)

Amounts are strings: `{"amount":"0.5","currency":"EUR"}` (use the org's
currency). Tested live:

```bash
# Create a search results campaign (always PAUSED)
POST /campaigns
{"orgId":<ORG_ID>,"name":"FR - Search - Brand","adamId":<ADAM_ID>,
 "countriesOrRegions":["FR"],"dailyBudgetAmount":{"amount":"3","currency":"EUR"},
 "supplySources":["APPSTORE_SEARCH_RESULTS"],"adChannelType":"SEARCH",
 "billingEvent":"TAPS","status":"PAUSED"}
# Search tab: supplySources ["APPSTORE_SEARCH_TAB"], adChannelType "DISPLAY"
# Product pages ("You might also like"): ["APPSTORE_PRODUCT_PAGES_BROWSE"], "DISPLAY"

# Ad group (startTime in UTC, format "%Y-%m-%dT%H:%M:%S.000"; put it ~10 min in the future)
POST /campaigns/{cid}/adgroups
{"name":"Brand","pricingModel":"CPC","defaultBidAmount":{"amount":"0.5","currency":"EUR"},
 "startTime":"2026-01-12T12:10:00.000","status":"ENABLED",
 "automatedKeywordsOptIn":false,
 "targetingDimensions":{"deviceClass":{"included":["IPHONE","IPAD"]}}}
# automatedKeywordsOptIn true = Search Match; omit it for a DISPLAY campaign

# Keywords (bulk)
POST /campaigns/{cid}/adgroups/{gid}/targetingkeywords/bulk
[{"text":"my app","matchType":"EXACT","bidAmount":{"amount":"0.5","currency":"EUR"}}]

# Campaign negatives (bulk)
POST /campaigns/{cid}/negativekeywords/bulk
[{"text":"my app","matchType":"EXACT"}]

# Ad required for the Search tab (otherwise NO_AVAILABLE_ADS)
POST /campaigns/{cid}/adgroups/{gid}/ads
{"creativeId":<CREATIVE_ID>,"name":"Default product page","status":"ENABLED"}

# Enable / pause a campaign (body wrapped in "campaign")
PUT /campaigns/{cid}
{"campaign":{"status":"ENABLED"}}      # or "PAUSED"
```

Not yet exercised in the field, shape from Apple's v5 docs: try on one
object before a loop and re-read afterwards:

```bash
PUT /campaigns/{cid}                                   # daily budget
{"campaign":{"dailyBudgetAmount":{"amount":"7","currency":"EUR"}}}
PUT /campaigns/{cid}/adgroups/{gid}                    # default bid, pause the group
{"defaultBidAmount":{"amount":"0.3","currency":"EUR"}}   # or {"status":"PAUSED"}
PUT /campaigns/{cid}/adgroups/{gid}/targetingkeywords/bulk   # bid or pause keywords
[{"id":<keywordId>,"bidAmount":{"amount":"0.7","currency":"EUR"}}]   # or "status":"PAUSED"
POST /campaigns/{cid}/adgroups/{gid}/negativekeywords/bulk   # ad group negatives
```

A `PUT` on a campaign only changes the fields sent.

Creation scripts are usually not idempotent: a "plan" script that creates
ten campaigns will create ten more if re-run. Keep such scripts, but never
re-run them; write a small new one for each new campaign.

## Observed behaviours

- The daily budget can be exceeded: 156 % of it on one day (10.89 for 7),
  120 % the next day on another campaign. Reason in maximum cumulative
  spend, not a strict cap.
- Automatic campaign with a very low `targetCpa`: Apple bids at the floor
  and barely serves; with several countries it goes wherever the bid passes.
- Today tab: eligible on iPhone but requires a custom product page. iPad
  Today tab: `INELIGIBLE`.
- Right after creation, a DISPLAY ad group without an ad shows `NOT_RUNNING`
  / `NO_AVAILABLE_ADS`, and the campaign `NO_AVAILABLE_AD_GROUPS`. The
  product-pages placement did not need an explicit ad.
