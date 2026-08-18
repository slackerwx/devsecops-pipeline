import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { handler } from './handler.js';

test('health answers ok', async () => {
  const server = createServer(handler).listen(0);
  await new Promise((r) => server.once('listening', r));
  const { port } = server.address();
  const res = await fetch(`http://127.0.0.1:${port}/health`);
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { ok: true });
  server.close();
});
