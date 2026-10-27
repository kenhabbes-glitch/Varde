"""Varde – parametriske kapslinger for 3D-print.

Kjør:  python3 varde_kapsling.py            (lager alle deler, begge varianter, i ./stl)
       python3 varde_kapsling.py hovedenhet  (bare én enhet)

Krever bare Python 3.9+ (ingen pakker). Alle mål i mm. Mål merket SJEKK må kontrolleres mot
kretskortet og komponentenes datablad før print i serie.

Varianter:
  prototype – PETG, tynnere vegger, ingen pakning. For passform og test på pult.
  felt      – ASA eller PA12, tykkere vegger, spor for pakningssnor, trykkutjevningsventil.
"""
import math, os, sys
from csg import Solid, box, cyl, rbox, union_all, Polygon, run_big_stack

# ---------------- felles parametre ----------------
CLR = 0.3            # klaring mellom deler som skal passe sammen
INSERT_M3 = 4.0      # hull for M3 gjengeinnsats (varmepresset, f.eks. M3 x 5,7). SJEKK mot innsatsens datablad
INSERT_M3_DEPTH = 6.0
INSERT_M2 = 3.2      # hull for M2 gjengeinnsats (M2 x 4)
INSERT_M2_DEPTH = 4.5
CLEAR_M3, HEAD_M3 = 3.4, 6.6     # gjennomgående hull og forsenking for M3 sikkerhetsskrue (Torx med pinne)
CLEAR_M2, HEAD_M2 = 2.4, 4.4
SMA_HOLE = 6.5       # SMA skottkontakt 1/4"-36. SJEKK
GLAND_M16 = 16.3     # kabelforskruing M16 x 1,5 med mutter
M12_PANEL = 16.3     # M12 panelkontakt med M16 x 1,5 festegjenge (frontmontert). SJEKK: PG9-varianter trenger 15,5
VENT_M12 = 12.3      # trykkutjevningsventil M12 x 1,5 med mutter (membranventil, IP67/IP69K)
SEG = 48


def variant(name, small=False):
    """Veggtykkelse, pakningsspor og annet som skiller prototype og felt."""
    felt = name == 'felt'
    if small:
        return dict(felt=felt, wall=2.4 if felt else 2.0, floor=2.0 if felt else 1.6, lid=2.4 if felt else 2.0,
                    groove_w=1.7, groove_d=1.1, groove_wall=1.0, cord='silikonsnor 1,5 mm', r=3.0,
                    ear_r=3.6, ins=INSERT_M2, ins_d=INSERT_M2_DEPTH, clr_h=CLEAR_M2, head=HEAD_M2, screw='M2')
    return dict(felt=felt, wall=3.0 if felt else 2.4, floor=3.0 if felt else 2.4, lid=3.0 if felt else 2.4,
                groove_w=2.3, groove_d=1.5, groove_wall=1.3, cord='EPDM- eller silikonsnor 2,0 mm', r=5.0,
                ear_r=5.2, ins=INSERT_M3, ins_d=INSERT_M3_DEPTH, clr_h=CLEAR_M3, head=HEAD_M3, screw='M3')


def rloft(x0, y0, x1, y1, za, zb, ia, ib, r, seg=32):
    """Overgang mellom to rundede rektangler (innfelt ia ved za, ib ved zb). Gir 45° fas når |ib-ia| = |zb-za|."""
    def ring(i, z):
        pts = []
        rr = max(r - i, 0.01)
        cs = [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]
        for cx, cy, a0 in cs:
            for k in range(seg // 4 + 1):
                a = math.radians(a0 + 90 * k / (seg // 4))
                pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a), z))
        return pts
    A, B = ring(ia, za), ring(ib, zb)
    polys = [Polygon(list(reversed(A))), Polygon(B)]
    n = len(A)
    for i in range(n):
        j = (i + 1) % n
        if A[i] == A[j] and B[i] == B[j]: continue
        polys.append(Polygon([A[i], A[j], B[j], B[i]]))
    return Solid(polys)


class Enclosure:
    """Bunn og lokk. Koordinater: komponentsonen starter i (0,0) og har mål L x W.
    z = 0 er undersiden av bunnen, gulvets overside er self.fz, toppkanten er self.H."""

    def __init__(self, name, L, W, D, v, ears, corner=None):
        self.name, self.v = name, v
        w = v['wall']
        # felt: bånd på toppen av veggen gir plass til pakningssporet. Komponentsonen holdes fri.
        self.band = (v['groove_w'] + 2 * v['groove_wall']) if v['felt'] else 0
        self.intr = max(self.band - w, 0)              # hvor langt båndet stikker inn fra veggen
        i = self.intr
        self.L, self.W, self.D = L, W, D
        self.x0, self.y0 = -i - w, -i - w              # ytre hjørne
        self.x1, self.y1 = L + i + w, W + i + w
        self.fz = v['floor']; self.H = v['floor'] + D
        self.r = corner if corner else v['r']
        self.ears = ears                               # liste av (x, y) for ørenes senter
        self.base_cuts, self.base_adds, self.lid_cuts, self.lid_adds = [], [], [], []

    # ---------- geometri ----------
    def ear_centers(self):
        return self.ears

    def outer(self, z0, z1):
        s = rbox(self.x0, self.y0, z0, self.x1, self.y1, z1, self.r)
        for ex, ey in self.ears:
            s = s + cyl(ex, ey, z0, z1, self.v['ear_r'], SEG)
        return s

    def cavity(self):
        v, i, w = self.v, self.intr, self.v['wall']
        ri = max(self.r - w, 0.5)
        x0, y0, x1, y1 = -i, -i, self.L + i, self.W + i
        if not v['felt'] or self.intr <= 0:
            return rbox(x0, y0, self.fz, x1, y1, self.H + 1, ri)
        bh = 3.0                                       # båndets høyde
        z_b = self.H - bh; z_a = z_b - i               # 45° fas under båndet
        low = rbox(x0, y0, self.fz, x1, y1, z_a + 0.001, ri)
        fas = rloft(x0, y0, x1, y1, z_a, z_b, 0, i, ri)
        top = rbox(x0 + i, y0 + i, z_b - 0.001, x1 - i, y1 - i, self.H + 1, max(ri - i, 0.5))
        return low + fas + top

    def lip_ring(self):
        """Lokkets kant som går ned i bunnen og styrer lokket på plass."""
        w, i = self.v['wall'], self.intr
        inset = (self.band if self.v['felt'] else w) + CLR
        t = 1.6; h = 3.0
        ri = max(self.r - inset, 0.5)
        X0, Y0, X1, Y1 = self.x0 + inset, self.y0 + inset, self.x1 - inset, self.y1 - inset
        o = rbox(X0, Y0, self.H - h, X1, Y1, self.H + 0.01, ri)
        n = rbox(X0 + t, Y0 + t, self.H - h - 1, X1 - t, Y1 - t, self.H + 1, max(ri - t, 0.3))
        return o - n

    def groove(self):
        v = self.v
        a = v['groove_wall']; g = v['groove_w']
        x0, y0, x1, y1, r = self.x0, self.y0, self.x1, self.y1, self.r
        o = rbox(x0 + a, y0 + a, self.H - v['groove_d'], x1 - a, y1 - a, self.H + 1, max(r - a, 0.5))
        n = rbox(x0 + a + g, y0 + a + g, self.H - v['groove_d'] - 1, x1 - a - g, y1 - a - g, self.H + 2, max(r - a - g, 0.5))
        return o - n

    # ---------- detaljer ----------
    def wall_hole(self, side, u, z, d, part='base', recess=None):
        """Hull gjennom en vegg. side: '-x', '+x', '-y', '+y'. u = posisjon langs veggen, z = høyde over gulvets underside.
        recess = (diameter, dybde) for en flat forsenking på innsiden (membran, mutter)."""
        w = self.v['wall'] + self.intr + 1
        if side == '-x': s = cyl(u, z, self.x0 - 1, self.x0 + w + 0.5, d / 2, SEG, 'x')
        elif side == '+x': s = cyl(u, z, self.x1 - w - 0.5, self.x1 + 1, d / 2, SEG, 'x')
        elif side == '-y': s = cyl(u, z, self.y0 - 1, self.y0 + w + 0.5, d / 2, SEG, 'y')
        else: s = cyl(u, z, self.y1 - w - 0.5, self.y1 + 1, d / 2, SEG, 'y')
        self.base_cuts.append(s)
        if recess:
            rd, rdep = recess
            iw = self.v['wall']
            if side == '-y': self.base_cuts.append(cyl(u, z, self.y0 + iw - rdep, self.y0 + iw + 5, rd / 2, SEG, 'y'))
            if side == '+y': self.base_cuts.append(cyl(u, z, self.y1 - iw - 5, self.y1 - iw + rdep, rd / 2, SEG, 'y'))
            if side == '-x': self.base_cuts.append(cyl(u, z, self.x0 + iw - rdep, self.x0 + iw + 5, rd / 2, SEG, 'x'))
            if side == '+x': self.base_cuts.append(cyl(u, z, self.x1 - iw - 5, self.x1 - iw + rdep, rd / 2, SEG, 'x'))

    def standoff(self, x, y, h, od=7.0, hole=INSERT_M3, depth=5.8):
        self.base_adds.append(cyl(x, y, self.fz - 0.5, self.fz + h, od / 2, SEG))
        self.base_cuts.append(cyl(x, y, self.fz + h - depth, self.fz + h + 1, hole / 2, SEG))

    def floor_hole(self, x, y, d, boss=None):
        if boss: self.base_adds.append(cyl(x, y, self.fz - 0.5, self.fz + 1.2, boss / 2, SEG))
        self.base_cuts.append(cyl(x, y, -1, self.fz + 2, d / 2, SEG))

    def rib(self, x0, y0, x1, y1, h):
        self.base_adds.append(box(x0, y0, self.fz - 0.5, x1, y1, self.fz + h))

    def lid_pocket(self, x0, y0, x1, y1, leave):
        """Lomme fra innsiden av lokket. leave = tykkelse som står igjen."""
        t = self.v['lid']
        self.lid_cuts.append(box(x0, y0, self.H - 5, x1, y1, self.H + t - leave))

    def lid_magnet(self, x, y, d=6.3, depth=3.2):
        """Tapp på undersiden av lokket med lomme for magneten (6 x 3 mm) til reed-bryteren."""
        self.lid_adds.append(cyl(x, y, self.H - 2.6, self.H + 0.01, d / 2 + 2.0, SEG))
        self.lid_cuts.append(cyl(x, y, self.H - 3.6, self.H - 2.6 + depth, d / 2, SEG))

    def lid_label(self, x0, y0, x1, y1, depth=0.6):
        t = self.v['lid']
        self.lid_cuts.append(box(x0, y0, self.H + t - depth, x1, y1, self.H + t + 1))

    # ---------- bygging ----------
    def build_base(self):
        v = self.v
        s = self.outer(0, self.H)
        s = s - self.cavity()
        for a in self.base_adds: s = s + a
        cuts = list(self.base_cuts)
        if v['felt']: cuts.append(self.groove())
        for ex, ey in self.ears:
            cuts.append(cyl(ex, ey, self.H - v['ins_d'], self.H + 1, v['ins'] / 2, SEG))
        cut = union_all(cuts)
        return s - cut

    def build_lid(self):
        """Lokket i montert stilling (z fra H til H + lokktykkelse)."""
        v = self.v; t = v['lid']
        s = self.outer(self.H, self.H + t) + self.lip_ring()
        for a in self.lid_adds: s = s + a
        cuts = list(self.lid_cuts)
        for ex, ey in self.ears:
            cuts.append(cyl(ex, ey, self.H - 1, self.H + t + 1, v['clr_h'] / 2, SEG))
            cuts.append(cyl(ex, ey, self.H + t - 1.6, self.H + t + 1, v['head'] / 2, SEG))  # forsenking for skruehodet
        return s - union_all(cuts)

    def lid_for_print(self, lid):
        """Snur lokket (utsiden ned mot platen) og legger det på z = 0."""
        t = self.v['lid']
        return lid.rotate('x', 180).translate(0, 0, self.H + t)

    def size(self):
        e = self.v['ear_r'] if self.ears else 0
        xs = [self.x0, self.x1] + [ex - e for ex, _ in self.ears] + [ex + e for ex, _ in self.ears]
        ys = [self.y0, self.y1] + [ey - e for _, ey in self.ears] + [ey + e for _, ey in self.ears]
        return round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1), round(self.H + self.v['lid'], 1)


def side_ears(enc_L, W, v, x0, x1, fr=(0.2, 0.8)):
    """Ører på kortsidene (±x), litt utenfor veggen."""
    off = v['ear_r'] - 1.2
    return [(x0 - off, W * f) for f in fr] + [(x1 + off, W * f) for f in fr]


# ======================================================================
# Hovedenhet: kort 100 x 70 mm, 18650-batteri, 3 SMA, 3 kabelforskruinger
# ======================================================================
def hovedenhet(vn):
    v = variant(vn)
    L, W, D = 120.0, 104.0, 30.0
    i = (2.3 + 2 * 1.3 - v['wall']) if v['felt'] else 0
    x0, x1 = -i - v['wall'], L + i + v['wall']
    e = Enclosure('hovedenhet', L, W, D, v, side_ears(L, W, v, x0, x1))
    fz = e.fz
    # kretskort 100 x 70 i x 10–110, y 4–74. Hull 4 mm fra hjørnene (SJEKK mot kortet)
    for hx, hy in ((14, 8), (106, 8), (14, 70), (106, 70)):
        e.standoff(hx, hy, 6.0)
    # batteriholder 18650 (ca. 78 x 21 mm) i y 80–102: lave ribber som styrer holderen
    e.rib(20, 78.5, 100, 80.0, 3.0); e.rib(20, 102.0, 100, 103.0, 3.0)
    # festehull for M6 (bare tilgjengelig med lokket av). Bruk tetningsskive.
    for hx, hy in ((5, 20), (115, 20), (5, 92), (115, 92)):
        e.floor_hole(hx, hy, 6.6, boss=12)
    # sabotasjebryter mot underlaget (tett trykknapp)
    e.floor_hole(5, 56, 8.2, boss=13)
    # -x: tre SMA-kontakter (LTE, LoRa, aktiv GNSS)
    for u in (30, 52, 74): e.wall_hole('-x', u, fz + 20, SMA_HOLE)
    # +x: tre kabelforskruinger M16 (strøm 9–36 V, kabelsløyfe GPS, utvidelse/kamera)
    for u in (24, 52, 80): e.wall_hole('+x', u, fz + 15, GLAND_M16)
    # -y: mikrofonport med membran (lim inn akustisk membran i forsenkingen på innsiden)
    e.wall_hole('-y', 40, fz + 12, 1.8, recess=(9.0, 0.8))
    if v['felt']: e.wall_hole('-y', 95, fz + 10, VENT_M12)   # trykkutjevningsventil
    # lokk: radarvindu (60 GHz). Godstykkelse ca. lambda/2 i plast med eps_r 2,6–3,0. SJEKK med radaren
    e.lid_pocket(10, 25, 40, 55, leave=1.5)
    # magnet for reed-bryter (6 x 3 mm), over bryteren på kortet (SJEKK posisjon)
    e.lid_magnet(100, 40)
    # etikettfelt for serienummer og QR-kode på utsiden
    e.lid_label(65, 70, 110, 95)
    return e


# ======================================================================
# Utvidelsesboks: kort 120 x 80 mm, 4 x M12, 3 kabelforskruinger
# ======================================================================
def utvidelsesboks(vn):
    v = variant(vn)
    L, W, D = 140.0, 96.0, 34.0
    i = (2.3 + 2 * 1.3 - v['wall']) if v['felt'] else 0
    x0, x1 = -i - v['wall'], L + i + v['wall']
    e = Enclosure('utvidelsesboks', L, W, D, v, side_ears(L, W, v, x0, x1))
    fz = e.fz
    for hx, hy in ((14, 12), (126, 12), (14, 84), (126, 84)):
        e.standoff(hx, hy, 6.0)
    for hx, hy in ((5, 22), (135, 22), (5, 74), (135, 74)):
        e.floor_hole(hx, hy, 6.6, boss=12)
    # +y: fire M12-porter for sensorbussen
    for u in (34, 58, 82, 106): e.wall_hole('+y', u, fz + 18, M12_PANEL)
    # -y: tre kabelforskruinger M16 (EOL-innganger, reléutganger, RS-485)
    for u in (40, 70, 100): e.wall_hole('-y', u, fz + 17, GLAND_M16)
    if v['felt']: e.wall_hole('-x', 48, fz + 10, VENT_M12)
    e.lid_magnet(125, 48)                        # magnet for lokkbryter
    e.lid_label(15, 30, 60, 60)
    return e


# ======================================================================
# Sensornode: kort 30 x 40 mm, M12 inn og ut
# ======================================================================
def sensornode(vn):
    v = variant(vn)
    L, W, D = 38.0, 72.0, 26.0
    i = (2.3 + 2 * 1.3 - v['wall']) if v['felt'] else 0
    x0, x1 = -i - v['wall'], L + i + v['wall']
    e = Enclosure('sensornode', L, W, D, v, side_ears(L, W, v, x0, x1))
    fz = e.fz
    for hx, hy in ((7, 22), (31, 22), (7, 50), (31, 50)):
        e.standoff(hx, hy, 4.0, od=6.0, hole=INSERT_M2, depth=4.5)
    e.wall_hole('-y', L / 2, fz + 12, M12_PANEL)
    e.wall_hole('+y', L / 2, fz + 12, M12_PANEL)
    for hx, hy in ((19, 13), (19, 59)):
        e.floor_hole(hx, hy, 4.5, boss=9)
    return e


# ======================================================================
# Brikke S og L (utstyr uten strøm). Elektronikken støpes inn i serie.
# ======================================================================
def brikke(vn, size):
    v = variant(vn, small=True)
    if size == 'S':     # kort 28 x 22, ER14250 (14,5 x 25 mm) i holder ca. 27 x 16
        L, W, D = 30.0, 40.0, 15.6
    else:               # kort 40 x 25, AA Li-SOCl2 (14,5 x 50,5 mm) i holder ca. 57 x 17
        L, W, D = 59.0, 44.0, 15.6
    i = (v['groove_w'] + 2 * v['groove_wall'] - v['wall']) if v['felt'] else 0
    x0, x1 = -i - v['wall'], L + i + v['wall']
    e = Enclosure('brikke-' + size.lower(), L, W, D, v, side_ears(L, W, v, x0, x1, (0.5,)), corner=3.0)
    fz = e.fz
    # kort over batteriet: to lave ribber som skiller batterirommet (y 0–16,5) fra kortet
    e.rib(1, 17.0, L - 1, 18.0, 2.0)
    # vindu for fototransistor eller bryter mot underlaget
    e.floor_hole(L / 2, 30 if size == 'S' else 32, 3.0)
    return e


# ======================================================================
# Kamerapod: 30 x 30 x 22 mm, kort 25 x 25, glassvindu bak små åpninger
# ======================================================================
def kamerapod(vn):
    felt = vn == 'felt'
    S, Hb = 30.0, 20.0
    w = 2.0 if felt else 1.8
    front = 2.8
    r = 3.0
    body = rbox(0, 0, 0, S, S, Hb, r)
    cav = rbox(w, w, front, S - w, S - w, Hb + 1, r - w)
    body = body - cav
    # monteringsfot på undersiden (y = 0) med to M3-innsatser
    foot = box(5, -4, 4, 25, 0.5, 18)
    body = body + foot
    # hjørnetapper for M2-innsatser til baklokket
    for cx, cy in ((w + 2.2, w + 2.2), (S - w - 2.2, w + 2.2), (w + 2.2, S - w - 2.2), (S - w - 2.2, S - w - 2.2)):
        body = body + cyl(cx, cy, Hb - 8, Hb, 2.6, 32)
        body = body + cyl(cx, cy, Hb - 8 - 2.4, Hb - 8 + 0.01, 0.3, 32, r2=2.6)   # 45° kjegle under, så tappen printes uten støtte
    cuts = []
    for cx, cy in ((w + 2.2, w + 2.2), (S - w - 2.2, w + 2.2), (w + 2.2, S - w - 2.2), (S - w - 2.2, S - w - 2.2)):
        cuts.append(cyl(cx, cy, Hb - INSERT_M2_DEPTH, Hb + 1, INSERT_M2 / 2, 32))
    # glass: 24 x 16 x 1,1 mm (herdet eller kuttet objektglass) limt inn fra innsiden
    cuts.append(box(S / 2 - 12.2, S / 2 - 8.2, front - 1.2, S / 2 + 12.2, S / 2 + 8.2, front + 0.5))
    # åpninger i fronten: objektiv, to IR-dioder og nærhetssensor (SJEKK mot kortet)
    cuts.append(cyl(S / 2, S / 2 + 1, -1, front, 2.3, 32))
    cuts.append(cyl(S / 2 - 8.5, S / 2 + 1, -1, front, 1.7, 32))
    cuts.append(cyl(S / 2 + 8.5, S / 2 + 1, -1, front, 1.7, 32))
    cuts.append(cyl(S / 2, S / 2 - 5.5, -1, front, 1.2, 32))
    for fx in (10, 20):
        cuts.append(cyl(fx, 11, -4.5, 0.6, INSERT_M3 / 2, 32, 'y'))
    body = body - union_all(cuts)
    # baklokk med kabelinngang og strekkavlaster
    t = 2.0
    lid = rbox(0, 0, 0, S, S, t, r)
    lip_o = rbox(w + CLR, w + CLR, t, S - w - CLR, S - w - CLR, t + 2.0, max(r - w - CLR, 0.3))
    lip_i = rbox(w + CLR + 1.2, w + CLR + 1.2, t - 1, S - w - CLR - 1.2, S - w - CLR - 1.2, t + 3, 0.3)
    lid = lid + (lip_o - lip_i)
    # lokkets kant må gå klar av hjørnetappene
    for cx, cy in ((w + 2.2, w + 2.2), (S - w - 2.2, w + 2.2), (w + 2.2, S - w - 2.2), (S - w - 2.2, S - w - 2.2)):
        lid = lid - cyl(cx, cy, t - 0.01, t + 3, 3.0, 32)
    lid = lid + cyl(S / 2, S / 2, t - 0.01, t + 6, 5.0, 32)  # strekkavlaster på innsiden
    lc = [cyl(S / 2, S / 2, -1, t + 7, 2.9, 32)]          # kabel ca. 5,5 mm med stålflettet strømpe (SJEKK)
    for cx, cy in ((w + 2.2, w + 2.2), (S - w - 2.2, w + 2.2), (w + 2.2, S - w - 2.2), (S - w - 2.2, S - w - 2.2)):
        lc.append(cyl(cx, cy, -1, t + 1, CLEAR_M2 / 2, 32))
        lc.append(cyl(cx, cy, -1, 0.8, HEAD_M2 / 2, 32))
    lid = lid - union_all(lc)
    # brakett: plate med to hull for maskinen og en vippetunge med dreiepunkt og bueslisse
    br = box(0, 0, 0, 34, 24, 3.0)
    br = br - cyl(6, 12, -1, 4, 2.25, 32) - cyl(28, 12, -1, 4, 2.25, 32)
    br = br - cyl(6, 12, 1.8, 4, 4.3, 32, r2=4.3) - cyl(28, 12, 1.8, 4, 4.3, 32)
    tongue = box(7, 10.5, 3.0, 27, 14.5, 24.0)
    br = br + tongue
    slot = []
    slot.append(cyl(10, 15, 9.0, 16.0, CLEAR_M3 / 2, 32, 'y'))        # dreiepunkt (matcher innsats x = 10)
    for k in range(-6, 7):                                            # bueslisse rundt dreiepunktet, ±30°
        a = math.radians(5 * k)
        slot.append(cyl(10 + 10 * math.cos(a), 15 + 10 * math.sin(a), 9.0, 16.0, CLEAR_M3 / 2, 24, 'y'))
    br = br - union_all(slot)
    return body, lid, br


# ======================================================================
def build_unit(name, vn, out):
    os.makedirs(out, exist_ok=True)
    files = []
    if name == 'kamerapod':
        body, lid, br = kamerapod(vn)
        parts = [('hus', body), ('baklokk', lid), ('brakett', br)]
        size = (30.0, 34.0, 22.0)
    else:
        e = {'hovedenhet': hovedenhet, 'utvidelsesboks': utvidelsesboks, 'sensornode': sensornode,
             'brikke-s': lambda v: brikke(v, 'S'), 'brikke-l': lambda v: brikke(v, 'L')}[name](vn)
        base = e.build_base(); lid = e.build_lid()
        parts = [('bunn', base), ('lokk', e.lid_for_print(lid))]
        size = e.size()
    for pn, s in parts:
        p = os.path.join(out, f'varde-{name}-{pn}-{vn}.stl')
        n = s.save_stl(p, f'Varde {name} {pn} {vn}')
        files.append((p, n))
    return files, size


UNITS = ['hovedenhet', 'kamerapod', 'brikke-s', 'brikke-l', 'sensornode', 'utvidelsesboks']

if __name__ == '__main__':
    want = sys.argv[1:] or UNITS
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stl')
    def work():
        for u in want:
            for vn in ('prototype', 'felt'):
                files, size = build_unit(u, vn, out)
                print(f'{u:15s} {vn:9s} ytre mål {size[0]} x {size[1]} x {size[2]} mm  ' + ', '.join(f'{os.path.basename(p)} ({n} trekanter)' for p, n in files))
    run_big_stack(work)
