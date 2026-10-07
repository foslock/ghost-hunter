// DOM heads-up display. Everything is positioned in CSS pixels over the canvas.
import { GHOST, HUNTER, ROLES, ROUND } from '../../../shared/constants.js';

const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
};

const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export class Hud {
  constructor(root, role, mapName, penaltyLabel) {
    this.root = root;
    this.role = role;
    root.innerHTML = '';
    root.classList.remove('hidden');
    const ghost = role === ROLES.GHOST;
    this.vignette = el('div', 'vignette');
    this.top = el('div', 'top', `<div class="timer">--:--</div><div class="pips">${'<div class="pip"></div>'.repeat(ROUND.capturesToWin)}</div>`);
    this.timer = this.top.querySelector('.timer');
    this.pips = [...this.top.querySelectorAll('.pip')];
    this.roleBox = el('div', `role ${role}`, `<div class="badge">${ghost ? 'Ghost' : 'Hunter'}</div><div class="obj"></div>`);
    this.obj = this.roleBox.querySelector('.obj');
    this.feedBox = el('div', 'feed');
    this.cross = el('div', `crosshair ${ghost ? 'ghostx' : ''}`);
    this.ringSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    this.ringSvg.setAttribute('viewBox', '-110 -110 220 220');
    this.ringSvg.setAttribute('class', 'ring');
    this.prompt = el('div', 'prompt hidden');
    this.bracket = el('div', 'bracket hidden');
    this.markers = el('div', 'markers');
    this.tags = el('div', 'tags');
    this.bar = el('div', 'bar');
    this.meters = el('div', 'meters');
    this.banner = el('div', 'banner hidden');
    this.blind = el('div', 'blind hidden', '<div>The ghosts are hiding…</div><div class="n">10</div><div class="muted" style="font-size:18px;font-family:var(--body)">Listen for snaps and whistles. Watch things move.</div>');
    this.blindN = this.blind.querySelector('.n');
    this.score = el('div', 'scoreboard panel hidden');
    this.help = el('div', 'help', ghost
      ? '<kbd>WASD</kbd> move · <kbd>Space</kbd> float · <kbd>LMB</kbd> snap · <kbd>F</kbd> whistle · <kbd>E</kbd> subtle · <kbd>Q</kbd> big · <kbd>G</kbd> drop relic · <kbd>Tab</kbd> scores'
      : '<kbd>WASD</kbd> move · <kbd>Space</kbd> jump · <kbd>LMB</kbd> revealer · <kbd>Shift</kbd> walk · <kbd>Tab</kbd> scores');
    this.penaltyLabel = penaltyLabel || 'the penalty box';
    root.append(this.vignette, this.markers, this.tags, this.top, this.roleBox, this.feedBox, this.ringSvg, this.cross, this.bracket, this.prompt, this.meters, this.bar, this.banner, this.help, this.score, this.blind);

    this.abilities = {};
    const abil = ghost
      ? [['snap', 'LMB', 'Snap'], ['whistle', 'F', 'Whistle'], ['subtle', 'E', 'Subtle'], ['big', 'Q', 'Big'], ['drop', 'G', 'Drop']]
      : [['ray', 'LMB', 'Revealer']];
    for (const [k, key, label] of abil) {
      const b = el('div', 'ab ready', `<kbd>${key}</kbd><span>${label}</span><div class="cdfill" style="height:0"></div><div class="cdtext"></div>`);
      this.abilities[k] = { el: b, fill: b.querySelector('.cdfill'), text: b.querySelector('.cdtext') };
      this.bar.append(b);
    }
    if (ghost) {
      this.stamina = el('div', '', '<div class="meter-label"><span>Relic grip</span><span class="v"></span></div><div class="meter stamina"><i></i></div>');
      this.clump = el('div', '', '<div class="meter-label"><span>Too close to another ghost!</span><span></span></div><div class="meter clump"><i></i></div>');
      this.meters.append(this.clump, this.stamina);
    }
    this.indicators = [];
    this.markerEls = new Map();
    this.tagEls = new Map();
    this.objective(ghost ? 'Find the relic (glowing marker) and carry it to the capture altar.' : 'Listen and watch. Freeze ghosts with the revealer before they deliver the relic three times.');
  }

  objective(text) {
    if (this.obj.textContent !== text) this.obj.textContent = text;
  }

  setTime(sec, captures) {
    const s = fmt(Math.max(0, sec));
    if (this.timer.textContent !== s) this.timer.textContent = s;
    this.timer.classList.toggle('low', sec <= 30);
    this.pips.forEach((p, i) => p.classList.toggle('on', i < captures));
  }

  feed(text, kind = 'info') {
    const d = el('div', kind);
    d.textContent = text;
    this.feedBox.prepend(d);
    while (this.feedBox.children.length > 6) this.feedBox.lastChild.remove();
    setTimeout(() => d.remove(), 7000);
  }

  setBanner(text, sub = '', kind = '') {
    if (!text) { this.banner.classList.add('hidden'); return; }
    this.banner.className = `banner ${kind}`;
    const html = `${esc(text)}${sub ? `<small>${esc(sub)}</small>` : ''}`;
    if (this.banner.innerHTML !== html) this.banner.innerHTML = html;
  }

  setBlind(seconds) {
    if (seconds === null) { this.blind.classList.add('hidden'); return; }
    this.blind.classList.remove('hidden');
    this.blindN.textContent = Math.ceil(seconds);
  }

  ability(k, cd, max, enabled = true) {
    const a = this.abilities[k];
    if (!a) return;
    const ready = cd <= 0.05 && enabled;
    a.el.classList.toggle('ready', ready);
    a.el.style.opacity = enabled ? 1 : 0.4;
    a.fill.style.height = `${Math.min(1, Math.max(0, cd / max)) * 100}%`;
    a.text.textContent = cd > 0.05 ? Math.ceil(cd) : '';
  }

  meters_(stamina, max, carrying, clump) {
    if (!this.stamina) return;
    const showSt = carrying || stamina < max - 0.05;
    this.stamina.style.visibility = showSt ? 'visible' : 'hidden';
    this.stamina.querySelector('i').style.width = `${(stamina / max) * 100}%`;
    this.stamina.querySelector('.v').textContent = carrying ? `${stamina.toFixed(0)}s` : 'recovering';
    this.clump.style.visibility = clump > 0.02 ? 'visible' : 'hidden';
    this.clump.querySelector('i').style.width = `${Math.min(1, clump) * 100}%`;
  }

  setPrompt(target, bigCd) {
    if (!target) {
      this.prompt.classList.add('hidden');
      this.bracket.classList.add('hidden');
      return;
    }
    this.prompt.classList.remove('hidden');
    const html = `<b>${esc(target.label)}</b><div class="opts"><span><kbd>E</kbd> ${esc(target.subtle)}</span><span class="${bigCd > 0 ? 'cd' : ''}"><kbd>Q</kbd> ${esc(target.big)}${bigCd > 0 ? ` (${Math.ceil(bigCd)}s)` : ''}</span></div>`;
    if (this.prompt.innerHTML !== html) this.prompt.innerHTML = html;
    if (target.rect) {
      const r = target.rect;
      this.bracket.classList.remove('hidden');
      Object.assign(this.bracket.style, { left: `${r.x}px`, top: `${r.y}px`, width: `${r.w}px`, height: `${r.h}px` });
    } else this.bracket.classList.add('hidden');
  }

  // A directional arc around the crosshair pointing to where a sound came from.
  indicate(angle, kind) {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const span = kind === 'whistle' ? 0.5 : kind === 'big' ? 0.35 : 0.28;
    const r = kind === 'whistle' ? 98 : 84;
    const a0 = angle - span, a1 = angle + span;
    const p = (a) => `${(Math.sin(a) * r).toFixed(1)} ${(-Math.cos(a) * r).toFixed(1)}`;
    path.setAttribute('d', `M ${p(a0)} A ${r} ${r} 0 0 1 ${p(a1)}`);
    const color = kind === 'whistle' ? '#9fe8ff' : kind === 'big' ? '#ffb36b' : kind === 'hum' ? '#7fffd4' : '#ffffff';
    path.setAttribute('stroke', color);
    path.setAttribute('stroke-width', kind === 'whistle' ? '6' : '4');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('fill', 'none');
    path.style.filter = `drop-shadow(0 0 6px ${color})`;
    this.ringSvg.append(path);
    const born = performance.now();
    const life = kind === 'whistle' ? 2600 : 1700;
    this.indicators.push({ path, born, life });
  }

  tick() {
    const now = performance.now();
    this.indicators = this.indicators.filter((i) => {
      const k = (now - i.born) / i.life;
      if (k >= 1) { i.path.remove(); return false; }
      i.path.setAttribute('opacity', (1 - k * k).toFixed(3));
      return true;
    });
  }

  // markers: [{ key, pos: Vector3, kind, label }]
  setMarkers(list, camera, w, h) {
    const seen = new Set();
    for (const m of list) {
      seen.add(m.key);
      let e = this.markerEls.get(m.key);
      if (!e) {
        e = el('div', `marker ${m.kind}`, `<div class="ic">${m.icon || '◆'}</div><span></span>`);
        this.markers.append(e);
        this.markerEls.set(m.key, e);
      }
      // on-screen: project; off-screen or behind: pin to an ellipse in the target's direction
      const v = m.pos.clone().project(camera);
      const cv = m.pos.clone().applyMatrix4(camera.matrixWorldInverse);
      let x = (v.x * 0.5 + 0.5) * w, y = (-v.y * 0.5 + 0.5) * h;
      const pad = 46;
      const off = cv.z > 0 || x < pad || x > w - pad || y < pad || y > h - pad;
      if (off) {
        const a = Math.atan2(cv.x, cv.y);
        x = w / 2 + Math.sin(a) * (w / 2 - pad);
        y = h / 2 - Math.cos(a) * (h / 2 - pad);
      }
      e.style.left = `${x}px`;
      e.style.top = `${y}px`;
      e.style.opacity = off ? 0.7 : 1;
      const label = `${m.label} · ${Math.round(m.dist)}m`;
      const span = e.querySelector('span');
      if (span.textContent !== label) span.textContent = label;
    }
    for (const [k, e] of this.markerEls) if (!seen.has(k)) { e.remove(); this.markerEls.delete(k); }
  }

  // name tags above visible players: [{ key, pos, text, color, alpha }]
  setTags(list, camera, w, h) {
    const seen = new Set();
    for (const t of list) {
      const v = t.pos.clone().project(camera);
      if (v.z > 1 || Math.abs(v.x) > 1.1 || Math.abs(v.y) > 1.1) continue;
      seen.add(t.key);
      let e = this.tagEls.get(t.key);
      if (!e) {
        e = el('div', 'tag3d');
        this.tags.append(e);
        this.tagEls.set(t.key, e);
      }
      if (e.textContent !== t.text) e.textContent = t.text;
      e.style.color = t.color;
      e.style.opacity = t.alpha;
      e.style.left = `${(v.x * 0.5 + 0.5) * w}px`;
      e.style.top = `${(-v.y * 0.5 + 0.5) * h}px`;
    }
    for (const [k, e] of this.tagEls) if (!seen.has(k)) { e.remove(); this.tagEls.delete(k); }
  }

  setVignette(css) {
    if (this.vignette.style.boxShadow !== css) this.vignette.style.boxShadow = css;
  }

  showScores(show, rows) {
    this.score.classList.toggle('hidden', !show);
    if (!show) return;
    const tr = (r) => `<tr><td style="color:${r.color}">${esc(r.name)}</td><td>${r.role === ROLES.HUNTER ? 'Hunter' : 'Ghost'}</td><td>${esc(r.status || '')}</td></tr>`;
    this.score.innerHTML = `<table><tr><th>Player</th><th>Role</th><th></th></tr>${rows.map(tr).join('')}</table>`;
  }

  dispose() {
    this.root.innerHTML = '';
    this.root.classList.add('hidden');
  }
}

export const MAX_CD = { whistle: GHOST.whistleCooldown, big: GHOST.bigCooldown, ray: HUNTER.rayCooldown };
export { fmt, esc };
