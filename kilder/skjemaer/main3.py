from lib import Sheet, NOTE, NET

def tc2030(s, x, y, ref, prefix, vref='3V3_AON'):
    J = s.conn(x, y, ref, 'TC2030-IDC-NL', [(1, 'VREF'), (2, 'SWDIO'), (3, 'RESET'), (4, 'SWDCLK'), (5, 'GND'), (6, 'NC')], pitch=4.5, desc='Testpunkt for SWD, ingen komponent')
    s.pwr(J['VREF'][:2], vref, 'r')
    for nm in ['SWDIO', 'RESET', 'SWDCLK']: s.label(J[nm][:2], f'{prefix}_{nm}', 'r', 3)
    s.pl(J, 'GND', '', 3, 'gnd'); s.pl(J, 'NC', '', kind='nc')
    return J

def sheet_cop_can(B):
    s = Sheet(B, 'Koprosessor (BLE-gateway) og isolert CAN-lytting')
    # ---------- A nRF54L15 ----------
    s.block(14, 16, 186, 124, 'A  Koprosessor nRF54L15 (modul med antenne)')
    U = s.ic(74, 32, 38, 'U12', 'nRF54L15-modul', left=['VDD', None, 'nRESET', 'SWDIO', 'SWDCLK', None, 'GND', 'GND#2'],
             right=['UART_RX', 'UART_TX', 'SPI_SCK', 'SPI_MOSI', 'SPI_MISO', 'SPI_CS', 'GPIO_INT', None, 'GPIO_LED'], pitch=5,
             desc='nRF54L15-modul med integrert 2,4 GHz-antenne', sub='f.eks. Raytac, Fanstel eller u-blox')
    vx, vy = U['VDD'][:2]
    s.wire((vx, vy), (vx - 26, vy)); s.pwr((vx - 26, vy), '3V3_AON', 'u')
    for i, v in enumerate(['10 µF', '100 nF']):
        px = vx - 8 - i * 9; s.dot((px, vy)); c = s.C((px, vy), 'v', v, L=5, side='l' if i else 'r'); s.gnd(c[1])
    s.label(U['nRESET'][:2], 'COP_RESET', 'l', 3)
    s.label(U['SWDIO'][:2], 'COP_SWDIO', 'l', 3); s.label(U['SWDCLK'][:2], 'COP_SWDCLK', 'l', 3)
    s.gndjoin(U, ['GND', 'GND#2'])
    for nm, net in [('UART_RX', 'COP_UART_TX'), ('UART_TX', 'COP_UART_RX'), ('SPI_SCK', 'CAN_SCK'), ('SPI_MOSI', 'CAN_MOSI'), ('SPI_MISO', 'CAN_MISO'), ('SPI_CS', 'CAN_CS'), ('GPIO_INT', 'CAN_INT')]:
        s.label(U[nm][:2], net, 'r', 3)
    l = U['GPIO_LED'][:2]
    r = s.R(l, 'h', '1 kΩ', L=10); d = s.D(r[1], 'h', 'Blå, service', L=10, kind='led'); s.wire(d[1], (d[1][0] + 3, d[1][1])); s.gnd((d[1][0] + 3, d[1][1]))
    J = tc2030(s, 28, 92, 'J10', 'COP')
    s.note(96, 100, ['UART_RX ← P0.25 og UART_TX → P0.29 på nRF9151.', 'COP_RESET er open drain fra I/O-utvideren (ark 6).', 'Modulen er BLE-gateway for utstyrsbrikker', '(Coded PHY) og styrer CAN-kontrolleren.', 'Velg modul med CE/RED-sertifisering og', 'plasser antennen mot plastsiden av kapslingen.'], w=98, title='Merknader')

    # ---------- B CAN ----------
    s.block(206, 16, 204, 124, 'B  CAN-kontroller og isolert transceiver (bare lytting)')
    M = s.ic(236, 32, 30, 'U13', 'MCP2518FD', left=['SCK', 'SDI', 'SDO', 'nCS', 'nINT', 'INT0/GPIO0', 'INT1/GPIO1'], right=['VDD', 'OSC1', 'OSC2', 'TXCAN', 'RXCAN', 'CLKO/SOF', 'VSS'], pitch=5, desc='CAN FD-kontroller, SPI')
    for nm, net in [('SCK', 'CAN_SCK'), ('SDI', 'CAN_MOSI'), ('SDO', 'CAN_MISO'), ('nCS', 'CAN_CS'), ('nINT', 'CAN_INT')]:
        s.label(M[nm][:2], net, 'l', 3)
    s.pl(M, 'INT0/GPIO0', '', kind='nc'); s.pl(M, 'INT1/GPIO1', '', kind='nc'); s.pl(M, 'CLKO/SOF', '', kind='nc')
    vx, vy = M['VDD'][:2]; s.wire((vx, vy), (vx + 10, vy)); s.pwr((vx + 10, vy), '3V3_AON', 'u')
    s.text(vx + 6, vy - 1.5, '100 nF', 1.5, 'start', NOTE)
    o1, o2 = M['OSC1'][:2], M['OSC2'][:2]
    xx = o1[0] + 14
    s.wire(o1, (xx, o1[1])); s.wire(o2, (xx, o2[1]))
    y_ = s.X((xx, o1[1]), 'v', '40 MHz', L=5)
    s.dot((xx, o1[1])); s.dot((xx, o2[1]))
    for yy in (o1[1], o2[1]):
        s.wire((xx, yy), (xx + 14, yy))
    c1 = s.C((xx + 14, o1[1]), 'h', '12 pF*', L=8); e = c1[1][0] + 2; s.wire(c1[1], (e, o1[1]))
    c2 = s.C((xx + 14, o2[1]), 'h', '', L=8, desc='12 pF*'); s.wire(c2[1], (e, o2[1]))
    s.wire((e, o1[1]), (e, o2[1])); s.dot((e, o2[1])); s.wire((e, o2[1]), (e + 3, o2[1])); s.gnd((e + 3, o2[1]))
    t = M['TXCAN'][:2]; s.wire(t, (t[0] + 4, t[1])); s.text(t[0] + 5, t[1] + 0.7, 'TP1, ikke tilkoplet', 1.6, 'start', NOTE)
    s.pl(M, 'VSS', '', 3, 'gnd')
    I = s.ic(332, 74, 24, 'U15', 'ISO1042', left=['VCC1', 'TXD', 'RXD', 'GND1'], right=['VCC2', 'CANH', 'CANL', 'GND2'], pitch=5, desc='Isolert CAN FD-transceiver 5 kV')
    rx = M['RXCAN'][:2]
    s.wire(rx, (rx[0] + 6, rx[1]), (rx[0] + 6, I['RXD'][1]), I['RXD'][:2])
    s.pl(I, 'VCC1', '3V3_AON', 3, 'pwr')
    tx = I['TXD'][:2]; r = s.R((tx[0] - 14, tx[1]), 'h', '10 kΩ', L=12); s.wire(r[1], tx); s.pwr(r[0], '3V3_AON', 'l')
    s.pl(I, 'GND1', '', 3, 'gnd')
    s.label(I['VCC2'][:2], '5V_ISO', 'r', 3); s.label(I['CANH'][:2], 'MCAN_H', 'r', 3); s.label(I['CANL'][:2], 'MCAN_L', 'r', 3)
    g2 = I['GND2'][:2]; s.wire(g2, (g2[0] + 3, g2[1])); s.gnd((g2[0] + 3, g2[1]), 'GND_ISO')
    s.note(214, 118, ['Maskinvaresikret lyttemodus: TXD på U15 holdes høy (resessiv) med R,', 'og TXCAN på U13 er ikke koplet til. Enheten kan ikke sende på maskinens buss.', 'U13 kjøres i tillegg i Listen Only-modus.'], w=188, title='Lytt, ikke skriv')

    # ---------- C isolert forsyning ----------
    s.block(14, 148, 186, 108, 'C  Isolert forsyning til CAN-siden')
    P = s.ic(80, 166, 28, 'U14', 'UCC12050', left=['VINP', None, 'EN', 'SEL', 'GNDP'], right=['VISO', 'GNDS'], pitch=5, desc='Isolert DC/DC 500 mW, 5 kV')
    vx, vy = P['VINP'][:2]; s.wire((vx, vy), (vx - 24, vy)); s.pwr((vx - 24, vy), '5V_BUCK', 'u'); s.dot((vx - 14, vy))
    c = s.C((vx - 14, vy), 'v', '10 µF', L=5, side='l'); s.gnd(c[1])
    s.label(P['EN'][:2], 'CAN_PWR_EN', 'l', 3)
    s.text(P['SEL'][0] - 3, P['SEL'][1] + 0.7, 'SEL: 5,0 V', 1.6, 'end', NOTE); s.wire(P['SEL'][:2], (P['SEL'][0] - 1, P['SEL'][1]))
    s.pl(P, 'GNDP', '', 3, 'gnd')
    vo = P['VISO'][:2]; o = (vo[0] + 24, vo[1]); s.wire(vo, o); s.dot((vo[0] + 14, vo[1]))
    c = s.C((vo[0] + 14, vo[1]), 'v', '10 µF', L=7); s.gnd(c[1], 'GND_ISO')
    s.label(o, '5V_ISO', 'r', 0)
    g = P['GNDS'][:2]; s.wire(g, (g[0] + 3, g[1])); s.gnd((g[0] + 3, g[1]), 'GND_ISO')
    s.note(22, 226, ['CAN-siden er galvanisk skilt fra enheten (jordfeil og støy fra maskinen).', 'CAN er bare i bruk når maskinstrøm finnes, derfor forsyning fra 5V_BUCK.', 'Krypavstand ≥ 4 mm mellom GND og GND_ISO på kortet.'], w=172)

    # ---------- D kontakt ----------
    s.block(206, 148, 204, 108, 'D  Tilkopling til maskinens CAN-buss (Y-kabel)')
    y0 = 172
    s.label((228, y0), 'MCAN_H', 'l', 0); s.label((228, y0 + 20), 'MCAN_L', 'l', 0)
    # felles modus drossel som to spoler
    l1 = s.Lind((228, y0), 'h', '', L=14, desc='Strømkompensert drossel 51 µH (2 linjer)')
    l2 = s.Lind((228, y0 + 20), 'h', '', L=14, ref=l1 and None, desc='(samme komponent som over)')
    s.text(235, y0 + 10.7, 'CMC, f.eks. TDK ACT45B', 1.6, 'middle', NOTE)
    ah, al = (l1[1][0] + 12, y0), (l2[1][0] + 12, y0 + 20)
    s.wire(l1[1], ah); s.wire(l2[1], al)
    for p in (ah, al):
        s.dot(p); d = s.D(p, 'v', '', L=10, kind='tvsb', desc='CAN ESD, NUP2105L (2 linjer i én kapsel)'); s.gnd(d[1], 'GND_ISO')
    s.text(ah[0] + 6, y0 + 30, 'NUP2105L', 1.6, 'start', NOTE)
    J = s.conn(330, 162, 'J4', 'Deutsch DT04-4P', [(1, 'CAN_H'), (2, 'CAN_L'), (3, 'CAN_GND'), (4, 'SHLD')], side='l', pitch=5, desc='Maskin-CAN, IP67')
    s.wire(ah, (J['CAN_H'][0] - 10, y0), (J['CAN_H'][0] - 10, J['CAN_H'][1]), J['CAN_H'][:2])
    s.wire(al, (J['CAN_L'][0] - 6, al[1]), (J['CAN_L'][0] - 6, J['CAN_L'][1]), J['CAN_L'][:2])
    g = J['CAN_GND'][:2]; s.wire(g, (g[0] - 3, g[1])); s.gnd((g[0] - 3, g[1]), 'GND_ISO')
    sh = J['SHLD'][:2]
    s.wire(sh, (sh[0] - 3, sh[1])); s.wire((sh[0] - 3, sh[1]), (sh[0] - 3, sh[1] + 4))
    s.text(sh[0] - 30, sh[1] + 14, 'SHLD: 1 nF 2 kV ∥ 1 MΩ til GND_ISO', 1.5, 'start', NOTE)
    s.note(214, 214, ['Ingen terminering: maskinens buss er allerede terminert i begge ender.', 'Y-kabel mot diagnosekontakt (ofte Deutsch 9-pin), tilpasses maskintype.', '250 eller 500 kbit/s J1939, ISOBUS på traktorer.'], w=188)
    return s


def sheet_radio(B):
    s = Sheet(B, 'GNSS, LoRa 868 MHz og flash')
    # ---------- A GNSS ----------
    s.block(14, 16, 200, 124, 'A  GNSS u-blox MAX-M10S med jamming-deteksjon')
    G = s.ic(70, 30, 36, 'U16', 'MAX-M10S', left=['VCC', 'V_IO', 'V_BCKP', None, 'RESET_N', 'SAFEBOOT_N', 'EXTINT', None, 'GND'],
             right=['RF_IN', 'VCC_RF', 'LNA_EN', 'SDA', 'SCL', 'TXD', 'RXD', 'TIMEPULSE'], pitch=5, desc='GNSS-modul, I2C')
    s.pl(G, 'VCC', '3V3_SW', 3, 'pwr'); s.label(G['V_IO'][:2], '3V3_SW', 'l', 3)
    s.label(G['V_BCKP'][:2], '3V3_AON', 'l', 3)
    s.label(G['RESET_N'][:2], 'GNSS_RESET_N', 'l', 3)
    s.pl(G, 'SAFEBOOT_N', '', kind='nc'); s.pl(G, 'EXTINT', '', kind='nc'); s.pl(G, 'TXD', '', kind='nc'); s.pl(G, 'RXD', '', kind='nc'); s.pl(G, 'TIMEPULSE', '', kind='nc'); s.pl(G, 'LNA_EN', '', kind='nc')
    s.text(G['SAFEBOOT_N'][0] - 3, G['SAFEBOOT_N'][1] + 0.7, 'testpunkt', 1.5, 'end', NOTE)
    s.pl(G, 'GND', '', 3, 'gnd')
    s.label(G['SDA'][:2], 'I2C_SDA', 'r', 3); s.label(G['SCL'][:2], 'I2C_SCL', 'r', 3)
    s.text(G['TXD'][0] + 3, G['TXD'][1] + 0.7, 'testpunkt', 1.5, 'start', NOTE)
    # RF: bryter mellom patch og ekstern aktiv antenne
    rf = G['RF_IN'][:2]
    SW = s.ic(150, rf[1] - 4, 22, 'U17', 'SPDT RF-bryter', left=['RFC', None, None, 'CTRL', 'VDD', 'GND'], right=['RF1', 'RF2'], pitch=4, desc='SPDT RF-bryter, f.eks. pSemi PE4259')
    s.wire(rf, SW['RFC'][:2])
    s.label(SW['CTRL'][:2], 'ANT_SEL', 'l', 3)
    s.label(SW['VDD'][:2], '3V3_AON', 'l', 3); s.pl(SW, 'GND', '', 3, 'gnd')
    p1 = SW['RF1'][:2]; s.wire(p1, (p1[0] + 6, p1[1])); s.ant((p1[0] + 6, p1[1]), 'AE2 patch')
    p2 = SW['RF2'][:2]
    c = s.C(p2, 'h', '47 pF', L=8, desc='DC-sperre')
    jn = (c[1][0] + 6, p2[1]); s.wire(c[1], jn); s.dot(jn); s.wire(jn, (jn[0] + 12, p2[1])); s.ant((jn[0] + 12, p2[1]), 'J7 SMA')
    s.text(jn[0] + 14, p2[1] + 3, 'aktiv antenne', 1.5, 'start', NOTE)
    l = s.Lind(jn, 'v', '47 nH', L=10)
    r = s.R(l[1], 'v', '10 Ω', L=10, desc='Strømmåling antenne')
    s.wire(r[1], (jn[0], r[1][1] + 2)); s.label((jn[0], r[1][1] + 2), 'VCC_RF', 'd', 0)
    s.text(jn[0] + 4, l[1][1] + 1.6, 'GNSS_ANT_I+', 1.5, 'start', NET)
    s.label(G['VCC_RF'][:2], 'VCC_RF', 'r', 3)
    s.b.bom.append(('U18', 'TLV7031', 'Komparator for GNSS-antenneovervåking (ikke tegnet i detalj)'))
    s.note(22, 106, ['Jamming og spoofing: MAX-M10S melder interferens (jamming-indikator) og', 'spoofing-flagg over I2C. nRF9151 sin egen GNSS-inngang brukes ikke.', 'Antenneovervåking: strøm over 10 Ω måles av komparator (U18, ikke vist i', 'detalj) → GNSS_ANT_OK til I/O-utvideren. Ingen strøm = kabel kuttet.', 'Buck-regulatorer holdes langt fra GNSS-delen.'], w=190, title='Merknader')

    # ---------- B LoRa ----------
    s.block(220, 16, 190, 124, 'B  LoRa 868 MHz (SX1262-modul)')
    L = s.ic(246, 30, 30, 'U19', 'E22-900M22S', left=['VCC', None, 'NSS', 'SCK', 'MOSI', 'MISO', 'BUSY', 'DIO1', 'NRST'], right=['ANT', 'TXEN', 'DIO2', 'RXEN', 'GND'], pitch=5, desc='LoRa-modul SX1262, +22 dBm')
    vx, vy = L['VCC'][:2]; s.wire((vx, vy), (vx - 16, vy)); s.pwr((vx - 16, vy), '3V3_AON', 'u'); s.dot((vx - 10, vy))
    c = s.C((vx - 10, vy), 'v', '22 µF', L=5, side='l'); s.gnd(c[1])
    for nm, net in [('NSS', 'CS_LORA'), ('SCK', 'SPI_SCK'), ('MOSI', 'SPI_MOSI'), ('MISO', 'SPI_MISO'), ('BUSY', 'LORA_BUSY'), ('DIO1', 'LORA_DIO1'), ('NRST', 'LORA_NRESET')]:
        s.label(L[nm][:2], net, 'l', 3)
    t, d2 = L['TXEN'][:2], L['DIO2'][:2]
    s.wire(t, (t[0] + 3, t[1]), (t[0] + 3, d2[1]), d2); s.dot((t[0] + 3, d2[1]))
    s.text(t[0] + 4.5, t[1] + 2.9, 'DIO2 styrer TXEN', 1.5, 'start', NOTE)
    s.label(L['RXEN'][:2], 'LORA_RXEN', 'r', 3)
    s.pl(L, 'GND', '', 3, 'gnd')
    a = L['ANT'][:2]
    SW = s.ic(320, a[1] - 4, 22, 'U20', 'SPDT RF-bryter', left=['RFC', None, None, 'CTRL', 'VDD', 'GND'], right=['RF1', 'RF2'], pitch=4, desc='SPDT RF-bryter, f.eks. pSemi PE4259')
    s.wire(a, SW['RFC'][:2]); s.label(SW['CTRL'][:2], 'ANT_SEL', 'l', 3)
    s.label(SW['VDD'][:2], '3V3_AON', 'l', 3); s.pl(SW, 'GND', '', 3, 'gnd')
    p1 = SW['RF1'][:2]; s.wire(p1, (p1[0] + 8, p1[1])); s.ant((p1[0] + 8, p1[1]), 'AE3 PCB')
    p2 = SW['RF2'][:2]
    c = s.C(p2, 'h', '100 pF', L=8)
    jn = (c[1][0] + 8, p2[1]); s.wire(c[1], jn); s.dot(jn); s.wire(jn, (jn[0] + 14, p2[1])); s.ant((jn[0] + 14, p2[1]), 'J8 SMA')
    l = s.Lind(jn, 'v', '1 µH', L=10)
    nd = (jn[0], l[1][1] + 2); s.wire(l[1], nd); s.dot(nd)
    r = s.R(nd, 'v', '100 kΩ', L=10, side='l'); s.pwr(r[1], '3V3_SW', 'd')
    r = s.R(nd, 'h', '10 kΩ', L=10); s.dot(r[1]); c = s.C(r[1], 'v', '100 nF', L=7); s.gnd(c[1])
    s.label((r[1][0], r[1][1]), 'ANT_LORA_SENSE', 'r', 9)
    s.b.bom += [('AE2', 'GNSS-patch 25 × 25 mm', 'Intern reserveantenne GNSS'), ('J7', 'SMA hunn IP67, skott', 'Ekstern aktiv GNSS-antenne'), ('AE3', 'PCB-antenne 868 MHz', 'Kobberbane, ingen komponent'), ('J8', 'SMA hunn IP67, skott', 'Ekstern LoRa-antenne')]
    s.note(228, 120, ['Sjekk TXEN/RXEN-styring og CE/RED-samsvar mot modulens datablad.', 'Ca. 120 mA sendetopp: VSYS-bufferen tar toppen.'], w=176)

    # ---------- C flash ----------
    s.block(14, 148, 200, 80, 'C  Flash 64 Mbit (hendelseslogg og FOTA)')
    F = s.ic(80, 164, 30, 'U21', 'MX25R6435F', left=['CS#', 'SCLK', 'SI', 'SO'], right=['VCC', 'WP#', 'HOLD#', 'GND'], pitch=5, desc='SPI NOR-flash 64 Mbit, lav effekt')
    for nm, net in [('CS#', 'CS_FLASH'), ('SCLK', 'SPI_SCK'), ('SI', 'SPI_MOSI'), ('SO', 'SPI_MISO')]: s.label(F[nm][:2], net, 'l', 3)
    vx, vy = F['VCC'][:2]
    s.wire((vx, vy), (vx + 26, vy)); s.pwr((vx + 26, vy), '3V3_SW', 'u')
    for nm, xo in [('WP#', 6), ('HOLD#', 12)]:
        p = F[nm][:2]
        s.wire(p, (p[0] + xo, p[1]), (p[0] + xo, vy)); s.dot((p[0] + xo, vy))
    s.text(F['_box'][0], F['_box'][1] + F['_box'][3] + 6, 'WP# og HOLD# koplet til VCC (ikke brukt).', 1.5, 'start', NOTE)
    s.dot((vx + 20, vy)); c = s.C((vx + 20, vy), 'v', '100 nF', L=7); s.gnd(c[1])
    s.pl(F, 'GND', '', 3, 'gnd')
    s.note(22, 216, ['Delt SPI-buss med radar og LoRa. Ekstern flash ≥ 4 MB er nødvendig for modemoppdatering (FOTA).'], w=190)

    # ---------- D SPI-merknad ----------
    s.block(220, 148, 190, 80, 'D  SPI-buss og avslutning')
    s.note(228, 164, ['SPI_SCK, SPI_MOSI og SPI_MISO deles av A121 (ark 6), U19 og U21.', 'Seriemotstand 22–33 Ω ved nRF9151 på SCK og MOSI (dempning).', 'Egen CS per enhet: CS_RADAR, CS_LORA, CS_FLASH med 100 kΩ pull-up', 'til egen forsyning, slik at enheter som er av ikke velges.', 'Når 3V3_SW eller 1V8_RADAR er av, settes SPI-linjene lave', '(unngår lekkasje gjennom ESD-dioder).'], w=176, title='Delt buss')
    return s


def sheet_sensors(B):
    s = Sheet(B, 'Radar, sensorer, sikkerhetsbrikke og I/O-utvider')
    # ---------- A radar ----------
    s.block(14, 16, 196, 120, 'A  60 GHz radar Acconeer A121')
    R = s.ic(80, 30, 30, 'U22', 'A121', left=['VIO', 'VDIG', 'RX', 'TX', None, 'XIN', 'XOUT', 'GND'], right=['SPI_SCLK', 'SPI_MOSI', 'SPI_MISO', 'SPI_SS', 'INTERRUPT', 'ENABLE'], pitch=5, desc='60 GHz pulset koherent radar')
    s.label(R['VIO'][:2], '3V3_AON', 'l', 3)
    for k, nm in enumerate(['VDIG', 'RX', 'TX']):
        p = R[nm][:2]; xx = p[0] - 10 - k * 0
        s.wire(p, (p[0] - 22, p[1]))
    # felles 1,8 V til de tre domenene via egne ferritter
    xb = R['VDIG'][0] - 22
    s.wire((xb, R['VDIG'][1]), (xb, R['TX'][1]))
    s.dot((xb, R['RX'][1])); s.dot((xb, R['VDIG'][1]))
    s.wire((xb, R['VDIG'][1]), (xb - 6, R['VDIG'][1])); s.pwr((xb - 6, R['VDIG'][1]), '1V8_RADAR', 'u')
    for k, nm in enumerate(['VDIG', 'RX', 'TX']):
        p = R[nm][:2]; px = p[0] - 6 - 0
    s.text(xb + 2, R['TX'][1] + 4, 'Hver: 1 µF + 100 nF nær pinnen', 1.5, 'start', NOTE)
    x1, x2 = R['XIN'][:2], R['XOUT'][:2]
    xx = x1[0] - 10
    s.wire(x1, (xx, x1[1])); s.wire(x2, (xx, x2[1]))
    s.X((xx, x1[1]), 'v', '24 MHz', L=5, side='l')
    s.text(xx - 3, x2[1] + 4, 'lastkapasitans etter datablad', 1.5, 'end', NOTE)
    s.pl(R, 'GND', '', 3, 'gnd')
    for nm, net in [('SPI_SCLK', 'SPI_SCK'), ('SPI_MOSI', 'SPI_MOSI'), ('SPI_MISO', 'SPI_MISO'), ('SPI_SS', 'CS_RADAR'), ('INTERRUPT', 'RADAR_INT'), ('ENABLE', 'RADAR_EN')]:
        s.label(R[nm][:2], net, 'r', 3)
    s.note(22, 108, ['RX, TX og VDIG = 1,8 V fra U6 (1V8_RADAR). VIO = 3,3 V som nRF9151.', 'Radaren monteres under et plastvindu uten metallpigment, etter', 'Acconeers retningslinjer. Ingen kobber over antennene i brikken.', 'ENABLE lav gir under 1 µA.'], w=184)

    # ---------- B sensorer ----------
    s.block(216, 16, 194, 120, 'B  IMU, lyssensor, mikrofon')
    I = s.ic(244, 30, 28, 'U23', 'LSM6DSV16X', left=['VDD', 'VDDIO', 'SDO/SA0', 'CS'], right=['SDA', 'SCL', 'INT1', 'INT2', 'GND'], pitch=5, desc='IMU 6 akser')
    s.label(I['VDD'][:2], '3V3_AON', 'l', 3); s.label(I['VDDIO'][:2], '3V3_AON', 'l', 3)
    s.label(I['SDO/SA0'][:2], '3V3_AON', 'l', 3); s.label(I['CS'][:2], '3V3_AON', 'l', 3)
    for nm, net in [('SDA', 'I2C_SDA'), ('SCL', 'I2C_SCL'), ('INT1', 'IMU_INT1'), ('INT2', 'SYS_INT')]: s.label(I[nm][:2], net, 'r', 3)
    s.pl(I, 'GND', '', 3, 'gnd')
    s.text(244, 72, 'SA0 høy: adresse 0x6B. INT2 open drain.', 1.5, 'start', NOTE)
    O = s.ic(244, 78, 28, 'U24', 'OPT3001', left=['VDD', 'ADDR'], right=['SDA', 'SCL', 'INT', 'GND'], pitch=5, desc='Lyssensor')
    s.label(O['VDD'][:2], '3V3_AON', 'l', 3); s.pl(O, 'ADDR', '', 3, 'gnd')
    for nm, net in [('SDA', 'I2C_SDA'), ('SCL', 'I2C_SCL'), ('INT', 'SYS_INT')]: s.label(O[nm][:2], net, 'r', 3)
    s.pl(O, 'GND', '', 3, 'gnd')
    Mi = s.ic(346, 30, 26, 'U27', 'IM69D130', left=['VDD', 'SELECT', 'GND'], right=['CLK', 'DATA'], pitch=5, desc='PDM-mikrofon')
    s.label(Mi['VDD'][:2], '3V3_SW', 'l', 3); s.pl(Mi, 'SELECT', '', 3, 'gnd'); s.pl(Mi, 'GND', '', 3, 'gnd')
    s.label(Mi['CLK'][:2], 'PDM_CLK', 'r', 3); s.label(Mi['DATA'][:2], 'PDM_DIN', 'r', 3)
    s.note(334, 64, ['Lyd analyseres lokalt,', 'ingen lagring (personvern).', 'Port i kortet med pustende', 'membran.'], w=70)

    # ---------- C sikkerhet og I/O ----------
    s.block(14, 142, 196, 114, 'C  Sikkerhetsbrikke og I2C-buss')
    A = s.ic(64, 160, 26, 'U25', 'ATECC608B', left=['VCC'], right=['SDA', 'SCL', 'GND'], pitch=5, desc='Sikkerhetsbrikke ECDSA P-256')
    s.label(A['VCC'][:2], '3V3_AON', 'l', 3); s.label(A['SDA'][:2], 'I2C_SDA', 'r', 3); s.label(A['SCL'][:2], 'I2C_SCL', 'r', 3); s.pl(A, 'GND', '', 3, 'gnd')
    # pull-ups
    for k, (net, val) in enumerate([('I2C_SDA', '4,7 kΩ'), ('I2C_SCL', '4,7 kΩ'), ('SYS_INT', '100 kΩ')]):
        x = 140 + k * 20
        s.pwr((x, 160), '3V3_AON', 'u'); r = s.R((x, 160), 'v', val, L=10, side='r'); s.label(r[1], net, 'd', 2)
    rows = [('U4 BQ25180', '0x6A'), ('U16 MAX-M10S', '0x42'), ('U23 LSM6DSV16X', '0x6B'), ('U24 OPT3001', '0x44'), ('U25 ATECC608B', '0x60'), ('U26 PCAL6416A', '0x20')]
    s.text(22, 202, 'I2C-adresser (7 bit)', 1.9, 'start', NOTE, 'bold')
    for k, (a_, b_) in enumerate(rows):
        s.text(22 + (k // 3) * 60, 208 + (k % 3) * 5, a_, 1.8); s.text(52 + (k // 3) * 60, 208 + (k % 3) * 5, b_, 1.8, 'start', NET)
    s.note(22, 230, ['Ingen adressekollisjon. ATECC608B nøkler låses ved produksjon.', 'I2C 400 kHz. SYS_INT samler open drain-avbrudd fra U4, U23, U24, U26.'], w=184)

    # ---------- D I/O-utvider ----------
    s.block(216, 142, 194, 114, 'D  I/O-utvider PCAL6416A (16 bit)')
    io = [('P0_0', 'LED_G', 'Grønn LED via 1 kΩ'), ('P0_1', 'LED_R', 'Rød LED via 1 kΩ'), ('P0_2', 'GNSS_RESET_N', 'U16'), ('P0_3', 'LORA_NRESET', 'U19'),
          ('P0_4', 'EXP_EN', 'U8 lastbryter'), ('P0_5', 'MESH_DRIVE', 'tamperfolie (ark 7)'), ('P0_6', 'ANT_SEL', 'intern/ekstern antenne'), ('P0_7', 'BAT_HEAT', 'Q3 (ark 2)'),
          ('P1_0', 'RADAR_PWR', 'U6 EN'), ('P1_1', 'PWR_EN_SENS', 'U7 ON'), ('P1_2', 'COP_RESET', 'U12, open drain'), ('P1_3', 'CAN_PWR_EN', 'U14 EN'),
          ('P1_4', 'LORA_RXEN', 'U19 RXEN'), ('P1_5', 'GNSS_ANT_OK', 'inngang fra U18'), ('P1_6', 'HW_REV0', 'inngang, stropp'), ('P1_7', 'RESERVE', '')]
    X = s.ic(236, 154, 26, 'U26', 'PCAL6416A', left=['VDDI', 'VDDP', 'SDA', 'SCL', 'INT', 'RESET', 'ADDR', 'GND'], right=[p for p, _, _ in io], pitch=5.5, desc='I/O-utvider 16 bit, I2C')
    s.label(X['VDDI'][:2], '3V3_AON', 'l', 3); s.label(X['VDDP'][:2], '3V3_AON', 'l', 3)
    for nm, net in [('SDA', 'I2C_SDA'), ('SCL', 'I2C_SCL'), ('INT', 'SYS_INT'), ('RESET', '3V3_AON')]: s.label(X[nm][:2], net, 'l', 3)
    s.pl(X, 'ADDR', '', 3, 'gnd'); s.pl(X, 'GND', '', 3, 'gnd')
    for p, net, use in io:
        if net == 'RESERVE': s.pl(X, p, '', kind='nc'); continue
        s.label(X[p][:2], net, 'r', 3); s.text(X[p][0] + 24, X[p][1] + 0.7, use, 1.5, 'start', NOTE)
    return s


def sheet_tamper(B):
    s = Sheet(B, 'Sabotasjekretser og ekspansjonskontakt')
    # ---------- A tamperfolie ----------
    s.block(14, 16, 196, 100, 'A  Tamperfolie (bane som dekker kortet)')
    s.label((30, 44), 'MESH_DRIVE', 'l', 0)
    r = s.R((30, 44), 'h', '47 kΩ', L=12); n = (r[1][0] + 10, 44); s.wire(r[1], n); s.dot(n)
    # foliebane som buktet linje
    pts = [n]; x = n[0]
    for i in range(6):
        pts += [(x + 4, 44), (x + 4, 52)] if i % 2 == 0 else [(x + 4, 52), (x + 4, 44)]
        x += 4
    s.wire(*pts, c='#8a5a00')
    s.text(n[0] + 12, 58, 'Foliebane på L4 (serpentin)', 1.6, 'middle', '#8a5a00')
    e = pts[-1]
    r = s.R((e[0] + 4, e[1]), 'h', '47 kΩ', L=12); s.wire(e, (e[0] + 4, e[1])); s.wire(r[1], (r[1][0] + 2, r[1][1])); s.gnd((r[1][0] + 2, r[1][1]))
    s.wire(n, (n[0], 64)); r = s.R((n[0], 64), 'h', '10 kΩ', L=12); s.dot(r[1]); c = s.C(r[1], 'v', '100 nF', L=7); s.gnd(c[1])
    s.label(r[1], 'MESH_SENSE', 'r', 4)
    s.note(22, 92, ['MESH_DRIVE pulses kort, MESH_SENSE (AIN2) leses i pulsen.', 'Normal: ca. halv spenning. Brudd: stiger mot full. Kortsluttet mot jord: faller.', 'To baner flettet inn i hverandre gjør det vanskelig å bore uten å bryte.'], w=184)

    # ---------- B lokk og vegg ----------
    s.block(216, 16, 194, 100, 'B  Lokkbryter, veggbryter og ekspansjonssløyfe (i serie)')
    s.pwr((234, 34), '3V3_AON', 'u')
    r = s.R((234, 34), 'v', '3,3 MΩ', L=10, side='l'); n = (234, 48); s.wire(r[1], n); s.dot(n)
    sw1 = s.SW(n, 'h', 'Lokk (NC, lukket når lokket er på)', L=12, desc='Mikrobryter lokk')
    sw2 = s.SW((sw1[1][0] + 30, 48), 'h', 'Vegg (lukket når montert)', L=12, desc='Mikrobryter mot veggen')
    s.wire(sw1[1], (sw1[1][0] + 30, 48))
    lp = (sw2[1][0] + 8, 48); s.wire(sw2[1], lp)
    s.label(lp, 'EXP_LOOP_A', 'r', 0)
    s.text(lp[0] - 6, 58, 'sløyfe gjennom ekspansjonskontakten', 1.5, 'end', NOTE)
    s.label((356, 66), 'EXP_LOOP_B', 'l', 0); s.wire((356, 66), (362, 66)); s.gnd((362, 66))
    s.wire(n, (n[0] - 8, 48), (n[0] - 8, 72)); r = s.R((n[0] - 8, 72), 'h', '1 kΩ', L=10); s.dot(r[1]); c = s.C(r[1], 'v', '100 nF', L=7); s.gnd(c[1])
    s.label(r[1], 'LID_SW', 'r', 4)
    s.note(224, 96, ['Normal: kjeden er lukket, LID_SW lav (ca. 1 µA). Lokk åpnet, enheten tatt ned', 'eller ekspansjonskortet trukket ut: LID_SW høy → vekking og alarm.', 'Uten ekspansjonskort settes en kortslutningsplugg i kontakten.'], w=184)

    # ---------- C GPS-kabelsløyfe ----------
    s.block(14, 122, 196, 74, 'C  Kabelsløyfe rundt GPS-utstyret')
    s.pwr((40, 138), '3V3_SW', 'u')
    r = s.R((40, 138), 'v', '47 kΩ', L=10, side='l'); n = (40, 152); s.wire(r[1], n); s.dot(n)
    s.wire(n, (70, 152)); s.dot((60, 152))
    d = s.D((60, 152), 'v', 'SMAJ5.0CA', L=10, kind='tvsb'); s.gnd(d[1])
    r = s.R((70, 152), 'h', '1 kΩ', L=10); s.wire(r[1], (84, 152)); s.label((84, 152), 'GPS_LOOP_A', 'r', 0)
    s.label((106, 172), 'GPS_LOOP_B', 'l', 0)
    r = s.R((106, 172), 'h', '10 kΩ', L=12); s.wire(r[1], (r[1][0] + 2, 172)); s.gnd((r[1][0] + 2, 172))
    s.wire(n, (n[0] - 6, 152), (n[0] - 6, 168)); r = s.R((n[0] - 6, 168), 'h', '10 kΩ', L=10); s.dot(r[1]); c = s.C(r[1], 'v', '100 nF', L=7); s.gnd(c[1])
    s.label(r[1], 'GPS_LOOP_SENSE', 'r', 3)
    s.note(130, 140, ['Ledning fra J1-6 rundt', 'GPS-mottaker, skjerm og', 'kabler, tilbake til J1-7.', 'Normal ca. 0,6 V,', 'kuttet 3,3 V, kortsluttet 0 V.'], w=74)

    # ---------- D ekspansjonskontakt ----------
    s.block(216, 122, 194, 134, 'D  Ekspansjonskontakt (kamerahub / utvidelsesboks)')
    J = s.conn(300, 136, 'J5', 'Molex Micro-Fit 3.0, 10-pin', [(1, 'EXP_VIN'), (2, 'EXP_VIN#'), (3, 'GND'), (4, 'GND#'), (5, '3V3_EXP'), (6, 'UART_TX'), (7, 'UART_RX'), (8, 'EXP_INT'), (9, 'LOOP_A'), (10, 'LOOP_B')], side='l', pitch=5, desc='Ekspansjonskontakt, låsende')
    vx, vy = J['EXP_VIN'][:2]
    s.wire((vx, vy), (vx - 4, vy), (vx - 4, J['EXP_VIN#'][1]), J['EXP_VIN#'][:2]); s.dot((vx - 4, vy))
    f = s.F((vx - 26, vy), 'h', 'PTC 1,5 A', L=14); s.wire(f[1], (vx - 4, vy)); s.label(f[0], 'VIN_PROT', 'l', 0)
    g = J['GND'][:2]; s.wire(g, (g[0] - 4, g[1]), (g[0] - 4, J['GND#'][1]), J['GND#'][:2]); s.dot((g[0] - 4, g[1])); s.wire((g[0] - 4, J['GND#'][1]), (g[0] - 8, J['GND#'][1])); s.gnd((g[0] - 8, J['GND#'][1]))
    s.pwr(J['3V3_EXP'][:2], '3V3_EXP', 'l')
    for nm, net in [('UART_TX', 'EXP_UART_TX'), ('UART_RX', 'EXP_UART_RX'), ('EXP_INT', 'EXP_INT'), ('LOOP_A', 'EXP_LOOP_A'), ('LOOP_B', 'EXP_LOOP_B')]:
        s.label(J[nm][:2], net, 'l', 4)
    s.note(320, 150, ['Pinne 6 og 7 sett fra hovedenheten', '(TX ut, RX inn).', 'EXP_VIN maks 1,5 A til hub og', 'kamerapods. Strømmen begrenses', 'per port i hubben (eFuse).', 'LOOP_A–LOOP_B er kortsluttet', 'i hubben: trekkes kontakten,', 'brytes lokk-kjeden.'], w=84)
    s.note(222, 222, ['ESD-vern (TVS-array) på UART, EXP_INT og LOOP ved kontakten.', 'EXP_INT har 100 kΩ pull-down på hovedkortet.'], w=180)

    # ---------- E LED og testpunkt ----------
    s.block(14, 202, 196, 54, 'E  Statuslys og testpunkter')
    for k, (net, col) in enumerate([('LED_G', 'Grønn'), ('LED_R', 'Rød')]):
        x = 30 + k * 46
        s.label((x, 222), net, 'l', 0)
        r = s.R((x, 222), 'h', '1 kΩ', L=10); d = s.D(r[1], 'h', col, L=10, kind='led'); s.wire(d[1], (d[1][0] + 2, 222)); s.gnd((d[1][0] + 2, 222))
    s.note(22, 240, ['Lysene er bare aktive i servicemodus (skjult i drift).', 'Testpunkt på alle forsyninger, I2C, SPI, UART og CAN-signaler.'], w=184)
    return s
