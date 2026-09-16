# Aligning the map overlay

`simmap/web/overlay.json` holds a coordinate for every dynamic thing on the
map — building hotspots and their boxes, traffic heads, houses, streetlights,
the rail path, the river, the swimmers, the two utility flows. Every value is a
**fraction, 0..1**, of the base image's width or height. `app.js` just
multiplies by the `viewBox` (today `[1800, 1522]`, matching `basemap.png`'s
real pixel size), so the SVG sits 1:1 on the art with no letterboxing. If the
art ever changes shape, update `viewBox` (and `index.html`'s `<svg>`,
`style.css`'s `.viewport`/`.world`, and `camera.js`'s fallback `worldW`/
`worldH`) to match, or the whole overlay shifts - `simmap/tools/
migrate_canvas_v2.py` is the script that did this the one time the canvas
was padded; a future resize would want a similar one-off, not a hand edit
of every coordinate.

Shapes:

| key | shape | meaning |
|---|---|---|
| `buildings[id]` | `{x, y, w, h}` | `x,y` = **centre**, `w,h` = box size |
| `river` | `{x, y, w, h}` | `x,y` = **top-left**, `w,h` = size |
| `intersections`, `houses`, `streetlights` | `[{x, y}]` | points |
| `railPath`, `outfall`, `waterMain`, `powerFeeder`, `swimmers` | `[[x, y], ...]` | vertex lists |
| `spurBranch`, `spurEnd` | `[x, y]` | single points |

## Building art: the `sprite` field

A `buildings[id]` entry can carry an optional `sprite` object so its art is
its own image instead of being painted into `basemap.png`:

```json
"sprite": { "src": "sprites/power.png", "w": 812, "h": 664,
            "anchorX": 0.5, "anchorY": 1.0, "scale": 1.0 }
```

- `src` - path to the PNG. Core buildings: relative to `simmap/web/` (e.g.
  `sprites/power.png`). Pack buildings: relative to the pack's own
  `sprites/` dir (e.g. `"grain_bin.png"`) - `simmap/server.py`'s
  `_merged_overlay()` rewrites it to `/packs/<pack>/sprites/<file>` before
  the client ever sees it.
- `w` / `h` - the PNG's **native pixel dimensions**, recorded once. Render
  width locks to the building's `w` (its existing footprint, already sizing
  the hotspot), render height derives from `w`/`h`'s aspect ratio - no
  per-building pixel math.
- `anchorX` / `anchorY` (default `0.5` / `1.0`) - which point on the sprite
  sits on the building's ground point (`x`, bottom edge of the footprint
  box). Only override for art with baked-in shadow/padding.
- `scale` (default `1`) - a multiplier on the footprint width, for art that
  should read larger or smaller than its hotspot.

No `sprite` field ⇒ the building renders exactly as it always has (art
expected in `basemap.png`, hotspot + ring only). This is what lets the
20 existing buildings migrate a few at a time instead of all at once - see
`app.js`'s `drawBuildingSprite()`. When a building has a `sprite`, the
`?edit=1` editor shows a faint preview of it under the drag handles.

## The editor (`?edit=1`)

Open the map with `?edit=1`:

```
http://127.0.0.1:8080/?edit=1
```

`edit.js` loads for everyone but is inert without that flag, so players never
see it. With it on you get a draggable handle on every coordinate, a
calibration grid, a live cursor readout, and a JSON panel. Drag the map or
scroll to zoom (same camera as the live game) to reach an area that's off
screen before placing a handle there.

- **Drag** a cyan handle to move it. The real overlay redraws live as you drag.
- Buildings and the river get a **yellow square** at the bottom-right for size.
- **Arrow keys** nudge the selection by `0.001` (Shift = `0.01`).
  Cmd/Ctrl + arrows resize the selection.
- **`[`** / **`]`** cycle the selection; **`Esc`** deselects.
- **`g`** cycles the grid (off → 5% → 2.5%).
- On a polyline vertex: **Alt+click** the map to insert a vertex after it,
  **Delete** to remove it.
- **copy JSON** / **download** hand you the finished `overlay.json`. Paste it
  over `simmap/web/overlay.json` and rebuild `simmap`.
- **apply edits ↑** parses the textarea back in (hand-tweak, then apply).
  **revert** restores the version the page loaded with.
- Click the panel header to collapse it out of the way.

The coordinates round to four decimals on every edit, which is well under a
pixel at the art's size and keeps the JSON diff clean.
