// Varde (prosjekt GPS Vs Tyv) – plattformkjerne, første versjon.
// Ett program med roller. Ingen eksterne avhengigheter, kjører på Node 22 eller nyere:
//   node platform/server.ts
//
// Grensesnitt:
//   POST /v1/ingest                 Enhetene. CBOR-konvolutt, signert. Svar: signert kvittering (CBOR).
//   GET  /api/platform-key          Plattformens offentlige nøkkel (enhetene får den ved produksjon).
//   POST /api/devices               Rolle admin. Registrerer enhet med offentlig nøkkel.
//   GET  /api/units | /api/alarms | /api/log
//   POST /api/alarms/:id/take       Rolle operatør. Body {who}
//   POST /api/alarms/:id/close      Rolle operatør. Body {who, result, falseAlarm}
//   POST /api/units/:id/env         Rolle admin. Body {env: skog|landlig|by}
//   GET  /api/stream?token=…        Live-hendelser (Server-Sent Events)
//   GET  /                          Dashboard
//
// Roller i første versjon: admin og operatør, med hvert sitt token (GVT_ADMIN_TOKEN, GVT_OPERATOR_TOKEN).
// Plattformen starter ikke uten dem. admin-dev/operator-dev virker bare med --dev (npm run dev).
// I drift: innlogging med BankID/Entra ID, roller per kunde og anlegg, se designdokumentet.

import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { readFileSync, existsSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { createPrivateKey, createPublicKey, generateKeyPairSync, timingSafeEqual, type KeyObject } from 'node:crypto';
import { openEnvelope, decodePayload, verify, loadPublicKey, sealAck, type EnvProfile } from '../shared/protocol.ts';
import { RuleEngine, type Unit } from './rules.ts';
import { Store } from './store.ts';
import { formatDc09 } from './dc09.ts';
import { validateFence, type Geofence } from './geofence.ts';

const here = dirname(fileURLToPath(import.meta.url));

export interface ServerOptions {
  port?: number;
  adminToken?: string;
  operatorToken?: string;
  dev?: boolean;              // utviklingsmodus: tillater admin-dev/operator-dev. Aldri i drift.
  dataFile?: string;          // JSON-fil for tilstand, utelatt = bare i minnet
  keyFile?: string;           // plattformens private nøkkel (PEM), lages hvis den mangler
  now?: () => number;         // sekunder, kan overstyres i tester
  tickMs?: number;
  arcEnabled?: boolean;
  escalateAfterSec?: number;
  quiet?: boolean;
}

// Token-krav: i drift må begge settes, være minst 32 tegn, ulike og ikke utviklingsverdiene.
// Uten dette nekter plattformen å starte (fail closed). Utviklingsmodus må slås på eksplisitt.
export const DEV_TOKENS = { admin: 'admin-dev', operator: 'operator-dev' } as const;
export const MIN_TOKEN_LEN = 32;
export function resolveTokens(o: { adminToken?: string; operatorToken?: string; dev?: boolean }, env: Record<string, string | undefined> = process.env) {
  const dev = o.dev ?? env.GVT_DEV === '1';
  const admin = o.adminToken ?? env.GVT_ADMIN_TOKEN ?? (dev ? DEV_TOKENS.admin : undefined);
  const operator = o.operatorToken ?? env.GVT_OPERATOR_TOKEN ?? (dev ? DEV_TOKENS.operator : undefined);
  if (!admin || !operator) throw new Error('GVT_ADMIN_TOKEN og GVT_OPERATOR_TOKEN må settes. Lokalt: start med --dev (npm run dev).');
  if (!dev) {
    const weak = (t: string) => t.length < MIN_TOKEN_LEN || t === DEV_TOKENS.admin || t === DEV_TOKENS.operator;
    if (weak(admin) || weak(operator)) throw new Error(`Token må være minst ${MIN_TOKEN_LEN} tegn og ikke utviklingsverdiene. Lag et med: openssl rand -base64 32`);
    if (admin === operator) throw new Error('Admin-token og operatør-token må være ulike.');
  }
  return { admin, operator, dev };
}
const sameToken = (a: string, b: string) => { const x = Buffer.from(a), y = Buffer.from(b); return x.length === y.length && timingSafeEqual(x, y); };

export function startServer(o: ServerOptions = {}) {
  const tokens = resolveTokens(o);
  const adminToken = tokens.admin, operatorToken = tokens.operator;
  const now = o.now ?? (() => Date.now() / 1000);
  const say = (s: string) => { if (!o.quiet) console.log(s); };

  // ---------- plattformnøkkel ----------
  let platformKey: KeyObject;
  if (o.keyFile && existsSync(o.keyFile)) platformKey = createPrivateKey(readFileSync(o.keyFile, 'utf8'));
  else {
    platformKey = generateKeyPairSync('ec', { namedCurve: 'prime256v1' }).privateKey;
    if (o.keyFile) writeFileSync(o.keyFile, platformKey.export({ type: 'pkcs8', format: 'pem' }), { mode: 0o600 });
  }
  const platformPub = createPublicKey(platformKey).export({ type: 'spki', format: 'pem' }).toString();

  // ---------- hendelser ut (SSE, logg, varsling) ----------
  const clients = new Set<ServerResponse>();
  const log: { t: number; text: string }[] = [];
  const keys = new Map<string, KeyObject>();
  const store = new Store(o.dataFile);
  let dc09Seq = 0;

  const broadcast = (kind: string, data: unknown) => {
    const line = `event: ${kind}\ndata: ${JSON.stringify(data)}\n\n`;
    for (const c of clients) c.write(line);
  };
  const emit = (kind: string, data: unknown) => {
    if (kind === 'log') { log.unshift(data as { t: number; text: string }); if (log.length > 500) log.pop(); say(`[logg] ${(data as { text: string }).text}`); }
    if (kind === 'notify') notify(data as Record<string, unknown>);
    if (kind === 'case' && engine.policy.arcEnabled) {
      const c = data as { state: string; unitId: string; code: any; prio: number };
      if (c.state === 'Videresendt') say('[DC-09] ' + JSON.stringify(formatDc09({ seq: ++dc09Seq, account: c.unitId.replace(/\W/g, '').slice(-6), code: c.code === 'GF' ? 'BA' : c.code, time: new Date(now() * 1000) })));
    }
    broadcast(kind, kind === 'unit' ? publicUnit(data as Unit) : data);
    store.saveSoon(() => ({ units: [...engine.units.values()], cases: engine.cases, log, fences: [...engine.fences.values()] }));
  };

  // Varsling: i første versjon bare til konsoll og SSE. Leverandøren kopler på push (FCM/APNs), SMS og taleanrop.
  function notify(n: Record<string, unknown>) { say(`[varsel:${n.level}] ${n.text ?? n.caseId}`); }

  const engine = new RuleEngine(now, emit, { arcEnabled: o.arcEnabled ?? false, escalateAfterSec: o.escalateAfterSec ?? 180 });
  const snap = store.load();
  if (snap) { engine.restore(snap.units, snap.cases, snap.fences ?? []); log.push(...snap.log); }
  for (const u of engine.units.values()) keys.set(u.id, loadPublicKey(u.publicKeyPem));

  const ticker = setInterval(() => engine.tick(), o.tickMs ?? 1000);
  // Holder live-linjen åpen bak proxyer og lastbalanserere i skyen.
  const pinger = setInterval(() => { for (const c of clients) c.write(': ping\n\n'); }, 20000);

  // ---------- hjelpere ----------
  const MAX_BODY = 8 * 1024;
  function body(req: IncomingMessage): Promise<Buffer> {
    return new Promise((res, rej) => {
      const parts: Buffer[] = []; let n = 0;
      req.on('data', (d: Buffer) => { n += d.length; if (n > MAX_BODY) { rej(new HttpError(413, 'For stor melding')); req.destroy(); } else parts.push(d); });
      req.on('end', () => res(Buffer.concat(parts)));
      req.on('error', rej);
    });
  }
  async function json(req: IncomingMessage): Promise<any> {
    const b = await body(req);
    try { return b.length ? JSON.parse(b.toString('utf8')) : {}; } catch { throw new HttpError(400, 'Ugyldig JSON'); }
  }
  function role(req: IncomingMessage, url: URL): 'admin' | 'operator' | undefined {
    const h = req.headers.authorization?.replace(/^Bearer\s+/i, '') ?? url.searchParams.get('token') ?? '';
    if (sameToken(h, adminToken)) return 'admin';
    if (sameToken(h, operatorToken)) return 'operator';
    return undefined;
  }
  function need(r: ReturnType<typeof role>, min: 'admin' | 'operator') {
    if (!r) throw new HttpError(401, 'Mangler eller ugyldig token');
    if (min === 'admin' && r !== 'admin') throw new HttpError(403, 'Krever admin-rolle');
  }
  const send = (res: ServerResponse, code: number, data: unknown) => {
    res.writeHead(code, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
    res.end(JSON.stringify(data));
  };

  // ---------- mottak fra enheter ----------
  async function ingest(req: IncomingMessage, res: ServerResponse) {
    const raw = new Uint8Array(await body(req));
    let env, msg;
    try { env = openEnvelope(raw); msg = decodePayload(env.payload); }
    catch (e) { throw new HttpError(400, (e as Error).message); }
    const key = keys.get(msg.id);
    if (!key) { engine.log(`Melding fra ukjent enhet ${msg.id} avvist.`); throw new HttpError(404, 'Ukjent enhet'); }
    if (!verify(env.payload, env.signature, key)) {
      engine.log(`SIKKERHET: Ugyldig signatur på melding som utgir seg for å være ${msg.id}. Avvist.`);
      throw new HttpError(401, 'Ugyldig signatur');
    }
    const u = engine.units.get(msg.id)!;
    if (msg.ctr <= u.lastCtr) {
      engine.log(`SIKKERHET: Gjentatt melding (teller ${msg.ctr}, siste ${u.lastCtr}) fra ${u.name}. Avvist.`);
      throw new HttpError(409, 'Teller er ikke ny (gjentatt melding)');
    }
    const r = engine.accept(msg);
    const ack = sealAck(msg.ctr, Math.floor(now()), platformKey, r.newInterval);
    res.writeHead(200, { 'content-type': 'application/cbor' });
    res.end(Buffer.from(ack));
  }

  // ---------- ruter ----------
  const server = createServer(async (req, res) => {
    const url = new URL(req.url ?? '/', 'http://localhost');
    const p = url.pathname, m = req.method ?? 'GET';
    try {
      if (m === 'POST' && p === '/v1/ingest') return await ingest(req, res);
      if (m === 'GET' && (p === '/' || p === '/index.html')) {
        res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
        return res.end(readFileSync(join(here, '..', 'dashboard', 'index.html')));
      }
      if (m === 'GET' && p === '/api/platform-key') { res.writeHead(200, { 'content-type': 'text/plain' }); return res.end(platformPub); }
      if (m === 'GET' && p === '/api/health') return send(res, 200, { ok: true, units: engine.units.size });

      const r = role(req, url);
      if (m === 'GET' && p === '/api/stream') {
        need(r, 'operator');
        res.writeHead(200, { 'content-type': 'text/event-stream', 'cache-control': 'no-store', connection: 'keep-alive' });
        res.write(`event: hello\ndata: ${JSON.stringify({ role: r })}\n\n`);
        clients.add(res); req.on('close', () => clients.delete(res));
        return;
      }
      if (m === 'GET' && p === '/api/units') { need(r, 'operator'); return send(res, 200, [...engine.units.values()].map(publicUnit)); }
      if (m === 'GET' && p === '/api/alarms') { need(r, 'operator'); return send(res, 200, engine.cases); }
      if (m === 'GET' && p === '/api/log') { need(r, 'operator'); return send(res, 200, log.slice(0, 200)); }
      if (m === 'GET' && p === '/api/policy') { need(r, 'operator'); return send(res, 200, engine.policy); }
      if (m === 'GET' && p === '/api/geofences') { need(r, 'operator'); return send(res, 200, [...engine.fences.values()]); }
      if (m === 'POST' && p === '/api/geofences') {
        need(r, 'admin');
        const b = await json(req);
        const f: Geofence = { id: b.id, site: String(b.site ?? ''), name: String(b.name ?? b.id ?? '').slice(0, 60), polygon: b.polygon, bufferM: b.bufferM ?? 25 };
        const err = validateFence(f); if (err) throw new HttpError(400, err);
        engine.setFence(f); return send(res, 201, f);
      }

      if (m === 'POST' && p === '/api/devices') {
        need(r, 'admin');
        const b = await json(req);
        if (typeof b.id !== 'string' || !/^[A-Za-z0-9-]{3,32}$/.test(b.id)) throw new HttpError(400, 'Ugyldig id');
        if (!['skog', 'landlig', 'by'].includes(b.env ?? 'landlig')) throw new HttpError(400, 'Ugyldig miljø');
        let k: KeyObject;
        try { k = loadPublicKey(b.publicKeyPem); } catch { throw new HttpError(400, 'Ugyldig offentlig nøkkel'); }
        if (k.asymmetricKeyDetails?.namedCurve !== 'prime256v1') throw new HttpError(400, 'Nøkkelen må være P-256');
        if (engine.units.has(b.id)) throw new HttpError(409, 'Enheten finnes allerede');
        keys.set(b.id, k);
        const u = engine.register({ id: b.id, name: String(b.name ?? b.id).slice(0, 60), kind: String(b.kind ?? 'maskin'), site: String(b.site ?? ''), env: (b.env ?? 'landlig') as EnvProfile, publicKeyPem: b.publicKeyPem });
        engine.log(`Enhet ${u.name} (${u.id}) registrert.`);
        return send(res, 201, publicUnit(u));
      }
      let mm;
      if (m === 'DELETE' && (mm = p.match(/^\/api\/geofences\/([A-Za-z0-9-]+)$/))) { need(r, 'admin'); engine.removeFence(mm[1]); return send(res, 200, { ok: true }); }
      if (m === 'POST' && (mm = p.match(/^\/api\/units\/([A-Za-z0-9-]+)\/env$/))) {
        need(r, 'admin');
        const b = await json(req);
        if (!['skog', 'landlig', 'by'].includes(b.env)) throw new HttpError(400, 'Ugyldig miljø');
        engine.setEnv(mm[1], b.env); return send(res, 200, publicUnit(engine.units.get(mm[1])!));
      }
      if (m === 'POST' && (mm = p.match(/^\/api\/alarms\/(A-\d+)\/(take|close)$/))) {
        need(r, 'operator');
        const b = await json(req);
        const who = String(b.who ?? 'operatør').slice(0, 60);
        const c = mm[2] === 'take' ? engine.take(mm[1], who) : engine.close(mm[1], who, String(b.result ?? 'Kontrollert').slice(0, 200), !!b.falseAlarm);
        return send(res, 200, c);
      }
      throw new HttpError(404, 'Finnes ikke');
    } catch (e) {
      const code = e instanceof HttpError ? e.code : /^Ukjent (enhet|sak|gjerde)/.test((e as Error).message) ? 404 : 500;
      if (code === 500) console.error(e);
      if (!res.headersSent) send(res, code, { error: (e as Error).message });
    }
  });

  const ready = new Promise<number>(resolve => server.listen(o.port ?? Number(process.env.PORT ?? 8080), () => {
    const a = server.address(); resolve(typeof a === 'object' && a ? a.port : 0);
  }));
  const close = () => new Promise<void>(r => { clearInterval(ticker); clearInterval(pinger); for (const c of clients) c.end(); server.close(() => r()); });
  return { engine, ready, close, platformPub };
}

// Offentlig nøkkel sendes ikke ut i lister.
function publicUnit(u: Unit) { const { publicKeyPem, ...rest } = u; return rest; }

class HttpError extends Error { code: number; constructor(code: number, msg: string) { super(msg); this.code = code; } }

// Start når filen kjøres direkte
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const dev = process.argv.includes('--dev') || process.env.GVT_DEV === '1';
  try {
    const s = startServer({ dev, dataFile: process.env.GVT_DATA ?? join(here, '..', 'data.json'), keyFile: process.env.GVT_KEY ?? join(here, '..', 'platform-key.pem'), arcEnabled: process.env.GVT_ARC === '1' });
    s.ready.then(port => console.log(`Varde-plattformen kjører på http://localhost:${port}` + (dev ? '  (UTVIKLINGSMODUS: operatør-token operator-dev, admin-token admin-dev)' : '')));
  } catch (e) {
    console.error('Varde-plattformen startet ikke: ' + (e as Error).message);
    process.exit(1);
  }
}
