# Map authoring guide

Maps are Python scripts run by Blender in background mode. Each script builds geometry with
`blender/lib/gh.py` (+ `prefabs.py`, `tex.py`) and calls `m.finish()`, which writes:

- `client/public/maps/<id>.glb` — everything visible
- `shared/maps/<id>.json` — gameplay data (colliders, props, altars, spawns, lights, environment)

```bash
# build + render previews into blender/build/preview/<id>_*.png
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P blender/maps/<id>.py -- --preview
# validate (must print OK): schema, prop nodes, spawn placement, reachability, budgets
node scripts/check-map.mjs <id> --ascii
```

`--moody` renders previews with the in-game night lighting instead of bright inspection lighting.
Geometry is exported with meshopt compression (decoded by the client); `--no-compress` disables it.
`--blend` also saves `blender/build/<id>.blend` for inspection.

## Coordinates and scale

Blender space: X east, Y north, Z up, metres. The JSON is converted to three.js (Y up) for you.

| thing | size |
|---|---|
| player | 1.7 m tall, eye 1.55 m, radius 0.32 m (collides as a 0.64 m square) |
| step-up | 0.45 m (anything taller blocks walking) |
| hunter jump | ~0.9 m; ghost jump ~1.4 m (ghosts float down slowly) |
| doorways / gaps | ≥ 1.4 m wide, ≥ 2.3 m tall; corridors ≥ 1.8 m |
| manipulation reach | 7 m — ghosts should almost always have a prop within reach |
| ghost see radius | 4.5 m; snap hearing 9 m; whistle 48 m |

Playable area: roughly 55–75 m on a side. Bigger is not better: the relic carrier walks ~3.5 m/s.

## Collision

Collision is a list of axis-aligned boxes. `MapBuilder.box(..., col=True)` (the default for
`m.box`) registers its bounds; `Geo.box(..., col=True)`, `Geo.collide(center, size)` and
`m.collider(min, max)` add colliders explicitly. Rotated boxes register their axis-aligned
bounds, so prefer 90° rotations for anything big and solid.

- Every solid thing a player could walk into needs a collider; decorative clutter can skip it.
- Interiors need a ceiling collider. Outdoor maps need **invisible perimeter colliders at least
  8 m tall** (`m.collider`) behind a believable visual boundary (hedges, fences, buildings, cliffs).
- Nothing may let a player get out of the map by jumping (ghost hop 1.4 m on top of any surface).
- Floors are boxes whose top is the walkable surface (`m.floor`). Stairs: `m.stairs` (rise ≤ 0.3).

## Gameplay markers

- **Altars** (`m.flag_point(pos, rz, prefab=pf.altar, stone=..., trim=..., glow=...)`): 10–14 per
  map. All altars on a map must look identical — the hunter never knows which is the active spawn
  or capture point. Leave ≥ 1.2 m of walkable clearance around each. Spread them out: the game
  picks spawn/capture pairs at least 55% of the longest pair distance apart, so put several near
  the edges/corners and avoid clumps (the validator warns under 6 m).
- **Hunter spawns** (`m.spawn('hunter', pos, face=(dx, dy))`): 1–4, together.
- **Ghost spawns**: ≥ 10, spread across the map (ghosts spawn scattered, never in one room).
- **Penalty box** (`m.penalty_spawn(pos)` ×4–6): an enclosure inside the map that frozen ghosts
  sit in. It must be fully sealed (walls + lid colliders) yet visible to everyone (bars, fence,
  glass, cage). Interior ≥ 3 × 3 m. The validator fails if it is reachable from the play area.

## Interactive props

Props are what ghosts manipulate to talk to each other and distract hunters. Aim for 80–130 per
map across all archetypes, distributed so every area has several. Each needs a short `label`
("Grandfather Clock", "Laundry Line"). Idle motion should look natural; the subtle manipulation
stays inside the range of natural motion so only an attentive hunter notices; the big
manipulation is loud and obvious.

```python
m.place(prefab_fn, 'archetype', 'Label', pos, rz=0, params={...}, key='cache-key', **prefab_kwargs)
```

`prefab_fn(p, **kw)` draws into `p.body` (static part of the prop) and into named parts:
`p.part(name, pos, rz=..., parent=...)` returns a `Part`; draw into `part.geo` in the part's local
space (origin = the pivot). Use `key=` for identical copies so meshes are shared.

The client animates nodes named `P_<id>_<part>`. In three.js the part's local axes are Blender's
converted: three `x` = Blender X, three `y` = Blender Z (up), three `z` = Blender −Y.

| archetype | required parts | idle | subtle | big | params |
|---|---|---|---|---|---|
| `hinge` | `pivot` | tiny sway | swings ~12° and back | flings open and slams (bang) | `axis` (y), `dir` ±1 opening sign, `closed` offset of the shut pose (0 = authored pose is shut), `open` max swing (1.3) |
| `swing` | `pivot` | pendulum sway | sways wider for a few seconds | wild swing | `amp` idle rad, `period` s, `axes` `xz`/`x`/`z` |
| `rock` | `pivot` | still | gentle rocking | violent rocking | `axis` (x), `period` |
| `spin` | `pivot` | slow spin/oscillation | turns ~30° (persists) | whirls | `axis` (y), `speed` rad/s, `wobble` |
| `clock` | `hour`, `minute` (+`pend`) | ticks | runs backwards | hands spin + chimes | `axis` (z: face normal) |
| `foliage` | `pivot` | wind sway | sways against the wind | violent shake + leaves | `amp`, `leaf` hex |
| `cloth` | `cloth0`… | ripples | billows softly | huge billow | `amp` metres, `axis` (z) |
| `flame` | `flame0`… | flicker | gutters in a draft | flares then goes out, relights | — |
| `jolt` | `pivot` | still | scoots a few cm (persists) | hops and lands askew | — |
| `music` | — (`pivot` lid optional) | — | one soft note | crashing chord | `instrument` piano/musicbox/organ/calliope |
| `bell` | `pivot` | still | trembles | swings and rings | `axis` (z), `tone` Hz |
| `flicker` | `bulb0`… | steady glow | brief flicker | strobes and blacks out | — |
| `bob` | `pivot` | bobs | drifts | yanked up, bounces | `amp` metres |

Any prop may also include decorative parts that always animate: `flame*` (flicker), `cloth*`
(wind ripple, sheet hanging down from its node origin — use `geo.sheet`), `bulb*` (glow),
`dancer*` (spins while music plays). Sheets for cloth should be subdivided (`nx`, `ny` ≥ 6).

`params.sound` may override the archetype sound with one of: bang, creak, chime, clatter, rustle,
whoosh, thud, whoomp, buzz, piano, musicbox, organ, calliope, bell, whirr, squeak, jingle,
splash, caw, rattle, gong.

## Lights and environment

- `m.light(pos, color, intensity, distance, flicker=0..1)` for fixed lights, `p.light(...)` for
  lights that belong to a prop (they swing/flicker with it). Budget: ≤ 24 lights per map.
  Intensity ~1 is a candle cluster, ~2 a chandelier/streetlamp. Lights have no shadows in-game,
  so keep their `distance` modest to limit bleeding through walls.
- Emissive materials (`m.mat(..., emit='#hex', strength=...)`) bloom in-game: windows, bulbs, embers.

```python
m.env(
    sky='#0d1020',                                   # background / horizon colour
    fog={'color': '#0d1020', 'near': 6, 'far': 45},
    hemi={'sky': '#5b6a9a', 'ground': '#2a1f18', 'intensity': 0.5},
    moon={'dir': [-0.4, -1.0, -0.3], 'color': '#9fb4ff', 'intensity': 0.6, 'shadows': True},  # three.js dir (Y up), outdoor maps
    exposure=1.0,
    ambience='indoor',    # indoor | wind | night (ambient sound bed)
    stars=True,           # outdoor sky dome
    previewClip=3.6,      # overview render camera height (below ceilings)
)
```

## Style

The goal is a cohesive, handmade-looking stylised diorama, not "AI slop":

- Pick a tight palette (8–12 colours) and stick to it. Large surfaces use `tex.*` generated
  textures in palette colours; small props use flat materials. Reuse materials.
- Bevel boxes slightly (0.01–0.03) so edges catch light. Mix flat shading (boxes, rocks, foliage
  blobs) with smooth lathe shapes (vases, lamps, bottles).
- Compose vignettes that tell small stories — a dinner abandoned mid-meal, a reading nook with a
  book left open, a toppled chair — rather than uniform scatter. Vary heights and silhouettes.
- No floating or interpenetrating objects; things rest on things. Rugs under tables, frames on
  walls, clutter on shelves.
- Every area should be recognisable at a glance (landmarks help players call out locations).
- Keep the GLB ≤ 10 MB and ≤ 60 materials.

## Lessons from building the three maps

- **Instancing.** Static geometry is merged into spatial chunks, so a repeated bookcase is stored once
  per copy. For heavily repeated furniture, create linked-duplicate Blender objects that share one
  mesh before `finish()` (see `inst()` in `blender/maps/manor.py`); the exporter writes the mesh once.
- **Bevels cost vertices.** A bevelled box exports roughly 4× the vertices of a plain one. Skip
  bevels on thin trim and anything small.
- **Stairs and raised floors.** The nav grid samples one floor per 0.5 m cell and accepts rises up
  to 0.65 m between neighbouring cells (bots hop the steep ones). Snap platform edges to the 0.5 m
  grid where you can, and fill under lofts so the walkable surface is unambiguous.
- **Windows vs doors.** `m.wall` seals openings whose sill is ≥ 0.5 m with an invisible collider;
  lower sills count as door thresholds and stay open.
- **Keyed props** (`place(..., key=...)`) share meshes and inherit the prefab's archetype params;
  params passed explicitly to `place` override them.
- **Validator hangs** usually mean the GLB was being rewritten mid-read; rerun it.
