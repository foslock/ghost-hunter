"""Find and fix coplanar, overlapping faces with different materials (z-fighting).

`fix()` runs on every map build: in each group of overlapping coplanar faces the one that should
show (thinnest, then smallest) stays put and the others sink a few millimetres into their solids. `report()` (map flag `--zcheck`)
lists whatever remains in blender/build/zfight_<map>.txt.

Faces facing the same way always fight. Back-to-back faces only fight when one of the materials
is double-sided (closed geometry renders single-sided; see MapBuilder._set_sidedness).
"""
import math
import os
from collections import defaultdict

import bpy
import numpy as np

PLANE_EPS = 0.0015      # faces closer than this along their normal count as coplanar
EDGE_EPS = 0.002        # shrink triangles before testing overlap so touching edges don't count
LIFT = 0.003            # how far the smaller face is lifted


def _triangles():
    """World-space triangles with owner info."""
    V, M, OB, PI, DS = [], [], [], [], []
    bpy.context.view_layer.update()  # parented objects' world matrices are stale until this runs
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.data.polygons]
    for oi, o in enumerate(objs):
        me = o.data
        me.calc_loop_triangles()
        nv = len(me.vertices)
        co = np.empty(nv * 3, dtype=np.float64)
        me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        mw = np.array(o.matrix_world)
        co = co @ mw[:3, :3].T + mw[:3, 3]
        nt = len(me.loop_triangles)
        tri = np.empty(nt * 3, dtype=np.int64)
        me.loop_triangles.foreach_get('vertices', tri)
        mi = np.empty(nt, dtype=np.int64)
        me.loop_triangles.foreach_get('material_index', mi)
        pi = np.empty(nt, dtype=np.int64)
        me.loop_triangles.foreach_get('polygon_index', pi)
        mats = list(me.materials) or [None]
        names = [m.name if m else '-' for m in mats]
        dbl = [bool(m and not m.use_backface_culling) for m in mats]
        mi = np.minimum(mi, len(names) - 1)
        V.append(co[tri.reshape(-1, 3)])
        M += [names[i] for i in mi]
        DS += [dbl[i] for i in mi]
        OB.append(np.full(nt, oi))
        PI.append(pi)
    if not V:
        return objs, np.zeros((0, 3, 3)), [], np.zeros(0, int), np.zeros(0, int), []
    return objs, np.concatenate(V), M, np.concatenate(OB), np.concatenate(PI), DS


def _shrink(t):
    c = t.mean(axis=0)
    d = t - c
    ln = np.linalg.norm(d, axis=1, keepdims=True)
    ln[ln < 1e-9] = 1e-9
    return c + d * np.maximum(0.0, 1 - EDGE_EPS / ln)


def _overlap2d(a, b):
    """Separating-axis test for two 2D triangles (3x2 arrays), shrunk by EDGE_EPS."""
    a, b = _shrink(a), _shrink(b)
    for t in (a, b):
        for i in range(3):
            e = t[(i + 1) % 3] - t[i]
            ax = np.array([-e[1], e[0]])
            pa, pb = a @ ax, b @ ax
            if pa.max() <= pb.min() + 1e-9 or pb.max() <= pa.min() + 1e-9:
                return False
    return True


def find():
    """Returns (objs, pairs). Each pair: dict(a=(obj, poly, area), b=..., facing, mats, center, normal)."""
    objs, V, M, OB, PI, DS = _triangles()
    if not len(V):
        return objs, []
    n = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0])
    area2 = np.linalg.norm(n, axis=1)
    keep = np.nonzero(area2 > 2e-6)[0]
    V, n, area2 = V[keep], n[keep], area2[keep]
    M = [M[k] for k in keep]
    DS = [DS[k] for k in keep]
    OB, PI = OB[keep], PI[keep]
    n = n / area2[:, None]
    base = [m[:-3] if m.endswith('_2s') else m for m in M]
    # polygon areas (sum of their triangles)
    poly_key = OB.astype(np.int64) * 10_000_000 + PI
    uk, inv = np.unique(poly_key, return_inverse=True)
    parea = np.zeros(len(uk))
    np.add.at(parea, inv.ravel(), area2 / 2)
    tri_parea = parea[inv.ravel()]
    # canonical orientation so back-to-back faces share a plane key
    flip = (n[:, 0] < -1e-6) | ((np.abs(n[:, 0]) <= 1e-6) & (n[:, 1] < -1e-6)) | \
           ((np.abs(n[:, 0]) <= 1e-6) & (np.abs(n[:, 1]) <= 1e-6) & (n[:, 2] < 0))
    cn = np.where(flip[:, None], -n, n)
    d = np.einsum('ij,ij->i', cn, V[:, 0])
    nq = np.round(cn * 200).astype(np.int64)
    order = np.lexsort((d, nq[:, 2], nq[:, 1], nq[:, 0]))
    pairs = []
    N = len(order)
    i = 0
    while i < N:
        j = i + 1
        a = order[i]
        while j < N and (nq[order[j]] == nq[a]).all() and d[order[j]] - d[order[j - 1]] < PLANE_EPS:
            j += 1
        idx = order[i:j]
        i = j
        if len(idx) < 2 or len(set(base[k] for k in idx)) < 2:
            continue
        nn = cn[idx[0]]
        u = np.cross(nn, [0, 0, 1] if abs(nn[2]) < 0.9 else [1, 0, 0])
        u /= np.linalg.norm(u)
        w = np.cross(nn, u)
        P = np.stack([V[idx] @ u, V[idx] @ w], axis=-1)
        lo, hi = P.min(axis=1), P.max(axis=1)
        cell = 0.5
        grid = defaultdict(list)
        for k in range(len(idx)):
            for gx in range(int(math.floor(lo[k, 0] / cell)), int(math.floor(hi[k, 0] / cell)) + 1):
                for gy in range(int(math.floor(lo[k, 1] / cell)), int(math.floor(hi[k, 1] / cell)) + 1):
                    grid[(gx, gy)].append(k)
        seen = set()
        for bucket in grid.values():
            for x in range(len(bucket)):
                ka = bucket[x]
                ta = idx[ka]
                for y in range(x + 1, len(bucket)):
                    kb = bucket[y]
                    tb = idx[kb]
                    if base[ta] == base[tb]:
                        continue  # same look (a material and its double-sided copy) can't flicker
                    same = flip[ta] == flip[tb]
                    if not same and not DS[ta] and not DS[tb]:
                        continue
                    pair = (min(ka, kb), max(ka, kb))
                    if pair in seen:
                        continue
                    seen.add(pair)
                    if (lo[ka] > hi[kb]).any() or (lo[kb] > hi[ka]).any():
                        continue
                    # undersides on the ground and tops above any eye height are never seen
                    if (n[ta][2] < -0.9 and V[ta][:, 2].max() < 0.1) or (n[ta][2] > 0.9 and V[ta][:, 2].min() > 7.5):
                        continue
                    if _overlap2d(P[ka], P[kb]):
                        pairs.append(dict(
                            a=(int(OB[ta]), int(PI[ta]), float(tri_parea[ta]), n[ta]),
                            b=(int(OB[tb]), int(PI[tb]), float(tri_parea[tb]), n[tb]),
                            mat_a=base[ta], mat_b=base[tb],
                            facing='same' if same else 'back', mats=tuple(sorted((M[ta], M[tb]))),
                            center=(V[ta].mean(axis=0) + V[tb].mean(axis=0)) / 2))
    return objs, pairs


class _Shells:
    """Per-mesh connected shells (raw vertex connectivity, so each primitive is its own shell), used
    to measure how thick the piece of geometry behind a face is."""

    def __init__(self):
        self.cache = {}

    def _mesh(self, me):
        hit = self.cache.get(me.name)
        if hit is None:
            nv = len(me.vertices)
            co = np.empty(nv * 3)
            me.vertices.foreach_get('co', co)
            co = co.reshape(-1, 3)
            nl = len(me.loops)
            lv = np.empty(nl, dtype=np.int64)
            me.loops.foreach_get('vertex_index', lv)
            np_ = len(me.polygons)
            start = np.empty(np_, dtype=np.int64)
            total = np.empty(np_, dtype=np.int64)
            me.polygons.foreach_get('loop_start', start)
            me.polygons.foreach_get('loop_total', total)
            nxt = np.arange(nl) + 1
            nxt[start + total - 1] = start
            a, b = lv, lv[nxt]
            label = np.arange(nv)
            for _ in range(500):
                m = np.minimum(label[a], label[b])
                before = label.copy()
                np.minimum.at(label, a, m)
                np.minimum.at(label, b, m)
                label = label[label]
                if np.array_equal(label, before):
                    break
            order = np.argsort(label, kind='stable')
            bounds = np.searchsorted(label[order], np.unique(label))
            groups = {int(label[order[i]]): order[i:j] for i, j in zip(bounds, list(bounds[1:]) + [nv])}
            hit = self.cache[me.name] = (co, label, groups, lv, start)
        return hit

    def thickness(self, o, pi, n_world):
        co, label, groups, lv, start = self._mesh(o.data)
        shell = groups[int(label[lv[start[pi]]])]
        rot = np.array(o.matrix_world)[:3, :3]
        n_local = np.linalg.solve(rot, n_world)
        n_local /= np.linalg.norm(n_local) or 1.0
        proj = co[shell] @ n_local
        return float(proj.max() - proj.min())


def fix(passes=10):
    """Separate fighting faces by layering. Each group of mutually overlapping coplanar faces is
    coloured greedily in visibility order (see below); a face on layer k sinks k * LIFT into its own
    solid. Repeats in case a move lands on another plane. Returns the number of faces moved."""
    moved_total = 0
    for _ in range(passes):
        objs, pairs = find()
        if not pairs:
            break
        nodes = {}
        adj = defaultdict(set)
        shells = _Shells()
        for p in pairs:
            ka = (objs[p['a'][0]].data.name, p['a'][1])
            kb = (objs[p['b'][0]].data.name, p['b'][1])
            if ka == kb:
                continue
            nodes.setdefault(ka, (p['a'][2], p['mat_a'], objs[p['a'][0]], p['a'][1], p['a'][3]))
            nodes.setdefault(kb, (p['b'][2], p['mat_b'], objs[p['b'][0]], p['b'][1], p['b'][3]))
            adj[ka].add(kb)
            adj[kb].add(ka)
        # The face that should show stays put: thin pieces (panes, rugs, decals, leaves) beat thick
        # ones (walls, floors, furniture bodies), then smaller beats larger, then by material. The rest
        # sink back into their own solid, so nothing is ever pushed toward the viewer.
        thick = {k: round(shells.thickness(v[2], v[3], np.asarray(v[4])), 2) for k, v in nodes.items()}
        layer = {}
        for k in sorted(nodes, key=lambda k: (thick[k], round(nodes[k][0], 4), nodes[k][1], k)):
            used = {layer[n] for n in adj[k] if n in layer}
            lv = 0
            while lv in used:
                lv += 1
            layer[k] = lv
        by_mesh = defaultdict(list)
        for k, lv in layer.items():
            if lv == 0:
                continue
            area, mat, o, pi, nrm = nodes[k]
            dist = LIFT * lv
            if thick[k] > 0.004:
                dist = min(dist, 0.45 * thick[k])  # never sink a face through its own solid
            inv = np.array(o.matrix_world.inverted())[:3, :3]
            by_mesh[o.data.name].append((o.data, pi, inv @ (-np.asarray(nrm) * dist)))
        if not by_mesh:
            break
        for items in by_mesh.values():
            me = items[0][0]
            co = np.empty(len(me.vertices) * 3)
            me.vertices.foreach_get('co', co)
            co = co.reshape(-1, 3)
            moved = set()
            for _, pi, off in items:
                for vi in me.polygons[pi].vertices:
                    if vi not in moved:
                        co[vi] += off
                        moved.add(vi)
                moved_total += 1
            me.vertices.foreach_set('co', co.ravel())
            me.update()
    return moved_total


def report(map_id, out_dir):
    objs, pairs = find()
    clusters = defaultdict(list)
    for p in pairs:
        c = p['center']
        clusters[(p['mats'], p['facing'], round(c[0] / 1.5), round(c[1] / 1.5), round(c[2] / 1.5))].append(p)
    lines = []
    for (mats, facing, *_), ps in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        c = np.mean([p['center'] for p in ps], axis=0)
        p0 = ps[0]
        nrm = p0['a'][3]
        lines.append(f'{facing:4} {mats[0]} / {mats[1]}  at blender({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f})  tris={len(ps)}  '
                     f'normal=({nrm[0]:.2f},{nrm[1]:.2f},{nrm[2]:.2f}) areas={p0["a"][2]:.4f}/{p0["b"][2]:.4f} '
                     f'objs={objs[p0["a"][0]].name}/{objs[p0["b"][0]].name}')
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f'zfight_{map_id}.txt')
    with open(path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'[zfight] {map_id}: {len(lines)} overlapping coplanar spots remain ({path})')
    for ln in lines[:25]:
        print('[zfight]  ', ln)
    return len(lines)
