"""XR-77 flight controls + variable geometry + small service doors:
drooping outer wing panels (XB-70 style compression-lift tips, HighSpeed channel) with visible hinge fittings,
flaperons, ailerons, swept leading-edge flaps, all-moving canted tails, dorsal speed brakes, refuel receptacle,
avionics bay doors. Hinges that are not on a model axis use a vector axis (rig format allows any direction).
"""
from .lib import *
from common import rig
from . import airframe as AF


def hinge(ob, pivot, typ, axis, opn, channel, stage, desc, kind='part', **kw):
    set_origin(ob, pivot)
    rig.motion(ob, typ, axis, opn, channel, stage, kind, desc, **kw)


def build():
    from .airframe import wing_z
    for s in (1, -1):
        S_ = 'L' if s > 0 else 'R'
        wt = bpy.data.objects['Wingtip_' + S_]
        ail = bpy.data.objects['Aileron_' + S_]
        parent_keep(ail, wt)
        # droop hinge runs just under the lower skin (so the panel swings down and away, opening a V-gap on top);
        # piano-hinge knuckles alternate between the fixed wing and the moving panel along the hinge pin
        HZ = ZW - 0.088
        kn_in, kn_out = [], []
        for k, y in enumerate(cosspace(2.2, 6.9, 12, (False, False))):
            zl = wing_z(HINGE_X, y, upper=False)
            lug = merge_vf(cyl_vf((s * HINGE_X, y, HZ), 0.022, 0.11, 'Y', 12),
                           box_between((s * HINGE_X - 0.012, y - 0.055, HZ), (s * HINGE_X + 0.012, y + 0.055, zl + 0.01)))
            if k % 2 == 0:
                kn_in.append(merge_vf(lug, box_between((s * (HINGE_X - 0.10), y - 0.055, zl - 0.004),
                                                       (s * HINGE_X, y + 0.055, zl + 0.01))))
            else:
                kn_out.append(merge_vf(lug, box_between((s * HINGE_X, y - 0.055, zl - 0.004),
                                                        (s * (HINGE_X + 0.10), y + 0.055, zl + 0.01))))
        mk('WingHinge_Fixed_' + S_, merge_vf(*kn_in), 'Titanium', 'Aero', bev=(0.003, 1, 30))
        mk('WingHinge_Moving_' + S_, merge_vf(*kn_out), 'Titanium', 'Aero', wt, bev=(0.003, 1, 30))
        act = [cyl_between((s * (HINGE_X - 0.55), y, wing_z(HINGE_X - 0.55, y, False) - 0.03),
                           (s * (HINGE_X - 0.10), y, wing_z(HINGE_X - 0.1, y, False) - 0.05), 0.03, 10) for y in (3.0, 5.4)]
        mk('WingHinge_Actuators_' + S_, merge_vf(*act), 'Chrome', 'Aero')
        fair = [box_between((s * (HINGE_X - 0.62) if s > 0 else -(HINGE_X - 0.04), y - 0.07, wing_z(HINGE_X - 0.3, y, False) - 0.075),
                            (s * (HINGE_X - 0.04) if s > 0 else -(HINGE_X - 0.62), y + 0.07, wing_z(HINGE_X - 0.3, y, False) + 0.01))
                for y in (3.0, 5.4)]
        mk('WingHinge_ActuatorFairings_' + S_, merge_vf(*fair), 'Skin', 'Aero', bev=(0.02, 2, 30))
        hinge(wt, (s * HINGE_X, 4.0, HZ), 'rotate', 'Y', 60 * s, 'HighSpeed', (0.1, 0.9),
              'outer wing panel droops 60 deg at high speed (compression lift + directional stability)')
        hinge(ail, (s * 6.30, 6.70, ZW), 'control', 'X', None, None, (0, 1),
              'aileron (roll): + = trailing edge up (Blender X)', min=-25, max=25, speed=120, input='roll')
        fl = bpy.data.objects['Flaperon_' + S_]
        hinge(fl, (s * 4.20, 6.55, ZW), 'rotate', 'X', -25, 'Flaps', (0, 1),
              'flaperon: droops 25 deg as a flap (Flaps channel) and also deflects +/-20 deg for roll / pitch',
              control={'input': 'roll+pitch', 'min': -20, 'max': 20})
        le = bpy.data.objects['LEFlap_' + S_]
        axis = V((s * 1.0, LE_TAN, 0.0)).normalized()
        px = 4.25
        hinge(le, (s * px, wing_le(px) + 0.42, ZW - 0.031), 'rotate', axis, 15 * s, 'Flaps', (0, 1),
              'leading-edge flap: droops 15 deg about the swept hinge line for low-speed / VTOL lift')
        tl = bpy.data.objects['Tail_' + S_]
        span, thick = tail_axes(s)
        hinge(tl, (s * NAC_X, TAIL_PIVOT_Y, TAIL_ROOT_Z), 'control', span, None, None, (0, 1),
              'all-moving canted tail (rudder): rotates about its own spindle', min=-20, max=20, speed=90, input='yaw')
        spind = cyl_between(V((s * NAC_X, TAIL_PIVOT_Y, TAIL_ROOT_Z - 0.10)), V((s * NAC_X, TAIL_PIVOT_Y, TAIL_ROOT_Z + 0.02)),
                            0.045, 14)
        mk('Tail_Spindle_' + S_, spind, 'Titanium', 'Aero')
        # speed brakes (dorsal)
        sb = AF.DOORS['Speedbrake_' + S_]
        hinge(sb, AF.hinge_line((s * 0.22, 7.547), (s * 1.05, 7.547), 'top')[0], 'rotate', 'X', 50, 'Speedbrake', (0, 1),
              'dorsal speed brake: front-hinged, rises 50 deg')
        kn = [cyl_vf((s * x, 7.56, body_top(x, 7.56) - 0.03), 0.02, 0.10, 'X', 10) for x in (0.40, 0.85)]
        mk('Speedbrake_Hinges_' + S_, merge_vf(*kn), 'Steel', 'Aero')
        rb = [box_between((s * 0.30 if s > 0 else -1.0, y - 0.012, body_top(0.6, y) - 0.06), (s * 1.0 if s > 0 else -0.30, y + 0.012, body_top(0.6, y) - 0.027))
              for y in (7.85, 8.25, 8.6)]
        mk(sb.name + '_Ribs', merge_vf(*rb), 'Primer', 'Aero', sb)
        # avionics bay doors (nose sides, top-hinged along a slanted edge)
        d = AF.DOORS['Avionics_Door_' + S_]
        hp, hd = AF.hinge_line((-8.45, 2.333), (-7.45, 2.363), 'left' if s > 0 else 'right')
        hinge(d, hp, 'rotate', hd, -100 * s, 'Service', (0, 1),
              'avionics bay door: hinged along its top edge, lifts up')
        boxes = [box_between((s * 0.57, y - 0.17, 2.15), (s * 0.72, y + 0.17, 2.26)) for y in (-8.15, -7.75)]
        mk('Avionics_Boxes_' + S_, merge_vf(*boxes), 'Hardware', 'Systems', bev=(0.006, 1, 30))
        cab = [tube_vf([V((s * 0.575, -8.40, 2.24)), V((s * 0.575, -7.95, 2.27)), V((s * 0.575, -7.50, 2.24))], 0.012, 8)]
        mk('Avionics_Cables_' + S_, merge_vf(*cab), 'CableBlack', 'Systems')
    # refuel receptacle
    d = AF.DOORS['Refuel_Door']
    hinge(d, AF.hinge_line((-0.17, -1.547), (0.17, -1.547), 'top')[0], 'rotate', 'X', -105, 'Refuel', (0, 1),
          'air-refuelling receptacle door: rear-hinged, opens forward-up to form the boom slipway')
    sl = box_between((-0.13, -2.20, 2.66), (0.13, -1.62, 2.70))
    mk('Refuel_Slipway', sl, 'GearWhite', 'Systems')
    noz = cyl_between((0.0, -1.70, 2.66), (0.0, -1.70, 2.76), 0.05, 16)
    mk('Refuel_Receptacle', noz, 'Steel', 'Systems', bev=(0.004, 1, 30))
    mk('Refuel_Light', cyl_vf((0.0, -2.12, 2.705), 0.025, 0.012, 'Z', 12), 'LED', 'Systems')
    rig.point('Socket_Refuel', (0.0, -1.70, 2.80), 'socket', direction=(0, 0, 1),
              note='tanker boom connects here (only when the Refuel door is open)')
