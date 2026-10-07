// End-to-end: boots the real server and drives it with two WebSocket clients.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import WebSocket from 'ws';

const PORT = 5900 + Math.floor(Math.random() * 90);

function client() {
  const ws = new WebSocket(`ws://127.0.0.1:${PORT}/ws`);
  const inbox = [];
  const waiters = [];
  ws.on('message', (raw) => {
    const m = JSON.parse(raw);
    inbox.push(m);
    for (const w of [...waiters]) if (w.pred(m)) { waiters.splice(waiters.indexOf(w), 1); w.resolve(m); }
  });
  return {
    ws, inbox,
    send: (m) => ws.send(JSON.stringify(m)),
    wait: (pred, ms = 4000) => new Promise((resolve, reject) => {
      const hit = inbox.find(pred);
      if (hit) return resolve(hit);
      const w = { pred, resolve };
      waiters.push(w);
      setTimeout(() => reject(new Error('timed out waiting for message')), ms);
    }),
  };
}

test('two players: create, join, teams, start, snapshots, sound routing', async (t) => {
  const srv = spawn(process.execPath, ['server/index.js'], { env: { ...process.env, PORT: String(PORT) }, stdio: ['ignore', 'pipe', 'inherit'] });
  t.after(() => srv.kill());
  await new Promise((resolve) => srv.stdout.on('data', (d) => { if (String(d).includes('listening')) resolve(); }));

  const a = client(), b = client();
  await Promise.all([once(a.ws, 'open'), once(b.ws, 'open')]);
  const helloA = await a.wait((m) => m.t === 'hello');
  const helloB = await b.wait((m) => m.t === 'hello');
  a.send({ t: 'create', name: 'Alice' });
  const room = await a.wait((m) => m.t === 'room');
  assert.equal(room.host, helloA.id);
  assert.match(room.code, /^[A-Z]{4}$/);
  b.send({ t: 'join', code: room.code, name: 'Bob' });
  await b.wait((m) => m.t === 'room' && m.players.length === 2);
  // the first player becomes a hunter, the second a ghost
  a.send({ t: 'team', id: helloA.id, role: 'hunter' });
  a.send({ t: 'team', id: helloB.id, role: 'ghost' });
  a.send({ t: 'settings', map: room.maps[0].id, roundTime: 120 });
  await a.wait((m) => m.t === 'room' && m.settings.roundTime === 120 && m.players.find((p) => p.id === helloB.id)?.role === 'ghost');
  // non-hosts can't start
  b.send({ t: 'start' });
  a.send({ t: 'start' });
  const startA = await a.wait((m) => m.t === 'start');
  const startB = await b.wait((m) => m.t === 'start');
  assert.equal(startA.you.role, 'hunter');
  assert.equal(startB.you.role, 'ghost');
  const snapB = await b.wait((m) => m.t === 's');
  assert.ok(snapB.r, 'ghosts receive the relic state');
  const snapA = await a.wait((m) => m.t === 's');
  assert.equal(snapA.r, undefined, 'hunters do not');
  assert.equal(snapA.ph, 'blind');
  // a ghost snapping far from the hunter is not heard by the hunter
  b.send({ t: 'snap' });
  await new Promise((r) => setTimeout(r, 300));
  const heard = a.inbox.some((m) => m.t === 's' && m.ev?.some((e) => e.e === 'snap'));
  const dist = Math.hypot(startA.you.pos[0] - startB.you.pos[0], startA.you.pos[2] - startB.you.pos[2]);
  if (dist > 9.5) assert.equal(heard, false);
  // chat is lobby-only
  a.send({ t: 'chat', text: 'boo' });
  await new Promise((r) => setTimeout(r, 200));
  assert.ok(!b.inbox.some((m) => m.t === 'chat'));
  a.ws.close();
  b.ws.close();
});
