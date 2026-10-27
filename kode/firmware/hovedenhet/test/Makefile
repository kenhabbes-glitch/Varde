CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O1 -g
SRC = ../src/alarm_logic.c ../src/heartbeat.c ../src/channels.c ../src/protocol.c ../src/geofence.c

all: test_logic host_main
	./test_logic

test_logic: test_logic.c $(SRC)
	$(CC) $(CFLAGS) -o $@ test_logic.c $(SRC) -lm

# Hele hovedløkken bygget mot stubber, én runde
host_main: ../src/main.c ../src/hal_stub.c $(SRC)
	$(CC) $(CFLAGS) -DGVT_HOST_ONCE -o $@ ../src/main.c ../src/hal_stub.c $(SRC) -lm
	./host_main

fixture: test_logic
	./test_logic --hex > ../../../test/fixtures/fw_alarm.hex

clean:
	rm -f test_logic host_main
