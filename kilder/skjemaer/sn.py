from lib import Sheet, NOTE, NET
from common import buck, swd, m12, atecc

def sheet_node(B):
    s = Sheet(B, 'Sensornode (mal for dør-, radar-, sirene- og NFC-noder)')
    # ---------- A M12 inn/ut ----------
    s.block(14, 16, 150, 112, 'A  M12 inn og ut (gjennomgående buss)')
    Ji = m12(s, 24, 30, s.b.ref('J'), 'M12 hann (inn)', side='r')
    Jo = m12(s, 130, 30, s.b.ref('J'), 'M12 hunn (ut)', side='l')
    for nm in ['V+', 'GND', 'CAN_H', 'CAN_L', 'SHLD']:
        a, b = Ji[nm][:2], Jo[nm][:2]
        s.wire(a, b)
    for nm, net in [('V+', 'VBUS'), ('GND', 'GND'), ('CAN_H', 'BUS_CANH'), ('CAN_L', 'BUS_CANL'), ('SHLD', 'SHLD')]:
        a = Ji[nm][:2]; mx = (a[0] + Jo[nm][0]) / 2
        s.wname((mx, a[1]), net, '#b3261e' if net == 'VBUS' else ('#1a1a1a' if net == 'GND' else None))
    s.note(22, 106, ['V+, GND, CAN og skjerm går rett gjennom, så noder kan', 'kjedes. Siste node får termineringsplugg på utgangen.', 'Forsyningen tas ut via diode og TVS (ikke vist) til VBUS.'], w=136)

    # ---------- B buck ----------
    buck(s, 170, 16, vin='VBUS', out='3V3', rtop='100 kΩ 1 %', rbot='57,6 kΩ 1 %', ind='47 µH*', title='B  Buck 9–36 V → 3,3 V', w=176, h=112, note='Lett last (2–10 mW): LM5164 i PFM gir lav hvilestrøm.')

    # ---------- C MCU ----------
    s.block(14, 134, 236, 122, 'C  STM32G0B1 med CAN FD og sikkerhetsbrikke')
    left = ['VDD', 'VDDA', None, 'NRST', 'PA13-SWDIO', 'PA14-SWCLK', None, 'VSS']
    right = ['FDCAN1_TX', 'FDCAN1_RX', 'GPIO#stb', None, 'I2C1_SDA', 'I2C1_SCL', None, 'SPI1_SCK', 'SPI1_MOSI', 'SPI1_MISO', 'SPI1_NSS', None, 'ADC_IN0', 'GPIO#1', 'GPIO#2', 'GPIO#lid', 'GPIO#led']
    M = s.ic(86, 144, 34, s.b.ref('U'), 'STM32G0B1KET6', left=left, right=right, pitch=4.5, desc='STM32G0B1, Cortex-M0+, FDCAN')
    s.label(M['VDD'][:2], '3V3', 'l', 3); s.label(M['VDDA'][:2], '3V3', 'l', 3)
    s.text(M['VDD'][0] - 3, M['VDD'][1] - 2, '100 nF + 4,7 µF', 1.5, 'end', NOTE)
    s.label(M['NRST'][:2], 'SN_RESET', 'l', 3); s.label(M['PA13-SWDIO'][:2], 'SN_SWDIO', 'l', 3); s.label(M['PA14-SWCLK'][:2], 'SN_SWDCLK', 'l', 3)
    s.pl(M, 'VSS', '', 3, 'gnd')
    for nm, net in [('FDCAN1_TX', 'CAN_TXD'), ('FDCAN1_RX', 'CAN_RXD'), ('GPIO#stb', 'CAN_STB'), ('I2C1_SDA', 'I2C_SDA'), ('I2C1_SCL', 'I2C_SCL'),
                    ('SPI1_SCK', 'S_SCK'), ('SPI1_MOSI', 'S_MOSI'), ('SPI1_MISO', 'S_MISO'), ('SPI1_NSS', 'S_CS'), ('ADC_IN0', 'S_AIN'),
                    ('GPIO#1', 'S_GPIO1'), ('GPIO#2', 'S_GPIO2'), ('GPIO#lid', 'LID_SW'), ('GPIO#led', 'LED')]:
        s.label(M[nm][:2], net, 'r', 3)
    atecc(s, 190, 150, '3V3')
    s.label((30, 244), 'LED', 'l', 0); r = s.R((30, 244), 'h', '1 kΩ', L=10); d = s.D(r[1], 'h', 'Service', L=10, kind='led'); s.wire(d[1], (d[1][0] + 2, 244)); s.gnd((d[1][0] + 2, 244))
    s.pwr((96, 236), '3V3', 'u'); r = s.R((96, 236), 'v', '1 MΩ', L=8, side='l'); s.wire(r[1], (96, 246)); s.dot((96, 246)); sw_ = s.SW((96, 246), 'h', 'Lokk (NC)', L=10, desc='Lokkbryter'); s.wire(sw_[1], (sw_[1][0] + 2, 246)); s.gnd((sw_[1][0] + 2, 246))
    s.label((96, 246), 'LID_SW', 'l', 3)
    swd(s, 190, 194, 'SN_')

    # ---------- D transceiver og sensor ----------
    s.block(256, 134, 154, 122, 'D  Transceiver, terminering og sensorkontakt')
    T = s.ic(292, 144, 24, s.b.ref('U'), 'TCAN3413', left=['TXD', 'RXD', 'STB', 'VIO'], right=['VCC', 'CANH', 'CANL', 'GND'], pitch=5, desc='CAN FD-transceiver 3,3 V')
    s.label(T['TXD'][:2], 'CAN_TXD', 'l', 3); s.label(T['RXD'][:2], 'CAN_RXD', 'l', 3); s.label(T['STB'][:2], 'CAN_STB', 'l', 3); s.label(T['VIO'][:2], '3V3', 'l', 3)
    s.label(T['VCC'][:2], '3V3', 'r', 3); s.label(T['CANH'][:2], 'BUS_CANH', 'r', 3); s.label(T['CANL'][:2], 'BUS_CANL', 'r', 3); s.pl(T, 'GND', '', 3, 'gnd')
    J = s.conn(292, 186, s.b.ref('J'), 'Sensorkontakt 12-pin', [(1, '3V3'), (2, 'GND'), (3, 'SDA'), (4, 'SCL'), (5, 'SCK'), (6, 'MOSI'), (7, 'MISO'), (8, 'CS'), (9, 'AIN'), (10, 'GPIO1'), (11, 'GPIO2'), (12, 'VBUS')], side='l', pitch=4.5, desc='Kontakt for sensorkort (avhenger av node)')
    for nm, net in [('SDA', 'I2C_SDA'), ('SCL', 'I2C_SCL'), ('SCK', 'S_SCK'), ('MOSI', 'S_MOSI'), ('MISO', 'S_MISO'), ('CS', 'S_CS'), ('AIN', 'S_AIN'), ('GPIO1', 'S_GPIO1'), ('GPIO2', 'S_GPIO2'), ('VBUS', 'VBUS')]:
        s.label(J[nm][:2], net, 'l', 3)
    s.pwr(J['3V3'][:2], '3V3', 'l'); s.pl(J, 'GND', '', 3, 'gnd')
    s.note(324, 192, ['Eksempler på sensorkort:', 'Dør: magnetkontakt + LIS2DW12', 'Radar: Acconeer A121', 'Sirene: driver fra VBUS', 'NFC: PN7160-leser', 'Miljø: SHT40 + lekkasje', '', 'Lokkbryter til LID_SW.', 'Terminering 2 × 60,4 Ω', 'via jumper (ikke vist).'], w=82)
    return s
