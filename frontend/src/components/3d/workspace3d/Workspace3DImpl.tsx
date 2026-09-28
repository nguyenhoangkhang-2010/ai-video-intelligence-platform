"use client";

import { Environment } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Suspense, useEffect, useMemo, useRef } from "react";
import * as THREE from "three";

import { useGLTF } from "@react-three/drei";

import { WORKSPACE_3D_MODELS, type Workspace3DModelName } from "@/components/3d/workspace3d/registry";

export interface Workspace3DImplProps {
  model: Workspace3DModelName;
  /** Scrub mode: drives the named clip's own timeline directly from real 0..1 progress - never autoplays, never invents motion the data doesn't back. Takes priority over playClip/loopClip if set. */
  scrubClip?: string;
  scrubProgress?: number;
  /** One-shot mode: plays the named clip once (LoopOnce, clamped on its last frame) whenever `playKey` changes. */
  playClip?: string;
  playKey?: string | number;
  /** Continuous ambient loop (e.g. Float) - no data to drive, just a restrained idle accent. */
  loopClip?: string;
  /**
   * Bidirectional hold mode, for a real boolean UI state (hover/focus)
   * rather than a one-off event: plays the named clip forward and
   * clamps on its last frame while `holdActive` is true, or in
   * reverse back to its first frame while false - the kit's own
   * documented pattern for reversing a hover ("play it with
   * timeScale = -1", see ui-3d/README.md), driven by real DOM
   * hover/focus events, never a fabricated toggle.
   */
  holdClip?: string;
  holdActive?: boolean;
  /**
   * Some GLBs bake several mutually-exclusive variants, or extra
   * geometry this integration doesn't want, into one file (e.g.
   * rs_status_badges.glb's Badge_Processing/Badge_Ready/Badge_Failed,
   * or rs_video_frame.glb's own playback-control geometry alongside
   * its decorative bezel) - each name here is hidden wherever it
   * actually sits in the scene graph (found via `getObjectByName`,
   * which searches every descendant, not just direct children - these
   * models nest each variant/part under their own root group, not as
   * flat siblings of the scene itself). Everything not named stays at
   * its own authored visibility. Omit for a model that's already
   * exactly one thing (the other five integrations never set this).
   */
  hideNodes?: readonly string[];
}

function ModelStage({ model, scrubClip, scrubProgress, playClip, playKey, loopClip, holdClip, holdActive, hideNodes }: Workspace3DImplProps) {
  const def = WORKSPACE_3D_MODELS[model];
  const { scene, animations } = useGLTF(def.path);
  const mixer = useMemo(() => new THREE.AnimationMixer(scene), [scene]);
  const actionsRef = useRef<Map<string, THREE.AnimationAction>>(new Map());
  const { camera, size: viewport } = useThree();

  // Node isolation: explicitly hide only the named nodes, wherever
  // they sit in the hierarchy - everything else keeps its own
  // authored visibility, so this never depends on guessing the
  // model's exact nesting depth.
  useEffect(() => {
    scene.traverse((node) => {
      node.visible = true;
    });
    if (!hideNodes) return;
    for (const name of hideNodes) {
      const node = scene.getObjectByName(name);
      if (node) node.visible = false;
    }
  }, [scene, hideNodes]);

  // Auto-fit: each ui-3d model has a wildly different real footprint
  // (verified by measuring the actual loaded bounding box, not
  // assumed) - rs_pipeline.glb is ~9 units wide but only ~1 tall (a
  // long horizontal strip: 5 stages side by side), while
  // rs_flashcards.glb is closer to a single square card. One fixed
  // camera distance for every model silently cropped the wide ones
  // down to an unrecognizable sliver (found live, via a temporary
  // bounding-box console dump while testing the processing banner) -
  // this instead re-centers the model on its own real bounding-box
  // center and derives a camera distance from that box's actual
  // width/height and the canvas's own aspect ratio, so every model
  // frames correctly regardless of its native proportions. Always
  // measures the model's own full, real bounding box - even with
  // `hideNodes` set, so a model like rs_video_frame.glb (whose hidden
  // control geometry extends further than its own visible bezel)
  // frames at a consistent, honest scale rather than zooming in
  // tighter than the model's own real proportions would suggest.
  useEffect(() => {
    const box = new THREE.Box3().setFromObject(scene);
    const boxSize = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    scene.position.set(-center.x, -center.y, -center.z);

    const perspCamera = camera as THREE.PerspectiveCamera;
    const vFov = THREE.MathUtils.degToRad(perspCamera.fov);
    const aspect = viewport.width / viewport.height;
    const hFov = 2 * Math.atan(Math.tan(vFov / 2) * aspect);
    const distForHeight = boxSize.y / 2 / Math.tan(vFov / 2);
    const distForWidth = boxSize.x / 2 / Math.tan(hFov / 2);
    // 1.25x padding so the model doesn't touch the frame edges.
    const distance = Math.max(distForHeight, distForWidth, 0.1) * 1.25;
    perspCamera.position.set(0, 0, distance + boxSize.z / 2);
    perspCamera.near = Math.max(0.01, distance - boxSize.z * 2);
    perspCamera.far = distance + boxSize.z * 2 + 20;
    perspCamera.lookAt(0, 0, 0);
    perspCamera.updateProjectionMatrix();
  }, [scene, camera, viewport.width, viewport.height, hideNodes]);

  useEffect(() => {
    const map = new Map<string, THREE.AnimationAction>();
    for (const clip of animations) {
      map.set(clip.name, mixer.clipAction(clip));
    }
    actionsRef.current = map;
    return () => {
      mixer.stopAllAction();
    };
  }, [animations, mixer]);

  // Scrub mode: pause the action and set its time directly from real
  // progress (0..1) each time progress changes - the model becomes a
  // pure function of real backend state, never plays on its own clock.
  useEffect(() => {
    if (!scrubClip || scrubProgress === undefined) return;
    const action = actionsRef.current.get(scrubClip);
    const clip = animations.find((c) => c.name === scrubClip);
    if (!action || !clip) return;
    action.reset().play();
    action.paused = true;
    action.time = THREE.MathUtils.clamp(scrubProgress, 0, 1) * clip.duration;
    mixer.update(0);
  }, [scrubClip, scrubProgress, animations, mixer]);

  // One-shot mode: play the clip fresh each time playKey changes,
  // clamped on its last frame rather than looping or resetting to bind
  // pose - a brief, honest reaction to something that just happened.
  useEffect(() => {
    if (!playClip || playKey === undefined) return;
    const action = actionsRef.current.get(playClip);
    if (!action) return;
    action.setLoop(THREE.LoopOnce, 1);
    action.clampWhenFinished = true;
    action.reset().play();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playClip, playKey]);

  // Ambient loop mode: just keep it running.
  useEffect(() => {
    if (!loopClip) return;
    const action = actionsRef.current.get(loopClip);
    if (!action) return;
    action.setLoop(THREE.LoopRepeat, Infinity);
    action.play();
    return () => {
      action.stop();
    };
  }, [loopClip]);

  // Hold mode: a real boolean UI state (hover/focus), not a one-off
  // event - plays forward and clamps on `holdActive`, or in reverse
  // (`timeScale = -1`) back toward the first frame otherwise, exactly
  // the kit's own documented reverse-a-hover pattern. `.play()` on an
  // already-clamped LoopOnce action un-pauses it from wherever it
  // currently sits, so toggling `holdActive` mid-animation reverses
  // smoothly from the current pose rather than snapping.
  useEffect(() => {
    if (!holdClip) return;
    const action = actionsRef.current.get(holdClip);
    if (!action) return;
    action.setLoop(THREE.LoopOnce, 1);
    action.clampWhenFinished = true;
    action.timeScale = holdActive ? 1 : -1;
    action.play();
  }, [holdClip, holdActive]);

  useFrame((_, delta) => {
    // Scrub mode owns time explicitly (paused above) - don't let the
    // mixer's own clock advance it back out from under real progress.
    if (scrubClip) return;
    mixer.update(delta);
  });

  return <primitive object={scene} />;
}

/**
 * The one shared R3F Canvas every Workspace 3D accent mounts into -
 * each call site gets its OWN small Canvas instance (React Three
 * Fiber has no built-in way to render into an existing canvas from an
 * unrelated component tree), but there is only ever at most one of
 * these plus Nova's own ambient canvas mounted at a time in practice:
 * exactly one Workspace mode panel is active at once (see
 * VideoWorkspacePage's ActivePanel switch), so at most one
 * Workspace3DObject instance exists alongside Nova's single ambient
 * instance - never "many unnecessary canvases".
 *
 * Lighting matches NovaScene.tsx's own restrained studio setup (same
 * self-hosted HDR environment map, soft ambient + directional fill) so
 * Nova and these ui-3d accents read as one consistent material system
 * rather than two different rendering styles bolted together.
 */
export default function Workspace3DImpl(props: Workspace3DImplProps) {
  return (
    <Canvas
      camera={{ position: [0, 0.3, 2.6], fov: 32 }}
      dpr={[1, 1.75]}
      gl={{ antialias: true, alpha: true }}
      onCreated={({ gl }) => {
        gl.toneMapping = THREE.ACESFilmicToneMapping;
      }}
    >
      <ambientLight intensity={0.5} />
      <directionalLight position={[1.5, 2.5, 3]} intensity={1.4} color="#ffffff" />
      <directionalLight position={[-2, 1, -1.5]} intensity={0.25} color="#5CF2E3" />
      <Suspense fallback={null}>
        <Environment files="/assets/hdr/studio_small_03_1k.hdr" environmentIntensity={0.5} />
        <ModelStage {...props} />
      </Suspense>
    </Canvas>
  );
}
