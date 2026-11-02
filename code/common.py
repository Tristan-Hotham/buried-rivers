"""Shared paths, the lost river catalogue and helpers for the buried-rivers project.

Raw inputs (read in place, never modified; raw/ is not part of the release, everything the page, paper and zip need
is written to data/ by 01 to 03):
  raw/london_waterways_osm.json   {"waterways": <Overpass JSON as a string>, "ep": <endpoint>}. OpenStreetMap ways in the
                                  box 51.28,-0.52,51.70,0.34 with waterway=river|stream|canal|drain|ditch, with tags and
                                  geometry (lat/lon lists). OSM base timestamp 2026. (c) OpenStreetMap contributors, ODbL.
  raw/london_rivers_wiki.json     English Wikipedia API results per title (plain text extract, coordinates, current
                                  wikitext) for "Subterranean rivers of London" and about 35 river articles. CC BY-SA 4.0.
                                  "Falcon Brook", "Ching Brook", "Bounds Green Brook" and "Tyburn (village)" are missing;
                                  "Black Ditch" redirects to an unrelated article (dropped); "Norwood" and "Kidbrooke" are
                                  place articles (not used); "Walbrook" is the City ward article.
  /home/claude/newdata/raw/geo/ne_10m_admin_1_states_provinces.geojson   Natural Earth admin-1 (public domain): the 33
                                  units with region "Greater London" (32 boroughs and the City) give the borough outlines
                                  and, unioned, the Greater London boundary; the neighbouring GB units give the land
                                  around it for the page's own base map.
"""
import json, gzip, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("BR_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("BR_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("BR_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("BRTMP", "/dev/shm/buriedrivers"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "buried-rivers"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23873535"                # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/buried-rivers/"          # filled in by the publisher
TITLE = "London's buried rivers"
PAPER_TITLE = "London's Buried Rivers: Open and Culverted Waterways in OpenStreetMap, and the Lost Rivers Beneath the City"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
OSM_YEAR = "2026"              # OSM base timestamp (year only in public copy)
BBOX = (51.28, -0.52, 51.70, 0.34)   # south, west, north, east of the Overpass query

TYPES = ["river", "stream", "canal", "drain", "ditch"]
TYPE_NAME = {"river": "Rivers", "stream": "Streams and brooks", "canal": "Canals", "drain": "Drains", "ditch": "Ditches"}

# Inner London as defined by the London Government Act 1963 (the statutory definition): 12 boroughs and the City.
# Natural Earth names. (The ONS statistical definition swaps Greenwich for Haringey and Newham; the paper says so.)
INNER = ["City", "Camden", "Greenwich", "Hackney", "Hammersmith and Fulham", "Islington", "Kensington and Chelsea", "Lambeth",
         "Lewisham", "Southwark", "Tower Hamlets", "Wandsworth", "Westminster"]
BOROUGH_NAME = {"City": "City of London"}


def buried(t):
    """A way counts as buried (culverted, piped or otherwise underground) if OSM says location=underground, or
    tunnel=culvert|yes|covered|pipe|building_passage, or covered=yes, or it has a negative layer without tunnel=no."""
    if t.get("location") == "underground":
        return 1
    tu = t.get("tunnel")
    if tu in ("culvert", "yes", "covered", "pipe", "building_passage"):
        return 1
    if tu == "no":
        return 0
    if t.get("covered") == "yes":
        return 1
    try:
        return int(float(t.get("layer", "0").split(";")[0]) < 0)
    except ValueError:
        return 0


def river_key(name):
    """Group OSM ways into rivers by name: 'River Fleet' and 'The Fleet' -> 'fleet'; 'Hogsmill River' -> 'hogsmill'."""
    if not name:
        return ""
    k = norm(name)
    k = re.sub(r"^(river|the) ", "", k)
    k = re.sub(r" river$", "", k)
    return ALIAS.get(k, k)


ALIAS = {"moselle brook": "moselle", "ravensbourne": "ravensbourne"}

# The lost rivers: the streams that Wikipedia's "Subterranean rivers of London" lists as built over, and that its
# articles describe. osm = the OSM names (grouped by river_key) that belong to it; wiki = the article title in the raw
# file; facts = phrases checked against the article text in 03_results.py (the stories below paraphrase them).
LOST = [
    {"key": "fleet", "name": "River Fleet", "side": "N", "osm": ["fleet"], "wiki": "River Fleet",
     "story": "The largest of London's buried rivers. It rises in the Hampstead and Highgate ponds and gives its name to Fleet Street; its lower reaches, the Holbourne, gave Holborn its name. After the Great Fire it became the New Canal, finished in 1680 under Robert Hooke; it was covered over in stages from 1737 to the 1870s and now runs as a sewer. You can still hear it through a grating in Ray Street, Clerkenwell.",
     "facts": ["gives its name to Fleet Street", "from which Holborn derived its name", "completed in 1680 under the supervision of Robert Hooke",
               "from 1737 enclosed between Holborn and Ludgate Circus", "covered when Hampstead was expanded in the 1870s",
               "grating in Ray Street, Clerkenwell", "Joseph Bazalgette's London sewer system"]},
    {"key": "tyburn", "name": "River Tyburn", "side": "N", "osm": ["tyburn"], "wiki": "River Tyburn",
     "story": "Rises at the Shepherd's Well in Hampstead and runs in underground conduits for its whole length, including one beneath Buckingham Palace. Where it split near the Thames it made Thorney Island, on which Westminster Abbey was built. Marylebone Lane still bends along its old bank, and the Tyburn gave its name to the gallows at the end of Oxford Street.",
     "facts": ["including one beneath Buckingham Palace", "creating Thorney Island on which Westminster Abbey was built",
               "Its main source was the Shepherd's Well", "Tyburn Gallows", "Kings Scholars Pond Sewer was constructed between 1848 and 1856"]},
    {"key": "westbourne", "name": "River Westbourne", "side": "N", "osm": ["westbourne"], "wiki": "River Westbourne",
     "story": "Also called the Kilburn, it gave Bayswater its name. It was dammed in 1730 to make the Serpentine in Hyde Park, which it stopped feeding in 1834 once it had become a sewer. Its pipe still crosses above the platforms of Sloane Square tube station, and it survived the bombing of the station in 1940.",
     "facts": ["running above the platform of Sloane Square tube station", "The Serpentine was formed in 1730 by building a dam across the Westbourne",
               "ceased to provide the water for the Serpentine in 1834", "Bombing of London in November 1940 but the pipe was not damaged",
               "gave its name to the area now known as Bayswater"]},
    {"key": "effra", "name": "River Effra", "side": "S", "osm": ["effra"], "wiki": "River Effra",
     "story": "Rises in Upper Norwood and runs under Brixton. By 1821 it was an open sewer below North Brixton, and in 1847 it was arched over as far up as Herne Hill. Bazalgette folded it into his southern sewers. A local story holds that a coffin once fell from a Norwood grave into the buried river and floated to the Thames.",
     "facts": ["by 1821 it was classed as an open sewer", "In 1847 the commissioners of the Surrey and East Kent Sewers",
               "Sir Joseph Bazalgette incorporated flows from the River Effra", "the entire coffin had fallen into the underground Effra river"]},
    {"key": "walbrook", "name": "Walbrook", "side": "N", "osm": ["walbrook"], "wiki": "Walbrook",
     "story": "The City of London's own stream, now underground. The street called Walbrook follows its lower course, and the valley can still be seen where it meets Cannon Street. The Bank of England and Mansion House stand in the ward named after it.",
     "facts": ["The ward is named after a river of the same name", "A street called Walbrook runs along the lower part of the brook's course",
               "A valley is clearly visible", "the Bank of England and the Mansion House"]},
    {"key": "neckinger", "name": "River Neckinger", "side": "S", "osm": ["neckinger"], "wiki": "River Neckinger",
     "story": "A short stream from St George's Fields in Southwark to St Saviour's Dock. In 1838 Dickens called Jacob's Island, the district on its tidal ditches, the filthiest of the many places hidden in London, and in 1849 the Morning Chronicle called it the very capital of cholera. In Oliver Twist a branch of it is Folly Ditch.",
     "facts": ["flows approximately 2.5 kilometres", "Jacob's Island district", "described by Charles Dickens in 1838", "The very capital of cholera", "Folly Ditch"]},
    {"key": "counters creek", "name": "Counter's Creek", "side": "N", "osm": ["chelsea creek"], "wiki": "Counter's Creek",
     "story": "Flowed from Kensal Green past Earl's Court to the Thames at Sands End. Its lowest part was turned into the Kensington Canal from 1824, and much of the rest was culverted from 1859 to carry the West London Line. Stamford Bridge, home of Chelsea FC, is named after a bridge over it. Only its tidal mouth, Chelsea Creek, is still open.",
     "facts": ["Its remaining open watercourse is the quay of Chelsea Creek", "In 1824–8 the lowest part of the creek was developed into the Kensington Canal",
               "culverted to take the West London Line along its course in 1859–63", "Chelsea F.C. ground at Stamford Bridge"]},
    {"key": "hackney brook", "name": "Hackney Brook", "side": "N", "osm": [], "wiki": "Hackney Brook",
     "story": "Rose near Holloway Road and flowed through Stoke Newington and Hackney to the Lea at Old Ford. Until the late 1830s it was up to 10 metres wide at Stoke Newington. In 1860 Bazalgette's northern high level sewer swallowed it. Builders in the 1860s found flint axes about 200,000 years old on its banks.",
     "facts": ["10 metres wide in full flood at Stoke Newington", "constructed its northern high-level sewer in 1860", "200,000-year-old palaeolithic flint axes"]},
    {"key": "moselle", "name": "Moselle Brook", "side": "N", "osm": ["moselle"], "wiki": "Moselle Brook",
     "story": "Rises in Muswell Hill and Highgate and flows through Tottenham. Its stretch by Tottenham High Road and White Hart Lane was covered in 1836, and more culverting from 1906 left it enclosed all the way from Tottenham Cemetery to Pymmes Brook. Muswell Hill shares its name.",
     "facts": ["in 1836 the stretch around Tottenham High Road and White Hart Lane was covered", "More culverting occurred in 1906",
               "completely enclosed from Tottenham Cemetery"]},
    {"key": "peck", "name": "River Peck", "side": "S", "osm": [], "wiki": "River Peck",
     "story": "A small stream that gave Peckham its name, the homestead of the Peck. It was enclosed in 1823 and still comes to the surface on the west side of Peckham Rye Park before joining Earl's Sluice.",
     "facts": ["enclosed in 1823", "daylights on the west side of Peckham Rye Park", "homestead of the Peck"]},
    {"key": "earls sluice", "name": "Earl's Sluice", "side": "S", "osm": [], "wiki": "Earl's Sluice",
     "story": "Runs underground from Ruskin Park on Denmark Hill to the Thames at Deptford Wharf, along the old boundary between Kent and Surrey. Where it crossed the Old Kent Road, Chaucer's pilgrims watered their horses at St Thomas-a-Watering.",
     "facts": ["Its source is Ruskin Park on Denmark Hill", "the boundary between the historic counties of Kent and Surrey", "Canterbury Tales"]},
    {"key": "stamford brook", "name": "Stamford Brook", "side": "N", "osm": [], "wiki": "Stamford Brook",
     "story": "A web of small streams between Acton, Hammersmith and Chiswick. By 1900 all six strands had been covered over and turned into sewers. It gave its name to the district and to Stamford Brook tube station.",
     "facts": ["By 1900, all six strands of the brook and drainage dykes had been covered over", "the local London Underground station, Stamford Brook"]},
    {"key": "muswell stream", "name": "Muswell Stream", "side": "N", "osm": ["muswell stream"], "wiki": None,
     "story": "A headwater of Pymmes Brook below Muswell Hill, listed by Wikipedia among the subterranean rivers as a tributary of a tributary of the Lea. Every metre of it that OpenStreetMap maps is underground.",
     "facts": []},
    {"key": "falcon brook", "name": "Falcon Brook", "side": "S", "osm": [], "wiki": None,
     "story": "A south London stream, listed by Wikipedia as one of the subterranean rivers (as Falconbrook). It has no article of its own in the source and is not mapped as a waterway in OpenStreetMap.",
     "facts": []},
    {"key": "wogebourne", "name": "Wogebourne", "side": "S", "osm": ["wogebourne"], "wiki": None,
     "story": "A stream in south east London, listed by Wikipedia as one of the subterranean rivers. Part of it is still open and part runs in culverts.",
     "facts": []},
    {"key": "graveney", "name": "River Graveney", "side": "S", "osm": ["graveney", "norbury brook"], "wiki": "River Graveney",
     "story": "A tributary of the Wandle, with its upper course known as Norbury Brook. It runs partly in deep concrete channels; its tributary the Little Graveney Stream was culverted early in the twentieth century and can no longer be seen.",
     "facts": ["Little Graveney Stream", "culverted in the early 20th century and is no longer visible"]},
    {"key": "quaggy", "name": "River Quaggy", "side": "S", "osm": ["quaggy"], "wiki": "Quaggy River",
     "story": "Listed as partly underground. In the 1960s it was put into straight concrete channels to stop flooding; at Chinbrook Meadows the concrete was torn out and the river given back its meanders in 2002, a model for bringing London's rivers back to the surface.",
     "facts": ["In the 1960s the River Quaggy within Chinbrook Meadows", "The regeneration was completed on 1 October 2002"]},
]
LOST_KEYS = [l["key"] for l in LOST]
LOST_BY_OSM = {k: l["key"] for l in LOST for k in l["osm"]}
FAMOUS = ["fleet", "tyburn", "westbourne", "effra", "walbrook", "neckinger", "counters creek", "moselle", "muswell stream"]   # highlighted by the toggle


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower().replace("'", "").replace("’", "")
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    raise ValueError(f)


def hav_km(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2); dl = math.radians(lon2 - lon1)
    return 6371.0088 * 2 * math.asin(math.sqrt(math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))


def line_km(coords):
    """Haversine length of a lon/lat coordinate sequence, km."""
    return sum(hav_km(*coords[i], *coords[i + 1]) for i in range(len(coords) - 1))


def geom_km(g):
    """Length of a shapely (Multi)LineString / GeometryCollection in lon/lat, km."""
    if g.is_empty: return 0.0
    if g.geom_type == "LineString": return line_km(list(g.coords))
    if hasattr(g, "geoms"): return sum(geom_km(x) for x in g.geoms)
    return 0.0
