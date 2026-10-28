"""Step 7. Build the paper PDF: fill code/paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_War_Memorial_Names.tex and compile it with xelatex (figures from step 6).
Run: python3 code/07_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_War_Memorial_Names"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f in ("f1", "x1"): return f"{v:.1f}"
    if f in ("f2", "x2"): return f"{v:.2f}"
    if f == "m1": return f"{v / 1e6:.1f}"
    return tex(str(v))


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


rows = "".join(f"{r['band']} & {r['n']:,} & {r['median_dead']:.0f} & {r['median']:.1f}\\\\\n" for r in R["rate_by_pop"])
rows2 = "".join(f"{r['nation']} & {r['n']:,} & {r['median_dead']:.0f} & {r['median']:.1f}\\\\\n" for r in R["rate_by_nation"])
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Names of the First World War dead per 1,000 residents today, villages and small towns of "
      f"{R['rate']['lo']:,} to {R['rate']['hi']:,} residents with an exact count. Names: median names on the chosen memorial.}}\\label{{tab:rates}}"
      "\\begin{tabular}{lrrr}\\toprule Group & Places & Names & Per 1,000\\\\\\midrule\n\\multicolumn{4}{l}{\\emph{Residents today}}\\\\\n" + rows +
      "\\midrule\\multicolumn{4}{l}{\\emph{Nation}}\\\\\n" + rows2 +
      f"\\midrule All & {R['rate']['n']:,} & & {R['rate']['median']:.1f}\\\\\n\\bottomrule\\end{{tabular}}\\end{{table}}")
rows = "".join(f"{i + 1} & {tex(r['place'])} & {tex(r['county'] or r['nation'])} & {r['dead']:,} & {r['pop']:,} & {r['rate']:.1f}\\\\\n" for i, r in enumerate(R["highest"]))
TH = ("\\begin{table}[tbp]\\centering\\small\\caption{Highest names per 1,000 residents today among places of "
      f"{R['highest_rule']['min_pop']} or more residents with a single-place memorial. Leads, not findings.}}\\label{{tab:highest}}"
      "\\begin{tabular}{rllrrr}\\toprule & Place & County & Names & Residents & Per 1,000\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex")).read()
t = re.sub(r"\{\{(?!TABLE_)(.+?)\}\}", sub, t).replace("{{TABLE_RATES}}", TR).replace("{{TABLE_HIGHEST}}", TH)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
print("paper written", r.returncode)
