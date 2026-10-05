# XR-77 "Umbra" — Roblox handoff package

> **To the Roblox coding chat:** this folder is a complete, self-describing model package from Nic's Blender pipeline. Everything you need to make the model *fully functional and realistic* in Survival Island is here: the mesh file, every moving part with its exact hinge and motion, seats, sockets, lights, collision proxies, physics data and gameplay rules. The machine-readable source of truth is `XR77_Umbra_Rig.json` (schema `survival-island-model/1`); this file explains it. Please read sections 3–4 before writing code.

**XR-77 "Umbra"** · category: **aircraft** · Classified strike-reconnaissance VTOL fighter (original design, admin-only): SR-71-style chined Mach 3+ airframe with stealth shaping, adaptive-cycle engines with spiked inlets, hybrid-electric lift fan and swivel nozzles for VTOL, drooping wing tips for high-speed flight, internal + external weapons.

## 1. Files
| File | What |
|---|---|
| `XR77_Umbra.fbx` | 355 meshes, 287676 triangles (largest 15000 — under Roblox's 20k limit), already in studs |
| `XR77_Umbra_Rig.json` | all data below, machine-readable |
| `HANDOFF.md` | this guide |
| `previews/` | renders at rest and deployed |

## 2. Import into Studio
3D Importer (Home → Import / Avatar → Import 3D / File → Import 3D / Ctrl+M) with: **Scale Unit = Stud, Scale Factor = 1, World Forward = Front, World Up = Top, Set Pivot to Scene Origin ✔, Upload to Roblox ✔**.
Expected File Dimensions ≈ **55.11 × 18.39 × 87.82** studs (X × Y × Z). The import is a flat Model of MeshParts that are all grey/white, anchored-or-unanchored, unwelded and fully collidable — your setup code must fix that (§4).
Bounding-box centre after a correct import: `(0.00, 9.19, -2.80)` — use it to re-align the model if a different pivot option was used (`shift = expected_center − actual_center`).

## 3. Coordinates, units, names
- **1 stud = 0.28 m.** All `*_studs` values in the JSON are final Roblox numbers.
- Model space: origin on the ground under the model's centre, **front = −Z (LookVector)**, up = +Y, **the model's RIGHT = +X**, its left = −X. (Blender source: front −Y, left +X; converted for you.)
- Mesh names: `RBX_<Group>_<Material>[_n]`. `<Group>` is either `Body` (static) or a moving group from §5. Group names contain underscores, so match them against the JSON `groups` keys (longest match first); `<Material>` has no digits; `_n` is a chunk index for big meshes.
- Every moving group's meshes were exported with the MeshPart pivot on the group's hinge, but Roblox recentres MeshParts — always use `pivot_studs` from the JSON, never the MeshPart position.

## 4. Recommended assembly
1. Invisible, unanchored **root part** (PrimaryPart) — for vehicles a heavy chassis box low in the hull (`RootPriority` high); set `Model.WorldPivot` = ground origin so `PivotTo` places it on the ground.
2. All visual MeshParts: `CanCollide/CanTouch/CanQuery = false`, `Massless = true`, materials from §11, `CollisionFidelity = Box`, `CastShadow = false` for Neon/Glass.
3. One invisible **joint part per moving group** at `pivot_studs` (identity rotation), connected to its parent group's joint part (or the root for `parent_group = Body`) with a **Motor6D**: `C0 = Part0.CFrame:ToObjectSpace(joint.CFrame)`, `C1 = identity`. Weld the group's meshes to its joint part. Create joints in parent-first order.
4. Animate on clients by setting `Motor6D.Transform` (`rotate` → `CFrame.Angles` about the listed axis, `translate` → `CFrame.new(axis * studs)`); keep the authoritative state on the server as attributes (channel targets 0/1, aim angles). The joint frame is model-aligned at rest, so axes in §5 are exact.
5. Collision: use the boxes in §9 (invisible, welded, `CanCollide`/`CanQuery` true) instead of mesh collision.
6. Physics wheels (vehicles): invisible cylinder parts at the wheel centres on suspension constraints; weld the wheel groups' meshes to them (§10). Use collision groups so wheels never touch the body boxes.
7. Set `Model.ModelStreamingMode = Atomic` (the map uses streaming).

## 5. Moving parts
Axes are the joint frame (= model axes at rest). An axis is a letter (X / Y / Z) or a unit vector `(x, y, z)` in model space for hinges that are not on a model axis — rotate about it with `CFrame.fromAxisAngle(axis, math.rad(angle))`. `open` is the value at channel state 1; `stage` is the slice of the channel's 0→1 progress during which this part moves (ease each slice with smoothstep). Types: rotate / translate (channel-driven), aim_yaw / aim_pitch / steer / control (player input, clamp to min..max), spin (continuous while its channel > 0), wheel (rolls on the ground), fixed (rides on its parent; `store` = a weapon that can be hidden / released).

| Group | Parent | Pivot (studs) | Motion | Channel · stage | What it is |
|---|---|---|---|---|---|
| `Aileron_L` | Wingtip_L | (-22.50, 7.50, 23.93) | control about X, -25 .. 25 deg, 120 deg/s | — | aileron (roll): + = trailing edge up (Blender X) |
| `Aileron_R` | Wingtip_R | (22.50, 7.50, 23.93) | control about X, -25 .. 25 deg, 120 deg/s | — | aileron (roll): + = trailing edge up (Blender X) |
| `AuxInlet_L` | Body | (-8.75, 10.09, -6.95) | rotate +35 deg about X | VTOL · 0–0.4 | VTOL auxiliary inlet door: rear-hinged, opens 35 deg for extra hover airflow |
| `AuxInlet_R` | Body | (8.75, 10.09, -6.95) | rotate +35 deg about X | VTOL · 0–0.4 | VTOL auxiliary inlet door: rear-hinged, opens 35 deg for extra hover airflow |
| `Avionics_Door_L` | Body | (-2.36, 8.39, -28.39) | rotate -100 deg about (-0.000, 0.030, 1.000) | Service · 0–1 | avionics bay door: hinged along its top edge, lifts up |
| `Avionics_Door_R` | Body | (2.36, 8.39, -28.39) | rotate +100 deg about (-0.000, 0.030, 1.000) | Service · 0–1 | avionics bay door: hinged along its top edge, lifts up |
| `BellyTurret_Barrels_L` | BellyTurret_Pitch | (-1.18, 5.75, 17.32) | spin about Z at 55 rad/s | BellyTurret · 0.9–1 | belly turret rotary gun (spins while firing) |
| `BellyTurret_Barrels_R` | BellyTurret_Pitch | (1.18, 5.75, 17.32) | spin about Z at 55 rad/s | BellyTurret · 0.9–1 | belly turret rotary gun (spins while firing) |
| `BellyTurret_Lift` | Body | (-0.00, 8.11, 19.46) | slide -2.8571 studs along Y | BellyTurret · 0.35–1 | turret elevator: lowers the gun turret out of the belly |
| `BellyTurret_Pitch` | BellyTurret_Yaw | (-0.00, 5.75, 19.46) | aim pitch about X, -90 .. 10 deg, 90 deg/s | — | belly turret gun elevation (+ = guns down, Blender X) |
| `BellyTurret_Yaw` | BellyTurret_Lift | (-0.00, 6.07, 19.46) | aim yaw about Y, unlimited, 120 deg/s | — | belly turret traverse (360 deg) |
| `Canopy` | Body | (-0.00, 10.93, -18.39) | rotate +48 deg about X | Canopy · 0–1 | one-piece canopy, rear-hinged: opens up 48 deg (front rises) |
| `ChineCam_Door_L` | Body | (-1.99, 5.69, -28.04) | rotate +100 deg about Z | Recon · 0–0.4 | chine camera bay door: swings down |
| `ChineCam_Door_R` | Body | (1.99, 5.69, -28.04) | rotate -100 deg about Z | Recon · 0–0.4 | chine camera bay door: swings down |
| `DIRCM_Bot_Head` | DIRCM_Bot_Lift | (-0.00, 5.16, 24.46) | aim yaw about Y, unlimited, 360 deg/s | — | laser countermeasure head: tracks incoming missiles (360 deg) |
| `DIRCM_Bot_Lift` | Body | (-0.00, 5.66, 24.46) | slide -0.6071 studs along Y | Countermeasures · 0.2–0.8 | DIRCM turret: rises out of its flush well |
| `DIRCM_Top_Head` | DIRCM_Top_Lift | (-0.00, 9.77, 22.50) | aim yaw about Y, unlimited, 360 deg/s | — | laser countermeasure head: tracks incoming missiles (360 deg) |
| `DIRCM_Top_Lift` | Body | (-0.00, 9.27, 22.50) | slide +0.6071 studs along Y | Countermeasures · 0.2–0.8 | DIRCM turret: rises out of its flush well |
| `Decoy_Cap` | Body | (-0.00, 8.26, 41.00) | rotate -110 deg about X | Countermeasures · 0–0.4 | decoy tube end cap: flips up to let the towed decoy out |
| `Decoy_Pod` | Body | (-0.00, 7.71, 38.57) | slide +3.3929 studs along Z | Countermeasures · 0.4–1 | towed radar decoy: slides out aft (the game then trails it on a cable) |
| `EnginePanel_Aft_L` | Body | (-10.83, 9.05, 15.71) | rotate +110 deg about Z | EnginePanels · 0.15–1 | engine access panel: hinged on its outboard edge, swings up 110 deg |
| `EnginePanel_Aft_R` | Body | (10.83, 9.05, 15.71) | rotate -110 deg about Z | EnginePanels · 0.15–1 | engine access panel: hinged on its outboard edge, swings up 110 deg |
| `EnginePanel_Fwd_L` | Body | (-10.83, 9.05, 5.09) | rotate +110 deg about Z | EnginePanels · 0–1 | engine access panel: hinged on its outboard edge, swings up 110 deg |
| `EnginePanel_Fwd_R` | Body | (10.83, 9.05, 5.09) | rotate -110 deg about Z | EnginePanels · 0–1 | engine access panel: hinged on its outboard edge, swings up 110 deg |
| `Engine_Fan_L` | Body | (-8.75, 7.50, -6.64) | spin about Z at 95 rad/s | EngineRun · 0–1 | engine fan (visible down the intake) |
| `Engine_Fan_R` | Body | (8.75, 7.50, -6.64) | spin about Z at -95 rad/s | EngineRun · 0–1 | engine fan (visible down the intake) |
| `Flaperon_L` | Body | (-15.00, 7.50, 23.39) | rotate +25 deg about X (+ control -20..20 deg) | Flaps · 0–1 | flaperon: droops 25 deg as a flap (Flaps channel) and also deflects +/-20 deg for roll / pitch |
| `Flaperon_R` | Body | (15.00, 7.50, 23.39) | rotate +25 deg about X (+ control -20..20 deg) | Flaps · 0–1 | flaperon: droops 25 deg as a flap (Flaps channel) and also deflects +/-20 deg for roll / pitch |
| `Flares_Door_L` | Body | (-4.87, 5.68, 28.57) | rotate -100 deg about Z | Countermeasures · 0–0.5 | countermeasure magazine door: drops open to expose the flare / chaff cells |
| `Flares_Door_R` | Body | (4.87, 5.68, 28.57) | rotate +100 deg about Z | Countermeasures · 0–0.5 | countermeasure magazine door: drops open to expose the flare / chaff cells |
| `Gear_MainDoor_L` | Body | (-5.65, 5.62, 8.75) | rotate +95 deg about Z | GearUp · 0.8–1 | main gear door: open while the gear is down, closes after the gear is up |
| `Gear_MainDoor_R` | Body | (5.65, 5.62, 8.75) | rotate -95 deg about Z | GearUp · 0.8–1 | main gear door: open while the gear is down, closes after the gear is up |
| `Gear_MainWheel_L` | Gear_Main_L | (-5.00, 1.43, 12.36) | wheel, rolls about X | — | main wheel (rolls on the ground) |
| `Gear_MainWheel_R` | Gear_Main_R | (5.00, 1.43, 12.36) | wheel, rolls about X | — | main wheel (rolls on the ground) |
| `Gear_Main_L` | Body | (-4.25, 6.43, 12.14) | rotate +100 deg about X | GearUp · 0.1–0.8 | main gear: retracts forward into its well |
| `Gear_Main_R` | Body | (4.25, 6.43, 12.14) | rotate +100 deg about X | GearUp · 0.1–0.8 | main gear: retracts forward into its well |
| `Gear_Nose` | Body | (0.79, 6.86, -29.82) | rotate +95 deg about X | GearUp · 0.05–0.7 | nose gear: retracts forward |
| `Gear_NoseDoor_L` | Body | (-0.15, 5.33, -33.12) | rotate +95 deg about Z | GearUp · 0.7–0.95 | nose gear door: closes after retraction |
| `Gear_NoseDoor_R` | Body | (1.73, 5.80, -33.12) | rotate -95 deg about Z | GearUp · 0.7–0.95 | nose gear door: closes after retraction |
| `Gear_NoseSteer` | Gear_Nose | (0.79, 3.39, -29.82) | steer about Y, -60 .. 60 deg, 90 deg/s | — | nose wheel steering (taxi) |
| `Gear_NoseWheels` | Gear_NoseSteer | (0.79, 1.07, -29.46) | wheel, rolls about X | — | nose wheels (roll) |
| `Gun_Barrels` | Body | (-1.07, 6.07, -33.57) | spin about Z at 60 rad/s | Gun · 0.6–1 | rotary cannon barrel cluster (spins while firing) |
| `Gun_Door` | Body | (-1.62, 5.45, -34.11) | rotate -100 deg about Z | Gun · 0–0.6 | gun bay door: drops open before firing |
| `LEFlap_L` | Body | (-15.18, 7.39, 2.21) | rotate +15 deg about (-0.500, 0.000, 0.866) | Flaps · 0–1 | leading-edge flap: droops 15 deg about the swept hinge line for low-speed / VTOL lift |
| `LEFlap_R` | Body | (15.18, 7.39, 2.21) | rotate -15 deg about (0.500, 0.000, 0.866) | Flaps · 0–1 | leading-edge flap: droops 15 deg about the swept hinge line for low-speed / VTOL lift |
| `Laser_Door_L` | Body | (-1.62, 10.26, 3.75) | rotate +100 deg about Z | DorsalLaser · 0–0.35 | energy weapon bay door: swings up |
| `Laser_Door_R` | Body | (1.62, 10.26, 3.75) | rotate -100 deg about Z | DorsalLaser · 0–0.35 | energy weapon bay door: swings up |
| `Laser_Lift` | Body | (-0.00, 8.43, 3.75) | slide +2.2143 studs along Y | DorsalLaser · 0.35–1 | energy weapon elevator: raises the turret above the spine |
| `Laser_Pitch` | Laser_Yaw | (-0.00, 9.75, 4.29) | aim pitch about X, -5 .. 60 deg, 70 deg/s | — | energy weapon elevation (- = up, Blender X) |
| `Laser_Yaw` | Laser_Lift | (-0.00, 9.00, 4.29) | aim yaw about Y, unlimited, 90 deg/s | — | energy weapon traverse (360 deg) |
| `LiftFan_DoorBot_L` | Body | (-3.08, 5.08, -12.68) | rotate -92 deg about Z | VTOL · 0.05–0.5 | lift fan ventral door: hinged on its outer edge, folds down 92 deg |
| `LiftFan_DoorBot_R` | Body | (3.08, 5.08, -12.68) | rotate +92 deg about Z | VTOL · 0.05–0.5 | lift fan ventral door: hinged on its outer edge, folds down 92 deg |
| `LiftFan_DoorTop` | Body | (-0.00, 10.22, -8.92) | rotate +70 deg about X | VTOL · 0–0.45 | lift fan intake door: rear-hinged, opens 70 deg (front rises) |
| `LiftFan_Rotor1` | Body | (-0.00, 8.21, -12.86) | spin about Y at 70 rad/s | VTOL · 0.6–1 | lift fan upper rotor (spins in VTOL) |
| `LiftFan_Rotor2` | Body | (-0.00, 7.25, -12.86) | spin about Y at -70 rad/s | VTOL · 0.6–1 | lift fan lower rotor (counter-rotating) |
| `LiftFan_Vane_1` | Body | (-0.00, 5.36, -15.07) | rotate +72 deg about X | VTOL · 0.35–0.8 | lift fan louvre vane: swings to near-vertical in VTOL (vectors the fan thrust) |
| `LiftFan_Vane_2` | Body | (-0.00, 5.36, -14.21) | rotate +72 deg about X | VTOL · 0.35–0.8 | lift fan louvre vane: swings to near-vertical in VTOL (vectors the fan thrust) |
| `LiftFan_Vane_3` | Body | (-0.00, 5.36, -13.36) | rotate +72 deg about X | VTOL · 0.35–0.8 | lift fan louvre vane: swings to near-vertical in VTOL (vectors the fan thrust) |
| `LiftFan_Vane_4` | Body | (-0.00, 5.36, -12.50) | rotate +72 deg about X | VTOL · 0.35–0.8 | lift fan louvre vane: swings to near-vertical in VTOL (vectors the fan thrust) |
| `LiftFan_Vane_5` | Body | (-0.00, 5.36, -11.64) | rotate +72 deg about X | VTOL · 0.35–0.8 | lift fan louvre vane: swings to near-vertical in VTOL (vectors the fan thrust) |
| `LiftFan_Vane_6` | Body | (-0.00, 5.36, -10.79) | rotate +72 deg about X | VTOL · 0.35–0.8 | lift fan louvre vane: swings to near-vertical in VTOL (vectors the fan thrust) |
| `MainBay_DoorIn_L` | Body | (-0.35, 4.91, 4.29) | rotate +100 deg about Z | MainBays · 0–0.45 | weapon bay door: swings down 100 deg |
| `MainBay_DoorIn_R` | Body | (0.35, 4.91, 4.29) | rotate -100 deg about Z | MainBays · 0–0.45 | weapon bay door: swings down 100 deg |
| `MainBay_DoorOut_L` | Body | (-3.15, 5.02, 4.29) | rotate -100 deg about Z | MainBays · 0–0.45 | weapon bay door: swings down 100 deg |
| `MainBay_DoorOut_R` | Body | (3.15, 5.02, 4.29) | rotate +100 deg about Z | MainBays · 0–0.45 | weapon bay door: swings down 100 deg |
| `MainBay_Launcher_L` | Body | (-1.75, 7.29, 4.29) | slide -2.0714 studs along Y | MainBays · 0.45–1 | bay launcher: lowers the stores 0.58 m clear of the airframe |
| `MainBay_Launcher_R` | Body | (1.75, 7.29, 4.29) | slide -2.0714 studs along Y | MainBays · 0.45–1 | bay launcher: lowers the stores 0.58 m clear of the airframe |
| `Nozzle_Swivel1_L` | Body | (-8.75, 7.50, 32.86) | rotate +45 deg about X | VTOL · 0.25–0.85 | swivel nozzle bearing 1: turns 45 deg down about its spherical seat |
| `Nozzle_Swivel1_R` | Body | (8.75, 7.50, 32.86) | rotate +45 deg about X | VTOL · 0.25–0.85 | swivel nozzle bearing 1: turns 45 deg down about its spherical seat |
| `Nozzle_Swivel2_L` | Nozzle_Swivel1_L | (-8.75, 7.50, 35.54) | rotate +45 deg about X | VTOL · 0.35–1 | swivel nozzle bearing 2: another 45 deg down -> exhaust points straight down for hover |
| `Nozzle_Swivel2_R` | Nozzle_Swivel1_R | (8.75, 7.50, 35.54) | rotate +45 deg about X | VTOL · 0.35–1 | swivel nozzle bearing 2: another 45 deg down -> exhaust points straight down for hover |
| `RAT_Arm` | Body | (4.75, 6.61, 0.71) | rotate +90 deg about X | Emergency · 0.3–0.9 | ram-air turbine arm: swings down into the airflow for emergency power |
| `RAT_Door` | Body | (3.92, 5.14, 1.61) | rotate -100 deg about Z | Emergency · 0–0.4 | ram-air turbine door: drops open |
| `RAT_Prop` | RAT_Arm | (4.75, 6.43, 2.36) | spin about Y at 40 rad/s | Emergency · 0.6–1 | ram-air turbine propeller (windmills in the airflow) |
| `Radome` | Body | (2.07, 7.25, -37.86) | rotate -100 deg about Y | Radome · 0–1 | radome: hinged on the right side, swings 100 deg to expose the AESA radar |
| `Recon_Ball` | Recon_Mast | (-0.00, 5.71, -7.68) | aim yaw about Y, unlimited, 60 deg/s | — | recon ball pan (360 deg) |
| `Recon_ChineCam_L` | Body | (-2.43, 7.11, -28.04) | slide -0.5714 studs along Y | Recon · 0.4–1 | reconnaissance camera cradle: lowers out of the chine bay |
| `Recon_ChineCam_R` | Body | (2.43, 7.11, -28.04) | slide -0.5714 studs along Y | Recon · 0.4–1 | reconnaissance camera cradle: lowers out of the chine bay |
| `Recon_Door_L` | Body | (-1.44, 4.93, -7.68) | rotate -100 deg about Z | Recon · 0–0.4 | recon turret door: swings down |
| `Recon_Door_R` | Body | (1.44, 4.93, -7.68) | rotate +100 deg about Z | Recon · 0–0.4 | recon turret door: swings down |
| `Recon_Head` | Recon_Ball | (-0.00, 5.71, -7.68) | aim pitch about X, -90 .. 10 deg, 60 deg/s | — | recon head tilt (+ = look down, Blender X) |
| `Recon_Mast` | Body | (-0.00, 7.00, -7.68) | slide -1.6071 studs along Y | Recon · 0.4–1 | recon mast: lowers the ball turret |
| `Refuel_Door` | Body | (-0.00, 10.27, -5.53) | rotate +105 deg about X | Refuel · 0–1 | air-refuelling receptacle door: rear-hinged, opens forward-up to form the boom slipway |
| `RollPost_Door_L` | Body | (-16.87, 7.15, 16.96) | rotate -95 deg about Z | VTOL · 0.1–0.5 | roll-post nozzle door: opens so bled engine air can control roll in the hover |
| `RollPost_Door_R` | Body | (16.87, 7.15, 16.96) | rotate +95 deg about Z | VTOL · 0.1–0.5 | roll-post nozzle door: opens so bled engine air can control roll in the hover |
| `ServiceHatch_L` | Body | (-9.62, 5.04, 4.73) | rotate -100 deg about Z | Service · 0–1 | engine service hatch (gearbox / oil): hinged outboard, drops open |
| `ServiceHatch_R` | Body | (9.62, 5.04, 4.73) | rotate +100 deg about Z | Service · 0–1 | engine service hatch (gearbox / oil): hinged outboard, drops open |
| `SideBay_Door_L` | Body | (-3.63, 5.09, -5.27) | rotate +100 deg about Z | SideBays · 0–0.45 | side-bay door: hinged on its inboard edge, swings down |
| `SideBay_Door_R` | Body | (3.63, 5.09, -5.27) | rotate -100 deg about Z | SideBays · 0–0.45 | side-bay door: hinged on its inboard edge, swings down |
| `SideBay_Rail_L` | Body | (-4.71, 6.89, -5.36) | slide -1.5 studs along Y | SideBays · 0.4–1 | side-bay drop rail: lowers the missile below the airframe |
| `SideBay_Rail_R` | Body | (4.71, 6.89, -5.36) | slide -1.5 studs along Y | SideBays · 0.4–1 | side-bay drop rail: lowers the missile below the airframe |
| `Speedbrake_L` | Body | (-2.27, 9.52, 26.95) | rotate -50 deg about X | Speedbrake · 0–1 | dorsal speed brake: front-hinged, rises 50 deg |
| `Speedbrake_R` | Body | (2.27, 9.52, 26.95) | rotate -50 deg about X | Speedbrake · 0–1 | dorsal speed brake: front-hinged, rises 50 deg |
| `Spike_L` | Body | (-8.75, 7.50, -21.43) | slide +1.7857 studs along Z | HighSpeed · 0–1 | inlet shock spike: slides 0.50 m aft as speed rises (keeps the shock on the lip) |
| `Spike_R` | Body | (8.75, 7.50, -21.43) | slide +1.7857 studs along Z | HighSpeed · 0–1 | inlet shock spike: slides 0.50 m aft as speed rises (keeps the shock on the lip) |
| `Store_GBU_R1` | MainBay_Launcher_R | (2.43, 6.36, 3.57) | fixed to its parent (store: GBU-X Hammer precision glide bomb (fictional)) | — | precision glide bomb on the right bay launcher |
| `Store_GBU_R2` | MainBay_Launcher_R | (1.07, 6.36, 3.57) | fixed to its parent (store: GBU-X Hammer precision glide bomb (fictional)) | — | precision glide bomb on the right bay launcher |
| `Store_LRM_L1` | MainBay_Launcher_L | (-1.07, 6.55, 3.93) | fixed to its parent (store: LRM-9 Lancer long-range missile (fictional)) | — | long-range missile on the left bay launcher |
| `Store_LRM_L2` | MainBay_Launcher_L | (-2.43, 6.55, 3.93) | fixed to its parent (store: LRM-9 Lancer long-range missile (fictional)) | — | long-range missile on the left bay launcher |
| `Store_SRM_PylonL1` | Body | (-13.82, 5.40, 10.54) | fixed to its parent (store: SRM-4 Viper short-range missile (fictional)) | — | wing pylon missile |
| `Store_SRM_PylonL2` | Body | (-15.11, 5.40, 10.54) | fixed to its parent (store: SRM-4 Viper short-range missile (fictional)) | — | wing pylon missile |
| `Store_SRM_PylonR1` | Body | (15.11, 5.40, 10.54) | fixed to its parent (store: SRM-4 Viper short-range missile (fictional)) | — | wing pylon missile |
| `Store_SRM_PylonR2` | Body | (13.82, 5.40, 10.54) | fixed to its parent (store: SRM-4 Viper short-range missile (fictional)) | — | wing pylon missile |
| `Store_SRM_SideL` | SideBay_Rail_L | (-4.71, 6.30, -5.36) | fixed to its parent (store: SRM-4 Viper short-range missile (fictional)) | — | side-bay dogfight missile |
| `Store_SRM_SideR` | SideBay_Rail_R | (4.71, 6.30, -5.36) | fixed to its parent (store: SRM-4 Viper short-range missile (fictional)) | — | side-bay dogfight missile |
| `TailHook` | Body | (-0.00, 5.98, 30.93) | rotate +38 deg about X | Emergency · 0–1 | emergency arrestor hook: drops 38 deg to catch a runway cable |
| `Tail_L` | Body | (-8.75, 10.43, 26.26) | control about (0.259, 0.966, 0.000), -20 .. 20 deg, 90 deg/s | — | all-moving canted tail (rudder): rotates about its own spindle |
| `Tail_R` | Body | (8.75, 10.43, 26.26) | control about (-0.259, 0.966, 0.000), -20 .. 20 deg, 90 deg/s | — | all-moving canted tail (rudder): rotates about its own spindle |
| `Turret_Door_L` | Body | (-1.80, 4.93, 19.46) | rotate -100 deg about Z | BellyTurret · 0–0.35 | belly turret door: swings down |
| `Turret_Door_R` | Body | (1.80, 4.93, 19.46) | rotate +100 deg about Z | BellyTurret · 0–0.35 | belly turret door: swings down |
| `Wingtip_L` | Body | (-18.57, 7.19, 14.29) | rotate +60 deg about Z | HighSpeed · 0.1–0.9 | outer wing panel droops 60 deg at high speed (compression lift + directional stability) |
| `Wingtip_R` | Body | (18.57, 7.19, 14.29) | rotate -60 deg about Z | HighSpeed · 0.1–0.9 | outer wing panel droops 60 deg at high speed (compression lift + directional stability) |

## 6. Channels (states the server owns)
| Channel | Duration 0→1 | Moves | Rules |
|---|---|---|---|
| `Canopy` | 3.00 s | `Canopy` | ground only, below 30 km/h; auto-close before takeoff |
| `GearUp` | 5.50 s | `Gear_MainDoor_L`, `Gear_MainDoor_R`, `Gear_Main_L`, `Gear_Main_R`, `Gear_Nose`, `Gear_NoseDoor_L`, `Gear_NoseDoor_R` | only when airborne (no wheel touching the ground); HighSpeed must be 0 before the gear comes down |
| `VTOL` | 4.00 s | `AuxInlet_L`, `AuxInlet_R`, `LiftFan_DoorBot_L`, `LiftFan_DoorBot_R`, `LiftFan_DoorTop`, `LiftFan_Rotor1`, `LiftFan_Rotor2`, `LiftFan_Vane_1`, `LiftFan_Vane_2`, `LiftFan_Vane_3`, `LiftFan_Vane_4`, `LiftFan_Vane_5`, `LiftFan_Vane_6`, `Nozzle_Swivel1_L`, `Nozzle_Swivel1_R`, `Nozzle_Swivel2_L`, `Nozzle_Swivel2_R`, `RollPost_Door_L`, `RollPost_Door_R` | HighSpeed must be 0; max 280 km/h with VTOL deployed; hover thrust comes from LiftFan_Exhaust + Exhaust_L/R + RollPost_L/R |
| `Flaps` | 2.00 s | `Flaperon_L`, `Flaperon_R`, `LEFlap_L`, `LEFlap_R` | auto-on with VTOL and below 400 km/h |
| `HighSpeed` | 6.00 s | `Spike_L`, `Spike_R`, `Wingtip_L`, `Wingtip_R` | airborne only with GearUp = 1 and VTOL = 0; use above ~900 km/h (Mach 0.8) |
| `Speedbrake` | 1.00 s | `Speedbrake_L`, `Speedbrake_R` | — |
| `MainBays` | 1.60 s | `MainBay_DoorIn_L`, `MainBay_DoorIn_R`, `MainBay_DoorOut_L`, `MainBay_DoorOut_R`, `MainBay_Launcher_L`, `MainBay_Launcher_R` | stores in the main bays can only be released at 1; open bays break stealth (larger radar signature) |
| `SideBays` | 1.20 s | `SideBay_Door_L`, `SideBay_Door_R`, `SideBay_Rail_L`, `SideBay_Rail_R` | release only at 1 |
| `Gun` | 0.60 s | `Gun_Barrels`, `Gun_Door` | fire only at 1 |
| `BellyTurret` | 2.50 s | `BellyTurret_Barrels_L`, `BellyTurret_Barrels_R`, `BellyTurret_Lift`, `Turret_Door_L`, `Turret_Door_R` | deploy only when airborne (aimed down on the ground the guns would hit the runway); aim only at 1 |
| `DorsalLaser` | 2.50 s | `Laser_Door_L`, `Laser_Door_R`, `Laser_Lift` | fire only at 1 |
| `Recon` | 3.00 s | `ChineCam_Door_L`, `ChineCam_Door_R`, `Recon_ChineCam_L`, `Recon_ChineCam_R`, `Recon_Door_L`, `Recon_Door_R`, `Recon_Mast` | — |
| `Countermeasures` | 1.20 s | `DIRCM_Bot_Lift`, `DIRCM_Top_Lift`, `Decoy_Cap`, `Decoy_Pod`, `Flares_Door_L`, `Flares_Door_R` | — |
| `Emergency` | 3.00 s | `RAT_Arm`, `RAT_Door`, `RAT_Prop`, `TailHook` | — |
| `Radome` | 3.00 s | `Radome` | ground only, engines off |
| `EnginePanels` | 2.50 s | `EnginePanel_Aft_L`, `EnginePanel_Aft_R`, `EnginePanel_Fwd_L`, `EnginePanel_Fwd_R` | ground only, engines off |
| `Service` | 2.00 s | `Avionics_Door_L`, `Avionics_Door_R`, `ServiceHatch_L`, `ServiceHatch_R` | ground only |
| `Refuel` | 1.50 s | `Refuel_Door` | airborne, below 600 km/h |
| `EngineRun` | 4.00 s | `Engine_Fan_L`, `Engine_Fan_R` | 0 = engines off |

## 6b. Named poses (flight modes / test states)
| Pose | Channels at 1 | Inputs | On the ground | What it is |
|---|---|---|---|---|
| `rest` | — (all 0) | — | yes | parked: gear down + gear doors open, everything else closed |
| `service` | Canopy=1, Radome=1, EnginePanels=1, Service=1, Refuel=1 | — | yes | maintenance on the ground: canopy, radome, engine panels, service + refuel doors open |
| `vtol` | VTOL=1, Flaps=1, EngineRun=1 | — | yes | hover / vertical landing configuration (gear down) |
| `cruise` | GearUp=1, EngineRun=1 | — | no | clean normal flight |
| `highspeed` | GearUp=1, HighSpeed=1, EngineRun=1 | — | no | supersonic dash: wing tips drooped, spikes aft |
| `combat` | GearUp=1, EngineRun=1, MainBays=1, SideBays=1, Gun=1, BellyTurret=1, DorsalLaser=1, Countermeasures=1, Speedbrake=1 | BellyTurret_Yaw=35, BellyTurret_Pitch=25, Laser_Yaw=-20, Laser_Pitch=-12 | no | every weapon deployed |
| `recon` | GearUp=1, EngineRun=1, Recon=1 | Recon_Ball=40, Recon_Head=35 | no | reconnaissance sensors deployed |
| `landing` | Flaps=1, Speedbrake=1, Emergency=1, EngineRun=1 | — | yes | emergency landing: flaps, speed brakes, hook + RAT out |
| `allground` | Canopy=1, VTOL=1, Flaps=1, Speedbrake=1, MainBays=1, SideBays=1, Gun=1, BellyTurret=1, DorsalLaser=1, Recon=1, Countermeasures=1, Emergency=1, Radome=1, EnginePanels=1, Service=1, Refuel=1 | — | yes | everything that can open on the ground opened at once (clash test) |
| `controls` | — (all 0) | Aileron_L=25, Aileron_R=-25, Tail_L=20, Tail_R=20, Gear_NoseSteer=60, Flaperon_L=20, Flaperon_R=-20 | yes | control surfaces + nose-wheel steering at full deflection |

## 7. Seats
| Seat | Position (studs, cushion top) | Attached to | Role | Enter at | Exit to |
|---|---|---|---|---|---|
| `Seat_Pilot` | (-0.00, 8.11, -23.82) | Body | pilot (**driver**) | Board_Left | Exit_Left |

## 8. Points / sockets
| Point | Position (studs) | Attached to | Purpose |
|---|---|---|---|
| `Board_Left` | (-5.71, 0.00, -23.57) | Body | prompt (action=board / exit the cockpit (ladder side)) |
| `Exit_Left` | (-7.86, 0.00, -23.57) | Body | exit (note=where the pilot is placed after leaving the seat on the ground) |
| `Eye_Pilot` | (-0.00, 10.71, -23.04) | Body | camera (note=first-person cockpit camera) |
| `Exhaust_L` | (-17.50, 15.00, 75.36) | Nozzle_Swivel2_L | effect (direction=[-0.0, 0.0, 1.0], effect=engine exhaust / afterburner flame (points straight down in VTOL)) |
| `Exhaust_R` | (17.50, 15.00, 75.36) | Nozzle_Swivel2_R | effect (direction=[-0.0, 0.0, 1.0], effect=engine exhaust / afterburner flame (points straight down in VTOL)) |
| `RollPost_L` | (-16.25, 7.14, 16.96) | Body | effect (direction=[-0.0, -1.0, 0.0], effect=roll-control jet (VTOL)) |
| `RollPost_R` | (16.25, 7.14, 16.96) | Body | effect (direction=[-0.0, -1.0, 0.0], effect=roll-control jet (VTOL)) |
| `LiftFan_Exhaust` | (-0.00, 5.00, -12.86) | Body | effect (direction=[-0.0, -1.0, 0.0], effect=lift fan downwash (dust / heat haze under the aircraft in VTOL)) |
| `Muzzle_Gun` | (-2.14, 12.14, -71.50) | Gun_Barrels | muzzle (direction=[-0.0, 0.0, -1.0], weapon=M77 Thunder 7-barrel rotary cannon (fictional)) |
| `Launch_MainBay_L` | (-3.50, 11.75, 8.21) | MainBay_Launcher_L | launch (direction=[-0.0, 0.0, -1.0], note=stores leave from here after the launcher is down) |
| `Launch_MainBay_R` | (3.50, 11.75, 8.21) | MainBay_Launcher_R | launch (direction=[-0.0, 0.0, -1.0], note=stores leave from here after the launcher is down) |
| `Launch_SideBay_L` | (-9.43, 11.71, -15.18) | SideBay_Rail_L | launch (direction=[-0.0, 0.0, -1.0]) |
| `Launch_SideBay_R` | (9.43, 11.71, -15.18) | SideBay_Rail_R | launch (direction=[-0.0, 0.0, -1.0]) |
| `Launch_PylonL1` | (-27.64, 10.81, 16.61) | Store_SRM_PylonL1 | launch (direction=[-0.0, 0.0, -1.0]) |
| `Launch_PylonL2` | (-30.21, 10.81, 16.61) | Store_SRM_PylonL2 | launch (direction=[-0.0, 0.0, -1.0]) |
| `Launch_PylonR1` | (30.21, 10.81, 16.61) | Store_SRM_PylonR1 | launch (direction=[-0.0, 0.0, -1.0]) |
| `Launch_PylonR2` | (27.64, 10.81, 16.61) | Store_SRM_PylonR2 | launch (direction=[-0.0, 0.0, -1.0]) |
| `Muzzle_Belly_R` | (2.36, 11.50, 33.39) | BellyTurret_Barrels_R | muzzle (direction=[-0.0, 0.0, -1.0], weapon=twin 6-barrel rotary guns (fictional)) |
| `Muzzle_Belly_L` | (-2.36, 11.50, 33.39) | BellyTurret_Barrels_L | muzzle (direction=[-0.0, 0.0, -1.0], weapon=twin 6-barrel rotary guns (fictional)) |
| `Muzzle_Laser` | (-0.00, 19.50, 5.18) | Laser_Pitch | muzzle (direction=[-0.0, 0.0, -1.0], weapon=Helios directed-energy beam (fictional)) |
| `Sensor_Radar` | (-0.00, 7.37, -38.79) | Body | sensor (direction=[-0.0, 0.0, -1.0], note=AESA radar boresight (lock-on cone origin)) |
| `Sensor_EOTS` | (0.18, 5.53, -37.29) | Body | sensor (direction=[-0.0, -0.8944, -0.4472], note=electro-optical targeting camera) |
| `Sensor_IRST` | (-0.00, 9.06, -35.36) | Body | sensor (direction=[-0.0, 0.0, -1.0], note=infrared search and track) |
| `Camera_Chine_L` | (-5.00, 13.18, -56.07) | Recon_ChineCam_L | camera (direction=[-0.3102, -0.9507, 0.0], note=oblique reconnaissance camera) |
| `Camera_Chine_R` | (5.00, 13.18, -56.07) | Recon_ChineCam_R | camera (direction=[0.3102, -0.9507, 0.0], note=oblique reconnaissance camera) |
| `Camera_ReconBall` | (-0.00, 11.43, -15.79) | Recon_Head | camera (direction=[-0.0, 0.0, -1.0], note=stabilised long-range reconnaissance camera (zoom view)) |
| `Flares_L` | (-4.07, 5.54, 28.57) | Body | effect (direction=[-0.2822, -0.9407, 0.1881], effect=flare / chaff release (only while the magazine door is open)) |
| `Flares_R` | (4.07, 5.54, 28.57) | Body | effect (direction=[0.2822, -0.9407, 0.1881], effect=flare / chaff release (only while the magazine door is open)) |
| `DIRCM_Top` | (-0.00, 20.36, 44.54) | DIRCM_Top_Head | effect (direction=[-0.0, 0.0, -1.0], effect=invisible jamming laser (show a faint beam toward the incoming missile)) |
| `DIRCM_Bot` | (-0.00, 9.50, 48.46) | DIRCM_Bot_Head | effect (direction=[-0.0, 0.0, -1.0], effect=invisible jamming laser (show a faint beam toward the incoming missile)) |
| `Decoy_Tow` | (-0.00, 15.43, 82.79) | Decoy_Pod | effect (direction=[-0.0, 0.0, 1.0], effect=towed decoy: attach a long cable + drag the pod behind the aircraft) |
| `Socket_Refuel` | (-0.00, 10.00, -6.07) | Body | socket (direction=[-0.0, 1.0, 0.0], note=tanker boom connects here (only when the Refuel door is open)) |
| `Vent_NACA_L` | (-2.21, 9.83, 23.75) | Body | effect (direction=[-0.0, 0.0, 1.0], effect=cooling air intake (heat shimmer at high power)) |
| `Vent_NACA_R` | (2.21, 9.82, 23.75) | Body | effect (direction=[-0.0, 0.0, 1.0], effect=cooling air intake (heat shimmer at high power)) |

## 9. Boxes (collision / zones)
| Box | Centre (studs) | Size (studs) | Purpose |
|---|---|---|---|
| `Box_Nose` | (-0.00, 7.14, -38.04) | (3.93, 3.00, 12.50) | collision |
| `Box_ForwardBody` | (-0.00, 7.50, -23.93) | (7.50, 4.71, 15.71) | collision |
| `Box_Canopy` | (-0.00, 10.61, -25.71) | (3.57, 2.64, 15.00) | collision |
| `Box_CentreBody` | (-0.00, 7.61, 5.18) | (12.50, 5.36, 42.50) | collision |
| `Box_AftBody` | (-0.00, 7.34, 32.59) | (8.57, 4.32, 12.32) | collision |
| `Box_Nacelle_L` | (-8.75, 7.52, 7.77) | (5.21, 5.18, 48.39) | collision |
| `Box_Nacelle_R` | (8.75, 7.52, 7.77) | (5.21, 5.18, 48.39) | collision |
| `Box_InnerWing_L` | (-14.96, 7.50, 10.18) | (7.21, 0.86, 32.50) | collision |
| `Box_InnerWing_R` | (14.96, 7.50, 10.18) | (7.21, 0.86, 32.50) | collision |
| `Box_OuterWing_L` | (-22.86, 7.50, 16.50) | (8.57, 0.57, 19.86) | collision |
| `Box_OuterWing_R` | (22.86, 7.50, 16.50) | (8.57, 0.57, 19.86) | collision |
| `Box_Tail_L` | (-7.86, 14.39, 28.30) | (2.50, 7.93, 13.39) | collision |
| `Box_Tail_R` | (7.86, 14.39, 28.30) | (2.50, 7.93, 13.39) | collision |

## 10. Physics (realistic data + Roblox tuning)
| Wheel group | Centre (studs) | Radius | Width | Steers | Driven | Travel up / down (m) |
|---|---|---|---|---|---|---|
| `Gear_MainWheel_L` | (-5.00, 1.43, 12.36) | 1.429 st (0.40 m) | 0.929 st | no | no | 0.28 / 0.05 |
| `Gear_MainWheel_R` | (5.00, 1.43, 12.36) | 1.429 st (0.40 m) | 0.929 st | no | no | 0.28 / 0.05 |
| `Gear_NoseWheels` | (0.79, 1.07, -29.46) | 1.071 st (0.30 m) | 0.536 st | ±60° | no | 0.22 / 0.05 |

- **empty mass kg:** 19800
- **max takeoff mass kg:** 36500
- **max vtol mass kg:** 28000
- **internal fuel kg:** 11000
- **centre of mass m blender:** [0.0, 1.2, 2.05]
- **centre of mass studs:** [0.0, 7.321, 4.286]
- **wing area m2:** 131.2
- **wheelbase m:** 11.75
- **main gear track m:** 2.8
- **engines:** 2 x F-140 adaptive-cycle afterburning turbofan (fictional): 155 kN dry / 225 kN with afterburner each
- **lift fan:** hybrid-electric contra-rotating lift fan, 110 kN (fictional)
- **roll posts:** 2 x 9 kN bleed-air jets
- **thrust to weight combat:** 1.53
- **top speed:** Mach 3.3 at 24,000 m (~3,500 km/h); 1,450 km/h at sea level
- **cruise speed kmh:** 950
- **stall speed kmh clean:** 230
- **vtol transition max kmh:** 280
- **ceiling m:** 26000
- **range km:** 4800
- **g limits:** [9.0, -3.0]
- **roll rate deg s:** 270
- **sustained turn deg s:** 22
- **ground clearance m:** 1.38
- **roblox speed hint:** the island is ~16,000 studs wide: compress speeds about 3x. Suggested game values: taxi 25 studs/s, takeoff 110 studs/s, cruise 260 studs/s, afterburner 650 studs/s, HighSpeed mode up to 1,200 studs/s; hover/VTOL 0-80 studs/s.
- **roblox assembly hint:** one invisible root part at the centre of mass (Massless=false, everything else massless) + the collision boxes; fly it with VectorForce / LinearVelocity + AlignOrientation; on the ground use raycast suspension at the three wheel groups (rig.wheels).

## 11a. Lights
| Light | Position (studs) | Attached to | Type | Mode | Direction | Range (studs) | Neon materials |
|---|---|---|---|---|---|---|---|
| `Light_CockpitFlood` | (-0.00, 9.64, -21.43) | Body | point | interior | (-0.00, 0.00, -1.00) | 8.93 | — |
| `Light_Landing` | (1.73, 11.00, -60.14) | Gear_Nose | spot 24° | landing | (-0.00, -0.08, -1.00) | 214.29 | LED |
| `Light_Taxi` | (1.41, 11.00, -60.14) | Gear_Nose | spot 60° | taxi | (-0.00, -0.15, -0.99) | 107.14 | — |
| `Light_Nav_L` | (-27.14, 7.50, 23.64) | Wingtip_L | point | navigation | (-0.00, 0.00, -1.00) | 21.43 | NavRed |
| `Light_Tail_L` | (-6.64, 18.29, 34.77) | Tail_L | point | navigation | (-0.00, 0.00, -1.00) | 17.86 | Strobe |
| `Light_Nav_R` | (27.14, 7.50, 23.64) | Wingtip_R | point | navigation | (-0.00, 0.00, -1.00) | 21.43 | NavGreen |
| `Light_Tail_R` | (6.64, 18.29, 34.77) | Tail_R | point | navigation | (-0.00, 0.00, -1.00) | 17.86 | Strobe |
| `Light_Strobe_Top` | (-0.00, 10.21, 16.43) | Body | point | anticollision | (-0.00, 0.00, -1.00) | 50 | Strobe |
| `Light_Strobe_Bot` | (-0.00, 5.36, 29.64) | Body | point | anticollision | (-0.00, 0.00, -1.00) | 50 | Strobe |

## 11. Materials (apply by the `<Material>` part of each mesh name)
| Material | Roblox material | Colour (RGB) | Transparency | Reflectance |
|---|---|---|---|---|
| Alu | Metal | 172, 174, 178 | 0 | 0 |
| BandBrown | SmoothPlastic | 122, 76, 40 | 0 | 0 |
| BayGrey | SmoothPlastic | 160, 162, 163 | 0 | 0 |
| Black | SmoothPlastic | 18, 18, 20 | 0 | 0 |
| Bomb | SmoothPlastic | 86, 92, 64 | 0 | 0 |
| Brass | Metal | 190, 150, 70 | 0 | 0 |
| BurntTi | Metal | 92, 74, 88 | 0 | 0 |
| CableBlack | SmoothPlastic | 22, 22, 22 | 0 | 0 |
| CableOrange | Fabric | 215, 100, 30 | 0 | 0 |
| Ceramic | Slate | 52, 48, 45 | 0 | 0 |
| Chrome | Foil | 205, 207, 212 | 0 | 0.4 |
| Cockpit | SmoothPlastic | 72, 76, 82 | 0 | 0 |
| CockpitDark | SmoothPlastic | 30, 31, 34 | 0 | 0 |
| Copper | Metal | 190, 110, 62 | 0 | 0 |
| Display | SmoothPlastic | 12, 14, 18 | 0 | 0.2 |
| Engine | Metal | 80, 82, 88 | 0 | 0 |
| Exhaust | Metal | 44, 41, 39 | 0 | 0 |
| Formation | Neon | 110, 235, 140 | 0.25 | 0 |
| GearWhite | SmoothPlastic | 200, 200, 196 | 0 | 0 |
| Glass | Glass | 150, 128, 82 | 0.45 | 0.25 |
| GlassClear | Glass | 205, 218, 222 | 0.7 | 0.1 |
| Gunmetal | Metal | 40, 42, 46 | 0 | 0 |
| Hardware | Metal | 56, 56, 55 | 0 | 0 |
| Harness | Fabric | 118, 110, 80 | 0 | 0 |
| Inconel | Metal | 112, 92, 74 | 0 | 0 |
| Insulation | Foil | 212, 172, 84 | 0 | 0.2 |
| LED | Neon | 240, 244, 255 | 0 | 0 |
| Laser | Neon | 170, 95, 255 | 0 | 0 |
| Missile | SmoothPlastic | 178, 180, 178 | 0 | 0 |
| NavGreen | Neon | 40, 255, 90 | 0 | 0 |
| NavRed | Neon | 255, 30, 25 | 0 | 0 |
| Primer | SmoothPlastic | 98, 122, 78 | 0 | 0 |
| Radar | SmoothPlastic | 96, 100, 82 | 0 | 0 |
| Red | SmoothPlastic | 170, 22, 18 | 0 | 0 |
| Rubber | Rubber | 28, 28, 28 | 0 | 0 |
| ScreenAmber | Neon | 255, 160, 40 | 0 | 0 |
| ScreenCyan | Neon | 40, 190, 255 | 0 | 0 |
| ScreenGreen | Neon | 60, 235, 110 | 0 | 0 |
| ScreenRed | Neon | 255, 40, 30 | 0 | 0 |
| Seat | Fabric | 52, 58, 44 | 0 | 0 |
| SensorGlass | Glass | 30, 34, 46 | 0.15 | 0.35 |
| Skin | SmoothPlastic | 54, 57, 63 | 0 | 0 |
| SkinAlt | SmoothPlastic | 64, 67, 73 | 0 | 0 |
| SkinDark | SmoothPlastic | 33, 34, 37 | 0 | 0 |
| Steel | Metal | 130, 130, 128 | 0 | 0 |
| Stencil | SmoothPlastic | 92, 96, 102 | 0 | 0 |
| Strobe | Neon | 235, 240, 255 | 0 | 0 |
| Tire | Rubber | 30, 30, 30 | 0 | 0 |
| Titanium | Metal | 122, 120, 117 | 0 | 0 |
| Wheel | Metal | 150, 152, 156 | 0 | 0 |
| Yellow | SmoothPlastic | 235, 180, 20 | 0 | 0 |

## 12. Gameplay systems
### M77 Thunder rotary cannon
- **type:** gun
- **muzzle:** Muzzle_Gun
- **spin group:** Gun_Barrels
- **channel:** Gun
- **rounds:** 1200
- **fire rate per s:** 70
- **suggested damage:** 18
- **range studs:** 1500
- **note:** 7-barrel (fictional); door must be open (Gun = 1); barrels spin up 0.3 s before firing

### LRM-9 Lancer
- **type:** missile
- **stores:** ['Store_LRM_L1', 'Store_LRM_L2']
- **launch point:** Launch_MainBay_L
- **channel:** MainBays
- **lock time s:** 1.5
- **range studs:** 3000
- **speed studs s:** 900
- **suggested damage:** 220
- **note:** radar-guided long-range missile (fictional); hide the store mesh on launch

### SRM-4 Viper
- **type:** missile
- **stores:** ['Store_SRM_SideL', 'Store_SRM_SideR', 'Store_SRM_PylonL1', 'Store_SRM_PylonL2', 'Store_SRM_PylonR1', 'Store_SRM_PylonR2']
- **launch points:** ['Launch_SideBay_L', 'Launch_SideBay_R', 'Launch_PylonL1', 'Launch_PylonL2', 'Launch_PylonR1', 'Launch_PylonR2']
- **channel:** SideBays (side-bay rounds only; pylon rounds are always ready)
- **lock time s:** 0.6
- **range studs:** 1200
- **speed studs s:** 750
- **suggested damage:** 140
- **note:** infrared dogfight missile (fictional)

### GBU-X Hammer
- **type:** bomb
- **stores:** ['Store_GBU_R1', 'Store_GBU_R2']
- **launch point:** Launch_MainBay_R
- **channel:** MainBays
- **guidance:** glides to the point the EOTS / pilot designates (Sensor_EOTS)
- **blast radius studs:** 40
- **suggested damage:** 400
- **note:** precision glide bomb (fictional)

### Belly twin rotary guns
- **type:** turret
- **lift:** BellyTurret_Lift
- **yaw:** BellyTurret_Yaw
- **pitch:** BellyTurret_Pitch
- **spin groups:** ['BellyTurret_Barrels_L', 'BellyTurret_Barrels_R']
- **muzzles:** ['Muzzle_Belly_L', 'Muzzle_Belly_R']
- **channel:** BellyTurret
- **fire rate per s:** 90
- **suggested damage:** 12
- **range studs:** 1200
- **note:** 360 deg traverse, -10..+90 deg (down) elevation

### Helios energy turret
- **type:** beam
- **lift:** Laser_Lift
- **yaw:** Laser_Yaw
- **pitch:** Laser_Pitch
- **muzzle:** Muzzle_Laser
- **channel:** DorsalLaser
- **damage per s:** 120
- **range studs:** 2500
- **overheat s:** 6
- **cooldown s:** 4
- **note:** continuous beam (fictional); Laser material glows when firing

### Countermeasures
- **type:** defence
- **flares:** ['Flares_L', 'Flares_R']
- **flares per side:** 36
- **dircm:** ['DIRCM_Top', 'DIRCM_Bot']
- **decoy:** Decoy_Pod
- **channel:** Countermeasures
- **note:** flares + DIRCM defeat locks for ~2 s; the towed decoy pulls radar missiles away while deployed

### Sensors
- **type:** sensors
- **radar:** Sensor_Radar
- **eots:** Sensor_EOTS
- **irst:** Sensor_IRST
- **cameras:** ['Camera_Chine_L', 'Camera_Chine_R', 'Camera_ReconBall', 'Eye_Pilot']
- **note:** radar lock cone 60 deg forward; Recon channel gives zoom camera views + marks targets

### VTOL
- **type:** flight
- **channel:** VTOL
- **thrust points:** ['LiftFan_Exhaust', 'Exhaust_L', 'Exhaust_R']
- **roll points:** ['RollPost_L', 'RollPost_R']
- **note:** hover: lift fan carries ~55%, swivel nozzles ~45%; roll posts trim roll; transition below 280 km/h

### Stealth
- **type:** signature
- **note:** radar signature is low only with GearUp = 1 and MainBays / SideBays / Gun / BellyTurret / DorsalLaser / Refuel / Recon all at 0

## 13. Notes and rules
- Rest pose = parked on the ground: gear DOWN with the gear doors OPEN, everything else closed. GearUp=1 retracts.
- Every store (missile / bomb) is its own group: hide it when it is fired and spawn the projectile at the matching Launch_* point; show it again on rearm.
- Interlocks: VTOL and HighSpeed are mutually exclusive; GearUp=1 blocks Canopy / Radome / EnginePanels / Service; EngineRun must be 0 for Radome / EnginePanels; the wing tips must never droop with the gear down (they would reach 0.07 m above the ground).
- Hinges that are not on a model axis (canted tails, swept leading-edge flaps, avionics doors) give their axis as a unit vector - rotate about that vector (CFrame.fromAxisAngle).
- Flaperons: Flaps channel sets the droop; roll / pitch input adds +/-20 deg on top (motion.control).
- Spin groups (fans, rotors, barrels, RAT) only spin while their channel is > 0 (fans: EngineRun).
- Lights: navigation red (left tip) / green (right tip) / white tails steady; strobes flash 1 Hz; formation strips glow dim green at night; landing + taxi lights on the nose gear (only with GearUp = 0).
- The canopy glass is tinted gold (Glass material, 0.45 transparency) - the cockpit is visible from outside.
- Admin-only aircraft: check admin status on the server before seating a pilot or firing any weapon.
- Scale: 87.9 studs long, 54.3 studs span - give it a clear 100 x 70 stud spawn pad.

## 14. Acceptance checklist (test in Studio before calling it done)
- [ ] Import size matches §2; installer reports 0 unknown mesh names.
- [ ] Every group in §5 moves about the right hinge, in the right direction, by the listed amount, in stage order.
- [ ] Nothing floats or clips at rest **and** fully deployed (the Blender checks found 0 floating parts in both).
- [ ] Every seat can be entered from its enter point and exits to its exit point; occupants face −Z.
- [ ] Drives straight, steers the right way, brakes, climbs hills, does not bounce or flip in normal turns.
- [ ] All server checks in place (who may use what, rate limits, clamped inputs) — the game is server-authoritative.
- [ ] Output window clean (no errors/warnings from the new scripts).

_Generated 2026-10-05 02:10 by `blender/export_handoff.py`. FBX re-import check: PASSED (112 pivots compared, 0 problems)._
