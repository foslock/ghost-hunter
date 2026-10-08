import { test } from 'node:test';
import assert from 'node:assert/strict';
import { CollisionWorld } from '../shared/collision.js';
import { GHOST, HUNTER, PF, PHASE, PLAYER, RELIC, ROLES } from '../shared/constants.js';
import { Game } from '../server/game.js';
import { loadMap } from '../server/maps.js';

// A tiny deterministic arena: floor, one wall, one step.
function arena() {
  const flagPoints = [
    { id: 'a', pos: [-20, 1, 0] }, { id: 'b', pos: [20, 1, 0] }, { id: 'c', pos: [0, 1, 20] }, { id: 'd', pos: [0, 1, -20] },
  ];
  const colliders = [[-30, -1, -30, 30, 0, 30], [5, 0, -2, 5.3, 4, 2], [-8, 0, -1, -7, 0.3, 1]];
  const data = {
    id: 'arena', bounds: [-30, -30, 30, 30], colliders, flagPoints, props: [{ id: 'door1', type: 'hinge', label: 'Door', pos: [0, 0, 5], params: {} }],
    spawns: { hunter: [[0, 0, -25, 0]], ghost: [[10, 0, 10, 0], [-10, 0, 10, 0], [10, 0, -10, 0]] },
    penalty: { spawns: [[28, 0, 28]], label: 'Cage' }, lights: [], env: {},
  };
  const world = new CollisionWorld(colliders);
  return { id: 'arena', data, world, nav: null };
}

function makeGame(roster, settings = {}) {
  const sent = [];
  const room = { send: (id, m) => sent.push({ id, m }), broadcast: (m) => sent.push({ id: '*', m }) };
  let seed = 1;
  const rng = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const g = new Game(room, arena(), { roundTime: 300, penaltyTime: 30, carryLimit: 14, ...settings }, roster, rng);
  return { g, sent };
}

const R = (id, role) => ({ id, name: id, role, color: '#fff' });
const step = (g, secs) => { for (let t = 0; t < secs; t += 1 / 30) g.tick(1 / 30); };
const place = (p, x, z, y = 0) => { p.pos.x = x; p.pos.y = y; p.pos.z = z; };

test('collision: walls stop movement and low steps are climbed', () => {
  const w = arena().world;
  const body = { pos: { x: 0, y: 0, z: 0 }, vel: { x: 6, y: 0, z: 0 }, onGround: true };
  for (let i = 0; i < 60; i++) w.move(body, 1 / 60, PLAYER.radius, PLAYER.height, PLAYER.stepHeight);
  assert.ok(body.pos.x < 5 - PLAYER.radius + 0.01, `stopped by wall at ${body.pos.x}`);
  const b2 = { pos: { x: -5, y: 0, z: 0 }, vel: { x: -3, y: 0, z: 0 }, onGround: true };
  let maxY = 0;
  for (let i = 0; i < 90; i++) {
    b2.vel.x = -3;
    b2.vel.y -= PLAYER.gravity / 60;
    w.move(b2, 1 / 60, PLAYER.radius, PLAYER.height, PLAYER.stepHeight);
    maxY = Math.max(maxY, b2.pos.y);
  }
  assert.ok(Math.abs(maxY - 0.3) < 0.01, `stepped up onto the 0.3 m step (max y ${maxY})`);
  assert.ok(b2.pos.x < -8.5, `walked over it (x ${b2.pos.x})`);
  assert.equal(w.raycast(0, 1, 0, 1, 0, 0, 20).toFixed(2), '5.00');
  assert.equal(w.segmentClear(0, 1, 0, 4, 1, 0), true);
  assert.equal(w.segmentClear(0, 1, 0, 6, 1, 0), false);
});

test('relic: pickup, stamina drain, capture and win after three deliveries', () => {
  const { g } = makeGame([R('h', ROLES.HUNTER), R('g1', ROLES.GHOST)]);
  g.phase = PHASE.PLAY;
  const ghost = g.players.get('g1');
  for (let n = 1; n <= 3; n++) {
    const spawn = g.map.flagPoints[g.relic.spawn].pos;
    const cap = g.map.flagPoints[g.relic.capture].pos;
    place(ghost, spawn[0], spawn[2]);
    ghost.stamina = 14;
    g.tick(1 / 30);
    assert.equal(g.relic.holder, 'g1', 'picked up');
    place(ghost, cap[0] + 0.5, cap[2]);
    step(g, RELIC.captureChannel + 0.2);
    assert.equal(g.captures, n);
  }
  assert.equal(g.phase, PHASE.RESULTS);
  assert.equal(g.result.winner, ROLES.GHOST);
});

test('relic: carrier drops it when their grip runs out and cannot instantly regrab', () => {
  const { g } = makeGame([R('h', ROLES.HUNTER), R('g1', ROLES.GHOST)], { carryLimit: 5 });
  g.phase = PHASE.PLAY;
  const ghost = g.players.get('g1');
  const spawn = g.map.flagPoints[g.relic.spawn].pos;
  place(ghost, spawn[0], spawn[2]);
  g.tick(1 / 30);
  assert.equal(g.relic.holder, 'g1');
  place(ghost, 0, 0);
  step(g, 5.2);
  assert.equal(g.relic.holder, null);
  assert.equal(g.relic.state, 'dropped');
  g.tick(1 / 30);
  assert.equal(g.relic.holder, null, 'no instant regrab');
});

test('revealer: freezes ghosts in the cone, resets a carried relic, then penalty and release', () => {
  const { g } = makeGame([R('h', ROLES.HUNTER), R('g1', ROLES.GHOST), R('g2', ROLES.GHOST)]);
  g.phase = PHASE.PLAY;
  const h = g.players.get('h'), g1 = g.players.get('g1'), g2 = g.players.get('g2');
  place(h, 0, 10); place(g1, 0, 4); place(g2, 8, 4);
  const spawn = g.map.flagPoints[g.relic.spawn].pos;
  place(g1, spawn[0], spawn[2]);
  g.tick(1 / 30);
  assert.equal(g.relic.holder, 'g1');
  const oldPair = [g.relic.spawn, g.relic.capture];
  place(g1, 0, 4);
  g.history = [];
  g.ray(h, [0, 0, -1]); // looking down -Z at g1
  assert.ok(g.isFrozen(g1), 'g1 frozen');
  assert.ok(!g.isFrozen(g2), 'g2 outside the cone');
  assert.equal(g.relic.holder, null);
  assert.equal(g.relic.state, 'home');
  assert.notDeepEqual([g.relic.spawn, g.relic.capture], oldPair);
  g.ray(h, [0, 0, -1]);
  assert.equal(h.stats.shots, 1, 'cooldown blocks a second shot');
  step(g, GHOST.freezeTime + 0.1);
  assert.ok(g.inPenalty(g1));
  assert.deepEqual([g1.pos.x, g1.pos.z], [28, 28]);
  step(g, 30.1);
  assert.ok(!g.inPenalty(g1));
  assert.ok(g.map.spawns.ghost.some((s) => s[0] === g1.pos.x && s[2] === g1.pos.z), 'released at a ghost spawn');
});

test('revealer: walls block the cone and it has limited range', () => {
  const { g } = makeGame([R('h', ROLES.HUNTER), R('g1', ROLES.GHOST)]);
  g.phase = PHASE.PLAY;
  const h = g.players.get('h'), g1 = g.players.get('g1');
  place(h, 2, 0); place(g1, 8, 0); // wall at x=5
  g.ray(h, [1, 0, 0]);
  assert.ok(!g.isFrozen(g1));
  h.nextRay = 0;
  place(h, 0, -20); place(g1, 0, -20 + HUNTER.rayRange + 2);
  g.ray(h, [0, 0, 1]);
  assert.ok(!g.isFrozen(g1));
});

test('clumping: ghosts that stay together too long are exposed', () => {
  const { g } = makeGame([R('h', ROLES.HUNTER), R('g1', ROLES.GHOST), R('g2', ROLES.GHOST)]);
  g.phase = PHASE.PLAY;
  const g1 = g.players.get('g1'), g2 = g.players.get('g2');
  place(g1, -15, 15); place(g2, -14, 15);
  step(g, GHOST.clumpLimit - 0.5);
  assert.ok(!g.isExposed(g1));
  step(g, 0.7);
  assert.ok(g.isExposed(g1) && g.isExposed(g2));
});

test('visibility: hunters only receive exposed/frozen ghosts; ghosts see each other up close', () => {
  const { g, sent } = makeGame([R('h', ROLES.HUNTER), R('g1', ROLES.GHOST), R('g2', ROLES.GHOST)]);
  g.phase = PHASE.PLAY;
  const g1 = g.players.get('g1'), g2 = g.players.get('g2');
  place(g1, -15, 15); place(g2, -12, 15);
  sent.length = 0;
  g.snapAcc = 1;
  g.tick(1 / 30);
  const snapFor = (id) => sent.find((s) => s.id === id && s.m.t === 's').m;
  assert.deepEqual(snapFor('h').pl.map((e) => e[0]), []);
  const seen = snapFor('g1').pl.map((e) => e[0]);
  assert.ok(seen.includes('g2') && seen.includes('h'));
  assert.ok(snapFor('g1').pl.find((e) => e[0] === 'g2')[6] & PF.NEAR);
  assert.equal(snapFor('h').r, undefined, 'hunters never learn the relic location');
  g1.exposedUntil = g.time + 5;
  sent.length = 0;
  g.snapAcc = 1;
  g.tick(1 / 30);
  assert.deepEqual(snapFor('h').pl.map((e) => e[0]), ['g1']);
});

test('snaps are only delivered within earshot; whistles carry further but have a cooldown', () => {
  const { g, sent } = makeGame([R('h', ROLES.HUNTER), R('g1', ROLES.GHOST), R('g2', ROLES.GHOST)]);
  g.phase = PHASE.PLAY;
  const h = g.players.get('h'), g1 = g.players.get('g1'), g2 = g.players.get('g2');
  place(g1, 0, 0); place(g2, GHOST.snapRadius - 1, 0); place(h, 0, GHOST.snapRadius + 5);
  g.snap(g1);
  assert.equal(g2.outbox.filter((e) => e.e === 'snap').length, 1);
  assert.equal(h.outbox.filter((e) => e.e === 'snap').length, 0);
  assert.equal(g2.outbox.find((e) => e.e === 'snap').id, 'g1', 'ghosts know who snapped');
  g.whistle(g1);
  g.whistle(g1);
  assert.equal(h.outbox.filter((e) => e.e === 'whistle').length, 1);
  assert.equal(h.outbox.find((e) => e.e === 'whistle').id, undefined, 'hunters do not');
  void sent;
});

test('manipulations: reach, big cooldown, and broadcast to everyone', () => {
  const { g } = makeGame([R('h', ROLES.HUNTER), R('g1', ROLES.GHOST)]);
  g.phase = PHASE.PLAY;
  const h = g.players.get('h'), g1 = g.players.get('g1');
  place(g1, 0, 25);
  g.manip(g1, 'door1', 'b');
  assert.equal(h.outbox.filter((e) => e.e === 'manip').length, 0, 'out of reach');
  place(g1, 0, 8);
  g.manip(g1, 'door1', 's');
  g.manip(g1, 'door1', 'b');
  g.time += 3.5;
  g.manip(g1, 'door1', 'b');
  const ev = h.outbox.filter((e) => e.e === 'manip');
  assert.deepEqual(ev.map((e) => e.k), ['s', 'b']);
  g.time += GHOST.bigCooldown;
  g.manip(g1, 'door1', 'b');
  assert.equal(h.outbox.filter((e) => e.e === 'manip').length, 3);
});

test('built maps load with nav grids and every altar pair list is non-empty', () => {
  for (const id of ['sandbox', 'manor', 'farm', 'carnival']) {
    const m = loadMap(id);
    if (!m) continue;
    assert.ok(m.nav.w > 0);
    const { g } = (() => {
      const room = { send() {}, broadcast() {} };
      return { g: new Game(room, m, { roundTime: 300, penaltyTime: 30, carryLimit: 14 }, [R('h', ROLES.HUNTER), R('g', ROLES.GHOST)]) };
    })();
    assert.ok(g.pairs.length > 0, `${id} has usable altar pairs`);
  }
});

test('waiting room: everyone visible, practice freezes have no penalty, pads switch teams', () => {
  const lobbyMap = loadMap('lobby');
  assert.ok(lobbyMap, 'lobby map built');
  const sent = [];
  const roles = [];
  const room = { send: (id, m) => sent.push({ id, m }), broadcast() {}, setRole: (id, role) => { roles.push([id, role]); g.setRole(id, role); } };
  const g = new Game(room, lobbyMap, { roundTime: 300, penaltyTime: 30, carryLimit: 14 }, [R('h', ROLES.HUNTER), R('g1', ROLES.GHOST)], Math.random, 'lobby');
  const h = g.players.get('h'), g1 = g.players.get('g1');
  assert.equal(g.phase, PHASE.LOBBY);
  place(h, 0, 0); place(g1, 0, -4);
  g.snapAcc = 1;
  g.tick(1 / 30);
  const snap = sent.find((x) => x.id === 'h' && x.m.t === 's').m;
  assert.deepEqual(snap.pl.map((e) => e[0]), ['g1'], 'hunters see ghosts in the waiting room');
  g.ray(h, [0, 0, -1]);
  assert.ok(g.isFrozen(g1));
  for (let i = 0; i < 60; i++) g.tick(1 / 30);
  assert.ok(!g.isFrozen(g1) && !g.inPenalty(g1), 'short freeze, no penalty');
  const pad = lobbyMap.data.lobby.pads.hunter;
  place(g1, pad.pos[0], pad.pos[2], pad.pos[1]);
  for (let i = 0; i < 40; i++) g.tick(1 / 30);
  assert.deepEqual(roles, [['g1', ROLES.HUNTER]]);
  assert.equal(g1.role, ROLES.HUNTER);
  // switching back through the menu while standing on the hunters' pad must not bounce back
  g.setRole('g1', ROLES.GHOST);
  for (let i = 0; i < 60; i++) g.tick(1 / 30);
  assert.equal(g1.role, ROLES.GHOST);
});
