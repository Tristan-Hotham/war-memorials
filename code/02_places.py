"""Step 2. Group memorials into places, pick one community memorial per place, and attach a population proxy.

Input : work/memorials_all.pkl (step 1)
        /home/claude/hist/_data8/uk_bundle_wikidata_osm.json, key wd_settlements_pop_tsv (Wikidata, CC0)
        work/thankful-villages/data/raw/thankful_villages.json (clone of github.com/Tristan-Hotham/thankful-villages)
Output: data/places.csv, data/thankful_villages.csv, work/places.pkl

Place: memorials that share the same town name in the register (normalised) and lie within 6 km of
each other (single-linkage). The place sits at the median of its memorials' coordinates.

Community memorial (the double-counting rule): one place's dead appear on a village cross, a church board,
a school roll and a workplace plaque. So I never add memorials together. For each place I take the one
memorial of class "community" that carries most First World War names of the dead; if the place has none
with names of the dead, the church memorial that carries most. A roll of those who served (no dead) is
chosen only when no community or church memorial at the place records any dead. Memorials to one person, military units, schools, workplaces, clubs
and county or national memorials are never chosen. The same is done for the Second World War.

Population proxy: the Wikidata settlement (civil parish or Welsh community first, then village, town or
other settlement) with the same normalised name within 5 km of the place. Wikidata stores a modern
population, mostly from the 2011 or 2021 census; it is not the 1911 population.
Run: python3 code/02_places.py
"""
import json, os, re
from difflib import SequenceMatcher
import numpy as np, pandas as pd
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
WD = "/home/claude/hist/_data8/uk_bundle_wikidata_osm.json"
TVJ = os.path.join(ROOT, "work", "thankful-villages", "data", "raw", "thankful_villages.json")
M = pd.read_pickle(os.path.join(ROOT, "work", "memorials_all.pkl"))
K = np.cos(np.radians(54.5))


def norm(s):
    s = (s or "").strip().lower().replace("&", " and ")
    s = re.sub(r"\bsaint\b", "st", s); s = re.sub(r"\bst\.", "st", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ---- 1. places ----
G = M[M.lat.notna() & (M.town_key != "") & ~M.nation.isin(["Elsewhere", "No location"])].copy()
keys = G.town_key.values; xy_all = np.c_[G.lng.values * K * 111.2, G.lat.values * 111.2]
pid = np.full(len(G), -1); nxt = 0
for key, idx in pd.Series(np.arange(len(G))).groupby(keys).groups.items():
    idx = np.asarray(idx); n = len(idx); parent = list(range(n))

    def f(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    if n > 1:
        for a, b in cKDTree(xy_all[idx]).query_pairs(6.0):
            ra, rb = f(a), f(b)
            if ra != rb: parent[ra] = rb
    roots = [f(a) for a in range(n)]
    ids = {r: i for i, r in enumerate(dict.fromkeys(roots))}
    pid[idx] = [nxt + ids[r] for r in roots]
    nxt += len(ids)
G["pid"] = pid

# one row per place
agg = G.groupby("pid").agg(lat=("lat", "median"), lng=("lng", "median"), n_mem=("id", "size"), n_ww1=("ww1", "sum"),
                           n_ww2=("ww2", "sum"), key=("town_key", "first"),
                           n_community=("cls", lambda c: int((c == "community").sum())), n_church=("cls", lambda c: int((c == "church").sum())),
                           ww1_dead_all=("ww1_dead", lambda c: float(c.fillna(0).sum())), ww2_dead_all=("ww2_dead", lambda c: float(c.fillna(0).sum())))
G["town_s"] = G.town.str.strip()
mode = lambda col: G.groupby("pid")[col].agg(lambda c: c.dropna().value_counts().index[0] if c.notna().any() else "")
agg["place"] = mode("town_s"); agg["county"] = mode("county"); agg["district"] = mode("district"); agg["nation"] = mode("nation")
agg["lat"] = agg.lat.round(5); agg["lng"] = agg.lng.round(5)
P = agg.reset_index()
for war in ("ww1", "ww2"):
    d = f"{war}_dead"
    c = G[G.cls.isin(["community", "church"]) & G[war] & G[d].notna()].copy()
    c["_p"] = (c[d] > 0).astype(int)
    c["_c"] = (c.cls == "community").astype(int); c["_e"] = c[f"{war}_exact"].astype(int); c["_l"] = (~c.lost).astype(int)
    # a memorial with names of the dead first; then community before church; then most names; exact; not lost
    c = c.sort_values(["pid", "_p", "_c", d, "_e", "_l"], ascending=[True, False, False, False, False, False]).drop_duplicates("pid")
    c = c.set_index("pid")
    P[f"{war}_mid"] = P.pid.map(c.id); P[f"{war}_title"] = P.pid.map(c.title).fillna("")
    P[f"{war}_src"] = P.pid.map(c.cls).fillna(""); P[d] = P.pid.map(c[d]); P[f"{war}_served"] = P.pid.map(c[f"{war}_served"])
    P[f"{war}_exact"] = P.pid.map(c[f"{war}_exact"]).fillna(False).astype(bool)
    P[f"{war}_status"] = P.pid.map(c[f"{war}_status"]).fillna(""); P[f"{war}_types"] = P.pid.map(c.types).fillna("")
    P[f"{war}_lost"] = P.pid.map(c.lost).fillna(False).astype(bool)
P = P[["pid", "place", "key", "lat", "lng", "county", "district", "nation", "n_mem", "n_ww1", "n_ww2", "n_community", "n_church",
       "ww1_dead_all", "ww2_dead_all"] + [c for c in P.columns if c.startswith(("ww1_", "ww2_")) and not c.endswith("_all")]]

# ---- 2. population proxy from Wikidata ----
wd = json.load(open(WD))["wd_settlements_pop_tsv"].splitlines()
W = []
for line in wd[1:]:
    c = line.split("\t")
    if len(c) < 5: continue
    m = re.match(r"POINT\(([-\d.]+) ([-\d.]+)\)", c[3])
    if not m: continue
    W.append(dict(qid=c[0].strip("<>").rsplit("/", 1)[-1], label=c[1].split('"')[1] if '"' in c[1] else c[1],
                  cls=c[2].split('"')[1] if '"' in c[2] else c[2], lng=float(m.group(1)), lat=float(m.group(2)),
                  pop=float(c[4]) if c[4] else np.nan))
W = pd.DataFrame(W)
KEEP = {"civil parish": 0, "community": 0, "village": 1, "town": 1, "market town": 1, "hamlet": 1, "small burgh": 1,
        "human settlement": 1, "city": 1, "cathedral city": 1, "suburb": 2, "island": 2, "abandoned village": 2,
        "burgh": 1, "large burgh": 1, "port settlement": 1, "seaside resort": 1, "spa town": 1, "new town": 1, "area of London": 2,
        "settlement": 1, "townland": 2, "post town": 1, "ghost town": 2}
W = W[W.cls.isin(KEEP) & W["pop"].notna() & (W["pop"] > 0)].copy()
W["prio"] = W.cls.map(KEEP); W["key"] = W.label.map(norm)
W = W.sort_values(["qid", "prio"]).drop_duplicates("qid")
wt = W.groupby("key")
P["pop"] = np.nan; P["pop_qid"] = ""; P["pop_label"] = ""; P["pop_class"] = ""; P["pop_km"] = np.nan
for i, r in P.iterrows():
    if r.key not in wt.groups: continue
    c = W.loc[wt.groups[r.key]]
    km = np.hypot((c.lng - r.lng) * K, c.lat - r.lat) * 111.2
    c = c.assign(km=km)[km <= 5.0]
    if not len(c): continue
    b = c.sort_values(["prio", "km"]).iloc[0]
    P.loc[i, ["pop", "pop_qid", "pop_label", "pop_class", "pop_km"]] = [b["pop"], b.qid, b.label, b.cls, round(b.km, 2)]
P["ww1_per1000"] = np.where((P["pop"] > 0) & P.ww1_dead.notna(), 1000 * P.ww1_dead / P["pop"], np.nan)
P["ww2_per1000"] = np.where((P["pop"] > 0) & P.ww2_dead.notna(), 1000 * P.ww2_dead / P["pop"], np.nan)

# ---- 3. Thankful Villages ----
TV = json.load(open(TVJ))
pt = cKDTree(np.c_[P.lng.values * K, P.lat.values])
T = []
for v in TV:
    nm = v["name"].split("/")[0].strip(); key = norm(nm)
    idx = pt.query_ball_point([v["lon"] * K, v["lat"]], 6.0 / 111.2)
    tok = lambda k: " ".join(sorted(k.split()))
    same = [j for j in idx if P.key.iloc[j] == key or P.key.iloc[j].startswith(key + " ") or key.startswith(P.key.iloc[j] + " ")
            or tok(P.key.iloc[j]) == tok(key)]
    j = None; how = "none found"
    if same:
        j = min(same, key=lambda j: np.hypot((P.lng.iloc[j] - v["lon"]) * K, P.lat.iloc[j] - v["lat"])); how = "same name"
    else:
        # fallback: a memorial within 1.5 km whose town is a near spelling of the village, or whose title names it
        dm = np.hypot((G.lng - v["lon"]) * K, G.lat - v["lat"]) * 111.2
        near = G[dm < 1.5].assign(km=dm[dm < 1.5])
        ok = [SequenceMatcher(None, k, key).ratio() >= 0.85 or re.search(r"\b" + re.escape(key) + r"\b", norm(t)) is not None
              for k, t in zip(near.town_key, near.title)]
        near = near[np.array(ok, dtype=bool)]
        if len(near):
            j = int(np.where(P.pid.values == near.sort_values("km").iloc[0].pid)[0][0]); how = "near spelling or title"
    T.append(dict(village=nm, county=v["county"], nation=v["nation"], doubly=v["doubly"], lat=v["lat"], lng=v["lon"],
                  pid=int(P.pid.iloc[j]) if j is not None else None, match=how))
T = pd.DataFrame(T)
P["thankful"] = P.pid.isin(T.pid.dropna().astype(int))
P["doubly"] = P.pid.isin(T[T.doubly].pid.dropna().astype(int))
# what the register holds at each Thankful Village
ext = []
for _, t in T.iterrows():
    if pd.isna(t.pid):
        ext.append(dict(n_mem=0, n_ww1=0, ww1_title="", ww1_mid=None, ww1_dead=None, ww1_served=None, ww1_status="", ww1_src="",
                        max_dead_any=None, served_any=None)); continue
    p = P[P.pid == t.pid].iloc[0]; sub = G[G.pid == t.pid]
    ext.append(dict(n_mem=int(p.n_mem), n_ww1=int(p.n_ww1), ww1_title=p.ww1_title, ww1_mid=p.ww1_mid, ww1_dead=p.ww1_dead,
                    ww1_served=p.ww1_served, ww1_status=p.ww1_status, ww1_src=p.ww1_src,
                    max_dead_any=float(sub.ww1_dead.max()) if sub.ww1_dead.notna().any() else None,
                    served_any=float(sub.ww1_served.max()) if sub.ww1_served.notna().any() else None))
T = pd.concat([T, pd.DataFrame(ext)], axis=1)
T.to_csv(os.path.join(ROOT, "data", "thankful_villages.csv"), index=False)

P.to_pickle(os.path.join(ROOT, "work", "places.pkl"))
G[["id", "pid"]].to_pickle(os.path.join(ROOT, "work", "mem_pid.pkl"))
out = P.drop(columns=["key"]).copy()
for c in ("ww1_per1000", "ww2_per1000"): out[c] = out[c].round(2)
out.to_csv(os.path.join(ROOT, "data", "places.csv"), index=False)
print(len(P), "places;", int(P.ww1_dead.notna().sum()), "with a WW1 community memorial;", int(P["pop"].notna().sum()), "with population")
print(T[["village", "match", "n_mem", "n_ww1", "ww1_title", "ww1_dead", "ww1_served", "ww1_status", "max_dead_any"]].to_string())
