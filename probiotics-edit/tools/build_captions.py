"""Build compositions/captions.html from assets/transcript.raw.json.

Whisper's word timings and a few transcription/script slips are corrected here, then the
words are grouped (punctuation, a pause of 300 ms+, or 4 words / 22 characters) and written
out as timed caption groups. Re-run after editing the transcript:

    python3 tools/build_captions.py
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
END = 54.9  # captions stop where the end card takes over

# word index -> replacement text ("" drops the word and gives its time to the previous one)
TEXT_FIX = {
    "valory": "pylori",          # H. pylori, misheard
    "includes": "include",
}
# fixes keyed by (index of first word of phrase, phrase) so repeated words stay unambiguous
PHRASE_FIX = [
    (["taken", "an", "adequate", "amount"], ["taken", "in", "adequate", "amounts"]),
    (["help", "you", "from", "the", "diarrhea"], ["help", "prevent", "", "", "diarrhoea"]),
    (["includes", "the", "foods"], ["include", "", "foods"]),
    (["as", "the", "curd"], ["as", "", "curd"]),
    (["and", "the", "buttermilk."], ["and", "", "buttermilk."]),
    (["for", "the", "IBS,"], ["for", "", "IBS,"]),
    (["evidence", "based"], ["evidence-based", ""]),
]
# word starts that whisper placed inside a measured silence (silencedetect -35 dB)
START_FIX = {"They@24.92": 25.2, "Not@28.18": 28.82, "Follow@54.24": 54.95}
EMPHASIS = {"probiotics", "probiotics?", "probiotics,", "probiotic", "good.", "good", "live",
            "antibiotics.", "pylori", "uncertain.", "fibre", "curd", "buttermilk.", "magic",
            "right", "difference."}


def load_words():
    raw = json.loads((ROOT / "assets/transcript.raw.json").read_text())
    words = [{"text": w["text"], "start": w["start"], "end": w["end"]} for w in raw]
    for w in words:
        key = f'{w["text"]}@{w["start"]:.2f}'
        if key in START_FIX:
            w["start"] = START_FIX[key]
        w["text"] = TEXT_FIX.get(w["text"], w["text"])
    texts = [w["text"] for w in words]
    for src, dst in PHRASE_FIX:
        src = [TEXT_FIX.get(s, s) for s in src]
        for i in range(len(texts) - len(src) + 1):
            if texts[i:i + len(src)] == src:
                for j, d in enumerate(dst):
                    words[i + j]["text"] = d
    out = []
    for w in words:
        if not w["text"]:
            out[-1]["end"] = w["end"]
            continue
        w["text"] = w["text"].replace("fiber", "fibre")
        out.append(w)
    # keep starts monotonic and ends after starts
    for a, b in zip(out, out[1:]):
        a["end"] = max(a["start"] + 0.08, min(a["end"], b["start"]))
    return [w for w in out if w["start"] < END]


def group(words):
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        chars = sum(len(x["text"]) + 1 for x in cur)
        brk = (
            nxt is None
            or (w["text"][-1] in ".?!," and w["text"] != "H.")
            or nxt["start"] - w["end"] >= 0.3
            or len(cur) >= 4
            or chars + len(nxt["text"]) > 22
        )
        if brk:
            groups.append(cur)
            cur = []
    return groups


def main():
    words = load_words()
    groups = group(words)
    (ROOT / "assets/transcript.json").write_text(json.dumps(
        [{"id": f"w{i}", "text": w["text"], "start": round(w["start"], 3), "end": round(w["end"], 3)}
         for i, w in enumerate(words)], indent=1))
    rows = []
    timing = []
    for gi, g in enumerate(groups):
        start = max(0.1, g[0]["start"] - 0.05)
        nxt = groups[gi + 1][0]["start"] - 0.05 if gi + 1 < len(groups) else END
        end = min(nxt, max(g[-1]["end"] + 0.35, start + 0.6), END)
        spans = []
        wt = []
        for wi, w in enumerate(g):
            bare = w["text"].lower().strip(".,?!")
            cls = "w hi" if w["text"].lower() in EMPHASIS or bare in EMPHASIS else "w"
            spans.append(f'<span id="cg{gi}-{wi}" class="{cls}">{html.escape(w["text"])}</span>')
            wt.append(round(w["start"] - start, 3))
        rows.append(
            f'    <div id="cg{gi}" class="clip cg" data-start="{start:.2f}" '
            f'data-duration="{end - start:.2f}" data-track-index="0">{" ".join(spans)}</div>'
        )
        timing.append({"g": f"cg{gi}", "start": round(start, 3), "end": round(end, 3), "words": wt})

    page = TEMPLATE.replace("%ROWS%", "\n".join(rows)).replace("%TIMING%", json.dumps(timing))
    (ROOT / "compositions/captions.html").write_text(page)
    print(f"{len(words)} words, {len(groups)} groups")


TEMPLATE = """<template>
  <style>
    #root {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    /* full-width row centred just above the speaker's head */
    .cg {
      position: absolute;
      left: 0;
      right: 0;
      top: 1150px;
      height: 96px;
      text-align: center;
      overflow: visible;
      font-family: "Inter", sans-serif;
      font-weight: 900;
      font-size: 64px;
      line-height: 96px;
      letter-spacing: -0.01em;
      white-space: nowrap;
    }
    .cg .w {
      display: inline-block;
      color: #fff;
      -webkit-text-stroke: 12px rgba(0, 0, 0, 0.85);
      paint-order: stroke fill;
      text-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
      margin: 0 11px;
    }
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
%ROWS%
  </div>
  <script>
    const TIMING = %TIMING%;
    const tl = gsap.timeline({ paused: true });
    TIMING.forEach(({ g, start, end, words }) => {
      const el = document.getElementById(g);
      tl.fromTo(el, { opacity: 0, scale: 0.86 }, { opacity: 1, scale: 1, duration: 0.18, ease: "back.out(2.2)" }, start);
      words.forEach((at, i) => {
        const w = document.getElementById(`${g}-${i}`);
        const said = w.classList.contains("hi") ? "#8AF5E8" : "#FFFFFF";
        const next = i + 1 < words.length ? start + words[i + 1] : end;
        tl.fromTo(w, { color: "#FFFFFF", scale: 1 }, { color: "#FFD23F", scale: 1.08, duration: 0.12, ease: "power2.out" }, start + at);
        tl.to(w, { color: said, scale: 1, duration: 0.1, ease: "power1.out" }, Math.max(start + at + 0.12, next - 0.02));
      });
      tl.to(el, { opacity: 0, duration: 0.1, ease: "power2.in" }, end - 0.1);
      tl.set(el, { opacity: 0, visibility: "hidden" }, end);
    });
    window.__timelines["captions"] = tl;
  </script>
</template>
"""

if __name__ == "__main__":
    main()
