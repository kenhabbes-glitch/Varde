// Formatering av alarmer til SIA DC-09 for alarmstasjon (Avarn, Securitas, Vaktcompaniet m.fl.).
// FØRSTE VERSJON: bare formatering av ukryptert ramme. Kryptering (AES), kvittering, ventetid
// og reserveforbindelse avtales med hver alarmstasjon og implementeres av leverandøren.
// Alarmstasjon er AV som standard og slås på per kunde.

import type { EventCode } from '../shared/protocol.ts';

// CRC-16/ARC (polynom 0xA001), slik DC-09 bruker.
export function crc16(s: string): number {
  let crc = 0;
  for (const b of new TextEncoder().encode(s)) {
    crc ^= b;
    for (let i = 0; i < 8; i++) crc = crc & 1 ? (crc >>> 1) ^ 0xa001 : crc >>> 1;
  }
  return crc & 0xffff;
}

export interface Dc09Event { seq: number; receiver?: string; line?: string; account: string; code: EventCode; zone?: number; time: Date; }

/** Lager en DC-09-ramme med SIA-DCS-innhold: <LF>crc 0LLL"SIA-DCS"seq R L #acct[#acct|Nri0/CODEzone]_tid<CR> */
export function formatDc09(e: Dc09Event): string {
  const seq = String(e.seq % 10000).padStart(4, '0');
  const zone = String(e.zone ?? 0).padStart(3, '0');
  const t = e.time;
  const p2 = (n: number) => String(n).padStart(2, '0');
  const ts = `_${p2(t.getUTCHours())}:${p2(t.getUTCMinutes())}:${p2(t.getUTCSeconds())},${p2(t.getUTCMonth() + 1)}-${p2(t.getUTCDate())}-${t.getUTCFullYear()}`;
  const body = `"SIA-DCS"${seq}R${e.receiver ?? '0'}L${e.line ?? '0'}#${e.account}[#${e.account}|N${e.code}${zone}]${ts}`;
  const len = body.length.toString(16).toUpperCase().padStart(4, '0');
  const crc = crc16(body).toString(16).toUpperCase().padStart(4, '0');
  return `\n${crc}${len}${body}\r`;
}
