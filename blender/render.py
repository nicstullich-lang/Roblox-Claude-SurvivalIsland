"""Render views of TX6_Bastion.blend into a contact sheet.

Usage: bpy-run blender/render.py OUT.png view1;view2;... [width] [samples] [pose]
pose: 'rest' (default) or 'deploy'
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from tx6 import lib
from PIL import Image

out = sys.argv[1]
views = sys.argv[2].split(';')
w = int(sys.argv[3]) if len(sys.argv) > 3 else 960
samples = int(sys.argv[4]) if len(sys.argv) > 4 else 32
pose = sys.argv[5] if len(sys.argv) > 5 else 'rest'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'TX6_Bastion.blend'))
sc = bpy.context.scene
sc.render.resolution_x = w
sc.render.resolution_y = int(w * 9 / 16)
sc.cycles.samples = samples
sc.render.threads_mode = 'AUTO'
if pose != 'rest':
    from tx6 import poses
    poses.apply(pose)
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
    p = (out + (name or v) + '.png') if single else '/tmp/tx6_view_%d.png' % len(tmp)
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
