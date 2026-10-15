"""Check the baked atlases: render each weapon with its procedural materials and again with ONLY the baked textures
(BaseColor / Roughness / Metalness on a plain Principled BSDF - what Roblox's SurfaceAppearance will show), side by side.

Usage: bpy-run blender/verify_bake.py [BLEND] [OUT_DIR] [CODE ...] [--width 960] [--samples 24]
Writes OUT_DIR/bake_check_<Name>.png (left = procedural, right = baked textures only) and prints the mean absolute
pixel difference of the two renders (0..255) as a reliability number.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
from PIL import Image, ImageChops, ImageStat

args = [a for a in sys.argv[1:] if not a.endswith('.py')]


def opt(name, default):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


W = int(opt('--width', 960))
SAMPLES = int(opt('--samples', 24))
blend = next((a for a in args if a.endswith('.blend')), os.path.join(REPO, 'weapon_output', 'SurvivalWeaponPack.blend'))
out_dir = next((a for a in args if not a.endswith('.blend') and a not in ('R12', 'MAKO9', 'TM308', 'SP9', 'BLMG')),
               os.path.join(REPO, 'weapon_output', 'previews'))
os.makedirs(out_dir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
from weapons import lib
codes = [a for a in args if a in lib.WEAPONS] or [c for c in lib.ORDER if bpy.data.collections.get(lib.WEAPONS[c][0])]
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = W, int(W * 9 / 16)
sc.cycles.samples = SAMPLES
cam = bpy.data.objects.new('CAM_Verify', bpy.data.cameras.new('CAM_Verify'))
sc.collection.objects.link(cam)
sc.camera = cam
results = {}
for code in codes:
    name = lib.WEAPONS[code][1]
    for c in lib.ORDER:
        col = bpy.data.collections.get(lib.WEAPONS[c][0])
        if col:
            col.hide_render = c != code
    objs = [o for o in bpy.data.collections[lib.WEAPONS[code][0]].all_objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(b) for o in objs for b in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)])
    mx = Vector([max(p[i] for p in pts) for i in range(3)])
    cc = (mn + mx) / 2
    L = max(mx.y - mn.y, (mx.z - mn.z) * 2.25)
    cam.location = cc + Vector((-1.25, -0.72, 0.48)) * L
    cam.rotation_euler = (cc - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50
    p1 = os.path.join(out_dir, '_proc.png')
    sc.render.filepath = p1
    bpy.ops.render.render(write_still=True)
    # baked-only material
    m = bpy.data.materials.new('SW_BakedPreview_' + name)
    nt = m.node_tree
    pr = nt.nodes['Principled BSDF']
    imgs = {k: bpy.data.images.get('%s_%s' % (name, k)) for k in ('BaseColor', 'Roughness', 'Metalness')}
    assert all(imgs.values()), 'missing baked images for %s - run bake_weapons.py first' % name
    for k, sock in (('BaseColor', 'Base Color'), ('Roughness', 'Roughness'), ('Metalness', 'Metallic')):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = imgs[k]
        nt.links.new(n.outputs['Color'], pr.inputs[sock])
    saved = {}
    for o in objs:
        saved[o.name] = list(o.data.materials)
        for i in range(len(o.data.materials)):
            o.data.materials[i] = m
    p2 = os.path.join(out_dir, '_baked.png')
    sc.render.filepath = p2
    bpy.ops.render.render(write_still=True)
    for o in objs:
        for i, mm in enumerate(saved[o.name]):
            o.data.materials[i] = mm
    bpy.data.materials.remove(m)
    a, b = Image.open(p1).convert('RGB'), Image.open(p2).convert('RGB')
    diff = sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3
    sheet = Image.new('RGB', (a.width * 2, a.height))
    sheet.paste(a, (0, 0))
    sheet.paste(b, (a.width, 0))
    path = os.path.join(out_dir, 'bake_check_%s.png' % name)
    sheet.save(path)
    os.remove(p1)
    os.remove(p2)
    results[code] = round(diff, 2)
    print('bake check %s: mean abs difference %.2f / 255 -> %s' % (code, diff, path), flush=True)
print('BAKE CHECK', results)
