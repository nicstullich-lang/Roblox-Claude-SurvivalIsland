"""Survival Island weapon pack - shared library (materials, shape builders, hardware, presentation).

Five original survival-game weapons share one fictional universe ("the Haven workshops": scavenged, re-built
service weapons). Each weapon is built by its own module (r12, mako9, trailmark, sparrow9, bastion) into its own
collection under the parent collection SURVIVAL_WEAPONS.

Units and axes (same as every model in this repo): metres, Z up, the weapon's MUZZLE points to -Y, its LEFT is +X.
Game scale: 1 stud = 0.28 m, so the weapons are built at the requested stud sizes x 0.28 (the R-12 carbine is
4.6 studs = 1.29 m long). That is larger than a real carbine on purpose - Roblox characters are ~5 studs tall.

Every weapon's ORIGIN is the same datum: on the bore axis (x = 0, z = 0) straight above the trigger blade.
Every part of a weapon shares that origin (transforms applied), except moving parts, whose origin is their hinge /
slide pivot (rig_motion tag, see common/rig.py).
"""
import bpy, bmesh
from math import sin, cos, tan, atan2, acos, asin, pi, radians, degrees, sqrt, ceil
from mathutils import Vector, Matrix, Quaternion
from common.geo import *          # noqa: F401,F403  (shared toolkit)
from common import geo, rig

V = Vector
PREFIX = 'SW_'                    # material prefix
PACK = 'SURVIVAL_WEAPONS'         # parent collection
PACK_FILE = 'SurvivalWeaponPack'
S = 1 / 0.28                      # studs per metre

# code: (collection, export file name, display name, target size in studs (L, H, W), description)
WEAPONS = {
    'R12': ('ROADRUNNER_R12', 'RoadrunnerR12', 'Roadrunner R-12', (4.6, 1.4, 0.6),
            'scavenger carbine built from salvaged rifle parts: olive-gray receiver, curved tan magazine, red-dot optic'),
    'MAKO9': ('MAKO9', 'Mako9', 'Mako-9', (3.3, 1.35, 0.55),
              'compact 9 mm submachine gun with a side-folding stock and a tan side panel'),
    'TM308': ('TRAILMARK_308', 'Trailmark308', 'Trailmark .308', (5.1, 1.55, 0.6),
              'bolt-action marksman rifle: slate receiver, olive precision stock, medium scope, folding bipod'),
    'SP9': ('SPARROW9', 'Sparrow9', 'Sparrow-9', (2.0, 1.0, 0.45),
            '9 mm service pistol with a dark-steel slide, polymer frame and stippled grip panels'),
    'BLMG': ('BASTION_LMG', 'BastionLMG', 'Bastion LMG', (5.0, 1.8, 0.75),
             'belt-fed light machine gun with a carry handle, side ammo box and folding bipod'),
}
ORDER = ['R12', 'MAKO9', 'TM308', 'SP9', 'BLMG']


def R(material, rgb, transparency=0.0, reflectance=0.0):
    """explicit Roblox look for a material (read by the handoff exporter)."""
    return {'roblox_material': material, 'color_rgb': list(rgb), 'transparency': transparency,
            'reflectance': reflectance, 'emissive': False}


def lin(r, g, b):
    """sRGB 0-255 -> linear 0-1 (Blender colour sockets are linear)."""
    f = lambda c: (c / 255) / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


# ============================================================== material library
# One consistent library for the whole pack. Every material is a Principled BSDF driven by procedural wear:
#   vary   - large blotchy colour variation (faded / re-touched finish)
#   grime  - darker brownish dirt patches
#   ao     - darker recesses (ambient occlusion on the part itself)
#   edge   - (exposed colour, amount): worn edges show the material underneath (bare steel under paint, lighter
#            polymer under the surface skin) - uses the Cycles Bevel node, so it needs no extra geometry
#   scratch- fine light scratches
#   bump   - 'paint' (orange peel), 'stipple' (moulded polymer texture), 'rubber', 'grain' (wood), 'cast'
# The Roblox spec (R) is the flat colour used when the FBX is imported (Roblox shows no procedural shaders).
STEEL_BARE = lin(132, 132, 128)
MATS = {
    # painted metal
    'PaintOliveGray': dict(col=lin(76, 82, 68), rough=0.66, metal=0.0, vary=0.15, grime=0.50, ao=0.55,
                           edge=(STEEL_BARE, 0.9, 0.35, 0.9), scratch=0.75, bump='paint',
                           roblox=R('SmoothPlastic', (82, 88, 74))),
    'PaintOlive': dict(col=lin(80, 84, 56), rough=0.68, metal=0.0, vary=0.17, grime=0.55, ao=0.55,
                       edge=(STEEL_BARE, 0.9, 0.35, 0.9), scratch=0.70, bump='paint',
                       roblox=R('SmoothPlastic', (86, 90, 62))),
    'PaintOliveDark': dict(col=lin(56, 60, 45), rough=0.70, metal=0.0, vary=0.17, grime=0.60, ao=0.6,
                           edge=(STEEL_BARE, 0.9, 0.35, 0.9), scratch=0.80, bump='paint',
                           roblox=R('SmoothPlastic', (60, 64, 50))),
    'PaintSlate': dict(col=lin(62, 66, 70), rough=0.62, metal=0.0, vary=0.13, grime=0.50, ao=0.55,
                       edge=(STEEL_BARE, 0.9, 0.35, 0.9), scratch=0.75, bump='paint',
                       roblox=R('SmoothPlastic', (68, 72, 77))),
    # metal finishes
    'Graphite': dict(col=lin(64, 66, 69), rough=0.55, metal=0.50, vary=0.08, grime=0.40, ao=0.6,
                     edge=(lin(118, 118, 116), 0.8, 0.32, 1.0), scratch=0.75, bump='cast',
                     roblox=R('Metal', (74, 76, 80))),
    'DarkSteel': dict(col=lin(42, 43, 45), rough=0.44, metal=0.9, vary=0.10, grime=0.35, ao=0.5,
                      edge=(lin(128, 128, 126), 0.7, 0.30, 1.0), scratch=0.60,
                      roblox=R('Metal', (52, 53, 56))),
    'Blackened': dict(col=lin(30, 30, 31), rough=0.52, metal=0.75, vary=0.10, grime=0.40, ao=0.5,
                      edge=(lin(110, 110, 108), 0.7, 0.32, 1.0), scratch=0.55,
                      roblox=R('Metal', (38, 38, 40))),
    'Steel': dict(col=lin(120, 120, 117), rough=0.38, metal=1.0, vary=0.12, grime=0.25, ao=0.45,
                  roblox=R('Metal', (128, 128, 125))),
    'Copper': dict(col=lin(132, 82, 54), rough=0.45, metal=1.0, vary=0.15, grime=0.3, ao=0.4,
                   roblox=R('Metal', (140, 90, 62))),
    'Brass': dict(col=lin(128, 104, 62), rough=0.42, metal=1.0, vary=0.18, grime=0.35, ao=0.4,
                  roblox=R('Metal', (136, 110, 66))),
    # polymers / rubber / wood
    'PolyBlack': dict(col=lin(31, 31, 32), rough=0.80, metal=0.0, vary=0.06, grime=0.35, ao=0.5,
                      edge=(lin(62, 62, 62), 0.6, 0.72, 0.0), scratch=0.45, bump='stipple',
                      roblox=R('Plastic', (34, 34, 36))),
    'PolyTan': dict(col=lin(132, 116, 88), rough=0.74, metal=0.0, vary=0.12, grime=0.55, ao=0.5,
                    edge=(lin(172, 156, 124), 0.6, 0.70, 0.0), scratch=0.50, bump='stipple',
                    roblox=R('Plastic', (138, 122, 94))),
    'PolyOlive': dict(col=lin(70, 74, 48), rough=0.74, metal=0.0, vary=0.10, grime=0.50, ao=0.5,
                      edge=(lin(122, 124, 98), 0.6, 0.70, 0.0), scratch=0.50, bump='stipple',
                      roblox=R('Plastic', (76, 80, 54))),
    'Rubber': dict(col=lin(25, 25, 25), rough=0.92, metal=0.0, vary=0.08, grime=0.35, ao=0.5, bump='rubber',
                   roblox=R('Rubber', (30, 30, 30))),
    'Walnut': dict(col=lin(76, 46, 28), rough=0.55, metal=0.0, wood=True, grime=0.25, ao=0.45,
                   edge=(lin(118, 80, 52), 0.6, 0.6, 0.0), scratch=0.3,
                   roblox=R('Wood', (84, 52, 34))),
    # markings, glass
    'MarkRed': dict(col=lin(112, 46, 34), rough=0.82, metal=0.0, vary=0.25, grime=0.3, ao=0.2,
                    roblox=R('SmoothPlastic', (118, 50, 38))),
    'Lens': dict(col=lin(14, 24, 22), rough=0.04, metal=0.0, coat=1.0, lens=True,
                 roblox=R('Glass', (32, 44, 42), 0.15, 0.35)),
    'LensClear': dict(col=lin(196, 204, 190), rough=0.02, metal=0.0, glass=1.0,
                      roblox=R('Glass', (170, 182, 176), 0.6, 0.15)),
}


def _sock(coll, ident):
    return next(x for x in coll if x.identifier == ident)


def make_material(name):
    """build SW_<name> (Cycles node tree with procedural wear)."""
    full = PREFIX + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    d = MATS[name]
    m = bpy.data.materials.new(full)
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = N.get('Principled BSDF')
    col = d['col']
    m.diffuse_color = (*col, 1)
    m.roughness = d['rough']
    m.metallic = d['metal']
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = d['rough']
    b.inputs['Metallic'].default_value = d['metal']
    if d.get('glass'):
        b.inputs['Transmission Weight'].default_value = d['glass']
        b.inputs['IOR'].default_value = 1.50
        m.diffuse_color = (*col, 0.4)
    if d.get('coat'):
        b.inputs['Coat Weight'].default_value = d['coat']
        b.inputs['Coat Roughness'].default_value = 0.03
    if d.get('lens'):
        b.inputs['Specular IOR Level'].default_value = 0.7
    import json
    m['rig_roblox'] = json.dumps(d['roblox'])
    if d.get('glass') or d.get('lens'):
        return m

    tc = N.new('ShaderNodeTexCoord')

    def noise(scale, detail=6.0, rough=0.6, vec=None, dist=0.0):
        n = N.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        n.inputs['Distortion'].default_value = dist
        L.new(vec if vec is not None else tc.outputs['Object'], n.inputs['Vector'])
        return n.outputs['Fac']

    def mrange(src, a, b_, c=0.0, d_=1.0, clamp=True):
        r = N.new('ShaderNodeMapRange')
        r.clamp = clamp
        r.inputs['From Min'].default_value = a
        r.inputs['From Max'].default_value = b_
        r.inputs['To Min'].default_value = c
        r.inputs['To Max'].default_value = d_
        if isinstance(src, (int, float)):
            r.inputs['Value'].default_value = src
        else:
            L.new(src, r.inputs['Value'])
        return r.outputs['Result']

    def math(op, a, b_=None, clamp=False):
        mm = N.new('ShaderNodeMath')
        mm.operation = op
        mm.use_clamp = clamp
        for i, v in enumerate((a, b_)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                mm.inputs[i].default_value = v
            else:
                L.new(v, mm.inputs[i])
        return mm.outputs[0]

    def mix(fac, a, b_, blend='MIX'):
        mx = N.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        mx.blend_type = blend
        for ident, v in (('Factor_Float', fac), ('A_Color', a), ('B_Color', b_)):
            s = _sock(mx.inputs, ident)
            if isinstance(v, (int, float)):
                s.default_value = v
            elif isinstance(v, tuple):
                s.default_value = (*v[:3], 1)
            else:
                L.new(v, s)
        return _sock(mx.outputs, 'Result_Color')

    def rgb(c):
        n = N.new('ShaderNodeRGB')
        n.outputs[0].default_value = (*c[:3], 1)
        return n.outputs[0]

    # ---- base colour (+ wood grain) + variation
    if d.get('wood'):
        mp = N.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1.0, 0.06, 1.0)        # grain runs along the weapon (Y)
        L.new(tc.outputs['Object'], mp.inputs['Vector'])
        wv = N.new('ShaderNodeTexWave')
        wv.wave_type = 'BANDS'
        wv.bands_direction = 'Z'
        wv.inputs['Scale'].default_value = 34.0
        wv.inputs['Distortion'].default_value = 5.0
        wv.inputs['Detail'].default_value = 4.0
        wv.inputs['Detail Scale'].default_value = 1.5
        L.new(mp.outputs['Vector'], wv.inputs['Vector'])
        g = mrange(wv.outputs['Fac'], 0.15, 0.95)
        fine = noise(90.0, 8.0, 0.6, mp.outputs['Vector'])
        g = math('MULTIPLY', g, mrange(fine, 0.3, 0.7, 0.75, 1.15))
        base = mix(g, lin(50, 30, 18), lin(86, 54, 33))
    else:
        base = rgb(col)
    if d.get('vary'):
        k = d['vary']
        v = mrange(noise(2.2, 8.0, 0.62), 0.3, 0.7, 1.0 - k, 1.0 + k)
        cm = N.new('ShaderNodeCombineColor')
        for i in range(3):
            L.new(v, cm.inputs[i])
        base = mix(1.0, base, cm.outputs['Color'], 'MULTIPLY')
    if d.get('grime'):
        gm = math('MULTIPLY', mrange(noise(3.5, 6.0, 0.7), 0.48, 0.72), d['grime'])
        base = mix(gm, base, mix(1.0, base, (0.62, 0.58, 0.50), 'MULTIPLY'))
    rough = mrange(noise(7.0, 8.0, 0.6), 0.25, 0.75, max(0.0, d['rough'] - 0.08), min(1.0, d['rough'] + 0.08))
    metal = d['metal']

    # ---- wear: edges + scratches reveal the material underneath
    wear = None
    if d.get('edge'):
        ecol, eamt, erough, emetal = d['edge']
        bev = N.new('ShaderNodeBevel')
        bev.samples = 8
        bev.inputs['Radius'].default_value = 0.0045
        geo_n = N.new('ShaderNodeNewGeometry')
        dot = N.new('ShaderNodeVectorMath')
        dot.operation = 'DOT_PRODUCT'
        L.new(bev.outputs['Normal'], dot.inputs[0])
        L.new(geo_n.outputs['Normal'], dot.inputs[1])
        edge = mrange(dot.outputs['Value'], 0.9985, 0.965)              # 0 on flat faces, 1 on sharp edges
        brk = mrange(noise(38.0, 6.0, 0.65), 0.32, 0.66)               # patchy break-up
        edge = mrange(math('MULTIPLY', edge, math('ADD', brk, 0.40)), 0.16, 0.48)
        wear = math('MULTIPLY', edge, eamt, clamp=True)
        if d.get('scratch'):
            # thin scratches = iso-lines of strongly stretched noise, two directions, sparse regions only
            sc = None
            for rot, scl in (((0.4, 0.2, 0.3), (1.0, 0.035, 1.0)), ((1.2, 0.9, 0.1), (0.035, 1.0, 1.0))):
                mp2 = N.new('ShaderNodeMapping')
                mp2.inputs['Rotation'].default_value = rot
                mp2.inputs['Scale'].default_value = scl
                L.new(tc.outputs['Object'], mp2.inputs['Vector'])
                f_ = noise(160.0, 2.0, 0.5, mp2.outputs['Vector'])
                line = mrange(math('ABSOLUTE', math('SUBTRACT', f_, 0.5)), 0.0, 0.010, 1.0, 0.0)
                sc = line if sc is None else math('MAXIMUM', sc, line)
            region = mrange(noise(4.0, 4.0, 0.6), 0.50, 0.66)
            sc = math('MULTIPLY', math('MULTIPLY', sc, region), d['scratch'] * 0.75)
            wear = math('MAXIMUM', wear, sc)
        base = mix(wear, base, ecol)
        rough = mix(wear, rough, (erough,) * 3)
        mt = math('ADD', math('MULTIPLY', wear, emetal - metal), metal)
        L.new(mt, b.inputs['Metallic'])
    # ---- dark recesses
    if d.get('ao'):
        ao = N.new('ShaderNodeAmbientOcclusion')
        ao.samples = 8
        ao.only_local = True
        ao.inputs['Distance'].default_value = 0.012
        f = mrange(ao.outputs['AO'], 0.0, 1.0, 1.0 - d['ao'], 1.0)
        cm = N.new('ShaderNodeCombineColor')
        for i in range(3):
            L.new(f, cm.inputs[i])
        base = mix(1.0, base, cm.outputs['Color'], 'MULTIPLY')
    L.new(base, b.inputs['Base Color'])
    if hasattr(rough, 'node') and rough.node.bl_idname == 'ShaderNodeMix':
        bw = N.new('ShaderNodeRGBToBW')
        L.new(rough, bw.inputs[0])
        L.new(bw.outputs[0], b.inputs['Roughness'])
    else:
        L.new(rough, b.inputs['Roughness'])
    # ---- surface texture (bump)
    bk = d.get('bump') or ('grain' if d.get('wood') else None)
    if bk:
        sc_, st_, di_ = {'paint': (420.0, 0.035, 0.0004), 'stipple': (650.0, 0.30, 0.0007), 'rubber': (420.0, 0.25, 0.0007),
                         'cast': (380.0, 0.10, 0.0005), 'grain': (140.0, 0.10, 0.0005)}[bk]
        h = noise(sc_, 4.0 if bk != 'stipple' else 2.0, 0.55)
        if wear is not None:
            h = math('SUBTRACT', h, math('MULTIPLY', wear, 0.25))
        bp = N.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = st_
        bp.inputs['Distance'].default_value = di_
        L.new(h, bp.inputs['Height'])
        L.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def make_materials():
    for n in MATS:
        make_material(n)


# ============================================================== pack / weapon scaffolding
CUR = {}


def new_pack():
    """empty file with the parent collection (call once per build)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    pack = bpy.data.collections.new(PACK)
    sc.collection.children.link(pack)
    geo.setup(PREFIX, PACK, 'unused_root', {k: (v['col'], v['rough'], v['metal'], {}) for k, v in MATS.items()})
    geo.PROJ['coll_prefix'] = ''
    make_materials()
    return pack


def begin(code):
    """start building weapon `code`: its collection, root empty (the weapon origin), rig holder and marker collection."""
    coll_name, export, display, dims, desc = WEAPONS[code]
    c = bpy.data.collections.new(coll_name)
    bpy.data.collections[PACK].children.link(c)
    mc = bpy.data.collections.new(code + '_RigMarkers')
    c.children.link(mc)
    r = bpy.data.objects.new(code + '_Root', None)
    r.empty_display_type = 'ARROWS'
    r.empty_display_size = 0.12
    c.objects.link(r)
    r['weapon_code'] = code
    r['export_name'] = export
    r['target_studs_LHW'] = list(dims)
    geo.PROJ['root'] = r.name
    rig.HOLDER = r
    rig.MARKERS = mc.name
    CUR.clear()
    CUR.update(code=code, coll=coll_name, root=r)
    return r


def nm(name):
    return CUR['code'] + '_' + name


def obj(name):
    return bpy.data.objects[nm(name)]


def part(name, vf, mat, parent=None, bev=None, sharp=30, mat_idx=None, smooth=True, wn=True):
    """create a weapon part '<CODE>_<name>' (transforms applied, origin = weapon origin).
    bev = (width, segments, angle_deg) -> bevel + weighted normals, applied immediately."""
    ob = mk(nm(name), vf, mat, CUR['coll'], parent, smooth, sharp, None, True, mat_idx)
    if bev:
        finish(ob, *bev) if isinstance(bev, (tuple, list)) else finish(ob, bev)
    elif wn and smooth:
        weighted(ob)
    return ob


def weighted(ob):
    w = ob.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL')
    w.keep_sharp = True
    w.weight = 50
    w.mode = 'FACE_AREA'
    apply_mods(ob)


def finish(ob, w=0.0015, seg=2, ang=35):
    """bevel the hard edges (angle-limited, clamped) + harden / weighted normals; applied (no live modifiers)."""
    m = bevel(ob, w, seg, ang, harden=True)
    m.miter_outer = 'MITER_ARC'
    wn = ob.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL')
    wn.keep_sharp = True
    wn.weight = 50
    apply_mods(ob)
    return ob


def _triangulate_ngons(ob):
    """EXACT booleans on bevelled meshes leave holes when big (slightly non-planar / concave) n-gons are involved:
    triangulate faces with more than 4 corners first (verified: 0 non-manifold edges afterwards)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    ng = [f for f in bm.faces if len(f.verts) > 4]
    if ng:
        bmesh.ops.triangulate(bm, faces=ng, quad_method='BEAUTY', ngon_method='BEAUTY')
        bm.to_mesh(ob.data)
    bm.free()


def _clean_slots(ob):
    """booleans append an empty material slot for the (material-less) cutters: drop it, remap the faces."""
    me = ob.data
    slots = list(me.materials)
    if all(m is not None for m in slots):
        return
    keep = [i for i, m in enumerate(slots) if m is not None]
    remap = {old: new for new, old in enumerate(keep)}
    idx = [0] * len(me.polygons)
    me.polygons.foreach_get('material_index', idx)
    idx = [remap.get(i, 0) for i in idx]
    for i in reversed(range(len(slots))):
        if slots[i] is None:
            me.materials.pop(index=i)
    me.polygons.foreach_set('material_index', idx)


def cut(ob, vfs, op='DIFFERENCE'):
    """boolean `ob` with one or more raw (verts, faces) solids (EXACT solver, applied)."""
    if not isinstance(vfs, list):
        vfs = [vfs]
    _triangulate_ngons(ob)
    cs = [cutter('_c%d' % i, vf) for i, vf in enumerate(vfs)]
    boolean(ob, cs, op)
    for c in cs:
        me = c.data
        bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.meshes.remove(me)
    _clean_slots(ob)
    return ob


def detail(ob, vfs):
    """cut small features (serrations, vents, slots, ribs) AFTER the part was bevelled: crisp, cheap edges + weighted
    normals (the same look at game distance for a fraction of the triangles)."""
    cut(ob, vfs)
    weighted(ob)
    return ob


def rail_part(name, y0, y1, z0, mat='Blackened', parent=None, down=False):
    """Picatinny rail part: chamfered body, then the cross slots. down=True hangs it under a surface at z0."""
    rb, rc = rail_vf(y0, y1, 0.0 if down else z0)
    if down:
        T = Matrix.Translation((0, 0, z0))
        rb = xform_vf(mirror_vf(rb, 2), T)
        rc = [xform_vf(mirror_vf(c, 2), T) for c in rc]
    r = part(name, rb, mat, parent, wn=False)
    finish(r, 0.0008, 1, 35)
    return detail(r, rc)


def union_vf(*vfs):
    """real boolean union of raw solids -> (verts, faces) (for single clean shells, e.g. a receiver + its magwell)."""
    base = cutter('_u', vfs[0])
    others = [cutter('_u%d' % i, vf) for i, vf in enumerate(vfs[1:])]
    boolean(base, others, 'UNION')
    me = base.data
    out = ([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    for c in [base] + others:
        m2 = c.data
        bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.meshes.remove(m2)
    return out


def group(ob, pivot, typ, axis, opn, channel, desc, stage=(0.0, 1.0), kind='part', **kw):
    """make `ob` a moving group: origin on its hinge / slide pivot + rig tag."""
    set_origin(ob, pivot)
    rig.motion(ob, typ, axis, opn, channel, stage, kind, desc, **kw)
    return ob


def point(name, loc, purpose, direction=None, attach=None, **kw):
    return rig.point(nm(name), loc, purpose, attach=attach or CUR['root'], direction=direction, **kw)


# ============================================================== 2D sketching (CAD-style profiles)
FILLET_STEP = radians(15)


def fillet2(pts, seg=None, closed=True):
    """polygon / polyline through pts = [(a, b) or (a, b, radius)]; corners with a radius get a tangent arc
    (radius clamped to the neighbouring edge lengths). seg=None -> one segment per 15 deg of arc; a fixed seg
    always emits seg+1 points per rounded corner (lofts need constant counts)."""
    P = [(V((p[0], p[1])), (p[2] if len(p) > 2 else 0.0)) for p in pts]
    n = len(P)
    out = []
    for i in range(n):
        p, r = P[i]
        if r <= 0 or (not closed and (i == 0 or i == n - 1)):
            out.append((p.x, p.y))
            continue
        a, b = P[i - 1][0], P[(i + 1) % n][0]
        u, w = (a - p), (b - p)
        if u.length < 1e-9 or w.length < 1e-9:
            out.append((p.x, p.y))
            continue
        u.normalize()
        w.normalize()
        ang = acos(max(-1.0, min(1.0, u.dot(w))))
        if ang < 1e-3 or ang > pi - 1e-3:
            out += [(p.x, p.y)] * ((seg + 1) if seg else 1)
            continue
        dd = r / tan(ang / 2)
        dd = min(dd, 0.49 * (a - p).length, 0.49 * (b - p).length)
        re = dd * tan(ang / 2)
        t1 = p + u * dd
        bis = (u + w).normalized()
        c = p + bis * (re / sin(ang / 2))
        t2 = p + w * dd
        a1 = atan2(t1.y - c.y, t1.x - c.x)
        a2 = atan2(t2.y - c.y, t2.x - c.x)
        da = a2 - a1
        while da > pi:
            da -= 2 * pi
        while da < -pi:
            da += 2 * pi
        k = seg if seg else max(1, int(ceil(abs(da) / FILLET_STEP)))
        for j in range(k + 1):
            t = a1 + da * j / k
            out.append((c.x + re * cos(t), c.y + re * sin(t)))
    return out


def stadium2(cx, cy, length, width, ang=0.0, n=6):
    """rounded slot (two half circles) centred on (cx, cy), long axis rotated by ang (radians)."""
    r = width / 2
    h = max(0.0, length / 2 - r)
    pts = []
    for k in range(n + 1):
        t = -pi / 2 + pi * k / n
        pts.append((h + r * cos(t), r * sin(t)))
    for k in range(n + 1):
        t = pi / 2 + pi * k / n
        pts.append((-h + r * cos(t), r * sin(t)))
    ca, sa = cos(ang), sin(ang)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def sec(hw_b, hw_t, zb, zt, rb, rt, seg=3, xc=0.0):
    """cross-section (x, z): trapezoid bottom half-width hw_b, top half-width hw_t, filleted corners (CCW)."""
    return fillet2([(xc + hw_b, zb, max(rb, 1e-4)), (xc + hw_t, zt, max(rt, 1e-4)),
                    (xc - hw_t, zt, max(rt, 1e-4)), (xc - hw_b, zb, max(rb, 1e-4))], seg)


def sec6(hw_b, hw_m, hw_t, zb, zm, zt, rb, rm, rt, seg=3):
    """6-corner cross-section (x, z): bottom, widest (shoulder) and top half-widths at three heights."""
    return fillet2([(hw_b, zb, max(rb, 1e-4)), (hw_m, zm, max(rm, 1e-4)), (hw_t, zt, max(rt, 1e-4)),
                    (-hw_t, zt, max(rt, 1e-4)), (-hw_m, zm, max(rm, 1e-4)), (-hw_b, zb, max(rb, 1e-4))], seg)


# ============================================================== 3D builders
def slab(outline_yz, x0, x1):
    """side-profile solid: the (y, z) outline extruded across x0..x1."""
    return prism([V((x0, p[0], p[1])) for p in outline_yz], (x1 - x0, 0, 0))


def plate_xy(outline_xy, z0, z1):
    """top-view solid: the (x, y) outline extruded from z0 to z1."""
    return prism([V((p[0], p[1], z0)) for p in outline_xy], (0, 0, z1 - z0))


def plate_xz(outline_xz, y0, y1):
    """front-view solid: the (x, z) outline extruded from y0 to y1."""
    return prism([V((p[0], y0, p[1])) for p in outline_xz], (0, y1 - y0, 0))


def loft_y(secs, cap0=True, cap1=True):
    """loft (x, z) cross-sections placed at y: secs = [(y, pts)] (equal point counts)."""
    return loft([[V((p[0], y, p[1])) for p in pts] for y, pts in secs], cap0, cap1)


def loft_z(secs, cap0=True, cap1=True):
    """loft (x, y) cross-sections placed at height z: secs = [(z, pts)]."""
    return loft([[V((p[0], p[1], z)) for p in pts] for z, pts in secs], cap0, cap1)


def sweep_yz(path, section, cap0=True, cap1=True):
    """sweep along a path in the YZ plane (x = 0). section(i, s) -> list of (x, u) where u runs along the in-plane
    normal n = (0, -tz, ty) (90 deg left of the travel direction seen from +X). s = 0..1 along the path."""
    P = [V((0.0, p[0], p[1])) for p in path]
    m = len(P)
    acc = [0.0]
    for i in range(1, m):
        acc.append(acc[-1] + (P[i] - P[i - 1]).length)
    loops = []
    for i in range(m):
        if i == 0:
            t = P[1] - P[0]
        elif i == m - 1:
            t = P[-1] - P[-2]
        else:
            t = (P[i + 1] - P[i]).normalized() + (P[i] - P[i - 1]).normalized()
        t.normalize()
        n = V((0.0, -t.z, t.y))
        s = acc[i] / acc[-1]
        loops.append([P[i] + V((q[0], 0, 0)) + n * q[1] for q in section(i, s)])
    return loft(loops, cap0, cap1)


def lathe_y(profile, n=24, cx=0.0, cz=0.0, cap0=True, cap1=True):
    """revolve a (radius, y) profile around the line x = cx, z = cz (parallel to Y)."""
    return orient(lathe_vf([(r, y) for r, y in profile], n, cap0, cap1), (cx, 0, cz), 'Y')


def lathe_axis(profile, n, center, axis, cap0=True, cap1=True):
    """revolve (radius, h) profile around an axis through `center` ('X','Y','Z','-Y'.. or a vector)."""
    return orient(lathe_vf(profile, n, cap0, cap1), center, axis)


def tube_y(r_out, r_in, y0, y1, n=24, cx=0.0, cz=0.0):
    """open-ended thick tube along Y (barrel with a bore)."""
    prof = [(r_in, y0), (r_out, y0), (r_out, y1), (r_in, y1)]
    vf = lathe_vf([(r, y) for r, y in prof] + [(r_in, y0)], n, False, False)
    return orient(vf, (cx, 0, cz), 'Y')


def ring_y(profile, n=24, cx=0.0, cz=0.0, a0=0.0):
    """closed ring solid around Y from a closed (r, y) profile loop (barrel bands, muzzle devices with a bore)."""
    prof = list(profile) + [profile[0]]
    return orient(lathe_vf(prof, n, False, False, a0=a0), (cx, 0, cz), 'Y')


def array_vf(vf, offsets):
    return merge_vf(*[xform_vf(vf, Matrix.Translation(V(o))) for o in offsets])


def rotz_vf(vf, deg, pivot=(0, 0, 0)):
    return rot_about(vf, pivot, 'Z', deg)


def rotx_vf(vf, deg, pivot=(0, 0, 0)):
    return rot_about(vf, pivot, 'X', deg)


def roty_vf(vf, deg, pivot=(0, 0, 0)):
    return rot_about(vf, pivot, 'Y', deg)


def mirror_x(vf):
    return mirror_vf(vf, 0)


def both_sides(vf):
    """geometry built on the +X side plus its mirror on -X."""
    return merge_vf(vf, mirror_x(vf))


# ============================================================== hardware
def _hex12(r):
    return [((r if k % 2 == 0 else r * cos(pi / 6)) * cos(k * pi / 6), (r if k % 2 == 0 else r * cos(pi / 6)) * sin(k * pi / 6))
            for k in range(12)]


def screw_vf(p, nrm, r=0.0042, h=0.0016, sink=0.0010):
    """socket-head screw: round head with a chamfered rim and a real hex socket; sits `sink` into the surface."""
    hx = _hex12(r * 0.45)
    loops = [[(r * cos(k * pi / 6), r * sin(k * pi / 6), -sink) for k in range(12)],
             [(r * cos(k * pi / 6), r * sin(k * pi / 6), h * 0.55) for k in range(12)],
             [(r * 0.82 * cos(k * pi / 6), r * 0.82 * sin(k * pi / 6), h) for k in range(12)],
             [(x, y, h) for x, y in hx],
             [(x, y, h - r * 0.45) for x, y in hx]]
    vf = loft(loops, True, True)
    return orient(vf, p, nrm)


def pin_vf(p, axis, r, length, cham=None):
    """cross pin / axle with chamfered ends, centred on p."""
    c = cham if cham is not None else r * 0.3
    h = length / 2
    prof = [(0, -h), (r - c, -h), (r, -h + c), (r, h - c), (r - c, h), (0, h)]
    return orient(lathe_vf(prof, 12), p, axis)


def pinhead_vf(p, nrm, r, h=0.0012):
    """flush pin end / rivet head: low disc with a domed edge standing h proud."""
    prof = [(0, -0.0015), (r, -0.0015), (r, h * 0.4), (r * 0.8, h), (0, h)]
    return orient(lathe_vf(prof, 12), p, nrm)


def rail_vf(y0, y1, z0, hw=0.0118, h=0.0112, pitch=0.0150, slot_w=0.0078, slot_d=0.0050, name_cut=None):
    """Picatinny-style rail (scaled to the pack): dovetail profile from y0 (front) to y1 (rear) sitting on z0.
    Returns (rail solid, list of slot cutters)."""
    prof = [(hw * 0.93, 0.0), (hw * 0.93, h * 0.30), (hw * 1.36, h * 0.62), (hw, h), (-hw, h), (-hw * 1.36, h * 0.62),
            (-hw * 0.93, h * 0.30), (-hw * 0.93, 0.0)]
    pts = [V((x, y0, z0 + z)) for x, z in prof]
    body = prism(pts, (0, y1 - y0, 0))
    cuts = []
    L_ = abs(y1 - y0)
    k = int((L_ - pitch * 0.6) // pitch)
    start = min(y0, y1) + (L_ - k * pitch) / 2 + pitch / 2
    for i in range(k):
        yc = start + i * pitch
        cuts.append(box_vf((0, yc, z0 + h - slot_d / 2 + 0.003), (hw * 3.2, slot_w, slot_d + 0.006)))
    return body, cuts


def sling_loop_vf(c, axis_dir, r_ring=0.011, r_wire=0.0022, n=16):
    """closed wire loop (sling point) in the plane normal to axis_dir."""
    path = [V((r_ring * cos(2 * pi * k / n), r_ring * sin(2 * pi * k / n), 0)) for k in range(n)]
    vf = sweep_vf(path, circle2(r_wire, 8), closed=True)
    return orient(vf, c, axis_dir)


def grooves_side(y_from, y_to, z_from, z_to, x_face, depth, width, n, along='y'):
    """box cutters for n parallel grooves `depth` deep into BOTH side faces at x = +/-x_face.
    along='y': grooves run along Y, stacked in Z; along='z': grooves run along Z, stacked in Y."""
    out = []
    for sgn in (1, -1):
        for i in range(n):
            t = (i + 0.5) / n
            if along == 'y':
                zc = z_from + (z_to - z_from) * t
                out.append(box_vf((sgn * (x_face + 0.01 - depth / 2), (y_from + y_to) / 2, zc),
                                  (0.02 + depth, abs(y_to - y_from), width)))
            else:
                yc = y_from + (y_to - y_from) * t
                out.append(box_vf((sgn * (x_face + 0.01 - depth / 2), yc, (z_from + z_to) / 2),
                                  (0.02 + depth, width, abs(z_to - z_from))))
    return out


# ============================================================== engraved + paint-filled markings
def _text_raw(body, size, half_t, res=3):
    """text solid (centred, extruded +/- half_t) with a low curve resolution - small engravings need few segments."""
    c = bpy.data.curves.new('_txt', 'FONT')
    c.body = body
    c.size = size
    c.extrude = half_t
    c.align_x = 'CENTER'
    c.align_y = 'CENTER'
    c.resolution_u = res
    c.space_character = 1.08              # the default kerning makes some glyph pairs (R-A) touch -> non-manifold
    o = bpy.data.objects.new('_txt', c)
    bpy.context.scene.collection.objects.link(o)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    vv = [v.co.copy() for v in me.vertices]
    ff = [tuple(p.vertices) for p in me.polygons]
    bpy.data.objects.remove(o)
    bpy.data.curves.remove(c)
    bpy.data.meshes.remove(me)
    return vv, ff


def marking(ob, body, center, face, size, depth=0.0007, fill='MarkRed', up=(0, 0, 1), rot_deg=0.0):
    """engrave `body` into ob's flat face (outward normal `face`, e.g. (-1,0,0) = the weapon's right side) and fill the
    engraving with paint (`fill` material) just below the surface - the faded factory / armoury markings.
    Returns the fill object."""
    f = V(face).normalized()
    u = V(up)
    u = (u - f * u.dot(f)).normalized()
    rgt = u.cross(f)                        # reading direction seen from outside: right = up x out
    M3 = Matrix((rgt, u, f)).transposed()
    rot = Matrix.Rotation(radians(rot_deg), 3, f)
    Mw = (rot @ M3).to_4x4()
    Mw.translation = V(center)
    vv, ff = _text_raw(body, size, depth * 1.6)
    cutter_vf = xform_vf((vv, ff), Mw)
    cut(ob, cutter_vf)
    vv2, ff2 = _text_raw(body, size * 0.995, 0.00012)
    M2 = Mw.copy()
    M2.translation = V(center) - f * (depth * 0.55)
    fill_ob = part(ob.name[len(CUR['code']) + 1:] + '_Marking_' + ''.join(ch for ch in body if ch.isalnum())[:10],
                   xform_vf((vv2, ff2), M2), fill, parent=ob, smooth=False, wn=False)
    return fill_ob


# ============================================================== presentation (separate collection)
PRES = 'PRESENTATION'


def presentation(layout):
    """neutral studio: seamless backdrop + soft key / fill / rim / top lights + cameras.
    layout = {code: (root location, bbox min, bbox max)} after the weapons were placed."""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = -1.1
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    pc = bpy.data.collections.new(PRES)
    sc.collection.children.link(pc)
    w = bpy.data.worlds.new('SW_StudioWorld')
    sc.world = w
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (*lin(150, 152, 156), 1)
    bg.inputs['Strength'].default_value = 0.35
    # bounds of the whole lineup
    mn = V((min(l[1].x for l in layout.values()), min(l[1].y for l in layout.values()), min(l[1].z for l in layout.values())))
    mx = V((max(l[2].x for l in layout.values()), max(l[2].y for l in layout.values()), max(l[2].z for l in layout.values())))
    cen = (mn + mx) / 2
    # seamless backdrop (cyclorama): floor at z = 0 curving up into a wall behind the weapons (+X)
    wall_x = mx.x + 0.9
    R_ = 0.9
    W_ = 14.0
    prof = [(-6.0, 0.0)]
    for k in range(13):
        a = -pi / 2 + (pi / 2) * k / 12
        prof.append((wall_x - R_ + R_ * cos(a) + 0.0, R_ + R_ * sin(a)))
    prof.append((wall_x, 6.0))
    Vs, F = [], []
    for i, (x, z) in enumerate(prof):
        Vs += [V((x, cen.y - W_ / 2, z)), V((x, cen.y + W_ / 2, z))]
    for i in range(len(prof) - 1):
        a = 2 * i
        F.append((a, a + 2, a + 3, a + 1))
    me = bpy.data.meshes.new('Studio_Backdrop')
    me.from_pydata(Vs, [], F)
    me.shade_smooth()
    bd = bpy.data.objects.new('Studio_Backdrop', me)
    pc.objects.link(bd)
    fm = bpy.data.materials.new('Studio_BackdropMat')
    b = fm.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin(104, 106, 108), 1)
    b.inputs['Roughness'].default_value = 0.9
    me.materials.append(fm)

    def area(name, loc, target, energy, size, color=(1, 1, 1), size_y=None):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.color = color
        if size_y:
            ld.shape = 'RECTANGLE'
            ld.size, ld.size_y = size, size_y
        else:
            ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = V(loc)
        d = (V(target) - V(loc)).normalized()
        lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        pc.objects.link(lo)
        return lo
    span = max(mx.y - mn.y, 1.0)
    k = span / 3.0
    area('Light_Key', (cen.x - 3.0 * k, cen.y + 2.2 * k, mx.z + 2.4 * k), cen, 900 * k * k, 3.0 * k, (1.0, 0.96, 0.90))
    area('Light_Fill', (cen.x - 3.4 * k, cen.y - 3.0 * k, cen.z + 0.4 * k), cen, 260 * k * k, 4.0 * k, (0.86, 0.92, 1.0))
    area('Light_Rim', (cen.x + 1.2 * k, cen.y - 0.5 * k, mx.z + 2.0 * k), (cen.x - 0.2, cen.y, cen.z), 650 * k * k,
         4.5 * k, (1.0, 0.98, 0.95), 0.8 * k)
    area('Light_Top', (cen.x - 0.4 * k, cen.y, mx.z + 3.0 * k), cen, 300 * k * k, 5.0 * k)
    return pc


def camera(name, loc, target, lens=50):
    sc = bpy.context.scene
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.02
    cd.clip_end = 200
    co = bpy.data.objects.new(name, cd)
    bpy.data.collections[PRES].objects.link(co)
    co.location = V(loc)
    co.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co
