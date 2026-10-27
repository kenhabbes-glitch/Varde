// Geofence (elektronisk gjerde) rundt et anlegg.
// Et gjerde er en mangekant av punkter (grader) pluss en buffer i meter.
// Avstander regnes i en lokal flat projeksjon, som er nøyaktig nok for anlegg på noen kilometer.

export interface LatLon { lat: number; lon: number; }
export interface Geofence {
  id: string;
  site: string;          // anlegget gjerdet gjelder for (samme som Unit.site)
  name: string;
  polygon: LatLon[];     // minst 3 punkter, i rekkefølge rundt anlegget
  bufferM: number;       // margin utenfor streken før enheten regnes som ute (GNSS-unøyaktighet)
}

export type GeoState = 'inne' | 'ute' | 'usikker' | 'ukjent';

const R = 6371000;
function toXY(p: LatLon, ref: LatLon): [number, number] {
  const x = (p.lon - ref.lon) * Math.PI / 180 * R * Math.cos(ref.lat * Math.PI / 180);
  const y = (p.lat - ref.lat) * Math.PI / 180 * R;
  return [x, y];
}

function segDist(px: number, py: number, ax: number, ay: number, bx: number, by: number): number {
  const dx = bx - ax, dy = by - ay;
  const t = dx || dy ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy))) : 0;
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

/** Avstand i meter fra punktet til gjerdet: negativ innenfor, positiv utenfor. */
export function signedDistance(p: LatLon, fence: Geofence): number {
  const ref = fence.polygon[0];
  const [px, py] = toXY(p, ref);
  const pts = fence.polygon.map(q => toXY(q, ref));
  let inside = false, d = Infinity;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j];
    if ((yi > py) !== (yj > py) && px < (xj - xi) * (py - yi) / (yj - yi) + xi) inside = !inside;
    d = Math.min(d, segDist(px, py, xi, yi, xj, yj));
  }
  return inside ? -d : d;
}

/** Klassifiserer en posisjon. 'usikker' når unøyaktigheten er større enn avstanden til streken. */
export function classify(p: LatLon & { acc: number }, fence: Geofence): { state: GeoState; distM: number } {
  const d = signedDistance(p, fence);
  if (d <= fence.bufferM) {
    return { state: d > fence.bufferM - p.acc && d > 0 ? 'usikker' : 'inne', distM: d };
  }
  return { state: d - p.acc > fence.bufferM ? 'ute' : 'usikker', distM: d };
}

export function validateFence(f: Partial<Geofence>): string | undefined {
  if (!f.id || !/^[A-Za-z0-9-]{2,40}$/.test(f.id)) return 'Ugyldig id';
  if (!f.site) return 'Mangler anlegg';
  if (!Array.isArray(f.polygon) || f.polygon.length < 3 || f.polygon.length > 200) return 'Gjerdet må ha 3–200 punkter';
  for (const p of f.polygon) if (typeof p?.lat !== 'number' || typeof p?.lon !== 'number' || Math.abs(p.lat) > 90 || Math.abs(p.lon) > 180) return 'Ugyldig punkt i gjerdet';
  if (typeof f.bufferM !== 'number' || f.bufferM < 0 || f.bufferM > 1000) return 'Buffer må være 0–1000 m';
  return undefined;
}
