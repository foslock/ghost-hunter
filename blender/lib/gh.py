"""Ghost Hunter map toolkit. Run inside Blender in background mode.

Maps are authored as Python: static geometry is accumulated into spatial chunk
meshes, interactive props become small node hierarchies the client animates,
and everything gameplay-related (colliders, props, relic altars, spawns,
lights, environment) is written to a JSON sidecar next to the GLB.

Coordinates in this file are Blender's (X east, Y north, Z up). The JSON is
written in three.js space (Y up): three = (bx, bz, -by).
"""
import bpy
import json
import math
import os
import random
import sys

import numpy as np
from mathutils import Matrix, Vector

from . import tex as texlib

BLENDER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BLENDER_DIR)
BUILD_DIR = os.path.join(BLENDER_DIR, 'build')
MAP_GLB_DIR = os.path.join(ROOT, 'client', 'public', 'maps')
MAP_JSON_DIR = os.path.join(ROOT, 'shared', 'maps')

TAU = math.pi * 2


def script_args():
    return sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


# ---------------------------------------------------------------- transforms

def T(x=0.0, y=0.0, z=0.0):
    if isinstance(x, (tuple, list, Vector)):
        x, y, z = (tuple(x) + (0.0, 0.0, 0.0))[:3]
    return Matrix.Translation((x, y, z))


def RX(a):
    return Matrix.Rotation(a, 4, 'X')


def RY(a):
    return Matrix.Rotation(a, 4, 'Y')


def RZ(a):
    return Matrix.Rotation(a, 4, 'Z')


def S(x, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    return Matrix.Diagonal((x, y, z, 1.0))


def X(pos=(0, 0, 0), rz=0.0, rx=0.0, ry=0.0, s=None):
    m = T(pos) @ RZ(rz) @ RY(ry) @ RX(rx)
    if s is not None:
        m = m @ (S(*s) if isinstance(s, (tuple, list)) else S(s))
    return m


def to_three(p):
    return [round(p[0], 4), round(p[2], 4), round(-p[1], 4)]


def yaw_from_dir(fx, fy):
    """three.js camera yaw for a Blender XY facing direction."""
    return math.atan2(-fx, fy)


# ---------------------------------------------------------------- primitives
# Each returns (verts, faces, smooth_per_face). Faces are vertex-index tuples.

def _fix_convex(verts, faces, center=(0, 0, 0)):
    out = []
    c = Vector(center)
    for f in faces:
        a, b, d = Vector(verts[f[0]]), Vector(verts[f[1]]), Vector(verts[f[2]])
        n = (b - a).cross(d - a)
        cen = sum((Vector(verts[i]) for i in f), Vector()) / len(f)
        out.append(tuple(reversed(f)) if n.dot(cen - c) < 0 else tuple(f))
    return out


def prim_box(sx, sy, sz, bevel=0.0):
    a, b, c = sx / 2, sy / 2, sz / 2
    d = min(bevel, a * 0.45, b * 0.45, c * 0.45)
    if d <= 1e-5:
        v = [(x * a, y * b, z * c) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        idx = lambda x, y, z: ((x > 0) * 4 + (y > 0) * 2 + (z > 0))
        faces = []
        for axis in range(3):
            for s in (-1, 1):
                quad = []
                for u, w in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    p = [0, 0, 0]
                    p[axis] = s
                    p[(axis + 1) % 3] = u
                    p[(axis + 2) % 3] = w
                    quad.append(idx(*p))
                faces.append(tuple(quad))
        return v, _fix_convex(v, faces), [False] * 6
    verts = []
    key = {}
    for sxn in (-1, 1):
        for syn in (-1, 1):
            for szn in (-1, 1):
                for ax in range(3):
                    p = [sxn * (a - d), syn * (b - d), szn * (c - d)]
                    p[ax] = (sxn, syn, szn)[ax] * (a, b, c)[ax]
                    key[(sxn, syn, szn, ax)] = len(verts)
                    verts.append(tuple(p))
    faces = []
    for ax in range(3):
        for s in (-1, 1):
            o1, o2 = (ax + 1) % 3, (ax + 2) % 3
            quad = []
            for u, w in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                sg = [0, 0, 0]
                sg[ax] = s
                sg[o1] = u
                sg[o2] = w
                quad.append(key[(sg[0], sg[1], sg[2], ax)])
            faces.append(tuple(quad))
    for ax in range(3):  # edges parallel to axis `ax`
        o1, o2 = (ax + 1) % 3, (ax + 2) % 3
        for u in (-1, 1):
            for w in (-1, 1):
                q = []
                for s, which in ((-1, o1), (1, o1), (1, o2), (-1, o2)):
                    sg = [0, 0, 0]
                    sg[ax] = s
                    sg[o1] = u
                    sg[o2] = w
                    q.append(key[(sg[0], sg[1], sg[2], which)])
                faces.append(tuple(q))
    for sxn in (-1, 1):
        for syn in (-1, 1):
            for szn in (-1, 1):
                faces.append(tuple(key[(sxn, syn, szn, ax)] for ax in range(3)))
    return verts, _fix_convex(verts, faces), [False] * len(faces)


def prim_lathe(profile, n=16, cap_bottom=True, cap_top=True, smooth=True, arc=TAU):
    """Revolve a profile [(radius, z), ...] (bottom to top) around Z."""
    verts, faces, sm = [], [], []
    full = abs(arc - TAU) < 1e-6
    cols = n if full else n + 1
    for j in range(cols):
        ang = arc * j / n
        ca, sa = math.cos(ang), math.sin(ang)
        for r, z in profile:
            verts.append((r * ca, r * sa, z))
    rows = len(profile)
    for j in range(n):
        j2 = (j + 1) % cols
        for i in range(rows - 1):
            a = j * rows + i
            b = j2 * rows + i
            c = j2 * rows + i + 1
            d = j * rows + i + 1
            faces.append((a, b, c, d))
            sm.append(smooth)
    # caps get their own vertices so they shade flat
    if cap_bottom and profile[0][0] > 1e-5:
        base = len(verts)
        r, z = profile[0]
        for j in range(n):
            ang = arc * j / n
            verts.append((r * math.cos(ang), r * math.sin(ang), z))
        faces.append(tuple(base + j for j in reversed(range(n))))
        sm.append(False)
    if cap_top and profile[-1][0] > 1e-5:
        base = len(verts)
        r, z = profile[-1]
        for j in range(n):
            ang = arc * j / n
            verts.append((r * math.cos(ang), r * math.sin(ang), z))
        faces.append(tuple(base + j for j in range(n)))
        sm.append(False)
    return verts, faces, sm


def prim_cyl(r, h, n=12, r2=None, smooth=True, caps=True):
    r2 = r if r2 is None else r2
    prof = [(r, 0.0), (r2, h)]
    if r2 <= 1e-5:
        prof = [(r, 0.0), (1e-4, h)]
    v, f, s = prim_lathe(prof, n, caps, caps and r2 > 1e-5, smooth)
    return v, f, s


def prim_sphere(r, n=12, rings=None, smooth=True):
    rings = rings or max(4, n // 2)
    prof = [(max(r * math.sin(math.pi * i / rings), 1e-4), -r * math.cos(math.pi * i / rings)) for i in range(rings + 1)]
    return prim_lathe(prof, n, False, False, smooth)


def prim_torus(R, r, n=16, m=8, smooth=True, arc=TAU):
    verts, faces = [], []
    full = abs(arc - TAU) < 1e-6
    cols = n if full else n + 1
    for j in range(cols):
        a = arc * j / n
        for i in range(m):
            b = TAU * i / m
            rr = R + r * math.cos(b)
            verts.append((rr * math.cos(a), rr * math.sin(a), r * math.sin(b)))
    for j in range(n):
        j2 = (j + 1) % cols
        for i in range(m):
            i2 = (i + 1) % m
            faces.append((j * m + i, j2 * m + i, j2 * m + i2, j * m + i2))
    return verts, faces, [smooth] * len(faces)


def prim_prism(poly, h, smooth=False):
    """Extrude a CCW XY polygon upward by h."""
    k = len(poly)
    verts = [(x, y, 0.0) for x, y in poly] + [(x, y, h) for x, y in poly]
    faces = [tuple(reversed(range(k))), tuple(range(k, 2 * k))]
    for i in range(k):
        j = (i + 1) % k
        faces.append((i, j, k + j, k + i))
    # sides use split verts for flat shading via separate smooth flags
    return verts, faces, [False, False] + [smooth] * k


def prim_ico(r, subdiv=1, jitter=0.0, seed=0, squash=1.0):
    t = (1 + 5 ** 0.5) / 2
    vs = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
          (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    vs = [Vector(v).normalized() for v in vs]
    fs = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
          (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
          (8, 6, 7), (9, 8, 1)]
    for _ in range(subdiv):
        cache = {}

        def mid(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache:
                cache[k] = len(vs)
                vs.append(((vs[a] + vs[b]) / 2).normalized())
            return cache[k]
        nf = []
        for a, b, c in fs:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        fs = nf
    rng = random.Random(seed)
    verts = []
    for v in vs:
        k = r * (1 + rng.uniform(-jitter, jitter))
        verts.append((v.x * k, v.y * k, v.z * k * squash))
    return verts, _fix_convex(verts, fs), [False] * len(fs)


def prim_tube(points, r, n=6, smooth=True, caps=True):
    pts = [Vector(p) for p in points]
    verts, faces, sm = [], [], []
    for i, p in enumerate(pts):
        if i == 0:
            d = pts[1] - pts[0]
        elif i == len(pts) - 1:
            d = pts[-1] - pts[-2]
        else:
            d = (pts[i + 1] - pts[i - 1])
        d.normalize()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        u = d.cross(up).normalized()
        w = d.cross(u).normalized()
        for j in range(n):
            a = TAU * j / n
            verts.append(tuple(p + (u * math.cos(a) + w * math.sin(a)) * r))
    for i in range(len(pts) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((i * n + j, i * n + j2, (i + 1) * n + j2, (i + 1) * n + j))
            sm.append(smooth)
    if caps:
        faces.append(tuple(reversed(range(n))))
        sm.append(False)
        last = (len(pts) - 1) * n
        faces.append(tuple(last + j for j in range(n)))
        sm.append(False)
    return verts, faces, sm


def prim_sheet(w, h, nx=8, ny=8, two_sided=True):
    """Vertical sheet in the XZ plane hanging down from z=0 to z=-h, centred on x."""
    verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            verts.append((-w / 2 + w * i / nx, 0.0, -h * j / ny))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + nx + 1, a + nx + 2, a + 1))
    if two_sided:
        off = len(verts)
        verts += [(x, y + 0.004, z) for x, y, z in verts]
        faces += [tuple(off + i for i in reversed(f)) for f in faces[:]]
    return verts, faces, [True] * len(faces)


# ---------------------------------------------------------------- materials

class Mat:
    def __init__(self, name, color='#888888', rough=0.85, metal=0.0, emit=None, strength=1.0,
                 image=None, uv=1.0, uv_rot=0.0, map_id='map'):
        self.name = name
        self.uv = uv
        self.uv_rot = uv_rot
        self.textured = image is not None
        m = bpy.data.materials.new(name)
        try:
            m.use_nodes = True
        except Exception:
            pass
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        rgb = texlib.hex_rgb(color)
        lin = [srgb_to_linear(c) for c in rgb]
        bsdf.inputs['Base Color'].default_value = (*lin, 1.0)
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Metallic'].default_value = metal
        if emit:
            e = [srgb_to_linear(c) for c in texlib.hex_rgb(emit)]
            bsdf.inputs['Emission Color'].default_value = (*e, 1.0)
            bsdf.inputs['Emission Strength'].default_value = strength
        if image is not None:
            img = save_texture(f'{map_id}_{name}', image)
            node = nt.nodes.new('ShaderNodeTexImage')
            node.image = img
            nt.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
        m.diffuse_color = (*lin, 1.0)
        self.bmat = m


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def save_texture(name, arr):
    os.makedirs(os.path.join(BUILD_DIR, 'tex'), exist_ok=True)
    path = os.path.join(BUILD_DIR, 'tex', name + '.jpg')
    h, w, _ = arr.shape
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :3] = arr[::-1]
    img = bpy.data.images.new(name, w, h, alpha=False)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = 'JPEG'
    img.save()
    bpy.data.images.remove(img)
    loaded = bpy.data.images.load(path)
    loaded.name = name
    return loaded


# ---------------------------------------------------------------- geometry accumulator

class Geo:
    """Accumulates primitives into one mesh. `owner` receives colliders."""

    def __init__(self, owner=None, base=None):
        self.V, self.F, self.FM, self.FS = [], [], [], []
        self.stack = [Matrix.Identity(4)]
        self.owner = owner
        self.base = base or Matrix.Identity(4)

    @property
    def M(self):
        return self.stack[-1]

    class _Ctx:
        def __init__(self, g):
            self.g = g

        def __enter__(self):
            return self.g

        def __exit__(self, *a):
            self.g.stack.pop()

    def at(self, pos=(0, 0, 0), rz=0.0, rx=0.0, ry=0.0, s=None):
        self.stack.append(self.M @ X(pos, rz, rx, ry, s))
        return Geo._Ctx(self)

    def add(self, prim, mat, m=None):
        verts, faces, smooth = prim
        mm = self.M @ m if m is not None else self.M
        flip = mm.determinant() < 0
        base = len(self.V)
        for v in verts:
            self.V.append(tuple(mm @ Vector(v)))
        for f, s in zip(faces, smooth):
            f = tuple(i + base for i in f)
            self.F.append(tuple(reversed(f)) if flip else f)
            self.FM.append(mat)
            self.FS.append(s)
        return self

    # --- convenience primitives (sizes in metres) ---
    def box(self, c, s, mat, rz=0.0, bevel=0.0, rx=0.0, ry=0.0, col=False):
        self.add(prim_box(*s, bevel=bevel), mat, X(c, rz, rx, ry))
        if col:
            self.collide(c, s, rz)
        return self

    def cyl(self, base, r, h, mat, n=12, r2=None, smooth=True, caps=True, rx=0.0, ry=0.0, rz=0.0, col=False):
        self.add(prim_cyl(r, h, n, r2, smooth, caps), mat, X(base, rz, rx, ry))
        if col:
            c = (base[0], base[1], base[2] + h / 2)
            self.collide(c, (2 * r, 2 * r, h))
        return self

    def lathe(self, base, profile, mat, n=16, smooth=True, cap_bottom=True, cap_top=True, rx=0.0, ry=0.0, rz=0.0):
        return self.add(prim_lathe(profile, n, cap_bottom, cap_top, smooth), mat, X(base, rz, rx, ry))

    def sphere(self, c, r, mat, n=12, smooth=True, s=None, rx=0.0, ry=0.0, rz=0.0):
        return self.add(prim_sphere(r, n, None, smooth), mat, X(c, rz, rx, ry, s))

    def blob(self, c, r, mat, seed=0, jitter=0.18, subdiv=1, s=None, rz=0.0):
        return self.add(prim_ico(r, subdiv, jitter, seed), mat, X(c, rz, 0, 0, s))

    def torus(self, c, R, r, mat, n=16, m=8, rx=0.0, ry=0.0, rz=0.0, arc=TAU):
        return self.add(prim_torus(R, r, n, m, True, arc), mat, X(c, rz, rx, ry))

    def prism(self, base, poly, h, mat, rx=0.0, ry=0.0, rz=0.0):
        return self.add(prim_prism(poly, h), mat, X(base, rz, rx, ry))

    def tube(self, points, r, mat, n=6, caps=True):
        return self.add(prim_tube(points, r, n, True, caps), mat)

    def sheet(self, top_center, w, h, mat, nx=8, ny=8, rz=0.0, two_sided=True):
        return self.add(prim_sheet(w, h, nx, ny, two_sided), mat, X(top_center, rz))

    def collide(self, c, s, rz=0.0):
        """Register an axis-aligned collider (of the rotated box's bounds)."""
        m = self.base @ self.M @ X(c, rz)
        hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
        corners = [m @ Vector((x, y, z)) for x in (-hx, hx) for y in (-hy, hy) for z in (-hz, hz)]
        if self.owner is not None:
            self.owner.add_collider_points(corners)
        return self

    def empty(self):
        return not self.F

    def to_mesh(self, name):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.V, [], self.F)
        mats = []
        lookup = {}
        idx = []
        for mt in self.FM:
            if mt.name not in lookup:
                lookup[mt.name] = len(mats)
                mats.append(mt)
            idx.append(lookup[mt.name])
        for mt in mats:
            mesh.materials.append(mt.bmat)
        nf = len(self.F)
        mesh.polygons.foreach_set('material_index', np.array(idx, dtype=np.int32))
        mesh.polygons.foreach_set('use_smooth', np.array(self.FS, dtype=bool))
        mesh.update()
        # box-projected UVs, scaled per material
        nl = len(mesh.loops)
        loop_v = np.empty(nl, dtype=np.int32)
        mesh.loops.foreach_get('vertex_index', loop_v)
        totals = np.empty(nf, dtype=np.int32)
        mesh.polygons.foreach_get('loop_total', totals)
        normals = np.empty(nf * 3, dtype=np.float32)
        mesh.polygons.foreach_get('normal', normals)
        normals = normals.reshape(-1, 3)
        co = np.array(self.V, dtype=np.float64)
        face_of_loop = np.repeat(np.arange(nf), totals)
        n = normals[face_of_loop]
        p = co[loop_v]
        ax = np.argmax(np.abs(n), axis=1)
        sgn = np.sign(n[np.arange(nl), ax])
        sgn[sgn == 0] = 1
        u = np.where(ax == 2, p[:, 0], np.where(ax == 0, p[:, 1] * sgn, -p[:, 0] * sgn))
        v = np.where(ax == 2, p[:, 1], p[:, 2])
        scale = np.array([m.uv for m in mats])[np.array(idx)][face_of_loop]
        rot = np.array([m.uv_rot for m in mats])[np.array(idx)][face_of_loop]
        textured = np.array([m.textured for m in mats])[np.array(idx)][face_of_loop]
        cr, sr = np.cos(rot), np.sin(rot)
        # untextured faces get constant UVs so the exporter doesn't split vertices at UV seams
        uu = np.where(textured, (u * cr - v * sr) / scale, 0.0)
        vv = np.where(textured, (u * sr + v * cr) / scale, 0.0)
        if textured.any():
            uvl = mesh.uv_layers.new(name='UVMap')
            uvl.data.foreach_set('uv', np.stack([uu, vv], axis=1).ravel().astype(np.float32))
        mesh.validate(clean_customdata=False)
        mesh.update()
        return mesh


# ---------------------------------------------------------------- props

class Part:
    def __init__(self, prop, name, local, parent):
        self.prop = prop
        self.name = name
        self.local = local           # relative to parent part (or prop root)
        self.parent = parent
        self.geo = Geo(owner=prop, base=self.root_local())
        self.mesh = None

    def root_local(self):
        m = self.local
        p = self.parent
        while p is not None:
            m = p.local @ m
            p = p.parent
        return m


class Prop:
    """An interactive object. The client finds nodes named P_<id>_<part>."""

    def __init__(self, mb, pid, ptype, label, pos, rz, params):
        self.mb = mb
        self.id = pid
        self.type = ptype
        self.label = label
        self.pos = tuple(pos) + (0.0,) * (3 - len(pos))
        self.rz = rz
        self.params = dict(params or {})
        self.world = X(self.pos, rz)
        self.parts = {}
        self.local_colliders = []
        self.lights = []
        self.body = self.part('body').geo

    def part(self, name, pos=(0, 0, 0), rz=0.0, rx=0.0, ry=0.0, parent=None):
        """Create a named child node. Returns the Part (draw into part.geo, local to its origin)."""
        par = self.parts[parent] if isinstance(parent, str) else parent
        pt = Part(self, name, X(pos, rz, rx, ry), par)
        self.parts[name] = pt
        return pt

    def geo(self, name, pos=(0, 0, 0), rz=0.0, rx=0.0, ry=0.0, parent=None):
        return self.part(name, pos, rz, rx, ry, parent).geo

    def add_collider_points(self, pts):
        self.local_colliders.append(pts)

    def light(self, pos, color='#ffb066', intensity=1.0, distance=7.0, part=None):
        self.lights.append(dict(pos=tuple(pos), color=color, intensity=intensity, distance=distance, part=part))

    def flame(self, pos, size=1.0, parent=None, mat=None):
        """Teardrop flame node (P_<id>_flameN), flickered by the client."""
        k = sum(1 for n in self.parts if n.startswith('flame'))
        g = self.geo(f'flame{k}', pos, parent=parent)
        s = 0.05 * size
        g.lathe((0, 0, 0), [(s * 0.15, 0), (s * 0.7, s * 0.6), (s * 0.55, s * 1.4), (s * 0.001, s * 3.0)],
                mat or self.mb.flame_mat(), n=8)
        return g

    def world_matrix(self):
        return self.world

    def clone_into(self, other):
        for name, pt in self.parts.items():
            parent = other.parts[pt.parent.name] if pt.parent else None
            if name == 'body':
                np_ = other.parts['body']
            else:
                np_ = Part(other, name, pt.local.copy(), parent)
                other.parts[name] = np_
            np_.shared_from = pt
        other.local_colliders = [list(c) for c in self.local_colliders]
        other.lights = [dict(l) for l in self.lights]


# ---------------------------------------------------------------- map builder

class MapBuilder:
    def __init__(self, map_id, name, chunk=14.0, seed=7):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.id = map_id
        self.name = name
        self.chunk = chunk
        self.rng = random.Random(seed)
        self.mats = {}
        self.chunks = {}
        self.colliders = []
        self.props = []
        self.prop_cache = {}
        self.prop_counts = {}
        self.flag_points = []
        self.spawns = {'hunter': [], 'ghost': []}
        self.penalty = {'spawns': [], 'label': 'Penalty Box'}
        self.lights = []
        self.env_data = {}
        self.preview_views = []
        self._flame = None

    # --- materials ---
    def mat(self, name, color='#888888', rough=0.85, metal=0.0, emit=None, strength=1.0, image=None, uv=1.0, uv_rot=0.0):
        if name in self.mats:
            return self.mats[name]
        m = Mat(name, color, rough, metal, emit, strength, image, uv, uv_rot, self.id)
        self.mats[name] = m
        return m

    def flame_mat(self):
        if self._flame is None:
            self._flame = self.mat('flame', '#ffcf7a', rough=1.0, emit='#ffb347', strength=6.0)
        return self._flame

    # --- static geometry ---
    def static(self, x, y):
        key = (math.floor(x / self.chunk), math.floor(y / self.chunk))
        g = self.chunks.get(key)
        if g is None:
            g = self.chunks[key] = Geo(owner=self)
        return g

    def put(self, prefab, pos, rz=0.0, **kw):
        """Draw a prefab function (geo, **kw) into static geometry at pos/rotation."""
        g = self.static(pos[0], pos[1])
        with g.at(pos, rz):
            prefab(g, **kw)
        return g

    def box(self, c, s, mat, rz=0.0, bevel=0.0, col=True):
        return self.static(c[0], c[1]).box(c, s, mat, rz=rz, bevel=bevel, col=col)

    def add_collider_points(self, pts):
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]
        self.colliders.append((min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)))

    def collider(self, mn, mx):
        self.colliders.append((mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]))

    def floor(self, x0, y0, x1, y1, mat, z=0.0, thick=0.3):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        return self.box((cx, cy, z - thick / 2), (abs(x1 - x0), abs(y1 - y0), thick), mat)

    def wall(self, a, b, mat, h=4.0, t=0.3, openings=(), z=0.0, lower=None, mat_back=None, trim=None):
        """Axis-aligned wall from a to b (XY). openings: [(offset_from_a, width, height, sill)].
        lower: (height, material) for a wainscot band. mat_back: material for the +normal half.
        trim: (height, depth, material) baseboard on both sides."""
        ax, ay = a
        bx, by = b
        horizontal = abs(by - ay) < 1e-6
        length = abs(bx - ax) if horizontal else abs(by - ay)
        sign = 1 if (bx - ax if horizontal else by - ay) >= 0 else -1
        ops = sorted(openings, key=lambda o: o[0])
        segs = []  # (start, end, z0, z1)
        cursor = 0.0
        for off, w, oh, sill in ops:
            s0, s1 = off - w / 2, off + w / 2
            if s0 > cursor:
                segs.append((cursor, s0, 0, h))
            if sill > 0:
                segs.append((s0, s1, 0, sill))
            if oh < h:
                segs.append((s0, s1, oh, h))
            cursor = s1
        if cursor < length:
            segs.append((cursor, length, 0, h))

        def piece(s0, s1, z0, z1, m, toff=0.0, tt=t):
            mid = (s0 + s1) / 2 * sign
            ln = s1 - s0
            if horizontal:
                c = (ax + mid, ay + toff, z + (z0 + z1) / 2)
                size = (ln, tt, z1 - z0)
            else:
                c = (ax + toff, ay + mid, z + (z0 + z1) / 2)
                size = (tt, ln, z1 - z0)
            self.static(c[0], c[1]).box(c, size, m, col=False)

        for s0, s1, z0, z1 in segs:
            if s1 - s0 < 1e-4 or z1 - z0 < 1e-4:
                continue
            bands = [(z0, z1, mat)]
            if lower and z0 < lower[0] < z1:
                bands = [(z0, lower[0], lower[1]), (lower[0], z1, mat)]
            elif lower and z1 <= lower[0]:
                bands = [(z0, z1, lower[1])]
            for bz0, bz1, m in bands:
                if mat_back is not None:
                    piece(s0, s1, bz0, bz1, m, -t / 4, t / 2)
                    piece(s0, s1, bz0, bz1, mat_back if m is mat else m, t / 4, t / 2)
                else:
                    piece(s0, s1, bz0, bz1, m)
            # collider for the whole segment (window openings are sealed below)
            mid = (s0 + s1) / 2 * sign
            ln = s1 - s0
            if horizontal:
                self.collider((ax + mid - ln / 2, ay - t / 2, z + z0), (ax + mid + ln / 2, ay + t / 2, z + z1))
            else:
                self.collider((ax - t / 2, ay + mid - ln / 2, z + z0), (ax + t / 2, ay + mid + ln / 2, z + z1))
            if trim and z0 == 0:
                th, td, tm = trim
                for side in (-1, 1):
                    piece(s0, s1, 0, th, tm, side * (t / 2 + td / 2), td)
        self.seal_windows(a, b, ops, h, t, z)

    def seal_windows(self, a, b, openings, h, t, z=0.0):
        """Invisible colliders across window openings (sill >= 0.5 m) so nobody can climb out.
        Lower sills are treated as door thresholds and left open."""
        ax, ay = a
        bx, by = b
        horizontal = abs(by - ay) < 1e-6
        sign = 1 if (bx - ax if horizontal else by - ay) >= 0 else -1
        for off, w, oh, sill in openings:
            if sill < 0.5:
                continue
            mid = off * sign
            if horizontal:
                self.collider((ax + mid - w / 2, ay - t / 2, z + sill), (ax + mid + w / 2, ay + t / 2, z + min(oh, h)))
            else:
                self.collider((ax - t / 2, ay + mid - w / 2, z + sill), (ax + t / 2, ay + mid + w / 2, z + min(oh, h)))

    def stairs(self, start, direction, width, steps, rise, run, mat, z=0.0, side_mat=None):
        """Straight stair: start is the centre of the bottom edge, direction 'N','S','E','W'."""
        dx, dy = {'N': (0, 1), 'S': (0, -1), 'E': (1, 0), 'W': (-1, 0)}[direction]
        for i in range(steps):
            top = z + rise * (i + 1)
            cx = start[0] + dx * (run * i + run / 2)
            cy = start[1] + dy * (run * i + run / 2)
            if dx:
                size = (run, width, top - z)
            else:
                size = (width, run, top - z)
            self.box((cx, cy, z + (top - z) / 2), size, mat, bevel=0.01)

    # --- props ---
    def place(self, prefab, ptype, label, pos, rz=0.0, params=None, key=None, pid=None, **kw):
        if pid is None:
            n = self.prop_counts.get(ptype, 0) + 1
            self.prop_counts[ptype] = n
            pid = f'{ptype}{n}'
        p = Prop(self, pid, ptype, label, pos, rz, params)
        if key and key in self.prop_cache:
            cached = self.prop_cache[key]
            cached.clone_into(p)
            # keep the prefab's archetype defaults (axis, dir, sound...) unless overridden here
            p.params = {**cached.params, **(params or {})}
        else:
            prefab(p, **kw)
            if key:
                self.prop_cache[key] = p
        self.props.append(p)
        return p

    # --- gameplay markers ---
    def flag_point(self, pos, rz=0.0, prefab=None, **kw):
        """A relic altar. pos is floor position; the relic rests at the returned height."""
        top = 1.0
        if prefab is not None:
            g = self.static(pos[0], pos[1])
            with g.at(pos, rz):
                top = prefab(g, **kw) or top
        self.flag_points.append((pos[0], pos[1], pos[2] + top))
        return self

    def spawn(self, role, pos, face=(0, 1)):
        self.spawns[role].append(to_three(pos) + [round(yaw_from_dir(*face), 4)])

    def penalty_spawn(self, pos):
        self.penalty['spawns'].append(to_three(pos))

    def light(self, pos, color='#ffb066', intensity=1.0, distance=8.0, flicker=0.0):
        self.lights.append(dict(pos=to_three(pos), color=color, intensity=intensity, distance=distance, flicker=flicker))

    def env(self, **kw):
        self.env_data.update(kw)

    def preview(self, pos, look, lens=22, name=None):
        self.preview_views.append((pos, look, lens, name))

    # --- output ---
    def _build_objects(self):
        scene = bpy.context.scene
        coll = scene.collection
        for i, (key, g) in enumerate(sorted(self.chunks.items())):
            if g.empty():
                continue
            mesh = g.to_mesh(f'S_{key[0]}_{key[1]}')
            obj = bpy.data.objects.new(f'S_{key[0]}_{key[1]}'.replace('-', 'm'), mesh)
            coll.objects.link(obj)
        for p in self.props:
            root = bpy.data.objects.new(f'P_{p.id}', None)
            root.empty_display_size = 0.3
            root.matrix_basis = p.world
            coll.objects.link(root)
            nodes = {}
            # parents before children
            order = []
            seen = set()

            def visit(pt):
                if pt.name in seen:
                    return
                if pt.parent is not None:
                    visit(pt.parent)
                seen.add(pt.name)
                order.append(pt)
            for pt in p.parts.values():
                visit(pt)
            for pt in order:
                node = bpy.data.objects.new(f'P_{p.id}_{pt.name}', None)
                node.empty_display_size = 0.1
                node.parent = nodes[pt.parent.name] if pt.parent else root
                node.matrix_basis = pt.local
                coll.objects.link(node)
                nodes[pt.name] = node
                src = getattr(pt, 'shared_from', None)
                mesh = None
                if src is not None:
                    mesh = src.mesh
                elif not pt.geo.empty():
                    mesh = pt.geo.to_mesh(f'P_{p.id}_{pt.name}_mesh')
                pt.mesh = mesh
                if mesh is not None:
                    mo = bpy.data.objects.new(f'P_{p.id}_{pt.name}_m', mesh)
                    mo.parent = node
                    coll.objects.link(mo)
            for pts in p.local_colliders:
                self.add_collider_points([p.world @ v for v in pts])

    def _json(self):
        props = []
        for p in self.props:
            for l in p.lights:
                wp = p.world @ Vector(l['pos'])
                self.lights.append(dict(pos=to_three(wp), color=l['color'], intensity=l['intensity'],
                                        distance=l['distance'], prop=p.id, part=l['part']))
            props.append(dict(id=p.id, type=p.type, label=p.label, pos=to_three(p.pos), rot=round(p.rz, 4),
                              params=p.params))
        cols = []
        for c in self.colliders:
            mn = (c[0], c[2], -c[4])
            mx = (c[3], c[5], -c[1])
            cols.append([round(v, 3) for v in (*mn, *mx)])
        xs = [c[0] for c in cols] + [c[3] for c in cols]
        zs = [c[2] for c in cols] + [c[5] for c in cols]
        data = dict(
            id=self.id, name=self.name, glb=f'/maps/{self.id}.glb',
            bounds=[round(min(xs), 2), round(min(zs), 2), round(max(xs), 2), round(max(zs), 2)],
            env=self.env_data,
            spawns=self.spawns,
            penalty=self.penalty,
            flagPoints=[dict(id=f'altar{i + 1}', pos=to_three(p)) for i, p in enumerate(self.flag_points)],
            lights=self.lights,
            props=props,
            colliders=cols,
        )
        return data

    def _set_sidedness(self):
        """Closed geometry renders single-sided (back faces culled), so hidden faces such as a rug's
        underside or a pane's back can't z-fight with the surface they rest on. Connected shells
        with open edges (cups, sheets, open cylinders) get a double-sided copy of their material,
        so only they pay for it."""
        for m in bpy.data.materials:
            m.use_backface_culling = True
        clones = {}

        def double(mat):
            c = clones.get(mat.name)
            if c is None:
                c = mat.copy()
                c.name = mat.name + '_2s'
                c.use_backface_culling = False
                clones[mat.name] = c
            return c

        for me in {o.data for o in bpy.context.scene.objects if o.type == 'MESH'}:
            if not me.polygons or not me.materials:
                continue
            nv = len(me.vertices)
            co = np.empty(nv * 3)
            me.vertices.foreach_get('co', co)
            _, weld = np.unique(np.round(co.reshape(-1, 3), 4), axis=0, return_inverse=True)
            weld = weld.ravel()
            nl = len(me.loops)
            lv = np.empty(nl, dtype=np.int64)
            me.loops.foreach_get('vertex_index', lv)
            lv = weld[lv]
            np_ = len(me.polygons)
            start = np.empty(np_, dtype=np.int64)
            total = np.empty(np_, dtype=np.int64)
            me.polygons.foreach_get('loop_start', start)
            me.polygons.foreach_get('loop_total', total)
            nxt = np.arange(nl) + 1
            nxt[start + total - 1] = start  # wrap each polygon's last loop to its first
            a, b = lv, lv[nxt]
            keys = np.minimum(a, b) * (nv + 1) + np.maximum(a, b)
            _, inv, counts = np.unique(keys, return_inverse=True, return_counts=True)
            boundary = counts[inv.ravel()] == 1
            if not boundary.any():
                continue
            # connected shells over welded vertices (label propagation with pointer jumping)
            label = np.arange(weld.max() + 1)
            for _ in range(200):
                la, lb = label[a], label[b]
                m = np.minimum(la, lb)
                before = label.copy()
                np.minimum.at(label, a, m)
                np.minimum.at(label, b, m)
                label = label[label]
                if np.array_equal(label, before):
                    break
            open_shells = np.unique(label[a[boundary]])
            face_shell = label[lv[start]]
            open_face = np.isin(face_shell, open_shells)
            mi = np.empty(np_, dtype=np.int64)
            me.polygons.foreach_get('material_index', mi)
            slot = {}
            for idx in np.unique(mi[open_face]):
                if idx >= len(me.materials) or me.materials[idx] is None:
                    continue
                me.materials.append(double(me.materials[idx]))
                slot[idx] = len(me.materials) - 1
            for idx, new in slot.items():
                mi[open_face & (mi == idx)] = new
            me.polygons.foreach_set('material_index', mi.astype(np.int32))
            me.update()
        if '--sides' in script_args():
            print(f'[sides] double-sided copies: {", ".join(sorted(clones))}')

    def finish(self):
        args = script_args()
        self._build_objects()
        self._set_sidedness()
        from . import zfight
        if '--no-zfix' not in args:
            print(f'[gh] lifted {zfight.fix()} coplanar faces to stop z-fighting')
        if '--zcheck' in args:
            zfight.report(self.id, BUILD_DIR)
        os.makedirs(MAP_GLB_DIR, exist_ok=True)
        os.makedirs(MAP_JSON_DIR, exist_ok=True)
        glb = os.path.join(MAP_GLB_DIR, f'{self.id}.glb')
        bpy.ops.export_scene.gltf(
            filepath=glb, export_format='GLB', export_apply=False, export_yup=True,
            export_lights=False, export_cameras=False, use_selection=False, export_animations=False,
            export_extras=False, export_image_format='AUTO', export_materials='EXPORT',
            export_meshopt_compression_enable='--no-compress' not in args,  # client decodes EXT_meshopt_compression
        )
        data = self._json()
        with open(os.path.join(MAP_JSON_DIR, f'{self.id}.json'), 'w') as f:
            json.dump(data, f, separators=(',', ':'))
        print(f'[gh] exported {self.id}: {len(data["colliders"])} colliders, {len(data["props"])} props, '
              f'{len(data["flagPoints"])} altars, {len(data["lights"])} lights, '
              f'{os.path.getsize(glb) / 1e6:.2f} MB')
        if '--preview' in args or '--blend' in args:
            from . import preview
            preview.render(self, data, args)
