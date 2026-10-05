"""XR-77 surface detail pass: recessed panel lines, nacelle joint rings, NACA cooling ducts (one EXACT boolean on the
hull), flush fasteners around access panels and joints, low-visibility stencils + insignia, RAM-coated inlet lips,
static dischargers, composite repair patches.
"""
from .lib import *
from common import rig
from . import airframe as AF

FAST = []          # (point, normal, parent) for fasteners


def groove(path, proj, closed=False):
    return groove_vf(AF.CASTER, path, proj, width=0.006, depth=0.004, step=0.12, closed=closed)


def row(poly, proj, spacing=0.10, inset=0.025, closed=True, parent=None):
    for p, n in surface_points(AF.CASTER, poly, proj, spacing, inset, closed):
        FAST.append((p, n, parent))


def body_lines():
    cutters = []
    for s in (1, -1):
        # longitudinal spine lines + lower longerons
        cutters.append(groove([(s * 0.95, -4.55), (s * 0.95, 0.05)], 'top'))
        cutters.append(groove([(s * 0.95, 2.0), (s * 0.95, 7.35)], 'top'))
        cutters.append(groove([(s * 1.45, -2.0), (s * 1.45, 1.05)], 'bottom'))
        cutters.append(groove([(s * 1.45, 3.85), (s * 1.45, 7.30)], 'bottom'))
        # wing panels: front spar, rear spar, rib lines (top + bottom)
        for proj in ('top', 'bottom'):
            cutters.append(groove([(s * 3.30, wing_le(3.30) + 0.62), (s * 5.12, wing_le(5.12) + 0.62)], proj))
            cutters.append(groove([(s * 3.25, 6.45), (s * 5.12, 6.45)], proj))
            for x in (3.85, 4.55):
                cutters.append(groove([(s * x, wing_le(x) + 0.65), (s * x, 6.40)], proj))
        # outer panels are separate objects - skip; nose section joint lines
        cutters.append(groove([(s * 0.22, -9.62), (s * (W_(-9.62) - 0.06), -9.62)], 'top'))
    for y in (-1.05, 3.0, 6.85):
        cutters.append(groove([(-1.55, y), (1.55, y)], 'top'))
    for y in (-0.95, 4.25):
        cutters.append(groove([(-0.90, y), (-0.12, y)], 'bottom'))
        cutters.append(groove([(0.12, y), (0.90, y)], 'bottom'))
    # nacelle joint rings (exact lathes) + RAM inlet lips
    for s in (1, -1):
        for y in (-3.40, -0.20, 6.10, 7.70):
            r = NR_(y)
            ring = orient(lathe_vf([(r - 0.004, y - 0.003), (r + 0.01, y - 0.003), (r + 0.01, y + 0.003),
                                    (r - 0.004, y + 0.003), (r - 0.004, y - 0.003)], 56, cap0=False, cap1=False),
                          (s * NAC_X, 0, NAC_Z), 'Y')
            cutters.append(ring)
    # NACA cooling ducts on the aft body (recessed ramps)
    for s in (1, -1):
        x0, y0, L, w = s * 0.62, 6.10, 0.55, 0.16
        outline = [(x0 - w / 2 * (0.25 + 0.75 * (k / 8) ** 0.7), y0 + L * k / 8) for k in range(9)]
        outline += [(x0 + w / 2 * (0.25 + 0.75 * (k / 8) ** 0.7), y0 + L * k / 8) for k in range(8, -1, -1)]
        top = [AF.CASTER.on(p, 'top')[0] for p in outline]
        Vs, F = [], []
        n = len(outline)
        for p in top:
            Vs.append(p + V((0, 0, 0.03)))
        for p in top:
            depth = 0.004 + 0.065 * max(0.0, (p.y - y0) / L) ** 1.2
            Vs.append(p - V((0, 0, depth)))
        F = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        cutters.append((Vs, F))
        rig.point('Vent_NACA_' + ('L' if s > 0 else 'R'), (x0, y0 + L, top[0].z), 'effect', direction=(0, 1, 0),
                  effect='cooling air intake (heat shimmer at high power)')
    cos_ = [cutter('_groove_%d' % i, vf) for i, vf in enumerate(cutters)]
    for c in cos_:
        for p in c.data.polygons:
            p.material_index = 5            # SkinDark walls in the grooves
    body = bpy.data.objects['Airframe']
    boolean(body, cos_)
    body.data.set_sharp_from_angle(angle=radians(40))
    # fastener rows beside the joint lines
    for s in (1, -1):
        for y in (-1.05, 3.0, 6.85):
            for dy in (-0.022, 0.022):
                row([(s * 0.12, y + dy), (s * 1.50, y + dy)], 'top', 0.13, 0.0, closed=False)
        for proj in ('top', 'bottom'):
            row([(s * 3.32, wing_le(3.32) + 0.60), (s * 5.10, wing_le(5.10) + 0.60)], proj, 0.14, 0.0, closed=False)
            row([(s * 3.27, 6.43), (s * 5.10, 6.43)], proj, 0.14, 0.0, closed=False)


def panel_fasteners():
    D = AF.DOORS
    for s in ('L', 'R'):
        sx = 1 if s == 'L' else -1
        cx = sx * NAC_X
        for k, (y0, y1) in (('Fwd', (0.00, 2.85)), ('Aft', (3.05, 5.75))):
            row([(cx - 0.58, y0), (cx + 0.58, y0), (cx + 0.58, y1), (cx - 0.58, y1)], 'top', 0.12, 0.022,
                parent=D['EnginePanel_%s_%s' % (k, s)])
        row([(cx - 0.24, 0.90), (cx + 0.24, 0.90), (cx + 0.24, 1.75), (cx - 0.24, 1.75)], 'bottom', 0.11, 0.02,
            parent=D['ServiceHatch_' + s])
        row([(sx * 0.22, 7.55), (sx * 1.05, 7.55), (sx * 1.05, 8.75), (sx * 0.22, 8.75)], 'top', 0.12, 0.02,
            parent=D['Speedbrake_' + s])
    row(rrect2(0.34, 0.70, 0.08, 3, 0.0, -1.90), 'top', 0.09, 0.02, parent=D['Refuel_Door'])
    row([(-0.86, -4.42), (0.86, -4.42), (0.86, -2.50), (-0.86, -2.50)], 'top', 0.14, 0.03, parent=D['LiftFan_DoorTop'])


def stencils():
    parts = []
    parts_red = []
    C = AF.CASTER
    for s in (1, -1):
        proj = 'left' if s > 0 else 'right'
        # tail number + type on the outer face of each tail (side projection hits the tail)
        parts_t = [stamp_vf(C, 'XR-77', (8.10, 4.15), proj, 0.20, up2d=(0, 1), rot=0.0 if s > 0 else 0.0)]
        parts_t.append(stamp_vf(C, '077', (8.25, 3.75), proj, 0.16))
        vv, ff = merge_vf(*parts_t)
        if s < 0:      # text seen from the right reads mirrored unless flipped along y
            vv = [V((v.x, 16.35 - v.y, v.z)) for v in vv]
            ff = [tuple(reversed(f)) for f in ff]
        mk('Stencil_Tail_' + ('L' if s > 0 else 'R'), (vv, ff), 'Stencil', 'Details', bpy.data.objects['Tail_' + ('L' if s > 0 else 'R')],
           smooth=False)
        # nose name + rescue / danger markings near the cockpit
        nm = stamp_vf(C, 'UMBRA', (-10.0 if s > 0 else -10.0, 2.18), proj, 0.11)
        if s < 0:
            vv, ff = nm
            nm = ([V((v.x, -20.0 - v.y, v.z)) for v in vv], [tuple(reversed(f)) for f in ff])
        parts.append(nm)
        nostep = stamp_vf(C, 'NO STEP', (s * 4.6, 2.6), 'top', 0.08, up2d=(-s, 0))
        parts.append(nostep)
    resc = stamp_vf(C, 'RESCUE', (-6.30, 2.30), 'left', 0.07)
    arrow = skin_patch(C, [(-6.68, 2.27), (-6.52, 2.20), (-6.52, 2.34)], 'left', t=0.0012, lift=0.0026, spacing=0.03)
    parts_red += [resc, arrow]
    tri = skin_patch(C, [(-5.70, 2.20), (-5.50, 2.20), (-5.60, 2.37)], 'left', t=0.0012, lift=0.0026, spacing=0.03,
                     holes=[[(-5.66, 2.225), (-5.54, 2.225), (-5.60, 2.33)]])
    parts_red.append(tri)
    for s in (1, -1):
        # intake danger chevrons on the nacelle fronts (top)
        cx = s * NAC_X
        chev = skin_patch(C, [(cx - 0.20, -4.05), (cx, -3.90), (cx + 0.20, -4.05), (cx + 0.20, -3.98), (cx, -3.83),
                              (cx - 0.20, -3.98)], 'top', t=0.0012, lift=0.0026, spacing=0.03)
        parts_red.append(chev)
    mk('Stencils', merge_vf(*parts), 'Stencil', 'Details', smooth=False)
    mk('Stencils_Red', merge_vf(*parts_red), 'Red', 'Details', smooth=False)
    # fictional low-visibility insignia (ring + chevron): left wing top, right wing bottom, both nacelle sides
    ins = []
    for (c2, proj) in (((4.30, 3.20), 'top'), ((-4.30, 3.20), 'bottom')):
        ins.append(skin_patch(C, circle2(0.42, 40, *c2), proj, t=0.0012, lift=0.0026, spacing=0.05,
                              holes=[circle2(0.34, 40, *c2)]))
        ins.append(skin_patch(C, [(c2[0] - 0.22, c2[1] + 0.10), (c2[0], c2[1] - 0.18), (c2[0] + 0.22, c2[1] + 0.10),
                                  (c2[0] + 0.12, c2[1] + 0.10), (c2[0], c2[1] - 0.04), (c2[0] - 0.12, c2[1] + 0.10)],
                              proj, t=0.0012, lift=0.0026, spacing=0.03))
    for s in (1, -1):
        proj = 'left' if s > 0 else 'right'
        c2 = (3.0, 2.12)
        ins.append(skin_patch(C, ellipse2(0.30, 0.22, 40, *c2), proj, t=0.0012, lift=0.0026, spacing=0.04,
                              holes=[ellipse2(0.24, 0.17, 40, *c2)]))
    mk('Insignia', merge_vf(*ins), 'Stencil', 'Details', smooth=False)


def extras():
    # RAM-coated inlet lips (dark ring on the sharp lip)
    lips = []
    for s in (1, -1):
        lips.append(orient(lathe_vf([(0.586, -4.605), (0.602, -4.605), (NR_(-4.50) + 0.0015, -4.50), (0.584, -4.50),
                                     (0.586, -4.605)], 56, cap0=False, cap1=False), (s * NAC_X, 0, NAC_Z), 'Y'))
    mk('Inlet_RAMLips', merge_vf(*lips), 'SkinDark', 'Details', sharp=35)
    # static dischargers on the wing tips + tail tips
    for s in (1, -1):
        S_ = 'L' if s > 0 else 'R'
        wt = bpy.data.objects['Wingtip_' + S_]
        rods = []
        for x in (6.95, 7.25, 7.52):
            y = WING_TE - 0.01
            rods.append(cyl_between((s * x, y, ZW), (s * x, y + 0.16, ZW), 0.005, 6))
        mk('StaticWicks_' + S_, merge_vf(*rods), 'Black', 'Details', wt)
        tl = bpy.data.objects['Tail_' + S_]
        span, thick = tail_axes(s)
        rods = []
        for h in (1.60, 2.05):
            p = V((s * NAC_X, 0, TAIL_ROOT_Z)) + span * h
            p.y = TAIL_TE0 + h * 0.268 - 0.012
            rods.append(cyl_between(p, p + V((0, 0.15, 0)), 0.005, 6))
        mk('StaticWicks_Tail_' + S_, merge_vf(*rods), 'Black', 'Details', tl)
    # composite repair patches (slightly different coating tone) - subtle imperfection
    pat = []
    for (c2, w, h, proj) in (((0.80, -6.3), 0.26, 0.20, 'top'), ((-1.6, 1.9), 0.42, 0.30, 'top'),
                             ((0.55, 4.6), 0.26, 0.20, 'top'), ((-3.9, 2.2), 0.50, 0.32, 'top'),
                             ((1.2, 0.6), 0.36, 0.24, 'bottom'), ((-0.6, 6.95), 0.30, 0.22, 'bottom')):
        pat.append(skin_patch(AF.CASTER, rrect2(w, h, 0.03, 2, *c2), proj, t=0.0012, lift=0.0018, spacing=0.05))
        row(rrect2(w, h, 0.03, 2, *c2), proj, 0.07, 0.015)
    mk('RepairPatches', merge_vf(*pat), 'SkinAlt', 'Details', smooth=False)


def build():
    body_lines()
    panel_fasteners()
    stencils()
    extras()
    groups = {}
    for p, n, par in FAST:
        groups.setdefault(par.name if par else '', []).append((p, n))
    for k, pn in groups.items():
        vf = fasteners_vf(pn, r=0.0055, h=0.0012, n=4)
        mk('Fasteners' + ('_' + k if k else '_Body'), vf, 'Titanium', 'Details', bpy.data.objects[k] if k else None,
           smooth=False)
    print('details: fasteners', len(FAST))
