// Thin WebSocket wrapper with typed message handlers and automatic reconnect to the lobby.
export class Net {
  constructor() {
    this.handlers = new Map();
    this.id = null;
    this.ws = null;
    this.queue = [];
    this.connected = false;
    this.rtt = 0;
    this.open();
    setInterval(() => this.send({ t: 'ping', c: performance.now() }), 3000);
    this.on('pong', (m) => { this.rtt = performance.now() - m.c; });
  }

  open() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${location.host}/ws`);
    this.ws = ws;
    ws.onopen = () => {
      this.connected = true;
      for (const m of this.queue) ws.send(m);
      this.queue = [];
      this.emit('open', {});
    };
    ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch { return; }
      if (msg.t === 'hello') this.id = msg.id;
      this.emit(msg.t, msg);
    };
    ws.onclose = () => {
      const was = this.connected;
      this.connected = false;
      this.emit('close', { was });
      setTimeout(() => this.open(), 1500);
    };
  }

  on(type, fn) {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set());
    this.handlers.get(type).add(fn);
    return () => this.handlers.get(type).delete(fn);
  }

  emit(type, msg) {
    const set = this.handlers.get(type);
    if (set) for (const fn of [...set]) fn(msg);
  }

  send(msg) {
    const data = JSON.stringify(msg);
    if (this.ws && this.ws.readyState === 1) this.ws.send(data);
    else if (msg.t !== 'ping' && msg.t !== 'st') this.queue.push(data);
  }
}
