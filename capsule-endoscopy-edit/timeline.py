"""Build the edit timeline: pause cuts, corrected captions, scene cues and SFX cues.

All times in the output JSON are on the *edited* timeline (after pause cuts).
"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
FPS = 30
SRC_DURATION = 48.96
OUTRO_HOLD = 2.6  # seconds of held last frame for the end card

# Silent gaps trimmed from the source (start, end) in source seconds.
# Cut points sit on frame boundaries (30 fps) so audio and video cuts line up exactly.
CUTS = [(268 / FPS, 280 / FPS), (542 / FPS, 552 / FPS)]


def remap(t):
    """Source time -> edited time."""
    shift = 0.0
    for a, b in CUTS:
        if t >= b:
            shift += b - a
        elif t > a:
            return a - shift - (0)  # inside a cut: snap to the cut point
    return t - shift


DURATION = remap(SRC_DURATION) + OUTRO_HOLD

# ---------------------------------------------------------------- captions
words = [
    {"w": w["w"].strip(), "s": w["s"], "e": w["e"]}
    for seg in json.load(open(HERE / "transcript.json"))
    for w in seg["words"]
]


def find(word, near):
    """Index of `word` whose start is closest to `near` (source seconds)."""
    cands = [i for i, w in enumerate(words) if w["w"].strip(".,?").lower() == word.lower()]
    return min(cands, key=lambda i: abs(words[i]["s"] - near))


# Script fixes: (word, approx time, replacement or None to drop)
FIXES = [
    ("It", 2.36, "It's"),
    ("is", 2.50, None),
    ("a", 12.30, None),
    ("thousand", 12.52, "thousands"),
    ("upper", 19.76, "upper GI"),
    ("gyandoscopy", 20.00, "endoscopy"),
    ("the", 22.94, None),
    ("the", 27.24, None),
    ("the", 32.68, None),
    ("the", 37.10, None),
    ("the", 42.84, None),
    ("the", 43.44, None),
    ("anemia", 30.28, "anaemia,"),
    ("advanced", 46.82, "an advanced"),
]
for word, near, rep in FIXES:
    i = find(word, near)
    if rep is None:
        # give the dropped word's time to the next word so highlighting stays continuous
        words[i + 1]["s"] = words[i]["s"]
        words[i]["drop"] = True
    else:
        words[i]["w"] = rep
words = [w for w in words if not w.get("drop")]
# the trailing "." on "intestine." etc. is kept; tidy a couple of tokens
for w in words:
    if w["w"] == "it's" and abs(w["s"] - 46.16) < 0.05:
        w["w"] = "it's"

EMPHASIS = {
    "not", "medicine", "camera", "intestine", "swallows", "thousands", "images",
    "recording", "device", "cannot", "bleeding", "iron", "deficiency", "anaemia",
    "crohn's", "biopsies", "treatment", "retention", "narrowing", "diagnostic",
    "investigation", "water", "colonoscopy", "gi", "endoscopy",
}

# Captions hidden while a full-screen title says the same thing.
CAPTION_MUTE = [(16.05, 18.0)]

# Hand-written caption phrases (display text, with corrected punctuation).
PHRASES = [
    "The capsule you see here", "is NOT a medicine.", "It's actually a small camera",
    "that records information", "about your small intestine.", "The patient swallows",
    "this capsule with water", "and as it travels", "through the digestive tract",
    "it captures", "thousands of images", "that are transmitted", "to a recording device.",
    "This is because", "the upper GI endoscopy", "and the colonoscopy", "cannot examine most",
    "of the small intestine.", "Capsule endoscopy", "is especially important",
    "for evaluation of", "small bowel bleeding,", "unexplained iron", "deficiency anaemia,",
    "and selected patients", "with suspicion of", "small bowel", "Crohn's disease.",
    "But remember,", "this capsule cannot", "take biopsies", "or perform treatment.",
    "Capsule retention", "is the main consideration", "here, especially in", "people with",
    "small bowel narrowing.", "So it's not a medicine,", "it's an advanced",
    "diagnostic investigation.",
]


def norm(x):
    return "".join(ch for ch in x.lower() if ch.isalnum() or ch in " '").split()


visible = [w for w in words if not any(a <= w["s"] < b for a, b in CAPTION_MUTE)]
chunks, k = [], 0
for phrase in PHRASES:
    target, got, cur = norm(phrase), [], []
    while got != target:
        w = visible[k]
        k += 1
        cur.append(w)
        got += norm(w["w"])
        assert got == target[: len(got)], (phrase, got)
    # display words come from the phrase so punctuation/casing follow the script fix
    pieces = phrase.split()
    j = 0
    for w in cur:
        n = len(w["w"].split())
        w["w"] = " ".join(pieces[j : j + n])
        j += n
    chunks.append(cur)
assert k == len(visible), visible[k:]

captions = []
for c in chunks:
    captions.append({
        "start": round(remap(c[0]["s"]), 3),
        "end": round(remap(c[-1]["e"]), 3),
        "words": [
            {
                "w": x["w"],
                "s": round(remap(x["s"]), 3),
                "e": round(remap(x["e"]), 3),
                "hi": x["w"].lower().strip(".,?") in EMPHASIS,
            }
            for x in c
        ],
    })
# hold each caption until the next one starts (max 0.6 s) so it doesn't flicker
for a, b in zip(captions, captions[1:]):
    a["end"] = round(min(b["start"], a["end"] + 0.6), 3)
captions[-1]["end"] = round(remap(SRC_DURATION), 3)

# ---------------------------------------------------------------- cues
# Named moments in source time; the renderer and the audio mixer both read these.
SRC_CUES = {
    "hook": 0.0,
    "notMedicine": 1.24,
    "camera": 3.38,
    "records": 4.46,
    "smallIntestine": 5.80,
    "journey": 6.70,
    "swallow": 7.22,
    "water": 8.38,
    "travels": 9.40,
    "captures": 11.90,
    "transmit": 14.20,
    "recorder": 14.92,
    "why": 16.10,
    "because": 18.58,
    "upperGI": 19.76,
    "colonoscopy": 21.18,
    "cannot": 21.84,
    "smallBowelMiss": 23.58,
    "capsuleEndo": 24.52,
    "usedFor": 25.68,
    "bleeding": 28.18,
    "anaemia": 29.14,
    "crohns": 31.60,
    "remember": 35.02,
    "noBiopsy": 36.38,
    "noTreatment": 38.22,
    "retention": 39.52,
    "narrowing": 43.58,
    "summary": 45.08,
    "diagnostic": 46.82,
    "outro": SRC_DURATION - 0.25,
}
cues = {k: round(remap(v), 3) for k, v in SRC_CUES.items()}

# Video punch-in zoom keyframes (edited time, zoom). "snap" = hard change (hides jump cuts).
ZOOM = [
    {"t": 0.0, "z": 1.16, "snap": True},
    {"t": cues["camera"] - 1.0, "z": 1.16},
    {"t": cues["camera"], "z": 1.0},
    {"t": remap(CUTS[0][1]), "z": 1.12, "snap": True},
    {"t": cues["why"] - 0.3, "z": 1.12},
    {"t": cues["why"], "z": 1.22},
    {"t": remap(CUTS[1][1]), "z": 1.0, "snap": True},
    {"t": cues["remember"] - 0.4, "z": 1.0},
    {"t": cues["remember"], "z": 1.12},
    {"t": cues["summary"] - 0.4, "z": 1.12},
    {"t": cues["summary"], "z": 1.2},
    {"t": DURATION, "z": 1.2},
]

out = {
    "fps": FPS,
    "duration": round(DURATION, 3),
    "srcDuration": SRC_DURATION,
    "cuts": CUTS,
    "captions": captions,
    "cues": cues,
    "zoom": ZOOM,
}
json.dump(out, open(HERE / "timeline.json", "w"), indent=1)

if __name__ == "__main__":
    print("duration", out["duration"], "frames", round(DURATION * FPS))
    for c in captions:
        print(f'{c["start"]:6.2f}-{c["end"]:6.2f}  ' + " ".join(
            ("*" + w["w"] + "*") if w["hi"] else w["w"] for w in c["words"]))
