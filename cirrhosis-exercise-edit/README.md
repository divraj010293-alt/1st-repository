# Liver cirrhosis & exercise explainer: edit

- `output/cirrhosis-exercise-final.mp4`: final video (1080×1920, 30 fps, 1:47, −14 LUFS)
- `source/original.mp4`: original recording (1:43)

## What the edit adds
- **White background:** the flat navy studio background is keyed to white in `build.py`, with edge
  pixels un-mixed and blue spill removed. The graphics use a matching light theme.
- **Layout:** graphics fill the top part of the frame, and Dr Mahar stays in the bottom-right corner of his
  original footage. A soft gradient hides the hard crop edge on the left of his footage.
- **Scenes:** hook ("Sirf aaram? → Ji nahi → Exercise aur bhi zaroori") → sarcopenia and its effects →
  the 3 exercise types with animated figures:
  1. walking, 15–20 min rozana, increasing with capacity
  2. muscle strengthening: chair sit-to-stand, wall push-ups, resistance band
  3. balance & flexibility: stretching, balance holding a chair

  Then the caution cases before starting (fluid in the abdomen, recent hematemesis, hepatic
  encephalopathy → gastroenterologist), the summary, "dawaiyan + sahi khaan-paan + exercise = daily routine", and the end card.
- **Content:** kept strictly to what he says.
- **Captions:** word-by-word Hinglish captions in the strip above his head, plus a name lower-third bottom-left.
- **Sound:** sound effects only, no music. The voice is turned down from about −9 LUFS, lightly de-hissed,
  and the mix is normalised to −14 LUFS.

## Rebuild
```sh
python3 timeline.py
node render.js /tmp/overlay 4
python3 audio.py /tmp/audio
python3 build.py source/original.mp4 /tmp/overlay /tmp/audio output/cirrhosis-exercise-final.mp4
```
Caption phrase times in `timeline.py` were set from Whisper segment times, checked against a pause map of the voice.
