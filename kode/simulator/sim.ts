// Enhetssimulator: virtuelle alarmenheter som snakker med plattformen over samme protokoll som ekte enheter.
//   node simulator/sim.ts                 interaktiv, skriv "hjelp"
//   node simulator/sim.ts --auto          kjører et fast scenario og avslutter med feilkode ved avvik
// Miljøvariabler: GVT_URL (standard http://localhost:8080), GVT_ADMIN_TOKEN (standard admin-dev)

import { createInterface } from 'node:readline';
import { createPublicKey, type KeyObject } from 'node:crypto';
import { newKeyPair, sealMessage, openEnvelope, verify, TAMPER, type Message, type EnvProfile, type Channel } from '../shared/protocol.ts';
import { decode } from '../shared/cbor.ts';

const URL_ = process.env.GVT_URL ?? 'http://localhost:8080';
const ADMIN = process.env.GVT_ADMIN_TOKEN ?? 'admin-dev';
const args = process.argv.slice(2);
const AUTO = args.includes('--auto');
const INTERVAL = Number(args.find(a => a.startsWith('--interval='))?.split('=')[1] ?? (AUTO ? 2 : 20));
const RUN = Math.random().toString(36).slice(2, 6).toUpperCase();

interface Dev {
  n: number; id: string; name: string; site: string; env: EnvProfile; kind: string;
  key: KeyObject; ctr: number; tamper: number;
  jammed: boolean; silent: boolean; noise: boolean; armed: boolean;
  lat: number; lon: number;
  lastSealed?: Uint8Array; timer?: NodeJS.Timeout;
}

// Eksempelanlegg (fiktive koordinater) og et kvadratisk gjerde på ±150 m rundt sentrum.
const SITES: Record<string, { lat: number; lon: number }> = {
  'Anlegg Nord': { lat: 59.95, lon: 10.60 }, 'Skogsvei 4': { lat: 60.40, lon: 9.90 }, 'Oslo sentrum': { lat: 59.9127, lon: 10.7461 },
};
const M_LAT = 1 / 111320;                                   // grader per meter nord–sør
const mLon = (lat: number) => 1 / (111320 * Math.cos(lat * Math.PI / 180));

const FLEET: [string, string, EnvProfile, string][] = [
  ['Gravemaskin 1', 'Anlegg Nord', 'landlig', 'maskin'],
  ['Gravemaskin 2', 'Anlegg Nord', 'landlig', 'maskin'],
  ['Hjullaster', 'Anlegg Nord', 'landlig', 'maskin'],
  ['Traktor', 'Skogsvei 4', 'skog', 'maskin'],
  ['Verktøycontainer', 'Anlegg Nord', 'landlig', 'brakke'],
  ['Minigraver', 'Oslo sentrum', 'by', 'maskin'],
];

let platformKey: KeyObject;
const devs: Dev[] = [];
let failures = 0;
const out = (s: string) => console.log(s);
const fail = (s: string) => { failures++; console.log('  FEIL: ' + s); };

async function api(path: string, method = 'GET', body?: unknown) {
  const r = await fetch(URL_ + path, { method, headers: { authorization: `Bearer ${ADMIN}`, 'content-type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
  const text = await r.text();
  return { status: r.status, data: text ? (() => { try { return JSON.parse(text); } catch { return text; } })() : undefined };
}

async function post(b: Uint8Array): Promise<{ status: number; ack?: Uint8Array }> {
  const r = await fetch(URL_ + '/v1/ingest', { method: 'POST', headers: { 'content-type': 'application/cbor' }, body: b });
  return { status: r.status, ack: r.ok ? new Uint8Array(await r.arrayBuffer()) : undefined };
}

/** Kontrollerer at kvitteringen er signert av plattformen og gjelder riktig teller. */
function checkAck(ack: Uint8Array, ctr: number): boolean {
  const { payload, signature } = openEnvelope(ack);
  if (!verify(payload, signature, platformKey)) return false;
  const m = decode(payload) as Map<number, unknown>;
  return m.get(1) === 'ack' && m.get(2) === ctr;
}

function channel(d: Dev): Channel { return d.jammed ? 'LoRa' : 'LTE-M'; }

async function send(d: Dev, partial: Partial<Message>, quiet = false): Promise<number> {
  const msg: Message = {
    v: 1, id: d.id, ctr: ++d.ctr, ts: Math.floor(Date.now() / 1000), type: 'hb', iv: INTERVAL,
    st: { bat: 96, ext: true, tamper: d.tamper, armed: d.armed }, rf: { ch: channel(d), rsrp: -95, noise: d.noise },
    pos: { lat: d.lat, lon: d.lon, acc: 5 }, ...partial,
  };
  const sealed = sealMessage(msg, d.key);
  d.lastSealed = sealed;
  const r = await post(sealed);
  if (r.status === 200 && r.ack && !checkAck(r.ack, msg.ctr)) fail(`Kvittering til ${d.name} har ugyldig signatur`);
  if (!quiet) out(`  ${d.name}: ${msg.type}${msg.ev ? ' ' + msg.ev.code : ''} ctr=${msg.ctr} -> ${r.status}`);
  return r.status;
}

/** Heartbeat med tilfeldig forskyvning, slik at enhetene ikke sender samtidig. */
function schedule(d: Dev) {
  clearTimeout(d.timer);
  const jitter = INTERVAL * (0.9 + Math.random() * 0.1);
  d.timer = setTimeout(async () => {
    if (!d.jammed && !d.silent) await send(d, { type: 'hb' }, true).catch(e => out(`  ${d.name}: ${e.message}`));
    // Naboene merker at en jammet enhet er borte fra LoRa og melder fra.
    if (!d.jammed) for (const v of devs) if (v.jammed && v.site === d.site && v !== d) await send(d, { type: 'report', tgt: v.id, rf: { ch: 'LTE-M', noise: true } }, true).catch(() => {});
    schedule(d);
  }, jitter * 1000);
}

async function setupFences() {
  for (const [site, c] of Object.entries(SITES)) {
    const id = `${site.replace(/\W+/g, '-').toLowerCase()}-${RUN}`.slice(0, 40);
    const dl = 150 * M_LAT, dn = 150 * mLon(c.lat);
    const polygon = [{ lat: c.lat - dl, lon: c.lon - dn }, { lat: c.lat - dl, lon: c.lon + dn }, { lat: c.lat + dl, lon: c.lon + dn }, { lat: c.lat + dl, lon: c.lon - dn }];
    const r = await api('/api/geofences', 'POST', { id, site, name: `${site} (sim)`, polygon, bufferM: 25 });
    if (r.status !== 201) throw new Error(`Gjerde for ${site} feilet: ${r.status} ${JSON.stringify(r.data)}`);
  }
}

async function setup() {
  const r = await fetch(URL_ + '/api/platform-key');
  if (!r.ok) throw new Error(`Får ikke kontakt med plattformen på ${URL_}`);
  platformKey = createPublicKey(await r.text());
  await setupFences();
  for (const [i, [name, site, env, kind]] of FLEET.entries()) {
    const kp = newKeyPair();
    const c = SITES[site];
    const d: Dev = { n: i + 1, id: `SIM-${RUN}-${i + 1}`, name, site, env, kind, key: kp.privateKey, ctr: 0, tamper: 0, jammed: false, silent: false, noise: false, armed: true,
      lat: c.lat + (Math.random() - 0.5) * 120 * M_LAT, lon: c.lon + (Math.random() - 0.5) * 120 * mLon(c.lat) };
    const res = await api('/api/devices', 'POST', { id: d.id, name, site, env, kind, publicKeyPem: kp.publicKeyPem });
    if (res.status !== 201) throw new Error(`Registrering av ${name} feilet: ${res.status} ${JSON.stringify(res.data)}`);
    devs.push(d);
    await send(d, { type: 'hb' }, true);
    schedule(d);
  }
  out(`${devs.length} enheter registrert og sender heartbeat hvert ${INTERVAL}. sekund.`);
}

// ---------- kommandoer ----------
const TAMPER_NAMES: Record<string, number> = { lokk: TAMPER.lid, folie: TAMPER.mesh, antenne: TAMPER.antenna, sloyfe: TAMPER.gpsLoop, strom: TAMPER.power, kamera: TAMPER.camera, can: TAMPER.canGps };

async function command(line: string): Promise<void> {
  const [cmd, a, ...rest] = line.trim().split(/\s+/);
  const d = devs[Number(a) - 1];
  const needDev = () => { if (!d) throw new Error('Oppgi enhetsnummer, se "liste"'); return d; };
  switch (cmd) {
    case '': return;
    case 'hjelp': case 'help':
      out(`Kommandoer:
  liste                    vis enhetene
  jam <n>                  enheten jammes: slutter å sende, naboene melder den borte
  slutt <n>                avslutt jamming
  stille <n>               enheten slutter å sende uten tegn til jamming (f.eks. strømbrudd)
  stoy <n>                 enheten melder høy støy (forvarsel om jammer)
  sabotasje <n> <type>     type: ${Object.keys(TAMPER_NAMES).join(', ')}
  person <n>               radar og kamera ser person i kjernesonen
  forvarsel <n> <tekst>    info-melding, håndteres etter miljøprofil
  gjenta <n>               send siste melding på nytt (skal avvises)
  forfalsk <n>             send melding med feil nøkkel (skal avvises)
  flytt <n> <meter>        flytt enheten mot nord (f.eks. 400 = ut av anlegget)
  avarmer <n> / armer <n>  arbeidstid eller natt for enheten
  avslutt`); return;
    case 'liste': for (const x of devs) out(`  ${x.n}. ${x.name.padEnd(18)} ${x.id}  ${x.site} / ${x.env}${x.jammed ? '  JAMMET' : ''}${x.silent ? '  STILLE' : ''}`); return;
    case 'jam': needDev().jammed = true; d.noise = true; await send(d, { type: 'hb', rf: { ch: 'LTE-M', noise: true } }); out(`  ${d.name} jammes nå.`); return;
    case 'slutt': needDev().jammed = false; d.silent = false; d.noise = false; await send(d, { type: 'hb' }); return;
    case 'stille': needDev().silent = true; out(`  ${d.name} er stille.`); return;
    case 'stoy': needDev().noise = true; await send(d, { type: 'hb' }); return;
    case 'sabotasje': {
      const bit = TAMPER_NAMES[rest[0] ?? '']; if (!bit) throw new Error('Ukjent sabotasjetype');
      needDev().tamper |= bit; await send(d, { type: 'alarm', ev: { code: 'TA', text: `Sabotasje: ${rest[0]}` } }); return;
    }
    case 'flytt': {
      const m = Number(rest[0] ?? 400); needDev().lat += m * M_LAT;
      await send(d, { type: 'hb' }); await send(d, { type: 'hb' });
      out(`  ${d.name} flyttet ${m} m mot nord.`); return;
    }
    case 'avarmer': needDev().armed = false; await send(d, { type: 'hb' }); return;
    case 'armer': needDev().armed = true; await send(d, { type: 'hb' }); return;
    case 'person': await send(needDev(), { type: 'alarm', ev: { code: 'BA', zone: 1, text: 'Person ved maskinen (radar og kamera)', img: true } }); return;
    case 'forvarsel': await send(needDev(), { type: 'info', ev: { code: 'OP', text: rest.join(' ') || 'Bevegelse i ytre sone' } }); return;
    case 'gjenta': {
      if (!needDev().lastSealed) throw new Error('Ingen melding å gjenta');
      const r = await post(d.lastSealed!); out(`  Gjentatt melding fra ${d.name} -> ${r.status} ${r.status === 409 ? '(avvist, riktig)' : '(FORVENTET 409)'}`); return;
    }
    case 'forfalsk': {
      const fake = newKeyPair().privateKey;
      const msg: Message = { v: 1, id: needDev().id, ctr: d.ctr + 100, ts: Math.floor(Date.now() / 1000), type: 'hb', iv: INTERVAL };
      const r = await post(sealMessage(msg, fake)); out(`  Forfalsket melding for ${d.name} -> ${r.status} ${r.status === 401 ? '(avvist, riktig)' : '(FORVENTET 401)'}`); return;
    }
    case 'avslutt': case 'exit': process.exit(0);
    default: throw new Error(`Ukjent kommando "${cmd}". Skriv "hjelp".`);
  }
}

// ---------- fast scenario for test ----------
const sleep = (s: number) => new Promise(r => setTimeout(r, s * 1000));
async function waitFor(desc: string, f: () => Promise<boolean>, sec: number) {
  const end = Date.now() + sec * 1000;
  while (Date.now() < end) { if (await f()) { out(`  OK: ${desc}`); return; } await sleep(0.5); }
  fail(`${desc} (ventet ${sec} s)`);
}
const units = async () => (await api('/api/units')).data as any[];
const cases = async () => (await api('/api/alarms')).data as any[];
const unitOf = async (d: Dev) => (await units()).find(u => u.id === d.id);

async function auto() {
  out('\n1. Normal drift');
  await sleep(INTERVAL * 1.5);
  await waitFor('alle enheter er Normal', async () => (await units()).filter(u => u.id.includes(RUN)).every(u => u.state === 'Normal'), 5);

  out('\n2. Sikkerhet: gjentatt og forfalsket melding');
  const d1 = devs[0];
  const replay = await post(d1.lastSealed!);
  replay.status === 409 ? out('  OK: gjentatt melding avvist (409)') : fail(`gjentatt melding ga ${replay.status}`);
  const forged = await post(sealMessage({ v: 1, id: d1.id, ctr: d1.ctr + 50, ts: 0, type: 'alarm', ev: { code: 'BA' } }, newKeyPair().privateKey));
  forged.status === 401 ? out('  OK: forfalsket signatur avvist (401)') : fail(`forfalsket melding ga ${forged.status}`);
  const garbage = await post(Uint8Array.from([1, 2, 3]));
  garbage.status === 400 ? out('  OK: ødelagt melding avvist (400)') : fail(`ødelagt melding ga ${garbage.status}`);

  out('\n3. Sabotasje: kabelsløyfen rundt GPS-utstyret kuttes på Gravemaskin 2');
  await command('sabotasje 2 sloyfe');
  await waitFor('Gravemaskin 2 er i Alarm med sak prioritet 1', async () => (await unitOf(devs[1]))?.state === 'Alarm' && (await cases()).some(c => c.unitId === devs[1].id && c.prio === 1 && c.code === 'TA'), 3);

  out('\n4. Forvarsel i by-profil logges bare, i skog varsles det');
  await command('forvarsel 6 Bevegelse i ytre sone');
  await command('forvarsel 4 Bevegelse i ytre sone');
  await waitFor('ingen sak for Minigraver (by)', async () => !(await cases()).some(c => c.unitId === devs[5].id), 2);

  out('\n5. Jamming av Hjullaster: stillhet + naboer melder den borte = alarm');
  await command('jam 3');
  await waitFor('Hjullaster blir Mistenkelig eller Alarm', async () => ['Mistenkelig', 'Alarm'].includes((await unitOf(devs[2]))?.state), INTERVAL * 1.1 + 15);
  await waitFor('Hjullaster går i Alarm med sak YC', async () => (await cases()).some(c => c.unitId === devs[2].id && c.code === 'YC'), INTERVAL * 2.5 + 25);

  out('\n6. Operatør tar og lukker saken for Gravemaskin 2');
  const c = (await cases()).find(x => x.unitId === devs[1].id);
  const ot = { authorization: 'Bearer ' + (process.env.GVT_OPERATOR_TOKEN ?? 'operator-dev'), 'content-type': 'application/json' };
  await fetch(`${URL_}/api/alarms/${c.id}/take`, { method: 'POST', headers: ot, body: JSON.stringify({ who: 'Testoperatør' }) });
  devs[1].tamper = 0; // sløyfen er reparert
  await fetch(`${URL_}/api/alarms/${c.id}/close`, { method: 'POST', headers: ot, body: JSON.stringify({ who: 'Testoperatør', result: 'Sløyfe reparert' }) });
  await waitFor('Gravemaskin 2 tilbake til Normal', async () => (await unitOf(devs[1]))?.state === 'Normal', 3);

  out('\n7. Geofence: Gravemaskin 1 kjøres ut i arbeidstid (avarmert), Verktøycontainer flyttes om natten');
  await command('avarmer 1');
  await command('flytt 1 400');
  await waitFor('ingen sak for Gravemaskin 1 (avarmert gir bare forvarsel)', async () => (await unitOf(devs[0]))?.geo === 'ute' && !(await cases()).some(c => c.unitId === devs[0].id && c.code === 'GF'), 3);
  await command('flytt 5 300');
  await waitFor('Verktøycontainer gir geofence-alarm (GF)', async () => (await cases()).some(c => c.unitId === devs[4].id && c.code === 'GF' && c.prio === 1), 3);
  await command('flytt 1 -400');
  await waitFor('Gravemaskin 1 er tilbake innenfor', async () => (await unitOf(devs[0]))?.geo === 'inne', 3);

  out('\n8. Rolle: operatør kan ikke registrere enheter');
  const r = await fetch(URL_ + '/api/devices', { method: 'POST', headers: ot, body: '{}' });
  r.status === 403 ? out('  OK: operatør får 403') : fail(`operatør fikk ${r.status}`);

  out(failures ? `\n${failures} avvik.` : '\nAlle kontroller bestått.');
  process.exit(failures ? 1 : 0);
}

// ---------- start ----------
setup().then(() => {
  if (AUTO) return auto();
  out('Skriv "hjelp" for kommandoer.');
  const rl = createInterface({ input: process.stdin, prompt: 'sim> ' });
  rl.prompt();
  rl.on('line', l => command(l).catch(e => out('  ' + e.message)).finally(() => rl.prompt()));
}).catch(e => { console.error(e.message); process.exit(2); });
