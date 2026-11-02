"""Geography. The Overpass fetch of the Greater London boundary failed, so the boundary and the borough outlines come from
Natural Earth admin-1 (1:10m): the 33 GB units whose region is "Greater London" (32 London boroughs and the City),
unioned for the boundary. Every OSM way is clipped to Greater London and to each borough, and its length inside is
measured with the haversine formula on the clipped coordinates. Also written: the land around London for the page's
own base map (the GB admin-1 units that touch the view), and simplified geometry for the page and figures.

Natural Earth outlines are generalised (to a few hundred metres), so a stream that runs along a borough boundary can
be split between the two boroughs somewhat arbitrarily; borough figures are approximate for that reason."""
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping, LineString, box
from shapely.ops import unary_union, transform
import warnings; warnings.filterwarnings("ignore", category=DeprecationWarning)
from shapely.strtree import STRtree
from shapely.prepared import prep
from pyproj import Transformer
from common import *

A1 = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")
GB = [f for f in A1["features"] if f["properties"].get("adm0_a3") == "GBR"]
LB = [f for f in GB if f["properties"].get("region") == "Greater London"]
assert len(LB) == 33, len(LB)
assert {f["properties"]["type_en"] for f in LB} <= {"London Borough", "London Borough (royal)", "London Borough (city)", "City Corporation"}
assert set(INNER) <= {f["properties"]["name"] for f in LB}
BNG = Transformer.from_crs(4326, 27700, always_xy=True).transform
bor = []
for f in LB:
    p = f["properties"]; g = shape(f["geometry"]).buffer(0)
    bor.append({"name": p["name"], "label": BOROUGH_NAME.get(p["name"], p["name"]), "inner": int(p["name"] in INNER), "geom": g,
                "area_km2": transform(BNG, g).area / 1e6, "code": p.get("code_hasc") or p.get("iso_3166_2")})
GL = unary_union([b["geom"] for b in bor]).buffer(0)
GLa = transform(BNG, GL).area / 1e6
assert GL.geom_type == "Polygon" or len(GL.geoms) <= 3, GL.geom_type
assert 1400 < GLa < 1700, GLa                      # Greater London is about 1,572 km2
west, south, east, north = GL.bounds
assert BBOX[0] <= south and north <= BBOX[2] and BBOX[1] <= west and east <= BBOX[3], GL.bounds   # the OSM box covers it

# ---- clip ways
W = pd.read_pickle(f"{WORK}/ways.pkl")
GLp = prep(GL); BT = STRtree([b["geom"] for b in bor])
km_gl, bkm, inside = [], [], []
for co in W.coords:
    ln = LineString(co)
    if GLp.contains(ln):
        k = line_km(co); km_gl.append(k); inside.append(2)
    elif GLp.intersects(ln):
        k = geom_km(ln.intersection(GL)); km_gl.append(k); inside.append(1)
    else:
        km_gl.append(0.0); inside.append(0); bkm.append({}); continue
    d = {}
    for i in BT.query(ln):
        g = bor[i]["geom"]
        kk = line_km(co) if g.contains(ln) else geom_km(ln.intersection(g))
        if kk > 0: d[bor[i]["name"]] = kk
    bkm.append(d)
W["km_gl"] = km_gl; W["inside"] = inside; W["bkm"] = bkm
# Unnamed ways tagged waterway=river that lie along the Thames (at least 90% of their length within 400 m of the Thames
# centre line) are parallel channel lines drawn beside the main line, around Barnes and elsewhere. They would count the
# Thames twice, so they are left out of every measure and of the page.
TH = unary_union([transform(BNG, LineString(c)) for c in W[W.key == "thames"].coords]).buffer(400)
def along(c):
    g = transform(BNG, LineString(c)); return g.intersection(TH).length / g.length if g.length else 0
W["dup"] = [int(r.key == "" and r.type == "river" and along(r.coords) >= .9) for r in W.itertuples()]
CHK = jload(f"{WORK}/checks.json")
CHK["thames_dups"] = int(W.dup.sum()); CHK["thames_dups_km_gl"] = round(float(W[W.dup == 1].km_gl.sum()), 2)
jsave(CHK, f"{WORK}/checks.json", indent=1)
W.loc[W.dup == 1, "inside"] = 0; W.loc[W.dup == 1, "km_gl"] = 0.0
W["bkm"] = [{} if d else b for d, b in zip(W.dup, W.bkm)]
# borough pieces should add up to the Greater London length (boundaries shared, so tiny overlaps only)
tot_b = sum(sum(d.values()) for d in W.bkm)
assert abs(tot_b - W.km_gl.sum()) < .001 * W.km_gl.sum(), (tot_b, W.km_gl.sum())
W.to_pickle(f"{WORK}/ways_gl.pkl")


def rnd(c, k=5):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


def gj(g, tol, k=5):
    s = g.simplify(tol, preserve_topology=True); m = mapping(s)
    return {"type": m["type"], "coordinates": rnd(m["coordinates"], k)}


# ---- outlines for the page and figures
feats = [{"type": "Feature", "properties": {"name": b["name"], "label": b["label"], "inner": b["inner"], "area_km2": round(b["area_km2"], 1),
          "lx": round(b["geom"].representative_point().x, 4), "ly": round(b["geom"].representative_point().y, 4)}, "geometry": gj(b["geom"], .0004)} for b in bor]
inner = unary_union([b["geom"] for b in bor if b["inner"]]).buffer(0)
jsave({"type": "FeatureCollection", "features": feats,
       "london": gj(GL, .0004), "inner": gj(inner, .0004), "area_km2": round(GLa, 1)}, f"{DATA}/london.json")
VIEW = box(BBOX[1] - .25, BBOX[0] - .15, BBOX[3] + .25, BBOX[2] + .15)
ctx = [shape(f["geometry"]).buffer(0) for f in GB if shape(f["geometry"]).intersects(VIEW)]
land = unary_union(ctx).intersection(VIEW)
jsave({"type": "Feature", "properties": {}, "geometry": gj(land, .001, 4)}, f"{DATA}/land.json")

# ---- page ways: every way in the OSM box, simplified (about 3 m); flag 1 = inside Greater London (wholly or partly)
keys = sorted(k for k in W.key.unique() if k)
KI = {k: i for i, k in enumerate(keys)}
names = {}
for r in W[W.key != ""].itertuples():
    names.setdefault(r.key, []).append(r.name)
disp = {k: max(set(v), key=lambda n: (v.count(n), n.startswith("River"))) for k, v in names.items()}
for l in LOST:
    for k in l["osm"]:
        disp[k] = l["name"] if len(l["osm"]) == 1 else disp[k]
rows = []
for r in W[W.dup == 0].itertuples():
    s = LineString(r.coords).simplify(.00003)
    c = np.round(np.array(s.coords) * 1e5).astype(int)
    flat = [int(c[0, 0]), int(c[0, 1])] + np.diff(c, axis=0).ravel().astype(int).tolist()
    rows.append([KI.get(r.key, -1), TYPES.index(r.type), int(r.buried), int(r.inside > 0), round(r.km_gl, 3), flat])
jsave({"cols": ["river", "type", "buried", "in_london", "km_in_london", "coords_delta_1e5"], "types": TYPES,
       "rivers": [[k, disp[k]] for k in keys], "rows": rows}, f"{WORK}/ways_page.json")
print("boroughs", len(bor), "GL area", round(GLa), "km2; ways in GL", int((W.inside > 0).sum()), "km in GL", round(W.km_gl.sum(), 1),
      "buried", round(W[W.buried == 1].km_gl.sum(), 1), "| london.json", os.path.getsize(f"{DATA}/london.json") // 1024, "KB; land.json",
      os.path.getsize(f"{DATA}/land.json") // 1024, "KB; page ways", os.path.getsize(f"{WORK}/ways_page.json") // 1024, "KB")
