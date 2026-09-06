"use strict";

const SVGNS = "http://www.w3.org/2000/svg";
let VB = [1000, 545];
const X = n => n * VB[0];
const Y = n => n * VB[1];

function el(tag, attrs, parent) {
  const n = document.createElementNS(SVGNS, tag);
  for (const k in (attrs || {})) n.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(n);
  return n;
}
function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { t.hidden = true; }, 2600);
}

// ----------------------------------------------------------- overlay build
const REFS = { shops: {}, civic: {}, ints: [], houses: [], streetlights: [] };
let LAYOUT = null;

function buildOverlay(layout) {
  LAYOUT = layout;
  VB = layout.viewBox || [1000, 545];
  const svg = document.getElementById("overlay");
  svg.setAttribute("viewBox", `0 0 ${VB[0]} ${VB[1]}`);
  svg.innerHTML = "";

  // river + outfall + swimmers
  const r = layout.river;
  REFS.river = el("rect", { x: X(r.x), y: Y(r.y), width: X(r.w), height: Y(r.h),
    class: "river-body" }, svg);
  REFS.outfall = el("line", {
    x1: X(layout.outfall[0][0]), y1: Y(layout.outfall[0][1]),
    x2: X(layout.outfall[1][0]), y2: Y(layout.outfall[1][1]),
    stroke: "#4aa35b", "stroke-width": 5 }, svg);
  REFS.swimmers = layout.swimmers.map(p =>
    el("circle", { cx: X(p[0]), cy: Y(p[1]), r: 4, class: "swimmer" }, svg));

  // water main + power feeder flows
  REFS.waterMain = el("polyline", {
    points: layout.waterMain.map(p => `${X(p[0])},${Y(p[1])}`).join(" "),
    fill: "none", stroke: "#2f8fbf", "stroke-width": 4, class: "flow" }, svg);
  REFS.powerFeeder = el("polyline", {
    points: layout.powerFeeder.map(p => `${X(p[0])},${Y(p[1])}`).join(" "),
    fill: "none", stroke: "#e3a52e", "stroke-width": 4, class: "flow" }, svg);

  // rail loop (perimeter) + spur + a little train
  REFS.rail = el("polyline", {
    points: layout.railPath.map(p => `${X(p[0])},${Y(p[1])}`).join(" "),
    fill: "none", stroke: "#6f6350", "stroke-width": 2.5, "stroke-dasharray": "2 6",
    opacity: 0.7 }, svg);
  const sb = layout.spurBranch || layout.railPath[Math.floor(layout.railPath.length / 4)];
  REFS.spur = el("line", {
    x1: X(sb[0]), y1: Y(sb[1]), x2: X(layout.spurEnd[0]), y2: Y(layout.spurEnd[1]),
    stroke: "#6f6350", "stroke-width": 2.5, class: "spur" }, svg);
  REFS.train = el("g", { class: "train" }, svg);
  // loco + two cars, centred on the origin so the group can translate+rotate
  el("rect", { x: -13, y: -3.5, width: 9, height: 7, rx: 1.5, fill: "#8a3b2f" }, REFS.train);
  el("rect", { x: -3, y: -3, width: 7, height: 6, rx: 1, fill: "#5b4636" }, REFS.train);
  el("rect", { x: 5, y: -3, width: 7, height: 6, rx: 1, fill: "#5b4636" }, REFS.train);

  // buildings: hotspot + status ring + badge
  for (const [id, b] of Object.entries(layout.buildings)) {
    const w = X(b.w), h = Y(b.h), x = X(b.x) - w / 2, y = Y(b.y) - h / 2;
    const g = el("g", { id: "b-" + id }, svg);
    el("rect", { x, y, width: w, height: h, rx: 4,
      class: "ring healthy " + id }, g).classList.add("ring");
    const hot = el("rect", { x, y, width: w, height: h, rx: 4, class: "hotspot" }, g);
    hot.addEventListener("click", () => openTarget(id, b));
    const badge = el("text", { x: X(b.x), y: y - 4, "text-anchor": "middle",
      class: "badge", visibility: "hidden" }, g);
    const rec = { g, ring: g.querySelector(".ring"), badge, kind: b.kind };
    if (b.kind === "shop" || b.kind === "bank" || b.kind === "civic" || b.kind === "utility")
      REFS.civic[id] = rec;
    REFS.shops[id] = rec;
  }

  // intersections
  REFS.ints = layout.intersections.map(it => {
    const g = el("g", { id: "int" + it.id, class: "int" }, svg);
    const ns = el("circle", { cx: X(it.x), cy: Y(it.y) - 9, r: 4.5, class: "light off" }, g);
    const ew = el("circle", { cx: X(it.x) + 12, cy: Y(it.y), r: 4.5, class: "light off" }, g);
    const crash = el("text", { x: X(it.x) + 8, y: Y(it.y) - 14, class: "badge defaced",
      "font-size": 10 }, g);
    return { g, ns, ew, crash };
  });

  // houses + streetlights
  REFS.houses = layout.houses.map(hp => {
    const cx = X(hp.x), cy = Y(hp.y), g = el("g", { class: "house" }, svg);
    el("path", { d: `M ${cx - 11} ${cy + 9} L ${cx - 11} ${cy - 3} L ${cx} ${cy - 12} ` +
      `L ${cx + 11} ${cy - 3} L ${cx + 11} ${cy + 9} Z`,
      fill: "#2b2521", stroke: "#0f0d0b", "stroke-width": 1 }, g);
    // the window is the power indicator: yellow = powered, dark = out
    const win = el("rect", { x: cx - 4, y: cy - 1, width: 8, height: 8, rx: 1, class: "win" }, g);
    const drop = el("circle", { cx: cx + 7, cy: cy + 4, r: 2.6, class: "drop" }, g);
    return { win, drop };
  });
  REFS.streetlights = layout.streetlights.map(sp =>
    el("circle", { cx: X(sp.x), cy: Y(sp.y), r: 3, class: "streetlight" }, svg));
}

function openTarget(id, b) {
  // Phase 1+ opens the real service in a side panel; its first screen is a
  // login portal (Cross Creek / Widgetorium style). Phase 0 just names it.
  if (b.kind === "dressing") { toast(b.label + " — just scenery"); return; }
  toast(b.label + " — login portal opens here in Phase 1");
}

// --------------------------------------------------------------- render
function render(s) {
  const setStatus = (rec, status) => {
    if (!rec) return;
    rec.ring.setAttribute("class", "ring " + status + " " + (rec.ring.dataset.id || ""));
    if (status === "healthy") { rec.badge.setAttribute("visibility", "hidden"); }
    else {
      rec.badge.setAttribute("visibility", "visible");
      rec.badge.setAttribute("class", "badge " + status);
      rec.badge.textContent = status.replace("_", " ");
    }
  };

  (s.shops || []).forEach(sh => setStatus(REFS.shops[sh.key], sh.site_status));
  if (s.bank) {
    setStatus(REFS.shops["bank"], s.bank.site_status);
    if (!s.bank.alarm_armed && REFS.shops["bank"])
      REFS.shops["bank"].badge.setAttribute("visibility", "visible"),
      REFS.shops["bank"].badge.textContent = "alarm cut";
  }
  if (s.cityhall) setStatus(REFS.shops["cityhall"], s.cityhall.site_status);
  if (s.police) setStatus(REFS.shops["police"], s.police.site_status);
  if (s.fire) setStatus(REFS.shops["fire"], s.fire.site_status);

  // traffic
  (s.traffic || []).forEach((t, i) => {
    const R = REFS.ints[i]; if (!R) return;
    const setL = (node, c) => node.setAttribute("class", "light " + c);
    if (t.phase === "dark") { setL(R.ns, "off"); setL(R.ew, "off"); }
    else if (t.phase === "ALL-GREEN") { setL(R.ns, "green"); setL(R.ew, "green"); }
    else if (t.phase === "ns-green") { setL(R.ns, "green"); setL(R.ew, "red"); }
    else if (t.phase === "ew-green") { setL(R.ns, "red"); setL(R.ew, "green"); }
    else { setL(R.ns, "red"); setL(R.ew, "red"); }
    R.g.classList.toggle("hijacked", t.mode === "ALL-GREEN");
    R.crash.textContent = t.crash_count ? "⚠ " + t.crash_count : "";
  });

  // rail: the train runs the full perimeter loop; on a thrown switch it ends
  // up on the spur and stops.
  if (s.rail && REFS.rail) {
    const L = REFS.rail.getTotalLength();
    let p, ang;
    if (s.rail.derailed) {
      p = REFS.spur.getPointAtLength(REFS.spur.getTotalLength());
      const a = REFS.spur.getPointAtLength(0);
      ang = Math.atan2(p.y - a.y, p.x - a.x) * 180 / Math.PI;
    } else {
      const d = (s.rail.train_pos * L) % L;
      p = REFS.rail.getPointAtLength(d);
      const q = REFS.rail.getPointAtLength((d + 6) % L);
      ang = Math.atan2(q.y - p.y, q.x - p.x) * 180 / Math.PI;
    }
    REFS.train.setAttribute("transform", `translate(${p.x.toFixed(1)},${p.y.toFixed(1)}) rotate(${ang.toFixed(1)})`);
    REFS.spur.classList.toggle("spur-set", s.rail.switch_position === "spur");
    if (REFS.shops["factory"]) {
      REFS.shops["factory"].ring.classList.add("factory");
      REFS.shops["factory"].ring.classList.toggle("fire", !!s.rail.factory_fire);
    }
  }

  // water / sewage / power
  if (s.water) REFS.waterMain.classList.toggle("stopped", s.water.quality === "dry");
  if (s.sewage) {
    REFS.river.classList.toggle("foul", s.sewage.river_contamination > 0.4);
    REFS.outfall.setAttribute("stroke", s.sewage.effluent_path === "raw" ? "#7d6a3c" : "#4aa35b");
    REFS.swimmers.forEach(sw => sw.classList.toggle("sick", s.sewage.swimmers_sick));
  }
  if (s.power) {
    const f = s.power.feeders || {};
    REFS.powerFeeder.classList.toggle("stopped", f.residential === false);
    REFS.streetlights.forEach(sl => sl.classList.toggle("on", f.streetlights !== false));
  }
  (s.houses || []).forEach((h, i) => {
    if (!REFS.houses[i]) return;
    REFS.houses[i].win.classList.toggle("on", !!h.has_power);
    REFS.houses[i].drop.classList.toggle("on", !!h.has_water);
  });

  // hud
  const lvl = (s.alert && s.alert.level) || 0;
  document.getElementById("hud-alert").dataset.lvl = lvl;
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
  ws.onmessage = ev => {
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
  ["Dump General Store", { effect: "shop_sqli_dump", shop: "generalstore" }],
  ["Deface Barbershop", { effect: "shop_xss_deface", shop: "barber" }],
  ["Card the Diner Wi-Fi", { effect: "shop_carded", shop: "diner" }],
  ["Drain the Bank", { effect: "bank_drain" }],
  ["Deface Town Hall", { effect: "cityhall_deface", player: "debug" }],
  ["Drain payroll", { effect: "cityhall_payroll" }],
  ["Break water main", { effect: "water_main_break" }],
  ["Sewage bypass", { effect: "sewage_bypass" }],
  ["Trip industrial feeder", { effect: "power_trip_feeder", feeder: "industrial" }],
  ["Trip residential feeder", { effect: "power_trip_feeder", feeder: "residential" }],
  ["Hijack all lights", { effect: "traffic_all_green" }],
  ["Throw rail switch", { effect: "rail_switch_spur" }],
];

async function post(url, body) {
  await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}) });
}

function buildPanels(cfg) {
  const rb = document.getElementById("reset-buttons");
  (cfg.reset_scopes || ["all"]).forEach(scope => {
    const b = document.createElement("button");
    b.textContent = scope;
    if (scope === "all") b.className = "danger";
    b.onclick = () => post("/api/debug/reset", { scope });
    rb.appendChild(b);
  });
  const db = document.getElementById("debug-buttons");
  DEBUG_ACTIONS.forEach(([label, body]) => {
    const b = document.createElement("button");
    b.textContent = label; b.className = "danger";
    b.onclick = () => post("/api/debug/effect", body);
    db.appendChild(b);
  });
}

function setupDonation(tag) {
  const box = document.getElementById("donation");
  try { if (localStorage.getItem("pktr_donation_dismissed") === "1") return; } catch {}
  const link = document.getElementById("donation-link");
  link.textContent = "$" + tag;
  link.href = "https://cash.app/$" + tag;
  box.hidden = false;
  document.getElementById("donation-dismiss").onclick = () => {
    box.hidden = true;
    try { localStorage.setItem("pktr_donation_dismissed", "1"); } catch {}
  };
}

// ---------------------------------------------------------------- boot
(async function () {
  let layout, cfg = { reset_scopes: ["all"], cashapp: "britleywren", phase: 0 };
  try { layout = await (await fetch("/overlay.json")).json(); } catch (e) { console.error(e); }
  try { cfg = await (await fetch("/api/config")).json(); } catch {}
  if (layout) buildOverlay(layout);
  document.getElementById("phase-badge").textContent = "phase " + (cfg.phase ?? 0) + " · scaffold";
  buildPanels(cfg);
  setupDonation(cfg.cashapp || "britleywren");
  connect();
})();
