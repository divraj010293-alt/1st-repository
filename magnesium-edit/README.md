# Magnesium & sleep explainer

Script-first edit: the graphics were built from the script before the voiceover was recorded.

- `script.md`: revised script to record from (Devanagari), with sources
- `output/magnesium-draft.mp4`: **draft**, timed to an estimated speaking pace, music + SFX, no voice
  (1080×1920, 1:59). Doubles as a pace guide for recording.

## Scenes
Hook → 3 AM / "Magnesium lo!" trend → "Scientific evidence?" with the 3 studies →
Study 1 (2021 meta-analysis: 3 RCTs, 151 older adults, −17 min vs placebo, no total-sleep-time difference, low/very low quality) →
Study 2 (2025 RCT: 155 healthy adults with poor sleep, 4 weeks, 250 mg elemental Mg bisglycinate, ISI −3.9 vs −2.3, d = 0.2) →
Study 3 (2026 review of 12 RCTs: not enough evidence for routine use) →
"Kuch logon ko fayda / har kisi ko zaroorat nahi" → CBT-I first line, doctor after 3 months →
safety (loose motions, 2-hour gap, kidney disease) → "Essential mineral ≠ proven sleeping pill" → follow/share → end card with sources.

## When the voiceover arrives
1. Get phrase start times from the recording (Whisper word timestamps, matched to the 78 phrases in `timeline.py`)
   and save them as `phrase_times.json`: a list of 79 numbers (78 phrase starts, then the end of speech).
2. Rebuild:
```sh
python3 timeline.py                    # switches from draft to recorded timing automatically
node render.js /tmp/frames 4
python3 audio.py /tmp/audio
python3 build.py /tmp/frames /tmp/audio output/magnesium-final.mp4 voiceover.wav
```
