"""Thistlewick Farm (id `farm`): an autumn farmstead at dusk turning to night.

Layout (Blender X east, Y north; playable square +-35 m):

    NW orchard ........ back lane ............ NE corn maze (beyond: endless corn)
    (apple trees,       (trough, wagon)        (clearing + scarecrow)
     cider press)    +-------------------+
                     |  BIG RED BARN     |  silo
    W farmhouse      |  (S/N doors, loft)|   barn east path ---- maze west entrances
    (porch, kitchen) +-------------------+
                       barnyard hub: oak + tire swing, well, haystack, wagon     E pumpkin patch
    SW laundry yard,     coop + "The Chicken Run" (penalty cage)                   (scarecrows)
    garden, outhouse                                                             SE windmill + pond
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~ creek (south boundary) with a closed footbridge ~~~~~~~~~~~~~~~~~
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from lib import gh, tex, prefabs as pf  # noqa: E402
import farm_props as fp  # noqa: E402
from farm_props import PI, TAU  # noqa: E402

m = gh.MapBuilder('farm', 'Thistlewick Farm', chunk=14.0, seed=11)
RNG = random.Random(1907)


class Bag:
    pass


# ============================================================================ palette
# pumpkin orange, barn red, straw/ochre, weathered grey wood, sage greens, dusk violet, deep teal
M = Bag()
M.grass = m.mat('grass', image=tex.ground(a='#4a5530', b='#6d6a3a', c='#5d4a2d', seed=8, scale=6), uv=7.0)
M.dirt = m.mat('dirt', image=tex.ground(a='#6b5236', b='#806a4a', c='#4a3826', seed=12, scale=5), uv=4.0)
M.barn_red = m.mat('barn_red', image=tex.boards(base='#8c2e22', dark='#3a130e', boards_n=8, wear=0.2,
                                                weathered='#74453a', seed=7), uv=2.4)
M.barn_in = m.mat('barn_in', image=tex.boards(base='#6e5a44', dark='#2e2419', boards_n=7, wear=0.15,
                                              weathered='#8a7a62', seed=17), uv=2.4)
M.weathered = m.mat('weathered', image=tex.wood_planks(base='#7d7568', dark='#4a453d', light='#a19887', planks=6,
                                                       seed=3), uv=2.0)
M.barn_roof = m.mat('barn_roof', image=tex.shingles(base='#5d5550', seed=9), uv=2.2)
M.barn_roof_top = m.mat('barn_roof_top', image=tex.shingles(base='#5d5550', seed=9), uv=2.2, uv_rot=PI / 2)
M.siding = m.mat('siding', image=tex.boards(base='#cbc3a5', dark='#6e6754', boards_n=10, wear=0.12,
                                            weathered='#a9a189', seed=27), uv=2.5, uv_rot=PI / 2)
M.house_roof = m.mat('house_roof', image=tex.shingles(base='#4b4352', rows=10, seed=19), uv=2.4, uv_rot=PI / 2)
M.stone = m.mat('stone', image=tex.flagstones(stone='#7c796e', grout='#3b3833', seed=4), uv=1.6)
M.hay = m.mat('hay', image=fp.straw_tex(), uv=0.7)
M.corn = m.mat('corn', image=fp.corn_tex(), uv=2.4)
M.wallpaper = m.mat('wallpaper', image=tex.wallpaper(bg='#7c8a68', fg='#95a17e', stripe='#6a785a', seed=2), uv=1.4)
M.gingham = m.mat('gingham', image=fp.gingham_tex(), uv=0.5)
M.hedge = m.mat('hedge', image=tex.noise_tint(base='#3b4a35', amount=0.3, cells=10, seed=14), uv=2.0)
M.quilt = m.mat('quilt', image=tex.fabric(base='#7e8c6c', pattern='border', pattern_col='#c9a24a', seed=10), uv=1.2)
M.awning = m.mat('awning', image=tex.stripes(a='#9a3a2e', b='#e2d6bc', count=4), uv=1.3)

M.wood_dk = m.mat('wood_dk', '#3c2d22')
M.wood_mid = m.mat('wood_mid', '#6c4c33')
M.wood_light = m.mat('wood_light', '#9a7f5c')
M.paint_white = m.mat('paint_white', '#dcd4c0', rough=0.7)
M.trim_green = m.mat('trim_green', '#3d4c3f', rough=0.7)
M.paint_sage = m.mat('paint_sage', '#7f9078', rough=0.7)
M.pumpkin = m.mat('pumpkin', '#d4702a', rough=0.6)
M.stem = m.mat('stem', '#5a5a2e')
M.leaf_orange = m.mat('leaf_orange', '#c4652a')
M.leaf_gold = m.mat('leaf_gold', '#cf9e3e')
M.leaf_red = m.mat('leaf_red', '#963726')
M.leaf_olive = m.mat('leaf_olive', '#7c8048')
M.leaf_sage = m.mat('leaf_sage', '#69785a')
M.pine = m.mat('pine', '#2c4237')
M.bark = m.mat('bark', '#4a3a2e')
M.straw = m.mat('straw', '#cfa95e')
M.burlap = m.mat('burlap', '#a48858')
M.sack_pale = m.mat('sack_pale', '#c8b48a')
M.denim = m.mat('denim', '#4a5a78')
M.cloth_white = m.mat('cloth_white', '#e6dfd0', rough=0.9)
M.cloth_sage = m.mat('cloth_sage', '#8fa07e', rough=0.9)
M.cloth_rose = m.mat('cloth_rose', '#b0604f', rough=0.9)
M.iron = m.mat('iron', '#2a2826', rough=0.6, metal=0.4)
M.tin = m.mat('tin', '#8d9394', rough=0.4, metal=0.7)
M.rust = m.mat('rust', '#7a4630', rough=0.8)
M.rope = m.mat('rope', '#b5a07a')
M.crow = m.mat('crow', '#17171c', rough=0.5)
M.window_glow = m.mat('window_glow', '#ffcf86', emit='#ffb85c', strength=2.5)
M.window_glow_dim = m.mat('window_glow_dim', '#c89a58', emit='#e09848', strength=0.9)
M.window_dark = m.mat('window_dark', '#1c2633', rough=0.2)
M.water = m.mat('water', '#2b4a56', rough=0.08, metal=0.3)
M.altar_glow = m.mat('altar_glow', '#58c8b8', emit='#2fc0b0', strength=1.6)
M.jack_glow = m.mat('jack_glow', '#ffb04a', emit='#ff8a20', strength=5.0)
M.apple = m.mat('apple', '#a8302a', rough=0.5)
M.teal = m.mat('teal', '#3d6b69', rough=0.6)
M.millstone = m.mat('millstone', '#a39d90')
M.brass = m.mat('brass', '#b08a3e', rough=0.35, metal=0.9)
M.corn_leaf = m.mat('corn_leaf', '#b4a060')
M.corn_leaf2 = m.mat('corn_leaf2', '#958a52')
M.grey_wood = m.mat('grey_wood', '#6f685d')
# aliases keep the material count down
M.stone_cap = M.millstone
M.moss = M.cabbage = M.herb = M.leaf_sage
M.soil = M.leather = M.felt = M.cattail = M.sunface = M.wood_dk
M.grass_tuft = M.reed = M.leaf_olive
M.grass_dry = M.sunleaf = M.corn_leaf2
M.ochre = M.corn_husk = M.straw
M.lantern_glass = M.window_glow
M.ember = M.jack_glow
M.rubber = M.crow
M.wax = M.egg = M.clock_face = M.cloth_white
M.screen = M.window_dark
M.corn_stalk = M.sunstalk = M.corn_leaf
M.bronze = M.brass
M.copper = M.rust
M.ribbon = M.apple
M.patch = M.denim
M.wicker = M.burlap
M.cushion = M.cloth_rose
M.canvas = M.sailcloth = M.sack_pale
M.tarp = M.leaf_olive
M.boat = M.teal
M.water_dk = M.water
M.duck_body = M.wood_mid
M.duck_head = M.pine
M.sunpetal = M.leaf_gold
M.plaid = M.gingham
M.beak = M.iron


# ============================================================================ helpers

def G(x, y):
    return m.static(x, y)


def put(fn, pos, rz=0.0, **kw):
    g = m.static(pos[0], pos[1])
    with g.at(pos, rz):
        fn(g, M, **kw)
    return g


def place(fn, ptype, label, pos, rz=0.0, params=None, key=None, **kw):
    """m.place wrapper: explicit params win over prefab defaults; keyed clones inherit the
    source prop's params (MapBuilder.place does not copy params onto clones)."""
    p = m.place(fn, ptype, label, pos, rz, key=key, M=M, **kw)
    src = m.prop_cache.get(key) if key else None
    if src is not None and src is not p:
        for k, v in src.params.items():
            p.params.setdefault(k, v)
    p.params.update(params or {})
    return p


class StaticShim:
    """Lets a prop prefab draw into static geometry (its parts all collapse onto one Geo)."""

    def __init__(self, g):
        self.g = self.body = g
        self.params = {}

    def part(self, name, pos=(0, 0, 0), rz=0.0, rx=0.0, ry=0.0, parent=None):
        return _ShimPart(self.g)

    def geo(self, name, pos=(0, 0, 0), **k):
        return self.g

    def light(self, *a, **k):
        pass

    def flame(self, *a, **k):
        pass


class _ShimPart:
    def __init__(self, g):
        self.geo = g


def put_prop_static(fn, pos, rz=0.0, **kw):
    g = m.static(pos[0], pos[1])
    with g.at(pos, rz):
        fn(StaticShim(g), M, **kw)


def rot(x, y, a):
    c, s = math.cos(a), math.sin(a)
    return x * c - y * s, x * s + y * c


def round_collider(cx, cy, r, z0, z1):
    m.collider((cx - r, cy - r * 0.7, z0), (cx + r, cy + r * 0.7, z1))
    m.collider((cx - r * 0.7, cy - r, z0), (cx + r * 0.7, cy + r, z1))


def path(pts, width=2.4, seed=0, mat=None):
    g = G(*pts[0])
    g.add(fp.prim_ribbon(pts, width, z=0.012 + (seed % 5) * 0.0004, seed=seed), mat or M.dirt)


def patch(cx, cy, rx, ry, seed=0, mat=None, z=0.01):
    G(cx, cy).add(fp.prim_poly(fp.blob_poly(cx, cy, rx, ry, n=18, seed=seed, jitter=0.16), z), mat or M.dirt)


def tufts(cx, cy, radius, count, seed=0):
    rng = random.Random(seed)
    g = G(cx, cy)
    for i in range(count):
        a = rng.uniform(0, TAU)
        d = radius * math.sqrt(rng.random())
        fp.grass_tuft(g, M, (cx + math.cos(a) * d, cy + math.sin(a) * d, 0), seed=seed * 101 + i,
                      h=rng.uniform(0.25, 0.45))


def tufts_line(a, b, count, seed=0, jitter=0.4):
    rng = random.Random(seed)
    g = G(*a)
    for i in range(count):
        t = rng.random()
        x = a[0] + (b[0] - a[0]) * t + rng.uniform(-jitter, jitter)
        y = a[1] + (b[1] - a[1]) * t + rng.uniform(-jitter, jitter)
        fp.grass_tuft(g, M, (x, y, 0), seed=seed * 97 + i, h=rng.uniform(0.25, 0.5))


def leaves(cx, cy, radius, count, seed=0, mats=None):
    fp.leaf_scatter(G(cx, cy), M, cx, cy, radius, count, seed=seed, mats=mats)


def window(cx, cy, rz, w, sill, top, lit=True, inner=False, curtains=True, z0=0.0):
    """Static window in a wall opening. (cx, cy) = opening centre on the wall line; rz turns the
    window so its outside faces local -Y (0: south wall, pi: north, pi/2: east, -pi/2: west)."""
    g = G(cx, cy)
    h = top - sill
    with g.at((cx, cy, z0 + sill), rz):
        if inner:
            g.box((0, -0.03, h / 2), (w, 0.02, h), M.window_glow_dim)
            g.box((0, -0.01, h / 2), (w, 0.02, h), M.window_dark)
        else:
            g.box((0, -0.02, h / 2), (w, 0.03, h), M.window_glow if lit else M.window_dark)
            if lit and curtains:
                for sx in (-1, 1):
                    g.box((sx * (w / 2 - 0.12), -0.04, h / 2 + 0.05), (0.2, 0.01, h - 0.12),
                          M.cloth_rose if (int(cx * 7 + cy * 3) % 2) else M.cloth_sage)
        for sx in (-1, 1):
            g.box((sx * (w / 2 - 0.035), 0, h / 2), (0.07, 0.34, h), M.paint_white)
        g.box((0, 0, h - 0.035), (w, 0.34, 0.07), M.paint_white)
        g.box((0, -0.06, -0.02), (w + 0.16, 0.44, 0.06), M.paint_white)
        g.box((0, -0.05, h / 2), (0.04, 0.05, h), M.paint_white)
        g.box((0, -0.05, h * 0.55), (w, 0.05, 0.04), M.paint_white)
        g.box((0, -0.17, h + 0.06), (w + 0.2, 0.06, 0.1), M.paint_white)
    hx, hy = rot(w / 2, 0.16, rz)
    ex, ey = abs(hx), abs(hy)
    m.collider((cx - ex, cy - ey, z0 + sill), (cx + ex, cy + ey, z0 + top))


# ============================================================================ ground & boundary
B = 35.0
m.collider((-36.0, -36.0, -0.6), (36.0, 36.0, 0.0))                 # walkable ground
PH = 14.0
m.collider((-37.0, 35.0, -1.0), (37.0, 36.6, PH))                   # perimeter (invisible, 14 m)
m.collider((-37.0, -36.6, -1.0), (37.0, -35.0, PH))
m.collider((-36.6, -37.0, -1.0), (-35.0, 37.0, PH))
m.collider((35.0, -37.0, -1.0), (36.6, 37.0, PH))

# visual ground: north part, far south bank, and the creek between
m.box((0, 32.0, -0.3), (220, 136, 0.6), M.grass, col=False)          # y -36 .. 100
m.box((0, -70.3, -0.3), (220, 59.4, 0.6), M.grass, col=False)        # y -100 .. -40.6
m.box((0, -38.3, -0.75), (220, 4.6, 0.3), M.dirt, col=False)         # creek bed
m.box((0, -38.3, -0.37), (220, 4.2, 0.04), M.water, col=False)       # creek water
gS = G(0, -36)
for y_edge, sgn in ((-36.0, -1), (-40.6, 1)):                          # sloping banks
    ang = math.atan2(0.5, 1.0)
    gS.box((0, y_edge + sgn * 0.45, -0.24), (220, 1.15, 0.12), M.dirt, rx=sgn * ang)
for i in range(70):                                                    # bank stones
    x = RNG.uniform(-60, 60)
    y = RNG.choice((-36.3, -40.3)) + RNG.uniform(-0.3, 0.3)
    gS.blob((x, y, -0.25), RNG.uniform(0.15, 0.45), M.millstone, seed=i, jitter=0.3, subdiv=0, s=(1.3, 1, 0.6))

# north boundary hedgerow (west of the corn) + tree line behind
put(fp.hedge, (-10.2, 35.85, 0), length=49.6, h=2.6, d=1.4, seed=1)
# west boundary: dry-stone wall + hedge + trees
put(fp.stone_wall, (-35.35, 0, 0), rz=PI / 2, length=70.6, seed=2, col=False)
put(fp.hedge, (-36.9, 0, 0), rz=PI / 2, length=72, h=2.8, d=1.6, seed=3, col=False)
# east boundary south of the corn: split-rail fence, pasture beyond
put(fp.rail_fence, (35.25, -35.0, 0), rz=PI / 2, length=44.5, seed=4, col=False)


def tree_band(x0, x1, y0, y1, n, seed, pine_frac=0.4, hmin=6.5, hmax=11):
    rng = random.Random(seed)
    for i in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        style = 'pine' if rng.random() < pine_frac else 'round'
        h = rng.uniform(hmin, hmax)
        lv = [M.pine] if style == 'pine' else rng.choice(([M.leaf_orange, M.leaf_gold], [M.leaf_olive, M.leaf_gold],
                                                          [M.leaf_red, M.leaf_orange], [M.leaf_sage, M.leaf_olive]))
        g = G(x, y)
        with g.at((x, y, 0), rng.uniform(0, TAU)):
            fp.tree_static(g, M, seed=seed * 1000 + i, h=h, crown=h * rng.uniform(0.3, 0.4), style=style, leaves=lv,
                           subdiv=0)


tree_band(-48, 14, 38.5, 52, 24, 11)
tree_band(-52, -39.5, -45, 50, 20, 12, pine_frac=0.5)
tree_band(-50, 30, -56, -43, 20, 13, pine_frac=0.4)
tree_band(44, 60, -50, 10, 12, 14, pine_frac=0.5)
tree_band(30, 58, -58, -44, 8, 15)
# pasture east: round bales and a lone tree
for i, (x, y) in enumerate(((40.5, -6.0), (42.0, -2.5), (46.0, -14.0), (41.0, -24.0))):
    g = G(x, y)
    with g.at((x, y, 0.75), RNG.uniform(0, 3), rx=PI / 2):
        g.cyl((0, 0, -0.7), 0.75, 1.4, M.hay, n=12)
        g.cyl((0, 0, -0.71), 0.6, 1.42, M.straw, n=12, caps=True)

# the corn field runs on past the north and east boundaries
gc = G(30, 40)
fp.corn_block(gc, M, 14.0, 35.75, 52.0, 44.0, faces='', seed=91, col=False, top_spacing=1.0)
fp.corn_block(gc, M, 35.75, 12.6, 46.0, 35.75, faces='', seed=92, col=False, top_spacing=1.0)
fp.corn_block(G(30, 8), M, 36.4, -2.0, 44.0, 9.4, faces='W', seed=93, col=False, top_spacing=1.0)
gtr = G(36, 11)                                                            # the east track's gate, chained shut
for yy in (9.7, 12.3):
    gtr.box((35.3, yy, 0.7), (0.18, 0.18, 1.4), M.wood_dk, bevel=0.015)
for i in range(5):
    gtr.box((35.3, 11.0, 0.25 + i * 0.24), (0.06, 2.5, 0.1), M.grey_wood)
gtr.box((35.3, 11.0, 0.7), (0.06, 2.7, 0.1), M.grey_wood, rx=0.38)

# ============================================================================ paths (packed dirt)
path([(-3.0, -34.6), (-2.4, -30.0), (-0.5, -22.0), (0.6, -14.0), (1.0, -8.0), (0.0, 0.0), (0.0, 11.0)], 2.6, 1)
path([(0.0, 11.0), (0.0, 28.0)], 3.4, 2)                                  # barn aisle
path([(0.0, 28.0), (0.0, 31.0), (-6.0, 31.5), (-13.0, 31.0), (-20.0, 31.8)], 2.4, 3)
path([(0.0, 31.0), (8.0, 31.2), (12.8, 30.6), (15.5, 29.0)], 2.4, 4)
path([(-9.5, 7.5), (-10.0, 18.0), (-10.0, 31.0)], 2.2, 5)                 # west of the barn
path([(6.0, 9.0), (11.0, 12.0), (11.2, 20.3), (15.0, 20.3)], 2.2, 6)      # east of the barn
path([(11.2, 20.3), (12.4, 28.0)], 2.0, 7)
path([(0.0, 0.0), (-9.0, -0.6), (-15.0, -1.5), (-18.6, -1.6)], 2.4, 8)    # to the porch steps
path([(-20.2, 4.8), (-19.0, 9.0), (-19.0, 13.5), (-21.0, 20.0)], 2.0, 9)  # porch north to orchard
path([(-24.4, -5.6), (-24.0, -11.0), (-24.5, -22.0), (-29.0, -27.0), (-30.4, -29.0)], 2.0, 10)  # laundry/outhouse
path([(-24.0, -12.0), (-14.0, -12.5), (-5.0, -14.5), (0.6, -14.0)], 2.0, 11)
path([(0.0, 0.0), (8.0, 1.0), (15.6, 1.2), (24.0, 0.2), (31.0, -2.0)], 2.4, 12)  # east to the patch
path([(6.0, 8.0), (14.0, 11.0), (25.0, 11.2), (37.0, 10.8)], 2.6, 13)     # east track
path([(24.0, 0.2), (24.5, -8.0), (24.8, -13.0), (25.5, -19.5)], 2.0, 14) # patch -> windmill
path([(25.5, -19.5), (16.0, -22.0), (6.0, -26.5), (-2.4, -30.0)], 2.2, 15)
path([(-2.4, -30.0), (-12.0, -31.5), (-22.0, -32.0), (-29.0, -28.0)], 2.0, 16)
patch(0.5, 3.0, 9.5, 6.5, seed=1)                                       # barnyard
patch(-3.0, -5.0, 5.0, 3.0, seed=2)
patch(1.0, 30.6, 7.0, 2.6, seed=3)
patch(-30.0, -29.0, 3.0, 2.2, seed=4)
patch(26.0, -21.5, 5.0, 3.5, seed=5)


# ============================================================================ BARN
BX0, BX1, BY0, BY1, BWH = -7.0, 7.0, 11.0, 28.0, 5.2
DZ = BWH - 4.6
DOOR_W, DOOR_H = 4.6, 3.9
LOFT_Z = 2.7
POSTS_Y = (14.5, 18.0, 21.5, 25.0)
STX0, STX1 = -6.6, -5.17          # loft stairs (east edge snapped to the nav grid)


def build_barn():
    low = (0.45, M.stone)
    m.wall((BX0, BY0), (BX1, BY0), M.barn_red, h=BWH, openings=[(7.0, DOOR_W, DOOR_H, 0)], mat_back=M.barn_in, lower=low)
    m.wall((BX0, BY1), (BX1, BY1), M.barn_in, h=BWH, openings=[(7.0, DOOR_W, DOOR_H, 0)], mat_back=M.barn_red, lower=low)
    m.wall((BX0, BY0), (BX0, BY1), M.barn_red, h=BWH, openings=[(5.0, 1.0, 2.3, 1.2), (11.5, 1.0, 2.3, 1.2)],
           mat_back=M.barn_in, lower=low)
    m.wall((BX1, BY0), (BX1, BY1), M.barn_in, h=BWH, openings=[(5.6, 1.6, 2.4, 0), (11.5, 1.0, 2.6, 1.5)],
           mat_back=M.barn_red, lower=low)
    for wy in (16.0, 22.5):
        window(BX0, wy, -PI / 2, 1.0, 1.2, 2.3, lit=False, inner=True)
    window(BX1, 22.5, PI / 2, 1.0, 1.5, 2.6, lit=False, inner=True)
    g = G(0, 19)
    # gables (pentagon above the eaves), outer red / inner planks
    poly = [(-7.15, BWH), (7.15, BWH), (5.0, 7.6 + DZ), (0.0, 9.2 + DZ), (-5.0, 7.6 + DZ)]
    g.prism((0, BY0 + 0.15, 0), poly, 0.15, M.barn_in, rx=PI / 2)
    g.prism((0, BY0, 0), poly, 0.15, M.barn_red, rx=PI / 2)
    g.prism((0, BY1, 0), poly, 0.15, M.barn_in, rx=PI / 2)
    g.prism((0, BY1 + 0.15, 0), poly, 0.15, M.barn_red, rx=PI / 2)
    # roof: shingle slab over a plank lining, four slopes
    L = BY1 - BY0 + 1.1
    yc = (BY0 + BY1) / 2
    E, K, R = (7.412, 4.234 + DZ), (5.0, 7.6 + DZ), (0.0, 9.2 + DZ)

    def off(a, b, d):
        dx, dz = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dz)
        nx, nz = dz / ln, -dx / ln
        if nz < 0:
            nx, nz = -nx, -nz
        return (a[0] + nx * d, a[1] + nz * d), (b[0] + nx * d, b[1] + nz * d)

    for sx in (-1, 1):
        e, k = (sx * E[0], E[1]), (sx * K[0], K[1])
        for a, b, mat, ext in ((e, k, M.barn_roof, 0.12), (k, R, M.barn_roof_top, 0.2)):
            fp.slab(g, a, b, L, 0.04, M.barn_in, y=yc, extend=ext)
            a2, b2 = off(a, b, 0.04)
            fp.slab(g, a2, b2, L, 0.16, mat, y=yc, extend=ext)
            # rake trim on both gable ends
            ai, bi = off(a, b, -0.22)
            for yy in (BY0 - 0.53, BY1 + 0.53):
                fp.slab(g, ai, bi, 0.06, 0.22, M.paint_white, y=yy, extend=ext)
            # rafters
            ar, br = off(a, b, -0.16)
            for yy in (12.6, 14.5, 16.25, 18.0, 19.75, 21.5, 23.25, 25.0, 26.6):
                fp.slab(g, ar, br, 0.1, 0.16, M.wood_dk, y=yy)
        g.box((sx * 7.42, yc, 4.17 + DZ), (0.08, L, 0.24), M.paint_white)       # eave fascia
        for yy in (BY0, BY1):
            g.box((sx * 7.0, yy, (BWH + 0.45) / 2), (0.38, 0.38, BWH - 0.45), M.paint_white)  # corner boards
    g.box((0, yc, 9.42 + DZ), (0.34, L + 0.05, 0.1), M.iron)                   # ridge cap
    for yy in POSTS_Y:                                                           # posts and tie beams
        for sx in (-1, 1):
            m.box((sx * 2.3, yy, BWH / 2), (0.24, 0.24, BWH), M.wood_dk, bevel=0.02)
        g.box((0, yy, BWH - 0.15), (13.7, 0.22, 0.22), M.wood_dk)
        g.box((0, yy, 7.45 + DZ), (9.6, 0.16, 0.16), M.wood_dk)
    for yy in (BY0 + 0.25, BY1 - 0.25):
        g.box((0, yy, BWH - 0.15), (13.7, 0.2, 0.2), M.wood_dk)
    # door trim + headers on both gable ends
    for yy, s in ((BY0 - 0.17, -1), (BY1 + 0.17, 1)):
        for sx in (-1, 1):
            g.box((sx * (DOOR_W / 2 + 0.1), yy, DOOR_H / 2), (0.22, 0.06, DOOR_H), M.paint_white)
        g.box((0, yy, DOOR_H + 0.12), (DOOR_W + 0.44, 0.06, 0.24), M.paint_white)
    # hayloft opening + door on the south gable, hay hood with pulley at the peak
    g.box((0, BY0 - 0.16, 5.8 + DZ), (1.5, 0.02, 1.6), M.wood_dk)
    for sx in (-1, 1):
        g.box((sx * 0.84, BY0 - 0.17, 5.8 + DZ), (0.16, 0.06, 1.8), M.paint_white)
    g.box((0, BY0 - 0.17, 6.68 + DZ), (1.84, 0.06, 0.16), M.paint_white)
    g.box((0, BY0 - 0.17, 4.92 + DZ), (1.84, 0.06, 0.16), M.paint_white)
    for sx in (-1, 1):
        fp.slab(g, (sx * 1.45, 8.74 + DZ), (0, 9.2 + DZ), 1.6, 0.1, M.barn_roof_top, y=BY0 - 0.95, extend=0.1)
    g.prism((0, BY0 - 1.74, 0), [(-1.45, 8.74 + DZ), (1.45, 8.74 + DZ), (0, 9.2 + DZ)], 0.06, M.paint_white, rx=PI / 2)
    g.box((0, BY0 - 0.85, 8.86 + DZ), (0.14, 1.9, 0.16), M.wood_dk)
    # cupola on the ridge
    with g.at((0, yc, DZ)):
        g.box((0, 0, 9.5), (1.3, 1.3, 1.2), M.barn_red, bevel=0.02)
        for a in range(4):
            with g.at((0, 0, 0), a * PI / 2):
                for i in range(4):
                    g.box((0, -0.66, 9.45 + i * 0.16), (0.8, 0.04, 0.06), M.paint_white, rx=0.6)
                g.box((0, -0.66, 9.68), (0.9, 0.02, 0.75), M.wood_dk)
        for sx in (-1, 1):
            for sy in (-1, 1):
                g.box((sx * 0.62, sy * 0.62, 9.5), (0.1, 0.1, 1.2), M.paint_white)
        g.cyl((0, 0, 10.1), 1.05, 0.62, M.barn_roof, n=4, r2=0.06, rz=PI / 4, smooth=False)
        g.cyl((0, 0, 10.7), 0.06, 0.1, M.iron, n=6)
    # interior: aisle floor, straw in the stalls
    g.box((0, yc, 0.004), (4.3, BY1 - BY0 - 0.3, 0.008), M.dirt)
    for (sx0, sx1, sy0, sy1) in ((-6.85, -2.42, 11.15, 25.0), (2.42, 6.85, 18.0, 25.0)):
        g.box(((sx0 + sx1) / 2, (sy0 + sy1) / 2, 0.012), (sx1 - sx0, sy1 - sy0, 0.01), M.hay)
    # hayloft (west), joists, stairs, railing
    # (edges of raised floors are snapped to the 0.5 m nav grid so bots/validator can climb them)
    SW0 = 22.83                                                                 # stairwell south edge
    m.box((-4.635, (BY0 + 0.15 + SW0) / 2, LOFT_Z - 0.1), (4.67, SW0 - BY0 - 0.15, 0.2), M.weathered)
    m.box(((STX1 - 2.3) / 2, (SW0 + 25.0) / 2, LOFT_Z - 0.1), (-2.3 - STX1, 25.0 - SW0, 0.2), M.weathered)
    for yy in (12.0, 13.2, 15.6, 16.8, 19.2, 20.4, 21.8):
        g.box((-4.6, yy, LOFT_Z - 0.26), (4.5, 0.1, 0.14), M.wood_dk)
    g.box(((STX1 - 2.3) / 2, 23.9, LOFT_Z - 0.26), (-2.3 - STX1, 0.1, 0.14), M.wood_dk)
    for k in range(9):                                                          # 0.5 m treads, 0.3 m risers
        s0 = 26.83 - 0.5 * k
        top = 0.3 * (k + 1)
        m.box(((STX0 + STX1) / 2, s0 + 0.25, top / 2), (STX1 - STX0, 0.5, top), M.weathered)
        g.box(((STX0 + STX1) / 2, s0 + 0.48, top + 0.005), (STX1 - STX0 + 0.04, 0.06, 0.012), M.wood_dk)
    g.box((STX1 + 0.04, 25.08, 2.15), (0.06, 6.0, 0.08), M.wood_dk, rx=0.58)
    for yy in (27.2, 25.3, 23.4):
        g.box((STX1 + 0.04, yy, (0.3 * (1 + (26.83 - yy) / 0.5) + 2.95) / 2 + 0.3), (0.07, 0.07, 1.0), M.wood_dk)
    for (ya, yb) in ((BY0 + 0.15, 14.38), (18.12, 25.0)):
        yl = yb - ya
        g.box((-2.3, (ya + yb) / 2, LOFT_Z + 0.95), (0.08, yl, 0.1), M.wood_mid)
        g.box((-2.3, (ya + yb) / 2, LOFT_Z + 0.45), (0.06, yl, 0.08), M.wood_mid)
        n = int(yl / 0.9)
        for i in range(n + 1):
            g.box((-2.3, ya + yl * i / max(1, n), LOFT_Z + 0.5), (0.07, 0.07, 1.0), M.wood_mid)
        m.collider((-2.38, ya, LOFT_Z), (-2.22, yb, LOFT_Z + 1.05))
    g.box(((STX1 - 2.3) / 2, 25.0, LOFT_Z + 0.95), (-2.3 - STX1, 0.08, 0.1), M.wood_mid)
    g.box(((STX1 - 2.3) / 2, 25.0, LOFT_Z + 0.45), (-2.3 - STX1, 0.06, 0.08), M.wood_mid)
    m.collider((STX1, 24.92, LOFT_Z), (-2.3, 25.08, LOFT_Z + 1.05))
    # west side under the loft: the hay mow, bales stacked to the joists (one floor per nav cell,
    # so the loft above is the walkable level there)
    HM = LOFT_Z - 0.2
    m.collider((BX0 + 0.15, BY0 + 0.15, 0), (-2.42, SW0, HM))
    m.collider((STX1, SW0, 0), (-2.42, 25.0, HM))
    g.box((-4.6, (BY0 + 0.15 + 25.0) / 2, HM / 2), (4.4, 25.0 - BY0 - 0.2, HM), M.hay)
    rngb = random.Random(3)
    for k in range(5):                                      # bale courses facing the aisle
        z = 0.22 + k * 0.46
        y = BY0 + 0.15 + (k % 2) * 0.5
        while y < 24.9:
            ln = min(1.0, 24.95 - y)
            g.box((-2.43 + rngb.uniform(-0.04, 0.05), y + ln / 2, z), (0.06, ln - 0.06, 0.4), M.hay)
            y += 1.0
        g.box((-2.38, 18.0, z + 0.22), (0.02, 13.8, 0.03), M.wood_dk)
    for k in range(3):
        z = 0.22 + k * 0.46
        g.box(((STX1 - 2.42) / 2, 25.03, z), (-2.42 - STX1 - 0.1, 0.06, 0.4), M.hay)
    for (y, z) in ((13.2, 2.45), (16.4, 2.42), (20.9, 2.47)):  # loose straw spilling over the edge
        g.blob((-2.35, y, z), 0.35, M.hay, seed=int(y), jitter=0.3, subdiv=0, s=(0.6, 1.8, 0.4))
    # east stalls
    sh = 1.4
    for yy in (18.0, 21.5, 25.0):
        m.box((4.64, yy, sh / 2), (4.42, 0.1, sh), M.barn_in)
    for ya, yb in ((18.12, 18.95), (20.55, 21.38), (21.62, 22.45), (24.05, 24.88)):
        m.box((2.3, (ya + yb) / 2, sh / 2), (0.1, yb - ya, sh), M.barn_in)
    # ceiling collider (interior roof)
    m.collider((BX0 - 0.15, BY0 - 0.15, BWH), (BX1 + 0.15, BY1 + 0.15, BWH + 0.4))
    m.collider((BX0 - 0.6, BY0 - 0.6, BWH + 0.4), (BX1 + 0.6, BY1 + 0.6, 9.4 + DZ))


build_barn()

# barn doors (hinged, flung open against the yard) and the rest of the barn's props
for (hx, ext, hy, rz) in ((-2.3, 1, BY0 - 0.205, 0.0), (2.3, -1, BY0 - 0.205, 0.0),
                          (2.3, 1, BY1 + 0.205, PI), (-2.3, -1, BY1 + 0.205, PI)):
    place(fp.barn_door, 'hinge', 'Barn Door', (hx, hy, 0), rz, key=f'barn_door_{ext}', ext=ext, rest=1.72)
place(fp.plank_door, 'hinge', 'Barn Side Door', (BX1 + 0.2, 15.8, 0), PI / 2, w=1.6, h=2.4, ext=1, rest=1.5,
      mat=M.barn_red)
place(fp.hayloft_door, 'hinge', 'Hayloft Door', (-0.75, BY0 - 0.215, 5.0 + DZ), 0.0, rest=0.55)
place(fp.hay_hook, 'swing', 'Hay Hook', (0, BY0 - 1.2, 8.78 + DZ), drop=2.3)
place(fp.weathervane, 'spin', 'Rooster Weathervane', (0, 19.5, 10.78 + DZ))
for yy, x in ((14.5, 0.0), (21.5, 0.0), (18.0, 4.6)):
    place(fp.hanging_lantern, 'swing', 'Barn Lantern', (x, yy, BWH - 0.26), key='barn_lantern', drop=1.2)
place(fp.stall_gate, 'hinge', 'Stall Gate', (2.3, 20.55, 0), -PI / 2, ext=1, rest=1.3, key='stall_gate')
place(fp.stall_gate, 'hinge', 'Stall Gate', (2.3, 24.05, 0), -PI / 2, ext=1, rest=1.3, key='stall_gate')
place(fp.horse_collar, 'swing', 'Horse Collar', (4.4, BY1 - 0.27, 2.05))
place(fp.hay_bale, 'jolt', 'Hay Bale', (-5.2, 13.4, LOFT_Z), 0.2, key='bale')
place(fp.hay_bale, 'jolt', 'Hay Bale', (-3.3, 14.2, LOFT_Z), 1.4, key='bale')
place(fp.hay_bale, 'jolt', 'Hay Bale', (1.75, 26.5, 0), 1.45, key='bale')
place(fp.feed_sacks, 'jolt', 'Feed Sacks', (3.5, 27.25, 0), 0.1)
put_prop_static(fp.milk_can, (5.9, 26.6, 0), 0.4)
fp.crate_geo(G(6, 19), M, 0.6, (6.2, 18.9, 0), 0.2)
m.collider((5.85, 18.6, 0), (6.55, 19.2, 0.6))
gb = G(0, 19)
put(fp.tractor, (4.6, 14.0, 0), 0.06)
# loft hay stacks, stall clutter, tools
for i, (x, y, z, r) in enumerate(((-6.2, 12.1, 0, 0.1), (-6.2, 12.1, 0.44, -0.05), (-6.1, 13.2, 0, 0.05),
                                  (-6.25, 16.0, 0, PI / 2), (-6.25, 17.0, 0, PI / 2), (-6.25, 16.5, 0.44, PI / 2),
                                  (-6.0, 20.85, 0, 0.0), (-6.0, 21.85, 0, 0.1), (-6.1, 21.35, 0.44, 0.05),
                                  (-6.0, 21.35, 0.88, 1.5), (-4.0, 24.4, 0, 0.0))):
    fp.hay_bale_geo(gb, M, (x, y, LOFT_Z + z), r)
m.collider((-6.85, 11.6, LOFT_Z), (-5.6, 13.7, LOFT_Z + 0.9))
m.collider((-6.85, 15.3, LOFT_Z), (-5.7, 17.6, LOFT_Z + 0.9))
m.collider((-6.85, 20.4, LOFT_Z), (-5.4, 22.3, LOFT_Z + 1.3))
for (x, y, r) in ((5.8, 23.0, 0.0), (6.0, 24.1, 0.1), (5.4, 19.4, 1.5)):
    fp.hay_bale_geo(gb, M, (x, y, 0), r)
for (x, y) in ((5.8, 23.5), (5.4, 19.4)):
    m.collider((x - 0.6, y - 0.6, 0), (x + 0.6, y + 0.6, 0.45))
with gb.at((-4.6, 27.7, 0), 0.0):
    fp.tool_lean(gb, M, 'pitchfork', 0.22)
with gb.at((-4.1, 27.7, 0), 0.1):
    fp.tool_lean(gb, M, 'rake', 0.2)
with gb.at((6.7, 12.0, 0), -PI / 2):
    fp.tool_lean(gb, M, 'shovel', 0.2)
gb.box((6.4, 26.6, 0.9), (0.6, 0.6, 0.05), M.wood_mid)      # tack shelf + saddle on its rack
gb.box((4.64, 21.5, 1.48), (0.5, 0.6, 0.12), M.wood_dk, bevel=0.03)
gb.sphere((4.64, 21.5, 1.6), 0.28, M.wood_dk, n=8, s=(1.0, 1.5, 0.45))
fp.bucket_geo(gb, M, (3.0, 26.9, 0), 0.15, 0.3, water=True)
fp.bucket_geo(gb, M, (-1.9, 12.3, 0), 0.15, 0.3)
fp.sack_geo(gb, M, (1.9, 11.9, 0), 0.8)
for i in range(6):
    x, y = RNG.uniform(-1.9, 1.9), RNG.uniform(11.5, 27.5)
    gb.box((x, y, 0.016), (RNG.uniform(0.3, 0.8), RNG.uniform(0.2, 0.5), 0.01), M.hay, rz=RNG.uniform(0, 3))

# silo (fieldstone, domed) hugging the barn's NE corner
SILO = (9.45, 25.0)
gs = G(*SILO)
gs.cyl((SILO[0], SILO[1], 0), 2.3, 12.4, M.stone, n=18, smooth=True)
for z in (2.0, 4.6, 7.2, 9.8):
    gs.torus((SILO[0], SILO[1], z), 2.31, 0.045, M.iron, n=24, m=4)
gs.lathe((SILO[0], SILO[1], 12.4), [(2.42, 0), (2.3, 0.6), (1.8, 1.4), (1.0, 2.0), (0.2, 2.25)], M.tin, n=18)
gs.cyl((SILO[0], SILO[1], 14.6), 0.2, 0.4, M.tin, n=8)
with gs.at((SILO[0] + 2.35, SILO[1] - 0.6, 0)):
    for sy in (-1, 1):
        gs.box((0.12, sy * 0.25, 6.0), (0.05, 0.05, 12.0), M.iron)
    for z in range(1, 23):
        gs.cyl((0.12, -0.25, z * 0.5), 0.015, 0.5, M.iron, n=4, rx=-PI / 2)
gs.box((SILO[0] - 0.4, SILO[1] - 2.27, 11.0), (0.9, 0.08, 1.2), M.wood_dk)
round_collider(SILO[0], SILO[1], 2.3, 0, 12.4)

# ============================================================================ FARMHOUSE
HX0, HX1, HY0, HY1, HWH = -31.0, -22.0, -5.0, 4.0, 6.2
KZ = 0.4           # house / porch floor height
PORCH_PX = -18.85  # porch posts (deck edge -18.67 is snapped to the nav grid)
KCEIL = 3.2


def build_house():
    # exterior walls (two storeys)
    m.wall((HX0, HY0), (HX1, HY0), M.siding, h=HWH, lower=(0.4, M.stone), openings=[
        (2.0, 1.0, 2.75, 1.35), (5.8, 1.0, 2.7, 1.35), (7.7, 1.4, 2.75, 0),
        (2.0, 1.0, 5.3, 3.9), (5.8, 1.0, 5.3, 3.9)])
    m.wall((HX0, HY1), (HX1, HY1), M.siding, h=HWH, lower=(0.4, M.stone), openings=[
        (2.5, 1.0, 2.75, 1.35), (6.5, 1.0, 2.75, 1.35), (2.5, 1.0, 5.3, 3.9), (6.5, 1.0, 5.3, 3.9)])
    m.wall((HX0, HY0), (HX0, HY1), M.siding, h=HWH, lower=(0.4, M.stone), openings=[
        (3.0, 1.0, 2.75, 1.35), (6.5, 1.0, 2.75, 1.35), (3.0, 1.0, 5.3, 3.9), (6.5, 1.0, 5.3, 3.9)])
    m.wall((HX1, HY0), (HX1, HY1), M.siding, h=HWH, lower=(0.4, M.stone), openings=[
        (1.1, 1.0, 2.7, 1.35), (3.4, 1.4, 2.75, 0), (6.0, 1.0, 2.75, 1.35), (7.9, 1.0, 2.75, 1.35),
        (1.6, 1.0, 5.3, 3.9), (4.5, 1.0, 5.3, 3.9), (7.4, 1.0, 5.3, 3.9)])
    # door thresholds at floor height (door openings use sill=0 so MapBuilder.wall doesn't seal them as windows)
    m.box((HX1, -1.6, KZ / 2), (0.3, 1.4, KZ), M.weathered)
    m.box((-23.3, HY0, KZ / 2), (1.4, 0.3, KZ), M.weathered)
    # windows: kitchen ones glow outside / show the night inside; the rest are lit rooms with curtains
    window(HX0 + 5.8, HY0, 0.0, 1.0, 1.35, 2.7, inner=True)
    window(HX1, HY0 + 1.1, PI / 2, 1.0, 1.35, 2.7, inner=True)
    window(HX0 + 2.0, HY0, 0.0, 1.0, 1.35, 2.75, lit=False)
    for (x, y, rz) in ((HX0 + 2.5, HY1, PI), (HX0 + 6.5, HY1, PI), (HX0, HY0 + 3.0, -PI / 2), (HX0, HY0 + 6.5, -PI / 2),
                       (HX1, HY0 + 6.0, PI / 2), (HX1, HY0 + 7.9, PI / 2)):
        window(x, y, rz, 1.0, 1.35, 2.75, lit=(x, y) != (HX0, HY0 + 3.0))
    for (x, y, rz, lit) in ((HX0 + 2.0, HY0, 0.0, False), (HX0 + 5.8, HY0, 0.0, True), (HX0 + 2.5, HY1, PI, False),
                            (HX0 + 6.5, HY1, PI, True), (HX0, HY0 + 3.0, -PI / 2, False), (HX0, HY0 + 6.5, -PI / 2, False),
                            (HX1, HY0 + 1.6, PI / 2, False), (HX1, HY0 + 4.5, PI / 2, True), (HX1, HY0 + 7.4, PI / 2, False)):
        window(x, y, rz, 1.0, 3.9, 5.3, lit=lit)
    g = G(-26, 0)
    # corner boards, storey band, foundation
    for (x, y) in ((HX0, HY0), (HX1, HY0), (HX0, HY1), (HX1, HY1)):
        g.box((x, y, HWH / 2 + 0.2), (0.4, 0.4, HWH - 0.4), M.paint_white)
    for (a, b, horiz) in (((HX0, HY0), (HX1, HY0), True), ((HX0, HY1), (HX1, HY1), True),
                          ((HX0, HY0), (HX0, HY1), False), ((HX1, HY0), (HX1, HY1), False)):
        if horiz:
            g.box(((a[0] + b[0]) / 2, a[1], 3.55), (b[0] - a[0] + 0.4, 0.38, 0.14), M.paint_white)
        else:
            g.box((a[0], (a[1] + b[1]) / 2, 3.55), (0.38, b[1] - a[1] + 0.4, 0.14), M.paint_white)
    # gable roof, ridge N-S
    yc, L = (HY0 + HY1) / 2, HY1 - HY0 + 1.0
    for sx in (-1, 1):
        a = (-26.5 + sx * 5.05, 5.86)
        b = (-26.5, 9.2)
        fp.slab(g, a, b, L, 0.18, M.house_roof, y=yc, extend=0.25)
        g.box((-26.5 + sx * 5.0, yc, 5.83), (0.08, L, 0.22), M.paint_white)
    g.box((-26.5, yc, 9.4), (0.3, L + 0.04, 0.1), M.iron)
    tri = [(HX0 - 0.15, HWH), (HX1 + 0.15, HWH), (-26.5, 9.15)]
    g.prism((0, HY0 + 0.15, 0), [(x, z) for x, z in tri], 0.3, M.siding, rx=PI / 2)
    g.prism((0, HY1 + 0.15, 0), [(x, z) for x, z in tri], 0.3, M.siding, rx=PI / 2)
    for yy in (HY0 - 0.17, HY1 + 0.17):
        window(-26.5, yy, 0.0 if yy < 0 else PI, 0.7, 6.6, 7.6, lit=(yy > 0), curtains=False)
    # stone chimney through the roof above the kitchen stove
    m.box((-26.5, -3.0, 8.2), (0.85, 0.85, 4.4), M.stone, bevel=0.02, col=False)
    g.box((-26.5, -3.0, 10.45), (1.0, 1.0, 0.12), M.stone)
    # kitchen: floor, partitions, linings, ceiling
    m.box((-24.25, -2.75, KZ / 2), (4.2, 4.2, KZ), M.weathered)
    m.box((-20.26, -0.435, KZ / 2), (3.18, 9.53, KZ), M.weathered)                          # porch deck
    m.wall((-26.5, HY0), (-26.5, -0.5), M.wallpaper, h=KCEIL - KZ, z=KZ, lower=(0.9, M.wood_mid))
    m.wall((-26.5, -0.5), (HX1, -0.5), M.wallpaper, h=KCEIL - KZ, z=KZ, lower=(0.9, M.wood_mid))
    m.wall((-22.17, -4.85), (-22.17, -0.65), M.wallpaper, h=KCEIL - KZ, t=0.04, z=KZ, lower=(0.9, M.wood_mid),
           openings=[(0.95, 1.0, 2.3, 0.95), (3.25, 1.4, 2.35, 0)])
    m.wall((-26.35, -4.83), (-22.15, -4.83), M.wallpaper, h=KCEIL - KZ, t=0.04, z=KZ, lower=(0.9, M.wood_mid),
           openings=[(1.15, 1.0, 2.3, 0.95), (3.05, 1.4, 2.35, 0)])
    m.box((-24.3, -2.75, KCEIL + 0.07), (4.5, 4.5, 0.14), M.paint_white)
    for i in range(4):
        g.box((-26.35 + 0.6 + i * 1.05, -2.75, KCEIL - 0.06), (0.12, 4.2, 0.12), M.wood_mid)
    # solid (non-enterable) remainder of the house
    m.collider((HX0 + 0.15, HY0 + 0.15, 0), (-26.65, HY1 - 0.15, HWH))
    m.collider((-26.65, -0.35, 0), (HX1 - 0.15, HY1 - 0.15, HWH))
    m.collider((-26.65, HY0 + 0.15, KCEIL), (HX1 - 0.15, -0.35, HWH))
    # porch: posts, beam, roof, ceiling, rails, steps
    px = PORCH_PX
    for py in (-5.05, -2.75, -0.45, 1.85, 4.15):
        m.box((px, py, KZ + 1.33), (0.18, 0.18, 2.66), M.paint_white, bevel=0.015)
        g.box((px, py, KZ + 2.62), (0.26, 0.26, 0.08), M.paint_white)
    g.box((px, -0.45, 3.12), (0.22, 9.7, 0.24), M.paint_white)
    fp.slab(g, (-22.15, 3.75), (-18.45, 3.2), 9.9, 0.14, M.house_roof, y=-0.45, extend=0.0)
    g.box((-20.4, -0.45, 3.17), (3.3, 9.6, 0.05), M.paint_sage)
    m.collider((-22.0, -5.3, 3.2), (-18.55, 4.4, 3.5))
    g.box((-18.45, -0.45, 3.14), (0.06, 10.0, 0.2), M.paint_white)
    for (ya, yb) in ((-5.05, -2.75), (-0.45, 1.85), (1.85, 4.15)):
        yl = yb - ya
        g.box((px, (ya + yb) / 2, KZ + 0.95), (0.1, yl, 0.08), M.paint_white)
        g.box((px, (ya + yb) / 2, KZ + 0.12), (0.08, yl, 0.06), M.paint_white)
        n = int(yl / 0.13)
        for i in range(1, n):
            g.box((px, ya + yl * i / n, KZ + 0.52), (0.04, 0.04, 0.8), M.paint_white)
        m.collider((px - 0.08, ya, KZ), (px + 0.08, yb, KZ + 1.0))
    ya, yb = -21.85, px
    g.box(((ya + yb) / 2, -5.05, KZ + 0.95), (yb - ya, 0.1, 0.08), M.paint_white)
    g.box(((ya + yb) / 2, -5.05, KZ + 0.12), (yb - ya, 0.08, 0.06), M.paint_white)
    for i in range(1, 22):
        g.box((ya + (yb - ya) * i / 22, -5.05, KZ + 0.52), (0.04, 0.04, 0.8), M.paint_white)
    m.collider((-21.85, -5.13, KZ), (px, -4.97, KZ + 1.0))
    m.box((-18.42, -1.6, 0.1), (0.5, 2.0, 0.2), M.stone, bevel=0.02)                     # front step
    m.box((-20.3, 4.58, 0.1), (2.4, 0.5, 0.2), M.stone, bevel=0.02)                      # north step
    m.box((-23.3, -5.24, KZ / 2), (1.6, 0.18, KZ), M.stone)                              # back landing
    m.box((-23.3, -5.58, 0.1), (1.6, 0.5, 0.2), M.stone, bevel=0.02)                     # back step
    g.box((-20.0, -1.6, KZ + 0.006), (0.9, 1.4, 0.012), M.burlap)                         # doormat
    # screen door frame
    for yy in (-2.38, -0.82):
        g.box((HX1 + 0.18, yy, KZ + 1.18), (0.06, 0.12, 2.36), M.paint_white)
    g.box((HX1 + 0.18, -1.6, KZ + 2.4), (0.06, 1.7, 0.12), M.paint_white)


build_house()

# porch & house props
place(fp.plank_door, 'hinge', 'Screen Door', (HX1 + 0.25, -2.3, KZ), PI / 2, w=1.36, h=2.32, ext=1, rest=0.75,
      screen=True, mat=M.paint_white, params={'sound': 'bang'})
place(fp.plank_door, 'hinge', 'Back Door', (-24.0, HY0 - 0.2, KZ), 0.0, w=1.36, h=2.32, ext=1, rest=1.35,
      mat=M.trim_green)
place(fp.porch_swing, 'swing', 'Porch Swing', (-20.6, 2.95, 3.12), PI / 2, drop=2.2)
def rocker(p, M):
    pf.rocking_chair(p, M.wood_mid, M.cushion)


def kitchen_curtains(p, M):
    pf.curtains(p, 1.0, 1.25, M.gingham, M.wood_dk)


place(rocker, 'rock', 'Rocking Chair', (-20.5, -3.85, KZ), PI / 2 + 0.3, key='rocker')
place(rocker, 'rock', 'Rocking Chair', (-20.3, 0.5, KZ), PI / 2 - 0.35, key='rocker')
place(fp.wind_chimes, 'swing', 'Wind Chimes', (-19.5, -4.35, 3.12))
place(fp.hanging_lantern, 'swing', 'Porch Lantern', (-19.55, -1.6, 3.12), drop=0.35, intensity=1.2, dist=8.0)
place(fp.shutter, 'hinge', 'Loose Shutter', (HX1 + 0.17, HY0 + 4.5 + 0.55, 3.9), PI / 2, ext=-1, rest=2.2)
with G(-24, 4).at((HX0 + 6.5 + 0.55, HY1 + 0.17, 3.9), PI):
    fp.shutter(StaticShim(G(-24, 4)), M, ext=1, rest=PI)
place(fp.bell_post, 'bell', 'Dinner Bell', (-18.2, 5.0, 0), PI / 2 + 0.3, tone=560)
place(fp.jack_o_lantern, 'flame', "Jack-o'-Lantern", (-18.25, -0.2, 0), PI / 2 + 0.2, face=0, light=0.9)
place(fp.jack_o_lantern, 'flame', "Jack-o'-Lantern", (-18.3, -3.0, 0), PI / 2 - 0.3, face=1, r=0.22)
gol = G(-20.5, -3)
with gol.at((-20.55, -2.95, KZ + 0.62)):
    gol.lathe((0, 0, 0), [(0.07, 0), (0.04, 0.03), (0.06, 0.08), (0.025, 0.14), (0.03, 0.15)], M.brass, n=10)
    gol.lathe((0, 0, 0.15), [(0.03, 0), (0.045, 0.06), (0.025, 0.2)], M.window_glow, n=8, cap_top=False)
gh_ = G(-20, 0)
gh_.box((-20.55, -2.95, KZ + 0.3), (0.42, 0.42, 0.6), M.wood_light, bevel=0.01)          # crate side table
gh_.box((-20.55, -2.95, KZ + 0.605), (0.3, 0.22, 0.03), M.cloth_white)
fp.pumpkin(gh_, M, (-18.42, -0.9, 0.2), 0.2, 0.4)
fp.pumpkin(gh_, M, (-18.45, -2.3, 0.2), 0.16, 1.4)
fp.pumpkin(gh_, M, (-19.6, 3.6, KZ), 0.26, 0.7)
fp.pumpkin(gh_, M, (-19.3, 3.2, KZ), 0.15, 2.0, mat=M.leaf_gold)
with gh_.at((-21.9, 2.9, KZ), PI / 2):
    gh_.box((0, 0.1, 0.45), (0.06, 0.06, 0.9), M.wood_light, rx=-0.15)                    # broom
    gh_.cyl((0, 0.0, 0.0), 0.12, 0.3, M.straw, n=6, r2=0.04, smooth=False)
gh_.box((PORCH_PX, -3.9, KZ + 0.98), (0.12, 1.4, 0.02), M.quilt)                    # quilt over the rail
gh_.box((PORCH_PX + 0.07, -3.9, KZ + 0.7), (0.02, 1.3, 0.55), M.quilt)
# kitchen interior
place(fp.wood_stove, 'flame', 'Kitchen Stove', (-25.95, -3.3, KZ), PI / 2, light=1.0, pipe=KCEIL - KZ - 0.79)
place(fp.wall_clock, 'clock', 'Kitchen Clock', (-24.6, -0.68, 2.35), 0.0)
place(kitchen_curtains, 'cloth', 'Kitchen Curtains', (-25.2, HY0 + 0.19, KZ + 2.35), PI)
place(fp.pot_rack, 'swing', 'Pot Rack', (-24.4, -3.3, KCEIL))
place(fp.kitchen_chair, 'jolt', 'Kitchen Chair', (-23.0, -3.7, KZ), -0.4, tipped=True)
gkc = G(-25, -3)
with gkc.at((-25.1, -2.7, KZ), PI / 2 + 0.12):
    for sx in (-1, 1):
        for sy in (-1, 1):
            gkc.box((sx * 0.19, sy * 0.18, 0.22), (0.04, 0.04, 0.44), M.wood_mid)
        gkc.box((sx * 0.19, 0.19, 0.72), (0.04, 0.04, 0.58), M.wood_mid, rx=-0.06)
    gkc.box((0, 0, 0.46), (0.46, 0.44, 0.04), M.wood_mid)
    for i in range(3):
        gkc.box((0, 0.2, 0.62 + i * 0.13), (0.38, 0.02, 0.05), M.wood_mid, rx=-0.06)
m.collider((-25.35, -2.95, KZ), (-24.85, -2.45, KZ + 0.9))
with gol.at((-23.75, -2.3, KZ + 0.79)):
    gol.lathe((0, 0, 0), [(0.06, 0), (0.035, 0.03), (0.05, 0.08), (0.022, 0.13)], M.brass, n=10)
    gol.lathe((0, 0, 0.13), [(0.026, 0), (0.04, 0.06), (0.022, 0.18)], M.window_glow, n=8, cap_top=False)
gk = G(-24, -3)
gk.box((-24.15, -2.6, KZ + 0.003), (2.4, 2.0, 0.006), M.quilt)                          # rag rug
with gk.at((-24.15, -2.6, KZ)):
    pf.table(gk, 1.3, 0.85, 0.78, M.wood_mid, cloth=M.gingham)
gk.lathe((-24.4, -2.75, KZ + 0.8), [(0.16, 0), (0.17, 0.05), (0.15, 0.06)], M.leaf_orange, n=14)   # pie
gk.cyl((-24.4, -2.75, KZ + 0.8), 0.12, 0.062, M.straw, n=14)
gk.box((-24.35, -2.7, KZ + 0.868), (0.12, 0.07, 0.006), M.wood_dk, rz=0.5)               # missing slice
for (x, y) in ((-23.75, -2.85), (-24.55, -2.3)):
    gk.cyl((x, y, KZ + 0.79), 0.11, 0.015, M.cloth_white, n=12)
gk.cyl((-23.7, -2.4, KZ + 0.79), 0.04, 0.1, M.cloth_white, n=8)                         # mug
with gk.at((-26.05, -1.4, KZ), PI / 2):                                                 # hutch
    fp.hutch(gk, M)
m.collider((-26.35, -2.15, KZ), (-25.75, -0.65, KZ + 2.2))
gk.box((-25.2, -4.55, KZ + 0.45), (1.6, 0.55, 0.9), M.paint_sage, bevel=0.02)             # sink cabinet
gk.box((-25.2, -4.55, KZ + 0.92), (1.7, 0.6, 0.05), M.wood_mid)
gk.box((-25.3, -4.55, KZ + 0.9), (0.6, 0.4, 0.04), M.tin)
m.collider((-26.0, -4.85, KZ), (-24.4, -4.25, KZ + 0.95))
fp.bucket_geo(gk, M, (-24.75, -4.5, KZ + 0.95), 0.12, 0.2, water=True)
for i, x in enumerate((-22.6, -23.0, -26.2)):
    gk.box((x, -0.85, KZ + 1.7 + (i % 2) * 0.2), (0.25, 0.2, 0.03), M.wood_dk)
gk.box((-22.55, -4.4, KZ + 0.4), (0.5, 0.5, 0.8), M.wood_mid)                              # butter churn stand
gk.lathe((-22.55, -4.4, KZ + 0.8), [(0.17, 0), (0.15, 0.5), (0.08, 0.56)], M.wood_light, n=10)
gk.cyl((-22.55, -4.4, KZ + 1.3), 0.015, 0.4, M.wood_dk, n=5)
m.collider((-22.8, -4.65, KZ), (-22.3, -4.15, KZ + 1.3))
# north side yard: woodpile against the house, cellar doors, dinner bell
put(fp.woodpile, (-26.0, HY1 + 0.6, 0), 0.0, length=3.4, h=1.3, seed=5, back=False)
gcd = G(-29.5, 5)
with gcd.at((-29.4, HY1 + 0.15, 0)):
    gcd.box((0, 0.75, 0.3), (1.9, 1.5, 0.6), M.stone)
    gcd.box((-0.45, 0.62, 0.66), (0.86, 1.45, 0.06), M.trim_green, rx=-0.42)
    gcd.box((-0.06, 0.62, 0.7), (0.04, 0.3, 0.04), M.iron, rx=-0.42)
    m.collider((-30.35, HY1 + 0.15, 0), (-28.45, HY1 + 1.65, 0.9))


def cellar_door(p, M):
    """Right leaf of the bulkhead cellar doors; hinged along its outer (east) edge, on the slope."""
    pv = p.part('pivot', (0.0, 0.0, 0.0), rx=-0.42)
    g = pv.geo
    g.box((-0.43, 0.0, 0.0), (0.86, 1.45, 0.06), M.trim_green)
    for yy in (-0.5, 0.0, 0.5):
        g.box((-0.43, yy, 0.04), (0.84, 0.08, 0.025), M.trim_green)
    g.box((-0.78, 0.0, 0.05), (0.04, 0.3, 0.04), M.iron)
    for yy in (-0.55, 0.55):
        g.box((-0.12, yy, 0.04), (0.24, 0.05, 0.012), M.iron)
    p.params.update(axis='z', dir=-1, closed=0, open=1.25, sound='bang')


place(cellar_door, 'hinge', 'Cellar Door', (-28.52, HY1 + 0.77, 0.66), 0.0)
place(fp.barrel_prop, 'jolt', 'Rain Barrel', (-31.62, -1.6, 0), 0.0, key='barrel')
gwb = G(-32, -1)
gwb.box((-31.22, -1.6, 3.55), (0.08, 0.08, 2.5), M.tin)                           # downspout into the barrel
gwb.box((-31.38, -1.6, 2.25), (0.08, 0.08, 0.36), M.tin, ry=0.7)
gwb.box((-31.52, -1.6, 1.98), (0.08, 0.08, 0.3), M.tin)
gwb.box((-31.25, -0.5, 5.98), (0.16, 9.6, 0.1), M.tin)                            # gutter along the eave
# west alley clutter: a tub planter gone to seed, a broken wheel, crates, an old plow
with gwb.at((-33.6, 1.6, 0), 0.25):
    gwb.lathe((0, 0, 0.12), [(0.32, 0), (0.34, 0.4), (0.36, 0.45)], M.rust, n=12, cap_top=False)
    for sx in (-1, 1):
        gwb.box((sx * 0.2, 0.75, 0.06), (0.08, 0.08, 0.12), M.iron)
        gwb.box((sx * 0.2, -0.75, 0.06), (0.08, 0.08, 0.12), M.iron)
    gwb.box((0, 0, 0.3), (0.6, 1.5, 0.36), M.rust, bevel=0.12)
    gwb.box((0, 0, 0.47), (0.62, 1.52, 0.04), M.paint_white, bevel=0.015)
    gwb.box((0, 0, 0.49), (0.5, 1.36, 0.02), M.soil)
    for q in range(6):
        fp.grass_tuft(gwb, M, (RNG.uniform(-0.15, 0.15), RNG.uniform(-0.5, 0.5), 0.5), seed=70 + q, h=0.5,
                      mats=[M.leaf_olive, M.corn_leaf2])
m.collider((-34.1, 0.75, 0), (-33.1, 2.45, 0.5))
with gwb.at((-34.65, -3.5, 0.62), PI / 2, rx=0.12):
    fp.spoked_wheel(gwb, (0, 0, 0), 0.6, M, spokes=7, axis='y')
fp.crate_geo(gwb, M, 0.6, (-34.3, 5.6, 0), 0.2)
fp.crate_geo(gwb, M, 0.5, (-34.3, 5.55, 0.6), 0.7, apples=False)
fp.crate_geo(gwb, M, 0.55, (-33.6, 6.1, 0), 1.1)
m.collider((-34.7, 5.2, 0), (-33.25, 6.45, 1.1))
with gwb.at((-33.9, -7.0, 0), 1.2):
    gwb.box((0, 0, 0.35), (0.08, 1.6, 0.08), M.rust, rx=0.35)
    gwb.box((0, -0.75, 0.15), (0.35, 0.5, 0.05), M.rust, rx=-0.6, ry=0.4)
    for sx in (-1, 1):
        gwb.box((sx * 0.22, 0.65, 0.55), (0.05, 0.9, 0.05), M.wood_mid, rx=0.5)
tufts_line((-34.4, -4.0), (-34.4, 8.0), 14, seed=71, jitter=0.25)

# ============================================================================ BARNYARD (hub)
OAK = (-10.5, 4.0)
place(fp.oak, 'foliage', 'Old Oak', (OAK[0], OAK[1], 0), 0.0)
lx, ly, lz = 2.405, -1.3375, 4.47
place(fp.tire_swing, 'swing', 'Tire Swing', (OAK[0] + lx, OAK[1] + ly, lz), 0.0, drop=3.65)
leaves(OAK[0], OAK[1], 6.0, 260, seed=1)
leaves(OAK[0] + 2.0, OAK[1] - 2.0, 3.0, 60, seed=2)
go = G(*OAK)
for i in range(6):
    a = TAU * i / 6 + 0.4
    go.tube([(OAK[0] + math.cos(a) * 0.4, OAK[1] + math.sin(a) * 0.4, 0.35),
             (OAK[0] + math.cos(a) * 1.0, OAK[1] + math.sin(a) * 1.0, 0.08),
             (OAK[0] + math.cos(a) * 1.5, OAK[1] + math.sin(a) * 1.5, -0.05)], 0.12, M.bark, n=5)
with go.at((-13.2, 2.6, 0), 0.45):
    fp.bench_geo(go, M, 1.6)

WELL = (6.0, -2.5)
gw = G(*WELL)
with gw.at((WELL[0], WELL[1], 0)):
    gw.lathe((0, 0, 0), [(0.95, 0), (0.95, 0.75), (0.99, 0.8), (0.99, 0.88), (0.7, 0.88), (0.7, 0.8), (0.68, 0.2)],
             M.stone, n=14, smooth=False, cap_bottom=False, cap_top=False)
    gw.cyl((0, 0, 0.2), 0.69, 0.01, M.water, n=14)
    for sx in (-1, 1):
        gw.box((sx * 1.05, 0, 1.3), (0.15, 0.15, 2.6), M.wood_dk, bevel=0.015)
        gw.box((sx * 1.05, 0, 2.05), (0.2, 0.2, 0.12), M.wood_dk)
    with gw.at((0, 0, 2.62)):
        for sy in (-1, 1):
            gw.box((0, sy * 0.52, 0.28), (2.7, 1.2, 0.06), M.barn_roof, rx=-sy * 0.5)
        gw.box((0, 0, 0.58), (2.75, 0.12, 0.08), M.wood_dk)
        gw.prism((-1.25, 0.0, 0.0), [(-1.0, 0.0), (1.0, 0.0), (0.0, 0.55)], 0.04, M.wood_dk, rx=PI / 2, rz=PI / 2)
        gw.prism((1.29, 0.0, 0.0), [(-1.0, 0.0), (1.0, 0.0), (0.0, 0.55)], 0.04, M.wood_dk, rx=PI / 2, rz=PI / 2)
    gw.box((0, 0, 2.62), (2.3, 0.1, 0.1), M.wood_dk)
round_collider(WELL[0], WELL[1], 1.0, 0, 1.0)
m.collider((WELL[0] - 1.35, WELL[1] - 1.1, 2.62), (WELL[0] + 1.35, WELL[1] + 1.1, 3.25))   # well roof
m.collider((WELL[0] - 1.13, WELL[1] - 0.09, 0), (WELL[0] - 0.97, WELL[1] + 0.09, 2.6))
m.collider((WELL[0] + 0.97, WELL[1] - 0.09, 0), (WELL[0] + 1.13, WELL[1] + 0.09, 2.6))
place(fp.well_crank, 'spin', 'Well Crank', (WELL[0], WELL[1], 2.05), 0.0, span=1.8)
place(fp.well_bucket, 'swing', 'Well Bucket', (WELL[0], WELL[1] + 0.0, 1.94), 0.0, drop=0.9)
fp.bucket_geo(gw, M, (WELL[0] + 1.4, WELL[1] - 0.6, 0), 0.15, 0.3, water=True)
fp.bucket_geo(gw, M, (WELL[0] + 1.75, WELL[1] - 0.35, 0.14), 0.14, 0.28, tilt=1.45)

put(fp.hay_stack, (-6.5, -8.5, 0), 0.0, r=2.2, h=4.2)
put(fp.corn_crib, (11.6, -6.6, 0), PI / 2)
put(fp.wagon, (8.0, 6.2, 0), 2.35, load='hay', seed=1)
put(fp.trough, (-4.3, 9.6, 0), 0.0)
put(fp.woodpile, (-14.8, -6.8, 0), PI / 2, length=3.2, h=1.5, seed=2)
place(fp.tarp, 'cloth', 'Woodpile Tarp', (-14.8, -6.8, 1.5), PI / 2, w=3.4, d=0.9, h=0.42)
place(fp.chopping_block, 'jolt', 'Chopping Block', (-13.0, -5.3, 0), 0.4)
place(fp.burn_barrel, 'flame', 'Burn Barrel', (-11.6, -3.4, 0), light=1.3)
place(fp.lantern_post, 'flame', 'Lantern Post', (2.9, 9.4, 0), key='lpost', light=1.1, dist=9.0)
place(fp.lantern_post, 'flame', 'Lantern Post', (-15.4, 0.6, 0), key='lpost')
place(fp.milk_can, 'jolt', 'Milk Can', (3.6, 10.0, 0), 0.0)
put_prop_static(fp.milk_can, (4.1, 9.55, 0), 1.2)

place(fp.barrel_prop, 'jolt', 'Rain Barrel', (-7.7, 10.35, 0), key='barrel')
_g = G(7, 10)
with _g.at((7.75, 10.4, 0)):
    _g.lathe((0, 0, 0), [(0.27, 0), (0.32, 0.22), (0.34, 0.45), (0.32, 0.68), (0.27, 0.9)], M.wood_mid, n=12)
    _g.cyl((0, 0, 0.82), 0.27, 0.01, M.water, n=12)
    for z in (0.1, 0.8):
        _g.torus((0, 0, z), 0.3, 0.012, M.iron, n=12, m=3)
m.collider((7.43, 10.08, 0), (8.07, 10.72, 0.9))
fp.crate_geo(G(8, 9), M, 0.6, (8.7, 9.6, 0), 0.3)
m.collider((8.3, 9.2, 0), (9.1, 10.0, 0.6))
place(fp.crate_prop, 'jolt', 'Crate', (-3.4, 6.2, 0), 1.1, key='crate_apples', s=0.55, apples=True)
place(fp.wheelbarrow, 'jolt', 'Wheelbarrow', (-2.2, 5.0, 0), 2.6, load='leaves', seed=3)
gy = G(0, 0)
fp.crate_geo(gy, M, 0.6, (9.3, 9.95, 0), 0.1)
fp.crate_geo(gy, M, 0.55, (9.15, 9.9, 0.6), 0.5)
m.collider((8.95, 9.6, 0), (9.65, 10.3, 1.15))
fp.sack_geo(gy, M, (-3.8, 8.7, 0), 0.4)
fp.sack_geo(gy, M, (-3.3, 9.0, 0), 1.8, mat=M.sack_pale)
fp.hay_bale_geo(gy, M, (-0.1, -7.1, 0), 1.1)
m.collider((-0.5, -7.65, 0), (0.3, -6.55, 0.45))
place(fp.hay_bale, 'jolt', 'Hay Bale', (-1.25, -6.3, 0), 0.4, key='bale')
leaves(-6.5, -8.5, 3.6, 40, seed=7, mats=[M.straw, M.leaf_gold])
tufts(0, 0, 12, 50, seed=3)

# pig sty between the well and the coop: fence, lean-to shed, wallow and two dozing Durocs
SX0, SX1, SY0, SY1 = 2.6, 8.4, -10.8, -6.6
put(fp.rail_fence, (SX0, SY0, 0), 0.0, length=SX1 - SX0, seed=31)
put(fp.rail_fence, (SX0, SY0, 0), PI / 2, length=SY1 - SY0, seed=32)
put(fp.rail_fence, (SX1, SY0, 0), PI / 2, length=SY1 - SY0, seed=33)
put(fp.rail_fence, (SX0, SY1, 0), 0.0, length=1.0, seed=34)
put(fp.rail_fence, (SX0 + 2.6, SY1, 0), 0.0, length=SX1 - SX0 - 2.6, seed=35)
gsty = G(5, -9)
with gsty.at((SX0 + 1.0, SY1, 0), 0.0):                                  # gate left swung open
    gsty.box((0, 0, 0.7), (0.16, 0.16, 1.4), M.wood_dk)
    with gsty.at((0, 0, 0), -1.9):
        for i in range(4):
            gsty.box((0.8, 0, 0.25 + i * 0.27), (1.5, 0.05, 0.09), M.grey_wood)
        gsty.box((0.8, 0.04, 0.6), (1.6, 0.04, 0.08), M.grey_wood, ry=-0.6)
gsty.add(fp.prim_poly(fp.blob_poly(4.6, -8.9, 1.6, 1.1, n=14, seed=4), 0.011), M.soil)       # wallow
gsty.add(fp.prim_poly(fp.blob_poly(4.4, -9.0, 0.9, 0.6, n=12, seed=5), 0.014), M.water)
for (x, y, a, z) in ((4.0, -8.6, 0.6, 0.0), (5.2, -9.3, 2.9, 0.0)):        # pigs
    with gsty.at((x, y, z), a):
        gsty.sphere((0, 0, 0.3), 0.36, M.cloth_rose, n=10, s=(0.72, 1.25, 0.72))
        gsty.sphere((0, -0.48, 0.3), 0.19, M.cloth_rose, n=8)
        gsty.cyl((0, -0.6, 0.27), 0.08, 0.1, M.cushion, n=8, rx=PI / 2)
        for sx in (-1, 1):
            gsty.box((sx * 0.1, -0.52, 0.47), (0.1, 0.03, 0.1), M.cloth_rose, rx=0.5, ry=sx * 0.4)
            for sy in (-0.25, 0.3):
                gsty.cyl((sx * 0.13, sy, 0.0), 0.05, 0.12, M.cloth_rose, n=5)
        gsty.tube([(0, 0.44, 0.35), (0.06, 0.52, 0.42), (-0.03, 0.56, 0.45)], 0.012, M.cloth_rose, n=3)
m.collider((3.5, -9.2, 0), (4.5, -8.0, 0.55))
m.collider((4.7, -9.9, 0), (5.7, -8.7, 0.55))
with gsty.at((SX0 + 0.35, -8.6, 0), PI / 2):
    fp.trough(gsty, M, length=1.6, col=False)
m.collider((SX0 + 0.05, -9.4, 0), (SX0 + 0.65, -7.8, 0.6))
# lean-to shed in the SE corner of the sty
LX0, LX1, LY0, LY1 = 5.8, SX1, SY0, -8.8
for (x, y, h) in ((LX0, LY1, 1.9), (LX1, LY1, 1.9), (LX0, LY0, 2.4), (LX1, LY0, 2.4)):
    gsty.box((x, y, h / 2), (0.14, 0.14, h), M.wood_dk)
gsty.box((( LX0 + LX1) / 2, LY0 + 0.05, 1.2), (LX1 - LX0, 0.08, 2.4), M.barn_in)
gsty.box((LX1 - 0.05, (LY0 + LY1) / 2, 1.05), (0.08, LY1 - LY0, 2.1), M.barn_in)
with gsty.at(((LX0 + LX1) / 2, (LY0 + LY1) / 2, 0), PI / 2):
    fp.slab(gsty, (-(LY1 - LY0) / 2 - 0.35, 2.45), ((LY1 - LY0) / 2 + 0.35, 1.85), LX1 - LX0 + 0.4, 0.05, M.rust)
gsty.box(((LX0 + LX1) / 2 + 0.3, (LY0 + LY1) / 2, 0.03), (1.6, 1.4, 0.05), M.hay)
m.collider((LX0 - 0.05, LY0, 0), (LX1, LY0 + 0.12, 2.4))
m.collider((LX0 - 0.1, LY0, 1.95), (LX1, LY1 + 0.3, 2.5))                         # shed roof
m.collider((LX1 - 0.1, LY0, 0), (LX1, LY1, 2.1))
for (px, py) in ((LX0, LY1), (LX0, LY0)):
    m.collider((px - 0.08, py - 0.08, 0), (px + 0.08, py + 0.08, 2.0))
tufts_line((SX0, SY0 - 0.3), (SX1, SY0 - 0.3), 10, seed=36)
tufts_line((SX1 + 0.3, SY0), (SX1 + 0.3, SY1), 8, seed=37)
# puddles after the afternoon rain
for i, (x, y, rx, ry) in enumerate(((-2.0, 1.5, 1.1, 0.6), (2.8, 6.8, 0.8, 0.5), (0.6, -16.5, 0.9, 0.45),
                                    (-1.6, -27.0, 1.0, 0.5), (12.0, 11.4, 0.9, 0.5), (-23.8, -15.0, 0.7, 0.4))):
    G(x, y).add(fp.prim_poly(fp.blob_poly(x, y, rx, ry, n=12, seed=40 + i, jitter=0.2), 0.016), M.water)

# ============================================================================ ORCHARD (NW)
put(fp.stone_wall, (-29.0, 13.0, 0), 0.0, length=12.0, seed=5)           # south wall x -35..-23
put(fp.stone_wall, (-16.0, 13.0, 0), 0.0, length=6.0, seed=6)            # x -19..-13 (gap -23..-19)
put(fp.stone_wall, (-13.0, 16.5, 0), PI / 2, length=7.0, seed=7)         # east wall y 13..20
put(fp.stone_wall, (-13.0, 25.0, 0), PI / 2, length=6.0, seed=8)         # y 22..28 (gap 20..22)
place(fp.farm_gate, 'hinge', 'Orchard Gate', (-23.0, 13.0, 0), 0.0, w=2.0, ext=1, rest=1.9, key='gate2')
TREES = [(-30.0, 17.5, 0), (-24.5, 16.5, 1), (-18.5, 17.8, 2), (-29.0, 23.5, 1), (-23.2, 23.0, 0), (-17.0, 24.0, 2),
         (-25.5, 29.5, 2), (-19.0, 30.0, 0), (-31.0, 27.5, 1)]
for i, (x, y, v) in enumerate(TREES):
    if i in (2, 5):   # a couple of the trees are plain scenery
        put_prop_static(fp.apple_tree, (x, y, 0), RNG.uniform(0, TAU), seed=10 + v, h=4.2 + v * 0.25)
    else:
        place(fp.apple_tree, 'foliage', 'Apple Tree', (x, y, 0), RNG.uniform(0, TAU), key=f'apple{v}', seed=10 + v,
              h=4.2 + v * 0.25)
    leaves(x, y, 2.4, 55, seed=20 + i, mats=[M.leaf_gold, M.leaf_olive, M.leaf_orange])
    ga = G(x, y)
    for k in range(5):
        a = RNG.uniform(0, TAU)
        d = RNG.uniform(0.6, 2.2)
        ga.sphere((x + math.cos(a) * d, y + math.sin(a) * d, 0.05), 0.055, M.apple, n=6)
place(fp.cider_press, 'spin', 'Cider Press', (-21.2, 20.2, 0), 0.4)
place(fp.basket_prop, 'jolt', 'Apple Basket', (-22.4, 21.1, 0), 0.0, key='basket_apples', kind='apples', seed=1)
place(fp.basket_prop, 'jolt', 'Apple Basket', (-24.0, 17.8, 0), 0.6, key='basket_apples')

go2 = G(-24, 23)
fp.crate_geo(go2, M, 0.55, (-19.9, 22.15, 0), 0.2, apples=True)
fp.crate_geo(go2, M, 0.55, (-19.95, 21.85, 0.55), 0.6)
m.collider((-20.3, 21.0, 0), (-19.5, 22.5, 1.1))
with go2.at((-23.2, 22.25, 0), 0.0):
    fp.ladder_geo(go2, M, 3.0, lean=0.3)
for (x, y) in ((-33.3, 19.5), (-33.3, 21.0)):                               # beehives
    go2.box((x, y, 0.2), (0.6, 0.6, 0.4), M.wood_dk)
    for k in range(3):
        go2.box((x, y, 0.55 + k * 0.28), (0.55, 0.55, 0.26), M.paint_white, bevel=0.01)
    go2.box((x, y, 1.42), (0.66, 0.66, 0.06), M.tin)
    m.collider((x - 0.33, y - 0.33, 0), (x + 0.33, y + 0.33, 1.45))
place(fp.crow, 'bob', 'Crow', (-15.5, 13.0, 0.95), 0.3, key='crow', look=0.0)
place(fp.lantern_post, 'flame', 'Orchard Lantern', (-12.35, 22.7, 0), key='lpost')
tufts(-24, 23, 9, 70, seed=8)

# ============================================================================ BACK LANE (behind the barn)
put(fp.trough, (5.5, 32.6, 0), 0.0, length=2.4)
put(fp.wagon, (-9.2, 32.8, 0), PI / 2 + 0.08, load='hay', seed=4)
put(fp.rail_fence, (8.2, 34.2, 0), 0.0, length=6.0, seed=9, col=False)
place(fp.crow, 'bob', 'Crow', (10.6, 34.2, 1.2), PI, key='crow')
fp.hay_bale_geo(G(8, 32), M, (8.2, 32.1, 0), 0.15)
gbl = G(-4, 28)                                                            # wall lantern by the north doors
gbl.box((-3.6, BY1 + 0.17, 3.45), (0.12, 0.06, 0.3), M.iron)
gbl.box((-3.6, BY1 + 0.42, 3.55), (0.04, 0.5, 0.04), M.iron)
place(fp.hanging_lantern, 'swing', 'Barn Lantern', (-3.6, BY1 + 0.62, 3.53), 0.0, drop=0.25, intensity=1.1, dist=8.0)
m.collider((7.65, 31.8, 0), (8.75, 32.4, 0.44))
gl = G(0, 32)
gl.blob((2.5, 34.0, -0.2), 1.3, M.wood_dk, seed=4, jitter=0.2, subdiv=1, s=(1.6, 1.0, 0.55))     # manure heap
with gl.at((1.0, 33.3, 0), 0.4):
    fp.tool_lean(gl, M, 'pitchfork', 0.35)
m.collider((0.6, 33.2, 0), (4.4, 34.9, 0.7))
tufts(0, 32, 10, 40, seed=9)

# ============================================================================ CORN MAZE (NE)
MAZE = ['###############',
        '#       #     #',
        '# ### ##### ###',
        '    #         #',
        '### ### #   # #',
        '#     # #   # #',
        '# ### ### ### #',
        '# #       #   #',
        '### ### ### # #',
        '      #     # #',
        '# ### ### ### #',
        '#   #     #   #',
        '### # ##### # #',
        '#     #       #',
        '### ##### #####']


def mz_x(c):
    k = c // 2
    if c % 2 == 0:
        x0 = 14.55 + k * 2.9
        return x0, x0 + 0.9
    x0 = 14.55 + 0.9 + k * 2.9
    return x0, x0 + 2.0


def mz_y(r):
    if r % 2 == 0:
        k = (14 - r) // 2
        y0 = 12.6 + k * 2.9
        return y0, (35.75 if r == 0 else y0 + 0.9)
    j = (13 - r) // 2
    y0 = 12.6 + 0.9 + j * 2.9
    return y0, y0 + 2.0


def mz_cell(i, j):
    return 16.45 + 2.9 * i, 14.5 + 2.9 * j


def maze_open(r, c):
    if r < 0 or c < 0 or r > 14 or c > 14:
        return r > 14 or c < 0   # south and west of the maze are open ground; north/east is more corn
    return MAZE[r][c] != '#'


def build_maze():
    gmz = G(25, 24)
    for r in range(15):
        row = MAZE[r]
        c = 0
        while c < 15:
            if row[c] != '#':
                c += 1
                continue
            c0 = c
            while c < 15 and row[c] == '#':
                c += 1
            x0, x1 = mz_x(c0)[0], mz_x(c - 1)[1]
            y0, y1 = mz_y(r)
            fp.corn_block(gmz, M, x0, y0, x1, y1, faces='', seed=r * 31 + c0, col=True, top=False, shrink=0.0)
        for c in range(15):
            if row[c] != '#':
                continue
            faces = ''
            for f, (dr, dc) in (('N', (-1, 0)), ('S', (1, 0)), ('E', (0, 1)), ('W', (0, -1))):
                if maze_open(r + dr, c + dc):
                    faces += f
            x0, x1 = mz_x(c)
            y0, y1 = mz_y(r)
            if r == 0:
                y1 = min(y1, 34.2)
            fp.corn_block(gmz, M, x0, y0, x1, y1, faces=faces, seed=1000 + r * 31 + c, col=False, top=True,
                          core=False, shrink=0.0)


build_maze()
for (i, j, lbl) in ((0, 0, 'Corn Stalks'), (0, 3, 'Corn Stalks'), (3, 0, 'Corn Stalks'), (3, 6, 'Corn Stalks'),
                    (6, 6, 'Corn Stalks')):
    x, y = mz_cell(i, j)
    place(fp.corn_clump, 'foliage', lbl, (x + RNG.uniform(-0.3, 0.3), y + RNG.uniform(-0.3, 0.3), 0),
          RNG.uniform(0, TAU), key=f'clump{(i + j) % 2}', seed=40 + (i + j) % 2)
place(fp.scarecrow, 'spin', 'Maze Scarecrow', (31.4, 25.7, 0), -2.34, hat='felt', shirt=M.cloth_sage, seed=3)
place(fp.corn_shock, 'foliage', 'Corn Shock', (13.55, 18.2, 0), 0.3, key='shock', seed=5)
place(fp.corn_shock, 'foliage', 'Corn Shock', (13.55, 22.4, 0), 1.9, key='shock')
place(fp.lantern_post, 'flame', 'Maze Lantern', (21.4, 11.75, 0), key='lpost')
# maze sign on a post by the south-west entrance, hanging from an arm
gms = G(17, 12)
gms.box((17.3, 11.9, 1.3), (0.14, 0.14, 2.6), M.grey_wood)
gms.box((17.85, 11.9, 2.62), (1.2, 0.1, 0.1), M.grey_wood)
m.collider((17.2, 11.8, 0), (17.4, 12.0, 2.6))


def maze_sign(p, M):
    pv = p.part('pivot')
    g = pv.geo
    for sx in (-0.3, 0.3):
        g.cyl((sx, 0, -0.32), 0.006, 0.32, M.iron, n=3)
    g.box((0, 0, -0.55), (0.9, 0.05, 0.46), M.wood_light, bevel=0.015)
    for k, (x, z, w) in enumerate(((-0.25, -0.48, 0.22), (0.05, -0.48, 0.2), (0.3, -0.48, 0.15), (-0.1, -0.62, 0.5))):
        g.box((x, -0.03, z), (w, 0.01, 0.07), M.leaf_red if k < 3 else M.wood_dk)
    g.prism((0.1, -0.03, -0.73), [(0, 0), (0.25, 0.04), (0, 0.08)], 0.01, M.wood_dk, rx=PI / 2)
    p.params.update(axes='x', amp=0.05, period=2.4, sound='creak')


place(maze_sign, 'swing', 'Corn Maze Sign', (18.1, 11.9, 2.57), 0.0)
place(fp.crow, 'bob', 'Crow', (17.3, 11.9, 2.6), 0.6, key='crow')
tufts_line((14.0, 11.5), (35.0, 11.8), 40, seed=10)

# ============================================================================ PUMPKIN PATCH (E)
put(fp.rail_fence, (15.5, -12.0, 0), PI / 2, length=12.0, seed=11)        # y -12..0
put(fp.rail_fence, (15.5, 2.5, 0), PI / 2, length=6.8, seed=12)           # y 2.5..9.3
put(fp.rail_fence, (15.5, 9.3, 0), 0.0, length=6.5, seed=13)              # x 15.5..22
put(fp.rail_fence, (24.0, 9.3, 0), 0.0, length=11.0, seed=14)             # x 24..35
place(fp.farm_gate, 'hinge', 'Pumpkin Patch Gate', (15.5, 0.0, 0), PI / 2, w=2.5, ext=1, rest=1.75, key='gate')
gp = G(25, 0)
prng = random.Random(77)
for row_y in (7.6, 5.2, -4.4, -6.9, -9.6):
    xs = 17.0
    while xs < 34.0:
        x = xs + prng.uniform(-0.3, 0.3)
        y = row_y + prng.uniform(-0.45, 0.45)
        skip = any(math.hypot(x - ax, y - ay) < 1.6 for ax, ay in ((19.5, 6.8), (22.5, 4.5), (28.5, -7.0), (25.5, -4.5),
                                                                   (31.0, 5.0), (21.0, -8.6), (31.0, -2.0), (26.5, -10.5)))
        if not skip:
            r = prng.uniform(0.16, 0.34)
            fp.pumpkin(gp, M, (x, y, 0), r, prng.uniform(0, TAU), prng.uniform(-0.15, 0.15),
                       mat=M.pumpkin if prng.random() > 0.12 else M.leaf_gold, ribs=6, rings=4)
            a0 = prng.uniform(0, TAU)
            side = prng.choice((-1, 1))
            pts = [(x + math.cos(a0) * r * 0.7, y + math.sin(a0) * r * 0.7, 0.05)]
            for q in range(1, 5):
                aa = a0 + side * q * 0.55
                pts.append((pts[-1][0] + math.cos(aa) * 0.28, pts[-1][1] + math.sin(aa) * 0.28, 0.035))
            gp.tube(pts, 0.016, M.stem, n=3, caps=False)
            for k, (vx, vy, _) in enumerate(pts[1::2]):
                a = prng.uniform(0, TAU)
                gp.add(fp.prim_blade(0.3, 0.22, up=0.35, droop=0.8, seg=2), M.leaf_olive, fp._mat((vx, vy, 0.03), a))
        xs += prng.uniform(1.3, 2.1)
# farm stand with awning
FS = (19.6, 6.8)
with gp.at((FS[0], FS[1], 0)):
    gp.box((0, 0, 0.45), (2.4, 0.9, 0.9), M.weathered, bevel=0.02)
    gp.box((0, -0.05, 0.92), (2.6, 1.1, 0.06), M.wood_mid)
    for sx in (-1, 1):
        gp.box((sx * 1.25, 0.4, 1.3), (0.1, 0.1, 2.6), M.wood_mid)
        gp.box((sx * 1.25, -0.5, 1.15), (0.1, 0.1, 2.3), M.wood_mid)
    gp.box((0, -0.05, 2.45), (2.8, 1.4, 0.06), M.barn_roof, rx=-0.25)
    gp.box((0, 0.46, 1.75), (2.4, 0.04, 0.5), M.wood_light)
    for k, x in enumerate((-0.8, -0.35, 0.15, 0.6)):
        fp.pumpkin(gp, M, (x, -0.05, 0.95), 0.14 + 0.03 * (k % 2), k * 1.3, 0.1)
    fp.pumpkin(gp, M, (0.9, 0.05, 0.95), 0.1, 0, 0, mat=M.leaf_gold)
    gp.box((-1.0, -0.3, 0.98), (0.2, 0.15, 0.12), M.tin)                                     # honesty box
    for k in range(4):
        gp.box((-0.85 + k * 0.4, 0.465, 1.75), (0.22, 0.012, 0.1), M.leaf_red)
m.collider((FS[0] - 1.3, FS[1] - 0.6, 0), (FS[0] + 1.3, FS[1] + 0.5, 1.0))
m.collider((FS[0] - 1.32, FS[1] - 0.57, 0), (FS[0] - 1.18, FS[1] - 0.43, 2.3))
m.collider((FS[0] + 1.18, FS[1] - 0.57, 0), (FS[0] + 1.32, FS[1] - 0.43, 2.3))
m.collider((FS[0] - 1.4, FS[1] - 0.75, 2.3), (FS[0] + 1.4, FS[1] + 0.65, 2.65))         # stand roof
place(fp.farm_stand_awning, 'cloth', 'Stand Awning', (FS[0], FS[1] - 0.72, 2.27), 0.0, w=2.6)
place(fp.scarecrow, 'spin', 'Scarecrow', (22.5, 4.5, 0), 0.4, seed=1)
place(fp.scarecrow, 'spin', 'Scarecrow', (28.5, -7.0, 0), PI + 0.5, hat='felt', seed=2, shirt=M.denim)
place(fp.jack_o_lantern, 'flame', "Jack-o'-Lantern", (18.4, 5.85, 0.95), 0.2, face=2, r=0.2, light=0.7)
place(fp.jack_o_lantern, 'flame', "Jack-o'-Lantern", (17.4, -0.9, 0), -0.3, face=0, key='jack0')
fp.pumpkin(G(25, 2), M, (24.8, 2.0, 0), 0.26, 0.4)
place(fp.jack_o_lantern, 'flame', "Jack-o'-Lantern", (29.4, -0.4, 0), 0.9, face=0, light=0.9)
place(fp.jack_o_lantern, 'flame', "Jack-o'-Lantern", (25.6, -12.6, 0), 0.0, face=2, key='jack2')
place(fp.prize_pumpkin, 'jolt', 'Prize Pumpkin', (25.5, -4.5, 0), -0.4)
put(fp.wagon, (31.0, 5.0, 0), -0.25, load='pumpkins', seed=7)
place(fp.wheelbarrow, 'jolt', 'Wheelbarrow', (21.0, -8.6, 0), 0.9, load='pumpkins', seed=4)
place(fp.hay_bale, 'jolt', 'Hay Bale', (17.4, 5.0, 0), 1.3, key='bale')
fp.hay_bale_geo(G(33, 1), M, (33.2, 1.5, 0), 0.2)
m.collider((32.65, 1.15, 0), (33.75, 1.85, 0.44))
for (x, y, a) in ((18.0, 9.3, 0.0),):
    place(fp.crow, 'bob', 'Crow', (x, y, 1.18), a, key='crow')
place(fp.corn_shock, 'foliage', 'Corn Shock', (33.4, -9.8, 0), 0.8, key='shock')

# withered sunflowers divide the patch from the mill field
for (x, y, n) in ((18.5, -12.6, 5), (30.0, -12.6, 6)):
    place(fp.sunflowers, 'foliage', 'Sunflowers', (x, y, 0), 0.0, n=n, seed=int(x))

tufts(25, -2, 10, 55, seed=11)

# ============================================================================ WINDMILL & POND (SE)
WM = (28.2, -25.0)
WROT = -3 * PI / 4


def windmill_static(g, M):
    g.cyl((0, 0, 0), 3.0, 0.45, M.stone, n=8, smooth=False, rz=PI / 8)
    g.lathe((0, 0, 0.45), [(2.65, 0), (1.85, 7.4)], M.weathered, n=8, smooth=False, rz=PI / 8)
    for z in (2.6, 5.2):
        r = 2.65 - (2.65 - 1.85) * z / 7.4
        g.cyl((0, 0, z), r + 0.06, 0.12, M.wood_dk, n=8, smooth=False, rz=PI / 8)
    # reefing stage: ring of planks with a rail
    g.cyl((0, 0, 2.3), 3.1, 0.1, M.wood_mid, n=16, smooth=False)
    for i in range(16):
        a = TAU * i / 16
        g.box((math.cos(a) * 3.05, math.sin(a) * 3.05, 2.8), (0.06, 0.06, 0.95), M.wood_dk)
        g.box((math.cos(a) * 2.55, math.sin(a) * 2.55, 1.95), (1.15, 0.08, 0.08), M.wood_dk, rz=a, ry=-0.5)
    g.torus((0, 0, 3.25), 3.05, 0.04, M.wood_dk, n=24, m=4)
    # cap
    g.lathe((0, 0, 7.75), [(2.05, 0), (2.1, 0.5), (1.7, 1.4), (0.9, 2.1), (0.1, 2.3)], M.barn_roof, n=12, smooth=False)
    g.cyl((0, 0, 7.6), 2.0, 0.2, M.paint_white, n=12, smooth=False)
    g.box((0, -1.95, 8.55), (0.5, 1.0, 0.5), M.wood_dk)
    # windows and door frame on the front faces
    for (a, z) in ((0.0, 4.6), (PI * 0.75, 5.6), (-PI * 0.75, 3.8), (PI / 2, 6.2)):
        r = 2.65 - (2.65 - 1.85) * (z - 0.45) / 7.4
        with g.at((0, 0, 0), a):
            g.box((0, -r * 0.93, z), (0.6, 0.12, 0.8), M.window_glow_dim if a == 0.0 else M.window_dark)
            g.box((0, -r * 0.95, z - 0.45), (0.8, 0.16, 0.08), M.paint_white)
    g.box((0, -2.43, 1.55), (1.3, 0.1, 2.2), M.wood_dk)
    g.box((0, -2.5, 2.7), (1.5, 0.12, 0.14), M.paint_white)
    for sx in (-1, 1):
        g.box((sx * 0.7, -2.5, 1.55), (0.14, 0.12, 2.2), M.paint_white)
    g.box((0, -3.25, 0.15), (1.6, 0.6, 0.3), M.stone, bevel=0.02)


gwm = G(*WM)
with gwm.at((WM[0], WM[1], 0), WROT):
    windmill_static(gwm, M)
round_collider(WM[0], WM[1], 2.95, 0, 9.5)
sx_, sy_ = rot(0, -3.25, WROT)
m.collider((WM[0] + sx_ - 0.8, WM[1] + sy_ - 0.8, 0), (WM[0] + sx_ + 0.8, WM[1] + sy_ + 0.8, 0.3))


def wm_local(x, y):
    dx, dy = rot(x, y, WROT)
    return WM[0] + dx, WM[1] + dy


hx_, hy_ = wm_local(0, -2.15)
place(fp.windmill_sails, 'spin', 'Windmill Sails', (hx_, hy_, 8.8), WROT, R=5.15)
dx_, dy_ = wm_local(-0.6, -2.52)
place(fp.plank_door, 'hinge', 'Mill Door', (dx_, dy_, 0.45), WROT, w=1.2, h=2.05, ext=1, rest=0.35, mat=M.barn_red)
lx_, ly_ = wm_local(1.5, -3.4)
place(fp.lantern_post, 'flame', 'Mill Lantern', (lx_, ly_, 0), key='lpost')
sx2, sy2 = wm_local(-1.5, -3.3)
put_prop_static(fp.feed_sacks, (sx2, sy2, 0), WROT, n=3, seed=4)
bx_, by_ = wm_local(2.9, -1.9)
place(fp.bell_post, 'bell', 'Mill Bell', (bx_, by_, 0), WROT, h=2.2, r=0.17, tone=700)

POND = (19.0, -27.6)
pond_poly = fp.blob_poly(POND[0], POND[1], 4.3, 3.1, n=20, seed=8, jitter=0.12)
gpd = G(*POND)
gpd.add(fp.prim_poly(fp.blob_poly(POND[0], POND[1], 4.9, 3.6, n=20, seed=8, jitter=0.12), 0.008), M.dirt)
gpd.add(fp.prim_poly(pond_poly, 0.016), M.water)
for i in range(24):                                                       # rocks around the rim
    a = TAU * i / 24 + RNG.uniform(-0.1, 0.1)
    if 1.0 < a < 1.9:
        continue
    k = 1.08 + RNG.uniform(-0.05, 0.08)
    gpd.blob((POND[0] + math.cos(a) * 4.3 * k, POND[1] + math.sin(a) * 3.1 * k, 0.02), RNG.uniform(0.12, 0.35),
             M.millstone, seed=i, jitter=0.3, subdiv=0, s=(1.3, 1, 0.55))
# dock from the north shore
with gpd.at((20.3, -24.0, 0)):
    gpd.box((0, -1.6, 0.3), (1.4, 3.6, 0.08), M.weathered)
    for sy in (-3.2, -1.6, 0.0):
        for sx in (-0.65, 0.65):
            gpd.cyl((sx, sy, -0.1), 0.07, 0.55, M.wood_dk, n=6)
m.collider((19.6, -27.4, 0), (21.0, -23.8, 0.34))
place(fp.rowboat, 'rock', 'Rowboat', (18.4, -28.3, 0.32), 0.25)
place(fp.duck, 'bob', 'Duck', (16.6, -26.6, 0.0), 0.8, key='drake', drake=True)
place(fp.duck, 'bob', 'Duck', (17.1, -29.5, 0.0), 2.4, drake=False)
place(fp.cattails, 'foliage', 'Cattails', (15.2, -28.8, 0), 0.0, key='cattails', seed=2)
place(fp.cattails, 'foliage', 'Cattails', (22.9, -30.2, 0), 1.3, key='cattails')
gpd.sphere((21.8, -27.9, 0.03), 0.03, M.apple, n=6)
gpd.tube([(20.9, -26.6, 0.38), (21.4, -27.0, 1.6), (21.9, -27.6, 2.2)], 0.012, M.wood_light, n=4)
gpd.tube([(21.9, -27.6, 2.2), (21.85, -27.8, 1.0), (21.8, -27.9, 0.08)], 0.002, M.cloth_white, n=3, caps=False)
fp.bucket_geo(gpd, M, (20.0, -24.6, 0.34), 0.13, 0.24, water=True)
tufts(19, -27.6, 6.5, 36, seed=12)
tufts(28, -25, 7, 25, seed=13)

# ============================================================================ COOP & THE CHICKEN RUN (penalty)
CX0, CX1, CY0, CY1 = 9.1, 13.1, -17.0, -13.0      # cage interior
CH = 2.6


def build_cage():
    g = G(11, -15)
    wt = 0.2
    xa, xb, ya, yb = CX0 - wt, CX1 + wt, CY0 - wt, CY1 + wt
    for (x, y) in ((xa + 0.1, ya + 0.1), (xb - 0.1, ya + 0.1), (xa + 0.1, yb - 0.1), (xb - 0.1, yb - 0.1),
                   ((xa + xb) / 2, ya + 0.1), ((xa + xb) / 2, yb - 0.1), (xb - 0.1, (ya + yb) / 2)):
        g.box((x, y, CH / 2 + 0.05), (0.14, 0.14, CH + 0.1), M.grey_wood)
    # plank skirt + wire mesh on the three open sides
    for side in ('S', 'N', 'E'):
        if side in 'SN':
            y = ya + 0.1 if side == 'S' else yb - 0.1
            g.box(((xa + xb) / 2, y, 0.25), (xb - xa, 0.05, 0.5), M.barn_in)
            x = xa + 0.2
            while x < xb - 0.1:
                g.box((x, y, 1.55), (0.012, 0.012, 2.1), M.iron)
                x += 0.19
            for z in [0.5 + 0.16 * k for k in range(14)]:
                g.box(((xa + xb) / 2, y, z), (xb - xa, 0.012, 0.012), M.iron)
            g.box(((xa + xb) / 2, y, CH), (xb - xa, 0.1, 0.1), M.grey_wood)
        else:
            x = xb - 0.1
            g.box((x, (ya + yb) / 2, 0.25), (0.05, yb - ya, 0.5), M.barn_in)
            y = ya + 0.2
            while y < yb - 0.1:
                g.box((x, y, 1.55), (0.012, 0.012, 2.1), M.iron)
                y += 0.19
            for z in [0.5 + 0.16 * k for k in range(14)]:
                g.box((x, (ya + yb) / 2, z), (0.012, yb - ya, 0.012), M.iron)
            g.box((x, (ya + yb) / 2, CH), (0.1, yb - ya, 0.1), M.grey_wood)
    # lid: wire grid with a tin roof over the coop half
    for k in range(18):
        g.box((xa + 0.15 + k * (xb - xa - 0.3) / 17, (ya + yb) / 2, CH + 0.06), (0.012, yb - ya, 0.012), M.iron)
    for k in range(18):
        g.box(((xa + xb) / 2, ya + 0.15 + k * (yb - ya - 0.3) / 17, CH + 0.06), (xb - xa, 0.012, 0.012), M.iron)
    g.box(((xa + xb) / 2, (ya + yb) / 2, CH + 0.02), (0.1, yb - ya, 0.08), M.grey_wood)
    g.box((xa + 0.9, (ya + yb) / 2, CH + 0.18), (1.9, yb - ya + 0.3, 0.04), M.rust, ry=0.08)
    # inside: straw, roost ladder, a few hens
    g.box(((xa + xb) / 2, (ya + yb) / 2, 0.012), (CX1 - CX0, CY1 - CY0, 0.012), M.hay)
    with g.at((CX1 - 0.6, CY1 - 0.4, 0), 0.0):
        fp.ladder_geo(g, M, 1.6, w=0.6, lean=0.6)
    for (x, y, z, a) in ((CX1 - 0.6, CY1 - 0.62, 0.9, 0.0), (CX0 + 0.5, CY0 + 0.6, 0.0, 1.0),
                         (CX0 + 0.9, CY1 - 0.5, 0.0, 2.5)):
        with g.at((x, y, z), a):
            g.sphere((0, 0, 0.2), 0.15, M.cloth_white if a else M.wood_mid, n=8, s=(0.8, 1.2, 0.95))
            g.sphere((0, -0.15, 0.36), 0.07, M.cloth_white if a else M.wood_mid, n=6)
            g.box((0, -0.15, 0.45), (0.02, 0.07, 0.05), M.apple)
            g.cyl((0, -0.22, 0.35), 0.02, 0.05, M.straw, n=4, r2=0.002, rx=PI / 2)
            g.box((0, 0.17, 0.3), (0.12, 0.1, 0.16), M.cloth_white if a else M.wood_mid, rx=0.6)
    g.cyl((CX0 + 1.4, CY0 + 0.4, 0), 0.22, 0.06, M.tin, n=10)
    # colliders: walls on every side + lid
    m.collider((xa, ya, 0), (xb, ya + wt, 3.2))
    m.collider((xa, yb - wt, 0), (xb, yb, 3.2))
    m.collider((xa, ya, 0), (xa + wt, yb, 3.2))
    m.collider((xb - wt, ya, 0), (xb, yb, 3.2))
    m.collider((xa, ya, CH), (xb, yb, CH + 0.3))


def build_coop():
    g = G(7, -15)
    x0, x1, y0, y1 = 5.0, 8.9, -16.6, -13.4
    for sx in (x0 + 0.15, x1 - 0.15):
        for sy in (y0 + 0.15, y1 - 0.15):
            g.box((sx, sy, 0.3), (0.12, 0.12, 0.6), M.wood_dk)
    g.box(((x0 + x1) / 2, (y0 + y1) / 2, 0.62), (x1 - x0, y1 - y0, 0.06), M.weathered)
    wb = [(x0, y0, x1, y0 + 0.08), (x0, y1 - 0.08, x1, y1), (x0, y0, x0 + 0.08, y1), (x1 - 0.08, y0, x1, y1)]
    for (a, b, c, d) in wb:
        g.box(((a + c) / 2, (b + d) / 2, 1.5), (c - a, d - b, 1.8), M.barn_red)
    g.box(((x0 + x1) / 2, (y0 + y1) / 2, 1.5), (x1 - x0 - 0.16, y1 - y0 - 0.16, 1.78), M.wood_dk)
    for (x, y) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        g.box((x, y, 1.5), (0.14, 0.14, 1.85), M.paint_white)
    with g.at(((x0 + x1) / 2, (y0 + y1) / 2, 0), PI / 2):
        fp.slab(g, (-(y1 - y0) / 2 - 0.4, 2.35), ((y1 - y0) / 2 + 0.4, 2.65), x1 - x0 + 0.5, 0.06, M.rust, y=0)
    window(x0 + 3.0, y1, PI, 0.6, 1.3, 1.8, lit=True, curtains=False)
    window((x0 + x1) / 2 - 0.3, y0, 0.0, 0.6, 1.3, 1.8, lit=False)
    # pop-hole ramp on the west side
    with g.at((x0 - 0.75, -15.3, 0), 0.0):
        g.box((0, 0, 0.36), (1.6, 0.45, 0.04), M.weathered, ry=0.42)
        for k in range(6):
            g.box((-0.6 + k * 0.24, 0, 0.12 + 0.1 * k + 0.05), (0.03, 0.45, 0.03), M.wood_dk)
    g.box((x0 - 0.02, -15.3, 0.9), (0.04, 0.4, 0.42), M.wood_dk)
    # nest box bump-out on the south side
    g.box((6.5, y0 - 0.3, 1.1), (1.6, 0.6, 0.6), M.barn_red)
    m.collider((x0 - 0.1, y0 - 0.65, 0), (x1 + 0.2, y1 + 0.1, 2.75))
    m.collider((x0 - 1.6, -15.6, 0), (x0, -15.0, 0.75))


build_cage()
build_coop()
place(fp.plank_door, 'hinge', 'Coop Door', (6.25, -13.32, 0.62), PI, w=0.8, h=1.6, ext=1, rest=0.3, mat=M.paint_sage)


def nest_lid(p, M):
    pv = p.part('pivot', rx=0.0)
    g = pv.geo
    g.box((0, -0.32, -0.02), (1.7, 0.66, 0.05), M.rust, rx=-0.25)
    g.box((0, -0.62, -0.08), (0.2, 0.04, 0.04), M.iron)
    p.params.update(axis='x', dir=-1, closed=0, open=0.9, sound='bang')


place(nest_lid, 'hinge', 'Nest Box Lid', (6.5, -16.62, 1.43), 0.0)


def feeder(p, M):
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0, -0.5), 0.006, 0.5, M.iron, n=3)
    g.lathe((0, 0, -0.95), [(0.2, 0), (0.22, 0.04), (0.1, 0.06), (0.11, 0.42), (0.04, 0.47)], M.tin, n=12)
    p.params.update(axes='xz', amp=0.03, period=1.6, sound='clatter')


place(feeder, 'swing', 'Hanging Feeder', (12.1, -13.9, CH), 0.0)
place(fp.lantern_post, 'flame', 'Coop Lantern', (8.6, -12.5, 0), key='lpost')
place(fp.basket_prop, 'jolt', 'Egg Basket', (5.8, -12.8, 0), 0.3, kind='eggs', seed=4)
gco = G(7, -12)
for i in range(30):                                                       # scattered feed / straw
    gco.box((RNG.uniform(4.5, 9), RNG.uniform(-12.8, -11.8), 0.014), (0.1, 0.03, 0.005), M.straw, rz=RNG.uniform(0, 3))
tufts(7, -15, 5, 30, seed=14)

# ============================================================================ LAUNDRY YARD, GARDEN, OUTHOUSE (SW)
LINES = [
    ((-28.4, -10.0), 0.0, 6.4, [('sheet', -2.1, M.cloth_white), ('shirt', -0.6, M.gingham), ('pants', 0.4, M.denim),
                                ('shirt', 1.4, M.cloth_sage), ('socks', 2.5, M.cloth_rose)]),
    ((-28.0, -13.4), 0.0, 6.4, [('sheet', -2.1, M.cloth_white), ('sheet', -0.6, M.cloth_sage),
                                ('towel', 0.75, M.awning), ('dress', 2.1, M.cloth_rose)]),
    ((-28.6, -16.8), 0.0, 6.4, [('quilt', -2.0, M.quilt), ('shirt', -0.55, M.cloth_white), ('pants', 0.6, M.denim),
                                ('sheet', 2.15, M.cloth_white)]),
    ((-20.6, -12.2), PI / 2, 5.4, [('sheet', -1.6, M.cloth_white), ('shirt', -0.25, M.cloth_rose),
                                   ('towel', 0.75, M.gingham), ('socks', 1.8, M.cloth_sage)]),
]
for i, ((x, y), rz, L, items) in enumerate(LINES):
    place(fp.laundry_line, 'cloth', 'Laundry Line', (x, y, 0), rz, length=L, items=items, seed=i)
place(fp.basket_prop, 'jolt', 'Laundry Basket', (-25.6, -11.7, 0), 0.4, kind='laundry', seed=2)
place(fp.wash_tub, 'jolt', 'Wash Tub', (-22.7, -7.4, 0), 0.3)
place(fp.hand_pump, 'rock', 'Hand Pump', (-26.4, -6.4, 0), 0.2)
gla = G(-26, -8)
with gla.at((-25.3, -7.4, 0), 0.0):
    fp.trough(gla, M, length=1.4, col=False)
m.collider((-26.0, -7.75, 0), (-24.6, -7.05, 0.6))
# vegetable garden (picket fence: ghosts can hop it, hunters use the gate)
GX0, GX1, GY0, GY1 = -21.5, -14.0, -25.0, -17.5
put(fp.picket_fence, (GX0, GY0, 0), 0.0, length=GX1 - GX0)
put(fp.picket_fence, (GX0, GY1, 0), 0.0, length=2.5)
put(fp.picket_fence, (GX0 + 4.3, GY1, 0), 0.0, length=GX1 - GX0 - 4.3)
put(fp.picket_fence, (GX0, GY0, 0), PI / 2, length=GY1 - GY0)
put(fp.picket_fence, (GX1, GY0, 0), PI / 2, length=GY1 - GY0)
place(fp.farm_gate, 'hinge', 'Garden Gate', (GX0 + 2.5, GY1, 0), 0.0, w=1.8, h=1.0, ext=1, rest=1.6, key='gate3')
ggd = G(-18, -21)
for k, bx in enumerate((-19.6, -17.6, -15.6)):
    ggd.box((bx, -21.6, 0.13), (1.3, 5.6, 0.26), M.weathered)
    ggd.box((bx, -21.6, 0.265), (1.15, 5.45, 0.02), M.soil)
    for j in range(6):
        y = -24.0 + j * 0.95
        if k == 0:
            ggd.blob((bx + RNG.uniform(-0.2, 0.2), y, 0.38), 0.2, M.cabbage, seed=j, jitter=0.25, subdiv=1, s=(1, 1, 0.7))
        elif k == 1:
            fp.pumpkin(ggd, M, (bx + RNG.uniform(-0.2, 0.2), y, 0.27), RNG.uniform(0.12, 0.2), RNG.uniform(0, 6),
                       mat=M.leaf_gold if j % 2 else M.pumpkin)
        else:
            for q in range(3):
                fp.grass_tuft(ggd, M, (bx + RNG.uniform(-0.3, 0.3), y + RNG.uniform(-0.2, 0.2), 0.27), seed=j * 3 + q,
                              h=0.3, mats=[M.leaf_sage])
    m.collider((bx - 0.65, -24.4, 0), (bx + 0.65, -18.8, 0.28))
for (x, y) in ((-20.6, -18.2), (-15.0, -18.3)):                            # bean teepees
    for q in range(5):
        a = TAU * q / 5
        ggd.tube([(x + math.cos(a) * 0.45, y + math.sin(a) * 0.45, 0), (x, y, 2.0)], 0.02, M.wood_light, n=4)
    ggd.blob((x, y, 0.9), 0.45, M.leaf_olive, seed=int(x), jitter=0.3, subdiv=1, s=(0.8, 0.8, 1.9))
    m.collider((x - 0.4, y - 0.4, 0), (x + 0.4, y + 0.4, 2.0))
place(fp.sunflowers, 'foliage', 'Sunflowers', (-17.5, -24.55, 0), 0.0, n=5, seed=9)
with G(-17, -16).at((-17.3, -15.9, 0), -0.6):
    fp.wheelbarrow_geo(G(-17, -16), M, 'wood', 1)
m.collider((-17.9, -16.7, 0), (-16.7, -15.1, 0.7))
ggd.blob((-14.6, -27.0, 0.0), 1.2, M.soil, seed=6, jitter=0.25, subdiv=1, s=(1.4, 1.0, 0.5))      # compost heap
ggd.blob((-14.7, -26.9, 0.35), 0.5, M.leaf_orange, seed=7, jitter=0.3, subdiv=0, s=(1.6, 1.2, 0.5))
m.collider((-16.2, -28.0, 0), (-13.0, -26.0, 0.6))
# outhouse
OH = (-31.6, -29.2)
goh = G(*OH)
with goh.at((OH[0], OH[1], 0), PI / 2):
    goh.box((0, 0, 0.08), (1.6, 1.6, 0.16), M.stone)
    for (sx, sy, w, d) in ((0, 0.72, 1.5, 0.08), (-0.72, 0, 0.08, 1.5), (0.72, 0, 0.08, 1.5)):
        goh.box((sx, sy, 1.25), (w, d, 2.2), M.barn_in)
    goh.box((-0.58, -0.72, 1.25), (0.34, 0.08, 2.2), M.barn_in)
    goh.box((0.58, -0.72, 1.25), (0.34, 0.08, 2.2), M.barn_in)
    goh.box((0, -0.72, 2.3), (1.5, 0.08, 0.3), M.barn_in)
    goh.box((0, 0.0, 1.25), (1.36, 1.36, 2.1), M.wood_dk)
    goh.box((0, -0.05, 2.55), (1.9, 2.0, 0.08), M.rust, rx=0.18)
m.collider((OH[0] - 0.8, OH[1] - 0.8, 0), (OH[0] + 0.8, OH[1] + 0.8, 2.6))
place(fp.plank_door, 'hinge', 'Outhouse Door', (OH[0] + 0.78, OH[1] - 0.41, 0.16), PI / 2, w=0.82, h=2.0, ext=1,
      rest=0.25, moon=True)
place(fp.lantern_post, 'flame', 'Outhouse Lantern', (OH[0] + 1.7, OH[1] + 1.4, 0), key='lpost')
place(fp.crow, 'bob', 'Crow', (OH[0] + 0.3, OH[1] + 0.2, 2.72), 2.0, key='crow')
goh.box((OH[0] + 1.25, OH[1] - 1.2, 0.3), (0.5, 0.5, 0.6), M.wood_mid)                     # crate of corncobs
for k in range(5):
    goh.cyl((OH[0] + 1.1 + k * 0.07, OH[1] - 1.2, 0.6), 0.03, 0.14, M.straw, n=5, rx=PI / 2)
tufts(-28, -14, 8, 50, seed=15)
tufts(-30, -28, 5, 40, seed=16)
leaves(-26, -20, 7, 60, seed=17, mats=[M.leaf_gold, M.leaf_orange])

# ============================================================================ CREEK BANK & FOOTBRIDGE (S)
gcb = G(-3, -35)
BRX = -3.0
with gcb.at((BRX, -34.3, 0)):
    for k in range(18):                                                    # arched deck
        y = -k * 0.5
        z = 0.22 + 0.45 * math.sin(PI * k / 17)
        gcb.box((0, y - 0.25, z), (1.8, 0.48, 0.07), M.weathered, rx=0.0)
    for sx in (-1, 1):
        pts = [(sx * 0.9, -k * 0.5 - 0.25, 0.22 + 0.45 * math.sin(PI * k / 17) + 0.9) for k in range(18)]
        gcb.tube(pts, 0.035, M.wood_mid, n=5)
        for k in range(0, 18, 3):
            gcb.box((sx * 0.9, -k * 0.5 - 0.25, 0.22 + 0.45 * math.sin(PI * k / 17) + 0.45), (0.08, 0.08, 0.9), M.wood_mid)
    for k in (4, 9, 13):
        gcb.cyl((0, -k * 0.5 - 0.25, -0.8), 0.12, 1.0, M.wood_dk, n=6)
m.box((BRX, -34.6, 0.11), (1.8, 0.6, 0.22), M.weathered, col=True)
# the bridge gate is chained shut: nobody leaves the farm tonight
with gcb.at((BRX, -34.85, 0)):
    for sx in (-1, 1):
        gcb.box((sx * 1.0, 0, 0.7), (0.16, 0.16, 1.4), M.wood_dk, bevel=0.015)
    for i in range(4):
        gcb.box((0, 0, 0.35 + i * 0.28), (1.85, 0.05, 0.09), M.grey_wood)
    gcb.box((0, 0.0, 0.8), (2.1, 0.05, 0.09), M.grey_wood, ry=0.55)
    gcb.torus((0.85, -0.05, 0.9), 0.06, 0.012, M.iron, n=8, m=3, rx=PI / 2)
    gcb.tube([(0.8, -0.06, 0.95), (0.9, -0.08, 0.7), (0.98, -0.06, 0.95)], 0.01, M.iron, n=3)
    gcb.box((0.0, -0.06, 1.15), (0.6, 0.02, 0.3), M.wood_light, rz=0.06)
    gcb.box((-0.05, -0.08, 1.17), (0.4, 0.01, 0.06), M.leaf_red, rz=0.06)
m.collider((BRX - 1.1, -35.0, 0), (BRX + 1.1, -34.7, 1.5))
place(fp.mailbox, 'hinge', 'Mailbox', (BRX - 2.0, -33.9, 0), 0.0)
place(fp.lantern_post, 'flame', 'Bridge Lantern', (BRX + 1.6, -34.2, 0), key='lpost')
place(fp.cattails, 'foliage', 'Cattails', (-14.5, -34.4, 0), 0.6, key='cattails')

place(fp.fishing_bobber, 'bob', 'Fishing Bobber', (-9.6, -37.6, -0.35), 0.0, key='bobber')
with gcb.at((-10.2, -32.6, 0), PI + 0.1):
    fp.bench_geo(gcb, M, 1.5)
gcb.tube([(-10.9, -33.0, 0.45), (-10.6, -34.4, 1.3), (-9.8, -36.2, 1.9)], 0.012, M.wood_light, n=4)
gcb.tube([(-9.8, -36.2, 1.9), (-9.7, -37.0, 0.9), (-9.6, -37.6, -0.3)], 0.002, M.cloth_white, n=3, caps=False)
fp.bucket_geo(gcb, M, (-9.2, -32.9, 0), 0.14, 0.26, water=True)
gcb.cyl((4.0, -30.5, 0.28), 0.3, 4.5, M.bark, n=8, ry=PI / 2, smooth=False)                      # fallen log
gcb.blob((5.4, -30.6, 0.45), 0.4, M.moss, seed=3, jitter=0.3, subdiv=0, s=(1.6, 1, 0.4))
m.collider((4.0, -30.8, 0), (8.5, -30.2, 0.58))
gcb.cyl((10.8, -28.0, 0), 0.35, 0.45, M.bark, n=8, smooth=False)
gcb.cyl((10.8, -28.0, 0.45), 0.33, 0.01, M.wood_light, n=8)
m.collider((10.45, -28.35, 0), (11.15, -27.65, 0.45))
tufts_line((-34, -34.6), (34, -34.6), 90, seed=18, jitter=0.4)
for i in range(16):                                                       # reeds along the near bank
    x = RNG.uniform(-34, 34)
    if abs(x - BRX) < 2:
        continue
    with gcb.at((x, -35.4, -0.1)):
        for q in range(5):
            gcb.add(fp.prim_blade(RNG.uniform(0.7, 1.2), 0.04, up=2.0, droop=1.4, seg=2), M.reed,
                    fp._mat((RNG.uniform(-0.3, 0.3), RNG.uniform(-0.2, 0.2), 0), RNG.uniform(0, TAU)))

# hedge island + young trees between the coop and the laundry yard break the long E-W sightline
put(fp.hedge, (-8.5, -18.5, 0), 0.0, length=6.0, h=2.0, d=1.2, seed=21)
def young_maple(p, M, seed=0):
    pv = p.part('pivot')
    fp.tree_static(pv.geo, M, seed=seed, h=5.5, crown=2.0, leaves=[M.leaf_red, M.leaf_orange], subdiv=1)
    p.body.collide((0, 0, 1.5), (0.5, 0.5, 3.0))
    p.params.update(amp=0.02, leaf='#b8402a', sound='rustle')


for (x, y, s) in ((-12.5, -21.0, 1), (-5.0, -23.5, 2), (13.6, -21.2, 3), (13.6, 14.4, 4)):
    if s in (1, 2):
        place(young_maple, 'foliage', 'Young Maple', (x, y, 0), RNG.uniform(0, 3), seed=500 + s)
    else:
        g = G(x, y)
        with g.at((x, y, 0), RNG.uniform(0, 3)):
            fp.tree_static(g, M, seed=500 + s, h=5.5, crown=2.0, leaves=[M.leaf_red, M.leaf_orange], subdiv=1)
        m.collider((x - 0.25, y - 0.25, 0), (x + 0.25, y + 0.25, 3.0))
    leaves(x, y, 2.5, 55, seed=600 + s, mats=[M.leaf_red, M.leaf_orange])
place(fp.cattails, 'foliage', 'Cattails', (33.4, -34.3, 0), 1.1, key='cattails')
place(fp.cattails, 'foliage', 'Cattails', (7.6, -34.5, 0), 2.0, key='cattails')
place(fp.crow, 'bob', 'Crow', (35.25, -27.0, 1.2), PI / 2, key='crow')
place(fp.crow, 'bob', 'Crow', (6.3, -30.5, 0.58), 2.6, key='crow')
place(fp.crow, 'bob', 'Crow', (35.3, 12.3, 1.4), PI / 2 + 0.4, key='crow')
place(fp.bucket_prop, 'jolt', 'Bait Bucket', (3.35, -30.0, 0), 0.0)
place(fp.signpost, 'spin', 'Old Signpost', (-4.6, -13.2, 0), 0.3)

# ============================================================================ altars, spawns, lights, env
ALTARS = [(-31.5, 31.5, 0), (-3.5, 31.9, 0), (29.5, 27.55, 0), (-4.2, 18.6, LOFT_Z), (-27.0, 8.6, 0),
          (-32.0, -22.0, 0), (-22.5, -31.0, 0), (-8.6, -28.6, 0), (31.0, -31.0, 0), (31.0, -2.0, 0),
          (3.0, -22.0, 0), (12.4, 2.0, 0), (11.0, 17.0, 0)]
for (x, y, z) in ALTARS:
    m.flag_point((x, y, z), RNG.uniform(0, TAU), prefab=fp.altar, M=M)

for x in (-1.2, 0.0, 1.2):
    m.spawn('hunter', (x, -3.6, 0), face=(0, 1))
GHOSTS = [(-21.5, 26.5, 0), (-12.0, 30.5, 0), mz_cell(1, 3) + (0,), mz_cell(5, 6) + (0,), (26.5, -10.0, 0),
          (22.5, -19.0, 0), (8.0, -31.5, 0), (-27.0, -26.5, 0), (-23.5, -19.5, 0), (-33.0, -2.9, 0),
          (-3.6, 12.6, LOFT_Z), (4.6, 23.2, 0), (17.5, -22.5, 0)]
for (x, y, z) in GHOSTS:
    m.spawn('ghost', (x, y, z), face=(-x or 1, -y or 1))
for (x, y) in ((CX0 + 1.0, CY0 + 1.0), (CX1 - 1.0, CY0 + 1.0), (CX0 + 1.0, CY1 - 1.0), (CX1 - 1.0, CY1 - 1.0),
               ((CX0 + CX1) / 2, (CY0 + CY1) / 2)):
    m.penalty_spawn((x, y, 0))
m.penalty['label'] = 'The Chicken Run'

m.light((-24.3, -2.6, 2.9), '#ffc27a', 0.7, 6.0)                         # kitchen fill
m.env(
    sky='#3a3456',
    fog={'color': '#3b3a58', 'near': 16, 'far': 82},
    hemi={'sky': '#8784b6', 'ground': '#3b3024', 'intensity': 0.62},
    moon={'dir': [-0.55, -0.62, -0.42], 'color': '#b0bcff', 'intensity': 0.8, 'shadows': True},
    exposure=1.05,
    ambience='wind',
    stars=True,
    previewClip=2.45,
)

E = 1.65
m.preview((1.5, -12.0, E), (-1.0, 12.0, 3.0), name='yard')
m.preview((-11.0, -6.0, E), (-21.0, 0.0, 1.9), name='porch')
m.preview((0.8, 11.8, E), (-1.0, 27.0, 2.4), name='barn_in')
m.preview((-4.0, 25.0, LOFT_Z + E), (-4.5, 12.0, 2.6), name='loft')
m.preview((19.0, 9.5, E), (21.0, 22.0, 1.6), name='maze')
m.preview((17.0, -1.5, E), (31.0, -5.0, 1.0), name='patch')
m.preview((14.6, -12.4, E), (28.0, -25.0, 5.5), name='windmill')
m.preview((-17.0, -7.5, E), (-31.0, -16.0, 1.4), name='laundry')
m.preview((-12.0, 13.0, E), (-27.0, 27.0, 1.8), name='orchard')
m.preview((-22.6, -1.1, KZ + E), (-26.2, -4.4, 1.1), name='kitchen')
m.preview((1.4, -12.6, E), (11.0, -15.2, 1.2), name='coop')
m.preview((0.6, -4.6, E), (6.5, -9.8, 0.6), name='sty')
m.preview((27.6, 29.6, E), (31.0, 25.0, 1.2), name='maze_in')
m.preview((-12.5, 30.0, E), (6.0, 32.5, 1.2), name='backlane')
m.preview((-33.0, -4.5, E), (-33.0, 8.0, 1.4), name='house_west')
m.preview((-1.0, -25.0, E), (-3.0, -40.0, 0.4), name='creek')
m.preview((-48.0, -52.0, 34.0), (0.0, 0.0, 0.0), lens=26, name='aerial')
m.finish()
