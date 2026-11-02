"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23873535 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_London_Buried_Rivers"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
assert R["lost_sum"]["mapped"] == 12                                                   # "The twelve that are mapped"
assert R["outer"]["km_per_km2"] > R["inner"]["km_per_km2"] and R["inner"]["x_density"] < R["inner"]["x_share"]   # "per unit area the contrast is smaller"
assert R["rivers"]["lower kid brook"]["boroughs"][0] == "Greenwich"
assert R["rivers"]["thames"]["km_buried"] < .01


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


rows = "".join(f"{tex(t['label'])} & {t['km']:,.1f} & {t['km_open']:,.1f} & {t['km_buried']:,.1f} & {t['pct_buried']:.1f}\\% & {t['share_of_buried_pct']:.1f}\\%\\\\\n" for t in R["types_list"])
g = R["gl"]
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{Mapped waterway inside Greater London by OpenStreetMap type.}\\label{tab:types}"
      "\\begin{tabular}{lrrrrr}\\toprule Type & km & Open & Buried & Buried share & Share of all buried\\\\\\midrule\n" + rows +
      f"\\midrule All & {g['km']:,.1f} & {g['km_open']:,.1f} & {g['km_buried']:,.1f} & {g['pct_buried']:.1f}\\% & 100\\%\\\\\n\\bottomrule\\end{{tabular}}\\end{{table}}")
rk = R["rank"]["by_share"]
rows = "".join(f"{tex(r['name'])} & {tex(', '.join(R['rivers'][r['key']]['boroughs'][:2]))} & {r['km']:.1f} & {r['km_buried']:.1f} & {r['pct']:.1f}\\%\\\\\n" for r in rk)
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{The fifteen most buried named waterways with at least " + f"{R['rank']['min_km']:.0f}" + " km mapped inside Greater London.}\\label{tab:rank}"
      "\\begin{tabular}{llrrr}\\toprule Waterway & Main boroughs & km & Buried km & Buried\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(l['name'])} & {'N' if l['side'] == 'N' else 'S'} & {tex(', '.join(l['osm_names'])) if l['mapped'] else 'not mapped'} & {l['km']:.2f} & {(str(round(l['pct_buried'])) + chr(92) + '%') if l['mapped'] else ''}\\\\\n" for l in R["lost_list"])
TL = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Lost rivers named by Wikipedia, side of the Thames, the OpenStreetMap names matched to them, km mapped inside Greater London and the buried share.}\\label{tab:lost}"
      "\\begin{tabular}{lcp{6.2cm}rr}\\toprule River & Side & OpenStreetMap names & km & Buried\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(b['label'])} & {'inner' if b['inner'] else 'outer'} & {b['km']:.1f} & {b['km_buried']:.1f} & {b['pct']:.1f}\\%\\\\\n" for b in R["bor_by_pct"])
TB = ("\\begin{longtable}{llrrr}\\caption{Boroughs by buried share of mapped waterway, excluding the Thames.}\\label{tab:boroughs}\\\\\\toprule Borough & & km & Buried km & Buried\\\\\\midrule\\endfirsthead\n"
      "\\toprule Borough & & km & Buried km & Buried\\\\\\midrule\\endhead\n" + rows + "\\bottomrule\\end{longtable}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("TYPES", TT), ("RANK", TR), ("LOST", TL), ("BOROUGHS", TB)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("@@DOILINK@@", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
for bad in ("DSIT", "DCMS", "civil serv"):
    assert bad not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
