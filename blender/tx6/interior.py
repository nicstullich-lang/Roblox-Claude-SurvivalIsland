"""TX-6 Bastion - crew compartment: dash + displays, steering, 4 armoured seats with harnesses, console with
radio stack and turret fire-control grip, roll cage, door cards, gunner platform, rear cargo, seat markers."""
from tx6.lib import *


def box_arm_i(p0, p1, w, h):
    return sweep_vf([V(p0), V(p1)], [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)])


def seat_vf(c, facing=-1):
    """armoured bucket seat; c = centre of the cushion top. facing -1 = faces -Y (forward)."""
    c = V(c)
    f = facing
    cushion = box_vf(c + V((0, 0, -0.06)), (0.50, 0.50, 0.12))
    bol = [box_vf(c + V((sx * 0.235, 0, -0.01)), (0.06, 0.48, 0.10)) for sx in (1, -1)]
    back_c = c + V((0, -f * 0.27, 0.36))
    back = xform_vf(box_vf((0, 0, 0), (0.50, 0.12, 0.68)),
                    Matrix.Translation(back_c) @ Matrix.Rotation(radians(12 * f), 4, 'X'))
    wings = [xform_vf(box_vf((sx * 0.24, -f * 0.03, 0.05), (0.06, 0.16, 0.56)),
                      Matrix.Translation(back_c) @ Matrix.Rotation(radians(12 * f), 4, 'X')) for sx in (1, -1)]
    head = xform_vf(box_vf((0, 0, 0), (0.30, 0.11, 0.20)),
                    Matrix.Translation(c + V((0, -f * 0.36, 0.84))) @ Matrix.Rotation(radians(12 * f), 4, 'X'))
    return merge_vf(cushion, *bol, back, *wings, head)


def seat_base_vf(c):
    c = V(c)
    return merge_vf(box_vf(c + V((0, 0, -0.12 - (c.z - 0.12 - 0.70) / 2)), (0.42, 0.42, c.z - 0.12 - 0.70)),
                    box_vf(V((c.x, c.y, 0.71)), (0.46, 0.46, 0.02)))


def harness_vf(c, facing=-1):
    c = V(c)
    f = facing
    st = []
    shp = [(-0.003, -0.025), (0.003, -0.025), (0.003, 0.025), (-0.003, 0.025)]
    for sx in (1, -1):
        top = c + V((sx * 0.09, -f * 0.33, 0.66))
        mid = c + V((sx * 0.08, f * 0.02, 0.24))
        st.append(sweep_vf([top, top + V((0, f * 0.10, -0.06)), mid + V((0, f * 0.06, 0.0)), c + V((0, f * 0.12, 0.08))],
                           shp))
        st.append(sweep_vf([c + V((sx * 0.22, -f * 0.10, 0.02)), c + V((sx * 0.12, f * 0.10, 0.10)),
                            c + V((0, f * 0.14, 0.09))], shp))
    st.append(cyl_vf(c + V((0, f * 0.14, 0.09)), 0.035, 0.015, (0, f, 0.3), 16))
    return merge_vf(*st)


def build():
    # ---------------- firewall + floor mats
    mk('Int_Firewall', box_between((-1.15, -1.17, 0.68), (1.15, -1.15, 1.62)), 'PaintDark', 'Interior')
    mats = [box_between((sx * 0.30, -1.05, 0.68), (sx * 0.80, -0.10, 0.695)) for sx in (1, -1)]
    mats += [box_between((sx * 0.35, 0.05, 0.68), (sx * 0.90, 1.00, 0.695)) for sx in (1, -1)]
    mk('Int_FloorMats', merge_vf(*mats), 'Rubber', 'Interior')
    # ---------------- dashboard
    prof = [(-1.15, 0.95), (-0.95, 0.95), (-0.86, 1.22), (-0.80, 1.45), (-0.86, 1.58), (-1.15, 1.61)]
    dash = loft([[(x, y, z) for (y, z) in prof] for x in (-1.13, 1.13)])
    mk('Int_Dash', dash, 'Plastic', 'Interior', bev=(0.01, 2, 30))
    # glare shield over the driver display
    mk('Int_GlareShield', box_between((0.28, -0.90, 1.58), (0.82, -0.78, 1.60)), 'Plastic', 'Interior')
    # displays on the near-vertical dash face (normal tilted up/back)
    a, b = V((0, -0.86, 1.22)), V((0, -0.80, 1.45))
    t = (b - a).normalized()
    nrm = V((0, t.z, -t.y))
    if nrm.y < 0:
        nrm = -nrm
    screens, bezels = [], []
    for (xc, w, h, zc) in ((0.55, 0.42, 0.15, 1.38), (0.0, 0.30, 0.20, 1.34), (-0.50, 0.26, 0.16, 1.36), (0.0, 0.22, 0.09, 1.21)):
        p = V((xc, a.y + (zc - a.z) * (b.y - a.y) / (b.z - a.z), zc)) + nrm * 0.004
        q = [p + V((dx, 0, 0)) + t * dz for (dx, dz) in rect2(w, h)]
        bezels.append(prism([p + V((dx, 0, 0)) + t * dz for (dx, dz) in rect2(w + 0.03, h + 0.03)], nrm * 0.010))
        screens.append(prism([v + nrm * 0.010 for v in q], nrm * 0.003))
    mk('Int_ScreenBezels', merge_vf(*bezels), 'Housing', 'Interior')
    mk('Int_Screens', merge_vf(*screens[:2]), 'Screen', 'Interior')
    mk('Int_Screens2', merge_vf(*screens[2:]), 'ScreenBlue', 'Interior')
    # ---------------- steering (column + 3-spoke wheel)
    wc = V((0.55, -0.62, 1.32))
    wn = V((0, 0.88, 0.47)).normalized()
    rim = [wc + (V((cos(2 * pi * k / 32), 0, sin(2 * pi * k / 32))) * 0.19) for k in range(32)]
    q = V((0, 1, 0)).rotation_difference(wn)
    rim = [wc + q @ (p - wc) for p in rim]
    sw = [tube_vf(rim + [rim[0]], 0.018, 8), cyl_between(wc - wn * 0.30, wc, 0.03, 12), cyl_vf(wc, 0.05, 0.05, wn, 16)]
    for k in (0, 1, 2):
        ang = -pi / 2 + k * 2 * pi / 3 + (pi / 3 if k else 0) * 0
        ang = [-pi / 2, pi / 6, 5 * pi / 6][k]
        sp = wc + q @ (V((cos(ang), 0, sin(ang))) * 0.18)
        sw.append(sweep_vf([wc, sp], [(-0.012, -0.022), (0.012, -0.022), (0.012, 0.022), (-0.012, 0.022)]))
    mk('Int_SteeringWheel', merge_vf(*sw), 'Plastic', 'Interior', sharp=50)
    ped = [box_between((x - 0.04, -0.99, 0.78), (x + 0.04, -0.97, 0.90)) for x in (0.42, 0.56, 0.72)]
    ped += [box_arm_i(V((x, -0.98, 0.89)), V((x, -1.15, 1.06)), 0.02, 0.015) for x in (0.42, 0.56, 0.72)]
    mk('Int_Pedals', merge_vf(*ped), 'Hardware', 'Interior')
    # ---------------- seats (front + rear), harnesses, seat markers
    seats = [('Driver', V((0.55, -0.30, 1.04))), ('Passenger', V((-0.55, -0.30, 1.04))),
             ('RearL', V((0.62, 0.62, 1.04))), ('RearR', V((-0.62, 0.62, 1.04)))]
    sv, bv, hv = [], [], []
    for nm, c in seats:
        sv.append(seat_vf(c))
        bv.append(seat_base_vf(c))
        hv.append(harness_vf(c))
        e = empty('Seat_' + nm, c + V((0, 0, 0.02)), 'Interior', size=0.15)
        e['tx_seat'] = {'Driver': 'driver (drives the vehicle)', 'Passenger': 'front passenger',
                        'RearL': 'rear left passenger', 'RearR': 'rear right passenger'}[nm]
    mk('Int_Seats', merge_vf(*sv), 'Fabric', 'Interior', bev=(0.02, 2, 30))
    mk('Int_SeatBases', merge_vf(*bv), 'Hardware', 'Interior', bev=(0.004, 1, 30))
    mk('Int_Harnesses', merge_vf(*hv), 'Canvas', 'Interior', sharp=60)
    # ---------------- centre console: radio stack, turret fire-control grip, switch panel
    con = [box_between((-0.22, -0.82, 0.68), (0.22, 0.05, 1.02)), box_between((-0.20, -0.84, 1.02), (0.20, -0.55, 1.30))]
    mk('Int_Console', merge_vf(*con), 'Plastic', 'Interior', bev=(0.008, 1, 30))
    rad = [box_between((-0.18, -0.83, 1.04), (0.18, -0.60, 1.16)), box_between((-0.18, -0.83, 1.17), (0.18, -0.60, 1.29))]
    knobs = []
    for z in (1.10, 1.23):
        for x in (-0.13, -0.07, 0.10, 0.14):
            knobs.append(cyl_vf(V((x, -0.845, z)), 0.013, 0.02, 'Y', 10))
        knobs.append(box_between((-0.04, -0.836, z - 0.025), (0.06, -0.83, z + 0.025)))
    for x in (-0.19, 0.19):
        knobs.append(tube_vf([V((x, -0.84, 1.06)), V((x, -0.87, 1.06)), V((x, -0.87, 1.27)), V((x, -0.84, 1.27))], 0.008, 6))
    mk('Int_Radios', merge_vf(*rad), 'Paint', 'Interior', bev=(0.004, 1, 30))
    mk('Int_RadioKnobs', merge_vf(*knobs), 'Hardware', 'Interior')
    mk('Int_RadioDisplays', merge_vf(*[box_between((-0.035, -0.8365, z - 0.018), (0.055, -0.835, z + 0.018))
                                       for z in (1.10, 1.23)]), 'Screen', 'Interior')
    grip = [box_between((-0.10, -0.30, 1.02), (0.10, -0.10, 1.05)), cyl_between(V((0, -0.20, 1.05)), V((0, -0.22, 1.20)), 0.022, 12),
            box_between((-0.03, -0.25, 1.17), (0.03, -0.19, 1.24))]
    mk('Int_FireControlGrip', merge_vf(*grip), 'Housing', 'Interior', bev=(0.006, 1, 30))
    sws = [box_between((x - 0.012, -0.10, 1.02), (x + 0.012, -0.06, 1.035)) for x in (-0.15, -0.10, -0.05, 0.05, 0.10, 0.15)]
    mk('Int_Switches', merge_vf(*sws), 'SafetyRed', 'Interior')
    # ---------------- roll cage (visible through the glass)
    R = 0.025
    cage = []
    for sx in (1, -1):
        cage.append(tube_vf([V((sx * 1.05, -0.06, 0.70)), V((sx * 1.10, -0.06, 1.62)), V((sx * 0.98, -0.06, 2.34))], R, 10))
        cage.append(tube_vf([V((sx * 0.96, -0.74, 2.36)), V((sx * 0.96, 2.70, 2.36))], R, 10))
        cage.append(tube_vf([V((sx * 1.05, 1.06, 0.70)), V((sx * 1.10, 1.06, 1.62)), V((sx * 0.98, 1.06, 2.34))], R, 10))
        cage.append(tube_vf([V((sx * 0.96, -0.74, 2.36)), V((sx * 1.00, -1.02, 1.80))], R, 10))
    for y in (-0.42, 1.06):
        cage.append(tube_vf([V((-0.96, y, 2.36)), V((0.96, y, 2.36))], R, 10))
    mk('Int_RollCage', merge_vf(*cage), 'Gunmetal', 'Interior', sharp=50)
    # ---------------- gunner platform, dome light
    mk('Int_GunnerPlatform', merge_vf(box_between((-0.25, 0.20, 0.675), (0.25, 0.70, 0.82)),
                                      box_between((-0.25, 0.20, 0.82), (0.25, 0.70, 0.835))), 'Hardware', 'Interior',
       bev=(0.004, 1, 30))
    mk('Int_DomeLight', box_between((-0.10, -0.62, 2.405), (0.10, -0.52, 2.42)), 'RedLens', 'Interior')
    # ---------------- rear cargo
    crates = merge_vf(box_vf((0.30, 2.20, 0.84), (0.55, 0.40, 0.32)), box_vf((-0.30, 2.30, 0.82), (0.45, 0.60, 0.28)),
                      box_vf((0.30, 2.20, 1.07), (0.40, 0.30, 0.14)))
    mk('Int_CargoCrates', crates, 'Paint', 'Interior', bev=(0.01, 1, 30))
    # ---------------- door cards (move with the doors)
    for s, sfx in ((1, 'L'), (-1, 'R')):
        for door, y0, y1 in (('Door_F', -1.02, -0.14), ('Door_R', 0.02, 0.92)):
            d = bpy.data.objects[door + sfx]
            xi = s * (X_SIDE - T_SHELL - 0.004)
            card = [box_between((xi, y0, 0.78), (xi - s * 0.012, y1, 1.58)),
                    box_between((xi - s * 0.012, y0 + 0.15, 1.12), (xi - s * 0.08, y1 - 0.10, 1.18)),
                    box_between((xi - s * 0.012, y1 - 0.30, 1.30), (xi - s * 0.05, y1 - 0.12, 1.33))]
            mk('Int_DoorCard_%s%s' % (door[-1], sfx), merge_vf(*card), 'Plastic', 'Interior', d, bev=(0.004, 1, 30))
