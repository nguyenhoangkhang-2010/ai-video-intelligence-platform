# Nova: AI mascot (GLB)

- `nova.glb`: the model (glTF 2.0 binary, 1.0 m tall, +Y up, facing +Z, origin between the soles)
- `build.mjs`: the script that generates the model. Edit it, then run `node build.mjs` to rebuild
- `index.html`: viewer page. Run `python -m http.server 8765` in this folder and open http://localhost:8765
- `Nova.jsx`: React Three Fiber component (drei `useGLTF` + `useAnimations`)

## Contents
| | |
|---|---|
| Triangles | 22,652 |
| Meshes | Nova_Body, Nova_Suit, Nova_Visor, Nova_Signal, Nova_Face, Nova_Cheeks (6 draw calls) |
| Materials | M_Shell, M_Suit, M_Visor, M_Signal (emissive), M_Cheek, all PBR with no textures |
| Bones | 32: Root, Hips, Spine…Spine2, Chest, Neck, Head, Eye_L/R, Antenna, Left/Right Shoulder-Arm-ForeArm-Hand-Thumb, UpLeg-Leg-Foot-ToeBase |
| Morph targets | Nova_Face: Blink_L, Blink_R, Eyes_Happy, Eyes_Wide, Eyes_Squint, Brow_Raise_L, Brow_Raise_R, Mouth_Smile, Mouth_Open, Mouth_Side. Nova_Cheeks: Cheek_Glow |
| Clips | Idle_Breathe, Blink, Look_Around, Look_At_Camera, Wave, Think, Greet, Excited, Nod, Float |

## Using the clips
- `Float` (Root bone) and `Blink` (Eye bone scale) run as separate layers alongside everything else.
- The other clips all drive the full body pose, so switch between them with `crossFadeTo(next, 0.35)`.
- The eyes and head follow the cursor by rotating the `Head`, `Eye_L` and `Eye_R` bones after `mixer.update()`.
