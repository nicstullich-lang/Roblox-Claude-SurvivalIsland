"""XR-77 cockpit: one-piece canopy (frame + gold-tinted glass) on a rear hinge, ejection seat with harness,
panoramic display with real symbology geometry (readable in Roblox without textures), HUD, side-stick, throttle,
consoles with guarded switches, warning panel, oxygen, emergency handles, lighting.

Pilot ergonomics: seat reference point SRP (0, -6.55, 2.20); eye ~ (0, -6.45, 3.00); panel face y -7.55.
"""
from .lib import *
from common import rig
from . import airframe as AF

SRP = V((0.0, -6.55, 2.20))
BACK = radians(18)            # seat back recline


def tilt(vf, pivot, deg, axis='X'):
    return rot_about(vf, pivot, axis, deg)


def screen(c, w, h, tilt_deg, kind, parent):
    """display: bezel + dark glass + symbology (emissive strips 1 mm proud). c = centre of the glass face."""
    px = Matrix.Translation(c) @ Matrix.Rotation(radians(tilt_deg), 4, 'X')
    loc = lambda vf: xform_vf(vf, px)
    bez = loc(box_vf((0, -0.012, 0), (w + 0.03, 0.022, h + 0.03)))
    glass = loc(box_vf((0, 0.0, 0), (w, 0.004, h)))
    sym = {'ScreenGreen': [], 'ScreenAmber': [], 'ScreenCyan': [], 'ScreenRed': []}
    f = 0.0025                                         # just in front of the glass (the pilot sits toward +y)

    def strip(p0, p1, wd=0.004, col='ScreenGreen'):
        a, b = V((p0[0], f, p0[1])), V((p1[0], f, p1[1]))
        d = b - a
        if d.length < 1e-6:
            return
        n = V((-d.z, 0, d.x)).normalized() * wd / 2
        q = [a + n, b + n, b - n, a - n]
        sym[col].append(loc(prism(q, (0, 0.0015, 0))))

    def arc(cx, cz, r, a0, a1, n=16, col='ScreenGreen', wd=0.003):
        for k in range(n):
            t0, t1 = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
            strip((cx + r * cos(t0), cz + r * sin(t0)), (cx + r * cos(t1), cz + r * sin(t1)), wd, col)

    def block(x0, z0, x1, z1, col):
        sym[col].append(loc(prism([V((x0, f, z0)), V((x1, f, z0)), V((x1, f, z1)), V((x0, f, z1))], (0, 0.0015, 0))))

    hw, hh = w / 2, h / 2
    if kind == 'pano':
        # three formats across the panoramic display: tactical radar, attitude/flight, engines + VTOL
        cx = -hw + w / 6
        for r in (0.035, 0.065, 0.095):
            arc(cx, -hh + 0.015, r, radians(30), radians(150), 14)
        strip((cx, -hh + 0.015), (cx + 0.09 * cos(radians(70)), -hh + 0.015 + 0.09 * sin(radians(70))), 0.003)
        for (dx, dz, col) in ((0.03, 0.05, 'ScreenRed'), (-0.05, 0.07, 'ScreenAmber'), (0.06, 0.08, 'ScreenCyan')):
            block(cx + dx - 0.006, -hh + 0.015 + dz - 0.006, cx + dx + 0.006, -hh + 0.015 + dz + 0.006, col)
        # attitude: horizon + pitch ladder + speed/alt tapes
        cx = 0.0
        strip((cx - 0.10, -0.01), (cx + 0.10, 0.012), 0.004, 'ScreenCyan')
        for k in (-2, -1, 1, 2):
            z = k * 0.03
            strip((cx - 0.035, z), (cx + 0.035, z), 0.0025)
        block(cx - 0.125, -hh + 0.02, cx - 0.105, hh - 0.02, 'ScreenGreen')
        block(cx + 0.105, -hh + 0.02, cx + 0.125, hh - 0.02, 'ScreenGreen')
        strip((cx - 0.012, 0.0), (cx + 0.012, 0.0), 0.006, 'ScreenAmber')
        # engines + VTOL page: two arc gauges and nozzle angle bars
        cx = hw - w / 6
        for dx in (-0.055, 0.055):
            arc(cx + dx, 0.02, 0.04, radians(-30), radians(210), 18, 'ScreenGreen')
            strip((cx + dx, 0.02), (cx + dx + 0.03, 0.045), 0.003, 'ScreenAmber')
        for k in range(5):
            block(cx - 0.09 + k * 0.04, -hh + 0.02, cx - 0.07 + k * 0.04, -hh + 0.05 + 0.012 * k, 'ScreenCyan')
        # format separators
        for xs in (-hw + w / 3, hw - w / 3):
            strip((xs, -hh + 0.01), (xs, hh - 0.01), 0.002, 'ScreenCyan')
    elif kind == 'warn':
        for i in range(3):
            for j in range(2):
                col = 'ScreenRed' if (i + j) % 3 == 0 else 'ScreenAmber'
                block(-hw + 0.01 + i * (w - 0.02) / 3, -hh + 0.01 + j * (h - 0.02) / 2,
                      -hw + 0.01 + (i + 1) * (w - 0.02) / 3 - 0.004, -hh + 0.01 + (j + 1) * (h - 0.02) / 2 - 0.004, col)
    elif kind == 'standby':
        arc(0, 0, min(hw, hh) * 0.75, 0, 2 * pi, 20, 'ScreenGreen')
        strip((-hw * 0.6, 0), (hw * 0.6, 0.004), 0.003, 'ScreenCyan')
    screen.n = getattr(screen, 'n', 0) + 1
    obs = [mk('Cockpit_Bezel_%s_%d' % (kind, screen.n), bez, 'CockpitDark', 'Cockpit', parent, bev=(0.003, 1, 30))]
    obs.append(mk(obs[0].name.replace('Bezel', 'Glass'), glass, 'Display', 'Cockpit', parent))
    for col, parts in sym.items():
        if parts:
            obs.append(mk(obs[0].name.replace('Bezel', col), merge_vf(*parts), col, 'Cockpit', parent, smooth=False))
    return obs


def switches(c, n, pitch, tilt_deg, guard=False, red=False):
    """row of toggle switches on a panel facing up (c = first switch base)."""
    parts, guards = [], []
    for i in range(n):
        p = V(c) + V((pitch * i, 0, 0))
        parts.append(cyl_vf(p + V((0, 0, 0.004)), 0.006, 0.008, 'Z', 8))
        lever = cyl_between(p + V((0, 0, 0.008)), p + V((0, -0.010, 0.028)), 0.0022, 6)
        parts.append(lever)
        parts.append(cyl_vf(p + V((0, -0.010, 0.029)), 0.0035, 0.004, 'Z', 6))
        if guard:
            guards.append(box_vf(p + V((0, 0.0, 0.018)), (0.022, 0.03, 0.002)))
            guards.append(box_vf(p + V((0.011, 0, 0.009)), (0.002, 0.03, 0.018)))
            guards.append(box_vf(p + V((-0.011, 0, 0.009)), (0.002, 0.03, 0.018)))
    return merge_vf(*parts), (merge_vf(*guards) if guards else None)


def knobs(c, n, pitch):
    return merge_vf(*[cyl_vf(V(c) + V((pitch * i, 0, 0.007)), 0.008, 0.014, 'Z', 12) for i in range(n)])


def build_canopy():
    out = canopy_outline()
    inner = canopy_outline(inset=0.06)
    vf = skin_patch(AF.CASTER, out, 'top', t=0.035, holes=[inner], spacing=0.07, inset=GAP)
    frame = mk('Canopy', vf, ['Skin', 'Cockpit', 'SkinDark'], 'Cockpit', sharp=40, mat_idx=skin_patch.last_mi)
    set_origin(frame, CAN_HINGE)
    vf = skin_patch(AF.CASTER, inner, 'top', t=0.022, spacing=0.075, inset=0.001)
    glass = mk('Canopy_Glass', vf, 'Glass', 'Cockpit', frame, sharp=60)
    # inner frame detail: sill rails, rear arch bow, lock hooks, hinge lugs, seal
    parts = []
    ys = cosspace(CAN_Y0 + 0.25, CAN_Y1 - 0.08, 18)
    for side in (1, -1):
        rail = []
        for y in ys:
            x = side * (Wcan_(y) * 0.86 - 0.045)
            z = canopy_z(x, y) - 0.05
            rail.append(V((x, y, z)))
        parts.append(sweep_vf(rail, rect2(0.03, 0.03)))
        for y in (-8.6, -7.6, -6.6, -5.7):
            x = side * (Wcan_(y) * 0.86 - 0.03)
            z = canopy_z(x, y) - 0.085
            parts.append(box_vf((x, y, z), (0.03, 0.05, 0.03)))           # lock hooks
    bow = []
    for k in range(17):
        v = -1 + 2 * k / 16
        x = v * Wcan_(-5.25) * 0.84
        bow.append(V((x, -5.25, canopy_z(x, -5.25) - 0.05)))
    parts.append(sweep_vf(bow, rect2(0.05, 0.035)))
    mk('Canopy_InnerFrame', merge_vf(*parts), 'CockpitDark', 'Cockpit', frame, bev=(0.004, 1, 30))
    hinge = []
    for x in (-0.22, 0.22):
        hinge.append(cyl_vf((x, CAN_HINGE.y, CAN_HINGE.z), 0.032, 0.06, 'X', 12))
        hinge.append(box_between((x - 0.025, CAN_HINGE.y - 0.12, CAN_HINGE.z - 0.02), (x + 0.025, CAN_HINGE.y, CAN_HINGE.z + 0.03)))
    mk('Canopy_Hinge', merge_vf(*hinge), 'Steel', 'Cockpit', frame, bev=(0.003, 1, 30))
    rig.motion(frame, 'rotate', 'X', -48, 'Canopy', (0, 1), 'canopy',
               'one-piece canopy, rear-hinged: opens up 48 deg (front rises)')
    # fixed hinge brackets on the body
    fx = []
    for x in (-0.22, 0.22):
        for dx in (-0.045, 0.045):
            fx.append(box_between((x + dx - 0.008, CAN_HINGE.y - 0.04, CAN_HINGE.z - 0.16),
                                  (x + dx + 0.008, CAN_HINGE.y + 0.05, CAN_HINGE.z + 0.02)))
        fx.append(cyl_vf((x, CAN_HINGE.y, CAN_HINGE.z), 0.012, 0.13, 'X', 8))
    mk('Canopy_HingeBrackets', merge_vf(*fx), 'Steel', 'Cockpit')
    return frame


def build_seat():
    s = SRP
    rot = Matrix.Translation(s) @ Matrix.Rotation(BACK, 4, 'X') @ Matrix.Translation(-s)

    def back(vf):
        return xform_vf(vf, rot)
    # seat bucket + pan + survival kit
    bucket = [box_between((-0.25, s.y - 0.42, s.z - 0.13), (0.25, s.y + 0.06, s.z - 0.02)),
              box_between((-0.26, s.y - 0.44, s.z - 0.02), (-0.22, s.y + 0.06, s.z + 0.10)),
              box_between((0.22, s.y - 0.44, s.z - 0.02), (0.26, s.y + 0.06, s.z + 0.10))]
    mk('Seat_Bucket', merge_vf(*bucket), 'CockpitDark', 'Cockpit', bev=(0.006, 1, 30))
    kit = box_between((-0.21, s.y - 0.40, s.z - 0.02), (0.21, s.y + 0.02, s.z + 0.06))
    mk('Seat_Cushion', kit, 'Seat', 'Cockpit', bev=(0.02, 2, 30))
    # back cushion, side beams, headbox
    bc = back(box_between((-0.20, s.y + 0.02, s.z + 0.08), (0.20, s.y + 0.10, s.z + 0.66)))
    mk('Seat_BackCushion', bc, 'Seat', 'Cockpit', bev=(0.02, 2, 30))
    beams = [back(box_between((x - 0.03, s.y + 0.10, s.z - 0.10), (x + 0.03, s.y + 0.20, s.z + 0.95))) for x in (-0.23, 0.23)]
    beams.append(back(box_between((-0.24, s.y + 0.095, s.z + 0.10), (0.24, s.y + 0.19, s.z + 0.70))))
    mk('Seat_Frame', merge_vf(*beams), 'CockpitDark', 'Cockpit', bev=(0.006, 1, 30))
    head = back(box_between((-0.18, s.y + 0.04, s.z + 0.72), (0.18, s.y + 0.20, s.z + 0.97)))
    mk('Seat_Headbox', head, 'Black', 'Cockpit', bev=(0.02, 2, 30))
    pads = back(box_between((-0.11, s.y + 0.015, s.z + 0.74), (0.11, s.y + 0.045, s.z + 0.90)))
    mk('Seat_Headrest', pads, 'Seat', 'Cockpit', bev=(0.012, 2, 30))
    # catapult rails + drogue gun + top warning triangle
    rails = [back(box_between((x - 0.012, s.y + 0.185, s.z - 0.12), (x + 0.012, s.y + 0.225, s.z + 1.02))) for x in (-0.14, 0.14)]
    rails.append(back(cyl_between((0.10, s.y + 0.25, s.z + 0.35), (0.10, s.y + 0.25, s.z + 0.95), 0.03, 12)))
    mk('Seat_Rails', merge_vf(*rails), 'Steel', 'Cockpit', bev=(0.003, 1, 30))
    tri = back(prism([V((-0.05, s.y + 0.042, s.z + 0.93)), V((0.05, s.y + 0.042, s.z + 0.93)),
                      V((0.0, s.y + 0.042, s.z + 1.01))], (0, -0.006, 0)))
    mk('Seat_EjectWarning', tri, 'Red', 'Cockpit')
    # ejection handle (yellow/black loop between the knees) + harness
    loop = [V((x, s.y - 0.30, s.z + 0.10 + 0.045 * (1 - (x / 0.07) ** 2))) for x in cosspace(-0.07, 0.07, 10)]
    h = tube_vf(loop, 0.009, 8)
    mk('Seat_EjectHandle', h, 'Yellow', 'Cockpit')
    stripes = [cyl_between((x - 0.008, s.y - 0.30, s.z + 0.10 + 0.045 * (1 - (x / 0.07) ** 2)),
                           (x + 0.008, s.y - 0.30, s.z + 0.10 + 0.045 * (1 - (x / 0.07) ** 2)), 0.0095, 8)
               for x in (-0.045, 0.0, 0.045)]
    mk('Seat_EjectHandleStripes', merge_vf(*stripes), 'Black', 'Cockpit')
    straps = []
    for sx in (-1, 1):
        sh = rot @ V((sx * 0.10, s.y + 0.08, s.z + 0.66))
        hip = V((sx * 0.13, s.y - 0.06, s.z + 0.09))
        mid = (sh + hip) / 2 + V((0, -0.11, 0.0))
        straps.append(sweep_vf([sh + V((0, 0.02, 0.06)), sh, mid, hip], rect2(0.045, 0.006)))
        straps.append(sweep_vf([V((sx * 0.22, s.y - 0.02, s.z + 0.08)), V((sx * 0.035, s.y - 0.13, s.z + 0.11))],
                               rect2(0.045, 0.006)))
    mk('Seat_Harness', merge_vf(*straps), 'Harness', 'Cockpit')
    buckle = box_vf((0, s.y - 0.13, s.z + 0.12), (0.08, 0.015, 0.07))
    mk('Seat_Buckle', buckle, 'Alu', 'Cockpit', bev=(0.004, 1, 30))
    # oxygen / comms hose from the seat kit to the left console
    hose = [V((0.18, s.y - 0.10, s.z + 0.02)), V((0.25, s.y - 0.20, s.z + 0.03)), V((0.31, s.y - 0.38, s.z + 0.10)),
            V((0.36, s.y - 0.30, s.z + 0.20))]
    mk('Seat_OxygenHose', tube_vf(hose, 0.013, 10), 'Black', 'Cockpit')
    # leg garters + seat base
    mk('Seat_Base', box_between((-0.22, s.y - 0.30, 2.05), (0.22, s.y + 0.18, s.z - 0.13)), 'CockpitDark', 'Cockpit',
       bev=(0.006, 1, 30))
    seat = rig.seat('Seat_Pilot', (0.0, s.y - 0.12, s.z + 0.07), 'pilot', driver=True, enter='Board_Left',
                    exit='Exit_Left', camera='Eye_Pilot', description='single ejection seat; pilot flies the aircraft')
    return seat


def build_panel():
    # main instrument panel + glareshield + HUD
    pnl = [box_between((-0.45, -8.05, 2.30), (0.45, -7.58, 2.70)),
           box_between((-0.40, -8.35, 2.40), (0.40, -8.05, 2.66))]
    mk('Cockpit_Panel', merge_vf(*pnl), 'Cockpit', 'Cockpit', bev=(0.008, 1, 30))
    gs = tilt(box_between((-0.43, -8.32, 2.69), (0.43, -7.53, 2.735)), V((0, -7.53, 2.71)), -6)
    mk('Cockpit_Glareshield', gs, 'CockpitDark', 'Cockpit', bev=(0.01, 2, 30))
    screen(V((0.0, -7.575, 2.54)), 0.78, 0.22, 14, 'pano', None)
    screen(V((-0.36, -7.57, 2.37)), 0.10, 0.06, 10, 'warn', None)
    screen(V((0.35, -7.57, 2.37)), 0.08, 0.08, 10, 'standby', None)
    # HUD: projector on the glareshield + combiner glass + symbology
    mk('Cockpit_HUDBase', box_between((-0.13, -7.95, 2.73), (0.13, -7.62, 2.83)), 'CockpitDark', 'Cockpit',
       bev=(0.008, 1, 30))
    comb = tilt(box_between((-0.12, -7.66, 2.83), (0.12, -7.648, 3.05)), V((0, -7.66, 2.83)), 32)
    mk('Cockpit_HUDGlass', comb, 'GlassClear', 'Cockpit')
    fr = [tilt(box_between((x - 0.007, -7.668, 2.83), (x + 0.007, -7.64, 3.06)), V((0, -7.66, 2.83)), 32) for x in (-0.126, 0.126)]
    fr.append(tilt(box_between((-0.133, -7.668, 3.05), (0.133, -7.64, 3.065)), V((0, -7.66, 2.83)), 32))
    mk('Cockpit_HUDFrame', merge_vf(*fr), 'CockpitDark', 'Cockpit')
    sym = []
    for k, z in enumerate((2.90, 2.94, 2.98)):
        w = 0.05 if k != 1 else 0.07
        sym.append(tilt(box_between((-w, -7.6615, z), (w, -7.6595, z + 0.0035)), V((0, -7.66, 2.83)), 32))
    sym.append(tilt(cyl_vf((0, -7.6605, 2.945), 0.012, 0.002, 'Y', 12), V((0, -7.66, 2.83)), 32))
    mk('Cockpit_HUDSymbology', merge_vf(*sym), 'ScreenGreen', 'Cockpit')
    # forward avionics deck (under the canopy front) with standby compass + sensor head
    deck = box_between((-0.32, -9.10, 2.34), (0.32, -8.24, 2.50))
    mk('Cockpit_FwdDeck', deck, 'CockpitDark', 'Cockpit', bev=(0.01, 1, 30))
    mk('Cockpit_Compass', cyl_vf((0.18, -8.55, 2.53), 0.035, 0.05, 'Z', 16), 'Black', 'Cockpit', bev=(0.004, 1, 30))
    # pedals + heel plate
    ped = []
    for x in (-0.16, 0.16):
        ped.append(tilt(box_between((x - 0.06, -8.02, 2.12), (x + 0.06, -7.99, 2.32)), V((x, -8.0, 2.12)), 15))
        ped.append(cyl_between((x, -8.02, 2.30), (x, -8.25, 2.36), 0.012, 8))
    mk('Cockpit_Pedals', merge_vf(*ped), 'Alu', 'Cockpit', bev=(0.003, 1, 30))
    mk('Cockpit_HeelPlate', box_between((-0.30, -7.98, 2.05), (0.30, -7.55, 2.07)), 'Hardware', 'Cockpit')


def build_consoles():
    for side in (1, -1):
        x0, x1 = side * 0.29, side * 0.465
        lo, hi = min(x0, x1), max(x0, x1)
        con = [box_between((lo, -7.45, 2.05), (hi, -5.55, 2.40))]
        mk('Cockpit_Console_' + ('L' if side > 0 else 'R'), merge_vf(*con), 'Cockpit', 'Cockpit', bev=(0.006, 1, 30))
        top = box_between((lo + 0.008, -7.42, 2.40), (hi - 0.008, -5.58, 2.408))
        mk('Cockpit_ConsoleTop_' + ('L' if side > 0 else 'R'), top, 'CockpitDark', 'Cockpit')
        sw, gd = switches((lo + 0.03, -7.30, 2.408), 5, 0.028, 0, guard=(side < 0))
        mk('Cockpit_Switches_' + ('L' if side > 0 else 'R'), sw, 'Alu', 'Cockpit')
        if gd:
            mk('Cockpit_SwitchGuards_R', gd, 'Red', 'Cockpit')
        mk('Cockpit_Knobs_' + ('L' if side > 0 else 'R'), knobs((lo + 0.035, -5.85, 2.408), 4, 0.035), 'Black',
           'Cockpit', bev=(0.002, 1, 30))
        screen(V((side * 0.38, -6.0, 2.41)), 0.12, 0.08, 90, 'standby', None)
        # side wall: wiring loom + map pocket + circuit-breaker panel
        wall = side * 0.468
        loom = [V((wall - side * 0.02, y, 2.55 + 0.02 * sin(y * 6))) for y in cosspace(-8.2, -5.6, 14)]
        mk('Cockpit_Loom_' + ('L' if side > 0 else 'R'), tube_vf(loom, 0.012, 8), 'CableBlack', 'Cockpit')
        cb = []
        for i in range(6):
            for j in range(3):
                cb.append(cyl_vf((wall - side * 0.005, -6.9 + i * 0.03, 2.47 + j * 0.03), 0.007, 0.012, 'X', 8))
        mk('Cockpit_Breakers_' + ('L' if side > 0 else 'R'), merge_vf(*cb), 'Black', 'Cockpit')
        mk('Cockpit_BreakerPanel_' + ('L' if side > 0 else 'R'),
           box_between((wall - side * 0.0 - 0.004, -6.93, 2.44), (wall + 0.004, -6.70, 2.55)), 'CockpitDark', 'Cockpit')
    # throttle (left) + side-stick (right) with armrest
    thr = [box_between((0.33, -6.85, 2.408), (0.40, -6.62, 2.43)),
           tilt(box_between((0.345, -6.80, 2.43), (0.385, -6.72, 2.56)), V((0.365, -6.76, 2.43)), -12),
           tilt(box_between((0.335, -6.83, 2.54), (0.395, -6.70, 2.60)), V((0.365, -6.76, 2.43)), -12)]
    mk('Cockpit_Throttle', merge_vf(*thr), 'Black', 'Cockpit', bev=(0.008, 2, 30))
    stk = [cyl_vf((-0.36, -6.74, 2.415), 0.035, 0.02, 'Z', 14),
           cyl_between((-0.36, -6.74, 2.42), (-0.36, -6.75, 2.52), 0.018, 12),
           tilt(box_between((-0.385, -6.78, 2.50), (-0.335, -6.72, 2.60)), V((-0.36, -6.75, 2.5)), -10)]
    mk('Cockpit_SideStick', merge_vf(*stk), 'Black', 'Cockpit', bev=(0.006, 2, 30))
    mk('Cockpit_StickTrigger', box_between((-0.366, -6.79, 2.54), (-0.354, -6.775, 2.565)), 'Red', 'Cockpit')
    mk('Cockpit_Armrest', box_between((-0.45, -6.55, 2.40), (-0.30, -6.05, 2.46)), 'Seat', 'Cockpit', bev=(0.015, 2, 30))
    # emergency: canopy jettison T-handle (yellow/black), emergency gear handle, master caution
    mk('Cockpit_CanopyJettison', merge_vf(cyl_between((0.30, -7.59, 2.62), (0.30, -7.52, 2.62), 0.008, 8),
                                           box_vf((0.30, -7.51, 2.62), (0.06, 0.016, 0.016))), 'Yellow', 'Cockpit')
    mk('Cockpit_EmergencyGear', merge_vf(cyl_between((-0.42, -7.59, 2.48), (-0.42, -7.53, 2.48), 0.007, 8),
                                         cyl_vf((-0.42, -7.525, 2.48), 0.02, 0.014, 'Y', 12)), 'Red', 'Cockpit')
    mc = [cyl_vf((x, -7.585, 2.665), 0.014, 0.012, 'Y', 12) for x in (-0.20, 0.20)]
    mk('Cockpit_MasterCaution', merge_vf(*mc), 'ScreenAmber', 'Cockpit')
    # cockpit flood lights (small spot heads) + rear equipment deck with oxygen bottles + avionics
    fl = [cyl_between((x, -5.9, 2.62), (x, -5.95, 2.58), 0.012, 8) for x in (-0.40, 0.40)]
    mk('Cockpit_FloodLights', merge_vf(*fl), 'LED', 'Cockpit')
    deck = box_between((-0.46, -5.95, 2.05), (0.46, -5.36, 2.60))
    mk('Cockpit_RearDeck', deck, 'CockpitDark', 'Cockpit', bev=(0.01, 1, 30))
    ox = [cyl_between((x, -5.55, 2.595), (x, -5.55, 2.80), 0.06, 16) for x in (-0.30, 0.30)]
    mk('Cockpit_OxygenBottles', merge_vf(*ox), 'Primer', 'Cockpit', bev=(0.01, 2, 30))
    av = [box_between((-0.18, -5.75, 2.60), (0.18, -5.40, 2.78))]
    mk('Cockpit_AvionicsRack', merge_vf(*av), 'Hardware', 'Cockpit', bev=(0.006, 1, 30))
    fins = [box_between((-0.16 + 0.02 * k, -5.76, 2.62), (-0.152 + 0.02 * k, -5.74, 2.76)) for k in range(17)]
    mk('Cockpit_AvionicsFins', merge_vf(*fins), 'Alu', 'Cockpit')
    rig.light('Light_CockpitFlood', (0.0, -6.0, 2.70), 'point', (1.0, 0.75, 0.55), 2.5, 'interior',
              brightness=0.6)


def build():
    build_canopy()
    build_seat()
    build_panel()
    build_consoles()
    rig.point('Board_Left', (1.6, -6.6, 0.0), 'prompt', action='board / exit the cockpit (ladder side)')
    rig.point('Exit_Left', (2.2, -6.6, 0.0), 'exit', note='where the pilot is placed after leaving the seat on the ground')
    rig.point('Eye_Pilot', (0.0, -6.45, 3.00), 'camera', note='first-person cockpit camera')
