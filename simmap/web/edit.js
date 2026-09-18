"use strict";
/* Packet River overlay editor.
 *
 * Loads for everyone but does nothing unless the page URL has ?edit=1.
 * With it on: a draggable handle for every coordinate in overlay.json, a
 * calibration grid, a live cursor readout, and a JSON panel you copy or
 * download straight back into simmap/web/overlay.json.
 *
 *   http://127.0.0.1:8080/?edit=1
 *
 * Drag a handle to move it. Buildings and the river get a second handle at
 * the bottom-right corner for size. Arrow keys nudge the selection by 0.001
 * (Shift = 0.01). [ and ] cycle the selection. g cycles the grid. On a
 * polyline vertex: Alt+click the layer to insert one after it, Delete to
 * remove it. The real overlay redraws live as you drag.
 */
(function () {
  if (!/[?&]edit=1(?:&|$)/.test(location.search)) return;

  const SVGNS = "http://www.w3.org/2000/svg";
  const r4 = (n) => Math.round(n * 1e4) / 1e4;
  const PE_STROKE = 1.2; // must match #pe-layer .pe-shape's stroke-width below
  const mk = (tag, attrs, parent) => {
    const n = document.createElementNS(SVGNS, tag);
    for (const k in attrs || {}) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  };

  let S = null;                 // window.PKTR_EDIT from app.js
  let L = null;                 // the live layout object (=== app's LAYOUT)
  let VB = [1408, 736];
  let initialJSON = "";
  const ui = {};
  let handles = [];             // ordered accessor list for cycling
  let sel = null;               // selected accessor
  let grid = 0;                 // 0 | 20 | 40  (lines count)
  let rebuildQueued = false;

  waitFor(() => window.PKTR_EDIT && window.PKTR_EDIT.layout, start);

  function waitFor(test, fn, tries = 200) {
    if (test()) return fn();
    if (tries <= 0) return console.warn("[edit] PKTR_EDIT never appeared");
    setTimeout(() => waitFor(test, fn, tries - 1), 60);
  }

  // ---------------------------------------------------------------- start
  function start() {
    S = window.PKTR_EDIT;
    L = S.layout;
    VB = S.VB || [1408, 736];
    initialJSON = JSON.stringify(L, null, 2);
    injectStyle();
    buildPanel();
    buildLayer();
    document.body.classList.add("pktr-editing");
    window.addEventListener("keydown", onKey);
    renderAll();
    console.log("[edit] overlay editor active — ?edit=1");
  }

  function injectStyle() {
    const css = `
      body.pktr-editing #overlay { pointer-events: none; }
      #pe-layer { position:absolute; inset:0; width:100%; height:100%; z-index:5; }
      #pe-layer .pe-grid line { stroke: rgba(0,200,255,.18); stroke-width:1; }
      #pe-layer .pe-grid text { fill: rgba(0,200,255,.5); font: 9px monospace; }
      #pe-layer .pe-shape { fill:none; stroke:#12b6d8; stroke-width:1.2; stroke-dasharray:4 3; }
      #pe-layer .pe-road { stroke:#4a4a4a; stroke-width:2; stroke-dasharray:6 4; }
      #pe-layer .pe-h { fill:#12b6d8; stroke:#04303a; stroke-width:1; cursor:grab; }
      #pe-layer .pe-h:hover { fill:#38d9f5; }
      #pe-layer .pe-h.sel { fill:#ff3bd0; stroke:#3a0030; }
      #pe-layer .pe-h.size { fill:#f6c445; }
      #pe-panel { position:fixed; right:12px; bottom:12px; z-index:9999; width:360px;
        max-height:78vh; display:flex; flex-direction:column; gap:6px;
        background:#0d1117ee; color:#c9d4e0; border:1px solid #2b3440; border-radius:10px;
        padding:10px; font:12px/1.4 ui-monospace,Menlo,monospace; backdrop-filter:blur(3px); }
      #pe-panel h4 { margin:0; font-size:12px; color:#38d9f5; letter-spacing:.5px; cursor:pointer; user-select:none; }
      #pe-panel.collapsed > *:not(h4) { display:none; }
      #pe-panel.collapsed { width:auto; }
      #pe-panel .row { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
      #pe-panel button { background:#1b2530; color:#c9d4e0; border:1px solid #33404d;
        border-radius:6px; padding:4px 8px; cursor:pointer; font:inherit; }
      #pe-panel button:hover { background:#243140; }
      #pe-panel button.warn { border-color:#7a3b3b; }
      #pe-panel .mono { color:#8aa0b4; }
      #pe-panel .sel { color:#ff8fe0; }
      #pe-tilt label { display:flex; align-items:center; gap:4px; color:#8aa0b4; }
      #pe-tilt input { width:52px; background:#05080c; color:#c9d4e0;
        border:1px solid #222c36; border-radius:6px; padding:2px 4px; font:inherit; }
      #pe-tilt #pe-rot-ccw, #pe-tilt #pe-rot-cw { padding:2px 6px; font-size:13px; line-height:1; }
      .pe-legend-h { display:inline-block; width:9px; height:9px; border-radius:50%;
        background:#12b6d8; vertical-align:middle; margin-right:2px; }
      .pe-legend-h.size { border-radius:2px; background:#f6c445; }
      .pe-legend-h.sel { background:#ff3bd0; }
      #pe-json { width:100%; flex:1 1 auto; min-height:180px; resize:vertical;
        background:#05080c; color:#9fb4c6; border:1px solid #222c36; border-radius:6px;
        padding:6px; font:11px/1.35 ui-monospace,monospace; white-space:pre; }
      #pe-msg { min-height:14px; color:#f6c445; }
    `;
    const s = document.createElement("style");
    s.id = "pe-style";
    s.textContent = css;
    document.head.appendChild(s);
  }

  function buildPanel() {
    const p = document.createElement("div");
    p.id = "pe-panel";
    p.innerHTML = `
      <h4 title="click to collapse">OVERLAY EDITOR ▾</h4>
      <div class="row mono" style="gap:4px">${legendHTML()}</div>
      <div class="row mono" style="gap:10px">
        <span><span class="pe-legend-h"></span> move</span>
        <span><span class="pe-legend-h size"></span> resize</span>
        <span><span class="pe-legend-h sel"></span> selected</span>
      </div>
      <div class="row mono">cursor <span id="pe-cur">–</span></div>
      <div class="row"><span class="sel" id="pe-sel">nothing selected</span></div>
      <div class="row" id="pe-tilt" hidden>
        <label>rotate
          <button id="pe-rot-ccw" type="button" title="turn left (shift = bigger step)">&#8630;</button>
          <input id="pe-rot" type="number" step="1" value="0">
          <button id="pe-rot-cw" type="button" title="turn right (shift = bigger step)">&#8631;</button>
        </label>
        <label>skew X <input id="pe-skx" type="number" step="1" value="0"></label>
        <label>skew Y <input id="pe-sky" type="number" step="1" value="0"></label>
        <button id="pe-tilt-reset" title="rotate=0, skewX=0, skewY=0">reset</button>
      </div>
      <div class="row">
        <button id="pe-grid">grid: off</button>
        <button id="pe-prev">[ prev</button>
        <button id="pe-next">next ]</button>
        <button id="pe-sel-train" title="jump straight to the moving train, instead of hunting for its dot or cycling through every other handle">select train</button>
        <button id="pe-revert" class="warn">revert</button>
      </div>
      <div class="row">
        <button id="pe-copy">copy JSON</button>
        <button id="pe-dl">download</button>
        <button id="pe-apply">apply edits ↑</button>
      </div>
      <div id="pe-msg"></div>
      <textarea id="pe-json" spellcheck="false"></textarea>
    `;
    document.body.appendChild(p);
    p.querySelector("h4").onclick = () => p.classList.toggle("collapsed");
    ui.cur = p.querySelector("#pe-cur");
    ui.sel = p.querySelector("#pe-sel");
    ui.msg = p.querySelector("#pe-msg");
    ui.json = p.querySelector("#pe-json");
    ui.tilt = p.querySelector("#pe-tilt");
    ui.rot = p.querySelector("#pe-rot");
    ui.skx = p.querySelector("#pe-skx");
    ui.sky = p.querySelector("#pe-sky");
    p.querySelector("#pe-grid").onclick = cycleGrid;
    p.querySelector("#pe-prev").onclick = () => cycleSel(-1);
    p.querySelector("#pe-next").onclick = () => cycleSel(1);
    p.querySelector("#pe-sel-train").onclick = () => {
      const h = handles.find((x) => x.id === "train");
      if (h) select(h); else msg("train handle not found - reload the page?");
    };
    p.querySelector("#pe-revert").onclick = revert;
    p.querySelector("#pe-copy").onclick = copyJSON;
    p.querySelector("#pe-dl").onclick = downloadJSON;
    p.querySelector("#pe-apply").onclick = applyJSON;
    const tiltInput = (input, field) => input.addEventListener("input", () => {
      if (!sel || !sel.building) return;
      const n = Number(input.value);
      sel.building.sprite[field] = Number.isFinite(n) ? n : 0;
      queueRebuild();
    });
    tiltInput(ui.rot, "rotate");
    tiltInput(ui.skx, "skewX");
    tiltInput(ui.sky, "skewY");
    // turn-left/turn-right buttons beside the rotate field, for nudging by
    // eye instead of typing a degree value - 1deg per click, shift-click
    // for a coarser 5deg step, same shift-for-bigger-step convention as the
    // arrow-key nudge on a position handle
    const bumpRotate = (dir) => (e) => {
      if (!sel || !sel.building) return;
      const step = e.shiftKey ? 5 : 1;
      const cur = Number(ui.rot.value) || 0;
      const next = r4(cur + dir * step);
      ui.rot.value = next;
      sel.building.sprite.rotate = next;
      queueRebuild();
    };
    p.querySelector("#pe-rot-ccw").onclick = bumpRotate(-1);
    p.querySelector("#pe-rot-cw").onclick = bumpRotate(1);
    p.querySelector("#pe-tilt-reset").onclick = () => {
      if (!sel || !sel.building) return;
      delete sel.building.sprite.rotate;
      delete sel.building.sprite.skewX;
      delete sel.building.sprite.skewY;
      ui.rot.value = ui.skx.value = ui.sky.value = 0;
      queueRebuild();
    };
  }

  function buildLayer() {
    const scene = S.overlay.parentNode;
    const svg = mk("svg", { id: "pe-layer", viewBox: `0 0 ${VB[0]} ${VB[1]}`,
      preserveAspectRatio: "xMidYMid meet" });
    scene.appendChild(svg);
    ui.layer = svg;
    ui.grid = mk("g", { class: "pe-grid" }, svg);
    ui.sprites = mk("g", { class: "pe-sprites" }, svg);
    ui.shapes = mk("g", { class: "pe-shapes" }, svg);
    ui.handles = mk("g", { class: "pe-handles" }, svg);
    svg.addEventListener("pointermove", (e) => {
      const f = frac(e);
      ui.cur.textContent = `x ${f.x.toFixed(4)}  y ${f.y.toFixed(4)}`;
    });
    svg.addEventListener("pointerdown", (e) => {
      if (e.target === svg && e.altKey && sel && sel.kind === "vertex") insertVertex(frac(e));
      else if (e.target === svg) select(null);
    });
  }

  // ------------------------------------------------------------- geometry
  function frac(evt) {
    const svg = ui.layer;
    const pt = svg.createSVGPoint();
    pt.x = evt.clientX;
    pt.y = evt.clientY;
    const p = pt.matrixTransform(svg.getScreenCTM().inverse());
    return { x: p.x / VB[0], y: p.y / VB[1] };
  }
  const px = (fx) => fx * VB[0];
  const py = (fy) => fy * VB[1];

  // handle fill matches the live map colour of whatever it edits, so you can
  // tell the layers apart while dragging - also drives the legend in the
  // panel, so a new entry here shows up there automatically
  const DEFAULT_COLOUR = "#12b6d8"; // buildings, and anything unmatched
  const HANDLE_COLOUR = [
    { label: "building", re: /^bld /, c: DEFAULT_COLOUR },
    { label: "intersection", re: /^int /, c: "#8fd18f" },
    { label: "streetlight", re: /^light /, c: "#f2f2ec" },
    { label: "power: residential", re: /^P-res /, c: "#f0cf5c" },
    { label: "power: business", re: /^P-biz /, c: "#e88a2e" },
    { label: "power: plant", re: /^P-plant /, c: "#9aa0aa" },
    { label: "water: residential", re: /^W-res /, c: "#4aa8e0" },
    { label: "rail / spur", re: /^(railPath|spurPath) /, c: "#d98a6a" },
    { label: "road", re: /^road:/, c: "#4a4a4a" },
    { label: "swimmers", re: /^swimmers /, c: "#ffe4b8" },
    { label: "outfall", re: /^outfall /, c: "#7cb03a" },
    { label: "water main", re: /^waterMain /, c: "#2f8fbf" },
    { label: "power feeder", re: /^powerFeeder/, c: "#e3a52e" },
    { label: "river", re: /^river$/, c: "#3a8fb0" },
    { label: "beach zone", re: /^beachZone$/, c: "#6fae54" },
  ];
  const colourFor = (id) => {
    for (const { re, c } of HANDLE_COLOUR) if (re.test(id)) return c;
    return DEFAULT_COLOUR;
  };
  const legendHTML = () => HANDLE_COLOUR
    .map(({ label, c }) => `<span style="color:${c}">&#9679;${label}</span>`).join("");

  // ------------------------------------------------ accessor collection
  // Every editable thing becomes an accessor: { id, kind, get()->[x,y],
  //   set(x,y), and for sizables getSize()/setSize(). kind drives the key
  //   handling (vertex = member of a [[x,y]] list, so it can be inserted /
  //   deleted). }
  function collect() {
    const A = [];
    const push = (o) => { A.push(o); return o; };

    for (const [id, b] of Object.entries(L.buildings || {})) {
      if (b.sprite) {
        // drag the building directly by what you see: get/set operate on the
        // sprite's own rendered box (top-left + size), not the underlying
        // x,y,w,h/anchor fields - same math as app.js's drawBuildingSprite()
        // and this file's drawSpritePreviews(), kept in sync via spriteBox()
        push({ id: "bld " + id, kind: "rect", building: b,
          get: () => { const o = spriteBox(b); return [o[0], o[1]]; },
          set: (x, y) => {
            const [, , w, h] = spriteBox(b);
            const spr = b.sprite, ax = spr.anchorX ?? 0.5, ay = spr.anchorY ?? 1.0;
            b.x = r4(x + w * ax);
            b.y = r4(y + h * ay - b.h / 2);
          },
          getSize: () => { const o = spriteBox(b); return [o[2], o[3]]; },
          setSize: (w) => { b.sprite.scale = r4(Math.max(0.05, w / b.w)); },
          outline: () => spriteBox(b) });
      } else {
        push({ id: "bld " + id, kind: "box",
          get: () => [b.x, b.y], set: (x, y) => { b.x = r4(x); b.y = r4(y); },
          getSize: () => [b.w, b.h],
          setSize: (w, h) => { b.w = r4(Math.max(0.004, w)); b.h = r4(Math.max(0.004, h)); },
          outline: () => [b.x - b.w / 2, b.y - b.h / 2, b.w, b.h] });
      }
    }
    // the train: no fixed x/y of its own (it's animated along railPath/
    // spurPath every tick by app.js's render()), so drag/rotate/skew all
    // act on layout.train.sprite instead of a static box. get() reports
    // the train's current on-screen point (its live path position plus
    // whatever offsetX/offsetY nudge is already dialed in); set() converts
    // a drag back into that offset, using the same "raw" path point app.js
    // stamps onto S.trainLive.raw every tick (deliberately off L, not part
    // of the saved layout) so the handle tracks a moving target instead of
    // a fixed spot - unless select() has frozen it, see below.
    if (L.train && L.train.sprite) {
      push({ id: "train", kind: "point", building: { sprite: L.train.sprite },
        get: () => {
          const raw = (S.trainLive && S.trainLive.raw) || { x: 0.5, y: 0.5 };
          const spr = L.train.sprite;
          return [r4(raw.x + (spr.offsetX || 0)), r4(raw.y + (spr.offsetY || 0))];
        },
        set: (x, y) => {
          const raw = (S.trainLive && S.trainLive.raw) || { x: 0.5, y: 0.5 };
          L.train.sprite.offsetX = r4(x - raw.x);
          L.train.sprite.offsetY = r4(y - raw.y);
        } });
    }
    (L.intersections || []).forEach((p) => push({ id: "int " + p.id, kind: "point",
      get: () => [p.x, p.y], set: (x, y) => { p.x = r4(x); p.y = r4(y); } }));
    const pts = (key, label) => (L[key] || []).forEach((p, i) => push({
      id: label + " " + i, kind: "point",
      get: () => [p.x, p.y], set: (x, y) => { p.x = r4(x); p.y = r4(y); } }));
    pts("streetlights", "light");
    pts("powerResidential", "P-res");
    pts("powerBusiness", "P-biz");
    pts("powerPlant", "P-plant");
    pts("waterResidential", "W-res");

    ["railPath", "spurPath", "outfall", "waterMain", "powerFeeder", "powerFeederBiz", "powerFeederPlant", "swimmers"].forEach((key) => {
      const arr = L[key];
      if (!Array.isArray(arr)) return;
      arr.forEach((_, i) => push({ id: key + " " + i, kind: "vertex", arr, key,
        get: () => arr[i].slice(), set: (x, y) => { arr[i] = [r4(x), r4(y)]; },
        idx: () => arr.indexOf(arr[i]) }));
    });
    // road network (layout.roads: {id: [[x,y],...]}) - invisible on the
    // live map (roads are painted into the terrain) but fully editable
    // here, same vertex mechanics as railPath/spurPath: drag a point, Alt+
    // click the layer to insert one after the selected vertex, Delete to
    // remove it. Add a brand new named road by hand-editing the JSON panel.
    for (const [roadId, arr] of Object.entries(L.roads || {})) {
      if (!Array.isArray(arr)) continue;
      arr.forEach((_, i) => push({ id: "road:" + roadId + " " + i, kind: "vertex", arr, key: "road:" + roadId,
        get: () => arr[i].slice(), set: (x, y) => { arr[i] = [r4(x), r4(y)]; },
        idx: () => arr.indexOf(arr[i]) }));
    }
    for (const key of ["river", "beachZone"]) {
      const rv = L[key];
      if (!rv) continue;
      push({ id: key, kind: "rect",
        get: () => [rv.x, rv.y], set: (x, y) => { rv.x = r4(x); rv.y = r4(y); },
        getSize: () => [rv.w, rv.h],
        setSize: (w, h) => { rv.w = r4(Math.max(0.01, w)); rv.h = r4(Math.max(0.01, h)); },
        outline: () => [rv.x, rv.y, rv.w, rv.h] });
    }
    return A;
  }

  // ------------------------------------------------------------- rendering
  function renderAll() {
    handles = collect();
    if (sel) sel = handles.find((h) => h.id === sel.id) || null;
    drawGrid();
    drawSpritePreviews();
    drawShapes();
    drawHandles();
    updateJSON();
    updateSelLabel();
  }

  // a sprited building's rendered box, in fraction units: [x, y, w, h] with
  // x,y = top-left, w = fraction of VB[0], h = fraction of VB[1] (same
  // outline() convention as river/beachZone). Single source of truth for the
  // drag handle (collect()) and the faint art preview (drawSpritePreviews())
  // below - matches app.js's drawBuildingSprite(); keep the two in sync.
  function spriteBox(b) {
    const spr = b.sprite;
    const rw = b.w * (spr.scale || 1);
    const rh = rw * VB[0] / VB[1] * (spr.h / spr.w);
    const anchorX = spr.anchorX ?? 0.5, anchorY = spr.anchorY ?? 1.0;
    const gx = b.x - rw * anchorX;
    const gy = (b.y + b.h / 2) - rh * anchorY;
    return [gx, gy, rw, rh];
  }

  // faint preview of a building's sprite art under its drag handles, so
  // placing/resizing is done against the real art, not a blank rectangle.
  function drawSpritePreviews() {
    ui.sprites.innerHTML = "";
    for (const b of Object.values(L.buildings || {})) {
      if (!b.sprite) continue;
      const [gx, gy, rw, rh] = spriteBox(b);
      const spr = b.sprite;
      const rot = spr.rotate || 0, skx = spr.skewX || 0, sky = spr.skewY || 0;
      let parent = ui.sprites;
      if (rot || skx || sky) {
        const cx = px(b.x), cy = py(b.y + b.h / 2);
        parent = mk("g", { transform:
          `translate(${cx},${cy}) rotate(${rot}) skewX(${skx}) skewY(${sky}) translate(${-cx},${-cy})` }, ui.sprites);
      }
      mk("image", { href: spr.src, x: px(gx), y: py(gy), width: px(rw), height: py(rh),
        opacity: 0.65 }, parent);
    }
  }

  function drawGrid() {
    ui.grid.innerHTML = "";
    if (!grid) return;
    const step = 100 / grid;
    for (let pct = 0; pct <= 100 + 1e-6; pct += step) {
      const gx = (pct / 100) * VB[0];
      const gy = (pct / 100) * VB[1];
      mk("line", { x1: gx, y1: 0, x2: gx, y2: VB[1] }, ui.grid);
      mk("line", { x1: 0, y1: gy, x2: VB[0], y2: gy }, ui.grid);
      if (Math.round(pct) % 10 === 0) {
        mk("text", { x: gx + 2, y: 10 }, ui.grid).textContent = pct.toFixed(0);
        mk("text", { x: 2, y: gy - 2 }, ui.grid).textContent = pct.toFixed(0);
      }
    }
  }

  function drawShapes() {
    ui.shapes.innerHTML = "";
    // polylines
    ["railPath", "spurPath", "outfall", "waterMain", "powerFeeder", "powerFeederBiz", "powerFeederPlant"].forEach((key) => {
      const arr = L[key];
      if (!Array.isArray(arr) || arr.length < 2) return;
      mk("polyline", { class: "pe-shape",
        points: arr.map((p) => `${px(p[0])},${py(p[1])}`).join(" ") }, ui.shapes);
    });
    for (const arr of Object.values(L.roads || {})) {
      if (!Array.isArray(arr) || arr.length < 2) continue;
      mk("polyline", { class: "pe-shape pe-road",
        points: arr.map((p) => `${px(p[0])},${py(p[1])}`).join(" ") }, ui.shapes);
    }
    // box / rect outlines - inset by half the stroke width so the drawn
    // line's outer edge lands exactly on the box (image) edge instead of
    // straddling it; a centered SVG stroke would otherwise overshoot by
    // stroke-width/2 on every side, making the outline visibly bigger than
    // the sprite art it is supposed to hug
    handles.filter((h) => h.outline).forEach((h) => {
      const [ox, oy, ow, oh] = h.outline();
      const sw = PE_STROKE;
      mk("rect", { class: "pe-shape",
        x: px(ox) + sw / 2, y: py(oy) + sw / 2,
        width: Math.max(0, px(ow) - sw), height: Math.max(0, py(oh) - sw) },
        ui.shapes);
    });
  }

  function drawHandles() {
    ui.handles.innerHTML = "";
    handles.forEach((h) => {
      const [x, y] = h.get();
      const attrs = { class: "pe-h" + (sel === h ? " sel" : ""),
        cx: px(x), cy: py(y), r: sel === h ? 7 : 5 };
      // inline style (not the fill attr) so it beats the .pe-h CSS rule;
      // when selected we leave it off so .pe-h.sel's magenta wins
      if (sel !== h) attrs.style = "fill:" + colourFor(h.id);
      const c = mk("circle", attrs, ui.handles);
      c.addEventListener("pointerdown", (e) => beginDrag(e, h, "move"));
      if (h.getSize) {
        const [w, hh] = h.getSize();
        const cornerX = h.kind === "rect" ? x + w : x + w / 2;
        const cornerY = h.kind === "rect" ? y + hh : y + hh / 2;
        const sq = mk("rect", { class: "pe-h size" + (sel === h ? " sel" : ""),
          x: px(cornerX) - 4, y: py(cornerY) - 4, width: 8, height: 8 }, ui.handles);
        sq.addEventListener("pointerdown", (e) => beginDrag(e, h, "size"));
      }
    });
  }

  // ------------------------------------------------------------- dragging
  function beginDrag(e, h, mode) {
    e.stopPropagation();
    e.preventDefault();
    select(h);
    const move = (ev) => {
      const f = frac(ev);
      if (mode === "move") h.set(f.x, f.y);
      else {
        const [cx, cy] = h.get();
        if (h.kind === "rect") h.setSize(f.x - cx, f.y - cy);
        else h.setSize((f.x - cx) * 2, (f.y - cy) * 2);
      }
      queueRebuild();
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      flushRebuild();
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  function queueRebuild() {
    if (rebuildQueued) return;
    rebuildQueued = true;
    requestAnimationFrame(flushRebuild);
  }
  function flushRebuild() {
    rebuildQueued = false;
    try { S.rebuild(); } catch (err) { msg("rebuild: " + err.message); }
    // app.js may have made a fresh PKTR_EDIT; keep our layout reference (it is
    // the same object) but refresh VB and the overlay node.
    S = window.PKTR_EDIT;
    VB = S.VB || VB;
    drawSpritePreviews();
    drawShapes();
    drawHandles();
    updateJSON();
    updateSelLabel();
  }

  // ------------------------------------------------------- selection + keys
  function select(h) {
    // freeze the train in place while it's the selection, otherwise rotate/
    // skew/offset are judged against a target that's moved again by the
    // time the next tick redraws it - see app.js's TRAIN_LIVE.frozen check.
    // Anything else selected (including nothing) lets it resume moving.
    if (S.trainLive) S.trainLive.frozen = !!(h && h.id === "train");
    sel = h;
    drawHandles();
    updateSelLabel();
  }
  function cycleSel(dir) {
    if (!handles.length) return;
    let i = sel ? handles.indexOf(sel) : -1;
    i = (i + dir + handles.length) % handles.length;
    select(handles[i]);
  }
  function updateSelLabel() {
    if (!sel) { ui.sel.textContent = "nothing selected"; ui.tilt.hidden = true; return; }
    const [x, y] = sel.get();
    let t = `${sel.id}  x ${x}  y ${y}`;
    if (sel.getSize) { const [w, h] = sel.getSize(); t += `  w ${w}  h ${h}`; }
    if (sel.id === "train") t += "  [frozen - moves again once deselected]";
    ui.sel.textContent = t;
    if (sel.building) {
      const spr = sel.building.sprite;
      ui.tilt.hidden = false;
      if (document.activeElement !== ui.rot) ui.rot.value = spr.rotate || 0;
      if (document.activeElement !== ui.skx) ui.skx.value = spr.skewX || 0;
      if (document.activeElement !== ui.sky) ui.sky.value = spr.skewY || 0;
    } else {
      ui.tilt.hidden = true;
    }
  }

  function onKey(e) {
    if (/^(TEXTAREA|INPUT)$/.test(e.target.tagName)) return;
    if (e.key === "g") { cycleGrid(); return; }
    if (e.key === "Escape") { select(null); return; }
    if (e.key === "[") { cycleSel(-1); e.preventDefault(); return; }
    if (e.key === "]") { cycleSel(1); e.preventDefault(); return; }
    if (!sel) return;
    if ((e.key === "Delete" || e.key === "Backspace") && sel.kind === "vertex") {
      if (sel.arr.length > 2) { sel.arr.splice(sel.idx(), 1); select(null); renderAll(); flushRebuild(); }
      e.preventDefault();
      return;
    }
    const d = e.shiftKey ? 0.01 : 0.001;
    let dx = 0, dy = 0;
    if (e.key === "ArrowLeft") dx = -d;
    else if (e.key === "ArrowRight") dx = d;
    else if (e.key === "ArrowUp") dy = -d;
    else if (e.key === "ArrowDown") dy = d;
    else return;
    e.preventDefault();
    if (e.metaKey || e.ctrlKey) {
      if (!sel.getSize) return;
      const [w, h] = sel.getSize();
      sel.setSize(w + dx * 2, h + dy * 2);
    } else {
      const [x, y] = sel.get();
      sel.set(x + dx, y + dy);
    }
    flushRebuild();
  }

  function insertVertex(f) {
    if (!sel || sel.kind !== "vertex") return;
    sel.arr.splice(sel.idx() + 1, 0, [r4(f.x), r4(f.y)]);
    renderAll();
    flushRebuild();
    select(handles.find((h) => h.key === sel.key && Math.abs(h.get()[0] - f.x) < 1e-6));
  }

  function cycleGrid() {
    grid = grid === 0 ? 20 : grid === 20 ? 40 : 0;   // off -> 5% -> 2.5% -> off
    document.querySelector("#pe-grid").textContent =
      "grid: " + (grid === 0 ? "off" : (100 / grid) + "%");
    drawGrid();
  }

  // ----------------------------------------------------------------- JSON
  function updateJSON() {
    if (document.activeElement === ui.json) return;
    ui.json.value = JSON.stringify(L, null, 2);
  }
  function msg(t) {
    ui.msg.textContent = t;
    clearTimeout(msg._t);
    msg._t = setTimeout(() => (ui.msg.textContent = ""), 4000);
  }
  function copyJSON() {
    navigator.clipboard.writeText(ui.json.value)
      .then(() => msg("copied — paste into simmap/web/overlay.json"))
      .catch(() => msg("clipboard blocked; use download"));
  }
  function downloadJSON() {
    const blob = new Blob([ui.json.value], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "overlay.json";
    a.click();
    URL.revokeObjectURL(a.href);
    msg("downloaded overlay.json");
  }
  function applyJSON() {
    let parsed;
    try { parsed = JSON.parse(ui.json.value); }
    catch (err) { msg("parse error: " + err.message); return; }
    Object.keys(L).forEach((k) => delete L[k]);
    Object.assign(L, parsed);
    sel = null;
    renderAll();
    flushRebuild();
    msg("applied");
  }
  function revert() {
    Object.keys(L).forEach((k) => delete L[k]);
    Object.assign(L, JSON.parse(initialJSON));
    sel = null;
    renderAll();
    flushRebuild();
    msg("reverted to loaded overlay.json");
  }
})();
