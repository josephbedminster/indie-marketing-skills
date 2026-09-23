# TikTok Ads Manager UI tips (browser tool)

- **Open**: navigate to the full URL (`https://ads.tiktok.com/i18n/…`), wait
  8-9 s before reading. A side browser pane is ~800 px wide: apply
  `document.documentElement.style.zoom='0.6'` through the JavaScript tool
  after each navigation to see the whole page (redo it on every URL change).
  Viewport emulation makes clicks unreliable; prefer the zoom.
- **Popups**: "Announcement / A better way to navigate" and "Got it" come
  back on every page; close them first (click "Got it" or the cross),
  otherwise clicks land on them.
- **Read the page**: the JavaScript tool with
  `document.body.innerText.replace(/\n+/g,' | ')` is more reliable than
  page-text or accessibility-tree tools (shadow DOM). Mask long tokens before
  printing them.
- **Click**: `find` returns refs usable even inside the shadow DOM; otherwise
  coordinates after a screenshot. Dialog footer buttons fall outside the frame
  without zoom (click the visible edge, near the right border).
- **Simplified → full mode**: "Switch to full version" button at the bottom of
  the Objectives page; the confirmation dialog takes 2-4 s to appear, then
  "Confirm".
- **Useful URLs** (replace `<aadvid>` with the advertiser id from the config):
  - Campaigns: `/i18n/manage/campaign?aadvid=<aadvid>&st=…&et=…`; ad groups
    `/i18n/manage/adgroup`; ads `/i18n/manage/ad`.
  - Create: `/i18n/creation/1nn/create/campaign?aadvid=<aadvid>`.
  - Events Manager: `/i18n/events_manager/home?aadvid=<aadvid>`, app detail
    `/i18n/events_manager/app/detail/<App Store id>?aadvid=<aadvid>`
    (Settings tab > Show App Secret).
  - Payment: `/i18n/account/payment?aadvid=<aadvid>` (the user acts there).
- **Text fields**: triple-click + `cmd+a` then type (fields are web
  components). After typing, the layout shifts: take a new screenshot before
  the next click. TikTok's AI assistant opens a suggestion menu under the
  text field; click elsewhere to close it.
- **Creative picker** ("Edit selections"): "Recommended" tab = 3 groups (Your
  own / Creator / Auto-generated) to set to "Don't add"; "Creative library"
  tab = one checkbox per video; "Save" bottom right.
- **Edit an existing ad**: Ad tab > hover the row > "Edit" (a link that
  appears under the name); the panel closes if you navigate, and everything
  is lost.
- **Duplicate an ad group**: copy icon that appears on hover of the row in
  the left rail of the creation flow; the copy keeps the ad, then rename and
  change age and videos.
- **Secrets copied by the page** (App Secret) land in the OS clipboard. Never
  print them: on macOS, a small script reads `pbpaste` and writes the value
  where it belongs (e.g. an env file), then `printf '' | pbcopy` clears the
  clipboard.
