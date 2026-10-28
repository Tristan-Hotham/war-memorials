"""Step 3. Every number used on the page, in the paper, the blog and the collage -> data/results.json.
Also writes work/site_data.json (compact map data, embedded in the page by step 4) and
data/memorials_search.json (compact list of published memorials, fetched by the page's search).

Run: python3 code/03_analyse.py
"""
import gzip, json, os, re
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
M = pd.read_pickle(os.path.join(ROOT, "work", "memorials_all.pkl"))
P = pd.read_pickle(os.path.join(ROOT, "work", "places.pkl"))
MP = pd.read_pickle(os.path.join(ROOT, "work", "mem_pid.pkl"))
T = pd.read_csv(os.path.join(ROOT, "data", "thankful_villages.csv"))
SRC = json.load(gzip.open("/home/claude/hist/_data11/iwm_memorials.json.gz"))
HIST = json.load(open("/home/claude/hist/_data9/wd_osm_bundle.json"))["wd_historic_populations_tsv"]
R = {}
i_ = lambda x: int(x)
f_ = lambda x, d=2: None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)

# ---------- 1. the register ----------
R["register"] = dict(rows=len(M), expected=SRC["expected_count"], retrieved="28 October 2026",
                     lost=i_(M.lost.sum()), located=i_(M.lat.notna().sum()), no_location=i_(M.lat.isna().sum()),
                     ww1=i_(M.ww1.sum()), ww2=i_(M.ww2.sum()), both=i_((M.ww1 & M.ww2).sum()),
                     civ1=i_(M.civ1.sum()), civ2=i_(M.civ2.sum()),
                     boer=i_(M.wars.str.contains("Boer War; Second").sum()))
R["register"]["ww1_share"] = M.ww1.mean(); R["register"]["ww2_share"] = M.ww2.mean()
types = M.types.str.split("; ").explode()
tc = types[types != ""].value_counts()
R["types"] = [dict(type=k, n=i_(v)) for k, v in tc.head(16).items()]
R["n_types"] = i_(len(tc))
grp = {"Board, plaque or tablet": ["Board / Plaque / Tablet"], "Addition to a gravestone": ["Addition to gravestone"],
       "Roll of honour or book": ["Roll of honour or book of remembrance"], "Cross": ["Cross"], "Window": ["Window"],
       "Obelisk, pillar or cenotaph": ["Obelisk", "Pillar / Column", "Cenotaph"], "Stone of remembrance": ["Stone of remembrance"],
       "Church fitting": [t for t in tc.index if t.startswith("Church Fabric")],
       "Figure or sculpture": ["Sculptured / Cast figure", "Sculptured / Cast group", "Serviceman / Servicewoman", "Allegory (eg: Victory)", "Sculpture", "Animal figure"],
       "Hall, garden, gate or seat": ["Hall / Institute", "Garden", "Gate", "Seat", "Avenue / Tree or grove", "Park / Sports field", "Memorial homes / Alms houses", "Hospital / Clinic", "Endowed bed", "Clock or clock tower", "Lamp or lighting", "Bells or bell tower", "Shelter", "Fountain", "Sports pavilion", "Accommodation", "Street", "Land"]}
R["type_groups"] = [dict(group=g, n=i_(M.types.apply(lambda s: any(t in s.split("; ") for t in ts)).sum())) for g, ts in grp.items()]
wc = M.wars.str.split(" | ", regex=False).explode(); wc = wc[wc != ""].value_counts()
R["wars"] = [dict(war=k, n=i_(v)) for k, v in wc.head(14).items()]
R["n_wars"] = i_(len(wc))
R["nations"] = {k: i_(v) for k, v in M.nation.value_counts().items()}
cls_names = ["community", "church", "school", "workplace", "military", "regional", "individual"]
R["classes"] = {c: dict(n=i_((M.cls == c).sum()), ww1=i_(((M.cls == c) & M.ww1).sum()),
                        ww1_dead=i_(M.loc[M.cls == c, "ww1_dead"].fillna(0).sum())) for c in cls_names}
R["published_memorials"] = i_((M.cls != "individual").sum())

# ---------- 2. names ----------
w1 = M[M.ww1]; w2 = M[M.ww2]
R["names"] = dict(
    ww1_tot=i_(w1.ww1_tot.fillna(0).sum()), ww1_died=i_(w1.ww1_died.fillna(0).sum()), ww1_served=i_(w1.ww1_served.fillna(0).sum()),
    ww1_dead=i_(w1.ww1_dead.fillna(0).sum()), ww1_with_count=i_((w1.ww1_tot.fillna(0) > 0).sum()),
    ww1_exact=i_(w1.ww1_exact.sum()), ww1_exact_share=w1.ww1_exact.mean(),
    ww1_served_only=i_((w1.ww1_status == "served only").sum()),
    ww2_tot=i_(w2.ww2_tot.fillna(0).sum()), ww2_died=i_(w2.ww2_died.fillna(0).sum()), ww2_dead=i_(w2.ww2_dead.fillna(0).sum()),
    ww1_big=i_((w1.ww1_dead.fillna(0) >= 5000).sum()), ww1_big_dead=i_(w1.loc[w1.ww1_dead.fillna(0) >= 5000, "ww1_dead"].sum()),
    ww1_median_named=f_(w1.loc[w1.ww1_dead.fillna(0) > 0, "ww1_dead"].median(), 1))
R["names"]["ww1_dead_excl_big"] = R["names"]["ww1_dead"] - R["names"]["ww1_big_dead"]
R["names"]["ww2_big"] = i_((w2.ww2_dead.fillna(0) >= 5000).sum())
R["names"]["ww2_dead_excl_big"] = i_(w2.loc[w2.ww2_dead.fillna(0) < 5000, "ww2_dead"].fillna(0).sum())
# benchmark from Wikipedia "World War I casualties" (table row United Kingdom of Great Britain and Ireland (and colonies),
# note s1: "Total of 744,000 dead and missing from the British Isles"; population 45.4 million), retrieved 28 Oct 2026
B = dict(uk_dead=744000, uk_pop=45.4e6, source="Wikipedia, World War I casualties (retrieved 28 October 2026)")
B["per1000"] = 1000 * B["uk_dead"] / B["uk_pop"]
B["entries_per_man"] = R["names"]["ww1_dead"] / B["uk_dead"]
B["entries_per_man_excl_big"] = R["names"]["ww1_dead_excl_big"] / B["uk_dead"]
R["benchmark"] = B

# ---------- 3. places and the community memorial ----------
p1 = P[P.ww1_dead.notna()]
R["places"] = dict(n=i_(len(P)), with_ww1=i_(len(p1)), src_community=i_((p1.ww1_src == "community").sum()),
                   src_church=i_((p1.ww1_src == "church").sum()), ww1_exact=i_(p1.ww1_exact.sum()),
                   ww1_exact_died=i_((p1.ww1_exact & (p1.ww1_status == "died")).sum()),
                   with_pop=i_(P["pop"].notna().sum()), with_ww1_pop=i_((p1["pop"].notna()).sum()),
                   chosen_sum=i_(p1.ww1_dead.sum()), naive_sum=i_(P.ww1_dead_all.sum()),
                   median_mem_per_place=f_(P.n_mem.median(), 1), multi_mem=i_((P.n_mem > 1).sum()),
                   with_ww2=i_(P.ww2_dead.notna().sum()), chosen_sum_ww2=i_(P.ww2_dead.fillna(0).sum()))
R["places"]["chosen_share_of_uk"] = R["places"]["chosen_sum"] / B["uk_dead"]
R["places"]["naive_over_chosen"] = R["places"]["naive_sum"] / R["places"]["chosen_sum"]
R["places"]["by_nation"] = {k: i_(v) for k, v in P.nation.value_counts().items()}
R["places"]["pop_classes"] = {k: i_(v) for k, v in P.pop_class.replace("", np.nan).dropna().value_counts().head(6).items()}
# size of the community memorial (names of the dead), all places with a died count > 0
pd1 = p1[(p1.ww1_status == "died") & (p1.ww1_dead > 0)]
bins = [1, 5, 10, 20, 50, 100, 250, 1000, 1e9]; labs = ["1 to 4", "5 to 9", "10 to 19", "20 to 49", "50 to 99", "100 to 249", "250 to 999", "1,000 or more"]
cut = pd.cut(pd1.ww1_dead, bins, right=False, labels=labs)
R["size_dist"] = [dict(band=l, n=i_((cut == l).sum())) for l in labs]
R["size_median"] = f_(pd1.ww1_dead.median(), 1)
R["size_n"] = i_(len(pd1))
top = P[P.ww1_dead.notna() & (P.ww1_status == "died")].sort_values("ww1_dead", ascending=False).head(15)
R["biggest"] = [dict(place=r.place, county=r.county, nation=r.nation, title=r.ww1_title, dead=i_(r.ww1_dead), mid=i_(r.ww1_mid),
                     exact=bool(r.ww1_exact)) for r in top.itertuples()]

# ---------- 4. names per 1,000 residents ----------
LO, HI = 100, 5000
S = P[P["pop"].between(LO, HI) & P.ww1_exact & P.ww1_status.isin(["died", "served only"])].copy()
S["rate"] = 1000 * S.ww1_dead / S["pop"]
q = S.rate.quantile([.1, .25, .5, .75, .9]).values
R["rate"] = dict(lo=LO, hi=HI, n=i_(len(S)), p10=f_(q[0]), p25=f_(q[1]), median=f_(q[2]), p75=f_(q[3]), p90=f_(q[4]),
                 mean=f_(S.rate.mean()), zero=i_((S.ww1_dead == 0).sum()), above_bench=i_((S.rate > B["per1000"]).sum()),
                 over100=i_((S.rate >= 100).sum()), pooled=f_(1000 * S.ww1_dead.sum() / S["pop"].sum()),
                 src_church=i_((S.ww1_src == "church").sum()))
R["rate"]["above_bench_share"] = R["rate"]["above_bench"] / R["rate"]["n"]
hb = list(range(0, 105, 5)); hc = np.histogram(S.rate.clip(upper=104.99), bins=hb + [1e9])[0]
R["rate_hist"] = [dict(lo=hb[i], n=i_(hc[i])) for i in range(len(hb))]
popb = [100, 200, 500, 1000, 2000, 5001]; pl = ["100 to 199", "200 to 499", "500 to 999", "1,000 to 1,999", "2,000 to 5,000"]
S["pb"] = pd.cut(S["pop"], popb, right=False, labels=pl)
R["rate_by_pop"] = [dict(band=l, n=i_((S.pb == l).sum()), median=f_(S.loc[S.pb == l, "rate"].median()),
                         median_dead=f_(S.loc[S.pb == l, "ww1_dead"].median(), 1)) for l in pl]
R["rate_by_nation"] = [dict(nation=k, n=i_(len(g)), median=f_(g.rate.median()), p25=f_(g.rate.quantile(.25)), p75=f_(g.rate.quantile(.75)), median_pop=f_(g["pop"].median(), 0),
                            median_dead=f_(g.ww1_dead.median(), 1))
                       for k, g in S.groupby("nation") if len(g) >= 20]
R["rate_by_nation"].sort(key=lambda r: -r["median"])
cty = [dict(county=k, nation=g.nation.mode().iloc[0], n=i_(len(g)), median=f_(g.rate.median())) for k, g in S.groupby("county") if len(g) >= 25 and k]
cty.sort(key=lambda r: -r["median"])
R["rate_by_county"] = cty
# league table: single-place memorials only (titles naming districts, several parishes, estates, clans,
# counties or books for a wider area are left out), 300+ residents today, and rates under 200 per 1,000
WIDE = r"\band\b|&|,|district|parishes|estate|clan|county|shire|golden book|united|with\b"
single = ~S.ww1_title.str.contains(WIDE, case=False, regex=True)
HS = S[(S["pop"] >= 300) & (S.ww1_status == "died") & single & (S.rate < 200)]
R["highest_rule"] = dict(min_pop=300, max_rate=200, n=i_(len(HS)), dropped_wide=i_(((S["pop"] >= 300) & ~single).sum()),
                         dropped_200=i_(((S["pop"] >= 300) & single & (S.rate >= 200)).sum()))
hi = HS.sort_values("rate", ascending=False).head(15)
R["highest"] = [dict(place=r.place, county=r.county, nation=r.nation, dead=i_(r.ww1_dead), pop=i_(r.pop), rate=f_(r.rate, 1),
                     title=r.ww1_title, mid=i_(r.ww1_mid), pop_label=r.pop_label, pop_class=r.pop_class) for r in hi.itertuples()]

# 1911 check: places whose Wikidata population item also has a 1911 census figure in Wikidata
h = []
for line in HIST.splitlines()[1:]:
    c = line.split("\t")
    if len(c) >= 5 and c[4].strip('"').startswith("1911"):
        h.append((c[0].strip("<>").rsplit("/", 1)[-1], float(c[3])))
H = dict(h)
S["pop1911"] = S.pop_qid.map(H)
S11 = S[S.pop1911.notna() & (S.pop1911 > 0)].copy(); S11["rate1911"] = 1000 * S11.ww1_dead / S11.pop1911
R["rate1911"] = dict(n=i_(len(S11)), median=f_(S11.rate1911.median()), median_modern=f_(S11.rate.median()),
                     p25=f_(S11.rate1911.quantile(.25)), p75=f_(S11.rate1911.quantile(.75)),
                     pooled=f_(1000 * S11.ww1_dead.sum() / S11.pop1911.sum()) if len(S11) else None)

# ---------- 5. the Second World War on the same memorials ----------
B2 = P[P.ww1_exact & P.ww2_exact & (P.ww1_status == "died") & (P.ww2_status == "died") & (P.ww1_mid == P.ww2_mid)]
r2 = B2.ww2_dead / B2.ww1_dead
R["ww2"] = dict(n=i_(len(B2)), median_ratio=f_(r2.median(), 3), more_ww2=i_((B2.ww2_dead > B2.ww1_dead).sum()),
                sum_ww1=i_(B2.ww1_dead.sum()), sum_ww2=i_(B2.ww2_dead.sum()))
R["ww2"]["pooled_ratio"] = R["ww2"]["sum_ww2"] / R["ww2"]["sum_ww1"]
R["ww2"]["more_ww2_share"] = R["ww2"]["more_ww2"] / max(1, R["ww2"]["n"])

# ---------- 6. Thankful Villages ----------
mem_pid = MP.merge(M[["id", "cls", "ww1", "ww1_dead", "ww1_status", "title"]], on="id")
tv = []
for r in T.itertuples():
    sub = mem_pid[mem_pid.pid == r.pid] if not pd.isna(r.pid) else mem_pid.iloc[0:0]
    dead_any = sub[(sub.ww1_status == "died") & (sub.ww1_dead > 0)]
    thank = sub.title.str.contains(r"thank", case=False).any()
    served = sub[(sub.ww1_status == "served only")]
    tv.append(dict(village=r.village, county=r.county, nation=r.nation, doubly=bool(r.doubly), matched=not pd.isna(r.pid),
                   n_mem=i_(len(sub)), served_only=len(served) > 0, served_max=i_(served.ww1_dead.size and sub.loc[served.index].shape[0]) if False else None,
                   thank_title=bool(thank), dead_any=i_(dead_any.ww1_dead.sum()) if len(dead_any) else 0,
                   dead_mem=i_(len(dead_any)), dead_indiv=i_((dead_any.cls == "individual").sum()),
                   lat=r.lat, lng=r.lng, pid=None if pd.isna(r.pid) else i_(r.pid)))
TVD = pd.DataFrame(tv)
srv = {}
for r in T.itertuples():
    if not pd.isna(r.pid):
        s = M[M.id.isin(MP[MP.pid == r.pid].id)]
        srv[r.village] = s.loc[s.ww1_status == "served only", "ww1_served"].max()
TVD["served_n"] = TVD.village.map(srv)
R["thankful"] = dict(n=i_(len(TVD)), england=i_((TVD.nation == "England").sum()), wales=i_((TVD.nation == "Wales").sum()),
                     doubly=i_(TVD.doubly.sum()), matched=i_(TVD.matched.sum()), with_served_roll=i_(TVD.served_only.sum()),
                     thank_title=i_(TVD.thank_title.sum()), any_record=i_((TVD.n_mem > 0).sum()),
                     with_dead=i_((TVD.dead_any > 0).sum()), with_dead_indiv_only=i_(((TVD.dead_any > 0) & (TVD.dead_mem == TVD.dead_indiv)).sum()),
                     served_median=f_(TVD.served_n.median(), 1), served_total=i_(TVD.served_n.fillna(0).sum()),
                     served_n=i_(TVD.served_n.notna().sum()))
R["thankful_list"] = [dict(village=r.village, county=r.county, nation=r.nation, doubly=r.doubly, n_mem=r.n_mem,
                           served=None if pd.isna(r.served_n) else i_(r.served_n), dead_any=r.dead_any, dead_mem=r.dead_mem,
                           dead_indiv=r.dead_indiv, thank_title=r.thank_title) for r in TVD.itertuples()]
nk = TVD[TVD.village == "Nether Kellet"].iloc[0]
R["thankful"]["nether_kellet_dead"] = i_(nk.dead_any)
# the tail: small places whose community memorial records no dead
R["tail"] = dict(zero=R["rate"]["zero"], one=i_((S.ww1_dead == 1).sum()), two=i_((S.ww1_dead == 2).sum()),
                 three=i_((S.ww1_dead == 3).sum()), le3=i_((S.ww1_dead <= 3).sum()), n=R["rate"]["n"])
R["tail"]["zero_share"] = R["tail"]["zero"] / R["tail"]["n"]
R["tail"]["zero_tv"] = i_((S.thankful & (S.ww1_dead == 0)).sum()); R["tail"]["zero_other"] = R["tail"]["zero"] - R["tail"]["zero_tv"]
R["tail"]["le3_share"] = R["tail"]["le3"] / R["tail"]["n"]
# places (any size) where the register holds only a roll of those who served: no memorial at the place records any WW1 dead
dead_pid = set(mem_pid.loc[(mem_pid.ww1_dead.fillna(0) > 0) & (mem_pid.ww1_status != "served only"), "pid"])
SO = P[(P.ww1_status == "served only") & ~P.pid.isin(dead_pid)].copy()
SO["tv"] = SO.thankful
R["served_only"] = dict(n=i_(len(SO)), tv=i_(SO.tv.sum()), other=i_((~SO.tv).sum()),
                        exact=i_((SO.ww1_exact & ~SO.tv).sum()))
oth = SO[~SO.tv].sort_values("ww1_served", ascending=False)
R["served_only_list"] = [dict(place=r.place, county=r.county, nation=r.nation, served=None if pd.isna(r.ww1_served) else i_(r.ww1_served),
                              title=r.ww1_title, mid=i_(r.ww1_mid), exact=bool(r.ww1_exact)) for r in oth.itertuples()]
R["served_only_by_nation"] = {k: i_(v) for k, v in oth.nation.value_counts().items()}
# candidates worth checking: small places (population proxy up to 5,000 or unknown) whose only First World War
# community record lists between 1 and 100 people who served, and no memorial at the place records any dead
cand = oth[oth.ww1_served.between(1, 100) & (oth["pop"].isna() | (oth["pop"] <= 5000))]
R["candidates"] = dict(n=i_(len(cand)), exact=i_(cand.ww1_exact.sum()), with_pop=i_(cand["pop"].notna().sum()),
                       by_nation={k: i_(v) for k, v in cand.nation.value_counts().items()})
R["candidates_list"] = [dict(place=r.place, county=r.county, nation=r.nation, served=i_(r.ww1_served), title=r.ww1_title,
                             mid=i_(r.ww1_mid), exact=bool(r.ww1_exact), pop=None if pd.isna(r.pop) else i_(r.pop),
                             lat=r.lat, lng=r.lng) for r in cand.sort_values(["nation", "county", "place"]).itertuples()]
# the earlier Thankful Villages study (github.com/Tristan-Hotham/thankful-villages, data/thankful.json)
E = json.load(open(os.path.join(ROOT, "work", "thankful-villages", "data", "thankful.json")))
R["earlier"] = dict(expected_low=min(E["expected"].values()), expected_high=max(E["expected"].values()), risk=E["d"],
                    n_parishes=E["n_parishes"], doi="10.5281/zenodo.23676168",
                    nether_kellet_served=[x[1] for x in E["served"] if x[0] == "Nether Kellet"][0])

# ---------- 7. examples for the text ----------
def place_row(name, county=None):
    c = P[(P.place == name) & P.ww1_dead.notna()]
    if county: c = c[c.county == county]
    if not len(c): return None
    r = c.sort_values("ww1_dead", ascending=False).iloc[0]
    return dict(place=r.place, county=r.county, dead=f_(r.ww1_dead, 0), pop=f_(r["pop"], 0), rate=f_(r.ww1_per1000, 1),
                title=r.ww1_title, n_mem=i_(r.n_mem), dead_all=i_(r.ww1_dead_all), mid=i_(r.ww1_mid))
R["examples"] = {k: place_row(k) for k in ["Buckden", "Accrington"]}

json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))

# ---------- site data ----------
cnt = sorted(set(P.county.fillna("")))
CI = {c: i for i, c in enumerate(cnt)}
NAT = ["England", "Scotland", "Wales", "Northern Ireland", "Isle of Man", "Channel Islands"]
pts = []
for r in P.itertuples():
    pts.append([round(r.lat, 4), round(r.lng, 4), r.place, CI[r.county or ""], NAT.index(r.nation) if r.nation in NAT else 0,
                None if pd.isna(r.ww1_dead) else int(r.ww1_dead), int(bool(r.ww1_exact)),
                {"died": 0, "served only": 1, "status not given": 2}.get(r.ww1_status, 3),
                None if pd.isna(r.ww1_served) else int(r.ww1_served),
                None if pd.isna(r.ww2_dead) else int(r.ww2_dead), None if pd.isna(r.pop) else int(r.pop),
                int(r.n_mem), r.ww1_title or "", None if pd.isna(r.ww1_mid) else int(r.ww1_mid),
                int(r.thankful) + int(r.doubly), 1 if r.ww1_src == "church" else 0])
site = dict(cols="lat,lng,place,county,nation,ww1dead,exact,status,served,ww2dead,pop,nmem,title,mid,thankful,church", counties=cnt,
            nations=NAT, pts=pts, tv=[[r["village"], r["county"], r["lat"], r["lng"], int(r["doubly"])] for r in tv],
            hist=R["rate_hist"])
json.dump(site, open(os.path.join(ROOT, "work", "site_data.json"), "w"), separators=(",", ":"), ensure_ascii=False)

# ---------- search file (published memorials only, no memorials to one named person) ----------
Pub = M[(M.cls != "individual") & M.lat.notna()].merge(MP, on="id", how="left")
CL = ["community", "church", "school", "workplace", "military", "regional"]
srch = [[int(r.id), r.title, r.town, r.county if isinstance(r.county, str) else "", round(r.lat, 4), round(r.lng, 4),
         None if pd.isna(r.ww1_dead) else int(r.ww1_dead), None if pd.isna(r.ww2_dead) else int(r.ww2_dead), CL.index(r.cls),
         int(bool(r.lost)), None if pd.isna(r.pid) else int(r.pid)] for r in Pub.itertuples()]
json.dump(dict(cols="id,title,town,county,lat,lng,ww1dead,ww2dead,cls,lost,pid", classes=CL, rows=srch),
          open(os.path.join(ROOT, "data", "memorials_search.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print(json.dumps({k: R[k] for k in ["register", "names", "benchmark", "places", "rate", "rate1911", "ww2", "thankful", "tail", "served_only"]}, indent=1, default=str))
print(R["rate_by_pop"]); print(R["rate_by_nation"]); print(R["rate_by_county"][:8], R["rate_by_county"][-8:])
print(pd.DataFrame(R["highest"]).to_string()); print(pd.DataFrame(R["served_only_list"][:25]).to_string())
print(pd.DataFrame(R["thankful_list"]).to_string()); print(R["examples"])
