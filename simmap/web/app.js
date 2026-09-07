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
function $(id) { return document.getElementById(id); }
function toast(msg) {
  const t = $("toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { t.hidden = true; }, 2800);
}
async function api(path, method = "GET", body) {
  const r = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = {};
  try { data = await r.json(); } catch {}
  return { ok: r.ok, status: r.status, data };
}

// ----------------------------------------------------------- overlay build
const REFS = { shops: {}, ints: [], streetlights: [] };
let LAYOUT = null;

function buildOverlay(layout) {
  LAYOUT = layout;
  VB = layout.viewBox || [1000, 545];
  const svg = $("overlay");
  svg.setAttribute("viewBox", `0 0 ${VB[0]} ${VB[1]}`);
  svg.innerHTML = "";

  const r = layout.river;
  REFS.river = el("rect", { x: X(r.x), y: Y(r.y), width: X(r.w), height: Y(r.h), class: "river-body" }, svg);
  // the swim zone: a blocky "pixelated" contamination mosaic from the beach
  // edge (town side) across to the far bank, revealed as the water fouls
  const bz = layout.beachZone;
  if (bz) {
    REFS.beach = el("g", { class: "beach-mosaic" }, svg);
    const cell = X(0.011);
    for (let gx = X(bz.x); gx < X(bz.x + bz.w); gx += cell) {
      for (let gy = Y(bz.y); gy < Y(bz.y + bz.h); gy += cell) {
        el("rect", { x: gx, y: gy, width: cell - 0.6, height: cell - 0.6,
          opacity: (0.45 + Math.random() * 0.55).toFixed(2) }, REFS.beach);
      }
    }
  }
  // treated effluent flowing to the river: a moving blue line, green when the
  // treatment has been messed with
  REFS.outfall = el("polyline", {
    points: layout.outfall.map(p => `${X(p[0])},${Y(p[1])}`).join(" "),
    fill: "none", "stroke-width": 4, class: "flow outfall" }, svg);
  REFS.swimmers = layout.swimmers.map(p =>
    el("circle", { cx: X(p[0]), cy: Y(p[1]), r: 4, class: "swimmer" }, svg));

  const feed = (key, colour) => layout[key] && el("polyline", {
    points: layout[key].map(p => `${X(p[0])},${Y(p[1])}`).join(" "),
    fill: "none", stroke: colour, "stroke-width": 4, class: "flow" }, svg);
  REFS.waterMain       = feed("waterMain", "#2f8fbf");
  REFS.powerFeeder     = feed("powerFeeder", "#e3a52e");     // residential
  REFS.powerFeederBiz  = feed("powerFeederBiz", "#e3a52e");  // downtown / Main St
  REFS.powerFeederPlant = feed("powerFeederPlant", "#e3a52e"); // widget factory

  REFS.rail = el("polyline", {
    points: layout.railPath.map(p => `${X(p[0])},${Y(p[1])}`).join(" "),
    fill: "none", stroke: "none", opacity: 0 }, svg);
  const spur = layout.spurPath || [layout.spurBranch || layout.railPath[0], layout.spurEnd];
  REFS.spur = el("polyline", {
    points: spur.map(p => `${X(p[0])},${Y(p[1])}`).join(" "),
    fill: "none", stroke: "#6f6350", "stroke-width": 2.5, class: "spur" }, svg);
  REFS.train = el("g", { class: "train" }, svg);
  // fatter across the track (heights +3) without lengthening it (widths / x unchanged)
  el("rect", { x: -17, y: -6.5, width: 12, height: 13, fill: "#8a3b2f", stroke: "#3a1c16" }, REFS.train);
  el("rect", { x: -15, y: -11, width: 4, height: 5, fill: "#3a1c16" }, REFS.train);
  el("rect", { x: -4, y: -6, width: 9, height: 12, fill: "#4f3d30", stroke: "#251c15" }, REFS.train);
  el("rect", { x: 5, y: -6, width: 9, height: 12, fill: "#4f3d30", stroke: "#251c15" }, REFS.train);

  for (const [id, b] of Object.entries(layout.buildings)) {
    const w = X(b.w), h = Y(b.h), x = X(b.x) - w / 2, y = Y(b.y) - h / 2;
    const g = el("g", { id: "b-" + id }, svg);
    const ring = el("rect", { x, y, width: w, height: h, rx: 4, class: "ring healthy" }, g);
    const hot = el("rect", { x, y, width: w, height: h, rx: 4, class: "hotspot" }, g);
    hot.addEventListener("click", () => openTarget(id, b));
    const badge = el("text", { x: X(b.x), y: y - 4, "text-anchor": "middle", class: "badge", visibility: "hidden" }, g);
    REFS.shops[id] = { g, ring, badge, kind: b.kind };
  }

  REFS.ints = layout.intersections.map(it => {
    const g = el("g", { id: "int" + it.id, class: "int" }, svg);
    // one signal dot per crossroads — drop it on the light pole in the art
    const dot = el("circle", { cx: X(it.x), cy: Y(it.y), r: 4.5, class: "light off" }, g);
    const crash = el("text", { x: X(it.x) + 7, y: Y(it.y) - 8, class: "badge defaced", "font-size": 10 }, g);
    return { g, dot, crash };
  });

  REFS.streetlights = layout.streetlights.map(sp =>
    el("circle", { cx: X(sp.x), cy: Y(sp.y), r: 3, class: "streetlight" }, svg));

  // distribution dots: coloured by feeder / main, dim when de-energised
  const dots = (key, cls) => (layout[key] || []).map(pt =>
    el("circle", { cx: X(pt.x), cy: Y(pt.y), r: 3.2, class: cls }, svg));
  REFS.powerRes   = dots("powerResidential", "gdot res");
  REFS.powerBiz   = dots("powerBusiness", "gdot biz");
  REFS.powerPlant = dots("powerPlant", "gdot plant");
  REFS.waterRes   = dots("waterResidential", "wdot");

  // hook for the ?edit=1 overlay editor (edit.js); inert otherwise
  window.PKTR_EDIT = { layout, VB, overlay: svg, rebuild: () => buildOverlay(layout) };
}

// ---------------------------------------------------------------- render
function setStatus(rec, status) {
  if (!rec) return;
  rec.ring.setAttribute("class", "ring " + status);
  if (status === "healthy") {
    rec.badge.setAttribute("visibility", "hidden");
  } else {
    rec.badge.setAttribute("visibility", "visible");
    rec.badge.setAttribute("class", "badge " + status);
    rec.badge.textContent = status.replace("_", " ");
  }
}

function render(s) {
  (s.shops || []).forEach(sh => setStatus(REFS.shops[sh.key], sh.site_status));
  if (s.bank) {
    setStatus(REFS.shops["bank"], s.bank.site_status);
    if (!s.bank.alarm_armed && REFS.shops["bank"]) {
      REFS.shops["bank"].badge.setAttribute("visibility", "visible");
      REFS.shops["bank"].badge.textContent = "alarm cut";
    }
  }
  if (s.cityhall) setStatus(REFS.shops["cityhall"], s.cityhall.site_status);
  if (s.police) setStatus(REFS.shops["police"], s.police.site_status);
  if (s.fire) setStatus(REFS.shops["fire"], s.fire.site_status);

  (s.traffic || []).forEach((t, i) => {
    const R = REFS.ints[i]; if (!R) return;
    let c = "red";
    if (t.phase === "dark") c = "off";
    else if (t.phase === "ns-green" || t.phase === "ew-green" || t.phase === "ALL-GREEN") c = "green";
    R.dot.setAttribute("class", "light " + c);
    R.g.classList.toggle("hijacked", t.mode === "ALL-GREEN");
    R.crash.textContent = t.crash_count ? "⚠ " + t.crash_count : "";
  });

  if (s.rail && REFS.rail) {
    const L = REFS.rail.getTotalLength();
    const SL = REFS.spur.getTotalLength();
    let p, ang, show = true;
    if (s.rail.on_spur || s.rail.derailed) {
      // routed onto the spur: travel it from the branch down to the plant,
      // then hold at the factory once derailed
      const frac = s.rail.derailed ? 1.0 : (s.rail.spur_pos || 0);
      const d = Math.min(SL, frac * SL);
      p = REFS.spur.getPointAtLength(d);
      const q = REFS.spur.getPointAtLength(Math.max(0, d - 6));
      ang = Math.atan2(p.y - q.y, p.x - q.x) * 180 / Math.PI;
    } else if (s.rail.train_pos < 1.0) {
      const d = s.rail.train_pos * L;
      p = REFS.rail.getPointAtLength(d);
      const q = REFS.rail.getPointAtLength(Math.min(L, d + 6));
      ang = Math.atan2(q.y - p.y, q.x - p.x) * 180 / Math.PI;
    } else { show = false; }
    REFS.train.setAttribute("visibility", show ? "visible" : "hidden");
    if (show)
      REFS.train.setAttribute("transform",
        `translate(${p.x.toFixed(1)},${p.y.toFixed(1)}) rotate(${ang.toFixed(1)})`);
    REFS.spur.classList.toggle("spur-set", s.rail.switch_position === "spur");
  }

  // factory: fire from a derail, or a "trouble" ring from a PLC jam
  if (REFS.shops["factory"]) {
    const f = s.factory || {};
    const R = REFS.shops["factory"];
    R.ring.classList.add("factory");
    R.ring.classList.toggle("fire", !!(f.on_fire || (s.rail && s.rail.factory_fire)));
    const trouble = f.line_jam || (f.throughput_pct != null && f.throughput_pct < 40);
    R.ring.setAttribute("class", "ring " + (trouble && !f.on_fire ? "db_dumped factory" : "healthy factory"));
    if (f.on_fire) R.ring.classList.add("fire");
    R.badge.setAttribute("visibility", trouble || f.on_fire ? "visible" : "hidden");
    R.badge.textContent = f.on_fire ? "fire" : (trouble ? "line jam" : "");
    if (trouble || f.on_fire) R.badge.setAttribute("class", "badge db_dumped");
  }

  if (s.water) REFS.waterMain.classList.toggle("stopped", s.water.quality === "dry");
  if (s.sewage) {
    const raw = s.sewage.effluent_path === "raw";
    const c = Math.max(0, Math.min(1, s.sewage.river_contamination));
    // the only contamination visual: the pixelated swim-zone mosaic, revealed
    // as the water fouls
    if (REFS.beach)
      REFS.beach.style.opacity = (s.sewage.swimmers_sick || c > 0.2)
        ? (0.35 + 0.5 * c).toFixed(2) : 0;
    REFS.outfall.classList.toggle("foul", raw);
    REFS.swimmers.forEach(sw => sw.classList.toggle("sick", s.sewage.swimmers_sick));
  }
  if (s.power) {
    const f = s.power.feeders || {};
    REFS.powerFeeder.classList.toggle("stopped", f.residential === false);
    if (REFS.powerFeederBiz) REFS.powerFeederBiz.classList.toggle("stopped", f.business === false);
    if (REFS.powerFeederPlant) REFS.powerFeederPlant.classList.toggle("stopped", f.industrial === false);
    const lit = (arr, up) => arr.forEach(d => d.classList.toggle("on", up));
    lit(REFS.streetlights, f.streetlights !== false);
    lit(REFS.powerRes, f.residential !== false);
    lit(REFS.powerBiz, f.business !== false);
    lit(REFS.powerPlant, f.industrial !== false);
  }
  if (s.water)
    REFS.waterRes.forEach(d => d.classList.toggle("on", s.water.quality !== "dry"));

  const lvl = (s.alert && s.alert.level) || 0;
  $("hud-alert").dataset.lvl = lvl;
  $("hud-alert-lvl").textContent = lvl;

  // surface the blue team's latest response as a toast
  const acts = (s.alert && s.alert.blue_actions) || [];
  const last = acts[acts.length - 1] || "";
  if (last && last !== render._lastSoc) {
    render._lastSoc = last;
    toast("SOC: " + last);
  }
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
  const c = $("hud-conn");
  c.dataset.up = up ? "yes" : "no";
  $("hud-conn-lbl").textContent = up ? "live" : "down";
}

// -------------------------------------------------------------- account
let ME = { anon: true };

async function refreshMe() {
  const { data } = await api("/api/score/me");
  ME = data;
  $("hud-score").textContent = data.total ?? 0;
  $("hud-best").textContent = data.best ?? 0;
  const anon = !!data.anon;
  $("auth-box").hidden = !anon;
  $("run-box").hidden = anon;
  $("who").textContent = anon ? "" : data.name;
  if (!anon) {
    const run = data.active_run;
    $("run-state").textContent = run
      ? `Run #${run.id} active — ${run.score_so_far} pts this run.`
      : "No run started. Hit Start.";
  }
}

async function refreshBoard() {
  const { data } = await api("/api/score/leaderboard");
  const ol = $("board");
  ol.innerHTML = "";
  if (!Array.isArray(data) || !data.length) {
    ol.innerHTML = '<li class="hint">nobody on the board yet</li>';
    return;
  }
  data.forEach(row => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${escapeHtml(row.name)}</span><b>${row.best_run_total}</b>`;
    ol.appendChild(li);
  });
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function wireAccount() {
  $("auth-form").addEventListener("submit", async e => {
    e.preventDefault();
    await doAuth("/api/score/login");
  });
  $("auth-register").addEventListener("click", () => doAuth("/api/score/register"));
  $("auth-logout").addEventListener("click", async () => {
    await api("/api/score/logout", "POST", {});
    await refreshMe();
  });
  $("run-start").addEventListener("click", async () => {
    const { ok, data } = await api("/api/score/run", "POST", {});
    if (ok) { toast("run #" + data.run_id + " started"); refreshMe(); }
    else toast(data.error || "could not start run");
  });
}

async function doAuth(path) {
  const name = $("auth-name").value.trim();
  const password = $("auth-pass").value;
  const errEl = $("auth-err");
  errEl.hidden = true;
  const { ok, data } = await api(path, "POST", { name, password });
  if (ok) {
    $("auth-pass").value = "";
    await refreshMe();
    await refreshBoard();
  } else {
    errEl.textContent = data.error || "that didn't work";
    errEl.hidden = false;
  }
}

// ----------------------------------------------------------- site panel
function openTarget(id, b) {
  if (b.kind === "dressing") { toast(b.label + " — just scenery"); return; }
  if (!b.port) { toast(b.label + " — comes online in a later phase"); return; }
  const url = `${location.protocol}//${location.hostname}:${b.port}${b.path || "/"}`;
  $("sitepanel-title").textContent = b.label + " — login portal";
  $("sitepanel-open").href = url;
  $("sitepanel-frame").src = url;
  const term = $("sitepanel-term");
  if (b.terminal) {
    term.href = `${location.protocol}//${location.hostname}:${b.terminal}/`;
    term.textContent = (b.terminal_label || "terminal") + " ↗";
    term.hidden = false;
  } else {
    term.hidden = true;
  }
  $("flag-input").value = "";
  $("flag-result").textContent = "";
  $("submit-flag").hidden = !b.technique;
  $("submit-flag").dataset.technique = b.technique || "";
  $("sitepanel").hidden = false;
}

function wireSitePanel() {
  $("sitepanel-close").addEventListener("click", () => {
    $("sitepanel").hidden = true;
    $("sitepanel-frame").src = "about:blank";
  });
  $("submit-flag").addEventListener("submit", async e => {
    e.preventDefault();
    const flag = $("flag-input").value.trim();
    const res = $("flag-result");
    if (ME.anon) { res.textContent = "log in first"; return; }
    if (!ME.active_run) { res.textContent = "start a run first"; return; }
    res.textContent = "checking…";
    const { data } = await api("/api/score/submit", "POST", { flag });
    if (data.accepted) {
      res.textContent = `+${data.points} (${JSON.stringify(data.breakdown)})`;
      toast(`+${data.points} — ${data.target} breached`);
      refreshMe(); refreshBoard();
    } else {
      res.textContent = data.detail || "not a valid flag";
    }
  });
}

// ---------------------------------------------------------------- panels
const DEBUG_ACTIONS = [
  ["Deface Barbershop", { effect: "shop_xss_deface", shop: "barber" }],
  ["Card the Diner Wi-Fi", { effect: "shop_carded", shop: "diner" }],
  ["Drain the Bank", { effect: "bank_drain" }],
  ["Deface Town Hall", { effect: "cityhall_deface", player: "debug" }],
  ["Break water main", { effect: "water_main_break" }],
  ["Sewage bypass", { effect: "sewage_bypass" }],
  ["Trip residential feeder", { effect: "power_trip_feeder", feeder: "residential" }],
  ["Trip business feeder", { effect: "power_trip_feeder", feeder: "business" }],
  ["Trip plants feeder", { effect: "power_trip_feeder", feeder: "industrial" }],
  ["Hijack all lights", { effect: "traffic_all_green" }],
  ["Throw rail switch", { effect: "rail_switch_spur" }],
];

async function post(url, body) {
  await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
}

function buildPanels(cfg) {
  const rb = $("reset-buttons");
  (cfg.reset_scopes || ["all"]).forEach(scope => {
    const b = document.createElement("button");
    b.textContent = scope;
    if (scope === "all") b.className = "danger";
    b.onclick = () => post("/api/debug/reset", { scope });
    rb.appendChild(b);
  });
  const db = $("debug-buttons");
  DEBUG_ACTIONS.forEach(([label, body]) => {
    const b = document.createElement("button");
    b.textContent = label; b.className = "danger";
    b.onclick = () => post("/api/debug/effect", body);
    db.appendChild(b);
  });
}

function setupDonation(tag) {
  const box = $("donation");
  try { if (localStorage.getItem("pktr_donation_dismissed") === "1") return; } catch {}
  const link = $("donation-link");
  link.textContent = "$" + tag;
  link.href = "https://cash.app/$" + tag;
  box.hidden = false;
  $("donation-dismiss").onclick = () => {
    box.hidden = true;
    try { localStorage.setItem("pktr_donation_dismissed", "1"); } catch {}
  };
}

// ---------------------------------------------------------------- boot
(async function () {
  let layout, cfg = { reset_scopes: ["all"], cashapp: "britleywren", phase: 1 };
  try { layout = await (await fetch("/overlay.json")).json(); } catch (e) { console.error(e); }
  try { cfg = await (await fetch("/api/config")).json(); } catch {}
  if (layout) buildOverlay(layout);
  $("phase-badge").textContent = "phase " + (cfg.phase ?? 1);
  buildPanels(cfg);
  setupDonation(cfg.cashapp || "britleywren");
  wireAccount();
  wireSitePanel();
  connect();
  await refreshMe();
  await refreshBoard();
  setInterval(refreshMe, 5000);
  setInterval(refreshBoard, 12000);
})();
