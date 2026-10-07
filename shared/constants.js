// Gameplay tuning shared by server and client. Distances are metres, times are seconds.

export const TICK_RATE = 30;            // server simulation steps per second
export const SNAPSHOT_RATE = 20;        // snapshots sent to clients per second
export const CLIENT_SEND_RATE = 20;     // client position updates per second

export const PLAYER = {
  radius: 0.32,
  height: 1.7,
  eye: 1.55,
  stepHeight: 0.45,
  gravity: 22,
  jump: 6.2,
};

export const HUNTER = {
  speed: 5.0,
  rayRange: 11,
  rayHalfAngle: 14 * Math.PI / 180,
  rayCooldown: 2.2,
  blindTime: 10,          // hunters wait in the dark while ghosts spread out
};

export const GHOST = {
  speed: 4.6,
  carrySpeed: 3.5,
  gravity: 9,             // ghosts drift down slowly
  jump: 5.0,              // ~1.4 m hop
  seeRadius: 4.5,         // ghosts can see each other inside this range
  snapRadius: 9,          // ~double the see radius
  whistleRadius: 48,
  whistleCooldown: 12,
  manipReach: 7,
  subtleRate: 0.35,       // anti-spam only; subtle manipulations have no real cooldown
  bigCooldown: 10,
  clumpLimit: 4,          // seconds near another ghost before both are exposed
  clumpDecay: 1.5,        // clump meter drains this many times faster than it fills
  exposeTime: 5,
  freezeTime: 3,
};

export const RELIC = {
  pickupRadius: 1.3,
  captureRadius: 1.8,
  captureChannel: 2.5,    // carrier must hold the relic on the altar this long
  carryLimit: 14,         // seconds of carry stamina (lobby-configurable)
  staminaRegen: 0.8,      // per second while not carrying
  minPickupStamina: 4,
  regrabDelay: 2.5,       // a ghost who drops the relic can't grab it straight back
  dripInterval: 1.1,
  dripLife: 9,
  humRadius: 8,           // hunters can hear a carried relic within this range
  minPairFraction: 0.55,  // spawn/capture pairs must be at least this fraction of the longest pair
};

export const ROUND = {
  capturesToWin: 3,
  defaultTime: 6 * 60,
  defaultPenalty: 30,
  countdown: 3,
  resultsTime: 14,
};

export const LOBBY_LIMITS = {
  maxPlayers: 16,
  roundTime: [120, 900],
  penaltyTime: [5, 90],
  carryLimit: [5, 60],
};

export const ROLES = { HUNTER: 'hunter', GHOST: 'ghost' };

export const PHASE = {
  LOBBY: 'lobby',
  BLIND: 'blind',       // round started, hunters can't see yet
  PLAY: 'play',
  RESULTS: 'results',
};

// Bit flags packed into each player entry of a snapshot.
export const PF = {
  FROZEN: 1,
  EXPOSED: 2,
  PENALTY: 4,
  CARRYING: 8,
  NEAR: 16,     // visible only because the viewer is a ghost in close proximity
};

export const MAPS = [
  { id: 'manor', name: 'Hollowmere Manor', blurb: 'A candlelit Victorian house where every clock disagrees.' },
  { id: 'farm', name: 'Thistlewick Farm', blurb: 'An autumn farmstead at dusk: corn rows, laundry lines and a creaking windmill.' },
  { id: 'carnival', name: 'Lanternfall Carnival', blurb: 'A shuttered fairground where the carousel still turns on its own.' },
];

export const GHOST_NAMES = ['Wisp', 'Murmur', 'Hollow', 'Sorrow', 'Flicker', 'Gloom', 'Whimper', 'Drift', 'Shiver', 'Echo', 'Mope', 'Pallor'];
export const HUNTER_NAMES = ['Van Bell', 'Ash', 'Marlowe', 'Greaves', 'Thorne', 'Pike'];

export const PLAYER_COLORS = [
  '#8fd3ff', '#b9a7ff', '#7fffd4', '#ffb3c7', '#ffe08a', '#a8ff8f',
  '#ff9f7a', '#9ad0ff', '#e0a8ff', '#88ffe8', '#ffd1a8', '#c8ff9a',
  '#ff8fb8', '#a0b4ff', '#fff38f', '#8fffb0',
];
