// Builds nova.glb: the Nova AI mascot, generated procedurally from the design canvas.
// Run: node build.mjs
import * as THREE from 'three';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import fs from 'node:fs';

// GLTFExporter uses the browser FileReader to assemble the binary; Node has Blob but no FileReader.
globalThis.FileReader = class {
  readAsArrayBuffer(blob) { blob.arrayBuffer().then((b) => { this.result = b; this.onloadend?.(); }); }
  readAsDataURL(blob) {
    blob.arrayBuffer().then((b) => {
      this.result = `data:${blob.type || 'application/octet-stream'};base64,${Buffer.from(b).toString('base64')}`;
      this.onloadend?.();
    });
  }
};

// ---------------------------------------------------------------------------
// Units: the design sheet is drawn in "u" (SVG units, y down, soles at y=464).
// The model is 1.0 m from sole to head top (416 u), +Y up, facing +Z.
// ---------------------------------------------------------------------------
const S = 1 / 416;
const u = (v) => v * S;
const V = (x, y, z = 0) => new THREE.Vector3((x - 200) * S, (464 - y) * S, z * S);
const DEG = Math.PI / 180;

// Front surface of the visor (u), used to seat the face elements on it.
function zv(x, y) {
  const dx = Math.max(0, Math.abs(x - 200) - 35);
  const dy = Math.max(0, Math.abs(y - 154) - 5);
  return 65 + Math.sqrt(Math.max(0, 55 * 55 - dx * dx - dy * dy));
}
function visorNormal(x, y) {
  const dx = Math.max(0, Math.abs(x - 200) - 35) * Math.sign(x - 200);
  const dy = Math.max(0, Math.abs(y - 154) - 5) * -Math.sign(y - 154);
  const dz = Math.sqrt(Math.max(1, 55 * 55 - dx * dx - dy * dy));
  return new THREE.Vector3(dx, dy, dz).normalize();
}

// ---------------------------------------------------------------------------
// Geometry helpers
// ---------------------------------------------------------------------------
function roundedBox(w, h, d, r, sx = 8, sy = 8, sz = 8) {
  const g = new THREE.BoxGeometry(u(w), u(h), u(d), sx, sy, sz);
  const p = g.attributes.position, n = g.attributes.normal;
  const hx = u(w / 2 - r), hy = u(h / 2 - r), hz = u(d / 2 - r);
  const v = new THREE.Vector3(), c = new THREE.Vector3(), dir = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    c.set(THREE.MathUtils.clamp(v.x, -hx, hx), THREE.MathUtils.clamp(v.y, -hy, hy), THREE.MathUtils.clamp(v.z, -hz, hz));
    dir.subVectors(v, c);
    if (dir.lengthSq() < 1e-14) dir.set(0, 0, 1);
    dir.normalize();
    v.copy(c).addScaledVector(dir, u(r));
    p.setXYZ(i, v.x, v.y, v.z);
    n.setXYZ(i, dir.x, dir.y, dir.z);
  }
  return g;
}

function place(g, pos, rot = [0, 0, 0], scale = [1, 1, 1]) {
  const m = new THREE.Matrix4().compose(
    pos,
    new THREE.Quaternion().setFromEuler(new THREE.Euler(rot[0] * DEG, rot[1] * DEG, rot[2] * DEG)),
    new THREE.Vector3(...scale)
  );
  g.applyMatrix4(m);
  return g;
}

function capsule(r, total, cap = 6, radial = 14) {
  return new THREE.CapsuleGeometry(u(r), u(Math.max(0.01, total - 2 * r)), cap, radial);
}

// ---------------------------------------------------------------------------
// Skeleton (rest pose = 32° A-pose, identity bone orientations)
// ---------------------------------------------------------------------------
const bonesDef = [];
const boneWorld = {};
function defBone(name, parent, pos) { bonesDef.push({ name, parent }); boneWorld[name] = pos; }

const armRot = (side) => (side === 'Left' ? 32 : -32) * DEG;
const shoulderX = (side) => (side === 'Left' ? 256 : 144);
function armMatrix(side) {
  const Sp = V(shoulderX(side), 266, 2);
  return new THREE.Matrix4()
    .makeTranslation(Sp.x, Sp.y, Sp.z)
    .multiply(new THREE.Matrix4().makeRotationZ(armRot(side)))
    .multiply(new THREE.Matrix4().makeTranslation(-Sp.x, -Sp.y, -Sp.z));
}
const armPt = (side, y, z = 2, dx = 0) => V(shoulderX(side) + dx, y, z).applyMatrix4(armMatrix(side));

defBone('Root', null, V(200, 464, 0));
defBone('Hips', 'Root', V(200, 366, 0));
defBone('Spine', 'Hips', V(200, 345, 0));
defBone('Spine1', 'Spine', V(200, 318, 0));
defBone('Spine2', 'Spine1', V(200, 284, 0));
defBone('Chest', 'Spine2', V(200, 300, 0));
defBone('Neck', 'Spine2', V(200, 254, 0));
defBone('Head', 'Neck', V(200, 234, 0));
defBone('Eye_L', 'Head', V(236, 150, 20));
defBone('Eye_R', 'Head', V(164, 150, 20));
defBone('Antenna_01', 'Head', V(200, 50, 6));
defBone('Antenna_02', 'Antenna_01', V(200, 26, 6));
for (const side of ['Left', 'Right']) {
  const sgn = side === 'Left' ? 1 : -1;
  defBone(`${side}Shoulder`, 'Spine2', V(200 + sgn * 24, 262, 0));
  defBone(`${side}Arm`, `${side}Shoulder`, V(shoulderX(side), 266, 2));
  defBone(`${side}ForeArm`, `${side}Arm`, armPt(side, 326));
  defBone(`${side}Hand`, `${side}ForeArm`, armPt(side, 372));
  defBone(`${side}HandThumb1`, `${side}Hand`, armPt(side, 382, 12));
  defBone(`${side}HandThumb2`, `${side}HandThumb1`, armPt(side, 392, 16));
  const lx = side === 'Left' ? 220 : 180;
  defBone(`${side}UpLeg`, 'Hips', V(lx, 370, 1));
  defBone(`${side}Leg`, `${side}UpLeg`, V(lx, 410, 1));
  defBone(`${side}Foot`, `${side}Leg`, V(lx, 436, 4));
  defBone(`${side}ToeBase`, `${side}Foot`, V(lx, 456, 30));
}
const B = Object.fromEntries(bonesDef.map((b, i) => [b.name, i]));

function skin(g, weights) {
  const n = g.attributes.position.count;
  const si = new Uint16Array(n * 4), sw = new Float32Array(n * 4);
  const v = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    v.fromBufferAttribute(g.attributes.position, i);
    let w = typeof weights === 'function' ? weights(v) : weights;
    if (typeof w === 'string') w = [[w, 1]];
    w.forEach(([name, wt], k) => { si[i * 4 + k] = B[name]; sw[i * 4 + k] = wt; });
  }
  g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4));
  g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(sw, 4));
  return g;
}

// ---------------------------------------------------------------------------
// Parts, grouped by material
// ---------------------------------------------------------------------------
const shell = [], suit = [], visor = [], signal = [];

// Head
shell.push(skin(place(roundedBox(224, 188, 218, 86, 18, 16, 18), V(200, 142, 6)), 'Head'));
visor.push(skin(place(roundedBox(180, 120, 200, 55, 14, 10, 14), V(200, 154, 20)), 'Head'));
for (const sgn of [-1, 1]) {
  suit.push(skin(place(new THREE.CylinderGeometry(u(20), u(20), u(14), 28), V(200 + sgn * 115, 146, 6), [0, 0, 90]), 'Head'));
  signal.push(skin(place(new THREE.TorusGeometry(u(10), u(1.7), 6, 28), V(200 + sgn * 122.5, 146, 6), [0, 90, 0]), 'Head'));
}
suit.push(skin(place(new THREE.CylinderGeometry(u(2.6), u(3.2), u(28), 10), V(200, 42, 6)), 'Antenna_01'));
signal.push(skin(place(new THREE.SphereGeometry(u(8), 16, 12), V(200, 22, 6)), 'Antenna_02'));
signal.push(skin(place(capsule(3, 44, 3, 8), V(200, 199, -86), [0, 0, 90]), 'Head'));

// Neck + torso
suit.push(skin(place(new THREE.CylinderGeometry(u(16), u(17), u(30), 20), V(200, 240, 0)), 'Neck'));
{
  const g = roundedBox(106, 116, 70, 24, 10, 10, 8);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const t = (p.getY(i) + u(58)) / u(116);
    p.setX(i, p.getX(i) * THREE.MathUtils.lerp(0.9, 1.03, t));
    p.setZ(i, p.getZ(i) * THREE.MathUtils.lerp(0.94, 1.0, t));
  }
  g.computeVertexNormals();
  shell.push(skin(place(g, V(200, 308, 3)), 'Chest'));
}
suit.push(skin(place(new THREE.CylinderGeometry(u(16), u(16), u(8), 28), V(200, 300, 37), [90, 0, 0]), 'Chest'));
signal.push(skin(place(new THREE.SphereGeometry(u(8.5), 18, 12), V(200, 300, 41), [0, 0, 0], [1, 1, 0.55]), 'Chest'));
suit.push(skin(place(roundedBox(52, 66, 12, 6, 4, 6, 2), V(200, 305, -35)), 'Chest'));
for (const y of [290, 304, 318]) signal.push(skin(place(capsule(1.6, 26, 2, 6), V(200, y, -41.5), [0, 0, 90]), 'Chest'));
suit.push(skin(place(roundedBox(88, 20, 76, 9, 8, 3, 8), V(200, 364, 3)), 'Hips'));
signal.push(skin(place(capsule(1.6, 56, 2, 6), V(200, 364, 41.2), [0, 0, 90]), 'Hips'));

// Arms: modeled hanging straight down, then rotated into the 32° A-pose around the shoulder.
for (const side of ['Left', 'Right']) {
  const x = shoulderX(side);
  const M = armMatrix(side);
  const thumbDir = side === 'Left' ? -1 : 1;
  const arm = (g, bone, list) => list.push(skin(g.applyMatrix4(M), bone));
  arm(place(new THREE.SphereGeometry(u(19), 22, 16), V(x, 266, 2)), `${side}Arm`, shell);
  arm(place(capsule(11, 56), V(x, 294, 2)), `${side}Arm`, shell);
  arm(place(new THREE.SphereGeometry(u(10), 16, 12), V(x, 326, 2)), `${side}ForeArm`, suit);
  arm(place(capsule(10, 44), V(x, 350, 2)), `${side}ForeArm`, shell);
  arm(place(new THREE.TorusGeometry(u(10.6), u(2.6), 6, 22), V(x, 369, 2), [90, 0, 0]), `${side}ForeArm`, signal);
  arm(place(new THREE.SphereGeometry(u(13), 18, 14), V(x, 387, 2), [0, 0, 0], [1, 1.15, 0.85]), `${side}Hand`, suit);
  arm(place(capsule(5, 20, 3, 8), V(x + thumbDir * 3, 386, 13), [-35, 0, 0]), `${side}HandThumb1`, suit);
}

// Legs and boots
for (const side of ['Left', 'Right']) {
  const x = side === 'Left' ? 220 : 180;
  const legW = (v) => {
    const t = THREE.MathUtils.clamp(((464 - v.y / S) - 400) / 20, 0, 1); // 0 above y=400, 1 below y=420
    return [[`${side}UpLeg`, 1 - t], [`${side}Leg`, t]];
  };
  suit.push(skin(place(capsule(14, 70, 6, 14), V(x, 400, 1)), legW));
  shell.push(skin(place(new THREE.SphereGeometry(u(11), 16, 12), V(x, 410, 12), [0, 0, 0], [1, 0.82, 0.55]), `${side}Leg`));
  const bx = side === 'Left' ? 221 : 179;
  shell.push(skin(place(roundedBox(46, 34, 60, 15, 6, 5, 8), V(bx, 445, 8)), `${side}Foot`));
  suit.push(skin(place(roundedBox(48, 9, 62, 4, 4, 1, 6), V(bx, 461, 8)), `${side}Foot`));
  signal.push(skin(place(capsule(1.4, 28, 2, 6), V(bx, 446, 38.4), [0, 0, 90]), `${side}Foot`));
}

// ---------------------------------------------------------------------------
// Face: emissive eye/mouth/brow cards with morph targets (same topology per variant)
// ---------------------------------------------------------------------------
const FACE_MORPHS = ['Blink_L', 'Blink_R', 'Eyes_Happy', 'Eyes_Wide', 'Eyes_Squint', 'Brow_Raise_L', 'Brow_Raise_R', 'Mouth_Smile', 'Mouth_Open', 'Mouth_Side'];

function eyeGeo(side, variant) {
  const cx = side === 'L' ? 236 : 164;
  const g = new THREE.CapsuleGeometry(u(15), u(12), 6, 18);
  g.scale(1, 1, 0.24);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    let x = p.getX(i), y = p.getY(i);
    if (variant === `Blink_${side}`) y *= 0.12;
    if (variant === 'Eyes_Happy') { const nx = x / u(15); y = y * 0.24 + u(5) - nx * nx * u(8); }
    if (variant === 'Eyes_Wide') { x *= 1.13; y *= 1.14; }
    if (variant === 'Eyes_Squint') y *= 0.72;
    p.setXY(i, x, y);
  }
  return place(g, V(cx, 150, zv(cx, 150) + 0.4));
}

const MOUTH = {
  base: [[189, 186], [200, 193], [211, 186]],
  Mouth_Smile: [[185, 183], [200, 198], [215, 183]],
  Mouth_Open: [[184, 181], [200, 205], [216, 181]],
  Mouth_Side: [[197, 190], [206, 189], [214, 185]],
};
const OPEN_TOP = [[184, 181], [200, 187], [216, 181]];
const bez = (c, t) => {
  const a = (1 - t) * (1 - t), b = 2 * (1 - t) * t, d = t * t;
  return [a * c[0][0] + b * c[1][0] + d * c[2][0], a * c[0][1] + b * c[1][1] + d * c[2][1]];
};
const onVisor = ([x, y], lift) => V(x, y, zv(x, y) + lift);

function mouthTube(variant) {
  const c = MOUTH[variant] || MOUTH.base;
  const pts = [];
  for (let i = 0; i <= 24; i++) pts.push(onVisor(bez(c, i / 24), 1.2));
  const curve = new THREE.CatmullRomCurve3(pts);
  const tube = new THREE.TubeGeometry(curve, 24, u(2.3), 8, false);
  const ends = [0, 1].map((t) => place(new THREE.SphereGeometry(u(2.3), 8, 6), onVisor(bez(c, t), 1.2)));
  return mergeGeometries([tube, ...ends]);
}

function mouthFill(variant) {
  const N = 16;
  const top = variant === 'Mouth_Open' ? OPEN_TOP : (MOUTH[variant] || MOUTH.base);
  const bot = MOUTH[variant] || MOUTH.base;
  const pos = [], nrm = [], uv = [], idx = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    for (const [c, vv] of [[top, 1], [bot, 0]]) {
      const q = onVisor(bez(c, t), 0.6);
      pos.push(q.x, q.y, q.z); nrm.push(0, 0, 1); uv.push(t, vv);
    }
  }
  for (let i = 0; i < N; i++) {
    const a = i * 2, b = a + 1, c = a + 2, d = a + 3;
    idx.push(a, b, d, a, d, c);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  return g;
}

function browGeo(side, variant) {
  const cx = side === 'L' ? 236 : 164;
  const on = variant === `Brow_Raise_${side}`;
  const g = capsule(2, 30, 3, 6);
  g.rotateZ(Math.PI / 2 + (side === 'L' ? 16 : -16) * DEG);
  if (!on) g.scale(0.02, 0.02, 0.02);
  return place(g, V(cx, on ? 114 : 120, zv(cx, 116) + 1));
}

const faceParts = [
  { bone: 'Eye_L', build: (v) => eyeGeo('L', v) },
  { bone: 'Eye_R', build: (v) => eyeGeo('R', v) },
  { bone: 'Head', build: (v) => mouthTube(v) },
  { bone: 'Head', build: (v) => mouthFill(v) },
  { bone: 'Head', build: (v) => browGeo('L', v) },
  { bone: 'Head', build: (v) => browGeo('R', v) },
];

function cheekGeo(x, variant) {
  const k = variant === 'Cheek_Glow' ? 1.35 : 1;
  const g = new THREE.CircleGeometry(u(11), 20);
  g.scale(k, (6 / 11) * k, 1);
  const n = visorNormal(x, 184);
  g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), n));
  g.translate(...V(x, 184, zv(x, 184) + 0.5).toArray());
  return g;
}
const cheekParts = [
  { bone: 'Head', build: (v) => cheekGeo(140, v) },
  { bone: 'Head', build: (v) => cheekGeo(260, v) },
];

function morphGeometry(parts, morphs) {
  const base = mergeGeometries(parts.map((pt) => skin(pt.build('base'), pt.bone)));
  base.morphAttributes.position = morphs.map((m) => {
    const arrays = parts.map((pt) => pt.build(m).attributes.position.array);
    const out = new Float32Array(arrays.reduce((s, a) => s + a.length, 0));
    let o = 0;
    for (const a of arrays) { out.set(a, o); o += a.length; }
    if (out.length !== base.attributes.position.array.length) throw new Error(`morph ${m}: vertex count mismatch`);
    return new THREE.Float32BufferAttribute(out, 3);
  });
  return base;
}

// ---------------------------------------------------------------------------
// Materials (4 core PBR + cheek tint)
// ---------------------------------------------------------------------------
const mats = {
  shell: new THREE.MeshPhysicalMaterial({ name: 'M_Shell', color: '#F4F6FA', roughness: 0.28, metalness: 0, clearcoat: 0.6, clearcoatRoughness: 0.12 }),
  suit: new THREE.MeshStandardMaterial({ name: 'M_Suit', color: '#2A3142', roughness: 0.55, metalness: 0.1 }),
  visor: new THREE.MeshPhysicalMaterial({ name: 'M_Visor', color: '#070A12', roughness: 0.06, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.03 }),
  signal: new THREE.MeshStandardMaterial({ name: 'M_Signal', color: '#5CF2E3', emissive: '#5CF2E3', emissiveIntensity: 1.3, roughness: 0.3 }),
  cheek: new THREE.MeshStandardMaterial({ name: 'M_Cheek', color: '#B3A8FF', emissive: '#B3A8FF', emissiveIntensity: 0.45, roughness: 0.4 }),
};

// ---------------------------------------------------------------------------
// Assemble skinned meshes
// ---------------------------------------------------------------------------
const bones = bonesDef.map(({ name }) => { const b = new THREE.Bone(); b.name = name; return b; });
bonesDef.forEach(({ name, parent }, i) => {
  const wp = boneWorld[name];
  if (parent) {
    bones[B[parent]].add(bones[i]);
    bones[i].position.copy(wp).sub(boneWorld[parent]);
  } else {
    bones[i].position.copy(wp);
  }
});
const root = bones[B.Root];
const nova = new THREE.Group();
nova.name = 'Nova';
nova.add(root);
nova.updateMatrixWorld(true);
const skeleton = new THREE.Skeleton(bones);

function addMesh(name, geo, mat) {
  const m = new THREE.SkinnedMesh(geo, mat);
  m.name = name;
  nova.add(m);
  m.bind(skeleton, new THREE.Matrix4());
  if (geo.morphAttributes.position) m.updateMorphTargets();
  return m;
}

const faceGeo = morphGeometry(faceParts, FACE_MORPHS);
const cheekGeoM = morphGeometry(cheekParts, ['Cheek_Glow']);
const meshes = [
  addMesh('Nova_Body', mergeGeometries(shell), mats.shell),
  addMesh('Nova_Suit', mergeGeometries(suit), mats.suit),
  addMesh('Nova_Visor', mergeGeometries(visor), mats.visor),
  addMesh('Nova_Signal', mergeGeometries(signal), mats.signal),
  addMesh('Nova_Face', faceGeo, mats.signal),
  addMesh('Nova_Cheeks', cheekGeoM, mats.cheek),
];
const faceMesh = meshes[4];
faceMesh.morphTargetDictionary = Object.fromEntries(FACE_MORPHS.map((m, i) => [m, i]));
meshes[5].morphTargetDictionary = { Cheek_Glow: 0 };

// ---------------------------------------------------------------------------
// Animation clips (sampled at 30 fps)
// ---------------------------------------------------------------------------
const FPS = 30;
const smooth = (t) => { t = THREE.MathUtils.clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const env = (t, inEnd, outStart, dur) => smooth(t / inEnd) * (1 - smooth((t - outStart) / (dur - outStart)));
const mix = (a, b, k) => a.map((v, i) => v + (b[i] - v) * k);

const IDLE = {
  RightArm: [-4, 0, 18], RightForeArm: [0, 0, 6],
  LeftArm: [-4, 0, -18], LeftForeArm: [0, 0, -6],
  Head: [0, 0, 0], Neck: [0, 0, 0], Spine2: [0, 0, 0], Spine1: [0, 0, 0],
  Eye_L: [0, 0, 0], Eye_R: [0, 0, 0],
};
// Arm pose from directions: where the upper arm points, then where the forearm points (world space).
// Returns [armEulerDeg, foreArmEulerDeg] relative to the A-pose rest.
function aim(side, elbowDir, handDir) {
  const rest = new THREE.Vector3((side === 'Left' ? 1 : -1) * Math.sin(32 * DEG), -Math.cos(32 * DEG), 0);
  const qA = new THREE.Quaternion().setFromUnitVectors(rest, new THREE.Vector3(...elbowDir).normalize());
  const local = new THREE.Vector3(...handDir).normalize().applyQuaternion(qA.clone().invert());
  const qF = new THREE.Quaternion().setFromUnitVectors(rest, local);
  const deg = (q) => new THREE.Euler().setFromQuaternion(q).toArray().slice(0, 3).map((r) => r / DEG);
  return [deg(qA), deg(qF)];
}
const POSE = {
  thinkL: aim('Left', [-0.2, -0.75, 0.63], [-0.47, 0.81, 0.33]),
  waveR: aim('Right', [-0.95, 0.2, 0.25], [-0.25, 1, 0.15]),
  greetR: aim('Right', [-0.75, -0.55, 0.35], [-0.45, 0.6, 0.65]),
  greetL: aim('Left', [0.75, -0.55, 0.35], [0.45, 0.6, 0.65]),
  excitedR: aim('Right', [-0.8, 0.55, 0.2], [-0.5, 0.85, 0.15]),
  excitedL: aim('Left', [0.8, 0.55, 0.2], [0.5, 0.85, 0.15]),
};
const add = (a, b) => a.map((v, i) => v + b[i]);
// Blend two Euler poses (degrees) along the shortest rotation; returns a quaternion [x, y, z, w].
const toQ = (e) => new THREE.Quaternion().setFromEuler(new THREE.Euler(e[0] * DEG, e[1] * DEG, e[2] * DEG));
const slerp = (a, b, k) => toQ(a).slerp(toQ(b), k).toArray();

const faceZero = () => Object.fromEntries(FACE_MORPHS.map((m) => [m, 0]));

// Every body clip starts from the full idle pose so crossfades fully replace each other.
function body(extra = {}) {
  return {
    r: { ...structuredClone(IDLE), ...extra.r },
    p: { Hips: [0, 0, 0], Spine2: [0, 0, 0], ...extra.p },
    s: { Chest: [1, 1, 1], ...extra.s },
    m: { ...faceZero(), Mouth_Smile: 0.4, ...extra.m },
    c: { Cheek_Glow: 0, ...extra.c },
  };
}

const clips = {
  Idle_Breathe: { dur: 4, f: (t) => {
    const ph = Math.sin((2 * Math.PI * t) / 4), b = (1 - Math.cos((2 * Math.PI * t) / 4)) / 2;
    return body({
      r: { RightArm: [-4, 0, 18 + 1.5 * ph], LeftArm: [-4, 0, -18 - 1.5 * ph], Head: [-1.5 * ph, 0, 0], Neck: [0.8 * ph, 0, 0], Spine2: [0.6 * ph, 0, 0] },
      p: { Spine2: [0, u(1.2) * b, 0] },
      s: { Chest: [1 + 0.012 * b, 1 + 0.025 * b, 1 + 0.02 * b] },
    });
  } },
  Blink: { dur: 0.2, f: (t) => {
    const k = t < 0.07 ? 1 - 0.9 * (t / 0.07) : 0.1 + 0.9 * Math.min(1, (t - 0.07) / 0.13);
    return { s: { Eye_L: [1, k, 1], Eye_R: [1, k, 1] } };
  } },
  Look_Around: { dur: 6, f: (t) => {
    const keys = [[0, 0], [1.0, 28], [2.2, 28], [3.4, -28], [4.6, -28], [6, 0]];
    let yaw = 0;
    for (let i = 0; i < keys.length - 1; i++) {
      const [t0, a0] = keys[i], [t1, a1] = keys[i + 1];
      if (t >= t0 && t <= t1) yaw = a0 + (a1 - a0) * smooth((t - t0) / (t1 - t0));
    }
    return body({ r: { Head: [-3, yaw, 0], Neck: [0, yaw * 0.3, 0], Eye_L: [0, yaw * 0.5, 0], Eye_R: [0, yaw * 0.5, 0] }, m: { Mouth_Smile: 0.25 } });
  } },
  Look_At_Camera: { dur: 0.6, f: (t) => body({ m: { Mouth_Smile: 0.4 + 0.6 * smooth(t / 0.6) } }) },
  Wave: { dur: 1.8, f: (t) => {
    const a = env(t, 0.3, 1.5, 1.8);
    const osc = 17 * Math.sin(2 * Math.PI * 1.7 * Math.max(0, t - 0.3)) * a;
    return body({
      r: { RightArm: slerp(IDLE.RightArm, POSE.waveR[0], a), RightForeArm: slerp(IDLE.RightForeArm, add(POSE.waveR[1], [0, 0, osc]), a), Head: [0, 0, 5 * a] },
      m: { Mouth_Smile: 0.4 + 0.6 * a },
    });
  } },
  Think: { dur: 2.4, f: (t) => {
    const bob = Math.sin((2 * Math.PI * t) / 2.4);
    return body({
      r: { LeftArm: POSE.thinkL[0], LeftForeArm: POSE.thinkL[1], Head: [-8 + 1.5 * bob, 0, -6], Neck: [-2, 0, 0], Eye_L: [-12, 10, 0], Eye_R: [-12, 10, 0] },
      m: { Mouth_Smile: 0, Brow_Raise_L: 1, Eyes_Squint: 0.35, Mouth_Side: 1 },
    });
  } },
  Greet: { dur: 2.0, f: (t) => {
    const a = env(t, 0.4, 1.6, 2.0);
    const bow = t > 0.5 && t < 1.5 ? Math.sin((Math.PI * (t - 0.5)) / 1.0) : 0;
    return body({
      r: {
        RightArm: slerp(IDLE.RightArm, POSE.greetR[0], a), RightForeArm: slerp(IDLE.RightForeArm, POSE.greetR[1], a),
        LeftArm: slerp(IDLE.LeftArm, POSE.greetL[0], a), LeftForeArm: slerp(IDLE.LeftForeArm, POSE.greetL[1], a),
        Spine1: [8 * bow, 0, 0], Head: [6 * bow, 0, 0],
      },
      m: { Mouth_Smile: 0.4 + 0.6 * a, Eyes_Happy: a },
    });
  } },
  Excited: { dur: 1.6, f: (t) => {
    const a = env(t, 0.25, 1.3, 1.6);
    const shake = 8 * Math.sin(2 * Math.PI * 4 * t) * a;
    const hop = t > 0.2 && t < 1.3 ? Math.max(0, Math.sin((2 * Math.PI * (t - 0.2)) / 0.55)) : 0;
    return body({
      r: {
        RightArm: slerp(IDLE.RightArm, POSE.excitedR[0], a), RightForeArm: slerp(IDLE.RightForeArm, add(POSE.excitedR[1], [0, 0, shake]), a),
        LeftArm: slerp(IDLE.LeftArm, POSE.excitedL[0], a), LeftForeArm: slerp(IDLE.LeftForeArm, add(POSE.excitedL[1], [0, 0, -shake]), a),
        Head: [-5 * a, 0, 0],
      },
      p: { Hips: [0, 0.05 * hop, 0] },
      m: { Mouth_Smile: 0.4 * (1 - a), Eyes_Wide: a, Mouth_Open: a },
      c: { Cheek_Glow: a },
    });
  } },
  Nod: { dur: 0.9, f: (t) => {
    const x = t < 0.45 ? 12 * Math.sin((Math.PI * t) / 0.45) : 8 * Math.sin((Math.PI * (t - 0.45)) / 0.45);
    return body({ r: { Head: [x, 0, 0], Neck: [x * 0.3, 0, 0] }, m: { Mouth_Smile: 0.7 } });
  } },
  Float: { dur: 4, f: (t) => ({
    p: { Root: [0, 0.02 * Math.sin((2 * Math.PI * t) / 4), 0] },
    r: { Root: [0, 0, 1.2 * Math.sin((2 * Math.PI * t) / 4 + 1)] },
  }) },
};

function buildClip(name, { dur, f }) {
  const n = Math.round(dur * FPS);
  const times = Array.from({ length: n + 1 }, (_, i) => Math.min(dur, i / FPS));
  const samples = times.map((t) => f(t));
  const tracks = [];
  const keys = (field) => [...new Set(samples.flatMap((s) => Object.keys(s[field] || {})))];
  const q = new THREE.Quaternion(), e = new THREE.Euler();
  for (const bone of keys('r')) {
    const vals = [];
    for (const s of samples) {
      const r = s.r[bone];
      if (r.length === 4) q.fromArray(r);
      else q.setFromEuler(e.set(r[0] * DEG, r[1] * DEG, r[2] * DEG));
      vals.push(q.x, q.y, q.z, q.w);
    }
    tracks.push(new THREE.QuaternionKeyframeTrack(`${bone}.quaternion`, times, vals));
  }
  for (const bone of keys('p')) {
    const rest = bones[B[bone]].position;
    tracks.push(new THREE.VectorKeyframeTrack(`${bone}.position`, times, samples.flatMap((s) => {
      const d = s.p[bone];
      return [rest.x + d[0], rest.y + d[1], rest.z + d[2]];
    })));
  }
  for (const bone of keys('s')) tracks.push(new THREE.VectorKeyframeTrack(`${bone}.scale`, times, samples.flatMap((s) => s.s[bone])));
  for (const m of keys('m')) tracks.push(new THREE.NumberKeyframeTrack(`Nova_Face.morphTargetInfluences[${m}]`, times, samples.map((s) => s.m[m])));
  for (const m of keys('c')) tracks.push(new THREE.NumberKeyframeTrack(`Nova_Cheeks.morphTargetInfluences[${m}]`, times, samples.map((s) => s.c[m])));
  return new THREE.AnimationClip(name, dur, tracks);
}
const animations = Object.entries(clips).map(([name, c]) => buildClip(name, c));

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------
let tris = 0;
for (const m of meshes) tris += m.geometry.index.count / 3;
console.log(`meshes: ${meshes.length}  bones: ${bones.length}  triangles: ${tris}  morphs: ${FACE_MORPHS.length + 1}  clips: ${animations.map((a) => a.name).join(', ')}`);

new GLTFExporter().parse(
  nova,
  (glb) => {
    fs.writeFileSync('nova.glb', Buffer.from(glb));
    console.log(`wrote nova.glb (${(glb.byteLength / 1024).toFixed(0)} KB)`);
  },
  (err) => { console.error(err); process.exit(1); },
  { binary: true, animations }
);
