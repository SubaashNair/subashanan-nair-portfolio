// Leaderboard prototype: shared behaviour and illustrative data. All figures are made up.
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const NS = "http://www.w3.org/2000/svg";
const svgEl = (tag, attrs = {}) => {
  const el = document.createElementNS(NS, tag);
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  return el;
};
const seeded = seed => {
  let s = seed;
  return () => (s = (s * 16807) % 2147483647) / 2147483647;
};
const gauss = rand => Math.sqrt(-2 * Math.log(rand() + 1e-9)) * Math.cos(2 * Math.PI * rand());
const range = (lo, hi) => `${lo}–${hi}`;
const onWidth = (el, fn) => {
  let last = 0;
  new ResizeObserver(() => {
    if (el.clientWidth && el.clientWidth !== last) { last = el.clientWidth; fn(); }
  }).observe(el);
};

/* Tabs (role="tab", arrow keys) and pressed toggles */
function initTabs(list, onSelect) {
  const tabs = $$('[role="tab"]', list);
  const tabpanel = $('[role="tabpanel"]', list.closest("section") || document);
  const select = (tab, focus) => {
    if (tabpanel) tabpanel.setAttribute("aria-labelledby", tab.id);
    tabs.forEach(t => {
      const on = t === tab;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
    });
    if (focus) tab.focus();
    onSelect(tab.dataset.key, tab);
  };
  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => select(tab));
    tab.addEventListener("keydown", e => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
      const j = step ? (i + step + tabs.length) % tabs.length
        : e.key === "Home" ? 0 : e.key === "End" ? tabs.length - 1 : -1;
      if (j < 0) return;
      e.preventDefault();
      select(tabs[j], true);
    });
  });
  select(tabs.find(t => t.getAttribute("aria-selected") === "true") || tabs[0]);
}
function initToggles(group, onChange) {
  $$("button[aria-pressed]", group).forEach(btn => btn.addEventListener("click", () => {
    const on = btn.getAttribute("aria-pressed") !== "true";
    btn.setAttribute("aria-pressed", String(on));
    onChange(btn.dataset.key, on);
  }));
}

/* Scale-fixed SVGs (the map): keep text at a real 13px whatever the rendered width */
function fitText(svg) {
  const vbWidth = svg.viewBox.baseVal.width;
  onWidth(svg, () => svg.style.setProperty("--k", (vbWidth / svg.clientWidth).toFixed(3)));
}

/* ---------- LLM Eval Lab leaderboard ---------- */
// [model, score, ci low, ci high, cost label, latency, cost per 1k in dollars]
const TASKS = {
  sent: { label: "Manglish sentiment", metric: "Accuracy", rows: [
    ["Frontier model", 87, 84, 90, "$2.10", "900 ms", 2.10],
    ["Fine-tuned 1B", 84, 81, 87, "$0.04", "38 ms", 0.04],
    ["Open 8B, zero-shot", 79, 75, 83, "$0.12", "210 ms", 0.12],
    ["TF-IDF + logistic", 71, 67, 75, "<$0.01", "1 ms", 0.005]] },
  ner: { label: "BM entity extraction", metric: "F1", rows: [
    ["Frontier model", 83, 80, 86, "$2.40", "1.1 s", 2.40],
    ["Fine-tuned 1B", 78, 74, 81, "$0.05", "45 ms", 0.05],
    ["Open 8B, zero-shot", 70, 66, 74, "$0.14", "260 ms", 0.14],
    ["CRF baseline", 62, 58, 66, "<$0.01", "3 ms", 0.005]] },
  sum: { label: "BM summaries", metric: "Faithfulness", rows: [
    ["Frontier model", 82, 79, 85, "$4.80", "2.4 s", 4.80],
    ["Open 8B, zero-shot", 71, 67, 75, "$0.30", "640 ms", 0.30],
    ["Fine-tuned 1B", 66, 62, 70, "$0.09", "120 ms", 0.09],
    ["Extractive baseline", 58, 54, 62, "<$0.01", "5 ms", 0.005]] }
};
const SCORE_MIN = 50, SCORE_MAX = 100;
const pct = v => ((v - SCORE_MIN) / (SCORE_MAX - SCORE_MIN)) * 100;

function initBoard(root) {
  const tbody = $(".rows", root);
  const status = $(".status-line", root);
  const scatterBox = $(".scatter", root);
  const drawScatter = scatterBox ? makeScatter(scatterBox) : null;
  // Four stable rows, so switching tasks slides the marks rather than redrawing them.
  tbody.innerHTML = Array.from({ length: 4 }, () => `
    <tr><td class="model"><span></span></td>
      <td class="plot"><svg viewBox="0 0 100 22" preserveAspectRatio="none" aria-hidden="true">
        <line x1="0" y1="11" x2="100" y2="11" stroke="var(--rule)" stroke-width="1" vector-effect="non-scaling-stroke"/>
        <rect class="ci" x="0" y="9" height="4" rx="2" fill="var(--blue)" opacity=".35"/>
        <rect class="dot" x="-1.2" y="5" width="2.4" height="12" rx="1.2" fill="var(--blue)"/>
      </svg></td>
      <td class="num score"></td><td class="num hide-sm cost"></td><td class="num hide-sm lat"></td></tr>`).join("");
  initTabs($('[role="tablist"]', root), key => {
    const t = TASKS[key];
    $(".metric", root).textContent = t.metric;
    [...tbody.rows].forEach((tr, i) => {
      const [name, score, lo, hi, cost, lat] = t.rows[i];
      tr.classList.toggle("best", i === 0);
      $(".model span", tr).textContent = name;
      const ci = $(".ci", tr);
      ci.style.transform = `translateX(${pct(lo)}px)`;
      ci.setAttribute("width", pct(hi) - pct(lo));
      $(".dot", tr).style.transform = `translateX(${pct(score)}px)`;
      $(".score", tr).textContent = `${score} (${range(lo, hi)})`;
      $(".cost", tr).textContent = cost;
      $(".lat", tr).textContent = lat;
    });
    const [best, s, lo, hi] = t.rows[0];
    if (status) status.textContent = `${t.label}: ${best} leads on ${t.metric.toLowerCase()}, ${s} (95% CI ${lo} to ${hi}).`;
    if (drawScatter) drawScatter(t);
  });
}

// Cost (log scale) against score, one point per model. Positions slide between tasks.
function makeScatter(box) {
  const svg = svgEl("svg", { class: "chart", role: "img" });
  const axes = svgEl("g");
  const frontier = svgEl("path", { fill: "none", stroke: "var(--slate)", "stroke-width": 1.5, "stroke-dasharray": "5 5" });
  svg.append(axes, frontier);
  box.append(svg);
  const points = {};
  const LX0 = Math.log10(0.003), LX1 = Math.log10(10);
  const slot = name => (/Frontier|1B|8B/.exec(name) || ["base"])[0];
  let task = null;

  function draw() {
    if (!task) return;
    const W = box.clientWidth, H = W < 480 ? 280 : 320;
    const m = { l: 40, r: 14, t: 16, b: 48 };
    const x = c => m.l + ((Math.log10(c) - LX0) / (LX1 - LX0)) * (W - m.l - m.r);
    const y = s => m.t + (1 - (s - SCORE_MIN) / (SCORE_MAX - SCORE_MIN)) * (H - m.t - m.b);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("height", H);
    axes.innerHTML = "";
    const grid = svgEl("g", { class: "grid" });
    [50, 60, 70, 80, 90, 100].forEach(s => {
      grid.append(svgEl("line", { x1: m.l, x2: W - m.r, y1: y(s), y2: y(s) }));
      const t = svgEl("text", { x: m.l - 8, y: y(s) + 4, "text-anchor": "end" });
      t.textContent = s;
      axes.append(t);
    });
    [[0.01, "$0.01"], [0.1, "$0.10"], [1, "$1"], [10, "$10"]].forEach(([c, lbl]) => {
      grid.append(svgEl("line", { x1: x(c), x2: x(c), y1: m.t, y2: H - m.b }));
      const t = svgEl("text", { x: x(c), y: H - m.b + 18, "text-anchor": c === 10 ? "end" : "middle" });
      t.textContent = lbl;
      axes.append(t);
    });
    axes.prepend(grid);
    const xt = svgEl("text", { x: W - m.r, y: H - 6, "text-anchor": "end", class: "axis-label" });
    xt.textContent = "Cost per 1k items, log scale";
    const yt = svgEl("text", { x: m.l, y: m.t - 4 + 0, class: "axis-label", dx: 4, dy: 12 });
    yt.textContent = task.metric;
    axes.append(xt, yt);

    task.rows.forEach(([name, s, lo, hi, , , cost], i) => {
      const key = slot(name);
      if (!points[key]) {
        const g = svgEl("g", { class: "move" });
        g.append(
          svgEl("line", { class: "whisker", stroke: "var(--blue)", "stroke-width": 4, "stroke-linecap": "round", opacity: ".35" }),
          svgEl("circle", { r: 6, fill: "var(--blue)", stroke: "#fff", "stroke-width": 2 }),
          svgEl("text", { class: "lbl", y: 4.5 }));
        svg.append(g);
        points[key] = g;
      }
      const g = points[key], px = x(cost), py = y(s);
      g.style.transform = `translate(${px}px, ${py}px)`;
      const w = $(".whisker", g);
      w.setAttribute("y1", y(hi) - py);
      w.setAttribute("y2", y(lo) - py);
      const label = $("text", g);
      const right = px > W * 0.6;
      // Points near the right edge get their label above, so it clears neighbours and the edge.
      label.setAttribute("x", right ? 6 : 12);
      label.setAttribute("y", right ? -14 : 4.5);
      label.setAttribute("text-anchor", right ? "end" : "start");
      label.textContent = i === 0 ? `${name}, ${s}` : name;
      label.style.fontWeight = i === 0 ? "600" : "400";
    });
    // Frontier: models that no cheaper model beats.
    let bestSoFar = -1;
    const front = [...task.rows].sort((a, b) => a[6] - b[6]).filter(r => {
      if (r[1] <= bestSoFar) return false;
      bestSoFar = r[1];
      return true;
    });
    frontier.setAttribute("d", front.map((r, i) => `${i ? "L" : "M"}${x(r[6]).toFixed(1)},${y(r[1]).toFixed(1)}`).join(""));
    svg.setAttribute("aria-label", `${task.label}: cost per 1k items against ${task.metric.toLowerCase()}. ` +
      task.rows.map(r => `${r[0]} ${r[1]} at ${r[4]}`).join("; ") + ".");
  }
  onWidth(box, draw);
  return t => { task = t; draw(); };
}

/* ---------- Forecasting Lab ---------- */
const HORIZONS = [15, 30, 60, 90, 120];
const MODELS = [
  { key: "sn", name: "Seasonal naive", mae: [9.8, 11.2, 13.5, 15.1, 16.4], stroke: "#8b94a7", dash: "1 5", width: 2.4 },
  { key: "gb", name: "Gradient boosting", mae: [6.1, 7.9, 10.6, 12.4, 14.0], stroke: "var(--slate)", dash: "7 5", width: 2 },
  { key: "gru", name: "Small neural net (GRU)", mae: [6.4, 8.1, 10.4, 12.0, 13.6], stroke: "var(--slate)", dash: "12 4 2 4", width: 2 },
  { key: "chr", name: "Chronos (pre-trained, zero-shot)", mae: [7.0, 8.3, 10.1, 11.6, 13.4], stroke: "var(--blue)", dash: "", width: 2.5 }
];
const SENSORS = {
  s12: { label: "Sensor 12", seed: 12, level: 1.0, peak: 17.6, factor: 1.0 },
  s47: { label: "Sensor 47", seed: 47, level: 0.72, peak: 17.3, factor: 0.85 },
  s103: { label: "Sensor 103", seed: 103, level: 1.28, peak: 18.0, factor: 1.15 }
};
const STEPS = 60, NOW = 36, START_HOUR = 14; // 5-minute steps from 14:00, forecast from 17:00
const maeAt = (model, minutes) => {
  const xs = [0, ...HORIZONS], ys = [model.mae[0] * 0.55, ...model.mae];
  const i = Math.max(1, xs.findIndex(v => v >= minutes));
  const f = (minutes - xs[i - 1]) / (xs[i] - xs[i - 1]);
  return ys[i - 1] + f * (ys[i] - ys[i - 1]);
};
const maeCI = v => [+(v * 0.94).toFixed(1), +(v * 1.06).toFixed(1)];

function buildSeries(sensor) {
  const rand = seeded(sensor.seed * 7919);
  let ar = 0;
  const actual = Array.from({ length: STEPS + 1 }, (_, i) => {
    const hr = START_HOUR + i / 12;
    ar = 0.8 * ar + 0.6 * gauss(rand);
    const base = 105 + 88 * Math.exp(-(((hr - sensor.peak) / 0.85) ** 2)) + 14 * Math.sin(hr * 1.7);
    return Math.max(5, sensor.level * (base + 6 * ar));
  });
  const forecasts = {};
  MODELS.forEach((model, mi) => {
    const r = seeded(sensor.seed * 31 + mi * 977);
    let z = gauss(r);
    const pts = [];
    for (let i = NOW; i <= STEPS; i++) {
      const h = i - NOW;
      if (h) z = 0.88 * z + Math.sqrt(1 - 0.88 ** 2) * gauss(r);
      const err = h ? sensor.factor * maeAt(model, h * 5) * 1.25 * z : 0;
      pts.push(Math.max(0, actual[i] + err));
    }
    forecasts[model.key] = pts;
  });
  const chr = MODELS[3];
  const band = forecasts.chr.map((v, h) => {
    const w = 1.28 * 1.25 * sensor.factor * maeAt(chr, h * 5);
    return [Math.max(0, v - w), v + w];
  });
  return { actual, forecasts, band };
}

function initForecast(root) {
  const box = $(".forecast-chart", root);
  const keyBox = $(".mae-key", root);
  const series = Object.fromEntries(Object.entries(SENSORS).map(([k, s]) => [k, buildSeries(s)]));
  const yMax = Math.ceil(Math.max(...Object.values(series).flatMap(s => [...s.actual, ...s.band.map(b => b[1])])) / 50) * 50;
  const on = new Set(MODELS.map(m => m.key));
  let sensorKey = "s12";

  const svg = svgEl("svg", { class: "chart", role: "img" });
  const axes = svgEl("g");
  const band = svgEl("path", { class: "band", fill: "var(--blue)", "fill-opacity": ".12" });
  const lines = Object.fromEntries(MODELS.map(m => [m.key, svgEl("path", {
    class: "line", stroke: m.stroke, "stroke-width": m.width, "stroke-dasharray": m.dash })]));
  const actual = svgEl("path", { class: "line", stroke: "var(--ink)", "stroke-width": 2.5 });
  svg.append(axes, band, ...Object.values(lines), actual);
  box.append(svg);

  const setD = (el, d) => { el.setAttribute("d", d); el.style.d = `path("${d}")`; };
  function draw() {
    const W = box.clientWidth, H = W < 560 ? 270 : 340;
    const m = { l: 40, r: 12, t: 30, b: 34 };
    const x = i => m.l + (i / STEPS) * (W - m.l - m.r);
    const y = v => m.t + (1 - v / yMax) * (H - m.t - m.b);
    const pathOf = (vals, offset = 0) => vals.map((v, i) => `${i ? "L" : "M"}${x(i + offset).toFixed(1)},${y(v).toFixed(1)}`).join("");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("height", H);
    axes.innerHTML = "";
    axes.append(svgEl("rect", { x: x(NOW), y: m.t, width: x(STEPS) - x(NOW), height: H - m.t - m.b, fill: "var(--page)" }));
    const grid = svgEl("g", { class: "grid" });
    for (let v = 0; v <= yMax; v += 50) {
      grid.append(svgEl("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v) }));
      const t = svgEl("text", { x: m.l - 8, y: y(v) + 4, "text-anchor": "end" });
      t.textContent = v;
      axes.append(t);
    }
    const hourStep = W < 420 ? 2 : 1;
    for (let hr = 0; hr <= 5; hr += hourStep) {
      const t = svgEl("text", { x: x(hr * 12), y: H - m.b + 20, "text-anchor": hr === 0 ? "start" : hr === 5 ? "end" : "middle" });
      t.textContent = `${START_HOUR + hr}:00`;
      axes.append(t);
    }
    axes.prepend(grid);
    axes.append(svgEl("line", { x1: x(NOW), x2: x(NOW), y1: m.t - 6, y2: H - m.b, stroke: "var(--ink)", "stroke-dasharray": "3 3" }));
    const past = svgEl("text", { x: x(NOW) - 8, y: m.t - 12, "text-anchor": "end" });
    past.textContent = "Last 3 hours";
    const next = svgEl("text", { x: x(NOW) + 8, y: m.t - 12 });
    next.textContent = "Next 2 hours";
    const unit = svgEl("text", { x: m.l + 6, y: m.t + 14, class: "axis-label" });
    unit.textContent = "Vehicles per 5 min";
    axes.append(past, next, unit);

    const s = series[sensorKey];
    setD(actual, pathOf(s.actual));
    MODELS.forEach(mo => {
      setD(lines[mo.key], pathOf(s.forecasts[mo.key], NOW));
      lines[mo.key].classList.toggle("off", !on.has(mo.key));
    });
    const upper = s.band.map(b => b[1]), lower = s.band.map(b => b[0]).reverse();
    setD(band, pathOf(upper, NOW) + lower.map((v, i) => `L${x(STEPS - i).toFixed(1)},${y(v).toFixed(1)}`).join("") + "Z");
    band.classList.toggle("off", !on.has("chr"));
    svg.setAttribute("aria-label", `${SENSORS[sensorKey].label}: actual traffic from 14:00 to 19:00 with two-hour forecasts from 17:00 for ${[...on].length} models.`);
  }

  function renderKey() {
    const sensor = SENSORS[sensorKey];
    keyBox.innerHTML = `<span class="kh">${sensor.label}, MAE at 2 hours (95% CI)</span>` + MODELS.map(mo => {
      const v = +(mo.mae[4] * sensor.factor).toFixed(1);
      const [lo, hi] = maeCI(v);
      return `<span class="${on.has(mo.key) ? "" : "dim"}">${mo.name.split(" (")[0]} <b>${v.toFixed(1)}</b> (${range(lo.toFixed(1), hi.toFixed(1))})</span>`;
    }).join("");
  }

  initTabs($('[role="tablist"]', root), key => { sensorKey = key; draw(); renderKey(); });
  initToggles($(".toggles", root), (key, isOn) => {
    if (isOn) on.add(key); else on.delete(key);
    draw();
    renderKey();
  });
  onWidth(box, draw);
}

function initErrorTable(table) {
  const max = 18;
  const best = HORIZONS.map((_, c) => Math.min(...MODELS.map(m => m.mae[c])));
  $("tbody", table).innerHTML = MODELS.map(mo => `<tr><th scope="row">${mo.name}</th>${mo.mae.map((v, c) => {
    const [lo, hi] = maeCI(v);
    const sx = n => ((n / max) * 76).toFixed(1);
    const isBest = v === best[c];
    return `<td class="${isBest ? "best" : ""}"><span class="cell"><span class="v">${v.toFixed(1)}${isBest ? '<span class="visually-hidden"> (lowest)</span>' : ""}</span>
      <svg viewBox="0 0 76 8" aria-hidden="true"><rect x="0" y="2" width="${sx(v)}" height="4" rx="1" fill="${isBest ? "var(--ink)" : "var(--blue-mid)"}"/>
      <line x1="${sx(lo)}" x2="${sx(hi)}" y1="4" y2="4" stroke="var(--ink)" stroke-width="1.2"/>
      <line x1="${sx(lo)}" x2="${sx(lo)}" y1="1" y2="7" stroke="var(--ink)"/><line x1="${sx(hi)}" x2="${sx(hi)}" y1="1" y2="7" stroke="var(--ink)"/></svg></span></td>`;
  }).join("")}</tr>`).join("");
}

/* ---------- Penang Pulse ---------- */
const DISTRICTS = [
  { key: "tl", name: "Timur Laut", bands: [72, 24, 4], ci: [3, 6], pop: 545000, share: [.40, .37, .42], centres: [[275, 160, 34], [300, 255, 22], [235, 205, 26]] },
  { key: "bd", name: "Barat Daya", bands: [48, 34, 18], ci: [15, 21], pop: 236000, share: [.14, .13, .12], centres: [[240, 380, 26], [115, 275, 24], [140, 175, 18]] },
  { key: "spu", name: "Seberang Perai Utara", bands: [55, 33, 12], ci: [10, 15], pop: 330000, share: [.17, .17, .16], centres: [[420, 120, 26], [500, 70, 40]] },
  { key: "spt", name: "Seberang Perai Tengah", bands: [61, 30, 9], ci: [7, 11], pop: 402000, share: [.19, .22, .21], centres: [[430, 225, 26], [505, 280, 34]] },
  { key: "sps", name: "Seberang Perai Selatan", bands: [41, 38, 21], ci: [18, 24], pop: 205000, share: [.10, .11, .09], centres: [[455, 430, 34], [530, 385, 36]] }
];
const CATS = [ // [key, total points]; shares above are [schools, transit, clinics]
  { key: "school", total: 238, idx: 0 },
  { key: "transit", total: 122, idx: 1 },
  { key: "clinic", total: 52, idx: 2 }
];
const fmt = n => n.toLocaleString("en-GB");

function placePoints(svg) {
  const layer = $("#points", svg);
  const rand = seeded(2026);
  const inside = (d, px, py) => {
    const poly = $(`.district[data-key="${d.key}"]`, svg);
    const land = $(poly.dataset.land, svg);
    const pt = svg.createSVGPoint();
    pt.x = px; pt.y = py;
    return poly.isPointInFill(pt) && land.isPointInFill(pt);
  };
  const shape = (cat, px, py) => {
    if (cat === "clinic") return svgEl("circle", { cx: px, cy: py, r: 5, fill: "var(--blue)", stroke: "#fff", "stroke-width": 1.5 });
    if (cat === "school") return svgEl("rect", { x: px - 3, y: py - 3, width: 6, height: 6, fill: "#fff", stroke: "var(--slate)", "stroke-width": 1.2 });
    return svgEl("path", { d: `M${px} ${py - 3.6}L${px + 3.6} ${py}L${px} ${py + 3.6}L${px - 3.6} ${py}Z`, fill: "var(--ink)", "fill-opacity": ".8" });
  };
  const box = svg.viewBox.baseVal;
  CATS.forEach(cat => DISTRICTS.forEach((d, di) => {
    // Last district takes the remainder so each category sums to its total.
    const before = DISTRICTS.slice(0, di).reduce((a, x) => a + Math.round(cat.total * x.share[cat.idx]), 0);
    const n = di === DISTRICTS.length - 1 ? cat.total - before : Math.round(cat.total * d.share[cat.idx]);
    for (let placed = 0, tries = 0; placed < n && tries < 4000; tries++) {
      let px, py;
      if (rand() < 0.7) {
        const [cx, cy, spread] = d.centres[Math.floor(rand() * d.centres.length)];
        px = cx + gauss(rand) * spread; py = cy + gauss(rand) * spread;
      } else {
        px = rand() * box.width; py = rand() * box.height;
      }
      if (!inside(d, px, py)) continue;
      const el = shape(cat.key, +px.toFixed(1), +py.toFixed(1));
      el.classList.add("pt");
      el.dataset.cat = cat.key;
      layer.append(el);
      placed++;
    }
  }));
}

function initPulse(root) {
  const svg = $(".map", root);
  const tbody = $(".dist tbody", root);
  const readout = $(".readout", root);
  const count = $(".pt-count", root);
  fitText(svg);
  placePoints(svg);
  const maxShare = Math.max(...DISTRICTS.map(d => d.bands[2]));
  const minShare = Math.min(...DISTRICTS.map(d => d.bands[2]));
  DISTRICTS.forEach(d => {
    const poly = $(`.district[data-key="${d.key}"]`, svg);
    poly.setAttribute("fill", "var(--blue)");
    poly.setAttribute("fill-opacity", (0.06 + (d.bands[2] / maxShare) * 0.26).toFixed(2));
    poly.addEventListener("click", () => select(d.key));
  });
  tbody.innerHTML = DISTRICTS.map(d => {
    const [a, b, c] = d.bands;
    return `<tr data-key="${d.key}" class="${c === minShare ? "best" : ""}">
      <td class="name"><button type="button" aria-pressed="false" data-key="${d.key}"><span>${d.name}</span></button></td>
      <td><div class="stack" role="img" aria-label="${a}% under 1 km, ${b}% 1 to 3 km, ${c}% over 3 km">
        <span class="b1" style="width:${a}%"></span><span class="b2" style="width:${b}%"></span><span class="b3" style="width:${c}%"></span></div></td>
      <td class="num">${c}% (${range(d.ci[0], d.ci[1])})</td>
      <td class="num hide-xs">${fmt(d.pop)}</td></tr>`;
  }).join("");

  function select(key) {
    const d = DISTRICTS.find(x => x.key === key);
    $$(".district", svg).forEach(p => p.classList.toggle("sel", p.dataset.key === key));
    // Draw the selected outline last so its border sits on top of neighbours.
    const sel = $(`.district[data-key="${key}"]`, svg);
    sel.parentNode.append(sel);
    $$("tr[data-key]", tbody).forEach(tr => tr.classList.toggle("sel", tr.dataset.key === key));
    $$("button[data-key]", tbody).forEach(b => b.setAttribute("aria-pressed", String(b.dataset.key === key)));
    const [a, b, c] = d.bands;
    const over = Math.round((d.pop * c) / 100 / 1000);
    readout.innerHTML = `<h3>${d.name}</h3>
      <p class="big">${c}% <span class="cond" style="font-size:20px;font-weight:600;color:var(--slate)">over 3 km (95% CI ${d.ci[0]} to ${d.ci[1]}%)</span></p>
      <p>About ${fmt(over * 1000)} of ${fmt(d.pop)} residents. ${a}% live under 1 km from a public clinic and ${b}% between 1 and 3 km.</p>`;
  }
  $$("button[data-key]", tbody).forEach(b => b.addEventListener("click", () => select(b.dataset.key)));

  const shown = new Set(CATS.map(c => c.key));
  const updateCount = () => {
    const visible = $$(".pt", svg).filter(p => shown.has(p.dataset.cat)).length;
    count.textContent = `Showing ${fmt(visible)} of ${fmt($$(".pt", svg).length)} service points.`;
  };
  initToggles($(".toggles", root), (key, isOn) => {
    if (isOn) shown.add(key); else shown.delete(key);
    $$(`.pt[data-cat="${key}"]`, svg).forEach(p => p.classList.toggle("off", !isOn));
    updateCount();
  });
  updateCount();
  select("sps");
}

/* ---------- Experiments filter ---------- */
function initFilter(root) {
  const rows = $$("tbody tr", root);
  const btns = $$(".filters button", root);
  const status = $(".status-line", root);
  btns.forEach(btn => btn.addEventListener("click", () => {
    btns.forEach(b => b.setAttribute("aria-pressed", String(b === btn)));
    const cat = btn.dataset.key;
    rows.forEach(r => { r.hidden = cat !== "all" && r.dataset.cat !== cat; });
    const n = rows.filter(r => !r.hidden).length;
    status.textContent = `Showing ${n} of ${rows.length} projects${cat === "all" ? "" : ` in ${btn.textContent}`}.`;
  }));
}

$$("[data-board]").forEach(initBoard);
$$("[data-forecast]").forEach(initForecast);
$$("table[data-error]").forEach(initErrorTable);
$$("[data-pulse]").forEach(initPulse);
$$("[data-filter]").forEach(initFilter);
