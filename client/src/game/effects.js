// Transient visual effects: particles, the revealer cone, ectoplasm drips, capture beams.
import * as THREE from 'three';
import { HUNTER, RELIC } from '../../../shared/constants.js';

const MAX_PARTICLES = 1200;

class Particles {
  constructor(scene) {
    const g = new THREE.BufferGeometry();
    this.pos = new Float32Array(MAX_PARTICLES * 3);
    this.col = new Float32Array(MAX_PARTICLES * 4);
    this.size = new Float32Array(MAX_PARTICLES);
    this.vel = new Float32Array(MAX_PARTICLES * 3);
    this.life = new Float32Array(MAX_PARTICLES);
    this.max = new Float32Array(MAX_PARTICLES);
    this.kind = new Uint8Array(MAX_PARTICLES);
    g.setAttribute('position', new THREE.BufferAttribute(this.pos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('color', new THREE.BufferAttribute(this.col, 4).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('size', new THREE.BufferAttribute(this.size, 1).setUsage(THREE.DynamicDrawUsage));
    const m = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false,
      uniforms: { uScale: { value: 400 } },
      vertexShader: `attribute float size; attribute vec4 color; varying vec4 vC;
        uniform float uScale;
        void main(){ vC = color; vec4 mv = modelViewMatrix * vec4(position,1.0);
          gl_PointSize = size * uScale / max(0.1, -mv.z); gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `varying vec4 vC; void main(){ vec2 d = gl_PointCoord - 0.5; float r = length(d);
          if (r > 0.5) discard; gl_FragColor = vec4(vC.rgb, vC.a * smoothstep(0.5, 0.2, r)); }`,
    });
    this.points = new THREE.Points(g, m);
    this.points.frustumCulled = false;
    this.points.renderOrder = 5;
    scene.add(this.points);
    this.next = 0;
    this.geo = g;
  }

  spawn(p, v, color, size, life, kind = 0) {
    const i = this.next;
    this.next = (this.next + 1) % MAX_PARTICLES;
    this.pos.set([p.x, p.y, p.z], i * 3);
    this.vel.set([v.x, v.y, v.z], i * 3);
    this.col.set([color.r, color.g, color.b, 1], i * 4);
    this.size[i] = size;
    this.life[i] = life;
    this.max[i] = life;
    this.kind[i] = kind;
  }

  update(dt, t) {
    for (let i = 0; i < MAX_PARTICLES; i++) {
      if (this.life[i] <= 0) { this.col[i * 4 + 3] = 0; continue; }
      this.life[i] -= dt;
      const k = this.kind[i];
      const i3 = i * 3;
      if (k === 1) { // leaf: flutter down
        this.vel[i3 + 1] = Math.max(this.vel[i3 + 1] - 3 * dt, -1.1);
        this.vel[i3] += Math.sin(t * 4 + i) * 2 * dt;
        this.vel[i3] *= 0.98; this.vel[i3 + 2] *= 0.98;
      } else if (k === 2) { // dust: slow down, rise a little
        this.vel[i3] *= 0.92; this.vel[i3 + 2] *= 0.92; this.vel[i3 + 1] = this.vel[i3 + 1] * 0.95 + 0.02;
      } else if (k === 3) { // spark: gravity
        this.vel[i3 + 1] -= 6 * dt;
      } else if (k === 4) { // wisp: drift up
        this.vel[i3 + 1] = this.vel[i3 + 1] * 0.97 + 0.03;
      }
      this.pos[i3] += this.vel[i3] * dt;
      this.pos[i3 + 1] += this.vel[i3 + 1] * dt;
      this.pos[i3 + 2] += this.vel[i3 + 2] * dt;
      const a = this.life[i] / this.max[i];
      this.col[i * 4 + 3] = k === 1 ? Math.min(1, a * 3) : a;
    }
    this.geo.attributes.position.needsUpdate = true;
    this.geo.attributes.color.needsUpdate = true;
    this.geo.attributes.size.needsUpdate = true;
  }
}

const rnd = (a, b) => a + Math.random() * (b - a);

export class Effects {
  constructor(scene, engine) {
    this.scene = scene;
    this.engine = engine;
    this.particles = new Particles(scene);
    this.items = [];   // { obj, t0, dur, update(k) }
    this.drips = [];
    const dripGeo = new THREE.CircleGeometry(0.11, 10).rotateX(-Math.PI / 2);
    this.dripMat = new THREE.MeshBasicMaterial({ color: 0x7fffd4, transparent: true, opacity: 0.9, depthWrite: false, blending: THREE.AdditiveBlending });
    this.dripGeo = dripGeo;
    this.coneGeo = new THREE.CylinderGeometry(Math.tan(HUNTER.rayHalfAngle) * HUNTER.rayRange, 0.06, HUNTER.rayRange, 28, 1, true);
    this.coneGeo.translate(0, HUNTER.rayRange / 2, 0);
    this.coneGeo.rotateX(Math.PI / 2); // +Z forward
  }

  add(obj, dur, update) {
    this.scene.add(obj);
    this.items.push({ obj, t0: performance.now() / 1000, dur, update });
  }

  update(dt, t) {
    this.particles.update(dt, t);
    const now = performance.now() / 1000;
    this.items = this.items.filter((it) => {
      const k = (now - it.t0) / it.dur;
      if (k >= 1) {
        this.scene.remove(it.obj);
        it.obj.traverse?.((o) => { if (o.material?.dispose && o.userData.ownMat) o.material.dispose(); });
        return false;
      }
      it.update?.(k, now - it.t0);
      return true;
    });
    for (const d of this.drips) {
      const k = (now - d.t0) / RELIC.dripLife;
      d.mesh.material.opacity = Math.max(0, 0.85 * (1 - k * k));
      d.mesh.scale.setScalar(0.6 + Math.min(1, k * 6) * 0.4 + k * 0.4);
    }
    while (this.drips.length && now - this.drips[0].t0 > RELIC.dripLife) {
      const d = this.drips.shift();
      this.scene.remove(d.mesh);
      d.mesh.material.dispose();
    }
  }

  leaves(center, hex, n = 30) {
    const c = new THREE.Color(hex);
    for (let i = 0; i < n; i++) {
      const p = new THREE.Vector3(center.x + rnd(-1.2, 1.2), center.y + rnd(0, 1.5), center.z + rnd(-1.2, 1.2));
      const cc = c.clone().offsetHSL(rnd(-0.03, 0.03), 0, rnd(-0.12, 0.08));
      this.particles.spawn(p, new THREE.Vector3(rnd(-1, 1), rnd(0, 1.5), rnd(-1, 1)), cc, rnd(0.05, 0.09), rnd(2.5, 4.5), 1);
    }
  }

  dust(center, n = 14) {
    const c = new THREE.Color(0x8a8070);
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2;
      this.particles.spawn(new THREE.Vector3(center.x, Math.max(0.05, center.y - 0.3), center.z), new THREE.Vector3(Math.cos(a) * 1.6, rnd(0, 0.4), Math.sin(a) * 1.6), c, rnd(0.12, 0.22), rnd(0.8, 1.4), 2);
    }
  }

  burst(pos, hex, n = 30, speed = 3, size = 0.07, life = 1.0, kind = 3) {
    const c = new THREE.Color(hex);
    for (let i = 0; i < n; i++) {
      const v = new THREE.Vector3(rnd(-1, 1), rnd(-0.2, 1), rnd(-1, 1)).normalize().multiplyScalar(rnd(0.4, 1) * speed);
      this.particles.spawn(new THREE.Vector3(pos[0] ?? pos.x, pos[1] ?? pos.y, pos[2] ?? pos.z), v, c, size * rnd(0.6, 1.3), life * rnd(0.6, 1.2), kind);
    }
  }

  wisps(pos, hex, n = 3) {
    const c = new THREE.Color(hex);
    for (let i = 0; i < n; i++) {
      this.particles.spawn(new THREE.Vector3(pos.x + rnd(-0.15, 0.15), pos.y + rnd(-0.1, 0.1), pos.z + rnd(-0.15, 0.15)), new THREE.Vector3(rnd(-0.1, 0.1), rnd(0.1, 0.3), rnd(-0.1, 0.1)), c, rnd(0.03, 0.06), rnd(0.8, 1.6), 4);
    }
  }

  ray(origin, dir) {
    const mat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
      uniforms: { uK: { value: 0 }, uColor: { value: new THREE.Color(0xbff6ff) } },
      vertexShader: `varying vec3 vP; varying vec3 vN; varying vec3 vV;
        void main(){ vP = position; vec4 mv = modelViewMatrix * vec4(position,1.0); vN = normalize(normalMatrix*normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix*mv; }`,
      fragmentShader: `uniform float uK; uniform vec3 uColor; varying vec3 vP; varying vec3 vN; varying vec3 vV;
        void main(){ float along = clamp(vP.z / ${HUNTER.rayRange.toFixed(1)}, 0.0, 1.0);
          float rim = pow(1.0 - abs(dot(vN, vV)), 1.5);
          float sweep = smoothstep(uK*1.6 - 0.25, uK*1.6, along) * (1.0 - smoothstep(uK*1.6, uK*1.6+0.08, along));
          float a = (0.10 + rim*0.35) * (1.0 - along*0.7) * (1.0 - uK) + sweep*0.5*(1.0-uK);
          gl_FragColor = vec4(uColor, a); }`,
    });
    const mesh = new THREE.Mesh(this.coneGeo, mat);
    mesh.userData.ownMat = true;
    mesh.position.copy(origin);
    mesh.lookAt(origin.clone().add(dir));
    mesh.renderOrder = 6;
    this.add(mesh, 0.45, (k) => { mat.uniforms.uK.value = k; });
    // a burst of motes along the beam
    for (let i = 0; i < 18; i++) {
      const d = Math.random() * HUNTER.rayRange * 0.9;
      const spread = Math.tan(HUNTER.rayHalfAngle) * d;
      const p = origin.clone().addScaledVector(dir, d).add(new THREE.Vector3(rnd(-1, 1) * spread, rnd(-1, 1) * spread, rnd(-1, 1) * spread));
      this.particles.spawn(p, dir.clone().multiplyScalar(rnd(0.5, 2)), new THREE.Color(0xd8fbff), rnd(0.03, 0.06), rnd(0.3, 0.7), 2);
    }
  }

  drip(p) {
    const mesh = new THREE.Mesh(this.dripGeo, this.dripMat.clone());
    mesh.position.set(p[0], p[1] + 0.015, p[2]);
    mesh.rotation.y = Math.random() * 6;
    mesh.scale.setScalar(0.6);
    mesh.renderOrder = 2;
    this.scene.add(mesh);
    this.drips.push({ mesh, t0: performance.now() / 1000 });
  }

  beam(pos, hex, dur = 3.5, height = 30, radius = 0.8) {
    const geo = new THREE.CylinderGeometry(radius, radius * 1.4, height, 24, 1, true);
    geo.translate(0, height / 2, 0);
    const mat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
      uniforms: { uK: { value: 0 }, uColor: { value: new THREE.Color(hex) }, uH: { value: height } },
      vertexShader: 'varying float vY; void main(){ vY = position.y; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
      fragmentShader: `uniform float uK, uH; uniform vec3 uColor; varying float vY;
        void main(){ float f = 1.0 - vY/uH; float a = f*f*0.6*(1.0 - uK*uK) * smoothstep(0.0, 0.08, uK+0.02);
          gl_FragColor = vec4(uColor, a); }`,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(pos[0], pos[1] - 1.0, pos[2]);
    mesh.userData.ownMat = true;
    this.add(mesh, dur, (k) => { mat.uniforms.uK.value = k; mesh.scale.x = mesh.scale.z = 1 + k * 0.6; });
    this.burst([pos[0], pos[1], pos[2]], hex, 60, 4, 0.08, 1.6, 4);
  }

  // Rotating rune ring used while ghosts channel a capture: visible to everyone.
  channelRing(pos) {
    const geo = new THREE.RingGeometry(0.9, 1.25, 48, 1).rotateX(-Math.PI / 2);
    const mat = new THREE.MeshBasicMaterial({ color: 0x9fffe0, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(pos[0], pos[1] - 0.98, pos[2]);
    mesh.userData.ownMat = true;
    this.add(mesh, RELIC.captureChannel + 0.4, (k, el) => {
      mat.opacity = Math.min(0.85, el * 1.2) * (1 - Math.max(0, (k - 0.85) / 0.15));
      mesh.rotation.y = el * 2;
      mesh.position.y = pos[1] - 0.98 + Math.sin(el * 6) * 0.03;
      if (Math.random() < 0.5) this.wisps({ x: pos[0] + rnd(-1, 1), y: pos[1] - 0.8, z: pos[2] + rnd(-1, 1) }, '#9fffe0', 1);
    });
    return mesh;
  }

  cancel(obj) {
    const it = this.items.find((i) => i.obj === obj);
    if (it) it.t0 = -1e9;
  }
}
