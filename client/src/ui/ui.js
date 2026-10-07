// Menus: home, lobby, loading, waiting, pause and results screens.
import { GHOST, HUNTER, LOBBY_LIMITS, ROLES } from '../../../shared/constants.js';

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmtTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

export class UI {
  constructor(app) {
    this.app = app;
    this.root = document.getElementById('screens');
    this.toasts = document.getElementById('toasts');
    this.room = null;
    this.chat = [];
    this.screen = null;
  }

  toast(text, kind = '') {
    const t = document.createElement('div');
    t.className = `toast ${kind}`;
    t.textContent = text;
    this.toasts.append(t);
    setTimeout(() => t.remove(), 4200);
  }

  clear() {
    this.root.innerHTML = '';
    this.screen = null;
  }

  // ---------------------------------------------------------------- home
  showHome() {
    this.screen = 'home';
    const name = localStorage.getItem('gh.name') || '';
    const code = new URLSearchParams(location.search).get('room') || '';
    this.root.innerHTML = `
      <div class="screen backdrop home">
        <div class="title"><h1>Ghost Hunter</h1><div class="sub">Invisible ghosts smuggle a relic. Hunters listen for the snap.</div></div>
        <div class="panel home-card">
          <label class="field">Your name<input id="name" type="text" maxlength="16" placeholder="e.g. Mortimer" value="${esc(name)}" autocomplete="off" /></label>
          <button class="btn primary" id="create">Create a room</button>
          <div class="divider">or join friends</div>
          <div class="join"><input id="code" type="text" maxlength="4" placeholder="CODE" value="${esc(code)}" autocomplete="off" /><button class="btn" id="join">Join</button></div>
        </div>
        <div class="panel howto">
          <div class="ghost"><h3>Ghosts</h3><ul>
            <li>Invisible to hunters — and to each other unless within ${GHOST.seeRadius} m.</li>
            <li>Carry the relic to the capture altar three times before time runs out. Your grip tires; pass it on.</li>
            <li><kbd>LMB</kbd> snap (heard ${GHOST.snapRadius} m), <kbd>F</kbd> whistle (loud, cooldown).</li>
            <li><kbd>E</kbd> subtle haunt (natural-looking), <kbd>Q</kbd> big haunt (loud, cooldown).</li>
            <li>Linger together too long and you're exposed.</li></ul></div>
          <div class="hunter"><h3>Hunters</h3><ul>
            <li>You can't see ghosts. Listen for snaps, whistles and the relic's hum.</li>
            <li>Watch the room: clocks running backwards, curtains breathing, doors easing open.</li>
            <li><kbd>LMB</kbd> fires the revealer cone (${HUNTER.rayRange} m). It freezes ghosts and resets a carried relic.</li>
            <li>The carried relic drips glowing ectoplasm. Follow the trail.</li></ul></div>
        </div>
      </div>`;
    const nameEl = this.root.querySelector('#name');
    const codeEl = this.root.querySelector('#code');
    const getName = () => {
      const n = nameEl.value.trim() || `Guest${Math.floor(Math.random() * 900 + 100)}`;
      localStorage.setItem('gh.name', n);
      return n;
    };
    this.root.querySelector('#create').onclick = () => { this.app.audio.resume(); this.app.net.send({ t: 'create', name: getName() }); };
    const join = () => {
      const c = codeEl.value.trim().toUpperCase();
      if (c.length !== 4) return this.toast('Room codes are four letters.', 'error');
      this.app.audio.resume();
      this.app.net.send({ t: 'join', code: c, name: getName() });
    };
    this.root.querySelector('#join').onclick = join;
    codeEl.onkeydown = (e) => { if (e.key === 'Enter') join(); };
    nameEl.onkeydown = (e) => { if (e.key === 'Enter') (codeEl.value.trim().length === 4 ? join() : this.root.querySelector('#create').click()); };
    (name ? codeEl : nameEl).focus();
  }

  // ---------------------------------------------------------------- lobby
  showLobby(room) {
    this.room = room;
    const me = this.app.net.id;
    const isHost = room.host === me;
    if (this.screen !== 'lobby') {
      this.screen = 'lobby';
      this.root.innerHTML = `
        <div class="screen backdrop lobby">
          <div class="lobby-grid">
            <div class="lobby-col">
              <div class="panel">
                <div class="room-head">
                  <div><div class="muted">Room code</div><div class="room-code"></div></div>
                  <div style="display:flex;gap:8px"><button class="btn small" id="copy">Copy invite link</button><button class="btn small" id="leave">Leave</button></div>
                </div>
                <div class="last-round muted" id="last"></div>
              </div>
              <div class="panel"><h2>Map</h2><div class="maps" id="maps"></div></div>
              <div class="panel"><h2>Rules</h2><div class="settings" id="settings"></div></div>
            </div>
            <div class="lobby-col">
              <div class="panel"><h2 style="margin-bottom:10px">Teams</h2><div class="teams" id="teams"></div>
                <div class="lobby-actions" style="margin-top:14px" id="hostbar"></div></div>
              <div class="panel chat"><h2>Chat</h2><div class="chat-log" id="chatlog"></div>
                <input type="text" id="chatin" maxlength="160" placeholder="Say something before the lights go out…" /></div>
              <div class="lobby-actions"><div class="grow muted" id="startnote"></div><button class="btn primary" id="start">Start round</button></div>
            </div>
          </div>
        </div>`;
      this.root.querySelector('#copy').onclick = () => {
        const url = `${location.origin}${location.pathname}?room=${this.room.code}`;
        navigator.clipboard?.writeText(url).then(() => this.toast('Invite link copied.'), () => this.toast(url));
      };
      this.root.querySelector('#leave').onclick = () => { this.app.net.send({ t: 'leave' }); this.room = null; history.replaceState(null, '', location.pathname); this.showHome(); };
      this.root.querySelector('#start').onclick = () => this.app.net.send({ t: 'start' });
      const chatin = this.root.querySelector('#chatin');
      chatin.onkeydown = (e) => {
        if (e.key === 'Enter' && chatin.value.trim()) { this.app.net.send({ t: 'chat', text: chatin.value }); chatin.value = ''; }
      };
      this.renderChat();
      if (!new URLSearchParams(location.search).get('test')) history.replaceState(null, '', `?room=${room.code}`);
    }
    const $ = (s) => this.root.querySelector(s);
    $('.room-code').textContent = room.code;
    $('#last').innerHTML = room.lastRound ? `Last round: <b style="color:var(--${room.lastRound.winner})">${room.lastRound.winner === ROLES.GHOST ? 'Ghosts' : 'Hunters'}</b> won` : 'Share the code. Add bots to fill out the teams.';

    // maps
    const s = room.settings;
    $('#maps').innerHTML = room.maps.map((m) => `
      <button class="map-card ${m.id === s.map ? 'sel' : ''}" data-map="${esc(m.id)}" ${isHost ? '' : 'disabled'}>
        <img src="/maps/${esc(m.id)}.jpg" alt="" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'ph'}))" />
        <div class="meta"><b>${esc(m.name)}</b><span>${esc(m.blurb)}</span></div>
      </button>`).join('');
    if (isHost) for (const b of this.root.querySelectorAll('.map-card')) b.onclick = () => this.app.net.send({ t: 'settings', map: b.dataset.map });

    // settings
    const slider = (key, label, min, max, step, fmt) => `
      <label class="field"><div class="row"><span>${label}</span><b id="v_${key}">${fmt(s[key])}</b></div>
      <input type="range" data-k="${key}" min="${min}" max="${max}" step="${step}" value="${s[key]}" ${isHost ? '' : 'disabled'} /></label>`;
    const settingsEl = $('#settings');
    if (!settingsEl.contains(document.activeElement)) {
      settingsEl.innerHTML = [
        slider('roundTime', 'Round length', LOBBY_LIMITS.roundTime[0], LOBBY_LIMITS.roundTime[1], 30, fmtTime),
        slider('penaltyTime', 'Penalty box time', LOBBY_LIMITS.penaltyTime[0], LOBBY_LIMITS.penaltyTime[1], 5, (v) => `${v}s`),
        slider('carryLimit', 'Relic grip (carry time)', LOBBY_LIMITS.carryLimit[0], LOBBY_LIMITS.carryLimit[1], 1, (v) => `${v}s`),
        `<label class="field"><div class="row"><span>Bot skill</span></div>
          <select id="botskill" ${isHost ? '' : 'disabled'} class="btn small">${['easy', 'normal', 'hard'].map((k) => `<option value="${k}" ${s.botSkill === k ? 'selected' : ''}>${k}</option>`).join('')}</select></label>`,
      ].join('');
      for (const inp of settingsEl.querySelectorAll('input[type=range]')) {
        const fmt = inp.dataset.k === 'roundTime' ? fmtTime : (v) => `${v}s`;
        inp.oninput = () => { settingsEl.querySelector(`#v_${inp.dataset.k}`).textContent = fmt(+inp.value); };
        inp.onchange = () => { this.app.net.send({ t: 'settings', [inp.dataset.k]: +inp.value }); inp.blur(); };
      }
      const bs = settingsEl.querySelector('#botskill');
      bs.onchange = () => this.app.net.send({ t: 'settings', botSkill: bs.value });
    }

    // teams
    const team = (role) => {
      const list = room.players.filter((p) => p.role === role);
      const other = role === ROLES.HUNTER ? ROLES.GHOST : ROLES.HUNTER;
      const rows = list.map((p) => {
        const mine = p.id === me;
        const canMove = isHost || mine;
        return `<div class="player-row ${mine ? 'me' : ''}">
          <span class="dot" style="background:${p.color}"></span>
          <span class="name">${esc(p.name)}</span>
          ${p.id === room.host ? '<span class="tag host">host</span>' : ''}${p.bot ? '<span class="tag">bot</span>' : ''}
          <span class="acts">
            ${canMove ? `<button class="btn small" data-team="${p.id}" data-role="${other}" title="Switch team">⇄</button>` : ''}
            ${isHost && !mine ? `<button class="btn small" data-kick="${p.id}" title="Remove">✕</button>` : ''}
          </span></div>`;
      }).join('');
      return `<div class="team ${role}s"><h3>${role === ROLES.HUNTER ? 'Hunters' : 'Ghosts'} <span class="count">${list.length}</span></h3>${rows || '<div class="muted">Nobody yet.</div>'}
        ${isHost ? `<button class="btn small add" data-bot="${role}">+ Add ${role} bot</button>` : ''}</div>`;
    };
    $('#teams').innerHTML = team(ROLES.HUNTER) + team(ROLES.GHOST);
    for (const b of this.root.querySelectorAll('[data-team]')) b.onclick = () => this.app.net.send({ t: 'team', id: b.dataset.team, role: b.dataset.role });
    for (const b of this.root.querySelectorAll('[data-kick]')) b.onclick = () => this.app.net.send({ t: 'kick', id: b.dataset.kick });
    for (const b of this.root.querySelectorAll('[data-bot]')) b.onclick = () => this.app.net.send({ t: 'addBot', role: b.dataset.bot });
    const counts = { hunter: 0, ghost: 0 };
    for (const p of room.players) counts[p.role]++;
    $('#hostbar').innerHTML = isHost
      ? `<span class="muted">Random teams with</span>
         <button class="btn small" id="hm">−</button><b id="hn">${Math.max(1, counts.hunter)}</b><button class="btn small" id="hp">+</button>
         <span class="muted">hunter(s)</span><button class="btn small" id="shuffle">Shuffle teams</button>`
      : '<span class="muted">The host picks the map, rules and teams. You can switch your own team with ⇄.</span>';
    if (isHost) {
      let n = Math.max(1, counts.hunter);
      const hn = $('#hn');
      $('#hm').onclick = () => { n = Math.max(1, n - 1); hn.textContent = n; };
      $('#hp').onclick = () => { n = Math.min(Math.max(1, room.players.length - 1), n + 1); hn.textContent = n; };
      $('#shuffle').onclick = () => this.app.net.send({ t: 'shuffle', hunters: n });
    }
    const start = $('#start');
    start.classList.toggle('hidden', !isHost);
    const ready = counts.hunter > 0 && counts.ghost > 0;
    start.disabled = !ready;
    $('#startnote').textContent = isHost
      ? (ready ? `${counts.hunter} hunter${counts.hunter === 1 ? '' : 's'} vs ${counts.ghost} ghost${counts.ghost === 1 ? '' : 's'}` : 'Each team needs at least one player or bot.')
      : 'Waiting for the host to start…';
  }

  addChat(m) {
    this.chat.push(m);
    if (this.chat.length > 80) this.chat.shift();
    this.renderChat();
  }

  renderChat() {
    const log = this.root.querySelector('#chatlog');
    if (!log) return;
    log.innerHTML = this.chat.map((m) => m.sys ? `<div class="sys">${esc(m.text)}</div>` : `<div><b style="color:${m.color}">${esc(m.from)}:</b> ${esc(m.text)}</div>`).join('');
    log.scrollTop = log.scrollHeight;
  }

  // ---------------------------------------------------------------- transitions
  showLoading(text) {
    this.screen = 'loading';
    this.root.innerHTML = `<div class="screen backdrop"><div class="panel center-card"><h2>Entering the haunt</h2><div class="spinner"></div><div class="muted" id="ltext">${esc(text || '')}</div></div></div>`;
  }

  setLoadingText(text) {
    const e = this.root.querySelector('#ltext');
    if (e) e.textContent = text;
  }

  showWait(m) {
    this.screen = 'wait';
    this.root.innerHTML = `<div class="screen backdrop"><div class="panel center-card"><h2>A round is in progress</h2>
      <p class="muted">You'll join when it ends. Relics delivered: ${m.captures}/3, about ${fmtTime(Math.max(0, m.timeLeft))} left.</p>
      <button class="btn" id="leave">Leave room</button></div></div>`;
    this.root.querySelector('#leave').onclick = () => { this.app.net.send({ t: 'leave' }); this.showHome(); };
  }

  showClickToPlay(game) {
    this.screen = 'click';
    const ghost = game.isGhost;
    this.root.innerHTML = `<div class="screen" style="background:rgba(5,4,10,.35)"><div class="panel center-card" style="max-width:520px">
      <h1 style="font-size:44px;color:var(--${ghost ? 'ghost' : 'hunter'})">You are a ${ghost ? 'Ghost' : 'Hunter'}</h1>
      <p>${ghost
        ? 'Find the relic and carry it to the glowing altar. Stay apart from other ghosts; talk with snaps, whistles and haunted objects.'
        : 'You are blind for a few seconds while the ghosts hide. Then listen, watch the room, and freeze them with the revealer.'}</p>
      <button class="btn primary" id="go">Click to play</button></div></div>`;
    this.root.querySelector('#go').onclick = () => { this.app.audio.resume(); game.input.requestLock(); this.clear(); };
  }

  showPause(game) {
    if (this.screen === 'results') return;
    this.screen = 'pause';
    const sens = game.input.sensitivity;
    const vol = this.app.audio.volume;
    this.root.innerHTML = `<div class="screen pause" style="background:rgba(5,4,10,.55)"><div class="panel">
      <h2>Paused</h2><p class="muted" style="margin:0">The round keeps going.</p>
      <label class="field"><div class="row"><span>Mouse sensitivity</span><b id="sv">${sens.toFixed(2)}</b></div><input type="range" id="sens" min="0.2" max="3" step="0.05" value="${sens}" /></label>
      <label class="field"><div class="row"><span>Volume</span><b id="vv">${Math.round(vol * 100)}%</b></div><input type="range" id="vol" min="0" max="1" step="0.05" value="${vol}" /></label>
      <label class="field"><div class="row"><span>Field of view</span><b id="fv">${game.camera.fov}°</b></div><input type="range" id="fov" min="60" max="100" step="1" value="${game.camera.fov}" /></label>
      <label class="field"><div class="row"><span>Graphics</span></div>
        <select id="quality" class="btn small">${['high', 'balanced', 'low'].map((q) => `<option value="${q}" ${this.app.settings.quality === q ? 'selected' : ''}>${q}</option>`).join('')}</select></label>
      <label class="field" style="flex-direction:row;align-items:center;gap:8px"><input type="checkbox" id="inv" ${game.input.invertY ? 'checked' : ''} /> Invert mouse Y</label>
      <button class="btn primary" id="resume">Resume</button>
      <button class="btn" id="quit">Leave room</button></div></div>`;
    const $ = (s) => this.root.querySelector(s);
    $('#sens').oninput = (e) => { game.input.sensitivity = +e.target.value; $('#sv').textContent = (+e.target.value).toFixed(2); localStorage.setItem('gh.sens', e.target.value); };
    $('#vol').oninput = (e) => { this.app.audio.setVolume(+e.target.value); $('#vv').textContent = `${Math.round(e.target.value * 100)}%`; localStorage.setItem('gh.vol', e.target.value); };
    $('#fov').oninput = (e) => {
      const v = +e.target.value;
      game.camera.fov = v;
      game.camera.updateProjectionMatrix();
      this.app.settings.fov = v;
      $('#fv').textContent = `${v}°`;
      localStorage.setItem('gh.fov', v);
    };
    $('#quality').onchange = (e) => this.app.setQuality(e.target.value);
    $('#inv').onchange = (e) => { game.input.invertY = e.target.checked; localStorage.setItem('gh.invert', e.target.checked ? '1' : '0'); };
    $('#resume').onclick = () => { game.input.requestLock(); this.clear(); };
    $('#quit').onclick = () => { this.app.leaveGame(); this.app.net.send({ t: 'leave' }); this.showHome(); };
  }

  hidePause() {
    if (this.screen === 'pause' || this.screen === 'click') this.clear();
  }

  showResults(m, game) {
    this.screen = 'results';
    const ghostWin = m.winner === ROLES.GHOST;
    const why = {
      captures: 'The relic was delivered three times.',
      time: 'Time ran out before the third delivery.',
      forfeit: ghostWin ? 'The hunters left the haunt.' : 'Every ghost fled.',
    }[m.reason] || '';
    const me = this.app.net.id;
    const youWon = game && ((ghostWin && game.isGhost) || (!ghostWin && !game.isGhost));
    const rows = m.stats.map((p) => `<tr>
      <td style="color:${p.color}">${esc(p.name)}${p.id === me ? ' (you)' : ''}</td>
      <td>${p.role === ROLES.HUNTER ? 'Hunter' : 'Ghost'}</td>
      <td>${p.role === ROLES.HUNTER ? `${p.freezes} freezes · ${p.shots} shots` : `${p.captures} deliveries · ${p.carry}s carrying`}</td>
      <td>${p.role === ROLES.GHOST ? `${p.frozen} frozen · ${p.snaps} snaps · ${p.manips} haunts` : ''}</td></tr>`).join('');
    const isHost = this.room?.host === me;
    this.root.innerHTML = `<div class="screen results" style="background:rgba(5,4,10,.6)"><div class="panel">
      <h1 class="${ghostWin ? 'ghost' : 'hunter'}">${ghostWin ? 'The Ghosts Win' : 'The Hunters Win'}</h1>
      <div class="why">${esc(why)} ${game ? (youWon ? 'Well played.' : 'Better luck next haunt.') : ''}</div>
      <table><tr><th>Player</th><th>Role</th><th></th><th></th></tr>${rows}</table>
      <div class="acts">${isHost ? '<button class="btn primary" id="lobby">Back to lobby now</button>' : '<span class="muted">Returning to the lobby shortly…</span>'}</div>
    </div></div>`;
    const b = this.root.querySelector('#lobby');
    if (b) b.onclick = () => this.app.net.send({ t: 'lobby' });
  }
}

