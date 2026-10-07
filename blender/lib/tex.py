"""Tileable procedural textures generated with numpy.

Every generator returns an (H, W, 3) float array of sRGB values in [0, 1] whose
edges wrap, so it can be repeated across walls and floors without seams.
"""
import numpy as np


def hex_rgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def _rng(seed):
    return np.random.default_rng(seed)


def value_noise(size, cells, seed=0):
    """Periodic smooth value noise in [0,1]. size: (h, w); cells: lattice cells across."""
    h, w = size
    cy, cx = (cells, cells) if np.isscalar(cells) else cells
    grid = _rng(seed).random((cy, cx))
    ys = np.arange(h) / h * cy
    xs = np.arange(w) / w * cx
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    fy = ys - y0
    fx = xs - x0
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    y1 = (y0 + 1) % cy
    x1 = (x0 + 1) % cx
    y0 %= cy
    x0 %= cx
    a = grid[np.ix_(y0, x0)]
    b = grid[np.ix_(y0, x1)]
    c = grid[np.ix_(y1, x0)]
    d = grid[np.ix_(y1, x1)]
    fx = fx[None, :]
    fy = fy[:, None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(size, base_cells=4, octaves=4, seed=0, gain=0.5):
    total = np.zeros(size)
    amp = 1.0
    norm = 0.0
    for o in range(octaves):
        cells = base_cells * (2 ** o) if np.isscalar(base_cells) else tuple(c * (2 ** o) for c in base_cells)
        total += amp * value_noise(size, cells, seed + o * 101)
        norm += amp
        amp *= gain
    return total / norm


def _mix(c0, c1, t):
    t = np.clip(t, 0, 1)[..., None]
    return c0 * (1 - t) + c1 * t


def colorize(field, c0, c1):
    return _mix(hex_rgb(c0), hex_rgb(c1), field)


def wood_planks(size=512, base='#5a3a24', dark='#3a2416', light='#7a5236', planks=6, seed=1, plank_len=2):
    """Floorboards running along U, with staggered joints and grain."""
    h = w = size
    rng = _rng(seed)
    y = np.arange(h)[:, None] / h * planks
    x = np.arange(w)[None, :] / w
    row = np.floor(y).astype(int) % planks
    fy = y - np.floor(y)
    offsets = rng.random(planks)
    tints = rng.uniform(-0.12, 0.12, planks)
    grain = fbm((h, w), (planks * 2, 3), 4, seed + 5)
    streak = value_noise((h, w), (planks * 16, 2), seed + 9)
    t = 0.5 + tints[row] + (grain - 0.5) * 0.7 + (streak - 0.5) * 0.5
    img = _mix(hex_rgb(dark), hex_rgb(light), t)
    img = _mix(img, hex_rgb(base), np.full((h, w), 0.35))
    seam = (fy < 0.035) | (fy > 0.965)
    jx = (x * plank_len + offsets[row]) % 1.0
    joint = (jx < 0.006) | (jx > 0.994)
    edge = seam | joint
    img[edge] *= 0.45
    return np.clip(img, 0, 1)


def wallpaper(size=512, bg='#4a1f2a', fg='#6b2e3a', stripe='#3a161f', seed=2, motifs=3):
    """Victorian damask-ish wallpaper: vertical stripes with a repeating lozenge motif."""
    h = w = size
    y = np.arange(h)[:, None] / h
    x = np.arange(w)[None, :] / w
    img = np.broadcast_to(hex_rgb(bg), (h, w, 3)).copy()
    sx = (x * motifs) % 1.0
    stripes = (np.abs(sx - 0.5) > 0.46)
    img[np.broadcast_to(stripes, (h, w))] = hex_rgb(stripe)
    # lozenge + inner flourish per cell
    my = (y * motifs * 1.5) % 1.0
    row = np.floor(y * motifs * 1.5).astype(int)
    shift = (row % 2) * 0.5
    mx = (x * motifs + shift) % 1.0
    dx = np.abs(mx - 0.5)
    dy = np.abs(my - 0.5)
    loz = (dx * 1.6 + dy) < 0.32
    inner = (dx * 1.6 + dy) < 0.2
    petals = ((dx - 0.12) ** 2 + (dy - 0.0) ** 2 < 0.004) | ((dx) ** 2 + (dy - 0.2) ** 2 < 0.003)
    motif = (loz & ~inner) | petals | ((dx * 1.6 + dy) < 0.06)
    motif &= ~stripes
    img[motif] = hex_rgb(fg)
    n = fbm((h, w), 6, 3, seed)
    img *= (0.9 + 0.2 * n)[..., None]
    return np.clip(img, 0, 1)


def bricks(size=512, brick='#6e3b2c', mortar='#3b3530', rows=8, cols=4, seed=3, var=0.15, rough=0.25):
    h = w = size
    rng = _rng(seed)
    y = np.arange(h)[:, None] / h * rows
    x = np.arange(w)[None, :] / w * cols
    r = np.floor(y).astype(int)
    xx = x + (r % 2) * 0.5
    c = np.floor(xx).astype(int) % cols
    fy = y - np.floor(y)
    fx = xx - np.floor(xx)
    tint = rng.uniform(-var, var, (rows, cols))
    n = fbm((h, w), 8, 4, seed + 1)
    img = hex_rgb(brick) * (1 + tint[r % rows, c])[..., None]
    img = img * (1 - rough + rough * 2 * n)[..., None]
    m = (fy < 0.08) | (fx < 0.04)
    img[m] = hex_rgb(mortar) * (0.8 + 0.4 * n[m])[..., None]
    return np.clip(img, 0, 1)


def flagstones(size=512, stone='#5b5d5a', grout='#2e2f2c', n_cells=7, seed=4):
    """Irregular stone slabs (periodic Voronoi)."""
    h = w = size
    rng = _rng(seed)
    pts = rng.random((n_cells * n_cells, 2))
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    best = np.full((h, w), 9.0)
    second = np.full((h, w), 9.0)
    owner = np.zeros((h, w), int)
    for i, (py, px) in enumerate(pts):
        dy = np.abs(yy - py)
        dy = np.minimum(dy, 1 - dy)
        dx = np.abs(xx - px)
        dx = np.minimum(dx, 1 - dx)
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < best
        second = np.where(closer, best, np.minimum(second, d))
        owner = np.where(closer, i, owner)
        best = np.where(closer, d, best)
    tint = rng.uniform(-0.12, 0.12, len(pts))
    n = fbm((h, w), 8, 4, seed + 3)
    img = hex_rgb(stone) * (1 + tint[owner] + (n - 0.5) * 0.35)[..., None]
    edge = (second - best) < 0.012
    img[edge] = hex_rgb(grout)
    return np.clip(img, 0, 1)


def checker_tiles(size=512, a='#d8d0bc', b='#2a2826', tiles=4, seed=5):
    h = w = size
    y = np.arange(h)[:, None] / h * tiles
    x = np.arange(w)[None, :] / w * tiles
    chk = ((np.floor(x) + np.floor(y)) % 2).astype(bool)
    img = np.where(chk[..., None], hex_rgb(a), hex_rgb(b))
    n = fbm((h, w), 8, 3, seed)
    img = img * (0.88 + 0.2 * n)[..., None]
    gx = (x % 1.0)
    gy = (y % 1.0)
    grout = (gx < 0.02) | (gy < 0.02)
    img[grout] *= 0.55
    return np.clip(img, 0, 1)


def stripes(size=512, a='#b8322e', b='#efe2c4', count=4, seed=6, wear=0.18, vertical=True):
    """Painted canvas stripes for tents and awnings."""
    h = w = size
    y = np.arange(h)[:, None] / h
    x = np.arange(w)[None, :] / w
    coord = x if vertical else y
    band = (np.floor(coord * count * 2) % 2).astype(bool)
    band = np.broadcast_to(band, (h, w))
    img = np.where(band[..., None], hex_rgb(a), hex_rgb(b))
    weave = (np.sin(x * w * 1.3) * np.sin(y * h * 1.3)) * 0.03
    n = fbm((h, w), 5, 4, seed)
    img = img * (1 - wear + wear * 2 * n + weave)[..., None]
    return np.clip(img, 0, 1)


def boards(size=512, base='#7a2a22', dark='#3d1612', boards_n=6, seed=7, wear=0.3, weathered='#9a8a7a'):
    """Vertical painted barn boards with peeling paint."""
    h = w = size
    rng = _rng(seed)
    x = np.arange(w)[None, :] / w * boards_n
    col = np.floor(x).astype(int) % boards_n
    fx = x - np.floor(x)
    tint = rng.uniform(-0.1, 0.1, boards_n)
    grain = value_noise((h, w), (2, boards_n * 12), seed + 1)
    n = fbm((h, w), 6, 5, seed + 2)
    img = hex_rgb(base) * (1 + tint[col] + (grain - 0.5) * 0.25)[..., None]
    peel = n > (1 - wear * 0.9)
    img = np.where(np.broadcast_to(peel[..., None], (h, w, 3)), hex_rgb(weathered) * (0.8 + 0.3 * grain[..., None]), img)
    gap = np.broadcast_to((fx < 0.03) | (fx > 0.97), (h, w))
    img[gap] = hex_rgb(dark)
    return np.clip(img, 0, 1)


def ground(size=512, a='#3d4a2a', b='#5a5a32', c='#4a3a28', seed=8, scale=5):
    """Grass/dirt mottling."""
    h = w = size
    n1 = fbm((h, w), scale, 5, seed)
    n2 = fbm((h, w), scale * 2, 4, seed + 7)
    img = _mix(hex_rgb(a), hex_rgb(b), (n1 - 0.3) * 2)
    img = _mix(img, hex_rgb(c), np.clip((n2 - 0.62) * 5, 0, 1))
    speck = value_noise((h, w), 128, seed + 3)
    img *= (0.85 + 0.3 * speck)[..., None]
    return np.clip(img, 0, 1)


def shingles(size=512, base='#3b3f4a', rows=8, cols=6, seed=9):
    h = w = size
    rng = _rng(seed)
    y = np.arange(h)[:, None] / h * rows
    x = np.arange(w)[None, :] / w * cols
    r = np.floor(y).astype(int)
    xx = x + (r % 2) * 0.5
    c = np.floor(xx).astype(int) % cols
    fy = y - np.floor(y)
    fx = xx - np.floor(xx)
    tint = rng.uniform(-0.15, 0.15, (rows, cols))
    img = hex_rgb(base) * (1 + tint[r % rows, c] - fy * 0.35)[..., None]
    gap = (fx < 0.03) | (fy > 0.95)
    img[gap] *= 0.4
    return np.clip(img, 0, 1)


def fabric(size=256, base='#3c5a3a', seed=10, weave=0.06, pattern=None, pattern_col='#c9a24a'):
    h = w = size
    y = np.arange(h)[:, None] / h
    x = np.arange(w)[None, :] / w
    n = fbm((h, w), 6, 3, seed)
    wv = np.sin(x * w * np.pi * 0.5) * np.sin(y * h * np.pi * 0.5) * weave
    img = hex_rgb(base) * (0.9 + 0.2 * n + wv)[..., None]
    if pattern == 'diamonds':
        d = (np.abs((x * 6) % 1 - 0.5) + np.abs((y * 6) % 1 - 0.5))
        mask = np.broadcast_to((d > 0.42) & (d < 0.47), (h, w))
        img[mask] = hex_rgb(pattern_col)
    elif pattern == 'border':
        e = np.minimum(np.minimum(x, 1 - x), np.minimum(y, 1 - y))
        mask = np.broadcast_to(((e > 0.06) & (e < 0.09)) | ((e > 0.12) & (e < 0.13)), (h, w))
        img[mask] = hex_rgb(pattern_col)
    return np.clip(img, 0, 1)


def noise_tint(size=256, base='#888888', amount=0.25, cells=6, seed=11):
    n = fbm((size, size), cells, 4, seed)
    img = hex_rgb(base) * (1 - amount + 2 * amount * n)[..., None]
    return np.clip(img, 0, 1)
