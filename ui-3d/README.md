# ReelSense 3D UI kit

3D versions of ReelSense's own interface pieces, in a "Daylight Instrument" style: layered
machined plates (an aluminium tray under a porcelain or enamel cap) with small crisp bevels.
The colours come from `frontend/src/app/globals.css`: cobalt for primary actions, teal only for
AI activity, violet for Study, green/red for status. The icons are the site's own `Icon.tsx`
strokes swept into tubes.

The GLB files are in `frontend/public/models/ui/`, so the site loads them as `/models/ui/<file>`.

- **Rebuild:** run `node build.mjs` in this folder. It uses three.js from `frontend/node_modules`.
- **Preview:** run `python -m http.server 8766` in the project root, then open
  http://localhost:8766/ui-3d/gallery.html

## Conventions
- 1 unit = 100 CSS px. Every model faces +Z and is centred on the origin.
- No text inside any model. Labels stay in HTML for accessibility and translation, and bars stand
  in for text where a layout needs it.
- All materials are opaque PBR with no textures. Teal glow uses `emissive` plus
  `KHR_materials_emissive_strength`.
- One-shot clips are meant to be played with `LoopOnce` and `clampWhenFinished = true`. Reverse a
  hover by playing it with `timeScale = -1`.

## Files
| File | What it is | Nodes for code | Clips |
|---|---|---|---|
| `rs_button_primary.glb` | Cobalt pill button | `Cap`, `Halo` | Hover, Press |
| `rs_button_secondary.glb` | Porcelain pill with a cobalt rim | `Cap`, `Halo` | Hover, Press |
| `rs_button_ai.glb` | Teal AI button with a live dot | `Cap`, `Halo`, `LiveDot` | Hover, Press, Thinking |
| `rs_icon_keys.glb` | 18 keys: workspace modes and player controls | `Key_<icon>`, `Cap_<icon>` | Ripple |
| `rs_icons.glb` | Every Icon.tsx glyph as a 3D icon | `Icon_<name>` | – |
| `rs_video_frame.glb` | Cinematic video frame with a control dock | `Screen` (material `M_Screen`, UV 0–1), `Progress`, `Playhead`, `PlayKey`, `EvidencePin_*`, `AIChip` | Playback, Intro, Hover_Play, AI_Live |
| `rs_chapter_strip.glb` | Chapter timeline (5 segments) | `Chapter_0..4`, `Playhead` | Scan |
| `rs_pipeline.glb` | Ingest → Transcribe → Understand → Index → Ready | `Stage_<name>`, `Lit_<name>`, `RailFill_0..3` | Process |
| `rs_upload_tray.glb` | Upload drop zone | `Arrow`, `FileCard` | Idle, Drop |
| `rs_ai_answer.glb` | AI answer card with a citation | `QueryBar`, `Line_0..3`, `Citation` | Answer |
| `rs_flashcards.glb` | Violet flashcard stack | `Card_Front` | Flip, Float |
| `rs_status_badges.glb` | Processing / Ready / Failed | `Badge_<state>` | Pulse |
| `rs_logo_mark.glb` | ReelSense mark (frame + signal line) | `MarkSpin`, `MarkSignal` | Float, Signal |
| `rs_quiz_card.glb` | Quiz question with 4 options | `Option_0..3`, `CorrectMark`, `WrongMark` | Answer_Correct, Answer_Wrong |

## Examples
Playing the real video on the frame's screen (React Three Fiber):
```tsx
const { scene } = useGLTF('/models/ui/rs_video_frame.glb');
const video = useVideoTexture(src);
const screen = scene.getObjectByName('Screen') as THREE.Mesh;
(screen.material as THREE.MeshStandardMaterial).map = video;
(screen.material as THREE.MeshStandardMaterial).emissiveMap = video;
(screen.material as THREE.MeshStandardMaterial).emissive.set('#ffffff');
```

Driving the progress bar from the real playback time, instead of the Playback clip:
```ts
const progress = scene.getObjectByName('Progress')!;
const playhead = scene.getObjectByName('Playhead')!;
progress.scale.x = Math.max(0.001, currentTime / duration);
playhead.position.x = -1.35 + 3.1 * (currentTime / duration);
```
