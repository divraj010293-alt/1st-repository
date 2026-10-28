"""Build the edit timeline for the Hepatitis B explainer: pause cut, Hinglish captions, scene cues.

Caption word times come from Whisper word timestamps on the Hindi voiceover, corrected
against detected pauses. All times written to timeline.json are on the *edited* timeline.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
FPS = 30
SRC_DURATION = 98.70
# Long pause before "aaj treatment..." tightened; cut sits on frame boundaries.
CUTS = [(2301 / FPS, 2315 / FPS)]
CONCLUSION = 2.6  # on-screen finish of the cut-off last sentence
HCC_CARD = 3.4  # on-screen only: liver cancer surveillance note (not in the voiceover)
END_CARD = 3.4
OUTRO_HOLD = CONCLUSION + HCC_CARD + END_CARD


def remap(t):
    """Source time -> edited time."""
    shift = 0.0
    for a, b in CUTS:
        if t >= b:
            shift += b - a
        elif t > a:
            return a - shift
    return t - shift


# Hinglish caption phrases: "word@sourceSeconds ...". Words marked with * are emphasised.
PHRASES = """
Bahut@0.00 saare@0.42 *Hepatitis@0.70 *B@1.24
patients@1.40 ke@1.88 saath@2.02
ek@2.30 common@2.64 *problem@2.94 hoti@3.26 hai.@3.46
*HBsAg@3.90 *positive@4.72 aata@5.26 hai.@5.42
Doctor@6.03 *HBV@6.40 *DNA@7.06
test@7.40 karwate@7.74 hain.@8.10
Report@8.24 mein@8.76 *HBV@9.02 *DNA@9.80
*undetectable@9.98 aata@10.68 hai.@10.90
Doctor@11.35 kehte@11.68 hain,@11.95
abhi@12.56 *treatment@12.78 ki@13.40 zaroorat@13.50
*nahi@13.90 hai.@14.12
Patient@14.50 ghar@14.86 jaakar@15.08
sochte@15.40 hain…@15.70
"Jab@16.17 *virus@16.46 hi@16.86 *nahi@16.96 hai,@17.15
toh@17.69 ab@17.82 doctor@18.02
ke@18.34 paas@18.46 *kyun@18.66 jaana?"@18.82
Aur@19.45 phir@19.60 woh@19.74 *saalon@19.92 tak@20.24
*follow-up@20.50 *nahi@20.90 karta.@21.12
Lekin@21.73 yahan@22.00 ek@22.34
*important@22.48 baat@22.88 samjhiye.@23.12
*HBsAg@23.88 *positive@24.64
hone@25.28 ka@25.54 matlab@25.68 hai,@25.96
ki@26.49 *Hepatitis@26.62 *B@27.24
*infection@27.40 abhi@27.95 *present@28.30 hai.@28.62
Aur@29.08 *HBV@29.24 *DNA@29.86
*undetectable@30.22 hone@31.04 ka@31.28
matlab@31.42 hai,@31.70
ki@32.22 blood@32.32 mein@32.68 *virus@33.00
ka@33.42 *level@33.60 test@33.92 ki@34.24
*limit@34.70 se@35.00 *neeche@35.16 hai.@35.45
Iska@35.87 matlab@36.12
yeh@36.88 *nahi@37.10 ki@37.34 *virus@37.44
poori@37.88 tarah@38.20 body@38.44 se@38.78
*eliminate@39.02 ho@39.52 gaya@39.65 hai.@39.76
Isiliye@40.16 doctor@40.60 *sirf@40.96
ek@41.32 *report@41.54 dekh@41.86 kar@42.14
*decision@42.30 *nahi@42.72 lete.@42.94
Woh@43.51 *SGPT,@43.68
*HBV@44.87 *DNA,@45.30
liver@46.27 mein@46.45 *fibrosis@46.62
aur@47.32 patient@47.64 ke@48.06 doosre@48.18
*risk@48.58 *factors@48.86 ko@49.28 bhi@49.40
*assess@49.54 karte@49.94 hain.@50.20
*EASL@50.91 ki@51.20 *2025@51.44 *guidelines@52.12 bhi@53.00
isi@53.54 baat@53.74 par@54.02
*zor@54.20 deti@54.46 hain,@54.74
ki@55.23 *Hepatitis@55.36 *B@56.00 ke@56.20 patients@56.36
ki@56.82 *regular@57.00 *monitoring@57.44
*zaroori@57.92 hai.@58.20
Naye@58.60 diagnose@58.80 hue@59.22
patients@59.40 mein@59.82 *pehle@60.02 *saal@60.36
*ALT@60.68 aur@61.36 *HBV@61.52 *DNA@62.08
aam@62.46 taur@62.78 par@63.02
har@63.51 *3–6@63.68 *mahine@64.26
check@64.68 kiye@64.90 jaate@65.10 hain.@65.38
Uske@65.78 baad@66.04
*monitoring@66.30 ka@67.04 *interval@67.22
*disease@67.66 *phase@68.00 ke@68.36 hisaab@68.80 se@69.16
*decide@69.32 hota@69.70 hai.@69.90
*HBsAg@70.30 ko@71.12 bhi@71.26
*annually@71.44 check@71.90
karna@72.12 chahiye,@72.40
aur@73.06 liver@73.22 *fibrosis@73.50
ka@74.06 *assessment@74.22 bhi@74.76
*zaroori@74.98 hai.@75.30
Toh@75.76 *yaad@75.95 rakhiye:@76.18
aaj@77.43 *treatment@77.70
ki@78.16 zaroorat@78.30 *nahi@78.66 hai,@78.88
iska@79.24 matlab@79.50 yeh@79.90 *nahi@80.08
ki@80.42 *future@80.50 mein@80.88
*kabhi@81.16 zaroorat@81.42
*nahi@81.90 padegi.@82.12
Aur@82.82 agar@83.04 liver@83.34 mein@83.64
*cirrhosis@84.10
ya@84.88 *significant@85.02
*fibrosis@85.64 hai,@86.10
toh@86.54 *management@86.64
aur@87.22 bhi@87.50 *carefully@87.70
decide@88.28 karna@88.62 padta@88.84 hai.@89.08
*Hepatitis@89.26 *B@90.10 mein@90.24
*symptoms@90.44 na@90.84 hone@91.00
ka@91.26 matlab@91.40 bhi@91.78
yeh@92.24 *nahi@92.42 ki@92.76
liver@92.86 *bilkul@93.10 *safe@93.54 hai.@93.86
Agar@94.20 aap@94.46 *HBsAg@94.64
*positive@95.54 hain,@95.98
aur@96.40 aapka@96.58
*HBV@96.98 *DNA@97.66 *negative@97.96 hai…@98.46
"""

captions = []
for line in PHRASES.strip().splitlines():
    words = []
    for tok in line.split():
        w, t = tok.rsplit("@", 1)
        hi = w.startswith("*")
        words.append({"w": w.lstrip("*"), "s": float(t), "hi": hi})
    captions.append(words)

# word ends: next word's start (or +0.45 s for the phrase's last word)
flat = [w for c in captions for w in c]
for a, b in zip(flat, flat[1:]):
    a["e"] = min(b["s"], a["s"] + 0.9)
flat[-1]["e"] = SRC_DURATION

out_caps = []
for i, c in enumerate(captions):
    nxt = captions[i + 1][0]["s"] if i + 1 < len(captions) else SRC_DURATION
    end = min(nxt, c[-1]["s"] + 0.75)
    assert all(x["s"] < y["s"] for x, y in zip(c, c[1:])), c
    out_caps.append({
        "start": round(remap(c[0]["s"]), 3),
        "end": round(remap(end), 3),
        "words": [{"w": w["w"], "s": round(remap(w["s"]), 3), "e": round(remap(w["e"]), 3), "hi": w["hi"]} for w in c],
    })

SRC_CUES = {
    "hook": 0.0,
    "lab": 3.70,
    "hbsag": 3.90,
    "dnaTest": 6.03,
    "undetectable": 9.98,
    "doctor": 11.35,
    "patient": 14.50,
    "thought": 16.17,
    "years": 19.45,
    "noFollow": 20.50,
    "important": 21.73,
    "decodeA": 23.88,
    "present": 27.40,
    "decodeB": 29.08,
    "graph": 32.22,
    "limit": 34.70,
    "notEliminated": 35.87,
    "eliminate": 39.02,
    "oneReport": 40.16,
    "decision": 42.30,
    "sgpt": 43.68,
    "dna": 44.87,
    "fibrosis": 46.27,
    "risk": 47.32,
    "easl": 50.91,
    "regular": 56.82,
    "year1": 58.60,
    "every36": 63.51,
    "phase": 65.78,
    "hbsagYearly": 70.30,
    "fibroAssess": 73.06,
    "yaad": 75.76,
    "today": 77.43,
    "future": 80.42,
    "cirrhosis": 82.82,
    "careful": 86.54,
    "symptoms": 89.26,
    "safe": 92.86,
    "final": 94.20,
    "finalDna": 96.40,
}
cues = {k: round(remap(v), 3) for k, v in SRC_CUES.items()}
end_speech = remap(SRC_DURATION)
cues["conclusion"] = round(end_speech, 3)
cues["hcc"] = round(end_speech + CONCLUSION, 3)
cues["outro"] = round(end_speech + CONCLUSION + HCC_CARD, 3)
DURATION = round(round((end_speech + OUTRO_HOLD) * FPS) / FPS, 3)

# Slow Ken Burns drift on the static background: (t, zoom, dx, dy) keyframes, eased between.
KB = [
    {"t": 0.0, "z": 1.10, "x": 0, "y": 0},
    {"t": cues["important"], "z": 1.18, "x": -30, "y": 40},
    {"t": cues["easl"], "z": 1.12, "x": 40, "y": -30},
    {"t": cues["yaad"], "z": 1.22, "x": -20, "y": -50},
    {"t": DURATION, "z": 1.14, "x": 30, "y": 20},
]

out = {
    "fps": FPS,
    "duration": DURATION,
    "srcDuration": SRC_DURATION,
    "cuts": CUTS,
    "captions": out_caps,
    "cues": cues,
    "kenburns": KB,
}
json.dump(out, open(HERE / "timeline.json", "w"), indent=1, ensure_ascii=False)

if __name__ == "__main__":
    print("duration", DURATION, "frames", round(DURATION * FPS), "captions", len(out_caps))
    print("longest caption:", max((" ".join(w["w"] for w in c["words"]) for c in out_caps), key=len))
