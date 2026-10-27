// Enkel lagring i minnet med lagring til JSON-fil.
// FØRSTE VERSJON. I drift erstattes dette av PostgreSQL (se kapittel om programvare).

import { readFileSync, writeFileSync, existsSync, renameSync } from 'node:fs';
import type { Unit, AlarmCase } from './rules.ts';
import type { Geofence } from './geofence.ts';

export interface Snapshot { units: Unit[]; cases: AlarmCase[]; log: { t: number; text: string }[]; fences?: Geofence[]; }

export class Store {
  private file?: string;
  private timer?: NodeJS.Timeout;
  constructor(file?: string) { this.file = file; }

  load(): Snapshot | undefined {
    if (!this.file || !existsSync(this.file)) return undefined;
    return JSON.parse(readFileSync(this.file, 'utf8')) as Snapshot;
  }

  /** Lagrer med kort forsinkelse, slik at mange endringer gir én skriving. */
  saveSoon(get: () => Snapshot): void {
    if (!this.file || this.timer) return;
    this.timer = setTimeout(() => {
      this.timer = undefined;
      const tmp = this.file + '.tmp';
      writeFileSync(tmp, JSON.stringify(get(), null, 1));
      renameSync(tmp, this.file!);
    }, 500);
  }
}
