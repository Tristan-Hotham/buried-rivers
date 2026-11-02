# London's buried rivers: what still flows in the open, and what runs underground

A map and analysis of every river, stream, canal, drain and ditch that OpenStreetMap records inside Greater London, split into open water and the parts that run in culverts, pipes and tunnels, with the stories of the lost rivers (the Fleet, Tyburn, Westbourne, Effra, Walbrook, Neckinger, Counter's Creek, Hackney Brook, Moselle and more) from their Wikipedia articles.

Interactive page: https://maps.tristanhotham.com/buried-rivers/
Paper: https://doi.org/10.5281/zenodo.23873535
Blog post: https://blog.tristanhotham.com/2026/10/31/buried-rivers/

## Headline results

- Greater London: 1,297 km of mapped waterway, 228 km (17.6%) buried, about one kilometre in 6. Without the Thames (75 km, open), 18.6%.
- By type: streams and brooks 30% buried (67% of all buried length); rivers 8.6%; canals 6.0%; drains 15%; ditches 9%.
- Rivers: of 79 named waterways with at least 3 km mapped, 21 are more than half buried. The Tyburn is buried for all 12.1 km; the Westbourne 99%, the Fleet 93%. Longest buried: Moselle Brook 15.7 km, Westbourne 12.5, Tyburn 12.1, Fleet 10.6.
- Boroughs (Thames excluded): inner London 37% buried, outer London 16%. City of London 100%, Westminster 74%, Camden 73%; most buried length Haringey (34.1 km).
- Coverage: of 17 lost rivers checked, 5 (Hackney Brook, River Peck, Earl's Sluice, Stamford Brook, Falcon Brook) are not mapped as waterways in OpenStreetMap, and the Effra is only a 0.13 km fragment. The buried totals are a lower bound.

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

- Waterways: OSM ways tagged waterway=river, stream, canal, drain or ditch in the box 51.28,-0.52,51.70,0.34 (8,439 ways), via the Overpass API in 2026.
- Buried: tunnel=culvert, yes, covered, pipe or building_passage; covered=yes; location=underground; or a negative layer without tunnel=no. Everything else is open.
- Length: haversine length after clipping each way to Greater London and to each borough. 17 unnamed river ways (19.5 km) drawn as extra channel lines beside the Thames are left out.
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

Hotham, T. (2026) London's buried rivers: open and culverted waterways in OpenStreetMap, and the lost rivers beneath the city. Zenodo. https://doi.org/10.5281/zenodo.23873535

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
