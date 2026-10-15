"""Render views of the weapon pack.

Usage: bpy-run blender/render_weapons.py BLEND OUT "view;view;..." [width] [samples] [pose-json]
  view = lineup | CODE:34 | CODE:rear34 | CODE:right | CODE:left | CODE:top | CODE:under | CODE:front |
         CODE:rear | CODE:(dx,dy,dz)[,lens][,(tx,ty,tz)]   (offsets relative to the weapon centre, in weapon lengths)
         prefix 'name=' to name the output file.
  OUT ending in '/' writes one PNG per view, else a 2-column contact sheet.
  pose-json: {"channels": {...}, "inputs": {...}} applied to every weapon (rig channel names).
Close-ups hide the other weapons; 'under' views hide the backdrop.
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
from PIL import Image

blend, out, views = sys.argv[1], sys.argv[2], sys.argv[3].split(';')
w = int(sys.argv[4]) if len(sys.argv) > 4 else 960
samples = int(sys.argv[5]) if len(sys.argv) > 5 else 32
pose = json.loads(sys.argv[6]) if len(sys.argv) > 6 else None
bpy.ops.wm.open_mainfile(filepath=blend)
from weapons import lib
from common import poses
sc = bpy.context.scene
sc.render.resolution_x = w
sc.render.resolution_y = int(w * 9 / 16)
sc.cycles.samples = samples
for o in sc.objects:
    o.animation_data_clear()
if pose:
    poses.apply_state(pose.get('channels'), pose.get('inputs'))
codes = [c for c in lib.ORDER if bpy.data.collections.get(lib.WEAPONS[c][0])]
cam = bpy.data.objects.new('CAM_Render', bpy.data.cameras.new('CAM_Render'))   # free camera for close-ups
sc.collection.objects.link(cam)
cam.data.clip_start = 0.01


def bounds(code):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in bpy.data.collections[lib.WEAPONS[code][0]].all_objects
           if o.type == 'MESH' and not o.hide_render for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)])
    mx = Vector([max(p[i] for p in pts) for i in range(3)])
    return mn, mx


PRESET = {'34': (-1.25, -0.72, 0.48), 'rear34': (-1.15, 0.85, 0.45), 'right': (-1.85, 0.0, 0.05),
          'left': (1.85, 0.0, 0.05), 'top': (0.0, 0.0, 1.85), 'under': (-0.25, 0.0, -1.8), 'front': (-0.40, -1.7, 0.18),
          'rear': (-0.35, 1.7, 0.22), 'left34': (1.25, -0.72, 0.48), 'left_rear34': (1.15, 0.85, 0.45)}
tmp = []
single = out.endswith('/')
bd = bpy.data.objects.get('Studio_Backdrop')
for v in views:
    name = None
    if '=' in v:
        name, v = v.split('=', 1)
    for c in codes:
        bpy.data.collections[lib.WEAPONS[c][0]].hide_render = False
    if bd:
        bd.hide_render = False
    if v == 'lineup':
        sc.camera = bpy.data.objects['CAM_Lineup']
        tag = 'lineup'
    else:
        code, spec = v.split(':', 1)
        for c in codes:
            bpy.data.collections[lib.WEAPONS[c][0]].hide_render = c != code
        mn, mx = bounds(code)
        cc = (mn + mx) / 2
        L = max(mx.y - mn.y, (mx.z - mn.z) * 2.25)       # framing size: long guns by length, the pistol by height
        lens = 50
        tgt = cc
        if spec in PRESET:
            off = Vector(PRESET[spec])
        else:
            parts_ = eval('(' + spec + ',)') if not spec.startswith('((') else eval(spec)
            off = Vector(parts_[0])
            if len(parts_) > 1:
                lens = parts_[1]
            if len(parts_) > 2:
                tgt = cc + Vector(parts_[2]) * L
        if (spec == 'under' or off.x > 0.3) and bd:      # views from below / from the left side (+X) look through
            bd.hide_render = True                          # where the backdrop is: use the plain studio world
        cam.location = cc + off * L
        d = (tgt - cam.location).normalized()
        up = 'Y' if abs(d.z) < 0.95 else 'Z'
        cam.rotation_euler = d.to_track_quat('-Z', 'Y' if up == 'Y' else 'X').to_euler()
        if abs(d.z) >= 0.95:
            # straight down / up: keep the weapon horizontal in the frame (muzzle to the right)
            from mathutils import Matrix
            f = d
            u = Vector((-1, 0, 0)) if d.z < 0 else Vector((1, 0, 0))
            y = (u - f * u.dot(f)).normalized()
            x = y.cross(-f)
            cam.rotation_euler = Matrix((x, y, -f)).transposed().to_euler()
        cam.data.lens = lens
        sc.camera = cam
        tag = v.replace(':', '_').replace('(', '').replace(')', '').replace(',', '_').replace(' ', '')[:40]
    p = (out + (name or tag) + '.png') if single else '/tmp/_wview_%d.png' % len(tmp)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    tmp.append(p)
if single:
    print('wrote', len(tmp), 'images to', out)
    sys.exit(0)
ims = [Image.open(p) for p in tmp]
cols = 1 if len(ims) == 1 else 2
rows = (len(ims) + cols - 1) // cols
W, H = ims[0].size
sheet = Image.new('RGB', (W * cols, H * rows), (30, 30, 30))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * W, (i // cols) * H))
sheet.save(out)
print('wrote', out)
