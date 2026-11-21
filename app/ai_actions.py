"""Parse model action envelopes and validate before device execution."""
import json,math,re
class ActionError(ValueError):pass
def parse_action(raw):
 if not isinstance(raw,str) or not raw.strip():raise ActionError('模型未返回文字动作')
 text=raw.strip();decoder=json.JSONDecoder();action=None
 # Some compatible endpoints add markdown or commentary after the JSON object.
 for match in re.finditer(r'\{',text):
  try:
   obj,_=decoder.raw_decode(text[match.start():])
   if isinstance(obj,dict):
    if 'type' in obj:action=obj;break
    if isinstance(obj.get('action'),dict) and 'type' in obj['action']:action=obj['action'];break
    if obj.get('action') in ('tap','click','swipe','text','input','key','done','wait'):
     action=dict(obj);action['type']={'click':'tap','input':'text'}.get(obj['action'],obj['action']);break
  except json.JSONDecodeError:continue
 if action is None:raise ActionError('模型没有返回可识别的动作 JSON')
 t=action.get('type')
 if t not in ('tap','swipe','text','key','wait','done','confirm','recover'):raise ActionError('模型返回未知动作：'+str(t))
 required={'tap':['x','y'],'swipe':['x','y','x2','y2'],'text':['text'],'key':['key']}.get(t,[])
 for k in required:
  if k not in action:raise ActionError('模型动作缺少字段：'+k)
 for k in ('x','y','x2','y2'):
  if k in action and (isinstance(action[k],bool) or not isinstance(action[k],(int,float)) or not math.isfinite(action[k]) or not 0<=action[k]<=1):raise ActionError('模型坐标 '+k+' 必须在0到1之间')
 if t=='text' and (not isinstance(action['text'],str) or len(action['text'])>10000):raise ActionError('模型输入文本无效或过长')
 if t=='key' and action['key'] not in ('home','back','recents','enter','tab','delete','wake'):raise ActionError('模型按键不受支持')
 for k in ('duration','seconds'):
  if k in action and (isinstance(action[k],bool) or not isinstance(action[k],(int,float)) or not math.isfinite(action[k])):raise ActionError('模型时间参数无效')
 return action
