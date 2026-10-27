/* Geofence i enheten: lagret kopi av anleggets gjerde, slik at enheten selv merker
 * at den forlater anlegget også når mobilnettet er jammet (meldes da via LoRa eller satellitt). */
#ifndef GVT_GEOFENCE_H
#define GVT_GEOFENCE_H
#include <stdint.h>

#define GVT_FENCE_MAX_PTS 32

typedef struct { int32_t lat_e7, lon_e7; } gvt_pt_t;
typedef struct { gvt_pt_t pts[GVT_FENCE_MAX_PTS]; uint8_t n; uint16_t buffer_m; } gvt_fence_t;

/* Avstand i meter fra punktet til gjerdet: negativ innenfor, positiv utenfor. */
float gvt_fence_distance(const gvt_fence_t *f, int32_t lat_e7, int32_t lon_e7);
/* 1 = sikkert ute (avstand minus unøyaktighet er større enn bufferen), 0 ellers. */
int gvt_fence_outside(const gvt_fence_t *f, int32_t lat_e7, int32_t lon_e7, uint16_t acc_m);

#endif
