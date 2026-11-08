"""Composite the cirrhosis & exercise explainer: original video with its navy background keyed to
white, graphics overlay, end-card hold,
voice levelled and lightly de-hissed, plus sound effects. No music.

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
HOLD = TL["duration"] - TL["srcDuration"]
NAVY = np.array([85, 33, 24], np.float32)  # studio background, BGR
KEY_LO, KEY_HI = 8.0, 66.0                  # colour distance: fully background below LO, untouched above HI

pre = pathlib.Path(OUT).with_suffix(".pre.wav")
mix = pathlib.Path(OUT).with_suffix(".mix.wav")
# The recording arrives very loud and over-compressed (about -9 LUFS) with hiss in the pauses:
# turn it down first, take a little hiss off, then add the effects and normalise.
fc = ("[0:a]aresample=48000,volume=-8dB,highpass=f=70,afftdn=nr=10:nf=-40,"
      f"apad=pad_dur={HOLD + 0.3:.3f}[voice];[1:a]volume=-3dB[fx];"
      f"[voice][fx]amix=inputs=2:normalize=0:duration=first,atrim=end={TL['duration']:.3f}[mix]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-i", f"{AUD}/sfx.wav", "-filter_complex", fc,
                "-map", "[mix]", "-ar", "48000", str(pre)], check=True)
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                       "-f", "null", "-"], capture_output=True, text=True).stderr
m = json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", ln, "-ar", "48000", str(mix)], check=True)
pre.unlink()

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf",
                        f"fps={FPS},scale={W}:{H},tpad=stop_mode=clone:stop_duration={HOLD + 0.5:.3f},format=bgr24",
                        "-frames:v", str(NFR), "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-i", str(mix), "-map", "0:v", "-map", "1:a",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
                        "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
size = W * H * 3
for i in range(NFR):
    buf = dec.stdout.read(size)
    if len(buf) < size:
        raise SystemExit(f"decoder ended early at frame {i}")
    frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32)
    # key the flat navy background to white; partial edge pixels are un-mixed so no blue fringe stays
    d = np.linalg.norm(frame - NAVY, axis=2)
    k = np.clip((KEY_HI - d) / (KEY_HI - KEY_LO), 0, 1)[..., None]
    frame = np.clip(frame + k * (255.0 - NAVY), 0, 255)
    # despill: near-background pixels (hair fringe) lose any leftover blue cast
    b, m = frame[..., 0], np.maximum(frame[..., 1], frame[..., 2])
    frame[..., 0] = np.where((d < 95) & (b > m), m, b)
    ov = cv2.imread(f"{OVL}/f_{i:05d}.png", cv2.IMREAD_UNCHANGED)
    a = ov[:, :, 3:4].astype(np.float32) / 255
    enc.stdin.write((frame * (1 - a) + ov[:, :, :3] * a).astype(np.uint8).tobytes())
    if i % 300 == 0:
        print(f"frame {i}/{NFR}", flush=True)
enc.stdin.close()
enc.wait()
dec.kill()
mix.unlink()
print("wrote", OUT)
