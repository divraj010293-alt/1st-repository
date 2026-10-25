# Probiotics explainer: edit

Captions and motion graphics over Dr Dheeraj Mahar's 57 s vertical explainer on probiotics,
built with [HyperFrames](https://hyperframes.heygen.com). Original sound only: no music or effects.

- `output/probiotics-final.mp4`: final video (1080×1920, 30 fps, 59.5 s)
- `assets/probiotics.mp4`: the upload, upscaled from 478×850 (lanczos, keyframe every second)

## What the edit adds
- Graphics panel over the bookshelf, one scene per section: hook → inside your gut → what
  probiotics are → "not every probiotic works for every problem" → where they help (antibiotic
  diarrhoea, H. pylori treatment, uncertain for IBS / fatty liver) → what you can do → not magic
  pills → end card
- Word-by-word captions above the speaker's head, with transcription and script slips corrected
  ("H. pylori", "in adequate amounts", "help prevent diarrhoea")
- Name lower-third, end card with follow/save/share and an educational-use disclaimer

## Layout
- `index.html`: the A-roll and one host per scene
- `compositions/`: `frame` (scrim, panel, chip), the seven scenes, `lowerthird`, `captions`, `endcard`
- `assets/transcript.raw.json`: Whisper small word timings; `tools/build_captions.py` corrects
  them and writes `assets/transcript.json` and `compositions/captions.html`

## Rebuild
```sh
python3 tools/build_captions.py   # only after editing the transcript or caption rules
npm run check
npm run render                    # -> renders/
```
GSAP is loaded from `assets/gsap.min.js` so renders need no network.
