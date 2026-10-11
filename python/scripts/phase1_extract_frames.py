"""FASE 1: estrae i fotogrammi dei video del venditore (1 ogni 3 s + cambi di scena) e tiene solo quelli
diversi fra loro (differenza media di un'impronta 32x18 in scala di grigi), per leggerli a mano.

usage: python python/scripts/phase1_extract_frames.py <video.mkv> <nome_breve>
out:   output/video/<nome>/all/   tutti i fotogrammi (non versionati)
       output/video/<nome>/frames/ fotogrammi unici, nome = secondo del video (non versionati)
       output/video/<nome>/frames.csv elenco unici con il secondo
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def main(video, name, every=3.0, diff_thr=6.0):
    out = ROOT / "output" / "video" / name
    allf, uniq = out / "all", out / "frames"
    allf.mkdir(parents=True, exist_ok=True)
    uniq.mkdir(parents=True, exist_ok=True)
    # periodic frames
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-vf", f"fps=1/{every}",
                    str(allf / "p_%05d.png")], check=True)
    # scene changes with their timestamps
    r = subprocess.run(["ffmpeg", "-loglevel", "info", "-y", "-i", video, "-vf",
                        "select='gt(scene,0.25)',showinfo", "-vsync", "vfr", str(allf / "s_%05d.png")],
                       capture_output=True, text=True)
    scene_t = [float(x.split("pts_time:")[1].split()[0]) for x in r.stderr.splitlines() if "pts_time:" in x]
    frames = [((i) * every, p) for i, p in enumerate(sorted(allf.glob("p_*.png")))]
    frames += list(zip(scene_t, sorted(allf.glob("s_*.png"))))
    frames.sort(key=lambda x: x[0])
    keep, last = [], None
    for t, p in frames:
        sig = np.asarray(Image.open(p).convert("L").resize((64, 36)), dtype=float)
        if last is None or np.abs(sig - last).mean() > diff_thr:
            dst = uniq / f"t{t:07.1f}.png"
            Image.open(p).save(dst)
            keep.append((t, dst.name))
            last = sig
    (out / "frames.csv").write_text("t_sec,file\n" + "\n".join(f"{t:.1f},{f}" for t, f in keep))
    print(name, "frames", len(frames), "unique", len(keep))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
