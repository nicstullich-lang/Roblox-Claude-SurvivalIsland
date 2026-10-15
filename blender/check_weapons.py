"""Automated QA of the weapon pack (every weapon, every pose).

Usage: bpy-run blender/check_weapons.py [BLEND] [CODE ...]     (default: weapon_output/SurvivalWeaponPack.blend)

Per weapon it reports
  FLOATING   mesh parts that touch no other part of the weapon (gap > 1.5 mm) at rest
  CLASHES    new overlaps between different moving groups / the body in each rig pose (rest contacts are mounts)
  HOLES      open (boundary) or non-manifold edges per object, inverted solids (negative volume)
  HYGIENE    names (<CODE>_...), collection, materials on every slot, UV map, no live modifiers,
             identity rotation / unit scale on every part
  SIZE       bounding box in studs vs the requested size, triangle budget, largest merged (group, material) mesh
The pack-level verdict lists the relative-size rules from the brief (pistol smallest, SMG shorter than the carbine,
marksman rifle longest and slimmest, LMG broadest).
"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

args = [a for a in sys.argv[1:] if not a.endswith('.py')]
blend = next((a for a in args if a.endswith('.blend')), os.path.join(os.path.dirname(HERE), 'weapon_output',
                                                                      'SurvivalWeaponPack.blend'))
bpy.ops.wm.open_mainfile(filepath=blend)
from weapons import lib
from common import poses
from common.rig import get_json
codes = [c for c in args if c in lib.WEAPONS] or [c for c in lib.ORDER if bpy.data.collections.get(lib.WEAPONS[c][0])]
sc = bpy.context.scene
for o in sc.objects:
    o.animation_data_clear()
poses.apply_state()
GAP = 0.0015
S = lib.S
report = {}
t0 = time.time()


def mesh_data(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    V = [v.co.copy() for v in bm.verts]
    F = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    ev.to_mesh_clear()
    return V, F


def world(objs, LOCAL):
    bpy.context.view_layer.update()
    D = {}
    for o in objs:
        vs, fs = LOCAL[o.name]
        mw = o.matrix_world
        W = [mw @ v for v in vs]
        mn = Vector([min(v[i] for v in W) for i in range(3)])
        mx = Vector([max(v[i] for v in W) for i in range(3)])
        D[o.name] = dict(bvh=BVHTree.FromPolygons(W, fs), mn=mn, mx=mx, verts=W)
    return D


def bb(a, b, m=0.0):
    return all(a['mn'][i] - m <= b['mx'][i] and b['mn'][i] - m <= a['mx'][i] for i in range(3))


sizes = {}
for code in codes:
    coll = bpy.data.collections[lib.WEAPONS[code][0]]
    root = bpy.data.objects[code + '_Root']
    objs = [o for o in coll.all_objects if o.type == 'MESH']
    groups = {o.name for o in coll.all_objects if o.get('rig_motion')}

    def group_of(o):
        p = o
        while p:
            if p.name in groups:
                return p.name
            p = p.parent
        return 'Body'
    G = {o.name: group_of(o) for o in objs}
    LOCAL = {o.name: mesh_data(o) for o in objs}
    D0 = world(objs, LOCAL)
    names = sorted(D0)
    # ------------------------------------------------------------ floating parts
    floating = []
    for a in names:
        A = D0[a]
        ok = False
        sample = A['verts'][::max(1, len(A['verts']) // 300)]
        for b in names:
            if a == b or not bb(A, D0[b], GAP):
                continue
            B = D0[b]
            if A['bvh'].overlap(B['bvh']) or any(B['bvh'].find_nearest(v, GAP)[0] is not None for v in sample):
                ok = True
                break
        if not ok:
            floating.append(a)

    # ------------------------------------------------------------ clashes per pose
    def pairs(D, min_tris):
        out = {}
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if G[a] == G[b] or not bb(D[a], D[b]):
                    continue
                n = len(D[a]['bvh'].overlap(D[b]['bvh']))
                if n >= min_tris:
                    out[(a, b)] = n
        return out
    base = pairs(D0, 1)
    ps = get_json(root, 'rig_poses', {})
    clashes = {}
    for pn, p in ps.items():
        poses.apply_state(p.get('channels'), p.get('inputs'))
        D = world(objs, LOCAL)
        new = {k: v for k, v in pairs(D, 3).items() if k not in base}
        clashes[pn] = sorted(new.items(), key=lambda kv: -kv[1])
        poses.apply_state()
    # ------------------------------------------------------------ holes / inverted / hygiene
    holes, inverted, hyg = [], [], []
    for o in objs:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        nonman = sum(1 for e in bm.edges if not e.is_manifold)
        vol = bm.calc_volume(signed=True)
        bm.free()
        if nonman:
            holes.append((o.name, nonman))
        if vol < -1e-12:
            inverted.append(o.name)
        if not o.name.startswith(code + '_'):
            hyg.append('%s: name lacks the %s_ prefix' % (o.name, code))
        if o.users_collection[0] != coll:
            hyg.append('%s: not in collection %s' % (o.name, coll.name))
        if not o.data.materials or any(m is None for m in o.data.materials):
            hyg.append('%s: empty material slot' % o.name)
        if not o.data.uv_layers:
            hyg.append('%s: no UV map' % o.name)
        if o.modifiers:
            hyg.append('%s: %d live modifiers' % (o.name, len(o.modifiers)))
        r = o.rotation_quaternion if o.rotation_mode == 'QUATERNION' else o.rotation_euler.to_quaternion()
        if r.angle > 1e-5 or any(abs(s_ - 1) > 1e-6 for s_ in o.scale):
            hyg.append('%s: transform not applied (rot %.3g, scale %s)' % (o.name, r.angle, tuple(o.scale)))
    # ------------------------------------------------------------ size + budget
    mn = Vector([min(D0[n]['mn'][i] for n in names) for i in range(3)]) - root.location
    mx = Vector([max(D0[n]['mx'][i] for n in names) for i in range(3)]) - root.location
    sz = (mx - mn) * S
    L, H, W = sz.y, sz.z, sz.x
    tL, tH, tW = lib.WEAPONS[code][3]
    tris = sum(len(LOCAL[n][1]) for n in names)
    merged = {}
    for o in objs:
        for i, m in enumerate(o.data.materials):
            k = (G[o.name], m.name if m else None)
            merged[k] = merged.get(k, 0) + sum(len(p.vertices) - 2 for p in o.data.polygons if p.material_index == i)
    big = max(merged.items(), key=lambda kv: kv[1])
    sizes[code] = (L, H, W)
    ncl = sum(len(v) for v in clashes.values())
    report[code] = dict(objects=len(objs), groups=sorted(groups), floating=floating, clashes={k: [(a, b, n) for (a, b), n in v]
                                                                                             for k, v in clashes.items()},
                        holes=holes, inverted=inverted, hygiene=hyg, tris=tris, largest_merge=[list(big[0]), big[1]],
                        size_studs=[round(L, 3), round(H, 3), round(W, 3)], target_studs=[tL, tH, tW],
                        origin_check=[round(c, 4) for c in mn])
    print('\n=== %s (%s)  objects %d, groups %d, tris %d, largest merged mesh %s = %d' %
          (code, coll.name, len(objs), len(groups), tris, big[0], big[1]))
    print('    size  L %.2f  H %.2f  W %.2f studs   (target %.1f x %.2f x %.2f)' % (L, H, W, tL, tH, tW))
    print('    floating %d %s' % (len(floating), floating[:8]))
    for pn, v in clashes.items():
        print('    pose %-14s clashes %d %s' % (pn, len(v), [(a, b, n) for (a, b), n in v[:6]]))
    print('    holes %d %s' % (len(holes), holes[:8]))
    print('    inverted %d %s' % (len(inverted), inverted[:8]))
    print('    hygiene %d %s' % (len(hyg), hyg[:8]))

# ---------------------------------------------------------------- relative-size rules from the brief
rules = []
if all(c in sizes for c in lib.ORDER):
    Ls = {c: s[0] for c, s in sizes.items()}
    vol = {c: s[0] * s[1] * s[2] for c, s in sizes.items()}
    rules.append(('pistol is the smallest weapon', all(vol['SP9'] < vol[c] for c in lib.ORDER if c != 'SP9')))
    rules.append(('SMG is more compact than the carbine', Ls['MAKO9'] < Ls['R12'] and vol['MAKO9'] < vol['R12']))
    rules.append(('marksman rifle is the longest', all(Ls['TM308'] >= Ls[c] for c in lib.ORDER)))
    rules.append(('marksman rifle is the slimmest long gun (H/L)', all(sizes['TM308'][1] / Ls['TM308'] <= sizes[c][1] / Ls[c]
                                                                       for c in ('R12', 'BLMG'))))
    rules.append(('LMG is the broadest (width and height)', all(sizes['BLMG'][2] >= sizes[c][2] and
                                                                sizes['BLMG'][1] >= sizes[c][1] for c in lib.ORDER)))
    print('\n=== RELATIVE SIZE RULES')
    for t, ok in rules:
        print('    %-48s %s' % (t, 'PASS' if ok else 'FAIL'))
tot_fl = sum(len(r['floating']) for r in report.values())
tot_cl = sum(len(v) for r in report.values() for v in r['clashes'].values())
tot_h = sum(len(r['holes']) + len(r['inverted']) + len(r['hygiene']) for r in report.values())
print('\n=== SUMMARY floating=%d clashes=%d mesh/hygiene issues=%d rules=%s  (%.0fs)' %
      (tot_fl, tot_cl, tot_h, all(ok for _, ok in rules) if rules else 'n/a', time.time() - t0))
out = os.path.join(os.path.dirname(blend), 'qa_report.json') if 'weapon_output' in blend else None
if out:
    json.dump(dict(blend=os.path.basename(blend), weapons=report, rules=[[t, ok] for t, ok in rules]), open(out, 'w'),
              indent=1)
    print('wrote', out)
