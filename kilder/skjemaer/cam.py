from lib import Sheet, NOTE, NET
from common import buck, can_fd, atecc, swd

def sheet_cam1(B):
    s = Sheet(B, 'Strøm, IR-belysning og sensorbuss')
    # ---------- A kabel og vern ----------
    s.block(14, 16, 104, 84, 'A  Innstøpt kabel og vern')
    J = s.conn(22, 32, s.b.ref('J'), 'Kabelpute (innstøpt kabel)', [(1, 'V+'), (2, 'GND'), (3, 'CAN_H'), (4, 'CAN_L'), (5, 'SHLD')], pitch=5, desc='Loddepute for innstøpt kabel, 2 × 2 ledere + skjerm')
    v = J['V+'][:2]
    d = s.D(v, 'h', 'SS1H10', L=12, kind='s', desc='Schottky 100 V 1 A, feilpolaritet')
    n = (d[1][0] + 8, v[1]); s.wire(d[1], n); s.dot(n)
    t = s.D(n, 'v', 'SMBJ36A', L=10, kind='tvs', flip=True); s.gnd(t[1])
    s.wire(n, (n[0] + 14, v[1])); s.pwr((n[0] + 14, v[1]), 'VBUS', 'u')
    g = J['GND'][:2]; s.wire(g, (g[0] + 4, g[1])); s.gnd((g[0] + 4, g[1]))
    s.label(J['CAN_H'][:2], 'BUS_CANH', 'r', 3); s.label(J['CAN_L'][:2], 'BUS_CANL', 'r', 3)
    sh = J['SHLD'][:2]; s.wire(sh, (sh[0] + 4, sh[1])); s.text(sh[0] + 6, sh[1] + 0.7, 'til kapslingen via 1 nF ∥ 1 MΩ', 1.5, 'start', NOTE)
    s.note(22, 82, ['Kabelen er støpt inn i poden (ingen kontakt).', 'Strøm og strømgrense kommer fra eFuse i hubben.', 'Ingen terminering i poden (linje med T-stykker).'], w=90)

    # ---------- B buck ----------
    buck(s, 124, 16, vin='VBUS', out='3V3', rtop='100 kΩ 1 %', rbot='57,6 kΩ 1 %', ind='33 µH*', title='B  Buck 9–36 V → 3,3 V', w=176, h=84, note='VOUT = 1,2 V × (1 + 100k / 57,6k) ≈ 3,28 V. Maks ca. 400 mA i analyse.')

    # ---------- C LDO ----------
    s.block(306, 16, 104, 84, 'C  1,8 V for bildebrikke og I/O')
    U = s.ic(338, 34, 24, s.b.ref('U'), 'TLV75518P', left=['IN', 'EN'], right=['OUT', 'GND'], pitch=5, desc='LDO 1,8 V 500 mA')
    vx, vy = U['IN'][:2]; s.wire((vx, vy), (vx - 18, vy)); s.pwr((vx - 18, vy), '3V3', 'u'); s.dot((vx - 10, vy))
    c = s.C((vx - 10, vy), 'v', '1 µF', L=5, side='l'); s.gnd(c[1])
    s.wire(U['EN'][:2], (vx - 4, U['EN'][1]), (vx - 4, vy)); s.dot((vx - 4, vy))
    o = U['OUT'][:2]; s.wire(o, (o[0] + 18, o[1])); s.pwr((o[0] + 18, o[1]), '1V8', 'u'); s.dot((o[0] + 8, o[1]))
    c = s.C((o[0] + 8, o[1]), 'v', '1 µF', L=5); s.gnd(c[1])
    s.pl(U, 'GND', '', 3, 'gnd')
    s.note(314, 76, ['Kjernespenning til WiseEye2 lages etter', 'Himax referansedesign (intern PMU eller', 'egen regulator), se ark 2.'], w=90)

    # ---------- D IR-belysning ----------
    s.block(14, 106, 196, 92, 'D  IR-belysning 940 nm (konstantstrøm, pulset)')
    L = s.ic(64, 122, 26, s.b.ref('U'), 'AL8860', left=['VIN', 'CTRL', 'GND'], right=['SET', 'SW'], pitch=6, desc='Buck LED-driver 40 V 1,5 A')
    vx, vy = L['VIN'][:2]; s.wire((vx, vy), (vx - 30, vy)); s.pwr((vx - 30, vy), 'VBUS', 'u'); s.dot((vx - 22, vy))
    c = s.C((vx - 22, vy), 'v', '4,7 µF 50 V', L=5, side='l'); s.gnd(c[1])
    s.label(L['CTRL'][:2], 'IR_PWM', 'l', 3); s.pl(L, 'GND', '', 3, 'gnd')
    # strømvei: VIN -> Rs -> LED -> L -> SW
    st = L['SET'][:2]; sw = L['SW'][:2]
    top = (st[0] + 8, vy - 10)
    s.wire((vx - 22, vy), (vx - 22, top[1]), (st[0] + 24, top[1]))
    s.dot((st[0] + 24, top[1]))
    r = s.R((st[0] + 24, top[1]), 'v', '0,2 Ω', L=8, desc='Strømmåling LED, 0,5 A')
    s.wire(r[1], (st[0] + 24, st[1])); s.wire(st, (st[0] + 24, st[1])); s.dot((st[0] + 24, st[1]))
    d1 = s.D((st[0] + 24, st[1]), 'v', '940 nm 1 W', L=8, kind='led', desc='IR-LED 940 nm, f.eks. OSRAM Oslon')
    d2 = s.D(d1[1], 'v', '940 nm 1 W', L=8, kind='led', desc='IR-LED 940 nm, f.eks. OSRAM Oslon')
    l = s.Lind(d2[1], 'v', '47 µH', L=10)
    s.wire(l[1], (st[0] + 24, l[1][1] + 4), (sw[0] + 4, l[1][1] + 4), (sw[0] + 4, sw[1]), sw)
    s.wire((st[0] + 24, top[1]), (st[0] + 40, top[1]))
    s.wire((st[0] + 40, top[1]), (st[0] + 40, l[1][1] - 6))
    fd = s.D((st[0] + 40, l[1][1] - 6), 'v', 'SS36', L=10, kind='s', flip=True, desc='Schottky 60 V 3 A, frihjul')
    s.wire(fd[1], (st[0] + 40, l[1][1] + 4), (st[0] + 24, l[1][1] + 4)); s.dot((st[0] + 24, l[1][1] + 4))
    s.note(146, 128, ['Maks ca. 0,5 A', '(0,1 V / 0,2 Ω).', 'IR_PWM fra WiseEye2,', 'synkront med', 'eksponering (FSTROBE).', 'Egen strømvei fra', 'VBUS, så toppene ikke', 'forstyrrer bildebrikken.'], w=58)

    # ---------- E sensorbuss ----------
    can_fd(s, 216, 106, title='E  Sensorbuss CAN FD', vcc='3V3', w=194, spi=('CAN_SCK', 'CAN_MOSI', 'CAN_MISO', 'CAN_CS', 'CAN_INT'), stb='CAN_STB', xcvr='TCAN3413')
    s.note(222, 180, ['Krystall 40 MHz med 2 × 12 pF* (etter krystallens lastkapasitans).', 'TCAN3413: CAN FD-transceiver for 3,3 V (kontrolleres mot datablad).', 'Heartbeat til hubben hvert sekund, signert. STB lav i drift.'], w=184)

    # ---------- F varme ----------
    s.block(14, 204, 196, 52, 'F  Vindusvarme mot dugg og is')
    q = s.fet((60, 236), 'n', val='30 V, logikknivå', desc='N-MOSFET 30 V')
    s.label((40, 236), 'HEAT_EN', 'l', 0); r = s.R((40, 236), 'h', '100 Ω', L=12); s.wire(r[1], q['g'])
    s.dot((56, 236)); r = s.R((56, 236), 'v', '100 kΩ', L=8, side='l'); s.gnd(r[1])
    s.gnd(q['s'])
    h = s.R((q['d'][0], q['d'][1] - 12), 'v', '22 Ω 1 W', L=12, desc='Varmemotstand ved vinduet, 0,5 W'); s.wire(h[1], q['d']); s.pwr(h[0], '3V3', 'u')
    s.note(100, 222, ['Varmen slås på når SHT40 (ark 2) viser fare for', 'dugg eller is. Ca. 0,5 W. Sabotasje gir', 'fortsatt alarm mens varmen står på.'], w=104)
    return s


def sheet_cam2(B):
    s = Sheet(B, 'WiseEye2, bildebrikke, anti-masking og sensorer')
    # ---------- A WE2 ----------
    s.block(14, 16, 236, 182, 'A  AI-prosessor Himax WiseEye2 (HX6538)')
    left = ['VDD_3V3', 'VDD_1V8', 'VCORE', None, 'CSI_CLKP', 'CSI_CLKN', 'CSI_D0P', 'CSI_D0N', None, 'SEN_MCLK', 'SEN_XSHUT', 'SEN_INT', 'SEN_STROBE', None, 'I2CM_SDA', 'I2CM_SCL', None, 'GND', 'GND#2']
    right = ['QSPI_CS', 'QSPI_CLK', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2', 'QSPI_IO3', None, 'SPI_SCK', 'SPI_MOSI', 'SPI_MISO', 'SPI_CS', 'GPIO0', 'GPIO1', 'GPIO2', 'GPIO3', 'PWM0', 'GPIO4', None, 'SWDIO', 'SWDCLK', 'nRESET', 'UART_TX']
    W = s.ic(100, 26, 44, s.b.ref('U'), 'HX6538 (WiseEye2)', left=left, right=right, pitch=4, desc='Himax WiseEye2, Cortex-M55 + Ethos-U55', sub='pinner etter Himax referansedesign')
    s.label(W['VDD_3V3'][:2], '3V3', 'l', 3); s.label(W['VDD_1V8'][:2], '1V8', 'l', 3)
    s.text(W['VCORE'][0] - 3, W['VCORE'][1] + 0.7, 'intern PMU / ekstern etter ref.', 1.5, 'end', NOTE); s.wire(W['VCORE'][:2], (W['VCORE'][0] - 1, W['VCORE'][1]))
    for nm in ['CSI_CLKP', 'CSI_CLKN', 'CSI_D0P', 'CSI_D0N']: s.label(W[nm][:2], nm, 'l', 3)
    for nm, net in [('SEN_MCLK', 'SEN_MCLK'), ('SEN_XSHUT', 'SEN_XSHUT'), ('SEN_INT', 'SEN_INT'), ('SEN_STROBE', 'FSTROBE'), ('I2CM_SDA', 'I2C_SDA'), ('I2CM_SCL', 'I2C_SCL')]:
        s.label(W[nm][:2], net, 'l', 3)
    s.gndjoin(W, ['GND', 'GND#2'])
    for nm, net in [('QSPI_CS', 'FL_CS'), ('QSPI_CLK', 'FL_CLK'), ('QSPI_IO0', 'FL_IO0'), ('QSPI_IO1', 'FL_IO1'), ('QSPI_IO2', 'FL_IO2'), ('QSPI_IO3', 'FL_IO3'),
                    ('SPI_SCK', 'CAN_SCK'), ('SPI_MOSI', 'CAN_MOSI'), ('SPI_MISO', 'CAN_MISO'), ('SPI_CS', 'CAN_CS'), ('GPIO0', 'CAN_INT'), ('GPIO1', 'PROX_INT'),
                    ('GPIO2', 'ACC_INT'), ('GPIO3', 'HEAT_EN'), ('PWM0', 'IR_PWM'), ('GPIO4', 'CAN_STB'), ('SWDIO', 'WE_SWDIO'), ('SWDCLK', 'WE_SWDCLK'), ('nRESET', 'WE_RESET'), ('UART_TX', 'WE_UART_TX')]:
        s.label(W[nm][:2], net, 'r', 3)
    s.note(22, 130, ['Avkopling og krystall etter Himax', 'referansedesign (ikke vist).', 'CSI-2 med 1 datalane: 100 Ω', 'differensielt, korte og like', 'lange baner.', 'UART_TX: testpunkt for logg.'], w=60, title='Merknader')
    swd(s, 190, 150, 'WE_')

    # ---------- B bildebrikke ----------
    s.block(256, 16, 154, 92, 'B  Bildebrikke HM0360 (modul med M7-objektiv)')
    C = s.ic(300, 30, 30, s.b.ref('J'), 'HM0360-modul (FPC)', left=['VDD', 'IOVDD', 'MCLK', 'XSHUTDOWN', 'INT', 'STROBE', 'GND'], right=['SDA', 'SCL', 'MIPI_CLKP', 'MIPI_CLKN', 'MIPI_D0P', 'MIPI_D0N'], pitch=5, desc='HM0360 VGA mono uten IR-filter, M7-objektiv ca. 100°')
    s.label(C['VDD'][:2], '3V3', 'l', 3); s.label(C['IOVDD'][:2], '1V8', 'l', 3)
    for nm, net in [('MCLK', 'SEN_MCLK'), ('XSHUTDOWN', 'SEN_XSHUT'), ('INT', 'SEN_INT'), ('STROBE', 'FSTROBE')]: s.label(C[nm][:2], net, 'l', 3)
    s.pl(C, 'GND', '', 3, 'gnd')
    for nm, net in [('SDA', 'I2C_SDA'), ('SCL', 'I2C_SCL'), ('MIPI_CLKP', 'CSI_CLKP'), ('MIPI_CLKN', 'CSI_CLKN'), ('MIPI_D0P', 'CSI_D0P'), ('MIPI_D0N', 'CSI_D0N')]:
        s.label(C[nm][:2], net, 'r', 3)
    s.note(264, 90, ['Modulen har egne regulatorer for sensorens analog- og kjernespenning.', 'INT = bevegelsesdeteksjon i lavstrømsmodus, vekker WiseEye2.'], w=140)

    # ---------- C anti-masking og sensorer ----------
    s.block(256, 114, 154, 142, 'C  Anti-masking, bevegelse, klima og signatur')
    P = s.ic(290, 126, 24, s.b.ref('U'), 'VCNL4040', left=['VDD'], right=['SDA', 'SCL', 'INT', 'GND'], pitch=5, desc='IR-nærhet og lys, ved linsen')
    s.label(P['VDD'][:2], '3V3', 'l', 3)
    for nm, net in [('SDA', 'I2C_SDA'), ('SCL', 'I2C_SCL'), ('INT', 'PROX_INT')]: s.label(P[nm][:2], net, 'r', 3)
    s.pl(P, 'GND', '', 3, 'gnd')
    A = s.ic(290, 162, 24, s.b.ref('U'), 'LIS2DW12', left=['VDD', 'VDD_IO', 'SA0', 'CS'], right=['SDA', 'SCL', 'INT1', 'GND'], pitch=5, desc='Akselerometer, slag og vridning')
    for nm in ['VDD', 'VDD_IO', 'CS']: s.label(A[nm][:2], '3V3', 'l', 3)
    s.pl(A, 'SA0', '', 3, 'gnd')
    for nm, net in [('SDA', 'I2C_SDA'), ('SCL', 'I2C_SCL'), ('INT1', 'ACC_INT')]: s.label(A[nm][:2], net, 'r', 3)
    s.pl(A, 'GND', '', 3, 'gnd')
    T = s.ic(362, 126, 20, s.b.ref('U'), 'SHT40', left=['VDD'], right=['SDA', 'SCL', 'GND'], pitch=5, desc='Temperatur og fukt ved vinduet')
    s.label(T['VDD'][:2], '3V3', 'l', 3)
    s.label(T['SDA'][:2], 'I2C_SDA', 'r', 3); s.label(T['SCL'][:2], 'I2C_SCL', 'r', 3)
    s.pl(T, 'GND', '', 3, 'gnd')
    atecc(s, 362, 162, '3V3')
    s.note(262, 210, ['Adresser: VCNL4040 0x60, LIS2DW12 0x18, SHT40 0x44, ATECC608B 0x35*.', '*ATECC608B kjøpes med alternativ adresse (TNGTLS/TFLXTLS) for å unngå', 'kollisjon med VCNL4040 på 0x60. Pull-up 4,7 kΩ på I2C_SDA/SCL.', 'Hvert bilde og hver heartbeat signeres med telleren i ATECC608B.'], w=144)

    # ---------- D flash ----------
    s.block(14, 204, 236, 52, 'D  Flash 16 MB (bilder før og etter hendelse)')
    F = s.ic(80, 212, 28, s.b.ref('U'), 'W25Q128JV', left=['/CS', 'CLK', 'IO0', 'IO1'], right=['VCC', 'IO2', 'IO3', 'GND'], pitch=5, desc='QSPI NOR-flash 128 Mbit')
    for nm, net in [('/CS', 'FL_CS'), ('CLK', 'FL_CLK'), ('IO0', 'FL_IO0'), ('IO1', 'FL_IO1')]: s.label(F[nm][:2], net, 'l', 3)
    s.pl(F, 'VCC', '3V3', 3, 'pwr')
    for nm, net in [('IO2', 'FL_IO2'), ('IO3', 'FL_IO3')]: s.label(F[nm][:2], net, 'r', 3)
    s.pl(F, 'GND', '', 3, 'gnd')
    s.note(150, 222, ['Ringbuffer med bilder.', 'Krypteres før lagring.'], w=60)
    return s
