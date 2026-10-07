// A lobby that hosts consecutive rounds. The host picks the map, settings and team sizes.
import { GHOST_NAMES, HUNTER_NAMES, LOBBY_LIMITS, PHASE, PLAYER_COLORS, RELIC, ROLES, ROUND, TICK_RATE } from '../shared/constants.js';
import { Game } from './game.js';
import { availableMaps, loadMap } from './maps.js';

const clamp = (v, [lo, hi]) => Math.max(lo, Math.min(hi, v));

export class Room {
  constructor(code, server) {
    this.code = code;
    this.server = server;
    this.players = new Map();   // id -> { id, name, ws, bot, role, color }
    this.hostId = null;
    this.game = null;
    const maps = availableMaps(server.dev);
    this.settings = {
      map: maps[0]?.id || 'sandbox',
      roundTime: ROUND.defaultTime,
      penaltyTime: ROUND.defaultPenalty,
      carryLimit: RELIC.carryLimit,
      botSkill: 'normal',
    };
    this.lastRound = null;
    this.created = Date.now();
  }

  get phase() { return this.game ? 'game' : 'lobby'; }
  get humans() { return [...this.players.values()].filter((p) => !p.bot); }

  // ------------------------------------------------------------ membership
  addHuman(id, name, ws) {
    const roleCounts = this.counts();
    const role = roleCounts.hunter === 0 ? ROLES.HUNTER : ROLES.GHOST;
    const p = { id, name: this.uniqueName(name), ws, bot: null, role, color: this.freeColor() };
    this.players.set(id, p);
    if (!this.hostId) this.hostId = id;
    this.broadcastRoom();
    if (this.game) this.send(id, { t: 'wait', captures: this.game.captures, timeLeft: Math.ceil(this.game.timeLeft) });
    return p;
  }

  addBot(role) {
    if (this.players.size >= LOBBY_LIMITS.maxPlayers) return;
    const pool = role === ROLES.HUNTER ? HUNTER_NAMES : GHOST_NAMES;
    const used = new Set([...this.players.values()].map((p) => p.name));
    const base = pool.find((n) => !used.has(`${n} (bot)`)) || `${pool[0]}${this.players.size}`;
    const id = this.server.nextId();
    this.players.set(id, { id, name: `${base} (bot)`, ws: null, bot: { skill: this.settings.botSkill }, role, color: this.freeColor() });
    this.broadcastRoom();
  }

  remove(id) {
    const p = this.players.get(id);
    if (!p) return;
    this.players.delete(id);
    if (this.game) this.game.removePlayer(id);
    if (this.hostId === id) this.hostId = this.humans[0]?.id ?? null;
    if (!this.humans.length) {
      this.server.closeRoom(this.code);
      return;
    }
    this.broadcastRoom();
  }

  uniqueName(name) {
    const clean = String(name || 'Player').replace(/[^\p{L}\p{N} _'.-]/gu, '').trim().slice(0, 16) || 'Player';
    const used = new Set([...this.players.values()].map((p) => p.name));
    if (!used.has(clean)) return clean;
    for (let i = 2; ; i++) if (!used.has(`${clean} ${i}`)) return `${clean} ${i}`;
  }

  freeColor() {
    const used = new Set([...this.players.values()].map((p) => p.color));
    return PLAYER_COLORS.find((c) => !used.has(c)) || PLAYER_COLORS[this.players.size % PLAYER_COLORS.length];
  }

  counts() {
    const c = { hunter: 0, ghost: 0 };
    for (const p of this.players.values()) c[p.role]++;
    return c;
  }

  // ------------------------------------------------------------ messages
  handle(id, msg) {
    const p = this.players.get(id);
    if (!p) return;
    const isHost = id === this.hostId;
    const g = this.game;
    const gp = g?.players.get(id);
    switch (msg.t) {
      case 'st': if (gp) g.onState(gp, msg); break;
      case 'snap': if (gp) g.snap(gp); break;
      case 'whistle': if (gp) g.whistle(gp); break;
      case 'manip': if (gp) g.manip(gp, String(msg.prop), msg.k === 'b' ? 'b' : 's'); break;
      case 'ray': if (gp) g.ray(gp, msg.d); break;
      case 'drop': if (gp) g.dropRelic(gp, 'drop'); break;
      case 'dbg': // dev-only helpers for testing
        if (!this.server.dev || !gp) break;
        if (Array.isArray(msg.p)) g.teleport(gp, msg.p, msg.yaw);
        if (msg.time) g.timeLeft = msg.time;
        if (msg.phase === 'play' && g.phase === PHASE.BLIND) g.phaseEnd = g.time;
        if ('pauseBots' in msg) g.botsPaused = !!msg.pauseBots;
        if (msg.near) { // stand 2.5 m in front of another player of the given role, facing them
          const other = [...g.players.values()].find((o) => o.id !== gp.id && o.role === msg.near);
          if (other) {
            const a = other.yaw;
            const p = [other.pos.x - Math.sin(a) * 2.5, other.pos.y, other.pos.z - Math.cos(a) * 2.5];
            g.teleport(gp, p, a + Math.PI);
          }
        }
        if (msg.expose) for (const o of g.ghosts) o.exposedUntil = g.time + 30;
        if (msg.freeze) for (const o of g.ghosts) if (o.id !== gp.id) g.freeze(o, null);
        break;
      case 'settings': if (isHost && !g) this.applySettings(msg); break;
      case 'team': {
        const target = this.players.get(String(msg.id ?? id));
        if (!target || g || (target.id !== id && !isHost)) break;
        if (msg.role === ROLES.HUNTER || msg.role === ROLES.GHOST) target.role = msg.role;
        this.broadcastRoom();
        break;
      }
      case 'shuffle': if (isHost && !g) this.shuffle(msg.hunters); break;
      case 'addBot': if (isHost && !g) this.addBot(msg.role === ROLES.HUNTER ? ROLES.HUNTER : ROLES.GHOST); break;
      case 'kick': {
        const target = this.players.get(String(msg.id));
        if (!isHost || !target || target.id === id) break;
        if (target.ws) this.server.kick(target.id);
        else this.remove(target.id);
        break;
      }
      case 'host': {
        const target = this.players.get(String(msg.id));
        if (isHost && target && !target.bot) { this.hostId = target.id; this.broadcastRoom(); }
        break;
      }
      case 'start': if (isHost && !g) this.start(); break;
      case 'lobby': if (isHost && g) this.endGame(); break;
      case 'chat': {
        const text = String(msg.text || '').slice(0, 160).trim();
        if (text && (!g || g.phase === PHASE.RESULTS)) this.broadcast({ t: 'chat', from: p.name, color: p.color, text });
        break;
      }
      default: break;
    }
  }

  applySettings(msg) {
    const s = this.settings;
    if (typeof msg.map === 'string' && availableMaps(this.server.dev).some((m) => m.id === msg.map)) s.map = msg.map;
    if (Number.isFinite(msg.roundTime)) s.roundTime = clamp(Math.round(msg.roundTime), LOBBY_LIMITS.roundTime);
    if (Number.isFinite(msg.penaltyTime)) s.penaltyTime = clamp(Math.round(msg.penaltyTime), LOBBY_LIMITS.penaltyTime);
    if (Number.isFinite(msg.carryLimit)) s.carryLimit = clamp(Math.round(msg.carryLimit), LOBBY_LIMITS.carryLimit);
    if (['easy', 'normal', 'hard'].includes(msg.botSkill)) {
      s.botSkill = msg.botSkill;
      for (const p of this.players.values()) if (p.bot) p.bot.skill = s.botSkill;
    }
    this.broadcastRoom();
  }

  shuffle(hunters) {
    const list = [...this.players.values()];
    const n = Math.max(1, Math.min(list.length - 1, Math.round(hunters) || 1));
    for (let i = list.length - 1; i > 0; i--) {
      const j = (Math.random() * (i + 1)) | 0;
      [list[i], list[j]] = [list[j], list[i]];
    }
    list.forEach((p, i) => { p.role = i < n ? ROLES.HUNTER : ROLES.GHOST; });
    this.broadcastRoom();
  }

  start() {
    const c = this.counts();
    if (!c.hunter || !c.ghost) {
      this.send(this.hostId, { t: 'error', msg: 'You need at least one hunter and one ghost (add bots to fill a team).' });
      return;
    }
    const entry = loadMap(this.settings.map);
    if (!entry) {
      this.send(this.hostId, { t: 'error', msg: `Map ${this.settings.map} is not built.` });
      return;
    }
    const roster = [...this.players.values()].map((p) => ({ id: p.id, name: p.name, role: p.role, color: p.color, bot: p.bot }));
    this.game = new Game(this, entry, { ...this.settings }, roster);
    for (const p of this.players.values()) {
      if (p.bot) continue;
      const gp = this.game.players.get(p.id);
      this.send(p.id, {
        t: 'start', map: this.settings.map, settings: this.settings,
        you: { id: p.id, role: p.role, pos: [gp.pos.x, gp.pos.y, gp.pos.z], yaw: gp.yaw, seq: gp.tpSeq },
        roster: roster.map(({ id, name, role, color, bot }) => ({ id, name, role, color, bot: !!bot })),
      });
    }
    this.broadcastRoom();
  }

  endGame() {
    if (this.game?.result) this.lastRound = this.game.result;
    this.game = null;
    // players who joined mid-round are already in this.players
    this.broadcast({ t: 'lobby' });
    this.broadcastRoom();
  }

  tick(dt) {
    if (!this.game) return;
    this.game.tick(dt);
    if (this.game.phase === PHASE.RESULTS && this.game.time >= this.game.phaseEnd) this.endGame();
  }

  // ------------------------------------------------------------ output
  roomState() {
    return {
      t: 'room', code: this.code, host: this.hostId, phase: this.phase, settings: this.settings,
      maps: availableMaps(this.server.dev), lastRound: this.lastRound,
      players: [...this.players.values()].map((p) => ({ id: p.id, name: p.name, role: p.role, color: p.color, bot: !!p.bot })),
    };
  }

  broadcastRoom() { this.broadcast(this.roomState()); }

  broadcast(msg) {
    const data = JSON.stringify(msg);
    for (const p of this.players.values()) if (p.ws && p.ws.readyState === 1) p.ws.send(data);
  }

  send(id, msg) {
    const p = this.players.get(id);
    if (p?.ws && p.ws.readyState === 1) p.ws.send(JSON.stringify(msg));
  }
}

export const TICK_MS = 1000 / TICK_RATE;
