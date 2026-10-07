"""Render quick EEVEE previews of a built map: python ... -- --preview [--blend]

Writes blender/build/preview/<map>_<n>.png (eye-level views registered with
MapBuilder.preview plus an automatic top-down overview with altars marked).
"""
import math
import os

import bpy
from mathutils import Vector

from . import gh
from . import tex as texlib


def _lin(hexcol):
    return tuple(gh.srgb_to_linear(c) for c in texlib.hex_rgb(hexcol))


def render(mb, data, args):
    out_dir = os.path.join(gh.BUILD_DIR, 'preview')
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    env = data.get('env', {})
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.film_transparent = False
    try:
        scene.view_settings.view_transform = 'AgX'
    except TypeError:
        pass
    world = bpy.data.worlds.new('preview_world')
    scene.world = world
    try:
        world.use_nodes = True
    except Exception:
        pass
    bg = world.node_tree.nodes.get('Background')
    sky = env.get('sky', '#1a1d2e')
    moody = '--moody' in args
    if bg:
        if moody:
            bg.inputs[0].default_value = (*_lin(sky), 1.0)
            bg.inputs[1].default_value = 1.0 + env.get('hemi', {}).get('intensity', 1.0) * 0.6
        else:
            bg.inputs[0].default_value = (0.55, 0.55, 0.6, 1.0)
            bg.inputs[1].default_value = 1.6
    moon = env.get('moon')
    if moon:
        sun = bpy.data.lights.new('moon', 'SUN')
        sun.energy = moon.get('intensity', 1.0) * 1.5
        sun.color = _lin(moon.get('color', '#9fb4ff'))
        so = bpy.data.objects.new('moon', sun)
        d = moon.get('dir', [-0.4, -1, -0.3])  # three.js direction light travels
        v = Vector((d[0], -d[2], d[1])).normalized()  # back to blender space
        so.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
        scene.collection.objects.link(so)
    for i, l in enumerate(data['lights']):
        ld = bpy.data.lights.new(f'pl{i}', 'POINT')
        ld.energy = l['intensity'] * (60 if moody else 250)
        ld.color = _lin(l['color'])
        ld.shadow_soft_size = 0.1
        lo = bpy.data.objects.new(f'pl{i}', ld)
        p = l['pos']
        lo.location = (p[0], -p[2], p[1])
        scene.collection.objects.link(lo)

    # altar markers for the overview only
    marker_mat = bpy.data.materials.new('marker')
    try:
        marker_mat.use_nodes = True
    except Exception:
        pass
    bsdf = next(n for n in marker_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Emission Color'].default_value = (0.2, 1.0, 0.6, 1)
    bsdf.inputs['Emission Strength'].default_value = 20
    markers = []
    for fp in data['flagPoints']:
        p = fp['pos']
        bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=0.2, location=(p[0], -p[2], p[1] + 3))
        o = bpy.context.active_object
        o.data.materials.append(marker_mat)
        markers.append(o)

    views = list(mb.preview_views)
    b = data['bounds']
    cx, cy = (b[0] + b[2]) / 2, -(b[1] + b[3]) / 2
    span = max(b[2] - b[0], b[3] - b[1])
    cam_data = bpy.data.cameras.new('cam')
    cam = bpy.data.objects.new('cam', cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    def shoot(path):
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print('[preview]', path)

    # overview: an ortho camera just under the ceiling so interiors read
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = span * 1.08
    cam.location = (cx, cy, 120)
    cam.rotation_euler = (0, 0, 0)
    cam_data.clip_end = 500
    if '--keep-ceiling' not in args:
        cam.location.z = env.get('previewClip', 3.6)
        cam_data.clip_start = 0.01
        cam_data.clip_end = 60
    if not moody:
        top = bpy.data.lights.new('overview_sun', 'SUN')
        top.energy = 2.5
        to = bpy.data.objects.new('overview_sun', top)
        to.rotation_euler = (0.35, 0.2, 0.6)
        scene.collection.objects.link(to)
    shoot(os.path.join(out_dir, f'{mb.id}_overview.png'))
    for m in markers:
        m.hide_render = True

    cam_data.type = 'PERSP'
    cam_data.clip_start = 0.05
    cam_data.clip_end = 300
    for i, (pos, look, lens, name) in enumerate(views):
        cam_data.lens = lens
        cam.location = pos
        d = Vector(look) - Vector(pos)
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        shoot(os.path.join(out_dir, f'{mb.id}_{name or i}.png'))
    if '--blend' in args:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(gh.BUILD_DIR, f'{mb.id}.blend'))
