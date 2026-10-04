# CLAUDE.md — Survival Island + VX-9 Wraith admin supercar

Reference for Claude Code sessions working on Nic's Roblox game **Survival Island** and the **VX-9 "Wraith"**
admin-only supercar (built in Blender, imported into Roblox). Everything here was verified in the
3–4 Oct 2026 build session unless marked otherwise.

---

## 0. Working with Nic (read first)

- Act as an expert (automotive 3D artist / hard-surface modeller / Roblox engineer), but **explain slowly** — Nic is a
  beginner in coding. Still use the correct technical words; just explain them.
- Always **finish and deliver the full result**. Don't stop early, don't spend the budget on planning, don't hand back
  partial work. **Double-check everything** (measure, screenshot, playtest) before calling it done.
- Project goals: the game must **not look "vibe coded"**. Reference expert-made games for models and game feel
  (DayZ, Rust, Forza Horizon, Minecraft-style building). Fun to play for hours, with incremental progression.
- Nic runs AutoElevate (an AI receptionist agency) — unrelated to this repo, ignore unless asked.

---

## 1. Quick start for a new session

1. Open Studio place **Survival Island** (placeId `114363482402331`, Team Create — edits go live to the team session,
   nothing is *published* until Nic publishes).
2. Open `Documents\VX9_Wraith_AdminSupercar.blend` in Blender (5.2.2 LTS, Steam install). Scene: **VX9_Wraith**.
3. In Blender, load the build library (it is stored as text blocks inside the .blend):
   ```python
   import bpy, sys, types
   vx = types.ModuleType('vx9')
   exec(bpy.data.texts['vx9_lib.py'].as_string(), vx.__dict__)
   sys.modules['vx9'] = vx
   vx.store_rest()                     # remembers the closed pose of all moving parts
   ```
4. Blender MCP rule: `execute_blender_code` must set `result = {...}` (a **dict**, never a string).
5. Roblox MCP rule: `execute_luau` needs `datamodel_type` = `Edit` (editing) / `Server` / `Client` (during playtest).

---

## 2. Files and IDs

| What | Where / value |
|---|---|
| Blender source (all build scripts inside as text blocks) | `C:\Users\nicst\OneDrive\Documents\VX9_Wraith_AdminSupercar.blend` |
| Roblox export (stud scale, 111 meshes) | `C:\Users\nicst\OneDrive\Documents\VX9_Wraith_Roblox.fbx` (~3.08 MB) |
| Stray duplicate .blend (safe to delete) | `C:\Users\nicst\VX9_Wraith_AdminSupercar.blend` |
| Unrelated file in the same folder | `Documents\adminsmg.blend` (an SMG blockout, 11 primitives; scene "Scene") |
| **Current** Roblox model asset | **115958792929759** (uploaded 3 Oct 2026 4:38 PM) |
| Broken first upload — do NOT use | 119399325688960 (metre scale, grey, stray spikes) |
| Roblox place | Survival Island, placeId 114363482402331, Studio account DOGMENSEM |
| Project build log (claude.ai project "Roblox game") | `claude/World build log.md` |

---

## 3. The car at a glance

- Original design (McLaren/Lamborghini *language*, not a copy) + fictional military prototype. Admin-only.
- Real size: **4.62 m long, ~2.04 m body width (2.16 m incl. mirrors), 1.125 m roof, 2.72 m wheelbase**.
  In Roblox: **17.02 × 7.70 × 4.47 studs** (L × W × H incl. mirrors and wing). 1 stud = 0.28 m.
- Wheels: 20" front (tyre R 0.334 m, W 0.265 m), 21" rear (R 0.364 m, W 0.325 m). Front track ±0.852 m, rear ±0.838 m.
- **Right-hand drive** (yoke on the car's right). Mid-engine twin-turbo V8 (visual only).
- Military features (all visual + rigged pivots, no real-world weapon detail):
  side gun pods behind armoured intake hatches, frunk micro-rocket pods on scissor lifts under clamshell lids,
  window armour shutters stowed in the doors, roof sensor pod + antenna blades, hazard markings,
  weapons console with guarded switches, overhead arming panel, HUD.
- Triangles: **~145,400** total; largest single mesh 16,000 (Roblox per-mesh limit ~20k).

---

## 4. Coordinate systems (most common source of bugs)

| | Blender | Roblox |
|---|---|---|
| Units | metres | studs (×3.5714) |
| Up | +Z | +Y |
| Car nose | **−Y** | **−Z** (= LookVector, Roblox "forward") |
| Car's right side | **−X** | **+X** |

**Conversion:** `Roblox = (-x_b, z_b, y_b) * (1/0.28)` — Luau helper `B(x,y,z)` in `VX9_ImportSetup`.

⚠️ **Side-label trap:** Blender objects named `_L` sit at −X, which is the car's **right** side. In Roblox they are
renamed by their true side (`Door_L` → `Doors.Door_Right`, `Wheel_FL` → `Wheels.FrontRight`, etc.).
Keep the Blender names as-is (the export/import pipeline depends on them).

---

## 5. Blender build system

### 5.1 Scene layout
- Collections: `VX9_Wraith` › `VX9_Body`, `VX9_Glass`, `VX9_Aero`, `VX9_Wheels`, `VX9_Chassis`, `VX9_Lights`,
  `VX9_Interior`, `VX9_Powertrain`, `VX9_Military`. Plus `VX9_Studio` (floor, lights, camera) and
  `VX9_RobloxExport` (merged export meshes; **excluded** from the view layer except while exporting).
- Root empty: `VX9_Root` — every car object is parented under it.
- Materials: all prefixed `VX9_` (get with `vx.M('Paint')`). Names: Paint, PanelInner, Carbon, CarbonMatte, Glass,
  GlassDark, Lens, Rubber, Tire, Alu, Chrome, Titanium, BurntTi, Rim, RimLip, Rotor, Accent, Caliper, Grille, Plastic,
  Steel, LED, Amber, TailRed, HUD, Screen, Housing, Alcantara, Leather, Stitch, Belt, Armor, Gunmetal, Hazard, Engine,
  Copper, Exhaust, WellLiner, GuardRed, Floor. Carbon/CarbonMatte use a procedural checker "weave" (Blender only).
- Render: EEVEE, AgX, 1600×900, camera `Studio_Cam`, lights `Key_Top`, `Key_Left`, `Rim_Right`, `Sun`.
  `vx.setview(name)` presets: front34, rear34, side, front, rear, top, low34, cockpit, interior, under
  (or `vx.setview(None, loc, target, lens)`).

### 5.2 Text blocks inside the .blend (run in this order for a full rebuild)

| Text block | Builds | Deletes before rebuild (custom prop tag) |
|---|---|---|
| `vx9_lib.py` | the library (module `vx9`) — run first, never "rebuilds" anything | — |
| `vx9_body.py` | lofted body panels with real 4 mm seams, glass, seam liner, nose/tail caps | `vx_body` |
| `vx9_wheels.py` | tyres, rims, spokes, centre-lock, rotors, bells, calipers (on `Upright_*` empties), wheel-well liners | `vx_wheel` |
| `vx9_exterior.py` | splitter, chin, intakes, canards, headlights, vents, mirrors, door handles, skirts, diffuser, taillights, exhaust, louvres, active wing, underbody floor | `vx_ext` |
| `vx9_military.py` | side gun hatches/pods, frunk rocket pods + lifts, armour shutters, roof sensor, hazard marks, **sets hinge origins** for doors, frunk lids, hatches, pods, wing | `vx_mil` |
| `vx9_interior.py` | tub, dash, displays, HUD, vents, yoke, seats, harnesses, console, pedals, overhead panel, door cards | `vx_int` |
| `vx9_engine.py` | V8, plenum, turbos, headers, exhaust pipes, intercoolers, double wishbones + pushrod coilovers | `vx_eng` |
| `vx9_extras.py` | brake cooling ducts, door hinge brackets + gas struts, underbody vortex generators | `vx_xtra` |

Run a script with: `g = {}; exec(bpy.data.texts['vx9_exterior.py'].as_string(), g)`.

**Dependencies:** rebuilding `body` → rerun **everything** after it. Rebuilding `exterior` → rerun `military` and
`interior` too (they parent to doors/wing). After any rerun of exterior/military, finish with:
```python
vx = sys.modules['vx9']
f = bpy.data.objects['Wing_DRSFlap']; vx.set_origin_keep_children(f, (0, 2.17, 1.175))  # DRS hinge
vx.store_rest(); vx.REST['Wing_DRSFlap'] = f.matrix_basis.copy()
bpy.data.objects['Body_TailPanel'].data.materials[0] = vx.M('Grille')
```

### 5.3 How the body is built (`vx9_lib.py`)
- Body = cross-sections ("stations") along Y every 0.04 m (+ extra stations at arch edges and panel cuts) → **136
  stations × 35 rows**. Profile curves are monotone cubic (`pchip`) tables: `W_SH` (shoulder width), `Z_SH` (shoulder
  height), `Z_BASE`, `X_DECK`, `DZ_DECK`, `Z_TOP` (roof/top line), `scoop(y)` (side intake pocket depth).
- Row segments and their starting row index: **A=0, B=3, C=8, D=12, E=15, P=21, F=23…34** (34 = centreline).
  Row 8 is a sharp **concave crease** (bottom of the side-intake pocket) between y≈0.05 and 1.0.
- Panel cut lines (Y, metres): frunk lid −2.02 / −1.13, windshield −1.07 / −0.28, door −0.86 / 0.40, quarter glass 0.72,
  roof rear 0.46, engine glass 0.86, engine cover 1.95, tail 2.03. Seam gap ±0.0022 m.
- Key constants: `L0, L1 = -2.31, 2.31`; `AXF = (-1.30, 0.334, 0.380)` and `AXR = (1.42, 0.364, 0.410)` = (axle y,
  wheel-centre z, arch radius); `TRACK_F 0.852`, `TRACK_R 0.838`.
- **Library note:** later definitions in `vx9_lib.py` override earlier ones (fixes were appended). Always exec the
  whole text block.

### 5.4 Library helpers you'll use
| Helper | Purpose |
|---|---|
| `surf(y, u)` / `surf_n(y, u)` | point / outward normal on the right-hand (+X) body surface at station y, row u |
| `on_body(name, [(y,u),…], off, th, mats, col, side='both'|'L'|'R', subdiv, merge)` | body-conforming decal panel (vents, lights, hatches) — uses `conform_fill` so it follows creases |
| `on_plane(name, [(x,z),…], yfun, off, th, mats, col, ydir, merge)` | decal on the flat nose (`vx.nose_y`) or tail (`lambda x,z: vx.L1`, `ydir=1`) |
| `mk(name, V, F, mats=[...], col=..., sharp=35)` | create mesh object (auto cleans, parents to root, marks sharp edges) |
| `solidify(ob, th)` | thickness (even offset OFF, **quality normals ON**) |
| `box_vf, prism_vf, lathe_vf, tube_vf, sweep_vf, merge_vf, mirror_vf, airfoil` | raw (verts, faces) builders |
| `poly_fill` (ear-clipping, concave-safe) / `conform_fill` (cuts on every station + row line) | 2D polygon fills |
| `set_origin_keep_children(ob, point)` | move an object's pivot without moving it or its children |
| `store_rest()`, `reset_pose()`, `deploy_pose()` | closed pose / everything-deployed preview pose |

### 5.5 Moving parts — hinges (Blender coords, metres) and motions
| Part | Pivot | Motion (Blender local axes) |
|---|---|---|
| `Door_L` / `Door_R` | (∓0.84, −0.84, 0.74) | dihedral: +72° about X, ±12° about Z |
| `Frunk_Lid_L/R` | outer edge, y −1.57 | clamshell: ∓105° about Y |
| `Mil_RocketPod_L/R` | (∓0.25, −1.72, 0.395) | +0.24 Z, then −12° about X (nose up) |
| `Mil_RocketPod_Lift_L/R` | — | stretches up with the pod |
| `Hatch_SideGun_L/R` | top edge (`surf(0.72,10.5)`) | ±75° about Y |
| `Mil_GunPod_L/R` | (∓0.52, 0.76, 0.40) | slides ∓0.36 X (outward) after hatch opens |
| `Mil_ArmorShutter_L/R` | (inside door) | +0.33 Z and ±0.17 X (relative to door) |
| `Aero_ActiveWing` (empty) | (0, 2.03, 0.95) | airbrake: +0.08 Z |
| `Wing_DRSFlap` | (0, 2.17, 1.175) | up to −25° about X |
| Wheels `Wheel_FL/FR/RL/RR` (empties) | wheel centre | spin about X; calipers live on `Upright_*` (don't spin) |

Each has a `vx_anim` custom property with the same note.

### 5.6 Export to Roblox (paste into Blender MCP)
Merges objects per (moving group, material), bakes stud scale, keeps each group's pivot, splits >18k-tri meshes.
```python
import bpy, sys, os
from mathutils import Vector, Matrix
vx = sys.modules['vx9']; vx.reset_pose()
S = 1/0.28
ex = bpy.data.collections['VX9_RobloxExport']
for o in list(ex.objects): bpy.data.objects.remove(o, do_unlink=True)
lc = bpy.context.view_layer.layer_collection.children['VX9_RobloxExport']; lc.exclude = False
ROOTS = ['Mil_ArmorShutter_L','Mil_ArmorShutter_R','Hatch_SideGun_L','Hatch_SideGun_R','Mil_GunPod_L','Mil_GunPod_R',
         'Mil_RocketPod_L','Mil_RocketPod_R','Mil_RocketPod_Lift_L','Mil_RocketPod_Lift_R','Frunk_Lid_L','Frunk_Lid_R',
         'Door_L','Door_R','Wing_DRSFlap','Aero_ActiveWing','Wheel_FL','Wheel_FR','Wheel_RL','Wheel_RR']
def group_of(o):
    p = o
    while p:
        if p.name in ROOTS: return p.name
        p = p.parent
    return 'Body'
dg = bpy.context.evaluated_depsgraph_get(); buckets = {}
for o in vx.coll('VX9_Wraith').all_objects:
    if o.type != 'MESH' or o.hide_render: continue
    g = group_of(o); e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world
    mats = [m.name.replace('VX9_','') if m else 'None' for m in me.materials] or ['None']
    co = [mw @ v.co for v in me.vertices]
    for p in me.polygons:
        mn = mats[p.material_index] if p.material_index < len(mats) else mats[0]
        b = buckets.setdefault((g, mn), {'V': [], 'F': [], 'map': {}}); idx = []
        for vi in p.vertices:
            key = (o.name, vi)
            if key not in b['map']: b['map'][key] = len(b['V']); b['V'].append(co[vi] * S)
            idx.append(b['map'][key])
        b['F'].append(tuple(idx))
    e.to_mesh_clear()
tri = lambda F: sum(len(f) - 2 for f in F); made = []
def emit(name, V, F, mat, piv):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in V], [], F); me.validate()
    o = bpy.data.objects.new(name, me); ex.objects.link(o)
    me.materials.append(bpy.data.materials.get('VX9_' + mat))
    me.transform(Matrix.Translation(-piv)); o.location = piv
    vx.mark_sharp(me, 40); made.append((name, tri(F)))
for (g, mn), b in sorted(buckets.items()):
    piv = Vector((0,0,0)) if g == 'Body' else bpy.data.objects[g].matrix_world.translation * S
    name = 'RBX_%s_%s' % (g, mn); V, F = b['V'], b['F']
    if tri(F) <= 18000: emit(name, V, F, mn, piv)
    else:
        Fs = sorted(F, key=lambda f: sum(V[i].y for i in f) / len(f)); chunks = []; cur = []; ct = 0
        for f in Fs:
            cur.append(f); ct += len(f) - 2
            if ct >= 16000: chunks.append(cur); cur = []; ct = 0
        if cur: chunks.append(cur)
        for k, ch in enumerate(chunks):
            used = sorted({i for f in ch for i in f}); rm = {i: j for j, i in enumerate(used)}
            emit('%s_%d' % (name, k+1), [V[i] for i in used], [tuple(rm[i] for i in f) for f in ch], mn, piv)
bpy.context.view_layer.update()   # REQUIRED before reading matrix_world of the new objects
bpy.ops.object.select_all(action='DESELECT')
for o in ex.objects: o.select_set(True)
bpy.context.view_layer.objects.active = ex.objects[0]
bpy.ops.export_scene.fbx(filepath=r"C:\Users\nicst\OneDrive\Documents\VX9_Wraith_Roblox.fbx",
    use_selection=True, object_types={'MESH'}, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
    axis_forward='Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True,
    add_leaf_bones=False, bake_anim=False)
bpy.ops.object.select_all(action='DESELECT'); lc.exclude = True
bpy.ops.wm.save_mainfile()
result = {'meshes': len(made), 'tris': sum(m[1] for m in made)}
```
Expected: **111 meshes, ~145k tris, overall 7.70 × 17.02 × 4.47 (Blender X × Y × Z, studs)**.
Export names `RBX_<Group>_<Material>[_n]` are what the Roblox setup module parses — don't rename.

### 5.7 Quality checks to run before every export
- **Spike check** (solidify blow-ups): compare each object's evaluated bbox to its raw bbox; growth > 3× thickness = bad.
- **Decal clearance**: BVH of raw body panels (`Body_*`, `Door_L/R`, `Frunk_Lid_L/R`) → for every decal vertex **and face
  centre**, signed distance along the surface normal must be ≥ ~3 mm (edge contacts at the headlight/nose join are OK).
- **Envelope**: no export vertex outside |x| > 3.9, |y| > 8.7, z > 4.7 studs, z < −0.1.
- Check the importer's **File Dimensions** reads `7.70, 4.47, 17.02` before clicking Import.

---

## 6. Roblox side

### 6.1 Importing (Studio GUI)
1. Home tab → **Import** (3D Importer) → pick `Documents\VX9_Wraith_Roblox.fbx`.
2. Settings (Studio Default preset is correct): Import Only as a Model ✔, Upload to Roblox ✔, Add to Workspace ✔,
   Set Pivot to Scene Origin ✔, World Forward **Front**, World Up **Top**, Scale Unit **Stud**, Scale Factor **1**.
3. Import → new asset ID appears in Asset Manager; model lands in Workspace as `VX9_Wraith_Roblox` (111 MeshParts).
4. Run the setup module in the Command Bar (or `execute_luau`, Edit):
   ```lua
   local car = require(game.ServerStorage._DevTools.VX9_ImportSetup)(workspace.VX9_Wraith_Roblox)
   car.Parent = game.ServerStorage.AdminVehicles   -- replace the old VX9_Wraith there first
   ```
   (When calling from `execute_luau` repeatedly, `require(module:Clone())` so edits to the module are picked up.)

### 6.2 What `ServerStorage._DevTools.VX9_ImportSetup` does
- `PivotTo(identity)`; auto `ScaleTo(1/0.28)` if the import is metre-scale (< 8 studs long).
- Creates `VX9_Wraith` Model with invisible anchored **`Root`** (PrimaryPart, size 1.9×0.5×4.4 m, pivot on the ground
  under the car's centre via `PivotOffset`).
- Sorts parts into `Body`, `Doors`, `Wheels`, `Aero`, `Military` (sub-models per moving group), renames parts to their
  material name (`Paint`, `Tire`, `PanelInner_1`, …), sets materials, `CanCollide/CanQuery/CanTouch = false`,
  `Massless`, `CollisionFidelity.Box`, `RenderFidelity.Automatic`, `CastShadow=false` for lights/interior.
- Adds `Collision` model: 4 invisible boxes (the only colliders; bullets/raycasts hit them) — metres:
  `Hull_Lower` c(0,0.45,0) s(1.96,0.66,4.55); `Hull_Cabin` c(0,0.95,0) s(1.30,0.34,2.0);
  `Hull_RearDeck` c(0,0.83,1.45) s(1.85,0.12,1.7); `Hull_Wing` c(0,1.15,2.09) s(1.70,0.18,0.42).
- WeldConstraints from Root to every part (in `Root.Welds`).
- Sets each moving group's `WorldPivot` to its hinge and a **`Motion`** attribute (plain-English movement).
- Car attributes: `AdminOnly=true`, `Source`, `Scale="1 stud = 0.28 m"`. Warns in Output on unknown names.

### 6.3 Finished model structure
```
VX9_Wraith (Model, PrimaryPart = Root, nose → −Z)
├─ Root (Part, anchored, invisible) └─ Welds (Folder of WeldConstraints)
├─ Body        (MeshParts by material + FrunkLid_Left/Right)
├─ Doors       Door_Left, Door_Right
├─ Wheels      FrontLeft, FrontRight, RearLeft, RearRight  (Tire, Rim, RimLip, Rotor, Alu, Accent)
├─ Aero        RearWing, DRSFlap
├─ Military    SideGunHatch_*, SideGunPod_*, RocketPod_*, RocketLift_*, ArmorShutter_*  (Left/Right)
└─ Collision   Hull_Lower, Hull_Cabin, Hull_RearDeck, Hull_Wing
```
Locations in the place:
- **Master:** `ServerStorage.AdminVehicles.VX9_Wraith` (clients can't see ServerStorage — verified).
- **Viewing copy:** `Workspace.AdminPreview.VX9_Wraith`, pivot `CFrame.lookAt((50.8, 38.97, 192), (30, 38.97, 180))`,
  beside the Haven Trading Post, tyres measured on the ground. **Visible to every player in a live server** — delete
  or move before publishing if the car should stay secret.

### 6.4 Roblox material map (final, tuned for Roblox lighting)
| Blender | Roblox material | RGB | Refl. | Transp. |
|---|---|---|---|---|
| Paint | SmoothPlastic | 78,82,88 | 0.10 | |
| Carbon | SmoothPlastic | 17,18,20 | 0.15 | |
| CarbonMatte / WellLiner | Fabric | 20,20,22 / 14,14,15 | | |
| PanelInner / Grille / Housing / Plastic | SmoothPlastic | 18,18,19 / 10,10,11 / 14,14,15 (0.15) / 22,22,24 | | |
| Glass | Glass | 30,36,42 | 0.2 | **0.62** (see-through from cockpit) |
| GlassDark / Lens | Glass | 8,10,12 / 220,225,230 | 0.3 | 0.1 / 0.7 |
| Tire / Rubber | Rubber | 26,26,26 / 20,20,20 | | |
| Alu / Steel / Rotor / Gunmetal / Armor | Metal | 140,142,147 / 72,74,78 / 70,70,72 / 30,31,34 / 62,66,58 | | |
| Titanium / BurntTi / Exhaust / Engine / Copper | Metal | 64,65,70 / 48,46,54 / 92,86,82 / 32,32,35 / 200,110,60 | | |
| Chrome / RimLip | Foil | 205,207,212 (0.4) / 175,177,182 (0.3) | | |
| Rim | SmoothPlastic | 16,16,18 | 0.08 | |
| Accent / Caliper / Stitch / Belt | SmoothPlastic/Fabric | 242,92,10 (belt 228,76,10) | | |
| Hazard / GuardRed | SmoothPlastic | 242,192,12 / 150,12,8 | | |
| LED / Amber / TailRed | Neon | 230,238,255 / 255,138,20 / 255,24,12 | | |
| HUD / Screen | Neon | 30,200,255 / 18,120,175 | | 0.25 / 0.3 |
| Alcantara / Leather | Fabric / Leather | 26,26,27 / 30,30,32 | | |

Carbon weave is **not** carried over (Roblox has no carbon material) — add a SurfaceAppearance/MaterialVariant later.

### 6.5 Hinge pivots in Roblox (studs, car space) = `B(...)` of the Blender table
Door_Right `B(-0.84,-0.84,0.74)`, Door_Left `B(0.84,-0.84,0.74)`, wheels `B(∓0.852,-1.30,0.334)` front /
`B(∓0.838,1.42,0.364)` rear, RearWing `B(0,2.03,0.95)`, DRSFlap `B(0,2.17,1.175)`, SideGunPod `B(∓0.52,0.76,0.40)`,
RocketPod `B(∓0.25,-1.72,0.395)`; frunk lids & hatches = outer/top bbox edge; lifts & shutters = bbox centre.
To animate later: replace the WeldConstraint for a group with a Motor6D/HingeConstraint at its `WorldPivot`.

### 6.6 Verification snippets
```lua
-- (Server, during playtest) car stays whole
local car = workspace.AdminPreview.VX9_Wraith; local root = car.PrimaryPart; local bad = 0
for _, d in car:GetDescendants() do
  if d:IsA("BasePart") and d ~= root and d.AssemblyRootPart ~= root then bad += 1 end end
return bad  -- expect 0
```
Last full check (3 Oct): server — pivot unchanged, Root anchored, 0 unwelded parts, one assembly; client — 111/111
meshes loaded, AdminVehicles not visible; Output — no car-related errors.

---

## 7. The game (Survival Island) — structure you'll touch

- **Workspace:** `Map` (Foliage, Zones, Bridges, Haven, Towns, Sites, Props, `HavenSpawn` SpawnLocation at
  **(30, 39.3, 180)**), `_ZView`, `_ZBase`, `AdminPreview`, Terrain. Map is 2× scale (16,384² studs, island r≈7,000).
- **ServerScriptService:** `WorldBootstrap`, `GraphicsSettingsServer`, `SafeZoneService`, `Gameplay`, `Systems/`
  (LootTables, InventoryService, VitalsService, CombatService, EquipmentService, LootService, **AdminService**,
  WeaponService, LootPlacer, ContainerService, MedicalService, ZombieService).
- **ReplicatedStorage:** `Shared` (ItemDB, Net, GraphicsProfiles, …), `Items`.
- **ServerStorage:** `LightingBackup`, `_DevTools` (GunForge, Generated, _AssetStudio, **VX9_ImportSetup**), `MapGen`
  (MapGenerator seed 7351, InteriorTemplates, PropLibrary = script-free Creator Store car/wreck models…),
  **`AdminVehicles`**.
- Tags: `LootSpawn` (3,978), `ZombieSpawn` (356), `Building`, `LootContainer` (4,404), `WorldProp` (304);
  `workspace.WorldReady`.
- All gameplay is **server-authoritative**: the client asks, the server checks everything.

### 7.1 AdminService (use this for anything admin-only — e.g. spawning the car)
- `Admin.Allowed(player)`: `true` in Studio; live → game owner (user place) or group rank 255 (group place).
- On join, allowed players get attribute **`IsAdmin = true`** (client shows admin UI only then).
- Remote: `Net.Event("Admin")` → client `Remotes.Admin:FireServer(action, a, b)`; server re-checks `Allowed` on every
  request; flood guard 12 actions/second.
- Actions: `"Give", itemId, count` · `"Kit", name` (Survivor, Military, Mechanic, Arsenal, Legendary, Medic) ·
  `"Heal"` · `"Clear"` · `"GunCond", 0-100` · `"JamNext"`. Item Spawner panel on **F2**.
- Natural next step: add `"SpawnCar"` → clone `ServerStorage.AdminVehicles.VX9_Wraith` in front of the admin.

### 7.2 Other systems (summary from the build log)
Inventory (DataStore `PlayerInventory_v1`, hotbar 6, pockets, vest, backpack, gear slots), Vitals (food ~55 min,
water ~40 min), DayZ-style loot economy (200-stud cells), 9 server-checked guns in first person, 491 furnished houses
with 4,404 searchable containers (hold E), graphics tiers Low→Ultra on **F3**, 304 roadside wrecks.
Full details: project doc `claude/World build log.md`.

---

## 8. Known issues / open items

- **Car is not drivable yet** — needs chassis (VehicleSeat or custom raycast suspension), animations for doors /
  hatches / pods / wing, an admin `SpawnCar` action, and a carbon texture.
- Exhaust tips are slightly see-through when viewed from very close at an angle (open tube) — cosmetic.
- `DataStoreService: StudioAccessToApisNotAllowed` in Output → Game Settings → Security → *Enable Studio Access to API
  Services* (otherwise inventory never loads/saves in Studio tests). Not caused by the car.
- `MaterialManager … debug.profileEnd()` stack in Output = Studio's own built-in plugin, harmless.
- `FlyToggle` (StarterPlayerScripts, L key) works for every player in live games — restrict before publishing.
- Six "Roblox Generated Object" models near Haven at ~(-13, 39, 18) — origin unknown, left in place.
- Viewing copy of the car in `Workspace.AdminPreview` is public — remove before publishing if needed.

---

## 9. Lessons learned (bugs hit in this project — don't repeat)

**Blender**
1. Parenting: set `child.matrix_parent_inverse = parent.matrix_world.inverted()` *or* build in local space; otherwise
   offsets double. Call `bpy.context.view_layer.update()` before reading `matrix_world` of objects you just moved/made.
2. Moving a pivot after children are attached moves the children → use `set_origin_keep_children`.
3. `bmesh` n-gon triangulation mis-fills **concave** polygons (5× area) → use the ear-clipping `poly_fill`.
4. Surface normal at the **centreline row (u=34)** used a zero-length forward step and returned (1,0,0) (sideways) →
   decals there sat on the paint and z-fought. Fixed with a backward step in `surf_n`.
5. Decals: keep **≥ 4 mm** off the body (≥ 7–8 mm on concave/curvy spots like the rear outlet, headlight corners, side
   hatches), stack layers ≥ 3–4 mm apart, and use `conform_fill` so they follow creases (coarse faces across a crease
   dip under the body).
6. Never place a decal strip across the row-8 concave crease — offsetting folds the mesh; **Solidify then explodes it
   into multi-metre spikes** (the thin "white lines in the sky" in Roblox). Side-gun fins now at u = 4.2, 5.25, 6.3,
   7.35, 8.4, 9.45. Solidify uses quality normals + no even offset.
7. Blender MCP: `result` must be a dict. Sharp-crease lofts need extra stations at panel cuts and arch edges.
8. Old metre-scale export read as studs in Roblox → car 3.57× too small. Export now bakes ×(1/0.28).

**Roblox / tools**
9. Imported FBX → every MeshPart is grey Plastic, unanchored, unwelded, full collision. Always run `VX9_ImportSetup`.
10. Neon/Glass/Metal read differently from Blender: Titanium looked rusty, burnt-titanium looked purple, tinted glass
    made the cockpit too dark → values in §6.4 are the corrected ones.
11. `CollisionFidelity` and `RenderFidelity` *can* be set from Studio (plugin-level) Luau.
12. Computer use: `open_application("Roblox Studio")` launches a **second** empty Studio start window — close it with
    its X (top-right) to get back to the place. While computer-use is active, Blender's window is hidden, so Blender
    viewport screenshots come back black → verify with numeric checks instead. Release the lock when done.
13. `screen_capture` with `camera_position` / `look_at_position` is the fastest visual check; compute camera points in
    car space with `car:GetPivot():PointToWorldSpace(Vector3.new(x,y,z) * (1/0.28))`.

---

## 10. TX-6 "Bastion" armoured super-SUV (built 4 Oct 2026, cloud session)

Original military super-SUV, *inspired by* the Terradyne Gurkha (general proportions only, not a replica).
Built entirely by Python scripts in **headless Blender 5.2.2** in a Claude Code cloud container, then committed here.

### 10.1 Files (all in this repo)
| What | Path |
|---|---|
| Blender file (build scripts also stored inside as text blocks `tx6_*.py`) | `blender/TX6_Bastion.blend` |
| Build scripts (one module per system) | `blender/tx6/*.py` — `lib, body, wheels, armor, bumpers, lights, roof, equipment, details, interior, engine, poses` |
| Rebuild everything from scratch (~3 s) | `bpy-run blender/build.py` (writes the .blend) |
| Automated inspection | `bpy-run blender/checks.py rest|combat|deploy|hood` (floating parts, moving-part collisions, low points, tri budget) |
| Renders / contact sheets | `bpy-run blender/render.py OUT.png "front34;side;..." [width] [samples] [pose]` (OUT ending in `/` = one file per view) |
| Roblox export | `bpy-run blender/export_roblox.py` → `exports/TX6_Bastion_Roblox.fbx` + `exports/TX6_Bastion_Rig.json` |
| Showcase renders | `renders/01..09_*.png` |

Cloud setup (container is temporary, redo each new session): Blender comes from PyPI, not blender.org (blocked):
`uv venv --python 3.13 /root/blender-env && uv pip install --python /root/blender-env/bin/python bpy==5.2.2 pillow numpy`,
then `printf '#!/bin/sh\nexec /root/blender-env/bin/python "$@"\n' > /usr/local/bin/bpy-run && chmod +x /usr/local/bin/bpy-run`.
EEVEE needs `apt-get install libegl1 libegl-mesa0 libgl1-mesa-dri`; renders use **Cycles CPU** (faster here).

### 10.2 Conventions (different from the VX-9!)
- Metres, Z up, nose → **−Y**. **`_L` = vehicle LEFT = +X, `_R` = vehicle RIGHT = −X** (true sides, no side-label trap).
- Front/rear: `F`/`R` (e.g. `Door_FL`, `Wheel_RR`). Materials prefixed `TX6_` (`lib.M('Paint')`).
- Every top-level part is parented to empty `TX6_Root`; collections `TX6_Body, Armor, Doors, Glass, Wheels, Suspension,
  Lights, Turret, Missiles, Sensor, Equipment, Details, Interior, Engine`.
- All moving parts have **identity rotation at rest** and their **origin on the real hinge**; each carries `tx_anim`
  (plain English) and, if keyed, `tx_deploy` (e.g. `rot Y +120 between frames 10-35`).
- Build in world coordinates, parent with `lib.parent_keep` (computes the parent inverse without a depsgraph update).

### 10.3 Size
Body 6.00 m long (7.03 m incl. bumpers, hook and spare), 2.44 m body / 2.71 m over flares / 3.14 m over mirrors,
roof 2.48 m, turret shield top 3.24 m. Wheelbase 3.95 m, track ±1.10 m, 47" tyres (R 0.60 m) on 22.5" beadlocks.
Roblox: **11.21 × 25.09 × 13.69 studs** (X × Z × Y incl. mirrors and whip antennas). ~224k triangles, 172 export meshes,
largest 15,000 tris.

### 10.4 How the body is made (`body.py`)
Outer + inner (60 mm armour) lofts of 12-point cross-sections → closed shell. Openings and panels are cut with EXACT
booleans: each door/hatch = shell ∩ (outline shrunk 3.5 mm), body = shell − (outline grown 3.5 mm) → real 7 mm gaps.
Outlines are in `body.py` (`FD_OUT, RD_OUT, LK_OUT, FU_OUT, FW_WIN, RW_WIN, REAR_DOOR, HOOD_OUT, MB_OUT`).
Key helpers in `lib.py`: `xs(z)` side surface x (tumblehome above the 1.62 m beltline), `zh(y)` hood height,
`y_ws(z)` windshield, `side_pt/side_n`, `prism, ring_prism, loft, lathe_vf, sweep_vf, tube_vf, offset2, bolts`.

### 10.5 Moving parts (Blender pivots → see `exports/TX6_Bastion_Rig.json` for Roblox studs)
| Part | Motion | Keyed frames |
|---|---|---|
| `Turret_Rotor` → `Turret_Cradle` → `Turret_Minigun` → `Turret_Barrels` | traverse Z / elevate X (negative = up) / barrels spin local Y | 30-70 / 50-75 / 60-180 |
| `Missile_Hatch_L/R` | ±120° about Y (flip outward) | 10-35 |
| `Missile_Lift_L/R` → `Missile_Pod_L/R` | +0.46 m Z, then −18° X (nose up) | 35-60, 60-80 |
| `Sensor_Mast` → `Sensor_MastUpper` → `Sensor_Head` → `Sensor_EOBall` | +90° X raise / +0.55 m local Y / spin local Y / tilt X | 15-45 / 45-65 / 65-180 / 65-80 |
| `Deploy_WindshieldShield` (child of `Hood`) | −113.6° X (flips up in front of the windshield) | 1-30 |
| `Deploy_Shutter_FL/FR/RL/RR` (children of doors) | ±171° Y (flip up over the windows) | 5-38 |
| `Door_FL/FR/RL/RR`, `Door_Rear`, `Spare_Carrier` | ∓70° Z, −100° Z, +95° Z | 95-130 |
| `Locker_Door_L/R`, `Locker_Tray_L` | ∓100° Y (awning), +0.42 m X | 92-135 |
| `Fuel_Door_L`, `Utility_Hatch_R`, `Searchlight`, `Hood` | ∓95° Z, ∓95° Z, pan Z, −55° X (not keyed) | |
| `Upright_*` → `Wheel_*` | steer Z (front) → spin X | |
Timeline poses for renders/checks: `rest`=frame 1, `combat`=85, `deploy`=140 (`poses.apply(name)`).
Seats (empties, `tx_seat`): `Seat_Driver` (left, LHD), `Seat_Passenger`, `Seat_RearL/R`, `Seat_Gunner` (turret sling seat).
Gameplay notes: hood can only open with the windshield shield stowed (it rides on the hood); don't traverse the gun
through the raised sensor mast (rear arc) — limit traverse when the mast is up.

### 10.6 Roblox import (not done yet — needs Studio on Nic's PC)
Import `exports/TX6_Bastion_Roblox.fbx` with the same 3D-Importer settings as §6.1 (Stud, scale 1, Front/Top). Mesh
names are `RBX_<Group>_<Material>[_n]`; `<Group>` = moving group or `Body`. A `TX6_ImportSetup` module (like
`VX9_ImportSetup`) still needs writing: weld everything to a Root, set materials (map like §6.4; TX6 colours: Paint
olive ≈ 74,78,58, ArmorPaint ≈ 66,70,52, Coating near-black textured), add collision boxes, set group pivots from the
rig JSON and replace welds with Motor6D/HingeConstraints for the moving groups.

### 10.7 Lessons learned (TX-6 session)
1. `checks.py` found 19 floating parts on the first run (gaps of 2–70 mm); always run it after a change — renders hide it.
2. Gun shields/flat panels between polar points sit at `r·cos(half-angle)`, not `r` — mount things on the chord plane.
3. Hinge axes on tumblehome sides must sit outside the surface at the **lowest** point of the door, or the door swings
   into the body (fuel door bug).
4. Packaging: the missile bays and side lockers overlapped inside the hull → lockers are L-shaped (deep low, shallow high).
5. Brake hoses must route inside the wheel barrel (radius < rim inner radius) or they cut through the tyre.
6. `boolean()` applies *all* modifiers — add bevels after booleans, never before (double-bevel bug).
