import unittest,tempfile,sys,json,ssl,urllib.request,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from lan_pairing import LanPairing
class LanPairTests(unittest.TestCase):
 def test_single_use_and_separate_https_endpoint(self):
  with tempfile.TemporaryDirectory() as folder:
   pairing=LanPairing(Path(folder));data=pairing.start();values=urllib.parse.parse_qs(urllib.parse.urlparse(data['url']).query);port=values['port'][0];code=values['code'][0];ctx=ssl.create_default_context(cafile=str(Path(folder)/'lan-cert.pem'));ctx.check_hostname=False
   def send(value):
    req=urllib.request.Request('https://127.0.0.1:'+port+'/pair',json.dumps({'code':value,'deviceId':'test-phone','name':'test'}).encode(),{'Content-Type':'application/json'});return json.load(urllib.request.urlopen(req,context=ctx,timeout=5))
   try:
    with self.assertRaises(urllib.error.HTTPError):send('wrong')
    self.assertTrue(send(code)['ok'])
    with self.assertRaises(urllib.error.HTTPError):send(code)
    self.assertIn('test-phone',json.loads((Path(folder)/'lan-paired-devices.json').read_text()))
   finally:pairing.server.shutdown();pairing.server.server_close()
