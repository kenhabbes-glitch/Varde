// Minimal CBOR (RFC 8949) for Varde-meldinger.
// Støtter: uint, negative int, byte string, text string, array, map (int- eller text-nøkler),
// true/false/null. Ingen float, ingen tags. Holder meldingene små og deterministiske.

export type CborValue =
  | number
  | string
  | boolean
  | null
  | Uint8Array
  | CborValue[]
  | Map<number | string, CborValue>;

function head(major: number, n: number, out: number[]): void {
  if (!Number.isInteger(n) || n < 0) throw new Error(`Ugyldig lengde/verdi: ${n}`);
  const m = major << 5;
  if (n < 24) out.push(m | n);
  else if (n < 0x100) out.push(m | 24, n);
  else if (n < 0x10000) out.push(m | 25, n >> 8, n & 0xff);
  else if (n < 0x100000000) out.push(m | 26, (n >>> 24) & 0xff, (n >>> 16) & 0xff, (n >>> 8) & 0xff, n & 0xff);
  else {
    const hi = Math.floor(n / 0x100000000), lo = n >>> 0;
    out.push(m | 27, (hi >>> 24) & 0xff, (hi >>> 16) & 0xff, (hi >>> 8) & 0xff, hi & 0xff,
      (lo >>> 24) & 0xff, (lo >>> 16) & 0xff, (lo >>> 8) & 0xff, lo & 0xff);
  }
}

function enc(v: CborValue, out: number[]): void {
  if (v === null) { out.push(0xf6); return; }
  if (v === true) { out.push(0xf5); return; }
  if (v === false) { out.push(0xf4); return; }
  if (typeof v === 'number') {
    if (!Number.isSafeInteger(v)) throw new Error('Bare heltall støttes');
    if (v >= 0) head(0, v, out); else head(1, -1 - v, out);
    return;
  }
  if (typeof v === 'string') {
    const b = new TextEncoder().encode(v);
    head(3, b.length, out); for (const x of b) out.push(x); return;
  }
  if (v instanceof Uint8Array) { head(2, v.length, out); for (const x of v) out.push(x); return; }
  if (Array.isArray(v)) { head(4, v.length, out); for (const x of v) enc(x, out); return; }
  if (v instanceof Map) {
    // Deterministisk rekkefølge: heltallsnøkler stigende, deretter tekst.
    const keys = [...v.keys()].sort((a, b) => {
      if (typeof a === 'number' && typeof b === 'number') return a - b;
      if (typeof a === 'number') return -1;
      if (typeof b === 'number') return 1;
      return a < b ? -1 : a > b ? 1 : 0;
    });
    head(5, keys.length, out);
    for (const k of keys) { enc(k, out); enc(v.get(k) as CborValue, out); }
    return;
  }
  throw new Error('Ukjent type i CBOR-koding');
}

export function encode(v: CborValue): Uint8Array {
  const out: number[] = [];
  enc(v, out);
  return Uint8Array.from(out);
}

export function decode(buf: Uint8Array): CborValue {
  let i = 0;
  const need = (n: number) => { if (i + n > buf.length) throw new Error('CBOR: for kort melding'); };
  const readLen = (info: number): number => {
    if (info < 24) return info;
    if (info === 24) { need(1); return buf[i++]; }
    if (info === 25) { need(2); const n = (buf[i] << 8) | buf[i + 1]; i += 2; return n; }
    if (info === 26) { need(4); const n = ((buf[i] << 24) >>> 0) + (buf[i + 1] << 16) + (buf[i + 2] << 8) + buf[i + 3]; i += 4; return n; }
    if (info === 27) {
      need(8);
      let n = 0; for (let k = 0; k < 8; k++) n = n * 256 + buf[i + k]; i += 8;
      if (!Number.isSafeInteger(n)) throw new Error('CBOR: tall for stort');
      return n;
    }
    throw new Error('CBOR: ubestemt lengde støttes ikke');
  };
  const item = (depth: number): CborValue => {
    if (depth > 16) throw new Error('CBOR: for dyp struktur');
    need(1);
    const b = buf[i++], major = b >> 5, info = b & 0x1f;
    switch (major) {
      case 0: return readLen(info);
      case 1: return -1 - readLen(info);
      case 2: { const n = readLen(info); need(n); const s = buf.slice(i, i + n); i += n; return s; }
      case 3: { const n = readLen(info); need(n); const s = new TextDecoder('utf-8', { fatal: true }).decode(buf.subarray(i, i + n)); i += n; return s; }
      case 4: { const n = readLen(info); if (n > 1024) throw new Error('CBOR: for lang liste'); const a: CborValue[] = []; for (let k = 0; k < n; k++) a.push(item(depth + 1)); return a; }
      case 5: {
        const n = readLen(info); if (n > 256) throw new Error('CBOR: for stort kart');
        const m = new Map<number | string, CborValue>();
        for (let k = 0; k < n; k++) {
          const key = item(depth + 1);
          if (typeof key !== 'number' && typeof key !== 'string') throw new Error('CBOR: ugyldig nøkkel');
          m.set(key, item(depth + 1));
        }
        return m;
      }
      case 7:
        if (info === 20) return false;
        if (info === 21) return true;
        if (info === 22) return null;
        throw new Error('CBOR: flyttall og andre enkle verdier støttes ikke');
      default: throw new Error('CBOR: tagger støttes ikke');
    }
  };
  const v = item(0);
  if (i !== buf.length) throw new Error('CBOR: overflødige bytes');
  return v;
}

export const toHex = (b: Uint8Array) => Buffer.from(b).toString('hex');
export const fromHex = (h: string) => Uint8Array.from(Buffer.from(h, 'hex'));
