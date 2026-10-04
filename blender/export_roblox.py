"""Export TX6_Bastion.blend to a Roblox-ready FBX (stud scale) + a rig JSON.

Usage: bpy-run blender/export_roblox.py
Writes: exports/TX6_Bastion_Roblox.fbx, exports/TX6_Bastion_Rig.json

- Merges meshes per (moving group, material) -> names RBX_<Group>_<Material>[_n]
- Bakes bevels, triangulates, scales 1 stud = 0.28 m, keeps each moving group's pivot
- Splits any mesh above 16k triangles (Roblox per-mesh limit is ~20k)
- Axes: Blender (x, y, z) -> Roblox (-x, z, y) / 0.28 ; vehicle nose -> Roblox -Z (LookVector)
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix

S = 1 / 0.28
OUT_DIR = os.path.join(os.path.dirname(HERE), 'exports')
os.makedirs(OUT_DIR, exist_ok=True)
FBX = os.path.join(OUT_DIR, 'TX6_Bastion_Roblox.fbx')
RIG = os.path.join(OUT_DIR, 'TX6_Bastion_Rig.json')

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'TX6_Bastion.blend'))
sc = bpy.context.scene
sc.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()


def group_of(o):
    p = o
    while p and p.name != 'TX6_Root':
        if p.get('tx_deploy') or p.get('tx_anim'):
            return p.name
        p = p.parent
    return 'Body'


def rbx(v):
    return [round(-v.x * S, 4), round(v.z * S, 4), round(v.y * S, 4)]


ex = bpy.data.collections.new('TX6_RobloxExport')
sc.collection.children.link(ex)
buckets = {}
for o in [o for o in sc.objects if o.type == 'MESH' and not o.name.startswith('Studio')]:
    if o.users_collection and o.users_collection[0].name == 'TX6_RobloxExport':
        continue
    g = group_of(o)
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.transform(Matrix.Scale(S, 4) @ o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    mats = [m.name.replace('TX6_', '') if m else 'None' for m in me.materials] or ['None']
    bm.verts.index_update()
    for f in bm.faces:
        mn = mats[f.material_index] if f.material_index < len(mats) else mats[0]
        b = buckets.setdefault((g, mn), {'V': [], 'F': [], 'map': {}})
        idx = []
        for v in f.verts:
            key = (o.name, v.index)
            if key not in b['map']:
                b['map'][key] = len(b['V'])
                b['V'].append(v.co.copy())
            idx.append(b['map'][key])
        b['F'].append(tuple(idx))
    bm.free()
    ev.to_mesh_clear()

made = []


def emit(name, V, F, mat, piv):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v - piv) for v in V], [], F)
    me.validate()
    me.materials.append(bpy.data.materials.get('TX6_' + mat))
    me.shade_smooth()
    me.set_sharp_from_angle(angle=0.70)
    ob = bpy.data.objects.new(name, me)
    ex.objects.link(ob)
    ob.location = piv
    made.append((name, len(F)))


for (g, mn), b in sorted(buckets.items()):
    piv = Vector((0, 0, 0)) if g == 'Body' else bpy.data.objects[g].matrix_world.translation * S
    name = 'RBX_%s_%s' % (g, mn)
    V, F = b['V'], b['F']
    if len(F) <= 16000:
        emit(name, V, F, mn, piv)
        continue
    Fs = sorted(F, key=lambda f: sum(V[i].y for i in f))
    chunks, cur = [], []
    for f in Fs:
        cur.append(f)
        if len(cur) >= 15000:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    for k, ch in enumerate(chunks):
        used = sorted({i for f in ch for i in f})
        rm = {i: j for j, i in enumerate(used)}
        emit('%s_%d' % (name, k + 1), [V[i] for i in used], [tuple(rm[i] for i in f) for f in ch], mn, piv)

bpy.context.view_layer.update()
for o in bpy.context.view_layer.objects:
    o.select_set(o.name in ex.objects)
bpy.context.view_layer.objects.active = ex.objects[0]
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
                         apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y', mesh_smooth_type='FACE',
                         use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False)

# ------------------------------------------------------------------ rig description (Roblox coordinates, studs)
rig = {'vehicle': 'TX-6 Bastion', 'scale': '1 stud = 0.28 m', 'axes': 'Roblox = (-x, z, y)/0.28 of Blender; nose = -Z',
       'groups': {}, 'seats': {}}
for o in sc.objects:
    if o.name.startswith('Studio') or o.name == 'TX6_Root':
        continue
    if o.get('tx_deploy') or o.get('tx_anim'):
        par = o.parent
        while par and not (par.get('tx_deploy') or par.get('tx_anim')) and par.name != 'TX6_Root':
            par = par.parent
        rig['groups'][o.name] = {'pivot_studs': rbx(o.matrix_world.translation),
                                 'parent_group': par.name if par and par.name != 'TX6_Root' else 'Body',
                                 'motion': o.get('tx_anim', ''), 'deploy_key': o.get('tx_deploy', ''),
                                 'meshes': [n for (n, t) in made if n.startswith('RBX_%s_' % o.name)]}
    if o.get('tx_seat'):
        rig['seats'][o.name] = {'position_studs': rbx(o.matrix_world.translation), 'role': o['tx_seat']}
with open(RIG, 'w') as f:
    json.dump(rig, f, indent=1)

tris = sum(t for _, t in made)
allv = [v for o in ex.objects for v in [o.matrix_world @ vv.co for vv in o.data.vertices]]
mn = Vector((min(v.x for v in allv), min(v.y for v in allv), min(v.z for v in allv)))
mx = Vector((max(v.x for v in allv), max(v.y for v in allv), max(v.z for v in allv)))
print('EXPORTED', FBX, 'meshes', len(made), 'tris', tris, 'max mesh tris', max(t for _, t in made))
print('size (Blender X x Y x Z, studs):', tuple(round(c, 2) for c in (mx - mn)))
print('size MB', round(os.path.getsize(FBX) / 1e6, 2), 'rig groups', len(rig['groups']), 'seats', len(rig['seats']))
