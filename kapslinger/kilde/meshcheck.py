"""Sjekk av STL: åpne kanter (T-koblinger), volum, mål."""
import struct, sys, collections
def load(p):
    d=open(p,'rb').read(); n=struct.unpack('<I',d[80:84])[0]; T=[]
    for i in range(n):
        f=struct.unpack('<12f',d[84+50*i:84+50*i+48]); T.append((f[3:6],f[6:9],f[9:12]))
    return T
def check(p):
    T=load(p); q=lambda v: tuple(round(c,3) for c in v)
    E=collections.Counter()
    for a,b,c in T:
        for u,v in ((a,b),(b,c),(c,a)): E[(q(u),q(v))]+=1
    bad=sum(1 for (u,v),k in E.items() if E.get((v,u),0)!=k)
    xs=[v for t in T for v in t]
    mn=[min(v[i] for v in xs) for i in range(3)]; mx=[max(v[i] for v in xs) for i in range(3)]
    return len(T), bad, [round(mx[i]-mn[i],2) for i in range(3)]
if __name__=='__main__':
    import glob  # Windows utvider ikke * selv
    for a in sys.argv[1:]:
        for p in sorted(glob.glob(a)) or [a]: print(p, check(p))
