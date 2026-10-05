"""Pose engine for rig-tagged models: turns channel values / inputs into transforms of the moving groups,
so renders, checks and the Blender timeline all use exactly the motions written into the rig data.

    apply_pose('vtol')                       # a pose stored with rig.pose(...)
    apply_state({'GearUp': 1}, {'Turret_Yaw': 90})
    key_showcase([(1, 'rest'), (60, 'vtol'), ...])   # keyframes for scrubbing in Blender
"""
import bpy
from math import radians
from mathutils import Vector, Quaternion
from .rig import get_json

AX = {'X': Vector((1, 0, 0)), 'Y': Vector((0, 1, 0)), 'Z': Vector((0, 0, 1))}


def axis_vec(a):
    return AX[a].copy() if isinstance(a, str) else Vector(a).normalized()


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def groups():
    return [o for o in bpy.context.scene.objects if o.get('rig_motion')]


def progress(m, channels):
    v = channels.get(m.get('channel'), 0.0) if m.get('channel') else 0.0
    s0, s1 = m.get('stage') or (0.0, 1.0)
    return smooth((v - s0) / max(1e-6, s1 - s0))


def transform_of(o, channels, inputs):
    """(rotation quaternion, location offset) of a group for the given state."""
    m = get_json(o, 'rig_motion')
    t = m['type']
    q, d = Quaternion(), Vector((0, 0, 0))
    if not m.get('axis'):
        return q, d
    ax = axis_vec(m['axis'])
    if t == 'rotate':
        q = Quaternion(ax, radians(m['open'] * progress(m, channels)))
        ctl = m.get('control')
        if ctl and o.name in inputs:
            q = Quaternion(ax, radians(m['open'] * progress(m, channels) + inputs[o.name]))
    elif t == 'translate':
        d = ax * (m['open'] * progress(m, channels))
    elif t in ('aim_yaw', 'aim_pitch', 'steer', 'control', 'spin', 'wheel'):
        a = inputs.get(o.name, 0.0)
        q = Quaternion(ax, radians(a))
    return q, d


def apply_state(channels=None, inputs=None):
    channels, inputs = channels or {}, inputs or {}
    for o in groups():
        q, d = transform_of(o, channels, inputs)
        rest = Vector(o.get('rig_rest_loc', list(o.location)))
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = q
        o.location = rest + d
    bpy.context.view_layer.update()


def pose_def(name):
    ps = get_json(bpy.context.scene, 'rig_poses', {})
    if name == 'rest':
        return ps.get('rest', dict(channels={}, inputs={}, ground=True))
    return ps[name]


def apply_pose(name):
    p = pose_def(name)
    apply_state(p.get('channels'), p.get('inputs'))


def key_showcase(sequence):
    """sequence of (frame, pose name) - inserts keys for every group so the timeline plays the poses."""
    sc = bpy.context.scene
    sc.frame_start = sequence[0][0]
    sc.frame_end = sequence[-1][0]
    for frame, name in sequence:
        apply_pose(name)
        for o in groups():
            o.keyframe_insert('location', frame=frame)
            o.keyframe_insert('rotation_quaternion', frame=frame)
    apply_pose('rest')
    sc.frame_set(sequence[0][0])
