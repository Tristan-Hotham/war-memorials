"""Step 1. Read the IWM War Memorials Register extract and build one clean row per memorial.

Input : /home/claude/hist/_data11/iwm_memorials.json.gz (IWM War Memorials Register via its JSON:API,
        retrieved 28 Oct 2026; pass another path as the first argument).
        /home/claude/hist/osnames_gb.tsv (OS Open Names, for county and nation of each memorial).
Output: work/memorials_all.pkl (every memorial, internal only, not published)
        data/memorials.csv (published: every memorial except those to one named person, see README)

For each memorial I keep: its current location (first location flagged current, else the first with
coordinates), the town given there, its types, the lost flag, and for the First and Second World Wars
the number of names, the number recorded as died and as served, and the exact-count flag.
Each memorial is then given one class by simple, documented rules on its types and title:
individual, military, regional, school, workplace, church or community. See README for the rules.
Run: python3 code/01_prepare.py [path/to/iwm_memorials.json.gz]
"""
import gzip, json, os, re, sys
import numpy as np, pandas as pd
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
SRC = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/hist/_data11/iwm_memorials.json.gz"
OSN = "/home/claude/hist/osnames_gb.tsv"
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True); os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)

D = json.load(gzip.open(SRC))
rows = D["rows"]
W1, W2 = "First World War (1914-1918)", "Second World War (1939-1945)"

INDIV_TYPES = {"Addition to gravestone", "Serviceman / Servicewoman"}
OBJECT_TYPES = {"Battlefield cross or marker", "Trophy / Relic", "Locomotive / Train"}
CHURCH_TYPES = {"Window", "Chapel: Dedicated within church building", "Triptych", "Chapel or Church: Restoration or extension",
                "Chapel or Church: Freestanding building"}
RANK = (r"private|pte|captain|capt|lieutenant|lieut|lt|sergeant|serjeant|serjt|sgt|corporal|cpl|lance corporal|l/cpl|major|"
        r"gunner|sapper|rifleman|second lieutenant|2nd lieutenant|2nd lt|flying officer|pilot officer|flight lieutenant|"
        r"flight sergeant|squadron leader|wing commander|group captain|air commodore|major general|lieutenant colonel|colonel|"
        r"brigadier|general|admiral|commander|lieutenant commander|midshipman|able seaman|leading seaman|stoker|driver|trooper|"
        r"bombardier|guardsman|fusilier|drummer|piper|nurse|sister|matron|rev|reverend|dr|sir|lord|lady|sub lt|sub lieutenant|"
        r"engineer|petty officer|chief petty officer|warrant officer|company sergeant major|csm|rsm|cadet|aircraftman|lac|ac2|ac1|"
        r"marine|signaller|seaman|ensign|cornet|surgeon|chaplain|quartermaster|qms|cqms")
RE_RANK = re.compile(r"^\s*(" + RANK + r")\.?\s", re.I)
RE_INITIALS = re.compile(r"^\s*([A-Z](\.\s*|\s+)){1,4}(Mc|Mac|O'|De |Van )?[A-Z][a-z][a-zA-Z'\-]*(\s*[-,(&]|\s+and\s|\s*$)")
COUNTIES = ("bedfordshire|berkshire|buckinghamshire|cambridgeshire|cheshire|cornwall|cumberland|derbyshire|devon|dorset|durham|essex|"
            "gloucestershire|hampshire|herefordshire|hertfordshire|huntingdonshire|kent|lancashire|leicestershire|lincolnshire|middlesex|"
            "norfolk|northamptonshire|northumberland|nottinghamshire|oxfordshire|rutland|shropshire|somerset|staffordshire|suffolk|surrey|"
            "sussex|warwickshire|westmorland|wiltshire|worcestershire|yorkshire|anglesey|brecknockshire|caernarfonshire|cardiganshire|"
            "carmarthenshire|denbighshire|flintshire|glamorgan|merionethshire|monmouthshire|montgomeryshire|pembrokeshire|radnorshire|"
            "aberdeenshire|angus|argyll|ayrshire|banffshire|berwickshire|caithness|dumfriesshire|fife|inverness-shire|kincardineshire|"
            "lanarkshire|midlothian|morayshire|nairnshire|orkney|peeblesshire|perthshire|renfrewshire|ross and cromarty|roxburghshire|"
            "selkirkshire|stirlingshire|sutherland|west lothian|east lothian|wigtownshire|antrim|armagh|down|fermanagh|londonderry|tyrone")
RE_REGION = re.compile(r"\b(national war memorial|national memorial|national roll|scottish national|welsh national|manx national|national book|german war|german cemetery|germans|empire|imperial|commonwealth|allied|allies|international|battle of|"
                       r"county war memorial|county memorial|county book|county roll|shire book|shire roll|shire war memorial|"
                       r"heroes' memorial|clan|holocaust|genocide|shot at dawn|north wales|south wales|welsh book|welsh national|scottish|ulster|county of|whole county)\b", re.I)
RE_COUNTY_START = re.compile(r"^\s*(" + COUNTIES + r")\b", re.I)
RE_AIRCRAFT = re.compile(r"\b(avro|lancaster|handley page|halifax|wellington|vickers|short stirling|stirling|catalina|consolidated|"
                         r"de havilland|mosquito|spitfire|hurricane|b-17|b-24|b17|b24|liberator|flying fortress|dakota|douglas|"
                         r"blenheim|beaufighter|hampden|whitley|heinkel|junkers|messerschmitt|dornier|sunderland|anson|oxford|"
                         r"typhoon|tempest|thunderbolt|mustang|lightning|marauder|mitchell|boston|ventura|hudson|beaufort|"
                         r"botha|defiant|gladiator|hawker|bristol|fairey|swordfish|meteor|vampire|canberra|vulcan|victor|"
                         r"valiant|shackleton|airship|zeppelin|aircrew|air crash|crash site|aircraft)\b", re.I)
RE_MIL = re.compile(r"\b(regiment|regiments|regt|regimental|battalion|battalions|bn|brigade|division|div|corps|squadron|sqn|flight|wing|raf|r\.a\.f|"
                    r"royal air force|royal flying corps|rfc|royal navy|navy|naval|hms|h\.m\.s|hmt|submarine|yeomanry|fusiliers|"
                    r"guards|rifles|rifle brigade|light infantry|infantry|artillery|engineers|royal marines|commando|airborne|parachute|"
                    r"army|expeditionary|association|old comrades|oca|veterans|territorial|militia|volunteers|home guard|"
                    r"cavalry|hussars|lancers|dragoons|highlanders|borderers|grenadier|gurkha|machine gun|tank|signals|"
                    r"usaaf|us army|american|canadian|australian|new zealand|polish|czech|french|belgian|norwegian|dutch|"
                    r"prisoners of war|pow|bomber command|coastal command|fighter command|air training|airfield|aerodrome|"
                    r"burma star|commonwealth war graves|cwgc)\b", re.I)
RE_SCHOOL = re.compile(r"\b(school|schools|college|academy|university|grammar|old boys|old girls|scouts?|boys' brigade|boys brigade|"
                       r"seminary|institution|polytechnic|technical institute|pupils|scholars|old [a-z]+ians|oldians|cadets)\b", re.I)
RE_WORK = re.compile(r"\b(railway|railways|rly|lnwr|l n w r|gwr|g w r|lms|lner|ner|midland|great western|great eastern|great northern|"
                     r"southern railway|company|co\.|coy|ltd|limited|plc|works|colliery|collieries|mine|mines|pit|quarry|bank|"
                     r"post office|gpo|g p o|postmen|police|constabulary|fire brigade|fire service|club|lodge|masonic|freemasons?|"
                     r"oddfellows|foresters|buffaloes|rotary|society|co-operative|cooperative|co-op|hospital|insurance|assurance|"
                     r"newspaper|brewery|brewers|shipyard|shipbuilding|dock|docks|harbour board|exchange|employees|employes|staff|"
                     r"workers|workmen|tramways|corporation|gas light|gasworks|electricity|union|guild|chamber of commerce|cricket|"
                     r"football|rugby|golf|bowling|bowls|rowing|swimming|harriers|athletic|tennis|hockey|stores|bros|& sons|and sons|"
                     r"factory|foundry|steelworks|ironworks|wireworks|chemical|telegraph|telephone|customs|excise|inland revenue|"
                     r"ministry|stock exchange|lloyds|lloyd's|warehouse|mill company|mills ltd|printing|press|council staff|"
                     r"council employees|county council|borough council|civil service|admiralty|war office|board of|"
                     r"lifeboat|rnli|trinity house|pilots|fishermen|merchant navy|merchant seamen|mercantile marine|"
                     r"y m c a|ymca|salvation army|toc h|british legion|royal british legion|comrades of the great war)\b", re.I)
RE_CHURCH = re.compile(r"\b(church|churches|chapel|cathedral|abbey|priory|minster|kirk|methodist|wesleyan|wesley|primitive|baptist|"
                       r"congregational|united reformed|urc|presbyterian|catholic|roman catholic|synagogue|hebrew|jewish|mosque|"
                       r"sunday school|parishioners|congregation|mission|tabernacle|free church|st|st\.|saint|saints|all saints|"
                       r"holy|christ|our lady|sacred heart|evangelical|quaker|friends meeting|bible class|choir|bell ?ringers|"
                       r"ringers|vicar|rector|curate|clergy|bethel|bethesda|ebenezer|zion|salem|calvinistic|independent chapel|"
                       r"unitarian|brethren|gospel hall|mariners' church|episcopal|parish church|benefice)\b", re.I)


def norm_town(s):
    s = (s or "").strip().lower().replace("&", " and ")
    s = re.sub(r"\bsaint\b", "st", s); s = re.sub(r"\bst\.", "st", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def war(r, name):
    E = [w for w in r["wars"] if w["w"] == name]
    if not E: return None
    # a few memorials carry the same war twice: keep the entry with most names
    e = max(E, key=lambda w: (w["tot"] or 0, w["died"] or 0))
    tot, died, served = e["tot"], e["died"], e["served"]
    # names of the dead: the 'died' count; if neither died nor served is given but there are names, the names
    if (died or 0) > 0: dead, status = died, "died"
    elif (served or 0) > 0: dead, status = 0, "served only"
    elif (tot or 0) > 0: dead, status = tot, "status not given"
    else: dead, status = None, "no count"
    return dict(tot=tot, died=died, served=served, exact=e["exact"], dead=dead, status=status)


def classify(r, title, town, w1, w2):
    types = set(r["types"])
    tots = [w["tot"] or 0 for w in r["wars"]]
    t = title or ""
    tt = t
    if town:  # strip the town's own name so "St Ives War Memorial" is not read as a church
        tt = re.sub(re.escape(town.strip()), " ", t, flags=re.I)
    if types & INDIV_TYPES or (tots and max(tots) == 1) or RE_RANK.search(t) or RE_INITIALS.search(t):
        return "individual"
    if any(w["w"] in ("Regimental Memorials", "Military Service") for w in r["wars"]) or RE_AIRCRAFT.search(tt) or RE_MIL.search(tt) \
            or (types and types <= OBJECT_TYPES):
        return "military"
    if RE_SCHOOL.search(tt): return "school"
    if RE_WORK.search(tt): return "workplace"
    if (RE_REGION.search(tt) or (RE_COUNTY_START.search(t) and not (town and t.lower().startswith(town.strip().lower())))) \
            and not re.search(r"county borough|city and county", tt, re.I):
        return "regional"
    if RE_CHURCH.search(tt) or (types and types <= (CHURCH_TYPES | {x for x in types if x.startswith("Church Fabric")})):
        return "church"
    return "community"


out = []
for r in rows:
    locs = r["locs"]
    loc = next((l for l in locs if l["cur"] == "1" and l["lat"] is not None), None) or \
        next((l for l in locs if l["lat"] is not None), None) or (locs[0] if locs else None)
    lat = loc["lat"] if loc else None; lng = loc["lng"] if loc else None
    town = re.sub(r"\s*[\u2013\u2014]\s*", " - ", (loc["town"] or "").strip()) if loc else ""
    title = re.sub(r"\s*[\u2013\u2014]\s*", " - ", (r["t"] or "").strip())  # register dashes shown as hyphens
    w1, w2 = war(r, W1), war(r, W2)
    cls = classify(r, title, town, w1, w2)
    rec = dict(id=r["id"], title=title, town=town, town_key=norm_town(town), lat=lat, lng=lng,
               postcode=(loc.get("pc") or "") if loc else "", lost=r["lost"] == "1", types="; ".join(r["types"]),
               n_types=len(r["types"]), wars=" | ".join(sorted({w["w"] for w in r["wars"] if w["w"]})), cls=cls,
               civ1=any(w["w"] == "First World War - civilians" for w in r["wars"]),
               civ2=any(w["w"] == "Second World War - civilians" for w in r["wars"]))
    for k, w in (("ww1", w1), ("ww2", w2)):
        rec[k] = w is not None
        for f in ("tot", "died", "served", "dead"):
            rec[f"{k}_{f}"] = (w or {}).get(f)
        rec[f"{k}_exact"] = (w or {}).get("exact") == "1"
        rec[f"{k}_status"] = (w or {}).get("status")
    out.append(rec)
M = pd.DataFrame(out)

# nation and county from the nearest OS Open Names populated place (Great Britain); boxes for NI, IoM, Channel Islands
osn = pd.read_csv(OSN, sep="\t", usecols=["type", "lat", "lon", "x", "y", "county", "district", "country"], dtype=str)
osn = osn[osn["type"] == "populatedPlace"].copy()
for c in ("lat", "lon"): osn[c] = osn[c].astype(float)
K = np.cos(np.radians(54.5))
tree = cKDTree(np.c_[osn.lon.values * K, osn.lat.values])
has = M.lat.notna()
d, i = tree.query(np.c_[M.loc[has, "lng"].values * K, M.loc[has, "lat"].values])
M.loc[has, "os_km"] = d * 111.2
M.loc[has, "county"] = osn.county.fillna("").values[i]
M.loc[has, "district"] = osn.district.fillna("").values[i]
M.loc[has, "nation"] = osn.country.values[i]
lat, lng = M.lat, M.lng
ni = has & lat.between(54.0, 55.35) & lng.between(-8.2, -5.4)
iom = has & lat.between(54.03, 54.43) & lng.between(-4.85, -4.28)
ci = has & lat.between(49.1, 49.8) & lng.between(-2.75, -2.0)
M.loc[ni, "nation"] = "Northern Ireland"; M.loc[iom, "nation"] = "Isle of Man"; M.loc[ci, "nation"] = "Channel Islands"
M.loc[ni | iom | ci, ["county", "district"]] = ""
far = has & ~(ni | iom | ci) & (M.os_km > 15)
M.loc[far, "nation"] = "Elsewhere"; M.loc[far, ["county", "district"]] = ""
M.loc[~has, "nation"] = "No location"
M.to_pickle(os.path.join(ROOT, "work", "memorials_all.pkl"))

# published memorial file: everything except memorials to one named person (their titles are personal names)
P = M[M.cls != "individual"].copy()
cols = ["id", "title", "town", "county", "nation", "lat", "lng", "lost", "types", "cls",
        "ww1_tot", "ww1_died", "ww1_served", "ww1_exact", "ww2_tot", "ww2_died", "ww2_served", "ww2_exact", "wars"]
P["lat"] = P.lat.round(5); P["lng"] = P.lng.round(5)
for c in ("title", "town", "types", "wars"):
    P[c] = P[c].astype(str).map(lambda v: re.sub(r"\s*[\u2013\u2014]\s*", " - ", v))
P[cols].to_csv(os.path.join(ROOT, "data", "memorials.csv"), index=False)
print(len(M), "memorials;", M.cls.value_counts().to_dict())
print("published", len(P))
print(M.nation.value_counts().to_dict())
