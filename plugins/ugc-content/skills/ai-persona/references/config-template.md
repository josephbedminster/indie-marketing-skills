# UGC config
Project: <product name>. Updated: <YYYY-MM-DD>.
Private file: identifiers, paths and account names are fine here, secrets never
(API keys stay in env files; this file only says where they are).
Read by the `ugc-content` skills: ai-persona, image-prompt-porting, ugc-video-ad.

## Product and audience
What the product is, in one line: <…>. Audience: <students 16-20, parents…>.
Content language(s): <…>. If `.claude/posthog-funnel-map.md` exists, its
Business profile wins; only add what it lacks.

## Keys and how scripts run
API provider: <OpenRouter / other>. Key env var: <OPENROUTER_API_KEY> in <path/.env> (git-ignored).
Scripts run from: <folder>, because <they import the env loader from there>.
Env loading pitfall: <e.g. the loader must be called, importing it is not enough>.

## Image pipeline (carousels, stills)
Location: <path>. Start: <command>. Docs: <path to its README / CLAUDE.md>.
Prompts live in: <prompts/ folder>. Face prompt: <file> + per-shot fragments <pattern>.
Placeholder filler / escaper: <function name>. Prompt loader behaviour: <refuses leftover {{X}}…>.
Data check: <command>. Typecheck: <command>. Print a prompt without paying: <command>.
Persona commands: portrait <command, flags>, test shot <command, flags>.

## Personas / accounts
| Account or series | Format / style | Face shown? | Face text lives in | Reference portrait | Age |
|---|---|---|---|---|---|
| <id> | <selfie / POV / design> | <yes / never (POV)> | <file#field> | <path> | <18+> |

Face shot types (get the reference image): <list>. All other shots: <no person at all>.
Where old portraits are kept: <resource library, never deleted without asking>.

## Shot types
Enum / schema: <file#CONST>, face subset: <CONST>. Viewfinder text: <file#CONST>.
Guard (where a shot type is allowed): <file#function>.
Planner prompts that must list every shot type: <files>. Tool descriptions: <file>.
UI: <file, filtered by …>. Model per format: <file#field>, model list: <file>.
Project doc line to update: <file, section>.

## Models, cost, time
Image (face shots): <model id>, <~80 s / image>, <output size>. Other shots: <model>.
Image-to-video: <model id>, <duration>, <~cost / clip>, <~time / clip>.
Music: <model id>, <cost>. Voice (if any): <model id, status>.

## Video ad pipeline
Location: <path>. Variants file: <path> (schema below or link). Assets: <layout>. Outputs: <path pattern>.
Commands: photos <…>, clips <…>, render <…>, check frames <…>, audio only <…>, preview <…>.
Timeline: <duration, segments with times>. App demo embed: <file, how it is served, port>.
Localized demo files: <pattern>. Sound design / music volume constants: <file#consts>.

## Brand invariants (validated by the founder, do not re-discuss)
- Product appears: <only at the end / only on the CTA slide>. Never the hook.
- Banned words: <e.g. "free" when there is no free plan>. Punctuation: <e.g. no em dash>.
- Mascot / logo in photos: <never>. Readable text in photos: <never>.
- Faces: <plain but pretty, never model-like>. Nobody talks on screen: <yes/no>.
- AI-generated label on ad platforms: <required, who ticks it>.
- Other: <…>

## Lessons and results
| What was done | Feedback | Rule |
|---|---|---|
| <…> | <…> | <…> |

Benchmarks (date, platform, CPM, CTR, 6-second view rate, installs): <…>.

## Project conventions
Report language and style: <…>. How to send files to the user: <tool / path>.
Where decisions are logged: <memory file / notes / History below>.
Neighbour skills: <ads manager, app store listing…>.

## History
<YYYY-MM-DD: persona X attached (user's pick), variant Y rendered, uploaded or not>
