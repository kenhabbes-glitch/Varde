# Enkel tegnemotor for elektriske skjemaark (SVG, mm-enheter, A3 liggende).
from html import escape as _e

W, H = 420, 297
INK = '#1a1a1a'
NET = '#0b4f9c'     # nettnavn
PWR = '#b3261e'     # forsyning
NOTE = '#5b5b57'
FILL = '#fffbe8'    # IC-fyll

class Board:
    def __init__(self, code, name, rev='0.1'):
        self.code, self.name, self.rev = code, name, rev
        self.cnt = {}
        self.sheets = []
        self.bom = []   # (ref, verdi, beskrivelse)
        self.nets = []
    def ref(self, p):
        self.cnt[p] = self.cnt.get(p, 0) + 1
        return f'{p}{self.cnt[p]}'

class Sheet:
    def __init__(self, board, title):
        self.b, self.title = board, title
        self.o = []
        board.sheets.append(self)

    # ---------- grunnleggende ----------
    def raw(self, s): self.o.append(s)
    def line(self, x1, y1, x2, y2, w=0.25, c=INK, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.o.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{c}" stroke-width="{w}"{d}/>')
    def wire(self, *pts, c=INK):
        p = ' '.join(f'{x:.2f},{y:.2f}' for x, y in pts)
        self.o.append(f'<polyline points="{p}" fill="none" stroke="{c}" stroke-width="0.3" stroke-linejoin="round"/>')
    def hv(self, a, b):  # horisontalt så vertikalt
        self.wire(a, (b[0], a[1]), b)
    def vh(self, a, b):
        self.wire(a, (a[0], b[1]), b)
    def dot(self, p):
        self.o.append(f'<circle cx="{p[0]:.2f}" cy="{p[1]:.2f}" r="0.6" fill="{INK}"/>')
    def text(self, x, y, s, size=2.0, anchor='start', c=INK, weight='normal', rot=0, italic=False):
        t = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ''
        st = ' font-style="italic"' if italic else ''
        self.o.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" fill="{c}" font-weight="{weight}"{st}{t}>{_e(s)}</text>')
    def rect(self, x, y, w, h, fill='none', c=INK, sw=0.3, dash=None, r=0):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.o.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{r}" fill="{fill}" stroke="{c}" stroke-width="{sw}"{d}/>')

    def block(self, x, y, w, h, label):
        """Stiplet ramme rundt en funksjonsblokk."""
        self.rect(x, y, w, h, c='#8a8a85', sw=0.25, dash='2 1.2', r=1.5)
        self.text(x + 2, y + 4, label, 2.6, weight='bold', c='#55554f')

    def note(self, x, y, lines, size=1.9, w=None, title=None):
        lh = size * 1.35
        n = len(lines) + (1 if title else 0)
        if w:
            self.rect(x - 1.5, y - size - 1.2, w, n * lh + 2.2, fill='#f4f3ef', c='#c9c7c0', sw=0.2, r=1)
        yy = y
        if title:
            self.text(x, yy, title, size, weight='bold', c=NOTE); yy += lh
        for l in lines:
            self.text(x, yy, l, size, c=NOTE); yy += lh

    # ---------- nett og forsyning ----------
    def label(self, p, name, side='r', stub=0.0, c=None):
        """Nettnavn som flagg. side = retning fra punktet."""
        x, y = p
        c = c or NET
        self.b.nets.append((name, self.title))
        if stub:
            dx = {'r': stub, 'l': -stub, 'u': 0, 'd': 0}[side]; dy = {'u': -stub, 'd': stub, 'r': 0, 'l': 0}[side]
            self.wire((x, y), (x + dx, y + dy)); x += dx; y += dy
        tw = len(name) * 1.38 + 2.6
        h = 2.8
        if side in 'rl':
            s = 1 if side == 'r' else -1
            pts = [(x, y), (x + s * 1.2, y - h / 2), (x + s * tw, y - h / 2), (x + s * tw, y + h / 2), (x + s * 1.2, y + h / 2)]
            self.o.append('<polygon points="%s" fill="#fff" stroke="%s" stroke-width="0.22"/>' % (' '.join(f'{a:.2f},{b:.2f}' for a, b in pts), c))
            self.text(x + s * (1.7 if s > 0 else tw - 0.5), y + 0.7, name, 1.9, 'start', c) if s > 0 else self.text(x - 1.7, y + 0.7, name, 1.9, 'end', c)
        else:
            s = -1 if side == 'u' else 1
            self.wire((x, y), (x, y + s * 1.5), c=c)
            self.text(x, y + s * 1.5 + (-0.7 if s < 0 else 2.4), name, 1.9, 'middle', c)
        return (x, y)

    def wname(self, p, name, c=None):
        """Nettnavn skrevet over en ledning (samme nett som et flagg med samme navn)."""
        self.b.nets.append((name, self.title))
        self.text(p[0], p[1] - 1.0, name, 1.8, 'middle', c or NET)

    def pwr(self, p, name, side='u'):
        x, y = p
        self.b.nets.append((name, self.title))
        if side == 'u':
            self.wire((x, y), (x, y - 2.5)); self.line(x - 1.6, y - 2.5, x + 1.6, y - 2.5, 0.35, PWR)
            self.text(x, y - 3.4, name, 1.9, 'middle', PWR, 'bold')
        elif side == 'r':
            self.wire((x, y), (x + 2.5, y)); self.line(x + 2.5, y - 1.6, x + 2.5, y + 1.6, 0.35, PWR)
            self.text(x + 3.2, y + 0.7, name, 1.9, 'start', PWR, 'bold')
        elif side == 'd':
            self.wire((x, y), (x, y + 2.5)); self.line(x - 1.6, y + 2.5, x + 1.6, y + 2.5, 0.35, PWR)
            self.text(x, y + 5.2, name, 1.9, 'middle', PWR, 'bold')
        else:
            self.wire((x, y), (x - 2.5, y)); self.line(x - 2.5, y - 1.6, x - 2.5, y + 1.6, 0.35, PWR)
            self.text(x - 3.2, y + 0.7, name, 1.9, 'end', PWR, 'bold')

    def gnd(self, p, kind='GND'):
        x, y = p
        self.wire((x, y), (x, y + 2))
        for i, w in enumerate((1.8, 1.2, 0.6)):
            self.line(x - w, y + 2 + i * 0.7, x + w, y + 2 + i * 0.7, 0.3)
        if kind != 'GND':
            self.text(x + 2, y + 3.5, kind, 1.5, 'start', NOTE)

    # ---------- to-terminal komponenter ----------
    def _two(self, p, o, L, draw, ref, val, lab_side=None):
        """p = startpunkt, o = 'h' eller 'v'. Tegner ledning inn til symbolet. Returnerer (a, b)."""
        x, y = p
        a, b = (x, y), ((x + L, y) if o == 'h' else (x, y + L))
        cx, cy = (x + L / 2, y) if o == 'h' else (x, y + L / 2)
        draw(cx, cy, o)
        if ref:
            if o == 'h':
                self.text(cx, cy - 2.6, ref, 1.8, 'middle')
                if val: self.text(cx, cy + 4.0, val, 1.7, 'middle', NOTE)
            else:
                side = lab_side or 'r'
                if side == 'r':
                    self.text(cx + 2.6, cy - 0.3, ref, 1.8)
                    if val: self.text(cx + 2.6, cy + 2.0, val, 1.7, 'start', NOTE)
                else:
                    self.text(cx - 2.6, cy - 0.3, ref, 1.8, 'end')
                    if val: self.text(cx - 2.6, cy + 2.0, val, 1.7, 'end', NOTE)
        return a, b

    def _leads(self, cx, cy, o, half, L):
        if o == 'h':
            self.line(cx - L / 2, cy, cx - half, cy, 0.3); self.line(cx + half, cy, cx + L / 2, cy, 0.3)
        else:
            self.line(cx, cy - L / 2, cx, cy - half, 0.3); self.line(cx, cy + half, cx, cy + L / 2, 0.3)

    def R(self, p, o='h', val='', L=10, ref=None, side=None, desc='Motstand'):
        ref = ref or self.b.ref('R'); self.b.bom.append((ref, val, desc))
        def d(cx, cy, o):
            self._leads(cx, cy, o, 3, L)
            if o == 'h': self.rect(cx - 3, cy - 1.1, 6, 2.2, fill='#fff', sw=0.3)
            else: self.rect(cx - 1.1, cy - 3, 2.2, 6, fill='#fff', sw=0.3)
        return self._two(p, o, L, d, ref, val, side)

    def C(self, p, o='v', val='', L=8, ref=None, side=None, pol=False, desc='Kondensator'):
        ref = ref or self.b.ref('C'); self.b.bom.append((ref, val, desc))
        def d(cx, cy, o):
            g = 0.7
            self._leads(cx, cy, o, g, L)
            if o == 'h':
                self.line(cx - g, cy - 2, cx - g, cy + 2, 0.45); self.line(cx + g, cy - 2, cx + g, cy + 2, 0.45 if not pol else 0.9)
                if pol: self.text(cx - 2.4, cy - 1.6, '+', 1.8)
            else:
                self.line(cx - 2, cy - g, cx + 2, cy - g, 0.45); self.line(cx - 2, cy + g, cx + 2, cy + g, 0.45 if not pol else 0.9)
                if pol: self.text(cx - 3.2, cy - 1.2, '+', 1.8)
        return self._two(p, o, L, d, ref, val, side)

    def Lind(self, p, o='h', val='', L=10, ref=None, side=None, ferrite=False, desc='Spole'):
        ref = ref or self.b.ref('FB' if ferrite else 'L'); self.b.bom.append((ref, val, 'Ferrittperle' if ferrite else desc))
        def d(cx, cy, o):
            self._leads(cx, cy, o, 3, L)
            if ferrite:
                if o == 'h': self.rect(cx - 3, cy - 1.1, 6, 2.2, fill=INK)
                else: self.rect(cx - 1.1, cy - 3, 2.2, 6, fill=INK)
                return
            if o == 'h':
                path = f'M{cx-3:.2f},{cy:.2f} ' + ' '.join(f'a0.75,0.75 0 0 1 1.5,0' for _ in range(4))
            else:
                path = f'M{cx:.2f},{cy-3:.2f} ' + ' '.join(f'a0.75,0.75 0 0 1 0,1.5' for _ in range(4))
            self.o.append(f'<path d="{path}" fill="none" stroke="{INK}" stroke-width="0.3"/>')
        return self._two(p, o, L, d, ref, val, side)

    def D(self, p, o='h', val='', L=10, ref=None, kind='d', flip=False, side=None, desc='Diode'):
        """kind: d (diode), s (schottky), z (zener), tvs (enveis), tvsb (toveis), led. Anode ved p, katode ved enden (flip snur)."""
        pref = 'D'
        ref = ref or self.b.ref(pref); self.b.bom.append((ref, val, desc if desc != 'Diode' else {'tvs': 'TVS-diode', 'tvsb': 'TVS-diode toveis', 'led': 'LED', 's': 'Schottky-diode', 'z': 'Zenerdiode'}.get(kind, desc)))
        def d(cx, cy, o):
            self._leads(cx, cy, o, 1.6, L)
            s = -1 if flip else 1
            def tri(cx, cy, s, o):
                if o == 'h': pts = [(cx - 1.6 * s, cy - 1.6), (cx - 1.6 * s, cy + 1.6), (cx + 1.6 * s, cy)]
                else: pts = [(cx - 1.6, cy - 1.6 * s), (cx + 1.6, cy - 1.6 * s), (cx, cy + 1.6 * s)]
                self.o.append('<polygon points="%s" fill="none" stroke="%s" stroke-width="0.3"/>' % (' '.join(f'{a:.2f},{b:.2f}' for a, b in pts), INK))
            if kind == 'tvsb':
                # to trekanter mot hverandre
                if o == 'h':
                    self.o.append(f'<polygon points="{cx-1.6:.2f},{cy-1.6:.2f} {cx-1.6:.2f},{cy+1.6:.2f} {cx:.2f},{cy:.2f}" fill="none" stroke="{INK}" stroke-width="0.3"/>')
                    self.o.append(f'<polygon points="{cx+1.6:.2f},{cy-1.6:.2f} {cx+1.6:.2f},{cy+1.6:.2f} {cx:.2f},{cy:.2f}" fill="none" stroke="{INK}" stroke-width="0.3"/>')
                    self.wire((cx - 0.6, cy - 2.2), (cx, cy - 1.6), (cx, cy + 1.6), (cx + 0.6, cy + 2.2))
                else:
                    self.o.append(f'<polygon points="{cx-1.6:.2f},{cy-1.6:.2f} {cx+1.6:.2f},{cy-1.6:.2f} {cx:.2f},{cy:.2f}" fill="none" stroke="{INK}" stroke-width="0.3"/>')
                    self.o.append(f'<polygon points="{cx-1.6:.2f},{cy+1.6:.2f} {cx+1.6:.2f},{cy+1.6:.2f} {cx:.2f},{cy:.2f}" fill="none" stroke="{INK}" stroke-width="0.3"/>')
                    self.wire((cx - 2.2, cy + 0.6), (cx - 1.6, cy), (cx + 1.6, cy), (cx + 2.2, cy - 0.6))
                return
            tri(cx, cy, s, o)
            # katodestrek
            if o == 'h':
                kx = cx + 1.6 * s
                if kind in ('z', 'tvs'): self.wire((kx - 0.6 * s, cy - 2.2), (kx, cy - 1.6), (kx, cy + 1.6), (kx + 0.6 * s, cy + 2.2))
                elif kind == 's': self.wire((kx + 0.6, cy - 1.0), (kx + 0.6, cy - 1.6), (kx, cy - 1.6), (kx, cy + 1.6), (kx - 0.6, cy + 1.6), (kx - 0.6, cy + 1.0))
                else: self.line(kx, cy - 1.6, kx, cy + 1.6, 0.3)
            else:
                ky = cy + 1.6 * s
                if kind in ('z', 'tvs'): self.wire((cx - 2.2, ky - 0.6 * s), (cx - 1.6, ky), (cx + 1.6, ky), (cx + 2.2, ky + 0.6 * s))
                elif kind == 's': self.wire((cx - 1.0, ky - 0.6), (cx - 1.6, ky - 0.6), (cx - 1.6, ky), (cx + 1.6, ky), (cx + 1.6, ky + 0.6), (cx + 1.0, ky + 0.6))
                else: self.line(cx - 1.6, ky, cx + 1.6, ky, 0.3)
            if kind == 'led':
                for k in (0, 1.4):
                    if o == 'h': self.wire((cx + 0.5 + k, cy - 2), (cx + 1.8 + k, cy - 3.4))
                    else: self.wire((cx + 2 , cy - 0.5 + k), (cx + 3.4, cy + 0.8 + k))
        return self._two(p, o, L, d, ref, val, side)

    def F(self, p, o='h', val='', L=10, ref=None, side=None):
        ref = ref or self.b.ref('F'); self.b.bom.append((ref, val, 'Sikring'))
        def d(cx, cy, o):
            self._leads(cx, cy, o, 3, L)
            if o == 'h': self.rect(cx - 3, cy - 1.1, 6, 2.2, fill='#fff'); self.line(cx - 3, cy, cx + 3, cy, 0.3)
            else: self.rect(cx - 1.1, cy - 3, 2.2, 6, fill='#fff'); self.line(cx, cy - 3, cx, cy + 3, 0.3)
        return self._two(p, o, L, d, ref, val, side)

    def X(self, p, o='h', val='', L=10, ref=None, side=None, desc='Krystall'):
        ref = ref or self.b.ref('Y'); self.b.bom.append((ref, val, desc))
        def d(cx, cy, o):
            self._leads(cx, cy, o, 2, L)
            if o == 'h':
                self.line(cx - 2, cy - 1.8, cx - 2, cy + 1.8, 0.4); self.line(cx + 2, cy - 1.8, cx + 2, cy + 1.8, 0.4)
                self.rect(cx - 1.2, cy - 1.4, 2.4, 2.8, fill='#fff')
            else:
                self.line(cx - 1.8, cy - 2, cx + 1.8, cy - 2, 0.4); self.line(cx - 1.8, cy + 2, cx + 1.8, cy + 2, 0.4)
                self.rect(cx - 1.4, cy - 1.2, 2.8, 2.4, fill='#fff')
        return self._two(p, o, L, d, ref, val, side)

    def SW(self, p, o='h', val='', L=10, ref=None, side=None, nc=False, desc='Bryter'):
        ref = ref or self.b.ref('S'); self.b.bom.append((ref, val, desc))
        def d(cx, cy, o):
            self._leads(cx, cy, o, 3, L)
            if o == 'h':
                self.dot((cx - 3, cy)); self.dot((cx + 3, cy))
                self.line(cx - 3, cy, cx + 2.6, cy - (0.4 if nc else 2.2), 0.3)
                if nc: self.line(cx + 3, cy, cx + 3, cy - 1.0, 0.3)
            else:
                self.dot((cx, cy - 3)); self.dot((cx, cy + 3))
                self.line(cx, cy - 3, cx - (0.4 if nc else 2.2), cy + 2.6, 0.3)
        return self._two(p, o, L, d, ref, val, side)

    # ---------- flerterminal ----------
    def fet(self, p, ch='n', ref=None, val='', desc=None):
        """MOSFET. p = gate-punkt (venstre). Returnerer dict g, d, s. Drain opp for n, ned for p."""
        ref = ref or self.b.ref('Q'); self.b.bom.append((ref, val, desc or f'MOSFET {ch.upper()}-kanal'))
        x, y = p
        bx = x + 5
        self.line(x, y, bx, y, 0.3)
        self.line(bx, y - 2.5, bx, y + 2.5, 0.35)        # gate-plate
        self.line(bx + 1, y - 2.8, bx + 1, y + 2.8, 0.5)  # kanal
        top, bot = (bx + 4, y - 6), (bx + 4, y + 6)
        self.wire((bx + 1, y - 2), (bx + 4, y - 2), top)
        self.wire((bx + 1, y + 2), (bx + 4, y + 2), bot)
        # pil
        if ch == 'n': self.o.append(f'<polygon points="{bx+1.2:.2f},{y+2:.2f} {bx+2.6:.2f},{y+1.3:.2f} {bx+2.6:.2f},{y+2.7:.2f}" fill="{INK}"/>')
        else: self.o.append(f'<polygon points="{bx+2.6:.2f},{y-2:.2f} {bx+1.2:.2f},{y-2.7:.2f} {bx+1.2:.2f},{y-1.3:.2f}" fill="{INK}"/>')
        self.text(bx + 5.5, y - 0.2, ref, 1.8); self.text(bx + 5.5, y + 2.1, val, 1.6, 'start', NOTE)
        if ch == 'n': return {'g': (x, y), 'd': top, 's': bot}
        return {'g': (x, y), 's': top, 'd': bot}

    def ant(self, p, label=''):
        x, y = p
        self.wire((x, y), (x, y - 5))
        self.wire((x - 2.2, y - 8.5), (x, y - 5), (x + 2.2, y - 8.5)); self.line(x, y - 5, x, y - 8.5, 0.3)
        if label: self.text(x + 3, y - 6.5, label, 1.8)

    def ic(self, x, y, w, ref, value, left=(), right=(), top=(), bottom=(), pitch=4.0, plen=4.0, desc='', sub=''):
        """IC som boks. Pinner gis som lister med navn; None = tom plass. Navn 'GND#2' vises som 'GND'.
        Returnerer dict navn -> (x, y, side)."""
        n = max(len(left), len(right), 1)
        h = (n + 1) * pitch
        if top or bottom:
            w = max(w, (max(len(top), len(bottom)) + 1) * pitch)
        self.b.bom.append((ref, value, desc))
        self.rect(x, y, w, h, fill=FILL, sw=0.35)
        if bottom:
            self.text(x + w / 2, y - 4.4, ref, 2.2, 'middle', weight='bold')
            self.text(x + w / 2, y - 1.4, value, 1.8, 'middle')
        else:
            self.text(x + w / 2, y - 1.5, ref, 2.2, 'middle', weight='bold')
            self.text(x + w / 2, y + h + 3.2, value, 2.0, 'middle')
            if sub: self.text(x + w / 2, y + h + 5.6, sub, 1.6, 'middle', NOTE)
        pins = {}
        for i, nm in enumerate(left):
            if nm is None: continue
            py = y + pitch * (i + 1)
            self.line(x - plen, py, x, py, 0.3)
            self.text(x + 1.0, py + 0.65, nm.split('#')[0], 1.7)
            pins[nm] = (x - plen, py, 'l')
        for i, nm in enumerate(right):
            if nm is None: continue
            py = y + pitch * (i + 1)
            self.line(x + w, py, x + w + plen, py, 0.3)
            self.text(x + w - 1.0, py + 0.65, nm.split('#')[0], 1.7, 'end')
            pins[nm] = (x + w + plen, py, 'r')
        for i, nm in enumerate(top):
            if nm is None: continue
            px = x + pitch * (i + 1)
            self.line(px, y - plen, px, y, 0.3)
            self.text(px + 0.6, y + 1.2, nm.split('#')[0], 1.6, 'start', rot=90)
            pins[nm] = (px, y - plen, 'u')
        for i, nm in enumerate(bottom):
            if nm is None: continue
            px = x + pitch * (i + 1)
            self.line(px, y + h, px, y + h + plen, 0.3)
            self.text(px + 0.6, y + h - 1.2, nm.split('#')[0], 1.6, 'end', rot=90)
            pins[nm] = (px, y + h + plen, 'd')
        pins['_box'] = (x, y, w, h)
        return pins

    def pl(self, pins, name, net, stub=3.0, kind='net'):
        """Nett på en IC-pinne: kind 'net' (flagg), 'gnd', 'pwr', 'nc'."""
        x, y, side = pins[name]
        if kind == 'nc':
            dx = {'l': -1, 'r': 1, 'u': 0, 'd': 0}[side]; dy = {'u': -1, 'd': 1, 'l': 0, 'r': 0}[side]
            self.line(x - 0.9, y - 0.9, x + 0.9, y + 0.9, 0.3); self.line(x - 0.9, y + 0.9, x + 0.9, y - 0.9, 0.3)
            return
        if kind == 'gnd':
            if side in 'lr':
                ex = x + (-stub if side == 'l' else stub)
                self.wire((x, y), (ex, y)); self.gnd((ex, y))
            else:
                self.gnd((x, y))
            return
        if kind == 'pwr':
            if side in 'lr':
                ex = x + (-stub if side == 'l' else stub)
                self.wire((x, y), (ex, y)); self.pwr((ex, y), net, side)
            else:
                self.pwr((x, y), net, 'u' if side == 'u' else 'u')
            return
        self.label((x, y), net, side, stub)

    def gndjoin(self, P, names, stub=3.0):
        """Flere pinner på samme side koples sammen til én jord."""
        pts = [P[n] for n in names]
        side = pts[0][2]
        xs = pts[0][0] + (stub if side == 'r' else -stub)
        for x, y, _ in pts: self.wire((x, y), (xs, y))
        ys = sorted(p[1] for p in pts)
        self.wire((xs, ys[0]), (xs, ys[-1])); self.gnd((xs, ys[-1]))
        for y in ys[:-1]: self.dot((xs, y))

    def pins(self, P, mapping, stub=3.0):
        for k, v in mapping.items():
            if v is None: continue
            if v == 'GND': self.pl(P, k, v, stub, 'gnd')
            elif v == 'NC': self.pl(P, k, v, stub, 'nc')
            elif v.startswith('+'): self.pl(P, k, v[1:], stub, 'pwr')
            else: self.pl(P, k, v, stub)

    def conn(self, x, y, ref, value, pins, side='r', pitch=4.0, desc='Kontakt'):
        """Kontakt: pins = liste med (nr, navn). Returnerer dict navn -> punkt på pinneenden."""
        self.b.bom.append((ref, value, desc))
        n = len(pins); h = (n + 1) * pitch; w = max(9, max(len(nm) for _, nm in pins) * 1.05 + 6)
        self.rect(x, y, w, h, fill='#eef3f8', sw=0.35)
        self.text(x + w / 2, y - 1.5, ref, 2.2, 'middle', weight='bold')
        self.text(x + w / 2, y + h + 3.2, value, 1.8, 'middle')
        out = {}
        for i, (nr, nm) in enumerate(pins):
            py = y + pitch * (i + 1)
            if side == 'r':
                self.line(x + w, py, x + w + 4, py, 0.3); self.text(x + 1, py + 0.65, str(nr), 1.6, 'start', NOTE)
                self.text(x + w - 1, py + 0.65, nm.split('#')[0], 1.6, 'end')
                out[nm] = (x + w + 4, py, 'r')
            else:
                self.line(x - 4, py, x, py, 0.3); self.text(x + w - 1, py + 0.65, str(nr), 1.6, 'end', NOTE)
                self.text(x + 1, py + 0.65, nm.split('#')[0], 1.6)
                out[nm] = (x - 4, py, 'l')
        return out

    # ---------- side ----------
    def svg(self, idx, total, date):
        b = self.b
        f = []
        f.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm" font-family="Helvetica, Arial, sans-serif">')
        f.append(f'<rect width="{W}" height="{H}" fill="#fff"/>')
        f.append(f'<rect x="8" y="8" width="{W-16}" height="{H-16}" fill="none" stroke="{INK}" stroke-width="0.5"/>')
        # rutereferanser
        for i in range(8):
            xx = 8 + (W - 16) / 8 * i
            f.append(f'<text x="{xx + (W-16)/16:.1f}" y="6.6" font-size="2.2" text-anchor="middle" fill="{NOTE}">{i+1}</text>')
            if i: f.append(f'<line x1="{xx:.1f}" y1="8" x2="{xx:.1f}" y2="10" stroke="{INK}" stroke-width="0.3"/>')
        for i, L in enumerate('ABCDEF'):
            yy = 8 + (H - 16) / 6 * i
            f.append(f'<text x="5" y="{yy + (H-16)/12 + 0.8:.1f}" font-size="2.2" text-anchor="middle" fill="{NOTE}">{L}</text>')
            if i: f.append(f'<line x1="8" y1="{yy:.1f}" x2="10" y2="{yy:.1f}" stroke="{INK}" stroke-width="0.3"/>')
        f.extend(self.o)
        # tittelfelt
        tx, ty, tw, th = W - 8 - 170, H - 8 - 26, 170, 26
        f.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" fill="#fff" stroke="{INK}" stroke-width="0.45"/>')
        for yy in (ty + 9, ty + 17.5):
            f.append(f'<line x1="{tx}" y1="{yy}" x2="{tx+tw}" y2="{yy}" stroke="{INK}" stroke-width="0.25"/>')
        f.append(f'<line x1="{tx+110}" y1="{ty+9}" x2="{tx+110}" y2="{ty+th}" stroke="{INK}" stroke-width="0.25"/>')
        f.append(f'<line x1="{tx+140}" y1="{ty+9}" x2="{tx+140}" y2="{ty+th}" stroke="{INK}" stroke-width="0.25"/>')
        def t(x, y, s, size=2.0, wgt='normal', c=INK):
            f.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{wgt}" fill="{c}">{_e(s)}</text>')
        t(tx + 2, ty + 3.2, 'GPS Vs Tyv · Elektrisk skjema', 1.7, c=NOTE)
        t(tx + 2, ty + 7.6, f'{b.code} {b.name} – {self.title}', 3.0, 'bold')
        t(tx + 2, ty + 11.6, 'Status', 1.5, c=NOTE); t(tx + 2, ty + 15.6, 'Utkast. Pinnenummer og verdier kontrolleres mot datablad.', 2.0)
        t(tx + 112, ty + 11.6, 'Revisjon', 1.5, c=NOTE); t(tx + 112, ty + 15.6, b.rev, 2.4, 'bold')
        t(tx + 142, ty + 11.6, 'Ark', 1.5, c=NOTE); t(tx + 142, ty + 15.6, f'{idx} av {total}', 2.4, 'bold')
        t(tx + 2, ty + 20.2, 'Tegnet', 1.5, c=NOTE); t(tx + 2, ty + 24.2, 'Claude (utkast for anbud)', 2.0)
        t(tx + 112, ty + 20.2, 'Dato', 1.5, c=NOTE); t(tx + 112, ty + 24.2, date, 2.0)
        t(tx + 142, ty + 20.2, 'Format', 1.5, c=NOTE); t(tx + 142, ty + 24.2, 'A3', 2.0)
        f.append('</svg>')
        return '\n'.join(f)
