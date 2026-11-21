"""Explicit user-created task recordings; atomic local persistence."""
import json,time,uuid,threading,copy
class TaskStore:
 def __init__(self,path):self.path=path;self.lock=threading.RLock();self.draft=None;self.scope=None
 def all(self):
  if not self.path.exists():return []
  data=json.loads(self.path.read_text())
  if not isinstance(data,list):raise ValueError('任务文件格式错误')
  return data
 def list(self):
  items=self.all()
  return items if self.scope is None else [x for x in items if x.get('deviceId')==self.scope]
 def claim_legacy(self):
  if not self.scope or self.scope=='__none__':raise ValueError('请先连接手机')
  with self.lock:
   items=self.all()
   for item in items:
    if not item.get('deviceId'):item['deviceId']=self.scope
   self.write(items)
 def write(self,items):
  tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(items,ensure_ascii=False,indent=2));tmp.chmod(0o600);tmp.replace(self.path)
 def start(self,name,description='',category='日常'):
  with self.lock:
   if self.draft:raise ValueError('请先保存或取消当前录制')
   if not name.strip():raise ValueError('请输入任务名称')
   self.draft={'deviceId':self.scope,'id':uuid.uuid4().hex,'name':name.strip()[:100],'description':description[:2000],'category':category[:30],'steps':[],'createdAt':time.strftime('%Y-%m-%d %H:%M:%S')};return self.snapshot()
 def snapshot(self):return copy.deepcopy(self.draft)
 def add(self,action,app):
  with self.lock:
   if self.draft is None:return
   if len(self.draft['steps'])>=300:raise ValueError('录制已达300步，请保存当前任务')
   self.draft['steps'].append({'action':copy.deepcopy(action),'app':app,'recordedAt':time.strftime('%H:%M:%S')})
 def finish(self):
  with self.lock:
   if not self.draft:raise ValueError('没有正在录制的任务')
   if not self.draft['steps']:raise ValueError('请先录制至少一个操作，或取消录制')
   items=self.all();item=self.snapshot();items.insert(0,item);self.write(items);self.draft=None;return item
 def cancel(self):
  with self.lock:self.draft=None
 def delete(self,id):
  with self.lock:
   self.get(id);self.write([x for x in self.all() if x['id']!=id])
 def get(self,id):
  for x in self.list():
   if x['id']==id:return x
  raise ValueError('任务不存在')
 def remove_step(self,index):
  with self.lock:
   if self.draft is None:raise ValueError('没有录制中的任务')
   self.draft['steps'].pop(int(index))
 def set_schedule(self,id,at):
  self.get(id)
  with self.lock:
   items=self.all();item=next((x for x in items if x['id']==id),None)
   if item is None:raise ValueError('任务不存在')
   item['schedule']=self.schedule_value(at);self.write(items);return item
 @staticmethod
 def schedule_value(at):
  if not at:return None
  from datetime import datetime,timezone,timedelta
  try:dt=datetime.fromisoformat(at)
  except (TypeError,ValueError):raise ValueError('请选择有效的执行时间')
  if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone(timedelta(hours=8)))
  epoch=dt.timestamp()
  if epoch<=time.time():raise ValueError('执行时间必须晚于现在')
  return {'at':epoch,'display':dt.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S'),'timezone':'Asia/Shanghai','status':'scheduled','nextStep':0}
 def tick(self,ready,now=None):
  now=time.time() if now is None else now
  with self.lock:
   items=self.all();changed=False;due=[]
   for item in items:
    if self.scope is not None and item.get('deviceId')!=self.scope:continue
    s=item.get('schedule')
    if not s or s['status']!='scheduled' or s['at']>now:continue
    changed=True
    if now-s['at']>300:s.update(status='missed',message='错过执行时间，请重新设置定时')
    elif not ready:s.update(status='blocked',message='手机未连接、未配对或有其他任务，请重新定时')
    else:s.update(status='awaiting_confirmation',message='时间已到，请核对画面并确认第一步');due.append(item['id'])
   if changed:self.write(items)
   return due
 def advance(self,id,index):
  self.get(id)
  with self.lock:
   items=self.all();item=next(x for x in items if x['id']==id);s=item.get('schedule')
   if s and s['status']=='awaiting_confirmation':
    if index!=s['nextStep']:raise ValueError('请按顺序执行定时任务')
    s['nextStep']=index+1
    if s['nextStep']>=len(item['steps']):s.update(status='completed',message='执行完成')
    self.write(items)
 def rename(self,id,name):
  self.get(id)
  if not isinstance(name,str) or not name.strip() or len(name.strip())>100:raise ValueError('任务名称需为1到100个字符')
  with self.lock:
   items=self.all();item=next((x for x in items if x['id']==id),None)
   if item is None:raise ValueError('任务不存在')
   item['name']=name.strip();self.write(items);return item
 def edit(self,id,name,keep_indices,schedule_changed=False,scheduled_at=None,interval=0.5,checks=None):
  self.get(id)
  if not isinstance(name,str) or not 1<=len(name.strip())<=100:raise ValueError('任务名称需为1到100个字符')
  if isinstance(interval,bool) or not isinstance(interval,(int,float)) or not 0<=interval<=300:raise ValueError('步骤间隔需为0到300秒')
  with self.lock:
   items=self.all();item=next((x for x in items if x['id']==id),None)
   if item is None:raise ValueError('任务不存在')
   if not isinstance(keep_indices,list) or not keep_indices or any(type(i)!=int or i<0 or i>=len(item['steps']) for i in keep_indices) or keep_indices!=sorted(set(keep_indices)):raise ValueError('请至少保留一个有效步骤')
   updated=copy.deepcopy(item);updated['name']=name.strip();updated['steps']=[copy.deepcopy(item['steps'][i]) for i in keep_indices];updated['intervalSeconds']=interval
   if checks is not None:
    if not isinstance(checks,list) or len(checks)!=len(keep_indices) or any(type(x)!=bool for x in checks):raise ValueError('截图判断配置无效')
    for step,check in zip(updated['steps'],checks):step['screenshotCheck']=check
   if updated.get('schedule') and keep_indices!=list(range(len(item['steps']))):updated['schedule']['nextStep']=0
   if schedule_changed:updated['schedule']=self.schedule_value(scheduled_at)
   items[items.index(item)]=updated;self.write(items);return updated
