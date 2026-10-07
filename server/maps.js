// Loads map JSON sidecars and caches their collision worlds / nav grids.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { CollisionWorld } from '../shared/collision.js';
import { NavGrid } from '../shared/nav.js';
import { MAPS } from '../shared/constants.js';

const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'shared', 'maps');
const cache = new Map();

function mtime(file) {
  try { return fs.statSync(file).mtimeMs; } catch { return 0; }
}

export function loadMap(id) {
  const file = path.join(dir, `${id}.json`);
  const stamp = mtime(file);
  const hit = cache.get(id);
  if (hit && hit.stamp === stamp) return hit;
  if (!stamp) return null;
  const data = JSON.parse(fs.readFileSync(file, 'utf8'));
  const world = new CollisionWorld(data.colliders);
  const b = data.bounds;
  const nav = new NavGrid(world, [b[0] - 1, b[1] - 1, b[2] + 1, b[3] + 1]);
  const entry = { id, stamp, data, world, nav };
  cache.set(id, entry);
  return entry;
}

// Maps the lobby offers: the official three when built, plus any other JSON (dev sandbox etc).
export function availableMaps(dev) {
  const files = fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => f.endsWith('.json')) : [];
  const ids = files.map((f) => f.replace(/\.json$/, ''));
  const out = [];
  for (const m of MAPS) if (ids.includes(m.id)) out.push(m);
  if (dev || out.length === 0) {
    for (const id of ids) {
      if (!MAPS.some((m) => m.id === id)) out.push({ id, name: id[0].toUpperCase() + id.slice(1), blurb: 'Development map.' });
    }
  }
  return out;
}
