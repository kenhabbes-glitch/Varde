#include "geofence.h"
#include <math.h>

#define DEG2RAD 0.017453292519943295f
#define EARTH_R 6371000.0f

static void to_xy(const gvt_pt_t *ref, int32_t lat, int32_t lon, float *x, float *y)
{
	float lat0 = (float)ref->lat_e7 * 1e-7f;
	*x = (float)(lon - ref->lon_e7) * 1e-7f * DEG2RAD * EARTH_R * cosf(lat0 * DEG2RAD);
	*y = (float)(lat - ref->lat_e7) * 1e-7f * DEG2RAD * EARTH_R;
}

static float seg_dist(float px, float py, float ax, float ay, float bx, float by)
{
	float dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy, t = 0.0f;
	if (l2 > 0.0f) { t = ((px - ax) * dx + (py - ay) * dy) / l2; t = t < 0.0f ? 0.0f : (t > 1.0f ? 1.0f : t); }
	float ex = px - (ax + t * dx), ey = py - (ay + t * dy);
	return sqrtf(ex * ex + ey * ey);
}

float gvt_fence_distance(const gvt_fence_t *f, int32_t lat_e7, int32_t lon_e7)
{
	if (f->n < 3) return 0.0f;
	float px, py, d = 1e30f; int inside = 0;
	to_xy(&f->pts[0], lat_e7, lon_e7, &px, &py);
	for (uint8_t i = 0, j = f->n - 1; i < f->n; j = i++) {
		float xi, yi, xj, yj;
		to_xy(&f->pts[0], f->pts[i].lat_e7, f->pts[i].lon_e7, &xi, &yi);
		to_xy(&f->pts[0], f->pts[j].lat_e7, f->pts[j].lon_e7, &xj, &yj);
		if (((yi > py) != (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) inside = !inside;
		float s = seg_dist(px, py, xi, yi, xj, yj);
		if (s < d) d = s;
	}
	return inside ? -d : d;
}

int gvt_fence_outside(const gvt_fence_t *f, int32_t lat_e7, int32_t lon_e7, uint16_t acc_m)
{
	return gvt_fence_distance(f, lat_e7, lon_e7) - (float)acc_m > (float)f->buffer_m;
}
