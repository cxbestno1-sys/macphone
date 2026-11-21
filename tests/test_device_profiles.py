import unittest,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from device_profiles import DeviceProfiles
class ProfileTests(unittest.TestCase):
 def test_aliases_share_name_and_phones_stay_separate(self):
  with tempfile.TemporaryDirectory() as folder:
   p=DeviceProfiles(Path(folder)/'profiles.json');p.bind('USB','phoneA');p.bind('192.168.1.2:5555','phoneA');p.bind('USB-B','phoneB');p.rename('phoneA','工作手机');self.assertEqual(p.name(serial='USB'),'工作手机');self.assertEqual(p.name(serial='192.168.1.2:5555'),'工作手机');self.assertEqual(p.name(serial='USB-B'),'');p.rename('phoneA','');self.assertEqual(p.name(serial='USB'),'')
