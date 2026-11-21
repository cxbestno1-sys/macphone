"""Bundle local Python and relocate its non-system dylibs for another Mac."""
from pathlib import Path
import shutil,subprocess,os,sys
source=Path('/opt/homebrew/opt/python@3.13/Frameworks/Python.framework/Versions/3.13').resolve();dest=Path(sys.argv[1]).resolve()
if dest.exists():shutil.rmtree(dest)
(dest/'bin').mkdir(parents=True);shutil.copy2(source/'bin/python3.13',dest/'bin/python3');shutil.copy2(source/'Python',dest/'Python')
shutil.copytree(source/'lib/python3.13',dest/'lib/python3.13',ignore=shutil.ignore_patterns('site-packages','__pycache__','test','tests','readline*.so'))
shutil.copy2(source/'Resources/English.lproj/Documentation/License.rtf',dest/'LICENSE.rtf') if (source/'Resources/English.lproj/Documentation/License.rtf').exists() else None
shutil.copytree(source/'Resources/Python.app',dest/'Resources/Python.app')
vendor=dest/'lib/vendor';vendor.mkdir();mapping={str(source/'Python'):dest/'Python'}
queue=[dest/'bin/python3',dest/'Python',dest/'Resources/Python.app/Contents/MacOS/Python']+list((dest/'lib/python3.13/lib-dynload').glob('*.so'));seen=set()
while queue:
 file=queue.pop()
 if file in seen:continue
 seen.add(file);out=subprocess.check_output(['/usr/bin/otool','-L',str(file)],text=True)
 for line in out.splitlines()[1:]:
  dep=line.strip().split(' (')[0]
  if not dep.startswith('/opt/homebrew/'):continue
  key=str(Path(dep).resolve())
  if key not in mapping:
   target=vendor/Path(dep).name
   if not target.exists():shutil.copy2(Path(dep).resolve(),target)
   mapping[key]=target;queue.append(target)
  relative=os.path.relpath(mapping[key],file.parent)
  subprocess.run(['/usr/bin/install_name_tool','-change',dep,'@loader_path/'+relative,str(file)],check=True,capture_output=True)
for file in seen:subprocess.run(['/usr/bin/codesign','--force','--sign','-',str(file)],check=True,capture_output=True)
licenses=dest/'licenses';licenses.mkdir(exist_ok=True)
for package in Path('/opt/homebrew/Cellar').glob('*'):
 if package.name not in ('python@3.13','openssl@3','xz','zstd','sqlite','libffi','mpdecimal','readline','ncurses','bzip2','expat'):continue
 for version in package.iterdir():
  for pattern in ('LICENSE*','COPYING*'):
   for file in version.glob(pattern):
    if file.is_file():shutil.copy2(file,licenses/(package.name+'-'+file.name))
print('Bundled portable Python:',len(seen),'Mach-O files')
