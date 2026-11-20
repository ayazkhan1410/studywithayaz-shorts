"""Render the assistant alone (transparent PNG), arm raised, from a pipeline index.html."""
import json, sys, os
from playwright.sync_api import sync_playwright
d = sys.argv[1]; out = sys.argv[2]; t = float(sys.argv[3])
with sync_playwright() as p:
    b = p.chromium.launch(args=["--allow-file-access-from-files"])
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto("file://" + os.path.abspath(d + "/index.html"))
    pg.evaluate("tm => initTM(tm)", json.load(open(d + "/timing.json")))
    pg.evaluate("document.fonts.ready")
    pg.evaluate(f"(async()=>{{await render({t})}})()")
    pg.evaluate("""()=>{for(const id of ['bg','stage','cap','flash']){const e=document.getElementById(id);if(e)e.style.display='none'}
      document.documentElement.style.background='transparent';document.body.style.background='transparent';
      document.getElementById('mOpen').style.opacity=0;document.getElementById('mClosed').style.opacity=1;
      document.getElementById('asst').style.transform='none';}""")
    pg.screenshot(path=out, omit_background=True, clip={"x": 230, "y": 1150, "width": 680, "height": 770})
    b.close()
