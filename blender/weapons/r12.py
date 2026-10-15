"""Roadrunner R-12 - scavenger carbine (collection ROADRUNNER_R12, export RoadrunnerR12.fbx).

Target 4.6 x 1.4 x 0.6 studs (L x H x W) = 1.288 x 0.392 x 0.168 m.
Layout (y, metres; muzzle -0.800 ... buttpad +0.488; bore z = 0; origin above the trigger):
  compensator -0.800..-0.703 | barrel to -0.166 | handguard -0.520..-0.172 | upper receiver -0.170..+0.205
  lower receiver -0.135..+0.170 (magwell -0.135..-0.050) | grip +0.05..+0.16 | buffer tube +0.205..+0.444
  stock body +0.300..+0.468 | rubber buttpad +0.466..+0.488
Finish: olive-gray painted receiver, graphite handguard, black polymer grip + stock, faded tan magazine with a black
baseplate, dark-steel barrel, blackened optic. Hero side = the weapon's RIGHT (-X): ejection port, bolt, side panel.
"""
from .lib import *
from . import parts as P

ZS = -0.030          # upper / lower seam (upper bottom)
UY0, UY1 = -0.170, 0.205
UTOP = 0.044         # upper deck (rail base)
HW_U = 0.040         # upper half width
HW_L = 0.034         # lower half width
RAIL_Z = UTOP - 0.0006
MAG_TOP = (-0.0915, -0.040)
SEL = (0.078, -0.050)  # selector pivot (y, z), left side


def upper():
    sec_ = [(HW_U, ZS), (HW_U, 0.026), (0.026, UTOP), (-0.026, UTOP), (-HW_U, 0.026), (-HW_U, ZS)]
    side = fillet2([(UY0, ZS - 0.01), (UY1 + 0.01, ZS - 0.01), (UY1 + 0.01, 0.016), (UY1, 0.016),
                    (UY1 - 0.010, UTOP + 0.01), (UY0, UTOP + 0.01)])
    up = part('Receiver_Upper', plate_xz(sec_, UY0, UY1), 'PaintOliveGray', wn=False)
    cut(up, slab(side, -0.1, 0.1), 'INTERSECT')
    cuts = []
    # ejection port (right side): a deep window that shows the bolt
    cuts.append(slab(fillet2([(-0.022, -0.013, 0.003), (0.066, -0.013, 0.003), (0.066, 0.019, 0.003),
                              (-0.022, 0.019, 0.003)]), -0.06, -0.010))
    # charging-handle channel (left side)
    cuts.append(slab(fillet2([(-0.146, 0.005, 0.0035), (0.036, 0.005, 0.0035), (0.036, 0.0175, 0.0035),
                              (-0.146, 0.0175, 0.0035)]), 0.028, 0.06))
    # machined flutes: left side front, right side rear (two rows)
    flutes = [(1, -0.150, -0.032, -0.0175), (-1, 0.100, 0.190, -0.0175), (-1, 0.100, 0.190, -0.0040)]
    for sg, y_a, y_b, zc in flutes:
        cuts.append(slab(fillet2([(y_a, zc - 0.0028, 0.0028), (y_b, zc - 0.0028, 0.0028), (y_b, zc + 0.0028, 0.0028),
                                  (y_a, zc + 0.0028, 0.0028)]), sg * (HW_U - 0.0016), sg * (HW_U + 0.02)))
    cuts.append(cyl_vf((0, UY0, 0), 0.0165, 0.03, 'Y', 24))           # barrel bore through the front face
    cut(up, cuts)
    finish(up, 0.0016, 2, 35)
    marking(up, 'ROADRUNNER', (HW_U, 0.135, -0.0185), (1, 0, 0), 0.0072)
    # brass deflector bump behind the port
    defl = loft_y([(0.068, sec(0.003, 0.003, 0.008, 0.028, 0.0015, 0.0015, 2, xc=-HW_U + 0.001)),
                   (0.080, sec(0.0062, 0.0062, 0.010, 0.030, 0.002, 0.002, 2, xc=-HW_U - 0.002)),
                   (0.094, sec(0.0062, 0.0062, 0.010, 0.030, 0.002, 0.002, 2, xc=-HW_U - 0.002))])
    part('Receiver_Deflector', defl, 'PaintOliveGray', bev=(0.0010, 2, 30))
    # side panel: riveted scavenger repair plate on the right, ahead of the port
    pl = fillet2([(-0.158, -0.025, 0.004), (-0.034, -0.025, 0.004), (-0.028, -0.010), (-0.028, 0.021, 0.004),
                  (-0.150, 0.021, 0.004), (-0.158, 0.010)])
    panel = part('SidePanel', slab(pl, -HW_U - 0.0026, -HW_U + 0.0006), 'Graphite', wn=False)
    cut(panel, slab(fillet2([(-0.140, -0.012, 0.002), (-0.055, -0.012, 0.002), (-0.055, -0.006, 0.002),
                             (-0.140, -0.006, 0.002)]), -HW_U - 0.01, -HW_U - 0.0016))
    finish(panel, 0.0010, 2, 35)
    marking(panel, '07', (-HW_U - 0.0026, -0.090, 0.0085), (-1, 0, 0), 0.010)
    pts = [(-0.150, -0.0185), (-0.150, 0.0145), (-0.096, -0.0185), (-0.096, 0.0145), (-0.040, -0.0185), (-0.040, 0.0145)]
    part('SidePanel_Screws', merge_vf(*[screw_vf((-HW_U - 0.0026, y, z), (-1, 0, 0), 0.0034, 0.0014) for y, z in pts]),
         'Steel')
    # barrel nut (visible in the gap between handguard and receiver)
    part('BarrelNut', ring_y([(0.0158, -0.189), (0.0222, -0.189), (0.0222, -0.1695), (0.0158, -0.1695)], 12),
         'DarkSteel', bev=(0.0007, 1, 35))
    return up


def lower():
    prof = fillet2([(-0.135, ZS - 0.0015, 0.002), (-0.135, -0.056, 0.02), (-0.1385, -0.094), (-0.050, -0.094),
                    (-0.050, -0.0745, 0.006), (0.120, -0.0745, 0.012), (0.170, -0.054, 0.012),
                    (0.170, ZS - 0.0015, 0.002)])
    lo = part('Receiver_Lower', slab(prof, -HW_L, HW_L), 'PaintOliveGray', wn=False)
    fl = fillet2([(-0.1405, -0.108, 0.003), (-0.0455, -0.108, 0.003), (-0.0455, -0.098), (-0.050, -0.090),
                  (-0.135, -0.090), (-0.1405, -0.098)])
    cut(lo, slab(fl, -HW_L - 0.0035, HW_L + 0.0035), 'UNION')          # flared magwell lip
    cuts = [prism([V((x, y, -0.115)) for x, y in fillet2([(0.0162, -0.1288, 0.009), (0.0162, -0.0552, 0.004),
                                                          (-0.0162, -0.0552, 0.004), (-0.0162, -0.1288, 0.009)])],
                  (0, 0, 0.080)),                                       # magazine cavity
            box_vf((0, -0.003, -0.074), (0.012, 0.040, 0.030))]         # trigger slot
    for sg in (1, -1):                                                  # recessed magwell side panels
        cuts.append(slab(fillet2([(-0.128, -0.087, 0.004), (-0.063, -0.087, 0.004), (-0.063, -0.045, 0.004),
                                  (-0.128, -0.045, 0.004)]), sg * (HW_L - 0.0012), sg * 0.06))
    cut(lo, cuts)
    finish(lo, 0.0015, 2, 35)
    RW = HW_L - 0.0012
    marking(lo, 'R-12', (RW, -0.0955, -0.066), (1, 0, 0), 0.0135)
    marking(lo, 'HAVEN ARMORY', (-RW, -0.0955, -0.058), (-1, 0, 0), 0.0050)
    marking(lo, 'SI-0472', (-RW, -0.0955, -0.0745), (-1, 0, 0), 0.0068)
    # selector markings (left): S forward, 1 up, A rear around the selector pivot
    for txt, a in (('S', 0), ('1', 90), ('A', 180)):
        marking(lo, txt, (HW_L, SEL[0] - 0.0135 * cos(radians(a)), SEL[1] + 0.0135 * sin(radians(a))), (1, 0, 0), 0.0050)
    heads = []
    for (y, z, r) in ((-0.123, -0.042, 0.0034), (0.156, -0.042, 0.0034), (-0.004, -0.054, 0.0026),
                      (0.028, -0.054, 0.0026)):
        for sg in (1, -1):
            heads.append(pinhead_vf((sg * HW_L, y, z), (sg, 0, 0), r, 0.0010))
    part('Receiver_Pins', merge_vf(*heads), 'Steel')
    # magazine release (right): button inside a raised fence ring
    part('MagRelease_Fence', lathe_axis([(0.0062, 0), (0.0078, 0), (0.0078, 0.0028), (0.0062, 0.0028), (0.0062, 0)], 16,
                                        (-HW_L, -0.040, -0.0605), '-X', False, False), 'PaintOliveGray')
    part('MagRelease', lathe_axis([(0, -0.001), (0.0052, -0.001), (0.0052, 0.0032), (0.0044, 0.0042), (0, 0.0042)], 16,
                                  (-HW_L, -0.040, -0.0605), '-X'), 'Blackened')
    # bolt catch paddle (left, rear of the magwell)
    bc = merge_vf(slab(fillet2([(-0.058, -0.050, 0.002), (-0.040, -0.050, 0.002), (-0.040, -0.040, 0.002),
                                (-0.058, -0.040, 0.002)]), HW_L - 0.001, HW_L + 0.0032),
                  slab(fillet2([(-0.052, -0.070, 0.003), (-0.044, -0.070, 0.003), (-0.044, -0.046), (-0.052, -0.046)]),
                       HW_L - 0.001, HW_L + 0.0045))
    part('BoltCatch', bc, 'Blackened', bev=(0.0008, 2, 35))
    return lo


def trigger_group():
    part('TriggerGuard', P.guard_vf([(-0.052, -0.082), (-0.046, -0.110, 0.010), (0.044, -0.112, 0.012),
                                     (0.060, -0.084)], 0.0078, 0.0034), 'PaintOliveGray')
    trig = part('Trigger', P.trigger_vf((-0.002, -0.058), (-0.010, -0.099), 0.007), 'Steel')
    group(trig, (0, -0.003, -0.054), 'rotate', 'X', 14, 'Trigger',
          'trigger blade: pivots on the trigger pin, pulled 14 deg rearward to fire')
    return trig


def grip():
    top, bot = (0.080, -0.066), (0.123, -0.207)
    fr = P.Frame(top, bot)
    w0, w1 = 0.0175, 0.0198
    g = part('Grip', P.grip_vf(top, bot, w0, w1, -0.031, 0.030, 0.035, fingers=3, finger_depth=0.0048,
                               finger_range=(0.20, 0.88), flare=0.0025), 'PolyBlack', wn=False)
    cuts = []
    for k in range(8):
        f = 0.25 + 0.074 * k
        w = w0 + (w1 - w0) * f
        for sg in (1, -1):
            cuts.append(fr.box(sg * (w - 0.0011), sg * (w + 0.02), fr.L * f - 0.0009, fr.L * f + 0.0009, -0.022, 0.026))
    finish(g, 0.0012, 2, 40)
    detail(g, cuts)
    # bottom storage cap
    capl = [[V((p[0], s_, p[1])) for p in P.grip_section(0.0170, -0.026, 0.030)] for s_ in (-0.003, 0.0022)]
    part('Grip_Cap', fr.vf(xform_vf(loft(capl), Matrix.Translation((0, fr.L, 0.002)))), 'Blackened', bev=(0.0008, 2, 35))
    return g


def magazine():
    path = P.arc_down_path(MAG_TOP, -0.100, 0.36, 24.0, 4, 26)
    m = part('Magazine', P.mag_vf(path, 0.0145, 0.0345, 0.0345, ribs=[(0.70, 0.73), (0.79, 0.82)],
                                  rib_h=0.0018), 'PolyTan', wn=False)
    finish(m, 0.0012, 2, 35)
    part('Magazine_Baseplate', P.baseplate_vf(path, 0.0145, 0.0345, 0.0345, 0.010, 0.0050, 0.0045), 'PolyBlack', m,
         bev=(0.0016, 2, 35))
    th = asin((0.222 - 0.100) / 0.36)
    marking(m, '30', (0.0145, -0.4515 + 0.36 * cos(th), -0.222), (1, 0, 0), 0.0105, up=(0, sin(th), cos(th)))
    group(m, (0, MAG_TOP[0], MAG_TOP[1]), 'translate', V((0, -0.12, -1)).normalized(), 0.20, 'Reload',
          'magazine: drops out of the magwell along its insertion line (0.20 m) for a reload; the reverse inserts a '
          'fresh one', stage=(0.0, 0.45))
    return m


def bolt_and_handle():
    # bolt carrier (visible through the ejection port): steel, cam-pin recess, dark bolt head
    head = lathe_axis([(0, 0), (0.0085, 0), (0.0085, 0.0105), (0, 0.0105)], 16, (0, -0.044, 0.004), 'Y')
    b = part('Bolt', union_vf(loft_y([(y, sec(0.0150, 0.0150, -0.0135, 0.0215, 0.003, 0.006, 3)) for y in (-0.034, 0.112)]),
                              head), 'Steel', wn=False)
    cut(b, [slab(fillet2([(0.000, -0.003, 0.002), (0.040, -0.003, 0.002), (0.040, 0.009, 0.002), (0.000, 0.009, 0.002)]),
                 -0.03, -0.0128),
            box_vf((-0.016, 0.050, 0.004), (0.010, 0.012, 0.0045))])
    finish(b, 0.0010, 2, 35)
    part('Bolt_Extractor', box_vf((-0.0086, -0.039, 0.004), (0.0026, 0.010, 0.006)), 'DarkSteel', b, bev=(0.0006, 1, 35))
    group(b, (0, -0.034, 0.004), 'translate', 'Y', 0.085, 'Cycle',
          'bolt carrier: recoils 0.085 m rearward and returns once per shot (ejects through the port)')
    # charging handle (left side, non-reciprocating): slider in the channel + folding knob
    sl = slab(fillet2([(-0.140, 0.0058, 0.0025), (-0.104, 0.0058, 0.0025), (-0.104, 0.0167, 0.0025),
                       (-0.140, 0.0167, 0.0025)]), 0.024, HW_U - 0.0015)
    arm = slab(fillet2([(-0.137, 0.006, 0.002), (-0.111, 0.006, 0.002), (-0.116, 0.017, 0.002),
                        (-0.135, 0.017, 0.002)]), HW_U - 0.002, HW_U + 0.014)
    ch = part('ChargingHandle', merge_vf(sl, arm), 'Blackened', bev=(0.0009, 2, 35))
    kc = (HW_U + 0.012, -0.124, 0.0115)
    kn = part('ChargingHandle_Knob', lathe_axis([(0, 0), (0.0068, 0), (0.0068, 0.016), (0.0058, 0.0185), (0, 0.0185)],
                                                16, kc, 'X'), 'PolyBlack', ch, wn=False)
    cut(kn, P.knurl_ring_cutters((kc[0] + 0.0085, kc[1], kc[2]), 'X', 0.0068, 0.012, 18, 0.0007, 0.0012))
    weighted(kn)
    group(ch, (HW_U, -0.124, 0.0115), 'translate', 'Y', 0.110, 'Charge',
          'charging handle: pulled 0.11 m rearward to chamber the first round, then released')
    # dust cover (right): closed over the port at rest; DustCover = 1 swings it open (hanging below the port)
    hp = V((-HW_U - 0.0018, 0.022, -0.0165))
    plate = slab(fillet2([(-0.020, -0.0160, 0.002), (0.064, -0.0160, 0.002), (0.064, 0.0205, 0.003),
                          (-0.020, 0.0205, 0.003)]), -HW_U - 0.0028, -HW_U - 0.0008)
    rib = slab(fillet2([(-0.012, 0.0045, 0.0015), (0.056, 0.0045, 0.0015), (0.056, 0.0085, 0.0015),
                        (-0.012, 0.0085, 0.0015)]), -HW_U - 0.0046, -HW_U - 0.0024)
    d = part('DustCover', plate, 'PaintOliveGray', bev=(0.0007, 2, 35))
    part('DustCover_Rib', rib, 'PaintOliveGray', d, bev=(0.0005, 1, 35))
    part('DustCover_HingeRod', cyl_vf((hp.x, 0.022, hp.z), 0.0019, 0.094, 'Y', 10), 'Steel')
    group(d, hp, 'rotate', 'Y', -150, 'DustCover',
          'ejection-port dust cover: closed at rest; swings 150 deg down to hang open below the port (first shot)')
    return b, ch, d


def barrel_and_muzzle():
    prof = [(0, -0.680), (0.0055, -0.680), (0.0055, -0.703), (0.0128, -0.703), (0.0128, -0.690), (0.0136, -0.688),
            (0.0136, -0.600), (0.0150, -0.540), (0.0160, -0.440), (0.0160, -0.166), (0, -0.166)]
    part('Barrel', lathe_axis(prof, 28, (0, 0, 0), 'Y'), 'DarkSteel')
    solid, cuts = P.comp_vf(-0.800, 0.097, 0.0205, 0.0062, 3, 0.0056)
    mz = part('Muzzle_Compensator', solid, 'Blackened', wn=False)
    finish(mz, 0.0009, 2, 35)
    detail(mz, cuts)
    part('Muzzle_JamNut', ring_y([(0.0128, -0.703), (0.0172, -0.703), (0.0172, -0.697), (0.0128, -0.697)], 6),
         'Steel', bev=(0.0006, 1, 35))
    gb = merge_vf(lathe_axis([(0, 0), (0.0200, 0), (0.0200, 0.026), (0, 0.026)], 20, (0, -0.505, 0.0), 'Y'),
                  box_vf((0, -0.492, 0.019), (0.016, 0.026, 0.012)))
    part('GasBlock', gb, 'DarkSteel', bev=(0.0010, 2, 35))
    part('GasTube', tube_vf([V((0, -0.480, 0.021)), V((0, -0.176, 0.021))], 0.0032, 10), 'Steel')


HG_OUT = [(0.024, -0.046, 0.008), (0.0385, -0.032, 0.004), (0.0385, 0.010, 0.004), (0.029, UTOP, 0.003)]
HG_IN = [(0.0205, -0.0425, 0.006), (0.0350, -0.030, 0.003), (0.0350, 0.008, 0.003), (0.0255, UTOP - 0.0045, 0.002)]


def _sym(half):
    """mirror a list of (x, z, r) corners on the +X side into a closed CCW section."""
    right = [(x, z, r) for x, z, r in half]
    left = [(-x, z, r) for x, z, r in reversed(half)]
    return fillet2(right + left, 3)


def handguard():
    Y0, Y1 = -0.520, -0.172

    def scaled(half, k):
        return _sym([(x * k, UTOP + (z - UTOP) * k, r) for x, z, r in half])
    ys = [Y0, Y0 + 0.004, Y0 + 0.012, Y1]
    ks = [0.94, 0.97, 1.0, 1.0]
    loops = [[V((p[0], y, p[1])) for p in scaled(HG_OUT, k)] for y, k in zip(ys, ks)]
    loops += [[V((p[0], y, p[1])) for p in scaled(HG_IN, k)] for y, k in reversed(list(zip(ys, ks)))]
    hg = part('Handguard', loft(loops + [loops[0]], False, False), 'Graphite', wn=False)
    cuts = []
    for sg in (1, -1):        # recessed side panels with through vent slots
        cuts.append(slab(fillet2([(-0.492, -0.028, 0.006), (-0.205, -0.028, 0.006), (-0.205, 0.006, 0.006),
                                  (-0.492, 0.006, 0.006)]), sg * 0.0373, sg * 0.06))
        for k in range(5):
            cuts.append(slab(stadium2(-0.462 + k * 0.058, -0.011, 0.040, 0.0105), sg * 0.02, sg * 0.06))
    for k in range(4):        # bottom slots
        cuts.append(plate_xy(stadium2(0, -0.450 + k * 0.070, 0.045, 0.012, pi / 2), -0.08, -0.030))
    finish(hg, 0.0014, 2, 35)
    detail(hg, cuts)
    rail_part('Handguard_Rail', -0.515, -0.200, RAIL_Z)
    # rail screws on the upper facets + barrel-nut clamp screws at the rear
    pts = []
    fn = V((0.034, 0, 0.0095)).normalized()
    for y in (-0.470, -0.360, -0.250):
        for sg in (1, -1):
            pts.append(screw_vf((sg * 0.0329, y, 0.030), (sg * fn.x, 0, fn.z), 0.0030, 0.0012))
    for sg in (1, -1):
        for z in (-0.024, -0.010):
            pts.append(screw_vf((sg * 0.0385, -0.188, z), (sg, 0, 0), 0.0032, 0.0013))
    part('Handguard_Screws', merge_vf(*pts), 'Steel')
    cup, loop = P.qd_loop((0.0383, -0.503, -0.012), (1, 0, 0))
    part('Sling_Front_Socket', cup, 'Blackened')
    part('Sling_Front_Loop', loop, 'Steel')
    return hg


def upper_rail():
    return rail_part('Receiver_Rail', -0.168, 0.203, RAIL_Z)


def optic_and_sights():
    o, zc, r = P.red_dot(-0.020, RAIL_Z)
    part('Optic_Body', o['body'], 'Blackened', bev=(0.0010, 2, 35))
    part('Optic_Mount', o['base'], 'Graphite', bev=(0.0010, 2, 35))
    part('Optic_TurretBosses', o['boss'], 'Blackened', bev=(0.0008, 2, 35))
    part('Optic_Turrets', o['turrets'], 'DarkSteel')
    part('Optic_Lenses', o['lens'], 'Lens')
    part('Optic_ClampBolt', o['bolt'], 'Steel')
    # flip-up iron sights (deployed at rest); IronSights = 1 folds them flat
    b, leaf, hole, ring, hinge, hp = P.flip_rear_sight(0.168, 0.198, RAIL_Z)
    part('RearSight_Base', b, 'Blackened', bev=(0.0008, 2, 35))
    lf = part('RearSight_Leaf', leaf, 'Blackened', wn=False)
    cut(lf, hole)
    finish(lf, 0.0006, 2, 35)
    part('RearSight_Ring', ring, 'Blackened', lf)
    part('RearSight_Hinge', hinge, 'Steel')
    group(lf, hp, 'rotate', 'X', 90, 'IronSights', 'rear aperture leaf: folds 90 deg forward, flat on the rail')
    b2, fr, post, hinge2, hp2 = P.flip_front_sight(-0.508, -0.478, RAIL_Z)
    part('FrontSight_Base', b2, 'Blackened', bev=(0.0008, 2, 35))
    fs = part('FrontSight_Ears', fr, 'Blackened', bev=(0.0007, 2, 35))
    part('FrontSight_Post', post, 'Steel', fs)
    part('FrontSight_Hinge', hinge2, 'Steel')
    group(fs, hp2, 'rotate', 'X', -90, 'IronSights', 'front post: folds 90 deg rearward, flat on the rail')
    return zc


def stock():
    cn = part('Stock_CastleNut', ring_y([(0.0176, 0.205), (0.0245, 0.205), (0.0245, 0.217), (0.0176, 0.217)], 24,
                                        cz=-0.004), 'Steel', wn=False)
    cut(cn, [box_vf((cos(a) * 0.025, 0.211, -0.004 + sin(a) * 0.025), (0.006, 0.014, 0.006))
             for a in (pi / 4, 3 * pi / 4, 5 * pi / 4, 7 * pi / 4)])
    finish(cn, 0.0006, 1, 35)
    tube = lathe_axis([(0, 0.214), (0.0175, 0.214), (0.0175, 0.401), (0.0160, 0.405), (0, 0.405)], 24, (0, 0, -0.004), 'Y')
    key = box_vf((0, 0.300, -0.0235), (0.007, 0.170, 0.006))
    part('Stock_BufferTube', merge_vf(tube, key), 'DarkSteel')
    zt = Spline([(0.300, 0.024), (0.380, 0.034), (0.468, 0.050)])
    zb = Spline([(0.300, -0.028), (0.360, -0.050), (0.468, -0.114)])
    hw = Spline([(0.300, 0.0225), (0.468, 0.0285)])
    secs = [(y, sec(hw(y), hw(y) * 0.80, zb(y), zt(y), 0.007, 0.012, 3)) for y in cosspace(0.300, 0.468, 20, (True, True))]
    st = part('Stock', loft_y(secs), 'PolyBlack', wn=False)
    win = fillet2([(0.352, -0.031, 0.006), (0.442, -0.031, 0.006), (0.442, zb(0.442) + 0.013, 0.008),
                   (0.362, zb(0.362) + 0.011, 0.006)])
    cut(st, [slab(win, -0.05, 0.05), cyl_vf((0, 0.37, -0.004), 0.0177, 0.2, 'Y', 24),
             box_vf((0, 0.33, -0.0235), (0.0075, 0.240, 0.0065))])
    finish(st, 0.0016, 2, 40)
    rib_v = []
    for k in range(5):        # raised cheek ribs across the sloping top
        y = 0.352 + k * 0.022
        rib_v.append(loft_y([(y - 0.0024, sec(hw(y) * 0.62, hw(y) * 0.50, zt(y) - 0.004, zt(y) + 0.0022, 0.001, 0.0016, 2)),
                             (y + 0.0024, sec(hw(y) * 0.62, hw(y) * 0.50, zt(y + 0.0024) - 0.004, zt(y + 0.0024) + 0.0022,
                                              0.001, 0.0016, 2))]))
    part('Stock_CheekRibs', merge_vf(*rib_v), 'PolyBlack', st, bev=(0.0006, 1, 35))
    ys = [0.306 + 0.044 * k / 6 for k in range(7)]
    lat = [(y, zb(y) + 0.0015) for y in ys] + [(y, zb(y) - 0.0045) for y in reversed(ys)]
    part('Stock_Latch', slab(lat, -0.0055, 0.0055), 'Blackened', st, bev=(0.0007, 2, 35))
    cup, loop = P.qd_loop((hw(0.454) - 0.0003, 0.454, -0.092), (1, 0, 0))
    part('Sling_Rear_Socket', cup, 'Blackened', st)
    part('Sling_Rear_Loop', loop, 'Steel', st)
    po = fillet2([(0.0335, -0.123, 0.014), (0.0335, 0.054, 0.016), (-0.0335, 0.054, 0.016), (-0.0335, -0.123, 0.014)])
    pad = part('Stock_Buttpad', plate_xz(po, 0.466, 0.488), 'Rubber', st, wn=False)
    finish(pad, 0.0018, 2, 35)
    detail(pad, [box_vf((0, 0.4895, -0.110 + k * 0.0128), (0.09, 0.006, 0.0042)) for k in range(13)])
    group(st, (0, 0.300, -0.004), 'translate', 'Y', -0.055, 'StockLength',
          'adjustable stock: slides 0.055 m forward along the buffer tube (collapsed); 0 = extended')
    return st


def selector():
    sel = merge_vf(lathe_axis([(0, 0), (0.0068, 0), (0.0068, 0.0022), (0, 0.0022)], 16, (HW_L, SEL[0], SEL[1]), 'X'),
                   slab(fillet2([(SEL[0], SEL[1] - 0.0032), (SEL[0] - 0.0085, SEL[1] - 0.0024, 0.0022),
                                 (SEL[0] - 0.0085, SEL[1] + 0.0024, 0.0022), (SEL[0], SEL[1] + 0.0032)]),
                        HW_L + 0.0010, HW_L + 0.0042))
    s = part('Selector', sel, 'Blackened', bev=(0.0006, 2, 35))
    group(s, (HW_L, SEL[0], SEL[1]), 'control', 'X', None, None,
          'fire selector lever: SAFE = 0 deg (lever forward), SEMI = -90 (up), AUTO = -180 (rearward)', min=-180, max=0,
          speed=600, detents={'SAFE': 0, 'SEMI': -90, 'AUTO': -180}, input='fire_mode')


def build():
    r = begin('R12')
    upper()
    lower()
    upper_rail()
    handguard()
    barrel_and_muzzle()
    trigger_group()
    grip()
    magazine()
    bolt_and_handle()
    zc = optic_and_sights()
    stock()
    selector()
    # ---------------------------------------------------------------- rig data
    point('Muzzle', (0, -0.800, 0), 'muzzle', (0, -1, 0), note='bullet origin + muzzle flash (compensator vents sideways)')
    point('Ejection', (-HW_U - 0.004, 0.022, 0.003), 'ejection', (-0.82, 0.30, 0.48),
          note='spent cases leave the ejection port here (right side, up and slightly back)')
    point('Grip_Right', (0, 0.100, -0.135), 'grip_right', note='firing hand on the pistol grip')
    point('Grip_Left', (0, -0.360, -0.040), 'grip_left', note='support hand under the handguard')
    point('Aim', (0, 0.190, zc), 'aim_eye', (0, -1, 0), note='eye position for aiming down the red-dot (sight axis)')
    point('MagWell', (0, MAG_TOP[0], -0.100), 'magwell', (0, -0.12, -1))
    point('Sling_Front', (0.0575, -0.503, -0.012), 'sling')
    point('Sling_Rear', (0.0475, 0.454, -0.092), 'sling')
    rig.model('RoadrunnerR12', 'Roadrunner R-12', 'weapon', WEAPONS['R12'][4],
              origin='on the bore axis directly above the trigger (all five weapons share this datum)')
    rig.channel('Trigger', 'trigger pull (0 = rest, 1 = pulled)', 0.06)
    rig.channel('Cycle', 'bolt cycle per shot: play 0 -> 1 -> 0 once per round at the fire rate', 0.05)
    rig.channel('Charge', 'charging handle pulled back (chambering)', 0.35,
                ['the bolt follows the handle while charging: drive Cycle together with Charge'])
    rig.channel('Reload', 'magazine out (1) / in (0)', 0.9)
    rig.channel('DustCover', 'dust cover open (1) / closed (0); spring-loaded: set it to 1 on the first shot or '
                'when charging, close it only on request', 0.12)
    rig.channel('IronSights', 'iron sights folded (1) / deployed (0)', 0.3)
    rig.channel('StockLength', 'stock collapsed (1) / extended (0)', 0.3)
    rig.pose('fire', {'Trigger': 1, 'Cycle': 1, 'DustCover': 1}, description='trigger pulled, bolt fully back, port open',
             ground=False)
    rig.pose('reload', {'Reload': 1, 'Charge': 1, 'Cycle': 1, 'DustCover': 1},
             description='magazine out, handle and bolt back', ground=False)
    rig.pose('stowed', {'IronSights': 1, 'StockLength': 1}, {'R12_Selector': 0},
             description='carried: sights folded, stock collapsed, SAFE', ground=False)
    rig.pose('auto', {}, {'R12_Selector': -180}, description='selector on AUTO', ground=False)
    rig.system('Weapon', kind='carbine', caliber='5.5x42 mm (fictional)', magazine=30,
               fire_modes=['SAFE', 'SEMI', 'AUTO'], rpm=720, muzzle_velocity_mps=880,
               effective_range_studs=round(400 * S), reload_s=2.4, damage_hint='medium',
               recoil_hint='moderate, compensated (low muzzle rise)', aim='1x red-dot; iron sights co-witness below it',
               ammo_item='Ammo_5.5x42')
    rig.note('Weapon origin = bore axis above the trigger; the muzzle points -Z in Roblox (LookVector).')
    rig.note('Hide / eject the magazine by its group (R12_Magazine with its baseplate and marking).')
    return r
