#include "protocol.h"
#include <string.h>

void cbor_init(cbor_w *w, uint8_t *buf, size_t cap) { w->buf = buf; w->cap = cap; w->len = 0; w->err = false; }

static void put(cbor_w *w, uint8_t b) { if (w->len < w->cap) w->buf[w->len++] = b; else w->err = true; }

static void head(cbor_w *w, uint8_t major, uint64_t n)
{
	uint8_t m = (uint8_t)(major << 5);
	if (n < 24) put(w, m | (uint8_t)n);
	else if (n <= 0xff) { put(w, m | 24); put(w, (uint8_t)n); }
	else if (n <= 0xffff) { put(w, m | 25); put(w, (uint8_t)(n >> 8)); put(w, (uint8_t)n); }
	else if (n <= 0xffffffffu) { put(w, m | 26); for (int s = 24; s >= 0; s -= 8) put(w, (uint8_t)(n >> s)); }
	else { put(w, m | 27); for (int s = 56; s >= 0; s -= 8) put(w, (uint8_t)(n >> s)); }
}

void cbor_uint(cbor_w *w, uint64_t v) { head(w, 0, v); }
void cbor_int(cbor_w *w, int64_t v) { if (v >= 0) head(w, 0, (uint64_t)v); else head(w, 1, (uint64_t)(-1 - v)); }
void cbor_text(cbor_w *w, const char *s) { size_t n = strlen(s); head(w, 3, n); for (size_t i = 0; i < n; i++) put(w, (uint8_t)s[i]); }
void cbor_bytes(cbor_w *w, const uint8_t *b, size_t n) { head(w, 2, n); for (size_t i = 0; i < n; i++) put(w, b[i]); }
void cbor_bool(cbor_w *w, bool v) { put(w, v ? 0xf5 : 0xf4); }
void cbor_array(cbor_w *w, size_t n) { head(w, 4, n); }
void cbor_map(cbor_w *w, size_t n) { head(w, 5, n); }

size_t gvt_encode_payload(const gvt_msg_t *m, uint8_t *out, size_t cap)
{
	cbor_w w; cbor_init(&w, out, cap);
	bool has_ev = m->ev_code != NULL, has_tgt = m->tgt != NULL;
	size_t n = 6 /* v id ctr ts type iv */ + 2 /* st rf */ + (has_ev ? 1 : 0) + (has_tgt ? 1 : 0) + (m->has_pos ? 1 : 0);
	cbor_map(&w, n);
	cbor_uint(&w, F_V); cbor_uint(&w, GVT_PROTOCOL_VERSION);
	cbor_uint(&w, F_ID); cbor_text(&w, m->id);
	cbor_uint(&w, F_CTR); cbor_uint(&w, m->ctr);
	cbor_uint(&w, F_TS); cbor_uint(&w, m->ts);
	cbor_uint(&w, F_TYPE); cbor_text(&w, m->type);
	cbor_uint(&w, F_IV); cbor_uint(&w, m->iv);

	cbor_uint(&w, F_ST); cbor_map(&w, 4);
	cbor_uint(&w, ST_BAT); cbor_uint(&w, m->bat);
	cbor_uint(&w, ST_EXT); cbor_bool(&w, m->ext);
	cbor_uint(&w, ST_TAMPER); cbor_uint(&w, m->tamper);
	cbor_uint(&w, ST_ARMED); cbor_bool(&w, m->armed);

	cbor_uint(&w, F_RF); cbor_map(&w, 4);
	cbor_uint(&w, RF_CH); cbor_text(&w, m->ch ? m->ch : "LTE-M");
	cbor_uint(&w, RF_RSRP); cbor_int(&w, m->rsrp);
	cbor_uint(&w, RF_NOISE); cbor_bool(&w, m->noise);
	cbor_uint(&w, RF_GNSSJAM); cbor_bool(&w, m->gnss_jam);

	if (has_ev) {
		size_t k = 1 + (m->ev_zone ? 1 : 0) + (m->ev_text ? 1 : 0) + (m->ev_img ? 1 : 0);
		cbor_uint(&w, F_EV); cbor_map(&w, k);
		cbor_uint(&w, EV_CODE); cbor_text(&w, m->ev_code);
		if (m->ev_zone) { cbor_uint(&w, EV_ZONE); cbor_uint(&w, m->ev_zone); }
		if (m->ev_text) { cbor_uint(&w, EV_TEXT); cbor_text(&w, m->ev_text); }
		if (m->ev_img) { cbor_uint(&w, EV_IMG); cbor_bool(&w, true); }
	}
	if (has_tgt) { cbor_uint(&w, F_TGT); cbor_text(&w, m->tgt); }
	if (m->has_pos) { cbor_uint(&w, F_POS); cbor_array(&w, 3); cbor_int(&w, m->lat_e7); cbor_int(&w, m->lon_e7); cbor_uint(&w, m->acc_m); }
	return w.err ? 0 : w.len;
}

size_t gvt_seal(const gvt_msg_t *m, gvt_sign_fn sign, uint8_t *out, size_t cap)
{
	uint8_t payload[512], sig[64];
	size_t n = gvt_encode_payload(m, payload, sizeof payload);
	if (!n || sign(payload, n, sig) != 0) return 0;
	cbor_w w; cbor_init(&w, out, cap);
	cbor_array(&w, 2); cbor_bytes(&w, payload, n); cbor_bytes(&w, sig, 64);
	return w.err ? 0 : w.len;
}
