# Magnesium & sleep explainer

- `output/magnesium-final.mp4`: final video (1080×1920, 30 fps, 2:20, −14 LUFS).
  Voiceover + sound effects, **no background music**.
- `script.md`: revised script (Devanagari), with sources
- `voiceover.wav`: the synthesised Hindi voiceover (24 kHz mono)

## Voiceover
An AI-generated Hindi male voice (Kokoro-82M, voice `hm_psi`, 1.2× speed), not Dr Mahar's own voice.
`tts.py` holds the spoken text, one line per caption phrase. Hindi is in Devanagari, English terms
are in English, and numbers are written the way they're spoken. It synthesises sentence by sentence and
writes `phrase_times.json`, which `timeline.py` uses to time every caption and animation.

Model files (all fetched from npm/PyPI):
- `kokoro-q8.onnx`: concatenate the 6 parts of the `kokoro-q8-shards` npm package
  (sha256 `fbae9257…a1478`)
- `voices/hm_psi.bin`: from the `kokoro-js` npm package
- Python: `onnxruntime`, `kokoro-onnx` (phoneme vocabulary), `espeakng-loader` + `phonemizer-fork` (eSpeak NG Hindi/English)

## Rebuild
```sh
python3 tts.py <kokoroDir> voiceover.wav hm_psi 1.2   # also writes phrase_times.json
python3 timeline.py
node render.js /tmp/frames 4
python3 audio.py /tmp/audio                            # sound effects only
python3 build.py /tmp/frames /tmp/audio voiceover.wav output/magnesium-final.mp4
```

To swap in a real recording later, replace `voiceover.wav` and write its 78 phrase start times
(plus end of speech) to `phrase_times.json`. Then rerun from `timeline.py`.
