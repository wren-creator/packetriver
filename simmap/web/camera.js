"use strict";
/* Pan/zoom camera around the map's #world layer.
 *
 * Minimum zoom is "whole town fits the viewport" (recomputed on resize);
 * maximum is a fixed readability ceiling. World pixel size comes from the
 * basemap image's natural dimensions, so this keeps working once the canvas
 * grows (see the sprite-layer plan's canvas-resize step) without a code
 * change here - only the matching CSS aspect-ratio on .viewport (style.css)
 * needs updating alongside overlay.json's viewBox at that point.
 *
 * Drag-to-pan swallows the synthetic click that would otherwise fire on
 * pointerup after a real drag (mousedown+drag+mouseup can still target an
 * element and fire "click" even though the user meant to pan, not click a
 * building) - see the pointerup handler below.
 */
(function () {
  const MAX_ZOOM = 4;
  const DRAG_THRESHOLD = 6;

  const viewport = document.getElementById("viewport");
  const world = document.getElementById("world");
  if (!viewport || !world) return;
  const img = world.querySelector(".basemap");

  let worldW = 1408, worldH = 736;
  let zoom = 1, panX = 0, panY = 0, minZoom = 1;

  function setWorldSize(w, h) {
    if (!w || !h) return;
    worldW = w; worldH = h;
    world.style.width = w + "px";
    world.style.height = h + "px";
    fit();
  }

  function fitScale() {
    return Math.min(viewport.clientWidth / worldW, viewport.clientHeight / worldH) || 1;
  }

  function clampZoom(z) { return Math.max(minZoom, Math.min(z, MAX_ZOOM)); }

  function clampPan(x, y, z) {
    const vw = viewport.clientWidth, vh = viewport.clientHeight;
    const ww = worldW * z, wh = worldH * z;
    const minX = Math.min(0, vw - ww), minY = Math.min(0, vh - wh);
    return [Math.max(minX, Math.min(0, x)), Math.max(minY, Math.min(0, y))];
  }

  function apply() {
    world.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
  }

  function fit() {
    minZoom = fitScale();
    zoom = minZoom;
    panX = (viewport.clientWidth - worldW * zoom) / 2;
    panY = (viewport.clientHeight - worldH * zoom) / 2;
    [panX, panY] = clampPan(panX, panY, zoom);
    apply();
  }

  function zoomTo(newZoom, cx, cy) {
    newZoom = clampZoom(newZoom);
    // keep the world point under (cx, cy) fixed on screen while zooming
    const wx = (cx - panX) / zoom, wy = (cy - panY) / zoom;
    panX = cx - wx * newZoom;
    panY = cy - wy * newZoom;
    zoom = newZoom;
    [panX, panY] = clampPan(panX, panY, zoom);
    apply();
  }

  // ------------------------------------------------------------- pan/drag
  let dragging = false, moved = false, dragStart = null;

  viewport.addEventListener("pointerdown", (e) => {
    if (e.button !== undefined && e.button !== 0) return;
    dragging = true; moved = false;
    dragStart = { x: e.clientX, y: e.clientY, panX, panY };
  });
  window.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const dx = e.clientX - dragStart.x, dy = e.clientY - dragStart.y;
    if (!moved) {
      if (Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
      moved = true;
      viewport.classList.add("panning");
    }
    [panX, panY] = clampPan(dragStart.panX + dx, dragStart.panY + dy, zoom);
    apply();
  });
  window.addEventListener("pointerup", () => {
    if (dragging && moved) {
      const swallow = (ev) => { ev.stopPropagation(); ev.preventDefault(); };
      window.addEventListener("click", swallow, { capture: true, once: true });
    }
    dragging = false;
    viewport.classList.remove("panning");
  });

  // -------------------------------------------------------------- wheel
  viewport.addEventListener("wheel", (e) => {
    e.preventDefault();
    const rect = viewport.getBoundingClientRect();
    const factor = Math.exp(-e.deltaY * 0.001);
    zoomTo(zoom * factor, e.clientX - rect.left, e.clientY - rect.top);
  }, { passive: false });

  // -------------------------------------------------------------- buttons
  const center = () => [viewport.clientWidth / 2, viewport.clientHeight / 2];
  const btn = (id, fn) => { const b = document.getElementById(id); if (b) b.addEventListener("click", fn); };
  btn("cam-in", () => { const [cx, cy] = center(); zoomTo(zoom * 1.4, cx, cy); });
  btn("cam-out", () => { const [cx, cy] = center(); zoomTo(zoom / 1.4, cx, cy); });
  btn("cam-fit", fit);

  window.addEventListener("resize", fit);

  if (img) {
    if (img.complete && img.naturalWidth) setWorldSize(img.naturalWidth, img.naturalHeight);
    else img.addEventListener("load", () => setWorldSize(img.naturalWidth, img.naturalHeight), { once: true });
  } else {
    fit();
  }

  window.PKTR_CAMERA = { fit, zoomTo, get zoom() { return zoom; } };
})();
