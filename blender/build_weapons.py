"""Build the Survival Island weapon pack (five weapons, presentation studio, UVs) and save the .blend.

Usage:  bpy-run blender/build_weapons.py [CODE ...] [--out PATH]
        CODE = R12 MAKO9 TM308 SP9 BLMG (default: all five)
        --out  default weapon_output/SurvivalWeaponPack.blend (full build only; partial builds need --out)
"""
import sys, os, time, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
from weapons import lib

MODULES = {'R12': 'r12', 'MAKO9': 'mako9', 'TM308': 'trailmark', 'SP9': 'sparrow9', 'BLMG': 'bastion'}
ROWS = [['TM308', 'R12'], ['BLMG', 'MAKO9', 'SP9']]      # presentation: top row, bottom row (left -> right in camera)

args = [a for a in sys.argv[1:] if not a.endswith('.py')]
out = None
if '--out' in args:
    i = args.index('--out')
    out = args[i + 1]
    del args[i:i + 2]
codes = [a for a in args if a in MODULES] or list(lib.ORDER)
if out is None:
    assert set(codes) == set(lib.ORDER), 'partial builds need --out (never overwrite the pack with a subset)'
    out = os.path.join(REPO, 'weapon_output', lib.PACK_FILE + '.blend')


def bbox(code):
    root = bpy.data.objects[code + '_Root']
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in bpy.data.collections[lib.WEAPONS[code][0]].all_objects
           if o.type == 'MESH' for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)])
    mx = Vector([max(p[i] for p in pts) for i in range(3)])
    return mn - root.location, mx - root.location


t0 = time.time()
lib.new_pack()
for code in lib.ORDER:
    if code not in codes:
        continue
    t = time.time()
    importlib.import_module('weapons.' + MODULES[code]).build()
    lib.clear_scratch()
    n = len(bpy.data.collections[lib.WEAPONS[code][0]].all_objects)
    print('built %-6s %5.1fs  objects=%d' % (code, time.time() - t, n), flush=True)

# ------------------------------------------------------------------ UVs: one smart-UV atlas layout per weapon
for code in codes:
    obs = [o for o in bpy.data.collections[lib.WEAPONS[code][0]].all_objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, area_weight=0.0, correct_aspect=True,
                             scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

# ------------------------------------------------------------------ presentation layout (two rows, muzzles to the right)
BB = {c: bbox(c) for c in codes}
GAP_Y, GAP_Z, Z0 = 0.14, 0.12, 0.34
layout = {}
z_cursor = Z0
for row in reversed(ROWS):
    row = [c for c in row if c in codes]
    if not row:
        continue
    width = sum(BB[c][1].y - BB[c][0].y for c in row) + GAP_Y * (len(row) - 1)
    y_cursor = width / 2
    zlow = min(BB[c][0].z for c in row)
    hmax = max(BB[c][1].z - BB[c][0].z for c in row)
    for c in row:
        mn, mx = BB[c]
        loc = Vector((0.0, y_cursor - mx.y, z_cursor - zlow))
        bpy.data.objects[c + '_Root'].location = loc
        layout[c] = (loc, loc + mn, loc + mx)
        y_cursor = loc.y + mn.y - GAP_Y
    z_cursor += hmax + GAP_Z
bpy.context.view_layer.update()
lib.presentation(layout)
# cameras: lineup + one three-quarter close-up per weapon
mn = Vector([min(l[1][i] for l in layout.values()) for i in range(3)])
mx = Vector([max(l[2][i] for l in layout.values()) for i in range(3)])
cen = (mn + mx) / 2
w = max(mx.y - mn.y, (mx.z - mn.z) * 16 / 9)
cam = lib.camera('CAM_Lineup', (cen.x - 1.42 * w, cen.y, cen.z + 0.16 * w), cen + Vector((0, 0, -0.02 * w)), 50)
bpy.context.scene.camera = cam
for c, (loc, a, b) in layout.items():
    cc = (a + b) / 2
    L = max(b.y - a.y, (b.z - a.z) * 2.25)
    lib.camera('CAM_%s_34' % c, cc + Vector((-1.25 * L, -0.72 * L, 0.48 * L)), cc, 50)

# ------------------------------------------------------------------ store the build scripts inside the .blend
for d, pre in (('weapons', 'weapons_'), ('common', 'common_')):
    for fn in sorted(os.listdir(os.path.join(HERE, d))):
        if fn.endswith('.py') and fn != '__init__.py':
            t = bpy.data.texts.get(pre + fn) or bpy.data.texts.new(pre + fn)
            t.from_string(open(os.path.join(HERE, d, fn)).read())
for fn in ('build_weapons.py',):
    t = bpy.data.texts.get(fn) or bpy.data.texts.new(fn)
    t.from_string(open(os.path.join(HERE, fn)).read())
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
tot = 0
for c in codes:
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
               for o in bpy.data.collections[lib.WEAPONS[c][0]].all_objects if o.type == 'MESH')
    mn_, mx_ = BB[c]
    sz = mx_ - mn_
    L, H, W = sz.y * lib.S, sz.z * lib.S, sz.x * lib.S
    tL, tH, tW = lib.WEAPONS[c][3]
    print('%-6s tris %6d  size L %.2f H %.2f W %.2f studs  (target %.1f x %.2f x %.2f)' % (c, tris, L, H, W, tL, tH, tW))
    tot += tris
print('saved', out, 'tris', tot, 'time %.1fs' % (time.time() - t0))
