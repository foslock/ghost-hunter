// HTTP + WebSocket server. `--dev` serves the client through Vite middleware (with HMR);
// otherwise it serves the production build from dist/.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { WebSocketServer } from 'ws';
import { Room, TICK_MS } from './room.js';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const dev = process.argv.includes('--dev');
const PORT = Number(process.env.PORT) || 5173;
const HOST = process.env.HOST || '0.0.0.0';

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
  '.woff2': 'font/woff2', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.webp': 'image/webp',
};

class GameServer {
  constructor() {
    this.dev = dev;
    this.rooms = new Map();
    this.clients = new Map(); // id -> { ws, room }
    this.idSeq = 1;
  }

  nextId() { return String(this.idSeq++); }

  makeCode() {
    const letters = 'BCDFGHJKLMNPQRSTVWXZ';
    for (;;) {
      let code = '';
      for (let i = 0; i < 4; i++) code += letters[(Math.random() * letters.length) | 0];
      if (!this.rooms.has(code)) return code;
    }
  }

  closeRoom(code) { this.rooms.delete(code); }

  kick(id) {
    const c = this.clients.get(id);
    if (!c) return;
    c.room?.remove(id);
    c.room = null;
    if (c.ws.readyState === 1) c.ws.send(JSON.stringify({ t: 'kicked' }));
  }

  connect(ws) {
    const id = this.nextId();
    const client = { ws, room: null };
    this.clients.set(id, client);
    ws.send(JSON.stringify({ t: 'hello', id }));
    ws.on('message', (raw) => {
      let msg;
      try { msg = JSON.parse(raw); } catch { return; }
      if (!msg || typeof msg.t !== 'string') return;
      if (msg.t === 'create') {
        client.room?.remove(id);
        const room = new Room(this.makeCode(), this);
        this.rooms.set(room.code, room);
        client.room = room;
        room.addHuman(id, msg.name, ws);
      } else if (msg.t === 'join') {
        const room = this.rooms.get(String(msg.code || '').toUpperCase());
        if (!room) return ws.send(JSON.stringify({ t: 'error', msg: 'No room with that code.' }));
        if (room.players.size >= 16) return ws.send(JSON.stringify({ t: 'error', msg: 'That room is full.' }));
        client.room?.remove(id);
        client.room = room;
        room.addHuman(id, msg.name, ws);
      } else if (msg.t === 'leave') {
        client.room?.remove(id);
        client.room = null;
      } else if (msg.t === 'ping') {
        ws.send(JSON.stringify({ t: 'pong', c: msg.c }));
      } else {
        client.room?.handle(id, msg);
      }
    });
    ws.on('error', (err) => console.warn(`socket ${id} error: ${err.message}`));
    ws.on('close', () => {
      client.room?.remove(id);
      this.clients.delete(id);
    });
  }

  loop() {
    let last = performance.now();
    setInterval(() => {
      const now = performance.now();
      const dt = Math.min(0.1, (now - last) / 1000);
      last = now;
      for (const room of this.rooms.values()) {
        try { room.tick(dt); } catch (err) { console.error(`room ${room.code} tick failed`, err); }
      }
    }, TICK_MS);
  }
}

async function main() {
  const gs = new GameServer();
  let vite = null;
  if (dev) {
    const { createServer } = await import('vite');
    vite = await createServer({ configFile: path.join(root, 'vite.config.js'), server: { middlewareMode: true, hmr: { port: PORT + 1 } }, appType: 'spa' });
  }
  const dist = path.join(root, 'dist');
  const server = http.createServer((req, res) => {
    if (req.url === '/healthz') { res.writeHead(200); res.end('ok'); return; }
    if (dev && req.method === 'POST' && req.url.startsWith('/dev/thumb?map=')) {
      // dev-only: save a lobby thumbnail captured by the client renderer
      const id = new URL(req.url, 'http://x').searchParams.get('map').replace(/[^a-z0-9_-]/gi, '');
      const chunks = [];
      req.on('data', (c) => chunks.push(c));
      req.on('end', () => {
        const b64 = Buffer.concat(chunks).toString().replace(/^data:image\/jpeg;base64,/, '');
        fs.writeFileSync(path.join(root, 'client', 'public', 'maps', `${id}.jpg`), Buffer.from(b64, 'base64'));
        res.writeHead(200); res.end('saved');
      });
      return;
    }
    if (vite) { vite.middlewares(req, res); return; }
    const url = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let file = path.join(dist, url);
    if (!file.startsWith(dist)) { res.writeHead(403); res.end(); return; }
    if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(dist, 'index.html');
    if (!fs.existsSync(file)) { res.writeHead(500); res.end('Run `npm run build` first.'); return; }
    const ext = path.extname(file);
    res.writeHead(200, {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'Cache-Control': url.startsWith('/assets/') ? 'public, max-age=31536000, immutable' : 'no-cache',
    });
    fs.createReadStream(file).pipe(res);
  });
  const wss = new WebSocketServer({ noServer: true, maxPayload: 64 * 1024 });
  server.on('upgrade', (req, socket, head) => {
    if (req.url?.startsWith('/ws')) wss.handleUpgrade(req, socket, head, (ws) => gs.connect(ws));
  });
  gs.loop();
  server.listen(PORT, HOST, () => console.log(`Ghost Hunter ${dev ? '(dev) ' : ''}listening on http://localhost:${PORT}`));
}

main();
