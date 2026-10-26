// Builds the ReelSense 3D UI kit ("Daylight Instrument" style) into frontend/public/models/ui/*.glb.
// Run from this folder: node build.mjs
//
// Style: layered machined plates. An aluminium tray, a porcelain or enamel cap on top, and crisp
// small bevels, like a precision hardware control. The colours are the site's own tokens from
// frontend/src/app/globals.css. Teal (Signal) appears only where the site marks AI activity.
// Units: 1 unit = 100 CSS px. Every model faces +Z, is centred on the origin and has no text,
// since labels stay in HTML for accessibility and translation.
import * as THREE from '../frontend/node_modules/three/build/three.module.js';
import { GLTFExporter } from '../frontend/node_modules/three/examples/jsm/exporters/GLTFExporter.js';
import { SVGLoader } from '../frontend/node_modules/three/examples/jsm/loaders/SVGLoader.js';
import { mergeGeometries, mergeVertices } from '../frontend/node_modules/three/examples/jsm/utils/BufferGeometryUtils.js';
import fs from 'node:fs';
import path from 'node:path';

const OUT = path.resolve('../frontend/public/models/ui');
const ICON_SOURCE = path.resolve('../frontend/src/components/ui/Icon.tsx');
fs.mkdirSync(OUT, { recursive: true });

// ---------------------------------------------------------------------------
// Node shims: GLTFExporter needs FileReader, SVGLoader needs a DOMParser.
// ---------------------------------------------------------------------------
globalThis.FileReader = class {
  readAsArrayBuffer(blob) { blob.arrayBuffer().then((b) => { this.result = b; this.onloadend?.(); }); }
  readAsDataURL(blob) {
    blob.arrayBuffer().then((b) => { this.result = `data:${blob.type};base64,${Buffer.from(b).toString('base64')}`; this.onloadend?.(); });
  }
};
// A tiny DOM parser for the flat SVG markup used here: one <svg> root holding rect, circle and path elements.
globalThis.DOMParser = class {
  parseFromString(text) {
    const el = (nodeName, attrs) => ({
      nodeType: 1, nodeName, childNodes: [],
      getAttribute: (n) => (n in attrs ? attrs[n] : null),
      hasAttribute: (n) => n in attrs,
      getAttributeNS: () => null,
    });
    const attrsOf = (s) => Object.fromEntries([...s.matchAll(/([\w:-]+)="([^"]*)"/g)].map((m) => [m[1], m[2]]));
    const rootMatch = text.match(/<svg([^>]*)>/);
    const root = el('svg', attrsOf(rootMatch[1]));
    for (const m of text.matchAll(/<(rect|circle|path|line|polyline|ellipse)\b([^>]*?)\/?>/g)) root.childNodes.push(el(m[1], attrsOf(m[2])));
    return { documentElement: root };
  }
};

// ---------------------------------------------------------------------------
// Materials: site tokens (globals.css), PBR, all opaque
// ---------------------------------------------------------------------------
const M = {
  porcelain: new THREE.MeshPhysicalMaterial({ name: 'M_Porcelain', color: '#F7F8FC', roughness: 0.42, clearcoat: 0.35, clearcoatRoughness: 0.3 }),
  mist: new THREE.MeshStandardMaterial({ name: 'M_Mist', color: '#E3E5EE', roughness: 0.6 }),
  alu: new THREE.MeshStandardMaterial({ name: 'M_Aluminium', color: '#C9CDD9', roughness: 0.3, metalness: 1 }),
  ink: new THREE.MeshStandardMaterial({ name: 'M_Ink', color: '#161826', roughness: 0.45, metalness: 0.2 }),
  cobalt: new THREE.MeshPhysicalMaterial({ name: 'M_Cobalt', color: '#2B40CC', roughness: 0.36, clearcoat: 0.45, clearcoatRoughness: 0.2 }),
  cobaltGlow: new THREE.MeshStandardMaterial({ name: 'M_CobaltGlow', color: '#5265E8', emissive: '#5265E8', emissiveIntensity: 1.2, roughness: 0.4 }),
  signal: new THREE.MeshPhysicalMaterial({ name: 'M_Signal', color: '#08736C', roughness: 0.36, clearcoat: 0.45, clearcoatRoughness: 0.15 }),
  signalGlow: new THREE.MeshStandardMaterial({ name: 'M_SignalGlow', color: '#12B5A8', emissive: '#16C9BA', emissiveIntensity: 1.3, roughness: 0.35 }),
  signalSoft: new THREE.MeshStandardMaterial({ name: 'M_SignalSoft', color: '#BFE6E2', roughness: 0.55 }),
  violet: new THREE.MeshPhysicalMaterial({ name: 'M_Violet', color: '#5E3FD6', roughness: 0.36, clearcoat: 0.45, clearcoatRoughness: 0.15 }),
  warm: new THREE.MeshPhysicalMaterial({ name: 'M_Warm', color: '#BF5A2A', roughness: 0.32, clearcoat: 0.5 }),
  success: new THREE.MeshPhysicalMaterial({ name: 'M_Success', color: '#15875A', roughness: 0.32, clearcoat: 0.5 }),
  error: new THREE.MeshPhysicalMaterial({ name: 'M_Error', color: '#BE3337', roughness: 0.32, clearcoat: 0.5 }),
  screen: new THREE.MeshStandardMaterial({ name: 'M_Screen', color: '#0E1018', roughness: 0.18 }),
};

// ---------------------------------------------------------------------------
// Geometry helpers
// ---------------------------------------------------------------------------
function rrShape(w, h, r, ShapeClass = THREE.Shape) {
  r = Math.max(0.0001, Math.min(r, w / 2, h / 2));
  const s = new ShapeClass(), x = -w / 2, y = -h / 2;
  s.moveTo(x + r, y);
  s.lineTo(x + w - r, y); s.absarc(x + w - r, y + r, r, -Math.PI / 2, 0);
  s.lineTo(x + w, y + h - r); s.absarc(x + w - r, y + h - r, r, 0, Math.PI / 2);
  s.lineTo(x + r, y + h); s.absarc(x + r, y + h - r, r, Math.PI / 2, Math.PI);
  s.lineTo(x, y + r); s.absarc(x + r, y + r, r, Math.PI, Math.PI * 1.5);
  return s;
}

// A bevelled rounded plate, centred, thickness along Z. `hole` = [w, h, r] cuts a window.
function slab(w, h, r, depth, { bevel = 0.012, hole = null, curve } = {}) {
  // Corner detail scales with the corner radius, so small parts stay light.
  curve ??= THREE.MathUtils.clamp(Math.round(r * 30), 3, 10);
  const b = Math.min(bevel, depth / 3, w / 6, h / 6);
  const s = rrShape(w - 2 * b, h - 2 * b, r - b);
  if (hole) s.holes.push(rrShape(hole[0] + 2 * b, hole[1] + 2 * b, hole[2] + b, THREE.Path));
  const d = Math.max(0.0005, depth - 2 * b);
  const g = new THREE.ExtrudeGeometry(s, { depth: d, bevelEnabled: b > 0, bevelThickness: b, bevelSize: b, bevelSegments: 3, curveSegments: curve });
  g.translate(0, 0, -d / 2);
  g.normalizeNormals();
  return g;
}
const disc = (r, depth, opts) => slab(2 * r, 2 * r, r, depth, { curve: THREE.MathUtils.clamp(Math.round(r * 24), 5, 12), ...opts });
const leftAnchored = (g, w) => g.translate(w / 2, 0, 0);

function mesh(geo, mat, name, pos = [0, 0, 0], rot = [0, 0, 0]) {
  if (!geo.index) { geo.deleteAttribute('uv'); geo = mergeVertices(geo, 1e-5); }
  const m = new THREE.Mesh(geo, mat);
  m.name = name;
  m.position.set(...pos);
  m.rotation.set(...rot.map((d) => (d * Math.PI) / 180));
  return m;
}
function group(name, pos = [0, 0, 0], children = []) {
  const g = new THREE.Group();
  g.name = name;
  g.position.set(...pos);
  children.forEach((c) => g.add(c));
  return g;
}

// ---------------------------------------------------------------------------
// Icons: the site's own Icon.tsx strokes, swept into round tubes
// ---------------------------------------------------------------------------
function readIcons() {
  const src = fs.readFileSync(ICON_SOURCE, 'utf8');
  const body = src.slice(src.indexOf('const paths'), src.indexOf('\n};', src.indexOf('const paths')));
  const icons = {};
  const re = /^ {2}("?[\w-]+"?):\s*([\s\S]*?)(?=^ {2}"?[\w-]+"?:|$(?![\s\S]))/gm;
  for (const m of body.matchAll(re)) {
    const name = m[1].replaceAll('"', '');
    const inner = m[2].replace(/<>|<\/>/g, '').replace(/^\(|\),?\s*$/gm, '').replace(/,\s*$/, '').trim();
    if (inner.includes('<')) icons[name] = inner;
  }
  return icons;
}
const ICONS = readIcons();

function strokeGeometry(svgInner, { viewBox = 20, size = 1, radius = 0.05 } = {}) {
  const k = size / viewBox;
  const svg = `<svg viewBox="0 0 ${viewBox} ${viewBox}" fill="none" stroke="#000">${svgInner.replaceAll('currentColor', '#000')}</svg>`;
  const parts = [];
  const P = (v) => new THREE.Vector3((v.x - viewBox / 2) * k, -(v.y - viewBox / 2) * k, 0);
  const ball = (p, r = radius) => { const g = new THREE.SphereGeometry(r, 8, 6); g.translate(p.x, p.y, p.z); parts.push(g); };
  for (const p of new SVGLoader().parse(svg).paths) {
    const filled = p.userData.style.fill && p.userData.style.fill !== 'none' && p.userData.style.stroke === 'none';
    for (const sub of p.subPaths) {
      let pts = sub.getPoints(10).map(P).filter((v, i, a) => i === 0 || v.distanceTo(a[i - 1]) > 1e-4);
      if (filled) {
        const box = new THREE.Box3().setFromPoints(pts);
        ball(box.getCenter(new THREE.Vector3()), Math.max(radius * 1.1, (box.max.x - box.min.x) * 0.6));
        continue;
      }
      if (pts.length === 1) { ball(pts[0]); continue; }
      const closed = sub.autoClose || pts[0].distanceTo(pts[pts.length - 1]) < 1e-3;
      if (closed && pts[0].distanceTo(pts[pts.length - 1]) > 1e-3) pts.push(pts[0].clone());
      // Split at sharp corners so each run is a smooth tube; round joins come from spheres.
      const runs = [[pts[0]]];
      for (let i = 1; i < pts.length; i++) {
        runs[runs.length - 1].push(pts[i]);
        if (i < pts.length - 1) {
          const a = pts[i].clone().sub(pts[i - 1]).normalize(), b = pts[i + 1].clone().sub(pts[i]).normalize();
          if (a.angleTo(b) > 0.6) runs.push([pts[i]]);
        }
      }
      for (const run of runs) {
        if (run.length === 2) {
          const [a, b] = run, len = a.distanceTo(b);
          const g = new THREE.CylinderGeometry(radius, radius, len, 8, 1, true);
          g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize()));
          g.translate(...a.clone().add(b).multiplyScalar(0.5).toArray());
          parts.push(g);
        } else {
          const curve = new THREE.CatmullRomCurve3(run, false, 'centripetal');
          parts.push(new THREE.TubeGeometry(curve, Math.max(4, run.length), radius, 8, false));
        }
        ball(run[0]); ball(run[run.length - 1]);
      }
    }
  }
  return mergeGeometries(parts);
}
const iconGeo = (name, size = 1, radius = 0.05) => strokeGeometry(ICONS[name], { size, radius });

// ---------------------------------------------------------------------------
// Animation: clips sampled from f(t) -> { node: { p: offset[3], s: scale[3], r: eulerDeg[3] } }
// ---------------------------------------------------------------------------
const FPS = 30;
const smooth = (t) => { t = THREE.MathUtils.clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const back = (t) => { t = THREE.MathUtils.clamp(t, 0, 1); const c = 1.7; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2; };
const pulse = (t, start, dur) => (t < start || t > start + dur ? 0 : Math.sin((Math.PI * (t - start)) / dur));

function clip(root, name, dur, f) {
  const n = Math.round(dur * FPS);
  const times = Array.from({ length: n + 1 }, (_, i) => Math.min(dur, i / FPS));
  const samples = times.map(f);
  const nodes = [...new Set(samples.flatMap((s) => Object.keys(s)))];
  const tracks = [];
  const q = new THREE.Quaternion(), e = new THREE.Euler();
  for (const node of nodes) {
    const obj = root.getObjectByName(node);
    if (!obj) throw new Error(`${name}: no node ${node}`);
    const has = (k) => samples.some((s) => s[node]?.[k]);
    if (has('p')) tracks.push(new THREE.VectorKeyframeTrack(`${node}.position`, times, samples.flatMap((s) => {
      const d = s[node]?.p || [0, 0, 0];
      return [obj.position.x + d[0], obj.position.y + d[1], obj.position.z + d[2]];
    })));
    if (has('s')) tracks.push(new THREE.VectorKeyframeTrack(`${node}.scale`, times, samples.flatMap((s) => s[node]?.s || obj.scale.toArray())));
    if (has('r')) tracks.push(new THREE.QuaternionKeyframeTrack(`${node}.quaternion`, times, samples.flatMap((s) => {
      const r = s[node]?.r || [0, 0, 0];
      return q.setFromEuler(e.set(...r.map((d) => (d * Math.PI) / 180))).toArray();
    })));
  }
  return new THREE.AnimationClip(name, dur, tracks);
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------
const report = [];
async function save(file, root, animations = []) {
  root.updateMatrixWorld(true);
  let tris = 0;
  root.traverse((o) => { if (o.isMesh) tris += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; });
  const glb = await new GLTFExporter().parseAsync(root, { binary: true, animations });
  fs.writeFileSync(path.join(OUT, file), Buffer.from(glb));
  report.push({ file, tris, kb: Math.round(glb.byteLength / 1024), clips: animations.map((a) => a.name) });
}

// ===========================================================================
// 1-3. Buttons: primary (cobalt), secondary (outline), AI (signal)
// ===========================================================================
function button(kind) {
  const W = 2.2, H = 0.56;
  const root = group(`Button_${kind}`);
  root.add(mesh(slab(W + 0.16, H + 0.16, (H + 0.16) / 2, 0.08), M.alu, 'Tray', [0, 0, 0]));
  root.add(mesh(slab(W + 0.06, H + 0.06, (H + 0.06) / 2, 0.02, { bevel: 0.004 }), M.ink, 'Well', [0, 0, 0.045]));
  const halo = mesh(slab(W + 0.42, H + 0.42, (H + 0.42) / 2, 0.02, { hole: [W + 0.3, H + 0.3, (H + 0.3) / 2], bevel: 0.004 }),
    kind === 'AI' ? M.signalGlow : M.cobaltGlow, 'Halo', [0, 0, 0.02]);
  halo.scale.set(0.001, 0.001, 0.001);
  root.add(halo);
  const cap = group('Cap', [0, 0, 0.1]);
  const capMat = kind === 'Primary' ? M.cobalt : kind === 'AI' ? M.signal : M.porcelain;
  cap.add(mesh(slab(W, H, H / 2, 0.1), capMat, 'CapBody'));
  if (kind === 'Secondary') cap.add(mesh(slab(W, H, H / 2, 0.104, { hole: [W - 0.06, H - 0.06, (H - 0.06) / 2], bevel: 0.006 }), M.cobalt, 'CapRim'));
  if (kind === 'AI') {
    const dot = mesh(new THREE.SphereGeometry(0.055, 16, 12), M.signalGlow, 'LiveDot', [-W / 2 + 0.26, 0, 0.055]);
    dot.scale.set(1, 1, 0.5);
    cap.add(dot);
  }
  root.add(cap);
  const clips = [
    clip(root, 'Hover', 0.25, (t) => { const k = smooth(t / 0.25); return { Cap: { p: [0, 0, 0.035 * k] }, Halo: { s: [Math.max(0.001, k), Math.max(0.001, k), Math.max(0.001, k)] } }; }),
    clip(root, 'Press', 0.32, (t) => { const k = t < 0.1 ? smooth(t / 0.1) : 1 - smooth((t - 0.1) / 0.22); return { Cap: { p: [0, 0, -0.045 * k] } }; }),
  ];
  if (kind === 'AI') clips.push(clip(root, 'Thinking', 1.4, (t) => {
    const k = 0.5 - 0.5 * Math.cos((2 * Math.PI * t) / 1.4);
    return { LiveDot: { s: [1 + 0.5 * k, 1 + 0.5 * k, 0.5 + 0.25 * k] }, Halo: { s: [0.97 + 0.05 * k, 0.97 + 0.08 * k, 1] } };
  }));
  return { root, clips };
}

// ===========================================================================
// 4. Icon keys: the workspace mode bar and player controls as physical keys
// ===========================================================================
const TONE = { chat: 'signal', search: 'signal', quiz: 'violet', flashcard: 'violet', check: 'success', alert: 'error', 'file-warning': 'error', 'server-off': 'error', 'wifi-off': 'error' };
const toneMat = (name) => M[TONE[name] || 'cobalt'];

function iconKeys() {
  const names = ['video', 'chapters', 'transcript', 'summary', 'translate', 'chat', 'search', 'quiz', 'flashcard', 'upload', 'play', 'pause', 'skip-back', 'skip-forward', 'volume', 'fullscreen', 'download', 'refresh'];
  const root = group('IconKeys');
  const cols = 6, gap = 1.12;
  const icons = {};
  names.forEach((name, i) => {
    const x = ((i % cols) - (cols - 1) / 2) * gap, y = -(Math.floor(i / cols) - 1) * gap;
    const key = group(`Key_${name}`, [x, y, 0]);
    key.add(mesh(slab(0.92, 0.92, 0.2, 0.07), M.alu, `Base_${name}`));
    const cap = group(`Cap_${name}`, [0, 0, 0.085]);
    cap.add(mesh(slab(0.82, 0.82, 0.16, 0.09), M.porcelain, `CapBody_${name}`));
    icons[name] ??= iconGeo(name, 0.52, 0.03);
    cap.add(mesh(icons[name], toneMat(name), `Icon_${name}`, [0, 0, 0.05]));
    key.add(cap);
    root.add(key);
  });
  const clips = [clip(root, 'Ripple', 2.6, (t) => Object.fromEntries(names.map((n, i) => {
    const col = i % cols, row = Math.floor(i / cols);
    return [`Cap_${n}`, { p: [0, 0, -0.05 * pulse(t, 0.12 * (col + row), 0.4)] }];
  })))];
  return { root, clips };
}

// ===========================================================================
// 5. Icons: every Icon.tsx glyph as a free-floating extruded icon (Icon_<name>)
// ===========================================================================
function iconSet() {
  const root = group('Icons');
  const names = Object.keys(ICONS).filter((n) => n !== 'spinner');
  const cols = 9;
  names.forEach((name, i) => {
    const x = ((i % cols) - (cols - 1) / 2) * 1.3, y = -(Math.floor(i / cols) - 2) * 1.3;
    root.add(mesh(iconGeo(name, 1, 0.05), toneMat(name), `Icon_${name}`, [x, y, 0]));
  });
  return { root, clips: [] };
}

// ===========================================================================
// 6. Video frame: cinematic bezel, swappable Screen, floating control dock
// ===========================================================================
function videoFrame() {
  const SW = 6.4, SH = 3.6;
  const root = group('VideoFrame');
  const body = group('FrameBody');
  body.add(mesh(slab(SW + 0.44, SH + 0.44, 0.28, 0.08), M.porcelain, 'BackPlate', [0, 0, -0.09]));
  body.add(mesh(slab(SW + 0.4, SH + 0.4, 0.28, 0.16, { hole: [SW, SH, 0.14] }), M.alu, 'Bezel'));
  body.add(mesh(slab(SW + 0.06, SH + 0.06, 0.16, 0.02, { hole: [SW - 0.02, SH - 0.02, 0.14], bevel: 0.004 }), M.ink, 'InnerLip', [0, 0, 0.07]));
  // Screen: a plain 0..1 UV plane. Assign a VideoTexture to material "M_Screen" (mesh "Screen").
  body.add(mesh(new THREE.PlaneGeometry(SW + 0.1, SH + 0.1), M.screen, 'Screen', [0, 0, -0.02]));
  // AI status chip, top-left
  const chip = group('AIChip', [-SW / 2 + 0.75, SH / 2 - 0.35, 0.12]);
  chip.add(mesh(slab(1.1, 0.3, 0.15, 0.06), M.signal, 'AIChipBody'));
  chip.add(mesh(new THREE.SphereGeometry(0.045, 14, 10), M.signalGlow, 'AIChipDot', [-0.38, 0, 0.035]));
  body.add(chip);
  root.add(body);

  // Control dock, floating in front of the lower edge
  const dock = group('Dock', [0, -SH / 2 + 0.42, 0.28]);
  dock.add(mesh(slab(5.8, 0.62, 0.31, 0.08), M.porcelain, 'DockBody'));
  const play = group('PlayKey', [-2.55, 0, 0.07]);
  play.add(mesh(disc(0.23, 0.08), M.cobalt, 'PlayKeyBody'));
  play.add(mesh(iconGeo('play', 0.28, 0.022), M.porcelain, 'PlayIcon', [0.015, 0, 0.045]));
  dock.add(play);
  dock.add(mesh(iconGeo('skip-back', 0.26, 0.018), M.ink, 'SkipBack', [-2.08, 0, 0.05]));
  dock.add(mesh(iconGeo('skip-forward', 0.26, 0.018), M.ink, 'SkipForward', [-1.68, 0, 0.05]));
  const TW = 3.1, TX = -1.35;
  dock.add(mesh(leftAnchored(slab(TW, 0.07, 0.035, 0.03, { bevel: 0.005 }), TW), M.mist, 'Track', [TX, 0, 0.05]));
  const progress = mesh(leftAnchored(slab(TW, 0.07, 0.035, 0.036, { bevel: 0.005 }), TW), M.cobalt, 'Progress', [TX, 0, 0.052]);
  progress.scale.set(0.001, 1, 1);
  dock.add(progress);
  [0.22, 0.47, 0.7].forEach((f, i) => dock.add(mesh(slab(0.02, 0.14, 0.01, 0.04, { bevel: 0.003 }), M.porcelain, `ChapterTick_${i}`, [TX + f * TW, 0, 0.056])));
  [0.34, 0.81].forEach((f, i) => dock.add(mesh(new THREE.SphereGeometry(0.05, 14, 10), M.signalGlow, `EvidencePin_${i}`, [TX + f * TW, 0.12, 0.06])));
  dock.add(mesh(disc(0.075, 0.06), M.porcelain, 'Playhead', [TX, 0, 0.07]));
  dock.add(mesh(iconGeo('volume', 0.26, 0.018), M.ink, 'Volume', [2.2, 0, 0.05]));
  dock.add(mesh(iconGeo('fullscreen', 0.24, 0.018), M.ink, 'Fullscreen', [2.58, 0, 0.05]));
  root.add(dock);

  const clips = [
    clip(root, 'Playback', 10, (t) => { const k = t / 10; return { Progress: { s: [Math.max(0.001, k), 1, 1] }, Playhead: { p: [k * TW, 0, 0] } }; }),
    clip(root, 'Intro', 1.2, (t) => {
      const a = back(t / 0.8), b = smooth((t - 0.4) / 0.8);
      return { FrameBody: { p: [0, 0, -0.8 * (1 - a)], s: [0.92 + 0.08 * a, 0.92 + 0.08 * a, 1] }, Dock: { p: [0, -0.5 * (1 - b), -0.2 * (1 - b)], s: [0.8 + 0.2 * b, 0.8 + 0.2 * b, 1] } };
    }),
    clip(root, 'Hover_Play', 0.25, (t) => { const k = smooth(t / 0.25); return { PlayKey: { p: [0, 0, 0.05 * k], s: [1 + 0.1 * k, 1 + 0.1 * k, 1] } }; }),
    clip(root, 'AI_Live', 1.4, (t) => { const k = 0.5 - 0.5 * Math.cos((2 * Math.PI * t) / 1.4); return { AIChipDot: { s: [1 + 0.6 * k, 1 + 0.6 * k, 1 + 0.6 * k] }, EvidencePin_0: { p: [0, 0.03 * k, 0] }, EvidencePin_1: { p: [0, 0.03 * (1 - k), 0] } }; }),
  ];
  return { root, clips };
}

// ===========================================================================
// 7. Chapter strip: detected chapters as raised segments with a scanning playhead
// ===========================================================================
function chapterStrip() {
  const widths = [1.2, 2.0, 1.4, 1.8, 1.0], gap = 0.05, H = 0.72;
  const total = widths.reduce((a, b) => a + b, 0) + gap * (widths.length - 1);
  const root = group('ChapterStrip');
  root.add(mesh(slab(total + 0.24, H + 0.24, 0.12, 0.06), M.alu, 'Rail', [0, 0, -0.06]));
  let x = -total / 2;
  const spans = [];
  widths.forEach((w, i) => {
    const seg = group(`Chapter_${i}`, [x + w / 2, 0, 0.03]);
    seg.add(mesh(slab(w, H, 0.07, 0.1), i === 1 ? M.cobalt : M.porcelain, `ChapterBody_${i}`));
    root.add(seg);
    spans.push([x, x + w]);
    x += w + gap;
  });
  const head = group('Playhead', [-total / 2, 0, 0.14]);
  head.add(mesh(slab(0.04, H + 0.34, 0.02, 0.04, { bevel: 0.004 }), M.signalGlow, 'PlayheadLine'));
  head.add(mesh(disc(0.08, 0.05), M.signalGlow, 'PlayheadKnob', [0, (H + 0.34) / 2, 0]));
  root.add(head);
  const clips = [clip(root, 'Scan', 6, (t) => {
    const px = -total / 2 + (t / 6) * total;
    const out = { Playhead: { p: [(t / 6) * total, 0, 0] } };
    spans.forEach(([a, b], i) => {
      const inside = Math.min(smooth((px - a) / 0.2), smooth((b - px) / 0.2));
      out[`Chapter_${i}`] = { p: [0, 0, 0.07 * Math.max(0, inside)] };
    });
    return out;
  })];
  return { root, clips };
}

// ===========================================================================
// 8. Pipeline tracker: Ingest -> Transcribe -> Understand -> Index -> Ready
// ===========================================================================
function pipeline() {
  const stages = [['Ingest', 'upload'], ['Transcribe', 'transcript'], ['Understand', 'summary'], ['Index', 'search'], ['Ready', 'check']];
  const root = group('Pipeline');
  const gapX = 2;
  stages.forEach(([label, icon], i) => {
    const x = (i - 2) * gapX;
    const st = group(`Stage_${label}`, [x, 0, 0]);
    st.add(mesh(disc(0.52, 0.08), M.alu, `StageBase_${label}`));
    const lit = mesh(disc(0.62, 0.03, { hole: [1.1, 1.1, 0.55] }), M.signalGlow, `Lit_${label}`, [0, 0, -0.01]);
    lit.scale.set(0.001, 0.001, 0.001);
    st.add(lit);
    const cap = group(`StageCap_${label}`, [0, 0, 0.1]);
    cap.add(mesh(disc(0.45, 0.12), M.porcelain, `StageCapBody_${label}`));
    cap.add(mesh(iconGeo(icon, 0.5, 0.028), i === 4 ? M.success : M.cobalt, `StageIcon_${label}`, [0, 0, 0.065]));
    st.add(cap);
    root.add(st);
    if (i < 4) {
      const rx = x + 0.56, rw = gapX - 1.12;
      root.add(mesh(leftAnchored(slab(rw, 0.08, 0.04, 0.04, { bevel: 0.006 }), rw), M.mist, `Rail_${i}`, [rx, 0, 0.02]));
      const fill = mesh(leftAnchored(slab(rw, 0.08, 0.04, 0.046, { bevel: 0.006 }), rw), M.signalGlow, `RailFill_${i}`, [rx, 0, 0.022]);
      fill.scale.set(0.001, 1, 1);
      root.add(fill);
    }
  });
  const step = 1.4;
  const clips = [clip(root, 'Process', 7.5, (t) => {
    const out = {};
    stages.forEach(([label], i) => {
      const k = back((t - i * step) / 0.35);
      out[`Lit_${label}`] = { s: [Math.max(0.001, k), Math.max(0.001, k), Math.max(0.001, k)] };
      out[`StageCap_${label}`] = { p: [0, 0, 0.05 * pulse(t, i * step, 0.5)], s: i === 4 ? [1 + 0.12 * pulse(t, i * step, 0.6), 1 + 0.12 * pulse(t, i * step, 0.6), 1] : [1, 1, 1] };
      if (i < 4) out[`RailFill_${i}`] = { s: [Math.max(0.001, smooth((t - i * step - 0.2) / (step - 0.2))), 1, 1] };
    });
    return out;
  })];
  return { root, clips };
}

// ===========================================================================
// 9. Upload tray: recessed drop zone, dashed rim, bobbing arrow, a file dropping in
// ===========================================================================
function uploadTray() {
  const W = 3.2, H = 2.2;
  const root = group('UploadTray');
  root.add(mesh(slab(W + 0.12, H + 0.12, 0.26, 0.06), M.alu, 'TrayBase', [0, 0, -0.1]));
  root.add(mesh(slab(W - 0.4, H - 0.4, 0.14, 0.04), M.mist, 'Floor', [0, 0, -0.05]));
  root.add(mesh(slab(W, H, 0.24, 0.22, { hole: [W - 0.4, H - 0.4, 0.14] }), M.porcelain, 'Walls', [0, 0, 0.02]));
  // Dashed rim around the floor
  const rim = rrShape(W - 0.6, H - 0.6, 0.1).getSpacedPoints(44);
  for (let i = 0; i < rim.length - 1; i += 2) {
    const a = rim[i], b = rim[i + 1], len = Math.hypot(b.x - a.x, b.y - a.y);
    rootAddDash(root, a, b, len, i / 2);
  }
  const arrow = group('Arrow', [0, 0.05, 0.2]);
  arrow.add(mesh(iconGeo('upload', 1.1, 0.07), M.cobalt, 'ArrowIcon'));
  root.add(arrow);
  const card = group('FileCard', [0, 0, 0.12]);
  card.add(mesh(slab(0.8, 1.0, 0.08, 0.05), M.porcelain, 'FileCardBody'));
  card.add(mesh(iconGeo('video', 0.5, 0.03), M.cobalt, 'FileCardIcon', [0, 0.05, 0.03]));
  card.scale.set(0.001, 0.001, 0.001);
  root.add(card);
  const clips = [
    clip(root, 'Idle', 2, (t) => ({ Arrow: { p: [0, 0.08 * Math.sin((2 * Math.PI * t) / 2), 0] } })),
    clip(root, 'Drop', 1.6, (t) => {
      const d = smooth(t / 0.7), land = back((t - 0.6) / 0.4);
      const k = t < 0.05 ? 0.001 : 1;
      return {
        FileCard: { p: [0, 1.6 * (1 - d), 1.2 * (1 - d)], s: [k, k, k], r: [-25 * (1 - d), 0, 8 * (1 - d)] },
        Arrow: { s: [Math.max(0.001, 1 - land), Math.max(0.001, 1 - land), Math.max(0.001, 1 - land)] },
      };
    }),
  ];
  return { root, clips };
}
function rootAddDash(root, a, b, len, i) {
  const g = new THREE.CapsuleGeometry(0.018, Math.max(0.001, len - 0.036), 3, 8);
  g.rotateZ(Math.atan2(b.y - a.y, b.x - a.x) - Math.PI / 2);
  root.add(mesh(g, M.cobalt, `Dash_${i}`, [(a.x + b.x) / 2, (a.y + b.y) / 2, -0.02]));
}

// ===========================================================================
// 10. AI answer card: question bar, answer lines being written, citation chip
// ===========================================================================
function aiAnswer() {
  const W = 4.2, H = 2.6;
  const root = group('AIAnswer');
  root.add(mesh(slab(W + 0.12, H + 0.12, 0.14, 0.05), M.signal, 'AIEdge', [0, 0, -0.05]));
  root.add(mesh(slab(W, H, 0.1, 0.08), M.porcelain, 'Panel'));
  const bar = group('QueryBar', [0, H / 2 - 0.42, 0.06]);
  bar.add(mesh(slab(W - 0.4, 0.44, 0.07, 0.04), M.mist, 'QueryBarBody'));
  bar.add(mesh(iconGeo('chevron-right', 0.28, 0.022), M.signal, 'QueryChevron', [-W / 2 + 0.45, 0, 0.03]));
  bar.add(mesh(leftAnchored(slab(1.9, 0.07, 0.035, 0.02, { bevel: 0.004 }), 1.9), M.ink, 'QueryText', [-W / 2 + 0.68, 0, 0.025]));
  root.add(bar);
  const lines = [[3.2, M.signal], [2.5, M.signalSoft], [2.9, M.signalSoft], [1.6, M.signalSoft]];
  lines.forEach(([w, mat], i) => {
    const l = mesh(leftAnchored(slab(w, 0.13, 0.065, 0.03, { bevel: 0.005 }), w), mat, `Line_${i}`, [-W / 2 + 0.3, 0.25 - i * 0.3, 0.05]);
    l.scale.set(0.001, 1, 1);
    root.add(l);
  });
  const cite = group('Citation', [-W / 2 + 1.0, -H / 2 + 0.35, 0.07]);
  cite.add(mesh(slab(1.3, 0.3, 0.15, 0.05), M.signal, 'CitationBody'));
  cite.add(mesh(iconGeo('search', 0.2, 0.018), M.porcelain, 'CitationIcon', [-0.45, 0, 0.03]));
  cite.add(mesh(leftAnchored(slab(0.7, 0.05, 0.025, 0.015, { bevel: 0.003 }), 0.7), M.porcelain, 'CitationText', [-0.3, 0, 0.03]));
  cite.scale.set(0.001, 0.001, 0.001);
  root.add(cite);
  const clips = [clip(root, 'Answer', 3, (t) => {
    const out = {};
    lines.forEach((_, i) => { out[`Line_${i}`] = { s: [Math.max(0.001, smooth((t - 0.2 - i * 0.45) / 0.6)), 1, 1] }; });
    const c = Math.max(0.001, back((t - 2.2) / 0.35));
    out.Citation = { s: [c, c, c] };
    return out;
  })];
  return { root, clips };
}

// ===========================================================================
// 11. Flashcards: violet Study stack, front card flips
// ===========================================================================
function flashcards() {
  const W = 2.4, H = 1.6;
  const root = group('Flashcards');
  const card = (name, pos, rotZ, front) => {
    const g = group(name, pos);
    g.rotation.z = (rotZ * Math.PI) / 180;
    g.add(mesh(slab(W, H, 0.1, 0.05), M.porcelain, `${name}_Body`));
    g.add(mesh(slab(W, H, 0.1, 0.056, { hole: [W - 0.05, H - 0.05, 0.08], bevel: 0.004 }), front ? M.violet : M.mist, `${name}_Edge`));
    if (front) {
      g.add(mesh(iconGeo('flashcard', 0.55, 0.03), M.violet, `${name}_Icon`, [0, 0.12, 0.03]));
      g.add(mesh(slab(1.2, 0.07, 0.035, 0.02, { bevel: 0.004 }), M.mist, `${name}_Label`, [0, -0.4, 0.03]));
      g.add(mesh(slab(W - 0.2, H - 0.2, 0.08, 0.02), M.violet, `${name}_Answer`, [0, 0, -0.032], [0, 180, 0]));
    }
    return g;
  };
  root.add(card('Card_Back', [0.4, -0.3, -0.16], 3, false));
  root.add(card('Card_Middle', [0.2, -0.15, -0.08], -1, false));
  root.add(card('Card_Front', [0, 0, 0], 0, true));
  const clips = [
    clip(root, 'Flip', 1.2, (t) => { const k = smooth(t / 1.2); return { Card_Front: { r: [0, 180 * k, 0], p: [0, 0, 0.5 * Math.sin(Math.PI * k)] } }; }),
    clip(root, 'Float', 4, (t) => { const s = Math.sin((2 * Math.PI * t) / 4); return { Card_Front: { p: [0, 0.04 * s, 0], r: [2 * s, -3 * s, 0] }, Card_Middle: { p: [0, 0.025 * s, 0], r: [0, 0, -1] }, Card_Back: { p: [0, 0.015 * s, 0], r: [0, 0, 3] } }; }),
  ];
  return { root, clips };
}

// ===========================================================================
// 12. Status badges: Processing (live), Ready, Failed
// ===========================================================================
function statusBadges() {
  const root = group('StatusBadges');
  const badge = (name, x, mat, icon) => {
    const b = group(`Badge_${name}`, [x, 0, 0]);
    b.add(mesh(slab(1.7, 0.46, 0.23, 0.05), M.alu, `BadgeTray_${name}`, [0, 0, -0.04]));
    b.add(mesh(slab(1.6, 0.38, 0.19, 0.08), mat, `BadgeBody_${name}`));
    if (icon) b.add(mesh(iconGeo(icon, 0.24, 0.022), M.porcelain, `BadgeIcon_${name}`, [-0.55, 0, 0.05]));
    else b.add(mesh(new THREE.SphereGeometry(0.06, 16, 12), M.signalGlow, `BadgeDot_${name}`, [-0.55, 0, 0.045]));
    b.add(mesh(leftAnchored(slab(0.75, 0.06, 0.03, 0.02, { bevel: 0.004 }), 0.75), M.porcelain, `BadgeText_${name}`, [-0.35, 0, 0.045]));
    root.add(b);
  };
  badge('Processing', -2, M.signal, null);
  badge('Ready', 0, M.success, 'check');
  badge('Failed', 2, M.error, 'alert');
  const clips = [clip(root, 'Pulse', 1.2, (t) => { const k = 0.5 - 0.5 * Math.cos((2 * Math.PI * t) / 1.2); return { BadgeDot_Processing: { s: [1 + 0.7 * k, 1 + 0.7 * k, 1 + 0.7 * k] } }; })];
  return { root, clips };
}

// ===========================================================================
// 13. Logo mark: the ReelSense frame notch + signal line (Logo.tsx)
// ===========================================================================
function logoMark() {
  const root = group('LogoMark');
  const spin = group('MarkSpin');
  spin.add(mesh(strokeGeometry('<rect x="1.5" y="4" width="21" height="16" rx="3.5" />', { viewBox: 24, size: 2.4, radius: 0.09 }), M.cobalt, 'MarkFrame'));
  const sig = group('MarkSignal', [0, 0, 0.06]);
  sig.add(mesh(strokeGeometry('<path d="M5 15.5 8.6 11l3 3.2L14 9l5 5.5" />', { viewBox: 24, size: 2.4, radius: 0.09 }), M.signal, 'MarkSignalLine'));
  spin.add(sig);
  root.add(spin);
  const clips = [
    clip(root, 'Float', 6, (t) => ({ MarkSpin: { r: [4 * Math.sin((2 * Math.PI * t) / 6), 16 * Math.sin((2 * Math.PI * t) / 6 + 0.6), 0], p: [0, 0.05 * Math.sin((2 * Math.PI * t) / 3), 0] } })),
    clip(root, 'Signal', 1.2, (t) => { const k = pulse(t, 0, 1.2); return { MarkSignal: { p: [0, 0, 0.12 * k], s: [1, 1 + 0.12 * k, 1] } }; }),
  ];
  return { root, clips };
}

// ===========================================================================
// 14. Quiz card: question + four options, correct / wrong answer states
// ===========================================================================
function quizCard() {
  const W = 3.4, H = 2.7;
  const root = group('QuizCard');
  root.add(mesh(slab(W + 0.12, H + 0.12, 0.14, 0.05), M.violet, 'QuizEdge', [0, 0, -0.05]));
  root.add(mesh(slab(W, H, 0.1, 0.08), M.porcelain, 'QuizPanel'));
  root.add(mesh(iconGeo('quiz', 0.36, 0.026), M.violet, 'QuizIcon', [-W / 2 + 0.4, H / 2 - 0.38, 0.06]));
  root.add(mesh(leftAnchored(slab(2.2, 0.1, 0.05, 0.02, { bevel: 0.004 }), 2.2), M.ink, 'QuestionText', [-W / 2 + 0.7, H / 2 - 0.38, 0.05]));
  for (let i = 0; i < 4; i++) {
    const o = group(`Option_${i}`, [0, 0.45 - i * 0.48, 0.05]);
    o.add(mesh(slab(W - 0.5, 0.38, 0.06, 0.05), M.mist, `OptionBody_${i}`));
    o.add(mesh(disc(0.08, 0.03, { hole: [0.1, 0.1, 0.05], bevel: 0.004 }), M.alu, `OptionRadio_${i}`, [-(W - 0.5) / 2 + 0.25, 0, 0.03]));
    o.add(mesh(leftAnchored(slab(1.4 - (i % 2) * 0.4, 0.07, 0.035, 0.015, { bevel: 0.003 }), 1.4 - (i % 2) * 0.4), M.ink, `OptionText_${i}`, [-(W - 0.5) / 2 + 0.45, 0, 0.03]));
    root.add(o);
  }
  const mark = (name, mat, icon, y) => {
    const g = group(name, [(W - 0.5) / 2 - 0.25, y, 0.13]);
    g.add(mesh(disc(0.14, 0.05), mat, `${name}_Body`));
    g.add(mesh(iconGeo(icon, 0.2, 0.018), M.porcelain, `${name}_Icon`, [0, 0, 0.03]));
    g.scale.set(0.001, 0.001, 0.001);
    root.add(g);
  };
  mark('CorrectMark', M.success, 'check', 0.45 - 2 * 0.48);
  mark('WrongMark', M.error, 'close', 0.45 - 1 * 0.48);
  const clips = [
    clip(root, 'Answer_Correct', 1.2, (t) => { const k = Math.max(0.001, back((t - 0.2) / 0.4)); return { Option_2: { p: [0, 0, 0.06 * smooth(t / 0.2)] }, CorrectMark: { s: [k, k, k] } }; }),
    clip(root, 'Answer_Wrong', 1.0, (t) => { const k = Math.max(0.001, back((t - 0.1) / 0.3)); return { Option_1: { p: [0.05 * Math.sin(t * 40) * (1 - smooth(t / 0.6)), 0, 0] }, WrongMark: { s: [k, k, k] } }; }),
  ];
  return { root, clips };
}

// ---------------------------------------------------------------------------
const builds = [
  ['rs_button_primary.glb', () => button('Primary')],
  ['rs_button_secondary.glb', () => button('Secondary')],
  ['rs_button_ai.glb', () => button('AI')],
  ['rs_icon_keys.glb', iconKeys],
  ['rs_icons.glb', iconSet],
  ['rs_video_frame.glb', videoFrame],
  ['rs_chapter_strip.glb', chapterStrip],
  ['rs_pipeline.glb', pipeline],
  ['rs_upload_tray.glb', uploadTray],
  ['rs_ai_answer.glb', aiAnswer],
  ['rs_flashcards.glb', flashcards],
  ['rs_status_badges.glb', statusBadges],
  ['rs_logo_mark.glb', logoMark],
  ['rs_quiz_card.glb', quizCard],
];
for (const [file, build] of builds) {
  const { root, clips } = build();
  await save(file, root, clips);
}
console.table(report.map((r) => ({ file: r.file, triangles: r.tris, KB: r.kb, clips: r.clips.join(', ') })));
fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(report, null, 2));
