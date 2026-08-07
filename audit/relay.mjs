import net from 'net';
const LISTEN = 36999, UP = 36431;
net.createServer(c => {
  const u = net.connect(UP, '127.0.0.1');
  let first = true;
  c.on('data', d => { if (first) { console.log('CLIENT->PROXY:\n' + d.toString('utf8').slice(0,400)); first = false; } u.write(d); });
  let firstUp = true;
  u.on('data', d => { if (firstUp) { console.log('PROXY->CLIENT:\n' + JSON.stringify(d.toString('utf8').slice(0,300))); firstUp = false; } c.write(d); });
  u.on('error', e => console.log('UP ERR', e.message));
  c.on('error', e => console.log('CL ERR', e.message));
  u.on('close', () => { console.log('UP CLOSE'); c.end(); });
  c.on('close', () => u.end());
}).listen(LISTEN, '127.0.0.1', () => console.log('relay on', LISTEN));
