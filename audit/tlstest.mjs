import net from 'net'; import tls from 'tls'; import fs from 'fs';
const ca = fs.readFileSync('/root/.ccr/ca-bundle.crt');
function tryAlpn(alpn, servername='example.com'){
  return new Promise(res=>{
    const s = net.connect(36431,'127.0.0.1',()=>{ s.write(`CONNECT ${servername}:443 HTTP/1.1\r\nHost: ${servername}:443\r\n\r\n`); });
    let buf='';
    s.on('data', function onData(d){
      buf+=d.toString();
      if(buf.includes('\r\n\r\n')){
        s.removeListener('data',onData);
        const t = tls.connect({socket:s, servername, ca, ALPNProtocols: alpn});
        t.on('secureConnect',()=>{ res(`${JSON.stringify(alpn)} OK alpn=${t.alpnProtocol} authorized=${t.authorized} ${t.authorizationError||''}`); t.destroy(); });
        t.on('error',e=>{ res(`${JSON.stringify(alpn)} ERR ${e.message}`); s.destroy(); });
      }
    });
    s.on('error',e=>res(`${JSON.stringify(alpn)} SOCKERR ${e.message}`));
    setTimeout(()=>res(`${JSON.stringify(alpn)} TIMEOUT`),15000);
  });
}
for (const a of [['http/1.1'],['h2','http/1.1'],['h2']]) console.log(await tryAlpn(a));
