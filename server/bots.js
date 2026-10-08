// Server-side bots. They act through the same Game methods as human players and only use
// information their role is allowed to have (hunter bots can't see hidden ghosts).
import { GHOST, HUNTER, PLAYER, RELIC, ROLES, PHASE } from '../shared/constants.js';

const SKILL = {
  easy: { reaction: 1.1, aimError: 0.16, shootChance: 0.35, manipRate: 0.12 },
  normal: { reaction: 0.6, aimError: 0.09, shootChance: 0.55, manipRate: 0.2 },
  hard: { reaction: 0.35, aimError: 0.05, shootChance: 0.75, manipRate: 0.3 },
};

export class Bot {
  constructor(game, player, opts = {}) {
    this.game = game;
    this.p = player;
    this.skill = SKILL[opts.skill] || SKILL.normal;
    this.body = { pos: player.pos, vel: { x: 0, y: 0, z: 0 }, onGround: true };
    this.path = null;
    this.pathGoal = null;
    this.pathAge = 0;
    this.stuck = 0;
    this.lastPos = { ...player.pos };
    this.goal = null;
    this.goalKind = 'wander';
    this.goalUntil = 0;
    this.noises = [];          // hunter: recent sounds {p, t, weight}
    this.nextThink = 0;
    this.nextSnap = 2 + Math.random() * 6;
    this.nextManip = 3 + Math.random() * 4;
    this.aimTarget = null;
    this.aimSince = 0;
    this.lookYaw = player.yaw;
  }

  onTeleport() {
    this.body.pos = this.p.pos;
    this.body.vel.x = this.body.vel.y = this.body.vel.z = 0;
    this.path = null;
    this.lastPos = { ...this.p.pos };
  }

  hear(ev) {
    if (this.p.role !== ROLES.HUNTER) return;
    const t = this.game.time;
    // humans localise sounds roughly; so do bots
    const fuzz = (pt, k = 1.2) => [pt[0] + (Math.random() - 0.5) * 2 * k, pt[1], pt[2] + (Math.random() - 0.5) * 2 * k];
    if (ev.p && ev.e !== 'channel') ev = { ...ev, p: fuzz(ev.p, ev.e === 'drip' ? 0.3 : 1.4) };
    if (ev.e === 'snap') this.noises.push({ p: ev.p, t, w: 3 });
    else if (ev.e === 'whistle') this.noises.push({ p: ev.p, t, w: 2 });
    else if (ev.e === 'drip') {
      // drips are only noticed when they're close and in view
      const e = this.game.eye(this.p);
      const d = Math.hypot(ev.p[0] - e.x, ev.p[2] - e.z);
      if (d < 16 && this.game.world.segmentClear(e.x, e.y, e.z, ev.p[0], ev.p[1] + 0.2, ev.p[2])) this.noises.push({ p: ev.p, t, w: 4 });
    }
    else if (ev.e === 'channel') this.noises.push({ p: ev.p, t, w: 6 });
    else if (ev.e === 'manip') {
      const prop = this.game.props.get(ev.prop);
      if (!prop) return;
      const d = Math.hypot(prop.pos[0] - this.p.pos.x, prop.pos[2] - this.p.pos.z);
      // big manipulations are heard across the map, subtle ones only noticed when close
      if (ev.k === 'b' && d < 35) this.noises.push({ p: prop.pos, t, w: 2 });
      else if (ev.k === 's' && d < 12 && Math.random() < 0.5) this.noises.push({ p: prop.pos, t, w: 1.5 });
    }
    if (this.noises.length > 20) this.noises.shift();
  }

  update(dt) {
    const g = this.game;
    const p = this.p;
    if (g.phase === PHASE.RESULTS) return;
    const frozen = g.isFrozen(p);
    const blind = p.role === ROLES.HUNTER && g.phase === PHASE.BLIND;
    if (frozen || blind) {
      this.body.vel.x = this.body.vel.z = 0;
      this.physics(dt);
      return;
    }
    if (g.time >= this.nextThink) {
      this.nextThink = g.time + 0.4 + Math.random() * 0.3;
      if (g.lobby) this.thinkLobby();
      else if (p.role === ROLES.GHOST) this.thinkGhost();
      else this.thinkHunter();
    }
    if (p.role === ROLES.HUNTER) this.combat(dt);
    else this.ghostActions();
    this.steer(dt);
    this.physics(dt);
  }

  // ------------------------------------------------------------ waiting room: mill about
  thinkLobby() {
    const g = this.game;
    if (!this.goal || g.time > this.goalUntil || this.arrived()) {
      if (Math.random() < 0.35) {
        this.goal = null; // stand around for a bit
        this.path = null;
        this.goalUntil = g.time + 2 + Math.random() * 4;
        return;
      }
      const pt = g.nav.randomWalkable(Math.random);
      if (pt) this.setGoal(pt, 'wander', 6 + Math.random() * 6);
    }
  }

  // ------------------------------------------------------------ ghost brain
  thinkGhost() {
    const g = this.game, p = this.p, rel = g.relic;
    if (g.inPenalty(p)) { this.goal = null; return; }
    const hunters = g.hunters;
    const nearestHunter = minBy(hunters, (h) => d2(h.pos, p.pos));
    const hd = nearestHunter ? Math.sqrt(d2(nearestHunter.pos, p.pos)) : 99;
    if (rel.holder === p.id) {
      const cap = g.map.flagPoints[rel.capture].pos;
      this.setGoal([cap[0], cap[1] - 1, cap[2]], 'deliver');
      return;
    }
    // flee a hunter that is close and facing us
    if (nearestHunter && hd < 6) {
      const away = norm2(p.pos.x - nearestHunter.pos.x, p.pos.z - nearestHunter.pos.z);
      const target = [p.pos.x + away[0] * 8, p.pos.y, p.pos.z + away[1] * 8];
      if (this.setGoal(target, 'flee', 2)) return;
    }
    if (!rel.holder && p.stamina >= RELIC.minPickupStamina + 1) {
      // only the closest couple of ghosts go for the relic
      const ghosts = g.ghosts.filter((o) => g.active(o) && o.stamina >= RELIC.minPickupStamina);
      ghosts.sort((a, b) => d2(a.pos, rel.pos) - d2(b.pos, rel.pos));
      const rank = ghosts.indexOf(p);
      if (rank >= 0 && rank < 1 + (ghosts.length > 3 ? 1 : 0)) {
        this.setGoal([rel.pos.x, rel.pos.y - 0.9, rel.pos.z], 'fetch');
        return;
      }
    }
    if (rel.holder && rel.holder !== p.id) {
      // escort loosely: stay 6-10 m away from the carrier and distract
      const c = g.players.get(rel.holder);
      if (c && (this.goalKind !== 'escort' || g.time > this.goalUntil)) {
        const a = Math.random() * Math.PI * 2;
        const t = [c.pos.x + Math.cos(a) * 8, c.pos.y, c.pos.z + Math.sin(a) * 8];
        this.setGoal(t, 'escort', 5);
        return;
      }
    }
    if (!this.goal || g.time > this.goalUntil || this.arrived()) {
      const pt = g.nav.randomWalkable(Math.random);
      if (pt) this.setGoal(pt, 'wander', 8 + Math.random() * 8);
    }
  }

  ghostActions() {
    const g = this.game, p = this.p;
    if (!g.active(p) || (g.phase !== PHASE.PLAY && !g.lobby)) return;
    if (g.time > this.nextSnap) {
      this.nextSnap = g.time + 4 + Math.random() * 10;
      // a sensible ghost doesn't snap right next to a hunter
      const hunterNear = g.hunters.some((h) => Math.sqrt(d2(h.pos, p.pos)) < GHOST.snapRadius + 2);
      if (!hunterNear || Math.random() < 0.15) g.snap(p);
    }
    if (g.time > this.nextManip) {
      this.nextManip = g.time + 2 + Math.random() * 5;
      if (Math.random() < this.skill.manipRate * 3) {
        const e = g.eye(p);
        const near = [...g.props.values()].filter((pr) => Math.hypot(pr.pos[0] - e.x, pr.pos[1] - e.y, pr.pos[2] - e.z) < GHOST.manipReach - 0.5);
        if (near.length) {
          const pr = near[(Math.random() * near.length) | 0];
          const carrierFar = g.lobby || (g.relic.holder && g.relic.holder !== p.id);
          const big = g.time >= p.nextBig && carrierFar && Math.random() < 0.5;
          g.manip(p, pr.id, big ? 'b' : 's');
        }
      }
    }
    if (Math.random() < 0.0015) g.whistle(p);
  }

  // ------------------------------------------------------------ hunter brain
  thinkHunter() {
    const g = this.game, p = this.p;
    // relic hum is audible when close
    const rel = g.relic;
    if (rel.holder) {
      const h = g.players.get(rel.holder);
      if (h && Math.sqrt(d2(h.pos, p.pos)) < RELIC.humRadius) {
        this.noises.push({ p: [h.pos.x + (Math.random() - 0.5) * 2.4, h.pos.y + 1, h.pos.z + (Math.random() - 0.5) * 2.4], t: g.time, w: 5 });
      }
    }
    // pick the freshest, weightiest noise
    let best = null, bs = 0;
    for (const n of this.noises) {
      const age = g.time - n.t;
      if (age > 8) continue;
      const d = Math.hypot(n.p[0] - p.pos.x, n.p[2] - p.pos.z);
      const s = n.w / (1 + age * 0.5) / (1 + d * 0.04);
      if (s > bs) { bs = s; best = n; }
    }
    this.noises = this.noises.filter((n) => g.time - n.t < 8);
    if (best && (this.goalKind !== 'investigate' || bs > 0.6)) {
      this.setGoal([best.p[0], best.p[1] - 1, best.p[2]], 'investigate', 4);
      this.aimTarget = { x: best.p[0], y: best.p[1], z: best.p[2], t: g.time, noise: true };
      return;
    }
    if (!this.goal || g.time > this.goalUntil || this.arrived()) {
      const fp = g.map.flagPoints;
      const altar = Math.random() < 0.6;
      const pick = altar ? fp[(Math.random() * fp.length) | 0].pos : g.nav.randomWalkable(Math.random);
      if (pick) this.setGoal([pick[0], pick[1] - (altar ? 1 : 0), pick[2]], 'patrol', 10 + Math.random() * 8);
    }
  }

  combat() {
    const g = this.game, p = this.p;
    if (g.phase !== PHASE.PLAY) return;
    const eye = g.eye(p);
    // visible ghosts are fair game
    let target = null, td = Infinity;
    for (const o of g.ghosts) {
      if (!g.active(o) || !g.visibleTo(p, o)) continue;
      const d = Math.sqrt(d2(o.pos, p.pos));
      if (d < td && g.world.segmentClear(eye.x, eye.y, eye.z, o.pos.x, o.pos.y + 1, o.pos.z)) { td = d; target = o; }
    }
    if (target) {
      this.aimTarget = { x: target.pos.x, y: target.pos.y + 1, z: target.pos.z, t: g.time, noise: false };
      if (td > HUNTER.rayRange * 0.8) this.setGoal([target.pos.x, target.pos.y, target.pos.z], 'chase', 2);
    }
    const a = this.aimTarget;
    if (!a) return;
    if (g.time - a.t > 3) { this.aimTarget = null; return; }
    const dx = a.x - eye.x, dy = a.y - eye.y, dz = a.z - eye.z;
    const dist = Math.hypot(dx, dy, dz);
    const yaw = Math.atan2(-dx, -dz);
    p.yaw = approachAngle(p.yaw, yaw, 0.25);
    p.pitch = Math.atan2(dy, Math.hypot(dx, dz));
    if (this.aimSince === 0) this.aimSince = g.time;
    const aligned = Math.abs(angleDiff(p.yaw, yaw)) < 0.12;
    const ready = g.time >= p.nextRay && g.time - this.aimSince > this.skill.reaction;
    const chance = a.noise ? (dist < 7 ? this.skill.shootChance * 0.5 : 0) : 1;
    if (aligned && ready && dist < HUNTER.rayRange && Math.random() < chance * 0.25) {
      const e = this.skill.aimError;
      const yawN = p.yaw + (Math.random() - 0.5) * e * 2;
      const pitN = p.pitch + (Math.random() - 0.5) * e;
      g.ray(p, [-Math.sin(yawN) * Math.cos(pitN), Math.sin(pitN), -Math.cos(yawN) * Math.cos(pitN)]);
      this.aimSince = 0;
      if (a.noise) this.aimTarget = null;
    }
  }

  // ------------------------------------------------------------ movement
  setGoal(pt, kind, hold = 6) {
    if (!pt) return false;
    this.goal = { x: pt[0], y: pt[1], z: pt[2] };
    this.goalKind = kind;
    this.goalUntil = this.game.time + hold;
    if (!this.pathGoal || d2(this.pathGoal, this.goal) > 1 || this.game.time - this.pathAge > 2.5) this.repath();
    return !!this.path;
  }

  repath() {
    const g = this.game, p = this.p;
    this.pathAge = g.time;
    this.pathGoal = { ...this.goal };
    const path = g.nav.path([p.pos.x, p.pos.y, p.pos.z], [this.goal.x, this.goal.y, this.goal.z]);
    this.path = path ? path.slice(1) : null;
  }

  arrived() {
    return !this.goal || Math.hypot(this.goal.x - this.p.pos.x, this.goal.z - this.p.pos.z) < 1.2;
  }

  steer(dt) {
    const p = this.p, g = this.game;
    const speed = p.role === ROLES.HUNTER ? HUNTER.speed * 0.92 : (p.carrying ? GHOST.carrySpeed : GHOST.speed) * 0.9;
    let vx = 0, vz = 0;
    if (this.path && this.path.length) {
      const wp = this.path[0];
      const dx = wp[0] - p.pos.x, dz = wp[2] - p.pos.z;
      const d = Math.hypot(dx, dz);
      if (d < 0.45) this.path.shift();
      else { vx = (dx / d) * speed; vz = (dz / d) * speed; }
    } else if (this.goal && !this.arrived() && g.time - this.pathAge > 1.5) {
      this.repath();
    }
    // ghosts keep a little distance from one another to avoid exposing themselves
    if (p.role === ROLES.GHOST && p.near && p.clump > GHOST.clumpLimit * 0.4) {
      for (const o of g.ghosts) {
        if (o === p || !g.active(o)) continue;
        const dx = p.pos.x - o.pos.x, dz = p.pos.z - o.pos.z;
        const d = Math.hypot(dx, dz);
        if (d < GHOST.seeRadius && d > 0.01) { vx += (dx / d) * speed * 0.8; vz += (dz / d) * speed * 0.8; }
      }
      const s = Math.hypot(vx, vz);
      if (s > speed) { vx *= speed / s; vz *= speed / s; }
    }
    this.body.vel.x = vx;
    this.body.vel.z = vz;
    // hop up ledges and steep stair treads the walk can't step over
    const wp = this.path?.[0];
    if (wp && this.body.onGround && wp[1] - p.pos.y > PLAYER.stepHeight * 0.8 && Math.hypot(wp[0] - p.pos.x, wp[2] - p.pos.z) < 1.4) {
      this.body.vel.y = p.role === ROLES.GHOST ? GHOST.jump : PLAYER.jump;
    }
    if (Math.hypot(vx, vz) > 0.1 && !(p.role === ROLES.HUNTER && this.aimTarget)) {
      p.yaw = approachAngle(p.yaw, Math.atan2(-vx, -vz), 0.2);
      p.pitch *= 0.9;
    }
    // stuck detection
    this.stuck = Math.hypot(p.pos.x - this.lastPos.x, p.pos.z - this.lastPos.z) < speed * dt * 0.2 && Math.hypot(vx, vz) > 0.1 ? this.stuck + dt : 0;
    this.lastPos = { ...p.pos };
    if (this.stuck > 1.2) {
      this.stuck = 0;
      this.path = null;
      const pt = g.nav.randomWalkable(Math.random);
      if (pt) this.setGoal(pt, 'unstick', 3);
    }
  }

  physics(dt) {
    const p = this.p, g = this.game;
    const grav = p.role === ROLES.GHOST ? GHOST.gravity : PLAYER.gravity;
    this.body.pos = p.pos;
    this.body.vel.y -= grav * dt;
    g.world.move(this.body, dt, PLAYER.radius, PLAYER.height, PLAYER.stepHeight);
    if (this.body.onGround && this.body.vel.y < 0) this.body.vel.y = 0;
    if (p.pos.y < -20) g.teleport(p, (p.role === ROLES.HUNTER ? g.map.spawns.hunter : g.map.spawns.ghost)[0]);
    p.lastMove = g.time;
  }
}

function d2(a, b) {
  const ax = a.x ?? a[0], az = a.z ?? a[2], bx = b.x ?? b[0], bz = b.z ?? b[2];
  return (ax - bx) ** 2 + (az - bz) ** 2;
}

function norm2(x, z) {
  const l = Math.hypot(x, z) || 1;
  return [x / l, z / l];
}

function minBy(arr, f) {
  let best = null, bv = Infinity;
  for (const a of arr) { const v = f(a); if (v < bv) { bv = v; best = a; } }
  return best;
}

function angleDiff(a, b) {
  let d = b - a;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  return d;
}

function approachAngle(a, b, k) {
  return a + angleDiff(a, b) * k;
}
