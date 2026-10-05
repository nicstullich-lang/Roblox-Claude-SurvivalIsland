"""XR-77 admin weapons (all fictional, game-oriented):
  * M77 "Thunder" 7-barrel rotary cannon in the left chin blister (gun door + spinning barrel cluster)
  * two main bays: drop-down ejector launchers with 2x LRM-9 "Lancer" (left) / 2x GBU-X "Hammer" glide bombs (right)
  * two side bays: drop rails with 1x SRM-4 "Viper" each
  * two wing pylons with twin-rail launchers (2x SRM-4 each)
  * retractable belly turret with twin 6-barrel rotary guns (360 deg)
  * pop-up dorsal "Helios" directed-energy turret
Every store is its own group (kind 'store') so the game can hide / release it individually.
"""
from .lib import *
from common import rig
from . import airframe as AF


def hinge(ob, pivot, typ, axis, opn, channel, stage, desc, kind='part', **kw):
    set_origin(ob, pivot)
    rig.motion(ob, typ, axis, opn, channel, stage, kind, desc, **kw)


def ylathe(profile, c, n=24, ring=False):
    """lathe (radius, y-offset) around a Y-axis line through c."""
    prof = list(profile) + ([profile[0]] if ring else [])
    return orient(lathe_vf(prof, n, cap0=not ring, cap1=not ring), (c[0], c[1], c[2]), 'Y')


def fin_vf(c, ang, y0, root, tip, span, sweep, r0, th=0.006):
    """trapezoid fin on a body of radius r0 along Y, at azimuth ang (deg, 0 = +X, 90 = +Z)."""
    a = radians(ang)
    d = V((cos(a), 0, sin(a)))
    t = V((-sin(a), 0, cos(a))) * (th / 2)
    base = V(c) + d * (r0 - 0.003)
    q = [base + V((0, y0, 0)), base + V((0, y0 + root, 0)),
         base + d * span + V((0, y0 + sweep + tip, 0)), base + d * span + V((0, y0 + sweep, 0))]
    return prism([p - t for p in q], t * 2)


def missile(name, c, L, r, parent, kind='LRM', body='Missile'):
    """a missile along Y (nose -> -Y) centred at c. Returns the group object (origin at c)."""
    c = V(c)
    nose = 0.42 if kind == 'LRM' else 0.30
    prof = [(0.0, -L / 2)]
    for k in range(1, 9):
        t = k / 8
        prof.append((r * sqrt(1 - (1 - t) ** 2), -L / 2 + nose * t))
    prof += [(r, L / 2 - 0.10), (r * 0.82, L / 2), (r * 0.55, L / 2), (r * 0.55, L / 2 - 0.05), (0.0, L / 2 - 0.05)]
    g = mk(name, ylathe(prof, c, 24), body, 'Weapons', parent, sharp=35)
    mk(name + '_Seeker', ylathe([(0.0, -L / 2 - 0.002), (r * 0.55, -L / 2 + 0.07), (r * 0.62, -L / 2 + 0.10),
                                 (0.0, -L / 2 + 0.10)], c, 20), 'SensorGlass', 'Weapons', g)
    bands = [ylathe([(r + 0.001, yy), (r + 0.001, yy + 0.04), (r - 0.002, yy + 0.04), (r - 0.002, yy)], c, 24, ring=True)
             for yy in (-L / 2 + nose + 0.10,)]
    mk(name + '_WarheadBand', merge_vf(*bands), 'Yellow', 'Weapons', g, smooth=False)
    mk(name + '_MotorBand', ylathe([(r + 0.001, 0.15), (r + 0.001, 0.19), (r - 0.002, 0.19), (r - 0.002, 0.15)], c, 24,
                                   ring=True), 'BandBrown', 'Weapons', g, smooth=False)
    fins = []
    for ang in (45, 135, 225, 315):
        fins.append(fin_vf(c, ang, L / 2 - 0.36, 0.30, 0.12, 0.15 if kind == 'LRM' else 0.12, 0.16, r))
        if kind == 'LRM':
            fins.append(fin_vf(c, ang, -0.30, 0.90, 0.70, 0.035, 0.10, r, 0.004))        # long strakes
        else:
            fins.append(fin_vf(c, ang, -L / 2 + 0.34, 0.10, 0.05, 0.07, 0.04, r, 0.005))  # canards
    mk(name + '_Fins', merge_vf(*fins), body, 'Weapons', g, smooth=False)
    mk(name + '_Nozzle', ylathe([(r * 0.50, L / 2 - 0.05), (r * 0.56, L / 2 + 0.005), (r * 0.40, L / 2 + 0.005),
                                 (r * 0.40, L / 2 - 0.05)], c, 16, ring=True), 'Exhaust', 'Weapons', g)
    set_origin(g, c)
    return g


def bomb(name, c, L, r, parent):
    c = V(c)
    prof = [(0.0, -L / 2), (r * 0.45, -L / 2 + 0.06), (r * 0.80, -L / 2 + 0.22), (r, -L / 2 + 0.50), (r, L / 2 - 0.55),
            (r * 0.62, L / 2 - 0.05), (r * 0.40, L / 2), (0.0, L / 2)]
    g = mk(name, ylathe(prof, c, 28), 'Bomb', 'Weapons', parent, sharp=35)
    mk(name + '_Seeker', ylathe([(0.0, -L / 2 - 0.003), (r * 0.42, -L / 2 + 0.055), (0.0, -L / 2 + 0.055)], c, 20),
       'SensorGlass', 'Weapons', g)
    mk(name + '_Band', ylathe([(r + 0.001, -L / 2 + 0.55), (r + 0.001, -L / 2 + 0.60), (r - 0.002, -L / 2 + 0.60),
                               (r - 0.002, -L / 2 + 0.55)], c, 28, ring=True), 'Yellow', 'Weapons', g, smooth=False)
    wing = box_between(c + V((-0.14, -0.35, r - 0.01)), c + V((0.14, 0.25, r + 0.012)))
    pivot = cyl_vf(c + V((0, -0.05, r + 0.02)), 0.035, 0.03, 'Z', 12)
    mk(name + '_Wings', merge_vf(wing, pivot), 'Bomb', 'Weapons', g, bev=(0.004, 1, 30))
    fins = [fin_vf(c, ang, L / 2 - 0.50, 0.42, 0.20, 0.10, 0.18, r * 0.9) for ang in (45, 135, 225, 315)]
    mk(name + '_Fins', merge_vf(*fins), 'Bomb', 'Weapons', g, smooth=False)
    lugs = [box_between(c + V((-0.02, yy - 0.03, r - 0.005)), c + V((0.02, yy + 0.03, r + 0.035))) for yy in (-0.38, 0.38)]
    mk(name + '_Lugs', merge_vf(*lugs), 'Steel', 'Weapons', g)
    set_origin(g, c)
    return g


def tag_store(g, store, launch, desc):
    rig.motion(g, 'fixed', None, None, None, (0, 1), 'store', desc, store=store, launch=launch)


# ======================================================================== gun
def build_gun():
    c0 = V((0.30, 0.0, 1.70))
    parts = []
    for k in range(7):
        a = 2 * pi * k / 7
        o = V((0.085 * cos(a), 0, 0.085 * sin(a)))
        parts.append(cyl_between(c0 + o + V((0, -10.52, 0)), c0 + o + V((0, -8.30, 0)), 0.021, 10))
        parts.append(cyl_between(c0 + o + V((0, -10.56, 0)), c0 + o + V((0, -10.44, 0)), 0.026, 10))
    for yy in (-10.25, -9.35):
        parts.append(cyl_between(c0 + V((0, yy - 0.03, 0)), c0 + V((0, yy + 0.03, 0)), 0.118, 18))
    parts.append(cyl_between(c0 + V((0, -10.52, 0)), c0 + V((0, -8.30, 0)), 0.04, 12))
    bar = mk('Gun_Barrels', merge_vf(*parts), 'Gunmetal', 'Weapons', sharp=35)
    hinge(bar, c0 + V((0, -9.4, 0)), 'spin', 'Y', None, 'Gun', (0.6, 1.0), 'rotary cannon barrel cluster (spins while firing)',
          speed=60.0)
    rec = merge_vf(cyl_between(c0 + V((0, -8.32, 0)), c0 + V((0, -7.92, 0)), 0.15, 18),
                   box_between(c0 + V((-0.10, -8.25, 0.10)), c0 + V((0.10, -7.95, 0.18))))
    mk('Gun_Receiver', rec, 'Gunmetal', 'Weapons', bev=(0.006, 1, 30))
    chute = tube_vf([c0 + V((0.0, -7.95, 0.14)), c0 + V((0.0, -7.75, 0.20)), c0 + V((0.0, -7.55, 0.20))], 0.05, 8)
    mk('Gun_FeedChute', chute, 'Steel', 'Weapons')
    d = AF.DOORS['Gun_Door']
    hinge(d, AF.hinge_line((0.453, -10.40), (0.453, -8.70), 'bottom')[0], 'rotate', 'Y', -100, 'Gun', (0.0, 0.6), 'gun bay door: drops open before firing')
    rig.point('Muzzle_Gun', (0.30, -10.62, 1.70), 'muzzle', attach=bar, direction=(0, -1, 0),
              weapon='M77 Thunder 7-barrel rotary cannon (fictional)')


# ======================================================================== main bays
def build_main_bays():
    for s in (1, -1):
        S_ = 'L' if s > 0 else 'R'
        xc = s * 0.49
        # bay structure
        fr = [box_between((s * 0.10, yy - 0.025, 2.17), (s * 0.88, yy + 0.025, 2.25)) if s > 0 else
              box_between((-0.88, yy - 0.025, 2.17), (-0.10, yy + 0.025, 2.25)) for yy in (-1.0, -0.2, 0.6, 1.4, 2.2, 3.0, 3.7)]
        mk('MainBay_Frames_' + S_, merge_vf(*fr), 'BayGrey', 'Weapons')
        hyd = [tube_vf([V((s * 0.83, -1.4, 2.20)), V((s * 0.83, 3.8, 2.20))], 0.012, 8),
               tube_vf([V((s * 0.80, -1.4, 2.22)), V((s * 0.80, 3.8, 2.22))], 0.009, 8)]
        mk('MainBay_Lines_' + S_, merge_vf(*hyd), 'Steel', 'Weapons')
        lamps = [cyl_vf((xc, yy, 2.245), 0.04, 0.012, 'Z', 12) for yy in (-0.6, 3.2)]
        mk('MainBay_Lamps_' + S_, merge_vf(*lamps), 'LED', 'Weapons')
        # telescopic launcher arms (fixed sleeves) + moving ejector launcher
        slv = [cyl_between((xc, yy, 2.25), (xc, yy, 2.06), 0.04, 12) for yy in (-0.4, 2.8)]
        mk('MainBay_ArmSleeves_' + S_, merge_vf(*slv), 'Steel', 'Weapons')
        beam = merge_vf(box_between((xc - 0.08, -1.10, 2.00), (xc + 0.08, 3.50, 2.08)),
                        *[cyl_between((xc, yy, 2.08), (xc, yy, 2.30), 0.028, 12) for yy in (-0.4, 2.8)],
                        *[box_between((xc + dx - 0.03, yy - 0.12, 1.94), (xc + dx + 0.03, yy + 0.12, 2.00))
                          for dx in (-0.19, 0.19) for yy in (-0.3, 2.3)])
        la = mk('MainBay_Launcher_' + S_, beam, 'GearWhite', 'Weapons', bev=(0.004, 1, 30))
        if s > 0:
            st = [missile('Store_LRM_L%d' % (k + 1), (xc + dx, 1.10, 1.835), 3.70, 0.095, la, 'LRM')
                  for k, dx in enumerate((-0.19, 0.19))]
            for g in st:
                tag_store(g, 'LRM-9 Lancer long-range missile (fictional)', 'drop 0.4 m then ignite, fly toward -Y',
                          'long-range missile on the left bay launcher')
        else:
            st = [bomb('Store_GBU_R%d' % (k + 1), (xc + dx, 1.00, 1.78), 3.00, 0.16, la) for k, dx in enumerate((-0.19, 0.19))]
            for g in st:
                tag_store(g, 'GBU-X Hammer precision glide bomb (fictional)', 'drop, pop wings, glide to target',
                          'precision glide bomb on the right bay launcher')
        hinge(la, (xc, 1.2, 2.04), 'translate', 'Z', -0.58, 'MainBays', (0.45, 1.0),
              'bay launcher: lowers the stores 0.58 m clear of the airframe')
        for nm, hxx, ang in (('MainBay_DoorIn_' + S_, s * 0.10, 100 * s), ('MainBay_DoorOut_' + S_, s * 0.88, -100 * s)):
            d = AF.DOORS[nm]
            hx2 = hxx + (-s * 0.003 if abs(hxx) < 0.5 else s * 0.003)
            hinge(d, AF.hinge_line((hx2, -1.60), (hx2, 4.00), 'bottom')[0], 'rotate', 'Y', ang, 'MainBays', (0.0, 0.45),
                  'weapon bay door: swings down 100 deg')
            stiff = [box_between((min(hxx, s * 0.49) + 0.02, yy - 0.012, body_bot(0.49, yy) + 0.022),
                                 (max(hxx, s * 0.49) - 0.02, yy + 0.012, body_bot(0.49, yy) + 0.05)) for yy in (-0.8, 0.4, 1.6, 2.8)]
            mk(nm + '_Stiffeners', merge_vf(*stiff), 'BayGrey', 'Weapons', d)
        rig.point('Launch_MainBay_' + S_, (xc, 1.10, 1.25), 'launch', attach=la, direction=(0, -1, 0),
                  note='stores leave from here after the launcher is down')


# ======================================================================== side bays
def build_side_bays():
    for s in (1, -1):
        S_ = 'L' if s > 0 else 'R'
        xc = s * 1.32
        rail = merge_vf(box_between((xc - 0.05, -2.45, 1.90), (xc + 0.05, -0.55, 1.95)),
                        *[cyl_between((xc, yy, 1.95), (xc, yy, 2.05), 0.022, 10) for yy in (-2.2, -0.8)],
                        box_between((xc - 0.02, -2.40, 1.85), (xc + 0.02, -0.60, 1.90)))
        la = mk('SideBay_Rail_' + S_, rail, 'GearWhite', 'Weapons', bev=(0.003, 1, 30))
        slv = [cyl_between((xc, yy, 2.02), (xc, yy, 1.96), 0.035, 12) for yy in (-2.2, -0.8)]
        mk('SideBay_Sleeves_' + S_, merge_vf(*slv), 'Steel', 'Weapons')
        g = missile('Store_SRM_Side%s' % S_, (xc, -1.50, 1.765), 2.40, 0.065, la, 'SRM')
        tag_store(g, 'SRM-4 Viper short-range missile (fictional)', 'rail launch toward -Y', 'side-bay dogfight missile')
        hinge(la, (xc, -1.5, 1.93), 'translate', 'Z', -0.42, 'SideBays', (0.40, 1.0),
              'side-bay drop rail: lowers the missile below the airframe')
        d = AF.DOORS['SideBay_Door_' + S_]
        hx = s * 1.02
        hinge(d, AF.hinge_line((s * 1.017, -2.70), (s * 1.017, -0.25), 'bottom')[0], 'rotate', 'Y', 100 * s, 'SideBays', (0.0, 0.45),
              'side-bay door: hinged on its inboard edge, swings down')
        rig.point('Launch_SideBay_' + S_, (xc, -2.75, 1.35), 'launch', attach=la, direction=(0, -1, 0))


# ======================================================================== wing pylons
def build_pylons():
    for s in (1, -1):
        S_ = 'L' if s > 0 else 'R'
        x = s * 4.05
        from .airframe import wing_z
        loops = []
        for yy in cosspace(1.70, 4.10, 16):
            t = (yy - 1.70) / 2.40
            hw = 0.05 * sin(pi * min(1.0, t * 1.0)) ** 0.5 + 0.006
            ztop = wing_z(abs(x), yy, upper=False) + 0.02
            loops.append([V((x - hw, yy, ztop)), V((x + hw, yy, ztop)), V((x + hw, yy, 1.70)), V((x - hw, yy, 1.70))])
        mk('Pylon_' + S_, loft(loops), 'Skin', 'Weapons', sharp=35)
        lau = merge_vf(box_between((x - 0.24, 2.0, 1.64), (x + 0.24, 3.9, 1.71)),
                       *[box_between((x + dx - 0.025, 2.05, 1.58), (x + dx + 0.025, 3.85, 1.64)) for dx in (-0.18, 0.18)],
                       *[box_between((x + dx - 0.012, yy - 0.04, 1.71), (x + dx + 0.012, yy + 0.04, 1.80)) for dx in (-0.10, 0.10) for yy in (2.3, 3.6)])
        mk('Pylon_Launcher_' + S_, lau, 'Skin', 'Weapons', bev=(0.004, 1, 30))
        for k, dx in enumerate((-0.18, 0.18)):
            g = missile('Store_SRM_Pylon%s%d' % (S_, k + 1), (x + dx, 2.95, 1.513), 2.40, 0.065, None, 'SRM')
            tag_store(g, 'SRM-4 Viper short-range missile (fictional)', 'rail launch toward -Y', 'wing pylon missile')
            rig.point('Launch_Pylon%s%d' % (S_, k + 1), (x + dx, 1.70, 1.513), 'launch', attach=g, direction=(0, -1, 0))


# ======================================================================== belly turret
def build_belly_turret():
    yc = 5.45
    col = merge_vf(cyl_vf((0, yc, 2.27), 0.44, 0.06, 'Z', 36), cyl_between((0, yc, 2.24), (0, yc, 1.80), 0.14, 20))
    lift = mk('BellyTurret_Lift', col, 'GearWhite', 'Weapons', sharp=35)
    rails = [cyl_between((x, yc + dy, 2.30), (x, yc + dy, 2.06), 0.03, 10) for x in (-0.40, 0.40) for dy in (-0.3, 0.3)]
    mk('BellyTurret_Guides', merge_vf(*rails), 'Steel', 'Weapons')
    ring = cyl_vf((0, yc, 1.78), 0.30, 0.05, 'Z', 32)
    mk('BellyTurret_Ring', ring, 'Steel', 'Weapons', lift)
    head_pts = []
    for k in range(8):
        a = 2 * pi * k / 8 + pi / 8
        head_pts.append((0.31 * cos(a), 0.31 * sin(a)))
    head = merge_vf(prism([V((p[0], yc + p[1], 1.76)) for p in head_pts], (0, 0, -0.30)))
    yaw = mk('BellyTurret_Yaw', head, 'SkinDark', 'Weapons', lift, bev=(0.01, 1, 30))
    win = cyl_vf((0.0, yc - 0.30, 1.61), 0.06, 0.02, 'Y', 16)
    mk('BellyTurret_Sight', win, 'SensorGlass', 'Weapons', yaw)
    pitch_parts = [cyl_between((-0.30, yc, 1.61), (0.30, yc, 1.61), 0.10, 18)]
    pit = mk('BellyTurret_Pitch', merge_vf(*pitch_parts), 'Gunmetal', 'Weapons', yaw)
    for sx in (-1, 1):
        S_ = 'L' if sx > 0 else 'R'
        gx = sx * 0.33
        hs = merge_vf(box_between((gx - 0.07, yc - 0.20, 1.54), (gx + 0.07, yc + 0.22, 1.68)))
        mk('BellyTurret_GunHousing_' + S_, hs, 'Gunmetal', 'Weapons', pit, bev=(0.008, 1, 30))
        bp = []
        for k in range(6):
            a = 2 * pi * k / 6
            o = V((0.045 * cos(a), 0, 0.045 * sin(a)))
            bp.append(cyl_between(V((gx, yc - 0.20, 1.61)) + o, V((gx, yc - 0.94, 1.61)) + o, 0.013, 8))
        bp.append(cyl_between((gx, yc - 0.55, 1.61), (gx, yc - 0.60, 1.61), 0.07, 14))
        bp.append(cyl_between((gx, yc - 0.88, 1.61), (gx, yc - 0.92, 1.61), 0.07, 14))
        gb = mk('BellyTurret_Barrels_' + S_, merge_vf(*bp), 'Gunmetal', 'Weapons', pit)
        hinge(gb, (gx, yc - 0.6, 1.61), 'spin', 'Y', None, 'BellyTurret', (0.9, 1.0),
              'belly turret rotary gun (spins while firing)', speed=55.0)
        rig.point('Muzzle_Belly_' + S_, (gx, yc - 0.95, 1.61), 'muzzle', attach=gb, direction=(0, -1, 0),
                  weapon='twin 6-barrel rotary guns (fictional)')
    hinge(pit, (0.0, yc, 1.61), 'aim_pitch', 'X', None, None, (0, 1),
          'belly turret gun elevation (+ = guns down, Blender X)', min=-10, max=90, speed=90)
    hinge(yaw, (0.0, yc, 1.70), 'aim_yaw', 'Z', None, None, (0, 1), 'belly turret traverse (360 deg)', speed=120)
    hinge(lift, (0.0, yc, 2.27), 'translate', 'Z', -0.80, 'BellyTurret', (0.35, 1.0),
          'turret elevator: lowers the gun turret out of the belly')
    for nm, hx, ang in (('Turret_Door_L', 0.50, -100), ('Turret_Door_R', -0.50, 100)):
        d = AF.DOORS[nm]
        hinge(d, AF.hinge_line((hx * 1.006, 4.45), (hx * 1.006, 6.45), 'bottom')[0], 'rotate', 'Y', ang, 'BellyTurret', (0.0, 0.35),
              'belly turret door: swings down')


# ======================================================================== dorsal energy weapon
def build_laser():
    yc = 1.05
    col = merge_vf(cyl_vf((0, yc, 2.36), 0.36, 0.05, 'Z', 32), cyl_between((0, yc, 2.38), (0, yc, 2.52), 0.12, 18))
    lift = mk('Laser_Lift', col, 'GearWhite', 'Weapons', sharp=35)
    rails = [cyl_between((x, yc, 2.32), (x, yc, 2.62), 0.025, 10) for x in (-0.30, 0.30)]
    mk('Laser_Guides', merge_vf(*rails), 'Steel', 'Weapons')
    base_pts = [(0.36 * cos(2 * pi * k / 8 + pi / 8), 0.36 * sin(2 * pi * k / 8 + pi / 8)) for k in range(8)]
    base = prism([V((p[0], yc + 0.15 + p[1], 2.52)) for p in base_pts], (0, 0, 0.10))
    yaw = mk('Laser_Yaw', base, 'SkinDark', 'Weapons', lift, bev=(0.008, 1, 30))
    pc = V((0.0, yc + 0.15, 2.73))
    hexa = [V((0.11 * cos(2 * pi * k / 6), 0, 0.09 * sin(2 * pi * k / 6))) + pc for k in range(6)]
    barrel = prism([p + V((0, 0.06, 0)) for p in hexa], (0, -1.00, 0))
    trun = cyl_between(pc + V((-0.20, 0, 0)), pc + V((0.20, 0, 0)), 0.07, 16)
    pit = mk('Laser_Pitch', merge_vf(barrel, trun), 'SkinDark', 'Weapons', yaw, sharp=30)
    fins = [box_between(pc + V((-0.13, -0.15 - 0.05 * k, -0.075)), pc + V((0.13, -0.135 - 0.05 * k, 0.075))) for k in range(9)]
    mk('Laser_CoolingFins', merge_vf(*fins), 'Titanium', 'Weapons', pit)
    caps = [cyl_between(pc + V((sx * 0.15, -0.03, 0.0)), pc + V((sx * 0.15, -0.50, 0.0)), 0.04, 14) for sx in (-1, 1)]
    mk('Laser_Capacitors', merge_vf(*caps), 'Gunmetal', 'Weapons', pit, bev=(0.006, 1, 30))
    lens = cyl_between(pc + V((0, -0.93, 0)), pc + V((0, -0.945, 0)), 0.07, 18)
    mk('Laser_Lens', lens, 'Laser', 'Weapons', pit)
    ring = ylathe([(0.075, -0.92), (0.095, -0.92), (0.095, -0.945), (0.075, -0.945)], pc, 18, ring=True)
    mk('Laser_LensRing', ring, 'Titanium', 'Weapons', pit)
    hinge(pit, pc, 'aim_pitch', 'X', None, None, (0, 1), 'energy weapon elevation (- = up, Blender X)',
          min=-60, max=5, speed=70)
    hinge(yaw, (0.0, yc + 0.15, 2.52), 'aim_yaw', 'Z', None, None, (0, 1), 'energy weapon traverse (360 deg)', speed=90)
    hinge(lift, (0.0, yc, 2.36), 'translate', 'Z', 0.62, 'DorsalLaser', (0.35, 1.0),
          'energy weapon elevator: raises the turret above the spine')
    rig.point('Muzzle_Laser', pc + V((0, -0.95, 0)), 'muzzle', attach=pit, direction=(0, -1, 0),
              weapon='Helios directed-energy beam (fictional)')
    for nm, hx, ang in (('Laser_Door_L', 0.45, 100), ('Laser_Door_R', -0.45, -100)):
        d = AF.DOORS[nm]
        hinge(d, AF.hinge_line((hx * 1.0067, 0.20), (hx * 1.0067, 1.90), 'top')[0], 'rotate', 'Y', ang, 'DorsalLaser', (0.0, 0.35),
              'energy weapon bay door: swings up')


def build():
    build_gun()
    build_main_bays()
    build_side_bays()
    build_pylons()
    build_belly_turret()
    build_laser()
