"""Step 5. Render header.png (1200x630 social card) with Playwright Chromium.

Fonts: FONT_DIR holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf, IBMPlexMono-Medium.ttf
(from github.com/google/fonts); otherwise system serif is used. Coastline: data/coast_ne10m.json (Natural Earth 1:10m land, public domain).
Run: FONT_DIR=/path/to/fonts python3 code/05_header.py
"""
import json, math, os
import pandas as pd
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = pd.read_csv(os.path.join(ROOT, "data", "places.csv"))
FD = os.environ.get("FONT_DIR", "")
K = math.cos(math.radians(54.5))
X0, X1, Y0, Y1 = -8.3 * K, 2.0 * K, -59.0, -49.9
Hh = 610; Ww = Hh * (X1 - X0) / (Y1 - Y0)
pr = lambda lat, lon: ((lon * K - X0) / (Y1 - Y0) * Hh, (-lat - Y0) / (Y1 - Y0) * Hh)
land = ""
for g in json.load(open(os.path.join(ROOT, "data", "coast_ne10m.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        land += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (pr(q[1], q[0]) for q in poly[0])) + "Z"
COL = ["#E4C9AE", "#DE9F7E", "#CF6E4E", "#B73A2A", "#8A1C15"]
dots = ""
d = P[P.ww1_dead > 0].sort_values("ww1_dead", ascending=False)
for r in d.itertuples():
    x, y = pr(r.lat, r.lng); rr = min(9, 0.7 + math.sqrt(r.ww1_dead) * 0.13)
    rate = r.ww1_per1000
    c = "#B9B1A3" if pd.isna(rate) else COL[sum(rate >= t for t in (10, 20, 30, 50))]
    dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr:.1f}" fill="{c}" fill-opacity=".85"/>'
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(circle at 78% 50%,#F7F4EE 0%,#F1EEE7 55%,#E4DED2 100%);color:#1E1C1A;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:60px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#67625A;display:flex;gap:12px;align-items:center}}
.k b{{background:#B3261E;color:#fff;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:64px;top:96px;margin:0;font:900 82px/.93 Fraunces,Georgia,serif;letter-spacing:-.02em;width:720px}}
h1 em{{font-style:normal;color:#B3261E}}
p{{position:absolute;left:70px;top:380px;width:640px;margin:0;font-size:25px;line-height:1.36}}
p b{{color:#B3261E}}
.f{{position:absolute;left:70px;bottom:38px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#67625A}}
svg{{position:absolute;right:26px;top:10px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Remembrance · 1914 to 1918</span></div>
<h1>How many names on your <em>war memorial?</em></h1>
<p>{R['register']['rows']:,} memorials, {R['places']['with_ww1']:,} places. A typical village memorial carries <b>{R['rate']['median']:.1f}</b> names for every 1,000 people who live there today. Only <b>{R["tail"]["zero"]}</b> of {R["tail"]["n"]:,} counted villages and small towns name no dead.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Ww:.0f}" height="{Hh}" viewBox="0 0 {Ww:.0f} {Hh}"><path d="{land}" fill="#E2DCD0" stroke="#C9C1B2" stroke-width="1"/>{dots}</svg>
</body></html>"""
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
