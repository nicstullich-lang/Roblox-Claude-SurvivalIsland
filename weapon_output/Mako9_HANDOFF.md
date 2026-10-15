# Mako-9 — Roblox handoff package

> **To the Roblox coding chat:** this folder is a complete, self-describing model package from Nic's Blender pipeline. Everything you need to make the model *fully functional and realistic* in Survival Island is here: the mesh file, every moving part with its exact hinge and motion, seats, sockets, lights, collision proxies, physics data and gameplay rules. The machine-readable source of truth is `Mako9_Rig.json` (schema `survival-island-model/1`); this file explains it. Please read sections 3–4 before writing code.

**Mako-9** · category: **weapon** · compact 9 mm submachine gun with a side-folding stock and a tan side panel

## 1. Files
| File | What |
|---|---|
| `Mako9.fbx` | 17 meshes, 30286 triangles (largest 7986 — under Roblox's 20k limit), already in studs |
| `Mako9_Rig.json` | all data below, machine-readable |
| `Mako9_HANDOFF.md` | this guide |
| `previews/` | renders at rest and deployed |

## 2. Import into Studio
3D Importer (Home → Import / Avatar → Import 3D / File → Import 3D / Ctrl+M) with: **Scale Unit = Stud, Scale Factor = 1, World Forward = Front, World Up = Top, Set Pivot to Scene Origin ✔, Upload to Roblox ✔**.
Expected File Dimensions ≈ **0.53 × 1.30 × 3.30** studs (X × Y × Z). The import is a flat Model of MeshParts that are all grey/white, anchored-or-unanchored, unwelded and fully collidable — your setup code must fix that (§4).
Bounding-box centre after a correct import: `(0.05, -0.37, -0.81)` — use it to re-align the model if a different pivot option was used (`shift = expected_center − actual_center`).

## 3. Coordinates, units, names
- **1 stud = 0.28 m.** All `*_studs` values in the JSON are final Roblox numbers.
- Model space: origin on the bore axis directly above the trigger (all five weapons share this datum), **front = −Z (LookVector)**, up = +Y, **the model's RIGHT = +X**, its left = −X. (Blender source: front −Y, left +X; converted for you.)
- Mesh names: `RBX_<Group>_<Material>[_n]`. `<Group>` is either `Body` (static) or a moving group from §5. Group names contain underscores, so match them against the JSON `groups` keys (longest match first); `<Material>` has no digits; `_n` is a chunk index for big meshes.
- Every moving group's meshes were exported with the MeshPart pivot on the group's hinge, but Roblox recentres MeshParts — always use `pivot_studs` from the JSON, never the MeshPart position.

## 4. Recommended assembly (Roblox `Tool`)
1. Put every MeshPart in a **`Tool`**. Add an invisible, unanchored **`Handle`** part (about 0.4 × 0.4 × 0.4 studs, `CanCollide = false`) centred on point `MAKO9_Grip_Right` (§8). Set `Tool.Grip` so that point sits in the character's right hand. The weapon then points along the HumanoidRootPart LookVector, because the muzzle is −Z.
2. Static meshes (`RBX_Body_*`): `WeldConstraint` to the Handle. Visual parts: `CanCollide = CanTouch = CanQuery = false`, `Massless = true`, materials from §11 (or the SurfaceAppearance of §15).
3. **One Motor6D per moving group** (§5): Part0 = the parent group's joint (or the Handle for `parent_group = Body`), Part1 = an invisible joint part at `pivot_studs` (identity rotation); weld the group's meshes to that joint part. Create parents first (e.g. a bolt before its handle).
4. Animate on the client with `Motor6D.Transform` (`rotate` → `CFrame.fromAxisAngle(axis, math.rad(open * eased_progress))`, `translate` → `CFrame.new(axis * studs * eased_progress)`). Use the channels in §6: play `Cycle` 0→1→0 once per shot at the `rpm` of §12, `Trigger` while the button is held, `Reload` / `Charge` / covers in the order given in the channel rules. The server owns ammo, fire rate and hit detection.
5. Attachments at the points of §8: `Muzzle` (raycast origin + direction, flash, smoke), `Ejection` (shell casing emitter, direction given), `Aim` (camera position for aiming down sights), `Grip_Left` (support hand IK target), `MagWell` (where a new magazine enters).
6. Hide / show a group (e.g. the magazine during reload) by setting `LocalTransparencyModifier` on its meshes; groups of `kind = store` are meant to be hidden and shown like that.

## 5. Moving parts
Axes are the joint frame (= model axes at rest). An axis is a letter (X / Y / Z) or a unit vector `(x, y, z)` in model space for hinges that are not on a model axis — rotate about it with `CFrame.fromAxisAngle(axis, math.rad(angle))`. `open` is the value at channel state 1; `stage` is the slice of the channel's 0→1 progress during which this part moves (ease each slice with smoothstep). Types: rotate / translate (channel-driven), aim_yaw / aim_pitch / steer / control (player input, clamp to min..max), spin (continuous while its channel > 0), wheel (rolls on the ground), fixed (rides on its parent; `store` = a weapon that can be hidden / released).

| Group | Parent | Pivot (studs) | Motion | Channel · stage | What it is |
|---|---|---|---|---|---|
| `MAKO9_Bolt` | Body | (-0.00, 0.08, -0.26) | slide +0.2143 studs along Z | Cycle · 0–1 | bolt: recoils 0.060 m rearward and returns once per shot (visible through the ejection port) |
| `MAKO9_ChargingHandle` | Body | (-0.09, 0.10, -0.99) | slide +0.4 studs along Z | Charge · 0–1 | cocking handle: pulled 0.112 m rearward along the slot to cock, then released |
| `MAKO9_Magazine` | Body | (-0.00, -0.14, -0.44) | slide +0.6429 studs along (-0.000, -0.995, -0.100) | Reload · 0–0.45 | magazine: drops out of the magwell along its insertion line (0.18 m) |
| `MAKO9_Selector` | Body | (-0.10, -0.19, 0.26) | control about X, 0 .. 180 deg, 600 deg/s | — | fire selector: SAFE = 0 deg (forward), SEMI = -90 (up), AUTO = -180 (rearward) |
| `MAKO9_Stock` | Body | (0.12, -0.02, 0.82) | rotate -180 deg about Y | StockFold · 0–1 | side-folding stock: modelled folded along the right side; swings 180 deg outward and back to extend |
| `MAKO9_Trigger` | Body | (-0.00, -0.20, -0.02) | rotate -14 deg about X | Trigger · 0–1 | trigger: pivots 14 deg rearward to fire |

## 6. Channels (states the server owns)
| Channel | Duration 0→1 | Moves | Rules |
|---|---|---|---|
| `Trigger` | 0.05 s | `MAKO9_Trigger` | — |
| `Cycle` | 0.04 s | `MAKO9_Bolt` | — |
| `Charge` | 0.30 s | `MAKO9_ChargingHandle` | drive Cycle together with Charge while cocking |
| `Reload` | 0.80 s | `MAKO9_Magazine` | — |
| `StockFold` | 0.45 s | `MAKO9_Stock` | folded stock: lower accuracy, faster handling; extended: shoulder-fired |

## 6b. Named poses (flight modes / test states)
| Pose | Channels at 1 | Inputs | On the ground | What it is |
|---|---|---|---|---|
| `fire` | Trigger=1, Cycle=1, StockFold=1 | — | no | stock out, trigger pulled, bolt back |
| `reload` | Reload=1, Charge=1, Cycle=1 | — | no | magazine out, handle and bolt back |
| `stock_extended` | StockFold=1 | — | no | stock unfolded |

## 8. Points / sockets
| Point | Position (studs) | Attached to | Purpose |
|---|---|---|---|
| `MAKO9_Muzzle` | (-0.00, 0.00, -2.46) | Body | muzzle (direction=[-0.0, 0.0, -1.0], note=bullet origin + muzzle flash (4-prong flash hider)) |
| `MAKO9_Ejection` | (0.13, 0.08, -0.09) | Body | ejection (direction=[0.798, 0.5486, 0.2494], note=spent cases leave the ejection port here (right side, above the folded stock)) |
| `MAKO9_Grip_Right` | (-0.00, -0.46, 0.38) | Body | grip_right (note=firing hand on the pistol grip) |
| `MAKO9_Grip_Left` | (-0.00, -0.11, -1.41) | Body | grip_left (note=support hand on the handguard, behind the hand stop) |
| `MAKO9_Aim` | (-0.00, 0.24, 0.54) | Body | aim_eye (direction=[-0.0, 0.0, -1.0], note=eye position behind the aperture rear sight) |
| `MAKO9_MagWell` | (-0.00, -0.36, -0.44) | Body | magwell (direction=[-0.0, -0.995, -0.0995]) |
| `MAKO9_Sling` | (-0.20, 0.17, 0.59) | Body | sling |

## 11. Materials (apply by the `<Material>` part of each mesh name)
| Material | Roblox material | Colour (RGB) | Transparency | Reflectance |
|---|---|---|---|---|
| Blackened | Metal | 38, 38, 40 | 0 | 0 |
| DarkSteel | Metal | 52, 53, 56 | 0 | 0 |
| Graphite | Metal | 74, 76, 80 | 0 | 0 |
| MarkRed | SmoothPlastic | 118, 50, 38 | 0 | 0 |
| PolyBlack | Plastic | 34, 34, 36 | 0 | 0 |
| PolyTan | Plastic | 138, 122, 94 | 0 | 0 |
| Rubber | Rubber | 30, 30, 30 | 0 | 0 |
| Steel | Metal | 128, 128, 125 | 0 | 0 |

## 12. Gameplay systems
### Weapon
- **kind:** submachine gun
- **caliber:** 9x21 mm (fictional)
- **magazine:** 32
- **fire modes:** ['SAFE', 'SEMI', 'AUTO']
- **rpm:** 900
- **muzzle velocity mps:** 390
- **effective range studs:** 536
- **reload s:** 1.9
- **damage hint:** low-medium
- **recoil hint:** low; more spread with the stock folded
- **aim:** aperture rear + hooded front post
- **ammo item:** Ammo_9x21

## 13. Notes and rules
- Weapon origin = bore axis above the trigger; the muzzle points -Z in Roblox (LookVector).
- The stock group (MAKO9_Stock) rotates about a vertical hinge pin at its pivot; folded = rest.

## 14. Acceptance checklist (test in Studio before calling it done)
- [ ] Import size matches §2; installer reports 0 unknown mesh names.
- [ ] Every group in §5 moves about the right hinge, in the right direction, by the listed amount, in stage order.
- [ ] Nothing floats or clips at rest **and** fully deployed (the Blender checks found 0 floating parts in both).
- [ ] All server checks in place (who may use what, rate limits, clamped inputs) — the game is server-authoritative.
- [ ] Output window clean (no errors/warnings from the new scripts).

_Generated 2026-10-15 17:08 by the handoff exporter (`blender/common/handoff.py`). FBX re-import check: PASSED (6 pivots compared, 0 problems)._

## 15. Baked texture atlas (optional, recommended)
All meshes of this weapon share ONE UV layout, so one `SurfaceAppearance` (cloned into every MeshPart) gives the worn, weathered look from the Blender renders (edge wear, scratches, grime, dark recesses, red markings):

| Map | File | Colour space |
|---|---|---|
| ColorMap | `textures/Mako9_BaseColor.png` | sRGB |
| RoughnessMap | `textures/Mako9_Roughness.png` | linear |
| MetalnessMap | `textures/Mako9_Metalness.png` | linear |

Upload the three PNGs (Asset Manager > Bulk Import), create a SurfaceAppearance with the three IDs, and parent a clone to each MeshPart. With a SurfaceAppearance the MeshPart `Color` is ignored; without it, use the flat colours of section 11.

## 16. Previews
![34](Mako9_34.png) ![right](previews/Mako9_right.png) ![rear](previews/Mako9_left_rear34.png)

Pose previews (moving parts deployed): `previews/Mako9_pose_*.png`.
