#!/usr/bin/env node
// Headless bots-only rounds for balance checks: node scripts/sim.mjs [map] [hunters] [ghosts] [rounds]
import { Room } from '../server/room.js';
import { PHASE } from '../shared/constants.js';

const [map = 'sandbox', nh = '1', ng = '4', rounds = '3'] = process.argv.slice(2);
let seq = 1;
const server = { dev: true, nextId: () => String(seq++), closeRoom() {}, kick() {} };
const tally = { hunter: 0, ghost: 0 };
for (let r = 0; r < Number(rounds); r++) {
  const room = new Room('TEST', server);
  room.settings.map = map;
  for (let i = 0; i < Number(nh); i++) room.addBot('hunter');
  for (let i = 0; i < Number(ng); i++) room.addBot('ghost');
  room.start();
  const g = room.game;
  const counts = {};
  const origEmit = g.emit.bind(g);
  g.emit = (ev, to) => { const e = typeof ev === 'function' ? ev({ role: 'ghost' }) : ev; counts[e.e] = (counts[e.e] || 0) + 1; origEmit(ev, to); };
  const dt = 1 / 30;
  const t0 = performance.now();
  while (g.phase !== PHASE.RESULTS && g.time < 1000) g.tick(dt);
  const ms = performance.now() - t0;
  tally[g.result.winner]++;
  console.log(`round ${r + 1}: ${g.result.winner} win (${g.result.reason}) at t=${g.time.toFixed(0)}s, captures ${g.captures}, ` +
    `sim ${(ms / g.time).toFixed(2)} ms per game-second; events ${JSON.stringify(counts)}`);
}
console.log('tally', tally);
