"""Synthesise the music bed and sound effects for the edit (48 kHz stereo WAVs).

usage: python3 audio.py <outDir>
Everything is generated here from oscillators and filtered noise, so there are no
third-party samples to license.
"""
import json
import pathlib
import sys
import wave

import numpy as np
from scipy import signal

HERE = pathlib.Path(__file__).parent
SR = 48000
TL = json.load(open(HERE / "timeline.json"))
Q = TL["cues"]
DUR = TL["duration"]
N = int(DUR * SR)
rng = np.random.default_rng(7)


def tt(d):
    return np.arange(int(d * SR)) / SR


def env_ad(n, a, d_curve=None):
    """Attack (seconds) then exponential decay to the end of n samples."""
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    if d_curve is not None:
        e[na:] = np.exp(-np.arange(n - na) / SR / d_curve)
    return e


def sweep(f0, f1, d, curve="exp"):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d) if curve == "exp" else np.linspace(f0, f1, len(t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def bandnoise(d, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, rng.standard_normal(int(d * SR)))


def swept_noise(d, f0, f1, q=1.2):
    """Noise through a band-pass whose centre glides f0 -> f1 (block-wise, state carried)."""
    x = rng.standard_normal(int(d * SR))
    out = np.zeros_like(x)
    blk = 256
    zi = None
    for i in range(0, len(x), blk):
        k = i / len(x)
        fc = f0 * (f1 / f0) ** k
        bw = fc / q
        sos = signal.butter(1, [max(30, fc - bw / 2), min(SR / 2 - 100, fc + bw / 2)], btype="band", fs=SR, output="sos")
        if zi is None:
            zi = signal.sosfilt_zi(sos) * 0
        out[i:i + blk], zi = signal.sosfilt(sos, x[i:i + blk], zi=zi)
    return out


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


# ------------------------------------------------------------------ SFX
def whoosh(d=0.55, up=True):
    n = swept_noise(d, 250 if up else 3500, 3500 if up else 250, q=1.0)
    t = tt(d)
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.6
    return norm(n * e, 0.8)


def pop(f0=650, f1=220, d=0.09):
    return norm(sweep(f0, f1, d) * env_ad(int(d * SR), 0.002, 0.025), 0.8)


def tick():
    a = np.sin(2 * np.pi * 1320 * tt(0.09)) * env_ad(int(0.09 * SR), 0.001, 0.02)
    b = np.sin(2 * np.pi * 1980 * tt(0.22)) * env_ad(int(0.22 * SR), 0.001, 0.06)
    out = np.zeros(int(0.3 * SR))
    out[:len(a)] += a
    o = int(0.06 * SR)
    out[o:o + len(b)] += b
    return norm(out, 0.55)


def shutter():
    out = np.zeros(int(0.12 * SR))
    for off, g in [(0, 1.0), (0.055, 0.7)]:
        n = bandnoise(0.018, 2500, 9000) * env_ad(int(0.018 * SR), 0.0005, 0.005) * g
        o = int(off * SR)
        out[o:o + len(n)] += n
    return norm(out, 0.7)


def gulp():
    d = 0.22
    t = tt(d)
    f = 260 * (110 / 260) ** (t / d)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + 0.4 * np.sin(2 * np.pi * 28 * t))
    return norm(x * env_ad(len(t), 0.01, 0.07), 0.7)


def droplet():
    return norm(sweep(700, 1700, 0.07) * env_ad(int(0.07 * SR), 0.001, 0.02), 0.5)


def blip(f=1500, d=0.045):
    x = signal.square(2 * np.pi * f * tt(d)) * 0.4 + np.sin(2 * np.pi * f * tt(d))
    sos = signal.butter(2, 5000, fs=SR, output="sos")
    return norm(signal.sosfilt(sos, x) * env_ad(int(d * SR), 0.002, 0.015), 0.35)


def impact():
    d = 1.2
    sub = sweep(110, 38, d) * env_ad(int(d * SR), 0.003, 0.35)
    crack = bandnoise(0.25, 200, 4000) * env_ad(int(0.25 * SR), 0.001, 0.05)
    out = sub * 1.0
    out[:len(crack)] += crack * 0.6
    return norm(out, 0.95)


def thud(f=90):
    return norm(sweep(f * 1.8, f, 0.25) * env_ad(int(0.25 * SR), 0.002, 0.07), 0.7)


def buzz():
    out = np.zeros(int(0.32 * SR))
    for off, f in [(0, 233), (0.14, 175)]:
        t = tt(0.14)
        x = signal.sawtooth(2 * np.pi * f * t, 0.5)
        sos = signal.butter(2, 1400, fs=SR, output="sos")
        x = signal.sosfilt(sos, x) * env_ad(len(t), 0.004, 0.06)
        o = int(off * SR)
        out[o:o + len(x)] += x
    return norm(out, 0.45)


def bell(f=880, d=1.4, partials=((1, 1), (2.76, .45), (5.4, .25), (8.93, .12))):
    t = tt(d)
    x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * (2.2 + r * 0.9)) for r, a in partials)
    x[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return norm(x, 0.6)


def chime():
    out = np.zeros(int(1.6 * SR))
    for off, f in [(0, 1046.5), (0.09, 1318.5), (0.18, 1568)]:
        b = bell(f, 1.3)
        o = int(off * SR)
        out[o:o + len(b)] += b
    return norm(out, 0.5)


def alert():
    out = np.zeros(int(0.6 * SR))
    for off, f in [(0, 784), (0.16, 659)]:
        b = bell(f, 0.42, partials=((1, 1), (2, .3)))
        o = int(off * SR)
        out[o:o + len(b)] += b
    return norm(out, 0.5)


def riser(d=1.0):
    t = tt(d)
    n = swept_noise(d, 300, 6000, q=2.0) * (t / d) ** 2
    s = sweep(200, 900, d) * (t / d) ** 2 * 0.3
    return norm(n + s, 0.6)


def shimmer():
    out = np.zeros(int(1.8 * SR))
    for i, f in enumerate([1568, 2093, 2637, 3136, 2637]):
        b = bell(f, 1.0) * 0.6
        o = int(i * 0.07 * SR)
        out[o:o + len(b)] += b
    return norm(out, 0.4)


sfx = np.zeros((N + SR * 2, 2))


def place(t, x, gain_db=0.0, pan=0.0):
    i = int(t * SR)
    if i < 0:
        x, i = x[-i:], 0
    g = 10 ** (gain_db / 20)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    sfx[i:i + len(x), 0] += x * g * l * 1.414
    sfx[i:i + len(x), 1] += x * g * r * 1.414


place(0.0, impact(), -8)
place(0.0, whoosh(0.4), -12)
place(2.3, pop(), -6)
place(2.45, buzz(), -7)
place(Q["lab"] - 0.1, whoosh(0.5), -9)
place(Q["hbsag"] + 0.8, thud(120), -4)
place(Q["hbsag"] + 0.85, pop(900, 300, 0.07), -10)
for k in range(8):
    place(Q["dnaTest"] + 0.6 + k * 0.45, blip(1300 + 200 * (k % 3)), -16, 0.2)
place(Q["undetectable"], thud(120), -5)
place(Q["undetectable"] + 0.05, tick(), -9)
place(Q["doctor"] - 0.15, whoosh(0.4), -12)
place(Q["doctor"] + 0.1, pop(), -8, -0.4)
place(Q["patient"] - 0.1, pop(), -10, 0.4)
place(Q["thought"] - 0.2, pop(700, 400, 0.1), -8, 0.4)
place(Q["years"] - 0.1, whoosh(0.5), -8)
for k in range(6):
    place(Q["years"] + 0.2 + k * 0.22, shutter(), -14)
place(Q["noFollow"], buzz(), -6)
place(Q["important"] - 0.2, whoosh(0.3), -8)
place(Q["important"] + 0.7, impact(), -4)
place(Q["decodeA"] - 0.1, whoosh(0.45), -10)
place(Q["present"], tick(), -9)
place(Q["decodeB"] - 0.1, whoosh(0.45), -10)
place(Q["graph"] - 0.1, pop(), -8)
place(Q["graph"] + 0.1, whoosh(2.2, up=False), -18)
place(Q["limit"] - 0.2, blip(1800), -10)
place(Q["limit"] + 0.3, alert(), -12)
place(Q["notEliminated"] - 0.15, whoosh(0.5), -9)
place(Q["eliminate"] + 0.4, buzz(), -8)
place(Q["oneReport"] - 0.15, whoosh(0.45), -9)
place(Q["decision"] + 0.3, pop(), -6)
place(Q["decision"] + 0.4, buzz(), -8)
place(Q["sgpt"] - 0.4, whoosh(0.4), -12)
for c in ("sgpt", "dna", "fibrosis", "risk"):
    place(Q[c] - 0.1, pop(), -7)
place(Q["easl"] - 0.15, whoosh(0.5), -9)
place(Q["easl"] + 0.1, chime(), -10)
place(Q["regular"], tick(), -7)
place(Q["year1"] - 0.35, whoosh(0.5), -10)
for c in ("year1", "phase", "hbsagYearly", "fibroAssess"):
    place(Q[c] - 0.15, pop(), -7)
    place(Q[c] + 0.2, tick(), -11)
place(Q["every36"], blip(2000), -12)
place(Q["yaad"] - 0.15, whoosh(0.5), -9)
place(Q["yaad"], alert(), -7)
place(Q["today"] - 0.15, pop(), -8, -0.4)
place(Q["future"] - 0.15, pop(), -8, 0.4)
place(Q["future"] + 0.2, thud(80), -7)
place(Q["cirrhosis"] - 0.1, whoosh(0.45), -10)
place(Q["cirrhosis"] + 0.3, alert(), -11)
place(Q["careful"] + 0.3, tick(), -8)
place(Q["symptoms"] - 0.2, whoosh(0.5), -9)
place(Q["safe"] - 0.25, pop(), -8, 0.4)
place(Q["safe"] + 0.7, buzz(), -8)
place(Q["final"] - 0.1, whoosh(0.45), -10)
place(Q["final"] + 0.4, thud(110), -6)
place(Q["finalDna"] + 0.7, thud(110), -6)
place(Q["conclusion"] - 0.7, riser(0.7), -12)
place(Q["conclusion"] + 0.25, impact(), -5)
place(Q["conclusion"] + 0.35, chime(), -8)
place(Q["conclusion"] + 0.8, tick(), -9)
place(Q["hcc"] - 0.15, whoosh(0.5), -8)
place(Q["hcc"] + 0.05, alert(), -9)
place(Q["hcc"] + 0.4, pop(), -8)
for k in range(4):
    place(Q["hcc"] + 0.6 + k * 0.38, blip(1700, 0.035), -18)
place(Q["hcc"] + 0.8, pop(), -7)
place(Q["hcc"] + 1.1, tick(), -9)
place(Q["outro"] - 0.1, whoosh(0.6), -8)
place(Q["outro"] + 0.1, chime(), -9)
for k in range(3):
    place(Q["outro"] + 0.9 + k * 0.15, pop(700 + 120 * k, 300, 0.07), -10, -0.5 + 0.5 * k)
sfx = sfx[:N]

# ------------------------------------------------------------------ music
BPM = 88
beat = 60 / BPM
bar = 4 * beat


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


# Dm9 - Bbmaj7 - Fmaj7 - C6, two bars each (calmer, more serious than the capsule edit)
CHORDS = [
    (38, [57, 60, 62, 65, 69]),
    (46, [57, 58, 62, 65, 69]),
    (41, [57, 60, 64, 65, 69]),
    (48, [55, 60, 64, 67, 69]),
]
music = np.zeros((N + SR * 4, 2))


def add(t0, x, pan=0.0, g=1.0):
    i = int(t0 * SR)
    if i >= len(music):
        return
    x = x[: len(music) - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    music[i:i + len(x), 0] += x * g * l
    music[i:i + len(x), 1] += x * g * r


def pad_note(f, d):
    t = tt(d)
    x = sum(signal.sawtooth(2 * np.pi * f * (1 + det) * t + ph) for det, ph in [(-0.004, 0), (0, 1.3), (0.0045, 2.1)])
    sos = signal.butter(2, 900, fs=SR, output="sos")
    x = signal.sosfilt(sos, x)
    e = np.minimum(1, t / 0.8) * np.minimum(1, (d - t) / 0.9)
    return x * e


def pluck(f, d=0.6):
    t = tt(d)
    x = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t))
    return x * np.exp(-t / 0.16) * np.minimum(1, t / 0.003)


def kick():
    return sweep(140, 45, 0.3) * env_ad(int(0.3 * SR), 0.001, 0.09)


def hat():
    return bandnoise(0.06, 6000, 14000) * env_ad(int(0.06 * SR), 0.0005, 0.015)


total_bars = int(np.ceil((DUR + 2) / bar))
for b in range(total_bars):
    t0 = b * bar
    root, notes = CHORDS[(b // 2) % 4]
    if b % 2 == 0:
        for k, m in enumerate(notes[:4]):
            add(t0, pad_note(midi(m), 2 * bar + 0.8), pan=-0.5 + k / 3, g=0.05)
        add(t0, np.sin(2 * np.pi * midi(root) * tt(2 * bar)) * np.minimum(1, tt(2 * bar) / 0.05)
            * np.minimum(1, (2 * bar - tt(2 * bar)) / 0.3), g=0.16)
    # arpeggio: 8ths, pattern over chord tones an octave up
    pat = [0, 2, 4, 3, 1, 3, 2, 4]
    for k in range(8):
        f = midi(notes[pat[k]] + 12)
        add(t0 + k * beat / 2, pluck(f), pan=(-0.35 if k % 2 else 0.35), g=0.10 if k % 2 else 0.13)
    # light beat from bar 2 on: kick on 1 & 3, hats on the off-beats
    if b >= 1:
        for k in (0, 2):
            add(t0 + k * beat, kick(), g=0.32)
        for k in range(4):
            add(t0 + k * beat + beat / 2, hat(), pan=0.25, g=0.05)

# simple stereo echo on the whole bed
d = int(beat * 0.75 * SR)
echo = np.zeros_like(music)
echo[d:, 0] = music[:-d, 1] * 0.25
echo[d:, 1] = music[:-d, 0] * 0.25
music = music + echo
music = music[:N]
# fade in, and fade out over the last 1.6 s
fi, fo = int(0.6 * SR), int(1.6 * SR)
music[:fi] *= np.linspace(0, 1, fi)[:, None]
music[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
music = norm(music, 0.5)
sfx = np.clip(sfx, -1, 1)


def write(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


out = pathlib.Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
write(out / "music.wav", music)
write(out / "sfx.wav", sfx)
print("wrote", out / "music.wav", out / "sfx.wav", f"{DUR:.2f}s")
