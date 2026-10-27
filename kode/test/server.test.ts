import { test } from 'node:test';
import assert from 'node:assert/strict';
import { startServer, resolveTokens } from '../platform/server.ts';
import { newKeyPair, sealMessage } from '../shared/protocol.ts';

test('mottak: registrering, signatur, gjentak og roller', async () => {
  const s = startServer({ port: 0, quiet: true, tickMs: 50, dev: true });
  const port = await s.ready, base = `http://localhost:${port}`;
  const admin = { authorization: 'Bearer admin-dev', 'content-type': 'application/json' };
  const op = { authorization: 'Bearer operator-dev', 'content-type': 'application/json' };
  try {
    const kp = newKeyPair();
    let r = await fetch(base + '/api/devices', { method: 'POST', headers: op, body: JSON.stringify({ id: 'T-1', publicKeyPem: kp.publicKeyPem }) });
    assert.equal(r.status, 403);
    r = await fetch(base + '/api/devices', { method: 'POST', headers: admin, body: JSON.stringify({ id: 'T-1', name: 'Test', publicKeyPem: kp.publicKeyPem }) });
    assert.equal(r.status, 201);
    assert.equal((await r.json()).publicKeyPem, undefined);

    const m = sealMessage({ v: 1, id: 'T-1', ctr: 1, ts: 0, type: 'hb', iv: 60 }, kp.privateKey);
    const ing = (b: Uint8Array) => fetch(base + '/v1/ingest', { method: 'POST', body: b });
    assert.equal((await ing(m)).status, 200);
    assert.equal((await ing(m)).status, 409);
    assert.equal((await ing(sealMessage({ v: 1, id: 'T-1', ctr: 5, ts: 0, type: 'hb' }, newKeyPair().privateKey))).status, 401);
    assert.equal((await ing(sealMessage({ v: 1, id: 'T-9', ctr: 5, ts: 0, type: 'hb' }, kp.privateKey))).status, 404);
    assert.equal((await fetch(base + '/api/units')).status, 401);
    assert.equal((await fetch(base + '/api/units', { headers: op })).status, 200);
  } finally { await s.close(); }
});

test('token: plattformen nekter å starte uten sterke token (fail closed)', () => {
  const strong = 'a'.repeat(32), strong2 = 'b'.repeat(32);
  assert.throws(() => resolveTokens({}, {}), /må settes/);
  assert.throws(() => resolveTokens({}, { GVT_ADMIN_TOKEN: strong }), /må settes/);
  assert.throws(() => resolveTokens({}, { GVT_ADMIN_TOKEN: 'admin-dev', GVT_OPERATOR_TOKEN: strong2 }), /minst 32/);
  assert.throws(() => resolveTokens({}, { GVT_ADMIN_TOKEN: 'kort', GVT_OPERATOR_TOKEN: strong2 }), /minst 32/);
  assert.throws(() => resolveTokens({}, { GVT_ADMIN_TOKEN: strong, GVT_OPERATOR_TOKEN: strong }), /ulike/);
  assert.deepEqual(resolveTokens({}, { GVT_ADMIN_TOKEN: strong, GVT_OPERATOR_TOKEN: strong2 }), { admin: strong, operator: strong2, dev: false });
  // Utviklingsmodus må slås på eksplisitt
  assert.equal(resolveTokens({}, { GVT_DEV: '1' }).admin, 'admin-dev');
  assert.equal(resolveTokens({ dev: true }, {}).operator, 'operator-dev');
  assert.throws(() => startServer({ port: 0, quiet: true, dev: false, adminToken: 'admin-dev', operatorToken: 'operator-dev' }), /minst 32/);
});
