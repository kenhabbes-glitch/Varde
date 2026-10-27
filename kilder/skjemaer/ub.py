from lib import Sheet, NOTE, NET
from common import buck, swd, m12

def sheet_ub_power(B):
    s = Sheet(B, 'Forsyning og prosessor (strøm, klokker, programmering)')
    # ---------- A innganger ----------
    s.block(14, 16, 150, 112, 'A  Forsyning: fra hovedenheten eller egen 12/24 V')
    s.label((30, 40), 'EXP_VIN', 'l', 0)
    d1 = s.D((30, 40), 'h', '', L=12, kind='s', desc='Schottky 100 V 5 A, ELLER-kopling')
    jr = s.b.ref('J')
    J2 = s.conn(20, 56, jr, 'Rekkeklemme 2-pol', [(1, '+12/24V'), (2, '0V')], pitch=5, desc='Egen forsyning (brakke/container)')
    p = J2['+12/24V'][:2]
    f = s.F(p, 'h', '5 A', L=10)
    d2 = s.D((f[1][0] + 2, p[1]), 'h', '', L=12, kind='s', desc='Schottky 100 V 5 A, ELLER-kopling'); s.wire(f[1], (f[1][0] + 2, p[1]))
    nx = 76
    s.wire(d1[1], (nx, 40)); s.wire(d2[1], (nx, p[1]), (nx, 40)); s.dot((nx, 40))
    s.text(52, 37, 'D1, D2: Schottky 100 V 5 A', 1.5, 'start', NOTE)
    g = J2['0V'][:2]; s.wire(g, (g[0] + 4, g[1])); s.gnd((g[0] + 4, g[1]))
    s.dot((nx + 10, 40)); t = s.D((nx + 10, 40), 'v', 'SMCJ36A', L=10, kind='tvs', flip=True); s.gnd(t[1])
    s.dot((nx + 26, 40)); c = s.C((nx + 26, 40), 'v', '100 µF 63 V', L=10, pol=True); s.gnd(c[1])
    s.wire((nx, 40), (nx + 44, 40)); s.pwr((nx + 44, 40), 'VBOX', 'u')
    from main2 import divider
    divider(s, 120, 54, 'VBOX', '1 MΩ', '82 kΩ', 'VBOX_SENSE')
    s.note(22, 92, ['VBOX forsyner portene (ark 3) og logikken.', 'EXP_VIN kommer fra hovedenheten (PTC 1,5 A der). Med', 'mange porter eller 360-pod brukes egen forsyning på ' + jr + '.', jr + ' i brakke: 24 V fra innkapslet nettdel med batteri.'], w=136)

    # ---------- B buck 5 V ----------
    buck(s, 170, 16, vin='VBOX', out='5V', rtop='100 kΩ 1 %', rbot='31,6 kΩ 1 %', ind='27 µH*', title='B  Buck 9–36 V → 5 V (relé, CAN, RS-485)', w=176, h=112, note='VOUT ≈ 5,0 V. Maks ca. 1 A.')

    # ---------- C 3V3 ----------
    s.block(352, 16, 58, 112, 'C  5 V → 3,3 V')
    U = s.ic(364, 36, 18, s.b.ref('U'), 'TLV62569', left=['VIN', 'EN'], right=['SW', 'FB', 'GND'], pitch=6, desc='Buck 2 A, 5,5 V inn')
    s.label(U['VIN'][:2], '5V', 'l', 3); s.label(U['EN'][:2], '5V', 'l', 3)
    s.pl(U, 'GND', '', 3, 'gnd')
    sw = U['SW'][:2]; l = s.Lind(sw, 'h', '2,2 µH', L=10); s.wire(l[1], (l[1][0] + 4, sw[1])); s.pwr((l[1][0] + 4, sw[1]), '3V3', 'u')
    s.note(358, 70, ['2 × 22 µF ut.', 'FB-deler 453k / 100k', '(0,6 V ref) ≈ 3,3 V.', 'Maks ca. 0,8 A.'], w=48)
    s.wire(U['FB'][:2], (U['FB'][0] + 2, U['FB'][1]))

    # ---------- D STM32 del A ----------
    s.block(14, 134, 396, 122, 'D  STM32H563, del A: forsyning, klokker og programmering')
    left = ['VDD', 'VDD#2', 'VDD#3', 'VBAT', None, 'VDDA', 'VREF+', None, 'VCAP1', None, 'VCAP2', None, 'VSS', 'VSSA']
    right = ['PH0-OSC_IN', 'PH1-OSC_OUT', 'PC14-OSC32_IN', 'PC15-OSC32_OUT', None, 'NRST', None, None, 'BOOT0', None, 'PA13-SWDIO', 'PA14-SWCLK', 'PB3-SWO']
    B.mcu = s.b.ref('U')
    M = s.ic(110, 144, 40, B.mcu + 'A', 'STM32H563VIT6 (LQFP100)', left=left, right=right, pitch=4.5, desc='STM32H563, 2 × FDCAN, SDMMC, krypto')
    vx = M['VDD'][0]
    s.wire(M['VDD'][:2], (vx - 30, M['VDD'][1])); s.pwr((vx - 30, M['VDD'][1]), '3V3', 'u')
    for nm in ['VDD#2', 'VDD#3', 'VBAT']:
        s.wire(M[nm][:2], (vx - 6, M[nm][1]))
    s.wire((vx - 6, M['VDD'][1]), (vx - 6, M['VBAT'][1])); [s.dot((vx - 6, M[n][1])) for n in ['VDD', 'VDD#2', 'VDD#3']]
    s.text(vx - 20, M['VDD'][1] - 1.5, '4 × 100 nF + 4,7 µF', 1.5, 'middle', NOTE)
    fb = s.Lind((vx - 30, M['VDDA'][1]), 'h', '', L=14, ferrite=True)
    s.wire(fb[1], M['VDDA'][:2]); s.wire(M['VREF+'][:2], (vx - 8, M['VREF+'][1]), (vx - 8, M['VDDA'][1])); s.dot((vx - 8, M['VDDA'][1]))
    s.text(vx - 38, M['VDDA'][1] + 0.7, '3V3', 1.8, 'end', '#b3261e', 'bold'); s.wire((vx - 36, M['VDDA'][1]), fb[0])
    s.text(vx - 10, M['VREF+'][1] + 3.2, 'VDDA/VREF+: 1 µF + 100 nF', 1.5, 'end', NOTE)
    for nm in ['VCAP1', 'VCAP2']:
        p = M[nm][:2]; c = s.C((p[0] - 10, p[1]), 'h', '2,2 µF', L=8); s.wire(c[1], p); s.wire(c[0], (c[0][0] - 2, p[1])); s.gnd((c[0][0] - 2, p[1]))
    s.gndjoin(M, ['VSS', 'VSSA'], 8)
    # klokker
    o1, o2 = M['PH0-OSC_IN'][:2], M['PH1-OSC_OUT'][:2]; xx = o1[0] + 12
    s.wire(o1, (xx, o1[1])); s.wire(o2, (xx, o2[1])); s.X((xx, o1[1]), 'v', '25 MHz', L=4.5)
    l1, l2 = M['PC14-OSC32_IN'][:2], M['PC15-OSC32_OUT'][:2]; xx2 = l1[0] + 12
    s.wire(l1, (xx2, l1[1])); s.wire(l2, (xx2, l2[1])); s.X((xx2, l1[1]), 'v', '32,768 kHz', L=4.5)
    s.text(xx + 12, o2[1] + 0.7, 'lastkondensatorer etter krystall', 1.5, 'start', NOTE)
    n = M['NRST'][:2]; s.wire(n, (n[0] + 8, n[1])); s.dot((n[0] + 8, n[1])); c = s.C((n[0] + 8, n[1]), 'v', '100 nF', L=6); s.gnd(c[1])
    s.label((n[0] + 8, n[1]), 'UB_RESET', 'r', 8)
    b0 = M['BOOT0'][:2]; r = s.R(b0, 'h', '10 kΩ', L=10); s.wire(r[1], (r[1][0] + 2, b0[1])); s.gnd((r[1][0] + 2, b0[1]))
    s.label(M['PA13-SWDIO'][:2], 'UB_SWDIO', 'r', 3); s.label(M['PA14-SWCLK'][:2], 'UB_SWDCLK', 'r', 3); s.pl(M, 'PB3-SWO', '', kind='nc')
    swd(s, 300, 150, 'UB_', ref=s.b.ref('J'))
    s.note(300, 196, ['Programmering låses i produksjon', '(RDP nivå 2 / TrustZone).', 'Signert fastvare via sikker', 'oppstart, oppdatering fra', 'hovedenheten over UART.'], w=104)
    return s


def sheet_ub_mcu(B):
    s = Sheet(B, 'Prosessor del B, eMMC og tilkopling til hovedenheten')
    pins = [('FDCAN1_TX', 'CAN1_TXD'), ('FDCAN1_RX', 'CAN1_RXD'), ('FDCAN2_TX', 'CAN2_TXD'), ('FDCAN2_RX', 'CAN2_RXD'), ('GPIO', 'CAN_STB'), None,
            ('USART1_TX', 'HE_UART_TX'), ('USART1_RX', 'HE_UART_RX'), ('GPIO#exp', 'EXP_INT'), None,
            ('USART2_TX', 'RS485_TX'), ('USART2_RX', 'RS485_RX'), ('USART2_DE', 'RS485_DE'), None,
            ('I2C1_SDA', 'I2C_SDA'), ('I2C1_SCL', 'I2C_SCL'), ('GPIO#lid', 'LID_SW'), ('GPIO#led', 'LED_STATUS'), None,
            ('GPIO#p1', 'PORT1_EN'), ('GPIO#p2', 'PORT2_EN'), ('GPIO#p3', 'PORT3_EN'), ('GPIO#p4', 'PORT4_EN'), ('GPIO#flt', 'PORT_FLT'), None,
            ('GPIO#r1', 'REL1'), ('GPIO#r2', 'REL2')]
    adc = [('ADC1_INP0', 'EOL1'), ('ADC1_INP1', 'EOL2'), ('ADC1_INP2', 'EOL3'), ('ADC1_INP3', 'EOL4'), ('ADC1_INP4', 'EOL5'), ('ADC1_INP5', 'EOL6'), ('ADC1_INP6', 'EOL7'), ('ADC1_INP7', 'EOL8'), None,
           ('ADC2_INP0', 'IMON1'), ('ADC2_INP1', 'IMON2'), ('ADC2_INP2', 'IMON3'), ('ADC2_INP3', 'IMON4'), ('ADC2_INP4', 'VBOX_SENSE'), None,
           ('SDMMC1_CK', 'MMC_CLK'), ('SDMMC1_CMD', 'MMC_CMD'), ('SDMMC1_D0', 'MMC_D0'), ('SDMMC1_D1', 'MMC_D1'), ('SDMMC1_D2', 'MMC_D2'), ('SDMMC1_D3', 'MMC_D3'),
           ('SDMMC1_D4', 'MMC_D4'), ('SDMMC1_D5', 'MMC_D5'), ('SDMMC1_D6', 'MMC_D6'), ('SDMMC1_D7', 'MMC_D7'), ('GPIO#mr', 'MMC_RST')]
    s.block(14, 16, 236, 240, 'A  STM32H563, del B: periferienheter (portnavn settes ved layout)')
    M = s.ic(96, 26, 44, B.mcu + 'B', 'STM32H563VIT6', left=[p[0] if p else None for p in adc], right=[p[0] if p else None for p in pins], pitch=4.2, desc='(samme komponent som U5A)')
    s.b.bom.pop()
    for p in pins:
        if p: s.label(M[p[0]][:2], p[1], 'r', 3)
    for p in adc:
        if p: s.label(M[p[0]][:2], p[1], 'l', 3)
    s.note(22, 152, ['Navn på pinnene viser periferienhet.', 'Endelig pinnetildeling gjøres med', 'STM32CubeMX ved layout.'], w=58)
    s.note(22, 240, ['PORT_FLT: open drain fra alle fire eFuser (wired OR) med 10 kΩ pull-up.', 'IMON gir strøm per port: brudd, kortslutning og unormalt forbruk oppdages.'], w=222)

    # ---------- B eMMC ----------
    s.block(256, 16, 154, 116, 'B  eMMC 8 GB (kryptert bildelagring)')
    E = s.ic(300, 28, 30, s.b.ref('U'), 'eMMC 8 GB (BGA153)', left=['VCC', 'VCCQ', 'VDDI', None, 'RST_n', 'VSS'], right=['CLK', 'CMD', 'DAT0', 'DAT1', 'DAT2', 'DAT3', 'DAT4', 'DAT5', 'DAT6', 'DAT7'], pitch=5, desc='eMMC 5.1, 8 GB, industri (−40 til +85 °C)')
    s.label(E['VCC'][:2], '3V3', 'l', 3); s.label(E['VCCQ'][:2], '3V3', 'l', 3)
    s.text(E['VDDI'][0] - 3, E['VDDI'][1] + 0.7, '1 µF til GND', 1.5, 'end', NOTE); s.wire(E['VDDI'][:2], (E['VDDI'][0] - 1, E['VDDI'][1]))
    s.label(E['RST_n'][:2], 'MMC_RST', 'l', 3); s.pl(E, 'VSS', '', 3, 'gnd')
    for a, b in [('CLK', 'MMC_CLK'), ('CMD', 'MMC_CMD')] + [(f'DAT{i}', f'MMC_D{i}') for i in range(8)]:
        s.label(E[a][:2], b, 'r', 3)
    s.note(262, 104, ['CMD og DAT0–7: 10 kΩ pull-up til 3V3. CLK med 22 Ω serie.', 'Innhold krypteres (AES) med nøkkel i prosessoren.', 'eMMC er mer robust mot vibrasjon enn minnekort.'], w=142)

    # ---------- C ekspansjon ----------
    s.block(256, 138, 154, 118, 'C  Kabel til hovedenheten (J5 der)')
    J = s.conn(276, 150, s.b.ref('J'), 'Molex Micro-Fit 3.0, 10-pin', [(1, 'EXP_VIN'), (2, 'EXP_VIN#'), (3, 'GND'), (4, 'GND#'), (5, '3V3_EXP'), (6, 'RX'), (7, 'TX'), (8, 'EXP_INT'), (9, 'LOOP_A'), (10, 'LOOP_B')], pitch=5, desc='Ekspansjonskontakt, låsende')
    vx, vy = J['EXP_VIN'][:2]
    s.wire((vx, vy), (vx + 4, vy), (vx + 4, J['EXP_VIN#'][1]), J['EXP_VIN#'][:2]); s.dot((vx + 4, vy)); s.label((vx + 4, vy), 'EXP_VIN', 'r', 6)
    g = J['GND'][:2]; s.wire(g, (g[0] + 4, g[1]), (g[0] + 4, J['GND#'][1]), J['GND#'][:2]); s.dot((g[0] + 4, J['GND#'][1])); s.wire((g[0] + 4, J['GND#'][1]), (g[0] + 8, J['GND#'][1])); s.gnd((g[0] + 8, J['GND#'][1]))
    s.pl(J, '3V3_EXP', '', kind='nc')
    s.text(J['3V3_EXP'][0] + 3, J['3V3_EXP'][1] + 0.7, 'ikke brukt i boksen', 1.5, 'start', NOTE)
    s.label(J['RX'][:2], 'HE_UART_RX', 'r', 3); s.label(J['TX'][:2], 'HE_UART_TX', 'r', 3); s.label(J['EXP_INT'][:2], 'EXP_INT', 'r', 3)
    a, b = J['LOOP_A'][:2], J['LOOP_B'][:2]; s.wire(a, (a[0] + 6, a[1]), (a[0] + 6, b[1]), b)
    s.text(a[0] + 8, a[1] + 3, 'sløyfe: lokk-kjede i hovedenheten', 1.5, 'start', NOTE)
    s.note(262, 220, ['RX/TX sett fra boksen: RX = hovedenhetens EXP_UART_TX.', 'ESD-vern på alle signaler. Kabel i stålflettet strømpe', 'når boksen står utenfor hovedenhetens kapsling.'], w=142)
    return s


def sheet_ub_ports(B):
    s = Sheet(B, 'Sensorbussporter med eFuse og to CAN FD-segmenter')
    # ---------- A port 1 detaljert ----------
    s.block(14, 16, 236, 140, 'A  Port 1 (port 2–4 er like, se tabell)')
    E = s.ic(80, 34, 28, s.b.ref('U'), 'TPS1663', left=['IN', 'P_IN', 'EN/UVLO', 'OVP', 'SHDN'], right=['OUT', None, None, 'IMON', 'FLT', 'PGOOD', 'ILIM', 'dVdT', 'GND'], pitch=5, desc='eFuse 60 V 6 A med strømmåling')
    vx, vy = E['IN'][:2]
    s.wire((vx, vy), (vx - 26, vy)); s.pwr((vx - 26, vy), 'VBOX', 'u')
    s.wire(E['P_IN'][:2], (vx - 4, E['P_IN'][1]), (vx - 4, vy)); s.dot((vx - 4, vy))
    s.dot((vx - 18, vy)); c = s.C((vx - 18, vy), 'v', '1 µF 100 V', L=5, side='l'); s.gnd(c[1])
    s.label(E['EN/UVLO'][:2], 'PORT1_EN', 'l', 3)
    s.text(E['OVP'][0] - 3, E['OVP'][1] + 0.7, 'deler for 38 V*', 1.5, 'end', NOTE); s.wire(E['OVP'][:2], (E['OVP'][0] - 1, E['OVP'][1]))
    s.wire(E['SHDN'][:2], (E['SHDN'][0] - 1, E['SHDN'][1])); s.text(E['SHDN'][0] - 3, E['SHDN'][1] + 0.7, 'til EN-nett', 1.5, 'end', NOTE)
    o = E['OUT'][:2]; po = (o[0] + 40, o[1]); s.wire(o, po); s.dot((o[0] + 10, o[1]))
    c = s.C((o[0] + 10, o[1]), 'v', '10 µF 50 V', L=4); s.gnd(c[1])
    s.label(po, 'P1_V+', 'r', 0)
    im = E['IMON'][:2]; s.wire(im, (im[0] + 22, im[1])); s.dot((im[0] + 22, im[1]))
    s.label((im[0] + 22, im[1]), 'IMON1', 'r', 6)
    s.text(im[0] + 3, im[1] - 1.2, 'R_IMON + 10 nF', 1.4, 'start', NOTE)
    s.label(E['FLT'][:2], 'PORT_FLT', 'r', 3)
    s.pl(E, 'PGOOD', '', kind='nc')
    s.text(E['ILIM'][0] + 3, E['ILIM'][1] + 0.7, 'R for 1,0 A*', 1.5, 'start', NOTE); s.wire(E['ILIM'][:2], (E['ILIM'][0] + 1, E['ILIM'][1]))
    s.text(E['dVdT'][0] + 3, E['dVdT'][1] + 0.7, 'C for myk start*', 1.5, 'start', NOTE); s.wire(E['dVdT'][:2], (E['dVdT'][0] + 1, E['dVdT'][1]))
    s.pl(E, 'GND', '', 3, 'gnd')
    J = m12(s, 196, 56, s.b.ref('J'), side='l')
    E_ref = s.b.bom[[b[1] for b in s.b.bom].index('TPS1663')][0]; J_ref = s.b.bom[-1][0]
    s.label((J['V+'][0] - 26, J['V+'][1]), 'P1_V+', 'l', 0); s.wire((J['V+'][0] - 26, J['V+'][1]), J['V+'][:2])
    g = J['GND'][:2]; s.wire(g, (g[0] - 6, g[1])); s.gnd((g[0] - 6, g[1]))
    s.label(J['CAN_H'][:2], 'SEG1_CANH', 'l', 3); s.label(J['CAN_L'][:2], 'SEG1_CANL', 'l', 3)
    sh = J['SHLD'][:2]; s.wire(sh, (sh[0] - 6, sh[1])); s.text(sh[0] - 7, sh[1] + 0.7, 'kapsling (1 nF ∥ 1 MΩ)', 1.5, 'end', NOTE)
    s.note(22, 120, ['V+ på porten bare når PORTn_EN er høy. eFuse kutter ved kortslutning og', 'melder FLT. IMON måles kontinuerlig: brudd (ingen strøm), kortslutning', 'og unormalt forbruk gir sabotasjealarm. TVS (SMBJ36A) og ESD på hver port.'], w=226)

    # ---------- B tabell ----------
    s.block(256, 16, 154, 140, 'B  Portene')
    pr = [(E_ref, J_ref)] + [(s.b.ref('U'), s.b.ref('J')) for _ in range(3)]
    rows = [('Port', 'Kontakt', 'eFuse', 'Segment', 'Strøm')] + [(str(i + 1), pr[i][1], pr[i][0], 'SEG1' if i < 2 else 'SEG2', f'IMON{i + 1}') for i in range(4)]
    for k, r in enumerate(rows):
        for j, v in enumerate(r):
            s.text(264 + j * 28, 32 + k * 7, v, 1.9, 'start', '#1a1a1a', 'bold' if k == 0 else 'normal')
    for k in range(1, 4):
        s.b.bom.append((pr[k][0], 'TPS1663', f'eFuse 60 V 6 A med strømmåling (port {k + 1})'))
        s.b.bom.append((pr[k][1], 'M12 A-kodet 5-pin', 'M12 A-kodet 5-pin (CiA 303-1)'))
    s.note(264, 78, ['Kameraer på segment 1, øvrige sensorer på', 'segment 2. En kuttet kabel på ett segment', 'tar ikke ut det andre.', 'Kamerahub-varianten har bare port 1–2.'], w=140)

    # ---------- C segmenter ----------
    s.block(14, 162, 396, 94, 'C  CAN FD-segmenter med omkoplbar terminering i boksen')
    for k, (x0, seg) in enumerate([(30, 1), (220, 2)]):
        T = s.ic(x0 + 34, 170, 26, s.b.ref('U'), 'TCAN1462', left=['TXD', 'RXD', 'STB', 'VIO'], right=['VCC', 'CANH', None, None, None, None, 'CANL', 'GND'], pitch=4.5, desc='CAN FD-transceiver')
        s.label(T['TXD'][:2], f'CAN{seg}_TXD', 'l', 3); s.label(T['RXD'][:2], f'CAN{seg}_RXD', 'l', 3)
        s.label(T['STB'][:2], 'CAN_STB', 'l', 3); s.label(T['VIO'][:2], '3V3', 'l', 3)
        s.label(T['VCC'][:2], '5V', 'r', 3); s.pl(T, 'GND', '', 3, 'gnd')
        h, l = T['CANH'][:2], T['CANL'][:2]
        xh = h[0] + 20
        s.wire(h, (xh + 36, h[1])); s.wire(l, (xh + 36, l[1]))
        s.label((xh + 36, h[1]), f'SEG{seg}_CANH', 'r', 0); s.label((xh + 36, l[1]), f'SEG{seg}_CANL', 'r', 0)
        s.dot((xh, h[1])); s.dot((xh, l[1]))
        r1 = s.R((xh, h[1]), 'v', '60,4 Ω', L=8, side='l')
        sw_ = s.SW(r1[1], 'v', '', L=6, desc='Termineringsbryter (analog bryter eller jumper)')
        r2 = s.R((xh, sw_[1][1]), 'v', '60,4 Ω', L=8, side='l')
        s.wire(r2[1], (xh, l[1]))
    s.note(22, 244, ['Split-terminering 2 × 60,4 Ω (midtpunkt via 4,7 nF til jord, ikke vist). Boksen terminerer én ende, siste node eller termineringsplugg den andre.'], w=384)
    return s


def sheet_ub_io(B):
    s = Sheet(B, 'Overvåkede innganger, reléutganger, RS-485 og sabotasje')
    # ---------- A EOL ----------
    s.block(14, 16, 236, 120, 'A  Overvåket inngang 1 (dobbel EOL, ×8)')
    J = s.conn(24, 40, s.b.ref('J'), 'Rekkeklemme 16-pol (8 × 2)', [(1, 'IN1+'), (2, 'IN1−')], pitch=6, desc='Rekkeklemme for 8 EOL-innganger')
    p = J['IN1+'][:2]
    n0 = (p[0] + 10, p[1]); s.wire(p, n0); s.dot(n0)
    t = s.D(n0, 'v', 'SMAJ24CA', L=10, kind='tvsb'); s.wire(t[1], (n0[0], t[1][1])); s.gnd(t[1])
    s.wire(n0, (n0[0] + 8, p[1])); r = s.R((n0[0] + 8, p[1]), 'h', '1 kΩ', L=12); n1 = (r[1][0] + 10, p[1]); s.wire(r[1], n1); s.dot(n1)
    s.pwr((n1[0], p[1] - 14), '3V3_REF', 'u'); rp = s.R((n1[0], p[1] - 14), 'v', '4,7 kΩ 0,1 %', L=10, side='l'); s.wire(rp[1], n1)
    r = s.R(n1, 'h', '10 kΩ', L=12); s.dot(r[1]); c = s.C(r[1], 'v', '10 nF', L=6); s.gnd(c[1])
    d = s.D((r[1][0] + 14, p[1]), 'v', 'BAT54S', L=6, kind='s', flip=True); s.wire(r[1], (r[1][0] + 14, p[1])); s.dot((r[1][0] + 14, p[1])); s.gnd(d[1])
    s.label((r[1][0] + 14, p[1]), 'EOL1', 'r', 10)
    g = J['IN1−'][:2]; s.wire(g, (g[0] + 3, g[1])); s.gnd((g[0] + 3, g[1]))
    Rf = s.ic(176, 28, 22, s.b.ref('U'), 'REF3033', left=['IN', 'GND'], right=['OUT'], pitch=5, desc='Spenningsreferanse 3,3 V 0,2 %')
    s.label(Rf['IN'][:2], '5V', 'l', 3); s.pl(Rf, 'GND', '', 3, 'gnd')
    o = Rf['OUT'][:2]; s.wire(o, (o[0] + 10, o[1])); s.pwr((o[0] + 10, o[1]), '3V3_REF', 'u'); s.dot((o[0] + 5, o[1])); c = s.C((o[0] + 5, o[1]), 'v', '1 µF', L=6); s.gnd(c[1])
    # sensoren ute
    s.rect(140, 64, 100, 34, fill='#f7f7f5', c='#8a8a85', sw=0.25, dash='1.5 1', r=1)
    s.text(144, 69, 'Ute ved sensoren (dobbel EOL, eksempel 2,2 kΩ / 2,2 kΩ)', 1.7, 'start', NOTE)
    y = 82
    s.text(144, y - 6, 'IN+', 1.6, 'start', NET)
    s.wire((146, y), (152, y))
    r = s.R((152, y), 'h', 'R_EOL 2,2 kΩ', L=14, ref='(sensor)', desc='EOL i sensor'); s.b.bom.pop()
    s.wire(r[1], (176, y)); s.dot((176, y))
    sw_ = s.SW((176, y), 'h', 'Alarm (NC)', L=14, ref='(sensor)', nc=True); s.b.bom.pop()
    r2 = s.R((176, y + 8), 'h', 'R_ALM 2,2 kΩ', L=14, ref='(sensor)'); s.b.bom.pop()
    s.wire((176, y), (176, y + 8)); s.wire(sw_[1], (196, y)); s.wire(r2[1], (196, y + 8)); s.wire((196, y), (196, y + 8)); s.dot((196, y))
    s.wire((196, y), (204, y)); sw2 = s.SW((204, y), 'h', 'Sabotasje (NC)', L=14, ref='(sensor)', nc=True); s.b.bom.pop()
    s.wire(sw2[1], (226, y)); s.text(228, y + 0.7, 'IN−', 1.6, 'start', NET)
    s.note(22, 108, ['Måling mot presisjonsreferanse 3V3_REF (REF3033). Fem tilstander fra motstanden:', 'kortsluttet (< 1 kΩ), normal (2,2 kΩ), alarm (4,4 kΩ), sabotasje/brudd (∞), og', 'feil verdi. Tersklene kan settes i appen for å passe EOL-verdier fra ulike leverandører.'], w=226)

    # ---------- B relé ----------
    s.block(256, 16, 154, 120, 'B  Reléutgang 1 (×2, maks 2 A)')
    q = s.fet((288, 76), 'n', val='30 V', desc='N-MOSFET 30 V, relédriver')
    s.label((270, 76), 'REL1', 'l', 0); r = s.R((270, 76), 'h', '1 kΩ', L=12); s.wire(r[1], q['g'])
    s.dot((284, 76)); r = s.R((284, 76), 'v', '100 kΩ', L=8, side='l'); s.gnd(r[1])
    s.gnd(q['s'])
    top = (q['d'][0], 44); s.pwr(top, '5V', 'u')
    coil = s.Lind(top, 'v', 'Relé 5 V, 1 × CO', L=14, ref='K1', side='l', desc='Signalrelé 5 V spole, kontakt 2 A / 30 V DC'); s.wire(coil[1], q['d'])
    fd = s.D((top[0] + 10, 44), 'v', '1N4148W', L=14, flip=True); s.wire(top, (top[0] + 10, 44)); s.wire(fd[1], (top[0] + 10, q['d'][1])); s.wire((top[0] + 10, q['d'][1]), q['d'])
    J = s.conn(366, 40, s.b.ref('J'), 'Rekkeklemme 6-pol (2 × C/NO/NC)', [(1, 'C'), (2, 'NO'), (3, 'NC')], side='l', pitch=6, desc='Rekkeklemme reléutganger')
    for nm in ['C', 'NO', 'NC']: s.label(J[nm][:2], f'K1_{nm}', 'l', 3)
    s.text(q['d'][0] + 14, 62, 'Kontaktsett K1: K1_C, K1_NO, K1_NC', 1.5, 'start', NOTE)
    s.b.bom.append(('K2', 'Relé 5 V, 1 × CO', 'Signalrelé 5 V spole, kontakt 2 A / 30 V DC (utgang 2)'))
    s.note(264, 108, ['Sirene og strobe 12/24 V via kontakten. Varistor', 'eller RC over kontaktene ved induktiv last.', 'Reléet slipper ved strømbrudd i boksen (feilsikkert).'], w=140)

    # ---------- C RS-485 ----------
    s.block(14, 142, 236, 114, 'C  RS-485 (Modbus RTU)')
    R = s.ic(72, 158, 26, s.b.ref('U'), 'THVD1450', left=['R', 'RE', 'DE', 'D'], right=['VCC', 'A', 'B', 'GND'], pitch=5, desc='RS-485-transceiver 3,3 V')
    s.label(R['R'][:2], 'RS485_RX', 'l', 3); s.label(R['D'][:2], 'RS485_TX', 'l', 3)
    s.wire(R['RE'][:2], (R['RE'][0] - 2, R['RE'][1]), (R['RE'][0] - 2, R['DE'][1]), R['DE'][:2]); s.dot((R['RE'][0] - 2, R['DE'][1]))
    s.label((R['RE'][0] - 2, R['DE'][1]), 'RS485_DE', 'l', 3)
    s.label(R['VCC'][:2], '3V3', 'r', 3); s.pl(R, 'GND', '', 3, 'gnd')
    a, b = R['A'][:2], R['B'][:2]
    J = s.conn(200, R['A'][1] - 5, s.b.ref('J'), 'Rekkeklemme 3-pol', [(1, 'A'), (2, 'B'), (3, 'GND')], side='l', pitch=5, desc='RS-485')
    s.wire(a, (J['A'][0], a[1]) if abs(J['A'][1] - a[1]) < 0.01 else (a[0] + 4, a[1]))
    s.wire((a[0] + 4, a[1]), (a[0] + 4, J['A'][1]), J['A'][:2]) if abs(J['A'][1] - a[1]) > 0.01 else None
    s.wire(b, (b[0] + 8, b[1]), (b[0] + 8, J['B'][1]), J['B'][:2])
    g = J['GND'][:2]; s.wire(g, (g[0] - 3, g[1])); s.gnd((g[0] - 3, g[1]))
    s.note(22, 222, ['Velgbar 120 Ω terminering og fail-safe forspenning (680 Ω) med bryter.', 'TVS (SM712) på A og B. Galvanisk skille vurderes for lange kabler.'], w=226)

    # ---------- D sabotasje ----------
    s.block(256, 142, 154, 114, 'D  Sabotasje og lys i lokket')
    s.pwr((276, 160), '3V3', 'u'); r = s.R((276, 160), 'v', '1 MΩ', L=10, side='l'); n = (276, 174); s.wire(r[1], n); s.dot(n)
    sw_ = s.SW(n, 'h', 'Lokk (NC)', L=12, desc='Lokkbryter'); s.wire(sw_[1], (sw_[1][0] + 2, 174)); s.gnd((sw_[1][0] + 2, 174))
    s.wire(n, (n[0], 182)); s.label((n[0], 182), 'LID_SW', 'd', 0)
    O = s.ic(336, 160, 24, s.b.ref('U'), 'OPT3001', left=['VDD', 'ADDR'], right=['SDA', 'SCL', 'INT', 'GND'], pitch=5, desc='Lyssensor i lokket')
    s.label(O['VDD'][:2], '3V3', 'l', 3); s.pl(O, 'ADDR', '', 3, 'gnd')
    s.label(O['SDA'][:2], 'I2C_SDA', 'r', 3); s.label(O['SCL'][:2], 'I2C_SCL', 'r', 3); s.pl(O, 'INT', '', kind='nc')
    s.pl(O, 'GND', '', 3, 'gnd')
    s.label((276, 200), 'LED_STATUS', 'l', 0); r = s.R((276, 200), 'h', '1 kΩ', L=10); d = s.D(r[1], 'h', 'Status', L=10, kind='led'); s.wire(d[1], (d[1][0] + 2, 200)); s.gnd((d[1][0] + 2, 200))
    s.note(264, 214, ['Lys inne i en lukket boks betyr at den er åpnet', 'eller boret i. LID_SW vekker prosessoren.', 'ATECC608B for nøkler på I2C (som sensornoden).'], w=140)
    return s
