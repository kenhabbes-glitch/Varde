import { test } from 'node:test';
import assert from 'node:assert/strict';
import { signedDistance, classify, validateFence, type Geofence } from '../platform/geofence.ts';

const c = { lat: 59.95, lon: 10.6 };
const dl = 100 / 111320, dn = 100 / (111320 * Math.cos(c.lat * Math.PI / 180));
const F: Geofence = { id: 'f1', site: 'S', name: 'S', bufferM: 20, polygon: [{ lat: c.lat - dl, lon: c.lon - dn }, { lat: c.lat - dl, lon: c.lon + dn }, { lat: c.lat + dl, lon: c.lon + dn }, { lat: c.lat + dl, lon: c.lon - dn }] };
const north = (m: number) => ({ lat: c.lat + m / 111320, lon: c.lon });

test('avstand til gjerdet i meter', () => {
  assert.ok(Math.abs(signedDistance(north(0), F) + 100) < 1);   // midt i: 100 m innenfor
  assert.ok(Math.abs(signedDistance(north(150), F) - 50) < 1);  // 50 m utenfor
});

test('buffer og GNSS-unøyaktighet', () => {
  assert.equal(classify({ ...north(110), acc: 5 }, F).state, 'inne');      // innenfor bufferen
  assert.equal(classify({ ...north(130), acc: 5 }, F).state, 'ute');
  assert.equal(classify({ ...north(130), acc: 30 }, F).state, 'usikker');  // for unøyaktig til å si sikkert
});

test('validering', () => {
  assert.equal(validateFence(F), undefined);
  assert.ok(validateFence({ ...F, polygon: F.polygon.slice(0, 2) }));
  assert.ok(validateFence({ ...F, bufferM: -1 }));
});
