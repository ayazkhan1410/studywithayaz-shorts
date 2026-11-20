"""Make a 1080x1920 Shorts thumbnail from a key frame of the rendered video.
Usage: python3 thumbnail.py frame.jpg out.jpg "LINE ONE|LINE *TWO*|line three" [sub text]
Words wrapped in *stars* get the accent box. Crops the frame's scene area (top) and the
assistant presenter (bottom) so the thumbnail matches the video."""
import base64, os, sys, html
from PIL import Image
from playwright.sync_api import sync_playwright

frame, out, headline = sys.argv[1], sys.argv[2], sys.argv[3]
sub = sys.argv[4] if len(sys.argv) > 4 else ""
im = Image.open(frame).convert("RGB")
scene = im.crop((40, 30, 1040, 980)); scene.save("/tmp/_scene.jpg", quality=92)
ASST = os.environ.get("ASST_PNG", os.path.join(os.path.dirname(os.path.abspath(__file__)), "assistant_point.png"))
b64 = lambda p: "data:image/jpeg;base64," + base64.b64encode(open(p, "rb").read()).decode()
FONT = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf"
lines = []
for ln in headline.split("|"):
    parts = []
    for w in ln.split(" "):
        if w.startswith("*") and w.endswith("*"):
            parts.append(f'<span class="acc">{html.escape(w.strip("*"))}</span>')
        else:
            parts.append(html.escape(w))
    lines.append(" ".join(parts))
page = f"""<!DOCTYPE html><html><head><style>
@font-face{{font-family:M;src:url("file://{FONT}");font-weight:100 900}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;font-family:M;background:linear-gradient(160deg,#EEF0FF,#FDF0FF 45%,#FFF3E8);position:relative}}
.blob{{position:absolute;border-radius:50%;filter:blur(70px);opacity:.6}}
h1{{position:absolute;left:50px;right:50px;top:90px;text-align:center;font-weight:900;font-size:118px;line-height:1.08;color:#1B1640;letter-spacing:-2px}}
.acc{{display:inline-block;background:#FF3B5C;color:#fff;padding:0 22px;border-radius:24px;transform:rotate(-2deg)}}
.sub{{position:absolute;left:0;right:0;top:{{SUBTOP}}px;text-align:center}}
.sub span{{display:inline-block;background:#1B1640;color:#FFC93C;font-weight:900;font-size:56px;padding:12px 40px;border-radius:999px}}
.card{{position:absolute;left:70px;top:{{CARDTOP}}px;width:940px;border-radius:44px;overflow:hidden;box-shadow:0 40px 90px rgba(60,40,150,.28);border:8px solid #fff;transform:rotate(-1.5deg)}}
.card img{{width:100%;display:block}}
.asst{{position:absolute;right:-40px;bottom:-10px;width:600px;filter:drop-shadow(0 20px 30px rgba(60,40,150,.25))}}
.brand{{position:absolute;left:60px;bottom:90px;background:#fff;border-radius:999px;padding:16px 34px;font-weight:800;font-size:40px;color:#1B1640;box-shadow:0 14px 30px rgba(60,40,150,.18)}}
</style></head><body>
<div class="blob" style="width:600px;height:600px;background:#B9A8FF;left:-150px;top:500px"></div>
<div class="blob" style="width:520px;height:520px;background:#FFC1D9;right:-160px;top:1100px"></div>
<h1 id="h">{'<br>'.join(lines)}</h1>
{f'<div class="sub" id="s"><span>{html.escape(sub)}</span></div>' if sub else ''}
<div class="card" id="c"><img src="{b64('/tmp/_scene.jpg')}"></div>
<img class="asst" src="data:image/png;base64,{base64.b64encode(open(ASST,'rb').read()).decode()}">
<div class="brand">▶ Study with Ayaz</div>
</body></html>"""
with sync_playwright() as p:
    b = p.chromium.launch(args=["--allow-file-access-from-files"])
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    open("/tmp/_thumb.html", "w").write(page.replace("{SUBTOP}", "0").replace("{CARDTOP}", "0"))
    pg.goto("file:///tmp/_thumb.html"); pg.evaluate("document.fonts.ready")
    hb = pg.evaluate("document.getElementById('h').getBoundingClientRect().bottom")
    subtop = hb + 24; cardtop = subtop + (110 if sub else 10)
    open("/tmp/_thumb.html", "w").write(page.replace("{SUBTOP}", str(int(subtop))).replace("{CARDTOP}", str(int(cardtop))))
    pg.goto("file:///tmp/_thumb.html"); pg.evaluate("document.fonts.ready")
    pg.screenshot(path=out, type="jpeg", quality=90)
    b.close()
print(out, os.path.getsize(out) // 1024, "KB")
