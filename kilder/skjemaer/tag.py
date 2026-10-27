from lib import Sheet, NOTE, NET
from common import swd

def sheet_tag(B, variant='S'):
    L = variant == 'L'
    rail = '3V0' if L else '1V8'
    s = Sheet(B, 'Komplett skjema' + (' (med LoRa 868 MHz)' if L else ''))

    # ---------- A batteri og forsyning ----------
    s.block(14, 16, 196, 92, 'A  Batteri og forsyning')
    BT = s.conn(22, 32, s.b.ref('BT'), 'ER14250 (1/2 AA)' if not L else 'Li-SOCl2 AA (ER14505)', [('+', 'BAT+'), ('−', 'BAT−')], pitch=6, desc=('Li-SOCl2 1/2 AA 3,6 V ca. 1 200 mAh, holder med O-ring' if not L else 'Li-SOCl2 AA 3,6 V ca. 2 400–2 700 mAh, holder med O-ring'))
    p = BT['BAT+'][:2]
    s.wire(p, (p[0] + 50, p[1])); s.text(p[0] + 4, p[1] - 1.4, 'VBAT', 1.8, 'start', NET)
    s.dot((p[0] + 10, p[1])); c = s.C((p[0] + 10, p[1]), 'v', '470 µF lav lekkasje' if not L else '2 × 470 µF lav lekkasje', L=8, pol=True, desc='Lekkasjefattig bufferkondensator (f.eks. polymer)'); s.gnd(c[1])
    g = BT['BAT−'][:2]; s.wire(g, (g[0] + 4, g[1])); s.gnd((g[0] + 4, g[1]))
    U = s.ic(p[0] + 54, p[1] - 4, 22, s.b.ref('U'), 'TPS62840', left=['VIN', None, 'EN', 'VSET', 'MODE'], right=['VOS', 'SW', 'STOP', 'GND'], pitch=5, desc='Buck 60 nA hvilestrøm')
    s.wire((p[0] + 50, p[1]), U['VIN'][:2])
    s.wire(U['EN'][:2], (U['EN'][0] - 3, U['EN'][1]), (U['EN'][0] - 3, p[1])); s.dot((U['EN'][0] - 3, p[1]))
    vs = U['VSET'][:2]; s.wire(vs, (vs[0] - 9, vs[1])); r = s.R((vs[0] - 9, vs[1]), 'v', f'VSET for {rail[0]},{rail[2]} V*', L=8, side='l'); s.gnd(r[1])
    s.pl(U, 'MODE', '', 3, 'gnd')
    sw = U['SW'][:2]; l = s.Lind(sw, 'h', '2,2 µH', L=12)
    o = (l[1][0] + 12, sw[1]); s.wire(l[1], o); s.dot((l[1][0] + 4, sw[1])); c = s.C((l[1][0] + 4, sw[1]), 'v', '10 µF', L=6); s.gnd(c[1])
    s.wire(U['VOS'][:2], (o[0], U['VOS'][1]), o); s.pwr((o[0], U['VOS'][1]), rail, 'u')
    s.gndjoin(U, ['STOP', 'GND'])
    s.note(22, 88, ['Li-SOCl2-celler gir dårlig toppstrøm. Bufferkondensatoren tar radiopulsene,', 'og cella lader den langsomt opp igjen.' + (' LoRa (120 mA) krever hybrid-' if L else ''),
                    ('kondensator (HLC) eller større buffer, og begrenset sendehyppighet.' if L else 'Batteriet byttes med verktøy og registreres i appen.')], w=184)

    # ---------- B nRF54L15 ----------
    s.block(216, 16, 194, 150, 'B  nRF54L15 (BLE Coded PHY, NFC)')
    left = ['VDD', 'DCC', 'DECD', 'DEC#', None, 'XC1', 'XC2', 'XL1', 'XL2', None, 'SWDIO', 'SWDCLK', 'nRESET', None, 'VSS']
    right = ['ANT', None, 'NFC1', 'NFC2', None, 'GPIO (SDA)', 'GPIO (SCL)', 'GPIO (ACC_INT)', 'GPIO (BARO_INT)', 'GPIO (REMOVE)', 'GPIO (LED)'] + (['SPIM (SCK)', 'SPIM (MOSI)', 'SPIM (MISO)', 'GPIO (NSS)', 'GPIO (BUSY)', 'GPIO (DIO1)', 'GPIO (NRST)', 'GPIO (LORA_EN)'] if L else [])
    N = s.ic(276, 28, 40, s.b.ref('U'), 'nRF54L15 (QFN48)', left=left, right=right, pitch=4.5 if not L else 4.0, desc='Nordic nRF54L15 SoC', sub='DC/DC, avkopling og pinner etter Nordic referanse')
    s.label(N['VDD'][:2], rail, 'l', 3)
    s.text(N['DCC'][0] - 3, N['DCC'][1] + 0.7, 'DC/DC-spole 4,7 µH*', 1.5, 'end', NOTE); s.wire(N['DCC'][:2], (N['DCC'][0] - 1, N['DCC'][1]))
    for nm in ['DECD', 'DEC#']:
        s.wire(N[nm][:2], (N[nm][0] - 1, N[nm][1]))
    s.text(N['DEC#'][0] - 3, N['DEC#'][1] + 0.7, 'avkopling etter ref.', 1.5, 'end', NOTE)
    x1, x2 = N['XC1'][:2], N['XC2'][:2]; xx = x1[0] - 8
    s.wire(x1, (xx, x1[1])); s.wire(x2, (xx, x2[1])); s.X((xx, x1[1]), 'v', '', L=4.5 if not L else 4, side='l', desc='Krystall 32 MHz')
    s.text(xx - 3, x1[1] + 3, '32 MHz', 1.5, 'end', NOTE)
    l1, l2 = N['XL1'][:2], N['XL2'][:2]; xx2 = l1[0] - 8
    s.wire(l1, (xx2, l1[1])); s.wire(l2, (xx2, l2[1])); s.X((xx2, l1[1]), 'v', '', L=4.5 if not L else 4, side='l', desc='Krystall 32,768 kHz')
    s.text(xx2 - 3, l1[1] + 3, '32,768 kHz', 1.5, 'end', NOTE)
    s.label(N['SWDIO'][:2], 'T_SWDIO', 'l', 3); s.label(N['SWDCLK'][:2], 'T_SWDCLK', 'l', 3); s.label(N['nRESET'][:2], 'T_RESET', 'l', 3)
    s.pl(N, 'VSS', '', 3, 'gnd')
    s.label(N['ANT'][:2], 'RF_2G4', 'r', 3)
    s.label(N['NFC1'][:2], 'NFC1', 'r', 3); s.label(N['NFC2'][:2], 'NFC2', 'r', 3)
    nets = {'GPIO (SDA)': 'I2C_SDA', 'GPIO (SCL)': 'I2C_SCL', 'GPIO (ACC_INT)': 'ACC_INT', 'GPIO (BARO_INT)': 'BARO_INT', 'GPIO (REMOVE)': 'REMOVE', 'GPIO (LED)': 'LED',
            'SPIM (SCK)': 'L_SCK', 'SPIM (MOSI)': 'L_MOSI', 'SPIM (MISO)': 'L_MISO', 'GPIO (NSS)': 'L_NSS', 'GPIO (BUSY)': 'L_BUSY', 'GPIO (DIO1)': 'L_DIO1', 'GPIO (NRST)': 'L_NRST', 'GPIO (LORA_EN)': 'LORA_EN'}
    for k, v in nets.items():
        if k in N: s.label(N[k][:2], v, 'r', 3)
    swd(s, 226, 128 if L else 118, 'T_', vref=rail)

    # ---------- C antenner ----------
    s.block(14, 114, 196, 62, 'C  2,4 GHz-antenne og NFC-spole')
    y0 = 136
    s.label((30, y0), 'RF_2G4', 'l', 0); s.wire((30, y0), (36, y0))
    c1 = s.C((36, y0), 'v', 'DNP', L=7, side='l'); s.gnd(c1[1]); s.dot((36, y0))
    l1 = s.Lind((36, y0), 'h', '0 Ω*', L=12, desc='Tilpasning, settes ved måling')
    c2 = s.C(l1[1], 'v', 'DNP', L=7); s.gnd(c2[1]); s.dot(l1[1])
    s.wire(l1[1], (l1[1][0] + 12, y0)); s.ant((l1[1][0] + 12, y0), 'AE1 chipantenne 2,4 GHz')
    # NFC
    s.label((116, 132), 'NFC1', 'l', 0); s.label((116, 152), 'NFC2', 'l', 0)
    s.wire((116, 132), (130, 132)); s.wire((116, 152), (130, 152))
    s.dot((122, 132)); c = s.C((122, 132), 'v', 'C_tune*', L=6, side='l', desc='NFC-avstemming'); s.gnd(c[1])
    s.dot((126, 152)); c = s.C((126, 152), 'v', 'C_tune*', L=6, side='l', desc='NFC-avstemming'); s.gnd(c[1])
    lc = s.Lind((130, 132), 'v', 'NFC-spole i kortet', L=20, desc='NFC-spole som kobberbane'); s.wire(lc[1], (130, 152))
    s.note(22, 170, ['Pi-nett avstemmes i kapslingen. NFC-spolen ligger langs kortkanten', 'mot plastsiden; avstemmes til 13,56 MHz.'], w=184)

    # ---------- D sensorer ----------
    s.block(14, 182, 196, 74, 'D  Bevegelse, løft og fjerning')
    A = s.ic(50, 192, 24, s.b.ref('U'), 'LIS2DW12', left=['VDD', 'VDD_IO', 'SA0', 'CS'], right=['SDA', 'SCL', 'INT1', 'GND'], pitch=5, desc='Akselerometer, vekking ved bevegelse')
    for nm in ['VDD', 'VDD_IO', 'CS']: s.label(A[nm][:2], rail, 'l', 3)
    s.pl(A, 'SA0', '', 3, 'gnd')
    s.label(A['SDA'][:2], 'I2C_SDA', 'r', 3); s.label(A['SCL'][:2], 'I2C_SCL', 'r', 3); s.label(A['INT1'][:2], 'ACC_INT', 'r', 3); s.pl(A, 'GND', '', 3, 'gnd')
    Bp = s.ic(144, 192, 24, s.b.ref('U'), 'BMP585', left=['VDD', 'VDDIO', 'CSB', 'SDO'], right=['SDA', 'SCL', 'INT', 'GND'], pitch=5, desc='Barometer for løftdeteksjon')
    for nm in ['VDD', 'VDDIO', 'CSB']: s.label(Bp[nm][:2], rail, 'l', 3)
    s.pl(Bp, 'SDO', '', 3, 'gnd')
    s.label(Bp['SDA'][:2], 'I2C_SDA', 'r', 3); s.label(Bp['SCL'][:2], 'I2C_SCL', 'r', 3); s.label(Bp['INT'][:2], 'BARO_INT', 'r', 3); s.pl(Bp, 'GND', '', 3, 'gnd')
    sw_ = s.SW((92, 236), 'h', 'Fjerningsbryter', L=12, desc='Bryter mot underlaget (fjerning)'); s.label((92, 236), 'REMOVE', 'l', 0); s.wire(sw_[1], (sw_[1][0] + 2, 236)); s.gnd((sw_[1][0] + 2, 236))
    s.label((150, 236), 'LED', 'l', 0); r = s.R((150, 236), 'h', '2,2 kΩ', L=10); d = s.D(r[1], 'h', 'Service', L=10, kind='led'); s.wire(d[1], (d[1][0] + 2, 236)); s.gnd((d[1][0] + 2, 236))
    s.b.bom.append(('AE1', 'Chipantenne 2,4 GHz', 'BLE-antenne'))
    if L: s.b.bom.append(('AE2', 'Helix/chipantenne 868 MHz', 'LoRa-antenne'))
    s.note(22, 244, ['I2C pull-up 100 kΩ (lav strøm, lav hastighet). Barometeret startes av akselerometeret.', 'REMOVE: bryter mot underlaget til GND (intern pull-up), eller fototransistor.'], w=184)

    if not L:
        s.block(216, 172, 194, 84, 'E  Strømbudsjett (anslag)')
        rows = [('Søvn med akselerometer i lavstrøm', 'ca. 1–2 µA'), ('BLE-annonsering (Coded PHY) hvert 10–30 s', 'ca. 2–5 µA snitt'), ('Barometer ved bevegelse', '< 1 µA snitt'), ('Buck TPS62840', '60 nA'), ('Sum (S)', '5–10 µA → 5–8 år')]
        for k, (a_, b_) in enumerate(rows):
            s.text(224, 190 + k * 7, a_, 1.9, 'start', '#1a1a1a', 'bold' if k == 4 else 'normal'); s.text(330, 190 + k * 7, b_, 1.9, 'start', NET)
        s.note(224, 236, ['Tallene må måles på prototype. Kulde reduserer kapasiteten.'], w=180)
    else:
        s.block(216, 172, 194, 84, 'E  LoRa 868 MHz med lastbryter')
        S = s.ic(234, 184, 20, s.b.ref('U'), 'TPS22916', left=['VIN', 'ON'], right=['VOUT', 'GND'], pitch=5, desc='Lastbryter for LoRa (null lekkasje i søvn)')
        s.label(S['VIN'][:2], rail, 'l', 3); s.label(S['ON'][:2], 'LORA_EN', 'l', 3); s.pl(S, 'GND', '', 3, 'gnd')
        vo = S['VOUT'][:2]; s.wire(vo, (vo[0] + 10, vo[1])); s.pwr((vo[0] + 10, vo[1]), '3V0_LORA', 'u')
        E = s.ic(322, 182, 26, s.b.ref('U'), 'E22-900M22S', left=['VCC', 'NSS', 'SCK', 'MOSI', 'MISO', 'BUSY', 'DIO1', 'NRST'], right=['ANT', 'TXEN', 'DIO2', 'RXEN', 'GND'], pitch=4.2, desc='LoRa-modul SX1262')
        s.label(E['VCC'][:2], '3V0_LORA', 'l', 3)
        for nm, net in [('NSS', 'L_NSS'), ('SCK', 'L_SCK'), ('MOSI', 'L_MOSI'), ('MISO', 'L_MISO'), ('BUSY', 'L_BUSY'), ('DIO1', 'L_DIO1'), ('NRST', 'L_NRST')]: s.label(E[nm][:2], net, 'l', 3)
        t, d2 = E['TXEN'][:2], E['DIO2'][:2]; s.wire(t, (t[0] + 3, t[1]), (t[0] + 3, d2[1]), d2)
        s.text(E['RXEN'][0] + 3, E['RXEN'][1] + 0.7, 'RXEN: invertert DIO2 eller GPIO*', 1.4, 'start', NOTE); s.wire(E['RXEN'][:2], (E['RXEN'][0] + 1, E['RXEN'][1]))
        s.pl(E, 'GND', '', 3, 'gnd')
        a = E['ANT'][:2]; s.wire(a, (a[0] + 10, a[1])); s.ant((a[0] + 10, a[1]), 'AE2 868 MHz')
        s.note(224, 244, ['Snitt 10–20 µA med én LoRa-melding per time og BLE hvert 30 s (anslag).'], w=180)
    return s
