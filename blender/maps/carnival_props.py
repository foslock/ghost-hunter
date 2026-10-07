"""Prefabs for Lanternfall Carnival (blender/maps/carnival.py).

Static prefabs: fn(geo, P, ...) drawn relative to the current transform (front faces -Y).
Prop prefabs:   fn(prop, P, ...) drawing into prop parts, used with MapBuilder.place.
`P` is the palette namespace returned by palette(m).
"""
import math
import random
from types import SimpleNamespace

import numpy as np

from lib import gh, tex
from lib.gh import TAU

PI = math.pi
cos, sin = math.cos, math.sin


# ================================================================ palette

def _grime(img, amount=0.35, frac=0.35, streaks=0.12, seed=0):
    """Darken the lower part of a tile (mud splash) and add vertical drip streaks."""
    h, w, _ = img.shape
    rows = np.linspace(0.0, 1.0, h)[:, None]
    n = tex.fbm((h, w), 6, 3, seed)
    g = np.clip((rows - (1 - frac)) / frac + (n - 0.5) * 0.5, 0, 1) ** 1.4
    s = tex.value_noise((h, w), (3, 40), seed + 5) ** 4
    img = img * (1 - amount * g - streaks * s)[..., None]
    return np.clip(img, 0, 1)


def _stains(img, amount=0.18, seed=0):
    n = tex.fbm(img.shape[:2], 3, 4, seed)
    k = np.clip((n - 0.55) * 4, 0, 1)
    return np.clip(img * (1 - amount * k)[..., None], 0, 1)


def _boards(base, dark, weathered, seed=7, wear=0.2, cells=14):
    """Painted boards with fine flaking paint (smaller, darker flecks than tex.boards' wear)."""
    img = tex.boards(base=base, dark=dark, weathered=weathered, wear=0.0, seed=seed)
    h, w, _ = img.shape
    n = tex.fbm((h, w), (cells // 2, cells), 4, seed + 11)
    peel = np.clip((n - (1 - wear * 0.75)) * 10, 0, 1)
    wc = tex.hex_rgb(weathered)
    img = img * (1 - peel[..., None]) + wc * peel[..., None] * (0.8 + 0.4 * n[..., None])
    return _grime(np.clip(img, 0, 1), seed=seed)


def _mirror(size=256):
    y = np.arange(size)[:, None] / size
    x = np.arange(size)[None, :] / size
    d = (x + y * 0.55) % 1.0
    streak = np.exp(-((d - 0.3) / 0.06) ** 2) * 0.45 + np.exp(-((d - 0.45) / 0.02) ** 2) * 0.35
    base = tex.hex_rgb('#4f5b7a')
    img = base * (0.7 + 0.45 * (1 - y))[..., None] + streak[..., None] * tex.hex_rgb('#c9d2e8')
    return np.clip(img, 0, 1)


def palette(m):
    P = SimpleNamespace()
    # --- large surfaces (textured)
    P.grass = m.mat('grass', image=tex.ground(a='#1f281d', b='#2e3524', c='#3d3326', seed=8, scale=6), uv=10.0)
    P.dirt = m.mat('dirt', image=tex.ground(a='#4c3f31', b='#61523f', c='#3a2f25', seed=31, scale=4), uv=7.0)
    P.sawdust = m.mat('sawdust', image=tex.ground(a='#8a7250', b='#a08660', c='#6e5a40', seed=12, scale=8), uv=3.0)
    P.planks = m.mat('planks', image=tex.wood_planks(base='#584432', dark='#2a2019', light='#776047', seed=4), uv=2.4)
    P.boards_red = m.mat('boards_red', image=_boards('#8a3a30', '#2c1410', '#6f6456', seed=7, wear=0.22), uv=2.6)
    P.boards_teal = m.mat('boards_teal', image=_boards('#3a6b66', '#152828', '#6d6a5c', seed=17, wear=0.26), uv=2.6)
    P.boards_cream = m.mat('boards_cream', image=_boards('#c4b48f', '#4a3d2e', '#7d705c', seed=27, wear=0.2), uv=2.6)
    P.boards_indigo = m.mat('boards_indigo', image=_boards('#33345a', '#121328', '#5f5a6c', seed=37, wear=0.2), uv=2.6)
    P.checker = m.mat('checker', image=tex.checker_tiles(a='#c7b994', b='#2c2d47', tiles=4, seed=5), uv=2.4)
    P.canvas_red = m.mat('canvas_red', image=_stains(tex.fabric(size=256, base='#983f35', seed=41), seed=1), uv=3.0)
    P.canvas_cream = m.mat('canvas_cream', image=_stains(tex.fabric(size=256, base='#d0bf99', seed=42), seed=2), uv=3.0)
    P.canvas_teal = m.mat('canvas_teal', image=_stains(tex.fabric(size=256, base='#3c736d', seed=43), seed=3), uv=3.0)
    P.canvas_mustard = m.mat('canvas_mustard', image=_stains(tex.fabric(size=256, base='#bf8f2e', seed=44), seed=4), uv=3.0)
    P.tarp = m.mat('tarp', image=_stains(tex.fabric(size=256, base='#565240', seed=45), amount=0.3, seed=5), uv=2.0)
    P.velvet = m.mat('velvet', image=tex.fabric(size=256, base='#4a2342', seed=46, pattern='diamonds', pattern_col='#a8843e'), uv=0.8)
    # --- flat paints and materials
    P.wood = m.mat('wood', '#5c412b', rough=0.8)
    P.wood_dark = m.mat('wood_dark', '#30241b', rough=0.85)
    P.iron = m.mat('iron', '#27231f', rough=0.6, metal=0.4)
    P.brass = m.mat('brass', '#b08b45', rough=0.4, metal=0.45)
    P.red = m.mat('red_paint', '#953a30', rough=0.7)
    P.cream = m.mat('cream_paint', '#d8cba9', rough=0.75)
    P.teal = m.mat('teal_paint', '#3c7670', rough=0.7)
    P.indigo = m.mat('indigo_paint', '#2d2e52', rough=0.7)
    P.mustard = m.mat('mustard_paint', '#c0902d', rough=0.65)
    P.black = m.mat('black', '#121014', rough=0.9)
    P.stone = m.mat('stone', '#4a4541', rough=0.95)
    P.rope = m.mat('rope', '#8a7553', rough=0.95)
    P.hay = m.mat('hay', '#9c8146', rough=0.95)
    P.pink = m.mat('plush_pink', '#c08883', rough=0.95)
    P.fur = m.mat('plush_brown', '#7a5536', rough=0.95)
    P.popcorn = m.mat('popcorn', '#ecd9a0', rough=0.9)
    P.glass = m.mat('glass_dark', '#26303a', rough=0.12, metal=0.2)
    P.bottle = m.mat('bottle_green', '#35513a', rough=0.15)
    P.mirror = m.mat('mirror', image=_mirror(), uv=2.2, rough=0.08, metal=0.3)
    P.puddle = m.mat('puddle', '#14172a', rough=0.04, metal=0.3)
    P.leaf = [m.mat('leaf1', '#1f2b1e'), m.mat('leaf2', '#29331f')]
    P.bark = m.mat('bark', '#2b221b')
    P.balloons = [m.mat('balloon_red', '#c0443a', rough=0.25), m.mat('balloon_teal', '#4b9890', rough=0.25),
                  m.mat('balloon_mustard', '#d6a33c', rough=0.25), m.mat('balloon_cream', '#e6dcc4', rough=0.25)]
    # --- emissive
    P.bulb = m.mat('bulb', '#ffe0b0', rough=0.4, emit='#ffb050', strength=9.0)
    P.bulb_red = m.mat('bulb_red', '#ffb0a0', rough=0.4, emit='#ff5a3a', strength=7.0)
    P.bulb_dead = m.mat('bulb_dead', '#4c4640', rough=0.2)
    P.lamp = m.mat('lamp_glass', '#ffd9a8', rough=0.5, emit='#ffaa55', strength=2.5)
    P.window = m.mat('window_glow', '#d89a5c', rough=0.6, emit='#cf7d34', strength=1.6)
    P.ember = m.mat('ember', '#ff7a30', rough=1.0, emit='#ff4a10', strength=4.0)
    P.crystal = m.mat('crystal', '#b4b8ff', rough=0.1, emit='#7f78ff', strength=3.5)
    P.glow = m.mat('altar_glow', '#8ff0dc', rough=0.4, emit='#3fd0b0', strength=4.0)
    return P


# ================================================================ helpers

def W(origin, rz, local):
    """Prop/structure-local point -> world."""
    c, s = cos(rz), sin(rz)
    lx, ly = local[0], local[1]
    lz = local[2] if len(local) > 2 else 0.0
    oz = origin[2] if len(origin) > 2 else 0.0
    return (origin[0] + lx * c - ly * s, origin[1] + lx * s + ly * c, oz + lz)


def catenary(a, b, sag, n=14):
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                    a[2] + (b[2] - a[2]) * t - sag * 4 * t * (1 - t)))
    return pts


def cat_point(a, b, sag, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t - sag * 4 * t * (1 - t))


def prim_pennant(w, h, nx=3, ny=6, shape='tri'):
    """Flag hanging down from z=0 in the XZ plane. shape: tri | scallop | rect."""
    verts, faces = [], []
    for j in range(ny + 1):
        t = j / ny
        if shape == 'tri':
            k = max(0.02, 1 - t)
        elif shape == 'scallop':
            k = 1.0 if t < 0.45 else max(0.05, math.sqrt(max(0.0, 1 - ((t - 0.45) / 0.55) ** 2)))
        else:
            k = 1.0
        for i in range(nx + 1):
            u = -0.5 + i / nx
            verts.append((u * w * k, 0.0, -h * t))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + nx + 1, a + nx + 2, a + 1))
    off = len(verts)
    verts += [(x, y + 0.003, z) for x, y, z in verts]
    faces += [tuple(off + i for i in reversed(f)) for f in faces[:]]
    return verts, faces, [True] * len(faces)


def prim_quad(a, b, c, d):
    return [a, b, c, d], [(0, 1, 2, 3)], [False]


def prim_strip(top, bot, smooth=False):
    """Quad strip between two polylines of equal length."""
    verts = list(top) + list(bot)
    n = len(top)
    faces = [(i, n + i, n + i + 1, i + 1) for i in range(n - 1)]
    return verts, faces, [smooth] * len(faces)


_BULB = {}


def sqrt_safe(v):
    return math.sqrt(max(0.0, v))


def bulb(g, c, mat, r=0.045):
    """Small smooth-shaded icosahedron (12 verts once exported)."""
    if r not in _BULB:
        v, f, _ = gh.prim_ico(r, 0, 0.0, 0)
        _BULB[r] = (v, f, [True] * len(f))
    g.add(_BULB[r], mat, gh.X(c))


def soft_blob(g, c, r, mat, seed=0, jitter=0.2, s=None):
    v, f, _ = gh.prim_ico(r, 1, jitter, seed)
    g.add((v, f, [True] * len(f)), mat, gh.X(c, s=s))


def seg_col(g, a, b, t, z0, z1, step=0.7):
    """Colliders along a (possibly diagonal) wall segment a->b."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(math.ceil(L / step)))
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for i in range(n):
        tm = (i + 0.5) / n
        c = (a[0] + (b[0] - a[0]) * tm, a[1] + (b[1] - a[1]) * tm, (z0 + z1) / 2)
        g.collide(c, (L / n, t, z1 - z0), rz=ang)


def wedge_drum(g, c, r0, r1, h, mats, n=12, smooth=False):
    """Drum made of alternating coloured wedges (circus tub / striped barrel)."""
    for k in range(n):
        prim = gh.prim_lathe([(r0, 0.0), (r1, h)], 2, False, False, smooth, arc=TAU / n)
        g.add(prim, mats[k % len(mats)], gh.X(c, rz=k * TAU / n))


def wedge_cone(g, c, r0, z0, r1, z1, mats, n=12, rows=1, smooth=True, sag=0.0):
    """Cone/umbrella made of alternating gores."""
    prof = []
    for i in range(rows + 1):
        t = i / rows
        prof.append((r0 + (r1 - r0) * t, z0 + (z1 - z0) * t - sag * 4 * t * (1 - t)))
    for k in range(n):
        prim = gh.prim_lathe(prof, 2, False, False, smooth, arc=TAU / n)
        g.add(prim, mats[k % len(mats)], gh.X(c, rz=k * TAU / n))


def ball_wedges(g, c, r, mats, n=8):
    prof = [(max(r * math.sin(PI * i / 8), 1e-3), -r * math.cos(PI * i / 8)) for i in range(9)]
    for k in range(n):
        g.add(gh.prim_lathe(prof, 3, False, False, True, arc=TAU / n), mats[k % len(mats)], gh.X(c, rz=k * TAU / n))


FONT = {
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
    'C': ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
    'D': ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
    'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
    'F': ['#####', '#....', '#....', '####.', '#....', '#....', '#....'],
    'G': ['.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.###.'],
    'H': ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'I': ['.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    'K': ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'],
    'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
    'M': ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'],
    'N': ['#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#', '#...#'],
    'O': ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'P': ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'V': ['#...#', '#...#', '#...#', '#...#', '.#.#.', '.#.#.', '..#..'],
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'],
    'X': ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'],
    'Y': ['#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'],
    'Z': ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
    ' ': ['.....'] * 7,
}


def text_dots(text, pitch):
    """Lit dots (u, v, letter_index) of a 5x7 dot-matrix string centred on u=0, v>=0."""
    pts = []
    total = len(text) * 6 - 1
    for ci, ch in enumerate(text):
        for r, row in enumerate(FONT[ch]):
            for c, cell in enumerate(row):
                if cell == '#':
                    pts.append(((ci * 6 + c - (total - 1) / 2) * pitch, (6 - r) * pitch, ci))
    return pts


def painted_letters(g, text, origin, pitch, mat, depth=0.02):
    """Blocky painted lettering on a board facing -Y: one quad per horizontal run of dots."""
    total = len(text) * 6 - 1
    y = origin[1] - depth / 2
    for ci, ch in enumerate(text):
        for r, row in enumerate(FONT[ch]):
            c = 0
            while c < 5:
                if row[c] != '#':
                    c += 1
                    continue
                c0 = c
                while c < 5 and row[c] == '#':
                    c += 1
                u0 = (ci * 6 + c0 - (total - 1) / 2 - 0.5) * pitch
                u1 = (ci * 6 + c - 1 - (total - 1) / 2 + 0.5) * pitch
                v0 = (6 - r - 0.5) * pitch
                v1 = v0 + pitch
                ox, oz = origin[0], origin[2]
                g.add(prim_quad((ox + u0, y, oz + v0), (ox + u1, y, oz + v0), (ox + u1, y, oz + v1), (ox + u0, y, oz + v1)), mat)


# ================================================================ small static prefabs

def altar(g, P):
    """Relic altar: an indigo-and-gold lantern plinth with a glowing brass bowl. Identical everywhere."""
    g.box((0, 0, 0.07), (0.96, 0.96, 0.14), P.wood_dark, bevel=0.03, col=True)
    g.box((0, 0, 0.17), (0.78, 0.78, 0.07), P.mustard, bevel=0.02)
    g.lathe((0, 0, 0.2), [(0.34, 0.0), (0.22, 0.16), (0.2, 0.55), (0.3, 0.66)], P.indigo, n=8, smooth=False)
    for z in (0.24, 0.72):
        g.torus((0, 0, z), 0.235 if z < 0.5 else 0.215, 0.022, P.brass, n=12, m=4)
    g.lathe((0, 0, 0.86), [(0.12, 0.0), (0.3, 0.06), (0.36, 0.12), (0.37, 0.14)], P.brass, n=12)
    g.torus((0, 0, 0.995), 0.3, 0.022, P.glow, n=16, m=4)
    g.cyl((0, 0, 0.9), 0.24, 0.02, P.black, n=12)
    for k in range(4):
        a = k * TAU / 4 + TAU / 8
        x, y = cos(a) * 0.4, sin(a) * 0.4
        g.cyl((x, y, 0.14), 0.025, 0.42, P.iron, n=5, caps=False)
        g.lathe((x, y, 0.56), [(0.05, 0), (0.06, 0.03), (0.045, 0.09), (0.01, 0.13)], P.iron, n=5, cap_top=False)
        bulb(g, (x, y, 0.6), P.glow, 0.035)
    g.collide((0, 0, 0.5), (0.9, 0.9, 1.0))
    return 1.0


def crate_static(g, P, s=0.7, rz=0.0, pos=(0, 0, 0)):
    with g.at(pos, rz):
        g.box((0, 0, s / 2), (s, s, s), P.wood, bevel=0.015)
        for ax in range(2):
            for sgn in (-1, 1):
                with g.at((0, 0, 0), 0 if ax == 0 else PI / 2):
                    g.box((0, sgn * (s / 2 + 0.006), s / 2), (s * 0.96, 0.02, s * 0.12), P.wood_dark)
                    g.box((0, sgn * (s / 2 + 0.006), s * 0.12), (s * 0.96, 0.02, s * 0.08), P.wood_dark)
                    g.box((0, sgn * (s / 2 + 0.006), s * 0.88), (s * 0.96, 0.02, s * 0.08), P.wood_dark)
        g.collide((0, 0, s / 2), (s, s, s))


def barrel_static(g, P, pos=(0, 0, 0), h=0.9, r=0.32, mat=None, tipped=False):
    with g.at(pos):
        if tipped:
            with g.at((0, 0, r), rx=PI / 2):
                g.lathe((0, 0, -h / 2), [(r * 0.85, 0), (r, h * 0.25), (r * 1.06, h / 2), (r, h * 0.75), (r * 0.85, h)], mat or P.wood, n=14)
            g.collide((0, 0, r), (2 * r, h, 2 * r))
        else:
            g.lathe((0, 0, 0), [(r * 0.85, 0), (r, h * 0.25), (r * 1.06, h / 2), (r, h * 0.75), (r * 0.85, h)], mat or P.wood, n=14)
            for z in (0.12, 0.82):
                g.torus((0, 0, z * h), r * 0.93, 0.013, P.iron, n=16, m=4)
            g.cyl((0, 0, h - 0.01), r * 0.85, 0.012, P.wood_dark, n=14)
            g.collide((0, 0, h / 2), (2 * r, 2 * r, h))


def hay_bale(g, P, pos=(0, 0, 0), rz=0.0, s=(1.0, 0.5, 0.42)):
    with g.at(pos, rz):
        g.box((0, 0, s[2] / 2), s, P.hay, bevel=0.06)
        for x in (-s[0] * 0.25, s[0] * 0.25):
            g.box((x, 0, s[2] / 2), (0.03, s[1] + 0.012, s[2] + 0.012), P.rope)
        g.collide((0, 0, s[2] / 2), s)


def spoked_wheel(g, P, c, r, rz=0.0, spokes=10, rim=None, spoke=None, hub=None, t=0.06):
    """Cart wheel; the wheel plane is local XZ (axle along local Y)."""
    rim = rim or P.wood_dark
    spoke = spoke or P.wood
    hub = hub or P.iron
    with g.at(c, rz):
        g.torus((0, 0, 0), r - t / 2, t / 2, rim, n=16, m=4, rx=PI / 2)
        g.cyl((0, -0.07, 0), r * 0.16, 0.14, hub, n=8, rx=-PI / 2)
        spokes = min(spokes, 10)
        for k in range(spokes):
            a = k * TAU / spokes
            g.tube([(cos(a) * r * 0.14, 0, sin(a) * r * 0.14), (cos(a) * (r - t), 0, sin(a) * (r - t))], 0.022, spoke, n=4, caps=False)


def bench(g, P, pos, rz=0.0, w=1.6):
    with g.at(pos, rz):
        for sx in (-1, 1):
            g.box((sx * (w / 2 - 0.1), 0, 0.22), (0.06, 0.45, 0.44), P.iron)
            g.box((sx * (w / 2 - 0.1), 0.2, 0.62), (0.05, 0.05, 0.4), P.iron)
            g.box((sx * (w / 2 - 0.1), -0.05, 0.62), (0.05, 0.4, 0.04), P.iron)
        for i in range(3):
            g.box((0, -0.15 + i * 0.15, 0.45), (w, 0.12, 0.04), P.teal, bevel=0.01)
        for i in range(2):
            g.box((0, 0.23, 0.6 + i * 0.16), (w, 0.04, 0.11), P.teal, bevel=0.01)
        g.collide((0, 0, 0.4), (w, 0.5, 0.8))


def picnic_table(g, P, pos, rz=0.0, w=2.0):
    with g.at(pos, rz):
        g.box((0, 0, 0.74), (w, 0.8, 0.05), P.wood, bevel=0.01)
        for sy in (-1, 1):
            g.box((0, sy * 0.68, 0.44), (w, 0.28, 0.045), P.wood, bevel=0.01)
        for sx in (-1, 1):
            for sy in (-1, 1):
                g.tube([(sx * (w / 2 - 0.25), sy * 0.75, 0), (sx * (w / 2 - 0.25), sy * 0.05, 0.72)], 0.03, P.wood_dark, n=4)
        g.collide((0, 0, 0.38), (w, 1.7, 0.76))


def trash_barrel(g, P, pos, mat=None):
    with g.at(pos):
        g.cyl((0, 0, 0), 0.28, 0.85, mat or P.teal, n=12)
        g.torus((0, 0, 0.85), 0.28, 0.02, P.iron, n=12, m=4)
        g.torus((0, 0, 0.1), 0.28, 0.015, P.iron, n=12, m=4)
        g.cyl((0, 0, 0.8), 0.25, 0.02, P.black, n=12)
        g.box((0.05, 0.04, 0.88), (0.12, 0.09, 0.14), P.red, rz=0.4, ry=0.3)
        g.box((-0.08, -0.06, 0.86), (0.1, 0.08, 0.1), P.cream, rz=-0.3, rx=0.4)
        g.collide((0, 0, 0.43), (0.56, 0.56, 0.86))


def popcorn_box(g, P, pos, rz=0.0, tipped=False):
    with g.at(pos, rz):
        if tipped:
            with g.at((0, 0, 0.05), rx=PI / 2 - 0.1):
                g.lathe((0, 0, -0.06), [(0.04, 0), (0.055, 0.15)], P.red, n=6, smooth=False, cap_top=False)
            for k in range(5):
                bulb(g, (0.03 * k - 0.05, -0.12 - 0.05 * (k % 3), 0.02), P.popcorn, 0.018)
        else:
            g.lathe((0, 0, 0), [(0.04, 0), (0.055, 0.15)], P.red, n=6, smooth=False, cap_top=False)
            g.blob((0, 0, 0.15), 0.05, P.popcorn, seed=3, subdiv=1, s=(1, 1, 0.6))


def ticket_litter(g, P, pos, n=5, seed=0, spread=0.8):
    rng = random.Random(seed)
    for i in range(n):
        g.box((pos[0] + rng.uniform(-spread, spread), pos[1] + rng.uniform(-spread, spread), 0.025),
              (0.09, 0.045, 0.004), P.cream if i % 3 else P.red, rz=rng.uniform(0, PI))


def puddle(g, P, pos, r=0.8, seed=0, rz=0.0):
    pts = []
    rng = random.Random(seed)
    for k in range(14):
        a = k * TAU / 14
        rr = r * rng.uniform(0.75, 1.15)
        pts.append((pos[0] + cos(a + rz) * rr, pos[1] + sin(a + rz) * rr * 0.65))
    g.prism((0, 0, 0), pts, 0.03, P.puddle)


def deflated_balloon(g, P, pos, mat, rz=0.0):
    with g.at(pos, rz):
        g.blob((0, 0, 0.03), 0.16, mat, seed=5, jitter=0.3, subdiv=1, s=(1, 0.8, 0.18))
        g.tube([(0.15, 0, 0.02), (0.4, 0.08, 0.01), (0.7, -0.05, 0.01)], 0.004, P.cream, n=3)


def lamp_static(g, P, pos, h=2.9, lit=True):
    """Iron lamp standard with a frosted globe (no real light)."""
    with g.at(pos):
        g.lathe((0, 0, 0), [(0.18, 0), (0.18, 0.07), (0.12, 0.13), (0.08, 0.4), (0.06, 0.48)], P.iron, n=8)
        g.cyl((0, 0, 0.48), 0.045, h - 0.48, P.iron, n=8)
        g.torus((0, 0, h - 0.3), 0.06, 0.018, P.brass, n=8, m=4)
        g.sphere((0, 0, h + 0.14), 0.17, P.lamp if lit else P.glass, n=12)
        g.cyl((0, 0, h - 0.04), 0.09, 0.06, P.iron, n=8)
        g.collide((0, 0, h / 2), (0.3, 0.3, h))


def tree_static(g, P, pos, h=7.0, crown=2.6, seed=0, style='round'):
    """Cheap backdrop tree for beyond the hoarding."""
    rng = random.Random(seed)
    with g.at(pos):
        trunk_h = h * 0.5
        g.cyl((0, 0, 0), 0.32, trunk_h, P.bark, n=6, r2=0.16, caps=False)
        if style == 'pine':
            for i in range(3):
                t = i / 2
                rr = crown * (1 - t * 0.6)
                g.cyl((0, 0, h * 0.25 + h * 0.55 * t), rr, h * 0.4, P.leaf[i % 2], n=7, r2=0.05, caps=False)
        else:
            for i in range(4):
                a = rng.uniform(0, TAU)
                d = crown * rng.uniform(0.2, 0.55) if i else 0.0
                soft_blob(g, (cos(a) * d, sin(a) * d, trunk_h + crown * (rng.uniform(0.3, 0.9) if i else 1.0)), crown * rng.uniform(0.6, 0.85),
                          P.leaf[(i + seed) % 2], seed=seed * 13 + i, jitter=0.25, s=(1, 1, 0.85))


def poster(g, P, pos, rz, w=1.1, h=1.5, kind=0, z=0.9):
    """Faded circus poster pasted on a wall facing -Y (local)."""
    with g.at(pos, rz):
        bg = [P.canvas_mustard, P.canvas_cream, P.canvas_red][kind % 3]
        g.box((0, -0.01, z + h / 2), (w, 0.012, h), bg)
        fg = [P.red, P.indigo, P.cream][kind % 3]
        g.cyl((0, -0.02, z + h * 0.58), w * 0.3, 0.008, fg, n=16, rx=PI / 2)
        for i in range(3):
            g.box((0, -0.02, z + 0.15 + i * 0.1), (w * (0.8 - i * 0.15), 0.008, 0.05), fg)
        # a torn corner
        g.box((w / 2 - 0.12, -0.019, z + h - 0.1), (0.2, 0.004, 0.16), P.wood_dark, rz=0.0, ry=0.7)


# ================================================================ prop prefabs: lights, cloth

def bulb_string(p, P, a, b, sag=0.5, spacing=0.55, groups=2, light=None, dead=0.08, seed=0, red_every=0):
    """Festoon of bulbs between two prop-local points. light=(pos, colour, intensity, distance)."""
    rng = random.Random(seed)
    p.body.tube(catenary(a, b, sag, 16), 0.008, P.iron, n=3, caps=False)
    L = math.dist(a, b)
    n = max(2, int(L / spacing))
    parts = [p.geo(f'bulb{k}') for k in range(groups)]
    for i in range(1, n):
        c = cat_point(a, b, sag, i / n)
        p.body.cyl((c[0], c[1], c[2] - 0.06), 0.014, 0.06, P.iron, n=5)
        cc = (c[0], c[1], c[2] - 0.1)
        if rng.random() < dead:
            bulb(p.body, cc, P.bulb_dead, 0.04)
        else:
            bulb(parts[i % groups], cc, P.bulb_red if red_every and i % red_every == 0 else P.bulb, 0.042)
    if light:
        p.light(light[0], light[1], light[2], light[3], part='bulb0')
    p.params.setdefault('sound', 'buzz')


def bunting(p, P, a, b, sag=0.6, spacing=0.5, mats=None, fw=0.3, fh=0.4, shape='tri', amp=0.03):
    """Pennant bunting between two prop-local points; each flag is its own cloth part."""
    mats = mats or [P.canvas_red, P.canvas_cream, P.canvas_mustard, P.canvas_teal]
    p.body.tube(catenary(a, b, sag, 16), 0.009, P.rope, n=3, caps=False)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    L = math.dist(a, b)
    n = max(2, int(L / spacing))
    for i in range(1, n):
        c = cat_point(a, b, sag, i / n)
        pt = p.part(f'cloth{i - 1}', c, rz=ang)
        pt.geo.add(prim_pennant(fw, fh, 3, 6, shape), mats[i % len(mats)])
    p.params.setdefault('amp', amp)
    p.params.setdefault('sound', 'whoosh')


def valance(p, P, w, mats=None, depth=0.38, n=None, amp=0.025):
    """Scalloped awning valance along local X, hanging from z=0."""
    mats = mats or [P.canvas_red, P.canvas_cream]
    n = n or max(3, int(round(w / 0.42)))
    fw = w / n
    p.body.box((0, 0, 0.02), (w, 0.03, 0.05), P.mustard)
    for i in range(n):
        x = -w / 2 + fw * (i + 0.5)
        pt = p.part(f'cloth{i}', (x, -0.02, 0))
        pt.geo.add(prim_pennant(fw * 1.01, depth, 3, 6, 'scallop'), mats[i % len(mats)])
    p.params.setdefault('amp', amp)
    p.params.setdefault('sound', 'whoosh')


def lantern_post(p, P, h=3.0, light=True, intensity=1.3, dist=9.0, color='#ffb25a'):
    b = p.body
    b.lathe((0, 0, 0), [(0.2, 0), (0.2, 0.08), (0.14, 0.14), (0.1, 0.42), (0.065, 0.52)], P.iron, n=8)
    b.cyl((0, 0, 0.52), 0.05, h - 0.52, P.iron, n=8)
    b.torus((0, 0, 1.15), 0.065, 0.018, P.brass, n=8, m=4)
    b.torus((0, 0, h - 0.3), 0.065, 0.018, P.brass, n=8, m=4)
    # scroll brackets
    for k in range(2):
        a = k * PI
        b.tube([(0, 0, h - 0.55), (cos(a) * 0.2, sin(a) * 0.2, h - 0.35), (cos(a) * 0.12, sin(a) * 0.12, h - 0.1)], 0.015, P.iron, n=4)
    z0 = h
    b.lathe((0, 0, z0 - 0.12), [(0.03, 0), (0.15, 0.1), (0.16, 0.13)], P.iron, n=8)
    for k in range(4):
        a = k * TAU / 4 + TAU / 8
        b.box((0.15 * cos(a), 0.15 * sin(a), z0 + 0.2), (0.025, 0.025, 0.4), P.iron, rz=a)
    b.lathe((0, 0, z0 + 0.4), [(0.22, 0), (0.2, 0.04), (0.06, 0.2), (0.02, 0.3)], P.iron, n=8, smooth=False)
    b.sphere((0, 0, z0 + 0.72), 0.04, P.brass, n=8)
    b.cyl((0, 0, z0 + 0.01), 0.045, 0.06, P.brass, n=8)
    p.flame((0, 0, z0 + 0.07), size=1.7)
    if light:
        p.light((0, 0, z0 + 0.3), color, intensity, dist, part='flame0')
    b.collide((0, 0, h / 2), (0.3, 0.3, h))
    p.params.setdefault('sound', 'whoomp')


def hanging_lantern(p, P, drop=0.5, light=None, bracket=None):
    """Lantern hanging from a hook at the prop origin (swing)."""
    if bracket:
        p.body.tube([(0, 0, 0), (-bracket, 0, 0), (-bracket, 0, -0.25)], 0.02, P.iron, n=4)
        p.body.tube([(-bracket, 0, -0.25), (-bracket * 0.4, 0, -0.02)], 0.012, P.iron, n=4)
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.cyl((0, 0, -drop), 0.008, drop, P.iron, n=4)
    z = -drop
    g.torus((0, 0, z - 0.03), 0.035, 0.007, P.iron, n=8, m=4, rx=PI / 2)
    g.lathe((0, 0, z - 0.4), [(0.09, 0), (0.11, 0.02), (0.11, 0.05), (0.08, 0.07), (0.08, 0.28), (0.12, 0.3), (0.035, 0.4)],
            P.iron, n=6, smooth=False)
    for k in range(4):
        a = k * TAU / 4
        g.box((0.085 * cos(a), 0.085 * sin(a), z - 0.22), (0.015, 0.015, 0.22), P.iron, rz=a)
    p.flame((0, 0, z - 0.32), size=0.9, parent='pivot')
    if light:
        p.light((0, 0, z - 0.2), light[0], light[1], light[2], part='pivot')
    p.params.setdefault('amp', 0.05)
    p.params.setdefault('period', 2.2)
    p.params.setdefault('sound', 'creak')


def balloons(p, P, n=6, seed=0, h=2.5, post=True, post_h=1.1, post_mat=None, amp=0.06):
    """Bunch of balloons tied to a short striped post."""
    rng = random.Random(seed)
    b = p.body
    knot = (0, 0, post_h)
    if post:
        b.cyl((0, 0, 0), 0.16, 0.08, P.iron, n=8)
        b.cyl((0, 0, 0.08), 0.03, post_h - 0.05, post_mat or P.cream, n=6)
        b.sphere((0, 0, post_h + 0.02), 0.045, P.red, n=8)
        b.collide((0, 0, post_h / 2), (0.2, 0.2, post_h))
    pv = p.part('pivot')
    g = pv.geo
    for i in range(n):
        a = rng.uniform(0, TAU) + i * 1.3
        d = rng.uniform(0.12, 0.42)
        z = h + rng.uniform(-0.25, 0.45)
        c = (cos(a) * d, sin(a) * d, z)
        mat = P.balloons[(i + seed) % len(P.balloons)]
        g.sphere(c, 1.0, mat, n=10, s=(0.2, 0.2, 0.25))
        g.lathe((c[0], c[1], z - 0.29), [(0.005, 0), (0.025, 0.035), (0.03, 0.045)], mat, n=5)
        mid = (c[0] * 0.4 + rng.uniform(-0.05, 0.05), c[1] * 0.4, (z - 0.29 + knot[2]) / 2)
        g.tube([(c[0], c[1], z - 0.29), mid, knot], 0.004, P.cream, n=3, caps=False)
    p.params.setdefault('amp', amp)
    p.params.setdefault('sound', 'squeak')


# ================================================================ prop prefabs: carousel

def horse(p, P, coat, saddle, mane, pole_h=3.95, ride_h=1.2):
    b = p.body
    b.cyl((0, 0, 0), 0.032, pole_h, P.brass, n=8)
    for z in (0.02, pole_h - 0.14):
        b.lathe((0, 0, z), [(0.035, 0), (0.07, 0.04), (0.07, 0.08), (0.035, 0.12)], P.brass, n=8)
    b.collide((0, 0, 1.0), (0.5, 0.5, 2.0))
    pv = p.part('pivot', (0, 0, ride_h))
    horse_geo(pv.geo, P, coat, saddle, mane)
    p.params.setdefault('amp', 0.09)
    p.params.setdefault('sound', 'squeak')


def horse_geo(g, P, coat, saddle, mane):
    """Galloping carousel horse centred on its pole, facing +X."""
    g.sphere((0.0, 0, 0), 1.0, coat, n=12, s=(0.48, 0.19, 0.22))
    g.sphere((0.3, 0, 0.04), 1.0, coat, n=10, s=(0.22, 0.175, 0.21))
    g.sphere((-0.3, 0, 0.03), 1.0, coat, n=10, s=(0.24, 0.185, 0.21))
    g.tube([(0.34, 0, 0.08), (0.46, 0, 0.3), (0.54, 0, 0.47)], 0.1, coat, n=8)
    with g.at((0.55, 0, 0.5), ry=1.05):
        g.box((0.14, 0, 0), (0.32, 0.12, 0.15), coat, bevel=0.045)
        g.box((0.3, 0, -0.012), (0.1, 0.11, 0.12), coat, bevel=0.035)
        for sy in (-1, 1):
            g.sphere((0.06, sy * 0.062, 0.035), 0.018, P.black, n=6)
            g.box((-0.04, sy * 0.04, 0.1), (0.05, 0.025, 0.1), coat)
        g.torus((0.2, 0, 0), 0.075, 0.012, P.mustard, n=10, m=4, ry=PI / 2)
    g.tube([(0.28, 0, 0.2), (0.4, 0, 0.42), (0.49, 0, 0.6), (0.6, 0, 0.64)], 0.045, mane, n=6)
    g.lathe((0.56, 0, 0.62), [(0.03, 0), (0.05, 0.06), (0.03, 0.16), (0.005, 0.22)], saddle, n=6)
    for sy in (-1, 1):
        y = sy * 0.08
        g.tube([(0.3, y, -0.06), (0.47, y, -0.2), (0.4 + 0.05 * sy, y, -0.42)], 0.04, coat, n=6)
        g.sphere((0.4 + 0.05 * sy, y, -0.44), 0.045, mane, n=6)
        g.tube([(-0.32, y, -0.08), (-0.43, y, -0.32), (-0.56, y, -0.52)], 0.046, coat, n=6)
        g.sphere((-0.57, y, -0.54), 0.048, mane, n=6)
        g.box((-0.03, sy * 0.195, 0.08), (0.36, 0.015, 0.24), saddle)
        g.box((-0.03, sy * 0.2, -0.04), (0.38, 0.02, 0.035), P.mustard)
        g.tube([(0.78, sy * 0.06, 0.32), (0.42, sy * 0.13, 0.25), (0.08, sy * 0.15, 0.22)], 0.01, P.mustard, n=3)
        g.box((-0.05, sy * 0.22, -0.08), (0.02, 0.012, 0.22), P.wood_dark)
        g.torus((-0.05, sy * 0.22, -0.2), 0.04, 0.008, P.brass, n=8, m=3, rx=PI / 2)
    g.tube([(-0.5, 0, 0.08), (-0.64, 0, 0.0), (-0.7, 0, -0.32)], 0.045, mane, n=6)
    g.box((-0.06, 0, 0.215), (0.3, 0.26, 0.05), saddle, bevel=0.02)
    g.box((-0.2, 0, 0.25), (0.05, 0.22, 0.09), saddle, bevel=0.015)
    g.box((0.07, 0, 0.245), (0.04, 0.12, 0.06), P.mustard)


def mirror_drum(p, P, r=1.15, z0=0.4, z1=3.2, n=12):
    pv = p.part('pivot')
    g = pv.geo
    half = PI / n
    chord = 2 * r * sin(half)
    for k in range(n):
        am = k * TAU / n + half
        rr = r * cos(half)
        with g.at((rr * cos(am), rr * sin(am), 0), rz=am):
            g.box((0, 0, (z0 + z1) / 2), (0.08, chord + 0.01, z1 - z0), P.teal if k % 2 else P.indigo)
            g.box((0.045, 0, (z0 + z1) / 2 + 0.05), (0.02, chord * 0.6, (z1 - z0) * 0.56), P.mirror)
            for zz in ((z0 + z1) / 2 + 0.05 - (z1 - z0) * 0.29, (z0 + z1) / 2 + 0.05 + (z1 - z0) * 0.29):
                g.box((0.05, 0, zz), (0.03, chord * 0.68, 0.06), P.mustard, bevel=0.01)
            for sy in (-1, 1):
                g.box((0.05, sy * chord * 0.32, (z0 + z1) / 2 + 0.05), (0.03, 0.06, (z1 - z0) * 0.62), P.mustard, bevel=0.01)
            g.sphere((0.07, 0, z1 - 0.18), 0.06, P.red, n=8)
            g.sphere((0.07, 0, z0 + 0.16), 0.05, P.mustard, n=8)
    for z in (z0, z1):
        g.torus((0, 0, z), r + 0.02, 0.05, P.mustard, n=n * 2, m=5)
    p.params.setdefault('axis', 'y')
    p.params.setdefault('speed', 0.22)
    p.params.setdefault('wobble', 0.0)
    p.params.setdefault('sound', 'whirr')


def ring_lights(p, P, r, z, n, a0, a1, rows=((0.0, 'bulb'),), groups=2, light=None, dead=(), red_every=0):
    """Arc of bulbs around the prop origin (e.g. the carousel rounding board)."""
    parts = [p.geo(f'bulb{k}') for k in range(groups)]
    idx = 0
    for dz, _ in rows:
        for i in range(n):
            a = a0 + (a1 - a0) * (i + 0.5) / n
            c = (r * cos(a), r * sin(a), z + dz)
            if idx in dead:
                bulb(p.body, c, P.bulb_dead, 0.045)
            else:
                bulb(parts[i % groups], c, P.bulb_red if red_every and i % red_every == 0 else P.bulb, 0.05)
            idx += 1
    if light:
        p.light(light[0], light[1], light[2], light[3], part='bulb0')
    p.params.setdefault('sound', 'buzz')


def figurine(g, P, dress, s=1.0, arms_up=True):
    g.lathe((0, 0, 0), [(0.0, 0), (0.06 * s, 0.005), (0.07 * s, 0.03 * s), (0.03 * s, 0.13 * s), (0.02 * s, 0.14 * s)], P.mustard, n=8)
    g.lathe((0, 0, 0.14 * s), [(0.08 * s, 0), (0.03 * s, 0.14 * s), (0.025 * s, 0.2 * s)], dress, n=10)
    g.sphere((0, 0, 0.38 * s), 0.035 * s, P.cream, n=8)
    g.sphere((0, 0, 0.42 * s), 0.025 * s, dress, n=6)
    for sx in (-1, 1):
        if arms_up:
            g.tube([(sx * 0.02 * s, 0, 0.32 * s), (sx * 0.06 * s, 0, 0.4 * s), (sx * 0.05 * s, 0, 0.47 * s)], 0.008 * s, P.cream, n=3)
        else:
            g.tube([(sx * 0.02 * s, 0, 0.32 * s), (sx * 0.07 * s, -0.02 * s, 0.26 * s)], 0.008 * s, P.cream, n=3)


def band_organ(p, P):
    """Carousel band organ facing -Y (music: organ). Two little conductors spin when it plays."""
    b = p.body
    b.box((0, 0.05, 0.08), (1.6, 0.7, 0.16), P.wood_dark, bevel=0.02)
    b.box((0, 0.1, 0.85), (1.5, 0.55, 1.4), P.boards_teal, bevel=0.02)
    b.box((0, -0.19, 0.85), (1.56, 0.04, 1.46), P.mustard, bevel=0.01)
    b.box((0, -0.215, 0.92), (1.3, 0.02, 1.0), P.indigo)
    for i in range(11):
        x = -0.55 + i * 0.11
        hh = 0.42 + 0.34 * (1 - abs(i - 5) / 5)
        b.cyl((x, -0.27, 0.48), 0.035, hh, P.brass, n=8)
        b.box((x, -0.305, 0.58), (0.03, 0.01, 0.04), P.black)
        b.lathe((x, -0.27, 0.48 + hh), [(0.035, 0), (0.045, 0.02), (0.01, 0.05)], P.brass, n=8)
    for sx in (-1, 1):
        b.cyl((sx * 0.5, -0.22, 0.38), 0.17, 0.12, P.red, n=14, rx=PI / 2)
        b.cyl((sx * 0.5, -0.345, 0.38), 0.15, 0.01, P.cream, n=14, rx=PI / 2)
        b.box((sx * 0.62, -0.25, 1.62), (0.18, 0.08, 0.22), P.mustard, bevel=0.02)
    b.add(gh.prim_lathe([(0.8, 0), (0.75, 0.04), (0.001, 0.06)], 12, False, False, False, arc=PI), P.mustard,
          gh.X((0, -0.13, 1.55), rx=PI / 2))
    b.add(gh.prim_lathe([(0.55, 0), (0.5, 0.03), (0.001, 0.05)], 12, False, False, False, arc=PI), P.red,
          gh.X((0, -0.17, 1.55), rx=PI / 2))
    for k in range(7):
        a = PI * (k + 0.5) / 7
        bulb(b, (cos(a) * 0.68, -0.2, 1.57 + sin(a) * 0.32), P.bulb, 0.035)
    for k, sx in enumerate((-0.62, 0.62)):
        d = p.geo(f'dancer{k}', (sx, -0.25, 1.73))
        figurine(d, P, P.red if k else P.teal, s=0.9)
    b.collide((0, 0.05, 0.85), (1.6, 0.7, 1.7))
    p.params.setdefault('instrument', 'organ')


# ================================================================ prop prefabs: ferris wheel

def gondola(p, P, shell, roof, drop=1.95, w=1.45, d=1.05):
    pv = p.part('pivot')
    g = pv.geo
    for sy in (-1, 1):
        g.box((0, sy * 0.5, -0.24), (0.07, 0.035, 0.48), P.iron)
        g.cyl((0, sy * 0.55, 0), 0.06, 0.05, P.iron, n=8, rx=PI / 2)
    g.box((0, 0, -0.48), (0.08, 1.04, 0.06), P.iron)
    g.cyl((0, 0, -0.78), 0.03, 0.3, P.iron, n=6)
    zc = -1.05
    wedge_cone(g, (0, 0, zc), 0.86, 0.0, 0.05, 0.27, roof, n=8, rows=2)
    g.sphere((0, 0, zc + 0.3), 0.05, P.mustard, n=8)
    for k in range(8):
        a = k * TAU / 8
        bulb(g, (cos(a) * 0.82, sin(a) * 0.82, zc - 0.03), P.bulb if k % 3 else P.bulb_dead, 0.03)
    zb = -drop
    th = 0.62
    g.box((0, 0, zb + 0.03), (w, d, 0.06), P.wood_dark)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.03), 0, zb + th / 2), (0.06, d, th), shell)
        g.box((sx * (w / 2 - 0.25), 0, zb + 0.3), (0.38, d - 0.12, 0.08), P.red, bevel=0.02)
        g.box((sx * (w / 2 - 0.09), 0, zb + 0.52), (0.08, d - 0.12, 0.4), P.red, bevel=0.02)
    for sy in (-1, 1):
        g.box((0, sy * (d / 2 - 0.03), zb + th / 2), (w, 0.06, th), shell)
        g.box((0, sy * (d / 2 - 0.0), zb + th * 0.5), (w * 0.5, 0.02, th * 0.4), P.mustard)
    g.box((0, 0, zb + th + 0.02), (w + 0.04, d + 0.04, 0.04), P.mustard)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.tube([(sx * (w / 2 - 0.05), sy * (d / 2 - 0.05), zb + th), (sx * 0.62, sy * 0.45, zc - 0.02)], 0.015, P.iron, n=4)
    p.params.setdefault('axes', 'z')
    p.params.setdefault('amp', 0.035)
    p.params.setdefault('period', 3.4)
    p.params.setdefault('sound', 'creak')


def wheel_hub(p, P, r0=0.65, r1=2.1, rays=16):
    """Sunburst medallion on the Ferris wheel hub, facing -Y (spin about its face normal)."""
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0.1, 0), r0, 0.14, P.mustard, n=24, rx=PI / 2)
    g.cyl((0, -0.04, 0), r0 * 0.62, 0.06, P.red, n=20, rx=PI / 2)
    g.cyl((0, -0.1, 0), r0 * 0.3, 0.05, P.cream, n=16, rx=PI / 2)
    for k in range(rays):
        a = k * TAU / rays
        ln = r1 if k % 2 == 0 else r1 * 0.72
        hw = 0.16 if k % 2 == 0 else 0.12
        pts = []
        for rr, tt in ((r0 * 0.9, -hw), (ln, 0.0), (r0 * 0.9, hw)):
            pts.append((rr * cos(a) - tt * sin(a), rr * sin(a) + tt * cos(a)))
        g.prism((0, 0.0, 0), pts, 0.05, P.red if k % 2 == 0 else P.cream, rx=PI / 2)
        bulb(g, (ln * cos(a), -0.08, ln * sin(a)), P.bulb, 0.05)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('speed', 0.18)
    p.params.setdefault('wobble', 0.0)
    p.params.setdefault('sound', 'whirr')


def wheel_lights(p, P, R, half, n, spokes=False, light=None, seed=0):
    """Bulbs on the Ferris wheel (prop origin = hub centre). Rim or spoke runs, front and back."""
    rng = random.Random(seed)
    parts = [p.geo('bulb0'), p.geo('bulb1')]
    for side, y in enumerate((-half - 0.12, half + 0.12)):
        if spokes:
            for k in range(16):
                a = k * TAU / 16 + TAU / 32
                for j in range(1, n + 1):
                    rr = 0.9 + (R * 0.7 - 0.9) * j / n
                    c = (rr * cos(a), y, rr * sin(a))
                    if rng.random() < 0.06:
                        bulb(p.body, c, P.bulb_dead, 0.05)
                    else:
                        bulb(parts[side], c, P.bulb_red if j == n else P.bulb, 0.055)
        else:
            for i in range(n):
                a = i * TAU / n
                c = ((R + 0.16) * cos(a), y, (R + 0.16) * sin(a))
                if rng.random() < 0.05:
                    bulb(p.body, c, P.bulb_dead, 0.05)
                else:
                    bulb(parts[side], c, P.bulb_red if i % 4 == 0 else P.bulb, 0.06)
    if light:
        p.light(light[0], light[1], light[2], light[3], part='bulb0')
    p.params.setdefault('sound', 'buzz')


def lever(p, P):
    """Operator's brake lever in a floor quadrant (hinge about local X)."""
    b = p.body
    b.box((0, 0, 0.05), (0.3, 0.5, 0.1), P.iron)
    for k in range(5):
        a = -0.6 + k * 0.3
        b.box((0.08, sin(a) * 0.22, 0.1 + cos(a) * 0.22), (0.03, 0.05, 0.03), P.mustard, rx=-a)
    pv = p.part('pivot', (0, 0, 0.1), rx=0.35)
    pv.geo.cyl((0, 0, 0), 0.025, 0.95, P.iron, n=6)
    pv.geo.cyl((0, 0, 0.9), 0.04, 0.16, P.red, n=8)
    pv.geo.sphere((0, 0, 1.08), 0.05, P.red, n=8)
    p.params.setdefault('axis', 'x')
    p.params.setdefault('dir', -1)
    p.params.setdefault('open', 0.7)
    p.params.setdefault('sound', 'clatter')


# ================================================================ prop prefabs: big top

def trapeze(p, P, rope=3.0, w=0.9):
    pv = p.part('pivot', (0, 0, rope))
    g = pv.geo
    for sx in (-1, 1):
        g.cyl((sx * w / 2, 0, -rope), 0.012, rope, P.rope, n=4)
        g.torus((sx * w / 2, 0, -0.04), 0.04, 0.01, P.iron, n=8, m=3, rx=PI / 2)
    g.cyl((-w / 2 - 0.06, 0, -rope), 0.026, w + 0.12, P.cream, n=8, ry=PI / 2)
    for sx in (-0.3, -0.1, 0.1, 0.3):
        g.cyl((sx - 0.04, 0, -rope), 0.03, 0.08, P.red, n=8, ry=PI / 2)
    p.params.setdefault('axes', 'x')
    p.params.setdefault('amp', 0.06)
    p.params.setdefault('period', 3.6)
    p.params.setdefault('sound', 'creak')


def spotlight(p, P, drop=0.4, light=('#ffe2b0', 2.4, 13.0), tilt=0.5):
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0, -drop), 0.012, drop, P.iron, n=4)
    g.torus((0, 0, -drop - 0.05), 0.2, 0.02, P.iron, n=12, m=4, ry=PI / 2)
    with g.at((0, 0, -drop - 0.05), rx=tilt):
        g.lathe((0, 0, -0.45), [(0.17, 0), (0.2, 0.05), (0.2, 0.32), (0.14, 0.45), (0.07, 0.52)], P.black, n=12)
        g.cyl((0, 0, -0.46), 0.16, 0.02, P.lamp, n=12)
        for z in (-0.38, -0.25):
            g.torus((0, 0, z), 0.205, 0.012, P.brass, n=12, m=3)
    p.light((0, -0.25, -drop - 0.6), light[0], light[1], light[2], part='pivot')
    p.params.setdefault('amp', 0.02)
    p.params.setdefault('period', 4.0)
    p.params.setdefault('sound', 'creak')


def gong(p, P, r=0.55):
    b = p.body
    for sx in (-1, 1):
        b.box((sx * 0.82, 0, 1.0), (0.1, 0.1, 2.0), P.wood_dark, bevel=0.01)
        b.box((sx * 0.82, 0, 0.05), (0.14, 0.7, 0.1), P.wood_dark, bevel=0.01)
        b.sphere((sx * 0.82, 0, 2.06), 0.07, P.mustard, n=8)
    b.cyl((-0.85, 0, 1.92), 0.045, 1.7, P.red, n=8, ry=PI / 2)
    pv = p.part('pivot', (0, 0, 1.92))
    g = pv.geo
    for sx in (-0.22, 0.22):
        g.tube([(sx * 0.6, 0, 0), (sx, 0, -0.38)], 0.008, P.rope, n=3)
    zc = -0.38 - r
    g.cyl((0, 0.025, zc), r, 0.05, P.brass, n=28, rx=PI / 2)
    g.torus((0, 0, zc), r, 0.03, P.brass, n=28, m=5, rx=PI / 2)
    g.cyl((0, -0.025, zc), r * 0.32, 0.015, P.mustard, n=20, rx=PI / 2)
    g.torus((0, -0.03, zc), r * 0.66, 0.008, P.mustard, n=24, m=3, rx=PI / 2)
    b.tube([(1.0, -0.2, 0.0), (1.05, -0.15, 0.85)], 0.018, P.wood, n=5)
    b.sphere((1.05, -0.15, 0.9), 0.07, P.red, n=8)
    b.collide((0, 0, 1.0), (1.8, 0.6, 2.0))
    p.params.setdefault('axis', 'x')
    p.params.setdefault('tone', 110)
    p.params.setdefault('sound', 'gong')


def ring_pedestal(p, P, r0=0.48, r1=0.36, h=0.7):
    pv = p.part('pivot')
    g = pv.geo
    wedge_drum(g, (0, 0, 0), r0, r1, h, [P.red, P.cream], n=12)
    g.cyl((0, 0, h), r1 + 0.04, 0.06, P.mustard, n=16)
    g.torus((0, 0, 0.04), r0, 0.03, P.mustard, n=16, m=4)
    g.torus((0, 0, h - 0.02), r1 + 0.01, 0.025, P.mustard, n=16, m=4)
    for k in range(6):
        a = k * TAU / 6
        g.sphere(((r0 + r1) / 2 * cos(a) * 1.02, (r0 + r1) / 2 * sin(a) * 1.02, h / 2), 0.04, P.mustard, n=6)
    p.body.collide((0, 0, h / 2), (2 * r0, 2 * r0, h))
    p.params.setdefault('axis', 'y')
    p.params.setdefault('speed', 0.0)
    p.params.setdefault('wobble', 0.04)
    p.params.setdefault('sound', 'whirr')


def fire_hoop(p, P, r=0.62, h=1.55, flames=8):
    b = p.body
    b.cyl((0, 0, 0), 0.3, 0.06, P.iron, n=10)
    b.cyl((0, 0, 0.06), 0.03, h - r - 0.02, P.iron, n=6)
    b.torus((0, 0, h), r, 0.03, P.iron, n=24, m=5, rx=PI / 2)
    for k in range(flames):
        a = k * TAU / flames + TAU / (2 * flames)
        c = (r * cos(a), 0, h + r * sin(a))
        b.cyl((c[0], 0, c[2]), 0.025, 0.06, P.black, n=5)
        p.flame((c[0], 0, c[2] + 0.06), size=1.1)
    b.collide((0, 0, 0.5), (0.4, 0.4, 1.0))
    p.params.setdefault('sound', 'whoomp')


def cannon(p, P):
    b = p.body
    for sy in (-1, 1):
        spoked_wheel(b, P, (0.1, sy * 0.62, 0.55), 0.55, spokes=12, rim=P.red, spoke=P.mustard)
        b.box((0.1, sy * 0.4, 0.55), (1.4, 0.1, 0.32), P.red, bevel=0.02)
    b.box((-0.9, 0, 0.12), (0.9, 0.5, 0.12), P.red, bevel=0.02)
    b.collide((0, 0, 0.7), (2.2, 1.4, 1.4))
    pv = p.part('pivot', (0.1, 0, 0.75), ry=-0.38)
    g = pv.geo
    g.lathe((-0.9, 0, 0), [(0.22, 0), (0.3, 0.1), (0.3, 0.25), (0.26, 0.3), (0.22, 1.8), (0.27, 1.85), (0.27, 2.0), (0.2, 2.02)],
            P.indigo, n=14, ry=PI / 2)
    g.cyl((1.08, 0, 0), 0.17, 0.03, P.black, n=12, ry=PI / 2)
    for x in (-0.55, 0.2, 0.95):
        g.torus((x, 0, 0), 0.27, 0.025, P.mustard, n=14, m=4, ry=PI / 2)
    for k in range(5):
        a = k * TAU / 5
        g.sphere((-0.2 + 0.25 * k, 0.24 * cos(a), 0.24 * sin(a)), 0.03, P.mustard, n=6)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('period', 2.0)
    p.params.setdefault('sound', 'creak')


def big_ball(p, P, r=0.55):
    pv = p.part('pivot')
    ball_wedges(pv.geo, (0, 0, r), r, [P.red, P.cream, P.teal, P.cream], n=8)
    p.body.collide((0, 0, r), (2 * r * 0.9, 2 * r * 0.9, 2 * r))
    p.params.setdefault('sound', 'thud')


def show_clock(p, P, title='SHOW'):
    """'Next show' sandwich board with a clock face (clock archetype)."""
    b = p.body
    for sx in (-0.6, 0.6):
        b.box((sx, 0, 1.0), (0.08, 0.08, 2.0), P.wood_dark)
        b.box((sx, 0, 0.04), (0.1, 0.5, 0.08), P.wood_dark)
    b.box((0, 0, 1.45), (1.3, 0.06, 1.0), P.boards_red, bevel=0.01)
    b.box((0, -0.035, 1.45), (1.2, 0.01, 0.92), P.indigo)
    for zz in (0.97, 1.93):
        b.box((0, -0.04, zz), (1.32, 0.03, 0.05), P.mustard)
    b.add(gh.prim_lathe([(0.66, 0), (0.6, 0.03), (0.001, 0.05)], 10, False, False, False, arc=PI), P.mustard, gh.X((0, 0.02, 1.95), rx=PI / 2))
    painted_letters(b, title, (0, -0.045, 1.71), 0.026, P.cream)
    b.cyl((0, -0.04, 1.36), 0.3, 0.03, P.mustard, n=24, rx=PI / 2)
    b.cyl((0, -0.07, 1.36), 0.26, 0.01, P.cream, n=24, rx=PI / 2)
    for i in range(12):
        a = i * TAU / 12
        b.box((sin(a) * 0.21, -0.078, 1.36 + cos(a) * 0.21), (0.016, 0.006, 0.045), P.black, ry=-a)
    hr = p.geo('hour', (0, -0.085, 1.36))
    hr.box((0, 0, 0.06), (0.025, 0.008, 0.13), P.black)
    mn = p.geo('minute', (0, -0.09, 1.36))
    mn.box((0, 0, 0.09), (0.016, 0.008, 0.2), P.black)
    b.sphere((0, -0.095, 1.36), 0.018, P.brass, n=6)
    b.collide((0, 0, 1.0), (1.3, 0.4, 2.0))
    p.params.setdefault('axis', 'z')
    p.params.setdefault('sound', 'chime')


# ================================================================ prop prefabs: midway

def duck(g, P, x, mat):
    g.sphere((x, 0, 0.07), 1.0, mat, n=8, s=(0.13, 0.08, 0.075))
    g.sphere((x + 0.09, 0, 0.16), 0.055, mat, n=8)
    g.prism((x + 0.13, 0, 0.15), [(0, -0.02), (0.07, 0.0), (0, 0.02)], 0.02, P.red)
    for sy in (-1, 1):
        bulb(g, (x + 0.115, sy * 0.04, 0.18), P.black, 0.012)
    g.box((x - 0.12, 0, 0.12), (0.06, 0.05, 0.06), mat, ry=-0.6)
    g.cyl((x, -0.081, 0.07), 0.04, 0.005, P.cream, n=10, rx=PI / 2)
    g.cyl((x, -0.087, 0.07), 0.02, 0.005, P.red, n=10, rx=PI / 2)


def duck_row(p, P, length=4.2, n=8, amp=0.025):
    b = p.body
    b.box((0, 0, 0.12), (length + 0.2, 0.36, 0.24), P.boards_teal, bevel=0.01)
    b.box((0, 0, 0.235), (length, 0.26, 0.01), P.puddle)
    b.box((0, -0.19, 0.2), (length + 0.2, 0.03, 0.08), P.mustard)
    pv = p.part('pivot', (0, 0, 0.23))
    for i in range(n):
        duck(pv.geo, P, -length / 2 + (i + 0.5) * length / n, P.mustard if i % 3 else P.cream)
    p.params.setdefault('amp', amp)
    p.params.setdefault('sound', 'squeak')


def target_spinner(p, P, r=0.32, post=0.9):
    b = p.body
    b.box((0, 0.05, post / 2), (0.06, 0.06, post), P.iron)
    b.cyl((0, 0.02, post), 0.06, 0.06, P.iron, n=8, rx=PI / 2)
    pv = p.part('pivot', (0, -0.04, post))
    g = pv.geo
    for i, (rr, mat) in enumerate(((r, P.red), (r * 0.75, P.cream), (r * 0.5, P.red), (r * 0.25, P.cream))):
        g.cyl((0, 0.02 - i * 0.006, 0), rr, 0.015, mat, n=20, rx=PI / 2)
    for k in range(4):
        a = k * TAU / 4
        g.prism((0, 0.0, 0), [(r * cos(a), r * sin(a)), (r * 1.45 * cos(a + 0.2), r * 1.45 * sin(a + 0.2)),
                             (r * cos(a + 0.45), r * sin(a + 0.45))], 0.012, P.mustard, rx=PI / 2)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('speed', 0.0)
    p.params.setdefault('wobble', 0.08)
    p.params.setdefault('sound', 'whirr')


def bear(g, P, s=1.0, fur=None, belly=None, bow=None, lo=False):
    fur = fur or P.fur
    belly = belly or P.cream
    n1, n2 = (8, 6) if lo else (12, 8)
    g.sphere((0, 0, 0.32 * s), 1.0, fur, n=n1, s=(0.28 * s, 0.24 * s, 0.31 * s))
    g.sphere((0, -0.02 * s, 0.78 * s), 0.22 * s, fur, n=n1)
    if not lo:
        g.sphere((0, -0.17 * s, 0.3 * s), 1.0, belly, n=n2, s=(0.17 * s, 0.08 * s, 0.2 * s))
    for sx in (-1, 1):
        g.sphere((sx * 0.15 * s, 0, 0.96 * s), 0.07 * s, fur, n=6)
        bulb(g, (sx * 0.07 * s, -0.19 * s, 0.84 * s), P.black, round(0.022 * s, 3))
        g.sphere((sx * 0.26 * s, -0.06 * s, 0.42 * s), 1.0, fur, n=6, s=(0.08 * s, 0.08 * s, 0.17 * s), ry=sx * 0.5)
        g.sphere((sx * 0.14 * s, -0.2 * s, 0.1 * s), 1.0, fur, n=6, s=(0.1 * s, 0.16 * s, 0.1 * s))
    g.sphere((0, -0.19 * s, 0.74 * s), 1.0, belly, n=6, s=(0.08 * s, 0.07 * s, 0.065 * s))
    bulb(g, (0, -0.26 * s, 0.77 * s), P.black, round(0.025 * s, 3))
    if bow:
        for sx in (-1, 1):
            g.prism((0, -0.2 * s, 0.6 * s), [(0, 0), (sx * 0.1 * s, 0.04 * s), (sx * 0.1 * s, -0.04 * s)], 0.05 * s, bow, rx=0)
        g.sphere((0, -0.22 * s, 0.62 * s), 0.025 * s, bow, n=6)


def plush(p, P, kind='bear', s=1.0, fur=None, bow=None):
    pv = p.part('pivot')
    if kind == 'bear':
        bear(pv.geo, P, s, fur or P.fur, P.cream, bow or P.red)
    else:  # long-eared rabbit
        g = pv.geo
        f = fur or P.pink
        g.sphere((0, 0, 0.3 * s), 1.0, f, n=12, s=(0.24 * s, 0.22 * s, 0.3 * s))
        g.sphere((0, -0.02 * s, 0.72 * s), 0.19 * s, f, n=12)
        for sx in (-1, 1):
            g.sphere((sx * 0.08 * s, 0.02 * s, 1.05 * s), 1.0, f, n=8, s=(0.06 * s, 0.035 * s, 0.24 * s), ry=sx * 0.25)
            g.sphere((sx * 0.06 * s, -0.17 * s, 0.76 * s), 0.02 * s, P.black, n=6)
            g.sphere((sx * 0.13 * s, -0.2 * s, 0.08 * s), 1.0, f, n=8, s=(0.09 * s, 0.17 * s, 0.08 * s))
        g.sphere((0, -0.19 * s, 0.68 * s), 0.025 * s, P.red, n=6)
        g.box((0, -0.18 * s, 0.5 * s), (0.2 * s, 0.03 * s, 0.05 * s), bow or P.teal)
    p.body.collide((0, 0, 0.45 * s), (0.6 * s, 0.6 * s, 0.9 * s))
    p.params.setdefault('sound', 'thud')


def hanging_plush(p, P, drop=0.35, s=0.55, fur=None):
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0, -drop), 0.006, drop, P.rope, n=3)
    with g.at((0, 0, -drop - 1.02 * s)):
        bear(g, P, s, fur or P.pink, P.cream, P.teal)
    p.params.setdefault('axes', 'xz')
    p.params.setdefault('amp', 0.04)
    p.params.setdefault('period', 2.4)
    p.params.setdefault('sound', 'rustle')


def milk_bottle(g, P, c, s=1.0):
    g.lathe(c, [(0.05 * s, 0), (0.055 * s, 0.01), (0.055 * s, 0.13 * s), (0.03 * s, 0.19 * s), (0.028 * s, 0.24 * s),
                (0.032 * s, 0.25 * s)], P.cream, n=8)
    g.cyl((c[0], c[1], c[2] + 0.1 * s), 0.0565 * s, 0.03 * s, P.red, n=8)


def bottle_pyramid(p, P):
    b = p.body
    b.cyl((0, 0, 0), 0.05, 0.95, P.wood_dark, n=6)
    b.cyl((0, 0, 0), 0.25, 0.04, P.wood_dark, n=8)
    b.box((0, 0, 0.97), (0.42, 0.3, 0.04), P.red, bevel=0.01)
    b.collide((0, 0, 0.5), (0.45, 0.45, 1.0))
    pv = p.part('pivot', (0, 0, 0.99))
    g = pv.geo
    for row, count in enumerate((3, 2, 1)):
        for i in range(count):
            x = (i - (count - 1) / 2) * 0.12
            milk_bottle(g, P, (x, 0, row * 0.255))
            if row < 2 and i < count - 1:
                pass
        if row < 2:
            g.box((0, 0, row * 0.255 + 0.252), (0.12 * count, 0.13, 0.008), P.wood)
    p.params.setdefault('sound', 'clatter')


def mallet(p, P):
    pv = p.part('pivot', (0, 0, 0), ry=0.32)
    g = pv.geo
    g.cyl((0, 0, 0.0), 0.025, 1.15, P.wood, n=6)
    g.cyl((-0.22, 0, 1.15), 0.11, 0.44, P.red, n=12, ry=PI / 2)
    for x in (-0.2, 0.2):
        g.torus((x, 0, 1.15), 0.11, 0.015, P.iron, n=12, m=3, ry=PI / 2)
    p.params.setdefault('sound', 'thud')


def striker_bell(p, P, r=0.24):
    pv = p.part('pivot')
    g = pv.geo
    g.box((0, 0, 0), (0.08, 0.5, 0.08), P.iron)
    g.lathe((0, 0, -r * 2.0), [(r, 0), (r * 0.96, r * 0.15), (r * 0.62, r * 0.95), (r * 0.52, r * 1.7), (r * 0.25, r * 1.9), (0.01, r * 1.96)],
            P.brass, n=18)
    g.cyl((0, 0, -0.06), 0.03, 0.08, P.iron, n=6)
    g.sphere((0, 0, -r * 1.85), r * 0.18, P.iron, n=8)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('tone', 620)
    p.params.setdefault('sound', 'bell')


def weight_scale(p, P):
    """'Guess your weight' penny scale with a big dial (clock archetype)."""
    b = p.body
    b.box((0, 0, 0.09), (0.8, 0.9, 0.18), P.iron, bevel=0.02)
    b.box((0, -0.05, 0.19), (0.6, 0.6, 0.02), P.planks)
    b.lathe((0, 0.3, 0.18), [(0.16, 0), (0.12, 0.1), (0.09, 0.3), (0.08, 1.2), (0.12, 1.3), (0.1, 1.36)], P.red, n=10)
    for z in (0.3, 1.45):
        b.torus((0, 0.3, z), 0.1, 0.02, P.mustard, n=10, m=4)
    b.cyl((0, 0.38, 1.85), 0.42, 0.16, P.red, n=24, rx=PI / 2)
    b.torus((0, 0.22, 1.85), 0.41, 0.035, P.mustard, n=24, m=5, rx=PI / 2)
    b.cyl((0, 0.21, 1.85), 0.37, 0.01, P.cream, n=24, rx=PI / 2)
    for i in range(20):
        a = i * TAU / 20
        b.box((sin(a) * 0.3, 0.198, 1.85 + cos(a) * 0.3), (0.012, 0.006, 0.05 if i % 5 == 0 else 0.03), P.black, ry=-a)
    b.sphere((0, 0.3, 2.35), 0.08, P.mustard, n=8)
    hr = p.geo('hour', (0, 0.19, 1.85))
    hr.box((0, 0, 0.12), (0.02, 0.008, 0.26), P.red)
    mn = p.geo('minute', (0, 0.185, 1.85))
    mn.box((0, 0, 0.05), (0.03, 0.006, 0.12), P.black)
    b.sphere((0, 0.18, 1.85), 0.025, P.brass, n=6)
    b.collide((0, 0.15, 1.0), (0.8, 0.9, 2.0))
    p.params.setdefault('axis', 'z')
    p.params.setdefault('sound', 'chime')


# ================================================================ prop prefabs: food carts

def popcorn_cart(p, P):
    pv = p.part('pivot')
    g = pv.geo
    for sy in (-1, 1):
        spoked_wheel(g, P, (-0.25, sy * 0.42, 0.36), 0.36, spokes=10, rim=P.red, spoke=P.mustard)
    g.cyl((0.45, 0, 0.0), 0.05, 0.36, P.iron, n=6)
    g.box((0.0, 0, 0.62), (1.15, 0.7, 0.5), P.boards_red, bevel=0.02)
    g.box((0.0, -0.355, 0.62), (0.9, 0.01, 0.3), P.mustard)
    painted_letters(g, 'POPCORN', (0.0, -0.362, 0.53), 0.028, P.red)
    g.box((0, 0, 0.88), (1.2, 0.74, 0.04), P.mustard)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box((sx * 0.55, sy * 0.33, 1.2), (0.04, 0.04, 0.62), P.mustard)
    g.box((0, 0, 0.92), (1.08, 0.62, 0.04), P.popcorn)
    for k in range(18):
        rng = random.Random(k)
        bulb(g, (rng.uniform(-0.48, 0.48), rng.uniform(-0.26, 0.26), 0.96 + rng.uniform(0, 0.12)), P.popcorn, 0.06)
    g.lathe((0.1, 0.05, 1.12), [(0.1, 0), (0.16, 0.12), (0.17, 0.16)], P.iron, n=10)
    g.cyl((0.1, 0.05, 1.35), 0.01, 0.2, P.iron, n=4)
    for sx in (-1, 1):
        g.box((sx * 0.55, 0, 1.2), (0.01, 0.62, 0.6), P.glass)
    g.box((0, 0.33, 1.2), (1.06, 0.01, 0.6), P.glass)
    g.box((0, 0, 1.54), (1.2, 0.74, 0.06), P.mustard)
    wedge_cone(g, (0, 0, 1.56), 0.85, 0.0, 0.05, 0.42, [P.red, P.cream], n=12, rows=1)
    g.sphere((0, 0, 2.02), 0.07, P.mustard, n=8)
    g.tube([(0.58, -0.3, 0.75), (1.05, -0.3, 0.72), (1.05, 0.3, 0.72), (0.58, 0.3, 0.75)], 0.02, P.iron, n=4)
    bulb(g, (0, -0.37, 1.5), P.bulb, 0.04)
    p.body.collide((0.1, 0, 0.8), (1.3, 0.9, 1.6))
    p.params.setdefault('sound', 'thud')


def candy_cart(p, P):
    pv = p.part('pivot')
    g = pv.geo
    for sy in (-1, 1):
        spoked_wheel(g, P, (0.0, sy * 0.45, 0.4), 0.4, spokes=8, rim=P.teal, spoke=P.cream)
    g.box((0, 0, 0.75), (1.0, 0.75, 0.55), P.boards_teal, bevel=0.02)
    g.box((0, 0, 1.04), (1.08, 0.82, 0.04), P.cream)
    g.lathe((-0.15, 0, 1.06), [(0.12, 0), (0.3, 0.08), (0.32, 0.2), (0.3, 0.22)], P.iron, n=16, cap_top=False)
    g.blob((-0.15, 0, 1.3), 0.2, P.pink, seed=1, jitter=0.3, s=(1, 1, 0.6))
    for k in range(4):
        x = 0.25 + (k % 2) * 0.13
        y = -0.2 + (k // 2) * 0.32
        g.lathe((x, y, 1.06), [(0.005, 0), (0.025, 0.2)], P.cream, n=6)
        g.blob((x, y, 1.33), 0.1, P.pink if k % 3 else P.cream, seed=k + 3, jitter=0.3, s=(1, 1, 1.2))
    g.cyl((0.42, 0.3, 1.06), 0.02, 1.0, P.iron, n=6)
    wedge_cone(g, (0.42, 0.3, 2.0), 0.9, 0.0, 0.03, 0.3, [P.pink, P.cream], n=10, rows=2, sag=-0.04)
    g.tube([(-0.5, -0.3, 0.85), (-0.85, -0.3, 0.85), (-0.85, 0.3, 0.85), (-0.5, 0.3, 0.85)], 0.02, P.iron, n=4)
    g.cyl((-0.45, 0, 0.0), 0.04, 0.48, P.iron, n=6)
    p.body.collide((0, 0, 0.6), (1.1, 0.9, 1.2))
    p.params.setdefault('sound', 'thud')


# ================================================================ prop prefabs: fortune teller

def crystal_ball(p, P, light=('#8d7cff', 1.1, 6.5)):
    b = p.body
    b.lathe((0, 0, 0), [(0.11, 0), (0.1, 0.02), (0.05, 0.05), (0.04, 0.09), (0.08, 0.11)], P.brass, n=10)
    for k in range(3):
        a = k * TAU / 3
        b.tube([(0.07 * cos(a), 0.07 * sin(a), 0.1), (0.13 * cos(a), 0.13 * sin(a), 0.16), (0.08 * cos(a), 0.08 * sin(a), 0.23)],
               0.01, P.brass, n=4)
    g = p.geo('bulb0', (0, 0, 0.23))
    g.sphere((0, 0, 0), 0.12, P.crystal, n=16)
    if light:
        p.light((0, 0, 0.45), light[0], light[1], light[2], part='bulb0')
    p.params.setdefault('sound', 'buzz')


def bead_curtain(p, P, w=0.9, h=1.85, strands=10, groups=3):
    p.body.box((0, 0, 0.02), (w + 0.12, 0.05, 0.05), P.brass)
    mats = [P.red, P.mustard, P.teal, P.crystal, P.cream]
    parts = [p.part(f'cloth{k}', (0, 0, 0)) for k in range(groups)]
    for i in range(strands):
        x = -w / 2 + w * (i + 0.5) / strands
        g = parts[i % groups].geo
        nb = int(h / 0.075)
        for j in range(nb):
            z = -0.05 - j * 0.075
            bulb(g, (x, 0, z), mats[(i + j) % len(mats)] if j % 4 else P.mustard, 0.017)
        g.cyl((x, 0, -0.05 - nb * 0.075), 0.003, nb * 0.075, P.rope, n=3, caps=False)
    p.params.setdefault('amp', 0.04)
    p.params.setdefault('sound', 'jingle')


def candle_cluster(p, P, n=3, seed=0):
    rng = random.Random(seed)
    b = p.body
    b.cyl((0, 0, 0), 0.09, 0.015, P.brass, n=10)
    for i in range(n):
        a = i * TAU / n + 0.3
        d = 0.05 if n > 1 else 0
        hh = rng.uniform(0.08, 0.2)
        x, y = cos(a) * d, sin(a) * d
        b.cyl((x, y, 0.015), 0.018, hh, P.cream, n=8)
        b.lathe((x, y, 0.015), [(0.022, 0), (0.024, 0.03), (0.019, 0.06)], P.cream, n=6)
        p.flame((x, y, 0.015 + hh + 0.005), size=0.55)
    p.params.setdefault('sound', 'whoomp')


def wind_chime(p, P, drop=0.25):
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0, -drop), 0.005, drop, P.rope, n=3)
    g.cyl((0, 0, -drop - 0.02), 0.11, 0.02, P.wood, n=10)
    for k in range(6):
        a = k * TAU / 6
        ln = 0.2 + 0.05 * k
        g.cyl((0.08 * cos(a), 0.08 * sin(a), -drop - 0.06 - ln), 0.01, ln, P.brass, n=6)
    g.sphere((0, 0, -drop - 0.28), 0.03, P.crystal, n=8)
    p.params.setdefault('axes', 'xz')
    p.params.setdefault('amp', 0.07)
    p.params.setdefault('period', 1.8)
    p.params.setdefault('sound', 'jingle')


def hanging_sign(p, P, w=0.9, h=0.6, symbol='eye', arm=0.8):
    """Painted shop sign hanging from an iron arm (swing in its own plane... about local X)."""
    p.body.tube([(0, 0, 0.08), (-arm, 0, 0.08)], 0.02, P.iron, n=4)
    p.body.tube([(-arm, 0, 0.08), (-arm * 0.55, 0, -0.25), (-arm * 0.1, 0, 0.06)], 0.012, P.iron, n=4)
    pv = p.part('pivot', (-arm * 0.5, 0, 0.06))
    g = pv.geo
    for sx in (-1, 1):
        g.tube([(sx * w * 0.35, 0, 0), (sx * w * 0.35, 0, -0.12)], 0.006, P.iron, n=3)
    zc = -0.12 - h / 2
    g.box((0, 0, zc), (w, 0.04, h), P.indigo, bevel=0.01)
    for sy in (-1, 1):
        g.box((0, sy * 0.022, zc), (w - 0.06, 0.005, h - 0.06), P.mustard)
        g.box((0, sy * 0.025, zc), (w - 0.1, 0.005, h - 0.1), P.indigo)
        if symbol == 'eye':
            g.sphere((0, sy * 0.025, zc), 1.0, P.cream, n=12, s=(0.26, 0.012, 0.12))
            g.cyl((0, sy * 0.03, zc), 0.08, 0.008, P.teal, n=12, rx=PI / 2)
            g.cyl((0, sy * 0.036, zc), 0.035, 0.008, P.black, n=10, rx=PI / 2)
            for k in range(5):
                a = PI * (0.15 + 0.7 * k / 4)
                g.box((cos(a) * 0.2, sy * 0.028, zc + 0.08 + sin(a) * 0.08), (0.012, 0.004, 0.06), P.mustard, ry=-(a - PI / 2))
        else:
            g.cyl((0, sy * 0.03, zc), 0.16, 0.006, P.red, n=14, rx=PI / 2)
    p.params.setdefault('axes', 'x')
    p.params.setdefault('amp', 0.06)
    p.params.setdefault('period', 2.3)
    p.params.setdefault('sound', 'creak')


# ================================================================ prop prefabs: calliope

def calliope(p, P):
    b = p.body
    b.box((0, 0.05, 0.5), (1.9, 1.0, 1.0), P.boards_red, bevel=0.02)
    for z in (0.04, 0.98):
        b.box((0, 0.05, z), (1.96, 1.06, 0.06), P.mustard, bevel=0.01)
    for sx in (-1, 1):
        b.box((sx * 0.93, -0.46, 0.5), (0.1, 0.1, 1.0), P.mustard, bevel=0.01)
    b.box((0, -0.46, 0.5), (1.5, 0.02, 0.6), P.indigo)
    b.cyl((0, -0.47, 0.5), 0.25, 0.03, P.mustard, n=16, rx=PI / 2)
    b.cyl((0, -0.5, 0.5), 0.12, 0.02, P.red, n=12, rx=PI / 2)
    b.box((0, -0.6, 0.86), (1.4, 0.32, 0.06), P.wood)
    for i in range(24):
        b.box((-0.6 + i * 0.052, -0.66, 0.9), (0.044, 0.18, 0.02), P.cream)
        if i % 7 not in (2, 6):
            b.box((-0.574 + i * 0.052, -0.62, 0.915), (0.024, 0.1, 0.025), P.black)
    for row in range(3):
        for i in range(11):
            x = -0.8 + i * 0.16
            hh = 0.3 + 0.045 * i + row * 0.12
            y = -0.25 + row * 0.27
            b.lathe((x, y, 1.0), [(0.045, 0), (0.045, hh), (0.06, hh + 0.03), (0.03, hh + 0.1), (0.006, hh + 0.15)], P.brass, n=8)
            b.box((x, y - 0.045, 1.0 + hh * 0.3), (0.035, 0.01, 0.03), P.black)
    b.box((0, 0.5, 1.75), (1.9, 0.08, 1.5), P.boards_red, bevel=0.02)
    b.box((0, 0.455, 1.75), (1.7, 0.01, 1.3), P.indigo)
    b.add(gh.prim_lathe([(0.95, 0), (0.9, 0.04), (0.001, 0.07)], 14, False, False, False, arc=PI), P.mustard, gh.X((0, 0.48, 2.5), rx=PI / 2))
    for k in range(12):
        a = PI * (k + 0.5) / 12
        bulb(b, (cos(a) * 0.82, 0.43, 2.52 + sin(a) * 0.34), P.bulb if k % 5 else P.bulb_dead, 0.04)
    for k in range(10):
        a = k * TAU / 10
        b.box((cos(a) * 0.35, 0.445, 1.75 + sin(a) * 0.35), (0.05, 0.01, 0.42), P.mustard, ry=-a)
    b.cyl((0, 0.44, 1.75), 0.14, 0.01, P.red, n=14, rx=PI / 2)
    for k, sx in enumerate((-0.86, 0.86)):
        b.cyl((sx, -0.32, 1.0), 0.12, 0.05, P.mustard, n=10)
        d = p.geo(f'dancer{k}', (sx, -0.32, 1.05))
        figurine(d, P, P.teal if k else P.red, s=1.2)
    lid = p.part('pivot', (0, -0.46, 0.94))
    lid.geo.box((0, -0.17, 0.015), (1.44, 0.34, 0.03), P.wood_dark, bevel=0.006)
    b.collide((0, 0.05, 0.75), (1.9, 1.2, 1.5))
    p.params.setdefault('instrument', 'calliope')
    p.params.setdefault('axis', 'x')


# ================================================================ prop prefabs: funhouse

def clown_eye(p, P, r=0.55):
    """Hypnotic spiral eye facing -Y (spin about its face normal)."""
    b = p.body
    b.cyl((0, 0.06, 0), r + 0.12, 0.06, P.black, n=24, rx=PI / 2)
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0.0, 0), r, 0.04, P.cream, n=24, rx=PI / 2)
    pts = []
    for i in range(60):
        t = i / 59
        a = t * TAU * 2.6
        rr = 0.04 + (r - 0.08) * t
        pts.append((rr * cos(a), -0.045, rr * sin(a)))
    g.tube(pts, 0.035, P.black, n=4)
    g.sphere((0, -0.04, 0), 0.06, P.red, n=8)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('speed', 0.6)
    p.params.setdefault('wobble', 0.0)
    p.params.setdefault('sound', 'whirr')


def clown_jaw(p, P, w=2.0):
    """Lower jaw hinged at the cheeks (axis X); opens downward."""
    pv = p.part('pivot')
    g = pv.geo
    n = 12
    rx, rz = w / 2, 0.62
    cav = [(cos(PI + PI * i / n) * rx, sin(PI + PI * i / n) * rz) for i in range(n + 1)]
    g.prism((0, -0.02, 0), cav, 0.03, P.black, rx=PI / 2)
    for i in range(n):
        a0, a1 = PI + PI * i / n, PI + PI * (i + 1) / n
        p0 = (cos(a0) * rx, sin(a0) * rz)
        p1 = (cos(a1) * rx, sin(a1) * rz)
        q0 = (cos(a0) * (rx + 0.16), sin(a0) * (rz + 0.14))
        q1 = (cos(a1) * (rx + 0.16), sin(a1) * (rz + 0.14))
        g.add(prim_quad((p0[0], -0.06, p0[1]), (p1[0], -0.06, p1[1]), (q1[0], -0.06, q1[1]), (q0[0], -0.06, q0[1])), P.red)
    for i in range(5):
        x = -0.5 + i * 0.25
        zt = -sqrt_safe(1 - (x / rx) ** 2) * rz
        g.box((x, -0.06, zt + 0.1), (0.17, 0.03, 0.16), P.cream)
    g.sphere((0, 0.0, -rz - 0.42), 1.0, P.cream, n=12, s=(0.75, 0.22, 0.26))
    p.params.setdefault('axis', 'x')
    p.params.setdefault('dir', 1)
    p.params.setdefault('open', 0.45)
    p.params.setdefault('sound', 'bang')


def clown_nose(p, P, r=0.32, light=None):
    g = p.geo('bulb0')
    g.sphere((0, -r * 0.6, 0), r, P.bulb_red, n=14)
    if light:
        p.light((0, -1.2, 0), light[0], light[1], light[2], part='bulb0')
    p.params.setdefault('sound', 'buzz')


def fun_barrel(p, P, r=1.35, length=3.6, n=16):
    """Rotating barrel tunnel along local X (spin about X)."""
    pv = p.part('pivot')
    g = pv.geo
    mats = [P.red, P.cream, P.mustard, P.cream]
    for k in range(n):
        a0, a1 = k * TAU / n, (k + 1) * TAU / n
        pts0 = [(x, r * cos(a0), r * sin(a0)) for x in (-length / 2, length / 2)]
        pts1 = [(x, r * cos(a1), r * sin(a1)) for x in (-length / 2, length / 2)]
        g.add(prim_quad(pts0[0], pts1[0], pts1[1], pts0[1]), mats[k % len(mats)])
        q = [(x, (r + 0.08) * cos(a), (r + 0.08) * sin(a)) for x in (-length / 2, length / 2) for a in (a0, a1)]
        g.add(prim_quad(q[0], q[2], q[3], q[1]), P.wood_dark)
    for x in (-length / 2, length / 2):
        g.torus((x, 0, 0), r + 0.04, 0.07, P.mustard, n=n * 2, m=5, ry=PI / 2)
    for x in (-length / 4, 0, length / 4):
        g.torus((x, 0, 0), r + 0.09, 0.03, P.iron, n=n * 2, m=4, ry=PI / 2)
    p.params.setdefault('axis', 'x')
    p.params.setdefault('speed', 0.35)
    p.params.setdefault('wobble', 0.0)
    p.params.setdefault('sound', 'whirr')


def jack_in_box(p, P):
    b = p.body
    b.box((0, 0, 0.3), (0.6, 0.6, 0.6), P.boards_teal, bevel=0.02)
    for sx in (-1, 1):
        b.box((sx * 0.301, 0, 0.3), (0.01, 0.4, 0.4), P.mustard)
    b.box((-0.35, 0, 0.6), (0.6, 0.6, 0.04), P.boards_teal, ry=1.2)
    b.collide((0, 0, 0.3), (0.62, 0.62, 0.6))
    pv = p.part('pivot', (0, 0, 0.6))
    g = pv.geo
    pts = [(0.09 * cos(i * 0.9), 0.09 * sin(i * 0.9), i * 0.035) for i in range(16)]
    g.tube(pts, 0.012, P.iron, n=4)
    g.sphere((0, 0, 0.72), 0.17, P.cream, n=12)
    g.sphere((0, -0.16, 0.72), 0.04, P.bulb_red, n=8)
    for sx in (-1, 1):
        g.sphere((sx * 0.06, -0.14, 0.78), 0.02, P.black, n=6)
        g.sphere((sx * 0.17, 0, 0.78), 0.08, P.red, n=8)
    g.lathe((0, 0, 0.86), [(0.12, 0), (0.001, 0.32)], P.teal, n=10)
    g.sphere((0, 0, 1.19), 0.04, P.mustard, n=6)
    g.torus((0, 0, 0.56), 0.14, 0.05, P.red, n=12, m=6)
    p.params.setdefault('amp', 0.05)
    p.params.setdefault('sound', 'squeak')


# ================================================================ prop prefabs: back lot

def laundry_line(p, P, length=5.0, h=2.0, items=None, sag=0.25):
    b = p.body
    a, c = (-length / 2, 0, h), (length / 2, 0, h)
    for x in (-length / 2, length / 2):
        b.cyl((x, 0, 0), 0.05, h + 0.15, P.wood, n=6)
        b.box((x, 0, h + 0.02), (0.06, 0.4, 0.05), P.wood)
        b.collide((x, 0, h / 2), (0.2, 0.2, h))
    b.tube(catenary(a, c, sag, 12), 0.006, P.rope, n=3, caps=False)
    items = items or []
    for k, (t, w, hh, mat) in enumerate(items):
        top = cat_point(a, c, sag, t)
        pt = p.part(f'cloth{k}', (top[0], 0, top[2] - 0.01))
        pt.geo.sheet((0, 0, 0), w, hh, mat, nx=6, ny=6)
        for sx in (-1, 1):
            b.box((top[0] + sx * w * 0.4, 0, top[2] + 0.01), (0.015, 0.025, 0.06), P.wood)
    p.params.setdefault('amp', 0.05)
    p.params.setdefault('sound', 'whoosh')


def campfire(p, P, light=('#ff9a45', 1.6, 9.0)):
    b = p.body
    for k in range(9):
        a = k * TAU / 9
        soft_blob(b, (cos(a) * 0.55, sin(a) * 0.55, 0.08), 0.13, P.stone, seed=k, jitter=0.3, s=(1.2, 1, 0.75))
    for k in range(4):
        a = k * TAU / 4 + 0.3
        b.tube([(cos(a) * 0.45, sin(a) * 0.45, 0.05), (cos(a) * 0.05, sin(a) * 0.05, 0.28)], 0.05, P.wood_dark, n=6)
    soft_blob(b, (0, 0, 0.03), 0.3, P.ember, seed=4, jitter=0.3, s=(1, 1, 0.25))
    for i, (x, y, s) in enumerate(((0, 0, 3.2), (0.12, 0.05, 2.0), (-0.1, -0.06, 2.3), (0.02, -0.12, 1.7))):
        p.flame((x, y, 0.08), size=s)
    for k in range(3):
        a = k * TAU / 3
        b.tube([(cos(a) * 0.7, sin(a) * 0.7, 0), (0, 0, 1.3)], 0.02, P.iron, n=4)
    b.tube([(0, 0, 1.3), (0, 0, 0.85)], 0.006, P.iron, n=3)
    b.lathe((0, 0, 0.55), [(0.1, 0), (0.16, 0.08), (0.15, 0.24), (0.09, 0.3)], P.iron, n=10)
    b.collide((0, 0, 0.3), (1.2, 1.2, 0.6))
    if light:
        p.light((0, 0, 0.8), light[0], light[1], light[2], part='flame0')
    p.params.setdefault('sound', 'whoomp')


def fire_barrel(p, P, light=('#ff9040', 1.3, 8.0)):
    b = p.body
    b.lathe((0, 0, 0), [(0.27, 0), (0.3, 0.2), (0.31, 0.42), (0.3, 0.65), (0.28, 0.82)], P.iron, n=14, cap_top=False)
    for z in (0.15, 0.68):
        b.torus((0, 0, z), 0.305, 0.015, P.wood_dark, n=14, m=3)
    for k in range(5):
        a = k * TAU / 5
        b.box((cos(a) * 0.3, sin(a) * 0.3, 0.3), (0.02, 0.08, 0.05), P.ember, rz=a)
    b.cyl((0, 0, 0.7), 0.26, 0.04, P.ember, n=12)
    for k in range(3):
        a = k * TAU / 3
        p.flame((cos(a) * 0.1, sin(a) * 0.1, 0.74), size=2.4 - k * 0.4)
    b.collide((0, 0, 0.42), (0.62, 0.62, 0.84))
    if light:
        p.light((0, 0, 1.1), light[0], light[1], light[2], part='flame0')
    p.params.setdefault('sound', 'whoomp')


def barbell(p, P):
    b = p.body
    for sx in (-1, 1):
        b.box((sx * 0.5, 0, 0.35), (0.08, 0.35, 0.7), P.wood_dark)
        b.add(gh.prim_lathe([(0.06, 0), (0.06, 0.05)], 8, False, False, False, arc=PI), P.wood_dark,
              gh.X((sx * 0.5 - 0.025, 0, 0.72), ry=PI / 2))
    b.collide((0, 0, 0.35), (1.1, 0.4, 0.7))
    pv = p.part('pivot', (0, 0, 0.75))
    g = pv.geo
    g.cyl((-0.85, 0, 0), 0.025, 1.7, P.iron, n=8, ry=PI / 2)
    for sx in (-1, 1):
        g.sphere((sx * 0.85, 0, 0), 0.22, P.black, n=14)
        g.torus((sx * 0.63, 0, 0), 0.04, 0.015, P.iron, n=8, m=3, ry=PI / 2)
    g.box((-0.85, -0.2, 0.1), (0.12, 0.02, 0.06), P.cream)
    p.params.setdefault('sound', 'thud')


def gramophone(p, P):
    g = p.body
    g.box((0, 0, 0.1), (0.38, 0.38, 0.2), P.wood, bevel=0.015)
    rec = p.geo('dancer0', (0, 0, 0.2))
    rec.cyl((0, 0, 0), 0.16, 0.012, P.black, n=16)
    rec.cyl((0, 0, 0.012), 0.04, 0.005, P.red, n=10)
    rec.box((0.09, 0, 0.013), (0.05, 0.01, 0.003), P.cream)
    g.tube([(0.15, 0.15, 0.2), (0.15, 0.15, 0.35), (0.05, 0.05, 0.42)], 0.015, P.brass, n=5)
    with g.at((0.05, 0.05, 0.42), rx=-0.9, rz=0.6):
        g.lathe((0, 0, 0), [(0.02, 0), (0.04, 0.15), (0.1, 0.3), (0.26, 0.42), (0.3, 0.44)], P.brass, n=12, cap_top=False, cap_bottom=False)
    g.box((0.2, 0, 0.1), (0.02, 0.02, 0.06), P.brass)
    p.params.setdefault('instrument', 'musicbox')


def padlock_chain(p, P, drop=0.35):
    pv = p.part('pivot')
    g = pv.geo
    for i in range(6):
        g.torus((0, 0, -0.035 - i * 0.055), 0.025, 0.007, P.iron, n=8, m=3, rx=PI / 2 if i % 2 else 0, ry=PI / 2 if i % 2 == 0 else 0)
    g.box((0, 0, -drop - 0.06), (0.12, 0.05, 0.1), P.brass, bevel=0.01)
    g.torus((0, 0, -drop + 0.0), 0.04, 0.01, P.iron, n=10, m=3, rx=PI / 2, arc=PI)
    p.params.setdefault('axes', 'xz')
    p.params.setdefault('amp', 0.05)
    p.params.setdefault('period', 1.6)
    p.params.setdefault('sound', 'rattle')


def tamer_stool(p, P):
    pv = p.part('pivot')
    g = pv.geo
    wedge_drum(g, (0, 0, 0), 0.24, 0.2, 0.55, [P.red, P.cream], n=8)
    g.cyl((0, 0, 0.55), 0.23, 0.04, P.mustard, n=12)
    g.tube([(-0.1, -0.05, 0.6), (0.1, 0.05, 0.62), (0.25, 0.2, 0.6), (0.4, 0.15, 0.59), (0.5, -0.1, 0.6)], 0.008, P.wood_dark, n=3)
    g.cyl((-0.15, -0.08, 0.59), 0.014, 0.25, P.wood_dark, n=5, ry=PI / 2.3)
    p.body.collide((0, 0, 0.3), (0.5, 0.5, 0.6))
    p.params.setdefault('sound', 'thud')


def service_bell(p, P):
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0, 0), 0.06, 0.015, P.wood_dark, n=10)
    g.lathe((0, 0, 0.015), [(0.05, 0), (0.048, 0.01), (0.03, 0.045), (0.006, 0.055)], P.brass, n=12)
    g.cyl((0, 0, 0.07), 0.004, 0.015, P.brass, n=4)
    g.sphere((0, 0, 0.088), 0.008, P.brass, n=6)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('tone', 1400)
    p.params.setdefault('sound', 'bell')


def turnstile(p, P):
    b = p.body
    b.box((0, 0, 0.5), (0.25, 0.25, 1.0), P.red, bevel=0.02)
    b.box((0, 0, 1.02), (0.3, 0.3, 0.04), P.mustard)
    b.collide((0, 0, 0.5), (0.3, 0.3, 1.0))
    pv = p.part('pivot', (0, 0, 1.04))
    g = pv.geo
    g.cyl((0, 0, 0), 0.07, 0.14, P.iron, n=8)
    g.sphere((0, 0, 0.16), 0.06, P.brass, n=8)
    for k in range(4):
        a = k * TAU / 4 + 0.3
        g.tube([(0.06 * cos(a), 0.06 * sin(a), 0.07), (0.6 * cos(a), 0.6 * sin(a), 0.07)], 0.024, P.brass, n=6)
        g.sphere((0.6 * cos(a), 0.6 * sin(a), 0.07), 0.035, P.red, n=6)
    p.params.setdefault('axis', 'y')
    p.params.setdefault('speed', 0.0)
    p.params.setdefault('wobble', 0.03)
    p.params.setdefault('sound', 'clatter')


def gate_leaf_geo(g, P, w=2.3, h=2.4, side=1):
    s = side
    g.box((s * w / 2, 0, 0.12), (w, 0.05, 0.05), P.iron)
    g.box((s * w / 2, 0, h - 0.25), (w, 0.05, 0.05), P.iron)
    g.box((s * w / 2, 0, 1.1), (w, 0.04, 0.04), P.iron)
    n = int(w / 0.14)
    for i in range(n + 1):
        x = s * (0.05 + i * (w - 0.1) / n)
        top = h - 0.25 + 0.22 * sin(PI * abs(x) / w)
        g.cyl((x, 0, 0.05), 0.014, top - 0.05, P.iron, n=5)
        g.lathe((x, 0, top), [(0.025, 0), (0.001, 0.09)], P.iron, n=4, smooth=False)
    g.torus((s * w / 2, 0, 1.75), 0.3, 0.02, P.iron, n=16, m=4, rx=PI / 2)
    g.torus((s * w / 2, 0, 1.75), 0.15, 0.015, P.brass, n=12, m=3, rx=PI / 2)
    g.box((s * (w - 0.05), 0, h / 2 - 0.1), (0.07, 0.07, h - 0.2), P.iron)
    g.box((s * 0.04, 0, h / 2), (0.08, 0.08, h), P.iron)


def gate_leaf(p, P, w=2.3, h=2.4, side=1):
    """Iron gate leaf hinged at local x=0, extending toward +x*side (hinge, sound rattle)."""
    pv = p.part('pivot')
    g = pv.geo
    gate_leaf_geo(g, P, w, h, side)
    for i in range(5):
        g.torus((side * (w - 0.04), -0.06, 1.25 - i * 0.07), 0.03, 0.008, P.iron, n=8, m=3,
                rx=PI / 2 if i % 2 else 0, ry=PI / 2 if i % 2 == 0 else 0)
    g.box((side * (w - 0.04), -0.08, 0.88), (0.1, 0.04, 0.12), P.brass, bevel=0.01)
    p.params.setdefault('axis', 'y')
    p.params.setdefault('dir', side)
    p.params.setdefault('open', 0.25)
    p.params.setdefault('sound', 'rattle')


def shutter(p, P, w=1.2, h=0.8, mat=None, prop_open=0.9):
    """Top-hinged shutter (hinge about local X) propped part-way open; origin at the hinge line."""
    pv = p.part('pivot', (0, 0, 0), rx=-prop_open)
    g = pv.geo
    g.box((0, -0.025, -h / 2), (w, 0.05, h), mat or P.boards_teal, bevel=0.01)
    g.box((0, -0.055, -h / 2), (w - 0.1, 0.01, h - 0.1), P.mustard)
    g.box((0, -0.06, -h / 2), (w - 0.16, 0.01, h - 0.16), mat or P.boards_teal)
    for sx in (-1, 1):
        p.body.tube([(sx * (w / 2 - 0.08), -0.02, -h * 1.05), (sx * (w / 2 - 0.08), -sin(prop_open) * h * 0.95, -cos(prop_open) * h * 0.95)], 0.012, P.iron, n=4)
    p.params.setdefault('axis', 'x')
    p.params.setdefault('dir', -1)
    p.params.setdefault('open', 0.5)
    p.params.setdefault('sound', 'bang')


def tarp_sheet(p, P, w=2.6, h=1.6, mat=None, nx=8, ny=6, parts=2):
    """Loose tarp hanging from its top edge along local X."""
    pw = w / parts
    for k in range(parts):
        pt = p.part(f'cloth{k}', (-w / 2 + pw * (k + 0.5), 0, 0))
        pt.geo.sheet((0, 0, 0), pw, h * (1 - 0.12 * k), mat or P.tarp, nx=nx, ny=ny)
    p.params.setdefault('amp', 0.06)
    p.params.setdefault('sound', 'whoosh')


def spring_rider(p, P):
    """Coin-op spring rider shaped like a little duck (rock)."""
    b = p.body
    b.cyl((0, 0, 0), 0.4, 0.08, P.iron, n=14)
    b.collide((0, 0, 0.45), (0.7, 0.7, 0.9))
    pv = p.part('pivot', (0, 0, 0.08))
    g = pv.geo
    pts = [(0.09 * cos(i * 1.2), 0.09 * sin(i * 1.2), i * 0.022) for i in range(16)]
    g.tube(pts, 0.016, P.iron, n=4)
    g.sphere((0, 0, 0.55), 1.0, P.teal, n=12, s=(0.36, 0.2, 0.18))
    g.sphere((0.26, 0, 0.82), 0.14, P.teal, n=12)
    g.prism((0.38, 0, 0.78), [(0, -0.04), (0.13, 0.0), (0, 0.04)], 0.05, P.mustard)
    for sy in (-1, 1):
        g.sphere((0.33, sy * 0.1, 0.87), 0.025, P.black, n=6)
        g.sphere((0.0, sy * 0.19, 0.58), 1.0, P.cream, n=8, s=(0.18, 0.04, 0.09))
    g.box((-0.04, 0, 0.74), (0.26, 0.24, 0.05), P.red, bevel=0.02)
    g.cyl((0.18, -0.15, 0.85), 0.012, 0.3, P.iron, n=5, rx=PI / 2)
    p.params.setdefault('axis', 'x')
    p.params.setdefault('period', 1.2)
    p.params.setdefault('sound', 'squeak')


def cymbal_monkey(p, P):
    """Wind-up cymbal monkey on a tin drum (music: musicbox); it spins while it plays."""
    b = p.body
    b.cyl((0, 0, 0), 0.11, 0.09, P.red, n=12)
    b.torus((0, 0, 0.09), 0.11, 0.01, P.mustard, n=12, m=3)
    b.torus((0, 0, 0.0), 0.11, 0.01, P.mustard, n=12, m=3)
    d = p.geo('dancer0', (0, 0, 0.09))
    d.sphere((0, 0, 0.1), 1.0, P.fur, n=8, s=(0.07, 0.06, 0.09))
    d.sphere((0, -0.04, 0.09), 1.0, P.cream, n=6, s=(0.045, 0.02, 0.06))
    d.sphere((0, 0, 0.23), 0.06, P.fur, n=8)
    d.sphere((0, -0.045, 0.22), 1.0, P.cream, n=6, s=(0.04, 0.025, 0.035))
    for sx in (-1, 1):
        d.sphere((sx * 0.055, 0, 0.25), 0.022, P.fur, n=6)
        bulb(d, (sx * 0.022, -0.055, 0.245), P.black, 0.009)
        d.tube([(sx * 0.06, 0, 0.15), (sx * 0.12, -0.04, 0.17), (sx * 0.1, -0.09, 0.2)], 0.014, P.fur, n=4)
        d.cyl((sx * 0.1, -0.095, 0.2), 0.04, 0.008, P.brass, n=10, rx=PI / 2 + sx * 0.6, rz=sx * 0.5)
        d.sphere((sx * 0.04, -0.03, 0.02), 1.0, P.fur, n=6, s=(0.03, 0.05, 0.025))
    d.cyl((0, 0, 0.28), 0.03, 0.035, P.red, n=8, r2=0.025)
    d.box((0, -0.0, 0.08), (0.13, 0.11, 0.06), P.red)
    p.params.setdefault('instrument', 'musicbox')


def work_lamp(p, P):
    """Generator work lamp: caged bulb on a pole (flicker)."""
    b = p.body
    b.cyl((0, 0, 0), 0.06, 2.6, P.wood_dark, n=6)
    b.box((0.25, 0, 2.5), (0.6, 0.06, 0.06), P.wood_dark)
    b.lathe((0.5, 0, 2.18), [(0.2, 0), (0.14, 0.08), (0.05, 0.2), (0.03, 0.3)], P.iron, n=10, cap_bottom=False)
    for k in range(4):
        a = k * TAU / 4
        b.tube([(0.5 + 0.06 * cos(a), 0.06 * sin(a), 2.18), (0.5 + 0.1 * cos(a), 0.1 * sin(a), 2.06), (0.5, 0, 1.98)], 0.006, P.iron, n=3)
    b.tube([(0.5, 0, 2.48), (0.3, 0, 2.52), (0.05, 0.05, 2.3), (0.06, 0.06, 0.3), (0.4, 0.5, 0.02), (1.6, 1.4, 0.02)], 0.012, P.black, n=4)
    g = p.geo('bulb0', (0.5, 0, 2.08))
    g.sphere((0, 0, 0), 0.07, P.bulb, n=10)
    b.collide((0, 0, 1.3), (0.2, 0.2, 2.6))
    p.params.setdefault('sound', 'buzz')


def rocking_horse(p, P, s=0.55):
    """Child's wooden rocking horse (rock about its rockers' axis)."""
    p.body.collide((0, 0, 0.45 * s / 0.55), (1.0, 0.5, 0.9))
    pv = p.part('pivot')
    g = pv.geo
    for sy in (-1, 1):
        pts = [(-0.55 + 1.1 * i / 8, sy * 0.16, 0.05 + 0.1 * ((i / 8 - 0.5) * 2) ** 2) for i in range(9)]
        g.tube(pts, 0.025, P.red, n=5)
        for x in (-0.25, 0.25):
            g.tube([(x, sy * 0.16, 0.07), (x * 0.8, sy * 0.06, 0.38)], 0.02, P.wood, n=4)
    with g.at((0, 0, 0.75), s=s / 0.55 * 0.62):
        horse_geo(g, P, P.cream, P.red, P.teal)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('period', 1.4)
    p.params.setdefault('sound', 'creak')


def hay_prop(p, P, s=(1.0, 0.5, 0.42)):
    pv = p.part('pivot')
    g = pv.geo
    g.box((0, 0, s[2] / 2), s, P.hay, bevel=0.06)
    for x in (-s[0] * 0.25, s[0] * 0.25):
        g.box((x, 0, s[2] / 2), (0.03, s[1] + 0.012, s[2] + 0.012), P.rope)
    p.body.collide((0, 0, s[2] / 2), s)
    p.params.setdefault('sound', 'thud')
