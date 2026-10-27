// Kontrollerer at melding laget av fastvaren (C) leses likt av plattformen (TypeScript).
// Fiksturen lages med: make -C firmware/hovedenhet/test fixture
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fromHex } from '../shared/cbor.ts';
import { openEnvelope, decodePayload, encodePayload, TAMPER } from '../shared/protocol.ts';

test('fastvare og plattform koder meldingen likt', () => {
  const hex = readFileSync(new URL('./fixtures/fw_alarm.hex', import.meta.url), 'utf8').trim();
  const env = openEnvelope(fromHex(hex));
  assert.equal(env.signature.length, 64);
  const m = decodePayload(env.payload);
  assert.equal(m.id, 'GVT-0001A'); assert.equal(m.ctr, 4242); assert.equal(m.type, 'alarm');
  assert.equal(m.st?.tamper, TAMPER.lid | TAMPER.gpsLoop);
  assert.equal(m.rf?.rsrp, -101);
  assert.equal(m.ev?.text, 'Lokk åpnet');
  // Samme innhold kodet i TypeScript gir nøyaktig samme bytes (deterministisk CBOR).
  assert.deepEqual(encodePayload(m), env.payload);
});
