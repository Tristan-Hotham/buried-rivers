"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv, data/*.geojson) and the page
data (data/site.json, data/waterways.json).

Definitions:
  * length: haversine length of each OSM way inside Greater London (Natural Earth boundary), km;
  * buried: common.buried(); open: everything else;
  * a river: OSM ways grouped by common.river_key(); 'named rivers' are all named groups, of any waterway type;
  * the ranking of the most buried rivers uses named rivers with at least MIN_KM of mapped line in Greater London;
  * inner London: London Government Act 1963 (common.INNER); borough and inner/outer figures leave out the Thames;
  * lost rivers: common.LOST, from Wikipedia's 'Subterranean rivers of London' and its river articles. Their stories
    and dates are paraphrases of the articles; every quoted phrase and every number in a story is checked against the
    article text below."""
import numpy as np, pandas as pd
from collections import defaultdict
from shapely.geometry import LineString, mapping
from common import *

MIN_KM = 3.0
W = pd.read_pickle(f"{WORK}/ways_gl.pkl")
CHK = jload(f"{WORK}/checks.json")
LON = jload(f"{DATA}/london.json")
G = W[W.inside > 0].copy()
G["kb"] = G.km_gl * G.buried; G["ko"] = G.km_gl * (1 - G.buried)
pc = lambda a, b: round(100 * a / b, 2) if b else None
r2 = lambda v: round(float(v), 2)
R = {}

# ---------- source ----------
R["source"] = {"ways_box": CHK["ways"], "buried_ways_box": CHK["buried_ways"], "tunnel_or_neglayer": CHK["tunnel_or_neglayer"],
               "km_box": CHK["km_bbox"], "km_box_buried": CHK["km_bbox_buried"], "osm_year": OSM_YEAR, "bbox": list(BBOX),
               "ways_gl": len(G), "ways_gl_buried": int(G.buried.sum()), "named_rivers_gl": int(G[G.key != ""].key.nunique()),
               "thames_dups": CHK["thames_dups"], "thames_dups_km": CHK["thames_dups_km_gl"], "boroughs": len(LON["features"]), "area_km2": LON["area_km2"], "types_box": CHK["types"], "checks": CHK}
assert R["source"]["ways_box"] == 8439 and R["source"]["tunnel_or_neglayer"] == 2382

# ---------- Greater London overall ----------
km, kb = G.km_gl.sum(), G.kb.sum()
th = G[G.key == "thames"]
un = G[G.key == ""]; nm = G[G.key != ""]
R["gl"] = {"km": r2(km), "km_buried": r2(kb), "km_open": r2(km - kb), "pct_buried": pc(kb, km),
           "thames_km": r2(th.km_gl.sum()), "km_ex_thames": r2(km - th.km_gl.sum()), "pct_ex_thames": pc(kb - th.kb.sum(), km - th.km_gl.sum()),
           "unnamed_km": r2(un.km_gl.sum()), "unnamed_pct_buried": pc(un.kb.sum(), un.km_gl.sum()), "unnamed_share_pct": pc(un.km_gl.sum(), km),
           "named_km": r2(nm.km_gl.sum()), "named_pct_buried": pc(nm.kb.sum(), nm.km_gl.sum()),
           "km_per_km2": round(km / LON["area_km2"], 3), "buried_m_per_km2": round(1000 * kb / LON["area_km2"])}
R["gl"]["one_in"] = round(100 / R["gl"]["pct_buried"])
assert 1250 < km < 1400 and 15 < R["gl"]["pct_buried"] < 20, (km, R["gl"]["pct_buried"])
assert th.kb.sum() < .01                                   # the Thames is open water all the way

# ---------- by waterway type ----------
ty = []
for t in TYPES:
    a = G[G.type == t]
    ty.append({"type": t, "label": TYPE_NAME[t], "km": r2(a.km_gl.sum()), "km_buried": r2(a.kb.sum()), "km_open": r2(a.ko.sum()),
               "pct_buried": pc(a.kb.sum(), a.km_gl.sum()), "ways": len(a), "share_of_buried_pct": pc(a.kb.sum(), kb)})
R["types"] = {t["type"]: t for t in ty}; R["types_list"] = ty
assert max(ty, key=lambda t: t["pct_buried"])["type"] == "stream" and max(ty, key=lambda t: t["km_buried"])["type"] == "stream"
pd.DataFrame(ty).to_csv(f"{DATA}/waterways_by_type.csv", index=False)

# ---------- named rivers ----------
WP = jload(f"{WORK}/ways_page.json")
DISP = dict(WP["rivers"])
bor_of = defaultdict(lambda: defaultdict(float))
for r in G.itertuples():
    for b, v in r.bkm.items():
        bor_of[r.key][b] += v
rv = []
for k, a in nm.groupby("key"):
    bb = sorted(bor_of[k].items(), key=lambda kv: -kv[1])
    rv.append({"key": k, "name": DISP[k], "km": r2(a.km_gl.sum()), "km_buried": r2(a.kb.sum()), "km_open": r2(a.ko.sum()),
               "pct_buried": pc(a.kb.sum(), a.km_gl.sum()), "ways": len(a), "types": sorted(a.type.unique().tolist()),
               "boroughs": [BOROUGH_NAME.get(b, b) for b, v in bb if v >= .05][:6], "lost": LOST_BY_OSM.get(k, "")})
RV = pd.DataFrame(rv).sort_values("km", ascending=False)
RV.assign(types=RV.types.map(";".join), boroughs=RV.boroughs.map(";".join)).to_csv(f"{DATA}/rivers.csv", index=False)
R["rivers"] = {r["key"]: r for r in rv}
big = RV[RV.km >= MIN_KM]
top_share = big.sort_values(["pct_buried", "km_buried"], ascending=False)
top_km = RV.sort_values("km_buried", ascending=False)
R["rank"] = {"min_km": MIN_KM, "n_big": len(big), "n_big_over_half": int((big.pct_buried > 50).sum()), "n_big_all": int((big.pct_buried >= 99.5).sum()),
             "n_big_none": int((big.km_buried == 0).sum()),
             "by_share": [{"key": r.key, "name": r.name, "km": r.km, "km_buried": r.km_buried, "pct": r.pct_buried} for r in top_share.head(15).itertuples()],
             "by_km": [{"key": r.key, "name": r.name, "km": r.km, "km_buried": r.km_buried, "pct": r.pct_buried} for r in top_km.head(15).itertuples()]}
R["rank"]["top4_km_buried"] = r2(top_km.head(4).km_buried.sum()); R["rank"]["top4_pct_of_buried"] = pc(top_km.head(4).km_buried.sum(), kb)
assert [r["key"] for r in R["rank"]["by_km"][:4]] == ["moselle", "westbourne", "tyburn", "fleet"], [r["key"] for r in R["rank"]["by_km"][:6]]
for k in ("tyburn", "westbourne", "fleet", "moselle", "neckinger"):
    assert k in [r["key"] for r in R["rank"]["by_share"]], k
big_rivers = ["thames", "lea", "wandle", "brent", "ravensbourne", "crane", "colne", "roding"]
R["big_rivers"] = {k: {"name": R["rivers"][k]["name"], "km": R["rivers"][k]["km"], "pct": R["rivers"][k]["pct_buried"]} for k in big_rivers if k in R["rivers"]}

# ---------- Wikipedia ----------
WK = jload(f"{RAW}/london_rivers_wiki.json")


def page(t):
    q = WK[t]; p = list(q["pages"].values())[0]
    return None if "missing" in p else p


SUB = page("Subterranean rivers of London")["extract"]
north = SUB.split("== North of the Thames ==")[1].split("== South of the Thames ==")[0]
south = SUB.split("== South of the Thames ==")[1].split("\n\n\n==")[0]
lst = lambda s: [l.strip() for l in s.strip().splitlines() if l.strip() and not l.startswith("From west to east")]
NL, SL = lst(north), lst(south)
R["sub"] = {"north_n": len(NL), "south_n": len(SL), "n": len(NL) + len(SL), "north": NL, "south": SL,
            "partly": sum("partially underground" in x for x in NL + SL)}
for s in ("now flow through culverts", "London Rivers Action Plan", "In January 2009"):
    assert s in SUB, s
R["wiki_sub"] = {"lrap_year": 2009}
missing = [t for t in WK if not t.startswith("__") and page(t) is None]
redir = {t: list(WK[t]["pages"].values())[0]["title"] for t in WK if not t.startswith("__") and WK[t].get("redirects")}
assert set(missing) == {"Falcon Brook", "Ching Brook", "Bounds Green Brook", "Tyburn (village)"}, missing
assert redir["Black Ditch"] == "Taiwan Strait"
R["wiki_meta"] = {"titles": sum(1 for t in WK if not t.startswith("__")), "missing": missing, "dropped": ["Black Ditch", "Norwood", "Kidbrooke", "Lost rivers of London"],
                  "redirects": redir}

# ---------- lost rivers ----------
nums = lambda s: set(re.findall(r"\d[\d,]*", s.replace(",", "")))
lost = []
for l in LOST:
    a = G[G.key.isin(l["osm"])]
    p = page(l["wiki"]) if l["wiki"] else None
    if l["wiki"]:
        ex = p["extract"]
        for f in l["facts"]:
            assert f in ex, (l["key"], f)
        miss = nums(l["story"]) - nums(ex)
        assert not miss, (l["key"], miss)              # every number in the story is in the article
        assert l["name"].split()[-1] in ex or l["name"] in ex
    else:
        assert l["name"].replace("Falcon Brook", "Falconbrook") in SUB, l["name"]     # listed in the overview article
    title = p["title"] if p else None
    co = (p.get("coordinates") or [{}])[0] if p else {}
    kmv = a.km_gl.sum()
    lost.append({"key": l["key"], "name": l["name"], "side": l["side"], "osm_names": sorted(a.name.unique().tolist()), "osm_keys": l["osm"],
                 "km": r2(kmv), "km_buried": r2(a.kb.sum()), "km_open": r2(a.ko.sum()), "pct_buried": pc(a.kb.sum(), kmv),
                 "mapped": int(kmv >= .1), "wiki": title, "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}" if title else None,
                 "lat": co.get("lat"), "lon": co.get("lon"), "story": l["story"], "famous": int(l["key"] in FAMOUS),
                 "boroughs": [BOROUGH_NAME.get(b, b) for b, v in sorted(sum((list(bor_of[k].items()) for k in l["osm"]), []), key=lambda kv: -kv[1]) if v >= .05][:5]})
R["lost"] = {x["key"]: x for x in lost}; R["lost_list"] = lost
LS = R["lost"]
mapped = [x for x in lost if x["mapped"]]
R["lost_sum"] = {"n": len(lost), "mapped": len(mapped), "unmapped": len(lost) - len(mapped), "unmapped_names": [x["name"] for x in lost if not x["mapped"]],
                 "km": r2(sum(x["km"] for x in mapped)), "km_buried": r2(sum(x["km_buried"] for x in mapped)),
                 "pct_buried": pc(sum(x["km_buried"] for x in mapped), sum(x["km"] for x in mapped)),
                 "pct_of_gl_buried": pc(sum(x["km_buried"] for x in mapped), kb)}
big3 = ["fleet", "tyburn", "westbourne"]
R["lost_sum"]["big3_km"] = r2(sum(LS[k]["km"] for k in big3)); R["lost_sum"]["big3_buried"] = r2(sum(LS[k]["km_buried"] for k in big3))
R["lost_sum"]["big3_pct"] = pc(R["lost_sum"]["big3_buried"], R["lost_sum"]["big3_km"])
assert set(R["lost_sum"]["unmapped_names"]) == {"Hackney Brook", "River Peck", "Earl's Sluice", "Stamford Brook", "Falcon Brook"}, R["lost_sum"]["unmapped_names"]
assert LS["tyburn"]["pct_buried"] == 100 and LS["effra"]["km"] < .5 and LS["counters creek"]["km_buried"] == 0
pd.DataFrame(lost).drop(columns=["osm_keys"]).assign(osm_names=lambda d: d.osm_names.map(";".join), boroughs=lambda d: d.boroughs.map(";".join)).to_csv(f"{DATA}/lost_rivers.csv", index=False)

# dates and figures quoted in the text, each checked against its article
X = {k: page(t)["extract"] for k, t in (("fleet", "River Fleet"), ("tyburn", "River Tyburn"), ("westbourne", "River Westbourne"), ("effra", "River Effra"),
                                         ("neckinger", "River Neckinger"), ("counters", "Counter's Creek"), ("hackney", "Hackney Brook"), ("moselle", "Moselle Brook"),
                                         ("peck", "River Peck"), ("stamford", "Stamford Brook"), ("quaggy", "Quaggy River"))}
Y = {"fleet_canal": ("fleet", 1680, "completed in 1680"), "fleet_market": ("fleet", 1737, "from 1737 enclosed"), "fleet_bridge": ("fleet", 1769, "covered by 1769"),
     "fleet_camden": ("fleet", 1812, "from 1812"), "fleet_last": ("fleet", "1870s", "expanded in the 1870s"), "fleet_pope": ("fleet", 1728, "In 1728 Alexander Pope"),
     "fleet_miles": ("fleet", 4, "4 miles (6 km)"),
     "tyburn_km": ("tyburn", 11, "7-mile (11 km)"), "tyburn_sewer0": ("tyburn", 1848, "between 1848 and 1856"), "tyburn_sewer1": ("tyburn", 1856, "between 1848 and 1856"),
     "west_serp": ("westbourne", 1730, "formed in 1730"), "west_stop": ("westbourne", 1834, "Serpentine in 1834"), "west_bomb": ("westbourne", 1940, "November 1940"),
     "effra_sewer": ("effra", 1821, "by 1821"), "effra_basin": ("effra", 20, "around 20 square kilometres"), "effra_arch": ("effra", 1847, "In 1847"), "effra_flood": ("effra", 1914, "14 June 1914"), "effra_campaign": ("effra", 1992, "In 1992 a project"),
     "neck_km": ("neckinger", "2.5", "approximately 2.5 kilometres"), "neck_dickens": ("neckinger", 1838, "Charles Dickens in 1838"), "neck_chron": ("neckinger", 1849, "Morning Chronicle in 1849"),
     "count_canal": ("counters", 1824, "In 1824–8"), "count_rail0": ("counters", 1859, "1859–63"),
     "hack_sewer": ("hackney", 1860, "sewer in 1860"), "hack_m": ("hackney", 10, "10 metres wide"), "hack_axes": ("hackney", "200,000", "200,000-year-old"),
     "mos_cover": ("moselle", 1836, "in 1836"), "mos_more": ("moselle", 1906, "in 1906"), "peck": ("peck", 1823, "enclosed in 1823"), "stam": ("stamford", 1900, "By 1900"),
     "quag_concrete": ("quaggy", "1960s", "In the 1960s"), "quag_restored": ("quaggy", 2002, "1 October 2002")}
R["wiki"] = {}
# Bazalgette and the sewers: every claim the page, blog and paper make is stated in these articles
for art, phrase in (("hackney", "Metropolitan Board of Works constructed its northern high-level sewer in 1860 to a design by Sir Joseph Bazalgette"),
                    ("effra", "Bazalgette incorporated flows from the River Effra into the southern division"), ("effra", "Crossness"),
                    ("fleet", "Joseph Bazalgette's London sewer system"), ("fleet", "Beckton"), ("tyburn", "Bazalgette's west-to-east Interceptor sewers"),
                    ("westbourne", "Joseph Bazalgette-designed Northern Low Level Sewer")):
    assert phrase in X[art], (art, phrase)
for k, (art, v, phrase) in Y.items():
    assert phrase in X[art], (k, phrase)
    R["wiki"][k] = v

# ---------- boroughs ----------
# The Thames is left out of the borough figures: it is the boundary between boroughs along most of its course, and
# the generalised Natural Earth outlines put its centre line on one bank or the other more or less at random.
bo = defaultdict(lambda: [0.0, 0.0])
for r in G[G.key != "thames"].itertuples():
    for b, v in r.bkm.items():
        bo[b][0] += v; bo[b][1] += v * r.buried
BF = {f["properties"]["name"]: f["properties"] for f in LON["features"]}
br = []
for b, p in BF.items():
    t, u = bo[b]
    br.append({"borough": b, "label": p["label"], "inner": p["inner"], "area_km2": p["area_km2"], "km": r2(t), "km_buried": r2(u), "km_open": r2(t - u),
               "pct_buried": pc(u, t), "buried_m_per_km2": round(1000 * u / p["area_km2"]), "km_per_km2": round(t / p["area_km2"], 3)})
BR = pd.DataFrame(br).sort_values("km_buried", ascending=False)
BR.to_csv(f"{DATA}/boroughs.csv", index=False)
R["boroughs"] = {r["borough"]: r for r in br}
R["bor_by_km"] = [{"b": r.borough, "label": r.label, "km_buried": r.km_buried, "pct": r.pct_buried, "inner": r.inner} for r in BR.itertuples()]
R["bor_by_pct"] = [{"b": r.borough, "label": r.label, "km_buried": r.km_buried, "pct": r.pct_buried, "inner": r.inner, "km": r.km} for r in BR.sort_values("pct_buried", ascending=False).itertuples()]
for nmk, flag in (("inner", 1), ("outer", 0)):
    a = BR[BR.inner == flag]
    R[nmk] = {"n": len(a), "km": r2(a.km.sum()), "km_buried": r2(a.km_buried.sum()), "pct_buried": pc(a.km_buried.sum(), a.km.sum()), "area_km2": r2(a.area_km2.sum()),
              "km_per_km2": round(a.km.sum() / a.area_km2.sum(), 3), "buried_m_per_km2": round(1000 * a.km_buried.sum() / a.area_km2.sum())}
R["inner"]["x_share"] = round(R["inner"]["pct_buried"] / R["outer"]["pct_buried"], 1)
R["inner"]["x_density"] = round(R["inner"]["buried_m_per_km2"] / R["outer"]["buried_m_per_km2"], 1)
assert R["inner"]["pct_buried"] > R["outer"]["pct_buried"] and R["inner"]["n"] == 13
top_pct = R["bor_by_pct"]
assert all(r["inner"] for r in top_pct[:3]), [r["b"] for r in top_pct[:5]]
R["bor_top"] = {"km1": R["bor_by_km"][0], "km2": R["bor_by_km"][1], "km3": R["bor_by_km"][2], "pct1": top_pct[0], "pct2": top_pct[1], "pct3": top_pct[2],
                "least": top_pct[-1], "n_over_half": sum(1 for r in top_pct if r["pct"] > 50), "n_under_10": sum(1 for r in top_pct if r["pct"] < 10)}

R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG, "title": TITLE, "paper_title": PAPER_TITLE}

# ---------- clean data out (OSM derived, ODbL): ways clipped to Greater London ----------
from shapely.geometry import shape
GLs = shape(LON["london"])
feats = []
for r in G.itertuples():
    ln = LineString(r.coords)
    g = ln if r.inside == 2 else ln.intersection(GLs)
    if g.is_empty: continue
    g = g.simplify(.00002)
    m = mapping(g)
    def rr(c): return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], float) else [rr(x) for x in c]
    if m["type"] == "GeometryCollection": continue
    feats.append({"type": "Feature", "properties": {"osm_id": int(r.osm_id), "name": r.name or None, "river": DISP.get(r.key) if r.key else None,
                  "waterway": r.type, "buried": int(r.buried), "tunnel": r.tunnel or None, "layer": r.layer or None, "km_in_london": round(r.km_gl, 4),
                  "boroughs": ";".join(BOROUGH_NAME.get(b, b) for b in r.bkm) or None}, "geometry": {"type": m["type"], "coordinates": rr(m["coordinates"])}})
jsave({"type": "FeatureCollection", "license": "ODbL 1.0, (c) OpenStreetMap contributors", "features": feats}, f"{DATA}/waterways_greater_london.geojson")

# ---------- page data ----------
jsave({k: WP[k] for k in ("cols", "types", "rivers", "rows")}, f"{DATA}/waterways.json")
rinfo = {r["key"]: [r["km"], r["km_open"], r["km_buried"], r["pct_buried"], r["boroughs"][:3]] for r in rv}
site = {"rivers": rinfo, "lost": lost, "famous": FAMOUS, "lost_by_osm": LOST_BY_OSM, "types": TYPES}
jsave(site, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
sz = {k: os.path.getsize(f"{DATA}/{k}") // 1024 for k in os.listdir(DATA)}
assert max(sz.values()) < 10 * 1024, sz
print("sizes KB", sz)
print(R["gl"]); print([(t["type"], t["km"], t["pct_buried"]) for t in ty])
print("by share", [(r["name"], r["km"], r["pct"]) for r in R["rank"]["by_share"]])
print("by km", [(r["name"], r["km_buried"]) for r in R["rank"]["by_km"][:8]])
print("lost", [(x["name"], x["km"], x["pct_buried"]) for x in lost]); print(R["lost_sum"])
print("inner", R["inner"], "outer", R["outer"])
print("bor km", [(r["b"], r["km_buried"], r["pct"]) for r in R["bor_by_km"][:6]]); print("bor pct", [(r["b"], r["pct"]) for r in top_pct[:6]], top_pct[-1])
print(R["sub"]["north_n"], R["sub"]["south_n"], R["rank"]["n_big"], R["rank"]["n_big_over_half"], R["rank"]["n_big_all"], R["rank"]["n_big_none"])
