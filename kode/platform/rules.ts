// Regelmotor: én tilstandsmaskin per enhet, og alarmsaker med eskalering.
// Tiden kommer utenfra (now()), slik at motoren kan testes uten å vente.

import type { Message, EnvProfile, EventCode, Channel, Position } from '../shared/protocol.ts';
import { classify, type Geofence, type GeoState } from './geofence.ts';
import { TAMPER } from '../shared/protocol.ts';

export type UnitState = 'Normal' | 'Forsinket' | 'Mistenkelig' | 'Alarm';
export type CaseState = 'Ny' | 'Behandles' | 'Videresendt' | 'Avsluttet';

export interface Unit {
  id: string; name: string; kind: string; site: string; env: EnvProfile;
  publicKeyPem: string;
  lastCtr: number; lastSeen: number; interval: number; channel: Channel | '';
  state: UnitState; reason: string; latched: boolean;
  noise: boolean; neighborMissing: boolean; armed: boolean;
  battery?: number; extPower?: boolean; tamper: number;
  pos?: Position & { t: number };   // siste kjente posisjon
  geo?: GeoState; geoDistM?: number; geoOutCount?: number;
}

export interface AlarmCase {
  id: string; unitId: string; site: string; prio: 1 | 2 | 3; code: EventCode; title: string;
  state: CaseState; owner?: string; result?: string; created: number; escalateAt?: number;
  events: { t: number; text: string }[];
}

export interface Policy {
  escalateAfterSec: number;      // prioritet 1 uten eier eskaleres etter dette
  arcEnabled: boolean;           // alarmstasjon er valgfritt, av som standard
}

export type Emit = (kind: string, data: unknown) => void;

const TAMPER_TEXT: [number, string][] = [
  [TAMPER.lid, 'Lokket er åpnet'], [TAMPER.mesh, 'Brudd i tamperfolien'], [TAMPER.antenna, 'Antennekabel kuttet'],
  [TAMPER.gpsLoop, 'Kabelsløyfen rundt GPS-utstyret er brutt'], [TAMPER.power, 'Strømmen er kuttet'],
  [TAMPER.camera, 'Kamera tildekket eller flyttet'], [TAMPER.canGps, 'GPS-utstyret er borte fra CAN-bussen'],
];

export class RuleEngine {
  units = new Map<string, Unit>();
  fences = new Map<string, Geofence>();
  cases: AlarmCase[] = [];
  private caseNo = 1000;
  private now: () => number;
  private emit: Emit;
  policy: Policy;

  constructor(now: () => number, emit: Emit, policy?: Partial<Policy>) {
    this.now = now; this.emit = emit;
    this.policy = { escalateAfterSec: 180, arcEnabled: false, ...policy };
  }

  register(u: Pick<Unit, 'id' | 'name' | 'kind' | 'site' | 'env' | 'publicKeyPem'>): Unit {
    const unit: Unit = {
      ...u, lastCtr: -1, lastSeen: this.now(), interval: 120, channel: '',
      state: 'Normal', reason: '', latched: false, noise: false, neighborMissing: false, armed: true, tamper: 0,
    };
    this.units.set(u.id, unit);
    this.emit('unit', unit);
    return unit;
  }

  /** Gjenoppretter fra lagret tilstand. Enhetene får ny frist fra nå, slik at omstart ikke gir alarm. */
  restore(units: Unit[], cases: AlarmCase[], fences: Geofence[] = []): void {
    this.fences = new Map(fences.map(f => [f.id, f]));
    const t = this.now();
    this.units = new Map(units.map(u => [u.id, { ...u, lastSeen: Math.max(u.lastSeen, t) }]));
    this.cases = cases;
    for (const c of cases) { const n = Number(c.id.slice(2)); if (n > this.caseNo) this.caseNo = n; }
  }

  // ---------- geofence ----------
  setFence(f: Geofence): void {
    this.fences.set(f.id, f);
    this.log(`Geofence «${f.name}» for ${f.site} lagret (${f.polygon.length} punkter, buffer ${f.bufferM} m).`);
    for (const u of this.units.values()) if (u.site === f.site && u.pos) this.checkGeo(u);
    this.emit('fence', f);
  }
  removeFence(id: string): void {
    const f = this.fences.get(id); if (!f) throw new Error(`Ukjent gjerde ${id}`);
    this.fences.delete(id); this.log(`Geofence «${f.name}» slettet.`); this.emit('fence', { id, deleted: true });
  }

  /** Inne hvis innenfor ett av anleggets gjerder. Krever to posisjoner på rad utenfor før enheten regnes som ute. */
  private checkGeo(u: Unit): void {
    const fences = [...this.fences.values()].filter(f => f.site === u.site);
    if (!u.pos || !fences.length) { u.geo = 'ukjent'; return; }
    const res = fences.map(f => classify(u.pos!, f));
    const best = res.reduce((a, b) => (a.distM <= b.distM ? a : b));
    const state: GeoState = res.some(r => r.state === 'inne') ? 'inne' : res.some(r => r.state === 'usikker') ? 'usikker' : 'ute';
    u.geoDistM = Math.round(best.distM);
    const was = u.geo;
    if (state === 'ute') {
      u.geoOutCount = (u.geoOutCount ?? 0) + 1;
      if (u.geoOutCount < 2 || was === 'ute') { if (was !== 'ute') u.geo = 'usikker'; return; }
      u.geo = 'ute';
      const text = `Har forlatt ${u.site} (${u.geoDistM} m utenfor gjerdet)`;
      if (u.armed) this.raise(u, 1, 'GF', text);
      else { this.log(`${u.name}: ${text}, i arbeidstid (avarmert).`); this.emit('notify', { level: 'forvarsel', unitId: u.id, text: `${u.name}: ${text}` }); }
    } else {
      u.geoOutCount = 0;
      if (state === 'inne' && was === 'ute') this.log(`${u.name} er tilbake innenfor gjerdet.`);
      u.geo = state;
    }
  }

  setEnv(id: string, env: EnvProfile): void {
    const u = this.mustUnit(id); u.env = env;
    this.log(`Miljøprofil for ${u.name} satt til ${env}.`); this.emit('unit', u);
  }

  /** Kalles for hver melding som har gyldig signatur og ny teller. */
  accept(msg: Message): { newInterval?: number } {
    const u = this.mustUnit(msg.id);
    const t = this.now();
    u.lastCtr = msg.ctr; u.lastSeen = t;
    if (msg.iv) u.interval = msg.iv;
    if (msg.rf?.ch) u.channel = msg.rf.ch;
    if (msg.pos) { u.pos = { ...msg.pos, t }; }
    let freshTamper = 0;
    if (msg.st) {
      if (msg.st.bat !== undefined) u.battery = msg.st.bat;
      if (msg.st.ext !== undefined) u.extPower = msg.st.ext;
      if (msg.st.armed !== undefined) u.armed = msg.st.armed;
      if (msg.st.tamper !== undefined) {
        freshTamper = msg.st.tamper & ~u.tamper;
        u.tamper = msg.st.tamper;
        for (const [bit, text] of TAMPER_TEXT) if (freshTamper & bit) this.raise(u, 1, 'TA', text);
      }
    }
    if (msg.pos) this.checkGeo(u);
    switch (msg.type) {
      case 'hb':
        u.neighborMissing = false;
        if (msg.rf?.noise && !u.noise) this.log(`${u.name} melder høyt støynivå. Mulig jammer i nærheten.`);
        u.noise = !!msg.rf?.noise;
        if (!u.latched && u.state !== 'Normal') this.setState(u, 'Normal', '', `${u.name} er hørt igjen.`);
        break;
      case 'alarm':
        // Sabotasje som allerede er meldt via tamper-bitene gir ikke en sak til.
        if (msg.ev && !(msg.ev.code === 'TA' && freshTamper)) this.raise(u, msg.ev.code === 'XT' ? 3 : 1, msg.ev.code, msg.ev.text || 'Alarm fra enheten');
        break;
      case 'report':
        if (msg.tgt && this.units.has(msg.tgt)) {
          const v = this.units.get(msg.tgt)!;
          const first = !v.neighborMissing;
          v.neighborMissing = true;
          if (first) this.log(`${u.name} melder at ${v.name} er borte fra LoRa-nettet${msg.rf?.noise ? ' og at støyen er høy' : ''}.`);
        }
        break;
      case 'info':
        this.info(u, msg.ev?.text || 'Melding fra enheten');
        break;
    }
    this.emit('unit', u);
    return {};
  }

  /** Forvarsel behandles etter miljøprofil: skog varsler, by logger bare. */
  private info(u: Unit, text: string): void {
    if (u.env === 'by') this.log(`${u.name}: ${text} (by-profil, logges bare).`);
    else this.emit('notify', { level: 'forvarsel', unitId: u.id, text: `${u.name}: ${text}` }), this.log(`Forvarsel ${u.name}: ${text}.`);
  }

  /** Kjøres jevnlig (f.eks. hvert sekund). */
  tick(): void {
    const t = this.now();
    for (const u of this.units.values()) {
      if (u.latched) continue;
      const since = t - u.lastSeen, m = since / (u.interval * 1.1 + 10);
      if (m < 1) continue;
      const ind = u.neighborMissing || u.noise;
      if (m >= 2 || (ind && m >= 1.2)) {
        const why = `Ingen heartbeat på ${Math.round(since)} s` + (u.neighborMissing ? ', naboene melder at enheten er borte' : '') + (u.noise && !u.neighborMissing ? ', støy meldt før stillhet' : '');
        this.setState(u, 'Alarm', why);
        u.latched = true;
        this.openCase(u, 1, 'YC', why);
      } else {
        const st: UnitState = ind ? 'Mistenkelig' : 'Forsinket';
        if (u.state !== st) this.setState(u, st, ind ? 'Heartbeat mangler, og det er tegn til jamming' : 'Én heartbeat mangler');
      }
    }
    for (const c of this.cases) {
      if (c.state === 'Ny' && c.escalateAt !== undefined && t >= c.escalateAt) {
        c.escalateAt = undefined;
        if (this.policy.arcEnabled) { c.state = 'Videresendt'; this.caseEvent(c, 'Ingen tok saken. Sendt til alarmstasjon.'); }
        else { this.caseEvent(c, 'Ingen tok saken. Varsler neste på ringelisten (SMS og taleanrop).'); this.emit('notify', { level: 'eskalering', caseId: c.id }); }
        this.emit('case', c);
      }
    }
  }

  private raise(u: Unit, prio: 1 | 2 | 3, code: EventCode, text: string): void {
    if (prio === 1) { this.setState(u, 'Alarm', text); u.latched = true; }
    this.openCase(u, prio, code, text);
  }

  private openCase(u: Unit, prio: 1 | 2 | 3, code: EventCode, title: string): AlarmCase {
    const t = this.now();
    // Samme enhet og samme tittel mens saken er åpen: legg til hendelse i stedet for ny sak.
    const open = this.cases.find(c => c.unitId === u.id && c.title === title && c.state !== 'Avsluttet');
    if (open) { this.caseEvent(open, 'Gjentatt melding'); return open; }
    const c: AlarmCase = {
      id: `A-${++this.caseNo}`, unitId: u.id, site: u.site, prio, code, title, state: 'Ny', created: t,
      escalateAt: prio === 1 ? t + this.policy.escalateAfterSec : undefined,
      events: [{ t, text: `Mottatt via ${u.channel || 'ukjent kanal'}` }],
    };
    this.cases.unshift(c);
    this.log(`ALARM ${u.name}: ${title}`);
    this.emit('case', c);
    this.emit('notify', { level: prio === 1 ? 'alarm' : 'varsel', caseId: c.id, unitId: u.id, text: `${u.name}: ${title}` });
    return c;
  }

  // ---------- handlinger fra dashboard og app ----------
  take(caseId: string, who: string): AlarmCase {
    const c = this.mustCase(caseId);
    if (c.state === 'Ny') { c.state = 'Behandles'; c.owner = who; c.escalateAt = undefined; this.caseEvent(c, `Tatt av ${who}`); }
    this.emit('case', c); return c;
  }
  close(caseId: string, who: string, result: string, falseAlarm = false): AlarmCase {
    const c = this.mustCase(caseId);
    c.state = 'Avsluttet'; c.escalateAt = undefined; c.result = (falseAlarm ? 'Falsk alarm: ' : '') + result;
    this.caseEvent(c, `Avsluttet av ${who}: ${c.result}`);
    // Når ingen åpne saker gjenstår for enheten, kan tilstanden frigis.
    const u = this.units.get(c.unitId);
    if (u && !this.cases.some(x => x.unitId === u.id && x.state !== 'Avsluttet')) {
      u.latched = false; this.setState(u, 'Normal', '', `${u.name} er kvittert og tilbake til normal.`);
    }
    this.emit('case', c); return c;
  }

  // ---------- hjelpere ----------
  private setState(u: Unit, s: UnitState, reason: string, logText?: string): void {
    if (u.state === s && u.reason === reason) return;
    u.state = s; u.reason = reason;
    this.log(logText || `${u.name}: ${s.toLowerCase()}${reason ? '. ' + reason : ''}.`);
    this.emit('unit', u);
  }
  private caseEvent(c: AlarmCase, text: string): void { c.events.push({ t: this.now(), text }); }
  log(text: string): void { this.emit('log', { t: this.now(), text }); }
  private mustUnit(id: string): Unit { const u = this.units.get(id); if (!u) throw new Error(`Ukjent enhet ${id}`); return u; }
  private mustCase(id: string): AlarmCase { const c = this.cases.find(x => x.id === id); if (!c) throw new Error(`Ukjent sak ${id}`); return c; }
}
