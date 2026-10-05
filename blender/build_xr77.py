"""Rebuild the XR-77 "Umbra" from scratch and save XR77_Umbra.blend.

Usage:  bpy-run blender/build_xr77.py [stage ...]      (default: all stages)
"""
import sys, os, time, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from xr77 import lib

STAGES = ['airframe', 'cockpit', 'engines', 'vtol', 'gear', 'weapons', 'sensors', 'defense', 'controls', 'details', 'rigdata']
args = [a for a in sys.argv[1:] if not a.endswith('.py')]
want = args or STAGES
out = os.path.join(HERE, 'XR77_Umbra.blend')

t0 = time.time()
lib.reset_scene()
for st in STAGES:
    if st not in want:
        continue
    mod = importlib.import_module('xr77.' + st)
    t = time.time()
    mod.build()
    print('stage %-10s %5.1fs  objects=%d' % (st, time.time() - t, len(bpy.data.objects)), flush=True)
lib.clear_scratch()
for fn in sorted(os.listdir(os.path.join(HERE, 'xr77'))):
    if fn.endswith('.py'):
        t = bpy.data.texts.get('xr77_' + fn) or bpy.data.texts.new('xr77_' + fn)
        t.from_string(open(os.path.join(HERE, 'xr77', fn)).read())
for fn in ('geo.py', 'rig.py', 'handoff.py', 'poses.py'):
    p = os.path.join(HERE, 'common', fn)
    if os.path.exists(p):
        t = bpy.data.texts.get('common_' + fn) or bpy.data.texts.new('common_' + fn)
        t.from_string(open(p).read())
lib.studio(25.0)
lib.setview('front34')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
tris = 0
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.name.startswith('Studio'):
        tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
print('saved', out, 'objects', len(bpy.data.objects), 'base tris', tris, 'time %.1fs' % (time.time() - t0))
