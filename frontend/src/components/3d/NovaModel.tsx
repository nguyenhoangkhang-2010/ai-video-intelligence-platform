"use client";

import { useAnimations, useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { SkeletonUtils } from "three-stdlib";

import { NOVA_CLIPS_OWN_GAZE, NOVA_LOOP_CLIPS, NOVA_STATE_CLIP, type NovaState } from "@/components/3d/novaClips";
import { isPointerActive } from "@/lib/globalPointer";

const MODEL_PATH = "/models/nova.glb";

// Bounded look-at limits (radians) - small, deliberate glances that
// can never accumulate into a full turn, since they're recomputed
// fresh from the damped pointer position every frame rather than
// added to anything. The head carries slightly more range than the
// eyes, matching how a real gaze leads with the eyes and only
// partially follows with the head.
const HEAD_YAW_LIMIT = THREE.MathUtils.degToRad(14);
const HEAD_PITCH_LIMIT = THREE.MathUtils.degToRad(8);
const EYE_YAW_LIMIT = THREE.MathUtils.degToRad(10);
const EYE_PITCH_LIMIT = THREE.MathUtils.degToRad(6);

interface NovaModelProps {
  state: NovaState;
  /** Cursor/head-tracking layer - off in reduced-motion mode. */
  trackPointer?: boolean;
  onGestureEnd?: (state: NovaState) => void;
  /**
   * A page-wide pointer position (see lib/globalPointer.ts) to look
   * toward instead of R3F's own canvas-relative `pointer` - used by
   * the single ambient Nova instance so it reacts to the cursor
   * anywhere on screen, not only while the cursor happens to sit over
   * its own small canvas.
   */
  externalPointer?: { x: number; y: number } | null;
}

/**
 * Adapted from nova-3d/Nova.jsx (the prototype shipped alongside
 * nova.glb) - the layered animation approach there is already
 * correct against the real rig, so this keeps its structure rather
 * than reinventing it: Float runs as an always-on base layer, Blink
 * fires on a random timer as its own layer, a semantic `state` prop
 * crossfades the full-body gesture layer (falling back to
 * Idle_Breathe when a one-shot gesture finishes), and a look layer
 * rotates the real Head/Eye_L/Eye_R bones toward the pointer after
 * the mixer updates each frame.
 */
export function NovaModel({ state, trackPointer = true, onGestureEnd, externalPointer = null }: NovaModelProps) {
  const group = useRef<THREE.Group>(null);
  const { scene: sharedScene, animations } = useGLTF(MODEL_PATH);

  // useGLTF caches and shares ONE scene graph across every consumer of
  // this model - and several can be mounted at once (the ambient
  // corner instance plus a page's own hero Nova on Landing/Upload
  // Studio/the workspace). Two independent AnimationMixers driving the
  // literal same Head/Eye_L/Eye_R/Root bone objects stomp on each
  // other every frame - that collision, not any single instance's own
  // math, was the actual cause of Nova's "spinning" bug. Each instance
  // now gets its own cloned rig so its mixer and look layer only ever
  // touch bones nothing else can reach. Plain Object3D.clone() would
  // NOT work here - it doesn't re-bind SkinnedMesh -> Skeleton -> bone
  // references, so SkeletonUtils.clone is required.
  const scene = useMemo(() => SkeletonUtils.clone(sharedScene) as THREE.Group, [sharedScene]);

  const { actions, mixer } = useAnimations(animations, group);
  const current = useRef<THREE.AnimationAction | null>(null);
  const look = useRef(new THREE.Vector2());

  // Base layers: Float always on, Blink on a random timer. Every
  // other clip is a one-shot gesture that clamps on its last frame
  // until the gesture layer below crossfades it back to idle.
  useEffect(() => {
    for (const [name, action] of Object.entries(actions)) {
      if (!action) continue;
      if (!NOVA_LOOP_CLIPS.includes(name as never)) {
        action.setLoop(THREE.LoopOnce, 1);
        action.clampWhenFinished = true;
      }
    }

    actions.Float?.play();

    let timeoutId: ReturnType<typeof setTimeout>;
    const scheduleBlink = () => {
      timeoutId = setTimeout(() => {
        actions.Blink?.reset().play();
        scheduleBlink();
      }, 2500 + Math.random() * 3500);
    };
    scheduleBlink();

    return () => clearTimeout(timeoutId);
  }, [actions]);

  // Gesture layer: crossfade to whatever clip the current semantic
  // state maps to. One-shot gestures (Wave/Think/Greet/Excited/Nod/
  // Look_At_Camera) fall back to Idle_Breathe when they finish;
  // looping states (Idle_Breathe/Look_Around/Think) just keep going.
  useEffect(() => {
    const clipName = NOVA_STATE_CLIP[state];
    const next = actions[clipName];
    if (!next) return;

    next.reset().setEffectiveWeight(1).play();
    if (current.current && current.current !== next) {
      current.current.crossFadeTo(next, 0.35, true);
    }
    current.current = next;

    const handleFinished = (event: { action: THREE.AnimationAction }) => {
      if (event.action !== next) return;
      const idle = actions.Idle_Breathe;
      if (!idle) return;
      idle.reset().play();
      next.crossFadeTo(idle, 0.35, true);
      current.current = idle;
      onGestureEnd?.(state);
    };

    mixer.addEventListener("finished", handleFinished);
    return () => mixer.removeEventListener("finished", handleFinished);
  }, [state, actions, mixer, onGestureEnd]);

  // Look layer: head and eyes follow the pointer - R3F's own
  // per-frame, canvas-relative pointer by default, or a page-wide
  // `externalPointer` when supplied (the ambient instance; a mutable
  // object updated in place by lib/globalPointer.ts, read fresh every
  // frame here rather than via React state - avoids a re-render on
  // every mouse move), applied after the mixer each frame. Skipped
  // entirely in reduced-motion mode.
  //
  // Every real gesture clip (verified against the GLB directly) keys
  // Head/Eye_L/Eye_R itself, so the mixer's update() - which drei's
  // useAnimations already runs in its own useFrame, registered before
  // this one, i.e. earlier in the same tick - has already written an
  // absolute, freshly authored value into these bones by the time this
  // runs. Composing one small, angle-bounded offset on top of that per
  // frame (never adding to what we ourselves wrote last frame) is what
  // keeps this from ever compounding into a runaway spin.
  //
  // Two clips are exempt: Look_At_Camera centers the gaze instead of
  // following the pointer (it's the "Nova notices you" reaction), and
  // Look_Around/Think already tell their own deliberate story with the
  // eyes, so the procedural layer steps aside entirely rather than
  // visibly fighting them.
  useFrame(({ pointer }, delta) => {
    if (!trackPointer) return;

    const gesture = current.current;
    const clipName = gesture?.getClip().name as (typeof NOVA_CLIPS_OWN_GAZE)[number] | undefined;
    if (clipName && NOVA_CLIPS_OWN_GAZE.includes(clipName)) return;

    const head = scene.getObjectByName("Head");
    const eyeL = scene.getObjectByName("Eye_L");
    const eyeR = scene.getObjectByName("Eye_R");
    if (!head || !eyeL || !eyeR) return;

    const isLookingAtCamera = gesture === actions.Look_At_Camera;
    // externalPointer has a real "cursor left the window" signal
    // (lib/globalPointer.ts); R3F's own canvas-relative `pointer`
    // doesn't, so it's trusted as-is for the full-bleed hero instances.
    const pointerIsActive = externalPointer === null || isPointerActive();
    const target = isLookingAtCamera || !pointerIsActive ? { x: 0, y: 0 } : externalPointer ?? pointer;

    look.current.lerp(target, 1 - Math.exp(-8 * delta));
    const { x, y } = look.current;

    const headOffset = new THREE.Quaternion().setFromEuler(
      new THREE.Euler(-y * HEAD_PITCH_LIMIT, x * HEAD_YAW_LIMIT, 0),
    );
    head.quaternion.multiply(headOffset);

    const eyeOffset = new THREE.Quaternion().setFromEuler(
      new THREE.Euler(-y * EYE_PITCH_LIMIT, x * EYE_YAW_LIMIT, 0),
    );
    eyeL.quaternion.multiply(eyeOffset);
    eyeR.quaternion.multiply(eyeOffset);
  });

  return <primitive ref={group} object={scene} />;
}

useGLTF.preload(MODEL_PATH);
