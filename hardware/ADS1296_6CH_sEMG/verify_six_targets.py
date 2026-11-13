"""Independently measure the six requested placements in a saved KiCad PCB.

Run with KiCad's Python, for example:
  python.exe verify_six_targets.py --report SIX_TARGET_VERIFICATION.json

The PCB and project are read-only. Only an explicitly requested JSON report is
written. This checker uses hard-coded target pins/nets rather than the placement
script or its reported distances. It does not constitute electrical simulation.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import pcbnew as p
from trace_graph import TraceGraph, xy


BASE = Path(__file__).resolve().parent
DEFAULT_BOARD = BASE / "ADS1296_RevA4_TinySocket.kicad_pcb"
TOL_MM = 0.000002
# ref, U1 pin, component terminal, expected net, maximum planar centre distance
TARGETS = (
    ("C22", "48", "1", "3V3_D", 2.0),
    ("C10", "59", "1", "AVDD", 2.0),
    ("C14", "24", "1", "VREFP", 2.0),
    ("C20", "26", "1", "VCAP4", 2.0),
    ("C27", "54", "1", "AVDD", 2.0),
    ("R21", "61", "2", "RLDINV", 3.0),
)


def rounded(value):
    return round(value, 6)


def run(board_path: Path):
    board_path = board_path.resolve()
    source_bytes = board_path.read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    b = p.LoadBoard(str(board_path))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    pads = {
        (f.GetReference(), a.GetNumber()): a
        for f in fps.values() for a in f.Pads() if a.GetNumber()
    }
    vias = [v for v in b.GetTracks() if isinstance(v, p.PCB_VIA)]
    local_path = board_path.parent / "local_routes.json"
    local = json.loads(local_path.read_text()) if local_path.exists() else {}
    assigned_vias = local.get("ground_vias", {})
    failures, notes, rows, graphs = [], [], [], {}
    thickness_mm = p.ToMM(b.GetDesignSettings().GetBoardThickness())

    def check(ok, message):
        if not ok:
            failures.append(message)
        return bool(ok)

    def netcheck(key, expected):
        a = pads.get(key)
        if not check(a is not None, f"Missing pad {'.'.join(key)}"):
            return False
        return check(a.GetNetname() == expected,
                     f"{'.'.join(key)} expected {expected}, found {a.GetNetname()}")

    def graph(net):
        if net not in graphs:
            graphs[net] = TraceGraph(b, net,
                                    [a for a in pads.values() if a.GetNetname() == net])
        return graphs[net]

    def padroute(first, second, expected):
        valid = netcheck(first, expected) & netcheck(second, expected)
        if not valid:
            return {"found": False, "reason": "missing pad or net mismatch"}
        route = graph(expected).pads_path(first, second)
        check(route["found"], f"No explicit copper path {'.'.join(first)} to {'.'.join(second)}")
        check(not route.get("unsupported_arc_ids"),
              f"Unsupported copper arcs on {expected}; path audit is incomplete")
        return route

    # Inspect the actual edge coordinates; drawing stroke width is not a board
    # dimension. This revision is a rectangle, so reject other shapes rather
    # than silently understating the extent of a curved edge.
    edges = [e for e in b.GetDrawings() if e.GetLayer() == p.Edge_Cuts]
    check(len(edges) == 4 and all(e.GetShape() == p.SHAPE_T_SEGMENT for e in edges),
          "Expected four straight Edge.Cuts segments for the rectangular board")
    points = [xy(v) for e in edges for v in (e.GetStart(), e.GetEnd())]
    outline = None
    if check(bool(points), "No board outline found"):
        minxy = [min(q[i] for q in points) for i in (0, 1)]
        maxxy = [max(q[i] for q in points) for i in (0, 1)]
        outline = [rounded(maxxy[i] - minxy[i]) for i in (0, 1)]
        check(all(abs(a - z) <= TOL_MM for a, z in zip(outline, (100.0, 80.0))),
              f"Outline is {outline}, expected 100 x 80 mm")
        endpoint_count = defaultdict(int)
        for point in points:
            endpoint_count[tuple(round(v, 6) for v in point)] += 1
        check(len(endpoint_count) == 4 and set(endpoint_count.values()) == {2},
              "Edge.Cuts endpoints do not form a closed four-corner outline")
    check(abs(thickness_mm - 1.6) <= TOL_MM,
          f"Configured board thickness is {thickness_mm}, expected 1.6 mm")
    check(b.GetCopperLayerCount() == 4, "Expected four copper layers")

    for ref, pin, terminal, expected, maximum in TARGETS:
        fp, ap = fps.get(ref), pads.get(("U1", pin))
        if not check(fp is not None and ap is not None, f"Missing target {ref} or U1.{pin}"):
            continue
        centre, adc_centre = xy(fp.GetPosition()), xy(ap.GetPosition())
        planar = math.dist(centre, adc_centre)
        opposite_face = fp.GetLayer() != fps["U1"].GetLayer()
        dz = thickness_mm if opposite_face else 0.0
        passed = planar <= maximum + TOL_MM
        check(passed, f"{ref} to U1.{pin}: {planar:.6f} mm exceeds {maximum:.3f} mm")
        row = {
            "reference": ref, "ads1296_pin": pin,
            "component_signal_terminal": terminal, "expected_net": expected,
            "component_face": b.GetLayerName(fp.GetLayer()),
            "component_centre_xy_mm": list(map(rounded, centre)),
            "adc_pad_centre_xy_mm": list(map(rounded, adc_centre)),
            "component_centre_to_adc_pad_centre_planar_mm": rounded(planar),
            "maximum_planar_mm": maximum, "planar_limit_passed": passed,
            "assumed_surface_height_difference_mm": rounded(dz),
            "estimated_surface_to_surface_straight_line_mm": rounded(math.hypot(planar, dz)),
            "signal_path": padroute(("U1", pin), (ref, terminal), expected),
        }
        rows.append(row)
        if opposite_face:
            notes.append(f"{ref} is on B.Cu: the requested limit is a 2D placement limit. "
                         "Its 3D surface separation and via traversal are reported separately.")

    # Report BOTH feedback terminals; close placement of R21.2 cannot by itself
    # establish that the other half of the RLD feedback loop is connected.
    feedback = []
    for ref in ("R21", "C23"):
        for terminal, pin, net in (("1", "63", "RLDOUT"), ("2", "61", "RLDINV")):
            feedback.append({"reference": ref, "terminal": terminal, "adc_pin": pin,
                             "net": net,
                             "path": padroute(("U1", pin), (ref, terminal), net)})

    # Restrict local ground returns to the component face. A path is not allowed
    # to disappear into a plane, pass through another component's pad, or take
    # another via before reaching the capacitor's own assigned ground via.
    g = graph("GND")
    ground_usage, ground_track_usage = defaultdict(list), defaultdict(list)
    for row in rows:
        ref = row["reference"]
        if not ref.startswith("C"):
            continue
        if not netcheck((ref, "2"), "GND"):
            continue
        cap_pad = pads[ref, "2"]
        # PAD.GetLayer() can retain F.Cu for a flipped SMD pad while its actual
        # layer set is B.Cu/B.Mask/B.Paste. Use the physical footprint face and
        # independently check the pad's layer set.
        layer = fps[ref].GetLayer()
        check(cap_pad.IsOnLayer(layer), f"{ref}.2 does not occupy its footprint's copper face")
        direct_graph = copy(g)
        direct_graph.edges = defaultdict(list)
        for node, neighbours in g.edges.items():
            if node[2] != layer:
                continue
            for edge in neighbours:
                other, length, kind, ident = edge
                if other[2] != layer or kind in ("via", "plated_pad"):
                    continue
                if kind == "pad_land" and ident != f"{ref}.2":
                    continue
                direct_graph.edges[node].append(edge)
        declared = assigned_vias.get(ref)
        candidates = [v for v in vias
                      if v.GetNetname() == "GND" and v.IsOnLayer(layer)
                      and v.IsOnLayer(p.In1_Cu)]
        if declared is not None:
            candidates = [v for v in candidates
                          if math.dist(xy(v.GetPosition()), declared) <= 0.002]
            check(len(candidates) == 1,
                  f"{ref}: expected one assigned ground via at {declared}, found {len(candidates)}")
        else:
            notes.append(f"{ref}: no assignment in local_routes.json; "
                         "the closest explicitly connected ground via was inferred.")
        options = []
        for via in candidates:
            ident = via.m_Uuid.AsString()
            route = direct_graph.shortest(
                [n for n in g.pad_nodes[ref, "2"] if n[2] == layer],
                [n for n in g.via_nodes[ident] if n[2] == layer])
            if route["found"]:
                options.append((route["planar_centreline_mm"], ident, via, route))
        if not check(bool(options), f"{ref}: no direct same-face explicit return to a local GND via"):
            row["ground_return"] = {"found": False, "assignment_xy_mm": declared}
            continue
        _, ident, via, route = min(options, key=lambda option: option[0])
        q = xy(via.GetPosition())
        ground_usage[ident].append(ref)
        for track in route.get("track_ids", []):
            ground_track_usage[track].append(ref)
        other_assignments = [other for other, coord in assigned_vias.items()
                             if other != ref and math.dist(coord, q) <= 0.002]
        check(not other_assignments,
              f"{ref}: assigned ground via is also assigned to {other_assignments}")
        row["ground_return"] = {
            "found": True, "assignment_source": "local_routes.json" if declared is not None else "inferred",
            "via_uuid": ident, "via_xy_mm": list(map(rounded, q)),
            "ground_pad_centre_to_via_centre_planar_mm": rounded(math.dist(xy(cap_pad.GetPosition()), q)),
            "via_spans_In1_Cu": via.IsOnLayer(p.In1_Cu),
            "other_declared_users_of_same_via": other_assignments,
            "direct_explicit_same_face_path": route,
        }
    for ident, refs in ground_usage.items():
        check(len(refs) == 1, f"Ground via {ident} is shared by target capacitors {refs}")
    for ident, refs in ground_track_usage.items():
        check(len(set(refs)) == 1, f"Local ground trace {ident} is shared by target capacitors {refs}")

    # Reference return is a separate path to pin25, which is VREFN in this
    # design and joins GND. Do not confuse it with the VREFP connection to pin24.
    reference_return = padroute(("C14", "2"), ("U1", "25"), "GND")
    final_sha = hashlib.sha256(board_path.read_bytes()).hexdigest()
    check(source_sha == final_sha,
          "PCB changed on disk while the checker ran; rerun on the final saved board")
    measured_all = len(rows) == len(TARGETS)
    check(measured_all, "Not all six targets were measured")
    return {
        "passed": not failures,
        "six_planar_limits_passed": measured_all and all(r["planar_limit_passed"] for r in rows),
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_path": str(board_path), "board_sha256": source_sha,
        "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "trace_graph_sha256": hashlib.sha256((BASE / "trace_graph.py").read_bytes()).hexdigest(),
        "outline_mm": outline, "board_thickness_mm": rounded(thickness_mm),
        "target_measurements": rows, "feedback_terminals": feedback,
        "C14_to_VREFN_pin25_explicit_return": reference_return,
        "failures": failures, "notes": notes,
        "measurement_definition": {
            "placement": "Euclidean XY distance from saved footprint origin/centre to saved U1 pad centre; independently recomputed.",
            "three_dimensional_estimate": "Straight-line surface-to-surface separation uses the configured 1.6 mm board thickness for opposite faces; ignores component and lead heights. Not routed copper length.",
            "explicit_path": "Shortest explicit copper centreline path, including travel across pads. Excludes copper pours and vertical via-barrel length; via_count counts series layer changes by distinct via UUID.",
            "local_ground": "Same-face explicit pad-to-via path, with no other component pad bridges or intervening vias; target capacitors must use distinct local vias and local return tracks. Via must span In1.Cu. Plane-fill connection itself requires native DRC.",
            "scope_limit": "Geometric/connectivity audit only. Does not prove analogue noise, RLD phase margin, capacitor effective capacitance, assembly success, isolation, or human-use safety.",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--report", type=Path,
                        help="Optional JSON report path; PCB/project remain read-only")
    args = parser.parse_args()
    report = run(args.board)
    encoded = json.dumps(report, indent=2)
    if args.report:
        args.report.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
