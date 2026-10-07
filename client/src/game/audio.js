import { Vector3 } from 'three';

// Procedural sound: every effect is synthesised once into an AudioBuffer with an
// OfflineAudioContext, then played through HRTF panners so players can tell direction.
const SR = 44100;

function noiseBuffer(ctx, dur, color = 'white', seed = 1) {
  const n = Math.max(1, Math.ceil(dur * ctx.sampleRate));
  const buf = ctx.createBuffer(1, n, ctx.sampleRate);
  const d = buf.getChannelData(0);
  let s = seed * 9301 + 49297, last = 0;
  for (let i = 0; i < n; i++) {
    s = (s * 9301 + 49297) % 233280;
    const w = s / 233280 * 2 - 1;
    if (color === 'brown') { last = (last + 0.02 * w) / 1.02; d[i] = last * 3.5; } else d[i] = w;
  }
  return buf;
}

function noise(ctx, dur, color, seed) {
  const src = ctx.createBufferSource();
  src.buffer = noiseBuffer(ctx, dur, color, seed);
  return src;
}

function gainEnv(ctx, pts, curve = 'exp') {
  const g = ctx.createGain();
  const p = g.gain;
  p.setValueAtTime(pts[0][1], pts[0][0]);
  for (let i = 1; i < pts.length; i++) {
    const [t, v] = pts[i];
    if (curve === 'exp' && v > 0 && pts[i - 1][1] > 0) p.exponentialRampToValueAtTime(v, t);
    else p.linearRampToValueAtTime(v, t);
  }
  return g;
}

function filter(ctx, type, freq, Q = 1) {
  const f = ctx.createBiquadFilter();
  f.type = type;
  f.frequency.value = freq;
  f.Q.value = Q;
  return f;
}

function osc(ctx, type, freq, t0, t1, out, gainPts, opts = {}) {
  const o = ctx.createOscillator();
  o.type = type;
  if (Array.isArray(freq)) {
    o.frequency.setValueAtTime(freq[0][1], freq[0][0]);
    for (let i = 1; i < freq.length; i++) o.frequency.exponentialRampToValueAtTime(freq[i][1], freq[i][0]);
  } else o.frequency.value = freq;
  if (opts.detune) o.detune.value = opts.detune;
  if (opts.vibrato) {
    const l = ctx.createOscillator();
    const lg = ctx.createGain();
    l.frequency.value = opts.vibrato[0];
    lg.gain.value = opts.vibrato[1];
    l.connect(lg).connect(o.frequency);
    l.start(t0); l.stop(t1);
  }
  const g = gainEnv(ctx, gainPts);
  o.connect(g).connect(out);
  o.start(t0); o.stop(t1);
  return o;
}

// bell-like strike from inharmonic partials
function strike(ctx, out, t, base, partials, decay, amp = 0.3) {
  for (const [ratio, a, dk] of partials) {
    osc(ctx, 'sine', base * ratio, t, t + decay * dk + 0.05, out, [[t, 0.0001], [t + 0.004, amp * a], [t + decay * dk, 0.0001]]);
  }
}

function pianoNote(ctx, out, t, f, amp = 0.25, dur = 2.2) {
  for (const [h, a] of [[1, 1], [2, 0.5], [3, 0.28], [4, 0.14], [5, 0.08]]) {
    osc(ctx, 'sine', f * h * (1 + 0.0007 * h * h), t, t + dur, out, [[t, 0.0001], [t + 0.006, amp * a], [t + 0.3, amp * a * 0.4], [t + dur, 0.0001]]);
  }
}

const NOTE = (n) => 440 * 2 ** ((n - 69) / 12);

const DEFS = {
  snap: [0.16, (c, o) => {
    const n = noise(c, 0.16, 'white', 3);
    n.connect(filter(c, 'bandpass', 2600, 1.3)).connect(gainEnv(c, [[0, 0.0001], [0.0015, 1.4], [0.05, 0.0001]])).connect(o);
    n.start(0);
    osc(c, 'sine', [[0, 2100], [0.03, 1300]], 0, 0.05, o, [[0, 0.0001], [0.001, 0.35], [0.035, 0.0001]]);
    const b = noise(c, 0.1, 'white', 5);
    b.connect(filter(c, 'lowpass', 500)).connect(gainEnv(c, [[0, 0.0001], [0.002, 0.6], [0.04, 0.0001]])).connect(o);
    b.start(0);
  }],
  whistle: [1.25, (c, o) => {
    const v = [6, 18];
    osc(c, 'sine', [[0, 1050], [0.28, 1700], [0.4, 1680]], 0, 0.46, o, [[0, 0.0001], [0.06, 0.45], [0.36, 0.42], [0.45, 0.0001]], { vibrato: v });
    osc(c, 'sine', [[0.5, 1720], [1.15, 1180]], 0.5, 1.2, o, [[0.5, 0.0001], [0.56, 0.45], [1.0, 0.38], [1.19, 0.0001]], { vibrato: v });
    const n = noise(c, 1.2, 'white', 7);
    n.connect(filter(c, 'bandpass', 3200, 2)).connect(gainEnv(c, [[0, 0.0001], [0.05, 0.04], [1.1, 0.03], [1.2, 0.0001]])).connect(o);
    n.start(0);
  }],
  bang: [1.0, (c, o) => {
    const n = noise(c, 1, 'white', 11);
    n.connect(filter(c, 'lowpass', 1100)).connect(gainEnv(c, [[0, 0.0001], [0.003, 1.6], [0.22, 0.05], [0.9, 0.0001]])).connect(o);
    n.start(0);
    osc(c, 'sine', [[0, 110], [0.25, 45]], 0, 0.5, o, [[0, 0.0001], [0.004, 1.2], [0.45, 0.0001]]);
    const r = noise(c, 0.6, 'white', 13);
    r.connect(filter(c, 'bandpass', 380, 4)).connect(gainEnv(c, [[0.05, 0.0001], [0.08, 0.5], [0.7, 0.0001]])).connect(o);
    r.start(0.05);
  }],
  creak: [1.4, (c, o) => {
    const s = c.createOscillator();
    s.type = 'sawtooth';
    s.frequency.setValueAtTime(70, 0);
    for (let i = 1; i < 14; i++) s.frequency.linearRampToValueAtTime(60 + Math.sin(i * 1.7) * 30 + i * 4, i * 0.1);
    const g = c.createGain();
    g.gain.setValueAtTime(0.0001, 0);
    for (let i = 0; i < 26; i++) g.gain.setValueAtTime(0.1 + 0.25 * Math.abs(Math.sin(i * 2.3)), 0.05 + i * 0.05);
    g.gain.linearRampToValueAtTime(0.0001, 1.35);
    s.connect(filter(c, 'bandpass', 900, 3)).connect(g).connect(o);
    s.connect(filter(c, 'bandpass', 2300, 6)).connect(g);
    s.start(0); s.stop(1.4);
  }],
  chime: [3.2, (c, o) => {
    strike(c, o, 0, 196, [[1, 1, 1], [2, 0.6, 0.7], [2.4, 0.35, 0.5], [3, 0.3, 0.45], [4.2, 0.18, 0.3], [5.4, 0.1, 0.2]], 3.0, 0.32);
  }],
  clatter: [1.3, (c, o) => {
    for (let i = 0; i < 12; i++) {
      const t = 0.02 + (i * 0.083 + Math.sin(i * 7.1) * 0.03);
      const f = 1400 + ((i * 937) % 2600);
      strike(c, o, Math.max(0, t), f, [[1, 1, 1], [1.47, 0.6, 0.6], [2.31, 0.3, 0.4]], 0.18 + (i % 3) * 0.06, 0.18 * (1 - i / 14));
    }
    const n = noise(c, 1.2, 'white', 17);
    n.connect(filter(c, 'highpass', 3000)).connect(gainEnv(c, [[0, 0.0001], [0.01, 0.15], [1.1, 0.0001]])).connect(o);
    n.start(0);
  }],
  rustle: [1.6, (c, o) => {
    const n = noise(c, 1.6, 'white', 19);
    const g = c.createGain();
    g.gain.setValueAtTime(0.0001, 0);
    for (let i = 0; i < 40; i++) g.gain.setValueAtTime(0.05 + 0.4 * Math.abs(Math.sin(i * 1.93) * Math.sin(i * 0.37)), i * 0.038);
    g.gain.linearRampToValueAtTime(0.0001, 1.58);
    n.connect(filter(c, 'bandpass', 3400, 0.8)).connect(g).connect(o);
    n.start(0);
  }],
  whoosh: [1.4, (c, o) => {
    const n = noise(c, 1.4, 'white', 23);
    const f = filter(c, 'bandpass', 300, 1.5);
    f.frequency.setValueAtTime(300, 0);
    f.frequency.exponentialRampToValueAtTime(1600, 0.5);
    f.frequency.exponentialRampToValueAtTime(350, 1.3);
    n.connect(f).connect(gainEnv(c, [[0, 0.0001], [0.45, 1.0], [1.35, 0.0001]])).connect(o);
    n.start(0);
  }],
  thud: [0.6, (c, o) => {
    osc(c, 'sine', [[0, 95], [0.2, 42]], 0, 0.5, o, [[0, 0.0001], [0.004, 1.3], [0.45, 0.0001]]);
    const n = noise(c, 0.3, 'white', 29);
    n.connect(filter(c, 'lowpass', 600)).connect(gainEnv(c, [[0, 0.0001], [0.003, 0.9], [0.15, 0.0001]])).connect(o);
    n.start(0);
  }],
  whoomp: [1.0, (c, o) => {
    const n = noise(c, 1, 'white', 31);
    const f = filter(c, 'lowpass', 200, 2);
    f.frequency.setValueAtTime(150, 0);
    f.frequency.exponentialRampToValueAtTime(2200, 0.18);
    f.frequency.exponentialRampToValueAtTime(250, 0.9);
    n.connect(f).connect(gainEnv(c, [[0, 0.0001], [0.12, 1.2], [0.95, 0.0001]])).connect(o);
    n.start(0);
    osc(c, 'sine', [[0, 55], [0.4, 80]], 0, 0.6, o, [[0, 0.0001], [0.1, 0.5], [0.55, 0.0001]]);
  }],
  buzz: [1.6, (c, o) => {
    const g = c.createGain();
    g.gain.setValueAtTime(0, 0);
    let t = 0, i = 0;
    while (t < 1.4) {
      const on = (i * 7919) % 5 > 1;
      g.gain.setValueAtTime(on ? 0.22 : 0.0, t);
      t += 0.03 + ((i * 104729) % 9) * 0.012;
      i++;
    }
    g.gain.setValueAtTime(0, 1.45);
    for (const f of [120, 240, 360]) {
      const s = c.createOscillator();
      s.type = 'sawtooth';
      s.frequency.value = f;
      s.connect(filter(c, 'lowpass', 2400)).connect(g);
      s.start(0); s.stop(1.5);
    }
    g.connect(o);
    const p = noise(c, 0.1, 'white', 37);
    p.connect(gainEnv(c, [[1.45, 0.0001], [1.452, 1.0], [1.52, 0.0001]])).connect(o);
    p.start(1.45);
  }],
  piano: [3.0, (c, o) => {
    [36, 37, 43, 48, 49, 54].forEach((n, i) => pianoNote(c, o, i * 0.012, NOTE(n), 0.2, 2.8));
  }],
  piano_soft: [2.0, (c, o) => pianoNote(c, o, 0, NOTE(76), 0.12, 1.9)],
  musicbox: [3.2, (c, o) => {
    [84, 88, 91, 86, 84, 79, 83, 86].forEach((n, i) => {
      const t = i * 0.28 + Math.sin(i * 3) * 0.04;
      strike(c, o, t, NOTE(n) * (1 - i * 0.008), [[1, 1, 1], [4, 0.2, 0.3], [6.2, 0.06, 0.2]], 0.9, 0.22);
    });
  }],
  musicbox_soft: [1.6, (c, o) => {
    [88, 84, 91].forEach((n, i) => strike(c, o, i * 0.42, NOTE(n), [[1, 1, 1], [4, 0.2, 0.3]], 0.8, 0.12));
  }],
  organ: [3.2, (c, o) => {
    const lp = filter(c, 'lowpass', 1800);
    lp.connect(o);
    for (const n of [38, 45, 50, 51, 57]) {
      for (const [m, a] of [[1, 0.12], [2, 0.07], [4, 0.03]]) {
        osc(c, 'square', NOTE(n) * m, 0, 3.1, lp, [[0, 0.0001], [0.12, a], [2.6, a * 0.8], [3.05, 0.0001]], { vibrato: [5.5, 2] });
      }
    }
  }],
  organ_soft: [1.8, (c, o) => {
    const lp = filter(c, 'lowpass', 1400);
    lp.connect(o);
    osc(c, 'square', NOTE(57), 0, 1.7, lp, [[0, 0.0001], [0.15, 0.06], [1.3, 0.05], [1.65, 0.0001]]);
  }],
  calliope: [3.0, (c, o) => {
    const tune = [72, 76, 79, 84, 83, 79, 76, 78, 77, 74];
    tune.forEach((n, i) => {
      const t = i * 0.26;
      osc(c, 'square', NOTE(n) * (1 + 0.012 * Math.sin(i)), t, t + 0.3, o, [[t, 0.0001], [t + 0.02, 0.09], [t + 0.24, 0.07], [t + 0.29, 0.0001]], { vibrato: [7, 9] });
      osc(c, 'sine', NOTE(n) * 2, t, t + 0.3, o, [[t, 0.0001], [t + 0.02, 0.06], [t + 0.29, 0.0001]]);
    });
  }],
  calliope_soft: [0.8, (c, o) => {
    osc(c, 'square', NOTE(79), 0, 0.7, o, [[0, 0.0001], [0.05, 0.05], [0.6, 0.04], [0.68, 0.0001]], { vibrato: [7, 8] });
  }],
  bell: [3.0, (c, o) => {
    for (let k = 0; k < 3; k++) strike(c, o, k * 0.8, 420, [[0.5, 0.8, 1], [1, 1, 0.8], [1.19, 0.5, 0.6], [1.5, 0.4, 0.5], [2, 0.35, 0.4], [2.6, 0.2, 0.3]], 2.0, 0.28);
  }],
  bell_soft: [1.2, (c, o) => strike(c, o, 0, 420, [[1, 1, 1], [2.6, 0.2, 0.4]], 1.0, 0.06)],
  whirr: [2.2, (c, o) => {
    const s = c.createOscillator();
    s.type = 'sawtooth';
    s.frequency.setValueAtTime(18, 0);
    s.frequency.exponentialRampToValueAtTime(70, 0.6);
    s.frequency.exponentialRampToValueAtTime(12, 2.1);
    s.connect(filter(c, 'bandpass', 900, 1.5)).connect(gainEnv(c, [[0, 0.0001], [0.3, 0.6], [2.1, 0.0001]])).connect(o);
    s.start(0); s.stop(2.2);
  }],
  squeak: [0.5, (c, o) => {
    osc(c, 'sine', [[0, 1100], [0.12, 1850], [0.3, 1500], [0.42, 1900]], 0, 0.45, o, [[0, 0.0001], [0.02, 0.25], [0.4, 0.0001]], { vibrato: [30, 60] });
  }],
  jingle: [2.0, (c, o) => {
    [91, 88, 95, 86, 93, 98, 91].forEach((n, i) => strike(c, o, i * 0.17 + Math.sin(i * 5) * 0.05 + 0.05, NOTE(n), [[1, 1, 1], [2.76, 0.3, 0.5], [5.4, 0.1, 0.3]], 1.3, 0.1));
  }],
  jingle_soft: [1.4, (c, o) => {
    [91, 95].forEach((n, i) => strike(c, o, i * 0.3, NOTE(n), [[1, 1, 1], [2.76, 0.3, 0.5]], 1.1, 0.05));
  }],
  splash: [1.0, (c, o) => {
    const n = noise(c, 1, 'white', 41);
    n.connect(filter(c, 'lowpass', 2500)).connect(gainEnv(c, [[0, 0.0001], [0.02, 0.9], [0.7, 0.0001]])).connect(o);
    n.start(0);
    for (let i = 0; i < 6; i++) osc(c, 'sine', [[0.1 + i * 0.1, 500 + i * 120], [0.16 + i * 0.1, 1500]], 0.1 + i * 0.1, 0.18 + i * 0.1, o, [[0.1 + i * 0.1, 0.0001], [0.11 + i * 0.1, 0.12], [0.17 + i * 0.1, 0.0001]]);
  }],
  caw: [1.0, (c, o) => {
    for (const t of [0, 0.42]) {
      const s = c.createOscillator();
      s.type = 'sawtooth';
      s.frequency.setValueAtTime(480, t);
      s.frequency.exponentialRampToValueAtTime(360, t + 0.3);
      s.connect(filter(c, 'bandpass', 1300, 3)).connect(gainEnv(c, [[t, 0.0001], [t + 0.03, 0.7], [t + 0.25, 0.4], [t + 0.33, 0.0001]])).connect(o);
      s.start(t); s.stop(t + 0.35);
    }
  }],
  rattle: [0.9, (c, o) => {
    for (let i = 0; i < 22; i++) {
      const t = i * 0.035 + (i % 3) * 0.006;
      const n = noise(c, 0.03, 'white', 50 + i);
      n.connect(filter(c, 'bandpass', 1800 + (i % 4) * 300, 3)).connect(gainEnv(c, [[t, 0.0001], [t + 0.002, 0.5 * (1 - i / 24)], [t + 0.025, 0.0001]])).connect(o);
      n.start(t);
    }
  }],
  gong: [4.0, (c, o) => {
    strike(c, o, 0, 98, [[1, 1, 1], [1.52, 0.7, 0.9], [2.03, 0.5, 0.8], [2.72, 0.4, 0.6], [3.4, 0.3, 0.5], [4.1, 0.2, 0.4]], 3.8, 0.3);
  }],
  // ---- game events
  ray: [0.9, (c, o) => {
    osc(c, 'sawtooth', [[0, 1800], [0.45, 120]], 0, 0.5, o, [[0, 0.0001], [0.01, 0.3], [0.45, 0.0001]]);
    osc(c, 'sine', [[0, 2600], [0.3, 400]], 0, 0.35, o, [[0, 0.0001], [0.005, 0.35], [0.3, 0.0001]]);
    osc(c, 'sine', [[0, 90], [0.6, 40]], 0, 0.8, o, [[0, 0.0001], [0.02, 0.8], [0.75, 0.0001]]);
    const n = noise(c, 0.5, 'white', 61);
    n.connect(filter(c, 'highpass', 2500)).connect(gainEnv(c, [[0, 0.0001], [0.01, 0.5], [0.4, 0.0001]])).connect(o);
    n.start(0);
  }],
  freeze: [1.6, (c, o) => {
    [88, 92, 95, 100, 104].forEach((n, i) => strike(c, o, i * 0.07, NOTE(n), [[1, 1, 1], [2.4, 0.4, 0.5]], 1.0, 0.16));
    const n = noise(c, 1.5, 'white', 67);
    n.connect(filter(c, 'highpass', 6000)).connect(gainEnv(c, [[0, 0.0001], [0.05, 0.3], [1.4, 0.0001]])).connect(o);
    n.start(0);
  }],
  capture: [4.0, (c, o) => {
    const lp = filter(c, 'lowpass', 2200);
    lp.connect(o);
    for (const n of [57, 64, 69, 71, 76]) for (const d of [-8, 7]) {
      osc(c, 'sawtooth', NOTE(n), 0, 3.9, lp, [[0, 0.0001], [0.8, 0.05], [2.6, 0.045], [3.85, 0.0001]], { detune: d, vibrato: [5, 3] });
    }
    strike(c, o, 0.05, NOTE(69), [[1, 1, 1], [2, 0.5, 0.7], [3, 0.3, 0.5]], 3.5, 0.2);
  }],
  channel: [2.6, (c, o) => {
    osc(c, 'sine', [[0, 260], [2.4, 880]], 0, 2.5, o, [[0, 0.0001], [0.3, 0.3], [2.3, 0.35], [2.5, 0.0001]], { vibrato: [9, 14] });
    osc(c, 'triangle', [[0, 390], [2.4, 1320]], 0, 2.5, o, [[0, 0.0001], [0.3, 0.12], [2.5, 0.0001]]);
    const n = noise(c, 2.5, 'white', 71);
    n.connect(filter(c, 'bandpass', 5000, 1)).connect(gainEnv(c, [[0, 0.0001], [2.2, 0.15], [2.5, 0.0001]])).connect(o);
    n.start(0);
  }],
  shatter: [1.4, (c, o) => {
    const n = noise(c, 0.6, 'white', 73);
    n.connect(filter(c, 'highpass', 2500)).connect(gainEnv(c, [[0, 0.0001], [0.003, 1.2], [0.5, 0.0001]])).connect(o);
    n.start(0);
    for (let i = 0; i < 16; i++) strike(c, o, 0.02 + i * 0.05 + Math.sin(i * 9) * 0.02, 2200 + ((i * 1777) % 4000), [[1, 1, 1], [1.6, 0.5, 0.6]], 0.3, 0.1);
  }],
  pickup: [1.0, (c, o) => {
    [76, 81, 88].forEach((n, i) => strike(c, o, i * 0.08, NOTE(n), [[1, 1, 1], [2, 0.3, 0.6]], 0.8, 0.18));
  }],
  drop: [0.9, (c, o) => {
    [84, 79, 72].forEach((n, i) => strike(c, o, i * 0.08, NOTE(n), [[1, 1, 1], [2, 0.3, 0.6]], 0.7, 0.16));
  }],
  expose: [1.2, (c, o) => {
    osc(c, 'sawtooth', 220, 0, 0.5, o, [[0, 0.0001], [0.03, 0.18], [0.45, 0.0001]]);
    osc(c, 'sawtooth', 165, 0.5, 1.15, o, [[0.5, 0.0001], [0.53, 0.16], [1.1, 0.0001]]);
  }],
  tick: [0.12, (c, o) => {
    osc(c, 'sine', 1200, 0, 0.1, o, [[0, 0.0001], [0.003, 0.25], [0.09, 0.0001]]);
  }],
  go: [1.0, (c, o) => {
    strike(c, o, 0, NOTE(69), [[1, 1, 1], [2, 0.5, 0.7], [3, 0.2, 0.5]], 0.9, 0.3);
    strike(c, o, 0.0, NOTE(76), [[1, 1, 1], [2, 0.5, 0.7]], 0.9, 0.2);
  }],
  hum: [2.0, (c, o) => {
    for (const [f, a] of [[110, 0.22], [165, 0.12], [220, 0.08], [330, 0.04]]) {
      const s = c.createOscillator();
      s.frequency.value = f;
      const g = c.createGain();
      g.gain.value = a;
      const l = c.createOscillator();
      l.frequency.value = 1;
      const lg = c.createGain();
      lg.gain.value = a * 0.5;
      l.connect(lg).connect(g.gain);
      s.connect(g).connect(o);
      s.start(0); s.stop(2); l.start(0); l.stop(2);
    }
  }],
};

// Ambient beds (looped). Rendered longer then crossfaded so the loop point is seamless.
const AMBIENCE = {
  indoor: (c, o, dur) => {
    const n = noise(c, dur, 'brown', 81);
    n.connect(filter(c, 'lowpass', 220)).connect(gainEnv(c, [[0, 0.25], [dur, 0.25]], 'lin')).connect(o);
    n.start(0);
    const w = noise(c, dur, 'white', 83);
    const f = filter(c, 'bandpass', 500, 0.6);
    const g = c.createGain();
    g.gain.value = 0.015;
    const l = c.createOscillator();
    l.frequency.value = 0.11;
    const lg = c.createGain();
    lg.gain.value = 0.012;
    l.connect(lg).connect(g.gain);
    w.connect(f).connect(g).connect(o);
    w.start(0); l.start(0);
  },
  wind: (c, o, dur) => {
    const w = noise(c, dur, 'white', 87);
    const f = filter(c, 'bandpass', 420, 0.7);
    const l = c.createOscillator();
    l.frequency.value = 0.09;
    const lf = c.createGain();
    lf.gain.value = 200;
    l.connect(lf).connect(f.frequency);
    const g = c.createGain();
    g.gain.value = 0.05;
    const l2 = c.createOscillator();
    l2.frequency.value = 0.13;
    const lg = c.createGain();
    lg.gain.value = 0.035;
    l2.connect(lg).connect(g.gain);
    w.connect(f).connect(g).connect(o);
    w.start(0); l.start(0); l2.start(0);
    // crickets
    for (let t = 0.5; t < dur - 0.5; t += 0.9 + (t * 7.3 % 1.1)) {
      for (let k = 0; k < 3; k++) osc(c, 'sine', 4300, t + k * 0.06, t + k * 0.06 + 0.04, o, [[t + k * 0.06, 0.0001], [t + k * 0.06 + 0.005, 0.012], [t + k * 0.06 + 0.035, 0.0001]]);
    }
  },
  night: (c, o, dur) => {
    AMBIENCE.wind(c, o, dur);
    const n = noise(c, dur, 'brown', 91);
    n.connect(filter(c, 'lowpass', 160)).connect(gainEnv(c, [[0, 0.18], [dur, 0.18]], 'lin')).connect(o);
    n.start(0);
  },
};

async function render(dur, fn, sr = SR) {
  const c = new OfflineAudioContext(1, Math.ceil(dur * sr), sr);
  const out = c.createGain();
  out.connect(c.destination);
  fn(c, out, dur);
  return c.startRendering();
}

async function renderLoop(dur, fn) {
  const fade = 1.5;
  const buf = await render(dur + fade, fn, 22050);
  const d = buf.getChannelData(0);
  const n = Math.floor(dur * buf.sampleRate), fn2 = Math.floor(fade * buf.sampleRate);
  const out = new AudioBuffer({ length: n, sampleRate: buf.sampleRate, numberOfChannels: 1 });
  const od = out.getChannelData(0);
  for (let i = 0; i < n; i++) od[i] = d[i];
  for (let i = 0; i < fn2; i++) {
    const a = i / fn2;
    od[i] = d[i] * a + d[n + i] * (1 - a);
  }
  return out;
}

// How loud / how far each sound carries (refDistance, maxDistance, volume).
const PROFILE = {
  snap: [2.2, 14, 1.0], whistle: [10, 70, 0.9], ray: [4, 40, 0.8], freeze: [4, 35, 0.9],
  capture: [30, 200, 0.9], channel: [8, 60, 0.9], shatter: [6, 50, 0.9], hum: [1.5, 12, 0.7],
  _soft: [1.5, 12, 0.6], _big: [5, 60, 1.0], pickup: [3, 20, 0.7], drop: [3, 20, 0.7],
};

export class AudioEngine {
  constructor() {
    this.ctx = null;
    this.buffers = new Map();
    this.loading = null;
    this.volume = 0.8;
    this.loops = new Set();
    this.ambience = null;
  }

  async init() {
    if (this.loading) return this.loading;
    this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    this.master = this.ctx.createGain();
    this.master.gain.value = this.volume;
    const comp = this.ctx.createDynamicsCompressor();
    comp.threshold.value = -14;
    comp.ratio.value = 4;
    this.master.connect(comp).connect(this.ctx.destination);
    this.loading = Promise.all(Object.entries(DEFS).map(async ([name, [dur, fn]]) => {
      const buf = await render(dur, fn);
      // even out levels: loud events peak near 0.9, soft variants and UI blips much lower
      const target = name.endsWith('_soft') ? 0.32 : ['tick', 'hum'].includes(name) ? 0 : 0.9;
      if (target) {
        const d = buf.getChannelData(0);
        let peak = 0;
        for (let i = 0; i < d.length; i++) peak = Math.max(peak, Math.abs(d[i]));
        if (peak > 1e-4) {
          const k = target / peak;
          for (let i = 0; i < d.length; i++) d[i] *= k;
        }
      }
      this.buffers.set(name, buf);
    }));
    return this.loading;
  }

  resume() {
    if (!this.ctx) this.init();
    if (this.ctx.state === 'suspended') this.ctx.resume();
  }

  setVolume(v) {
    this.volume = v;
    if (this.master) this.master.gain.value = v;
  }

  setListener(cam) {
    if (!this.ctx) return;
    const l = this.ctx.listener;
    const p = cam.position;
    const f = cam.getWorldDirection(_v);
    const t = this.ctx.currentTime;
    if (l.positionX) {
      l.positionX.setTargetAtTime(p.x, t, 0.02); l.positionY.setTargetAtTime(p.y, t, 0.02); l.positionZ.setTargetAtTime(p.z, t, 0.02);
      l.forwardX.setTargetAtTime(f.x, t, 0.02); l.forwardY.setTargetAtTime(f.y, t, 0.02); l.forwardZ.setTargetAtTime(f.z, t, 0.02);
      l.upX.value = 0; l.upY.value = 1; l.upZ.value = 0;
    } else {
      l.setPosition(p.x, p.y, p.z);
      l.setOrientation(f.x, f.y, f.z, 0, 1, 0);
    }
  }

  _panner(pos, ref, max) {
    const pn = this.ctx.createPanner();
    pn.panningModel = 'HRTF';
    pn.distanceModel = 'inverse';
    pn.refDistance = ref;
    pn.maxDistance = max;
    pn.rolloffFactor = 1.2;
    if (pn.positionX) { pn.positionX.value = pos[0]; pn.positionY.value = pos[1]; pn.positionZ.value = pos[2]; } else pn.setPosition(...pos);
    return pn;
  }

  // Play a one-shot. pos = [x,y,z] for 3D, omit for 2D. opts: { profile, volume, rate, delay }
  play(name, pos = null, opts = {}) {
    if (!this.ctx || this.ctx.state !== 'running') return;
    const buf = this.buffers.get(name);
    if (!buf) return;
    const [ref, max, vol] = PROFILE[opts.profile || name] || PROFILE._big;
    const src = this.ctx.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = opts.rate ?? 1;
    const g = this.ctx.createGain();
    g.gain.value = (opts.volume ?? 1) * vol;
    src.connect(g);
    if (pos) g.connect(this._panner(pos, opts.ref ?? ref, max)).connect(this.master);
    else g.connect(this.master);
    src.start(this.ctx.currentTime + (opts.delay || 0));
  }

  loop(name, pos, opts = {}) {
    if (!this.ctx) return null;
    const buf = this.buffers.get(name);
    if (!buf) return null;
    const [ref, max, vol] = PROFILE[opts.profile || name] || PROFILE._soft;
    const src = this.ctx.createBufferSource();
    src.buffer = buf;
    src.loop = true;
    const g = this.ctx.createGain();
    g.gain.value = 0;
    const pn = this._panner(pos || [0, 0, 0], ref, max);
    src.connect(g).connect(pn).connect(this.master);
    src.start();
    const h = {
      setPos: (p) => { if (pn.positionX) { pn.positionX.value = p[0]; pn.positionY.value = p[1]; pn.positionZ.value = p[2]; } else pn.setPosition(...p); },
      setVolume: (v) => g.gain.setTargetAtTime(v * vol, this.ctx.currentTime, 0.1),
      stop: () => { try { src.stop(); } catch { /* already stopped */ } this.loops.delete(h); },
    };
    this.loops.add(h);
    return h;
  }

  async startAmbience(kind) {
    this.stopAmbience();
    if (!this.ctx) return;
    const fn = AMBIENCE[kind] || AMBIENCE.indoor;
    const buf = await renderLoop(12, fn);
    const src = this.ctx.createBufferSource();
    src.buffer = buf;
    src.loop = true;
    const g = this.ctx.createGain();
    g.gain.value = 0;
    g.gain.setTargetAtTime(0.9, this.ctx.currentTime, 1.5);
    src.connect(g).connect(this.master);
    src.start();
    this.ambience = { src, g };
  }

  stopAmbience() {
    if (!this.ambience) return;
    const { src, g } = this.ambience;
    g.gain.setTargetAtTime(0, this.ctx.currentTime, 0.4);
    setTimeout(() => { try { src.stop(); } catch { /* ignore */ } }, 1500);
    this.ambience = null;
  }

  stopAll() {
    for (const l of [...this.loops]) l.stop();
    this.stopAmbience();
  }
}

const _v = new Vector3();
