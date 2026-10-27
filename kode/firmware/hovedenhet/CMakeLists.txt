# Bygg med nRF Connect SDK (Zephyr), f.eks.:
#   west build -b nrf9151dk/nrf9151/ns
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(gvt_hovedenhet)

target_sources(app PRIVATE
  src/main.c
  src/alarm_logic.c
  src/heartbeat.c
  src/channels.c
  src/protocol.c
  src/geofence.c
  # src/hal_nrf.c   # lages av leverandør: modem, GNSS, LoRa, sensorbuss, ATECC608B
  src/hal_stub.c    # midlertidig, fjernes når hal_nrf.c finnes
)
