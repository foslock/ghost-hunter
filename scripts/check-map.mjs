#!/usr/bin/env node
// Validates a built map: node scripts/check-map.mjs <mapId> [--ascii]
// Checks the JSON sidecar, GLB prop nodes, spawn placement and reachability of every altar.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { CollisionWorld } from '../shared/collision.js';
import { NavGrid } from '../shared/nav.js';
import { ARCHETYPES, SOUNDS } from '../shared/archetypes.js';
import { PLAYER, RELIC } from '../shared/constants.js';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const id = process.argv[2];
const ascii = process.argv.includes('--ascii');
if (!id) {
  console.error('usage: node scripts/check-map.mjs <mapId> [--ascii]');
  process.exit(2);
}
const errors = [];
const warns = [];
const map = JSON.parse(fs.readFileSync(path.join(root, 'shared/maps', `${id}.json`), 'utf8'));
const glbPath = path.join(root, 'client/public/maps', `${id}.glb`);
const glb = fs.readFileSync(glbPath);
const gltf = JSON.parse(glb.slice(20, 20 + glb.readUInt32LE(12)).toString());
const nodeNames = new Set(gltf.nodes.map((n) => n.name));

for (const k of ['spawns', 'penalty', 'flagPoints', 'props', 'colliders', 'lights', 'env', 'bounds']) {
  if (!map[k]) errors.push(`missing field ${k}`);
}
const world = new CollisionWorld(map.colliders);
const nav = new NavGrid(world, [map.bounds[0] - 1, map.bounds[1] - 1, map.bounds[2] + 1, map.bounds[3] + 1]);

// --- props
const ids = new Set();
for (const p of map.props) {
  if (ids.has(p.id)) errors.push(`duplicate prop id ${p.id}`);
  ids.add(p.id);
  const a = ARCHETYPES[p.type];
  if (!a) { errors.push(`prop ${p.id}: unknown archetype ${p.type}`); continue; }
  if (!nodeNames.has(`P_${p.id}`)) errors.push(`prop ${p.id}: node P_${p.id} missing from GLB`);
  for (const part of a.parts) {
    if (!nodeNames.has(`P_${p.id}_${part}`)) errors.push(`prop ${p.id} (${p.type}): required part P_${p.id}_${part} missing`);
  }
  if (p.params?.sound && !SOUNDS.includes(p.params.sound)) errors.push(`prop ${p.id}: unknown sound ${p.params.sound}`);
  if (!p.label) warns.push(`prop ${p.id} has no label`);
}
const byType = {};
for (const p of map.props) byType[p.type] = (byType[p.type] || 0) + 1;

// --- spawns
const free = (p) => !world.overlaps(p[0], p[1] + 0.05, p[2], PLAYER.radius, PLAYER.height - 0.1);
const hs = map.spawns.hunter || [];
const gs = map.spawns.ghost || [];
const ps = map.penalty?.spawns || [];
if (hs.length < 1) errors.push('need at least 1 hunter spawn');
if (gs.length < 6) warns.push(`only ${gs.length} ghost spawns (want >= 8, spread out)`);
if (ps.length < 1) errors.push('need at least 1 penalty spawn');
if (map.flagPoints.length < 8) warns.push(`only ${map.flagPoints.length} altars (want 10-14)`);
for (const [label, list] of [['hunter', hs], ['ghost', gs], ['penalty', ps]]) {
  list.forEach((p, i) => { if (!free(p)) errors.push(`${label} spawn ${i} at ${p.slice(0, 3)} is inside a collider`); });
}

// --- reachability
const start = hs.length ? nav.nearest(hs[0][0], hs[0][1], hs[0][2]) : -1;
const reach = start >= 0 ? nav.reach(start) : new Uint8Array(nav.w * nav.h);
if (start < 0) errors.push('hunter spawn is not on walkable floor');
const reachable = (p, r = 1.6) => {
  const R = Math.ceil(r / nav.cell);
  const ci = Math.floor((p[0] - nav.x0) / nav.cell), cj = Math.floor((p[2] - nav.z0) / nav.cell);
  for (let dj = -R; dj <= R; dj++) for (let di = -R; di <= R; di++) {
    const i = ci + di, j = cj + dj;
    if (i < 0 || j < 0 || i >= nav.w || j >= nav.h) continue;
    const idx = j * nav.w + i;
    if (reach[idx] && Math.hypot(di, dj) * nav.cell <= r) return true;
  }
  return false;
};
gs.forEach((p, i) => { if (!reachable(p, 0.8)) errors.push(`ghost spawn ${i} not reachable from hunter spawn`); });
map.flagPoints.forEach((f) => {
  const base = [f.pos[0], f.pos[1] - 1.0, f.pos[2]];
  if (!reachable(base, RELIC.captureRadius - 0.2)) errors.push(`${f.id} at ${f.pos} not reachable within capture radius`);
});
ps.forEach((p, i) => { if (reachable(p, 0.6)) errors.push(`penalty spawn ${i} is reachable from the play area (must be enclosed)`); });

// --- altar spacing
const fp = map.flagPoints.map((f) => f.pos);
let maxD = 0;
const pairs = [];
for (let i = 0; i < fp.length; i++) for (let j = i + 1; j < fp.length; j++) {
  const d = Math.hypot(fp[i][0] - fp[j][0], fp[i][2] - fp[j][2]);
  pairs.push(d);
  maxD = Math.max(maxD, d);
}
const good = pairs.filter((d) => d >= maxD * RELIC.minPairFraction).length;
for (let i = 0; i < fp.length; i++) for (let j = i + 1; j < fp.length; j++) {
  if (Math.hypot(fp[i][0] - fp[j][0], fp[i][2] - fp[j][2]) < 6) warns.push(`altars ${i + 1} and ${j + 1} are closer than 6m`);
}

// --- budget
const size = fs.statSync(glbPath).size / 1e6;
if (size > 10) warns.push(`GLB is ${size.toFixed(1)} MB (budget 10 MB)`);
if (map.lights.length > 28) warns.push(`${map.lights.length} lights (client renders at most ~24 nearest; budget 28)`);
// double-sided copies (`*_2s`) are made automatically for open shells and don't count
const authored = new Set((gltf.materials || []).map((m) => m.name.replace(/_2s$/, ''))).size;
if (authored > 60) warns.push(`${authored} authored materials (budget 60)`);
const reachCells = reach.reduce((a, b) => a + b, 0);

console.log(`map ${map.id} "${map.name}"`);
console.log(`  bounds ${map.bounds.join(', ')}  (${(map.bounds[2] - map.bounds[0]).toFixed(0)} x ${(map.bounds[3] - map.bounds[1]).toFixed(0)} m)`);
console.log(`  glb ${size.toFixed(2)} MB, ${gltf.nodes.length} nodes, ${gltf.meshes.length} meshes, ${(gltf.materials || []).length} materials, ${(gltf.images || []).length} images`);
console.log(`  ${map.colliders.length} colliders, ${map.lights.length} lights, ${map.props.length} props ${JSON.stringify(byType)}`);
console.log(`  spawns: ${hs.length} hunter, ${gs.length} ghost, ${ps.length} penalty; ${fp.length} altars, longest pair ${maxD.toFixed(1)} m, ${good}/${pairs.length} pairs usable`);
console.log(`  walkable area reachable from hunter spawn: ${(reachCells * nav.cell * nav.cell).toFixed(0)} m^2`);

if (ascii) {
  const step = Math.max(1, Math.round(1 / nav.cell));
  const marks = new Map();
  const mark = (p, ch) => marks.set(`${Math.floor((p[0] - nav.x0) / nav.cell / step)},${Math.floor((p[2] - nav.z0) / nav.cell / step)}`, ch);
  gs.forEach((p) => mark(p, 'G'));
  ps.forEach((p) => mark(p, 'P'));
  fp.forEach((p) => mark(p, 'A'));
  hs.forEach((p) => mark(p, 'H'));
  map.props.forEach((p) => { if (!marks.has(`${Math.floor((p.pos[0] - nav.x0) / nav.cell / step)},${Math.floor((p.pos[2] - nav.z0) / nav.cell / step)}`)) mark(p.pos, 'o'); });
  console.log('\n  legend: . reachable floor, ? walkable but unreachable, # blocked, H/G hunter/ghost spawn, A altar, P penalty, o prop. North (Blender +Y) is up.');
  for (let j = 0; j < nav.h; j += step) {
    let line = '  ';
    for (let i = 0; i < nav.w; i += step) {
      const key = `${i / step},${j / step}`;
      if (marks.has(key)) { line += marks.get(key); continue; }
      let r = 0, wv = 0, blocked = 0;
      for (let b = 0; b < step; b++) for (let a = 0; a < step; a++) {
        const idx = (j + b) * nav.w + (i + a);
        if (i + a >= nav.w || j + b >= nav.h) continue;
        if (reach[idx]) r++;
        else if (nav.walkable(idx)) wv++;
        else blocked++;
      }
      line += r >= 3 ? '.' : r + wv >= 3 && wv > r ? '?' : '#';
    }
    console.log(line);
  }
}
for (const w of warns) console.log(`  WARN  ${w}`);
for (const e of errors) console.log(`  ERROR ${e}`);
console.log(errors.length ? `\n${errors.length} error(s)` : '\nOK');
process.exit(errors.length ? 1 : 0);
