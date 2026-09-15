#!/usr/bin/env python3
"""Project caller-supplied world points; no rig extraction, fitting or occlusion."""
import argparse
import html
import json
import math
from pathlib import Path
import sys


def require(condition, message):
    if not condition: raise ValueError(message)


def numbers(value, n):
    require(isinstance(value, list) and len(value) == n and all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in value), f"Expected {n} finite numbers")
    return value


def project(data):
    require(data.get("matrix_convention") == "row_major_times_column_vector", "Declare row_major_times_column_vector")
    require(data.get("ndc_depth") in {"minus_one_to_one", "zero_to_one"}, "Declare ndc_depth")
    require(data.get("camera") and isinstance(data.get("frame"), int) and data["frame"] >= 0, "Actual camera and nonnegative frame are required")
    width, height = numbers(data.get("viewport"), 2)
    require(width > 0 and height > 0, "Viewport must be positive")
    matrix = data.get("world_to_clip")
    require(isinstance(matrix, list) and len(matrix) == 4, "Expected 4x4 world_to_clip matrix")
    for row in matrix: numbers(row, 4)
    require(isinstance(data.get("points"), list) and data["points"], "Supply actual world points")
    ids, output = set(), []
    for point in data["points"]:
        ident = point.get("id")
        require(isinstance(ident, str) and ident and ident not in ids, "Unique point IDs required")
        ids.add(ident)
        p = numbers(point.get("world"), 3) + [1.0]
        clip = [sum(row[j] * p[j] for j in range(4)) for row in matrix]
        require(all(math.isfinite(x) for x in clip), "Nonfinite projected coordinate")
        record = {"id": ident, "group": point.get("group", "unclassified"), "visible": point.get("visible", "unknown")}
        require(record["visible"] in {True, False, "unknown"}, "visible must be true/false/unknown, supplied by caller")
        if clip[3] <= 1e-9:
            record.update(clip_status="behind_or_at_camera", pixel=None, normalized=None)
        else:
            x, y, z = [v / clip[3] for v in clip[:3]]
            u, v = (x + 1) / 2, (1 - y) / 2
            near = -1 if data["ndc_depth"] == "minus_one_to_one" else 0
            record.update(clip_status="inside" if -1 <= x <= 1 and -1 <= y <= 1 and near <= z <= 1 else "outside", normalized=[u, v], pixel=[u * width, v * height])
        if "target_pixel" in point:
            record["target_pixel"] = numbers(point["target_pixel"], 2)
        output.append(record)
    edges = data.get("edges", [])
    require(isinstance(edges, list), "Edges must be a list")
    for edge in edges:
        require(isinstance(edge, list) and len(edge) == 2 and all(x in ids for x in edge), "Edges must reference two supplied point IDs")
    return {"camera": data["camera"], "frame": data["frame"], "viewport": [width, height], "points": output, "edges": edges,
            "notice": "Projection only. Visibility is caller-supplied, not computed. Unordered points are never connected automatically."}


def svg(result):
    w, h = result["viewport"]
    by_id = {p["id"]: p for p in result["points"]}
    esc = html.escape
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           '<rect width="100%" height="100%" fill="#f7f9fc"/>',
           '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="#bd314d"/></marker></defs>',
           f'<text x="12" y="22" font-family="sans-serif" font-size="14">{esc(str(result["camera"]))} / frame {result["frame"]} · projection only</text>']
    for a, b in result["edges"]:
        pa, pb = by_id[a], by_id[b]
        if all(p["clip_status"] == "inside" and p["visible"] is not False for p in (pa, pb)):
            x, y = pa["pixel"]; xx, yy = pb["pixel"]
            out.append(f'<line x1="{x}" y1="{y}" x2="{xx}" y2="{yy}" stroke="#7b8c9c" stroke-width="1"/>')
    for p in result["points"]:
        if p["clip_status"] != "inside": continue
        x, y = p["pixel"]
        color = "#16718c" if p["visible"] is True else "#9aa0a8"
        out.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{color}"><title>{esc(p["id"])} · {esc(str(p["group"]))} · visible={p["visible"]}</title></circle>')
        out.append(f'<text x="{x+5}" y="{y-5}" font-family="sans-serif" font-size="10">{esc(p["id"])}</text>')
        if "target_pixel" in p:
            tx, ty = p["target_pixel"]
            out.append(f'<line x1="{x}" y1="{y}" x2="{tx}" y2="{ty}" stroke="#bd314d" marker-end="url(#arrow)"/>')
            out.append(f'<circle cx="{tx}" cy="{ty}" r="4" fill="none" stroke="#bd314d"/>')
    out.append('</svg>')
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input"); p.add_argument("--out", required=True, help="New output directory")
    args = p.parse_args()
    try:
        result = project(json.loads(Path(args.input).read_text(encoding="utf-8-sig")))
        out = Path(args.out)
        require(not out.exists(), "Output directory must be new")
        out.mkdir(parents=True)
        (out / "projection.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        (out / "projection.svg").write_text(svg(result), encoding="utf-8")
        print(str(out / "projection.svg"))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as ex:
        print(str(ex), file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
