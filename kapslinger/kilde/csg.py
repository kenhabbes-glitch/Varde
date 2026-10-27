"""Liten CSG-motor (BSP-trær), port av Evan Wallace sin csg.js (MIT-lisens).
Brukes for å lage kapslingene uten eksterne pakker. Kun standardbiblioteket.
Alle mål i millimeter.
"""
import math, struct, sys, threading

sys.setrecursionlimit(1_000_000)
EPS = 1e-5

COPLANAR, FRONT, BACK, SPANNING = 0, 1, 2, 3


def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)
def unit(a):
    l = math.sqrt(dot(a, a))
    return (a[0] / l, a[1] / l, a[2] / l)


class Plane:
    __slots__ = ('n', 'w')
    def __init__(self, n, w): self.n, self.w = n, w
    @staticmethod
    def from_points(a, b, c):
        n = unit(cross(sub(b, a), sub(c, a)))
        return Plane(n, dot(n, a))
    def clone(self): return Plane(self.n, self.w)
    def flip(self): self.n = (-self.n[0], -self.n[1], -self.n[2]); self.w = -self.w

    def split(self, poly, cof, cob, front, back):
        n, w = self.n, self.w
        types, ptype = [], 0
        for v in poly.v:
            t = dot(n, v) - w
            ty = BACK if t < -EPS else (FRONT if t > EPS else COPLANAR)
            ptype |= ty; types.append(ty)
        if ptype == COPLANAR:
            (cof if dot(n, poly.plane.n) > 0 else cob).append(poly)
        elif ptype == FRONT: front.append(poly)
        elif ptype == BACK: back.append(poly)
        else:
            f, b = [], []
            vs = poly.v; k = len(vs)
            for i in range(k):
                j = (i + 1) % k
                ti, tj = types[i], types[j]
                vi, vj = vs[i], vs[j]
                if ti != BACK: f.append(vi)
                if ti != FRONT: b.append(vi)
                if (ti | tj) == SPANNING:
                    t = (w - dot(n, vi)) / dot(n, sub(vj, vi))
                    v = lerp(vi, vj, t)
                    f.append(v); b.append(v)
            if len(f) >= 3: front.append(Polygon(f, poly.plane))
            if len(b) >= 3: back.append(Polygon(b, poly.plane))


def newell(vs):
    """Plan fra polygon med Newells metode (robust mot kolineære hjørner)."""
    nx = ny = nz = 0.0
    k = len(vs)
    for i in range(k):
        a, b = vs[i], vs[(i + 1) % k]
        nx += (a[1] - b[1]) * (a[2] + b[2]); ny += (a[2] - b[2]) * (a[0] + b[0]); nz += (a[0] - b[0]) * (a[1] + b[1])
    n = unit((nx, ny, nz))
    c = mul(tuple(sum(v[i] for v in vs) for i in range(3)), 1.0 / k)
    return Plane(n, dot(n, c))


class Polygon:
    __slots__ = ('v', 'plane')
    def __init__(self, v, plane=None):
        self.v = list(v)
        self.plane = plane if plane is not None else newell(self.v)
    def clone(self): return Polygon(list(self.v), self.plane.clone())
    def flip(self): self.v.reverse(); self.plane = self.plane.clone(); self.plane.flip()


class Node:
    __slots__ = ('plane', 'front', 'back', 'polys')
    def __init__(self, polys=None):
        self.plane = None; self.front = None; self.back = None; self.polys = []
        if polys: self.build(polys)

    def invert(self):
        stack = [self]
        while stack:
            nd = stack.pop()
            for p in nd.polys: p.flip()
            if nd.plane: nd.plane.flip()
            nd.front, nd.back = nd.back, nd.front
            if nd.front: stack.append(nd.front)
            if nd.back: stack.append(nd.back)

    def clip_polygons(self, polys):
        if not self.plane: return list(polys)
        f, b = [], []
        for p in polys: self.plane.split(p, f, b, f, b)
        if self.front: f = self.front.clip_polygons(f)
        b = self.back.clip_polygons(b) if self.back else []
        return f + b

    def clip_to(self, bsp):
        stack = [self]
        while stack:
            nd = stack.pop()
            nd.polys = bsp.clip_polygons(nd.polys)
            if nd.front: stack.append(nd.front)
            if nd.back: stack.append(nd.back)

    def all_polygons(self):
        out, stack = [], [self]
        while stack:
            nd = stack.pop()
            out.extend(nd.polys)
            if nd.front: stack.append(nd.front)
            if nd.back: stack.append(nd.back)
        return out

    def build(self, polys):
        work = [(self, polys)]
        while work:
            nd, ps = work.pop()
            if not ps: continue
            if not nd.plane: nd.plane = ps[0].plane.clone()
            f, b = [], []
            for p in ps: nd.plane.split(p, nd.polys, nd.polys, f, b)
            if f:
                if not nd.front: nd.front = Node()
                work.append((nd.front, f))
            if b:
                if not nd.back: nd.back = Node()
                work.append((nd.back, b))


class Solid:
    def __init__(self, polys=None): self.polys = polys or []
    def clone(self): return Solid([p.clone() for p in self.polys])

    def bbox(self):
        xs = [v for p in self.polys for v in p.v]
        return (tuple(min(v[i] for v in xs) for i in range(3)), tuple(max(v[i] for v in xs) for i in range(3)))

    def _bbox_hit(self, other):
        (a0, a1), (b0, b1) = self.bbox(), other.bbox()
        return all(a0[i] <= b1[i] + EPS and b0[i] <= a1[i] + EPS for i in range(3))

    def __add__(self, o):  # union
        if not self.polys: return o.clone()
        if not o.polys: return self.clone()
        if not self._bbox_hit(o): return Solid([p.clone() for p in self.polys] + [p.clone() for p in o.polys])
        a, b = Node(self.clone().polys), Node(o.clone().polys)
        a.clip_to(b); b.clip_to(a); b.invert(); b.clip_to(a); b.invert()
        a.build(b.all_polygons())
        return Solid(a.all_polygons())

    def __sub__(self, o):  # difference
        if not o.polys or not self._bbox_hit(o): return self.clone()
        a, b = Node(self.clone().polys), Node(o.clone().polys)
        a.invert(); a.clip_to(b); b.clip_to(a); b.invert(); b.clip_to(a); b.invert()
        a.build(b.all_polygons()); a.invert()
        return Solid(a.all_polygons())

    def __mul__(self, o):  # intersection
        a, b = Node(self.clone().polys), Node(o.clone().polys)
        a.invert(); b.clip_to(a); b.invert(); a.clip_to(b); b.clip_to(a)
        a.build(b.all_polygons()); a.invert()
        return Solid(a.all_polygons())

    def map(self, f):
        out = []
        for p in self.polys:
            vs = [f(v) for v in p.v]
            out.append(Polygon(vs))
        return Solid(out)

    def translate(self, x=0, y=0, z=0): return self.map(lambda v: (v[0] + x, v[1] + y, v[2] + z))

    def rotate(self, ax, deg):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        if ax == 'x': f = lambda v: (v[0], v[1] * c - v[2] * s, v[1] * s + v[2] * c)
        elif ax == 'y': f = lambda v: (v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)
        else: f = lambda v: (v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2])
        return self.map(f)

    def mirror_x(self, x0=0):
        s = self.map(lambda v: (2 * x0 - v[0], v[1], v[2]))
        for p in s.polys: p.flip()
        return s

    # ---------- eksport ----------
    def triangles(self):
        for p in self.polys:
            v = p.v
            for i in range(1, len(v) - 1):
                yield v[0], v[i], v[i + 1], p.plane.n

    def watertight_triangles(self, q=1e-4, cell=2.0):
        """Triangler uten T-koblinger: hjørner sveises, og punkter som ligger på en kant settes inn i kanten.
        Konvekse polygoner med flere enn tre hjørner deles fra midtpunktet, så ingen trekanter får null areal."""
        snap = lambda v: (round(v[0] / q) * q, round(v[1] / q) * q, round(v[2] / q) * q)
        def area2(vs):
            nx = ny = nz = 0.0
            for i in range(len(vs)):
                a, b = vs[i], vs[(i + 1) % len(vs)]
                nx += (a[1] - b[1]) * (a[2] + b[2]); ny += (a[2] - b[2]) * (a[0] + b[0]); nz += (a[0] - b[0]) * (a[1] + b[1])
            return math.sqrt(nx * nx + ny * ny + nz * nz)
        # sveis hjørner, fjern like nabopunkter og flater uten areal
        clean, normals = [], []
        for p in self.polys:
            vs = [snap(v) for v in p.v]
            out = [v for i, v in enumerate(vs) if v != vs[i - 1]]
            if len(out) >= 3 and area2(out) > 1e-7:
                clean.append(out); normals.append(p.plane.n)
        verts = {v for vs in clean for v in vs}
        grid = {}
        for v in verts:
            grid.setdefault((int(v[0] // cell), int(v[1] // cell), int(v[2] // cell)), []).append(v)
        tol = q * 2
        def on_edge(a, b):
            d = sub(b, a); L2 = dot(d, d)
            if L2 < tol * tol: return []
            lo = [int(min(a[i], b[i]) // cell) for i in range(3)]; hi = [int(max(a[i], b[i]) // cell) for i in range(3)]
            hits = []
            for gx in range(lo[0], hi[0] + 1):
                for gy in range(lo[1], hi[1] + 1):
                    for gz in range(lo[2], hi[2] + 1):
                        for v in grid.get((gx, gy, gz), ()):
                            if v == a or v == b: continue
                            t = dot(sub(v, a), d) / L2
                            if t <= 1e-9 or t >= 1 - 1e-9: continue
                            pr = add(a, mul(d, t)); e = sub(v, pr)
                            if dot(e, e) < tol * tol: hits.append((t, v))
            hits.sort()
            return [v for _, v in hits]
        cache = {}
        tris = []
        for vs, n in zip(clean, normals):
            ring = []
            k = len(vs)
            for i in range(k):
                a, b = vs[i], vs[(i + 1) % k]
                key = (a, b)
                if key not in cache:
                    rev = cache.get((b, a))
                    cache[key] = list(reversed(rev)) if rev is not None else on_edge(a, b)
                ring.append(a); ring.extend(cache[key])
            if len(ring) == 3:
                tris.append((ring[0], ring[1], ring[2], n))
            else:
                c = mul(tuple(sum(v[i] for v in ring) for i in range(3)), 1.0 / len(ring))
                for i in range(len(ring)):
                    tris.append((c, ring[i], ring[(i + 1) % len(ring)], n))
        return tris

    def save_stl(self, path, name='varde'):
        tris = self.watertight_triangles()
        with open(path, 'wb') as fh:
            fh.write(name.encode()[:80].ljust(80, b' '))
            fh.write(struct.pack('<I', len(tris)))
            for a, b, c, n in tris:
                fh.write(struct.pack('<12fH', *n, *a, *b, *c, 0))
        return len(tris)

    def volume(self):
        vol = 0.0
        for a, b, c, _ in self.triangles(): vol += dot(a, cross(b, c)) / 6.0
        return vol


# ---------- grunnformer ----------
def box(x0, y0, z0, x1, y1, z1):
    """Boks fra hjørne (x0,y0,z0) til (x1,y1,z1)."""
    P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)]
    return Solid([Polygon([P[i] for i in f]) for f in faces])


def cyl(x, y, z0, z1, r, seg=48, axis='z', r2=None):
    """Sylinder (eller kjegle med r2) langs z fra z0 til z1, sentrert i (x, y).
    axis='x' eller 'y' legger den langs den aksen: da er (x, y) koordinatene på tvers og z0/z1 langs aksen."""
    r2 = r if r2 is None else r2
    pts0 = [(r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    pts1 = [(r2 * math.cos(2 * math.pi * i / seg), r2 * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    def P(u, v, w):
        if axis == 'z': return (x + u, y + v, w)
        if axis == 'x': return (w, x + u, y + v)
        return (x + u, w, y + v)  # axis y: (x, z) på tvers
    bot = [P(*pts0[i], z0) for i in range(seg)]
    top = [P(*pts1[i], z1) for i in range(seg)]
    polys = []
    flip = axis == 'y'  # y-aksen gir speilvendt orientering
    def poly(vs):
        if flip: vs = list(reversed(vs))
        return Polygon(vs)
    polys.append(poly(list(reversed(bot))))
    polys.append(poly(top))
    for i in range(seg):
        j = (i + 1) % seg
        quad = [bot[i], bot[j], top[j], top[i]]
        polys.append(poly(quad))
    return Solid(polys)


def rbox(x0, y0, z0, x1, y1, z1, r, seg=32):
    """Boks med avrundede vertikale kanter (radius r)."""
    if r <= 0: return box(x0, y0, z0, x1, y1, z1)
    s = box(x0 + r, y0, z0, x1 - r, y1, z1) + box(x0, y0 + r, z0, x1, y1 - r, z1)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x1 - r, y1 - r), (x0 + r, y1 - r)):
        s = s + cyl(cx, cy, z0, z1, r, seg)
    return s


def rframe(x0, y0, x1, y1, z0, z1, r, w, seg=32):
    """Ramme (rundet rektangel minus innsiden) med bredde w."""
    return rbox(x0, y0, z0, x1, y1, z1, r, seg) - rbox(x0 + w, y0 + w, z0 - 1, x1 - w, y1 - w, z1 + 1, max(r - w, 0.01), seg)


def union_all(items):
    """Slår sammen mange deler parvis (raskere enn én og én)."""
    items = [i for i in items if i is not None and i.polys]
    if not items: return Solid()
    while len(items) > 1:
        nxt = []
        for i in range(0, len(items), 2):
            nxt.append(items[i] + items[i + 1] if i + 1 < len(items) else items[i])
        items = nxt
    return items[0]


def run_big_stack(fn):
    """Kjører fn i en tråd med stor stakk (BSP-rekursjon i clip_polygons)."""
    threading.stack_size(512 * 1024 * 1024)
    res = {}
    t = threading.Thread(target=lambda: res.setdefault('v', fn()))
    t.start(); t.join()
    return res.get('v')
