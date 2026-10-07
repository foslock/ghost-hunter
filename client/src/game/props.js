// Client-side animation of interactive props. Each archetype defines an idle motion that is
// always running, a subtle variation (stays inside natural motion) and a big, loud event.
// All randomness comes from the event seed so every client animates identically.
import * as THREE from 'three';
import { ARCHETYPES } from '../../../shared/archetypes.js';

const TAU = Math.PI * 2;
const smooth = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x));
const bump = (t, rise, hold, fall) => smooth(t / rise) * (1 - smooth((t - rise - hold) / fall));
const decayOsc = (t, amp, period, decay) => (t < 0 ? 0 : amp * Math.exp(-t / decay) * Math.sin((TAU * t) / period));

function rng(seed) {
  let s = (seed >>> 0) || 1;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function noise1(t, ph) {
  return Math.sin(t * 1.7 + ph) * 0.5 + Math.sin(t * 3.1 + ph * 1.3) * 0.3 + Math.sin(t * 7.3 + ph * 2.1) * 0.2;
}

const AXES = { x: new THREE.Vector3(1, 0, 0), y: new THREE.Vector3(0, 1, 0), z: new THREE.Vector3(0, 0, 1) };
const _q = new THREE.Quaternion();
const _q2 = new THREE.Quaternion();
const _e = new THREE.Euler();
const _v = new THREE.Vector3();

// Wind ripple for cloth parts, injected into the mesh's standard material.
function clothMaterial(src, height, axis) {
  const m = src.clone();
  m.side = THREE.DoubleSide;
  const uniforms = { uTime: { value: 0 }, uAmp: { value: 0.04 }, uBillow: { value: 0 }, uH: { value: height }, uPhase: { value: Math.random() * 10 } };
  m.userData.cloth = uniforms;
  const ax = axis === 'x' ? 'x' : axis === 'y' ? 'y' : 'z';
  m.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uTime, uAmp, uBillow, uH, uPhase;')
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        float w = clamp(-position.y / max(uH, 0.01), 0.0, 1.0);
        float ripple = sin(position.x * 5.0 + uTime * 2.3 + uPhase) * 0.6 + sin(position.x * 9.0 - uTime * 3.7 + position.y * 4.0) * 0.4;
        transformed.${ax} += w * (uAmp * ripple + uBillow * (0.6 + 0.4 * sin(position.x * 3.0 + uTime * 5.0)));
        transformed.y += w * w * abs(uBillow) * 0.25;`);
  };
  m.customProgramCacheKey = () => `cloth_${ax}`;
  return m;
}

export class PropCtl {
  constructor(def, root, scene, engine) {
    this.def = def;
    this.id = def.id;
    this.type = def.type;
    this.arch = ARCHETYPES[def.type] || ARCHETYPES.jolt;
    this.params = def.params || {};
    this.root = root;
    this.engine = engine;
    this.events = [];
    this.ph = (hash(def.id) % 1000) / 159.2;
    this.parts = {};
    this.flames = [];
    this.cloths = [];
    this.bulbs = [];
    this.dancers = [];
    this.lights = [];
    this.meshes = [];
    this.persist = { yaw: 0, x: 0, z: 0, spin: 0 };
    this.timeScale = { clock: 0 };
    this.flameState = 1;
    const prefix = `P_${def.id}_`;
    root.traverse((o) => {
      if (o.isMesh) {
        o.userData.propId = def.id;
        this.meshes.push(o);
      }
      if (!o.name.startsWith(prefix) || o.isMesh) return;
      const part = o.name.slice(prefix.length);
      if (part.endsWith('_m')) return;
      this.parts[part] = o;
      o.userData.base = { q: o.quaternion.clone(), p: o.position.clone(), s: o.scale.clone() };
      if (part.startsWith('flame')) this.flames.push(o);
      else if (part.startsWith('cloth')) this.cloths.push(o);
      else if (part.startsWith('bulb')) this.bulbs.push(o);
      else if (part.startsWith('dancer')) this.dancers.push(o);
    });
    this.pivot = this.parts.pivot || this.parts.body || root;
    if (!this.pivot.userData.base) this.pivot.userData.base = { q: this.pivot.quaternion.clone(), p: this.pivot.position.clone(), s: this.pivot.scale.clone() };
    for (const c of this.cloths) {
      c.traverse((o) => {
        if (!o.isMesh) return;
        o.geometry.computeBoundingBox();
        const h = Math.max(0.1, -o.geometry.boundingBox.min.y);
        o.material = clothMaterial(o.material, h, this.params.axis || 'z');
        o.userData.cloth = o.material.userData.cloth;
      });
    }
    for (const b of this.bulbs) {
      b.traverse((o) => {
        if (o.isMesh && o.material) {
          o.material = o.material.clone();
          o.userData.baseEmissive = o.material.emissiveIntensity || 1;
        }
      });
    }
    // world-space centre for sounds/targeting
    const box = new THREE.Box3().setFromObject(root);
    this.center = box.getCenter(new THREE.Vector3());
    this.size = box.getSize(new THREE.Vector3()).length();
  }

  attachLight(light, base) {
    this.lights.push({ light, base });
  }

  trigger(kind, seed, now) {
    const r = rng(seed);
    const ev = { kind, t0: now, r: [r(), r(), r(), r()], seed };
    if (kind === 'b') this.events = this.events.filter((e) => e.kind !== 'b');
    this.events.push(ev);
    this.onTrigger(ev);
  }

  sound(name, opts = {}) {
    this.engine.audio.play(name, [this.center.x, this.center.y, this.center.z], opts);
  }

  onTrigger(ev) {
    const P = this.params;
    const big = ev.kind === 'b';
    const snd = P.sound || this.arch.sound;
    switch (this.type) {
      case 'hinge':
        if (big) this.sound(snd, { profile: '_big', delay: (P.closed || 0) !== 0 ? 0.16 : 0.62 });
        else this.sound('creak', { profile: '_soft', volume: 0.22, rate: 1.3 });
        break;
      case 'clock':
        if (big) for (let i = 0; i < 3; i++) this.sound(snd, { profile: '_big', delay: i * 1.15 });
        else this.timeScale.subtleUntil = ev.t0 + 8;
        break;
      case 'jolt':
        if (big) this.sound(snd, { profile: '_big', delay: 0.5 });
        else {
          const a = ev.r[0] * TAU;
          const d = 0.02 + ev.r[1] * 0.04;
          [this.persist.x, this.persist.z] = clampLen(this.persist.x + Math.cos(a) * d, this.persist.z + Math.sin(a) * d, 0.3);
          this.persist.yaw += (ev.r[2] - 0.5) * 0.16;
        }
        break;
      case 'music': {
        const inst = P.instrument || 'piano';
        if (big) this.sound(inst, { profile: '_big' });
        else this.sound(`${inst}_soft`, { profile: '_soft', volume: 0.8 });
        break;
      }
      case 'bell':
        if (big) this.sound('bell', { profile: '_big', rate: (P.tone || 420) / 420 });
        else this.sound('bell_soft', { profile: '_soft', rate: (P.tone || 420) / 420 });
        break;
      case 'flicker':
        if (big) this.sound(snd, { profile: '_big' });
        break;
      case 'spin':
        if (!big) this.persist.spin += (ev.r[0] < 0.5 ? -1 : 1) * (0.35 + ev.r[1] * 0.3);
        else this.sound(snd, { profile: '_big' });
        break;
      case 'foliage':
        if (big) {
          this.sound(snd, { profile: '_big' });
          this.engine.effects?.leaves(this.center, this.params.leaf || '#8a7a3a', 40);
        } else this.sound('rustle', { profile: '_soft', volume: 0.15 });
        break;
      case 'flame':
        if (big) this.sound(snd, { profile: '_big' });
        break;
      default:
        if (big) this.sound(snd, { profile: '_big' });
    }
    if (big && this.type === 'jolt') setTimeout(() => this.engine.effects?.dust(this.center, 14), 500);
  }

  // offsets from events of a given kind, summed
  active(now, kind, dur) {
    return this.events.filter((e) => e.kind === kind && now - e.t0 < dur);
  }

  update(now, dt, wind) {
    const P = this.params;
    this.events = this.events.filter((e) => now - e.t0 < 12);
    const base = this.pivot.userData.base;
    const t = now + this.ph;
    switch (this.type) {
      case 'hinge': {
        const dir = P.dir ?? 1;
        let o = 0.012 * Math.sin(t * 0.6) + 0.006 * Math.sin(t * 1.7);
        for (const e of this.active(now, 's', 5)) o += 0.21 * bump(now - e.t0, 1.1, 1.0, 1.8);
        for (const e of this.active(now, 'b', 7)) {
          const τ = now - e.t0;
          const closed = P.closed || 0;
          if (closed !== 0) {
            if (τ < 0.16) o = closed * smooth(τ / 0.16) ** 2;
            else if (τ < 2.4) o = closed + decayOsc(τ - 0.16, -0.06 * Math.sign(closed), 0.18, 0.2);
            else o = closed * (1 - smooth((τ - 2.4) / 3));
          } else {
            const open = P.open ?? 1.3;
            if (τ < 0.35) o = open * smooth(τ / 0.35);
            else if (τ < 0.5) o = open;
            else if (τ < 0.62) o = open * (1 - ((τ - 0.5) / 0.12) ** 2);
            else o = Math.abs(decayOsc(τ - 0.62, 0.12, 0.3, 0.25));
          }
        }
        this.rotate(base, AXES[P.axis || 'y'], dir * o);
        break;
      }
      case 'swing': {
        const amp = P.amp ?? 0.03, per = P.period ?? 2.6;
        const axes = P.axes || 'xz';
        let ax = axes.includes('x') ? amp * Math.sin((TAU * t) / per) : 0;
        let az = axes.includes('z') ? amp * 0.6 * Math.sin((TAU * t) / (per * 1.13) + 1.3) : 0;
        for (const e of this.events) {
          const τ = now - e.t0;
          const big = e.kind === 'b';
          const a = big ? 0.5 : 0.075;
          const dirA = e.r[0] * TAU;
          const s = decayOsc(τ, a, per * (big ? 0.85 : 1), big ? 2.6 : 2.8);
          if (axes === 'z') az += s * (e.r[1] < 0.5 ? -1 : 1);
          else if (axes === 'x') ax += s;
          else { ax += s * Math.cos(dirA); az += s * Math.sin(dirA); }
        }
        _e.set(ax, 0, az);
        this.pivot.quaternion.copy(base.q).multiply(_q.setFromEuler(_e));
        break;
      }
      case 'rock': {
        const per = P.period ?? 1.6;
        let a = 0.004 * Math.sin(t * 0.9);
        for (const e of this.events) {
          const τ = now - e.t0;
          a += e.kind === 'b' ? decayOsc(τ, 0.3, per * 0.85, 3.2) : decayOsc(τ, 0.065, per, 2.6);
        }
        this.rotate(base, AXES[P.axis || 'x'], a);
        break;
      }
      case 'spin': {
        const speed = P.speed ?? 0;
        let a = this.persist.spinAcc = (this.persist.spinAcc || 0) + speed * dt;
        a += (P.wobble ?? 0.02) * Math.sin(t * 0.5);
        this.persist.spinShown = (this.persist.spinShown || 0) + (this.persist.spin - (this.persist.spinShown || 0)) * Math.min(1, dt * 1.6);
        a += this.persist.spinShown;
        for (const e of this.active(now, 'b', 6)) {
          const τ = now - e.t0;
          a += (e.r[0] < 0.5 ? -1 : 1) * 6 * Math.PI * (1 - Math.exp(-τ / 1.2));
        }
        this.rotate(base, AXES[P.axis || 'y'], a);
        break;
      }
      case 'clock': {
        let rate = 1;
        if (this.timeScale.subtleUntil && now < this.timeScale.subtleUntil) rate = -1;
        for (const e of this.active(now, 'b', 3.5)) rate = 40;
        this.timeScale.clock += dt * rate;
        const sec = this.timeScale.clock;
        const tickA = Math.floor(sec) + smooth((sec % 1) / 0.12);
        const ax = AXES[P.axis || 'z'];
        const mn = this.parts.minute, hr = this.parts.hour, pd = this.parts.pend;
        if (mn) mn.quaternion.copy(mn.userData.base.q).multiply(_q.setFromAxisAngle(ax, (-tickA * TAU) / 60));
        if (hr) hr.quaternion.copy(hr.userData.base.q).multiply(_q.setFromAxisAngle(ax, (-tickA * TAU) / 720 - 1.2));
        if (pd) {
          let amp = 0.12;
          if (rate < 0) amp = 0.05;
          if (rate > 1) amp = 0.35;
          pd.quaternion.copy(pd.userData.base.q).multiply(_q.setFromAxisAngle(ax, amp * Math.sin(this.timeScale.clock * Math.PI)));
        }
        break;
      }
      case 'foliage': {
        const amp = P.amp ?? 0.015;
        const g = noise1(t * 0.8, this.ph) * amp + amp * 0.6;
        let ax = wind.x * g, az = wind.z * g;
        for (const e of this.events) {
          const τ = now - e.t0;
          if (e.kind === 's') {
            const k = 0.05 * bump(τ, 0.8, 0.6, 1.2);
            const a = Math.atan2(-wind.z, -wind.x) + (e.r[0] - 0.5);
            ax += Math.cos(a) * k; az += Math.sin(a) * k;
          } else {
            const k = 0.11 * Math.exp(-τ / 1.1);
            ax += k * Math.sin(τ * 19); az += k * Math.sin(τ * 23 + 1);
          }
        }
        _e.set(az, 0, -ax);
        this.pivot.quaternion.copy(base.q).multiply(_q.setFromEuler(_e));
        break;
      }
      case 'jolt': {
        let y = 0, rx = 0, rz = 0;
        this.persist.yawShown = (this.persist.yawShown || 0) + (this.persist.yaw - (this.persist.yawShown || 0)) * Math.min(1, dt * 10);
        this.persist.xs = (this.persist.xs || 0) + (this.persist.x - (this.persist.xs || 0)) * Math.min(1, dt * 10);
        this.persist.zs = (this.persist.zs || 0) + (this.persist.z - (this.persist.zs || 0)) * Math.min(1, dt * 10);
        for (const e of this.active(now, 'b', 2)) {
          const τ = now - e.t0;
          if (τ < 0.5) {
            y = 0.38 * Math.sin((Math.PI * τ) / 0.5);
            rx = 0.25 * Math.sin(τ * 14) * (e.r[0] - 0.5);
            rz = 0.25 * Math.sin(τ * 11) * (e.r[1] - 0.5);
          } else {
            y = Math.abs(decayOsc(τ - 0.5, 0.05, 0.25, 0.12));
            if (!e.landed) {
              e.landed = true;
              this.persist.yaw += (e.r[2] < 0.5 ? -1 : 1) * (0.2 + e.r[3] * 0.35);
            }
          }
        }
        this.pivot.position.set(base.p.x + this.persist.xs, base.p.y + y, base.p.z + this.persist.zs);
        _e.set(rx, this.persist.yawShown, rz);
        this.pivot.quaternion.copy(base.q).multiply(_q.setFromEuler(_e));
        break;
      }
      case 'music': {
        if (this.parts.pivot) {
          let a = 0;
          for (const e of this.events) {
            const τ = now - e.t0;
            a += e.kind === 'b' ? (τ < 0.25 ? 0.35 * Math.sin((Math.PI * τ) / 0.25) : decayOsc(τ - 0.25, 0.04, 0.2, 0.2)) : 0.04 * Math.sin(Math.min(1, τ / 0.3) * Math.PI);
          }
          this.rotate(this.parts.pivot.userData.base, AXES[P.axis || 'x'], -a, this.parts.pivot);
        }
        break;
      }
      case 'bell': {
        let a = 0;
        for (const e of this.events) {
          const τ = now - e.t0;
          a += e.kind === 'b' ? decayOsc(τ, 0.6, 1.1, 2.5) : decayOsc(τ, 0.03, 0.5, 1.2);
        }
        this.rotate(base, AXES[P.axis || 'z'], a);
        break;
      }
      case 'bob': {
        const amp = P.amp ?? 0.05;
        let y = amp * Math.sin((TAU * t) / 3.2), x = 0, z = 0;
        for (const e of this.events) {
          const τ = now - e.t0;
          if (e.kind === 's') {
            const k = 0.13 * bump(τ, 1.0, 0.8, 1.4);
            x += Math.cos(e.r[0] * TAU) * k; z += Math.sin(e.r[0] * TAU) * k;
          } else {
            y += τ < 0.3 ? 1.0 * smooth(τ / 0.3) : 1.0 * Math.exp(-(τ - 0.3) / 0.5) * Math.cos((τ - 0.3) * 9);
          }
        }
        this.pivot.position.set(base.p.x + x, base.p.y + y, base.p.z + z);
        break;
      }
      default:
        break;
    }
    this.decorate(now, dt, t);
  }

  rotate(base, axis, angle, node = this.pivot) {
    node.quaternion.copy(base.q).multiply(_q2.setFromAxisAngle(axis, angle));
  }

  decorate(now, dt, t) {
    // flames: flicker, gutter (subtle) or flare-then-out (big, flame archetype only)
    let flameK = 1, lean = 0, lightK = 1;
    if (this.flames.length || this.lights.length) {
      for (const e of this.events) {
        const τ = now - e.t0;
        if (this.type === 'flame' && e.kind === 's') {
          const b = bump(τ, 0.4, 1.2, 1.0);
          lean += 0.5 * b * (e.r[0] < 0.5 ? -1 : 1);
          flameK *= 1 - 0.4 * b;
          lightK *= 1 - 0.45 * b;
        } else if (this.type === 'flame' && e.kind === 'b') {
          if (τ < 0.6) { flameK *= 1 + 1.6 * Math.sin((Math.PI * τ) / 0.6); lightK *= 1 + 2.2 * Math.sin((Math.PI * τ) / 0.6); }
          else if (τ < 5.5) { flameK *= 0.01; lightK *= 0.02; }
          else { const k = smooth((τ - 5.5) / 1.0); flameK *= Math.max(0.01, k); lightK *= Math.max(0.02, k); }
        } else if (this.type === 'swing' && e.kind === 'b') {
          lightK *= 1 - 0.5 * Math.max(0, Math.sin(τ * 23)) * Math.exp(-τ / 1.5);
        }
      }
    }
    // flicker archetype drives bulbs + lights
    let bulbK = 1;
    if (this.type === 'flicker') {
      bulbK = 1 - 0.04 * Math.max(0, Math.sin(t * 13) * Math.sin(t * 0.7));
      for (const e of this.events) {
        const τ = now - e.t0;
        if (e.kind === 's' && τ < 0.8) bulbK *= (Math.sin(τ * 31 + e.r[0] * 9) > 0.1 ? 1 : 0.15);
        if (e.kind === 'b') {
          if (τ < 2.6) bulbK *= Math.sin(τ * 47 + Math.sin(τ * 13) * 4) > 0 ? 1.3 : 0.05;
          else if (τ < 4.2) bulbK *= 0.03;
          else if (τ < 5.0) bulbK *= smooth((τ - 4.2) / 0.8);
        }
      }
      lightK *= bulbK;
    }
    for (let i = 0; i < this.flames.length; i++) {
      const f = this.flames[i];
      const b = f.userData.base;
      const n = noise1(t * 6 + i * 3.1, this.ph + i);
      const k = flameK * (1 + 0.12 * n);
      f.scale.set(b.s.x * k * (1 - 0.05 * n), b.s.y * k * (1 + 0.1 * n), b.s.z * k * (1 - 0.05 * n));
      _e.set(lean * 0.6 + 0.06 * n, 0, lean + 0.05 * Math.sin(t * 5 + i));
      f.quaternion.copy(b.q).multiply(_q.setFromEuler(_e));
    }
    for (const b of this.bulbs) {
      b.traverse((o) => {
        if (o.isMesh && o.material) o.material.emissiveIntensity = (o.userData.baseEmissive ?? 1) * bulbK;
      });
    }
    if (this.lights.length) {
      const fl = this.flames.length ? 0.88 + 0.12 * noise1(t * 7, this.ph) : 1;
      for (const L of this.lights) L.light.intensity = L.base * lightK * fl;
    }
    if (this.cloths.length) {
      let amp = this.params.amp ?? 0.04, billow = 0;
      for (const e of this.events) {
        const τ = now - e.t0;
        if (e.kind === 's') amp += 0.09 * bump(τ, 0.8, 1.2, 1.5);
        else billow += 0.55 * bump(τ, 0.35, 0.5, 2.0) * (e.r[0] < 0.5 ? -1 : 1);
      }
      for (const c of this.cloths) {
        c.traverse((o) => {
          const u = o.userData.cloth;
          if (!u) return;
          u.uTime.value = now;
          u.uAmp.value = amp;
          u.uBillow.value = billow;
        });
      }
    }
    if (this.dancers.length) {
      let spin = 0.0;
      for (const e of this.events) if (now - e.t0 < (e.kind === 'b' ? 6 : 3)) spin = e.kind === 'b' ? 6 : 2;
      for (const d of this.dancers) d.rotateY(spin * dt);
    }
  }
}

function clampLen(x, z, max) {
  const l = Math.hypot(x, z);
  return l > max ? [(x / l) * max, (z / l) * max] : [x, z];
}

export function hash(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}
