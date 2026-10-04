"""TX-6 Bastion - heavy front bumper (winch, shackles, grille guard, skid), armoured grille, rear bumper + pintle."""
from tx6.lib import *
from tx6.armor import box_arm


def bumper_vf(profile_mid, profile_end, xm, xe):
    """extrude a (y,z) profile across +-xm, then loft to an angled end profile at +-xe."""
    mid_l = [(xm, y, z) for (y, z) in profile_mid]
    mid_r = [(-xm, y, z) for (y, z) in profile_mid]
    end_l = [(xe, y, z) for (y, z) in profile_end]
    end_r = [(-xe, y, z) for (y, z) in profile_end]
    return loft([end_r, mid_r, mid_l, end_l])


def d_ring(c, out, r_bow=0.016):
    """D-ring: bow in the X/out plane, pin along X."""
    c, out = V(c), V(out).normalized()
    path = []
    w, d = 0.050, 0.085
    for k in range(17):
        a = pi * k / 16
        path.append(c + V((w * cos(a), 0, 0)) + out * (0.012 + d * sin(a)))
    bow = tube_vf(path, r_bow, 10)
    eyes = merge_vf(cyl_vf(c + V((w, 0, 0)), r_bow * 1.6, 0.03, 'X', 12),
                    cyl_vf(c + V((-w, 0, 0)), r_bow * 1.6, 0.03, 'X', 12))
    pin = merge_vf(cyl_vf(c, 0.011, 0.14, 'X', 10), cyl_vf(c + V((0.072, 0, 0)), 0.019, 0.016, 'X', 6))
    return merge_vf(bow, eyes), pin


def build():
    # ======================================================== FRONT BUMPER
    fmid = [(-2.99, 0.50), (-3.18, 0.50), (-3.30, 0.60), (-3.30, 0.84), (-3.22, 0.94), (-2.99, 0.94)]
    fend = [(-2.99, 0.54), (-3.14, 0.54), (-3.20, 0.62), (-3.20, 0.84), (-3.16, 0.92), (-2.99, 0.92)]
    fb = mk('Bumper_Front', bumper_vf(fmid, fend, 1.12, 1.34), 'Coating', 'Equipment')
    # winch recess
    boolean(fb, [cutter('_winch', box_between((-0.31, -3.40, 0.60), (0.31, -3.13, 0.87)))])
    clear_scratch()
    bevel(fb, 0.008, 2, 30)
    # top tread pads
    pads = []
    for s in (1, -1):
        for k in range(7):
            x = s * (0.36 + 0.04 * k)
            pads.append(box_vf((x, -3.10, 0.945), (0.022, 0.20, 0.012)))
    mk('Bumper_Front_Tread', merge_vf(*pads), 'Hardware', 'Equipment')
    # face bolts
    bp = [V((x, -3.302, z)) for x in (-1.0, -0.62, 0.62, 1.0) for z in (0.66, 0.80)]
    bolts('Bumper_Front_Bolts', bp, V((0, -1, 0)), fb, r=0.014, h=0.010, washer=True)
    # ---- winch: drum, rope wraps, motor, gearbox, hawse fairlead, hook
    wc = V((0, -3.205, 0.735))
    drum = merge_vf(cyl_vf(wc, 0.060, 0.44, 'X', 20), cyl_vf(wc + V((0.215, 0, 0)), 0.095, 0.02, 'X', 20),
                    cyl_vf(wc - V((0.215, 0, 0)), 0.095, 0.02, 'X', 20))
    mk('Winch_Drum', drum, 'Hardware', 'Equipment')
    wraps = []
    for k in range(9):
        x = -0.19 + 0.0475 * k
        wraps.append(lathe_vf([(0.060, -0.022), (0.078, -0.020), (0.083, 0.0), (0.078, 0.020), (0.060, 0.022)], 16,
                              False, False))
        wraps[-1] = orient(wraps[-1], wc + V((x, 0, 0)), 'X')
    mk('Winch_Rope', merge_vf(*wraps), 'Rope', 'Equipment', sharp=60)
    mk('Winch_Motor', merge_vf(cyl_vf(wc + V((0.272, 0, 0)), 0.080, 0.075, 'X', 20),
                               cyl_vf(wc + V((0.300, 0, 0.0)), 0.060, 0.02, 'X', 20)), 'Gunmetal', 'Equipment')
    mk('Winch_Gearbox', box_vf(wc - V((0.27, 0, 0)), (0.07, 0.17, 0.17)), 'Gunmetal', 'Equipment', bev=(0.01, 2, 30))
    # hawse fairlead (aluminium plate with rounded slot)
    fo = [(x, -3.305, z) for (x, z) in rrect2(0.30, 0.11, 0.035, 4, 0, 0.735)]
    fi = [(x, -3.305, z) for (x, z) in rrect2(0.20, 0.035, 0.0175, 4, 0, 0.735)]
    mk('Winch_Fairlead', ring_prism(fo, fi, (0, -0.035, 0)), 'Alu', 'Equipment', bev=(0.006, 2, 30))
    bolts('Winch_Fairlead_Bolts', [V((x, -3.340, 0.735)) for x in (-0.12, 0.12)], V((0, -1, 0)), None, r=0.012)
    # rope out through the fairlead to a forged hook clipped to the bull bar
    rope = [wc + V((0.0, -0.06, 0.06)), V((0, -3.32, 0.74)), V((0, -3.37, 0.75)), V((0, -3.40, 0.80))]
    mk('Winch_Line', tube_vf(rope, 0.0055, 8), 'Rope', 'Equipment', sharp=60)
    hk = [V((0, -3.40, 0.80)), V((0, -3.41, 0.84)), V((0, -3.40, 0.90)), V((0, -3.37, 0.94)), V((0, -3.34, 0.92)),
          V((0, -3.335, 0.89))]
    mk('Winch_Hook', merge_vf(sweep_vf(hk, [(-0.010, -0.014), (0.010, -0.014), (0.010, 0.014), (-0.010, 0.014)]),
                              cyl_vf(V((0, -3.40, 0.80)), 0.018, 0.02, 'X', 10)), 'SafetyRed', 'Equipment')
    # ---- tow tabs + red D-ring shackles
    for s in (1, -1):
        tab = [(s * 0.80 - 0.015, -3.30, 0.64), (s * 0.80 - 0.015, -3.40, 0.68), (s * 0.80 - 0.015, -3.40, 0.78),
               (s * 0.80 - 0.015, -3.30, 0.82)]
        mk('TowTab_F' + ('L' if s > 0 else 'R'), prism(tab, (0.03, 0, 0)), 'Coating', 'Equipment', bev=(0.004, 1, 30))
        bow, pin = d_ring(V((s * 0.80, -3.37, 0.73)), (0, -1, -0.35))
        mk('Shackle_F' + ('L' if s > 0 else 'R'), bow, 'SafetyRed', 'Equipment', sharp=60)
        mk('ShacklePin_F' + ('L' if s > 0 else 'R'), pin, 'Hardware', 'Equipment')
    # ---- grille guard / bull bar (tubular, bolted to bumper and to the nose)
    gb = []
    R = 0.034
    for s in (1, -1):
        up = [V((s * 0.66, -3.20, 0.93)), V((s * 0.66, -3.17, 1.20)), V((s * 0.66, -3.12, 1.47))]
        gb.append(tube_vf(up, R, 12))
        hoop = [V((s * 0.66, -3.12, 1.47)), V((s * 0.90, -3.12, 1.48)), V((s * 1.08, -3.11, 1.45)),
                V((s * 1.10, -3.13, 1.20)), V((s * 1.10, -3.17, 0.93))]
        gb.append(tube_vf(hoop, R * 0.85, 12))
        for xg in (0.81, 0.95):
            gb.append(tube_vf([V((s * xg, -3.15, 1.12)), V((s * xg, -3.12, 1.46))], 0.012, 8))
        gb.append(tube_vf([V((s * 0.66, -3.17, 1.13)), V((s * 1.10, -3.15, 1.13))], 0.015, 8))
        # brackets to the nose
        gb.append(box_arm(V((s * 0.66, -3.12, 1.45)), V((s * 0.66, -2.995, 1.43)), 0.05, 0.04))
        gb.append(box_arm(V((s * 1.09, -3.11, 1.43)), V((s * 1.05, -2.995, 1.43)), 0.04, 0.035))
        gb.append(box_vf((s * 0.66, -3.20, 0.94), (0.10, 0.10, 0.015)))
        gb.append(box_vf((s * 1.10, -3.17, 0.935), (0.08, 0.08, 0.015)))
    gb.append(tube_vf([V((-0.66, -3.12, 1.47)), V((0.66, -3.12, 1.47))], R, 12))
    for xc in (-0.22, 0.22):
        gb.append(tube_vf([V((xc, -3.19, 0.94)), V((xc, -3.13, 1.46))], 0.016, 8))
    mk('GrilleGuard', merge_vf(*gb), 'Coating', 'Equipment', sharp=40)
    # ---- front skid plate (bumper -> engine skid)
    sk = [(-1.00, -3.18, 0.505), (1.00, -3.18, 0.505), (1.00, -2.86, 0.545), (-1.00, -2.86, 0.545)]
    o = mk('Skid_Front', prism(sk, (0, 0, -0.02)), 'Coating', 'Equipment', bev=(0.005, 1, 30))
    bolts('Skid_Front_Bolts', pts_poly([V(p) - V((0, 0, 0.02)) for p in sk], 0.22, 0.035), V((0, 0, -1)), o, r=0.013)

    # ======================================================== ARMOURED GRILLE
    gf_o = [(x, -3.000, z) for (x, z) in rect2(1.36, 0.58, 0, 1.15)]
    gf_i = [(x, -3.000, z) for (x, z) in rect2(1.24, 0.46, 0, 1.15)]
    o = mk('Grille_Surround', ring_prism(gf_o, gf_i, (0, -0.035, 0)), 'ArmorPaint', 'Armor', bev=(0.006, 2, 30))
    bolts('Grille_Surround_Bolts', pts_poly([V((x, -3.035, z)) for (x, z) in rect2(1.30, 0.52, 0, 1.15)], 0.13, 0.0),
          V((0, -1, 0)), o, r=0.010)
    slats = []
    n = 11
    for k in range(n):
        x = -0.56 + 1.12 * k / (n - 1)
        prof = [(-0.016, -0.06), (0.016, -0.06), (0.016, 0.06), (-0.016, 0.06)]
        rot = Matrix.Rotation(radians(18), 4, 'Z')
        pts = []
        for (dx, dy) in prof:
            q = rot @ V((dx, dy, 0))
            pts.append(V((x + q.x, -2.95 + q.y, 0.93)))
        slats.append(prism(pts, (0, 0, 0.44)))
    for z in (1.02, 1.28):
        slats.append(box_vf((0, -2.95, z), (1.22, 0.10, 0.025)))
    mk('Grille_Slats', merge_vf(*slats), 'PaintDark', 'Armor', bev=(0.004, 1, 30))
    mk('Grille_Mesh', box_vf((0, -2.86, 1.15), (1.24, 0.01, 0.46)), 'Mesh', 'Armor')

    # ======================================================== REAR BUMPER
    rmid = [(2.99, 0.52), (3.16, 0.52), (3.24, 0.60), (3.24, 0.76), (3.19, 0.80), (2.99, 0.80)]
    rend = [(2.99, 0.55), (3.12, 0.55), (3.16, 0.62), (3.16, 0.75), (3.12, 0.79), (2.99, 0.79)]
    rb = mk('Bumper_Rear', bumper_vf(rmid, rend, 1.08, 1.30), 'Coating', 'Equipment')
    cuts = [cutter('_tl', box_between((s * 0.88, 3.10, 0.60), (s * 1.18, 3.40, 0.74))) for s in (1, -1)]
    boolean(rb, cuts)
    clear_scratch()
    bevel(rb, 0.008, 2, 30)
    pads = []
    for s in (1, -1):
        for k in range(8):
            pads.append(box_vf((s * (0.14 + 0.045 * k), 3.10, 0.805), (0.022, 0.20, 0.012)))
    mk('Bumper_Rear_Tread', merge_vf(*pads), 'Hardware', 'Equipment')
    bolts('Bumper_Rear_Bolts', [V((x, 3.242, z)) for x in (-0.62, -0.30, 0.30, 0.62) for z in (0.62, 0.72)],
          V((0, 1, 0)), rb, r=0.014, h=0.010, washer=True)
    # pintle hitch
    ph = [box_vf((0, 3.27, 0.66), (0.24, 0.06, 0.20)), box_vf((0, 3.33, 0.66), (0.10, 0.08, 0.12))]
    hook = [V((0, 3.37, 0.66)), V((0, 3.42, 0.62)), V((0, 3.47, 0.64)), V((0, 3.48, 0.70)), V((0, 3.45, 0.74))]
    ph.append(sweep_vf(hook, [(-0.02, -0.02), (0.02, -0.02), (0.02, 0.02), (-0.02, 0.02)]))
    mk('Pintle_Hitch', merge_vf(*ph), 'Gunmetal', 'Equipment', bev=(0.004, 1, 30))
    latch = [V((0, 3.38, 0.70)), V((0, 3.43, 0.745))]
    mk('Pintle_Latch', merge_vf(tube_vf(latch, 0.012, 8), cyl_vf(V((0.03, 3.38, 0.70)), 0.015, 0.02, 'X', 8)),
       'SafetyRed', 'Equipment')
    bolts('Pintle_Bolts', [V((x, 3.30, z)) for x in (-0.09, 0.09) for z in (0.59, 0.73)], V((0, 1, 0)), None, r=0.012)
    for s in (1, -1):
        sfx = 'L' if s > 0 else 'R'
        tab = [(s * 0.60 - 0.015, 3.24, 0.58), (s * 0.60 - 0.015, 3.33, 0.62), (s * 0.60 - 0.015, 3.33, 0.70),
               (s * 0.60 - 0.015, 3.24, 0.74)]
        mk('TowTab_R' + sfx, prism(tab, (0.03, 0, 0)), 'Coating', 'Equipment', bev=(0.004, 1, 30))
        bow, pin = d_ring(V((s * 0.60, 3.30, 0.66)), (0, 1, -0.35))
        mk('Shackle_R' + sfx, bow, 'SafetyRed', 'Equipment', sharp=60)
        mk('ShacklePin_R' + sfx, pin, 'Hardware', 'Equipment')
        # safety-chain loops
        loop = [V((s * 0.15, 3.235, 0.625)), V((s * 0.15, 3.27, 0.595)), V((s * 0.21, 3.27, 0.595)), V((s * 0.21, 3.235, 0.625))]
        mk('ChainLoop_R' + sfx, tube_vf(loop, 0.010, 8), 'Hardware', 'Equipment')
    # NATO trailer socket
    mk('TrailerSocket', merge_vf(cyl_vf(V((0.30, 3.25, 0.57)), 0.035, 0.05, 'Y', 16),
                                 cyl_vf(V((0.30, 3.28, 0.57)), 0.040, 0.012, 'Y', 16)), 'Gunmetal', 'Equipment')
    # rear skid under the bumper
    sk = [(-0.98, 2.86, 0.62), (0.98, 2.86, 0.62), (0.98, 3.16, 0.525), (-0.98, 3.16, 0.525)]
    o = mk('Skid_RearBumper', prism(sk, (0, 0, -0.02)), 'Coating', 'Equipment', bev=(0.005, 1, 30))
