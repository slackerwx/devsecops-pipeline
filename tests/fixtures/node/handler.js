export function handler(req, res) {
  if (req.url === '/health') {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end('{"ok":true}');
    return;
  }
  res.writeHead(200, { 'content-type': 'text/plain' });
  res.end('fixture-node\n');
}
