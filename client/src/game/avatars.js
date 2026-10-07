// Character models (from /models/characters.glb, with procedural fallbacks) and the
// interpolated avatars of other players.
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { GHOST, PF, ROLES } from '../../../shared/constants.js';

// ------------------------------------------------------------------ ghost shader
export function ghostMaterial(color = '#cdeeff') {
  return new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    uniforms: {
      uTime: { value: 0 }, uColor: { value: new THREE.Color(color) }, uOpacity: { value: 0.5 },
      uFrozen: { value: 0 }, uShimmer: { value: 0 }, uMinY: { value: 0 }, uMaxY: { value: 1.6 },
    },
    vertexShader: `uniform float uTime, uMinY, uMaxY, uFrozen;
      varying vec3 vN; varying vec3 vV; varying float vH; varying vec3 vW;
      void main(){
        vec3 p = position;
        float h = clamp((p.y - uMinY) / max(0.01, uMaxY - uMinY), 0.0, 1.0);
        float hem = 1.0 - smoothstep(0.0, 0.55, h);
        float wob = (1.0 - uFrozen);
        p.x += sin(uTime * 2.3 + p.y * 5.0 + p.z * 3.0) * 0.035 * hem * wob;
        p.z += cos(uTime * 1.9 + p.y * 4.0 + p.x * 3.0) * 0.035 * hem * wob;
        vH = h;
        vec4 wp = modelMatrix * vec4(p, 1.0);
        vW = wp.xyz;
        vec4 mv = viewMatrix * wp;
        vN = normalize(normalMatrix * normal);
        vV = normalize(-mv.xyz);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `uniform float uTime, uOpacity, uFrozen, uShimmer; uniform vec3 uColor;
      varying vec3 vN; varying vec3 vV; varying float vH; varying vec3 vW;
      void main(){
        float fres = pow(1.0 - abs(dot(normalize(vN), normalize(vV))), 2.0);
        vec3 ice = vec3(0.45, 0.72, 0.92);
        vec3 col = mix(uColor, vec3(1.0), fres * 0.6);
        col = mix(col, ice + fres * 0.25, uFrozen);
        float sh = 0.5 + 0.5 * sin(uTime * 14.0 + vW.y * 18.0 + vW.x * 6.0);
        float a = uOpacity * (0.32 + 0.68 * fres) * mix(1.0, 0.55 + 0.45 * sh, uShimmer);
        a *= smoothstep(0.0, 0.12, vH);
        a = mix(a, max(a, 0.82 * uOpacity), uFrozen);
        gl_FragColor = vec4(col * (1.0 - uFrozen * 0.15), a);
      }`,
  });
}

// ------------------------------------------------------------------ fallback models
function fallbackGhost() {
  const root = new THREE.Group();
  root.name = 'ghost';
  const prof = [];
  for (let i = 0; i <= 14; i++) {
    const t = i / 14;
    const y = 0.15 + t * 1.4;
    const r = t > 0.78 ? Math.sqrt(Math.max(0, 1 - ((t - 0.78) / 0.22) ** 2)) * 0.34 : 0.34 + (0.78 - t) * 0.22;
    prof.push(new THREE.Vector2(Math.max(0.001, r), y));
  }
  const body = new THREE.Mesh(new THREE.LatheGeometry(prof, 24), new THREE.MeshBasicMaterial({ name: 'ghost_cloth' }));
  body.name = 'ghost_body';
  const eyes = new THREE.Group();
  eyes.name = 'ghost_eyes';
  for (const x of [-0.1, 0.1]) {
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.05, 10, 8), new THREE.MeshBasicMaterial({ color: 0x050508, name: 'ghost_eyes' }));
    e.scale.set(1, 1.5, 0.4);
    e.position.set(x, 1.3, -0.3);
    eyes.add(e);
  }
  root.add(body, eyes);
  return root;
}

function fallbackHunter() {
  const root = new THREE.Group();
  root.name = 'hunter';
  const coat = new THREE.MeshStandardMaterial({ color: 0x3a2e28, roughness: 0.9 });
  const skin = new THREE.MeshStandardMaterial({ color: 0xc89f86, roughness: 0.8 });
  const hat = new THREE.MeshStandardMaterial({ color: 0x1d1a18, roughness: 0.8 });
  const brass = new THREE.MeshStandardMaterial({ color: 0xb08a3e, metalness: 1, roughness: 0.35 });
  const body = new THREE.Group();
  body.name = 'hunter_body';
  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.34, 1.15, 10), coat);
  torso.position.y = 0.95;
  const legs = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.5, 0.2), hat);
  legs.position.y = 0.25;
  body.add(torso, legs);
  const head = new THREE.Group();
  head.name = 'hunter_head';
  head.position.y = 1.55;
  const h = new THREE.Mesh(new THREE.SphereGeometry(0.13, 12, 10), skin);
  h.position.y = 0.1;
  const brim = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.02, 16), hat);
  brim.position.y = 0.2;
  const crown = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.15, 0.16, 14), hat);
  crown.position.y = 0.29;
  head.add(h, brim, crown);
  const arm = new THREE.Group();
  arm.name = 'hunter_arm';
  arm.position.set(0.26, 1.38, 0);
  const a = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.5, 8), coat);
  a.rotation.x = Math.PI / 2;
  a.position.z = -0.25;
  const gun = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.04, 0.3, 10), brass);
  gun.rotation.x = Math.PI / 2;
  gun.position.z = -0.55;
  const muzzle = new THREE.Object3D();
  muzzle.name = 'hunter_muzzle';
  muzzle.position.z = -0.72;
  arm.add(a, gun, muzzle);
  root.add(body, head, arm);
  return root;
}

function fallbackRelic() {
  const root = new THREE.Group();
  root.name = 'relic';
  const brass = new THREE.MeshStandardMaterial({ color: 0xb8913f, metalness: 1, roughness: 0.3 });
  const body = new THREE.Group();
  body.name = 'relic_body';
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.12, 0.05, 12), brass);
  base.position.y = 0.025;
  const cap = new THREE.Mesh(new THREE.ConeGeometry(0.1, 0.1, 12), brass);
  cap.position.y = 0.3;
  for (let i = 0; i < 4; i++) {
    const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.22, 4), brass);
    bar.position.set(Math.cos(i * Math.PI / 2) * 0.09, 0.16, Math.sin(i * Math.PI / 2) * 0.09);
    body.add(bar);
  }
  body.add(base, cap);
  const core = new THREE.Mesh(new THREE.SphereGeometry(0.07, 16, 12), new THREE.MeshStandardMaterial({ name: 'relic_glow', color: 0x7fffd4, emissive: 0x7fffd4, emissiveIntensity: 4 }));
  core.name = 'relic_core';
  core.position.y = 0.16;
  root.add(body, core);
  return root;
}

function fallbackRevealer() {
  const root = new THREE.Group();
  root.name = 'revealer';
  const brass = new THREE.MeshStandardMaterial({ color: 0xb08a3e, metalness: 1, roughness: 0.35 });
  const wood = new THREE.MeshStandardMaterial({ color: 0x4a2e1c, roughness: 0.7 });
  const grip = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.12, 0.05), wood);
  grip.position.set(0, -0.05, 0.02);
  grip.rotation.x = 0.3;
  const barrel = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.045, 0.28, 12), brass);
  barrel.rotation.x = Math.PI / 2;
  barrel.position.set(0, 0.03, -0.12);
  const bell = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.04, 0.08, 16, 1, true), brass);
  bell.rotation.x = Math.PI / 2;
  bell.position.set(0, 0.03, -0.3);
  const lens = new THREE.Mesh(new THREE.CircleGeometry(0.07, 18), new THREE.MeshStandardMaterial({ name: 'revealer_glow', color: 0xbff6ff, emissive: 0xbff6ff, emissiveIntensity: 2 }));
  lens.name = 'revealer_lens';
  lens.position.set(0, 0.03, -0.335);
  lens.rotation.y = Math.PI;
  const muzzle = new THREE.Object3D();
  muzzle.name = 'revealer_muzzle';
  muzzle.position.set(0, 0.03, -0.36);
  root.add(grip, barrel, bell, lens, muzzle);
  return root;
}

function fallbackAltarGlow() {
  const m = new THREE.Mesh(new THREE.RingGeometry(0.6, 0.8, 48).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ name: 'altar_rune', color: 0x7fffd4, transparent: true, side: THREE.DoubleSide }));
  m.name = 'altar_glow';
  m.position.y = 0.01;
  return m;
}

export class Characters {
  constructor() {
    this.models = {};
  }

  async load() {
    try {
      const gltf = await new GLTFLoader().loadAsync('/models/characters.glb');
      for (const name of ['ghost', 'hunter', 'relic', 'revealer', 'altar_glow']) {
        const o = gltf.scene.getObjectByName(name);
        if (o) {
          o.parent?.remove(o);
          o.position.set(0, 0, 0);
          this.models[name] = o;
        }
      }
    } catch (err) {
      console.warn('characters.glb unavailable, using fallback models', err?.message);
    }
    this.models.ghost ||= fallbackGhost();
    this.models.hunter ||= fallbackHunter();
    this.models.relic ||= fallbackRelic();
    this.models.revealer ||= fallbackRevealer();
    this.models.altar_glow ||= fallbackAltarGlow();
    this.models.revealer.traverse((o) => {
      if (!o.isMesh) return;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        if (m.name === 'revealer_filament') m.emissiveIntensity = Math.min(m.emissiveIntensity, 2.2);
      }
    });
    // ghosts: measure height for the shader's hem falloff
    const box = new THREE.Box3().setFromObject(this.models.ghost);
    this.ghostMinY = box.min.y;
    this.ghostMaxY = box.max.y;
  }

  make(name) {
    const o = this.models[name].clone(true);
    o.traverse((c) => {
      if (c.isMesh) {
        c.castShadow = name === 'hunter';
        c.material = Array.isArray(c.material) ? c.material.map((m) => m.clone()) : c.material.clone();
      }
    });
    return o;
  }

  makeGhost(color) {
    const o = this.make('ghost');
    const mat = ghostMaterial(color);
    mat.uniforms.uMinY.value = this.ghostMinY;
    mat.uniforms.uMaxY.value = this.ghostMaxY;
    const eyes = [];
    o.traverse((c) => {
      if (!c.isMesh) return;
      const names = (Array.isArray(c.material) ? c.material : [c.material]).map((m) => m.name);
      if (names.includes('ghost_eyes') || isUnder(c, 'ghost_eyes')) {
        c.material = new THREE.MeshBasicMaterial({ color: 0x05060a, transparent: true, depthWrite: false });
        eyes.push(c);
      } else {
        c.material = mat;
      }
      c.castShadow = false;
      c.renderOrder = 3;
    });
    o.userData.ghostMat = mat;
    o.userData.eyes = eyes;
    return o;
  }
}

function isUnder(o, name) {
  for (let p = o; p; p = p.parent) if (p.name === name) return true;
  return false;
}

// ------------------------------------------------------------------ remote avatars
const DELAY = 0.1;

export class Avatar {
  constructor(engine, info) {
    this.engine = engine;
    this.id = info.id;
    this.name = info.name;
    this.role = info.role;
    this.color = info.color;
    this.buf = [];
    this.visible = false;
    this.alpha = 0;
    this.flags = 0;
    this.lastSeen = -1;
    this.pos = new THREE.Vector3();
    this.yaw = 0;
    this.pitch = 0;
    this.walk = 0;
    const ch = engine.characters;
    if (this.role === ROLES.GHOST) {
      this.obj = ch.makeGhost(info.color);
      this.mat = this.obj.userData.ghostMat;
      this.ice = this.makeIce();
      this.obj.add(this.ice);
    } else {
      this.obj = ch.make('hunter');
      this.obj.scale.setScalar(0.94); // model is 1.83 m; players are 1.7 m
      this.head = this.obj.getObjectByName('hunter_head');
      this.arm = this.obj.getObjectByName('hunter_arm');
      this.muzzle = this.obj.getObjectByName('hunter_muzzle') || this.arm;
      // flashlight: a real spotlight (count fixed per match) plus a faint visible beam
      this.spot = new THREE.SpotLight(0xffe2b0, 0, 22, 0.42, 0.55, 1.6);
      this.spot.position.set(0, 0, 0);
      this.spotTarget = new THREE.Object3D();
      this.spotTarget.position.set(0, 0, -5);
      (this.arm || this.obj).add(this.spot, this.spotTarget);
      this.spot.target = this.spotTarget;
      this.beam = makeBeam();
      (this.muzzle || this.obj).add(this.beam);
    }
    this.obj.visible = false;
    engine.scene.add(this.obj);
  }

  makeIce() {
    const g = new THREE.Group();
    const mat = new THREE.MeshStandardMaterial({ color: 0x6fb6d8, emissive: 0x2a6f98, emissiveIntensity: 0.35, transparent: true, opacity: 0.55, roughness: 0.25, metalness: 0.0, depthWrite: false });
    for (let i = 0; i < 9; i++) {
      const m = new THREE.Mesh(new THREE.OctahedronGeometry(0.12 + Math.random() * 0.12, 0), mat);
      const a = (i / 9) * Math.PI * 2;
      m.position.set(Math.cos(a) * 0.38, 0.2 + Math.random() * 1.2, Math.sin(a) * 0.38);
      m.scale.y = 1.8 + Math.random();
      m.rotation.set(Math.random() - 0.5, Math.random() * 3, Math.random() - 0.5);
      g.add(m);
    }
    g.visible = false;
    return g;
  }

  push(e, now) {
    const [, x, y, z, yaw, pitch, flags] = e;
    if (now - this.lastSeen > 0.4) this.buf = []; // reappeared: don't slide from stale position
    this.lastSeen = now;
    this.flags = flags;
    this.buf.push({ t: now, x, y, z, yaw, pitch });
    if (this.buf.length > 30) this.buf.shift();
  }

  sample(now) {
    const t = now - DELAY;
    const b = this.buf;
    if (!b.length) return null;
    if (t <= b[0].t) return b[0];
    for (let i = b.length - 1; i >= 0; i--) {
      if (b[i].t <= t) {
        const a = b[i], c = b[i + 1];
        if (!c) return a;
        const k = (t - a.t) / (c.t - a.t);
        return { x: a.x + (c.x - a.x) * k, y: a.y + (c.y - a.y) * k, z: a.z + (c.z - a.z) * k, yaw: lerpAngle(a.yaw, c.yaw, k), pitch: a.pitch + (c.pitch - a.pitch) * k };
      }
    }
    return b[b.length - 1];
  }

  update(now, dt, viewer) {
    const present = now - this.lastSeen < 0.25;
    const s = this.sample(now);
    if (s) {
      const prev = this.pos.clone();
      this.pos.set(s.x, s.y, s.z);
      this.yaw = s.yaw;
      this.pitch = s.pitch;
      const sp = prev.distanceTo(this.pos) / Math.max(dt, 1e-3);
      this.walk += Math.min(sp, 7) * dt * 2.2;
      this.speed = sp;
    }
    const f = this.flags;
    let target = present ? 1 : 0;
    if (this.role === ROLES.GHOST) {
      let op = 0.55;
      if (f & PF.NEAR) {
        const d = viewer ? viewer.distanceTo(this.pos) : 2;
        op = THREE.MathUtils.clamp(1 - (d - 1.2) / GHOST.seeRadius, 0.12, 0.55);
      }
      if (f & PF.EXPOSED) op = 0.75;
      if (f & PF.PENALTY) op = 0.42;
      if (f & PF.FROZEN) op = 0.8;
      target *= op;
      this.alpha += (target - this.alpha) * Math.min(1, dt * 6);
      this.mat.uniforms.uOpacity.value = this.alpha;
      this.mat.uniforms.uTime.value = now + (+this.id % 7);
      this.mat.uniforms.uFrozen.value += (((f & PF.FROZEN) ? 1 : 0) - this.mat.uniforms.uFrozen.value) * Math.min(1, dt * 8);
      this.mat.uniforms.uShimmer.value = (f & PF.EXPOSED) ? 1 : 0;
      for (const e of this.obj.userData.eyes) e.material.opacity = Math.min(1, this.alpha * 1.6);
      this.ice.visible = !!(f & PF.FROZEN);
      this.obj.visible = this.alpha > 0.01;
      this.obj.position.copy(this.pos);
      this.obj.position.y += 0.08 + ((f & PF.FROZEN) ? 0 : Math.sin(now * 1.6 + +this.id) * 0.05);
      this.obj.rotation.y = this.yaw;
      if (this.obj.visible && !(f & PF.FROZEN) && Math.random() < dt * 6 * this.alpha) {
        this.engine.effects.wisps({ x: this.pos.x, y: this.pos.y + 0.25, z: this.pos.z }, this.color, 1);
      }
    } else {
      this.alpha = target;
      this.obj.visible = present || now - this.lastSeen < 1;
      this.obj.position.copy(this.pos);
      this.obj.rotation.y = this.yaw;
      const bob = Math.sin(this.walk * 2) * Math.min(1, (this.speed || 0) / 4);
      this.obj.position.y += Math.abs(bob) * 0.04;
      if (this.head) this.head.rotation.x = this.pitch * 0.6;
      if (this.arm) this.arm.rotation.x = this.pitch + bob * 0.04;
      const lit = this.engine.phase !== 'blind';
      this.spot.intensity = lit ? 26 : 0;
      this.beam.visible = lit && this.obj.visible;
    }
  }

  dispose() {
    this.engine.scene.remove(this.obj);
  }
}

function makeBeam() {
  const len = 9;
  const geo = new THREE.CylinderGeometry(Math.tan(0.36) * len, 0.05, len, 20, 1, true);
  geo.translate(0, len / 2, 0);
  geo.rotateX(-Math.PI / 2);
  const mat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    vertexShader: 'varying float vZ; varying vec3 vN; varying vec3 vV; void main(){ vZ = -position.z; vec4 mv = modelViewMatrix*vec4(position,1.0); vN = normalize(normalMatrix*normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix*mv; }',
    fragmentShader: `varying float vZ; varying vec3 vN; varying vec3 vV;
      void main(){ float f = 1.0 - clamp(vZ / ${len.toFixed(1)}, 0.0, 1.0); float edge = 1.0 - pow(abs(dot(vN, vV)), 0.6);
        gl_FragColor = vec4(1.0, 0.9, 0.7, f * f * 0.07 * (1.0 - edge * 0.6)); }`,
  });
  const m = new THREE.Mesh(geo, mat);
  m.renderOrder = 4;
  return m;
}

function lerpAngle(a, b, k) {
  let d = b - a;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  return a + d * k;
}
