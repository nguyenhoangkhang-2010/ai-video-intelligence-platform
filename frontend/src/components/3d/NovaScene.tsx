"use client";

import { Environment } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Suspense, type ReactNode } from "react";
import * as THREE from "three";

export type NovaPresentationMode = "ambient" | "hero" | "workspace";

interface NovaSceneProps {
  children: ReactNode;
  mode?: NovaPresentationMode;
}

/**
 * Two real camera presentations, derived from nova.glb's own bone
 * positions (nova-3d/build.mjs), not guessed:
 *
 * - "hero": position [0, 0.62, 2.6], fov 30, looking at (0, 0.52, 0) -
 *   matches nova-3d/index.html's tuned reference viewer exactly. At
 *   this framing the full figure (feet at world Y≈0, head/antenna top
 *   at Y≈1.06) fits within the vertical field of view with margin -
 *   verified by the FOV math (2.6 * tan(15°) ≈ 0.70 half-height, so a
 *   ±0.70 window centered on Y=0.52 spans roughly -0.18 to 1.22,
 *   covering the whole model) - appropriate for large/full-bleed
 *   placements where showing the whole figure matters (auth, a future
 *   landing hero).
 *
 * - "ambient": position [0, 0.85, 1.15], fov 28, looking at (0, 0.72, 0)
 *   - a genuine head-and-shoulders portrait crop, re-centered on the
 *   face specifically (the eye bones sit at world Y≈0.755, the mouth
 *   around Y≈0.65 - averaging toward eye level since gaze/eye contact
 *   is what actually reads at small sizes). The default "hero" framing
 *   centers on the upper chest, not the face - fine at 300px+, but at
 *   the ambient corner instance's ~56px the face becomes too small to
 *   register. Used for every small/boxed placement.
 *
 * - "workspace": position [0, 0.75, 1.7], fov 29, looking at (0, 0.62, 0)
 *   - a medium/waist-up shot, between the two above. Half-height at
 *   this distance/FOV (1.7 * tan(14.5°) ≈ 0.44) centered on Y=0.62
 *   spans ≈0.18–1.06, i.e. hips through head-top - shows Nova's full
 *   upper body and posture (not just a portrait) without the large
 *   empty floor space "hero" leaves at a few-hundred-px placement.
 *   Used for the workspace's own ambient/atmospheric instance.
 *
 * No shadow map, no contact shadow in any mode: the clearcoat shell
 * material and environment lighting already read as premium/glossy
 * without the extra render cost.
 */
export function NovaScene({ children, mode = "ambient" }: NovaSceneProps) {
  const cameras: Record<NovaPresentationMode, { position: [number, number, number]; fov: number; lookAt: [number, number, number] }> = {
    hero: { position: [0, 0.62, 2.6], fov: 30, lookAt: [0, 0.52, 0] },
    workspace: { position: [0, 0.75, 1.7], fov: 29, lookAt: [0, 0.62, 0] },
    ambient: { position: [0, 0.85, 1.15], fov: 28, lookAt: [0, 0.72, 0] },
  };
  const camera = cameras[mode];

  return (
    <Canvas
      camera={{ position: camera.position, fov: camera.fov }}
      dpr={[1, 1.75]}
      gl={{ antialias: true, alpha: true }}
      onCreated={({ gl, camera: activeCamera }) => {
        gl.toneMapping = THREE.ACESFilmicToneMapping;
        activeCamera.lookAt(...camera.lookAt);
      }}
    >
      <ambientLight intensity={0.35} />
      <directionalLight position={[1.5, 2.5, 3]} intensity={1.6} color="#ffffff" />
      <directionalLight position={[-2, 1, -1.5]} intensity={0.3} color="#5CF2E3" />
      <Suspense fallback={null}>
        <Environment preset="studio" environmentIntensity={0.6} />
        {children}
      </Suspense>
    </Canvas>
  );
}
