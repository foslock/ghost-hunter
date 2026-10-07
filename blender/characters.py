"""Ghost Hunter character + item models -> client/public/models/characters.glb

    Blender -b --factory-startup -P blender/characters.py [-- --preview]

Every model is a root empty at the world origin standing on Z=0 and facing
Blender +Y (three.js -Z). Roots: ghost, hunter, relic, revealer, altar_glow.
Named parts (the client looks these up by name):

  ghost      ghost_body (one material: ghost_cloth), ghost_eyes (ghost_eyes)
  hunter     hunter_body, hunter_head (empty pivot at the neck), hunter_arm
             (empty pivot at the right shoulder) > hunter_muzzle (empty)
  relic      relic_body, relic_core (relic_glow)
  revealer   revealer_body, revealer_chamber (revealer_glass),
             revealer_lens (revealer_glow), revealer_filament, revealer_muzzle
  altar_glow altar_glow_ring (altar_rune)

`--preview` also renders EEVEE stills to blender/build/preview/chars_*.png.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import gh  # noqa: E402
from lib.gh import TAU, Geo, X  # noqa: E402

ARGS = gh.script_args()
OUT = os.path.join(gh.ROOT, 'client', 'public', 'models', 'characters.glb')
PREVIEW_DIR = os.path.join(gh.BUILD_DIR, 'preview')
SHARP = math.radians(50)
PI = math.pi

bpy.ops.wm.read_factory_settings(use_empty=True)
SCENE = bpy.context.scene
COLL = SCENE.collection


# ------------------------------------------------------------------ helpers

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(e0, e1, x):
    t = clamp((x - e0) / (e1 - e0))
    return t * t * (3 - 2 * t)


def wrap(a):
    return (a + PI) % TAU - PI


MATS = {}


def mat(name, color, rough=0.8, metal=0.0, emit=None, strength=1.0, alpha=None):
    if name in MATS:
        return MATS[name]
    m = gh.Mat(name, color, rough=rough, metal=metal, emit=emit, strength=strength)
    assert m.bmat.name == name, m.bmat.name
    if alpha is not None:
        bsdf = next(n for n in m.bmat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Alpha'].default_value = alpha
        for attr, val in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
            try:
                setattr(m.bmat, attr, val)
            except (AttributeError, TypeError):
                pass
    MATS[name] = m
    return m


OBJECTS = {}   # root name -> [objects]


def _link(ob, parent, root):
    COLL.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    OBJECTS.setdefault(root, []).append(ob)
    return ob


def empty(name, parent=None, loc=(0, 0, 0), root=None, size=0.1):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_size = size
    ob.location = loc
    return _link(ob, parent, root or name)


def mesh_obj(name, geo, parent, root, sharp=True):
    me = geo.to_mesh(name + '_geo')
    # untextured models: drop the toolkit's box-projected UVs (they only split vertices)
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    if sharp and hasattr(me, 'set_sharp_from_angle'):
        me.set_sharp_from_angle(angle=SHARP)
    ob = bpy.data.objects.new(name, me)
    assert ob.name == name, ob.name
    return _link(ob, parent, root)


def tris(ob):
    if ob.type != 'MESH':
        return 0
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# ------------------------------------------------------------------ primitives

def crs(rows, t):
    """Catmull-Rom through a list of equal-length tuples, t in [0,1] (uniform in index)."""
    n = len(rows)
    if n == 1:
        return rows[0]
    f = clamp(t) * (n - 1)
    i = min(int(f), n - 2)
    u = f - i
    p0 = rows[max(i - 1, 0)]
    p1, p2 = rows[i], rows[i + 1]
    p3 = rows[min(i + 2, n - 1)]
    out = []
    for a, b, c, d in zip(p0, p1, p2, p3):
        out.append(0.5 * (2 * b + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3))
    return tuple(out)


def arc_resample(rows, n_out, dense=400):
    """Sample a Catmull-Rom curve through `rows` at n_out+1 points equally spaced by arc length
    (distance uses the first two components)."""
    pts = [crs(rows, k / dense) for k in range(dense + 1)]
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = acc[-1]
    out = []
    j = 0
    for k in range(n_out + 1):
        s = total * k / n_out
        while j < dense - 1 and acc[j + 1] < s:
            j += 1
        w = (s - acc[j]) / max(acc[j + 1] - acc[j], 1e-9)
        out.append(tuple(lerp(a, b, clamp(w)) for a, b in zip(pts[j], pts[j + 1])))
    return out


def surface(fn, nu, nv, closed=True, pole_bottom=False, pole_top=False, smooth=True, flip=False):
    """Grid surface fn(u, v) -> point, u around (0..1), v along (0..1)."""
    verts, faces = [], []
    cols = nu if closed else nu + 1
    rows = []
    for i in range(nv + 1):
        v = i / nv
        if (i == 0 and pole_bottom) or (i == nv and pole_top):
            rows.append([len(verts)] * cols)
            verts.append(tuple(fn(0.0, v)))
            continue
        row = []
        for j in range(cols):
            row.append(len(verts))
            verts.append(tuple(fn(j / nu, v)))
        rows.append(row)
    for i in range(nv):
        for j in range(nu):
            j2 = (j + 1) % cols
            f = []
            for k in (rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]):
                if k not in f:
                    f.append(k)
            if len(f) >= 3:
                faces.append(tuple(reversed(f)) if flip else tuple(f))
    return verts, faces, [smooth] * len(faces)


def shell(g, fn, nu, nv, t, mat_out, mat_in, closed=False, sides=True, bottom=True, top=False):
    """Two-sided cloth panel with thickness: fn(u, v, inset) -> point."""
    g.add(surface(lambda u, v: fn(u, v, 0.0), nu, nv, closed), mat_out)
    g.add(surface(lambda u, v: fn(u, v, t), nu, nv, closed, flip=True), mat_in)
    if bottom:
        g.add(surface(lambda u, w: fn(u, 0.0, t * w), nu, 1, closed, flip=True), mat_out)
    if top:
        g.add(surface(lambda u, w: fn(u, 1.0, t * w), nu, 1, closed), mat_out)
    if sides and not closed:
        g.add(surface(lambda w, v: fn(0.0, v, t * w), 1, nv, False), mat_out)
        g.add(surface(lambda w, v: fn(1.0, v, t * w), 1, nv, False, flip=True), mat_out)


def sel(th, rx, ry, e=2.0):
    """Superellipse point."""
    c, s = math.cos(th), math.sin(th)
    return (rx * math.copysign(abs(c) ** (2 / e), c), ry * math.copysign(abs(s) ** (2 / e), s))


def smooth_path(points, sub=4):
    pts = [tuple(p) for p in points]
    out = []
    for k in range((len(pts) - 1) * sub + 1):
        out.append(Vector(crs(pts, k / ((len(pts) - 1) * sub))))
    return out


def vtube(points, radii, n=8, caps=True, smooth=True):
    """Tapered tube along a polyline using parallel-transport frames."""
    pts = [Vector(p) for p in points]
    if isinstance(radii, (int, float)):
        radii = [radii] * len(pts)
    T = []
    for i in range(len(pts)):
        d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        T.append(d.normalized())
    up = Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0))
    N = T[0].cross(up).normalized()
    verts, faces, sm = [], [], []
    for i, p in enumerate(pts):
        if i > 0:
            ax = T[i - 1].cross(T[i])
            if ax.length > 1e-7:
                N = Matrix.Rotation(T[i - 1].angle(T[i]), 3, ax.normalized()) @ N
        B = T[i].cross(N).normalized()
        N = B.cross(T[i]).normalized()
        for j in range(n):
            a = TAU * j / n
            verts.append(tuple(p + (N * math.cos(a) + B * math.sin(a)) * radii[i]))
    for i in range(len(pts) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((i * n + j, i * n + j2, (i + 1) * n + j2, (i + 1) * n + j))
            sm.append(smooth)
    if caps:
        faces.append(tuple(reversed(range(n))))
        last = (len(pts) - 1) * n
        faces.append(tuple(last + j for j in range(n)))
        sm += [False, False]
    return verts, faces, sm


def ribbon(points, normals, width, thick, widths=None):
    """Flat strap: rectangle cross-section; normals give the strap's face direction."""
    pts = [Vector(p) for p in points]
    verts, faces = [], []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        nrm = Vector(normals[i] if isinstance(normals, list) else normals)
        nrm = (nrm - d * nrm.dot(d)).normalized()
        side = d.cross(nrm).normalized()
        w = (widths[i] if widths else width) / 2
        t = thick / 2
        for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            verts.append(tuple(p + side * w * sx + nrm * t * sy))
    for i in range(len(pts) - 1):
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((i * 4 + k, (i + 1) * 4 + k, (i + 1) * 4 + k2, i * 4 + k2))
    faces.append((3, 2, 1, 0))
    L = (len(pts) - 1) * 4
    faces.append((L, L + 1, L + 2, L + 3))
    return verts, faces, [True] * len(faces)


def basis(pos, normal, up=(0, 0, 1), spin=0.0, scale=(1, 1, 1)):
    """Matrix whose local +Y is `normal`, +Z is as close to `up` as possible."""
    n = Vector(normal).normalized()
    u = Vector(up)
    u = (u - n * u.dot(n)).normalized()
    s = n.cross(u).normalized()
    m = Matrix((s, n, u)).transposed().to_4x4()
    return Matrix.Translation(pos) @ m @ Matrix.Rotation(spin, 4, 'Y') @ Matrix.Diagonal((*scale, 1.0))


# ------------------------------------------------------------------ ghost

def build_ghost():
    root = empty('ghost', size=0.5)
    cloth = mat('ghost_cloth', '#eef2f4', rough=0.75)
    eyes_m = mat('ghost_eyes', '#07060c', rough=0.35)

    K = 6                                   # hem scallops
    th0 = PI / 2 - PI / K                   # a lobe hangs at the front
    prof = [(0.445, 0.04), (0.425, 0.19), (0.38, 0.42), (0.335, 0.66), (0.298, 0.88), (0.272, 1.05),
            (0.254, 1.16), (0.266, 1.28), (0.262, 1.38), (0.22, 1.47), (0.126, 1.535), (0.0, 1.552)]
    NV, NU = 46, 56
    rings = arc_resample(prof, NV)
    arms = [(0.30, 0.87, 1.0), (PI - 0.30, 0.87, -1.0)]

    def gpos(th, r, z):
        z0 = z
        A = smoothstep(0.40, 0.04, z0)      # hem zone
        A2 = smoothstep(0.95, 0.08, z0)     # drapery zone
        th = th + 0.10 * A2 * A2            # slight swirl
        phi = K * (th - th0) / 2 + 0.22 * math.sin(th + 0.5) * A2   # uneven lobe widths
        s = abs(math.sin(phi)) ** 0.7
        drop = 0.125 + 0.045 * math.sin(2 * th + 0.7) + 0.028 * math.sin(5 * th + 2.0)
        z = z + A * (0.17 - drop * s)
        r = r * (1 + 0.075 * A2 * -math.cos(2 * phi))
        for ath, az, side in arms:
            dth = wrap(th - ath)
            q = (r * dth / 0.08) ** 2 + ((z0 - az) / 0.075) ** 2
            if q < 1:
                w = (1 - q) ** 1.35
                r += 0.13 * w
                z -= 0.06 * w
                th += 0.12 * w * side
        sy = lerp(0.84, 0.97, smoothstep(1.02, 1.30, z0))
        x = r * math.cos(th)
        y = r * sy * math.sin(th)
        y -= 0.11 * smoothstep(1.15, 0.05, z0) ** 1.6
        return Vector((x, y, z))

    def fn(u, v):
        r, z = rings[round(v * NV)]
        return gpos(TAU * u, r, z)

    g = Geo()
    g.add(surface(fn, NU, NV, closed=True, pole_top=True), cloth)
    body = mesh_obj('ghost_body', g, root, 'ghost', sharp=False)

    # face features sit just proud of the head surface
    def at_height(zt):
        lo, hi = 0.5, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if crs(prof, mid)[1] < zt:
                lo = mid
            else:
                hi = mid
        return crs(prof, lo)[0]

    def surf(th, z):
        r = at_height(z)
        p = gpos(th, r, z)
        e = 0.004
        a = gpos(th + e, at_height(z), z) - gpos(th - e, at_height(z), z)
        b = gpos(th, at_height(z + e), z + e) - gpos(th, at_height(z - e), z - e)
        n = a.cross(b).normalized()
        return p, n

    ge = Geo()
    for side in (-1, 1):
        p, n = surf(PI / 2 + side * 0.30, 1.33)
        ge.add(gh.prim_sphere(1.0, 16, 8), eyes_m,
               basis(p - n * 0.010, n, spin=side * 0.14, scale=(0.046, 0.02, 0.068)))
    p, n = surf(PI / 2, 1.20)
    ge.add(gh.prim_sphere(1.0, 12, 6), eyes_m, basis(p - n * 0.008, n, scale=(0.026, 0.016, 0.033)))
    mesh_obj('ghost_eyes', ge, root, 'ghost', sharp=False)
    return root


# ------------------------------------------------------------------ revealer

REV_A = 0.08          # barrel axis height above the grip centre
REV_MUZZLE = 0.326    # bell mouth (Y)


def draw_revealer(G, M):
    """Full-detail revealer into geos G (body, lens, chamber, fil). Origin = grip centre,
    barrel axis along +Y at z=REV_A. Returns the muzzle point."""
    b, lens, ch, fil = G['body'], G['lens'], G['chamber'], G['fil']
    A = REV_A
    n = 28
    RY = -PI / 2  # lathe Z -> +Y

    def yl(g, y0, prof, m, nn=n, cb=True, ct=True, smooth=True):
        g.lathe((0, y0, A), prof, m, n=nn, rx=RY, cap_bottom=cb, cap_top=ct, smooth=smooth)

    def ring(y, R, r, m, nn=n, m2=8):
        b.torus((0, y, A), R, r, m, n=nn, m=m2, rx=RY)

    # winding key at the back
    b.cyl((0, -0.142, A), 0.0055, 0.03, M['brass'], n=10, rx=RY)
    for sx in (-1, 1):
        b.cyl((sx * 0.016, -0.146, A), 0.014, 0.006, M['brass'], n=16, rx=RY)
        b.torus((sx * 0.016, -0.143, A), 0.0095, 0.0016, M['dark'], n=12, m=4, rx=RY)
    b.box((0, -0.143, A), (0.034, 0.006, 0.009), M['brass'], bevel=0.002)
    # rear cap + tank
    yl(b, -0.118, [(0.014, 0.0), (0.027, 0.004), (0.037, 0.011), (0.0435, 0.021), (0.0455, 0.031)], M['brass'])
    ring(-0.086, 0.046, 0.0042, M['brass'])
    ring(-0.1085, 0.0335, 0.0022, M['copper'], m2=5)
    for k in range(8):
        a = TAU * k / 8
        b.sphere((math.cos(a) * 0.0405, -0.1005, A + math.sin(a) * 0.0405), 0.0028, M['copper'], n=6)
    b.cyl((0, -0.088, A), 0.044, 0.134, M['brass'], n=n, rx=RY)
    yl(b, -0.038, [(0.0445, 0.0), (0.0475, 0.002), (0.0475, 0.032), (0.0445, 0.034)], M['copper'])
    for k in range(12):
        a = TAU * k / 12
        b.sphere((math.cos(a) * 0.0478, -0.021, A + math.sin(a) * 0.0478), 0.0032, M['brass'], n=6)
    ring(0.0, 0.0455, 0.0028, M['brass'])
    # chamber collars + cage (no bar on top so the filament shows from behind)
    for y0 in (0.042, 0.166):
        yl(b, y0, [(0.044, 0.0), (0.05, 0.003), (0.05, 0.009), (0.044, 0.012)], M['brass'])
    yl(ch, 0.054, [(0.0362, 0.0), (0.0368, 0.056), (0.0362, 0.112)], M['glass'], nn=n)
    for k in range(6):
        a = TAU * k / 6
        b.cyl((math.cos(a) * 0.0415, 0.054, A + math.sin(a) * 0.0415), 0.0032, 0.112, M['brass'], n=6, rx=RY)
    # filament: helix coil between two posts, with a hot bead in the middle
    coil = []
    for k in range(57):
        t = k / 56
        a = t * TAU * 7
        coil.append((math.cos(a) * 0.009, 0.074 + 0.072 * t, A + math.sin(a) * 0.009))
    fil.add(vtube(coil, 0.0017, n=4), M['fil'])
    fil.sphere((0, 0.11, A), 0.0075, M['fil'], n=10)
    for y0, dy in ((0.054, 0.02), (0.146, 0.02)):
        b.cyl((0, y0, A), 0.0028, dy, M['dark'], n=6, rx=RY)
    # neck + bell
    yl(b, 0.178, [(0.044, 0.0), (0.037, 0.008), (0.032, 0.02), (0.031, 0.034)], M['brass'])
    ring(0.2, 0.0335, 0.0035, M['brass'])
    bell = [(0.031, 0.0), (0.032, 0.018), (0.036, 0.04), (0.044, 0.062), (0.056, 0.08), (0.069, 0.095),
            (0.0775, 0.106)]
    yl(b, 0.21, bell, M['brass'], cb=False, ct=False)
    ring(0.252, 0.0405, 0.0026, M['brass'], m2=6)
    ring(0.316, 0.0765, 0.0055, M['brass'])
    yl(b, 0.21, [(0.048, 0.072), (0.058, 0.084), (0.068, 0.096), (0.074, 0.106)], M['copper'], cb=False, ct=False)
    for k in range(8):
        a = TAU * k / 8 + PI / 8
        b.sphere((math.cos(a) * 0.0325, 0.218, A + math.sin(a) * 0.0325), 0.0028, M['brass'], n=6)
    # the emitter face: stepped fresnel lens set into the bell throat
    lens.lathe((0, 0.281, A), [(0.0495, 0.0), (0.046, 0.002), (0.034, 0.004), (0.034, 0.0065), (0.022, 0.008),
                               (0.022, 0.0105), (0.011, 0.012), (0.0001, 0.0135)], M['glow'], n=n, rx=RY,
               cap_bottom=False, cap_top=False)
    # receiver block + grip
    b.box((0, -0.028, A - 0.042), (0.03, 0.108, 0.026), M['brass'], bevel=0.006)
    with b.at((0, 0, 0), rx=-0.26):
        grip = [(-0.072, 0.0145, 0.0235), (-0.05, 0.0165, 0.027), (-0.015, 0.0175, 0.0285),
                (0.02, 0.0165, 0.026), (0.048, 0.015, 0.0235)]

        def gfn(u, v):
            z, rx, ry = crs(grip, v)
            x, y = sel(TAU * u, rx, ry, 2.6)
            return Vector((x, y, z))
        b.add(surface(gfn, 16, 8, closed=True), M['leather'])
        for zz in (-0.045, -0.02, 0.005, 0.03):
            rx, ry = crs(grip, (zz + 0.072) / 0.12)[1:]
            b.add(surface(lambda u, v, zz=zz, rx=rx, ry=ry: Vector(
                (*sel(TAU * u, rx + 0.0012, ry + 0.0012, 2.6), zz + 0.004 * (v - 0.5))), 16, 1), M['dark'])
        b.lathe((0, 0, -0.084), [(0.006, 0.0), (0.014, 0.003), (0.018, 0.008), (0.0185, 0.014)], M['brass'], n=14)
        b.torus((0, -0.012, -0.09), 0.008, 0.0022, M['brass'], n=10, m=4, rz=PI / 2, ry=PI / 2)
        b.lathe((0, 0, 0.044), [(0.02, 0.0), (0.021, 0.004), (0.02, 0.012)], M['brass'], n=14)
    # trigger guard + trigger
    guard = [(0, 0.064, A - 0.05), (0, 0.068, A - 0.078), (0, 0.054, A - 0.098), (0, 0.032, A - 0.102),
             (0, 0.017, A - 0.09)]
    b.add(vtube(smooth_path(guard, 3), 0.0038, n=6), M['brass'])
    trig = [(0, 0.036, A - 0.054), (0, 0.042, A - 0.07), (0, 0.037, A - 0.084)]
    b.add(vtube(smooth_path(trig, 3), 0.004, n=6), M['dark'])
    # pipes
    left = [(-0.03, -0.07, A + 0.032), (-0.052, -0.062, A + 0.022), (-0.062, -0.03, A + 0.016),
            (-0.061, 0.06, A + 0.014), (-0.058, 0.15, A + 0.012), (-0.046, 0.188, A + 0.006), (-0.031, 0.206, A + 0.002)]
    right = [(0.03, -0.06, A - 0.032), (0.052, -0.05, A - 0.03), (0.06, -0.02, A - 0.028),
             (0.06, 0.09, A - 0.026), (0.055, 0.16, A - 0.02), (0.044, 0.19, A - 0.012), (0.031, 0.204, A - 0.006)]
    for path in (left, right):
        sp = smooth_path(path, 4)
        b.add(vtube(sp, 0.0055, n=8), M['copper'])
        for p, q in ((sp[0], sp[1]), (sp[-1], sp[-2])):
            d = (p - q).normalized()
            b.add(vtube([p - d * 0.006, p + d * 0.004], 0.0078, n=8), M['brass'])
        for y in (0.05, 0.17):
            p = min(sp, key=lambda q: abs(q.y - y))
            b.add(vtube([p - Vector((0, 0.004, 0)), p + Vector((0, 0.004, 0))], 0.0072, n=8), M['patina'])
    # valve wheel on the right pipe
    vp = Vector((0.06, 0.03, A - 0.027))
    b.cyl(tuple(vp), 0.003, 0.016, M['brass'], n=6, ry=PI / 2)
    wc = vp + Vector((0.017, 0, 0))
    b.torus(tuple(wc), 0.011, 0.0022, M['oxblood'], n=12, m=4, ry=PI / 2)
    for k in range(4):
        a = k * PI / 4
        b.box(tuple(wc), (0.002, 0.021 * abs(math.cos(a)) + 0.002, 0.021 * abs(math.sin(a)) + 0.002), M['oxblood'])
    b.sphere(tuple(wc), 0.0035, M['brass'], n=6)
    # pressure gauge on top, tilted toward the holder
    with b.at((-0.012, -0.05, A + 0.04), rx=0.75):
        b.cyl((0, 0, -0.006), 0.009, 0.012, M['brass'], n=10)
        b.cyl((0, 0, 0.004), 0.024, 0.012, M['brass'], n=n)
        b.cyl((0, 0, 0.0155), 0.0205, 0.001, M['ivory'], n=n)
        b.torus((0, 0, 0.0165), 0.0215, 0.0028, M['brass'], n=n, m=6)
        for k in range(9):
            a = PI * 1.25 - k * PI * 1.5 / 8
            b.box((math.cos(a) * 0.0165, math.sin(a) * 0.0165, 0.0168), (0.0012, 0.0045, 0.0006),
                  M['dark'], rz=a + PI / 2)
        b.box((math.cos(PI * -0.2) * 0.012, math.sin(PI * -0.2) * 0.012, 0.0168), (0.004, 0.006, 0.0007),
              M['oxblood'], rz=PI * -0.2 + PI / 2)
        b.box((0.0035, 0.0045, 0.0172), (0.0016, 0.017, 0.0007), M['dark'], rz=-0.65)
        b.sphere((0, 0, 0.0172), 0.0022, M['brass'], n=6)
        b.add(gh.prim_sphere(0.0205, 16, 4), M['glass'], X((0, 0, 0.0165), s=(1, 1, 0.18)))
    # small side dial (right) and toggle (left)
    with b.at((0.044, 0.022, A + 0.012), rz=-PI / 2, rx=-PI / 2 + 0.35):
        b.cyl((0, 0, -0.004), 0.0135, 0.009, M['brass'], n=14)
        b.cyl((0, 0, 0.0052), 0.011, 0.001, M['ivory'], n=14)
        b.box((0.002, 0.002, 0.0064), (0.0012, 0.01, 0.0006), M['dark'], rz=0.6)
    with b.at((-0.044, 0.02, A + 0.006), rz=PI / 2, rx=-PI / 2):
        b.box((0, 0, 0.0), (0.016, 0.026, 0.006), M['brass'], bevel=0.0015)
        b.cyl((0, 0, 0.002), 0.0022, 0.016, M['dark'], n=6, rx=-0.45)
        b.sphere((0, 0.0068, 0.016), 0.0042, M['oxblood'], n=8)
    # power cell under the chamber
    b.cyl((0, 0.06, A - 0.052), 0.0135, 0.094, M['copper'], n=12, rx=RY)
    for y0 in (0.056, 0.15):
        b.cyl((0, y0, A - 0.052), 0.0152, 0.008, M['brass'], n=12, rx=RY)
    for y0 in (0.075, 0.135):
        b.box((0, y0, A - 0.042), (0.008, 0.008, 0.016), M['brass'])
    return Vector((0, REV_MUZZLE, A))


def draw_revealer_lo(g, M):
    """Low-poly revealer silhouette for the third-person hunter (same proportions/origin)."""
    A = REV_A
    n = 8
    RY = -PI / 2

    def yl(y0, prof, m, cb=True, ct=True, nn=n):
        g.lathe((0, y0, A), prof, m, n=nn, rx=RY, cap_bottom=cb, cap_top=ct)
    g.box((0, -0.143, A), (0.044, 0.006, 0.016), M['brass'])
    yl(-0.118, [(0.016, 0.0), (0.036, 0.01), (0.0455, 0.03)], M['brass'], ct=False)
    g.cyl((0, -0.088, A), 0.044, 0.13, M['brass'], n=n, rx=RY, caps=False)
    g.cyl((0, -0.038, A), 0.0475, 0.034, M['copper'], n=n, rx=RY, caps=False)
    for y0 in (0.042, 0.166):
        g.cyl((0, y0, A), 0.05, 0.012, M['brass'], n=n, rx=RY)
    g.cyl((0, 0.054, A), 0.037, 0.112, M['glow'], n=n, rx=RY, caps=False)
    yl(0.178, [(0.044, 0.0), (0.032, 0.02), (0.031, 0.034), (0.036, 0.072), (0.048, 0.094), (0.066, 0.112),
               (0.077, 0.138)], M['brass'], cb=False, ct=False)
    g.torus((0, 0.316, A), 0.0765, 0.006, M['brass'], n=n, m=3, rx=RY)
    g.cyl((0, 0.288, A), 0.06, 0.002, M['glow'], n=n, rx=RY)
    g.box((0, -0.028, A - 0.042), (0.03, 0.1, 0.026), M['brass'])
    g.box((0, -0.004, -0.014), (0.034, 0.052, 0.13), M['leather'], rx=-0.26, bevel=0.008)
    g.add(vtube(smooth_path([(0, 0.064, A - 0.05), (0, 0.06, A - 0.095), (0, 0.02, A - 0.095)], 1), 0.004, n=4),
          M['brass'])
    with g.at((-0.012, -0.05, A + 0.04), rx=0.75):
        g.cyl((0, 0, -0.004), 0.023, 0.016, M['brass'], n=n)
        g.cyl((0, 0, 0.012), 0.019, 0.001, M['ivory'], n=n, caps=True)
    for path in ([(-0.03, -0.07, A + 0.032), (-0.062, -0.03, A + 0.016), (-0.058, 0.15, A + 0.012),
                  (-0.031, 0.206, A + 0.002)],
                 [(0.03, -0.06, A - 0.032), (0.06, -0.02, A - 0.028), (0.055, 0.16, A - 0.02),
                  (0.031, 0.204, A - 0.006)]):
        g.add(vtube(smooth_path(path, 2), 0.006, n=4, caps=False), M['copper'])
    return Vector((0, REV_MUZZLE, A))


def build_revealer():
    root = empty('revealer', size=0.1)
    M = dict(
        brass=mat('revealer_brass', '#c99a45', rough=0.32, metal=1.0),
        copper=mat('revealer_copper', '#a5603d', rough=0.45, metal=0.9),
        patina=mat('revealer_patina', '#5f9c84', rough=0.7, metal=0.3),
        leather=mat('revealer_leather', '#4a1813', rough=0.55),
        oxblood=mat('revealer_leather', '#4a1813', rough=0.55),
        dark=mat('revealer_dark', '#2a2522', rough=0.5, metal=0.6),
        ivory=mat('revealer_ivory', '#ecdfc2', rough=0.55),
        glass=mat('revealer_glass', '#bff5e8', rough=0.05, alpha=0.28),
        glow=mat('revealer_glow', '#b8fff0', rough=0.4, emit='#5cffd8', strength=2.5),
        fil=mat('revealer_filament', '#f4fff9', rough=0.4, emit='#b8fff0', strength=8.0),
    )
    G = dict(body=Geo(), lens=Geo(), chamber=Geo(), fil=Geo())
    muzzle = draw_revealer(G, M)
    mesh_obj('revealer_body', G['body'], root, 'revealer')
    mesh_obj('revealer_chamber', G['chamber'], root, 'revealer')
    mesh_obj('revealer_filament', G['fil'], root, 'revealer')
    mesh_obj('revealer_lens', G['lens'], root, 'revealer')
    empty('revealer_muzzle', root, tuple(muzzle), root='revealer', size=0.03)
    return root


# ------------------------------------------------------------------ hunter

def build_hunter():
    root = empty('hunter', size=0.5)
    coat = mat('hunter_coat', '#4f6a47', rough=0.9)
    lining = mat('hunter_leather', '#6e2721', rough=0.7)
    dark = mat('hunter_dark', '#2c2420', rough=0.8)
    brass = mat('hunter_brass', '#c9a04e', rough=0.35, metal=1.0)
    skin = mat('hunter_skin', '#c8957a', rough=0.7)
    scarf = mat('hunter_scarf', '#b8821f', rough=0.85)
    cloth = mat('hunter_cloth', '#5d5249', rough=0.9)
    glow = mat('hunter_glow', '#b8fff0', rough=0.4, emit='#5cffd8', strength=3.0)

    g = Geo()
    E = 2.4

    # torso (closed, boxy superellipse)
    torso = [(0.90, 0.168, 0.118, 0.0), (1.00, 0.170, 0.120, 0.002), (1.12, 0.180, 0.126, 0.008),
             (1.24, 0.195, 0.132, 0.012), (1.34, 0.205, 0.128, 0.008), (1.41, 0.200, 0.118, 0.0),
             (1.455, 0.160, 0.100, -0.005), (1.48, 0.085, 0.07, -0.005)]

    def torso_fn(u, v):
        z, rx, ry, cy = crs(torso, v)
        x, y = sel(TAU * u, rx, ry, E)
        return Vector((x, cy + y, z))
    g.add(surface(torso_fn, 20, 10, closed=True), coat)

    def torso_front(x, z):
        lo, hi = 0.0, 1.0
        for _ in range(30):
            mid = (lo + hi) / 2
            if crs(torso, mid)[0] < z:
                lo = mid
            else:
                hi = mid
        zz, rx, ry, cy = crs(torso, lo)
        return cy + ry * max(0.0, 1 - abs(x / rx) ** E) ** (1 / E)

    # coat skirt with a front slit, oxblood lining
    skirt = [(0.43, 0.285, 0.215, -0.025), (0.60, 0.255, 0.188, -0.012), (0.78, 0.222, 0.160, -0.004),
             (0.92, 0.193, 0.138, 0.0), (1.02, 0.181, 0.131, 0.002)]

    def skirt_at(th, v, inset=0.0):
        z, rx, ry, cy = crs(skirt, v)
        x, y = sel(th, rx - inset, ry - inset, 2.2)
        z += 0.014 * math.sin(3 * th + 1.0) * (1 - v) ** 2
        return Vector((x, cy + y, z))

    def skirt_fn(u, v, inset=0.0):
        gap = 0.40 * (1 - smoothstep(0.0, 0.8, v))
        return skirt_at(PI / 2 + gap + u * (TAU - 2 * gap), v, inset)

    # two panels: open slit at the front, a narrow riding vent at the back
    def panel(side):
        def fn(u, v, inset=0.0):
            front = 0.40 * (1 - smoothstep(0.0, 0.8, v))
            vent = 0.07 * (1 - smoothstep(0.0, 0.45, v))
            if side < 0:   # left half: front-left round to the back
                a0, a1 = PI / 2 + front, 1.5 * PI - vent
            else:          # right half: back round to front-right
                a0, a1 = 1.5 * PI + vent, 2.5 * PI - front
            return skirt_at(a0 + u * (a1 - a0), v, inset)
        return fn
    for side in (-1, 1):
        shell(g, panel(side), 11, 4, 0.012, coat, lining)
    for z in (0.74, 0.86):
        p = skirt_at(1.5 * PI, (z - 0.43) / 0.59 * 0.85)
        g.cyl((p.x, p.y + 0.002, p.z), 0.011, 0.007, brass, n=6, rx=PI / 2)
    # pocket flaps
    for side in (-1, 1):
        th = PI / 2 - side * 1.0
        p = skirt_fn((th - PI / 2) / TAU % 1.0, (0.80 - 0.43) / 0.59)
        nrm = Vector((math.cos(th) / 0.22, math.sin(th) / 0.16, 0.12)).normalized()
        g.add(gh.prim_box(0.10, 0.012, 0.045, bevel=0.004), coat, basis(p + nrm * 0.004, nrm))
        g.add(gh.prim_box(0.012, 0.004, 0.012), brass, basis(p + nrm * 0.011 + Vector((0, 0, -0.012)), nrm))

    # belt + buckle
    belt = [(0.972, 0.194, 0.143), (1.034, 0.192, 0.141)]
    g.add(surface(lambda u, v: Vector((*sel(TAU * u, *crs(belt, v)[1:], 2.4), crs(belt, v)[0])), 20, 1), lining)
    g.box((0, 0.146, 1.003), (0.05, 0.012, 0.048), brass, bevel=0.004)
    g.box((0, 0.151, 1.003), (0.03, 0.006, 0.026), lining)

    # double-breasted buttons
    for z in (1.08, 1.17, 1.26):
        for x in (-0.058, 0.058):
            y = torso_front(x, z)
            g.cyl((x, y - 0.003, z), 0.011, 0.007, brass, n=6, rx=-PI / 2)

    # stand-up collar
    collar = [(1.44, 0.098, 0.084, -0.008), (1.51, 0.104, 0.090, -0.012), (1.575, 0.116, 0.099, -0.02)]

    def collar_fn(u, v, inset=0.0):
        z, rx, ry, cy = crs(collar, v)
        gap = 0.55
        th = PI / 2 + gap + u * (TAU - 2 * gap)
        x, y = sel(th, rx - inset, ry - inset, 2.0)
        return Vector((x, cy + y, z))
    shell(g, collar_fn, 14, 1, 0.008, coat, lining, top=True)

    # shoulder cape, swept back on the gun side
    cape = [(1.15, 0.305, 0.215, -0.012), (1.25, 0.292, 0.200, -0.006), (1.36, 0.258, 0.172, 0.0),
            (1.43, 0.205, 0.138, -0.003), (1.475, 0.13, 0.100, -0.006), (1.495, 0.108, 0.09, -0.006)]

    def cape_fn(u, v, inset=0.0):
        z, rx, ry, cy = crs(cape, v)
        gl = lerp(0.55, 0.40, v)
        gr = lerp(1.28, 0.45, v ** 0.8)
        a0, a1 = PI / 2 + gl, PI / 2 - gr + TAU
        th = a0 + u * (a1 - a0)
        x, y = sel(th, rx - inset, ry - inset, 2.1)
        z += 0.012 * math.sin(4 * th) * (1 - v) ** 2
        return Vector((x, cy + y, z))
    shell(g, cape_fn, 24, 5, 0.010, coat, lining)

    # scarf: two wraps + hanging tails with oxblood stripes and a little fringe
    g.torus((0, -0.004, 1.50), 0.092, 0.032, scarf, n=12, m=5, rx=0.05)
    g.add(gh.prim_torus(0.098, 0.028, 12, 5), scarf, X((0.0, 0.004, 1.465), rx=-0.12, ry=0.1, s=(1.0, 0.92, 1.0)))
    tail1 = [(-0.035, 0.085, 1.47), (-0.05, 0.13, 1.40), (-0.06, 0.15, 1.30), (-0.065, 0.155, 1.20)]
    tail2 = [(-0.01, 0.09, 1.46), (-0.01, 0.135, 1.39), (0.0, 0.150, 1.32), (0.005, 0.155, 1.25)]
    for tail, w in ((tail1, 0.062), (tail2, 0.055)):
        sp = smooth_path(tail, 2)
        g.add(ribbon(sp, (0, 1, 0.1), w, 0.014), scarf)
        end = sp[-1]
        for dz in (0.03, 0.055):
            g.box((end.x, end.y + 0.0005, end.z + dz), (w + 0.003, 0.0165, 0.010), lining)
        for k in range(3):
            g.box((end.x + (k - 1) * w / 3, end.y, end.z - 0.016), (0.008, 0.006, 0.026), scarf)

    # satchel on the left hip + strap over the right shoulder
    sx = -0.262
    g.box((sx, 0.01, 0.84), (0.072, 0.21, 0.16), lining, bevel=0.018)
    g.box((sx - 0.037, 0.01, 0.875), (0.012, 0.214, 0.095), lining, bevel=0.005)
    g.box((sx - 0.045, 0.01, 0.84), (0.006, 0.026, 0.07), dark)
    g.box((sx - 0.048, 0.01, 0.83), (0.006, 0.03, 0.026), brass)
    strap = []
    for k in range(6):
        s = k / 5
        x = lerp(-0.205, 0.14, s)
        z = lerp(0.93, 1.415, s)
        strap.append((x, torso_front(x, z) + 0.006 if z > 0.95 else 0.12, z))
    strap.append((0.17, 0.03, 1.46))
    strap.append((0.17, -0.06, 1.455))
    sp = smooth_path(strap, 1)
    nr = [Vector((p.x * 0.6, p.y, 0.25)) for p in sp]
    g.add(ribbon(sp, nr, 0.04, 0.007), dark)
    g.box((-0.215, 0.10, 0.92), (0.03, 0.01, 0.035), brass)

    # legs + boots
    for side in (-1, 1):
        x = side * 0.095
        g.cyl((x, 0.0, 0.26), 0.068, 0.67, cloth, n=8, r2=0.085, caps=False)
        bx = x + side * 0.008
        g.cyl((bx, 0.0, 0.03), 0.071, 0.2, dark, n=8, caps=False)
        g.cyl((bx, 0.0, 0.23), 0.08, 0.075, dark, n=8, r2=0.083)          # folded cuff
        g.box((bx + side * 0.07, 0.03, 0.2), (0.012, 0.03, 0.022), brass)   # cuff buckle
        with g.at((bx, 0.0, 0.0), rz=-side * 0.12):
            g.sphere((0, 0.075, 0.062), 1.0, dark, n=8, s=(0.064, 0.12, 0.058))
            g.box((0, 0.045, 0.016), (0.12, 0.29, 0.032), dark, bevel=0.01)
            g.box((0, -0.065, 0.032), (0.1, 0.07, 0.03), dark)

    # left arm hangs with the hand resting on the satchel
    larm = [(-0.20, 0.0, 1.40), (-0.235, -0.012, 1.26), (-0.252, -0.008, 1.13), (-0.258, 0.03, 1.02),
            (-0.262, 0.062, 0.955)]
    lp = smooth_path(larm, 2)
    g.add(vtube(lp, [lerp(0.06, 0.045, k / (len(lp) - 1)) for k in range(len(lp))], n=8), coat)
    g.add(vtube([(-0.26, 0.05, 0.975), (-0.263, 0.068, 0.945)], 0.05, n=8), lining)
    g.blob((-0.268, 0.082, 0.925), 1.0, dark, seed=3, jitter=0.08, subdiv=1, s=(0.042, 0.055, 0.04))

    mesh_obj('hunter_body', g, root, 'hunter')

    # ---- head (pivot at the neck)
    head = empty('hunter_head', root, (0, 0, 1.50), root='hunter', size=0.15)
    h = Geo()
    h.cyl((0, 0.0, -0.06), 0.052, 0.12, skin, n=8, caps=False)
    h.sphere((0, 0.012, 0.125), 1.0, skin, n=12, s=(0.105, 0.112, 0.118))
    h.sphere((0, 0.104, 0.105), 1.0, skin, n=6, s=(0.02, 0.03, 0.03), rx=0.3)  # nose
    for side in (-1, 1):
        h.sphere((side * 0.104, 0.0, 0.12), 1.0, skin, n=6, s=(0.018, 0.026, 0.034))  # ears
        h.add(gh.prim_sphere(1.0, 8, 4), dark, X((side * 0.034, 0.104, 0.073), ry=side * 0.35, rz=side * 0.25,
                                                 s=(0.04, 0.02, 0.016)))  # moustache
    h.blob((0, -0.03, 0.15), 1.0, dark, seed=5, jitter=0.12, subdiv=1, s=(0.11, 0.1, 0.09))  # hair
    # goggles
    h.torus((0, 0.012, 0.142), 0.111, 0.009, dark, n=12, m=3)
    for side in (-1, 1):
        cx = side * 0.043
        h.cyl((cx, 0.098, 0.142), 0.031, 0.02, brass, n=10, rx=-PI / 2, caps=False)
        h.torus((cx, 0.118, 0.142), 0.029, 0.0065, brass, n=10, m=4, rx=-PI / 2)
        h.cyl((cx, 0.114, 0.142), 0.025, 0.002, glow, n=10, rx=-PI / 2)
    h.box((0, 0.118, 0.145), (0.022, 0.01, 0.01), brass)
    # wide-brimmed hat
    bz = 0.205

    def brim_fn(u, v, inset=0.0):
        th = TAU * u
        r = lerp(0.112, 0.25, v)
        curl = 0.035 * math.cos(th) ** 2 * v ** 2
        dip = -0.022 * max(0.0, math.sin(th)) * v ** 1.5 - 0.012 * max(0.0, -math.sin(th)) * v ** 1.5
        return Vector((r * math.cos(th), 0.01 + r * 1.04 * math.sin(th), bz + curl + dip - inset))
    h.add(surface(lambda u, v: brim_fn(u, v), 20, 3), dark)
    h.add(surface(lambda u, v: brim_fn(u, v, 0.012), 20, 3, flip=True), dark)
    h.add(surface(lambda u, w: brim_fn(u, 1.0, 0.012 * w), 20, 1), dark)
    h.add(gh.prim_lathe([(0.118, 0.0), (0.121, 0.03), (0.113, 0.095), (0.10, 0.13), (0.055, 0.128),
                         (0.0001, 0.112)], 14, False, False), dark, X((0, 0.008, bz - 0.005), s=(1.0, 0.94, 1.0)))
    h.add(gh.prim_cyl(0.1205, 0.032, 14, 0.1195, caps=False), lining, X((0, 0.008, bz + 0.002), s=(1.0, 0.94, 1.0)))
    h.box((-0.118, 0.03, bz + 0.018), (0.008, 0.024, 0.024), brass)
    feather = [(-0.112, -0.02, bz + 0.02), (-0.125, -0.06, bz + 0.07), (-0.122, -0.10, bz + 0.13), (-0.11, -0.12, bz + 0.17)]
    fp = smooth_path(feather, 2)
    h.add(ribbon(fp, (1, 0, 0), 0.03, 0.004, widths=[0.012, 0.026, 0.034, 0.033, 0.028, 0.018, 0.003]), scarf)
    mesh_obj('hunter_head_mesh', h, head, 'hunter')

    # ---- right arm (pivot at the shoulder) holding a revealer pointing +Y
    shoulder = (0.205, 0.0, 1.40)
    arm = empty('hunter_arm', root, shoulder, root='hunter', size=0.15)
    a = Geo()
    S, Eb, W, H = (0, 0, 0), (0.032, 0.09, -0.255), (0.004, 0.33, -0.205), Vector((-0.004, 0.372, -0.198))
    path = smooth_path([S, (0.024, 0.035, -0.13), Eb, (0.02, 0.21, -0.24), W], 2)
    rad = [lerp(0.06, 0.046, k / (len(path) - 1)) for k in range(len(path))]
    a.add(vtube(path, rad, n=8), coat)
    a.add(vtube([(0.006, 0.285, -0.215), (0.003, 0.335, -0.204)], 0.052, n=8), lining)
    sc = 0.85
    M = dict(brass=brass, copper=brass, leather=dark, ivory=skin, glow=glow)
    with a.at(tuple(H), s=sc):
        muzzle = draw_revealer_lo(a, M)
    a.blob(tuple(H + Vector((0.0, -0.005, 0.0))), 1.0, dark, seed=7, jitter=0.08, subdiv=1, s=(0.045, 0.05, 0.05))
    mesh_obj('hunter_arm_mesh', a, arm, 'hunter')
    empty('hunter_muzzle', arm, tuple(H + muzzle * sc), root='hunter', size=0.03)
    return root


# ------------------------------------------------------------------ relic

def build_relic():
    root = empty('relic', size=0.2)
    brass = mat('relic_brass', '#cfa24c', rough=0.3, metal=1.0)
    enamel = mat('relic_enamel', '#1f4a3c', rough=0.35)
    garnet = mat('relic_garnet', '#8c1a2a', rough=0.15)
    glow = mat('relic_glow', '#a8ffe8', rough=0.4, emit='#2effc0', strength=3.0)
    b = Geo()
    n = 24
    # foot
    b.lathe((0, 0, 0), [(0.076, 0.0), (0.079, 0.006), (0.079, 0.013), (0.072, 0.018), (0.06, 0.024),
                        (0.054, 0.033), (0.042, 0.04), (0.03, 0.047), (0.025, 0.058), (0.027, 0.066),
                        (0.036, 0.072), (0.05, 0.079), (0.061, 0.085), (0.064, 0.092)], brass, n=n)
    b.torus((0, 0, 0.0095), 0.0795, 0.0045, enamel, n=n, m=5)
    b.torus((0, 0, 0.062), 0.027, 0.004, brass, n=14, m=4)
    for k in range(6):
        a = TAU * k / 6
        b.blob((math.cos(a) * 0.052, math.sin(a) * 0.052, 0.031), 1.0, garnet, seed=k, jitter=0.05, subdiv=1,
               s=(0.0075, 0.0075, 0.0075))
    # cage
    b.torus((0, 0, 0.095), 0.056, 0.006, brass, n=n, m=5)
    b.torus((0, 0, 0.247), 0.047, 0.006, brass, n=n, m=5)
    b.torus((0, 0, 0.172), 0.0735, 0.0035, brass, n=n, m=4)
    NR = 6
    for k in range(NR):
        a = TAU * k / NR
        pts = []
        for i in range(9):
            t = i / 8
            z = lerp(0.095, 0.247, t)
            r = lerp(0.055, 0.046, t) + 0.024 * math.sin(PI * t) ** 0.9
            pts.append((math.cos(a) * r, math.sin(a) * r, z))
        b.add(vtube(smooth_path(pts, 2), 0.0042, n=5), brass)
        r = 0.0735
        b.sphere((math.cos(a) * (r + 0.002), math.sin(a) * (r + 0.002), 0.172), 0.0065, brass, n=6)
        # little scroll between ribs
        am = a + TAU / NR / 2
        for zc, flip in ((0.133, 1), (0.212, -1)):
            rr = lerp(0.055, 0.046, (zc - 0.095) / 0.152) + 0.024 * math.sin(PI * (zc - 0.095) / 0.152) ** 0.9
            c = (math.cos(am) * rr, math.sin(am) * rr, zc)
            b.add(gh.prim_torus(0.0105, 0.0022, 10, 3, arc=PI * 1.5), brass,
                  X(c, rz=am + PI / 2, rx=PI / 2, ry=flip * PI / 2 + PI / 4))
    # crown
    b.lathe((0, 0, 0.247), [(0.05, 0.0), (0.052, 0.006), (0.046, 0.014), (0.032, 0.024), (0.02, 0.03),
                            (0.012, 0.034)], brass, n=n)
    for k in range(8):
        a = TAU * k / 8 + PI / 8
        c = (math.cos(a) * 0.046, math.sin(a) * 0.046, 0.252)
        tilt = Matrix.Rotation(0.32, 4, Vector((-math.sin(a), math.cos(a), 0)))
        b.add(gh.prim_cyl(0.0065, 0.03, 6, 0.0005), brass, X(c) @ tilt)
        tip = Vector(c) + Matrix.Rotation(0.32, 3, Vector((-math.sin(a), math.cos(a), 0))) @ Vector((0, 0, 0.03))
        b.sphere(tuple(tip), 0.0045, garnet if k % 2 == 0 else brass, n=6)
    b.cyl((0, 0, 0.278), 0.007, 0.024, brass, n=10)
    b.sphere((0, 0, 0.305), 0.012, brass, n=12)
    b.torus((0, 0, 0.332), 0.0145, 0.0036, brass, n=16, m=6, rx=PI / 2)
    mesh_obj('relic_body', b, root, 'relic')
    c = Geo()
    # a faceted, gently twisted soul flame
    flame = [(0.0001, 0.112), (0.02, 0.118), (0.034, 0.135), (0.039, 0.155), (0.035, 0.178), (0.025, 0.198),
             (0.013, 0.215), (0.0001, 0.234)]

    def flame_fn(u, v):
        i = round(v * (len(flame) - 1))
        r, z = flame[i]
        th = TAU * u + i * 0.42
        lean = 0.012 * (i / (len(flame) - 1)) ** 2
        return Vector((r * math.cos(th) + lean, r * math.sin(th), z))
    c.add(surface(flame_fn, 7, len(flame) - 1, closed=True, pole_bottom=True, pole_top=True, smooth=False), glow)
    rng = random.Random(4)
    for k in range(3):
        a = TAU * k / 3 + 0.4
        c.add(gh.prim_ico(0.0065, 0, 0.1, seed=k), glow,
              X((math.cos(a) * 0.058, math.sin(a) * 0.058, 0.14 + 0.03 * k + rng.uniform(-0.01, 0.01))))
    mesh_obj('relic_core', c, root, 'relic', sharp=False)
    return root


# ------------------------------------------------------------------ altar glow

GLYPHS = [
    [((-0.25, 0), (-0.25, 1)), ((-0.25, 1), (0.3, 0.75)), ((-0.25, 0.6), (0.3, 0.38))],
    [((0, 0), (0, 1)), ((0, 0.55), (-0.35, 0.95)), ((0, 0.55), (0.35, 0.95))],
    [((0, 1), (0.3, 0.65)), ((0.3, 0.65), (0, 0.3)), ((0, 0.3), (-0.3, 0.65)), ((-0.3, 0.65), (0, 1)),
     ((0, 0.3), (0.32, 0)), ((0, 0.3), (-0.32, 0))],
    [((-0.2, 0), (-0.2, 1)), ((-0.2, 0.78), (0.25, 0.5)), ((0.25, 0.5), (-0.2, 0.22))],
    [((-0.3, 0.15), (0.3, 0.85)), ((0.3, 0.15), (-0.3, 0.85)), ((0, 0), (0, 1))],
    [((0, 0), (0, 1)), ((0, 1), (-0.32, 0.68)), ((0, 1), (0.32, 0.68))],
    [((-0.3, 0), (-0.3, 1)), ((0.3, 0), (0.3, 1)), ((-0.3, 1), (0.3, 0.5)), ((0.3, 1), (-0.3, 0.5))],
    [((-0.25, 1), (0.25, 0.68)), ((0.25, 0.68), (-0.25, 0.32)), ((-0.25, 0.32), (0.25, 0))],
]


def build_altar_glow():
    root = empty('altar_glow', size=0.5)
    rune = mat('altar_rune', '#8affe6', rough=0.6, emit='#36ffc6', strength=3.5)
    g = Geo()
    z0, z1 = 0.008, 0.012
    T = z1 - z0

    def band(r0, r1, n=80):  # outer wall, top, inner wall (the underside is never seen)
        g.add(gh.prim_lathe([(r1, z0), (r1, z1), (r0, z1), (r0, z0)], n, False, False, False), rune)
    band(0.745, 0.80)
    band(0.575, 0.595)
    zc = (z0 + z1) / 2
    for k in range(48):  # notches on the inner edge of the outer band
        a = TAU * k / 48
        ln = 0.03 if k % 6 == 0 else 0.016
        g.box((math.cos(a) * (0.745 - ln / 2), math.sin(a) * (0.745 - ln / 2), zc), (ln + 0.002, 0.008, T), rune, rz=a)
    NG = 8
    for k in range(NG):
        a = TAU * k / NG + PI / NG
        strokes = GLYPHS[k % len(GLYPHS)]
        with g.at((0, 0, 0), rz=a - PI / 2):
            for (u0, v0), (u1, v1) in strokes:
                p0 = Vector((u0 * 0.075, 0.618 + v0 * 0.098))
                p1 = Vector((u1 * 0.075, 0.618 + v1 * 0.098))
                d = p1 - p0
                c = (p0 + p1) / 2
                g.box((c.x, c.y, zc), (0.013, d.length + 0.012, T), rune, rz=math.atan2(-d.x, d.y))
        am = a + PI / NG
        g.box((math.cos(am) * 0.667, math.sin(am) * 0.667, zc), (0.026, 0.026, T), rune, rz=am + PI / 4)
    mesh_obj('altar_glow_ring', g, root, 'altar_glow', sharp=False)
    return root


# ------------------------------------------------------------------ export + preview

def export():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=OUT, export_format='GLB', export_yup=True, export_apply=False,
        export_lights=False, export_cameras=False, export_animations=False, use_selection=False,
        export_extras=False, export_materials='EXPORT',
    )


def report(verbose=False):
    parts = []
    for root in ('ghost', 'hunter', 'relic', 'revealer', 'altar_glow'):
        obs = OBJECTS[root]
        t = sum(tris(o) for o in obs)
        mats = sorted({s.material.name for o in obs if o.type == 'MESH' for s in o.material_slots})
        parts.append(f'{root} {t} tris/{len(mats)} mats')
        if not verbose:
            continue
        pts = [o.matrix_world @ v.co for o in obs if o.type == 'MESH' for v in o.data.vertices]
        lo = [round(min(p[i] for p in pts), 3) for i in range(3)]
        hi = [round(max(p[i] for p in pts), 3) for i in range(3)]
        print(f'[chars]   {root}: {t} tris, bounds {lo}..{hi}, mats={mats}')
        for o in obs:
            print(f'[chars]     {o.name:20s} {o.type:5s} parent={o.parent.name if o.parent else "-":12s} '
                  f'loc={tuple(round(c, 3) for c in o.matrix_world.translation)} tris={tris(o)}')
    print(f'[chars] exported {os.path.relpath(OUT, gh.ROOT)}: ' + ', '.join(parts) +
          f', {os.path.getsize(OUT) / 1e6:.2f} MB')


def _lin(hexcol):
    from lib import tex as texlib
    return tuple(gh.srgb_to_linear(c) for c in texlib.hex_rgb(hexcol))


def preview():
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    scene = SCENE
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    try:  # 'Standard' is closest to how three.js shows flat colours; --agx for a filmic look
        scene.view_settings.view_transform = 'AgX' if '--agx' in ARGS else 'Standard'
    except TypeError:
        pass
    try:
        scene.eevee.taa_render_samples = 32
    except AttributeError:
        pass
    world = bpy.data.worlds.new('preview_world')
    scene.world = world
    bg = world.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = (*_lin('#1a1d29'), 1.0)
    bg.inputs[1].default_value = 0.6
    # dark floor disc
    fm = gh.Mat('preview_floor', '#2a2622', rough=0.9)
    fg = Geo()
    fg.cyl((0, 0, -0.02), 3.0, 0.02, fm, n=48)
    floor = bpy.data.objects.new('preview_floor', fg.to_mesh('preview_floor'))
    COLL.objects.link(floor)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    COLL.objects.link(cam)
    scene.camera = cam
    lights = []

    def light_rig(target, dist):
        for o in lights:
            bpy.data.objects.remove(o, do_unlink=True)
        lights.clear()
        tgt = Vector(target)
        for name, d, col, energy, size in (('key', (-1.0, 1.4, 1.2), '#ffe6c8', 150, 1.0),
                                           ('rim', (1.3, -1.2, 0.9), '#a8c4ff', 260, 0.8),
                                           ('fill', (1.4, 1.0, 0.2), '#ffd8b0', 40, 1.5)):
            ld = bpy.data.lights.new(name, 'AREA')
            ld.energy = energy * dist * dist
            ld.color = _lin(col)
            ld.size = size * dist * 0.5
            lo = bpy.data.objects.new(name, ld)
            pos = tgt + Vector(d).normalized() * dist * 2.2
            lo.location = pos
            lo.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
            COLL.objects.link(lo)
            lights.append(lo)

    def show(roots, offsets=None):
        for r, obs in OBJECTS.items():
            for o in obs:
                o.hide_render = r not in roots
        for r in OBJECTS:
            OBJECTS[r][0].location = (0, 0, 0)
        if offsets:
            for r, off in offsets.items():
                OBJECTS[r][0].location = off

    def shoot(name, roots, pos, look, lens=50, dist=None, offsets=None, floor_on=True):
        show(roots, offsets)
        floor.hide_render = not floor_on
        cam.data.lens = lens
        cam.data.clip_start = 0.01
        cam.location = pos
        cam.rotation_euler = (Vector(look) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
        light_rig(look, dist or (Vector(pos) - Vector(look)).length)
        scene.render.filepath = os.path.join(PREVIEW_DIR, f'chars_{name}.png')
        bpy.ops.render.render(write_still=True)
        print('[preview]', scene.render.filepath)

    only = [a.split('=', 1)[1] for a in ARGS if a.startswith('--only=')]

    def want(n):
        return not only or any(n.startswith(o) or o.startswith(n) for o in only)
    if want('ghost'):
        shoot('ghost', {'ghost'}, (1.5, 2.9, 1.25), (0, 0, 0.78), lens=45)
        shoot('ghost_side', {'ghost'}, (3.2, 0.2, 0.9), (0, 0, 0.78), lens=45)
        shoot('ghost_back', {'ghost'}, (-1.6, -2.8, 0.35), (0, 0, 0.6), lens=40)
    if want('hunter'):
        shoot('hunter', {'hunter'}, (1.5, 3.0, 1.45), (0, 0, 0.92), lens=45)
        shoot('hunter_back', {'hunter'}, (-1.9, -2.7, 1.6), (0, 0, 0.92), lens=45)
        shoot('hunter_face', {'hunter'}, (0.35, 0.9, 1.68), (0.02, 0.0, 1.55), lens=50)
        shoot('hunter_torso', {'hunter'}, (-0.5, 1.3, 1.25), (0.0, 0.0, 1.05), lens=50)
        shoot('hunter_side', {'hunter'}, (3.2, 0.6, 1.3), (0, 0.1, 0.92), lens=45)
    if want('relic'):
        shoot('relic', {'relic'}, (0.35, 0.62, 0.3), (0, 0, 0.165), lens=50)
    if want('revealer'):
        shoot('revealer', {'revealer'}, (0.62, 0.38, 0.25), (0, 0.1, 0.06), lens=50, floor_on=False)
        shoot('revealer_fp', {'revealer'}, (-0.13, -0.52, 0.21), (-0.13, 1.0, 0.08), lens=26, floor_on=False)
        shoot('revealer_front', {'revealer'}, (0.25, 0.85, 0.16), (0, 0.15, 0.07), lens=50, floor_on=False)
    if want('altar'):
        shoot('altar', {'altar_glow', 'relic'}, (1.3, 1.9, 1.5), (0, 0, 0.05), lens=40)
    if want('moody'):
        # in-game-ish: dim moonlit ambient + one warm candle, to judge readability on dark maps
        bg.inputs[1].default_value = 0.25
        shoot('moody', {'ghost', 'hunter', 'relic', 'altar_glow'}, (0.6, 5.2, 1.4), (0.6, 0, 0.85), lens=40,
              offsets={'ghost': (-0.75, 0, 0), 'hunter': (0.75, 0, 0), 'relic': (1.9, 0.3, 0),
                       'altar_glow': (-0.75, 0, 0)})
        for o in lights:
            o.data.energy *= 0.0
        candle = bpy.data.objects.new('candle', bpy.data.lights.new('candle', 'POINT'))
        candle.data.energy = 120
        candle.data.color = _lin('#ffb066')
        candle.location = (2.2, 2.0, 1.6)
        COLL.objects.link(candle)
        scene.render.filepath = os.path.join(PREVIEW_DIR, 'chars_moody.png')
        bpy.ops.render.render(write_still=True)
        print('[preview]', scene.render.filepath)
        bpy.data.objects.remove(candle, do_unlink=True)
        bg.inputs[1].default_value = 0.6
    if want('lineup'):
        shoot('lineup', {'ghost', 'hunter', 'relic', 'altar_glow'}, (0.6, 5.2, 1.4), (0.6, 0, 0.85), lens=40,
              offsets={'ghost': (-0.75, 0, 0), 'hunter': (0.75, 0, 0), 'relic': (1.9, 0.3, 0),
                       'altar_glow': (-0.75, 0, 0)})


def main():
    build_ghost()
    build_hunter()
    build_relic()
    build_revealer()
    build_altar_glow()
    export()
    report(verbose='--verbose' in ARGS)
    if '--preview' in ARGS:
        preview()


main()
