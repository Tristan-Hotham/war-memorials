"""Step 6. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png), from data/.
Fonts: FONT_DIR as in step 5 (Fraunces, Source Serif 4, IBM Plex Mono); falls back to matplotlib defaults.
Run: FONT_DIR=/path/to/fonts python3 code/06_figures.py
"""
import json, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = pd.read_csv(os.path.join(ROOT, "data", "places.csv"))
TV = pd.read_csv(os.path.join(ROOT, "data", "thankful_villages.csv"))
COAST = json.load(open(os.path.join(ROOT, "data", "coast_ne10m.json")))
FD = os.environ.get("FONT_DIR", "")
SER, MONO = "serif", "monospace"
if FD:
    for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf"]:
        fm.fontManager.addfont(os.path.join(FD, f))
    SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, RULE, LAND = "#F1EEE7", "#1E1C1A", "#67625A", "#D6D0C3", "#E2DCD0"
HOT, MOSS, SLATE, GREY = "#B3261E", "#4F7A3A", "#3D5A80", "#B9B1A3"
RC = ["#E4C9AE", "#DE9F7E", "#CF6E4E", "#B73A2A", "#8A1C15"]
K = np.cos(np.radians(54.5))
OUTP = os.path.join(ROOT, "release", "paper"); OUTB = os.path.join(ROOT, "release", "blog")
os.makedirs(OUTP, exist_ok=True); os.makedirs(OUTB, exist_ok=True)


def style(ax, blog):
    ax.set_facecolor(BG if blog else "white")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(MUT)
    ax.tick_params(colors=FG, labelsize=12 if blog else 9)
    for t in ax.get_xticklabels() + ax.get_yticklabels(): t.set_fontfamily(MONO)


def fig(w, h, blog):
    f = plt.figure(figsize=(w, h), dpi=200, facecolor=BG if blog else "white")
    return f


def save(f, name, blog):
    f.savefig(os.path.join(OUTB if blog else OUTP, ("b_" if blog else "f_") + name + ".png"), facecolor=f.get_facecolor(), bbox_inches="tight", pad_inches=0.15)
    plt.close(f)


def rate_col(r):
    if pd.isna(r): return GREY
    return RC[sum(r >= t for t in (10, 20, 30, 50))]


def fmap(blog):
    f = fig(7.6 if blog else 6.5, 8.6 if blog else 7.4, blog); ax = f.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG if blog else "white")
    for g in COAST:
        for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
            a = np.array(poly[0]); ax.add_patch(Polygon(np.c_[a[:, 0] * K, a[:, 1]], closed=True, fc=LAND, ec="#C9C1B2", lw=.4))
    d = P[P.ww1_dead > 0].sort_values("ww1_dead", ascending=False)
    ok = (d.ww1_status == "died") | (d.ww1_status == "served only")
    rate = np.where(ok, d.ww1_per1000, np.nan)
    ax.scatter(d.lng * K, d.lat, s=np.clip(0.4 + np.sqrt(d.ww1_dead) * 0.9, 0.4, 60) * (1.2 if blog else 0.8),
               c=[rate_col(r) for r in rate], lw=0, alpha=.85, rasterized=True)
    so = P[P.ww1_status == "served only"]
    ax.scatter(so.lng * K, so.lat, s=7, c=MOSS, lw=0, rasterized=True)
    t = TV
    ax.scatter(t.lng * K, t.lat, s=40 if blog else 26, facecolors="none", edgecolors=MOSS, lw=1.3)
    ax.set_xlim(-8.3 * K, 4.6 * K); ax.set_ylim(49.85, 59.0); ax.set_aspect(1); ax.axis("off")
    fs = 11 if blog else 8.5
    LX, LT, LH = 1.0 * K, 1.25 * K, 0.85 * K
    labs = ["Under 10", "10 to 19", "20 to 29", "30 to 49", "50 or more"]
    for i, (c, l) in enumerate(zip(RC, labs)):
        ax.scatter([LX], [58.7 - i * .3], s=55, c=c); ax.text(LT, 58.7 - i * .3, l, va="center", family=MONO, fontsize=fs, color=FG)
    ax.text(LH, 59.0, "Names per 1,000 residents today", va="center", family=MONO, fontsize=fs, color=MUT)
    y = 58.7 - 5 * .3
    ax.scatter([LX], [y], s=55, c=GREY); ax.text(LT, y, "No population match", va="center", family=MONO, fontsize=fs, color=FG)
    ax.scatter([LX], [y - .3], s=55, c=MOSS); ax.text(LT, y - .3, "Roll of service, no dead", va="center", family=MONO, fontsize=fs, color=FG)
    ax.scatter([LX], [y - .6], s=55, facecolors="none", edgecolors=MOSS, lw=1.3); ax.text(LT, y - .6, "Thankful Village", va="center", family=MONO, fontsize=fs, color=FG)
    save(f, "map", blog)


def hbar(ax, labels, vals, colors, blog, fmtv=lambda v: f"{v:,.0f}", ref=None):
    y = np.arange(len(vals))[::-1]
    ax.barh(y, vals, color=colors, height=.66)
    ax.set_yticks(y); ax.set_yticklabels(labels, family=MONO, fontsize=12 if blog else 9)
    for yi, v in zip(y, vals): ax.text(v + max(vals) * .01, yi, fmtv(v), va="center", family=MONO, fontsize=12 if blog else 9, color=FG,
                                       bbox=dict(fc=BG if blog else "white", ec="none", pad=1), zorder=5)
    ax.set_xlim(0, max(vals) * 1.17); ax.set_xticks([])
    ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0)
    if ref is not None: ax.axvline(ref, color=FG, ls=(0, (4, 4)), lw=1, zorder=1)


def fclasses(blog):
    names = {"community": "Community", "military": "Military units", "church": "Church and chapel", "regional": "County and national",
             "workplace": "Workplaces, clubs", "school": "Schools and colleges", "individual": "To one person"}
    c = sorted(R["classes"].items(), key=lambda kv: -kv[1]["ww1_dead"])
    f = fig(7.6 if blog else 6.5, 4.0 if blog else 3.2, blog); ax = f.add_subplot(111); style(ax, blog)
    hbar(ax, [names[k] for k, _ in c], [v["ww1_dead"] for _, v in c], [HOT if k == "community" else "#E0AE93" for k, _ in c], blog)
    save(f, "classes", blog)


def fsizes(blog):
    f = fig(7.6 if blog else 6.5, 4.0 if blog else 3.2, blog); ax = f.add_subplot(111); style(ax, blog)
    hbar(ax, [r["band"] + " names" for r in R["size_dist"]], [r["n"] for r in R["size_dist"]], "#CF6E4E", blog)
    save(f, "sizes", blog)


def fhist(blog):
    f = fig(7.6 if blog else 6.5, 4.2 if blog else 3.4, blog); ax = f.add_subplot(111); style(ax, blog)
    H = R["rate_hist"]; x = [h["lo"] for h in H]; n = [h["n"] for h in H]
    cols = [RC[sum(v >= t for t in (10, 20, 30, 50))] for v in x]
    ax.bar(x, n, width=4.6, align="edge", color=cols)
    b = R["benchmark"]["per1000"]; ax.axvline(b, color=FG, ls=(0, (4, 4)), lw=1.1)
    ax.text(b + 1, max(n) * 1.02, f"national {b:.1f}", family=MONO, fontsize=12 if blog else 9, color=FG)
    md = R["rate"]["median"]; ax.axvline(md, color=HOT, lw=1.6)
    ax.text(md + 1.5, max(n) * .72, f"median {md:.1f}", family=MONO, fontsize=12 if blog else 9, color=HOT)
    ax.set_xticks(range(0, 101, 10)); ax.set_xticklabels([str(v) for v in range(0, 100, 10)] + ["100+"])
    ax.set_xlabel("Names per 1,000 residents today", family=MONO, fontsize=12 if blog else 9, color=MUT)
    ax.set_ylabel("Places", family=MONO, fontsize=12 if blog else 9, color=MUT)
    ax.grid(axis="y", color=RULE, lw=.6); ax.set_axisbelow(True)
    style(ax, blog); save(f, "hist", blog)


def fbypop(blog):
    f = fig(7.6 if blog else 6.5, 5.6 if blog else 4.6, blog)
    a1 = f.add_subplot(211); a2 = f.add_subplot(212); style(a1, blog); style(a2, blog)
    b = R["benchmark"]["per1000"]
    hbar(a1, [r["band"] + " people" for r in R["rate_by_pop"]], [r["median"] for r in R["rate_by_pop"]], "#B73A2A", blog, lambda v: f"{v:.1f}", b)
    hbar(a2, [r["nation"] for r in R["rate_by_nation"]], [r["median"] for r in R["rate_by_nation"]],
         [SLATE if r["nation"] == "Scotland" else MOSS if r["nation"] == "Wales" else "#B73A2A" for r in R["rate_by_nation"]], blog, lambda v: f"{v:.1f}", b)
    a1.set_title(f"By population today (dashed line: national {b:.1f})", loc="left", family=MONO, fontsize=12 if blog else 9, color=MUT)
    a2.set_title("By nation", loc="left", family=MONO, fontsize=12 if blog else 9, color=MUT)
    f.tight_layout(h_pad=2); save(f, "bypop", blog)


def ftail(blog):
    S = P[P["pop"].between(R["rate"]["lo"], R["rate"]["hi"]) & P.ww1_exact & P.ww1_status.isin(["died", "served only"])]
    k = np.arange(0, 21); n = [(S.ww1_dead == v).sum() for v in k]; tv = [((S.ww1_dead == v) & S.thankful).sum() for v in k]
    f = fig(7.6 if blog else 6.5, 4.0 if blog else 3.2, blog); ax = f.add_subplot(111); style(ax, blog)
    ax.bar(k, n, color=["#4F7A3A" if v == 0 else "#DE9F7E" for v in k], width=.8)
    ax.bar(k, tv, color=MOSS, width=.8, hatch="////", edgecolor="white", lw=0)
    for v, c in zip(k, n): ax.text(v, c + max(n) * .015, f"{c}", ha="center", family=MONO, fontsize=10 if blog else 7.5, color=FG)
    ax.set_xticks(k); ax.set_xlabel("First World War names of the dead on the place's community memorial", family=MONO, fontsize=12 if blog else 9, color=MUT)
    ax.set_ylabel("Places", family=MONO, fontsize=12 if blog else 9, color=MUT)
    ax.text(0.6, max(n) * .55, f"no dead: {n[0]} places,\n{tv[0]} of them Thankful Villages (hatched)", family=MONO, fontsize=11 if blog else 8.5, color=MOSS)
    ax.grid(axis="y", color=RULE, lw=.6); ax.set_axisbelow(True)
    style(ax, blog); save(f, "tail", blog)


for blog in (False, True):
    for fn in (fmap, fclasses, fsizes, fhist, fbypop, ftail):
        fn(blog)
print("figures written")
