"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, and London geometry (waterways, boroughs, boundary) in British National Grid metres,
all read from data/ so that figures can be redrawn without raw/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
from matplotlib.collections import LineCollection, PatchCollection
import matplotlib.patheffects as pe
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72"})
BG, FG, MUT, LAND, RULE, LDN = "#F6F4EF", "#1D2128", "#636A72", "#E9E5DB", "#DDD8CC", "#F3F0E8"
WATER, THAMES, BUR, LOSTC, INNERC, OUTERC, NAVY = "#2A74B0", "#A9CBE6", "#C2412D", "#D3901A", "#7A4E9C", "#8C8478", "#1F2F4D"
HALO = [pe.withStroke(linewidth=3.2, foreground=BG)]

BNG = Transformer.from_crs(4326, 27700, always_xy=True)
WJ = jload(f"{DATA}/waterways.json")
LON = jload(f"{DATA}/london.json")
RKEYS = [k for k, _ in WJ["rivers"]]
RNAME = dict(WJ["rivers"])


def decode(flat):
    c = np.array(flat, dtype=float).reshape(-1, 2)
    c = np.cumsum(c, axis=0) / 1e5
    x, y = BNG.transform(c[:, 0], c[:, 1])
    return np.column_stack([x, y])


WAYS = []   # (river key, type, buried, in_london, km, xy)
for r in WJ["rows"]:
    WAYS.append((RKEYS[r[0]] if r[0] >= 0 else "", WJ["types"][r[1]], r[2], r[3], r[4], decode(r[5])))


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        p = np.array(poly[0]); x, y = BNG.transform(p[:, 0], p[:, 1]); yield np.column_stack([x, y])


BOR = [(f["properties"], list(rings(f["geometry"]))) for f in LON["features"]]
GLR = list(rings(LON["london"]))
INR = list(rings(LON["inner"]))
_all = np.vstack(GLR)
GL_EXT = (_all[:, 0].min(), _all[:, 0].max(), _all[:, 1].min(), _all[:, 1].max())


def to_xy(lon, lat):
    return BNG.transform(lon, lat)


def base(ax, ext, land=LDN, bor=True, bor_c="#FFFFFF", bor_lw=.8, outline=True, fill_outside=None):
    """London fill, borough lines and the dashed boundary."""
    for r in GLR:
        ax.add_patch(MPoly(r, closed=True, fc=land, ec="none", zorder=1))
    if bor:
        for p, rs in BOR:
            for r in rs:
                ax.add_patch(MPoly(r, closed=True, fc="none", ec=bor_c, lw=bor_lw, zorder=2))
    if outline:
        for r in GLR:
            ax.plot(r[:, 0], r[:, 1], color=MUT, lw=.9, ls=(0, (4, 3)), zorder=3)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def ways(ax, lw=1.0, outside=False, glow=True, keys_hi=None, dim=1.0, thames_lw=4.5, z=4, buried_dash=True):
    """Draw the Thames, open waterways in blue and buried ones in red with a soft glow."""
    TW = {"river": 1.25, "stream": .9, "canal": 1.1, "drain": .6, "ditch": .55}
    th = [w[5] for w in WAYS if w[0] == "thames"]
    ax.add_collection(LineCollection(th, colors=THAMES, linewidths=thames_lw, capstyle="round", joinstyle="round", zorder=z))
    sel = [w for w in WAYS if w[0] != "thames" and (outside or w[3])]
    op = [w for w in sel if not w[2]]; bu = [w for w in sel if w[2]]
    a_out = .35
    ax.add_collection(LineCollection([w[5] for w in op], colors=[(*matplotlib.colors.to_rgb(WATER), (1 if w[3] else a_out) * dim) for w in op],
                                     linewidths=[lw * TW[w[1]] for w in op], capstyle="round", joinstyle="round", zorder=z + .1))
    if glow:
        for k, a in ((5.5, .10), (3.4, .16)):
            ax.add_collection(LineCollection([w[5] for w in bu], colors=[(*matplotlib.colors.to_rgb(BUR), a * (1 if w[3] else .5)) for w in bu],
                                             linewidths=[lw * TW[w[1]] * k for w in bu], capstyle="round", joinstyle="round", zorder=z + .2))
    ax.add_collection(LineCollection([w[5] for w in bu], colors=[(*matplotlib.colors.to_rgb(BUR), 1 if w[3] else .5) for w in bu],
                                     linewidths=[lw * TW[w[1]] * 1.25 for w in bu], linestyles=(0, (2.2, 1.2)) if buried_dash else "solid", zorder=z + .3))
    if keys_hi:
        hi = [w[5] for w in WAYS if w[0] in keys_hi and w[3]]
        for k, a in ((9, .16), (5.5, .28)):
            ax.add_collection(LineCollection(hi, colors=[(*matplotlib.colors.to_rgb(LOSTC), a)] * len(hi), linewidths=lw * k, capstyle="round", joinstyle="round", zorder=z + .15))


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def river_xy(keys, where=.5):
    """A point on the longest way of a river (or group of keys) inside London, at fraction 'where' of its vertices."""
    best = max((w for w in WAYS if w[0] in keys and w[3]), key=lambda w: w[4])
    i = int(where * (len(best[5]) - 1)); return best[5][i]
