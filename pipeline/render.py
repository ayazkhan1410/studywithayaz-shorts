"""Render index.html frames with Playwright, piped as JPEG into one ffmpeg encode.
Usage: python3 render.py stills t1 t2 ...   |   python3 render.py video"""
import json
import os
import subprocess
import sys
from playwright.sync_api import sync_playwright

FPS = 30
tm = json.load(open("timing.json"))
mode = sys.argv[1]

with sync_playwright() as p:
    b = p.chromium.launch(args=["--allow-file-access-from-files"])
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto("file://" + os.path.abspath("index.html"))
    pg.evaluate("tm => initTM(tm)", tm)
    # mouth openness per frame from the voice envelope (lip-sync)
    import numpy as np, soundfile as sf
    vo, sr = sf.read("vo.wav")
    hop = sr // FPS
    rms = np.array([np.sqrt(np.mean(vo[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(len(vo) // hop)])
    m = np.clip((rms - 0.01) / 0.08, 0, 1)
    m = np.convolve(m, [0.25, 0.5, 0.25], "same")
    pg.evaluate("a => setMouth(a)", [round(float(x), 3) for x in m])
    pg.evaluate("document.fonts.ready")
    if mode == "stills":
        os.makedirs("stills", exist_ok=True)
        for t in sys.argv[2:]:
            pg.evaluate(f"render({float(t)})")
            pg.screenshot(path=f"stills/t{t}.jpg", type="jpeg", quality=80)
    else:
        json.dump(pg.evaluate("window.SFX"), open("sfx.json", "w"))
        n = int(tm["total"] * FPS)
        tmp = "video_noaudio.tmp.mp4"
        ff = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
             "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
             "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
        try:
            for i in range(n):
                pg.evaluate(f"render({i / FPS})")
                ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
                if i % 150 == 0:
                    print(f"frame {i}/{n}", flush=True)
        finally:
            ff.stdin.close()
            rc = ff.wait()
        if rc != 0:
            sys.exit(f"ffmpeg failed: {rc}")
        os.replace(tmp, "video_noaudio.mp4")
        print("done", n, "frames")
    b.close()
