"""Display-only names keyed by stable phone identity."""
import json,threading
class DeviceProfiles:
 def __init__(self,path):self.path=path;self.lock=threading.RLock()
 def read(self):
  if not self.path.exists():return {'names':{},'aliases':{}}
  return json.loads(self.path.read_text())
 def write(self,data):
  temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2));temp.chmod(0o600);temp.replace(self.path)
 def bind(self,serial,identity):
  with self.lock:
   data=self.read();data['aliases'][serial]=identity;self.write(data)
 def rename(self,identity,name):
  if not identity or identity=='__none__':raise ValueError('请先连接需要改名的手机')
  if not isinstance(name,str) or len(name.strip())>40:raise ValueError('名称最多40个字符')
  with self.lock:
   data=self.read()
   if name.strip():data['names'][identity]=name.strip()
   else:data['names'].pop(identity,None)
   self.write(data)
 def name(self,serial=None,identity=None):
  data=self.read();identity=identity or data['aliases'].get(serial)
  return data['names'].get(identity,'')
