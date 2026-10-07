// Local first-person controller. Movement is simulated here against the same collision boxes
// the server uses; the server only sanity-checks it.
import * as THREE from 'three';
import { GHOST, HUNTER, PLAYER, ROLES } from '../../../shared/constants.js';

export class LocalPlayer {
  constructor(role, world, pos, yaw) {
    this.role = role;
    this.world = world;
    this.body = { pos: { x: pos[0], y: pos[1], z: pos[2] }, vel: { x: 0, y: 0, z: 0 }, onGround: true };
    this.yaw = yaw;
    this.pitch = 0;
    this.eyeY = pos[1];
    this.bob = 0;
    this.moving = 0;
    this.locked = false;   // frozen / blind
    this.carrying = false;
    this.tpSeq = 1;
  }

  get eyeHeight() {
    return this.role === ROLES.GHOST ? 1.35 : PLAYER.eye;
  }

  teleport(p, yaw, seq) {
    this.body.pos.x = p[0]; this.body.pos.y = p[1]; this.body.pos.z = p[2];
    this.body.vel.x = this.body.vel.y = this.body.vel.z = 0;
    this.eyeY = p[1];
    if (yaw !== undefined) this.yaw = yaw;
    if (seq !== undefined) this.tpSeq = seq;
  }

  update(dt, input, look) {
    const [mx, my] = look;
    this.yaw -= mx;
    this.pitch = THREE.MathUtils.clamp(this.pitch - my, -1.5, 1.5);
    const ghost = this.role === ROLES.GHOST;
    const speed = ghost ? (this.carrying ? GHOST.carrySpeed : GHOST.speed) : HUNTER.speed;
    let fx = 0, fz = 0;
    if (!this.locked) {
      if (input.down('KeyW') || input.down('ArrowUp')) fz -= 1;
      if (input.down('KeyS') || input.down('ArrowDown')) fz += 1;
      if (input.down('KeyA') || input.down('ArrowLeft')) fx -= 1;
      if (input.down('KeyD') || input.down('ArrowRight')) fx += 1;
    }
    const len = Math.hypot(fx, fz);
    if (len > 0) { fx /= len; fz /= len; }
    const walk = input.down('ShiftLeft') || input.down('ShiftRight') ? 0.5 : 1;
    const sin = Math.sin(this.yaw), cos = Math.cos(this.yaw);
    const tx = (fx * cos + fz * sin) * speed * walk;
    const tz = (-fx * sin + fz * cos) * speed * walk;
    const b = this.body;
    const accel = b.onGround ? 14 : (ghost ? 5 : 3);
    b.vel.x += (tx - b.vel.x) * Math.min(1, accel * dt);
    b.vel.z += (tz - b.vel.z) * Math.min(1, accel * dt);
    if (this.locked) { b.vel.x = 0; b.vel.z = 0; }
    const grav = ghost ? GHOST.gravity : PLAYER.gravity;
    b.vel.y -= grav * dt;
    if (ghost && b.vel.y < -4.5) b.vel.y = -4.5; // ghosts drift down
    if (!this.locked && b.onGround && input.down('Space')) b.vel.y = ghost ? GHOST.jump : PLAYER.jump;
    this.world.move(b, dt, PLAYER.radius, PLAYER.height, PLAYER.stepHeight);
    // smooth eye over step-ups
    const target = b.pos.y;
    this.eyeY = target > this.eyeY ? Math.min(target, this.eyeY + dt * 4) : target;
    if (Math.abs(target - this.eyeY) > 0.6) this.eyeY = target;
    const hs = Math.hypot(b.vel.x, b.vel.z);
    this.moving = hs;
    if (b.onGround) this.bob += hs * dt * 1.9;
  }

  applyCamera(cam, t) {
    const ghost = this.role === ROLES.GHOST;
    const bobAmt = ghost ? 0 : Math.min(1, this.moving / HUNTER.speed) * 0.045;
    const float = ghost ? Math.sin(t * 1.6) * 0.035 : 0;
    cam.position.set(this.body.pos.x, this.eyeY + this.eyeHeight + Math.abs(Math.sin(this.bob)) * bobAmt + float, this.body.pos.z);
    cam.rotation.set(this.pitch, this.yaw, ghost ? Math.sin(t * 0.9) * 0.012 : Math.sin(this.bob) * bobAmt * 0.12, 'YXZ');
  }

  forward(out = new THREE.Vector3()) {
    return out.set(-Math.sin(this.yaw) * Math.cos(this.pitch), Math.sin(this.pitch), -Math.cos(this.yaw) * Math.cos(this.pitch));
  }
}
