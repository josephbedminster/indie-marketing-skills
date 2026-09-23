---
name: decision-model-batch
description: Run massive closed questions (classify, filter, tag, route, score, yes/no, link or not) over hundreds or thousands of items at near-zero cost with a typed decision model instead of a text LLM - Jev by TypeSafe through OpenRouter (`typesafe/jev-1.13`, endpoint POST https://openrouter.ai/api/alpha/decisions, not chat/completions). Covers the exact call format, the three question types (noul, choice, score), how to write questions, stacking dozens of questions per call, calibrating on a sample then deciding in code with explicit thresholds, caching raw probabilities, cost and throughput, and the pitfalls. Use it whenever a task is "the same closed question N times", when the user mentions Jev, TypeSafe or a decision model, or complains about what an LLM costs on a bulk job, even if they just say "classify all these" or "filter this list".
---

# Decision model batches

A decision model generates nothing. You send a `state` (text) and typed
questions; it returns typed answers with calibrated probabilities. On
OpenRouter, Jev costs $0.042 per million input tokens, output is free, and an
answer takes about 0.4 s: 40 to 200 times cheaper than a text LLM. It is
excellent at repeated closed judgments and useless for anything that needs a
sentence written.

The split that works: **code finds candidates, the model judges, code
decides.** Never ask it "find", ask it "is it true that".

## Before you start

If `.claude/seo-config.md` exists, read its **Decision model** section: the
project may already have a client with retries and caching. Reuse it. If the
file is missing and you write a new client, create the file from
`../pseo-internal-linking/references/config-template.md` and fill at least
that section, so the next job finds the client. Read the **Project
conventions** of `.claude/posthog-funnel-map.md` if present.

## The call

A dedicated endpoint, **not** `/chat/completions` (which returns 400 for a
decisions model):

```text
POST https://openrouter.ai/api/alpha/decisions
Authorization: Bearer $OPENROUTER_API_KEY
Content-Type: application/json

{
  "model": "typesafe/jev-1.13",
  "state": "…the text to judge, up to ~30,000 tokens…",
  "questions": {
    "is_urgent": { "type": "noul",   "instructions": "The message expresses urgency." },
    "team":      { "type": "choice", "instructions": "Which team should handle it?",
                   "criteria": { "billing": "payments, invoices, refunds", "tech": "bugs, errors, login" } },
    "anger":     { "type": "score",  "instructions": "Level of anger",
                   "criteria": ["calm", "annoyed", "furious"] }
  }
}

→ {
  "answers": {
    "is_urgent": { "noul": 0.97 },
    "team":  { "choice": "billing", "probabilities": { "billing": 0.8, "tech": 0.2 }, "confidence": 0.6 },
    "anger": { "score": 1.03, "confidence": 0.84 }
  },
  "usage": { "input_tokens": 318, "output_tokens": 38, "cost": 0.0000134 }
}
```

- `noul`: probability (0..1) that the statement is true. The default choice:
  keep the threshold in code.
- `choice`: one option among `criteria` (key → description). Good for a
  language, a category, a route. `criteria` is required.
- `score`: a float index on an ordered scale.

Minimal client (Node 18+):

```ts
async function ask(state: string, questions: Record<string, unknown>) {
  for (let attempt = 0; attempt < 6; attempt++) {
    if (attempt) await new Promise((r) => setTimeout(r, 800 * 2 ** attempt));
    const res = await fetch('https://openrouter.ai/api/alpha/decisions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'typesafe/jev-1.13', state, questions }),
    });
    const json = await res.json();
    if (res.ok && json.answers) return json;
    if (res.status < 500 && ![408, 429].includes(res.status)) throw new Error(JSON.stringify(json));
  }
  throw new Error('decision call failed');
}
```

In a latency-sensitive path (an edge function answering a user), use a short
timeout (2-3 s) and let the caller pick a fallback on failure.

Docs: `https://docs.typesafe.ai/llms.txt` (quickstart, primitives, patterns).

## Writing questions

- **One question = one statement checkable in the state.** Put in the
  instruction what must make the answer "no" ("Answer no if the relation is
  only thematic or another discipline"). The model calibrates on what you
  describe.
- **Write instructions in the language of the content.** French state, French
  questions.
- **Stack questions in one call.** They are evaluated in parallel and you pay
  for the state once. 40 questions on a 9,000-character state works fine.
  Speculative fan-out: also ask the questions you are not sure you'll need,
  and let the code sort them out.
- **Number the keys** (`rel_0`, `anc_0`, `rel_1`…) and keep the candidate list
  in code to map answers back.
- **Give the full context once, in the state**: document type, metadata
  (category, level), outline, then the body cut to a fixed budget. Only put
  in a question what is specific to it (the target, the sentence).
- **The model only sees the state.** If a fact is not there (for example the
  language a lesson teaches), it guesses. Ask for it explicitly with its own
  question rather than inferring it from another answer.

## Calibrate, then decide in code

1. **Sample**: 40 items drawn at random with a fixed seed, one call each.
   Costs about a cent.
2. **Cache every raw answer** (probabilities, not decisions) with a
   `promptVersion`. Every later tuning becomes free; changing an instruction
   invalidates the cache.
3. **Sensitivity table**: for each threshold from 0.5 to 0.9, count what
   passes and how many items end with no positive decision. Look for the
   elbow.
4. **Read 30 to 40 positive decisions** at the candidate threshold, with
   their context. Errors are almost always systemic (a class of candidates to
   exclude, a language rule, a formatting case) and are fixed in candidate
   selection or in the instruction, **never by raising the threshold "to be
   safe"**.
5. **Decide in code** with explicit thresholds and caps (max per item,
   dedupe, prefer the closest). Thresholds are command-line parameters.
6. Run on everything, then publish a report: counts, sensitivity table, a
   sample to read, the refused items. Refusals are a feature: the model says
   no when nothing fits.

Thresholds observed on an internal-linking job: 0.8 on a large corpus, 0.75
on a small one (fewer competing candidates, lower probabilities).

## Cost and throughput

`cost = input_tokens × 0.042 / 1,000,000`. A 9,000-character state is about
2,500 tokens, about $0.0001 per call, questions included. Field example:
3,642 pages × 33 questions = $1.17. Concurrency 24 without any rate limit
observed; the bottleneck becomes your local code (retrieval), not the API.

## Pitfalls

- `chat/completions` with a `typesafe/*` model returns 400. The model's
  `supported_parameters` is empty: don't send `temperature`, `messages`,
  `response_format`.
- `state` is required; `prompt` and `messages` are not accepted on the
  decisions endpoint.
- Probabilities are comparable only for identical prompts: version your
  prompts, never mix two caches.
- A `choice` question without `criteria` is rejected.
- Don't use it to write, summarize or extract free text. Use a text LLM for
  that, and the decision model to filter what the LLM should process.
