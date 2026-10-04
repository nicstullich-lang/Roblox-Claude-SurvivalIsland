"""Automated inspection of TX6_Bastion.blend.

Usage: bpy-run blender/checks.py [pose]      pose = rest (default) | combat | deploy | hood
Reports: floating objects, moving-part collisions (non-rest poses), low points, triangle budget.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

pose = sys.argv[1] if len(sys.argv) > 1 else 'rest'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'TX6_Bastion.blend'))
from tx6 import poses
poses.apply(pose)
dg = bpy.context.evaluated_depsgraph_get()

objs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.name.startswith('Studio')]
data = {}
tot = 0
for o in objs:
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    tris = len(bm.faces)
    tot += tris
    vs = [v.co.copy() for v in bm.verts]
    if not vs:
        print('EMPTY', o.name)
        continue
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    data[o.name] = dict(bvh=BVHTree.FromBMesh(bm), verts=vs, mn=mn, mx=mx, tris=tris)
    bm.free()
    ev.to_mesh_clear()


def bb_hit(a, b, m=0.01):
    return all(a['mn'][i] - m <= b['mx'][i] and b['mn'][i] - m <= a['mx'][i] for i in range(3))


def root_of(o):
    """moving group = nearest ancestor (or self) that is animated; 'STATIC' otherwise."""
    p = o
    while p and p.name != 'TX6_Root':
        if p.get('tx_deploy') or p.get('tx_anim'):
            return p.name
        p = p.parent
    return 'STATIC'


def is_desc(a, b):
    p = bpy.data.objects[a].parent
    while p:
        if p.name == b:
            return True
        p = p.parent
    return False


names = list(data)
# ---------------------------------------------------------------- floating
floating = []
for a in names:
    A = data[a]
    step = max(1, len(A['verts']) // 300)
    sample = A['verts'][::step]
    ok = False
    for b in names:
        if a == b or not bb_hit(A, data[b]):
            continue
        B = data[b]
        if A['bvh'].overlap(B['bvh']):
            ok = True
            break
        for v in sample:
            hit = B['bvh'].find_nearest(v, 0.006)
            if hit[0] is not None:
                ok = True
                break
        if ok:
            break
    if not ok:
        floating.append(a)
print('\n=== FLOATING (%s pose): %d' % (pose, len(floating)))
for f in floating:
    print('  ', f, tuple(round(c, 3) for c in data[f]['mn']), tuple(round(c, 3) for c in data[f]['mx']))

# ---------------------------------------------------------------- moving-part collisions
if pose != 'rest':
    print('\n=== COLLISIONS involving moving groups (%s pose), >8 tri pairs' % pose)
    groups = {}
    for o in objs:
        groups[o.name] = root_of(o)
    seen = set()
    rows = []
    for a in names:
        for b in names:
            if a >= b or groups[a] == groups[b]:
                continue
            ga, gb = groups[a], groups[b]
            if is_desc(ga, gb) or is_desc(gb, ga) if 'STATIC' not in (ga, gb) else False:
                continue
            A, B = data[a], data[b]
            if not bb_hit(A, B, 0.0):
                continue
            n = len(A['bvh'].overlap(B['bvh']))
            if n > 8:
                rows.append((n, a, b, groups[a], groups[b]))
    rows.sort(reverse=True)
    for r in rows[:60]:
        print('  %5d  %-32s %-32s [%s | %s]' % r)

# ---------------------------------------------------------------- low points + budget
print('\n=== LOWEST POINTS (below 0.42 m, excluding tyres/flaps/suspension)')
for a in names:
    z = data[a]['mn'].z
    if z < 0.42 and not any(k in a for k in ('Tire', 'MudFlap', 'Rim', 'Beadlock', 'Liner', 'Arms', 'Knuckle', 'Rotor',
                                              'LugNuts', 'CTIS', 'Spare')):
        print('  %-30s z=%.3f' % (a, z))
print('\n=== TRIANGLES (evaluated, bevels applied): total %d' % tot)
for a in sorted(names, key=lambda n: -data[n]['tris'])[:12]:
    print('  %-30s %6d' % (a, data[a]['tris']))
over = [a for a in names if data[a]['tris'] > 18000]
print('  objects over 18k tris:', over)
mn = Vector((min(d['mn'].x for d in data.values()), min(d['mn'].y for d in data.values()), min(d['mn'].z for d in data.values())))
mx = Vector((max(d['mx'].x for d in data.values()), max(d['mx'].y for d in data.values()), max(d['mx'].z for d in data.values())))
print('\n=== OVERALL BOUNDS (m)', tuple(round(c, 3) for c in mn), tuple(round(c, 3) for c in mx),
      ' size', tuple(round(c, 3) for c in (mx - mn)))
