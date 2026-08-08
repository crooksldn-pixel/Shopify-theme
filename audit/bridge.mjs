// Local HTTP/1.1 MITM bridge.
// Chromium's TLS ClientHello is reset by the session's egress proxy, but node's is not.
// So: Chromium -> this bridge (TLS terminated locally, cert errors ignored by the browser)
//     this bridge -> CONNECT tunnel through 127.0.0.1:36431 -> origin, using node TLS.
import net from 'net';
import tls from 'tls';
import http from 'http';
import https from 'https';
import fs from 'fs';

// Derive the egress proxy from the environment — the port changes per container session.
const UP = new URL(process.env.HTTPS_PROXY || 'http://127.0.0.1:36431');
const UPSTREAM_HOST = UP.hostname;
const UPSTREAM_PORT = Number(UP.port);
const CA = fs.readFileSync('/root/.ccr/ca-bundle.crt');
const key = fs.readFileSync(new URL('./certs/key.pem', import.meta.url));
const cert = fs.readFileSync(new URL('./certs/cert.pem', import.meta.url));

function tunnel(host, port) {
  return new Promise((resolve, reject) => {
    const s = net.connect(UPSTREAM_PORT, UPSTREAM_HOST);
    s.setNoDelay(true);
    s.once('error', reject);
    s.on('connect', () => s.write(`CONNECT ${host}:${port} HTTP/1.1\r\nHost: ${host}:${port}\r\n\r\n`));
    let buf = '';
    const onData = (d) => {
      buf += d.toString('latin1');
      if (buf.includes('\r\n\r\n')) {
        s.removeListener('data', onData);
        const status = parseInt(buf.split(' ')[1], 10);
        if (status !== 200) return reject(new Error('tunnel ' + status));
        resolve(s);
      }
    };
    s.on('data', onData);
  });
}

class TunnelAgent extends https.Agent {
  createConnection(opts, cb) {
    tunnel(opts.host, opts.port || 443).then((sock) => {
      const t = tls.connect({
        socket: sock,
        servername: opts.servername || opts.host,
        ca: CA,
        ALPNProtocols: ['http/1.1'],
      });
      t.setNoDelay(true);
      t.once('secureConnect', () => cb(null, t));
      t.once('error', (e) => cb(e));
    }).catch(cb);
  }
}
const agent = new TunnelAgent({ keepAlive: true, maxSockets: 128, maxFreeSockets: 16, timeout: 20000 });

function forward(req, res, scheme) {
  const host = req.headers.host;
  if (!host) { res.writeHead(400); return res.end('no host'); }
  const [h, p] = host.split(':');
  const headers = { ...req.headers };
  delete headers['proxy-connection'];
  // The origin may 421/misbehave with h2 hints; force 1.1 semantics.
  headers['accept-encoding'] = headers['accept-encoding'] || 'gzip, deflate, br';
  const opts = {
    host: h,
    port: p ? Number(p) : 443,
    method: req.method,
    path: req.url.startsWith('http') ? new URL(req.url).pathname + new URL(req.url).search : req.url,
    headers,
    agent,
    servername: h,
  };
  const up = https.request(opts, (ur) => {
    const outHeaders = { ...ur.headers };
    delete outHeaders['strict-transport-security'];
    delete outHeaders['content-security-policy-report-only'];
    res.writeHead(ur.statusCode, outHeaders);
    ur.pipe(res);
  });
  // A hung upstream must never hold a socket: some Shopify analytics endpoints
  // (web-pixels, monorail-edge) never close, and they starved the pool.
  up.setTimeout(25000, () => { up.destroy(new Error('upstream timeout')); });
  up.on('error', (e) => { try { if (!res.headersSent) res.writeHead(504); res.end('bridge: ' + e.message); } catch {} });
  req.on('error', () => up.destroy());
  req.pipe(up);
}

const tlsServer = https.createServer({ key, cert, ALPNProtocols: ['http/1.1'] }, (req, res) => forward(req, res, 'https'));
tlsServer.on('clientError', () => {});

const proxy = http.createServer((req, res) => forward(req, res, 'http'));
proxy.on('connect', (req, clientSocket, head) => {
  clientSocket.write('HTTP/1.1 200 Connection Established\r\nProxy-Agent: crk-bridge\r\n\r\n');
  clientSocket.setNoDelay(true);
  if (head && head.length) clientSocket.unshift(head);
  tlsServer.emit('connection', clientSocket);
});
proxy.on('clientError', () => {});

const PORT = Number(process.env.BRIDGE_PORT || 38080);
proxy.listen(PORT, '127.0.0.1', () => console.log('bridge listening on ' + PORT));
