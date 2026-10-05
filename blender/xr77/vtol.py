"""XR-77 VTOL system: hybrid-electric lift fan behind the cockpit (two counter-rotating rotors in a vertical duct,
superconducting motor hub fed by power conduits from the engine generators), rear-hinged dorsal intake door,
folding ventral doors with steerable louvre vanes, and wing roll-post nozzles. All driven by the VTOL channel.
"""
from .lib import *
from common import rig
from . import airframe as AF

FAN = V((0.0, -3.60, 0.0))
R_DUCT = 0.78


def hinge(ob, pivot, typ, axis, opn, channel, stage, desc, kind='part', **kw):
    set_origin(ob, pivot)
    rig.motion(ob, typ, axis, opn, channel, stage, kind, desc, **kw)


def rotor_vf(z, n, r0, r1, chord, tw0, tw1, sense=1, th=0.012):
    parts = []
    for k in range(n):
        a = 2 * pi * k / n
        loops = []
        for j in range(6):
            r = r0 + (r1 - r0) * j / 5
            tw = radians(tw0 + (tw1 - tw0) * j / 5) * sense
            c = chord * (1 - 0.2 * j / 5)
            L = []
            for (u, v) in ((-c / 2, -th / 2), (c / 2, -th / 2), (c / 2, th / 2), (-c / 2, th / 2)):
                tt = u * cos(tw) - v * sin(tw)          # tangential
                zz = u * sin(tw) + v * cos(tw)          # axial
                L.append(V((FAN.x + r * cos(a) - tt * sin(a), FAN.y + r * sin(a) + tt * cos(a), z + zz)))
            loops.append(L)
        parts.append(loft(loops))
    return merge_vf(*parts)


def build():
    # ------------------------------------------------------------ duct structure
    rings = [orient(lathe_vf([(R_DUCT - 0.035, z), (R_DUCT + 0.01, z), (R_DUCT + 0.01, z + 0.05),
                              (R_DUCT - 0.035, z + 0.05), (R_DUCT - 0.035, z)], 56, cap0=False, cap1=False),
                    (FAN.x, FAN.y, 0), 'Z') for z in (1.76, 2.12, 2.48)]
    mk('LiftFan_DuctRings', merge_vf(*rings), 'Primer', 'VTOL', smooth=False)
    bell = lathe_vf([(R_DUCT - 0.005, 2.50), (R_DUCT + 0.03, 2.545), (R_DUCT + 0.09, 2.555), (R_DUCT + 0.09, 2.50),
                     (R_DUCT - 0.005, 2.50)], 56, cap0=False, cap1=False)
    mk('LiftFan_Bellmouth', orient(bell, (FAN.x, FAN.y, 0), 'Z'), 'Titanium', 'VTOL', sharp=35)
    # motor hub (fixed), struts, stators, cooling fins, power conduits
    hub = lathe_vf([(0.0, 1.68), (0.20, 1.70), (0.225, 1.78), (0.225, 2.15), (0.06, 2.15), (0.06, 2.26), (0.0, 2.26)], 40)
    mk('LiftFan_Motor', orient(hub, (FAN.x, FAN.y, 0), 'Z'), 'Engine', 'VTOL', sharp=35)
    fins = []
    for k in range(24):
        a = 2 * pi * k / 24
        fins.append(prism([V((FAN.x + 0.225 * cos(a), FAN.y + 0.225 * sin(a), 1.80)),
                           V((FAN.x + 0.255 * cos(a), FAN.y + 0.255 * sin(a), 1.80)),
                           V((FAN.x + 0.255 * cos(a), FAN.y + 0.255 * sin(a), 2.08)),
                           V((FAN.x + 0.225 * cos(a), FAN.y + 0.225 * sin(a), 2.08))],
                          V((-sin(a), cos(a), 0)) * 0.006))
    mk('LiftFan_MotorFins', merge_vf(*fins), 'Alu', 'VTOL', smooth=False)
    st = []
    for k in range(12):
        a = 2 * pi * k / 12 + 0.13
        p0 = V((FAN.x + 0.22 * cos(a), FAN.y + 0.22 * sin(a), 1.88))
        p1 = V((FAN.x + 0.775 * cos(a), FAN.y + 0.775 * sin(a), 1.88))
        t = V((-sin(a), cos(a), 0))
        q = [p0 - t * 0.008 - V((0, 0, 0.07)), p1 - t * 0.008 - V((0, 0, 0.07)), p1 + t * 0.008 + V((0, 0, 0.07)),
             p0 + t * 0.008 + V((0, 0, 0.07))]
        st.append(prism(q, t * 0.012))
    mk('LiftFan_Stators', merge_vf(*st), 'Titanium', 'VTOL', smooth=False)
    cond = []
    for x0 in (-0.12, 0.12):
        path = [V((x0, FAN.y + 0.18, 1.98)), V((x0 * 1.5, FAN.y + 0.62, 2.0)), V((x0 * 2, FAN.y + 0.76, 2.05)),
                V((x0 * 2.2, FAN.y + 0.775, 2.40))]
        cond.append(tube_vf(path, 0.028, 10))
    mk('LiftFan_PowerConduits', merge_vf(*cond), 'CableOrange', 'VTOL')
    clamps = [cyl_vf((x * 2.1, FAN.y + 0.77, 2.25), 0.04, 0.03, 'Z', 12) for x in (-0.12, 0.12)]
    mk('LiftFan_ConduitClamps', merge_vf(*clamps), 'Steel', 'VTOL')
    # ------------------------------------------------------------ rotors (spin while VTOL is active)
    r1 = rotor_vf(2.30, 18, 0.20, 0.755, 0.15, 42, 18, 1)
    sp = lathe_vf([(0.0, 2.47), (0.12, 2.44), (0.20, 2.38), (0.205, 2.22), (0.0, 2.22)], 32)
    rot1 = mk('LiftFan_Rotor1', merge_vf(r1, orient(sp, (FAN.x, FAN.y, 0), 'Z')), 'Titanium', 'VTOL', sharp=30)
    hinge(rot1, (FAN.x, FAN.y, 2.30), 'spin', 'Z', None, 'VTOL', (0.6, 1.0), 'lift fan upper rotor (spins in VTOL)',
          speed=70.0)
    r2 = rotor_vf(2.03, 16, 0.20, 0.755, 0.15, -40, -18, -1)
    hb2 = lathe_vf([(0.0, 2.10), (0.205, 2.10), (0.205, 1.97), (0.0, 1.97)], 32)
    rot2 = mk('LiftFan_Rotor2', merge_vf(r2, orient(hb2, (FAN.x, FAN.y, 0), 'Z')), 'Titanium', 'VTOL', sharp=30)
    hinge(rot2, (FAN.x, FAN.y, 2.03), 'spin', 'Z', None, 'VTOL', (0.6, 1.0), 'lift fan lower rotor (counter-rotating)',
          speed=-70.0)
    # ------------------------------------------------------------ louvre vanes (bottom) - open to vertical in VTOL
    for k in range(6):
        y = -4.22 + k * 0.24
        half = 0.735
        v = merge_vf(box_between((-half, y - 0.10, 1.4875), (half, y + 0.10, 1.5125)),
                     cyl_vf((-half - 0.02, y, 1.50), 0.016, 0.04, 'X', 10), cyl_vf((half + 0.02, y, 1.50), 0.016, 0.04, 'X', 10))
        vane = mk('LiftFan_Vane_%d' % (k + 1), v, 'SkinDark', 'VTOL', bev=(0.004, 1, 30))
        hinge(vane, (0.0, y, 1.50), 'rotate', 'X', -72, 'VTOL', (0.35, 0.8),
              'lift fan louvre vane: swings to near-vertical in VTOL (vectors the fan thrust)')
    # vane side rails (fixed)
    rails = [box_between((x - 0.02, -4.36, 1.46), (x + 0.02, -2.84, 1.62)) for x in (-0.765, 0.765)]
    mk('LiftFan_VaneRails', merge_vf(*rails), 'Hardware', 'VTOL')
    # ------------------------------------------------------------ doors
    top = AF.DOORS['LiftFan_DoorTop']
    hinge(top, AF.hinge_line((-0.86, -2.497), (0.86, -2.497), 'top')[0], 'rotate', 'X', -70, 'VTOL', (0.0, 0.45),
          'lift fan intake door: rear-hinged, opens 70 deg (front rises)')
    ribs = []
    for x in (-0.55, 0.0, 0.55):
        path = [V((x, y, body_top(x, y) - 0.045)) for y in cosspace(-4.20, -2.62, 8, (False, False))]
        ribs.append(sweep_vf(path, rect2(0.03, 0.04)))
    for y in (-4.0, -3.3, -2.8):
        path = [V((x, y, body_top(x, y) - 0.045)) for x in cosspace(-0.78, 0.78, 8, (False, False))]
        ribs.append(sweep_vf(path, rect2(0.03, 0.04)))
    mk('LiftFan_DoorTop_Ribs', merge_vf(*ribs), 'BayGrey', 'VTOL', top)
    act = [cyl_between((x, -2.62, body_top(x, -2.62) - 0.08), (x, -3.05, body_top(x, -3.05) - 0.06), 0.022, 10)
           for x in (-0.45, 0.45)]
    mk('LiftFan_DoorTop_Actuators', merge_vf(*act), 'Chrome', 'VTOL', top)
    for s in (1, -1):
        d = AF.DOORS['LiftFan_DoorBot_' + ('L' if s > 0 else 'R')]
        hx = s * 0.86
        hinge(d, AF.hinge_line((s * 0.863, -4.40), (s * 0.863, -2.70), 'bottom')[0], 'rotate', 'Y', -92 * s, 'VTOL', (0.05, 0.5),
              'lift fan ventral door: hinged on its outer edge, folds down 92 deg')
        rb = [box_between((s * 0.06, y - 0.015, body_bot(0.4, y) + 0.022), (s * 0.80, y + 0.015, body_bot(0.4, y) + 0.06))
              for y in (-4.2, -3.55, -2.9)]
        rb = [(vv, ff) for vv, ff in rb]
        mk(d.name + '_Ribs', merge_vf(*rb), 'BayGrey', 'VTOL', d)
    # ------------------------------------------------------------ roll posts (wing undersides)
    for s in (1, -1):
        S_ = 'L' if s > 0 else 'R'
        cx, cy = s * 4.55, 4.75
        noz = lathe_vf([(0.16, 2.09), (0.165, 2.04), (0.13, 2.02), (0.125, 2.035), (0.15, 2.09), (0.16, 2.09)], 32,
                       cap0=False, cap1=False)
        mk('RollPost_Nozzle_' + S_, orient(noz, (cx, cy, 0), 'Z'), 'BurntTi', 'VTOL', sharp=35)
        vn = [box_between((cx - 0.125, cy + k * 0.06 - 0.004, 2.03), (cx + 0.125, cy + k * 0.06 + 0.004, 2.085))
              for k in (-2, -1, 0, 1, 2)]
        mk('RollPost_Vanes_' + S_, merge_vf(*vn), 'Inconel', 'VTOL')
        d = AF.DOORS['RollPost_Door_' + S_]
        hinge(d, AF.hinge_line((cx + s * 0.173, cy - 0.17), (cx + s * 0.173, cy + 0.17), 'bottom')[0], 'rotate', 'Y', -95 * s, 'VTOL', (0.1, 0.5),
              'roll-post nozzle door: opens so bled engine air can control roll in the hover')
        rig.point('RollPost_' + S_, (cx, cy, 2.0), 'effect', direction=(0, 0, -1), effect='roll-control jet (VTOL)')
    rig.point('LiftFan_Exhaust', (FAN.x, FAN.y, 1.40), 'effect', direction=(0, 0, -1),
              effect='lift fan downwash (dust / heat haze under the aircraft in VTOL)')


def wing_z_lower(x, y):
    from .airframe import wing_z
    return wing_z(x, y, upper=False)
