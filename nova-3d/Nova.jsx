// React Three Fiber component for nova.glb.
// Needs: three, @react-three/fiber, @react-three/drei. Put nova.glb in /public.
//
// <Canvas camera={{ position: [0, 0.6, 2.6], fov: 30 }}>
//   <Environment preset="studio" />
//   <Nova clip={clip} />   // clip: 'Idle_Breathe' | 'Wave' | 'Think' | 'Greet' | 'Excited' | 'Nod' | 'Look_At_Camera' | 'Look_Around'
// </Canvas>
import { useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF, useAnimations } from '@react-three/drei';
import * as THREE from 'three';

const LOOPS = ['Idle_Breathe', 'Look_Around', 'Think', 'Float'];

export function Nova({ clip = 'Idle_Breathe', onClipEnd, ...props }) {
  const group = useRef();
  const { scene, animations } = useGLTF('/nova.glb');
  const { actions, mixer } = useAnimations(animations, group);
  const current = useRef(null);
  const look = useRef(new THREE.Vector2());

  // Base layers: Float always on, Blink on a random timer.
  useEffect(() => {
    for (const [name, a] of Object.entries(actions)) {
      if (!LOOPS.includes(name)) { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; }
    }
    actions.Float.play();
    let t;
    const blink = () => { t = setTimeout(() => { actions.Blink.reset().play(); blink(); }, 2500 + Math.random() * 3500); };
    blink();
    return () => clearTimeout(t);
  }, [actions]);

  // Gesture layer: crossfade to the requested clip; one-shot clips fall back to Idle_Breathe.
  useEffect(() => {
    const next = actions[clip];
    if (!next) return;
    next.reset().setEffectiveWeight(1).play();
    if (current.current && current.current !== next) current.current.crossFadeTo(next, 0.35, true);
    current.current = next;
    const done = (e) => {
      if (e.action !== next) return;
      const idle = actions.Idle_Breathe;
      idle.reset().play();
      next.crossFadeTo(idle, 0.35, true);
      current.current = idle;
      onClipEnd?.(clip);
    };
    mixer.addEventListener('finished', done);
    return () => mixer.removeEventListener('finished', done);
  }, [clip, actions, mixer, onClipEnd]);

  // Look layer: head and eyes follow the pointer, applied after the mixer each frame.
  const q = new THREE.Quaternion();
  const e = new THREE.Euler();
  useFrame(({ pointer }, dt) => {
    const target = clip === 'Look_At_Camera' ? new THREE.Vector2() : pointer;
    look.current.lerp(target, 1 - Math.exp(-8 * dt));
    const { x, y } = look.current;
    scene.getObjectByName('Head').quaternion.multiply(q.setFromEuler(e.set(-y * 0.3, x * 0.55, 0)));
    q.setFromEuler(e.set(-y * 0.18, x * 0.3, 0));
    scene.getObjectByName('Eye_L').quaternion.multiply(q);
    scene.getObjectByName('Eye_R').quaternion.multiply(q);
  });

  return <primitive ref={group} object={scene} {...props} />;
}

useGLTF.preload('/nova.glb');
