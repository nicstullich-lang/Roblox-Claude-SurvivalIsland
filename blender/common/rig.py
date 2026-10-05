"""Rig tagging helpers - the contract between Nic's Blender models and the Roblox code chat.

Schema: "survival-island-model/1" (see docs/MODEL_HANDOFF_STANDARD.md).

Everything is stored INSIDE the .blend as custom properties / marker empties, so the exporter
(blender/export_handoff.py) can write a complete, machine-readable rig JSON + a HANDOFF.md for any model.

Blender conventions every model follows
  * metres, Z up, the model's FRONT points to -Y, the model's LEFT is +X (true sides: _L = +X, _R = -X)
  * every moving part (a "group") is an object whose ORIGIN sits on its real hinge / pivot and whose rotation is
    identity at rest; children move with it. Its motion is described with motion() in BLENDER local axes.
  * markers (seats, points, lights, collision boxes) are EMPTIES in the "RIG_Markers" collection - never exported
    as meshes, only as data.
"""
import bpy, json
from mathutils import Vector, Matrix

SCHEMA = 'survival-island-model/1'
S = 1 / 0.28          # studs per metre (Survival Island scale: 1 stud = 0.28 m)


def rbx(v):
    """Blender metres (x, y, z) -> Roblox studs (-x, z, y)."""
    return [round(-v[0] * S, 4), round(v[2] * S, 4), round(v[1] * S, 4)]


def rbx_dir(v):
    v = Vector(v)
    if v.length > 1e-9:
        v = v.normalized()
    return [round(-v.x, 4), round(v.z, 4), round(v.y, 4)]


def _scene():
    return bpy.context.scene


def _set_json(idb, key, value):
    idb[key] = json.dumps(value)


def get_json(idb, key, default=None):
    raw = idb.get(key)
    return json.loads(raw) if raw else default


def _markers():
    c = bpy.data.collections.get('RIG_Markers')
    if c is None:
        c = bpy.data.collections.new('RIG_Markers')
        _scene().collection.children.link(c)
    return c


def _empty(name, loc, shape='PLAIN_AXES', size=0.12, attach=None, rot=None):
    e = bpy.data.objects.get(name)
    if e is not None and e.type != 'EMPTY':
        raise ValueError('marker name %s is already used by a %s object' % (name, e.type))
    if e is None:
        e = bpy.data.objects.new(name, None)
        _markers().objects.link(e)
    e.empty_display_type = shape
    e.empty_display_size = size
    e.matrix_world = Matrix.Translation(Vector(loc)) @ (rot.to_4x4() if rot is not None else Matrix())
    if attach is not None:
        mw = e.matrix_world.copy()
        e.parent = attach
        e.matrix_parent_inverse = attach.matrix_world.inverted()
        e.matrix_world = mw
    return e


# ------------------------------------------------------------------------------------------ model-level data
def model(name, display, category, description, **extra):
    """category: vehicle | weapon | building | prop | tool | furniture | ..."""
    _set_json(_scene(), 'rig_model', dict(name=name, display=display, category=category, description=description,
                                          **extra))


def channel(name, description, duration_s, rules=None, default=0):
    """a named state (0 = rest / closed, 1 = deployed / open) that drives one or more groups in stages."""
    ch = get_json(_scene(), 'rig_channels', {})
    ch[name] = dict(description=description, duration_s=round(duration_s, 3), rules=rules or [], default=default)
    _set_json(_scene(), 'rig_channels', ch)


def physics(**data):
    """free-form realistic physics data (mass_kg, wheelbase_m, top_speed_kmh, ...) + roblox tuning hints."""
    ph = get_json(_scene(), 'rig_physics', {})
    ph.update(data)
    _set_json(_scene(), 'rig_physics', ph)


def system(name, **data):
    """a gameplay system (weapon, crane, radio, ...) - free-form but should reference groups / points by name."""
    sy = get_json(_scene(), 'rig_systems', {})
    sy[name] = data
    _set_json(_scene(), 'rig_systems', sy)


def note(text):
    n = get_json(_scene(), 'rig_notes', [])
    n.append(text)
    _set_json(_scene(), 'rig_notes', n)


# ------------------------------------------------------------------------------------------ groups (moving parts)
def motion(ob, type, axis=None, open=None, channel=None, stage=(0.0, 1.0), kind='part', description='',
           min=None, max=None, speed=None, units=None, **extra):
    """Describe how a moving part moves, in BLENDER local axes of the object (identity rotation at rest).

    axis:   'X' | 'Y' | 'Z' or a 3-vector (any hinge direction, e.g. a canted tail spindle or a swept hinge line)
    type:   rotate | translate         -> driven 0..1 by `channel` (open = degrees or metres at 1.0)
            aim_yaw | aim_pitch | steer | control -> driven by gameplay input, limited to [min, max] degrees,
                                          speed deg/s (control = flight control surface deflection)
            spin                      -> continuous rotation, speed in rad/s (optionally only while `channel` > 0)
            wheel                     -> wheel that rolls about `axis`
            fixed                     -> moves only with its parent (a store / a part that can be hidden or released)
    extra:  free-form, e.g. control={'input': 'roll', 'min': -25, 'max': 25} on a surface that also has a channel.
    """
    if axis is not None and not isinstance(axis, str):
        v = Vector(axis).normalized()
        axis = [round(v.x, 5), round(v.y, 5), round(v.z, 5)]
    _set_json(ob, 'rig_motion', dict(type=type, axis=axis, open=open, channel=channel, stage=list(stage), kind=kind,
                                     description=description, min=min, max=max, speed=speed, units=units, **extra))
    ob['rig_rest_loc'] = list(ob.location)


def pose(name, channels=None, inputs=None, description='', ground=True):
    """a named configuration: channel values (0..1) + input-driven values (degrees) for groups.
    ground=True means the model stands on its wheels in this pose (used by the low-point check)."""
    ps = get_json(_scene(), 'rig_poses', {})
    ps[name] = dict(channels=channels or {}, inputs=inputs or {}, description=description, ground=ground)
    _set_json(_scene(), 'rig_poses', ps)


# ------------------------------------------------------------------------------------------ markers
def point(name, loc, purpose, attach=None, direction=None, **extra):
    """a named socket: muzzle, launch tube, prompt (interaction), exit, camera, effect emitter, ..."""
    e = _empty(name, loc, 'PLAIN_AXES', 0.10, attach)
    _set_json(e, 'rig_point', dict(purpose=purpose, direction=list(direction) if direction else None, **extra))
    return e


def seat(name, loc, role, driver=False, enter=None, exit=None, attach=None, **extra):
    """a seat. loc = top of the cushion (where the hips go); the occupant faces the model's front (-Y)."""
    e = bpy.data.objects.get(name)
    if e is None or e.type != 'EMPTY':
        e = _empty(name, loc, 'SINGLE_ARROW', 0.25, attach)
    _set_json(e, 'rig_seat', dict(role=role, driver=driver, enter_point=enter, exit_point=exit, **extra))
    return e


def light(name, loc, kind, color, range_m, mode, direction=(0, -1, 0), angle_deg=None, brightness=2.0, attach=None,
          neon_materials=None):
    """kind: spot | point | surface. mode: headlights | beacons | brake | tail | interior | work | searchlight ..."""
    e = _empty(name, loc, 'CONE' if kind == 'spot' else 'SPHERE', 0.12, attach)
    _set_json(e, 'rig_light', dict(kind=kind, color=list(color), range_m=range_m, mode=mode, direction=list(direction),
                                   angle_deg=angle_deg, brightness=brightness, neon_materials=neon_materials or []))
    return e


def box(name, mn, mx, purpose='collision', attach=None):
    """an axis-aligned box (in model space at rest): collision proxy, trigger zone, loot area, ..."""
    mn, mx = Vector(mn), Vector(mx)
    e = _empty(name, (mn + mx) / 2, 'CUBE', 1.0, attach)
    e.scale = (mx - mn) / 2
    _set_json(e, 'rig_box', dict(purpose=purpose))
    return e


def wheel(group_ob, radius_m, width_m, steer=False, driven=True, suspension_up_m=0.25, suspension_down_m=0.30,
          steer_max_deg=None, **extra):
    """physical wheel data on a wheel group (the group that spins)."""
    _set_json(group_ob, 'rig_wheel', dict(radius_m=radius_m, width_m=width_m, steer=steer, driven=driven,
                                          suspension_up_m=suspension_up_m, suspension_down_m=suspension_down_m,
                                          steer_max_deg=steer_max_deg, **extra))
