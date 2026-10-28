# Hepatitis B explainer: edit

Edited version of Dr Dheeraj Mahar's Hindi voiceover explainer, "HBV DNA undetectable ≠ virus khatam".

- `output/hepatitis-b-final.mp4`: final video (1080×1920, 30 fps, 1:48, −14 LUFS)
- `source/original.mp4`: original upload (InShot export, 1:39)

## What the edit adds
- Full-screen motion graphics over a darkened, slowly drifting background:
  hook → lab-report story (HBsAg positive, HBV DNA undetectable, doctor/patient bubbles, years without follow-up)
  → "Ek IMPORTANT baat" → HBsAg/undetectable decoder cards and a virus-level vs test-limit graph
  → "Undetectable ≠ Eliminated" → what doctors assess (SGPT, HBV DNA, fibrosis, risk factors)
  → EASL 2025 monitoring timeline → "Yaad rakhiye" → "No symptoms ≠ safe liver" → summary
- The cut-off last sentence is finished on screen: "…toh Follow-up MAT CHHODIYE!"
- An on-screen-only card after the conclusion: liver cancer (HCC) surveillance, ultrasound every 6 months in cirrhosis or high-risk patients
- Word-by-word Hinglish captions, name lower-third, end card with disclaimer
- One long pause tightened (0.47 s), synthesised music bed ducked under the voice, sound effects per on-screen event

## Rebuild
Same toolchain as `../capsule-endoscopy-edit` (ffmpeg, Node + Playwright/Chromium, Python with numpy, scipy, opencv-python-headless).

```sh
python3 timeline.py
node render.js /tmp/overlay 4
python3 audio.py /tmp/audio
python3 build.py source/original.mp4 /tmp/overlay /tmp/audio output/hepatitis-b-final.mp4
```

Caption timings are hand-written in `timeline.py` from `transcript_words.json` (Whisper word timestamps).
