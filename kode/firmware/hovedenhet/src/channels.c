#include "channels.h"

gvt_channel_t gvt_choose_channel(const gvt_radio_t *r, bool is_alarm)
{
	if (r->lte_registered && r->rsrp_dbm > -125) return CH_LTE;
	/* Satellitt er dyrt og tregt: brukes for alarmer, og for heartbeat bare når LoRa heller ikke finnes. */
	if (r->ntn_available && (is_alarm || r->lora_neighbors == 0)) return CH_NTN;
	if (r->lora_neighbors > 0) return CH_LORA;
	if (r->ntn_available) return CH_NTN;
	return CH_STORE;
}

bool gvt_jamming_suspected(const gvt_radio_t *r)
{
	if (r->gnss_jam || r->gnss_spoof) return true;
	bool normally_good = r->rsrp_learned_dbm > -110;
	bool lost = !r->lte_registered || r->rsrp_dbm < r->rsrp_learned_dbm - 20;
	return normally_good && lost && r->lte_noise_high;
}
