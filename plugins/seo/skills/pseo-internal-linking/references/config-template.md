# SEO config
Project: <product / site>. Updated: <YYYY-MM-DD>.
Private file: identifiers and paths are fine here, secrets never (API keys and
service-account keys stay in files or env vars; this file says where).
Read by the `seo` plugin skills: pseo-internal-linking, decision-model-batch.

## Site and corpus
Site: <https://example.com>. Page pattern: <https://example.com/lessons/<country>/<level>/<subject>/<chapter>>.
Corpus per language / country: <fr: N pages, es: N pages…>. Where page content lives: <bundles JSON / markdown / DB>, path <…>.
Also published to: <public folder the site builds from, if copied>.
Rendering: <component that renders the body>, <component that shows related links / prev-next>.

## Scripts and commands
Run from: <folder>. API key env var: <OPENROUTER_API_KEY> in <path>.
Audit: <command> (flags: sample, concurrency, decide-only, thresholds, country).
Apply: <command> (dry-run, revert). Outputs: <report.md, links.csv, link-map.json, cache/> in <path>.
Prompt version constant: <file#CONST>. Cache file naming: <pattern>.
Per-language config (questions, stopwords, articles, subject families, language question): <file#CONST>.
Systemic-error fixes live in: <forbidden patterns, anchor extraction, language filter function names>.
Anchor matching at render time: <shared module>.

## Thresholds in use
| Corpus | rel | anc | Why | Date |
|---|---|---|---|---|
| <fr> | <0.8> | <0.8> | <large corpus> | <…> |

## Reference numbers
| Corpus | Pages | Questions | Cost | Time | Inline | Related | Refused | Orphans |
|---|---|---|---|---|---|---|---|---|
| <…> | | | | | | | | |

## Sitemap and indexing
Sitemap script: <path>, run by <prebuild>. Thin-page threshold: <600 words>. Opt-out env: <VAR=0>.
Regenerating thin pages: <command / neighbour skill>.
Search Console: property <…>, access via <MCP connector / service-account key path>.
Build + static HTML check: <command>, <file to grep>.
Preview for manual checks: <launch config name>, selectors <inline links, related block>.

## Decision model
Model: <typesafe/jev-1.13>. Endpoint: <https://openrouter.ai/api/alpha/decisions>.
Existing clients in the codebase: <paths, function names, timeouts, retry policy>.

## Known content issues
<e.g. N language lessons classified as the wrong language: content problem, not a linking problem>

## Project conventions
Report language: <…>. Neighbour skills: <country rollout, content regeneration…>. Where decisions are logged: <…>.

## History
<YYYY-MM-DD: corpus X linked at rel/anc, N inline, sitemap resubmitted>
