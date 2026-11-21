"""Local checks: no polling and no additional model requests."""
import re

def signature(a):
 t=a.get('type')
 if t=='tap':return (t,round(a['x']/0.03),round(a['y']/0.03))
 if t=='swipe':return (t,)+tuple(round(a[k]/.03) for k in ('x','y','x2','y2'))
 if t=='key':return (t,a.get('key'))
 if t=='text':return (t,a.get('text'))
 return (t,)
def transfer_status(task,controls):
 if not re.search(r'升级|更新|下载|安装',task):return None
 for n in controls:
  text=' '.join(str(n.get(k,'')) for k in ('text','label'))
  for status in ('下载中','正在下载','安装中','正在安装','正在升级','升级中','正在更新','更新中'):
   if status in text:return status
 return None
