"""Every opening in the XR-77 skin: where it is cut, how deep the compartment behind it goes, and the doors
that close it. The airframe stage cuts them all in one EXACT boolean and builds each door as a panel that
follows the real (uncut) skin, so doors sit flush with true 6 mm seams.

outline / door outlines are 2D polygons in the projection plane:
  'top' / 'bottom' -> (x, y)      'left' / 'right' -> (y, z)
floor = the coordinate (z for top/bottom, x for left/right) where the compartment ends.
slot  = body material slot of the compartment walls (see BODY_SLOTS).
"""
from .lib import *

BODY_SLOTS = ['Skin', 'BayGrey', 'GearWhite', 'Cockpit', 'Primer', 'SkinDark', 'Engine', 'Exhaust', 'Insulation',
              'Ceramic']
SLOT = {n: i for i, n in enumerate(BODY_SLOTS)}


def rect(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def saw_rect(x0, x1, y0, y1, teeth=1, depth=0.22):
    """rectangle (x0<x1, y0<y1) whose front (y0) and rear (y1) edges are stealth-serrated."""
    pts = saw_edge((x0, y0), (x1, y0), teeth, depth, side=-1)        # front edge, teeth point -y
    pts += [(x1, y0)]
    pts += saw_edge((x1, y1), (x0, y1), teeth, depth, side=-1)       # rear edge, teeth point +y
    pts += [(x0, y1)]
    return pts


def clip_half(poly, side):
    """the part of a convex polygon on one side of x = 0 (side +1 -> x >= 0)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina, inb = side * a[0] >= 0, side * b[0] >= 0
        if ina:
            out.append(a)
        if ina != inb:
            t = a[0] / (a[0] - b[0])
            out.append((0.0, a[1] + (b[1] - a[1]) * t))
    return out


def mirror_x(poly):
    return [(-x, y) for x, y in reversed(poly)]


def door(name, outline, mats=('Skin', 'BayGrey', 'SkinDark'), t=0.022):
    return dict(name=name, outline=outline, mats=mats, t=t)


def openings():
    O = []

    def add(name, proj, outline, floor, slot, doors=(), cutters=(), depth_from=None):
        O.append(dict(name=name, proj=proj, outline=outline, floor=floor, slot=SLOT[slot], doors=list(doors),
                      cutters=list(cutters), depth_from=depth_from))

    # ------------------------------------------------------------- cockpit + canopy
    add('Canopy', 'top', canopy_outline(), 2.40, 'Cockpit')          # glass + frame built by the cockpit stage
    tub = [(-0.455, -8.22), (0.455, -8.22), (0.47, -7.60), (0.47, -5.35), (-0.47, -5.35), (-0.47, -7.60)]
    add('CockpitTub', 'top', tub, 2.05, 'Cockpit', depth_from=3.45)
    tubf = [(-0.30, -9.10), (0.30, -9.10), (0.44, -8.55), (0.455, -8.20), (-0.455, -8.20), (-0.44, -8.55)]
    add('CockpitFront', 'top', tubf, 2.34, 'Cockpit', depth_from=3.45)      # floor above the nose gear well

    # ------------------------------------------------------------- VTOL lift fan (duct cut separately)
    # rear-hinged: serrated front edge only (a serrated rear edge would swing into the body)
    fan_top = saw_edge((-0.86, -4.42), (0.86, -4.42), 2, 0.16, side=-1) + [(0.86, -4.42), (0.86, -2.50), (-0.86, -2.50)]
    add('LiftFanTop', 'top', fan_top, 2.55, 'BayGrey',
        doors=[door('LiftFan_DoorTop', fan_top, ('Skin', 'BayGrey', 'SkinDark'), t=0.03)])
    add('LiftFanBottom', 'bottom', rect(-0.86, 0.86, -4.40, -2.70), 1.62, 'BayGrey',
        doors=[door('LiftFan_DoorBot_L', rect(0.0, 0.86, -4.40, -2.70)),
               door('LiftFan_DoorBot_R', rect(-0.86, 0.0, -4.40, -2.70))])

    # ------------------------------------------------------------- main weapon bays (two, either side of the keel)
    for s, sx in (('L', 1), ('R', -1)):
        x0, xm, x1 = 0.10, 0.49, 0.88
        whole = saw_rect(x0, x1, -1.60, 4.00, teeth=2, depth=0.22)
        inner = saw_rect(x0, xm, -1.60, 4.00, teeth=1, depth=0.22)
        outer = saw_rect(xm, x1, -1.60, 4.00, teeth=1, depth=0.22)
        if sx < 0:
            whole, inner, outer = mirror_x(whole), mirror_x(inner), mirror_x(outer)
        add('MainBay_' + s, 'bottom', whole, 2.25, 'BayGrey',
            doors=[door('MainBay_DoorIn_' + s, inner), door('MainBay_DoorOut_' + s, outer)])

        # side missile bays (lower body sides, ahead of the main gear)
        sb = saw_rect(1.02, 1.62, -2.70, -0.25, teeth=1, depth=0.20)
        if sx < 0:
            sb = mirror_x(sb)
        add('SideBay_' + s, 'bottom', sb, 2.02, 'BayGrey', doors=[door('SideBay_Door_' + s, sb)])

        # main landing gear wells
        gw = rect(1.10, 1.58, 1.15, 3.75)
        if sx < 0:
            gw = mirror_x(gw)
        add('MainWell_' + s, 'bottom', gw, 2.49, 'GearWhite',
            doors=[door('Gear_MainDoor_' + s, gw, ('Skin', 'GearWhite', 'SkinDark'))])

        # engine access panels (nacelle tops) - forward + aft
        cx = sx * NAC_X
        for k, (y0, y1) in enumerate(((0.00, 2.85), (3.05, 5.75))):
            pn = rect(cx - 0.58, cx + 0.58, y0, y1)
            nm = 'EnginePanel_%s_%s' % ('Fwd' if k == 0 else 'Aft', s)
            add(nm, 'top', pn, 2.50, 'Primer', doors=[door(nm, pn, ('SkinAlt', 'Primer', 'SkinDark'), t=0.02)])

        # VTOL auxiliary inlet doors (nacelle tops, ahead of the fan face)
        ai = rect(cx - 0.30, cx + 0.30, -2.85, -1.95)
        add('AuxInlet_' + s, 'top', ai, 2.55, 'SkinDark', doors=[door('AuxInlet_' + s, ai, ('Skin', 'SkinDark', 'SkinDark'))])

        # roll-post nozzle doors (inner wing underside)
        rp = circle2(0.17, 20, sx * 4.55, 4.75)
        add('RollPost_' + s, 'bottom', rp, 2.10, 'Exhaust', doors=[door('RollPost_Door_' + s, rp, ('Skin', 'Exhaust', 'SkinDark'), t=0.015)])

        # chine reconnaissance camera bays (SR-71 heritage)
        cb = rect(0.56, 0.90, -8.55, -7.15)
        if sx < 0:
            cb = mirror_x(cb)
        add('ChineCam_' + s, 'bottom', cb, 2.03, 'BayGrey', doors=[door('ChineCam_Door_' + s, cb, t=0.018)])

        # countermeasure (flare / chaff) magazines, aft body underside
        cm = rect(0.92, 1.36, 7.45, 8.55)
        if sx < 0:
            cm = mirror_x(cm)
        add('Flares_' + s, 'bottom', cm, 1.80, 'BayGrey', doors=[door('Flares_Door_' + s, cm, t=0.018)])

        # dorsal speed brakes (aft body top between the nacelles)
        spb = rect(0.22, 1.05, 7.55, 8.75)
        if sx < 0:
            spb = mirror_x(spb)
        add('Speedbrake_' + s, 'top', spb, 2.48, 'Primer', doors=[door('Speedbrake_' + s, spb, ('Skin', 'Primer', 'SkinDark'), t=0.025)])

        # nacelle underside service hatch (accessory gearbox / oil)
        sh = rect(cx - 0.24, cx + 0.24, 0.90, 1.75)
        add('ServiceHatch_' + s, 'bottom', sh, 1.52, 'Primer', doors=[door('ServiceHatch_' + s, sh, ('SkinAlt', 'Primer', 'SkinDark'), t=0.016)])

        # avionics bays (nose sides above the chine)
        ab = [(-8.45, 2.12), (-7.45, 2.12), (-7.45, 2.36), (-8.45, 2.33)]
        add('Avionics_' + s, 'left' if sx > 0 else 'right', ab, sx * 0.56, 'Primer',
            doors=[door('Avionics_Door_' + s, ab, ('SkinAlt', 'Primer', 'SkinDark'), t=0.015)])

    # ------------------------------------------------------------- landing gear (nose)
    nw = rect(-0.48, 0.04, -10.30, -8.25)
    add('NoseWell', 'bottom', nw, 2.28, 'GearWhite',
        doors=[door('Gear_NoseDoor_L', rect(-0.22, 0.04, -10.30, -8.25), ('Skin', 'GearWhite', 'SkinDark')),
               door('Gear_NoseDoor_R', rect(-0.48, -0.22, -10.30, -8.25), ('Skin', 'GearWhite', 'SkinDark'))])

    # ------------------------------------------------------------- weapons + sensors (centreline)
    gd = rect(0.15, 0.45, -10.40, -8.70)
    add('GunBay', 'bottom', gd, 1.74, 'BayGrey', doors=[door('Gun_Door', gd, t=0.016)])
    add('ReconBay', 'bottom', circle2(0.40, 28, 0.0, -2.15), 1.98, 'BayGrey',
        doors=[door('Recon_Door_L', [(0.0, -2.55)] + [(0.40 * cos(a), -2.15 + 0.40 * sin(a)) for a in
                                     [-pi / 2 + pi * k / 14 for k in range(1, 14)]] + [(0.0, -1.75)]),
               door('Recon_Door_R', [(0.0, -1.75)] + [(-0.40 * cos(a), -2.15 - 0.40 * sin(a)) for a in
                                     [-pi / 2 + pi * k / 14 for k in range(1, 14)]] + [(0.0, -2.55)])])
    # belly gun turret bay (racetrack: the stowed guns point forward) - two doors hinged on the outer edges
    tb = rrect2(1.00, 2.00, 0.42, 6, 0.0, 5.45)
    add('TurretBay', 'bottom', tb, 2.30, 'BayGrey',
        doors=[door('Turret_Door_L', [p for p in clip_half(tb, 1)]), door('Turret_Door_R', [p for p in clip_half(tb, -1)])])
    # dorsal energy-weapon bay - two doors hinged on the outer edges, open upward
    lb = rrect2(0.90, 1.70, 0.38, 6, 0.0, 1.05)
    add('LaserBay', 'top', lb, 2.32, 'BayGrey',
        doors=[door('Laser_Door_L', clip_half(lb, 1)), door('Laser_Door_R', clip_half(lb, -1))])
    rf = rrect2(0.34, 0.70, 0.08, 3, 0.0, -1.90)
    add('Refuel', 'top', rf, 2.62, 'Primer', doors=[door('Refuel_Door', rf, ('SkinAlt', 'Primer', 'SkinDark'), t=0.018)])
    add('DircmTop', 'top', circle2(0.15, 20, 0.0, 6.30), 2.52, 'BayGrey')
    add('DircmBot', 'bottom', circle2(0.15, 20, 0.0, 6.85), 1.66, 'BayGrey')
    # emergency ram-air turbine (right lower body) + arrestor hook recess (aft body centreline)
    rat = rect(-1.55, -1.10, 0.15, 0.75)
    add('RATBay', 'bottom', rat, 1.98, 'BayGrey', doors=[door('RAT_Door', rat, t=0.018)])
    add('HookRecess', 'bottom', rect(-0.07, 0.07, 8.60, 9.90), 1.76, 'SkinDark')
    return O
