import { test } from 'node:test';
import assert from 'node:assert/strict';
import { RuleEngine } from '../platform/rules.ts';
import { TAMPER, type Message } from '../shared/protocol.ts';

function setup(env: 'skog' | 'landlig' | 'by' = 'landlig', arc = false) {
  let t = 1000; const events: [string, any][] = [];
  const e = new RuleEngine(() => t, (k, d) => events.push([k, d]), { arcEnabled: arc });
  for (const id of ['A1', 'A2']) e.register({ id, name: id, kind: 'maskin', site: 'S', env, publicKeyPem: '' });
  let ctr = 0;
  const hb = (id: string, extra: Partial<Message> = {}) => e.accept({ v: 1, id, ctr: ++ctr, ts: t, type: 'hb', iv: 120, ...extra });
  return { e, events, hb, adv: (s: number) => { t += s; e.tick(); }, u: (id: string) => e.units.get(id)! };
}

test('stillhet: Forsinket etter ett intervall, Alarm etter to', () => {
  const { e, hb, adv, u } = setup();
  hb('A1'); hb('A2');
  adv(100); assert.equal(u('A1').state, 'Normal');
  adv(50); assert.equal(u('A1').state, 'Forsinket');
  adv(150); assert.equal(u('A1').state, 'Alarm');
  assert.equal(e.cases[0].code, 'YC');
});

test('heartbeat i tide holder enheten Normal', () => {
  const { hb, adv, u } = setup();
  for (let i = 0; i < 10; i++) { hb('A1'); adv(118); }
  assert.equal(u('A1').state, 'Normal');
});

test('jamming: naboens melding gir raskere alarm', () => {
  const { e, hb, adv, u } = setup();
  hb('A1', { rf: { noise: true } });
  e.accept({ v: 1, id: 'A2', ctr: 999, ts: 0, type: 'report', tgt: 'A1' });
  adv(145); assert.equal(u('A1').state, 'Mistenkelig');
  adv(30); assert.equal(u('A1').state, 'Alarm'); // 1,2 × (120·1,1+10) ≈ 170 s, mot 284 s uten tegn til jamming
});

test('sabotasje gir én sak med prioritet 1, også når enheten sender alarm samtidig', () => {
  const { e, hb, u } = setup();
  hb('A1', { type: 'alarm', st: { tamper: TAMPER.gpsLoop }, ev: { code: 'TA' } });
  assert.equal(u('A1').state, 'Alarm');
  assert.equal(e.cases.length, 1);
  assert.equal(e.cases[0].prio, 1);
});

test('forvarsel: by logger, skog varsler', () => {
  const by = setup('by'); by.hb('A1', { type: 'info', ev: { code: 'OP', text: 'bevegelse' } });
  assert.ok(!by.events.some(([k]) => k === 'notify'));
  const skog = setup('skog'); skog.hb('A1', { type: 'info', ev: { code: 'OP', text: 'bevegelse' } });
  assert.ok(skog.events.some(([k, d]) => k === 'notify' && d.level === 'forvarsel'));
});

test('eskalering uten alarmstasjon: ringeliste. Med alarmstasjon: videresendt', () => {
  for (const arc of [false, true]) {
    const { e, hb, adv } = setup('landlig', arc);
    hb('A1', { type: 'alarm', ev: { code: 'BA', text: 'Person' } });
    adv(181);
    const c = e.cases[0];
    if (arc) assert.equal(c.state, 'Videresendt');
    else { assert.equal(c.state, 'Ny'); assert.match(c.events.at(-1)!.text, /ringelisten/); }
  }
});

test('tatt sak eskaleres ikke, og lukking frigir enheten', () => {
  const { e, hb, adv, u } = setup();
  hb('A1', { type: 'alarm', ev: { code: 'BA', text: 'Person' } });
  e.take(e.cases[0].id, 'Kari');
  adv(200);
  assert.equal(e.cases[0].state, 'Behandles');
  e.close(e.cases[0].id, 'Kari', 'Elg', true);
  assert.equal(u('A1').state, 'Normal');
  assert.match(e.cases[0].result!, /^Falsk alarm/);
});

test('geofence: ute om natten gir alarm, i arbeidstid bare forvarsel', () => {
  const { e, events, hb, u } = setup();
  const c = { lat: 59.95, lon: 10.60 }, dl = 150 / 111320, dn = 150 / (111320 * Math.cos(c.lat * Math.PI / 180));
  e.setFence({ id: 'f1', site: 'S', name: 'S', bufferM: 25, polygon: [{ lat: c.lat - dl, lon: c.lon - dn }, { lat: c.lat - dl, lon: c.lon + dn }, { lat: c.lat + dl, lon: c.lon + dn }, { lat: c.lat + dl, lon: c.lon - dn }] });
  const at = (m: number) => ({ lat: c.lat + m / 111320, lon: c.lon, acc: 5 });
  hb('A1', { pos: at(0) }); assert.equal(u('A1').geo, 'inne');
  hb('A1', { pos: at(400) }); assert.equal(u('A1').geo, 'usikker');      // én posisjon ute er ikke nok
  hb('A1', { pos: at(400) }); assert.equal(u('A1').geo, 'ute');
  assert.ok(e.cases.some(x => x.code === 'GF' && x.prio === 1));
  hb('A2', { pos: at(0), st: { armed: false } });
  hb('A2', { pos: at(400) }); hb('A2', { pos: at(400) });
  assert.equal(u('A2').geo, 'ute');
  assert.ok(!e.cases.some(x => x.unitId === 'A2'));
  assert.ok(events.some(([k, d]) => k === 'notify' && d.level === 'forvarsel' && d.unitId === 'A2'));
  hb('A2', { pos: at(160) }); assert.equal(u('A2').geo, 'inne');       // innenfor bufferen på 25 m
});
