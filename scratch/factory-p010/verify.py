import json,hashlib,subprocess,sys
from pathlib import Path
root=Path.cwd(); s=root/'scratch/factory-p010'; w=Path(r'C:\Users\zacha\Workspace\_artifacts\2026-11-16_ai_factory_portfolio\projects\p010\worker'); source=Path(r'C:\Users\zacha\Workspace\20_Products\Agentic_Engineering_OS_Setup'); pkg=s/'package'; out=s/'aeos first run'
def inventory(base):
 p=subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=base,stdout=subprocess.PIPE,check=True)
 return {f:hashlib.sha256((base/f).read_bytes()).hexdigest() for f in p.stdout.decode().split('\0') if f and not f.startswith('scratch/factory-p010/') and (base/f).is_file() and (base/f).name != '.env' and not (base/f).name.startswith('.env.')}
before=json.loads((w/'before-hashes.json').read_text()); after={str(p):inventory(p) for p in (root,source)}
(w/'after-hashes.json').write_text(json.dumps(after,indent=2)); diff={p:{'added':sorted(set(after[p])-set(before[p])),'removed':sorted(set(before[p])-set(after[p])),'changed':sorted(k for k in set(before[p])&set(after[p]) if before[p][k]!=after[p][k])} for p in before}
commands=json.loads((out/'commands.json').read_text()); reviews=[{'exit_code':x['exit_code'],'stdout':x['stdout'],'stderr':x['stderr']} for x in commands if 'review' in x['command']]
proposal=list((out/'vault').rglob('*PROP-2026-000001*'))
print('proposal candidates',proposal)
checks={'inventory_diff':diff,'review_calls':reviews,'output_unchanged':json.loads((w/'existing-output-evidence.json').read_text())['unchanged'],'requirements_unchanged':(w/'requirements-before.sha256').read_text()==(w/'requirements-after.sha256').read_text(),'gold_exists':(out/'vault/04_RESEARCH/Sample_summary.md').exists()}
(w/'independent-observations.json').write_text(json.dumps(checks,indent=2))
print(json.dumps({'inventory_diff':diff,'review_exits':[r['exit_code'] for r in reviews],'output_unchanged':checks['output_unchanged'],'requirements_unchanged':checks['requirements_unchanged'],'gold_exists':checks['gold_exists']},indent=2))
