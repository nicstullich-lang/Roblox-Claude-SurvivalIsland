"""XR-77 sensors + reconnaissance: opening radome with a tilted AESA array, chin EO targeting window, IRST dome,
distributed IR apertures (DAS), chine camera bays (cameras lower out), belly recon ball turret, air-data probes,
blade antennas.
"""
from .lib import *
from common import rig
from . import airframe as AF


def hinge(ob, pivot, typ, axis, opn, channel, stage, desc, kind='part', **kw):
    set_origin(ob, pivot)
    rig.motion(ob, typ, axis, opn, channel, stage, kind, desc, **kw)


def build_radar():
    rad = bpy.data.objects['Radome']
    w = W_(Y_RADOME)
    # pitot / air-data probe on the radome tip (moves with the radome)
    probe = ylathe_simple([(0.0, -13.08), (0.006, -13.05), (0.010, -12.90), (0.016, -12.62), (0.030, -12.38),
                           (0.0, -12.36)], (0.0, 0.0, Zc_(Y_NOSE) + 0.005))
    mk('Radome_Probe', probe, 'Titanium', 'Sensors', rad, sharp=40)
    ring = ylathe_simple([(0.026, -12.40), (0.04, -12.40), (0.04, -12.37), (0.026, -12.37), (0.026, -12.40)],
                         (0.0, 0.0, Zc_(Y_NOSE) + 0.005), ring=True)
    mk('Radome_ProbeCollar', ring, 'SkinDark', 'Sensors', rad)
    hinge(rad, (-w, Y_RADOME, Zc_(Y_RADOME)), 'rotate', 'Z', -100, 'Radome', (0, 1),
          'radome: hinged on the right side, swings 100 deg to expose the AESA radar')
    hb = merge_vf(*[cyl_vf((-w + 0.012, Y_RADOME + 0.012, Zc_(Y_RADOME) + dz), 0.014, 0.025, 'Z', 12) for dz in (-0.012, 0.012)])
    mk('Radome_HingeKnuckles', hb, 'Steel', 'Sensors')
    # AESA array: tilted back 25 deg, elliptical face with T/R tile grid, back structure, cooling lines
    c = V((0.0, -10.86, Zc_(-10.86) + 0.04))
    tilt = Matrix.Translation(c) @ Matrix.Rotation(radians(25), 4, 'X')
    ax, az = 0.42, 0.24
    face = ellipse2(ax, az, 40)
    plate = xform_vf(prism([V((p[0], 0.0, p[1])) for p in face], (0, 0.05, 0)), tilt)
    mk('Radar_Array', plate, 'Radar', 'Sensors', bev=(0.006, 1, 30))
    tiles = []
    for i in range(-10, 11):
        for j in range(-6, 7):
            x, z = i * 0.038, j * 0.034
            if (x / (ax - 0.03)) ** 2 + (z / (az - 0.03)) ** 2 < 1:
                tiles.append(xform_vf(box_vf((x, -0.004, z), (0.030, 0.008, 0.026)), tilt))
    mk('Radar_Tiles', merge_vf(*tiles), 'Gunmetal', 'Sensors', smooth=False)
    back = merge_vf(xform_vf(box_vf((0, 0.12, 0), (0.30, 0.14, 0.20)), tilt),
                    xform_vf(cyl_vf((0, 0.26, 0), 0.07, 0.16, 'Y', 16), tilt))
    mk('Radar_Backplane', back, 'Hardware', 'Sensors', bev=(0.006, 1, 30))
    cool = [tube_vf([tilt @ V((x, 0.06, -0.18)), tilt @ V((x, 0.25, -0.22)), V((x, Y_RADOME + 0.01, Zc_(Y_RADOME) - 0.18))],
                    0.012, 8) for x in (-0.12, 0.12)]
    mk('Radar_Coolant', merge_vf(*cool), 'Copper', 'Sensors')
    bulk = merge_vf(box_between((-0.32, Y_RADOME + 0.0, 1.78), (0.32, Y_RADOME + 0.03, 2.32)))
    mk('Radar_Bulkhead', bulk, 'Primer', 'Sensors')
    boxes = [box_between((x - 0.09, Y_RADOME - 0.16, z - 0.07), (x + 0.09, Y_RADOME - 0.0, z + 0.07))
             for x, z in ((-0.22, 1.86), (0.22, 1.86), (-0.22, 2.20), (0.22, 2.20))]
    mk('Radar_LRUs', merge_vf(*boxes), 'Hardware', 'Sensors', bev=(0.005, 1, 30))
    rig.point('Sensor_Radar', c, 'sensor', direction=(0, -1, 0), note='AESA radar boresight (lock-on cone origin)')


def ylathe_simple(profile, c, ring=False, n=20):
    prof = list(profile)
    return orient(lathe_vf(prof, n, cap0=not ring, cap1=not ring), c, 'Y')


def build_eo():
    # chin EO targeting system: faceted sapphire windows in a low housing (ahead of the nose gear well)
    cx, cy = -0.05, -10.44
    zb = body_bot(cx, cy)
    base = [(cx + 0.13 * cos(a), cy + 0.10 * sin(a)) for a in [2 * pi * k / 7 + pi / 2 for k in range(7)]]
    low = [(cx + 0.075 * cos(a), cy + 0.06 * sin(a)) for a in [2 * pi * k / 7 + pi / 2 for k in range(7)]]
    V0 = [V((p[0], p[1], zb + 0.01)) for p in base]
    V1 = [V((p[0], p[1], zb - 0.085)) for p in low]
    F = [tuple(range(7)), tuple(range(7, 14))[::-1]] + [(i, (i + 1) % 7, 7 + (i + 1) % 7, 7 + i) for i in range(7)]
    mk('EOTS_Window', (V0 + V1, F), 'SensorGlass', 'Sensors', smooth=False)
    fr = [cyl_between(V0[i], V1[i], 0.006, 6) for i in range(7)]
    mk('EOTS_Frame', merge_vf(*fr), 'SkinDark', 'Sensors')
    rig.point('Sensor_EOTS', (cx, cy, zb - 0.06), 'sensor', direction=(0, -0.5, -1), note='electro-optical targeting camera')
    # IRST dome ahead of the canopy
    iy = -9.90
    iz = body_top(0.0, iy)
    dome = lathe_vf([(0.0, 0.11), (0.06, 0.10), (0.095, 0.06), (0.11, 0.0), (0.11, -0.04), (0.0, -0.04)], 24)
    mk('IRST_Dome', orient(dome, (0.0, iy, iz), 'Z'), 'SensorGlass', 'Sensors', sharp=40)
    mk('IRST_Base', orient(lathe_vf([(0.0, 0.0), (0.135, 0.0), (0.12, 0.02), (0.0, 0.02)], 24), (0.0, iy, iz - 0.012), 'Z'),
       'SkinDark', 'Sensors')
    rig.point('Sensor_IRST', (0.0, iy, iz + 0.08), 'sensor', direction=(0, -1, 0), note='infrared search and track')
    # distributed aperture IR windows (flush, 6 around the aircraft)
    das = [((-0.60, -9.45), 'bottom'), ((0.0, 6.6), 'top'), ((0.0, 7.4), 'bottom')]
    for s in (1, -1):
        das.append(((s * 0.62, -9.1), 'top'))
    parts, frames = [], []
    for (p, proj) in das:
        vf = skin_patch(AF.CASTER, circle2(0.055, 16, p[0], p[1]), proj, t=0.004, lift=0.002, spacing=0.03)
        parts.append(vf)
        vf = skin_patch(AF.CASTER, circle2(0.072, 20, p[0], p[1]), proj, t=0.003, lift=0.0012,
                        holes=[circle2(0.055, 16, p[0], p[1])], spacing=0.03)
        frames.append(vf)
    mk('DAS_Windows', merge_vf(*parts), 'SensorGlass', 'Sensors', smooth=False)
    mk('DAS_Rims', merge_vf(*frames), 'SkinDark', 'Sensors', smooth=False)
    # air-data: AoA vanes + static ports on the nose sides
    van = []
    for s in (1, -1):
        y, z = -10.35, Zc_(-10.35) + 0.10
        x = s * (W_(-10.35) * 0.55)
        z = body_top(abs(x), y)
        van.append(cyl_between((x, y, z - 0.01), (x + s * 0.02, y, z + 0.03), 0.008, 8))
        van.append(prism([V((x + s * 0.02, y - 0.01, z + 0.025)), V((x + s * 0.02, y + 0.05, z + 0.025)),
                          V((x + s * 0.025, y + 0.05, z + 0.075)), V((x + s * 0.025, y + 0.02, z + 0.075))], (0.004 * s, 0, 0)))
    mk('AirData_AoAVanes', merge_vf(*van), 'Titanium', 'Sensors', smooth=False)


def build_recon():
    for s in (1, -1):
        S_ = 'L' if s > 0 else 'R'
        d = AF.DOORS['ChineCam_Door_' + S_]
        hx = s * 0.56
        hinge(d, AF.hinge_line((s * 0.557, -8.55), (s * 0.557, -7.15), 'bottom')[0], 'rotate', 'Y', 100 * s, 'Recon', (0.0, 0.4),
              'chine camera bay door: swings down')
        xc = s * 0.68
        z0 = 1.99
        cradle = merge_vf(box_between((xc - 0.10, -8.45, z0), (xc + 0.10, -7.25, z0 + 0.035)))
        lenses, bodies = [], []
        for k, yy in enumerate((-8.25, -7.85, -7.45)):
            cam = rot_about(box_vf((xc, yy, z0 - 0.05), (0.13, 0.18, 0.10)), (xc, yy, z0), 'Y', -18 * s)
            bodies.append(cam)
            lens = rot_about(cyl_vf((xc, yy, z0 - 0.112), 0.045, 0.026, 'Z', 18), (xc, yy, z0), 'Y', -18 * s)
            lenses.append(lens)
        cr = mk('Recon_ChineCam_' + S_, cradle, 'Hardware', 'Sensors', bev=(0.005, 1, 30))
        mk('Recon_ChineCam_Bodies_' + S_, merge_vf(*bodies), 'Gunmetal', 'Sensors', cr, bev=(0.006, 1, 30))
        mk('Recon_ChineCam_Lenses_' + S_, merge_vf(*lenses), 'SensorGlass', 'Sensors', cr)
        hinge(cr, (xc, -7.85, z0), 'translate', 'Z', -0.16, 'Recon', (0.4, 1.0),
              'reconnaissance camera cradle: lowers out of the chine bay')
        rig.point('Camera_Chine_' + S_, (xc + s * 0.04, -7.85, z0 - 0.29), 'camera', attach=cr,
                  direction=(s * 0.31, 0, -0.95), note='oblique reconnaissance camera')
    # belly recon ball turret
    for nm, hx, ang in (('Recon_Door_L', 0.40, -100), ('Recon_Door_R', -0.40, 100)):
        d = AF.DOORS[nm]
        hinge(d, AF.hinge_line((hx * 1.0075, -2.55), (hx * 1.0075, -1.75), 'bottom')[0], 'rotate', 'Y', ang, 'Recon', (0.0, 0.4),
              'recon turret door: swings down')
    mast = merge_vf(cyl_vf((0, -2.15, 1.96), 0.30, 0.04, 'Z', 28), cyl_between((0, -2.15, 1.95), (0, -2.15, 1.76), 0.07, 16))
    m = mk('Recon_Mast', mast, 'GearWhite', 'Sensors', sharp=35)
    ball = lathe_vf([(0.0, 1.78), (0.10, 1.77), (0.19, 1.71), (0.22, 1.60), (0.19, 1.49), (0.10, 1.43), (0.0, 1.42)], 28)
    yb = mk('Recon_Ball', orient(ball, (0, -2.15, 0), 'Z'), 'SkinDark', 'Sensors', m, sharp=40)
    head = merge_vf(cyl_between((-0.13, -2.15, 1.60), (0.13, -2.15, 1.60), 0.10, 20))
    hd = mk('Recon_Head', head, 'Gunmetal', 'Sensors', yb, sharp=35)
    win = merge_vf(cyl_between((0.0, -2.25, 1.60), (0.0, -2.262, 1.60), 0.07, 20),
                   cyl_between((0.08, -2.24, 1.64), (0.08, -2.252, 1.64), 0.025, 12))
    mk('Recon_HeadWindows', win, 'SensorGlass', 'Sensors', hd)
    hinge(hd, (0.0, -2.15, 1.60), 'aim_pitch', 'X', None, None, (0, 1), 'recon head tilt (+ = look down, Blender X)',
          min=-10, max=90, speed=60)
    hinge(yb, (0.0, -2.15, 1.60), 'aim_yaw', 'Z', None, None, (0, 1), 'recon ball pan (360 deg)', speed=60)
    hinge(m, (0.0, -2.15, 1.96), 'translate', 'Z', -0.45, 'Recon', (0.4, 1.0), 'recon mast: lowers the ball turret')
    rig.point('Camera_ReconBall', (0.0, -2.27, 1.60), 'camera', attach=hd, direction=(0, -1, 0),
              note='stabilised long-range reconnaissance camera (zoom view)')


def build_antennas():
    parts = []
    for (y, top) in ((2.4, True), (3.9, True), (-6.2, False), (7.9, False), (-1.0, False)):
        x = 0.0 if y > -5 else 0.0
        if top:
            z = body_top(x, y)
            q = [V((x, y + 0.16, z - 0.01)), V((x, y - 0.06, z - 0.01)), V((x, y + 0.06, z + 0.16)), V((x, y + 0.14, z + 0.16))]
        else:
            z = body_bot(x, y)
            q = [V((x, y + 0.16, z + 0.01)), V((x, y - 0.06, z + 0.01)), V((x, y + 0.06, z - 0.14)), V((x, y + 0.14, z - 0.14))]
        parts.append(prism([p - V((0.005, 0, 0)) for p in q], (0.01, 0, 0)))
    mk('Antenna_Blades', merge_vf(*parts), 'SkinDark', 'Sensors', bev=(0.002, 1, 30))
    sat = skin_patch(AF.CASTER, rrect2(0.40, 0.55, 0.05, 3, 0.0, 3.15), 'top', t=0.004, lift=0.0025, spacing=0.05)
    mk('Antenna_SatcomPanel', sat, 'SkinAlt', 'Sensors', smooth=False)


def build():
    build_radar()
    build_eo()
    build_recon()
    build_antennas()
