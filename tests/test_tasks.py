import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from tasks import TaskStore
class TaskTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'tasks.json';self.store=TaskStore(self.path)
 def tearDown(self):self.tmp.cleanup()
 def test_explicit_save_and_reload(self):
  self.store.start('挂号准备');self.store.add({'type':'tap','x':.2,'y':.5},'com.example.app');self.assertFalse(self.path.exists());saved=self.store.finish();self.assertEqual(TaskStore(self.path).get(saved['id'])['steps'][0]['app'],'com.example.app');self.assertIsNone(self.store.draft)
 def test_cancel_does_not_save(self):
  self.store.start('取消测试');self.store.add({'type':'key','key':'home'},'');self.store.cancel();self.assertEqual(self.store.list(),[])
 def test_empty_recording_cannot_save(self):
  self.store.start('空任务')
  with self.assertRaises(ValueError):self.store.finish()
 def test_draft_snapshot_is_independent(self):
  self.store.start('测试');d=self.store.snapshot();d['steps'].append({});self.assertEqual(self.store.snapshot()['steps'],[])
class ScheduleTests(unittest.TestCase):
 def setUp(self):
  import time
  self.tmp=tempfile.TemporaryDirectory();self.store=TaskStore(Path(self.tmp.name)/'tasks.json');self.store.start('定时测试');self.store.add({'type':'key','key':'home'},'');self.item=self.store.finish();self.now=time.time()
 def tearDown(self):self.tmp.cleanup()
 def schedule(self,delay=60):
  from datetime import datetime,timezone
  return self.store.set_schedule(self.item['id'],datetime.fromtimestamp(self.now+delay,timezone.utc).isoformat())
 def test_due_fires_once_and_progress_persists(self):
  self.schedule();self.assertEqual(self.store.tick(True,self.now+61),[self.item['id']]);self.assertEqual(self.store.tick(True,self.now+62),[]);self.store.advance(self.item['id'],0);self.assertEqual(self.store.get(self.item['id'])['schedule']['status'],'completed')
 def test_disconnected_does_not_execute(self):
  self.schedule();self.assertEqual(self.store.tick(False,self.now+61),[]);self.assertEqual(self.store.get(self.item['id'])['schedule']['status'],'blocked')
 def test_missed_time_and_cancel(self):
  self.schedule();self.store.tick(True,self.now+400);self.assertEqual(self.store.get(self.item['id'])['schedule']['status'],'missed');self.store.set_schedule(self.item['id'],None);self.assertIsNone(self.store.get(self.item['id'])['schedule'])
 def test_reject_past_time(self):
  with self.assertRaises(ValueError):self.schedule(-10)
class RenameTests(unittest.TestCase):
 def test_rename_preserves_identity_steps_schedule(self):
  with tempfile.TemporaryDirectory() as folder:
   s=TaskStore(Path(folder)/'tasks.json');s.start('原名称');s.add({'type':'key','key':'home'},'launcher');t=s.finish();updated=s.rename(t['id'],'我的工作时间');self.assertEqual(updated['id'],t['id']);self.assertEqual(updated['steps'],t['steps']);self.assertEqual(s.get(t['id'])['name'],'我的工作时间')
 def test_empty_name_rejected(self):
  with tempfile.TemporaryDirectory() as folder:
   with self.assertRaises(ValueError):TaskStore(Path(folder)/'tasks.json').rename('id',' ')
class EditStepsTests(unittest.TestCase):
 def test_edit_deletes_selected_steps_and_preserves_id(self):
  with tempfile.TemporaryDirectory() as folder:
   s=TaskStore(Path(folder)/'tasks.json');s.start('旧名称');s.add({'type':'key','key':'home'},'');s.add({'type':'key','key':'back'},'');t=s.finish();edited=s.edit(t['id'],'新名称',[1]);self.assertEqual(edited['id'],t['id']);self.assertEqual(edited['steps'][0]['action']['key'],'back');self.assertEqual(s.get(t['id'])['name'],'新名称')
 def test_empty_steps_do_not_overwrite_task(self):
  with tempfile.TemporaryDirectory() as folder:
   s=TaskStore(Path(folder)/'tasks.json');s.start('保留');s.add({'type':'key','key':'home'},'');t=s.finish()
   with self.assertRaises(ValueError):s.edit(t['id'],'新名称',[])
   self.assertEqual(s.get(t['id']),t)
class ExecutionOptionsTests(unittest.TestCase):
 def test_interval_and_checks_are_saved(self):
  with tempfile.TemporaryDirectory() as folder:
   s=TaskStore(Path(folder)/'tasks.json');s.start('测试');s.add({'type':'key','key':'home'},'');t=s.finish();r=s.edit(t['id'],'测试',[0],interval=2,checks=[True]);self.assertEqual(r['intervalSeconds'],2);self.assertTrue(r['steps'][0]['screenshotCheck'])
 def test_invalid_interval_is_rejected(self):
  with tempfile.TemporaryDirectory() as folder:
   s=TaskStore(Path(folder)/'tasks.json')
   with self.assertRaises(ValueError):s.edit('x','测试',[0],interval=-1)
class SavedExecutionTests(unittest.TestCase):
 def test_unchecked_steps_do_not_take_screenshots(self):
  import importlib.util
  from unittest.mock import Mock,patch
  spec=importlib.util.spec_from_file_location('saved_backend',Path(__file__).resolve().parents[1]/'app/backend.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
  b.tasks.scope='test-device';phone=Mock();item={'deviceId':'test-device','name':'测试','intervalSeconds':2,'steps':[{'action':{'type':'key','key':'home'}}]}
  with patch.object(b,'phone',phone),patch.object(b.stop,'wait',return_value=False) as wait:
   b.run_saved_task(item)
  phone.ai_image.assert_not_called();self.assertEqual(b.task_result['status'],'completed');wait.assert_called_with(2.0)
class DeviceTaskTests(unittest.TestCase):
 def test_isolation_and_mutation_preserves_other_phone(self):
  with tempfile.TemporaryDirectory() as folder:
   s=TaskStore(Path(folder)/'tasks.json')
   def create(device,name):
    s.scope=device;s.start(name);s.add({'type':'key','key':'home'},'');return s.finish()
   a=create('phoneA','A');b=create('phoneB','B');self.assertEqual([t['name'] for t in s.list()],['B'])
   with self.assertRaises(ValueError):s.rename(a['id'],'wrong')
   s.rename(b['id'],'B2');s.delete(b['id']);s.scope='phoneA';self.assertEqual(s.get(a['id'])['name'],'A')
 def test_legacy_claim_is_explicit(self):
  with tempfile.TemporaryDirectory() as folder:
   s=TaskStore(Path(folder)/'tasks.json');s.start('old');s.add({'type':'key','key':'home'},'');t=s.finish();s.scope='phoneA';self.assertEqual(s.list(),[]);s.claim_legacy();self.assertEqual(s.get(t['id'])['deviceId'],'phoneA')
