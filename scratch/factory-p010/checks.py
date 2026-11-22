import os,subprocess,sys,json,hashlib,importlib.util
from pathlib import Path
root=Path.cwd(); s=root/'scratch/factory-p010'; w=Path(r'C:\Users\zacha\Workspace\_artifacts\2026-11-16_ai_factory_portfolio\projects\p010\worker'); pkg=s/'package'; env=s/'aeos env'; output=s/'aeos first run'
os.environ.update(TEMP=str(s/'temp'),TMP=str(s/'temp'),PYTHONDONTWRITEBYTECODE='1',PIP_CACHE_DIR=str(s/'pip-cache'),PIP_DISABLE_PIP_VERSION_CHECK='1')
def run(name,cmd,cwd=root):
 p=subprocess.run([str(x) for x in cmd],cwd=cwd,env=os.environ,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (w/(name+'.log')).write_text('cwd: '+str(cwd)+'\ncommand: '+subprocess.list2cmdline([str(x) for x in cmd])+'\nexit: '+str(p.returncode)+'\n'+p.stdout,encoding='utf8')
 print(name,p.returncode,flush=True); return p.returncode
py=sys.executable
run('boundary-tests',[py,'-B','-m','unittest','discover','-s','scripts','-p','test_check_public_boundary.py'])
run('boundary-scan',[py,'-B','scripts/check_public_boundary.py'])
spec=importlib.util.spec_from_file_location('boundary',root/'scripts/check_public_boundary.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
findings=[]
for p in pkg.rglob('*'):
 if p.is_file(): findings += m.scan_bytes(p.relative_to(pkg).as_posix(),p.read_bytes())
(w/'extracted-scan.json').write_text(json.dumps({'files':sum(p.is_file() for p in pkg.rglob('*')),'findings':findings,'limit':'bounded marker/name scan; binary content not scanned as text'},indent=2))
print('extracted scan findings',len(findings),flush=True)
req=pkg/'requirements.txt'; (w/'requirements-before.sha256').write_text(hashlib.sha256(req.read_bytes()).hexdigest())
if env.exists() or output.exists(): raise RuntimeError('sibling already exists')
if run('venv',[py,'-B','-m','venv',env]): raise SystemExit('venv failed')
vp=env/'Scripts/python.exe'
if run('install',[vp,'-B','-m','pip','install','-r',req],pkg): raise SystemExit('install failed')
if run('package-check',[vp,'-B','scripts/check_package.py','.'],pkg): raise SystemExit('package check failed')
if run('demo',[vp,'-B','scripts/demo.py','--output',output],pkg): raise SystemExit('demo failed')
run('continuation',[vp,'-B',output/'vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py','review','--bundle',output/'handoff','--vault-root',output/'vault'],s)
def hashes(p): return {q.relative_to(p).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in p.rglob('*') if q.is_file()}
b=hashes(output); code=run('existing-output',[vp,'-B','scripts/demo.py','--output',output],pkg); a=hashes(output)
(w/'existing-output-evidence.json').write_text(json.dumps({'exit':code,'before':b,'after':a,'unchanged':a==b},indent=2))
run('package-tests',[vp,'-B','-m','unittest','discover','-s','scripts','-p','test_*.py'],pkg)
(w/'requirements-after.sha256').write_text(hashlib.sha256(req.read_bytes()).hexdigest())
