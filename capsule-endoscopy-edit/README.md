# Capsule endoscopy explainer: edit

Edited version of Dr Dheeraj Mahar's 49 s vertical explainer on capsule endoscopy.

- `output/capsule-endoscopy-final.mp4`: final video (1080×1920, 30 fps, 50.8 s, −14 LUFS)
- `source/original.mp4`: original upload

## What the edit adds
- Animated graphics panel in the empty upper part of the frame, one scene per section:
  hook → inside the capsule → journey through the gut → "Why?" → endoscopy/colonoscopy reach vs
  the small-intestine gap → who needs it → limitations & capsule retention → summary → end card
- Word-by-word captions with the script slips corrected ("thousands of images", "upper GI endoscopy")
- Name lower-third, end card with follow/save/share and an educational-use disclaimer
- Two silent pauses tightened (0.4 s and 0.33 s); the cuts are hidden by punch-in zooms
- Synthesised music bed (ducked under the voice) and sound effects for every on-screen event

## Rebuild
Needs ffmpeg, Node with Playwright/Chromium, Python with numpy, scipy, opencv-python-headless.

```sh
python3 timeline.py                       # captions, cues, zoom keyframes -> timeline.json
node render.js /tmp/overlay 4             # graphics.html -> transparent PNG frames
python3 audio.py /tmp/audio               # music.wav + sfx.wav
python3 build.py source/original.mp4 /tmp/overlay /tmp/audio output/capsule-endoscopy-final.mp4
```

`transcript.json` holds the word-level transcript (Whisper small) the captions are built from.
