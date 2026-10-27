from lib import NOTE, NET

def buck(s, ox, oy, vin='VIN_PROT', out='3V3', rtop='100 kΩ 1 %', rbot='57,6 kΩ 1 %', ind='33 µH*', cout='2 × 22 µF 10 V', ref=None, w=174, title=None, note=None, h=78):
    """LM5164 buck 9–36 V inn. Tegnes innenfor ca. 150 × 70 mm fra (ox, oy)."""
    if title: s.block(ox, oy, w, h, title)
    yv = oy + 21
    s.label((ox + 12, yv), vin, 'l', 0)
    U = s.ic(ox + 80, oy + 16, 28, ref or s.b.ref('U'), 'LM5164', left=['VIN', None, 'EN/UVLO', 'RON', 'SS'], right=['BST', 'SW', 'FB', 'GND'], pitch=5, desc='Buck 100 V 1 A')
    s.wire((ox + 12, yv), U['VIN'][:2])
    s.dot((ox + 18, yv)); c = s.C((ox + 18, yv), 'v', '2 × 2,2 µF 100 V', L=10, desc='X7R 100 V, 2 stk'); s.gnd(c[1])
    en = U['EN/UVLO'][:2]; ex = ox + 48
    s.dot((ex, yv)); r = s.R((ex, yv), 'v', '1 MΩ', L=8); s.wire(r[1], (ex, en[1]), en); s.dot((ex, en[1]))
    r = s.R((ex, en[1]), 'v', '127 kΩ*', L=10); s.gnd(r[1])
    ron = U['RON'][:2]; rx = ox + 60; s.wire(ron, (rx, ron[1])); s.dot((rx, ron[1])); r = s.R((rx, ron[1]), 'v', '100 kΩ*', L=10); s.gnd(r[1])
    ss = U['SS'][:2]; sx_ = ox + 71; s.wire(ss, (sx_, ss[1])); s.dot((sx_, ss[1])); c = s.C((sx_, ss[1]), 'v', '22 nF', L=8); s.gnd(c[1])
    s.pl(U, 'GND', '', 2, 'gnd')
    bx, by, _ = U['BST']; swx, swy, _ = U['SW']
    s.wire((bx, by), (bx + 4, by)); s.C((bx + 4, by), 'v', '2,2 nF', L=5); s.dot((bx + 4, swy))
    la, lb = s.Lind((bx + 8, swy), 'h', ind, L=14); s.wire((swx, swy), la)
    o = (lb[0] + 26, swy); s.wire(lb, o)
    s.dot((lb[0] + 6, swy)); c = s.C((lb[0] + 6, swy), 'v', cout, L=10, desc='X7R'); s.gnd(c[1])
    s.pwr(o, out, 'u')
    r5 = s.R(o, 'v', rtop, L=10); fy = oy + 48
    s.wire(r5[1], (o[0], fy)); s.dot((o[0], fy))
    s.wire((o[0], fy), (U['FB'][0] + 6, fy), (U['FB'][0] + 6, U['FB'][1]), U['FB'][:2])
    r6 = s.R((o[0], fy), 'v', rbot, L=10); s.gnd(r6[1])
    if note: s.note(ox + 8, oy + h - 8, note if isinstance(note, list) else [note], w=w - 14)
    return U

def can_fd(s, ox, oy, pre='CAN', title='Sensorbuss CAN FD', vcc='5V', w=196, xtal='40 MHz', spi=('SPI_SCK', 'SPI_MOSI', 'SPI_MISO', 'CAN_CS', 'CAN_INT'), bus=('BUS_CANH', 'BUS_CANL'), stb='CAN_STB', xcvr='TCAN1462'):
    """MCP2518FD + TCAN1462 med SPI."""
    s.block(ox, oy, w, 84, title)
    M = s.ic(ox + 32, oy + 14, 28, s.b.ref('U'), 'MCP2518FD', left=['SCK', 'SDI', 'SDO', 'nCS', 'nINT'], right=['VDD', 'OSC1', 'OSC2', 'TXCAN', 'RXCAN', 'VSS'], pitch=5, desc='CAN FD-kontroller, SPI')
    for nm, net in zip(['SCK', 'SDI', 'SDO', 'nCS', 'nINT'], spi): s.label(M[nm][:2], net, 'l', 3)
    vx, vy = M['VDD'][:2]; s.wire((vx, vy), (vx + 22, vy)); s.pwr((vx + 22, vy), '3V3', 'u')
    s.text(vx + 3, vy - 1.4, '100 nF', 1.5, 'start', NOTE)
    o1, o2 = M['OSC1'][:2], M['OSC2'][:2]; xx = o1[0] + 8
    s.wire(o1, (xx, o1[1])); s.wire(o2, (xx, o2[1])); s.X((xx, o1[1]), 'v', '', L=5, desc=f'Krystall {xtal}')
    T = s.ic(ox + 120, oy + 30, 26, s.b.ref('U'), xcvr, left=['TXD', 'RXD', 'STB', 'VIO'], right=['VCC', 'CANH', 'CANL', 'GND'], pitch=5, desc=f'CAN FD-transceiver {xcvr}')
    tx, rx = M['TXCAN'][:2], M['RXCAN'][:2]
    s.wire(tx, (tx[0] + 10, tx[1]), (tx[0] + 10, T['TXD'][1]), T['TXD'][:2])
    s.wire(rx, (rx[0] + 6, rx[1]), (rx[0] + 6, T['RXD'][1]), T['RXD'][:2])
    s.pl(M, 'VSS', '', 3, 'gnd')
    s.label(T['STB'][:2], stb, 'l', 3); s.label(T['VIO'][:2], '3V3', 'l', 3)
    s.label(T['VCC'][:2], vcc, 'r', 3); s.label(T['CANH'][:2], bus[0], 'r', 3); s.label(T['CANL'][:2], bus[1], 'r', 3)
    s.pl(T, 'GND', '', 3, 'gnd')
    return M, T

def atecc(s, x, y, vcc='3V3', sda='I2C_SDA', scl='I2C_SCL'):
    A = s.ic(x, y, 24, s.b.ref('U'), 'ATECC608B', left=['VCC'], right=['SDA', 'SCL', 'GND'], pitch=5, desc='Sikkerhetsbrikke ECDSA P-256')
    s.label(A['VCC'][:2], vcc, 'l', 3); s.label(A['SDA'][:2], sda, 'r', 3); s.label(A['SCL'][:2], scl, 'r', 3); s.pl(A, 'GND', '', 3, 'gnd')
    return A

def m12(s, x, y, ref, title='M12 A-kodet 5-pin', side='l', names=('SHLD', 'V+', 'GND', 'CAN_H', 'CAN_L'), desc='M12 A-kodet 5-pin (CiA 303-1)'):
    return s.conn(x, y, ref, title, list(zip(range(1, 6), names)), side=side, pitch=5, desc=desc)

def swd(s, x, y, prefix, vref='3V3', ref=None):
    J = s.conn(x, y, ref or s.b.ref('J'), 'TC2030-IDC-NL', [(1, 'VREF'), (2, 'SWDIO'), (3, 'RESET'), (4, 'SWDCLK'), (5, 'GND'), (6, 'NC')], pitch=4.5, desc='Testpunkt for SWD, ingen komponent')
    s.pwr(J['VREF'][:2], vref, 'r')
    for nm in ['SWDIO', 'RESET', 'SWDCLK']: s.label(J[nm][:2], f'{prefix}{nm}', 'r', 3)
    s.pl(J, 'GND', '', 3, 'gnd'); s.pl(J, 'NC', '', kind='nc')
    return J
