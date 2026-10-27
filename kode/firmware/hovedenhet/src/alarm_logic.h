/* Alarmlogikk med miljøprofiler (kapittel 8 i designdokumentet).
 * Ren C uten avhengigheter, slik at den kan testes på PC. */
#ifndef GVT_ALARM_LOGIC_H
#define GVT_ALARM_LOGIC_H
#include <stdbool.h>
#include <stdint.h>

typedef enum { ENV_SKOG = 0, ENV_LANDLIG = 1, ENV_BY = 2 } gvt_env_t;
typedef enum { ZONE_NONE = 0, ZONE_OUTER = 1, ZONE_CORE = 2 } gvt_zone_t;
typedef enum { DEC_NONE = 0, DEC_LOG = 1, DEC_INFO = 2, DEC_ALARM = 3 } gvt_decision_t;

/* Fysiske tegn: noen gjør noe med maskinen */
enum {
	SIGN_VIBRATION = 1u << 0, /* IMU */
	SIGN_TOOL_SOUND = 1u << 1, /* mikrofon: vinkelsliper, bormaskin */
	SIGN_DOOR = 1u << 2,       /* kabindør / lokk på verktøykasse */
	SIGN_CAN_ACTIVE = 1u << 3, /* tenning eller CAN-trafikk uten avarmering */
	SIGN_TILT_LIFT = 1u << 4,  /* helning eller løft */
};

/* Entydig sabotasje: samme bitverdier som TAMPER i shared/protocol.ts */
enum {
	TAMPER_LID = 1u << 0, TAMPER_MESH = 1u << 1, TAMPER_ANTENNA = 1u << 2, TAMPER_GPS_LOOP = 1u << 3,
	TAMPER_POWER = 1u << 4, TAMPER_CAMERA = 1u << 5, TAMPER_CAN_GPS = 1u << 6,
};

typedef struct {
	gvt_zone_t zone;          /* hvor radaren ser personen */
	bool radar_person;        /* radaren klassifiserer person (ikke dyr) */
	bool camera_person;       /* kameraets KI bekrefter person */
	uint16_t dwell_on_machine_s; /* hvor lenge personen har vært på maskinen */
	uint8_t signs;            /* SIGN_* */
	uint8_t tamper_new;       /* nye TAMPER_*-bit siden forrige vurdering */
	uint8_t neighbors_same_vibration; /* antall naboer som melder samme vibrasjon samtidig */
	bool weather_damp;        /* sterk vind, regn eller snø fra værdata */
	bool night;               /* lokal natt etter anleggets kalender */
	bool learning;            /* læremodus de første 1–2 ukene */
	bool armed;
} gvt_inputs_t;

typedef struct {
	gvt_decision_t decision;
	bool siren;
	uint16_t siren_s;         /* 0 = til kvittering */
	bool send_image;
	const char *reason;       /* kort forklaring, sendes som tekst i meldingen */
} gvt_result_t;

gvt_result_t gvt_evaluate(gvt_env_t env, const gvt_inputs_t *in);
unsigned gvt_popcount8(uint8_t v);

#endif
