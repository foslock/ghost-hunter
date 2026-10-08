"""Prefabs and textures for Hollowmere Manor (blender/maps/manor.py).

Static prefabs: fn(g, M, ...) draw into a Geo at its current transform. Origin is the floor point
under the object and the object faces -Y (south) unless stated; wall-mounted things have their
back on the wall plane (y = 0) and face -Y.
Prop prefabs: fn(p, M, ...) draw into prop parts and set archetype params.
M is the manor palette: a namespace of materials built in manor.py.
"""
import math
import random

import numpy as np
from mathutils import Matrix

from lib.gh import TAU
from lib import prefabs as pf
from lib import tex

PI = math.pi
HALF = PI / 2
WARM = '#ffb35c'
CANDLE = '#ffbf6e'


def jitter_rng(seed):
    return random.Random(seed)


# ======================================================================= textures

def _mask_ellipse(xx, yy, cx, cy, rx, ry):
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 < 1.0


def _soft_ellipse(xx, yy, cx, cy, rx, ry, soft=0.25):
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    return np.clip((1.0 - d) / soft, 0, 1)


def _put(img, mask, col, alpha=1.0):
    c = tex.hex_rgb(col) if isinstance(col, str) else np.asarray(col)
    m = (mask.astype(float) * alpha)[..., None]
    img[:] = img * (1 - m) + c * m


def _figure(cell, seed, bg, coat, skin='#c9a68a', hair='#2a1a12', collar='#d8ccb0', kind='man',
            accent=None, glow='#7a4a2a'):
    h, w = cell.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    yy /= h
    xx /= w
    n = tex.fbm((h, w), 5, 4, seed)
    # background: dark umber with a warm haze behind the sitter
    base = tex.hex_rgb(bg)
    img = base * (0.55 + 0.45 * (1 - yy))[..., None] * (0.85 + 0.3 * n)[..., None]
    halo = _soft_ellipse(xx, yy, 0.42, 0.38, 0.55, 0.45, 0.9)
    _put(img, halo, glow, 0.35)
    hx = 0.5
    if kind == 'hound':
        body = _mask_ellipse(xx, yy, 0.5, 1.0, 0.5, 0.42)
        _put(img, body, coat)
        head = _mask_ellipse(xx, yy, 0.5, 0.44, 0.17, 0.2)
        snout = _mask_ellipse(xx, yy, 0.5, 0.58, 0.09, 0.11)
        _put(img, head | snout, coat)
        shade = np.clip(0.5 + (0.5 - xx) * 1.4, 0, 1)
        _put(img, (head | snout) & (xx > 0.5), '#1a120c', 0.35)
        for sx in (-1, 1):
            ear = _mask_ellipse(xx, yy, 0.5 + sx * 0.17, 0.5, 0.06, 0.15)
            _put(img, ear, hair)
            eye = _mask_ellipse(xx, yy, 0.5 + sx * 0.065, 0.42, 0.022, 0.016)
            _put(img, eye, '#0c0806')
        _put(img, _mask_ellipse(xx, yy, 0.5, 0.66, 0.035, 0.022), '#0c0806')
        collar_band = (np.abs(yy - 0.74 - (xx - 0.5) ** 2 * 0.6) < 0.018) & body
        _put(img, collar_band, accent or '#8a2a22')
        del shade
    else:
        torso = _mask_ellipse(xx, yy, hx, 1.04, 0.47, 0.42)
        _put(img, torso, coat)
        # shoulder light from the left
        _put(img, torso & (xx > 0.55), '#000000', 0.25)
        neck = (np.abs(xx - hx) < 0.06) & (yy > 0.48) & (yy < 0.66)
        _put(img, neck, skin)
        _put(img, neck & (xx > hx), '#3a2418', 0.35)
        if kind in ('man', 'officer', 'tophat'):
            v = torso & (np.abs(xx - hx) < (yy - 0.6) * 0.55) & (yy < 0.86)
            _put(img, v, collar)
            _put(img, v & (np.abs(xx - hx) < 0.02) & (yy > 0.66), '#1a1414')  # cravat
        elif kind in ('lady', 'girl', 'widow'):
            yoke = torso & (yy < 0.7)
            _put(img, yoke, collar if kind == 'girl' else coat)
            lace = (np.abs(yy - 0.64) < 0.02) & (np.abs(xx - hx) < 0.09)
            _put(img, lace, '#d8ccb0' if kind != 'widow' else '#e6dcc6')
        if kind == 'officer':
            for sx in (-1, 1):
                ep = _mask_ellipse(xx, yy, hx + sx * 0.33, 0.7, 0.1, 0.04)
                _put(img, ep, '#b08a3e')
            for k in range(4):
                _put(img, _mask_ellipse(xx, yy, hx + 0.05, 0.76 + k * 0.05, 0.012, 0.009), '#c9a24a')
        # hair behind the head
        if kind in ('lady', 'widow'):
            _put(img, _mask_ellipse(xx, yy, hx, 0.36, 0.17, 0.2), hair)
            _put(img, _mask_ellipse(xx, yy, hx, 0.2, 0.08, 0.06), hair)  # bun
        elif kind == 'girl':
            _put(img, _mask_ellipse(xx, yy, hx, 0.4, 0.18, 0.24), hair)
            _put(img, (np.abs(xx - hx) < 0.19) & (yy > 0.4) & (yy < 0.64) & (np.abs(xx - hx) > 0.1), hair)
        head = _mask_ellipse(xx, yy, hx, 0.41, 0.13, 0.175)
        _put(img, head, skin)
        shade = head & (xx > hx + 0.02)
        _put(img, shade, '#3a2418', 0.35)
        if kind in ('man', 'officer'):
            _put(img, _mask_ellipse(xx, yy, hx, 0.27, 0.14, 0.08) & (yy < 0.31), hair)
            for sx in (-1, 1):  # side whiskers
                _put(img, _mask_ellipse(xx, yy, hx + sx * 0.12, 0.47, 0.035, 0.09), hair)
        if kind == 'tophat':
            _put(img, (np.abs(xx - hx) < 0.12) & (yy > 0.08) & (yy < 0.27), '#141012')
            _put(img, (np.abs(xx - hx) < 0.19) & (yy > 0.25) & (yy < 0.29), '#141012')
        if kind == 'widow':
            cap = _mask_ellipse(xx, yy, hx, 0.27, 0.16, 0.09) & (yy < 0.3)
            _put(img, cap, '#e6dcc6')
        if kind == 'girl':
            _put(img, _mask_ellipse(xx, yy, hx, 0.29, 0.14, 0.07) & (yy < 0.31), hair)  # fringe
            _put(img, _mask_ellipse(xx, yy, hx + 0.15, 0.27, 0.05, 0.035), accent or '#8a2a22')  # bow
        # hollow, watchful eyes
        for sx in (-1, 1):
            _put(img, _mask_ellipse(xx, yy, hx + sx * 0.048, 0.4, 0.024, 0.014), '#120a08')
            _put(img, _mask_ellipse(xx, yy, hx + sx * 0.048 - 0.006, 0.398, 0.006, 0.005), '#d8ccb0', 0.7)
        _put(img, _mask_ellipse(xx, yy, hx, 0.5, 0.03, 0.007), '#5a2a22', 0.8)
    # varnish: vignette, yellowing and brush noise
    vig = np.clip(1.0 - (((xx - 0.5) / 0.62) ** 2 + ((yy - 0.48) / 0.7) ** 2), 0, 1) ** 0.6
    img *= (0.35 + 0.65 * vig)[..., None]
    img *= (0.88 + 0.24 * tex.fbm((h, w), 24, 3, seed + 5))[..., None]
    img = img * np.array([1.0, 0.94, 0.8])
    cell[:] = np.clip(img, 0, 1)


def _landscape(cell, seed, kind='lake'):
    h, w = cell.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    yy /= h
    xx /= w
    n = tex.fbm((h, w), (4, 8), 5, seed)
    sky_top, sky_low = tex.hex_rgb('#0e1424'), tex.hex_rgb('#3a4a62')
    img = sky_top * (1 - yy[..., None]) + sky_low * yy[..., None]
    clouds = np.clip((n - 0.5) * 3, 0, 1) * (yy < 0.55)
    _put(img, clouds > 0.2, '#1a2234', 0.6)
    horizon = 0.55 + 0.06 * np.sin(xx * 9 + seed) + 0.05 * tex.value_noise((h, w), (2, 6), seed)[0][None, :]
    if kind == 'lake':
        moon = _soft_ellipse(xx, yy, 0.72, 0.2, 0.05, 0.068, 0.15)
        _put(img, moon > 0, '#e8e2c8')
        _put(img, _soft_ellipse(xx, yy, 0.72, 0.2, 0.18, 0.24, 1.0), '#8a96a8', 0.25)
        hills = yy > horizon
        _put(img, hills, '#10140f')
        water = yy > 0.66
        refl = sky_top * 0.7 + sky_low * 0.2
        img[water] = refl + 0.05 * n[water][..., None]
        streak = water & (np.abs(xx - 0.72) < 0.03 + 0.02 * np.sin(yy * 90)) & (np.sin(yy * 120) > -0.2)
        _put(img, streak, '#c8ccc0', 0.7)
        # the manor on the hill, one window lit
        house = (np.abs(xx - 0.3) < 0.08) & (yy > 0.5) & (yy < horizon + 0.02)
        roof = (np.abs(xx - 0.3) < 0.08 - (0.5 - yy) * 1.4) & (yy > 0.44) & (yy <= 0.5)
        tower = (np.abs(xx - 0.36) < 0.015) & (yy > 0.4) & (yy < 0.5)
        _put(img, house | roof | tower, '#06070a')
        _put(img, (np.abs(xx - 0.27) < 0.008) & (np.abs(yy - 0.54) < 0.012), '#ffcf7a')
    else:
        sea = yy > 0.6
        waves = 0.5 + 0.5 * np.sin(xx * 40 + np.sin(yy * 30) * 3 + n * 6)
        img[sea] = (tex.hex_rgb('#16222a') * (0.6 + 0.6 * waves[sea])[..., None])
        crest = sea & (waves > 0.93)
        _put(img, crest, '#8a9a9a', 0.6)
        hull = (yy > 0.53) & (yy < 0.6) & (np.abs(xx - 0.4) < 0.12 - (yy - 0.53) * 0.8)
        mast = (np.abs(xx - 0.36) < 0.006) & (yy > 0.25) & (yy < 0.55)
        mast2 = (np.abs(xx - 0.46) < 0.005) & (yy > 0.32) & (yy < 0.55)
        sails = ((xx > 0.37) & (xx < 0.37 + (yy - 0.27) * 0.4) & (yy > 0.27) & (yy < 0.5))
        _put(img, hull | mast | mast2, '#0a0806')
        _put(img, sails, '#5a5a4a', 0.8)
        bolt = (np.abs(xx - 0.8 - np.sin(yy * 30) * 0.02) < 0.004) & (yy < 0.5) & (yy > 0.05)
        _put(img, bolt, '#d8dcff', 0.8)
    vig = np.clip(1.0 - (((xx - 0.5) / 0.7) ** 2 + ((yy - 0.5) / 0.75) ** 2), 0, 1) ** 0.5
    img *= (0.45 + 0.55 * vig)[..., None]
    img *= (0.9 + 0.2 * tex.fbm((h, w), (16, 32), 3, seed + 3))[..., None]
    img = img * np.array([1.0, 0.95, 0.82])
    cell[:] = np.clip(img, 0, 1)


ATLAS_UV = 3.2          # material uv scale: one atlas cell is 0.8 m x 1.0667 m at k = 1
ATLAS_CW = ATLAS_UV / 4
ATLAS_CH = ATLAS_UV / 3

# (col, row-from-bottom, span) cells of the portrait atlas
ART = {
    'lord': (0, 2, 1), 'lady': (1, 2, 1), 'girl': (2, 2, 1), 'colonel': (3, 2, 1),
    'widow': (0, 1, 1), 'heir': (1, 1, 1), 'lake': (2, 1, 2),
    'hound': (0, 0, 1), 'uncle': (1, 0, 1), 'sea': (2, 0, 2),
}


def portrait_atlas():
    """4 x 3 atlas of 192 x 256 px cells (portrait aspect 3:4); landscapes span two cells."""
    cw, ch = 192, 256
    img = np.zeros((ch * 3, cw * 4, 3))

    def cell(name):
        c, r, span = ART[name]
        row = 2 - r
        return img[row * ch:(row + 1) * ch, c * cw:(c + span) * cw]
    _figure(cell('lord'), 11, '#3a1414', '#141012', hair='#c8c0b0', kind='man', glow='#6a3a22')
    _figure(cell('lady'), 12, '#1e1a22', '#4a2440', hair='#1a100c', kind='lady', glow='#5a3a4a', skin='#d8bca4')
    _figure(cell('girl'), 13, '#22261e', '#d8d0c0', hair='#1a120e', collar='#e6dcc6', kind='girl', glow='#4a5a4a', skin='#e0c8b8')
    _figure(cell('colonel'), 14, '#1c1814', '#7a1c18', hair='#5a4a3a', kind='officer', glow='#6a4a2a')
    _figure(cell('widow'), 15, '#14120f', '#141214', hair='#8a8478', kind='widow', glow='#3a3a30', skin='#cfb8a0')
    _figure(cell('heir'), 16, '#2a2014', '#2e3a22', hair='#5a3a1e', kind='man', glow='#7a5a2a', skin='#d4b090')
    _figure(cell('hound'), 17, '#262014', '#6a4a2e', hair='#3a2414', kind='hound', glow='#7a5a32')
    _figure(cell('uncle'), 18, '#1a1c22', '#1e1e24', hair='#3a3030', kind='tophat', glow='#4a4a5a', skin='#c0a088')
    _landscape(cell('lake'), 19, 'lake')
    _landscape(cell('sea'), 20, 'sea')
    return img


def damask_floral(size=512, bg='#4a1820', fg='#6e2a30', seed=21):
    """Larger-scale damask: mirrored flame/leaf medallions on a dusty ground."""
    h = w = size
    yy, xx = np.mgrid[0:h, 0:w].astype(float) / size
    img = np.broadcast_to(tex.hex_rgb(bg), (h, w, 3)).copy()
    for (ox, oy) in ((0.0, 0.0), (0.5, 0.5)):
        ux = ((xx + ox) % 1.0) - 0.5
        uy = ((yy + oy) % 1.0) - 0.5
        ax = np.abs(ux)
        # flame-shaped medallion: teardrop + side leaves + small diamonds
        drop = (ax * 2.4) ** 2 + ((uy + 0.04) * 1.5) ** 2 * (1.0 + 2.5 * np.clip(-uy, 0, 1)) < 0.06
        inner = (ax * 2.4) ** 2 + ((uy + 0.04) * 1.5) ** 2 * (1.0 + 2.5 * np.clip(-uy, 0, 1)) < 0.025
        leaf = ((ax - 0.13) ** 2 * 30 + (uy - 0.08 + (ax - 0.13) * 0.8) ** 2 * 120) < 0.12
        stem = (ax < 0.006) & (uy > 0.12) & (uy < 0.24)
        dia = (np.abs(ux) + np.abs(uy - 0.32)) < 0.035
        m = (drop & ~inner) | leaf | stem | dia | ((ax * 2.4) ** 2 + (uy + 0.02) ** 2 < 0.0012)
        img[m] = tex.hex_rgb(fg)
    n = tex.fbm((h, w), 6, 4, seed)
    img *= (0.84 + 0.3 * n)[..., None]
    return np.clip(img, 0, 1)


def parquet(size=512, a='#4a2e1c', b='#3a2214', seed=22, n=8):
    """Herringbone-ish basketweave parquet blocks."""
    h = w = size
    yy, xx = np.mgrid[0:h, 0:w].astype(float) / size * n
    cx, cy = np.floor(xx).astype(int), np.floor(yy).astype(int)
    fx, fy = xx - cx, yy - cy
    horiz = (cx + cy) % 2 == 0
    strip = np.where(horiz, np.floor(fy * 3), np.floor(fx * 3)).astype(int)
    rng = np.random.default_rng(seed)
    tint = rng.uniform(-0.12, 0.12, (n, n, 3))
    grain = tex.fbm((h, w), (n * 3, n * 3), 3, seed + 1)
    t = 0.5 + tint[cy % n, cx % n, strip % 3] + (grain - 0.5) * 0.5
    img = tex.hex_rgb(b) * (1 - t[..., None]) + tex.hex_rgb(a) * t[..., None]
    seam = np.where(horiz, (fy * 3) % 1.0, (fx * 3) % 1.0)
    edge = (seam < 0.05) | (fx < 0.015) | (fy < 0.015)
    img[edge] *= 0.55
    return np.clip(img, 0, 1)


def panelling(size=512, base='#3a2416', dark='#1e120a', light='#5a3a24', seed=23, cols=2, rows=2):
    """Raised-and-fielded walnut panels: tiles of bevelled rectangles."""
    h = w = size
    yy, xx = np.mgrid[0:h, 0:w].astype(float) / size
    fx = (xx * cols) % 1.0
    fy = (yy * rows) % 1.0
    grain = tex.value_noise((h, w), (2, 40), seed)
    n = tex.fbm((h, w), 6, 4, seed + 1)
    img = tex.hex_rgb(base) * (0.85 + 0.25 * grain + 0.15 * (n - 0.5))[..., None]
    rail = (fx < 0.09) | (fx > 0.91) | (fy < 0.09) | (fy > 0.91)
    img[rail] = (tex.hex_rgb(dark) * 0.6 + tex.hex_rgb(base) * 0.4) * (0.9 + 0.2 * n[rail])[..., None]
    bev_l = (fx >= 0.09) & (fx < 0.13) & (fy > 0.09) & (fy < 0.91)
    bev_t = (fy >= 0.09) & (fy < 0.13) & (fx > 0.09) & (fx < 0.91)
    bev_r = (fx > 0.87) & (fx <= 0.91) & (fy > 0.09) & (fy < 0.91)
    bev_b = (fy > 0.87) & (fy <= 0.91) & (fx > 0.09) & (fx < 0.91)
    img[bev_l | bev_t] = tex.hex_rgb(light)
    img[bev_r | bev_b] = tex.hex_rgb(dark)
    return np.clip(img, 0, 1)


def encaustic(size=512, a='#8a4a32', b='#c8b89a', c='#2a2624', seed=24, tiles=4):
    """Victorian encaustic floor: quatrefoil-in-square tiles."""
    h = w = size
    yy, xx = np.mgrid[0:h, 0:w].astype(float) / size * tiles
    fx, fy = xx % 1.0 - 0.5, yy % 1.0 - 0.5
    img = np.broadcast_to(tex.hex_rgb(b), (h, w, 3)).copy()
    diamond = (np.abs(fx) + np.abs(fy)) < 0.42
    img[diamond] = tex.hex_rgb(a)
    petals = np.zeros_like(diamond)
    for px, py in ((0.16, 0), (-0.16, 0), (0, 0.16), (0, -0.16)):
        petals |= (fx - px) ** 2 + (fy - py) ** 2 < 0.012
    img[petals] = tex.hex_rgb(c)
    img[(fx ** 2 + fy ** 2) < 0.004] = tex.hex_rgb(b)
    grout = (np.abs(fx) > 0.485) | (np.abs(fy) > 0.485)
    n = tex.fbm((h, w), 8, 4, seed)
    img *= (0.82 + 0.3 * n)[..., None]
    img[grout] *= 0.5
    return np.clip(img, 0, 1)


# ======================================================================= small helpers

def turned_leg(g, pos, h, r, mat, n=6):
    g.lathe(pos, [(r * 0.75, 0), (r, h * 0.06), (r * 0.6, h * 0.18), (r * 1.05, h * 0.42),
                  (r * 0.65, h * 0.68), (r * 0.9, h * 0.88), (r, h)], mat, n=n)


def candle(g, M, pos, h=0.16, r=0.018):
    g.cyl(pos, r, h, M.wax, n=8)
    g.sphere((pos[0] + r * 0.6, pos[1], pos[2] + h * 0.75), r * 0.35, M.wax, n=5, s=(1, 1, 2.2))


def book(g, M, pos, w=0.2, d=0.28, t=0.05, rz=0.0, mat=None, open_=False):
    mat = mat or M.books[0]
    if open_:
        with g.at(pos, rz):
            for sx in (-1, 1):
                g.box((sx * w / 2, 0, 0.012), (w, d, 0.024), mat, ry=-sx * 0.06)
                g.box((sx * w / 2, 0, 0.03), (w - 0.02, d - 0.02, 0.014), M.paper, ry=-sx * 0.06)
        return
    with g.at(pos, rz):
        g.box((0, 0, t / 2), (w, d, t), mat)


def plate(g, M, pos, r=0.13, mat=None):
    g.lathe(pos, [(r * 0.55, 0), (r * 0.6, 0.008), (r, 0.018)], mat or M.porcelain, n=12, cap_top=False)


def goblet(g, M, pos, mat=None, tipped=False):
    mat = mat or M.glass_dark
    prof = [(0.035, 0), (0.006, 0.02), (0.005, 0.09), (0.03, 0.11), (0.042, 0.18)]
    if tipped:
        g.lathe((pos[0], pos[1], pos[2] + 0.04), prof, mat, n=8, rx=HALF, cap_top=False)
    else:
        g.lathe(pos, prof, mat, n=8, cap_top=False)


def bottle(g, M, pos, h=0.3, r=0.04, mat=None, rx=0.0, rz=0.0):
    mat = mat or M.glass_dark
    g.lathe(pos, [(r * 0.9, 0), (r, 0.01), (r, h * 0.6), (r * 0.4, h * 0.78), (r * 0.3, h * 0.95), (r * 0.36, h)], mat, n=10, rx=rx, rz=rz)


def jar(g, M, pos, h, r, mat, lid=None):
    g.lathe(pos, [(r * 0.8, 0), (r, h * 0.15), (r, h * 0.8), (r * 0.75, h)], mat, n=7)
    if lid is not None:
        g.cyl((pos[0], pos[1], pos[2] + h), r * 0.8, 0.02, lid, n=7)


def frame_rect(g, c, w, h, bar, depth, mat, bevel=0.0):
    """Rectangular picture/mirror frame in the XZ plane centred at c (face towards -Y)."""
    x, y, z = c
    g.box((x, y, z + h / 2 - bar / 2), (w, depth, bar), mat, bevel=bevel)
    g.box((x, y, z - h / 2 + bar / 2), (w, depth, bar), mat, bevel=bevel)
    for sx in (-1, 1):
        g.box((x + sx * (w / 2 - bar / 2), y, z), (bar, depth, h - 2 * bar + 0.002), mat, bevel=bevel)


# ======================================================================= static furniture

def settee(g, M, fabric, w=1.9, wood=None):
    wood = wood or M.walnut
    d = 0.8
    for sx in (-1, 1):
        for sy in (-1, 1):
            turned_leg(g, (sx * (w / 2 - 0.1), sy * (d / 2 - 0.1), 0), 0.2, 0.035, wood)
    g.box((0, 0, 0.25), (w, d, 0.1), wood, bevel=0.02)
    g.box((0, -0.02, 0.37), (w - 0.06, d - 0.06, 0.16), fabric, bevel=0.04)
    g.box((0, -0.07, 0.48), (w - 0.38, d - 0.24, 0.1), fabric, bevel=0.04)
    g.box((0, d / 2 - 0.12, 0.68), (w - 0.12, 0.17, 0.52), fabric, bevel=0.05, rx=-0.12)
    g.box((0, d / 2 - 0.09, 0.97), (w * 0.42, 0.15, 0.18), fabric, bevel=0.06, rx=-0.12)
    pts = [(-w / 2 + 0.08, d / 2 - 0.03, 0.9), (-w * 0.25, d / 2 - 0.03, 0.96), (0, d / 2 - 0.02, 1.08),
           (w * 0.25, d / 2 - 0.03, 0.96), (w / 2 - 0.08, d / 2 - 0.03, 0.9)]
    g.tube(pts, 0.022, wood, n=6)
    for i in range(5):  # buttons
        g.sphere((-w * 0.32 + i * w * 0.16, d / 2 - 0.215, 0.78), 0.018, M.brass, n=5)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.09), -0.02, 0.52), (0.16, d - 0.1, 0.3), fabric, bevel=0.03)
        g.cyl((sx * (w / 2 - 0.09), d / 2 - 0.08, 0.67), 0.1, d - 0.12, fabric, n=10, rx=HALF)
        g.cyl((sx * (w / 2 - 0.09), -d / 2 + 0.05, 0.67), 0.075, 0.012, wood, n=10, rx=HALF)
    g.collide((0, 0, 0.45), (w, d, 0.9))


def armchair_geo(g, M, fabric, wood=None):
    wood = wood or M.walnut
    w, d = 0.86, 0.82
    for sx in (-1, 1):
        for sy in (-1, 1):
            turned_leg(g, (sx * (w / 2 - 0.08), sy * (d / 2 - 0.08), 0), 0.16, 0.032, wood)
    g.box((0, 0, 0.26), (w, d, 0.2), fabric, bevel=0.04)
    g.box((0, -0.06, 0.4), (w - 0.28, d - 0.24, 0.1), fabric, bevel=0.04)
    g.box((0, d / 2 - 0.09, 0.78), (w - 0.04, 0.16, 0.82), fabric, bevel=0.06, rx=-0.1)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.07), d / 2 - 0.27, 0.9), (0.12, 0.36, 0.5), fabric, bevel=0.05)
        g.box((sx * (w / 2 - 0.07), -0.04, 0.48), (0.14, d - 0.14, 0.26), fabric, bevel=0.04)
        g.cyl((sx * (w / 2 - 0.07), d / 2 - 0.12, 0.6), 0.075, d - 0.2, fabric, n=10, rx=HALF)


def side_table(g, M, r=0.3, h=0.68, wood=None, col=True):
    wood = wood or M.walnut
    g.lathe((0, 0, 0.06), [(0.05, 0), (0.04, 0.12), (0.06, 0.24), (0.03, 0.4), (0.045, h - 0.1), (0.06, h - 0.06)], wood, n=10)
    for i in range(3):
        a = i * TAU / 3
        g.tube([(0, 0, 0.12), (math.cos(a) * 0.12, math.sin(a) * 0.12, 0.06), (math.cos(a) * 0.22, math.sin(a) * 0.22, 0.015)], 0.022, wood, n=5)
    g.cyl((0, 0, h - 0.035), r, 0.035, wood, n=20)
    g.torus((0, 0, h - 0.02), r, 0.012, wood, n=20, m=4)
    if col:
        g.collide((0, 0, h / 2), (r * 1.5, r * 1.5, h))


def round_table(g, M, r=0.9, h=0.78, wood=None, top=None):
    wood = wood or M.walnut
    g.lathe((0, 0, 0), [(0.45, 0), (0.42, 0.06), (0.16, 0.14), (0.11, 0.3), (0.16, 0.42), (0.09, 0.58), (0.14, h - 0.08), (0.2, h - 0.05)], wood, n=12)
    for i in range(4):
        a = i * TAU / 4 + TAU / 8
        g.tube([(math.cos(a) * 0.2, math.sin(a) * 0.2, 0.18), (math.cos(a) * 0.4, math.sin(a) * 0.4, 0.08), (math.cos(a) * 0.5, math.sin(a) * 0.5, 0.02)], 0.035, wood, n=6)
    g.cyl((0, 0, h - 0.05), r, 0.05, top or wood, n=28)
    g.torus((0, 0, h - 0.03), r, 0.02, wood, n=28, m=4)
    g.collide((0, 0, h / 2), (r * 1.6, r * 1.6, h))


def dining_table(g, M, L, W, h=0.76, wood=None):
    wood = wood or M.mahogany
    g.box((0, 0, h - 0.03), (L, W, 0.06), wood, bevel=0.015)
    for sx in (-1, 0, 1):
        for sy in (-1, 1):
            turned_leg(g, (sx * (L / 2 - 0.2), sy * (W / 2 - 0.15), 0), h - 0.06, 0.05, wood)
    g.box((0, 0, h + 0.006), (L + 0.1, W + 0.12, 0.012), M.linen)
    for sy in (-1, 1):
        g.box((0, sy * (W / 2 + 0.06), h - 0.16), (L + 0.1, 0.012, 0.33), M.linen)
    for sx in (-1, 1):
        g.box((sx * (L / 2 + 0.05), 0, h - 0.16), (0.012, W + 0.12, 0.33), M.linen)
    g.box((0, 0, h + 0.014), (L - 0.4, 0.42, 0.004), M.velvet_moss)  # runner
    g.collide((0, 0, h / 2), (L + 0.1, W + 0.12, h))


def dining_chair_geo(g, M, seat, wood=None, col=True):
    wood = wood or M.mahogany
    for sx in (-1, 1):
        turned_leg(g, (sx * 0.2, -0.18, 0), 0.44, 0.026, wood)
        g.tube([(sx * 0.19, 0.19, 0), (sx * 0.19, 0.2, 0.44), (sx * 0.17, 0.25, 0.75), (sx * 0.15, 0.27, 0.93)], 0.022, wood, n=6)
    g.box((0, 0, 0.46), (0.46, 0.44, 0.05), wood, bevel=0.01)
    g.box((0, -0.01, 0.5), (0.42, 0.4, 0.05), seat, bevel=0.02)
    loop = [(0.15 * math.sin(t), 0.27 - 0.02 * math.cos(t), 0.78 + 0.16 * math.cos(t)) for t in np.linspace(-2.4, 2.4, 10)]
    g.tube(loop, 0.02, wood, n=5)
    g.box((0, 0.255, 0.72), (0.2, 0.025, 0.08), wood, rx=-0.15)
    if col:
        g.collide((0, 0, 0.25), (0.46, 0.44, 0.5))


def sideboard(g, M, w=2.0, d=0.55, h=0.92, wood=None, top=None, doors=3):
    wood = wood or M.mahogany
    g.box((0, 0, 0.06), (w - 0.06, d - 0.06, 0.12), M.walnut_dark)
    g.box((0, 0, 0.12 + (h - 0.16) / 2), (w, d, h - 0.16), wood, bevel=0.01)
    g.box((0, -0.01, h - 0.02), (w + 0.06, d + 0.04, 0.04), top or wood, bevel=0.01)
    dw = (w - 0.1) / doors
    for i in range(doors):
        x = -w / 2 + 0.05 + dw * (i + 0.5)
        g.box((x, -d / 2 - 0.005, 0.12 + (h - 0.36) / 2), (dw - 0.06, 0.015, h - 0.42), wood)
        g.box((x, -d / 2 - 0.012, 0.12 + (h - 0.36) / 2), (dw - 0.18, 0.01, h - 0.56), M.walnut_dark)
        g.box((x, -d / 2 - 0.005, h - 0.14), (dw - 0.06, 0.015, 0.14), wood)
        g.sphere((x, -d / 2 - 0.03, h - 0.14), 0.016, M.brass, n=6)
        g.sphere((x + dw * 0.3, -d / 2 - 0.03, 0.12 + (h - 0.36) / 2), 0.014, M.brass, n=6)
    g.box((0, d / 2 - 0.02, h + 0.12), (w, 0.03, 0.24), wood, bevel=0.006)
    g.prism((0, d / 2 - 0.035, h + 0.24), [(-0.3, 0), (0.3, 0), (0, 0.12)], 0.03, wood, rx=-HALF)
    g.collide((0, 0, h / 2), (w, d, h))


def desk(g, M, w=1.7, d=0.85, h=0.78, wood=None):
    wood = wood or M.walnut
    for sx in (-1, 1):
        x = sx * (w / 2 - 0.26)
        g.box((x, 0, 0.05), (0.52, d - 0.02, 0.1), M.walnut_dark)
        g.box((x, 0, (h - 0.05) / 2 + 0.05), (0.5, d - 0.06, h - 0.1), wood, bevel=0.01)
        for k in range(3):
            z = 0.2 + k * 0.2
            g.box((x, -d / 2 + 0.02, z), (0.44, 0.015, 0.17), wood, bevel=0.005)
            g.sphere((x, -d / 2, z), 0.014, M.brass, n=6)
    g.box((0, d / 2 - 0.05, h - 0.2), (w - 1.0, 0.03, 0.3), wood)
    g.box((0, -d / 2 + 0.02, h - 0.1), (w - 1.04, 0.015, 0.12), wood, bevel=0.004)
    g.box((0, 0, h - 0.025), (w, d, 0.05), wood, bevel=0.012)
    g.box((0, 0, h + 0.002), (w - 0.18, d - 0.18, 0.006), M.velvet_moss)
    g.collide((0, 0, h / 2), (w, d, h))


ROW_H = 0.41      # every bookshelf row on the map is this tall so the spine texture lines up
ROW_Z0 = 0.1125   # height of the first row of books above the floor


def book_spines(size=512, seed=26):
    """Tileable row of book spines. One tile = ROW_H metres; rolled so a row starts at ROW_Z0."""
    rng = np.random.default_rng(seed)
    h = w = size
    img = np.zeros((h, w, 3))
    img[:] = tex.hex_rgb('#120c08')
    cols = ['#5a1a1a', '#26361f', '#1e2638', '#7a5a3a', '#3a2416', '#4a2440', '#6a4a2a', '#2a2a2a', '#5a3a1a']
    x = 0
    while x < w:
        bw = int(rng.integers(9, 26))
        if rng.random() < 0.06:
            x += int(rng.integers(6, 30))
            continue
        bh = int(h * rng.uniform(0.62, 0.92))
        c = tex.hex_rgb(cols[rng.integers(len(cols))]) * rng.uniform(0.7, 1.15)
        x1 = min(w, x + bw)
        col = np.linspace(0.75, 1.1, x1 - x) * (1 - 0.25 * np.abs(np.linspace(-1, 1, x1 - x)) ** 2)
        img[h - bh:, x:x1] = c * col[None, :, None]
        for band in range(int(rng.integers(0, 3))):
            y0 = h - bh + int(bh * (0.08 + 0.12 * band + rng.uniform(0, 0.04)))
            img[y0:y0 + 3, x + 1:x1 - 1] = tex.hex_rgb('#b08a3e') * 0.8
        if rng.random() < 0.5:
            yl = h - int(bh * 0.55)
            img[yl:yl + int(bh * 0.12), x + 2:x1 - 2] *= 0.6
        img[h - bh:, x:x + 1] *= 0.4
        x = x1 + int(rng.integers(0, 2))
    n = tex.fbm((h, w), 8, 3, seed)
    img *= (0.8 + 0.3 * n)[..., None]
    f = (ROW_Z0 / ROW_H) % 1.0
    img = np.roll(img, -int(round(f * h)), axis=0)
    return np.clip(img, 0, 1)


def bookcase(g, M, w, h, seed, depth=0.4, col=True, loose=True):
    """Walnut bookcase; each row of books is one box wearing the spine texture, plus a few
    loose volumes and curios so the shelves don't read as wallpaper."""
    rng = jitter_rng(seed)
    rows = int((h - 0.25) / ROW_H)
    g.box((0, depth / 2 - 0.015, h / 2), (w, 0.03, h), M.walnut_dark)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.02), 0, h / 2), (0.04, depth, h), M.walnut)
        g.box((sx * (w / 2 - 0.02), -depth / 2 - 0.015, h / 2), (0.07, 0.03, h), M.walnut)
    g.box((0, 0, 0.05), (w + 0.02, depth, 0.1), M.walnut_dark)
    g.box((0, -0.02, h - 0.02), (w + 0.08, depth + 0.06, 0.05), M.walnut)
    g.box((0, -depth / 2 - 0.03, h + 0.04), (w + 0.12, 0.1, 0.08), M.walnut)
    for k in range(rows + 1):
        z0 = ROW_Z0 - 0.0125 + k * ROW_H
        if z0 > h - 0.1:
            break
        g.box((0, 0, z0 - 0.0125), (w - 0.06, depth - 0.02, 0.025), M.walnut)
        if k == rows or z0 + ROW_H > h - 0.06:
            continue
        # leave a gap or two for loose books and objects
        segs = [(-w / 2 + 0.03, w / 2 - 0.03)]
        if loose and rng.random() < 0.45:
            gx = rng.uniform(-w / 2 + 0.3, w / 2 - 0.5)
            gw = rng.uniform(0.18, 0.32)
            segs = [(-w / 2 + 0.03, gx), (gx + gw, w / 2 - 0.03)]
            r = rng.random()
            if r < 0.5:
                for i in range(rng.randint(2, 4)):
                    book(g, M, (gx + gw / 2, -0.02, z0 + i * 0.045), gw * 0.85, depth * 0.7, 0.04, rng.uniform(-0.15, 0.15), rng.choice(M.books))
            elif r < 0.75:
                with g.at((gx + 0.03, -0.02, z0), 0, 0, 0.45):
                    g.box((0.02, 0, 0.14), (0.04, depth * 0.7, 0.28), rng.choice(M.books))
            elif r < 0.88:
                g.lathe((gx + gw / 2, -0.05, z0), [(0.05, 0), (0.07, 0.06), (0.05, 0.16), (0.03, 0.2), (0.045, 0.24)], M.porcelain, n=10)
            else:
                g.sphere((gx + gw / 2, -0.04, z0 + 0.07), 0.07, M.bone, n=8, s=(0.9, 1.1, 1.0))
        for a, b in segs:
            if b - a > 0.05:
                g.box(((a + b) / 2, -depth / 2 + depth * 0.4, z0 + (ROW_H - 0.045) / 2), (b - a, depth * 0.62, ROW_H - 0.045), M.bookrow)
    if col:
        g.collide((0, 0, h / 2), (w, depth, h))


def stack(g, M, length, h, seed):
    """Free-standing double-sided book stack running along X; origin at floor centre."""
    with g.at((0, -0.2, 0)):
        bookcase(g, M, length, h, seed, col=False)
    with g.at((0, 0.2, 0), PI):
        bookcase(g, M, length, h, seed + 7, col=False)
    for sx in (-1, 1):
        g.box((sx * (length / 2 + 0.03), 0, h / 2), (0.06, 0.86, h + 0.02), M.walnut, bevel=0.01)
        g.box((sx * (length / 2 + 0.06), 0, h * 0.6), (0.01, 0.4, 0.5), M.walnut_dark)
        g.box((sx * (length / 2 + 0.065), 0, h * 0.6 + 0.1), (0.008, 0.2, 0.06), M.paper)  # shelf label
    g.collide((0, 0, h / 2), (length + 0.12, 0.86, h))


def fireplace(g, M, w=2.2, stone=None, mantle=None, breast_h=4.2, glass=None, breast=None):
    """Fireplace with chimney breast; origin is at the floor in front of the breast, which runs
    back to y = +0.6 (place y=0.6 at the wall face). Pair with fire()."""
    stone = stone or M.marble
    mantle = mantle or stone
    with g.at((0, 0.275, 0)):
        pf.fireplace(g, w, stone, M.coal, mantle)
    g.box((0, 0.45, breast_h / 2), (w + 0.5, 0.3, breast_h), breast or M.plaster_dark, col=True)
    # firebox lining + brick back
    g.box((0, 0.32, 0.55), (w - 1.0, 0.04, 0.95), M.brick)
    g.box((0, 0.0, 0.11), (w - 1.04, 0.5, 0.02), M.coal)
    # overmantel mirror
    if glass is not False:
        frame_rect(g, (0, 0.27, 2.4), w * 0.72, 1.2, 0.08, 0.05, M.brass)
        g.box((0, 0.29, 2.4), (w * 0.72 - 0.12, 0.02, 1.08), M.mirror)
    # fender and fire irons
    g.box((0, -0.62, 0.06), (w - 0.6, 0.03, 0.1), M.brass, bevel=0.01)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.3), -0.45, 0.06), (0.03, 0.36, 0.1), M.brass, bevel=0.01)
    g.lathe((w / 2 - 0.12, -0.5, 0), [(0.08, 0), (0.07, 0.02), (0.015, 0.05), (0.012, 0.6), (0.02, 0.62), (0.01, 0.68)], M.brass, n=8)
    for i, a in enumerate((-0.15, 0.0, 0.15)):
        g.tube([(w / 2 - 0.12, -0.5, 0.62), (w / 2 - 0.12 + math.sin(a) * 0.12, -0.5 + 0.03 * i - 0.03, 0.15)], 0.008, M.iron, n=4)


def fire(p, M, w=1.2, light=(WARM, 1.5, 9.0)):
    """Log fire for a hearth. Origin on the hearth floor at the firebox centre."""
    b = p.body
    for sx in (-1, 1):
        b.box((sx * 0.3, -0.02, 0.12), (0.04, 0.28, 0.22), M.iron)
        b.sphere((sx * 0.3, -0.16, 0.25), 0.04, M.brass, n=8)
    b.box((0, 0.0, 0.03), (w * 0.62, 0.26, 0.04), M.ember)
    b.cyl((-0.35, -0.06, 0.13), 0.06, 0.7, M.walnut_dark, n=7, ry=HALF, rz=0.15)
    b.cyl((-0.32, 0.08, 0.15), 0.055, 0.66, M.walnut_dark, n=7, ry=HALF, rz=-0.1)
    b.cyl((-0.15, 0.0, 0.22), 0.05, 0.4, M.coal, n=7, ry=HALF + 0.3)
    for x, y, s in ((-0.18, 0.02, 1.9), (0.0, -0.02, 2.4), (0.17, 0.04, 1.8), (0.07, 0.08, 1.5)):
        p.flame((x, y, 0.16), size=s)
    if light:
        p.light((0, -0.2, 0.55), light[0], light[1], light[2], part='flame0')
    p.params.setdefault('sound', 'whoomp')


def window(g, M, w, h):
    """Sash window filling a wall opening (origin bottom centre, wall along X), moonlit panes."""
    t = 0.34
    g.box((0, 0, h / 2), (w - 0.04, 0.04, h - 0.04), M.glass)  # edges tucked inside the frame
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.04), 0, h / 2), (0.08, t, h), M.walnut)
    g.box((0, 0, h - 0.04), (w, t, 0.08), M.walnut)
    g.box((0, 0, 0.03), (w + 0.1, t + 0.1, 0.06), M.walnut)
    g.box((0, 0, h / 2), (0.04, 0.08, h), M.walnut)
    g.box((0, 0, h * 0.58), (w, 0.1, 0.06), M.walnut)
    for f in (0.3, 0.82):
        g.box((0, 0, h * f), (w, 0.06, 0.03), M.walnut)


def column(g, M, h, r=0.22, mat=None, base_mat=None):
    mat = mat or M.marble
    base_mat = base_mat or mat
    g.box((0, 0, 0.12), (r * 2.6, r * 2.6, 0.24), base_mat, bevel=0.02)
    g.lathe((0, 0, 0.24), [(r * 1.18, 0), (r * 1.18, 0.06), (r * 1.05, 0.1), (r * 1.08, 0.14), (r, 0.18),
                           (r * 0.88, h - 0.7), (r * 1.0, h - 0.62), (r * 1.25, h - 0.5), (r * 1.3, h - 0.46)], mat, n=16)
    g.box((0, 0, h - 0.11), (r * 2.9, r * 2.9, 0.22), base_mat, bevel=0.02)
    g.collide((0, 0, h / 2), (r * 2.6, r * 2.6, h))


def pedestal(g, M, h=1.05, mat=None):
    mat = mat or M.marble
    g.box((0, 0, 0.06), (0.5, 0.5, 0.12), mat, bevel=0.015)
    g.lathe((0, 0, 0.12), [(0.17, 0), (0.15, 0.06), (0.12, 0.1), (0.1, h - 0.3), (0.13, h - 0.24), (0.17, h - 0.2)], mat, n=12)
    g.box((0, 0, h - 0.1), (0.42, 0.42, 0.2), mat, bevel=0.015)
    g.collide((0, 0, h / 2), (0.5, 0.5, h))


def kitchen_range(g, M, w=2.4):
    """Cast-iron range in a brick chimney recess. Origin at the floor in front; back at y=+0.95."""
    d = 0.75
    # brick chimney recess
    g.box((0, 0.85, 2.1), (w + 1.2, 0.2, 4.2), M.brick)
    for sx in (-1, 1):
        g.box((sx * (w / 2 + 0.35), 0.45, 2.1), (0.5, 0.6, 4.2), M.brick, col=True)
    g.box((0, 0.45, 3.0), (w + 0.2, 0.6, 2.4), M.brick, col=True)
    g.box((0, 0.13, 1.82), (w + 0.4, 0.06, 0.12), M.walnut_dark)  # mantel shelf
    g.box((0, 0.44, 0.45), (w, d, 0.9), M.iron, bevel=0.02, col=True)
    g.box((0, 0.44, 0.9), (w + 0.08, d + 0.06, 0.04), M.iron, bevel=0.01)
    for i, x in enumerate((-0.8, -0.2, 0.75)):
        dw = 0.5 if i < 2 else 0.7
        if i == 1:  # open firebox: glowing coals behind a grate, door swung aside
            g.box((x, 0.062, 0.36), (dw - 0.08, 0.01, 0.34), M.ember)
            for k in range(6):
                g.box((x - 0.18 + k * 0.072, 0.045, 0.36), (0.018, 0.02, 0.34), M.iron)
            g.box((x + dw / 2 + 0.05, -0.15, 0.36), (0.03, 0.42, 0.4), M.iron, rz=0.0)
            continue
        g.box((x, 0.06, 0.42), (dw, 0.04, 0.5), M.iron, bevel=0.015)
        g.box((x, 0.03, 0.62), (dw * 0.6, 0.02, 0.03), M.brass)
        g.cyl((x - dw * 0.3, 0.04, 0.6), 0.02, 0.04, M.brass, n=6, rx=HALF)
    for x in (-0.6, 0.0, 0.6):
        g.cyl((x, 0.38, 0.92), 0.17, 0.02, M.black, n=14)
    g.box((0, 0.04, 0.82), (w + 0.1, 0.02, 0.02), M.brass)  # towel rail
    for sx in (-1, 1):
        g.box((sx * (w / 2 + 0.03), 0.04, 0.82), (0.02, 0.06, 0.02), M.brass)
    g.cyl((0.9, 0.6, 0.92), 0.09, 1.2, M.iron, n=10)  # flue
    g.box((0, 0.6, 1.1), (w, 0.1, 0.4), M.iron)  # back plate + plate rack
    g.box((0, 0.55, 1.32), (w, 0.2, 0.03), M.iron)


def butcher_block(g, M):
    g.box((0, 0, 0.73), (0.7, 0.7, 0.34), M.pine, bevel=0.03)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box((sx * 0.27, sy * 0.27, 0.28), (0.1, 0.1, 0.56), M.pine)
    g.box((0, 0, 0.12), (0.6, 0.6, 0.03), M.pine)
    g.collide((0, 0, 0.45), (0.7, 0.7, 0.9))


def wall_shelves(g, M, w, rows, seed, z0=0.9, step=0.45, depth=0.3, items='jars'):
    """Open wall shelving with brackets and clutter; origin on the wall at floor level."""
    rng = jitter_rng(seed)
    for r in range(rows):
        z = z0 + r * step
        g.box((0, -depth / 2, z), (w, depth, 0.035), M.pine)
        for sx in (-1, 1):
            g.prism((sx * (w / 2 - 0.12) - 0.015, 0, z - 0.02), [(0, 0), (0, -0.2), (-0.03, -0.02)], 0.03, M.iron, rx=0, ry=0)
        x = -w / 2 + 0.12
        while x < w / 2 - 0.12:
            kind = rng.random()
            if items == 'jars':
                if kind < 0.45:
                    hh, rr = rng.uniform(0.14, 0.26), rng.uniform(0.05, 0.08)
                    jar(g, M, (x + rr, -depth / 2 + rng.uniform(-0.03, 0.03), z + 0.018), hh, rr,
                        rng.choice([M.glass_dark, M.terracotta, M.porcelain]), M.iron if rng.random() < 0.5 else M.linen)
                    x += rr * 2 + 0.03
                elif kind < 0.65:
                    bottle(g, M, (x + 0.04, -depth / 2, z + 0.018), rng.uniform(0.22, 0.32), 0.035)
                    x += 0.1
                elif kind < 0.8:
                    g.lathe((x + 0.09, -depth / 2, z + 0.018), [(0.06, 0), (0.09, 0.03), (0.09, 0.12), (0.07, 0.16)], M.copper if rng.random() < 0.5 else M.terracotta, n=12)
                    x += 0.2
                else:
                    x += rng.uniform(0.15, 0.35)
            else:
                if kind < 0.6:
                    plate(g, M, (x + 0.12, -depth / 2 + 0.06, z + 0.13), 0.12)
                    x += 0.27
                else:
                    x += 0.15
    g.collide((0, -depth / 2, z0 + (rows - 1) * step / 2 + 0.1), (w, depth, (rows - 1) * step + 0.3))


def dresser(g, M, w=2.0):
    """Welsh dresser: cupboard base and a plate rack."""
    sideboard(g, M, w=w, d=0.5, h=0.9, wood=M.pine, doors=3)
    g.box((0, 0.2, 1.65), (w, 0.04, 1.5), M.pine)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.02), 0.06, 1.65), (0.04, 0.32, 1.5), M.pine)
    for k in range(3):
        z = 1.15 + k * 0.42
        g.box((0, 0.08, z), (w - 0.04, 0.24, 0.03), M.pine)
        g.box((0, -0.02, z + 0.06), (w - 0.04, 0.015, 0.025), M.pine)
        for i in range(6):
            x = -w / 2 + 0.2 + i * (w - 0.4) / 5
            g.cyl((x, 0.12, z + 0.17), 0.14, 0.015, M.porcelain if (i + k) % 3 else M.toy_blue, n=16, rx=HALF - 0.25)
    g.box((0, 0.06, 2.42), (w + 0.1, 0.36, 0.06), M.pine, bevel=0.01)


def sink(g, M):
    for sx in (-1, 1):
        g.box((sx * 0.55, 0.0, 0.35), (0.2, 0.6, 0.7), M.brick)
    g.box((0, 0, 0.8), (1.4, 0.65, 0.22), M.marble, bevel=0.02)
    g.box((0, -0.02, 0.86), (1.24, 0.5, 0.12), M.flag_dark)
    g.collide((0, 0, 0.45), (1.4, 0.65, 0.9))


def bed(g, M, w=1.0, L=1.9, quilt=None):
    """Child's iron bed, head at +Y."""
    quilt = quilt or M.velvet_plum
    for sy, hh in ((1, 1.15), (-1, 0.8)):
        y = sy * (L / 2)
        for sx in (-1, 1):
            g.cyl((sx * w / 2, y, 0), 0.025, hh, M.iron, n=8)
            g.sphere((sx * w / 2, y, hh + 0.02), 0.04, M.brass, n=8)
        g.cyl((-w / 2, y, hh - 0.05), 0.015, w, M.iron, n=6, ry=HALF)
        g.cyl((-w / 2, y, 0.42), 0.015, w, M.iron, n=6, ry=HALF)
        for i in range(1, 6):
            x = -w / 2 + w * i / 6
            g.cyl((x, y, 0.42), 0.01, hh - 0.47, M.iron, n=5)
        g.torus((0, y, hh * 0.72), 0.12, 0.012, M.brass, n=14, m=4, rx=HALF)
    g.box((0, 0, 0.3), (w, L, 0.08), M.iron)
    g.box((0, 0, 0.42), (w - 0.06, L - 0.06, 0.18), M.linen, bevel=0.05)
    g.box((0, -0.15, 0.53), (w + 0.04, L * 0.7, 0.06), quilt, bevel=0.03)
    for sx in (-1, 1):
        g.box((sx * (w / 2 + 0.02), -0.15, 0.4), (0.03, L * 0.7, 0.24), quilt)
    g.box((0, L / 2 - 0.25, 0.58), (w * 0.7, 0.32, 0.12), M.linen, bevel=0.05)
    g.collide((0, 0, 0.35), (w + 0.1, L, 0.7))


def toy_chest(g, M):
    g.box((0, 0, 0.27), (0.9, 0.5, 0.46), M.toy_red, bevel=0.02)
    g.box((0, 0, 0.04), (0.94, 0.54, 0.08), M.walnut)
    g.box((0, 0.22, 0.53), (0.92, 0.52, 0.05), M.walnut, rx=-0.6, bevel=0.01)
    for sx in (-1, 1):
        g.box((sx * 0.3, -0.255, 0.28), (0.18, 0.01, 0.22), M.toy_blue)
    g.sphere((-0.1, 0.0, 0.52), 0.07, M.toy_blue, n=10)  # ball peeking out
    g.collide((0, 0, 0.28), (0.9, 0.5, 0.56))


def dollhouse(g, M):
    """Tall dollhouse replica of the manor itself, windows faintly lit. ~1.1 x 0.6 footprint."""
    g.box((0, 0, 0.3), (1.2, 0.7, 0.6), M.walnut, bevel=0.02)
    g.box((0, 0.05, 1.05), (1.0, 0.5, 0.9), M.brick)
    g.prism((0, 0.05, 1.5), [(-0.55, -0.0), (0.55, 0.0), (0.0, 0.4)], 0.56, M.slate, rx=HALF)
    g.box((0.35, 0.05, 1.75), (0.18, 0.18, 0.5), M.brick)
    g.prism((0.35, 0.05, 2.0), [(-0.12, 0), (0.12, 0), (0, 0.22)], 0.2, M.slate, rx=HALF)
    for r in range(2):
        for c in range(4):
            x = -0.36 + c * 0.24
            z = 0.75 + r * 0.42
            lit = (r, c) in ((1, 1), (0, 3))
            g.box((x, -0.21, z), (0.1, 0.02, 0.16), M.glow if lit else M.glass)
            g.box((x, -0.215, z - 0.09), (0.14, 0.03, 0.025), M.linen)
    g.box((0, -0.215, 0.64), (0.14, 0.03, 0.2), M.walnut_dark)
    g.collide((0, 0, 0.9), (1.2, 0.7, 1.8))


def organ(g, M, w=2.6):
    """Chamber pipe organ case, console facing -Y."""
    d = 0.9
    g.box((0, 0.1, 0.55), (w, d - 0.2, 1.1), M.walnut, bevel=0.015)
    g.box((0, -0.2, 0.78), (w * 0.62, 0.42, 0.06), M.walnut, bevel=0.01)
    g.box((0, -0.3, 0.82), (w * 0.52, 0.18, 0.03), M.porcelain)
    g.box((0, -0.22, 0.93), (w * 0.52, 0.18, 0.03), M.porcelain, rx=-0.2)
    for i in range(22):
        if i % 7 in (2, 6):
            continue
        g.box((-w * 0.25 + i * w * 0.5 / 22, -0.33, 0.845), (0.016, 0.1, 0.02), M.black)
    for k in range(8):  # stops
        for sx in (-1, 1):
            g.cyl((sx * (w * 0.3 + 0.04), -0.27, 0.9 + k * 0.06 - (k // 4) * 0.24), 0.016, 0.06, M.porcelain, n=6, rx=HALF)
    g.box((0, 0.2, 1.65), (w, d - 0.4, 1.1), M.walnut, bevel=0.015)
    g.box((0, 0.04, 1.15), (w * 0.6, 0.06, 0.12), M.walnut)
    g.box((0, -0.0, 1.45), (w * 0.4, 0.05, 0.5), M.walnut_dark)
    g.box((0, -0.04, 1.45), (w * 0.3, 0.02, 0.36), M.paper)  # music rest
    heights = [1.6, 1.3, 1.1, 0.95, 0.85, 0.95, 1.1, 1.3, 1.6]
    for i, hh in enumerate(heights):
        x = -w / 2 + 0.2 + i * (w - 0.4) / 8
        r = 0.07 if i in (0, 8) else 0.055
        g.cyl((x, 0.05, 2.2), r, hh, M.brass, n=10)
        g.cyl((x, 0.05, 2.2 - 0.12), r * 0.9, 0.12, M.brass, n=10, r2=r * 0.4)
        g.box((x, 0.05 - r, 2.32), (r * 1.2, 0.01, 0.05), M.black)
    g.box((0, 0.2, 2.25), (w + 0.08, d - 0.36, 0.1), M.walnut, bevel=0.01)
    g.box((0, 0.3, 3.05), (w, 0.3, 1.6), M.walnut_dark)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.05), 0.2, 2.9), (0.12, 0.5, 1.4), M.walnut, bevel=0.01)
    g.box((0, 0.2, 3.62), (w + 0.12, 0.6, 0.12), M.walnut, bevel=0.015)
    g.box((0, -0.7, 0.24), (1.3, 0.36, 0.06), M.walnut)  # bench
    for sx in (-1, 1):
        g.box((sx * 0.58, -0.7, 0.11), (0.06, 0.32, 0.22), M.walnut)
    g.collide((0, 0.1, 1.8), (w, d - 0.2, 3.6))
    g.collide((0, -0.7, 0.14), (1.3, 0.36, 0.28))


def bench(g, M, w=1.6, wood=None, cushion=None):
    wood = wood or M.walnut
    g.box((0, 0, 0.43), (w, 0.42, 0.05), wood, bevel=0.01)
    if cushion is not None:
        g.box((0, 0, 0.48), (w - 0.06, 0.38, 0.07), cushion, bevel=0.03)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.08), 0, 0.2), (0.06, 0.36, 0.4), wood)
    g.box((0, 0, 0.12), (w - 0.2, 0.04, 0.04), wood)
    g.collide((0, 0, 0.25), (w, 0.42, 0.5))


def planter(g, M, w, d, h=0.5, seed=0, plants=True):
    g.box((0, 0, h / 2), (w, d, h), M.brick, bevel=0.01, col=True)
    g.box((0, 0, h + 0.02), (w + 0.06, d + 0.06, 0.04), M.marble)
    g.box((0, 0, h + 0.005), (w - 0.12, d - 0.12, 0.03), M.coal)
    if plants:
        rng = jitter_rng(seed)
        n = max(2, int(w * d * 0.8))
        for i in range(n):
            x = rng.uniform(-w / 2 + 0.2, w / 2 - 0.2)
            y = rng.uniform(-d / 2 + 0.15, d / 2 - 0.15)
            r = rng.uniform(0.15, 0.3)
            g.blob((x, y, h + r * 0.6), r, rng.choice(M.leaves), seed=seed * 13 + i, jitter=0.25, s=(1, 1, 0.75))


def stair_flight(g, M, x0, x1, y0, steps, rise, run, flare=()):
    """Straight flight rising to +Y from y0. Each step is a solid collider box."""
    for i in range(steps):
        top = rise * (i + 1)
        y = y0 + run * i
        fl = flare[i] if i < len(flare) else 0.0
        a, b = x0 - fl, x1 + fl
        g.box(((a + b) / 2, y + run / 2, top / 2), (b - a, run, top), M.marble, col=True)
        g.box(((a + b) / 2, y + 0.02, top - 0.015), (b - a + 0.03, 0.06, 0.035), M.marble_dark)
        g.box(((a + b) / 2, y + run / 2 + 0.02, top + 0.004), (min(b - a, x1 - x0) - 0.6, run + 0.02, 0.012), M.velvet_ox)
        g.box(((a + b) / 2, y + run - 0.02, top + 0.012), (min(b - a, x1 - x0) - 0.6, 0.018, 0.018), M.brass)


def balusters(g, M, a, b, z_of, step=0.16, h=0.95, mat=None, rail=None):
    """Balustrade from point a to b (XY) with floor height function z_of(t in 0..1)."""
    mat = mat or M.marble
    rail = rail or M.walnut
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    n = max(2, int(L / step))
    for i in range(n + 1):
        t = i / n
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        z = z_of(t)
        g.lathe((x, y, z), [(0.035, 0), (0.02, 0.1), (0.045, 0.3), (0.02, 0.62), (0.03, h - 0.04)], mat, n=6)
    pts = [(ax + (bx - ax) * t, ay + (by - ay) * t, z_of(t) + h) for t in (0, 1)]
    g.tube(pts, 0.04, rail, n=6)
    pts = [(ax + (bx - ax) * t, ay + (by - ay) * t, z_of(t) + 0.06) for t in (0, 1)]
    g.tube(pts, 0.03, rail, n=4)


def newel(g, M, pos, h=1.15):
    x, y, z = pos
    g.box((x, y, z + h / 2), (0.24, 0.24, h), M.walnut, bevel=0.02)
    g.box((x, y, z + h + 0.03), (0.3, 0.3, 0.06), M.walnut, bevel=0.015)
    g.sphere((x, y, z + h + 0.15), 0.1, M.brass, n=10)


def stag_head(g, M):
    """Mounted antlers on a shield, on a wall facing -Y."""
    g.prism((0, 0, 1.9), [(-0.22, 0), (0.22, 0), (0.22, 0.3), (0, 0.42), (-0.22, 0.3)], 0.05, M.walnut, rx=HALF)
    g.blob((0, -0.15, 2.05), 0.13, M.wool, seed=3, jitter=0.1, s=(0.8, 1.6, 0.9))
    g.blob((0, -0.36, 1.98), 0.08, M.wool, seed=4, jitter=0.1, s=(0.7, 1.4, 0.8))
    for sx in (-1, 1):
        base = (sx * 0.08, -0.15, 2.18)
        g.tube([base, (sx * 0.22, -0.18, 2.4), (sx * 0.35, -0.12, 2.6), (sx * 0.4, -0.05, 2.75)], 0.02, M.bone, n=5)
        g.tube([(sx * 0.22, -0.18, 2.4), (sx * 0.2, -0.3, 2.56)], 0.014, M.bone, n=4)
        g.tube([(sx * 0.33, -0.13, 2.56), (sx * 0.27, -0.22, 2.72)], 0.012, M.bone, n=4)
        g.sphere((sx * 0.07, -0.3, 2.04), 0.015, M.black, n=5)


def vestibule(g, M, w, h, depth=1.2):
    """Dark box behind the front doors (outside the wall at y=0, extending to -Y)."""
    g.box((0, -depth, h / 2), (w + 0.6, 0.1, h + 0.2), M.walnut_dark)
    for sx in (-1, 1):
        g.box((sx * (w / 2 + 0.25), -depth / 2, h / 2), (0.1, depth, h + 0.2), M.walnut_dark)
    g.box((0, -depth / 2, h + 0.1), (w + 0.6, depth, 0.1), M.walnut_dark)
    g.box((0, -depth / 2, -0.02), (w + 0.6, depth, 0.04), M.floor_check_mat)


def giant_birdcage(g, M, R=2.3, wall_h=3.4, top=4.9, bars=32):
    """The Birdcage penalty box. Origin at the floor centre. Sealed with chord colliders + lid."""
    g.cyl((0, 0, 0), R + 0.18, 0.12, M.marble, n=bars)
    g.cyl((0, 0, 0.12), R + 0.04, 0.03, M.marble_dark, n=bars)
    g.torus((0, 0, 0.15), R + 0.02, 0.04, M.brass, n=bars, m=4)
    for k in range(bars):
        a = k * TAU / bars
        x, y = math.cos(a) * R, math.sin(a) * R
        g.cyl((x, y, 0.15), 0.024, wall_h - 0.15, M.iron, n=4, smooth=False)
        # dome ribs
        pts = []
        for i in range(7):
            t = i / 6
            ang = t * HALF
            rr = R * math.cos(ang) * (1 - 0.06 * t)
            pts.append((math.cos(a) * rr, math.sin(a) * rr, wall_h + (top - wall_h) * math.sin(ang)))
        if k % 2 == 0:
            g.tube(pts[::2] + [pts[-1]] if len(pts) % 2 == 0 else pts[::2], 0.02, M.iron, n=4, caps=False)
    for z in (0.18, 1.1, 2.3, wall_h):
        g.torus((0, 0, z), R, 0.035 if z in (0.18, wall_h) else 0.022, M.brass if z == wall_h else M.iron, n=bars, m=4)
    for z, rr in ((wall_h + 0.6, R * 0.86), (wall_h + 1.1, R * 0.55)):
        g.torus((0, 0, z), rr, 0.022, M.iron, n=bars, m=4)
    # scrollwork band
    for k in range(bars // 4):
        a = (k + 0.5) * TAU / (bars / 4)
        c = (math.cos(a) * (R + 0.02), math.sin(a) * (R + 0.02), 2.9)
        g.torus(c, 0.12, 0.012, M.brass, n=10, m=4, rx=HALF, rz=a + HALF)
    g.lathe((0, 0, top - 0.05), [(0.25, 0), (0.18, 0.08), (0.08, 0.2), (0.12, 0.32), (0.02, 0.5)], M.brass, n=12)
    g.torus((0, 0, top + 0.62), 0.12, 0.025, M.brass, n=12, m=4, rx=HALF)
    # hanging perch ring inside
    g.cyl((0, 0, 2.7), 0.012, top - 2.7, M.brass, n=4)
    g.torus((0, 0, 2.6), 0.5, 0.025, M.brass, n=20, m=4, rx=HALF)
    g.cyl((-0.5, 0, 2.2), 0.03, 1.0, M.walnut, n=6, ry=HALF)
    # gate with padlock (on -Y side)
    g.box((0, -R - 0.02, 1.2), (1.1, 0.04, 0.04), M.brass)
    g.box((0, -R - 0.02, 2.2), (1.1, 0.04, 0.04), M.brass)
    g.box((0.45, -R - 0.08, 1.5), (0.12, 0.06, 0.14), M.brass, bevel=0.01)
    g.torus((0.45, -R - 0.08, 1.6), 0.04, 0.01, M.steel, n=8, m=4, rx=HALF)
    # colliders: chord segments around the ring + lid
    segs = 24
    t = 0.14
    for k in range(segs):
        a0, a1 = k * TAU / segs, (k + 1) * TAU / segs
        x0, y0 = math.cos(a0) * R, math.sin(a0) * R
        x1, y1 = math.cos(a1) * R, math.sin(a1) * R
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        sx, sy = abs(x1 - x0) + t, abs(y1 - y0) + t
        g.collide((cx, cy, wall_h / 2 + 0.3), (sx, sy, wall_h + 0.6))
    g.collide((0, 0, wall_h + 0.5), (2 * R + 0.3, 2 * R + 0.3, 0.4))


# ======================================================================= light props

def candlestick(p, M, light=None, h=0.17):
    b = p.body
    b.lathe((0, 0, 0), [(0.07, 0), (0.065, 0.015), (0.025, 0.035), (0.016, 0.16), (0.03, 0.18), (0.045, 0.19), (0.02, 0.2)], M.brass, n=10)
    candle(b, M, (0, 0, 0.2), h)
    p.flame((0, 0, 0.2 + h + 0.004), size=0.55)
    if light:
        p.light((0, 0, 0.2 + h + 0.15), light[0], light[1], light[2], part='flame0')
    p.params.setdefault('sound', 'whoomp')


def candelabra(p, M, arms=5, light=None, h=0.42):
    b = p.body
    b.lathe((0, 0, 0), [(0.1, 0), (0.09, 0.02), (0.035, 0.05), (0.022, h * 0.5), (0.04, h * 0.55), (0.02, h * 0.6), (0.02, h)], M.brass, n=10)
    tops = [(0, 0, h)]
    for i in range(arms - 1):
        a = i * TAU / (arms - 1)
        x, y = math.cos(a) * 0.16, math.sin(a) * 0.16
        b.tube([(0, 0, h * 0.62), (x * 0.5, y * 0.5, h * 0.56), (x, y, h * 0.7), (x, y, h * 0.84)], 0.009, M.brass, n=5)
        tops.append((x, y, h * 0.84))
    for t in tops:
        b.cyl(t, 0.028, 0.012, M.brass, n=8, r2=0.04)
        candle(b, M, (t[0], t[1], t[2] + 0.012), 0.13 if t[2] < h else 0.15, 0.016)
        p.flame((t[0], t[1], t[2] + 0.012 + (0.13 if t[2] < h else 0.15) + 0.003), size=0.55)
    if light:
        p.light((0, 0, h + 0.3), light[0], light[1], light[2], part='flame0')
    p.params.setdefault('sound', 'whoomp')


def oil_lamp(p, M, light=None, shade=None):
    b = p.body
    b.lathe((0, 0, 0), [(0.08, 0), (0.08, 0.02), (0.035, 0.05), (0.03, 0.14), (0.07, 0.19), (0.085, 0.25), (0.06, 0.3), (0.03, 0.32)], M.brass, n=12)
    bulb = p.geo('bulb0', (0, 0, 0.32))
    bulb.lathe((0, 0, 0), [(0.028, 0), (0.045, 0.04), (0.05, 0.08), (0.03, 0.15), (0.022, 0.26)], M.glow, n=10, cap_top=False)
    if shade is not None:
        b.lathe((0, 0, 0.36), [(0.04, 0), (0.12, 0.04), (0.14, 0.12), (0.1, 0.2), (0.06, 0.22)], shade, n=12, cap_bottom=False, cap_top=False)
    if light:
        p.light((0, 0, 0.5), light[0], light[1], light[2], part='bulb0')
    p.params.setdefault('sound', 'buzz')


def bankers_lamp(p, M, light=None):
    b = p.body
    b.box((0, 0, 0.02), (0.22, 0.14, 0.04), M.brass, bevel=0.01)
    b.cyl((0, 0.04, 0.04), 0.012, 0.32, M.brass, n=6)
    b.cyl((0.0, 0.04, 0.36), 0.012, 0.06, M.brass, n=6, rx=HALF)
    bulb = p.geo('bulb0', (0, -0.01, 0.38))
    bulb.cyl((-0.16, 0, 0), 0.07, 0.32, M.glass_green, n=10, ry=HALF, caps=True)
    bulb.cyl((-0.14, 0, -0.035), 0.05, 0.28, M.glow, n=8, ry=HALF)
    b.tube([(0.09, 0.04, 0.04), (0.09, 0.04, 0.2)], 0.006, M.brass, n=4)
    if light:
        p.light((0, -0.05, 0.3), light[0], light[1], light[2], part='bulb0')
    p.params.setdefault('sound', 'buzz')


def sconce(p, M, light=None, arms=1):
    """Gas wall sconce with a frosted tulip shade; origin on the wall, facing -Y."""
    b = p.body
    b.lathe((0, 0, 0), [(0.0, -0.1), (0.06, -0.08), (0.07, 0.0), (0.06, 0.08), (0.0, 0.1)], M.brass, n=10, rx=HALF)
    xs = [0.0] if arms == 1 else [-0.18, 0.18]
    for i, x in enumerate(xs):
        b.tube([(0, -0.02, 0), (x * 0.5, -0.12, -0.04), (x, -0.22, 0.02), (x, -0.22, 0.1)], 0.012, M.brass, n=5)
        bl = p.geo(f'bulb{i}', (x, -0.22, 0.1))
        bl.lathe((0, 0, 0), [(0.025, 0), (0.06, 0.05), (0.075, 0.12), (0.08, 0.17)], M.glow, n=10, cap_top=False)
        b.cyl((x, -0.22, 0.09), 0.03, 0.015, M.brass, n=8)
    if light:
        p.light((0, -0.4, 0.2), light[0], light[1], light[2], part='bulb0')
    p.params.setdefault('sound', 'buzz')


def chandelier(p, M, drop=1.0, arms=6, radius=0.6, light=None, tiers=1, crystal=None):
    """Hangs from the ceiling: origin at the ceiling attachment point."""
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.lathe((0, 0, -0.08), [(0.16, 0), (0.12, 0.05), (0.03, 0.08)], M.brass, n=12)
    g.cyl((0, 0, -drop), 0.014, drop, M.brass, n=5)
    z = -drop
    g.lathe((0, 0, z - 0.5), [(0.02, 0), (0.1, 0.08), (0.07, 0.22), (0.13, 0.32), (0.05, 0.42), (0.03, 0.5)], M.brass, n=12)
    for tier in range(tiers):
        rr = radius * (1 - 0.42 * tier)
        zz = z - 0.32 + tier * 0.32
        na = arms if tier == 0 else max(4, arms - 2)
        g.torus((0, 0, zz), rr * 0.95, 0.016, M.brass, n=24, m=4)
        for i in range(na):
            a = i * TAU / na + tier * 0.4
            x, y = math.cos(a) * rr, math.sin(a) * rr
            g.tube([(0, 0, zz - 0.06), (x * 0.45, y * 0.45, zz - 0.14), (x * 0.9, y * 0.9, zz - 0.06), (x, y, zz + 0.06)], 0.012, M.brass, n=5)
            g.cyl((x, y, zz + 0.06), 0.032, 0.02, M.brass, n=8, r2=0.045)
            candle(g, M, (x, y, zz + 0.08), 0.11, 0.016)
            p.flame((x, y, zz + 0.195), size=0.6, parent='pivot')
            g.cyl((x * 0.7, y * 0.7, zz - 0.25), 0.022, 0.09, crystal or M.crystal, n=4, r2=0.001, ry=PI)
    if light:
        p.light((0, 0, z - 0.3), light[0], light[1], light[2], part='pivot')
    p.params.setdefault('amp', 0.012)
    p.params.setdefault('period', 3.6)
    p.params.setdefault('sound', 'clatter')


def hanging_lantern(p, M, drop=0.6, light=None):
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.cyl((0, 0, -drop), 0.008, drop, M.iron, n=4)
    z = -drop
    g.torus((0, 0, z - 0.03), 0.04, 0.008, M.iron, n=8, m=4, rx=HALF)
    g.lathe((0, 0, z - 0.42), [(0.1, 0), (0.12, 0.02), (0.12, 0.05), (0.09, 0.07), (0.09, 0.3), (0.13, 0.32), (0.04, 0.42)], M.iron, n=6, smooth=False)
    g.cyl((0, 0, z - 0.36), 0.085, 0.24, M.glow_dim, n=6, smooth=False)
    p.flame((0, 0, z - 0.32), size=0.8, parent='pivot')
    if light:
        p.light((0, 0, z - 0.25), light[0], light[1], light[2], part='pivot')
    p.params.setdefault('amp', 0.03)
    p.params.setdefault('period', 2.2)
    p.params.setdefault('sound', 'creak')


# ======================================================================= props

def jolt_geo(p, fn, collider=None, sound='thud', **kw):
    """Generic jolt prop: whatever fn draws becomes the pivot."""
    pv = p.part('pivot')
    fn(pv.geo, **kw)
    if collider is not None:
        p.body.collide(*collider)
    p.params.setdefault('sound', sound)


def armchair(p, M, fabric):
    jolt_geo(p, armchair_geo, collider=((0, 0, 0.5), (0.86, 0.82, 1.0)), sound='thud', M=M, fabric=fabric)


def dining_chair(p, M, seat, tipped=False):
    if tipped:
        pv = p.part('pivot', (0, 0, 0))
        with pv.geo.at((0, 0.28, 0.25), 0, -HALF + 0.12):
            dining_chair_geo(pv.geo, M, seat)
    else:
        jolt_geo(p, dining_chair_geo, M=M, seat=seat, col=False)
        p.body.collide((0, 0, 0.25), (0.46, 0.44, 0.5))
    p.params.setdefault('sound', 'thud')


def rocking_chair(p, M, seat):
    pf.rocking_chair(p, M.walnut, seat)
    p.parts['pivot'].geo.box((0.02, 0.06, 0.5), (0.5, 0.44, 0.06), seat, bevel=0.02, rx=0.05)


def door(p, M, w, h, hinge='left', rest=0.0, open_dir=1, wood=None, baize=False):
    """Four-panel door (same conventions as prefabs.door, lighter geometry). Origin at the bottom
    centre of the opening, wall along X; `rest` leaves it ajar toward local +Y * open_dir."""
    wood = wood or M.walnut
    side = -1 if hinge == 'left' else 1
    pv = p.part('pivot', (side * w / 2, 0, 0), rz=rest * open_dir * -side)
    g = pv.geo
    cx = -side * w / 2
    t = 0.06
    g.box((cx, 0, h / 2), (w - 0.02, t, h), wood)
    for sy in (-1, 1):
        y = sy * (t / 2 + 0.004)
        if baize:
            g.box((cx, y, h / 2), (w - 0.14, 0.008, h - 0.16), M.baize)
            for i in range(5):
                for k in (-1, 1):
                    g.box((cx + k * (w / 2 - 0.09), y + sy * 0.006, 0.15 + i * (h - 0.3) / 4), (0.02, 0.006, 0.02), M.brass)
        else:
            for zz, hh in ((h * 0.27, h * 0.36), (h * 0.71, h * 0.4)):
                for kx in (-1, 1):
                    g.box((cx + kx * w * 0.2, y, zz), (w * 0.3, 0.008, hh), M.walnut_dark)
        hx = cx - side * (w / 2 - 0.1)
        g.box((hx, y, h * 0.47), (0.05, 0.006, 0.16), M.brass)
        g.sphere((hx, sy * (t / 2 + 0.04), h * 0.47), 0.03, M.brass, n=6)
    p.params.setdefault('axis', 'y')
    p.params.setdefault('dir', open_dir * -side)
    p.params.setdefault('closed', round(-rest, 4))
    p.params.setdefault('sound', 'bang')


def grandfather_clock(p, M):
    pf.grandfather_clock(p, M.mahogany, M.brass, M.paper, M.black)
    b = p.body
    b.box((0, -0.17, 0.9), (0.4, 0.01, 0.6), M.glass_dark)
    b.lathe((0, 0, 2.5), [(0.04, 0), (0.02, 0.08), (0.03, 0.12), (0.001, 0.2)], M.brass, n=8)


def mantel_clock(p, M):
    b = p.body
    b.box((0, 0, 0.03), (0.42, 0.16, 0.06), M.marble_dark, bevel=0.01)
    b.box((0, 0, 0.17), (0.3, 0.14, 0.22), M.marble_dark, bevel=0.01)
    b.cyl((0, 0, 0.3), 0.15, 0.14, M.marble_dark, n=16, rx=HALF, r2=0.15)
    b.box((0, 0, 0.32), (0.16, 0.12, 0.08), M.marble_dark)
    for sx in (-1, 1):
        b.lathe((sx * 0.17, 0, 0.06), [(0.025, 0), (0.018, 0.04), (0.012, 0.2), (0.022, 0.22)], M.brass, n=8)
        b.sphere((sx * 0.17, 0, 0.3), 0.02, M.brass, n=6)
    b.cyl((0, -0.07, 0.28), 0.1, 0.012, M.brass, n=16, rx=HALF)
    b.cyl((0, -0.078, 0.28), 0.085, 0.01, M.paper, n=16, rx=HALF)
    hr = p.geo('hour', (0, -0.09, 0.28))
    hr.box((0, 0, 0.025), (0.01, 0.004, 0.05), M.black)
    mn = p.geo('minute', (0, -0.094, 0.28))
    mn.box((0, 0, 0.035), (0.007, 0.004, 0.07), M.black)
    b.collide((0, 0, 0.2), (0.42, 0.16, 0.4))
    p.params.setdefault('axis', 'z')
    p.params.setdefault('sound', 'chime')


def wall_clock(p, M, r=0.24):
    """Round kitchen/schoolroom clock with a pendulum box; origin on the wall at the face centre."""
    b = p.body
    b.cyl((0, -0.01, 0), r + 0.04, 0.1, M.pine, n=20, rx=HALF)
    b.cyl((0, -0.105, 0), r, 0.01, M.paper, n=20, rx=HALF)
    b.torus((0, -0.11, 0), r, 0.012, M.brass, n=24, m=4, rx=HALF)
    for i in range(12):
        a = i * TAU / 12
        b.box((math.sin(a) * r * 0.82, -0.115, math.cos(a) * r * 0.82), (0.012, 0.004, 0.035), M.black, ry=-a)
    b.box((0, -0.04, -r - 0.32), (0.26, 0.08, 0.6), M.pine, bevel=0.01)
    b.box((0, -0.082, -r - 0.32), (0.18, 0.01, 0.48), M.glass_dark)
    hr = p.geo('hour', (0, -0.12, 0))
    hr.box((0, 0, 0.05), (0.018, 0.005, 0.11), M.black)
    mn = p.geo('minute', (0, -0.125, 0))
    mn.box((0, 0, 0.08), (0.012, 0.005, 0.17), M.black)
    pend = p.geo('pend', (0, -0.06, -r - 0.06))
    pend.box((0, 0, -0.2), (0.012, 0.006, 0.4), M.brass)
    pend.cyl((0, 0.0, -0.42), 0.05, 0.012, M.brass, n=12, rx=HALF)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('sound', 'chime')


def bracket_clock(p, M):
    b = p.body
    b.box((0, 0, 0.2), (0.3, 0.2, 0.4), M.walnut_dark, bevel=0.012)
    b.cyl((0, 0, 0.4), 0.15, 0.2, M.walnut_dark, n=12, rx=HALF, r2=0.15)
    b.tube([(-0.08, 0, 0.5), (0, 0, 0.58), (0.08, 0, 0.5)], 0.01, M.brass, n=4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.sphere((sx * 0.13, sy * 0.08, -0.0), 0.025, M.brass, n=6)
    b.cyl((0, -0.1, 0.25), 0.11, 0.01, M.brass, n=16, rx=HALF)
    b.cyl((0, -0.108, 0.25), 0.095, 0.008, M.paper, n=16, rx=HALF)
    hr = p.geo('hour', (0, -0.115, 0.25))
    hr.box((0, 0, 0.025), (0.01, 0.004, 0.05), M.black)
    mn = p.geo('minute', (0, -0.118, 0.25))
    mn.box((0, 0, 0.04), (0.007, 0.004, 0.08), M.black)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('sound', 'chime')


def portrait(p, M, art='lord', k=1.0, frame=None, ornate=True):
    """Gilt-framed oil painting on a wall facing -Y. Origin = the nail on the wall surface.
    The canvas samples one cell of the portrait atlas (see ART); k scales it."""
    frame = frame or M.brass
    i, j, span = ART[art]
    cw, ch = ATLAS_CW * span * k, ATLAS_CH * k
    fw = 0.075 + 0.035 * k
    W, H = cw + 2 * fw, ch + 2 * fw
    pv = p.part('pivot', (0, -0.015, 0))
    g = pv.geo
    top = -0.1
    cz = top - H / 2
    frame_rect(g, (0, -0.04, cz), W, H, fw, 0.06, frame, bevel=0.014)
    frame_rect(g, (0, -0.05, cz), W - fw * 1.4, H - fw * 1.4, fw * 0.35, 0.05, M.walnut_dark)
    if ornate:
        for sx in (-1, 1):
            for sz in (-1, 1):
                g.sphere((sx * (W / 2 - fw / 2), -0.075, cz + sz * (H / 2 - fw / 2)), fw * 0.45, frame, n=6, s=(1, 0.5, 1))
        g.prism((0, -0.07, top - 0.02), [(-0.18 * k, 0), (0.18 * k, 0), (0.08 * k, 0.07 * k), (0, 0.12 * k), (-0.08 * k, 0.07 * k)], 0.05, frame, rx=HALF)
    g.box((0, -0.01, cz), (W - 0.04, 0.02, H - 0.04), M.walnut_dark)
    g.tube([(-W * 0.3, -0.008, top - 0.05), (0, -0.008, 0.0), (W * 0.3, -0.008, top - 0.05)], 0.003, M.brass, n=3, caps=False)
    art_part = p.part('art', (-cw / 2 - k * i * ATLAS_CW, -0.045, cz - ch / 2 - k * j * ATLAS_CH), parent='pivot')
    art_part.local = art_part.local @ Matrix.Diagonal((k, k, k, 1.0))
    art_part.geo.box(((i + span / 2) * ATLAS_CW, 0, (j + 0.5) * ATLAS_CH), (span * ATLAS_CW, 0.008, ATLAS_CH), M.portraits)
    p.params.setdefault('axes', 'z')
    p.params.setdefault('amp', 0.0)
    p.params.setdefault('period', 2.6)
    p.params.setdefault('sound', 'clatter')


def covered_mirror(p, M, w=1.1, h=1.6):
    """Tall gilt mirror shrouded in black crepe (mourning). Origin on the wall at the frame top."""
    b = p.body
    frame_rect(b, (0, -0.04, -h / 2), w, h, 0.1, 0.07, M.brass)
    b.box((0, -0.02, -h / 2), (w - 0.16, 0.02, h - 0.16), M.mirror)
    b.prism((0, -0.06, -0.02), [(-0.25, 0), (0.25, 0), (0.1, 0.12), (0, 0.22), (-0.1, 0.12)], 0.05, M.brass, rx=HALF)
    b.box((0, -0.1, 0.02), (w + 0.1, 0.05, 0.05), M.crepe, bevel=0.02)
    c0 = p.geo('cloth0', (0, -0.12, 0.02))
    c0.sheet((0, 0, 0), w * 0.98, h * 0.82, M.crepe, nx=8, ny=10)
    c1 = p.geo('cloth1', (w * 0.42, -0.125, 0.02))
    c1.sheet((0, 0, 0), w * 0.28, h * 0.95, M.crepe, nx=4, ny=10)
    p.params.setdefault('amp', 0.03)
    p.params.setdefault('sound', 'whoosh')


def drapes(p, M, w, h, fabric, rod=None, lace=False):
    """Heavy velvet drapes with a pelmet; origin at the rod centre, wall along X, hanging toward -Y."""
    rod = rod or M.brass
    b = p.body
    b.cyl((-w / 2 - 0.2, -0.14, 0), 0.022, w + 0.4, rod, n=6, ry=HALF)
    for sx in (-1, 1):
        b.sphere((sx * (w / 2 + 0.22), -0.14, 0), 0.045, rod, n=8)
        b.box((sx * (w / 2 + 0.12), -0.07, 0), (0.03, 0.14, 0.03), rod)
    b.box((0, -0.2, 0.1), (w + 0.5, 0.04, 0.36), fabric, bevel=0.01)
    for i in range(7):
        x = -w / 2 - 0.15 + (w + 0.3) * i / 6
        b.prism((x, -0.225, -0.08), [(-0.09, 0), (0.09, 0), (0, -0.09)], 0.02, fabric, rx=HALF)
        b.sphere((x, -0.23, -0.16), 0.02, M.brass, n=5)
    for i, sx in enumerate((-1, 1)):
        pw = w * 0.34
        g = p.geo(f'cloth{i}', (sx * (w / 2 - pw / 2 + 0.12), -0.15, -0.02))
        g.sheet((0, 0, 0), pw, h, fabric, nx=6, ny=8)
        b.torus((sx * (w / 2 - pw * 0.25), -0.2, -h * 0.58), 0.09, 0.018, M.brass, n=10, m=4, rx=HALF)
    if lace:
        g = p.geo('cloth2', (0, -0.08, -0.04))
        g.sheet((0, 0, 0), w * 0.55, h * 0.9, M.lace, nx=6, ny=7)
    p.params.setdefault('amp', 0.04)
    p.params.setdefault('sound', 'whoosh')


def coat_rack(p, M):
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    for i in range(3):
        a = i * TAU / 3
        g.tube([(0, 0, 0.3), (math.cos(a) * 0.2, math.sin(a) * 0.2, 0.1), (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.02)], 0.022, M.walnut, n=5)
    g.lathe((0, 0, 0.0), [(0.04, 0.25), (0.035, 0.6), (0.03, 1.7), (0.045, 1.75), (0.03, 1.8), (0.05, 1.86), (0.001, 1.92)], M.walnut, n=8)
    for i in range(6):
        a = i * TAU / 6
        g.tube([(0, 0, 1.68), (math.cos(a) * 0.12, math.sin(a) * 0.12, 1.66), (math.cos(a) * 0.17, math.sin(a) * 0.17, 1.74)], 0.01, M.brass, n=4)
    g.cyl((0.0, 0.14, 1.72), 0.1, 0.16, M.black, n=12)
    g.cyl((0.0, 0.14, 1.72), 0.17, 0.012, M.black, n=14)
    g.lathe((-0.12, -0.04, 1.73), [(0.1, 0), (0.085, 0.03), (0.08, 0.09), (0.001, 0.11)], M.wool, n=10)
    for i, (a, L, mat) in enumerate(((0.3, 1.2, M.wool), (2.4, 0.95, M.velvet_moss), (4.3, 1.1, M.crepe))):
        hx, hy = math.cos(a) * 0.15, math.sin(a) * 0.15
        g.box((hx * 0.8, hy * 0.8, 1.62), (0.36, 0.1, 0.08), mat, rz=a + HALF, bevel=0.03)
        c = p.geo(f'cloth{i}', (hx, hy, 1.62), rz=a + HALF, parent='pivot')
        c.sheet((0, 0, 0), 0.38, L, mat, nx=4, ny=8)
    p.body.collide((0, 0, 0.9), (0.45, 0.45, 1.8))
    p.params.setdefault('axis', 'x')
    p.params.setdefault('period', 1.6)
    p.params.setdefault('sound', 'creak')


def umbrella_stand(p, M):
    pv = p.part('pivot')
    g = pv.geo
    g.lathe((0, 0, 0), [(0.13, 0), (0.15, 0.04), (0.14, 0.3), (0.16, 0.55), (0.15, 0.58)], M.porcelain, n=14, cap_top=False)
    g.torus((0, 0, 0.3), 0.145, 0.012, M.toy_blue, n=14, m=4)
    for i, (dx, dy, lean, mat) in enumerate(((0.04, 0.02, 0.12, M.crepe), (-0.05, 0.03, -0.15, M.velvet_ox), (0.0, -0.06, 0.06, M.wool))):
        top = (dx + lean * 0.9, dy + lean * 0.3, 0.98)
        g.tube([(dx, dy, 0.05), top], 0.01, M.walnut_dark, n=4)
        g.lathe((dx + lean * 0.35, dy + lean * 0.12, 0.3), [(0.01, 0), (0.06, 0.12), (0.04, 0.5), (0.01, 0.58)], mat, n=6, rx=-lean * 0.3, ry=lean)
        g.torus((top[0] + 0.04, top[1], top[2]), 0.04, 0.009, M.walnut_dark, n=8, m=3, rx=HALF, arc=PI)
    g.tube([(-0.08, -0.03, 0.05), (-0.16, -0.08, 1.0)], 0.012, M.walnut, n=5)
    g.sphere((-0.16, -0.08, 1.0), 0.025, M.brass, n=6)
    p.body.collide((0, 0, 0.3), (0.32, 0.32, 0.6))
    p.params.setdefault('sound', 'clatter')


def bust(p, M, who='man'):
    """Marble bust on a pedestal; the head turns (spin about the vertical)."""
    pedestal(p.body, M, 1.05)
    b = p.body
    b.lathe((0, 0, 1.05), [(0.12, 0), (0.1, 0.05), (0.13, 0.08)], M.marble, n=10)
    b.sphere((0, 0, 1.26), 0.2, M.marble, n=10, s=(1.25, 0.62, 0.62))
    b.cyl((0, 0, 1.3), 0.055, 0.14, M.marble, n=8)
    hd = p.part('pivot', (0, 0, 1.42))
    g = hd.geo
    g.sphere((0, 0, 0.11), 0.1, M.marble, n=10, s=(0.86, 0.96, 1.15))
    g.prism((0, -0.088, 0.085), [(-0.012, 0), (0.012, 0), (0, 0.04)], 0.025, M.marble, rx=HALF + 0.3)
    for sx in (-1, 1):
        g.sphere((sx * 0.085, 0.0, 0.11), 0.022, M.marble, n=5, s=(0.5, 1, 1.3))
    if who == 'man':
        g.sphere((0, 0.02, 0.15), 0.096, M.marble, n=10, s=(0.9, 1.0, 0.8))
    else:
        g.sphere((0, 0.07, 0.19), 0.06, M.marble, n=8)
        g.sphere((0, 0.01, 0.16), 0.102, M.marble, n=10, s=(0.92, 1.02, 0.85))
    for sx in (-1, 1):
        g.sphere((sx * 0.035, -0.09, 0.115), 0.012, M.marble_dark, n=5)
    p.params.setdefault('axis', 'y')
    p.params.setdefault('speed', 0.0)
    p.params.setdefault('wobble', 0.0)
    p.params.setdefault('sound', 'whirr')


def armour(p, M, halberd=True):
    """Suit of armour on a plinth. The visor is the hinge (axis x)."""
    b = p.body
    b.box((0, 0, 0.08), (0.7, 0.55, 0.16), M.walnut_dark, bevel=0.02)
    for sx in (-1, 1):
        x = sx * 0.11
        b.lathe((x, 0, 0.16), [(0.07, 0), (0.08, 0.04), (0.05, 0.1), (0.055, 0.45), (0.07, 0.5), (0.06, 0.58), (0.07, 0.95)], M.steel, n=10)
        b.box((x, -0.05, 0.2), (0.11, 0.2, 0.08), M.steel, bevel=0.02)
        b.sphere((x, -0.02, 0.62), 0.07, M.steel, n=8)
    b.lathe((0, 0, 0.95), [(0.17, 0), (0.2, 0.08), (0.17, 0.2), (0.21, 0.42), (0.23, 0.55), (0.14, 0.62), (0.08, 0.66)], M.steel, n=12)
    b.box((0, -0.12, 1.18), (0.03, 0.06, 0.4), M.steel)
    for sx in (-1, 1):
        b.sphere((sx * 0.26, 0, 1.48), 0.1, M.steel, n=10, s=(1.1, 1, 0.8))
        hand = (sx * 0.3, -0.18, 1.0) if sx > 0 or not halberd else (sx * 0.34, -0.12, 1.1)
        b.tube([(sx * 0.28, 0, 1.42), (sx * 0.31, -0.04, 1.2), hand], 0.055, M.steel, n=8)
        b.sphere(hand, 0.055, M.steel, n=8)
    hp = (-0.34, -0.12, 0.0)
    if halberd:
        b.cyl(hp, 0.018, 2.35, M.walnut, n=6)
        b.prism((hp[0], hp[1], 2.05), [(0, 0), (0.22, 0.05), (0.2, 0.2), (0, 0.15)], 0.012, M.steel, rx=HALF)
        b.prism((hp[0], hp[1], 2.2), [(-0.02, 0), (0.02, 0), (0, 0.32)], 0.02, M.steel, rx=HALF)
    b.lathe((0, 0, 1.6), [(0.06, 0), (0.12, 0.04), (0.14, 0.14), (0.13, 0.26), (0.08, 0.34), (0.001, 0.36)], M.steel, n=12)
    b.box((0, 0.0, 1.97), (0.02, 0.22, 0.06), M.velvet_ox)
    vis = p.part('pivot', (0, -0.02, 1.8))
    vis.geo.box((0, -0.12, -0.06), (0.24, 0.05, 0.14), M.steel, bevel=0.02)
    for k in range(3):
        vis.geo.box((0, -0.15, -0.09 + k * 0.035), (0.18, 0.012, 0.008), M.black)
    for sx in (-1, 1):
        vis.geo.box((sx * 0.13, -0.06, -0.03), (0.02, 0.1, 0.03), M.steel)
    b.collide((0, 0, 1.0), (0.6, 0.5, 2.0))
    p.params.setdefault('axis', 'x')
    p.params.setdefault('dir', -1)
    p.params.setdefault('closed', 0.0)
    p.params.setdefault('open', 0.9)
    p.params.setdefault('sound', 'clatter')


def bell(p, M, label_mat=None, tone=880):
    """Servants' bell on a coiled spring; origin at the spring mount on the bell board."""
    pv = p.part('pivot', (0, -0.06, 0))
    g = pv.geo
    coil = [(0.025 * math.cos(t * 2.2), 0.025 * math.sin(t * 2.2), -t * 0.022) for t in np.linspace(0, 6, 26)]
    g.tube(coil, 0.004, M.brass, n=3, caps=False)
    g.lathe((0, 0, -0.32), [(0.075, 0), (0.07, 0.015), (0.05, 0.07), (0.04, 0.12), (0.02, 0.15), (0.001, 0.16)], M.brass, n=12)
    g.sphere((0, 0, -0.33), 0.016, M.brass, n=5)
    p.body.box((0, -0.03, 0), (0.06, 0.06, 0.04), M.brass)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('tone', tone)
    p.params.setdefault('sound', 'bell')


def gong(p, M):
    b = p.body
    b.box((0, 0, 0.05), (0.9, 0.35, 0.1), M.walnut_dark, bevel=0.015)
    for sx in (-1, 1):
        b.lathe((sx * 0.38, 0, 0.1), [(0.05, 0), (0.035, 0.05), (0.03, 1.3), (0.045, 1.34), (0.02, 1.4)], M.walnut_dark, n=8)
    b.box((0, 0, 1.38), (0.86, 0.07, 0.07), M.walnut_dark, bevel=0.01)
    b.prism((0, 0.035, 1.42), [(-0.3, 0), (0.3, 0), (0.0, 0.14)], 0.07, M.walnut_dark, rx=HALF)
    pv = p.part('pivot', (0, 0, 1.34))
    g = pv.geo
    for sx in (-1, 1):
        g.cyl((sx * 0.1, 0, -0.18), 0.004, 0.18, M.brass, n=3)
    g.cyl((0, 0.02, -0.52), 0.3, 0.04, M.brass, n=24, rx=HALF)
    g.torus((0, -0.02, -0.52), 0.29, 0.02, M.brass, n=24, m=4, rx=HALF)
    g.sphere((0, -0.025, -0.52), 0.06, M.brass, n=10, s=(1, 0.3, 1))
    b.tube([(0.38, -0.05, 1.0), (0.42, -0.08, 0.68)], 0.012, M.walnut, n=4)
    b.sphere((0.42, -0.08, 0.66), 0.045, M.velvet_ox, n=8)
    b.collide((0, 0, 0.7), (0.9, 0.35, 1.4))
    p.params.setdefault('axis', 'x')
    p.params.setdefault('tone', 140)
    p.params.setdefault('sound', 'gong')


def telescope(p, M):
    b = p.body
    for i in range(3):
        a = i * TAU / 3 + 0.3
        b.tube([(0, 0, 1.1), (math.cos(a) * 0.45, math.sin(a) * 0.45, 0.0)], 0.02, M.walnut, n=5)
        b.sphere((math.cos(a) * 0.45, math.sin(a) * 0.45, 0.01), 0.025, M.brass, n=6)
    b.cyl((0, 0, 1.05), 0.06, 0.12, M.brass, n=10)
    pv = p.part('pivot', (0, 0, 1.2))
    g = pv.geo
    g.box((0, 0, 0.0), (0.08, 0.08, 0.06), M.brass, bevel=0.01)
    with g.at((0, 0, 0.08), 0, 0.5):
        g.cyl((0, 0.45, 0), 0.06, 0.9, M.brass, n=12, rx=HALF)
        g.cyl((0, 0.47, 0), 0.07, 0.06, M.brass, n=12, rx=HALF)
        g.cyl((0, -0.45, 0), 0.045, 0.32, M.brass, n=10, rx=HALF)
        g.cyl((0, -0.77, 0), 0.025, 0.12, M.black, n=8, rx=HALF)
        g.cyl((0, 0.15, 0.08), 0.02, 0.3, M.brass, n=6, rx=HALF)
    p.body.collide((0, 0, 0.6), (0.6, 0.6, 1.2))
    p.params.setdefault('axis', 'y')
    p.params.setdefault('speed', 0.0)
    p.params.setdefault('wobble', 0.01)
    p.params.setdefault('sound', 'whirr')


def typewriter(p, M):
    pv = p.part('pivot')
    g = pv.geo
    g.box((0, 0, 0.05), (0.38, 0.32, 0.1), M.black, bevel=0.015)
    g.box((0, 0.06, 0.13), (0.34, 0.18, 0.08), M.black, bevel=0.02, rx=-0.2)
    for r in range(4):
        for c in range(10 - r % 2):
            g.cyl((-0.14 + c * 0.03 + (r % 2) * 0.015, -0.12 + r * 0.035, 0.1 + r * 0.015), 0.011, 0.012, M.porcelain, n=6)
    g.cyl((-0.22, 0.13, 0.2), 0.03, 0.44, M.black, n=10, ry=HALF)
    g.box((0, 0.16, 0.3), (0.22, 0.004, 0.24), M.paper, rx=-0.15)
    g.torus((0, 0.05, 0.16), 0.08, 0.008, M.steel, n=12, m=3, arc=PI, rx=HALF)
    p.params.setdefault('sound', 'clatter')


def owl(p, M):
    """Stuffed owl on a T-perch under a glass dome; its head turns."""
    b = p.body
    b.cyl((0, 0, 0), 0.16, 0.05, M.walnut, n=14)
    b.cyl((0, 0, 0.05), 0.015, 0.25, M.walnut_dark, n=5)
    b.cyl((-0.1, 0, 0.3), 0.015, 0.2, M.walnut_dark, n=5, ry=HALF)
    b.blob((0, 0, 0.42), 0.11, M.owl, seed=4, jitter=0.08, s=(0.9, 0.85, 1.3))
    b.blob((0, -0.03, 0.4), 0.09, M.linen, seed=5, jitter=0.1, s=(0.7, 0.5, 1.1))
    for sx in (-1, 1):
        b.box((sx * 0.025, -0.02, 0.3), (0.02, 0.04, 0.02), M.brass)
    hd = p.part('pivot', (0, 0, 0.56))
    g = hd.geo
    g.sphere((0, 0, 0.05), 0.085, M.owl, n=10, s=(1.05, 0.95, 0.9))
    for sx in (-1, 1):
        g.sphere((sx * 0.036, -0.07, 0.06), 0.026, M.owl_face, n=8, s=(1, 0.5, 1))
        g.sphere((sx * 0.036, -0.082, 0.06), 0.014, M.amber, n=6)
        g.prism((sx * 0.05, 0.0, 0.11), [(-0.02, 0), (0.02, 0), (sx * 0.015, 0.06)], 0.02, M.owl, rx=HALF)
    g.box((0, -0.085, 0.035), (0.012, 0.02, 0.025), M.black)
    p.params.setdefault('axis', 'y')
    p.params.setdefault('speed', 0.0)
    p.params.setdefault('wobble', 0.02)
    p.params.setdefault('sound', 'whirr')


def cabinet(p, M, w=1.3, d=0.45, h=2.2, wood=None, contents='china', seed=0):
    """Tall glazed cabinet; the right-hand door is the hinge, swinging toward -Y."""
    wood = wood or M.mahogany
    b = p.body
    rng = jitter_rng(seed)
    b.box((0, 0, 0.08), (w + 0.06, d + 0.04, 0.16), wood, bevel=0.015)
    b.box((0, d / 2 - 0.02, h / 2), (w, 0.04, h), wood)
    for sx in (-1, 1):
        b.box((sx * (w / 2 - 0.02), 0, h / 2), (0.04, d, h), wood)
    b.box((0, 0, h - 0.02), (w + 0.1, d + 0.08, 0.06), wood, bevel=0.015)
    b.prism((0, -d / 2 - 0.04, h + 0.01), [(-w / 2, 0), (w / 2, 0), (w / 2 - 0.1, 0.1), (0.1, 0.12), (0, 0.2), (-0.1, 0.12), (-w / 2 + 0.1, 0.1)], 0.04, wood, rx=-HALF)
    b.box((0, 0, 0.18), (w - 0.06, d - 0.04, 0.04), wood)
    b.box((0, 0, 0.9), (w - 0.06, d - 0.04, 0.03), wood)
    for z in (1.3, 1.7):
        b.box((0, 0.02, z), (w - 0.06, d - 0.1, 0.02), M.glass_dark)
    for zz in (0.24, 0.94, 1.32, 1.72):
        x = -w / 2 + 0.12
        while x < w / 2 - 0.12:
            if contents == 'china':
                if rng.random() < 0.6:
                    b.cyl((x, d / 2 - 0.1, zz + 0.12), 0.11, 0.012, M.porcelain if rng.random() < 0.7 else M.toy_blue, n=10, rx=HALF - 0.2)
                    x += 0.24
                else:
                    goblet(b, M, (x, -0.02, zz))
                    x += 0.12
            else:
                r = rng.random()
                if r < 0.3:
                    b.sphere((x, 0, zz + 0.08), 0.07, M.bone, n=8, s=(0.9, 1.1, 1))
                    for sx in (-1, 1):
                        b.sphere((x + sx * 0.025, -0.06, zz + 0.09), 0.015, M.black, n=4)
                    x += 0.2
                elif r < 0.7:
                    jar(b, M, (x, 0, zz), rng.uniform(0.15, 0.25), 0.05, M.glass_green, M.brass)
                    x += 0.15
                else:
                    book(b, M, (x + 0.08, 0, zz), 0.16, 0.22, 0.04, rng.uniform(-0.4, 0.4), rng.choice(M.books))
                    x += 0.22
    b.box((-w / 4, -d / 2 + 0.01, 0.55), (w / 2 - 0.05, 0.02, 0.62), wood, bevel=0.005)
    b.box((w / 4, -d / 2 + 0.01, 0.55), (w / 2 - 0.05, 0.02, 0.62), wood, bevel=0.005)
    # left glass door (static)
    dw = w / 2 - 0.03
    frame_rect(b, (-w / 4, -d / 2 + 0.01, 1.4), dw, h - 1.0, 0.06, 0.03, wood)
    b.box((-w / 4, -d / 2 + 0.01, 1.4), (dw - 0.1, 0.01, h - 1.1), M.glass_dark)
    b.box((-w / 4, -d / 2 + 0.01, 1.4), (0.02, 0.025, h - 1.1), wood)
    pv = p.part('pivot', (w / 2 - 0.03, -d / 2 + 0.01, 0))
    g = pv.geo
    frame_rect(g, (-dw / 2, 0, 1.4), dw, h - 1.0, 0.06, 0.03, wood)
    g.box((-dw / 2, 0, 1.4), (dw - 0.1, 0.01, h - 1.1), M.glass_dark)
    g.box((-dw / 2, 0, 1.4), (0.02, 0.025, h - 1.1), wood)
    g.sphere((-dw + 0.06, -0.03, 1.3), 0.02, M.brass, n=6)
    b.collide((0, 0, h / 2), (w, d, h))
    p.params.setdefault('axis', 'y')
    p.params.setdefault('dir', -1)
    p.params.setdefault('closed', 0.0)
    p.params.setdefault('open', 1.5)
    p.params.setdefault('sound', 'bang')


def wardrobe(p, M, w=1.2, d=0.55, h=2.0, wood=None):
    wood = wood or M.pine
    b = p.body
    b.box((0, 0, h / 2), (w, d, h), wood, bevel=0.015)
    b.box((0, 0, h + 0.04), (w + 0.08, d + 0.06, 0.08), wood, bevel=0.015)
    b.box((0, 0, 0.05), (w + 0.04, d + 0.04, 0.1), M.walnut_dark)
    b.box((-w / 4, -d / 2 - 0.01, h / 2 + 0.05), (w / 2 - 0.04, 0.02, h - 0.2), wood, bevel=0.005)
    b.box((-w / 4, -d / 2 - 0.02, h * 0.62), (w / 2 - 0.2, 0.01, h * 0.45), M.toy_blue)
    b.box((-w / 4, -d / 2 - 0.02, h * 0.22), (w / 2 - 0.2, 0.01, h * 0.22), M.toy_blue)
    pv = p.part('pivot', (w / 2 - 0.02, -d / 2 - 0.01, 0), rz=-0.18)
    g = pv.geo
    g.box((-w / 4 + 0.0, 0, h / 2 + 0.05), (w / 2 - 0.04, 0.025, h - 0.2), wood, bevel=0.005)
    g.box((-w / 4, -0.015, h * 0.62), (w / 2 - 0.2, 0.01, h * 0.45), M.toy_blue)
    g.box((-w / 4, -0.015, h * 0.22), (w / 2 - 0.2, 0.01, h * 0.22), M.toy_blue)
    g.sphere((-w / 2 + 0.08, -0.03, h * 0.5), 0.02, M.brass, n=6)
    # a small dress hangs just inside, visible through the gap
    b.sheet((0.15, 0.0, h - 0.25), 0.35, 0.9, M.linen, nx=2, ny=2)
    b.collide((0, 0, h / 2), (w, d, h))
    p.params.setdefault('axis', 'y')
    p.params.setdefault('dir', -1)
    p.params.setdefault('closed', -0.18)  # authored ajar at -0.18 with dir -1
    p.params.setdefault('open', 1.4)
    p.params.setdefault('sound', 'creak')


def gramophone(p, M):
    b = p.body
    b.box((0, 0, 0.35), (0.5, 0.45, 0.7), M.mahogany, bevel=0.015)
    b.box((0, -0.226, 0.35), (0.4, 0.01, 0.5), M.walnut_dark)
    b.box((0, 0, 0.82), (0.42, 0.42, 0.24), M.mahogany, bevel=0.012)
    b.box((0, 0, 0.95), (0.44, 0.44, 0.02), M.walnut_dark)
    pv = p.part('pivot', (-0.02, 0.0, 0.96))
    pv.geo.cyl((0, 0, 0), 0.16, 0.012, M.felt, n=20)
    pv.geo.cyl((0, 0, 0.012), 0.15, 0.004, M.black, n=20)
    pv.geo.cyl((0, 0, 0.016), 0.04, 0.002, M.velvet_ox, n=12)
    pv.geo.cyl((0, 0, 0.0), 0.006, 0.04, M.brass, n=5)
    b.cyl((0.17, 0.15, 0.96), 0.02, 0.06, M.brass, n=8)
    b.tube([(0.17, 0.15, 1.02), (0.12, 0.05, 1.0), (0.06, -0.06, 0.985)], 0.008, M.brass, n=5)
    b.tube([(0.17, 0.15, 1.02), (0.17, 0.2, 1.12), (0.12, 0.25, 1.25)], 0.025, M.brass, n=6)
    b.lathe((0.12, 0.25, 1.25), [(0.03, 0), (0.05, 0.1), (0.1, 0.22), (0.2, 0.33), (0.3, 0.38)], M.brass, n=14, cap_top=False, cap_bottom=False, rx=0.9, rz=0.3)
    b.collide((0, 0, 0.5), (0.5, 0.45, 1.0))
    p.params.setdefault('axis', 'y')
    p.params.setdefault('speed', 0.0)
    p.params.setdefault('sound', 'whirr')


def music_stand(p, M):
    pv = p.part('pivot')
    music_stand_geo(pv.geo, M)
    p.params.setdefault('sound', 'clatter')


def music_stand_geo(g, M):
    for i in range(3):
        a = i * TAU / 3 + 0.5
        g.tube([(0, 0, 0.25), (math.cos(a) * 0.25, math.sin(a) * 0.25, 0.01)], 0.01, M.iron, n=4)
    g.cyl((0, 0, 0.2), 0.012, 0.9, M.iron, n=5)
    with g.at((0, 0, 1.12), 0, -0.35):
        g.box((0, 0, 0), (0.5, 0.012, 0.34), M.iron)
        g.box((0, -0.03, -0.17), (0.5, 0.05, 0.012), M.iron)
        g.box((-0.06, -0.012, 0.0), (0.26, 0.004, 0.34), M.paper, ry=0.03)
        g.box((0.12, -0.014, 0.01), (0.24, 0.004, 0.32), M.paper, ry=-0.05)


def metronome(p, M):
    b = p.body
    b.lathe((0, 0, 0), [(0.1, 0), (0.1, 0.02), (0.035, 0.24), (0.001, 0.26)], M.walnut, n=4, smooth=False, rz=PI / 4)
    b.box((0, -0.045, 0.1), (0.06, 0.01, 0.14), M.paper, rx=0.25)
    pv = p.part('pivot', (0, -0.05, 0.03))
    pv.geo.box((0, 0, 0.12), (0.006, 0.006, 0.24), M.brass)
    pv.geo.box((0, 0, 0.17), (0.035, 0.015, 0.03), M.brass, bevel=0.005)
    p.params.setdefault('axes', 'z')
    p.params.setdefault('amp', 0.0)
    p.params.setdefault('period', 1.0)
    p.params.setdefault('sound', 'squeak')


def dust_sheet(p, M, shape='chair'):
    """Furniture shrouded in a dust sheet; the skirt panels are cloth parts."""
    b = p.body
    if shape == 'chair':
        w, d, top = 0.8, 0.75, 0.5
        b.box((0, 0, top - 0.04), (w, d, 0.1), M.linen, bevel=0.06)
        b.box((0, d / 2 - 0.1, top + 0.35), (w - 0.05, 0.2, 0.75), M.linen, bevel=0.08, rx=-0.1)
        b.blob((0, d / 2 - 0.1, top + 0.72), 0.32, M.linen, seed=2, jitter=0.1, s=(1.3, 0.4, 0.35))
        b.collide((0, 0, 0.55), (w, d, 1.1))
        sides = [((0, -d / 2 - 0.01, top), 0, w + 0.06), ((-w / 2 - 0.01, 0, top), -HALF, d), ((w / 2 + 0.01, 0, top), HALF, d)]
    else:  # grand piano
        w, d, top = 1.5, 2.0, 1.0
        b.box((0, 0, top - 0.06), (w, d * 0.6, 0.12), M.linen, bevel=0.05)
        b.prism((0, d * 0.3 - 0.02, top - 0.12), [(-w / 2, 0), (w / 2, 0), (w / 2 - 0.08, 0.35), (w / 2 - 0.3, 0.62), (0.05, 0.8), (-0.45, 0.66), (-w / 2, 0.32)], 0.12, M.linen)
        b.box((0, -d * 0.3 + 0.1, top + 0.06), (w * 0.96, 0.22, 0.12), M.linen, bevel=0.05)
        for k, (x, y) in enumerate(((-0.4, 0.1), (0.3, 0.45), (0.1, -0.2))):
            b.sphere((x, y, top + 0.01), 0.22, M.linen, n=8, s=(1.4, 1.0, 0.25))
        b.cyl((0, 0.15, 0), 0.06, top - 0.1, M.linen, n=6)
        b.collide((0, 0.15, 0.55), (w, d, 1.1))
        sides = [((0, -d * 0.3 - 0.01, top), 0, w + 0.04), ((-w / 2 - 0.01, 0.1, top), -HALF, d * 0.75), ((w / 2 + 0.01, 0.15, top), HALF, d * 0.8)]
    for i, (pos, rz, sw) in enumerate(sides):
        g = p.geo(f'cloth{i}', pos, rz=rz)
        g.sheet((0, 0, 0), sw, top - 0.02, M.linen, nx=6, ny=6)
    p.params.setdefault('amp', 0.02)
    p.params.setdefault('sound', 'whoosh')


def lectern_book(p, M):
    b = p.body
    b.lathe((0, 0, 0), [(0.2, 0), (0.18, 0.04), (0.05, 0.08), (0.04, 0.9), (0.06, 0.95)], M.walnut, n=10)
    with b.at((0, 0, 1.05), 0, 0.42):
        b.box((0, 0, 0), (0.6, 0.45, 0.04), M.walnut, bevel=0.01)
        b.box((0, -0.24, 0.03), (0.6, 0.03, 0.05), M.walnut)
        for sx in (-1, 1):
            b.box((sx * 0.14, 0, 0.035), (0.27, 0.36, 0.035), M.books[0], ry=-sx * 0.06)
            b.box((sx * 0.13, 0, 0.06), (0.25, 0.34, 0.02), M.paper, ry=-sx * 0.04)
    # a loose page lifting off the open book
    a = 0.42
    pg = p.geo('cloth0', (0.13, 0.17 * math.cos(a), 1.05 + 0.17 * math.sin(a) + 0.075), rx=a - HALF)
    pg.sheet((0, 0, 0), 0.24, 0.33, M.paper, nx=6, ny=6)
    b.collide((0, 0, 0.6), (0.6, 0.5, 1.2))
    p.params.setdefault('amp', 0.012)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('sound', 'rustle')


def ladder(p, M, h=2.9, lean=0.32):
    """Library ladder hooked on a rail; origin at the hook (top), ladder leaning toward -Y."""
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    foot_y = -h * math.tan(lean)
    for sx in (-1, 1):
        g.tube([(sx * 0.22, 0.0, 0.0), (sx * 0.22, foot_y, -h + 0.08)], 0.025, M.walnut, n=6)
        g.cyl((sx * 0.22 - 0.02, foot_y, -h + 0.05), 0.045, 0.04, M.brass, n=8, ry=HALF)
        g.torus((sx * 0.22, 0.03, 0.0), 0.04, 0.01, M.brass, n=8, m=3, rx=0, ry=HALF)
    for k in range(1, 10):
        t = k / 10
        g.box((0, foot_y * t, -h * t), (0.44, 0.07, 0.025), M.walnut)
    p.params.setdefault('axes', 'z')
    p.params.setdefault('amp', 0.004)
    p.params.setdefault('period', 3.0)
    p.params.setdefault('sound', 'creak')


def globe(p, M):
    pf.globe(p, M.walnut, M.brass, M.sea, M.pine)


def spider(p, M, drop=1.6):
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.cyl((0, 0, -drop), 0.0025, drop, M.lace, n=3)
    g.sphere((0, 0, -drop - 0.03), 0.03, M.black, n=8, s=(1, 1.2, 0.9))
    g.sphere((0, -0.035, -drop - 0.035), 0.018, M.black, n=6)
    for sx in (-1, 1):
        for k in range(4):
            a = -0.6 + k * 0.4
            g.tube([(0, 0, -drop - 0.03), (sx * 0.05, math.sin(a) * 0.05, -drop - 0.0), (sx * 0.08, math.sin(a) * 0.07, -drop - 0.06)], 0.004, M.black, n=3)
    p.params.setdefault('amp', 0.05)
    p.params.setdefault('sound', 'squeak')


def marionette(p, M):
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.box((0, 0, 0), (0.3, 0.03, 0.03), M.walnut)
    g.box((0, 0, 0), (0.03, 0.22, 0.03), M.walnut)
    body_top = -0.7
    for (sx, sy, ex, ez) in ((-0.15, 0, -0.14, body_top - 0.25), (0.15, 0, 0.14, body_top - 0.25), (0, 0.11, 0, body_top + 0.02), (0, -0.11, 0.06, body_top - 0.62)):
        g.tube([(sx, sy, 0), (ex, sy * 0.3, ez)], 0.002, M.lace, n=3, caps=False)
    g.sphere((0, 0, body_top - 0.08), 0.075, M.porcelain, n=10)
    for sx in (-1, 1):
        g.sphere((sx * 0.026, -0.065, body_top - 0.07), 0.012, M.black, n=4)
        g.sphere((sx * 0.045, -0.06, body_top - 0.11), 0.016, M.toy_red, n=4)
    g.lathe((0, 0, body_top + 0.0), [(0.001, 0.0), (0.05, -0.02), (0.08, -0.05)], M.toy_red, n=8)
    g.lathe((0, 0, body_top - 0.48), [(0.15, 0), (0.1, 0.2), (0.06, 0.32)], M.velvet_ox, n=10, cap_bottom=False)
    for sx in (-1, 1):
        g.tube([(sx * 0.06, 0, body_top - 0.18), (sx * 0.14, -0.02, body_top - 0.28)], 0.018, M.velvet_ox, n=5)
        g.sphere((sx * 0.14, -0.02, body_top - 0.29), 0.022, M.porcelain, n=5)
        g.tube([(sx * 0.05, 0, body_top - 0.48), (sx * 0.06, -0.03, body_top - 0.66)], 0.016, M.black, n=5)
    p.params.setdefault('amp', 0.03)
    p.params.setdefault('sound', 'squeak')


def hanging_meat(p, M, kind='ham'):
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.torus((0, 0, -0.04), 0.035, 0.007, M.iron, n=8, m=3, rx=HALF)
    g.cyl((0, 0, -0.35), 0.004, 0.31, M.wicker, n=3)
    if kind == 'ham':
        g.blob((0, 0, -0.58), 0.16, M.roast, seed=7, jitter=0.12, s=(0.9, 0.75, 1.5))
        g.cyl((0, 0, -0.38), 0.035, 0.1, M.bone, n=6)
    else:  # brace of pheasants
        for sx in (-1, 1):
            g.blob((sx * 0.07, 0, -0.55), 0.09, M.owl, seed=sx + 3, jitter=0.15, s=(0.7, 0.7, 1.6))
            g.tube([(sx * 0.07, 0, -0.69), (sx * 0.1, 0, -1.0)], 0.012, M.owl_face, n=4)
    p.params.setdefault('amp', 0.02)
    p.params.setdefault('sound', 'squeak')


def hanging_pan(p, M, r=0.15, mat=None, pot=False):
    mat = mat or M.copper
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.tube([(0, 0, 0.02), (0, -0.02, -0.04), (0, 0.0, -0.08)], 0.006, M.iron, n=3, caps=False)
    if pot:
        g.cyl((0, 0, -0.1), 0.004, 0.02, M.iron, n=3)
        g.lathe((0, 0, -0.38), [(r * 0.9, 0), (r, 0.03), (r, 0.22), (r * 1.06, 0.24)], mat, n=14, cap_top=False)
        g.torus((0, 0, -0.14), r * 1.04, 0.008, M.iron, n=12, m=3, rx=HALF, arc=PI)
    else:
        g.box((0, 0, -0.18), (0.035, 0.012, 0.2), M.iron)
        g.cyl((0, 0.035, -0.28 - r), r, 0.04, mat, n=16, rx=-HALF)
        g.torus((0, 0.035, -0.28 - r), r, 0.01, mat, n=16, m=3, rx=HALF)
    p.params.setdefault('amp', 0.03)
    p.params.setdefault('period', 1.4)
    p.params.setdefault('sound', 'clatter')


def pot_rack(g, M, L=2.4, drop=1.1, ceil=4.2):
    z = ceil - drop
    g.box((0, 0, z), (L, 0.05, 0.05), M.iron, bevel=0.005)
    g.box((0, 0.35, z), (L, 0.05, 0.05), M.iron, bevel=0.005)
    for sx in (-1, 1):
        g.box((sx * L / 2, 0.175, z), (0.05, 0.4, 0.05), M.iron)
        g.tube([(sx * L / 2, 0.175, z), (sx * L / 2 * 0.8, 0.175, ceil)], 0.008, M.iron, n=3)


def kettle(p, M):
    pv = p.part('pivot')
    g = pv.geo
    g.lathe((0, 0, 0), [(0.09, 0), (0.12, 0.04), (0.12, 0.12), (0.08, 0.18), (0.04, 0.2)], M.copper, n=14)
    g.tube([(0.1, 0, 0.06), (0.17, 0, 0.12), (0.2, 0, 0.18)], 0.015, M.copper, n=6)
    g.torus((0, 0, 0.22), 0.09, 0.01, M.iron, n=12, m=3, rx=HALF, arc=PI)
    g.sphere((0, 0, 0.21), 0.02, M.black, n=6)
    p.params.setdefault('sound', 'clatter')


def cleaver_block(p, M):
    """A cleaver left stuck in a joint of meat on the butcher block (jolt: it jumps)."""
    pv = p.part('pivot')
    g = pv.geo
    g.blob((0, 0, 0.06), 0.11, M.roast, seed=3, jitter=0.15, s=(1.3, 0.9, 0.6))
    with g.at((0.02, 0, 0.1), 0.3, 0.2):
        g.box((0, 0, 0.06), (0.2, 0.008, 0.11), M.steel)
        g.box((0.17, 0, 0.1), (0.14, 0.022, 0.03), M.walnut_dark, bevel=0.006)
    p.params.setdefault('sound', 'thud')


def barrel(p, M, h=0.9, r=0.32):
    pf.barrel(p, M.pine, M.iron, h, r)


def crate(p, M, s=0.6):
    pf.crate(p, M.pine, M.walnut_dark, s)


def laundry(p, M, L=4.0, ceil=4.2, drop=1.7, n=2):
    """Washing line strung across the room with sheets; origin at line centre (floor)."""
    b = p.body
    z = ceil - drop
    b.cyl((-L / 2, 0, z), 0.006, L, M.wicker, n=3, ry=HALF)
    for sx in (-1, 1):
        b.cyl((sx * L / 2, 0, 0), 0.035, z + 0.12, M.pine, n=6)
        b.box((sx * L / 2, 0, z + 0.06), (0.06, 0.3, 0.04), M.pine)
        b.cyl((sx * L / 2, 0, 0), 0.14, 0.05, M.pine, n=6)
        b.collide((sx * L / 2, 0, (z + 0.1) / 2), (0.1, 0.1, z + 0.1))
    pieces = [(-0.3, 0.42, 1.5, M.linen), (0.18, 0.3, 0.75, M.paper), (0.36, 0.2, 0.9, M.linen)]
    for i in range(n):
        f, fw, fh, mat = pieces[i % 3]
        x = f * L
        sw = fw * L
        g = p.geo(f'cloth{i}', (x, 0, z - 0.02))
        g.sheet((0, 0, 0), sw, fh, mat, nx=6, ny=8)
        for k in (-1, 1):
            b.box((x + k * sw * 0.45, 0, z - 0.01), (0.012, 0.025, 0.06), M.pine)
    p.params.setdefault('amp', 0.05)
    p.params.setdefault('sound', 'whoosh')


def pump(p, M):
    b = p.body
    b.lathe((0, 0, 0), [(0.12, 0), (0.1, 0.06), (0.07, 0.1), (0.06, 1.45)], M.iron, n=10)
    b.collide((0, 0, 0.7), (0.24, 0.24, 1.4))
    b.lathe((0, 0, 1.45), [(0.06, 0), (0.07, 0.03), (0.05, 0.08), (0.02, 0.12)], M.iron, n=10)
    b.tube([(0, -0.05, 1.25), (0, -0.2, 1.24), (0, -0.25, 1.15)], 0.025, M.iron, n=6)
    pv = p.part('pivot', (0, 0.06, 1.48))
    pv.geo.tube([(0, 0, 0), (0, 0.2, 0.12), (0, 0.45, 0.1)], 0.018, M.iron, n=5)
    pv.geo.sphere((0, 0.46, 0.1), 0.03, M.iron, n=6)
    p.params.setdefault('axis', 'x')
    p.params.setdefault('dir', 1)
    p.params.setdefault('closed', 0.0)
    p.params.setdefault('open', 0.5)
    p.params.setdefault('sound', 'squeak')


def mangle(p, M):
    b = p.body
    for sx in (-1, 1):
        b.prism((sx * 0.3, 0, 0), [(-0.25, 0), (0.25, 0), (0.12, 1.0), (-0.12, 1.0)], 0.05, M.iron, rx=HALF, rz=HALF)
    b.cyl((-0.3, 0, 0.85), 0.08, 0.6, M.pine, n=12, ry=HALF)
    b.cyl((-0.3, 0, 0.68), 0.08, 0.6, M.pine, n=12, ry=HALF)
    b.box((0, -0.25, 0.75), (0.6, 0.35, 0.03), M.pine, rx=0.2)
    b.box((0, 0, 0.04), (0.8, 0.5, 0.08), M.iron)
    pv = p.part('pivot', (0.36, 0, 0.85))
    g = pv.geo
    g.torus((0, 0, 0), 0.36, 0.025, M.iron, n=20, m=4, ry=HALF)
    for k in range(5):
        a = k * TAU / 5
        g.box((0, math.cos(a) * 0.18, math.sin(a) * 0.18), (0.02, 0.36, 0.025), M.iron, rx=a)
    g.cyl((0, 0.0, 0.34), 0.02, 0.15, M.walnut, n=6, ry=HALF)
    b.collide((0, 0, 0.5), (0.8, 0.5, 1.0))
    p.params.setdefault('axis', 'x')
    p.params.setdefault('speed', 0.0)
    p.params.setdefault('sound', 'squeak')


def watering_can(p, M):
    pv = p.part('pivot')
    g = pv.geo
    g.lathe((0, 0, 0), [(0.12, 0), (0.13, 0.02), (0.13, 0.22), (0.1, 0.26)], M.copper, n=14)
    g.tube([(0.1, 0, 0.06), (0.25, 0, 0.2), (0.35, 0, 0.32)], 0.018, M.copper, n=6)
    g.cyl((0.35, 0, 0.32), 0.04, 0.03, M.copper, n=8, ry=1.0)
    g.tube([(-0.12, 0, 0.08), (-0.18, 0, 0.18), (-0.1, 0, 0.3), (0.05, 0, 0.3)], 0.012, M.copper, n=5)
    p.params.setdefault('sound', 'clatter')


def wicker_chair(p, M):
    """Peacock wicker chair."""
    pv = p.part('pivot')
    g = pv.geo
    g.lathe((0, 0, 0), [(0.3, 0), (0.28, 0.04), (0.14, 0.2), (0.2, 0.38), (0.3, 0.44)], M.wicker, n=14)
    g.cyl((0, 0, 0.42), 0.31, 0.06, M.velvet_moss, n=16)
    poly = [(math.cos(a) * 0.4, math.sin(a) * 0.78) for a in np.linspace(0.05, PI - 0.05, 12)]
    poly = [(0.22, 0.0)] + poly + [(-0.22, 0.0)]
    g.prism((0, 0.34, 0.42), poly, 0.035, M.wicker, rx=HALF + 0.12)
    with g.at((0, 0.3, 0.42), 0, 0.12):
        for k in range(7):
            a = 0.25 + k * (PI - 0.5) / 6
            g.box((math.cos(a) * 0.18, -0.02, math.sin(a) * 0.36), (0.012, 0.012, 0.68), M.walnut_dark, ry=-(a - HALF))
        pts = [(math.cos(a) * 0.4, -0.02, math.sin(a) * 0.78) for a in np.linspace(0.05, PI - 0.05, 9)]
        g.tube(pts, 0.028, M.wicker, n=5)
    for sx in (-1, 1):
        g.tube([(sx * 0.3, 0.25, 0.75), (sx * 0.34, 0.0, 0.62), (sx * 0.3, -0.22, 0.48)], 0.03, M.wicker, n=5)
    p.body.collide((0, 0, 0.45), (0.65, 0.65, 0.9))
    p.params.setdefault('sound', 'creak')


def birdcage(p, M, h=0.55, r=0.22, stand=True):
    """Small domed birdcage hanging from a stand; pivot at the hook. A dead canary lies inside."""
    b = p.body
    hook_z = 1.95 if stand else 0.0
    if stand:
        b.lathe((0, 0, 0), [(0.25, 0), (0.22, 0.04), (0.04, 0.1), (0.03, 1.8), (0.05, 1.84), (0.02, 1.9)], M.brass, n=10)
        b.tube([(0, 0, 1.88), (0.15, 0, 2.02), (0.32, 0, 2.0), (0.34, 0, 1.95)], 0.012, M.brass, n=5)
        b.collide((0, 0, 0.6), (0.4, 0.4, 1.2))
    pv = p.part('pivot', (0.34 if stand else 0, 0, hook_z))
    g = pv.geo
    top = -0.08
    g.torus((0, 0, top), 0.03, 0.007, M.brass, n=8, m=3, rx=HALF)
    base_z = top - 0.06 - h
    g.cyl((0, 0, base_z), r + 0.02, 0.04, M.brass, n=14)
    for k in range(14):
        a = k * TAU / 14
        pts = [(math.cos(a) * r, math.sin(a) * r, base_z + 0.04)]
        pts.append((math.cos(a) * r, math.sin(a) * r, base_z + h * 0.7))
        pts.append((math.cos(a) * r * 0.6, math.sin(a) * r * 0.6, base_z + h * 0.93))
        pts.append((0, 0, base_z + h))
        g.tube(pts, 0.004, M.brass, n=3, caps=False)
    g.torus((0, 0, base_z + h * 0.45), r, 0.006, M.brass, n=14, m=3)
    g.cyl((-r * 0.8, 0, base_z + h * 0.3), 0.006, r * 1.6, M.walnut, n=4, ry=HALF)
    g.blob((0.05, 0.02, base_z + 0.065), 0.03, M.amber, seed=2, jitter=0.1, s=(1.6, 0.8, 0.6))
    p.params.setdefault('amp', 0.025)
    p.params.setdefault('period', 1.9)
    p.params.setdefault('sound', 'squeak')


def palm(p, M, h=2.4, seed=0, fronds=8, pot=0.3):
    """Kentia palm in a glazed pot."""
    rng = jitter_rng(seed)
    b = p.body
    b.lathe((0, 0, 0), [(pot * 0.7, 0), (pot * 0.8, 0.05), (pot, pot * 1.2), (pot * 1.1, pot * 1.35), (pot * 0.95, pot * 1.4)], M.terracotta, n=12)
    b.cyl((0, 0, pot * 1.32), pot * 0.92, 0.02, M.coal, n=12)
    b.collide((0, 0, pot * 0.7), (pot * 2.0, pot * 2.0, pot * 1.4))
    pv = p.part('pivot', (0, 0, pot * 1.3))
    g = pv.geo
    trunk = [(0, 0, 0), (0.03, 0.0, h * 0.25), (0.05, 0.02, h * 0.45)]
    g.tube(trunk, 0.05, M.bark, n=6)
    top = trunk[-1]
    for f in range(fronds):
        a = f * TAU / fronds + rng.uniform(-0.25, 0.25)
        L = h * rng.uniform(0.45, 0.6)
        rise = rng.uniform(0.25, 0.6)
        pts = []
        for i in range(6):
            t = i / 5
            d = L * t
            pts.append((top[0] + math.cos(a) * d, top[1] + math.sin(a) * d, top[2] + rise * L * t - L * 0.9 * t * t * (0.6 + rise * 0.3)))
        g.tube(pts, 0.012, M.leaf_dark, n=4)
        mat = rng.choice(M.leaves)
        for i0, i1 in ((0, 3), (2, 5)):
            p0, p1 = pts[i0], pts[i1]
            for sgn in (-1, 1):
                ang = a + sgn * 1.15
                ll = 0.34 if i0 == 0 else 0.26
                tip = ((p0[0] + p1[0]) / 2 + math.cos(ang) * ll, (p0[1] + p1[1]) / 2 + math.sin(ang) * ll, (p0[2] + p1[2]) / 2 - 0.12)
                leaf_blade(g, p0, p1, tip, mat)
    p.params.setdefault('amp', 0.02)
    p.params.setdefault('leaf', '#4a5e30')
    p.params.setdefault('sound', 'rustle')


def fern(p, M, stand_h=0.85, seed=0, dead=False, r=0.45):
    """Boston fern on a turned plant stand."""
    rng = jitter_rng(seed)
    b = p.body
    if stand_h > 0:
        b.lathe((0, 0, 0), [(0.18, 0), (0.15, 0.04), (0.05, 0.1), (0.04, stand_h - 0.1), (0.15, stand_h - 0.04), (0.16, stand_h)], M.walnut, n=10)
        b.collide((0, 0, stand_h / 2), (0.36, 0.36, stand_h))
    b.lathe((0, 0, stand_h), [(0.1, 0), (0.15, 0.05), (0.17, 0.2), (0.15, 0.22)], M.porcelain if not dead else M.terracotta, n=12)
    pv = p.part('pivot', (0, 0, stand_h + 0.2))
    g = pv.geo
    mats = M.leaves if not dead else [M.leaf_dead]
    n = 14
    for f in range(n):
        a = f * TAU / n + rng.uniform(-0.2, 0.2)
        L = r * rng.uniform(0.75, 1.15)
        pts = []
        for i in range(5):
            t = i / 4
            pts.append((math.cos(a) * L * t, math.sin(a) * L * t, 0.3 * L * t - 0.85 * L * t * t))
        mat = rng.choice(mats)
        for sgn in (-1, 1):
            ang = a + sgn * 1.2
            p0, p1 = pts[0], pts[3]
            tip = ((p0[0] + p1[0]) / 2 + math.cos(ang) * 0.12, (p0[1] + p1[1]) / 2 + math.sin(ang) * 0.12, (p0[2] + p1[2]) / 2 - 0.03)
            leaf_blade(g, p0, pts[4], tip, mat)
    g.blob((0, 0, 0.05), 0.14, mats[0], seed=seed, jitter=0.25, s=(1, 1, 0.6))
    p.params.setdefault('amp', 0.025)
    p.params.setdefault('leaf', '#3e5a2c' if not dead else '#6a5a3a')
    p.params.setdefault('sound', 'rustle')


def dead_lilies(p, M, seed=4):
    """A tall urn of lilies left to wilt on the hall table."""
    rng = jitter_rng(seed)
    b = p.body
    b.lathe((0, 0, 0), [(0.1, 0), (0.12, 0.03), (0.08, 0.08), (0.16, 0.25), (0.17, 0.38), (0.1, 0.52), (0.08, 0.6), (0.13, 0.66)], M.porcelain, n=16)
    b.torus((0, 0, 0.36), 0.165, 0.012, M.brass, n=16, m=4)
    pv = p.part('pivot', (0, 0, 0.6))
    g = pv.geo
    for i in range(9):
        a = i * TAU / 9 + rng.uniform(-0.3, 0.3)
        L = rng.uniform(0.45, 0.7)
        droop = rng.uniform(0.2, 0.6)
        pts = [(0, 0, 0), (math.cos(a) * L * 0.25, math.sin(a) * L * 0.25, L * 0.6), (math.cos(a) * L * 0.55, math.sin(a) * L * 0.55, L * (0.95 - droop * 0.3)),
               (math.cos(a) * L * 0.75, math.sin(a) * L * 0.75, L * (0.85 - droop))]
        g.tube(pts, 0.008, M.leaf_dead, n=3)
        tip = pts[-1]
        g.lathe(tip, [(0.005, 0), (0.04, -0.06), (0.06, -0.12)], M.lily, n=6, rx=PI - droop, rz=a, cap_top=False)
        g.box((pts[1][0], pts[1][1], pts[1][2] - 0.1), (0.2, 0.015, 0.05), M.leaf_dead, rz=a, ry=0.7)
    p.params.setdefault('amp', 0.012)
    p.params.setdefault('leaf', '#8a7a5a')
    p.params.setdefault('sound', 'rustle')


def hanging_basket(p, M, drop=1.4, seed=6):
    rng = jitter_rng(seed)
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    for k in range(3):
        a = k * TAU / 3
        g.tube([(0, 0, 0), (math.cos(a) * 0.2, math.sin(a) * 0.2, -drop)], 0.004, M.iron, n=3, caps=False)
    g.lathe((0, 0, -drop - 0.18), [(0.05, 0), (0.18, 0.08), (0.22, 0.18)], M.wicker, n=12, cap_top=False)
    g.blob((0, 0, -drop - 0.08), 0.24, M.leaf_dark, seed=seed, jitter=0.25, s=(1, 1, 0.6))
    for i in range(10):
        a = rng.uniform(0, TAU)
        L = rng.uniform(0.3, 0.6)
        g.tube([(math.cos(a) * 0.18, math.sin(a) * 0.18, -drop - 0.05), (math.cos(a) * 0.28, math.sin(a) * 0.28, -drop - 0.1 - L * 0.5),
                (math.cos(a) * 0.3, math.sin(a) * 0.3, -drop - 0.1 - L)], 0.012, rng.choice(M.leaves), n=3)
    p.params.setdefault('amp', 0.03)
    p.params.setdefault('leaf', '#3e5a2c')
    p.params.setdefault('sound', 'rustle')


def rocking_horse(p, M):
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    for sx in (-1, 1):
        pts = [(sx * 0.2, -0.75 + 1.5 * i / 10, 0.04 + 0.16 * ((i / 10 - 0.5) * 2) ** 2) for i in range(11)]
        g.tube(pts, 0.03, M.toy_red, n=6)
    g.box((0, 0, 0.14), (0.44, 0.06, 0.04), M.walnut)
    for sy in (-1, 1):
        g.box((0, sy * 0.45, 0.1), (0.44, 0.05, 0.04), M.walnut)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.tube([(sx * 0.2, sy * 0.45, 0.1), (sx * 0.12, sy * 0.3, 0.45), (sx * 0.1, sy * 0.25, 0.62)], 0.03, M.porcelain, n=6)
    g.blob((0, 0, 0.72), 0.24, M.porcelain, seed=1, jitter=0.06, s=(0.65, 1.55, 0.75))
    g.tube([(0, -0.28, 0.78), (0, -0.4, 0.98), (0, -0.44, 1.1)], 0.085, M.porcelain, n=8)
    g.box((0, -0.55, 1.08), (0.13, 0.3, 0.14), M.porcelain, bevel=0.05, rx=0.6)
    for sx in (-1, 1):
        g.sphere((sx * 0.065, -0.5, 1.13), 0.018, M.black, n=5)
        g.prism((sx * 0.04, -0.42, 1.2), [(-0.02, 0), (0.02, 0), (0, 0.08)], 0.02, M.porcelain, rx=HALF)
        for k in range(4):
            g.sphere((sx * 0.09, 0.15 - k * 0.12, 0.8 + k * 0.03), 0.025, M.black, n=4)
    g.tube([(0, -0.3, 1.02), (0, -0.2, 0.92), (0, -0.1, 0.9)], 0.03, M.black, n=5)
    g.box((0, 0.0, 0.92), (0.3, 0.35, 0.05), M.velvet_ox, bevel=0.02)
    g.tube([(0, 0.35, 0.8), (0, 0.48, 0.7), (0, 0.52, 0.5)], 0.035, M.black, n=5)
    g.tube([(-0.07, -0.58, 1.05), (-0.18, -0.2, 0.95), (0.18, -0.2, 0.95), (0.07, -0.58, 1.05)], 0.006, M.brass, n=3, caps=False)
    p.body.collide((0, 0, 0.5), (0.5, 1.5, 1.0))
    p.params.setdefault('axis', 'x')
    p.params.setdefault('period', 1.5)
    p.params.setdefault('sound', 'creak')


def cradle(p, M):
    """Wooden rocking cradle, long axis along X; it rocks side to side (about X)."""
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    for sx in (-1, 1):
        pts = [(sx * 0.42, -0.35 + 0.7 * i / 8, 0.03 + 0.08 * ((i / 8 - 0.5) * 2) ** 2) for i in range(9)]
        g.tube(pts, 0.025, M.walnut, n=5)
        g.box((sx * 0.42, 0, 0.12), (0.05, 0.3, 0.14), M.walnut)
    g.box((0, 0, 0.42), (0.9, 0.48, 0.34), M.walnut, bevel=0.02)
    g.box((0, 0, 0.6), (0.82, 0.4, 0.04), M.linen, bevel=0.015)
    g.box((-0.1, 0, 0.62), (0.5, 0.42, 0.04), M.velvet_plum, bevel=0.015)
    g.box((0.42, 0, 0.75), (0.05, 0.5, 0.36), M.walnut, bevel=0.01)
    for k in range(5):
        a = k * PI / 4
        g.tube([(0.42, -0.25 * math.cos(a), 0.6 + 0.3 * math.sin(a)), (0.2, -0.24 * math.cos(a), 0.62 + 0.28 * math.sin(a) * 0.9)], 0.008, M.walnut, n=3)
    g.sheet((0.25, -0.26, 0.92), 0.4, 0.32, M.lace, nx=2, ny=2)
    g.sheet((0.25, 0.26, 0.92), 0.4, 0.32, M.lace, nx=2, ny=2)
    g.sphere((0.28, 0, 0.7), 0.06, M.porcelain, n=10)
    for sx in (-1, 1):
        g.sphere((0.235, sx * 0.022, 0.71), 0.01, M.black, n=4)
    p.body.collide((0, 0, 0.35), (0.95, 0.75, 0.7))
    p.params.setdefault('axis', 'x')
    p.params.setdefault('period', 2.2)
    p.params.setdefault('sound', 'creak')


def mobile(p, M, drop=0.9):
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.cyl((0, 0, -0.4), 0.004, 0.4, M.lace, n=3)
    g.cyl((-0.35, 0, -0.4), 0.006, 0.7, M.brass, n=4, ry=HALF)
    g.cyl((0, -0.3, -0.4), 0.006, 0.6, M.brass, n=4, rx=-HALF)
    hangs = [(-0.35, 0, 0.35), (0.35, 0, 0.5), (0, -0.3, 0.42), (0, 0.3, 0.28)]
    for i, (x, y, L) in enumerate(hangs):
        g.cyl((x, y, -0.4 - L), 0.003, L, M.lace, n=3)
        z = -0.4 - L - 0.05
        if i % 2 == 0:
            g.torus((x, y, z), 0.06, 0.02, M.porcelain if i == 0 else M.brass, n=12, m=4, rx=HALF, arc=PI * 1.3)
        else:
            g.prism((x, y, z - 0.06), [(math.cos(a) * (0.07 if k % 2 == 0 else 0.03), math.sin(a) * (0.07 if k % 2 == 0 else 0.03)) for k, a in enumerate(np.linspace(0, TAU, 11)[:-1] + HALF)], 0.015, M.brass, rx=HALF)
    g.blob((0, 0, -0.62), 0.05, M.toy_blue, seed=2, jitter=0.1, s=(1.6, 0.6, 0.8))
    p.params.setdefault('axis', 'y')
    p.params.setdefault('speed', 0.15)
    p.params.setdefault('sound', 'jingle')


def toy_blocks(p, M, seed=0):
    rng = jitter_rng(seed)
    pv = p.part('pivot')
    g = pv.geo
    cols = [M.toy_red, M.toy_blue, M.porcelain, M.brass, M.velvet_moss]
    z = 0
    for k in range(3):
        s = 0.1
        g.box((rng.uniform(-0.01, 0.01), rng.uniform(-0.01, 0.01), z + s / 2), (s, s, s), cols[(k + seed) % 5], rz=rng.uniform(-0.3, 0.3), bevel=0.008)
        z += s
    for k in range(3):
        a = rng.uniform(0, TAU)
        g.box((math.cos(a) * 0.18, math.sin(a) * 0.18, 0.05), (0.1, 0.1, 0.1), cols[(k + seed + 2) % 5], rz=rng.uniform(0, 1), bevel=0.008)
    p.params.setdefault('sound', 'clatter')


def jack_in_box(p, M):
    b = p.body
    b.box((0, 0, 0.12), (0.24, 0.24, 0.24), M.toy_red, bevel=0.01)
    for sx in (-1, 1):
        b.box((sx * 0.121, 0, 0.12), (0.004, 0.16, 0.16), M.brass)
    b.cyl((0.13, 0, 0.12), 0.01, 0.05, M.brass, n=5, ry=HALF)
    b.box((0.19, 0, 0.12), (0.01, 0.01, 0.06), M.brass)
    # the clown, half-risen on his spring
    coil = [(0.03 * math.cos(t * 3), 0.03 * math.sin(t * 3), 0.2 + t * 0.03) for t in np.linspace(0, 4, 20)]
    b.tube(coil, 0.005, M.steel, n=3, caps=False)
    b.sphere((0, 0, 0.36), 0.06, M.porcelain, n=10)
    b.lathe((0, 0, 0.4), [(0.05, 0), (0.001, 0.12)], M.toy_blue, n=8)
    b.sphere((0, -0.058, 0.36), 0.014, M.toy_red, n=5)
    lid = p.part('pivot', (0, 0.12, 0.24), rx=-1.9)
    lid.geo.box((0, -0.12, 0.012), (0.24, 0.24, 0.024), M.toy_red, bevel=0.006)
    lid.geo.box((0, -0.12, 0.026), (0.16, 0.16, 0.004), M.brass)
    p.params.setdefault('axis', 'x')
    p.params.setdefault('dir', -1)
    p.params.setdefault('closed', -1.9)
    p.params.setdefault('open', 2.0)
    p.params.setdefault('sound', 'squeak')


def music_box(p, M):
    pf.music_box(p, M.walnut, M.brass, M.velvet_ox)


def puppet_theatre(p, M):
    """Toy theatre booth; its little velvet curtains are cloth parts."""
    b = p.body
    w, d, h = 1.4, 0.6, 1.9
    b.box((0, 0, 0.45), (w, d, 0.9), M.toy_red, bevel=0.01)
    for sx in (-1, 1):
        b.box((sx * (w / 2 - 0.08), 0, 1.35), (0.16, d, 0.9), M.toy_red)
    b.box((0, 0, 1.85), (w, d, 0.2), M.toy_red)
    b.prism((0, -d / 2 - 0.01, 1.95), [(-w / 2, 0), (w / 2, 0), (0.15, 0.2), (0, 0.28), (-0.15, 0.2)], 0.03, M.brass, rx=HALF)
    b.box((0, 0.2, 1.35), (w - 0.3, 0.04, 0.9), M.night)
    b.box((0, -d / 2 - 0.01, 0.92), (w - 0.2, 0.04, 0.05), M.brass)
    for k in range(3):
        b.prism((-0.3 + k * 0.3, 0.15, 0.93), [(-0.12, 0), (0.12, 0), (0, 0.3)], 0.02, M.leaf_dark, rx=HALF)
    b.box((0, -d / 2 - 0.02, 1.72), (w - 0.25, 0.04, 0.12), M.velvet_ox)
    for i, sx in enumerate((-1, 1)):
        g = p.geo(f'cloth{i}', (sx * (w / 2 - 0.3), -d / 2 - 0.03, 1.68))
        g.sheet((0, 0, 0), 0.32, 0.72, M.velvet_ox, nx=4, ny=6)
    b.collide((0, 0, h / 2), (w, d, h))
    p.params.setdefault('amp', 0.02)
    p.params.setdefault('sound', 'whoosh')


def tea_party(g, M):
    """A small table laid for dolls, three tiny chairs, two porcelain guests."""
    g.cyl((0, 0, 0.0), 0.04, 0.42, M.walnut, n=8)
    g.cyl((0, 0, 0.42), 0.35, 0.03, M.walnut, n=18)
    g.cyl((0, 0, 0.45), 0.36, 0.006, M.lace, n=18)
    for k in range(3):
        a = k * TAU / 3
        x, y = math.cos(a) * 0.5, math.sin(a) * 0.5
        with g.at((x, y, 0), a + HALF):
            g.box((0, 0, 0.22), (0.24, 0.22, 0.03), M.walnut)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    g.box((sx * 0.1, sy * 0.09, 0.11), (0.025, 0.025, 0.22), M.walnut)
            g.box((0, 0.1, 0.38), (0.24, 0.02, 0.3), M.walnut)
            if k < 2:
                g.lathe((0, 0, 0.24), [(0.09, 0), (0.06, 0.12), (0.04, 0.2)], M.velvet_plum if k else M.linen, n=10)
                g.sphere((0, 0, 0.5), 0.06, M.porcelain, n=10)
                g.blob((0, 0.02, 0.54), 0.06, M.wool, seed=k, jitter=0.15, s=(1, 1, 0.6))
                for sx in (-1, 1):
                    g.sphere((sx * 0.02, -0.055, 0.51), 0.008, M.black, n=4)
        tx, ty = math.cos(a) * 0.2, math.sin(a) * 0.2
        g.lathe((tx, ty, 0.456), [(0.03, 0), (0.04, 0.035), (0.04, 0.04)], M.porcelain, n=10, cap_top=False)
        g.cyl((tx, ty, 0.456), 0.06, 0.004, M.porcelain, n=12)
    g.lathe((0, 0, 0.456), [(0.05, 0), (0.07, 0.05), (0.06, 0.1), (0.03, 0.13), (0.035, 0.14)], M.porcelain, n=12)
    g.collide((0, 0, 0.25), (0.8, 0.8, 0.5))


def wine_bottle(p, M):
    pv = p.part('pivot')
    pv.geo.lathe((0.0, 0, 0.04), [(0.036, 0), (0.04, 0.01), (0.04, 0.18), (0.016, 0.24), (0.014, 0.3), (0.017, 0.31)], M.glass_green, n=10, ry=HALF)
    pv.geo.cyl((0.3, 0, 0.04), 0.012, 0.03, M.wine, n=6, ry=HALF)
    p.params.setdefault('sound', 'clatter')


def teacup(p, M):
    pv = p.part('pivot')
    g = pv.geo
    g.cyl((0, 0, 0), 0.075, 0.008, M.porcelain, n=14)
    g.lathe((0, 0, 0.008), [(0.025, 0), (0.035, 0.01), (0.045, 0.05), (0.048, 0.06)], M.porcelain, n=12, cap_top=False)
    g.cyl((0, 0, 0.05), 0.043, 0.002, M.roast, n=12)
    g.torus((0.052, 0, 0.035), 0.016, 0.005, M.porcelain, n=8, m=3, rx=HALF)
    g.cyl((0.12, 0.04, 0), 0.03, 0.004, M.porcelain, n=8)
    p.params.setdefault('sound', 'clatter')


def bucket(p, M, mop=True):
    pv = p.part('pivot')
    g = pv.geo
    g.lathe((0, 0, 0), [(0.13, 0), (0.15, 0.02), (0.17, 0.3), (0.175, 0.32)], M.steel, n=14, cap_top=False)
    g.cyl((0, 0, 0.22), 0.155, 0.004, M.flag_dark, n=14)
    g.torus((0, 0, 0.36), 0.17, 0.006, M.iron, n=12, m=3, rx=HALF, arc=PI)
    if mop:
        g.tube([(0.02, 0.02, 0.05), (0.2, 0.15, 1.3)], 0.015, M.pine, n=5)
        g.blob((0.04, 0.03, 0.2), 0.08, M.linen, seed=4, jitter=0.3, s=(1, 1, 1.4))
    p.body.collide((0, 0, 0.17), (0.34, 0.34, 0.34))
    p.params.setdefault('sound', 'clatter')


def apron_pegs(p, M, n=3):
    """Peg rail with aprons and a cloak; origin on the wall at the rail."""
    b = p.body
    L = 0.5 * n + 0.2
    b.box((0, -0.02, 0), (L, 0.04, 0.1), M.pine, bevel=0.01)
    mats = [M.linen, M.crepe, M.linen, M.wool]
    for i in range(n):
        x = -L / 2 + 0.35 + i * 0.5
        b.cyl((x, -0.04, 0), 0.015, 0.1, M.pine, n=6, rx=HALF)
        g = p.geo(f'cloth{i}', (x, -0.1, -0.02))
        g.sheet((0, 0, 0), 0.4 if mats[i] is not M.linen else 0.32, 1.1 if mats[i] is M.linen else 1.4, mats[i], nx=4, ny=8)
    p.params.setdefault('amp', 0.02)
    p.params.setdefault('sound', 'whoosh')


def doll_chair(g, M):
    """A porcelain doll sitting in a small rocking chair-less chair (static)."""
    g.box((0, 0, 0.2), (0.3, 0.28, 0.03), M.walnut)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box((sx * 0.12, sy * 0.11, 0.1), (0.025, 0.025, 0.2), M.walnut)
    g.box((0, 0.13, 0.38), (0.3, 0.02, 0.36), M.walnut)
    g.lathe((0, 0, 0.22), [(0.1, 0), (0.07, 0.14), (0.04, 0.22)], M.velvet_plum, n=10)
    g.sphere((0, -0.01, 0.5), 0.07, M.porcelain, n=10)
    g.blob((0, 0.02, 0.54), 0.072, M.roast, seed=1, jitter=0.15, s=(1, 1, 0.7))
    for sx in (-1, 1):
        g.sphere((sx * 0.024, -0.07, 0.51), 0.01, M.black, n=4)


def marble_tex(size=256, base='#d8cfbc', vein='#7a7266', seed=25):
    yy, xx = np.mgrid[0:size, 0:size].astype(float) / size
    n = tex.fbm((size, size), 3, 5, seed)
    v = np.abs(np.sin(np.pi * (3 * xx + 2 * yy + 3.0 * n)))
    veins = np.clip(1 - v * 7, 0, 1) ** 1.5
    n2 = tex.fbm((size, size), 6, 4, seed + 1)
    img = tex.hex_rgb(base) * (0.9 + 0.14 * n2)[..., None]
    img = img * (1 - veins[..., None] * 0.55) + tex.hex_rgb(vein) * veins[..., None] * 0.55
    return np.clip(img, 0, 1)


def swivel_chair(p, M):
    b = p.body
    for i in range(4):
        a = i * TAU / 4 + TAU / 8
        b.tube([(0, 0, 0.14), (math.cos(a) * 0.18, math.sin(a) * 0.18, 0.08), (math.cos(a) * 0.27, math.sin(a) * 0.27, 0.03)], 0.02, M.walnut, n=5)
        b.sphere((math.cos(a) * 0.27, math.sin(a) * 0.27, 0.03), 0.03, M.brass, n=6)
    b.cyl((0, 0, 0.1), 0.03, 0.32, M.iron, n=8)
    b.collide((0, 0, 0.3), (0.55, 0.55, 0.6))
    pv = p.part('pivot', (0, 0, 0.42))
    g = pv.geo
    g.cyl((0, 0, 0), 0.26, 0.06, M.walnut, n=16)
    g.cyl((0, 0, 0.06), 0.24, 0.05, M.roast, n=16)
    g.torus((0, 0.0, 0.42), 0.25, 0.03, M.walnut, n=14, m=5, arc=PI)
    for k in range(5):
        a = 0.35 + k * (PI - 0.7) / 4
        g.cyl((math.cos(a) * 0.24, math.sin(a) * 0.24, 0.06), 0.012, 0.36, M.walnut, n=5)
    g.box((0, 0.2, 0.3), (0.34, 0.05, 0.18), M.roast, bevel=0.02)
    p.params.setdefault('axis', 'y')
    p.params.setdefault('speed', 0.0)
    p.params.setdefault('wobble', 0.015)
    p.params.setdefault('sound', 'squeak')


def organ_prop(p, M):
    organ(p.body, M)
    p.params.setdefault('instrument', 'organ')
    p.params.setdefault('sound', 'organ')


def cello(g, M):
    with g.at((0, 0, 0), 0, 0.0, 0.32):
        g.cyl((0, 0, 0), 0.006, 0.12, M.steel, n=4)
        g.sphere((0, 0, 0.36), 0.22, M.mahogany, n=14, s=(1, 0.42, 1.0))
        g.sphere((0, 0, 0.7), 0.18, M.mahogany, n=14, s=(1, 0.42, 1.0))
        g.box((0, 0, 0.53), (0.26, 0.16, 0.14), M.mahogany)
        g.box((0, -0.06, 1.0), (0.05, 0.04, 0.62), M.black)
        g.torus((0, -0.04, 1.34), 0.035, 0.014, M.mahogany, n=8, m=4, ry=HALF)
        for k in range(4):
            g.box((-0.022 + k * 0.015, -0.1, 0.72), (0.003, 0.003, 0.95), M.paper)
        for sx in (-1, 1):
            g.box((sx * 0.07, -0.095, 0.5), (0.012, 0.004, 0.12), M.black)
        g.box((0, -0.095, 0.38), (0.12, 0.012, 0.025), M.black)


def harp(g, M):
    g.box((0, 0, 0.06), (0.36, 0.6, 0.12), M.walnut, bevel=0.015)
    g.lathe((0, -0.24, 0.12), [(0.05, 0), (0.04, 0.1), (0.035, 1.5), (0.06, 1.56), (0.04, 1.62), (0.06, 1.7)], M.brass, n=10)
    g.tube([(0, -0.24, 1.72), (0, -0.05, 1.66), (0, 0.15, 1.5), (0, 0.35, 1.48), (0, 0.48, 1.52)], 0.04, M.walnut, n=6)
    g.tube([(0, -0.16, 0.14), (0, 0.48, 1.5)], 0.075, M.walnut, n=6)
    for k in range(14):
        t = (k + 1) / 15
        y = -0.16 + 0.64 * t
        zb = 0.14 + (1.5 - 0.14) * t
        zt = 1.66 - 0.18 * t if t < 0.5 else 1.5
        g.cyl((0, y - 0.04, zb + 0.05), 0.003, max(0.05, zt - zb - 0.08), M.paper if k % 7 else M.toy_red, n=3)
    g.collide((0, 0, 0.85), (0.4, 0.7, 1.7))


def copper_boiler(g, M):
    g.box((0, 0, 0.4), (0.9, 0.9, 0.8), M.brick, bevel=0.01, col=True)
    g.box((0, -0.46, 0.25), (0.3, 0.02, 0.25), M.iron)
    g.lathe((0, 0, 0.8), [(0.36, 0), (0.4, 0.1), (0.4, 0.2), (0.44, 0.22)], M.copper, n=16, cap_top=False)
    g.cyl((0, 0, 0.95), 0.4, 0.02, M.pine, n=16)
    g.sphere((0, 0, 0.98), 0.04, M.pine, n=6)
    g.cyl((0.3, 0.3, 0.8), 0.07, 3.4, M.iron, n=8)
    g.tube([(-0.2, 0.0, 0.97), (0.3, -0.1, 1.35)], 0.015, M.pine, n=4)


def washtub(g, M):
    g.lathe((0, 0, 0), [(0.3, 0), (0.36, 0.05), (0.4, 0.38), (0.41, 0.4)], M.pine, n=14, cap_top=False)
    for z in (0.08, 0.3):
        g.torus((0, 0, z), 0.34 + z * 0.15, 0.012, M.iron, n=14, m=3)
    g.cyl((0, 0, 0.28), 0.38, 0.004, M.coal, n=14)
    with g.at((0.32, 0.0, 0.0), 0, 0.0, -0.25):
        g.box((0, 0, 0.35), (0.04, 0.32, 0.7), M.pine)
        for k in range(10):
            g.box((-0.025, 0, 0.12 + k * 0.045), (0.015, 0.26, 0.012), M.steel)
    g.collide((0, 0, 0.2), (0.8, 0.8, 0.4))


def statue(g, M):
    """Marble maiden with an urn on a plinth (conservatory corner)."""
    g.box((0, 0, 0.35), (0.55, 0.55, 0.7), M.marble, bevel=0.02, col=True)
    g.box((0, 0, 0.72), (0.62, 0.62, 0.05), M.marble, bevel=0.01)
    g.lathe((0, 0, 0.75), [(0.2, 0), (0.18, 0.3), (0.13, 0.7), (0.12, 0.9), (0.14, 1.05), (0.08, 1.15), (0.05, 1.2)], M.marble, n=12)
    g.sphere((0, -0.02, 2.04), 0.1, M.marble, n=10, s=(0.9, 0.95, 1.1))
    g.blob((0, 0.03, 2.08), 0.1, M.marble, seed=3, jitter=0.1, s=(1, 1, 0.8))
    g.tube([(-0.12, 0, 1.8), (-0.2, -0.08, 1.55), (-0.1, -0.16, 1.4)], 0.035, M.marble, n=6)
    g.tube([(0.12, 0, 1.8), (0.22, -0.02, 1.95), (0.2, -0.04, 2.15)], 0.035, M.marble, n=6)
    g.lathe((0.2, -0.04, 2.15), [(0.04, 0), (0.08, 0.06), (0.06, 0.14), (0.07, 0.17)], M.marble, n=10)
    g.collide((0, 0, 1.3), (0.5, 0.5, 2.6))


def range_fire(p, M, light=None):
    for x, s in ((-0.08, 0.9), (0.02, 1.2), (0.1, 0.8)):
        p.flame((x, 0.0, -0.12), size=s)
    if light:
        p.light((0, -0.4, 0.3), light[0], light[1], light[2], part='flame0')
    p.params.setdefault('sound', 'whoomp')


def tipped_chair(g, M, seat):
    """A dining chair knocked over onto its back."""
    with g.at((0, 0.28, 0.25), 0, -HALF + 0.12):
        dining_chair_geo(g, M, seat, col=False)


def leaf_blade(g, a, b, c, mat, t=0.006):
    """A thin triangular leaf between points a, b (along the stem) and c (the leaf's edge)."""
    va = [tuple(a), tuple(b), tuple(c)]
    up = [(x, y, z + t) for x, y, z in va]
    verts = va + up
    faces = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    g.add((verts, faces, [False] * 5), mat)


def altar(g, M):
    """Relic altar: a marble pedestal carrying a brass offering dish. Every altar is identical."""
    g.box((0, 0, 0.08), (0.9, 0.9, 0.16), M.marble, col=True)
    g.box((0, 0, 0.2), (0.7, 0.7, 0.08), M.marble_dark)
    g.lathe((0, 0, 0.24), [(0.22, 0), (0.15, 0.08), (0.12, 0.5), (0.16, 0.6), (0.28, 0.68)], M.marble, n=8)
    g.collide((0, 0, 0.5), (0.5, 0.5, 1.0))
    g.cyl((0, 0, 0.92), 0.3, 0.06, M.marble, n=12)
    g.lathe((0, 0, 0.98), [(0.12, 0), (0.26, 0.04), (0.3, 0.05)], M.brass, n=12, cap_top=False)
    g.torus((0, 0, 1.03), 0.24, 0.02, M.altar_glow, n=16, m=4)
    for i in range(4):
        a = i * TAU / 4 + TAU / 8
        g.box((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.32), (0.06, 0.06, 0.16), M.brass, rz=a)
    return 1.03


# ======================================================================= more furniture

def billiard_table(g, M, L=3.6, W=1.9, h=0.82):
    for sx in (-1, 0, 1):
        for sy in (-1, 1):
            turned_leg(g, (sx * (L / 2 - 0.2), sy * (W / 2 - 0.2), 0), h - 0.2, 0.08, M.mahogany)
    g.box((0, 0, h - 0.12), (L, W, 0.24), M.mahogany)
    g.box((0, 0, h - 0.005), (L - 0.24, W - 0.24, 0.01), M.baize)
    for sy in (-1, 1):
        g.box((0, sy * (W / 2 - 0.06), h + 0.03), (L, 0.12, 0.06), M.mahogany)
        g.box((0, sy * (W / 2 - 0.135), h + 0.02), (L - 0.3, 0.03, 0.04), M.baize)
    for sx in (-1, 1):
        g.box((sx * (L / 2 - 0.06), 0, h + 0.03), (0.12, W - 0.24, 0.06), M.mahogany)
        g.box((sx * (L / 2 - 0.135), 0, h + 0.02), (0.03, W - 0.3, 0.04), M.baize)
    for sx in (-1, 0, 1):
        for sy in (-1, 1):
            g.cyl((sx * (L / 2 - 0.1), sy * (W / 2 - 0.1), h - 0.08), 0.055, 0.13, M.black, n=8)
    for k in range(4):
        g.sphere((-L / 2 + 0.6 + k * 0.4, -W / 2 - 0.004, h - 0.12), 0.025, M.brass, n=5)
    g.collide((0, 0, h / 2), (L, W, h + 0.06))


def billiard_balls(p, M):
    pv = p.part('pivot')
    g = pv.geo
    cols = [M.toy_red, M.brass, M.black, M.toy_blue, M.toy_red, M.brass, M.velvet_plum]
    k = 0
    for row in range(3):
        for i in range(row + 1):
            g.sphere((row * 0.046, (i - row / 2) * 0.054, 0.027), 0.027, cols[k % len(cols)], n=7)
            k += 1
    g.sphere((-0.9, 0.12, 0.027), 0.027, M.porcelain, n=7)
    g.tube([(-1.0, 0.16, 0.035), (-2.3, 0.6, 0.06)], 0.012, M.pine, n=4)
    p.params.setdefault('sound', 'clatter')


def billiard_lamp(p, M, L=2.2, drop=1.25, light=None):
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    for sx in (-1, 1):
        g.tube([(sx * L * 0.3, 0, 0), (sx * L * 0.4, 0, -drop)], 0.008, M.brass, n=3)
    g.box((0, 0, -drop), (L, 0.06, 0.06), M.mahogany)
    for k in range(3):
        x = (k - 1) * L * 0.36
        g.lathe((x, 0, -drop - 0.24), [(0.22, 0), (0.18, 0.06), (0.08, 0.18), (0.03, 0.22)], M.glass_dark, n=10, cap_bottom=False)
        b = p.geo(f'bulb{k}', (x, 0, -drop - 0.2), parent='pivot')
        b.sphere((0, 0, 0), 0.05, M.glow, n=8)
    if light:
        p.light((0, 0, -drop - 0.4), light[0], light[1], light[2], part='pivot')
    p.params.setdefault('amp', 0.02)
    p.params.setdefault('period', 2.4)
    p.params.setdefault('sound', 'creak')


def cue_rack(g, M):
    """Wall rack of cues and a scoreboard; origin on the wall at floor level, facing -Y."""
    g.box((0, -0.04, 0.9), (0.9, 0.06, 0.08), M.mahogany)
    g.box((0, -0.04, 1.75), (0.9, 0.06, 0.08), M.mahogany)
    for k in range(6):
        x = -0.35 + k * 0.14
        g.cyl((x, -0.07, 0.08), 0.012, 1.48, M.pine if k % 3 else M.walnut, n=5, r2=0.007)
        g.cyl((x, -0.07, 0.0), 0.016, 0.08, M.black, n=5)
    g.box((1.2, -0.03, 1.6), (0.9, 0.04, 0.5), M.mahogany)
    g.box((1.2, -0.055, 1.6), (0.8, 0.01, 0.4), M.black)
    for r in range(2):
        g.box((1.2, -0.06, 1.5 + r * 0.2), (0.78, 0.008, 0.006), M.brass)
        for k in range(7):
            g.sphere((0.88 + k * 0.05 + (0.3 if k > 3 else 0), -0.07, 1.5 + r * 0.2), 0.014, M.porcelain, n=5)


def chesterfield(g, M, fabric, w=2.0):
    d = 0.9
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.cyl((sx * (w / 2 - 0.1), sy * (d / 2 - 0.1), 0), 0.04, 0.12, M.walnut_dark, n=6)
    g.box((0, 0, 0.3), (w, d, 0.36), fabric)
    g.box((0, -0.05, 0.52), (w - 0.4, d - 0.25, 0.1), fabric)
    g.box((0, d / 2 - 0.12, 0.6), (w, 0.24, 0.62), fabric)
    for sx in (-1, 1):
        g.box((sx * (w / 2 - 0.12), -0.02, 0.6), (0.24, d - 0.04, 0.62), fabric)
        g.cyl((sx * (w / 2 - 0.12), d / 2, 0.86), 0.13, d, fabric, n=8, rx=HALF)
    g.cyl((-w / 2, d / 2 - 0.12, 0.86), 0.13, w, fabric, n=8, ry=HALF)
    for i in range(7):
        for r in range(2):
            g.sphere((-w * 0.38 + i * w * 0.127, d / 2 - 0.245, 0.68 + r * 0.14), 0.014, M.black, n=4)
    g.collide((0, 0, 0.45), (w, d, 0.9))


def chaise(g, M, fabric, L=1.8):
    for sx in (-1, 1):
        for sy in (-1, 1):
            turned_leg(g, (sx * (L / 2 - 0.1), sy * 0.26, 0), 0.22, 0.03, M.walnut)
    g.box((0, 0, 0.32), (L, 0.66, 0.2), fabric)
    g.box((0.1, 0, 0.45), (L - 0.4, 0.58, 0.08), fabric)
    with g.at((-L / 2 + 0.2, 0, 0.4), 0, 0, -0.75):
        g.box((0, 0, 0.32), (0.18, 0.64, 0.7), fabric)
    g.cyl((-L / 2 + 0.15, -0.33, 0.62), 0.09, 0.66, fabric, n=8, rx=-HALF)
    g.tube([(-L / 2 + 0.05, 0.3, 0.9), (-L / 2 + 0.4, 0.31, 0.62), (0.2, 0.31, 0.5)], 0.03, M.walnut, n=5)
    g.box((0.6, 0.0, 0.56), (0.3, 0.3, 0.12), M.velvet_ox, rz=0.4)
    g.collide((0, 0, 0.35), (L, 0.66, 0.7))


def etagere(g, M, w=0.9, d=0.4, h=1.8, seed=0):
    rng = jitter_rng(seed)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.cyl((sx * (w / 2 - 0.03), sy * (d / 2 - 0.03), 0), 0.018, h, M.walnut, n=5)
            g.sphere((sx * (w / 2 - 0.03), sy * (d / 2 - 0.03), h + 0.02), 0.03, M.walnut, n=5)
    for k in range(4):
        z = 0.15 + k * (h - 0.25) / 3
        g.box((0, 0, z), (w, d, 0.025), M.walnut)
        x = -w / 2 + 0.12
        while x < w / 2 - 0.1:
            r = rng.random()
            if r < 0.4:
                g.lathe((x, 0, z + 0.012), [(0.04, 0), (0.06, 0.06), (0.04, 0.16), (0.025, 0.2), (0.035, 0.22)], rng.choice([M.porcelain, M.toy_blue, M.brass]), n=8)
                x += 0.16
            elif r < 0.6:
                g.box((x + 0.05, 0, z + 0.05), (0.12, 0.09, 0.08), rng.choice([M.mahogany, M.brass]))
                x += 0.18
            elif r < 0.75:
                g.sphere((x + 0.04, 0, z + 0.05), 0.05, M.glass_dark, n=8)
                x += 0.13
            else:
                x += 0.12
    g.collide((0, 0, h / 2), (w, d, h))


def folding_screen(g, M, fabric, panels=3, pw=0.55, h=1.8):
    """Zig-zag folding screen; origin at the middle panel's base."""
    ang = 0.5
    x = 0.0
    pos = []
    for i in range(panels):
        a = ang * (1 if i % 2 else -1)
        pos.append((i, a))
    cx = -(panels - 1) / 2 * pw * math.cos(ang)
    for i, a in pos:
        px = cx + i * pw * math.cos(ang)
        py = (0.08 if i % 2 else -0.08)
        with g.at((px, py, 0), a):
            frame_rect(g, (0, 0, h / 2 + 0.06), pw, h, 0.04, 0.035, M.walnut)
            g.box((0, 0, h / 2 + 0.06), (pw - 0.08, 0.012, h - 0.08), fabric)
            for sx in (-1, 1):
                g.cyl((sx * (pw / 2 - 0.02), 0, 0), 0.015, 0.08, M.walnut, n=5)
    g.collide((0, 0, h / 2), (panels * pw * math.cos(ang), 0.45, h))


def trunk(g, M, w=0.9, d=0.5, h=0.45, mat=None):
    mat = mat or M.roast
    g.box((0, 0, h / 2), (w, d, h), mat)
    g.box((0, 0, h + 0.03), (w + 0.01, d + 0.01, 0.06), mat)
    for sx in (-1, 1):
        g.box((sx * w * 0.3, 0, h / 2 + 0.02), (0.05, d + 0.012, h + 0.08), M.walnut_dark)
        for sy in (-1, 1):
            g.box((sx * (w / 2 - 0.02), sy * (d / 2 - 0.02), h / 2), (0.05, 0.05, h + 0.06), M.brass)
    g.box((0, -d / 2 - 0.01, h - 0.02), (0.08, 0.02, 0.1), M.brass)
    g.collide((0, 0, h / 2 + 0.03), (w, d, h + 0.06))


def hat_stand(g, M):
    for i in range(3):
        a = i * TAU / 3
        g.tube([(0, 0, 0.3), (math.cos(a) * 0.25, math.sin(a) * 0.25, 0.02)], 0.02, M.walnut, n=4)
    g.cyl((0, 0, 0.2), 0.03, 1.7, M.walnut, n=6)
    for i in range(4):
        a = i * TAU / 4
        g.tube([(0, 0, 1.6), (math.cos(a) * 0.15, math.sin(a) * 0.15, 1.72)], 0.012, M.brass, n=4)
    g.cyl((0.13, 0, 1.72), 0.1, 0.13, M.black, n=10)
    g.cyl((0.13, 0, 1.72), 0.16, 0.01, M.black, n=12)
    g.box((-0.1, 0.02, 1.25), (0.08, 0.36, 0.7), M.wool, ry=0.1)
    g.collide((0, 0, 0.9), (0.4, 0.4, 1.8))


def round_sofa(g, M, fabric, r=1.0):
    """Gallery borne: circular buttoned ottoman around a central column carrying a jardiniere."""
    g.cyl((0, 0, 0), r, 0.12, M.walnut_dark, n=16)
    g.cyl((0, 0, 0.12), r - 0.02, 0.3, fabric, n=16)
    g.cyl((0, 0, 0.42), r - 0.08, 0.06, fabric, n=16, r2=r - 0.2)
    g.cyl((0, 0, 0.42), 0.42, 0.55, fabric, n=12, r2=0.3)
    g.cyl((0, 0, 0.97), 0.3, 0.06, M.walnut, n=12)
    for i in range(8):
        a = i * TAU / 8
        g.sphere((math.cos(a) * 0.36, math.sin(a) * 0.36, 0.7), 0.016, M.brass, n=4)
    g.lathe((0, 0, 1.03), [(0.1, 0), (0.22, 0.1), (0.26, 0.28), (0.22, 0.34)], M.porcelain, n=12)
    g.collide((0, 0, 0.5), (r * 1.6, r * 1.6, 1.0))


def vase_stand(g, M, h=0.75):
    g.lathe((0, 0, 0), [(0.18, 0), (0.14, 0.05), (0.06, 0.12), (0.05, h - 0.1), (0.16, h - 0.04), (0.17, h)], M.mahogany, n=8)
    g.lathe((0, 0, h), [(0.1, 0), (0.2, 0.15), (0.24, 0.35), (0.16, 0.6), (0.09, 0.72), (0.12, 0.78)], M.porcelain, n=12)
    for z in (0.28, 0.5):
        g.torus((0, 0, h + z), 0.23 - abs(z - 0.35) * 0.3, 0.02, M.toy_blue, n=12, m=3)
    g.collide((0, 0, (h + 0.78) / 2), (0.45, 0.45, h + 0.78))


def toy_train(g, M):
    g.box((0, 0, 0.08), (0.3, 0.14, 0.1), M.toy_red)
    g.cyl((0.02, 0, 0.12), 0.055, 0.2, M.black, n=8, ry=HALF)
    g.box((-0.1, 0, 0.18), (0.12, 0.14, 0.12), M.toy_red)
    g.cyl((0.16, 0, 0.12), 0.02, 0.1, M.black, n=6)
    for k, x in enumerate((-0.35, -0.65)):
        g.box((x, 0, 0.08), (0.26, 0.13, 0.08), M.toy_blue if k == 0 else M.velvet_moss)
        for sx in (-1, 1):
            for sy in (-1, 1):
                g.cyl((x + sx * 0.08, sy * 0.075, 0.035), 0.03, 0.02, M.black, n=6, rx=HALF)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.cyl((sx * 0.1, sy * 0.075, 0.04), 0.04, 0.02, M.black, n=6, rx=HALF)


def pram(g, M):
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.torus((sx * 0.22, sy * 0.2, 0.12), 0.11, 0.012, M.iron, n=10, m=3, rx=HALF, rz=0)
        g.tube([(sx * 0.22, -0.2, 0.12), (sx * 0.1, 0, 0.3), (sx * 0.22, 0.2, 0.12)], 0.01, M.iron, n=3)
    g.box((0, 0, 0.45), (0.65, 0.34, 0.26), M.velvet_plum)
    g.lathe((0.2, 0, 0.56), [(0.17, 0), (0.17, 0.05), (0.001, 0.18)], M.velvet_plum, n=10, rx=0, ry=-HALF)
    g.tube([(-0.32, 0, 0.55), (-0.5, 0, 0.85), (-0.55, 0, 0.88)], 0.012, M.iron, n=3)
    g.sphere((0.05, 0, 0.62), 0.07, M.porcelain, n=8)
    g.collide((0, 0, 0.4), (0.7, 0.45, 0.8))


def iron_bench(g, M, w=1.5):
    for sx in (-1, 0, 1):
        g.tube([(sx * (w / 2 - 0.05), -0.22, 0), (sx * (w / 2 - 0.05), -0.2, 0.42), (sx * (w / 2 - 0.05), 0.2, 0.42), (sx * (w / 2 - 0.05), 0.24, 0.9)], 0.02, M.iron, n=4)
    for k in range(4):
        g.box((0, -0.18 + k * 0.11, 0.44), (w, 0.07, 0.025), M.iron)
    for k in range(5):
        g.box((0, 0.22, 0.52 + k * 0.08), (w, 0.012, 0.03), M.iron, rx=-0.1)
    g.torus((0, 0.23, 0.72), 0.12, 0.012, M.iron, n=10, m=3, rx=HALF)
    g.collide((0, 0, 0.25), (w, 0.5, 0.5))


def potted_plant(g, M, seed=0, r=0.45, pot=0.28):
    rng = jitter_rng(seed)
    g.lathe((0, 0, 0), [(pot * 0.7, 0), (pot, pot * 1.1), (pot * 1.08, pot * 1.25), (pot * 0.95, pot * 1.3)], M.terracotta, n=10)
    for i in range(3):
        a = rng.uniform(0, TAU)
        g.blob((math.cos(a) * r * 0.25, math.sin(a) * r * 0.25, pot * 1.3 + r * 0.55 + i * 0.12), r * rng.uniform(0.55, 0.8), rng.choice(M.leaves), seed=seed * 5 + i, jitter=0.25, s=(1, 1, 0.75))
    g.collide((0, 0, pot * 0.65), (pot * 2, pot * 2, pot * 1.3))


def potting_bench(g, M, w=1.8):
    pf.table(g, w, 0.6, 0.85, M.pine)
    g.box((0, 0.27, 1.05), (w, 0.04, 0.4), M.pine)
    for k in range(5):
        x = -w / 2 + 0.2 + k * 0.35
        g.lathe((x, -0.05, 0.85), [(0.05, 0), (0.08, 0.12), (0.085, 0.13)], M.terracotta, n=8, cap_top=False)
    g.lathe((0.5, 0.0, 0.0), [(0.12, 0), (0.15, 0.22), (0.16, 0.24)], M.terracotta, n=8)
    g.blob((-0.5, 0.0, 0.95), 0.12, M.coal, seed=3, jitter=0.3, s=(1.5, 1, 0.5))


def harpsichord_sheet(g, M):
    """A statue under a dust sheet."""
    g.lathe((0, 0, 0), [(0.35, 0), (0.33, 0.3), (0.26, 0.9), (0.2, 1.3), (0.22, 1.45), (0.16, 1.6), (0.001, 1.75)], M.linen, n=9, smooth=False)
    g.collide((0, 0, 0.8), (0.6, 0.6, 1.6))


def cold_fireplace(p, M):
    """Dead grate: ash and a half-burnt log. Still a flame prop: a ghost can make it flare."""
    b = p.body
    b.box((0, 0.0, 0.03), (0.6, 0.26, 0.04), M.coal)
    b.cyl((-0.25, -0.02, 0.1), 0.05, 0.5, M.walnut_dark, n=6, ry=HALF, rz=0.2)
    p.flame((0.05, 0.0, 0.08), size=0.6)
    p.params.setdefault('sound', 'whoomp')


def painting_static(g, M, art):
    """Non-interactive framed painting drawn in atlas space (instance it with an offset)."""
    i, j, span = ART[art]
    cw, ch = ATLAS_CW * span, ATLAS_CH
    cx, cz = (i + span / 2) * ATLAS_CW, (j + 0.5) * ATLAS_CH
    fw = 0.11
    W, H = cw + 2 * fw, ch + 2 * fw
    frame_rect(g, (cx, -0.045, cz), W, H, fw, 0.06, M.brass, bevel=0.014)
    frame_rect(g, (cx, -0.055, cz), W - fw * 1.4, H - fw * 1.4, fw * 0.35, 0.05, M.walnut_dark)
    g.box((cx, -0.015, cz), (W - 0.04, 0.02, H - 0.04), M.walnut_dark)
    g.box((cx, -0.05, cz), (cw, 0.008, ch), M.portraits)
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.sphere((cx + sx * (W / 2 - fw / 2), -0.08, cz + sz * (H / 2 - fw / 2)), fw * 0.45, M.brass, n=6, s=(1, 0.5, 1))
    top = cz + H / 2
    g.tube([(cx - W * 0.3, -0.008, top - 0.05), (cx, -0.008, top + 0.1), (cx + W * 0.3, -0.008, top - 0.05)], 0.003, M.brass, n=3, caps=False)


def wardrobe_static(g, M, w=1.2, d=0.55, h=2.0, wood=None):
    wood = wood or M.walnut
    g.box((0, 0, h / 2), (w, d, h), wood, col=True)
    g.box((0, 0, h + 0.04), (w + 0.08, d + 0.06, 0.08), wood)
    g.box((0, 0, 0.05), (w + 0.04, d + 0.04, 0.1), M.walnut_dark)
    for sx in (-1, 1):
        g.box((sx * w / 4, -d / 2 - 0.01, h / 2 + 0.05), (w / 2 - 0.04, 0.02, h - 0.2), wood)
        g.box((sx * w / 4, -d / 2 - 0.022, h * 0.62), (w / 2 - 0.2, 0.01, h * 0.42), M.walnut_dark)
        g.box((sx * w / 4, -d / 2 - 0.022, h * 0.22), (w / 2 - 0.2, 0.01, h * 0.22), M.walnut_dark)
        g.sphere((sx * 0.06, -d / 2 - 0.035, h * 0.5), 0.02, M.brass, n=6)


def drapes_static(g, M, w, h, fabric, rod=None):
    """Non-interactive tied-back drapes (pleats faked with zig-zag boxes); origin at rod centre."""
    rod = rod or M.brass
    g.cyl((-w / 2 - 0.2, -0.14, 0), 0.022, w + 0.4, rod, n=6, ry=HALF)
    g.box((0, -0.2, 0.1), (w + 0.5, 0.04, 0.36), fabric)
    for sx in (-1, 1):
        for k in range(4):
            x = sx * (w / 2 - 0.05 + k * 0.08)
            g.box((x, -0.16 - 0.03 * (k % 2), -h / 2), (0.1, 0.03, h), fabric, rz=0.35 * (1 if k % 2 else -1))
        g.torus((sx * (w / 2 + 0.06), -0.2, -h * 0.58), 0.12, 0.016, M.brass, n=10, m=3, rx=HALF)


def kitchen_rack(g, M, L=2.4, h=1.9, d=0.5, seed=0):
    """Free-standing double-sided pine rack of crocks, jars and bowls (runs along X)."""
    rng = jitter_rng(seed)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box((sx * (L / 2 - 0.03), sy * (d / 2 - 0.03), h / 2), (0.05, 0.05, h), M.pine)
    for k in range(4):
        z = 0.12 + k * (h - 0.2) / 3
        g.box((0, 0, z), (L, d, 0.03), M.pine)
        if k == 3:
            continue
        x = -L / 2 + 0.15
        while x < L / 2 - 0.15:
            r = rng.random()
            y = rng.choice((-0.12, 0.12))
            if r < 0.35:
                rr = rng.uniform(0.08, 0.12)
                g.lathe((x + rr, y, z + 0.015), [(rr * 0.8, 0), (rr, rr * 0.8), (rr * 0.9, rr * 2.0), (rr * 0.6, rr * 2.3)], rng.choice([M.terracotta, M.porcelain, M.wicker]), n=8)
                x += rr * 2 + 0.06
            elif r < 0.6:
                jar(g, M, (x + 0.06, y, z + 0.015), rng.uniform(0.18, 0.26), 0.06, M.glass_dark, M.linen)
                x += 0.16
            elif r < 0.75:
                g.lathe((x + 0.14, y, z + 0.015), [(0.07, 0), (0.15, 0.07), (0.16, 0.08)], M.porcelain, n=10, cap_top=False)
                x += 0.32
            else:
                x += rng.uniform(0.1, 0.25)
    g.collide((0, 0, h / 2), (L, d, h))


def cat(g, M):
    """A black cat asleep in a curl."""
    g.sphere((0, 0, 0.09), 0.17, M.black, n=10, s=(1.2, 1.0, 0.55))
    g.sphere((0.15, -0.08, 0.13), 0.075, M.black, n=8)
    for sx in (-1, 1):
        g.prism((0.15 + sx * 0.035, -0.08, 0.18), [(-0.02, 0), (0.02, 0), (0, 0.05)], 0.015, M.black, rx=HALF, rz=0.4)
    g.tube([(-0.17, 0.02, 0.05), (-0.12, -0.15, 0.04), (0.05, -0.2, 0.04), (0.12, -0.16, 0.05)], 0.025, M.black, n=5)


def flour_bin(g, M):
    g.box((0, 0, 0.4), (0.7, 0.5, 0.8), M.pine, col=True)
    g.box((0, 0.05, 0.82), (0.72, 0.42, 0.04), M.pine, rx=-0.15)
    g.box((0, -0.26, 0.55), (0.4, 0.01, 0.12), M.paper)
    g.cyl((0.1, -0.05, 0.84), 0.06, 0.04, M.porcelain, n=8)
