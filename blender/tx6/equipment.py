"""TX-6 Bastion - side equipment lockers (with contents + slide-out drone tray), rear equipment system
(swing-out spare carrier, ladder, jerry can), snorkel, mirrors, pioneer tools."""
from tx6.lib import *
from tx6 import wheels as W
from tx6.armor import box_arm


def jerry_can(c, axis_w=(1, 0, 0), axis_d=(0, 1, 0)):
    """NATO 20 L jerry can, 0.345 (w) x 0.165 (d) x 0.47 (h), standing on its base at c."""
    c = V(c)
    uw, ud = V(axis_w).normalized(), V(axis_d).normalized()
    uz = uw.cross(ud)
    if uz.z < 0:
        uz = -uz
    m = Matrix((uw, ud, uz)).transposed().to_4x4()
    m.translation = c
    parts = [box_vf((0, 0, 0.215), (0.345, 0.165, 0.43))]
    # X-pressings on both faces
    for sd in (1, -1):
        for a in (1, -1):
            p0 = V((-0.14, sd * 0.084, 0.04 + (0 if a > 0 else 0.35)))
            p1 = V((0.14, sd * 0.084, 0.39 - (0 if a > 0 else 0.35)))
            parts.append(sweep_vf([p0, p1], [(-0.004, -0.012), (0.004, -0.012), (0.004, 0.012), (-0.004, 0.012)]))
    # three-bar handle + spout
    for x in (-0.10, 0.0, 0.10):
        parts.append(box_vf((x, 0, 0.455), (0.022, 0.03, 0.05)))
    parts.append(box_vf((0, 0, 0.475), (0.24, 0.03, 0.012)))
    parts.append(cyl_vf((0.13, 0, 0.45), 0.024, 0.05, 'Z', 12))
    return xform_vf(merge_vf(*parts), m)


def ammo_can(c, ux=(1, 0, 0)):
    c = V(c)
    ux = V(ux).normalized()
    uy = V((0, 0, 1)).cross(ux)
    m = Matrix((ux, uy, V((0, 0, 1)))).transposed().to_4x4()
    m.translation = c
    parts = [box_vf((0, 0, 0.09), (0.28, 0.11, 0.18)), box_vf((0, 0, 0.185), (0.285, 0.115, 0.012)),
             box_vf((0.13, 0, 0.16), (0.03, 0.12, 0.05))]
    parts.append(sweep_vf([V((-0.06, 0, 0.19)), V((-0.06, 0, 0.21)), V((0.06, 0, 0.21)), V((0.06, 0, 0.19))],
                          [(-0.004, -0.006), (0.004, -0.006), (0.004, 0.006), (-0.004, 0.006)]))
    return xform_vf(merge_vf(*parts), m)


def hard_case(c, size):
    c, (w, d, h) = V(c), size
    parts = [box_vf(c + V((0, 0, h / 2)), (w, d, h)), box_vf(c + V((0, 0, h * 0.62)), (w + 0.012, d + 0.012, 0.012))]
    for dx in (-w * 0.3, w * 0.3):
        parts.append(box_vf(c + V((dx, -d / 2 - 0.006, h * 0.62)), (0.04, 0.014, 0.05)))
    parts.append(box_vf(c + V((0, -d / 2 - 0.01, h * 0.8)), (0.12, 0.016, 0.022)))
    return merge_vf(*parts)


def drone(c):
    c = V(c)
    body = [box_vf(c + V((0, 0, 0.045)), (0.15, 0.15, 0.05)),
            orient(lathe_vf([(0, 0.0), (0.065, 0.0), (0.055, 0.025), (0.03, 0.04), (0, 0.045)], 16), c + V((0, 0, 0.07)), 'Z')]
    arms, motors, props = [], [], []
    for k in range(4):
        a = pi / 4 + k * pi / 2
        tip = c + V((0.14 * cos(a), 0.14 * sin(a), 0.055))
        arms.append(cyl_between(c + V((0, 0, 0.055)), tip, 0.011, 8))
        motors.append(cyl_vf(tip + V((0, 0, 0.018)), 0.021, 0.03, 'Z', 12))
        pa = a + pi / 2
        props.append(xform_vf(box_vf((0, 0, 0), (0.16, 0.018, 0.004)),
                              Matrix.Translation(tip + V((0, 0, 0.034))) @ Matrix.Rotation(pa, 4, 'Z')))
    skids = [box_vf(c + V((0, sd * 0.055, 0.006)), (0.18, 0.012, 0.012)) for sd in (1, -1)]
    for sd in (1, -1):
        for dx in (-0.05, 0.05):
            skids.append(cyl_between(c + V((dx, sd * 0.055, 0.006)), c + V((dx, sd * 0.04, 0.025)), 0.005, 6))
    cam = orient(lathe_vf([(0, -0.02)] + [(0.02 * sin(pi * k / 6), -0.02 * cos(pi * k / 6)) for k in range(1, 6)] +
                          [(0, 0.02)], 10), c + V((0.06, 0, 0.012)), 'Z')
    return merge_vf(*body, *arms, *motors), merge_vf(*props), merge_vf(*skids), cam


def build_lockers():
    for s, sfx in ((1, 'L'), (-1, 'R')):
        xin = 0.72
        xo = xs(1.70) - 0.008
        # L-shaped compartment: deep lower bay, shallow upper bay (the missile bay sits above/inboard of it)
        xu = 0.957
        comp = [box_between((s * xin, 1.105, 1.685), (s * xo, 2.495, 1.70)),                         # floor
                box_between((s * xin, 1.105, 1.985), (s * xu, 2.495, 2.0)),                          # step / shelf
                box_between((s * xu, 1.105, 2.30), (s * (xs(2.30) - 0.005), 2.495, 2.315)),          # roof
                box_between((s * (xin - 0.015), 1.105, 1.685), (s * xin, 2.495, 2.0)),               # lower back wall
                box_between((s * xu, 1.105, 1.985), (s * (xu + 0.015), 2.495, 2.315)),               # upper back wall
                box_between((s * xin, 1.09, 1.685), (s * xo, 1.105, 2.315)),
                box_between((s * xin, 2.495, 1.685), (s * xo, 2.51, 2.315))]
        mk('Locker_Box_' + sfx, merge_vf(*comp), 'PaintDark', 'Equipment')
        mk('Locker_Light_' + sfx, box_between((s * 1.00, 1.50, 2.29), (s * 1.04, 2.10, 2.30)), 'LED', 'Equipment')
        door = bpy.data.objects['Locker_Door_' + sfx]
        # gas struts + latch handles on the door, hinge knuckles on the roof rail
        kn = []
        for yy in (1.25, 1.80, 2.35):
            p = V((s * (xs(2.30) + 0.012), yy, 2.30))
            kn.append(cyl_vf(p, 0.016, 0.12, 'Y', 10))
        mk('Locker_Hinges_' + sfx, merge_vf(*kn), 'Hardware', 'Equipment')
        n = side_n(2.0, s)
        lat = []
        for yy in (1.35, 2.25):
            p = side_pt(yy, 1.76, s, 0.0)
            lat.append(orient(box_vf((0, 0, 0.012), (0.10, 0.035, 0.024)), p, n, 0))
            lat.append(orient(cyl_vf((0, 0, 0.03), 0.009, 0.02, 'Z', 8), p + V((0, 0, 0)), n))
        mk('Locker_Latches_' + sfx, merge_vf(*lat), 'Hardware', 'Equipment', door)
        # pressed stiffener ribs + label on the locker door
        ribs = []
        for zr in (1.90, 2.12):
            q = [side_pt(y, z, s, 0.0) for (y, z) in ((1.20, zr - 0.02), (2.40, zr - 0.02), (2.40, zr + 0.02), (1.20, zr + 0.02))]
            ribs.append(prism(q, n * 0.012))
        for yr in (1.55, 2.05):
            q = [side_pt(y, z, s, 0.0) for (y, z) in ((yr - 0.02, 1.80), (yr + 0.02, 1.80), (yr + 0.02, 2.22), (yr - 0.02, 2.22))]
            ribs.append(prism(q, n * 0.008))
        mk('Locker_Ribs_' + sfx, merge_vf(*ribs), 'ArmorPaint', 'Equipment', door, bev=(0.004, 1, 30))
        from tx6.details import stencil
        up = V((0, 0, 1)).cross(n).cross(n) * -1
        stencil('Stencil_Locker' + sfx, 'EQUIP BAY 2' if s > 0 else 'EQUIP BAY 1', 0.04, side_pt(1.80, 2.245, s, 0.0015), n,
                up=up, parent=door)
        if s > 0:
            # ---- left: recon drone on a slide-out tray, hard cases, extinguisher
            tray = empty('Locker_Tray_L', (0.96, 1.46, 1.70), 'Equipment', size=0.15)
            anim(tray, 'drone tray: slide +0.42 along X (out of the locker)')
            tp = [box_between((0.76, 1.20, 1.700), (1.16, 1.72, 1.715)),
                  box_between((0.76, 1.20, 1.715), (1.16, 1.215, 1.735)),
                  box_between((0.76, 1.705, 1.715), (1.16, 1.72, 1.735)),
                  box_between((1.145, 1.20, 1.715), (1.16, 1.72, 1.75))]
            mk('Locker_Tray_L_Plate', merge_vf(*tp), 'Hardware', 'Equipment', tray)
            b, p, sk, cam = drone(V((0.96, 1.46, 1.715)))
            mk('Drone_Body', b, 'PaintDark', 'Equipment', tray, sharp=40)
            mk('Drone_Props', p, 'Plastic', 'Equipment', tray)
            mk('Drone_Skids', sk, 'Hardware', 'Equipment', tray)
            mk('Drone_Camera', cam, 'GlassDark', 'Equipment', tray)
            cases = merge_vf(hard_case(V((0.95, 2.03, 1.70)), (0.34, 0.46, 0.16)),
                             hard_case(V((0.95, 2.03, 1.86)), (0.30, 0.40, 0.115)))
            mk('Locker_Cases_L', cases, 'PaintDark', 'Equipment', bev=(0.006, 1, 30))
            ext = [cyl_vf(V((1.06, 2.42, 1.895)), 0.045, 0.37, 'Z', 16),
                   orient(lathe_vf([(0.045, 0), (0.03, 0.03), (0.012, 0.04), (0, 0.04)], 16), (1.06, 2.42, 2.08), 'Z')]
            mk('Locker_Extinguisher_L', merge_vf(*ext), 'ExtRed', 'Equipment')
            mk('Locker_ExtinguisherValve_L', merge_vf(cyl_vf(V((1.06, 2.42, 2.135)), 0.012, 0.03, 'Z', 8),
                                                       box_between((1.05, 2.38, 2.14), (1.07, 2.45, 2.15))),
               'Gunmetal', 'Equipment')
        else:
            # ---- right: ammunition, medical, comms, recovery strap
            mk('Locker_Shelf_R', box_between((-1.19, 1.105, 1.985), (-0.72, 2.495, 2.0)), 'Hardware', 'Equipment')
            cans = merge_vf(*[ammo_can(V((-0.95, 1.18 + 0.12 * k, 1.70)), (1, 0, 0)) for k in range(4)])
            mk('Locker_AmmoCans_R', cans, 'Paint', 'Equipment', bev=(0.003, 1, 30))
            med = merge_vf(box_vf((-0.92, 1.96, 1.81), (0.30, 0.38, 0.22)))
            mk('Locker_MedBag_R', med, 'Canvas', 'Equipment', bev=(0.03, 3, 30))
            mk('Locker_MedCross_R', merge_vf(box_vf((-1.072, 1.96, 1.86), (0.006, 0.10, 0.03)),
                                             box_vf((-1.072, 1.96, 1.86), (0.006, 0.03, 0.10))), 'SafetyRed', 'Equipment')
            strap = orient(lathe_vf([(0.05, -0.05), (0.11, -0.05), (0.11, 0.05), (0.05, 0.05), (0.05, -0.05)], 20, False,
                                    False), (-0.90, 2.36, 1.75), 'Z')
            mk('Locker_TowStrap_R', strap, 'Hazard', 'Equipment', bev=(0.01, 2, 30))
            radio = [box_vf((-1.065, 1.45, 2.09), (0.17, 0.42, 0.18)), box_vf((-1.065, 1.45, 2.185), (0.175, 0.43, 0.012))]
            mk('Locker_CommsCase_R', merge_vf(*radio), 'PaintDark', 'Equipment', bev=(0.006, 1, 30))
            mk('Locker_CommsAntenna_R', cyl_between(V((-1.04, 1.30, 2.19)), V((-1.04, 1.30, 2.28)), 0.006, 6), 'Plastic',
               'Equipment')
            bats = merge_vf(*[box_vf((-1.065, 1.93 + 0.13 * k, 2.06), (0.16, 0.11, 0.12)) for k in range(4)])
            mk('Locker_Batteries_R', bats, 'Plastic', 'Equipment', bev=(0.004, 1, 30))


def build_rear():
    # ---------------- swing-out spare wheel carrier (right rear corner)
    piv = V((-1.15, 3.035, 1.40))
    car = empty('Spare_Carrier', piv, 'Equipment', size=0.25)
    anim(car, 'spare carrier: rotate +95 deg about Z (swings out before the rear door opens)')
    fr = [cyl_between(V((-1.15, 3.035, 0.88)), V((-1.15, 3.035, 1.96)), 0.03, 12),
          box_arm(V((-1.15, 3.04, 1.86)), V((-0.10, 3.06, 1.86)), 0.05, 0.05),
          box_arm(V((-1.15, 3.04, 0.96)), V((-0.10, 3.06, 0.96)), 0.05, 0.05),
          box_arm(V((-0.10, 3.06, 0.96)), V((-0.10, 3.06, 1.86)), 0.05, 0.05),
          box_arm(V((-1.10, 3.05, 1.00)), V((-0.66, 3.06, 1.42)), 0.04, 0.04),
          box_arm(V((-0.14, 3.06, 1.82)), V((-0.58, 3.06, 1.48)), 0.04, 0.04),
          cyl_vf(V((-0.62, 3.075, 1.45)), 0.12, 0.03, 'Y', 20)]
    mk('Spare_CarrierFrame', merge_vf(*fr), 'Coating', 'Equipment', car, bev=(0.004, 1, 30))
    kn = []
    for z in (1.0, 1.80):
        kn.append(cyl_vf(V((-1.15, 3.035, z)), 0.042, 0.10, 'Z', 12))
        kn.append(box_between((-1.20, 2.99, z - 0.06), (-1.09, 3.01, z + 0.06)))
    mk('Spare_CarrierHinges', merge_vf(*kn), 'Hardware', 'Equipment')
    mk('Spare_Latch', merge_vf(box_between((-0.08, 3.00, 1.38), (-0.02, 3.09, 1.46)),
                               cyl_between(V((-0.05, 3.09, 1.42)), V((-0.05, 3.16, 1.42)), 0.012, 8)), 'Hardware',
       'Equipment', car)
    C_ = V((-0.62, 3.305, 1.45))
    m = Matrix.Translation(C_) @ Matrix.Rotation(radians(-90), 4, 'X')
    tire = W.tire_local()
    rim = W.rim_local()
    mk('Spare_Tire', xform_vf(tire, m), 'Tire', 'Equipment', car, sharp=40)
    mk('Spare_Rim', xform_vf(rim['Rim'], m), 'Rim', 'Equipment', car, sharp=40, bev=(0.003, 1, 40))
    mk('Spare_Beadlock', xform_vf(rim['Beadlock'], m), 'Hardware', 'Equipment', car, sharp=40)
    mk('Spare_Nuts', xform_vf(rim['Nuts'], m), 'Steel', 'Equipment', car, sharp=40)
    # ---------------- rear door: ladder, jerry can rack, hinges, handles
    rd = bpy.data.objects['Door_Rear']
    lad = []
    for x in (0.66, 0.80):
        lad.append(box_between((x - 0.012, 3.045, 0.86), (x + 0.012, 3.07, 2.05)))
        for z in (0.92, 2.035):
            lad.append(box_between((x - 0.01, 3.0, z - 0.02), (x + 0.01, 3.05, z + 0.02)))
    for k in range(5):
        z = 1.05 + 0.23 * k
        lad.append(cyl_between(V((0.65, 3.058, z)), V((0.81, 3.058, z)), 0.015, 10))
    mk('Rear_Ladder', merge_vf(*lad), 'Coating', 'Equipment', rd, bev=(0.003, 1, 30))
    rack = [box_between((0.12, 3.0, 0.88), (0.50, 3.20, 0.90)),
            box_between((0.12, 3.18, 0.90), (0.135, 3.20, 1.30)), box_between((0.485, 3.18, 0.90), (0.50, 3.20, 1.30)),
            box_between((0.12, 3.188, 1.20), (0.50, 3.20, 1.22))]
    mk('Rear_CanRack', merge_vf(*rack), 'Coating', 'Equipment', rd, bev=(0.002, 1, 30))
    mk('Rear_JerryCan', jerry_can(V((0.31, 3.10, 0.90))), 'PaintDark', 'Equipment', rd, bev=(0.006, 1, 30))
    hg = []
    for z in (1.05, 1.45, 1.85):
        hg.append(cyl_vf(V((0.845, 3.025, z)), 0.022, 0.12, 'Z', 12))
        hg.append(box_between((0.70, 3.0, z - 0.04), (0.84, 3.018, z + 0.04)))
    mk('Rear_DoorHinges', merge_vf(*hg), 'Hardware', 'Equipment', rd)
    mk('Rear_DoorBodyHinges', merge_vf(*[box_between((0.85, 2.995, z - 0.05), (1.02, 3.012, z + 0.05))
                                          for z in (1.05, 1.45, 1.85)]), 'Hardware', 'Equipment')
    h = [box_between((-0.27, 3.0, 1.30), (-0.21, 3.02, 1.50)),
         cyl_between(V((-0.24, 3.02, 1.33)), V((-0.24, 3.07, 1.33)), 0.012, 8),
         cyl_between(V((-0.24, 3.02, 1.47)), V((-0.24, 3.07, 1.47)), 0.012, 8),
         cyl_between(V((-0.24, 3.07, 1.32)), V((-0.24, 3.07, 1.48)), 0.013, 8)]
    mk('Rear_DoorHandle', merge_vf(*h), 'Hardware', 'Equipment', rd)
    # rear door armour bezel around the window + upper applique
    o = [(x, 3.0, z) for (x, z) in offset2([(0.00, 1.62), (0.60, 1.62), (0.60, 1.96), (0.00, 1.96)], 0.055)]
    i = [(x, 3.0, z) for (x, z) in [(0.00, 1.62), (0.60, 1.62), (0.60, 1.96), (0.00, 1.96)]]
    mk('Rear_WinFrame', ring_prism(o, i, (0, 0.022, 0)), 'ArmorPaint', 'Armor', rd, bev=(0.004, 2, 30))
    win = [(0.00, 1.62), (0.60, 1.62), (0.60, 1.96), (0.00, 1.96)]
    bolts('Rear_WinFrame_Bolts', pts_poly([V((x, 3.022, z)) for (x, z) in offset2(win, 0.03)], 0.11, 0.0), V((0, 1, 0)),
          rd, r=0.009)
    # roof grab bar above the ladder
    mk('Rear_RoofGrab', tube_vf([V((0.66, 2.93, 2.44)), V((0.66, 2.99, 2.50)), V((0.80, 2.99, 2.50)), V((0.80, 2.93, 2.44))],
                               0.014, 8), 'Coating', 'Equipment')


def build_snorkel():
    s = -1
    pts = [V((s * 1.08, -1.45, 1.50)), V((s * 1.10, -1.44, 1.63)), V((s * 1.12, -1.36, 1.74)), V((s * 1.115, -1.215, 1.80)),
           V((s * 1.085, -1.025, 2.20)), V((s * 1.06, -0.90, 2.50)), V((s * 1.06, -0.88, 2.58))]
    path = catmull_pts(pts, 6)
    shape = rrect2(0.12, 0.10, 0.035, 3)
    mk('Snorkel_Pipe', sweep_vf(path, shape), 'Coating', 'Equipment', sharp=50)
    top = V((s * 1.06, -0.88, 2.60))
    head = [box_between(top + V((-0.08, -0.13, -0.05)), top + V((0.08, 0.06, 0.08))),
            box_between(top + V((-0.075, -0.15, -0.045)), top + V((0.075, -0.13, 0.075)))]
    mk('Snorkel_Head', merge_vf(*head), 'Coating', 'Equipment', bev=(0.012, 2, 30))
    mk('Snorkel_Mesh', box_between(top + V((-0.065, -0.152, -0.035)), top + V((0.065, -0.148, 0.065))), 'Mesh',
       'Equipment')
    br = []
    for t in (0.35, 0.72):
        p = path[int(t * (len(path) - 1))]
        br.append(box_between(p + V((-0.08, -0.02, -0.025)), p + V((0.08, 0.02, 0.025))))
    mk('Snorkel_Brackets', merge_vf(*br), 'Hardware', 'Equipment')


def catmull_pts(pts, n):
    from tx6.roof import catmull
    return catmull(pts, n)


def build_mirrors():
    for s, sfx in ((1, 'L'), (-1, 'R')):
        base = V((s * 1.18, -1.58, zh(-1.58) - 0.01))
        elbow = V((s * 1.38, -1.52, 1.86))
        hc = V((s * 1.47, -1.46, 2.02))
        arm = merge_vf(tube_vf([base + V((0, 0, 0.02)), elbow, hc + V((-s * 0.10, 0, -0.10))], 0.018, 10),
                       tube_vf([base + V((0, -0.08, 0.02)), elbow + V((0, -0.02, -0.06)), hc + V((-s * 0.10, 0, -0.17))],
                               0.014, 10),
                       box_between(base + V((-0.05, -0.12, -0.01)), base + V((0.05, 0.04, 0.025))))
        mk('Mirror_Arm' + sfx, arm, 'Coating', 'Equipment', sharp=50)
        head = [box_between(hc + V((-0.10, -0.035, -0.20)), hc + V((0.10, 0.035, 0.16)))]
        mk('Mirror_Head' + sfx, merge_vf(*head), 'Coating', 'Equipment', bev=(0.015, 2, 30))
        mk('Mirror_Glass' + sfx, box_between(hc + V((-0.088, 0.035, -0.19)), hc + V((0.088, 0.040, 0.15))), 'Steel',
           'Equipment')
        mk('Mirror_Camera' + sfx, merge_vf(box_between(hc + V((-0.025, -0.03, -0.25)), hc + V((0.025, 0.03, -0.20))),
                                           cyl_vf(hc + V((0, -0.035, -0.225)), 0.012, 0.012, 'Y', 10)), 'Housing',
           'Equipment')


def build_tools():
    # quarter-rail pioneer tools
    s = 1
    x = s * 1.29
    sh = [cyl_between(V((x, 1.20, 1.525)), V((x, 2.18, 1.525)), 0.018, 10)]
    mk('Tool_ShovelHandle', merge_vf(*sh), 'Wood', 'Equipment')
    blade = [box_between((x - 0.006, 2.18, 1.43), (x + 0.006, 2.48, 1.62)),
             cyl_between(V((x, 2.15, 1.525)), V((x, 2.22, 1.525)), 0.024, 10),
             box_between((x - 0.01, 1.12, 1.475), (x + 0.01, 1.20, 1.575))]
    mk('Tool_ShovelBlade', merge_vf(*blade), 'PaintDark', 'Equipment', bev=(0.003, 1, 30))
    cl = []
    for yy in (1.45, 2.02):
        cl.append(box_between((s * 1.245, yy - 0.025, 1.49), (s * 1.315, yy + 0.025, 1.505)))
        cl.append(box_between((s * 1.245, yy - 0.025, 1.545), (s * 1.315, yy + 0.025, 1.56)))
        cl.append(box_between((s * 1.305, yy - 0.025, 1.49), (s * 1.315, yy + 0.025, 1.56)))
    mk('Tool_ClampsL', merge_vf(*cl), 'Hardware', 'Equipment')
    s = -1
    x = s * 1.29
    mk('Tool_AxeHandle', cyl_between(V((x, 1.25, 1.525)), V((x, 2.05, 1.525)), 0.018, 10), 'Wood', 'Equipment')
    mk('Tool_AxeHead', merge_vf(box_between((x - 0.012, 2.02, 1.48), (x + 0.012, 2.10, 1.60)),
                                prism([(x - 0.004, 2.02, 1.48), (x - 0.004, 2.10, 1.48), (x - 0.004, 2.12, 1.44),
                                       (x - 0.004, 2.00, 1.44)], (0.008, 0, 0))), 'PaintDark', 'Equipment')
    mk('Tool_MattockHandle', cyl_between(V((x, 1.95, 1.565)), V((x, 2.75, 1.565)), 0.018, 10), 'Wood', 'Equipment')
    mk('Tool_MattockHead', box_between((x - 0.014, 1.90, 1.47), (x + 0.014, 1.97, 1.66)), 'PaintDark', 'Equipment')
    cl = []
    for yy in (1.55, 2.40):
        cl.append(box_between((s * 1.245, yy - 0.025, 1.49), (s * 1.315, yy + 0.025, 1.505)))
        cl.append(box_between((s * 1.245, yy - 0.025, 1.585), (s * 1.315, yy + 0.025, 1.60)))
        cl.append(box_between((s * 1.305, yy - 0.025, 1.49), (s * 1.315, yy + 0.025, 1.60)))
    mk('Tool_ClampsR', merge_vf(*cl), 'Hardware', 'Equipment')


def build():
    build_lockers()
    build_rear()
    build_snorkel()
    build_mirrors()
    build_tools()
