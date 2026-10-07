"""Lanternfall Carnival: a shuttered travelling fairground at night where things still move on their own.

Layout (Blender XY, north = +Y, ~72 x 72 m inside a board hoarding):
  S   entrance gate (LANTERNFALL marquee), ticket booth, turnstiles, food-cart avenue  [hunter spawn]
  C   central plaza with the carousel
  N   Ferris wheel (landmark) with its loading deck; picnic yard to the north-east
  W   big-top tent (walk-through: plaza door east, performers' door west)
  E   midway lane of game booths, high striker at its north end, back alley behind the east booths
  NE  funhouse (walk-through: clown mouth -> mirror hall -> clown room / barrel tunnel -> side exits)
  NW  back lot: caravan circle, campfire, laundry, strongman corner
  SW  fortune teller's vardo, calliope bandwagon, picnic area
  SE  the Lion Cage (penalty box), ticket booth
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from lib import gh, prefabs as pf  # noqa: E402
import carnival_props as cp  # noqa: E402
from carnival_props import W, PI, TAU, cos, sin, bulb, seg_col  # noqa: E402

import numpy as np  # noqa: E402

# --- workaround (local to this map): gh.Geo.to_mesh box-projects UVs for every material, so smooth
# meshes in flat (untextured) materials get split at UV seams on export, roughly doubling vertex
# counts. Collapse those loops to one UV so the glTF exporter can share their vertices.
_orig_to_mesh = gh.Geo.to_mesh


def _to_mesh_flat_uv(self, name):
    mesh = _orig_to_mesh(self, name)
    flat = [i for i, mt in enumerate(mesh.materials)
            if not any(n.type == 'TEX_IMAGE' for n in mt.node_tree.nodes)]
    if flat and mesh.uv_layers:
        nf = len(mesh.polygons)
        midx = np.empty(nf, dtype=np.int32)
        mesh.polygons.foreach_get('material_index', midx)
        totals = np.empty(nf, dtype=np.int32)
        mesh.polygons.foreach_get('loop_total', totals)
        mask = np.isin(np.repeat(midx, totals), flat)
        uv = np.empty(len(mesh.loops) * 2, dtype=np.float32)
        mesh.uv_layers[0].data.foreach_get('uv', uv)
        uv = uv.reshape(-1, 2)
        uv[mask] = 0.5
        mesh.uv_layers[0].data.foreach_set('uv', uv.ravel())
        if len(flat) == len(mesh.materials):
            mesh.uv_layers.remove(mesh.uv_layers[0])   # no textures at all: skip TEXCOORD_0 on export
    return mesh


def split_untextured_chunks():
    """Split every static chunk into a textured and an untextured mesh so the latter can drop its UVs."""
    textured = {name for name, mt in m.mats.items() if any(n.type == 'TEX_IMAGE' for n in mt.bmat.node_tree.nodes)}
    for key, g in list(m.chunks.items()):
        if g.empty():
            continue
        tg, fg = gh.Geo(owner=m), gh.Geo(owner=m)
        maps = ({}, {})
        for f, mt, sm in zip(g.F, g.FM, g.FS):
            k = 0 if mt.name in textured else 1
            dst, remap = (tg, fg)[k], maps[k]
            nf = []
            for i in f:
                j = remap.get(i)
                if j is None:
                    j = remap[i] = len(dst.V)
                    dst.V.append(g.V[i])
                nf.append(j)
            dst.F.append(tuple(nf))
            dst.FM.append(mt)
            dst.FS.append(sm)
        m.chunks[key] = tg
        m.chunks[key + ('u',)] = fg


gh.Geo.to_mesh = _to_mesh_flat_uv

# Bevelled boxes export ~4x the vertices of plain ones; on thin trims the bevel is invisible anyway.
_orig_box = gh.Geo.box


def _box_lean(self, c, s, mat, rz=0.0, bevel=0.0, rx=0.0, ry=0.0, col=False):
    if bevel and min(s) < 0.15:
        bevel = 0.0
    return _orig_box(self, c, s, mat, rz=rz, bevel=bevel, rx=rx, ry=ry, col=col)


gh.Geo.box = _box_lean

m = gh.MapBuilder('carnival', 'Lanternfall Carnival', chunk=14.0, seed=11)
P = cp.palette(m)
EDGE = 35.6      # fence line
RNG = random.Random(5)


def S(x, y):
    return m.static(x, y)


def col_box(c, s):
    m.collider((c[0] - s[0] / 2, c[1] - s[1] / 2, c[2] - s[2] / 2), (c[0] + s[0] / 2, c[1] + s[1] / 2, c[2] + s[2] / 2))


def place(fn, ptype, label, pos, rz=0.0, params=None, key=None, **kw):
    return m.place(fn, ptype, label, pos, rz=rz, params=params, key=key, P=P, **kw)


def face_rz(fx, fy):
    """rz that turns a prefab's front (-Y) toward the direction (fx, fy)."""
    return math.atan2(fx, -fy)


# ================================================================ ground, paths, boundary

def jitter_rect(x0, y0, x1, y1, jit, seed, step=1.7):
    rng = random.Random(seed)
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    pts = []
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        L = math.dist(a, b)
        n = max(2, int(L / step))
        nx, ny = (b[1] - a[1]) / L, -(b[0] - a[0]) / L
        for k in range(n):
            t = k / n
            j = rng.uniform(-jit, jit) * 0.6 if 0 < k else 0
            pts.append((a[0] + (b[0] - a[0]) * t + nx * j, a[1] + (b[1] - a[1]) * t + ny * j))
    return pts


def jitter_circle(cx, cy, r, jit, seed, n=36, sy=1.0):
    rng = random.Random(seed)
    return [(cx + cos(k * TAU / n) * (r + rng.uniform(-jit, jit)), cy + sin(k * TAU / n) * (r + rng.uniform(-jit, jit)) * sy)
            for k in range(n)]


def dirt(pts, z, mat=None):
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    S(cx, cy).prism((0, 0, 0), pts, z, mat or P.dirt)


def build_ground():
    S(0, 0).box((0, 0, -0.15), (140, 140, 0.3), P.grass, col=False)
    m.collider((-36.5, -36.5, -0.4), (36.5, 36.5, 0.0))
    e = EDGE - 0.15
    m.collider((-38, -38, 0), (-e, 38, 14))
    m.collider((e, -38, 0), (38, 38, 14))
    m.collider((-38, -38, 0), (38, -e, 14))
    m.collider((-38, e, 0), (38, 38, 14))
    # trodden dirt: plaza, avenue, midway, connectors, clearings
    dirt(jitter_circle(0, 0, 12.0, 0.6, 1, n=48), 0.024)
    dirt(jitter_rect(-4.2, -35.5, 4.2, -9.0, 0.5, 2), 0.012)
    dirt(jitter_rect(-3.6, -52.0, 3.6, -35.4, 0.6, 22), 0.012)
    dirt(jitter_rect(15.8, -31.0, 25.2, 13.0, 0.5, 3), 0.014)
    dirt(jitter_rect(14.5, 12.0, 33.0, 24.2, 0.6, 4), 0.018)
    dirt(jitter_rect(8.5, -12.5, 17.0, -4.5, 0.5, 5), 0.016)
    dirt(jitter_rect(8.5, -0.8, 17.0, 4.6, 0.5, 6), 0.016)
    dirt(jitter_rect(-14.0, -4.2, -8.0, 2.4, 0.4, 7), 0.016)
    dirt(jitter_rect(-5.5, 9.0, 1.5, 27.0, 0.5, 8), 0.014)
    dirt(jitter_rect(3.0, -31.0, 16.5, -25.5, 0.5, 9), 0.016)
    dirt(jitter_rect(28.5, -33.0, 34.5, 30.0, 0.7, 10), 0.01)
    dirt(jitter_circle(-23.5, 21.5, 7.0, 1.0, 11), 0.012)
    dirt(jitter_circle(-21.0, -20.5, 6.5, 0.9, 12), 0.012)
    dirt(jitter_rect(-35.2, -13.0, -31.5, 15.0, 0.5, 13), 0.01)
    dirt(jitter_rect(-11.5, -16.0, -5.5, -8.0, 0.6, 14), 0.008)
    dirt(jitter_rect(-24.0, 6.0, -19.5, 16.0, 0.5, 15), 0.008)
    dirt(jitter_rect(6.0, 17.0, 16.0, 31.0, 0.7, 16), 0.01)
    for i, (x, y, r) in enumerate(((3.2, -18.0, 0.9), (-2.0, -26.0, 0.7), (6.5, 9.5, 1.1), (20.0, -9.0, 1.2), (21.5, 6.0, 0.8),
                                   (-21.0, 15.0, 0.9), (-9.0, -9.5, 1.0), (31.0, -6.0, 0.9), (12.0, 22.0, 0.8))):
        cp.puddle(S(x, y), P, (x, y), r * 0.7, seed=i, rz=i * 0.7)


def fence_run(a, b, rz_in, seed=0, posters=()):
    L = math.dist(a, b)
    n = max(1, round(L / 2.4))
    dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    horiz = abs(dy) < 1e-6
    rng = random.Random(seed)
    for i in range(n):
        p0 = (a[0] + dx * L * i / n, a[1] + dy * L * i / n)
        mid = (a[0] + dx * L * (i + 0.5) / n, a[1] + dy * L * (i + 0.5) / n)
        ln = L / n
        g = S(*mid)
        mat = P.boards_red if (i + seed) % 3 else P.boards_cream
        hh = 2.3 + (0.25 if i % 5 == 2 else 0.0)
        size = (ln - 0.06, 0.08, hh) if horiz else (0.08, ln - 0.06, hh)
        g.box((mid[0], mid[1], 0.05 + hh / 2), size, mat)
        g.box((p0[0], p0[1], 1.35), (0.18, 0.18, 2.7), P.wood_dark)
        if i % 2 == 0:
            g.sphere((p0[0], p0[1], 2.78), 0.1, P.mustard, n=8)
        if i in posters:
            ix, iy = sin(rz_in), -cos(rz_in)
            cp.poster(g, P, (mid[0] + ix * 0.05, mid[1] + iy * 0.05, 0), rz_in, kind=rng.randint(0, 2), w=1.0, h=1.3, z=0.7)
    S(*b).box((b[0], b[1], 1.35), (0.18, 0.18, 2.7), P.wood_dark)


def fence_buntings():
    y = -EDGE + 0.22
    place(cp.bunting, 'cloth', 'Fence Bunting', (-16.0, y, 2.55), a=(-4.9, 0, 0.0), b=(4.9, 0, 0.0), sag=0.35, fw=0.26, fh=0.34)
    place(cp.bunting, 'cloth', 'Fence Bunting', (20.9, y, 2.55), a=(-4.9, 0, 0.0), b=(4.9, 0, 0.0), sag=0.35, fw=0.26, fh=0.34,
          mats=[P.canvas_cream, P.canvas_teal, P.canvas_red])


def build_boundary():
    fence_run((-EDGE, EDGE), (EDGE, EDGE), 0.0, 0, posters=(3, 11, 22))
    fence_run((EDGE, -EDGE), (EDGE, EDGE), -PI / 2, 1, posters=(4, 9, 17, 25))
    fence_run((-EDGE, -EDGE), (-EDGE, EDGE), PI / 2, 2, posters=(5, 13, 20, 26))
    fence_run((-EDGE, -EDGE), (-6.2, -EDGE), PI, 3, posters=(2, 7))
    fence_run((6.2, -EDGE), (EDGE, -EDGE), PI, 4, posters=(4, 9))
    # tree line beyond the hoarding
    rng = random.Random(21)
    for side in range(4):
        for k in range(10):
            t = -42 + k * 9.3 + rng.uniform(-2.5, 2.5)
            d = rng.uniform(38.5, 45)
            x, y = [(t, d), (d, t), (t, -d), (-d, t)][side]
            if side == 2 and abs(x) < 9:
                y -= 6
            cp.tree_static(S(x, y), P, (x, y, 0), h=rng.uniform(7, 11), crown=rng.uniform(2.4, 3.6), seed=side * 50 + k,
                           style='pine' if rng.random() < 0.35 else 'round')


# ================================================================ entrance gate (south)

def build_gate():
    gy = -EDGE
    g = S(0, -33)
    for sx in (-1, 1):
        x = sx * 5.7
        for k in range(8):
            g.box((x, gy, 0.4 + k * 0.8), (1.0, 1.0, 0.8), P.red if k % 2 == 0 else P.cream, bevel=0.015)
        g.box((x, gy, 0.08), (1.2, 1.2, 0.16), P.wood_dark, bevel=0.02)
        g.box((x, gy, 6.45), (1.25, 1.25, 0.14), P.mustard, bevel=0.02)
        g.cyl((x, gy, 6.52), 0.85, 1.1, P.teal, n=4, r2=0.02, smooth=False, rz=PI / 4)
        g.sphere((x, gy, 7.7), 0.13, P.mustard, n=10)
        g.cyl((x, gy, 7.8), 0.02, 0.8, P.iron, n=4)
        g.add(cp.prim_pennant(0.55, 0.32, 3, 3, 'tri'), P.canvas_red, gh.X((x + 0.02 + 0.3, gy, 8.5), rz=0, ry=PI / 2))
        for k in range(10):
            bulb(g, (x - sx * 0.52, gy + 0.35, 0.6 + k * 0.6), P.bulb if k % 4 else P.bulb_dead, 0.045)
            bulb(g, (x - sx * 0.52, gy - 0.35, 0.6 + k * 0.6), P.bulb, 0.045)
        g.collide((x, gy, 3.3), (1.0, 1.0, 6.6))
        # iron railing panels between tower and gate leaves
        for i in range(10):
            xx = sx * (2.45 + i * 0.27)
            g.cyl((xx, gy, 0.05), 0.016, 2.0, P.iron, n=5)
            g.lathe((xx, gy, 2.05), [(0.03, 0), (0.001, 0.1)], P.iron, n=4, smooth=False)
        for z in (0.2, 1.1, 1.9):
            g.box((sx * 3.8, gy, z), (2.7, 0.04, 0.04), P.iron)
        g.collide((sx * 3.8, gy, 1.1), (2.75, 0.2, 2.2))
    # arched marquee board
    arch = [(-5.2, 0)] + [(-5.2 + 10.4 * i / 16, 1.45 + 0.65 * sin(PI * i / 16)) for i in range(17)] + [(5.2, 0)]
    arch_poly = [(x, 5.0 + z) for x, z in arch]
    g.prism((0, gy + 0.12, 0), arch_poly, 0.24, P.mustard, rx=PI / 2)
    inner = [(x * 0.97, 5.0 + 0.08 + z * 0.9) for x, z in arch]
    g.prism((0, gy + 0.14, 0), inner, 0.02, P.indigo, rx=PI / 2)
    for i in range(1, 16):
        x, z = arch[i + 1]
        bulb(g, (x * 0.99, gy + 0.18, 5.0 + z - 0.06), P.bulb if i % 5 else P.bulb_red, 0.05)
    for i in range(12):
        bulb(g, (-4.9 + i * 0.89, gy + 0.18, 5.08), P.bulb, 0.045)
    # marquee letters (flicker) on the inside face
    def marquee(p, P):
        dots = cp.text_dots('LANTERNFALL', 0.13)
        parts = [p.geo('bulb0'), p.geo('bulb1')]
        for u, v, ci in dots:
            c = (-u, 0.0, v)   # read from inside the park (looking south)
            if (ci * 7 + int(u * 100)) % 37 == 0:
                bulb(p.body, c, P.bulb_dead, 0.045)
            else:
                bulb(parts[ci % 2], c, P.bulb, 0.052)
        p.light((0, 2.2, -0.8), '#ffb860', 1.5, 11.0, part='bulb0')
        p.params.setdefault('sound', 'buzz')
    place(marquee, 'flicker', 'Lanternfall Marquee', (0, gy + 0.2, 5.55))
    # chained double gates (one leaf rattles)
    g.box((0, gy, 0.02), (4.9, 0.3, 0.04), P.iron)
    place(cp.gate_leaf, 'hinge', 'Front Gate', (2.42, gy, 0), w=2.4, h=2.5, side=-1)
    lg = S(-1, gy)
    with lg.at((-2.42, gy, 0)):
        cp.gate_leaf_geo(lg, P, w=2.4, h=2.5, side=1)
    col_box((0, gy, 1.3), (4.9, 0.3, 2.6))
    # ticket booth (east) and turnstiles (west)
    build_ticket_booth((7.4, -32.2))
    place(cp.turnstile, 'spin', 'Turnstile', (-5.55, -31.6, 0), rz=0)
    gt0 = S(-7.2, -31.6)
    gt0.box((-7.25, -31.6, 0.5), (0.25, 0.25, 1.0), P.red)
    gt0.box((-7.25, -31.6, 1.02), (0.3, 0.3, 0.04), P.mustard)
    gt0.collide((-7.25, -31.6, 0.5), (0.3, 0.3, 1.0))
    for k in range(4):
        a = k * TAU / 4 + 0.6
        gt0.tube([(-7.25, -31.6, 1.11), (-7.25 + 0.6 * cos(a), -31.6 + 0.6 * sin(a), 1.11)], 0.024, P.brass, n=6)
    gt = S(-6.4, -31.6)
    for x in (-4.7, -6.4, -8.1):
        gt.box((x, -31.6, 0.5), (0.1, 1.6, 1.0), P.iron)
        gt.box((x, -31.6, 1.02), (0.14, 1.7, 0.05), P.brass)
        gt.collide((x, -31.6, 0.5), (0.14, 1.6, 1.0))
    cp.ticket_litter(S(-6, -30), P, (-6.2, -30.2), n=9, seed=3, spread=1.4)
    cp.ticket_litter(S(5, -30), P, (5.6, -29.6), n=6, seed=4, spread=1.0)


def build_ticket_booth(c):
    g = S(*c)
    with g.at((c[0], c[1], 0), rz=face_rz(-1, 0)):
        rz8 = PI / 8
        g.lathe((0, 0, 0), [(1.0, 0), (1.0, 1.0)], P.boards_red, n=8, smooth=False, rz=rz8)
        g.lathe((0, 0, 1.0), [(1.1, 0), (1.1, 0.07)], P.mustard, n=8, smooth=False, rz=rz8)
        for k in range(8):
            a = k * TAU / 8 + rz8
            g.box((cos(a) * 1.0, sin(a) * 1.0, 1.7), (0.09, 0.09, 1.3), P.mustard, rz=a)
            am = a + TAU / 16
            if k != 5:
                with g.at((cos(am) * 0.93, sin(am) * 0.93, 1.7), rz=am):
                    g.box((0, 0, 0), (0.03, 0.72, 1.2), P.glass)
                    g.box((0.02, 0, 0.25), (0.02, 0.72, 0.04), P.mustard)
        g.lathe((0, 0, 2.35), [(1.2, 0), (1.25, 0.08)], P.mustard, n=8, smooth=False, rz=rz8)
        prof = [(1.25, 0.0), (1.15, 0.25), (0.85, 0.55), (0.45, 0.9), (0.15, 1.2), (0.02, 1.35)]
        for k in range(8):
            g.add(gh.prim_lathe(prof, 2, False, False, False, arc=TAU / 8), P.red if k % 2 else P.cream,
                  gh.X((0, 0, 2.43), rz=k * TAU / 8 + rz8))
        g.sphere((0, 0, 3.82), 0.09, P.mustard, n=8)
        for k in range(16):
            a = k * TAU / 16
            bulb(g, (cos(a) * 1.27, sin(a) * 1.27, 2.4), P.bulb if k % 6 else P.bulb_dead, 0.04)
        g.box((0, -0.25, 1.95), (1.0, 0.5, 0.06), P.wood_dark)
        g.box((0, -0.6, 0.95), (0.9, 0.3, 0.05), P.wood, bevel=0.01)
        g.cyl((0.25, -0.3, 1.0), 0.07, 0.12, P.cream, n=10, rx=PI / 2)
        g.box((0, -1.02, 0.55), (0.7, 0.02, 0.4), P.indigo)
        cp.painted_letters(g, 'TICKETS', (0, -1.035, 0.42), 0.022, P.cream)
        g.collide((0, 0, 1.2), (2.1, 2.1, 2.4))
    rz = face_rz(-1, 0)
    place(cp.service_bell, 'bell', 'Ticket Bell', W((c[0], c[1], 0), rz, (-0.2, -0.62, 0.975)), rz)
    gt = S(*c)
    with gt.at(W((c[0], c[1], 0), rz, (0, -0.98, 2.36)), rz, rx=-0.9):
        gt.box((0, -0.025, -0.38), (0.95, 0.05, 0.75), P.boards_red)
        gt.box((0, -0.055, -0.38), (0.8, 0.01, 0.6), P.mustard)


# ================================================================ central plaza + carousel

def build_carousel():
    g = S(0, 0)
    R, ph = 5.6, 0.35
    poly = [(R * cos(k * TAU / 32), R * sin(k * TAU / 32)) for k in range(32)]
    g.prism((0, 0, 0), poly, ph - 0.05, P.red)
    g.prism((0, 0, ph - 0.05), poly, 0.05, P.planks)
    g.torus((0, 0, ph - 0.03), R, 0.035, P.mustard, n=32, m=4)
    g.torus((0, 0, 0.06), R + 0.01, 0.03, P.mustard, n=32, m=4)
    for k in range(16):
        a = k * TAU / 16
        g.sphere((cos(a) * (R + 0.02), sin(a) * (R + 0.02), 0.17), 0.06, P.mustard, n=6)
    # strip colliders for the round platform
    for i in range(14):
        y0, y1 = -R + i * 0.8, -R + (i + 1) * 0.8
        yy = max(abs(y0), abs(y1)) if y0 * y1 > 0 else 0.0
        hw = math.sqrt(max(0.0, R * R - yy * yy))
        if hw > 0.3:
            m.collider((-hw, y0, 0.0), (hw, y1, ph))
    # centre column, sweeps and canopy
    g.cyl((0, 0, ph), 0.5, 4.0, P.cream, n=12)
    g.cyl((0, 0, ph), 0.55, 0.3, P.mustard, n=12)
    col_box((0, 0, 2.3), (2.5, 2.5, 4.0))
    zs = 4.3
    for k in range(20):
        a = k * TAU / 20
        with g.at((0, 0, zs), rz=a):
            g.box((3.2, 0, 0.0), (5.6, 0.12, 0.18), P.wood_dark)
            g.box((3.2, 0, -0.1), (5.6, 0.13, 0.03), P.mustard)
    g.cyl((0, 0, zs - 0.2), 0.8, 0.45, P.mustard, n=16)
    Rb = 6.05
    nb = 30
    for k in range(nb):
        a = (k + 0.5) * TAU / nb
        ch = 2 * Rb * sin(PI / nb) + 0.02
        with g.at((cos(a) * Rb, sin(a) * Rb, 0), rz=a):
            g.box((0, 0, 4.72), (0.08, ch, 0.86), P.cream if k % 2 else P.teal)
            g.box((0.05, 0, 4.72), (0.02, ch * 0.66, 0.5), P.mirror if k % 2 == 0 else P.red)
            g.box((0.06, 0, 4.72), (0.02, ch * 0.78, 0.05), P.mustard)
            g.box((0.06, ch / 2 - 0.02, 4.72), (0.03, 0.05, 0.86), P.mustard)
            for half in (-1, 1):
                g.add(cp.prim_pennant(ch / 2, 0.32, 3, 3, 'scallop'), P.canvas_red if k % 2 else P.canvas_cream,
                      gh.X((0.07, half * ch / 4, 4.29), rz=PI / 2))
    g.torus((0, 0, 5.15), Rb + 0.02, 0.05, P.mustard, n=48, m=4)
    g.torus((0, 0, 4.29), Rb + 0.02, 0.04, P.mustard, n=48, m=4)
    cp.wedge_cone(g, (0, 0, 5.15), Rb + 0.15, 0.0, 0.75, 1.95, [P.canvas_teal, P.canvas_cream], n=20, rows=6, sag=0.25)
    g.cyl((0, 0, 7.05), 0.75, 0.5, P.mustard, n=16)
    for k in range(8):
        a = k * TAU / 8
        g.box((cos(a) * 0.76, sin(a) * 0.76, 7.3), (0.03, 0.22, 0.3), P.mirror, rz=a)
    cp.wedge_cone(g, (0, 0, 7.55), 0.95, 0.0, 0.03, 0.75, [P.canvas_red, P.canvas_cream], n=12, rows=2, sag=0.08)
    g.sphere((0, 0, 8.4), 0.14, P.mustard, n=10)
    g.cyl((0, 0, 8.5), 0.02, 0.9, P.iron, n=4)
    g.add(cp.prim_pennant(0.7, 0.36, 3, 3, 'tri'), P.canvas_red, gh.X((0.37, 0, 9.35), ry=PI / 2))
    for k in range(20):
        a = k * TAU / 20
        bulb(g, (cos(a) * 3.2, sin(a) * 3.2, 4.08), P.bulb, 0.04)
    # carousel props
    place(cp.mirror_drum, 'spin', 'Carousel Mirror Drum', (0, 0, ph))
    horses = [(P.cream, P.red, P.mustard), (P.indigo, P.mustard, P.cream), (P.cream, P.teal, P.red),
              (P.teal, P.red, P.cream), (P.cream, P.indigo, P.mustard)]
    for k in range(10):
        a = k * TAU / 10 + 0.1
        coat, saddle, mane = horses[k % 5]
        place(cp.horse, 'bob', 'Carousel Horse', (cos(a) * 4.3, sin(a) * 4.3, ph), rz=a + PI / 2,
              params={'amp': 0.08 + 0.02 * (k % 3)}, key=f'horse{k % 5}', coat=coat, saddle=saddle, mane=mane)
    a = 0.1 + TAU / 20
    place(cp.band_organ, 'music', 'Carousel Band Organ', (cos(a) * 2.45, sin(a) * 2.45, ph), rz=a + PI / 2)
    for k, a in enumerate((0.1 + TAU / 20 + TAU / 3, 0.1 + TAU / 20 + 2 * TAU / 3)):
        chariot(g, (cos(a) * 2.55, sin(a) * 2.55, ph), a + PI / 2, P.teal if k else P.red)
        col_box((cos(a) * 2.55, sin(a) * 2.55, ph + 0.5), (1.1, 1.1, 1.0))
    place(cp.ring_lights, 'flicker', 'Carousel Lights (east)', (0, 0, 0), r=Rb + 0.09, z=5.03, n=15, a0=-PI / 2, a1=PI / 2,
          rows=((0.0, 'b'), (-0.62, 'b')), light=((3.2, 0, 3.9), '#ffb45c', 1.8, 11.0), dead=(4, 19))
    place(cp.ring_lights, 'flicker', 'Carousel Lights (west)', (0, 0, 0), r=Rb + 0.09, z=5.03, n=15, a0=PI / 2, a1=3 * PI / 2,
          rows=((0.0, 'b'), (-0.62, 'b')), light=((-3.2, 0, 3.9), '#ffb45c', 1.8, 11.0), dead=(9, 22, 23))


def chariot(g, pos, rz, mat):
    with g.at(pos, rz):
        g.box((0, 0, 0.25), (1.2, 0.8, 0.5), mat, bevel=0.04)
        g.box((0, 0.3, 0.75), (1.2, 0.2, 0.6), mat, bevel=0.04)
        g.box((0, -0.05, 0.53), (1.0, 0.5, 0.06), P.red)
        for sx in (-1, 1):
            g.tube([(sx * 0.6, 0.35, 1.05), (sx * 0.75, 0.0, 0.9), (sx * 0.65, -0.35, 0.55)], 0.05, P.mustard, n=6)
        g.sphere((0.7, -0.38, 0.6), 1.0, P.cream, n=10, s=(0.12, 0.12, 0.2))
        g.tube([(0.7, -0.38, 0.7), (0.78, -0.42, 1.05), (0.68, -0.5, 1.25)], 0.045, P.cream, n=6)
        g.sphere((0.66, -0.52, 1.27), 0.08, P.cream, n=8)
        g.prism((0.66, -0.6, 1.25), [(-0.02, 0), (0.02, 0), (0, -0.1)], 0.03, P.mustard, rx=PI / 2)


def build_plaza():
    for k, a in enumerate((PI / 4, 3 * PI / 4, 5 * PI / 4, 7 * PI / 4)):
        x, y = cos(a) * 10.6, sin(a) * 10.6
        place(cp.lantern_post, 'flame', 'Plaza Lantern', (x, y, 0), key='lantern_lit', light=True)
        place(cp.bunting, 'cloth', 'Carousel Bunting', (cos(a) * 8.3, sin(a) * 8.3, 4.2),
              a=(cos(a) * -2.2, sin(a) * -2.2, 0.95), b=(cos(a) * 2.3, sin(a) * 2.3, -0.9), sag=0.35,
              mats=[P.canvas_red, P.canvas_cream, P.canvas_teal, P.canvas_mustard][k:] + [P.canvas_red, P.canvas_cream, P.canvas_teal, P.canvas_mustard][:k])
    for k, a in enumerate((0.42, PI - 0.42, PI + 0.42, -0.42, PI / 2 + 0.5, PI / 2 - 0.5)):
        x, y = cos(a) * 9.7, sin(a) * 9.7
        cp.bench(S(x, y), P, (x, y, 0), rz=face_rz(-x, -y))
    for x, y in ((9.6, 1.3), (-9.6, -1.6), (2.0, -10.2), (-2.4, 10.3)):
        cp.trash_barrel(S(x, y), P, (x, y, 0), mat=P.teal if x > 0 else P.red)
    a = PI - 0.42
    place(cp.plush, 'jolt', 'Forgotten Teddy', W((cos(a) * 9.7, sin(a) * 9.7, 0), face_rz(-cos(a), -sin(a)), (0.45, 0.02, 0.47)),
          rz=face_rz(-cos(a), -sin(a)), kind='bear', s=0.42, fur=P.fur)
    place(cp.balloons, 'bob', 'Balloon Bunch', (-5.2, -8.6, 0), n=6, seed=1)
    place(cp.balloons, 'bob', 'Balloon Bunch', (9.3, 4.6, 0), n=5, seed=2, post_mat=P.teal)
    place(cp.spring_rider, 'rock', 'Duck Spring Rider', (-4.6, 8.4, 0), rz=face_rz(0.5, -1))
    gp = S(0, -9)
    for i, (x, y) in enumerate(((1.0, -8.2), (-6.4, 4.4), (7.3, -2.7), (-1.6, 8.9), (5.0, 7.8))):
        cp.popcorn_box(gp, P, (x, y, 0.02), rz=i * 1.3, tipped=i % 2 == 0)
    cp.ticket_litter(gp, P, (-3.0, -7.5), n=6, seed=8, spread=1.6)
    cp.ticket_litter(gp, P, (7.0, 6.0), n=5, seed=9, spread=1.3)
    cp.deflated_balloon(gp, P, (6.9, -7.4, 0), P.balloons[1], rz=0.6)
    cp.deflated_balloon(gp, P, (-8.0, 5.9, 0), P.balloons[0], rz=2.1)


# ================================================================ south avenue (food carts)

def build_avenue():
    place(cp.lantern_post, 'flame', 'Avenue Lantern', (-4.4, -25.0, 0), key='lantern_lit', light=True)
    place(cp.lantern_post, 'flame', 'Avenue Lantern', (4.4, -14.5, 0), key='lantern_dark', light=False)
    for (x, y) in ((4.4, -25.0), (-4.4, -14.5)):
        cp.lamp_static(S(x, y), P, (x, y, 0), h=3.0, lit=True)
    place(cp.bunting, 'cloth', 'Avenue Bunting', (0, -25.0, 3.2), a=(-4.4, 0, 0.1), b=(4.4, 0, 0.1), sag=0.7)
    place(cp.bulb_string, 'flicker', 'Avenue Festoon', (0, -14.5, 3.2), a=(-4.4, 0, 0.1), b=(4.4, 0, 0.1), sag=0.8, seed=3)
    place(cp.popcorn_cart, 'jolt', 'Popcorn Cart', (-6.4, -20.5, 0), rz=face_rz(1, 0))
    place(cp.candy_cart, 'jolt', 'Candy Floss Cart', (5.6, -11.5, 0), rz=face_rz(-1, 0.3))
    place(cp.balloons, 'bob', 'Balloon Vendor Bunch', (-6.0, -12.0, 0), n=9, seed=4, h=2.8, post_h=1.3, post_mat=P.red)
    gb = S(-6, -12)
    gb.box((-6.0, -12.0, 0.25), (0.6, 0.6, 0.5), P.boards_teal, bevel=0.02)
    gb.collide((-6.0, -12.0, 0.25), (0.6, 0.6, 0.5))
    for i, (x, y) in enumerate(((-6.9, -19.4), (-5.2, -21.6), (-1.0, -20.0))):
        cp.popcorn_box(S(x, y), P, (x, y, 0.02), rz=i * 2.1, tipped=True)
    for i in range(10):
        rng = random.Random(i + 40)
        bulb(S(-6, -20), (-6.4 + rng.uniform(-1.2, 1.2), -20.5 + rng.uniform(-1.5, 1.5), 0.025), P.popcorn, 0.03)
    cp.bench(S(-6.8, -26), P, (-6.8, -27.5, 0), rz=face_rz(1, 0))
    cp.bench(S(6.8, -16), P, (6.6, -16.2, 0), rz=face_rz(-1, 0))
    cp.trash_barrel(S(-6, -24), P, (-6.2, -24.6, 0), mat=P.red)
    cp.lamp_static(S(4.6, -30), P, (4.6, -29.6, 0), lit=False)
    cp.lamp_static(S(-4.6, -30), P, (-4.6, -29.6, 0), lit=True)


# ================================================================ the lion cage (penalty box)

def build_lion_cage(c=(9.0, -20.5), rz=PI / 2):
    g = S(*c)
    hl, hw = 2.45, 1.9
    with g.at((c[0], c[1], 0), rz):
        g.box((0, 0, 0.72), (2 * hl + 0.1, 2 * hw + 0.1, 0.36), P.red, bevel=0.03)
        g.box((0, 0, 0.92), (2 * hl + 0.2, 2 * hw + 0.2, 0.06), P.mustard, bevel=0.01)
        g.box((0, 0, 0.45), (2 * hl - 0.6, 2 * hw - 0.8, 0.2), P.wood_dark)
        for sx in (-1, 1):
            for sy in (-1, 1):
                cp.spoked_wheel(g, P, (sx * 1.55, sy * (hw + 0.12), 0.58), 0.58, spokes=12, rim=P.red, spoke=P.mustard)
            g.cyl((sx * 1.55, -hw - 0.2, 0.58), 0.05, 2 * hw + 0.4, P.iron, n=6, rx=-PI / 2)
        for k in range(10):
            g.blob((-1.8 + k * 0.4, (k % 3 - 1) * 0.8, 0.96), 0.35, P.hay, seed=k, jitter=0.3, s=(1, 1, 0.18))
        g.box((0, 0, 0.955), (2 * hl - 0.1, 2 * hw - 0.1, 0.02), P.hay)
        for sx in (-1, 1):
            for sy in (-1, 1):
                g.box((sx * hl, sy * hw, 2.2), (0.2, 0.2, 2.6), P.red, bevel=0.02)
                g.sphere((sx * hl, sy * hw, 3.75), 0.12, P.mustard, n=8)
        nbar_l, nbar_s = 20, 15
        for i in range(nbar_l):
            x = -hl + 0.2 + i * (2 * hl - 0.4) / (nbar_l - 1)
            for sy in (-1, 1):
                g.cyl((x, sy * hw, 0.95), 0.022, 2.2, P.iron, n=5, caps=False)
        for i in range(nbar_s):
            y = -hw + 0.2 + i * (2 * hw - 0.4) / (nbar_s - 1)
            for sx in (-1, 1):
                g.cyl((sx * hl, y, 0.95), 0.022, 2.2, P.iron, n=5, caps=False)
        for z in (1.0, 2.1):
            for sy in (-1, 1):
                g.box((0, sy * hw, z), (2 * hl, 0.05, 0.04), P.iron)
            for sx in (-1, 1):
                g.box((sx * hl, 0, z), (0.05, 2 * hw, 0.04), P.iron)
        for sy in (-1, 1):
            g.box((0, sy * hw, 3.27), (2 * hl, 0.12, 0.45), P.red, bevel=0.01)
            g.box((0, sy * (hw + 0.065), 3.27), (2 * hl - 0.3, 0.01, 0.32), P.mustard)
            with g.at((0, sy * (hw + 0.075), 0), rz=0 if sy < 0 else PI):
                cp.painted_letters(g, 'LION', (0, 0, 3.15), 0.035, P.red)
        for sx in (-1, 1):
            g.box((sx * hl, 0, 3.27), (0.12, 2 * hw, 0.45), P.red, bevel=0.01)
        g.box((0, 0, 3.55), (2 * hl + 0.4, 2 * hw + 0.4, 0.12), P.mustard, bevel=0.02)
        g.box((0, 0, 3.66), (2 * hl + 0.2, 2 * hw + 0.2, 0.1), P.red, bevel=0.02)
        for k in range(14):
            x = -hl + 0.2 + k * (2 * hl - 0.4) / 13
            for sy in (-1, 1):
                bulb(g, (x, sy * (hw + 0.2), 3.48), P.bulb if (k + sy) % 5 else P.bulb_dead, 0.04)
        g.torus((0.4, 0.3, 1.0), 0.18, 0.04, P.cream, n=10, m=4)
        g.cyl((-1.2, -0.9, 0.97), 0.18, 0.08, P.iron, n=10)
        g.tube([(1.0, -0.6, 1.0), (1.4, -0.4, 1.02)], 0.035, P.cream, n=5)
        for sx in (1.0, 1.4):
            g.sphere((sx, -0.6 + (sx - 1.0) * 0.5, 1.02), 0.06, P.cream, n=6)
        g.box((-0.5, 0.8, 0.98), (1.2, 0.8, 0.03), P.velvet, rz=0.3)
        # door frame on the +x end
        g.box((hl + 0.03, 0, 2.0), (0.06, 1.1, 2.1), P.iron)
        # colliders: bed, four walls and lid (sealed)
        g.collide((0, 0, 0.47), (2 * hl + 0.2, 2 * hw + 0.2, 0.94))
        for sy in (-1, 1):
            g.collide((0, sy * hw, 2.2), (2 * hl + 0.2, 0.16, 2.6))
        for sx in (-1, 1):
            g.collide((sx * hl, 0, 2.2), (0.16, 2 * hw + 0.2, 2.6))
        g.collide((0, 0, 3.6), (2 * hl + 0.4, 2 * hw + 0.4, 0.3))
    for lx, ly in ((-1.3, -0.85), (1.3, -0.85), (-1.3, 0.85), (1.3, 0.85), (0.0, 0.0)):
        m.penalty_spawn(W((c[0], c[1], 0), rz, (lx, ly, 0.96)))
    m.penalty['label'] = 'The Lion Cage'
    place(cp.padlock_chain, 'swing', 'Cage Padlock', W((c[0], c[1], 0), rz, (hl + 0.12, 0.35, 1.9)), rz + PI / 2)
    place(cp.hanging_lantern, 'swing', 'Cage Lantern', W((c[0], c[1], 0), rz, (hl + 0.5, -1.3, 3.3)), rz, bracket=0.5,
          drop=0.35)
    # bare bulb inside the cage so whoever is locked in stays visible
    gb = S(*c)
    bc = W((c[0], c[1], 0), rz, (0.0, 0.0, 0.0))
    gb.cyl((bc[0], bc[1], 2.95), 0.006, 0.5, P.black, n=3, caps=False)
    gb.lathe((bc[0], bc[1], 2.86), [(0.02, 0), (0.03, 0.06), (0.025, 0.1)], P.brass, n=6)
    bulb(gb, (bc[0], bc[1], 2.8), P.bulb, 0.06)
    m.light((bc[0], bc[1], 2.7), '#ffc070', 1.3, 7.5)
    place(cp.tarp_sheet, 'cloth', 'Cage Tarp', W((c[0], c[1], 0), rz, (-hl - 0.14, 0, 3.4)), rz + PI / 2, w=2.4, h=1.5, mat=P.canvas_red)
    place(cp.tamer_stool, 'jolt', "Tamer's Stool", W((c[0], c[1], 0), rz, (1.0, -hw - 1.4, 0)), rz + 0.4)
    gs = S(*c)
    with gs.at(W((c[0], c[1], 0), rz, (-0.5, -hw - 1.2, 0)), rz + 0.15):
        gs.box((0, 0, 0.6), (0.06, 0.06, 1.2), P.wood_dark)
        gs.box((0, -0.04, 1.25), (0.7, 0.03, 0.4), P.cream, ry=0.06)
        cp.painted_letters(gs, 'KEEP BACK', (0, -0.06, 1.13), 0.016, P.red)


# ================================================================ big top (west)

def oval(L, R, n_side, n_end):
    pts = []
    for i in range(n_side):
        pts.append((-L + 2 * L * i / n_side, -R))
    for i in range(n_end):
        a = -PI / 2 + PI * i / n_end
        pts.append((L + R * cos(a), R * sin(a)))
    for i in range(n_side):
        pts.append((L - 2 * L * i / n_side, R))
    for i in range(n_end):
        a = PI / 2 + PI * i / n_end
        pts.append((-L + R * cos(a), R * sin(a)))
    return pts


def build_big_top(cx=-22.5, cy=-1.0):
    L, R, eave, H = 3.0, 7.0, 4.0, 9.6
    ns, ne = 5, 18
    pts = oval(L, R, ns, ne)
    N = len(pts)
    doors = {ns + 8, ns + 9, 2 * ns + ne + 8, 2 * ns + ne + 9}
    g = S(cx, cy)
    lift = 2.6
    with g.at((cx, cy, 0)):
        g.prism((0, 0, 0), [(x * 0.985, y * 0.985) for x, y in pts], 0.03, P.sawdust)
        for i in range(N):
            a, b = pts[i], pts[(i + 1) % N]
            mat = P.canvas_red if i % 2 == 0 else P.canvas_cream
            z0 = lift if i in doors else 0.0
            g.add(cp.prim_quad((a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], eave), (a[0], a[1], eave)), mat)
            seg_col(g, a, b, 0.3, z0, eave + 0.3, step=0.6)
            # roof gore
            K = 7
            top, rows = [], []
            for k in range(K + 1):
                t = k / K
                row = []
                for p in (a, b):
                    rx = max(-L, min(L, p[0]))
                    row.append((p[0] + (rx - p[0]) * t, p[1] * (1 - t), eave + (H - eave) * t ** 1.8))
                rows.append(row)
            verts, faces = [], []
            for k in range(K + 1):
                verts += rows[k]
            for k in range(K):
                faces.append((2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2))
            g.add((verts, faces, [True] * K), mat)
            # valance scallops
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy)
            th = math.atan2(dy, dx)
            nx, ny = dy / ln, -dx / ln
            for hlf in (-0.25, 0.25):
                mx, my = a[0] + dx * (0.5 + hlf), a[1] + dy * (0.5 + hlf)
                g.add(cp.prim_pennant(ln / 2 + 0.02, 0.5, 3, 4, 'scallop'), P.canvas_mustard if i % 2 == 0 else P.canvas_red,
                      gh.X((mx + nx * 0.06, my + ny * 0.06, eave + 0.05), rz=th))
            # guy ropes
            if i % 2 == 0 and i not in doors and (i - 1) not in doors and (i + 1) not in doors:
                sx, sy = a[0] + nx * 2.2, a[1] + ny * 2.2
                g.tube([(a[0], a[1], eave - 0.05), (sx, sy, 0.15)], 0.014, P.rope, n=4)
                g.box((sx, sy, 0.15), (0.06, 0.06, 0.3), P.wood, rx=0.2)
        # king poles, rigging and pole-top pennants
        for sx in (-1, 1):
            g.cyl((sx * L, 0, 0), 0.17, H + 1.3, P.cream, n=10)
            for z in (0.5, 2.5, 4.5, 6.5, 8.5):
                g.cyl((sx * L, 0, z), 0.19, 0.25, P.red, n=10)
            g.cyl((sx * L, 0, H - 0.1), 0.5, 0.25, P.mustard, n=12)
            g.sphere((sx * L, 0, H + 1.4), 0.14, P.mustard, n=10)
            g.add(cp.prim_pennant(1.0, 0.5, 3, 3, 'tri'), P.canvas_red, gh.X((sx * L + 0.52, 0, H + 1.2), ry=PI / 2))
            g.collide((sx * L, 0, H / 2), (0.4, 0.4, H))
            for k in range(8):
                ang = k * TAU / 8 + 0.2
                tgt = (sx * L + cos(ang) * 6.0, sin(ang) * 5.8)
                if abs(tgt[1]) > 6.4:
                    continue
                pts_b = cp.catenary((sx * L, 0, H - 0.5), (tgt[0], tgt[1], eave + 0.3), 0.5, 12)
                g.tube(pts_b, 0.008, P.iron, n=3, caps=False)
                for j in range(2, 12, 2):
                    pp = pts_b[j]
                    bulb(g, (pp[0], pp[1], pp[2] - 0.08), P.bulb if (j + k) % 7 else P.bulb_dead, 0.045)
        g.cyl((-L, 0, 7.8), 0.06, 2 * L, P.iron, n=6, ry=PI / 2)
        # tightrope with pole platforms and rope ladders
        g.cyl((-L, 0, 3.3), 0.012, 2 * L, P.rope, n=4, ry=PI / 2, caps=False)
        for sx in (-1, 1):
            g.box((sx * (L - 0.05), 0, 3.22), (0.9, 0.7, 0.06), P.planks)
            g.box((sx * (L - 0.05), -0.36, 3.3), (0.9, 0.03, 0.12), P.mustard)
            g.tube([(sx * (L + 0.35), 0.3, 3.2), (sx * L, 0.3, 2.7)], 0.025, P.iron, n=4)
            g.tube([(sx * (L + 0.35), -0.3, 3.2), (sx * L, -0.3, 2.7)], 0.025, P.iron, n=4)
            for side in (-0.18, 0.18):
                g.tube([(sx * (L + 0.3), side, 3.2), (sx * (L + 0.45), side, 0.0)], 0.012, P.rope, n=3)
            for k in range(10):
                z = 0.3 + k * 0.29
                xx = sx * (L + 0.3 + 0.15 * (1 - z / 3.2))
                g.cyl((xx, -0.18, z), 0.015, 0.36, P.wood, n=4, rx=-PI / 2, caps=False)
        # ring
        Rr = 3.0
        for k in range(24):
            a0, a1 = k * TAU / 24, (k + 1) * TAU / 24
            am = (a0 + a1) / 2
            ch = 2 * Rr * sin(PI / 24) + 0.03
            with g.at((cos(am) * Rr, sin(am) * Rr, 0), rz=am):
                g.box((0, 0, 0.19), (0.32, ch, 0.38), P.red if k % 2 else P.cream)
                g.box((0, 0, 0.395), (0.36, ch, 0.04), P.mustard)
            seg_col(g, (cos(a0) * Rr, sin(a0) * Rr), (cos(a1) * Rr, sin(a1) * Rr), 1.1, 0.0, 0.4, step=0.8)
        g.prism((0, 0, 0), [(cos(k * TAU / 32) * (Rr - 0.14), sin(k * TAU / 32) * (Rr - 0.14)) for k in range(32)], 0.045, P.dirt)
        # bleachers along the straight sides
        for sy in (-1, 1):
            for t in range(3):
                yf = sy * (4.55 + 0.75 * t)
                top = 0.4 * (t + 1)
                yc = yf + sy * 0.375
                g.box((0, yc, top / 2), (6.6, 0.75, top), P.red)
                g.box((0, yc - sy * 0.1, top - 0.03), (6.7, 0.5, 0.06), P.planks, bevel=0.01)
                g.box((0, yf + sy * 0.02, top - 0.12), (6.65, 0.03, 0.08), P.mustard)
                g.collide((0, yc, top / 2), (6.6, 0.75, top))
            for x in (-3.32, 3.32):
                for t in range(3):
                    yy = sy * (4.6 + 0.75 * t + 0.1)
                    g.cyl((x, yy, 0.4 * (t + 1)), 0.025, 0.85, P.iron, n=5, caps=False)
                g.tube([(x, sy * 4.7, 1.25), (x, sy * 6.2, 2.05)], 0.03, P.brass, n=5)
            for t in range(3):
                yf = sy * (4.55 + 0.75 * t)
                for k in range(9):
                    g.box((-3.0 + k * 0.75, yf + sy * 0.05, 0.4 * t + 0.2), (0.05, 0.05, 0.36), P.wood_dark)
        # performers' end: wardrobe trunk, costume rack, ringmaster podium
        g.box((-8.0, 3.0, 0.35), (1.1, 0.6, 0.7), P.boards_indigo, bevel=0.03, col=True)
        g.box((-8.0, 3.0, 0.72), (1.14, 0.64, 0.06), P.mustard)
        g.box((-7.5, -3.4, 0.9), (0.06, 1.6, 0.06), P.iron)
        for sy in (-1, 1):
            g.box((-7.5, -3.4 + sy * 0.8, 0.45), (0.05, 0.05, 0.9), P.iron)
        for k, mat in enumerate((P.canvas_red, P.canvas_teal, P.velvet, P.canvas_mustard)):
            g.add(gh.prim_sheet(0.5, 0.85, 3, 4), mat, gh.X((-7.5, -3.95 + k * 0.38, 0.86), rz=PI / 2 + 0.2 * (k % 2)))
        g.collide((-7.5, -3.4, 0.5), (0.4, 1.7, 1.0))
        g.box((6.4, -3.2, 0.5), (0.9, 0.9, 1.0), P.boards_red, bevel=0.03)
        g.box((6.4, -3.2, 1.02), (1.0, 1.0, 0.05), P.mustard)
        g.cyl((6.4, -3.2, 1.05), 0.18, 0.04, P.black, n=12)
        g.cyl((6.4, -3.2, 1.08), 0.11, 0.22, P.black, n=12)
        g.torus((6.4, -3.2, 1.12), 0.11, 0.012, P.red, n=12, m=3)
        g.collide((6.4, -3.2, 0.5), (0.9, 0.9, 1.0))
        # marquee over the main (east) entrance
        ex = L + R
        for sy in (-1, 1):
            g.cyl((ex + 0.9, sy * 1.7, 0), 0.08, 4.6, P.mustard, n=8)
            g.collide((ex + 0.9, sy * 1.7, 2.3), (0.2, 0.2, 4.6))
        g.box((ex + 0.9, 0, 4.2), (0.16, 3.6, 0.8), P.indigo, bevel=0.02)
        g.box((ex + 0.98, 0, 4.2), (0.02, 3.7, 0.9), P.mustard)
        g.box((ex + 0.99, 0, 4.2), (0.02, 3.4, 0.68), P.indigo)
        with g.at((ex + 1.01, 0, 0), rz=PI / 2):
            for u, v, ci in cp.text_dots('CIRCUS', 0.095):
                bulb(g, (u, 0, 3.88 + v), P.bulb if (ci * 7 + int(u * 31) + int(v * 53)) % 17 else P.bulb_dead, 0.04)
    # lid / ceiling collider (tent interior)
    m.collider((cx - L - R, cy - R, eave), (cx + L + R, cy + R, eave + 0.3))
    # props inside
    T = lambda x, y, z=0.0: (cx + x, cy + y, z)  # noqa: E731
    for i, x in enumerate((-1.1, 1.1)):
        place(cp.trapeze, 'swing', 'Trapeze', T(x, 0, 4.8), rope=3.0, params={'amp': 0.05 + 0.02 * i, 'period': 3.4 + 0.5 * i})
    place(cp.spotlight, 'swing', 'Ring Spotlight', T(L - 0.5, 0.6, 6.6), rz=PI / 2)
    g.tube([T(L, 0.0, 6.75), T(L - 0.5, 0.6, 6.62)], 0.03, P.iron, n=4)
    g.tube([T(L, 0.0, 6.2), T(L - 0.35, 0.42, 6.6)], 0.02, P.iron, n=4)

    place(cp.gong, 'bell', 'Ringmaster Gong', T(6.9, 3.0), rz=face_rz(-1, -0.3))
    place(cp.ring_pedestal, 'spin', 'Ring Pedestal', T(-1.7, 1.5))
    place(cp.fire_hoop, 'flame', 'Fire Hoop', T(1.9, -1.9), rz=0.6)
    place(cp.cannon, 'rock', 'Cannonball Cannon', T(-7.4, 0.2), rz=0.0)
    ball_wedges_static = cp.ball_wedges
    ball_wedges_static(g, T(-4.4, 3.9, 0.55), 0.55, [P.red, P.cream, P.teal, P.cream], n=8)
    g.collide(T(-4.4, 3.9, 0.55), (1.0, 1.0, 1.1))
    place(cp.show_clock, 'clock', 'Next Show Clock', (cx + L + R + 1.9, cy + 3.0, 0), rz=face_rz(1, 0.2), title='NEXT SHOW')
    cp.wedge_drum(g, T(1.8, 1.4, 0), 0.4, 0.32, 0.55, [P.teal, P.cream], n=10)
    g.cyl(T(1.8, 1.4, 0.55), 0.35, 0.05, P.mustard, n=12)
    g.collide(T(1.8, 1.4, 0.3), (0.8, 0.8, 0.6))
    for (x, y) in ((L + R + 0.15, 0.0), (-L - R - 0.15, 0.0)):
        door_flaps((cx + x, cy + y), x > 0)
    m.light(T(5.6, 0.0, 3.4), '#ffbf75', 1.1, 10.0)


def door_flaps(pos, east):
    rz = PI / 2 if east else -PI / 2

    def flaps(p, P):
        for k, sx in enumerate((-1, 1)):
            pt = p.part(f'cloth{k}', (sx * 1.15, 0.0, 3.95))
            pt.geo.sheet((0, 0, 0), 0.6, 3.85, P.canvas_red if k else P.canvas_cream, nx=6, ny=10)
            p.body.tube([(sx * 1.45, -0.05, 1.3), (sx * 1.1, -0.1, 1.25), (sx * 0.9, -0.08, 1.4)], 0.015, P.rope, n=3)
        p.params.setdefault('amp', 0.03)
        p.params.setdefault('sound', 'whoosh')
    off = 0.12 if east else -0.12
    place(flaps, 'cloth', 'Tent Flaps', (pos[0] + off, pos[1], 0), rz=rz)


# ================================================================ Ferris wheel (north)

def build_ferris(wx=-2.0, wy=29.5):
    R, AZ, half = 8.6, 11.2, 0.9
    g = S(wx, wy)
    with g.at((wx, wy, 0)):
        for y in (-half, half):
            g.torus((0, y, AZ), R, 0.1, P.cream, n=64, m=6, rx=PI / 2)
            g.torus((0, y, AZ), R * 0.7, 0.07, P.cream, n=48, m=5, rx=PI / 2)
            g.torus((0, y, AZ), 1.0, 0.08, P.mustard, n=16, m=5, rx=PI / 2)
            n = 32
            for i in range(n):
                a0, a1, a2 = TAU * i / n, TAU * (i + 0.5) / n, TAU * (i + 1) / n
                p0 = (R * cos(a0), y, AZ + R * sin(a0))
                pm = (R * 0.7 * cos(a1), y, AZ + R * 0.7 * sin(a1))
                p2 = (R * cos(a2), y, AZ + R * sin(a2))
                g.tube([p0, pm, p2], 0.035, P.cream, n=4, caps=False)
            for k in range(16):
                a = k * TAU / 16
                g.tube([(cos(a) * 1.0, y, AZ + sin(a) * 1.0), (cos(a) * R, y, AZ + sin(a) * R)], 0.05, P.cream, n=5, caps=False)
        for k in range(16):
            a = k * TAU / 16 + TAU / 32
            g.tube([(cos(a) * R * 0.7, -half, AZ + sin(a) * R * 0.7), (cos(a) * R * 0.7, half, AZ + sin(a) * R * 0.7)], 0.03, P.cream, n=4)
        for k in range(8):
            a = -PI / 2 + k * TAU / 8
            g.cyl((cos(a) * R, -half - 0.15, AZ + sin(a) * R), 0.06, 2 * half + 0.3, P.iron, n=6, rx=-PI / 2)
        g.cyl((0, -1.6, AZ), 0.2, 3.2, P.iron, n=10, rx=-PI / 2)
        g.cyl((0, -half - 0.1, AZ), 0.55, 2 * half + 0.2, P.red, n=14, rx=-PI / 2)
        for sy in (-1, 1):
            by = sy * 1.45
            g.box((0, by, AZ), (0.7, 0.4, 0.7), P.iron, bevel=0.03)
            for sx in (-1, 1):
                foot = (sx * 5.6, sy * 2.7, 0.0)
                top = (sx * 0.3, by, AZ - 0.3)
                g.tube([foot, top], 0.17, P.cream, n=8)
                inner = (foot[0] - sx * 0.55, foot[1], 0.0)
                g.tube([inner, (sx * 0.1, by, AZ - 0.9)], 0.09, P.cream, n=6)
                for j in range(1, 8):
                    t0 = j / 8.0
                    t1 = (j + 0.5) / 8.0
                    a = (foot[0] + (top[0] - foot[0]) * t0, foot[1] + (top[1] - foot[1]) * t0, foot[2] + (top[2] - foot[2]) * t0)
                    b = (inner[0] + (sx * 0.1 - inner[0]) * t1, inner[1] + (by - inner[1]) * t1, (AZ - 0.9) * t1)
                    g.tube([a, b], 0.035, P.cream, n=4)
                g.box((foot[0] - sx * 0.25, foot[1], 0.2), (1.4, 0.9, 0.4), P.stone, bevel=0.04)
                g.collide((foot[0] - sx * 0.25, foot[1], 0.2), (1.4, 0.9, 0.4))
                for j in range(6):
                    z = 0.35 + j * 0.6
                    t = z / (AZ - 0.3)
                    x = foot[0] + (top[0] - foot[0]) * t
                    y = foot[1] + (top[1] - foot[1]) * t
                    g.collide((x - sx * 0.25, y, z), (0.9, 0.5, 0.65))
            g.tube([(-5.0, by * 1.6, 1.2), (5.0, by * 1.6, 1.2)], 0.06, P.cream, n=5)
            g.tube([(-3.4, by * 1.4, 4.0), (3.4, by * 1.4, 4.0)], 0.05, P.cream, n=5)
        # loading deck with railings and a step
        dy0, dy1 = -4.9, -1.1
        g.box((0, (dy0 + dy1) / 2, 0.2), (7.0, dy1 - dy0, 0.4), P.planks, bevel=0.02)
        g.box((0, dy0 - 0.3, 0.1), (3.0, 0.6, 0.2), P.planks, bevel=0.02)
        g.collide((0, (dy0 + dy1) / 2, 0.2), (7.0, dy1 - dy0, 0.4))
        g.collide((0, dy0 - 0.3, 0.1), (3.0, 0.6, 0.2))
        for sx in (-1, 1):
            for j in range(5):
                y = dy0 + 0.1 + j * (dy1 - dy0 - 0.2) / 4
                g.cyl((sx * 3.4, y, 0.4), 0.035, 1.0, P.mustard, n=6)
            g.box((sx * 3.4, (dy0 + dy1) / 2, 1.4), (0.08, dy1 - dy0, 0.06), P.mustard)
            g.collide((sx * 3.4, (dy0 + dy1) / 2, 0.9), (0.15, dy1 - dy0, 1.0))
            for j in range(3):
                x = sx * (1.6 + j * 0.85)
                g.cyl((x, dy0 + 0.05, 0.4), 0.035, 1.0, P.mustard, n=6)
            g.box((sx * 2.5, dy0 + 0.05, 1.4), (1.8, 0.08, 0.06), P.mustard)
            g.collide((sx * 2.5, dy0 + 0.05, 0.9), (1.8, 0.15, 1.0))
        # bottom gondola collider (it hangs at the deck)
        g.collide((0, 0, 1.0), (1.45, 1.05, 0.7))
        # operator booth
        bx, by_ = 5.4, -6.1
        g.box((bx, by_, 0.1), (1.8, 1.8, 0.2), P.planks)
        g.box((bx, by_ + 0.85, 1.25), (1.8, 0.1, 2.5), P.boards_teal)
        g.box((bx + 0.85, by_, 1.25), (0.1, 1.8, 2.5), P.boards_teal)
        g.box((bx, by_ - 0.85, 0.55), (1.8, 0.1, 0.9), P.boards_teal)
        g.box((bx - 0.85, by_ + 0.4, 1.25), (0.1, 1.0, 2.5), P.boards_teal)
        for sx in (-1, 1):
            g.box((bx + sx * 0.85, by_ - 0.85, 1.25), (0.12, 0.12, 2.5), P.mustard)
        g.box((bx, by_, 2.6), (2.1, 2.1, 0.15), P.red, bevel=0.03)
        g.box((bx, by_ - 0.5, 1.0), (1.4, 0.5, 0.06), P.wood)
        for k in range(6):
            bulb(g, (bx - 0.9 + k * 0.36, by_ - 1.07, 2.5), P.bulb if k != 3 else P.bulb_dead, 0.04)
        g.collide((bx, by_, 1.3), (1.8, 1.8, 2.6))
        # height sign: "you must be this tall"
        with g.at((-2.4, dy0 - 0.9, 0), rz=0.15):
            g.box((0, 0, 0.75), (0.08, 0.08, 1.5), P.wood_dark)
            g.box((0.3, -0.05, 1.2), (0.6, 0.03, 0.08), P.red)
            g.sphere((0.6, -0.05, 1.2), 0.08, P.cream, n=8)
            g.box((0, -0.05, 1.75), (0.5, 0.04, 0.5), P.cream)
            g.cyl((0, -0.08, 1.75), 0.2, 0.01, P.red, n=12, rx=PI / 2)
            g.collide((0, 0, 0.75), (0.2, 0.2, 1.5))
    # props
    for k in range(8):
        a = -PI / 2 + k * TAU / 8
        shell = [P.boards_red, P.boards_teal, P.boards_cream, P.boards_indigo][k % 4]
        roofs = [[P.canvas_red, P.canvas_cream], [P.canvas_teal, P.canvas_cream], [P.canvas_mustard, P.canvas_red],
                 [P.canvas_cream, P.canvas_teal]][k % 4]
        place(cp.gondola, 'swing', 'Ferris Gondola', (wx + cos(a) * R, wy, AZ + sin(a) * R),
              params={'amp': 0.03 + 0.008 * (k % 3), 'period': 3.2 + 0.25 * (k % 4)}, key=f'gondola{k % 4}', shell=shell, roof=roofs)
    place(cp.wheel_hub, 'spin', 'Ferris Wheel Sunburst', (wx, wy - half - 0.4, AZ))
    place(cp.wheel_lights, 'flicker', 'Ferris Wheel Rim Lights', (wx, wy, AZ), R=R, half=half, n=72,
          light=((0, -4.0, -AZ + 2.6), '#ffb45c', 1.6, 11.0), seed=1)
    place(cp.wheel_lights, 'flicker', 'Ferris Wheel Spoke Lights', (wx, wy, AZ), R=R, half=half, n=8, spokes=True, seed=2)
    place(cp.lever, 'hinge', 'Brake Lever', (wx + 2.7, wy - 4.3, 0.4), rz=PI / 2)


# ================================================================ midway (east)

def booth_shell(g, w, d, h=2.7, wall=None, trim=None, aw=None, sign=True, seed=0, awning=1.3, posts=True, title=None, ink=None,
                back_posters=True):
    """Game booth, front facing local -Y. Interior floor y in [-d/2+0.6, d/2-0.15]."""
    wall = wall or P.boards_red
    trim = trim or P.mustard
    aw = aw or [P.canvas_red, P.canvas_cream]
    hw, hd = w / 2, d / 2
    rng = random.Random(seed)
    g.box((0, 0, 0.05), (w, d, 0.1), P.planks)
    g.box((0, hd - 0.06, h / 2), (w, 0.12, h), wall)
    for sx in (-1, 1):
        g.box((sx * (hw - 0.06), 0, h / 2), (0.12, d, h), wall)
        g.box((sx * (hw - 0.07), -hd + 0.07, h / 2 + 0.1), (0.18, 0.18, h + 0.2), trim, bevel=0.02)
    g.box((0, 0.1, h + 0.06), (w + 0.2, d + 0.3, 0.12), P.wood_dark)
    g.box((0, -hd + 0.28, 0.5), (w - 0.2, 0.5, 1.0), wall)
    g.box((0, -hd + 0.02, 0.5), (w - 0.3, 0.02, 0.7), trim)
    g.box((0, -hd + 0.01, 0.5), (w - 0.5, 0.02, 0.56), P.indigo)
    g.box((0, -hd + 0.2, 1.03), (w - 0.1, 0.66, 0.06), P.wood, bevel=0.01)
    g.box((0, -hd + 0.06, 2.45 + (h - 2.45) / 2), (w, 0.12, h - 2.45), wall)
    # shelves on the back wall
    for z in (1.45, 1.95):
        g.box((0, hd - 0.3, z), (w - 0.3, 0.4, 0.04), P.wood)
    for z in (1.45, 1.95):
        x = -hw + 0.35
        while x < hw - 0.3:
            kind = rng.random() if z > 1.5 else 0.9
            col = rng.choice([P.fur, P.pink, P.teal, P.mustard, P.cream, P.red])
            if kind < 0.6:
                s = rng.uniform(0.11, 0.16)
                g.sphere((x, hd - 0.3, z + 0.02 + s), s, col, n=6)
                g.sphere((x, hd - 0.33, z + 0.02 + s * 2.6), s * 0.7, col, n=6)
                bulb(g, (x - s * 0.5, hd - 0.33, z + 0.02 + s * 3.1), col, round(s * 0.25, 3))
                bulb(g, (x + s * 0.5, hd - 0.33, z + 0.02 + s * 3.1), col, round(s * 0.25, 3))
                x += s * 2 + 0.08
            else:
                bw = rng.uniform(0.22, 0.4)
                g.box((x + bw / 2, hd - 0.3, z + 0.14), (bw, 0.22, rng.uniform(0.16, 0.3)), col, rz=rng.uniform(-0.15, 0.15))
                x += bw + 0.1
    # awning: alternating strips
    n = max(4, int(round(w / 0.5)))
    sw = w / n
    drop = 0.45
    ang = math.atan2(drop, awning)
    ln = math.hypot(drop, awning)
    for i in range(n):
        x = -hw + sw * (i + 0.5)
        g.box((x, -hd - awning / 2, h - 0.05 - drop / 2), (sw + 0.005, ln, 0.03), aw[i % 2], rx=ang)
    if posts:
        for sx in (-1, 1):
            g.cyl((sx * (hw - 0.05), -hd - awning + 0.05, 0), 0.04, h - drop, P.wood_dark, n=6)
            g.collide((sx * (hw - 0.05), -hd - awning + 0.05, (h - drop) / 2), (0.15, 0.15, h - drop))
    # headboard sign
    if sign:
        top = h + 0.9
        poly = [(-hw + 0.2, h), (hw - 0.2, h), (hw - 0.2, h + 0.55), (hw * 0.5, h + 0.6), (0.6, top), (-0.6, top), (-hw * 0.5, h + 0.6),
                (-hw + 0.2, h + 0.55)]
        g.prism((0, -hd + 0.12, 0), poly, 0.08, trim, rx=PI / 2)
        inner = [(x * 0.92, h + (z - h) * 0.85 + 0.06) for x, z in poly]
        g.prism((0, -hd + 0.04, 0), inner, 0.02, wall, rx=PI / 2)
        for i, (x, z) in enumerate(poly[2:] + poly[:1]):
            pass
        for k in range(12):
            t = k / 11
            x = -hw + 0.3 + (w - 0.6) * t
            bulb(g, (x, -hd - 0.0, h + 0.05), P.bulb if rng.random() > 0.12 else P.bulb_dead, 0.04)
        if title:
            pitch = min(0.068, 0.82 * (w - 0.6) / (6 * len(title) - 1))
            cp.painted_letters(g, title, (0, -hd + 0.02, h + 0.42 - 3 * pitch), pitch, ink or P.cream)
    # bulbs under the awning edge
    ez = h - 0.05 - drop - 0.07
    for k in range(int(w / 0.55)):
        x = -hw + 0.3 + k * 0.55
        bulb(g, (x, -hd - awning + 0.06, ez), P.bulb if rng.random() > 0.15 else P.bulb_dead, 0.038)
    if back_posters:
        for k in range(1 + int(w > 4.8)):
            cp.poster(g, P, (-w * 0.22 + k * w * 0.44 if w > 4.8 else rng.uniform(-0.6, 0.6), hd + 0.02, 0), PI,
                      w=0.9, h=1.2, kind=seed + k, z=0.75)
    g.collide((0, 0, h / 2 + 0.06), (w, d, h + 0.12))


def booth_frame(origin, rz):
    return lambda x, y, z=0.0: W(origin, rz, (x, y, z))


def build_midway():
    # west row (fronts face east), east row (fronts face west)
    wrz, erz = face_rz(1, 0), face_rz(-1, 0)
    d = 3.4
    booths = [
        ('knock', (14.8, -23.5), wrz, 5.0, P.boards_teal, P.mustard, [P.canvas_teal, P.canvas_cream], 'KNOCK EM DOWN', P.mustard),
        ('ring', (14.8, -14.5), wrz, 5.0, P.boards_red, P.mustard, [P.canvas_red, P.canvas_cream], 'RING TOSS', P.cream),
        ('prize', (14.8, -2.3), wrz, 5.0, P.boards_indigo, P.mustard, [P.canvas_mustard, P.canvas_red], 'PRIZES', P.mustard),
        ('darts', (14.8, 7.0), wrz, 4.6, P.boards_cream, P.red, [P.canvas_red, P.canvas_cream], 'DARTS', P.red),
        ('gallery', (26.2, -11.5), erz, 7.0, P.boards_indigo, P.mustard, [P.canvas_red, P.canvas_mustard], 'SHOOTING GALLERY', P.cream),
        ('fish', (26.2, -0.6), erz, 4.6, P.boards_teal, P.cream, [P.canvas_teal, P.canvas_cream], 'GOLDFISH', P.mustard),
        ('prize2', (26.2, 8.6), erz, 5.0, P.boards_red, P.mustard, [P.canvas_cream, P.canvas_red], 'EVERY ONE WINS', P.cream),
    ]
    for i, (kind, c, rz, w, wall, trim, aw, title, ink) in enumerate(booths):
        g = S(*c)
        with g.at((c[0], c[1], 0), rz):
            booth_shell(g, w, d, wall=wall, trim=trim, aw=aw, seed=i, title=title, ink=ink)
            booth_contents(g, kind, w, d)
        F = booth_frame((c[0], c[1], 0), rz)
        hd = d / 2
        if kind in ('ring', 'prize', 'gallery', 'prize2'):
            place(cp.valance, 'cloth', 'Awning Valance', F(0, -hd - 1.3 + 0.02, 2.2), rz, w=w, mats=aw[::-1],
                  params={'amp': 0.02 + 0.01 * (i % 3)})
        booth_props(kind, F, rz, w, d)
    # bulb festoons and bunting across the lane
    for y in (-23.0, -9.0, 8.0):
        place(cp.bulb_string, 'flicker', 'Midway Festoon', (20.5, y, 3.3), a=(-4.0, 0, 0.1), b=(4.0, 0, 0.1), sag=0.75, seed=int(y),
              light=((0, 0, -0.9), '#ffb45c', 1.3, 9.0), red_every=4)
    place(cp.bunting, 'cloth', 'Midway Bunting', (20.5, -14.25, 3.3), a=(-4.0, -1.25, 0.1), b=(4.0, 1.25, 0.1), sag=0.8)

    # festoon poles where there is no booth to tie to
    for (x, y) in ((24.6, -23.0), (16.4, -9.0)):
        gp = S(x, y)
        gp.cyl((x, y, 0), 0.07, 3.5, P.wood_dark, n=6)
        gp.sphere((x, y, 3.52), 0.08, P.mustard, n=8)
        gp.collide((x, y, 1.75), (0.2, 0.2, 3.5))
    build_cutout_board((21.2, -5.4), face_rz(0.15, -1))
    build_kiosk((20.3, -18.6))
    # weight-guessing stand (east row, south)
    build_weight_stand((25.8, -24.0))
    build_high_striker((20.5, 16.5))
    # lane clutter
    for i, (x, y) in enumerate(((18.2, -26.5), (22.6, -19.0), (19.0, -7.5), (23.0, 2.0), (18.0, 11.0))):
        cp.popcorn_box(S(x, y), P, (x, y, 0.02), rz=i * 0.9, tipped=i % 2 == 1)
    cp.ticket_litter(S(20, -10), P, (20.5, -10.0), n=10, seed=21, spread=2.5)
    cp.ticket_litter(S(20, 5), P, (21.0, 5.0), n=7, seed=22, spread=2.0)
    cp.deflated_balloon(S(22, -4), P, (22.3, -4.4, 0), P.balloons[2], rz=1.1)
    cp.trash_barrel(S(17.4, -9), P, (17.4, -9.2, 0), mat=P.red)
    cp.trash_barrel(S(23.8, 4), P, (23.7, 4.0, 0), mat=P.teal)
    cp.bench(S(17.3, 1.4), P, (17.2, 1.6, 0), rz=face_rz(1, 0))


def build_cutout_board(c, rz):
    """Face-in-the-hole photo board: a strongman and a bearded lady (static cover in the lane)."""
    g = S(*c)
    with g.at((c[0], c[1], 0), rz):
        for sx in (-1.0, 1.0):
            g.box((sx * 1.1, 0.12, 1.0), (0.1, 0.1, 2.0), P.wood_dark)
            g.box((sx * 1.1, 0.3, 0.05), (0.1, 0.7, 0.1), P.wood_dark)
        poly = [(-1.3, 0.25), (1.3, 0.25), (1.3, 2.1), (0.7, 2.35), (0.0, 2.2), (-0.7, 2.35), (-1.3, 2.1)]
        g.prism((0, 0.06, 0), poly, 0.06, P.boards_cream, rx=PI / 2)
        for sx, body, trim in ((-0.62, P.red, P.cream), (0.62, P.teal, P.mustard)):
            g.box((sx, -0.01, 1.05), (0.9, 0.01, 1.3), body)
            for k in range(4):
                g.box((sx, -0.015, 0.55 + k * 0.32), (0.9, 0.01, 0.1), trim)
            g.cyl((sx, 0.08, 1.85), 0.15, 0.2, P.black, n=12, rx=PI / 2)
            g.cyl((sx, -0.012, 1.85), 0.19, 0.01, P.cream, n=14, rx=PI / 2)
        g.sphere((-0.62, -0.02, 1.4), 1.0, P.red, n=8, s=(0.5, 0.02, 0.18))
        g.box((0.62, -0.02, 1.55), (0.3, 0.01, 0.35), P.wood_dark)
        cp.painted_letters(g, 'SAY CHEESE', (0, -0.02, 0.32), 0.022, P.indigo)
        g.collide((0, 0.06, 1.15), (2.6, 0.3, 2.3))


def build_kiosk(c, roof=None, body=None, label=None):
    """Round kiosk with a striped dome (lemonade in the midway, ride tickets by the wheel)."""
    roof = roof or [P.canvas_cream, P.canvas_mustard]
    g = S(*c)
    with g.at((c[0], c[1], 0)):
        g.lathe((0, 0, 0), [(0.95, 0), (0.95, 1.05)], body or P.boards_cream, n=10, smooth=False)
        g.lathe((0, 0, 1.05), [(1.05, 0), (1.05, 0.06)], P.red, n=10, smooth=False)
        for k in range(5):
            a = k * TAU / 5
            g.cyl((cos(a) * 0.9, sin(a) * 0.9, 1.1), 0.04, 1.3, P.mustard, n=6)
        g.cyl((0, 0, 1.1), 0.5, 0.5, P.glass, n=10)
        g.cyl((0, 0, 1.12), 0.46, 0.35, P.mustard, n=10)
        cp.wedge_cone(g, (0, 0, 2.4), 1.35, 0.0, 0.05, 0.7, roof, n=10, rows=2, sag=-0.05)
        if label:
            g.box((0, -0.97, 0.62), (1.0, 0.04, 0.32), P.indigo)
            cp.painted_letters(g, label, (0, -1.0, 0.53), 0.02, P.mustard)
        g.sphere((0, 0, 3.15), 0.09, P.red, n=8)
        for k in range(10):
            a = (k + 0.5) * TAU / 10
            g.add(cp.prim_pennant(0.75, 0.22, 3, 3, 'scallop'), P.canvas_red if k % 2 else P.canvas_cream,
                  gh.X((cos(a) * 1.33, sin(a) * 1.33, 2.4), rz=a + PI / 2))
            bulb(g, (cos(a) * 1.2, sin(a) * 1.2, 2.32), P.bulb if k % 4 else P.bulb_dead, 0.035)
        for k in range(5):
            a = k * 1.1
            g.lathe((cos(a) * 0.3, sin(a) * 0.3, 1.47), [(0.035, 0), (0.04, 0.12)], P.cream, n=6, cap_top=False)
        g.collide((0, 0, 1.2), (1.9, 1.9, 2.4))


def booth_contents(g, kind, w, d):
    hd, hw = d / 2, w / 2
    if kind == 'knock':
        for x in (-1.5, 1.5):
            g.cyl((x, 0.3, 0.1), 0.05, 0.85, P.wood_dark, n=6)
            g.box((x, 0.3, 0.97), (0.42, 0.3, 0.04), P.red, bevel=0.01)
            for row, cnt in enumerate((3, 2, 1)):
                for i in range(cnt):
                    if x > 0 and row == 2:
                        continue
                    cp.milk_bottle(g, P, (x + (i - (cnt - 1) / 2) * 0.12, 0.3, 0.99 + row * 0.255))
                if row < 2:
                    g.box((x, 0.3, 0.99 + row * 0.255 + 0.252), (0.12 * cnt, 0.13, 0.008), P.wood)
            if x > 0:
                cp.milk_bottle(g, P, (x + 0.35, 0.0, 0.1))
        for i in range(3):
            g.sphere((-0.6 + i * 0.15, -hd + 0.25, 1.12), 0.06, P.cream, n=8)
        g.box((0, -hd + 0.25, 1.07), (0.6, 0.25, 0.04), P.wood_dark)
    elif kind == 'ring':
        for t in range(3):
            g.box((0, -0.1 + t * 0.35, 0.45 + t * 0.2), (w - 0.6, 0.35, 0.9 + t * 0.4), P.red if t % 2 else P.boards_red)
            for i in range(int((w - 0.8) / 0.18)):
                x = -hw + 0.5 + i * 0.18
                mat = P.bottle if (i + t) % 3 else P.balloons[2]
                g.lathe((x, -0.1 + t * 0.35, 0.9 + t * 0.4), [(0.04, 0), (0.042, 0.12), (0.016, 0.2), (0.016, 0.26)], mat, n=6)
        for k in range(5):
            g.torus((-hw + 0.5 + k * 0.08, hd - 0.12, 2.25), 0.12, 0.012, [P.red, P.mustard, P.teal][k % 3], n=12, m=3, rx=PI / 2)
        g.cyl((-hw + 0.45, hd - 0.06, 2.37), 0.015, 0.4, P.brass, n=4, rx=PI / 2)
    elif kind in ('prize', 'prize2'):
        for t in range(2):
            g.box((0, 0.6 - t * 0.5, 0.35 + t * 0.2), (w - 0.5, 0.45, 0.7 + t * 0.4), P.wood)
        rng = random.Random(len(kind))
        for t in range(1):
            x = -hw + 0.5
            while x < hw - 0.5:
                s = rng.uniform(0.18, 0.26)
                col = rng.choice([P.fur, P.pink, P.teal, P.cream])
                with g.at((x, 0.55 - t * 0.5, 0.7 + t * 0.4 + 0.0)):
                    cp.bear(g, P, s * 1.6, col, P.cream, lo=True)
                x += s * 1.6 + 0.2
    elif kind == 'darts':
        g.box((0, hd - 0.2, 1.75), (w - 0.5, 0.06, 1.4), P.wood)
        rng = random.Random(9)
        for i in range(7):
            for j in range(4):
                x = -hw + 0.55 + i * (w - 1.1) / 6
                z = 1.25 + j * 0.33
                if rng.random() < 0.18:
                    g.box((x, hd - 0.24, z), (0.1, 0.01, 0.06), P.balloons[(i + j) % 4], rz=0.3)
                else:
                    g.sphere((x, hd - 0.33, z), 1.0, P.balloons[(i + j) % 4], n=8, s=(0.12, 0.1, 0.14))
        for i in range(6):
            g.cyl((-0.5 + i * 0.12, -hd + 0.25, 1.07), 0.006, 0.12, P.wood_dark, n=4, ry=PI / 2)
            g.prism((-0.5 + i * 0.12 + 0.12, -hd + 0.25, 1.07), [(0, -0.015), (0.04, 0.0), (0, 0.015)], 0.006, P.red)
    elif kind == 'fish':
        g.box((0, 0.2, 0.45), (w - 0.5, 1.6, 0.9), P.wood)
        for i in range(6):
            for j in range(4):
                x = -hw + 0.55 + i * (w - 1.1) / 5
                y = -0.4 + j * 0.38
                g.lathe((x, y, 0.9), [(0.06, 0), (0.12, 0.05), (0.13, 0.12), (0.09, 0.2), (0.1, 0.22)], P.glass, n=10, cap_top=False)
                if (i * 3 + j) % 5 == 0:
                    g.sphere((x, y, 1.0), 1.0, P.mustard, n=6, s=(0.04, 0.015, 0.025))
        for k in range(8):
            g.torus((-0.6 + k * 0.17, -hd + 0.25, 1.07), 0.06, 0.008, [P.red, P.mustard, P.cream][k % 3], n=10, m=3)
    elif kind == 'gallery':
        g.box((0, hd - 0.15, 1.4), (w - 0.3, 0.05, 2.5), P.indigo)
        rng = random.Random(4)
        for i in range(24):
            x, z = rng.uniform(-hw + 0.4, hw - 0.4), rng.uniform(1.0, 2.5)
            g.prism((x, hd - 0.18, z), [(0, 0.06), (-0.05, -0.04), (0.05, -0.04)], 0.01, P.cream, rx=PI / 2)
        g.box((0, 0.7, 0.55), (w - 0.4, 0.3, 1.1), P.boards_teal)
        g.box((0, 1.22, 0.8), (w - 0.4, 0.56, 1.6), P.boards_teal)
        for i in range(5):
            x = -0.9 + i * 0.45
            g.cyl((x, -hd + 0.4, 1.08), 0.02, 0.85, P.iron, n=6, ry=PI / 2 - 0.05, rz=0.3)
            g.box((x + 0.1, -hd + 0.33, 1.1), (0.25, 0.06, 0.1), P.wood_dark, rz=0.3)
            g.tube([(x, -hd + 0.33, 1.08), (x - 0.1, -hd + 0.15, 1.07)], 0.006, P.iron, n=3)


def booth_props(kind, F, rz, w, d):
    hd = d / 2
    if kind == 'knock':
        place(cp.bottle_pyramid, 'jolt', 'Milk Bottle Pyramid', F(0.0, 0.3, 0.0), rz)
    elif kind == 'ring':
        pass
    elif kind == 'prize':
        place(cp.plush, 'jolt', 'Giant Bear', F(1.85, -hd + 0.3, 1.06), rz, kind='bear', s=0.75, fur=P.pink)
        place(cp.hanging_plush, 'swing', 'Hanging Teddy', F(-0.9, -hd - 1.15, 2.2), rz, s=0.55)
    elif kind == 'prize2':
        place(cp.plush, 'jolt', 'Giant Bear', F(-1.9, -hd + 0.3, 1.06), rz - 0.3, kind='bear', s=0.7, fur=P.fur)


    elif kind == 'gallery':
        place(cp.duck_row, 'bob', 'Duck Row', F(0, 0.7, 1.1), rz, length=w - 0.8, n=10)
        place(cp.duck_row, 'bob', 'Duck Row', F(0, 1.05, 1.6), rz, length=w - 0.8, n=9, params={'amp': 0.018})
        for i, x in enumerate((-1.6, 1.6)):
            place(cp.target_spinner, 'spin', 'Tin Target', F(x, 1.38, 1.6), rz, post=0.62, key='spinner')
        place(cp.shutter, 'hinge', 'Gallery Shutter', F(-w / 2 + 0.95, -hd + 0.02, 2.4), rz, w=1.6, h=0.9, mat=P.boards_indigo)


def build_weight_stand(c):
    rz = face_rz(-1, 0)
    g = S(*c)
    with g.at((c[0], c[1], 0), rz):
        g.box((0, 0, 0.08), (3.6, 2.6, 0.16), P.planks, bevel=0.02)
        g.collide((0, 0, 0.08), (3.6, 2.6, 0.16))
        g.box((0, 1.2, 1.4), (3.4, 0.1, 2.5), P.boards_cream)
        g.box((0, 1.2, 2.9), (3.6, 0.14, 0.6), P.red, bevel=0.02)
        g.box((0, 1.12, 2.9), (3.3, 0.02, 0.48), P.cream)
        cp.painted_letters(g, 'GUESS YOUR', (0, 1.105, 2.95), 0.034, P.red)
        cp.painted_letters(g, 'WEIGHT', (0, 1.105, 2.67), 0.032, P.indigo)
        g.collide((0, 1.2, 1.5), (3.6, 0.2, 3.0))
        for sx in (-1, 1):
            g.box((sx * 1.75, 1.2, 1.6), (0.14, 0.14, 3.2), P.mustard)
        g.box((1.0, 0.6, 0.55), (0.45, 0.45, 0.06), P.wood)
        for sx in (-1, 1):
            for sy in (-1, 1):
                g.cyl((1.0 + sx * 0.18, 0.6 + sy * 0.18, 0.16), 0.02, 0.4, P.wood_dark, n=4)
        g.box((1.0, 0.82, 0.85), (0.45, 0.04, 0.55), P.wood)
        g.box((-1.1, 0.7, 0.6), (0.6, 0.4, 0.9), P.boards_red, bevel=0.02)
        g.collide((-1.1, 0.7, 0.55), (0.6, 0.4, 1.1))
        g.box((-1.1, 0.7, 1.08), (0.65, 0.45, 0.04), P.mustard)
        for k in range(3):
            g.box((-1.25 + k * 0.15, 0.6, 1.15), (0.1, 0.13, 0.1), [P.red, P.teal, P.mustard][k], bevel=0.01)
    place(cp.weight_scale, 'clock', 'Guess-Your-Weight Scale', W((c[0], c[1], 0), rz, (0.0, 0.4, 0.16)), rz)


def build_high_striker(c):
    g = S(*c)
    x, y = c
    with g.at((x, y, 0)):
        g.box((0, 0, 0.12), (1.6, 1.4, 0.24), P.wood_dark, bevel=0.03)
        g.collide((0, 0, 0.12), (1.6, 1.4, 0.24))
        g.box((0, -0.4, 0.3), (0.5, 0.4, 0.12), P.red, bevel=0.02)
        g.cyl((0, -0.4, 0.36), 0.14, 0.04, P.mustard, n=12)
        g.box((0, 0.35, 3.4), (0.42, 0.16, 6.4), P.boards_cream)
        for k in range(10):
            z = 0.7 + k * 0.56
            mat = [P.mustard, P.red][k % 2] if k < 9 else P.teal
            g.box((0, 0.26, z + 0.25), (0.38, 0.02, 0.48), mat)
            g.box((0, 0.25, z), (0.4, 0.02, 0.03), P.black)
        g.cyl((0, 0.18, 0.3), 0.012, 6.0, P.brass, n=4)
        g.cyl((0, 0.18, 0.45), 0.07, 0.12, P.red, n=10)
        for sx in (-1, 1):
            g.tube([(sx * 0.18, 0.35, 5.5), (sx * 2.4, 2.0, 0.05)], 0.01, P.iron, n=3)
            g.box((sx * 2.4, 2.0, 0.12), (0.06, 0.06, 0.24), P.wood)
        crest = [(-0.75, 0), (0.75, 0), (0.6, 0.45), (0.3, 0.75), (0, 0.85), (-0.3, 0.75), (-0.6, 0.45)]
        g.prism((0, 0.25, 6.55), crest, 0.1, P.mustard, rx=PI / 2)
        g.prism((0, 0.2, 6.55), [(px * 0.85, pz * 0.85 + 0.05) for px, pz in crest], 0.02, P.red, rx=PI / 2)
        cp.painted_letters(g, 'HIGH', (0, 0.17, 6.95), 0.03, P.cream)
        cp.painted_letters(g, 'STRIKER', (0, 0.17, 6.68), 0.026, P.cream)
        g.collide((0, 0.35, 3.4), (0.6, 0.4, 6.8))
    place(cp.striker_bell, 'bell', 'High Striker Bell', (x, y + 0.08, 6.35))
    place(cp.mallet, 'jolt', 'Striker Mallet', (x + 0.95, y - 0.5, 0.24), rz=-0.4)

    def striker_lights(p, P):
        parts = [p.geo('bulb0'), p.geo('bulb1')]
        for k in range(18):
            z = 0.6 + k * 0.33
            for j, sx in enumerate((-0.24, 0.24)):
                if (k * 7 + j * 3) % 11 == 0:
                    bulb(p.body, (sx, 0.24, z), P.bulb_dead, 0.04)
                else:
                    bulb(parts[(k + j) % 2], (sx, 0.24, z), P.bulb_red if k % 6 == 0 else P.bulb, 0.045)
        p.light((0, -1.2, 2.4), '#ffb45c', 1.2, 8.0, part='bulb0')
        p.params.setdefault('sound', 'buzz')
    place(striker_lights, 'flicker', 'High Striker Lights', (x, y, 0))


# ================================================================ funhouse (north-east)

def build_funhouse():
    x0, x1, y0, y1 = 17.0, 31.0, 24.0, 33.0
    H, ceil = 4.2, 3.4
    cx, cy = 24.0, 28.5
    g = S(cx, cy)
    g.box((cx, cy, 0.01), (x1 - x0, y1 - y0, 0.02), P.checker, col=False)
    ext, inn = P.boards_red, P.boards_indigo
    m.wall((x0, y0), (x1, y0), ext, h=H, openings=[(7.0, 2.4, 2.6, 0)], mat_back=inn)
    m.wall((x0, y1), (x1, y1), inn, h=H, mat_back=ext)
    m.wall((x0, y0), (x0, y1), inn, h=H, openings=[(6.75, 2.0, 2.5, 0)], mat_back=ext)
    m.wall((x1, y0), (x1, y1), ext, h=H, openings=[(2.4, 1.5, 2.4, 0)], mat_back=inn)
    m.wall((x0, 28.5), (x1, 28.5), inn, h=ceil, t=0.2, openings=[(5.5, 2.0, 2.5, 0), (11.5, 2.0, 2.5, 0)])
    m.wall((24.0, 28.5), (24.0, y1), inn, h=ceil, t=0.2, openings=[(2.5, 2.0, 2.5, 0)])
    g.box((cx, cy, ceil + 0.06), (x1 - x0, y1 - y0, 0.12), P.wood_dark, col=False)
    m.collider((x0, y0, ceil), (x1, y1, ceil + 0.12))
    g.box((cx, cy + 0.2, H + 0.08), (x1 - x0 + 0.5, y1 - y0 + 0.4, 0.16), P.red, bevel=0.03, col=False)
    # stripes on the exterior side walls
    for k in range(9):
        y = y0 + 0.5 + k * 1.0
        for x, sgn in ((x0 - 0.16, -1), (x1 + 0.16, 1)):
            if (x == x1 + 0.16 and 25.2 < y < 27.6) or (x == x0 - 0.16 and 29.6 < y < 31.9):
                continue
            g.box((x, y, 2.1), (0.02, 0.4, 4.2), P.mustard)
    for k in range(13):
        x = x0 + 0.5 + k * 1.0
        g.box((x, y1 + 0.16, 2.1), (0.4, 0.02, 4.2), P.mustard)
    # --- facade: false front, clown head, striped door arch
    fy = y0 - 0.16
    g.box((cx, fy + 0.05, 5.6), (11.0, 0.2, 2.8), P.boards_red, col=False)
    m.collider((cx - 5.5, y0 - 0.25, H), (cx + 5.5, y0 + 0.1, 7.0))
    for sx in (-1, 1):
        tx = cx + sx * 6.2
        for k in range(9):
            g.box((tx, fy, 0.4 + k * 0.8), (1.0, 1.0, 0.8), P.mustard if k % 2 else P.indigo, bevel=0.02)
        g.cyl((tx, fy, 7.2), 0.6, 1.3, P.red, n=8, r2=0.02, smooth=False)
        g.sphere((tx, fy, 8.55), 0.12, P.mustard, n=8)
        g.collide((tx, fy, 3.6), (1.0, 1.0, 7.2))
        for k in range(11):
            bulb(g, (tx - sx * 0.52, fy - 0.3, 0.5 + k * 0.6), P.bulb if (k + sx) % 4 else P.bulb_dead, 0.045)
    hz = 6.2
    g.cyl((cx, fy - 0.05, hz), 3.0, 0.25, P.cream, n=36, rx=PI / 2)
    for sx in (-1, 1):
        g.cyl((cx + sx * 1.8, fy - 0.31, hz - 0.6), 0.55, 0.02, P.red, n=20, rx=PI / 2)
        g.tube([(cx + sx * 0.5, fy - 0.33, hz + 1.55), (cx + sx * 1.1, fy - 0.33, hz + 1.85), (cx + sx * 1.7, fy - 0.33, hz + 1.6)],
               0.07, P.black, n=5)
        for k in range(5):
            a = PI / 2 + sx * (0.5 + k * 0.28)
            g.blob((cx + cos(a) * 3.1, fy - 0.15, hz + sin(a) * 2.8 - 0.4), 0.55, P.teal if k % 2 else P.red, seed=k + (sx > 0) * 9,
                   jitter=0.3, s=(1, 0.5, 1))
    smile = [(cos(PI + PI * i / 14) * 1.6, sin(PI + PI * i / 14) * 1.0) for i in range(15)]
    g.prism((cx, fy - 0.3, hz - 1.08), smile, 0.015, P.red, rx=PI / 2)
    for i in range(6):
        x = -0.7 + i * 0.28
        g.box((cx + x, fy - 0.335, hz - 1.17), (0.2, 0.03, 0.17), P.cream)
    cp.wedge_cone(g, (cx, fy - 0.1, hz + 2.75), 1.3, 0.0, 0.03, 1.7, [P.canvas_mustard, P.canvas_red], n=10, rows=1)
    g.sphere((cx, fy - 0.1, hz + 4.5), 0.25, P.cream, n=10)
    for k in range(14):
        a = PI + PI * k / 13
        g.add(cp.prim_pennant(0.55, 0.45, 3, 3, 'scallop'), P.canvas_cream if k % 2 else P.canvas_red,
              gh.X((cx + cos(a) * 3.1, fy - 0.3, hz + sin(a) * 2.3 - 0.4), rz=a + PI / 2))
    for k in range(9):
        ang = PI * k / 8
        bx, bz = cx + cos(ang) * 1.55, 1.15 + sin(ang) * 1.45
        g.box((bx, fy - 0.2, bz), (0.28, 0.25, 0.28), P.red if k % 2 else P.cream, bevel=0.02, rz=0)
        bulb(g, (bx, fy - 0.35, bz), P.bulb, 0.045)
    for sx in (-1, 1):
        g.box((cx + sx * 1.55, fy - 0.2, 0.58), (0.3, 0.3, 1.16), P.red, bevel=0.02)
    for k in range(10):
        bulb(g, (cx - 5.2 + k * 1.15, fy - 0.12, 7.1), P.bulb if k % 3 else P.bulb_red, 0.05)
    g.box((cx, fy - 0.38, 3.08), (3.3, 0.06, 0.52), P.mustard)
    g.box((cx, fy - 0.42, 3.08), (3.15, 0.03, 0.42), P.indigo)
    cp.painted_letters(g, 'FUNHOUSE', (cx, fy - 0.445, 2.93), 0.05, P.mustard)
    # props on the facade
    for sx in (-1, 1):
        place(cp.clown_eye, 'spin', 'Clown Eye', (cx + sx * 1.05, fy - 0.33, hz + 0.75), params={'speed': 0.6 * sx}, key='clown_eye')
    place(cp.clown_nose, 'flicker', 'Clown Nose', (cx, fy - 0.15, hz - 0.15), light=('#ff6a4a', 1.2, 8.0))
    place(cp.clown_jaw, 'hinge', 'Clown Jaw', (cx, fy - 0.3, hz - 1.15), w=2.4)
    # --- interior: mirror hall (south), clown room (NE), barrel room (NW)
    mirror_panel(g, (24.0, 26.7), True, 2.2)
    mirror_panel(g, (21.0, 25.6), False, 1.9)
    mirror_panel(g, (27.9, 25.5), False, 1.8)
    for (x, y, along_x) in ((18.6, 24.2, True), (21.8, 24.2, True), (26.2, 24.2, True), (29.4, 24.2, True),
                            (17.2, 26.3, False), (30.8, 25.0, False), (25.6, 28.35, True), (19.0, 28.35, True)):
        wall_mirror(g, (x, y), along_x)
    place(cp.fun_barrel, 'spin', 'Barrel of Fun', (19.05, 30.75, 1.33), length=3.7)
    m.collider((17.2, 30.75 - 1.48, 0), (20.9, 30.75 - 1.02, 2.8))
    m.collider((17.2, 30.75 + 1.02, 0), (20.9, 30.75 + 1.48, 2.8))
    g.box((19.05, 30.75 - 1.52, 0.4), (3.7, 0.1, 0.8), P.wood_dark)
    g.box((19.05, 30.75 + 1.52, 0.4), (3.7, 0.1, 0.8), P.wood_dark)
    place(cp.jack_in_box, 'bob', 'Jack-in-the-Box', (29.6, 31.6, 0), rz=face_rz(-1, -1))
    place(mirror_ball, 'spin', 'Mirror Ball', (27.6, 30.8, ceil))
    for k in range(9):
        bulb(g, (24.6 + k * 0.75, 32.62, 3.05 - 0.2 * sin(PI * k / 8)), P.bulb_red if k % 3 == 0 else P.bulb, 0.04)
    door_prop((x1, 26.4), PI / 2, 'Funhouse Exit Door', hinge='right', w=1.5, h=2.35, rest=1.1, wood=P.boards_red)
    # creepy clown room set dressing
    g.box((30.3, 29.4, 0.5), (0.8, 0.8, 1.0), P.boards_teal, bevel=0.02)
    g.collide((30.3, 29.4, 0.5), (0.8, 0.8, 1.0))
    g.sphere((30.3, 29.4, 1.35), 0.3, P.cream, n=12)
    g.sphere((30.05, 29.2, 1.33), 0.07, P.bulb_red, n=8)
    for sx in (-1, 1):
        g.sphere((30.3 + sx * 0.28, 29.4, 1.42), 0.14, P.red, n=8)
    g.lathe((30.3, 29.4, 1.6), [(0.2, 0), (0.001, 0.4)], P.teal, n=10)
    for k in range(6):
        bulb(g, (24.4 + k * 1.1, 28.62, 3.1), P.bulb if k % 2 else P.bulb_red, 0.04)
    for k in range(5):
        bulb(g, (17.6 + k * 1.2, 24.42, 3.1), P.bulb if k != 2 else P.bulb_dead, 0.04)
    # painted zig-zag dado and arrow signs
    for (xa, ya, xb, yb, nx, ny) in ((17.16, 24.2, 17.16, 28.4, 1, 0), (30.84, 24.2, 30.84, 28.4, -1, 0),
                                     (17.2, 24.16, 30.8, 24.16, 0, 1), (17.2, 28.38, 30.8, 28.38, 0, -1),
                                     (24.12, 28.6, 24.12, 32.84, 1, 0), (30.84, 28.6, 30.84, 32.84, -1, 0)):
        L = math.dist((xa, ya), (xb, yb))
        n = int(L / 0.6)
        step = L / n
        ang = math.atan2(yb - ya, xb - xa)
        for k in range(n):
            t = (k + 0.5) / n
            x, y = xa + (xb - xa) * t, ya + (yb - ya) * t
            g.box((x + nx * 0.006, y + ny * 0.006, 0.85), (step / cos(0.45) + 0.02, 0.01, 0.09), P.mustard if k % 2 else P.red,
                  rz=ang, ry=0.45 if k % 2 else -0.45)

    def arrow_sign(pos, rz, left=True, rods=True):
        with g.at(pos, rz=rz):
            g.box((0, -0.03, 0), (0.8, 0.03, 0.3), P.cream)
            g.box((0, -0.02, 0), (0.86, 0.02, 0.36), P.red)
            sx = -1 if left else 1
            tri = [(sx * 0.46, -0.16), (sx * 0.7, 0.0), (sx * 0.46, 0.16)]
            if sx < 0:
                tri = tri[::-1]
            g.prism((0, -0.03, 0), tri, 0.02, P.red, rx=PI / 2)
            cp.painted_letters(g, 'THIS WAY', (0, -0.047, -0.055), 0.015, P.red)
            if rods:
                for x in (-0.3, 0.3):
                    g.cyl((x, -0.03, 0.15), 0.008, 3.4 - pos[2] - 0.15, P.iron, n=4, caps=False)
    arrow_sign((24.0, 26.55, 2.92), 0.0, left=True)
    arrow_sign((27.6, 32.82, 2.2), 0.0, left=True, rods=False)
    m.light((24.0, 26.0, 3.0), '#ffb070', 0.9, 8.0)


def mirror_panel(g, c, along_x, ln):
    sx, sy = (ln, 0.12) if along_x else (0.12, ln)
    g.box((c[0], c[1], 1.25), (sx, sy, 2.5), P.wood_dark)
    g.box((c[0], c[1], 1.3), (sx - 0.2 if along_x else 0.16, 0.16 if along_x else sy - 0.2, 2.1), P.mirror)
    g.box((c[0], c[1], 2.55), (sx + 0.08, sy + 0.08, 0.1), P.mustard)
    g.collide((c[0], c[1], 1.3), (sx, sy, 2.6))


def wall_mirror(g, c, along_x):
    w = 1.2
    if along_x:
        g.box((c[0], c[1], 1.5), (w, 0.04, 2.0), P.mirror)
        g.box((c[0], c[1], 1.5), (w + 0.12, 0.03, 2.12), P.mustard)
    else:
        g.box((c[0], c[1], 1.5), (0.04, w, 2.0), P.mirror)
        g.box((c[0], c[1], 1.5), (0.03, w + 0.12, 2.12), P.mustard)


def mirror_ball(p, P):
    p.body.cyl((0, 0, -0.5), 0.008, 0.5, P.iron, n=4)
    pv = p.part('pivot', (0, 0, -0.5))
    g = pv.geo
    g.add(gh.prim_ico(0.32, 2, 0.0, 0), P.mirror, gh.X((0, 0, -0.32)))
    p.params.setdefault('axis', 'y')
    p.params.setdefault('speed', 0.4)
    p.params.setdefault('sound', 'whirr')


def door_prop(c, rz, label, hinge='left', w=1.3, h=2.3, z=0.0, rest=0.0, wood=None):
    m.place(pf.door, 'hinge', label, (c[0], c[1], z), rz=rz, w=w, h=h, wood=wood or P.boards_teal, frame=P.mustard, panel=P.teal,
            handle=P.brass, hinge=hinge, rest=rest)


def tree_prop(p, P, h=7.0, crown=2.4, seed=0, style='round'):
    pf.tree(p, P.bark, P.leaf, h=h, crown=crown, seed=seed, style=style)


# ================================================================ caravans and wagons

def caravan(g, body, trim, roof=None, length=4.6, width=2.2, floor=0.85, wall=1.9, door='static', lit=True, seed=0,
            awning=None):
    """Living wagon, long axis local X, door end at +X (porch and steps)."""
    hl, hw = length / 2, width / 2
    roof = roof or P.wood_dark
    top = floor + wall
    g.box((0, 0, floor - 0.1), (length - 0.2, width - 0.3, 0.2), P.wood_dark)
    g.box((0, 0, floor + wall / 2), (length, width, wall), body, bevel=0.03)
    g.box((0, 0, floor + 0.05), (length + 0.06, width + 0.06, 0.1), trim, bevel=0.01)
    g.box((0, 0, top - 0.05), (length + 0.06, width + 0.06, 0.1), trim, bevel=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box((sx * (hl - 0.02), sy * (hw - 0.02), floor + wall / 2), (0.1, 0.1, wall), trim, bevel=0.01)
    for sx, r in ((1, 0.45), (-1, 0.64)):
        for sy in (-1, 1):
            cp.spoked_wheel(g, P, (sx * (hl - 0.8), sy * (hw + 0.1), r), r, spokes=12, rim=P.red if seed % 2 else P.wood_dark, spoke=trim)
        g.cyl((sx * (hl - 0.8), -hw - 0.2, r), 0.05, width + 0.4, P.iron, n=6, rx=-PI / 2)
    # bowed roof of slats
    n = 9
    rise = 0.55
    span = hw + 0.18
    Rr = (span * span + rise * rise) / (2 * rise)
    phimax = math.asin(span / Rr)
    for i in range(n):
        phi = -phimax + 2 * phimax * (i + 0.5) / n
        y = Rr * sin(phi)
        z = top + Rr * cos(phi) - Rr * cos(phimax)
        g.box((0.15, y, z), (length + 0.5, 2 * Rr * sin(phimax / n) + 0.02, 0.06), roof, rx=-phi)
    for sx in (-1, 1):
        poly = [(Rr * sin(-phimax + 2 * phimax * j / 10), top + Rr * cos(-phimax + 2 * phimax * j / 10) - Rr * cos(phimax)) for j in range(11)]
        pts = [(-(z - top), y) for y, z in poly]
        g.prism((sx * hl, 0, top), [(y, z - top) for y, z in poly], 0.06, trim, rx=PI / 2, rz=PI / 2)
    g.cyl((-hl + 0.8, 0.4, top + 0.3), 0.07, 0.9, P.iron, n=8)
    g.lathe((-hl + 0.8, 0.4, top + 1.2), [(0.12, 0), (0.08, 0.1)], P.iron, n=8)
    # windows on both long sides
    for sy in (-1, 1):
        for wx in (-0.9, 0.7):
            y = sy * (hw + 0.02)
            g.box((wx, y, floor + 1.15), (0.75, 0.05, 0.7), trim, bevel=0.01)
            g.box((wx, y + sy * 0.01, floor + 1.15), (0.6, 0.04, 0.55), P.window if lit and (wx > 0) == (sy > 0) else P.glass)
            g.box((wx, y + sy * 0.015, floor + 1.15), (0.04, 0.04, 0.55), trim)
            for sxs in (-1, 1):
                g.box((wx + sxs * 0.55, y + sy * 0.02, floor + 1.15), (0.34, 0.04, 0.7), P.teal if seed % 2 else P.red, bevel=0.01)
            g.box((wx, y + sy * 0.06, floor + 0.78), (0.85, 0.12, 0.05), trim)
            for k in range(3):
                bulb(g, (wx - 0.24 + k * 0.24, y + sy * 0.09, floor + 0.86), P.leaf[k % 2], 0.09)
                bulb(g, (wx - 0.12 + k * 0.24, y + sy * 0.1, floor + 0.93), P.red if k != 1 else P.cream, 0.035)
    # porch, door and steps at +X
    g.box((hl + 0.35, 0, floor - 0.05), (0.7, width - 0.2, 0.1), P.planks)
    for sy in (-1, 1):
        g.cyl((hl + 0.65, sy * (hw - 0.15), floor), 0.03, 0.8, trim, n=6)
        g.box((hl + 0.35, sy * (hw - 0.15), floor + 0.75), (0.7, 0.05, 0.05), trim)
    for k, (zt, x) in enumerate(((0.57, hl + 0.85), (0.29, hl + 1.15))):
        g.box((x, 0, zt / 2), (0.3, 1.0, zt), P.wood, bevel=0.01)
        g.collide((x, 0, zt / 2), (0.3, 1.0, zt))
    g.collide((hl + 0.35, 0, floor / 2), (0.7, width - 0.2, floor))
    if door == 'static':
        g.box((hl + 0.02, 0, floor + 0.85), (0.06, 0.78, 1.7), trim, bevel=0.01)
        g.box((hl + 0.04, 0, floor + 0.85), (0.04, 0.66, 1.58), P.boards_cream)
        g.sphere((hl + 0.07, -0.22, floor + 0.85), 0.03, P.brass, n=6)
    elif door == 'open':
        g.box((hl + 0.01, 0, floor + 0.85), (0.02, 0.78, 1.7), P.black)
    for sy in (-1, 1):
        g.tube([(hl - 0.8, sy * 0.55, 0.45), (hl + 1.6, sy * 0.6, 0.35), (hl + 2.6, sy * 0.62, 0.04)], 0.04, P.wood, n=5)
    g.collide((0, 0, (top + 0.3) / 2), (length, width, top + 0.3))
    if awning:
        side, mats = awning
        aw = 2.2
        for i in range(8):
            x = -hl + 0.3 + (length - 0.6) * (i + 0.5) / 8
            g.box((x, side * (hw + aw / 2), top - 0.35), ((length - 0.6) / 8 + 0.005, aw + 0.1, 0.03), mats[i % 2], rx=-side * 0.22)
        for x in (-hl + 0.4, hl - 0.4):
            g.cyl((x, side * (hw + aw), 0), 0.045, top - 0.6, P.wood_dark, n=6)
            g.collide((x, side * (hw + aw), (top - 0.6) / 2), (0.15, 0.15, top - 0.6))
        for i in range(10):
            x = -hl + 0.3 + (length - 0.6) * (i + 0.5) / 10
            g.add(cp.prim_pennant((length - 0.6) / 10, 0.3, 3, 3, 'scallop'), mats[(i + 1) % 2],
                  gh.X((x, side * (hw + aw + 0.03), top - 0.6)))


def wagon_place(c, rz, **kw):
    g = S(*c)
    with g.at((c[0], c[1], 0), rz):
        caravan(g, **kw)


def build_back_lot():
    # caravan circle (NW)
    wagon_place((-30.0, 12.5), 0.0, body=P.boards_red, trim=P.mustard, roof=P.canvas_teal, door='open', seed=1)
    door_prop(W((-30.0, 12.5), 0.0, (2.33, 0.0)), PI / 2, 'Caravan Door', hinge='left', w=0.78, h=1.7, z=0.85, rest=0.6,
              wood=P.boards_cream)
    wagon_place((-31.0, 26.5), -0.25, body=P.boards_teal, trim=P.cream, roof=P.wood_dark, seed=2)
    wagon_place((-21.0, 31.6), -PI / 2 + 0.2, body=P.boards_cream, trim=P.red, roof=P.canvas_red, door='static', seed=3, lit=False)
    place(cp.campfire, 'flame', 'Campfire', (-23.5, 21.5, 0))
    gc = S(-23.5, 21.5)
    for k, a in enumerate((0.3, 2.0, 3.9, 5.2)):
        x, y = -23.5 + cos(a) * 2.4, 21.5 + sin(a) * 2.4
        with gc.at((x, y, 0), rz=a + PI / 2):
            gc.cyl((-0.8, 0, 0.22), 0.22, 1.6, P.wood, n=8, ry=PI / 2)
            gc.collide((0, 0, 0.22), (1.6, 0.44, 0.44))
    place(lambda p, P: pf.rocking_chair(p, P.wood, P.red), 'rock', 'Rocking Chair', (-26.2, 15.0, 0), rz=face_rz(0.6, 1))
    place(cp.laundry_line, 'cloth', 'Laundry Line', (-26.0, 30.0, 0), rz=0.4, length=5.2, h=2.0,
          items=[(0.15, 0.6, 0.75, P.canvas_cream), (0.32, 0.5, 0.9, P.canvas_teal), (0.5, 0.9, 1.1, P.velvet),
                 (0.7, 0.45, 0.6, P.canvas_red), (0.86, 0.55, 0.8, P.canvas_mustard)])
    place(cp.laundry_line, 'cloth', 'Costume Line', (-34.0, 16.2, 0), rz=PI / 2, length=4.4, h=2.1,
          items=[(0.2, 0.7, 1.2, P.canvas_red), (0.45, 0.6, 0.9, P.canvas_cream), (0.75, 0.8, 1.3, P.canvas_teal)])
    place(cp.gramophone, 'music', 'Gramophone', W((-31.0, 26.5), -0.25, (2.6, 0.2, 0.85)), rz=-0.25 + PI / 2)
    # strongman corner
    place(cp.barbell, 'jolt', "Strongman's Barbell", (-14.5, 13.2, 0), rz=0.3)
    gs = S(-14, 14)
    for i, (x, y, r) in enumerate(((-15.8, 12.0, 0.17), (-15.4, 11.6, 0.13), (-13.2, 12.4, 0.2))):
        gs.sphere((x, y, r), r, P.black, n=10)
        gs.torus((x, y, r * 2.1), r * 0.5, 0.02, P.iron, n=10, m=3, rx=PI / 2)
    with gs.at((-13.6, 15.2, 0), rz=0.2):
        gs.box((0, 0, 0.45), (1.8, 0.5, 0.06), P.planks)
        for sx in (-1, 1):
            gs.box((sx * 0.75, 0, 0.22), (0.1, 0.45, 0.45), P.iron)
        gs.collide((0, 0, 0.24), (1.8, 0.5, 0.48))
    with gs.at((-12.6, 11.2, 0), rz=face_rz(0.4, -1)):
        gs.box((0, 0, 1.4), (1.4, 0.08, 1.9), P.canvas_mustard)
        for sx in (-1, 1):
            gs.box((sx * 0.72, 0, 1.2), (0.08, 0.08, 2.4), P.wood_dark)
        gs.collide((0, 0, 1.2), (1.6, 0.2, 2.4))
        cp.painted_letters(gs, 'STRONGMAN', (0, -0.05, 2.1), 0.024, P.red)
        gs.sphere((0, -0.06, 1.35), 1.0, P.red, n=10, s=(0.25, 0.02, 0.35))
        gs.sphere((0, -0.07, 1.8), 0.13, P.cream, n=10)
        for sx in (-1, 1):
            gs.tube([(sx * 0.2, -0.07, 1.6), (sx * 0.42, -0.07, 1.75), (sx * 0.5, -0.07, 1.95)], 0.05, P.cream, n=4)
            gs.sphere((sx * 0.5, -0.07, 2.05), 0.1, P.black, n=8)
    # crates, barrels, hay
    gb = S(-28, 20)
    cp.crate_static(gb, P, 0.8, 0.2, (-33.6, 9.5, 0))
    cp.crate_static(gb, P, 0.6, 0.7, (-33.4, 10.5, 0))
    cp.crate_static(gb, P, 0.6, 0.1, (-33.6, 9.5, 0.8))
    cp.barrel_static(gb, P, (-27.4, 10.6, 0))
    cp.barrel_static(gb, P, (-26.8, 11.2, 0), tipped=True)
    cp.hay_bale(gb, P, (-17.5, 26.0, 0), rz=0.3)
    cp.hay_bale(gb, P, (-17.0, 25.0, 0), rz=-0.2)
    cp.hay_bale(gb, P, (-17.3, 25.5, 0.42), rz=0.1)
    cp.hay_bale(gb, P, (-34.2, 31.5, 0), rz=PI / 2)
    place(lambda p, P: pf.crate(p, P.wood, P.wood_dark, s=0.7), 'jolt', 'Crate', (-26.0, 31.0, 0), rz=0.3, key='crate')
    place(lambda p, P: pf.barrel(p, P.wood, P.iron), 'jolt', 'Water Barrel', (-18.0, 21.0, 0), key='barrel')
    cp.lamp_static(S(-18, 18), P, (-18.4, 18.0, 0), lit=True)
    # trees in the back lot
    cp.tree_static(S(-34.2, 4.0), P, (-34.2, 4.0, 0), h=6.5, crown=2.0, seed=23)
    for i, (x, y, h, cr) in enumerate(((-34.0, 34.0, 8.0, 2.6), (-13.0, 33.8, 7.0, 2.2))):
        place(tree_prop, 'foliage', 'Elm Tree', (x, y, 0), params={'leaf': '#4a4a2a'}, h=h, crown=cr, seed=i + 3)


def build_menagerie_pen(c=(-19.5, 9.4)):
    """An empty animal pen with a trough and an open gate: whatever lived here is gone."""
    g = S(*c)
    x0, y0 = c
    hx, hy = 1.9, 1.5
    with g.at((x0, y0, 0)):
        posts = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
        for i in range(4):
            a, b = posts[i], posts[(i + 1) % 4]
            if i == 0:   # south side: gate gap
                segs = [(a, (-0.6, -hy)), ((0.8, -hy), b)]
            else:
                segs = [(a, b)]
            for p0, p1 in segs:
                L = math.dist(p0, p1)
                ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
                n = max(1, round(L / 1.0))
                for k in range(n + 1):
                    t = k / n
                    g.box((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t, 0.55), (0.1, 0.1, 1.1), P.wood_dark)
                for z in (0.45, 0.9):
                    g.box(((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, z), (L, 0.05, 0.1), P.wood, rz=ang)
                seg_col(g, p0, p1, 0.2, 0.0, 1.1, step=1.2)
        with g.at((-0.6, -hy, 0), rz=-1.1):
            g.box((0.7, 0, 0.45), (1.35, 0.05, 0.1), P.wood)
            g.box((0.7, 0, 0.9), (1.35, 0.05, 0.1), P.wood)
            g.box((1.35, 0, 0.55), (0.08, 0.08, 1.0), P.wood_dark)
            g.box((0.7, 0, 0.67), (1.4, 0.04, 0.08), P.wood, ry=0.33)
        g.box((0.6, 1.0, 0.25), (1.6, 0.5, 0.5), P.wood, bevel=0.02)
        g.box((0.6, 1.0, 0.47), (1.45, 0.38, 0.04), P.puddle)
        g.collide((0.6, 1.0, 0.25), (1.6, 0.5, 0.5))
        for k in range(6):
            soft = cp.soft_blob
            soft(g, (-1.0 + k * 0.32, -0.3 + (k % 2) * 0.5, 0.05), 0.32, P.hay, seed=k, jitter=0.3, s=(1, 1, 0.22))
        g.lathe((-1.2, 0.9, 0), [(0.15, 0), (0.18, 0.3)], P.iron, n=10, cap_top=False)
        g.torus((-1.2, 0.9, 0.3), 0.18, 0.012, P.iron, n=10, m=3)
        g.cyl((1.5, -0.6, 0.06), 0.06, 0.6, P.wood, n=5, rx=PI / 2 - 0.3, rz=0.7)
    with g.at((x0 + 2.6, y0 - 1.2, 0), rz=face_rz(0.3, -1)):
        g.box((0, 0, 0.65), (0.06, 0.06, 1.3), P.wood_dark)
        g.box((0, -0.04, 1.35), (0.75, 0.03, 0.42), P.cream, rz=0.05)
        cp.painted_letters(g, 'DO NOT FEED', (0, -0.06, 1.24), 0.0145, P.red)
        g.collide((0, 0, 0.65), (0.2, 0.2, 1.3))


def build_canvas_wagon(c=(-27.6, -12.6), rz=0.12):
    """Flatbed loaded with rolled tent canvas and poles: the show was being packed away."""
    g = S(*c)
    with g.at((c[0], c[1], 0), rz):
        g.box((0, 0, 0.85), (4.4, 2.0, 0.16), P.planks, bevel=0.02)
        g.box((0, 0, 0.65), (3.8, 1.6, 0.25), P.wood_dark)
        for sx in (-1, 1):
            for sy in (-1, 1):
                cp.spoked_wheel(g, P, (sx * 1.45, sy * 1.08, 0.5), 0.5, spokes=10, rim=P.wood_dark, spoke=P.teal)
            g.cyl((sx * 1.45, -1.25, 0.5), 0.045, 2.5, P.iron, n=6, rx=-PI / 2)
        for sy in (-1, 1):
            for k in range(5):
                g.box((-1.8 + k * 0.9, sy * 0.98, 1.15), (0.06, 0.06, 0.45), P.wood_dark)
            g.box((0, sy * 0.98, 1.35), (4.3, 0.05, 0.06), P.wood)
        for k, (mat, y, z, r) in enumerate(((P.canvas_red, -0.5, 1.2, 0.27), (P.canvas_cream, 0.05, 1.2, 0.27),
                                            (P.canvas_red, 0.58, 1.2, 0.25), (P.canvas_cream, -0.22, 1.66, 0.25),
                                            (P.canvas_red, 0.33, 1.66, 0.24))):
            g.cyl((-1.9, y, z), r, 3.6, mat, n=10, ry=PI / 2)
            for x in (-1.2, 0.6):
                g.torus((x, y, z), r + 0.01, 0.015, P.rope, n=10, m=3, ry=PI / 2)
        for k in range(4):
            g.cyl((-2.4, -0.7 + k * 0.45, 2.02), 0.07, 5.0, P.cream if k % 2 else P.red, n=6, ry=PI / 2)
        g.tube([(2.2, -0.6, 0.6), (3.4, -0.65, 0.3), (4.4, -0.7, 0.03)], 0.045, P.wood, n=5)
        g.tube([(2.2, 0.6, 0.6), (3.4, 0.65, 0.3), (4.4, 0.7, 0.03)], 0.045, P.wood, n=5)
        g.collide((0, 0, 0.75), (4.4, 2.0, 1.5))
        g.collide((0, 0, 1.8), (4.4, 1.6, 0.6))
    place(cp.tarp_sheet, 'cloth', 'Canvas Tarp', W((c[0], c[1], 0), rz, (0.3, -1.03, 1.9)), rz, w=2.6, h=1.1, mat=P.canvas_cream)


def build_retired_horses(c=(-9.4, 14.2)):
    """Two carousel horses taken off their poles, waiting for repairs that never came."""
    g = S(*c)
    with g.at((c[0], c[1], 0.21), rz=0.5, rx=PI / 2 - 0.05):
        cp.horse_geo(g, P, P.cream, P.red, P.mustard)
    with g.at((c[0] + 1.3, c[1] + 1.1, 0.21), rz=2.3, rx=-PI / 2 + 0.05):
        cp.horse_geo(g, P, P.teal, P.mustard, P.cream)
    g.collide((c[0] + 0.6, c[1] + 0.5, 0.35), (3.0, 2.6, 0.7))
    cp.crate_static(g, P, 0.6, 0.3, (c[0] + 2.6, c[1] - 0.4, 0))
    g.cyl((c[0] - 1.5, c[1] - 0.8, 0.04), 0.035, 2.3, P.brass, n=6, ry=PI / 2 - 0.02, rz=0.3)
    g.cyl((c[0] - 1.1, c[1] + 1.6, 0.04), 0.035, 1.6, P.brass, n=6, ry=PI / 2 - 0.02, rz=-0.6)
    cp.barrel_static(g, P, (c[0] - 1.9, c[1] + 0.9, 0), mat=P.red)
    place(cp.rocking_horse, 'rock', 'Rocking Horse', (c[0] + 3.0, c[1] + 2.4, 0), rz=-0.7)
    place(cp.balloons, 'bob', 'Balloon Bunch', (3.2, 16.8, 0), n=5, seed=9, post_mat=P.mustard)
    build_kiosk((3.4, 21.2), roof=[P.canvas_teal, P.canvas_cream], body=P.boards_teal, label='RIDE TICKETS')
    for i, (x, y, h, cr, st) in enumerate(((9.2, 15.4, 6.5, 2.1, 'round'), (14.6, 17.6, 7.5, 1.9, 'pine'), (-12.6, 18.6, 7.0, 2.2, 'round'),
                                           (6.4, -27.0, 6.0, 1.9, 'round'))):
        cp.tree_static(S(x, y), P, (x, y, 0), h=h, crown=cr, seed=60 + i, style=st)
        m.collider((x - 0.3, y - 0.3, 0), (x + 0.3, y + 0.3, h * 0.5))


def build_sw():
    # fortune teller's vardo with side awning, tarot table, beaded curtain
    c, rz = (-22.0, -23.5), 0.0
    wagon_place(c, rz, body=P.boards_indigo, trim=P.mustard, roof=P.canvas_red, door='open', seed=5,
                awning=(1, [P.velvet, P.canvas_mustard]))
    place(cp.bead_curtain, 'cloth', 'Beaded Curtain', W(c, rz, (2.36, 0.0, 0.85 + 1.72)), rz + PI / 2, w=0.78, h=1.65)
    gt = S(-22, -20)
    tx, ty = -21.6, -20.6
    gt.cyl((tx, ty, 0), 0.08, 0.72, P.wood_dark, n=8)
    gt.cyl((tx, ty, 0), 0.35, 0.04, P.wood_dark, n=10)
    gt.cyl((tx, ty, 0.72), 0.6, 0.04, P.wood, n=16)
    gt.lathe((tx, ty, 0.35), [(0.66, 0), (0.62, 0.4), (0.62, 0.42)], P.velvet, n=16, cap_bottom=False, cap_top=False)
    gt.cyl((tx, ty, 0.76), 0.62, 0.012, P.velvet, n=16)
    gt.collide((tx, ty, 0.38), (1.2, 1.2, 0.76))
    for k in range(5):
        a = -0.6 + k * 0.3
        gt.box((tx + cos(a) * 0.35, ty + sin(a) * 0.35 - 0.1, 0.778), (0.07, 0.11, 0.004), P.cream if k != 2 else P.red, rz=a)
        gt.box((tx + cos(a) * 0.35, ty + sin(a) * 0.35 - 0.1, 0.776), (0.075, 0.115, 0.003), P.mustard, rz=a)
    for k in range(3):
        gt.box((tx - 0.3 + k * 0.012, ty + 0.3, 0.78 + k * 0.004), (0.07, 0.11, 0.004), P.red, rz=0.1 * k)
    for k, (dx, dy) in enumerate(((0.95, 0.0), (-0.95, 0.1), (0.0, 0.95))):
        with gt.at((tx + dx, ty + dy, 0), rz=face_rz(-dx, -dy)):
            gt.box((0, 0, 0.45), (0.45, 0.45, 0.05), P.velvet)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    gt.cyl((sx * 0.18, sy * 0.18, 0), 0.02, 0.45, P.wood_dark, n=4)
            gt.box((0, 0.22, 0.8), (0.45, 0.04, 0.65), P.wood_dark, rx=-0.1)
            gt.collide((0, 0, 0.45), (0.5, 0.5, 0.9))
    place(cp.crystal_ball, 'flicker', 'Crystal Ball', (tx, ty, 0.76))
    place(cp.candle_cluster, 'flame', 'Tarot Candles', (tx + 0.35, ty + 0.25, 0.76), n=3, seed=2)
    place(cp.wind_chime, 'swing', 'Wind Chime', W(c, rz, (-1.6, 3.05, 2.19)), rz)
    place(cp.hanging_lantern, 'swing', 'Awning Lantern', W(c, rz, (1.2, 3.2, 2.2)), rz, drop=0.35, light=('#ffaa55', 1.0, 7.0))
    place(cp.hanging_sign, 'swing', 'Fortune Sign', (-17.6, -18.3, 2.6), rz=face_rz(1, 0.8))
    gt.cyl((-17.6 - 0.0, -18.3, 0), 0.07, 2.75, P.wood_dark, n=6)
    gt.collide((-17.6, -18.3, 1.35), (0.2, 0.2, 2.7))
    # calliope bandwagon
    build_bandwagon((-10.5, -15.0), face_rz(0.6, 0.8))
    # picnic area
    gp = S(-13, -27)
    cp.picnic_table(gp, P, (-13.5, -26.5, 0), rz=0.3)
    cp.picnic_table(gp, P, (-8.5, -29.0, 0), rz=-0.2)
    place(lambda p, P: pf.chair(p, P.wood, P.red), 'jolt', 'Toppled Chair', (-11.2, -24.6, 0), rz=1.2)
    cp.popcorn_box(gp, P, (-13.2, -26.6, 0.77), rz=0.4)
    cp.popcorn_box(gp, P, (-8.1, -29.2, 0.77), rz=2.4, tipped=True)
    wagon_place((-33.3, -26.2), PI / 2, body=P.boards_teal, trim=P.mustard, roof=P.canvas_cream, seed=6, lit=False)
    cp.hay_bale(gp, P, (-26.6, -30.0, 0), rz=0.2)
    cp.hay_bale(gp, P, (-26.0, -31.0, 0), rz=-0.1)
    place(lambda p, P: pf.barrel(p, P.wood, P.iron), 'jolt', 'Rain Barrel', (-34.5, -19.6, 0), key='barrel')
    cp.crate_static(gp, P, 0.6, 0.2, (-29.2, -33.9, 0))
    place(cp.cymbal_monkey, 'music', 'Cymbal Monkey', (-29.2, -33.9, 0.6), rz=face_rz(0.6, 1))
    cp.crate_static(gp, P, 0.7, 0.4, (-34.3, -18.4, 0))
    cp.lamp_static(S(-16, -24), P, (-16.0, -24.5, 0), lit=True)
    place(lambda p, P: pf.tree(p, P.bark, P.leaf, h=7.5, crown=2.4, seed=11), 'foliage', 'Old Oak', (-34.0, -13.5, 0),
          params={'leaf': '#4a4a2a'})
    place(lambda p, P: pf.tree(p, P.bark, P.leaf, h=6.0, crown=0.1, seed=12, style='bare'), 'foliage', 'Dead Tree', (-5.5, -33.5, 0),
          params={'leaf': '#5a4a2a'})


def build_bandwagon(c, rz):
    g = S(*c)
    with g.at((c[0], c[1], 0), rz):
        g.box((0, 0, 0.78), (3.4, 2.2, 0.44), P.boards_red, bevel=0.03)
        g.box((0, 0, 1.02), (3.5, 2.3, 0.06), P.mustard, bevel=0.01)
        g.box((0, 0, 0.55), (3.0, 1.8, 0.1), P.wood_dark)
        for sx in (-1, 1):
            for sy in (-1, 1):
                cp.spoked_wheel(g, P, (sx * 1.15, sy * 1.22, 0.52), 0.52, spokes=12, rim=P.mustard, spoke=P.red)
                g.cyl((sx * 1.6, sy * 1.0, 1.05), 0.05, 2.4, P.brass, n=8)
        for sy in (-1, 1):
            g.box((0, sy * 1.12, 0.78), (3.0, 0.04, 0.3), P.mustard)
            for k in range(5):
                g.sphere((-1.2 + k * 0.6, sy * 1.15, 0.78), 0.07, P.cream, n=8)
        g.box((0, 0, 3.5), (3.6, 2.4, 0.1), P.wood_dark)
        cp.wedge_cone(g, (0, 0, 3.55), 2.1, 0.0, 0.05, 0.6, [P.canvas_red, P.canvas_cream], n=14, rows=2)
        for k in range(16):
            x = -1.7 + k * 3.4 / 15
            for sy in (-1, 1):
                g.add(cp.prim_pennant(0.24, 0.25, 3, 3, 'scallop'), P.canvas_mustard if k % 2 else P.canvas_red,
                      gh.X((x, sy * 1.21, 3.45)))
        for k in range(8):
            a = k * TAU / 8
            bulb(g, (cos(a) * 1.4, sin(a) * 1.0, 3.42), P.bulb if k % 3 else P.bulb_dead, 0.045)
        g.collide((0, 0, 0.53), (3.4, 2.2, 1.06))
        for sx in (-1, 1):
            for sy in (-1, 1):
                g.collide((sx * 1.6, sy * 1.0, 2.2), (0.15, 0.15, 2.4))
        g.box((1.95, 0, 0.32), (0.4, 1.0, 0.64), P.wood, bevel=0.01)
        g.collide((1.95, 0, 0.32), (0.4, 1.0, 0.64))
    place(cp.calliope, 'music', 'Steam Calliope', W((c[0], c[1], 0), rz, (0.0, -0.1, 1.05)), rz)
    m.light(W((c[0], c[1], 0), rz, (0.0, -1.6, 2.9)), '#ffb060', 1.1, 8.0)


def build_east_alley():
    # parked trailers along the east hoarding
    g = S(33, -8)
    with g.at((33.6, -8.0, 0), PI / 2):
        g.box((0, 0, 1.75), (7.5, 2.6, 2.7), P.boards_cream, bevel=0.03)
        g.box((0, 0, 3.15), (7.6, 2.7, 0.12), P.red)
        for sx in (-1, 1):
            for x in (-2.6, 2.6):
                cp.spoked_wheel(g, P, (x, sx * 1.4, 0.45), 0.45, spokes=10, rim=P.wood_dark, spoke=P.red)
        g.box((0, -1.32, 1.9), (5.0, 0.02, 0.8), P.red)
        cp.painted_letters(g, 'PRIZES', (0, -1.34, 1.6), 0.07, P.cream)
        g.box((3.76, 0, 1.6), (0.04, 2.2, 2.2), P.boards_red)
        g.collide((0, 0, 1.6), (7.5, 2.6, 3.2))
    g2 = S(33, 6)
    with g2.at((33.4, 6.0, 0), PI / 2):
        g2.box((0, 0, 0.7), (3.4, 2.0, 0.3), P.wood_dark)
        for sx in (-1, 1):
            cp.spoked_wheel(g2, P, (sx * 1.1, -1.1, 0.5), 0.5, spokes=10)
            cp.spoked_wheel(g2, P, (sx * 1.1, 1.1, 0.5), 0.5, spokes=10)
        g2.box((-0.3, 0, 1.45), (2.2, 1.6, 1.2), P.iron, bevel=0.04)
        for k in range(8):
            g2.box((-1.0 + k * 0.2, -0.81, 1.5), (0.06, 0.02, 0.9), P.wood_dark)
        g2.cyl((0.4, 0.4, 2.05), 0.1, 1.1, P.iron, n=8)
        g2.lathe((0.4, 0.4, 3.15), [(0.14, 0), (0.06, 0.15)], P.iron, n=8)
        g2.cyl((1.15, 0, 0.85), 0.35, 0.9, P.red, n=12)
        g2.box((-0.3, -0.84, 1.8), (0.4, 0.04, 0.3), P.mustard)
        g2.collide((0, 0, 1.2), (3.4, 2.2, 2.4))
    gg = S(30, -10)
    place(cp.fire_barrel, 'flame', 'Fire Barrel', (30.4, -18.0, 0))
    place(lambda p, P: pf.crate(p, P.wood, P.wood_dark, s=0.7), 'jolt', 'Crate', (34.2, -14.6, 0), rz=0.15, key='crate')
    cp.crate_static(gg, P, 0.7, -0.3, (34.3, 1.8, 0))
    place(cp.work_lamp, 'flicker', 'Generator Work Lamp', (31.4, 3.4, 0), rz=face_rz(-1, 0.3) + PI / 2)
    place(cp.hanging_lantern, 'swing', 'Porch Lantern', W((27.0, -33.6), 0.0, (2.6, 0.8, 2.72)), rz=0.0, drop=0.3)
    cp.crate_static(gg, P, 0.9, 0.1, (34.3, -16.0, 0))
    cp.crate_static(gg, P, 0.6, 0.5, (34.2, -16.2, 0.9))
    cp.barrel_static(gg, P, (34.6, 0.3, 0))
    cp.barrel_static(gg, P, (33.9, 0.6, 0))
    cp.barrel_static(gg, P, (34.5, 12.0, 0), tipped=True)
    # tarp over a stack of crates
    gt = S(34, 16)
    cp.crate_static(gt, P, 0.9, 0.0, (34.3, 16.2, 0))
    cp.crate_static(gt, P, 0.9, 0.0, (34.3, 17.2, 0))
    gt.box((34.3, 16.7, 0.93), (1.05, 2.1, 0.06), P.tarp)
    place(cp.tarp_sheet, 'cloth', 'Loose Tarp', (33.75, 16.7, 0.93), rz=PI / 2, w=2.0, h=0.85)
    cp.lamp_static(S(30, 8), P, (30.2, 10.0, 0), lit=False)
    place(cp.hay_prop, 'jolt', 'Hay Bale', (33.6, -25.0, 0), rz=PI / 2 + 0.1)
    cp.hay_bale(S(33, -25), P, (34.4, -26.2, 0), rz=-0.15)
    wagon_place((27.0, -33.6), 0.0, body=P.boards_red, trim=P.cream, roof=P.wood_dark, seed=7, lit=True)
    place(lambda p, P: pf.tree(p, P.bark, P.leaf, h=7.0, crown=2.3, seed=21), 'foliage', 'Elm Tree', (34.0, 33.6, 0),
          params={'leaf': '#4a4a2a'})
    cp.tree_static(S(34.2, 22.2), P, (34.2, 22.2, 0), h=6.5, crown=2.0, seed=22)


def build_north_yard():
    # picnic yard between the wheel and the funhouse
    g = S(12, 28)
    cp.picnic_table(g, P, (10.5, 21.5, 0), rz=0.2)
    cp.picnic_table(g, P, (13.8, 29.8, 0), rz=-0.4)
    for (x, y) in ((10.5, 21.5),):
        g.cyl((x, y, 0.76), 0.03, 1.6, P.wood_dark, n=6)
        cp.wedge_cone(g, (x, y, 2.3), 1.3, 0.0, 0.03, 0.35, [P.canvas_teal, P.canvas_cream], n=10, rows=1)
    # hot-dog stand
    c, rz = (11.5, 33.4), 0.0
    gs = S(*c)
    with gs.at((c[0], c[1], 0), rz):
        booth_shell(gs, 3.6, 2.2, h=2.6, wall=P.boards_teal, trim=P.cream, aw=[P.canvas_red, P.canvas_cream], seed=40, awning=1.0,
                    title='HOT DOGS', ink=P.mustard, back_posters=False)
        gs.box((0.6, 0.2, 1.15), (0.9, 0.5, 0.2), P.iron)
        for k in range(4):
            gs.cyl((0.3 + k * 0.2, 0.2, 1.27), 0.03, 0.005, P.red, n=6, ry=PI / 2)
    place(cp.balloons, 'bob', 'Balloon Bunch', (8.4, 25.2, 0), n=5, seed=6)
    place(cp.lantern_post, 'flame', 'Yard Lantern', (13.2, 24.8, 0), key='lantern_lit', light=True)
    gs.cyl((8.8, 27.0, 0), 0.07, 3.3, P.wood_dark, n=6)
    gs.collide((8.8, 27.0, 1.6), (0.2, 0.2, 3.3))
    cp.trash_barrel(g, P, (15.5, 20.6, 0))
    cp.popcorn_box(g, P, (12.1, 22.6, 0.02), rz=1.0, tipped=True)
    cp.ticket_litter(g, P, (11.6, 26.0), n=5, seed=31, spread=1.5)
    # calliope? no — a broken kiddie ride car
    with g.at((7.6, 33.6, 0), rz=0.6):
        g.box((0, 0, 0.35), (1.3, 0.8, 0.5), P.red, bevel=0.08)
        g.box((0.1, 0, 0.7), (0.5, 0.7, 0.3), P.cream, bevel=0.05)
        for sx in (-1, 1):
            for sy in (-1, 1):
                g.cyl((sx * 0.45, sy * 0.42, 0.18), 0.17, 0.08, P.black, n=10, rx=PI / 2)
        g.collide((0, 0, 0.4), (1.3, 0.9, 0.8))


# ================================================================ altars, spawns, env, previews

def build_markers():
    altars = [(-31.6, -31.5), (-13.8, -21.0), (-22.5, -1.0), (-33.4, 22.0), (-12.5, 26.0), (-7.2, 19.5), (11.2, 26.2),
              (19.0, 26.4), (32.0, 13.5), (31.8, -29.5), (20.5, -27.6), (5.0, 6.0), (-3.0, -8.3)]
    for (x, y) in altars:
        m.flag_point((x, y, 0), prefab=lambda g: cp.altar(g, P))
    m.spawn('hunter', (-1.2, -30.2, 0), face=(0, 1))
    m.spawn('hunter', (1.2, -30.2, 0), face=(0, 1))
    m.spawn('hunter', (0.0, -31.4, 0), face=(0, 1))
    for (x, y) in ((-33.4, 0.0), (-26.0, -26.5), (-9.0, -31.5), (-18.5, 23.5), (-9.5, 9.0), (4.5, 33.5), (15.0, 22.5), (33.0, 27.5),
                   (31.0, -6.0), (20.5, 1.5), (11.5, -15.0), (-17.0, -1.0), (28.0, 30.5), (-28.0, 8.5)):
        m.spawn('ghost', (x, y, 0), face=(-x, -y))


def build_env():
    m.env(
        sky='#0c0e1f',
        fog={'color': '#11142a', 'near': 9, 'far': 62},
        hemi={'sky': '#53608f', 'ground': '#2a2018', 'intensity': 0.5},
        moon={'dir': [-0.38, -1.0, -0.42], 'color': '#a9b8ff', 'intensity': 0.55, 'shadows': True},
        exposure=1.0,
        ambience='night',
        stars=True,
        previewClip=3.3,
    )
    v = m.preview
    v((0.0, -29.0, 1.6), (0.0, 0.0, 3.5), name='gate')
    v((10.2, -5.2, 1.6), (0.0, 0.0, 2.6), name='plaza')
    v((-2.0, 7.5, 1.6), (-2.0, 29.0, 8.0), name='wheel')
    v((-13.2, -1.0, 1.7), (-27.0, -1.0, 2.6), name='bigtop')
    v((20.5, -28.5, 1.6), (20.5, 0.0, 2.0), name='midway')
    v((22.0, 11.0, 1.6), (24.0, 24.0, 5.0), name='funhouse')
    v((-15.0, -16.5, 1.6), (-22.0, -22.0, 1.6), name='fortune')
    v((-16.5, 17.0, 1.6), (-27.0, 22.0, 1.4), name='backlot')
    v((2.5, -16.5, 1.6), (9.0, -21.0, 1.6), name='lioncage')
    v((24.0, 24.6, 1.6), (21.0, 27.5, 1.4), name='funhouse_in')
    v((31.0, -26.0, 1.6), (32.0, 0.0, 1.6), name='alley')
    v((1.5, -26.0, 1.7), (0.0, -35.6, 5.0), name='marquee')
    v((0.0, -2.0, 88.0), (0.0, -1.99, 0.0), name='top')
    v((-14.5, 4.5, 1.7), (-20.0, 10.5, 0.8), name='pen')
    v((-20.0, -10.8, 1.7), (-28.5, -13.0, 1.0), name='canvaswagon')
    v((-4.5, 10.0, 1.7), (-9.6, 14.6, 0.6), name='retired')


build_ground()
build_boundary()
fence_buntings()
build_gate()
build_carousel()
build_plaza()
build_avenue()
build_lion_cage()
build_big_top()
build_ferris()
build_midway()
build_funhouse()
build_back_lot()
build_sw()
build_menagerie_pen()
build_canvas_wagon()
build_retired_horses()
build_east_alley()
build_north_yard()
build_markers()
build_env()
split_untextured_chunks()
m.finish()
