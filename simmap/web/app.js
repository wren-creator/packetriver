"use strict";

const SVGNS = "http://www.w3.org/2000/svg";
function el(tag, attrs, parent) {
  const n = document.createElementNS(SVGNS, tag);
  for (const k in (attrs || {})) n.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(n);
  return n;
}
function txt(x, y, s, cls, parent) {
  const t = el("text", { x, y, class: cls || "label" }, parent);
  t.textContent = s;
  return t;
}

// ---------------------------------------------------------------- scene
const REFS = {};

function buildScene() {
  const host = document.getElementById("scene");
  host.innerHTML = "";
  const svg = el("svg", { viewBox: "0 0 1600 900", role: "img" }, host);

  // rail loop (perimeter) + train
  const railD =
    "M 70 70 H 1530 Q 1550 70 1550 90 V 810 Q 1550 830 1530 830 " +
    "H 70 Q 50 830 50 810 V 90 Q 50 70 70 70 Z";
  REFS.railPath = el("path", { d: railD, fill: "none", stroke: "#3d444d",
    "stroke-width": 4, "stroke-dasharray": "2 10" }, svg);
  REFS.spur = el("path", { d: "M 1300 830 L 1440 760", fill: "none",
    stroke: "#3d444d", "stroke-width": 4 }, svg);
  REFS.train = el("rect", { width: 26, height: 12, rx: 2, fill: "#9db7d0" }, svg);

  // river band + swimmers + sewage plant
  REFS.river = el("rect", { x: 0, y: 8, width: 1600, height: 78,
    class: "river-body" }, svg);
  txt(20, 34, "FOX RIVER", "label", svg);
  REFS.swimmers = [];
  for (let i = 0; i < 5; i++) {
    REFS.swimmers.push(el("circle", { cx: 360 + i * 60, cy: 50, r: 6,
      class: "swimmer" }, svg));
  }
  el("rect", { x: 1360, y: 20, width: 200, height: 92, rx: 6, fill: "#243",
    stroke: "#3d444d" }, svg);
  txt(1372, 52, "SEWAGE PLANT", "value", svg);
  REFS.outfall = el("line", { x1: 1400, y1: 112, x2: 1400, y2: 86,
    stroke: "#3fb950", "stroke-width": 6 }, svg);

  // utilities strip
  mkBox(svg, "water", 40, 150, "WATER TREATMENT");
  REFS.waterVal = txt(52, 232, "", "value", svg);
  mkBox(svg, "power", 40, 300, "ELECTRIC CO");
  REFS.powerVal = txt(52, 382, "", "value", svg);
  REFS.factory = el("rect", { x: 1380, y: 690, width: 170, height: 92, rx: 6,
    fill: "#243", stroke: "#3d444d" }, svg);
  txt(1392, 722, "WIDGET FACTORY", "value", svg);

  // water main + power feeder flows toward the houses
  REFS.waterFlow = el("polyline", { points: "120,240 120,560 260,600",
    fill: "none", stroke: "#2f6fb0", "stroke-width": 5,
    class: "svg-flow" }, svg);
  REFS.powerFlow = el("polyline", { points: "120,390 120,540 260,560",
    fill: "none", stroke: "#d29922", "stroke-width": 4,
    class: "svg-flow" }, svg);

  // 4 intersections
  REFS.ints = [];
  for (let i = 0; i < 4; i++) {
    const cx = 460 + i * 210, cy = 300;
    const g = el("g", { id: "int" + (i + 1), transform: `translate(${cx},${cy})` }, svg);
    el("line", { x1: -45, y1: 0, x2: 45, y2: 0, stroke: "#3d444d", "stroke-width": 10 }, g);
    el("line", { x1: 0, y1: -45, x2: 0, y2: 45, stroke: "#3d444d", "stroke-width": 10 }, g);
    const ns = el("circle", { cx: 0, cy: -30, r: 7, class: "light off" }, g);
    const ew = el("circle", { cx: 30, cy: 0, r: 7, class: "light off" }, g);
    txt(-45, 40, "X" + (i + 1), "label", g);
    const crash = txt(12, -34, "", "value", g);
    REFS.ints.push({ g, ns, ew, crash });
  }

  // City Hall + 8 shops
  mkBox(svg, "cityhall", 60, 430, "CITY HALL");
  REFS.chVal = txt(72, 520, "", "value", svg);
  REFS.chAnnounce = txt(72, 540, "", "label", svg);
  REFS.shops = [];
  for (let i = 0; i < 8; i++) {
    const x = 320 + (i % 4) * 150;
    const y = 430 + Math.floor(i / 4) * 90;
    const r = el("rect", { x, y, width: 128, height: 72, rx: 5,
      class: "site healthy" }, svg);
    const nm = txt(x + 8, y + 24, "S" + (i + 1), "value", svg);
    const st = txt(x + 8, y + 44, "", "label", svg);
    const fr = txt(x + 8, y + 62, "", "label", svg);
    REFS.shops.push({ r, nm, st, fr });
  }

  // houses + streetlights
  REFS.houses = [];
  REFS.streetlights = [];
  for (let i = 0; i < 8; i++) {
    const x = 300 + i * 150, y = 650;
    el("path", { d: `M ${x} ${y + 40} L ${x} ${y + 10} L ${x + 30} ${y - 10} ` +
      `L ${x + 60} ${y + 10} L ${x + 60} ${y + 40} Z`, fill: "#1c2330",
      stroke: "#3d444d" }, svg);
    const win = el("rect", { x: x + 22, y: y + 12, width: 16, height: 16,
      class: "win off" }, svg);
    const drop = el("circle", { cx: x + 12, cy: y + 26, r: 5, class: "drop off" }, svg);
    REFS.houses.push({ win, drop });
    REFS.streetlights.push(el("circle", { cx: x + 75, cy: y - 10, r: 5,
      class: "light off" }, svg));
  }
}

function mkBox(svg, id, x, y, label) {
  el("rect", { x, y, width: 190, height: 92, rx: 6, fill: "#243",
    stroke: "#3d444d", id: "box-" + id }, svg);
  txt(x + 12, y + 32, label, "value", svg);
}

// --------------------------------------------------------------- render
function render(s) {
  // traffic
  s.traffic.forEach((t, i) => {
    const R = REFS.ints[i];
    const setL = (node, color) => { node.setAttribute("class", "light " + color); };
    if (t.phase === "dark") { setL(R.ns, "off"); setL(R.ew, "off"); }
    else if (t.phase === "ALL-GREEN") { setL(R.ns, "green"); setL(R.ew, "green"); }
    else if (t.phase === "ns-green") { setL(R.ns, "green"); setL(R.ew, "red"); }
    else if (t.phase === "ew-green") { setL(R.ns, "red"); setL(R.ew, "green"); }
    else { setL(R.ns, "red"); setL(R.ew, "red"); }
    R.g.classList.toggle("hijacked", t.mode === "ALL-GREEN");
    R.crash.textContent = t.crash_count ? "⚠ " + t.crash_count : "";
  });

  // rail + factory
  const L = REFS.railPath.getTotalLength();
  let p;
  if (s.rail.derailed) {
    p = REFS.spur.getPointAtLength(REFS.spur.getTotalLength());
  } else {
    p = REFS.railPath.getPointAtLength((s.rail.train_pos * L) % L);
  }
  REFS.train.setAttribute("x", p.x - 13);
  REFS.train.setAttribute("y", p.y - 6);
  REFS.spur.setAttribute("stroke", s.rail.switch_position === "spur" ? "#f85149" : "#3d444d");
  REFS.factory.classList.toggle("fire", s.rail.factory_fire);

  // water
  REFS.waterVal.textContent = `mains ${s.water.mains_pressure_pct}%  ·  ${s.water.quality}`;
  REFS.waterFlow.classList.toggle("stopped", s.water.quality === "dry");

  // sewage + river
  REFS.river.classList.toggle("foul", s.sewage.river_contamination > 0.4);
  REFS.outfall.setAttribute("stroke", s.sewage.effluent_path === "raw" ? "#6b5330" : "#3fb950");
  REFS.swimmers.forEach(sw => sw.classList.toggle("sick", s.sewage.swimmers_sick));

  // power
  const f = s.power.feeders;
  REFS.powerVal.textContent =
    `${s.power.bus_freq_hz.toFixed(2)} Hz  ·  ` +
    Object.keys(f).filter(k => !f[k]).map(k => k + " OFF").join(" ") || `${s.power.bus_freq_hz.toFixed(2)} Hz`;
  REFS.powerFlow.classList.toggle("stopped", !f.residential);
  REFS.streetlights.forEach(sl => sl.setAttribute("class", "light " + (f.streetlights ? "amber" : "off")));

  // shops
  s.shops.forEach((sh, i) => {
    const R = REFS.shops[i];
    R.r.setAttribute("class", "site " + sh.site_status);
    R.st.textContent = sh.site_status === "healthy" ? "" : sh.site_status.replace("_", " ");
    R.fr.textContent = sh.fraud_charges ? "$" + sh.fraud_charges + " fraud" : "";
  });

  // city hall
  REFS.chVal.textContent = `payroll $${s.cityhall.payroll_balance.toLocaleString()}`;
  REFS.chAnnounce.textContent = '"' + s.cityhall.announcement_text.slice(0, 40) + '"';
  document.getElementById("box-cityhall").setAttribute(
    "stroke", s.cityhall.site_status === "healthy" ? "#3d444d" : "#f85149");

  // houses
  s.houses.forEach((h, i) => {
    REFS.houses[i].win.setAttribute("class", "win " + (h.has_power ? "on" : "off"));
    REFS.houses[i].drop.setAttribute("class", "drop " + (h.has_water ? "on" : "off"));
  });

  // hud
  const lvl = s.alert.level;
  const a = document.getElementById("hud-alert");
  a.dataset.lvl = lvl;
  document.getElementById("hud-alert-lvl").textContent = lvl;
}

// ------------------------------------------------------------ transport
let ws = null, backoff = 1000;
function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen = () => { backoff = 1000; setConn(true); ws.send(JSON.stringify({ type: "resync" })); };
  ws.onclose = () => { setConn(false); setTimeout(connect, backoff); backoff = Math.min(backoff * 2, 10000); };
  ws.onerror = () => ws.close();
  ws.onmessage = (ev) => {
    let m; try { m = JSON.parse(ev.data); } catch { return; }
    if (m.type === "snapshot") render(m);
  };
}
function setConn(up) {
  const c = document.getElementById("hud-conn");
  c.dataset.up = up ? "yes" : "no";
  document.getElementById("hud-conn-lbl").textContent = up ? "live" : "down";
}

// ---------------------------------------------------------------- panels
const DEBUG_ACTIONS = [
  ["Dump shop 3", { effect: "shop_sqli_dump", shop: 3 }],
  ["Deface shop 5", { effect: "shop_xss_deface", shop: 5 }],
  ["Card shop 1", { effect: "shop_carded", shop: 1 }],
  ["Deface City Hall", { effect: "cityhall_deface", player: "debug" }],
  ["Drain payroll", { effect: "cityhall_payroll" }],
  ["Break water main", { effect: "water_main_break" }],
  ["Sewage bypass", { effect: "sewage_bypass" }],
  ["Trip industrial feeder", { effect: "power_trip_feeder", feeder: "industrial" }],
  ["Trip residential feeder", { effect: "power_trip_feeder", feeder: "residential" }],
  ["Hijack all lights", { effect: "traffic_all_green" }],
  ["Throw rail switch", { effect: "rail_switch_spur" }],
];

async function post(url, body) {
  await fetch(url, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
}

function buildPanels(cfg) {
  const rb = document.getElementById("reset-buttons");
  cfg.reset_scopes.forEach(scope => {
    const b = document.createElement("button");
    b.textContent = scope;
    if (scope === "all") b.className = "danger";
    b.onclick = () => post("/api/debug/reset", { scope });
    rb.appendChild(b);
  });
  const db = document.getElementById("debug-buttons");
  DEBUG_ACTIONS.forEach(([label, body]) => {
    const b = document.createElement("button");
    b.textContent = label;
    b.className = "danger";
    b.onclick = () => post("/api/debug/effect", body);
    db.appendChild(b);
  });
}

function setupDonation(tag) {
  const box = document.getElementById("donation");
  if (localStorage.getItem("pkt_donation_dismissed") === "1") return;
  const link = document.getElementById("donation-link");
  link.textContent = "$" + tag;
  link.href = "https://cash.app/$" + tag;
  box.hidden = false;
  document.getElementById("donation-dismiss").onclick = () => {
    box.hidden = true;
    try { localStorage.setItem("pkt_donation_dismissed", "1"); } catch {}
  };
}

// ---------------------------------------------------------------- boot
(async function () {
  buildScene();
  let cfg = { reset_scopes: ["all"], cashapp: "britleywren" };
  try { cfg = await (await fetch("/api/config")).json(); } catch {}
  document.getElementById("phase-badge").textContent = "phase " + (cfg.phase ?? 0) + " · scaffold";
  buildPanels(cfg);
  setupDonation(cfg.cashapp);
  connect();
})();
