"""TX-6 Bastion - roof weapon station (rotating turret + gunner seat + fictional rotary cannon), concealed
missile bays with lift + launch pods, folding sensor/comms mast, deployable windshield shield and window shutters.

Every moving part has its pivot at the real hinge and a 'tx_anim' custom property describing the motion.
All fictional / game-oriented: no real-world weapon construction detail.
"""
from tx6.lib import *
from tx6 import body as B
from tx6.armor import box_arm

TC = V((0.0, 0.30, 0.0))       # turret ring centre (plan)
Z_RACE = 2.55                  # top of the fixed ring collar


def pol(phi, r, z):
    a = radians(phi)
    return V((TC.x + r * sin(a), TC.y - r * cos(a), z))


def u_r(phi):
    a = radians(phi)
    return V((sin(a), -cos(a), 0))


def u_t(phi):
    a = radians(phi)
    return V((cos(a), sin(a), 0))


def catmull(pts, n=8):
    P_ = [V(p) for p in pts]
    P_ = [P_[0]] + P_ + [P_[-1]]
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P_[-2])
    return out


def basis_box(c, ux, uy, size):
    """box centred at c with local axes ux, uy, z."""
    ux, uy = V(ux).normalized(), V(uy).normalized()
    uz = ux.cross(uy)
    m = Matrix((ux, uy, uz)).transposed().to_4x4()
    m.translation = V(c)
    return xform_vf(box_vf((0, 0, 0), size), m)


# ============================================================== TURRET
SH_ANG = [-105, -60, -22, 22, 60, 105]
SH_Z0, SH_Z1 = 2.60, 3.24


def r_out(z):
    return 0.745 - 0.05 * (z - SH_Z0) / (SH_Z1 - SH_Z0)


def build_turret():
    # ---------------- fixed ring collar + hole lining
    collar = lathe_vf([(0.60, 2.48), (0.765, 2.48), (0.765, 2.53), (0.745, Z_RACE), (0.60, Z_RACE), (0.60, 2.48)], 64,
                      False, False)
    lining = lathe_vf([(0.56, 2.38), (0.60, 2.38), (0.60, 2.50), (0.56, 2.50), (0.56, 2.38)], 64, False, False)
    base = mk('Turret_RingBase', xform_vf(merge_vf(collar, lining), Matrix.Translation(TC)), 'ArmorPaint', 'Turret',
              bev=(0.004, 1, 30))
    bolts('Turret_RingBase_Bolts', [pol(a * 15, 0.755, 2.53) for a in range(24)], V((0, 0, 1)), base, r=0.012)
    # ---------------- rotor (rotates about Z)
    rotor = empty('Turret_Rotor', TC + V((0, 0, Z_RACE)), 'Turret', size=0.4)
    anim(rotor, 'turret traverse: rotate about Z (360 deg)')
    race = lathe_vf([(0.58, Z_RACE + 0.001), (0.73, Z_RACE + 0.001), (0.73, SH_Z0), (0.58, SH_Z0), (0.58, Z_RACE + 0.001)], 64, False, False)
    mk('Turret_Race', xform_vf(race, Matrix.Translation(TC)), 'Gunmetal', 'Turret', rotor, bev=(0.003, 1, 30))
    # ---------------- faceted, rear-raked gun shield (one loft), cut for the gun port and two vision blocks
    def loop(z, ro, ri, angs):
        return [pol(a, ro, z) for a in angs] + [pol(a, ri, z) for a in reversed(angs)]
    sh = loft([loop(SH_Z0, 0.745, 0.705, SH_ANG), loop(SH_Z1, 0.695, 0.655, SH_ANG)])
    shield = mk('Turret_Shield', sh, 'ArmorPaint', 'Turret', rotor)
    cuts = [cutter('_notch', box_between((-0.165, -0.62, 2.84), (0.165, -0.15, 3.40)))]
    glass = []
    for s in (1, -1):
        phi = 41 * s
        half = radians(19)

        def ctr(z, dr=0.0):
            rm = r_out(z) - 0.02 + dr
            return TC + u_r(phi) * (rm * cos(half)) + V((0, 0, z))
        c = ctr(3.02)
        q = [c - u_r(phi) * 0.15 + u_t(phi) * dx + V((0, 0, dz)) for (dx, dz) in rect2(0.24, 0.18)]
        cuts.append(cutter('_win', prism(q, u_r(phi) * 0.30)))
        loops = []
        for z in (2.92, 3.12):
            cz = ctr(z)
            loops.append([cz - u_r(phi) * 0.016 - u_t(phi) * 0.13, cz - u_r(phi) * 0.016 + u_t(phi) * 0.13,
                          cz + u_r(phi) * 0.016 + u_t(phi) * 0.13, cz + u_r(phi) * 0.016 - u_t(phi) * 0.13])
        glass.append(loft(loops))
    boolean(shield, cuts)
    clear_scratch()
    bevel(shield, 0.006, 2, 30)
    mk('Turret_VisionBlocks', merge_vf(*glass), 'Glass', 'Turret', rotor)
    # shield bolts (bottom + top rows on every facet)
    bp, bn = [], []
    for a0, a1 in zip(SH_ANG[:-1], SH_ANG[1:]):
        nm = u_r((a0 + a1) / 2)
        for z in (2.66, 3.18):
            p0 = pol(a0, r_out(z), z)
            p1 = pol(a1, r_out(z), z)
            for q in pts_line(p0, p1, 0.11, 0.05):
                if z > 3.0 and abs(q.x) < 0.2 and a0 == -22:
                    continue
                bp.append(q + nm * 0.002)
                bn.append(nm)
    shb = merge_vf(*[bolt_vf(p, n, 0.011, 0.009, washer=False) for p, n in zip(bp, bn)])
    mk('Turret_Shield_Bolts', shb, 'Hardware', 'Turret', rotor)
    # rear side wings (lower)
    for s in (1, -1):
        angs = [105 * s, 140 * s] if s > 0 else [-140, -105]
        w = loft([loop(SH_Z0, 0.745, 0.705, angs), loop(2.92, 0.72, 0.68, angs)])
        mk('Turret_Wing' + ('L' if s > 0 else 'R'), w, 'ArmorPaint', 'Turret', rotor, bev=(0.005, 2, 30))
    # smoke-grenade dischargers on the shield flanks (fictional)
    sm = []
    for s in (1, -1):
        phi = 88 * s
        a0, a1 = (60 * s, 105 * s)
        P0, P1 = pol(a0, r_out(3.0), 3.0), pol(a1, r_out(3.0), 3.0)
        base_c = P0.lerp(P1, (88 - 60) / 45) + u_r(82.5 * s) * 0.013
        d = (u_r(phi) * 0.75 + V((0, -0.25, 0.62))).normalized()
        sm.append(basis_box(base_c, u_t(phi), V((0, 0, 1)), (0.20, 0.17, 0.03)))
        for i in (-1, 1):
            for j in (-1, 1):
                c0 = base_c + u_t(phi) * (0.045 * i) + V((0, 0, 0.045 * j)) + u_r(phi) * 0.02
                sm.append(cyl_between(c0, c0 + d * 0.16, 0.034, 12))
    mk('Turret_SmokeLaunchers', merge_vf(*sm), 'Gunmetal', 'Turret', rotor, bev=(0.003, 1, 30))
    # ---------------- ammunition box on a bracket + segmented feed chute
    phi = 75
    ac = pol(phi, 0.47, 2.785)
    ab = [basis_box(ac, u_r(phi), u_t(phi), (0.18, 0.36, 0.30)),
          basis_box(ac + V((0, 0, 0.155)), u_r(phi), u_t(phi), (0.19, 0.37, 0.02)),
          basis_box(pol(phi, 0.55, 2.615), u_r(phi), u_t(phi), (0.34, 0.30, 0.03))]
    for dy in (-0.10, 0.10):
        ab.append(basis_box(ac + u_t(phi) * dy + u_r(phi) * 0.095 + V((0, 0, 0.10)), u_r(phi), u_t(phi),
                            (0.02, 0.04, 0.05)))
    mk('Turret_AmmoBox', merge_vf(*ab), 'PaintDark', 'Turret', rotor, bev=(0.004, 1, 30))
    path = catmull([V((0.39, 0.06, 2.94)), V((0.36, -0.06, 3.05)), V((0.24, -0.20, 3.07)), V((0.125, -0.31, 2.99))], 8)
    chute = [sweep_vf(path, [(-0.018, -0.035), (0.018, -0.035), (0.018, 0.035), (-0.018, 0.035)])]
    P_, T, N = frames(path)
    for i in range(1, len(P_) - 1):
        bvec = T[i].cross(N[i])
        ring = [P_[i] + N[i] * qx + bvec * qy for (qx, qy) in rect2(0.046, 0.084)]
        ringi = [P_[i] + N[i] * qx + bvec * qy for (qx, qy) in rect2(0.036, 0.070)]
        chute.append(ring_prism(ring, ringi, T[i] * 0.012))
    mk('Turret_FeedChute', merge_vf(*chute), 'Gunmetal', 'Turret', rotor, sharp=45)
    # ---------------- trunnion cheeks on the shield (rotor) + pitching cradle
    cheeks = []
    for s in (1, -1):
        cheeks.append(box_between((s * 0.175, -0.335, 2.85), (s * 0.195, -0.19, 3.05)))
        cheeks.append(cyl_vf(V((s * 0.205, -0.27, 2.96)), 0.03, 0.02, 'X', 12))
    mk('Turret_Cheeks', merge_vf(*cheeks), 'Gunmetal', 'Turret', rotor, bev=(0.003, 1, 30))
    cradle = empty('Turret_Cradle', (0, -0.27, 2.96), 'Turret', rotor, 0.25)
    anim(cradle, 'gun elevation: rotate about X (negative = barrels up), -35 to +8 deg')
    cr = [box_between((0.148, -0.33, 2.88), (0.168, -0.16, 3.03)), box_between((-0.168, -0.33, 2.88), (-0.148, -0.16, 3.03)),
          box_between((-0.168, -0.33, 2.875), (0.168, -0.16, 2.895)),
          cyl_vf(V((0, -0.27, 2.96)), 0.022, 0.36, 'X', 12)]
    mk('Turret_CradleFrame', merge_vf(*cr), 'Gunmetal', 'Turret', cradle, bev=(0.003, 1, 30))
    # ---------------- fictional 6-barrel rotary cannon
    gun = []
    rcv = [(-0.065, 2.90), (0.065, 2.90), (0.065, 3.01), (0.05, 3.025), (-0.05, 3.025), (-0.065, 3.01)]
    gun.append(prism([(x, -0.13, z) for (x, z) in rcv], (0, -0.37, 0)))
    gun.append(box_between((-0.12, -0.13, 2.905), (0.12, -0.11, 3.02)))                  # back plate
    gun.append(cyl_vf(V((-0.088, -0.30, 2.995)), 0.035, 0.16, 'Y', 16))                  # drive motor
    gun.append(box_between((0.065, -0.37, 2.925), (0.125, -0.27, 3.005)))                 # feeder / delinker
    gun.append(cyl_vf(V((0, -0.54, 2.96)), 0.075, 0.08, 'Y', 24))                         # barrel bearing housing
    gun.append(box_between((-0.012, -0.47, 3.025), (0.012, -0.16, 3.035)))                # top rail
    for s in (1, -1):
        gun.append(cyl_vf(V((s * 0.10, -0.06, 2.97)), 0.017, 0.14, 'Z', 10))              # spade grips
        gun.append(box_arm(V((s * 0.10, -0.06, 3.03)), V((s * 0.08, -0.115, 3.01)), 0.022, 0.022))
        gun.append(box_arm(V((s * 0.10, -0.06, 2.91)), V((s * 0.08, -0.115, 2.93)), 0.022, 0.022))
    gun.append(box_between((-0.03, -0.075, 2.955), (0.03, -0.065, 2.985)))                # butterfly trigger
    mn = mk('Turret_Minigun', merge_vf(*gun), 'Gunmetal', 'Turret', cradle, bev=(0.003, 1, 30))
    sight = [box_between((-0.028, -0.36, 3.035), (0.028, -0.22, 3.095))]
    mk('Turret_Sight', merge_vf(*sight), 'Housing', 'Turret', mn, bev=(0.004, 1, 30))
    mk('Turret_SightLens', box_between((-0.022, -0.364, 3.042), (0.022, -0.358, 3.088)), 'GlassDark', 'Turret', mn)
    bar = []
    for k in range(6):
        a = 2 * pi * k / 6
        c = V((0.042 * cos(a), 0, 2.96 + 0.042 * sin(a)))
        bar.append(cyl_between(c + V((0, -0.58, 0)), c + V((0, -1.30, 0)), 0.0115, 10))
        bar.append(cyl_between(c + V((0, -1.30, 0)), c + V((0, -1.325, 0)), 0.0145, 10))
    for yc, rr in ((-0.83, 0.066), (-1.25, 0.062)):
        bar.append(cyl_vf(V((0, yc, 2.96)), rr, 0.026, 'Y', 24))
    bar.append(cyl_between(V((0, -0.58, 2.96)), V((0, -1.26, 2.96)), 0.026, 12))
    barrels = mk('Turret_Barrels', merge_vf(*bar), 'Gunmetal', 'Turret', mn, sharp=40)
    set_origin(barrels, (0, -0.95, 2.96))
    anim(barrels, 'barrel cluster spin: rotate about local Y (gun axis)')
    # ---------------- gunner sling seat (rotates with the turret)
    seat = []
    seat.append(box_between((-0.20, 0.33, 1.77), (0.20, 0.67, 1.84)))
    seat.append(xform_vf(box_vf((0, 0, 0), (0.40, 0.06, 0.34)),
                         Matrix.Translation((0, 0.70, 2.02)) @ Matrix.Rotation(radians(-10), 4, 'X')))
    mk('Turret_GunnerSeat', merge_vf(*seat), 'Fabric', 'Turret', rotor, bev=(0.012, 2, 30))
    straps = []
    hangers = []
    for s in (1, -1):
        for (p_seat, phi_r) in ((V((s * 0.19, 0.36, 1.83)), 128 * s), (V((s * 0.19, 0.66, 1.83)), 158 * s)):
            top = pol(phi_r, 0.50, SH_Z0 - 0.015)
            straps.append(sweep_vf([p_seat, top], [(-0.003, -0.022), (0.003, -0.022), (0.003, 0.022), (-0.003, 0.022)]))
            straps.append(box_vf(top, (0.05, 0.05, 0.02)))
            hangers.append(sweep_vf([pol(phi_r, 0.49, SH_Z0 - 0.015), pol(phi_r, 0.66, SH_Z0 - 0.015)],
                                    [(-0.012, -0.025), (0.012, -0.025), (0.012, 0.025), (-0.012, 0.025)]))
    mk('Turret_SeatStraps', merge_vf(*straps), 'Canvas', 'Turret', rotor)
    mk('Turret_SeatHangers', merge_vf(*hangers), 'Gunmetal', 'Turret', rotor)
    st = empty('Seat_Gunner', (0, 0.50, 1.84), 'Turret', rotor, 0.15)
    st['tx_seat'] = 'gunner (second player): sits on the sling seat, operates the turret'


# ============================================================== MISSILE BAYS
def build_missiles():
    for s, sfx in ((1, 'L'), (-1, 'R')):
        xc = s * 0.67
        # bay box (inside the roof)
        bay = [box_between((s * 0.385, 1.255, 1.985), (s * 0.955, 2.545, 2.0))]
        bay.append(box_between((s * 0.385, 1.255, 2.0), (s * 0.40, 2.545, 2.42)))
        bay.append(box_between((s * 0.94, 1.255, 2.0), (s * 0.955, 2.545, 2.42)))
        bay.append(box_between((s * 0.40, 1.255, 2.0), (s * 0.94, 1.27, 2.42)))
        bay.append(box_between((s * 0.40, 2.53, 2.0), (s * 0.94, 2.545, 2.42)))
        mk('Missile_Bay_' + sfx, merge_vf(*bay), 'Coating', 'Missiles')
        cyls = [cyl_between(V((xc, yy, 1.90)), V((xc, yy, 2.075)), 0.042, 14) for yy in (1.55, 2.25)]
        mk('Missile_LiftBase_' + sfx, merge_vf(*cyls), 'Gunmetal', 'Missiles')
        lift = empty('Missile_Lift_' + sfx, (xc, 1.90, 2.09), 'Missiles', size=0.2)
        anim(lift, 'launcher lift: move +0.46 along Z (after the hatch opens)')
        lp = [box_between((xc - 0.25, 1.30, 2.075), (xc + 0.25, 2.48, 2.10))]
        for yy in (1.55, 2.25):
            lp.append(cyl_between(V((xc, yy, 1.52)), V((xc, yy, 2.08)), 0.022, 10))
        mk('Missile_LiftPlatform_' + sfx, merge_vf(*lp), 'Gunmetal', 'Missiles', lift, bev=(0.003, 1, 30))
        pod_e = empty('Missile_Pod_' + sfx, (xc, 2.46, 2.10), 'Missiles', lift, 0.2)
        anim(pod_e, 'launch pod elevation: rotate -18 deg about X (nose up), after the lift is up')
        pod = mk('Missile_PodBody_' + sfx, box_between((xc - 0.24, 1.32, 2.10), (xc + 0.24, 2.46, 2.38)), 'ArmorPaint',
                 'Missiles', pod_e)
        holes = []
        noses, bands, tips, liners = [], [], [], []
        for i in (-1, 0, 1):
            for zz in (2.175, 2.305):
                c = V((xc + 0.155 * i, 1.32, zz))
                holes.append(cutter('_tube', cyl_between(c - V((0, 0.05, 0)), c + V((0, 0.14, 0)), 0.055, 24)))
                noses.append(orient(lathe_vf([(0, 0.0), (0.012, 0.004), (0.028, 0.020), (0.040, 0.045), (0.047, 0.070),
                                              (0.048, 0.085), (0.0, 0.085)], 20), c + V((0, 0.040, 0)), (0, 1, 0)))
                tips.append(orient(lathe_vf([(0, 0.0), (0.012, 0.0045), (0.014, -0.002), (0, -0.002)], 12),
                                   c + V((0, 0.040, 0)), (0, -1, 0)))
                bands.append(cyl_vf(c + V((0, 0.12, 0)), 0.0485, 0.012, 'Y', 20))
                liners.append(lathe_vf([(0.055, 0.0), (0.060, 0.0), (0.060, 0.012), (0.055, 0.012), (0.055, 0.0)], 24,
                                       False, False))
                liners[-1] = orient(liners[-1], c + V((0, -0.002, 0)), (0, -1, 0))
        boolean(pod, holes)
        clear_scratch()
        bevel(pod, 0.008, 2, 30)
        mk('Missile_Noses_' + sfx, merge_vf(*noses), 'Missile', 'Missiles', pod_e)
        mk('Missile_Seekers_' + sfx, merge_vf(*tips), 'GlassDark', 'Missiles', pod_e)
        mk('Missile_Bands_' + sfx, merge_vf(*bands), 'Hazard', 'Missiles', pod_e)
        mk('Missile_TubeRims_' + sfx, merge_vf(*liners), 'Gunmetal', 'Missiles', pod_e)
        mk('Missile_PodExhaust_' + sfx, box_between((xc - 0.21, 2.46, 2.13), (xc + 0.21, 2.468, 2.35)), 'Mesh', 'Missiles',
           pod_e)
        bolts('Missile_PodBody_%s_Bolts' % sfx,
              pts_poly([V((xc + dx, y, 2.38)) for (dx, y) in rect2(0.46, 1.12, 0, 1.89)], 0.16, 0.0), V((0, 0, 1)),
              pod_e, r=0.009)
        # hatch hinge knuckles (fixed on the roof)
        kn = []
        for yy in (1.40, 1.90, 2.40):
            kn.append(cyl_vf(V((s * 0.96, yy, Z_ROOF)), 0.017, 0.12, 'Y', 12))
            kn.append(box_between((s * 0.975, yy - 0.06, Z_ROOF - 0.002), (s * 1.0, yy + 0.06, Z_ROOF + 0.008)))
        mk('Missile_HatchHinges_' + sfx, merge_vf(*kn), 'Hardware', 'Missiles')
        h = bpy.data.objects['Missile_Hatch_' + sfx]
        bolts('Missile_Hatch_%s_Bolts' % sfx,
              pts_poly([V((s * x, y, Z_ROOF)) for (x, y) in [(0.40, 1.27), (0.94, 1.27), (0.94, 2.53), (0.40, 2.53)]],
                       0.18, 0.03), V((0, 0, 1)), h, r=0.010)


# ============================================================== SENSOR / COMMS MAST
def build_mast():
    H = V((0, 1.10, 2.60))
    base = [box_between((0.06, 1.03, 2.48), (0.085, 1.17, 2.68)), box_between((-0.085, 1.03, 2.48), (-0.06, 1.17, 2.68)),
            box_between((-0.11, 1.02, 2.475), (0.11, 1.18, 2.50)), cyl_vf(H, 0.018, 0.21, 'X', 10),
            box_between((-0.09, 2.08, 2.475), (0.09, 2.18, 2.53)), box_between((0.065, 2.08, 2.53), (0.085, 2.18, 2.62)),
            box_between((-0.085, 2.08, 2.53), (-0.065, 2.18, 2.62)),
            cyl_between(V((0, 1.50, 2.505)), V((0, 1.26, 2.52)), 0.025, 12),
            box_between((-0.05, 1.48, 2.475), (0.05, 1.56, 2.50))]
    mb = mk('Sensor_MastBase', merge_vf(*base), 'Gunmetal', 'Sensor', bev=(0.003, 1, 30))
    mk('Sensor_RestPad', box_between((-0.065, 2.09, 2.53), (0.065, 2.17, 2.548)), 'Rubber', 'Sensor')
    mast = empty('Sensor_Mast', H, 'Sensor', size=0.25)
    anim(mast, 'mast raise: rotate +90 deg about X (stowed flat -> vertical)')
    lower = [box_between((-0.05, 1.10, 2.55), (0.05, 2.21, 2.65)), cyl_vf(H, 0.036, 0.12, 'X', 16),
             box_between((-0.058, 2.17, 2.542), (0.058, 2.21, 2.658))]
    mk('Sensor_MastLower', merge_vf(*lower), 'ArmorPaint', 'Sensor', mast, bev=(0.004, 1, 30))
    upper = empty('Sensor_MastUpper', (0, 2.21, 2.60), 'Sensor', mast, 0.15)
    anim(upper, 'telescopic section: slide +0.55 along local Y (mast axis)')
    mk('Sensor_MastTube', box_between((-0.035, 1.40, 2.565), (0.035, 2.27, 2.635)), 'Alu', 'Sensor', upper)
    head = empty('Sensor_Head', (0, 2.30, 2.60), 'Sensor', upper, 0.15)
    anim(head, 'sensor head: continuous rotation about local Y (mast axis)')
    hd = [cyl_vf(V((0, 2.29, 2.60)), 0.07, 0.04, 'Y', 20), box_between((-0.085, 2.31, 2.548), (0.085, 2.52, 2.652))]
    mk('Sensor_HeadBody', merge_vf(*hd), 'Gunmetal', 'Sensor', head, bev=(0.004, 1, 30))
    pan = [box_between((-0.165, 2.31, 2.655), (0.165, 2.535, 2.69)), box_between((-0.165, 2.31, 2.51), (0.165, 2.535, 2.545))]
    mk('Sensor_RadarPanels', merge_vf(*pan), 'ArmorPaint', 'Sensor', head, bev=(0.004, 1, 30))
    face = [box_between((-0.15, 2.325, 2.69), (0.15, 2.52, 2.694)), box_between((-0.15, 2.325, 2.506), (0.15, 2.52, 2.51))]
    mk('Sensor_RadarFaces', merge_vf(*face), 'Housing', 'Sensor', head)
    ant = [box_between((0.085, 2.38, 2.585), (0.09, 2.52, 2.615)), box_between((-0.09, 2.38, 2.585), (-0.085, 2.52, 2.615))]
    mk('Sensor_Blades', merge_vf(*ant), 'Plastic', 'Sensor', head)
    eo = empty('Sensor_EOBall', (0, 2.60, 2.60), 'Sensor', head, 0.1)
    anim(eo, 'EO/IR gimbal: tilt about local X')
    ball = orient(lathe_vf([(0, -0.075)] + [(0.075 * sin(pi * k / 10), -0.075 * cos(pi * k / 10)) for k in range(1, 10)] +
                           [(0, 0.075)], 20), (0, 2.60, 2.60), (0, 0, 1))
    mk('Sensor_EOBallShell', merge_vf(ball, cyl_vf(V((0, 2.52, 2.60)), 0.03, 0.03, 'Y', 12)), 'ArmorPaint', 'Sensor', eo)
    mk('Sensor_EOWindow', cyl_vf(V((0.0, 2.60, 2.672)), 0.035, 0.012, 'Z', 20), 'GlassDark', 'Sensor', eo)
    # shift the whole mast assembly 5 cm aft so the turret's rear wings clear the hinge clevis at any traverse
    for nm in ('Sensor_MastBase', 'Sensor_RestPad', 'Sensor_Mast'):
        o = bpy.data.objects[nm]
        o.matrix_basis = Matrix.Translation((0, 0.05, 0)) @ o.matrix_basis


# ============================================================== DEPLOYABLE ARMOUR
def build_deploy_armor():
    hood = bpy.data.objects['Hood']
    hz = zh(-1.215)
    piv = V((0, -1.215, 1.715))
    sh = mk('Deploy_WindshieldShield', box_between((-0.96, -1.915, 1.70), (0.96, -1.215, 1.73)), 'ArmorPaint', 'Armor',
            hood)
    slits = [cutter('_slit', box_between((x0, -1.675, 1.60), (x1, -1.615, 1.80))) for (x0, x1) in ((0.14, 0.78),
                                                                                                    (-0.78, -0.14))]
    boolean(sh, slits)
    clear_scratch()
    bevel(sh, 0.006, 2, 30)
    set_origin(sh, piv)
    anim(sh, 'windshield armour: rotate -113.6 deg about X (flips up in front of the windshield)')
    g = [box_between((x0 - 0.005, -1.68, 1.702), (x1 + 0.005, -1.61, 1.728)) for (x0, x1) in ((0.14, 0.78), (-0.78, -0.14))]
    mk('Deploy_WindshieldShield_Glass', merge_vf(*g), 'Glass', 'Armor', sh)
    bolts('Deploy_WindshieldShield_Bolts',
          pts_poly([V((x, y, 1.73)) for (x, y) in rect2(1.86, 0.64, 0, -1.565)], 0.16, 0.0), V((0, 0, 1)), sh, r=0.010)
    kn = []
    for x in (-0.70, 0.0, 0.70):
        kn.append(cyl_vf(V((x, -1.215, 1.715)), 0.02, 0.16, 'X', 12))
        kn.append(box_between((x - 0.07, -1.24, hz - 0.002), (x + 0.07, -1.20, 1.700)))
    pads = [box_between((x - 0.05, y - 0.03, zh(y) - 0.003), (x + 0.05, y + 0.03, 1.70)) for x in (-0.7, 0.7)
            for y in (-1.40, -1.85)]
    mk('Deploy_WindshieldShield_Hinges', merge_vf(*kn), 'Hardware', 'Armor', hood)
    mk('Deploy_WindshieldShield_Pads', merge_vf(*pads), 'Rubber', 'Armor', hood)
    # ---------------- flip-up window shutters (stowed hanging over the door armour, hinge below the window)
    for s, sfx in ((1, 'L'), (-1, 'R')):
        for door, outline, slit in (('Door_F', [(-0.9875, 1.705), (-0.14, 1.705), (-0.14, 1.105), (-0.691, 1.105)],
                                     (-0.78, -0.30)),
                                    ('Door_R', [(0.02, 1.705), (0.86, 1.705), (0.86, 1.105), (0.02, 1.105)], (0.14, 0.74))):
            d = bpy.data.objects[door + sfx]
            nm = 'Deploy_Shutter_%s%s' % (door[-1], sfx)
            pts = [V((s * 1.285, y, z)) for (y, z) in outline]
            sh = mk(nm, prism(pts, (s * 0.025, 0, 0)), 'ArmorPaint', 'Armor', d)
            boolean(sh, [cutter('_s', box_between((s * 1.25, slit[0], 1.385), (s * 1.35, slit[1], 1.425)))])
            clear_scratch()
            bevel(sh, 0.005, 2, 30)
            yc = sum(p[0] for p in outline) / 4
            set_origin(sh, (s * 1.285, yc, 1.705))
            anim(sh, 'window shutter: rotate %+d deg about Y (flips up over the window)' % (171 * s))
            mk(nm + '_Glass', box_between((s * 1.288, slit[0] - 0.005, 1.382), (s * 1.302, slit[1] + 0.005, 1.428)),
               'Glass', 'Armor', sh)
            bolts(nm + '_Bolts', pts_poly([V((s * 1.31, y, z)) for (y, z) in outline], 0.14, 0.03), V((s, 0, 0)), sh,
                  r=0.009)
            hz_ = []
            for yy in (outline[0][0] + 0.12, (outline[0][0] + outline[1][0]) / 2, outline[1][0] - 0.12):
                hz_.append(cyl_vf(V((s * 1.285, yy, 1.705)), 0.016, 0.09, 'Y', 10))
                hz_.append(box_between((s * 1.205, yy - 0.04, 1.69), (s * 1.285, yy + 0.04, 1.718)))
            mk(nm + '_Hinges', merge_vf(*hz_), 'Hardware', 'Armor', d)


def build():
    build_turret()
    build_missiles()
    build_mast()
    build_deploy_armor()
