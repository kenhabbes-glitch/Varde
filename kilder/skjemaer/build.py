import sys, importlib, datetime, html, subprocess, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import Board
DATE = '24.10.2026'

def boards():
    import main1, main2, main3, cam, ub, sn, tag
    B = Board('HE', 'Hovedenhet v1.1')
    main1.sheet_power_in(B)
    main2.sheet_charger(B)
    main2.sheet_nrf9151(B)
    main3.sheet_cop_can(B)
    main3.sheet_radio(B)
    main3.sheet_sensors(B)
    main3.sheet_tamper(B)
    K = Board('KP', 'Kamerapod')
    cam.sheet_cam1(K); cam.sheet_cam2(K)
    U = Board('UB', 'Utvidelsesboks')
    ub.sheet_ub_power(U); ub.sheet_ub_mcu(U); ub.sheet_ub_ports(U); ub.sheet_ub_io(U)
    N = Board('SN', 'Sensornode')
    sn.sheet_node(N)
    S = Board('BS', 'Utstyrsbrikke S')
    tag.sheet_tag(S, 'S')
    Lb = Board('BL', 'Utstyrsbrikke L')
    tag.sheet_tag(Lb, 'L')
    return [B, K, U, N, S, Lb]

def render(bs, out='schem.html', only=None):
    import front
    pages = []
    for B in bs:
        for i, sh in enumerate(B.sheets):
            pages.append(sh.svg(i + 1, len(B.sheets), DATE))
    doc = '<!doctype html><html lang="no"><head><meta charset="utf-8"><title>GPS Vs Tyv – elektriske skjemaer</title><style>' + front.CSS + '</style></head><body>'
    doc += front.cover(bs, DATE, 1)
    doc += ''.join(f'<div class="pg">{p}</div>' for p in pages)
    doc += front.bom(bs)
    doc += '</body></html>'
    open(out, 'w').write(doc)
    return len(pages)

def check(bs):
    import collections
    for B in bs:
        refs = [r for r, _, _ in B.bom if not r.startswith('(')]
        d = [r for r, c in collections.Counter(refs).items() if c > 1]
        if d: print('DUPLIKAT', B.code, sorted(d))
        c = collections.Counter(n for n, _ in B.nets)
        single = sorted(n for n, k in c.items() if k == 1)
        if single: print('ENKELTNETT', B.code, single)

if __name__ == '__main__':
    bs = boards(); check(bs)
    n = render(bs)
    print(n, 'ark')
