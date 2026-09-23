---
name: image-prompt-porting
description: Port an external photoreal image prompt (a viral JSON prompt from a tweet, another creator's "photorealistic" template, a prompt pasted by the user) into your own image pipeline, or add a new shot type (camera angle, framing, face shot) to it. Keeps the structure that makes these prompts work (subject, pose, wardrobe, setting, light, camera, realism, micro-details, negatives, priorities, output), replaces the domain content, adds your invariants (no readable text or logos, camera never visible, one light source, calm zone for overlay text), keeps the JSON valid after placeholder filling, keeps prompts in files instead of code, and walks the checklist so the new shot type is actually used by the pipeline. Use it whenever the user shares an image prompt or a link to one and says "take inspiration", "rework ours like this", "use this style", or asks for a new angle, framing or photo style for carousels or ads, even if they never say "prompt" or "shot type".
---

# Porting an image prompt into your pipeline

What makes a good shared photoreal prompt work is its **structure**, not its
content. A JSON prompt that separates subject, pose, wardrobe, setting, light,
camera, realism requirements, fine details, negatives, a priority order and
the output spec is followed far more literally by GPT-style image models than
the same ideas in prose. So you port the skeleton and throw away the gym
mirror.

## Before you start

Read `.claude/ugc-config.md` (paths of the pipeline, where prompts live, the
placeholder filler, the check commands, the shot-type files, brand
invariants). Missing? Create it with the questions and template described in
the `ai-persona` skill of this plugin (`../ai-persona/references/config-template.md`).
Read the **Project conventions** of `.claude/posthog-funnel-map.md` if present.

## Port a prompt

1. **Read the source in full.** If it is a tweet or a page, open it in the
   browser tool and extract the text; don't work from a screenshot excerpt.
2. **Keep the structure, replace all domain content.** Typical top-level
   blocks worth keeping: `type`, `objective`, `image_format`, `subject`
   (count, identity, attractiveness, skin, hair, face, hands, clothing),
   `shot` (kind, camera position, pose, gaze, expression, subject position,
   lens), `environment`, `text_overlay_composition`, `lighting`,
   `camera_characteristics`, `color_palette`, `realism_requirements`,
   `fine_details`, `negative_prompt`, `identity_handling`, `priority_order`,
   `output`. Replace the scene (gym → student revising at a desk, whatever
   your product needs). Delete what doesn't apply to you ("upload a reference
   image" instructions, mirrors, brand products).
3. **Add your invariants**, the ones a shared prompt never has:
   - no readable text, letters, numbers, logos, brand names, watermarks,
     readable screens or handwriting (overlay text is added later, and
     garbled AI text is the first tell);
   - the camera taking the picture is never visible (and never write "looks
     at the phone");
   - exactly one real light source consistent with the scene;
   - faces plain but pretty, never model-like (see `ai-persona`);
   - a calm, low-detail band where the overlay text will sit;
   - your own brand rules (no mascot in photos, no product in the hook…);
   - `identity_handling`: a generic fictional adult, never a real person.
4. **Split shared vs per-shot.** One base file holds everything common; one
   fragment per shot type holds the `shot` block and its own priority list.
   Keep them in prompt files, never as string literals in code: the code only
   chooses which file to load and fills placeholders.
5. **Keep the JSON valid after filling.** This is where ports break silently:
   - inject values through an escaping helper (JSON-escape, then collapse
     whitespace), never raw string concatenation:
     ```ts
     const jsonText = (s: string) => JSON.stringify(s.replace(/\s+/g, ' ').trim()).slice(1, -1);
     ```
   - never glue a placeholder to a closing brace (`{{SHOT}}}`): a loader that
     rejects any leftover `{{X}}` will see `}}` as a broken placeholder;
   - if a fragment carries two parts (the `shot` block and the priorities),
     separate them with an explicit marker line such as `---PRIORITIES---`
     and split on it in code;
   - `JSON.parse` the final prompt before every call, and have a "print the
     prompt, don't call the model" mode that runs the same parse.

A short skeleton of the base file is in `references/json-prompt-skeleton.md`.

## Wire a new shot type into the pipeline

Each item exists because forgetting it fails **silently**: the validator
strips an unknown key, the UI never offers the shot, the planner never picks
it. Map each one to your code (the config lists the files):

- [ ] The shot-type enum in the data schema, plus the "face shots" subset if
      the face is visible (and the helper everyone uses to test it).
- [ ] The viewfinder description of the shot in English, used both by the
      image prompt and by any planner model that chooses shots.
- [ ] The prompt fragment for the shot (face shots use the structured prompt).
- [ ] The guard deciding where the shot is allowed (for example: face shots
      only on the first slide, never on first-person POV formats).
- [ ] Every planner, storyboard or visual-specialist prompt that lists the
      available shots, and per-format guidance. Without this the pipeline
      never chooses the new shot.
- [ ] Tool descriptions (MCP or API docs) that enumerate shot types.
- [ ] UI selectors (often filtered by the face-shot helper: check the logic).
- [ ] The image model per format, and the list of allowed models if new.
- [ ] One line in the project's own docs.

Then run the typecheck, the data check, a print of the final prompt (it must
parse), and **one real image that you open and look at before saying it
works**. The defects that matter (a phone drawn in the frame, a face too
beautiful, the persona appearing on shots that should be empty) only show on
the image, never in the prompt.

## Don't

- Put prompt text in code, or add a data key without adding it to the schema
  first (it will be dropped without an error).
- Add a visible face to a first-person POV format without the user's decision.
- Apply the crisp modern-smartphone look of face shots to shots that have a
  different house style (film, flash, grain) unless asked.
- Use `git stash` as a way to test something. Check `git status` first if you
  must touch git at all.
