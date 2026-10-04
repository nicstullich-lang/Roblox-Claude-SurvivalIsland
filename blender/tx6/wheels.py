"""TX-6 Bastion - 47" military tyres, beadlock wheels, brakes, uprights and double-wishbone suspension.

Wheel geometry is built in a local frame (lathe axis = +Z = outboard face) and placed per corner.
Right-side wheels use mirrored geometry so the directional tread rolls the right way on both sides.
"""
from tx6.lib import *

RB = 0.288          # bead seat radius (22.5" class wheel)
R_CROWN = 0.562     # carcass radius under the tread

TIRE_PROFILE = [(RB, -0.170), (0.312, -0.196), (0.330, -0.206), (0.342, -0.204), (0.390, -0.219), (0.450, -0.222),
                (0.505, -0.212), (0.535, -0.195), (0.552, -0.165), (0.558, -0.110), (0.561, -0.040), (R_CROWN, 0.0),
                (0.561, 0.040), (0.558, 0.110), (0.552, 0.165), (0.535, 0.195), (0.505, 0.212), (0.450, 0.222),
                (0.390, 0.219), (0.342, 0.204), (0.330, 0.206), (0.312, 0.196), (RB, 0.170),
                (RB - 0.010, 0.120), (RB - 0.012, 0.0), (RB - 0.010, -0.120), (RB, -0.170)]


def _rc(z):
    """carcass radius at lateral position z (crown region)."""
    z = abs(z)
    pts = [(0.0, R_CROWN), (0.040, 0.561), (0.110, 0.558), (0.165, 0.552), (0.195, 0.535), (0.212, 0.505), (0.222, 0.450)]
    for (z0, r0), (z1, r1) in zip(pts, pts[1:]):
        if z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return pts[-1][1]


def _pt(r, a, z):
    return V((r * cos(a), r * sin(a), z))


def tire_local(n=64, lugs_per_side=22):
    parts = [lathe_vf(TIRE_PROFILE, n, cap0=False, cap1=False)]
    pitch = 2 * pi / lugs_per_side
    wa = 0.088 / R_CROWN
    lean = tan(radians(30))
    zs = [0.012, 0.06, 0.11, 0.16, 0.19, 0.214]
    rt = {0.012: 0.603, 0.06: 0.604, 0.11: 0.603, 0.16: 0.600, 0.19: 0.588, 0.214: 0.560}
    rb = {0.012: R_CROWN - 0.006, 0.06: 0.555, 0.11: 0.552, 0.16: 0.545, 0.19: 0.525, 0.214: 0.478}
    for side in (1, -1):
        for i in range(lugs_per_side):
            a0 = i * pitch + (pitch / 2 if side < 0 else 0)
            loops = []
            for z in zs:
                lead = a0 + z * lean / R_CROWN
                trail = lead + wa * (1.0 + 0.25 * z / 0.214)
                loops.append([_pt(rb[z], lead, z * side), _pt(rt[z], lead, z * side),
                              _pt(rt[z], trail, z * side), _pt(rb[z], trail, z * side)])
            parts.append(loft(loops))
            # sidewall protector block below each shoulder lug
            am = a0 + 0.214 * lean / R_CROWN + wa * 0.55
            w2 = wa * 0.45
            q = [[_pt(0.425, am - w2, 0.214 * side), _pt(0.425, am - w2, 0.232 * side),
                  _pt(0.425, am + w2, 0.232 * side), _pt(0.425, am + w2, 0.214 * side)],
                 [_pt(0.488, am - w2, 0.204 * side), _pt(0.488, am - w2, 0.222 * side),
                  _pt(0.488, am + w2, 0.222 * side), _pt(0.488, am + w2, 0.204 * side)]]
            parts.append(loft(q))
    return merge_vf(*parts)


def rim_local(n=48):
    """returns dict of material -> vf (local frame, +Z = outboard)."""
    barrel = [(0.276, 0.205), (0.302, 0.205), (0.306, 0.190), (0.291, 0.176), (0.287, 0.100), (0.287, -0.150),
              (0.293, -0.176), (0.303, -0.188), (0.300, -0.200), (0.272, -0.200), (0.269, -0.150), (0.269, 0.150),
              (0.276, 0.205)]
    ring = [(0.236, 0.205), (0.306, 0.205), (0.306, 0.226), (0.300, 0.230), (0.242, 0.230), (0.236, 0.226), (0.236, 0.205)]
    disc = [(0.112, 0.050), (0.272, 0.050), (0.272, 0.070), (0.112, 0.070), (0.112, 0.050)]
    hub = [(0, -0.115), (0.062, -0.115), (0.062, 0.070), (0.118, 0.070), (0.118, 0.128), (0.112, 0.134), (0.075, 0.134), (0.072, 0.150), (0.060, 0.170),
           (0.040, 0.180), (0, 0.183)]
    # disc with 8 trapezoid hand-holes (boolean once)
    dv = lathe_vf(disc, n, False, False)
    me_o = cutter('_rimdisc', dv)
    holes = []
    for k in range(8):
        a = 2 * pi * k / 8 + pi / 8
        pts = []
        for (r, da) in ((0.150, -0.17), (0.242, -0.20), (0.242, 0.20), (0.150, 0.17)):
            pts.append((r * cos(a + da), r * sin(a + da), 0.0))
        holes.append(cutter('_hole', prism([(x, y, -0.05) for (x, y, _) in pts], (0, 0, 0.2))))
    boolean(me_o, holes)
    disc_vf = ([v.co.copy() for v in me_o.data.vertices], [tuple(p.vertices) for p in me_o.data.polygons])
    parts_rim = [lathe_vf(barrel, n, False, False), disc_vf, lathe_vf(hub, 32, False, False)]
    # stiffening ribs between the holes
    for k in range(8):
        a = 2 * pi * k / 8
        p0 = V((0.118 * cos(a), 0.118 * sin(a), 0.070))
        p1 = V((0.262 * cos(a), 0.262 * sin(a), 0.070))
        parts_rim.append(sweep_vf([p0, p1], [(-0.0, -0.011), (0.022, -0.011), (0.022, 0.011), (0.0, 0.011)]))
    beadlock = [lathe_vf(ring, n, False, False)]
    for k in range(18):
        a = 2 * pi * k / 18
        beadlock.append(bolt_vf((0.272 * cos(a), 0.272 * sin(a), 0.230), (0, 0, 1), 0.0105, 0.010))
    nuts = []
    for k in range(10):
        a = 2 * pi * k / 10
        nuts.append(bolt_vf((0.093 * cos(a), 0.093 * sin(a), 0.134), (0, 0, 1), 0.0135, 0.020, washer=True))
    # CTIS (central tyre inflation) rotary seal + hose to the valve on the rim
    ctis = [cyl_vf((0, 0, 0.190), 0.022, 0.016, 'Z', 16)]
    hose = [V((0.018, 0.0, 0.192)), V((0.08, 0.02, 0.196)), V((0.16, 0.05, 0.20)), V((0.215, 0.07, 0.212)),
            V((0.238, 0.08, 0.226))]
    ctis_hose = tube_vf(hose, 0.0065, 8)
    ctis.append(cyl_vf((0.245, 0.082, 0.234), 0.010, 0.024, 'Z', 8))
    rotor = [lathe_vf([(0.105, -0.052), (0.212, -0.052), (0.212, -0.016), (0.105, -0.016), (0.105, -0.052)], n, False, False),
             lathe_vf([(0.095, -0.016), (0.118, -0.016), (0.118, 0.052), (0.095, 0.052), (0.095, -0.016)], 32, False, False)]
    clear_scratch()
    return {'Rim': merge_vf(*parts_rim), 'Beadlock': merge_vf(*beadlock), 'Nuts': merge_vf(*nuts),
            'CTIS': merge_vf(*ctis), 'CTISHose': ctis_hose, 'Rotor': merge_vf(*rotor)}


def caliper_local():
    """brake caliper (does not spin) in the local wheel frame, sits at the rear-top of the rotor."""
    a0, a1 = radians(105), radians(160)
    path = [V((0.19 * cos(a0 + (a1 - a0) * k / 8), 0.19 * sin(a0 + (a1 - a0) * k / 8), -0.034)) for k in range(9)]
    body = sweep_vf(path, [(-0.045, -0.050), (0.040, -0.050), (0.040, 0.030), (-0.045, 0.030)])
    return body


def place(vf, C, s, spin=0.0):
    """local wheel frame -> world. local +Z -> world +X (left) / mirrored for right side."""
    m = Matrix.Translation(V(C)) @ Matrix.Rotation(radians(90), 4, 'Y') @ Matrix.Rotation(spin, 4, 'Z')
    vv, ff = xform_vf(vf, m)
    if s < 0:
        c = V(C)
        vv = [V((2 * c.x - v.x, v.y, v.z)) for v in vv]
        ff = [tuple(reversed(f)) for f in ff]
    return vv, ff


def box_arm(p0, p1, w, h):
    return sweep_vf([V(p0), V(p1)], [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)])


def bushing(c, axis, r=0.032, L=0.07):
    return cyl_vf(c, r, L, axis, 12)


def build():
    tire = tire_local()
    rim = rim_local()
    cal = caliper_local()
    out = {}
    for (fr, ya, xin) in (('F', Y_AF, 0.48), ('R', Y_AR, 0.50)):
        for s, sfx in ((1, 'L'), (-1, 'R')):
            tag = fr + sfx
            C = V((s * X_TRACK, ya, Z_WHEEL))
            up = empty('Upright_' + tag, C, 'Wheels', size=0.3)
            anim(up, 'steering pivot: rotate about Z (front only, +-32 deg)' if fr == 'F' else 'rear upright (fixed)')
            wh = empty('Wheel_' + tag, C, 'Wheels', parent=up, size=0.35)
            anim(wh, 'wheel spin: rotate about X')
            mk('Tire_' + tag, place(tire, C, s), 'Tire', 'Wheels', wh, sharp=40)
            mk('Rim_' + tag, place(rim['Rim'], C, s), 'Rim', 'Wheels', wh, sharp=40, bev=(0.003, 1, 40))
            mk('Beadlock_' + tag, place(rim['Beadlock'], C, s), 'Hardware', 'Wheels', wh, sharp=40)
            mk('LugNuts_' + tag, place(rim['Nuts'], C, s), 'Steel', 'Wheels', wh, sharp=40)
            mk('CTIS_' + tag, place(rim['CTIS'], C, s), 'Brass', 'Wheels', wh, sharp=40)
            mk('CTISHose_' + tag, place(rim['CTISHose'], C, s), 'Rubber', 'Wheels', wh, sharp=60)
            mk('Rotor_' + tag, place(rim['Rotor'], C, s), 'Steel', 'Wheels', wh, sharp=40)
            # ---------------- upright / knuckle (steers, does not spin)
            xk = s * (X_TRACK - 0.155)
            LB = V((s * 0.985, ya, 0.375))
            UB = V((s * 0.975, ya, 0.810))
            knuck = merge_vf(
                box_arm(V((xk, ya, 0.40)), V((xk, ya, 0.79)), 0.07, 0.10),
                cyl_vf(V((xk + s * 0.02, ya, Z_WHEEL)), 0.085, 0.06, 'X', 20),
                box_arm(V((xk, ya, 0.40)), LB, 0.06, 0.05),
                box_arm(V((xk, ya, 0.79)), UB, 0.06, 0.05),
                cyl_vf(LB, 0.03, 0.05, 'Z', 12), cyl_vf(UB, 0.028, 0.05, 'Z', 12),
            )
            parts = [knuck, place(cal, C, s)]
            if fr == 'F':
                parts.append(box_arm(V((xk, ya + 0.02, 0.52)), V((s * 0.90, ya + 0.17, 0.53)), 0.035, 0.03))
            else:
                parts.append(box_arm(V((xk, ya + 0.02, 0.54)), V((s * 0.90, ya + 0.20, 0.55)), 0.035, 0.03))
            mk('Knuckle_' + tag, merge_vf(*parts), 'Gunmetal', 'Suspension', up, bev=(0.004, 1, 30))
            # ---------------- control arms (boxed lower A-arm, tubular upper A-arm)
            x0 = xin + 0.035
            LPf, LPr = V((s * x0, ya - 0.24, 0.47)), V((s * x0, ya + 0.24, 0.47))
            UPf, UPr = V((s * (x0 + 0.05), ya - 0.17, 0.94)), V((s * (x0 + 0.05), ya + 0.17, 0.94))
            lower = merge_vf(box_arm(LPf, LB, 0.07, 0.055), box_arm(LPr, LB, 0.07, 0.055),
                             box_arm(LPf.lerp(LB, 0.45), LPr.lerp(LB, 0.45), 0.05, 0.04),
                             bushing(LPf, 'Y'), bushing(LPr, 'Y'))
            # bracket for the auxiliary damper on the front leg
            dl = V((s * 0.78, ya - 0.24, 0.445))
            lower = merge_vf(lower, box_arm(LPf.lerp(LB, 0.62) + V((0, 0, 0.0)), dl, 0.05, 0.045),
                             cyl_vf(dl, 0.024, 0.06, 'Y', 12))
            upper = merge_vf(tube_vf([UPf, UB], 0.026, 10), tube_vf([UPr, UB], 0.026, 10),
                             tube_vf([UPf.lerp(UB, 0.5), UPr.lerp(UB, 0.5)], 0.022, 8),
                             bushing(UPf, 'Y', 0.028, 0.06), bushing(UPr, 'Y', 0.028, 0.06))
            # chassis brackets (double shear plates) on the well wall
            br = []
            for p in (LPf, LPr, UPf, UPr):
                for dy in (-0.045, 0.045):
                    br.append(box_vf(p + V((-s * 0.02, dy, 0)), (0.10, 0.012, 0.11)))
                br.append(bolt_vf(p + V((0, -0.052, 0)), (0, -1, 0), 0.014, 0.012))
            cl = (UPf.lerp(UB, 0.5) + UPr.lerp(UB, 0.5)) / 2 + V((0, 0, 0.035))
            upper = merge_vf(upper, cyl_vf(cl - V((0, 0, 0.012)), 0.03, 0.05, 'Y', 12))
            mk('Arms_' + tag, merge_vf(lower, upper), 'Gunmetal', 'Suspension', bev=(0.004, 1, 30))
            mk('ArmBrackets_' + tag, merge_vf(*br), 'Hardware', 'Suspension')
            # ---------------- coilover on the upper arm + auxiliary damper with piggy-back reservoir
            cu = V((s * 0.64, ya, 1.31))
            ax = (cu - cl).normalized()
            Lc = (cu - cl).length
            spring = helix(V((0, 0, 0)), 0.078, Lc - 0.10, 6.5, 14)
            spring_w = [cl + (orient(([p], []), (0, 0, 0), ax)[0][0]) + ax * 0.05 for p in spring]
            coil = tube_vf(spring_w, 0.013, 6, caps=True)
            shock = merge_vf(cyl_between(cl, cl + ax * 0.24, 0.032, 14), cyl_between(cl + ax * 0.22, cu, 0.018, 10),
                             cyl_between(cl + ax * 0.03, cl + ax * 0.05, 0.092, 18),
                             cyl_between(cu - ax * 0.05, cu - ax * 0.03, 0.092, 18),
                             cyl_vf(cl, 0.03, 0.05, 'Y', 12), cyl_vf(cu, 0.03, 0.05, 'Y', 12))
            mk('Spring_' + tag, coil, 'SafetyRed', 'Suspension', sharp=60)
            mk('Coilover_' + tag, shock, 'Alu', 'Suspension')
            du = V((s * 0.60, ya - 0.26, 1.28))
            dax = (du - dl).normalized()
            res_c = dl + dax * 0.20 + V((0, -0.06, 0))
            damper = merge_vf(cyl_between(dl, dl + dax * 0.40, 0.036, 14), cyl_between(dl + dax * 0.38, du, 0.017, 10),
                              cyl_between(res_c - dax * 0.10, res_c + dax * 0.10, 0.026, 12),
                              tube_vf([dl + dax * 0.33, res_c + dax * 0.11 + V((0, 0.0, 0.02))], 0.007, 6),
                              cyl_vf(du, 0.026, 0.05, 'Y', 12),
                              box_vf(du + V((0, 0, 0.04)), (0.08, 0.08, 0.03)))
            mk('Damper_' + tag, damper, 'Gunmetal', 'Suspension')
            # spring perch / shock tower plate on the well top
            mk('ShockTower_' + tag, merge_vf(box_vf(V((s * 0.62, ya - 0.08, 1.335)), (0.22, 0.46, 0.03)),
                                               box_vf(cu + V((0, 0, 0.012)), (0.09, 0.09, 0.025))),
               'Hardware', 'Suspension', bev=(0.004, 1, 30))
            # bump stop above the upper arm
            mk('BumpStop_' + tag, merge_vf(cyl_vf(V((s * 0.80, ya + 0.10, 1.26)), 0.035, 0.16, 'Z', 12),
                                            cyl_vf(V((s * 0.80, ya + 0.10, 1.335)), 0.05, 0.02, 'Z', 12)),
               'Rubber', 'Suspension')
            # ---------------- half shaft with CV joints and boots
            hs0, hs1 = V((s * (xin - 0.02), ya, Z_WHEEL)), V((s * (X_TRACK - 0.19), ya, Z_WHEEL))
            boots = []
            for (p, d) in ((hs0, 1), (hs1, -1)):
                for k in range(4):
                    t = 0.03 + 0.025 * k
                    boots.append(cyl_vf(p + V((s * d * t, 0, 0)), 0.055 - 0.008 * k + (0.006 if k % 2 else 0), 0.024, 'X', 14))
            mk('HalfShaft_' + tag, cyl_between(hs0, hs1, 0.026, 12), 'Steel', 'Suspension')
            mk('CVBoots_' + tag, merge_vf(*boots), 'Rubber', 'Suspension')
            # ---------------- steering tie rod / rear toe link
            if fr == 'F':
                tr0, tr1 = V((s * (xin - 0.005), ya + 0.17, 0.53)), V((s * 0.90, ya + 0.17, 0.53))
                mk('TieRod_' + tag, merge_vf(cyl_between(tr0, tr1, 0.017, 10), cyl_vf(tr1, 0.026, 0.05, 'Z', 10),
                                              cyl_between(tr0, tr0 + V((s * 0.09, 0, 0)), 0.03, 12)),
                   'Steel', 'Suspension')
            else:
                tr0, tr1 = V((s * (xin - 0.005), ya + 0.20, 0.55)), V((s * 0.90, ya + 0.20, 0.55))
                mk('ToeLink_' + tag, merge_vf(cyl_between(tr0, tr1, 0.016, 10), cyl_vf(tr1, 0.024, 0.05, 'Z', 10)),
                   'Steel', 'Suspension')
            # ---------------- brake hose (chassis -> caliper)
            cp = place(([V((0.19 * cos(radians(130)), 0.19 * sin(radians(130)), -0.06))], []), C, s)[0][0]
            hose = [V((s * (xin + 0.02), ya + 0.30, 1.15)), V((s * 0.70, ya + 0.25, 1.00)), V((s * 0.86, ya + 0.12, 0.80)),
                    V((s * 0.93, ya + 0.10, 0.78)), cp]
            mk('BrakeHose_' + tag, tube_vf(hose, 0.007, 6), 'Rubber', 'Suspension')
            out[tag] = (up, wh)
    return out
