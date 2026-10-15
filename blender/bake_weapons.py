"""Bake one texture atlas per weapon from the procedural materials (Cycles, EMIT trick).

Usage: bpy-run blender/bake_weapons.py [CODE ...] [--size 2048] [--samples 16] [--blend PATH] [--pack=CODE,CODE]
       --pack=...  re-pack earlier PNGs of those weapons (after a rebuild that left them unchanged); bake only the
                   CODEs listed explicitly

Every weapon already has one shared smart-UV layout over all its parts (build_weapons.py). For each weapon this bakes
    weapon_output/textures/<Name>_BaseColor.png   (sRGB)  colour incl. wear, grime, scratches, dark recesses
    weapon_output/textures/<Name>_Roughness.png   (linear)
    weapon_output/textures/<Name>_Metalness.png   (linear)
by routing the Principled input into a temporary Emission shader and baking EMIT (works for metals too, unlike the
DIFFUSE pass). The images are packed into the .blend (no broken paths); the procedural materials stay untouched.
In Roblox they are used as a SurfaceAppearance (ColorMap / RoughnessMap / MetalnessMap) shared by all the weapon's
MeshParts, because every exported mesh keeps the atlas UVs.
"""
import sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import bpy

args = [a for a in sys.argv[1:] if not a.endswith('.py')]


def opt(name, default):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


SIZE = int(opt('--size', 2048))
SAMPLES = int(opt('--samples', 16))
OUT = os.path.join(REPO, 'weapon_output')
BLEND = opt('--blend', os.path.join(OUT, 'SurvivalWeaponPack.blend'))
TEX = os.path.join(os.path.dirname(BLEND), 'textures')
os.makedirs(TEX, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
from weapons import lib
codes = [a for a in args if a in lib.WEAPONS] or [c for c in lib.ORDER if bpy.data.collections.get(lib.WEAPONS[c][0])]
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = False
sc.render.bake.margin = 8
sc.render.bake.target = 'IMAGE_TEXTURES'
for o in sc.objects:
    o.animation_data_clear()
from common import poses
poses.apply_state()

MAPS = [('BaseColor', 'Base Color', 'sRGB'), ('Roughness', 'Roughness', 'Non-Color'), ('Metalness', 'Metallic', 'Non-Color')]


def route(mat, socket_name):
    """temporarily feed the Principled input `socket_name` into an Emission shader on the material output."""
    nt = mat.node_tree
    pr = nt.nodes.get('Principled BSDF')
    outn = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.name = '_bake_emit'
    em.inputs['Strength'].default_value = 1.0
    sock = pr.inputs[socket_name]
    if sock.is_linked:
        nt.links.new(sock.links[0].from_socket, em.inputs['Color'])
    else:
        v = sock.default_value
        em.inputs['Color'].default_value = (v[0], v[1], v[2], 1) if hasattr(v, '__len__') else (v, v, v, 1)
    prev = outn.inputs['Surface'].links[0].from_socket if outn.inputs['Surface'].is_linked else None
    nt.links.new(em.outputs['Emission'], outn.inputs['Surface'])
    return prev


def unroute(mat, prev):
    nt = mat.node_tree
    outn = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
    for n in [n for n in nt.nodes if n.name.startswith('_bake')]:
        nt.nodes.remove(n)
    if prev is not None:
        nt.links.new(prev, outn.inputs['Surface'])


report = {}
PACK_ONLY = [a for a in sys.argv[1:] if a.startswith('--pack=')]
if PACK_ONLY:
    # re-pack atlases that were baked earlier (after a rebuild that did not change these weapons' geometry / UVs)
    for code in PACK_ONLY[0][7:].split(','):
        name = lib.WEAPONS[code][1]
        for map_name, sock, cs in MAPS:
            img_name = '%s_%s' % (name, map_name)
            img = bpy.data.images.load(os.path.join(TEX, img_name + '.png'))
            img.name = img_name
            img.colorspace_settings.name = cs
            img.use_fake_user = True
            img.filepath = '//textures/%s.png' % img_name
            img.pack()
            print('packed', img_name, flush=True)
    # with --pack=..., only the weapons named explicitly on the command line are baked
    codes = [a for a in args if a in lib.WEAPONS and a not in PACK_ONLY[0][7:].split(',')]
for code in codes:
    t0 = time.time()
    name = lib.WEAPONS[code][1]
    objs = [o for o in bpy.data.collections[lib.WEAPONS[code][0]].all_objects if o.type == 'MESH']
    mats = sorted({m for o in objs for m in o.data.materials if m}, key=lambda m: m.name)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    for map_name, sock, cs in MAPS:
        img_name = '%s_%s' % (name, map_name)
        img = bpy.data.images.get(img_name) or bpy.data.images.new(img_name, SIZE, SIZE, alpha=False)
        img.colorspace_settings.name = cs
        img.use_fake_user = True          # keep the atlas in the .blend although no material uses it
        prevs = {}
        for m in mats:
            node = m.node_tree.nodes.new('ShaderNodeTexImage')
            node.name = '_bake_img'
            node.image = img
            m.node_tree.nodes.active = node
            prevs[m.name] = route(m, sock)
        bpy.ops.object.bake(type='EMIT', margin=8, use_clear=True)
        for m in mats:
            unroute(m, prevs[m.name])
        path = os.path.join(TEX, img_name + '.png')
        img.filepath_raw = path
        img.file_format = 'PNG'
        img.save()
        img.filepath = '//textures/%s.png' % img_name
        img.pack()
        px = list(img.pixels[::4 * 97])
        report.setdefault(code, {})[map_name] = dict(file='textures/%s.png' % img_name, mean=round(sum(px) / len(px), 4))
        print('baked %s %s (%.0fs)' % (code, map_name, time.time() - t0), flush=True)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_mainfile(compress=True)
import json
json.dump(dict(size=SIZE, samples=SAMPLES, maps=report), open(os.path.join(TEX, 'bake_report.json'), 'w'), indent=1)
print('BAKE DONE', report)
