/* Heartbeat-intervall og jitter (kapittel om mottakssentral og heartbeat). */
#ifndef GVT_HEARTBEAT_H
#define GVT_HEARTBEAT_H
#include <stdbool.h>
#include <stdint.h>
#include "alarm_logic.h"

typedef enum { HB_ARMED = 0, HB_DISARMED = 1, HB_SUSPICIOUS = 2, HB_ALARM = 3 } gvt_hb_mode_t;

typedef struct {
	gvt_hb_mode_t mode;
	bool ext_power;       /* maskinens batteri tilkoplet */
	uint8_t battery_pct;  /* reservebatteri */
	uint16_t platform_override_s; /* 0 = ingen, ellers intervall plattformen har bedt om i kvitteringen */
	uint32_t alarm_left_ms;  /* holdetid for alarmmodus etter siste alarmbeslutning */
	uint32_t susp_left_ms;   /* holdetid for mistenkelig-modus etter siste info-beslutning */
} gvt_hb_state_t;

#define GVT_HB_ALARM_HOLD_MS 600000u /* 10 min med tett heartbeat etter siste alarm */
#define GVT_HB_SUSP_HOLD_MS  120000u /* 2 min etter siste mistenkelige hendelse */

/* Setter modus ut fra armering og siste beslutning fra alarmlogikken.
 * Alarm går foran mistenkelig, som går foran armert/avarmert. Holdetiden telles ned med elapsed_ms,
 * slik at modusen ikke faller tilbake i neste runde selv om beslutningen bare kom én gang.
 * Returnerer true når modusen endret seg (da bør neste heartbeat planlegges på nytt). */
bool gvt_hb_update_mode(gvt_hb_state_t *s, bool armed, gvt_decision_t decision, uint32_t elapsed_ms);

uint16_t gvt_hb_interval(const gvt_hb_state_t *s);
/* Neste sendetid: intervall minus 0–10 % tilfeldig, slik at enhetene ikke sender samtidig og aldri for sent. */
uint32_t gvt_hb_next_ms(uint16_t interval_s, uint32_t random32);

#endif
