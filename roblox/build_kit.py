"""Generate roblox/src/TX6/RigData.luau from the Blender model and pack the Roblox kit into roblox/TX6_Kit.rbxmx.

Usage: bpy-run roblox/build_kit.py
(needs Blender's bpy only to read the material table + measure the model; everything else is plain Python)
"""
import sys, os, json, re
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'blender'))
import bpy
from mathutils import Vector
from tx6 import lib

S = 1 / 0.28
rig = json.load(open(os.path.join(REPO, 'exports', 'TX6_Bastion_Rig.json')))


def rb(v):
    """Blender metres (x, y, z) -> Roblox studs (-x, z, y)."""
    x, y, z = v
    return (-x * S, z * S, y * S)


def v3(t):
    return 'Vector3.new(%.4f, %.4f, %.4f)' % tuple(0.0 if abs(c) < 5e-5 else c for c in t)


# --------------------------------------------------------------------------------------- joints + drives
CHANNEL = {
    'Deploy_WindshieldShield': ('Armor', 0.0, 0.75),
    'Deploy_Shutter_FL': ('Armor', 0.2, 0.95), 'Deploy_Shutter_FR': ('Armor', 0.2, 0.95),
    'Deploy_Shutter_RL': ('Armor', 0.3, 1.0), 'Deploy_Shutter_RR': ('Armor', 0.3, 1.0),
    'Missile_Hatch_L': ('Missiles', 0.0, 0.35), 'Missile_Hatch_R': ('Missiles', 0.0, 0.35),
    'Missile_Lift_L': ('Missiles', 0.35, 0.7), 'Missile_Lift_R': ('Missiles', 0.35, 0.7),
    'Missile_Pod_L': ('Missiles', 0.7, 1.0), 'Missile_Pod_R': ('Missiles', 0.7, 1.0),
    'Sensor_Mast': ('Mast', 0.0, 0.55), 'Sensor_MastUpper': ('Mast', 0.55, 0.85), 'Sensor_EOBall': ('Mast', 0.85, 1.0),
    'Door_FL': ('Door_FL', 0, 1), 'Door_FR': ('Door_FR', 0, 1), 'Door_RL': ('Door_RL', 0, 1), 'Door_RR': ('Door_RR', 0, 1),
    'Spare_Carrier': ('Rear', 0.0, 0.5), 'Door_Rear': ('Rear', 0.35, 1.0),
    'Locker_Door_L': ('Locker_L', 0.0, 0.7), 'Locker_Tray_L': ('Locker_L', 0.6, 1.0), 'Locker_Door_R': ('Locker_R', 0, 1),
    'Fuel_Door_L': ('Fuel', 0, 1), 'Utility_Hatch_R': ('Utility', 0, 1), 'Hood': ('Hood', 0, 1),
}
MANUAL = {'Hood': ('rot', 'X', -55.0)}          # hood isn't in the keyed timeline


def to_roblox(kind, axis, amt):
    """Blender local motion -> Roblox local motion (proper rotation (x,y,z)->(-x,z,y): angles keep their size)."""
    if kind == 'rot':
        return {'X': ('rot', 'X', -amt), 'Y': ('rot', 'Z', amt), 'Z': ('rot', 'Y', amt)}[axis]
    return {'X': ('loc', 'X', -amt * S), 'Y': ('loc', 'Z', amt * S), 'Z': ('loc', 'Y', amt * S)}[axis]


joints = {}
for name, g in rig['groups'].items():
    piv = g['pivot_studs']
    parent = g['parent_group']
    drive = None
    m = re.match(r'(rot|loc) ([XYZ]) ([+-]?[0-9.]+)', g.get('deploy_key', ''))
    spec = MANUAL.get(name) or ((m.group(1), m.group(2), float(m.group(3))) if m else None)
    if name in CHANNEL and spec:
        k, a, amt = to_roblox(*spec)
        ch, t0, t1 = CHANNEL[name]
        drive = (ch, t0, t1, k, a, amt)
    physics = 'Strut' if name.startswith('Upright_') else ('Wheel' if name.startswith('Wheel_') else None)
    joints[name] = dict(pivot=piv, parent=parent, drive=drive, physics=physics)


def depth(n):
    d = 0
    while joints[n]['parent'] in joints:
        n = joints[n]['parent']
        d += 1
    return d


order = sorted(joints, key=lambda n: (depth(n), n))

# --------------------------------------------------------------------------------------- points (Blender metres)
P = {
    'Muzzle': (0, -1.325, 2.96),
    'PodTube_L': (0.67, 1.32, 2.24), 'PodTube_R': (-0.67, 1.32, 2.24),
    'HeadlightL': (0.88, -3.03, 1.28), 'HeadlightR': (-0.88, -3.03, 1.28),
    'LightBar': (0, -0.73, 2.585),
    'Beacon1': (0.86, -0.63, 2.60), 'Beacon2': (-0.86, -0.63, 2.60), 'Beacon3': (0.86, 2.78, 2.60), 'Beacon4': (-0.86, 2.78, 2.60),
    'SearchlightLamp': (-0.80, -0.46, 2.68),
    'Dome': (0, -0.57, 2.37),
    'TailL': (1.03, 3.27, 0.67), 'TailR': (-1.03, 3.27, 0.67),
    'RearClusterL': (0.96, 3.02, 2.18), 'RearClusterR': (-0.96, 3.02, 2.18),
    'Horn': (0, -2.2, 1.2),
    'P_DriverDoor': (1.34, -0.35, 1.15), 'P_PassengerDoor': (-1.34, -0.35, 1.15),
    'P_RearLeftDoor': (1.34, 0.60, 1.15), 'P_RearRightDoor': (-1.34, 0.60, 1.15),
    'P_Rear': (0.30, 3.32, 1.25), 'P_LockerL': (1.32, 1.85, 1.95), 'P_LockerR': (-1.32, 1.85, 1.95),
    'P_Hood': (0, -3.32, 1.50), 'P_Fuel': (1.26, 2.68, 1.96),
    'Exit_Driver': (2.05, -0.55, 0.95), 'Exit_Passenger': (-2.05, -0.55, 0.95),
    'Exit_RearL': (2.05, 0.50, 0.95), 'Exit_RearR': (-2.05, 0.50, 0.95), 'Exit_Gunner': (2.05, 1.60, 0.95),
}
BOXES = [  # name, Blender min, max (metres)
    ('HullLower', (-1.22, -3.0, 0.62), (1.22, 3.0, 1.62)),
    ('Cabin', (-1.12, -0.78, 1.62), (1.12, 2.95, 2.48)),
    ('Cowl', (-1.15, -1.13, 1.62), (1.15, -0.78, 2.0)),
    ('BumperFront', (-1.34, -3.30, 0.50), (1.34, -3.0, 0.94)),
    ('RearBlock', (-1.30, 3.0, 0.52), (1.30, 3.52, 2.05)),
    ('Turret', (-0.75, -0.45, 2.48), (0.75, 1.05, 3.24)),
    ('Underbody', (-1.38, -1.15, 0.46), (1.38, 1.0, 0.62)),
]


def box_rb(mn, mx):
    a, b = rb(mn), rb(mx)
    lo = tuple(min(p, q) for p, q in zip(a, b))
    hi = tuple(max(p, q) for p, q in zip(a, b))
    return tuple((p + q) / 2 for p, q in zip(lo, hi)), tuple(q - p for p, q in zip(lo, hi))


# --------------------------------------------------------------------------------------- expected import bounds
bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, 'blender', 'TX6_Bastion.blend'))
bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
mn = Vector((1e9, 1e9, 1e9))
mx = -mn
for o in bpy.context.scene.objects:
    if o.type != 'MESH' or o.name.startswith('Studio'):
        continue
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    for v in me.vertices:
        w = o.matrix_world @ v.co
        mn = Vector(map(min, mn, w))
        mx = Vector(map(max, mx, w))
    ev.to_mesh_clear()
imp_center, imp_size = box_rb(tuple(mn), tuple(mx))

# --------------------------------------------------------------------------------------- materials
RMAT = {
    'Paint': 'SmoothPlastic', 'ArmorPaint': 'SmoothPlastic', 'PaintDark': 'SmoothPlastic', 'Coating': 'Plastic',
    'Hardware': 'Metal', 'Steel': 'Metal', 'Alu': 'Metal', 'Gunmetal': 'Metal', 'Rubber': 'Rubber', 'Tire': 'Rubber',
    'Rim': 'Metal', 'Glass': 'Glass', 'GlassDark': 'Glass', 'Lens': 'Glass', 'LED': 'Neon', 'LEDOff': 'SmoothPlastic',
    'Amber': 'Neon', 'RedLens': 'Neon', 'IRLens': 'Glass', 'Mesh': 'Metal', 'SafetyRed': 'SmoothPlastic',
    'Hazard': 'SmoothPlastic', 'Canvas': 'Fabric', 'Wood': 'Wood', 'Plastic': 'SmoothPlastic', 'Fabric': 'Fabric',
    'Screen': 'Neon', 'ScreenBlue': 'Neon', 'Missile': 'SmoothPlastic', 'Engine': 'Metal', 'Copper': 'Metal',
    'Brass': 'Metal', 'Exhaust': 'Metal', 'Floor': 'Plastic', 'Rope': 'Fabric', 'Housing': 'SmoothPlastic',
    'Stencil': 'SmoothPlastic', 'ExtRed': 'SmoothPlastic',
}
OVERRIDE = {  # name: (rgb, transparency, reflectance)
    'LED': ((235, 240, 255), 0, 0), 'Amber': ((255, 140, 25), 0, 0), 'RedLens': ((255, 35, 25), 0, 0),
    'Screen': ((60, 230, 120), 0, 0), 'ScreenBlue': ((40, 150, 255), 0, 0),
    'Glass': ((120, 150, 145), 0.5, 0.1), 'GlassDark': ((20, 24, 26), 0.25, 0.1), 'Lens': ((220, 225, 230), 0.6, 0.1),
    'IRLens': ((40, 6, 8), 0.15, 0.05), 'Steel': ((150, 150, 148), 0, 0.05), 'Alu': ((185, 188, 192), 0, 0.08),
    'Brass': ((190, 150, 70), 0, 0.05),
}


def srgb(c):
    c = max(0.0, min(1.0, c))
    s = c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return int(round(s * 255))


mats = {}
for name, (col, rough, metal, ex) in lib.MATS.items():
    rgb = tuple(srgb(c) for c in col)
    tr, rf = 0, 0
    if name in OVERRIDE:
        rgb, tr, rf = OVERRIDE[name]
    mats[name] = (RMAT.get(name, 'SmoothPlastic'), rgb, tr, rf)
LIGHT_OFF = {'LED': ('SmoothPlastic', (150, 155, 160)), 'Amber': ('SmoothPlastic', (140, 72, 18)),
             'RedLens': ('SmoothPlastic', (95, 12, 10))}

# --------------------------------------------------------------------------------------- write RigData.luau
L = ['--!nonstrict', '-- GENERATED by roblox/build_kit.py from the Blender model - do not edit by hand.',
     '-- Vehicle space: studs, origin on the ground under the vehicle centre, nose = -Z, vehicle right = +X.', '',
     'local Rig = {}', 'Rig.S = %.10f -- studs per metre' % S]
L.append('Rig.ImportCenter = %s' % v3(imp_center))
L.append('Rig.ImportSize = %s' % v3(imp_size))
L.append('Rig.ChassisCenter = Vector3.new(0, 2.95, 0)')
L.append('Rig.ChassisSize = Vector3.new(8, 1.4, 19)')
L.append('Rig.WheelRadius = %.4f' % (0.60 * S))
L.append('Rig.WheelWidth = %.4f' % (0.44 * S))
L.append('Rig.SpringTop = 3')
L.append('')
L.append('Rig.Joints = {')
for n in order:
    j = joints[n]
    parts = ['Pivot = %s' % v3(j['pivot']), 'Parent = "%s"' % j['parent']]
    if j['drive']:
        ch, t0, t1, k, a, amt = j['drive']
        parts.append('Drive = { Channel = "%s", T0 = %g, T1 = %g, Kind = "%s", Axis = "%s", Amount = %.4f }'
                     % (ch, t0, t1, k, a, amt))
    if j['physics']:
        parts.append('Physics = "%s"' % j['physics'])
    L.append('\t%s = { %s },' % (n, ', '.join(parts)))
L.append('}')
L.append('Rig.JointOrder = { %s }' % ', '.join('"%s"' % n for n in order))
L.append('')
L.append('Rig.Wheels = {')
for tag in ('FL', 'FR', 'RL', 'RR'):
    L.append('\t%s = { Center = %s, Steer = %s, Side = %d },' % (tag, v3(joints['Upright_' + tag]['pivot']),
                                                               'true' if tag[0] == 'F' else 'false',
                                                               1 if tag[1] == 'R' else -1))
L.append('}')
L.append('')
seat_names = {'Seat_Driver': 'DriverSeat', 'Seat_Passenger': 'PassengerSeat', 'Seat_RearL': 'RearLeftSeat',
              'Seat_RearR': 'RearRightSeat', 'Seat_Gunner': 'GunnerSeat'}
L.append('Rig.Seats = {')
for k, v in rig['seats'].items():
    L.append('\t%s = { Position = %s, Role = "%s" },' % (seat_names[k], v3(v['position_studs']), v['role']))
L.append('}')
L.append('')
L.append('Rig.Points = {')
for k, v in P.items():
    L.append('\t%s = %s,' % (k, v3(rb(v))))
L.append('}')
L.append('')
L.append('Rig.Collision = {')
for name, a, b in BOXES:
    c, s = box_rb(a, b)
    L.append('\t{ Name = "%s", Center = %s, Size = %s },' % (name, v3(c), v3(s)))
L.append('}')
L.append('')
L.append('Rig.Materials = {')
for name in sorted(mats):
    m, rgb, tr, rf = mats[name]
    L.append('\t%s = { Material = "%s", Color = Color3.fromRGB(%d, %d, %d), Transparency = %g, Reflectance = %g },'
             % (name, m, *rgb, tr, rf))
L.append('}')
L.append('Rig.LightOff = {')
for name, (m, rgb) in LIGHT_OFF.items():
    L.append('\t%s = { Material = "%s", Color = Color3.fromRGB(%d, %d, %d) },' % (name, m, *rgb))
L.append('}')
L.append('')
L.append('return Rig')
os.makedirs(os.path.join(HERE, 'src', 'TX6'), exist_ok=True)
open(os.path.join(HERE, 'src', 'TX6', 'RigData.luau'), 'w').write('\n'.join(L) + '\n')
print('RigData.luau written: %d joints, import size %s' % (len(joints), tuple(round(c, 2) for c in imp_size)))

# --------------------------------------------------------------------------------------- pack the .rbxmx kit
KIT = [  # (folder in kit, class, name, source file)
    ('', 'ModuleScript', 'Install', 'Install.luau'),
    ('Shared', 'ModuleScript', 'Config', 'TX6/Config.luau'),
    ('Shared', 'ModuleScript', 'RigData', 'TX6/RigData.luau'),
    ('Shared', 'ModuleScript', 'Shared', 'TX6/Shared.luau'),
    ('Server', 'Script', 'TX6_Spawner', 'Server/TX6_Spawner.server.luau'),
    ('Client', 'LocalScript', 'TX6_Visuals', 'Client/TX6_Visuals.client.luau'),
    ('Client', 'LocalScript', 'TX6_SpawnClient', 'Client/TX6_SpawnClient.client.luau'),
    ('Vehicle', 'Script', 'TX6_Server', 'Vehicle/TX6_Server.server.luau'),
    ('Vehicle', 'LocalScript', 'TX6_DriverClient', 'Vehicle/TX6_DriverClient.client.luau'),
    ('Vehicle', 'LocalScript', 'TX6_GunnerClient', 'Vehicle/TX6_GunnerClient.client.luau'),
]
ref = [0]


def nref():
    ref[0] += 1
    return 'RBX%08X' % ref[0]


def item(cls, name, src=None, children=''):
    props = '<string name="Name">%s</string>' % escape(name)
    if src is not None:
        assert ']]>' not in src, 'source contains ]]> which would break CDATA'
        props += '<ProtectedString name="Source"><![CDATA[%s]]></ProtectedString>' % src
    return '<Item class="%s" referent="%s"><Properties>%s</Properties>%s</Item>' % (cls, nref(), props, children)


folders = {}
top = []
for folder, cls, name, path in KIT:
    fp = os.path.join(HERE, 'src', path)
    if not os.path.exists(fp):
        print('WARNING: missing', path)
        continue
    src = open(fp).read()
    x = item(cls, name, src)
    if folder:
        folders.setdefault(folder, []).append(x)
    else:
        top.append(x)
readme = open(os.path.join(HERE, 'README.md')).read() if os.path.exists(os.path.join(HERE, 'README.md')) else ''
body = ''.join(top) + ''.join(item('Folder', f, None, ''.join(xs)) for f, xs in folders.items())
body += '<Item class="StringValue" referent="%s"><Properties><string name="Name">README</string>' \
        '<string name="Value">%s</string></Properties></Item>' % (nref(), escape(readme))
xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
       'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4"><External>null</External>'
       '<External>nil</External>' + item('Folder', 'TX6_Kit', None, body) + '</roblox>')
open(os.path.join(HERE, 'TX6_Kit.rbxmx'), 'w').write(xml)
print('TX6_Kit.rbxmx written (%d bytes, %d scripts)' % (len(xml), len(KIT)))
