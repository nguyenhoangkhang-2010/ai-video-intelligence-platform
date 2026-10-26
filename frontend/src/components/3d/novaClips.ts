/**
 * Nova's real, verified animation clips (nova-3d/nova.glb — confirmed
 * by directly parsing the GLB's glTF JSON chunk, not assumed from the
 * prototype's README alone): Idle_Breathe, Blink, Look_Around,
 * Look_At_Camera, Wave, Think, Greet, Excited, Nod, Float.
 *
 * Every other component in the app talks to Nova through the
 * semantic `NovaState` union below, never a raw clip name - this is
 * the one place a semantic state maps to a real clip, so a future
 * re-export of the GLB with renamed clips only requires editing this
 * file. No state here maps to a clip that doesn't exist in the file
 * (see the audit note next to each one).
 */
export type NovaClipName =
  | "Idle_Breathe"
  | "Blink"
  | "Look_Around"
  | "Look_At_Camera"
  | "Wave"
  | "Think"
  | "Greet"
  | "Excited"
  | "Nod"
  | "Float";

/**
 * Semantic states the rest of the app actually needs. Deliberately
 * NOT one-to-one with the raw clip list above - e.g. there is no
 * "error"/"sad" clip in the GLB, so an error state falls back to
 * Idle_Breathe rather than inventing one.
 */
export type NovaState = "idle" | "greeting" | "thinking" | "searching" | "success" | "excited" | "attention";

export const NOVA_STATE_CLIP: Record<NovaState, NovaClipName> = {
  idle: "Idle_Breathe",
  greeting: "Greet",
  thinking: "Think",
  searching: "Look_Around",
  // No dedicated "success" clip exists - Nod is the closest real
  // gesture to a calm acknowledgement, used instead of inventing one.
  success: "Nod",
  excited: "Excited",
  // A brief, real reaction to a hover on an AI-marked element
  // elsewhere on the page - Nova notices, doesn't perform.
  attention: "Look_At_Camera",
};

/** Clips that loop continuously as base layers, never one-shot. */
export const NOVA_LOOP_CLIPS: readonly NovaClipName[] = ["Idle_Breathe", "Look_Around", "Think", "Float"];

/**
 * Clips whose own keyframes already tell a deliberate story with the
 * head/eyes (verified against the real GLB - every gesture clip keys
 * Head/Eye_L/Eye_R, but these two are semantically ABOUT looking).
 * The procedural cursor-tracking layer in NovaModel.tsx skips these
 * bones entirely while one of them is active, so it never doubles up
 * on/visibly fights the clip's own gaze motion.
 */
export const NOVA_CLIPS_OWN_GAZE: readonly NovaClipName[] = ["Look_Around", "Think"];
