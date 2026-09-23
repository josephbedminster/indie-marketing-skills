---
name: pseo-internal-linking
description: Internal linking for programmatic SEO sites with thousands of generated pages (lessons, glossaries, city pages, recipes, docs) - candidate retrieval in code (TF-IDF plus labels of other pages already written in the text), a cheap decision model answering two closed questions per candidate, deterministic decisions in code (thresholds, caps, same language, closest level), links placed at render time only on anchors that already exist in the text, a cached audit you can re-tune for free, a report to read before applying, and the sitemap rule that keeps thin pages out. Use it whenever pages are generated or regenerated, a new language or country is added, or the user talks about internal links, orphan pages, "related articles", previous / next links, link juice, "Discovered, currently not indexed", or the sitemap of generated pages, even if they only say "relink the new pages" or "rerun the interlink".
---

# Internal linking for programmatic SEO

At a few thousand pages nobody links by hand, and an LLM that "adds relevant
links" invents sentences, links to the wrong level and costs real money. The
approach that works splits the job three ways:

**code finds candidates → a decision model answers closed questions → code
decides.**

The decision model is a typed classifier (see the `decision-model-batch`
skill of this plugin for the call format and calibration method). At fractions
of a cent per page, the whole corpus costs about a dollar.

## Before you start

Read `.claude/seo-config.md`: where pages live, the audit / apply commands,
thresholds already chosen, the sitemap script, the Search Console property.
Missing? Ask at most five questions in one message (where the page content
lives and in which format; how pages are rendered; which languages or
countries; whether a linking script already exists; how Search Console is
accessed), then write it from `references/config-template.md`. Read the
**Project conventions** of `.claude/posthog-funnel-map.md` if present.

## Architecture

### Audit (paid, cached)

1. **Load the corpus**: id, URL, title, level or tier if any, category, a
   category family (subjects grouped by family through regex rules), section
   headings, plain text, word count.
2. **Retrieve candidates in code**, per page:
   - TF-IDF neighbours (top ~12), limited to nearby levels (distance ≤ 2);
   - **mentions**: titles of other pages already written in this page's text.
     Build anchor phrases from each title: strip leading articles, split on
     "and / or / : / ,", keep phrases of 2+ content words, or a single long
     word (7+ letters) only when the title used it as a noun with an article
     and it is not on a generic-words list ("introduction", "vocabulary",
     "numbers"…). Cheap prefilter (every stem present) before any regex;
   - when the same anchor could point to the same topic at several levels,
     keep the closest levels (~10 mention candidates max).
3. **One decision call per page.** The state is the page itself (type of
   document, level, category, title, outline, then the body cut to a fixed
   budget such as 9,000 characters). Two closed questions per candidate:
   - `rel_i`: "A reader of this page has a real reason to also open
     '<target title>' (<level>, <category>; outline: …): it is a direct
     prerequisite, the direct continuation, or a notion explicitly used here.
     Answer no if the relation is vague, only thematic, or another discipline
     or language."
   - `anc_i` (only when an anchor was found): "In the sentence '<sentence>',
     the words '<anchor>' designate precisely the notion taught in
     '<target title>', so a hyperlink on these words to that page would be
     natural and useful."
   Write the questions in the language of the content. For language-learning
   pages, add one `choice` question "which language does this lesson teach?".
4. **Cache the raw probabilities per page**, with a `promptVersion`. Never
   cache decisions: thresholds change, probabilities don't.

### Decide (free, deterministic)

- Accept a candidate when `rel ≥ threshold` and languages are compatible (a
  language lesson only links to lessons of the same language).
- Rank accepted candidates by `rel - 0.05 × level distance` (closest level
  wins).
- Inline link only when `anc ≥ threshold`, with caps: ~6 inline per page,
  ~2 per section, no two overlapping anchors.
- A "related" block (~6) gets the accepted candidates not linked inline
  first.
- Previous / next inside the same category and level come from the order,
  not from the model.
- Thresholds are command-line flags, never constants.

### Apply (deterministic, no model)

- Write a structured field (inline, related, prev, next) into each page's
  data, never rewrite the text. The page renderer places each inline link on
  the anchor text **that already exists** in the body.
- Why: a link is never an invented sentence (nothing for anyone to proofread),
  and when a page is regenerated, anchors that disappeared simply drop. Apply
  re-checks every anchor and reports the dropped ones.
- Keep a `--revert` that removes the field everywhere.

## When to rerun

After any content change: new language, regenerated pages, merged
categories. The audit only calls the model for pages without a cache entry:

- new pages: nothing to do, they get audited;
- **regenerated pages: delete their cache file first**, or they keep
  decisions made on the old text (their old anchors drop at apply, and new
  anchors are never found);
- changed question wording: bump `promptVersion`, the whole cache is ignored.

## Run

```text
audit --sample=40              # calibration on a fixed-seed random sample, about a cent
audit --concurrency=24         # full run
audit --decide-only --rel=0.8 --anc=0.8   # re-tune from cache, free
apply --dry-run
apply
```

## Read the report before applying

The audit writes a report with everything needed to decide without paying
again:

1. **Sensitivity table**: accepted targets, inline links and pages with no
   target for each threshold from 0.5 to 0.9. Find where refused pages take
   off.
2. **A sample of 40 inline links with their source sentence. Read them.**
   This is where systemic defects show: mixed languages, an anchor inside a
   table header, a lone adjective, a level jump. **Fix a systemic defect in
   code** (forbidden patterns, anchor extraction, language filter), **not by
   raising the threshold**.
3. **Most-linked pages**: a page with 100 inbound links usually has a title
   that is too generic ("Numbers").
4. **Refused and orphan pages**: normal. The model says no when nothing fits,
   that is the point. Only worry if an entire category is refused: that is a
   content problem, not a threshold problem.

Thresholds seen in practice: **0.8 / 0.8 on a large corpus**; **rel 0.75 on a
small one**, because obvious links fall under 0.8 when fewer candidates
compete. Between 0.75 and 0.8 on the large corpus, anchors were weak (single
generic nouns).

## Verify

- Apply reports `0 inline dropped` on a fresh corpus (drops right after a
  regeneration are expected, see cache above).
- In a preview, count the inline links and the related block in the DOM;
  the console is clean.
- After the production build, grep a built page's static HTML for the link
  `href`s: **the static HTML must contain the links**, that is what Google
  reads. Client-only links are worth much less.

## Sitemap and thin pages

Generate the sitemap at build time and **exclude pages whose body is under
~600 words**: in the field, those are the ones Search Console left as
"Discovered, currently not indexed". Log how many are excluded, keep an env
opt-out. To bring them back: regenerate them longer, delete their audit cache,
rerun audit + apply, rebuild. Then resubmit the sitemap in Search Console (same
URL, it only speeds up the recrawl).

## Field notes (one education site, anonymized)

- Large corpus: 3,642 pages, about 120,000 questions, $1.17, 26 minutes. The
  time was local CPU (mention detection), not the API. Concurrency 24, no
  rate limit.
- Small corpus: 1,206 pages, about 30,000 questions, $0.31, 48 seconds.
- Result on the large corpus at 0.8 / 0.8: ~2,300 inline links, ~15,700
  related links, ~325 refused pages.
- Side finding worth more than the links: the language question revealed
  that 708 of 1,157 foreign-language lessons were actually about the site's
  native language (pages generated without a target language). The decision
  model is also a cheap content audit.
- A new language needs its own config: questions in that language,
  stopwords, articles to strip from anchors, category-family rules, the
  language question and the native language.
