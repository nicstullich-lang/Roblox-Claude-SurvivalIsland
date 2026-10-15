# Trailmark .308 — Roblox handoff package

> **To the Roblox coding chat:** this folder is a complete, self-describing model package from Nic's Blender pipeline. Everything you need to make the model *fully functional and realistic* in Survival Island is here: the mesh file, every moving part with its exact hinge and motion, seats, sockets, lights, collision proxies, physics data and gameplay rules. The machine-readable source of truth is `Trailmark308_Rig.json` (schema `survival-island-model/1`); this file explains it. Please read sections 3–4 before writing code.

**Trailmark .308** · category: **weapon** · bolt-action marksman rifle: slate receiver, olive precision stock, medium scope, folding bipod

## 1. Files
| File | What |
|---|---|
| `Trailmark308.fbx` | 27 meshes, 34172 triangles (largest 9864 — under Roblox's 20k limit), already in studs |
| `Trailmark308_Rig.json` | all data below, machine-readable |
| `Trailmark308_HANDOFF.md` | this guide |
| `previews/` | renders at rest and deployed |

## 2. Import into Studio
3D Importer (Home → Import / Avatar → Import 3D / File → Import 3D / Ctrl+M) with: **Scale Unit = Stud, Scale Factor = 1, World Forward = Front, World Up = Top, Set Pivot to Scene Origin ✔, Upload to Roblox ✔**.
Expected File Dimensions ≈ **0.49 × 1.51 × 5.10** studs (X × Y × Z). The import is a flat Model of MeshParts that are all grey/white, anchored-or-unanchored, unwelded and fully collidable — your setup code must fix that (§4).
Bounding-box centre after a correct import: `(0.04, -0.25, -0.84)` — use it to re-align the model if a different pivot option was used (`shift = expected_center − actual_center`).

## 3. Coordinates, units, names
- **1 stud = 0.28 m.** All `*_studs` values in the JSON are final Roblox numbers.
- Model space: origin on the bore axis directly above the trigger (all five weapons share this datum), **front = −Z (LookVector)**, up = +Y, **the model's RIGHT = +X**, its left = −X. (Blender source: front −Y, left +X; converted for you.)
- Mesh names: `RBX_<Group>_<Material>[_n]`. `<Group>` is either `Body` (static) or a moving group from §5. Group names contain underscores, so match them against the JSON `groups` keys (longest match first); `<Material>` has no digits; `_n` is a chunk index for big meshes.
- Every moving group's meshes were exported with the MeshPart pivot on the group's hinge, but Roblox recentres MeshParts — always use `pivot_studs` from the JSON, never the MeshPart position.

## 4. Recommended assembly (Roblox `Tool`)
1. Put every MeshPart in a **`Tool`**. Add an invisible, unanchored **`Handle`** part (about 0.4 × 0.4 × 0.4 studs, `CanCollide = false`) centred on point `TM308_Grip_Right` (§8). Set `Tool.Grip` so that point sits in the character's right hand. The weapon then points along the HumanoidRootPart LookVector, because the muzzle is −Z.
2. Static meshes (`RBX_Body_*`): `WeldConstraint` to the Handle. Visual parts: `CanCollide = CanTouch = CanQuery = false`, `Massless = true`, materials from §11 (or the SurfaceAppearance of §15).
3. **One Motor6D per moving group** (§5): Part0 = the parent group's joint (or the Handle for `parent_group = Body`), Part1 = an invisible joint part at `pivot_studs` (identity rotation); weld the group's meshes to that joint part. Create parents first (e.g. a bolt before its handle).
4. Animate on the client with `Motor6D.Transform` (`rotate` → `CFrame.fromAxisAngle(axis, math.rad(open * eased_progress))`, `translate` → `CFrame.new(axis * studs * eased_progress)`). Use the channels in §6: play `Cycle` 0→1→0 once per shot at the `rpm` of §12, `Trigger` while the button is held, `Reload` / `Charge` / covers in the order given in the channel rules. The server owns ammo, fire rate and hit detection.
5. Attachments at the points of §8: `Muzzle` (raycast origin + direction, flash, smoke), `Ejection` (shell casing emitter, direction given), `Aim` (camera position for aiming down sights), `Grip_Left` (support hand IK target), `MagWell` (where a new magazine enters).
6. Hide / show a group (e.g. the magazine during reload) by setting `LocalTransparencyModifier` on its meshes; groups of `kind = store` are meant to be hidden and shown like that.

## 5. Moving parts
Axes are the joint frame (= model axes at rest). An axis is a letter (X / Y / Z) or a unit vector `(x, y, z)` in model space for hinges that are not on a model axis — rotate about it with `CFrame.fromAxisAngle(axis, math.rad(angle))`. `open` is the value at channel state 1; `stage` is the slice of the channel's 0→1 progress during which this part moves (ease each slice with smoothstep). Types: rotate / translate (channel-driven), aim_yaw / aim_pitch / steer / control (player input, clamp to min..max), spin (continuous while its channel > 0), wheel (rolls on the ground), fixed (rides on its parent; `store` = a weapon that can be hidden / released).

| Group | Parent | Pivot (studs) | Motion | Channel · stage | What it is |
|---|---|---|---|---|---|
| `TM308_BipodLeg_L` | Body | (-0.08, -0.33, -2.16) | rotate -90 deg about X | Bipod · 0–1 | bipod leg: folded forward under the barrel; swings 90 deg down to stand the rifle on its bipod |
| `TM308_BipodLeg_R` | Body | (0.08, -0.33, -2.16) | rotate -90 deg about X | Bipod · 0–1 | bipod leg: folded forward under the barrel; swings 90 deg down to stand the rifle on its bipod |
| `TM308_Bolt` | Body | (-0.00, 0.00, -0.46) | slide +0.3571 studs along Z | Bolt · 0.4–1 | bolt: slides 0.100 m rearward after the handle is lifted (ejects through the port), then returns |
| `TM308_BoltHandle` | TM308_Bolt | (-0.00, 0.00, 0.19) | rotate +60 deg about Z | Bolt · 0–0.4 | bolt handle: lifts 60 deg (unlocks), first stage of the bolt cycle |
| `TM308_CheekRiser` | Body | (-0.00, 0.08, 1.24) | slide +0.05 studs along Y | CheekHeight · 0–1 | adjustable cheek riser: rises up to 0.014 m on its two posts (0 = lowest) |
| `TM308_Magazine` | Body | (-0.00, -0.09, -0.31) | slide -0.4286 studs along Y | Reload · 0–0.45 | box magazine: drops straight down 0.12 m |
| `TM308_Safety` | Body | (0.09, -0.07, 0.25) | rotate +20 deg about X | Safety · 0–1 | safety lever: rocks 20 deg forward to FIRE (rest = SAFE) |
| `TM308_Scope_PowerRing` | Body | (-0.00, 0.32, 0.44) | control about Z, 0 .. 120 deg, 240 deg/s | — | magnification ring: rotates with the zoom (3x at 0, 12x at 120 deg) |
| `TM308_Trigger` | Body | (-0.00, -0.19, 0.04) | rotate -10 deg about X | Trigger · 0–1 | trigger: crisp single-stage, 10 deg rearward |

## 6. Channels (states the server owns)
| Channel | Duration 0→1 | Moves | Rules |
|---|---|---|---|
| `Trigger` | 0.05 s | `TM308_Trigger` | — |
| `Bolt` | 0.85 s | `TM308_Bolt`, `TM308_BoltHandle` | play 0 -> 1 -> 0 after every shot (bolt action); TM308_BoltHandle rotates in stage 0-0.4, TM308_Bolt slides in stage 0.4-1 |
| `Reload` | 0.80 s | `TM308_Magazine` | — |
| `Bipod` | 0.50 s | `TM308_BipodLeg_L`, `TM308_BipodLeg_R` | deployed bipod: allow prone / rested fire with much less sway |
| `Safety` | 0.10 s | `TM308_Safety` | — |
| `CheekHeight` | 0.40 s | `TM308_CheekRiser` | — |

## 6b. Named poses (flight modes / test states)
| Pose | Channels at 1 | Inputs | On the ground | What it is |
|---|---|---|---|---|
| `bolt_open` | Bolt=1, Safety=1 | — | no | bolt handle up and back (ejecting / loading) |
| `bipod` | Bipod=1, Safety=1 | TM308_Scope_PowerRing=120 | no | bipod down, scope at max zoom |
| `reload` | Reload=1, Bolt=1 | — | no | magazine out, bolt open |

## 8. Points / sockets
| Point | Position (studs) | Attached to | Purpose |
|---|---|---|---|
| `TM308_Muzzle` | (-0.00, 0.00, -3.39) | Body | muzzle (direction=[-0.0, 0.0, -1.0], note=bullet origin + muzzle flash (2-port brake vents sideways)) |
| `TM308_Ejection` | (0.11, 0.03, -0.18) | Body | ejection (direction=[0.8653, 0.4581, 0.2036], note=the case is extracted when the bolt is pulled back (Bolt channel), not on firing) |
| `TM308_Grip_Right` | (-0.00, -0.57, 0.46) | Body | grip_right (note=firing hand on the thumbhole grip) |
| `TM308_Grip_Left` | (-0.00, -0.18, -1.57) | Body | grip_left (note=support hand under the forend) |
| `TM308_Aim` | (-0.00, 0.32, 0.94) | Body | aim_eye (direction=[-0.0, 0.0, -1.0], note=eye position at the scope eye relief (sight axis)) |
| `TM308_MagWell` | (-0.00, -0.23, -0.31) | Body | magwell (direction=[-0.0, -1.0, 0.0]) |
| `TM308_BipodFeet` | (-0.00, -1.05, -2.16) | Body | bipod_contact (note=ground contact of both feet when the Bipod channel = 1 (legs straight down)) |
| `TM308_Sling_Front` | (-0.16, -0.15, -2.09) | Body | sling |
| `TM308_Sling_Rear` | (-0.16, -0.62, 1.43) | Body | sling |

## 11. Materials (apply by the `<Material>` part of each mesh name)
| Material | Roblox material | Colour (RGB) | Transparency | Reflectance |
|---|---|---|---|---|
| Blackened | Metal | 38, 38, 40 | 0 | 0 |
| DarkSteel | Metal | 52, 53, 56 | 0 | 0 |
| Lens | Glass | 32, 44, 42 | 0.15 | 0.35 |
| MarkRed | SmoothPlastic | 118, 50, 38 | 0 | 0 |
| PaintSlate | SmoothPlastic | 68, 72, 77 | 0 | 0 |
| PolyBlack | Plastic | 34, 34, 36 | 0 | 0 |
| PolyOlive | Plastic | 76, 80, 54 | 0 | 0 |
| Rubber | Rubber | 30, 30, 30 | 0 | 0 |
| Steel | Metal | 128, 128, 125 | 0 | 0 |

## 12. Gameplay systems
### Weapon
- **kind:** marksman rifle (bolt action)
- **caliber:** .308 / 7.8x51 mm (fictional)
- **magazine:** 5
- **fire modes:** ['BOLT']
- **rpm:** 50
- **muzzle velocity mps:** 830
- **effective range studs:** 2857
- **reload s:** 3.0
- **damage hint:** high
- **recoil hint:** strong single kick, brake reduces it
- **aim:** 3-12x scope (zoom on the power ring); no iron sights
- **ammo item:** Ammo_308
- **scope:** {'magnification': [3, 12], 'eye_point': 'TM308_Aim', 'lens_front_y_m': -0.286, 'axis_z_m': 0.09}

## 13. Notes and rules
- Weapon origin = bore axis above the trigger; the muzzle points -Z in Roblox (LookVector).
- Bolt animation: TM308_BoltHandle (child of TM308_Bolt) rotates about the bolt axis, then TM308_Bolt slides.

## 14. Acceptance checklist (test in Studio before calling it done)
- [ ] Import size matches §2; installer reports 0 unknown mesh names.
- [ ] Every group in §5 moves about the right hinge, in the right direction, by the listed amount, in stage order.
- [ ] Nothing floats or clips at rest **and** fully deployed (the Blender checks found 0 floating parts in both).
- [ ] All server checks in place (who may use what, rate limits, clamped inputs) — the game is server-authoritative.
- [ ] Output window clean (no errors/warnings from the new scripts).

_Generated 2026-10-15 17:08 by the handoff exporter (`blender/common/handoff.py`). FBX re-import check: PASSED (9 pivots compared, 0 problems)._

## 15. Baked texture atlas (optional, recommended)
All meshes of this weapon share ONE UV layout, so one `SurfaceAppearance` (cloned into every MeshPart) gives the worn, weathered look from the Blender renders (edge wear, scratches, grime, dark recesses, red markings):

| Map | File | Colour space |
|---|---|---|
| ColorMap | `textures/Trailmark308_BaseColor.png` | sRGB |
| RoughnessMap | `textures/Trailmark308_Roughness.png` | linear |
| MetalnessMap | `textures/Trailmark308_Metalness.png` | linear |

Upload the three PNGs (Asset Manager > Bulk Import), create a SurfaceAppearance with the three IDs, and parent a clone to each MeshPart. With a SurfaceAppearance the MeshPart `Color` is ignored; without it, use the flat colours of section 11.

## 16. Previews
![34](Trailmark308_34.png) ![right](previews/Trailmark308_right.png) ![rear](previews/Trailmark308_left_rear34.png)

Pose previews (moving parts deployed): `previews/Trailmark308_pose_*.png`.
