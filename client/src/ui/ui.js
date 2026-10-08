// Menus: home, lobby, loading, waiting, pause and results screens.
import { GHOST, HUNTER, LOBBY_LIMITS, RELIC, ROLES } from '../../../shared/constants.js';

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

  // ---------------------------------------------------------------- how to play
  // A little handbook with tabbed pages: everything the home screen used to cram in.
  showHowto(page = 'haunt') {
    const k = (...keys) => keys.map((x) => `<kbd>${x}</kbd>`).join('');
    const pages = {
      haunt: ['The Haunt', `
        <p class="lede">Each night a train of spirits rides out to a haunted place. The <b class="g">ghosts</b> smuggle a relic between
        altars; the <b class="h">hunters</b> try to stop them, though they cannot see a single ghost.</p>
        <p>The ghosts win by delivering the relic <b>three times</b> before the clock runs out. Every map has a dozen identical
        altars; only ghosts know where the relic waits and which altar takes it. After each delivery both move somewhere new.</p>
        <p>Hunters begin blind for ten seconds while the ghosts scatter.</p>`],
      ghosts: ['For Ghosts', `
        <p class="lede">You are unseen. Hunters can't see you at all, and fellow ghosts only within ${GHOST.seeRadius} m, so you talk
        in other ways.</p>
        <table class="keys">
          <tr><td>${k('W', 'A', 'S', 'D')}</td><td>drift about</td></tr>
          <tr><td>${k('Space')}</td><td>float upward; you sink back slowly</td></tr>
          <tr><td>${k('Click')}</td><td>snap your fingers: heard within ${GHOST.snapRadius} m, as often as you like</td></tr>
          <tr><td>${k('F')}</td><td>whistle: carries ${GHOST.whistleRadius} m, then rest ${GHOST.whistleCooldown}s</td></tr>
          <tr><td>${k('E')}</td><td>subtle haunt: nudge a thing within its natural motion</td></tr>
          <tr><td>${k('Q')}</td><td>big haunt: loud and unmistakable (rest ${GHOST.bigCooldown}s)</td></tr>
          <tr><td>${k('G')}</td><td>set the relic down for someone else</td></tr>
        </table>
        <p>Linger beside another ghost for ${GHOST.clumpLimit} seconds and you'll both be <b>exposed</b> to the hunters.</p>`],
      hunters: ['For Hunters', `
        <p class="lede">You carry the revealer: a lantern that throws a short cone of spectral light.</p>
        <table class="keys">
          <tr><td>${k('W', 'A', 'S', 'D')}</td><td>walk</td></tr>
          <tr><td>${k('Space')}</td><td>jump</td></tr>
          <tr><td>${k('Shift')}</td><td>creep</td></tr>
          <tr><td>${k('Click')}</td><td>fire the revealer: ${HUNTER.rayRange} m, recharges in ${HUNTER.rayCooldown}s</td></tr>
        </table>
        <p>A ghost caught in the cone freezes, then spends time in the map's penalty cage. Catch the one carrying the relic and it
        shatters: it re-forms elsewhere and the capture altar moves too.</p>
        <p><b>Signs of a spirit:</b> snaps and whistles (arcs around your sights show the direction); things that move wrongly,
        like a clock running backwards, a curtain breathing or a door easing open; drips of glowing ectoplasm; the relic's hum up close.</p>`],
      relic: ['The Relic', `
        <p class="lede">Walk into the relic to take it. Carry it to the capture altar and hold it there a moment to deliver it.</p>
        <p>Your grip tires: after ${RELIC.carryLimit} seconds (the host can change this) it slips from your hands and you must rest
        before carrying again, so long journeys need a relay.</p>
        <p>A carried relic slows you, drips glowing ectoplasm and hums. The delivery ritual can be seen and heard by everyone.</p>`],
      room: ['The Waiting Room', `
        <p class="lede">Between rounds everyone gathers in the station waiting room. Walk about and practise; nothing counts in there.</p>
        <p>Stand on the <b class="h">Hunters</b> or <b class="g">Ghosts</b> floor medallion to change sides. The walls carry these
        instructions, and the notice board shows the next destination and the teams.</p>
        <p>${k('Enter')} to talk, ${k('Esc')} for the room menu. The host picks the map, rules and bots and starts the round from there.</p>`],
    };
    const tabs = Object.entries(pages).map(([id, [name]]) => `<button class="tab ${id === page ? 'on' : ''}" data-page="${id}">${name}</button>`).join('');
    const [head, body] = pages[page];
    let m = this.root.querySelector('.handbook-wrap');
    if (!m) {
      m = document.createElement('div');
      m.className = 'screen handbook-wrap';
      this.root.append(m);
      m.onclick = (e) => { if (e.target === m) m.remove(); };
    }
    m.innerHTML = `<div class="handbook">
      <div class="hb-tabs">${tabs}</div>
      <div class="hb-page"><div class="hb-kicker">The Spirit Railway Handbook</div><h2>${head}</h2>${body}
        <button class="btn hb-close">Close the handbook</button></div></div>`;
    for (const b of m.querySelectorAll('.tab')) b.onclick = () => { this.click(); this.showHowto(b.dataset.page); };
    m.querySelector('.hb-close').onclick = () => { this.click(); m.remove(); };
  }

  click() {
    try {
      this.app.audio.resume();
      this.app.audio.play('tick', null, { volume: 0.5 });
    } catch {
      /* audio not ready yet */
    }
  }

  // ---------------------------------------------------------------- home
  showHome() {
    this.screen = 'home';
    const name = localStorage.getItem('gh.name') || '';
    const code = (new URLSearchParams(location.search).get('room') || '').toUpperCase().slice(0, 4);
    const serial = String(1000 + Math.floor(Math.random() * 9000));
    this.root.innerHTML = `
      <div class="screen home">
        <header class="marquee">
          <div class="line">The Spirit Railway &middot; Departures Nightly</div>
          <h1>Ghost Hunter</h1>
          <div class="line">Hollowmere &middot; Thistlewick &middot; Lanternfall</div>
        </header>
        <div class="ticket">
          <div class="stub">
            <div class="stub-no">N&ordm; ${serial}</div>
            <button class="stub-link" id="howto">How to play</button>
            <div class="stub-foot">retain this portion</div>
          </div>
          <div class="ticket-body">
            <div class="ticket-head"><span>Single Journey</span><span>Third Class &middot; Spirits Welcome</span></div>
            <label class="passenger">Passenger
              <input id="name" type="text" maxlength="16" placeholder="sign here" value="${esc(name)}" autocomplete="off" spellcheck="false" />
            </label>
            <div class="ticket-actions">
              <button class="btn primary board" id="create">Board a new train</button>
              <div class="join">
                <span class="join-label">or join a friend's train</span>
                <div class="slots" id="slots">${[0, 1, 2, 3].map((i) => `<input maxlength="1" data-i="${i}" value="${esc(code[i] || '')}" autocomplete="off" spellcheck="false" aria-label="Room code letter ${i + 1}" />`).join('')}</div>
                <button class="btn small" id="join">Punch</button>
              </div>
            </div>
            <div class="stamp">Admit One</div>
          </div>
        </div>
      </div>`;
    const nameEl = this.root.querySelector('#name');
    const slots = [...this.root.querySelectorAll('#slots input')];
    const getName = () => {
      const n = nameEl.value.trim() || `Passenger ${Math.floor(Math.random() * 900 + 100)}`;
      localStorage.setItem('gh.name', n);
      return n;
    };
    const codeVal = () => slots.map((x) => x.value).join('').toUpperCase();
    const create = () => { this.click(); this.app.net.send({ t: 'create', name: getName() }); };
    const join = () => {
      const c = codeVal();
      const box = this.root.querySelector('.slots');
      if (c.length !== 4) {
        box.classList.remove('shake');
        void box.offsetWidth;
        box.classList.add('shake');
        return;
      }
      this.click();
      this.app.net.send({ t: 'join', code: c, name: getName() });
    };
    slots.forEach((inp, i) => {
      inp.oninput = () => {
        inp.value = inp.value.replace(/[^a-z]/gi, '').toUpperCase().slice(-1);
        if (inp.value && slots[i + 1]) slots[i + 1].focus();
        this.root.querySelector('#join').classList.toggle('ready', codeVal().length === 4);
      };
      inp.onkeydown = (e) => {
        if (e.key === 'Backspace' && !inp.value && slots[i - 1]) slots[i - 1].focus();
        if (e.key === 'Enter') join();
      };
      inp.onpaste = (e) => {
        const t = (e.clipboardData?.getData('text') || '').replace(/[^a-z]/gi, '').toUpperCase().slice(0, 4);
        if (!t) return;
        e.preventDefault();
        slots.forEach((x, j) => { x.value = t[j] || ''; });
        this.root.querySelector('#join').classList.toggle('ready', codeVal().length === 4);
      };
    });
    this.root.querySelector('#create').onclick = create;
    this.root.querySelector('#join').onclick = join;
    this.root.querySelector('#howto').onclick = () => { this.click(); this.showHowto(); };
    nameEl.onkeydown = (e) => { if (e.key === 'Enter') (codeVal().length === 4 ? join() : create()); };
    if (code.length === 4) this.root.querySelector('#join').classList.add('ready');
    (name ? (code ? this.root.querySelector('#join') : slots[0]) : nameEl).focus();
  }

  // ---------------------------------------------------------------- lobby
  // The room menu: an overlay on top of the waiting room (opened with Esc). The host sets the map,
  // rules and teams here; everyone gets chat, the invite link and their own settings.
  showLobby(room, game = this.app.game) {
    this.room = room;
    const me = this.app.net.id;
    const isHost = room.host === me;
    if (this.screen !== 'lobby') {
      this.screen = 'lobby';
      const input = game?.input;
      const sens = input?.sensitivity ?? 1;
      const vol = this.app.audio.volume;
      const fov = game?.camera?.fov ?? this.app.settings.fov;
      this.root.innerHTML = `
        <div class="screen lobby room-overlay">
          <div class="lobby-grid">
            <div class="lobby-col">
              <div class="panel">
                <div class="room-head">
                  <div><div class="muted">Room code</div><div class="room-code"></div></div>
                  <div style="display:flex;gap:8px;flex-wrap:wrap">
                    ${game ? '<button class="btn small primary" id="resume">Back to the room</button>' : ''}
                    <button class="btn small" id="howto">How to play</button><button class="btn small" id="copy">Copy invite link</button><button class="btn small" id="leave">Leave</button></div>
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
              <div class="panel"><h2>Your settings</h2><div class="settings" id="mine">
                <label class="field"><div class="row"><span>Mouse sensitivity</span><b id="sv">${sens.toFixed(2)}</b></div><input type="range" id="sens" min="0.2" max="3" step="0.05" value="${sens}" /></label>
                <label class="field"><div class="row"><span>Volume</span><b id="vv">${Math.round(vol * 100)}%</b></div><input type="range" id="vol" min="0" max="1" step="0.05" value="${vol}" /></label>
                <label class="field"><div class="row"><span>Field of view</span><b id="fv">${fov}°</b></div><input type="range" id="fov" min="60" max="100" step="1" value="${fov}" /></label>
                <label class="field"><div class="row"><span>Graphics</span></div><select id="quality" class="btn small">${['high', 'balanced', 'low'].map((q) => `<option value="${q}" ${this.app.settings.quality === q ? 'selected' : ''}>${q}</option>`).join('')}</select></label>
                <label class="field" style="flex-direction:row;align-items:center;gap:8px"><input type="checkbox" id="inv" ${input?.invertY ? 'checked' : ''} /> Invert mouse Y</label>
              </div></div>
              <div class="lobby-actions"><div class="grow muted" id="startnote"></div><button class="btn primary" id="start">Start round</button></div>
            </div>
          </div>
        </div>`;
      this.bindPersonalSettings(game);
      const resume = this.root.querySelector('#resume');
      if (resume) resume.onclick = () => { this.app.audio.resume(); game.input.requestLock(); this.clear(); };
      this.root.querySelector('#howto').onclick = () => this.showHowto();
      this.root.querySelector('#copy').onclick = () => {
        const url = `${location.origin}${location.pathname}?room=${this.room.code}`;
        navigator.clipboard?.writeText(url).then(() => this.toast('Invite link copied.'), () => this.toast(url));
      };
      this.root.querySelector('#leave').onclick = () => {
        this.app.leaveGame();
        this.app.net.send({ t: 'leave' });
        this.room = null;
        history.replaceState(null, '', location.pathname);
        this.showHome();
      };
      this.root.querySelector('#start').onclick = () => this.app.net.send({ t: 'start' });
      const chatin = this.root.querySelector('#chatin');
      chatin.onkeydown = (e) => {
        if (e.key === 'Enter' && chatin.value.trim()) { this.app.net.send({ t: 'chat', text: chatin.value }); chatin.value = ''; }
      };
      this.renderChat();
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
          ${p.id === room.host ? '<span class="tag host">host</span>' : ''}${p.bot ? '<span class="tag">bot</span>' : ''}${p.where === 'round' ? '<span class="tag">in round</span>' : ''}
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
    const roundOn = !!room.round;
    start.classList.toggle('hidden', !isHost || roundOn);
    const ready = counts.hunter > 0 && counts.ghost > 0;
    start.disabled = !ready;
    const mapName = (id) => room.maps.find((m) => m.id === id)?.name || id;
    $('#startnote').textContent = roundOn
      ? `A round is in progress on ${mapName(room.round.map)} (${fmtTime(Math.max(0, room.round.timeLeft))} left). You'll join the next one.`
      : isHost
        ? (ready ? `${counts.hunter} hunter${counts.hunter === 1 ? '' : 's'} vs ${counts.ghost} ghost${counts.ghost === 1 ? '' : 's'}` : 'Each team needs at least one player or bot.')
        : 'Waiting for the host to start…';
  }

  bindPersonalSettings(game) {
    const $ = (sel) => this.root.querySelector(sel);
    if (!$('#sens')) return;
    $('#sens').oninput = (e) => {
      if (game) game.input.sensitivity = +e.target.value;
      $('#sv').textContent = (+e.target.value).toFixed(2);
      localStorage.setItem('gh.sens', e.target.value);
    };
    $('#vol').oninput = (e) => { this.app.audio.setVolume(+e.target.value); $('#vv').textContent = `${Math.round(e.target.value * 100)}%`; localStorage.setItem('gh.vol', e.target.value); };
    $('#fov').oninput = (e) => {
      const v = +e.target.value;
      if (game) { game.camera.fov = v; game.camera.updateProjectionMatrix(); }
      this.app.settings.fov = v;
      $('#fv').textContent = `${v}°`;
      localStorage.setItem('gh.fov', v);
    };
    $('#quality').onchange = (e) => this.app.setQuality(e.target.value);
    $('#inv').onchange = (e) => { if (game) game.input.invertY = e.target.checked; localStorage.setItem('gh.invert', e.target.checked ? '1' : '0'); };
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

  showClickToEnter(game) {
    this.screen = 'click';
    this.root.innerHTML = `<div class="screen enter-prompt"><button class="plaque" id="go">
      <span class="plaque-small">The Waiting Room</span><span class="plaque-big">Step inside</span><span class="plaque-small">click to enter</span></button></div>`;
    this.root.querySelector('#go').onclick = () => { this.click(); game.input.requestLock(); this.clear(); };
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
    if (this.screen === 'pause' || this.screen === 'click' || this.screen === 'lobby') this.clear();
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

