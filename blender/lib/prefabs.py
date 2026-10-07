"""Reusable prefabs.

Static prefabs have the signature fn(geo, **kw) and draw relative to the
current transform (origin = floor point under the object, facing -Y / "south"
unless stated). Use MapBuilder.put(fn, pos, rz, **kw).

Prop prefabs have the signature fn(prop, **kw), draw into prop parts and set
prop.params defaults for the client-side animation archetype. Use
MapBuilder.place(fn, type, label, pos, rz, params, key=..., **kw).
"""
import math
import random

from .gh import TAU


# ------------------------------------------------------------------ static

def altar(g, stone, trim, glow=None, style='plinth'):
    """Relic altar: every one on a map looks identical to the hunter. Returns top height."""
    if style == 'stump':
        g.cyl((0, 0, 0), 0.42, 0.75, stone, n=9, r2=0.36, col=True)
        g.cyl((0, 0, 0.75), 0.36, 0.05, trim, n=9)
        g.torus((0, 0, 0.79), 0.26, 0.025, glow or trim, n=16, m=4)
        return 0.82
    g.box((0, 0, 0.08), (0.9, 0.9, 0.16), stone, bevel=0.03, col=True)
    g.box((0, 0, 0.2), (0.7, 0.7, 0.1), stone, bevel=0.02)
    g.lathe((0, 0, 0.25), [(0.22, 0), (0.17, 0.08), (0.15, 0.55), (0.19, 0.62), (0.3, 0.68), (0.3, 0.74)], stone, n=10)
    g.collide((0, 0, 0.5), (0.5, 0.5, 1.0))
    g.cyl((0, 0, 0.99), 0.32, 0.04, trim, n=16)
    g.torus((0, 0, 1.03), 0.25, 0.02, glow or trim, n=20, m=4)
    for i in range(4):
        a = i * TAU / 4 + TAU / 8
        g.box((math.cos(a) * 0.26, math.sin(a) * 0.26, 0.6), (0.05, 0.05, 0.5), trim, rz=a)
    return 1.03


def table(g, w, d, h, wood, legs=None, cloth=None, bevel=0.02, col=True):
    legs = legs or wood
    g.box((0, 0, h - 0.03), (w, d, 0.06), wood, bevel=bevel)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box((sx * (w / 2 - 0.08), sy * (d / 2 - 0.08), (h - 0.06) / 2), (0.07, 0.07, h - 0.06), legs, bevel=0.01)
    g.box((0, d / 2 - 0.08, h - 0.12), (w - 0.2, 0.03, 0.1), legs)
    g.box((0, -d / 2 + 0.08, h - 0.12), (w - 0.2, 0.03, 0.1), legs)
    if cloth is not None:
        g.box((0, 0, h + 0.005), (w + 0.12, d + 0.12, 0.012), cloth)
        for sy in (-1, 1):
            g.box((0, sy * (d / 2 + 0.06), h - 0.12), (w + 0.12, 0.012, 0.25), cloth)
    if col:
        g.collide((0, 0, h / 2), (w, d, h))


def bookshelf(g, w, h, wood, books, depth=0.38, seed=1, gaps=0.15, col=True):
    rng = random.Random(seed)
    g.box((0, 0, h / 2), (w, depth, h), wood, bevel=0.015)  # carcass back reads as a solid block
    shelves = max(3, int(h / 0.42))
    inner_h = (h - 0.12) / shelves
    g.box((0, -depth / 2 - 0.005, h - 0.04), (w + 0.06, 0.06, 0.08), wood, bevel=0.01)
    for s in range(shelves):
        z0 = 0.08 + s * inner_h
        g.box((0, -depth / 2 + 0.01, z0), (w - 0.04, 0.04, 0.03), wood)
        x = -w / 2 + 0.06
        while x < w / 2 - 0.08:
            if rng.random() < gaps:
                x += rng.uniform(0.06, 0.2)
                continue
            bw = rng.uniform(0.035, 0.07)
            bh = rng.uniform(0.6, 0.9) * (inner_h - 0.05)
            lean = 0.0 if rng.random() > 0.08 else rng.uniform(-0.25, 0.25)
            m = rng.choice(books)
            g.box((x + bw / 2, -depth / 2 - 0.01, z0 + 0.015 + bh / 2), (bw, depth * 0.75, bh), m, ry=lean)
            x += bw + 0.004
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.02), -depth / 2 - 0.02, h / 2), (0.05, 0.05, h), wood)
    if col:
        g.collide((0, 0, h / 2), (w, depth, h))


def rug(g, w, d, mat, border=None):
    g.box((0, 0, 0.006), (w, d, 0.012), mat)
    if border is not None:
        for sy in (-1, 1):
            g.box((0, sy * (d / 2 - 0.04), 0.008), (w, 0.08, 0.013), border)


def window(g, w, h, frame, glass, sill_mat=None, mullions=2, t=0.34):
    """Window filling a wall opening; origin at the bottom centre of the opening, wall along X."""
    g.box((0, 0, h / 2), (w, 0.04, h), glass)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.04), 0, h / 2), (0.08, t + 0.02, h), frame)
    g.box((0, 0, h - 0.04), (w, t + 0.02, 0.08), frame)
    g.box((0, 0, 0.03), (w + 0.12, t + 0.12, 0.06), sill_mat or frame, bevel=0.01)
    for i in range(1, mullions):
        x = -w / 2 + w * i / mullions
        g.box((x, 0, h / 2), (0.04, 0.08, h), frame)
    g.box((0, 0, h * 0.62), (w, 0.08, 0.04), frame)


def fireplace(g, w, stone, dark, mantle):
    """Static surround; pair it with a flame prop placed in the hearth."""
    d = 0.55
    g.box((-w / 2 + 0.25, 0, 0.6), (0.5, d, 1.2), stone, bevel=0.02)
    g.box((w / 2 - 0.25, 0, 0.6), (0.5, d, 1.2), stone, bevel=0.02)
    g.box((0, 0, 1.12), (w, d, 0.24), stone, bevel=0.02)
    g.box((0, -0.05, 1.29), (w + 0.25, d + 0.15, 0.08), mantle, bevel=0.02)
    g.box((0, 0.15, 0.6), (w - 1.0, 0.2, 1.0), dark)
    g.box((0, -0.05, 0.05), (w - 1.0, d, 0.1), dark)
    g.box((0, -0.45, 0.02), (w + 0.3, 0.5, 0.04), stone)
    g.collide((0, 0, 0.7), (w, d, 1.4))


def lamp_post(g, metal, glass, h=3.2):
    g.cyl((0, 0, 0), 0.14, 0.25, metal, n=8, col=False)
    g.cyl((0, 0, 0.25), 0.05, h - 0.25, metal, n=8)
    g.collide((0, 0, h / 2), (0.25, 0.25, h))
    g.lathe((0, 0, h), [(0.08, 0), (0.16, 0.08), (0.14, 0.35), (0.2, 0.38), (0.02, 0.5)], metal, n=6, smooth=False)
    g.cyl((0, 0, h + 0.08), 0.12, 0.26, glass, n=6, smooth=False)


def fence(g, length, h, mat, post_mat=None, spacing=1.6, pickets=False, col=True):
    """Fence along +X from the origin."""
    post_mat = post_mat or mat
    n = max(1, round(length / spacing))
    for i in range(n + 1):
        x = length * i / n
        g.box((x, 0, h / 2), (0.1, 0.1, h), post_mat, bevel=0.01)
    if pickets:
        x = 0.1
        while x < length - 0.05:
            g.prism((x, 0, 0.05), [(-0.04, -0.015), (0.04, -0.015), (0.04, 0.015), (-0.04, 0.015)], h - 0.1, mat)
            g.box((x, 0, h - 0.02), (0.06, 0.03, 0.06), mat, ry=math.pi / 4)
            x += 0.15
    for z in (h * 0.3, h * 0.8):
        g.box((length / 2, -0.06, z), (length, 0.03, 0.1), mat)
    if col:
        g.collide((length / 2, 0, h / 2 + 0.2), (length, 0.15, h + 0.4))


def crate_geo(g, s, wood, dark):
    g.box((0, 0, s / 2), (s, s, s), wood, bevel=0.015)
    for ax in range(2):
        for sgn in (-1, 1):
            rz = 0 if ax == 0 else math.pi / 2
            with g.at((0, 0, 0), rz):
                g.box((0, sgn * (s / 2 + 0.005), s / 2), (s * 0.95, 0.02, s * 0.12), dark)
                g.box((0, sgn * (s / 2 + 0.008), s / 2), (s * 1.2, 0.02, s * 0.1), dark, ry=math.atan2(1, 1))


def barrel_geo(g, wood, hoop, h=0.9, r=0.32):
    g.lathe((0, 0, 0), [(r * 0.85, 0), (r, h * 0.25), (r * 1.06, h / 2), (r, h * 0.75), (r * 0.85, h)], wood, n=14)
    for z in (0.12, 0.3, 0.6, 0.78):
        rr = r * (0.88 + 0.18 * math.sin(math.pi * z / 1.0 * 0.95))
        g.torus((0, 0, z * h / 0.9), rr + 0.01, 0.012, hoop, n=16, m=4)


# ------------------------------------------------------------------ props

def door(p, w, h, wood, frame=None, panel=None, handle=None, hinge='left', thick=0.06, rest=0.0, open_dir=1):
    """Hinged door filling an opening of width w (origin at opening bottom centre, wall along X).
    The pivot is on the hinge edge and rotates about the vertical axis."""
    side = -1 if hinge == 'left' else 1
    pv = p.part('pivot', (side * w / 2, 0, 0), rz=rest * open_dir * -side)
    g = pv.geo
    cx = -side * w / 2
    g.box((cx, 0, h / 2), (w - 0.02, thick, h), wood, bevel=0.008)
    pm = panel or wood
    for zz in (h * 0.28, h * 0.7):
        for sy in (-1, 1):
            g.box((cx, sy * thick / 2, zz), (w * 0.62, 0.012, h * 0.3), pm, bevel=0.004)
    if handle is not None:
        for sy in (-1, 1):
            g.sphere((cx - side * (w / 2 - 0.12), sy * (thick / 2 + 0.04), h * 0.47), 0.035, handle, n=8)
    if frame is not None:
        for sx in (-1, 1):
            p.body.box((sx * (w / 2 + 0.05), 0, h / 2), (0.1, 0.36, h + 0.1), frame, bevel=0.01)
        p.body.box((0, 0, h + 0.05), (w + 0.2, 0.36, 0.12), frame, bevel=0.01)
    # client: angle = authored + dir * offset; offset `closed` (radians) is the shut position
    p.params.setdefault('axis', 'y')
    p.params.setdefault('dir', open_dir * -side)
    p.params.setdefault('closed', round(-rest, 4))
    p.params.setdefault('sound', 'bang')


def grandfather_clock(p, wood, brass, face, dark):
    b = p.body
    b.box((0, 0, 0.3), (0.62, 0.42, 0.6), wood, bevel=0.02)
    b.box((0, 0, 0.62), (0.68, 0.46, 0.05), wood, bevel=0.01)
    b.box((0, 0.02, 1.2), (0.48, 0.34, 1.1), wood, bevel=0.015)
    b.box((0, -0.16, 1.2), (0.36, 0.02, 0.95), dark)
    b.box((0, 0, 1.78), (0.64, 0.44, 0.06), wood, bevel=0.01)
    b.box((0, 0, 2.05), (0.6, 0.42, 0.5), wood, bevel=0.02)
    b.prism((0, 0.21, 2.3), [(-0.34, 0), (0.34, 0), (0.0, 0.0)], 0.01, wood)
    b.box((0, 0, 2.35), (0.66, 0.46, 0.08), wood, bevel=0.02)
    b.box((-0.2, 0, 2.47), (0.1, 0.3, 0.16), wood, bevel=0.02, rz=0.0)
    b.box((0.2, 0, 2.47), (0.1, 0.3, 0.16), wood, bevel=0.02)
    b.sphere((0, 0, 2.5), 0.06, brass, n=8)
    b.cyl((0, -0.2, 2.05), 0.2, 0.02, brass, n=20, rx=math.pi / 2)
    b.cyl((0, -0.215, 2.05), 0.175, 0.02, face, n=20, rx=math.pi / 2)
    for i in range(12):
        a = i * TAU / 12
        b.box((math.sin(a) * 0.15, -0.23, 2.05 + math.cos(a) * 0.15), (0.012, 0.01, 0.03), dark, ry=-a)
    b.collide((0, 0, 1.25), (0.62, 0.44, 2.5))
    hr = p.geo('hour', (0, -0.235, 2.05))
    hr.box((0, 0, 0.045), (0.022, 0.008, 0.1), dark)
    mn = p.geo('minute', (0, -0.24, 2.05))
    mn.box((0, 0, 0.065), (0.014, 0.008, 0.14), dark)
    b.sphere((0, -0.245, 2.05), 0.014, brass, n=6)
    pend = p.geo('pend', (0, -0.1, 1.68))
    pend.box((0, 0, -0.32), (0.015, 0.01, 0.64), brass)
    pend.cyl((0, 0.0, -0.66), 0.09, 0.02, brass, n=16, rx=math.pi / 2)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('sound', 'chime')


def candle(g, wax, pos=(0, 0, 0), h=0.18, r=0.025):
    g.cyl(pos, r, h, wax, n=8)
    g.cyl((pos[0], pos[1], pos[2] + h), r * 0.9, 0.008, wax, n=8, r2=r * 0.4)


def candelabra(p, metal, wax, arms=3, light='#ffb15c'):
    b = p.body
    b.lathe((0, 0, 0), [(0.09, 0), (0.08, 0.02), (0.03, 0.05), (0.02, 0.2), (0.035, 0.22), (0.018, 0.25), (0.018, 0.34)], metal, n=10)
    tops = [(0, 0, 0.34)]
    for i in range(arms - 1):
        a = i * TAU / (arms - 1)
        x, y = math.cos(a) * 0.14, math.sin(a) * 0.14
        b.tube([(0, 0, 0.27), (x * 0.5, y * 0.5, 0.25), (x, y, 0.27), (x, y, 0.32)], 0.01, metal, n=5)
        tops.append((x, y, 0.32))
    for t in tops:
        b.cyl((t[0], t[1], t[2]), 0.03, 0.015, metal, n=8, r2=0.04)
        candle(b, wax, (t[0], t[1], t[2] + 0.015), 0.12, 0.016)
        p.flame((t[0], t[1], t[2] + 0.145), size=0.6)
    p.light((0, 0, 0.55), light, 1.0, 6.0, part='flame0')
    p.params.setdefault('sound', 'whoomp')


def chandelier(p, metal, wax, drop=1.0, arms=6, radius=0.6, light='#ffbf6e'):
    """Hangs from the ceiling: origin at the ceiling attachment point."""
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.cyl((0, 0, -drop), 0.012, drop, metal, n=5)
    z = -drop
    g.lathe((0, 0, z - 0.35), [(0.02, 0), (0.08, 0.06), (0.06, 0.18), (0.1, 0.25), (0.03, 0.35)], metal, n=10)
    g.torus((0, 0, z - 0.25), radius, 0.018, metal, n=24, m=5)
    for i in range(arms):
        a = i * TAU / arms
        x, y = math.cos(a) * radius, math.sin(a) * radius
        g.tube([(0, 0, z - 0.3), (x * 0.5, y * 0.5, z - 0.38), (x, y, z - 0.25), (x, y, z - 0.18)], 0.012, metal, n=5)
        g.cyl((x, y, z - 0.18), 0.035, 0.02, metal, n=8, r2=0.045)
        candle(g, wax, (x, y, z - 0.16), 0.1, 0.016)
        p.flame((x, y, z - 0.055), size=0.6, parent='pivot')
        # crystal drops
        g.sphere((x * 0.75, y * 0.75, z - 0.42), 0.022, metal, n=6, s=(1, 1, 1.8))
    p.light((0, 0, -drop - 0.2), light, 2.0, 11.0, part='pivot')
    p.params.setdefault('amp', 0.015)
    p.params.setdefault('period', 3.2)
    p.params.setdefault('sound', 'clatter')


def hanging_lantern(p, metal, glass, drop=0.6):
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.cyl((0, 0, -drop), 0.01, drop, metal, n=4)
    z = -drop
    g.torus((0, 0, z - 0.03), 0.04, 0.008, metal, n=8, m=4, rx=math.pi / 2)
    g.lathe((0, 0, z - 0.42), [(0.1, 0), (0.12, 0.02), (0.12, 0.05), (0.09, 0.07), (0.09, 0.3), (0.13, 0.32), (0.04, 0.42)], metal, n=6, smooth=False, cap_bottom=True)
    g.cyl((0, 0, z - 0.36), 0.085, 0.24, glass, n=6, smooth=False)
    p.flame((0, 0, z - 0.33), size=0.8, parent='pivot')
    p.light((0, 0, z - 0.25), '#ffb35c', 1.2, 7.0, part='pivot')
    p.params.setdefault('amp', 0.04)
    p.params.setdefault('period', 2.0)
    p.params.setdefault('sound', 'creak')


def rocking_chair(p, wood, seat=None):
    seat = seat or wood
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    for sx in (-1, 1):
        pts = [(sx * 0.25, -0.45 + 0.9 * i / 8, 0.06 + 0.12 * ((i / 8 - 0.5) * 2) ** 2) for i in range(9)]
        g.tube(pts, 0.022, wood, n=5)
        g.box((sx * 0.25, -0.15, 0.25), (0.04, 0.04, 0.42), wood)
        g.box((sx * 0.25, 0.22, 0.25), (0.04, 0.04, 0.42), wood)
        g.box((sx * 0.25, 0.27, 0.8), (0.045, 0.045, 0.75), wood, rx=-0.15)
        g.box((sx * 0.25, 0.02, 0.62), (0.05, 0.42, 0.04), wood)
    g.box((0, 0.03, 0.46), (0.52, 0.48, 0.05), seat, bevel=0.01)
    for i in range(5):
        g.box((-0.18 + i * 0.09, 0.3, 0.85), (0.035, 0.025, 0.7), wood, rx=-0.15)
    g.box((0, 0.33, 1.18), (0.56, 0.05, 0.08), wood, rx=-0.15, bevel=0.01)
    p.body.collide((0, 0, 0.5), (0.6, 0.8, 1.0))
    p.params.setdefault('axis', 'x')
    p.params.setdefault('sound', 'creak')


def chair(p, wood, seat=None, back='slats'):
    seat = seat or wood
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box((sx * 0.2, sy * 0.19, 0.22), (0.045, 0.045, 0.44), wood)
        g.box((sx * 0.2, 0.2, 0.75), (0.045, 0.045, 0.62), wood, rx=-0.08)
    g.box((0, 0, 0.47), (0.48, 0.46, 0.06), seat, bevel=0.012)
    if back == 'slats':
        for i in range(3):
            g.box((-0.1 + i * 0.1, 0.22, 0.78), (0.04, 0.02, 0.5), wood, rx=-0.08)
    else:
        g.box((0, 0.22, 0.8), (0.36, 0.04, 0.44), seat, rx=-0.08, bevel=0.015)
    g.box((0, 0.24, 1.05), (0.46, 0.05, 0.07), wood, rx=-0.08, bevel=0.01)
    p.params.setdefault('sound', 'thud')


def crate(p, wood, dark, s=0.7):
    pv = p.part('pivot', (0, 0, 0))
    crate_geo(pv.geo, s, wood, dark)
    p.body.collide((0, 0, s / 2), (s, s, s))
    p.params.setdefault('sound', 'thud')


def barrel(p, wood, hoop, h=0.9, r=0.32):
    pv = p.part('pivot', (0, 0, 0))
    barrel_geo(pv.geo, wood, hoop, h, r)
    p.body.collide((0, 0, h / 2), (r * 2, r * 2, h))
    p.params.setdefault('sound', 'thud')


def tree(p, bark, leaves, h=5.0, crown=2.0, seed=0, lumps=5, style='round', col=True):
    """Foliage prop. leaves: list of materials. The whole tree sways from its base."""
    rng = random.Random(seed)
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    trunk_h = h * 0.55
    pts = [(0, 0, 0)]
    lean = rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25)
    for i in range(1, 6):
        t = i / 5
        pts.append((lean[0] * t * t, lean[1] * t * t, trunk_h * t))
    g.lathe((0, 0, 0), [(0.35, 0), (0.22, 0.25), (0.18, 0.4)], bark, n=7, smooth=False)
    g.tube(pts, 0.17, bark, n=7)
    top = pts[-1]
    for i in range(3):
        a = rng.uniform(0, TAU)
        ln = rng.uniform(0.7, 1.2) * crown * 0.6
        g.tube([(top[0] * 0.8, top[1] * 0.8, trunk_h * 0.8),
                (top[0] + math.cos(a) * ln * 0.5, top[1] + math.sin(a) * ln * 0.5, trunk_h + 0.4),
                (top[0] + math.cos(a) * ln, top[1] + math.sin(a) * ln, trunk_h + 0.9)], 0.07, bark, n=5)
    if style == 'pine':
        for i in range(lumps):
            t = i / max(1, lumps - 1)
            rr = crown * (1 - t * 0.75)
            g.cyl((top[0], top[1], h * 0.3 + (h * 0.65) * t), rr, h * 0.32, rng.choice(leaves), n=8, r2=0.02, smooth=False)
    elif style != 'bare':
        for i in range(lumps):
            a = TAU * i / lumps + rng.uniform(-0.4, 0.4)
            d = crown * rng.uniform(0.25, 0.6)
            c = (top[0] + math.cos(a) * d, top[1] + math.sin(a) * d, trunk_h + crown * rng.uniform(0.3, 0.9))
            g.blob(c, crown * rng.uniform(0.5, 0.75), rng.choice(leaves), seed=seed * 31 + i, jitter=0.2, s=(1, 1, 0.8))
        g.blob((top[0], top[1], trunk_h + crown * 1.0), crown * 0.75, rng.choice(leaves), seed=seed + 99, jitter=0.2, s=(1, 1, 0.85))
    if col:
        p.body.collide((0, 0, trunk_h / 2), (0.45, 0.45, trunk_h))
    p.params.setdefault('amp', 0.012)
    p.params.setdefault('sound', 'rustle')


def bush(p, leaves, r=0.8, seed=0):
    rng = random.Random(seed)
    pv = p.part('pivot', (0, 0, 0))
    for i in range(4):
        a = rng.uniform(0, TAU)
        d = r * 0.4
        pv.geo.blob((math.cos(a) * d, math.sin(a) * d, r * 0.55), r * rng.uniform(0.55, 0.8), rng.choice(leaves),
                    seed=seed * 7 + i, jitter=0.2, s=(1, 1, 0.75))
    p.params.setdefault('amp', 0.02)
    p.params.setdefault('sound', 'rustle')


def curtains(p, w, h, fabric, rod, gather=0.35):
    """Pair of drapes hanging from a rod; origin at the rod centre (top of window), wall along X."""
    p.body.cyl((-w / 2 - 0.15, -0.12, 0), 0.02, w + 0.3, rod, n=6, ry=math.pi / 2)
    for sx in (-1, 1):
        p.body.sphere((sx * (w / 2 + 0.17), -0.12, 0), 0.04, rod, n=8)
    for i, sx in enumerate((-1, 1)):
        g = p.geo(f'cloth{i}', (sx * (w / 2 - w * gather / 2), -0.12, -0.02))
        g.sheet((0, 0, 0), w * gather, h, fabric, nx=6, ny=10)
        # pleats are faked by the client's wave shader; add a tie-back
    p.params.setdefault('amp', 0.05)
    p.params.setdefault('sound', 'whoosh')


def portrait(p, w, h, frame, canvas):
    """Hangs on a wall facing -Y; pivot at the nail (top centre). Swings like a pendulum when bumped."""
    pv = p.part('pivot', (0, -0.03, 0))
    g = pv.geo
    g.box((0, -0.02, -h / 2 - 0.06), (w - 0.1, 0.02, h - 0.1), canvas)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.04), -0.03, -h / 2 - 0.06), (0.09, 0.05, h), frame, bevel=0.012)
    for zc in (-0.06 - 0.045, -0.06 - h + 0.045):
        g.box((0, -0.03, zc), (w, 0.05, 0.09), frame, bevel=0.012)
    g.tube([(-w * 0.3, -0.01, -0.12), (0, -0.01, 0.0), (w * 0.3, -0.01, -0.12)], 0.004, frame, n=3, caps=False)
    p.params.setdefault('axes', 'z')
    p.params.setdefault('amp', 0.0)
    p.params.setdefault('sound', 'clatter')


def globe(p, wood, brass, sea, land):
    b = p.body
    b.lathe((0, 0, 0), [(0.22, 0), (0.2, 0.04), (0.05, 0.08), (0.04, 0.6), (0.07, 0.65)], wood, n=10)
    b.torus((0, 0, 0.98), 0.3, 0.012, brass, n=24, m=4, rx=math.pi / 2)
    pv = p.part('pivot', (0, 0, 0.98), rx=0.4)
    g = pv.geo
    g.sphere((0, 0, 0), 0.27, sea, n=16)
    rng = random.Random(4)
    for i in range(7):
        a, e = rng.uniform(0, TAU), rng.uniform(-0.9, 0.9)
        c = (math.cos(a) * math.cos(e) * 0.262, math.sin(a) * math.cos(e) * 0.262, math.sin(e) * 0.262)
        g.blob(c, rng.uniform(0.06, 0.11), land, seed=i, jitter=0.25, s=(1, 1, 0.35), rz=a)
    g.cyl((0, 0, -0.32), 0.008, 0.64, brass, n=4)
    b.collide((0, 0, 0.6), (0.6, 0.6, 1.2))
    p.params.setdefault('axis', 'y')
    p.params.setdefault('speed', 0.0)
    p.params.setdefault('sound', 'whirr')


def upright_piano(p, wood, keys_white, keys_black, brass):
    b = p.body
    b.box((0, 0.15, 0.7), (1.5, 0.55, 1.4), wood, bevel=0.02)
    b.box((0, -0.18, 0.7), (1.5, 0.3, 0.12), wood, bevel=0.01)
    b.box((0, -0.2, 0.78), (1.3, 0.22, 0.04), keys_white)
    for i in range(36):
        if i % 7 in (2, 6):
            continue
        b.box((-0.62 + i * 0.036, -0.24, 0.81), (0.018, 0.12, 0.03), keys_black)
    for sx in (-1, 1):
        b.box((sx * 0.68, -0.25, 0.35), (0.08, 0.08, 0.7), wood, bevel=0.01)
        b.lathe((sx * 0.3, -0.3, 0.06), [(0.02, 0), (0.025, 0.05)], brass, n=6)
    b.collide((0, 0.05, 0.7), (1.5, 0.75, 1.4))
    lid = p.part('pivot', (0, -0.12, 1.4))
    lid.geo.box((0, 0.12, 0.015), (1.52, 0.32, 0.03), wood, bevel=0.008)
    p.params.setdefault('axis', 'x')
    p.params.setdefault('instrument', 'piano')


def bell(p, metal, wood, r=0.25):
    """Bell hanging from a yoke; origin at the yoke axle."""
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.lathe((0, 0, -r * 2.2), [(r, 0), (r * 0.95, r * 0.15), (r * 0.6, r * 1.0), (r * 0.5, r * 1.8), (r * 0.25, r * 2.0), (0.01, r * 2.05)], metal, n=16)
    g.box((0, 0, 0), (0.08, r * 2.6, 0.1), wood)
    g.sphere((0, 0, -r * 1.95), r * 0.18, metal, n=8)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('tone', 420)
    p.params.setdefault('sound', 'bell')


def music_box(p, wood, brass, felt):
    b = p.body
    b.box((0, 0, 0.06), (0.24, 0.16, 0.12), wood, bevel=0.01)
    b.box((0, 0, 0.12), (0.22, 0.14, 0.005), felt)
    b.cyl((0.13, 0, 0.06), 0.008, 0.04, brass, n=6, ry=math.pi / 2)
    b.box((0.17, 0, 0.06), (0.01, 0.06, 0.012), brass)
    lid = p.part('pivot', (0, 0.08, 0.12), rx=0.9)
    lid.geo.box((0, -0.08, 0.012), (0.24, 0.16, 0.024), wood, bevel=0.006)
    tiny = p.part('dancer', (0, 0, 0.125))
    tiny.geo.lathe((0, 0, 0), [(0.02, 0), (0.008, 0.03), (0.004, 0.05), (0.008, 0.06), (0.001, 0.07)], brass, n=6)
    p.params.setdefault('axis', 'x')
    p.params.setdefault('instrument', 'musicbox')
