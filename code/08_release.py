"""Step 8. Blog post (release/blog/post.html from code/blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader (numbers inside them are filled).
Run: python3 code/08_release.py
"""
import importlib.util, json, os, re, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = open(os.path.join(HERE, "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)([^}|]+)(\|(\w+))?\}\}", b.sub, t)
assert "{{" not in t.replace("{{IMG|", "")
vis = re.sub(r"<!--.*?-->", "", t, flags=re.S)
for bad in ("\u2014", "\u2013", "--"): assert bad not in vis, bad
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m
meta = dict(
    title="How many names on your war memorial?",
    slug="war-memorials",
    excerpt=(f"I counted the First World War names on {R['places']['with_ww1']:,} community memorials in the Imperial War Museums register. "
             f"A typical village memorial carries {R['rate']['median']:.1f} names for every 1,000 people living there today, and only "
             f"{R['tail']['zero']} of {R['tail']['n']:,} small places record no dead."),
    seo_description=f"First World War names on {R['places']['with_ww1']:,} community war memorials, per 1,000 residents, and where the Thankful Villages sit.",
    tags=["war memorials", "Remembrance", "First World War", "Thankful Villages", "Imperial War Museums", "maps", "data"],
    header_alt=(f"Title card reading 'How many names on your war memorial?' in dark ink and poppy red on a pale stone background, beside a map of "
                f"Britain dotted with memorials coloured from stone to deep red. Text: {R['register']['rows']:,} memorials, {R['places']['with_ww1']:,} places; "
                f"a typical village memorial carries {R['rate']['median']:.1f} names for every 1,000 people who live there today."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

NAME = "Hotham_War_Memorial_Names"
pt = open(os.path.join(ROOT, "release", "paper", NAME + ".tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("\\&", "&")
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title="How Many Names on Your War Memorial? Counting the First World War Dead Place by Place in the War Memorials Register",
    description_html=f"<p>{ab}</p><p>Interactive version: https://tristan-hotham.github.io/war-memorials/. Data and code: https://github.com/Tristan-Hotham/war-memorials. Blog post: to follow.</p>",
    keywords=["war memorials", "First World War", "Remembrance", "Thankful Villages", "War Memorials Register", "Imperial War Museums",
              "commemoration", "United Kingdom", "Wikidata", "open data"],
    licence="cc-by-nc-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/war-memorials", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/war-memorials/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://www.iwm.org.uk/memorials", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.wikidata.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://en.wikipedia.org/wiki/World_War_I_casualties", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://en.wikipedia.org/wiki/Thankful_Villages", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://doi.org/10.5281/zenodo.23676168", relation="isderivedfrom", resource_type="dataset"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", NAME + ".pdf"), Z)
for f in ["places.csv", "memorials.csv", "thankful_villages.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "war-memorials_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"war-memorials/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"war-memorials/{f}")
words = len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t)).split())
print("release files written; post words:", words)
