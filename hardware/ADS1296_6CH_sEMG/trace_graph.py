"""Read-only explicit-copper path metrics. Filled planes are excluded."""
from collections import Counter, defaultdict
import math, heapq
import pcbnew as p
EPS=0.00001

def xy(v):
    return (p.ToMM(v.x), p.ToMM(v.y))


def rounded(value):
    return round(value, 6) if value is not None else None


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def project(q, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    den = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((q[0]-a[0])*dx+(q[1]-a[1])*dy)/den)) if den else 0.0
    return t, (a[0] + t*dx, a[1] + t*dy)


def crossing(a, b, c, d):
    """Centreline intersection for nonparallel segments; endpoints handle overlap."""
    ax, ay, bx, by = b[0]-a[0], b[1]-a[1], d[0]-c[0], d[1]-c[1]
    den = ax*by-ay*bx
    if abs(den) < 1e-12:
        return None
    cx, cy = c[0]-a[0], c[1]-a[1]
    t, u = (cx*by-cy*bx)/den, (cx*ay-cy*ax)/den
    if -EPS <= t <= 1+EPS and -EPS <= u <= 1+EPS:
        return a[0]+t*ax, a[1]+t*ay
    return None


def copper_layers(board, item):
    return [layer for layer in board.GetEnabledLayers().Seq()
            if p.IsCopperLayer(layer) and item.GetLayerSet().Contains(layer)]


class TraceGraph:
    """Copper centreline graph, with pad bridges and split interior junctions."""
    def __init__(self, board, net, pads):
        self.board, self.net = board, net
        self.edges = defaultdict(list)
        self.pad_nodes = defaultdict(list)
        self.via_nodes = defaultdict(list)
        self.unsupported = []
        segments, vias = [], []
        for item in board.GetTracks():
            if item.GetNetname() != net:
                continue
            if isinstance(item, p.PCB_VIA):
                vias.append(item)
            elif isinstance(item, p.PCB_ARC):
                self.unsupported.append(item.m_Uuid.AsString())
            else:
                segments.append({"a": xy(item.GetStart()), "b": xy(item.GetEnd()),
                                 "layer": item.GetLayer(), "width": p.ToMM(item.GetWidth()),
                                 "id": item.m_Uuid.AsString(), "split": {0.0, 1.0}})

        def node(q, layer):
            return (round(q[0], 6), round(q[1], 6), layer)

        def add(a, b, length, kind, ident=""):
            if a == b:
                self.edges[a]
                return
            self.edges[a].append((b, length, kind, ident))
            self.edges[b].append((a, length, kind, ident))

        # Segment endpoints/intersections split same-layer copper paths. A node
        # inside another trace width receives a short explicit centreline bridge.
        pending = []
        for i, seg in enumerate(segments):
            for other in segments[:i]:
                if seg["layer"] != other["layer"]:
                    continue
                q = crossing(seg["a"], seg["b"], other["a"], other["b"])
                if q is not None:
                    seg["split"].add(project(q, seg["a"], seg["b"])[0])
                    other["split"].add(project(q, other["a"], other["b"])[0])
                for one, two in ((seg, other), (other, seg)):
                    for endpoint in (one["a"], one["b"]):
                        t, q = project(endpoint, two["a"], two["b"])
                        if dist(endpoint, q) <= (one["width"]+two["width"])/2 + EPS:
                            two["split"].add(t)
                            pending.append((node(endpoint, one["layer"]), node(q, two["layer"]),
                                            dist(endpoint, q), "copper_junction", ""))

        # Vias join only the copper layers which they actually span.
        for via in vias:
            q, ident = xy(via.GetPosition()), via.m_Uuid.AsString()
            nodes = [node(q, layer) for layer in copper_layers(board, via)]
            self.via_nodes[ident] = nodes
            for a, b in zip(nodes, nodes[1:]):
                add(a, b, 0.0, "via", ident)
            for seg in segments:
                if seg["layer"] not in [n[2] for n in nodes]:
                    continue
                t, z = project(q, seg["a"], seg["b"])
                if dist(q, z) <= (p.ToMM(via.GetWidth(seg["layer"]))+seg["width"])/2 + EPS:
                    seg["split"].add(t)
                    pending.append((node(q, seg["layer"]), node(z, seg["layer"]),
                                    dist(q, z), "via_land", ident))

        # Attach pad centres to all trace portions/vias entering the pad. This
        # permits endpoint-to-endpoint paths through the conductive pad itself.
        for pad in pads:
            q = xy(pad.GetPosition())
            key = (pad.GetParentFootprint().GetReference(), pad.GetNumber())
            layers = copper_layers(board, pad)
            padnodes = [node(q, layer) for layer in layers]
            self.pad_nodes[key].extend(padnodes)
            for a, b in zip(padnodes, padnodes[1:]):
                add(a, b, 0.0, "plated_pad", ".".join(key))
            for seg in segments:
                if seg["layer"] not in layers:
                    continue
                t, z = project(q, seg["a"], seg["b"])
                testpoint = p.VECTOR2I(p.FromMM(z[0]), p.FromMM(z[1]))
                if pad.HitTest(testpoint):
                    seg["split"].add(t)
                    pending.append((node(q, seg["layer"]), node(z, seg["layer"]),
                                    dist(q, z), "pad_land", ".".join(key)))
            for via in vias:
                z = xy(via.GetPosition())
                if pad.HitTest(via.GetPosition()):
                    for layer in set(layers) & set(copper_layers(board, via)):
                        pending.append((node(q, layer), node(z, layer), dist(q, z),
                                        "pad_land", ".".join(key)))

        for seg in segments:
            split = sorted(seg["split"])
            for ta, tb in zip(split, split[1:]):
                a = (seg["a"][0]+ta*(seg["b"][0]-seg["a"][0]),
                     seg["a"][1]+ta*(seg["b"][1]-seg["a"][1]))
                b = (seg["a"][0]+tb*(seg["b"][0]-seg["a"][0]),
                     seg["a"][1]+tb*(seg["b"][1]-seg["a"][1]))
                add(node(a, seg["layer"]), node(b, seg["layer"]), dist(a, b), "track", seg["id"])
        for args in pending:
            add(*args)

    def shortest(self, starts, goals):
        goals = set(goals)
        queue = [(0.0, node) for node in starts]
        heapq.heapify(queue)
        best = {node: 0.0 for node in starts}
        previous = {}
        end = None
        while queue:
            cost, here = heapq.heappop(queue)
            if cost > best[here] + EPS:
                continue
            if here in goals:
                end = here
                break
            for there, length, kind, ident in self.edges.get(here, []):
                newcost = cost+length
                if newcost + EPS < best.get(there, math.inf):
                    best[there] = newcost
                    previous[there] = (here, kind, ident, length)
                    heapq.heappush(queue, (newcost, there))
        if end is None:
            return {"found": False, "planar_centreline_mm": None,
                    "unsupported_arc_ids": self.unsupported}
        path, kinds, identifiers = [end], Counter(), defaultdict(set)
        cursor = end
        while cursor in previous:
            last, kind, ident, length = previous[cursor]
            kinds[kind] += 1
            identifiers[kind].add(ident)
            cursor = last
            path.append(cursor)
        return {"found": True, "planar_centreline_mm": rounded(best[end]),
                "via_count": len(identifiers["via"]),
                "via_ids": sorted(identifiers["via"]),
                "layers": sorted({self.board.GetLayerName(n[2]) for n in path}),
                "track_ids": sorted(identifiers["track"]),
                "node_count": len(path), "unsupported_arc_ids": self.unsupported}

    def pads_path(self, first, second):
        return self.shortest(self.pad_nodes[first], self.pad_nodes[second])



