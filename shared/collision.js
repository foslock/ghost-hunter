// Axis-aligned box world used for player movement (client) and line-of-sight checks (server).
// Boxes are [minX, minY, minZ, maxX, maxY, maxZ] in three.js (Y-up) coordinates.

const CELL = 4;
const EPS = 1e-4;

export class CollisionWorld {
  constructor(boxes) {
    this.boxes = boxes.map((b) => Float64Array.from(b));
    this.grid = new Map();
    this.stamp = new Uint32Array(this.boxes.length);
    this.stampId = 0;
    this.boxes.forEach((b, i) => {
      for (let cx = Math.floor(b[0] / CELL); cx <= Math.floor(b[3] / CELL); cx++) {
        for (let cz = Math.floor(b[2] / CELL); cz <= Math.floor(b[5] / CELL); cz++) {
          const key = cx * 73856093 ^ cz * 19349663;
          let list = this.grid.get(key);
          if (!list) this.grid.set(key, (list = []));
          list.push(i);
        }
      }
    });
  }

  // Calls fn(box) once for every box whose grid cells overlap the XZ rectangle.
  query(minX, minZ, maxX, maxZ, fn) {
    const id = ++this.stampId;
    for (let cx = Math.floor(minX / CELL); cx <= Math.floor(maxX / CELL); cx++) {
      for (let cz = Math.floor(minZ / CELL); cz <= Math.floor(maxZ / CELL); cz++) {
        const list = this.grid.get(cx * 73856093 ^ cz * 19349663);
        if (!list) continue;
        for (const i of list) {
          if (this.stamp[i] === id) continue;
          this.stamp[i] = id;
          if (fn(this.boxes[i]) === false) return;
        }
      }
    }
  }

  // True if a body with feet at (x,y,z) overlaps any box.
  overlaps(x, y, z, r, h) {
    let hit = false;
    this.query(x - r, z - r, x + r, z + r, (b) => {
      if (x - r < b[3] - EPS && x + r > b[0] + EPS && y < b[4] - EPS && y + h > b[1] + EPS &&
          z - r < b[5] - EPS && z + r > b[2] + EPS) {
        hit = true;
        return false;
      }
    });
    return hit;
  }

  // Moves a body (feet position) by its velocity, resolving collisions axis by axis.
  // body = { pos: {x,y,z}, vel: {x,y,z}, onGround }
  move(body, dt, r, h, stepHeight) {
    const speed = Math.hypot(body.vel.x, body.vel.z, body.vel.y);
    const steps = Math.max(1, Math.ceil((speed * dt) / (r * 0.9)));
    const sdt = dt / steps;
    let grounded = false;
    for (let s = 0; s < steps; s++) {
      this._axis(body, 'x', body.vel.x * sdt, r, h, stepHeight);
      this._axis(body, 'z', body.vel.z * sdt, r, h, stepHeight);
      if (this._vertical(body, body.vel.y * sdt, r, h)) grounded = true;
    }
    body.onGround = grounded;
    return body;
  }

  _axis(body, axis, d, r, h, stepHeight) {
    if (d === 0) return;
    const p = body.pos;
    p[axis] += d;
    const ai = axis === 'x' ? 0 : 2;
    this.query(p.x - r, p.z - r, p.x + r, p.z + r, (b) => {
      if (!(p.x - r < b[3] - EPS && p.x + r > b[0] + EPS && p.y < b[4] - EPS && p.y + h > b[1] + EPS &&
            p.z - r < b[5] - EPS && p.z + r > b[2] + EPS)) return;
      const rise = b[4] - p.y;
      if (body.onGround && rise > 0 && rise <= stepHeight && !this.overlaps(p.x, b[4] + EPS * 2, p.z, r, h)) {
        p.y = b[4] + EPS;
        return;
      }
      p[axis] = d > 0 ? b[ai] - r - EPS * 2 : b[ai + 3] + r + EPS * 2;
    });
  }

  _vertical(body, d, r, h) {
    const p = body.pos;
    p.y += d;
    let grounded = false;
    this.query(p.x - r, p.z - r, p.x + r, p.z + r, (b) => {
      if (!(p.x - r < b[3] - EPS && p.x + r > b[0] + EPS && p.y < b[4] - EPS && p.y + h > b[1] + EPS &&
            p.z - r < b[5] - EPS && p.z + r > b[2] + EPS)) return;
      if (d <= 0) {
        p.y = b[4];
        grounded = true;
        if (body.vel.y < 0) body.vel.y = 0;
      } else {
        p.y = b[1] - h - EPS;
        if (body.vel.y > 0) body.vel.y = 0;
      }
    });
    // A tiny probe below the feet keeps us grounded while walking over seams.
    if (!grounded && d <= 0 && this.overlaps(p.x, p.y - 0.03, p.z, r * 0.95, 0.04)) grounded = true;
    return grounded;
  }

  // Distance along a normalised direction to the first box, or Infinity.
  raycast(ox, oy, oz, dx, dy, dz, maxDist) {
    const ex = ox + dx * maxDist, ez = oz + dz * maxDist;
    let best = maxDist;
    const ix = 1 / (dx || 1e-12), iy = 1 / (dy || 1e-12), iz = 1 / (dz || 1e-12);
    this.query(Math.min(ox, ex), Math.min(oz, ez), Math.max(ox, ex), Math.max(oz, ez), (b) => {
      let t1 = (b[0] - ox) * ix, t2 = (b[3] - ox) * ix;
      let tmin = Math.min(t1, t2), tmax = Math.max(t1, t2);
      t1 = (b[1] - oy) * iy; t2 = (b[4] - oy) * iy;
      tmin = Math.max(tmin, Math.min(t1, t2)); tmax = Math.min(tmax, Math.max(t1, t2));
      t1 = (b[2] - oz) * iz; t2 = (b[5] - oz) * iz;
      tmin = Math.max(tmin, Math.min(t1, t2)); tmax = Math.min(tmax, Math.max(t1, t2));
      if (tmax >= Math.max(tmin, 0) && tmin < best) best = Math.max(tmin, 0);
    });
    return best < maxDist ? best : Infinity;
  }

  segmentClear(ax, ay, az, bx, by, bz) {
    const dx = bx - ax, dy = by - ay, dz = bz - az;
    const len = Math.hypot(dx, dy, dz);
    if (len < 1e-6) return true;
    return this.raycast(ax, ay, az, dx / len, dy / len, dz / len, len) === Infinity;
  }

  // Highest walkable surface under (x,z) at or below maxY, or -Infinity.
  groundHeight(x, z, maxY, r = 0.05) {
    let best = -Infinity;
    this.query(x - r, z - r, x + r, z + r, (b) => {
      if (x + r > b[0] && x - r < b[3] && z + r > b[2] && z - r < b[5] && b[4] <= maxY && b[4] > best) best = b[4];
    });
    return best;
  }
}
