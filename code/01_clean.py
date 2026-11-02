"""Read the OpenStreetMap waterways, classify every way as open or buried, and group the named ways into rivers.

Buried: common.buried() (tunnel=culvert|yes|covered|pipe|building_passage, covered=yes, location=underground, or a
negative layer without tunnel=no). Everything else counts as open water. A river is the set of ways whose names share
common.river_key() ('River Fleet' and 'The Fleet' are one river). Unnamed ways are kept: they are most of the drains and
ditches. Lengths are computed after clipping to Greater London in 02_geo.py."""
import pandas as pd
from collections import Counter
from common import *

raw = jload(f"{RAW}/london_waterways_osm.json")
J = json.loads(raw["waterways"]) if isinstance(raw["waterways"], str) else raw["waterways"]
E = J["elements"]
chk = {"elements": len(E), "endpoint": raw.get("ep"), "osm_base": J["osm3s"]["timestamp_osm_base"], "copyright": J["osm3s"]["copyright"]}
assert chk["osm_base"].startswith(OSM_YEAR) and "ODbL" in chk["copyright"]
assert len(E) == 8439 and all(e["type"] == "way" for e in E)
chk["types"] = dict(Counter(e["tags"]["waterway"] for e in E))
chk["tunnel_tags"] = dict(Counter(e["tags"].get("tunnel", "(none)") for e in E))
chk["tunnel_or_neglayer"] = sum(1 for e in E if "tunnel" in e["tags"] or e["tags"].get("layer", "0").startswith("-"))
assert chk["tunnel_or_neglayer"] == 2382, chk["tunnel_or_neglayer"]

rows = []
for e in E:
    t = e["tags"]; g = e["geometry"]
    co = [(round(p["lon"], 7), round(p["lat"], 7)) for p in g]
    if len(co) < 2:
        continue
    nm = t.get("name", "")
    rows.append({"osm_id": e["id"], "name": nm, "key": river_key(nm), "type": t["waterway"], "buried": buried(t),
                 "tunnel": t.get("tunnel", ""), "layer": t.get("layer", ""), "covered": t.get("covered", ""), "location": t.get("location", ""),
                 "alt_name": t.get("alt_name", ""), "wikipedia": t.get("wikipedia", ""), "coords": co, "km_all": line_km(co)})
W = pd.DataFrame(rows)
chk["ways"] = len(W); chk["buried_ways"] = int(W.buried.sum()); chk["named_ways"] = int((W.name != "").sum())
chk["km_bbox"] = round(float(W.km_all.sum()), 2); chk["km_bbox_buried"] = round(float(W[W.buried == 1].km_all.sum()), 2)
chk["rule"] = dict(Counter((r.tunnel or "-", "neg" if r.layer.startswith("-") else (r.layer or "-"), r.covered or "-", r.buried) for r in W.itertuples()).most_common())
chk["rule"] = {"|".join(map(str, k)): v for k, v in chk["rule"].items()}
for l in LOST:
    for k in l["osm"]:
        assert (W.key == k).any(), (l["key"], k)
W.to_pickle(f"{WORK}/ways.pkl")
jsave(chk, f"{WORK}/checks.json", indent=1)
print("ways", len(W), "buried", chk["buried_ways"], "km in box", chk["km_bbox"], "buried km", chk["km_bbox_buried"], "named rivers", W[W.key != ""].key.nunique())
