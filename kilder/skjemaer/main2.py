from lib import Sheet, NOTE, NET

def divider(s, x, y, top_net, r1, r2, out_net, note=None, cval='100 nF'):
    """Spenningsdeler med filter. Øverst forsyningsflagg."""
    s.pwr((x, y), top_net, 'u')
    r = s.R((x, y), 'v', r1, L=10, side='l'); nd = (x, y + 14); s.wire(r[1], nd); s.dot(nd)
    r = s.R(nd, 'v', r2, L=10, side='l'); s.gnd(r[1])
    r = s.R(nd, 'h', '10 kΩ', L=12); s.dot(r[1])
    c = s.C(r[1], 'v', cval, L=8); s.gnd(c[1])
    s.label(r[1], out_net, 'r', 4)
    if note: s.text(x + 4, y + 32, note, 1.6, 'start', NOTE)

def sheet_charger(B):
    s = Sheet(B, 'Lader, reservebatteri og regulatorer')
    # ---------- A lader ----------
    s.block(14, 16, 186, 124, 'A  Lader med power path og reservebatteri')
    U = s.ic(84, 34, 30, 'U4', 'BQ25180', left=['IN', 'MR', 'TS'], right=['SYS', None, 'INT', 'SDA', 'SCL', 'BAT', 'GND'], pitch=5, desc='Lineær lader 1S med power path, I2C')
    s.pwr((60, U['IN'][1]), '5V_BUCK', 'u'); s.wire((60, U['IN'][1]), U['IN'][:2]); s.dot((66, U['IN'][1]))
    c = s.C((66, U['IN'][1]), 'v', '1 µF 25 V', L=8, side='l'); s.gnd(c[1])
    s.pl(U, 'MR', '', kind='nc')
    s.text(U['MR'][0] - 3, U['MR'][1] - 1.4, 'testpunkt', 1.5, 'end', NOTE)
    for nm, net in [('INT', 'SYS_INT'), ('SDA', 'I2C_SDA'), ('SCL', 'I2C_SCL')]:
        s.label(U[nm][:2], net, 'r', 3)
    s.pl(U, 'GND', '', 3, 'gnd')
    # SYS
    sy = U['SYS'][1]; sx = U['SYS'][0]
    s.wire((sx, sy), (sx + 56, sy)); s.pwr((sx + 56, sy), 'VSYS', 'u')
    for i, (val, d) in enumerate([('2 × 100 µF polymer', 'Polymer, lav ESR, 2 stk'), ('22 µF', 'X5R')]):
        px = sx + 20 + i * 24; s.dot((px, sy)); c = s.C((px, sy), 'v', val, L=5, pol=(i == 0), desc=d); s.gnd(c[1])
    # BAT -> J2
    J2 = s.conn(28, 92, 'J2', 'JST-PH 3-pin', [(1, 'BAT+'), (2, 'NTC'), (3, 'BAT−')], pitch=5, desc='Batterikontakt')
    bx, by = U['BAT'][:2]
    s.wire((bx, by), (bx + 8, by), (bx + 8, 86), (J2['BAT+'][0] + 6, 86), (J2['BAT+'][0] + 6, J2['BAT+'][1]), J2['BAT+'][:2])
    s.dot((J2['BAT+'][0] + 6, J2['BAT+'][1]))
    c = s.C((J2['BAT+'][0] + 6, J2['BAT+'][1]), 'h', '10 µF', L=10)
    s.wire(c[1], (c[1][0] + 2, c[1][1])); s.gnd((c[1][0] + 2, c[1][1]))
    s.wname(((bx + 8 + J2['BAT+'][0] + 6) / 2, 86), 'VBAT', '#b3261e')
    s.wire(U['TS'][:2], (U['TS'][0] - 8, U['TS'][1]), (U['TS'][0] - 8, J2['NTC'][1]), J2['NTC'][:2])
    s.wire(J2['BAT−'][:2], (J2['BAT−'][0] + 3, J2['BAT−'][1])); s.gnd((J2['BAT−'][0] + 3, J2['BAT−'][1]))
    s.note(22, 126, ['18650 Li-ion for lav temperatur, med beskyttelseskrets (PCM).', 'NTC 10 kΩ (103AT) på cella stopper lading under 0 °C.', 'Ladestrøm og spenning settes over I2C ved oppstart.'], w=110)
    # varme
    q = s.fet((150, 112), 'n', val='30 V, logikknivå', desc='N-MOSFET 30 V')
    r = s.R((128, 112), 'h', '100 Ω', L=10); s.label((128, 112), 'BAT_HEAT', 'l', 0); s.wire(r[1], q['g'])
    s.dot((141, 112)); r = s.R((141, 112), 'v', '100 kΩ', L=8); s.gnd(r[1])
    s.gnd(q['s'])
    J3 = s.conn(176, 92, 'J3', 'JST-PH 2-pin', [(1, 'HEAT+'), (2, 'HEAT−')], side='l', pitch=5, desc='Batterivarme, varmefolie ca. 25 Ω')
    s.wire(q['d'], (q['d'][0], J3['HEAT−'][1]), J3['HEAT−'][:2])
    s.pwr((J3['HEAT+'][0] - 6, J3['HEAT+'][1]), '5V_BUCK', 'u'); s.wire((J3['HEAT+'][0] - 6, J3['HEAT+'][1]), J3['HEAT+'][:2])
    s.text(140, 130, 'Varme bare når maskinstrøm finnes (5V_BUCK).', 1.6, 'start', NOTE)

    # ---------- B regulatorer ----------
    s.block(206, 16, 204, 124, 'B  Regulatorer 3,3 V (alltid på) og 1,8 V (radar)')
    for k, (x0, ref, out, en, vset) in enumerate([(244, 'U5', '3V3_AON', None, 'VSET for 3,3 V*'), (352, 'U6', '1V8_RADAR', 'RADAR_PWR', 'VSET for 1,8 V*')]):
        U = s.ic(x0, 40, 22, ref, 'TPS62840', left=['VIN', None, 'EN', 'VSET', 'MODE'], right=['VOS', 'SW', 'STOP', 'GND'], pitch=5, desc='Buck 60 nA hvilestrøm')
        vx, vy = U['VIN'][:2]
        s.pwr((vx - 24, vy), 'VSYS', 'u'); s.wire((vx - 24, vy), (vx, vy)); s.dot((vx - 20, vy))
        c = s.C((vx - 20, vy), 'v', '4,7 µF', L=7, side='l'); s.gnd(c[1])
        if en: s.label(U['EN'][:2], en, 'l', 3)
        else:
            s.wire(U['EN'][:2], (vx - 3, U['EN'][1]), (vx - 3, vy)); s.dot((vx - 3, vy))
        s.pl(U, 'MODE', '', 3, 'gnd')
        vs = U['VSET'][:2]; s.wire(vs, (vs[0] - 9, vs[1])); r = s.R((vs[0] - 9, vs[1]), 'v', vset, L=8, side='l'); s.gnd(r[1])
        swx, swy = U['SW'][:2]
        l = s.Lind((swx, swy), 'h', '2,2 µH', L=10)
        o = (l[1][0] + 10, swy); s.wire(l[1], o); s.dot((l[1][0] + 4, swy))
        c = s.C((l[1][0] + 4, swy), 'v', '10 µF', L=8); s.gnd(c[1])
        s.wire(U['VOS'][:2], (o[0], U['VOS'][1]), o); s.pwr((o[0], U['VOS'][1]), out, 'u')
        s.gndjoin(U, ['STOP', 'GND'])
    s.note(214, 100, ['U5 er alltid på og forsyner det som må våke: IMU, ATECC608B, OPT3001, I/O-utvider,', 'LoRa og VDD_GPIO på nRF9151. U6 slås av med RADAR_PWR (I/O-utvider) mellom', 'radarmålinger. A121 kan i tillegg holdes i ENABLE lav (under 1 µA).', 'VSET-motstand velges fra tabellen i databladet.'], w=188, title='Merknader')

    # ---------- C lastbrytere ----------
    s.block(14, 148, 186, 108, 'C  Lastbrytere')
    for k, (x0, y0, ref, on, out, use) in enumerate([(70, 166, 'U7', 'PWR_EN_SENS', '3V3_SW', 'GNSS, mikrofon, flash, antenneovervåking'), (70, 212, 'U8', 'EXP_EN', '3V3_EXP', 'Ekspansjonskontakt (kamerahub/utvidelsesboks)')]):
        U = s.ic(x0, y0, 22, ref, 'TPS22916', left=['VIN', 'ON'], right=['VOUT', 'GND'], pitch=5, desc='Lastbryter 1 A')
        s.pl(U, 'VIN', '3V3_AON', 6, 'pwr'); s.label(U['ON'][:2], on, 'l', 3)
        vo = U['VOUT'][:2]; o = (vo[0] + 22, vo[1]); s.wire(vo, o); s.dot((vo[0] + 8, vo[1]))
        c = s.C((vo[0] + 8, vo[1]), 'v', '1 µF', L=8); s.gnd(c[1])
        s.pwr(o, out, 'r')
        s.pl(U, 'GND', '', 3, 'gnd')
        s.text(x0 - 40, y0 + 22, use, 1.6, 'start', NOTE)

    # ---------- D måling ----------
    s.block(206, 148, 204, 108, 'D  Måling av batteri og systemspenning')
    divider(s, 226, 168, 'VBAT', '1 MΩ', '1 MΩ', 'VBAT_SENSE', '→ AIN1 (P0.14). 4,2 V gir 2,1 V.')
    divider(s, 316, 168, 'VSYS', '1 MΩ', '1 MΩ', 'VSYS_SENSE', '→ AIN7 (P0.20). Overvåker buffer.')
    s.note(214, 214, ['Delere på 1 MΩ gir ca. 2 µA hver. Kan byttes til', 'måling via lastbryter hvis strømbudsjettet krever det.'], w=110)
    return s


NRF_GPIO = [
    ('P0.00', 'SPI_SCK', 'A121, LoRa, flash'), ('P0.01', 'SPI_MOSI', 'A121, LoRa, flash'), ('P0.02', 'SPI_MISO', 'A121, LoRa, flash'),
    ('P0.03', 'CS_RADAR', 'A121 SPI_SS'), ('P0.04', 'CS_LORA', 'SX1262 NSS'), ('P0.05', 'CS_FLASH', 'MX25R6435F CS#'),
    ('P0.06', 'RADAR_INT', 'A121 INTERRUPT'), ('P0.07', 'RADAR_EN', 'A121 ENABLE'), ('P0.08', 'LORA_BUSY', 'SX1262 BUSY'),
    ('P0.09', 'LORA_DIO1', 'SX1262 DIO1'), ('P0.10', 'EXP_INT', 'Ekspansjon, vekking'), ('P0.11', 'I2C_SDA', 'I2C-buss'),
    ('P0.12', 'I2C_SCL', 'I2C-buss'), ('P0.13/AIN0', 'VIN_SENSE', 'Maskinspenning (ark 1)'), ('P0.14/AIN1', 'VBAT_SENSE', 'Batteri (ark 2)'),
    ('P0.15/AIN2', 'MESH_SENSE', 'Tamperfolie (ark 7)'), ('P0.16/AIN3', 'ANT_LTE_SENSE', 'LTE-antennesløyfe'), ('P0.17/AIN4', 'ANT_LORA_SENSE', 'LoRa-antennesløyfe (ark 5)'),
    ('P0.18/AIN5', 'GPS_LOOP_SENSE', 'GPS-kabelsløyfe (ark 7)'), ('P0.19/AIN6', 'IGN_SENSE', 'Tenning (ark 1)'), ('P0.20/AIN7', 'VSYS_SENSE', 'Systemspenning (ark 2)'),
    ('P0.21', 'IMU_INT1', 'LSM6DSV16X INT1'), ('P0.22', 'SYS_INT', 'Felles avbrudd, open drain'), ('P0.23', 'PDM_CLK', 'IM69D130 CLK'),
    ('P0.24', 'PDM_DIN', 'IM69D130 DATA'), ('P0.25', 'COP_UART_TX', 'Til nRF54L15 (ark 4)'), ('P0.26', 'LID_SW', 'Lokk- og veggbryter (ark 7)'),
    ('P0.27', 'PFAIL_N', 'Strømbrudd (ark 1)'), ('P0.28', 'SIREN_EN', 'Sirene (ark 1)'), ('P0.29', 'COP_UART_RX', 'Fra nRF54L15, vekking'),
    ('P0.30', 'EXP_UART_TX', 'Ekspansjon (ark 7)'), ('P0.31', 'EXP_UART_RX', 'Ekspansjon (ark 7)')]

def sheet_nrf9151(B):
    s = Sheet(B, 'nRF9151 SiP, SIM, LTE-antenne og programmering')
    left = ['VDD', None, None, 'VDD_GPIO', 'ENABLE', 'nRESET', 'SWDIO', 'SWDCLK', None, 'SIM_1V8', 'SIM_CLK', 'SIM_RST', 'SIM_IO', 'SIM_DET', None,
            'ANT', 'AUX', 'GPS', None, 'COEX0', 'COEX1', 'COEX2', 'MAGPIO0', 'MAGPIO1', 'MAGPIO2', 'VIO', 'DEC0', None, 'GND', 'GND#2', 'GND#3']
    right = [p for p, _, _ in NRF_GPIO]
    U = s.ic(178, 22, 46, 'U9', 'nRF9151 SiP (LGA)', left=left, right=right, pitch=4, desc='Nordic nRF9151, LTE-M/NB-IoT/NTN')
    for p, net, use in NRF_GPIO:
        x, y, _ = U[p]
        s.label((x, y), net, 'r', 3)
        s.text(x + 30, y + 0.7, use, 1.7, 'start', NOTE)
    # forsyning
    vx, vy = U['VDD'][:2]
    s.wire((vx, vy), (vx - 30, vy)); s.pwr((vx - 30, vy), 'VSYS', 'l')
    for i, v in enumerate(['10 µF*', '100 nF']):
        px = vx - 10 - i * 9; s.dot((px, vy)); c = s.C((px, vy), 'v', '', L=6); s.gnd(c[1])
    s.text(vx - 15, vy - 2, '10 µF* + 100 nF', 1.5, 'middle', NOTE)
    gx, gy = U['VDD_GPIO'][:2]
    s.wire((gx, gy), (gx - 6, gy)); s.wire((gx - 6, gy), (gx - 6, gy)); s.pwr((gx - 6, gy), '3V3_AON', 'l')
    ex, ey = U['ENABLE'][:2]
    s.wire((ex, ey), (ex - 18, ey)); s.pwr((ex - 18, ey), '3V3_AON', 'l')
    s.text(ex - 3, ey - 1.2, 'høy = på', 1.4, 'end', NOTE)
    s.label(U['nRESET'][:2], 'NRF91_RESET', 'l', 3)
    s.label(U['SWDIO'][:2], 'NRF91_SWDIO', 'l', 3)
    s.label(U['SWDCLK'][:2], 'NRF91_SWDCLK', 'l', 3)
    for nm in ['SIM_CLK', 'SIM_RST', 'SIM_IO']: s.label(U[nm][:2], nm, 'l', 3)
    s.label(U['SIM_1V8'][:2], 'SIM_1V8', 'l', 3)
    for nm in ['SIM_DET', 'AUX', 'GPS', 'COEX0', 'COEX1', 'COEX2', 'MAGPIO0', 'MAGPIO1', 'MAGPIO2', 'VIO', 'DEC0']: s.pl(U, nm, '', kind='nc')
    s.text(U['GPS'][0] - 3, U['GPS'][1] + 0.6, 'ikke brukt (MAX-M10S)', 1.5, 'end', NOTE)
    s.text(U['COEX1'][0] - 3, U['COEX1'][1] + 0.6, 'ikke brukt', 1.5, 'end', NOTE)
    s.text(U['DEC0'][0] - 3, U['DEC0'][1] + 0.6, 'etter Nordic referanse', 1.5, 'end', NOTE)
    s.label(U['ANT'][:2], 'LTE_RF', 'l', 3)
    for g in ['GND', 'GND#2', 'GND#3']:
        x, y, _ = U[g]; s.wire((x, y), (x - 4, y))
    x, y, _ = U['GND#3']; s.wire((U['GND'][0] - 4, U['GND'][1]), (x - 4, y)); s.gnd((x - 4, y))
    s.text(U['GND'][0] - 6, U['GND'][1] + 0.6, 'alle GND-pinner og pute', 1.5, 'end', NOTE)

    # SIM
    s.block(14, 16, 116, 62, 'A  Loddet SIM (MFF2 / eSIM)')
    S = s.ic(54, 28, 22, 'U10', 'MFF2 SIM', left=['VCC', 'CLK', 'RST', 'IO'], right=['GND'], pitch=5, desc='Loddet SIM/eSIM MFF2, industri')
    s.label(S['VCC'][:2], 'SIM_1V8', 'l', 3)
    for nm, net in [('CLK', 'SIM_CLK'), ('RST', 'SIM_RST'), ('IO', 'SIM_IO')]: s.label(S[nm][:2], net, 'l', 3)
    s.pl(S, 'GND', '', 3, 'gnd')
    c = s.C((96, 40), 'v', '100 nF', L=8); s.gnd(c[1]); s.label((96, 40), 'SIM_1V8', 'u', 0)
    s.note(22, 70, ['Industri-SIM (−40 til +105 °C), loddet for å tåle vibrasjon og hindre bytte.'], w=104)

    # SWD
    s.block(14, 84, 116, 52, 'B  Programmering (Tag-Connect TC2030)')
    J = s.conn(30, 94, 'J9', 'TC2030-IDC-NL', [(1, 'VREF'), (2, 'SWDIO'), (3, 'RESET'), (4, 'SWDCLK'), (5, 'GND'), (6, 'NC')], pitch=4.5, desc='Testpunkt for SWD, ingen komponent')
    s.pwr(J['VREF'][:2], '3V3_AON', 'r')
    for nm, net in [('SWDIO', 'NRF91_SWDIO'), ('RESET', 'NRF91_RESET'), ('SWDCLK', 'NRF91_SWDCLK')]: s.label(J[nm][:2], net, 'r', 3)
    s.pl(J, 'GND', '', 3, 'gnd'); s.pl(J, 'NC', '', kind='nc')
    s.note(80, 98, ['Ingen ekstern pull-up på nRESET', '(ikke tillatt av Nordic).', 'SWD låses i produksjon', '(APPROTECT).'], w=46)

    # LTE RF
    s.block(14, 166, 226, 92, 'C  LTE/NTN-antenne: tilpasning, intern/ekstern og kabelovervåking')
    y0 = 196
    s.label((36, y0), 'LTE_RF', 'l', 0)
    s.wire((36, y0), (44, y0))
    c1 = s.C((44, y0), 'v', 'DNP', L=8, side='l'); s.gnd(c1[1]); s.dot((44, y0))
    l1 = s.Lind((44, y0), 'h', '0 Ω*', L=12, desc='Tilpasning, settes ved måling')
    c2 = s.C(l1[1], 'v', 'DNP', L=8); s.gnd(c2[1]); s.dot(l1[1])
    SW = s.ic(92, y0 - 8, 22, 'U11', 'SPDT RF-bryter', left=[None, 'RFC', 'CTRL', 'VDD'], right=['RF1', 'RF2', 'GND'], pitch=4, desc='SPDT RF-bryter 0,7–2,7 GHz, f.eks. pSemi PE4259')
    s.wire(l1[1], SW['RFC'][:2])
    s.label(SW['CTRL'][:2], 'ANT_SEL', 'l', 3); s.label(SW['VDD'][:2], '3V3_AON', 'l', 3)
    s.pl(SW, 'GND', '', 3, 'gnd')
    r1 = SW['RF1'][:2]; s.wire(r1, (r1[0] + 10, r1[1])); s.ant((r1[0] + 10, r1[1]), 'AE1 chipantenne (intern reserve)')
    r2 = SW['RF2'][:2]
    c = s.C((r2[0], r2[1]), 'h', '100 pF', L=10, desc='DC-sperre')
    jn = (c[1][0] + 16, r2[1]); s.wire(c[1], jn); s.dot(jn)
    s.wire(jn, (jn[0] + 30, r2[1]))
    J6 = (jn[0] + 30, r2[1])
    s.ant(J6, 'J6 SMA (IP67), ekstern antenne')
    s.text(J6[0] + 3, J6[1] + 3, 'Antennefot: 10 kΩ til jord', 1.6, 'start', NOTE)
    l = s.Lind(jn, 'v', '390 nH (RF-drossel)', L=12)
    nd = (jn[0], l[1][1] + 2); s.wire(l[1], nd); s.dot(nd)
    r = s.R(nd, 'v', '100 kΩ', L=10, side='l'); s.pwr(r[1], '3V3_SW', 'd')
    r = s.R(nd, 'h', '10 kΩ', L=12); s.dot(r[1]); c = s.C(r[1], 'v', '100 nF', L=8); s.gnd(c[1])
    s.label(r[1], 'ANT_LTE_SENSE', 'r', 4)
    s.b.bom += [('AE1', 'Chipantenne LTE 698–2200 MHz', 'Intern reserveantenne LTE/NTN'), ('J6', 'SMA hunn IP67, skott', 'Ekstern LTE/NTN-antenne')]
    s.note(22, 236, ['Normal: ca. 0,3 V. Kuttet kabel: 3,3 V. Kortsluttet: 0 V.', 'Pi-nett (C/L/C) avstemmes med nettverksanalysator.', '50 Ω coplanar med jordvias, jordfri sone under AE1.'], w=110)
    return s
