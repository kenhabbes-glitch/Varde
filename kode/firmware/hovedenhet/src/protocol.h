/* Meldingsformat v1, samme feltnummer som shared/protocol.ts.
 * Konvolutt: CBOR-liste [payload: bytes, signatur: bytes(64)], ECDSA P-256 r||s fra ATECC608B. */
#ifndef GVT_PROTOCOL_H
#define GVT_PROTOCOL_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define GVT_PROTOCOL_VERSION 1

enum { F_V = 1, F_ID = 2, F_CTR = 3, F_TS = 4, F_TYPE = 5, F_IV = 6, F_ST = 7, F_RF = 8, F_EV = 9, F_TGT = 10, F_ENV = 11, F_POS = 12 };
enum { ST_BAT = 1, ST_VINMV = 2, ST_TEMPC = 3, ST_EXT = 4, ST_TAMPER = 5, ST_ARMED = 6 };
enum { RF_CH = 1, RF_RSRP = 2, RF_NOISE = 3, RF_GNSSJAM = 4 };
enum { EV_CODE = 1, EV_ZONE = 2, EV_TEXT = 3, EV_IMG = 4 };

typedef struct { uint8_t *buf; size_t cap, len; bool err; } cbor_w;

void cbor_init(cbor_w *w, uint8_t *buf, size_t cap);
void cbor_uint(cbor_w *w, uint64_t v);
void cbor_int(cbor_w *w, int64_t v);
void cbor_text(cbor_w *w, const char *s);
void cbor_bytes(cbor_w *w, const uint8_t *b, size_t n);
void cbor_bool(cbor_w *w, bool v);
void cbor_array(cbor_w *w, size_t n);
void cbor_map(cbor_w *w, size_t n);

typedef struct {
	const char *id;
	uint32_t ctr;
	uint32_t ts;
	const char *type;   /* "hb", "alarm", "info", "report" */
	uint16_t iv;
	/* status */
	uint8_t bat; bool ext; uint8_t tamper; bool armed;
	/* radio */
	const char *ch; int16_t rsrp; bool noise; bool gnss_jam;
	/* hendelse (valgfri) */
	const char *ev_code; uint8_t ev_zone; const char *ev_text; bool ev_img;
	const char *tgt;    /* for "report" */
	/* posisjon (valgfri): grader × 1e7 og nøyaktighet i meter */
	bool has_pos; int32_t lat_e7; int32_t lon_e7; uint16_t acc_m;
} gvt_msg_t;

/* Koder payload. Returnerer lengde, 0 ved feil. Nøkler i stigende rekkefølge (deterministisk). */
size_t gvt_encode_payload(const gvt_msg_t *m, uint8_t *out, size_t cap);

/* Signeringsfunksjon: ATECC608B i drift, programvare i tester. 0 = OK. */
typedef int (*gvt_sign_fn)(const uint8_t *data, size_t len, uint8_t sig[64]);

/* Lager signert konvolutt. Returnerer lengde, 0 ved feil. */
size_t gvt_seal(const gvt_msg_t *m, gvt_sign_fn sign, uint8_t *out, size_t cap);

#endif
