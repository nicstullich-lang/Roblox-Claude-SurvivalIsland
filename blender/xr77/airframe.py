"""XR-77 airframe: chined fuselage, canopy bulge, spiked-inlet nacelles, blended inner wing, tail root fairings and
gun blister -> one welded hull (EXACT boolean union). Then every opening in openings.py is cut in one pass and its
doors are built as panels that follow the original skin. Also builds the separate moving skins: radome, outer
(droop) wing panels, flaperons, ailerons, leading-edge flaps and the two all-moving canted tails.
"""
from .lib import *
from . import openings as OP

DOORS = {}          # name -> door object (filled by build(), used by the system stages)
CASTER = None       # ray caster on the uncut hull (used by later stages for decals, fasteners, grooves)


def hinge_pt(p2, proj, out=0.005):
    """a hinge point on the uncut skin under 2D point p2, pushed `out` metres outside the skin. Hinges must sit
    just outside the outer surface (on the opening edge) so the door edge swings clear of the surrounding skin."""
    loc, n = CASTER.on(p2, proj)
    return loc + n * out


def hinge_line(pa, pb, proj, out=0.005, n=11):
    """(midpoint, unit axis) of a hinge running along the 2D edge pa -> pb, placed `out` metres OUTSIDE the skin
    at its most outward point along the whole edge (a curved skin would otherwise put part of the edge below the
    axis, and that part would swing into the surrounding skin)."""
    a, b, c, s = PROJS[proj]
    vals = []
    for k in range(n):
        t = k / (n - 1)
        p2 = (pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t)
        vals.append(CASTER.on(p2, proj)[0][c])
    w = (max(vals) if s > 0 else min(vals)) + s * out
    mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
    d = to3(pb, proj, w) - to3(pa, proj, w)
    return to3(mid, proj, w), d.normalized()


# ======================================================================== component lofts
def fuselage_vf(y0, y1, shrink=0.0):
    return loft([body_section(y, shrink) for y in body_stations(y0, y1)])


def canopy_bulge_vf():
    loops = []
    ys = cosspace(-9.75, -4.45, 44)
    vs = cosspace(-1.0, 1.0, 24)
    for y in ys:
        w = Wcan_(y)
        loops.append([V((v * w, y, canopy_z(v * w, y))) for v in vs])
    return loft(loops)


def nacelle_vf(side):
    cx = side * NAC_X
    ys = sorted(set([round(y, 4) for y in cosspace(Y_LIP, -2.6, 16, (True, False))] +
                    [round(-2.6 + 0.25 * k, 4) for k in range(1, 47)] + [Y_NACEND]))
    ys = [y for y in ys if y <= Y_NACEND]
    loops = []
    for y in ys:
        r = NR_(y)
        loops.append([V((cx + r * cos(a), y, NAC_Z + r * sin(a))) for a in [2 * pi * k / 56 for k in range(56)]])
    return loft(loops)


def wing_section(x, xs_sign=1):
    """closed aerofoil loop at span station x (>0); y from LE to TE, z about ZW."""
    le, te = wing_le(x), WING_TE
    c = te - le
    tc = wing_tc(x)
    ss = cosspace(0.0, 1.0, 40)
    up = [V((xs_sign * x, le + s * c, ZW + max(foil_t(s, tc) * c / 2, 0.0015))) for s in reversed(ss)]
    lo = [V((xs_sign * x, le + s * c, ZW - max(foil_t(s, tc) * c / 2, 0.0015))) for s in ss[1:-1]]
    return up + lo


def wing_vf(x0, x1, side, n=None):
    n = n or max(4, int((x1 - x0) / 0.1))
    xs = [x0 + (x1 - x0) * k / n for k in range(n + 1)]
    return loft([wing_section(x, side) for x in xs])


def wing_z(x, y, upper=True):
    """aerofoil surface height at (x, y) of the outer wing."""
    x = abs(x)
    le, te = wing_le(x), WING_TE
    s = (y - le) / (te - le)
    h = max(foil_t(s, wing_tc(x)) * (te - le) / 2, 0.0015)
    return ZW + h if upper else ZW - h


def tail_root_fairing_vf(side):
    cx = side * NAC_X
    loops = []
    ys = cosspace(5.80, Y_NACEND - 0.02, 30)
    for y in ys:
        t = (y - 5.80) / (Y_NACEND - 0.02 - 5.80)
        hw = max(0.012, 0.17 * min(1.0, t / 0.18) ** 0.6)
        top = TAIL_ROOT_Z - 0.06
        base = nacelle_top(y) - 0.10
        if t < 0.18:
            top = base + (top - base) * (t / 0.18) ** 0.5
        pts = []
        for k in range(13):
            a = pi * k / 12
            pts.append(V((cx + hw * cos(a), y, base + (top - base) * (sin(a) ** 0.35))))
        pts.append(V((cx - hw, y, base - 0.08)))
        pts.append(V((cx + hw, y, base - 0.08)))
        loops.append(pts)
    return loft(loops)


def gun_blister_vf():
    loops = []
    ys = cosspace(-10.62, -7.70, 30)
    for y in ys:
        if y < -10.20:
            k = max(0.04, ((y + 10.62) / 0.42) ** 0.55)
        elif y > -8.40:
            k = max(0.08, 1 - ((y + 8.40) / 0.70) ** 1.4)
        else:
            k = 1.0
        a, b = 0.245 * k, 0.215 * k
        zc = 1.70 + (1 - k) * 0.12
        loops.append([V((0.30 + a * cos(t), y, zc + b * sin(t))) for t in [2 * pi * i / 28 for i in range(28)]])
    return loft(loops)


def radome_vf(shrink=0.0):
    ys = cosspace(Y_NOSE + 0.015, Y_RADOME - GAP, 22, (True, False)) if shrink == 0 else cosspace(-12.0, Y_RADOME + 0.05, 12, (False, False))
    return loft([body_section(y, shrink) for y in ys])


# ======================================================================== moving aero surfaces
def outer_wing(side):
    x0, x1 = HINGE_X + GAP, WING_TIP_X
    ob = mk('Wingtip_' + ('L' if side > 0 else 'R'), wing_vf(x0, x1, side, 26), 'Skin', 'Aero', sharp=40)
    return ob


def tail_vf(side):
    span, thick = tail_axes(side)
    root = V((side * NAC_X, 0.0, TAIL_ROOT_Z))
    loops = []
    hs = cosspace(0.0, TAIL_SPAN, 22, (False, True))
    for h in hs:
        le = TAIL_LE0 + h * 1.0
        te = TAIL_TE0 + h * 0.268
        c = te - le
        tc = 0.045 + (0.035 - 0.045) * h / TAIL_SPAN
        ss = cosspace(0.0, 1.0, 34)
        o = root + span * h
        up = [V((o.x, le + s * c, o.z)) + thick * max(foil_t(s, tc) * c / 2, 0.0015) for s in reversed(ss)]
        lo = [V((o.x, le + s * c, o.z)) - thick * max(foil_t(s, tc) * c / 2, 0.0015) for s in ss[1:-1]]
        loops.append(up + lo)
    return loft(loops)


def surface_cutter(x0, x1, hinge_y, y_end, z0, r, grow=0.0, le_side=False):
    """cutter for a control surface with a round nose sitting in a cove: hinge line along X at (hinge_y, z0)."""
    r = r + grow
    pts = []
    for k in range(13):
        a = pi / 2 + pi * k / 12                     # front half-circle (toward -y)
        pts.append((hinge_y + r * cos(a), z0 + r * sin(a)))
    pts = list(reversed(pts))                         # bottom -> front -> top
    pts += [(y_end + 0.3, z0 + 0.4), (y_end + 0.3, z0 - 0.4)]
    outline = [(y, z) for (y, z) in pts]
    # extrude along X
    A = [V((x0 - grow, y, z)) for y, z in outline]
    return prism(A, (x1 - x0 + 2 * grow, 0, 0))


def le_flap_cutter(side, x0, x1, chord, grow=0.0):
    """leading-edge flap cutter: the strip in front of a hinge line parallel to the swept leading edge. Its ends
    are cut square to the hinge line (a flap end parallel to Y would swing into the wing on a swept hinge)."""
    a = V((1.0, LE_TAN, 0.0)).normalized()            # hinge direction (left wing, x > 0)
    nf = V((a.y, -a.x, 0.0))                         # forward normal (toward the leading edge)
    h0 = V((x0, wing_le(x0) + chord, 0.0)) - nf * grow - a * grow
    h1 = V((x1, wing_le(x1) + chord, 0.0)) - nf * grow + a * grow
    poly = [h0, h1, h1 + nf * 1.2, h0 + nf * 1.2]
    A = [V((side * p.x, p.y, ZW - 0.5)) for p in poly]
    return prism(A, (0, 0, 1.0))


# ======================================================================== build
def build():
    global CASTER
    t_slots = OP.BODY_SLOTS
    # ---------------------------------------------------------------- hull components
    fus = mk('Airframe', fuselage_vf(Y_RADOME + GAP, Y_TAILEND), t_slots, 'Body', sharp=40)
    parts = [mk('_canopy_bulge', canopy_bulge_vf(), 'Skin', 'Body', sharp=40),
             mk('_gun_blister', gun_blister_vf(), 'Skin', 'Body', sharp=40)]
    for side in (1, -1):
        parts.append(mk('_nacelle_%d' % side, nacelle_vf(side), 'Skin', 'Body', sharp=40))
        parts.append(mk('_wing_%d' % side, wing_vf(NAC_X, HINGE_X - GAP, side, 28), 'Skin', 'Body', sharp=40))
        parts.append(mk('_tailfair_%d' % side, tail_root_fairing_vf(side), 'Skin', 'Body', sharp=40))
    boolean(fus, parts, 'UNION')
    for p in parts:
        bpy.data.objects.remove(p, do_unlink=True)

    # ---------------------------------------------------------------- separate moving skins
    rad = mk('Radome', radome_vf(), 'Skin', 'Body', sharp=40)
    hol = cutter('_radome_hollow', radome_vf(0.028))
    boolean(rad, [hol])
    wt = {s: outer_wing(s) for s in (1, -1)}
    for side in (1, -1):
        mk('Tail_' + ('L' if side > 0 else 'R'), tail_vf(side), 'Skin', 'Aero', sharp=40)

    # ---------------------------------------------------------------- caster on the uncut hull (+ outer wings)
    CASTER = Caster([fus, rad] + list(wt.values()) + [bpy.data.objects['Tail_L'], bpy.data.objects['Tail_R']])

    # ---------------------------------------------------------------- openings: doors from the skin, then one cut
    cut_list = []
    for op in OP.openings():
        a, b, c, s = PROJS[op['proj']]
        start = op['depth_from'] if op['depth_from'] is not None else s * 9.0
        grown = offset2(ccw(op['outline']), GAP)
        A = [to3(p, op['proj'], start) for p in grown]
        d = [0.0, 0.0, 0.0]
        d[c] = op['floor'] - start
        cvf = prism(A, d)
        co = cutter('_cut_' + op['name'], cvf)
        for poly in co.data.polygons:
            poly.material_index = op['slot']
        cut_list.append(co)
        for dd in op['doors']:
            vf = skin_patch(CASTER, dd['outline'], op['proj'], t=dd['t'], spacing=0.10, inset=GAP)
            mi = skin_patch.last_mi
            ob = mk(dd['name'], vf, list(dd['mats']), 'Doors', sharp=40, mat_idx=mi)
            ob['opening'] = op['name']
            DOORS[dd['name']] = ob

    # engine ducts / bays (lathe cutters) + lift-fan duct + gun barrel tunnel
    for side in (1, -1):
        cx = side * NAC_X
        prof = [(0.0, -4.80)] + [(DUCT_(y), y) for y in cosspace(-4.80, -1.78, 24)] + [(0.0, -1.78)]
        duct = orient(lathe_vf(prof, 48), (cx, 0, NAC_Z), 'Y')
        co = cutter('_cut_duct_%d' % side, duct)
        for poly in co.data.polygons:
            poly.material_index = OP.SLOT['SkinDark']
        cut_list.append(co)
        prof = [(0.0, -1.82)] + [(BAY_R_(y), y) for y in cosspace(-1.82, 9.30, 40)] + [(0.0, 9.30)]
        bay = orient(lathe_vf(prof, 48), (cx, 0, NAC_Z), 'Y')
        co = cutter('_cut_engbay_%d' % side, bay)
        for poly in co.data.polygons:
            poly.material_index = OP.SLOT['Insulation']
        cut_list.append(co)
    fan = cyl_vf((0.0, -3.60, 2.10), 0.78, 2.4, 'Z', 48)
    co = cutter('_cut_fanduct', fan)
    for poly in co.data.polygons:
        poly.material_index = OP.SLOT['BayGrey']
    cut_list.append(co)
    gun = cyl_between((0.30, -10.90, 1.70), (0.30, -8.05, 1.70), 0.165, 20)
    co = cutter('_cut_guntunnel', gun)
    for poly in co.data.polygons:
        poly.material_index = OP.SLOT['BayGrey']
    cut_list.append(co)

    boolean(fus, cut_list)
    fus.data.set_sharp_from_angle(angle=radians(40))

    # ---------------------------------------------------------------- control surfaces cut from the wings
    for side in (1, -1):
        sfx = 'L' if side > 0 else 'R'
        wing_in = fus
        # flaperon (inner wing trailing edge)
        x0, x1, hy = 3.30, 5.10, 6.55
        r = (wing_z(x0, hy) - ZW) * 1.12
        sel = mk('Flaperon_' + sfx, ([], []), 'Skin', 'Aero')
        fl_src = mk('_wing_src_%s' % sfx, wing_vf(3.0, 5.15, side, 22), 'Skin', 'Aero')
        lo, hi = (x0, x1) if side > 0 else (-x1, -x0)
        cut_in = cutter('_flp_in', surface_cutter(lo, hi, hy, WING_TE, ZW, r, -GAP))
        boolean(fl_src, [cut_in], 'INTERSECT')
        sel.data = fl_src.data
        sel.data.name = sel.name
        bpy.data.objects.remove(fl_src, do_unlink=True)
        cut_out = cutter('_flp_out', surface_cutter(lo, hi, hy, WING_TE, ZW, r, GAP))
        boolean(wing_in, [cut_out])
        # aileron (outer, drooping wing panel)
        ax0, ax1, ahy = 5.34, 7.30, 6.70
        r2 = (wing_z(ax0, ahy) - ZW) * 1.12
        ail = mk('Aileron_' + sfx, ([], []), 'Skin', 'Aero')
        src = mk('_ail_src', wing_vf(HINGE_X + GAP, WING_TIP_X, side, 26), 'Skin', 'Aero')
        lo, hi = (ax0, ax1) if side > 0 else (-ax1, -ax0)
        boolean(src, [cutter('_ail_in', surface_cutter(lo, hi, ahy, WING_TE, ZW, r2, -GAP))], 'INTERSECT')
        ail.data = src.data
        ail.data.name = ail.name
        bpy.data.objects.remove(src, do_unlink=True)
        boolean(wt[side], [cutter('_ail_out', surface_cutter(lo, hi, ahy, WING_TE, ZW, r2, GAP))])
        # leading-edge flap (inner wing, outboard of the nacelle)
        lx0, lx1, lch = 3.40, 5.10, 0.42
        lef = mk('LEFlap_' + sfx, ([], []), 'Skin', 'Aero')
        src = mk('_lef_src', wing_vf(3.2, 5.15, side, 20), 'Skin', 'Aero')
        boolean(src, [cutter('_lef_in', le_flap_cutter(side, lx0, lx1, lch, -GAP))], 'INTERSECT')
        lef.data = src.data
        lef.data.name = lef.name
        bpy.data.objects.remove(src, do_unlink=True)
        boolean(wing_in, [cutter('_lef_out', le_flap_cutter(side, lx0, lx1, lch, GAP))])
    fus.data.set_sharp_from_angle(angle=radians(40))
    for o in [bpy.data.objects[n] for n in ('Flaperon_L', 'Flaperon_R', 'Aileron_L', 'Aileron_R', 'LEFlap_L',
                                            'LEFlap_R', 'Wingtip_L', 'Wingtip_R', 'Radome')]:
        o.data.set_sharp_from_angle(angle=radians(40))
