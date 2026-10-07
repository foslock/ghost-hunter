// A dim procedural environment map (sky gradient, horizon glow, moon) so glossy materials such
// as brass, glass and puddles have something to reflect instead of rendering black.
import * as THREE from 'three';

export function makeEnvironment(renderer, env) {
  const scene = new THREE.Scene();
  const sky = new THREE.Color(env.sky || '#101320');
  const hemi = env.hemi || {};
  const top = new THREE.Color(hemi.sky || '#5b6a9a').lerp(sky, 0.5).multiplyScalar(0.9);
  const horizon = new THREE.Color(env.fog?.color || env.sky || '#20243a').multiplyScalar(1.4);
  const ground = new THREE.Color(hemi.ground || '#2a1f18').multiplyScalar(0.8);
  const geo = new THREE.SphereGeometry(50, 32, 16);
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    uniforms: { uTop: { value: top }, uHorizon: { value: horizon }, uGround: { value: ground } },
    vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader: `uniform vec3 uTop, uHorizon, uGround; varying vec3 vP;
      void main(){ float h = normalize(vP).y;
        vec3 c = h > 0.0 ? mix(uHorizon, uTop, pow(h, 0.6)) : mix(uHorizon, uGround, pow(-h, 0.4));
        gl_FragColor = vec4(c, 1.0); }`,
  });
  scene.add(new THREE.Mesh(geo, mat));
  if (env.moon) {
    const d = new THREE.Vector3(...(env.moon.dir || [-0.4, -1, -0.3])).normalize().negate();
    const moon = new THREE.Mesh(new THREE.SphereGeometry(4, 16, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(env.moon.color || '#9fb4ff').multiplyScalar(6) }));
    moon.position.copy(d.multiplyScalar(40));
    scene.add(moon);
  } else {
    // indoors: a few warm "windows of candlelight" so brass glints
    for (const [x, y, z] of [[30, 8, 10], [-25, 6, -20], [5, 12, 35]]) {
      const glow = new THREE.Mesh(new THREE.SphereGeometry(5, 12, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color('#ffb066').multiplyScalar(2.5) }));
      glow.position.set(x, y, z);
      scene.add(glow);
    }
  }
  const pmrem = new THREE.PMREMGenerator(renderer);
  const rt = pmrem.fromScene(scene, 0.02);
  pmrem.dispose();
  geo.dispose();
  mat.dispose();
  return rt.texture;
}
