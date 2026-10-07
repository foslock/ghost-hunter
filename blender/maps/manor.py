"""Hollowmere Manor: a candlelit Victorian house, one floor, twelve rooms in loops.

Floor plan (Blender XY, north = +Y, front door on the south side):

  y=22 +-----------+-------------+---------------+------------------+
       |           |  NURSERY    |   SCULLERY    |                  |
       |  LIBRARY  |             +---D-------D---+   CONSERVATORY   |
       |  (stacks) D             |               D  (The Birdcage)  |
  y=10 |           +------D------+    KITCHEN    |  glass N/E walls |
       |           D MUSIC ROOM  |               D                  |
  y=0  +----A------+--D----+--D--+--B--+---D-----+------D-----------+
       |  PORTRAIT GALLERY  D  landing  D      SERVANTS' HALL       |
  y=-6 +----D----+-----D---+  (stairs)  +--D------------------D-----+
       |  STUDY  D  PARLOR A   FOYER    A        DINING ROOM        |
  y=-22+---------+---------+---[door]---+---------------------------+
       x=-30    -19       -9            9                           30
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from lib import gh, prefabs as pf, tex  # noqa: E402
import manor_props as mp  # noqa: E402
from manor_props import PI, HALF, WARM, CANDLE  # noqa: E402

m = gh.MapBuilder('manor', 'Hollowmere Manor')
COOL = '#7f9ad8'


# =================================================================== palette

class NS:
    pass


M = NS()
M.walnut = m.mat('walnut', '#3a2416', rough=0.55)
M.walnut_dark = m.mat('walnut_dark', '#22150d', rough=0.6)
M.mahogany = m.mat('mahogany', '#4e2216', rough=0.45)
M.pine = m.mat('pine', '#7a5a3a', rough=0.75)
M.brass = m.mat('brass', '#b08a3e', rough=0.35, metal=1.0)
M.iron = m.mat('iron', '#1e1c1e', rough=0.55, metal=0.6)
M.copper = m.mat('copper', '#a0583a', rough=0.35, metal=1.0)
M.steel = m.mat('steel', '#8a8c90', rough=0.3, metal=1.0)
M.marble = m.mat('marble', image=mp.marble_tex(), uv=1.4, rough=0.25)
M.marble_dark = m.mat('marble_dark', '#2e2a28', rough=0.3)
M.linen = m.mat('linen', '#d8ccb4', rough=0.9)
M.porcelain = m.mat('porcelain', '#ece6da', rough=0.25)
M.paper = m.mat('paper', '#cfc3a6', rough=0.9)
M.wax = m.mat('wax', '#efe6d0', rough=0.6)
M.glow = m.mat('glow', '#ffd9a0', rough=0.5, emit='#ffb866', strength=3.0)
M.ember = m.mat('ember', '#ff6a20', rough=1.0, emit='#ff5a14', strength=4.0)
M.glass = m.mat('window_glass', '#2a3a5a', rough=0.1, emit='#4a6aa8', strength=0.9)
M.glass_dark = m.mat('glass_dark', '#26342e', rough=0.08, metal=0.3)
M.mirror = m.mat('mirror', '#9aa4b0', rough=0.05, metal=1.0)
M.black = m.mat('black', '#121012', rough=0.4)
M.velvet_moss = m.mat('velvet_moss', image=tex.fabric(base='#3e4a26', seed=31), uv=0.8)
M.velvet_plum = m.mat('velvet_plum', image=tex.fabric(base='#4a2440', seed=32, pattern='diamonds', pattern_col='#5e3254'), uv=0.8)
M.velvet_ox = m.mat('velvet_ox', image=tex.fabric(base='#5a1820', seed=33), uv=0.8)
M.books = [m.mat('book_red', '#5a1a1a'), m.mat('book_green', '#26361f'), m.mat('book_navy', '#1e2638'), m.mat('book_tan', '#7a5a3a')]
M.leaf_dark = m.mat('leaf_dark', '#2e4226', rough=0.8)
M.leaf_light = m.mat('leaf_light', '#4a5e30', rough=0.8)
M.leaves = [M.leaf_dark, M.leaf_light]
M.leaf_dead = m.mat('leaf_dead', '#6a5a3a', rough=0.9)
M.terracotta = m.mat('terracotta', '#8a4a32')
M.wicker = m.mat('wicker', '#a08458')
M.roast = m.mat('roast', '#5a3220', rough=0.6)
M.coal = m.mat('coal', '#1a1614', rough=0.95)
M.wool = m.mat('wool', '#2c2826', rough=1.0)
M.crepe = m.mat('crepe', '#121014', rough=0.95)
M.toy_red = m.mat('toy_red', '#8a2a22', rough=0.5)
M.toy_blue = m.mat('toy_blue', '#2a4a6a', rough=0.5)
M.portraits = m.mat('portraits', image=mp.portrait_atlas(), uv=mp.ATLAS_UV, rough=0.45)
# aliases keep the material count down
M.glow_dim = M.glow
M.lily = M.paper
M.owl = M.roast
M.owl_face = M.wicker
M.amber = M.glow
M.bark = M.walnut_dark
M.sea = M.toy_blue
M.slate = M.iron
M.night = M.black
M.flag_dark = M.coal
M.crystal = M.mirror
M.bone = M.paper
M.lace = M.linen
M.felt = M.velvet_moss
M.wine = M.velvet_ox
M.glass_green = M.glass_dark

# large surfaces
M.floor_walnut = m.mat('floor_walnut', image=tex.wood_planks(base='#4a3020', dark='#2a1a10', light='#5e3e26', planks=6, seed=41), uv=3.0)
M.parquet = m.mat('parquet', image=mp.parquet(), uv=2.4)
M.floor_check = m.mat('floor_check', image=tex.checker_tiles(a='#d6cdb8', b='#262220', tiles=4, seed=42), uv=3.2, uv_rot=PI / 4, rough=0.3)
M.flagstone = m.mat('flagstone', image=tex.flagstones(stone='#6a6258', grout='#2a2622', n_cells=6, seed=43), uv=3.0)
M.encaustic = m.mat('encaustic', image=mp.encaustic(), uv=1.6)
M.wp_ox = m.mat('wp_ox', image=mp.damask_floral(bg='#4a1820', fg='#66262c'), uv=1.4)
M.wp_plum = m.mat('wp_plum', image=tex.wallpaper(bg='#3a1c34', fg='#52284a', stripe='#2a1226', seed=45), uv=1.6)
M.wp_moss = m.mat('wp_moss', image=tex.wallpaper(bg='#2c3620', fg='#3e4a2c', stripe='#20281a', seed=46, motifs=4), uv=1.6)
M.wp_nursery = m.mat('wp_nursery', image=tex.stripes(a='#8a6e68', b='#c6b69c', count=6, wear=0.3, seed=47), uv=1.2)
M.panelling = m.mat('panelling', image=mp.panelling(), uv=1.2)
M.plaster = m.mat('plaster', image=tex.noise_tint(base='#b4a68e', amount=0.14, seed=48), uv=2.0)
M.ceiling = m.mat('ceiling', image=tex.noise_tint(base='#4e443a', amount=0.12, seed=49), uv=3.0)
M.brick = m.mat('brick', image=tex.bricks(brick='#6e4232', mortar='#3e3630', seed=50), uv=1.6)
M.rug_red = m.mat('rug_red', image=tex.fabric(base='#561a1c', seed=51, pattern='diamonds', pattern_col='#7a4a26'), uv=0.9)
M.rug_blue = m.mat('rug_blue', image=tex.fabric(base='#222a3c', seed=52, pattern='diamonds', pattern_col='#5a4a32'), uv=0.9)
M.altar_glow = m.mat('altar_glow', '#9fd8c0', rough=0.5, emit='#6fd0a8', strength=1.2)
M.floor_check_mat = M.floor_check
M.plaster_dark = M.ceiling


# =================================================================== helpers

def face_dir(dx, dy):
    """rz that turns a prefab's -Y front toward (dx, dy)."""
    return math.atan2(dx, -dy)


def rel(base, rz, local):
    """World position of a point given in an object's local frame."""
    c, s = math.cos(rz), math.sin(rz)
    x, y = local[0], local[1]
    z = local[2] if len(local) > 2 else 0.0
    return (base[0] + x * c - y * s, base[1] + x * s + y * c, (base[2] if len(base) > 2 else 0.0) + z)


def place(fn, typ, label, pos, rz=0.0, params=None, key=None, **kw):
    """MapBuilder.place, but keyed copies keep the prefab's default params (toolkit drops them)."""
    cached = m.prop_cache.get(key) if key else None
    p = m.place(fn, typ, label, pos, rz, params, key=key, **kw)
    if cached is not None:
        for k, v in cached.params.items():
            p.params.setdefault(k, v)
    return p


def put(fn, pos, rz=0.0, **kw):
    return m.put(fn, pos, rz, **kw)


def geo_at(pos):
    return m.static(pos[0], pos[1])


def rug(x0, y0, x1, y1, field, border=None, fringe=True):
    g = geo_at(((x0 + x1) / 2, (y0 + y1) / 2))
    border = border or M.velvet_moss
    cx, cy, w, d = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    g.box((cx, cy, 0.006), (w, d, 0.012), border)
    g.box((cx, cy, 0.008), (w - 0.36, d - 0.36, 0.013), field)
    g.box((cx, cy, 0.009), (w - 0.5, d - 0.5, 0.0135), field)
    for sx in (-1, 1):
        g.box((cx + sx * (w / 2 - 0.24), cy, 0.0095), (0.03, d - 0.42, 0.014), M.brass if field is M.rug_red else M.paper)
        if fringe:
            g.box((cx + sx * (w / 2 + 0.04), cy, 0.004), (0.08, d - 0.04, 0.008), M.linen)


# =================================================================== rooms

T = 0.3  # wall thickness


class Style:
    def __init__(self, paper, H=4.2, dado=None, dado_h=1.0, base=None, crown=None, panels=True, string=None):
        self.paper, self.H, self.dado, self.dado_h = paper, H, dado, dado_h
        self.base = base or M.walnut_dark
        self.crown = crown or M.walnut
        self.panels = panels
        self.string = string


class Room:
    def __init__(self, name, x0, y0, x1, y1, style, floor, ceil=None, H=None):
        self.name, self.x0, self.y0, self.x1, self.y1 = name, x0, y0, x1, y1
        self.s = style
        self.H = H or style.H
        self.floor = floor
        self.ceil = ceil or M.ceiling

    def on(self, side, t, off=0.0, z=0.0):
        """Point `off` metres out from a wall face, at coordinate t along the wall; rz faces into the room."""
        if side == 'N':
            return (t, self.y1 - T / 2 - off, z), 0.0
        if side == 'S':
            return (t, self.y0 + T / 2 + off, z), PI
        if side == 'W':
            return (self.x0 + T / 2 + off, t, z), HALF
        return (self.x1 - T / 2 - off, t, z), -HALF

    @property
    def c(self):
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)


ST = dict(
    foyer=Style(M.wp_ox, 7.5, M.marble, 1.3, M.marble_dark, M.walnut, string=4.2),
    parlor=Style(M.wp_plum, 4.2, M.panelling, 0.95),
    study=Style(M.wp_moss, 4.2, M.panelling, 2.1),
    dining=Style(M.wp_moss, 4.2, M.panelling, 1.05),
    gallery=Style(M.wp_ox, 4.2, M.panelling, 1.0),
    servants=Style(M.plaster, 4.2, M.walnut_dark, 1.2, panels=False),
    library=Style(M.panelling, 4.2, None),
    music=Style(M.wp_plum, 4.2, M.panelling, 1.0),
    nursery=Style(M.wp_nursery, 4.2, M.linen, 1.0, M.walnut),
    kitchen=Style(M.plaster, 4.2, M.brick, 1.3, panels=False),
    scullery=Style(M.plaster, 4.2, M.brick, 1.3, panels=False),
    cons=Style(M.brick, 4.6, None, base=M.marble_dark, crown=M.iron, panels=False),
)

R = dict(
    study=Room('Study', -30, -22, -19, -6, ST['study'], M.floor_walnut, M.panelling),
    parlor=Room('Parlour', -19, -22, -9, -6, ST['parlor'], M.floor_walnut),
    foyer=Room('Grand Foyer', -9, -22, 9, 0, ST['foyer'], M.floor_check),
    dining=Room('Dining Room', 9, -22, 30, -6, ST['dining'], M.parquet),
    gallery=Room('Portrait Gallery', -30, -6, -9, 0, ST['gallery'], M.parquet),
    servants=Room("Servants' Hall", 9, -6, 30, 0, ST['servants'], M.flagstone, M.plaster),
    library=Room('Library', -30, 0, -15, 22, ST['library'], M.floor_walnut, M.panelling),
    music=Room('Music Room', -15, 0, 0, 10, ST['music'], M.parquet),
    nursery=Room('Nursery', -15, 10, 0, 22, ST['nursery'], M.floor_walnut, M.plaster),
    kitchen=Room('Kitchen', 0, 0, 16, 14, ST['kitchen'], M.flagstone, M.plaster),
    scullery=Room('Scullery', 0, 14, 16, 22, ST['scullery'], M.flagstone, M.plaster),
    cons=Room('Conservatory', 16, 0, 30, 22, ST['cons'], M.encaustic),
)


# =================================================================== walls

def wbox(axis, fixed, u0, u1, v0, v1, z0, z1, mat, bevel=0.0):
    if u1 - u0 < 1e-4 or v1 - v0 < 1e-4 or z1 - z0 < 1e-4:
        return
    if axis == 'h':
        c = ((u0 + u1) / 2, fixed + (v0 + v1) / 2, (z0 + z1) / 2)
        s = (u1 - u0, v1 - v0, z1 - z0)
    else:
        c = (fixed + (v0 + v1) / 2, (u0 + u1) / 2, (z0 + z1) / 2)
        s = (v1 - v0, u1 - u0, z1 - z0)
    m.static(c[0], c[1]).box(c, s, mat, bevel=bevel, col=False)


def wcol(axis, fixed, u0, u1, v0, v1, z0, z1):
    if axis == 'h':
        m.collider((u0, fixed + v0, z0), (u1, fixed + v1, z1))
    else:
        m.collider((fixed + v0, u0, z0), (fixed + v1, u1, z1))


def vspan(sgn, a, b):
    lo, hi = sgn * a, sgn * b
    return min(lo, hi), max(lo, hi)


def face(axis, fixed, u0, u1, z0, z1, st, sgn, H):
    """One room's half of a wall between z0..z1 with its wallpaper, dado and mouldings."""
    t2 = T / 2
    dh = st.dado_h if st.dado else 0.0
    if st.dado and z0 < dh:
        wbox(axis, fixed, u0, u1, *vspan(sgn, 0, t2), z0, min(z1, dh), st.dado)
    if z1 > max(z0, dh):
        wbox(axis, fixed, u0, u1, *vspan(sgn, 0, t2), max(z0, dh), z1, st.paper)
    if z0 <= 0.001:
        wbox(axis, fixed, u0, u1, *vspan(sgn, t2, t2 + 0.025), 0, 0.2, st.base)
        wbox(axis, fixed, u0, u1, *vspan(sgn, t2, t2 + 0.035), 0.2, 0.235, st.base)
    if st.dado and z0 < dh - 0.02 < z1 and st.dado is not st.paper:
        wbox(axis, fixed, u0, u1, *vspan(sgn, t2, t2 + 0.035), dh - 0.035, dh + 0.035, st.crown, bevel=0.008)
        if st.panels and z0 <= 0.001 and dh > 0.7:
            n = max(1, int((u1 - u0 - 0.1) / 0.85))
            pw = (u1 - u0) / n
            for i in range(n):
                a = u0 + i * pw + 0.12
                b = u0 + (i + 1) * pw - 0.12
                if b - a > 0.15:
                    wbox(axis, fixed, a, b, *vspan(sgn, t2, t2 + 0.014), 0.34, dh - 0.14, st.dado, bevel=0.01)
    if st.string and z0 < st.string < z1:
        wbox(axis, fixed, u0, u1, *vspan(sgn, t2, t2 + 0.06), st.string - 0.08, st.string + 0.08, st.crown, bevel=0.01)
    if abs(z1 - H) < 0.001:
        wbox(axis, fixed, u0, u1, *vspan(sgn, t2, t2 + 0.09), H - 0.12, H, st.crown, bevel=0.01)
        wbox(axis, fixed, u0, u1, *vspan(sgn, t2, t2 + 0.045), H - 0.24, H - 0.12, st.crown)
        if H < 5:
            wbox(axis, fixed, u0, u1, *vspan(sgn, t2, t2 + 0.02), H - 0.62, H - 0.59, M.brass)  # picture rail


def casing(axis, fixed, op, st, sgn, H):
    t2 = T / 2
    u0, u1, top = op['u0'], op['u1'], op['top']
    cw = 0.13
    if op['kind'] == 'window':
        wbox(axis, fixed, u0 - 0.06, u1 + 0.06, *vspan(sgn, t2, t2 + 0.12), op['sill'] - 0.05, op['sill'], M.walnut, bevel=0.01)
        wbox(axis, fixed, u0, u1, *vspan(sgn, t2, t2 + 0.02), op['sill'] - 0.2, op['sill'] - 0.05, M.walnut)
        z0 = op['sill']
    else:
        z0 = 0
        for uu in (u0 - cw / 2 - 0.01, u1 + cw / 2 + 0.01):
            wbox(axis, fixed, uu - 0.09, uu + 0.09, *vspan(sgn, t2, t2 + 0.045), 0, 0.3, st.base)
    head = min(top + 0.2, H - 0.25)
    for uu in (u0 - cw / 2, u1 + cw / 2):
        wbox(axis, fixed, uu - cw / 2, uu + cw / 2, *vspan(sgn, t2, t2 + 0.03), z0, head, M.walnut, bevel=0.008)
    if head > top + 0.02:
        wbox(axis, fixed, u0 - cw, u1 + cw, *vspan(sgn, t2, t2 + 0.035), top, head, M.walnut, bevel=0.008)
        if head + 0.06 < H - 0.25:
            wbox(axis, fixed, u0 - cw - 0.08, u1 + cw + 0.08, *vspan(sgn, t2, t2 + 0.07), head, head + 0.06, M.walnut, bevel=0.01)
    if op['kind'] == 'arch':
        r = min(0.55, (u1 - u0) / 2 - 0.05)
        n = 6
        for corner in (0, 1):
            pts = [(0, 0)]
            if corner == 0:
                pts.append((0, -r))
                for k in range(1, n):
                    a = PI - k * HALF / n
                    pts.append((r + r * math.cos(a), -r + r * math.sin(a)))
                pts.append((r, 0))
                cu = u0
            else:
                pts.append((-r, 0))
                for k in range(1, n):
                    a = HALF - k * HALF / n
                    pts.append((-r + r * math.cos(a), -r + r * math.sin(a)))
                pts.append((0, -r))
                cu = u1
            if axis == 'h':
                base = (cu, fixed + t2 + 0.005, top)
                geo_at(base).prism(base, pts, T + 0.01, M.walnut, rx=HALF)
            else:
                base = (fixed - t2 - 0.005, cu, top)
                geo_at(base).prism(base, pts, T + 0.01, M.walnut, rx=HALF, rz=HALF)
        km = (u0 + u1) / 2
        wbox(axis, fixed, km - 0.1, km + 0.1, *vspan(sgn, t2, t2 + 0.06), top - 0.12, top + 0.16, M.marble, bevel=0.01)


def jambs(axis, fixed, op):
    u0, u1, top = op['u0'], op['u1'], op['top']
    t2 = T / 2 + 0.02
    wbox(axis, fixed, u0, u0 + 0.03, -t2, t2, 0, top, M.walnut)
    wbox(axis, fixed, u1 - 0.03, u1, -t2, t2, 0, top, M.walnut)
    wbox(axis, fixed, u0, u1, -t2, t2, top - 0.03, top, M.walnut)


DOOR_PROPS = []


def wall(axis, fixed, a, b, neg, pos, ops=()):
    """Axis-aligned wall on the line x=fixed ('v') or y=fixed ('h') from a to b.
    neg/pos: Room on the -Y/-X and +Y/+X sides (None = outside). ops: openings, dicts with
    c (centre along the wall), w, kind ('door', 'arch', 'window', 'sealed'), top, sill, door=..."""
    rooms = [r for r in (neg, pos) if r is not None]
    H = max(r.H for r in rooms)
    Hcol = 9.0 if len(rooms) < 2 else H
    spans = []
    cur = a
    for op in sorted(ops, key=lambda o: o['c']):
        op = dict(op)
        op.setdefault('kind', 'door')
        op.setdefault('top', 2.5 if op['kind'] != 'window' else 3.4)
        op.setdefault('sill', 0.0)
        op['u0'], op['u1'] = op['c'] - op['w'] / 2, op['c'] + op['w'] / 2
        if op['u0'] > cur:
            spans.append((cur, op['u0'], None))
        spans.append((op['u0'], op['u1'], op))
        cur = op['u1']
    if cur < b:
        spans.append((cur, b, None))
    sides = [(neg, -1), (pos, 1)]
    for u0, u1, op in spans:
        if op is None:
            wcol(axis, fixed, u0, u1, -T / 2, T / 2, 0, Hcol)
            for r, sgn in sides:
                if r is not None:
                    face(axis, fixed, u0, u1, 0, r.H, r.s, sgn, r.H)
            continue
        top = op['top']
        if op['kind'] in ('window', 'sealed'):
            wcol(axis, fixed, u0, u1, -T / 2, T / 2, 0, Hcol)
        else:
            wcol(axis, fixed, u0, u1, -T / 2, T / 2, top, Hcol)
        for r, sgn in sides:
            if r is None:
                continue
            if op['kind'] == 'window' and op['sill'] > 0:
                face(axis, fixed, u0, u1, 0, op['sill'], r.s, sgn, r.H)
            if top < r.H:
                face(axis, fixed, u0, u1, top, r.H, r.s, sgn, r.H)
            casing(axis, fixed, op, r.s, sgn, r.H)
        if op['kind'] == 'window':
            pos3 = (op['c'], fixed, op['sill']) if axis == 'h' else (fixed, op['c'], op['sill'])
            put(mp.window, pos3, 0.0 if axis == 'h' else HALF, M=M, w=op['w'], h=top - op['sill'])
        else:
            jambs(axis, fixed, op)
        if op.get('door'):
            DOOR_PROPS.append((axis, fixed, op, neg, pos))


def doors():
    """Hinged door props for openings that asked for one."""
    for axis, fixed, op, neg, pos in DOOR_PROPS:
        d = op['door']
        into = d.get('into', 'pos')
        if axis == 'h':
            pos3, rz = (op['c'], fixed, 0), 0.0
            open_dir = 1 if into == 'pos' else -1
        else:
            pos3, rz = (fixed, op['c'], 0), HALF
            open_dir = -1 if into == 'pos' else 1
        w = op['w'] - 0.08
        place(mp.door, 'hinge', d['label'], pos3, rz, key=d.get('key'), M=M, w=w, h=op['top'] - 0.04,
              hinge=d.get('hinge', 'left'), rest=d.get('rest', 0.0), open_dir=open_dir,
              wood=d.get('wood'), baize=d.get('baize', False))


def D(c, w=1.5, top=2.5, **door):
    op = dict(c=c, w=w, top=top, kind='door')
    if door:
        op['door'] = door
    return op


def A(c, w=2.2, top=3.0):
    return dict(c=c, w=w, top=top, kind='arch')


def W(c, w=1.5, sill=0.8, top=3.4):
    return dict(c=c, w=w, sill=sill, top=top, kind='window')


r = R
# ---- exterior
wall('h', -22, -30, -19, None, r['study'], [W(-27.0), W(-22.0)])
wall('h', -22, -19, -9, None, r['parlor'], [W(-16.4, 1.6, 0.6, 3.5), W(-11.6, 1.6, 0.6, 3.5)])
wall('h', -22, -9, 9, None, r['foyer'], [W(-5.6, 1.6, 0.9, 6.4), dict(c=0, w=2.8, top=3.5, kind='sealed'), W(5.6, 1.6, 0.9, 6.4)])
wall('h', -22, 9, 30, None, r['dining'], [W(13.0, 1.6, 0.7), W(19.5, 1.6, 0.7), W(26.0, 1.6, 0.7)])
wall('v', -30, -22, -6, None, r['study'], [W(-14.0, 1.8, 0.7)])
wall('v', -30, -6, 0, None, r['gallery'], [W(-3.0, 1.8, 0.6, 3.6)])
wall('v', -30, 0, 22, None, r['library'], [W(4.5, 1.6, 0.8), W(17.0, 1.6, 0.8)])
wall('h', 22, -30, -15, r['library'], None, [W(-22.5, 1.6, 0.8)])
wall('h', 22, -15, 0, r['nursery'], None, [W(-7.5, 1.8, 0.75)])
wall('h', 22, 0, 16, r['scullery'], None, [W(4.0, 1.4, 1.2), W(12.0, 1.4, 1.2)])
wall('v', 30, -6, 0, r['servants'], None, [W(-3.0, 1.4, 1.0)])
wall('v', 30, -22, -6, r['dining'], None, [W(-18.5, 1.6, 0.7), W(-9.5, 1.6, 0.7)])
# ---- interior
wall('v', -19, -22, -6, r['study'], r['parlor'], [D(-18.3, label='Study Door', into='neg', rest=0.9)])
wall('v', -9, -22, -6, r['parlor'], r['foyer'], [A(-13.0, 2.4, 3.0)])
wall('v', -9, -6, 0, r['gallery'], r['foyer'], [D(-2.0, 1.6, 2.35, label='Gallery Door', into='neg', rest=1.2, hinge='right')])
wall('v', 9, -22, -6, r['foyer'], r['dining'], [A(-13.0, 2.4, 3.0)])
wall('v', 9, -6, 0, r['foyer'], r['servants'], [D(-2.0, 1.6, 2.35, label="Servants' Door", into='pos', rest=0.35)])
wall('h', -6, -30, -19, r['study'], r['gallery'], [D(-24.5, label='Study Door', into='neg', rest=1.35, hinge='right')])
wall('h', -6, -19, -9, r['parlor'], r['gallery'], [D(-14.0, label='Parlour Door', into='neg', rest=0.5)])
wall('h', -6, 9, 30, r['dining'], r['servants'], [D(13.0, label='Dining Room Door', into='neg', rest=1.1), D(26.0, label="Butler's Door", into='pos', rest=0.15, hinge='right')])
wall('h', 0, -30, -15, r['gallery'], r['library'], [A(-26.0, 2.0, 2.9)])
wall('h', 0, -15, -9, r['gallery'], r['music'], [D(-12.0, label='Music Room Door', into='pos', rest=1.3, hinge='right')])
wall('h', 0, -9, 0, r['foyer'], r['music'], [D(-5.0, 1.6, 2.35)])
wall('h', 0, 0, 9, r['foyer'], r['kitchen'], [D(5.0, 1.5, 2.35, label='Green Baize Door', into='pos', rest=0.2, baize=True)])
wall('h', 0, 9, 16, r['servants'], r['kitchen'], [D(12.5, label='Kitchen Door', into='pos', rest=1.25)])
wall('h', 0, 16, 30, r['servants'], r['cons'], [A(23.0, 2.2, 2.9)])
wall('v', -15, 0, 10, r['library'], r['music'], [D(5.0, label='Library Door', into='neg', rest=1.0, hinge='right')])
wall('v', -15, 10, 22, r['library'], r['nursery'], [D(17.0, label='Nursery Door', into='pos', rest=0.6)])
wall('h', 10, -15, 0, r['music'], r['nursery'], [D(-4.0, label='Nursery Door', into='pos', rest=1.3, hinge='right')])
wall('v', 0, 0, 10, r['music'], r['kitchen'])
wall('v', 0, 10, 14, r['nursery'], r['kitchen'])
wall('v', 0, 14, 22, r['nursery'], r['scullery'], [D(18.0, label='Back Stair Door', into='pos', rest=0.25, hinge='right')])
wall('h', 14, 0, 16, r['kitchen'], r['scullery'], [D(3.5, label='Pantry Door', into='pos', rest=0.7), A(12.0, 1.8, 2.6)])
wall('v', 16, 0, 14, r['kitchen'], r['cons'], [D(7.0, label='Garden Door', into='pos', rest=1.2)])
wall('v', 16, 14, 22, r['scullery'], r['cons'], [D(18.0, label='Scullery Door', into='neg', rest=0.4, hinge='right')])


# =================================================================== floors and ceilings

for rm in R.values():
    m.floor(rm.x0, rm.y0, rm.x1, rm.y1, rm.floor)
    if rm.name == 'Conservatory':
        continue
    m.box((rm.c[0], rm.c[1], rm.H + 0.125), (rm.x1 - rm.x0, rm.y1 - rm.y0, 0.25), rm.ceil)


def beams(rm, n, axis='x', mat=None, depth=0.22):
    mat = mat or M.walnut_dark
    g = geo_at(rm.c)
    for i in range(1, n):
        if axis == 'x':
            y = rm.y0 + (rm.y1 - rm.y0) * i / n
            g.box(((rm.x0 + rm.x1) / 2, y, rm.H - depth / 2), (rm.x1 - rm.x0, 0.22, depth), mat)
        else:
            x = rm.x0 + (rm.x1 - rm.x0) * i / n
            g.box((x, (rm.y0 + rm.y1) / 2, rm.H - depth / 2), (0.22, rm.y1 - rm.y0, depth), mat)


def rose(pos, H, r=0.45):
    geo_at(pos).lathe((pos[0], pos[1], H - 0.06), [(r, 0.06), (r * 0.8, 0.03), (r * 0.5, 0.0), (0.1, -0.02), (0.001, -0.03)], M.ceiling, n=16, cap_top=False)


beams(R['library'], 5, 'x')
beams(R['study'], 4, 'x')
beams(R['kitchen'], 4, 'y', M.pine, 0.26)
beams(R['scullery'], 3, 'y', M.pine, 0.26)
beams(R['servants'], 5, 'y', M.pine, 0.2)


# =================================================================== conservatory shell (glass)

def conservatory_shell():
    rm = R['cons']
    g = geo_at(rm.c)
    eave, ridge, xr = 4.6, 6.4, 23.0

    def roof_z(x):
        return eave + (ridge - eave) * (1 - abs(x - xr) / (xr - rm.x0))
    # glass walls on N (y=22) and E (x=30): dwarf brick wall, iron frame, moonlit panes
    for axis, fixed, a, b in (('h', 22.0, 16.0, 30.0), ('v', 30.0, 0.0, 22.0)):
        L = b - a
        n = int(round(L / 1.15))
        wbox(axis, fixed, a, b, -T / 2, T / 2, 0, 0.55, M.brick)
        wbox(axis, fixed, a, b, -T / 2 - 0.04, T / 2, 0.55, 0.62, M.marble)
        wbox(axis, fixed, a, b, -0.03, 0.03, 0.62, eave, M.glass)
        for i in range(n + 1):
            u = a + L * i / n
            wbox(axis, fixed, u - 0.05, u + 0.05, -0.1, 0.1, 0.62, eave, M.iron)
        for z in (0.66, 2.4, 3.3, eave - 0.06):
            wbox(axis, fixed, a, b, -0.08, 0.08, z - 0.04, z + 0.04, M.iron)
        for i in range(n):
            u = a + L * (i + 0.5) / n
            for zz in (2.85,):
                if axis == 'h':
                    g.torus((u, fixed - 0.06, zz), 0.28, 0.018, M.iron, n=14, m=4, rx=HALF)
                else:
                    g.torus((fixed - 0.06, u, zz), 0.28, 0.018, M.iron, n=14, m=4, rx=HALF, rz=HALF)
        if axis == 'h':
            m.collider((a, fixed - T / 2, 0), (b, fixed + T / 2, 9.0))
        else:
            m.collider((fixed - T / 2, a, 0), (fixed + T / 2, b, 9.0))
    # pitched glass roof, ridge running N-S
    slope = math.atan2(ridge - eave, xr - rm.x0)
    run = math.hypot(xr - rm.x0, ridge - eave)
    for sx in (-1, 1):
        cx = xr + sx * (xr - rm.x0) / 2
        cz = (eave + ridge) / 2
        g.box((cx, 11.0, cz), (run, 22.0, 0.03), M.glass, ry=-sx * slope)
        for k in range(12):
            y = k * 22.0 / 11
            g.box((cx, y, cz - 0.05), (run, 0.08, 0.1), M.iron, ry=-sx * slope)
        g.box((cx, 11, cz - 0.08), (run, 0.06, 0.08), M.iron, ry=-sx * slope) if False else None
    g.box((xr, 11.0, ridge + 0.02), (0.16, 22.0, 0.16), M.iron)
    for x in (16.0, 30.0):
        g.box((x, 11.0, eave), (0.2, 22.0, 0.16), M.iron)
    for k in range(1, 6):  # tie rods with ring bosses
        y = k * 22.0 / 6
        g.box((xr, y, eave - 0.2), (14.0, 0.04, 0.04), M.iron)
        g.torus((xr, y, eave - 0.2), 0.35, 0.02, M.iron, n=16, m=4, rx=HALF, rz=HALF)
        g.cyl((xr, y, eave - 0.2), 0.02, ridge - eave + 0.2, M.iron, n=4)
    # gable glass at the north end, brick gable above the house walls (W and S)
    for y, mat in ((22.0, M.glass), (0.0, M.brick)):
        pts = [(rm.x0 - xr, 0), (rm.x1 - xr, 0), (0, ridge - eave)]
        base = (xr, y + (0.03 if y > 0 else 0.15), eave)
        g.prism(base, pts, 0.06 if y > 0 else 0.3, mat, rx=HALF)
    g.prism((16.0, 22.0, eave), [(0, 0), (22.0, 0), (22.0, 0.01)], 0.3, M.brick, rx=HALF, rz=-HALF) if False else None
    for x in (16.15,):
        g.box((x - 0.15 + 0.15, 11.0, (eave + R['kitchen'].H) / 2 + 0.2), (0.3, 22.0, eave - R['kitchen'].H + 0.4), M.brick)
    m.collider((16, 0, ridge + 0.2), (30, 22, ridge + 0.5))
    m.collider((16 - T / 2, 0, 4.2), (16 + T / 2, 22, ridge + 0.5))
    m.collider((16, -T / 2, 4.2), (30, T / 2, ridge + 0.5))
    return roof_z


roof_z = conservatory_shell()


# =================================================================== the grand foyer

F = R['foyer']
LAND = 3.0
STEPS, RISE, RUN = 12, 0.25, 0.36
Y_LAND = -3.5
Y0 = Y_LAND - STEPS * RUN


def foyer_architecture():
    g = geo_at((0, -6))
    mp.stair_flight(g, M, -1.7, 1.7, Y0, STEPS, RISE, RUN, flare=(0.75, 0.5, 0.3, 0.15))
    # landing slab spanning the north wall, carried on two columns
    m.box((0, (Y_LAND + 0) / 2, LAND - 0.15), (18.0, -Y_LAND, 0.3), M.walnut_dark)
    g.box((0, (Y_LAND - 0.15) / 2, LAND + 0.006), (17.7, -Y_LAND - 0.15, 0.012), M.parquet)
    g.box((0, Y_LAND - 0.03, LAND - 0.17), (18.0, 0.08, 0.36), M.walnut, bevel=0.01)
    g.box((0, (Y_LAND - 0.15) / 2, LAND + 0.014), (10.0, 1.6, 0.01), M.velvet_ox)
    for sx in (-1, 1):
        with g.at((sx * 5.5, Y_LAND, 0)):
            mp.column(g, M, LAND - 0.3, 0.2)
        # stair balustrade (from the 4th step) and newel posts
        x = sx * 1.78
        y_start = Y0 + 4 * RUN

        def zf(t, y_start=y_start):
            y = y_start + (Y_LAND - y_start) * t
            k = min(STEPS - 1, int((y - Y0) / RUN))
            return RISE * (k + 1)
        mp.balusters(g, M, (x, y_start + 0.1), (x, Y_LAND - 0.05), zf, step=0.18)
        mp.newel(g, M, (x, y_start + 0.05, RISE * 4), 1.1)
        for k in range(4, STEPS):
            m.collider((x - 0.06, Y0 + k * RUN, 0), (x + 0.06, Y0 + (k + 1) * RUN, RISE * (k + 1) + 1.0))
        # landing balustrade
        a, b = (sx * 1.78, Y_LAND - 0.06), (sx * 8.85, Y_LAND - 0.06)
        mp.balusters(g, M, a, b, lambda t: LAND, step=0.2)
        mp.newel(g, M, (sx * 1.78, Y_LAND - 0.06, LAND), 1.15)
        lo, hi = sorted((sx * 1.7, sx * 8.85))
        m.collider((lo, Y_LAND - 0.14, LAND), (hi, Y_LAND + 0.02, LAND + 1.05))
        # stringers on the open sides of the flight
        g.box((x, (Y0 + Y_LAND) / 2 + 0.6, 1.2), (0.06, Y_LAND - Y0 - 1.2, 0.3), M.walnut, rx=-math.atan2(RISE, RUN) * 0 + 0.0) if False else None
    # fanlight above the front doors and the vestibule behind them
    fz = 3.75
    g.prism((0, -21.84, fz), [(math.cos(a) * 1.5, math.sin(a) * 1.5) for a in [i * PI / 12 for i in range(13)]], 0.02, M.glass, rx=HALF)
    for i in range(7):
        a = i * PI / 6
        g.box((math.cos(a) * 0.75, -21.86, fz + math.sin(a) * 0.75), (1.5, 0.03, 0.05), M.iron, ry=-a)
    g.torus((0, -21.86, fz), 1.5, 0.05, M.walnut, n=24, m=4, rx=HALF, arc=PI)
    g.torus((0, -21.87, fz), 0.45, 0.03, M.iron, n=12, m=4, rx=HALF, arc=PI)
    g.box((0, -21.86, fz - 0.05), (3.1, 0.06, 0.1), M.walnut)
    with g.at((0, -22.15, 0)):
        mp.vestibule(g, M, 2.8, 3.5)
    for sx in (-1, 1):
        place(mp.door, 'hinge', 'Front Door', (sx * 0.7, -22.0, 0), 0.0, key='frontdoor_' + ('l' if sx < 0 else 'r'),
              M=M, w=1.38, h=3.46, hinge='left' if sx < 0 else 'right', open_dir=1, wood=M.mahogany)
    # tall stair-window transoms
    for sx in (-1, 1):
        g.box((sx * 5.6, -22.0, 3.6), (1.6, 0.36, 0.1), M.walnut)
        g.box((sx * 5.6, -22.0, 5.0), (1.6, 0.36, 0.06), M.walnut)
    rose((0, -13.5), F.H, 0.7)


foyer_architecture()


def foyer_contents():
    rug(-1.3, -21.4, 1.3, -8.25, M.rug_red)
    put(mp.round_table, (0, -13.5, 0), r=0.95, h=0.8, top=M.marble)
    place(mp.dead_lilies, 'foliage', 'Funeral Lilies', (0, -13.5, 0.8), 0.3, M=M)
    g = geo_at((0, -13.5))
    g.cyl((0.55, -13.15, 0.8), 0.16, 0.02, M.brass, n=16)
    for i in range(3):
        g.box((0.55 + 0.03 * i, -13.15 + 0.02 * i, 0.83 + 0.004 * i), (0.12, 0.08, 0.003), M.paper, rz=0.3 * i)
    mp.book(g, M, (-0.6, -13.1, 0.8), rz=0.4, mat=M.books[0])
    mp.book(g, M, (-0.58, -13.12, 0.85), rz=0.2, mat=M.books[2])
    place(mp.candlestick, 'flame', 'Hall Candle', (-0.45, -13.95, 0.8), M=M, key='candlestick')
    place(mp.chandelier, 'swing', 'Great Chandelier', (0, -13.5, F.H), M=M, drop=2.2, arms=8, radius=1.0, tiers=2,
          light=(CANDLE, 2.4, 16.0), params={'amp': 0.01, 'period': 4.2})
    place(mp.grandfather_clock, 'clock', 'Grandfather Clock', *F.on('W', -17.6, 0.27), M=M)
    put(mp.sideboard, *F.on('E', -17.6, 0.25), w=1.7, d=0.45, h=0.86, doors=2, M=M)
    cpos, crz = F.on('E', -17.6, 0.0, 2.85)
    place(mp.covered_mirror, 'cloth', 'Shrouded Mirror', cpos, crz, M=M, w=1.2, h=1.7)
    place(mp.candelabra, 'flame', 'Hall Candelabra', rel(F.on('E', -17.6, 0.25)[0], -HALF, (0.5, 0, 0.86)), M=M, arms=3, key='candelabra3')
    place(mp.coat_rack, 'rock', 'Coat Stand', (3.4, -20.9, 0), 0.4, M=M)
    place(mp.umbrella_stand, 'jolt', 'Umbrella Stand', (2.35, -21.35, 0), M=M)
    bpos, brz = F.on('S', -3.6, 0.25)
    put(mp.bench, bpos, brz, w=1.5, cushion=M.velvet_ox, M=M)
    g = geo_at(bpos)
    g.cyl((-3.2, -21.5, 0.55), 0.1, 0.16, M.black, n=12)
    g.cyl((-3.2, -21.5, 0.55), 0.17, 0.012, M.black, n=14)
    g.box((-4.0, -21.55, 0.56), (0.18, 0.1, 0.02), M.wool, rz=0.4)
    for sx in (-1, 1):
        place(mp.fern, 'foliage', 'Potted Aspidistra', (sx * 3.0, -8.4, 0), sx * 0.7, M=M, seed=3 + sx, key='aspidistra', stand_h=0.75)
        spos, srz = F.on('W' if sx < 0 else 'E', -8.6, 0.0, 2.25)
        place(mp.sconce, 'flicker', 'Gas Sconce', spos, srz, M=M, key='sconce1')
        put(mp.window_seat if hasattr(mp, 'window_seat') else (lambda g, **k: None), (sx * 5.6, -21.6, 0))
    # landing: the master of the house watches over everything
    ppos, prz = F.on('N', 0.0, 0.0, 7.0)
    place(mp.portrait, 'swing', 'Portrait of Lord Hollowmere', ppos, prz, M=M, art='lord', k=1.75)
    for sx in (-1, 1):
        spos, srz = F.on('N', sx * 2.6, 0.0, 4.9)
        place(mp.sconce, 'flicker', 'Landing Sconce', spos, srz, M=M, arms=2, key=None if sx < 0 else 'sconce2',
              light=(CANDLE, 1.0, 8.0) if sx < 0 else None)
    lpos, lrz = F.on('N', -5.0, 0.45, LAND)
    put(mp.settee, lpos, lrz, fabric=M.velvet_ox, w=1.8, M=M)
    place(mp.palm, 'foliage', 'Landing Palm', (5.5, -1.0, LAND), 0.0, M=M, h=2.2, seed=8)
    for art, side in (('sea', 'W'), ('lake', 'E')):
        ppos, prz = F.on(side, -13.0, 0.0, 6.7)
        place(mp.portrait, 'swing', 'Painting of Hollowmere Lake' if art == 'lake' else 'Painting of the Wreck', ppos, prz, M=M, art=art, k=1.25)
    m.light((0, -19.5, 5.0), COOL, 0.7, 12.0)


foyer_contents()


# =================================================================== parlour

P = R['parlor']


def parlour():
    fpos, frz = P.on('W', -11.0, 0.6)
    put(mp.fireplace, fpos, frz, M=M, w=2.2, stone=M.marble, mantle=M.marble)
    fire = rel(fpos, frz, (0, 0.38, 0.1))
    place(mp.fire, 'flame', 'Parlour Fire', fire, frz, M=M, light=(WARM, 1.5, 9.0))
    mantel = rel(fpos, frz, (0, 0.2, 1.33))
    place(mp.mantel_clock, 'clock', 'Mantel Clock', mantel, frz, M=M)
    g = geo_at(fpos)
    for sx in (-1, 1):
        pp = rel(fpos, frz, (sx * 0.85, 0.2, 1.33))
        g.lathe(pp, [(0.05, 0), (0.07, 0.08), (0.06, 0.22), (0.03, 0.3), (0.045, 0.34)], M.porcelain, n=12)
    rug(-17.3, -14.2, -12.0, -7.6, M.rug_red)
    place(mp.rocking_chair, 'rock', 'Rocking Chair', (-16.4, -12.9, 0), face_dir(-1, 0.55), M=M, seat=M.velvet_plum)
    put(mp.settee, (-13.6, -11.0, 0), face_dir(-1, 0), fabric=M.velvet_moss, M=M)
    place(mp.armchair, 'jolt', 'Wingback Armchair', (-16.0, -8.6, 0), face_dir(-0.8, -1), M=M, fabric=M.velvet_moss, key='armchair_moss')
    put(mp.side_table, (-14.0, -8.5, 0), M=M)
    place(mp.oil_lamp, 'flicker', 'Oil Lamp', (-14.0, -8.5, 0.68), M=M, shade=M.glow, light=(WARM, 0.9, 6.5))
    place(mp.teacup, 'jolt', 'Teacup', (-13.85, -12.6, 0.0), M=M) if False else None
    # tea things on a low table before the settee
    put(lambda g, M: mp.side_table(g, M, r=0.42, h=0.45), (-14.9, -11.0, 0), M=M)
    place(mp.teacup, 'jolt', 'Teacup', (-14.75, -11.15, 0.45), 0.6, M=M)
    g = geo_at((-14.9, -11))
    g.lathe((-15.05, -10.8, 0.45), [(0.05, 0), (0.08, 0.05), (0.07, 0.12), (0.03, 0.15), (0.035, 0.17)], M.porcelain, n=12)
    g.tube([(-15.12, -10.8, 0.5), (-15.2, -10.8, 0.56)], 0.01, M.porcelain, n=4)
    # piano on the north wall
    ppos, prz = P.on('N', -11.4, 0.44)
    place(pf.upright_piano, 'music', 'Upright Piano', ppos, prz, wood=M.walnut, keys_white=M.porcelain, keys_black=M.black, brass=M.brass)
    place(mp.metronome, 'swing', 'Metronome', rel(ppos, prz, (0.55, 0.3, 1.4)), prz, M=M)
    g = geo_at(ppos)
    g.cyl((-11.4, -7.4, 0), 0.04, 0.45, M.walnut, n=8)
    g.cyl((-11.4, -7.4, 0.45), 0.2, 0.08, M.velvet_ox, n=14)
    for i in range(3):
        g.box((-11.85 + i * 0.2, -6.62, 0.83 + 0.0), (0.2, 0.004, 0.27), M.paper, rx=-0.2, rz=0.1 * (i - 1))
    for i, x in enumerate((-16.4, -11.6)):
        cpos, crz = P.on('S', x, 0.0, 3.75)
        place(mp.drapes, 'cloth', 'Velvet Drapes', cpos, crz, M=M, w=1.6, h=3.6, fabric=M.velvet_moss, key='drapes_moss')
    place(mp.fern, 'foliage', 'Boston Fern', (-9.75, -21.2, 0), M=M, seed=5, key='fern')
    # an abandoned game of patience
    put(mp.round_table, (-12.6, -17.3, 0), r=0.55, h=0.74, M=M)
    g = geo_at((-12.6, -17.3))
    import random as _r
    rr = _r.Random(3)
    for i in range(14):
        g.box((-12.6 + rr.uniform(-0.35, 0.35), -17.3 + rr.uniform(-0.35, 0.35), 0.745 + i * 0.0015), (0.07, 0.1, 0.002),
              M.porcelain if i % 3 else M.toy_red, rz=rr.uniform(0, 3))
    for a in (0.3, 2.6):
        put(mp.dining_chair_geo, (-12.6 + math.cos(a) * 0.85, -17.3 + math.sin(a) * 0.85, 0), face_dir(-math.cos(a), -math.sin(a)), M=M, seat=M.velvet_plum, wood=M.walnut)
    place(mp.portrait, 'swing', 'Portrait of Lady Hollowmere', *P.on('E', -18.0, 0.0, 2.95), M=M, art='lady', k=1.0)


parlour()


# =================================================================== study

S_ = R['study']


def study():
    rug(-26.8, -13.2, -22.2, -8.8, M.rug_blue)
    dpos = (-24.5, -11.2, 0)
    put(mp.desk, dpos, PI, M=M)
    place(mp.typewriter, 'jolt', 'Typewriter', rel(dpos, PI, (0.2, 0.05, 0.78)), PI + 0.1, M=M)
    place(mp.bankers_lamp, 'flicker', "Banker's Lamp", rel(dpos, PI, (-0.55, -0.15, 0.78)), PI, M=M, light=(WARM, 0.9, 6.5))
    g = geo_at(dpos)
    for i in range(5):
        g.box(rel(dpos, PI, (-0.2 + i * 0.03, -0.05, 0.782 + i * 0.002)), (0.21, 0.29, 0.002), M.paper, rz=0.15 * i)
    g.cyl(rel(dpos, PI, (0.6, -0.2, 0.78)), 0.035, 0.05, M.glass_dark, n=8)
    g.tube([rel(dpos, PI, (0.6, -0.2, 0.83)), rel(dpos, PI, (0.66, -0.26, 0.98))], 0.004, M.paper, n=3)
    for i in range(3):
        mp.book(g, M, rel(dpos, PI, (0.55, 0.15, 0.78 + i * 0.05)), rz=0.2 * i, mat=M.books[i])
    place(mp.swivel_chair, 'spin', 'Swivel Chair', (-24.5, -10.1, 0), PI, M=M)
    place(mp.telescope, 'spin', 'Brass Telescope', (-28.6, -14.0, 0), HALF, M=M)
    place(mp.cabinet, 'hinge', 'Curio Cabinet', *S_.on('N', -27.4, 0.27), M=M, contents='curio', seed=4, wood=M.walnut)
    for i, y in enumerate((-15.9, -13.6, -11.3, -9.0)):
        put(mp.bookcase, *S_.on('E', y, 0.23), w=2.2, h=2.6, seed=60 + i, M=M)
    cpos, crz = S_.on('S', -24.5, 0.27)
    put(mp.sideboard, cpos, crz, w=1.8, d=0.5, h=0.9, wood=M.walnut, M=M)
    place(mp.bracket_clock, 'clock', 'Bracket Clock', rel(cpos, crz, (-0.5, 0, 0.9)), crz, M=M)
    place(mp.owl, 'spin', 'Stuffed Owl', rel(cpos, crz, (0.45, 0, 0.9)), crz, M=M)
    place(mp.armchair, 'jolt', 'Leather Armchair', (-21.2, -19.0, 0), face_dir(-0.6, 1), M=M, fabric=M.roast)
    put(mp.side_table, (-20.3, -20.0, 0), r=0.25, h=0.6, M=M)
    g = geo_at((-20.3, -20.0))
    mp.bottle(g, M, (-20.35, -20.0, 0.6), 0.26, 0.05, M.glass_dark)
    mp.goblet(g, M, (-20.18, -19.9, 0.6))
    put(mp.stag_head, *S_.on('W', -9.0), M=M)
    cpos, crz = S_.on('W', -14.0, 0.0, 3.65)
    place(mp.drapes, 'cloth', 'Study Curtains', cpos, crz, M=M, w=1.8, h=3.5, fabric=M.velvet_ox, lace=False)
    g = geo_at((-27, -6.5))
    with g.at((-21.5, -6.6, 0)):
        mp.planter(g, M, 0.1, 0.1, 0.01, plants=False) if False else None


study()


# =================================================================== dining room

DR = R['dining']


def dining():
    cx, cy = 19.5, -14.0
    L, Wd = 7.6, 1.4
    rug(cx - 5.0, cy - 2.6, cx + 5.0, cy + 2.6, M.rug_red)
    put(mp.dining_table, (cx, cy, 0), L=L, W=Wd, M=M)
    top = 0.776
    xs = (16.7, 18.6, 20.4, 22.3)
    seats = []
    for x in xs:
        seats.append(((x, cy + 0.98), 0.0))
        seats.append(((x, cy - 0.98), PI))
    seats.append(((cx - L / 2 - 0.25, cy), HALF))
    seats.append(((cx + L / 2 + 0.25, cy), -HALF))
    g = geo_at((cx, cy))
    for i, ((x, y), rz) in enumerate(seats):
        if i == 2:
            place(mp.dining_chair, 'jolt', 'Dining Chair', (x + 0.15, y - 0.55, 0), rz + 0.45, M=M, seat=M.velvet_ox, key='dchair')
        elif i == 5:
            place(mp.dining_chair, 'jolt', 'Toppled Chair', (x - 0.2, y - 0.75, 0), rz - 0.3, M=M, seat=M.velvet_ox, tipped=True)
        elif i == 9:
            place(mp.dining_chair, 'jolt', 'Dining Chair', (x + 0.4, y, 0), rz - 0.2, M=M, seat=M.velvet_ox, key='dchair')
        else:
            put(mp.dining_chair_geo, (x, y, 0), rz, M=M, seat=M.velvet_ox)
        # place setting in front of each seat
        px, py, _ = rel((x, y, 0), rz, (0, -0.5, 0))
        if i in (5,):
            continue
        mp.plate(g, M, (px, py, top + 0.012))
        gx, gy, _ = rel((x, y, 0), rz, (0.2, -0.68, 0))
        mp.goblet(g, M, (gx, gy, top + 0.012), tipped=(i == 3))
        for sxx in (-1, 1):
            kx, ky, _ = rel((x, y, 0), rz, (sxx * 0.18, -0.5, 0))
            g.box((kx, ky, top + 0.016), (0.02, 0.2, 0.006), M.steel, rz=rz)
    g.cyl((18.6, cy - 0.3, top + 0.013), 0.16, 0.002, M.wine, n=14)  # spilled wine
    g.lathe((cx, cy, top + 0.012), [(0.3, 0), (0.34, 0.02), (0.36, 0.03)], M.steel, n=20)
    g.blob((cx, cy, top + 0.09), 0.16, M.roast, seed=2, jitter=0.12, s=(1.4, 1.0, 0.6))
    g.lathe((21.5, cy + 0.15, top + 0.012), [(0.18, 0), (0.18, 0.13), (0.15, 0.14), (0.15, 0.22), (0.001, 0.23)], M.linen, n=16)
    g.box((21.62, cy + 0.15, top + 0.13), (0.14, 0.02, 0.2), M.walnut, rz=0.3) if False else None
    g.lathe((18.0, cy + 0.2, top + 0.012), [(0.05, 0), (0.06, 0.04), (0.2, 0.1), (0.21, 0.11)], M.porcelain, n=14, cap_top=False)
    for k in range(5):
        g.sphere((18.0 + 0.07 * math.cos(k * 1.3), cy + 0.2 + 0.07 * math.sin(k * 1.3), top + 0.13), 0.045, M.wine if k % 2 else M.leaf_light, n=8)
    for x in (17.2, 21.8):
        place(mp.candelabra, 'flame', 'Table Candelabra', (x, cy - 0.1, top + 0.012), M=M, arms=5, key='candelabra5')
    place(mp.wine_bottle, 'jolt', 'Wine Bottle', (19.0, cy + 0.35, top + 0.012), 2.4, M=M)
    place(mp.chandelier, 'swing', 'Dining Chandelier', (17.4, cy, DR.H), M=M, drop=1.25, arms=6, radius=0.62,
          light=(CANDLE, 2.0, 12.0), key=None)
    place(mp.chandelier, 'swing', 'Dining Chandelier', (21.6, cy, DR.H), M=M, drop=1.25, arms=6, radius=0.62, key='chand_dark')
    rose((17.4, cy), DR.H)
    rose((21.6, cy), DR.H)
    place(mp.cabinet, 'hinge', 'China Cabinet', *DR.on('N', 19.5, 0.27), M=M, contents='china', seed=2, w=1.6)
    spos, srz = DR.on('E', -14.0, 0.3)
    put(mp.sideboard, spos, srz, w=2.4, d=0.55, h=0.94, M=M)
    g = geo_at(spos)
    for i, lx in enumerate((-0.8, -0.45, 0.6)):
        mp.bottle(g, M, rel(spos, srz, (lx, 0.05, 0.94)), 0.3, 0.05, M.glass_dark)
    g.lathe(rel(spos, srz, (0.1, 0.05, 0.94)), [(0.1, 0), (0.18, 0.08), (0.2, 0.18), (0.14, 0.24), (0.04, 0.27), (0.05, 0.3)], M.steel, n=14)
    place(mp.candlestick, 'flame', 'Sideboard Candle', rel(spos, srz, (1.0, 0.05, 0.94)), srz, M=M, key='candlestick')
    place(mp.gong, 'bell', 'Dinner Gong', (10.0, -19.6, 0), HALF, M=M)
    for x in (13.0, 26.0):
        cpos, crz = DR.on('S', x, 0.0, 3.6)
        place(mp.drapes, 'cloth', 'Dining Room Drapes', cpos, crz, M=M, w=1.6, h=3.45, fabric=M.velvet_ox, key='drapes_ox')
    put(mp.window_drape_static if hasattr(mp, 'window_drape_static') else (lambda g, **k: None), (19.5, -21.6, 0))
    place(mp.portrait, 'swing', 'Portrait of the Colonel', *DR.on('W', -18.6, 0.0, 3.0), M=M, art='colonel', k=1.15)
    place(mp.portrait, 'swing', 'Portrait of the Heir', *DR.on('N', 24.5, 0.0, 3.0), M=M, art='heir', k=0.95)


dining()


# =================================================================== portrait gallery

G = R['gallery']


def gallery():
    rug(-28.6, -3.65, -10.2, -2.35, M.rug_red, fringe=False)
    for art, x, k in (('girl', -22.6, 1.0), ('widow', -19.5, 1.1), ('uncle', -16.4, 1.0)):
        label = {'girl': 'Portrait of Little Ada', 'widow': 'Portrait of the Dowager', 'uncle': 'Portrait of Uncle Silas'}[art]
        place(mp.portrait, 'swing', label, *G.on('N', x, 0.0, 3.25), M=M, art=art, k=k)
    for art, x, k in (('hound', -21.2, 0.85), ('heir', -17.6, 0.9), ('colonel', -28.0, 0.9)):
        label = {'hound': 'Portrait of the Hound', 'heir': 'Portrait of Young Edmund', 'colonel': 'Portrait of Great-Uncle Ambrose'}[art]
        place(mp.portrait, 'swing', label, *G.on('S', x, 0.0, 3.1), M=M, art=art, k=k)
    bpos, brz = G.on('N', -14.3, 0.28)
    place(mp.bust, 'spin', 'Marble Bust', bpos, brz, M=M, who='man')
    bpos, brz = G.on('S', -19.4, 0.28)
    place(mp.bust, 'spin', 'Marble Bust', bpos, brz, M=M, who='woman')
    for y in (-4.65, -1.35):
        place(mp.armour, 'hinge', 'Suit of Armour', (-29.45, y, 0), HALF, M=M, key='armour', halberd=True)
    cpos, crz = G.on('W', -3.0, 0.0, 3.85)
    place(mp.drapes, 'cloth', 'Gallery Drapes', cpos, crz, M=M, w=1.8, h=3.7, fabric=M.velvet_ox, key='drapes_ox_wide')
    for i, x in enumerate((-21.05, -17.95)):
        spos, srz = G.on('N', x, 0.0, 2.35)
        place(mp.sconce, 'flicker', 'Gallery Sconce', spos, srz, M=M, key=None if i == 0 else 'sconce1',
              light=(CANDLE, 1.0, 8.0) if i == 0 else None)
    # a column screen halfway along breaks up the hall
    g = geo_at((-11.5, -3))
    for y in (-5.25, -0.75):
        with g.at((-11.0, y, 0)):
            mp.column(g, M, G.H - 0.3, 0.19)
    g.box((-11.0, -3.0, G.H - 0.3), (0.62, 6.0, 0.36), M.walnut, bevel=0.01)
    put(mp.bench, (-24.0, -2.0, 0), HALF, w=1.4, cushion=M.velvet_moss, M=M) if False else None


gallery()


# =================================================================== servants' hall

SV = R['servants']


def servants():
    bx = 17.6
    bpos, brz = SV.on('N', bx, 0.0, 2.6)
    g = geo_at(bpos)
    g.box((bx, -0.2, 2.62), (3.4, 0.08, 0.9), M.walnut, bevel=0.015)
    g.box((bx, -0.25, 2.62), (3.2, 0.02, 0.76), M.walnut_dark)
    g.box((bx, -0.24, 3.13), (3.6, 0.12, 0.12), M.walnut, bevel=0.01)
    bells = ('Drawing Room', 'Library', 'Nursery', 'Front Door', 'Blue Bedroom')
    for i, name in enumerate(bells):
        x = bx - 1.3 + i * 0.65
        g.box((x, -0.27, 2.95), (0.5, 0.01, 0.1), M.paper)
        place(mp.bell, 'bell', f'{name} Bell', (x, -0.26, 2.82), 0.0, M=M, key='bell', params={'tone': 700 + i * 70})
    put(mp.bench, (bx, -0.55, 0), PI, w=2.6, M=M)
    g = geo_at((bx, -0.6))
    for k in range(3):
        g.box((bx - 0.8 + k * 0.6, -0.75, 0.08), (0.12, 0.28, 0.16), M.black, bevel=0.03, rz=0.2 * k)
        g.box((bx - 0.66 + k * 0.6, -0.75, 0.08), (0.12, 0.28, 0.16), M.black, bevel=0.03, rz=0.2 * k - 0.1)
    place(mp.apron_pegs, 'cloth', 'Aprons on Pegs', *SV.on('S', 20.5, 0.0, 1.75), M=M, n=4)
    place(mp.bucket, 'jolt', 'Mop Bucket', (28.7, -5.2, 0), 0.3, M=M)
    place(mp.hanging_lantern, 'swing', 'Hall Lantern', (20.5, -3.0, SV.H), M=M, drop=1.0, light=(WARM, 1.1, 8.5))
    put(mp.wall_shelves, *SV.on('S', 14.6), w=2.4, rows=2, seed=7, z0=1.5, M=M)
    put(mp.wall_shelves, *SV.on('N', 27.2), w=2.0, rows=1, seed=9, z0=1.7, M=M)
    put(mp.round_table, (24.0, -3.0, 0), r=0.5, h=0.76, wood=M.pine, M=M) if False else None


servants()


# =================================================================== library

L_ = R['library']


def library():
    for i, (y, w) in enumerate(((2.0, 2.6), (7.0, 2.5), (9.55, 2.5), (12.1, 2.5), (14.65, 2.5), (19.7, 3.0))):
        put(mp.bookcase, *L_.on('W', y, 0.23), w=w, h=3.0, seed=10 + i, M=M)
    for i, x in enumerate((-28.0, -25.1, -19.9, -17.0)):
        put(mp.bookcase, *L_.on('N', x, 0.23), w=2.7, h=3.0, seed=20 + i, M=M)
    for i, (y, w) in enumerate(((2.2, 3.2), (7.4, 2.35), (9.8, 2.35), (12.2, 2.35), (14.6, 2.35), (19.8, 3.0))):
        put(mp.bookcase, *L_.on('E', y, 0.23), w=w, h=3.0, seed=30 + i, M=M)
    for i, (x, w) in enumerate(((-28.4, 1.8), (-23.4, 2.2))):
        put(mp.bookcase, *L_.on('S', x, 0.23), w=w, h=3.0, seed=40 + i, M=M)
    g = geo_at((-29.4, 10))
    g.cyl((-29.38, 5.6, 2.9), 0.016, 10.4, M.brass, n=6, rx=-HALF)
    for i, x in enumerate((-26.2, -22.5, -18.8)):
        with g.at((x, 13.8, 0), HALF):
            mp.stack(g, M, 7.6, 2.9, 50 + i)
    place(mp.ladder, 'swing', 'Library Ladder', (-29.35, 11.0, 2.9), HALF, M=M)
    # reading area by the fire
    fpos, frz = L_.on('S', -20.5, 0.6)
    put(mp.fireplace, fpos, frz, M=M, w=2.2, stone=M.marble_dark, mantle=M.walnut, glass=False)
    place(mp.fire, 'flame', 'Library Fire', rel(fpos, frz, (0, 0.38, 0.1)), frz, M=M, light=(WARM, 1.4, 9.0))
    place(mp.portrait, 'swing', 'Portrait of Lady Hollowmere', rel(fpos, frz, (0, 0.6, 3.3)), frz, M=M, art='lady', k=0.95)
    rug(-25.6, 1.6, -16.6, 9.6, M.rug_blue)
    for sx in (-1, 1):
        place(mp.armchair, 'jolt', 'Library Armchair', (-20.5 + sx * 1.4, 3.1, 0), face_dir(-sx * 0.5, -1), M=M, fabric=M.velvet_moss, key='armchair_moss')
    put(mp.side_table, (-20.5, 3.6, 0), r=0.26, h=0.6, M=M)
    place(mp.candlestick, 'flame', 'Reading Candle', (-20.45, 3.6, 0.6), M=M, key='candlestick')
    tpos = (-23.2, 7.0, 0)
    put(pf.table, tpos, 0.0, w=2.6, d=1.1, h=0.78, wood=M.walnut)
    g = geo_at(tpos)
    g.box((-23.2, 7.0, 0.784), (2.3, 0.85, 0.006), M.velvet_moss)
    mp.book(g, M, (-23.5, 6.9, 0.786), 0.22, 0.3, rz=0.1, mat=M.books[3], open_=True)
    mp.book(g, M, (-22.7, 7.2, 0.786), 0.18, 0.26, rz=-0.3, mat=M.books[1], open_=True)
    for i in range(4):
        mp.book(g, M, (-24.2, 7.15, 0.786 + i * 0.05), 0.2, 0.28, 0.045, rz=0.15 * i, mat=M.books[i % 4])
    g.cyl((-22.4, 6.75, 0.786), 0.05, 0.004, M.glass_dark, n=10)
    g.box((-22.25, 6.7, 0.79), (0.12, 0.012, 0.01), M.brass, rz=0.4)
    place(mp.candelabra, 'flame', 'Reading Lamp Candles', (-23.6, 7.35, 0.786), M=M, arms=3, key=None, light=(CANDLE, 0.9, 7.0))
    for x, y, rz in ((-24.0, 6.15, PI), (-22.4, 6.15, PI), (-23.2, 7.9, 0.15)):
        put(mp.dining_chair_geo, (x, y, 0), rz, M=M, seat=M.velvet_moss, wood=M.walnut)
    place(mp.globe, 'spin', 'Library Globe', (-27.6, 7.6, 0), 0.4, M=M)
    place(mp.lectern_book, 'cloth', 'Lectern Book', (-16.9, 8.4, 0), -HALF, M=M)
    place(mp.spider, 'bob', 'Dangling Spider', (-24.35, 15.8, L_.H), M=M, drop=1.9)
    for y in (4.5, 17.0):
        cpos, crz = L_.on('W', y, 0.0, 3.75)
        place(mp.drapes, 'cloth', 'Library Curtains', cpos, crz, M=M, w=1.6, h=3.6, fabric=M.velvet_moss, key='drapes_moss')
    put(mp.bust_static if hasattr(mp, 'bust_static') else (lambda g, **k: None), (-23.4, 0.4, 3.0))


library()


# =================================================================== music room

MU = R['music']


def music():
    opos, orz = MU.on('N', -10.0, 0.46)
    place(mp.organ_prop, 'music', 'Chamber Organ', opos, orz, M=M, params={'instrument': 'organ'})
    place(mp.candelabra, 'flame', 'Organ Candelabra', rel(opos, orz, (-1.15, -0.15, 1.1)), orz, M=M, arms=3, key=None, light=(CANDLE, 1.0, 7.5))
    place(mp.metronome, 'swing', 'Metronome', rel(opos, orz, (1.15, -0.15, 1.1)), orz, M=M, key='metronome')
    place(mp.gramophone, 'spin', 'Gramophone', (-1.0, 1.0, 0), face_dir(-1, 1), M=M)
    place(mp.dust_sheet, 'cloth', 'Shrouded Grand Piano', (-4.8, 6.3, 0), 0.5, M=M, shape='piano')
    place(mp.dust_sheet, 'cloth', 'Shrouded Chair', (-13.7, 2.0, 0), 2.2, M=M, shape='chair')
    rug(-13.0, 3.2, -7.4, 7.6, M.rug_blue)
    qc = (-10.2, 5.4)
    for k, a in enumerate((-2.6, -1.9, -1.2, -0.5)):
        x, y = qc[0] + math.cos(a) * 1.4, qc[1] + math.sin(a) * 1.4
        rz = face_dir(qc[0] - x, qc[1] + 1.2 - y)
        put(mp.dining_chair_geo, (x, y, 0), rz, M=M, seat=M.velvet_plum, wood=M.walnut)
        sx, sy, _ = rel((x, y, 0), rz, (0, -0.75, 0))
        if k == 1:
            place(mp.music_stand, 'jolt', 'Music Stand', (sx, sy, 0), rz, M=M)
        else:
            put(lambda g, M: mp.music_stand_geo(g, M), (sx, sy, 0), rz, M=M)
    put(mp.cello, (qc[0] + math.cos(-0.5) * 1.4 + 0.45, qc[1] + math.sin(-0.5) * 1.4 + 0.1, 0), 0.4, M=M)
    put(mp.harp, (-2.2, 8.6, 0), -0.6, M=M)
    place(mp.portrait, 'swing', 'Painting of Hollowmere Lake', *MU.on('W', 7.6, 0.0, 3.1), M=M, art='lake', k=0.8)


music()


# =================================================================== nursery

N_ = R['nursery']


def nursery():
    put(mp.bed, (-12.7, 20.6, 0), 0.0, M=M)
    put(mp.side_table, (-14.2, 21.2, 0), r=0.24, h=0.6, M=M)
    place(mp.oil_lamp, 'flicker', 'Night Lamp', (-14.2, 21.2, 0.6), M=M, shade=None, light=(WARM, 0.9, 7.0), key=None)
    place(mp.cradle, 'rock', 'Cradle', (-3.0, 19.6, 0), 0.0, M=M)
    place(mp.mobile, 'spin', 'Ceiling Mobile', (-3.0, 19.6, N_.H), M=M)
    place(mp.rocking_horse, 'rock', 'Rocking Horse', (-8.6, 15.2, 0), 0.7, M=M)
    put(mp.dollhouse, *N_.on('E', 12.2, 0.39), M=M)
    place(mp.wardrobe, 'hinge', 'Nursery Wardrobe', *N_.on('E', 15.6, 0.3), M=M)
    tpos, trz = N_.on('S', -10.5, 0.34)
    place(mp.puppet_theatre, 'cloth', 'Puppet Theatre', tpos, trz, M=M)
    place(mp.marionette, 'bob', 'Marionette', (-10.0, 11.35, 2.15), 0.3, M=M)
    geo_at((-10, 11.3)).cyl((-10.0, 11.35, 2.15), 0.004, N_.H - 2.15, M.linen, n=3)
    put(mp.toy_chest, *N_.on('W', 12.6, 0.29), M=M)
    place(mp.toy_blocks, 'jolt', 'Toy Blocks', (-6.4, 12.4, 0), 0.3, M=M, seed=1)
    place(mp.toy_blocks, 'jolt', 'Toy Blocks', (-12.2, 16.4, 0), 1.2, M=M, seed=2)
    place(mp.jack_in_box, 'hinge', 'Jack-in-the-Box', (-5.0, 13.4, 0), face_dir(1, -1), M=M)
    dpos, drz = N_.on('W', 14.6, 0.27)
    put(mp.sideboard, dpos, drz, w=1.1, d=0.45, h=0.85, wood=M.pine, doors=2, M=M)
    place(mp.music_box, 'music', 'Music Box', rel(dpos, drz, (-0.2, 0, 0.85)), drz + 0.4, M=M, params={'instrument': 'musicbox'})
    put(mp.doll_chair, rel(dpos, drz, (0.3, 0.02, 0.85)), drz, M=M)
    put(mp.tea_party, (-10.4, 18.4, 0), 0.4, M=M)
    rug(-11.0, 12.6, -5.4, 17.6, M.rug_blue)
    cpos, crz = N_.on('N', -7.5, 0.0, 3.55)
    place(mp.drapes, 'cloth', 'Lace Curtains', cpos, crz, M=M, w=1.8, h=3.0, fabric=M.velvet_plum)
    spos, srz = N_.on('N', -7.5, 0.3)
    put(mp.bench, spos, srz, w=2.0, cushion=M.velvet_plum, M=M)
    place(mp.portrait, 'swing', 'Portrait of Little Ada', *N_.on('S', -6.6, 0.0, 2.8), M=M, art='girl', k=0.7)


nursery()


# =================================================================== kitchen

K = R['kitchen']


def kitchen():
    rpos, rrz = K.on('N', 8.0, 0.95)
    put(mp.kitchen_range, rpos, rrz, M=M)
    place(mp.range_fire, 'flame', 'Range Firebox', rel(rpos, rrz, (-0.2, 0.25, 0.18)), rrz, M=M, light=(WARM, 1.4, 9.0))
    place(mp.kettle, 'jolt', 'Copper Kettle', rel(rpos, rrz, (-0.6, 0.38, 0.94)), rrz, M=M)
    g = geo_at(rpos)
    for i, x in enumerate((-1.3, -0.9, -0.4, 0.4, 0.95)):
        g.lathe(rel(rpos, rrz, (x, 0.13, 1.88)), [(0.07, 0), (0.09, 0.04), (0.09, 0.14)], M.copper if i % 2 == 0 else M.porcelain, n=12)
    tpos = (8.0, 6.6, 0)
    put(pf.table, tpos, 0.0, w=3.2, d=1.2, h=0.82, wood=M.pine)
    g = geo_at(tpos)
    import random as _r
    rr = _r.Random(11)
    for i in range(7):
        g.blob((7.0 + rr.uniform(-0.5, 0.5), 6.7 + rr.uniform(-0.3, 0.3), 0.87), rr.uniform(0.04, 0.07), rr.choice([M.terracotta, M.leaf_light, M.wicker]), seed=i, jitter=0.2)
    g.blob((9.1, 6.5, 0.9), 0.1, M.wicker, seed=3, jitter=0.1, s=(1.6, 1, 0.8))
    g.lathe((8.3, 6.9, 0.82), [(0.1, 0), (0.18, 0.06), (0.2, 0.1)], M.porcelain, n=14, cap_top=False)
    g.box((8.9, 6.95, 0.83), (0.4, 0.25, 0.03), M.pine)
    put(mp.pot_rack, (8.0, 6.42, 0), L=2.6, drop=1.1, ceil=K.H, M=M)
    for i, (x, y, pot) in enumerate(((7.0, 6.42, False), (8.0, 6.77, True), (9.0, 6.42, False), (9.6, 6.77, False))):
        place(mp.hanging_pan, 'swing', 'Hanging Pot' if pot else 'Hanging Pan', (x, y, K.H - 1.1), M=M, pot=pot, r=0.13 + 0.02 * (i % 2))
    put(mp.butcher_block, (2.6, 10.8, 0), M=M)
    place(mp.cleaver_block, 'jolt', 'Cleaver', (2.6, 10.8, 0.9), 0.4, M=M)
    put(mp.dresser, *K.on('W', 6.6, 0.27), M=M)
    put(mp.wall_shelves, *K.on('E', 11.3), w=3.6, rows=4, seed=3, M=M)
    for i, (x, y) in enumerate(((15.2, 1.0), (15.15, 1.75))):
        place(mp.barrel, 'jolt', 'Ale Barrel', (x, y, 0), 0.3 * i, M=M, key='barrel')
    g = geo_at((14, 2))
    g.blob((13.9, 0.75, 0.3), 0.32, M.wicker, seed=5, jitter=0.1, s=(1, 0.8, 1.0))
    g.blob((13.3, 0.7, 0.25), 0.28, M.wicker, seed=6, jitter=0.1, s=(1, 0.8, 0.9))
    place(mp.wall_clock, 'clock', 'Kitchen Clock', *K.on('S', 8.0, 0.0, 2.9), M=M)
    place(mp.hanging_meat, 'bob', 'Hanging Ham', (5.3, 11.6, K.H), M=M, kind='ham')
    place(mp.hanging_meat, 'bob', 'Brace of Pheasants', (10.8, 11.7, K.H), M=M, kind='birds')
    place(mp.hanging_lantern, 'swing', 'Kitchen Lantern', (4.0, 4.0, K.H), M=M, drop=1.1, light=(WARM, 1.0, 7.5), key=None)


kitchen()


# =================================================================== scullery

SC = R['scullery']


def scullery():
    put(mp.sink, (4.0, 21.5, 0), 0.0, M=M)
    place(mp.pump, 'hinge', 'Water Pump', (4.85, 21.55, 0), 0.0, M=M)
    put(mp.copper_boiler, (14.9, 20.8, 0), M=M)
    place(mp.mangle, 'spin', 'Mangle', (12.0, 19.9, 0), 0.0, M=M)
    place(mp.laundry, 'cloth', 'Washing Line', (4.0, 16.0, 0), 0.0, M=M, L=5.6, ceil=SC.H, drop=1.6, n=2, key='laundry')
    place(mp.laundry, 'cloth', 'Washing Line', (12.4, 16.2, 0), 0.0, M=M, L=5.6, ceil=SC.H, drop=1.6, n=2, key='laundry')
    place(mp.crate, 'jolt', 'Crate of Coal', (1.0, 15.0, 0), 0.2, M=M)
    place(mp.bucket, 'jolt', 'Pail', (6.1, 21.3, 0), 1.0, M=M, mop=False)
    put(mp.wall_shelves, *SC.on('S', 7.8), w=4.0, rows=3, seed=13, M=M)
    put(mp.washtub, (8.6, 21.0, 0), 0.2, M=M)
    place(mp.hanging_lantern, 'swing', 'Scullery Lantern', (8.0, 18.3, SC.H), M=M, drop=1.0, light=(WARM, 1.0, 8.0), key=None)


scullery()


# =================================================================== conservatory

C = R['cons']


def conservatory():
    cage = (23.5, 12.0)
    put(mp.giant_birdcage, (cage[0], cage[1], 0), 0.0, M=M)
    g = geo_at(cage)
    g.cyl((cage[0], cage[1], 4.95), 0.015, roof_z(cage[0]) - 4.95, M.iron, n=4)
    for dx, dy in ((0, 0), (1.0, 1.0), (-1.0, 1.0), (1.0, -1.0), (-1.0, -1.0)):
        m.penalty_spawn((cage[0] + dx, cage[1] + dy, 0))
    m.penalty['label'] = 'The Birdcage'
    put(mp.planter, (28.95, 5.5, 0), 0.0, w=1.3, d=6.0, h=0.5, seed=3, M=M)
    put(mp.planter, (19.75, 21.0, 0), 0.0, w=4.5, d=1.2, h=0.5, seed=4, M=M)
    place(mp.palm, 'foliage', 'Kentia Palm', (17.1, 20.9, 0), 0.3, M=M, h=2.8, seed=1, key=None)
    place(mp.palm, 'foliage', 'Kentia Palm', (29.0, 12.0, 0), 1.2, M=M, h=2.6, seed=2, key=None)
    place(mp.palm, 'foliage', 'Kentia Palm', (17.1, 10.2, 0), 2.0, M=M, h=2.4, seed=3, key=None)
    for x in (20.6, 25.4):
        place(mp.fern, 'foliage', 'Fern Stand', (x, 0.75, 0), M=M, seed=7, key='fern')
    place(mp.birdcage, 'swing', 'Canary Cage', (18.6, 16.6, 0), 0.6, M=M)
    place(mp.wicker_chair, 'jolt', 'Peacock Chair', (25.6, 5.0, 0), face_dir(0.6, 0.7), M=M, key='wicker')
    place(mp.wicker_chair, 'jolt', 'Peacock Chair', (27.6, 6.9, 0), face_dir(-0.9, -0.3), M=M, key='wicker')
    put(mp.side_table, (26.7, 5.9, 0), r=0.35, h=0.62, wood=M.wicker, M=M)
    g = geo_at((26.7, 5.9))
    g.lathe((26.6, 5.85, 0.62), [(0.05, 0), (0.08, 0.05), (0.07, 0.12), (0.03, 0.15), (0.035, 0.17)], M.porcelain, n=12)
    g.cyl((26.85, 6.0, 0.62), 0.07, 0.008, M.porcelain, n=12)
    place(mp.watering_can, 'jolt', 'Watering Can', (22.6, 20.2, 0), 0.8, M=M)
    place(mp.hanging_basket, 'foliage', 'Hanging Fern', (19.5, 6.0, roof_z(19.5)), M=M, drop=roof_z(19.5) - 2.7, seed=6, key=None)
    place(mp.hanging_basket, 'foliage', 'Hanging Fern', (27.0, 15.6, roof_z(27.0)), M=M, drop=roof_z(27.0) - 2.7, seed=9, key=None)
    put(mp.statue, (28.9, 20.9, 0), face_dir(-1, -1), M=M)
    m.light((20.0, 5.0, 4.4), COOL, 1.1, 13.0)
    m.light((26.0, 17.5, 4.4), COOL, 1.1, 13.0)


conservatory()

doors()


# =================================================================== altars, spawns, environment

ALTARS = [
    (-27.0, -18.4),   # study, by the window
    (-16.4, -18.6),   # parlour
    (12.3, -19.0),    # dining room, west end
    (27.0, -18.6),    # dining room, east end
    (-26.9, -3.0),    # portrait gallery, west end
    (27.1, -3.0),     # servants' hall, east end
    (-24.35, 19.6),   # library, north aisle
    (-7.4, 2.4),      # music room
    (-6.6, 19.0),     # nursery
    (3.2, 3.6),       # kitchen
    (8.2, 18.6),      # scullery
    (19.4, 4.1),      # conservatory, south
    (26.9, 18.8),     # conservatory, north-east corner
]
for x, y in ALTARS:
    m.flag_point((x, y, 0), 0.0, prefab=pf.altar, stone=M.marble, trim=M.brass, glow=M.altar_glow)

for x, y, dx, dy in ((-1.6, -19.8, 0, 1), (1.6, -19.8, 0, 1), (0.0, -18.9, 0, 1)):
    m.spawn('hunter', (x, y, 0), face=(dx, dy))

GHOSTS = [
    (-21.6, -14.6, 1, 0), (-13.0, -15.0, 0, 1), (15.0, -9.0, 1, 0), (25.2, -9.4, -1, 0),
    (-13.0, -3.0, -1, 0), (15.5, -3.0, 1, 0), (-20.65, 12.4, 0, 1), (-3.4, 4.6, -1, 0),
    (-9.6, 13.2, 0, 1), (12.6, 9.6, -1, 0), (13.8, 18.2, -1, 0), (19.2, 13.6, 0, -1),
]
for x, y, dx, dy in GHOSTS:
    m.spawn('ghost', (x, y, 0), face=(dx, dy))

m.env(
    sky='#07080c',
    fog={'color': '#0a0a0e', 'near': 7, 'far': 42},
    hemi={'sky': '#4a5478', 'ground': '#2a1a14', 'intensity': 0.55},
    exposure=1.05,
    ambience='indoor',
    previewClip=3.6,
)

# eye-level preview views, one or two per room
V = [
    ('foyer', (0, -20.8, 1.6), (0, -6, 2.2)),
    ('foyer_landing', (6.5, -1.2, 4.55), (-3, -15, 2.0)),
    ('parlour', (-10.0, -21.0, 1.6), (-17, -10, 1.0)),
    ('study', (-20.0, -7.0, 1.6), (-27, -17, 1.0)),
    ('dining', (10.2, -7.0, 1.6), (22, -16, 0.9)),
    ('gallery', (-10.0, -3.0, 1.6), (-30, -3, 1.6)),
    ('servants', (10.2, -3.0, 1.6), (25, -1, 1.8)),
    ('library', (-16.2, 1.2, 1.6), (-25, 14, 1.2)),
    ('library_stacks', (-24.35, 20.8, 1.6), (-24.35, 8, 1.2)),
    ('music', (-1.0, 9.0, 1.6), (-11, 3, 1.4)),
    ('nursery', (-1.2, 11.2, 1.6), (-10, 19, 1.0)),
    ('kitchen', (14.8, 1.2, 1.6), (6, 11, 1.2)),
    ('scullery', (15.2, 15.0, 1.6), (3, 20, 1.2)),
    ('conservatory', (17.0, 1.0, 1.6), (25, 14, 2.0)),
    ('birdcage', (28.8, 20.6, 1.6), (22, 10, 1.8)),
]
for name, pos, look in V:
    m.preview(pos, look, name=name)

m.finish()
