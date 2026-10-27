/* GPS Vs Tyv – hovedenhet, fastvareskjelett (første versjon).
 * Hovedløkke: les sensorer -> vurder etter miljøprofil -> send alarm eller heartbeat på beste kanal.
 * Ikke testet på maskinvare. Strømsparing (hendelsesstyrt søvn), FOTA, LoRa-mesh og sensorbuss
 * implementeres av leverandøren etter designdokumentet. */
#include "alarm_logic.h"
#include "channels.h"
#include "heartbeat.h"
#include "protocol.h"
#include "hal.h"

#ifndef GVT_DEVICE_ID
#define GVT_DEVICE_ID "GVT-0001A" /* skrives inn ved produksjon */
#endif

static gvt_env_t env = ENV_LANDLIG;   /* settes fra plattformen ved oppsett */
static uint8_t tamper_seen;
static const char *ch_name[] = { "LTE-M", "NTN", "LoRa", "lokal" };

static void transmit(gvt_msg_t *m, bool is_alarm)
{
	gvt_radio_t r; hal_read_radio(&r);
	gvt_channel_t ch = gvt_choose_channel(&r, is_alarm);
	m->ch = ch_name[ch]; m->rsrp = r.rsrp_dbm; m->noise = gvt_jamming_suspected(&r); m->gnss_jam = r.gnss_jam;
	uint8_t buf[640], ack[128]; size_t al = sizeof ack;
	size_t n = gvt_seal(m, hal_sign, buf, sizeof buf);
	if (!n) return;
	if (ch == CH_STORE || hal_send(ch, buf, n, ack, &al) != 0) hal_store(buf, n);
	/* TODO leverandør: verifiser kvittering med plattformens offentlige nøkkel og hent nytt intervall. */
}

static gvt_msg_t base(const char *type, uint16_t iv, bool armed)
{
	gvt_msg_t m = { 0 };
	m.id = GVT_DEVICE_ID; m.ctr = hal_counter_next(); m.ts = hal_time_s(); m.type = type; m.iv = iv;
	m.bat = hal_battery_pct(); m.ext = hal_ext_power(); m.tamper = hal_tamper_bits(); m.armed = armed;
	return m;
}

int main(void)
{
	hal_init();
	gvt_hb_state_t hb = { .mode = HB_ARMED };
	uint32_t until_hb_ms = 0, elapsed_ms = 0;
	for (;;) {
		gvt_inputs_t in; hal_read_inputs(&in);
		uint8_t t = hal_tamper_bits();
		in.tamper_new = t & (uint8_t)~tamper_seen; tamper_seen = t;
		hb.ext_power = hal_ext_power(); hb.battery_pct = hal_battery_pct();

		gvt_result_t res = gvt_evaluate(env, &in);
		/* Modus følger beslutningen (alarm > mistenkelig > armert/avarmert), med holdetid. */
		bool changed = gvt_hb_update_mode(&hb, in.armed, res.decision, elapsed_ms);
		uint16_t iv = gvt_hb_interval(&hb);
		/* Tettere oppfølging skal gjelde med en gang, ikke først etter det gamle intervallet. */
		if (changed && until_hb_ms > (uint32_t)iv * 1000u) until_hb_ms = gvt_hb_next_ms(iv, hal_random32());
		if (res.decision == DEC_ALARM || res.decision == DEC_INFO) {
			gvt_msg_t m = base(res.decision == DEC_ALARM ? "alarm" : "info", iv, in.armed);
			m.ev_code = in.tamper_new ? "TA" : (res.decision == DEC_ALARM ? "BA" : "OP");
			m.ev_zone = (uint8_t)in.zone; m.ev_text = res.reason; m.ev_img = res.send_image;
			transmit(&m, res.decision == DEC_ALARM);
			if (res.siren) hal_siren(true, res.siren_s);
		}
		if (until_hb_ms == 0) {
			gvt_msg_t m = base("hb", iv, in.armed);
			transmit(&m, false);
			until_hb_ms = gvt_hb_next_ms(iv, hal_random32());
		}
		/* I drift: sov til neste heartbeat eller til en sensor vekker enheten (avbrudd). */
		uint32_t step = until_hb_ms < 1000 ? until_hb_ms : 1000;
		hal_sleep_ms(step); until_hb_ms -= step; elapsed_ms = step;
#ifdef GVT_HOST_ONCE
		break;
#endif
	}
	return 0;
}
