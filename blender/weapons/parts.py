"""Parametric weapon components shared by the five weapons (each weapon calls them with its own proportions so the
silhouettes stay distinct). All functions return raw (verts, faces) solids or create parts through lib.part().

Local frames: many components follow a straight or curved axis in the weapon's side plane (YZ). For those, a point is
given as (x, s, u): x across the weapon, s along the axis, u along the in-plane normal n = (0, -t.z, t.y) (for an axis
that points down, u > 0 is toward the rear of the weapon).
"""
from .lib import *


class Frame:
    """straight axis in the YZ plane from p0 = (y, z) to p1 = (y, z)."""

    def __init__(self, p0, p1):
        self.o = V((0.0, p0[0], p0[1]))
        d = V((0.0, p1[0] - p0[0], p1[1] - p0[1]))
        self.L = d.length
        self.t = d.normalized()
        self.n = V((0.0, -self.t.z, self.t.y))

    def M(self):
        m = Matrix((V((1, 0, 0)), self.t, self.n)).transposed().to_4x4()
        m.translation = self.o
        return m

    def at(self, x, s, u):
        return self.o + V((x, 0, 0)) + self.t * s + self.n * u

    def box(self, x0, x1, s0, s1, u0, u1):
        return xform_vf(box_between((x0, s0, u0), (x1, s1, u1)), self.M())

    def vf(self, vf):
        return xform_vf(vf, self.M())


def line_path(p0, p1, n):
    return [(p0[0] + (p1[0] - p0[0]) * k / n, p0[1] + (p1[1] - p0[1]) * k / n) for k in range(n + 1)]


def arc_down_path(top, z_knee, radius, angle_deg, n_straight=4, n_arc=24, forward=True):
    """path that runs straight down from top = (y, z) to z_knee, then curves toward the muzzle (-Y) along an arc."""
    y0, z0 = top
    pts = [(y0, z0 + (z_knee - z0) * k / n_straight) for k in range(n_straight)]
    sg = -1 if forward else 1
    cy = y0 + sg * radius
    for k in range(n_arc + 1):
        th = radians(angle_deg) * k / n_arc
        pts.append((cy - sg * radius * cos(th), z_knee - radius * sin(th)))
    return pts


# ------------------------------------------------------------------------------------------ grips
def grip_section(w, uf, ub, seg=3):
    """pistol-grip cross-section (x, u): narrow rounded front strap, widest just behind the middle, round backstrap."""
    return fillet2([(0.60 * w, uf, 0.55 * w), (w, uf * 0.25 + ub * 0.15, 0.6 * w), (0.86 * w, ub, 0.75 * w),
                    (-0.86 * w, ub, 0.75 * w), (-w, uf * 0.25 + ub * 0.15, 0.6 * w), (-0.60 * w, uf, 0.55 * w)], seg)


def grip_vf(p_top, p_bot, w0, w1, uf0, ub0, ub1, fingers=3, finger_depth=0.0035, finger_range=(0.18, 0.90),
            n=26, flare=0.0):
    """angled pistol grip from p_top to p_bot (y, z). Front strap with `fingers` finger swells, backstrap that
    grows from ub0 to ub1, width w0 -> w1, optional bottom flare (extra size over the last 12 %)."""
    path = line_path(p_top, p_bot, n)
    f0, f1 = finger_range

    def sec_(i, s):
        w = w0 + (w1 - w0) * s
        ub = ub0 + (ub1 - ub0) * smooth01(s)
        uf = uf0
        if fingers and f0 < s < f1:
            ph = (s - f0) / (f1 - f0)
            uf = uf0 - finger_depth * max(0.0, sin(pi * fingers * ph)) ** 0.8
        if flare and s > 0.88:
            k = smooth01((s - 0.88) / 0.12)
            w += flare * k
            ub += flare * 1.2 * k
            uf -= flare * 0.8 * k
        return grip_section(w, uf, ub)
    return sweep_yz(path, sec_)


def grip_grooves(fr, w, s_list, uf, ub, depth=0.0011, width=0.0016):
    """horizontal grooves across both grip sides (cutters, in the grip frame)."""
    out = []
    for s in s_list:
        for sg in (1, -1):
            out.append(fr.box(sg * (w - depth), sg * (w + 0.02), s - width / 2, s + width / 2, uf * 0.55, ub * 0.80))
    return out


# ------------------------------------------------------------------------------------------ magazines
def mag_section(hw, depth_f, depth_b, rf=0.008, rb=0.0035, seg=3):
    return fillet2([(hw, -depth_f, rf), (hw, depth_b, rb), (-hw, depth_b, rb), (-hw, -depth_f, rf)], seg)


def mag_vf(path, hw, depth_f, depth_b, ribs=(), rib_h=0.0012, rf=0.008, rb=0.0035):
    """magazine body swept along `path` (top -> bottom). ribs = list of (s0, s1) bands standing rib_h proud."""
    def sec_(i, s):
        h = hw
        for a, b in ribs:
            if a - 0.02 < s < b + 0.02:
                h += rib_h * smooth01(min((s - (a - 0.02)) / 0.02, ((b + 0.02) - s) / 0.02))
        return mag_section(h, depth_f, depth_b, rf, rb)
    return sweep_yz(path, sec_)


def path_end_frame(path):
    """(end point (y, z), unit tangent (ty, tz)) of a YZ path."""
    a, b = V(path[-2]), V(path[-1])
    t = (b - a).normalized()
    return b, t


def baseplate_vf(path, hw, depth_f, depth_b, under=0.010, over=0.0045, lip=0.004, grow=0.0022):
    """magazine baseplate: a short, slightly larger block across the end of the magazine path."""
    e, t = path_end_frame(path)
    p0 = (e.x - t.x * under, e.y - t.y * under)
    p1 = (e.x + t.x * over, e.y + t.y * over)
    pts = line_path(p0, p1, 2)
    return sweep_yz(pts, lambda i, s: mag_section(hw + grow, depth_f + grow + lip * smooth01(s * 1.5), depth_b + grow,
                                                   0.009, 0.004))


# ------------------------------------------------------------------------------------------ trigger group
def trigger_vf(top, bot, curve=0.006, hw=0.0045, t=0.0032, n=10):
    """curved trigger blade from top = (y, z) (hidden inside the receiver) down to the tip, curving forward."""
    y0, z0 = top
    y1, z1 = bot
    pts = []
    for k in range(n + 1):
        s = k / n
        bend = curve * sin(pi * s * 0.9) * (1 - 0.3 * s)
        pts.append((y0 + (y1 - y0) * s + bend, z0 + (z1 - z0) * s))
    return sweep_yz(pts, lambda i, s: fillet2([(hw, -t * (1 - 0.35 * s), 0.0012), (hw, t, 0.0012),
                                               (-hw, t, 0.0012), (-hw, -t * (1 - 0.35 * s), 0.0012)], 2))


def guard_vf(path, hw=0.0075, t=0.0034, r=0.0025):
    """open trigger guard: a rounded bar swept along a U-shaped path (y, z)."""
    pts = fillet2(path, None, closed=False)
    return sweep_yz(pts, lambda i, s: fillet2([(hw, -t, r), (hw, t, r), (-hw, t, r), (-hw, -t, r)], 2))


# ------------------------------------------------------------------------------------------ sights / optics
def rail_clamp_vf(y0, y1, z_rail, hw_rail=0.0118, h_rail=0.0112, top=0.010, hw=None):
    """mount base that hooks over a rail's dovetails: block on the rail top + two feet down the dovetail flanks."""
    hw = hw or hw_rail * 1.62
    zt = z_rail + h_rail
    out = [(hw, zt - h_rail * 0.42), (hw, zt + top), (-hw, zt + top), (-hw, zt - h_rail * 0.42),
           (-hw_rail * 1.30, zt - h_rail * 0.42), (-hw_rail * 1.02, zt - h_rail * 0.05),
           (hw_rail * 1.02, zt - h_rail * 0.05), (hw_rail * 1.30, zt - h_rail * 0.42)]
    return plate_xz(out, y0, y1)


def red_dot(y_c, z_rail, mat_body='Blackened', mat_base='Graphite'):
    """compact red-dot sight: octagonal tube with hoods, recessed lenses, top + right turrets, battery cap,
    clamp base with cross-bolt. Returns (parts dict, axis height)."""
    base_top = z_rail + 0.0112 + 0.011
    r = 0.0235
    zc = base_top + r - 0.002
    L0, L1 = y_c - 0.040, y_c + 0.028
    # closed ring profile (outer then back along the inside)
    ring = [(r - 0.0045, L0 - 0.004), (r + 0.0008, L0 - 0.004), (r + 0.0025, L0 + 0.001), (r + 0.0025, L0 + 0.009),
            (r, L0 + 0.013), (r, L1 - 0.010), (r + 0.0015, L1 - 0.007), (r + 0.0015, L1), (r - 0.0045, L1)]
    body = orient(lathe_vf([(a, b) for a, b in ring] + [ring[0]], 8, False, False, a0=pi / 8), (0, 0, zc), 'Y')
    out = {}
    out['body'] = body
    base = rail_clamp_vf(y_c - 0.030, y_c + 0.020, z_rail, top=0.011)
    # saddle between base and the octagon
    sad = plate_xz(fillet2([(0.016, base_top - 0.002, 0), (0.016, zc - r * 0.6, 0.004), (-0.016, zc - r * 0.6, 0.004),
                            (-0.016, base_top - 0.002, 0)]), y_c - 0.026, y_c + 0.016)
    out['base'] = merge_vf(base, sad)
    lens_f = cyl_vf((0, L0 + 0.009, zc), r - 0.0040, 0.003, 'Y', 24)
    lens_r = cyl_vf((0, L1 - 0.007, zc), r - 0.0040, 0.003, 'Y', 24)
    out['lens'] = merge_vf(lens_f, lens_r)
    # turrets: elevation (top), windage (right side = -X), battery cap (left = +X)
    yt = y_c - 0.006
    fl = r * cos(pi / 8)
    tur_top = lathe_axis([(0, 0), (0.0085, 0), (0.0085, 0.0075), (0.0075, 0.0095), (0, 0.0095)], 16,
                         (0, yt, zc + fl + 0.0020), 'Z')
    tur_rgt = lathe_axis([(0, 0), (0.0085, 0), (0.0085, 0.0075), (0.0075, 0.0095), (0, 0.0095)], 16,
                         (-fl - 0.0020, yt, zc), '-X')
    bat = lathe_axis([(0, 0), (0.0105, 0), (0.0105, 0.0085), (0.0092, 0.011), (0, 0.011)], 16,
                     (fl + 0.0020, yt, zc), 'X')
    # turret housings (square bosses the caps sit on): 1.5 mm into the flat, 4.5 mm proud
    fl = r * cos(pi / 8)
    boss = merge_vf(box_vf((0, yt, zc + fl + 0.0015), (0.022, 0.022, 0.006)),
                    box_vf((-fl - 0.0015, yt, zc), (0.006, 0.022, 0.022)),
                    box_vf((fl + 0.0015, yt, zc), (0.006, 0.024, 0.024)))
    out['turrets'] = merge_vf(tur_top, tur_rgt, bat)
    out['boss'] = boss
    # cross-bolt clamp: nut on the right, bolt head on the left
    zb = z_rail + 0.0112 - 0.004
    out['bolt'] = merge_vf(orient(lathe_vf([(0, 0), (0.0055, 0), (0.0055, 0.004), (0, 0.004)], 6, a0=pi / 6),
                                  (-0.0118 * 1.62, y_c - 0.005, zb), '-X'),
                           orient(lathe_vf([(0, 0), (0.0048, 0), (0.0048, 0.0028), (0.0038, 0.0038), (0, 0.0038)], 12),
                                  (0.0118 * 1.62, y_c - 0.005, zb), 'X'))
    return out, zc, r


def flip_rear_sight(y0, y1, z_rail):
    """flip-up rear aperture sight: clamp base + upright leaf with an aperture ring and protective ears."""
    base = rail_clamp_vf(y0, y1, z_rail, top=0.006, hw=0.0118 * 1.45)
    zt = z_rail + 0.0112 + 0.006
    yl = y1 - 0.006
    leaf = plate_xz(fillet2([(0.0105, zt - 0.002, 0), (0.0105, zt + 0.022, 0.003), (0.0062, zt + 0.031, 0.004),
                             (-0.0062, zt + 0.031, 0.004), (-0.0105, zt + 0.022, 0.003), (-0.0105, zt - 0.002, 0)]),
                    yl - 0.0025, yl + 0.0025)
    hole = cyl_vf((0, yl, zt + 0.0215), 0.0028, 0.03, 'Y', 16)
    ring = orient(lathe_vf([(0.0028, -0.004), (0.0058, -0.004), (0.0058, 0.004), (0.0028, 0.004), (0.0028, -0.004)],
                           16, False, False), (0, yl, zt + 0.0215), 'Y')
    hinge = cyl_vf((0, yl, zt + 0.0055), 0.003, 0.024, 'X', 12)      # raised so the folded aperture ring clears
    return base, leaf, hole, ring, hinge, (0, yl, zt + 0.0055)


def flip_front_sight(y0, y1, z_rail):
    """flip-up front post sight: clamp base, two protective ears and a round post with a threaded collar."""
    base = rail_clamp_vf(y0, y1, z_rail, top=0.006, hw=0.0118 * 1.45)
    zt = z_rail + 0.0112 + 0.006
    yp = (y0 + y1) / 2 + 0.003
    frame_ = plate_xz(fillet2([(0.0125, zt - 0.002, 0), (0.0125, zt + 0.018, 0.004), (0.0095, zt + 0.030, 0.003),
                               (0.0060, zt + 0.030, 0.002), (0.0060, zt + 0.012, 0.004), (-0.0060, zt + 0.012, 0.004),
                               (-0.0060, zt + 0.030, 0.002), (-0.0095, zt + 0.030, 0.003), (-0.0125, zt + 0.018, 0.004),
                               (-0.0125, zt - 0.002, 0)]), yp - 0.004, yp + 0.004)
    post = merge_vf(cyl_vf((0, yp, zt + 0.0135), 0.0032, 0.004, 'Z', 12),
                    lathe_axis([(0, 0), (0.0016, 0), (0.0016, 0.012), (0.0010, 0.0135), (0, 0.0135)], 10,
                               (0, yp, zt + 0.0150), 'Z'))
    hinge = cyl_vf((0, yp + 0.004, zt + 0.0045), 0.003, 0.028, 'X', 12)
    return base, frame_, post, hinge, (0, yp + 0.004, zt + 0.0045)


# ------------------------------------------------------------------------------------------ muzzle devices
def comp_vf(y_front, length, r, bore=0.0065, ports=3, port_w=0.0055, flats=True):
    """compensator: chamfered cylinder with a bore, `ports` vertical slots through the sides and two top holes.
    returns (solid, cutters)."""
    yf, yr = y_front, y_front + length
    ring = [(bore, yf), (r - 0.003, yf), (r, yf + 0.003), (r, yr - 0.010), (r - 0.0025, yr - 0.006),
            (r - 0.0025, yr), (bore, yr)]
    solid = orient(lathe_vf([(a, b) for a, b in ring] + [ring[0]], 24, False, False), (0, 0, 0), 'Y')
    cuts = []
    for k in range(ports):
        yc = yf + 0.014 + k * (length - 0.032) / max(1, ports - 1)
        cuts.append(merge_vf(box_vf((0, yc, 0.0), (0.06, port_w, r * 1.15))))
    for k in range(2):
        cuts.append(cyl_vf((0, yf + 0.016 + k * 0.016, r), 0.0028, 0.02, 'Z', 12))
    if flats:
        for sg in (1, -1):
            cuts.append(box_vf((sg * (r + 0.004 - 0.0018), yr - 0.010, 0), (0.008, 0.012, 0.04)))
    return solid, cuts


def birdcage_vf(y_front, length, r, bore=0.0065, prongs=6, slot_w=0.0042, slot_len=0.030, closed_bottom=True):
    """slotted flash hider: cylinder with long slots open toward the front (bottom prong left solid)."""
    yf, yr = y_front, y_front + length
    ring = [(bore, yf), (r - 0.0025, yf), (r, yf + 0.0025), (r, yr - 0.008), (r * 0.86, yr - 0.004), (r * 0.86, yr), (bore, yr)]
    solid = orient(lathe_vf([(a, b) for a, b in ring] + [ring[0]], 24, False, False), (0, 0, 0), 'Y')
    cuts = []
    for k in range(prongs):
        a = 2 * pi * k / prongs + pi / prongs
        if closed_bottom and abs(a - 1.5 * pi) < pi / prongs:
            continue
        c = V((cos(a) * r, yf + slot_len / 2 - 0.004, sin(a) * r))
        b = box_vf((0, 0, 0), (slot_w, slot_len + 0.008, r * 1.1))
        b = xform_vf(b, Matrix.Translation(c) @ Matrix.Rotation(a - pi / 2, 4, 'Y').inverted())
        cuts.append(b)
    return solid, cuts


# ------------------------------------------------------------------------------------------ misc hardware
def qd_loop(c, out_dir, r_ring=0.010, r_wire=0.0021):
    """QD sling swivel: socket cup on the surface + a wire loop standing out along out_dir."""
    od = V(out_dir).normalized()
    cup = lathe_axis([(0, 0), (0.0068, 0), (0.0068, 0.004), (0.0056, 0.0055), (0, 0.0055)], 14, c, od)
    stem = cyl_between(V(c) + od * 0.004, V(c) + od * 0.009, 0.0026, 10)
    lc = V(c) + od * (0.009 + r_ring)
    side = V((0, 1, 0)) if abs(od.y) < 0.9 else V((1, 0, 0))
    nrm = od.cross(side).normalized()           # loop plane contains od and `side`
    loop = sling_loop_vf(lc, nrm, r_ring, r_wire, 16)
    return merge_vf(cup, stem), loop


def knurl_ring_cutters(c, axis, r, h, n=24, depth=0.0008, w=0.0012):
    """axial knurl grooves around a knob (cutters)."""
    ax = axis_v(axis)
    out = []
    for k in range(n):
        a = 2 * pi * k / n
        p = V((cos(a) * r, sin(a) * r, 0))
        b = box_vf(p, (depth * 2, w, h * 1.2))
        b = xform_vf(b, Matrix.Rotation(a, 4, 'Z'))
        out.append(orient(b, c, ax))
    return out


def path_at(path, f):
    """point (y, z) and unit tangent (ty, tz) at fraction f (0..1 of the length) along a YZ polyline."""
    P = [V(p) for p in path]
    acc = [0.0]
    for i in range(1, len(P)):
        acc.append(acc[-1] + (P[i] - P[i - 1]).length)
    tgt = f * acc[-1]
    for i in range(1, len(P)):
        if acc[i] >= tgt:
            k = (tgt - acc[i - 1]) / max(1e-12, acc[i] - acc[i - 1])
            p = P[i - 1].lerp(P[i], k)
            t = (P[i] - P[i - 1]).normalized()
            return p, t
    return P[-1], (P[-1] - P[-2]).normalized()


def path_point3(path, f, x, u):
    """3D point at fraction f along a YZ path, offset x across and u along the in-plane normal."""
    p, t = path_at(path, f)
    n = V((-t.y, t.x))          # (ny, nz) = (-tz, ty)
    return V((x, p.x + n.x * u, p.y + n.y * u))


def checker_cutters(fr, w_of_s, s0, s1, u0, u1, pitch=0.0055, ang=42.0, width=0.0012, depth=0.0010):
    """cross-hatched checkering on both sides of a grip (cutters in the grip frame `fr`).
    w_of_s(s) = grip half-width at distance s along the frame axis."""
    out = []
    for a_deg in (ang, -ang):
        a = radians(a_deg)
        d = V((cos(a), sin(a)))
        nn = V((-sin(a), cos(a)))
        corners = [V((s0, u0)), V((s1, u0)), V((s1, u1)), V((s0, u1))]
        cs = [c.dot(nn) for c in corners]
        c = min(cs) + pitch * 0.5
        while c < max(cs):
            # clip the line c*nn + t*d to the rectangle (Liang-Barsky)
            t0, t1 = -1.0, 1.0
            p0 = nn * c
            ok = True
            for k, (lo, hi) in enumerate(((s0, s1), (u0, u1))):
                if abs(d[k]) < 1e-9:
                    if not lo <= p0[k] <= hi:
                        ok = False
                    continue
                ta, tb = (lo - p0[k]) / d[k], (hi - p0[k]) / d[k]
                t0, t1 = max(t0, min(ta, tb)), min(t1, max(ta, tb))
            if ok and t1 - t0 > 0.004:
                for sg in (1, -1):
                    A = p0 + d * t0
                    B = p0 + d * t1
                    sm = (A.x + B.x) / 2
                    w = w_of_s(sm)
                    xi, xo = sg * (w - depth), sg * (w + 0.02)
                    Dl = V((0.0, d.x, d.y))
                    Nl = V((0.0, nn.x, nn.y))
                    vs = []
                    for x in (xi, xo):
                        for (pp, sgn) in ((A, -1), (B, 1)):
                            base = V((x, pp.x, pp.y)) + Dl * (0.0006 * sgn)
                            vs.append(base - Nl * (width / 2))
                            vs.append(base + Nl * (width / 2))
                    # vs order: (xi,A,-), (xi,A,+), (xi,B,-), (xi,B,+), (xo,A,-), (xo,A,+), (xo,B,-), (xo,B,+)
                    F = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
                    out.append(fr.vf((vs, F)))
            c += pitch
    return out
