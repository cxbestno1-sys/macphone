import subprocess,shlex,time
from pathlib import Path,PurePosixPath

def remote_path(value):
 if not isinstance(value,str) or '\n' in value or '\x00' in value:raise ValueError('手机路径无效')
 p=PurePosixPath(value)
 if '..' in p.parts or not (value=='/sdcard' or value.startswith('/sdcard/')):raise ValueError('仅支持手机共享存储 /sdcard')
 return str(p)
def execute(phone,operation,data):
 phone.ensure_connected()
 def run(*args):
  p=subprocess.run([str(__import__('pathlib').Path(__file__).parent/'runtime/adb'),'-s',phone.serial]+list(args),capture_output=True,timeout=600)
  out=(p.stdout+p.stderr).decode(errors='replace')
  if p.returncode or 'Failure [' in out:raise RuntimeError(out[-2000:] or '传输失败')
  return out
 if operation=='list':
  path=remote_path(data.get('path','/sdcard/Download'))
  out=run('shell','ls -1Ap -- '+shlex.quote(path))
  items=[{'name':line.rstrip('/'),'directory':line.endswith('/'),'path':path.rstrip('/')+'/'+line.rstrip('/')} for line in out.splitlines() if line and line not in ('./','../')]
  return {'path':path,'items':items}
 if operation in ('push','install'):
  local=Path(data.get('local','')).expanduser().resolve()
  if not local.is_file():raise ValueError('请选择电脑上的文件')
  if operation=='install':
   if local.suffix.lower()!='.apk':raise ValueError('请选择 APK 安装包；暂不支持 XAPK/APKS')
   out=run('install','--no-incremental','-r',str(local))
   if 'Success' not in out:raise RuntimeError('未确认安装成功：'+out[-1500:])
   return {'message':'APK 安装成功：'+local.name}
  directory=remote_path(data.get('path','/sdcard/Download'));target=directory.rstrip('/')+'/'+local.name
  if '\n' in local.name:raise ValueError('文件名不支持换行符')
  check=subprocess.run([str(Path(__file__).parent/'runtime/adb'),'-s',phone.serial,'shell','test -e '+shlex.quote(target)],capture_output=True,timeout=10)
  if check.returncode==0:raise ValueError('手机上存在同名文件，请先更换文件名，避免覆盖')
  run('push',str(local),target);return {'message':'已发送到手机：'+target}
 if operation=='pull':
  path=remote_path(data['path']);folder=Path.home()/'Downloads/MacPhone'/time.strftime('%Y%m%d-%H%M%S');folder.mkdir(parents=True,exist_ok=True)
  target=folder/PurePosixPath(path).name
  if target.exists():raise ValueError('下载目录已存在同名文件，请稍后重试')
  run('pull',path,str(target));return {'message':'已拷贝到电脑：'+str(target),'local':str(target)}
 raise ValueError('未知文件操作')
