// The waiting room's wall boards, painted onto canvases: the notice of departure (live room
// state), the Ghost's Guide, the Hunter's Handbook and the house-rules chalkboard.
import { GHOST, HUNTER, ROLES } from '../../../shared/constants.js';

const DISPLAY = '"IM Fell English SC", Georgia, serif';
const FELL = '"IM Fell English", Georgia, serif';
const BODY = 'Spectral, Georgia, serif';
const CHALK = 'Caveat, "Comic Sans MS", cursive';
const INK = '#2a1d14';
const FADED = '#6b5640';
const RUST = '#8c3b1c';
const TEAL = '#1f5f6e';

const fmt = (v) => `${Math.floor(v / 60)}:${String(v % 60).padStart(2, '0')}`;

export const FONTS_READY = Promise.all([
  `52px ${DISPLAY}`, `30px ${FELL}`, `italic 26px ${FELL}`, `26px ${BODY}`, `600 26px ${BODY}`, `48px ${CHALK}`, `700 48px ${CHALK}`,
].map((f) => document.fonts?.load(f).catch(() => null))).catch(() => null);

// ---------------------------------------------------------------- paper and helpers
function paper(g, W, H, seed = 1) {
  const grad = g.createRadialGradient(W / 2, H / 2, H * 0.2, W / 2, H / 2, W * 0.75);
  grad.addColorStop(0, '#efe4c8');
  grad.addColorStop(1, '#d6c39b');
  g.fillStyle = grad;
  g.fillRect(0, 0, W, H);
  // foxing and stains
  let s = seed * 9301;
  const rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280);
  for (let i = 0; i < 26; i++) {
    g.fillStyle = `rgba(120, 82, 40, ${0.03 + rnd() * 0.05})`;
    g.beginPath();
    g.arc(rnd() * W, rnd() * H, 6 + rnd() * 40, 0, Math.PI * 2);
    g.fill();
  }
  g.strokeStyle = '#7a5c3a';
  g.lineWidth = 5;
  g.strokeRect(16, 16, W - 32, H - 32);
  g.lineWidth = 1.5;
  g.strokeRect(27, 27, W - 54, H - 54);
  // corner flourishes
  for (const [x, y, sx, sy] of [[27, 27, 1, 1], [W - 27, 27, -1, 1], [27, H - 27, 1, -1], [W - 27, H - 27, -1, -1]]) {
    g.beginPath();
    g.moveTo(x + sx * 4, y + sy * 46);
    g.quadraticCurveTo(x + sx * 4, y + sy * 4, x + sx * 46, y + sy * 4);
    g.stroke();
    g.beginPath();
    g.arc(x + sx * 18, y + sy * 18, 5, 0, Math.PI * 2);
    g.stroke();
  }
}

function rule(g, x0, x1, y, color = '#7a5c3a') {
  g.strokeStyle = color;
  g.lineWidth = 1.5;
  g.beginPath();
  g.moveTo(x0, y);
  g.lineTo(x1, y);
  g.stroke();
  const mx = (x0 + x1) / 2;
  g.fillStyle = color;
  g.beginPath();
  g.moveTo(mx - 8, y);
  g.lineTo(mx, y - 5);
  g.lineTo(mx + 8, y);
  g.lineTo(mx, y + 5);
  g.closePath();
  g.fill();
}

function wrap(g, text, x, y, maxW, lh) {
  const words = String(text || '').split(' ');
  let line = '';
  let lines = 0;
  for (const word of words) {
    const test = line ? `${line} ${word}` : word;
    if (g.measureText(test).width > maxW && line) {
      g.fillText(line, x, y + lines * lh);
      line = word;
      lines++;
    } else line = test;
  }
  if (line) { g.fillText(line, x, y + lines * lh); lines++; }
  return lines;
}

// a small brass keycap with a legend
function key(g, label, x, y, h = 36) {
  g.font = `600 ${Math.round(h * 0.52)}px ${BODY}`;
  const w = Math.max(h, g.measureText(label).width + h * 0.6);
  const r = 6;
  g.fillStyle = '#c9a65a';
  g.strokeStyle = '#6b5226';
  g.lineWidth = 2;
  g.beginPath();
  g.roundRect(x, y - h + 6, w, h, r);
  g.fill();
  g.stroke();
  g.fillStyle = 'rgba(255,255,255,0.25)';
  g.fillRect(x + 4, y - h + 9, w - 8, 4);
  g.fillStyle = '#2a1d0c';
  g.textAlign = 'center';
  g.fillText(label, x + w / 2, y - h * 0.18 + 1);
  g.textAlign = 'left';
  return w;
}

// one control line: keycaps then a description
function control(g, keys, text, x, y, maxW) {
  let cx = x;
  for (const k of keys) cx += key(g, k, cx, y) + 6;
  g.font = `25px ${BODY}`;
  g.fillStyle = INK;
  g.textAlign = 'left';
  wrap(g, text, Math.max(cx + 8, x + 120), y, maxW - (Math.max(cx + 8, x + 120) - x), 28);
}

function title(g, W, text, sub, color = INK) {
  g.textAlign = 'center';
  g.fillStyle = color;
  g.font = `60px ${DISPLAY}`;
  g.fillText(text, W / 2, 96);
  g.font = `italic 26px ${FELL}`;
  g.fillStyle = FADED;
  g.fillText(sub, W / 2, 130);
  rule(g, W * 0.22, W * 0.78, 150);
}

// ---------------------------------------------------------------- boards
export function drawNotice(c, room) {
  const g = c.getContext('2d');
  const W = c.width, H = c.height;
  paper(g, W, H, 3);
  const map = room.maps.find((m) => m.id === room.settings.map) || { name: room.settings.map, blurb: '' };
  g.textAlign = 'center';
  g.fillStyle = INK;
  g.font = `52px ${DISPLAY}`;
  g.fillText('Notice of Departure', W / 2, 92);
  g.font = `italic 26px ${FELL}`;
  g.fillStyle = FADED;
  g.fillText(`Room ${room.code}  ·  the next train calls at`, W / 2, 130);
  g.fillStyle = RUST;
  g.font = `66px ${DISPLAY}`;
  g.fillText(map.name, W / 2, 205);
  g.font = `italic 25px ${FELL}`;
  g.fillStyle = FADED;
  wrap(g, map.blurb, W / 2, 242, W - 180, 28);
  rule(g, W * 0.18, W * 0.82, 290);
  const s = room.settings;
  g.font = `27px ${BODY}`;
  g.fillStyle = INK;
  g.fillText(`Round ${fmt(s.roundTime)}   ·   Penalty cage ${s.penaltyTime}s   ·   Relic grip ${s.carryLimit}s`, W / 2, 330);
  const col = (role, x, head, color) => {
    const list = room.players.filter((p) => p.role === role);
    g.textAlign = 'left';
    g.font = `36px ${DISPLAY}`;
    g.fillStyle = color;
    g.fillText(`${head} (${list.length})`, x, 388);
    g.font = `25px ${BODY}`;
    g.fillStyle = INK;
    list.slice(0, 6).forEach((p, i) => {
      g.fillText(`${p.id === room.host ? '★ ' : '· '}${p.name}${p.where === 'round' ? ' — on the train' : ''}`, x, 424 + i * 29);
    });
    if (list.length > 6) g.fillText(`…and ${list.length - 6} more`, x, 424 + 6 * 29);
  };
  col(ROLES.HUNTER, 80, 'Hunters', RUST);
  col(ROLES.GHOST, W / 2 + 40, 'Ghosts', TEAL);
  g.textAlign = 'center';
  g.font = `italic 25px ${FELL}`;
  g.fillStyle = FADED;
  const host = room.players.find((p) => p.id === room.host);
  g.fillText(room.round
    ? `A train is already out — back in ${fmt(Math.max(0, room.round.timeLeft))}. All aboard the next one.`
    : `Departs when ${host ? host.name : 'the host'} is ready.  The host chooses the destination from the room menu (Esc).`, W / 2, H - 52);
}

// two-column guide: keys on the left, advice on the right
function guide(c, seed, head, sub, color, controls, sections, footer) {
  const g = c.getContext('2d');
  const W = c.width, H = c.height;
  paper(g, W, H, seed);
  title(g, W, head, sub, color);
  const lx = 64, mid = W * 0.5, rx = mid + 26, rw = W - rx - 60;
  let y = 206;
  for (const [k, t] of controls) {
    let cx = lx;
    for (const kk of k) cx += key(g, kk, cx, y, 38) + 6;
    g.font = `26px ${BODY}`;
    g.fillStyle = INK;
    g.textAlign = 'left';
    const tx = Math.max(cx + 10, lx + 132);
    y += 30 * wrap(g, t, tx, y, mid - 20 - tx, 28) + 16;
  }
  // column rule
  g.strokeStyle = 'rgba(122, 92, 58, 0.6)';
  g.lineWidth = 1.5;
  g.beginPath();
  g.moveTo(mid, 180);
  g.lineTo(mid, H - 86);
  g.stroke();
  let ry = 210;
  for (const [h, text] of sections) {
    g.font = `34px ${DISPLAY}`;
    g.fillStyle = color;
    g.textAlign = 'left';
    g.fillText(h, rx, ry);
    ry += 34;
    g.font = `25px ${BODY}`;
    g.fillStyle = INK;
    ry += 29 * wrap(g, text, rx, ry, rw, 29) + 16;
  }
  g.textAlign = 'center';
  g.font = `italic 25px ${FELL}`;
  g.fillStyle = FADED;
  g.fillText(footer, W / 2, H - 46);
}

export function drawGhostGuide(c, settings) {
  guide(c, 5, "The Ghost's Guide", 'being advice for the recently departed', TEAL, [
    [['W', 'A', 'S', 'D'], 'drift about'],
    [['Space'], 'float up; sink back slowly'],
    [['Click'], `snap: heard ${GHOST.snapRadius} m away, use freely`],
    [['F'], `whistle: carries ${GHOST.whistleRadius} m (rest ${GHOST.whistleCooldown}s)`],
    [['E'], 'subtle haunt, within its natural motion'],
    [['Q'], `big haunt, loud and plain (rest ${GHOST.bigCooldown}s)`],
    [['G'], 'set the relic down'],
  ], [
    ['Unseen', `Hunters cannot see you; fellow ghosts only within ${GHOST.seeRadius} m. Linger together ${GHOST.clumpLimit}s and you're all exposed.`],
    ['The relic', `Bear it to the glowing altar three times. Your grip fails after ${settings?.carryLimit ?? 14}s, so pass it on. It drips, and it hums.`],
  ], "To hunt instead, stand upon the hunters' medallion.");
}

export function drawHunterGuide(c, settings) {
  guide(c, 7, "The Hunter's Handbook", 'on the detection and detainment of spirits', RUST, [
    [['W', 'A', 'S', 'D'], 'walk'],
    [['Space'], 'jump'],
    [['Shift'], 'creep quietly'],
    [['Click'], `revealer: a ${HUNTER.rayRange} m cone that freezes ghosts (recharges ${HUNTER.rayCooldown}s)`],
  ], [
    ['Signs of a spirit', 'Snaps and whistles, which way the arcs point; things moving wrongly: a clock run backward, a curtain breathing, a door easing open; ectoplasm drips; the relic’s hum.'],
    ['The cage', `A frozen ghost serves ${settings?.penaltyTime ?? 30}s. Freeze the carrier and the relic shatters, and both altars move.`],
  ], "To haunt instead, stand upon the ghosts' medallion.");
}

export function drawRules(c, settings) {
  const g = c.getContext('2d');
  const W = c.width, H = c.height;
  // slate with chalk dust
  g.fillStyle = '#1e2624';
  g.fillRect(0, 0, W, H);
  for (let i = 0; i < 1400; i++) {
    g.fillStyle = `rgba(230, 235, 230, ${Math.random() * 0.035})`;
    g.fillRect(Math.random() * W, Math.random() * H, 2 + Math.random() * 30, 1 + Math.random() * 3);
  }
  const chalk = (text, x, y, size, color = '#ecefe6', align = 'left', weight = 500) => {
    g.font = `${weight} ${size}px ${CHALK}`;
    g.textAlign = align;
    g.fillStyle = color;
    g.globalAlpha = 0.92;
    g.fillText(text, x, y);
    g.globalAlpha = 0.25;
    g.fillText(text, x + 1.5, y + 1);
    g.globalAlpha = 1;
  };
  chalk("Tonight's Haunt", W / 2, 80, 70, '#f3e9b8', 'center', 700);
  g.strokeStyle = 'rgba(243,233,184,0.7)';
  g.lineWidth = 3;
  g.beginPath();
  g.moveTo(W * 0.28, 98);
  g.quadraticCurveTo(W / 2, 110, W * 0.72, 96);
  g.stroke();
  const rows = [
    ['Ghosts', `deliver the relic three times before the ${fmt(settings?.roundTime ?? 360)} clock runs out`, '#bfefff'],
    ['Hunters', 'stop them. You start blind for 10 seconds while they scatter.', '#ffd0a0'],
    ['Altars', 'all look alike. Only ghosts know which is which.', '#ecefe6'],
    ['Haunt', 'anything that moves. Everyone sees it move.', '#ecefe6'],
  ];
  let y = 170;
  for (const [head, text, color] of rows) {
    chalk(`${head} —`, 60, y, 44, color, 'left', 700);
    g.font = `700 44px ${CHALK}`;
    const hw = g.measureText(`${head} — `).width + 6;
    g.font = `500 40px ${CHALK}`;
    const words = text.split(' ');
    let line = '', ly = y, lx = 60 + hw;
    for (const wd of words) {
      const test = line ? `${line} ${wd}` : wd;
      if (g.measureText(test).width > W - 60 - lx && line) {
        chalk(line, lx, ly, 40);
        line = wd;
        ly += 44;
        lx = 100;
      } else line = test;
    }
    if (line) chalk(line, lx, ly, 40);
    y = ly + 62;
  }
  chalk('Enter: speak    ·    Esc: room menu', W / 2, H - 40, 38, '#d8dccf', 'center');
}
