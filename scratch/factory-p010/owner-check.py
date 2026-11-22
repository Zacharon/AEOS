import json,re,hashlib
from pathlib import Path
s=Path.cwd()/'scratch/factory-p010'; pkg=s/'package/vault'; out=s/'aeos first run/vault'; w=Path(r'C:\Users\zacha\Workspace\_artifacts\2026-11-16_ai_factory_portfolio\projects\p010\worker')
rx=re.compile(r'(?im)^\s*(?:owner_decision|owner_decision_by|owner_decision_at|owner_decision_note|owner_approved|approved_by|approved_at)\s*:.*$')
def fields(root):
 d={}
 for p in root.rglob('*'):
  if p.is_file():
   try: hits=rx.findall(p.read_text(encoding='utf8'))
   except (UnicodeError,OSError): continue
   if hits: d[p.relative_to(root).as_posix()]=hits
 return d
b=fields(pkg); a=fields(out); shared={k:{'before':v,'after':a.get(k)} for k,v in b.items() if a.get(k)!=v}; added={k:v for k,v in a.items() if k not in b}
proposal=out/'00_SYSTEM/AGENTIC_LIBRARIAN/silver/proposals/PROP-2026-000001.md'
result={'existing_owner_fields_changed':shared,'new_files_owner_fields':added,'proposal_frontmatter':proposal.read_text(encoding='utf8').split('---',2)[1]}
(w/'owner-fields.json').write_text(json.dumps(result,indent=2),encoding='utf8'); print(json.dumps(result,indent=2))
