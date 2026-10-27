/* Stubber for PC-bygg og tester. Ingen ekte maskinvare. */
#include "hal.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

static uint32_t ctr;
int hal_init(void) { return 0; }
uint32_t hal_time_s(void) { return (uint32_t)time(NULL); }
uint32_t hal_random32(void) { static uint32_t x = 2463534242u; x ^= x << 13; x ^= x >> 17; x ^= x << 5; return x; }
uint32_t hal_counter_next(void) { return ++ctr; }
int hal_sign(const uint8_t *data, size_t len, uint8_t sig[64]) { (void)data; (void)len; memset(sig, 0xA5, 64); return 0; } /* IKKE en ekte signatur */
void hal_read_inputs(gvt_inputs_t *in) { memset(in, 0, sizeof *in); in->armed = true; }
void hal_read_radio(gvt_radio_t *r) { memset(r, 0, sizeof *r); r->lte_registered = true; r->rsrp_dbm = -95; r->rsrp_learned_dbm = -95; r->lora_neighbors = 3; }
uint8_t hal_battery_pct(void) { return 96; }
bool hal_ext_power(void) { return true; }
uint8_t hal_tamper_bits(void) { return 0; }
int hal_send(gvt_channel_t ch, const uint8_t *d, size_t n, uint8_t *ack, size_t *al) { (void)d; (void)ack; *al = 0; printf("[stub] sender %zu byte på kanal %d\n", n, ch); return 0; }
int hal_store(const uint8_t *d, size_t n) { (void)d; printf("[stub] lagrer %zu byte\n", n); return 0; }
void hal_siren(bool on, uint16_t s) { printf("[stub] sirene %s %u s\n", on ? "på" : "av", s); }
void hal_sleep_ms(uint32_t ms) { (void)ms; }
