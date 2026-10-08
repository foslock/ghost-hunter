"""The Waiting Room: a small Victorian spirit-railway waiting hall where players gather between rounds.

Everyone can walk around, try snaps and whistles, haunt the props and practise with the revealer.
Standing on the Hunters or Ghosts medallion switches team. The north wall has a departure door for
each map (the selected one lights up in-game) and the south wall holds the room's notice board,
which the client draws live.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib import gh, prefabs as pf, tex  # noqa: E402

PI = math.pi
HALF = PI / 2
W, D, H = 12.0, 9.0, 5.5          # half-width (x), half-depth (y), ceiling height

m = gh.MapBuilder('lobby', 'The Waiting Room', chunk=12.0)

# ------------------------------------------------------------------ palette
floor = m.mat('floor', image=tex.wood_planks(base='#5b3b26', dark='#3a2417', light='#7b5536', planks=7, seed=31), uv=3.2)
paper = m.mat('wallpaper', image=tex.wallpaper(bg='#1f3833', fg='#2d5048', stripe='#172b27', seed=32, motifs=3), uv=2.2)
wains = m.mat('wainscot', image=tex.boards(base='#4a2c1c', dark='#2a170e', boards_n=8, seed=33, wear=0.05, weathered='#5a3a26'), uv=2.0)
plaster = m.mat('plaster', image=tex.noise_tint(base='#d8cdb4', amount=0.08, seed=34), uv=3.0)
walnut = m.mat('walnut', '#4a2c1c', rough=0.65)
walnut_dk = m.mat('walnut_dark', '#2c1a10', rough=0.7)
brass = m.mat('brass', '#b8913f', rough=0.35, metal=1.0)
iron = m.mat('iron', '#2a2a2e', rough=0.6, metal=0.7)
glass = m.mat('window_glass', '#20304e', rough=0.1, emit='#3d5a96', strength=0.8)
velvet = m.mat('velvet', image=tex.fabric(base='#5a1d26', seed=35), uv=1.0)
teal_cloth = m.mat('teal_velvet', image=tex.fabric(base='#1f4f4a', seed=36), uv=1.0)
rug_red = m.mat('rug_red', image=tex.fabric(base='#6a2a2a', seed=37, pattern='border', pattern_col='#c9a24a'), uv=4.0)
cream = m.mat('cream', '#e9dfc8', rough=0.8)
sheet = m.mat('dust_sheet', '#d9d6cf', rough=0.95)
wax = m.mat('wax', '#efe6d0', rough=0.6)
face = m.mat('clockface', '#ece2c6', rough=0.6)
black = m.mat('black', '#121012', rough=0.6)
leaf = [m.mat('leaf_a', '#3d5a33'), m.mat('leaf_b', '#4c6b39')]
bark = m.mat('bark', '#3b2b20')
terracotta = m.mat('terracotta', '#9a5a3a', rough=0.9)
amber = m.mat('amber_glow', '#ffb36b', rough=0.5, emit='#ff9a3c', strength=0.7)
teal_glow = m.mat('teal_glow', '#9fe8ff', rough=0.5, emit='#58d6e8', strength=0.7)
bulb_mat = m.mat('bulb', '#fff2d0', emit='#ffd38a', strength=5.0)
sea = m.mat('sea', '#2d4a5a')
land = m.mat('land', '#a08850')
balloon_mats = [m.mat('balloon_red', '#b8322e', rough=0.35), m.mat('balloon_teal', '#3aa7a0', rough=0.35),
                m.mat('balloon_cream', '#efe2c4', rough=0.35)]
leather = m.mat('leather', '#5a3420', rough=0.7)


# ------------------------------------------------------------------ helpers
def text_prim(text, size, extrude=0.015):
    """3D lettering in the XY plane facing +Z, centred on the origin."""
    cu = bpy.data.curves.new('txt', 'FONT')
    cu.body = text
    cu.size = size
    cu.extrude = extrude
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    ob = bpy.data.objects.new('txt', cu)
    bpy.context.scene.collection.objects.link(ob)
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    verts = [tuple(v.co) for v in me.vertices]
    faces = [tuple(p.vertices) for p in me.polygons]
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bpy.data.meshes.remove(me)
    return verts, faces, [False] * len(faces)


def sign_text(g, text, pos, size, mat, rz=0.0):
    """Upright lettering facing -Y (rotate with rz)."""
    g.add(text_prim(text, size), mat, gh.X(pos, rz, rx=HALF))


def picture(path, center, w, h, rz=0.0):
    """A canvas with an image mapped once across it (separate object so it gets its own UVs)."""
    img = bpy.data.images.load(path)
    mat = bpy.data.materials.new(f'pic_{os.path.basename(path)}')
    try:
        mat.use_nodes = True
    except Exception:
        pass
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    node = nt.nodes.new('ShaderNodeTexImage')
    node.image = img
    nt.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.55
    # a little self-illumination so the night-time thumbnails read on the wall
    nt.links.new(node.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 0.35
    me = bpy.data.meshes.new(f'pic_{os.path.basename(path)}')
    hw, hh = w / 2, h / 2
    me.from_pydata([(-hw, 0, -hh), (hw, 0, -hh), (hw, 0, hh), (-hw, 0, hh)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name='UVMap')
    for i, (u, v) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = (u, v)
    me.materials.append(mat)
    ob = bpy.data.objects.new(f'pic_{os.path.basename(path).split(".")[0]}', me)
    ob.matrix_basis = gh.X(center, rz)
    bpy.context.scene.collection.objects.link(ob)


def bench(g, length=2.4):
    for sx in (-1, 1):
        g.box((sx * (length / 2 - 0.15), 0, 0.22), (0.08, 0.5, 0.44), iron)
        g.box((sx * (length / 2 - 0.15), 0.22, 0.65), (0.08, 0.06, 0.5), iron)
    for k in range(4):
        g.box((0, -0.18 + k * 0.12, 0.47), (length, 0.1, 0.04), walnut, bevel=0.008)
    for k in range(3):
        g.box((0, 0.25, 0.62 + k * 0.13), (length, 0.035, 0.09), walnut, bevel=0.008, rx=-0.12)
    g.collide((0, 0, 0.4), (length, 0.6, 0.8))


def trolley(g):
    g.box((0, 0, 0.32), (1.6, 0.8, 0.05), iron)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.cyl((sx * 0.62, sy * 0.36, 0.0), 0.11, 0.06, black, n=10, rx=HALF, rz=0)
        g.tube([(sx * 0.8, -0.38, 0.32), (sx * 0.8, -0.38, 1.0), (sx * 0.8, 0.38, 1.0), (sx * 0.8, 0.38, 0.32)], 0.018, iron, n=5)
    g.collide((0, 0, 0.5), (1.7, 0.85, 1.0))


def medallion(g, ring, inner, glow):
    """Team pad set into the floor (top at ~3 cm)."""
    g.cyl((0, 0, 0), 1.85, 0.02, ring, n=48)
    g.cyl((0, 0, 0.02), 1.6, 0.008, inner, n=48)
    g.torus((0, 0, 0.03), 1.3, 0.025, glow, n=48, m=4)
    g.torus((0, 0, 0.03), 0.55, 0.02, glow, n=32, m=4)
    for k in range(8):
        a = k * PI / 4
        g.box((math.cos(a) * 0.93, math.sin(a) * 0.93, 0.03), (0.7, 0.05, 0.012), ring, rz=a)


def coat_rack(g):
    g.lathe((0, 0, 0), [(0.25, 0), (0.22, 0.04), (0.03, 0.08), (0.025, 1.75), (0.04, 1.8)], walnut_dk, n=8)
    for k in range(4):
        a = k * PI / 2 + 0.3
        g.tube([(0, 0, 1.6), (math.cos(a) * 0.18, math.sin(a) * 0.18, 1.72)], 0.015, brass, n=4)
    g.cyl((0.15, 0, 1.66), 0.2, 0.02, black, n=12)       # a hunter's hat
    g.cyl((0.15, 0, 1.68), 0.1, 0.14, black, n=12)
    g.collide((0, 0, 0.9), (0.4, 0.4, 1.8))


def revealer_case(g):
    """Glass display case of spare revealers."""
    g.box((0, 0, 0.45), (1.4, 0.55, 0.9), walnut, bevel=0.015)
    g.box((0, 0, 1.2), (1.3, 0.48, 0.6), glass)
    g.box((0, 0, 1.52), (1.42, 0.58, 0.05), walnut)
    for k in range(3):
        x = -0.4 + k * 0.4
        g.cyl((x, 0, 1.0), 0.05, 0.28, brass, n=10, rx=HALF, rz=HALF * 0.6)
        g.lathe((x, 0.15, 1.0), [(0.05, 0), (0.09, 0.08)], brass, n=10, rx=-HALF)
    g.collide((0, 0, 0.78), (1.42, 0.58, 1.56))


def draped(g, w, d, h, seed):
    """Furniture under a dust sheet."""
    g.box((0, 0, h / 2), (w, d, h), sheet, bevel=0.08)
    g.blob((0, 0, h), max(w, d) * 0.42, sheet, seed=seed, jitter=0.12, s=(w / max(w, d), d / max(w, d), 0.35))
    for sx in (-1, 1):
        g.box((sx * w / 2, 0, h * 0.35), (0.02, d * 0.9, h * 0.7), sheet)
    g.collide((0, 0, h / 2), (w, d, h))


def side_table(g):
    g.lathe((0, 0, 0), [(0.25, 0), (0.22, 0.03), (0.05, 0.1), (0.04, 0.68), (0.08, 0.72)], walnut_dk, n=10)
    g.cyl((0, 0, 0.72), 0.36, 0.04, walnut, n=20)
    g.collide((0, 0, 0.38), (0.72, 0.72, 0.76))


def board_frame(g, w, h, wood=None, inset=None):
    """A wall-hung frame facing -Y (origin at its centre); the client draws the board inside it."""
    wood = wood or walnut
    for sx in (-1, 1):
        g.box((sx * (w / 2 + 0.07), 0, 0), (0.14, 0.1, h + 0.28), wood, bevel=0.015)
    for sz in (-1, 1):
        g.box((0, 0, sz * (h / 2 + 0.07)), (w + 0.28, 0.1, 0.14), wood, bevel=0.015)
    g.box((0, 0.04, 0), (w, 0.03, h), inset or walnut_dk)
    for sx in (-1, 1):  # brass picture-rail hooks and chains
        g.sphere((sx * w * 0.3, 0.02, h / 2 + 0.55), 0.04, brass, n=8)
        g.tube([(sx * w * 0.3, -0.01, h / 2 + 0.53), (sx * w * 0.36, -0.03, h / 2 + 0.16)], 0.008, brass, n=3, caps=False)


def easel(g, w, h):
    """A-frame chalkboard easel facing -Y; origin on the floor. The client draws the chalk."""
    bz = 0.75 + h / 2
    for sx in (-1, 1):
        g.tube([(sx * (w / 2 - 0.05), -0.12, 0.0), (sx * (w / 2 - 0.12), 0.0, bz + h / 2 + 0.25)], 0.035, walnut, n=6)
    g.tube([(0, 0.55, 0.0), (0, 0.05, bz + h / 2 + 0.2)], 0.03, walnut, n=6)
    g.box((0, -0.06, bz - h / 2 - 0.05), (w + 0.1, 0.12, 0.06), walnut)   # chalk ledge
    for sx in (-1, 1):
        g.box((sx * (w / 2 + 0.03), -0.02, bz), (0.06, 0.06, h + 0.12), walnut_dk)
    for sz in (-1, 1):
        g.box((0, -0.02, bz + sz * (h / 2 + 0.03)), (w + 0.12, 0.06, 0.06), walnut_dk)
    g.box((0, 0.0, bz), (w, 0.03, h), m.mat('slate', '#1d2422', rough=0.9))
    g.box((-0.3, -0.07, bz - h / 2 - 0.0), (0.09, 0.015, 0.015), cream)   # a stick of chalk
    g.collide((0, 0.15, 1.0), (w + 0.2, 0.9, 2.0))


# ------------------------------------------------------------------ props
def station_clock(p):
    """Hanging station clock (one face); origin at the ceiling."""
    b = p.body
    b.cyl((0, 0, -0.6), 0.02, 0.6, iron, n=6)
    b.cyl((0, 0.02, -1.05), 0.48, 0.1, brass, n=32, rx=HALF)
    b.cyl((0, -0.085, -1.05), 0.42, 0.02, face, n=32, rx=HALF)
    for k in range(12):
        a = k * PI / 6
        b.box((math.sin(a) * 0.36, -0.1, -1.05 + math.cos(a) * 0.36), (0.02, 0.01, 0.07), black, ry=-a)
    b.sphere((0, -0.11, -1.05), 0.025, brass, n=8)
    hr = p.geo('hour', (0, -0.105, -1.05))
    hr.box((0, 0, 0.1), (0.04, 0.008, 0.22), black)
    mn = p.geo('minute', (0, -0.112, -1.05))
    mn.box((0, 0, 0.15), (0.025, 0.008, 0.32), black)
    p.params.setdefault('axis', 'z')
    p.params.setdefault('sound', 'chime')


def sconce(p):
    """Gas wall lamp; origin on the wall, lamp facing -Y."""
    b = p.body
    b.box((0, 0.0, 0), (0.14, 0.04, 0.24), brass, bevel=0.01)
    b.tube([(0, -0.02, -0.04), (0, -0.18, 0.02), (0, -0.2, 0.1)], 0.015, brass, n=5)
    b.lathe((0, -0.2, 0.08), [(0.03, 0), (0.09, 0.08), (0.1, 0.2), (0.04, 0.26)], glass, n=10, cap_top=False)
    bl = p.geo('bulb0', (0, -0.2, 0.15))
    bl.sphere((0, 0, 0), 0.05, bulb_mat, n=10)
    p.light((0, -0.3, 0.15), '#ffcf8a', 1.1, 7.0, part='bulb0')
    p.params.setdefault('sound', 'buzz')


def desk_bell(p):
    """Small brass bell on a bracket above the ticket counter; origin at the axle."""
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.lathe((0, 0, -0.26), [(0.12, 0), (0.11, 0.02), (0.07, 0.12), (0.06, 0.2), (0.03, 0.24), (0.005, 0.26)], brass, n=16)
    g.sphere((0, 0, -0.24), 0.025, brass, n=8)
    p.body.box((0, 0.2, 0), (0.04, 0.4, 0.04), iron)
    p.params.setdefault('axis', 'x')
    p.params.setdefault('tone', 880)
    p.params.setdefault('sound', 'bell')


def balloons(p):
    """A bunch of lost balloons tied to a bench."""
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    for k, (dx, dy, dz) in enumerate(((0, 0, 1.75), (0.22, 0.08, 1.6), (-0.2, 0.1, 1.62))):
        g.tube([(0, 0, 0.0), (dx * 0.5, dy * 0.5, dz * 0.5), (dx, dy, dz - 0.2)], 0.004, cream, n=3, caps=False)
        g.sphere((dx, dy, dz), 0.17, balloon_mats[k], n=14, s=(1, 1, 1.18))
    p.params.setdefault('amp', 0.06)
    p.params.setdefault('sound', 'squeak')


def trunk(p, s=1.0, mat=None):
    pv = p.part('pivot', (0, 0, 0))
    g = pv.geo
    g.box((0, 0, 0.22 * s), (0.9 * s, 0.5 * s, 0.44 * s), mat or leather, bevel=0.02)
    for sx in (-1, 1):
        g.box((sx * 0.3 * s, 0, 0.22 * s), (0.04, 0.52 * s, 0.46 * s), brass)
    g.box((0, -0.26 * s, 0.38 * s), (0.12, 0.02, 0.08), brass)
    p.body.collide((0, 0, 0.22 * s), (0.9 * s, 0.5 * s, 0.44 * s))
    p.params.setdefault('sound', 'thud')


# ------------------------------------------------------------------ shell
m.floor(-W, -D, W, D, floor)
m.box((0, 0, H + 0.15), (2 * W, 2 * D, 0.3), plaster)
for x in (-6, 0, 6):  # ceiling beams
    m.box((x, 0, H - 0.12), (0.3, 2 * D, 0.24), walnut_dk, col=False)
for y in (-4.5, 4.5):
    m.box((0, y, H - 0.1), (2 * W, 0.24, 0.2), walnut_dk, col=False)

win_ops = [(D - 4.0, 1.6, 3.6, 1.0), (D + 4.0, 1.6, 3.6, 1.0)]
m.wall((-W, -D), (-W, D), paper, h=H, openings=win_ops, lower=(1.15, wains), trim=(0.16, 0.03, walnut_dk))
m.wall((W, -D), (W, D), paper, h=H, openings=win_ops, lower=(1.15, wains), trim=(0.16, 0.03, walnut_dk))
m.wall((-W, D), (W, D), paper, h=H, lower=(1.15, wains), trim=(0.16, 0.03, walnut_dk))
m.wall((-W, -D), (W, -D), paper, h=H, lower=(1.15, wains), trim=(0.16, 0.03, walnut_dk))
# night sky beyond the windows
for sx in (-1, 1):
    m.box((sx * (W + 1.2), 0, H / 2), (0.1, 2 * D, H), m.mat('night', '#0b1222', emit='#0e1a33', strength=0.6), col=False)
    for y in (-4.0, 4.0):
        m.put(pf.window, (sx * W, y, 1.0), rz=HALF, w=1.6, h=2.6, frame=walnut, glass=glass)
        m.place(pf.curtains, 'cloth', 'Curtains', (sx * (W - 0.18), y, 3.75), rz=-sx * HALF, key='curtain',
                w=1.8, h=2.8, fabric=velvet, rod=brass)
# crown moulding
for (a, b) in (((-W, D - 0.17), (W, D - 0.17)), ((-W, -D + 0.17), (W, -D + 0.17))):
    m.box((0, a[1], H - 0.08), (2 * W, 0.08, 0.16), walnut, col=False)

# ------------------------------------------------------------------ north wall: departures
dest = {}
for i, (mid, label) in enumerate((('manor', 'HOLLOWMERE MANOR'), ('farm', 'THISTLEWICK FARM'), ('carnival', 'LANTERNFALL CARNIVAL'))):
    x = -7.0 + i * 7.0
    y = D - 0.15
    g = m.static(x, y - 1)
    # door frame + painted platform number
    for sx in (-1, 1):
        g.box((x + sx * 0.9, y - 0.06, 1.45), (0.16, 0.14, 2.9), walnut, bevel=0.015)
    g.box((x, y - 0.06, 2.95), (1.96, 0.16, 0.18), walnut, bevel=0.015)
    m.place(pf.door, 'hinge', f'Departure Door ({label.title()})', (x, y - 0.12, 0), rz=PI, key='depart_door',
            w=1.6, h=2.85, wood=walnut_dk, handle=brass, hinge='left', open_dir=1)
    # destination painting with its own lit frame
    pic_c = (x, y - 0.05, 3.95)
    thumb = os.path.join(gh.ROOT, 'client', 'public', 'maps', f'{mid}.jpg')
    if os.path.exists(thumb):
        picture(thumb, (x, y - 0.075, 3.95), 1.9, 1.07)
    for sx in (-1, 1):
        g.box((x + sx * 1.01, y - 0.05, 3.95), (0.12, 0.06, 1.31), brass, bevel=0.01)
    for sz in (-1, 1):
        g.box((x, y - 0.05, 3.95 + sz * 0.6), (2.14, 0.06, 0.12), brass, bevel=0.01)
    g.box((x, y - 0.02, 3.95), (2.0, 0.02, 1.15), walnut_dk)
    sign_text(g, label, (x, y - 0.1, 3.21), 0.16, cream)
    sign_text(g, f'PLATFORM {i + 1}', (x, y - 0.1, 3.06 - 0.02), 0.09, brass)
    dest[mid] = gh.to_three((x, y - 0.1, 3.95))
m.place(sconce, 'flicker', 'Gas Lamp', (-3.5, D - 0.15, 2.6), rz=0, key='sconce')
m.place(sconce, 'flicker', 'Gas Lamp', (3.5, D - 0.15, 2.6), rz=0, key='sconce')

# ------------------------------------------------------------------ south wall: entrance, board, tickets
y = -D + 0.15
g = m.static(0, y + 1)
for sx in (-1, 1):
    m.place(pf.door, 'hinge', 'Entrance Door', (sx * 0.75, y + 0.12, 0), rz=0, key='entrance_' + ('l' if sx < 0 else 'r'),
            w=1.4, h=3.0, wood=walnut_dk, handle=brass, hinge='left' if sx < 0 else 'right', open_dir=-1)
g.box((0, y + 0.06, 1.5), (3.2, 0.12, 3.3), walnut_dk)
g.box((0, y + 0.08, 3.15), (3.4, 0.18, 0.25), walnut, bevel=0.015)
sign_text(g, 'THE WAITING ROOM', (0, y + 0.18, 4.25), 0.34, brass, rz=PI)
sign_text(g, 'all spirits & their hunters', (0, y + 0.18, 3.85), 0.14, cream, rz=PI)
# notice board frame (the client draws the live board inside it)
BX, BZ, BW, BH = -6.2, 2.45, 3.2, 1.9
for sx in (-1, 1):
    g.box((BX + sx * (BW / 2 + 0.07), y + 0.07, BZ), (0.14, 0.12, BH + 0.28), walnut, bevel=0.015)
for sz in (-1, 1):
    g.box((BX, y + 0.07, BZ + sz * (BH / 2 + 0.07)), (BW + 0.28, 0.12, 0.14), walnut, bevel=0.015)
g.box((BX, y + 0.02, BZ), (BW, 0.03, BH), m.mat('cork', '#6b4a2e', rough=0.95))
sign_text(g, 'NOTICES', (BX, y + 0.14, BZ + BH / 2 + 0.32), 0.18, brass, rz=PI)
# ticket counter
TX = 6.2
g.box((TX, y + 0.75, 0.55), (3.0, 0.7, 1.1), walnut, bevel=0.02, col=True)
g.box((TX, y + 0.72, 1.12), (3.2, 0.8, 0.05), walnut_dk)
for k in range(9):
    g.cyl((TX - 1.4 + k * 0.35, y + 0.45, 1.15), 0.012, 1.3, brass, n=5)
g.box((TX, y + 0.45, 2.48), (3.0, 0.1, 0.1), brass)
g.box((TX, y + 0.15, 1.8), (3.0, 0.3, 1.4), walnut_dk)
sign_text(g, 'TICKETS', (TX, y + 0.4, 2.85), 0.28, brass, rz=PI)
m.place(desk_bell, 'bell', 'Counter Bell', (TX + 0.9, y + 0.95, 1.6), rz=0)
m.place(pf.candelabra, 'flame', 'Ticket Candles', (TX - 1.0, y + 0.95, 1.15), metal=brass, wax=wax)
m.place(sconce, 'flicker', 'Gas Lamp', (-3.0, -D + 0.15, 2.6), rz=PI, key='sconce')
m.place(sconce, 'flicker', 'Gas Lamp', (3.0, -D + 0.15, 2.6), rz=PI, key='sconce')

# ------------------------------------------------------------------ hunters' side (east)
HP = (7.0, -1.5)
m.put(medallion, (HP[0], HP[1], 0), ring=brass, inner=m.mat('hunter_pad', '#3a2a1c', rough=0.7), glow=amber)
g = m.static(10.3, -1.5)
g.box((10.6, -1.5, 1.2), (0.12, 2.6, 0.9), walnut, bevel=0.015)
g.box((10.55, -1.5, 1.2), (0.06, 2.4, 0.7), walnut_dk)
sign_text(g, 'HUNTERS', (10.5, -1.5, 1.28), 0.3, amber, rz=-HALF)
sign_text(g, 'stand here to hunt', (10.5, -1.5, 0.98), 0.11, cream, rz=-HALF)
for sy in (-1, 1):
    g.box((10.6, -1.5 + sy * 1.15, 0.4), (0.08, 0.08, 0.8), walnut)
m.put(coat_rack, (10.8, -5.2, 0))
m.put(revealer_case, (10.9, 2.6, 0), rz=HALF)
m.place(pf.hanging_lantern, 'swing', 'Hunter Lantern', (8.5, -4.2, H), metal=iron, glass=glass, drop=1.6, key='lantern')
m.place(pf.hanging_lantern, 'swing', 'Hunter Lantern', (8.5, 1.4, H), metal=iron, glass=glass, drop=1.6, key='lantern')
m.place(pf.crate, 'jolt', 'Crate of Lamp Oil', (10.6, -7.6, 0), rz=0.2, wood=walnut, dark=walnut_dk, key='crate')
m.place(pf.crate, 'jolt', 'Crate of Lamp Oil', (9.8, -7.9, 0), rz=-0.1, wood=walnut, dark=walnut_dk, key='crate')
m.place(pf.barrel, 'jolt', 'Barrel', (10.9, 5.6, 0), wood=walnut, hoop=iron)
m.place(pf.upright_piano, 'music', 'Station Piano', (9.4, D - 0.6, 0), rz=0, wood=walnut_dk, keys_white=cream, keys_black=black, brass=brass)
m.place(pf.globe, 'spin', 'Globe', (11.0, 7.4, 0), wood=walnut, brass=brass, sea=sea, land=land)

# ------------------------------------------------------------------ ghosts' side (west)
GP = (-7.0, -1.5)
m.put(medallion, (GP[0], GP[1], 0), ring=m.mat('pewter', '#8a9a9e', rough=0.4, metal=0.8), inner=m.mat('ghost_pad', '#1a2f33', rough=0.7), glow=teal_glow)
g = m.static(-10.3, -1.5)
g.box((-10.6, -1.5, 1.2), (0.12, 2.6, 0.9), walnut, bevel=0.015)
g.box((-10.55, -1.5, 1.2), (0.06, 2.4, 0.7), walnut_dk)
sign_text(g, 'GHOSTS', (-10.5, -1.5, 1.28), 0.3, teal_glow, rz=HALF)
sign_text(g, 'stand here to haunt', (-10.5, -1.5, 0.98), 0.11, cream, rz=HALF)
for sy in (-1, 1):
    g.box((-10.6, -1.5 + sy * 1.15, 0.4), (0.08, 0.08, 0.8), walnut)
m.put(draped, (-10.6, -5.6, 0), w=1.6, d=0.9, h=0.9, seed=1)
m.put(draped, (-10.8, 3.2, 0), rz=HALF, w=1.1, d=0.9, h=1.3, seed=2)
m.put(draped, (-9.3, 6.9, 0), w=0.9, d=0.9, h=1.0, seed=3)
m.put(side_table, (-9.0, -7.3, 0))
m.place(pf.candelabra, 'flame', 'Candelabra', (-9.0, -7.3, 0.76), metal=brass, wax=wax)
m.place(pf.rocking_chair, 'rock', 'Rocking Chair', (-8.6, 4.6, 0), rz=-2.4, wood=walnut, seat=teal_cloth)
m.place(pf.portrait, 'swing', 'Portrait of the Stationmaster', (-W + 0.18, 7.0, 3.0), rz=HALF, w=1.0, h=1.3,
        frame=brass, canvas=teal_cloth)

# ------------------------------------------------------------------ centre: benches, clock, chandeliers
m.put(pf.rug, (0, -1.0, 0), w=8.0, d=6.0, mat=rug_red)
for x in (-2.0, 2.0):
    m.put(bench, (x, 0.9, 0), rz=PI)
    m.put(bench, (x, -2.9, 0))
m.place(station_clock, 'clock', 'Station Clock', (0, -1.0, H), rz=0, key='sclock_s')
m.place(station_clock, 'clock', 'Station Clock', (0, -1.0, H), rz=PI, key='sclock_n')
for x in (-6.0, 6.0):
    m.place(pf.chandelier, 'swing', 'Chandelier', (x, 3.6, H), metal=brass, wax=wax, drop=1.3, key='chand')
m.put(trolley, (-3.6, -6.8, 0), rz=0.15)
m.place(trunk, 'jolt', 'Steamer Trunk', (-3.75, -6.82, 0.35), rz=0.15, s=0.85)
m.place(trunk, 'jolt', 'Hatbox', (-3.4, -6.7, 0.73), rz=0.5, s=0.45, mat=velvet)
m.place(balloons, 'bob', 'Lost Balloons', (3.1, 0.9, 0.5))
for (x, y) in ((-W + 0.8, D - 0.8), (W - 0.8, -D + 0.8), (-W + 0.8, -D + 0.8), (4.0, D - 0.7)):
    pot = m.static(x, y)
    pot.lathe((x, y, 0), [(0.28, 0), (0.34, 0.45), (0.38, 0.5), (0.3, 0.52)], terracotta, n=12)
    pot.collide((x, y, 0.3), (0.7, 0.7, 0.6))
    m.place(pf.tree, 'foliage', 'Potted Palm', (x, y, 0.5), bark=bark, leaves=leaf, h=1.9, crown=0.75, seed=int(x * 3 + y), lumps=4,
            col=False, params={'leaf': '#4c6b39'})

# ------------------------------------------------------------------ guide boards
GW, GH, GZ = 2.5, 1.7, 2.95
m.put(board_frame, (-W + 0.2, GP[1], GZ), rz=HALF, w=GW, h=GH)    # Ghost's Guide, west wall (faces east)
m.put(board_frame, (W - 0.2, HP[1], GZ), rz=-HALF, w=GW, h=GH)    # Hunter's Handbook, east wall (faces west)
EW, EH = 2.3, 1.45
m.put(easel, (0, -6.2, 0), rz=PI, w=EW, h=EH)                     # house rules chalkboard, facing the benches

# ------------------------------------------------------------------ gameplay data
m.spawn('hunter', (HP[0], HP[1], 0), face=(-1, 0))
m.spawn('ghost', (GP[0], GP[1], 0), face=(1, 0))
for a in range(6):
    ang = a * PI / 3
    m.spawn('hunter', (HP[0] + math.cos(ang) * 2.6, HP[1] + math.sin(ang) * 2.6, 0), face=(-1, 0))
    m.spawn('ghost', (GP[0] + math.cos(ang) * 2.6, GP[1] + math.sin(ang) * 2.6, 0), face=(1, 0))
m.penalty_spawn((0, -1.0, 0))  # unused in the waiting room
m.meta('lobby', {
    'pads': {'hunter': {'pos': gh.to_three((HP[0], HP[1], 0.03)), 'r': 1.6},
             'ghost': {'pos': gh.to_three((GP[0], GP[1], 0.03)), 'r': 1.6}},
    'board': {'pos': gh.to_three((BX, -D + 0.15 + 0.05, BZ)), 'normal': [0, 0, -1], 'w': BW, 'h': BH},
    'boards': {
        'notice': {'pos': gh.to_three((BX, -D + 0.15 + 0.05, BZ)), 'normal': [0, 0, -1], 'w': BW, 'h': BH, 'style': 'paper'},
        'ghost': {'pos': gh.to_three((-W + 0.2 + 0.01, GP[1], GZ)), 'normal': [1, 0, 0], 'w': GW, 'h': GH, 'style': 'paper'},
        'hunter': {'pos': gh.to_three((W - 0.2 - 0.01, HP[1], GZ)), 'normal': [-1, 0, 0], 'w': GW, 'h': GH, 'style': 'paper'},
        'rules': {'pos': gh.to_three((0, -6.2 + 0.03, 0.75 + EH / 2)), 'normal': [0, 0, -1], 'w': EW, 'h': EH, 'style': 'chalk'},
    },
    'destinations': dest,
})
m.light((0, -1.0, 4.4), '#ffcf8a', 1.2, 12)
m.env(sky='#141018', fog={'color': '#120f16', 'near': 14, 'far': 60},
      hemi={'sky': '#8a86a8', 'ground': '#3a2a20', 'intensity': 0.75}, exposure=1.15, ambience='indoor', previewClip=5.2)
m.preview((0, -7.5, 1.6), (0, 4, 2.2), name='north')
m.preview((0, 6, 1.6), (0, -8, 2.0), name='south')
m.preview((-2, -1.5, 1.6), (10, -1.5, 1.2), name='hunters')
m.preview((2, -1.5, 1.6), (-10, -1.5, 1.2), name='ghosts')
m.finish()
