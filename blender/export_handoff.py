"""Export a rig-tagged model as a Roblox handoff package.

Usage: bpy-run blender/export_handoff.py MODEL [--no-renders]      (MODEL = package, e.g. xr77)
Writes exports/<ModelName>/<ModelName>.fbx, <ModelName>_Rig.json, HANDOFF.md and previews/*.png
(see docs/MODEL_HANDOFF_STANDARD.md).
"""
import sys, os, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from common import handoff

pkg = sys.argv[1]
lib = importlib.import_module(pkg + '.lib')
repo = os.path.dirname(HERE)
rig = handoff.export(repo, os.path.join(HERE, lib.MODEL + '.blend'), renders='--no-renders' not in sys.argv,
                     mat_prefix=lib.PREFIX)
v = rig['verification']
print('VERIFICATION', 'PASSED' if v['passed'] else 'FAILED', v)
