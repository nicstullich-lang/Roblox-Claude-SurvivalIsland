"""Rebuild the TX-6 Bastion from scratch and save TX6_Bastion.blend.

Usage:  bpy-run blender/build.py [stage ...]      (default: all stages)
"""
import sys, os, time, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from tx6 import lib

STAGES = ['body', 'wheels', 'armor', 'bumpers', 'lights', 'roof', 'equipment', 'details', 'interior', 'engine', 'poses']
args = [a for a in sys.argv[1:] if not a.endswith('.py')]
if '--' in sys.argv:
    args = sys.argv[sys.argv.index('--') + 1:]
want = args or STAGES
out = os.path.join(HERE, 'TX6_Bastion.blend')

t0 = time.time()
lib.reset_scene()
for st in STAGES:
    if st not in want:
        continue
    path = os.path.join(HERE, 'tx6', st + '.py')
    if not os.path.exists(path):
        print('skip (missing)', st)
        continue
    mod = importlib.import_module('tx6.' + st)
    t = time.time()
    mod.build()
    print('stage %-10s %5.1fs  objects=%d' % (st, time.time() - t, len(bpy.data.objects)))
lib.clear_scratch()
# store the build scripts inside the .blend as text blocks (like the VX-9 file)
for fn in sorted(os.listdir(os.path.join(HERE, 'tx6'))):
    if fn.endswith('.py'):
        t = bpy.data.texts.get('tx6_' + fn) or bpy.data.texts.new('tx6_' + fn)
        t.from_string(open(os.path.join(HERE, 'tx6', fn)).read())
lib.studio()
lib.setview('front34')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
tris = 0
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('Studio') is False:
        tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
print('saved', out, 'objects', len(bpy.data.objects), 'base tris', tris, 'time %.1fs' % (time.time() - t0))
