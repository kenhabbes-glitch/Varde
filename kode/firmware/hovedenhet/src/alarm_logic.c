#include "alarm_logic.h"

unsigned gvt_popcount8(uint8_t v) { unsigned n = 0; while (v) { n += v & 1u; v >>= 1; } return n; }

static gvt_result_t mk(gvt_decision_t d, bool siren, uint16_t siren_s, bool img, const char *why)
{
	gvt_result_t r = { d, siren, siren_s, img, why };
	return r;
}

gvt_result_t gvt_evaluate(gvt_env_t env, const gvt_inputs_t *in)
{
	/* 1. Entydig sabotasje gir alltid alarm, også avarmert og i læremodus. */
	if (in->tamper_new) {
		return mk(DEC_ALARM, in->armed, env == ENV_BY ? 60 : 0, true, "Sabotasje");
	}
	if (!in->armed) return mk(DEC_NONE, false, 0, false, "");

	/* 2. Fysiske tegn, renset for det som rammer alle (lastebil, tog) og vær. */
	uint8_t signs = in->signs;
	if (in->neighbors_same_vibration >= 2) signs &= (uint8_t)~SIGN_VIBRATION;
	if (in->weather_damp) signs &= (uint8_t)~SIGN_VIBRATION;
	unsigned nsigns = gvt_popcount8(signs);

	bool person = in->radar_person || in->camera_person;
	if (in->weather_damp && !in->camera_person) person = false; /* radar alene stoles ikke på i uvær */
	bool confirmed = in->radar_person && in->camera_person;

	/* 3. Krav for alarm per miljøprofil */
	bool alarm = false, doubt = false;
	if (in->zone == ZONE_CORE && person) {
		switch (env) {
		case ENV_SKOG:
			alarm = confirmed || in->dwell_on_machine_s > 10 || nsigns >= 1;
			doubt = !alarm;
			break;
		case ENV_LANDLIG:
			alarm = nsigns >= 1;
			doubt = !alarm;
			break;
		case ENV_BY:
			alarm = nsigns >= 2;
			doubt = !alarm && (nsigns == 1 || in->dwell_on_machine_s > 30);
			break;
		}
	} else if (in->zone != ZONE_CORE && (signs & (SIGN_CAN_ACTIVE | SIGN_TILT_LIFT | SIGN_DOOR))) {
		/* Ingen person sett, men maskinen startes, løftes eller åpnes: tvil, bilde til anleggsleder. */
		doubt = true;
	}

	if (in->learning) {
		/* Læremodus: logger hva som ville skjedd, men alarmerer ikke. */
		return mk((alarm || doubt) ? DEC_LOG : DEC_NONE, false, 0, false, alarm ? "Læremodus: ville gitt alarm" : "Læremodus");
	}
	if (alarm) return mk(DEC_ALARM, true, env == ENV_BY ? 60 : 0, true, "Person i kjernesonen og fysiske tegn");
	if (doubt) return mk(DEC_INFO, false, 0, true, "Usikker hendelse, bilde til anleggsleder");

	/* 4. Ytre sone gir aldri alarm alene */
	if (person && in->zone == ZONE_OUTER) {
		switch (env) {
		case ENV_SKOG: return mk(DEC_INFO, false, 0, true, "Person i ytre sone");
		case ENV_LANDLIG: return in->night ? mk(DEC_INFO, false, 0, true, "Person i ytre sone om natten") : mk(DEC_LOG, false, 0, false, "Person i ytre sone");
		case ENV_BY: return mk(DEC_LOG, false, 0, false, "Person i ytre sone");
		}
	}
	return mk(DEC_NONE, false, 0, false, "");
}
