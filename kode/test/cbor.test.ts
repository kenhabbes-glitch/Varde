import { test } from 'node:test';
import assert from 'node:assert/strict';
import { encode, decode, toHex } from '../shared/cbor.ts';

test('kjente CBOR-eksempler fra RFC 8949', () => {
  assert.equal(toHex(encode(0)), '00');
  assert.equal(toHex(encode(23)), '17');
  assert.equal(toHex(encode(24)), '1818');
  assert.equal(toHex(encode(1000)), '1903e8');
  assert.equal(toHex(encode(1000000)), '1a000f4240');
  assert.equal(toHex(encode(-1)), '20');
  assert.equal(toHex(encode(-1000)), '3903e7');
  assert.equal(toHex(encode('IETF')), '6449455446');
  assert.equal(toHex(encode([1, [2, 3]])), '8201820203');
  assert.equal(toHex(encode(true)), 'f5');
});

test('kart sorteres deterministisk', () => {
  const a = encode(new Map<number | string, any>([[3, 1], [1, 2], ['b', 3], ['a', 4]]));
  const b = encode(new Map<number | string, any>([['a', 4], [1, 2], ['b', 3], [3, 1]]));
  assert.deepEqual(a, b);
});

test('rundtur', () => {
  const v = new Map<number | string, any>([[1, 'æøå'], [2, Uint8Array.from([1, 2])], [3, [true, false, null, -5, 2 ** 40]]]);
  assert.deepEqual(decode(encode(v)), v);
});

test('avviser ødelagte og ondsinnede data', () => {
  assert.throws(() => decode(Uint8Array.from([0x19, 0x01])));        // for kort
  assert.throws(() => decode(Uint8Array.from([0x00, 0x00])));        // overflødige bytes
  assert.throws(() => decode(Uint8Array.from([0x9f])));              // ubestemt lengde
  assert.throws(() => decode(Uint8Array.from([0xfb, 0, 0, 0, 0, 0, 0, 0, 0]))); // flyttall
  assert.throws(() => decode(Uint8Array.from(new Array(40).fill(0x81).concat([0])))); // for dypt
  assert.throws(() => encode(1.5 as any));
});
