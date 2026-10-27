#include "heartbeat.h"

uint16_t gvt_hb_interval(const gvt_hb_state_t *s)
{
	uint16_t iv;
	switch (s->mode) {
	case HB_ALARM: iv = 15; break;      /* tett oppfølging under alarm */
	case HB_SUSPICIOUS: iv = 30; break;
	case HB_DISARMED: iv = 900; break;  /* i arbeidstid holder det med sjeldne livstegn */
	case HB_ARMED: default: iv = 120; break;
	}
	/* På reservebatteri: spar strøm, men aldri lenger enn 10 min når armert. */
	if (!s->ext_power && s->mode == HB_ARMED) iv = s->battery_pct < 20 ? 600 : 300;
	if (s->platform_override_s >= 15 && s->platform_override_s <= 3600 && s->mode != HB_ALARM) iv = s->platform_override_s;
	return iv;
}

uint32_t gvt_hb_next_ms(uint16_t interval_s, uint32_t random32)
{
	uint32_t full = (uint32_t)interval_s * 1000u;
	uint32_t jitter = full / 10u;
	return full - (jitter ? random32 % jitter : 0);
}

static uint32_t count_down(uint32_t left, uint32_t elapsed) { return left > elapsed ? left - elapsed : 0; }

bool gvt_hb_update_mode(gvt_hb_state_t *s, bool armed, gvt_decision_t decision, uint32_t elapsed_ms)
{
	gvt_hb_mode_t before = s->mode;
	s->alarm_left_ms = count_down(s->alarm_left_ms, elapsed_ms);
	s->susp_left_ms = count_down(s->susp_left_ms, elapsed_ms);
	if (decision == DEC_ALARM) s->alarm_left_ms = GVT_HB_ALARM_HOLD_MS;
	else if (decision == DEC_INFO) s->susp_left_ms = GVT_HB_SUSP_HOLD_MS;
	if (s->alarm_left_ms) s->mode = HB_ALARM;
	else if (s->susp_left_ms) s->mode = HB_SUSPICIOUS;
	else s->mode = armed ? HB_ARMED : HB_DISARMED;
	return s->mode != before;
}
