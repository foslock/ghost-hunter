"""Prefabs for Thistlewick Farm (blender/maps/farm.py).

Static prefabs: fn(g, M, ...) draw into a Geo at its current transform (origin = the floor point
under the object, front facing -Y). Prop prefabs: fn(p, M, ...) draw into prop parts and set the
archetype params. `M` is the map's material palette (an attribute bag built in farm.py).
"""
import math
import random

import numpy as np

from lib import tex
from lib.gh import TAU

PI = math.pi


# ======================================================================== textures

def _stamp(img, cx, cy, rad, col):
    """Soft disc stamped into img (wrapping on both axes). cx, cy in pixels."""
    h, w, _ = img.shape
    r = int(math.ceil(rad)) + 1
    ys = np.arange(int(cy) - r, int(cy) + r + 1)
    xs = np.arange(int(cx) - r, int(cx) + r + 1)
    d = np.sqrt((ys[:, None] - cy) ** 2 + (xs[None, :] - cx) ** 2)
    a = np.clip(rad + 0.5 - d, 0, 1)[..., None]
    ix = np.ix_(ys % h, xs % w)
    img[ix] = img[ix] * (1 - a) + np.asarray(col) * a


def corn_tex(size=512, seed=21):
    """Side view of a dense corn row: stalks, arching leaves and a few ears on a deep shadow."""
    h = w = size
    k = size / 512
    rng = random.Random(seed)
    yy = np.arange(h)[:, None] / h  # row 0 = top of the wall
    n = tex.fbm((h, w), (3, 10), 4, seed)
    dark, mid = tex.hex_rgb('#211f16'), tex.hex_rgb('#4f4529')
    t = np.clip(0.8 - yy * 0.85 + (n - 0.5) * 0.5, 0, 1)
    img = dark * (1 - t[..., None]) + mid * t[..., None]
    img = np.broadcast_to(img, (h, w, 3)).copy()
    stalks = ['#b39a5e', '#a08a50', '#c4ad6e', '#8e8048', '#9a9050']
    leaves = ['#a48c50', '#c2a664', '#8a7e46', '#b8a05c', '#7c7a44', '#9a8a4a']
    for s in range(26):
        far = s < 11
        f = 0.5 if far else 1.0
        x0 = rng.uniform(0, w)
        col = tex.hex_rgb(rng.choice(stalks)) * rng.uniform(0.75, 1.05) * f
        wid = (1.4 if far else 2.4) * k
        top = rng.uniform(0.0, 0.06) * h
        for yi in range(int(top), h, 2):
            x = x0 + math.sin(yi / h * 3.0 + s) * 3 * k
            _stamp(img, x, yi, wid, col)
        for j in range(rng.randint(4, 7)):
            y0 = rng.uniform(0.1, 0.9) * h
            side = rng.choice((-1, 1))
            L = rng.uniform(0.07, 0.15) * w
            lc = tex.hex_rgb(rng.choice(leaves)) * rng.uniform(0.75, 1.05) * f
            for q in range(24):
                tt = q / 23
                _stamp(img, x0 + side * L * tt, y0 - L * 0.45 * tt + L * 1.0 * tt * tt,
                       max(0.6, 3.2 * k * (1 - tt) + 0.5), lc)
        if not far and rng.random() < 0.7:
            ey = rng.uniform(0.35, 0.62) * h
            side = rng.choice((-1, 1))
            for q in range(10):
                _stamp(img, x0 + side * (4 + q * 0.9) * k, ey + q * 2.6 * k, 3.4 * k, tex.hex_rgb('#c8a860') * 0.85)
        # tassel
        for q in range(6):
            a = rng.uniform(-1.2, 1.2)
            for r in range(8):
                _stamp(img, x0 + math.sin(a) * r * 1.6 * k, top + 2 + math.cos(a) * r * 1.6 * k, 0.8 * k,
                       tex.hex_rgb('#d8c080') * f)
    return np.clip(img, 0, 1)


def straw_tex(size=256, seed=31, dark='#8f6c33', light='#e0c482'):
    """Hay / straw: fine horizontal fibres."""
    h = w = size
    s1 = tex.value_noise((h, w), (128, 8), seed)
    s2 = tex.value_noise((h, w), (256, 16), seed + 1)
    n = tex.fbm((h, w), 6, 3, seed + 2)
    t = 0.55 + (s1 - 0.5) * 0.9 + (s2 - 0.5) * 0.8 + (n - 0.5) * 0.35
    return np.clip(tex.colorize(t, dark, light), 0, 1)


def gingham_tex(size=256, a='#9a3a2e', b='#e2d8c2', checks=8):
    h = w = size
    y = np.arange(h)[:, None] / h * checks
    x = np.arange(w)[None, :] / w * checks
    bx = (np.floor(x * 2) % 2).astype(float)
    by = (np.floor(y * 2) % 2).astype(float)
    k = (bx + by) / 2  # 0 / 0.5 / 1
    img = tex.colorize(np.broadcast_to(k, (h, w)), b, a)
    n = tex.fbm((h, w), 8, 3, 3)
    return np.clip(img * (0.92 + 0.12 * n)[..., None], 0, 1)


# ======================================================================== primitives

def prim_pumpkin(r, h, ribs=8, depth=0.12, rings=7, bottom=True):
    """Ribbed, squashed pumpkin body from z=0 to ~h, with a dimpled top."""
    n = ribs * 3
    prof = []
    for i in range(rings + 1):
        phi = PI * (0.1 + 0.8 * i / rings)
        z = h * ((1 - math.cos(phi)) / 2 - 0.0245) / 0.951
        prof.append((r * math.sin(phi), z))
    prof.append((r * 0.12, h * 0.86))
    rows = len(prof)
    verts = []
    for j in range(n):
        th = TAU * j / n
        k = 1 - depth * 0.5 * (1 - math.cos(ribs * th))
        c, s = math.cos(th), math.sin(th)
        for rr, z in prof:
            kk = k if rr > r * 0.2 else 1 - (1 - k) * 0.4
            verts.append((rr * kk * c, rr * kk * s, z))
    faces, sm = [], []
    for j in range(n):
        j2 = (j + 1) % n
        for i in range(rows - 1):
            faces.append((j * rows + i, j2 * rows + i, j2 * rows + i + 1, j * rows + i + 1))
            sm.append(True)
    if bottom:
        faces.append(tuple(j * rows for j in reversed(range(n))))
        sm.append(False)
    faces.append(tuple(j * rows + rows - 1 for j in range(n)))
    sm.append(False)
    return verts, faces, sm


def prim_blade(length, width, up=0.45, droop=0.95, seg=3, two_sided=False):
    """Leaf blade along +X from the origin: rises, then arches down to a point."""
    verts, faces = [], []
    for i in range(seg + 1):
        t = i / seg
        d = length * t
        z = length * (up * t - droop * t * t)
        w = width * math.sin(PI * min(0.97, 0.18 + 0.82 * t))
        verts += [(d, -w / 2, z), (d, w / 2, z)]
    for i in range(seg):
        faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    if two_sided:
        off = len(verts)
        verts += [(x, y, z - 0.004) for x, y, z in verts]
        faces += [tuple(off + v for v in reversed(f)) for f in faces[:seg]]
    return verts, faces, [True] * len(faces)


def prim_ribbon(pts, width, z=0.012, seed=0, rough=0.25, step=0.7, taper=True):
    """Flat ribbon (dirt path) along a polyline with wobbly edges."""
    rng = random.Random(seed)
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        for i in range(n):
            t = i / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    out.append(tuple(pts[-1]))
    p1, p2 = rng.uniform(0, 6), rng.uniform(0, 6)
    verts, faces = [], []
    s = 0.0
    N = len(out)
    for i, (x, y) in enumerate(out):
        a = out[max(0, i - 1)]
        b = out[min(N - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        s += step
        end = 1.0
        if taper:
            end = min(1.0, 0.45 + 0.55 * min(i, N - 1 - i) / 2.0)
        wl = width / 2 * end * (1 + rough * (0.6 * math.sin(s * 0.9 + p1) + 0.4 * math.sin(s * 2.3 + p2)))
        wr = width / 2 * end * (1 + rough * (0.6 * math.sin(s * 1.1 + p2) + 0.4 * math.sin(s * 2.7 + p1)))
        verts.append((x - nx * wr, y - ny * wr, z))
        verts.append((x + nx * wl, y + ny * wl, z))
    for i in range(N - 1):
        a = 2 * i
        faces.append((a, a + 2, a + 3, a + 1))
    return verts, faces, [False] * len(faces)


def prim_poly(points, z=0.0):
    """Flat upward-facing polygon (CCW points)."""
    return [(x, y, z) for x, y in points], [tuple(range(len(points)))], [False]


def blob_poly(cx, cy, rx, ry, n=14, seed=0, jitter=0.18):
    rng = random.Random(seed)
    pts = []
    for i in range(n):
        a = TAU * i / n
        k = 1 + rng.uniform(-jitter, jitter)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return pts


def prim_hull(L, W, D, n=8, t=0.035):
    """Open rowboat hull along Y (bow at -Y), gunwale at z=0, keel at -D. Outer + inner skin."""
    stations = []
    for i in range(n + 1):
        u = -1 + 2 * i / n
        w = W / 2 * max(0.02, (1 - abs(u) ** 2.2)) ** 0.5
        if u < 0:
            w *= 1 - 0.35 * (-u) ** 3
        d = D * (1 - 0.25 * abs(u) ** 2)
        stations.append((u * L / 2, w, d))
    prof = [(-1.0, 0.0), (-0.92, -0.55), (-0.55, -0.92), (0.0, -1.0), (0.55, -0.92), (0.92, -0.55), (1.0, 0.0)]
    m = len(prof)
    verts, faces = [], []
    for skin, k in ((0, 1.0), (1, None)):
        base = len(verts)
        for y, w, d in stations:
            ww, dd = (w, d) if skin == 0 else (max(0.01, w - t), d - t)
            for px, pz in prof:
                verts.append((px * ww, y, pz * dd))
        for i in range(n):
            for j in range(m - 1):
                a = base + i * m + j
                b = base + (i + 1) * m + j
                q = (a, b, b + 1, a + 1) if skin == 0 else (a, a + 1, b + 1, b)
                faces.append(q)
    # gunwale rim
    for i in range(n):
        for j in (0, m - 1):
            o0, o1 = i * m + j, (i + 1) * m + j
            off = (n + 1) * m
            q = (o0, off + o0, off + o1, o1) if j == 0 else (o0, o1, off + o1, off + o0)
            faces.append(q)
    return verts, faces, [True] * len(faces)


# ======================================================================== small helpers

def slab(g, a, b, length, thick, mat, y=0.0, extend=0.0, bevel=0.0):
    """Board/slab whose inner face runs from a=(x,z) to b=(x,z) in the XZ plane, spanning
    `length` along Y centred on y. The thickness grows to the side facing up/out."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz)
    nx, nz = dz / L, -dx / L
    if nz < 0:
        nx, nz = -nx, -nz
    cx = (a[0] + b[0]) / 2 + nx * thick / 2
    cz = (a[1] + b[1]) / 2 + nz * thick / 2
    g.box((cx, y, cz), (L + extend, length, thick), mat, ry=-math.atan2(dz, dx), bevel=bevel)


def spoked_wheel(g, c, r, M, spokes=8, width=0.08, rim=None, axis='x'):
    rim = rim or M.wood_dk
    ry = PI / 2 if axis == 'x' else 0.0
    rx = PI / 2 if axis == 'y' else 0.0
    with g.at(c, ry=ry, rx=rx):
        g.torus((0, 0, 0), r - 0.02, 0.04, rim, n=14, m=4)
        g.cyl((0, 0, -width), 0.07, width * 2, M.wood_dk, n=8)
        for i in range(spokes):
            a = TAU * i / spokes
            g.box((math.cos(a) * r / 2, math.sin(a) * r / 2, 0), (r - 0.05, 0.025, 0.025), M.wood_mid, rz=a)


def bucket_geo(g, M, pos=(0, 0, 0), r=0.15, h=0.3, mat=None, water=False, tilt=0.0):
    mat = mat or M.tin
    with g.at(pos, rx=tilt):
        g.lathe((0, 0, 0), [(r * 0.78, 0), (r, h)], mat, n=12, cap_top=False)
        g.lathe((0, 0, 0.02), [(r * 0.95, h - 0.02), (r * 0.74, 0.0)], mat, n=12, cap_bottom=False, cap_top=False)
        g.torus((0, 0, h), r, 0.01, M.iron, n=12, m=4)
        if water:
            g.cyl((0, 0, h * 0.75), r * 0.94, 0.01, M.water, n=12)
        g.tube([(-r, 0, h), (-r * 0.6, 0, h + r * 0.7), (r * 0.6, 0, h + r * 0.7), (r, 0, h)], 0.006, M.iron, n=4, caps=False)


def pumpkin(g, M, pos=(0, 0, 0), r=0.3, rz=0.0, tilt=0.0, mat=None, stem=True, ribs=8, rings=7):
    h = r * 1.3
    low = rings <= 5
    with g.at(pos, rz, rx=tilt):
        g.add(prim_pumpkin(r, h, ribs=ribs, rings=rings, bottom=not low), mat or M.pumpkin)
        if stem:
            g.cyl((0, 0, h * 0.82), r * 0.09, r * 0.34, M.stem, n=4 if low else 5, r2=r * 0.055, rx=0.3,
                  smooth=False, caps=not low)


def leaf_scatter(g, M, cx, cy, radius, count, seed=0, mats=None, z=0.006):
    rng = random.Random(seed)
    mats = mats or [M.leaf_orange, M.leaf_gold, M.leaf_red]
    for i in range(count):
        a = rng.uniform(0, TAU)
        d = radius * math.sqrt(rng.random())
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        s = rng.uniform(0.07, 0.12)
        rot = rng.uniform(0, TAU)
        pts = [(math.cos(rot + q) * s * k, math.sin(rot + q) * s * k) for q, k in ((0, 1.0), (2.2, 0.5), (PI, 0.8), (4.1, 0.5))]
        g.add(prim_poly([(x + px, y + py) for px, py in pts], z + rng.uniform(0, 0.004)), rng.choice(mats))


def grass_tuft(g, M, pos, seed=0, h=0.35, n=4, mats=None):
    rng = random.Random(seed)
    mats = mats or [M.grass_tuft, M.grass_dry]
    for i in range(n):
        a = rng.uniform(0, TAU)
        L = h * rng.uniform(0.7, 1.2)
        g.add(prim_blade(L, 0.035, up=2.2, droop=1.6, seg=2, two_sided=False), rng.choice(mats),
              _mat(pos, a, rng.uniform(-0.05, 0.05)))


class Geo_off:
    """Wraps a Geo so everything drawn through it is offset (used for re-pivoting prefabs)."""

    def __init__(self, g, off):
        self.g = g
        self.off = off

    def __getattr__(self, name):
        fn = getattr(self.g, name)
        if name in ('box', 'cyl', 'lathe', 'sphere', 'blob', 'torus', 'prism'):
            def wrapped(c, *a, **k):
                return fn((c[0] + self.off[0], c[1] + self.off[1], c[2] + self.off[2]), *a, **k)
            return wrapped
        return fn


def _mat(pos, rz, dz=0.0):
    from lib.gh import X
    return X((pos[0], pos[1], pos[2] + dz), rz)


# ======================================================================== corn

def corn_stalk(g, M, pos, h, rng, leaves=3, ear=True, out_dir=None, tassel=True, base_from=0.0):
    """One corn stalk. out_dir: preferred leaf heading (radians) or None for any."""
    x, y, z = pos
    lean_x, lean_y = rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)
    z0 = z + base_from
    g.cyl((x, y, z0), 0.024, h - base_from, M.corn_stalk, n=4, r2=0.014, smooth=True, ry=lean_x, rx=lean_y,
          caps=False)
    tx, ty, tz = x + lean_x * h, y - lean_y * h, z + h
    for i in range(leaves):
        lz = z0 + (h - base_from) * (rng.uniform(0.25, 0.7) if i else rng.uniform(0.78, 0.92))
        a = (out_dir + rng.uniform(-1.1, 1.1)) if out_dir is not None else rng.uniform(0, TAU)
        L = rng.uniform(0.45, 0.8)
        g.add(prim_blade(L, rng.uniform(0.06, 0.09), up=0.5, droop=rng.uniform(0.7, 1.1)),
              rng.choice((M.corn_leaf, M.corn_leaf2)), _mat((x + lean_x * (lz - z), y - lean_y * (lz - z), lz), a))
    if tassel:
        for q in range(1):
            a = rng.uniform(0, TAU)
            g.add(prim_blade(0.22, 0.02, up=1.4, droop=1.6, seg=2, two_sided=False), M.straw,
                  _mat((tx, ty, tz - 0.02), a))
    if ear and rng.random() < 0.3:
        ez = z + h * rng.uniform(0.45, 0.6)
        a = (out_dir if out_dir is not None else rng.uniform(0, TAU)) + rng.uniform(-0.6, 0.6)
        ex, ey = x + math.cos(a) * 0.06, y + math.sin(a) * 0.06
        g.lathe((ex, ey, ez), [(0.03, 0), (0.042, 0.08), (0.005, 0.24)], M.corn_husk, n=4,
                smooth=False, ry=0.45 * math.cos(a), rx=-0.45 * math.sin(a), cap_top=False)


def corn_block(g, M, x0, y0, x1, y1, faces, seed=0, h=2.35, spacing=0.52, col=True, top=True, core=True,
               shrink=0.15, top_spacing=0.42):
    """Dense corn: a shadowed core block with stalks along the given open faces ('N','S','E','W')."""
    rng = random.Random(seed)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sx, sy = x1 - x0, y1 - y0
    inset = shrink - 0.03
    if core:
        g.box((cx, cy, h * 0.41), (max(0.1, sx - 2 * shrink), max(0.1, sy - 2 * shrink), h * 0.82), M.corn,
              bevel=0.05 if shrink > 0 else 0.0)
    if col:
        g.collide((cx, cy, 2.0), (sx, sy, 4.0))   # tall enough that nothing lets a ghost hop on top
    ztop = h * 0.82
    for f in faces:                                            # leaves drooping over the core's top edge
        horiz = f in 'NS'
        L0, L1 = (x0, x1) if horiz else (y0, y1)
        od = {'N': PI / 2, 'S': -PI / 2, 'E': 0.0, 'W': PI}[f]
        edge = {'N': y1 - shrink, 'S': y0 + shrink, 'E': x1 - shrink, 'W': x0 + shrink}[f]
        t = L0 + rng.uniform(0.05, 0.25)
        while t < L1 - 0.05:
            px, py = (t, edge) if horiz else (edge, t)
            g.add(prim_blade(rng.uniform(0.35, 0.55), rng.uniform(0.06, 0.09), up=0.9, droop=1.7, seg=3),
                  rng.choice((M.corn_leaf, M.corn_leaf2)), _mat((px, py, ztop - 0.04), od + rng.uniform(-0.7, 0.7)))
            t += rng.uniform(0.22, 0.38)
    for f in faces:
        if f in 'NS':
            yy = y1 - inset if f == 'N' else y0 + inset
            od = PI / 2 if f == 'N' else -PI / 2
            n = max(1, int(sx / spacing))
            for i in range(n):
                xx = x0 + (i + rng.uniform(0.2, 0.8)) * sx / n
                corn_stalk(g, M, (xx, yy + rng.uniform(-0.08, 0.08), 0), h * rng.uniform(1.0, 1.14), rng,
                           leaves=2, out_dir=od)
        else:
            xx = x1 - inset if f == 'E' else x0 + inset
            od = 0.0 if f == 'E' else PI
            n = max(1, int(sy / spacing))
            for i in range(n):
                yy = y0 + (i + rng.uniform(0.2, 0.8)) * sy / n
                corn_stalk(g, M, (xx + rng.uniform(-0.08, 0.08), yy, 0), h * rng.uniform(1.0, 1.14), rng,
                           leaves=2, out_dir=od)
    if top:
        # tops of the inner stalks poke above the core for a ragged silhouette
        nx, ny = max(1, int((sx - 0.3) / top_spacing)), max(1, int((sy - 0.3) / top_spacing))
        for i in range(nx):
            for j in range(ny):
                if rng.random() < 0.3:
                    continue
                px = x0 + 0.15 + (i + rng.uniform(0.2, 0.8)) * (sx - 0.3) / nx
                py = y0 + 0.15 + (j + rng.uniform(0.2, 0.8)) * (sy - 0.3) / ny
                corn_stalk(g, M, (px, py, 0), h * rng.uniform(0.98, 1.16), rng, leaves=2, ear=False,
                           base_from=h * 0.74)


# ======================================================================== vegetation (static)

def tree_static(g, M, seed=0, h=7.0, crown=2.6, style='round', leaves=None, lumps=3, subdiv=1):
    rng = random.Random(seed)
    leaves = leaves or [M.leaf_olive, M.leaf_gold]
    trunk_h = h * (0.45 if style != 'pine' else 0.25)
    g.lathe((0, 0, 0), [(0.32 * h / 7, 0), (0.2 * h / 7, 0.3), (0.05, trunk_h + crown)], M.bark, n=5, smooth=False,
            cap_bottom=False)
    if style == 'pine':
        tiers = 3
        for i in range(tiers):
            t = i / (tiers - 1)
            rr = crown * (1 - t * 0.7)
            g.cyl((0, 0, trunk_h + (h - trunk_h) * t * 0.72), rr, (h - trunk_h) * 0.42, rng.choice(leaves), n=7,
                  r2=0.05, smooth=False, rz=rng.uniform(0, 1))
        return
    for i in range(lumps):
        a = TAU * i / lumps + rng.uniform(-0.4, 0.4)
        d = crown * rng.uniform(0.3, 0.6)
        c = (math.cos(a) * d, math.sin(a) * d, trunk_h + crown * rng.uniform(0.4, 0.9))
        g.blob(c, crown * rng.uniform(0.5, 0.72), rng.choice(leaves), seed=seed * 31 + i, jitter=0.22,
               subdiv=subdiv, s=(1, 1, 0.82))
    g.blob((0, 0, trunk_h + crown * 1.15), crown * 0.72, rng.choice(leaves), seed=seed + 99, jitter=0.22,
           subdiv=subdiv, s=(1, 1, 0.85))


def hedge(g, M, length, h=2.3, d=1.3, seed=0, col=True, lump=2.0):
    """Hedgerow along X centred on the origin."""
    rng = random.Random(seed)
    g.box((0, 0, h * 0.45), (length, d * 0.8, h * 0.9), M.hedge, bevel=0.2)
    n = max(1, int(length / lump))
    for i in range(n):
        x = -length / 2 + (i + 0.5) * length / n + rng.uniform(-0.3, 0.3)
        g.blob((x, rng.uniform(-0.2, 0.2), h * rng.uniform(0.72, 0.9)), rng.uniform(0.6, 0.85), M.hedge,
               seed=seed * 13 + i, jitter=0.25, subdiv=0, s=(1.4, 1.1, 0.85))
    if col:
        g.collide((0, 0, h / 2), (length, d, h))


def stone_wall(g, M, length, h=0.95, d=0.7, seed=0, col=True):
    """Dry-stone wall along X centred on the origin (ghosts can hop it, hunters can't)."""
    rng = random.Random(seed)
    g.box((0, 0, h * 0.42), (length, d, h * 0.84), M.stone, bevel=0.08)
    x = -length / 2
    while x < length / 2:
        w = rng.uniform(0.45, 0.8)
        g.box((min(x + w / 2, length / 2 - 0.1), rng.uniform(-0.04, 0.04), h * 0.88), (w, d * 0.95, rng.uniform(0.14, 0.22)),
              M.stone_cap, rz=rng.uniform(-0.08, 0.08), ry=rng.uniform(-0.12, 0.12))
        x += w
    if col:
        g.collide((0, 0, 0.525), (length, d, 1.05))


def rail_fence(g, M, length, h=1.15, spacing=2.4, rails=3, seed=0, col=True, mat=None, col_h=None):
    """Post-and-rail fence along +X from the origin."""
    rng = random.Random(seed)
    mat = mat or M.grey_wood
    n = max(1, round(length / spacing))
    for i in range(n + 1):
        x = length * i / n
        hh = h + rng.uniform(-0.04, 0.1)
        g.box((x, 0, hh / 2), (0.13, 0.13, hh), mat, rz=rng.uniform(-0.12, 0.12))
    for i in range(n):
        xa, xb = length * i / n, length * (i + 1) / n
        for r in range(rails):
            z = h * (0.32 + 0.55 * r / max(1, rails - 1)) + rng.uniform(-0.04, 0.04)
            dz = rng.uniform(-0.06, 0.06)
            g.box(((xa + xb) / 2, -0.085, z), (xb - xa + 0.18, 0.055, 0.11), mat,
                  ry=-math.atan2(dz, xb - xa), rz=rng.uniform(-0.02, 0.02))
    if col:
        ch = col_h or (h + 0.5)
        g.collide((length / 2, 0, ch / 2), (length, 0.22, ch))


def picket_fence(g, M, length, h=0.95, col=True):
    """White picket fence along +X (collider 1.05 m: ghosts hop it, hunters can't)."""
    n = max(1, round(length / 2.0))
    for i in range(n + 1):
        x = length * i / n
        g.box((x, 0, (h + 0.08) / 2), (0.1, 0.1, h + 0.08), M.paint_white)
        g.cyl((x, 0, h + 0.08), 0.055, 0.06, M.paint_white, n=6, r2=0.02, smooth=False)
    for z in (h * 0.3, h * 0.75):
        g.box((length / 2, 0.06, z), (length, 0.03, 0.08), M.paint_white)
    x = 0.12
    hp = h - 0.02
    while x < length - 0.08:
        vs = [(x + px, 0.1, 0.04 + pz) for px, pz in ((-0.0375, 0), (0.0375, 0), (0.0375, hp - 0.07), (0.0, hp),
                                                       (-0.0375, hp - 0.07))]
        g.add((vs, [(0, 1, 2, 3, 4)], [False]), M.paint_white)
        x += 0.19
    if col:
        g.collide((length / 2, 0.04, 0.525), (length, 0.2, 1.05))


# ======================================================================== farm clutter (static)

def hay_bale_geo(g, M, pos=(0, 0, 0), rz=0.0, ry=0.0):
    with g.at(pos, rz, ry=ry):
        g.box((0, 0, 0.22), (1.0, 0.5, 0.44), M.hay, bevel=0.07)
        for x in (-0.24, 0.24):
            g.box((x, 0, 0.22), (0.022, 0.512, 0.452), M.rope)


def hay_stack(g, M, r=2.2, h=4.0, col=True):
    """Rounded haystack around a pole (landmark + sight blocker)."""
    g.lathe((0, 0, 0), [(r * 0.92, 0), (r, h * 0.22), (r * 0.95, h * 0.45), (r * 0.72, h * 0.7), (r * 0.38, h * 0.88),
                        (0.12, h)], M.hay, n=14, smooth=True)
    g.cyl((0, 0, h - 0.2), 0.05, 0.9, M.wood_dk, n=5)
    for i in range(9):
        a = TAU * i / 9 + 0.3
        g.box((math.cos(a) * r * 0.97, math.sin(a) * r * 0.97, 0.18), (0.6, 0.18, 0.36), M.hay, rz=a + PI / 2, bevel=0.05)
    if col:
        g.collide((0, 0, h * 0.4), (r * 1.7, r * 1.7, h * 0.8))
        g.collide((0, 0, h * 0.85), (r * 1.0, r * 1.0, h * 0.3))


def trough(g, M, length=2.2, col=True):
    g.box((0, 0, 0.32), (length, 0.7, 0.5), M.weathered, bevel=0.03)
    g.box((0, 0, 0.56), (length - 0.12, 0.56, 0.02), M.water)
    for sx in (-1, 1):
        g.box((sx * (length / 2 - 0.25), 0, 0.04), (0.12, 0.8, 0.08), M.wood_dk)
    if col:
        g.collide((0, 0, 0.3), (length, 0.7, 0.6))


def woodpile(g, M, length=3.0, h=1.4, seed=0, col=True, back=True):
    rng = random.Random(seed)
    rows = int(h / 0.16)
    g.box((0, 0, rows * 0.155 / 2 + 0.01), (length - 0.1, 0.66, rows * 0.155), M.bark)
    for r in range(rows):
        z = 0.08 + r * 0.155
        x = -length / 2 + 0.08 + (r % 2) * 0.07
        while x < length / 2 - 0.08:
            rr = rng.uniform(0.06, 0.085)
            for sy in ((-1, 1) if back else (-1,)):
                y = sy * (0.335 + rng.uniform(0, 0.03))
                ring = [(x + math.cos(TAU * k / 6 + 0.3) * rr, z + math.sin(TAU * k / 6 + 0.3) * rr) for k in range(6)]
                core = [(x + (px - x) * 0.72, z + (pz - z) * 0.72) for px, pz in ring]
                for poly, mat, dy in ((ring, M.bark, 0.0), (core, rng.choice((M.wood_light, M.wood_light, M.wood_mid)), 0.006)):
                    vs = [(px, y + sy * dy, pz) for px, pz in poly]
                    f = tuple(range(6)) if sy < 0 else tuple(reversed(range(6)))
                    g.add((vs, [f], [False]), mat)
            x += rr * 2.05
    for sx in (-1, 1):
        g.box((sx * (length / 2 + 0.05), 0, h / 2 + 0.1), (0.1, 0.1, h + 0.2), M.wood_dk)
    if col:
        g.collide((0, 0, h / 2), (length + 0.2, 0.75, h))


def sack_geo(g, M, pos=(0, 0, 0), rz=0.0, s=1.0, mat=None):
    with g.at(pos, rz, s=s):
        g.sphere((0, 0, 0.22), 0.26, mat or M.burlap, n=8, s=(1.0, 0.7, 0.9))
        g.sphere((0, 0, 0.44), 0.1, mat or M.burlap, n=6, s=(1.2, 0.8, 0.8))
        g.torus((0, 0, 0.42), 0.07, 0.012, M.rope, n=8, m=3)


def crate_geo(g, M, s=0.6, pos=(0, 0, 0), rz=0.0, apples=False):
    with g.at(pos, rz):
        g.box((0, 0, s * 0.04), (s, s * 0.8, s * 0.08), M.wood_light)
        for sy in (-1, 1):
            for z in (0.18, 0.5, 0.82):
                g.box((0, sy * s * 0.38, s * z), (s, 0.025, s * 0.2), M.wood_light)
        for sx in (-1, 1):
            g.box((sx * s * 0.48, 0, s * 0.5), (0.03, s * 0.8, s), M.wood_mid)
        if apples:
            g.box((0, 0, s * 0.8), (s * 0.92, s * 0.72, 0.02), M.apple)
            rng = random.Random(int(s * 100))
            for i in range(9):
                g.sphere((rng.uniform(-0.4, 0.4) * s, rng.uniform(-0.3, 0.3) * s, s * 0.83), 0.05, M.apple, n=6)


def ladder_geo(g, M, h=3.4, w=0.45, lean=0.28):
    with g.at((0, 0, 0), rx=-lean):
        for sx in (-1, 1):
            g.box((sx * w / 2, 0, h / 2), (0.05, 0.06, h), M.wood_light)
        z = 0.3
        while z < h - 0.1:
            g.cyl((-w / 2, 0, z), 0.018, w, M.wood_light, n=5, ry=PI / 2)
            z += 0.3


def tool_lean(g, M, kind='pitchfork', lean=0.25):
    with g.at((0, 0, 0), rx=-lean):
        g.cyl((0, 0, 0), 0.018, 1.45, M.wood_light, n=5)
        if kind == 'pitchfork':
            g.box((0, 0, 1.47), (0.22, 0.02, 0.03), M.iron)
            for i in range(3):
                g.cyl((-0.09 + i * 0.09, 0, 1.47), 0.007, 0.28, M.iron, n=4, r2=0.002)
        elif kind == 'rake':
            g.box((0, 0, 1.47), (0.4, 0.03, 0.04), M.iron)
            for i in range(9):
                g.cyl((-0.18 + i * 0.045, 0, 1.47), 0.005, 0.07, M.iron, n=3)
        elif kind == 'shovel':
            g.box((0, 0, -0.1), (0.2, 0.02, 0.26), M.iron)


def bench_geo(g, M, w=1.5):
    g.box((0, 0, 0.44), (w, 0.36, 0.05), M.grey_wood, bevel=0.01)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.15), 0, 0.21), (0.06, 0.32, 0.42), M.grey_wood)
    g.collide((0, 0, 0.23), (w, 0.36, 0.46))


def wagon(g, M, length=3.6, width=1.7, load='hay', seed=0, col=True):
    """Hay wagon, tongue toward -Y."""
    rng = random.Random(seed)
    deck = 0.95
    g.box((0, 0, deck), (width, length, 0.1), M.weathered, bevel=0.02)
    for sx in (-1, 1):
        g.box((sx * (width / 2 - 0.03), 0, deck + 0.25), (0.06, length, 0.4), M.weathered)
        for y in (-length / 2 + 0.2, 0, length / 2 - 0.2):
            g.box((sx * (width / 2 - 0.03), y, deck + 0.25), (0.09, 0.08, 0.48), M.wood_dk)
    g.box((0, length / 2 - 0.03, deck + 0.25), (width, 0.06, 0.4), M.weathered)
    for sy in (-1, 1):
        g.box((0, sy * length * 0.32, deck - 0.12), (width - 0.1, 0.12, 0.12), M.wood_dk)
        for sx in (-1, 1):
            spoked_wheel(g, (sx * (width / 2 + 0.06), sy * length * 0.32, 0.52), 0.52, M, spokes=8)
    g.box((0, -length / 2 - 0.8, 0.55), (0.08, 1.8, 0.08), M.wood_dk, rx=0.3)
    if load == 'hay':
        for i in range(3):
            for j in range(2):
                hay_bale_geo(g, M, (rng.uniform(-0.05, 0.05), -length / 2 + 0.6 + i * 1.15 + j * 0.0, deck + 0.05 + j * 0.44),
                             PI / 2 + rng.uniform(-0.1, 0.1))
        hay_bale_geo(g, M, (0, -0.3, deck + 0.93), PI / 2 + 0.2)
    elif load == 'pumpkins':
        for i in range(13):
            pumpkin(g, M, (rng.uniform(-0.55, 0.55), rng.uniform(-1.5, 1.5), deck + 0.05 + rng.uniform(0, 0.18)),
                    rng.uniform(0.17, 0.27), rng.uniform(0, TAU), rng.uniform(-0.2, 0.2), ribs=6, rings=5)
    if col:
        g.collide((0, 0, 0.75), (width + 0.3, length, 1.5))


def tractor(g, M):
    """Little old tractor facing -Y, faded teal with ochre wheels."""
    body = M.teal
    g.box((0, -0.55, 0.95), (0.62, 1.5, 0.62), body, bevel=0.06)          # hood
    g.box((0, -1.32, 0.95), (0.68, 0.08, 0.66), M.iron, bevel=0.02)        # grille
    for i in range(6):
        g.box((-0.25 + i * 0.1, -1.37, 0.95), (0.03, 0.02, 0.55), M.tin)
    g.box((0, 0.45, 0.85), (0.7, 0.8, 0.55), body, bevel=0.05)             # transmission
    g.box((0, 0.62, 1.2), (0.5, 0.42, 0.08), M.iron, bevel=0.02)           # seat pan
    g.box((0, 0.84, 1.42), (0.46, 0.06, 0.4), M.iron, rx=-0.2, bevel=0.02)
    g.cyl((0, 0.15, 1.2), 0.025, 0.55, M.iron, n=5, rx=-0.55)              # steering column
    g.torus((0, -0.15, 1.68), 0.2, 0.02, M.iron, n=14, m=4, rx=-0.55)
    g.cyl((0.2, -0.95, 1.2), 0.04, 0.75, M.iron, n=6)                       # exhaust
    g.cyl((0.2, -0.95, 1.95), 0.05, 0.08, M.rust, n=6)
    for sx in (-1, 1):                                                       # big rear wheels
        with g.at((sx * 0.62, 0.55, 0.72), ry=PI / 2):
            g.cyl((0, 0, -0.18), 0.72, 0.36, M.rubber, n=16, smooth=False)
            g.cyl((0, 0, -0.19), 0.5, 0.38, M.ochre, n=12, smooth=False)
            for i in range(14):
                a = TAU * i / 14
                g.box((math.cos(a) * 0.71, math.sin(a) * 0.71, 0), (0.08, 0.16, 0.38), M.rubber, rz=a + 0.5)
        g.box((sx * 0.62, 0.55, 1.5), (0.42, 0.9, 0.04), body, rx=0.0, bevel=0.01)  # fender
        with g.at((sx * 0.42, -1.0, 0.36), ry=PI / 2):                       # front wheels
            g.cyl((0, 0, -0.08), 0.36, 0.16, M.rubber, n=12, smooth=False)
            g.cyl((0, 0, -0.09), 0.22, 0.18, M.ochre, n=10, smooth=False)
    g.box((0, -1.0, 0.45), (0.9, 0.12, 0.12), M.iron)
    g.collide((0, -0.2, 0.8), (1.7, 2.9, 1.6))


def wheelbarrow_geo(g, M, load=None, seed=0):
    rng = random.Random(seed)
    with g.at((0, -0.05, 0.42)):
        g.box((0, 0, 0), (0.62, 0.8, 0.03), M.rust)
        for sx in (-1, 1):
            g.box((sx * 0.36, 0, 0.14), (0.03, 0.85, 0.3), M.rust, ry=sx * 0.3)
        g.box((0, -0.45, 0.14), (0.66, 0.03, 0.3), M.rust, rx=-0.45)
        g.box((0, 0.42, 0.12), (0.66, 0.03, 0.26), M.rust, rx=0.2)
    spoked_wheel(g, (0, -0.72, 0.22), 0.22, M, spokes=8)
    for sx in (-1, 1):
        g.box((sx * 0.25, 0.0, 0.33), (0.05, 1.7, 0.05), M.wood_mid, rx=-0.12)
        g.box((sx * 0.25, 0.55, 0.15), (0.05, 0.05, 0.3), M.wood_mid)
    if load == 'pumpkins':
        for i in range(3):
            pumpkin(g, M, (rng.uniform(-0.15, 0.15), -0.15 + i * 0.2, 0.47), 0.17, rng.uniform(0, 6), 0.2)
    elif load == 'wood':
        for i in range(6):
            g.cyl((-0.25 + (i % 3) * 0.17, -0.4, 0.52 + (i // 3) * 0.13), 0.06, 0.75, M.wood_mid, n=6, rx=-PI / 2 + 0.05)
    elif load == 'leaves':
        g.blob((0, -0.05, 0.55), 0.38, M.leaf_orange, seed=seed, jitter=0.25, subdiv=1, s=(0.9, 1.15, 0.45))


# ======================================================================== altar

def altar(g, M):
    """Relic altar: a mossy pedestal crowned by an old millstone with a teal rune ring."""
    g.cyl((0, 0, 0), 0.5, 0.14, M.stone, n=8, smooth=False, rz=PI / 8)
    g.cyl((0, 0, 0.14), 0.36, 0.46, M.stone, n=8, r2=0.31, smooth=False, rz=PI / 8)
    g.cyl((0, 0, 0.6), 0.58, 0.2, M.millstone, n=18, smooth=False)
    for i in range(6):
        a = TAU * i / 6
        g.box((math.cos(a) * 0.36, math.sin(a) * 0.36, 0.805), (0.36, 0.03, 0.012), M.stone, rz=a + 0.45)
    g.torus((0, 0, 0.81), 0.44, 0.022, M.altar_glow, n=24, m=4)
    g.cyl((0, 0, 0.8), 0.12, 0.02, M.iron, n=10)
    g.blob((0.33, 0.1, 0.12), 0.12, M.moss, seed=3, jitter=0.3, subdiv=0, s=(1.2, 1.0, 0.5))
    g.collide((0, 0, 0.4), (1.0, 1.0, 0.8))
    return 0.83


# ======================================================================== props

def barn_door(p, M, w=2.3, h=3.9, ext=1, rest=1.75, t=0.09):
    """Hinged barn door leaf hung on the outside of a wall along X (outside = -Y).
    Origin = hinge line at the floor. ext=+1: shut leaf extends toward +X."""
    d = -ext
    pv = p.part('pivot', rz=d * rest)
    g = pv.geo
    cx = ext * w / 2
    g.box((cx, 0, h / 2), (w - 0.02, t, h), M.barn_red, bevel=0.01)
    for fy in (-1, 1):
        y = fy * (t / 2 + 0.012)
        for sx in (0.1, w - 0.1):
            g.box((ext * sx, y, h / 2), (0.18, 0.025, h), M.paint_white)
        for z in (0.1, h / 2, h - 0.1):
            g.box((cx, y, z), (w, 0.025, 0.18), M.paint_white)
        for z0, z1 in ((0.15, h / 2 - 0.05), (h / 2 + 0.05, h - 0.15)):
            ang = math.atan2(z1 - z0, w - 0.36)
            ln = math.hypot(z1 - z0, w - 0.36)
            g.box((cx, y, (z0 + z1) / 2), (ln, 0.024, 0.16), M.paint_white, ry=-ang * ext)
    for z in (0.55, h - 0.55):
        g.box((ext * 0.45, -t / 2 - 0.03, z), (0.9, 0.012, 0.07), M.iron)
        g.cyl((0, -t / 2 - 0.03, z - 0.08), 0.03, 0.16, M.iron, n=6)
    g.torus((ext * (w - 0.35), -t / 2 - 0.05, h * 0.48), 0.07, 0.012, M.iron, n=10, m=4, rx=PI / 2)
    p.params.update(axis='y', dir=d, closed=round(-rest, 4), open=1.1, sound='bang')


def plank_door(p, M, w=0.9, h=2.1, ext=1, rest=0.0, t=0.06, mat=None, moon=False, screen=False, frame=None):
    """Simple hinged plank door (outhouse, coop, side doors). Origin = hinge at the floor; wall along X."""
    mat = mat or M.grey_wood
    d = -ext
    pv = p.part('pivot', rz=d * rest)
    g = pv.geo
    cx = ext * w / 2
    if screen:
        for sx in (0.05, w - 0.05):
            g.box((ext * sx, 0, h / 2), (0.1, t, h), mat, bevel=0.008)
        for z in (0.06, h * 0.42, h - 0.06):
            g.box((cx, 0, z), (w, t, 0.12), mat, bevel=0.008)
        g.box((cx, 0, h * 0.21), (w - 0.1, 0.012, h * 0.36), M.screen)
        g.box((cx, 0, h * 0.71), (w - 0.1, 0.012, h * 0.52), M.screen)
        g.box((ext * w * 0.5, 0, h * 0.62), (w * 0.4, t * 0.8, 0.06), mat)  # push bar
        g.sphere((ext * (w - 0.12), -t, h * 0.45), 0.03, M.tin, n=6)
    else:
        n = max(3, int(w / 0.15))
        for i in range(n):
            g.box((ext * (w * (i + 0.5) / n), 0, h / 2), (w / n - 0.008, t, h - 0.02 * (i % 2)), mat, bevel=0.006)
        for fy in (-1, 1):
            for z in (0.25, h - 0.3):
                g.box((cx, fy * (t / 2 + 0.012), z), (w - 0.06, 0.025, 0.12), mat)
            ang = math.atan2(h - 0.55, w - 0.1)
            g.box((cx, fy * (t / 2 + 0.012), h / 2 - 0.02), (math.hypot(h - 0.55, w - 0.1), 0.024, 0.11), mat,
                  ry=-ang * ext)
        if moon:
            g.box((cx, -t / 2 - 0.004, h - 0.42), (0.17, 0.012, 0.17), M.wood_dk)
            g.cyl((cx + ext * 0.04, -t / 2 - 0.012, h - 0.42), 0.075, 0.01, M.window_glow_dim, n=10, rx=PI / 2)
            g.cyl((cx + ext * 0.075, -t / 2 - 0.02, h - 0.42), 0.065, 0.01, M.wood_dk, n=10, rx=PI / 2)
        g.torus((ext * (w - 0.12), -t / 2 - 0.03, h * 0.48), 0.04, 0.008, M.iron, n=8, m=3, rx=PI / 2)
    if frame is not None:
        for sx in (-0.05, w + 0.05):
            p.body.box((ext * sx, 0, h / 2), (0.1, t + 0.14, h + 0.1), frame)
        p.body.box((cx, 0, h + 0.05), (w + 0.2, t + 0.14, 0.1), frame)
    p.params.update(axis='y', dir=d, closed=round(-rest, 4), sound='bang')


def farm_gate(p, M, w=2.6, h=1.15, ext=1, rest=1.4):
    """Five-bar field gate. Origin = hinge post at the ground; shut gate spans along X."""
    d = -ext
    p.body.box((0, 0, (h + 0.25) / 2), (0.16, 0.16, h + 0.25), M.wood_dk, bevel=0.015)
    p.body.collide((0, 0, (h + 0.25) / 2), (0.18, 0.18, h + 0.25))
    pv = p.part('pivot', (0, 0, 0), rz=d * rest)
    g = pv.geo
    for i in range(5):
        z = 0.22 + i * (h - 0.3) / 4
        g.box((ext * w / 2, 0, z), (w - 0.1, 0.05, 0.1), M.grey_wood)
    for sx in (0.08, w - 0.08):
        g.box((ext * sx, 0, h / 2 + 0.06), (0.1, 0.07, h), M.grey_wood)
    ang = math.atan2(h - 0.3, w - 0.3)
    g.box((ext * w / 2, 0.05, h / 2 + 0.06), (math.hypot(h - 0.3, w - 0.3), 0.04, 0.09), M.grey_wood, ry=-ang * ext)
    for z in (0.25, h - 0.05):
        g.box((ext * 0.12, 0.0, z), (0.2, 0.09, 0.04), M.iron)
    p.params.update(axis='y', dir=d, closed=round(-rest, 4), sound='bang')


def stall_gate(p, M, w=1.6, h=1.35, ext=1, rest=1.3):
    d = -ext
    pv = p.part('pivot', rz=d * rest)
    g = pv.geo
    n = 6
    for i in range(n):
        g.box((ext * (w * (i + 0.5) / n), 0, 0.35), (w / n - 0.01, 0.05, 0.62), M.barn_in, bevel=0.005)
    for z in (0.05, 0.68, h):
        g.box((ext * w / 2, 0, z), (w, 0.07, 0.09), M.wood_mid, bevel=0.01)
    for i in range(1, 8):
        g.cyl((ext * w * i / 8, 0, 0.7), 0.015, h - 0.7, M.iron, n=5)
    for sx in (0.04, w - 0.04):
        g.box((ext * sx, 0, h / 2), (0.08, 0.08, h), M.wood_mid)
    p.params.update(axis='y', dir=d, closed=round(-rest, 4), sound='bang')


def shutter(p, M, w=0.55, h=1.45, ext=1, rest=2.0):
    """Loose louvred window shutter. Origin = hinge at the bottom of the window edge (wall along X)."""
    d = -ext
    pv = p.part('pivot', rz=d * rest)
    g = pv.geo
    cx = ext * w / 2
    for sx in (0.04, w - 0.04):
        g.box((ext * sx, 0, h / 2), (0.08, 0.04, h), M.trim_green)
    for z in (0.04, h / 2, h - 0.04):
        g.box((cx, 0, z), (w, 0.04, 0.08), M.trim_green)
    z = 0.12
    while z < h - 0.1:
        if abs(z - h / 2) > 0.07:
            g.box((cx, 0, z), (w - 0.12, 0.012, 0.07), M.trim_green, rx=0.5)
        z += 0.075
    g.box((ext * 0.1, -0.03, 0.25), (0.2, 0.01, 0.04), M.iron)
    g.box((ext * 0.1, -0.03, h - 0.25), (0.2, 0.01, 0.04), M.iron)
    p.params.update(axis='y', dir=d, closed=round(-rest, 4), sound='bang')


def hayloft_door(p, M, w=1.5, h=1.6, rest=0.45):
    plank_door(p, M, w=w, h=h, ext=1, rest=rest, t=0.07, mat=M.barn_red)
    pv = p.parts['pivot'].geo
    for fy in (-1,):
        y = fy * 0.05
        for z in (0.08, h - 0.08):
            pv.box((w / 2, y, z), (w, 0.02, 0.12), M.paint_white)
        for sx in (0.06, w - 0.06):
            pv.box((sx, y, h / 2), (0.12, 0.02, h), M.paint_white)
    p.params.update(sound='bang')


def weathervane(p, M):
    """Rooster weathervane: body = rod + compass arms, pivot = rooster and arrow (spins about Z)."""
    b = p.body
    b.cyl((0, 0, 0), 0.025, 1.25, M.iron, n=6)
    b.sphere((0, 0, 0.55), 0.06, M.brass, n=8)
    for a in range(4):
        ang = a * PI / 2
        b.box((math.cos(ang) * 0.24, math.sin(ang) * 0.24, 0.7), (0.48, 0.018, 0.018), M.iron, rz=ang)
        b.sphere((math.cos(ang) * 0.48, math.sin(ang) * 0.48, 0.7), 0.035, M.brass, n=6)
    pv = p.part('pivot', (0, 0, 1.0))
    g = pv.geo
    g.box((0.05, 0, 0.0), (1.1, 0.02, 0.025), M.iron)
    g.prism((0.58, 0.012, -0.08), [(0, 0), (0.16, 0.08), (0, 0.16)], 0.024, M.iron, rx=PI / 2)  # arrow head
    g.prism((-0.55, 0.012, -0.1), [(0, 0), (0.1, 0.1), (0.0, 0.2), (-0.12, 0.2), (-0.02, 0.1), (-0.12, 0.0)], 0.024,
            M.iron, rx=PI / 2)  # fletching
    rooster = [(0.0, 0.0), (0.06, 0.0), (0.05, 0.08), (0.12, 0.12), (0.18, 0.2), (0.2, 0.3), (0.27, 0.32), (0.21, 0.355),
               (0.225, 0.41), (0.17, 0.42), (0.15, 0.37), (0.12, 0.28), (0.0, 0.22), (-0.12, 0.24), (-0.2, 0.36),
               (-0.31, 0.43), (-0.27, 0.28), (-0.22, 0.17), (-0.1, 0.1), (-0.02, 0.08)]
    g.prism((0.05, 0.015, 0.012), [(x * 1.4, z * 1.4) for x, z in rooster], 0.03, M.iron, rx=PI / 2)
    p.params.update(axis='y', speed=0.0, wobble=0.18, sound='squeak')


def hay_hook(p, M, drop=2.6):
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0, -0.18), 0.1, 0.06, M.wood_dk, n=10, rx=PI / 2)
    g.box((0, 0, -0.06), (0.05, 0.08, 0.16), M.iron)
    for sx in (-0.06, 0.06):
        g.cyl((sx, 0, -drop + 0.2), 0.012, drop - 0.35, M.rope, n=4)
    g.box((0, 0, -drop + 0.14), (0.2, 0.1, 0.14), M.wood_dk, bevel=0.02)
    g.tube([(0, 0, -drop + 0.08), (0, 0, -drop - 0.15), (0.04, 0, -drop - 0.3), (0.16, 0, -drop - 0.28),
            (0.2, 0, -drop - 0.18)], 0.018, M.iron, n=5)
    p.params.update(axes='xz', amp=0.03, period=3.2, sound='creak')


def hanging_lantern(p, M, drop=0.7, light=True, intensity=1.3, dist=8.0):
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0, -drop), 0.008, drop, M.iron, n=4)
    z = -drop
    g.torus((0, 0, z - 0.03), 0.035, 0.008, M.iron, n=8, m=4, rx=PI / 2)
    g.lathe((0, 0, z - 0.4), [(0.09, 0), (0.11, 0.02), (0.11, 0.05), (0.085, 0.07), (0.085, 0.29), (0.12, 0.31),
                              (0.03, 0.4)], M.iron, n=6, smooth=False)
    g.cyl((0, 0, z - 0.34), 0.078, 0.23, M.lantern_glass, n=6, smooth=False)
    for i in range(3):
        a = TAU * i / 3
        g.box((math.cos(a) * 0.085, math.sin(a) * 0.085, z - 0.22), (0.012, 0.012, 0.26), M.iron)
    p.flame((0, 0, z - 0.3), size=0.75, parent='pivot')
    if light:
        p.light((0, 0, z - 0.25), '#ffb35c', intensity, dist, part='pivot')
    p.params.update(amp=0.035, period=2.2, sound='creak')


def horse_collar(p, M):
    """Horse collar and harness hanging from a wall peg (pivot at the peg, wall behind at +Y)."""
    p.body.cyl((0, 0.12, 0), 0.025, 0.14, M.wood_dk, n=6, rx=PI / 2)
    pv = p.part('pivot', (0, -0.02, 0))
    g = pv.geo
    with g.at((0, -0.04, -0.42), rx=PI / 2):
        g.torus((0, 0, 0), 0.26, 0.07, M.leather, n=14, m=6)
    g.torus((0, -0.04, -0.42), 0.32, 0.03, M.brass, n=14, m=4, rx=PI / 2, arc=PI)
    g.tube([(-0.2, -0.04, -0.6), (-0.3, -0.03, -1.0), (-0.2, -0.02, -1.25)], 0.02, M.leather, n=4)
    g.tube([(0.2, -0.04, -0.6), (0.32, -0.03, -0.95), (0.26, -0.02, -1.2)], 0.02, M.leather, n=4)
    g.cyl((0, -0.02, -0.12), 0.012, 0.14, M.leather, n=4)
    p.params.update(axes='z', amp=0.01, period=2.4, sound='creak')


def hay_bale(p, M, rz=0.0):
    pv = p.part('pivot')
    hay_bale_geo(pv.geo, M)
    p.body.collide((0, 0, 0.22), (1.0, 0.5, 0.44))
    p.params.update(sound='thud')


def milk_can(p, M):
    pv = p.part('pivot')
    g = pv.geo
    g.lathe((0, 0, 0), [(0.16, 0), (0.17, 0.02), (0.17, 0.42), (0.15, 0.47), (0.085, 0.56), (0.08, 0.62),
                        (0.095, 0.64), (0.095, 0.66)], M.tin, n=14)
    g.lathe((0, 0, 0.66), [(0.1, 0), (0.1, 0.04), (0.05, 0.07), (0.02, 0.1)], M.tin, n=12)
    for sx in (-1, 1):
        g.torus((sx * 0.13, 0, 0.5), 0.05, 0.01, M.tin, n=8, m=3, ry=PI / 2)
    g.torus((0, 0, 0.12), 0.17, 0.012, M.tin, n=14, m=3)
    p.body.collide((0, 0, 0.35), (0.36, 0.36, 0.7))
    p.params.update(sound='clatter')


def feed_sacks(p, M, n=3, seed=0):
    rng = random.Random(seed)
    pv = p.part('pivot')
    for i in range(n):
        sack_geo(pv.geo, M, (-0.28 + i * 0.3, rng.uniform(-0.1, 0.1), 0 if i < 2 or n < 3 else 0.0), rng.uniform(-0.4, 0.4),
                 rng.uniform(0.9, 1.05), mat=M.burlap if i % 2 == 0 else M.sack_pale)
    if n >= 3:
        sack_geo(pv.geo, M, (-0.1, 0.05, 0.38), 1.3, 0.85, M.sack_pale)
    p.body.collide((0, 0, 0.3), (0.95, 0.55, 0.6))
    p.params.update(sound='thud')


def crate_prop(p, M, s=0.6, apples=False):
    pv = p.part('pivot')
    crate_geo(pv.geo, M, s, apples=apples)
    p.body.collide((0, 0, s / 2), (s, s * 0.8, s))
    p.params.update(sound='thud')


def barrel_prop(p, M, h=0.9, r=0.32, lid=True):
    pv = p.part('pivot')
    g = pv.geo
    g.lathe((0, 0, 0), [(r * 0.85, 0), (r, h * 0.25), (r * 1.06, h / 2), (r, h * 0.75), (r * 0.85, h)], M.wood_mid, n=12)
    for z in (0.1, 0.3, 0.7, 0.9):
        rr = r * (0.85 + 0.21 * math.sin(PI * z))
        g.torus((0, 0, z * h), rr + 0.008, 0.012, M.iron, n=12, m=3)
    p.body.collide((0, 0, h / 2), (r * 2, r * 2, h))
    p.params.update(sound='thud')


def basket_prop(p, M, kind='apples', seed=0):
    rng = random.Random(seed)
    pv = p.part('pivot')
    g = pv.geo
    g.lathe((0, 0, 0), [(0.2, 0), (0.27, 0.28), (0.29, 0.3)], M.wicker, n=12, cap_top=False)
    g.lathe((0, 0, 0.02), [(0.27, 0.28), (0.19, 0.0)], M.wicker, n=12, cap_bottom=False, cap_top=False)
    g.torus((0, 0, 0.3), 0.29, 0.02, M.wicker, n=12, m=4)
    g.tube([(-0.26, 0, 0.3), (-0.2, 0, 0.55), (0.2, 0, 0.55), (0.26, 0, 0.3)], 0.015, M.wicker, n=4, caps=False)
    if kind == 'apples':
        for i in range(10):
            a = rng.uniform(0, TAU)
            d = rng.uniform(0, 0.2)
            g.sphere((math.cos(a) * d, math.sin(a) * d, 0.26 + rng.uniform(0, 0.06)), 0.05, M.apple, n=6)
    elif kind == 'laundry':
        for i in range(3):
            g.box((rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 0.2 + i * 0.05), (0.36, 0.3, 0.05),
                  rng.choice((M.cloth_white, M.cloth_sage, M.cloth_rose)), rz=rng.uniform(-0.4, 0.4), bevel=0.02)
        g.box((0.05, 0.0, 0.36), (0.3, 0.26, 0.04), M.quilt, rz=0.3, bevel=0.015)
    elif kind == 'eggs':
        g.cyl((0, 0, 0.12), 0.24, 0.02, M.straw, n=10)
        for i in range(8):
            a = rng.uniform(0, TAU)
            d = rng.uniform(0, 0.16)
            g.sphere((math.cos(a) * d, math.sin(a) * d, 0.17), 0.035, M.egg, n=6, s=(1, 1, 1.3))
    p.body.collide((0, 0, 0.18), (0.55, 0.55, 0.36))
    p.params.update(sound='thud')


def wash_tub(p, M):
    pv = p.part('pivot')
    g = pv.geo
    g.lathe((0, 0, 0), [(0.3, 0), (0.38, 0.32), (0.4, 0.34)], M.tin, n=14, cap_top=False)
    g.cyl((0, 0, 0.24), 0.36, 0.01, M.water, n=14)
    with g.at((0.12, 0.05, 0.2), rx=0.35, rz=0.4):
        g.box((0, 0, 0.25), (0.34, 0.03, 0.6), M.wood_light, bevel=0.01)
        for i in range(9):
            g.box((0, -0.02, 0.05 + i * 0.045), (0.26, 0.02, 0.018), M.tin)
    g.box((-0.2, -0.1, 0.27), (0.3, 0.25, 0.03), M.cloth_white, rz=0.2, ry=0.2)
    p.body.collide((0, 0, 0.17), (0.8, 0.8, 0.34))
    p.params.update(sound='splash')


def chopping_block(p, M):
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0, 0), 0.3, 0.52, M.bark, n=9, smooth=False)
    g.cyl((0, 0, 0.52), 0.28, 0.015, M.wood_light, n=9)
    with g.at((0.05, 0, 0.6), ry=-0.55):
        g.box((0, 0, 0), (0.18, 0.03, 0.1), M.iron)
        g.cyl((-0.07, 0, 0.0), 0.02, 0.7, M.wood_light, n=5, ry=-PI / 2 + 0.25)
    for i in range(4):
        g.box((0.4 + i * 0.07, -0.25 + i * 0.13, 0.05), (0.08, 0.3, 0.08), M.wood_light, rz=i * 0.9, bevel=0.01)
    p.body.collide((0, 0, 0.27), (0.6, 0.6, 0.54))
    p.params.update(sound='thud')


def wheelbarrow(p, M, load=None, seed=0):
    pv = p.part('pivot')
    wheelbarrow_geo(pv.geo, M, load, seed)
    p.body.collide((0, -0.1, 0.35), (0.8, 1.7, 0.7))
    p.params.update(sound='rattle')


def prize_pumpkin(p, M):
    pv = p.part('pivot')
    pumpkin(pv.geo, M, (0, 0, 0), 0.62, 0.4, ribs=10)
    pv.geo.box((0.0, -0.6, 0.25), (0.5, 0.02, 0.3), M.wood_light, rx=-0.15)
    pv.geo.box((0.0, -0.61, 0.25), (0.15, 0.02, 0.15), M.ribbon, rx=-0.15)
    p.body.collide((0, 0, 0.4), (1.2, 1.2, 0.8))
    p.params.update(sound='thud')


def kitchen_chair(p, M, tipped=False):
    pv = p.part('pivot', (0, 0.2, 0) if tipped else (0, 0, 0), rx=-(PI / 2 - 0.1) if tipped else 0.0)
    g = Geo_off(pv.geo, (0, -0.2, 0) if tipped else (0, 0, 0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box((sx * 0.19, sy * 0.18, 0.22), (0.04, 0.04, 0.44), M.wood_mid)
        g.box((sx * 0.19, 0.19, 0.72), (0.04, 0.04, 0.58), M.wood_mid, rx=-0.06)
    g.box((0, 0, 0.46), (0.46, 0.44, 0.04), M.wood_mid, bevel=0.01)
    for i in range(3):
        g.box((0, 0.2, 0.62 + i * 0.13), (0.38, 0.02, 0.05), M.wood_mid, rx=-0.06)
    if not tipped:
        p.body.collide((0, 0, 0.45), (0.46, 0.44, 0.9))
    p.params.update(sound='clatter')


def scarecrow(p, M, shirt=None, hat='straw', seed=0):
    rng = random.Random(seed)
    shirt = shirt or M.plaid
    b = p.body
    b.cyl((0, 0, 0), 0.05, 1.62, M.wood_mid, n=6, smooth=False)
    b.box((0, 0.02, 1.5), (1.55, 0.07, 0.07), M.wood_mid, ry=rng.uniform(-0.05, 0.05))
    b.box((0, 0, 1.17), (0.48, 0.27, 0.62), shirt, bevel=0.07)
    b.box((0, 0, 0.88), (0.5, 0.29, 0.06), M.rope)
    for sx in (-1, 1):
        b.box((sx * 0.46, 0, 1.46), (0.5, 0.21, 0.21), shirt, ry=sx * 0.14, bevel=0.05)
        b.cyl((sx * 0.7, 0, 1.42), 0.09, 0.2, M.straw, n=6, r2=0.015, ry=sx * PI / 2 + sx * 0.25, smooth=False)
        b.box((sx * 0.13, 0, 0.56), (0.19, 0.21, 0.62), M.denim, ry=sx * 0.06, bevel=0.03)
        b.cyl((sx * 0.15, 0, 0.27), 0.07, 0.16, M.straw, n=6, r2=0.012, rx=PI, smooth=False)
    b.box((0.12, -0.14, 1.25), (0.12, 0.012, 0.12), M.patch)  # patch
    hd = p.part('pivot', (0, 0, 1.52))
    g = hd.geo
    g.sphere((0, 0, 0.23), 0.19, M.burlap, n=10, s=(1, 0.95, 1.1))
    for sx in (-1, 1):
        g.box((sx * 0.07, -0.175, 0.27), (0.07, 0.02, 0.016), M.iron, ry=PI / 4)
        g.box((sx * 0.07, -0.175, 0.27), (0.07, 0.02, 0.016), M.iron, ry=-PI / 4)
    g.box((0, -0.18, 0.15), (0.14, 0.02, 0.014), M.iron, ry=0.08)
    for i in range(5):
        g.box((-0.06 + i * 0.03, -0.182, 0.15), (0.008, 0.02, 0.04), M.iron)
    g.torus((0, 0, 0.06), 0.1, 0.022, M.rope, n=10, m=4)
    hm = M.straw if hat == 'straw' else M.felt
    with g.at((0, 0, 0.36), rx=rng.uniform(-0.12, 0.12), ry=rng.uniform(-0.15, 0.15)):
        g.cyl((0, 0, 0), 0.34, 0.025, hm, n=12)
        g.cyl((0, 0, 0.02), 0.16, 0.2, hm, n=10, r2=0.13)
        g.cyl((0, 0, 0.03), 0.165, 0.05, M.ribbon if hat == 'straw' else M.iron, n=10)
    for i in range(7):
        a = rng.uniform(0, TAU)
        g.add(prim_blade(0.16, 0.03, up=0.2, droop=1.2, seg=2), M.straw, _mat((math.cos(a) * 0.14, math.sin(a) * 0.14, 0.3), a))
    p.body.collide((0, 0, 0.9), (0.25, 0.25, 1.8))
    p.params.update(axis='y', speed=0.0, wobble=0.035, sound='creak')


def jack_o_lantern(p, M, r=0.26, face=0, light=None, lid=True):
    """Carved pumpkin with a candle flame peeking out of the cut top."""
    h = r * 1.3
    b = p.body
    b.add(prim_pumpkin(r, h, ribs=8, depth=0.1), M.pumpkin)
    b.cyl((0, 0, h * 0.9), r * 0.42, 0.02, M.jack_glow, n=10)
    fz = h * 0.52

    def cut(cx, cz, poly, depth=0.07):
        k = r
        yy = -math.sqrt(max(0.0, r * r - (cx * k) ** 2)) * 0.98
        b.prism((cx * k, yy + depth * 0.6, fz + cz * k), [(x * k, z * k) for x, z in poly], depth, M.jack_glow, rx=PI / 2)
    tri = [(-0.13, -0.08), (0.13, -0.08), (0.0, 0.12)]
    if face == 0:
        cut(-0.36, 0.2, tri)
        cut(0.36, 0.2, tri)
        cut(0.0, 0.0, [(-0.06, -0.05), (0.06, -0.05), (0.0, 0.06)])
        cut(0.0, -0.28, [(-0.5, 0.06), (-0.3, -0.14), (0.0, -0.2), (0.3, -0.14), (0.5, 0.06), (0.25, -0.03),
                         (0.15, 0.04), (0.05, -0.05), (-0.05, -0.05), (-0.15, 0.04), (-0.25, -0.03)])
    elif face == 1:
        cut(-0.34, 0.18, [(-0.14, -0.1), (0.12, -0.1), (0.12, 0.06), (-0.14, 0.12)])
        cut(0.34, 0.18, [(-0.12, -0.1), (0.14, -0.1), (0.14, 0.12), (-0.12, 0.06)])
        cut(0.0, -0.25, [(-0.42, 0.0), (-0.2, -0.16), (0.2, -0.16), (0.42, 0.0), (0.2, -0.06), (-0.2, -0.06)])
    else:
        cut(-0.33, 0.2, [(-0.1, -0.1), (0.1, -0.1), (0.1, 0.1), (-0.1, 0.1)])
        cut(0.33, 0.14, [(-0.08, -0.08), (0.08, -0.08), (0.08, 0.08), (-0.08, 0.08)])
        cut(0.0, -0.26, [(-0.36, -0.04), (0.36, -0.04), (0.3, 0.05), (-0.3, 0.05)])
    if lid:
        with b.at((r * 1.05, r * 0.45, 0.0), ry=0.5):
            b.sphere((0, 0, 0.05), r * 0.42, M.pumpkin, n=10, s=(1, 1, 0.38))
            b.cyl((0, 0, 0.08), r * 0.08, r * 0.3, M.stem, n=5, r2=r * 0.05, smooth=False)
    b.cyl((0, 0, h * 0.55), 0.025, h * 0.32, M.wax, n=6)
    p.flame((0, 0, h * 0.86), size=0.55)
    if light:
        p.light((0, -r * 1.6, h * 0.7), '#ff9a40', light, 5.5, part='flame0')
    p.body.collide((0, 0, h / 2), (r * 2, r * 2, h))
    p.params.update(sound='whoomp')


def crow(p, M, perch_h=0.0, look=0.0):
    pv = p.part('pivot', (0, 0, perch_h), rz=look)
    g = pv.geo
    g.sphere((0, 0.01, 0.13), 0.075, M.crow, n=8, s=(0.78, 1.55, 0.85), rx=-0.25)
    g.sphere((0, -0.1, 0.22), 0.05, M.crow, n=8)
    g.cyl((0, -0.135, 0.215), 0.018, 0.07, M.beak, n=4, r2=0.002, rx=PI / 2 + 0.1)
    g.box((0, 0.15, 0.09), (0.07, 0.14, 0.012), M.crow, rx=0.45)
    for sx in (-1, 1):
        g.sphere((sx * 0.05, 0.03, 0.14), 0.055, M.crow, n=6, s=(0.3, 1.7, 0.6), rx=-0.25)
        g.cyl((sx * 0.025, 0.0, 0.0), 0.006, 0.07, M.beak, n=3)
        g.sphere((sx * 0.033, -0.125, 0.235), 0.008, M.brass, n=4)
    p.params.update(amp=0.006, sound='caw')


def laundry_line(p, M, length=6.0, H=2.05, sag=0.14, items=(), seed=0):
    """Clothesline between two T-posts along X; items hang from the rope as cloth parts.
    items: [(kind, x, material)], kind in sheet/shirt/pants/towel/socks/dress/quilt."""
    rng = random.Random(seed)
    b = p.body
    L = length
    for sx in (-1, 1):
        x = sx * L / 2
        b.box((x, 0, (H + 0.25) / 2), (0.1, 0.1, H + 0.25), M.grey_wood)
        b.box((x, 0, H + 0.12), (0.08, 0.7, 0.08), M.grey_wood)
        b.box((x, 0.2, H - 0.15), (0.05, 0.4, 0.05), M.grey_wood, rx=0.8)
        b.box((x, -0.2, H - 0.15), (0.05, 0.4, 0.05), M.grey_wood, rx=-0.8)
        b.collide((x, 0, (H + 0.25) / 2), (0.14, 0.14, H + 0.25))
    pts = []
    for i in range(13):
        x = -L / 2 + L * i / 12
        pts.append((x, 0, H + 0.1 - sag * (1 - (2 * x / L) ** 2)))
    b.tube(pts, 0.008, M.rope, n=4, caps=False)
    for i, (kind, x, mat) in enumerate(items):
        zt = H + 0.1 - sag * (1 - (2 * x / L) ** 2) - 0.01
        g = p.geo(f'cloth{i}', (x, 0, zt))
        if kind == 'sheet':
            g.sheet((0, 0, 0), 1.35, 1.55, mat, nx=8, ny=8)
            pins = (-0.6, 0.0, 0.6)
        elif kind == 'quilt':
            g.sheet((0, 0, 0), 1.25, 1.35, mat, nx=8, ny=8)
            pins = (-0.55, 0.55)
        elif kind == 'shirt':
            g.sheet((0, 0, 0), 0.6, 0.74, mat, nx=6, ny=6)
            for sx in (-1, 1):
                g.sheet((sx * 0.42, 0, 0), 0.24, 0.24, mat, nx=2, ny=2)
            pins = (-0.27, 0.27)
        elif kind == 'dress':
            g.sheet((0, 0, 0), 0.5, 0.3, mat, nx=4, ny=2)
            g.sheet((0, 0, -0.3), 0.8, 0.8, mat, nx=6, ny=6)
            pins = (-0.22, 0.22)
        elif kind == 'pants':
            g.sheet((0, 0, 0), 0.5, 0.14, mat, nx=4, ny=2)
            for sx in (-1, 1):
                g.sheet((sx * 0.13, 0, -0.14), 0.23, 0.82, mat, nx=2, ny=6)
            pins = (-0.22, 0.22)
        elif kind == 'towel':
            g.sheet((0, 0, 0), 0.55, 0.75, mat, nx=4, ny=6)
            pins = (-0.24, 0.24)
        else:  # socks
            for sx in (-1, 1):
                g.sheet((sx * 0.1, 0, 0), 0.1, 0.32, mat, nx=1, ny=4)
            pins = (-0.1, 0.1)
        for px in pins:
            b.box((x + px, 0, zt + 0.005), (0.018, 0.03, 0.07), M.wood_light)
    p.params.update(amp=0.05, sound='whoosh')


def porch_swing(p, M, w=1.45, drop=1.95):
    pv = p.part('pivot')
    g = pv.geo
    z = -drop
    g.box((0, 0, z), (w, 0.5, 0.05), M.paint_sage, bevel=0.01)
    for i in range(5):
        g.box((-w / 2 + 0.1 + i * (w - 0.2) / 4, 0.25, z + 0.3), (0.08, 0.03, 0.5), M.paint_sage, rx=-0.18)
    g.box((0, 0.3, z + 0.56), (w, 0.05, 0.08), M.paint_sage, rx=-0.18)
    g.box((0, 0.21, z + 0.06), (w, 0.04, 0.08), M.paint_sage, rx=-0.18)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.03), 0.0, z + 0.22), (0.05, 0.48, 0.05), M.paint_sage)
        g.box((sx * (w / 2 - 0.03), -0.2, z + 0.11), (0.05, 0.05, 0.22), M.paint_sage)
        g.tube([(sx * (w / 2 - 0.03), -0.22, z + 0.22), (sx * (w / 2 - 0.08), -0.05, -0.04)], 0.007, M.iron, n=3)
        g.tube([(sx * (w / 2 - 0.03), 0.3, z + 0.6), (sx * (w / 2 - 0.08), 0.05, -0.04)], 0.007, M.iron, n=3)
    g.box((-0.25, 0.02, z + 0.07), (0.5, 0.42, 0.08), M.cushion, bevel=0.03)
    g.box((0.42, 0.0, z + 0.05), (0.45, 0.42, 0.06), M.quilt, bevel=0.02, rz=0.15)
    p.params.update(axes='x', amp=0.035, period=3.1, sound='creak')


def wind_chimes(p, M, drop=0.22):
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0, -drop), 0.003, drop, M.rope, n=3)
    z = -drop - 0.03
    g.cyl((0, 0, z), 0.09, 0.03, M.wood_mid, n=10)
    for i in range(6):
        a = TAU * i / 6
        L = 0.24 + 0.05 * ((i * 3) % 5)
        x, y = math.cos(a) * 0.065, math.sin(a) * 0.065
        g.cyl((x, y, z - 0.04), 0.002, 0.04, M.rope, n=3)
        g.cyl((x, y, z - 0.04 - L), 0.009, L, M.tin, n=6)
    g.cyl((0, 0, z - 0.3), 0.002, 0.3, M.rope, n=3)
    g.cyl((0, 0, z - 0.26), 0.035, 0.012, M.wood_mid, n=8)
    g.cyl((0, 0, z - 0.52), 0.002, 0.24, M.rope, n=3)
    g.box((0, 0, z - 0.6), (0.09, 0.006, 0.14), M.wood_mid)
    p.params.update(axes='xz', amp=0.06, period=1.5, sound='jingle')


def tire_swing(p, M, drop=3.65):
    pv = p.part('pivot')
    g = pv.geo
    g.torus((0, 0, 0.09), 0.1, 0.025, M.rope, n=8, m=4, rx=PI / 2, rz=PI / 2)
    g.cyl((0, 0, -drop + 0.4), 0.02, drop - 0.4, M.rope, n=5)
    g.torus((0, 0, -drop), 0.32, 0.11, M.rubber, n=16, m=6, rx=PI / 2)
    g.torus((0, 0, -drop + 0.43), 0.04, 0.015, M.rope, n=6, m=3, rx=PI / 2)
    p.params.update(axes='xz', amp=0.05, period=3.8, sound='creak')


def well_crank(p, M, span=1.6):
    """Windlass drum between the well posts (axle along X) with a crank on +X."""
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((-span / 2, 0, 0), 0.11, span, M.wood_mid, n=10, ry=PI / 2)
    g.cyl((-span / 2 - 0.1, 0, 0), 0.03, span + 0.48, M.iron, n=6, ry=PI / 2)
    for i in range(5):
        g.torus((-0.25 + i * 0.1, 0, 0), 0.12, 0.016, M.rope, n=12, m=3, ry=PI / 2)
    x = span / 2 + 0.33
    g.box((x, 0, -0.16), (0.04, 0.05, 0.36), M.iron)
    g.cyl((x, 0, -0.32), 0.022, 0.2, M.wood_dk, n=6, ry=PI / 2)
    p.params.update(axis='x', speed=0.0, wobble=0.03, sound='rattle')


def well_bucket(p, M, drop=0.95):
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0, -drop + 0.3), 0.012, drop - 0.3, M.rope, n=4)
    bucket_geo(g, M, (0, 0, -drop - 0.12), 0.15, 0.28, mat=M.wood_mid, water=True)
    for z in (0.06, 0.2):
        g.torus((0, 0, -drop - 0.12 + z), 0.15 * (0.78 + 0.22 * z / 0.28) + 0.006, 0.008, M.iron, n=12, m=3)
    p.params.update(axes='xz', amp=0.025, period=1.9, sound='splash')


def hand_pump(p, M):
    b = p.body
    b.box((0, 0, 0.06), (0.65, 0.65, 0.12), M.stone, bevel=0.03)
    b.cyl((0, 0, 0.12), 0.085, 0.9, M.iron, n=10)
    b.cyl((0, 0, 1.0), 0.1, 0.1, M.iron, n=10)
    b.sphere((0, 0, 1.12), 0.05, M.iron, n=8)
    b.tube([(0, -0.06, 0.82), (0, -0.25, 0.84), (0, -0.33, 0.74)], 0.03, M.iron, n=6)
    bucket_geo(b, M, (0, -0.35, 0.12), 0.14, 0.26, water=True)
    b.collide((0, 0, 0.55), (0.65, 0.65, 1.1))
    pv = p.part('pivot', (0, 0.07, 1.08), rx=0.3)
    g = pv.geo
    g.box((0, 0.36, 0), (0.035, 0.75, 0.04), M.iron)
    g.box((0, -0.05, -0.12), (0.03, 0.03, 0.24), M.iron)
    g.sphere((0, 0.74, 0), 0.04, M.wood_dk, n=6, s=(1, 2, 1))
    p.params.update(axis='x', period=2.4, sound='squeak')


def cider_press(p, M):
    b = p.body
    b.box((0, 0, 0.4), (1.1, 0.9, 0.08), M.wood_mid, bevel=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box((sx * 0.48, sy * 0.38, 0.2), (0.08, 0.08, 0.4), M.wood_mid)
        b.box((sx * 0.48, 0, 1.15), (0.12, 0.12, 1.5), M.wood_dk, bevel=0.01)
    b.box((0, 0, 1.85), (1.1, 0.16, 0.16), M.wood_dk, bevel=0.02)
    for i in range(14):
        a = TAU * i / 14
        b.box((math.cos(a) * 0.27, math.sin(a) * 0.27, 0.72), (0.04, 0.09, 0.56), M.wood_light, rz=a)
    for z in (0.5, 0.95):
        b.torus((0, 0, z), 0.29, 0.012, M.iron, n=14, m=3)
    b.cyl((0, 0, 0.9), 0.25, 0.06, M.wood_mid, n=12)
    b.box((0.55, -0.4, 0.38), (0.3, 0.1, 0.05), M.wood_mid, rx=0.3)
    bucket_geo(b, M, (0.72, -0.48, 0.0), 0.13, 0.25, mat=M.wood_mid)
    b.collide((0, 0, 0.9), (1.2, 1.0, 1.8))
    pv = p.part('pivot', (0, 0, 1.0))
    g = pv.geo
    g.cyl((0, 0, -0.04), 0.035, 1.05, M.iron, n=6)
    for i in range(10):
        g.torus((0, 0, 0.05 + i * 0.07), 0.04, 0.008, M.iron, n=6, m=3)
    g.cyl((-0.45, 0, 1.02), 0.025, 0.9, M.wood_light, n=6, ry=PI / 2)
    p.params.update(axis='y', speed=0.0, wobble=0.0, sound='squeak')


def bell_post(p, M, h=2.4, r=0.2, tone=520):
    """Dinner bell in a little yoke on a post (axle along Y)."""
    b = p.body
    b.box((0, 0, h / 2), (0.14, 0.14, h), M.grey_wood)
    b.collide((0, 0, h / 2), (0.18, 0.18, h))
    for sy in (-1, 1):
        b.box((0, sy * (r * 1.3 + 0.04), h + 0.18), (0.08, 0.06, 0.4), M.grey_wood)
    b.box((0, 0, h + 0.42), (0.12, r * 2.9, 0.08), M.grey_wood)
    b.prism((-0.1, -(r * 1.6), h + 0.46), [(0.0, 0.0), (r * 3.2, 0.0), (r * 1.6, 0.25)], 0.2, M.barn_roof,
            rx=PI / 2, rz=PI / 2)
    pv = p.part('pivot', (0, 0, h + 0.3))
    g = pv.geo
    g.lathe((0, 0, -r * 2.1), [(r, 0), (r * 0.95, r * 0.15), (r * 0.62, r * 1.0), (r * 0.52, r * 1.75),
                               (r * 0.25, r * 2.0), (0.01, r * 2.05)], M.bronze, n=14)
    g.box((0, 0, 0.0), (0.06, r * 2.6, 0.07), M.wood_dk)
    g.sphere((0, 0, -r * 1.95), r * 0.17, M.iron, n=6)
    g.tube([(0, 0, -0.05), (0.15, 0.0, -r * 2.2), (0.12, 0.0, -r * 2.2 - 0.6)], 0.006, M.rope, n=3)
    p.params.update(axis='z', tone=tone, sound='bell')


def mailbox(p, M):
    """Rural mailbox on a post; the red flag (pivot) rotates about X."""
    b = p.body
    b.box((0, 0, 0.55), (0.1, 0.1, 1.1), M.grey_wood)
    b.box((0, 0, 1.12), (0.3, 0.6, 0.04), M.grey_wood)
    b.box((0, 0, 1.25), (0.24, 0.5, 0.2), M.tin, bevel=0.01)
    b.cyl((0, -0.25, 1.35), 0.12, 0.5, M.tin, n=10, rx=-PI / 2, smooth=True)
    b.box((0, -0.252, 1.28), (0.24, 0.012, 0.26), M.tin)
    b.collide((0, 0, 0.6), (0.3, 0.6, 1.2))
    pv = p.part('pivot', (0.135, 0.12, 1.3), rx=-PI / 2 + 0.12)
    g = pv.geo
    g.box((0, 0.0, 0.15), (0.012, 0.03, 0.3), M.ribbon)
    g.box((0, 0.0, 0.32), (0.012, 0.12, 0.08), M.ribbon)
    p.params.update(axis='x', dir=1, closed=0, open=1.4, sound='clatter')


def lantern_post(p, M, h=2.3, light=1.1, dist=8.5, arm=False):
    """Rustic wooden post with a lantern box on top (flame + light)."""
    b = p.body
    b.box((0, 0, h / 2), (0.14, 0.14, h), M.wood_dk)
    b.collide((0, 0, h / 2), (0.18, 0.18, h))
    b.box((0, 0, h + 0.02), (0.22, 0.22, 0.04), M.iron)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box((sx * 0.09, sy * 0.09, h + 0.2), (0.02, 0.02, 0.34), M.iron)
    b.box((0, 0, h + 0.2), (0.16, 0.16, 0.3), M.lantern_glass)
    b.cyl((0, 0, h + 0.37), 0.15, 0.12, M.iron, n=4, r2=0.02, rz=PI / 4, smooth=False)
    b.torus((0, 0, h + 0.52), 0.035, 0.008, M.iron, n=8, m=3, rx=PI / 2)
    b.cyl((0, 0, h + 0.04), 0.022, 0.1, M.wax, n=6)
    p.flame((0, 0, h + 0.15), size=0.8)
    p.light((0, 0, h + 0.25), '#ffb45e', light, dist, part='flame0')
    p.params.update(sound='whoomp')


def burn_barrel(p, M, light=1.3):
    b = p.body
    b.lathe((0, 0, 0), [(0.29, 0), (0.3, 0.86), (0.28, 0.88)], M.rust, n=12, cap_top=False)
    b.lathe((0, 0, 0.05), [(0.28, 0.82), (0.27, 0.0)], M.iron, n=12, cap_bottom=False, cap_top=False)
    for z in (0.28, 0.58):
        b.torus((0, 0, z), 0.305, 0.014, M.rust, n=12, m=3)
    for i in range(5):
        a = TAU * i / 5 + 0.3
        b.box((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.15), (0.03, 0.06, 0.08), M.ember, rz=a)
    b.cyl((0, 0, 0.7), 0.26, 0.04, M.ember, n=10)
    for i in range(4):
        b.cyl((-0.15 + i * 0.1, 0, 0.74), 0.035, 0.45, M.bark, n=5, rx=0.8 + i * 0.3, rz=i * 1.3, smooth=False)
    for i, (x, y, s) in enumerate(((0, 0, 2.0), (0.1, 0.06, 1.4), (-0.1, -0.05, 1.5))):
        p.flame((x, y, 0.75), size=s)
    p.light((0, 0, 1.3), '#ff8a3a', light, 7.5, part='flame0')
    b.collide((0, 0, 0.45), (0.6, 0.6, 0.9))
    p.params.update(sound='whoomp')


def oil_lamp(p, M):
    b = p.body
    b.lathe((0, 0, 0), [(0.07, 0), (0.07, 0.01), (0.04, 0.03), (0.06, 0.08), (0.055, 0.12), (0.025, 0.14),
                        (0.03, 0.15)], M.brass, n=12)
    b.lathe((0, 0, 0.15), [(0.03, 0), (0.045, 0.06), (0.03, 0.14), (0.025, 0.2)], M.lantern_glass, n=10, cap_top=False)
    p.flame((0, 0, 0.17), size=0.6)
    p.params.update(sound='whoomp')


def wood_stove(p, M, light=1.0, pipe=2.0):
    """Cast-iron kitchen stove with its fire door open; pipe rises to the ceiling (h_pipe)."""
    b = p.body
    b.box((0, 0, 0.5), (0.95, 0.6, 0.5), M.iron, bevel=0.03)
    b.box((0, 0, 0.77), (1.0, 0.64, 0.04), M.iron, bevel=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.cyl((sx * 0.4, sy * 0.24, 0), 0.035, 0.25, M.iron, n=6, r2=0.025)
    b.box((-0.18, -0.305, 0.5), (0.36, 0.02, 0.3), M.ember)
    b.box((-0.18, -0.32, 0.5), (0.36, 0.01, 0.06), M.iron)
    with b.at((-0.36, -0.31, 0.5), rz=-1.7):
        b.box((0.18, -0.01, 0), (0.36, 0.02, 0.3), M.iron)
    b.box((0.25, -0.31, 0.5), (0.3, 0.02, 0.32), M.iron)
    b.sphere((0.25, -0.33, 0.6), 0.025, M.brass, n=6)
    for x in (-0.22, 0.18):
        b.cyl((x, 0.0, 0.79), 0.12, 0.012, M.iron, n=12)
    b.lathe((0.18, 0.0, 0.8), [(0.1, 0), (0.12, 0.06), (0.09, 0.14), (0.03, 0.16)], M.tin, n=10)
    b.tube([(0.26, -0.02, 0.88), (0.36, -0.07, 0.95)], 0.012, M.tin, n=4)
    b.cyl((0.0, 0.18, 0.79), 0.07, pipe, M.iron, n=8)
    b.box((0.55, 0.0, 0.9), (0.06, 0.3, 0.02), M.iron)
    p.flame((-0.24, -0.15, 0.4), size=1.4)
    p.flame((-0.12, -0.15, 0.4), size=1.1)
    b.box((-0.18, -0.15, 0.37), (0.3, 0.2, 0.03), M.ember)
    p.light((0, -0.6, 0.6), '#ff9a48', light, 6.5, part='flame0')
    b.collide((0, 0, 0.4), (1.0, 0.64, 0.8))
    p.params.update(sound='whoomp')


def wall_clock(p, M):
    """Round kitchen clock on a wall facing -Y; hands spin about Z (face normal)."""
    b = p.body
    b.cyl((0, 0.0, 0), 0.22, 0.06, M.wood_mid, n=20, rx=PI / 2)
    b.cyl((0, -0.061, 0), 0.19, 0.005, M.clock_face, n=20, rx=PI / 2)
    for i in range(12):
        a = i * TAU / 12
        b.box((math.sin(a) * 0.16, -0.067, math.cos(a) * 0.16), (0.012, 0.004, 0.03 if i % 3 else 0.045), M.iron, ry=-a)
    b.box((0, 0.0, -0.36), (0.16, 0.05, 0.3), M.wood_mid, bevel=0.01)
    b.box((0, -0.03, -0.38), (0.11, 0.01, 0.2), M.window_dark)
    hr = p.geo('hour', (0, -0.07, 0))
    hr.box((0, 0, 0.045), (0.02, 0.006, 0.1), M.iron)
    mn = p.geo('minute', (0, -0.075, 0))
    mn.box((0, 0, 0.07), (0.012, 0.006, 0.15), M.iron)
    pd = p.geo('pend', (0, -0.04, -0.24))
    pd.box((0, 0, -0.08), (0.008, 0.005, 0.16), M.brass)
    pd.cyl((0, 0.0, -0.17), 0.03, 0.01, M.brass, n=10, rx=PI / 2)
    b.sphere((0, -0.078, 0), 0.01, M.brass, n=5)
    p.params.update(axis='z', sound='chime')


def pot_rack(p, M, drop=0.55):
    pv = p.part('pivot')
    g = pv.geo
    for sx in (-1, 1):
        g.cyl((sx * 0.35, 0, -drop), 0.006, drop, M.iron, n=3)
    g.box((0, 0, -drop), (0.95, 0.05, 0.04), M.iron)
    for i, (x, kind) in enumerate(((-0.35, 'pot'), (-0.1, 'ladle'), (0.12, 'pan'), (0.36, 'pot'))):
        g.cyl((x, 0, -drop - 0.12), 0.004, 0.12, M.iron, n=3)
        if kind == 'pot':
            g.lathe((x, 0, -drop - 0.33), [(0.08, 0), (0.1, 0.18), (0.1, 0.2)], M.copper, n=10, cap_top=False)
        elif kind == 'pan':
            g.cyl((x, 0, -drop - 0.36), 0.14, 0.04, M.iron, n=12, rx=PI / 2)
            g.box((x, 0, -drop - 0.2), (0.025, 0.02, 0.18), M.iron)
        else:
            g.box((x, 0, -drop - 0.25), (0.015, 0.01, 0.26), M.wood_mid)
            g.sphere((x, 0, -drop - 0.4), 0.04, M.wood_mid, n=6, s=(1, 0.5, 1))
    for i in range(3):
        g.blob((-0.2 + i * 0.22, 0.04, -drop - 0.12), 0.06, M.herb, seed=i, jitter=0.3, subdiv=0, s=(0.7, 0.7, 1.6))
    p.params.update(axes='xz', amp=0.012, period=2.0, sound='clatter')


def farm_stand_awning(p, M, w=2.6):
    """Striped awning valance hanging from the farm stand roof edge (cloth parts)."""
    n = 4
    for i in range(n):
        g = p.geo(f'cloth{i}', (-w / 2 + w * (i + 0.5) / n, 0, 0))
        g.sheet((0, 0, 0), w / n - 0.01, 0.38, M.awning, nx=4, ny=3)
    p.body.box((0, 0.02, 0.02), (w + 0.1, 0.06, 0.06), M.wood_dk)
    p.params.update(amp=0.035, sound='whoosh')


def tarp(p, M, w=3.0, d=1.2, h=0.9):
    """Canvas tarp thrown over the woodpile; the front flap ripples (cloth0)."""
    for sy in (-1, 1):
        p.body.box((0, sy * d * 0.27, 0.05), (w, d * 0.58, 0.035), M.tarp, rx=sy * 0.22)
    p.body.box((0, 0, 0.11), (w + 0.02, 0.1, 0.04), M.tarp)
    for sx in (-1, 1):
        p.body.cyl((sx * (w / 2 - 0.1), -d / 2, -0.02), 0.03, 0.02, M.rope, n=6)
        p.body.tube([(sx * (w / 2 - 0.1), -d / 2 - 0.02, 0.0), (sx * (w / 2 - 0.05), -d / 2 - 0.05, -h - 0.3)], 0.008,
                    M.rope, n=3)
    g = p.geo('cloth0', (0, -d / 2 - 0.02, 0.0))
    g.sheet((0, 0, 0), w * 0.9, h, M.tarp, nx=8, ny=5)
    p.params.update(amp=0.04, sound='whoosh')


def corn_clump(p, M, n=6, seed=0, r=0.45, h=2.45):
    rng = random.Random(seed)
    pv = p.part('pivot')
    for i in range(n):
        a = TAU * i / n + rng.uniform(-0.4, 0.4)
        d = r * math.sqrt(rng.uniform(0.1, 1))
        corn_stalk(pv.geo, M, (math.cos(a) * d, math.sin(a) * d, 0), h * rng.uniform(0.85, 1.1), rng, leaves=4)
    p.body.collide((0, 0, 0.6), (r * 1.4, r * 1.4, 1.2))
    p.params.update(amp=0.025, leaf='#c4a860', sound='rustle')


def corn_shock(p, M, seed=0, r=0.6, h=2.1):
    """Bundled corn shock (teepee of dry stalks tied near the top)."""
    rng = random.Random(seed)
    pv = p.part('pivot')
    g = pv.geo
    tie = h * 0.72
    for i in range(22):
        a = TAU * i / 22 + rng.uniform(-0.1, 0.1)
        rr = r * rng.uniform(0.8, 1.05)
        base = (math.cos(a) * rr, math.sin(a) * rr, 0)
        mid = (math.cos(a) * 0.1, math.sin(a) * 0.1, tie)
        top = (math.cos(a) * (0.25 + rng.uniform(0, 0.2)), math.sin(a) * (0.25 + rng.uniform(0, 0.2)), h + rng.uniform(-0.1, 0.2))
        g.tube([base, mid, top], 0.022, rng.choice((M.corn_stalk, M.corn_leaf)), n=4, caps=False)
        if i % 3 == 0:
            g.add(prim_blade(0.6, 0.08, up=0.4, droop=1.0), M.corn_leaf2, _mat((base[0] * 0.6, base[1] * 0.6, tie * 0.5), a))
    g.torus((0, 0, tie), 0.13, 0.025, M.rope, n=10, m=4)
    p.body.collide((0, 0, 0.6), (r * 1.4, r * 1.4, 1.2))
    p.params.update(amp=0.012, leaf='#c4a860', sound='rustle')


def cattails(p, M, seed=0, n=9):
    rng = random.Random(seed)
    pv = p.part('pivot')
    g = pv.geo
    for i in range(n):
        a = rng.uniform(0, TAU)
        d = rng.uniform(0, 0.45)
        x, y = math.cos(a) * d, math.sin(a) * d
        hh = rng.uniform(1.3, 1.9)
        lx, ly = rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12)
        g.tube([(x, y, 0), (x + lx * 0.5, y + ly * 0.5, hh * 0.6), (x + lx, y + ly, hh)], 0.012, M.reed, n=4, caps=False)
        if i % 2 == 0:
            g.cyl((x + lx * 0.95, y + ly * 0.95, hh - 0.32), 0.03, 0.22, M.cattail, n=6)
        g.add(prim_blade(hh * 0.8, 0.05, up=1.6, droop=1.1), M.reed, _mat((x, y, 0), rng.uniform(0, TAU)))
    p.params.update(amp=0.03, leaf='#8a7a48', sound='rustle')


def sunflowers(p, M, n=4, spacing=0.7, seed=0):
    """A row of drooping, autumn-dry sunflowers along X."""
    rng = random.Random(seed)
    pv = p.part('pivot')
    g = pv.geo
    for i in range(n):
        x = (i - (n - 1) / 2) * spacing + rng.uniform(-0.12, 0.12)
        y = rng.uniform(-0.15, 0.15)
        hh = rng.uniform(1.9, 2.4)
        a = rng.uniform(-PI, PI) * 0.3 - PI / 2
        hx, hy = x + math.cos(a) * 0.25, y + math.sin(a) * 0.25
        g.tube([(x, y, 0), (x, y, hh * 0.7), (x + math.cos(a) * 0.12, y + math.sin(a) * 0.12, hh),
                (hx, hy, hh - 0.12)], 0.03, M.sunstalk, n=5)
        for j in range(4):
            g.add(prim_blade(0.4, 0.16, up=0.3, droop=1.2), M.sunleaf, _mat((x, y, hh * (0.3 + 0.13 * j)), rng.uniform(0, TAU)))
        with g.at((hx, hy, hh - 0.2), rz=a + PI / 2, rx=1.1):
            g.cyl((0, 0, 0), 0.17, 0.05, M.sunface, n=12, r2=0.13)
            for k in range(12):
                b = TAU * k / 12
                g.add(prim_blade(0.12, 0.05, up=0.0, droop=0.6, seg=2), M.sunpetal,
                      _mat((math.cos(b) * 0.15, math.sin(b) * 0.15, 0.02), b))
    p.body.collide((0, 0, 1.0), ((n - 1) * spacing + 0.4, 0.4, 2.0))
    p.params.update(amp=0.02, leaf='#b88a3a', sound='rustle')


def apple_tree(p, M, seed=0, h=4.3, crown=1.75, apples=12):
    rng = random.Random(seed)
    pv = p.part('pivot')
    g = pv.geo
    trunk_h = h * 0.42
    lx, ly = rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25)
    g.lathe((0, 0, 0), [(0.28, 0), (0.18, 0.18), (0.14, 0.4)], M.bark, n=7, smooth=False)
    g.tube([(0, 0, 0), (lx * 0.3, ly * 0.3, trunk_h * 0.5), (lx, ly, trunk_h)], 0.13, M.bark, n=7)
    top = (lx, ly, trunk_h)
    leaves = [M.leaf_olive, M.leaf_gold, M.leaf_sage, M.leaf_olive]
    blobs = []
    for i in range(4):
        a = TAU * i / 4 + rng.uniform(-0.4, 0.4)
        d = crown * rng.uniform(0.55, 0.8)
        end = (lx + math.cos(a) * d, ly + math.sin(a) * d, trunk_h + crown * rng.uniform(0.55, 0.85))
        mid = (lx + math.cos(a) * d * 0.45, ly + math.sin(a) * d * 0.45, trunk_h + crown * 0.3)
        g.tube([top, mid, end], 0.065, M.bark, n=5)
        r = crown * rng.uniform(0.55, 0.68)
        c = (end[0], end[1], end[2] + 0.25)
        g.blob(c, r, rng.choice(leaves), seed=seed * 17 + i, jitter=0.2, subdiv=1, s=(1, 1, 0.8))
        blobs.append((c, r))
    c = (lx, ly, trunk_h + crown * 1.1)
    g.blob(c, crown * 0.78, rng.choice(leaves), seed=seed + 77, jitter=0.2, subdiv=1, s=(1, 1, 0.85))
    blobs.append((c, crown * 0.78))
    for k in range(apples):
        c, r = rng.choice(blobs)
        a = rng.uniform(0, TAU)
        e = rng.uniform(-0.7, 0.3)
        dx, dy, dz = math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e) * 0.8
        g.sphere((c[0] + dx * r * 0.93, c[1] + dy * r * 0.93, c[2] + dz * r * 0.93), 0.06, M.apple, n=6)
    p.body.collide((0, 0, trunk_h / 2), (0.4, 0.4, trunk_h))
    p.params.update(amp=0.014, leaf='#c89a3a', sound='rustle')


OAK_LIMB = [(0, 0, 3.6), (1.3, -0.75, 4.35), (2.6, -1.5, 4.55), (3.4, -1.95, 4.8)]


def oak(p, M, seed=3, h=10.0, crown=4.4):
    """The big old oak; the tire swing hangs from OAK_LIMB."""
    rng = random.Random(seed)
    pv = p.part('pivot')
    g = pv.geo
    g.lathe((0, 0, 0), [(0.85, 0), (0.6, 0.25), (0.48, 0.7), (0.42, 1.5)], M.bark, n=9, smooth=False)
    trunk = [(0, 0, 0), (0.05, 0.08, 2.0), (-0.1, 0.1, 3.6), (0.0, 0.0, 5.0)]
    g.tube(trunk, 0.42, M.bark, n=9)
    for i in range(5):
        a = TAU * i / 5 + 0.9 + rng.uniform(-0.3, 0.3)
        z0 = rng.uniform(3.4, 4.6)
        L = crown * rng.uniform(0.75, 0.95)
        pts = [(0, 0, z0), (math.cos(a) * L * 0.45, math.sin(a) * L * 0.45, z0 + 1.0),
               (math.cos(a) * L, math.sin(a) * L, z0 + 2.4)]
        g.tube(pts, 0.2, M.bark, n=6)
    g.tube(OAK_LIMB, 0.16, M.bark, n=6)
    leaves = [M.leaf_orange, M.leaf_gold, M.leaf_red, M.leaf_olive, M.leaf_orange]
    for i in range(16):
        a = rng.uniform(0, TAU)
        d = crown * math.sqrt(rng.uniform(0.05, 1.0)) * 0.85
        z = 6.0 + rng.uniform(0, 3.2) - d * 0.35
        g.blob((math.cos(a) * d, math.sin(a) * d, z), rng.uniform(1.4, 2.1), rng.choice(leaves), seed=seed * 7 + i,
               jitter=0.22, subdiv=1, s=(1, 1, 0.78))
    g.blob((2.9, -1.7, 6.3), 1.5, M.leaf_gold, seed=91, jitter=0.2, subdiv=1, s=(1, 1, 0.75))
    p.body.collide((0, 0, 2.5), (1.0, 1.0, 5.0))
    p.params.update(amp=0.008, leaf='#c8642a', sound='rustle')


def rowboat(p, M):
    pv = p.part('pivot')
    g = pv.geo
    g.add(prim_hull(3.0, 1.15, 0.42), M.boat)
    g.box((0, 0, -0.02), (0.06, 3.0, 0.04), M.wood_dk)
    for y in (-0.6, 0.15, 0.85):
        g.box((0, y, -0.12), (1.0 if abs(y) < 0.5 else 0.85, 0.22, 0.04), M.wood_light)
    for sx in (-1, 1):
        g.box((sx * 0.2, 0.1, -0.05), (0.06, 2.2, 0.04), M.wood_light, rz=sx * 0.08)
        g.box((sx * 0.2, 1.15, -0.05), (0.13, 0.35, 0.02), M.wood_light, rz=sx * 0.08)
    g.box((0, -0.2, -0.36), (0.6, 1.6, 0.02), M.water_dk)
    p.params.update(axis='z', period=2.8, sound='splash')


def duck(p, M, drake=True):
    pv = p.part('pivot')
    g = pv.geo
    g.sphere((0, 0.02, 0.06), 0.12, M.duck_body, n=8, s=(0.75, 1.3, 0.62))
    g.box((0, 0.17, 0.09), (0.08, 0.1, 0.02), M.duck_body, rx=0.5)
    g.sphere((0, -0.12, 0.19), 0.055, M.duck_head if drake else M.duck_body, n=8)
    g.cyl((0, -0.16, 0.18), 0.022, 0.06, M.ochre, n=5, r2=0.012, rx=PI / 2 + 0.2)
    if drake:
        g.torus((0, -0.1, 0.14), 0.035, 0.008, M.paint_white, n=8, m=3)
    p.params.update(amp=0.012, sound='splash')


def fishing_bobber(p, M):
    pv = p.part('pivot')
    g = pv.geo
    g.sphere((0, 0, 0.03), 0.03, M.ribbon, n=6)
    g.sphere((0, 0, 0.06), 0.022, M.paint_white, n=6)
    g.cyl((0, 0, 0.07), 0.003, 0.05, M.iron, n=3)
    p.params.update(amp=0.015, sound='splash')


def windmill_sails(p, M, R=5.6):
    """Four lattice sails in the XZ plane (spinning about local Y); pivot at the hub."""
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0.0, 0), 0.32, 0.5, M.wood_dk, n=10, rx=PI / 2)
    g.sphere((0, -0.5, 0), 0.22, M.wood_dk, n=8)
    for k in range(4):
        with g.at((0, -0.3, 0), ry=k * PI / 2 + 0.3):
            g.box((0, 0, R / 2), (0.18, 0.16, R), M.wood_mid, bevel=0.02)
            w0, w1 = 0.1, 1.25
            for x in (w0, w1):
                g.box((x, -0.02, (R + 1.0) / 2), (0.06, 0.05, R - 1.0), M.wood_light)
            z = 1.0
            while z <= R + 0.01:
                g.box(((w0 + w1) / 2, -0.02, z), (w1 - w0, 0.04, 0.05), M.wood_light)
                z += 0.46
            # sailcloth reefed on three-quarters of the frame
            g.box(((w0 + w1) / 2, 0.02, 1.0 + (R - 1.0) * 0.6), (w1 - w0 - 0.04, 0.012, (R - 1.0) * 0.78), M.sailcloth)
            g.box((-0.18, -0.02, (R + 1.6) / 2), (0.2, 0.04, R - 1.6), M.wood_light)
    p.params.update(axis='z', speed=0.45, wobble=0.0, sound='whirr')


def corn_crib(g, M, L=3.2, W=1.7, H=2.7, col=True):
    """Slatted corn crib on stone piers, long axis along X; ears of corn show between the slats."""
    z0 = 0.5
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box((sx * (L / 2 - 0.15), sy * (W / 2 - 0.12), z0 / 2), (0.3, 0.3, z0), M.stone)
            g.box((sx * (L / 2 - 0.05), sy * (W / 2 - 0.05), z0 + (H - z0) / 2), (0.12, 0.12, H - z0), M.wood_dk)
    g.box((0, 0, z0 + 0.04), (L, W, 0.08), M.grey_wood)
    g.box((0, 0, (z0 + H) / 2), (L - 0.3, W - 0.3, H - z0 - 0.2), M.straw)
    z = z0 + 0.15
    while z < H - 0.05:
        for sy in (-1, 1):
            g.box((0, sy * (W / 2 - 0.02), z), (L - 0.1, 0.03, 0.07), M.grey_wood)
        for sx in (-1, 1):
            g.box((sx * (L / 2 - 0.02), 0, z), (0.03, W - 0.1, 0.07), M.grey_wood)
        z += 0.14
    for sy in (-1, 1):
        g.box((0, sy * W * 0.32, H + 0.36), (L + 0.5, W * 0.72, 0.05), M.rust, rx=sy * 0.62)
    g.prism((-L / 2, 0, H), [(-W / 2, 0), (W / 2, 0), (0, 0.6)], 0.04, M.grey_wood, rx=PI / 2, rz=-PI / 2)
    g.prism((L / 2 + 0.04, 0, H), [(-W / 2, 0), (W / 2, 0), (0, 0.6)], 0.04, M.grey_wood, rx=PI / 2, rz=-PI / 2)
    g.box((0, -W / 2 - 0.25, z0 - 0.1), (0.9, 0.5, 0.06), M.grey_wood, rx=0.2)
    if col:
        g.collide((0, 0, H / 2), (L, W, H))


def hutch(g, M):
    """Kitchen hutch against a wall at +Y (front faces -Y): closed base, open plate shelves above."""
    g.box((0, 0.05, 0.45), (1.4, 0.5, 0.9), M.paint_sage, bevel=0.015)
    g.box((0, 0.03, 0.92), (1.5, 0.56, 0.04), M.wood_mid)
    for sx in (-0.35, 0.35):
        g.box((sx, -0.205, 0.45), (0.6, 0.02, 0.72), M.paint_sage, bevel=0.01)
        g.sphere((sx + (0.2 if sx < 0 else -0.2), -0.225, 0.55), 0.02, M.brass, n=6)
    g.box((0, 0.27, 1.55), (1.4, 0.04, 1.25), M.paint_sage)
    for sx in (-0.68, 0.68):
        g.box((sx, 0.15, 1.55), (0.04, 0.26, 1.25), M.paint_sage)
    g.box((0, 0.15, 2.18), (1.44, 0.3, 0.05), M.wood_mid)
    for i, z in enumerate((1.3, 1.7)):
        g.box((0, 0.15, z), (1.32, 0.24, 0.03), M.wood_mid)
        for k in range(5):
            g.cyl((-0.5 + k * 0.25, 0.2, z + 0.13), 0.11, 0.015, M.cloth_white, n=10, rx=PI / 2 - 0.25)
    for k, x in enumerate((-0.45, -0.15, 0.2, 0.45)):
        g.lathe((x, 0.12, 0.94), [(0.05, 0), (0.055, 0.12), (0.035, 0.15), (0.04, 0.17)],
                (M.apple, M.window_glow_dim, M.leaf_gold, M.tin)[k], n=8)


def bucket_prop(p, M, water=True):
    pv = p.part('pivot')
    bucket_geo(pv.geo, M, (0, 0, 0), 0.15, 0.3, water=water)
    p.body.collide((0, 0, 0.15), (0.32, 0.32, 0.3))
    p.params.update(sound='clatter')


def signpost(p, M):
    """Leaning farm signpost; the arrow boards (pivot) can turn on the post like a weathervane."""
    b = p.body
    b.box((0, 0, 1.2), (0.12, 0.12, 2.4), M.grey_wood)
    b.cyl((0, 0, 2.4), 0.1, 0.08, M.grey_wood, n=4, r2=0.02, rz=PI / 4, smooth=False)
    b.collide((0, 0, 1.2), (0.16, 0.16, 2.4))
    pv = p.part('pivot', (0, 0, 0.0))
    g = pv.geo
    arrow = [(0.0, -0.09), (0.55, -0.09), (0.68, 0.0), (0.55, 0.09), (0.0, 0.09)]
    for k, (z, a, col) in enumerate(((2.15, 0.5, M.paint_white), (1.88, 2.6, M.wood_light), (1.62, -1.6, M.paint_white))):
        with g.at((0, 0, z), a):
            g.prism((0.06, 0.015, 0.0), arrow, 0.03, col, rx=PI / 2)
            for q in range(3):
                g.box((0.2 + q * 0.13, -0.02, 0.0), (0.08, 0.01, 0.07 - 0.02 * (q % 2)), M.wood_dk)
    p.params.update(axis='y', speed=0.0, wobble=0.015, sound='creak')
