// Authoritative round simulation: roles, relic, freezing, penalty box, exposure, sounds, props.
// Clients own their movement (the server sanity-checks it); everything else is decided here.
import { GHOST, HUNTER, PF, PHASE, PLAYER, RELIC, ROLES, ROUND, SNAPSHOT_RATE } from '../shared/constants.js';
import { ARCHETYPES } from '../shared/archetypes.js';
import { Bot } from './bots.js';

const r2 = (v) => Math.round(v * 100) / 100;
const r3 = (v) => Math.round(v * 1000) / 1000;

// A Game is either a round (`mode: 'round'`) or the always-running waiting room (`mode: 'lobby'`),
// where everyone is visible, players come and go, and nothing has consequences.
export class Game {
  constructor(room, mapEntry, settings, roster, rng = Math.random, mode = 'round') {
    this.room = room;
    this.map = mapEntry.data;
    this.world = mapEntry.world;
    this.nav = mapEntry.nav;
    this.settings = settings;
    this.rng = rng;
    this.lobby = mode === 'lobby';
    this.time = 0;
    this.phase = this.lobby ? PHASE.LOBBY : PHASE.BLIND;
    this.phaseEnd = this.lobby ? Infinity : HUNTER.blindTime;
    this.timeLeft = this.lobby ? Infinity : settings.roundTime;
    this.captures = 0;
    this.result = null;
    this.snapAcc = 0;
    this.players = new Map();
    this.props = new Map(this.map.props.map((p) => [p.id, { ...p, bigUntil: -1 }]));
    this.drips = 0;
    this.history = [];
    this.spawnQueue = { hunter: [...this.map.spawns.hunter], ghost: shuffle([...this.map.spawns.ghost], rng) };
    this.spawnIndex = { hunter: 0, ghost: 0 };
    for (const r of roster) this.addPlayer(r);
    this.relic = null;
    if (this.lobby) return;

    // relic pairs: precompute every altar pair that is far enough apart
    const fp = this.map.flagPoints;
    let maxD = 0;
    for (let i = 0; i < fp.length; i++) for (let j = i + 1; j < fp.length; j++) maxD = Math.max(maxD, hdist(fp[i].pos, fp[j].pos));
    this.pairs = [];
    for (let i = 0; i < fp.length; i++) for (let j = 0; j < fp.length; j++) {
      if (i !== j && hdist(fp[i].pos, fp[j].pos) >= maxD * RELIC.minPairFraction) this.pairs.push([i, j]);
    }
    this.relic = { state: 'home', pos: null, holder: null, spawn: 0, capture: 1, channel: 0, channeling: false, lastHolder: null, dropTime: -99, lastDrip: 0 };
    this.newPair();
  }

  nextSpawn(role) {
    const list = this.spawnQueue[role] || this.spawnQueue.ghost;
    const i = this.spawnIndex[role]++;
    return list[i % list.length];
  }

  addPlayer(r) {
    const sp = this.nextSpawn(r.role);
    const p = {
      id: r.id, name: r.name, role: r.role, color: r.color, isBot: !!r.bot,
      pos: { x: sp[0], y: sp[1], z: sp[2] }, yaw: sp[3] ?? 0, pitch: 0,
      lastMove: this.time, tpSeq: 1, outbox: [],
      frozenUntil: -1, penaltyUntil: -1, exposedUntil: -1, clump: 0, near: false,
      stamina: this.settings.carryLimit, carrying: false,
      nextWhistle: 0, nextBig: 0, nextSubtle: 0, nextSnap: 0, nextRay: 0, padTime: 0, padRole: null,
      stats: { freezes: 0, frozen: 0, captures: 0, carry: 0, snaps: 0, whistles: 0, manips: 0, shots: 0 },
    };
    if (r.bot) p.bot = new Bot(this, p, r.bot);
    this.players.set(r.id, p);
    return p;
  }

  // waiting room only: change a player's team in place
  setRole(id, role) {
    const p = this.players.get(id);
    if (!p || p.role === role) return;
    p.role = role;
    p.frozenUntil = -1;
    p.nextWhistle = p.nextBig = p.nextRay = 0;
    p.padBlock = true; // pads only count again once you've stepped off them
    if (p.bot) p.bot.onTeleport();
  }

  // ------------------------------------------------------------ helpers
  get ghosts() { return [...this.players.values()].filter((p) => p.role === ROLES.GHOST); }
  get hunters() { return [...this.players.values()].filter((p) => p.role === ROLES.HUNTER); }
  isFrozen(p) { return p.frozenUntil > this.time; }
  inPenalty(p) { return p.penaltyUntil > this.time; }
  isExposed(p) { return p.exposedUntil > this.time; }
  active(p) { return !this.isFrozen(p) && !this.inPenalty(p); }
  playing() { return this.phase === PHASE.PLAY || this.phase === PHASE.BLIND || this.phase === PHASE.LOBBY; }

  eye(p) {
    return { x: p.pos.x, y: p.pos.y + (p.role === ROLES.GHOST ? 1.35 : PLAYER.eye), z: p.pos.z };
  }

  newPair(avoid = []) {
    let options = this.pairs.filter(([a, b]) => !avoid.includes(a) && !avoid.includes(b));
    if (!options.length) options = this.pairs;
    if (!options.length) options = [[0, Math.min(1, this.map.flagPoints.length - 1)]];
    const [s, c] = options[(this.rng() * options.length) | 0];
    const rel = this.relic;
    if (rel.holder) {
      const h = this.players.get(rel.holder);
      if (h) h.carrying = false;
    }
    rel.spawn = s;
    rel.capture = c;
    rel.state = 'home';
    rel.holder = null;
    rel.channel = 0;
    rel.channeling = false;
    const p = this.map.flagPoints[s].pos;
    rel.pos = { x: p[0], y: p[1], z: p[2] };
  }

  // Queue an event. `to` decides recipients: 'all', 'ghosts', 'hunters', or fn(player).
  emit(ev, to = 'all') {
    for (const p of this.players.values()) {
      if (!(to === 'all' || (to === 'ghosts' && p.role === ROLES.GHOST) || (to === 'hunters' && p.role === ROLES.HUNTER) ||
          (typeof to === 'function' && to(p)))) continue;
      const e = typeof ev === 'function' ? ev(p) : ev;
      if (p.bot) p.bot.hear(e);
      else if (!p.isBot) p.outbox.push(e);
    }
  }

  feed(text, to = 'all', kind = 'info') {
    this.emit({ e: 'feed', text, kind }, to);
  }

  teleport(p, pos, yaw) {
    p.pos = { x: pos[0], y: pos[1], z: pos[2] };
    if (yaw !== undefined) p.yaw = yaw;
    p.tpSeq++;
    p.lastMove = this.time;
    p.lastTpSent = this.time;
    if (!p.isBot) this.room.send(p.id, { t: 'tp', p: [p.pos.x, p.pos.y, p.pos.z], yaw: p.yaw, seq: p.tpSeq });
    if (p.bot) p.bot.onTeleport();
  }

  // ------------------------------------------------------------ input from clients / bots
  onState(p, msg) {
    if (!this.playing() && this.phase !== PHASE.RESULTS) return;
    if (msg.tp !== p.tpSeq) {
      // stale: sent before our last teleport. If it persists the client missed it, so resend.
      if (this.time - (p.lastTpSent || 0) > 1.5) {
        p.lastTpSent = this.time;
        if (!p.isBot) this.room.send(p.id, { t: 'tp', p: [p.pos.x, p.pos.y, p.pos.z], yaw: p.yaw, seq: p.tpSeq });
      }
      return;
    }
    const [x, y, z] = msg.p;
    if (![x, y, z, msg.y, msg.pi].every(Number.isFinite)) return;
    p.yaw = msg.y;
    p.pitch = Math.max(-1.6, Math.min(1.6, msg.pi));
    if (this.isFrozen(p) || (p.role === ROLES.HUNTER && this.phase === PHASE.BLIND)) {
      return; // can't move; client is told via snapshot
    }
    if (y < -20) {
      const list = p.role === ROLES.HUNTER ? this.map.spawns.hunter : this.map.spawns.ghost;
      this.teleport(p, list[(this.rng() * list.length) | 0]);
      return;
    }
    const dt = Math.max(0.05, this.time - p.lastMove);
    const maxSpeed = (p.role === ROLES.HUNTER ? HUNTER.speed : GHOST.speed) * 1.6 + 4;
    const d = Math.hypot(x - p.pos.x, z - p.pos.z);
    // too fast, or the path passes through a wall (knee height clears steps and stairs)
    const ky = Math.max(p.pos.y, y) + 0.6;
    if (d > maxSpeed * dt + 1.5 || (d > 0.05 && !this.world.segmentClear(p.pos.x, ky, p.pos.z, x, ky, z))) {
      this.teleport(p, [p.pos.x, p.pos.y, p.pos.z]);
      return;
    }
    p.pos.x = x; p.pos.y = y; p.pos.z = z;
    p.lastMove = this.time;
  }

  snap(p) {
    if (p.role !== ROLES.GHOST || !this.playing() || this.isFrozen(p) || this.time < p.nextSnap) return;
    p.nextSnap = this.time + 0.12;
    p.stats.snaps++;
    const e = this.eye(p);
    const pos = [r2(e.x), r2(e.y - 0.3), r2(e.z)];
    this.emit((rp) => ({ e: 'snap', p: pos, id: rp.role === ROLES.GHOST ? p.id : undefined }),
      (rp) => rp.id !== p.id && dist3(rp.pos, p.pos) <= GHOST.snapRadius);
  }

  whistle(p) {
    if (p.role !== ROLES.GHOST || !this.playing() || this.isFrozen(p) || this.time < p.nextWhistle) return;
    p.nextWhistle = this.time + GHOST.whistleCooldown;
    p.stats.whistles++;
    const e = this.eye(p);
    const pos = [r2(e.x), r2(e.y - 0.2), r2(e.z)];
    this.emit((rp) => ({ e: 'whistle', p: pos, id: rp.role === ROLES.GHOST ? p.id : undefined }),
      (rp) => rp.id !== p.id && dist3(rp.pos, p.pos) <= GHOST.whistleRadius);
  }

  manip(p, propId, kind) {
    if (p.role !== ROLES.GHOST || !this.playing() || !this.active(p)) return;
    const prop = this.props.get(propId);
    if (!prop || !ARCHETYPES[prop.type]) return;
    const e = this.eye(p);
    const d = Math.hypot(prop.pos[0] - e.x, prop.pos[1] - e.y, prop.pos[2] - e.z);
    if (d > GHOST.manipReach + 2.5) return;
    if (prop.bigUntil > this.time) return;
    if (kind === 'b') {
      if (this.time < p.nextBig) return;
      p.nextBig = this.time + GHOST.bigCooldown;
      prop.bigUntil = this.time + 3;
    } else {
      if (this.time < p.nextSubtle) return;
      p.nextSubtle = this.time + GHOST.subtleRate;
      kind = 's';
    }
    p.stats.manips++;
    this.emit({ e: 'manip', prop: propId, k: kind, seed: (this.rng() * 1e6) | 0 });
  }

  dropRelic(p, reason = 'drop') {
    const rel = this.relic;
    if (!rel || rel.holder !== p.id) return;
    p.carrying = false;
    rel.holder = null;
    rel.lastHolder = p.id;
    rel.dropTime = this.time;
    rel.channel = 0;
    rel.channeling = false;
    rel.state = 'dropped';
    const g = this.world.groundHeight(p.pos.x, p.pos.z, p.pos.y + 0.6, 0.15);
    rel.pos = { x: p.pos.x, y: (Number.isFinite(g) ? g : p.pos.y) + 0.05, z: p.pos.z };
    this.emit({ e: 'relicDrop', id: p.id, reason, p: [r2(rel.pos.x), r2(rel.pos.y), r2(rel.pos.z)] }, 'ghosts');
  }

  ray(p, dir) {
    if (p.role !== ROLES.HUNTER || (this.phase !== PHASE.PLAY && !this.lobby) || this.time < p.nextRay) return;
    if (!Array.isArray(dir) || dir.length !== 3 || !dir.every(Number.isFinite)) return;
    const len = Math.hypot(dir[0], dir[1], dir[2]);
    if (len < 1e-3) return;
    const d = { x: dir[0] / len, y: dir[1] / len, z: dir[2] / len };
    p.nextRay = this.time + HUNTER.rayCooldown;
    p.stats.shots++;
    const o = this.eye(p);
    const hits = [];
    const past = this.pastPositions(0.15);
    for (const g of this.ghosts) {
      if (!this.active(g)) continue;
      const candidates = [g.pos];
      const old = past.get(g.id);
      if (old) candidates.push(old);
      let hit = false;
      for (const gp of candidates) {
        for (const h of [0.5, 0.95, 1.4]) {
          const tx = gp.x - o.x, ty = gp.y + h - o.y, tz = gp.z - o.z;
          const dl = Math.hypot(tx, ty, tz);
          if (dl > HUNTER.rayRange + 0.35 || dl < 1e-3) continue;
          const cos = (tx * d.x + ty * d.y + tz * d.z) / dl;
          const ang = Math.acos(Math.max(-1, Math.min(1, cos)));
          if (ang > HUNTER.rayHalfAngle + Math.atan(0.38 / dl)) continue;
          if (!this.world.segmentClear(o.x, o.y, o.z, gp.x, gp.y + h, gp.z)) continue;
          hit = true;
          break;
        }
        if (hit) break;
      }
      if (hit) hits.push(g);
    }
    this.emit({ e: 'ray', id: p.id, o: [r2(o.x), r2(o.y), r2(o.z)], d: [r3(d.x), r3(d.y), r3(d.z)], hits: hits.map((g) => g.id) });
    for (const g of hits) this.freeze(g, p);
  }

  freeze(g, hunter) {
    if (this.lobby) {
      // practice: a short freeze, no penalty box
      g.frozenUntil = this.time + 1.5;
      this.emit({ e: 'freeze', id: g.id, by: hunter?.id, p: [r2(g.pos.x), r2(g.pos.y), r2(g.pos.z)] });
      this.feed(`${hunter ? hunter.name : 'Someone'} practised on ${g.name}`, 'all', 'freeze');
      return;
    }
    g.frozenUntil = this.time + GHOST.freezeTime;
    g.stats.frozen++;
    if (hunter) hunter.stats.freezes++;
    this.emit({ e: 'freeze', id: g.id, by: hunter?.id, p: [r2(g.pos.x), r2(g.pos.y), r2(g.pos.z)] });
    this.feed(`${hunter ? hunter.name : 'A hunter'} froze ${g.name}`, 'all', 'freeze');
    if (this.relic.holder === g.id) {
      this.relic.lastHolder = null;
      this.newPair([this.relic.spawn, this.relic.capture]);
      this.emit({ e: 'relicReset', by: g.id });
      this.feed('The relic shattered and re-formed elsewhere!', 'all', 'relic');
    }
  }

  pastPositions(ago) {
    const target = this.time - ago;
    let best = null;
    for (const h of this.history) if (h.t <= target) best = h;
    return best ? best.pos : new Map();
  }

  // ------------------------------------------------------------ simulation
  tickLobby(dt) {
    if (!this.botsPaused) for (const p of this.players.values()) if (p.bot) p.bot.update(dt);
    for (const p of this.players.values()) if (p.frozenUntil > 0 && this.time >= p.frozenUntil) p.frozenUntil = -1;
    // team pads: stand on one for a moment to switch sides
    const pads = this.map.lobby?.pads || {};
    for (const p of this.players.values()) {
      if (p.isBot) continue;
      let on = null;
      for (const [role, pad] of Object.entries(pads)) {
        if (Math.hypot(p.pos.x - pad.pos[0], p.pos.z - pad.pos[2]) <= pad.r && Math.abs(p.pos.y - pad.pos[1]) < 1.2) on = role;
      }
      if (!on) p.padBlock = false;
      if (on && !p.padBlock && on !== p.role && on === p.padRole) {
        p.padTime += dt;
        if (p.padTime >= 1.0) {
          p.padTime = 0;
          this.room.setRole(p.id, on);
        }
      } else {
        p.padTime = 0;
      }
      p.padRole = on;
    }
    const snap = new Map();
    for (const g of this.ghosts) snap.set(g.id, { ...g.pos });
    this.history.push({ t: this.time, pos: snap });
    while (this.history.length && this.history[0].t < this.time - 0.6) this.history.shift();
    this.sendSnapshots(dt);
  }

  tick(dt) {
    this.time += dt;
    if (this.lobby) return this.tickLobby(dt);
    if (this.phase === PHASE.RESULTS) {
      this.sendSnapshots(dt);
      return;
    }
    if (this.phase === PHASE.BLIND && this.time >= this.phaseEnd) {
      this.phase = PHASE.PLAY;
      this.emit({ e: 'phase', ph: PHASE.PLAY });
      this.feed('The hunt begins!', 'all', 'phase');
    }
    if (this.phase === PHASE.PLAY) {
      this.timeLeft -= dt;
      if (this.timeLeft <= 0) {
        this.timeLeft = 0;
        return this.finish(ROLES.HUNTER, 'time');
      }
    }

    if (!this.botsPaused) for (const p of this.players.values()) if (p.bot) p.bot.update(dt);

    // freeze -> penalty -> release
    const pspawns = this.map.penalty.spawns;
    for (const g of this.ghosts) {
      if (g.frozenUntil > 0 && this.time >= g.frozenUntil) {
        g.frozenUntil = -1;
        g.penaltyUntil = this.time + this.settings.penaltyTime;
        g.clump = 0;
        this.teleport(g, pspawns[(this.rng() * pspawns.length) | 0]);
        this.emit({ e: 'penalty', id: g.id, until: this.settings.penaltyTime });
      } else if (g.penaltyUntil > 0 && this.time >= g.penaltyUntil) {
        g.penaltyUntil = -1;
        this.teleport(g, this.releaseSpawn());
        this.emit({ e: 'release', id: g.id });
      }
    }

    // clumping: ghosts close together for too long get exposed
    const gs = this.ghosts.filter((g) => this.active(g));
    for (const g of gs) g.near = false;
    for (let i = 0; i < gs.length; i++) for (let j = i + 1; j < gs.length; j++) {
      if (dist3(gs[i].pos, gs[j].pos) <= GHOST.seeRadius) { gs[i].near = true; gs[j].near = true; }
    }
    if (this.phase === PHASE.PLAY) {
      for (const g of gs) {
        if (g.near) g.clump += dt;
        else g.clump = Math.max(0, g.clump - dt * GHOST.clumpDecay);
        if (g.clump >= GHOST.clumpLimit) {
          g.clump = 0;
          g.exposedUntil = this.time + GHOST.exposeTime;
          this.emit({ e: 'expose', id: g.id });
        }
      }
    }

    // relic
    const rel = this.relic;
    for (const g of this.ghosts) {
      if (rel.holder === g.id) {
        g.stamina -= dt;
        g.stats.carry += dt;
        if (g.stamina <= 0) {
          g.stamina = 0;
          this.dropRelic(g, 'tired');
        }
      } else {
        g.stamina = Math.min(this.settings.carryLimit, g.stamina + dt * RELIC.staminaRegen);
      }
    }
    if (rel.holder) {
      const h = this.players.get(rel.holder);
      if (!h || !this.active(h)) {
        if (h) this.dropRelic(h, 'lost');
      } else {
        rel.pos = { x: h.pos.x, y: h.pos.y + 1.1, z: h.pos.z };
        const cap = this.map.flagPoints[rel.capture].pos;
        const inRange = hdist([h.pos.x, 0, h.pos.z], cap) <= RELIC.captureRadius && Math.abs(h.pos.y + 0.9 - cap[1]) < 2.5;
        if (inRange) {
          if (!rel.channeling) {
            rel.channeling = true;
            this.emit({ e: 'channel', p: cap, id: h.id });
          }
          rel.channel += dt;
          if (rel.channel >= RELIC.captureChannel) this.capture(h);
        } else if (rel.channeling) {
          rel.channeling = false;
          rel.channel = 0;
          this.emit({ e: 'channelStop' });
        }
        // ectoplasm drips trail behind the carrier
        if (this.time - rel.lastDrip > RELIC.dripInterval && this.phase === PHASE.PLAY) {
          rel.lastDrip = this.time;
          const gy = this.world.groundHeight(h.pos.x, h.pos.z, h.pos.y + 0.3, 0.1);
          this.emit({ e: 'drip', p: [r2(h.pos.x + (this.rng() - 0.5) * 0.3), r2((Number.isFinite(gy) ? gy : h.pos.y) + 0.01), r2(h.pos.z + (this.rng() - 0.5) * 0.3)] });
        }
      }
    } else if (this.playing()) {
      for (const g of this.ghosts) {
        if (!this.active(g)) continue;
        if (rel.lastHolder === g.id && this.time - rel.dropTime < RELIC.regrabDelay) continue;
        if (g.stamina < RELIC.minPickupStamina) continue;
        const dy = rel.pos.y - (g.pos.y + 0.8);
        if (hdist([g.pos.x, 0, g.pos.z], [rel.pos.x, 0, rel.pos.z]) <= RELIC.pickupRadius && Math.abs(dy) < 1.4) {
          rel.holder = g.id;
          rel.state = 'carried';
          g.carrying = true;
          this.emit({ e: 'pickup', id: g.id }, 'ghosts');
          break;
        }
      }
    }

    // position history for lag-compensated rays
    const snap = new Map();
    for (const g of this.ghosts) snap.set(g.id, { ...g.pos });
    this.history.push({ t: this.time, pos: snap });
    while (this.history.length && this.history[0].t < this.time - 0.6) this.history.shift();

    this.sendSnapshots(dt);
  }

  releaseSpawn() {
    // the ghost spawn farthest from every hunter
    let best = null, bd = -1;
    for (const s of this.map.spawns.ghost) {
      let d = Infinity;
      for (const h of this.hunters) d = Math.min(d, hdist(s, [h.pos.x, h.pos.y, h.pos.z]));
      d += this.rng() * 6;
      if (d > bd) { bd = d; best = s; }
    }
    return best;
  }

  capture(h) {
    const rel = this.relic;
    this.captures++;
    h.stats.captures++;
    const cap = this.map.flagPoints[rel.capture].pos;
    this.emit({ e: 'capture', n: this.captures, p: cap, id: h.id });
    this.feed(`${h.name} delivered the relic! (${this.captures}/${ROUND.capturesToWin})`, 'all', 'capture');
    if (this.captures >= ROUND.capturesToWin) return this.finish(ROLES.GHOST, 'captures');
    this.newPair([rel.spawn, rel.capture]);
  }

  finish(winner, reason) {
    if (this.phase === PHASE.RESULTS) return;
    this.phase = PHASE.RESULTS;
    this.result = { winner, reason };
    this.phaseEnd = this.time + ROUND.resultsTime;
    const stats = [...this.players.values()].map((p) => ({ id: p.id, name: p.name, role: p.role, color: p.color, bot: p.isBot, ...p.stats, carry: Math.round(p.stats.carry) }));
    this.room.broadcast({ t: 'end', winner, reason, captures: this.captures, stats });
  }

  removePlayer(id) {
    const p = this.players.get(id);
    if (!p) return;
    if (this.relic?.holder === id) this.dropRelic(p, 'left');
    this.players.delete(id);
    if (!this.lobby && this.phase !== PHASE.RESULTS) {
      if (!this.hunters.length) this.finish(ROLES.GHOST, 'forfeit');
      else if (!this.ghosts.length) this.finish(ROLES.HUNTER, 'forfeit');
    }
  }

  // ------------------------------------------------------------ snapshots
  visibleTo(viewer, other) {
    if (this.phase === PHASE.RESULTS || this.lobby) return true;
    if (other.role === ROLES.HUNTER) return true;
    if (this.inPenalty(other) || this.isFrozen(other) || this.isExposed(other)) return true;
    if (viewer.role === ROLES.GHOST && !this.inPenalty(viewer)) {
      return dist3(viewer.pos, other.pos) <= GHOST.seeRadius + 1;
    }
    return false;
  }

  sendSnapshots(dt) {
    this.snapAcc += dt;
    if (this.snapAcc < 1 / SNAPSHOT_RATE) return;
    this.snapAcc = 0;
    const rel = this.relic;
    const fp = this.map.flagPoints;
    for (const viewer of this.players.values()) {
      if (viewer.isBot) continue;
      const pl = [];
      for (const o of this.players.values()) {
        if (o === viewer || !this.visibleTo(viewer, o)) continue;
        let f = 0;
        if (this.isFrozen(o)) f |= PF.FROZEN;
        if (this.isExposed(o)) f |= PF.EXPOSED;
        if (this.inPenalty(o)) f |= PF.PENALTY;
        if (o.carrying) f |= PF.CARRYING;
        if (!this.lobby && viewer.role === ROLES.GHOST && o.role === ROLES.GHOST && !(f & (PF.FROZEN | PF.EXPOSED | PF.PENALTY))) f |= PF.NEAR;
        pl.push([o.id, r2(o.pos.x), r2(o.pos.y), r2(o.pos.z), r3(o.yaw), r3(o.pitch), f]);
      }
      const you = {
        st: r2(viewer.stamina), fz: r2(Math.max(0, viewer.frozenUntil - this.time)), pn: r2(Math.max(0, viewer.penaltyUntil - this.time)),
        ex: r2(Math.max(0, viewer.exposedUntil - this.time)),
        wc: r2(Math.max(0, viewer.nextWhistle - this.time)), bc: r2(Math.max(0, viewer.nextBig - this.time)),
        rc: r2(Math.max(0, viewer.nextRay - this.time)), cl: r2(viewer.clump / GHOST.clumpLimit), ca: viewer.carrying ? 1 : 0,
      };
      const msg = { t: 's', ph: this.phase, tl: this.lobby ? 0 : Math.ceil(this.timeLeft), bl: this.lobby ? 0 : r2(Math.max(0, this.phaseEnd - this.time)), cap: this.captures, pl, you };
      if (this.lobby) {
        msg.pad = viewer.padRole && viewer.padRole !== viewer.role ? r2(viewer.padTime) : 0;
      } else if (viewer.role === ROLES.GHOST || this.phase === PHASE.RESULTS) {
        msg.r = { s: rel.state, p: [r2(rel.pos.x), r2(rel.pos.y), r2(rel.pos.z)], h: rel.holder, sp: fp[rel.spawn].id, cp: fp[rel.capture].id, ch: r2(rel.channel / RELIC.captureChannel) };
      } else if (rel.holder) {
        const h = this.players.get(rel.holder);
        if (h && dist3(viewer.pos, h.pos) <= RELIC.humRadius) msg.hum = [r2(h.pos.x), r2(h.pos.y + 1), r2(h.pos.z)];
      }
      if (viewer.outbox.length) {
        msg.ev = viewer.outbox;
        viewer.outbox = [];
      }
      this.room.send(viewer.id, msg);
    }
  }
}

function hdist(a, b) {
  return Math.hypot(a[0] - b[0], a[2] - b[2]);
}

function dist3(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
}

function shuffle(arr, rng) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = (rng() * (i + 1)) | 0;
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}
