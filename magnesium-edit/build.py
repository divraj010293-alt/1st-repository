"""Encode the magnesium explainer: full-frame graphics + audio mix.

usage: python3 build.py <graphicsDir> <audioDir> <out.mp4> [voiceover.wav|mp4]
Without a voiceover this makes the draft (music + SFX only). With one, the music is ducked
under the voice; timings must already come from that recording (phrase_times.json).
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
GFX, AUD, OUT = sys.argv[1:4]
VOICE = sys.argv[4] if len(sys.argv) > 4 else None
TL = json.load(open(HERE / "timeline.json"))
D = TL["duration"]

pre = pathlib.Path(OUT).with_suffix(".pre.wav")
if VOICE:
    fc = ("[0:a]aresample=48000,highpass=f=75,acompressor=threshold=0.25:ratio=2:attack=10:release=200,"
          f"apad=whole_dur={D},asplit=2[voice][key];[1:a]volume=-4dB[mus];"
          "[mus][key]sidechaincompress=threshold=0.02:ratio=7:attack=20:release=450[duck];"
          "[2:a]volume=-1dB[fx];[voice][duck][fx]amix=inputs=3:normalize=0:duration=longest,"
          f"atrim=end={D}[mix]")
    ins = ["-i", VOICE, "-i", f"{AUD}/music.wav", "-i", f"{AUD}/sfx.wav"]
    target = -14
else:
    fc = f"[0:a]volume=-4dB[mus];[1:a]volume=-1dB[fx];[mus][fx]amix=inputs=2:normalize=0,atrim=end={D}[mix]"
    ins = ["-i", f"{AUD}/music.wav", "-i", f"{AUD}/sfx.wav"]
    target = -18  # music-only draft: keep it gentle
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[mix]", "-ar", "48000", str(pre)], check=True)
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af",
                       f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                      capture_output=True, text=True).stderr
m = json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])
ln = (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(TL["fps"]), "-i", f"{GFX}/f_%05d.png", "-i", str(pre),
                "-af", ln, "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                "-profile:v", "high", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-shortest", OUT], check=True)
pre.unlink()
print("wrote", OUT, "(draft, no voice)" if not VOICE else "")
