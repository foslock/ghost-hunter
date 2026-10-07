"""Small test arena used for engine development."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib import gh, prefabs as pf, tex  # noqa: E402

m = gh.MapBuilder('sandbox', 'Sandbox')
floor = m.mat('floor', image=tex.wood_planks(), uv=3.0)
wallp = m.mat('wallpaper', image=tex.wallpaper(), uv=2.0)
wood = m.mat('wood', '#4a2e1c', rough=0.7)
dark = m.mat('dark', '#1c1410')
brass = m.mat('brass', '#b08a3e', rough=0.35, metal=1.0)
stone = m.mat('stone', image=tex.flagstones(), uv=2.0)
trim = m.mat('trim', '#8c7350', rough=0.5, metal=0.6)
glow = m.mat('altar_glow', '#2a3b3a', rough=0.6)
face = m.mat('clockface', '#e8dcc0', rough=0.6)
wax = m.mat('wax', '#efe6d0', rough=0.6)
glass = m.mat('glass', '#22324a', rough=0.1, emit='#1b2a48', strength=0.6)
leaf = [m.mat('leaf1', '#3e5a2c'), m.mat('leaf2', '#4f6b30')]
bark = m.mat('bark', '#3b2b20')
velvet = m.mat('velvet', image=tex.fabric(base='#5a1820'), uv=1.0)

S = 14
m.floor(-S, -S, S, S, floor)
for a, b in (((-S, -S), (S, -S)), ((-S, S), (S, S))):
    m.wall(a, b, wallp, h=4, openings=[(10, 1.6, 2.4, 0), (20, 1.8, 2.2, 0.9)], lower=(1.0, wood), trim=(0.15, 0.03, wood))
for a, b in (((-S, -S), (-S, S)), ((S, -S), (S, S))):
    m.wall(a, b, wallp, h=4, lower=(1.0, wood))
m.wall((-S, 0), (-4, 0), wallp, h=4, openings=[(5, 1.4, 2.4, 0)], lower=(1.0, wood))
m.box((0, 0, 4.15), (2 * S, 2 * S, 0.3), dark)

for i, (x, y) in enumerate(((-10, -10), (10, -10), (-10, 10), (10, 10), (0, 8))):
    m.flag_point((x, y, 0), prefab=pf.altar, stone=stone, trim=trim, glow=glow)

m.place(pf.grandfather_clock, 'clock', 'Grandfather Clock', (6, 13.4, 0), rz=0, key='gclock', wood=wood, brass=brass, face=face, dark=dark)
m.place(pf.chandelier, 'swing', 'Chandelier', (0, -6, 4.0), key='chand', metal=brass, wax=wax)
m.place(pf.rocking_chair, 'rock', 'Rocking Chair', (-6, -6, 0), rz=0.6, wood=wood)
m.place(pf.candelabra, 'flame', 'Candelabra', (4, 4, 0.8), metal=brass, wax=wax)
m.put(pf.table, (4, 4, 0), w=1.6, d=0.9, h=0.8, wood=wood)
m.place(pf.door, 'hinge', 'Door', (-9, 0, 0), w=1.4, h=2.4, wood=wood, frame=dark, handle=brass)
m.place(pf.tree, 'foliage', 'Potted Fern', (8, -2, 0), bark=bark, leaves=leaf, h=3, crown=1.0, seed=3)
m.place(pf.curtains, 'cloth', 'Curtains', (6, -13.75, 3.2), w=1.8, h=2.4, fabric=velvet, rod=brass)
m.place(pf.globe, 'spin', 'Globe', (-4, 6, 0), wood=wood, brass=brass, sea=m.mat('sea', '#2d4a5a'), land=m.mat('land', '#a08850'))
m.place(pf.crate, 'jolt', 'Crate', (10, 4, 0), wood=wood, dark=dark)
m.place(pf.portrait, 'swing', 'Portrait', (-2, 13.82, 2.6), rz=0, w=1.0, h=1.3, frame=brass, canvas=velvet)
m.place(pf.upright_piano, 'music', 'Piano', (-8, 13.4, 0), wood=wood, keys_white=face, keys_black=dark, brass=brass)
m.place(pf.hanging_lantern, 'swing', 'Lantern', (8, 8, 4.0), metal=dark, glass=glass)

m.spawn('hunter', (0, -10, 0), face=(0, 1))
for x, y in ((-12, 12), (12, 12), (-12, 2), (12, 2)):
    m.spawn('ghost', (x, y, 0), face=(0, -1))
m.penalty_spawn((-12, -12, 0))
m.light((0, 0, 3.5), '#ffcf8a', 1.5, 16)
m.env(sky='#141826', fog={'color': '#141826', 'near': 8, 'far': 40}, hemi={'sky': '#8a96c8', 'ground': '#2a2018', 'intensity': 0.6})
m.preview((0, -12, 1.6), (0, 0, 1.4), name='eye')
m.preview((-10, 10, 1.6), (6, 8, 1.4), name='corner')
m.finish()
