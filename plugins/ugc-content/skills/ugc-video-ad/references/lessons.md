# Lessons from real UGC video ads

Condensed from the first six videos of a consumer-app campaign (four
iterations of the first video, then two more personas, then hook variants).
Each row is a failure a founder rejected, and the rule it produced.

| What was tried | Feedback | Rule |
|---|---|---|
| Still photos animated with a Ken Burns zoom | "find a real image-to-video" | Always animate with an image-to-video model, never zoom on a still |
| AI voice-over | "the voice is bad" | No voice. Music + sound design only |
| Hook selfie where she talks to the camera, no voice | "she talks and there's no sound, it's weird" | Nobody talks. Open on a situation (struggling with homework) |
| Clip where the persona blows out air | "it makes steam, very AI" | Forbid breath, sighs, puffed cheeks in every clip prompt |
| Same school topic and same bedroom in three videos | "different contexts, not always the same chapter" | Setting and demo topic are specific to each persona |
| A second character (a child) walks out of the frame at the end of a clip | fixed by slowing the clip | For a second person: "never leaves the frame, seen from behind", then check the sheet |
| Image model sometimes refuses with a reference portrait ("real person") | a retry was enough | Don't change model, retry |
| Mouth half-open in the middle of a clip | fixed with a start offset | Check every clip frame by frame before rendering |
| Caption blocks overlapping | auto-placement added | Always render control frames before the MP4 |
| Only ~2 % 6-second views in delivery | three hook variants on the best persona | Test three hooks per persona, not one |

## Field benchmarks (day 1, one European market, app-install campaign)

About 20 hours of delivery, three videos: CPM around 2 EUR, CTR 0.3 to 0.4 %,
6-second view rate around 2 %. The persona that looked most like a real
student (a university library setting, plain but pretty) got the most clicks, ahead of the
younger high-school persona and the parent persona. The app demo and the
onboarding held; the hook was the lever. Store attribution (SKAdNetwork)
arrives 24 to 72 hours later, so don't judge installs on day 1.

## Also learned

- Hook text visible from frame 0: that frame is the thumbnail.
- A bigger hook font (about 84 px on a 1080 px wide stage) reads in half a
  second; it is a cheap variant to test.
- Reorder existing clips (open on the look-into-the-camera shot, or on the
  smiling selfie) before paying for new ones.
- Ad platforms re-enable "automatic enhancements" (auto music, translation,
  dubbing, generated cards) by default: check them off before publishing.
