"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23873535, https://doi.org/10.5281/zenodo.23873535 and https://blog.tristanhotham.com/2026/10/31/buried-rivers/ stay as placeholders for the publisher. Needs only code/, data/ and release/
(raw/ may be absent)."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_London_Buried_Rivers"

# the page build checks the shared facts; these are numbers written in words or in alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
T, LS, B = R["types"], R["lost"], R["boroughs"]
assert [round(T[k]["km"]) for k in ("river", "stream", "canal", "drain", "ditch")] == [415, 510, 130, 146, 95]
assert [round(T[k]["pct_buried"]) for k in ("river", "stream", "canal", "drain", "ditch")] == [9, 30, 6, 15, 9]
assert [r["name"] for r in R["rank"]["by_share"][:4]] == ["River Tyburn", "Muswell Stream", "Cholmeley Brook", "Stonebridge Brook"]
assert [round(r["pct"]) for r in R["rank"]["by_share"][4:8]] == [99, 94, 93, 91]
assert [round(r["km_buried"], 1) for r in R["rank"]["by_km"][:5]] == [15.7, 12.5, 12.1, 10.6, 6.2]
assert [round(B[b]["pct_buried"]) for b in ("Westminster", "Camden", "Haringey", "Lambeth", "Greenwich", "Hackney")] == [74, 73, 62, 51, 45, 1]
assert [round(LS[k]["km"], 1) for k in ("moselle", "westbourne", "tyburn", "fleet", "quaggy", "graveney", "wogebourne", "muswell stream", "neckinger", "walbrook", "counters creek", "effra")] == \
       [17.3, 12.6, 12.1, 11.5, 8.8, 8.7, 7.2, 4.2, 3.4, 1.9, 0.5, 0.1]
assert R["rivers"]["lea"]["pct_buried"] < 5 and R["rivers"]["wandle"]["pct_buried"] < 20       # "Thames, Lea and Wandle stayed mostly open"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23873535"}
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
g = R["gl"]
meta = {"title": "London's buried rivers: what still flows in the open, and what runs in the dark",
        "slug": "buried-rivers",
        "excerpt": f"I mapped every waterway OpenStreetMap records in Greater London. {g['km_buried']:,.0f} km of it, about one kilometre in {g['one_in']}, runs in culverts and tunnels, and the Fleet, Tyburn and Westbourne are {R['lost_sum']['big3_pct']:.0f}% underground.",
        "seo_description": f"A map of London's buried rivers: {g['km_buried']:,.0f} km of culverts under the city, the Fleet, Tyburn and Westbourne, and the rivers lost to the sewers.",
        "tags": ["London", "lost rivers", "rivers", "maps", "data visualisation", "OpenStreetMap", "history", "sewers"],
        "header_alt": f"Title card reading 'London's buried rivers' in black, blue and red on pale paper, beside a map of central London where the Westbourne, Tyburn and Fleet run down to the Thames as red dashed lines glowing gold. Text: {g['km_buried']:,.0f} km of London's waterways run in culverts and tunnels; the Fleet, Tyburn and Westbourne are {R['lost_sum']['big3_pct']:.0f}% underground."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/buried-rivers_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"buried-rivers/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"buried-rivers/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "buried-rivers/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("``", "\"").replace("''", "\"")
zmeta = {"title": PAPER_TITLE,
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Waterway data (c) OpenStreetMap contributors, ODbL 1.0; the derived data are also ODbL. River histories from English Wikipedia, CC BY-SA 4.0. Boundaries: Natural Earth (public domain).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["London", "lost rivers", "subterranean rivers", "culverts", "urban streams", "OpenStreetMap", "volunteered geographic information", "sewers", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "notes": "Code: MIT. Text and figures: CC BY 4.0. OpenStreetMap derived data: ODbL 1.0. Wikipedia derived river stories: CC BY-SA 4.0.",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.openstreetmap.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://en.wikipedia.org/wiki/Subterranean_rivers_of_London", "relation": "references", "resource_type": "other"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
