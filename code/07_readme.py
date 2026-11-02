"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json. 10.5281/zenodo.23873535 and https://blog.tristanhotham.com/2026/10/31/buried-rivers/ stay as
placeholders for the publisher."""
from common import *

R = jload(f"{DATA}/results.json")
g, t, ls, rk, s = R["gl"], R["types"], R["lost"], R["rank"], R["source"]
N = lambda v: f"{round(v):,}"
readme = f"""# London's buried rivers: what still flows in the open, and what runs underground

A map and analysis of every river, stream, canal, drain and ditch that OpenStreetMap records inside Greater London, split into open water and the parts that run in culverts, pipes and tunnels, with the stories of the lost rivers (the Fleet, Tyburn, Westbourne, Effra, Walbrook, Neckinger, Counter's Creek, Hackney Brook, Moselle and more) from their Wikipedia articles.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Greater London: {N(g['km'])} km of mapped waterway, {N(g['km_buried'])} km ({g['pct_buried']:.1f}%) buried, about one kilometre in {g['one_in']}. Without the Thames ({N(g['thames_km'])} km, open), {g['pct_ex_thames']:.1f}%.
- By type: streams and brooks {t['stream']['pct_buried']:.0f}% buried ({t['stream']['share_of_buried_pct']:.0f}% of all buried length); rivers {t['river']['pct_buried']:.1f}%; canals {t['canal']['pct_buried']:.1f}%; drains {t['drain']['pct_buried']:.0f}%; ditches {t['ditch']['pct_buried']:.0f}%.
- Rivers: of {rk['n_big']} named waterways with at least {rk['min_km']:.0f} km mapped, {rk['n_big_over_half']} are more than half buried. The Tyburn is buried for all {ls['tyburn']['km']:.1f} km; the Westbourne {ls['westbourne']['pct_buried']:.0f}%, the Fleet {ls['fleet']['pct_buried']:.0f}%. Longest buried: Moselle Brook {ls['moselle']['km_buried']:.1f} km, Westbourne {ls['westbourne']['km_buried']:.1f}, Tyburn {ls['tyburn']['km_buried']:.1f}, Fleet {ls['fleet']['km_buried']:.1f}.
- Boroughs (Thames excluded): inner London {R['inner']['pct_buried']:.0f}% buried, outer London {R['outer']['pct_buried']:.0f}%. City of London 100%, Westminster {R['boroughs']['Westminster']['pct_buried']:.0f}%, Camden {R['boroughs']['Camden']['pct_buried']:.0f}%; most buried length Haringey ({R['boroughs']['Haringey']['km_buried']:.1f} km).
- Coverage: of {R['lost_sum']['n']} lost rivers checked, {R['lost_sum']['unmapped']} ({', '.join(R['lost_sum']['unmapped_names'])}) are not mapped as waterways in OpenStreetMap, and the Effra is only a {ls['effra']['km']:.2f} km fragment. The buried totals are a lower bound.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/waterways.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/waterways_greater_london.geojson` | Every OSM waterway way inside Greater London, clipped to the boundary: OSM id, name, river group, type, buried flag, tunnel and layer tags, km inside London, boroughs. ODbL. |
| `data/rivers.csv` | Every named river group in Greater London: km, km open, km buried, share buried, ways, types, main boroughs, lost river link. ODbL. |
| `data/lost_rivers.csv` | The lost rivers: OSM names matched, km mapped, share buried, Wikipedia article, coordinates and a short story (CC BY-SA 4.0). |
| `data/boroughs.csv` | Per borough (Thames excluded): area, km, km buried, share, metres buried per km2, inner or outer. |
| `data/waterways_by_type.csv` | km open and buried by OSM waterway type. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/waterways.json`, `data/london.json`, `data/land.json` | Page data (waterways.json holds every way in the download box, simplified, with delta encoded coordinates). |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Waterways: OSM ways tagged waterway=river, stream, canal, drain or ditch in the box 51.28,-0.52,51.70,0.34 ({N(s['ways_box'])} ways), via the Overpass API in {s['osm_year']}.
- Buried: tunnel=culvert, yes, covered, pipe or building_passage; covered=yes; location=underground; or a negative layer without tunnel=no. Everything else is open.
- Length: haversine length after clipping each way to Greater London and to each borough. {s['thames_dups']} unnamed river ways ({s['thames_dups_km']:.1f} km) drawn as extra channel lines beside the Thames are left out.
- Rivers: ways grouped by normalised name ("River Fleet" = "The Fleet"). Lost rivers matched by hand (Counter's Creek = Chelsea Creek; Graveney = River Graveney + Norbury Brook).
- Boundaries: Natural Earth 1:10m admin-1 units with region "Greater London" (generalised); inner London as in the London Government Act 1963. The Thames is left out of borough figures.
- Caveats: OSM coverage of buried water is uneven and many lost rivers survive only as sewers that are not mapped as waterways; tagging varies; borough splits along boundary streams are approximate.

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs (not in the repository): `raw/london_waterways_osm.json` (Overpass output) and `raw/london_rivers_wiki.json` (Wikipedia API output); Natural Earth in `/home/claude/newdata/raw/geo/` (paths in `code/common.py`). Intermediate files go to `/dev/shm/buriedrivers/work` (set `BRTMP` to change). Steps 5 onwards need only `data/`.

```
python3 code/01_clean.py        # read OSM, classify open and buried, group by name
python3 code/02_geo.py          # boundary and boroughs, clip and measure, page geometry
python3 code/03_results.py      # results.json, data tables, page data, Wikipedia checks
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- OpenStreetMap, (c) OpenStreetMap contributors, Open Database Licence 1.0 (https://www.openstreetmap.org/copyright). The OSM derived data in `data/` are released under the ODbL.
- English Wikipedia, "Subterranean rivers of London" and the river articles, CC BY-SA 4.0. The river stories in `data/` and on the page are summaries of those articles and are shared under CC BY-SA 4.0.
- Natural Earth admin-1 states and provinces, 1:10m. Public domain.
- Base map tiles on the page: (c) Esri.

## Citation

Hotham, T. (2026) London's buried rivers: open and culverted waterways in OpenStreetMap, and the lost rivers beneath the city. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/rocket-launches/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0, with these exceptions:
  * data derived from OpenStreetMap (waterways_greater_london.geojson,
    waterways.json, rivers.csv, the lengths in lost_rivers.csv, boroughs.csv,
    waterways_by_type.csv and results.json) are (c) OpenStreetMap contributors
    and released under the Open Database Licence 1.0,
    https://opendatacommons.org/licenses/odbl/1-0/ ;
  * the river stories derived from English Wikipedia (in lost_rivers.csv,
    site.json, results.json and on the page) are released under CC BY-SA 4.0.
Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] London's buried rivers: {N(g['km_buried'])} km of the city's mapped waterways run in culverts and tunnels. The Tyburn, which flows under Buckingham Palace, is 100% underground

## Body

I mapped every river, stream, canal, drain and ditch OpenStreetMap records inside Greater London ({N(g['km'])} km) and split it into what flows in the open and what is tagged as a culvert or tunnel: {g['pct_buried']:.1f}%, about one kilometre in {g['one_in']}. Small streams suffered most ({t['stream']['pct_buried']:.0f}% buried), while big rivers like the Thames, Lea and Wandle stayed mostly open. The famous lost rivers are almost wholly underground: the Tyburn {ls['tyburn']['pct_buried']:.0f}%, the Westbourne (which crosses Sloane Square tube station in a pipe) {ls['westbourne']['pct_buried']:.0f}%, the Fleet (of Fleet Street) {ls['fleet']['pct_buried']:.0f}%. The longest buried course is actually the Moselle Brook in Tottenham, {ls['moselle']['km_buried']:.1f} km. Leaving out the Thames, inner London has buried {R['inner']['pct_buried']:.0f}% of its waterways, outer London {R['outer']['pct_buried']:.0f}%. Caveat: OSM is a volunteer map, and {R['lost_sum']['unmapped']} lost rivers (Hackney Brook, the Peck, Earl's Sluice, Stamford Brook, Falcon Brook) now survive only as sewers and are not mapped as waterways at all, so the real buried total is higher. Interactive map with every river's story: {PAGE}

## Source comment

Source: OpenStreetMap waterways (waterway=river, stream, canal, drain, ditch), (c) OpenStreetMap contributors, ODbL, via the Overpass API. Buried = tunnel=culvert/yes/covered/pipe, covered=yes, location=underground or negative layer. Lengths are haversine lengths after clipping to Greater London (Natural Earth boroughs). River histories: English Wikipedia (CC BY-SA 4.0).

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for x in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in x.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
