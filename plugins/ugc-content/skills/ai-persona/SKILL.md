---
name: ai-persona
description: Create, replace or adjust a consistent AI-generated persona (the recurring face of a UGC account, a carousel series or a video ad) and verify it with a test shot through the real pipeline prompt. Covers the dense English face description, the reference portrait sent as an image on every face shot, the "plain but pretty, girl or boy next door, not a model" calibration, adults only, generating two portraits for the user to pick, and the known pitfalls (a phone drawn in the frame, the too-beautiful AI face, the too-tired face, identity drift). Use it whenever the user wants "a girl" or "a guy" for an account, a reference face, a portrait, asks to make someone "prettier", "plainer", "blonde", "less tired", starts a new selfie-style account, wants the same person across several images, or complains that a generated person "looks AI", even if they never say "persona" or "face reference".
---

# AI persona: one face, kept consistent

A persona is a fictional adult who appears in many images: the hook selfie of
a carousel, the struggling student of a video ad, the parent of a parenting
account. Two things keep them the same person from one image to the next, and
nothing else does:

1. **A face text**: one dense English sentence, sent in every prompt that
   shows the face.
2. **A reference portrait**: an image file sent to the image model **as an
   image input** on every shot where the face is visible.

Text alone drifts after two or three images. A reference alone drifts on hair
color and age. Use both, and keep them consistent with each other.

## Before you start

Read `.claude/ugc-config.md` in the user's project: where the image pipeline
lives, how scripts run, which accounts show a face, the image model, the brand
invariants, where decisions are logged. If `.claude/posthog-funnel-map.md`
exists, read its **Business profile** and **Project conventions** too
(audience, language, report style).

No `ugc-config.md`? Ask at most five questions in one message, each with a
default guessed from the repo: where the image pipeline is and how it runs;
the image model and the env var holding the API key; which accounts or series
show a face and which never do (first-person POV, hands only); the brand rules
the founder already set; where to log decisions. Then write the file from
`references/config-template.md` (in this skill's folder) and show it.

## Hard rules

- **Adults only.** Every persona is 18 or older, written in the face text
  ("19-year-old", "realistic youthful adult proportions"). If the audience is
  teenagers, the persona is an 18-19-year-old student, never younger. Refuse
  a persona described as a minor.
- **Fictional.** The portrait prompt says "a generic fictional adult, do not
  reproduce the identity of any real person". Never use a photo of a real
  person as the reference unless it is the user themself or someone who
  consented.
- **Disclose.** Ad platforms require an "AI-generated content" label for
  generated people. Say so when the persona is for ads.

## The calibration that matters: plain but pretty

Founders ask for two things that sound contradictory. Both are right.

- **Plain.** A face that is too beautiful (perfect symmetry, full pouty lips,
  sculpted cheekbones, flawless skin) reads as AI in a second, and a UGC post
  that reads as AI loses the viewer. The pipeline's global face rules should
  already lock this: ordinary features, pores, flyaways, small imperfections,
  no makeup, negatives such as "model-pretty face", "AI influencer look".
- **Pretty anyway.** The first "plain" persona tends to overshoot: dark
  circles, dull skin, tired eyes. It gets rejected. The target is
  **naturally pretty in an approachable, girl-next-door (or boy-next-door)
  way, fresh, no makeup, clearly a real student or parent, not a model**.
  Not ugly.

So: **never tune beauty in the global rules** (that changes every persona at
once). Tune it in this persona's face text and in the portrait scene.
Phrases that worked:

- "naturally pretty in an approachable girl-next-door way, but clearly a real
  student and not a model"
- "a few light freckles", "soft friendly closed-mouth smile, rested, fresh face"
- "keep pores, flyaways and tiny imperfections"

What failed, both ways: "beautiful", "gorgeous", "flawless" (instant AI);
"exhausted, dark circles, dull skin" in the face text itself (the tiredness
belongs to a scene, not to the identity, otherwise every shot looks sick).

## Procedure

1. **Write the face text.** One dense English sentence: age, hair (color,
   roots, strands, length, how it is usually worn), skin (tone, freckles,
   texture), eye color, brows, lips, nose, one small recurring detail (a thin
   necklace, small hoops), "no obvious makeup". Example:
   "a 20-year-old woman with chest-length wavy chestnut hair usually in a loose
   clip, a few flyaways at the hairline, light olive skin with faint marks on
   the chin, hazel eyes, natural medium brows, average lips, a straight nose,
   a thin gold chain, no obvious makeup". If you change the
   hair color, change it in the text **and** regenerate the portrait.
2. **Generate two portraits.** Head and shoulders, neutral daylight from a
   window, plain background from the persona's world (bedroom wall, library
   shelf), soft closed-mouth smile, looking into the lens, phone-camera
   realism. Use the pipeline's portrait command if it has one. With a GPT
   image model on OpenRouter (for example `openai/gpt-5.4-image-2`), expect
   about 80 seconds per image. Two, not one: people choose fast between two
   options and slowly on one.
3. **Look at them yourself first** (open the PNGs), then show both to the user
   and say which one you would pick and why. When they answer "the first
   one", they mean the first of the last batch you sent.
4. **Attach** the chosen file as the persona's reference (config field, UI or
   flag, as the pipeline does it), then run the pipeline's data check.
5. **Test shot with the real prompt.** The portrait prompt is not the
   production prompt. Generate one real face shot through the pipeline (a
   study or work portrait, or the front selfie of a hook). If the pipeline can
   print the final prompt without calling the model, do that first and check
   it parses. Then look at the image: same person? hair color, age, freckles
   kept? no phone in the frame? Send it to the user.
6. **Log** which file is attached and why (the user's choice, the rejected
   alternatives) where the config says decisions go.

## Pitfalls

- **Never write "looks at the phone"** in a brief. The model draws a phone in
  the frame. Write "looks up at the camera" and state that the camera taking
  the picture is never visible; if another phone appears, it lies face down.
- **Only face shots get the reference and the face text.** Every other image
  of the series must show no person at all (the place, the light, the
  objects), and must not receive the face rules, or the model draws the
  persona everywhere.
- **No face on first-person POV accounts** (the poster holds the phone and is
  never seen). Adding one is a product decision for the user, not yours.
- **"Real person" refusals.** Some image models occasionally refuse a
  generation that has a reference portrait. Retry; don't switch models for it.
- **Model names from social media.** A prompt shared online may name a model
  your provider doesn't serve. Use the closest available one and note the
  choice in the config.
- **Scripts that don't load the env.** A script that imports the env module
  without calling its loader fails after all retries with "API key is not
  set". Check the loader is called.
- **Never delete old portraits without asking.** Keep them as alternatives;
  the user often comes back to one.
- **Too tired or too sad by default.** Emotion belongs to each shot's brief
  (red-rimmed eyes, a forced half-smile), not to the persona.
