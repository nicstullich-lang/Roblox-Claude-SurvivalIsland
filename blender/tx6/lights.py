"""TX-6 Bastion - military lighting: LED headlights, blackout/IR lamps, fog, roof bar, beacons, searchlight,
work lights, rear clusters and caged bumper tail lamps."""
from tx6.lib import *
from tx6.armor import box_arm


REFL = []


def lamp_disc(c, n, r, depth, lens_mat='Lens', emit='LED', bezel=True):
    """round lamp: housing cup + emitter + lens, facing n."""
    c, n = V(c), V(n).normalized()
    hous = orient(lathe_vf([(0, -depth), (r * 1.18, -depth), (r * 1.25, 0.0), (r * 1.25, 0.008), (r * 1.02, 0.008),
                             (r * 1.0, -0.004), (0, -0.004)], 20, False, False), c, n)
    em = orient(lathe_vf([(0, -0.012), (r * 0.45, -0.012), (r * 0.45, -0.006), (0, -0.006)], 16), c, n)
    lens = orient(lathe_vf([(0, 0.002), (r * 0.98, 0.0), (r * 0.98, -0.004), (0, -0.004)], 20), c, n)
    REFL.append(orient(lathe_vf([(r * 0.30, -depth * 0.85), (r * 0.36, -depth * 0.85), (r * 0.99, -0.006), (r * 0.93, -0.006),
                                  (r * 0.30, -depth * 0.80)], 20, False, False), c, n))
    return hous, em, lens


def quad_on(c, u, v, w, h):
    c, u, v = V(c), V(u), V(v)
    return [c - u * w / 2 - v * h / 2, c + u * w / 2 - v * h / 2, c + u * w / 2 + v * h / 2, c - u * w / 2 + v * h / 2]


def build():
    H, E, L, A, R = [], [], [], [], []      # housing, LED, lens, amber, red
    W = []                                   # white reverse lamps
    IR = []
    for s in (1, -1):
        sfx = 'L' if s > 0 else 'R'
        # ------------------------------------------------ headlight (in the armoured recess)
        H.append(box_between((s * 0.705, -2.935, 1.165), (s * 1.055, -2.92, 1.395)))
        for xm in (0.79, 0.94):
            sq = [(s * xm + dx, -2.935, 1.265 + dz) for (dx, dz) in rect2(0.115, 0.115)]
            sqi = [(s * xm + dx, -2.935, 1.265 + dz) for (dx, dz) in rect2(0.095, 0.095)]
            H.append(ring_prism(sq, sqi, (0, -0.045, 0)))
            h, e, l = lamp_disc((s * xm, -2.975, 1.265), (0, -1, 0), 0.036, 0.035)
            H.append(h)
            E.append(e)
            L.append(l)
        E.append(box_between((s * 0.72, -2.99, 1.365), (s * 1.035, -2.975, 1.383)))       # DRL strip
        A.append(box_between((s * 1.036, -2.99, 1.18), (s * 1.050, -2.975, 1.36)))        # turn strip
        E.append(box_between((s * 0.72, -2.99, 1.175), (s * 1.02, -2.975, 1.188)))        # lower position strip
        mk('Headlight_Lens' + sfx, box_between((s * 0.706, -2.998, 1.166), (s * 1.054, -2.992, 1.394)), 'Lens',
           'Lights')
        # ------------------------------------------------ NATO blackout drive lamp + marker (IR capable)
        bc = V((s * 0.88, -3.02, 1.04))
        H.append(box_vf(bc, (0.16, 0.04, 0.075)))
        H.append(box_vf(bc + V((0, -0.025, 0.04)), (0.18, 0.05, 0.012)))   # hood/visor
        IR.append(box_vf(bc + V((-s * 0.025, -0.021, 0.0)), (0.085, 0.004, 0.014)))
        A.append(box_vf(bc + V((s * 0.055, -0.021, 0.0)), (0.03, 0.004, 0.03)))
        # ------------------------------------------------ fog lamps in the bumper wings
        n = V((s * 0.414, -0.910, 0))
        fc = V((s * 1.23, -3.25, 0.73)) + n * 0.005
        h, e, l = lamp_disc(fc + n * 0.03, n, 0.048, 0.05)
        H.append(h)
        E.append(e)
        L.append(l)
        # ------------------------------------------------ LED bars on the bumper top chamfer
        cn = V((0, -0.78, 0.625)).normalized()
        u = V((1, 0, 0))
        v = V((0, 0.08, 0.10)).normalized()
        cc = V((s * 0.49, -3.26, 0.89)) + cn * 0.003
        H.append(prism(quad_on(cc, u, v, 0.27, 0.075), cn * 0.012))
        E.append(prism(quad_on(cc + cn * 0.012, u, v, 0.24, 0.035), cn * 0.004))
        # ------------------------------------------------ side markers
        A.append(box_vf((s * 1.342, -3.07, 0.73), (0.008, 0.07, 0.035)))
        A.append(box_vf((s * (X_SIDE + 0.03), -2.72, 1.505), (0.012, 0.07, 0.03)))
        R.append(box_vf((s * 1.302, 3.07, 0.67), (0.008, 0.06, 0.03)))
        R.append(box_vf((s * (X_SIDE + 0.03), 2.70, 1.52), (0.012, 0.07, 0.03)))
        # ------------------------------------------------ rear upper corner clusters
        H.append(box_between((s * 0.865, 2.92, 2.085), (s * 1.055, 2.935, 2.275)))
        for (z0, z1, lst) in ((2.215, 2.268, R), (2.152, 2.205, A), (2.092, 2.142, W)):
            lst.append(box_between((s * 0.875, 2.935, z0), (s * 1.045, 2.985, z1)))
        mk('RearCluster_Lens' + sfx, box_between((s * 0.866, 2.990, 2.086), (s * 1.054, 2.996, 2.274)), 'Lens', 'Lights')
        # ------------------------------------------------ caged tail lamps in the rear bumper
        H.append(box_between((s * 0.885, 3.10, 0.605), (s * 1.175, 3.115, 0.735)))
        for k, lst in enumerate((R, A, W)):
            x0 = 0.90 + 0.09 * k
            lst.append(box_between((s * x0, 3.115, 0.625), (s * (x0 + 0.075), 3.16, 0.715)))
        cage = []
        for xg in (0.93, 1.02, 1.11):
            cage.append(tube_vf([V((s * xg, 3.215, 0.60)), V((s * xg, 3.215, 0.74))], 0.008, 8))
        cage.append(box_arm(V((s * 0.88, 3.215, 0.745)), V((s * 1.18, 3.215, 0.745)), 0.02, 0.012))
        cage.append(box_arm(V((s * 0.88, 3.215, 0.595)), V((s * 1.18, 3.215, 0.595)), 0.02, 0.012))
        mk('TailCage' + sfx, merge_vf(*cage), 'Coating', 'Lights')
        # ------------------------------------------------ roof beacons (front + rear corners)
        for yb in (-0.63, 2.78):
            bc = V((s * 0.86, yb, Z_ROOF))
            H.append(cyl_vf(bc + V((0, 0, 0.018)), 0.065, 0.036, 'Z', 20))
            A.append(xform_vf(lathe_vf([(0, 0.0), (0.050, 0.0), (0.052, 0.05), (0.046, 0.085), (0.030, 0.10), (0, 0.104)],
                                       20), Matrix.Translation(bc + V((0, 0, 0.036)))))
            H.append(cyl_vf(bc + V((0, 0, 0.145)), 0.03, 0.012, 'Z', 16))
            H.append(cyl_vf(bc + V((0, 0, 0.12)), 0.006, 0.05, 'Z', 6))
        # ------------------------------------------------ rear work floods on the roof
        wc = V((s * 0.50, 2.84, Z_ROOF + 0.07))
        rot = Matrix.Rotation(radians(-15), 4, 'X')
        pod = xform_vf(box_vf((0, 0, 0), (0.17, 0.07, 0.09)), Matrix.Translation(wc) @ rot)
        H.append(pod)
        E.append(xform_vf(box_vf((0, 0.036, 0), (0.15, 0.004, 0.07)), Matrix.Translation(wc) @ rot))
        H.append(box_vf(wc + V((0, -0.01, -0.05)), (0.05, 0.05, 0.05)))
        # ------------------------------------------------ side work floods (light the locker work areas)
        for yw in (1.12, 2.62):
            p = V((s * 1.05, yw, 2.47))
            n = V((s * 0.85, 0, -0.5)).normalized()
            H.append(orient(box_vf((0, 0, 0), (0.13, 0.07, 0.06)), p, n, 0))
            E.append(orient(box_vf((0, 0, 0.032), (0.11, 0.05, 0.004)), p, n, 0))
    # ------------------------------------------------ roof light bar
    lb = [box_between((-0.72, -0.70, 2.535), (0.72, -0.56, 2.635))]
    lb.append(prism([(-0.74, -0.71, 2.64), (0.74, -0.71, 2.64), (0.74, -0.55, 2.64), (-0.74, -0.55, 2.64)], (0, 0, 0.012)))
    for xs_ in (-0.55, 0.55):
        lb.append(box_between((xs_ - 0.03, -0.66, Z_ROOF - 0.01), (xs_ + 0.03, -0.60, 2.54)))
        lb.append(box_between((xs_ - 0.06, -0.69, Z_ROOF - 0.005), (xs_ + 0.06, -0.57, Z_ROOF + 0.008)))
    H += lb
    for k in range(12):
        x = -0.66 + 1.32 * k / 11
        H.append(ring_prism([(x + dx, -0.700, 2.585 + dz) for (dx, dz) in rect2(0.10, 0.085)],
                            [(x + dx, -0.700, 2.585 + dz) for (dx, dz) in rect2(0.08, 0.065)], (0, -0.01, 0)))
        E.append(box_between((x - 0.035, -0.705, 2.555), (x + 0.035, -0.70, 2.615)))
    mk('LightBar_Lens', box_between((-0.715, -0.716, 2.540), (0.715, -0.710, 2.630)), 'Lens', 'Lights')
    # high-mount brake light
    R.append(box_between((-0.18, 2.985, 2.315), (0.18, 3.0, 2.345)))
    H.append(box_between((-0.20, 2.975, 2.305), (0.20, 2.99, 2.355)))
    # ------------------------------------------------ remote searchlight (front right roof)
    sp = V((-0.80, -0.35, Z_ROOF))
    srch = [cyl_vf(sp + V((0, 0, 0.03)), 0.075, 0.06, 'Z', 20), cyl_vf(sp + V((0, 0, 0.09)), 0.04, 0.06, 'Z', 12)]
    yoke = [V((-0.105, 0, 0.11)), V((-0.105, 0, 0.21)), V((0.105, 0, 0.21)), V((0.105, 0, 0.11))]
    srch.append(sweep_vf([sp + V((-0.105, 0, 0.21)), sp + V((-0.105, 0, 0.11)), sp + V((0.105, 0, 0.11)),
                          sp + V((0.105, 0, 0.21))], [(-0.012, -0.02), (0.012, -0.02), (0.012, 0.02), (-0.012, 0.02)]))
    lamp_c = sp + V((0, 0, 0.20))
    srch.append(orient(lathe_vf([(0, -0.10), (0.06, -0.10), (0.085, -0.04), (0.092, 0.06), (0.098, 0.07), (0.0, 0.07)],
                                24), lamp_c, (0, -1, 0)))
    mk('Searchlight', merge_vf(*srch), 'Gunmetal', 'Lights', bev=(0.003, 1, 30))
    h, e, l = lamp_disc(lamp_c + V((0, -0.072, 0)), (0, -1, 0), 0.085, 0.02)
    sl = bpy.data.objects['Searchlight']
    set_origin(sl, sp)
    mk('Searchlight_LED', e, 'LED', 'Lights', sl)
    mk('Searchlight_Lens', l, 'Lens', 'Lights', sl)
    anim(sl, 'searchlight: pan about Z')

    mk('Light_Housings', merge_vf(*H), 'Housing', 'Lights', bev=(0.002, 1, 30))
    mk('Light_Reflectors', merge_vf(*REFL), 'Alu', 'Lights')
    REFL.clear()
    mk('Light_LED', merge_vf(*E), 'LED', 'Lights')
    mk('Light_Lenses', merge_vf(*L), 'Lens', 'Lights')
    mk('Light_Amber', merge_vf(*A), 'Amber', 'Lights')
    mk('Light_Red', merge_vf(*R), 'RedLens', 'Lights')
    mk('Light_White', merge_vf(*W), 'LEDOff', 'Lights')
    mk('Light_IR', merge_vf(*IR), 'IRLens', 'Lights')
