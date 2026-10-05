"""Render views of a model's .blend (contact sheet or single files).

Usage: bpy-run blender/render_model.py MODEL OUT.png "view1;view2;..." [width] [samples] [pose]
  MODEL = package name (e.g. xr77); its lib defines MODEL, VIEWS, setview().
  OUT ending in '/' writes one PNG per view. A view can be 'name=((loc),(target),lens)'.
  pose = rest (default) or any pose name from the model's poses module (common.poses channel presets).
"""
import sys, os, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from PIL import Image

pkg = sys.argv[1]
out = sys.argv[2]
views = sys.argv[3].split(';')
w = int(sys.argv[4]) if len(sys.argv) > 4 else 960
samples = int(sys.argv[5]) if len(sys.argv) > 5 else 32
pose = sys.argv[6] if len(sys.argv) > 6 else 'rest'
lib = importlib.import_module(pkg + '.lib')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, lib.MODEL + '.blend'))
sc = bpy.context.scene
sc.render.resolution_x = w
sc.render.resolution_y = int(w * 9 / 16)
sc.cycles.samples = samples
if pose != 'rest':
    import json
    from common import poses
    for o in bpy.context.scene.objects:
        o.animation_data_clear()
    if pose.startswith('{'):
        st = json.loads(pose)
        poses.apply_state(st.get('channels'), st.get('inputs'))
    else:
        poses.apply_pose(pose)
tmp = []
single = out.endswith('/')
for v in views:
    name = None
    if '=' in v:
        name, v = v.split('=', 1)
    if v.startswith('('):
        loc, tgt, lens = eval(v)
        lib.setview(None, loc, tgt, lens)
    else:
        lib.setview(v)
    fl = bpy.data.objects.get('Studio_Floor')
    if fl:
        fl.hide_render = (name or v).startswith('bottom') or (name or v).startswith('under')
    p = (out + (name or v) + '.png') if single else '/tmp/_view_%d.png' % len(tmp)
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
