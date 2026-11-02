"""r/dataisbeautiful collage for buried-rivers: 2400 x 3200 px, light background. Numbers from data/results.json.
Labels sit on the plain paper around Greater London (main map) or in the paper margins beside the central London
inset, never over London or over the data; leader lines are checked not to cross any label."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib.patches import Rectangle, ConnectionPatch
from matplotlib.lines import Line2D
from shapely.geometry import Polygon as SPoly, box as sbox, LineString as SLS, Point as SPt
from shapely.ops import unary_union

R = jload(f"{DATA}/results.json")
BGc = "#F8F6F1"
HALOP = [pe.withStroke(linewidth=4, foreground=BGc)]
g, LS, rk = R["gl"], R["lost"], R["rank"]
FAMK = {k for l in R["lost_list"] if l["famous"] for k in l["osm_keys"]}

fig = plt.figure(figsize=(12, 16.0), dpi=200, facecolor=BGc)
fig.text(.045, .985, "London's buried rivers", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(.045, .943, f"OpenStreetMap maps {g['km']:,.0f} km of rivers, streams, canals, drains and ditches inside Greater London.\n"
         f"{g['km_buried']:,.0f} km of them ({g['pct_buried']:.1f}%) run in culverts, pipes and tunnels. The Tyburn, which flows under\n"
         f"Buckingham Palace, is buried for every metre of its {LS['tyburn']['km']:.1f} km.", fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.45)
LEG = [Line2D([], [], color=WATER, lw=2.2, label="open water"), Line2D([], [], color=THAMES, lw=6, label="the Thames"),
       Line2D([], [], color=BUR, lw=2.2, ls=(0, (2.2, 1.2)), label="buried: culvert, pipe or tunnel"),
       Line2D([], [], color=LOSTC, lw=8, alpha=.45, label="famous lost rivers (inset)"),
       Line2D([], [], color=MUT, lw=1.1, ls=(0, (4, 3)), label="Greater London boundary"), Line2D([], [], color="#FFFFFF", lw=2.5, label="borough boundaries")]
LP = SERP.copy(); LP.set_size(11.5)
fig.legend(handles=LEG, loc="upper left", bbox_to_anchor=(.035, .878), ncol=3, frameon=False, prop=LP, handlelength=2.6, columnspacing=1.6)

# ---------- main map ----------
AX0 = [0, .555, 1, .285]
pad_x, pad_y = 6000, 1500
cxm, cym = (GL_EXT[0] + GL_EXT[1]) / 2, (GL_EXT[2] + GL_EXT[3]) / 2
H = GL_EXT[3] - GL_EXT[2] + 2 * pad_y; Wd = H * (12 * AX0[2]) / (16 * AX0[3])
EXT = (cxm - Wd / 2, cxm + Wd / 2, cym - H / 2, cym + H / 2)
ax = fig.add_axes(AX0); ax.set_facecolor(BGc)
base(ax, EXT, land="#ECE7DC", bor_lw=.7); ways(ax, lw=.85, outside=False)
GLP = unary_union([SPoly(r).buffer(0) for r in GLR])
x0i, y0i = to_xy(-0.235, 51.455); x1i, y1i = to_xy(-0.045, 51.575)
ax.add_patch(Rectangle((x0i, y0i), x1i - x0i, y1i - y0i, fc="none", ec=FG, lw=1.3, zorder=9))
DATA_G = unary_union([SLS(w[5]).buffer(150) for w in WAYS if (w[3] or w[0] == "thames") and len(w[5]) > 1] + [GLP.buffer(600)])   # no label may touch London or a line
fig.canvas.draw(); REN = fig.canvas.get_renderer()
PLACED, LINES = [], []


def tbox(t, a):
    bb = t.get_window_extent(REN)
    (u0, v0), (u1, v1) = a.transData.inverted().transform([[bb.x0 - 5, bb.y0 - 4], [bb.x1 + 5, bb.y1 + 4]])
    return sbox(u0, v0, u1, v1)


def place(name, s, target, cands, col, ha="center"):
    """target: (x, y) in map metres on the river; cands: label centres to try, nearest first. A leader joins the label to
    the target; neither may cross another label, and the label must sit on plain paper inside the map frame."""
    t = ax.text(0, 0, s, ha=ha, va="center", fontproperties=SERI, fontsize=13, color=col, zorder=12, path_effects=HALOP, linespacing=1.1)
    for cx, cy in sorted(cands, key=lambda c: np.hypot(c[0] - target[0], c[1] - target[1])):
        t.set_position((cx, cy)); b = tbox(t, ax)
        if not sbox(EXT[0] + 300, EXT[2] + 300, EXT[1] - 300, EXT[3] - 300).contains(b): continue
        if b.intersects(DATA_G) or any(b.intersects(o) for _, o in PLACED) or any(b.intersects(l) for _, l in LINES): continue
        from shapely.ops import nearest_points
        pb, _ = nearest_points(b.exterior, SPt(target)); ln = SLS([(pb.x, pb.y), target])
        if any(ln.intersects(o) for _, o in PLACED): continue
        PLACED.append((name, b)); LINES.append((name, ln))
        ax.plot(*ln.xy, color=FG, lw=.8, zorder=11); ax.plot([target[0]], [target[1]], "o", ms=3.2, color=FG, zorder=11)
        return
    raise RuntimeError("no clean spot for " + name)


GRID = [(x, y) for x in np.arange(EXT[0] + 3000, EXT[1] - 3000, 900) for y in np.arange(EXT[2] + 1200, EXT[3] - 1200, 700)]
for k, f, nm in (("moselle", .5, f"Moselle Brook\n{LS['moselle']['km_buried']:.1f} km buried"), ("mutton brook", .6, f"Mutton Brook\n{R['rivers']['mutton brook']['km_buried']:.1f} km buried"),
                 ("wogebourne", .5, f"Wogebourne\n{R['rivers']['wogebourne']['km_buried']:.1f} km buried"), ("kyd brook", .4, f"Kyd Brook\n{R['rivers']['kyd brook']['km_buried']:.1f} km buried"),
                 ("cran brook", .5, f"Cran Brook\n{R['rivers']['cran brook']['km_buried']:.1f} km buried"), ("wandle", .5, f"River Wandle\n{R['rivers']['wandle']['pct_buried']:.0f}% buried"),
                 ("brent", .5, f"River Brent\n{R['rivers']['brent']['pct_buried']:.0f}% buried"), ("crane", .5, f"River Crane\n{R['rivers']['crane']['pct_buried']:.0f}% buried")):
    xy = river_xy({k}, f); place(k, nm, (float(xy[0]), float(xy[1])), GRID, BUR if R["rivers"][k]["pct_buried"] > 50 else WATER)
# label for the inset frame, on paper
t = ax.text(0, 0, "Central London,\nenlarged below", ha="center", va="center", fontsize=11, color=FG, zorder=12, path_effects=HALOP)
for cx, cy in sorted(GRID, key=lambda c: np.hypot(c[0] - x0i, c[1] - y1i)):
    t.set_position((cx, cy)); b = tbox(t, ax)
    if b.intersects(DATA_G) or any(b.intersects(o) for _, o in PLACED) or any(b.intersects(l) for _, l in LINES) or not sbox(*EXT[:1], EXT[2], EXT[1], EXT[3]).contains(b): continue
    from shapely.ops import nearest_points
    pb, pr = nearest_points(b.exterior, sbox(x0i, y0i, x1i, y1i).exterior); ln = SLS([(pb.x, pb.y), (pr.x, pr.y)])
    if any(ln.intersects(o) for _, o in PLACED): continue
    PLACED.append(("inset", b)); ax.plot(*ln.xy, color=FG, lw=.8, zorder=11); LINES.append(("inset", ln)); break
for nm, b in PLACED:
    assert not b.intersects(DATA_G) and not any(b.intersects(o) for n2, o in PLACED if n2 != nm), nm
for nm, l in LINES:
    assert not any(l.intersects(o) for n2, o in PLACED if n2 != nm), nm

# ---------- central London inset, labels in the paper margins ----------
IA = [.31, .262, .38, .285]          # 4.56 in x 4.56 in
ai = fig.add_axes(IA); ai.set_facecolor(BGc)
base(ai, (x0i, x1i, y0i, y1i), land="#ECE7DC", bor_lw=1.0, outline=False); ways(ai, lw=1.25, outside=True, keys_hi=FAMK, thames_lw=7)
for sp in ai.spines.values(): sp.set_visible(True); sp.set_color(FG); sp.set_linewidth(1.3)
ai.axis("on"); ai.set_xticks([]); ai.set_yticks([])
fig.text(IA[0], IA[1] + IA[3] + .006, "Central London", fontproperties=DISPB, fontsize=15, color=FG)
SIDE = [("westbourne", .35, "L", "River Westbourne", "rose in Hampstead; crosses\nSloane Square station in a pipe"),
        ("tyburn", .55, "L", "River Tyburn", "runs beneath\nBuckingham Palace"),
        ("chelsea creek", .5, "L", "Counter's Creek", "only its open mouth,\nChelsea Creek, is mapped"),
        ("fleet", .3, "R", "River Fleet", "gave its name to\nFleet Street"),
        ("walbrook", .4, "R", "Walbrook", "the City's own stream"),
        ("neckinger", .5, "R", "River Neckinger", "Dickens's Jacob's Island"),
        ("effra", .5, "R", "River Effra", "a fragment is all\nthat is mapped")]
FW, FHt = fig.get_size_inches()
def fxy(a, x, y):   # data -> figure fraction
    return fig.transFigure.inverted().transform(a.transData.transform((x, y)))
LAB = []
for side in "LR":
    items = [(k, f, nm, sub, fxy(ai, *river_xy({k}, f))) for k, f, s_, nm, sub in SIDE if s_ == side]
    items.sort(key=lambda r: -r[4][1])
    n = len(items); ys = np.linspace(IA[1] + IA[3] - .03, IA[1] + .03, n)
    for (k, f, nm, sub, (tx, ty)), yy in zip(items, ys):
        l = LS[[q["key"] for q in R["lost_list"] if k in q["osm_keys"]][0]]
        stat = f"{l['km_buried']:.1f} of {l['km']:.1f} km buried" if l["km_buried"] else f"{l['km']:.1f} km mapped, open"
        xl = IA[0] - .012 if side == "L" else IA[0] + IA[2] + .012; ha = "right" if side == "L" else "left"
        t1 = fig.text(xl, yy + .009, nm, fontproperties=DISPB, fontsize=13, color=FG, ha=ha, va="bottom")
        t2 = fig.text(xl, yy + .008, stat, fontsize=9.5, color=BUR if l["km_buried"] else WATER, ha=ha, va="top")
        t3 = fig.text(xl, yy - .006, sub, fontproperties=SERI, fontsize=10.5, color=MUT, ha=ha, va="top", linespacing=1.1)
        LAB.append((k, [t1, t2, t3], (xl, yy + .0085), (tx, ty)))
fig.canvas.draw()
def fbox(ts):
    bb = [t.get_window_extent(REN) for t in ts]; inv = fig.transFigure.inverted()
    (a0, b0), (a1, b1) = inv.transform([[min(b.x0 for b in bb) - 4, min(b.y0 for b in bb) - 3], [max(b.x1 for b in bb) + 4, max(b.y1 for b in bb) + 3]])
    return sbox(a0, b0, a1, b1)
BOX = {k: fbox(ts) for k, ts, _, _ in LAB}
INS = sbox(IA[0], IA[1], IA[0] + IA[2], IA[1] + IA[3])
for k, ts, (xl, yl), (tx, ty) in LAB:
    ln = SLS([(xl + (.004 if xl < IA[0] else -.004), yl), (tx, ty)])
    assert not BOX[k].intersects(INS), k                                          # labels on paper, outside the map
    assert not any(ln.intersects(b) for k2, b in BOX.items() if k2 != k), k        # leader crosses no other label
    fig.add_artist(Line2D([ln.coords[0][0], tx], [yl, ty], transform=fig.transFigure, color=FG, lw=.8, zorder=20))
    fig.add_artist(Line2D([tx], [ty], transform=fig.transFigure, marker="o", ms=3.2, color=FG, zorder=21))
for k, b in BOX.items():
    assert not any(b.intersects(o) for k2, o in BOX.items() if k2 != k), k
for k, ts, (xl, yl), (tx, ty) in LAB:   # leaders must not cross each other either
    for k2, ts2, (xl2, yl2), (tx2, ty2) in LAB:
        if k2 != k: assert not SLS([(xl, yl), (tx, ty)]).crosses(SLS([(xl2, yl2), (tx2, ty2)])), (k, k2)

# ---------- numbers row ----------
nums = [(f"{g['km_buried']:,.0f} km", BUR, f"of waterway buried,\n{g['pct_buried']:.1f}% of {g['km']:,.0f} km mapped"),
        (f"{R['types']['stream']['pct_buried']:.0f}%", BUR, "of streams and brooks are\nburied; rivers only " + f"{R['types']['river']['pct_buried']:.0f}%"),
        (f"{R['inner']['pct_buried']:.0f}%", INNERC, f"buried in inner London,\n{R['outer']['pct_buried']:.0f}% in outer (no Thames)"),
        (f"{R['lost_sum']['unmapped']} of {R['lost_sum']['n']}", OUTERC, "lost rivers not mapped as\nwaterways at all: now sewers")]
for i, (big, col, small) in enumerate(nums):
    xx = .045 + i * .235
    fig.text(xx, .232, big, fontproperties=DISP, fontsize=31, color=col, va="top")
    fig.text(xx, .196, small, family=MONO, fontsize=10, color=FG, va="top", linespacing=1.4)

# ---------- bars: most buried rivers by km ----------
a = fig.add_axes([.235, .05, .3, .085]); a.set_facecolor(BGc)
rows = rk["by_km"][:6][::-1]; yy = np.arange(len(rows))
a.barh(yy, [r["km_buried"] for r in rows], color=BUR, height=.66); a.barh(yy, [r["km"] - r["km_buried"] for r in rows], left=[r["km_buried"] for r in rows], color=WATER, alpha=.35, height=.66)
for i, r in enumerate(rows): a.text(r["km"] + .3, i, f"{r['km_buried']:.1f}", va="center", fontsize=10)
a.set_yticks(yy); a.set_yticklabels([r["name"].replace("River ", "") for r in rows], fontsize=10.5); a.tick_params(axis="y", length=0)
a.set_xticks([]); spines(a); a.spines["bottom"].set_visible(False); a.set_xlim(0, 20)
a.set_title("Most kilometres buried (pale: open)", family=MONO, fontsize=11.5, color=FG, loc="left", pad=8, x=-.6)
b = fig.add_axes([.74, .05, .21, .085]); b.set_facecolor(BGc)
rows = R["bor_by_pct"][:6][::-1]; yy = np.arange(len(rows))
b.barh(yy, [r["pct"] for r in rows], color=[INNERC if r["inner"] else OUTERC for r in rows], height=.66)
for i, r in enumerate(rows): b.text(r["pct"] + 2, i, f"{r['pct']:.0f}%", va="center", fontsize=10)
b.set_yticks(yy); b.set_yticklabels([r["label"].replace("Kensington and Chelsea", "Kensington & Ch.") for r in rows], fontsize=10.5); b.tick_params(axis="y", length=0)
b.set_xticks([]); spines(b); b.spines["bottom"].set_visible(False); b.set_xlim(0, 125)
b.set_title("Most buried boroughs, % (purple: inner)", family=MONO, fontsize=11.5, color=FG, loc="left", pad=8, x=-.78)

fig.text(.045, .006, f"Source: OpenStreetMap waterways (river, stream, canal, drain, ditch), (c) OpenStreetMap contributors, ODbL, {R['source']['osm_year']}. Buried = tagged culvert, tunnel, covered,\n"
         "underground or below ground level. Boundaries: Natural Earth. River histories: English Wikipedia. Many lost rivers now survive\nonly as sewers, so this is a lower bound.  "
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/buried-rivers", family=MONO, fontsize=8.3, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "london_buried_rivers.png")
fig.savefig(out, facecolor=BGc, dpi=200)
print("ok", out, [n for n, _ in PLACED])
