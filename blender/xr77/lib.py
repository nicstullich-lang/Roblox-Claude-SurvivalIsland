"""XR-77 "Umbra" - classified strike-reconnaissance VTOL fighter (original design, admin-only game aircraft).

Shared library for the XR-77 build: materials, key dimensions and the mathematical shape of the airframe.

Blender 5.2 (PyPI bpy). Units: metres. Z up, the aircraft's NOSE points to -Y.
Aircraft LEFT (pilot's left) = +X (suffix _L), RIGHT = -X (suffix _R) - true sides, same as the TX-6.

Layout (top view, y in metres):
  -12.40 radome tip | -10.60 radar bulkhead | -9.3..-5.15 one-piece canopy | -4.45..-2.50 lift-fan door
  -4.60 inlet lips (spikes reach -6.0) | -1.80 engine fan faces | -1.6..4.0 main weapon bays
  3.40 main gear | 5.05 belly gun turret | 7.40 wing trailing edge | 8.95 nacelle end, swivel nozzles to ~10.95
  10.85 tail cone, decoy stinger to ~11.5
"""
import bpy
from math import sin, cos, tan, pi, radians, sqrt
from mathutils import Vector, Matrix
from common.geo import *          # noqa: F401,F403  (shared toolkit)
from common import geo

V = Vector
PREFIX = 'XR77_'
MODEL = 'XR77_Umbra'
ROOT_NAME = 'XR77_Root'


def R(material, rgb, transparency=0.0, reflectance=0.0):
    """explicit Roblox look for a material (used by the handoff exporter)."""
    return {'roblox_material': material, 'color_rgb': list(rgb), 'transparency': transparency,
            'reflectance': reflectance, 'emissive': material == 'Neon'}


# ============================================================== materials
# name: (base colour linear, roughness, metallic, extras)
MATS = {
    # ---- exterior coatings (stealth composite, patchwork of slightly different panel tones like real LO jets)
    'Skin':        ((0.030, 0.033, 0.039), 0.52, 0.0, {'vary': 0.10, 'bump': 0.10, 'roblox': R('SmoothPlastic', (54, 57, 63))}),
    'SkinAlt':     ((0.040, 0.043, 0.050), 0.47, 0.0, {'vary': 0.09, 'bump': 0.10, 'roblox': R('SmoothPlastic', (64, 67, 73))}),
    'SkinDark':    ((0.015, 0.016, 0.018), 0.66, 0.0, {'vary': 0.08, 'roblox': R('SmoothPlastic', (33, 34, 37))}),
    'Stencil':     ((0.075, 0.080, 0.088), 0.60, 0.0, {'roblox': R('SmoothPlastic', (92, 96, 102))}),
    'Titanium':    ((0.38, 0.37, 0.36), 0.34, 1.0, {'vary': 0.15, 'roblox': R('Metal', (122, 120, 117))}),
    'BurntTi':     ((0.20, 0.15, 0.18), 0.40, 1.0, {'vary': 0.25, 'roblox': R('Metal', (92, 74, 88))}),
    'Inconel':     ((0.26, 0.20, 0.15), 0.48, 1.0, {'vary': 0.20, 'roblox': R('Metal', (112, 92, 74))}),
    'Ceramic':     ((0.045, 0.041, 0.038), 0.86, 0.0, {'bump': 0.5, 'vary': 0.12, 'roblox': R('Slate', (52, 48, 45))}),
    'Exhaust':     ((0.035, 0.032, 0.030), 0.70, 0.6, {'vary': 0.2, 'roblox': R('Metal', (44, 41, 39))}),
    'Carbon':      ((0.018, 0.018, 0.020), 0.30, 0.0, {'weave': 320, 'coat': 0.6, 'roblox': R('SmoothPlastic', (28, 28, 31), 0, 0.08)}),
    # ---- glass
    'Glass':       ((0.80, 0.66, 0.38), 0.03, 0.0, {'glass': 1.0, 'roblox': R('Glass', (150, 128, 82), 0.45, 0.25)}),
    'GlassClear':  ((0.85, 0.90, 0.90), 0.02, 0.0, {'glass': 1.0, 'roblox': R('Glass', (205, 218, 222), 0.70, 0.1)}),
    'SensorGlass': ((0.040, 0.045, 0.060), 0.05, 0.3, {'glass': 0.35, 'coat': 1.0, 'roblox': R('Glass', (30, 34, 46), 0.15, 0.35)}),
    'Lens':        ((0.95, 0.95, 0.95), 0.02, 0.0, {'glass': 1.0, 'roblox': R('Glass', (220, 225, 230), 0.60, 0.1)}),
    # ---- landing gear, bays, structure
    'Rubber':      ((0.012, 0.012, 0.012), 0.82, 0.0, {'roblox': R('Rubber', (28, 28, 28))}),
    'Tire':        ((0.016, 0.016, 0.016), 0.90, 0.0, {'bump': 0.4, 'roblox': R('Rubber', (30, 30, 30))}),
    'Wheel':       ((0.30, 0.31, 0.32), 0.45, 0.7, {'roblox': R('Metal', (150, 152, 156))}),
    'Chrome':      ((0.85, 0.86, 0.88), 0.10, 1.0, {'roblox': R('Foil', (205, 207, 212), 0, 0.4)}),
    'GearWhite':   ((0.62, 0.62, 0.60), 0.45, 0.0, {'vary': 0.06, 'roblox': R('SmoothPlastic', (200, 200, 196))}),
    'BayGrey':     ((0.36, 0.37, 0.37), 0.55, 0.0, {'vary': 0.06, 'roblox': R('SmoothPlastic', (160, 162, 163))}),
    'Primer':      ((0.13, 0.20, 0.09), 0.60, 0.0, {'vary': 0.08, 'roblox': R('SmoothPlastic', (98, 122, 78))}),
    'Steel':       ((0.30, 0.30, 0.29), 0.38, 1.0, {'roblox': R('Metal', (130, 130, 128))}),
    'Alu':         ((0.55, 0.56, 0.57), 0.32, 1.0, {'roblox': R('Metal', (172, 174, 178))}),
    'Hardware':    ((0.050, 0.050, 0.048), 0.48, 0.75, {'roblox': R('Metal', (56, 56, 55))}),
    'Gunmetal':    ((0.030, 0.032, 0.035), 0.36, 0.85, {'roblox': R('Metal', (40, 42, 46))}),
    'Engine':      ((0.10, 0.10, 0.11), 0.42, 0.9, {'vary': 0.12, 'roblox': R('Metal', (80, 82, 88))}),
    'Copper':      ((0.60, 0.30, 0.12), 0.35, 1.0, {'roblox': R('Metal', (190, 110, 62))}),
    'Brass':       ((0.55, 0.40, 0.12), 0.30, 1.0, {'roblox': R('Metal', (190, 150, 70))}),
    'Insulation':  ((0.75, 0.55, 0.18), 0.32, 1.0, {'bump': 0.8, 'roblox': R('Foil', (212, 172, 84), 0, 0.2)}),
    'CableBlack':  ((0.012, 0.012, 0.012), 0.70, 0.0, {'roblox': R('SmoothPlastic', (22, 22, 22))}),
    'CableOrange': ((0.65, 0.18, 0.02), 0.70, 0.0, {'roblox': R('Fabric', (215, 100, 30))}),
    'CableBlue':   ((0.03, 0.10, 0.35), 0.60, 0.0, {'roblox': R('SmoothPlastic', (40, 80, 160))}),
    'Radar':       ((0.12, 0.13, 0.10), 0.50, 0.2, {'roblox': R('SmoothPlastic', (96, 100, 82))}),
    # ---- cockpit
    'Cockpit':     ((0.062, 0.066, 0.072), 0.62, 0.0, {'roblox': R('SmoothPlastic', (72, 76, 82))}),
    'CockpitDark': ((0.020, 0.021, 0.024), 0.60, 0.0, {'roblox': R('SmoothPlastic', (30, 31, 34))}),
    'Display':     ((0.004, 0.005, 0.007), 0.12, 0.0, {'coat': 1.0, 'roblox': R('SmoothPlastic', (12, 14, 18), 0, 0.2)}),
    'ScreenGreen': ((0.05, 0.30, 0.10), 0.20, 0.0, {'emit': ((0.20, 1.00, 0.35), 2.5), 'roblox': R('Neon', (60, 235, 110))}),
    'ScreenAmber': ((0.30, 0.15, 0.02), 0.20, 0.0, {'emit': ((1.00, 0.55, 0.08), 2.5), 'roblox': R('Neon', (255, 160, 40))}),
    'ScreenCyan':  ((0.02, 0.20, 0.30), 0.20, 0.0, {'emit': ((0.10, 0.75, 1.00), 2.5), 'roblox': R('Neon', (40, 190, 255))}),
    'ScreenRed':   ((0.30, 0.02, 0.01), 0.20, 0.0, {'emit': ((1.00, 0.05, 0.03), 2.5), 'roblox': R('Neon', (255, 40, 30))}),
    'Seat':        ((0.035, 0.040, 0.028), 0.95, 0.0, {'bump': 0.3, 'roblox': R('Fabric', (52, 58, 44))}),
    'Harness':     ((0.10, 0.095, 0.06), 0.90, 0.0, {'bump': 0.4, 'roblox': R('Fabric', (118, 110, 80))}),
    'Yellow':      ((0.80, 0.55, 0.02), 0.50, 0.0, {'roblox': R('SmoothPlastic', (235, 180, 20))}),
    'Black':       ((0.008, 0.008, 0.009), 0.50, 0.0, {'roblox': R('SmoothPlastic', (18, 18, 20))}),
    'Red':         ((0.50, 0.015, 0.010), 0.45, 0.0, {'roblox': R('SmoothPlastic', (170, 22, 18))}),
    # ---- stores (fictional munitions)
    'Missile':     ((0.50, 0.51, 0.50), 0.50, 0.0, {'roblox': R('SmoothPlastic', (178, 180, 178))}),
    'MissileDark': ((0.060, 0.065, 0.070), 0.55, 0.0, {'roblox': R('SmoothPlastic', (72, 76, 80))}),
    'Bomb':        ((0.10, 0.11, 0.07), 0.60, 0.0, {'roblox': R('SmoothPlastic', (86, 92, 64))}),
    'BandBrown':   ((0.20, 0.10, 0.04), 0.60, 0.0, {'roblox': R('SmoothPlastic', (122, 76, 40))}),
    # ---- lights / energy
    'NavRed':      ((0.60, 0.02, 0.01), 0.15, 0.0, {'emit': ((1.0, 0.03, 0.02), 4.0), 'roblox': R('Neon', (255, 30, 25))}),
    'NavGreen':    ((0.02, 0.50, 0.10), 0.15, 0.0, {'emit': ((0.05, 1.0, 0.25), 4.0), 'roblox': R('Neon', (40, 255, 90))}),
    'Strobe':      ((0.90, 0.93, 1.00), 0.15, 0.0, {'emit': ((0.9, 0.93, 1.0), 5.0), 'roblox': R('Neon', (235, 240, 255))}),
    'Formation':   ((0.20, 0.60, 0.28), 0.30, 0.0, {'emit': ((0.35, 1.0, 0.45), 0.9), 'roblox': R('Neon', (110, 235, 140), 0.25)}),
    'LED':         ((0.90, 0.93, 1.00), 0.20, 0.0, {'emit': ((0.85, 0.90, 1.0), 6.0), 'roblox': R('Neon', (240, 244, 255))}),
    'Laser':       ((0.40, 0.15, 0.80), 0.20, 0.0, {'emit': ((0.55, 0.25, 1.0), 6.0), 'roblox': R('Neon', (170, 95, 255))}),
}

geo.setup(PREFIX, MODEL, ROOT_NAME, MATS)

# ============================================================== key dimensions (metres)
Y_NOSE = -12.40          # radome tip
Y_RADOME = -10.60        # radome / radar bulkhead joint
Y_TAILEND = 10.85        # end of the tail cone
ZW = 2.10                # wing + chine reference plane height (aircraft level on its wheels)
NAC_X, NAC_Z = 2.45, 2.10
Y_LIP = -4.60            # inlet lip plane
Y_FAN = -1.80            # engine fan face
Y_NACEND = 8.95          # nacelle aft rim (swivel nozzle sockets)
GAP = 0.003              # half of a door seam gap (seams read as 6 mm dark lines)
WING_TIP_X = 7.60
WING_TE = 7.40
HINGE_X = 5.20           # wing-tip droop hinge line (variable geometry)
LE_TAN = tan(radians(60))  # leading-edge sweep 60 deg


def wing_le(x):
    """leading-edge y of the outer wing at span x (x >= 0)."""
    return 6.0 - LE_TAN * (WING_TIP_X - x)


def wing_tc(x):
    return 0.034 + (0.026 - 0.034) * (x - NAC_X) / (WING_TIP_X - NAC_X)


# ---------------------------------------------------------------- centre body (chined fuselage + blended body)
W_ = Spline([(-12.40, 0.0, 0.40), (-11.40, 0.36), (-10.60, 0.58), (-8.90, 0.88), (-7.00, 1.12), (-5.60, 1.33),
             (-4.17, 1.73, 0.577), (-3.00, 2.25), (-2.00, 2.40, 0.0), (6.50, 2.40, 0.0), (7.60, 2.15),
             (8.80, 1.45), (10.00, 0.80), (10.60, 0.48), (10.85, 0.22)])
Zc_ = Spline([(-12.40, 1.96), (-10.60, 2.03), (-8.00, 2.07), (-5.00, 2.10, 0.0), (8.00, 2.10, 0.0),
              (10.85, 2.16)])
Zt_ = Spline([(-12.40, 1.97, 0.35), (-11.40, 2.22), (-10.60, 2.37), (-8.90, 2.55), (-7.00, 2.68), (-5.00, 2.79),
              (-3.00, 2.85), (0.00, 2.88, 0.0), (3.00, 2.86), (6.00, 2.78), (8.00, 2.62), (10.60, 2.34),
              (10.85, 2.28)])
Zb_ = Spline([(-12.40, 1.95, -0.35), (-11.40, 1.74), (-10.60, 1.62), (-8.90, 1.52), (-7.00, 1.46), (-5.00, 1.42),
              (-1.00, 1.38, 0.0), (5.00, 1.38, 0.0), (7.00, 1.42), (9.00, 1.62), (10.60, 1.90), (10.85, 2.04)])
AT_ = Spline([(-12.4, 1.90), (-8.0, 1.95), (-4.0, 2.40), (0.0, 2.60), (7.0, 2.60), (10.85, 2.20)])
BT_ = Spline([(-12.4, 1.45), (-8.0, 1.45), (-4.0, 1.25), (7.0, 1.20), (10.85, 1.30)])
AB_ = Spline([(-12.4, 2.20), (-8.0, 2.40), (-4.0, 3.00), (0.0, 3.20), (7.0, 3.20), (10.85, 2.40)])
BB_ = Spline([(-12.4, 1.30), (-8.0, 1.25), (-4.0, 1.08), (7.0, 1.05), (10.85, 1.20)])

NU = 22
U_ = cosspace(0.0, 1.0, NU)


def body_top(x, y):
    """z of the centre-body upper surface at (x, y) (|x| <= W)."""
    w = W_(y)
    u = min(1.0, abs(x) / max(w, 1e-6))
    return Zc_(y) + (Zt_(y) - Zc_(y)) * max(0.0, 1 - u ** AT_(y)) ** BT_(y)


def body_bot(x, y):
    w = W_(y)
    u = min(1.0, abs(x) / max(w, 1e-6))
    return Zc_(y) - (Zc_(y) - Zb_(y)) * max(0.0, 1 - u ** AB_(y)) ** BB_(y)


def body_section(y, shrink=0.0):
    """closed loop (4*NU points) of the centre body at station y. shrink = inward offset (approx.) for hollows."""
    w = max(W_(y) - shrink * 1.6, 0.002)
    zc, zt, zb = Zc_(y), Zt_(y) - shrink, Zb_(y) + shrink
    at, bt, ab, bb = AT_(y), BT_(y), AB_(y), BB_(y)
    top = [(u * w, zc + (zt - zc) * max(0.0, 1 - u ** at) ** bt) for u in U_]
    bot = [(u * w, zc - (zc - zb) * max(0.0, 1 - u ** ab) ** bb) for u in U_]
    loop = top[:]                                    # right->: centre top .. +x chine
    loop += bot[NU - 1::-1]                          # +x bottom .. centre bottom
    loop += [(-x, z) for x, z in bot[1:NU]]          # centre bottom .. -x bottom
    loop += [(-w, zc)]                               # -x chine
    loop += [(-x, z) for x, z in top[NU - 1:0:-1]]   # -x top .. (centre top excluded, already first)
    return [V((x, y, z)) for x, z in loop]


def body_stations(y0, y1):
    ys = []
    y = y0
    while y < y1 - 1e-9:
        ys.append(y)
        if y < -11.6:
            y += 0.05
        elif y < -4.0:
            y += 0.10
        elif y < 8.0:
            y += 0.15
        else:
            y += 0.10
    ys.append(y1)
    return ys


# ---------------------------------------------------------------- canopy bulge
Zcan_ = Spline([(-9.75, 2.40), (-9.20, 2.72), (-8.40, 3.05), (-7.40, 3.29), (-6.60, 3.34, 0.0), (-5.80, 3.24),
                (-5.00, 3.00), (-4.45, 2.77)])
Wcan_ = Spline([(-9.75, 0.10), (-9.20, 0.33), (-8.40, 0.49), (-7.40, 0.555), (-6.60, 0.56, 0.0), (-5.60, 0.50),
                (-4.45, 0.22)])
CAN_BASE = 2.30
CAN_Y0, CAN_Y1 = -9.30, -5.15     # canopy (glass + frame) length
CAN_HINGE = V((0.0, -5.15, 3.06))  # rear hinge line (axis X)


def canopy_z(x, y):
    w = Wcan_(y)
    v = min(1.0, abs(x) / max(w, 1e-6))
    return CAN_BASE + (Zcan_(y) - CAN_BASE) * max(0.0, 1 - v ** 2.6) ** 0.5


def canopy_outline(k=0.86, n=26, inset=0.0):
    """top-view outline of the canopy opening; inset shrinks it evenly (frame / glass split)."""
    ys = cosspace(CAN_Y0 + inset, CAN_Y1 - inset, n)
    right = [(-(Wcan_(y) * k - inset), y) for y in ys]
    left = [(Wcan_(y) * k - inset, y) for y in reversed(ys)]
    return right + left


# ---------------------------------------------------------------- nacelles
NR_ = Spline([(-4.60, 0.600), (-4.30, 0.636), (-3.60, 0.681), (-2.60, 0.712), (-1.20, 0.725, 0.0),
              (4.00, 0.725, 0.0), (6.50, 0.714), (8.00, 0.682), (8.95, 0.640)])
DUCT_ = Spline([(-4.70, 0.592), (-4.60, 0.585), (-4.00, 0.570), (-3.30, 0.548), (-2.50, 0.560), (-1.80, 0.578)])
BAY_R_ = Spline([(-1.80, 0.640), (6.50, 0.640), (8.00, 0.612), (8.95, 0.592), (9.20, 0.592)])


def nacelle_top(y):
    return NAC_Z + NR_(y)


# ---------------------------------------------------------------- vertical tails (all-moving, canted 15 deg in)
TAIL_CANT = 15.0
TAIL_ROOT_Z = 2.92
TAIL_LE0, TAIL_TE0 = 6.05, 9.15
TAIL_SPAN = 2.30
TAIL_PIVOT_Y = TAIL_LE0 + 0.42 * (TAIL_TE0 - TAIL_LE0)


def tail_axes(side):
    """span direction (unit) and thickness direction for the left (+1) / right (-1) tail."""
    c, s = cos(radians(TAIL_CANT)), sin(radians(TAIL_CANT))
    span = V((-side * s, 0.0, c))
    thick = V((c, 0.0, side * s))
    return span, thick


# ---------------------------------------------------------------- landing gear
MAIN_GEAR = dict(x_leg=1.19, x_wheel=1.40, y=3.40, z_trunnion=1.80, r=0.400, w=0.26, retract=-100.0)  # left side
NOSE_GEAR = dict(x=-0.22, y=-8.35, z_trunnion=1.92, r=0.300, w=0.15, track=0.12, retract=-95.0)

# ---------------------------------------------------------------- render views (loc, target, lens)
VIEWS = {
    'front34':   ((-17.0, -21.0, 7.5), (0.0, -1.0, 2.0), 40),
    'rear34':    ((16.0, 21.0, 8.0), (0.0, 1.5, 2.0), 40),
    'side':      ((-34.0, 0.0, 3.0), (0.0, -0.6, 2.2), 45),
    'sideL':     ((34.0, 0.0, 3.0), (0.0, -0.6, 2.2), 45),
    'front':     ((0.0, -40.0, 2.6), (0.0, 0.0, 2.3), 55),
    'rear':      ((0.0, 40.0, 3.0), (0.0, 0.0, 2.3), 55),
    'top':       ((0.0, -0.8, 40.0), (0.0, -0.8, 0.0), 45, 'X'),
    'bottom':    ((0.0, -0.8, -36.0), (0.0, -0.8, 2.0), 45, 'X'),
    'low34':     ((-12.0, -15.0, 0.6), (0.0, -2.0, 1.8), 30),
    'high34':    ((-16.0, -12.0, 15.0), (0.0, 0.5, 2.0), 38),
    'cockpit':   ((-2.6, -9.6, 4.6), (0.0, -7.0, 2.6), 32),
    'cockpitin': ((0.0, -5.2, 3.35), (0.0, -8.6, 2.55), 18),
    'nose':      ((-5.5, -14.5, 3.2), (0.0, -10.5, 2.0), 32),
    'engine':    ((6.5, 1.5, 6.5), (2.45, 3.0, 2.4), 32),
    'exhaust':   ((-6.0, 17.0, 2.4), (0.0, 9.5, 2.0), 32),
    'under':     ((-9.0, -6.0, 0.25), (0.0, 1.0, 1.4), 26),
    'gear':      ((-5.5, 0.5, 0.6), (-1.3, 3.2, 1.0), 30),
    'bays':      ((-5.0, 1.0, 0.15), (0.0, 1.2, 1.6), 24),
}


def setview(name=None, loc=None, target=None, lens=45, up='Y'):
    if name:
        v = VIEWS[name]
        loc, target, lens = v[:3]
        up = v[3] if len(v) > 3 else 'Y'
    look(loc, target, lens, up)
