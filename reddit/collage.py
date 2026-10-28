"""r/dataisbeautiful collage: reddit/war_memorial_names.png (2400 x 3000), light poppy-and-stone palette.
Every number comes from ../data/results.json and ../data/places.csv. Fonts: FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono).
Run from this folder: FONT_DIR=/path/to/fonts python3 collage.py
"""
import json, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(FD, f))
DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, LAND, EDGE = "#F2EEE6", "#1E1C1A", "#6A645B", "#E3DCCF", "#CFC6B6"
HOT, MOSS = "#B3261E", "#4F7A3A"
RC = ["#E6CDB2", "#DFA17F", "#CF6E4E", "#B73A2A", "#7E1812"]
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = pd.read_csv(os.path.join(ROOT, "data", "places.csv"))
TV = pd.read_csv(os.path.join(ROOT, "data", "thankful_villages.csv"))
COAST = json.load(open(os.path.join(ROOT, "data", "coast_ne10m.json")))
K = np.cos(np.radians(54.5))

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.045, 0.968, "How many names on", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(0.045, 0.920, "your war memorial?", fontproperties=DISP, fontsize=50, color=HOT, va="top")
fig.text(0.045, 0.862, f"The Imperial War Museums register lists {R['register']['rows']:,} UK war memorials. I took one community memorial\n"
         f"per place, so no man is counted twice, and set its First World War names against the people living there today.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.3)

# hero map
ax = fig.add_axes([0.025, 0.215, 0.575, 0.595]); ax.set_facecolor(BG)
for g in COAST:
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0])
        if a[:, 0].min() > 1.75: continue  # skip the Continent
        ax.add_patch(Polygon(np.c_[a[:, 0] * K, a[:, 1]], closed=True, fc=LAND, ec=EDGE, lw=.5))
d = P[P.ww1_dead > 0].sort_values("ww1_dead", ascending=False)
ok = d.ww1_status.isin(["died", "served only"])
rate = np.where(ok, d.ww1_per1000, np.nan)
col = ["#BDB5A7" if np.isnan(r) else RC[sum(r >= t for t in (10, 20, 30, 50))] for r in rate]
ax.scatter(d.lng * K, d.lat, s=np.clip(0.5 + np.sqrt(d.ww1_dead) * 1.0, 0.5, 70), c=col, lw=0, alpha=.88, rasterized=True)
ax.scatter(TV.lng * K, TV.lat, s=46, facecolors="none", edgecolors=MOSS, lw=1.5, zorder=5)
ax.set_xlim(-10.9 * K, 1.9 * K); ax.set_ylim(49.9, 59.0); ax.set_aspect(1); ax.axis("off")
# legend over the Atlantic, top left
ax.text(-10.8 * K, 58.85, "Names per 1,000 people today", family=MONO, fontsize=10.5, color=MUT)
for i, l in enumerate(["under 10", "10 to 19", "20 to 29", "30 to 49", "50 or more"]):
    ax.scatter([-10.65 * K], [58.55 - i * .28], s=70, c=RC[i]); ax.text(-10.4 * K, 58.55 - i * .28, l, va="center", family=MONO, fontsize=10.5, color=FG)
ax.scatter([-10.65 * K], [58.55 - 5 * .28], s=70, c="#BDB5A7"); ax.text(-10.4 * K, 58.55 - 5 * .28, "no population match", va="center", family=MONO, fontsize=10.5, color=FG)
ax.scatter([-10.65 * K], [58.55 - 6 * .28], s=70, facecolors="none", edgecolors=MOSS, lw=1.5); ax.text(-10.4 * K, 58.55 - 6 * .28, "Thankful Village", va="center", family=MONO, fontsize=10.5, color=MOSS)
ax.text(-10.8 * K, 58.55 - 7 * .28 - .2, "dot size =\nnames on memorial", va="center", family=MONO, fontsize=10, color=MUT)

# headline numbers
tx = fig.add_axes([0.60, 0.215, 0.37, 0.61]); tx.axis("off")
items = [
    (f"{R['benchmark']['entries_per_man']:.1f}", f"names on the register's memorials for each of the\n{R['benchmark']['uk_dead']:,} dead and missing from the British Isles.\nThe same man is on his village cross, church\nboard, school roll and works plaque."),
    (f"{R['rate']['median']:.1f}", f"names per 1,000 people living there today, on\nthe median memorial of {R['rate']['n']:,} villages and\nsmall towns (middle half {R['rate']['p25']:.1f} to {R['rate']['p75']:.1f})."),
    (f"{R['rate_by_nation'][0]['median']:.1f} v {R['rate_by_nation'][1]['median']:.1f}", f"Scotland against England, per 1,000 today.\nWales {R['rate_by_nation'][3]['median']:.1f}. Depopulation since 1911 and\nparish-wide memorials push Scotland up too."),
    (f"{R['tail']['zero']}", f"of {R['tail']['n']:,} small places have a community\nrecord with no dead; {R['tail']['zero_tv']} are Thankful Villages.\n{R['tail']['one']} more name a single man."),
]
y = 0.985
for big, small in items:
    tx.text(0, y, big, fontproperties=DISP, fontsize=40, color=HOT, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.085, small, family=SER, fontsize=13, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)
    y -= 0.25

# bottom row: tail and size gradient
S = P[P["pop"].between(R["rate"]["lo"], R["rate"]["hi"]) & P.ww1_exact & P.ww1_status.isin(["died", "served only"])]
k = np.arange(0, 21); n = np.array([(S.ww1_dead == v).sum() for v in k])
a1 = fig.add_axes([0.065, 0.075, 0.45, 0.115]); a1.set_facecolor(BG)
a1.bar(k, n, color=[MOSS if v == 0 else RC[1] for v in k], width=.8)
a1.set_xticks([0, 5, 10, 15, 20]); a1.set_yticks([0, 100, 200, 300])
for s in ("top", "right"): a1.spines[s].set_visible(False)
for s in ("left", "bottom"): a1.spines[s].set_color(MUT)
a1.tick_params(colors=FG, labelsize=10)
for t in a1.get_xticklabels() + a1.get_yticklabels(): t.set_fontfamily(MONO)
a1.annotate(f"{n[0]} places:\nno dead", xy=(0, n[0] + 4), xytext=(-0.4, 215), family=MONO, fontsize=10.5, color=MOSS, arrowprops=dict(arrowstyle="-", color=MOSS, lw=1))
fig.text(0.065, 0.198, "SMALL PLACES BY NAMES ON MEMORIAL", family=MONO, fontsize=11, color=MUT)
a2 = fig.add_axes([0.62, 0.075, 0.33, 0.115]); a2.set_facecolor(BG)
rb = R["rate_by_pop"]; yy = np.arange(len(rb))[::-1]
a2.barh(yy, [r["median"] for r in rb], color=RC[3], height=.66)
a2.set_yticks(yy); a2.set_yticklabels([r["band"] for r in rb], family=MONO, fontsize=10)
for yi, r in zip(yy, rb): a2.text(r["median"] + .8, yi, f"{r['median']:.1f}", va="center", family=MONO, fontsize=10.5, color=FG)
a2.set_xticks([]); a2.set_xlim(0, max(r["median"] for r in rb) * 1.2)
for s in ("top", "right", "bottom"): a2.spines[s].set_visible(False)
a2.spines["left"].set_color(MUT); a2.tick_params(axis="y", length=0, colors=FG)
fig.text(0.62, 0.198, "PER 1,000, BY PLACE SIZE TODAY", family=MONO, fontsize=11, color=MUT)

fig.text(0.045, 0.012,
         "Data: Imperial War Museums, War Memorials Register, iwm.org.uk/memorials (non-commercial reuse with credit), retrieved 28 Oct 2026;\n"
         "populations: Wikidata (CC0), a modern proxy for 1911; national figure: Wikipedia, World War I casualties; Thankful Villages: Wikipedia.\n"
         "One community memorial per place, never summed. Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=9.5, color=MUT, linespacing=1.45)
fig.savefig(os.path.join(HERE, "war_memorial_names.png"), facecolor=BG)
print("collage written")
