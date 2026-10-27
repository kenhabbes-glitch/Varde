/* Maskinvarelag. Hovedenheten implementerer dette mot Zephyr/nRF Connect SDK (hal_nrf.c, lages av leverandør).
 * hal_stub.c brukes på PC og i tester. */
#ifndef GVT_HAL_H
#define GVT_HAL_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "alarm_logic.h"
#include "channels.h"

int hal_init(void);
uint32_t hal_time_s(void);              /* UTC fra nettet eller GNSS */
uint32_t hal_random32(void);            /* ATECC608B eller nRF CRACEN */
uint32_t hal_counter_next(void);        /* monoton teller i ATECC608B (overlever omstart) */
int hal_sign(const uint8_t *data, size_t len, uint8_t sig[64]); /* ATECC608B slot 0 */

void hal_read_inputs(gvt_inputs_t *in); /* radar, kamera via sensorbuss, IMU, mikrofon, CAN, tamper */
void hal_read_radio(gvt_radio_t *r);
uint8_t hal_battery_pct(void);
bool hal_ext_power(void);
uint8_t hal_tamper_bits(void);

int hal_send(gvt_channel_t ch, const uint8_t *data, size_t len, uint8_t *ack, size_t *ack_len); /* 0 = sendt og kvittert */
int hal_store(const uint8_t *data, size_t len); /* kø i ekstern flash til dekning er tilbake */
void hal_siren(bool on, uint16_t seconds);
void hal_sleep_ms(uint32_t ms);
#endif
