"""Sparrow-9 - 9 mm long-slide service pistol (collection SPARROW9, export Sparrow9.fbx). The smallest weapon.

Target 2.0 x 1.0 x 0.45 studs (L x H x W) = 0.560 x 0.280 x 0.126 m.
Layout (y, metres; bore z = 0; origin above the trigger):
  barrel crown -0.382 | dark-steel slide -0.370..+0.118 (raised sight rib, front + rear serrations, ejection port,
  top window) | polymer frame -0.352..+0.172 (dust cover with a small accessory rail, beavertail)
  open trigger guard -0.104..+0.072 | angled grip with rounded backstrap, flared base, checkered walnut grip panels
  magazine inside the grip, baseplate protruding below.
"""
from .lib import *
from . import parts as P

SY0, SY1 = -0.370, 0.118
HWS = 0.033                # slide half width
HWF = 0.028                # frame half width
HWG = 0.029                # grip half width (flat sides under the panels)
ZSB, ZST = -0.016, 0.056   # slide bottom / top (rib to 0.0635)
GT, GB = (0.098, -0.030), (0.148, -0.192)   # grip axis top / bottom


def _sym(half, seg=3):
    return fillet2([(x, z, r) for x, z, r in half] + [(-x, z, r) for x, z, r in reversed(half)], seg)


def slide_sec(k):
    """slide cross-section; k = 0 rear (full height) .. 1 front (lower, slimmer top) - same point count."""
    zt = ZST - 0.006 * k
    zc = 0.038 - 0.008 * k
    xt = 0.019 - 0.003 * k
    return _sym([(HWS, ZSB, 0.002), (HWS, zc, 0.003), (xt, zt, 0.003), (0.0090 - 0.001 * k, zt, 0.0012),
                 (0.0090 - 0.001 * k, zt + 0.0075 - 0.0005 * k, 0.0015)])


def slide():
    ys = [SY0, -0.160, -0.150, -0.140, -0.130, -0.120, -0.110, SY1]
    ks = [1.0, 1.0, 0.96, 0.82, 0.5, 0.18, 0.0, 0.0]
    side = fillet2([(SY0 + 0.010, ZSB - 0.01), (SY1 + 0.01, ZSB - 0.01), (SY1 + 0.01, 0.08), (SY0 + 0.016, 0.08),
                    (SY0, 0.040, 0.004), (SY0, ZSB + 0.009, 0.003)])
    sl = part('Slide', loft_y([(y, slide_sec(k)) for y, k in zip(ys, ks)]), 'DarkSteel', wn=False)
    cut(sl, slab(side, -0.1, 0.1), 'INTERSECT')
    finish(sl, 0.0012, 2, 35)          # round the slide body, then cut the features crisp
    cuts = [cyl_vf((0, SY0, 0), 0.0118, 0.08, 'Y', 24),                                     # muzzle bushing bore
            slab(fillet2([(-0.088, 0.012, 0.004), (0.002, 0.012, 0.004), (0.002, 0.09), (-0.088, 0.09)]), -0.06, 0.006),
            plate_xy(stadium2(0, -0.265, 0.070, 0.0115, pi / 2), 0.010, 0.09)]               # top window
    for sg in (1, -1):        # recessed flats on the slimmer front of the slide
        cuts.append(slab(fillet2([(-0.288, 0.0, 0.010), (-0.170, 0.0, 0.010), (-0.170, 0.026, 0.010),
                                  (-0.288, 0.026, 0.010)]), sg * (HWS - 0.0015), sg * 0.06))
    for sg in (1, -1):        # serrations: 6 front, 9 rear, slanted 14 deg
        for k in range(6):
            yc = -0.343 + k * 0.0095
            g = box_vf((sg * (HWS + 0.0085), yc, 0.016), (0.020, 0.0030, 0.050))
            cuts.append(rot_about(g, (0, yc, 0.016), 'X', 14))
        for k in range(9):
            yc = 0.032 + k * 0.0095
            g = box_vf((sg * (HWS + 0.0085), yc, 0.016), (0.020, 0.0030, 0.050))
            cuts.append(rot_about(g, (0, yc, 0.016), 'X', 14))
    detail(sl, cuts)
    marking(sl, 'SPARROW-9', (HWS - 0.0015, -0.229, 0.013), (1, 0, 0), 0.0105)
    marking(sl, 'HAVEN  9x21', (-HWS + 0.0015, -0.229, 0.013), (-1, 0, 0), 0.0072)
    # sights (front post with a faded red insert, notch rear sight in a dovetail), extractor, striker end plate
    fpost = merge_vf(plate_xz(fillet2([(0.0075, 0.048), (0.0075, 0.058, 0.002), (-0.0075, 0.058, 0.002), (-0.0075, 0.048)]),
                              -0.358, -0.344),
                     plate_xz(fillet2([(0.0034, 0.056), (0.0034, 0.0700, 0.0012), (-0.0034, 0.0700, 0.0012), (-0.0034, 0.056)]),
                              -0.356, -0.346))
    part('FrontSight', fpost, 'Blackened', sl, bev=(0.0005, 2, 35))
    part('FrontSight_Insert', cyl_vf((0, -0.3457, 0.0660), 0.0018, 0.0012, 'Y', 12), 'MarkRed', sl)
    rs = part('RearSight', plate_xz(fillet2([(0.018, 0.054), (0.018, 0.074, 0.002), (-0.018, 0.074, 0.002), (-0.018, 0.054)]),
                                    0.094, 0.110), 'Blackened', sl, wn=False)
    cut(rs, [box_vf((0, 0.102, 0.0745), (0.0072, 0.03, 0.013)),
             slab(fillet2([(0.090, 0.074), (0.090, 0.090), (0.102, 0.090)]), -0.03, 0.03)])
    finish(rs, 0.0006, 2, 35)
    part('Extractor', slab(fillet2([(-0.004, 0.026, 0.0012), (0.030, 0.026, 0.0012), (0.030, 0.032, 0.0012),
                                    (-0.004, 0.032, 0.0012)]), -HWS - 0.0016, -HWS + 0.0008), 'Steel', sl)
    ep = plate_xz(fillet2([(0.0115, 0.002, 0.003), (0.0115, 0.034, 0.003), (-0.0115, 0.034, 0.003), (-0.0115, 0.002, 0.003)]),
                  SY1 - 0.0008, SY1 + 0.0016)
    part('Slide_EndPlate', ep, 'Steel', sl, bev=(0.0004, 1, 35))
    group(sl, (0, SY0, 0.020), 'translate', 'Y', 0.080, 'Cycle',
          'slide: recoils 0.080 m rearward and returns once per shot (locks back on an empty magazine)')
    return sl


def barrel():
    prof = [(0, -0.372), (0.0052, -0.372), (0.0052, -0.382), (0.0105, -0.382), (0.0112, -0.380), (0.0112, -0.090),
            (0, -0.090)]
    b = lathe_axis(prof, 24, (0, 0, 0), 'Y')
    hood = box_between((-0.0135, -0.092, -0.010), (0.0135, 0.004, 0.0245))
    bb = part('Barrel', union_vf(b, hood), 'Steel', wn=False)
    finish(bb, 0.0008, 2, 35)
    marking(bb, '9x21', (-0.0060, -0.044, 0.0245), (0, 0, 1), 0.0062, up=(0, 1, 0))


def frame():
    prof = fillet2([(-0.352, ZSB, 0.002), (-0.352, -0.046, 0.009), (-0.104, -0.046, 0.004), (-0.096, -0.050, 0.004),
                    (0.060, -0.050, 0.006), (0.080, -0.044, 0.004), (0.150, -0.038, 0.010), (0.174, -0.028, 0.008),
                    (0.170, ZSB, 0.003)])
    fr_ = part('Frame', slab(prof, -HWF, HWF), 'PolyBlack', wn=False)
    # grip: swept section with a rounded backstrap and a flared base, unioned with the frame
    f = P.Frame(GT, GB)

    def gsec(i, s):
        w, uf, ub = HWG, -0.040, 0.040
        if s > 0.86:
            k = smooth01((s - 0.86) / 0.14)
            w += 0.0042 * k
            ub += 0.0040 * k
            uf -= 0.0035 * k
        return fillet2([(w * 0.80, uf, 0.009), (w, uf + 0.010, 0.006), (w, ub - 0.020, 0.012), (w * 0.62, ub, 0.016),
                        (-w * 0.62, ub, 0.016), (-w, ub - 0.020, 0.012), (-w, uf + 0.010, 0.006), (-w * 0.80, uf, 0.009)],
                       3)
    grip = sweep_yz(P.line_path(GT, GB, 30), gsec)
    cut(fr_, grip, 'UNION')
    cuts = [box_between((-0.0055, -0.020, -0.066), (0.0055, 0.012, -0.020)),                  # trigger slot
            f.box(-0.0162, 0.0162, f.L - 0.124, f.L + 0.03, -0.031, 0.027)]                       # magazine well
    cut(fr_, cuts)
    finish(fr_, 0.0014, 2, 35)
    marking(fr_, 'SI-0315', (HWF, -0.150, -0.033), (1, 0, 0), 0.0058)
    # accessory rail under the dust cover
    rail_part('Rail', -0.338, -0.244, -0.0456, down=True)
    part('TriggerGuard', P.guard_vf([(-0.104, -0.044), (-0.100, -0.092, 0.012), (0.040, -0.094, 0.014),
                                     (0.074, -0.058)], 0.0095, 0.0055, 0.0035), 'PolyBlack')
    # controls: slide stop (left), takedown lever (both sides), mag release (left), pins
    ss = merge_vf(slab(fillet2([(-0.066, -0.020, 0.003), (-0.012, -0.020, 0.002), (-0.006, -0.012, 0.003),
                                (-0.016, -0.008, 0.002), (-0.066, -0.013, 0.003)]), HWF - 0.001, HWF + 0.0032),
                  slab(fillet2([(-0.020, -0.021, 0.002), (-0.006, -0.021, 0.002), (-0.006, -0.009, 0.002),
                                (-0.020, -0.009, 0.002)]), HWF + 0.002, HWF + 0.0052))
    part('SlideStop', ss, 'Blackened', bev=(0.0005, 2, 35))
    tk = merge_vf(*[slab(fillet2([(-0.090, -0.024, 0.002), (-0.074, -0.024, 0.002), (-0.074, -0.019, 0.002),
                                  (-0.090, -0.019, 0.002)]), sg * (HWF - 0.001), sg * (HWF + 0.0024)) for sg in (1, -1)])
    part('TakedownLever', tk, 'Blackened', bev=(0.0004, 1, 35))
    part('MagRelease', lathe_axis([(0, -0.001), (0.0058, -0.001), (0.0058, 0.0030), (0.0048, 0.0042), (0, 0.0042)], 16,
                                  (HWF, 0.050, -0.043), 'X'), 'Blackened')
    part('Frame_Pins', merge_vf(*[pinhead_vf((sg * HWF, y, -0.036), (sg, 0, 0), 0.0024, 0.0008)
                                  for y in (-0.040, 0.012) for sg in (1, -1)]), 'Steel')
    trig = part('Trigger', P.trigger_vf((-0.002, -0.034), (-0.012, -0.080), 0.008, 0.0045, 0.0034), 'PolyBlack')
    part('Trigger_Safety', P.trigger_vf((-0.0035, -0.050), (-0.0125, -0.078), 0.006, 0.0013, 0.0034),
         'Blackened', trig)
    group(trig, (0, -0.002, -0.036), 'rotate', 'X', 12, 'Trigger', 'trigger (with safety blade): 12 deg rearward to fire')
    return fr_, f


def grip_panels(f):
    w_out = HWG + 0.0062
    parts_ = []
    for sg, S_ in ((1, 'L'), (-1, 'R')):
        out = fillet2([(0.010, -0.034, 0.008), (f.L - 0.024, -0.034, 0.008), (f.L - 0.024, 0.017, 0.008),
                       (0.010, 0.017, 0.008)])
        vf = f.vf(prism([V((sg * (HWG - 0.0006), s, u)) for s, u in out], (sg * 0.0068, 0, 0)))
        gp = part('GripPanel_%s' % S_, vf, 'Walnut', wn=False)
        finish(gp, 0.0024, 2, 35)
        wf = lambda s_: w_out
        cuts = []
        for c in P.checker_cutters(f, wf, 0.026, f.L - 0.040, -0.026, 0.009, 0.0062, 40.0, 0.0012, 0.0009):
            # keep only this side's cutters
            if (sum(v.x for v in c[0]) / len(c[0])) * sg > 0:
                cuts.append(c)
        cut(gp, cuts)
        weighted(gp)
        scr = [screw_vf(f.at(sg * w_out, s_, -0.008), (sg, 0, 0), 0.0034, 0.0012) for s_ in (0.018, f.L - 0.032)]
        part('GripPanel_%s_Screws' % S_, merge_vf(*scr), 'Steel')
        parts_.append(gp)
    return parts_


def magazine(f):
    body = f.box(-0.0150, 0.0150, 0.050, f.L + 0.001, -0.0285, 0.0245)
    m = part('Magazine', body, 'DarkSteel', bev=(0.0010, 2, 35))
    bp = fillet2([(f.L - 0.0015, -0.037, 0.003), (f.L + 0.011, -0.039, 0.004), (f.L + 0.012, 0.031, 0.004),
                  (f.L - 0.0015, 0.031, 0.003)])
    part('Magazine_Baseplate', f.vf(slab(bp, -0.0195, 0.0195)), 'PolyBlack', m, bev=(0.0016, 2, 35))
    group(m, f.at(0, 0.050, 0), 'translate', V((0, f.t.y, f.t.z)), 0.18, 'Reload',
          'magazine: drops out of the grip along the grip axis (0.18 m)', stage=(0, 0.45))


def build():
    r = begin('SP9')
    slide()
    barrel()
    fr_, f = frame()
    grip_panels(f)
    magazine(f)
    point('Muzzle', (0, -0.382, 0), 'muzzle', (0, -1, 0), note='bullet origin + muzzle flash')
    point('Ejection', (-0.022, -0.040, 0.050), 'ejection', (-0.62, 0.25, 0.74),
          note='spent cases leave the port up and to the right')
    point('Grip_Right', (0, 0.112, -0.110), 'grip_right', note='firing hand on the grip (RightGripAttachment)')
    point('Grip_Left', (0, 0.118, -0.135), 'grip_left', note='support hand wraps the firing hand (two-hand hold)')
    point('Aim', (0, 0.190, 0.069), 'aim_eye', (0, -1, 0), note='eye position on the notch / post sight line')
    point('MagWell', f.at(0, f.L, 0), 'magwell', (0, f.t.y, f.t.z))
    rig.model('Sparrow9', 'Sparrow-9', 'weapon', WEAPONS['SP9'][4],
              origin='on the bore axis directly above the trigger (all five weapons share this datum)')
    rig.channel('Trigger', 'trigger pull', 0.04)
    rig.channel('Cycle', 'slide cycle per shot: play 0 -> 1 -> 0 (hold at 1 when the magazine is empty = slide lock)',
                0.035)
    rig.channel('Reload', 'magazine out (1) / in (0)', 0.6)
    rig.pose('fire', {'Trigger': 1, 'Cycle': 1}, description='trigger pulled, slide fully back', ground=False)
    rig.pose('reload', {'Reload': 1, 'Cycle': 1}, description='slide locked back, magazine out', ground=False)
    rig.system('Weapon', kind='pistol', caliber='9x21 mm (fictional)', magazine=17, fire_modes=['SEMI'], rpm=420,
               muzzle_velocity_mps=370, effective_range_studs=round(60 * S), reload_s=1.5, damage_hint='low-medium',
               recoil_hint='snappy muzzle flip', aim='notch rear sight + post front sight (faded red insert)',
               ammo_item='Ammo_9x21', holster='hip')
    rig.note('Weapon origin = bore axis above the trigger; the muzzle points -Z in Roblox (LookVector).')
    return r
