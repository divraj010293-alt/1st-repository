"""Encode the magnesium explainer: full-frame graphics + voiceover + sound effects (no music).

usage: python3 build.py <graphicsDir> <audioDir> <voiceover.wav> <out.mp4>
Timings must come from that voiceover (phrase_times.json, written by tts.py).
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
GFX, AUD, VOICE, OUT = sys.argv[1:5]
TL = json.load(open(HERE / "timeline.json"))
D = TL["duration"]

pre = pathlib.Path(OUT).with_suffix(".pre.wav")
fc = ("[0:a]aresample=48000,highpass=f=70,acompressor=threshold=0.2:ratio=2.5:attack=8:release=180,"
      f"apad=whole_dur={D},pan=stereo|c0=c0|c1=c0[voice];"
      "[1:a]volume=-3dB[fx];[voice][fx]amix=inputs=2:normalize=0:duration=longest,"
      f"atrim=end={D}[mix]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VOICE, "-i", f"{AUD}/sfx.wav",
                "-filter_complex", fc, "-map", "[mix]", "-ar", "48000", str(pre)], check=True)
# two-pass loudness normalisation to -14 LUFS
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af",
                       "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                      capture_output=True, text=True).stderr
m = json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(TL["fps"]), "-i", f"{GFX}/f_%05d.png", "-i", str(pre),
                "-af", ln, "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                "-profile:v", "high", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-shortest", OUT], check=True)
pre.unlink()
print("wrote", OUT)
