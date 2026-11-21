"""Short-lived LAN pairing endpoint, isolated from the local control API."""
import json,secrets,time,threading,socket,ssl,subprocess,hashlib
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
class LanPairing:
 def __init__(self,root):self.root=root;self.server=None;self.code=None;self.expires=0;self.lock=threading.Lock();self.last='尚未配对'
 def start(self):
  with self.lock:
   if self.server:self.server.shutdown();self.server.server_close()
   cert=self.root/'lan-cert.pem';key=self.root/'lan-key.pem'
   if not cert.exists() or not key.exists():
    subprocess.run(['/usr/bin/openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','3650','-subj','/CN=MacPhone Local Pairing'],capture_output=True,check=True);key.chmod(0o600)
   der=ssl.PEM_cert_to_DER_cert(cert.read_text());pin=hashlib.sha256(der).hexdigest()
   host=None
   for iface in ('en0','en1'):
    p=subprocess.run(['/usr/sbin/ipconfig','getifaddr',iface],capture_output=True,text=True)
    if p.returncode==0 and p.stdout.strip():host=p.stdout.strip();break
   if not host:raise ValueError('未找到局域网地址，请连接 Wi-Fi 或有线网络')
   owner=self
   class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
     try:
      if self.path!='/pair':raise ValueError('无效接口')
      size=int(self.headers.get('Content-Length','0'))
      if not 0<size<4096:raise ValueError('请求无效')
      data=json.loads(self.rfile.read(size))
      with owner.lock:
       if not owner.code or time.time()>owner.expires or not secrets.compare_digest(str(data.get('code','')),owner.code):raise ValueError('二维码已过期或已使用，请重新生成')
       name=str(data.get('name','Android'))[:80];device=str(data.get('deviceId',''))
       if not device or len(device)>128:raise ValueError('手机身份无效')
       path=owner.root/'lan-paired-devices.json';devices=json.loads(path.read_text()) if path.exists() else {};devices[device]={'name':name,'pairedAt':time.strftime('%Y-%m-%d %H:%M:%S')};path.write_text(json.dumps(devices,ensure_ascii=False));path.chmod(0o600)
       owner.code=None;owner.last='已配对：'+name
      body=json.dumps({'ok':True,'computer':socket.gethostname(),'message':'已完成局域网身份配对；当前控制与传输仍使用 ADB 连接'}).encode();self.send_response(200)
     except Exception as e:body=json.dumps({'ok':False,'error':str(e)}).encode();self.send_response(400)
     self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
   server=ThreadingHTTPServer(('0.0.0.0',0),Handler);ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(str(cert),str(key));server.socket=ctx.wrap_socket(server.socket,server_side=True);self.server=server
   self.code=secrets.token_urlsafe(24);self.expires=time.time()+180;self.last='二维码等待扫描（3分钟有效）'
   threading.Thread(target=server.serve_forever,daemon=True).start()
   from urllib.parse import urlencode
   return {'url':'macphone://pair?'+urlencode({'host':host,'port':server.server_port,'code':self.code,'pin':pin,'name':socket.gethostname()}),'expiresIn':180,'address':host}
 def status(self):return {'message':self.last,'expired':bool(self.code and time.time()>self.expires)}
