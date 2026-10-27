from lib import Sheet, NOTE, NET
from common import buck

def sheet_power_in(B):
    s = Sheet(B, 'Strøminngang, vern, 5 V og sireneutgang')

    # ---------- A  maskinkontakt og inngangsvern ----------
    s.block(14, 16, 118, 118, 'A  Maskinkontakt og inngangsvern')
    J1 = s.conn(20, 30, 'J1', 'Deutsch DT04-08P', [(1, 'VIN'), (2, 'GND'), (3, 'IGN'), (4, 'SIREN+'), (5, 'SIREN−'), (6, 'GPS_LOOP_A'), (7, 'GPS_LOOP_B'), (8, 'RESERVE')], pitch=5, desc='Maskinkontakt 8-pin, IP67')
    x, y, _ = J1['VIN']
    a, b = s.F((x, y), 'h', '1 A treg', L=12)
    n1 = (b[0] + 4, y); s.wire(b, n1); s.dot(n1)
    s.label(n1, 'VIN_F', 'u', 0)
    ta, tb = s.D(n1, 'v', 'SMCJ36A', L=12, kind='tvs', flip=True); s.gnd(tb)
    Q1 = s.ic(n1[0] + 21, y - 4, 14, B.ref('Q'), 'N-MOSFET 60 V', left=['S'], right=['D'], bottom=['G'], pitch=4, desc='N-MOSFET 60 V, lav RDS(on), for ideell diode')
    sp = Q1['S'][:2]; s.wire(n1, sp)
    tap = (sp[0] - 4, y); s.dot(tap)
    dp = Q1['D'][:2]; vp = (dp[0] + 24, y); s.wire(dp, vp); s.dot(vp)
    s.label(vp, 'VIN_PROT', 'r', 3)
    U1 = s.ic(n1[0] + 23, y + 24, 24, 'U1', 'LM74700-Q1', left=['ANODE', 'EN', 'GND'], right=['GATE', 'CATHODE', 'VCAP'], pitch=4.5, desc='Ideell diode-kontroller')
    g = Q1['G'][:2]; gy = y + 16
    s.wire(g, (g[0], gy), (U1['GATE'][0] + 4, gy), (U1['GATE'][0] + 4, U1['GATE'][1]), U1['GATE'][:2])
    s.wire(U1['CATHODE'][:2], (vp[0], U1['CATHODE'][1]), vp)
    s.wire(tap, (tap[0], U1['ANODE'][1]), U1['ANODE'][:2])
    s.dot((tap[0], U1['ANODE'][1]))
    s.wire((tap[0], U1['ANODE'][1]), (tap[0], U1['EN'][1]), U1['EN'][:2])
    s.pl(U1, 'GND', '', 3, 'gnd')
    vc = U1['VCAP'][:2]; ca, cb = s.C((vc[0] + 4, vc[1]), 'v', '0,1 µF', L=8); s.wire(vc, ca); s.gnd(cb)
    gx2, gy2, _ = J1['GND']; s.wire((gx2, gy2), (gx2 + 5, gy2)); s.gnd((gx2 + 5, gy2))
    for nm, net in [('IGN', 'IGN_IN'), ('SIREN+', 'SIREN+'), ('SIREN−', 'SIREN−'), ('GPS_LOOP_A', 'GPS_LOOP_A'), ('GPS_LOOP_B', 'GPS_LOOP_B')]:
        s.label(J1[nm][:2], net, 'r', 3)
    s.pl(J1, 'RESERVE', '', kind='nc')
    s.note(20, 112, ['Koples før maskinens hovedstrømbryter.', 'TVS etter ISO 7637-2 / ISO 16750-2 (24 V-anlegg, lastdump', 'begrenset sentralt). Q1 + U1 hindrer feilpolaritet og', 'tilbakemating. Alle kontaktpinner har ESD-vern.'], w=106, title='Merknader')

    # ---------- B  buck 5 V ----------
    s.block(140, 16, 172, 118, 'B  Buck 9–36 V → 5 V (til lader og batterivarme)')
    buck(s, 140, 16, vin='VIN_PROT', out='5V_BUCK', rtop='100 kΩ 1 %', rbot='31,6 kΩ 1 %', ind='27 µH*', ref='U2')
    s.note(150, 108, ['VOUT = 1,2 V × (1 + 100k / 31,6k) ≈ 5,0 V.', 'UVLO ca. 8,5 V på / 7,5 V av (beregnes).', 'RON settes for ca. 400 kHz, L1 for rippel ≈ 40 %.', '* = beregnes ved design etter datablad.'], w=150, title='Dimensjonering')

    # ---------- C  maskinspenning og strømbrudd ----------
    s.block(318, 16, 92, 118, 'C  Maskinspenning og strømbrudd')
    X = 342
    s.label((332, 30), 'VIN_PROT', 'l', 0); s.wire((332, 30), (X, 30))
    r = s.R((X, 30), 'v', '1 MΩ', L=10, side='l'); s.wire(r[1], (X, 44)); s.dot((X, 44))
    r = s.R((X, 44), 'v', '82 kΩ', L=10, side='l'); s.gnd(r[1])
    r = s.R((X, 44), 'h', '10 kΩ', L=12); s.dot(r[1])
    c = s.C(r[1], 'v', '100 nF', L=8); s.gnd(c[1])
    s.label(r[1], 'VIN_SENSE', 'r', 4)

    U3 = s.ic(370, 86, 16, 'U3', 'TLV7031', left=['IN−', 'IN+'], right=['OUT', 'VDD', 'GND'], pitch=4.5, desc='Komparator, nanopower')
    s.label((332, 70), 'VIN_F', 'l', 0); s.wire((332, 70), (X, 70))
    r = s.R((X, 70), 'v', '1 MΩ', L=10, side='l')
    jp = (X, U3['IN+'][1]); s.wire(r[1], jp); s.dot(jp)
    r = s.R(jp, 'v', '100 kΩ', L=10, side='l'); s.gnd(r[1])
    cl = (352, jp[1]); s.wire(jp, cl); s.dot(cl)
    d = s.D(cl, 'v', 'BAT54', L=10, kind='s', flip=True); s.gnd(d[1])
    s.wire(cl, U3['IN+'][:2])
    vx = 360; vt = 62
    s.pwr((vx, vt), '3V3_AON', 'u')
    r = s.R((vx, vt), 'v', '1 MΩ', L=8, side='l'); s.dot(r[1]); nd = r[1]
    r = s.R(nd, 'v', '270 kΩ', L=8, side='l'); s.gnd(r[1])
    s.wire(nd, (364, nd[1]), (364, U3['IN−'][1]), U3['IN−'][:2])
    s.text(365, nd[1] - 1, 'VREF_PF', 1.6, c=NET)
    s.pl(U3, 'VDD', '3V3_AON', 3, 'pwr'); s.pl(U3, 'GND', '', 3, 'gnd')
    s.label(U3['OUT'][:2], 'PFAIL_N', 'r', 2)
    s.note(324, 116, ['VIN_SENSE → AIN0 (P0.13): 36 V gir 2,7 V.', 'VREF_PF 0,70 V → terskel ca. 7,7 V.', 'Hysterese 10 MΩ OUT → IN+ (ikke vist).', 'PFAIL_N lav = maskinstrøm borte → P0.27.'], w=82)

    # ---------- D  tenning ----------
    s.block(14, 142, 118, 74, 'D  Tenningsinngang')
    s.label((24, 166), 'IGN_IN', 'l', 0); s.wire((24, 166), (30, 166)); s.dot((30, 166))
    t = s.D((30, 166), 'v', 'SMAJ36CA', L=10, kind='tvsb', side='l'); s.gnd(t[1])
    d = s.D((30, 166), 'h', 'BAS16', L=10)
    s.wire(d[1], (48, 166))
    r = s.R((48, 166), 'v', '1 MΩ', L=10); s.wire(r[1], (48, 182)); s.dot((48, 182))
    r = s.R((48, 182), 'v', '82 kΩ', L=10, side='l'); s.gnd(r[1])
    r = s.R((48, 182), 'h', '10 kΩ', L=14); s.dot(r[1])
    c = s.C(r[1], 'v', '100 nF', L=8); s.gnd(c[1])
    k = (r[1][0] + 13, 182); s.wire(r[1], k); s.dot(k)
    d = s.D(k, 'v', 'BAT54S', L=8, kind='s', flip=True); s.gnd(d[1])
    s.label(k, 'IGN_SENSE', 'r', 8)
    s.note(22, 206, ['→ AIN6 (P0.19). BAT54S klemmer mot 3V3_AON og GND.'], w=104)

    # ---------- E  sirene ----------
    s.block(140, 142, 172, 74, 'E  Sireneutgang (lavside, maks ca. 2 A)')
    s.label((152, 158), 'VIN_PROT', 'l', 0)
    f = s.F((152, 158), 'h', 'PTC 2 A', L=12)
    s.wire(f[1], (232, 158)); s.dot((214, 158)); s.label((232, 158), 'SIREN+', 'r', 0)
    q = s.fet((180, 192), 'n', val='60 V, logikknivå', desc='N-MOSFET 60 V, RDS(on) < 50 mΩ')
    dpt = (q['d'][0], 174); s.wire(q['d'], dpt); s.dot(dpt)
    s.wire(dpt, (232, 174)); s.label((232, 174), 'SIREN−', 'r', 0)
    s.dot((214, 174))
    # frihjulsdiode: anode SIREN−, katode SIREN+
    dd = s.D((214, 158), 'v', 'SS36', L=16, kind='s', flip=True)
    s.gnd(q['s'])
    r = s.R((156, 192), 'h', '100 Ω', L=12); s.label((156, 192), 'SIREN_EN', 'l', 0)
    s.wire(r[1], q['g']); s.dot((170, 192))
    r = s.R((170, 192), 'v', '100 kΩ', L=10); s.gnd(r[1])
    s.note(150, 210, ['SIREN_EN fra P0.28. Sirene og blinklys koples mellom SIREN+ og SIREN−.'], w=156)

    # ---------- F  strømtre ----------
    s.block(318, 142, 92, 112, 'F  Strømtre (oversikt)')
    rows = [('VIN 12/24 V', 'F1, TVS, Q1/U1 → VIN_PROT'), ('VIN_PROT', 'U2, sirene, EXP_VIN'), ('5V_BUCK', 'U4 lader (ark 2), varme'),
            ('VSYS 3,4–4,4 V', 'nRF9151 VDD, U5, U6'), ('3V3_AON', 'sensorer, ATECC, LoRa, VDD_GPIO'),
            ('3V3_SW', 'GNSS, mikrofon, flash'), ('1V8_RADAR', 'A121 (RADAR_PWR)'), ('3V3_EXP', 'ekspansjon (EXP_EN)'), ('5V_ISO', 'CAN-side (CAN_PWR_EN)')]
    yy = 158
    for a_, b_ in rows:
        s.text(324, yy, a_, 1.8, 'start', '#b3261e', 'bold'); s.text(352, yy, b_, 1.7); yy += 6
    s.note(324, yy + 4, ['VDD_GPIO = 3,3 V fordi ATECC608B krever', 'minst 2,0 V. Alle domener har testpunkt.'], w=82)
    return s
