import importlib.util,json,socket,threading,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
spec=importlib.util.spec_from_file_location('backend',Path(__file__).resolve().parents[1]/'app/backend.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class CompanionTests(unittest.TestCase):
 def transact(self,response,action):
  server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);received=[]
  def serve():
   with server:
    s,_=server.accept()
    with s:
     received.append(json.loads(s.makefile('rb').readline()));s.sendall((json.dumps(response)+'\n').encode())
  t=threading.Thread(target=serve);t.start();p=b.Phone();p.companion_port=server.getsockname()[1];p.companion_token='a'*32;p.ensure_awake=lambda:None;p.ensure_connected=lambda:None
  try:return p.action(action),received
  finally:t.join(2)
 def test_shared_action_routes_authenticated_request(self):
  r,seen=self.transact({'ok':True},{'type':'tap','x':.2,'y':.8});self.assertTrue(r['ok']);self.assertEqual(seen[0],{'type':'tap','x':.2,'y':.8,'token':'a'*32})
 def test_locked_phone_error_is_not_hidden_by_uhid(self):
  with self.assertRaisesRegex(RuntimeError,'锁屏'):self.transact({'ok':False,'error':'手机已锁屏'},{'type':'key','key':'home'})
 def test_missing_pairing_is_explicit(self):
  with self.assertRaisesRegex(RuntimeError,'配对'):b.Phone().companion_request({'type':'status'})
if __name__=='__main__':unittest.main()
class WifiTests(unittest.TestCase):
 def test_valid_address(self):self.assertEqual(b.Phone.wifi_address('192.168.1.2:37123'),'192.168.1.2:37123')
 def test_invalid_addresses(self):
  for address in ['','example.com:5555','192.168.1.2:0','192.168.1.2:99999','1.2.3.999:5555']:
   with self.assertRaises(ValueError):b.Phone.wifi_address(address)
class MarketFallbackTests(unittest.TestCase):
 def test_market_skips_accessibility_query(self):
  from unittest.mock import Mock
  p=b.Phone();p.companion_token='test';p.foreground=Mock(return_value='com.xiaomi.market');p.companion_request=Mock(side_effect=AssertionError('must not query market tree'));self.assertEqual(p.ui_context(),[]);p.companion_request.assert_not_called()
class DeviceListTests(unittest.TestCase):
 def test_multiple_transports_and_auth_state(self):
  from unittest.mock import Mock
  p=b.Phone();p.serial='192.168.1.2:5555';p.sock=object();p.devices=Mock(return_value='List of devices attached\nUSB123 device product:a model:Pixel_8 device:a\n192.168.1.2:5555 device model:Redmi_Note\nUSB456 unauthorized usb:1\n')
  rows=p.device_list();self.assertEqual(len(rows),3);self.assertEqual(rows[0]['transport'],'USB');self.assertEqual(rows[0]['model'],'Pixel 8');self.assertEqual(rows[1]['transport'],'Wi-Fi');self.assertTrue(rows[1]['current']);self.assertEqual(rows[2]['state'],'unauthorized')
 def test_invalid_selection_preserves_current_connection(self):
  from unittest.mock import Mock
  p=b.Phone();p.serial='active';p.sock=object();p.devices=Mock(return_value='List of devices attached\nactive device\n');p.close=Mock()
  with self.assertRaises(RuntimeError):p.connect('missing')
  p.close.assert_not_called();self.assertEqual(p.serial,'active')
class PairingIdentityTests(unittest.TestCase):
 def test_usb_wifi_share_hardware_identity(self):
  from unittest.mock import Mock
  p=b.Phone();p.adb=Mock(return_value=b'hardware-A\n');p.serial='USB-A';usb=p.pairing_identity();p.serial='192.168.1.2:5555';self.assertEqual(p.pairing_identity(),usb)
 def test_pairing_uses_device_specific_keychain_account(self):
  from unittest.mock import Mock,patch
  p=b.Phone();p.adb=Mock(return_value=b'phone-B\n')
  with patch.object(b.subprocess,'run',return_value=Mock(returncode=0,stdout=b'secret-B\n')) as run:
   self.assertEqual(p.saved_pairing(),'secret-B');args=run.call_args.args[0];self.assertEqual(args[args.index('-a')+1],'phone-B')
