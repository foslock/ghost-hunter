// Interactive prop archetypes. Map JSON props carry a `type` from this table; the client animates
// nodes named P_<propId>_<part> inside the map GLB. `parts` lists nodes that must exist.
//
// Every archetype has three behaviours:
//   idle   - the natural ambient motion everyone sees all the time
//   subtle - a ghost nudge that stays within the range of natural motion (no cooldown)
//   big    - an attention-grabbing event with a loud sound (cooldown)
//
// Any prop may additionally contain decorative parts that animate regardless of archetype:
//   flame*  - flickering emissive flames (lights attached to the prop dim/flare with them)
//   cloth*  - meshes that ripple with a wind shader
//   bulb*   - emissive bulbs that glow (and blink during `flicker` events)

export const ARCHETYPES = {
  hinge:   { parts: ['pivot'], subtle: 'Nudge', big: 'Slam', sound: 'bang',
             params: 'axis (y|x|z, default y), dir (+1/-1 opening direction), rest (radians), open (max swing radians)' },
  swing:   { parts: ['pivot'], subtle: 'Sway', big: 'Shove', sound: 'creak',
             params: 'amp (idle radians), period (seconds), axes (xz|x|z)' },
  rock:    { parts: ['pivot'], subtle: 'Rock', big: 'Thrash', sound: 'creak',
             params: 'axis (x|z), period' },
  spin:    { parts: ['pivot'], subtle: 'Turn', big: 'Whirl', sound: 'whirr',
             params: 'axis (y|x|z), speed (idle rad/s, 0 = still), wobble (idle oscillation radians)' },
  clock:   { parts: ['hour', 'minute'], subtle: 'Rewind', big: 'Toll', sound: 'chime',
             params: 'axis (hand rotation axis, default z); optional part `pend` swings on the same axis' },
  foliage: { parts: ['pivot'], subtle: 'Rustle', big: 'Shake', sound: 'rustle',
             params: 'amp (idle sway radians), leaf (hex colour for falling-leaf particles)' },
  cloth:   { parts: ['cloth0'], subtle: 'Breathe', big: 'Billow', sound: 'whoosh',
             params: 'amp (idle ripple metres), axis (mesh-local displacement axis, default z)' },
  flame:   { parts: ['flame0'], subtle: 'Gutter', big: 'Flare', sound: 'whoomp', params: '' },
  jolt:    { parts: ['pivot'], subtle: 'Scoot', big: 'Jump', sound: 'thud', params: '' },
  music:   { parts: [], subtle: 'Plink', big: 'Crash', sound: 'piano',
             params: 'instrument (piano|musicbox|organ|calliope); optional part `pivot` (a lid on axis x)' },
  bell:    { parts: ['pivot'], subtle: 'Tremble', big: 'Ring', sound: 'bell', params: 'tone (Hz)' },
  flicker: { parts: ['bulb0'], subtle: 'Flicker', big: 'Blackout', sound: 'buzz', params: '' },
  bob:     { parts: ['pivot'], subtle: 'Drift', big: 'Yank', sound: 'squeak', params: 'amp (idle metres)' },
};

// Procedural sounds the client can synthesise. Props may override their archetype's sound with
// params.sound set to one of these.
export const SOUNDS = [
  'bang', 'creak', 'chime', 'clatter', 'rustle', 'whoosh', 'thud', 'whoomp', 'buzz', 'piano', 'musicbox',
  'organ', 'calliope', 'bell', 'whirr', 'squeak', 'jingle', 'splash', 'caw', 'rattle', 'gong',
];
