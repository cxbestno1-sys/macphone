import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from transfers import remote_path
class TransferPaths(unittest.TestCase):
 def test_shared_storage(self):self.assertEqual(remote_path('/sdcard/Download'),' /sdcard/Download'.strip())
 def test_private_and_traversal_paths_rejected(self):
  for value in ['/data/data','/sdcard/../data','/sdcard/a\nb','/sdcard-other']:
   with self.assertRaises(ValueError):remote_path(value)
