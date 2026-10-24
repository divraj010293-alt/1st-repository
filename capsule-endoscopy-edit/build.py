"""Composite the final video: pause cuts, 1080x1920 upscale, punch-in zooms, graphics overlay, audio mix.

usage: python3 build.py <source.mp4> <overlayDir> <audioDir> <out.mp4>
"""
import json
import pathlib
import subprocess
import sys

import cv2
import numpy as np

HERE = pathlib.Path(__file__).parent
SRC, OVL, AUD, OUT = sys.argv[1:5]
TL = json.load(open(HERE / "timeline.json"))
FPS, W, H = TL["fps"], 1080, 1920
NFR = round(TL["duration"] * FPS)
HOLD = TL["duration"] - (TL["srcDuration"] - sum(b - a for a, b in TL["cuts"]))
ANCHOR = (787, 1515)  # presenter's face in 1080x1920 space; zooms centre on it

# keep-ranges of the source between the cuts
keep, prev = [], 0.0
for a, b in TL["cuts"]:
    keep.append((prev, a))
    prev = b
keep.append((prev, None))


def trim_chain(kind):
    v = kind == "v"
    parts, labels = [], []
    for i, (a, b) in enumerate(keep):
        end = f":end={b:.6f}" if b is not None else ""
        if v:
            parts.append(f"[0:v]trim=start={a:.6f}{end},setpts=PTS-STARTPTS[v{i}]")
        else:
            fade = "afade=t=in:d=0.015,areverse,afade=t=in:d=0.015,areverse"
            parts.append(f"[0:a]atrim=start={a:.6f}{end},asetpts=PTS-STARTPTS,{fade}[a{i}]")
        labels.append(f"[{'v' if v else 'a'}{i}]")
    return parts, labels


def zoom_at(t):
    ks = TL["zoom"]
    for k0, k1 in zip(ks, ks[1:]):
        if k0["t"] <= t < k1["t"]:
            if k1.get("snap"):
                return k0["z"]
            u = (t - k0["t"]) / max(1e-6, k1["t"] - k0["t"])
            u = 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
            return k0["z"] + (k1["z"] - k0["z"]) * u
    return ks[-1]["z"]


def main():
    tmp = pathlib.Path(OUT).with_suffix(".mix.wav")
    # ---- audio: cut voice, duck music under it, add SFX, normalise to -14 LUFS
    ap, al = trim_chain("a")
    voice = (";".join(ap) + f";{''.join(al)}concat=n={len(al)}:v=0:a=1,"
             f"aresample=48000,apad=pad_dur={HOLD + 0.2:.3f},highpass=f=75,"
             "acompressor=threshold=0.25:ratio=2:attack=10:release=200,volume=-4dB,asplit=2[voice][key]")
    fc = (voice + ";[1:a]volume=-4dB[mus];[mus][key]sidechaincompress=threshold=0.02:ratio=7:attack=20:release=450:makeup=1[duck];"
          "[2:a]volume=-1dB[fx];[voice][duck][fx]amix=inputs=3:normalize=0:duration=first,"
          f"atrim=end={TL['duration']:.3f}[mix]")
    pre = pathlib.Path(OUT).with_suffix(".pre.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-i", f"{AUD}/music.wav", "-i", f"{AUD}/sfx.wav",
                    "-filter_complex", fc, "-map", "[mix]", "-ar", "48000", str(pre)], check=True)
    # two-pass loudnorm
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af",
                           "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", ln, "-ar", "48000", str(tmp)], check=True)
    pre.unlink()

    # ---- video: decoded, cut and upscaled by ffmpeg; zoom + overlay here
    vp, vl = trim_chain("v")
    vf = (";".join(vp) + f";{''.join(vl)}concat=n={len(vl)}:v=1:a=0,fps={FPS},"
          f"scale={W}:{H}:flags=lanczos,tpad=stop_mode=clone:stop_duration={HOLD + 0.5:.3f},format=bgr24[v]")
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-filter_complex", vf, "-map", "[v]",
                            "-frames:v", str(NFR), "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", str(tmp), "-map", "0:v", "-map", "1:a",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                            "-profile:v", "high", "-movflags", "+faststart",
                            "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
    fsize = W * H * 3
    for i in range(NFR):
        buf = dec.stdout.read(fsize)
        if len(buf) < fsize:
            raise SystemExit(f"decoder ended early at frame {i}")
        frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        z = zoom_at(i / FPS)
        if abs(z - 1) > 1e-4:
            ax, ay = ANCHOR
            M = np.float32([[z, 0, ax * (1 - z)], [0, z, ay * (1 - z)]])
            frame = cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        ov = cv2.imread(f"{OVL}/f_{i:05d}.png", cv2.IMREAD_UNCHANGED)
        a = ov[:, :, 3:4].astype(np.float32) / 255
        frame = (frame.astype(np.float32) * (1 - a) + ov[:, :, :3].astype(np.float32) * a).astype(np.uint8)
        enc.stdin.write(frame.tobytes())
        if i % 150 == 0:
            print(f"frame {i}/{NFR}", flush=True)
    enc.stdin.close()
    enc.wait()
    dec.kill()
    tmp.unlink()
    print("wrote", OUT)


main()
