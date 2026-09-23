# Video ad pipeline: architecture

Everything below can be built in a few hundred lines of TypeScript and one
Node render script. One API key (OpenRouter in this example) covers images,
video and music.

## Components

| Piece | Role |
|---|---|
| `variants.json` | Source of truth: one key per variant (a persona, or a hook reusing a persona's assets) |
| photo generator | Builds the structured face-shot prompt, sends the persona's reference portrait as an image, writes 9:16 PNGs |
| clip generator | Image-to-video on each photo, writes MP4 clips |
| music generator | One instrumental track shared by all variants |
| `ad.html` | Deterministic timeline exposing `seek(t)`, `DURATION`, `ready` |
| render script | Extracts clip frames, serves the folder, screenshots each frame with Playwright, pipes to ffmpeg, mixes audio |
| `assets/<variant>/photos`, `clips`, `face.png` | Per-persona assets; keep abandoned versions in an `_old/` folder |
| `dist/<name>-<variant>.mp4` | Outputs |

Generators only create what is missing; with explicit ids they regenerate
those. Run everything from the folder where the env loader lives.

## Variant schema (example)

```jsonc
{
  "label": "Student, library",
  "persona": "account-id",               // where face text + reference portrait come from
  "face": "…",                           // optional: override the face text (persona outside the image pipeline)
  "faceFrom": "react",                   // optional: generate this shot first and use it as the reference for the others
  "replace": [["student", "mother"]],    // optional: string patches on the shared prompt for another kind of persona
  "style": "setting + outfit constant across shots, 'Bright, clean, recent-smartphone rendering.'",
  "shots": {
    "struggle": { "angle": "desk-portrait", "prompt": "…", "twoPeople": false },
    "desk":     { "angle": "desk-portrait", "prompt": "…" },
    "react":    { "angle": "front-selfie",  "prompt": "…" }
  },
  "clips": { "struggle": "silent motion…", "desk": "…", "react": "…" },
  "captions": { "hook1": ["line", "line"], "hook2": [["line", "highlighted block"]], "desk1": [], "demo1": [], "react1": [] },
  "timing": { "struggle": [0.3, 0.75] }, // [offset in the clip (s), speed] to skip an awkward moment
  "demo": { "bg": "photo|brand", "tilt": -3, "enter": "bottom|right" },
  "course": { "typed": "text typed in the app demo", "…": "screens content" },
  // Hook variant reusing a persona:
  "assets": "persona-folder",
  "sceneClips": { "hook": "desk", "desk": "struggle" }, // which clip plays in which scene
  "hookBig": true                                         // bigger hook text
}
```

Never write "looks at the phone" in a shot prompt (a phone gets drawn); write
"looks up at the camera".

## Image-to-video (OpenRouter video API)

```ts
const API = 'https://openrouter.ai/api/v1/videos';
const COMMON = ' Handheld smartphone footage, natural subtle camera shake, real-time speed, realistic skin and hair, the room and lighting stay exactly the same. No visible breath, vapor, mist or smoke. No cuts, no zoom, no text, no extra people, her face and identity stay identical to the first frame.';

// first frame as a light JPEG data URL (720x1280)
// ffmpeg -y -i photo.png -vf "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280" -q:v 2 first.jpg
const job = await (await fetch(API, { method: 'POST', headers, body: JSON.stringify({
  model: 'kwaivgi/kling-v3.0-pro',
  prompt: clipPrompt + COMMON,
  duration: 3,
  aspect_ratio: '9:16',
  resolution: '720p',
  generate_audio: false,
  frame_images: [{ type: 'image_url', image_url: { url: dataUrl }, frame_type: 'first_frame' }],
}) })).json();
// poll every 10 s: GET `${API}/${job.id}` until status === 'completed' | 'failed' (timeout ~15 min)
// download: GET `${API}/${job.id}/content?index=0`
```

Orders of magnitude seen: 3-second clip, 1080x1920 at 24 fps out, 95-140 s and
about $0.56 per clip. A new persona (3 photos + 3 clips) is about $2 and 10
minutes. Clip prompts describe small silent motions ("she rubs her forehead,
looks back down at her notes, her lips stay closed the whole time").

Photos with a GPT image model: about 80 s each. Music: an instrumental prompt
("Instrumental only, no vocals, upbeat lo-fi pop, ~105 bpm, starts
immediately with the full beat, 20 seconds") on a music model such as Google
Lyria through OpenRouter chat completions, which requires `stream: true`.

## The timeline page

- Fixed stage 1080x1920. Scenes: hook (0-2.6 s), problem (2.6-5.4), app demo
  (5.4-12), reaction (12-13.7), end card (to ~16 s). Adjust to taste.
- `seek(t)` sets every element's state from `t` alone (opacity, transforms,
  which clip frame is shown). No timers, no CSS transitions in render mode.
- Clip frames: `assets/<variant>/clips/<id>/0001.jpg…` + a `frames.json`
  count; `seek` swaps `img.src` and awaits `img.decode()`.
- App demo: an iframe of an animated HTML mock of the app, same origin, with
  its own time remapped by the parent. Text the mock types can be replaced
  per variant by overriding the element that shows it. Localized mocks
  (one file per language) make translated ads a caption + content change.
- Captions: TikTok-style rounded blocks (black, white, one highlight color),
  auto-shrink lines too wide, auto-place the second block under the first.
  **Safe zone at 1080x1920: nothing below y = 1500 px, nothing right of
  x = 940 px** (platform UI covers it). The hook must be visible at frame 0.
- Wait for fonts before rendering (`document.fonts.check(...)`), abort if not
  loaded.

## Render script

```js
// 1. extract clips to JPEG frames
// ffmpeg -i clip.mp4 -vf "fps=30,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920" -q:v 2 out/%04d.jpg
// 2. tiny http server on 127.0.0.1 serving only the needed folders
// 3. Playwright chromium, viewport 1080x1920, deviceScaleFactor 1
await page.goto(`http://127.0.0.1:${PORT}/ad.html?render=1&v=${variant}`);
await page.evaluate(() => window.AD.ready);
const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', '30', '-i', '-',
  '-vf', 'format=yuv420p', '-c:v', 'libx264', '-profile:v', 'high', '-level', '4.2',
  '-preset', 'slow', '-b:v', '10M', '-maxrate', '12M', '-bufsize', '24M', '-an', silentMp4]);
for (let f = 0; f < DURATION * 30; f++) {
  await page.evaluate((t) => window.AD.seek(t), f / 30);
  const png = await page.screenshot({ type: 'png' });
  if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
}
ff.stdin.end();
// 4. mix audio onto the silent video (below)
```

Useful flags: `--frames 0.05,2,6,9,12.6` (PNG control frames only),
`--remix` (audio only on the existing MP4), `--serve` (live preview URL).
A full render is about 90 seconds.

## Audio: music + synthesized sound design

No sample files: each effect is an ffmpeg `lavfi` source, placed with
`adelay` at a timeline instant, then everything is mixed.

```js
const SFX_SRC = {
  whoosh: "anoisesrc=d=0.5:c=pink:a=0.9,bandpass=f=1400:w=1200,afade=t=in:d=0.32:curve=exp,afade=t=out:st=0.34:d=0.16",
  pop:    "aevalsrc='sin(2*PI*(420+2600*t)*t)*exp(-38*t)':d=0.14:s=48000",
  thump:  "aevalsrc='sin(2*PI*(95-120*t)*t)*exp(-14*t)':d=0.35:s=48000",
  tap:    "aevalsrc='sin(2*PI*1900*t)*exp(-90*t)+0.5*sin(2*PI*320*t)*exp(-60*t)':d=0.08:s=48000",
  key:    "anoisesrc=d=0.03:c=white:a=0.8,highpass=f=2500,afade=t=out:d=0.03:curve=exp",
  tick:   "aevalsrc='sin(2*PI*1568*t)*exp(-30*t)+0.4*sin(2*PI*3136*t)*exp(-45*t)':d=0.2:s=48000",
  riser:  "anoisesrc=d=0.9:c=white:a=0.7,highpass=f=3000,afade=t=in:d=0.85:curve=exp,afade=t=out:st=0.86:d=0.04",
};
// SFX = [[type, atSeconds, gain], …]: whoosh on cuts, pop on each caption,
// key presses while the demo types, ticks on checkmarks, a chime when the
// result appears, a thump on the end card.
// per effect: [i:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=G,adelay=MS:all=1[sI]
// music:      [m:a]atrim=0:DUR,volume=0.5,afade=t=in:d=0.15,afade=t=out:st=DUR-1.4:d=1.4[m]
// mix:        [s0]…[m]amix=inputs=N:normalize=0:duration=longest,alimiter=limit=0.89,apad,atrim=0:DUR[a]
// output:     -map 0:v -map [a] -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart
```

`normalize=0` keeps each gain as written; the limiter prevents clipping. You
cannot listen to the result: the user validates levels.
