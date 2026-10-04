"""TX-6 Bastion - animation-ready pivots + a keyed showcase timeline.

Frame 1    rest (everything stowed, doors shut)
Frame 1-90   COMBAT deploy: windshield armour + window shutters up, missile hatches open, lifts rise, pods
             elevate, sensor mast raises / extends / spins, turret traverses + elevates, barrels spin
Frame 90-140 ACCESS: spare carrier swings, rear door, side doors, equipment lockers, drone tray, fuel door
Frame 140-180 hold (barrels + radar keep spinning)

All moving parts have identity rotation at rest, so each motion is one local-axis rotation or translation.
"""
import bpy
from math import radians
from mathutils import Vector

AX = {'X': 0, 'Y': 1, 'Z': 2}

# name: (kind, axis, amount, start_frame, end_frame)
MOTIONS = {
    # ---- combat
    'Deploy_WindshieldShield': ('rot', 'X', -113.6, 1, 30),
    'Deploy_Shutter_FL': ('rot', 'Y', 171, 5, 35), 'Deploy_Shutter_RL': ('rot', 'Y', 171, 8, 38),
    'Deploy_Shutter_FR': ('rot', 'Y', -171, 5, 35), 'Deploy_Shutter_RR': ('rot', 'Y', -171, 8, 38),
    'Missile_Hatch_L': ('rot', 'Y', 120, 10, 35), 'Missile_Hatch_R': ('rot', 'Y', -120, 10, 35),
    'Missile_Lift_L': ('loc', 'Z', 0.46, 35, 60), 'Missile_Lift_R': ('loc', 'Z', 0.46, 35, 60),
    'Missile_Pod_L': ('rot', 'X', -18, 60, 80), 'Missile_Pod_R': ('rot', 'X', -18, 60, 80),
    'Sensor_Mast': ('rot', 'X', 90, 15, 45),
    'Sensor_MastUpper': ('loc', 'Y', 0.55, 45, 65),
    'Sensor_EOBall': ('rot', 'X', -20, 65, 80),
    'Turret_Rotor': ('rot', 'Z', -35, 30, 70),
    'Turret_Cradle': ('rot', 'X', -15, 50, 75),
    'Searchlight': ('rot', 'Z', 30, 20, 50),
    # ---- access
    'Spare_Carrier': ('rot', 'Z', 95, 90, 110),
    'Door_Rear': ('rot', 'Z', -100, 105, 130),
    'Door_FL': ('rot', 'Z', -70, 95, 120), 'Door_RL': ('rot', 'Z', -70, 98, 123),
    'Door_FR': ('rot', 'Z', 70, 95, 120), 'Door_RR': ('rot', 'Z', 70, 98, 123),
    'Locker_Door_L': ('rot', 'Y', -100, 92, 118), 'Locker_Door_R': ('rot', 'Y', 100, 92, 118),
    'Locker_Tray_L': ('loc', 'X', 0.42, 115, 135),
    'Fuel_Door_L': ('rot', 'Z', -95, 95, 115), 'Utility_Hatch_R': ('rot', 'Z', 95, 95, 115),
}
SPINS = {   # continuous linear spins: (axis, degrees, start, end)
    'Turret_Barrels': ('Y', 1440, 60, 180),
    'Sensor_Head': ('Y', 720, 65, 180),
}
FRAMES = {'rest': 1, 'combat': 85, 'deploy': 140, 'end': 180}


def _key(ob, frame):
    ob.keyframe_insert('location', frame=frame)
    ob.keyframe_insert('rotation_euler', frame=frame)


def build():
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 180
    sc.render.fps = 30
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = 'BEZIER'
    for name, (kind, ax, amt, f0, f1) in MOTIONS.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            print('poses: missing', name)
            continue
        loc0 = ob.location.copy()
        rot0 = ob.rotation_euler.copy()
        _key(ob, f0)
        if kind == 'rot':
            ob.rotation_euler[AX[ax]] = rot0[AX[ax]] + radians(amt)
        else:
            d = Vector((0, 0, 0))
            d[AX[ax]] = amt
            ob.location = loc0 + ob.matrix_basis.to_3x3() @ d
        _key(ob, f1)
        ob.location, ob.rotation_euler = loc0, rot0
        ob['tx_deploy'] = '%s %s %+g between frames %d-%d' % (kind, ax, amt, f0, f1)
    prefs.keyframe_new_interpolation_type = 'LINEAR'
    for name, (ax, deg, f0, f1) in SPINS.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        rot0 = ob.rotation_euler.copy()
        _key(ob, f0)
        ob.rotation_euler[AX[ax]] = rot0[AX[ax]] + radians(deg)
        _key(ob, f1)
        ob.rotation_euler = rot0
    prefs.keyframe_new_interpolation_type = old
    sc.frame_set(1)


def apply(pose):
    sc = bpy.context.scene
    if pose == 'hood':
        sc.frame_set(1)
        h = bpy.data.objects['Hood']
        h.rotation_euler.x = radians(-55)
        return
    sc.frame_set(FRAMES.get(pose, 1))
