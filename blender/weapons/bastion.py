"""Bastion LMG - belt-fed light machine gun (collection BASTION_LMG, export BastionLMG.fbx). Heaviest and broadest.

Target 5.0 x 1.8 x 0.75 studs (L x H x W) = 1.400 x 0.504 x 0.210 m.
Layout (y, metres; bore z = 0; origin above the trigger):
  flash hider -0.880..-0.802 | barrel to -0.205 | gas block + front sight tower -0.598..-0.566
  olive lower handguard -0.548..-0.232 under the barrel, perforated olive heat shield -0.540..-0.345 over it
  carry handle on the trunnion + a barrel clamp (-0.340..-0.205) | charcoal receiver -0.200..+0.205 with riveted
  reinforcement plates, hinged feed cover + small rail | belt feed on the RIGHT side from the ammo box hanging below
  | polymer trigger housing, textured grip, oversized open trigger guard | ribbed olive stock to +0.520
  folding bipod under the gas block, legs folded back under the handguard.
"""
from .lib import *
from . import parts as P

RY0, RY1 = -0.200, 0.205
HW = 0.044
ZB, ZT = -0.050, 0.030
FC = (-0.150, 0.078)              # feed cover y range
HINGE = (-0.150, 0.034)           # feed cover hinge (y, z)
BOX = (-0.026, -0.132, -0.205, -0.052, -0.072, -0.345)   # ammo box x0, x1, y0, y1, z top, z bottom
LID_Z = -0.098


def _sym(half, seg=3):
    return fillet2([(x, z, r) for x, z, r in half] + [(-x, z, r) for x, z, r in reversed(half)], seg)


def receiver():
    sec_ = _sym([(HW, ZB, 0.004), (HW, 0.020, 0.002), (0.036, ZT, 0.002)])
    side = fillet2([(RY0, ZB + 0.012), (RY0 + 0.014, ZB - 0.01), (RY1 + 0.01, ZB - 0.01), (RY1 + 0.01, 0.06),
                    (RY0, 0.06)])
    rc = part('Receiver', plate_xz(sec_, RY0, RY1), 'Graphite', wn=False)
    cut(rc, slab(side, -0.1, 0.1), 'INTERSECT')
    feed = slab(fillet2([(-0.122, -0.004, 0.004), (-0.048, -0.004, 0.004), (-0.048, 0.026, 0.004), (-0.122, 0.026, 0.004)]),
                -0.07, -0.020)
    eject = slab(fillet2([(-0.100, -0.012, 0.003), (-0.040, -0.012, 0.003), (-0.040, 0.010, 0.003), (-0.100, 0.010, 0.003)]),
                 0.020, 0.07)
    chs = slab(fillet2([(-0.190, -0.034, 0.004), (-0.038, -0.034, 0.004), (-0.038, -0.022, 0.004), (-0.190, -0.022, 0.004)]),
               0.030, 0.07)
    seam = [slab(fillet2([(-0.196, 0.0155, 0.001), (0.200, 0.0155, 0.001), (0.200, 0.0175, 0.001), (-0.196, 0.0175, 0.001)]),
                 sg * (HW - 0.0012), sg * 0.07) for sg in (1, -1)]
    cut(rc, [feed, eject, chs, cyl_vf((0, RY0, 0), 0.0185, 0.03, 'Y', 24)] + seam)
    finish(rc, 0.0018, 2, 35)
    # riveted reinforcement plates (both sides), cut for the feed / ejection / charging openings
    pl = fillet2([(-0.188, -0.046, 0.005), (0.192, -0.046, 0.005), (0.192, 0.012, 0.005), (-0.188, 0.012, 0.005)])
    for sg, S_ in ((1, 'L'), (-1, 'R')):
        p_ = part('ReinforcePlate_%s' % S_, slab(pl, sg * (HW - 0.0005), sg * (HW + 0.0028)), 'Blackened', wn=False)
        cut(p_, [feed, eject, chs])
        finish(p_, 0.0010, 2, 35)
        riv = []
        for k in range(12):
            y = -0.176 + k * 0.0325
            for z in (0.0065, -0.0405):
                if sg < 0 and -0.126 < y < -0.044 and z > 0:
                    continue
                if sg > 0 and -0.104 < y < -0.036 and z > 0:
                    continue
                riv.append(rivet_vf(V((sg * (HW + 0.0028), y, z)), V((sg, 0, 0)), 0.0042))
        part('ReinforcePlate_%s_Rivets' % S_, merge_vf(*riv), 'Steel')
        if sg > 0:
            marking(p_, 'BASTION LMG', (HW + 0.0028, 0.086, -0.018), (1, 0, 0), 0.0105)
            marking(p_, 'SI-7730', (HW + 0.0028, 0.086, -0.032), (1, 0, 0), 0.0060)
        else:
            marking(p_, 'HAVEN  7.8x51  BELT', (-HW - 0.0028, 0.086, -0.018), (-1, 0, 0), 0.0072)
    # barrel trunnion / quick-change collar + barrel latch (left)
    tr = plate_xz(_sym([(0.032, -0.044, 0.006), (0.034, 0.016, 0.006), (0.024, 0.028, 0.004)]), -0.228, -0.1985)
    part('Trunnion', tr, 'Blackened', bev=(0.0016, 2, 35))
    part('BarrelLatch', merge_vf(slab(fillet2([(-0.224, -0.030, 0.003), (-0.204, -0.030, 0.003), (-0.204, -0.014, 0.003),
                                               (-0.224, -0.014, 0.003)]), 0.0330, 0.0370),
                                 cyl_vf((0.0370, -0.214, -0.022), 0.0055, 0.004, 'X', 14)), 'Steel', bev=(0.0005, 1, 35))
    return rc


def feed_cover():
    sec_ = _sym([(0.040, ZT - 0.0012, 0.002), (0.040, 0.050, 0.006), (0.028, 0.058, 0.004)])
    side = fillet2([(FC[0], 0.020), (FC[1], 0.020), (FC[1], 0.07), (FC[0] + 0.026, 0.07), (FC[0], 0.046, 0.006)])
    fc = part('FeedCover', plate_xz(sec_, FC[0], FC[1]), 'Blackened', wn=False)
    cut(fc, slab(side, -0.1, 0.1), 'INTERSECT')
    cut(fc, [slab(fillet2([(-0.118, 0.040, 0.003), (0.060, 0.040, 0.003), (0.060, 0.046, 0.003), (-0.118, 0.046, 0.003)]),
                  sg * 0.0385, sg * 0.06) for sg in (1, -1)])
    finish(fc, 0.0014, 2, 35)
    rail_part('FeedCover_Rail', -0.118, 0.034, 0.0575, parent=fc)
    b, leaf, hole, ring, hinge, hp = P.flip_rear_sight(0.040, 0.070, 0.0575)
    part('RearSight_Base', b, 'Blackened', fc, bev=(0.0008, 2, 35))
    lf = part('RearSight_Leaf', leaf, 'Blackened', fc, wn=False)
    cut(lf, hole)
    finish(lf, 0.0006, 2, 35)
    part('RearSight_Ring', ring, 'Blackened', lf)
    part('RearSight_Hinge', hinge, 'Steel', fc)
    tabs = [slab(fillet2([(0.060, 0.040, 0.002), (0.074, 0.040, 0.002), (0.074, 0.052, 0.002), (0.060, 0.052, 0.002)]),
                 sg * 0.0392, sg * 0.0448) for sg in (1, -1)]
    part('FeedCover_Latches', merge_vf(*tabs), 'Steel', fc, bev=(0.0005, 1, 35))
    kn = cyl_vf((0, HINGE[0], HINGE[1]), 0.0062, 0.040, 'X', 16)
    part('FeedCover_Knuckle', kn, 'Blackened', fc)
    fixed = [cyl_vf((sg * 0.031, HINGE[0], HINGE[1]), 0.0062, 0.020, 'X', 16) for sg in (1, -1)]
    part('FeedCover_HingeBlocks', merge_vf(*fixed), 'Graphite', bev=(0.0006, 1, 35))
    part('FeedCover_HingePin', cyl_vf((0, HINGE[0], HINGE[1]), 0.0025, 0.086, 'X', 12), 'Steel')
    group(fc, (0, HINGE[0], HINGE[1]), 'rotate', 'X', 80, 'FeedCover',
          'feed cover: hinged at its front, lifts 80 deg to lay a new belt on the feed tray')
    return fc


def internals():
    b = part('Bolt', loft_y([(y, sec(0.022, 0.022, -0.020, 0.016, 0.004, 0.004, 3)) for y in (-0.110, 0.120)]),
             'Steel', wn=False)
    cut(b, [slab(fillet2([(-0.090, -0.006, 0.002), (-0.050, -0.006, 0.002), (-0.050, 0.004, 0.002), (-0.090, 0.004, 0.002)]),
                 0.017, 0.03)])
    finish(b, 0.0010, 2, 35)
    group(b, (0, -0.110, -0.002), 'translate', 'Y', 0.070, 'Cycle',
          'bolt: recoils 0.070 m and returns per shot (visible through the left ejection port)')
    # charging handle (left): carrier in the slot + folding T handle
    blk = slab(fillet2([(-0.186, -0.033, 0.002), (-0.160, -0.033, 0.002), (-0.160, -0.023, 0.002), (-0.186, -0.023, 0.002)]),
               0.026, HW + 0.002)
    arm = slab(fillet2([(-0.182, -0.032, 0.002), (-0.164, -0.032, 0.002), (-0.166, -0.024, 0.002), (-0.180, -0.024, 0.002)]),
               HW, HW + 0.024)
    tee = lathe_axis([(0, -0.016), (0.0058, -0.016), (0.0066, -0.012), (0.0066, 0.012), (0.0058, 0.016), (0, 0.016)], 14,
                     (HW + 0.026, -0.173, -0.028), 'Y')
    ch = part('ChargingHandle', merge_vf(blk, arm), 'Blackened', bev=(0.0007, 2, 35))
    part('ChargingHandle_Tee', tee, 'PolyBlack', ch)
    group(ch, (HW, -0.173, -0.028), 'translate', 'Y', 0.118, 'Charge',
          'charging handle (left): pulled 0.118 m back to cock the open bolt, then pushed forward again')


def lower():
    prof = fillet2([(-0.040, ZB - 0.001, 0.002), (-0.040, -0.082, 0.008), (0.135, -0.088, 0.010), (0.158, -0.062, 0.010),
                    (0.158, ZB - 0.001, 0.002)])
    lw = part('TriggerHousing', slab(prof, -0.034, 0.034), 'PolyBlack', wn=False)
    cut(lw, box_between((-0.006, -0.022, -0.10), (0.006, 0.014, -0.06)))
    finish(lw, 0.0016, 2, 35)
    part('Housing_Pins', merge_vf(*[pinhead_vf((sg * 0.034, y, -0.060), (sg, 0, 0), 0.0034, 0.0011)
                                    for y in (-0.024, 0.140) for sg in (1, -1)]), 'Steel')
    sf = part('Safety', lathe_axis([(0, -0.040), (0.0046, -0.040), (0.0050, -0.037), (0.0050, 0.037), (0.0046, 0.040),
                                    (0, 0.040)], 14, (0.004, 0.066, -0.066), 'X'), 'Steel')
    group(sf, (0.004, 0.066, -0.066), 'translate', 'X', -0.008, 'Safety',
          'cross-bolt safety: pushed 8 mm from left to right = FIRE (red band shows); rest = SAFE')
    part('Safety_RedBand', lathe_axis([(0.0049, 0.027), (0.0053, 0.027), (0.0053, 0.033), (0.0049, 0.033), (0.0049, 0.027)],
                                      14, (0.004, 0.066, -0.066), 'X', False, False), 'MarkRed', sf)
    part('TriggerGuard', P.guard_vf([(-0.034, -0.084), (-0.028, -0.130, 0.013), (0.050, -0.132, 0.015), (0.072, -0.100)],
                                    0.0105, 0.0052, 0.0034), 'PolyBlack')
    trig = part('Trigger', P.trigger_vf((-0.002, -0.070), (-0.012, -0.114), 0.009, 0.0050, 0.0036), 'Steel')
    group(trig, (0, -0.003, -0.072), 'rotate', 'X', 14, 'Trigger', 'trigger: 14 deg rearward; hold = automatic fire')
    top, bot = (0.094, -0.080), (0.126, -0.220)
    fr = P.Frame(top, bot)
    w0, w1 = 0.0210, 0.0232
    g = part('Grip', P.grip_vf(top, bot, w0, w1, -0.031, 0.032, 0.037, fingers=3, finger_depth=0.0042,
                               finger_range=(0.16, 0.86), flare=0.003), 'PolyBlack', wn=False)
    finish(g, 0.0014, 2, 40)
    cut(g, P.checker_cutters(fr, lambda s_: w0 + (w1 - w0) * s_ / fr.L, fr.L * 0.18, fr.L * 0.84, -0.020, 0.026, 0.0085,
                             45.0, 0.0018, 0.0013))
    weighted(g)


def barrel_front():
    prof = [(0, -0.788), (0.0062, -0.788), (0.0062, -0.802), (0.0150, -0.802), (0.0150, -0.795), (0.0175, -0.792),
            (0.0175, -0.250), (0.0198, -0.238), (0.0198, -0.205), (0, -0.205)]
    part('Barrel', lathe_axis(prof, 28, (0, 0, 0), 'Y'), 'DarkSteel')
    solid, cuts = P.birdcage_vf(-0.880, 0.078, 0.0215, 0.0068, 6, 0.0050, 0.046, closed_bottom=True)
    fh = part('Muzzle_FlashHider', solid, 'Blackened', wn=False)
    finish(fh, 0.0008, 2, 35)
    detail(fh, cuts)
    part('Muzzle_LockNut', ring_y([(0.0150, -0.803), (0.0196, -0.803), (0.0196, -0.795), (0.0150, -0.795)], 6), 'Steel',
         bev=(0.0005, 1, 35))
    # gas cylinder under the barrel + gas block with the front-sight tower
    part('GasCylinder', lathe_axis([(0, -0.575), (0.0120, -0.575), (0.0120, -0.226), (0, -0.226)], 18, (0, 0, -0.036), 'Y'),
         'Blackened')
    gbo = fillet2([(0.020, -0.054, 0.008), (0.022, 0.006, 0.010), (-0.022, 0.006, 0.010), (-0.020, -0.054, 0.008)])
    gb = part('GasBlock', plate_xz(gbo, -0.598, -0.566), 'Blackened', bev=(0.0014, 2, 35))
    tower = fillet2([(0.016, 0.000), (0.016, 0.064, 0.003), (0.0105, 0.084, 0.003), (0.0060, 0.084, 0.002),
                     (0.0060, 0.060, 0.004), (-0.0060, 0.060, 0.004), (-0.0060, 0.084, 0.002), (-0.0105, 0.084, 0.003),
                     (-0.016, 0.064, 0.003), (-0.016, 0.000)])
    ft = part('FrontSight', plate_xz(tower, -0.592, -0.578), 'Blackened', wn=False)
    cut(ft, cyl_vf((0, -0.585, 0.030), 0.0060, 0.04, 'Y', 14))
    finish(ft, 0.0010, 2, 35)
    part('FrontSight_Post', merge_vf(cyl_vf((0, -0.585, 0.0640), 0.0026, 0.010, 'Z', 10),
                                     lathe_axis([(0, 0), (0.0016, 0), (0.0016, 0.012), (0.0009, 0.0135), (0, 0.0135)], 10,
                                                (0, -0.585, 0.068), 'Z')), 'Steel')
    part('GasRegulator', lathe_axis([(0, 0), (0.0095, 0), (0.0095, 0.008), (0.0082, 0.010), (0, 0.010)], 6,
                                    (0, -0.598, -0.036), '-Y'), 'Steel')


def handguard():
    Y0, Y1 = -0.548, -0.232
    outer = _sym([(0.024, -0.075, 0.012), (0.033, -0.050, 0.008), (0.031, -0.016, 0.005)])
    hg = part('Handguard', plate_xz(outer, Y0, Y1), 'PolyOlive', wn=False)
    cuts = [cyl_vf((0, -0.39, -0.036), 0.0135, 0.40, 'Y', 18), cyl_vf((0, -0.39, 0.0), 0.0190, 0.40, 'Y', 24)]
    for sg in (1, -1):
        for row, zc in enumerate((-0.034, -0.054)):
            for k in range(5):
                cuts.append(slab(stadium2(-0.512 + k * 0.058 + row * 0.029, zc, 0.034, 0.0085), sg * 0.02, sg * 0.06))
    for k in range(9):
        cuts.append(box_vf((0, -0.528 + k * 0.032, -0.076), (0.08, 0.0055, 0.008)))
    finish(hg, 0.0020, 2, 35)
    detail(hg, cuts)
    # perforated heat shield arching over the barrel (+ two retaining clips)
    a0, a1 = radians(-40), radians(220)
    arc_o = [(0.0262 * cos(a0 + (a1 - a0) * k / 24), 0.0262 * sin(a0 + (a1 - a0) * k / 24)) for k in range(25)]
    arc_i = [(0.0222 * cos(a1 - (a1 - a0) * k / 24), 0.0222 * sin(a1 - (a1 - a0) * k / 24)) for k in range(25)]
    hs = part('HeatShield', plate_xz(arc_o + arc_i, -0.540, -0.345), 'PaintOlive', wn=False)
    hcuts = []
    for k in range(6):
        yc = -0.522 + k * 0.032
        hcuts.append(plate_xy(stadium2(0, yc, 0.022, 0.0080, pi / 2), 0.0, 0.05))
        for sg in (1, -1):
            hcuts.append(slab(stadium2(yc + 0.016, 0.006, 0.016, 0.0070), sg * 0.01, sg * 0.05))
    finish(hs, 0.0008, 2, 35)
    detail(hs, hcuts)
    clips = [ring_y([(0.0258, y), (0.0284, y), (0.0284, y + 0.007), (0.0258, y + 0.007)], 24, cz=0.0) for y in
             (-0.534, -0.360)]
    part('HeatShield_Clips', merge_vf(*clips), 'Blackened', bev=(0.0005, 1, 35))
    cup, loop = P.qd_loop((0.0328, -0.300, -0.050), (1, 0, 0))
    part('Sling_Front_Socket', cup, 'Blackened')
    part('Sling_Front_Loop', loop, 'Steel')


def carry_handle():
    path = fillet2([(-0.333, 0.012), (-0.333, 0.112, 0.020), (-0.212, 0.112, 0.020), (-0.212, 0.024)], 6, closed=False)
    bar = sweep_yz(path, lambda i, s: fillet2([(0.0085, -0.0062, 0.003), (0.0085, 0.0062, 0.003), (-0.0085, 0.0062, 0.003),
                                               (-0.0085, -0.0062, 0.003)], 2))
    ch = part('CarryHandle', bar, 'Blackened', bev=(0.0008, 2, 35))
    clamp = ring_y([(0.0170, -0.342), (0.0245, -0.342), (0.0245, -0.324), (0.0170, -0.324)], 24)
    part('CarryHandle_Clamp', clamp, 'Blackened', bev=(0.0008, 1, 35))
    part('CarryHandle_ClampScrew', screw_vf((-0.0245, -0.333, -0.004), (-1, 0, 0), 0.0040, 0.0016), 'Steel')
    sl = part('CarryHandle_Grip', loft_y([(y, fillet2([(0.0118, 0.1020, 0.004), (0.0118, 0.1220, 0.004),
                                                         (-0.0118, 0.1220, 0.004), (-0.0118, 0.1020, 0.004)], 2))
                                           for y in (-0.300, -0.245)]), 'PolyBlack', ch, wn=False)
    finish(sl, 0.0012, 2, 35)
    detail(sl, [box_vf((0, -0.296 + k * 0.0075, 0.112), (0.04, 0.0028, 0.04)) for k in range(7)])
    return ch


def stock():
    out = fillet2([(0.200, 0.026, 0.004), (0.330, 0.030, 0.030), (0.505, 0.034, 0.008), (0.505, -0.150, 0.010),
                   (0.455, -0.153, 0.020), (0.398, -0.112, 0.020), (0.362, -0.123, 0.022), (0.255, -0.068, 0.040),
                   (0.200, -0.052, 0.004)])
    plan = fillet2([(0.031, 0.19, 0.0), (0.031, 0.26, 0.04), (0.034, 0.36, 0.04), (0.034, 0.52, 0.0), (-0.034, 0.52, 0.0),
                    (-0.034, 0.36, 0.04), (-0.031, 0.26, 0.04), (-0.031, 0.19, 0.0)])
    st = part('Stock', slab(out, -0.04, 0.04), 'PolyOlive', wn=False)
    cut(st, plate_xy(plan, -0.3, 0.2), 'INTERSECT')
    finish(st, 0.0050, 3, 30)
    ribs = []
    for sg in (1, -1):
        for zc, y0 in ((0.010, 0.250), (-0.014, 0.250), (-0.038, 0.300)):
            ribs.append(slab(fillet2([(y0, zc - 0.0016, 0.0016), (0.488, zc - 0.0016, 0.0016), (0.488, zc + 0.0016, 0.0016),
                                      (y0, zc + 0.0016, 0.0016)]), sg * 0.0322, sg * 0.06))
    cut(st, ribs)
    weighted(st)
    marking(st, 'B-7', (0.0339, 0.440, -0.072), (1, 0, 0), 0.0130)
    cup, loop = P.qd_loop((0.0335, 0.470, -0.120), (1, 0, 0))
    part('Sling_Rear_Socket', cup, 'Blackened')
    part('Sling_Rear_Loop', loop, 'Steel')
    po = fillet2([(0.0365, -0.156, 0.012), (0.0365, 0.038, 0.014), (-0.0365, 0.038, 0.014), (-0.0365, -0.156, 0.012)])
    pad = part('Stock_Buttpad', plate_xz(po, 0.503, 0.521), 'Rubber', wn=False)
    finish(pad, 0.0020, 2, 35)
    detail(pad, [box_vf((0, 0.5225, -0.144 + k * 0.0135), (0.09, 0.006, 0.0048)) for k in range(14)])
    part('Stock_Plate', plate_xz(_sym([(0.030, -0.050, 0.004), (0.031, 0.022, 0.004), (0.026, 0.028, 0.003)]), 0.2035, 0.2085),
         'Blackened', bev=(0.0008, 1, 35))


def ammo_box():
    x0, x1, y0, y1, zt, zb = BOX
    body = part('AmmoBox', box_between((x0, y0, zb), (x1, y1, LID_Z - 0.0008)), 'PaintOliveDark', wn=False)
    finish(body, 0.0035, 1, 35)                                       # chamfer the box, then open its top
    cut(body, [box_between((x0 - 0.003, y0 + 0.003, LID_Z - 0.010), (x1 + 0.003, y1 - 0.003, LID_Z + 0.01))])
    weighted(body)
    ribs = [box_between((x1 - 0.0025, y0 + 0.012, z - 0.006), (x1 + 0.0005, y1 - 0.012, z + 0.006)) for z in (-0.165, -0.290)]
    ribs += [box_between((x0 - 0.004, y0 + 0.012, zb - 0.0035), (x1 + 0.004, y0 + 0.024, zb + 0.002)),
             box_between((x0 - 0.004, y1 - 0.024, zb - 0.0035), (x1 + 0.004, y1 - 0.012, zb + 0.002))]
    part('AmmoBox_Ribs', merge_vf(*ribs), 'PaintOliveDark', body, bev=(0.0012, 1, 35))
    marking(body, '200', (x1, -0.128, -0.228), (-1, 0, 0), 0.030)
    marking(body, '7.8 LINKED', (x1, -0.128, -0.252), (-1, 0, 0), 0.0105)
    # latch: clasp lever on the body front reaching over the lid seam
    lat = merge_vf(plate_xz(fillet2([(-0.092, -0.124, 0.003), (-0.066, -0.124, 0.003), (-0.066, -0.090, 0.003),
                                     (-0.092, -0.090, 0.003)]), y0 - 0.0040, y0 + 0.0004),
                   cyl_vf((-0.079, y0 - 0.0030, -0.123), 0.0030, 0.030, 'X', 10))
    part('AmmoBox_Latch', lat, 'Steel', body, bev=(0.0006, 1, 35))
    # lid (hinged on the outer top edge), with the belt exit slot near the receiver
    lid = part('AmmoBox_Lid', box_between((x0 + 0.002, y0 - 0.002, LID_Z), (x1 - 0.002, y1 + 0.002, zt)), 'PaintOliveDark',
               body, wn=False)
    cut(lid, box_between((-0.036, -0.126, LID_Z - 0.01), (-0.068, -0.054, zt + 0.01)))
    finish(lid, 0.0030, 1, 35)
    part('AmmoBox_LidCatch', box_between((-0.086, y0 - 0.0060, -0.094), (-0.072, y0 - 0.0015, -0.080)), 'Steel', lid,
         bev=(0.0005, 1, 35))
    kn = [cyl_vf((x1 - 0.0030, yc, LID_Z), 0.0042, 0.026, 'Y', 12) for yc in (-0.186, -0.128, -0.071)]
    part('AmmoBox_LidHinge', merge_vf(*kn), 'Blackened', lid, bev=(0.0005, 1, 35))
    group(lid, (x1 - 0.0030, -0.128, LID_Z), 'rotate', 'Y', -100, 'BoxLid',
          'ammo box lid: swings 100 deg outward on its hinge to refill the box')
    # mount bracket (stays on the gun) + its latch buttons
    br = box_between((-0.004, y0 + 0.010, zt - 0.0004), (-0.034, y1 - 0.013, ZB + 0.001))
    part('AmmoBox_Mount', br, 'Blackened', bev=(0.0010, 2, 35))
    part('AmmoBox_MountButtons', merge_vf(*[cyl_vf((-0.0345, yc, -0.061), 0.0040, 0.004, 'X', 12) for yc in
                                            (y0 + 0.022, y1 - 0.025)]), 'Steel')
    group(body, (0.5 * (x0 + x1), 0.5 * (y0 + y1), zt), 'translate', 'Z', -0.18, 'Reload',
          'ammo box: unlatches from its mount and drops 0.18 m (stage 0.3-1, after the feed cover is open)',
          stage=(0.3, 1.0))
    return body


def belt():
    """short decorative linked belt from the box lid up into the right-side feed port: 8 cartridges + links (2 objects)."""
    path = [V((-0.052, 0, -0.080)), V((-0.060, 0, -0.054)), V((-0.062, 0, -0.028)), V((-0.058, 0, -0.004)),
            V((-0.046, 0, 0.010)), V((-0.030, 0, 0.012))]
    acc = [0.0]
    for i in range(1, len(path)):
        acc.append(acc[-1] + (path[i] - path[i - 1]).length)
    pitch = 0.0140
    cases, bullets, links = [], [], []
    centers = []
    s = 0.004
    while s < acc[-1] - 0.002 and len(centers) < 8:
        for i in range(1, len(path)):
            if acc[i] >= s:
                k = (s - acc[i - 1]) / (acc[i] - acc[i - 1])
                centers.append(path[i - 1].lerp(path[i], k))
                break
        s += pitch
    case_prof = [(0, -0.050), (0.0068, -0.050), (0.0068, -0.053), (0.0058, -0.054), (0.0064, -0.056), (0.0064, -0.089),
                 (0.0056, -0.094), (0.0041, -0.097), (0.0041, -0.104), (0, -0.104)]
    bul_prof = [(0, -0.1035), (0.0039, -0.1035), (0.0038, -0.110), (0.0028, -0.117), (0.0010, -0.1205), (0, -0.1208)]
    for c in centers:
        cases.append(orient(lathe_vf([(r, -y) for r, y in case_prof], 14), (c.x, 0, c.z), '-Y'))
        bullets.append(orient(lathe_vf([(r, -y) for r, y in bul_prof], 12), (c.x, 0, c.z), '-Y'))
        for yc in (-0.088, -0.064):
            links.append(ring_y([(0.0066, yc - 0.0026), (0.0076, yc - 0.0026), (0.0076, yc + 0.0026), (0.0066, yc + 0.0026)],
                                12, cx=c.x, cz=c.z))
    for a, b in zip(centers[:-1], centers[1:]):
        d = (b - a)
        for yc in (-0.088, -0.064):
            links.append(box_vf(((a.x + b.x) / 2, yc, (a.z + b.z) / 2), (abs(d.x) + 0.003, 0.0052, abs(d.z) + 0.003)))
    cv, cf = merge_vf(*cases)
    bv, bf = merge_vf(*bullets)
    vf = merge_vf((cv, cf), (bv, bf))
    mi = [0] * len(cf) + [1] * len(bf)
    bl = part('Belt_Cartridges', vf, ['Brass', 'Copper'], mat_idx=mi)
    part('Belt_Links', merge_vf(*links), 'Blackened', bl)
    group(bl, (-0.046, -0.085, -0.020), 'fixed', None, None, None,
          'decorative linked belt (8 rounds): hide it while the feed cover is open / during reload', kind='store',
          store='belt')
    return bl


def bipod():
    zy = -0.054
    yoke = merge_vf(plate_xz(fillet2([(0.016, zy + 0.002), (0.016, -0.084, 0.004), (-0.016, -0.084, 0.004), (-0.016, zy + 0.002)]),
                             -0.596, -0.568),
                    cyl_vf((0, -0.582, -0.088), 0.0068, 0.040, 'X', 14))
    part('Bipod_Yoke', yoke, 'Blackened', bev=(0.0010, 2, 35))
    part('Bipod_HingePin', merge_vf(cyl_vf((0, -0.582, -0.088), 0.0026, 0.074, 'X', 12),
                                    *[cyl_vf((sg * 0.0365, -0.582, -0.088), 0.0042, 0.0025, 'X', 12) for sg in (1, -1)]),
         'Steel')
    hz, hy = -0.088, -0.582
    for sg, S_ in ((1, 'L'), (-1, 'R')):
        x = sg * 0.0275
        kn = cyl_vf((x, hy, hz), 0.0085, 0.014, 'X', 16)
        up = sweep_vf([V((x, hy + 0.004, hz)), V((x, hy + 0.180, hz))], rrect2(0.0150, 0.0118, 0.0045, 2))
        lg = part('BipodLeg_%s' % S_, merge_vf(kn, up), 'Blackened', bev=(0.0008, 2, 35))
        part('BipodLeg_%s_Lower' % S_, lathe_axis([(0, 0), (0.0055, 0), (0.0055, 0.060), (0, 0.060)], 14,
                                                  (x, hy + 0.172, hz), 'Y'), 'Steel', lg)
        part('BipodLeg_%s_Button' % S_, cyl_vf((x + sg * 0.0060, hy + 0.165, hz), 0.0030, 0.004, 'X', 10), 'Steel', lg)
        foot = merge_vf(lathe_axis([(0, 0), (0.0078, 0), (0.0095, 0.006), (0.0095, 0.011), (0.0060, 0.016), (0, 0.016)], 16,
                                   (x, hy + 0.228, hz), 'Y'))
        part('BipodLeg_%s_Foot' % S_, foot, 'Rubber', lg)
        group(lg, (x, hy, hz), 'rotate', 'X', -90, 'Bipod',
              'bipod leg: folded back under the handguard; swings 90 deg down to deploy')
    return hz


def build():
    r = begin('BLMG')
    receiver()
    feed_cover()
    internals()
    lower()
    barrel_front()
    handguard()
    carry_handle()
    stock()
    ammo_box()
    belt()
    hz = bipod()
    point('Muzzle', (0, -0.880, 0), 'muzzle', (0, -1, 0), note='bullet origin + muzzle flash (long 6-prong flash hider)')
    point('Ejection', (HW + 0.004, -0.070, -0.001), 'ejection', (0.85, 0.15, 0.35),
          note='spent cases leave the LEFT ejection port; links drop below')
    point('BeltFeed', (-HW - 0.004, -0.085, 0.012), 'belt_feed', (1, 0, 0), note='belt enters the feed tray (right side)')
    point('Grip_Right', (0, 0.114, -0.150), 'grip_right', note='firing hand on the pistol grip')
    point('Grip_Left', (0, -0.420, -0.072), 'grip_left', note='support hand under the handguard (or on the carry handle)')
    point('Carry', (0, -0.272, 0.118), 'carry_handle', note='hand position when carrying the gun one-handed')
    point('Aim', (0, 0.150, 0.090), 'aim_eye', (0, -1, 0), note='eye position behind the aperture rear sight')
    point('BipodFeet', (0, -0.582, hz - 0.244), 'bipod_contact', note='feet contact point with Bipod = 1')
    point('Sling_Front', (0.0518, -0.300, -0.050), 'sling')
    point('Sling_Rear', (0.0525, 0.470, -0.120), 'sling')
    rig.model('BastionLMG', 'Bastion LMG', 'weapon', WEAPONS['BLMG'][4],
              origin='on the bore axis directly above the trigger (all five weapons share this datum)')
    rig.channel('Trigger', 'trigger pull (hold for automatic fire)', 0.05)
    rig.channel('Cycle', 'bolt cycle per shot: play 0 -> 1 -> 0 once per round (open-bolt gun)', 0.05)
    rig.channel('Charge', 'charging handle pulled back', 0.4)
    rig.channel('Safety', 'safety off (1) / on (0)', 0.1)
    rig.channel('FeedCover', 'feed cover open (1) / closed (0)', 0.5,
                ['reload order: FeedCover 1 -> hide BLMG_Belt -> Reload 1 (box drops) -> Reload 0 (new box) -> '
                 'show BLMG_Belt -> FeedCover 0 -> Charge 1 -> 0'])
    rig.channel('Reload', 'ammo box removed (1) / mounted (0)', 1.2)
    rig.channel('BoxLid', 'ammo box lid open (1) / closed (0)', 0.4)
    rig.channel('Bipod', 'bipod deployed (1) / folded (0)', 0.6, ['deployed: prone / rested fire with much less spread'])
    rig.pose('fire', {'Trigger': 1, 'Cycle': 1, 'Safety': 1, 'Bipod': 1}, description='bipod down, firing', ground=False)
    rig.pose('reload', {'FeedCover': 1, 'Reload': 1, 'BoxLid': 1}, description='feed cover open, box off with lid open',
             ground=False)
    rig.pose('charge', {'Charge': 1, 'Cycle': 1}, description='charging handle and bolt back', ground=False)
    rig.system('Weapon', kind='light machine gun (belt fed, open bolt)', caliber='7.8x51 mm (fictional)', magazine=200,
               feed='linked belt from the side ammo box', fire_modes=['SAFE', 'AUTO'], rpm=750, muzzle_velocity_mps=840,
               effective_range_studs=round(600 * S), reload_s=5.5, damage_hint='medium-high',
               recoil_hint='heavy, sustained climb; much lower on the bipod', aim='aperture rear on the feed cover + tower front',
               movement_hint='slow while carried; very slow while firing standing', ammo_item='AmmoBelt_7.8x51')
    rig.note('Weapon origin = bore axis above the trigger; the muzzle points -Z in Roblox (LookVector).')
    rig.note('BLMG_Belt is a decorative 8-round belt (kind=store): hide it during reload, show it when the box is back.')
    return r
