"""Step 4. Build index.html from code/page_template.html.

Every number in the text is a {{path|format}} token filled from data/results.json, so the page cannot drift
from the analysis. The place data for the map (work/site_data.json, from step 3) and a slim copy of the results
are embedded; the full memorial list for the search (data/memorials_search.json) is fetched when first needed.
Run: python3 code/04_build_site.py
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
SITE = open(os.path.join(ROOT, "work", "site_data.json"), encoding="utf-8").read()
tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "x1": return f"{v:.1f}"
    if f == "x2": return f"{v:.2f}"
    if f == "m1": return f"{v / 1e6:.1f}"
    raise ValueError(f)


def sub(m):
    return fmt(get(m.group(1)), m.group(3))


# facts the template states in words: check them against the data
assert R["thankful_list"][16]["village"] == "Nether Kellet"
assert sorted(r["village"] for r in R["thankful_list"] if r["dead_any"] and r["dead_indiv"] == r["dead_mem"]) == ["Chantry", "East Norton", "Tellisford"]
assert [r["nation"] for r in R["rate_by_nation"]][:2] == ["Scotland", "England"] and R["rate_by_nation"][3]["nation"] == "Wales"
assert [r["county"] for r in R["rate_by_county"][:3]] == ["Highland", "Dumfries and Galloway", "Scottish Borders"]
assert R["size_dist"][7]["band"] == "1,000 or more"

if __name__ == "__main__":
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", sub, tpl)
    slim = {k: R[k] for k in ["type_groups", "classes", "size_dist", "rate_by_pop", "rate_hist", "rate_by_nation", "rate_by_county",
                              "biggest", "highest", "thankful_list", "candidates_list", "benchmark"]}
    html = html.replace("/*SITE*/", SITE).replace("/*RESULTS*/", json.dumps(slim, ensure_ascii=False, separators=(",", ":")))
    assert "{{" not in html
    assert "\u2014" not in SITE and "\u2013" not in SITE and "--" not in SITE
    for bad in ("\u2014", "\u2013", "--"):
        vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
        assert bad not in vis, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()), "bytes")
