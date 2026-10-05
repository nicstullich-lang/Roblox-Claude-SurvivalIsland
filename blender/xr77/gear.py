"""XR-77 landing gear: twin-wheel steerable nose gear (retracts forward), two single-wheel main gears (retract
forward into wells beside the weapon bays), wheel-well doors (open while the gear is down, close after retraction),
well interiors (frames, hydraulic lines, uplocks), taxi / landing lights.

Rest pose = parked: gear down, gear doors open. Channel GearUp 0 -> 1 retracts everything.
"""
from .lib import *
from common import rig
from . import airframe as AF


def hinge(ob, pivot, typ, axis, opn, channel, stage, desc, kind='part', **kw):
    set_origin(ob, pivot)
    rig.motion(ob, typ, axis, opn, channel, stage, kind, desc, **kw)


def rest_open(ob, pivot, axis, deg):
    """put the pivot on the hinge and swing the door geometry open (the parked pose is the rest pose)."""
    set_origin(ob, pivot)
    ob.data.transform(Matrix.Rotation(radians(deg), 4, axis))


def wheel_vf(c, r, w, rim_r):
    """tyre + rim + hub around the X axis at centre c."""
    tyre = lathe_vf([(rim_r, -w / 2), (r - 0.07, -w / 2), (r - 0.02, -w / 2 + 0.025), (r, -w / 2 + 0.06),
                     (r, w / 2 - 0.06), (r - 0.02, w / 2 - 0.025), (r - 0.07, w / 2), (rim_r, w / 2), (rim_r, -w / 2)],
                    40, cap0=False, cap1=False)
    rim = lathe_vf([(rim_r - 0.012, -w / 2 + 0.005), (rim_r + 0.012, -w / 2 + 0.005), (rim_r + 0.012, -w / 2 + 0.02),
                    (rim_r, -w / 2 + 0.03), (rim_r, w / 2 - 0.03), (rim_r + 0.012, w / 2 - 0.02),
                    (rim_r + 0.012, w / 2 - 0.005), (rim_r - 0.012, w / 2 - 0.005), (rim_r - 0.012, -w / 2 + 0.005)],
                   40, cap0=False, cap1=False)
    disc = lathe_vf([(0.0, w / 2 - 0.05), (rim_r - 0.01, w / 2 - 0.06), (rim_r - 0.01, w / 2 - 0.04), (0.09, w / 2 - 0.02),
                     (0.07, w / 2 - 0.0), (0.0, w / 2 - 0.0)], 32)
    hub = lathe_vf([(0.0, -w / 2 + 0.01), (0.08, -w / 2 + 0.01), (0.08, w / 2 - 0.03), (0.0, w / 2 - 0.03)], 20)
    nuts = [orient(cyl_vf((0.115 * cos(a), 0.115 * sin(a), w / 2 - 0.035), 0.012, 0.022, 'Z', 6), (0, 0, 0), 'Z')
            for a in [2 * pi * k / 8 for k in range(8)]]
    grooves = [lathe_vf([(r + 0.001, z - 0.006), (r + 0.001, z + 0.006), (r - 0.008, z + 0.006), (r - 0.008, z - 0.006),
                         (r + 0.001, z - 0.006)], 40, cap0=False, cap1=False) for z in (-w * 0.18, w * 0.18)]
    put = lambda vf: orient(vf, c, 'X')
    return put(tyre), merge_vf(put(rim), put(disc), put(hub)), merge_vf(*[put(n) for n in nuts]), \
        merge_vf(*[put(g) for g in grooves])


def strut_parts(top, bot, r_out, r_pis, oleo_z, front=-1):
    """oleo strut from top to axle height: outer cylinder, chrome piston, torque links, brake hose."""
    outer = cyl_between(top, V((top.x, top.y, oleo_z)), r_out, 16)
    collar = cyl_between(V((top.x, top.y, oleo_z + 0.05)), V((top.x, top.y, oleo_z - 0.02)), r_out + 0.012, 16)
    piston = cyl_between(V((top.x, top.y, oleo_z)), V((bot.x, bot.y, bot.z + 0.10)), r_pis, 14)
    tl = []
    zt, zb = oleo_z + 0.02, bot.z + 0.16
    zm = (zt + zb) / 2
    yk = top.y + front * 0.14
    for (za, zb_) in ((zt, zm), (zm, zb)):
        p0, p1 = V((top.x, top.y + front * (r_out + 0.01), za)), V((top.x, yk, zm))
        if za != zt:
            p0, p1 = V((top.x, yk, zm)), V((top.x, top.y + front * (r_pis + 0.01), zb_))
        tl.append(sweep_vf([p0, p1], rect2(0.035, 0.018)))
    tl.append(cyl_vf(V((top.x, yk, zm)), 0.018, 0.05, 'X', 10))
    return outer, collar, piston, merge_vf(*tl)


def build_main(s):
    S_ = 'L' if s > 0 else 'R'
    g = MAIN_GEAR
    xl, xw, y, zt, r, w = s * g['x_leg'], s * g['x_wheel'], g['y'], g['z_trunnion'], g['r'], g['w']
    top = V((xl, y, zt))
    axle = V((xw, y + 0.06, r))
    outer, collar, piston, links = strut_parts(top, V((xl, y + 0.06, r)), 0.075, 0.055, 0.95)
    trn = cyl_vf(top, 0.06, 0.30, 'X', 16)
    fork = merge_vf(box_between((xl - 0.07, y - 0.02, r - 0.08), (xl + 0.07, y + 0.14, r + 0.12)),
                    cyl_between(V((xl, y + 0.06, r)), axle - V((s * g['w'] / 2, 0, 0)), 0.045, 14))
    leg = mk('Gear_Main_' + S_, merge_vf(outer, trn, fork), 'GearWhite', 'Gear', sharp=35)
    mk('Gear_Main_Collar_' + S_, collar, 'GearWhite', 'Gear', leg, bev=(0.004, 1, 30))
    mk('Gear_Main_Piston_' + S_, piston, 'Chrome', 'Gear', leg)
    mk('Gear_Main_TorqueLinks_' + S_, links, 'Steel', 'Gear', leg, bev=(0.003, 1, 30))
    hose = tube_vf([top + V((s * 0.08, 0.05, -0.10)), V((xl + s * 0.085, y + 0.05, 1.2)), V((xl + s * 0.07, y + 0.07, 0.75)),
                    V((xl + s * 0.06, y + 0.10, r + 0.12)), axle + V((-s * 0.10, 0.09, 0.08))], 0.011, 8)
    mk('Gear_Main_BrakeHose_' + S_, hose, 'Black', 'Gear', leg)
    # brake (fixed to the leg) + wheel (spins)
    brake = merge_vf(cyl_vf(axle - V((s * 0.04, 0, 0)), 0.20, 0.10, 'X', 24),
                     box_between(axle + V((-s * 0.11, -0.05, 0.10)), axle + V((s * 0.02, 0.05, 0.20))))
    mk('Gear_Main_Brake_' + S_, brake, 'Steel', 'Gear', leg, bev=(0.004, 1, 30))
    tyre, rim, nuts, grooves = wheel_vf(axle, r, w, 0.255)
    if s < 0:                                    # hub face outboard on the right wheel too
        tyre, rim, nuts, grooves = [mirror_about_x(v, axle.x) for v in (tyre, rim, nuts, grooves)]
    wh = mk('Gear_MainWheel_' + S_, tyre, 'Tire', 'Gear', leg, sharp=50)
    mk('Gear_MainWheel_Rim_' + S_, rim, 'Wheel', 'Gear', wh, sharp=40)
    mk('Gear_MainWheel_Nuts_' + S_, nuts, 'Steel', 'Gear', wh)
    mk('Gear_MainWheel_Grooves_' + S_, grooves, 'Rubber', 'Gear', wh, smooth=False)
    hinge(leg, top, 'rotate', 'X', g['retract'], 'GearUp', (0.10, 0.80), 'main gear: retracts forward into its well')
    hinge(wh, axle, 'wheel', 'X', None, None, (0, 1), 'main wheel (rolls on the ground)', kind='wheel')
    rig.wheel(wh, r, w, steer=False, driven=False, suspension_up_m=0.28, suspension_down_m=0.05, brakes=True)
    # well door (open at rest) + well interior
    d = AF.DOORS['Gear_MainDoor_' + S_]
    hp = AF.hinge_line((s * 1.583, 1.15), (s * 1.583, 3.75), 'bottom')[0]
    rest_open(d, hp, 'Y', -95 * s)
    door_hinges('Gear_MainDoor_Hinges_' + S_, hp, (1.40, 2.45, 3.50), s, d)
    rig.motion(d, 'rotate', 'Y', 95 * s, 'GearUp', (0.80, 1.0), 'door',
               'main gear door: open while the gear is down, closes after the gear is up')
    ribs = []
    for yy in (1.45, 2.05, 2.65, 3.25):
        ribs.append(box_between((s * 1.10, yy - 0.02, 2.43), (s * 1.58, yy + 0.02, 2.49)))
    mk('Gear_MainWell_Frames_' + S_, merge_vf(*ribs), 'GearWhite', 'Gear')
    lines = [tube_vf([V((s * 1.14, 1.2, 2.44)), V((s * 1.14, 3.2, 2.44)), V((s * 1.17, 3.6, 2.2))], 0.010, 8),
             tube_vf([V((s * 1.16, 1.2, 2.46)), V((s * 1.16, 3.3, 2.46)), V((s * 1.20, 3.62, 2.15))], 0.008, 8)]
    mk('Gear_MainWell_Hydraulics_' + S_, merge_vf(*lines), 'Steel', 'Gear')
    up = merge_vf(box_between((s * 1.32, 1.95, 2.44), (s * 1.48, 2.10, 2.49)) if s > 0 else
                  box_between((-1.48, 1.95, 2.44), (-1.32, 2.10, 2.49)))
    mk('Gear_MainWell_Uplock_' + S_, up, 'Steel', 'Gear')


def build_nose():
    g = NOSE_GEAR
    x, y, zt, r, w = g['x'], g['y'], g['z_trunnion'], g['r'], g['w']
    top = V((x, y, zt))
    outer, collar, piston, links = strut_parts(top, V((x, y + 0.10, r)), 0.065, 0.048, 0.95, front=1)
    trn = cyl_vf(top, 0.05, 0.30, 'X', 14)
    leg = mk('Gear_Nose', merge_vf(outer, trn), 'GearWhite', 'Gear', sharp=35)
    mk('Gear_Nose_Collar', collar, 'GearWhite', 'Gear', leg, bev=(0.004, 1, 30))
    lights = merge_vf(box_between((x - 0.09, y - 0.13, 1.10), (x + 0.09, y - 0.06, 1.22)))
    mk('Gear_Nose_LightHousing', lights, 'GearWhite', 'Gear', leg, bev=(0.006, 1, 30))
    lens = merge_vf(cyl_vf((x - 0.045, y - 0.132, 1.16), 0.035, 0.008, 'Y', 16), cyl_vf((x + 0.045, y - 0.132, 1.16), 0.035, 0.008, 'Y', 16))
    mk('Gear_Nose_Lights', lens, 'LED', 'Gear', leg)
    hinge(leg, top, 'rotate', 'X', g['retract'], 'GearUp', (0.05, 0.70), 'nose gear: retracts forward')
    rig.light('Light_Landing', (x - 0.045, y - 0.14, 1.16), 'spot', (1.0, 0.97, 0.9), 60.0, 'landing',
              direction=(0, -1, -0.08), angle_deg=24, brightness=5.0, attach=leg, neon_materials=['LED'])
    rig.light('Light_Taxi', (x + 0.045, y - 0.14, 1.16), 'spot', (1.0, 0.97, 0.9), 30.0, 'taxi',
              direction=(0, -1, -0.15), angle_deg=60, brightness=3.0, attach=leg)
    # steering part (below the collar): piston, links, fork, axle, twin wheels
    steer_pivot = V((x, y, 0.95))
    fork = merge_vf(box_between((x - 0.04, y + 0.02, r - 0.05), (x + 0.04, y + 0.16, r + 0.10)),
                    cyl_between(V((x - g['track'] - 0.04, y + 0.10, r)), V((x + g['track'] + 0.04, y + 0.10, r)), 0.035, 14))
    st = mk('Gear_NoseSteer', merge_vf(piston, fork), 'Chrome', 'Gear', leg, mat_idx=None)
    mk('Gear_NoseSteer_Links', links, 'Steel', 'Gear', st, bev=(0.003, 1, 30))
    hinge(st, steer_pivot, 'steer', 'Z', None, None, (0, 1), 'nose wheel steering (taxi)', min=-60, max=60, speed=90)
    wheels = []
    rims, nuts, grooves = [], [], []
    for sx in (-1, 1):
        c = V((x + sx * (g['track'] + 0.01), y + 0.10, r))
        t_, rm, n_, gr = wheel_vf(c, r, w, 0.17)
        if sx < 0:
            t_, rm, n_, gr = [mirror_about_x(v, x) for v in (t_, rm, n_, gr)]
        wheels.append(t_)
        rims.append(rm)
        nuts.append(n_)
        grooves.append(gr)
    wh = mk('Gear_NoseWheels', merge_vf(*wheels), 'Tire', 'Gear', st, sharp=50)
    mk('Gear_NoseWheels_Rims', merge_vf(*rims), 'Wheel', 'Gear', wh, sharp=40)
    mk('Gear_NoseWheels_Nuts', merge_vf(*nuts), 'Steel', 'Gear', wh)
    mk('Gear_NoseWheels_Grooves', merge_vf(*grooves), 'Rubber', 'Gear', wh, smooth=False)
    hinge(wh, V((x, y + 0.10, r)), 'wheel', 'X', None, None, (0, 1), 'nose wheels (roll)', kind='wheel')
    rig.wheel(wh, r, w, steer=True, driven=False, suspension_up_m=0.22, suspension_down_m=0.05, steer_max_deg=60,
              twin=True, track_m=2 * g['track'])
    # nose well doors (open at rest)
    for nm, hx, sg in (('Gear_NoseDoor_L', 0.043, 1), ('Gear_NoseDoor_R', -0.483, -1)):
        d = AF.DOORS[nm]
        hp = AF.hinge_line((hx, -10.30), (hx, -8.25), 'bottom')[0]
        rest_open(d, hp, 'Y', -95 * sg)
        door_hinges(nm + '_Hinges', hp, (-10.05, -9.27, -8.50), sg, d)
        rig.motion(d, 'rotate', 'Y', 95 * sg, 'GearUp', (0.70, 0.95), 'door', 'nose gear door: closes after retraction')
    ribs = [box_between((-0.48, yy - 0.02, 2.262), (0.04, yy + 0.02, 2.28)) for yy in (-9.45, -8.65)]
    mk('Gear_NoseWell_Frames', merge_vf(*ribs), 'GearWhite', 'Gear')


def door_hinges(name, hp, ys, s, door=None):
    """fixed hinge brackets + pins along a door hinge line, and hinge arms on the (open, rest-pose) door."""
    parts, arms = [], []
    for y in ys:
        zt = body_bot(abs(hp.x), y)
        parts.append(cyl_vf((hp.x, y, hp.z), 0.013, 0.09, 'Y', 10))
        parts.append(box_between((hp.x + s * 0.004, y - 0.02, hp.z - 0.006), (hp.x + s * 0.03, y + 0.02, zt + 0.03)))
        arms.append(box_between((hp.x - s * 0.004, y + 0.05, hp.z - 0.010), (hp.x - s * 0.020, y + 0.08, hp.z - 0.08)))
    mk(name, merge_vf(*parts), 'Steel', 'Gear', bev=(0.002, 1, 30))
    if door is not None:
        mk(name + '_Arms', merge_vf(*arms), 'Steel', 'Gear', door)


def mirror_about_x(vf, x0):
    vv, ff = vf
    return [V((2 * x0 - v.x, v.y, v.z)) for v in vv], [tuple(reversed(f)) for f in ff]


def build():
    for s in (1, -1):
        build_main(s)
    build_nose()
