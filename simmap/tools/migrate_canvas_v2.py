"""One-off migration: reproject every coordinate in overlay.json from the
old 1600x872 basemap.png onto the new 1800x1522 canvas (padded +100 left,
+100 right, +400 north, +250 south - see the sprite-layer plan's canvas
step). Already run once; kept for the record of exactly how the numbers
were derived, not meant to run again unless the canvas is resized a second
time with the same LEFT/RIGHT/TOP/BOTTOM below updated to match.

    python3 simmap/tools/migrate_canvas_v2.py
"""
from __future__ import annotations

import json
import pathlib

OVERLAY = pathlib.Path(__file__).parent.parent / "web" / "overlay.json"

OLD_W, OLD_H = 1600, 872
LEFT, RIGHT, TOP, BOTTOM = 100, 100, 400, 250
NEW_W, NEW_H = OLD_W + LEFT + RIGHT, OLD_H + TOP + BOTTOM

r4 = lambda n: round(n, 4)


def shift_x(fx: float) -> float:
    return r4((fx * OLD_W + LEFT) / NEW_W)


def shift_y(fy: float) -> float:
    return r4((fy * OLD_H + TOP) / NEW_H)


def scale_w(fw: float) -> float:
    return r4(fw * OLD_W / NEW_W)


def scale_h(fh: float) -> float:
    return r4(fh * OLD_H / NEW_H)


def migrate_point(p: dict) -> None:
    p["x"] = shift_x(p["x"])
    p["y"] = shift_y(p["y"])


def migrate_vertex_list(arr: list) -> None:
    for v in arr:
        v[0] = shift_x(v[0])
        v[1] = shift_y(v[1])


def main() -> None:
    data = json.loads(OVERLAY.read_text())

    data["viewBox"] = [NEW_W, NEW_H]

    for b in data.get("buildings", {}).values():
        b["x"], b["y"] = shift_x(b["x"]), shift_y(b["y"])
        b["w"], b["h"] = scale_w(b["w"]), scale_h(b["h"])

    for it in data.get("intersections", []):
        migrate_point(it)
    for key in ("streetlights", "powerResidential", "powerBusiness",
                "powerPlant", "waterResidential"):
        for p in data.get(key, []):
            migrate_point(p)

    for key in ("railPath", "spurPath", "outfall", "waterMain",
                "powerFeeder", "powerFeederBiz", "powerFeederPlant",
                "swimmers"):
        if key in data:
            migrate_vertex_list(data[key])

    for key in ("river", "beachZone"):
        rv = data.get(key)
        if rv:
            rv["x"], rv["y"] = shift_x(rv["x"]), shift_y(rv["y"])
            rv["w"], rv["h"] = scale_w(rv["w"]), scale_h(rv["h"])

    OVERLAY.write_text(json.dumps(data, indent=2) + "\n")
    print(f"migrated {OLD_W}x{OLD_H} -> {NEW_W}x{NEW_H} "
          f"(pad L{LEFT} R{RIGHT} T{TOP} B{BOTTOM})")


if __name__ == "__main__":
    main()
