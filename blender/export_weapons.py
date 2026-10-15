"""Export the weapon pack: one FBX (+ rig JSON + handoff guide) per weapon into weapon_output/.

Usage: bpy-run blender/export_weapons.py [CODE ...]        (default: all five)

For every weapon the pack .blend is opened, everything that is not that weapon is deleted, the weapon root is moved to
the origin, its rig data (stored on the root) is copied to the scene and common/handoff.export() writes
    weapon_output/<Name>.fbx           meshes merged per (moving group, material), stud scale, Z forward / Y up
    weapon_output/<Name>_Rig.json      schema survival-island-model/1 (pivots, motions, points, materials, systems)
    weapon_output/<Name>_HANDOFF.md    guide for the Roblox coding chat
The FBX is re-imported and every group pivot + the overall size are compared with the rig data (verification block).
"""
import sys, os, json, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import bpy
from weapons import lib
from common import handoff

OUT = os.path.join(REPO, 'weapon_output')
PACK = os.path.join(OUT, lib.PACK_FILE + '.blend')
codes = [a for a in sys.argv[1:] if a in lib.WEAPONS] or list(lib.ORDER)
tmpdir = tempfile.mkdtemp(prefix='sw_export_')
summary = {}
for code in codes:
    coll_name, export_name, display, dims, desc = lib.WEAPONS[code]
    bpy.ops.wm.open_mainfile(filepath=PACK)
    sc = bpy.context.scene
    keep = set(o.name for o in bpy.data.collections[coll_name].all_objects)
    for o in list(bpy.data.objects):
        if o.name not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name not in (coll_name, code + '_RigMarkers', lib.PACK):
            bpy.data.collections.remove(c)
    root = bpy.data.objects[code + '_Root']
    for o in sc.objects:
        o.animation_data_clear()
    root.location = (0, 0, 0)
    for k in ('rig_model', 'rig_channels', 'rig_poses', 'rig_systems', 'rig_notes', 'rig_physics'):
        if root.get(k):
            sc[k] = root[k]
    bpy.context.view_layer.update()
    tmp = os.path.join(tmpdir, export_name + '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=tmp)
    rig = handoff.export(REPO, tmp, renders=False, mat_prefix=lib.PREFIX, out_dir=OUT, file_base=export_name)
    v = rig['verification']
    # extra verification: the atlas UVs survived the merge + FBX round trip
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(OUT, export_name + '.fbx'), axis_forward='Z', axis_up='Y')
    imp = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    no_uv = [o.name for o in imp if not o.data.uv_layers]
    if no_uv:
        v['problems'].append('meshes without UVs after re-import: %s' % no_uv)
        v['passed'] = False
    v['uv_meshes'] = len(imp) - len(no_uv)
    rj = os.path.join(OUT, export_name + '_Rig.json')
    data = json.load(open(rj))
    data['verification'] = v
    tex = {k: 'textures/%s_%s.png' % (export_name, k) for k in ('BaseColor', 'Roughness', 'Metalness')}
    data['textures'] = dict(tex, note='one atlas per weapon shared by ALL its MeshParts (every mesh keeps the atlas UVs): '
                            'SurfaceAppearance ColorMap / RoughnessMap / MetalnessMap. Without it, use the flat '
                            'per-material colours in `materials`.')
    data['previews'] = ['%s_34.png' % export_name, 'previews/%s_right.png' % export_name,
                        'previews/%s_left_rear34.png' % export_name]
    json.dump(data, open(rj, 'w'), indent=1)
    md = os.path.join(OUT, export_name + '_HANDOFF.md')
    txt = open(md).read()
    extra = ['', '## 15. Baked texture atlas (optional, recommended)',
             'All meshes of this weapon share ONE UV layout, so one `SurfaceAppearance` (cloned into every MeshPart) '
             'gives the worn, weathered look from the Blender renders (edge wear, scratches, grime, dark recesses, '
             'red markings):', '',
             '| Map | File | Colour space |', '|---|---|---|',
             '| ColorMap | `%s` | sRGB |' % tex['BaseColor'], '| RoughnessMap | `%s` | linear |' % tex['Roughness'],
             '| MetalnessMap | `%s` | linear |' % tex['Metalness'], '',
             'Upload the three PNGs (Asset Manager > Bulk Import), create a SurfaceAppearance with the three IDs, and '
             'parent a clone to each MeshPart. With a SurfaceAppearance the MeshPart `Color` is ignored; without it, '
             'use the flat colours of section 11.', '',
             '## 16. Previews',
             '![34](%s_34.png) ![right](previews/%s_right.png) ![rear](previews/%s_left_rear34.png)'
             % (export_name, export_name, export_name), '',
             'Pose previews (moving parts deployed): `previews/%s_pose_*.png`.' % export_name, '']
    open(md, 'w').write(txt + '\n'.join(extra))
    summary[code] = dict(fbx=export_name + '.fbx', meshes=rig['import']['mesh_count'], tris=rig['import']['triangles'],
                         max_mesh_tris=rig['import']['max_mesh_triangles'], size_studs=rig['import']['expected_size_studs'],
                         target_studs_LHW=list(dims), pivots_checked=v['pivots_checked'], passed=v['passed'],
                         problems=v['problems'])
    print('EXPORTED', code, summary[code], flush=True)
json.dump(summary, open(os.path.join(OUT, 'export_summary.json'), 'w'), indent=1)
print('ALL PASSED' if all(s['passed'] for s in summary.values()) else 'SOME FAILED')
