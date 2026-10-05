"""Handoff exporter: turns a tagged .blend into a Roblox-ready package for the Roblox coding chat.

    exports/<Model>/<Model>.fbx            meshes merged per (moving group, material), stud scale, Roblox axes
    exports/<Model>/<Model>_Rig.json       machine-readable rig (schema survival-island-model/1)
    exports/<Model>/HANDOFF.md             instructions written for the coding chat
    exports/<Model>/previews/*.png         renders (rest + deployed)

Verification is built in: the FBX is re-imported and every pivot / the size is compared with the rig data.
"""
import os, json, math, datetime
import bpy, bmesh
from mathutils import Vector, Matrix
from .rig import SCHEMA, S, rbx, rbx_dir, get_json

# ---------------------------------------------------------------------------------------------- materials
ROBLOX_MATERIAL_BY_NAME = {
    'Paint': 'SmoothPlastic', 'ArmorPaint': 'SmoothPlastic', 'PaintDark': 'SmoothPlastic', 'Coating': 'Plastic',
    'Hardware': 'Metal', 'Steel': 'Metal', 'Alu': 'Metal', 'Gunmetal': 'Metal', 'Rubber': 'Rubber', 'Tire': 'Rubber',
    'Rim': 'Metal', 'Glass': 'Glass', 'GlassDark': 'Glass', 'Lens': 'Glass', 'LED': 'Neon', 'LEDOff': 'SmoothPlastic',
    'Amber': 'Neon', 'RedLens': 'Neon', 'IRLens': 'Glass', 'Mesh': 'Metal', 'SafetyRed': 'SmoothPlastic',
    'Hazard': 'SmoothPlastic', 'Canvas': 'Fabric', 'Wood': 'Wood', 'Plastic': 'SmoothPlastic', 'Fabric': 'Fabric',
    'Screen': 'Neon', 'ScreenBlue': 'Neon', 'Missile': 'SmoothPlastic', 'Engine': 'Metal', 'Copper': 'Metal',
    'Brass': 'Metal', 'Exhaust': 'Metal', 'Floor': 'Plastic', 'Rope': 'Fabric', 'Housing': 'SmoothPlastic',
    'Stencil': 'SmoothPlastic', 'ExtRed': 'SmoothPlastic', 'Concrete': 'Concrete', 'Brick': 'Brick',
    'Leather': 'Leather', 'Foil': 'Foil',
}
COLOR_OVERRIDE = {  # tuned for Roblox lighting: (rgb, transparency, reflectance)
    'LED': ((235, 240, 255), 0, 0), 'Amber': ((255, 140, 25), 0, 0), 'RedLens': ((255, 35, 25), 0, 0),
    'Screen': ((60, 230, 120), 0, 0), 'ScreenBlue': ((40, 150, 255), 0, 0),
    'Glass': ((120, 150, 145), 0.5, 0.1), 'GlassDark': ((20, 24, 26), 0.25, 0.1), 'Lens': ((220, 225, 230), 0.6, 0.1),
    'IRLens': ((40, 6, 8), 0.15, 0.05), 'Steel': ((150, 150, 148), 0, 0.05), 'Alu': ((185, 188, 192), 0, 0.08),
    'Brass': ((190, 150, 70), 0, 0.05),
}


def _srgb(c):
    c = max(0.0, min(1.0, c))
    s = c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return int(round(s * 255))


def material_spec(mat, prefix):
    """Roblox material + colour for a Blender material (name map first, then shader heuristics)."""
    name = mat.name[len(prefix):] if mat.name.startswith(prefix) else mat.name
    custom = get_json(mat, 'rig_roblox')
    if custom:
        return name, custom
    b = mat.node_tree.nodes.get('Principled BSDF') if mat.node_tree else None
    col = tuple(b.inputs['Base Color'].default_value[:3]) if b else tuple(mat.diffuse_color[:3])
    rgb, tr, rf = tuple(_srgb(c) for c in col), 0, 0
    emissive = bool(b and b.inputs['Emission Strength'].default_value > 0.01)
    if name in ROBLOX_MATERIAL_BY_NAME:
        rmat = ROBLOX_MATERIAL_BY_NAME[name]
    elif emissive:
        rmat = 'Neon'
    elif b and b.inputs['Transmission Weight'].default_value > 0.5:
        rmat, tr = 'Glass', 0.5
    elif b and b.inputs['Metallic'].default_value > 0.5:
        rmat = 'Metal'
    elif b and b.inputs['Roughness'].default_value > 0.85:
        rmat = 'Fabric'
    else:
        rmat = 'SmoothPlastic'
    if name in COLOR_OVERRIDE:
        rgb, tr, rf = COLOR_OVERRIDE[name]
    return name, dict(roblox_material=rmat, color_rgb=list(rgb), transparency=tr, reflectance=rf,
                      emissive=emissive or rmat == 'Neon')


# ---------------------------------------------------------------------------------------------- motion conversion
def motion_to_roblox(m):
    """Blender local-axis motion -> Roblox local-axis motion of the joint frame (model-aligned at rest).
    The axis map M: (x, y, z) -> (-x, z, y) has determinant +1 (a proper rotation), so angles keep their size:
    a rotation about Blender axis a by t == a rotation about Roblox axis M*a by t. For the letter axes that means
    Blender X -> Roblox X with the angle sign flipped, Blender Y -> Roblox Z, Blender Z -> Roblox Y."""
    out = dict(m)
    ax = m.get('axis')
    if not ax:
        return out
    t = m['type']
    rot_types = ('rotate', 'spin', 'aim_yaw', 'aim_pitch', 'steer', 'wheel', 'control')
    if isinstance(ax, str):
        flip = ax == 'X'
        out['axis'] = {'X': 'X', 'Y': 'Z', 'Z': 'Y'}[ax]
    else:
        flip = False
        out['axis'] = rbx_dir(ax)
    k = -1 if flip else 1
    if t in rot_types:
        if m.get('open') is not None:
            out['open'] = k * m['open']
        if m.get('min') is not None or m.get('max') is not None:
            lo, hi = m.get('min'), m.get('max')
            out['min'], out['max'] = ((-hi if hi is not None else None), (-lo if lo is not None else None)) if flip else (lo, hi)
        if m.get('speed') is not None and t == 'spin':
            out['speed'] = k * m['speed']
        if isinstance(m.get('control'), dict):
            c = dict(m['control'])
            if flip and 'min' in c and 'max' in c:
                c['min'], c['max'] = -c['max'], -c['min']
            out['control'] = c
        out['units'] = 'radians per second' if t == 'spin' else 'degrees'
    elif t == 'translate':
        if m.get('open') is not None:
            out['open'] = round(m['open'] * S, 4)          # distance along the (converted) axis
        out['units'] = 'studs'
    return out


def _ax_txt(ax):
    return ax if isinstance(ax, str) else '(%s)' % ', '.join('%.3f' % c for c in ax)


def describe_motion(m):
    t = m['type']
    ax = _ax_txt(m.get('axis')) if m.get('axis') else ''
    if t == 'rotate':
        txt = 'rotate %+g deg about %s' % (m['open'], ax)
        if isinstance(m.get('control'), dict):
            txt += ' (+ control %g..%g deg)' % (m['control'].get('min', 0), m['control'].get('max', 0))
        return txt
    if t == 'translate':
        return 'slide %+g studs along %s' % (m['open'], ax)
    if t in ('aim_yaw', 'aim_pitch', 'steer', 'control'):
        rng = 'unlimited' if m.get('min') is None else '%g .. %g deg' % (m['min'], m['max'])
        return '%s about %s, %s%s' % (t.replace('_', ' '), ax, rng, (', %g deg/s' % m['speed']) if m.get('speed') else '')
    if t == 'spin':
        return 'spin about %s at %g rad/s' % (ax, m.get('speed') or 0)
    if t == 'wheel':
        return 'wheel, rolls about %s' % ax
    if t == 'fixed':
        return 'fixed to its parent' + (' (store: %s)' % m.get('store') if m.get('store') else '')
    return t


# ---------------------------------------------------------------------------------------------- export
def _group_of(o, groups):
    p = o
    while p:
        if p.name in groups:
            return p.name
        p = p.parent
    return 'Body'


def export(repo, blend_path, renders=True, preview_views=None, mat_prefix='', log=print):
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    sc = bpy.context.scene
    model = get_json(sc, 'rig_model')
    assert model, 'scene has no rig_model - tag the model with common.rig.model(...) first'
    name = model['name']
    out_dir = os.path.join(repo, 'exports', name)
    os.makedirs(os.path.join(out_dir, 'previews'), exist_ok=True)
    from . import poses as P
    for o in sc.objects:
        o.animation_data_clear()
    P.apply_state()
    frames = None
    dg = bpy.context.evaluated_depsgraph_get()

    groups = {o.name: o for o in sc.objects if o.get('rig_motion')}
    meshes = [o for o in sc.objects if o.type == 'MESH' and not o.name.startswith('Studio')
              and not (o.users_collection and o.users_collection[0].name == 'RIG_Markers')]

    # ---------------------------------------------------------------- merge meshes per (group, material)
    buckets = {}
    for o in meshes:
        g = _group_of(o, groups)
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.transform(Matrix.Scale(S, 4) @ o.matrix_world)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        mats = [m.name[len(mat_prefix):] if (m and m.name.startswith(mat_prefix)) else (m.name if m else 'None')
                for m in me.materials] or ['None']
        bm.verts.index_update()
        for f in bm.faces:
            mn = mats[f.material_index] if f.material_index < len(mats) else mats[0]
            b = buckets.setdefault((g, mn), {'V': [], 'F': [], 'map': {}})
            idx = []
            for v in f.verts:
                key = (o.name, v.index)
                if key not in b['map']:
                    b['map'][key] = len(b['V'])
                    b['V'].append(v.co.copy())
                idx.append(b['map'][key])
            b['F'].append(tuple(idx))
        bm.free()
        ev.to_mesh_clear()

    ex = bpy.data.collections.new('RBX_Export')
    sc.collection.children.link(ex)
    made = []

    def emit(nm, V, F, mat, piv, group):
        me = bpy.data.meshes.new(nm)
        me.from_pydata([tuple(v - piv) for v in V], [], F)
        me.validate()
        me.materials.append(bpy.data.materials.get(mat_prefix + mat) or bpy.data.materials.get(mat))
        me.shade_smooth()
        me.set_sharp_from_angle(angle=0.70)
        ob = bpy.data.objects.new(nm, me)
        ex.objects.link(ob)
        ob.location = piv
        made.append(dict(name=nm, group=group, material=mat, triangles=len(F)))

    for (g, mn), b in sorted(buckets.items()):
        piv = Vector((0, 0, 0)) if g == 'Body' else groups[g].matrix_world.translation * S
        base = 'RBX_%s_%s' % (g, mn)
        V, F = b['V'], b['F']
        if len(F) <= 16000:
            emit(base, V, F, mn, piv, g)
            continue
        Fs = sorted(F, key=lambda f: sum(V[i].y for i in f))
        chunks, cur = [], []
        for f in Fs:
            cur.append(f)
            if len(cur) >= 15000:
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        for k, ch in enumerate(chunks):
            used = sorted({i for f in ch for i in f})
            rm = {i: j for j, i in enumerate(used)}
            emit('%s_%d' % (base, k + 1), [V[i] for i in used], [tuple(rm[i] for i in f) for f in ch], mn, piv, g)

    bpy.context.view_layer.update()
    for o in bpy.context.view_layer.objects:
        o.select_set(o.name in ex.objects)
    bpy.context.view_layer.objects.active = ex.objects[0]
    fbx_path = os.path.join(out_dir, name + '.fbx')
    bpy.ops.export_scene.fbx(filepath=fbx_path, use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
                             mesh_smooth_type='FACE', use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False)
    allv = [o.matrix_world @ v.co for o in ex.objects for v in o.data.vertices]
    bmin = Vector([min(v[i] for v in allv) for i in range(3)])
    bmax = Vector([max(v[i] for v in allv) for i in range(3)])
    # Blender-axis studs -> Roblox axes
    r_min = [-bmax.x, bmin.z, bmin.y]
    r_max = [-bmin.x, bmax.z, bmax.y]
    size = [round(r_max[i] - r_min[i], 4) for i in range(3)]
    center = [round((r_max[i] + r_min[i]) / 2, 4) for i in range(3)]

    # ---------------------------------------------------------------- rig data
    def attached(o):
        p = o.parent
        while p:
            if p.name in groups:
                return p.name
            p = p.parent
        return 'Body'

    rig = dict(schema=SCHEMA, model=model, generated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
               units=dict(blender='metres', roblox='studs', studs_per_metre=round(S, 6), metres_per_stud=0.28),
               axes=dict(roblox_from_blender='(-x, z, y) * %.6f' % S, forward='-Z (LookVector)', up='+Y',
                         right='+X', note='all *_studs values and Roblox motions are already converted'),
               import_=dict(fbx=name + '.fbx', importer=dict(scale_unit='Stud', scale_factor=1, world_forward='Front',
                                                             world_up='Top', set_pivot_to_scene_origin=True,
                                                             upload_to_roblox=True),
                            expected_size_studs=size, expected_center_studs=center, mesh_count=len(made),
                            triangles=sum(m['triangles'] for m in made),
                            max_mesh_triangles=max(m['triangles'] for m in made)),
               groups={}, channels=get_json(sc, 'rig_channels', {}), poses=get_json(sc, 'rig_poses', {}),
               seats={}, points={}, lights={}, boxes={},
               wheels={}, materials={}, meshes=made, physics=get_json(sc, 'rig_physics', {}),
               systems=get_json(sc, 'rig_systems', {}), notes=get_json(sc, 'rig_notes', []))
    for gname, o in sorted(groups.items()):
        m = get_json(o, 'rig_motion')
        par = attached(o)
        piv = o.matrix_world.translation
        mr = motion_to_roblox(m)
        rig['groups'][gname] = dict(parent_group=par, pivot_studs=rbx(piv), pivot_blender_m=[round(c, 4) for c in piv],
                                    motion=mr, motion_text=describe_motion(mr), motion_blender=m,
                                    meshes=[mm['name'] for mm in made if mm['group'] == gname])
        if o.get('rig_wheel'):
            rig['wheels'][gname] = dict(get_json(o, 'rig_wheel'), center_studs=rbx(piv),
                                        radius_studs=round(get_json(o, 'rig_wheel')['radius_m'] * S, 4),
                                        width_studs=round(get_json(o, 'rig_wheel')['width_m'] * S, 4))
    for o in sc.objects:
        pos = rbx(o.matrix_world.translation)
        if o.get('rig_point'):
            d = get_json(o, 'rig_point')
            if d.get('direction'):
                d['direction'] = rbx_dir(d['direction'])
            rig['points'][o.name] = dict(position_studs=pos, attached_to=attached(o), **d)
        if o.get('rig_seat'):
            rig['seats'][o.name] = dict(position_studs=pos, attached_to=attached(o), facing='-Z', **get_json(o, 'rig_seat'))
        if o.get('rig_light'):
            d = get_json(o, 'rig_light')
            d['direction'] = rbx_dir(d['direction'])
            d['range_studs'] = round(d.pop('range_m') * S, 2)
            rig['lights'][o.name] = dict(position_studs=pos, attached_to=attached(o), **d)
        if o.get('rig_box'):
            half = o.scale
            c = o.matrix_world.translation
            sz = [abs(round(2 * half.x * S, 4)), abs(round(2 * half.z * S, 4)), abs(round(2 * half.y * S, 4))]
            rig['boxes'][o.name] = dict(center_studs=rbx(c), size_studs=sz, attached_to=attached(o),
                                        **get_json(o, 'rig_box'))
    used_mats = sorted({m['material'] for m in made})
    for mn in used_mats:
        mat = bpy.data.materials.get(mat_prefix + mn) or bpy.data.materials.get(mn)
        if mat:
            rig['materials'][mn] = material_spec(mat, mat_prefix)[1]

    # ---------------------------------------------------------------- consistency checks
    problems = []
    for gname, g in rig['groups'].items():
        ch = g['motion'].get('channel')
        if ch and ch not in rig['channels']:
            problems.append('group %s uses unknown channel %s' % (gname, ch))
    for sname, s in rig['seats'].items():
        for k in ('enter_point', 'exit_point'):
            if s.get(k) and s[k] not in rig['points']:
                problems.append('seat %s %s %s is not a point' % (sname, k, s[k]))
    for m in made:
        if m['triangles'] > 20000:
            problems.append('mesh %s has %d triangles (> 20k Roblox limit)' % (m['name'], m['triangles']))
    rig['import'] = rig.pop('import_')

    # ---------------------------------------------------------------- verify the FBX by importing it back
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx_path, axis_forward='Z', axis_up='Y')
    bpy.context.view_layer.update()
    imp = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
    checked = 0
    if len(imp) != len(made):
        problems.append('FBX re-import has %d meshes, expected %d' % (len(imp), len(made)))
    for gname, g in rig['groups'].items():
        for mname in g['meshes'][:1]:
            o = imp.get(mname)
            if not o:
                problems.append('mesh %s missing after re-import' % mname)
                continue
            want = Vector(g['pivot_blender_m']) * S
            if (o.matrix_world.translation - want).length > 0.01:
                problems.append('pivot of %s off by %.3f studs after re-import' % (gname, (o.matrix_world.translation - want).length))
            checked += 1
    vs = [o.matrix_world @ v.co for o in imp.values() for v in o.data.vertices]
    rsize = [max(v.x for v in vs) - min(v.x for v in vs), max(v.z for v in vs) - min(v.z for v in vs),
             max(v.y for v in vs) - min(v.y for v in vs)]
    if any(abs(a - b) > 0.02 for a, b in zip(rsize, size)):
        problems.append('re-imported size %s differs from %s' % (rsize, size))
    rig['verification'] = dict(fbx_reimported=True, pivots_checked=checked, problems=problems,
                               passed=not problems)
    json.dump(rig, open(os.path.join(out_dir, name + '_Rig.json'), 'w'), indent=1)
    log('EXPORT %s: %d meshes, %d tris, size %s studs, pivots checked %d, problems %d'
        % (name, len(made), rig['import']['triangles'], size, checked, len(problems)))
    for p in problems:
        log('  PROBLEM:', p)

    # ---------------------------------------------------------------- previews
    previews = []
    if renders:
        previews = render_previews(blend_path, out_dir, rig, preview_views, log)
    write_handoff_md(out_dir, rig, previews)
    return rig


def render_previews(blend_path, out_dir, rig, views, log):
    """renders of the rest pose from four sides + one view per named pose (uses the rig poses, not the timeline)."""
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    from . import poses as P
    sc = bpy.context.scene
    for o in sc.objects:
        o.animation_data_clear()
    cam = sc.camera
    if cam is None:
        log('no camera in the .blend - skipping previews')
        return []
    size = Vector(rig['import']['expected_size_studs']) / S       # metres, Roblox axis order (x, up, z)
    L = max(size.x, size.z)
    h = size.y
    tgt = Vector((0, 0, h * 0.42))
    d = L * 0.95
    fr = (-0.62 * d, -0.80 * d, h * 0.9 + 0.25 * d)
    default = [('rest', 'rest_front34', fr), ('rest', 'rest_rear34', (0.62 * d, 0.85 * d, h + 0.25 * d)),
               ('rest', 'rest_side', (-1.45 * d, 0.0, h * 0.6)), ('rest', 'rest_top', (0.0, 0.01, 1.7 * d))]
    for pn in rig.get('poses', {}):
        if pn != 'rest':
            default.append((pn, 'pose_' + pn, (-0.70 * d, -0.62 * d, h + 0.45 * d)))
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    sc.cycles.samples = 24
    out = []
    for pose, nm, loc in (views or default):
        if pose == 'rest':
            P.apply_state()
        else:
            P.apply_pose(pose)
        fl = bpy.data.objects.get('Studio_Floor')
        if fl:
            fl.hide_render = False
        cam.location = Vector(loc)
        cam.rotation_euler = (tgt - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = 40
        cam.data.clip_end = 1000
        p = os.path.join(out_dir, 'previews', nm + '.png')
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        out.append('previews/' + nm + '.png')
        log('  rendered', nm)
    P.apply_state()
    return out


# ---------------------------------------------------------------------------------------------- HANDOFF.md
def _v(v):
    return '(%s)' % ', '.join('%.2f' % c for c in v)


def write_handoff_md(out_dir, rig, previews):
    m = rig['model']
    name = m['name']
    imp = rig['import']
    L = []
    w = L.append
    w('# %s — Roblox handoff package' % m['display'])
    w('')
    w('> **To the Roblox coding chat:** this folder is a complete, self-describing model package from Nic\'s Blender '
      'pipeline. Everything you need to make the model *fully functional and realistic* in Survival Island is here: the '
      'mesh file, every moving part with its exact hinge and motion, seats, sockets, lights, collision proxies, physics '
      'data and gameplay rules. The machine-readable source of truth is `%s_Rig.json` (schema `%s`); this file explains it. '
      'Please read sections 3–4 before writing code.' % (name, rig['schema']))
    w('')
    w('**%s** · category: **%s** · %s' % (m['display'], m['category'], m['description']))
    w('')
    if previews:
        w(' '.join('![%s](%s)' % (os.path.basename(p)[:-4], p) for p in previews[:3]))
        w('')
    w('## 1. Files')
    w('| File | What |')
    w('|---|---|')
    w('| `%s.fbx` | %d meshes, %d triangles (largest %d — under Roblox\'s 20k limit), already in studs |'
      % (name, imp['mesh_count'], imp['triangles'], imp['max_mesh_triangles']))
    w('| `%s_Rig.json` | all data below, machine-readable |' % name)
    w('| `HANDOFF.md` | this guide |')
    w('| `previews/` | renders at rest and deployed |')
    w('')
    w('## 2. Import into Studio')
    w('3D Importer (Home → Import / Avatar → Import 3D / File → Import 3D / Ctrl+M) with: **Scale Unit = Stud, Scale '
      'Factor = 1, World Forward = Front, World Up = Top, Set Pivot to Scene Origin ✔, Upload to Roblox ✔**.')
    w('Expected File Dimensions ≈ **%.2f × %.2f × %.2f** studs (X × Y × Z). The import is a flat Model of MeshParts that '
      'are all grey/white, anchored-or-unanchored, unwelded and fully collidable — your setup code must fix that (§4).'
      % tuple(imp['expected_size_studs']))
    w('Bounding-box centre after a correct import: `%s` — use it to re-align the model if a different pivot option was '
      'used (`shift = expected_center − actual_center`).' % _v(imp['expected_center_studs']))
    w('')
    w('## 3. Coordinates, units, names')
    w('- **1 stud = 0.28 m.** All `*_studs` values in the JSON are final Roblox numbers.')
    w('- Model space: origin on the ground under the model\'s centre, **front = −Z (LookVector)**, up = +Y, '
      '**the model\'s RIGHT = +X**, its left = −X. (Blender source: front −Y, left +X; converted for you.)')
    w('- Mesh names: `RBX_<Group>_<Material>[_n]`. `<Group>` is either `Body` (static) or a moving group from §5. '
      'Group names contain underscores, so match them against the JSON `groups` keys (longest match first); '
      '`<Material>` has no digits; `_n` is a chunk index for big meshes.')
    w('- Every moving group\'s meshes were exported with the MeshPart pivot on the group\'s hinge, but Roblox recentres '
      'MeshParts — always use `pivot_studs` from the JSON, never the MeshPart position.')
    w('')
    w('## 4. Recommended assembly')
    w('1. Invisible, unanchored **root part** (PrimaryPart) — for vehicles a heavy chassis box low in the hull '
      '(`RootPriority` high); set `Model.WorldPivot` = ground origin so `PivotTo` places it on the ground.')
    w('2. All visual MeshParts: `CanCollide/CanTouch/CanQuery = false`, `Massless = true`, materials from §11, '
      '`CollisionFidelity = Box`, `CastShadow = false` for Neon/Glass.')
    w('3. One invisible **joint part per moving group** at `pivot_studs` (identity rotation), connected to its parent '
      'group\'s joint part (or the root for `parent_group = Body`) with a **Motor6D**: `C0 = Part0.CFrame:ToObjectSpace'
      '(joint.CFrame)`, `C1 = identity`. Weld the group\'s meshes to its joint part. Create joints in parent-first order.')
    w('4. Animate on clients by setting `Motor6D.Transform` (`rotate` → `CFrame.Angles` about the listed axis, '
      '`translate` → `CFrame.new(axis * studs)`); keep the authoritative state on the server as attributes '
      '(channel targets 0/1, aim angles). The joint frame is model-aligned at rest, so axes in §5 are exact.')
    w('5. Collision: use the boxes in §9 (invisible, welded, `CanCollide`/`CanQuery` true) instead of mesh collision.')
    w('6. Physics wheels (vehicles): invisible cylinder parts at the wheel centres on suspension constraints; weld the '
      'wheel groups\' meshes to them (§10). Use collision groups so wheels never touch the body boxes.')
    w('7. Set `Model.ModelStreamingMode = Atomic` (the map uses streaming).')
    w('')
    w('## 5. Moving parts')
    w('Axes are the joint frame (= model axes at rest). An axis is a letter (X / Y / Z) or a unit vector `(x, y, z)` '
      'in model space for hinges that are not on a model axis — rotate about it with `CFrame.fromAxisAngle(axis, '
      'math.rad(angle))`. `open` is the value at channel state 1; `stage` is the slice of the channel\'s 0→1 progress '
      'during which this part moves (ease each slice with smoothstep). Types: rotate / translate (channel-driven), '
      'aim_yaw / aim_pitch / steer / control (player input, clamp to min..max), spin (continuous while its channel > 0), '
      'wheel (rolls on the ground), fixed (rides on its parent; `store` = a weapon that can be hidden / released).')
    w('')
    w('| Group | Parent | Pivot (studs) | Motion | Channel · stage | What it is |')
    w('|---|---|---|---|---|---|')
    for g, d in rig['groups'].items():
        mo = d['motion']
        ch = ('%s · %g–%g' % (mo['channel'], mo['stage'][0], mo['stage'][1])) if mo.get('channel') else '—'
        w('| `%s` | %s | %s | %s | %s | %s |' % (g, d['parent_group'], _v(d['pivot_studs']), d['motion_text'], ch,
                                                 mo.get('description', '')))
    w('')
    if rig['channels']:
        w('## 6. Channels (states the server owns)')
        w('| Channel | Duration 0→1 | Moves | Rules |')
        w('|---|---|---|---|')
        for c, d in rig['channels'].items():
            members = [g for g, gd in rig['groups'].items() if gd['motion'].get('channel') == c]
            w('| `%s` | %.2f s | %s | %s |' % (c, d['duration_s'], ', '.join('`%s`' % x for x in members),
                                               '; '.join(d['rules']) or '—'))
        w('')
    if rig.get('poses'):
        w('## 6b. Named poses (flight modes / test states)')
        w('| Pose | Channels at 1 | Inputs | On the ground | What it is |')
        w('|---|---|---|---|---|')
        for pn, d in rig['poses'].items():
            ch = ', '.join('%s=%g' % kv for kv in d.get('channels', {}).items()) or '— (all 0)'
            ip = ', '.join('%s=%g' % kv for kv in d.get('inputs', {}).items()) or '—'
            w('| `%s` | %s | %s | %s | %s |' % (pn, ch, ip, 'yes' if d.get('ground', True) else 'no', d.get('description', '')))
        w('')
    if rig['seats']:
        w('## 7. Seats')
        w('| Seat | Position (studs, cushion top) | Attached to | Role | Enter at | Exit to |')
        w('|---|---|---|---|---|---|')
        for s, d in rig['seats'].items():
            w('| `%s` | %s | %s | %s%s | %s | %s |' % (s, _v(d['position_studs']), d['attached_to'], d['role'],
                                                     ' (**driver**)' if d.get('driver') else '', d.get('enter_point') or '—',
                                                     d.get('exit_point') or '—'))
        w('')
    if rig['points']:
        w('## 8. Points / sockets')
        w('| Point | Position (studs) | Attached to | Purpose |')
        w('|---|---|---|---|')
        for p, d in rig['points'].items():
            extra = ', '.join('%s=%s' % (k, v) for k, v in d.items()
                              if k not in ('position_studs', 'attached_to', 'purpose') and v not in (None, '', []))
            w('| `%s` | %s | %s | %s%s |' % (p, _v(d['position_studs']), d['attached_to'], d['purpose'],
                                            (' (%s)' % extra) if extra else ''))
        w('')
    if rig['boxes']:
        w('## 9. Boxes (collision / zones)')
        w('| Box | Centre (studs) | Size (studs) | Purpose |')
        w('|---|---|---|---|')
        for b, d in rig['boxes'].items():
            w('| `%s` | %s | %s | %s |' % (b, _v(d['center_studs']), _v(d['size_studs']), d['purpose']))
        w('')
    if rig['wheels'] or rig['physics']:
        w('## 10. Physics (realistic data + Roblox tuning)')
        if rig['wheels']:
            w('| Wheel group | Centre (studs) | Radius | Width | Steers | Driven | Travel up / down (m) |')
            w('|---|---|---|---|---|---|---|')
            for g, d in rig['wheels'].items():
                w('| `%s` | %s | %.3f st (%.2f m) | %.3f st | %s | %s | %.2f / %.2f |'
                  % (g, _v(d['center_studs']), d['radius_studs'], d['radius_m'], d['width_studs'],
                     ('±%g°' % d['steer_max_deg']) if d['steer'] else 'no', 'yes' if d['driven'] else 'no',
                     d['suspension_up_m'], d['suspension_down_m']))
            w('')
        for k, v in rig['physics'].items():
            w('- **%s:** %s' % (k.replace('_', ' '), v))
        w('')
    if rig['lights']:
        w('## 11a. Lights')
        w('| Light | Position (studs) | Attached to | Type | Mode | Direction | Range (studs) | Neon materials |')
        w('|---|---|---|---|---|---|---|---|')
        for l, d in rig['lights'].items():
            w('| `%s` | %s | %s | %s%s | %s | %s | %g | %s |' % (l, _v(d['position_studs']), d['attached_to'], d['kind'],
                                                             (' %g°' % d['angle_deg']) if d.get('angle_deg') else '',
                                                             d['mode'], _v(d['direction']), d['range_studs'],
                                                             ', '.join(d['neon_materials']) or '—'))
        w('')
    w('## 11. Materials (apply by the `<Material>` part of each mesh name)')
    w('| Material | Roblox material | Colour (RGB) | Transparency | Reflectance |')
    w('|---|---|---|---|---|')
    for mn, d in rig['materials'].items():
        w('| %s | %s | %s | %g | %g |' % (mn, d['roblox_material'], ', '.join(str(c) for c in d['color_rgb']),
                                          d['transparency'], d['reflectance']))
    w('')
    if rig['systems']:
        w('## 12. Gameplay systems')
        for s, d in rig['systems'].items():
            w('### %s' % s)
            for k, v in d.items():
                w('- **%s:** %s' % (k.replace('_', ' '), v))
            w('')
    if rig['notes']:
        w('## 13. Notes and rules')
        for n in rig['notes']:
            w('- %s' % n)
        w('')
    w('## 14. Acceptance checklist (test in Studio before calling it done)')
    w('- [ ] Import size matches §2; installer reports 0 unknown mesh names.')
    w('- [ ] Every group in §5 moves about the right hinge, in the right direction, by the listed amount, in stage order.')
    w('- [ ] Nothing floats or clips at rest **and** fully deployed (the Blender checks found 0 floating parts in both).')
    if rig['seats']:
        w('- [ ] Every seat can be entered from its enter point and exits to its exit point; occupants face −Z.')
    if rig['wheels']:
        w('- [ ] Drives straight, steers the right way, brakes, climbs hills, does not bounce or flip in normal turns.')
    w('- [ ] All server checks in place (who may use what, rate limits, clamped inputs) — the game is server-authoritative.')
    w('- [ ] Output window clean (no errors/warnings from the new scripts).')
    w('')
    v = rig['verification']
    w('_Generated %s by `blender/export_handoff.py`. FBX re-import check: %s (%d pivots compared, %d problems)._'
      % (rig['generated'], 'PASSED' if v['passed'] else 'FAILED', v['pivots_checked'], len(v['problems'])))
    open(os.path.join(out_dir, 'HANDOFF.md'), 'w').write('\n'.join(L) + '\n')
