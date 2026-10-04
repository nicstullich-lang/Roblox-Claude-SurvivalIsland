"""TX-6 Bastion - armoured monocoque shell, opening panels, armoured glass, wheel-well liners."""
import bmesh
from tx6.lib import *

GAP = 0.0035   # half of the 7 mm armoured panel gap


def hood_half(y):
    z = zh(y)
    return [(0, Z_SILL), (1.10, Z_SILL), (X_SIDE, 0.70), (X_SIDE, z - 0.06), (X_SIDE - 0.06 * TUMB, z), (1.00, z), (0, z)]


def cabin_half():
    return [(0, Z_SILL), (1.10, Z_SILL), (X_SIDE, 0.70), (X_SIDE, Z_BELT), (X_RE, Z_RE), (X_RT, Z_ROOF), (0, Z_ROOF)]


FRONT_HALF = [(0, 0.72), (1.00, 0.72), (1.12, 0.78), (1.12, 1.40), (1.11, 1.46), (0.92, 1.46), (0, 1.46)]
REAR_HALF = [(0, 0.70), (1.02, 0.70), (1.14, 0.76), (1.14, 1.62), (1.03, 2.31), (0.92, 2.40), (0, 2.40)]


def full(h):
    return list(h) + [(-x, z) for (x, z) in reversed(h[1:-1])]


def loop_at(sec, y):
    return [(x, y, z) for (x, z) in sec]


def oriented(vf, inward=False):
    me = bpy.data.meshes.new('_tmp')
    me.from_pydata([tuple(v) for v in vf[0]], [], [tuple(f) for f in vf[1]])
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if inward:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.verts.index_update()
    vv = [v.co.copy() for v in bm.verts]
    ff = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    bpy.data.meshes.remove(me)
    return vv, ff


# ------------------------------------------------------------------ outlines (side view y,z)
FD_OUT = [(-1.06, 0.72), (-1.06, 1.62), (-0.705, 2.33), (-0.10, 2.33), (-0.10, 0.72)]
RD_OUT = [(-0.02, 0.72), (-0.02, 2.33), (0.96, 2.33), (0.96, 0.72)]
LK_OUT = [(1.12, 1.70), (2.48, 1.70), (2.48, 2.30), (1.12, 2.30)]
FU_OUT = [(2.57, 1.84), (2.79, 1.84), (2.79, 2.08), (2.57, 2.08)]
FW_WIN = [(-0.91, 1.74), (-0.66, 2.24), (-0.20, 2.24), (-0.20, 1.74)]
RW_WIN = [(0.08, 1.74), (0.08, 2.24), (0.80, 2.24), (0.80, 1.74)]
REAR_DOOR = [(-0.30, 0.82), (0.82, 0.82), (0.82, 2.06), (-0.30, 2.06)]       # x,z on the rear face
REAR_WIN = [(0.00, 1.62), (0.60, 1.62), (0.60, 1.96), (0.00, 1.96)]
HOOD_OUT = [(-1.00, -2.86), (1.00, -2.86), (1.00, -1.20), (-1.00, -1.20)]      # x,y
MB_OUT = [(0.38, 1.25), (0.96, 1.25), (0.96, 2.55), (0.38, 2.55)]              # missile bay (left), x,y
TURRET_C, TURRET_R = (0.0, 0.30), 0.60


def side_cut(outline, s, x0=0.86, x1=1.75):
    pts = [(s * x0, y, z) for (y, z) in outline]
    return prism(pts, (s * (x1 - x0), 0, 0))


def rear_cut(outline, y0=2.80, y1=3.30):
    return prism([(x, y0, z) for (x, z) in outline], (0, y1 - y0, 0))


def top_cut(outline, z0=2.20, z1=2.80):
    return prism([(x, y, z0) for (x, y) in outline], (0, 0, z1 - z0))


def ws_normal():
    a = V((0, Y_COWL, zh(Y_COWL)))
    b = V((0, Y_WST, Z_ROOF))
    t = (b - a).normalized()
    return V((0, -t.z, t.y)).normalized()


def ws_pane(x0, x1, z0, z1, off=0.0):
    n = ws_normal()
    return [V((x, y_ws(z), z)) + n * off for (x, z) in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]


WS_PANES = [(0.06, 0.86, 1.80, 2.36), (-0.86, -0.06, 1.80, 2.36)]


def build():
    # ------------------------------------------------------------ outer + inner skins
    outer_st = [(Y_NOSE, FRONT_HALF), (-2.90, hood_half(-2.90)), (Y_COWL, hood_half(Y_COWL)),
                (Y_WST, cabin_half()), (2.88, cabin_half()), (Y_TAIL, REAR_HALF)]
    outer = loft([loop_at(full(h), y) for (y, h) in outer_st])
    inner_st = [(-2.80, hood_half(-2.80)), (Y_COWL, hood_half(Y_COWL)), (Y_WST, cabin_half()), (2.90, cabin_half())]
    inner = loft([loop_at(offset2(full(h), -T_SHELL), y) for (y, h) in inner_st])
    hull = mk('Body_Shell', merge_vf(oriented(outer), oriented(inner, True)), 'Paint', 'Body', recalc=False)

    # ------------------------------------------------------------ openings that go straight through / recesses
    cuts = []
    for s in (1, -1):
        for ya, xin in ((Y_AF, 0.48), (Y_AR, 0.50)):
            cuts.append(cutter('well', side_cut([(ya + dy, z) for (dy, z) in ARCH], s, xin, 1.80)))
        cuts.append(cutter('fwin', side_cut(FW_WIN, s)))
        cuts.append(cutter('rwin', side_cut(RW_WIN, s)))
        # headlight recesses + grille
        hx = [(s * 0.70, 1.16), (s * 1.06, 1.16), (s * 1.06, 1.40), (s * 0.70, 1.40)]
        cuts.append(cutter('head', prism([(x, -3.20, z) for (x, z) in hx], (0, 0.28, 0))))
        # rear upper corner light recesses
        tx = [(s * 0.86, 2.08), (s * 1.06, 2.08), (s * 1.06, 2.28), (s * 0.86, 2.28)]
        cuts.append(cutter('tail', prism([(x, 2.92, z) for (x, z) in tx], (0, 0.30, 0))))
    grille = [(-0.62, 0.92), (0.62, 0.92), (0.62, 1.38), (-0.62, 1.38)]
    cuts.append(cutter('grille', prism([(x, -3.20, z) for (x, z) in grille], (0, 0.52, 0))))
    for (x0, x1, z0, z1) in WS_PANES:
        pane = ws_pane(x0, x1, z0, z1, -0.20)
        cuts.append(cutter('ws', prism(pane, ws_normal() * 0.40)))
    cuts.append(cutter('rwin', rear_cut(REAR_WIN, 2.80, 3.30)))
    ring = [(TURRET_C[0] + TURRET_R * cos(a), TURRET_C[1] + TURRET_R * sin(a)) for a in [2 * pi * k / 64 for k in range(64)]]
    cuts.append(cutter('turret', top_cut(ring)))
    boolean(hull, cuts)

    # ------------------------------------------------------------ opening panels (cut out of the same shell)
    panels = []   # (name, shrunk cutter vf, grown cutter vf, pivot, anim note, collection)
    for s, sfx in ((1, 'L'), (-1, 'R')):
        hx = 1.27 * s
        panels.append(('Door_F' + sfx, side_cut(offset2(FD_OUT, -GAP), s), side_cut(offset2(FD_OUT, GAP), s),
                       (hx, -1.06, 1.20), 'front-hinged armoured door: rotate %+d deg about Z' % (-70 * s), 'Doors'))
        panels.append(('Door_R' + sfx, side_cut(offset2(RD_OUT, -GAP), s), side_cut(offset2(RD_OUT, GAP), s),
                       (hx, -0.02, 1.20), 'front-hinged armoured door: rotate %+d deg about Z' % (-70 * s), 'Doors'))
        panels.append(('Locker_Door_' + sfx, side_cut(offset2(LK_OUT, -GAP), s), side_cut(offset2(LK_OUT, GAP), s),
                       (s * (xs(2.30) + 0.02), 1.80, 2.30),
                       'top-hinged equipment locker: rotate %+d deg about Y (swings up into an awning)' % (-100 * s),
                       'Equipment'))
        nm = 'Fuel_Door_L' if s == 1 else 'Utility_Hatch_R'
        panels.append((nm, side_cut(offset2(FU_OUT, -GAP), s), side_cut(offset2(FU_OUT, GAP), s),
                       (s * (xs(1.84) + 0.012), 2.57, 1.96), 'rotate %+d deg about Z' % (-95 * s), 'Body'))
        mb = [(s * x, y) for (x, y) in MB_OUT]
        panels.append(('Missile_Hatch_' + sfx, top_cut(offset2(mb, -GAP)), top_cut(offset2(mb, GAP)),
                       (s * 0.96, 1.90, Z_ROOF), 'armoured roof hatch: rotate %+d deg about Y' % (120 * s), 'Missiles'))
    panels.append(('Hood', top_cut(offset2(HOOD_OUT, -GAP), 1.50, 1.95), top_cut(offset2(HOOD_OUT, GAP), 1.50, 1.95),
                   (0, -1.20, 1.69), 'rear-hinged armoured hood: rotate -55 deg about X', 'Body'))
    panels.append(('Door_Rear', rear_cut(offset2(REAR_DOOR, -GAP)), rear_cut(offset2(REAR_DOOR, GAP)),
                   (0.84, 3.02, 1.40), 'side-hinged rear door: rotate -100 deg about Z', 'Doors'))

    pieces = {}
    grown = []
    for (nm, shr, grw, piv, note, col) in panels:
        p = dup(hull, nm, col)
        boolean(p, [cutter(nm + '_c', shr)], 'INTERSECT')
        set_origin(p, piv)
        anim(p, note)
        pieces[nm] = p
        grown.append(cutter(nm + '_g', grw))
    boolean(hull, grown)
    clear_scratch()

    for ob in [hull] + list(pieces.values()):
        bevel(ob, 0.010, 2, 30)

    # ------------------------------------------------------------ armoured glass (inset 15 mm, 50 mm thick)
    def side_glass(name, win, s, parent):
        g = offset2(win, 0.012)
        z_mid = sum(p[1] for p in g) / len(g)
        n = side_n(z_mid, s)
        pts = [side_pt(y, z, s, -0.015) for (y, z) in g]
        return mk(name, prism(pts, -n * 0.05), 'Glass', 'Glass', parent, bev=(0.004, 1, 30))
    for s, sfx in ((1, 'L'), (-1, 'R')):
        side_glass('Glass_DoorF' + sfx, FW_WIN, s, pieces['Door_F' + sfx])
        side_glass('Glass_DoorR' + sfx, RW_WIN, s, pieces['Door_R' + sfx])
    for i, (x0, x1, z0, z1) in enumerate(WS_PANES):
        pane = ws_pane(x0 - 0.012, x1 + 0.012, z0 - 0.012, z1 + 0.012, -0.015)
        mk('Glass_Windshield_' + ('L' if i == 0 else 'R'), prism(pane, -ws_normal() * 0.055), 'Glass', 'Glass',
           bev=(0.004, 1, 30))
    rw = offset2(REAR_WIN, 0.012)
    mk('Glass_RearDoor', prism([(x, Y_TAIL - 0.015, z) for (x, z) in rw], (0, -0.05, 0)), 'Glass', 'Glass',
       pieces['Door_Rear'], bev=(0.004, 1, 30))

    # ------------------------------------------------------------ wheel-well liners (tunnel + inner wall)
    for s, sfx in ((1, 'L'), (-1, 'R')):
        for ya, xin, fr in ((Y_AF, 0.48, 'F'), (Y_AR, 0.50, 'R')):
            arch = [(ya + dy, z) for (dy, z) in ARCH]
            # tunnel: arch polyline (front leg, over the top, rear leg), 20 mm thick, extruded across x.
            # legs stop at the hull floor (z 0.62) - below that the well is open to the ground.
            off = offset2(arch, 0.02)
            path_out = [(s * xin, y, max(z, Z_SILL)) for (y, z) in arch]
            path_in = [(s * xin, y, max(z, Z_SILL)) for (y, z) in off]
            parts = []
            for k in range(len(arch) - 1):
                a0, a1 = V(path_out[k]), V(path_out[k + 1])
                b0, b1 = V(path_in[k]), V(path_in[k + 1])
                quad = [a0, a1, b1, b0]
                parts.append(prism(quad, (s * (X_SIDE - 0.01 - xin), 0, 0)))
            # inner wall plate
            wall = [(s * xin, y, max(z, 0.55)) for (y, z) in arch]
            parts.append(prism(wall, (-s * 0.02, 0, 0)))
            mk('Liner_%s%s' % (fr, sfx), merge_vf(*parts), 'Coating', 'Body', bev=(0.004, 1, 30))
    return hull, pieces
