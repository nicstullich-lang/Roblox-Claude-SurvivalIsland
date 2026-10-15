"""Trailmark .308 - bolt-action marksman rifle (collection TRAILMARK_308, export Trailmark308.fbx).

Target 5.1 x 1.55 x 0.6 studs (L x H x W) = 1.428 x 0.434 x 0.168 m. The longest, slimmest weapon of the pack.
Layout (y, metres; bore z = 0; origin above the trigger):
  muzzle brake -0.950..-0.885 | straight slender barrel to -0.240 | slate receiver -0.228..+0.065 (bolt shroud to +0.10)
  olive thumbhole precision stock -0.640..+0.456 (forend, grip, wrist, butt, lower strut), raised cheek riser on posts,
  two buttpad spacers + rubber pad to +0.478 | medium scope (rings at -0.150 / +0.040, axis z = 0.078)
  compact 5-round box magazine | folding bipod under the forend front (legs folded forward under the barrel).
Bolt: TM308_Bolt slides back 0.11 m (stage 0.4-1 of the Bolt channel); its child TM308_BoltHandle lifts 60 deg first.
"""
from .lib import *
from . import parts as P

HW = 0.026
ZB, ZT = -0.026, 0.028
RY0, RY1 = -0.228, 0.065
HY = 0.054                    # bolt-handle root (y)
ZS = 0.090                    # scope axis height (tall rings clear the bolt handle and the big objective)
TUBE = 0.0205
MAG = (-0.0875, 0.0195, 0.038)  # magazine centre y, half width, half depth


def receiver():
    sec_ = _sym([(HW, ZB, 0.004), (HW, 0.013, 0.003), (0.016, ZT, 0.003)])
    rc = part('Receiver', plate_xz(sec_, RY0, RY1), 'PaintSlate', wn=False)
    cuts = []
    # ejection port (right) showing the bolt
    cuts.append(slab(fillet2([(-0.112, -0.007, 0.004), (0.018, -0.007, 0.004), (0.018, 0.021, 0.004),
                              (-0.112, 0.021, 0.004)]), -0.06, -0.008))
    # bolt-handle notch at the right rear: wedge between -12 and +72 deg around the bore
    a0, a1 = radians(-12), radians(72)
    wedge = [(0.0, 0.0), (-cos(a0) * 0.08, sin(a0) * 0.08), (-0.08 * 0.75, 0.08 * 0.45), (-cos(a1) * 0.08, sin(a1) * 0.08)]
    cuts.append(prism([V((x, HY - 0.0085, z)) for x, z in wedge], (0, 0.03, 0)))
    # side panels (recessed seams) + the bore
    for sg in (1, -1):
        cuts.append(slab(fillet2([(-0.212, -0.019, 0.003), (-0.128, -0.019, 0.003), (-0.128, 0.008, 0.003),
                                  (-0.212, 0.008, 0.003)]), sg * (HW - 0.0012), sg * 0.06))
    cuts.append(slab(fillet2([(0.030, -0.019, 0.003), (0.046, -0.019, 0.003), (0.046, 0.008, 0.003), (0.030, 0.008, 0.003)]),
                     HW - 0.0012, 0.06))
    cuts.append(cyl_vf((0, RY0, 0), 0.0172, 0.03, 'Y', 24))
    cut(rc, cuts)
    finish(rc, 0.0014, 2, 35)
    marking(rc, 'TRAILMARK  .308', (HW - 0.0012, -0.170, -0.0055), (1, 0, 0), 0.0062)
    marking(rc, 'HVN 2291', (-HW + 0.0012, -0.170, -0.0055), (-1, 0, 0), 0.0060)
    # recoil lug + barrel nut at the front
    part('RecoilLug', plate_xz(_sym([(HW + 0.0018, ZB - 0.003, 0.003), (HW + 0.0018, 0.012, 0.003), (0.017, ZT, 0.003)]),
                               RY0 - 0.006, RY0 + 0.0005), 'PaintSlate', bev=(0.0007, 1, 35))
    part('BarrelNut', ring_y([(0.0160, RY0 - 0.020), (0.0205, RY0 - 0.020), (0.0205, RY0 - 0.006), (0.0160, RY0 - 0.006)],
                             12), 'DarkSteel', bev=(0.0006, 1, 35))
    # integral scope rail on top
    rail_part('Rail', -0.214, 0.042, ZT - 0.0006)
    # hardware: side-panel screws (both sides), bolt release (left), safety (right)
    scr = []
    for sg in (1, -1):
        for y in (-0.205, -0.135):
            for z in (-0.014, 0.003):
                scr.append(screw_vf((sg * (HW - 0.0012), y, z), (sg, 0, 0), 0.0026, 0.0011))
    for y in (-0.090, -0.030):
        scr.append(screw_vf((HW, y, -0.017), (1, 0, 0), 0.0028, 0.0011))
    part('Receiver_Screws', merge_vf(*scr), 'Steel')
    br = slab(fillet2([(0.031, -0.004, 0.002), (0.050, -0.006, 0.003), (0.050, 0.003, 0.002), (0.031, 0.004, 0.002)]),
              HW - 0.0014, HW + 0.0026)
    part('BoltRelease', br, 'Blackened', bev=(0.0005, 2, 35))
    sf = merge_vf(slab(fillet2([(0.064, -0.023, 0.002), (0.074, -0.023, 0.002), (0.074, -0.015, 0.002), (0.064, -0.015, 0.002)]),
                       -HW - 0.0030, -HW + 0.002),
                  slab(fillet2([(0.066, -0.016, 0.001), (0.072, -0.016, 0.001), (0.071, -0.006, 0.0015), (0.067, -0.006, 0.0015)]),
                       -HW - 0.0026, -HW - 0.0004))
    s = part('Safety', sf, 'Blackened', bev=(0.0005, 2, 35))
    group(s, (-HW, 0.069, -0.019), 'rotate', 'X', -20, 'Safety', 'safety lever: rocks 20 deg forward to FIRE (rest = SAFE)')
    return rc


def _sym(half, seg=3):
    return fillet2([(x, z, r) for x, z, r in half] + [(-x, z, r) for x, z, r in reversed(half)], seg)


def bolt():
    body = lathe_axis([(0, -0.128), (0.0110, -0.128), (0.0125, -0.124), (0.0125, RY1 - 0.002), (0, RY1 - 0.002)], 24,
                      (0, 0, 0), 'Y')
    lugs = merge_vf(box_vf((0, -0.122, 0.0125), (0.010, 0.012, 0.006)), box_vf((0, -0.122, -0.0125), (0.010, 0.012, 0.006)))
    b = part('Bolt', union_vf(body, lugs), 'Steel', wn=False)
    finish(b, 0.0007, 2, 35)
    detail(b, [box_vf((cos(a) * 0.0125, -0.050, sin(a) * 0.0125), (0.0032, 0.090, 0.0032)) for a in
               (pi * 0.85, pi * 1.0, pi * 1.15)])   # flutes, facing the ejection port
    shroud = lathe_axis([(0, RY1 - 0.003), (0.0142, RY1 - 0.003), (0.0150, RY1 + 0.006), (0.0150, RY1 + 0.024),
                         (0.0118, RY1 + 0.032), (0.0060, RY1 + 0.034), (0.0060, RY1 + 0.039), (0, RY1 + 0.039)], 20,
                        (0, 0, 0), 'Y')
    part('Bolt_Shroud', shroud, 'Blackened', b, bev=(0.0006, 1, 35))
    part('Bolt_CockingIndicator', cyl_vf((0, RY1 + 0.0375, 0.0), 0.0032, 0.004, 'Y', 12), 'MarkRed', b)
    # handle: root + swept bar bending down and back + oversized tactical knob
    path = [V((-0.010, HY, 0.0)), V((-0.030, HY + 0.001, -0.001)), V((-0.046, HY + 0.006, -0.012)),
            V((-0.058, HY + 0.012, -0.026))]
    bar = sweep_vf(path, circle2(0.0047, 12), scale=[1.15, 1.0, 0.95, 0.9])
    root = cyl_vf((-0.010, HY, 0.0), 0.0072, 0.008, 'X', 16)
    h = part('BoltHandle', merge_vf(bar, root), 'Blackened', b)
    kd = (path[-1] - path[-2]).normalized()
    knob = lathe_axis([(0.0040, 0), (0.0095, 0.004), (0.0120, 0.013), (0.0112, 0.022), (0.0060, 0.027), (0, 0.0275)], 18,
                      path[-1] - kd * 0.002, kd, cap0=True)
    kn = part('BoltHandle_Knob', knob, 'PolyBlack', h, wn=False)
    cut(kn, [orient(box_vf((0.0122 * cos(a), 0.0122 * sin(a), 0.014), (0.0016, 0.0016, 0.014)), path[-1] - kd * 0.002, kd)
             for a in [2 * pi * k / 14 for k in range(14)]])
    weighted(kn)
    group(h, (0, HY, 0), 'rotate', 'Y', 60, 'Bolt', 'bolt handle: lifts 60 deg (unlocks), first stage of the bolt cycle',
          stage=(0.0, 0.4))
    group(b, (0, -0.128, 0), 'translate', 'Y', 0.100, 'Bolt',
          'bolt: slides 0.100 m rearward after the handle is lifted (ejects through the port), then returns',
          stage=(0.4, 1.0))
    return b


def barrel():
    prof = [(0, -0.876), (0.0050, -0.876), (0.0050, -0.888), (0.0118, -0.888), (0.0118, -0.882), (0.0130, -0.880),
            (0.0130, -0.300), (0.0168, -0.262), (0.0168, -0.240), (0, -0.240)]
    part('Barrel', lathe_axis(prof, 28, (0, 0, 0), 'Y'), 'DarkSteel')
    yf, yr, r = -0.950, -0.885, 0.0185
    ring = [(0.0060, yf), (r - 0.003, yf), (r, yf + 0.003), (r, yr - 0.006), (r - 0.0035, yr - 0.002), (r - 0.0035, yr),
            (0.0060, yr)]
    br = part('Muzzle_Brake', orient(lathe_vf([(a, b) for a, b in ring] + [ring[0]], 24, False, False), (0, 0, 0), 'Y'),
              'Blackened', wn=False)
    cuts = [box_vf((0, yc, 0), (0.06, 0.0145, 0.0230)) for yc in (-0.936, -0.912)]
    cuts += [cyl_vf((0, yc, r), 0.0026, 0.02, 'Z', 12) for yc in (-0.944, -0.924, -0.900)]
    finish(br, 0.0008, 2, 35)
    detail(br, cuts)
    part('Muzzle_JamNut', ring_y([(0.0118, -0.886), (0.0158, -0.886), (0.0158, -0.879), (0.0118, -0.879)], 6), 'Steel',
         bev=(0.0005, 1, 35))


# stock outline (y, z, fillet radius) and thumbhole
ST_OUT = [(-0.640, -0.020, 0.012), (-0.236, -0.012, 0.004), (0.066, -0.012, 0.002), (0.073, -0.020, 0.004),
          (0.224, -0.019, 0.020), (0.258, 0.012, 0.022), (0.456, 0.024, 0.006), (0.456, -0.226, 0.012),
          (0.392, -0.236, 0.030), (0.300, -0.222, 0.040), (0.182, -0.280, 0.014), (0.128, -0.282, 0.012),
          (0.080, -0.070, 0.010), (-0.236, -0.064, 0.006), (-0.640, -0.060, 0.014)]
ST_HOLE = [(0.140, -0.064, 0.012), (0.246, -0.058, 0.022), (0.294, -0.190, 0.022), (0.184, -0.244, 0.012)]
ST_PLAN = [(-0.640, 0.021, 0.0), (-0.628, 0.027, 0.006), (-0.250, 0.027, 0.02), (-0.222, 0.0295, 0.02),
           (0.058, 0.0295, 0.02), (0.100, 0.0205, 0.02), (0.232, 0.0205, 0.02), (0.272, 0.025, 0.02), (0.470, 0.025, 0.0)]


def ztop(y):
    return 0.012 + 0.012 * (y - 0.258) / 0.198


def stock():
    plan = fillet2([(x, y, r) for y, x, r in ST_PLAN] + [(-x, y, r) for y, x, r in reversed(ST_PLAN)])
    st = part('Stock', slab(fillet2(ST_OUT), -0.04, 0.04), 'PolyOlive', wn=False)
    cut(st, slab(fillet2(ST_HOLE), -0.05, 0.05))
    cut(st, plate_xy(plan, -0.4, 0.2), 'INTERSECT')
    cuts = [cyl_vf((0, -0.44, 0), 0.0195, 0.42, 'Y', 24),                                  # barrel channel (free float)
            box_between((-HW - 0.0004, -0.2365, ZB - 0.0006), (HW + 0.0004, RY1 + 0.0015, 0.05)),  # action inlet
            box_between((-HW - 0.0022, RY0 - 0.0065, ZB - 0.0036), (HW + 0.0022, RY0 + 0.001, 0.05)),
            box_between((-MAG[1] - 0.0012, MAG[0] - MAG[2] - 0.0012, -0.12), (MAG[1] + 0.0012, MAG[0] + MAG[2] + 0.0012, 0.0)),
            box_between((-0.0062, -0.012, -0.09), (0.0062, 0.026, 0.0))]
    finish(st, 0.0060, 4, 30)                      # big round-overs first (outer shape only) ...
    # ... then the inlets / channels and the texture panels with small edges (a 6 mm bevel on the 14 mm inlet walls
    # folds the surface into itself and breaks every later boolean)
    rec = []
    for sg in (1, -1):
        rec.append(slab(fillet2([(0.094, -0.094, 0.006), (0.140, -0.094, 0.006), (0.174, -0.240, 0.006),
                                 (0.130, -0.244, 0.006)]), sg * 0.0195, sg * 0.05))
        rec.append(slab(fillet2([(-0.560, -0.051, 0.006), (-0.300, -0.052, 0.006), (-0.300, -0.031, 0.006),
                                 (-0.560, -0.030, 0.006)]), sg * 0.0262, sg * 0.05))
    cut(st, cuts + rec)
    weighted(st)
    marking(st, 'HAVEN', (0.0249, 0.360, -0.130), (1, 0, 0), 0.0105)
    # cheek riser: follows the butt profile, raised on two posts, locking knob on the right
    zt0, zt1 = ztop(0.264), ztop(0.446)
    ro = fillet2([(0.264, zt0 + 0.005), (0.446, zt1 + 0.005), (0.446, zt1 + 0.037, 0.008), (0.328, ztop(0.328) + 0.037, 0.04),
                  (0.274, zt0 + 0.020, 0.012)])
    ck = part('CheekRiser', slab(ro, -0.019, 0.019), 'PolyOlive', wn=False)
    finish(ck, 0.0055, 4, 30)
    posts = [cyl_vf((0, y, ztop(y) + 0.004), 0.0045, 0.022, 'Z', 14) for y in (0.302, 0.404)]
    part('CheekRiser_Posts', merge_vf(*posts), 'Steel', ck)
    part('CheekRiser_Knob', lathe_axis([(0, 0), (0.0090, 0), (0.0090, 0.006), (0.0075, 0.009), (0, 0.009)], 16,
                                       (-0.0245, 0.348, -0.010), '-X'), 'Blackened')
    group(ck, (0, 0.348, ztop(0.348) + 0.005), 'translate', 'Z', 0.014, 'CheekHeight',
          'adjustable cheek riser: rises up to 0.014 m on its two posts (0 = lowest)')
    # length-of-pull spacers + rubber buttpad with a ribbed back
    sp = fillet2([(0.0245, -0.222, 0.009), (0.0245, 0.020, 0.008), (-0.0245, 0.020, 0.008), (-0.0245, -0.222, 0.009)])
    part('Buttpad_Spacers', merge_vf(plate_xz(sp, 0.4535, 0.4595), plate_xz(offset2(ccw(sp), -0.0005), 0.4605, 0.4660)),
         'PolyBlack', bev=(0.0010, 2, 35))
    pd = fillet2([(0.0262, -0.230, 0.012), (0.0262, 0.028, 0.012), (-0.0262, 0.028, 0.012), (-0.0262, -0.230, 0.012)])
    pad = part('Buttpad', plate_xz(pd, 0.4655, 0.4780), 'Rubber', wn=False)
    finish(pad, 0.0020, 2, 35)
    detail(pad, [box_vf((0, 0.4795, -0.214 + k * 0.0135), (0.08, 0.005, 0.0045)) for k in range(18)])
    # QD sling cups (left side: butt + forend)
    for nm_, c in (('Rear', (0.0250, 0.400, -0.175)), ('Front', (0.0270, -0.585, -0.042))):
        cup, loop = P.qd_loop(c, (1, 0, 0))
        part('Sling_%s_Socket' % nm_, cup, 'Blackened')
        part('Sling_%s_Loop' % nm_, loop, 'Steel')
    return st


def bottom_metal():
    y0, y1 = MAG[0] - MAG[2] - 0.010, 0.072
    bm = part('BottomMetal', plate_xy(fillet2([(0.0165, y0, 0.008), (0.0165, y1, 0.008), (-0.0165, y1, 0.008),
                                               (-0.0165, y0, 0.008)]), -0.0705, -0.0632), 'DarkSteel', wn=False)
    cut(bm, box_between((-MAG[1] - 0.0012, MAG[0] - MAG[2] - 0.0012, -0.08), (MAG[1] + 0.0012, MAG[0] + MAG[2] + 0.0012, 0)))
    cut(bm, box_between((-0.0062, -0.012, -0.09), (0.0062, 0.026, 0.0)))
    finish(bm, 0.0010, 2, 35)
    part('TriggerGuard', P.guard_vf([(-0.028, -0.068), (-0.022, -0.100, 0.010), (0.062, -0.102, 0.013),
                                     (0.086, -0.076)], 0.0070, 0.0034), 'DarkSteel')
    part('BottomMetal_Screws', merge_vf(screw_vf((0, y0 + 0.006, -0.0705), (0, 0, -1), 0.0040, 0.0014),
                                        screw_vf((0, y1 - 0.006, -0.0705), (0, 0, -1), 0.0040, 0.0014)), 'Steel')
    rel = merge_vf(slab(fillet2([(-0.0405, -0.0705, 0.001), (-0.0345, -0.0705, 0.001), (-0.0350, -0.084, 0.0015),
                                 (-0.0420, -0.086, 0.0015)]), -0.0055, 0.0055))
    part('MagRelease', rel, 'Blackened', bev=(0.0005, 2, 35))
    part('TriggerHousing', box_between((-0.010, -0.016, -0.058), (0.010, 0.040, ZB + 0.0005)), 'DarkSteel',
         bev=(0.0008, 1, 35))
    trig = part('Trigger', P.trigger_vf((0.012, -0.050), (0.008, -0.090), 0.003, 0.0040, 0.0030), 'Steel')
    group(trig, (0, 0.010, -0.052), 'rotate', 'X', 10, 'Trigger', 'trigger: crisp single-stage, 10 deg rearward')


def magazine():
    y, hw, hd = MAG
    out = fillet2([(hw, y - hd, 0.010), (hw, y + hd, 0.003), (-hw, y + hd, 0.003), (-hw, y - hd, 0.010)])
    m = part('Magazine', plate_xy(out, -0.094, -0.024), 'DarkSteel', wn=False)
    cut(m, [box_between((sg * (hw - 0.0010), y - hd + 0.016, -0.090), (sg * (hw + 0.01), y + hd - 0.010, -0.074))
            for sg in (1, -1)])
    finish(m, 0.0010, 2, 35)
    bpo = fillet2([(hw + 0.002, y - hd - 0.005, 0.011), (hw + 0.002, y + hd + 0.002, 0.004),
                   (-hw - 0.002, y + hd + 0.002, 0.004), (-hw - 0.002, y - hd - 0.005, 0.011)])
    part('Magazine_Baseplate', plate_xy(bpo, -0.1045, -0.0930), 'PolyBlack', m, bev=(0.0016, 2, 35))
    group(m, (0, y, -0.024), 'translate', 'Z', -0.12, 'Reload', 'box magazine: drops straight down 0.12 m',
          stage=(0, 0.45))


def scope():
    k, SY = TUBE / 0.019, 0.025          # radial scale vs the base design, rearward shift of the optic on its rings
    prof = [(0, -0.311), (0.0280, -0.311), (0.0280, -0.326), (0.0322, -0.326), (0.0322, -0.318), (0.0312, -0.315),
            (0.0312, -0.265), (0.0198, -0.230), (0.019, -0.222), (0.019, 0.112), (0.0215, 0.120), (0.0245, 0.148),
            (0.0245, 0.156), (0.0200, 0.156), (0.0200, 0.148), (0, 0.148)]
    prof = [(r * k, y + SY) for r, y in prof]
    sc_ = part('Scope_Body', lathe_axis(prof, 32, (0, 0, ZS), 'Y'), 'Blackened')
    part('Scope_Lenses', merge_vf(cyl_vf((0, -0.3105 + SY, ZS), 0.0281 * k, 0.002, 'Y', 32),
                                  cyl_vf((0, 0.1475 + SY, ZS), 0.0201 * k, 0.002, 'Y', 32)), 'Lens', sc_)
    part('Scope_Eyecup', ring_y([(0.0198 * k, 0.152 + SY), (0.0258 * k, 0.152 + SY), (0.0262 * k, 0.164 + SY),
                                 (0.0222 * k, 0.168 + SY), (0.0198 * k, 0.166 + SY)], 32, cz=ZS), 'Rubber', sc_,
         bev=(0.0006, 1, 35))
    rp = 0.0222 * k
    pr = part('Scope_PowerRing', ring_y([(TUBE - 0.0005, 0.086 + SY), (rp, 0.086 + SY), (rp, 0.110 + SY),
                                         (TUBE - 0.0005, 0.110 + SY)], 32, cz=ZS), 'Blackened', sc_, wn=False)
    cut(pr, [orient(box_vf((rp * cos(a), rp * sin(a), 0.098 + SY), (0.0022, 0.0022, 0.018)), (0, 0, ZS), 'Y')
             for a in [2 * pi * j / 30 for j in range(30)]])
    weighted(pr)
    part('Scope_PowerLever', box_vf((-rp - 0.0026, 0.098 + SY, ZS + 0.004), (0.006, 0.006, 0.010)), 'Blackened', pr,
         bev=(0.0008, 2, 35))
    hs = 0.0235 * k
    sad = plate_xz(fillet2([(hs, ZS - 0.021 * k, 0.008), (hs, ZS + hs, 0.009), (-hs, ZS + hs, 0.009),
                            (-hs, ZS - 0.021 * k, 0.008)]), -0.076 + SY, -0.014 + SY)
    part('Scope_Saddle', sad, 'Blackened', sc_, bev=(0.0016, 2, 35))
    yt = -0.045 + SY

    def turret(name, base, axis, r, h):
        prof_ = [(0, 0), (r * 0.88, 0), (r * 0.88, h * 0.22), (r, h * 0.26), (r, h * 0.92), (r * 0.92, h), (0, h)]
        t = part(name, lathe_axis(prof_, 28, base, axis), 'Blackened', sc_, wn=False)
        ax = axis_v(axis)
        cut(t, [orient(box_vf((r * cos(a), r * sin(a), h * 0.6), (0.0018, 0.0018, h * 0.6)), base, ax)
                for a in [2 * pi * k / 24 for k in range(24)]])
        weighted(t)
        return t
    turret('Scope_TurretElevation', (0, yt, ZS + hs - 0.0005), 'Z', 0.0160, 0.027)
    turret('Scope_TurretWindage', (-hs + 0.0005, yt, ZS), '-X', 0.0136, 0.017)
    turret('Scope_TurretParallax', (hs - 0.0005, yt, ZS), 'X', 0.0170, 0.011)
    part('Scope_ZeroMark', box_vf((0, yt - 0.0161, ZS + hs + 0.020), (0.0016, 0.0012, 0.006)), 'MarkRed', sc_)
    # two rings: ring band + base clamped to the rail + cap screws + cross-bolt nut
    z_rail = ZT - 0.0006
    for nm_, y in (('Front', -0.150), ('Rear', 0.030)):
        ring = ring_y([(TUBE, y - 0.008), (0.0245, y - 0.008), (0.0245, y + 0.008), (TUBE, y + 0.008)], 32, cz=ZS)
        base = P.rail_clamp_vf(y - 0.008, y + 0.008, z_rail, top=ZS - 0.021 - (z_rail + 0.0112))
        neck = plate_xz(fillet2([(0.016, ZS - 0.024), (0.0105, ZS - 0.010, 0.004), (-0.0105, ZS - 0.010, 0.004),
                                 (-0.016, ZS - 0.024)]), y - 0.008, y + 0.008)
        part('ScopeRing_%s' % nm_, merge_vf(ring, base, neck), 'Blackened', bev=(0.0008, 2, 35))
        scr = [screw_vf((sg * 0.0236, y + dy, ZS + 0.0070), (sg * 0.94, 0, 0.34), 0.0024, 0.0010)
               for sg in (1, -1) for dy in (-0.0045, 0.0045)]
        scr.append(orient(lathe_vf([(0, 0), (0.0050, 0), (0.0050, 0.0035), (0, 0.0035)], 6, a0=pi / 6),
                          (-0.0118 * 1.62, y, z_rail + 0.007), '-X'))
        part('ScopeRing_%s_Screws' % nm_, merge_vf(*scr), 'Steel')
    group(pr, (0, 0.098 + SY, ZS), 'control', 'Y', None, None, 'magnification ring: rotates with the zoom (3x at 0, 12x at 120 deg)',
          min=0, max=120, speed=240, input='zoom')


def bipod():
    zr = -0.060 + 0.0006            # forend bottom (rail base, rail hangs down)
    rail_part('Bipod_Rail', -0.613, -0.567, zr, down=True)
    zb = zr - 0.0112
    body = merge_vf(plate_xz(fillet2([(0.019, zb + 0.002, 0.0), (0.019, zb - 0.016, 0.004), (-0.019, zb - 0.016, 0.004),
                                      (-0.019, zb + 0.002, 0.0)]), -0.616, -0.563),
                    plate_xz(fillet2([(0.0155, zb - 0.010, 0.002), (0.0155, zb - 0.030, 0.006), (-0.0155, zb - 0.030, 0.006),
                                      (-0.0155, zb - 0.010, 0.002)]), -0.614, -0.598))
    part('Bipod_Body', body, 'Blackened', bev=(0.0012, 2, 35))
    part('Bipod_ClampKnob', lathe_axis([(0, 0), (0.0080, 0), (0.0090, 0.004), (0.0090, 0.010), (0.0075, 0.012), (0, 0.012)],
                                       16, (-0.019, -0.590, zb - 0.007), '-X'), 'PolyBlack')
    hz, hy = zb - 0.022, -0.606
    part('Bipod_HingePin', merge_vf(cyl_vf((0, hy, hz), 0.0028, 0.062, 'X', 12),
                                    *[cyl_vf((sg * 0.0315, hy, hz), 0.0045, 0.0025, 'X', 12) for sg in (1, -1)]), 'Steel')
    legs = []
    for sg, S_ in ((1, 'L'), (-1, 'R')):
        x = sg * 0.0215
        kn = cyl_vf((x, hy, hz), 0.0080, 0.0095, 'X', 16)
        tube = lathe_axis([(0, 0), (0.0078, 0), (0.0078, 0.122), (0, 0.122)], 16, (x, hy - 0.004, hz), '-Y')
        lg = part('BipodLeg_%s' % S_, merge_vf(kn, tube), 'Blackened', bev=(0.0007, 2, 35))
        col = part('BipodLeg_%s_Collar' % S_, ring_y([(0.0072, hy - 0.130), (0.0098, hy - 0.130), (0.0098, hy - 0.118),
                                                       (0.0072, hy - 0.118)], 16, cx=x, cz=hz), 'Blackened', lg,
                   bev=(0.0006, 1, 35))
        part('BipodLeg_%s_Inner' % S_, lathe_axis([(0, 0), (0.0058, 0), (0.0058, 0.060), (0, 0.060)], 14,
                                                  (x, hy - 0.126, hz), '-Y'), 'Steel', lg)
        part('BipodLeg_%s_Foot' % S_, lathe_axis([(0, 0), (0.0085, 0), (0.0098, 0.006), (0.0090, 0.013), (0.0050, 0.017),
                                                  (0, 0.0175)], 16, (x, hy - 0.184, hz), '-Y'), 'Rubber', lg)
        group(lg, (x, hy, hz), 'rotate', 'X', 90, 'Bipod',
              'bipod leg: folded forward under the barrel; swings 90 deg down to stand the rifle on its bipod')
        legs.append(lg)
    return hz


def build():
    r = begin('TM308')
    receiver()
    bolt()
    barrel()
    stock()
    bottom_metal()
    magazine()
    scope()
    hz = bipod()
    point('Muzzle', (0, -0.950, 0), 'muzzle', (0, -1, 0), note='bullet origin + muzzle flash (2-port brake vents sideways)')
    point('Ejection', (-HW - 0.004, -0.050, 0.008), 'ejection', (-0.85, 0.20, 0.45),
          note='the case is extracted when the bolt is pulled back (Bolt channel), not on firing')
    point('Grip_Right', (0, 0.128, -0.160), 'grip_right', note='firing hand on the thumbhole grip')
    point('Grip_Left', (0, -0.440, -0.050), 'grip_left', note='support hand under the forend')
    point('Aim', (0, 0.262, ZS), 'aim_eye', (0, -1, 0), note='eye position at the scope eye relief (sight axis)')
    point('MagWell', (0, MAG[0], -0.064), 'magwell', (0, 0, -1))
    point('BipodFeet', (0, -0.606, hz - 0.184 - 0.0175), 'bipod_contact',
          note='ground contact of both feet when the Bipod channel = 1 (legs straight down)')
    point('Sling_Front', (0.0460, -0.585, -0.042), 'sling')
    point('Sling_Rear', (0.0440, 0.400, -0.175), 'sling')
    rig.model('Trailmark308', 'Trailmark .308', 'weapon', WEAPONS['TM308'][4],
              origin='on the bore axis directly above the trigger (all five weapons share this datum)')
    rig.channel('Trigger', 'trigger pull', 0.05)
    rig.channel('Bolt', 'bolt cycle: 0 -> 1 lifts the handle then pulls the bolt back (eject); 1 -> 0 chambers', 0.85,
                ['play 0 -> 1 -> 0 after every shot (bolt action)', 'TM308_BoltHandle rotates in stage 0-0.4, '
                 'TM308_Bolt slides in stage 0.4-1'])
    rig.channel('Reload', 'magazine out (1) / in (0)', 0.8)
    rig.channel('Bipod', 'bipod legs deployed (1) / folded (0)', 0.5,
                ['deployed bipod: allow prone / rested fire with much less sway'])
    rig.channel('Safety', 'safety off (1) / on (0)', 0.1)
    rig.channel('CheekHeight', 'cheek riser up (1) / down (0) - cosmetic adjustment', 0.4)
    rig.pose('bolt_open', {'Bolt': 1, 'Safety': 1}, description='bolt handle up and back (ejecting / loading)',
             ground=False)
    rig.pose('bipod', {'Bipod': 1, 'Safety': 1}, {'TM308_Scope_PowerRing': 120},
             description='bipod down, scope at max zoom', ground=False)
    rig.pose('reload', {'Reload': 1, 'Bolt': 1}, description='magazine out, bolt open', ground=False)
    rig.system('Weapon', kind='marksman rifle (bolt action)', caliber='.308 / 7.8x51 mm (fictional)', magazine=5,
               fire_modes=['BOLT'], rpm=50, muzzle_velocity_mps=830, effective_range_studs=round(800 * S),
               reload_s=3.0, damage_hint='high', recoil_hint='strong single kick, brake reduces it',
               aim='3-12x scope (zoom on the power ring); no iron sights', ammo_item='Ammo_308',
               scope={'magnification': [3, 12], 'eye_point': 'TM308_Aim', 'lens_front_y_m': -0.286, 'axis_z_m': ZS})
    rig.note('Weapon origin = bore axis above the trigger; the muzzle points -Z in Roblox (LookVector).')
    rig.note('Bolt animation: TM308_BoltHandle (child of TM308_Bolt) rotates about the bolt axis, then TM308_Bolt slides.')
    return r
