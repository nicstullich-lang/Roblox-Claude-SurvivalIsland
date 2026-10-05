# Model handoff standard (`survival-island-model/1`)

**Workflow (Nic, Oct 2026):** the *Blender chat* builds models only. A *separate Roblox chat* writes all the game
code. So every model must arrive as a self-describing **handoff package** that the Roblox chat can turn into working,
realistic gameplay without guessing anything.

## 1. What a package contains

```
exports/<ModelName>/
  <ModelName>.fbx          meshes merged per (moving group, material), already in studs, Roblox axes
  <ModelName>_Rig.json     machine-readable rig: groups/hinges/motions, channels, poses, seats, points, lights,
                           collision boxes, wheels, materials, physics, gameplay systems, notes, verification
  HANDOFF.md               the same data explained for the Roblox chat + an acceptance checklist
  previews/*.png           renders at rest and in every named pose
```

Give the Roblox chat **the whole folder** (at minimum `HANDOFF.md` + `_Rig.json` + the `.fbx`).

## 2. Blender conventions every model follows

| Rule | Why |
|---|---|
| Metres, Z up, the model's **front = −Y**, its **left = +X** (`_L` = +X, `_R` = −X: true sides) | one conversion for everything |
| Roblox = `(−x, z, y) × (1/0.28)` studs; front = −Z (LookVector), right = +X | 1 stud = 0.28 m (Survival Island scale) |
| Every moving part is a **group object** with its **origin on the real hinge** and **identity rotation at rest** | Roblox Motor6D joints are placed at `pivot_studs` |
| Each group is tagged with `common.rig.motion(...)` (type, axis, amount, channel, stage) | the exporter reads only tags, never guesses from names |
| Axes: `X`/`Y`/`Z` or any unit vector (canted tails, swept hinges) | `CFrame.fromAxisAngle` in Roblox |
| Children (details) are parented to their group; static parts belong to `Body` | merging per group keeps pivots exact |
| Markers are empties in `RIG_Markers`: `rig.seat`, `rig.point` (muzzles, launch points, prompts, exits, cameras, effects), `rig.light`, `rig.box` (collision), `rig.wheel` | data, never exported as meshes |
| Model-level data: `rig.model`, `rig.channel` (duration + rules), `rig.pose`, `rig.physics`, `rig.system`, `rig.note` | gameplay + realism info for the coder |
| Material names `<PREFIX><Name>`; Roblox look via the material's `roblox` spec (`R(...)` in the model lib) | exact colours in Roblox |
| Per-mesh limit: export splits anything over 16k triangles (Roblox max ~20k) | import never fails |

## 3. Motion types

| Type | Driven by | Data |
|---|---|---|
| `rotate`, `translate` | a channel 0→1 | `open` (deg / m at 1), `stage` (slice of the channel's progress), optional `control` (extra input on top) |
| `aim_yaw`, `aim_pitch`, `steer`, `control` | player input | `min`, `max` (deg), `speed` (deg/s) |
| `spin` | continuous while its channel > 0 | `speed` (rad/s) |
| `wheel` | rolling on the ground | `rig_wheel`: radius, width, steer, suspension travel |
| `fixed` | rides on its parent | `kind: store` = weapon that can be hidden / released |

**Rest pose = how the model sits when parked / spawned** (e.g. gear down with gear doors open). Parts that are open at
rest are modelled open and their motion closes them.

## 4. Quality gates before a package is delivered

1. `bpy-run blender/check_model.py <pkg>` → **0 floating parts, 0 clashes in every pose, nothing below the ground**
   in ground poses (tyres excepted). Hinges sit just *outside* the skin along the whole hinge edge
   (`airframe.hinge_line`), otherwise doors swing into the surrounding skin.
2. Renders from every side + every pose (`blender/render_model.py`) are inspected.
3. `bpy-run blender/export_handoff.py <pkg>` → the FBX is re-imported automatically and every group pivot + the size
   are compared with the rig data: `verification.passed` must be **true**.
4. Triangle budget: aim ≤ ~300k for a hero vehicle, no mesh > 16k.

## 5. Per-category requirements

| Category | Must include |
|---|---|
| Vehicles / aircraft | seats (driver flag, enter/exit points), wheels with suspension travel, collision boxes, centre of mass, mass + performance figures, every door / hatch / control surface as a group, lights with modes |
| Weapons | muzzle points + direction, moving parts (bolt, magazine, slide) as groups, fire modes / rates in `rig.system`, hand grip points |
| Buildings | doors / windows as groups, interaction points, collision boxes per room, loot / spawn zones as boxes |
| Props / tools | grip / attach points, collision box, any moving part |
| Characters / creatures | need an armature (skinned mesh) — a different pipeline; tell Nic first |

## 6. Tools (all in this repo)

| File | Purpose |
|---|---|
| `blender/common/geo.py` | shared geometry toolkit (lofts, lathes, sweeps, booleans, surface-following door panels, grooves, fasteners, stencils, studio) |
| `blender/common/rig.py` | tagging API (`motion`, `seat`, `point`, `light`, `box`, `wheel`, `model`, `channel`, `pose`, `physics`, `system`, `note`) |
| `blender/common/poses.py` | applies channel values / poses to the groups; keys the showcase timeline |
| `blender/common/handoff.py` | exporter: FBX + rig JSON + HANDOFF.md + previews + re-import verification |
| `blender/check_model.py` | floating / clash / ground / budget checks for every pose |
| `blender/render_model.py` | renders (any view, any pose) |
| `blender/export_handoff.py` | CLI for the exporter |
