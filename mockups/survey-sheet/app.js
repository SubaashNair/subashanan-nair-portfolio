/* Survey Sheet prototype: shared behaviour for every page. All data is illustrative. */
"use strict";

/* ---------- helpers ---------- */
const NS = "http://www.w3.org/2000/svg";

// Park-Miller generator, same as the approved mockup, so every figure is stable between reloads.
function seeded(seed) {
  let s = seed;
  return () => (s = (s * 16807) % 2147483647) / 2147483647;
}

function svg(tag, attrs, parent) {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(n);
  return n;
}

function label(parent, x, y, str, attrs = {}) {
  const t = svg("text", { x, y, ...attrs }, parent);
  t.textContent = str;
  return t;
}

const scale = (d0, d1, r0, r1) => v => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
const points = (xs, ys) => xs.map((x, i) => `${x.toFixed(1)},${ys[i].toFixed(1)}`).join(" ");
const mean = a => a.reduce((s, v) => s + v, 0) / a.length;

// Charts are drawn at the host's real pixel width, so 13px SVG text renders at 13px on any screen.
function mount(host, draw) {
  let width = 0;
  const render = () => {
    width = host.clientWidth;
    if (width) draw(width);
  };
  new ResizeObserver(() => { if (host.clientWidth !== width) render(); }).observe(host);
  render();
  return render;
}

function canvas(host, w, h, title) {
  const s = svg("svg", { viewBox: `0 0 ${w} ${h}`, class: "chart", role: "img", "aria-label": title });
  host.replaceChildren(s);
  return s;
}

function yAxis(s, ticks, y, x0, x1, fmt = String) {
  const g = svg("g", {}, s);
  ticks.forEach(t => {
    svg("line", { x1: x0, x2: x1, y1: y(t), y2: y(t), class: "grid" }, g);
    label(g, x0 - 8, y(t) + 4, fmt(t), { "text-anchor": "end" });
  });
}

function xAxis(s, ticks, x, y0, fmt = String) {
  const g = svg("g", {}, s);
  ticks.forEach(t => label(g, x(t), y0 + 20, fmt(t), { "text-anchor": "middle" }));
}

// Roving-tabindex tabs with arrow, Home and End keys. Returns a select(key) function.
function tabs(list, onSelect) {
  const items = [...list.querySelectorAll('[role="tab"]')];
  const select = (tab, focus) => {
    items.forEach(t => {
      const on = t === tab;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
    });
    const panel = document.getElementById(tab.getAttribute("aria-controls"));
    if (panel) panel.setAttribute("aria-labelledby", tab.id);
    if (focus) tab.focus();
    onSelect(tab.dataset.key);
  };
  items.forEach((t, i) => {
    t.addEventListener("click", () => select(t));
    t.addEventListener("keydown", e => {
      const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      let j = -1;
      if (step) j = (i + step + items.length) % items.length;
      else if (e.key === "Home") j = 0;
      else if (e.key === "End") j = items.length - 1;
      if (j < 0) return;
      e.preventDefault();
      select(items[j], true);
    });
  });
  select(items.find(t => t.getAttribute("aria-selected") === "true") || items[0]);
  return key => select(items.find(t => t.dataset.key === key));
}

function toggles(group, onChange) {
  group.querySelectorAll("button[aria-pressed]").forEach(b => b.addEventListener("click", () => {
    const on = b.getAttribute("aria-pressed") !== "true";
    b.setAttribute("aria-pressed", String(on));
    onChange(b.dataset.key, on);
  }));
}

/* ---------- data ---------- */
const DISTRICTS = [
  { key: "tl", name: "Timur Laut", short: "Timur Laut", bands: [72, 24, 4], pop: 545000 },
  { key: "bd", name: "Barat Daya", short: "Barat Daya", bands: [48, 34, 18], pop: 236000 },
  { key: "spu", name: "Seberang Perai Utara", short: "S. P. Utara", bands: [55, 33, 12], pop: 330000 },
  { key: "spt", name: "Seberang Perai Tengah", short: "S. P. Tengah", bands: [61, 30, 9], pop: 402000 },
  { key: "sps", name: "Seberang Perai Selatan", short: "S. P. Selatan", bands: [41, 38, 21], pop: 205000 },
];
const BAND_COLOURS = ["var(--forest)", "var(--contour)", "var(--magenta)"];

const HORIZONS = [15, 30, 60, 90, 120];
const MODELS = [
  { key: "naive", name: "Seasonal naive", colour: "var(--ink-soft)", dash: "6 4", mae: [9.8, 11.2, 13.5, 15.1, 16.4] },
  { key: "gbm", name: "Gradient boosting", colour: "var(--contour)", mae: [6.1, 7.9, 10.6, 12.4, 14.0] },
  { key: "gru", name: "Small neural net (GRU)", colour: "var(--sea-line)", mae: [6.4, 8.1, 10.4, 12.0, 13.6] },
  { key: "chronos", name: "Chronos", colour: "var(--magenta)", width: 2.75, mae: [7.0, 8.3, 10.1, 11.6, 13.4] },
];

const KIND_COLOUR = { frontier: "var(--sea-line)", ft: "var(--magenta)", open: "var(--contour)", base: "var(--ink-soft)" };
const row = (model, kind, score, low, high, cost, latency) => ({ model, kind, score, low, high, cost, latency });
const TASKS = {
  sentiment: {
    name: "Manglish sentiment", metric: "Accuracy",
    rows: [
      row("Frontier model", "frontier", 87, 84, 90, 2.10, "900 ms"),
      row("Fine-tuned 1B", "ft", 84, 81, 87, 0.04, "38 ms"),
      row("Open 8B, zero-shot", "open", 79, 75, 83, 0.12, "210 ms"),
      row("TF-IDF + logistic", "base", 71, 67, 75, null, "1 ms"),
    ],
  },
  entities: {
    name: "BM entity extraction", metric: "F1",
    rows: [
      row("Frontier model", "frontier", 83, 80, 86, 2.40, "1.1 s"),
      row("Fine-tuned 1B", "ft", 78, 74, 81, 0.05, "45 ms"),
      row("Open 8B, zero-shot", "open", 70, 66, 74, 0.14, "260 ms"),
      row("CRF baseline", "base", 62, 58, 66, null, "3 ms"),
    ],
  },
  summaries: {
    name: "BM summaries", metric: "Faithfulness",
    rows: [
      row("Frontier model", "frontier", 82, 79, 85, 4.80, "2.4 s"),
      row("Open 8B, zero-shot", "open", 71, 67, 75, 0.30, "640 ms"),
      row("Fine-tuned 1B", "ft", 66, 62, 70, 0.09, "120 ms"),
      row("Extractive baseline", "base", 58, 54, 62, null, "5 ms"),
    ],
  },
};
const UNDER_A_CENT = 0.007; // where "<$0.01" rows sit on the log axis
const costText = c => (c === null ? "<$0.01" : `$${c.toFixed(2)}`);

/* ---------- map ---------- */
const ISLAND = "M95 120 C130 95 175 100 205 105 C235 110 255 100 280 115 C300 125 318 140 322 160 C326 185 312 205 318 230 C324 260 315 290 322 320 C330 345 318 370 300 395 C285 415 262 432 240 438 C210 445 180 430 160 420 C130 405 110 385 100 360 C85 330 78 300 80 270 C82 240 70 210 75 180 C78 155 82 135 95 120 Z";
const MAINLAND = "M380 0 L600 0 L600 500 L395 500 C400 470 385 440 392 410 C398 380 385 350 390 320 C395 290 378 260 385 230 C390 200 375 170 382 140 C388 110 372 80 378 50 C380 30 378 15 380 0 Z";
const CONTOURS = [
  [190, 235, 92, 120, -12], [188, 232, 70, 94, -8], [185, 228, 50, 70, -4], [183, 224, 32, 46, 0],
  [181, 221, 15, 22, 0], [150, 360, 40, 28, 0], [150, 360, 20, 13, 0],
];
// Schematic district boundaries: one diagonal across the island, two lines across the mainland.
const islandSplitY = x => 170 + (x - 70) * (150 / 260);
const SHAPES = {
  tl: { land: "island", poly: "0,0 360,0 360,338 0,130", has: (x, y) => y < islandSplitY(x) },
  bd: { land: "island", poly: "0,130 360,338 360,500 0,500", has: (x, y) => y >= islandSplitY(x) },
  spu: { land: "main", poly: "360,0 600,0 600,205 360,205", has: (x, y) => y < 205 },
  spt: { land: "main", poly: "360,205 600,205 600,360 360,360", has: (x, y) => y >= 205 && y < 360 },
  sps: { land: "main", poly: "360,360 600,360 600,500 360,500", has: (x, y) => y >= 360 },
};
// [x, y, spread, weight, district]
const CLUSTERS = [
  [292, 170, 22, 16, "tl"], [190, 132, 26, 6, "tl"], [245, 225, 24, 7, "tl"],
  [296, 335, 16, 8, "bd"], [220, 400, 20, 4, "bd"], [118, 300, 18, 4, "bd"],
  [425, 170, 26, 11, "spu"], [450, 70, 26, 4, "spu"], [540, 120, 30, 3, "spu"],
  [500, 262, 34, 9, "spt"], [428, 300, 22, 5, "spt"],
  [470, 420, 38, 6, "sps"],
];
// [first line, second line, x, y, anchor]
const PLACES = [
  ["George", "Town", 236, 136, "middle"], ["Balik", "Pulau", 126, 248, "middle"], ["Bayan", "Lepas", 232, 372, "middle"],
  ["Butterworth", "", 592, 112, "end"], ["Bukit", "Mertajam", 592, 296, "end"], ["Nibong", "Tebal", 592, 438, "end"],
];
const CATS = ["clinic", "school", "transit"];

function insideFill(path, x, y) {
  try { return path.isPointInFill(new DOMPoint(x, y)); } catch { return true; }
}

function drawMap(fig, { districts = false, total = 70, spreadK = 1 } = {}) {
  const host = fig.querySelector("[data-map]");
  const s = svg("svg", {
    viewBox: "0 0 600 500", class: districts ? "map dense" : "map", role: "img",
    "aria-label": "Schematic map of Penang Island and Seberang Perai with public clinics, schools and transit stops plotted as points",
  });
  host.replaceChildren(s);
  new ResizeObserver(() => s.style.setProperty("--k", (600 / (s.clientWidth || 600)).toFixed(3))).observe(s);

  const defs = svg("defs", {}, s);
  svg("path", { d: ISLAND }, svg("clipPath", { id: "clip-island" }, defs));
  svg("path", { d: MAINLAND }, svg("clipPath", { id: "clip-main" }, defs));
  svg("rect", { width: 600, height: 500, class: "sea" }, s);
  const lands = { main: svg("path", { d: MAINLAND, class: "land" }, s), island: svg("path", { d: ISLAND, class: "land" }, s) };
  const contours = svg("g", { class: "contours", "clip-path": "url(#clip-island)" }, s);
  CONTOURS.forEach(([cx, cy, rx, ry, rot]) => svg("ellipse", { cx, cy, rx, ry, transform: `rotate(${rot} ${cx} ${cy})` }, contours));
  const hill = svg("g", { class: "contours", "clip-path": "url(#clip-main)" }, s);
  [[34, 22], [20, 13], [8, 6]].forEach(([rx, ry]) => svg("ellipse", { cx: 548, cy: 222, rx, ry }, hill));

  // Points, with a largest-first allocation so the drawn total matches `total` exactly.
  const rand = seeded(7);
  const weight = CLUSTERS.reduce((a, c) => a + c[3], 0);
  const counts = CLUSTERS.map(c => Math.floor((c[3] * total) / weight));
  for (let i = 0, rem = total - counts.reduce((a, b) => a + b, 0); i < rem; i++) counts[i]++;
  const g = svg("g", {}, s);
  const pts = [];
  CLUSTERS.forEach(([cx, cy, spread, , d], i) => {
    const shape = SHAPES[d];
    for (let n = 0; n < counts[i]; n++) {
      let x = cx, y = cy;
      for (let t = 0; t < 60; t++) {
        const px = cx + (rand() + rand() - 1) * spread * spreadK;
        const py = cy + (rand() + rand() - 1) * spread * spreadK;
        if (shape.has(px, py) && insideFill(lands[shape.land], px, py)) { x = px; y = py; break; }
      }
      const cat = CATS[Math.floor(rand() * 3)];
      const c = svg("circle", { cx: x.toFixed(1), cy: y.toFixed(1), r: 4, fill: `var(--${cat})`, stroke: "#f6f8f4", "stroke-width": 1.2, class: "pt" }, g);
      pts.push({ el: c, cat, d });
    }
  });

  const washes = {};
  if (districts) {
    Object.entries(SHAPES).forEach(([key, sh]) => {
      washes[key] = svg("polygon", { points: sh.poly, class: "wash", "clip-path": `url(#clip-${sh.land})` }, s);
    });
    const b1 = svg("g", { "clip-path": "url(#clip-island)" }, s);
    svg("line", { x1: 0, y1: islandSplitY(0), x2: 360, y2: islandSplitY(360), class: "boundary" }, b1);
    const b2 = svg("g", { "clip-path": "url(#clip-main)" }, s);
    [205, 360].forEach(y => svg("line", { x1: 360, x2: 600, y1: y, y2: y, class: "boundary" }, b2));
  }

  svg("line", { x1: 322, y1: 300, x2: 390, y2: 290, class: "bridge" }, s);
  svg("line", { x1: 303, y1: 398, x2: 393, y2: 430, class: "bridge" }, s);
  PLACES.forEach(([a, b, x, y, anchor]) => {
    const t = svg("text", { class: "place", x, y, "text-anchor": anchor }, s);
    svg("tspan", { x }, t).textContent = a;
    if (b) svg("tspan", { x, dy: "1.15em" }, t).textContent = b;
  });
  label(s, 30, 60, "Selat Melaka", { class: "water" });
  label(s, 360, 282, "Penang Strait", { class: "water", transform: "rotate(-86 360 282)" });

  const ticks = svg("g", { stroke: "var(--ink)", "stroke-width": 1 }, s);
  [150, 300, 450].forEach(x => svg("line", { x1: x, x2: x, y1: 0, y2: 8 }, ticks));
  [125, 250, 375].forEach(y => svg("line", { x1: 0, x2: 8, y1: y, y2: y }, ticks));
  ["100.25°E", "100.35°E", "100.45°E"].forEach((t, i) => label(s, 150 + i * 150, 25, t, { class: "tick", "text-anchor": "middle" }));
  ["5.45°N", "5.35°N", "5.25°N"].forEach((t, i) => label(s, 12, 121 + i * 125, t, { class: "tick" }));
  // North arrow, bottom left of the sea.
  const north = svg("g", { class: "north", transform: "translate(40 430)" }, s);
  svg("path", { d: "M0 -26 L9 6 L0 0 L-9 6 Z" }, north);
  label(north, 0, 30, "N", { class: "tick", "text-anchor": "middle" });

  fig.querySelectorAll(".legend button[data-cat]").forEach(btn => btn.addEventListener("click", () => {
    const on = btn.getAttribute("aria-pressed") !== "true";
    btn.setAttribute("aria-pressed", String(on));
    pts.forEach(p => { if (p.cat === btn.dataset.cat) p.el.classList.toggle("off", !on); });
  }));
  return { pts, washes };
}

/* ---------- charts ---------- */
function distanceBars(host, w, selected) {
  const labelW = 104, rowH = 30, h = DISTRICTS.length * rowH + 4;
  const s = canvas(host, w, h, "Share of residents by distance to the nearest public clinic, for each district: under 1 km, 1 to 3 km, over 3 km");
  const x = scale(0, 100, labelW, w - 2);
  DISTRICTS.forEach((d, i) => {
    const y = 4 + i * rowH;
    label(s, 0, y + 15, d.short, { class: selected === d.key ? "strong" : "" });
    const g = svg("g", { opacity: selected && selected !== d.key ? 0.38 : 1 }, s);
    let acc = 0;
    d.bands.forEach((v, j) => {
      svg("rect", { x: x(acc), y, width: x(acc + v) - x(acc), height: 20, fill: BAND_COLOURS[j] }, g);
      acc += v;
    });
  });
}

function horizonChart(host, w, h) {
  const m = { l: 34, r: 22, t: 12, b: 48 };
  const s = canvas(host, w, h, "Mean absolute error by forecast horizon for four models. Lower is better.");
  const x = scale(15, 120, m.l, w - m.r), y = scale(0, 18, h - m.b, m.t);
  yAxis(s, [0, 6, 12, 18], y, m.l, w - m.r);
  xAxis(s, HORIZONS, x, h - m.b);
  svg("line", { x1: m.l, x2: w - m.r, y1: y(0), y2: y(0), class: "base" }, s);
  MODELS.forEach(md => {
    svg("polyline", {
      points: points(HORIZONS.map(x), md.mae.map(y)), fill: "none", stroke: md.colour,
      "stroke-width": md.width || 2, ...(md.dash ? { "stroke-dasharray": md.dash } : {}),
    }, s);
    md.mae.forEach((v, i) => svg("circle", { cx: x(HORIZONS[i]), cy: y(v), r: 3, fill: md.colour }, s));
  });
  label(s, w - m.r, h - 4, "Minutes ahead", { "text-anchor": "end" });
}

function ciChart(host, w, task) {
  const labelW = 136, rowH = 34, h = task.rows.length * rowH + 34;
  const s = canvas(host, w, h, `${task.metric} with 95% intervals on ${task.name}`);
  const x = scale(50, 100, labelW, w - 18);
  [50, 75, 100].forEach(t => {
    svg("line", { x1: x(t), x2: x(t), y1: 4, y2: h - 26, class: "grid" }, s);
    label(s, x(t), h - 6, String(t), { "text-anchor": "middle" });
  });
  task.rows.forEach((r, i) => {
    const y = 20 + i * rowH, c = KIND_COLOUR[r.kind];
    label(s, 0, y + 4, r.model, { class: r.kind === "ft" ? "strong" : "" });
    svg("line", { x1: x(r.low), x2: x(r.high), y1: y, y2: y, stroke: c, "stroke-width": 2.5 }, s);
    svg("circle", { cx: x(r.score), cy: y, r: 6, fill: c }, s);
  });
}

function ciBar(r) {
  const W = 180, s = svg("svg", { width: W, height: 20, viewBox: `0 0 ${W} 20`, "aria-hidden": "true" });
  const x = scale(50, 100, 6, W - 6), c = KIND_COLOUR[r.kind];
  [50, 75, 100].forEach(t => svg("line", { x1: x(t), x2: x(t), y1: 2, y2: 18, stroke: "rgba(29,43,42,.2)" }, s));
  svg("line", { x1: x(r.low), x2: x(r.high), y1: 10, y2: 10, stroke: c, "stroke-width": 2.5 }, s);
  svg("circle", { cx: x(r.score), cy: 10, r: 5.5, fill: c }, s);
  return s;
}

function costChart(host, w, task) {
  const h = w < 520 ? 300 : 340, m = { l: 40, r: 18, t: 30, b: 48 };
  const s = canvas(host, w, h, `Cost per 1,000 items on a log scale against ${task.metric.toLowerCase()} for ${task.name}, one point per model`);
  const lx = scale(Math.log10(0.005), Math.log10(10), m.l, w - m.r);
  const x = v => lx(Math.log10(v === null ? UNDER_A_CENT : v));
  const y = scale(50, 95, h - m.b, m.t);
  yAxis(s, [50, 60, 70, 80, 90], y, m.l, w - m.r);
  [0.01, 0.1, 1, 10].forEach(v => svg("line", { x1: x(v), x2: x(v), y1: m.t, y2: h - m.b, class: "grid" }, s));
  xAxis(s, [0.01, 0.1, 1, 10], x, h - m.b, v => (v < 1 ? `$${v.toFixed(2)}` : `$${v}`));
  svg("line", { x1: m.l, x2: w - m.r, y1: h - m.b, y2: h - m.b, class: "base" }, s);
  label(s, 0, 14, task.metric);
  label(s, w - m.r, h - 4, "Cost per 1,000 items, log scale", { "text-anchor": "end" });
  task.rows.forEach(r => {
    const cx = x(r.cost), cy = y(r.score), c = KIND_COLOUR[r.kind];
    svg("line", { x1: cx, x2: cx, y1: y(r.low), y2: y(r.high), stroke: c, "stroke-width": 2 }, s);
    svg("circle", { cx, cy, r: 6.5, fill: c, stroke: "#f6f8f4", "stroke-width": 1.5 }, s);
    const right = cx < w * 0.6;
    label(s, cx + (right ? 11 : -11), right ? cy + 4 : cy - 9, r.model, { "text-anchor": right ? "start" : "end", class: "lbl" });
  });
}

/* ---------- forecasting ---------- */
const SENSORS = {
  s12: { name: "Sensor 12", base: 55, amp: 140, k: 1, seed: 1201 },
  s47: { name: "Sensor 47", base: 95, amp: 170, k: 1.2, seed: 4703 },
  s103: { name: "Sensor 103", base: 32, amp: 82, k: 0.65, seed: 10307 },
};
const START_HOUR = 11, NOW = 24, STEPS = 33; // 15 minute steps from 11:00; forecasts start at 17:00
const gauss = (t, mu, sd) => Math.exp(-((t - mu) ** 2) / (2 * sd * sd));

function maeAt(md, mins) {
  const i = HORIZONS.findIndex(hz => hz >= mins);
  if (HORIZONS[i] === mins) return md.mae[i];
  const f = (mins - HORIZONS[i - 1]) / (HORIZONS[i] - HORIZONS[i - 1]);
  return md.mae[i - 1] + f * (md.mae[i] - md.mae[i - 1]);
}

// Deterministic actual series plus one forecast per model whose error scales with that model's MAE.
function sensorData(key) {
  const sn = SENSORS[key], rand = seeded(sn.seed);
  const actual = Array.from({ length: STEPS }, (_, i) => {
    const t = START_HOUR + i / 4;
    const shape = 0.35 * gauss(t, 8, 1.5) + 0.22 * gauss(t, 13, 1) + gauss(t, 17.7, 1.4);
    return sn.base + sn.amp * shape + (rand() - 0.5) * 12 * sn.k;
  });
  const forecasts = {};
  MODELS.forEach(md => {
    const bias = (rand() < 0.5 ? -1 : 1) * (0.95 + 0.1 * rand());
    const errs = Array.from({ length: STEPS - 1 - NOW }, (_, k) => sn.k * maeAt(md, (k + 1) * 15) * (bias + 0.3 * (rand() * 2 - 1)));
    forecasts[md.key] = {
      values: errs.map((e, k) => Math.max(0, actual[NOW + 1 + k] + e)),
      mae: mean(errs.map(Math.abs)),
    };
  });
  return { actual, forecasts };
}

function forecastChart(host, w, sensorKey, data, visible) {
  const h = w < 520 ? 290 : 350, m = { l: 40, r: 14, t: 30, b: 32 };
  const s = canvas(host, w, h, `Actual traffic at ${SENSORS[sensorKey].name} from 11:00 to 19:00, with two hour forecasts made at 17:00`);
  const all = [...data.actual, ...Object.values(data.forecasts).flatMap(f => f.values)];
  const top = Math.ceil((Math.max(...all) * 1.05) / 50) * 50;
  const step = top > 200 ? 100 : 50;
  const x = scale(0, STEPS - 1, m.l, w - m.r), y = scale(0, top, h - m.b, m.t);
  svg("rect", { x: x(NOW), y: m.t, width: x(STEPS - 1) - x(NOW), height: h - m.b - m.t, class: "zone" }, s);
  yAxis(s, Array.from({ length: top / step + 1 }, (_, i) => i * step), y, m.l, w - m.r);
  xAxis(s, [0, 8, 16, 24, 32], x, h - m.b, i => `${START_HOUR + i / 4}:00`);
  svg("line", { x1: m.l, x2: w - m.r, y1: y(0), y2: y(0), class: "base" }, s);
  svg("line", { x1: x(NOW), x2: x(NOW), y1: m.t - 6, y2: h - m.b, class: "now" }, s);
  label(s, 0, 14, "Vehicles per 15 min");
  label(s, w - m.r, 14, "Next 2 hours", { "text-anchor": "end" });
  const idx = data.actual.map((_, i) => i);
  svg("polyline", { points: points(idx.map(x), data.actual.map(y)), fill: "none", stroke: "var(--ink)", "stroke-width": 2 }, s);
  MODELS.filter(md => visible[md.key]).forEach(md => {
    const vals = [data.actual[NOW], ...data.forecasts[md.key].values];
    svg("polyline", {
      points: points(vals.map((_, i) => x(NOW + i)), vals.map(y)), fill: "none", stroke: md.colour,
      "stroke-width": md.width || 2, "stroke-linejoin": "round", ...(md.dash ? { "stroke-dasharray": md.dash } : {}),
    }, s);
  });
}

function initForecasting() {
  const host = document.getElementById("forecast-chart");
  if (!host) return;
  const visible = Object.fromEntries(MODELS.map(md => [md.key, true]));
  let sensor = "s12", data = sensorData(sensor);
  const redraw = mount(host, w => forecastChart(host, w, sensor, data, visible));
  const readouts = document.querySelectorAll("[data-mae]");
  tabs(document.getElementById("sensor-tabs"), key => {
    sensor = key;
    data = sensorData(key);
    readouts.forEach(el => { el.textContent = `MAE ${data.forecasts[el.dataset.mae].mae.toFixed(1)}`; });
    redraw();
  });
  toggles(document.getElementById("model-toggles"), (key, on) => { visible[key] = on; redraw(); });
}

/* ---------- LLM eval ---------- */
function initLeaderboard() {
  const body = document.getElementById("board-body");
  if (!body) return;
  const costHost = document.getElementById("cost-chart");
  let task = TASKS.sentiment;
  const redraw = mount(costHost, w => costChart(costHost, w, task));
  tabs(document.getElementById("task-tabs"), key => {
    task = TASKS[key];
    document.querySelectorAll("[data-metric]").forEach(el => { el.textContent = task.metric; });
    document.querySelectorAll("[data-task-name]").forEach(el => { el.textContent = task.name; });
    body.replaceChildren(...task.rows.map(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<th scope="row"><span class="model"><span class="sw"></span></span></th>
        <td class="num"></td><td><span class="ci"><span class="num"></span></span></td><td class="num"></td><td class="num"></td>`;
      tr.querySelector(".sw").style.background = KIND_COLOUR[r.kind];
      tr.querySelector(".model").append(r.model);
      tr.children[1].textContent = r.score;
      tr.querySelector(".ci .num").textContent = `${r.low} to ${r.high}`;
      tr.querySelector(".ci").append(ciBar(r));
      tr.children[3].textContent = costText(r.cost);
      tr.children[4].textContent = r.latency;
      return tr;
    }));
    redraw();
  });
}

/* ---------- Penang Pulse ---------- */
function initPenang(fig, map) {
  const panel = document.getElementById("district-panel");
  const counts = {};
  map.pts.forEach(p => {
    counts[p.d] = counts[p.d] || { clinic: 0, school: 0, transit: 0 };
    counts[p.d][p.cat]++;
  });
  const byFar = [...DISTRICTS].sort((a, b) => b.bands[2] - a.bands[2]).map(d => d.key);
  const rankWord = ["the highest", "the second highest", "the third highest", "the fourth highest", "the lowest"];
  const f = name => panel.querySelector(`[data-f="${name}"]`);
  const barsHost = f("bars");
  let current = "tl";
  const redrawBars = mount(barsHost, w => distanceBars(barsHost, w, current));
  const select = tabs(document.getElementById("district-tabs"), key => {
    current = key;
    const d = DISTRICTS.find(x => x.key === key), c = counts[key];
    f("name").textContent = d.name;
    f("pop").textContent = `Population ${d.pop.toLocaleString("en-GB")} (Census 2020)`;
    ["near", "mid", "far"].forEach((k, i) => { f(k).textContent = `${d.bands[i]}%`; });
    f("note").textContent = `${d.bands[2]}% live more than 3 km from a public clinic, ${rankWord[byFar.indexOf(key)]} share of the five districts.`;
    f("counts").textContent = `Mapped here: ${c.clinic} clinics, ${c.school} schools, ${c.transit} transit stops.`;
    Object.entries(map.washes).forEach(([k, el]) => el.classList.toggle("dim", k !== key));
    redrawBars();
  });
  Object.entries(map.washes).forEach(([k, el]) => el.addEventListener("click", () => select(k)));
}

/* ---------- experiments filter ---------- */
function initFilters() {
  const group = document.getElementById("filters");
  if (!group) return;
  const buttons = [...group.querySelectorAll("button")];
  const items = [...document.querySelectorAll("[data-kind]")];
  const count = document.getElementById("filter-count");
  buttons.forEach(b => b.addEventListener("click", () => {
    buttons.forEach(x => x.setAttribute("aria-pressed", String(x === b)));
    let shown = 0;
    items.forEach(it => {
      it.hidden = b.dataset.filter !== "all" && it.dataset.kind !== b.dataset.filter;
      if (!it.hidden) shown++;
    });
    count.textContent = `Showing ${shown} of ${items.length}`;
  }));
}

/* ---------- boot ---------- */
document.querySelectorAll("[data-map-figure]").forEach(fig => {
  const atlas = fig.dataset.mapFigure === "atlas";
  const map = drawMap(fig, atlas ? { districts: true, total: 412, spreadK: 1.7 } : {});
  if (atlas) initPenang(fig, map);
});
document.querySelectorAll('[data-chart="bands"]').forEach(h => mount(h, w => distanceBars(h, w)));
document.querySelectorAll('[data-chart="horizon"]').forEach(h => mount(h, w => horizonChart(h, w, Number(h.dataset.height) || 220)));
document.querySelectorAll('[data-chart="ci"]').forEach(h => mount(h, w => ciChart(h, w, TASKS.sentiment)));
initForecasting();
initLeaderboard();
initFilters();
