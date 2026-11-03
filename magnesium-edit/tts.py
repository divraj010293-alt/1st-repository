"""Synthesise the Hindi voiceover with Kokoro-82M and write phrase_times.json.

usage: python3 tts.py <kokoroDir> <out.wav> [voice] [speed]
kokoroDir holds kokoro-q8.onnx (from the kokoro-q8-shards npm package) and voices/<voice>.bin
(from kokoro-js). Phonemes come from eSpeak NG via kokoro-onnx's tokenizer: Hindi runs with the
"hi" voice and English runs with "en-us", so medical terms keep their English pronunciation.

Text is synthesised one sentence at a time (natural intonation); each caption phrase's start
is placed inside its sentence by phoneme count, then snapped to the nearest pause.
"""
import json
import pathlib
import re
import sys
import wave

import numpy as np
import onnxruntime as ort
from kokoro_onnx.tokenizer import Tokenizer

HERE = pathlib.Path(__file__).parent
KDIR, OUT = pathlib.Path(sys.argv[1]), sys.argv[2]
VOICE = sys.argv[3] if len(sys.argv) > 3 else "hm_omega"
SPEED = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
SR = 24000

# One entry per caption phrase in timeline.py (same order). Numbers are written as spoken.
TTS = """
Magnesium Glycinate —
क्या सच में natural sleeping pill है?
आजकल नींद न आए,
तो लोग तुरंत
Magnesium tablets की सलाह
देने लगते हैं।
लेकिन scientific evidence
क्या कहता है?
तीन बड़ी studies ने
क्या पाया, देखिए।
twenty twenty-one में BMC Complementary
Medicine and Therapies में
एक systematic review
और meta-analysis प्रकाशित हुआ।
इसमें तीन randomized
controlled trials
और कुल एक सौ इक्यावन बुज़ुर्ग participants
शामिल थे।
Magnesium लेने से,
placebo की तुलना में,
सोने में लगने वाला समय
लगभग सत्रह मिनट कम हुआ।
लेकिन total sleep time में
कोई significant फर्क नहीं था।
और इन studies में
evidence की quality
low से very low थी।
twenty twenty-five में एक randomized
placebo controlled trial आया,
जिसमें खराब नींद वाले
एक सौ पचपन healthy adults शामिल थे।
चार हफ्ते तक रोज़
Magnesium Bisglycinate,
ढाई सौ milligram elemental magnesium,
देने पर
insomnia severity में
placebo से थोड़ा ज़्यादा
सुधार हुआ।
लेकिन effect size
बहुत छोटा था।
और twenty twenty-six की एक
systematic review ने
बारह randomized trials
का analysis किया।
Conclusion:
अभी insomnia के
routine treatment के लिए
magnesium को recommend करने के लिए
पर्याप्त evidence नहीं है।
तो क्या Magnesium
बिल्कुल काम नहीं करता?
ऐसा कहना भी सही नहीं होगा।
कुछ लोगों को
फायदा हो सकता है,
लेकिन हर उस व्यक्ति को
जिसे नींद नहीं आती,
Magnesium tablets की
ज़रूरत नहीं है।
लंबे समय की insomnia का
first line treatment
C B T I, यानी sleep therapy है।
और अगर तीन महीने से ज़्यादा
नींद की problem है,
तो doctor से मिलिए।
Magnesium से
loose motions हो सकते हैं,
और कुछ antibiotics
और osteoporosis की दवाओं से
दो घंटे का gap रखें।
अगर आपको kidney की बीमारी है,
तो बिना doctor की सलाह
Magnesium supplements
बिल्कुल न लें।
याद रखिए:
Magnesium एक essential mineral है,
लेकिन कोई proven sleeping pill नहीं।
ऐसी और evidence based जानकारी के लिए
follow करें, और share करें।
""".strip().splitlines()

GAP_SENTENCE = 0.38   # silence after . ? !
GAP_COLON = 0.28
GAP_SCENE = 0.30      # extra pause before a new scene

tk = Tokenizer()
sess = ort.InferenceSession(str(KDIR / "kokoro-q8.onnx"))
styles = np.fromfile(KDIR / "voices" / f"{VOICE}.bin", dtype=np.float32).reshape(-1, 256)


def phonemes(text):
    """Phonemise mixed Devanagari/Latin text run by run."""
    text = text.replace("।", ".").replace("—", ",")
    out = []
    for run in re.findall(r"[ऀ-ॿ][ऀ-ॿ\s,.?:!]*|[A-Za-z][A-Za-z\s\-',.?:!]*", text):
        lang = "hi" if re.match(r"[ऀ-ॿ]", run) else "en-us"
        p = tk.phonemize(run.strip(), lang=lang)
        if p:
            out.append(p)
    return " ".join(out)


def synth(ph):
    ids = tk.tokenize(ph)
    assert len(ids) <= 510, len(ids)
    style = styles[len(ids)][None, :]
    wav = sess.run(None, {"input_ids": np.array([[0, *ids, 0]], dtype=np.int64),
                          "style": style, "speed": np.array([SPEED], dtype=np.float32)})[0][0]
    return wav.astype(np.float32)


def trim(w, thr=0.01):
    idx = np.where(np.abs(w) > thr)[0]
    return w[max(0, idx[0] - 240): idx[-1] + 480] if len(idx) else w


def pauses(w, win=0.02, thr=0.012):
    """Centres of silent stretches (>= 90 ms) inside a sentence, in seconds."""
    n = int(win * SR)
    env = np.array([np.sqrt(np.mean(w[i:i + n] ** 2)) for i in range(0, len(w) - n, n)])
    quiet = env < thr
    out, start = [], None
    for i, q in enumerate(list(quiet) + [False]):
        if q and start is None:
            start = i
        elif not q and start is not None:
            if (i - start) * win >= 0.09:
                out.append((start + i) / 2 * win)
            start = None
    return out


timeline_src = (HERE / "timeline.py").read_text()
caption_lines = timeline_src.split('PHRASES = """')[1].split('"""')[0].strip().splitlines()
assert len(caption_lines) == len(TTS), (len(caption_lines), len(TTS))
scene_start = [ln.startswith("[") and not ln.startswith("[+") for ln in caption_lines]

# group phrases into sentences
sentences, cur = [], []
for i, line in enumerate(TTS):
    if cur and scene_start[i]:
        sentences.append(cur)
        cur = []
    cur.append(i)
    if line.rstrip()[-1] in "।.?!:":
        sentences.append(cur)
        cur = []
if cur:
    sentences.append(cur)

audio, starts, t = [np.zeros(int(0.30 * SR), np.float32)], [0.0] * len(TTS), 0.30
for si, sent in enumerate(sentences):
    if si and scene_start[sent[0]]:
        audio.append(np.zeros(int(GAP_SCENE * SR), np.float32))
        t += GAP_SCENE
    phs = [phonemes(TTS[i]) for i in sent]
    w = trim(synth(" ".join(phs)))
    dur = len(w) / SR
    # place phrase starts by phoneme count, then snap to a nearby pause
    counts = np.array([max(1, len(tk.tokenize(p))) for p in phs], float)
    cum = np.concatenate([[0], np.cumsum(counts)[:-1]]) / counts.sum()
    gaps = pauses(w)
    for k, i in enumerate(sent):
        s = cum[k] * dur
        if k and gaps:
            g = min(gaps, key=lambda x: abs(x - s))
            if abs(g - s) < 0.35:
                s = g
        starts[i] = round(t + s, 3)
    audio.append(w)
    t += dur
    end = TTS[sent[-1]].rstrip()[-1]
    gap = GAP_SENTENCE if end in "।.?!" else GAP_COLON if end == ":" else 0.12
    audio.append(np.zeros(int(gap * SR), np.float32))
    t += gap
    print(f"sentence {si + 1}/{len(sentences)} {dur:5.2f}s", flush=True)

speech_end = round(t, 3)
y = np.concatenate(audio)
y = y / max(1e-6, np.max(np.abs(y))) * 0.9
with wave.open(OUT, "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes((y * 32767).astype("<i2").tobytes())
json.dump(starts + [speech_end], open(HERE / "phrase_times.json", "w"))
print("wrote", OUT, f"{len(y) / SR:.2f}s", "voice", VOICE, "speed", SPEED)
