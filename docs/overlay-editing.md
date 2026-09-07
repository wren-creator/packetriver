# Aligning the map overlay

`simmap/web/overlay.json` holds a coordinate for every dynamic thing on the
map — building hotspots and their boxes, traffic heads, houses, streetlights,
the rail path, the river, the swimmers, the two utility flows. Every value is a
**fraction, 0..1**, of the base image's width or height. `app.js` just
multiplies by the `viewBox` (`[1000, 545]`), which shares `basemap.png`'s
aspect ratio, so the SVG sits 1:1 on the art with no letterboxing. If the art
ever changes shape, update `viewBox` to match or the whole overlay shifts.

Shapes:

| key | shape | meaning |
|---|---|---|
| `buildings[id]` | `{x, y, w, h}` | `x,y` = **centre**, `w,h` = box size |
| `river` | `{x, y, w, h}` | `x,y` = **top-left**, `w,h` = size |
| `intersections`, `houses`, `streetlights` | `[{x, y}]` | points |
| `railPath`, `outfall`, `waterMain`, `powerFeeder`, `swimmers` | `[[x, y], ...]` | vertex lists |
| `spurBranch`, `spurEnd` | `[x, y]` | single points |

## The editor (`?edit=1`)

Open the map with `?edit=1`:

```
http://127.0.0.1:8080/?edit=1
```

`edit.js` loads for everyone but is inert without that flag, so players never
see it. With it on you get a draggable handle on every coordinate, a
calibration grid, a live cursor readout, and a JSON panel.

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
