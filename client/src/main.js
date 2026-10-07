import './styles.css';
import * as THREE from 'three';
import { Net } from './net.js';
import { AudioEngine } from './game/audio.js';
import { Characters } from './game/avatars.js';
import { GameView } from './game/game.js';
import { UI } from './ui/ui.js';

const canvas = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.setSize(innerWidth, innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const app = {
  net: new Net(),
  audio: new AudioEngine(),
  renderer,
  characters: new Characters(),
  settings: { fov: Number(localStorage.getItem('gh.fov') || 75) },
  game: null,
  ui: null,
  leaveGame() {
    if (app.game) {
      app.game.dispose();
      app.game = null;
    }
    document.getElementById('hud').classList.add('hidden');
  },
};
app.ui = new UI(app);
app.audio.volume = Number(localStorage.getItem('gh.vol') || 0.8);
window.ghostHunter = app; // handy for debugging in the console
if (import.meta.env.DEV) window.THREE = THREE;
const charsReady = app.characters.load();

// idle backdrop when no round is running
const idle = { scene: new THREE.Scene(), cam: new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 100) };
idle.scene.background = new THREE.Color('#0b0a12');
renderer.setAnimationLoop(() => {
  if (app.game && !app.game.disposed && app.game.composer) app.game.frame();
  else renderer.render(idle.scene, idle.cam);
});
addEventListener('resize', () => {
  if (!app.game) renderer.setSize(innerWidth, innerHeight, false);
});

const net = app.net;
// Dev shortcut: ?test=ghost|hunter[&map=id][&bots=n][&time=s] spins up a room with bots and starts it.
const testParams = new URLSearchParams(location.search);
const testRole = import.meta.env.DEV ? testParams.get('test') : null;
let testState = testRole ? 'create' : null;
net.on('room', (m) => {
  if (testState !== 'setup') return;
  testState = 'started';
  const other = testRole === 'ghost' ? 'hunter' : 'ghost';
  net.send({ t: 'team', role: testRole });
  const n = Number(testParams.get('bots') || 3);
  for (let i = 0; i < n; i++) net.send({ t: 'addBot', role: testRole === 'ghost' && i > 0 ? 'ghost' : other });
  const settings = { t: 'settings' };
  if (testParams.get('map')) settings.map = testParams.get('map');
  if (testParams.get('time')) settings.roundTime = Number(testParams.get('time'));
  net.send(settings);
  setTimeout(() => net.send({ t: 'start' }), 200);
});
net.on('hello', () => {
  if (testState === 'create') {
    testState = 'setup';
    net.send({ t: 'create', name: localStorage.getItem('gh.name') || 'Tester' });
    return;
  }
  const code = new URLSearchParams(location.search).get('room');
  const name = localStorage.getItem('gh.name');
  if (code && name && !app.ui.room) net.send({ t: 'join', code, name });
  else if (!app.ui.room) app.ui.showHome();
});
net.on('room', (m) => {
  const first = !app.ui.room;
  app.ui.room = m;
  if (first) app.ui.chat.push({ sys: true, text: `Joined room ${m.code}.` });
  if (!app.game && m.phase === 'lobby' && testState !== 'started') app.ui.showLobby(m);
});
net.on('chat', (m) => app.ui.addChat(m));
net.on('error', (m) => {
  app.ui.toast(m.msg, 'error');
  if (!app.ui.room && app.ui.screen !== 'home') app.ui.showHome();
});
net.on('kicked', () => {
  app.leaveGame();
  app.ui.room = null;
  history.replaceState(null, '', location.pathname);
  app.ui.showHome();
  app.ui.toast('You were removed from the room.', 'error');
});
net.on('wait', (m) => { if (!app.game) app.ui.showWait(m); });
net.on('start', async (m) => {
  app.leaveGame();
  app.ui.showLoading('Summoning the spirits…');
  try {
    await Promise.all([charsReady, app.audio.init()]);
    const game = new GameView(app, m);
    await game.init((t) => app.ui.setLoadingText(t));
    app.game = game;
    app.ui.showClickToPlay(game);
  } catch (err) {
    console.error(err);
    app.ui.toast(`Failed to load the map: ${err.message}`, 'error');
  }
});
net.on('lobby', () => {
  app.leaveGame();
  if (app.ui.room) app.ui.showLobby(app.ui.room);
});
net.on('close', ({ was }) => {
  if (!was) return;
  app.leaveGame();
  app.ui.room = null;
  app.ui.toast('Lost connection to the server. Reconnecting…', 'error');
  app.ui.showHome();
});
