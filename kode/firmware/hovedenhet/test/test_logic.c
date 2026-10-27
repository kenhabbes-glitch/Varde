/* Tester for alarmlogikk, heartbeat, kanalvalg og meldingskoding. Kjør: make -C test */
#include <stdio.h>
#include <string.h>
#include "../src/alarm_logic.h"
#include "../src/heartbeat.h"
#include "../src/channels.h"
#include "../src/protocol.h"
#include "../src/geofence.h"

static int fails, runs;
#define CHECK(c) do { runs++; if (!(c)) { fails++; printf("FEIL %s:%d: %s\n", __FILE__, __LINE__, #c); } } while (0)

static gvt_inputs_t person_core(void) { gvt_inputs_t i = { 0 }; i.armed = true; i.zone = ZONE_CORE; i.radar_person = true; return i; }

static void test_profiles(void)
{
	gvt_inputs_t i = person_core();
	/* Person i kjernesonen uten fysiske tegn */
	CHECK(gvt_evaluate(ENV_SKOG, &i).decision == DEC_INFO);
	CHECK(gvt_evaluate(ENV_LANDLIG, &i).decision == DEC_INFO);
	CHECK(gvt_evaluate(ENV_BY, &i).decision == DEC_NONE);
	/* Radar og kamera bekrefter: alarm i skog */
	i.camera_person = true;
	CHECK(gvt_evaluate(ENV_SKOG, &i).decision == DEC_ALARM);
	CHECK(gvt_evaluate(ENV_LANDLIG, &i).decision == DEC_INFO);
	/* Ett fysisk tegn */
	i.signs = SIGN_DOOR;
	CHECK(gvt_evaluate(ENV_LANDLIG, &i).decision == DEC_ALARM);
	CHECK(gvt_evaluate(ENV_BY, &i).decision == DEC_INFO);
	/* To fysiske tegn: alarm også i by, med begrenset sirene */
	i.signs = SIGN_DOOR | SIGN_TOOL_SOUND;
	gvt_result_t r = gvt_evaluate(ENV_BY, &i);
	CHECK(r.decision == DEC_ALARM && r.siren && r.siren_s == 60);
}

static void test_outer_zone(void)
{
	gvt_inputs_t i = person_core(); i.zone = ZONE_OUTER;
	CHECK(gvt_evaluate(ENV_SKOG, &i).decision == DEC_INFO);
	CHECK(gvt_evaluate(ENV_LANDLIG, &i).decision == DEC_LOG);
	i.night = true;
	CHECK(gvt_evaluate(ENV_LANDLIG, &i).decision == DEC_INFO);
	CHECK(gvt_evaluate(ENV_BY, &i).decision == DEC_LOG);
	/* Ytre sone gir aldri alarm, uansett sensorer */
	i.camera_person = true; i.signs = SIGN_VIBRATION | SIGN_TOOL_SOUND;
	CHECK(gvt_evaluate(ENV_SKOG, &i).decision != DEC_ALARM);
}

static void test_sabotage_always(void)
{
	gvt_inputs_t i = { 0 }; i.tamper_new = TAMPER_GPS_LOOP;
	for (int e = 0; e < 3; e++) CHECK(gvt_evaluate((gvt_env_t)e, &i).decision == DEC_ALARM);
	i.learning = true; CHECK(gvt_evaluate(ENV_BY, &i).decision == DEC_ALARM);
	i.armed = false; CHECK(gvt_evaluate(ENV_BY, &i).decision == DEC_ALARM); /* også avarmert, men uten sirene */
	CHECK(!gvt_evaluate(ENV_BY, &i).siren);
}

static void test_group_and_weather(void)
{
	gvt_inputs_t i = person_core(); i.signs = SIGN_VIBRATION;
	CHECK(gvt_evaluate(ENV_LANDLIG, &i).decision == DEC_ALARM);
	i.neighbors_same_vibration = 3; /* lastebil eller tog: alle kjenner det */
	CHECK(gvt_evaluate(ENV_LANDLIG, &i).decision == DEC_INFO);
	i.neighbors_same_vibration = 0; i.weather_damp = true; /* storm, radar alene stoles ikke på */
	CHECK(gvt_evaluate(ENV_LANDLIG, &i).decision == DEC_NONE);
}

static void test_learning_and_disarmed(void)
{
	gvt_inputs_t i = person_core(); i.camera_person = true; i.signs = SIGN_DOOR | SIGN_CAN_ACTIVE;
	i.learning = true; CHECK(gvt_evaluate(ENV_SKOG, &i).decision == DEC_LOG);
	i.learning = false; i.armed = false; CHECK(gvt_evaluate(ENV_SKOG, &i).decision == DEC_NONE);
}

static void test_heartbeat(void)
{
	gvt_hb_state_t s = { HB_ARMED, true, 90, 0, 0, 0 };
	CHECK(gvt_hb_interval(&s) == 120);
	s.ext_power = false; CHECK(gvt_hb_interval(&s) == 300);
	s.battery_pct = 10; CHECK(gvt_hb_interval(&s) == 600);
	s.mode = HB_ALARM; s.platform_override_s = 900; CHECK(gvt_hb_interval(&s) == 15);
	for (uint32_t r = 0; r < 1000; r += 7) { uint32_t n = gvt_hb_next_ms(120, r * 2654435761u); CHECK(n <= 120000 && n > 108000); }

	/* Modus følger alarmlogikken, ikke bare armering */
	gvt_hb_state_t m = { HB_ARMED, true, 90, 0, 0, 0 };
	CHECK(!gvt_hb_update_mode(&m, true, DEC_NONE, 1000) && m.mode == HB_ARMED);
	CHECK(gvt_hb_update_mode(&m, false, DEC_NONE, 1000) && m.mode == HB_DISARMED);
	CHECK(gvt_hb_update_mode(&m, true, DEC_INFO, 1000) && m.mode == HB_SUSPICIOUS && gvt_hb_interval(&m) == 30);
	CHECK(gvt_hb_update_mode(&m, true, DEC_ALARM, 1000) && m.mode == HB_ALARM && gvt_hb_interval(&m) == 15);
	CHECK(!gvt_hb_update_mode(&m, true, DEC_NONE, 1000) && m.mode == HB_ALARM);          /* holder etter én alarm */
	CHECK(!gvt_hb_update_mode(&m, true, DEC_INFO, 1000) && m.mode == HB_ALARM);          /* alarm går foran mistenkelig */
	CHECK(gvt_hb_update_mode(&m, true, DEC_NONE, GVT_HB_ALARM_HOLD_MS) && m.mode == HB_ARMED); /* holdetiden er ute */
	CHECK(gvt_hb_update_mode(&m, false, DEC_ALARM, 1000) && m.mode == HB_ALARM);         /* sabotasje gir alarm også avarmert */
	CHECK(gvt_hb_update_mode(&m, false, DEC_NONE, GVT_HB_ALARM_HOLD_MS) && m.mode == HB_DISARMED);
}

static void test_channels(void)
{
	gvt_radio_t r = { true, -95, -95, false, true, 2, false, false };
	CHECK(gvt_choose_channel(&r, false) == CH_LTE);
	r.lte_registered = false;
	CHECK(gvt_choose_channel(&r, false) == CH_LORA);
	CHECK(gvt_choose_channel(&r, true) == CH_NTN);
	r.ntn_available = false; r.lora_neighbors = 0;
	CHECK(gvt_choose_channel(&r, true) == CH_STORE);
	/* Jamming: stabil dekning som faller bort samtidig med støy */
	r.lte_noise_high = true; CHECK(gvt_jamming_suspected(&r));
	/* Dårlig dekning som er normal for stedet er ikke jamming */
	r.rsrp_learned_dbm = -120; CHECK(!gvt_jamming_suspected(&r));
	r.gnss_jam = true; CHECK(gvt_jamming_suspected(&r));
}

static int fake_sign(const uint8_t *d, size_t n, uint8_t sig[64]) { (void)d; (void)n; for (int k = 0; k < 64; k++) sig[k] = (uint8_t)k; return 0; }

static gvt_msg_t sample(void)
{
	gvt_msg_t m = { 0 };
	m.id = "GVT-0001A"; m.ctr = 4242; m.ts = 1761300000; m.type = "alarm"; m.iv = 120;
	m.bat = 87; m.ext = true; m.tamper = TAMPER_LID | TAMPER_GPS_LOOP; m.armed = true;
	m.ch = "LTE-M"; m.rsrp = -101; m.noise = false; m.gnss_jam = false;
	m.ev_code = "TA"; m.ev_zone = 2; m.ev_text = "Lokk åpnet"; m.ev_img = true;
	return m;
}

static void test_protocol(void)
{
	uint8_t b[256];
	gvt_msg_t m = sample();
	size_t n = gvt_encode_payload(&m, b, sizeof b);
	CHECK(n > 0 && n < 120);
	CHECK(b[0] == 0xa9); /* kart med 9 felt */
	CHECK(gvt_encode_payload(&m, b, 10) == 0); /* for liten buffer gir feil, ikke overskriving */
	uint8_t e[512]; size_t en = gvt_seal(&m, fake_sign, e, sizeof e);
	CHECK(en == 1 /* liste */ + (n < 24 ? 1 : 2) /* bytes-hode */ + n + 2 /* sig-hode */ + 64);
}

static void test_geofence(void)
{
	/* Kvadrat på ±150 m rundt 59,95 N / 10,60 Ø */
	int32_t lat0 = 599500000, lon0 = 106000000, dl = 13474, dn = 26952; /* ca. 150 m i grader × 1e7 */
	gvt_fence_t f = { .n = 4, .buffer_m = 25 };
	f.pts[0] = (gvt_pt_t){ lat0 - dl, lon0 - dn }; f.pts[1] = (gvt_pt_t){ lat0 - dl, lon0 + dn };
	f.pts[2] = (gvt_pt_t){ lat0 + dl, lon0 + dn }; f.pts[3] = (gvt_pt_t){ lat0 + dl, lon0 - dn };
	float d0 = gvt_fence_distance(&f, lat0, lon0);
	CHECK(d0 < -140.0f && d0 > -160.0f);
	CHECK(!gvt_fence_outside(&f, lat0, lon0, 5));
	CHECK(!gvt_fence_outside(&f, lat0 + 14370, lon0, 5));  /* ca. 160 m nord: innenfor bufferen */
	CHECK(gvt_fence_outside(&f, lat0 + 35930, lon0, 5));   /* ca. 400 m nord: ute */
	CHECK(!gvt_fence_outside(&f, lat0 + 17960, lon0, 40)); /* ca. 200 m, men unøyaktig: ikke sikkert ute */
	/* posisjon i meldingen */
	gvt_msg_t m = sample(); uint8_t b[256];
	size_t n0 = gvt_encode_payload(&m, b, sizeof b);
	m.has_pos = true; m.lat_e7 = lat0; m.lon_e7 = lon0; m.acc_m = 5;
	size_t n1 = gvt_encode_payload(&m, b, sizeof b);
	CHECK(n1 == n0 + 1 + 1 + 5 + 5 + 1); /* nøkkel, liste, to int32, acc */
	CHECK(b[0] == 0xaa); /* kart med 10 felt */
}

int main(int argc, char **argv)
{
	if (argc > 1 && strcmp(argv[1], "--hex") == 0) {
		/* Skriver eksempelmelding som hex, slik at TypeScript-testen kan kontrollere at begge sider er like. */
		uint8_t e[512]; gvt_msg_t m = sample(); size_t n = gvt_seal(&m, fake_sign, e, sizeof e);
		for (size_t k = 0; k < n; k++) printf("%02x", e[k]);
		printf("\n"); return 0;
	}
	test_profiles(); test_outer_zone(); test_sabotage_always(); test_group_and_weather();
	test_learning_and_disarmed(); test_heartbeat(); test_channels(); test_protocol(); test_geofence();
	printf("%d av %d kontroller bestått\n", runs - fails, runs);
	return fails ? 1 : 0;
}
