"use client";

import { Environment } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { Suspense, useMemo, useRef, type MutableRefObject, type ReactNode } from "react";
import * as THREE from "three";

import { NovaErrorBoundary } from "@/components/3d/NovaErrorBoundary";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

/**
 * Same palette as globals.css, as literal hex - three.js materials
 * can't read CSS custom properties.
 */
const C = {
  caseDark: "#7C817F",
  titanium: "#A4A9A7",
  plate: "#B3B8B6",
  lume: "#E0A526",
  petrol: "#24566A",
  carmine: "#A3243B",
  ink: "#3D3442",
};

export interface MovementImplProps {
  /** 0 = assembled, 1 = fully exploded into its layers. */
  explode?: number;
  /** Tilt the movement toward the pointer. */
  tilt?: boolean;
  /** Camera framing: "hero" (oblique, room for the explode) or "badge" (closer, top-down-ish). */
  framing?: "hero" | "badge";
  className?: string;
}

/** A gear outline (teeth + spoke windows + arbor hole), lying in the XY plane. */
function gearShape(teeth: number, radius: number, toothDepth: number, spokes: number): THREE.Shape {
  const shape = new THREE.Shape();
  const root = radius - toothDepth;
  const step = (Math.PI * 2) / teeth;
  for (let i = 0; i < teeth; i += 1) {
    const a = i * step;
    const pts: Array<[number, number]> = [
      [root, a],
      [radius, a + step * 0.18],
      [radius, a + step * 0.48],
      [root, a + step * 0.66],
    ];
    pts.forEach(([r, angle], index) => {
      const x = r * Math.cos(angle);
      const y = r * Math.sin(angle);
      if (i === 0 && index === 0) shape.moveTo(x, y);
      else shape.lineTo(x, y);
    });
  }
  shape.closePath();

  const arbor = new THREE.Path();
  arbor.absarc(0, 0, Math.max(0.025, radius * 0.08), 0, Math.PI * 2, true);
  shape.holes.push(arbor);

  if (spokes > 0 && radius > 0.18) {
    const inner = radius * 0.24;
    const outer = root - radius * 0.12;
    const span = (Math.PI * 2) / spokes;
    const web = Math.min(0.35, 0.12 / radius);
    for (let s = 0; s < spokes; s += 1) {
      const a0 = s * span + web / 2;
      const a1 = (s + 1) * span - web / 2;
      const cutout = new THREE.Path();
      cutout.absarc(0, 0, outer, a0, a1, false);
      cutout.lineTo(inner * Math.cos(a1), inner * Math.sin(a1));
      cutout.absarc(0, 0, inner, a1, a0, true);
      cutout.closePath();
      shape.holes.push(cutout);
    }
  }
  return shape;
}

function annulusShape(outer: number, inner: number): THREE.Shape {
  const shape = new THREE.Shape();
  shape.absarc(0, 0, outer, 0, Math.PI * 2, false);
  const hole = new THREE.Path();
  hole.absarc(0, 0, inner, 0, Math.PI * 2, true);
  shape.holes.push(hole);
  return shape;
}

/** Extrude a flat shape into a plate lying on the XZ plane, thickness growing +Y. */
function useFlatGeometry(build: () => THREE.Shape, depth: number, deps: unknown[]) {
  return useMemo(() => {
    const geometry = new THREE.ExtrudeGeometry(build(), { depth, bevelEnabled: false, curveSegments: 40 });
    geometry.rotateX(-Math.PI / 2);
    return geometry;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}

function Metal({ color, rough = 0.38, metal = 0.75 }: { color: string; rough?: number; metal?: number }) {
  return <meshStandardMaterial color={color} roughness={rough} metalness={metal} />;
}

interface GearProps {
  position: [number, number, number];
  teeth: number;
  radius: number;
  speed: number;
  color: string;
  spokes?: number;
  animate: boolean;
}

function Gear({ position, teeth, radius, speed, color, spokes = 5, animate }: GearProps) {
  const ref = useRef<THREE.Mesh>(null);
  const geometry = useFlatGeometry(() => gearShape(teeth, radius, Math.min(0.05, radius * 0.11), spokes), 0.045, [
    teeth,
    radius,
    spokes,
  ]);
  useFrame((_, delta) => {
    if (animate && ref.current) ref.current.rotation.y += speed * delta;
  });
  return (
    <group position={position}>
      <mesh ref={ref} geometry={geometry}>
        <Metal color={color} rough={0.32} />
      </mesh>
      {/* Pinion + arbor */}
      <mesh position={[0, -0.02, 0]}>
        <cylinderGeometry args={[radius * 0.16, radius * 0.16, 0.12, 20]} />
        <Metal color={C.titanium} />
      </mesh>
    </group>
  );
}

function Jewel({ position }: { position: [number, number, number] }) {
  return (
    <mesh position={position}>
      <cylinderGeometry args={[0.045, 0.045, 0.03, 18]} />
      <meshStandardMaterial color={C.carmine} roughness={0.15} metalness={0.1} />
    </mesh>
  );
}

function Balance({ position, animate }: { position: [number, number, number]; animate: boolean }) {
  const ref = useRef<THREE.Group>(null);
  useFrame(({ clock }) => {
    if (animate && ref.current) ref.current.rotation.y = Math.sin(clock.elapsedTime * Math.PI * 2 * 1.25) * 1.4;
  });
  return (
    <group position={position}>
      <group ref={ref}>
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.36, 0.03, 12, 64]} />
          <Metal color={C.lume} rough={0.28} />
        </mesh>
        {[0, 1, 2].map((i) => (
          <mesh key={i} rotation={[0, (i * Math.PI) / 3, 0]}>
            <boxGeometry args={[0.72, 0.02, 0.03]} />
            <Metal color={C.lume} />
          </mesh>
        ))}
        {/* Hairspring, flattened */}
        <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0.03, 0]}>
          <torusGeometry args={[0.14, 0.008, 6, 48]} />
          <Metal color={C.petrol} rough={0.25} />
        </mesh>
      </group>
      <Jewel position={[0, 0.05, 0]} />
    </group>
  );
}

function Bridge({
  position,
  size,
  rotation = 0,
  jewels = [],
}: {
  position: [number, number, number];
  size: [number, number];
  rotation?: number;
  jewels?: Array<[number, number]>;
}) {
  return (
    <group position={position} rotation={[0, rotation, 0]}>
      <mesh>
        <boxGeometry args={[size[0], 0.06, size[1]]} />
        <Metal color={C.titanium} rough={0.45} metal={0.8} />
      </mesh>
      {jewels.map(([x, z], index) => (
        <Jewel key={index} position={[x, 0.04, z]} />
      ))}
    </group>
  );
}

function Layer({ index, explode, children }: { index: number; explode: MutableRefObject<number>; children: ReactNode }) {
  const ref = useRef<THREE.Group>(null);
  const gap = 0.46;
  useFrame(() => {
    if (ref.current) ref.current.position.y = index * 0.07 + explode.current * gap * index;
  });
  return <group ref={ref}>{children}</group>;
}

function Movement({ explode, tilt, animate }: { explode: number; tilt: boolean; animate: boolean }) {
  const root = useRef<THREE.Group>(null);
  const current = useRef(explode);
  const caseGeometry = useFlatGeometry(() => annulusShape(1.82, 1.6), 0.16, []);
  const bezelGeometry = useFlatGeometry(() => annulusShape(1.86, 1.62), 0.09, []);

  useFrame(({ pointer, camera }, delta) => {
    current.current += (explode - current.current) * Math.min(1, delta * 4);
    if (root.current) {
      const targetX = tilt && animate ? pointer.y * -0.12 : 0;
      const targetZ = tilt && animate ? pointer.x * 0.12 : 0;
      root.current.rotation.x += (targetX - root.current.rotation.x) * Math.min(1, delta * 3);
      root.current.rotation.z += (targetZ - root.current.rotation.z) * Math.min(1, delta * 3);
    }
    camera.lookAt(0, 0.35 + current.current * 1.0, 0);
  });

  return (
    <group ref={root}>
      {/* 0 - case back */}
      <Layer index={0} explode={current}>
        <mesh geometry={caseGeometry}>
          <Metal color={C.caseDark} rough={0.5} />
        </mesh>
        <mesh position={[0, 0.02, 0]}>
          <cylinderGeometry args={[1.6, 1.6, 0.04, 96]} />
          <Metal color={C.caseDark} rough={0.55} metal={0.7} />
        </mesh>
      </Layer>

      {/* 1 - main plate */}
      <Layer index={1} explode={current}>
        <mesh>
          <cylinderGeometry args={[1.52, 1.52, 0.07, 96]} />
          <Metal color={C.plate} rough={0.5} metal={0.6} />
        </mesh>
        {[
          [-0.6, 0.35],
          [0, 0],
          [0.62, -0.42],
          [0.66, 0.38],
          [0.1, 0.78],
        ].map(([x, z], i) => (
          <Jewel key={i} position={[x!, 0.05, z!]} />
        ))}
      </Layer>

      {/* 2 - gear train */}
      <Layer index={2} explode={current}>
        <Gear position={[-0.6, 0, 0.35]} teeth={64} radius={0.62} speed={0.12} color={C.lume} animate={animate} />
        <Gear position={[0, 0.02, 0]} teeth={48} radius={0.48} speed={-0.42} color={C.lume} animate={animate} />
        <Gear position={[0.66, 0, 0.38]} teeth={36} radius={0.34} speed={0.9} color={C.lume} animate={animate} />
        <Gear position={[0.62, 0.02, -0.42]} teeth={30} radius={0.3} speed={-1.6} color={C.lume} animate={animate} />
        <Gear position={[0.1, 0, 0.78]} teeth={15} radius={0.19} speed={3.4} color={C.petrol} spokes={3} animate={animate} />
      </Layer>

      {/* 3 - balance */}
      <Layer index={3} explode={current}>
        <Balance position={[-0.62, 0, -0.6]} animate={animate} />
      </Layer>

      {/* 4 - bridges */}
      <Layer index={4} explode={current}>
        <Bridge position={[-0.3, 0, 0.2]} size={[1.5, 0.34]} rotation={0.5} jewels={[[-0.55, 0], [0.4, 0]]} />
        <Bridge position={[0.62, 0, 0]} size={[0.3, 1.1]} jewels={[[0, 0.38], [0, -0.42]]} />
        <Bridge position={[-0.62, 0, -0.6]} size={[0.9, 0.18]} rotation={-0.7} jewels={[[0, 0]]} />
      </Layer>

      {/* 5 - bezel with printed indices */}
      <Layer index={5} explode={current}>
        <mesh geometry={bezelGeometry}>
          <Metal color={C.titanium} rough={0.3} metal={0.85} />
        </mesh>
        {Array.from({ length: 12 }).map((_, i) => {
          const a = (i / 12) * Math.PI * 2;
          const r = 1.74;
          return (
            <mesh key={i} position={[Math.sin(a) * r, 0.1, Math.cos(a) * r]} rotation={[0, a, 0]}>
              <boxGeometry args={[i % 3 === 0 ? 0.06 : 0.03, 0.02, 0.16]} />
              <meshStandardMaterial color={i === 0 ? C.lume : C.ink} roughness={0.6} />
            </mesh>
          );
        })}
      </Layer>
    </group>
  );
}

/**
 * A procedural chronograph movement (no GLB) - case back, plate, gear
 * train, balance, bridges and bezel as six real layers that can
 * separate along Y ("exploded view"). Always decorative: aria-hidden,
 * no pointer capture, and a reduced-motion preference freezes every
 * moving part while keeping the object on screen.
 */
function MovementImpl({ explode = 0, tilt = true, framing = "hero", className }: MovementImplProps) {
  const reducedMotion = useReducedMotion();
  const camera =
    framing === "hero"
      ? { position: [0, 5.6, 7.4] as [number, number, number], fov: 30 }
      : { position: [0, 4.4, 2.4] as [number, number, number], fov: 38 };

  return (
    <div aria-hidden="true" className={cn("pointer-events-none relative", className)}>
      <NovaErrorBoundary fallback={null}>
        <Canvas
          camera={camera}
          dpr={[1, 1.75]}
          frameloop={reducedMotion ? "demand" : "always"}
          gl={{ antialias: true, alpha: true }}
          onCreated={({ gl }) => {
            gl.toneMapping = THREE.ACESFilmicToneMapping;
          }}
        >
          <ambientLight intensity={0.45} />
          <directionalLight position={[3, 6, 2]} intensity={1.05} />
          <directionalLight position={[-3, 2, -3]} intensity={0.3} />
          <Suspense fallback={null}>
            <Environment files="/assets/hdr/studio_small_03_1k.hdr" environmentIntensity={0.3} />
          </Suspense>
          <Movement explode={explode} tilt={tilt} animate={!reducedMotion} />
        </Canvas>
      </NovaErrorBoundary>
    </div>
  );
}

export default MovementImpl;
