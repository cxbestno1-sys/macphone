import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from task_guard import signature,transfer_status
class GuardTests(unittest.TestCase):
 def test_nearby_taps_are_same(self):self.assertEqual(signature({'type':'tap','x':.50,'y':.90}),signature({'type':'tap','x':.501,'y':.901}))
 def test_progress_completes_upgrade(self):self.assertEqual(transfer_status('升级所有app',[{'text':'正在安装'}]),'正在安装')
 def test_no_false_completion_on_upgrade_button(self):self.assertIsNone(transfer_status('升级所有app',[{'text':'升级'},{'text':'暂停'}]))
 def test_unrelated_task_not_completed(self):self.assertIsNone(transfer_status('搜索商品',[{'text':'下载中'}]))
class GuardLoopTests(unittest.TestCase):
 def simulate(self,progress):
  import importlib.util,json,io
  from unittest.mock import Mock,patch
  spec=importlib.util.spec_from_file_location('guard_backend',Path(__file__).resolve().parents[1]/'app/backend.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
  phone=Mock();phone.ai_image.return_value=(b'jpg','image/jpeg',100);phone.ui_context.side_effect=[[],[{'text':'下载中'}]] if progress else None
  if not progress:phone.ui_context.return_value=[]
  actions=[{'type':'tap','x':.5,'y':.9}]*2+[{'type':'done'}]
  replies=[io.BytesIO(json.dumps({'choices':[{'message':{'content':json.dumps(a)}}]}).encode()) for a in actions]
  with patch.object(b,'settings',return_value={'url':'https://example.invalid/v1','model':'test'}),patch.object(b,'keychain',return_value=''),patch.object(b,'phone',phone),patch.object(b.urllib.request,'urlopen',side_effect=replies) as model,patch.object(b.approval,'wait',return_value=True) as approve:
   b.ai_run('升级所有app',3,'trusted')
  if progress:self.assertEqual(b.task_result['status'],'handed_off');self.assertIn('下载中',b.task_result['message'])
  return phone.action.call_count,model.call_count,approve.call_count,b.events
 def test_progress_ends_without_extra_model_call(self):
  actions,models,approvals,events=self.simulate(True);self.assertEqual((actions,models,approvals),(1,1,0));self.assertTrue(any('下载中' in x['message'] and '任务完成' in x['message'] for x in events))
 def test_two_repeated_actions_pause_even_when_trusted(self):
  actions,models,approvals,events=self.simulate(False);self.assertEqual(actions,2);self.assertEqual(approvals,1);self.assertTrue(any('重复动作保护' in x['message'] for x in events))
