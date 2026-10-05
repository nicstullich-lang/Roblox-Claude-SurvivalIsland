"""Shared geometry + scene toolkit for Nic's Blender models (headless Blender 5.2, PyPI bpy).

Started as blender/tx6/lib.py (TX-6 build) and generalised so every model uses the same proven builders.
A model's own lib calls setup(prefix, model_collection, root_name, MATS) once before building.

Conventions (all models): metres, Z up, the model's FRONT points to -Y, the model's LEFT is +X (_L = +X, _R = -X).
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Euler, Quaternion
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt
from math import sin, cos, tan, atan2, asin, acos, pi, radians, degrees, sqrt

V = Vector
PROJ = {'prefix': 'M_', 'collection': 'Model', 'root': 'Model_Root', 'mats': {}}


def setup(prefix, collection, root_name, mats):
    PROJ.update(prefix=prefix, collection=collection, root=root_name, mats=mats)


# ============================================================== scene / collections
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    root_coll = bpy.data.collections.new(PROJ['collection'])
    sc.collection.children.link(root_coll)
    r = bpy.data.objects.new(PROJ['root'], None)
    r.empty_display_type = 'PLAIN_AXES'
    r.empty_display_size = 0.5
    root_coll.objects.link(r)
    return r


def root():
    return bpy.data.objects[PROJ['root']]


def C(name):
    """collection <prefix><name> under the model collection."""
    full = PROJ['prefix'] + name
    c = bpy.data.collections.get(full)
    if c is None:
        c = bpy.data.collections.new(full)
        bpy.data.collections[PROJ['collection']].children.link(c)
    return c


def scratch():
    nm = PROJ['prefix'] + 'Scratch'
    c = bpy.data.collections.get(nm)
    if c is None:
        c = bpy.data.collections.new(nm)
        bpy.context.scene.collection.children.link(c)
    return c


# ============================================================== materials
def M(name):
    """material <prefix><name> from PROJ['mats']: name -> (base colour linear, roughness, metallic, extras).
    extras: glass (transmission), emit ((r,g,b), strength), bump, vary (colour/roughness noise variation),
    weave (carbon checker), roblox (explicit Roblox spec dict for the handoff exporter)."""
    full = PROJ['prefix'] + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    col, rough, metal, ex = PROJ['mats'][name]
    m = bpy.data.materials.new(full)
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*col, 1)
    m.roughness = rough
    m.metallic = metal
    if 'glass' in ex:
        b.inputs['Transmission Weight'].default_value = ex['glass']
        b.inputs['IOR'].default_value = 1.52
        m.diffuse_color = (*col, 0.35)
    if 'coat' in ex:
        b.inputs['Coat Weight'].default_value = ex['coat']
    if 'emit' in ex:
        ec, es = ex['emit']
        b.inputs['Emission Color'].default_value = (*ec, 1)
        b.inputs['Emission Strength'].default_value = es
    tc = None
    if ex.get('vary') or ex.get('weave'):
        tc = nt.nodes.new('ShaderNodeTexCoord')
    if ex.get('vary'):
        # large-scale blotchy colour + roughness variation: weathering / repaired coating patches
        k = ex['vary']
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = 1.6
        nz.inputs['Detail'].default_value = 8.0
        nz.inputs['Roughness'].default_value = 0.62
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['From Min'].default_value = 0.3
        mr.inputs['From Max'].default_value = 0.7
        mr.inputs['To Min'].default_value = 1.0 - k
        mr.inputs['To Max'].default_value = 1.0 + k
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
        mul = nt.nodes.new('ShaderNodeMix')
        mul.data_type = 'RGBA'
        mul.blend_type = 'MULTIPLY'
        sock = lambda coll, ident: next(x for x in coll if x.identifier == ident)
        sock(mul.inputs, 'Factor_Float').default_value = 1.0
        sock(mul.inputs, 'A_Color').default_value = (*col, 1)
        cm = nt.nodes.new('ShaderNodeCombineColor')
        for i in range(3):
            nt.links.new(mr.outputs['Result'], cm.inputs[i])
        nt.links.new(cm.outputs['Color'], sock(mul.inputs, 'B_Color'))
        nt.links.new(sock(mul.outputs, 'Result_Color'), b.inputs['Base Color'])
        rr = nt.nodes.new('ShaderNodeMapRange')
        rr.inputs['To Min'].default_value = max(0.0, rough - 0.12)
        rr.inputs['To Max'].default_value = min(1.0, rough + 0.12)
        nz2 = nt.nodes.new('ShaderNodeTexNoise')
        nz2.inputs['Scale'].default_value = 6.0
        nz2.inputs['Detail'].default_value = 10.0
        nt.links.new(tc.outputs['Object'], nz2.inputs['Vector'])
        nt.links.new(nz2.outputs['Fac'], rr.inputs['Value'])
        nt.links.new(rr.outputs['Result'], b.inputs['Roughness'])
    if ex.get('weave'):
        ck = nt.nodes.new('ShaderNodeTexChecker')
        ck.inputs['Scale'].default_value = ex['weave']
        ck.inputs['Color1'].default_value = (*col, 1)
        ck.inputs['Color2'].default_value = tuple(c * 1.9 for c in col) + (1,)
        nt.links.new(tc.outputs['Object'], ck.inputs['Vector'])
        nt.links.new(ck.outputs['Color'], b.inputs['Base Color'])
    if ex.get('bump'):
        if tc is None:
            tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = 180.0
        nz.inputs['Detail'].default_value = 6.0
        bp = nt.nodes.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = ex['bump'] * 0.25
        bp.inputs['Distance'].default_value = 0.0015
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
        nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    if ex.get('roblox'):
        import json
        m['rig_roblox'] = json.dumps(ex['roblox'])
    return m


# ============================================================== raw (verts, faces) builders
def merge_vf(*parts):
    Vs, Fs = [], []
    for vv, ff in parts:
        o = len(Vs)
        Vs += [V(v) for v in vv]
        Fs += [tuple(i + o for i in f) for f in ff]
    return Vs, Fs


def xform_vf(vf, mat):
    vv, ff = vf
    return [mat @ V(v) for v in vv], list(ff)


def mirror_vf(vf, axis=0):
    vv, ff = vf
    out = []
    for v in vv:
        v = V(v)
        v[axis] = -v[axis]
        out.append(v)
    return out, [tuple(reversed(f)) for f in ff]


def newell(pts):
    n = V((0, 0, 0))
    for i in range(len(pts)):
        a, b = V(pts[i]), V(pts[(i + 1) % len(pts)])
        n.x += (a.y - b.y) * (a.z + b.z)
        n.y += (a.z - b.z) * (a.x + b.x)
        n.z += (a.x - b.x) * (a.y + b.y)
    return n.normalized() if n.length > 1e-12 else V((0, 0, 1))


def prism(outline, d):
    """closed prism: planar 3D outline extruded by vector d."""
    n = len(outline)
    A = [V(p) for p in outline]
    B = [a + V(d) for a in A]
    F = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    F += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return A + B, F


def ring_prism(outer, inner, d):
    """frame: outer loop and inner loop (same vertex count), extruded by d."""
    n = len(outer)
    A = [V(p) for p in outer]
    Ai = [V(p) for p in inner]
    B = [a + V(d) for a in A]
    Bi = [a + V(d) for a in Ai]
    Vs = A + Ai + B + Bi
    o, i_, ob, ib = 0, n, 2 * n, 3 * n
    F = []
    for k in range(n):
        k1 = (k + 1) % n
        F.append((o + k, o + k1, i_ + k1, i_ + k))          # cap A
        F.append((ob + k, ib + k, ib + k1, ob + k1))        # cap B
        F.append((o + k, ob + k, ob + k1, o + k1))          # outer wall
        F.append((i_ + k, i_ + k1, ib + k1, ib + k))        # inner wall
    return Vs, F


def loft(loops, cap_start=True, cap_end=True, closed=True):
    """skin a list of equally sized point loops."""
    n = len(loops[0])
    Vs = [V(p) for L in loops for p in L]
    F = []
    m = n if closed else n - 1
    for s in range(len(loops) - 1):
        a, b = s * n, (s + 1) * n
        for i in range(m):
            j = (i + 1) % n
            F.append((a + i, a + j, b + j, b + i))
    if cap_start:
        F.append(tuple(reversed(range(n))))
    if cap_end:
        F.append(tuple(range((len(loops) - 1) * n, len(loops) * n)))
    return Vs, F


def plane_map(origin, u, v, pts2d):
    o, u, v = V(origin), V(u), V(v)
    return [o + u * p[0] + v * p[1] for p in pts2d]


def rect2(w, h, cx=0.0, cy=0.0):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


def chamf2(w, h, c, cx=0.0, cy=0.0):
    x, y = w / 2, h / 2
    pts = [(-x + c, -y), (x - c, -y), (x, -y + c), (x, y - c), (x - c, y), (-x + c, y), (-x, y - c), (-x, -y + c)]
    return [(p[0] + cx, p[1] + cy) for p in pts]


def rrect2(w, h, r, seg=4, cx=0.0, cy=0.0):
    x, y = w / 2 - r, h / 2 - r
    pts = []
    for (ox, oy, a0) in ((x, -y, -90), (x, y, 0), (-x, y, 90), (-x, -y, 180)):
        for k in range(seg + 1):
            a = radians(a0 + 90 * k / seg)
            pts.append((cx + ox + r * cos(a), cy + oy + r * sin(a)))
    return pts


def circle2(r, n=24, cx=0.0, cy=0.0, a0=0.0):
    return [(cx + r * cos(a0 + 2 * pi * k / n), cy + r * sin(a0 + 2 * pi * k / n)) for k in range(n)]


def offset2(poly, d):
    """offset a simple polygon; d>0 grows (outward), d<0 shrinks. Handles CW/CCW."""
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1           # CCW -> outward normal is (dy, -dx)
    lines = []
    for i in range(n):
        a, b = V((*poly[i], 0)), V((*poly[(i + 1) % n], 0))
        t = (b - a)
        if t.length < 1e-12:
            t = V((1, 0, 0))
        t.normalize()
        nrm = V((t.y, -t.x, 0)) * sgn
        lines.append((a + nrm * d, t))
    out = []
    for i in range(n):
        p1, t1 = lines[i - 1]
        p2, t2 = lines[i]
        den = t1.x * t2.y - t1.y * t2.x
        if abs(den) < 1e-9:
            out.append((p2.x, p2.y))
            continue
        w = p2 - p1
        s = (w.x * t2.y - w.y * t2.x) / den
        q = p1 + t1 * s
        orig = V((*poly[i], 0))
        if (q - orig).length > 4 * abs(d) + 1e-9:          # miter blow-up at a near-reversing corner: clamp
            n1, n2 = V((t1.y, -t1.x, 0)) * sgn, V((t2.y, -t2.x, 0)) * sgn
            bis = n1 + n2
            bis = bis.normalized() if bis.length > 1e-9 else n2
            q = orig + bis * d
        out.append((q.x, q.y))
    return out


def box_vf(c, s):
    c, s = V(c), V(s)
    x, y, z = s / 2
    o = [c + V((-x, -y, -z)), c + V((x, -y, -z)), c + V((x, y, -z)), c + V((-x, y, -z))]
    return prism(o, (0, 0, 2 * z))


def box_between(p0, p1):
    p0, p1 = V(p0), V(p1)
    return box_vf((p0 + p1) / 2, V([abs(a - b) for a, b in zip(p0, p1)]))


def lathe_vf(profile, n=24, cap0=True, cap1=True, a0=0.0, sweep=2 * pi):
    """revolve (r, z) profile around Z. r==0 points collapse to the axis."""
    full = abs(sweep - 2 * pi) < 1e-6
    steps = n if full else n + 1
    Vs, F, idx = [], [], []
    for (r, z) in profile:
        if r < 1e-9:
            idx.append([len(Vs)] * steps)
            Vs.append(V((0, 0, z)))
        else:
            row = []
            for k in range(steps):
                a = a0 + sweep * k / n
                row.append(len(Vs))
                Vs.append(V((r * cos(a), r * sin(a), z)))
            idx.append(row)
    for j in range(len(profile) - 1):
        A, B = idx[j], idx[j + 1]
        for k in range(n):
            k1 = (k + 1) % steps
            q = [A[k], A[k1], B[k1], B[k]]
            u = []
            for i in q:
                if i not in u:
                    u.append(i)
            if len(u) >= 3:
                F.append(tuple(u))
    if full:
        if cap0 and profile[0][0] > 1e-9:
            F.append(tuple(reversed(idx[0])))
        if cap1 and profile[-1][0] > 1e-9:
            F.append(tuple(idx[-1]))
    return Vs, F


def orient(vf, center=(0, 0, 0), axis='Z', rot=0.0):
    """take geometry built around +Z and point it along axis ('X','Y','Z', '-X'.. or a vector)."""
    if isinstance(axis, str):
        sgn = -1 if axis.startswith('-') else 1
        a = axis[-1]
        vec = V({'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}[a]) * sgn
    else:
        vec = V(axis).normalized()
    q = V((0, 0, 1)).rotation_difference(vec)
    m = Matrix.Translation(V(center)) @ q.to_matrix().to_4x4() @ Matrix.Rotation(rot, 4, 'Z')
    return xform_vf(vf, m)


def cyl_vf(c, r, h, axis='Z', n=16, rot=0.0):
    vf = lathe_vf([(0, -h / 2), (r, -h / 2), (r, h / 2), (0, h / 2)], n)
    return orient(vf, c, axis, rot)


def cyl_between(p0, p1, r, n=12):
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    vf = lathe_vf([(0, 0), (r, 0), (r, d.length), (0, d.length)], n)
    return orient(vf, p0, d)


def frames(path, closed=False):
    """parallel-transport frames along a polyline."""
    P_ = [V(p) for p in path]
    T = []
    for i in range(len(P_)):
        if closed:
            t = P_[(i + 1) % len(P_)] - P_[i - 1]
        elif i == 0:
            t = P_[1] - P_[0]
        elif i == len(P_) - 1:
            t = P_[-1] - P_[-2]
        else:
            t = (P_[i + 1] - P_[i]).normalized() + (P_[i] - P_[i - 1]).normalized()
        T.append(t.normalized())
    up = V((0, 0, 1)) if abs(T[0].z) < 0.9 else V((1, 0, 0))
    N = [(up - T[0] * up.dot(T[0])).normalized()]
    for i in range(1, len(P_)):
        n = N[-1] - T[i] * N[-1].dot(T[i])
        N.append(n.normalized())
    return P_, T, N


def sweep_vf(path, shape2d, closed=False, caps=True, scale=None):
    """sweep a 2D cross-section (x,y in the normal plane) along a polyline."""
    P_, T, N = frames(path, closed)
    loops = []
    for i, (p, t, n) in enumerate(zip(P_, T, N)):
        b = t.cross(n)
        s = scale[i] if scale else 1.0
        loops.append([p + n * (q[0] * s) + b * (q[1] * s) for q in shape2d])
    if closed:
        vv, ff = loft(loops + [loops[0]], False, False)
        return vv, ff
    return loft(loops, caps, caps)


def tube_vf(path, r, n=8, closed=False, caps=True):
    return sweep_vf(path, circle2(r, n), closed, caps)


def helix(c0, r, h, turns, seg=12):
    pts = []
    tot = int(turns * seg)
    for k in range(tot + 1):
        a = 2 * pi * k / seg
        pts.append(V((r * cos(a), r * sin(a), h * k / tot)) + V(c0))
    return pts


def arc_pts(c, r, a0, a1, n, plane='YZ'):
    out = []
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        u, v = r * cos(a), r * sin(a)
        if plane == 'YZ':
            out.append(V((c[0], c[1] + u, c[2] + v)))
        elif plane == 'XY':
            out.append(V((c[0] + u, c[1] + v, c[2])))
        else:
            out.append(V((c[0] + u, c[1], c[2] + v)))
    return out


# ============================================================== objects
def wm(ob):
    """world matrix without a depsgraph update."""
    m = ob.matrix_basis.copy()
    p = ob.parent
    child = ob
    while p:
        m = p.matrix_basis @ child.matrix_parent_inverse @ m
        child, p = p, p.parent
    return m


def parent_keep(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = wm(parent).inverted()


def mk(name, vf, mat='Paint', col='Body', parent=None, smooth=True, sharp=30, bev=None, recalc=True,
       mat_idx=None):
    vv, ff = vf
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in vv], [], [tuple(f) for f in ff])
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    mats = mat if isinstance(mat, (list, tuple)) else [mat]
    for m in mats:
        me.materials.append(M(m))
    if mat_idx is not None:
        for p, i in zip(me.polygons, mat_idx):
            p.material_index = i
    ob = bpy.data.objects.new(name, me)
    C(col).objects.link(ob)
    if parent is None:
        parent = root()
    parent_keep(ob, parent)
    if smooth:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=radians(sharp))
    if bev:
        bevel(ob, *bev) if isinstance(bev, (tuple, list)) else bevel(ob, bev)
    return ob


def empty(name, loc, col='Body', parent=None, size=0.2):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = size
    C(col).objects.link(e)
    e.location = V(loc)
    parent_keep(e, parent or root())
    # parent_keep sets inverse of parent's world; keep world location == loc
    return e


def set_origin(ob, p):
    """move the object's pivot to world point p without moving its geometry or its children."""
    w = wm(ob)
    local = w.inverted() @ V(p)
    if ob.data is not None:
        ob.data.transform(Matrix.Translation(-local))
    ob.matrix_basis = ob.matrix_basis @ Matrix.Translation(local)
    for ch in ob.children:
        ch.matrix_parent_inverse = Matrix.Translation(-local) @ ch.matrix_parent_inverse


def anim(ob, note):
    ob['anim_note'] = note


def bevel(ob, w=0.008, seg=2, ang=30, harden=True):
    m = ob.modifiers.new('Bevel', 'BEVEL')
    m.width = w
    m.segments = seg
    m.limit_method = 'ANGLE'
    m.angle_limit = radians(ang)
    m.harden_normals = harden
    m.use_clamp_overlap = True
    return m


def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    me.name = ob.name
    if old.users == 0:
        bpy.data.meshes.remove(old)


def cutter(name, vf):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in vf[0]], [], [tuple(f) for f in vf[1]])
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scratch().objects.link(ob)
    ob.display_type = 'WIRE'
    return ob


def boolean(ob, cutters, op='DIFFERENCE', solver='EXACT'):
    if not cutters:
        return ob
    if len(cutters) == 1:
        m = ob.modifiers.new('B', 'BOOLEAN')
        m.operation = op
        m.solver = solver
        m.object = cutters[0]
    else:
        tc = bpy.data.collections.new('_bool_tmp')
        bpy.context.scene.collection.children.link(tc)
        for c in cutters:
            tc.objects.link(c)
        m = ob.modifiers.new('B', 'BOOLEAN')
        m.operation = op
        m.solver = solver
        m.operand_type = 'COLLECTION'
        m.collection = tc
    m.material_mode = 'INDEX'
    apply_mods(ob)
    if len(cutters) > 1:
        bpy.data.collections.remove(tc)
    return ob


def dup(ob, name, col=None):
    o2 = ob.copy()
    o2.data = ob.data.copy()
    o2.name = name
    o2.data.name = name
    (C(col) if col else ob.users_collection[0]).objects.link(o2)
    return o2


def clear_scratch():
    c = bpy.data.collections.get(PROJ['prefix'] + 'Scratch')
    if c:
        for o in list(c.objects):
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if me and me.users == 0:
                bpy.data.meshes.remove(me)
        bpy.data.collections.remove(c)


# ============================================================== small hardware
def _hex_head(r, h, n=6):
    prof = [(0, 0), (r, 0), (r, h * 0.7), (r * 0.78, h), (0, h)]
    return lathe_vf(prof, n, a0=pi / 6)


def bolt_vf(pos, nrm, r=0.011, h=0.009, n=6, washer=True):
    parts = []
    if washer:
        parts.append(lathe_vf([(0, 0), (r * 1.45, 0), (r * 1.45, h * 0.25), (0, h * 0.25)], 10))
        head = _hex_head(r, h, n)
        parts.append(xform_vf(head, Matrix.Translation((0, 0, h * 0.25))))
    else:
        parts.append(_hex_head(r, h, n))
    vf = merge_vf(*parts)
    return orient(vf, pos, nrm)


def rivet_vf(pos, nrm, r=0.007):
    vf = lathe_vf([(0, 0), (r, 0), (r * 0.85, r * 0.45), (r * 0.45, r * 0.7), (0, r * 0.75)], 8)
    return orient(vf, pos, nrm)


def pts_line(p0, p1, spacing, inset=0.0):
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    L = d.length
    if L < 2 * inset + 1e-6:
        return []
    k = max(1, int(round((L - 2 * inset) / spacing)))
    return [p0 + d * ((inset + (L - 2 * inset) * i / k) / L) for i in range(k + 1)]


def pts_poly(poly3, spacing, inset=0.03):
    """bolt points along a closed 3D polyline, pulled `inset` inward toward the centroid plane."""
    P_ = [V(p) for p in poly3]
    cen = sum(P_, V((0, 0, 0))) / len(P_)
    out = []
    for i in range(len(P_)):
        a, b = P_[i], P_[(i + 1) % len(P_)]
        for q in pts_line(a, b, spacing)[:-1]:
            out.append(q + (cen - q).normalized() * inset)
    return out


def bolts(name, pts, nrm, parent=None, col='Details', r=0.011, h=0.009, mat='Hardware', rivets=False, washer=False):
    parts = []
    for p in pts:
        n = nrm(p) if callable(nrm) else nrm
        parts.append(rivet_vf(p, n, r * 0.65) if rivets else bolt_vf(p, n, r, h, washer=washer))
    if not parts:
        return None
    return mk(name, merge_vf(*parts), mat, col, parent, smooth=True, sharp=35)


def text_vf(body, size, extrude=0.002):
    c = bpy.data.curves.new('_txt', 'FONT')
    c.body = body
    c.size = size
    c.extrude = extrude
    c.align_x = 'CENTER'
    c.align_y = 'CENTER'
    o = bpy.data.objects.new('_txt', c)
    bpy.context.scene.collection.objects.link(o)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    vv = [v.co.copy() for v in me.vertices]
    ff = [tuple(p.vertices) for p in me.polygons]
    bpy.data.objects.remove(o)
    bpy.data.curves.remove(c)
    bpy.data.meshes.remove(me)
    return vv, ff




# ============================================================== curves
from bisect import bisect


class Spline:
    """Piecewise cubic Hermite through knots [(x, y), (x, y, slope), ...].
    Missing slopes are chosen monotone (Fritsch-Butland), so profiles never overshoot."""

    def __init__(self, knots):
        ks = sorted(knots, key=lambda k: k[0])
        self.x = [float(k[0]) for k in ks]
        self.y = [float(k[1]) for k in ks]
        n = len(ks)
        d = [(self.y[i + 1] - self.y[i]) / (self.x[i + 1] - self.x[i]) for i in range(n - 1)]
        m = []
        for i in range(n):
            s = ks[i][2] if len(ks[i]) > 2 else None
            if s is None:
                if i == 0:
                    s = d[0]
                elif i == n - 1:
                    s = d[-1]
                elif d[i - 1] * d[i] <= 0:
                    s = 0.0
                else:
                    h0, h1 = self.x[i] - self.x[i - 1], self.x[i + 1] - self.x[i]
                    w1, w2 = 2 * h1 + h0, h1 + 2 * h0
                    s = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
            m.append(float(s))
        self.m = m

    def __call__(self, t):
        x = self.x
        if t <= x[0]:
            return self.y[0] + self.m[0] * (t - x[0])
        if t >= x[-1]:
            return self.y[-1] + self.m[-1] * (t - x[-1])
        i = bisect(x, t) - 1
        h = x[i + 1] - x[i]
        s = (t - x[i]) / h
        h00 = 2 * s ** 3 - 3 * s ** 2 + 1
        h10 = s ** 3 - 2 * s ** 2 + s
        h01 = -2 * s ** 3 + 3 * s ** 2
        h11 = s ** 3 - s ** 2
        return h00 * self.y[i] + h10 * h * self.m[i] + h01 * self.y[i + 1] + h11 * h * self.m[i + 1]


def cosspace(a, b, n, ends=(True, True)):
    """n+1 values from a to b clustered at the ends that are True (cosine spacing)."""
    out = []
    for k in range(n + 1):
        s = k / n
        if ends[0] and ends[1]:
            f = 0.5 * (1 - cos(pi * s))
        elif ends[0]:
            f = 1 - cos(0.5 * pi * s)
        elif ends[1]:
            f = sin(0.5 * pi * s)
        else:
            f = s
        out.append(a + (b - a) * f)
    return out


def smooth01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ============================================================== 2D polygons
def area2(poly):
    n = len(poly)
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))


def ccw(poly):
    return list(poly) if area2(poly) > 0 else list(reversed(poly))


def pip(p, poly):
    x, y = p[0], p[1]
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i][0], poly[i][1]
        xj, yj = poly[j][0], poly[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi:
            inside = not inside
        j = i
    return inside


def seg_dist(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-18 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    qx, qy = ax + dx * t - p[0], ay + dy * t - p[1]
    return sqrt(qx * qx + qy * qy)


def poly_dist(p, poly):
    return min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def resample(poly, spacing, closed=True):
    """keep every corner, add points so no edge is longer than spacing."""
    out = []
    n = len(poly)
    m = n if closed else n - 1
    for i in range(m):
        a, b = V((poly[i][0], poly[i][1])), V((poly[(i + 1) % n][0], poly[(i + 1) % n][1]))
        k = max(1, int(math.ceil((b - a).length / spacing)))
        for j in range(k):
            out.append(a.lerp(b, j / k))
    if not closed:
        out.append(V((poly[-1][0], poly[-1][1])))
    return out


def saw_edge(p0, p1, teeth, depth, side=1):
    """points from p0 to p1 (p1 excluded) with `teeth` triangular serrations of `depth` (stealth door edges).
    side=+1 puts the teeth to the left of the travel direction."""
    a, b = V((p0[0], p0[1])), V((p1[0], p1[1]))
    d = b - a
    nrm = V((-d.y, d.x)).normalized() * side
    out = []
    for k in range(teeth):
        out.append(a + d * (k / teeth))
        out.append(a + d * ((k + 0.5) / teeth) + nrm * depth)
    return [(q.x, q.y) for q in out]


def ellipse2(rx, ry, n=24, cx=0.0, cy=0.0, a0=0.0):
    return [(cx + rx * cos(a0 + 2 * pi * k / n), cy + ry * sin(a0 + 2 * pi * k / n)) for k in range(n)]


def fill2d(outer, holes=(), spacing=0.06, edge_spacing=None):
    """triangulate a 2D region (outer polygon minus holes) with an even interior grid -> (pts, tris)."""
    es = edge_spacing or spacing * 0.7
    outer = ccw(outer)
    holes = [list(reversed(ccw(h))) for h in holes]
    loops = [resample(outer, es)] + [resample(h, es) for h in holes]
    pts, edges = [], []
    for L in loops:
        o = len(pts)
        pts += L
        edges += [(o + i, o + (i + 1) % len(L)) for i in range(len(L))]
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    row = 0
    y = y0 + spacing * 0.5
    while y < y1:
        x = x0 + spacing * (0.5 if row % 2 == 0 else 1.0)
        while x < x1:
            q = (x, y)
            if pip(q, outer) and not any(pip(q, h) for h in holes):
                if min(poly_dist(q, L) for L in [outer] + holes) > spacing * 0.42:
                    pts.append(V(q))
            x += spacing
        y += spacing * 0.866
        row += 1
    res = delaunay_2d_cdt(pts, edges, [], 0, 1e-7, False)
    vout, fout = res[0], res[2]
    keep = []
    for f in fout:
        c = sum((vout[i] for i in f), V((0, 0))) / len(f)
        if pip(c, outer) and not any(pip(c, h) for h in holes):
            keep.append(tuple(f))
    used = sorted({i for f in keep for i in f})
    remap = {i: j for j, i in enumerate(used)}
    return [V((vout[i][0], vout[i][1])) for i in used], [tuple(remap[i] for i in f) for f in keep]


# ============================================================== projecting onto a surface
PROJS = {  # 2D coords (axis a, axis b), ray axis c, side s: rays start at c = s*far and travel toward -s
    'top': (0, 1, 2, 1), 'bottom': (0, 1, 2, -1), 'left': (1, 2, 0, 1), 'right': (1, 2, 0, -1),
    'front': (0, 2, 1, -1), 'rear': (0, 2, 1, 1),
}


def ray_for(p2, proj, far=40.0):
    a, b, c, s = PROJS[proj]
    o = [0.0, 0.0, 0.0]
    o[a], o[b], o[c] = p2[0], p2[1], s * far
    d = [0.0, 0.0, 0.0]
    d[c] = -s
    return V(o), V(d)


def to3(p2, proj, w):
    a, b, c, s = PROJS[proj]
    o = [0.0, 0.0, 0.0]
    o[a], o[b], o[c] = p2[0], p2[1], w
    return V(o)


class Caster:
    """ray-cast helper on one or more evaluated mesh objects (world space)."""

    def __init__(self, obs):
        dg = bpy.context.evaluated_depsgraph_get()
        Vs, Ps = [], []
        for ob in obs:
            ev = ob.evaluated_get(dg)
            me = ev.to_mesh()
            mw = ob.matrix_world
            o = len(Vs)
            Vs += [mw @ v.co for v in me.vertices]
            Ps += [[o + i for i in p.vertices] for p in me.polygons]
            ev.to_mesh_clear()
        self.bvh = BVHTree.FromPolygons(Vs, Ps)

    def hit(self, origin, direction, maxd=200.0):
        loc, nrm, idx, d = self.bvh.ray_cast(V(origin), V(direction), maxd)
        if loc is None:
            return None
        if nrm.dot(V(direction)) > 0:
            nrm = -nrm
        return loc, nrm

    def on(self, p2, proj):
        o, d = ray_for(p2, proj)
        h = self.hit(o, d)
        if h is None:
            raise ValueError('ray missed the surface at %s (%s)' % (tuple(round(c, 3) for c in p2), proj))
        return h


def _vertex_normals(P, tris, hint):
    N = [V((0, 0, 0)) for _ in P]
    for f in tris:
        a, b, c = P[f[0]], P[f[1]], P[f[2]]
        n = (b - a).cross(c - a)
        for i in f:
            N[i] += n
    out = []
    for n, h in zip(N, hint):
        if n.length < 1e-12:
            n = h.copy()
        n.normalize()
        if n.dot(h) < 0:
            n = -n
        out.append(n)
    return out


def skin_patch(caster, outer, proj, t=0.02, holes=(), spacing=0.06, lift=0.0, inset=0.0, edge_spacing=None):
    """A solid panel that follows the surface under a 2D outline (door, hatch, glass, decal).
    The outer face sits `lift` above the surface, the inner face `t` below it. inset shrinks the outline
    (use the half seam gap for doors). Returns (verts, faces) - a closed solid."""
    if inset:
        outer = offset2(ccw(outer), -inset)
        holes = [offset2(ccw(h), inset) for h in holes]
    pts, tris = fill2d(outer, holes, spacing, edge_spacing)
    P, H = [], []
    for p in pts:
        loc, n = caster.on(p, proj)
        P.append(loc)
        H.append(n)
    N = _vertex_normals(P, tris, H)
    n = len(P)
    top = [P[i] + N[i] * lift for i in range(n)]
    bot = [P[i] - N[i] * t for i in range(n)]
    F = [tuple(f) for f in tris] + [tuple(n + i for i in reversed(f)) for f in tris]
    cnt = {}
    for f in tris:
        for k in range(3):
            e = (f[k], f[(k + 1) % 3])
            cnt[tuple(sorted(e))] = cnt.get(tuple(sorted(e)), 0) + 1
            cnt.setdefault(('dir',) + e, 1)
    nt = len(F)
    for f in tris:
        for k in range(3):
            i, j = f[k], f[(k + 1) % 3]
            if cnt[tuple(sorted((i, j)))] == 1:
                F.append((j, i, n + i, n + j))
    # material index per face: 0 = outer skin, 1 = inner face, 2 = edges
    mi = [0] * len(tris) + [1] * len(tris) + [2] * (len(F) - nt)
    skin_patch.last_mi = mi
    return top + bot, F


def surface_points(caster, poly2d, proj, spacing, inset=0.0, closed=True):
    """(point, normal) pairs along a 2D polyline projected on the surface (fastener rows, light strips...)."""
    poly = offset2(ccw(poly2d), -inset) if (inset and closed) else poly2d
    out = []
    for p in resample(poly, spacing, closed):
        try:
            out.append(caster.on(p, proj))
        except ValueError:
            pass
    return out


def fasteners_vf(pn, r=0.0055, h=0.0012, n=8):
    """flush countersunk fastener heads (tiny discs standing h proud of the skin)."""
    parts = []
    for p, nrm in pn:
        parts.append(orient(lathe_vf([(0, -0.002), (r, -0.002), (r, h), (0, h)], n), p, nrm))
    return merge_vf(*parts) if parts else ([], [])


def groove_vf(caster, path2d, proj, width=0.005, depth=0.004, step=0.05, closed=False):
    """cutter for a recessed panel line that follows the surface along a 2D path."""
    pts = resample(path2d, step, closed)
    hits = [caster.on(p, proj) for p in pts]
    P_ = [h[0] for h in hits]
    N_ = [h[1] for h in hits]
    loops = []
    m = len(P_)
    for i in range(m):
        if closed:
            tng = P_[(i + 1) % m] - P_[i - 1]
        else:
            tng = P_[min(i + 1, m - 1)] - P_[max(i - 1, 0)]
        tng.normalize()
        b = N_[i].cross(tng).normalized()
        p, nr = P_[i], N_[i]
        loops.append([p + b * (width / 2) + nr * 0.01, p - b * (width / 2) + nr * 0.01,
                      p - b * (width / 2) - nr * depth, p + b * (width / 2) - nr * depth])
    if closed:
        return loft(loops + [loops[0]], False, False)
    # extend the open ends slightly past the path so the groove reaches panel edges
    return loft(loops, True, True)


def stamp_vf(caster, text, center2d, proj, size, up2d=(0, 1), lift=0.0025, t=0.0015, rot=0.0, mirror=False):
    """raised low-visibility stencil text projected on the surface (mirror=True for surfaces seen from the
    other side of the projection plane, e.g. the model's right side)."""
    vv, ff = text_vf(text, size, 0.0)
    if mirror:
        vv = [V((-v.x, v.y, v.z)) for v in vv]
        ff = [tuple(reversed(f)) for f in ff]
    a = atan2(up2d[1], up2d[0]) - pi / 2 + rot
    out = []
    for v in vv:
        x = v.x * cos(a) - v.y * sin(a) + center2d[0]
        y = v.x * sin(a) + v.y * cos(a) + center2d[1]
        loc, n = caster.on((x, y), proj)
        out.append((loc, n))
    top = [p + n * lift for p, n in out]
    bot = [p + n * (lift - t) for p, n in out]
    k = len(top)
    F = [tuple(f) for f in ff] + [tuple(k + i for i in reversed(f)) for f in ff]
    return top + bot, F


# ============================================================== aerofoils
def _foil_raw(s, le):
    return (1 - le) * 4 * s * (1 - s) + le * 2.6 * sqrt(s) * (1 - s) ** 1.5


_FOIL_NORM = {}


def foil_t(s, tc, le=0.25):
    """total thickness (fraction of chord) at chord station s (0 = LE, 1 = TE) of a thin supersonic section:
    a biconvex arc blended with a little round-nose thickness (le) so the leading edge is not a razor."""
    if le not in _FOIL_NORM:
        _FOIL_NORM[le] = max(_foil_raw(k / 400, le) for k in range(401))
    s = max(0.0, min(1.0, s))
    return tc * _foil_raw(s, le) / _FOIL_NORM[le]


# ============================================================== rotations
def axis_v(axis):
    if isinstance(axis, str):
        return V({'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}[axis[-1]]) * (-1 if axis.startswith('-') else 1)
    return V(axis).normalized()


def qaxis(axis, deg):
    return Quaternion(axis_v(axis), radians(deg))


def rot_about(vf, pivot, axis, deg):
    m = Matrix.Translation(V(pivot)) @ qaxis(axis, deg).to_matrix().to_4x4() @ Matrix.Translation(-V(pivot))
    return xform_vf(vf, m)


# ============================================================== studio / camera
def studio(size=6.0, floor_color=(0.20, 0.19, 0.17)):
    """Cycles studio: sky world, ground plane, sun + two area lights scaled to a model of length `size` (m)."""
    sc = bpy.context.scene
    k = size / 6.0
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    w = bpy.data.worlds.new(PROJ['prefix'] + 'World')
    sc.world = w
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1)
    bg.inputs['Strength'].default_value = 0.55
    sc_coll = bpy.data.collections.new(PROJ['prefix'] + 'Studio')
    sc.collection.children.link(sc_coll)
    me = bpy.data.meshes.new('Studio_Floor')
    s = 60 * k
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    fl = bpy.data.objects.new('Studio_Floor', me)
    sc_coll.objects.link(fl)
    fm = bpy.data.materials.new('Studio_Ground')
    b = fm.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*floor_color, 1)
    b.inputs['Roughness'].default_value = 0.85
    me.materials.append(fm)

    def light(name, typ, loc, rot, energy, sz=1.0, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, typ)
        ld.energy = energy
        ld.color = color
        if typ == 'AREA':
            ld.size = sz
        if typ == 'SUN':
            ld.angle = radians(3)
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        lo.rotation_euler = Euler([radians(a) for a in rot])
        sc_coll.objects.link(lo)
    light('Studio_Sun', 'SUN', (0, 0, 10), (38, 0, 145), 3.2, color=(1.0, 0.95, 0.88))
    light('Studio_Key', 'AREA', (-7 * k, -8 * k, 7 * k), (55, 0, -40), 2500 * k * k, 6 * k)
    light('Studio_Fill', 'AREA', (8 * k, 5 * k, 5 * k), (60, 0, 125), 900 * k * k, 6 * k, (0.85, 0.9, 1.0))
    light('Studio_Under', 'AREA', (0, 0, 0.30), (180, 0, 0), 260 * k * k, 4.5 * k, (0.95, 0.95, 1.0))
    cam_d = bpy.data.cameras.new('Studio_Cam')
    cam = bpy.data.objects.new('Studio_Cam', cam_d)
    sc_coll.objects.link(cam)
    sc.camera = cam
    return cam


def look(loc, target, lens=45):
    cam = bpy.context.scene.camera
    cam.location = V(loc)
    cam.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.clip_start = 0.05
    cam.data.clip_end = 500
