"""TX-6 Bastion - tertiary detail pass: handles, hinges, hood latches, wipers, antennas, sensors, cameras,
lifting eyes, grab handles, exhaust, fuel filler, NATO slave socket, mud flaps, stencils."""
from tx6.lib import *
from tx6 import body as B


def ob(n):
    return bpy.data.objects[n]


def stencil(name, text, size, c, normal, up=(0, 0, 1), parent=None):
    vv, ff = text_vf(text, size, 0.0012)
    n = V(normal).normalized()
    upv = V(up).normalized()
    right = upv.cross(n)
    m = Matrix((right, upv, n)).transposed().to_4x4()
    m.translation = V(c)
    return mk(name, xform_vf((vv, ff), m), 'Stencil', 'Details', parent, smooth=False)


def lathe_and_orient(p, d):
    return orient(lathe_vf([(0.040, -0.03), (0.050, -0.03), (0.056, 0.04), (0.050, 0.045), (0.046, 0.0), (0.040, 0.0),
                            (0.040, -0.03)], 16, False, False), p, d)


def build():
    for s, sfx in ((1, 'L'), (-1, 'R')):
        xa = X_SIDE + 0.010 + 0.022           # outer face of the door applique (layer 1)
        # ------------------------------------------------ door pull handles + locks
        for door, y in (('Door_F', -0.185), ('Door_R', 0.885)):
            d = ob(door + sfx)
            h = [box_between((s * xa, y - 0.035, 0.93), (s * (xa + 0.008), y + 0.035, 1.12))]
            for z in (0.96, 1.09):
                h.append(cyl_between(V((s * xa, y, z)), V((s * (xa + 0.045), y, z)), 0.011, 8))
            h.append(cyl_between(V((s * (xa + 0.045), y, 0.95)), V((s * (xa + 0.045), y, 1.10)), 0.014, 10))
            h.append(cyl_vf(V((s * (xa + 0.012), y, 1.15)), 0.012, 0.012, 'X', 10))
            mk('Handle_%s%s' % (door[-1], sfx), merge_vf(*h), 'Hardware', 'Details', d)
        # ------------------------------------------------ heavy external door hinges
        for door, yf in (('Door_F', -1.06), ('Door_R', -0.02)):
            d = ob(door + sfx)
            kn, leaf_b, leaf_d = [], [], []
            for z in (1.08, 1.48):
                kn.append(cyl_vf(V((s * 1.272, yf, z)), 0.024, 0.13, 'Z', 12))
                kn.append(cyl_vf(V((s * 1.272, yf, z)), 0.010, 0.17, 'Z', 8))
                leaf_d.append(box_between((s * 1.222, yf + 0.004, z - 0.05), (s * 1.27, yf + 0.11, z + 0.05)))
                leaf_b.append(box_between((s * 1.222, yf - 0.10 if door == 'Door_F' else yf - 0.072, z - 0.05),
                                          (s * 1.262, yf - 0.006, z + 0.05)))
            mk('Hinge_%s%s_Knuckles' % (door[-1], sfx), merge_vf(*kn), 'Hardware', 'Details')
            mk('Hinge_%s%s_BodyLeaf' % (door[-1], sfx), merge_vf(*leaf_b), 'Hardware', 'Details')
            mk('Hinge_%s%s_DoorLeaf' % (door[-1], sfx), merge_vf(*leaf_d), 'Hardware', 'Details', d)
            bolts('Hinge_%s%s_Bolts' % (door[-1], sfx),
                  [V((s * 1.271, yf + 0.07, z + dz)) for z in (1.08, 1.48) for dz in (-0.03, 0.03)], V((s, 0, 0)), d,
                  r=0.008)
        # ------------------------------------------------ mud flaps behind every wheel
        for ya, nm in ((Y_AF + 0.86, 'F'), (Y_AR + 0.84, 'R')):
            fl = [box_between((s * 0.95, ya, 0.30), (s * 1.30, ya + 0.012, Z_SILL + 0.01)),
                  box_between((s * 0.95, ya - 0.012, Z_SILL - 0.04), (s * 1.30, ya, Z_SILL + 0.01))]
            mk('MudFlap_%s%s' % (nm, sfx), merge_vf(*fl), 'Rubber', 'Details')
        # ------------------------------------------------ lifting eyes on the roof edge
        for y in (-0.15, 2.30):
            c = V((s * 1.035, y, 2.452))
            n = V((s * (Z_ROOF - Z_RE), 0, (X_RE - X_RT))).normalized()
            path = [c + V((0, -0.035 * cos(pi * k / 8), 0)) + n * (0.012 + 0.04 * sin(pi * k / 8)) for k in range(9)]
            mk('LiftEye_%s%s' % (sfx, 'F' if y < 0 else 'R'), merge_vf(tube_vf(path, 0.011, 8),
                                                                        box_between(c - V((0.02, 0.05, 0.01)),
                                                                                    c + V((0.02, 0.05, 0.012)))),
               'Hardware', 'Details')
        # ------------------------------------------------ roof-rail grab handles above the doors
        for y in (-0.55, 0.45):
            c0 = V((s * 1.07, y - 0.13, 2.43))
            c1 = V((s * 1.07, y + 0.13, 2.43))
            n = V((s, 0, 0.3)).normalized()
            mk('GrabHandle_%s%d' % (sfx, 0 if y < 0 else 1),
               tube_vf([c0, c0 + n * 0.05, c1 + n * 0.05, c1], 0.012, 8), 'Coating', 'Details')
    # ---------------------------------------------------- rubber T-latches on the hood
    lat = []
    cat = []
    hcat = []
    for x in (-0.80, 0.80):
        path = [V((x, -2.78, zh(-2.78) + 0.004)), V((x, -2.885, 1.607)), V((x, -2.955, 1.53)), V((x, -2.992, 1.47)),
                V((x, -3.006, 1.43))]
        lat.append(sweep_vf(path, [(-0.004, -0.022), (0.004, -0.022), (0.004, 0.022), (-0.004, 0.022)]))
        lat.append(box_between((x - 0.035, -3.016, 1.418), (x + 0.035, -3.0, 1.432)))
        cat.append(box_between((x - 0.03, -3.02, 1.40), (x + 0.03, -3.0, 1.425)))
        hcat.append(box_between((x - 0.03, -2.80, zh(-2.80)), (x + 0.03, -2.74, zh(-2.74) + 0.02)))
    mk('HoodLatch_Straps', merge_vf(*lat), 'Rubber', 'Details', sharp=60)
    mk('HoodLatch_Catches', merge_vf(*cat), 'Hardware', 'Details')
    mk('HoodLatch_HoodCatches', merge_vf(*hcat), 'Hardware', 'Details', ob('Hood'))
    # ---------------------------------------------------- windshield wipers (parked on the lower frame)
    n = B.ws_normal()
    wp = []
    for xp, x0, x1 in ((0.47, 0.10, 0.82), (-0.42, -0.80, -0.10)):
        piv = V((xp, y_ws(1.705), 1.705)) + n * 0.035
        blade_z = 1.84
        a0 = V((x0, y_ws(blade_z), blade_z)) + n * 0.014
        a1 = V((x1, y_ws(blade_z), blade_z)) + n * 0.014
        wp.append(cyl_vf(piv, 0.022, 0.04, n, 12))
        mid = (a0 + a1) / 2
        wp.append(sweep_vf([piv, mid + n * 0.01], [(-0.006, -0.011), (0.006, -0.011), (0.006, 0.011), (-0.006, 0.011)]))
        wp.append(sweep_vf([a0, a1], [(-0.008, -0.008), (0.008, -0.008), (0.008, 0.008), (-0.008, 0.008)]))
    mk('Wipers', merge_vf(*wp), 'Housing', 'Details')
    # ---------------------------------------------------- whip antennas on the rear corners (spring bases)
    for s, sfx in ((1, 'L'), (-1, 'R')):
        b = V((s * 0.62, 3.03, 2.22))
        base = [box_between(b + V((-0.04, -0.03, -0.05)), b + V((0.04, 0.03, 0.03))),
                cyl_vf(b + V((0, 0, 0.05)), 0.03, 0.04, 'Z', 12)]
        coil = tube_vf(helix(b + V((0, 0, 0.07)), 0.022, 0.12, 6, 10), 0.006, 6)
        tip = b + V((s * 0.05, 0.22, 1.60))
        whip = cyl_between(b + V((0, 0, 0.19)), tip, 0.006, 6)
        mk('Antenna_Whip' + sfx, merge_vf(*base, coil, whip, cyl_vf(tip, 0.009, 0.02, (tip - b).normalized(), 8)),
           'Plastic', 'Details')
    # roof front: blade antennas, GPS / SATCOM puck, LIDAR puck, 360 cameras
    mk('Antenna_Blades', merge_vf(*[prism([(x - 0.004, -0.50, Z_ROOF), (x - 0.004, -0.40, Z_ROOF), (x - 0.004, -0.43, 2.62),
                                           (x - 0.004, -0.47, 2.62)], (0.008, 0, 0)) for x in (-0.38, 0.38)]),
       'Plastic', 'Details')
    mk('Sensor_GPS', orient(lathe_vf([(0, 0), (0.075, 0), (0.07, 0.02), (0.05, 0.035), (0, 0.04)], 20),
                            (0.58, -0.45, Z_ROOF), 'Z'), 'Plastic', 'Details')
    lid = [cyl_vf(V((-0.55, -0.47, Z_ROOF + 0.03)), 0.06, 0.06, 'Z', 20),
           cyl_vf(V((-0.55, -0.47, Z_ROOF + 0.075)), 0.052, 0.03, 'Z', 20)]
    mk('Sensor_LIDAR', merge_vf(*lid[:1]), 'Housing', 'Details')
    mk('Sensor_LIDARWindow', lid[1], 'GlassDark', 'Details')
    cams = []
    lenses = []
    for c, d in ((V((0.93, -0.74, Z_ROOF + 0.03)), V((0.4, -1, 0))), (V((-0.93, -0.74, Z_ROOF + 0.03)), V((-0.4, -1, 0))),
                 (V((0, -3.13, 1.53)), V((0, -1, 0))), (V((0, 3.0, 2.24)), V((0, 1, -0.4)))):
        cams.append(orient(box_vf((0, 0, 0.0), (0.06, 0.05, 0.055)), c, d))
        lenses.append(cyl_vf(c + d.normalized() * 0.03, 0.014, 0.01, d, 12))
    mk('Cameras', merge_vf(*cams), 'Housing', 'Details', bev=(0.004, 1, 30))
    mk('Camera_Lenses', merge_vf(*lenses), 'GlassDark', 'Details')
    # ---------------------------------------------------- exhaust tip under the rear bumper (+ heat shield)
    ex = [V((0.55, 2.84, 0.60)), V((0.80, 2.84, 0.59)), V((0.98, 2.84, 0.565)), V((1.06, 2.84, 0.535))]
    from tx6.roof import catmull
    pth = catmull(ex, 6)
    mk('Exhaust_Pipe', tube_vf(pth, 0.042, 14), 'Exhaust', 'Details', sharp=50)
    d = (pth[-1] - pth[-2]).normalized()
    mk('Exhaust_Tip', lathe_and_orient(pth[-1], d), 'Exhaust', 'Details', sharp=50)
    mk('Exhaust_Clamp', cyl_between(pth[6] - (pth[7] - pth[6]).normalized() * 0.02, pth[6] + (pth[7] - pth[6]).normalized() * 0.02,
                                    0.048, 14), 'Hardware', 'Details')
    # ---------------------------------------------------- fuel filler + NATO slave-start socket behind the hatches
    for s, nm in ((1, 'Fuel'), (-1, 'Slave')):
        zc, yc = 1.96, 2.68
        xo = xs(zc)
        rec = [box_between((s * (xo - 0.14), 2.585, 1.855), (s * (xo - 0.125), 2.775, 2.065)),
               box_between((s * (xo - 0.14), 2.585, 1.855), (s * (xo - 0.07), 2.60, 2.065)),
               box_between((s * (xo - 0.14), 2.76, 1.855), (s * (xo - 0.07), 2.775, 2.065)),
               box_between((s * (xo - 0.14), 2.585, 1.855), (s * (xo - 0.07), 2.775, 1.87)),
               box_between((s * (xo - 0.14), 2.585, 2.05), (s * (xo - 0.07), 2.775, 2.065))]
        mk('Recess_' + nm, merge_vf(*rec), 'Coating', 'Details')
        if s > 0:
            cap = [cyl_vf(V((xo - 0.10, yc, zc)), 0.045, 0.05, 'X', 20), cyl_vf(V((xo - 0.082, yc, zc)), 0.05, 0.015, 'X', 20),
                   box_between((xo - 0.076, yc - 0.035, zc - 0.006), (xo - 0.066, yc + 0.035, zc + 0.006))]
            mk('Fuel_Cap', merge_vf(*cap), 'Hardware', 'Details')
        else:
            sk = [cyl_vf(V((-xo + 0.10, yc, zc)), 0.040, 0.05, 'X', 20), cyl_vf(V((-xo + 0.08, yc, zc)), 0.046, 0.012, 'X', 20)]
            mk('Slave_Socket', merge_vf(*sk), 'Gunmetal', 'Details')
    # fuel door hinge + utility hatch hinge
    for nmh, s in (('Fuel_Door_L', 1), ('Utility_Hatch_R', -1)):
        x = s * (xs(1.84) + 0.012)
        hp = []
        for z in (1.90, 2.02):
            hp.append(cyl_vf(V((x, 2.57, z)), 0.012, 0.05, 'Z', 8))
            hp.append(box_between((s * (xs(z) - 0.006), 2.53, z - 0.018), (x, 2.566, z + 0.018)))
        mk(nmh + '_Hinge', merge_vf(*hp), 'Hardware', 'Details')
        dl = [box_between((s * (xs(1.96) - 0.004), 2.566, 1.945), (x, 2.62, 1.975)),
              cyl_vf(V((x, 2.57, 1.96)), 0.012, 0.03, 'Z', 8)]
        mk(nmh + '_DoorLeaf', merge_vf(*dl), 'Hardware', 'Details', ob(nmh))
    # ---------------------------------------------------- stencils (vehicle ID, designation)
    stencil('Stencil_FrontBumperL', 'TX-6', 0.055, (0.50, -3.303, 0.76), (0, -1, 0))
    stencil('Stencil_FrontBumperR', '0417', 0.055, (-0.50, -3.303, 0.76), (0, -1, 0))
    stencil('Stencil_RearBumperL', 'TX-6', 0.05, (0.30, 3.243, 0.70), (0, 1, 0))
    stencil('Stencil_RearBumperR', '0417', 0.05, (-0.30, 3.243, 0.70), (0, 1, 0))
    for s, sfx in ((1, 'L'), (-1, 'R')):
        stencil('Stencil_Fender' + sfx, 'TX-6  BASTION', 0.045, (s * (X_SIDE + 0.0285), -2.02, 1.503), (s, 0, 0))
    stencil('Stencil_Hood', 'NO STEP', 0.035, (0.0, -2.35, zh(-2.35) + 0.066), (0, 0, 1), up=(0, 1, 0), parent=ob('Hood'))
