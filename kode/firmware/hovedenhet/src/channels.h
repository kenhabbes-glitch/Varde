/* Kanalvalg og jammingdeteksjon. Rekkefølge: LTE-M -> NTN (satellitt) -> LoRa via nabo -> lagre og sende senere. */
#ifndef GVT_CHANNELS_H
#define GVT_CHANNELS_H
#include <stdbool.h>
#include <stdint.h>

typedef enum { CH_LTE = 0, CH_NTN = 1, CH_LORA = 2, CH_STORE = 3 } gvt_channel_t;

typedef struct {
	bool lte_registered;
	int16_t rsrp_dbm;         /* signalstyrke */
	int16_t rsrp_learned_dbm; /* normalnivå lært i læremodus */
	bool lte_noise_high;      /* modemet melder høy støy / tap av synk */
	bool ntn_available;       /* satellitt i sikt og abonnement aktivt */
	uint8_t lora_neighbors;   /* naboer hørt siste 5 min */
	bool gnss_jam;            /* MAX-M10S melder jamming */
	bool gnss_spoof;
} gvt_radio_t;

gvt_channel_t gvt_choose_channel(const gvt_radio_t *r, bool is_alarm);
/* Jamming: brudd i et ellers stabilt mønster, sammen med støy. Dårlig dekning alene er ikke jamming. */
bool gvt_jamming_suspected(const gvt_radio_t *r);

#endif
