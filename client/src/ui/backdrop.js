// Slow, ambient view of a map behind the menus: a gentle pan from one of the spawns with the
// props idling, so the lobby previews the selected map.
import * as THREE from 'three';
import { PropCtl } from '../game/props.js';
import { loadGLB, loadMapData } from '../game/game.js';

export class MenuBackdrop {
  constructor(renderer) {
    this.renderer = renderer;
    this.camera = new THREE.PerspectiveCamera(62, innerWidth / innerHeight, 0.1, 300);
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color('#0b0a12');
    this.mapId = null;
    this.props = [];
    this.loading = null;
    this.clock = new THREE.Clock();
    this.wind = new THREE.Vector3(1, 0, 0.3).normalize();
    this.engine = { audio: { play() {} }, effects: null };
    this.fade = 0;
  }

  // Resolves true once the map is showing.
  async show(mapId) {
    if (!mapId || mapId === this.mapId || mapId === this.pendingId) return mapId === this.mapId;
    this.pendingId = mapId;
    const token = (this.token = Symbol(mapId));
    let map, gltf;
    try {
      [map, gltf] = await Promise.all([loadMapData(mapId), loadGLB(`/maps/${mapId}.glb`)]);
    } catch {
      if (this.pendingId === mapId) this.pendingId = null;
      return false;
    }
    if (token !== this.token) return false;
    this.mapId = mapId;
    this.pendingId = null;
    const scene = new THREE.Scene();
    const env = map.env || {};
    scene.background = new THREE.Color(env.sky || '#0b0a12');
    const fog = env.fog || { color: env.sky || '#101320', near: 8, far: 50 };
    scene.fog = new THREE.Fog(fog.color, fog.near, fog.far);
    const hemi = env.hemi || { sky: '#7c88b8', ground: '#2a2018', intensity: 0.5 };
    scene.add(new THREE.HemisphereLight(hemi.sky, hemi.ground, (hemi.intensity ?? 0.5) * 1.6));
    if (env.moon) {
      const d = new THREE.Vector3(...(env.moon.dir || [-0.4, -1, -0.3])).normalize();
      const moon = new THREE.DirectionalLight(env.moon.color || '#9fb4ff', (env.moon.intensity ?? 0.6) * 2.2);
      moon.position.copy(d).multiplyScalar(-60);
      scene.add(moon);
    }
    const level = gltf.scene.clone(true);
    scene.add(level);
    this.props = [];
    for (const def of map.props) {
      const root = level.getObjectByName(`P_${def.id}`);
      if (root) this.props.push(new PropCtl(def, root, scene, this.engine));
    }
    const byId = new Map(this.props.map((p) => [p.id, p]));
    const scale = env.lightScale ?? 9;
    for (const l of map.lights) {
      const light = new THREE.PointLight(l.color, l.intensity * scale, l.distance * 1.15, 1.6);
      light.position.set(...l.pos);
      const prop = l.prop && byId.get(l.prop);
      const node = prop && l.part ? (prop.parts[l.part] || prop.root) : prop?.root;
      if (node) {
        node.updateWorldMatrix(true, false);
        node.worldToLocal(light.position);
        node.add(light);
        prop.attachLight(light, light.intensity);
      } else scene.add(light);
    }
    const sp = map.spawns.hunter[0] || map.spawns.ghost[0];
    this.origin = new THREE.Vector3(sp[0], sp[1] + 1.65, sp[2]);
    this.yaw0 = sp[3] || 0;
    this.scene = scene;
    this.fade = 0;
    this.renderer.toneMappingExposure = env.exposure ?? 1;
    return true;
  }

  // Dev helper: render the current map from a pose and return a 640x360 JPEG data URL.
  capture(pos, yaw, pitch = -0.08) {
    const r = this.renderer;
    const size = r.getSize(new THREE.Vector2());
    const ratio = r.getPixelRatio();
    r.setPixelRatio(1);
    r.setSize(1280, 720, false);
    const cam = this.camera;
    const saved = [cam.position.clone(), cam.rotation.clone(), cam.aspect];
    cam.aspect = 16 / 9;
    cam.updateProjectionMatrix();
    cam.position.set(...pos);
    cam.rotation.set(pitch, yaw, 0, 'YXZ');
    r.render(this.scene, cam);
    const c = document.createElement('canvas');
    c.width = 640;
    c.height = 360;
    c.getContext('2d').drawImage(r.domElement, 0, 0, 640, 360);
    const url = c.toDataURL('image/jpeg', 0.86);
    cam.position.copy(saved[0]);
    cam.rotation.copy(saved[1]);
    cam.aspect = saved[2];
    cam.updateProjectionMatrix();
    r.setPixelRatio(ratio);
    r.setSize(size.x, size.y, false);
    return url;
  }

  render() {
    const dt = Math.min(0.05, this.clock.getDelta());
    const t = this.clock.elapsedTime;
    this.fade = Math.min(1, this.fade + dt * 0.6);
    if (this.origin) {
      const yaw = this.yaw0 + Math.sin(t * 0.05) * 1.1;
      this.camera.position.copy(this.origin);
      this.camera.position.y += Math.sin(t * 0.3) * 0.05;
      this.camera.rotation.set(-0.06 + Math.sin(t * 0.07) * 0.04, yaw, 0, 'YXZ');
    }
    for (const p of this.props) p.update(t, dt, this.wind);
    const w = innerWidth, h = innerHeight;
    if (this.camera.aspect !== w / h) {
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
    }
    this.renderer.render(this.scene, this.camera);
  }
}
