"""Mako-9 - compact 9 mm submachine gun (collection MAKO9, export Mako9.fbx).

Target 3.3 x 1.35 x 0.55 studs (L x H x W) = 0.924 x 0.378 x 0.154 m (stock folded).
Layout (y, metres; bore z = 0; origin above the trigger):
  flash hider -0.688..-0.633 | barrel + 3-lug adapter to -0.470 | polymer handguard -0.470..-0.302
  graphite receiver -0.300..+0.200 (round top, flat sides) | end cap + stock hinge +0.200..+0.235
  polymer trigger housing -0.175..+0.150 (magwell -0.170..-0.084) | grip +0.06..+0.15
  side-folding skeleton stock, folded along the RIGHT side (hinge at the right rear corner); unfolds 180 deg.
Finish: graphite receiver, dark polymer housing / handguard / grip, one faded tan side panel with a red MAKO-9
marking, dark-steel curved magazine with witness holes.
"""
from .lib import *
from . import parts as P

HW = 0.032                 # receiver half width
ZB = -0.032                # receiver bottom (seam with the polymer housing)
ZR = 0.018                 # centre height of the round top (top = ZR + HW = 0.050)
RY0, RY1 = -0.300, 0.200
HL = 0.029                 # trigger housing half width
MAG_TOP = (-0.124, -0.040)
SEL = (0.074, -0.052)
PIV = (-0.034, 0.2285)     # stock hinge (x, y), vertical axis
SX = -0.068                # folded stock plane (x)
DM = -0.028                # barrel extension (muzzle at -0.688)


def receiver():
    sec_ = fillet2([(HW, ZB, 0.004), (HW, ZR + HW, 0.031), (-HW, ZR + HW, 0.031), (-HW, ZB, 0.004)], 8)
    side = fillet2([(RY0, ZB - 0.01), (RY1 + 0.01, ZB - 0.01), (RY1 + 0.01, 0.07), (RY0, 0.07)])
    rc = part('Receiver', plate_xz(sec_, RY0, RY1), 'Graphite', wn=False)
    cuts = [slab(fillet2([(RY0 - 0.01, 0.030), (RY0 + 0.020, 0.075), (RY0 - 0.01, 0.075)]), -0.1, 0.1)]  # nose chamfer
    # ejection port (right)
    cuts.append(slab(fillet2([(-0.060, 0.010, 0.003), (0.010, 0.010, 0.003), (0.010, 0.036, 0.003),
                              (-0.060, 0.036, 0.003)]), -0.06, -0.012))
    # cocking slot on the upper-left curve
    cuts.append(slab(fillet2([(-0.292, 0.022, 0.004), (-0.158, 0.022, 0.004), (-0.158, 0.032, 0.004),
                              (-0.292, 0.032, 0.004)]), 0.016, 0.06))
    # inset panels (both sides): front and rear recesses
    rec = {'F': [(-0.285, -0.024, 0.005), (-0.155, -0.024, 0.005), (-0.155, 0.008, 0.005), (-0.285, 0.008, 0.005)],
           'R': [(0.025, -0.024, 0.005), (0.185, -0.024, 0.005), (0.185, 0.010, 0.005), (0.025, 0.010, 0.005)]}
    for sg in (1, -1):
        for k, poly in rec.items():
            cuts.append(slab(fillet2(poly), sg * (HW - 0.0016), sg * 0.06))
    cuts.append(cyl_vf((0, RY0, 0), 0.0122, 0.03, 'Y', 20))
    cut(rc, cuts)
    finish(rc, 0.0015, 2, 35)
    marking(rc, 'SI-1185', (HW - 0.0016, 0.105, -0.0035), (1, 0, 0), 0.0068)
    marking(rc, 'HAVEN ARMORY  9x21', (HW - 0.0016, 0.105, -0.0150), (1, 0, 0), 0.0044)
    # tan polymer side panel (right front recess) with screws and the red MAKO-9 marking
    tp = part('SidePanel_Tan', slab(offset2(ccw(fillet2(rec['F'])), -0.0008), -HW + 0.0018, -HW + 0.0003), 'PolyTan',
              wn=False)
    finish(tp, 0.0006, 2, 35)
    marking(tp, 'MAKO-9', (-HW + 0.0003, -0.222, -0.0075), (-1, 0, 0), 0.0118)
    sc_ = [screw_vf((-HW + 0.0003, y, z), (-1, 0, 0), 0.0026, 0.0010) for y in (-0.276, -0.164) for z in (-0.017, 0.001)]
    part('SidePanel_Screws', merge_vf(*sc_), 'Steel')
    # end cap with the fixed hinge knuckles + stock latch button
    cap_sec = fillet2([(HW - 0.0015, ZB + 0.002, 0.004), (HW - 0.0015, ZR + HW - 0.002, 0.029),
                       (-HW + 0.0015, ZR + HW - 0.002, 0.029), (-HW + 0.0015, ZB + 0.002, 0.004)], 8)
    cap = part('EndCap', plate_xz(cap_sec, RY1 - 0.002, PIV[1] - 0.0005), 'Blackened', bev=(0.0016, 2, 35))
    kn = [cyl_vf((PIV[0], PIV[1], zc), 0.0068, h, 'Z', 16) for zc, h in ((0.021, 0.018), (-0.031, 0.018))]
    lugs = [box_between((PIV[0] + 0.001, PIV[1] - 0.012, z0), (PIV[0] + 0.012, PIV[1] - 0.0005, z1))
            for z0, z1 in ((0.012, 0.030), (-0.040, -0.022))]
    part('Hinge_Fixed', merge_vf(*kn, *lugs), 'Blackened', bev=(0.0007, 2, 35))
    part('Hinge_Pin', merge_vf(cyl_vf((PIV[0], PIV[1], -0.0055), 0.0026, 0.075, 'Z', 12),
                               cyl_vf((PIV[0], PIV[1], 0.0315), 0.0040, 0.003, 'Z', 12),
                               cyl_vf((PIV[0], PIV[1], -0.0425), 0.0040, 0.003, 'Z', 12)), 'Steel')
    part('Stock_LatchButton', lathe_axis([(0, 0), (0.0055, 0), (0.0055, 0.004), (0.0045, 0.005), (0, 0.005)], 14,
                                         (0.015, PIV[1] - 0.0005, 0.036), 'Y'), 'Steel')
    cup, loop = P.qd_loop((HW - 0.0016, 0.165, 0.030), (0.70, 0, 0.71))
    part('Sling_Socket', cup, 'Blackened')
    part('Sling_Loop', loop, 'Steel')
    return rc


def housing():
    prof = fillet2([(-0.175, ZB - 0.0012, 0.002), (-0.172, -0.090, 0.004), (-0.084, -0.090, 0.0),
                    (-0.084, -0.0745, 0.005), (0.128, -0.0745, 0.010), (0.150, -0.052, 0.010),
                    (0.150, ZB - 0.0012, 0.002)])
    h = part('TriggerHousing', slab(prof, -HL, HL), 'PolyBlack', wn=False)
    flare = fillet2([(-0.1765, -0.104, 0.003), (-0.0815, -0.104, 0.003), (-0.0815, -0.094), (-0.084, -0.086),
                     (-0.172, -0.086), (-0.1765, -0.094)])
    cut(h, slab(flare, -HL + 0.0025, HL - 0.0025), 'UNION')
    cuts = [prism([V((x, y, -0.112)) for x, y in fillet2([(0.0138, -0.1485, 0.006), (0.0138, -0.0995, 0.003),
                                                          (-0.0138, -0.0995, 0.003), (-0.0138, -0.1485, 0.006)])],
                  (0, 0, 0.078)),
            box_vf((0, -0.006, -0.074), (0.011, 0.034, 0.030))]
    for sg in (1, -1):        # moulded grip-texture pockets on the magwell sides
        for k in range(4):
            yc = -0.160 + k * 0.018
            cuts.append(slab(fillet2([(yc - 0.0055, -0.084, 0.002), (yc + 0.0055, -0.084, 0.002),
                                      (yc + 0.0055, -0.046, 0.002), (yc - 0.0055, -0.046, 0.002)]),
                             sg * (HL - 0.0012), sg * 0.06))
    finish(h, 0.0014, 2, 35)
    detail(h, cuts)
    for txt, a in (('S', 0), ('1', 90), ('F', 180)):
        marking(h, txt, (HL, SEL[0] - 0.012 * cos(radians(a)), SEL[1] + 0.012 * sin(radians(a))), (1, 0, 0), 0.0046)
    heads = [pinhead_vf((sg * HL, y, -0.042), (sg, 0, 0), 0.0034, 0.0012) for y in (-0.150, 0.132) for sg in (1, -1)]
    heads += [pinhead_vf((sg * HL, y, -0.058), (sg, 0, 0), 0.0024, 0.0009) for y in (-0.006, 0.030) for sg in (1, -1)]
    part('Housing_Pins', merge_vf(*heads), 'Steel')
    # paddle magazine release behind the magwell
    pad = merge_vf(slab(fillet2([(-0.0845, -0.0985, 0.001), (-0.068, -0.1005, 0.002), (-0.068, -0.1055, 0.002),
                                 (-0.0845, -0.1045, 0.001)]), -0.010, 0.010),
                   slab(fillet2([(-0.0700, -0.1055, 0.002), (-0.0640, -0.1060, 0.002), (-0.0655, -0.0975, 0.001),
                                 (-0.0700, -0.0995, 0.001)]), -0.008, 0.008))
    part('MagRelease_Paddle', pad, 'Blackened', bev=(0.0006, 2, 35))
    part('TriggerGuard', P.guard_vf([(-0.070, -0.068), (-0.066, -0.110, 0.010), (0.046, -0.112, 0.013),
                                     (0.066, -0.082)], 0.0072, 0.0036, 0.0028), 'PolyBlack')
    trig = part('Trigger', P.trigger_vf((-0.004, -0.058), (-0.012, -0.097), 0.0075, 0.0042, 0.0034), 'DarkSteel')
    group(trig, (0, -0.005, -0.056), 'rotate', 'X', 14, 'Trigger', 'trigger: pivots 14 deg rearward to fire')
    sel = merge_vf(lathe_axis([(0, 0), (0.0062, 0), (0.0062, 0.0024), (0, 0.0024)], 16, (HL, SEL[0], SEL[1]), 'X'),
                   slab(fillet2([(SEL[0] + 0.002, SEL[1] - 0.003), (SEL[0] - 0.0085, SEL[1] - 0.0022, 0.002),
                                 (SEL[0] - 0.0085, SEL[1] + 0.0022, 0.002), (SEL[0] + 0.002, SEL[1] + 0.003)]),
                        HL + 0.0012, HL + 0.0042))
    s = part('Selector', sel, 'Blackened', bev=(0.0006, 2, 35))
    group(s, (HL, SEL[0], SEL[1]), 'control', 'X', None, None,
          'fire selector: SAFE = 0 deg (forward), SEMI = -90 (up), AUTO = -180 (rearward)', min=-180, max=0, speed=600,
          detents={'SAFE': 0, 'SEMI': -90, 'AUTO': -180}, input='fire_mode')
    return h


def grip():
    top, bot = (0.092, -0.064), (0.120, -0.196)
    fr = P.Frame(top, bot)
    w0, w1 = 0.0185, 0.0205
    g = part('Grip', P.grip_vf(top, bot, w0, w1, -0.028, 0.029, 0.034, fingers=1, finger_depth=0.0040,
                               finger_range=(0.08, 0.36), flare=0.0030), 'PolyBlack', wn=False)
    finish(g, 0.0012, 2, 40)           # round the grip first, then cut the checkering (no bevel on the fine grooves)
    wfun = lambda s_: w0 + (w1 - w0) * s_ / fr.L
    cut(g, P.checker_cutters(fr, wfun, fr.L * 0.30, fr.L * 0.84, -0.018, 0.021, 0.0068, 42.0, 0.0014, 0.0011))
    weighted(g)
    capl = [[V((p[0], s_, p[1])) for p in P.grip_section(0.0185, -0.024, 0.031)] for s_ in (-0.003, 0.0024)]
    part('Grip_Cap', fr.vf(xform_vf(loft(capl), Matrix.Translation((0, fr.L, 0.002)))), 'Blackened', bev=(0.0008, 2, 35))
    return g


def magazine():
    path = P.arc_down_path(MAG_TOP, -0.110, 0.30, 32.0, 4, 28)
    m = part('Magazine', P.mag_vf(path, 0.0125, 0.022, 0.022, ribs=[(0.86, 0.90)], rib_h=0.0012, rf=0.0060, rb=0.0030),
             'DarkSteel', wn=False)
    pits = []
    for k in range(6):        # witness holes (both sides)
        f = 0.36 + 0.075 * k
        for sg in (1, -1):
            c = P.path_point3(path, f, sg * 0.0125, 0.010)
            pits.append(cyl_vf(c, 0.0023, 0.0034, 'X', 12))
    finish(m, 0.0010, 2, 35)
    detail(m, pits)
    part('Magazine_Baseplate', P.baseplate_vf(path, 0.0125, 0.022, 0.022, 0.010, 0.0050, 0.0035, 0.0020),
              'PolyBlack', m, bev=(0.0014, 2, 35))
    group(m, (0, MAG_TOP[0], MAG_TOP[1]), 'translate', V((0, -0.10, -1)).normalized(), 0.18, 'Reload',
          'magazine: drops out of the magwell along its insertion line (0.18 m)', stage=(0.0, 0.45))
    return m


def barrel_front():
    prof = [(0, -0.585 + DM), (0.0050, -0.585 + DM), (0.0050, -0.605 + DM), (0.0095, -0.605 + DM), (0.0095, -0.598 + DM),
            (0.0115, -0.596 + DM), (0.0115, -0.300), (0, -0.300)]
    part('Barrel', lathe_axis(prof, 24, (0, 0, 0), 'Y'), 'DarkSteel')
    lug = []
    for k in range(3):        # three-lug adapter
        a = pi / 2 + 2 * pi * k / 3
        c = V((cos(a) * 0.0135, -0.578 + DM, sin(a) * 0.0135))
        b = box_vf((0, 0, 0), (0.0085, 0.010, 0.0048))
        lug.append(xform_vf(b, Matrix.Translation(c) @ Matrix.Rotation(-(a - pi / 2), 4, 'Y')))
    ring = ring_y([(0.0112, -0.586 + DM), (0.0128, -0.586 + DM), (0.0128, -0.570 + DM), (0.0112, -0.570 + DM)], 24)
    part('Barrel_LugAdapter', merge_vf(ring, *lug), 'Blackened', bev=(0.0006, 1, 35))
    solid, cuts = P.birdcage_vf(-0.660 + DM, 0.056, 0.0158, 0.0058, 4, 0.0042, 0.030, closed_bottom=False)
    fh = part('Muzzle_FlashHider', solid, 'Blackened', wn=False)
    finish(fh, 0.0007, 2, 35)
    detail(fh, cuts)
    part('Muzzle_Collar', ring_y([(0.0095, -0.606 + DM), (0.0145, -0.606 + DM), (0.0145, -0.600 + DM),
                                  (0.0095, -0.600 + DM)], 6),
         'Steel', bev=(0.0005, 1, 35))


HG_OUT = [(0.023, -0.041, 0.014), (0.031, -0.014, 0.010), (0.029, 0.023, 0.014)]
HG_IN = [(0.0195, -0.0375, 0.011), (0.0275, -0.013, 0.008), (0.0255, 0.0195, 0.011)]


def _sym(half, seg=3):
    return fillet2([(x, z, r) for x, z, r in half] + [(-x, z, r) for x, z, r in reversed(half)], seg)


def handguard():
    Y0, Y1 = -0.462, -0.302
    loops = [[V((p[0], y, p[1])) for p in _sym(HG_OUT)] for y in (Y0, Y1)]
    loops += [[V((p[0], y, p[1])) for p in _sym(HG_IN)] for y in (Y1, Y0)]
    hg = part('Handguard', loft(loops + [loops[0]], False, False), 'PolyBlack', wn=False)
    cuts = []
    for sg in (1, -1):
        for k in range(4):
            cuts.append(cyl_vf((sg * 0.03, -0.432 + k * 0.034, -0.006), 0.0058, 0.02, 'X', 16))
    for k in range(3):
        cuts.append(cyl_vf((0, -0.415 + k * 0.040, 0.025), 0.0042, 0.02, 'Z', 12))
    for k in range(7):        # finger ribs across the bottom
        cuts.append(box_vf((0, -0.444 + k * 0.019, -0.0425), (0.07, 0.0042, 0.006)))
    finish(hg, 0.0012, 2, 35)
    detail(hg, cuts)
    # hand-stop flange at the front (keeps the fingers off the muzzle)
    fl = _sym([(0.024, -0.064, 0.010), (0.0325, -0.014, 0.009), (0.0305, 0.025, 0.014)])
    f = part('Handguard_HandStop', plate_xz(fl, -0.474, -0.461), 'PolyBlack', wn=False)
    cut(f, cyl_vf((0, -0.47, 0), 0.0125, 0.04, 'Y', 20))
    finish(f, 0.0016, 2, 35)
    part('Handguard_Pin', merge_vf(*[pinhead_vf((sg * 0.0305, -0.318, -0.012), (sg, 0, 0), 0.0030, 0.0010)
                                     for sg in (1, -1)]), 'Steel')
    return hg


def top_and_sights():
    base = plate_xz(fillet2([(0.013, 0.038, 0.0), (0.013, 0.0505, 0.0015), (-0.013, 0.0505, 0.0015), (-0.013, 0.038)]),
                    -0.150, 0.060)
    part('Rail_Base', base, 'Graphite', bev=(0.0010, 2, 35))
    rail_part('Rail', -0.148, 0.058, 0.0500)
    # front sight: hooded post on the receiver nose
    yf, zf = -0.282, 0.0665
    fb = plate_xz(fillet2([(0.010, 0.040), (0.0085, 0.058, 0.002), (-0.0085, 0.058, 0.002), (-0.010, 0.040)]),
                  yf - 0.007, yf + 0.007)
    hood = ring_y([(0.0086, yf - 0.007), (0.0118, yf - 0.007), (0.0118, yf + 0.007), (0.0086, yf + 0.007)], 24, cz=zf)
    fs = part('FrontSight', merge_vf(fb, hood), 'Blackened', bev=(0.0006, 2, 35))
    part('FrontSight_Post', merge_vf(cyl_vf((0, yf, zf - 0.0052), 0.0019, 0.008, 'Z', 10),
                                     cyl_vf((0, yf, zf - 0.0090), 0.0042, 0.003, 'Z', 12)), 'Steel')
    # rear sight: aperture block with protective ears
    yr, zr = 0.112, 0.0680
    rs_out = fillet2([(0.0125, 0.040), (0.0125, 0.077, 0.003), (0.0075, 0.080, 0.002), (0.0055, 0.071, 0.002),
                      (-0.0055, 0.071, 0.002), (-0.0075, 0.080, 0.002), (-0.0125, 0.077, 0.003), (-0.0125, 0.040)])
    rs = part('RearSight', plate_xz(rs_out, yr - 0.008, yr + 0.008), 'Blackened', wn=False)
    cut(rs, cyl_vf((0, yr, zr), 0.0024, 0.04, 'Y', 14))
    finish(rs, 0.0007, 2, 35)
    part('RearSight_Ring', ring_y([(0.0024, yr - 0.0095), (0.0045, yr - 0.0095), (0.0045, yr + 0.0095),
                                   (0.0024, yr + 0.0095)], 14, cz=zr), 'Steel')
    return zr


def bolt_and_handle():
    b = part('Bolt', loft_y([(y, sec(0.0195, 0.0195, 0.004, 0.042, 0.003, 0.010, 3)) for y in (-0.072, 0.120)]),
             'Steel', wn=False)
    cut(b, [slab(fillet2([(-0.040, 0.016, 0.002), (-0.004, 0.016, 0.002), (-0.004, 0.030, 0.002), (-0.040, 0.030, 0.002)]),
                 -0.03, -0.0172),
            cyl_vf((-0.0195, -0.020, 0.019), 0.0030, 0.006, 'X', 12)])
    finish(b, 0.0009, 2, 35)
    group(b, (0, -0.072, 0.023), 'translate', 'Y', 0.060, 'Cycle',
          'bolt: recoils 0.060 m rearward and returns once per shot (visible through the ejection port)')
    # cocking handle: carrier block in the slot + lever folded out 45 deg up-left with a mushroom knob
    blk = slab(fillet2([(-0.290, 0.023, 0.002), (-0.262, 0.023, 0.002), (-0.262, 0.031, 0.002), (-0.290, 0.031, 0.002)]),
               0.018, 0.031)
    d = V((0.0, 0.707, 0.707))     # lever direction in (x, ., z) via the (x, z) plane
    p0 = V((0.027, -0.276, 0.029))
    p1 = p0 + V((0.020, 0.0, 0.020))
    lev = sweep_vf([p0, p1], rrect2(0.009, 0.0065, 0.0022, 2))
    ch = part('ChargingHandle', merge_vf(blk, lev), 'Blackened', bev=(0.0006, 2, 35))
    kn = lathe_axis([(0, 0), (0.0068, 0), (0.0068, 0.008), (0.0055, 0.0115), (0, 0.0115)], 16, p1, (0.707, 0, 0.707))
    part('ChargingHandle_Knob', kn, 'PolyBlack', ch)
    group(ch, (0.025, -0.276, 0.027), 'translate', 'Y', 0.112, 'Charge',
          'cocking handle: pulled 0.112 m rearward along the slot to cock, then released')
    return b, ch


def stock():
    """skeleton side-folding stock, modelled FOLDED along the right side (rest)."""
    zu, zl = -0.004, -0.054             # strut centres
    y_front = PIV[1] - 0.360            # buttplate far face (folded)
    struts = []
    for zc in (zu, zl):
        struts.append(slab(fillet2([(y_front + 0.018, zc - 0.0048, 0.002), (0.214, zc - 0.0048, 0.002),
                                    (0.214, zc + 0.0048, 0.002), (y_front + 0.018, zc + 0.0048, 0.002)]),
                           SX - 0.0032, SX + 0.0032))
    brace = slab(fillet2([(0.060, zl, 0.0), (0.072, zl, 0.0), (0.040, zu, 0.0), (0.028, zu, 0.0)]), SX - 0.0028, SX + 0.0028)
    hplate = slab(fillet2([(0.204, zl - 0.0048, 0.003), (0.222, zl - 0.0048, 0.003), (0.222, zu + 0.0048, 0.003),
                           (0.204, zu + 0.0048, 0.003)]), SX - 0.0040, SX + 0.0040)
    # hinge arm entirely in front of the pivot and outside the end cap: clears the cap folded AND extended
    arm = box_between((SX - 0.004, PIV[1] - 0.012, -0.020), (PIV[0] - 0.002, PIV[1], 0.010))
    knuckle = cyl_vf((PIV[0], PIV[1], -0.005), 0.0068, 0.026, 'Z', 16)
    st = part('Stock', merge_vf(*struts, brace, hplate, arm), 'Blackened', bev=(0.0009, 2, 35))
    part('Stock_Knuckle', knuckle, 'Blackened', st, bev=(0.0006, 2, 35))
    # buttplate (faces forward while folded) + rubber pad
    bp_out = fillet2([(SX + 0.017, -0.074, 0.008), (SX + 0.019, 0.030, 0.010), (SX - 0.019, 0.030, 0.010),
                      (SX - 0.017, -0.074, 0.008)])
    bpl = part('Stock_Buttplate', prism([V((p[0], y_front + 0.004, p[1])) for p in bp_out], (0, 0.018, 0)), 'PolyBlack',
               st, wn=False)
    cut(bpl, [box_vf((SX, y_front + 0.016, z), (0.006, 0.010, 0.016)) for z in (-0.050, -0.022, 0.006)])
    finish(bpl, 0.0014, 2, 35)
    pad_out = fillet2([(SX + 0.0185, -0.077, 0.009), (SX + 0.0205, 0.033, 0.011), (SX - 0.0205, 0.033, 0.011),
                       (SX - 0.0185, -0.077, 0.009)])
    pad = part('Stock_Buttpad', prism([V((p[0], y_front - 0.002, p[1])) for p in pad_out], (0, 0.0075, 0)), 'Rubber', st,
               wn=False)
    finish(pad, 0.0012, 2, 35)
    detail(pad, [box_vf((SX, y_front - 0.003, -0.068 + k * 0.0095), (0.06, 0.0036, 0.0034)) for k in range(11)])
    group(st, (PIV[0], PIV[1], -0.005), 'rotate', 'Z', -180, 'StockFold',
          'side-folding stock: modelled folded along the right side; swings 180 deg outward and back to extend')
    return st


def build():
    r = begin('MAKO9')
    receiver()
    housing()
    grip()
    magazine()
    barrel_front()
    handguard()
    zr = top_and_sights()
    bolt_and_handle()
    stock()
    point('Muzzle', (0, -0.660 + DM, 0), 'muzzle', (0, -1, 0), note='bullet origin + muzzle flash (4-prong flash hider)')
    point('Ejection', (-HW - 0.004, -0.025, 0.023), 'ejection', (-0.80, 0.25, 0.55),
          note='spent cases leave the ejection port here (right side, above the folded stock)')
    point('Grip_Right', (0, 0.106, -0.128), 'grip_right', note='firing hand on the pistol grip')
    point('Grip_Left', (0, -0.395, -0.030), 'grip_left', note='support hand on the handguard, behind the hand stop')
    point('Aim', (0, 0.150, zr), 'aim_eye', (0, -1, 0), note='eye position behind the aperture rear sight')
    point('MagWell', (0, MAG_TOP[0], -0.100), 'magwell', (0, -0.10, -1))
    point('Sling', (HW + 0.025, 0.165, 0.048), 'sling')
    rig.model('Mako9', 'Mako-9', 'weapon', WEAPONS['MAKO9'][4],
              origin='on the bore axis directly above the trigger (all five weapons share this datum)')
    rig.channel('Trigger', 'trigger pull (0 = rest, 1 = pulled)', 0.05)
    rig.channel('Cycle', 'bolt cycle per shot: play 0 -> 1 -> 0 once per round', 0.04)
    rig.channel('Charge', 'cocking handle pulled back', 0.30, ['drive Cycle together with Charge while cocking'])
    rig.channel('Reload', 'magazine out (1) / in (0)', 0.8)
    rig.channel('StockFold', 'stock extended (1) / folded along the right side (0)', 0.45,
                ['folded stock: lower accuracy, faster handling; extended: shoulder-fired'])
    rig.pose('fire', {'Trigger': 1, 'Cycle': 1, 'StockFold': 1}, description='stock out, trigger pulled, bolt back',
             ground=False)
    rig.pose('reload', {'Reload': 1, 'Charge': 1, 'Cycle': 1}, description='magazine out, handle and bolt back',
             ground=False)
    rig.pose('stock_extended', {'StockFold': 1}, description='stock unfolded', ground=False)
    rig.system('Weapon', kind='submachine gun', caliber='9x21 mm (fictional)', magazine=32,
               fire_modes=['SAFE', 'SEMI', 'AUTO'], rpm=900, muzzle_velocity_mps=390,
               effective_range_studs=round(150 * S), reload_s=1.9, damage_hint='low-medium',
               recoil_hint='low; more spread with the stock folded', aim='aperture rear + hooded front post',
               ammo_item='Ammo_9x21')
    rig.note('Weapon origin = bore axis above the trigger; the muzzle points -Z in Roblox (LookVector).')
    rig.note('The stock group (MAKO9_Stock) rotates about a vertical hinge pin at its pivot; folded = rest.')
    return r
