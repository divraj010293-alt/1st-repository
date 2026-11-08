"""Timeline for the liver cirrhosis & exercise explainer: Hinglish captions and scene cues.

Phrase start times (source seconds) come from Whisper segment times on the Hindi recording,
checked against a pause map of the voice (speech level - 14 dB). Words inside a phrase are
spread by length. There are no cuts, so source time = edited time; an end card follows.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
FPS = 30
SRC_DURATION = 103.34
END_CARD = 3.6

# "start | [cue] phrase" ; *word = emphasised ; [+cue] marks a moment inside a scene
PHRASES = """
0.00 | [hook] Kya *liver *cirrhosis hone par
1.55 | patient ko zyada se zyada
2.75 | *aaram karna chahiye
3.78 | aur *physical *activity se
4.70 | *bachna chahiye?
5.86 | [+no] Ji *nahi,
6.30 | aisa *bilkul *nahi hai.
7.50 | [+yes] Balki liver cirrhosis patients ke liye
9.40 | *exercise karna
10.20 | aur *zyada *important hai.
11.92 | [muscle] Liver cirrhosis jo hai,
12.90 | wo sirf *liver ko
13.80 | affect nahi karta.
15.60 | Isme dheere-dheere
16.50 | [+weak] hamari body ki *muscles bhi
17.60 | *weak hone lagti hain,
18.60 | [+sarco] jise hum bolte hain *sarcopenia.
19.80 | [+effects] To muscle weakness ki wajah se
20.90 | patient ko *kamzori feel ho sakti hai,
22.60 | [+walkcap] *chalne-phirne ki kshamta
23.60 | *kam ho sakti hai,
25.00 | [+health] aur *overall *health par bhi
26.20 | effect aa sakta hai.
27.76 | [which] To aaiye samajhte hain
28.90 | liver cirrhosis wale patient ko
30.30 | *kaun-kaun si *exercises karni chahiye.
31.96 | [walk] To sabse pehle hai *walking.
33.20 | [+mins] Hamein rozana *15-20 *minute
34.60 | walk karni chahiye,
36.38 | [+increase] aur dheere-dheere *capacity ke according
37.90 | us *duration ko badha sakte hain.
39.56 | [strength] Doosri hain
40.20 | *muscle *strengthening exercises,
41.74 | [+chair] jaise *chair se
42.60 | *uthna-baithna,
43.92 | [+wall] *wall *push-ups karna,
45.96 | [+band] aur kuch cases mein
47.00 | *resistance *band exercises
48.98 | bhi kar sakte hain.
50.86 | [+mass] In exercises se
51.90 | *muscle *strength aur
53.00 | *muscle *mass badhta hai.
55.38 | [balance] Teesri exercise hai
56.60 | *balance and *flexibility exercises.
58.44 | [+stretch] Isme hum muscle *stretching
59.40 | kar sakte hain,
60.80 | [+chairbal] *chair ki madad se
61.70 | *balance exercises kar sakte hain.
63.10 | [+mobility] To in exercises se
64.00 | body mein *balance aur *mobility
65.30 | behtar rehne mein madad milti hai.
66.92 | [caution] Lekin *yaad *rakhiye,
67.90 | [+ascites] agar liver cirrhosis ki wajah se
69.40 | *pet mein *paani bahut bhar gaya hai,
71.84 | [+bleed] ya phir recently
73.52 | *hematemesis, yaani
74.40 | *khoon ki *ulti hui hai,
76.24 | [+he] ya phir patient
77.20 | *hepatic *encephalopathy mein hai,
79.22 | [+consult] to in cases mein
80.00 | exercise shuru karne se *pehle
81.70 | [+gastro] *gastroenterologist ki *salaah
82.70 | leni chahiye.
83.98 | [summary] To yaad rakhiye,
84.90 | liver cirrhosis mein sirf liver ka
86.20 | *ilaaj karna *kaafi *nahi,
87.78 | [+muscles] balki apni *muscles ko bhi
89.00 | *strong banaye rakhna hai,
90.30 | jiske liye hum kai exercises
92.22 | kar sakte hain.
92.90 | [+part] Apni *muscle *strength
93.90 | aur *muscle *mass ko banaye rakhna
95.30 | bhi *treatment ka
96.00 | ek *mahatvapurn *hissa hai.
97.82 | [routine] Isliye apni *dawaiyon
98.90 | aur *sahi *khaan-paan ke saath-saath,
100.58 | [+daily] *exercise ko bhi apne
101.70 | *daily *routine ka hissa banaiye.
"""

phrases = []
for line in PHRASES.strip().splitlines():
    t, text = line.split(" | ", 1)
    cue = None
    if text.startswith("["):
        cue, text = text[1:].split("] ", 1)
        cue = cue.lstrip("+")
    words = [{"w": w.lstrip("*"), "hi": w.startswith("*")} for w in text.split()]
    phrases.append({"t": float(t), "cue": cue, "words": words})
assert all(a["t"] < b["t"] for a, b in zip(phrases, phrases[1:]))

captions, cues = [], {}
for i, p in enumerate(phrases):
    s = p["t"]
    nxt = phrases[i + 1]["t"] if i + 1 < len(phrases) else SRC_DURATION
    speak = max(0.4, (nxt - s) * 0.92)
    lens = [len(w["w"]) + 2 for w in p["words"]]
    acc, ws = 0, []
    for w, L in zip(p["words"], lens):
        ws.append({"w": w["w"], "hi": w["hi"], "s": round(s + speak * acc / sum(lens), 3)})
        acc += L
    captions.append({"start": s, "end": round(min(nxt, s + speak + 0.5), 3), "words": ws})
    if p["cue"]:
        cues[p["cue"]] = s

cues["outro"] = SRC_DURATION
DURATION = round(round((SRC_DURATION + END_CARD) * FPS) / FPS, 3)
out = {"fps": FPS, "duration": DURATION, "srcDuration": SRC_DURATION, "captions": captions, "cues": cues}
json.dump(out, open(HERE / "timeline.json", "w"), indent=1, ensure_ascii=False)

if __name__ == "__main__":
    print("duration", DURATION, "phrases", len(phrases), "cues", len(cues))
