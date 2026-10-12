/* Peranakan Tiles prototype: shared tile generator plus the interactive figures. All figures are illustrative. */
(() => {
  "use strict";
  const C = {
    rose: "#e58fa4", mustard: "#d9a21b", jade: "#2e9c7a", cobalt: "#2b4c9b", porcelain: "#eef3f1",
    peacock: "#0f4c5c", peacockDeep: "#0a3843", ink: "#13262b", inkSoft: "#46595e", warm: "#f7e7d0", sky: "#e3eef4",
    roseTint: "#fbeef1",
    // Deeper glazes for lines and marks, at least 3:1 on porcelain; the light tints above stay for fills.
    mustardDeep: "#a87a0c", roseDeep: "#c4506e", jadeDeep: "#24805f"
  };
  const NS = "http://www.w3.org/2000/svg";
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const fmt = n => n.toLocaleString("en-GB");

  /* ---------- Tile generator (from the approved mockup) ---------- */
  const grounds = [C.porcelain, C.warm, C.porcelain, C.sky];
  const motifs = [
    (a, b) => `<g fill="${a}"><circle cx="50" cy="35" r="13"/><circle cx="50" cy="65" r="13"/><circle cx="35" cy="50" r="13"/><circle cx="65" cy="50" r="13"/></g><circle cx="50" cy="50" r="7" fill="${b}"/>`,
    (a, b) => `<g fill="${a}"><rect x="30" y="30" width="40" height="40"/><rect x="30" y="30" width="40" height="40" transform="rotate(45 50 50)"/></g><circle cx="50" cy="50" r="9" fill="${b}"/>`,
    (a, b) => `<path d="M50 18 L82 50 L50 82 L18 50Z" fill="${a}"/><path d="M50 34 L66 50 L50 66 L34 50Z" fill="${b}"/>`,
    (a, b) => `<g fill="${a}"><ellipse cx="50" cy="32" rx="9" ry="17"/><ellipse cx="50" cy="68" rx="9" ry="17"/><ellipse cx="32" cy="50" rx="17" ry="9"/><ellipse cx="68" cy="50" rx="17" ry="9"/></g><circle cx="50" cy="50" r="8" fill="${b}"/>`
  ];
  const pairs = [[C.cobalt, C.mustard], [C.jade, C.rose], [C.rose, C.cobalt], [C.mustard, C.jade], [C.peacock, C.rose]];
  // Corner quarter-circles share one colour, so neighbouring tiles join into a second pattern as real Peranakan tiles do.
  const corners = fill => `<g fill="${fill}"><path d="M0 0h18a18 18 0 0 1-18 18z"/><path d="M100 0v18a18 18 0 0 1-18-18z"/><path d="M0 100v-18a18 18 0 0 1 18 18z"/><path d="M100 100h-18a18 18 0 0 1 18-18z"/></g>`;
  const frame = stroke => `<rect x="6" y="6" width="88" height="88" fill="none" stroke="${stroke}" stroke-width="1.5" opacity=".6"/>`;
  const tileFrom = (motif, a, b, ground) => `<rect width="100" height="100" fill="${ground}"/>${corners(C.jade)}${frame(a)}${motifs[motif](a, b)}`;
  const tile = i => {
    const [a, b] = pairs[i % pairs.length];
    return tileFrom((i * 7 + 1) % motifs.length, a, b, grounds[(i * 3) % grounds.length]);
  };
  // Each study keeps one motif and colour pair wherever it appears.
  const PAIRS = {
    pulse: { motif: 2, a: C.mustard, b: C.jade, ground: C.warm, tint: C.warm },        // diamond (tile 3 on the mockup)
    forecast: { motif: 3, a: C.cobalt, b: C.mustard, ground: C.sky, tint: C.sky },    // four petals
    llm: { motif: 0, a: C.rose, b: C.cobalt, ground: C.porcelain, tint: C.roseTint }       // round flower
  };
  const STUDY = Object.fromEntries(Object.entries(PAIRS).map(([k, p]) => [k, tileFrom(p.motif, p.a, p.b, p.ground)]));

  // Generated decoration for study pages: the border frieze, the thin header frieze and the method step tiles.
  const svgUrl = (viewBox, body) => `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns="${NS}" viewBox="${viewBox}">${body}</svg>`)}")`;
  const borderTile = p => `<rect width="100" height="100" fill="${p.tint}"/>${corners(C.jade)}${frame(p.a)}<path d="M50 28L72 50L50 72L28 50Z" fill="${p.b}"/><circle cx="50" cy="50" r="6" fill="${p.a}"/>`;
  const current = Object.keys(PAIRS).find(k => document.body.classList.contains(`s-${k}`));
  const friezeKeys = current ? [current] : Object.keys(PAIRS);
  const friezeTiles = current ? [STUDY[current], borderTile(PAIRS[current])] : friezeKeys.map(k => STUDY[k]);
  const rootStyle = document.documentElement.style;
  rootStyle.setProperty("--frieze", svgUrl(`0 0 ${friezeTiles.length * 100} 100`, friezeTiles.map((t, i) => `<g transform="translate(${i * 100} 0)">${t}</g>`).join("")));
  const lead = PAIRS[friezeKeys[0]];
  rootStyle.setProperty("--frieze-thin", svgUrl("0 0 40 10", `<rect width="40" height="10" fill="${lead.tint}"/><path d="M10 1L14 5L10 9L6 5Z" fill="${lead.a}"/><path d="M30 1L34 5L30 9L26 5Z" fill="${lead.b}"/><g fill="${C.jade}"><circle cx="0" cy="5" r="2.2"/><circle cx="20" cy="5" r="2.2"/><circle cx="40" cy="5" r="2.2"/></g>`));
  const stepTile = fill => svgUrl("0 0 100 100", `<rect width="100" height="100" fill="${lead.tint}"/>${corners(C.jade)}<path d="M50 13L87 50L50 87L13 50Z" fill="${fill}"/>`);
  rootStyle.setProperty("--step-a", stepTile(lead.a));
  rootStyle.setProperty("--step-b", stepTile(lead.b));

  $$("svg[data-tile]").forEach(svg => { svg.innerHTML = tile(Number(svg.dataset.tile)); });
  $$("svg[data-study]").forEach(svg => { svg.innerHTML = STUDY[svg.dataset.study]; });

  // Turnable mosaics: the home hero (16 mixed tiles) and each study hero (4 of the study's own tile).
  $$("[data-mosaic]").forEach(mosaic => {
    const study = mosaic.dataset.study;
    const count = Number(mosaic.dataset.mosaic);
    for (let i = 0; i < count; i++) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("aria-label", `Turn tile ${i + 1}`);
      btn.innerHTML = `<svg viewBox="0 0 100 100" aria-hidden="true">${study ? STUDY[study] : tile(i)}</svg>`;
      let turns = 0;
      btn.addEventListener("click", () => { turns += 1; btn.style.transform = `rotate(${turns * 90}deg)`; });
      mosaic.appendChild(btn);
    }
  });

  /* ---------- Shared helpers ---------- */
  function setupTabs(list, onSelect) {
    const tabs = $$('[role="tab"]', list);
    const select = (tab, focus) => {
      tabs.forEach(t => {
        const on = t === tab;
        t.setAttribute("aria-selected", String(on));
        t.tabIndex = on ? 0 : -1;
      });
      if (focus) tab.focus();
      onSelect(tab);
    };
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
    tabs.forEach((tab, i) => {
      tab.addEventListener("click", () => select(tab));
      tab.addEventListener("keydown", e => {
        let j = -1;
        if (e.key in step) j = (i + step[e.key] + tabs.length) % tabs.length;
        else if (e.key === "Home") j = 0;
        else if (e.key === "End") j = tabs.length - 1;
        if (j < 0) return;
        e.preventDefault();
        select(tabs[j], true);
      });
    });
    select(tabs.find(t => t.getAttribute("aria-selected") === "true") || tabs[0]);
  }

  function setupToggles(group, onChange) {
    const btns = $$("button[aria-pressed]", group);
    const state = () => new Set(btns.filter(b => b.getAttribute("aria-pressed") === "true").map(b => b.dataset.key));
    btns.forEach(b => b.addEventListener("click", () => {
      b.setAttribute("aria-pressed", String(b.getAttribute("aria-pressed") !== "true"));
      onChange(state(), true);
    }));
    onChange(state(), false);
    return state;
  }

  // Charts are drawn at the container's real pixel width, so 13px SVG text stays 13px on every screen.
  function responsiveChart(el, draw) {
    let width = 0;
    new ResizeObserver(() => {
      const w = Math.round(el.clientWidth);
      if (w && w !== width) { width = w; draw(width); }
    }).observe(el);
    return () => {
      if (!width) return;
      draw(width);
      el.classList.remove("swap");
      void el.offsetWidth;
      el.classList.add("swap");
    };
  }
  const scale = (d0, d1, r0, r1) => v => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const seeded = seed => { let s = seed; return () => (s = (s * 16807) % 2147483647) / 2147483647; };
  const gauss = r => (r() + r() + r() + r() - 2) * 1.73;
  const pathOf = pts => pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join("");

  /* ---------- Penang Pulse ---------- */
  const pulse = $("#pulse");
  if (pulse) {
    const DISTRICTS = [
      { id: "tl", name: "Timur Laut", short: "Timur Laut", bands: [72, 24, 4], pop: 545000 },
      { id: "bd", name: "Barat Daya", short: "Barat Daya", bands: [48, 34, 18], pop: 236000 },
      { id: "spu", name: "Seberang Perai Utara", short: "SP Utara", bands: [55, 33, 12], pop: 330000 },
      { id: "spt", name: "Seberang Perai Tengah", short: "SP Tengah", bands: [61, 30, 9], pop: 402000 },
      { id: "sps", name: "Seberang Perai Selatan", short: "SP Selatan", bands: [41, 38, 21], pop: 205000 }
    ];
    const BAND_COLOURS = [C.jade, C.mustard, C.rose];
    const BAND_NAMES = ["Under 1 km", "1 to 3 km", "Over 3 km"];

    // A district tile: three fill bands stacked from the floor up (jade near, mustard middle, rose far).
    const bandTile = d => {
      let y = 94, out = `<rect width="100" height="100" fill="${C.porcelain}"/>`;
      d.bands.forEach((p, i) => { const hgt = p * 0.88; y -= hgt; out += `<rect x="6" y="${y.toFixed(2)}" width="88" height="${hgt.toFixed(2)}" fill="${BAND_COLOURS[i]}"/>`; });
      // A porcelain diamond outline keeps the tile's motif visible over the data bands.
      return out + `<path d="M50 20 L80 50 L50 80 L20 50Z" fill="none" stroke="${C.porcelain}" stroke-width="3" opacity=".85"/><circle cx="50" cy="50" r="5" fill="${C.porcelain}"/>` + corners(C.peacock) + frame(C.ink);
    };
    const tablist = $("#district-tabs");
    tablist.innerHTML = DISTRICTS.map(d => `
      <button type="button" role="tab" id="tab-${d.id}" aria-controls="district-panel" aria-selected="${d.id === "sps"}" data-id="${d.id}">
        <span class="tile-wrap"><svg viewBox="0 0 100 100" aria-hidden="true">${bandTile(d)}</svg></span>
        <span class="name">${d.short.replace("SP ", '<abbr title="Seberang Perai">SP</abbr> ')}</span>
        <span class="stat">${d.bands[2]}% over 3 km</span>
      </button>`).join("");

    const panel = $("#district-panel");
    setupTabs(tablist, tab => {
      const d = DISTRICTS.find(x => x.id === tab.dataset.id);
      panel.setAttribute("aria-labelledby", tab.id);
      let left = 0;
      panel.innerHTML = `
        <h4>${d.name}</h4>
        <p class="pop">Population ${fmt(d.pop)}, share of residents by road distance to the nearest public clinic</p>
        <div class="band-bar" aria-hidden="true">${d.bands.map((p, i) => {
          const seg = `<span class="band-seg" style="left:${left}%;width:${p}%;background:${BAND_COLOURS[i]}"></span>`;
          left += p;
          return seg;
        }).join("")}</div>
        <ul class="band-legend">${d.bands.map((p, i) => `<li><span class="sw sq" style="background:${BAND_COLOURS[i]};border-color:${C.ink}"></span>${BAND_NAMES[i]}<strong>${p}%</strong></li>`).join("")}</ul>
        <p class="callout"><strong>About ${fmt(Math.round(d.pop * d.bands[2] / 100 / 500) * 500)} residents</strong>live more than 3 km from a public clinic.</p>`;
      $$(".map .district").forEach(g => g.classList.toggle("on", g.dataset.district === d.id));
    });

    // Schematic points, seeded so they are stable between reloads.
    const rand = seeded(7);
    const clusters = [
      [300, 175, 18, 14, "tl"], [180, 125, 24, 5, "tl"], [298, 335, 14, 8, "bd"], [215, 405, 18, 4, "bd"], [120, 300, 16, 4, "bd"],
      [425, 165, 24, 10, "spu"], [540, 110, 30, 4, "spu"], [500, 260, 34, 9, "spt"], [470, 420, 40, 6, "sps"]
    ];
    const cats = ["clinic", "school", "transit"];
    const CAT_COLOUR = { clinic: C.cobalt, school: C.roseDeep, transit: C.peacock };
    const shape = (cat, x, y) => {
      const common = `class="pt" data-cat="${cat}" fill="${CAT_COLOUR[cat]}" stroke="#fff" stroke-width="1.4"`;
      if (cat === "clinic") return `<circle ${common} cx="${x}" cy="${y}" r="5.2"/>`;
      if (cat === "school") return `<rect ${common} x="${x - 4.6}" y="${y - 4.6}" width="9.2" height="9.2"/>`;
      return `<path ${common} d="M${x} ${y - 6.2}L${x + 6.2} ${y}L${x} ${y + 6.2}L${x - 6.2} ${y}Z"/>`;
    };
    $("#points").innerHTML = clusters.flatMap(([cx, cy, spread, n]) => Array.from({ length: n }, () => {
      const cat = cats[Math.floor(rand() * 3)];
      return shape(cat, +(cx + (rand() - 0.5) * spread * 2).toFixed(1), +(cy + (rand() - 0.5) * spread * 2).toFixed(1));
    })).join("");
    setupToggles($("#map-toggles"), on => {
      $$(".map .pt").forEach(p => p.classList.toggle("off", !on.has(p.dataset.cat)));
    });

    // Keep map labels at a fixed on-screen size however wide the map renders.
    const mapSvg = $(".map svg");
    new ResizeObserver(() => {
      if (mapSvg.clientWidth) mapSvg.style.setProperty("--u", (600 / mapSvg.clientWidth).toFixed(3));
    }).observe(mapSvg);
  }

  /* ---------- Forecasting Lab ---------- */
  const forecast = $("#forecast");
  if (forecast) {
    const HORIZONS = [15, 30, 60, 90, 120];
    const MODELS = [
      { id: "naive", name: "Seasonal naive", colour: C.inkSoft, dash: "7 5", mae: [9.8, 11.2, 13.5, 15.1, 16.4], seed: 11 },
      { id: "gb", name: "Gradient boosting", colour: C.mustardDeep, mae: [6.1, 7.9, 10.6, 12.4, 14.0], seed: 23 },
      { id: "gru", name: "Small neural net (GRU)", colour: C.cobalt, mae: [6.4, 8.1, 10.4, 12.0, 13.6], seed: 37 },
      { id: "chronos", name: "Chronos", colour: C.jadeDeep, mae: [7.0, 8.3, 10.1, 11.6, 13.4], seed: 53 }
    ];
    const SENSORS = {
      s12: { seed: 12, base: 96, peak: 82, peakAt: 17 * 60 + 50, k: 1 },
      s47: { seed: 47, base: 64, peak: 58, peakAt: 18 * 60 + 5, k: 0.8 },
      s103: { seed: 103, base: 128, peak: 64, peakAt: 17 * 60 + 35, k: 1.2 }
    };
    const ORIGIN = 17 * 60, STEP = 5, PAST = 36, AHEAD = 24;
    const clock = m => `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;

    // MAE at any horizon, linear between the published horizons.
    const maeAt = (m, h) => {
      const xs = [0, ...HORIZONS], ys = [m.mae[0] * 0.4, ...m.mae];
      for (let i = 1; i < xs.length; i++) if (h <= xs[i]) return ys[i - 1] + (ys[i] - ys[i - 1]) * (h - xs[i - 1]) / (xs[i] - xs[i - 1]);
      return ys[ys.length - 1];
    };

    // Deterministic series: an evening peak plus seeded noise; each forecast is the actual plus smooth
    // seeded error whose mean size follows the MAE table, so relative accuracy matches it.
    const series = id => {
      const s = SENSORS[id], r = seeded(s.seed * 97);
      const actual = [];
      for (let t = -PAST; t <= AHEAD; t++) {
        const m = ORIGIN + t * STEP;
        actual.push({ t, v: s.base + s.peak * Math.exp(-(((m - s.peakAt) / 58) ** 2)) + 6 * Math.sin(m / 37 + s.seed) * s.k + gauss(r) * 3.2 * s.k });
      }
      const at = t => actual[t + PAST].v;
      const forecasts = {};
      MODELS.forEach(m => {
        const rr = seeded(m.seed * 131 + s.seed);
        let z = 0;
        const zs = Array.from({ length: AHEAD }, () => (z = 0.85 * z + 0.5 * gauss(rr)));
        // Normalise so the window's error equals the horizon-weighted MAE exactly, keeping the table's ranking.
        const target = zs.map((_, i) => maeAt(m, (i + 1) * STEP));
        const norm = zs.reduce((a, z, i) => a + Math.abs(z) * target[i], 0) / target.reduce((a, b) => a + b, 0);
        const pts = [{ t: 0, v: at(0) }];
        zs.forEach((zz, i) => {
          const t = i + 1;
          pts.push({ t, v: at(t) + target[i] * s.k * (zz / norm) });
        });
        const mae = pts.slice(1).reduce((a, p) => a + Math.abs(p.v - at(p.t)), 0) / AHEAD;
        forecasts[m.id] = { pts, mae };
      });
      return { actual, forecasts };
    };

    let sensor = "s12";
    let visible = new Set(MODELS.map(m => m.id));
    const fcEl = $("#forecast-chart"), hzEl = $("#horizon-chart"), maeList = $("#window-mae");

    const drawForecast = w => {
      const h = Math.round(Math.min(420, Math.max(300, w * 0.52)));
      const pad = { l: 46, r: 14, t: 34, b: 38 };
      const { actual, forecasts } = series(sensor);
      const vals = actual.map(p => p.v).concat(...MODELS.filter(m => visible.has(m.id)).map(m => forecasts[m.id].pts.map(p => p.v)));
      const lo = Math.floor((Math.min(...vals) - 5) / 25) * 25, hi = Math.ceil((Math.max(...vals) + 5) / 25) * 25;
      const x = scale(-PAST, AHEAD, pad.l, w - pad.r), y = scale(lo, hi, h - pad.b, pad.t);
      const hourStep = w < 520 ? 24 : 12;
      let g = `<rect x="${x(0)}" y="${pad.t}" width="${x(AHEAD) - x(0)}" height="${h - pad.b - pad.t}" fill="${C.sky}"/>`;
      g += `<text class="strong" x="${x(0) + 8}" y="${pad.t - 12}">Next 2 hours</text>`;
      for (let v = lo; v <= hi; v += 25) g += `<line x1="${pad.l}" x2="${w - pad.r}" y1="${y(v)}" y2="${y(v)}" stroke="${C.ink}" stroke-opacity=".1"/><text x="${pad.l - 8}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
      for (let t = -PAST; t <= AHEAD; t += hourStep) g += `<text x="${x(t)}" y="${h - pad.b + 22}" text-anchor="middle">${clock(ORIGIN + t * STEP)}</text>`;
      g += `<line x1="${x(0)}" x2="${x(0)}" y1="${pad.t}" y2="${h - pad.b}" stroke="${C.ink}" stroke-width="1.5"/>`;
      g += `<line x1="${pad.l}" x2="${w - pad.r}" y1="${h - pad.b}" y2="${h - pad.b}" stroke="${C.ink}" stroke-width="1.5"/>`;
      let marks = `<path d="${pathOf(actual.map(p => [x(p.t), y(p.v)]))}" fill="none" stroke="${C.ink}" stroke-width="2.5" stroke-linejoin="round"/>`;
      MODELS.filter(m => visible.has(m.id)).forEach(m => {
        marks += `<path d="${pathOf(forecasts[m.id].pts.map(p => [x(p.t), y(p.v)]))}" fill="none" stroke="${m.colour}" stroke-width="2.75" stroke-linejoin="round" ${m.dash ? `stroke-dasharray="${m.dash}"` : ""}/>`;
      });
      fcEl.innerHTML = `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Traffic flow for ${$("#sensor-tabs [aria-selected=true]").textContent}, actual and forecast, vehicles per 5 minutes">${g}<g class="marks-layer">${marks}</g></svg>`;
      maeList.innerHTML = MODELS.map(m => `<li><span class="sw line" style="background:${m.colour}"></span>${m.name}<strong>${forecasts[m.id].mae.toFixed(1)}</strong></li>`).join("");
    };

    const drawHorizon = w => {
      const h = Math.round(Math.min(340, Math.max(260, w * 0.42)));
      const pad = { l: 40, r: 18, t: 18, b: 40 };
      const x = i => pad.l + 20 + i * ((w - pad.l - pad.r - 40) / (HORIZONS.length - 1));
      const y = scale(0, 18, h - pad.b, pad.t);
      let g = "";
      for (let v = 0; v <= 18; v += 6) g += `<line x1="${pad.l}" x2="${w - pad.r}" y1="${y(v)}" y2="${y(v)}" stroke="${C.ink}" stroke-opacity="${v ? .1 : 1}" stroke-width="${v ? 1 : 1.5}"/><text x="${pad.l - 8}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
      HORIZONS.forEach((hz, i) => { g += `<text x="${x(i)}" y="${h - pad.b + 22}" text-anchor="middle">${hz} min</text>`; });
      let marks = "";
      MODELS.filter(m => visible.has(m.id)).forEach(m => {
        marks += `<path d="${pathOf(m.mae.map((v, i) => [x(i), y(v)]))}" fill="none" stroke="${m.colour}" stroke-width="2.75" ${m.dash ? `stroke-dasharray="${m.dash}"` : ""}/>`;
        marks += m.mae.map((v, i) => `<circle cx="${x(i)}" cy="${y(v)}" r="4.5" fill="${m.colour}" stroke="#fff" stroke-width="1.5"/>`).join("");
      });
      hzEl.innerHTML = `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Mean absolute error by forecast horizon for the four models">${g}<g class="marks-layer">${marks}</g></svg>`;
    };

    const redrawForecast = responsiveChart(fcEl, drawForecast);
    const redrawHorizon = responsiveChart(hzEl, drawHorizon);
    setupTabs($("#sensor-tabs"), tab => { sensor = tab.dataset.key; redrawForecast(); });
    setupToggles($("#model-toggles"), (on, user) => {
      visible = on;
      if (user) { redrawForecast(); redrawHorizon(); }
    });
  }

  /* ---------- LLM Eval Lab ---------- */
  const llm = $("#llm");
  if (llm) {
    const ROLE_COLOUR = { frontier: C.cobalt, ft: C.jadeDeep, open: C.mustardDeep, base: C.roseDeep };
    const ROLE_TINT = { frontier: C.cobalt, ft: C.jade, open: C.mustard, base: C.rose };
    // [model, role, score, low, high, cost per 1k, cost label, latency]
    const TASKS = {
      sentiment: { metric: "Accuracy", rows: [
        ["Frontier model", "frontier", 87, 84, 90, 2.10, "$2.10", "900 ms"],
        ["Fine-tuned 1B", "ft", 84, 81, 87, 0.04, "$0.04", "38 ms"],
        ["Open 8B, zero-shot", "open", 79, 75, 83, 0.12, "$0.12", "210 ms"],
        ["TF-IDF + logistic", "base", 71, 67, 75, 0.007, "<$0.01", "1 ms"]] },
      entities: { metric: "F1", rows: [
        ["Frontier model", "frontier", 83, 80, 86, 2.40, "$2.40", "1.1 s"],
        ["Fine-tuned 1B", "ft", 78, 74, 81, 0.05, "$0.05", "45 ms"],
        ["Open 8B, zero-shot", "open", 70, 66, 74, 0.14, "$0.14", "260 ms"],
        ["CRF baseline", "base", 62, 58, 66, 0.007, "<$0.01", "3 ms"]] },
      summaries: { metric: "Faithfulness", rows: [
        ["Frontier model", "frontier", 82, 79, 85, 4.80, "$4.80", "2.4 s"],
        ["Open 8B, zero-shot", "open", 71, 67, 75, 0.30, "$0.30", "640 ms"],
        ["Fine-tuned 1B", "ft", 66, 62, 70, 0.09, "$0.09", "120 ms"],
        ["Extractive baseline", "base", 58, 54, 62, 0.007, "<$0.01", "5 ms"]] }
    };
    const pct = scale(50, 100, 0, 100);
    let task = "sentiment";
    const body = $("#board tbody"), metricHead = $("#metric-head"), scEl = $("#scatter");

    const drawBoard = () => {
      const t = TASKS[task];
      metricHead.textContent = `${t.metric}, with 95% interval`;
      body.innerHTML = t.rows.map(([name, role, s, lo, hi, , costLabel, lat]) => `
        <tr>
          <th scope="row"><span class="model-name"><span class="sw" style="background:${ROLE_COLOUR[role]};border-color:${C.ink}"></span>${esc(name)}</span></th>
          <td><div class="ci"><b>${s}<small>${lo} to ${hi}</small></b>
            <span class="ci-track" aria-hidden="true"><span class="ci-range" style="left:${pct(lo)}%;width:${pct(hi) - pct(lo)}%;background:${ROLE_TINT[role]}"></span><span class="ci-dot" style="left:${pct(s)}%;background:${ROLE_COLOUR[role]}"></span></span></div></td>
          <td class="num">${esc(costLabel)}</td>
          <td class="num">${lat}</td>
        </tr>`).join("");
    };

    const drawScatter = w => {
      const h = Math.round(Math.min(380, Math.max(300, w * 0.5)));
      const pad = { l: 44, r: 16, t: 18, b: 32 };
      const lx = scale(Math.log10(0.005), Math.log10(10), pad.l, w - pad.r);
      const x = v => lx(Math.log10(v));
      const y = scale(50, 95, h - pad.b, pad.t);
      let g = "";
      for (let v = 50; v <= 90; v += 10) g += `<line x1="${pad.l}" x2="${w - pad.r}" y1="${y(v)}" y2="${y(v)}" stroke="${C.ink}" stroke-opacity=".1"/><text x="${pad.l - 8}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
      [[0.01, "$0.01"], [0.1, "$0.10"], [1, "$1"], [10, "$10"]].forEach(([v, l]) => {
        g += `<line x1="${x(v)}" x2="${x(v)}" y1="${pad.t}" y2="${h - pad.b}" stroke="${C.ink}" stroke-opacity=".1"/><text x="${x(v)}" y="${h - pad.b + 20}" text-anchor="${v === 10 ? "end" : "middle"}">${l}</text>`;
      });
      g += `<line x1="${pad.l}" x2="${w - pad.r}" y1="${h - pad.b}" y2="${h - pad.b}" stroke="${C.ink}" stroke-width="1.5"/>`;
      const marks = TASKS[task].rows.map(([name, role, s, lo, hi, cost]) => {
        const px = x(cost), py = y(s), right = px > w * 0.62;
        return `<line x1="${px}" x2="${px}" y1="${y(lo)}" y2="${y(hi)}" stroke="${ROLE_COLOUR[role]}" stroke-width="2.5" stroke-linecap="round"/>
          <circle cx="${px}" cy="${py}" r="7.5" fill="${ROLE_COLOUR[role]}" stroke="${C.ink}" stroke-width="2"/>
          <text class="strong" x="${right ? px + 9 : px + 13}" y="${right ? py - 15 : py + 4.5}" text-anchor="${right ? "end" : "start"}">${esc(name)}</text>`;
      }).join("");
      scEl.innerHTML = `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${TASKS[task].metric} against cost per 1k items for each model">${g}<g class="marks-layer">${marks}</g></svg>`;
    };

    const redrawScatter = responsiveChart(scEl, drawScatter);
    setupTabs($("#task-tabs"), tab => {
      task = tab.dataset.key;
      $("#task-panel").setAttribute("aria-labelledby", tab.id);
      drawBoard();
      redrawScatter();
    });
  }

  /* ---------- Experiments filter ---------- */
  const filters = $("#filters");
  if (filters) {
    const btns = $$("button", filters);
    const items = $$("#tool-list .tool");
    const count = $("#tool-count");
    btns.forEach(b => b.addEventListener("click", () => {
      btns.forEach(x => x.setAttribute("aria-pressed", String(x === b)));
      const cat = b.dataset.cat;
      let shown = 0;
      items.forEach(it => { it.hidden = cat !== "all" && it.dataset.cat !== cat; if (!it.hidden) shown += 1; });
      count.textContent = `Showing ${shown} of ${items.length} tools`;
    }));
  }
})();
