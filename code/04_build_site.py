"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, london.json, land.json) is embedded; data/waterways.json is loaded
by the page. Facts stated in words are checked here. The full-screen map snippet (code/fullscreen_snippet.html) is
pasted before </body>. 10.5281/zenodo.23873535 and https://blog.tristanhotham.com/2026/10/31/buried-rivers/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
GL, T, LS, B, RK = R["gl"], R["types"], R["lost"], R["boroughs"], R["rank"]

# facts stated in words (page, blog, paper, collage)
assert 15 < GL["pct_buried"] < 20 and GL["one_in"] == 6                          # "about one kilometre in six"
assert R["rivers"]["thames"]["km_buried"] < .01                                   # "almost none of the Thames is buried"
assert max(R["types_list"], key=lambda t: t["pct_buried"])["type"] == "stream"     # "the small streams have suffered most"
assert all(R["big_rivers"][k]["pct"] < 20 for k in ("thames", "lea", "wandle", "brent"))   # "still run under the sky for most of their course"
assert T["canal"]["pct_buried"] < T["river"]["pct_buried"] < T["drain"]["pct_buried"] < T["stream"]["pct_buried"]
assert LS["tyburn"]["pct_buried"] == 100 and LS["tyburn"]["km"] > 10                 # "every metre"
assert RK["by_km"][0]["key"] == "moselle"                                            # "the leader is the Moselle Brook"
for k, b in (("stonebridge brook", "Haringey"), ("cholmeley brook", "Haringey"), ("mutton brook", "Barnet"), ("saddlers mill stream", "Enfield"), ("cran brook", "Redbridge"),
             ("moselle", "Haringey"), ("muswell stream", "Haringey")):
    assert R["rivers"][k]["boroughs"][0] == b, (k, R["rivers"][k]["boroughs"])
assert R["rivers"]["stonebridge brook"]["pct_buried"] > 99 and R["rivers"]["cholmeley brook"]["pct_buried"] > 99
assert [r["b"] for r in R["bor_by_km"][:3]] == ["Haringey", "Bromley", "Greenwich"]
assert [r["b"] for r in R["bor_by_pct"][:3]] == ["City", "Westminster", "Camden"] and R["bor_by_pct"][-1]["b"] == "Hackney"
assert B["City"]["pct_buried"] == 100
assert 2 <= R["inner"]["x_share"] < 2.5                                               # "twice as often"
assert R["inner"]["n"] == 13 and R["outer"]["n"] == 20 and R["source"]["boroughs"] == 33
assert set(R["lost_sum"]["unmapped_names"]) == {"Hackney Brook", "River Peck", "Earl's Sluice", "Stamford Brook", "Falcon Brook"}
assert LS["counters creek"]["osm_names"] == ["Chelsea Creek"] and LS["counters creek"]["km_buried"] == 0
assert LS["fleet"]["km_open"] < 1                                                    # "the open part being the ponds and streams on Hampstead Heath"
assert R["sub"]["n"] == R["sub"]["north_n"] + R["sub"]["south_n"]
assert R["lost"]["quaggy"]["km_open"] > R["lost"]["quaggy"]["km_buried"]
assert sum(1 for l in R["lost_list"] if l["key"] in ("fleet", "tyburn", "westbourne", "effra", "walbrook", "neckinger", "counters creek", "hackney brook", "moselle", "peck")) == 10   # "Ten stories"


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23873535", "https://blog.tristanhotham.com/2026/10/31/buried-rivers/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*LONDON*/", open(f"{DATA}/london.json", encoding="utf-8").read())
    html = html.replace("/*LAND*/", open(f"{DATA}/land.json", encoding="utf-8").read())
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
