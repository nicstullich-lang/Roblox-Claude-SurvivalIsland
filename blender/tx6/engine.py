"""TX-6 Bastion - engine bay: 6.7 L-class turbo-diesel V8 (visual), radiator pack + fan, snorkel air box,
batteries, reservoirs. Visible through the grille and with the hood open."""
from tx6.lib import *


def build():
    # radiator pack behind the armoured grille
    rad = [box_between((-0.45, -2.76, 0.80), (0.45, -2.70, 1.42))]
    tanks = [box_between((sx * 0.45, -2.77, 0.78), (sx * 0.40, -2.69, 1.44)) for sx in (1, -1)]
    mk('Eng_RadiatorCore', merge_vf(*rad), 'Mesh', 'Engine')
    mk('Eng_RadiatorTanks', merge_vf(*tanks), 'Alu', 'Engine', bev=(0.004, 1, 30))
    shroud = lathe_vf([(0.27, 0.0), (0.29, 0.0), (0.29, 0.10), (0.27, 0.10), (0.27, 0.0)], 32, False, False)
    mk('Eng_FanShroud', merge_vf(orient(shroud, (0, -2.69, 1.11), (0, 1, 0)),
                                 box_between((-0.40, -2.70, 0.82), (0.40, -2.68, 1.40))), 'Plastic', 'Engine')
    fan = [cyl_vf(V((0, -2.62, 1.11)), 0.06, 0.06, 'Y', 16), cyl_between(V((0, -2.62, 1.11)), V((0, -2.44, 1.11)), 0.035, 12)]
    for k in range(7):
        a = 2 * pi * k / 7
        fan.append(xform_vf(box_vf((0.15, 0, 0), (0.20, 0.008, 0.07)),
                            Matrix.Translation((0, -2.62, 1.11)) @ Matrix.Rotation(a, 4, 'Y') @ Matrix.Rotation(radians(25), 4, 'X')))
    mk('Eng_Fan', merge_vf(*fan), 'Plastic', 'Engine')
    # V8 block + banks + valve covers + plenum
    blk = [box_between((-0.27, -2.45, 0.72), (0.27, -1.62, 1.05)), box_between((-0.24, -2.40, 0.62), (0.24, -1.70, 0.72)),
           box_between((-0.22, -2.47, 0.75), (0.22, -2.44, 1.26))]
    for sx in (1, -1):
        bank = xform_vf(box_vf((0, 0, 0), (0.22, 0.78, 0.30)),
                        Matrix.Translation((sx * 0.20, -2.03, 1.17)) @ Matrix.Rotation(radians(-sx * 35), 4, 'Y'))
        blk.append(bank)
    mk('Eng_Block', merge_vf(*blk), 'Engine', 'Engine', bev=(0.008, 1, 30))
    vc = []
    for sx in (1, -1):
        vc.append(xform_vf(box_vf((0, 0, 0), (0.17, 0.74, 0.07)),
                           Matrix.Translation((sx * 0.29, -2.03, 1.32)) @ Matrix.Rotation(radians(-sx * 35), 4, 'Y')))
    mk('Eng_ValveCovers', merge_vf(*vc), 'Coating', 'Engine', bev=(0.01, 2, 30))
    mk('Eng_Plenum', merge_vf(box_between((-0.14, -2.38, 1.22), (0.14, -1.68, 1.40)),
                              cyl_between(V((0, -2.38, 1.33)), V((0, -2.52, 1.33)), 0.07, 16)), 'Alu', 'Engine',
       bev=(0.01, 2, 30))
    # twin turbos (rear of the engine) + intake + exhaust manifolds
    for sx in (1, -1):
        c = V((sx * 0.30, -1.55, 1.05))
        turbo = [orient(lathe_vf([(0, -0.05), (0.09, -0.05), (0.11, 0.0), (0.09, 0.05), (0, 0.05)], 20), c, 'X'),
                 cyl_between(c, c + V((0, 0, 0.20)), 0.045, 12)]
        mk('Eng_Turbo' + ('L' if sx > 0 else 'R'), merge_vf(*turbo), 'Exhaust', 'Engine')
        mani = tube_vf([V((sx * 0.30, -2.35, 1.00)), V((sx * 0.34, -2.00, 0.98)), V((sx * 0.33, -1.65, 1.00)), c], 0.035, 10)
        mk('Eng_Manifold' + ('L' if sx > 0 else 'R'), mani, 'Exhaust', 'Engine')
    # snorkel air box (right fender) + intake hose to the turbo
    mk('Eng_AirBox', box_between((-1.12, -1.62, 1.39), (-0.76, -1.28, 1.55)), 'Plastic', 'Engine', bev=(0.015, 2, 30))
    mk('Eng_IntakeHose', tube_vf([V((-0.77, -1.45, 1.45)), V((-0.55, -1.45, 1.40)), V((-0.38, -1.52, 1.28)),
                                  V((-0.30, -1.55, 1.25))], 0.05, 12), 'Rubber', 'Engine')
    # batteries (left fender), coolant reservoir, washer tank, fuse box
    for k in range(2):
        mk('Eng_Battery%d' % k, merge_vf(box_between((0.62, -2.30 + 0.27 * k, 1.38), (0.92, -2.06 + 0.27 * k, 1.53)),
                                         cyl_vf(V((0.68, -2.24 + 0.27 * k, 1.545)), 0.015, 0.03, 'Z', 8),
                                         cyl_vf(V((0.86, -2.24 + 0.27 * k, 1.545)), 0.015, 0.03, 'Z', 8)), 'Plastic',
           'Engine', bev=(0.004, 1, 30))
    mk('Eng_Coolant', merge_vf(box_between((0.62, -1.68, 1.38), (0.86, -1.45, 1.52)),
                               cyl_vf(V((0.74, -1.56, 1.535)), 0.035, 0.03, 'Z', 12)), 'Lens', 'Engine')
    mk('Eng_FuseBox', box_between((-0.95, -2.40, 1.355), (-0.70, -2.10, 1.50)), 'Plastic', 'Engine', bev=(0.008, 1, 30))
    mk('Eng_BatteryTray', box_between((0.60, -2.32, 1.355), (0.94, -1.77, 1.38)), 'Hardware', 'Engine')
    mk('Eng_CoolantBracket', merge_vf(box_between((0.86, -1.60, 1.42), (1.17, -1.53, 1.44)),
                                      box_between((0.62, -1.68, 1.365), (0.86, -1.45, 1.38))), 'Hardware', 'Engine')
    # hood inner stiffener frame (moves with the hood)
    hood = bpy.data.objects['Hood']
    ribs = []
    for x in (-0.70, -0.25, 0.25, 0.70):
        ribs.append(box_between((x - 0.025, -2.80, 1.50), (x + 0.025, -1.26, 1.545)))
    for y in (-2.70, -2.00, -1.32):
        ribs.append(box_between((-0.92, y - 0.025, 1.50), (0.92, y + 0.025, 1.545)))
    mk('Hood_InnerFrame', merge_vf(*ribs), 'PaintDark', 'Engine', hood, bev=(0.004, 1, 30))
