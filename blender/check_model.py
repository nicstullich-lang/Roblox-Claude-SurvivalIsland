"""Automated inspection of a rig-tagged model in every pose.

Usage: bpy-run blender/check_model.py MODEL [pose ...]        (MODEL = package, e.g. xr77; default: all poses)

Reports
  FLOATING     mesh objects that touch nothing (rest pose)
  CLASHES      new overlaps between different moving groups / the body in a pose (pairs already touching at rest
               are mounting contacts and ignored)
  GROUND       geometry below the ground in poses marked ground=True (tyres may touch)
  BUDGET       triangles (total, largest objects) and overall size
"""
import sys, os, json, time, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

pkg = sys.argv[1]
want = sys.argv[2:]
lib = importlib.import_module(pkg + '.lib')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, lib.MODEL + '.blend'))
from common import poses
from common.rig import get_json
sc = bpy.context.scene
for o in sc.objects:
    o.animation_data_clear()
poses.apply_state()

objs = [o for o in sc.objects if o.type == 'MESH' and not o.name.startswith('Studio')]
groups = {o.name for o in sc.objects if o.get('rig_motion')}


def group_of(o):
    p = o
    while p:
        if p.name in groups:
            return p.name
        p = p.parent
    return 'Body'


def ancestors(g):
    out = set()
    p = bpy.data.objects[g].parent if g != 'Body' else None
    while p:
        if p.name in groups:
            out.add(p.name)
        p = p.parent
    return out


G = {o.name: group_of(o) for o in objs}
ANC = {g: ancestors(g) for g in set(G.values())}
dg = bpy.context.evaluated_depsgraph_get()
LOCAL = {}
tot = 0
for o in objs:
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    LOCAL[o.name] = ([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces])
    tot += len(bm.faces)
    bm.free()
    ev.to_mesh_clear()


def world_data():
    bpy.context.view_layer.update()
    D = {}
    for o in objs:
        vs, fs = LOCAL[o.name]
        if not vs:
            continue
        mw = o.matrix_world
        W = [mw @ v for v in vs]
        mn = Vector((min(v.x for v in W), min(v.y for v in W), min(v.z for v in W)))
        mx = Vector((max(v.x for v in W), max(v.y for v in W), max(v.z for v in W)))
        D[o.name] = dict(bvh=BVHTree.FromPolygons(W, fs), mn=mn, mx=mx, verts=W)
    return D


def bb(a, b, m=0.0):
    return all(a['mn'][i] - m <= b['mx'][i] and b['mn'][i] - m <= a['mx'][i] for i in range(3))


def pairs(D, min_tris=4):
    names = sorted(D)
    out = {}
    for i, a in enumerate(names):
        A = D[a]
        for b in names[i + 1:]:
            if G[a] == G[b]:
                continue
            B = D[b]
            if not bb(A, B):
                continue
            n = len(A['bvh'].overlap(B['bvh']))
            if n >= min_tris:
                out[(a, b)] = n
    return out


t0 = time.time()
D0 = world_data()
names = sorted(D0)
# ---------------------------------------------------------------- floating (rest)
floating = []
for a in names:
    A = D0[a]
    ok = False
    sample = A['verts'][::max(1, len(A['verts']) // 250)]
    for b in names:
        if a == b or not bb(A, D0[b], 0.01):
            continue
        B = D0[b]
        if A['bvh'].overlap(B['bvh']):
            ok = True
            break
        if any(B['bvh'].find_nearest(v, 0.006)[0] is not None for v in sample):
            ok = True
            break
    if not ok:
        floating.append(a)
print('=== FLOATING (rest): %d' % len(floating))
for f in floating:
    print('   %-40s %s %s' % (f, tuple(round(c, 3) for c in D0[f]['mn']), tuple(round(c, 3) for c in D0[f]['mx'])))
base = pairs(D0, 1)
ps = get_json(sc, 'rig_poses', {})
todo = want or ['rest'] + [k for k in ps if k != 'rest']
summary = {}
for pn in todo:
    p = ps.get(pn, {'channels': {}, 'inputs': {}, 'ground': True})
    poses.apply_state(p.get('channels'), p.get('inputs'))
    D = world_data()
    new = {k: v for k, v in pairs(D, 4).items() if k not in base}
    rows = []
    for (a, b), n in sorted(new.items(), key=lambda kv: -kv[1]):
        ga, gb = G[a], G[b]
        rows.append((n, a, b, ga, gb))
    low = []
    if p.get('ground', True):
        for a in D:
            z = D[a]['mn'].z
            if z < 0.015 and not any(k in a for k in ('Wheel',)):
                low.append((a, round(z, 3)))
    summary[pn] = (len(rows), len(low))
    print('\n=== POSE %-10s clashes %d  below-ground %d' % (pn, len(rows), len(low)))
    for r in rows[:40]:
        print('   %5d  %-36s %-36s [%s | %s]' % r)
    for a, z in low[:20]:
        print('   LOW  %-36s z=%.3f' % (a, z))
poses.apply_state()
print('\n=== BUDGET: %d mesh objects, %d triangles (evaluated)' % (len(objs), tot))
for a in sorted(LOCAL, key=lambda n: -len(LOCAL[n][1]))[:8]:
    print('   %-36s %6d' % (a, len(LOCAL[a][1])))
mn = Vector((min(d['mn'].x for d in D0.values()), min(d['mn'].y for d in D0.values()), min(d['mn'].z for d in D0.values())))
mx = Vector((max(d['mx'].x for d in D0.values()), max(d['mx'].y for d in D0.values()), max(d['mx'].z for d in D0.values())))
print('=== BOUNDS (m) %s .. %s  size %s' % (tuple(round(c, 3) for c in mn), tuple(round(c, 3) for c in mx),
                                         tuple(round(c, 3) for c in (mx - mn))))
print('=== SUMMARY floating=%d %s  (%.0fs)' % (len(floating), ' '.join('%s:%d/%d' % (k, v[0], v[1]) for k, v in summary.items()),
                                              time.time() - t0))
