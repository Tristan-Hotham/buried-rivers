// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8874; set PORT to change).
const { chromium } = require("playwright");
// MapLibre from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked here,
// so the screenshots also show the page's own base map, which is what visitors see if the tile server fails.
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
const fs = require("fs");
const URL = "http://localhost:" + (process.env.PORT || 8874) + "/index.html";
(async () => {
  fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const errs = [];
  // 1. graceful degradation: no MapLibre at all (CDN blocked)
  {
    const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
    await p.route(/maplibre-gl|arcgisonline|googleapis|gstatic/, r => r.abort());
    p.on("pageerror", e => errs.push("nomap pageerror: " + e.message));
    await p.goto(URL, { waitUntil: "load" });
    await p.waitForTimeout(1500);
    console.log("no maplibre:", await p.textContent("#loading"), "| charts:", await p.evaluate(() => document.querySelectorAll(".chart svg").length), "| cards:", await p.evaluate(() => document.querySelectorAll(".card").length));
    await p.locator("#atlas").screenshot({ path: "qa/nomap_atlas.png" });
    await p.close();
  }
  for (const [nm, vw, vh] of (process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 900]] : [["desktop", 1280, 900], ["phone", 390, 844]])) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/maplibre-gl\.js$/, r => r.fulfill({ path: ML + "/maplibre-gl.js" }));
    await p.route(/maplibre-gl\.css$/, r => r.fulfill({ path: ML + "/maplibre-gl.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to fetch|AJAXError/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto(URL, { waitUntil: "load" });
    for (let k = 0; k < 60 && !(await p.evaluate(() => !!window.map && document.getElementById("loading") === null)); k++) await p.waitForTimeout(500);
    console.log(nm, "map ready:", await p.evaluate(() => !!window.map && document.getElementById("loading") === null));
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `qa/${nm}_top.png`, timeout: 120000 });
    // clip screenshots (element screenshots wait for animation frames, which the software GL renderer makes slow)
    const shot = async (sel, f) => { await p.evaluate(s => document.querySelector(s).scrollIntoView({ block: "start" }), sel); await p.waitForTimeout(1200);
      const bb = await p.evaluate(s => { const r = document.querySelector(s).getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height }; }, sel);
      await p.screenshot({ path: `qa/${nm}_${f}.png`, clip: bb, fullPage: true, timeout: 150000 }); };
    const drawn = async (l) => p.evaluate(l => map.queryRenderedFeatures({ layers: [l] }).length, l);
    await shot("#atlas", "map");
    console.log(nm, "drawn open/buried:", await drawn("open"), await drawn("buried"), "labels:", await p.evaluate(() => document.querySelectorAll(".rivL").length));
    await p.click("#lostBtn"); await p.waitForTimeout(2000); await shot("#atlas", "map_lost");
    console.log(nm, "lost labels:", await p.evaluate(() => [...document.querySelectorAll(".rivL.l")].map(e => e.textContent.slice(0, 18))));
    await p.click("#lostBtn"); await p.click('#showRow [data-s="buried"]'); await p.waitForTimeout(1200); await shot("#atlas", "map_buried");
    await p.click('#showRow [data-s="all"]');
    await p.click("#focusRow .btn:nth-child(3)"); await p.waitForTimeout(1800); await shot("#atlas", "central");
    await p.click("#focusRow .btn:nth-child(5)"); await p.waitForTimeout(2200); await shot("#atlas", "tyburn");
    // click on the map centre line of the selected river to open a popup
    const pt = await p.evaluate(() => { const f = map.queryRenderedFeatures({ layers: ["selc"] })[0]; if (!f) return null; const c = f.geometry.coordinates[Math.floor(f.geometry.coordinates.length / 2)]; const q = map.project(c); const r = map.getCanvas().getBoundingClientRect(); return [r.left + q.x, r.top + q.y]; });
    if (pt) { await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(800); await shot("#map", "popup"); console.log(nm, "popup:", await p.evaluate(() => (document.querySelector(".maplibregl-popup-content") || {}).textContent?.slice(0, 80))); }
    await p.fill("#q", "Westbourne"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2200); await shot("#atlas", "search_westbourne");
    await p.fill("#q", "Hackney Brook"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2200); await shot("#atlas", "search_hackney");
    await p.fill("#q", "Haringey"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2200); await shot("#atlas", "borough_haringey");
    await p.click("#focusRow .btn:nth-child(2)"); await p.waitForTimeout(1500);
    await p.click(".lyrBtn"); await p.waitForTimeout(300); await shot("#map", "layers_panel");
    await p.evaluate(() => { const i = document.querySelector('.lyrPanel [data-k="bnames"]'); i.click(); }); await p.waitForTimeout(800); await shot("#map", "borough_names");
    await p.evaluate(() => { const i = document.querySelector('.lyrPanel [data-k="bnames"]'); i.click(); }); await p.click(".lyrBtn");
    for (const c of ["typeChart", "rankChart", "cards", "borChart", "lostTable"]) await shot("#" + c, c);
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#rankChart", "dark_rank");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png`, timeout: 120000 });
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
