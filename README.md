# Ghost Hunter

A first-person multiplayer browser game of hide-and-seek with a relic. Invisible **ghosts** smuggle a
relic from altar to altar; **hunters** can't see them, so they listen for snaps and whistles, watch
for haunted objects behaving oddly, and freeze ghosts with a short cone of spectral light.

Three hand-built maps — **Hollowmere Manor**, **Thistlewick Farm** and **Lanternfall Carnival** —
are modelled procedurally in Blender (see `blender/`), and the client renders them with three.js.

## Running it

```bash
npm install
npm run dev        # http://localhost:5173 (Vite middleware + game server on one port)
```

Production:

```bash
npm run build
npm start          # serves dist/ and the WebSocket game server on $PORT (default 5173)
```

### Deploying (Render)

Live: **https://ghost-hunter-ylbq.onrender.com** (production, `production` branch, in the "Ghost
Hunters" Render project) and **https://ghost-hunter-staging.onrender.com** (staging, `main`).

`render.yaml` is a Render Blueprint with two Node web services on the starter plan, following the
same branch layout as decks-and-hexes: **`ghost-hunter`** deploys from the `production` branch and
**`ghost-hunter-staging`** from `main`. Each runs `npm ci --include=dev && npm run build`, then
`npm start`, which serves the client and the WebSocket game on one port (`/healthz` for health
checks). There is no database. To release, fast-forward `production` to `main` and push.

Open the page, create a room, share the four-letter code (or the invite link) and start. Add bots
from the lobby to fill teams or play solo. Requires a desktop browser with keyboard and mouse.

Other scripts:

| command | what it does |
|---|---|
| `npm test` | rules tests (collision, relic relay, revealer, exposure, visibility, sound routing) |
| `npm run sim -- manor 1 4 3` | headless bots-only rounds for balance (map, hunters, ghosts, rounds) |
| `npm run check -- manor --ascii` | validate a built map: props, spawns, altar reachability, budgets |
| `npm run maps` | rebuild every map and the character models with Blender |

Dev shortcut: `http://localhost:5173/?test=ghost&map=farm&bots=4` creates a room with bots and
starts immediately as the given role.

## How to play

**Round:** ghosts must deliver the relic to a capture altar three times before the timer runs out.
Every map has 10–14 identical altars; only ghosts know which one holds the relic and which one is
the capture point. Each delivery (or a reset) picks a new, far-apart spawn/capture pair. Hunters
start blind for 10 seconds while the ghosts spread out.

### Ghosts

| input | action |
|---|---|
| `WASD`, `Space` | move, float (ghosts drift down slowly) |
| `LMB` | **snap** — no cooldown, heard by anyone within 9 m, with direction |
| `F` | **whistle** — heard within ~48 m, 12 s cooldown |
| `E` | **subtle haunt** on the targeted prop — a natural-looking variation, no cooldown |
| `Q` | **big haunt** — loud and obvious, 10 s cooldown |
| `G` | drop the relic (to hand it over) |

- Ghosts are invisible to hunters and to each other unless within 4.5 m. Stay that close for more
  than 4 seconds and every ghost involved is **exposed** to the hunters for 5 seconds.
- Walk into the relic to pick it up. Your **grip** (14 s by default, configurable) drains while
  carrying and recovers slowly, so long routes need a relay between ghosts.
- Carrying is slow, leaves a fading trail of glowing ectoplasm, and makes the relic hum audibly to
  nearby hunters. Holding it on the capture altar for 2.5 s delivers it — and the altar's ritual
  ring and chime can be seen and heard by everyone.

### Hunters

| input | action |
|---|---|
| `WASD`, `Space`, `Shift` | move, jump, walk |
| `LMB` | **revealer** — 11 m cone, 2.2 s cooldown |

A ghost hit by the revealer is revealed and frozen for 3 seconds, then locked in the map's penalty
box (30 s by default) before returning to play. Hitting the relic carrier shatters the relic: it
re-forms at a new spawn altar and the capture altar moves too.

Things to watch for: snaps and whistles (direction arcs around the crosshair), big haunts anywhere,
subtle haunts — a clock ticking backwards, a curtain breathing, a chandelier swaying a little
wider, a chair that has moved a few centimetres — the ectoplasm trail and the relic's hum.

### Host options

Map, round length, penalty time, relic grip, bot skill, and teams: move any player between
Hunters and Ghosts, add/remove bots on either side, or shuffle with a chosen number of hunters.

## Maps

| map | setting | penalty box |
|---|---|---|
| **Hollowmere Manor** (60 × 44 m) | Thirteen candlelit rooms around a two-storey foyer: parlour, library stacks, dining room set mid-dinner, kitchen and scullery, nursery, billiard and music rooms, portrait gallery, glass conservatory. Many doorways form loops. | The Birdcage — a domed iron cage in the conservatory |
| **Thistlewick Farm** (70 × 70 m) | Autumn farmstead at night: walk-through barn with a hay loft, farmhouse porch and kitchen, a corn maze, orchard, pumpkin patch, windmill and pond, laundry lines, creek. | The Chicken Run — a wire-mesh cage by the coop |
| **Lanternfall Carnival** (71 × 71 m) | Shuttered fairground: walk-in big top, carousel plaza, Ferris wheel, midway booths and high striker, funhouse, fortune teller and calliope wagons, caravan back lot. | The Lion Cage — a barred circus wagon |

Each has 13 identical altars, 12–14 ghost spawns and ~130 interactive props across all archetypes.

## Architecture

```
shared/     rules shared by server and client: constants, AABB collision, nav grid, prop archetypes
            maps/<id>.json  gameplay data exported from Blender (colliders, props, altars, spawns, lights)
server/     Node WebSocket server: rooms/lobby (room.js), authoritative round (game.js), bots (bots.js)
client/     Vite + three.js: lobby UI, first-person controller, prop animation, procedural audio, HUD
blender/    map toolkit (lib/), map scripts (maps/), character models (characters.py)
docs/       MAP_AUTHORING.md — how to build a map and the prop archetype contract
```

- **Authority.** Clients simulate their own movement against the same collision boxes the server
  uses; the server sanity-checks speed and owns everything else: visibility, the relic, freezing
  (with lag-compensated cone tests and line of sight), the penalty box, exposure, and cooldowns.
- **Visibility is filtered per recipient.** A hunter's snapshot never contains a hidden ghost or
  the relic's location; snaps and whistles are only sent to players within earshot. There is
  nothing in a hunter's client to cheat with.
- **Props** are named node hierarchies inside the map GLB (`P_<id>_<part>`). Manipulations are
  broadcast as `{prop, kind, seed}` and every client plays the same seeded animation. See
  `shared/archetypes.js` and `docs/MAP_AUTHORING.md` for the 13 archetypes.
- **Audio** is synthesised at load time with `OfflineAudioContext` (no sound files) and played
  through HRTF panners.

## Building maps

Maps are Python scripts run by Blender headless:

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P blender/maps/manor.py -- --preview
node scripts/check-map.mjs manor --ascii
```

See [docs/MAP_AUTHORING.md](docs/MAP_AUTHORING.md) for the toolkit and the rules a map must satisfy.
