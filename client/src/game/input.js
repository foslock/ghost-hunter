// Keyboard/mouse with pointer lock. Falls back to drag-to-look when pointer lock is unavailable.
export class Input {
  constructor(canvas) {
    this.canvas = canvas;
    this.keys = new Set();
    this.dx = 0;
    this.dy = 0;
    this.locked = document.pointerLockElement === canvas;
    this.dragging = false;
    this.sensitivity = Number(localStorage.getItem('gh.sens') || 1);
    this.invertY = localStorage.getItem('gh.invert') === '1';
    this.actions = new Map();
    this.enabled = true;
    this._down = (e) => this.onKey(e, true);
    this._up = (e) => this.onKey(e, false);
    this._move = (e) => {
      if (!this.enabled) return;
      if (this.locked || this.dragging) {
        this.dx += e.movementX;
        this.dy += e.movementY;
      }
    };
    this._mousedown = (e) => {
      if (!this.enabled) return;
      if (!this.locked) {
        if (e.target === canvas) {
          this.requestLock();
          if (e.button === 2 || e.shiftKey) this.dragging = true;
        }
        return;
      }
      this.fire(`mouse${e.button}`, e);
    };
    this._mouseup = () => { this.dragging = false; };
    this._lockchange = () => {
      this.locked = document.pointerLockElement === canvas;
      this.fire(this.locked ? 'locked' : 'unlocked');
    };
    this._blur = () => this.keys.clear();
    window.addEventListener('keydown', this._down);
    window.addEventListener('keyup', this._up);
    window.addEventListener('mousemove', this._move);
    window.addEventListener('mousedown', this._mousedown);
    window.addEventListener('mouseup', this._mouseup);
    window.addEventListener('blur', this._blur);
    document.addEventListener('pointerlockchange', this._lockchange);
    canvas.addEventListener('contextmenu', (e) => e.preventDefault());
  }

  requestLock() {
    const fallback = () => {
      try {
        const p2 = this.canvas.requestPointerLock?.();
        if (p2?.catch) p2.catch(() => { this.dragging = true; });
      } catch { this.dragging = true; }
    };
    try {
      const p = this.canvas.requestPointerLock({ unadjustedMovement: true });
      if (p?.catch) p.catch(fallback);
    } catch {
      fallback();
    }
  }

  exitLock() {
    if (document.pointerLockElement) document.exitPointerLock();
  }

  on(action, fn) {
    this.actions.set(action, fn);
  }

  fire(action, e) {
    const fn = this.actions.get(action);
    if (fn) fn(e);
  }

  onKey(e, down) {
    if (e.target instanceof HTMLInputElement) return;
    const k = e.code;
    if (down) {
      if (!this.keys.has(k)) this.fire(`key:${k}`, e);
      this.keys.add(k);
      if (['Space', 'Tab', 'KeyQ', 'KeyE', 'KeyF', 'KeyG'].includes(k) && this.enabled) e.preventDefault();
    } else {
      this.keys.delete(k);
      this.fire(`keyup:${k}`, e);
    }
  }

  down(code) {
    return this.enabled && this.keys.has(code);
  }

  consumeMouse() {
    const s = 0.0022 * this.sensitivity;
    const out = [this.dx * s, this.dy * s * (this.invertY ? -1 : 1)];
    this.dx = 0;
    this.dy = 0;
    return out;
  }

  dispose({ keepLock = false } = {}) {
    window.removeEventListener('keydown', this._down);
    window.removeEventListener('keyup', this._up);
    window.removeEventListener('mousemove', this._move);
    window.removeEventListener('mousedown', this._mousedown);
    window.removeEventListener('mouseup', this._mouseup);
    window.removeEventListener('blur', this._blur);
    document.removeEventListener('pointerlockchange', this._lockchange);
    if (!keepLock) this.exitLock();
  }
}
