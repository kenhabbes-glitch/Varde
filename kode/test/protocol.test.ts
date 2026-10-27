import { test } from 'node:test';
import assert from 'node:assert/strict';
import { newKeyPair, loadPublicKey, sealMessage, openEnvelope, decodePayload, verify, encodePayload, TAMPER, type Message } from '../shared/protocol.ts';

const msg: Message = { v: 1, id: 'GVT-0001A', ctr: 7, ts: 1761300000, type: 'alarm', iv: 120,
  st: { bat: 88, ext: true, tamper: TAMPER.lid | TAMPER.gpsLoop, armed: true }, rf: { ch: 'LTE-M', rsrp: -101, noise: false },
  ev: { code: 'TA', zone: 2, text: 'Lokk åpnet' } };

test('signert melding kan åpnes og verifiseres', () => {
  const kp = newKeyPair();
  const env = openEnvelope(sealMessage(msg, kp.privateKey));
  assert.equal(env.signature.length, 64);
  assert.ok(verify(env.payload, env.signature, loadPublicKey(kp.publicKeyPem)));
  assert.deepEqual(decodePayload(env.payload), msg);
});

test('feil nøkkel og endret innhold avvises', () => {
  const a = newKeyPair(), b = newKeyPair();
  const env = openEnvelope(sealMessage(msg, a.privateKey));
  assert.equal(verify(env.payload, env.signature, loadPublicKey(b.publicKeyPem)), false);
  const tampered = Uint8Array.from(env.payload); tampered[tampered.length - 1] ^= 1;
  assert.equal(verify(tampered, env.signature, loadPublicKey(a.publicKeyPem)), false);
});

test('meldingen er liten nok for NTN/LoRa', () => {
  const hb = encodePayload({ v: 1, id: 'GVT-0001A', ctr: 123456, ts: 1761300000, type: 'hb', iv: 120, st: { bat: 90, tamper: 0 }, rf: { ch: 'LTE-M' } });
  assert.ok(hb.length < 64, `heartbeat er ${hb.length} byte`);
});

test('ugyldige felt avvises', () => {
  assert.throws(() => decodePayload(encodePayload({ ...msg, v: 2 })));
  assert.throws(() => decodePayload(encodePayload({ ...msg, id: 'x' })));
  assert.throws(() => decodePayload(encodePayload({ ...msg, type: 'boom' as any })));
});

test('posisjon kodes som heltall og leses tilbake', () => {
  const m: Message = { v: 1, id: 'GVT-0001A', ctr: 1, ts: 0, type: 'hb', pos: { lat: 59.9127123, lon: 10.7461456, acc: 4 } };
  const d = decodePayload(encodePayload(m));
  assert.ok(Math.abs(d.pos!.lat - 59.9127123) < 1e-7 && Math.abs(d.pos!.lon - 10.7461456) < 1e-7 && d.pos!.acc === 4);
});
