# Structured face-shot prompt: skeleton

A base file plus one fragment per shot type. Placeholders in `{{CAPS}}` are
filled by code through a JSON-escaping helper. `{{SHOT}}` sits on its own line
so that no placeholder touches a closing brace.

## Base file (for example `prompts/person.json.md`)

```text
{
  "prompt": {
    "type": "photorealistic_smartphone_photo",
    "objective": "ONE single photorealistic vertical frame that looks like an authentic photo from a real person's phone, posted on social media. Never an illustration, CGI, stock photo or studio shoot.",
    "image_format": {
      "orientation": "portrait",
      "framing": "one full-bleed vertical shot, no borders, collage or date stamp",
      "resolution": "very high resolution"
    },
    "this_photo": "{{IMAGE_PROMPT}}",
    "recurring_place_and_look": "{{STYLE_PROMPT}}",
    "subject": {
      "count": 1,
      "identity": "{{FACE}}",
      "identity_reference": "{{FACE_REF}}",
      "attractiveness": "ordinary, approachable, naturally pretty but NOT model-pretty; small natural imperfections",
      "skin": "visible pores, subtle tonal variation, no airbrushing, no beauty filter",
      "hair": "individual strands and flyaways, never salon-perfect",
      "face": "minimal or no makeup, slightly imperfect symmetry, realistic youthful adult proportions",
      "hands": "anatomically correct, naturally separated fingers",
      "clothing": "ordinary clothes with natural folds, no visible branding"
    },
{{SHOT}}
    "environment": {
      "type": "a believable lived-in place",
      "details": "everyday clutter that fits the scene; any paper or screen is blurred and unreadable",
      "constraint": "nothing staged, no luxury interior"
    },
    "text_overlay_composition": "{{TEXT_LAYOUT}}",
    "lighting": {
      "primary_source": "ONE real light source consistent with the scene",
      "avoid": ["hard direct flash", "studio or beauty lighting", "rim light", "colored lighting", "cinematic grading"]
    },
    "camera_characteristics": {
      "device": "modern flagship smartphone",
      "depth_of_field": "moderately deep, no strong portrait blur",
      "dynamic_range": "natural smartphone HDR",
      "exposure": "slightly imperfect, as shot",
      "noise": "low natural sensor noise"
    },
    "color_palette": { "mood_colors_to_favor": ["{{BG}}", "{{ACCENT}}"], "saturation": "natural, never oversaturated" },
    "realism_requirements": ["realistic anatomy", "correct hands", "physically plausible shadows", "a real moment, not a photoshoot"],
    "fine_details": ["flyaway hairs", "pores", "fabric weave", "paper grain", "contact shadows"],
    "negative_prompt": [
      "cartoon", "illustration", "3D render", "CGI", "plastic skin", "beauty filter",
      "model-pretty face", "overly symmetrical face", "AI influencer look", "model pose",
      "extra fingers", "deformed hands", "second person", "heavy bokeh", "studio lighting",
      "text", "letters", "numbers", "readable screen", "readable handwriting",
      "logo", "brand name", "mascot", "watermark", "caption"
    ],
    "identity_handling": {
      "instruction": "Create a generic fictional adult matching the description. Do not reproduce the identity of any real person."
    },
    "priority_order": [
{{PRIORITIES}}
    ]
  },
  "output": { "style": "ultra-photorealistic", "deliverable": "output only the image" }
}
```

## Fragment (for example `prompts/person-shot-desk-portrait.md`)

```text
    "shot": {
      "kind": "candid photo of the person at their desk, taken by their own phone propped on a pile of books, or by a friend opposite",
      "camera_rule": "the phone taking the picture is the camera and is NEVER visible in the frame; any other phone lies face down",
      "camera_position": "in front, about one meter away, seated eye level or slightly above",
      "pose": "leaning over the notes, pen in hand, the other hand under the chin",
      "gaze": "looking up at the camera for a second",
      "expression": "calm, focused, a little tired; at most a small closed-mouth half-smile",
      "lens_character": "smartphone main lens, about 26-30 mm equivalent"
    },
---PRIORITIES---
      "1. One real person caught mid-task, candid pose",
      "2. Keep the identity exactly as described",
      "3. The situation readable in one second",
      "4. Real skin, real hair, no beauty filter",
      "5. Authentic smartphone rendering",
      "6. The place and its single light source",
      "7. A calm band for the overlay text",
      "8. Accurate anatomy and object geometry",
      "9. Fine details"
```

## Filling, in code

```ts
const [shot, priorities] = fragment.split('---PRIORITIES---');
let prompt = base
  .replace('{{SHOT}}', shot.trimEnd())
  .replace('{{PRIORITIES}}', priorities.trim())
  .replace('{{FACE}}', jsonText(face))
  .replace('{{IMAGE_PROMPT}}', jsonText(brief));
// …other placeholders
if (/\{\{[A-Z_]+\}\}/.test(prompt)) throw new Error('unfilled placeholder');
JSON.parse(prompt); // must stay valid JSON
```

A two-person variant (a second person only ever seen from behind) is a string
patch on the filled prompt: change `"count": 1` to a description of both, and
remove `"second person"` from the negatives. Parse again afterwards.
