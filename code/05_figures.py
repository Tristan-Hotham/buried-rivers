"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json; geometry from data/ (see figstyle.py)."""
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
LS = R["lost"]
LOSTK = {k for l in R["lost_list"] for k in l["osm_keys"]}
FAMK = {k for l in R["lost_list"] if l["famous"] for k in l["osm_keys"]}


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())   # 12 in x 150 = 1800 px
    plt.close(fig)


def leg_lines(extra=()):
    return [Line2D([], [], color=WATER, lw=2, label="open water"), Line2D([], [], color=THAMES, lw=5, label="the Thames"),
            Line2D([], [], color=BUR, lw=2, ls=(0, (2.2, 1.2)), label="buried: culvert, pipe or tunnel")] + list(extra)


# ---------- Greater London map ----------
pad = 2500
EXT = (GL_EXT[0] - pad, GL_EXT[1] + pad, GL_EXT[2] - pad, GL_EXT[3] + pad)
W_, H_ = EXT[1] - EXT[0], EXT[3] - EXT[2]
FH = 12 * H_ / W_ + 1.0
fig = plt.figure(figsize=(12, FH), facecolor=BG)
ax = fig.add_axes([0, .55 / FH, 1, 12 * H_ / W_ / FH]); ax.set_facecolor(BG)
base(ax, EXT); ways(ax, lw=1.0, outside=False)
x, y = to_xy(-0.222, 51.548)
ax.text(x, y, "Westbourne,\nTyburn and Fleet", fontproperties=SERI, fontsize=11.5, color=BUR, ha="right", va="center", path_effects=HALO, zorder=8, linespacing=1.1)
LAB = [("moselle", .5, (0, 2600), "Moselle Brook"), ("mutton brook", .5, (0, 2000), "Mutton Brook"), ("wandle", .5, (-2400, 0), "Wandle"),
       ("brent", .55, (0, -1800), "Brent"), ("ravensbourne", .45, (2600, 0), "Ravensbourne"), ("crane", .5, (0, -1800), "Crane"),
       ("roding", .4, (2200, 0), "Roding"), ("wogebourne", .5, (2200, -1500), "Wogebourne"), ("kyd brook", .5, (2600, 800), "Kyd Brook")]
for k, f, (dx, dy), t in LAB:
    x, y = river_xy({k}, f); bur = R["rivers"][k]["pct_buried"] > 50
    ax.text(x + dx, y + dy, t, fontproperties=SERI, fontsize=11.5, color=BUR if bur else WATER, ha="center", va="center", path_effects=HALO, zorder=8)
fig.text(.02, 1 - .3 / FH, f"Every waterway OpenStreetMap maps in Greater London: {R['gl']['km']:,.0f} km, of which {R['gl']['km_buried']:,.0f} km ({R['gl']['pct_buried']:.1f}%) is buried", fontsize=11, color=FG)
fig.legend(handles=leg_lines([Line2D([], [], color=MUT, lw=1, ls=(0, (4, 3)), label="Greater London")]), loc="lower center", ncol=4, frameon=False, fontsize=10, bbox_to_anchor=(.5, .0))
both(fig, "map")

# ---------- central London: the lost rivers ----------
cx0, cy0 = to_xy(-0.235, 51.455); cx1, cy1 = to_xy(-0.045, 51.575)
CEXT = (cx0, cx1, cy0, cy1)
fig = plt.figure(figsize=(12, 12 * (cy1 - cy0) / (cx1 - cx0) * .9 + 1.0), facecolor=BG)
ax = fig.add_axes([0, .07, 1, .86]); ax.set_facecolor(BG)
base(ax, CEXT, bor_lw=1.1); ways(ax, lw=1.6, outside=True, keys_hi=FAMK, thames_lw=11)
CL = [("fleet", (-0.135, 51.548), "left", "River Fleet"), ("tyburn", (-0.1505, 51.524), "left", "River Tyburn"), ("westbourne", (-0.207, 51.541), "right", "River Westbourne"),
      ("walbrook", (-0.0735, 51.518), "left", "Walbrook"), ("neckinger", (-0.083, 51.4865), "left", "River Neckinger"), ("effra", (-0.117, 51.477), "left", "River Effra (a fragment)"),
      ("chelsea creek", (-0.157, 51.4695), "left", "Counter's Creek (Chelsea Creek)")]
for k, (lon, lat), ha, t in CL:
    x, y = to_xy(lon, lat); l = LS[[q["key"] for q in R["lost_list"] if k in q["osm_keys"]][0]]
    sub = f"{l['km_buried']:.1f} of {l['km']:.1f} km buried" if l["km_buried"] else "only the open mouth is mapped"
    ax.text(x, y, t, fontproperties=DISPB, fontsize=14, color=FG, ha=ha, va="bottom", path_effects=HALO, zorder=9)
    ax.text(x, y - 80, sub, fontsize=9.5, color=MUT, ha=ha, va="top", path_effects=HALO, zorder=9)
for nm, lon, lat, ha in (("Hampstead", -0.178, 51.556, "left"), ("Sloane Square", -0.157, 51.4925, "right"), ("Buckingham Palace", -0.1419, 51.5014, "left"), ("Fleet Street", -0.1075, 51.5141, "right"), ("Brixton", -0.1145, 51.4613, "left")):
    x, y = to_xy(lon, lat); ax.plot([x], [y], "o", ms=4, color=FG, zorder=10)
    ax.text(x + (250 if ha == "left" else -250), y + 120, nm, fontsize=9, color=FG, ha=ha, path_effects=HALO, zorder=10)
fig.text(.02, .965, "Central London: the famous lost rivers glow gold. Red dashes: buried; blue: open", fontsize=11, color=FG)
fig.legend(handles=leg_lines([Line2D([], [], color=LOSTC, lw=7, alpha=.45, label="famous lost rivers")]), loc="lower center", ncol=4, frameon=False, fontsize=10, bbox_to_anchor=(.5, .005))
both(fig, "central")

# ---------- by type ----------
T = R["types_list"]
fig = plt.figure(figsize=(12, 4.2), facecolor=BG); ax = fig.add_axes([.2, .14, .62, .74]); ax.set_facecolor(BG)
y = np.arange(len(T))[::-1]
ax.barh(y, [t["km_open"] for t in T], color=WATER, height=.62, label="open")
ax.barh(y, [t["km_buried"] for t in T], left=[t["km_open"] for t in T], color=BUR, height=.62, label="buried")
for yy, t in zip(y, T):
    ax.text(t["km"] + 8, yy, f"{t['km']:,.0f} km, {t['pct_buried']:.0f}% buried", va="center", fontsize=10.5)
ax.set_yticks(y); ax.set_yticklabels([t["label"] for t in T], fontsize=11); ax.tick_params(axis="y", length=0)
spines(ax); ax.set_xlabel("km mapped inside Greater London"); ax.set_xlim(0, 560)
ax.legend(loc="lower right", frameon=False, fontsize=11)
both(fig, "types")

# ---------- most buried rivers ----------
fig, axs = plt.subplots(1, 2, figsize=(12, 5.6), facecolor=BG); fig.subplots_adjust(left=.19, right=.97, wspace=.85, top=.86, bottom=.06)
for ax, rows, mode, t in ((axs[0], R["rank"]["by_share"][:12], "pct", f"share buried, rivers with {R['rank']['min_km']:.0f}+ km mapped"), (axs[1], R["rank"]["by_km"][:12], "km", "kilometres buried (pale: open)")):
    ax.set_facecolor(BG); rows = rows[::-1]; yy = np.arange(len(rows))
    if mode == "pct":
        ax.barh(yy, [r["pct"] for r in rows], color=BUR, height=.66); ax.barh(yy, [100 - r["pct"] for r in rows], left=[r["pct"] for r in rows], color=WATER, alpha=.3, height=.66)
        for i, r in enumerate(rows): ax.text(101.5, i, f"{r['pct']:.0f}%", va="center", fontsize=9.5)
        ax.set_xlim(0, 100)
    else:
        ax.barh(yy, [r["km_buried"] for r in rows], color=BUR, height=.66); ax.barh(yy, [r["km"] - r["km_buried"] for r in rows], left=[r["km_buried"] for r in rows], color=WATER, alpha=.3, height=.66)
        for i, r in enumerate(rows): ax.text(r["km"] + .3, i, f"{r['km_buried']:.1f}", va="center", fontsize=9.5)
    ax.set_yticks(yy); ax.set_yticklabels([r["name"] for r in rows], fontsize=10)
    for lab, r in zip(ax.get_yticklabels(), rows):
        if r["key"] in LOSTK: lab.set_color(LOSTC); lab.set_fontweight("medium")
    ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0)
    ax.set_title(t, loc="left", fontsize=11.5, color=FG, x=-.02 if mode == "pct" else -.02)
fig.text(.02, .955, "Gold names: rivers on Wikipedia's list of London's subterranean rivers", fontsize=10, color=MUT)
both(fig, "rank")

# ---------- boroughs: choropleth of the buried share ----------
from matplotlib import cm, colors as mcol
cmap = mcol.LinearSegmentedColormap.from_list("b", ["#F3EEE6", "#E9B9A6", "#D4775E", "#B23A26", "#6E1E12"])
norm_ = mcol.Normalize(0, 100)
fig = plt.figure(figsize=(12, 9.4), facecolor=BG); ax = fig.add_axes([0, .08, .78, .86]); ax.set_facecolor(BG)
for p, rs in BOR:
    v = R["boroughs"][p["name"]]["pct_buried"] or 0
    for r in rs: ax.add_patch(MPoly(r, closed=True, fc=cmap(norm_(v)), ec="#FFFFFF", lw=1.1, zorder=1))
for r in INR: ax.plot(r[:, 0], r[:, 1], color=INNERC, lw=2.2, zorder=3)
for r in GLR: ax.plot(r[:, 0], r[:, 1], color=MUT, lw=1, zorder=3)
th = [w[5] for w in WAYS if w[0] == "thames"]; ax.add_collection(LineCollection(th, colors=THAMES, linewidths=3.5, zorder=2))
SHOW = {"City": (0, 0), "Westminster": (0, 0), "Camden": (0, 0), "Haringey": (0, 0), "Greenwich": (0, 0), "Bromley": (0, 0), "Hackney": (0, 0),
        "Barnet": (0, 0), "Enfield": (0, 0), "Redbridge": (0, 0), "Hillingdon": (0, 0), "Havering": (0, 0), "Lambeth": (0, 0), "Southwark": (0, 0), "Croydon": (0, 0)}
for p, rs in BOR:
    if p["name"] not in SHOW: continue
    b = R["boroughs"][p["name"]]; x, y = to_xy(p["lx"], p["ly"])
    if p["name"] == "City": x += 2600; y += 900
    if p["name"] == "Westminster": y -= 1100; x += 300
    ax.text(x, y, f"{p['label'].replace('Kensington and Chelsea', 'Kensington & Chelsea')}\n{b['pct_buried']:.0f}%", ha="center", va="center", fontsize=8.6 if p["name"] not in ("City",) else 8.2,
            color=FG, path_effects=[pe.withStroke(linewidth=2.6, foreground="#FFFFFF")], zorder=6)
ax.set_xlim(EXT[0], EXT[1]); ax.set_ylim(EXT[2], EXT[3]); ax.set_aspect("equal"); ax.axis("off")
cax = fig.add_axes([.81, .3, .022, .45]); cb = fig.colorbar(cm.ScalarMappable(norm=norm_, cmap=cmap), cax=cax); cb.set_label("share of mapped waterway that is buried, %", fontsize=10)
cb.outline.set_visible(False)
fig.text(.80, .2, f"Inner London (purple line)\n{R['inner']['pct_buried']:.0f}% buried\n\nOuter London\n{R['outer']['pct_buried']:.0f}% buried\n\nThe Thames is left out.", fontsize=10, color=FG, va="top")
fig.text(.02, .96, "Share of each borough's mapped waterway that runs underground", fontsize=11, color=FG)
both(fig, "boroughs")

# ---------- the lost rivers: what OSM maps ----------
L = sorted(R["lost_list"], key=lambda l: -l["km"])
fig = plt.figure(figsize=(12, 6.6), facecolor=BG); ax = fig.add_axes([.2, .13, .62, .78]); ax.set_facecolor(BG)
yy = np.arange(len(L))[::-1]
ax.barh(yy, [l["km_buried"] for l in L], color=BUR, height=.64)
ax.barh(yy, [l["km_open"] for l in L], left=[l["km_buried"] for l in L], color=WATER, height=.64)
for y_, l in zip(yy, L):
    ax.text(l["km"] + .25, y_, f"{l['km']:.1f} km, {l['pct_buried']:.0f}% buried" if l["mapped"] else "not mapped as a waterway", va="center", fontsize=9.5, color=FG if l["mapped"] else MUT)
ax.set_yticks(yy); ax.set_yticklabels([l["name"] for l in L], fontsize=10.5); ax.tick_params(axis="y", length=0); spines(ax)
ax.set_xlabel("km mapped in OpenStreetMap inside Greater London"); ax.set_xlim(0, 22)
fig.legend(handles=[Patch(color=BUR, label="buried"), Patch(color=WATER, label="open")], loc="upper right", frameon=False, bbox_to_anchor=(.98, .9))
fig.text(.02, .955, "The lost rivers on Wikipedia's list, and how much of each OpenStreetMap still traces", fontsize=11, color=FG)
both(fig, "lost")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
hx0, hy0 = to_xy(-0.26, 51.445); hx1, hy1 = to_xy(-0.01, 51.60)
ax = fig.add_axes([.43, .0, .57, 1]); ax.set_facecolor(BG)
hw = (hx1 - hx0); hh = hw * (6.3 / (12 * .57))
cyc = (hy0 + hy1) / 2
base(ax, (hx0, hx1, cyc - hh / 2, cyc + hh / 2), bor_lw=.7); ways(ax, lw=1.2, outside=True, keys_hi=FAMK, thames_lw=7)
fig.text(.04, .88, "London's", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.04, .72, "buried", fontproperties=DISP, fontsize=50, color=WATER, va="top")
fig.text(.04, .56, "rivers", fontproperties=DISP, fontsize=50, color=BUR, va="top")
fig.text(.04, .36, f"{R['gl']['km_buried']:,.0f} km of London's waterways\nrun in culverts and tunnels.\nThe Fleet, Tyburn and Westbourne\nare {R['lost_sum']['big3_pct']:.0f}% underground.", fontproperties=SERP, fontsize=14.5, color=FG, va="top", linespacing=1.35)
fig.text(.04, .04, "maps.tristanhotham.com/buried-rivers", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
