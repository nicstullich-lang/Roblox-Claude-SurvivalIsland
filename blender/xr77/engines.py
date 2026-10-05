"""XR-77 adaptive-cycle engines (fictional): translating inlet spikes, fan faces, engine cores with accessories
(visible under the access panels), afterburner, heat shielding and the two-bearing swivel VTOL nozzles.

Per side s (+1 = left): nacelle axis along Y at (s*2.45, y, 2.10).
"""
from .lib import *
from common import rig
from . import airframe as AF


def nl(profile, s, n=48, a0=0.0, ring=False):
    """lathe a (radius, y) profile around the nacelle axis of side s. ring=True closes the profile into a ring."""
    prof = [(r, y) for r, y in profile]
    if ring:
        prof.append(prof[0])
    return orient(lathe_vf(prof, n, cap0=not ring, cap1=not ring, a0=a0), (s * NAC_X, 0.0, NAC_Z), 'Y')


def on_axis(s, r, a_deg, y):
    """point on the nacelle at radius r, angle a (0 = outboard, 90 = top), station y."""
    a = radians(a_deg)
    return V((s * NAC_X + s * r * cos(a), y, NAC_Z + r * sin(a)))


def radial(s, a_deg):
    a = radians(a_deg)
    return V((s * cos(a), 0, sin(a)))


def hinge(ob, pivot, typ, axis, opn, channel, stage, desc, kind='part', **kw):
    set_origin(ob, pivot)
    rig.motion(ob, typ, axis, opn, channel, stage, kind, desc, **kw)


def blade_vf(s, r0, r1, chord, tw0, tw1, y, ang, th=0.008, n=6):
    """one twisted fan / turbine blade at azimuth ang (deg), root r0 tip r1."""
    loops = []
    for k in range(n + 1):
        r = r0 + (r1 - r0) * k / n
        tw = radians(tw0 + (tw1 - tw0) * k / n)
        c = chord * (1.0 - 0.25 * k / n)
        pts = []
        for (u, v) in ((-c / 2, -th / 2), (c / 2, -th / 2), (c / 2, th / 2), (-c / 2, th / 2)):
            # u along the axis (y), v tangential, then twist
            yy = u * cos(tw) - v * sin(tw)
            tt = u * sin(tw) + v * cos(tw)
            pts.append((r, yy, tt))
        loops.append(pts)
    a = radians(ang)
    out = []
    for L in loops:
        q = []
        for (r, yy, tt) in L:
            x = r * cos(a) - tt * sin(a)
            z = r * sin(a) + tt * cos(a)
            q.append(V((s * NAC_X + x, y + yy, NAC_Z + z)))
        out.append(q)
    return loft(out)


def build_side(s):
    S_ = 'L' if s > 0 else 'R'
    cx = s * NAC_X
    # ------------------------------------------------------------ inlet spike (translates aft at high speed)
    ta = tan(radians(11.0))
    prof = [(0.0, -6.00), (0.012, -5.94)] + [((y + 6.0) * ta, y) for y in (-5.6, -5.2, -4.8, -4.4)]
    prof += [(0.330, -4.18), (0.352, -3.95), (0.360, -3.75), (0.360, -3.45), (0.0, -3.45)]
    spike = mk('Spike_' + S_, nl(prof, s, 40), 'SkinDark', 'Engines', sharp=30)
    bleed = []
    for y in (-4.62, -4.52, -4.42, -4.32):
        r = (y + 6.0) * ta + 0.0015
        bleed.append(nl([(r - 0.004, y), (r, y), (r, y + 0.05), (r - 0.004, y + 0.05)], s, 32, ring=True))
    mk('Spike_Bleed_' + S_, merge_vf(*bleed), 'Exhaust', 'Engines', spike, smooth=False)
    tip = nl([(0.0, -6.02), (0.012, -5.94), (0.0, -5.94)], s, 12)
    mk('Spike_Tip_' + S_, tip, 'Titanium', 'Engines', spike)
    hinge(spike, (cx, -6.0, NAC_Z), 'translate', 'Y', 0.50, 'HighSpeed', (0.0, 1.0),
          'inlet shock spike: slides 0.50 m aft as speed rises (keeps the shock on the lip)')
    # fixed centrebody + struts + fan spinner
    cb = nl([(0.0, -3.70), (0.32, -3.70), (0.32, -3.00), (0.30, -2.40), (0.26, -1.95), (0.0, -1.95)], s, 40)
    mk('Inlet_Centerbody_' + S_, cb, 'SkinDark', 'Engines', sharp=30)
    st = []
    for a in (45, 135, 225, 315):
        p0, p1 = on_axis(s, 0.30, a, -2.70), on_axis(s, 0.565, a, -2.70)
        d = radial(s, a)
        tang = V((0, 1, 0))
        side_v = d.cross(tang).normalized() * 0.012
        q = [p0 - side_v, p1 - side_v, p1 + side_v, p0 + side_v]
        st.append(prism(q, (0, 0.55, 0)))
    mk('Inlet_Struts_' + S_, merge_vf(*st), 'SkinDark', 'Engines', bev=(0.004, 1, 30))
    # ------------------------------------------------------------ fan (spins)
    fan_parts = [nl([(0.0, -2.00), (0.15, -1.96), (0.255, -1.88), (0.265, -1.78), (0.0, -1.78)], s, 32)]
    for k in range(22):
        fan_parts.append(blade_vf(s, 0.255, 0.565, 0.13, 52, 28, -1.86, k * 360 / 22))
    fan = mk('Engine_Fan_' + S_, merge_vf(*fan_parts), 'Titanium', 'Engines', sharp=30)
    hinge(fan, (cx, -1.86, NAC_Z), 'spin', 'Y', None, 'EngineRun', (0, 1), 'engine fan (visible down the intake)',
          speed=95.0 * s)
    mk('Engine_FanCone_' + S_, nl([(0.0, -2.01), (0.03, -2.0), (0.0, -1.97)], s, 12), 'Black', 'Engines', fan)
    # ------------------------------------------------------------ core engine (static), visible through panels
    case = nl([(0.592, -1.98), (0.625, -1.98), (0.625, -0.95), (0.592, -0.95)], s, 48, ring=True)
    mk('Engine_FanCase_' + S_, case, 'Titanium', 'Engines', sharp=35)
    core = nl([(0.0, -0.95), (0.592, -0.95), (0.52, -0.80), (0.50, 2.30), (0.545, 2.40), (0.545, 3.20), (0.52, 3.30),
               (0.52, 4.20), (0.585, 4.40), (0.585, 6.60), (0.0, 6.60)], s, 48)
    mk('Engine_Core_' + S_, core, 'Engine', 'Engines', sharp=35)
    fl, bolts_ = [], []
    for y in (-0.80, -0.30, 0.20, 0.70, 1.20, 1.70, 2.30, 3.20, 3.75, 4.30):
        r0 = 0.505 if y < 2.3 else (0.55 if y < 3.25 else 0.525)
        if y >= 4.3:
            r0 = 0.59
        fl.append(nl([(r0 - 0.01, y - 0.015), (r0 + 0.028, y - 0.015), (r0 + 0.028, y + 0.015), (r0 - 0.01, y + 0.015)], s, 32, ring=True))
        for k in range(8):
            a = k * 360 / 8 + 22.5
            bolts_.append(bolt_vf(on_axis(s, r0 + 0.028, a, y), radial(s, a), 0.008, 0.007, washer=False))
    mk('Engine_Flanges_' + S_, merge_vf(*fl), 'Steel', 'Engines', smooth=False)
    mk('Engine_FlangeBolts_' + S_, merge_vf(*bolts_), 'Hardware', 'Engines')
    # fuel manifold ring + injector stubs around the combustor
    fm = [tube_vf([on_axis(s, 0.585, a, 2.75) for a in range(0, 361, 15)], 0.012, 8)]
    for k in range(18):
        a = k * 20
        fm.append(cyl_between(on_axis(s, 0.545, a, 2.75), on_axis(s, 0.585, a, 2.75), 0.008, 6))
    mk('Engine_FuelManifold_' + S_, merge_vf(*fm), 'Brass', 'Engines')
    # top accessories: FADEC, fuel pump, starter-generator, oil tank, heat exchanger, pipe runs, harness
    top = lambda y, h=0.0: on_axis(s, 0.50 + h, 90, y)
    acc = [box_between(top(0.25) + V((-0.16, 0, 0.0)), top(1.15) + V((0.16, 0, 0.12)))]
    mk('Engine_FADEC_' + S_, merge_vf(*acc), 'Hardware', 'Engines', bev=(0.008, 1, 30))
    fins = [box_between(top(0.30 + 0.05 * k) + V((-0.15, 0, 0.12)), top(0.312 + 0.05 * k) + V((0.15, 0, 0.15)))
            for k in range(17)]
    mk('Engine_FADECFins_' + S_, merge_vf(*fins), 'Alu', 'Engines')
    sg = cyl_between(on_axis(s, 0.55, 145, 1.4), on_axis(s, 0.55, 145, 2.15), 0.085, 18)
    mk('Engine_StarterGen_' + S_, sg, 'Alu', 'Engines', bev=(0.006, 1, 30))
    ot = cyl_between(on_axis(s, 0.55, 35, 0.4), on_axis(s, 0.55, 35, 1.3), 0.075, 18)
    mk('Engine_OilTank_' + S_, ot, 'Primer', 'Engines', bev=(0.01, 2, 30))
    hx = box_between(top(3.4) + V((-0.20, 0, 0.0)), top(4.1) + V((0.20, 0, 0.10)))
    mk('Engine_HeatExchanger_' + S_, hx, 'Alu', 'Engines', bev=(0.005, 1, 30))
    hxf = [box_between(top(3.42 + 0.03 * k) + V((-0.19, 0, 0.10)), top(3.43 + 0.03 * k) + V((0.19, 0, 0.13)))
           for k in range(22)]
    mk('Engine_HeatExchangerFins_' + S_, merge_vf(*hxf), 'Copper', 'Engines')
    pipes_c, pipes_s, harn = [], [], []
    for a, rr, mat in ((70, 0.535, pipes_c), (110, 0.535, pipes_s), (60, 0.56, pipes_s)):
        path = [on_axis(s, rr + 0.012 * sin(y * 2.0), a, y) for y in cosspace(-0.6, 4.0, 22, (False, False))]
        mat.append(tube_vf(path, 0.016, 10))
        for y in (-0.3, 0.7, 1.7, 2.9, 3.6):
            mat.append(cyl_vf(on_axis(s, rr, a, y), 0.024, 0.02, 'Y', 10))
    harn.append(tube_vf([on_axis(s, 0.545, 100, y) for y in cosspace(-0.7, 4.3, 20, (False, False))], 0.02, 10))
    harn.append(tube_vf([on_axis(s, 0.545, 125, y) for y in cosspace(0.2, 2.2, 10, (False, False))], 0.014, 8))
    mk('Engine_FuelPipes_' + S_, merge_vf(*pipes_c), 'Copper', 'Engines')
    mk('Engine_BleedPipes_' + S_, merge_vf(*pipes_s), 'Steel', 'Engines')
    mk('Engine_Harness_' + S_, merge_vf(*harn), 'CableOrange', 'Engines')
    # gearbox (bottom, under the service hatch) + mounts + bay frames
    gb = box_between(on_axis(s, 0.50, 270, 0.85) + V((-0.16, 0, -0.10)), on_axis(s, 0.50, 270, 1.80) + V((0.16, 0, 0.01)))
    mk('Engine_Gearbox_' + S_, gb, 'Alu', 'Engines', bev=(0.01, 1, 30))
    pads = [cyl_vf(on_axis(s, 0.61, 270, y), 0.05, 0.03, 'Z', 14) for y in (1.05, 1.35, 1.6)]
    mk('Engine_GearboxPads_' + S_, merge_vf(*pads), 'Steel', 'Engines')
    mounts, frames = [], []
    for y in (0.0, 2.95, 5.9):
        for a in (30, 150, 270):
            mounts.append(cyl_between(on_axis(s, 0.50, a, y), on_axis(s, 0.635, a, y), 0.018, 8))
        frames.append(nl([(0.615, y - 0.03), (0.645, y - 0.03), (0.645, y + 0.03), (0.615, y + 0.03)], s, 32, ring=True))
    for y in (-1.2, 1.5, 4.4, 7.2, 8.4):
        frames.append(nl([(0.62, y - 0.025), (0.645, y - 0.025), (0.645, y + 0.025), (0.62, y + 0.025)], s, 32, ring=True))
    mk('Engine_Mounts_' + S_, merge_vf(*mounts), 'Titanium', 'Engines')
    mk('EngineBay_Frames_' + S_, merge_vf(*frames), 'Primer', 'Engines', smooth=False)
    # ------------------------------------------------------------ afterburner: turbine exit, flameholders, liner
    ab = [nl([(0.0, 6.55), (0.20, 6.60), (0.0, 7.30)], s, 32)]                         # exit cone
    for k in range(14):
        a = k * 360 / 14
        ab.append(prism([on_axis(s, 0.18, a, 6.62), on_axis(s, 0.58, a, 6.62), on_axis(s, 0.58, a, 6.90),
                         on_axis(s, 0.16, a, 6.90)], radial(s, a + 90) * 0.008))
    mk('Engine_TurbineExit_' + S_, merge_vf(*ab), 'Inconel', 'Engines', smooth=False)
    fh = []
    for rr in (0.26, 0.44):
        fh.append(nl([(rr - 0.03, 7.42), (rr, 7.50), (rr + 0.03, 7.42), (rr + 0.02, 7.42), (rr, 7.47), (rr - 0.02, 7.42)], s, 48, ring=True))
    for k in range(12):
        a = k * 30 + 15
        fh.append(cyl_between(on_axis(s, 0.14, a, 7.44), on_axis(s, 0.58, a, 7.44), 0.008, 6))
    mk('Engine_Flameholders_' + S_, merge_vf(*fh), 'Exhaust', 'Engines')
    liner = nl([(0.588, 6.60), (0.575, 6.62), (0.575, 8.70), (0.588, 8.70)], s, 48, ring=True)
    mk('Engine_ABLiner_' + S_, liner, 'Inconel', 'Engines')
    rings = [nl([(0.574, y), (0.570, y), (0.570, y + 0.03), (0.574, y + 0.03)], s, 32, ring=True) for y in cosspace(6.8, 8.6, 5, (False, False))]
    mk('Engine_ABCoolingRings_' + S_, merge_vf(*rings), 'Exhaust', 'Engines', smooth=False)
    # heat-tinted titanium aft shroud on the nacelle + cooling louvres
    shroud = nl([(NR_(8.35) + 0.0015, 8.35), (NR_(8.95) + 0.0015, 8.95), (NR_(8.95) - 0.045, 8.95), (NR_(8.35) - 0.04, 8.35)], s, 56, ring=True)
    mk('Nacelle_HotShroud_' + S_, shroud, 'BurntTi', 'Engines', sharp=35)
    louv = []
    for a in (200, 215, 230):
        for k in range(6):
            y = 6.55 + k * 0.14
            p = on_axis(s, NR_(y) + 0.002, a, y)
            n = radial(s, a)
            t_ = V((0, 1, 0))
            b = n.cross(t_).normalized()
            q = [p - b * 0.045, p + b * 0.045, p + b * 0.045 + t_ * 0.09, p - b * 0.045 + t_ * 0.09]
            louv.append(prism(q, n * 0.006))
    mk('Nacelle_Louvres_' + S_, merge_vf(*louv), 'SkinDark', 'Engines', smooth=False)
    # ------------------------------------------------------------ swivel nozzle: two spherical bearings
    # Ball-and-socket bearings. Clearance rule (checked numerically): every point of a moving segment is either
    # closer to its joint centre than the socket bore radius, or far enough behind the socket rim that a 45 deg
    # turn cannot bring it back inside the socket wall. That is why each duct necks in right behind its ball.
    J1, J2 = 9.20, 9.95
    sph1 = [(0.585 * cos(radians(a)), J1 + 0.585 * sin(radians(a))) for a in (-40, -28, -16, -5, 5, 12)]
    seg1 = nl(sph1 + [(0.552, J1 + 0.20), (0.600, J1 + 0.26), (0.600, J2 - 0.02), (0.560, J2 - 0.02),
                      (0.560, J1 + 0.15), (0.43, J1 - 0.36)], s, 48, ring=True)
    n1 = mk('Nozzle_Swivel1_' + S_, seg1, 'BurntTi', 'Engines', sharp=35)
    rings1 = [nl([(0.603, y), (0.611, y), (0.611, y + 0.045), (0.603, y + 0.045)], s, 48, ring=True)
              for y in (J1 + 0.28, J2 - 0.07)]
    mk('Nozzle_Bearing1_' + S_, merge_vf(*rings1), 'Titanium', 'Engines', n1)
    hinge(n1, (cx, J1, NAC_Z), 'rotate', 'X', -45, 'VTOL', (0.25, 0.85),
          'swivel nozzle bearing 1: turns 45 deg down about its spherical seat')
    sph2 = [(0.55 * cos(radians(a)), J2 + 0.55 * sin(radians(a))) for a in (-38, -25, -12, 0, 12, 27)]
    seg2 = nl(sph2 + [(0.455, J2 + 0.30), (0.42, J2 + 0.35), (0.395, J2 + 0.38), (0.395, J2 + 0.41), (0.42, J2 + 0.43),
                      (0.45, J2 + 0.46), (0.49, J2 + 0.50), (0.53, J2 + 0.54), (0.545, J2 + 0.56), (0.53, J2 + 0.56),
                      (0.38, J2 + 0.44), (0.36, J2 + 0.20), (0.40, J2 - 0.32)],
              s, 48, ring=True)
    n2 = mk('Nozzle_Swivel2_' + S_, seg2, 'BurntTi', 'Engines', n1, sharp=35)
    pet = []
    np_ = 16
    for k in range(np_):
        a0, a1 = k * 360 / np_ + 0.9, (k + 1) * 360 / np_ - 0.9
        q0 = [on_axis(s, 0.545, a0, J2 + 0.56), on_axis(s, 0.545, a1, J2 + 0.56), on_axis(s, 0.49, a1, J2 + 1.20),
              on_axis(s, 0.49, a0, J2 + 1.20)]
        pet.append(prism(q0, radial(s, (a0 + a1) / 2) * -0.018))
    mk('Nozzle_Petals_' + S_, merge_vf(*pet), 'BurntTi', 'Engines', n2, sharp=20)
    inner = nl([(0.528, J2 + 0.56), (0.42, J2 + 0.86), (0.41, J2 + 0.90), (0.468, J2 + 1.19), (0.458, J2 + 1.19),
                (0.40, J2 + 0.90), (0.41, J2 + 0.84), (0.518, J2 + 0.56)], s, 48, ring=True)
    mk('Nozzle_Liner_' + S_, inner, 'Inconel', 'Engines', n2)
    act = []
    for k in range(4):
        a = 45 + 90 * k
        act.append(cyl_between(on_axis(s, 0.552, a, J2 + 0.63), on_axis(s, 0.505, a, J2 + 1.05), 0.014, 8))
        act.append(cyl_vf(on_axis(s, 0.552, a, J2 + 0.63), 0.020, 0.05, 'Y', 10))
    mk('Nozzle_Actuators_' + S_, merge_vf(*act), 'Titanium', 'Engines', n2)
    rings2 = [nl([(0.546, y), (0.556, y), (0.556, y + 0.035), (0.546, y + 0.035)], s, 48, ring=True) for y in (J2 + 0.56,)]
    mk('Nozzle_Bearing2_' + S_, merge_vf(*rings2), 'Titanium', 'Engines', n2)
    hinge(n2, (cx, J2, NAC_Z), 'rotate', 'X', -45, 'VTOL', (0.35, 1.0),
          'swivel nozzle bearing 2: another 45 deg down -> exhaust points straight down for hover')
    rig.point('Exhaust_' + S_, (cx, J2 + 1.20, NAC_Z), 'effect', attach=n2, direction=(0, 1, 0),
              effect='engine exhaust / afterburner flame (points straight down in VTOL)')
    # ------------------------------------------------------------ access doors (from the airframe stage)
    for k in ('Fwd', 'Aft'):
        d = AF.DOORS['EnginePanel_%s_%s' % (k, S_)]
        y0, y1 = (0.00, 2.85) if k == 'Fwd' else (3.05, 5.75)
        hinge(d, AF.hinge_line((cx + s * 0.583, y0), (cx + s * 0.583, y1), 'top')[0], 'rotate', 'Y', 110 * s, 'EnginePanels', (0.0, 1.0) if k == 'Fwd' else (0.15, 1.0),
              'engine access panel: hinged on its outboard edge, swings up 110 deg')
        ribs = []
        for t in (0.25, 0.5, 0.75):
            y = y0 + (y1 - y0) * t
            arc_ = [on_axis(s, NR_(y) - 0.03, a, y) for a in range(42, 140, 8)]
            ribs.append(sweep_vf(arc_, rect2(0.03, 0.035)))
        mk(d.name + '_Ribs', merge_vf(*ribs), 'Primer', 'Doors', d)
    ai = AF.DOORS['AuxInlet_' + S_]
    hinge(ai, AF.hinge_line((cx - 0.30, -1.947), (cx + 0.30, -1.947), 'top')[0], 'rotate', 'X', -35, 'VTOL', (0.0, 0.4),
          'VTOL auxiliary inlet door: rear-hinged, opens 35 deg for extra hover airflow')
    vanes = []
    for k in range(5):
        y = -2.78 + k * 0.17
        vanes.append(box_between((cx - 0.27, y, 2.62), (cx + 0.27, y + 0.012, 2.74)))
    mk('AuxInlet_Vanes_' + S_, merge_vf(*vanes), 'SkinDark', 'Engines')
    sh = AF.DOORS['ServiceHatch_' + S_]
    hinge(sh, AF.hinge_line((cx + s * 0.243, 0.90), (cx + s * 0.243, 1.75), 'bottom')[0], 'rotate', 'Y', -100 * s, 'Service', (0, 1),
          'engine service hatch (gearbox / oil): hinged outboard, drops open')


def build():
    for s in (1, -1):
        build_side(s)
