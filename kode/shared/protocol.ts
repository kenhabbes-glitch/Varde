// Felles meldingsformat mellom enheter og plattform (versjon 1).
// Samme feltnummer brukes i fastvaren (firmware/hovedenhet/src/protocol.h).
//
// Konvolutt:  CBOR-liste [ payload: bytes, signatur: bytes(64) ]
// Signatur:   ECDSA P-256 / SHA-256 over payload-bytene, rå r||s (64 byte),
//             samme format som ATECC608B gir.
// Payload:    CBOR-kart med heltallsnøkler, se FIELD under.

import { createSign, createVerify, generateKeyPairSync, KeyObject, createPublicKey, createPrivateKey } from 'node:crypto';
import { encode, decode, type CborValue } from './cbor.ts';

export const PROTOCOL_VERSION = 1;

export const FIELD = {
  v: 1, id: 2, ctr: 3, ts: 4, type: 5, iv: 6, st: 7, rf: 8, ev: 9, tgt: 10, env: 11, pos: 12,
} as const;
export const ST = { bat: 1, vinMv: 2, tempC: 3, ext: 4, tamper: 5, armed: 6 } as const;
export const RF = { ch: 1, rsrp: 2, noise: 3, gnssJam: 4 } as const;
export const EV = { code: 1, zone: 2, text: 3, img: 4 } as const;

export type MsgType = 'hb' | 'alarm' | 'info' | 'report';
export type Channel = 'LTE-M' | 'NTN' | 'LoRa' | 'lokal';
export type EnvProfile = 'skog' | 'landlig' | 'by';

// Bitfelt for sabotasje (samme verdier i fastvaren)
export const TAMPER = {
  lid: 1 << 0, mesh: 1 << 1, antenna: 1 << 2, gpsLoop: 1 << 3, power: 1 << 4, camera: 1 << 5, canGps: 1 << 6,
} as const;

// SIA-lignende hendelseskoder (kapittel om alarmstasjoner)
export type EventCode = 'BA' | 'TA' | 'YC' | 'YK' | 'XT' | 'XR' | 'AT' | 'CL' | 'OP' | 'RP' | 'GF';

/** Posisjon fra GNSS. Heltall for å unngå flyttall i CBOR: grader × 1e7 og nøyaktighet i meter. */
export interface Position { lat: number; lon: number; acc: number; }

export interface Status { bat?: number; vinMv?: number; tempC?: number; ext?: boolean; tamper?: number; armed?: boolean; }
export interface Radio { ch?: Channel; rsrp?: number; noise?: boolean; gnssJam?: boolean; }
export interface DeviceEvent { code: EventCode; zone?: number; text?: string; img?: boolean; }

export interface Message {
  v: number;
  id: string;        // enhets-ID, f.eks. "GVT-0001A"
  ctr: number;       // monoton teller, øker for hver melding
  ts: number;        // enhetens tid, sekunder siden 1970
  type: MsgType;
  iv?: number;       // forventet heartbeat-intervall i sekunder
  st?: Status;
  rf?: Radio;
  ev?: DeviceEvent;
  tgt?: string;      // for 'report': enheten det meldes om (nabo som er borte)
  env?: EnvProfile;
  pos?: Position;    // siste GNSS-posisjon (sendes ved bevegelse og jevnlig i heartbeat)
}

function sub(obj: Record<string, unknown> | undefined, keys: Record<string, number>): Map<number, CborValue> | undefined {
  if (!obj) return undefined;
  const m = new Map<number, CborValue>();
  for (const [k, n] of Object.entries(keys)) {
    const v = obj[k];
    if (v !== undefined) m.set(n, v as CborValue);
  }
  return m.size ? m : undefined;
}
function unsub<T>(m: CborValue | undefined, keys: Record<string, number>): T | undefined {
  if (!(m instanceof Map)) return undefined;
  const o: Record<string, unknown> = {};
  for (const [k, n] of Object.entries(keys)) if (m.has(n)) o[k] = m.get(n);
  return o as T;
}

export function encodePayload(msg: Message): Uint8Array {
  const m = new Map<number, CborValue>();
  m.set(FIELD.v, msg.v); m.set(FIELD.id, msg.id); m.set(FIELD.ctr, msg.ctr); m.set(FIELD.ts, msg.ts); m.set(FIELD.type, msg.type);
  if (msg.iv !== undefined) m.set(FIELD.iv, msg.iv);
  const st = sub(msg.st as Record<string, unknown>, ST); if (st) m.set(FIELD.st, st);
  const rf = sub(msg.rf as Record<string, unknown>, RF); if (rf) m.set(FIELD.rf, rf);
  const ev = sub(msg.ev as unknown as Record<string, unknown>, EV); if (ev) m.set(FIELD.ev, ev);
  if (msg.tgt) m.set(FIELD.tgt, msg.tgt);
  if (msg.env) m.set(FIELD.env, msg.env);
  if (msg.pos) m.set(FIELD.pos, [Math.round(msg.pos.lat * 1e7), Math.round(msg.pos.lon * 1e7), Math.round(msg.pos.acc)]);
  return encode(m);
}

export function decodePayload(b: Uint8Array): Message {
  const m = decode(b);
  if (!(m instanceof Map)) throw new Error('Payload er ikke et kart');
  const get = (k: number) => m.get(k);
  const msg: Message = {
    v: get(FIELD.v) as number, id: get(FIELD.id) as string, ctr: get(FIELD.ctr) as number,
    ts: get(FIELD.ts) as number, type: get(FIELD.type) as MsgType,
  };
  if (msg.v !== PROTOCOL_VERSION) throw new Error(`Ukjent protokollversjon ${msg.v}`);
  if (typeof msg.id !== 'string' || !/^[A-Za-z0-9-]{3,32}$/.test(msg.id)) throw new Error('Ugyldig enhets-ID');
  if (!Number.isSafeInteger(msg.ctr) || msg.ctr < 0) throw new Error('Ugyldig teller');
  if (!['hb', 'alarm', 'info', 'report'].includes(msg.type)) throw new Error('Ugyldig meldingstype');
  if (m.has(FIELD.iv)) msg.iv = get(FIELD.iv) as number;
  msg.st = unsub<Status>(get(FIELD.st), ST);
  msg.rf = unsub<Radio>(get(FIELD.rf), RF);
  msg.ev = unsub<DeviceEvent>(get(FIELD.ev), EV);
  if (m.has(FIELD.tgt)) msg.tgt = get(FIELD.tgt) as string;
  if (m.has(FIELD.env)) msg.env = get(FIELD.env) as EnvProfile;
  if (m.has(FIELD.pos)) {
    const a = get(FIELD.pos);
    if (!Array.isArray(a) || a.length !== 3 || !a.every(x => Number.isSafeInteger(x))) throw new Error('Ugyldig posisjon');
    const [lat, lon, acc] = a as number[];
    if (Math.abs(lat) > 900000000 || Math.abs(lon) > 1800000000 || acc < 0) throw new Error('Posisjon utenfor gyldig område');
    msg.pos = { lat: lat / 1e7, lon: lon / 1e7, acc };
  }
  return msg;
}

// ---------- signering ----------

export function newKeyPair(): { publicKeyPem: string; privateKey: KeyObject } {
  const { publicKey, privateKey } = generateKeyPairSync('ec', { namedCurve: 'prime256v1' });
  return { publicKeyPem: publicKey.export({ type: 'spki', format: 'pem' }).toString(), privateKey };
}
export const loadPublicKey = (pem: string) => createPublicKey(pem);
export const loadPrivateKey = (pem: string) => createPrivateKey(pem);

export function sign(payload: Uint8Array, key: KeyObject): Uint8Array {
  const s = createSign('SHA256'); s.update(payload); s.end();
  return Uint8Array.from(s.sign({ key, dsaEncoding: 'ieee-p1363' }));
}
export function verify(payload: Uint8Array, signature: Uint8Array, key: KeyObject): boolean {
  if (signature.length !== 64) return false;
  const v = createVerify('SHA256'); v.update(payload); v.end();
  try { return v.verify({ key, dsaEncoding: 'ieee-p1363' }, signature); } catch { return false; }
}

export function sealMessage(msg: Message, key: KeyObject): Uint8Array {
  const p = encodePayload(msg);
  return encode([p, sign(p, key)]);
}
export function openEnvelope(b: Uint8Array): { payload: Uint8Array; signature: Uint8Array } {
  const e = decode(b);
  if (!Array.isArray(e) || e.length !== 2 || !(e[0] instanceof Uint8Array) || !(e[1] instanceof Uint8Array)) throw new Error('Ugyldig konvolutt');
  if (e[0].length > 1024) throw new Error('Payload for stor');
  return { payload: e[0], signature: e[1] };
}

// Kvittering fra plattformen til enheten, signert med plattformens nøkkel.
// Kart: 1 = 'ack', 2 = teller som kvitteres, 3 = plattformens tid, 4 = nytt intervall (valgfritt)
export function sealAck(ctr: number, serverTs: number, key: KeyObject, newInterval?: number): Uint8Array {
  const m = new Map<number, CborValue>([[1, 'ack'], [2, ctr], [3, serverTs]]);
  if (newInterval) m.set(4, newInterval);
  const p = encode(m);
  return encode([p, sign(p, key)]);
}
