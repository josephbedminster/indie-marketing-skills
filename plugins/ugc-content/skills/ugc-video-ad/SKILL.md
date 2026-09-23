---
name: ugc-video-ad
description: Produce or iterate a 9:16 UGC-style video ad (TikTok, Reels, Shorts) with AI personas and no video SaaS - persona, still photos, image-to-video clips through an API (for example Kling via the OpenRouter video endpoint), a deterministic HTML timeline rendered frame by frame with Playwright, then H.264 with music and synthesized sound design through ffmpeg. Includes the creative rules learned from real campaigns (nobody talks, no breathing or sighing, plain faces, a new setting and topic per video, product only at the end, three hooks per persona, caption safe zones, AI-content disclosure) and the ffmpeg contact-sheet commands to check frames before rendering. Use it whenever the user talks about a video ad, a TikTok or Reels creative, UGC video, a new variant or hook, a new persona for an ad ("a student", "a mom"), a low 6-second view rate, or says a video "looks AI", even if they don't name the pipeline.
---

# UGC video ad with AI personas

A 15-16 second vertical ad, produced locally for a few dollars: a persona
struggles with a real problem, the product demo solves it, the persona reacts,
an end card names the product. Everything runs from one variants file, so a new
hook costs zero generation and 90 seconds of rendering.

## Before you start

Read `.claude/ugc-config.md`: pipeline location, commands, variants file,
models, cost, brand invariants, lessons already learned, results so far.
Missing? Create it with the questions and template of the `ai-persona` skill
(`../ai-persona/references/config-template.md`). Read **Business profile**
and **Project conventions** of `.claude/posthog-funnel-map.md` if present.
No pipeline yet? `references/pipeline.md` describes the architecture to build.

## Creative rules (learned the expensive way, apply by default)

Each clip costs about half a dollar and two minutes, so these save real
round-trips. Details and the failures behind them: `references/lessons.md`.

- **Nobody talks.** No AI voice-over (it sounds cheap), and a mouth moving
  with no sound is uncanny. Every clip prompt says the lips stay closed.
  Hooks are situations (stuck on homework at 11 pm), not someone addressing
  the camera.
- **No breathing, sighing, blowing, puffed cheeks.** Video models draw visible
  steam or mist: the most obvious AI tell. Forbid it in a shared clip suffix
  and never ask for it in a clip prompt.
- **Plain faces, not models** (see `ai-persona`).
- **One setting and one topic per video.** Bedroom + a geometry chapter,
  library + a history chapter, living room + a grammar lesson. The product
  demo inside the ad changes with the persona.
- **The product appears only at the end** (a line like "it's called X" and the
  end card). The product is never the hook.
- **Test three hooks per persona**, not one. The first second drives the
  6-second view rate, and that is the lever: demo and onboarding usually hold.
- **Captions in the safe zone**, hook visible from frame 0 (it is the
  thumbnail).
- **Declare AI-generated content** on the ad platform: the people are
  generated. Ticking that box is often irreversible: get the user's yes.
- Copy follows the project's banned-word and punctuation rules (config).

## Workflow

1. **Pick the case.**
   - New persona: photos and clips to generate, about $2 and 10 minutes.
   - New hook on an existing persona: reuse its assets, remap which clip
     plays in which scene, new captions. Zero generation cost. Always make
     three hook variants at once.
2. **Write the variant** in the variants file (copy the closest one). For a
   persona: a constant style line (setting + outfit + "bright, clean,
   recent-smartphone rendering"), three shots (struggle / desk / react), three
   silent clip motions, captions, the demo content (topic typed in the app,
   screens), the demo framing. The face comes from the persona's reference
   portrait, or from a frozen face image for a persona outside the image
   pipeline.
3. **Generate** photos, then clips. Generators skip what already exists; pass
   an id to regenerate one. **Check contact sheets before rendering**: same
   face across shots, mouth closed, no second person leaving the frame, no
   phone in the frame.
4. **Render** control frames first (hook at 0.05 s, then a few instants),
   read them, then the full MP4. If a clip has an awkward moment (mouth
   opening, someone walking out), shift its start or slow it down in the
   variant's timing instead of regenerating.
5. **Verify** on extracted keyframes, then send the MP4 to the user. **Say
   clearly that you have not listened to the audio**: they validate the mix.
6. **Log** the variants made, the feedback, and what was uploaded to the ad
   platform, where the config says.

## Checking frames (ffmpeg contact sheets)

Open the resulting PNGs with the Read tool.

```bash
# three photos side by side
ffmpeg -y -i a.png -i b.png -i c.png -filter_complex "[0]scale=360:640[a];[1]scale=360:640[b];[2]scale=360:640[c];[a][b][c]hstack=3" sheet.png
# one clip, 6 frames (2 per second)
ffmpeg -y -i clip.mp4 -vf "fps=2,scale=216:384,tile=6x1" -frames:v 1 sheet.png
# keyframes of a render (frame numbers at 30 fps)
ffmpeg -y -i ad.mp4 -vf "select='eq(n,0)+eq(n,60)+eq(n,150)+eq(n,380)',scale=300:-1,tile=4x1" -vsync 0 -frames:v 1 keys.png
```

Look for: identical face between shots, closed mouth on every frame, a
secondary character always seen from behind and inside the frame, captions
readable and not overlapping, frame 0 already showing the hook.

## Before editing the timeline

- It is a deterministic HTML page exposing `seek(t)`, rendered frame by frame;
  real-time CSS animations or `<video>` playback will not render correctly.
- Headless Chromium does not decode H.264: clips are pre-extracted to JPEG
  frames and `seek` awaits `img.decode()`.
- An embedded app demo in an iframe must be same-origin: serve the folder
  over a tiny local HTTP server, `file://` fails.
- Audio is mixed after the video; keep an "audio only" mode to remix in
  seconds.

Full architecture, variant schema, video API calls and the sound-design
recipes: `references/pipeline.md`.
