import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from ai_actions import parse_action,ActionError
class ActionsTests(unittest.TestCase):
 def test_trailing_explanation_does_not_break_next_step(self):
  self.assertEqual(parse_action('{"type":"tap","x":0.14,"y":0.75}\nI will click this icon.')['type'],'tap')
 def test_markdown(self):self.assertEqual(parse_action('```json\n{"type":"key","key":"home"}\n```')['key'],'home')
 def test_invalid_coordinates(self):
  for x in [-1,2,True,float('nan')]:
   import json
   with self.assertRaises(ActionError):parse_action(json.dumps({'type':'tap','x':x,'y':.5}))
 def test_missing_and_unknown(self):
  for raw in ['{"type":"tap"}','{"type":"shell"}','not json']:
   with self.assertRaises(ActionError):parse_action(raw)
class LoopTests(unittest.TestCase):
 def test_two_steps_execute_without_confirmation(self):
  import importlib.util,json,io
  from unittest.mock import patch,Mock
  spec=importlib.util.spec_from_file_location('ai_test_backend',Path(__file__).resolve().parents[1]/'app/backend.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
  actions=['{"type":"tap","x":0.1,"y":0.2}\nexplanation','```json\n{"type":"key","key":"home"}\n```','{"type":"done","reason":"ok"}']
  responses=[io.BytesIO(json.dumps({'choices':[{'message':{'content':a}}]}).encode()) for a in actions]
  phone=Mock();phone.ai_image.return_value=(b'jpg','image/jpeg',100);phone.ui_context.return_value=[]
  with patch.object(b,'settings',return_value={'url':'https://example.invalid/v1','model':'test'}),patch.object(b,'keychain',return_value=''),patch.object(b,'phone',phone),patch.object(b.urllib.request,'urlopen',side_effect=responses),patch.object(b.stop,'wait',return_value=False):
   b.ai_run('test',3)
  self.assertEqual(phone.action.call_count,2);self.assertIsNone(b.pending);self.assertFalse(any('任务失败' in e['message'] for e in b.events));self.assertEqual(b.task_result['status'],'completed')
class NetworkTests(unittest.TestCase):
 def backend(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('network_backend',Path(__file__).resolve().parents[1]/'app/backend.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);return b
 def test_timeout_then_success_retries_without_executing_phone(self):
  import io,socket
  from unittest.mock import patch
  b=self.backend()
  with patch.object(b.urllib.request,'urlopen',side_effect=[socket.timeout(),io.BytesIO(b'{"ok":true}')]) as call,patch.object(b.stop,'wait',return_value=False):
   self.assertEqual(b.request_model(None),{'ok':True});self.assertEqual(call.call_count,2);self.assertEqual(call.call_args.kwargs['timeout'],180)
 def test_repeated_timeout_is_bounded(self):
  import socket
  from unittest.mock import patch
  b=self.backend()
  with patch.object(b.urllib.request,'urlopen',side_effect=socket.timeout()) as call,patch.object(b.stop,'wait',return_value=False):
   with self.assertRaisesRegex(RuntimeError,'180'):b.request_model(None)
   self.assertEqual(call.call_count,2)
 def test_stop_cancels_retry(self):
  import socket
  from unittest.mock import patch
  b=self.backend()
  with patch.object(b.urllib.request,'urlopen',side_effect=socket.timeout()) as call,patch.object(b.stop,'wait',return_value=True):
   self.assertIsNone(b.request_model(None));self.assertEqual(call.call_count,1)
class TrustModeTests(unittest.TestCase):
 def run_mode(self,mode):
  import importlib.util,json,io
  from unittest.mock import patch,Mock
  spec=importlib.util.spec_from_file_location('mode_backend',Path(__file__).resolve().parents[1]/'app/backend.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
  actions=[{'type':'confirm','reason':'update','action':{'type':'tap','x':.5,'y':.9}},{'type':'done'}]
  replies=[io.BytesIO(json.dumps({'choices':[{'message':{'content':json.dumps(a)}}]}).encode()) for a in actions]
  phone=Mock();phone.ai_image.return_value=(b'jpg','image/jpeg',100);phone.ui_context.return_value=[]
  with patch.object(b,'settings',return_value={'url':'https://example.invalid/v1','model':'test'}),patch.object(b,'keychain',return_value=''),patch.object(b,'phone',phone),patch.object(b.urllib.request,'urlopen',side_effect=replies),patch.object(b.stop,'wait',return_value=False),patch.object(b.approval,'wait',return_value=True) as approval:
   b.ai_run('update',2,mode)
  self.assertEqual(phone.action.call_count,1);self.assertEqual(phone.action.call_args.args[0]['type'],'tap');self.assertFalse(b.stop.is_set());return approval.call_count
 def test_trusted_executes_nested_confirmation_without_pause(self):self.assertEqual(self.run_mode('trusted'),0)
 def test_manual_executes_after_approval(self):self.assertGreater(self.run_mode('manual'),0)
class FormatRepairTests(unittest.TestCase):
 def test_wrapped_action(self):self.assertEqual(parse_action('{"action":{"type":"tap","x":0.2,"y":0.3}}')['type'],'tap')
 def test_action_named_click(self):self.assertEqual(parse_action('{"action":"click","x":0.2,"y":0.3}')['type'],'tap')
 def test_invalid_output_repairs_before_execution(self):
  import importlib.util,json,io
  from unittest.mock import patch,Mock
  spec=importlib.util.spec_from_file_location('repair_backend',Path(__file__).resolve().parents[1]/'app/backend.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
  replies=[io.BytesIO(json.dumps({'choices':[{'message':{'content':x}}]}).encode()) for x in ['I will click the search box.','{"type":"tap","x":0.2,"y":0.3}','{"type":"done"}']]
  phone=Mock();phone.ai_image.return_value=(b'jpg','image/jpeg',100);phone.ui_context.return_value=[]
  with patch.object(b,'settings',return_value={'url':'https://example.invalid/v1','model':'test'}),patch.object(b,'keychain',return_value=''),patch.object(b,'phone',phone),patch.object(b.urllib.request,'urlopen',side_effect=replies) as request:
   b.ai_run('search',2,'trusted')
  self.assertEqual(phone.action.call_count,1);self.assertEqual(request.call_count,3);self.assertFalse(any('任务失败' in x['message'] for x in b.events))
class RecoveryTests(unittest.TestCase):
 def test_home_recovery_is_bounded(self):
  import importlib.util,json,io
  from unittest.mock import patch,Mock
  spec=importlib.util.spec_from_file_location('recovery_backend',Path(__file__).resolve().parents[1]/'app/backend.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
  replies=[io.BytesIO(json.dumps({'choices':[{'message':{'content':'{"type":"recover","reason":"unknown page"}'}}]}).encode()) for _ in range(2)]
  phone=Mock();phone.ai_image.return_value=(b'jpg','image/jpeg',100);phone.ui_context.return_value=[]
  with patch.object(b,'settings',return_value={'url':'https://example.invalid/v1','model':'test'}),patch.object(b,'keychain',return_value=''),patch.object(b,'phone',phone),patch.object(b.urllib.request,'urlopen',side_effect=replies):
   b.ai_run('search',3,'trusted')
  self.assertEqual(phone.action.call_count,1);self.assertEqual(phone.action.call_args.args[0],{'type':'key','key':'home'});self.assertTrue(any('恢复后仍无法定位' in e['message'] for e in b.events))
