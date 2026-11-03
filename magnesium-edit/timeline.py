"""Build the edit timeline for the magnesium & sleep explainer.

Scenes hang off named caption phrases, so the whole edit re-times from one list of phrase
start times. Until the voiceover is recorded, phrase times are estimated from a typical
Hindi speaking pace (draft). Once a voiceover exists (tts.py writes one), its phrase start
times go in phrase_times.json (one per phrase, then the end of speech) and this picks them up.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
FPS = 30
SEC_PER_WORD = 0.30   # calibrated on Dr Mahar's Hep B recording (0.35 s/word incl. pauses)
PHRASE_GAP = 0.08
SENTENCE_GAP = 0.35   # after a phrase ending in . ? : !
SECTION_GAP = 0.50    # before a [cue] that starts a new scene
END_CARD = 4.0

# "[cue] phrase" starts a scene (with a pause before it); "[+cue] phrase" marks a moment inside
# a scene. *word = emphasised in captions. Hinglish, matching script.md line by line.
PHRASES = """
[hook] *Magnesium *Glycinate:
kya sach mein *natural *sleeping *pill hai?
[trend] Aajkal *neend na aaye,
toh log turant
[+mag] *Magnesium *tablets ki salaah
dene lagte hain.
[question] Lekin *scientific *evidence
kya kehta hai?
[three] *3 badi *studies ne
kya paaya, dekhiye.
[s1] *2021 mein *BMC Complementary
Medicine and Therapies mein
[+s1meta] ek *systematic *review
aur *meta-analysis prakashit hua.
[s1n] Ismein *3 randomized
controlled trials
aur kul *151 buzurg participants
shaamil the.
[s1sol] Magnesium lene se,
*placebo ki tulna mein,
sone mein lagne wala samay
[+s17] lagbhag *17 *minute kam hua.
[s1tst] Lekin *total *sleep *time mein
koi significant *farak *nahi tha.
[s1q] Aur in studies mein
evidence ki *quality
*low se *very *low thi.
[s2] *2025 mein ek randomized
placebo-controlled *trial aaya,
[s2n] jismein kharab neend wale
*155 healthy adults shaamil the.
[s2dose] *4 hafte tak roz
*Magnesium *Bisglycinate,
[+s2mg] *250 mg elemental magnesium,
dene par
[s2res] insomnia severity mein
placebo se *thoda zyada
sudhaar hua.
[s2small] Lekin effect size
*bahut *chhota tha.
[s3] Aur *2026 ki ek
*systematic *review ne
[+s3grid] *12 randomized trials
ka analysis kiya.
[s3c] Conclusion:
abhi insomnia ke
*routine treatment ke liye
magnesium ko recommend karne ke liye
[+s3nahi] *paryaapt *evidence *nahi hai.
[close] Toh kya Magnesium
*bilkul kaam nahi karta?
[+closeNo] Aisa kehna bhi sahi nahi hoga.
[some] *Kuch logon ko
fayda ho sakta hai,
[+some2] lekin *har us vyakti ko
jise neend nahi aati,
Magnesium tablets ki
*zaroorat *nahi hai.
[cbti] Lambe samay ki insomnia ka
*first-line treatment
[+cbti2] *CBT-I, yaani *sleep *therapy hai.
[doc] Aur agar *3 *mahine se zyada
neend ki problem hai,
toh *doctor se miliye.
[side] Magnesium se
*loose *motions ho sakte hain,
[gap] aur kuch *antibiotics
aur osteoporosis ki dawaon se
*2 *ghante ka gap rakhein.
[kidney] Agar aapko *kidney ki bimari hai,
toh bina doctor ki salaah
Magnesium supplements
*bilkul *na lein.
[yaad] Yaad rakhiye:
Magnesium ek *essential *mineral hai,
[+yaad2] lekin koi *proven *sleeping *pill nahi.
[cta] Aisi aur *evidence-based jaankari ke liye
[+follow] *follow karein, aur *share karein.
"""

phrases = []
for line in PHRASES.strip().splitlines():
    cue, sub = None, False
    if line.startswith("["):
        cue, line = line[1:].split("] ", 1)
        sub = cue.startswith("+")
        cue = cue.lstrip("+")
    words = [{"w": w.lstrip("*"), "hi": w.startswith("*")} for w in line.split()]
    phrases.append({"cue": cue, "sub": sub, "words": words})

times_file = HERE / "phrase_times.json"
if times_file.exists():
    starts = json.load(open(times_file))
    assert len(starts) in (len(phrases), len(phrases) + 1), (len(starts), len(phrases))  # optional trailing end-of-speech
    mode = "recorded"
else:
    starts, t = [], 0.3
    for i, p in enumerate(phrases):
        if p["cue"] and not p["sub"] and i:
            t += SECTION_GAP
        starts.append(round(t, 3))
        t += len(p["words"]) * SEC_PER_WORD
        last = p["words"][-1]["w"]
        t += SENTENCE_GAP if last[-1] in ".?:!" else PHRASE_GAP
    starts.append(round(t, 3))  # end of speech
    mode = "draft"

speech_end = starts[len(phrases)] if len(starts) > len(phrases) else starts[-1] + 2.0
captions, cues = [], {}
for i, p in enumerate(phrases):
    s = starts[i]
    nxt = starts[i + 1] if i + 1 < len(starts) else speech_end
    speak = max(0.3, nxt - s - (SENTENCE_GAP if p["words"][-1]["w"][-1] in ".?:!" else PHRASE_GAP))
    # spread words across the phrase by length (vowel-heavy Hindi: chars are a fair proxy)
    lens = [len(w["w"]) + 2 for w in p["words"]]
    acc, ws = 0, []
    for w, L in zip(p["words"], lens):
        ws.append({"w": w["w"], "hi": w["hi"], "s": round(s + speak * acc / sum(lens), 3)})
        acc += L
    captions.append({"start": round(s, 3), "end": round(min(nxt, s + speak + 0.6), 3), "words": ws})
    if p["cue"]:
        cues[p["cue"]] = round(s, 3)

cues["outro"] = round(speech_end + 0.3, 3)
DURATION = round(round((cues["outro"] + END_CARD) * FPS) / FPS, 3)

out = {"fps": FPS, "mode": mode, "duration": DURATION, "speechEnd": speech_end,
       "captions": captions, "cues": cues}
json.dump(out, open(HERE / "timeline.json", "w"), indent=1, ensure_ascii=False)

if __name__ == "__main__":
    print(mode, "duration", DURATION, "phrases", len(phrases), "cues", len(cues))
