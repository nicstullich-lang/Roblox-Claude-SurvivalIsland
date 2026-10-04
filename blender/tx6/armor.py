"""TX-6 Bastion - layered add-on armour, flares, V-hull, skid plates, side steps."""
from tx6.lib import *
from tx6 import body as B


def ob(name):
    return bpy.data.objects[name]


def plate_side(name, outline, s, off, th, parent=None, mat='ArmorPaint', sp=0.15, inset=0.028, bolt=True,
               col='Armor', bev=(0.006, 2, 30)):
    """armour plate on the body side (outline y,z must stay on one side of the beltline crease)."""
    zm = sum(p[1] for p in outline) / len(outline)
    n = side_n(zm, s)
    pts = [side_pt(y, z, s, off) for (y, z) in outline]
    o = mk(name, prism(pts, n * th), mat, col, parent, bev=bev)
    if bolt:
        top = [p + n * th for p in pts]
        bolts(name + '_Bolts', pts_poly(top, sp, inset), n, parent or o)
    return o


def quad_plate(name, quad, off, th, parent=None, mat='ArmorPaint', sp=0.15, inset=0.03, bolt=True, col='Armor',
               bev=(0.006, 2, 30)):
    n = newell(quad)
    cen = sum((V(p) for p in quad), V((0, 0, 0))) / len(quad)
    if n.dot(cen - V((0, cen.y, 1.4))) < 0:      # always extrude away from the vehicle centre
        n = -n
    pts = [V(p) + n * off for p in quad]
    o = mk(name, prism(pts, n * th), mat, col, parent, bev=bev)
    if bolt:
        bolts(name + '_Bolts', pts_poly([p + n * th for p in pts], sp, inset), n, parent or o)
    return o


def flare(name, ya, s):
    """armoured wheel-arch flare: angled band that steps out from the body side to 1.355 m."""
    arch = [(ya + dy, max(z, Z_SILL)) for (dy, z) in ARCH]
    arch[0] = (arch[0][0], Z_SILL)
    arch[-1] = (arch[-1][0], Z_SILL)
    inner = [p for p in arch]
    outer_w = offset2(arch, 0.105)
    outer_n = offset2(arch, 0.045)
    # polyline only (drop the closing bottom edge): use the 6 arch points
    def band(inn, out, x):
        poly = [(x, y, z) for (y, z) in inn] + [(x, y, z) for (y, z) in reversed(out)]
        return poly
    # clamp the outer leg ends to the sill height
    outer_w = [(y, max(z, Z_SILL)) for (y, z) in outer_w]
    outer_n = [(y, max(z, Z_SILL)) for (y, z) in outer_n]
    outer_w[0] = (outer_w[0][0], Z_SILL)
    outer_w[-1] = (outer_w[-1][0], Z_SILL)
    outer_n[0] = (outer_n[0][0], Z_SILL)
    outer_n[-1] = (outer_n[-1][0], Z_SILL)
    lA = band(inner, outer_w, s * (X_SIDE - 0.012))
    lB = band(inner, outer_w, s * 1.30)
    lC = band(inner, outer_n, s * 1.355)
    o = mk(name, loft([lA, lB, lC]), 'ArmorPaint', 'Armor', bev=(0.006, 2, 30))
    # bolts along the outer lip
    mid = offset2(arch, 0.024)
    pts = []
    for (y0, z0), (y1, z1) in zip(mid[:-1], mid[1:]):
        for q in pts_line((s * 1.356, y0, max(z0, 0.66)), (s * 1.356, y1, max(z1, 0.66)), 0.13)[:-1]:
            pts.append(q)
    bolts(name + '_Bolts', pts, V((s, 0, 0)), o)
    return o


def build():
    for s, sfx in ((1, 'L'), (-1, 'R')):
        # ------------------------------------------------------------ armoured flares
        flare('Flare_F' + sfx, Y_AF, s)
        flare('Flare_R' + sfx, Y_AR, s)
        # ------------------------------------------------------------ door applique armour (two layers, V-pattern)
        dF, dR = ob('Door_F' + sfx), ob('Door_R' + sfx)
        plate_side('Armor_DoorF1' + sfx, [(-1.02, 0.80), (-0.15, 0.80), (-0.15, 1.48), (-0.22, 1.55), (-0.95, 1.55),
                                          (-1.02, 1.48)], s, 0.010, 0.022, dF, bolt=False)
        plate_side('Armor_DoorF2' + sfx, [(-0.96, 0.93), (-0.24, 0.86), (-0.24, 1.40), (-0.30, 1.46), (-0.90, 1.46),
                                          (-0.96, 1.40)], s, 0.032, 0.018, dF, sp=0.14)
        plate_side('Armor_DoorR1' + sfx, [(0.02, 0.80), (0.92, 0.80), (0.92, 1.48), (0.85, 1.55), (0.09, 1.55),
                                          (0.02, 1.48)], s, 0.010, 0.022, dR, bolt=False)
        plate_side('Armor_DoorR2' + sfx, [(0.08, 0.86), (0.86, 0.93), (0.86, 1.40), (0.80, 1.46), (0.14, 1.46),
                                          (0.08, 1.40)], s, 0.032, 0.018, dR, sp=0.14)
        # ------------------------------------------------------------ armoured window frames (bolted bezels)
        for win, door, nm in ((B.FW_WIN, dF, 'F'), (B.RW_WIN, dR, 'R')):
            outer = offset2(win, 0.058)
            inner = offset2(win, 0.0)
            n = side_n(2.0, s)
            o3 = [side_pt(y, z, s, 0.0) for (y, z) in outer]
            i3 = [side_pt(y, z, s, 0.0) for (y, z) in inner]
            fr = mk('WinFrame_%s%s' % (nm, sfx), ring_prism(o3, i3, n * 0.024), 'ArmorPaint', 'Armor', door,
                    bev=(0.005, 2, 30))
            mid = [side_pt(y, z, s, 0.024) for (y, z) in offset2(win, 0.030)]
            bolts('WinFrame_%s%s_Bolts' % (nm, sfx), pts_poly(mid, 0.11, 0.0), n, door, r=0.009)
        # ------------------------------------------------------------ rocker armour (angled deflector below doors)
        rk = [(s * 1.14, -1.17, 0.565), (s * 1.14, 1.04, 0.565), (s * 1.245, 1.04, 0.705), (s * 1.245, -1.17, 0.705)]
        quad_plate('Armor_Rocker' + sfx, rk, 0.0, 0.025, sp=0.20)
        # ------------------------------------------------------------ fender / quarter armour rails above the arches
        plate_side('Armor_FenderRail' + sfx, [(-2.84, 1.455), (-1.16, 1.455), (-1.16, 1.555), (-2.80, 1.535)], s, 0.006,
                   0.022, sp=0.17)
        plate_side('Armor_QuarterRail' + sfx, [(1.06, 1.455), (2.84, 1.455), (2.80, 1.590), (1.06, 1.590)], s, 0.006,
                   0.022, sp=0.17)
        # ------------------------------------------------------------ A-pillar armour
        hc, hw = B.hood_half(Y_COWL), B.cabin_half()
        P4a, P5a = V((s * hc[4][0], Y_COWL, hc[4][1])), V((s * hc[5][0], Y_COWL, hc[5][1]))
        P4b, P5b = V((s * hw[4][0], Y_WST, hw[4][1])), V((s * hw[5][0], Y_WST, hw[5][1]))
        quad = [P5a, P4a, P4b, P5b] if s > 0 else [P4a, P5a, P5b, P4b]
        quad_plate('Armor_APillar' + sfx, quad, 0.004, 0.028, sp=0.16, inset=0.035)
        # ------------------------------------------------------------ roof-edge armour caps
        def chamfer_pt(y, t, off):
            a = V((s * X_RE, y, Z_RE))
            b = V((s * X_RT, y, Z_ROOF))
            p = a.lerp(b, t)
            n = V((s * (Z_ROOF - Z_RE), 0, (X_RE - X_RT))).normalized()
            return p + n * off
        cap = [chamfer_pt(-0.74, 0.05, 0.004), chamfer_pt(2.84, 0.05, 0.004), chamfer_pt(2.84, 0.92, 0.004),
               chamfer_pt(-0.74, 0.92, 0.004)]
        quad_plate('Armor_RoofEdge' + sfx, cap, 0.0, 0.016, sp=0.22, inset=0.03)
        # ------------------------------------------------------------ side steps (grated tread on a tube frame)
        y0, y1 = -1.15, 1.00
        x0, x1 = s * 1.12, s * 1.385
        zt = 0.505
        fr_path = [V((x0, y0, zt)), V((x1, y0, zt)), V((x1, y1, zt)), V((x0, y1, zt))]
        frame = sweep_vf(fr_path + [fr_path[0]], [(-0.02, -0.025), (0.02, -0.025), (0.02, 0.025), (-0.02, 0.025)])
        slats = []
        k = 0
        y = y0 + 0.05
        while y < y1 - 0.03:
            slats.append(box_vf(((x0 + x1) / 2, y, zt + 0.006), (abs(x1 - x0) - 0.03, 0.014, 0.034)))
            y += 0.055
        supports = []
        for ys in (-0.95, -0.05, 0.82):
            a = V((s * 0.96, ys, 0.60))
            b = V((s * 1.30, ys, zt - 0.02))
            supports.append(box_arm(a, b, 0.05, 0.06))
            supports.append(box_vf((s * 0.98, ys, 0.615), (0.10, 0.12, 0.03)))
        mk('Step_Frame' + sfx, merge_vf(frame, *supports), 'Coating', 'Armor', bev=(0.004, 1, 30))
        mk('Step_Tread' + sfx, merge_vf(*slats), 'Hardware', 'Armor')
        # ------------------------------------------------------------ lower rear corner armour (behind rear arch)
        plate_side('Armor_RearCorner' + sfx, [(2.80, 0.74), (2.92, 0.74), (2.92, 1.40), (2.80, 1.40)], s, 0.006, 0.02,
                   sp=0.12)

    # ------------------------------------------------------------ windshield armoured frame
    n = B.ws_normal()

    def ws_strip(name, x0, x1, z0, z1, th=0.026):
        pts = [V((x, y_ws(z), z)) + n * 0.004 for (x, z) in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
        o = mk(name, prism(pts, n * th), 'ArmorPaint', 'Armor', bev=(0.005, 2, 30))
        return o, [p + n * th for p in pts]
    strips = [('WSFrame_Bottom', -0.985, 0.985, 1.705, 1.805), ('WSFrame_Top', -0.975, 0.975, 2.355, 2.455),
              ('WSFrame_Centre', -0.065, 0.065, 1.805, 2.355), ('WSFrame_L', 0.855, 0.985, 1.805, 2.355),
              ('WSFrame_R', -0.985, -0.855, 1.805, 2.355)]
    bp = []
    for nm, x0, x1, z0, z1 in strips:
        o, top = ws_strip(nm, x0, x1, z0, z1)
        bp += pts_poly(top, 0.14, 0.022)
    bolts('WSFrame_Bolts', bp, n, None, r=0.010)

    # ------------------------------------------------------------ hood: raised armour bulge + louvred vents
    hood = ob('Hood')

    def hpt(x, y, dz=0.0):
        return V((x, y, zh(y) + dz))
    lo = [hpt(-0.56, -2.74, -0.01), hpt(0.56, -2.74, -0.01), hpt(0.56, -1.97, -0.01), hpt(-0.56, -1.97, -0.01)]
    hi = [hpt(-0.48, -2.64, 0.065), hpt(0.48, -2.64, 0.065), hpt(0.48, -2.05, 0.065), hpt(-0.48, -2.05, 0.065)]
    mk('Hood_Bulge', loft([lo, hi]), 'ArmorPaint', 'Armor', hood, bev=(0.008, 2, 25))
    bolts('Hood_Bulge_Bolts', pts_poly([p + V((0, 0, 0.0)) for p in hi], 0.16, 0.03), V((0, 0, 1)), hood)
    # air intake slot on the front of the bulge
    for s in (1, -1):
        base = [hpt(s * 0.62, -2.62, 0.002), hpt(s * 0.94, -2.62, 0.002), hpt(s * 0.94, -2.00, 0.002),
                hpt(s * 0.62, -2.00, 0.002)]
        mk('Hood_VentBase' + ('L' if s > 0 else 'R'), prism(base, (0, 0, 0.012)), 'Mesh', 'Armor', hood)
        slats = []
        y = -2.59
        while y < -2.02:
            p0 = hpt(s * 0.635, y, 0.004)
            slats.append(sweep_vf([p0, p0 + V((s * 0.29, 0, 0))],
                                  [(0.0, -0.004), (0.030, 0.012), (0.030, 0.020), (0.0, 0.004)]))
            y += 0.055
        fr = [hpt(s * 0.60, -2.64, 0.0), hpt(s * 0.96, -2.64, 0.0), hpt(s * 0.96, -1.98, 0.0), hpt(s * 0.60, -1.98, 0.0)]
        fi = [hpt(s * 0.625, -2.615, 0.0), hpt(s * 0.935, -2.615, 0.0), hpt(s * 0.935, -2.005, 0.0),
              hpt(s * 0.625, -2.005, 0.0)]
        if s < 0:
            fr, fi = fr[::-1], fi[::-1]
        mk('Hood_VentFrame' + ('L' if s > 0 else 'R'), ring_prism(fr, fi, (0, 0, 0.03)), 'ArmorPaint', 'Armor', hood,
           bev=(0.004, 1, 30))
        mk('Hood_VentSlats' + ('L' if s > 0 else 'R'), merge_vf(*slats), 'PaintDark', 'Armor', hood, sharp=40)

    # ------------------------------------------------------------ V-hull blast belly + skid plates
    tri = [(-1.10, 0.628), (1.10, 0.628), (0.0, 0.455)]
    vh = prism([(x, -1.20, z) for (x, z) in tri], (0, 2.24, 0))
    keel = box_vf((0, -0.08, 0.452), (0.05, 2.20, 0.02))
    ribs = []
    for yy in (-0.85, -0.25, 0.35, 0.80):
        ribs.append(prism([(x, yy - 0.02, z) for (x, z) in [(-1.00, 0.625), (1.00, 0.625), (0.0, 0.47)]], (0, 0.04, 0)))
    mk('VHull', vh, 'Coating', 'Armor', bev=(0.006, 1, 20))
    mk('VHull_Keel', keel, 'Hardware', 'Armor')
    bp = []
    for xx in (-0.85, -0.45, 0.45, 0.85):
        for yy in (-1.10, -0.55, 0.0, 0.55, 0.95):
            z = 0.455 + abs(xx) / 1.10 * 0.173
            bp.append(V((xx, yy, z - 0.002)))
    bolts('VHull_Bolts', bp, lambda p: V((0.157 * (1 if p.x > 0 else -1), 0, -1)).normalized(), ob('VHull'), r=0.014,
          h=0.008)
    # engine skid plate (between the front wells, turns up into the bumper)
    sk = [(-0.44, -1.26, 0.585), (0.44, -1.26, 0.585), (0.44, -2.90, 0.545), (-0.44, -2.90, 0.545)]
    mk('Skid_Engine', prism(sk, (0, 0, -0.022)), 'Coating', 'Armor', bev=(0.005, 1, 30))
    bolts('Skid_Engine_Bolts', pts_poly([V(p) - V((0, 0, 0.022)) for p in sk], 0.25, 0.04), V((0, 0, -1)),
          ob('Skid_Engine'), r=0.013)
    # rear skid / fuel tank guard
    rs = [(-0.46, 1.12, 0.60), (0.46, 1.12, 0.60), (0.46, 2.92, 0.62), (-0.46, 2.92, 0.62)]
    mk('Skid_Rear', prism(rs, (0, 0, -0.022)), 'Coating', 'Armor', bev=(0.005, 1, 30))
    bolts('Skid_Rear_Bolts', pts_poly([V(p) - V((0, 0, 0.022)) for p in rs], 0.25, 0.04), V((0, 0, -1)),
          ob('Skid_Rear'), r=0.013)


def box_arm(p0, p1, w, h):
    return sweep_vf([V(p0), V(p1)], [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)])
