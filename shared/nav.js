// Grid navigation built from the collision boxes. Used by server bots and the map validator.
import { PLAYER } from './constants.js';

const DIRS = [
  [1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1],
  [1, 1, Math.SQRT2], [1, -1, Math.SQRT2], [-1, 1, Math.SQRT2], [-1, -1, Math.SQRT2],
];

export class NavGrid {
  constructor(world, bounds, cell = 0.5) {
    this.world = world;
    this.cell = cell;
    this.x0 = bounds[0];
    this.z0 = bounds[1];
    this.w = Math.ceil((bounds[2] - bounds[0]) / cell);
    this.h = Math.ceil((bounds[3] - bounds[1]) / cell);
    this.floor = new Float32Array(this.w * this.h).fill(NaN);
    const r = PLAYER.radius, ph = PLAYER.height;
    for (let j = 0; j < this.h; j++) {
      for (let i = 0; i < this.w; i++) {
        const x = this.x0 + (i + 0.5) * cell, z = this.z0 + (j + 0.5) * cell;
        const tops = [];
        world.query(x - 0.01, z - 0.01, x + 0.01, z + 0.01, (b) => {
          if (x >= b[0] && x <= b[3] && z >= b[2] && z <= b[5]) tops.push(b[4]);
        });
        tops.sort((a, b) => a - b);
        for (const t of tops) {
          if (!world.overlaps(x, t + 0.02, z, r, ph - 0.04)) {
            this.floor[j * this.w + i] = t;
            break;
          }
        }
      }
    }
  }

  index(x, z) {
    const i = Math.floor((x - this.x0) / this.cell), j = Math.floor((z - this.z0) / this.cell);
    if (i < 0 || j < 0 || i >= this.w || j >= this.h) return -1;
    return j * this.w + i;
  }

  center(idx) {
    const i = idx % this.w, j = (idx / this.w) | 0;
    return [this.x0 + (i + 0.5) * this.cell, this.floor[idx], this.z0 + (j + 0.5) * this.cell];
  }

  walkable(idx) {
    return idx >= 0 && !Number.isNaN(this.floor[idx]);
  }

  // Nearest walkable cell to (x, z) within `radius` metres whose floor is near y.
  nearest(x, y, z, radius = 2) {
    const c = this.index(x, z);
    if (this.walkable(c) && Math.abs(this.floor[c] - y) < 1.2) return c;
    const R = Math.ceil(radius / this.cell);
    const ci = Math.floor((x - this.x0) / this.cell), cj = Math.floor((z - this.z0) / this.cell);
    let best = -1, bd = Infinity;
    for (let dj = -R; dj <= R; dj++) {
      for (let di = -R; di <= R; di++) {
        const i = ci + di, j = cj + dj;
        if (i < 0 || j < 0 || i >= this.w || j >= this.h) continue;
        const idx = j * this.w + i;
        if (!this.walkable(idx) || Math.abs(this.floor[idx] - y) > 1.6) continue;
        const d = di * di + dj * dj;
        if (d < bd) { bd = d; best = idx; }
      }
    }
    return best;
  }

  _step(a, di, dj) {
    const i = (a % this.w) + di, j = ((a / this.w) | 0) + dj;
    if (i < 0 || j < 0 || i >= this.w || j >= this.h) return -1;
    const b = j * this.w + i;
    if (!this.walkable(b) || Math.abs(this.floor[b] - this.floor[a]) > PLAYER.stepHeight) return -1;
    if (di && dj) {
      const c1 = a + di, c2 = a + dj * this.w;
      if (!this.walkable(c1) || !this.walkable(c2)) return -1;
    }
    return b;
  }

  // Flood fill from a cell; returns Uint8Array mask of reachable cells.
  reach(start) {
    const seen = new Uint8Array(this.w * this.h);
    if (!this.walkable(start)) return seen;
    const q = [start];
    seen[start] = 1;
    while (q.length) {
      const a = q.pop();
      for (const [di, dj] of DIRS) {
        const b = this._step(a, di, dj);
        if (b >= 0 && !seen[b]) { seen[b] = 1; q.push(b); }
      }
    }
    return seen;
  }

  // A* path between world points; returns array of [x,y,z] waypoints (smoothed) or null.
  path(from, to, maxNodes = 20000) {
    const s = this.nearest(from[0], from[1], from[2]);
    const t = this.nearest(to[0], to[1], to[2]);
    if (s < 0 || t < 0) return null;
    const n = this.w * this.h;
    const g = new Float32Array(n).fill(Infinity);
    const came = new Int32Array(n).fill(-1);
    const closed = new Uint8Array(n);
    const heap = new MinHeap();
    const tx = t % this.w, tz = (t / this.w) | 0;
    const hfn = (a) => {
      const dx = Math.abs((a % this.w) - tx), dz = Math.abs(((a / this.w) | 0) - tz);
      return Math.max(dx, dz) + (Math.SQRT2 - 1) * Math.min(dx, dz);
    };
    g[s] = 0;
    heap.push(s, hfn(s));
    let expanded = 0;
    while (heap.size) {
      const a = heap.pop();
      if (a === t) break;
      if (closed[a]) continue;
      closed[a] = 1;
      if (++expanded > maxNodes) return null;
      for (const [di, dj, cost] of DIRS) {
        const b = this._step(a, di, dj);
        if (b < 0 || closed[b]) continue;
        const ng = g[a] + cost;
        if (ng < g[b]) {
          g[b] = ng;
          came[b] = a;
          heap.push(b, ng + hfn(b));
        }
      }
    }
    if (came[t] < 0 && s !== t) return null;
    const cells = [];
    for (let c = t; c >= 0; c = came[c]) {
      cells.push(c);
      if (c === s) break;
    }
    cells.reverse();
    return this.smooth(cells.map((c) => this.center(c)));
  }

  smooth(pts) {
    if (pts.length <= 2) return pts;
    const out = [pts[0]];
    let anchor = 0;
    for (let i = 2; i < pts.length; i++) {
      const a = pts[anchor], b = pts[i];
      const clear = Math.abs(b[1] - a[1]) < 0.05 && this._clearWide(a, b);
      if (!clear) {
        out.push(pts[i - 1]);
        anchor = i - 1;
      }
    }
    out.push(pts[pts.length - 1]);
    return out;
  }

  _clearWide(a, b) {
    const w = this.world;
    const y = a[1] + 0.6;
    const dx = b[0] - a[0], dz = b[2] - a[2];
    const len = Math.hypot(dx, dz) || 1;
    const ox = (-dz / len) * PLAYER.radius, oz = (dx / len) * PLAYER.radius;
    if (!w.segmentClear(a[0] + ox, y, a[2] + oz, b[0] + ox, y, b[2] + oz)) return false;
    if (!w.segmentClear(a[0] - ox, y, a[2] - oz, b[0] - ox, y, b[2] - oz)) return false;
    // make sure the floor doesn't vanish along the way
    const steps = Math.ceil(len / this.cell);
    for (let k = 1; k < steps; k++) {
      const idx = this.index(a[0] + (dx * k) / steps, a[2] + (dz * k) / steps);
      if (!this.walkable(idx) || Math.abs(this.floor[idx] - a[1]) > PLAYER.stepHeight) return false;
    }
    return true;
  }

  randomWalkable(rng = Math.random, mask = null) {
    for (let tries = 0; tries < 500; tries++) {
      const idx = (rng() * this.w * this.h) | 0;
      if (this.walkable(idx) && (!mask || mask[idx])) return this.center(idx);
    }
    return null;
  }
}

class MinHeap {
  constructor() { this.k = []; this.p = []; }
  get size() { return this.k.length; }
  push(key, pri) {
    const k = this.k, p = this.p;
    let i = k.length;
    k.push(key); p.push(pri);
    while (i > 0) {
      const par = (i - 1) >> 1;
      if (p[par] <= pri) break;
      k[i] = k[par]; p[i] = p[par];
      i = par;
    }
    k[i] = key; p[i] = pri;
  }
  pop() {
    const k = this.k, p = this.p;
    const top = k[0];
    const lk = k.pop(), lp = p.pop();
    if (k.length) {
      let i = 0;
      const n = k.length;
      for (;;) {
        let c = 2 * i + 1;
        if (c >= n) break;
        if (c + 1 < n && p[c + 1] < p[c]) c++;
        if (p[c] >= lp) break;
        k[i] = k[c]; p[i] = p[c];
        i = c;
      }
      k[i] = lk; p[i] = lp;
    }
    return top;
  }
}
