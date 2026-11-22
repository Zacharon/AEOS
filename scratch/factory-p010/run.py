import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
root=Path.cwd(); scratch=root/'scratch/factory-p010'; worker=Path(r'C:\Users\zacha\Workspace\_artifacts\2026-11-16_ai_factory_portfolio\projects\p010\worker'); source=Path(r'C:\Users\zacha\Workspace\20_Products\Agentic_Engineering_OS_Setup')
os.environ.update(TEMP=str(scratch/'temp'),TMP=str(scratch/'temp'),PYTHONDONTWRITEBYTECODE='1',PIP_CACHE_DIR=str(scratch/'pip-cache'),PIP_DISABLE_PIP_VERSION_CHECK='1')
def inventory(base):
 p=subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=base,stdout=subprocess.PIPE,check=True)
 result={}
 for f in p.stdout.decode().split('\0'):
  if f and not f.startswith('scratch/factory-p010/'):
   q=base/f
   if q.is_file() and q.name != '.env' and not q.name.startswith('.env.'):
    result[f]=hashlib.sha256(q.read_bytes()).hexdigest()
 return result
before={str(p):inventory(p) for p in (root,source)}
(worker/'before-hashes.json').write_text(json.dumps(before,indent=2))
def run(name,cmd,cwd=root):
 p=subprocess.run([str(x) for x in cmd],cwd=cwd,env=os.environ,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (worker/(name+'.log')).write_text('cwd: '+str(cwd)+'\ncommand: '+subprocess.list2cmdline([str(x) for x in cmd])+'\nexit: '+str(p.returncode)+'\n'+p.stdout,encoding='utf8')
 print(name,p.returncode,flush=True)
 return p.returncode
archive=root/'site/downloads/agentic-engineering-os-2026.10.17-public.4.zip'; counterpart=root/'distribution/agentic-engineering-os-2026.10.17-public.4.zip'
(worker/'archive-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (archive,counterpart)},indent=2))
pkg=scratch/'package'; pkg.mkdir()
with zipfile.ZipFile(archive) as z:
 for i in z.infolist():
  target=(pkg/i.filename).resolve()
  if not target.is_relative_to(pkg.resolve()): raise ValueError('unsafe archive path')
 z.extractall(pkg)
print('package entries', [x.name for x in pkg.iterdir()],flush=True)
