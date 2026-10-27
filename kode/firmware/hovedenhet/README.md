# Hovedenhet – fastvareskjelett

Første versjon for leverandør. Ikke testet på maskinvare.

| Fil | Innhold |
|---|---|
| src/alarm_logic.c | Miljøprofiler (skog, landlig, by), kjernesone og ytre sone, fysiske tegn, sabotasje, læremodus, naboer og vær |
| src/heartbeat.c | Intervall per modus og batteri, jitter |
| src/channels.c | Kanalvalg LTE-M → satellitt (NTN) → LoRa via nabo → lagre, og jammingdeteksjon |
| src/geofence.c | Lagret kopi av anleggets gjerde, så enheten merker at den forlater anlegget også uten mobilnett |
| src/protocol.c | CBOR-koding, samme feltnummer som `shared/protocol.ts` |
| src/hal.h | Maskinvarelaget leverandøren implementerer mot nRF Connect SDK |
| src/hal_stub.c | Stubber for PC |
| test/test_logic.c | Tester som kjører på PC |

Kjør tester på PC (gcc eller clang):

    make -C test

Bygg for nRF9151 DK med nRF Connect SDK:

    west build -b nrf9151dk/nrf9151/ns

Det leverandøren må lage: `hal_nrf.c` (modem, GNSS, LoRa SX1262, sensorbuss CAN FD, ATECC608B), strømstyrt søvn og vekking på avbrudd, verifisering av plattformens kvittering, LoRa-mesh og gruppealarm, FOTA med MCUboot og modemoppdatering, og fastvare for nRF54L15, kamera, utvidelsesboks og brikker.
