// One round, client side: loads the map, renders, runs the local player and reacts to the
// server's snapshots and events.
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { CollisionWorld } from '../../../shared/collision.js';
import { ARCHETYPES } from '../../../shared/archetypes.js';
import { CLIENT_SEND_RATE, GHOST, HUNTER, PF, PHASE, RELIC, ROLES } from '../../../shared/constants.js';
import { PropCtl } from './props.js';
import { Effects } from './effects.js';
import { Avatar } from './avatars.js';
import { LocalPlayer } from './player.js';
import { Hud, MAX_CD } from './hud.js';
import { Input } from './input.js';

const mapModules = import.meta.glob('../../../shared/maps/*.json');

export async function loadMapData(id) {
  const loader = mapModules[`../../../shared/maps/${id}.json`];
  if (!loader) throw new Error(`unknown map ${id}`);
  return (await loader()).default;
}

const gltfCache = new Map();
function loadGLB(url) {
  if (!gltfCache.has(url)) gltfCache.set(url, new GLTFLoader().loadAsync(url));
  return gltfCache.get(url);
}

const FinalShader = {
  uniforms: {
    tDiffuse: { value: null }, uTime: { value: 0 }, uTint: { value: new THREE.Color(1, 1, 1) }, uTintAmt: { value: 0 },
    uDesat: { value: 0 }, uVignette: { value: 0.35 }, uBlind: { value: 0 }, uFrozen: { value: 0 }, uAlarm: { value: 0 },
  },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uTime, uTintAmt, uDesat, uVignette, uBlind, uFrozen, uAlarm; uniform vec3 uTint;
    varying vec2 vUv;
    void main(){
      vec4 c = texture2D(tDiffuse, vUv);
      float l = dot(c.rgb, vec3(0.299, 0.587, 0.114));
      c.rgb = mix(c.rgb, vec3(l), uDesat);
      c.rgb = mix(c.rgb, c.rgb * uTint * 1.25, uTintAmt);
      vec2 d = vUv - 0.5;
      float r = length(d * vec2(1.6, 1.0));
      c.rgb *= 1.0 - smoothstep(0.35, 1.05, r) * uVignette;
      // frozen: icy rim + frost noise
      float n = fract(sin(dot(floor(vUv * 180.0), vec2(12.9898, 78.233))) * 43758.5453);
      float frost = smoothstep(0.45, 0.95, r + n * 0.12) * uFrozen;
      c.rgb = mix(c.rgb, vec3(0.75, 0.92, 1.0), frost * 0.85);
      c.rgb = mix(c.rgb, vec3(l) * vec3(0.7, 0.85, 1.1), uFrozen * 0.5);
      // alarm: red pulse at the edges (exposed)
      c.rgb += vec3(0.6, 0.05, 0.05) * smoothstep(0.5, 1.1, r) * uAlarm * (0.6 + 0.4 * sin(uTime * 8.0));
      c.rgb *= 1.0 - uBlind;
      gl_FragColor = c;
    }`,
};

export class GameView {
  constructor(app, start) {
    this.app = app;
    this.net = app.net;
    this.audio = app.audio;
    this.renderer = app.renderer;
    this.characters = app.characters;
    this.start = start;
    this.me = start.you.id;
    this.role = start.you.role;
    this.isGhost = this.role === ROLES.GHOST;
    this.roster = new Map(start.roster.map((r) => [r.id, r]));
    this.phase = PHASE.BLIND;
    this.snap = null;
    this.avatars = new Map();
    this.props = new Map();
    this.unsub = [];
    this.disposed = false;
    this.sendAcc = 0;
    this.clock = new THREE.Clock();
    this.wind = new THREE.Vector3(1, 0, 0.3).normalize();
    this.target = null;
    this.localRayAt = -99;
    this.relicVis = { pos: new THREE.Vector3(), has: false };
  }

  // ---------------------------------------------------------------- setup
  async init(onProgress) {
    const mapId = this.start.map;
    onProgress?.('Reading the map…');
    const [map, gltf] = await Promise.all([loadMapData(mapId), loadGLB(`/maps/${mapId}.glb`)]);
    this.map = map;
    this.world = new CollisionWorld(map.colliders);
    onProgress?.('Lighting candles…');
    const scene = (this.scene = new THREE.Scene());
    const env = map.env || {};
    this.env = env;
    const sky = new THREE.Color(env.sky || '#101320');
    scene.background = sky;
    const fog = env.fog || { color: env.sky || '#101320', near: 8, far: 50 };
    scene.fog = new THREE.Fog(fog.color, fog.near, fog.far * (this.isGhost ? 1.25 : 1));
    const hemi = env.hemi || { sky: '#7c88b8', ground: '#2a2018', intensity: 0.5 };
    this.hemi = new THREE.HemisphereLight(hemi.sky, hemi.ground, (hemi.intensity ?? 0.5) * (this.isGhost ? 2.6 : 1.15));
    scene.add(this.hemi);
    if (this.isGhost) scene.add(new THREE.AmbientLight(0x8fb8d8, 0.25));
    const bounds = map.bounds;
    const cx = (bounds[0] + bounds[2]) / 2, cz = (bounds[1] + bounds[3]) / 2;
    const span = Math.max(bounds[2] - bounds[0], bounds[3] - bounds[1]);
    if (env.moon) {
      const d = new THREE.Vector3(...(env.moon.dir || [-0.4, -1, -0.3])).normalize();
      const moon = new THREE.DirectionalLight(env.moon.color || '#9fb4ff', (env.moon.intensity ?? 0.6) * 2.2);
      moon.position.set(cx, 0, cz).addScaledVector(d, -80);
      moon.target.position.set(cx, 0, cz);
      if (env.moon.shadows !== false) {
        moon.castShadow = true;
        moon.shadow.mapSize.set(4096, 4096);
        const s = moon.shadow.camera;
        s.left = -span * 0.6; s.right = span * 0.6; s.top = span * 0.6; s.bottom = -span * 0.6;
        s.near = 1; s.far = 220;
        moon.shadow.bias = -0.0006;
        moon.shadow.normalBias = 0.04;
      }
      scene.add(moon, moon.target);
      this.moon = moon;
    }
    if (env.stars) scene.add(makeSky(env, cx, cz));

    const level = gltf.scene.clone(true);
    level.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        for (const m of mats) {
          if (m.emissiveIntensity > 0 && m.emissive && m.emissive.getHex() !== 0) m.toneMapped = true;
          m.shadowSide = THREE.FrontSide;
        }
      }
    });
    scene.add(level);
    this.level = level;
    this.effects = new Effects(scene, this);

    // props
    for (const def of map.props) {
      const root = level.getObjectByName(`P_${def.id}`);
      if (!root) continue;
      this.props.set(def.id, new PropCtl(def, root, scene, this));
    }
    this.propMeshes = [];
    for (const p of this.props.values()) this.propMeshes.push(...p.meshes);

    // lights
    const scale = env.lightScale ?? 9;
    for (const l of map.lights) {
      const light = new THREE.PointLight(l.color, l.intensity * scale, l.distance * 1.15, 1.6);
      light.position.set(...l.pos);
      const prop = l.prop && this.props.get(l.prop);
      const node = prop && l.part ? (prop.parts[l.part] || prop.root) : prop?.root;
      if (node) {
        node.updateWorldMatrix(true, false);
        node.worldToLocal(light.position);
        node.add(light);
        prop.attachLight(light, light.intensity);
      } else {
        scene.add(light);
        if (l.flicker) this.flickerLights = [...(this.flickerLights || []), { light, base: light.intensity, k: l.flicker, ph: Math.random() * 9 }];
      }
    }

    // camera + view models
    this.camera = new THREE.PerspectiveCamera(this.app.settings.fov || 75, innerWidth / innerHeight, 0.05, 400);
    scene.add(this.camera);
    if (!this.isGhost) {
      const spot = new THREE.SpotLight(0xffe7c0, 34, 26, 0.45, 0.6, 1.5);
      spot.castShadow = true;
      spot.shadow.mapSize.set(1024, 1024);
      spot.shadow.bias = -0.0008;
      spot.shadow.camera.near = 0.3;
      spot.position.set(0.2, -0.18, -0.8); // in front of the view model so it doesn't light it
      const tgt = new THREE.Object3D();
      tgt.position.set(0.05, -0.3, -7);
      this.camera.add(spot, tgt);
      spot.target = tgt;
      this.flashlight = spot;
      this.viewModel = this.characters.make('revealer');
      this.viewModel.position.set(0.24, -0.24, -0.42);
      this.viewModel.rotation.set(0.02, -0.05, 0);
      this.viewModel.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.renderOrder = 10; } });
      this.camera.add(this.viewModel);
      this.lens = this.viewModel.getObjectByName('revealer_lens');
    } else {
      this.heldRelic = this.characters.make('relic');
      this.heldRelic.scale.setScalar(0.9);
      this.heldRelic.position.set(0, -0.36, -0.55);
      this.heldRelic.visible = false;
      this.camera.add(this.heldRelic);
    }

    // relic + altar markers
    this.relic = this.characters.make('relic');
    this.relic.visible = false;
    this.relicLight = new THREE.PointLight(0x7fffd4, 0, 5, 2);
    this.relic.add(this.relicLight);
    this.relicLight.position.y = 0.25;
    scene.add(this.relic);
    if (this.isGhost) {
      this.altarSpawn = this.characters.make('altar_glow');
      this.altarCapture = this.characters.make('altar_glow');
      for (const a of [this.altarSpawn, this.altarCapture]) {
        a.traverse((o) => { if (o.isMesh) { o.material.transparent = true; o.material.depthWrite = false; o.material.blending = THREE.AdditiveBlending; o.renderOrder = 2; } });
        a.visible = false;
        scene.add(a);
      }
      this.captureBeacon = makeBeacon();
      scene.add(this.captureBeacon);
    }

    // avatars for everyone else
    for (const r of this.start.roster) if (r.id !== this.me) this.avatars.set(r.id, new Avatar(this, r));

    // local player
    this.player = new LocalPlayer(this.role, this.world, this.start.you.pos, this.start.you.yaw);
    this.player.tpSeq = this.start.you.seq;

    // post-processing
    const size = this.renderer.getSize(new THREE.Vector2());
    const composer = new EffectComposer(this.renderer);
    composer.addPass(new RenderPass(scene, this.camera));
    this.bloom = new UnrealBloomPass(size, 0.55, 0.6, 0.82);
    this.bloom.enabled = this.app.bloomEnabled ? this.app.bloomEnabled() : true;
    composer.addPass(this.bloom);
    this.final = new ShaderPass(FinalShader);
    composer.addPass(this.final);
    composer.addPass(new OutputPass());
    this.composer = composer;
    this.renderer.toneMappingExposure = (env.exposure ?? 1) * (this.isGhost ? 1.15 : 1);
    if (this.isGhost) {
      this.final.uniforms.uTint.value.set(0.75, 0.95, 1.1);
      this.final.uniforms.uTintAmt.value = 0.35;
      this.final.uniforms.uDesat.value = 0.25;
    }

    // UI + input
    this.hud = new Hud(document.getElementById('hud'), this.role, map.name, map.penalty?.label);
    this.input = new Input(this.renderer.domElement);
    this.bindInput();
    this.bindNet();
    this.audio.startAmbience(env.ambience || (env.moon ? 'wind' : 'indoor'));
    this.hum = this.audio.loop('hum', [0, 0, 0]);
    this.resize();
    this._resize = () => this.resize();
    window.addEventListener('resize', this._resize);
    // warm up shaders so the first frames don't hitch
    this.renderer.compile(scene, this.camera);
  }

  resize() {
    const w = innerWidth, h = innerHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
    this.composer.setSize(w, h);
    this.effects.particles.points.material.uniforms.uScale.value = h * 0.9;
  }

  bindInput() {
    const inp = this.input;
    const ghostAct = (fn) => () => { if (this.isGhost && this.canAct()) fn(); };
    inp.on('mouse0', () => {
      if (this.isGhost) { if (this.canAct(true)) this.doSnap(); } else this.doRay();
    });
    inp.on('key:KeyF', ghostAct(() => this.doWhistle()));
    inp.on('key:KeyE', ghostAct(() => this.doManip('s')));
    inp.on('key:KeyQ', ghostAct(() => this.doManip('b')));
    inp.on('key:KeyG', () => { if (this.isGhost) this.net.send({ t: 'drop' }); });
    inp.on('key:Tab', () => { this.showScores = true; });
    inp.on('keyup:Tab', () => { this.showScores = false; });
    inp.on('locked', () => this.app.ui.hidePause());
    inp.on('unlocked', () => { if (!this.disposed && this.phase !== PHASE.RESULTS) this.app.ui.showPause(this); });
  }

  canAct(allowPenalty = false) {
    const y = this.snap?.you;
    if (!y || this.phase === PHASE.RESULTS) return false;
    if (y.fz > 0) return false;
    if (y.pn > 0 && !allowPenalty) return false;
    return true;
  }

  bindNet() {
    const on = (t, fn) => this.unsub.push(this.net.on(t, fn));
    on('s', (m) => this.onSnapshot(m));
    on('tp', (m) => this.player.teleport(m.p, m.yaw, m.seq));
    on('end', (m) => this.onEnd(m));
  }

  // ---------------------------------------------------------------- actions
  doSnap() {
    this.audio.play('snap', null, { volume: 0.55 });
    this.net.send({ t: 'snap' });
    this.snapHand = performance.now();
  }

  doWhistle() {
    if ((this.snap?.you.wc ?? 0) > 0) return;
    this.audio.play('whistle', null, { volume: 0.5 });
    this.net.send({ t: 'whistle' });
  }

  doManip(k) {
    if (!this.target) return;
    if (k === 'b' && (this.snap?.you.bc ?? 0) > 0) return;
    this.net.send({ t: 'manip', prop: this.target.id, k });
  }

  doRay() {
    const y = this.snap?.you;
    if (!y || this.phase !== PHASE.PLAY) return;
    const now = performance.now() / 1000;
    if (y.rc > 0 || now - this.localRayAt < HUNTER.rayCooldown) return;
    this.localRayAt = now;
    const dir = this.player.forward(new THREE.Vector3());
    const origin = this.camera.position.clone();
    this.effects.ray(origin.clone().addScaledVector(dir, 0.3).add(new THREE.Vector3(0, -0.12, 0)), dir);
    this.audio.play('ray', null, { volume: 0.7 });
    this.recoil = 1;
    this.net.send({ t: 'ray', d: [dir.x, dir.y, dir.z] });
  }

  // ---------------------------------------------------------------- network
  onSnapshot(m) {
    const now = this.clock.elapsedTime;
    const prevPhase = this.phase;
    this.snap = m;
    this.phase = m.ph;
    if (prevPhase === PHASE.BLIND && m.ph === PHASE.PLAY) this.audio.play('go', null, { volume: 0.8 });
    const seen = new Set();
    for (const e of m.pl) {
      const a = this.avatars.get(e[0]);
      if (!a) continue;
      a.push(e, now);
      seen.add(e[0]);
    }
    this.player.carrying = !!m.you.ca;
    if (m.ev) for (const ev of m.ev) this.onEvent(ev);
  }

  onEvent(ev) {
    const now = this.clock.elapsedTime;
    const name = (id) => this.roster.get(id)?.name || 'Someone';
    switch (ev.e) {
      case 'snap':
        this.audio.play('snap', ev.p);
        this.indicate(ev.p, 'snap', ev.id);
        break;
      case 'whistle':
        this.audio.play('whistle', ev.p);
        this.indicate(ev.p, 'whistle', ev.id);
        break;
      case 'manip': {
        const p = this.props.get(ev.prop);
        if (!p) break;
        p.trigger(ev.k, ev.seed, now);
        if (ev.k === 'b') this.indicate(p.center.toArray(), 'big');
        break;
      }
      case 'ray':
        if (ev.id !== this.me) {
          const a = this.avatars.get(ev.id);
          const o = a?.muzzle ? a.muzzle.getWorldPosition(new THREE.Vector3()) : new THREE.Vector3(...ev.o);
          this.effects.ray(o, new THREE.Vector3(...ev.d));
          this.audio.play('ray', ev.o);
        }
        break;
      case 'freeze':
        this.audio.play('freeze', ev.p);
        this.effects.burst([ev.p[0], ev.p[1] + 1, ev.p[2]], '#bfe9ff', 50, 3.5, 0.07, 1.2, 3);
        if (ev.id === this.me) this.hud.feed('You were frozen by the revealer!', 'warn');
        break;
      case 'penalty':
        if (ev.id === this.me) this.hud.feed(`Locked in ${this.map.penalty?.label || 'the penalty box'} for ${ev.until}s`, 'warn');
        break;
      case 'release':
        if (ev.id === this.me) { this.hud.feed('You slipped free. Back to haunting!', 'info'); this.audio.play('pickup', null, { volume: 0.5, rate: 0.7 }); }
        break;
      case 'expose':
        if (ev.id === this.me) {
          this.audio.play('expose', null, { volume: 0.7 });
          this.hud.feed('Exposed! You lingered too close to another ghost.', 'warn');
        } else if (!this.isGhost) {
          this.audio.play('expose', null, { volume: 0.35, rate: 1.3 });
          this.hud.feed('A ghost has been exposed!', 'info');
        }
        break;
      case 'pickup':
        if (ev.id === this.me) { this.audio.play('pickup', null, { volume: 0.7 }); this.hud.feed('You have the relic! Get it to the capture altar.', 'relic'); }
        else { this.audio.play('pickup', this.relicVis.pos.toArray(), { volume: 0.6 }); this.hud.feed(`${name(ev.id)} took the relic`, 'relic'); }
        break;
      case 'relicDrop':
        this.audio.play('drop', ev.p, { volume: 0.7 });
        if (ev.id === this.me) this.hud.feed(ev.reason === 'tired' ? 'Your grip gave out. A teammate must carry it on.' : 'You set the relic down.', 'relic');
        else this.hud.feed(`${name(ev.id)} dropped the relic${ev.reason === 'tired' ? ' (exhausted)' : ''}`, 'relic');
        break;
      case 'relicReset':
        this.audio.play('shatter', null, { volume: 0.6 });
        break;
      case 'channel':
        this.audio.play('channel', ev.p);
        this.channelFx = this.effects.channelRing(ev.p);
        break;
      case 'channelStop':
        if (this.channelFx) { this.effects.cancel(this.channelFx); this.channelFx = null; }
        break;
      case 'capture':
        if (this.channelFx) { this.effects.cancel(this.channelFx); this.channelFx = null; }
        this.audio.play('capture', null, { volume: 0.8 });
        this.effects.beam(ev.p, '#7fffd4');
        break;
      case 'drip':
        this.effects.drip(ev.p);
        break;
      case 'phase':
        break;
      case 'feed':
        this.hud.feed(ev.text, ev.kind);
        break;
      default:
        break;
    }
  }

  // Direction arc around the crosshair; ghosts also learn which teammate made the sound.
  indicate(p, kind, fromId) {
    const cam = this.camera;
    const dx = p[0] - cam.position.x, dz = p[2] - cam.position.z;
    if (Math.hypot(dx, dz) < 0.6) return;
    const world = Math.atan2(dx, -dz);
    const fwd = Math.atan2(-Math.sin(this.player.yaw), Math.cos(this.player.yaw));
    const who = fromId && this.roster.get(fromId);
    this.hud.indicate(world - fwd, kind, who ? { text: `${who.name} · ${Math.round(Math.hypot(dx, dz))}m`, color: who.color } : null);
  }

  onEnd(m) {
    this.phase = PHASE.RESULTS;
    this.input.exitLock();
    this.app.ui.showResults(m, this);
  }

  // ---------------------------------------------------------------- frame
  frame() {
    if (this.disposed) return;
    const dt = Math.min(0.05, this.clock.getDelta());
    const t = this.clock.elapsedTime;
    const y = this.snap?.you;
    const frozen = (y?.fz ?? 0) > 0;
    const blind = !this.isGhost && this.phase === PHASE.BLIND;
    this.player.locked = frozen || blind || this.phase === PHASE.RESULTS;
    const look = this.input.consumeMouse();
    if (frozen) { look[0] *= 0.15; look[1] *= 0.15; }
    this.player.update(dt, this.input, look);
    this.player.applyCamera(this.camera, t);
    this.audio.setListener(this.camera);

    // send state
    this.sendAcc += dt;
    if (this.sendAcc >= 1 / CLIENT_SEND_RATE) {
      this.sendAcc = 0;
      const b = this.player.body.pos;
      this.net.send({ t: 'st', p: [round(b.x), round(b.y), round(b.z)], y: round(this.player.yaw), pi: round(this.player.pitch), tp: this.player.tpSeq });
    }

    // world animation
    this.wind.set(Math.cos(t * 0.05), 0, Math.sin(t * 0.05) * 0.5 + 0.3).normalize();
    for (const p of this.props.values()) p.update(t, dt, this.wind);
    if (this.flickerLights) for (const f of this.flickerLights) f.light.intensity = f.base * (1 - f.k * 0.5 * (0.5 + 0.5 * Math.sin(t * 9 + f.ph) * Math.sin(t * 2.3 + f.ph)));
    const viewerPos = this.camera.position;
    for (const a of this.avatars.values()) a.update(t, dt, viewerPos);
    this.updateRelic(t, dt);
    this.effects.update(dt, t);
    this.updateViewModel(t, dt);
    if (this.isGhost) this.updateTarget();
    this.updateHud(t);

    // post
    const u = this.final.uniforms;
    u.uTime.value = t;
    u.uBlind.value += ((blind ? 1 : 0) - u.uBlind.value) * Math.min(1, dt * 4);
    u.uFrozen.value += ((frozen ? 1 : 0) - u.uFrozen.value) * Math.min(1, dt * 5);
    u.uAlarm.value += (((y?.ex ?? 0) > 0 ? 1 : 0) - u.uAlarm.value) * Math.min(1, dt * 5);
    this.composer.render(dt);
  }

  updateRelic(t, dt) {
    const s = this.snap;
    const rel = this.relic;
    let show = false;
    let carriedByMe = false;
    if (s?.r) {
      const r = s.r;
      carriedByMe = r.h === this.me;
      if (!carriedByMe) {
        const target = new THREE.Vector3(r.p[0], r.p[1], r.p[2]);
        if (r.s === 'carried') {
          const a = this.avatars.get(r.h);
          if (a && a.alpha > 0.02) carriedBy(a, target);
        }
        if (!this.relicVis.has || this.relicVis.pos.distanceTo(target) > 4) this.relicVis.pos.copy(target);
        else this.relicVis.pos.lerp(target, Math.min(1, dt * 10));
        this.relicVis.has = true;
        show = true;
      }
      // altar markers for ghosts
      const fp = this.map.flagPoints;
      const spawn = fp.find((f) => f.id === r.sp);
      const cap = fp.find((f) => f.id === r.cp);
      if (this.altarSpawn && spawn && cap) {
        this.altarSpawn.visible = r.s === 'home';
        this.altarSpawn.position.set(spawn.pos[0], spawn.pos[1] - 1.0 + 0.02, spawn.pos[2]);
        this.altarSpawn.rotation.y = t * 0.3;
        this.altarCapture.visible = true;
        this.altarCapture.position.set(cap.pos[0], cap.pos[1] - 1.0 + 0.03, cap.pos[2]);
        this.altarCapture.rotation.y = -t * 0.5;
        this.altarCapture.scale.setScalar(1 + 0.05 * Math.sin(t * 3) + r.ch * 0.4);
        this.captureBeacon.position.set(cap.pos[0], cap.pos[1] - 1.0, cap.pos[2]);
        this.captureBeacon.material.uniforms.uTime.value = t;
        this.capPos = new THREE.Vector3(cap.pos[0], cap.pos[1] + 0.3, cap.pos[2]);
      }
    } else {
      // hunters only see the relic on a visible carrier
      for (const a of this.avatars.values()) {
        if (a.role === ROLES.GHOST && (a.flags & PF.CARRYING) && a.alpha > 0.05) {
          carriedBy(a, this.relicVis.pos);
          show = true;
        }
      }
    }
    rel.visible = show;
    if (show) {
      rel.position.copy(this.relicVis.pos);
      rel.position.y += Math.sin(t * 2) * 0.05;
      rel.rotation.y = t * 0.8;
    }
    this.relicLight.intensity = show ? 3 + Math.sin(t * 5) * 0.6 : 0;
    if (this.heldRelic) {
      this.heldRelic.visible = carriedByMe;
      if (carriedByMe) {
        this.heldRelic.position.y = -0.36 + Math.sin(t * 2.2) * 0.012;
        this.heldRelic.rotation.y = t * 0.6;
        if (Math.random() < dt * 4) this.effects.wisps(this.camera.localToWorld(new THREE.Vector3(0, -0.2, -0.55)), '#7fffd4', 1);
      }
    }
    // hum: hunters hear a carried relic nearby; ghosts hear the relic itself
    let humPos = null, humVol = 0;
    if (s?.hum) { humPos = s.hum; humVol = 0.9; }
    else if (show && this.isGhost) { humPos = this.relicVis.pos.toArray(); humVol = 0.35; }
    else if (carriedByMe) { humPos = this.camera.position.toArray(); humVol = 0.25; }
    if (this.hum) {
      if (humPos) this.hum.setPos(humPos);
      this.hum.setVolume(humVol);
    }
    if (s?.hum && Math.random() < dt * 0.7) this.indicate(s.hum, 'hum');
  }

  updateViewModel(t, dt) {
    if (!this.viewModel) return;
    const stride = Math.floor(this.player.bob / Math.PI);
    if (stride !== this.lastStride && this.player.moving > 1.5 && this.player.body.onGround) {
      this.audio.play('step', null, { volume: 0.18 * Math.min(1, this.player.moving / 5), rate: 0.9 + Math.random() * 0.2 });
    }
    this.lastStride = stride;
    this.recoil = Math.max(0, (this.recoil || 0) - dt * 4);
    const mv = Math.min(1, this.player.moving / HUNTER.speed);
    const b = this.player.bob;
    this.viewModel.position.set(0.24 + Math.cos(b) * 0.012 * mv, -0.24 + Math.abs(Math.sin(b)) * 0.012 * mv - this.recoil * 0.02, -0.42 + this.recoil * 0.08);
    this.viewModel.rotation.x = 0.02 + this.recoil * 0.25;
    if (this.lens) {
      const now = performance.now() / 1000;
      const ready = (this.snap?.you.rc ?? 0) <= 0 && now - this.localRayAt > HUNTER.rayCooldown;
      this.lens.traverse((o) => { if (o.isMesh && o.material.emissiveIntensity !== undefined) o.material.emissiveIntensity = ready ? 0.9 + Math.sin(t * 4) * 0.25 : 0.15; });
    }
    if (this.flashlight) this.flashlight.intensity = this.phase === PHASE.BLIND ? 0 : 34;
  }

  updateTarget() {
    this.target = null;
    if (!this.canAct()) return;
    const cam = this.camera;
    const fwd = cam.getWorldDirection(new THREE.Vector3());
    const reach = GHOST.manipReach;
    const near = [];
    for (const p of this.props.values()) {
      const d = p.center.distanceTo(cam.position);
      if (d < reach + p.size * 0.5) near.push(p);
    }
    if (!near.length) return;
    const ray = new THREE.Raycaster(cam.position, fwd, 0, reach + 1);
    const meshes = near.flatMap((p) => p.meshes);
    const hits = ray.intersectObjects(meshes, false);
    let best = null;
    const wall = this.world.raycast(cam.position.x, cam.position.y, cam.position.z, fwd.x, fwd.y, fwd.z, reach + 1);
    for (const h of hits) {
      if (h.distance > reach || h.distance > wall + 0.6) break;
      best = this.props.get(h.object.userData.propId);
      if (best) break;
    }
    if (!best) {
      let ba = 0.13;
      for (const p of near) {
        const v = p.center.clone().sub(cam.position);
        const d = v.length();
        if (d > reach) continue;
        const ang = v.normalize().angleTo(fwd);
        if (ang < ba && this.world.segmentClear(cam.position.x, cam.position.y, cam.position.z, p.center.x, p.center.y, p.center.z)) { ba = ang; best = p; }
      }
    }
    if (!best) return;
    const arch = ARCHETYPES[best.type];
    const box = new THREE.Box3().setFromObject(best.root);
    const rect = projectBox(box, cam, innerWidth, innerHeight);
    this.target = { id: best.id, label: best.def.label, subtle: arch.subtle, big: arch.big, rect };
  }

  updateHud(t) {
    const hud = this.hud;
    const s = this.snap;
    hud.tick();
    if (!s) return;
    hud.setTime(s.ph === PHASE.BLIND ? s.tl : s.tl, s.cap);
    const y = s.you;
    const w = innerWidth, h = innerHeight;
    if (!this.isGhost && s.ph === PHASE.BLIND) hud.setBlind(s.bl);
    else hud.setBlind(null);
    if (this.isGhost) {
      hud.ability('snap', 0, 1, this.canAct(true));
      hud.ability('whistle', y.wc, MAX_CD.whistle, this.canAct());
      hud.ability('subtle', 0, 1, this.canAct() && !!this.target);
      hud.ability('big', y.bc, MAX_CD.big, this.canAct() && !!this.target);
      hud.ability('drop', 0, 1, !!y.ca);
      hud.meters_(y.st, this.start.settings.carryLimit, !!y.ca, y.cl);
      hud.setPrompt(this.target, y.bc);
    } else {
      const now = performance.now() / 1000;
      const cd = Math.max(y.rc, HUNTER.rayCooldown - (now - this.localRayAt));
      hud.ability('ray', cd, MAX_CD.ray, s.ph === PHASE.PLAY);
    }
    // banners
    if (y.fz > 0) hud.setBanner('Frozen!', `${Math.ceil(y.fz)}s`, 'frozen');
    else if (y.pn > 0) hud.setBanner(this.map.penalty?.label || 'Penalty box', `Released in ${Math.ceil(y.pn)}s — you can still snap`, '');
    else if (y.ex > 0) hud.setBanner('Exposed!', 'The hunters can see you — scatter!', 'warn');
    else if (this.isGhost && s.ph === PHASE.BLIND) hud.setBanner('Spread out!', `The hunters open their eyes in ${Math.ceil(s.bl)}s`, '');
    else hud.setBanner(null);
    // objective + markers
    const markers = [];
    if (this.isGhost && s.r) {
      const r = s.r;
      const cam = this.camera.position;
      if (r.h !== this.me) {
        const p = this.relicVis.pos.clone().add(new THREE.Vector3(0, 0.5, 0));
        markers.push({ key: 'relic', pos: p, kind: 'relic', icon: '✦', label: r.s === 'carried' ? 'Relic (carried)' : 'Relic', dist: p.distanceTo(cam) });
      }
      if (this.capPos) markers.push({ key: 'cap', pos: this.capPos, kind: 'capture', icon: '⌂', label: 'Capture altar', dist: this.capPos.distanceTo(cam) });
      if (r.h === this.me) hud.objective(`Carry the relic to the capture altar! (${s.cap}/3 delivered)`);
      else if (r.s === 'carried') hud.objective('A teammate carries the relic. Distract the hunters, or get close to take over when they tire.');
      else hud.objective(`Grab the relic and deliver it to the capture altar. (${s.cap}/3 delivered)`);
    }
    hud.setMarkers(markers, this.camera, w, h);
    // name tags
    const tags = [];
    for (const a of this.avatars.values()) {
      if (!a.obj.visible || a.alpha < 0.05) continue;
      if (a.role === ROLES.HUNTER && !this.isGhost) {
        tags.push({ key: a.id, pos: a.pos.clone().add(new THREE.Vector3(0, 2.15, 0)), text: a.name, color: '#ffb36b', alpha: 0.85 });
      } else if (a.role === ROLES.GHOST) {
        tags.push({ key: a.id, pos: a.pos.clone().add(new THREE.Vector3(0, 1.9, 0)), text: a.name, color: a.color, alpha: Math.min(1, a.alpha * 1.8) });
      }
    }
    hud.setTags(tags, this.camera, w, h);
    // vignette by clump meter
    if (this.isGhost) {
      const c = Math.min(1, y.cl);
      hud.setVignette(c > 0.05 ? `inset 0 0 ${80 + c * 120}px rgba(255, 90, 60, ${c * 0.55})` : '');
    }
    if (this.showScores) hud.showScores(true, this.scoreRows());
    else hud.showScores(false);
  }

  scoreRows() {
    const rows = [];
    const me = this.roster.get(this.me);
    rows.push({ ...me, status: 'you' });
    for (const a of this.avatars.values()) {
      const f = a.flags;
      const fresh = this.clock.elapsedTime - a.lastSeen < 0.5;
      let status = '';
      if (fresh && f & PF.FROZEN) status = 'frozen';
      else if (fresh && f & PF.PENALTY) status = 'in the cage';
      else if (fresh && f & PF.EXPOSED) status = 'exposed';
      if (this.isGhost && this.snap?.r?.h === a.id) status = 'carrying the relic';
      rows.push({ name: a.name, role: a.role, color: a.color, status });
    }
    return rows;
  }

  dispose() {
    this.disposed = true;
    for (const u of this.unsub) u();
    this.input?.dispose();
    this.hud?.dispose();
    this.audio.stopAll();
    window.removeEventListener('resize', this._resize);
    for (const a of this.avatars.values()) a.dispose();
    this.scene?.traverse((o) => {
      if (o.isMesh && o.geometry && !o.geometry.userData.shared) o.geometry.dispose?.();
    });
    this.composer?.dispose?.();
  }
}

// where a ghost holds the relic: in front of its arm nubs
function carriedBy(a, out) {
  return out.set(a.pos.x - Math.sin(a.yaw) * 0.42, a.pos.y + 0.78, a.pos.z - Math.cos(a.yaw) * 0.42);
}

function round(v) {
  return Math.round(v * 1000) / 1000;
}

function projectBox(box, cam, w, h) {
  const pts = [];
  for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) {
    const v = new THREE.Vector3(x, y, z).project(cam);
    if (v.z > 1) return null;
    pts.push(v);
  }
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const v of pts) {
    const sx = (v.x * 0.5 + 0.5) * w, sy = (-v.y * 0.5 + 0.5) * h;
    x0 = Math.min(x0, sx); x1 = Math.max(x1, sx); y0 = Math.min(y0, sy); y1 = Math.max(y1, sy);
  }
  x0 = Math.max(4, x0); y0 = Math.max(4, y0); x1 = Math.min(w - 4, x1); y1 = Math.min(h - 4, y1);
  if (x1 - x0 < 4 || y1 - y0 < 4) return null;
  return { x: x0 - 6, y: y0 - 6, w: x1 - x0 + 12, h: y1 - y0 + 12 };
}

function makeBeacon() {
  const hgt = 14;
  const geo = new THREE.CylinderGeometry(0.35, 0.6, hgt, 16, 1, true);
  geo.translate(0, hgt / 2, 0);
  const mat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    uniforms: { uTime: { value: 0 } },
    vertexShader: 'varying float vY; varying vec2 vUv; void main(){ vY = position.y; vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader: `uniform float uTime; varying float vY; varying vec2 vUv;
      void main(){ float f = 1.0 - vY / ${hgt.toFixed(1)}; float s = 0.6 + 0.4 * sin(vUv.x * 40.0 + uTime * 2.0 - vY * 2.0);
        gl_FragColor = vec4(1.0, 0.86, 0.55, f * f * 0.22 * s); }`,
  });
  const m = new THREE.Mesh(geo, mat);
  m.renderOrder = 4;
  m.frustumCulled = false;
  return m;
}

function makeSky(env, cx, cz) {
  const g = new THREE.Group();
  const n = 1500;
  const pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const u = Math.random(), v = Math.random() * 0.9 + 0.1;
    const th = u * Math.PI * 2, ph = Math.acos(1 - v);
    pos[i * 3] = Math.sin(ph) * Math.cos(th) * 300;
    pos[i * 3 + 1] = Math.cos(ph) * 300;
    pos[i * 3 + 2] = Math.sin(ph) * Math.sin(th) * 300;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const stars = new THREE.Points(geo, new THREE.PointsMaterial({ color: 0xdfe8ff, size: 1.2, sizeAttenuation: false, fog: false, transparent: true, opacity: 0.85 }));
  g.add(stars);
  const moonDir = new THREE.Vector3(...(env.moon?.dir || [-0.4, -1, -0.3])).normalize().negate();
  const disc = new THREE.Mesh(new THREE.CircleGeometry(9, 32), new THREE.MeshBasicMaterial({ color: 0xf2f0dc, fog: false }));
  disc.position.copy(moonDir.clone().multiplyScalar(280));
  disc.lookAt(0, 0, 0);
  const halo = new THREE.Mesh(new THREE.CircleGeometry(26, 32), new THREE.MeshBasicMaterial({ color: 0x9fb4ff, transparent: true, opacity: 0.12, fog: false, depthWrite: false }));
  halo.position.copy(moonDir.clone().multiplyScalar(285));
  halo.lookAt(0, 0, 0);
  g.add(disc, halo);
  g.position.set(cx, 0, cz);
  g.renderOrder = -1;
  return g;
}
