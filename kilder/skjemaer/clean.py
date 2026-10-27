import sys
for fn in sys.argv[1:]:
    L=open(fn).read().split('\n'); out=[]
    for l in L:
        if 'if False' not in l: out.append(l); continue
        ind=l[:len(l)-len(l.lstrip())]
        keep=[]
        for p in [p.strip() for p in l.strip().split('; ')]:
            if ' if False else ' in p:
                alt=p.split(' if False else ')[1]
                if alt!='None': keep.append(alt)
            else: keep.append(p)
        if keep: out.append(ind+'; '.join(keep))
    open(fn,'w').write('\n'.join(out))
