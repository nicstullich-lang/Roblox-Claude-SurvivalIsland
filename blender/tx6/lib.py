"""TX-6 "Bastion" armoured super-SUV - shared build library.

Blender 5.2 LTS. Units: metres. Axes: Z up, vehicle nose points to -Y.
Vehicle LEFT side = +X (suffix _L), vehicle RIGHT side = -X (suffix _R).
(Unlike the VX-9 file, side suffixes here are the vehicle's TRUE sides.)
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Euler, Quaternion
from mathutils.bvhtree import BVHTree
from math import sin, cos, tan, atan2, pi, radians, sqrt

V = Vector
P = 'TX6_'
ROOT_NAME = 'TX6_Root'

# ============================================================== key dimensions
Y_NOSE, Y_TAIL = -3.00, 3.00          # grille face / rear face
X_SIDE = 1.22                          # lower body side (half width)
Z_SILL = 0.62                          # hull bottom
Z_BELT = 1.62                          # beltline (tumblehome starts)
X_RE, Z_RE = 1.10, 2.38                # roof edge (top of side glass plane)
X_RT, Z_ROOF = 0.98, 2.48              # roof top flat
Y_COWL, Y_WST = -1.13, -0.78           # windshield base / top
TUMB = (X_SIDE - X_RE) / (Z_RE - Z_BELT)
T_SHELL = 0.06                         # armour shell thickness
Y_AF, Y_AR = -2.05, 1.90               # axles
R_WHEEL, W_TIRE, X_TRACK = 0.60, 0.44, 1.10
Z_WHEEL = R_WHEEL                      # wheel centre height (static, on ground)
ARCH = [(-0.80, 0.40), (-0.80, 0.95), (-0.46, 1.34), (0.46, 1.34), (0.80, 0.95), (0.80, 0.40)]


def xs(z):
    """x of the body side surface at height z (vertical below beltline, tumblehome above)."""
    return X_SIDE if z <= Z_BELT else X_SIDE - (z - Z_BELT) * TUMB


def zh(y):
    """hood top height (y between -2.90 and the cowl)."""
    return 1.60 + (y + 2.90) * (0.08 / (Y_COWL + 2.90))


def side_pt(y, z, s=1, off=0.0):
    """point on the body side surface (s=+1 left, -1 right), pushed `off` metres outward."""
    n = side_n(z, s)
    return V((s * xs(z), y, z)) + n * off


def side_n(z, s=1):
    if z <= Z_BELT:
        return V((s, 0, 0))
    a = math.atan(TUMB)
    return V((s * cos(a), 0, sin(a)))


def y_ws(z):
    """windshield surface y at height z."""
    return Y_COWL + (z - zh(Y_COWL)) * (Y_WST - Y_COWL) / (Z_ROOF - zh(Y_COWL))


# ============================================================== scene / collections
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    root_coll = bpy.data.collections.new('TX6_Bastion')
    sc.collection.children.link(root_coll)
    r = bpy.data.objects.new(ROOT_NAME, None)
    r.empty_display_type = 'PLAIN_AXES'
    r.empty_display_size = 0.5
    root_coll.objects.link(r)
    return r


def root():
    return bpy.data.objects[ROOT_NAME]


def C(name):
    """collection TX6_<name> under the vehicle collection."""
    full = P + name
    c = bpy.data.collections.get(full)
    if c is None:
        c = bpy.data.collections.new(full)
        bpy.data.collections['TX6_Bastion'].children.link(c)
    return c


def scratch():
    c = bpy.data.collections.get('TX6_Scratch')
    if c is None:
        c = bpy.data.collections.new('TX6_Scratch')
        bpy.context.scene.collection.children.link(c)
    return c


# ============================================================== materials
MATS = {
    # name: (base colour linear, roughness, metallic, extras)
    'Paint':      ((0.062, 0.068, 0.042), 0.66, 0.0, {'bump': 0.15}),
    'ArmorPaint': ((0.050, 0.056, 0.034), 0.70, 0.0, {'bump': 0.25}),
    'PaintDark':  ((0.030, 0.033, 0.022), 0.72, 0.0, {'bump': 0.15}),
    'Coating':    ((0.016, 0.016, 0.016), 0.88, 0.0, {'bump': 0.6}),   # bedliner / bumper coating
    'Hardware':   ((0.050, 0.050, 0.048), 0.48, 0.75, {}),
    'Steel':      ((0.300, 0.300, 0.290), 0.38, 1.00, {}),
    'Alu':        ((0.550, 0.560, 0.570), 0.32, 1.00, {}),
    'Gunmetal':   ((0.030, 0.032, 0.035), 0.36, 0.85, {}),
    'Rubber':     ((0.012, 0.012, 0.012), 0.82, 0.0, {}),
    'Tire':       ((0.016, 0.016, 0.016), 0.90, 0.0, {'bump': 0.4}),
    'Rim':        ((0.022, 0.023, 0.024), 0.55, 0.3, {}),
    'Glass':      ((0.70, 0.82, 0.78), 0.02, 0.0, {'glass': 1.0}),
    'GlassDark':  ((0.10, 0.12, 0.12), 0.05, 0.0, {'glass': 0.6}),
    'Lens':       ((0.95, 0.95, 0.95), 0.02, 0.0, {'glass': 1.0}),
    'LED':        ((0.90, 0.93, 1.00), 0.20, 0.0, {'emit': ((0.85, 0.90, 1.0), 6.0)}),
    'LEDOff':     ((0.60, 0.62, 0.65), 0.15, 0.6, {}),
    'Amber':      ((1.00, 0.35, 0.02), 0.20, 0.0, {'emit': ((1.0, 0.33, 0.02), 3.0)}),
    'RedLens':    ((0.70, 0.02, 0.01), 0.15, 0.0, {'emit': ((1.0, 0.02, 0.01), 2.0)}),
    'IRLens':     ((0.06, 0.005, 0.008), 0.10, 0.0, {}),
    'Mesh':       ((0.012, 0.012, 0.012), 0.60, 0.6, {}),
    'SafetyRed':  ((0.42, 0.012, 0.006), 0.50, 0.0, {}),
    'Hazard':     ((0.75, 0.48, 0.01), 0.55, 0.0, {}),
    'Canvas':     ((0.080, 0.075, 0.048), 0.90, 0.0, {'bump': 0.5}),
    'Wood':       ((0.20, 0.10, 0.045), 0.65, 0.0, {}),
    'Plastic':    ((0.020, 0.020, 0.022), 0.60, 0.0, {}),
    'Fabric':     ((0.028, 0.030, 0.024), 0.92, 0.0, {'bump': 0.3}),
    'Screen':     ((0.02, 0.05, 0.03), 0.20, 0.0, {'emit': ((0.15, 0.85, 0.35), 1.2)}),
    'ScreenBlue': ((0.02, 0.03, 0.06), 0.20, 0.0, {'emit': ((0.10, 0.45, 1.0), 1.2)}),
    'Missile':    ((0.55, 0.56, 0.54), 0.45, 0.0, {}),
    'Engine':     ((0.040, 0.040, 0.042), 0.50, 0.6, {}),
    'Copper':     ((0.60, 0.30, 0.12), 0.35, 1.0, {}),
    'Brass':      ((0.55, 0.40, 0.12), 0.30, 1.0, {}),
    'Exhaust':    ((0.20, 0.17, 0.15), 0.55, 0.9, {}),
    'Floor':      ((0.020, 0.020, 0.020), 0.90, 0.0, {}),
    'Rope':       ((0.045, 0.045, 0.048), 0.85, 0.0, {'bump': 0.8}),
    'Housing':    ((0.012, 0.012, 0.013), 0.45, 0.2, {}),
    'Stencil':    ((0.48, 0.48, 0.44), 0.85, 0.0, {}),
    'ExtRed':     ((0.50, 0.015, 0.010), 0.35, 0.0, {}),
}


def M(name):
    full = P + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    col, rough, metal, ex = MATS[name]
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
    if 'emit' in ex:
        ec, es = ex['emit']
        b.inputs['Emission Color'].default_value = (*ec, 1)
        b.inputs['Emission Strength'].default_value = es
    if ex.get('bump'):
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
    """move the object's pivot to world point p without moving its geometry (no children yet)."""
    w = wm(ob)
    local = w.inverted() @ V(p)
    ob.data.transform(Matrix.Translation(-local))
    ob.matrix_basis = ob.matrix_basis @ Matrix.Translation(local)


def anim(ob, note):
    ob['tx_anim'] = note


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
    c = bpy.data.collections.get('TX6_Scratch')
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


def mats_by_name():
    return {m.name[len(P):]: m for m in bpy.data.materials if m.name.startswith(P)}


# ============================================================== render helpers
def studio():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    w = bpy.data.worlds.new('TX6_World')
    sc.world = w
    nt = w.node_tree
    bg = nt.nodes['Background']
    bg.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1)
    bg.inputs['Strength'].default_value = 0.55
    sc_coll = bpy.data.collections.new('TX6_Studio')
    sc.collection.children.link(sc_coll)
    # ground
    me = bpy.data.meshes.new('Studio_Floor')
    me.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
    fl = bpy.data.objects.new('Studio_Floor', me)
    sc_coll.objects.link(fl)
    fm = bpy.data.materials.new('Studio_Ground')
    b = fm.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.20, 0.19, 0.17, 1)
    b.inputs['Roughness'].default_value = 0.85
    me.materials.append(fm)
    # lights
    def light(name, typ, loc, rot, energy, size=1.0, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, typ)
        ld.energy = energy
        ld.color = color
        if typ == 'AREA':
            ld.size = size
        if typ == 'SUN':
            ld.angle = radians(3)
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        lo.rotation_euler = Euler([radians(a) for a in rot])
        sc_coll.objects.link(lo)
    light('Sun', 'SUN', (0, 0, 10), (38, 0, 145), 3.2, color=(1.0, 0.95, 0.88))
    light('Key', 'AREA', (-7, -8, 7), (55, 0, -40), 2500, 6)
    light('Fill', 'AREA', (8, 5, 5), (60, 0, 125), 900, 6, (0.85, 0.9, 1.0))
    cam_d = bpy.data.cameras.new('Studio_Cam')
    cam = bpy.data.objects.new('Studio_Cam', cam_d)
    sc_coll.objects.link(cam)
    sc.camera = cam
    return cam


VIEWS = {
    'front34': ((-7.6, -9.0, 3.1), (0, -0.2, 1.25), 45),
    'rear34':  ((7.8, 9.5, 3.6), (0, 0.3, 1.25), 45),
    'side':    ((-14.0, 0.2, 1.5), (0, 0.2, 1.3), 50),
    'sideL':   ((14.0, 0.2, 1.5), (0, 0.2, 1.3), 50),
    'front':   ((0, -14.0, 1.6), (0, 0, 1.35), 55),
    'rear':    ((0, 14.5, 1.8), (0, 0, 1.35), 55),
    'top':     ((0, 0.2, 16.0), (0, 0.2, 0), 50),
    'low34':   ((-5.0, -6.2, 0.5), (0, -0.8, 1.0), 32),
    'high34':  ((-6.5, -6.0, 6.5), (0, 0.4, 1.6), 40),
    'roof':    ((-3.5, 4.5, 5.6), (0, 0.9, 2.5), 35),
    'wheel':   ((-3.2, -3.8, 0.8), (-1.1, -2.05, 0.6), 35),
    'under':   ((-6.0, -2.0, 0.12), (0, 0.0, 0.5), 30),
}


def setview(name=None, loc=None, target=None, lens=45):
    sc = bpy.context.scene
    cam = sc.camera
    if name:
        loc, target, lens = VIEWS[name]
    cam.location = V(loc)
    d = V(target) - V(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.clip_start = 0.05
    cam.data.clip_end = 200
