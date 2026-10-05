"""XR-77 defensive + emergency systems and exterior lighting:
flare / chaff magazines, pop-out laser countermeasure (DIRCM) turrets, towed decoy in a tail stinger, emergency
arrestor hook, ram-air turbine, navigation / tail / strobe / formation lights, radar-warning antennas.
"""
from .lib import *
from common import rig
from . import airframe as AF


def hinge(ob, pivot, typ, axis, opn, channel, stage, desc, kind='part', **kw):
    set_origin(ob, pivot)
    rig.motion(ob, typ, axis, opn, channel, stage, kind, desc, **kw)


def build_flares():
    for s in (1, -1):
        S_ = 'L' if s > 0 else 'R'
        d = AF.DOORS['Flares_Door_' + S_]
        hx = s * 1.36
        hinge(d, AF.hinge_line((s * 1.363, 7.45), (s * 1.363, 8.55), 'bottom')[0], 'rotate', 'Y', -100 * s, 'Countermeasures', (0.0, 0.5),
              'countermeasure magazine door: drops open to expose the flare / chaff cells')
        x0, x1 = (0.95, 1.33) if s > 0 else (-1.33, -0.95)
        blk = box_between((x0, 7.48, 1.66), (x1, 8.52, 1.80))
        mk('Flares_Magazine_' + S_, blk, 'Hardware', 'Defense', bev=(0.004, 1, 30))
        cells, caps = [], []
        for i in range(4):
            for j in range(9):
                cx = x0 + 0.05 + i * (x1 - x0 - 0.10) / 3
                cy = 7.56 + j * 0.112
                cells.append(cyl_vf((cx, cy, 1.655), 0.034, 0.012, 'Z', 10))
                caps.append(cyl_vf((cx, cy, 1.648), 0.026, 0.004, 'Z', 10))
        mk('Flares_Cells_' + S_, merge_vf(*cells), 'Steel', 'Defense')
        mk('Flares_Caps_' + S_, merge_vf(*caps), 'Red' if s > 0 else 'Yellow', 'Defense')
        rig.point('Flares_' + S_, (s * 1.14, 8.0, 1.55), 'effect', direction=(s * 0.3, 0.2, -1),
                  effect='flare / chaff release (only while the magazine door is open)')


def build_dircm():
    for nm, y, up in (('Top', 6.30, 1), ('Bot', 6.85, -1)):
        z0 = body_top(0.0, y) if up > 0 else body_bot(0.0, y)
        base_z = z0 - up * 0.17
        housing = cyl_vf((0.0, y, base_z + up * 0.07), 0.13, 0.14, 'Z', 24)
        lift = mk('DIRCM_%s_Lift' % nm, housing, 'SkinDark', 'Defense', sharp=35)
        ball = lathe_vf([(0.0, 0.0), (0.09, 0.012), (0.12, 0.06), (0.11, 0.11), (0.0, 0.13)], 20)
        if up < 0:
            ball = mirror_vf(ball, 2)
        head = mk('DIRCM_%s_Head' % nm, orient(ball, (0.0, y, base_z + up * 0.14), 'Z'), 'SkinDark', 'Defense', lift, sharp=40)
        win = cyl_between((0.0, y - 0.105, base_z + up * 0.20), (0.0, y - 0.125, base_z + up * 0.20), 0.04, 14)
        mk('DIRCM_%s_Window' % nm, win, 'SensorGlass', 'Defense', head)
        hinge(head, (0.0, y, base_z + up * 0.14), 'aim_yaw', 'Z', None, None, (0, 1),
              'laser countermeasure head: tracks incoming missiles (360 deg)', speed=360)
        hinge(lift, (0.0, y, base_z), 'translate', 'Z', up * 0.17, 'Countermeasures', (0.2, 0.8),
              'DIRCM turret: rises out of its flush well')
        rig.point('DIRCM_' + nm, (0.0, y - 0.13, base_z + up * 0.37), 'effect', attach=head, direction=(0, -1, 0),
                  effect='invisible jamming laser (show a faint beam toward the incoming missile)')


def build_decoy():
    y0, y1, z = 10.70, 11.48, Zc_(Y_TAILEND)
    tube = merge_vf(orient(lathe_vf([(0.0, y0), (0.19, y0), (0.19, y1 - 0.04), (0.17, y1), (0.15, y1), (0.15, y0 + 0.05),
                                     (0.0, y0 + 0.05)], 28), (0, 0, z), 'Y'))
    mk('Decoy_Stinger', tube, 'Ceramic', 'Defense', sharp=35)
    cap = orient(lathe_vf([(0.0, y1 - 0.005), (0.152, y1 - 0.005), (0.152, y1 + 0.02), (0.0, y1 + 0.03)], 28), (0, 0, z), 'Y')
    c = mk('Decoy_Cap', cap, 'SkinDark', 'Defense')
    hinge(c, (0.0, y1, z + 0.152), 'rotate', 'X', 110, 'Countermeasures', (0.0, 0.4),
          'decoy tube end cap: flips up to let the towed decoy out')
    pod = merge_vf(orient(lathe_vf([(0.0, y0 + 0.10), (0.10, y0 + 0.14), (0.11, y1 - 0.20), (0.06, y1 - 0.06),
                                    (0.0, y1 - 0.05)], 20), (0, 0, z), 'Y'))
    fins = [prism([V((0.10 * cos(a), y1 - 0.40, z + 0.10 * sin(a))), V((0.14 * cos(a), y1 - 0.30, z + 0.14 * sin(a))),
                   V((0.14 * cos(a), y1 - 0.14, z + 0.14 * sin(a))), V((0.10 * cos(a), y1 - 0.14, z + 0.10 * sin(a)))],
                  V((-sin(a), 0, cos(a))) * 0.006) for a in [pi / 4 + k * pi / 2 for k in range(4)]]
    p = mk('Decoy_Pod', merge_vf(pod, *fins), 'Missile', 'Defense', sharp=35)
    hinge(p, (0.0, y0 + 0.10, z), 'translate', 'Y', 0.95, 'Countermeasures', (0.4, 1.0),
          'towed radar decoy: slides out aft (the game then trails it on a cable)')
    rig.point('Decoy_Tow', (0.0, y1 + 0.9, z), 'effect', attach=p, direction=(0, 1, 0),
              effect='towed decoy: attach a long cable + drag the pod behind the aircraft')


def build_hook():
    z = body_bot(0.0, 8.65) + 0.10
    bar = merge_vf(cyl_between((0.0, 8.66, z), (0.0, 9.80, Zb_(9.80) + 0.07), 0.035, 12),
                   box_between((-0.05, 9.72, Zb_(9.80) + 0.02), (0.05, 9.88, Zb_(9.80) + 0.11)))
    h = mk('TailHook', bar, 'Yellow', 'Defense', bev=(0.004, 1, 30))
    stripes = [cyl_between((0.0, yy, z + (Zb_(9.8) + 0.07 - z) * (yy - 8.66) / 1.14), (0.0, yy + 0.08, z + (Zb_(9.8) + 0.07 - z) * (yy + 0.08 - 8.66) / 1.14), 0.036, 12)
               for yy in (8.9, 9.2, 9.5)]
    mk('TailHook_Stripes', merge_vf(*stripes), 'Black', 'Defense', h)
    hinge(h, (0.0, 8.66, z), 'rotate', 'X', -38, 'Emergency', (0.0, 1.0),
          'emergency arrestor hook: drops 38 deg to catch a runway cable')
    mk('TailHook_Pivot', cyl_vf((0.0, 8.66, z), 0.05, 0.12, 'X', 14), 'Steel', 'Defense')


def build_rat():
    d = AF.DOORS['RAT_Door']
    hinge(d, AF.hinge_line((-1.097, 0.15), (-1.097, 0.75), 'bottom')[0], 'rotate', 'Y', -100, 'Emergency', (0.0, 0.4),
          'ram-air turbine door: drops open')
    x, z = -1.33, 1.85
    arm = merge_vf(box_between((x - 0.035, 0.20, z - 0.03), (x + 0.035, 0.66, z + 0.03)), cyl_vf((x, 0.20, z), 0.04, 0.10, 'X', 12))
    a = mk('RAT_Arm', arm, 'GearWhite', 'Defense', bev=(0.004, 1, 30))
    hub = cyl_vf((x, 0.66, z - 0.05), 0.05, 0.08, 'Z', 14)
    blades = [box_between((x - 0.20, 0.645, z - 0.075), (x + 0.20, 0.675, z - 0.065))]
    prop = mk('RAT_Prop', merge_vf(hub, *blades), 'Black', 'Defense', a, bev=(0.003, 1, 30))
    hinge(prop, (x, 0.66, z - 0.05), 'spin', 'Z', None, 'Emergency', (0.6, 1.0),
          'ram-air turbine propeller (windmills in the airflow)', speed=40.0)
    hinge(a, (x, 0.20, z), 'rotate', 'X', -90, 'Emergency', (0.3, 0.9),
          'ram-air turbine arm: swings down into the airflow for emergency power')


def strip_patch(name, pts2d, proj, w, mat, parent=None):
    a, b = V((*pts2d[0], 0)), V((*pts2d[1], 0))
    d = (b - a).normalized()
    n = V((-d.y, d.x, 0)) * (w / 2)
    poly = [(a + n).to_2d(), (b + n).to_2d(), (b - n).to_2d(), (a - n).to_2d()]
    vf = skin_patch(AF.CASTER, poly, proj, t=0.003, lift=0.0025, spacing=0.05)
    return mk(name, vf, mat, 'Lights', parent, smooth=False)


def build_lights():
    for s in (1, -1):
        S_ = 'L' if s > 0 else 'R'
        wt = bpy.data.objects['Wingtip_' + S_]
        col = 'NavRed' if s > 0 else 'NavGreen'
        y, z = 6.62, ZW
        lens = orient(lathe_vf([(0.0, 0.0), (0.035, 0.0), (0.03, 0.025), (0.0, 0.035)], 14), (s * (WING_TIP_X - 0.005), y, z), 'X' if s > 0 else '-X')
        mk('NavLight_' + S_, lens, col, 'Lights', wt)
        rig.light('Light_Nav_' + S_, (s * WING_TIP_X, y, z), 'point', (1.0, 0.1, 0.08) if s > 0 else (0.1, 1.0, 0.3), 6.0,
                  'navigation', attach=wt, brightness=1.5, neon_materials=[col])
        rwr = orient(lathe_vf([(0.0, 0.0), (0.04, 0.0), (0.03, 0.10), (0.0, 0.12)], 12), (s * (WING_TIP_X - 0.005), 6.3, z), 'X' if s > 0 else '-X')
        mk('RWR_Wingtip_' + S_, rwr, 'SkinDark', 'Lights', wt)
        tl = bpy.data.objects['Tail_' + S_]
        span, thick = tail_axes(s)
        tip = V((s * NAC_X, 0, TAIL_ROOT_Z)) + span * (TAIL_SPAN - 0.02)
        tip.y = TAIL_TE0 + TAIL_SPAN * 0.268 - 0.03
        mk('TailLight_' + S_, cyl_between(tip + V((0, -0.02, 0)), tip + V((0, 0.03, 0)), 0.018, 10), 'Strobe', 'Lights', tl)
        rig.light('Light_Tail_' + S_, tip, 'point', (1.0, 1.0, 1.0), 5.0, 'navigation', attach=tl, brightness=1.0,
                  neon_materials=['Strobe'])
        # formation strips: forward fuselage near the chine, tail outer face, outer wing top
        ys = (-9.70, -8.75)
        strip_patch('Formation_Nose_' + S_, [(s * (W_(ys[0]) - 0.10), ys[0]), (s * (W_(ys[1]) - 0.11), ys[1])], 'top', 0.035,
                    'Formation')
        p0 = V((s * NAC_X, 0, TAIL_ROOT_Z)) + span * 0.6
        p1 = V((s * NAC_X, 0, TAIL_ROOT_Z)) + span * 1.6
        strip_patch('Formation_Tail_' + S_, [(7.75, p0.z), (8.35, p1.z)], 'left' if s > 0 else 'right', 0.035, 'Formation', tl)
        strip_patch('Formation_Wing_' + S_, [(s * 6.35, 5.25), (s * 6.95, 5.90)], 'top', 0.035, 'Formation', wt)
    for nm, y, top in (('Top', 4.60, True), ('Bot', 8.30, False)):
        z = body_top(0, y) if top else body_bot(0, y)
        dome = lathe_vf([(0.0, 0.0), (0.05, 0.0), (0.045, 0.025), (0.0, 0.035)], 14)
        if not top:
            dome = mirror_vf(dome, 2)
        mk('Strobe_' + nm, orient(dome, (0, y, z - (0.004 if top else -0.004)), 'Z'), 'Strobe', 'Lights')
        rig.light('Light_Strobe_' + nm, (0, y, z + (0.03 if top else -0.03)), 'point', (1.0, 0.25, 0.2), 14.0,
                  'anticollision', brightness=3.0, neon_materials=['Strobe'])


def build():
    build_flares()
    build_dircm()
    build_decoy()
    build_hook()
    build_rat()
    build_lights()
