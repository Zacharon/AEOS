"""Local Windows qualification; raw paths/logs stay in caller-owned work directory."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile

REPO = Path(__file__).absolute().parents[1]
NEW = "agentic-engineering-os-2026.10.09-public.3"
OLD = "agentic-engineering-os-2026.10.09-public.2"

def extract_verified(archive_path, destination, expected):
    """Bind the complete ZIP member set and bytes BEFORE creating any output."""
    import build_public
    guard=build_public.checker()
    destination=guard.safe_path(destination)
    archive_path=guard.safe_path(archive_path)
    if destination.exists():
        raise ValueError("Extraction requires an absent destination")
    with zipfile.ZipFile(archive_path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or set(names)!=set(expected):
            raise ValueError("Archive member allowlist differs")
        for name in names:
            guard.manifest_path(name)
            if z.read(name)!=expected[name]:
                raise ValueError("Archive bytes differ: "+name)
    destination.mkdir(parents=True)
    for name,raw in sorted(expected.items()):
        path=guard.safe_path(destination/guard.manifest_path(name))
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("xb") as f:
            f.write(raw)
    guard.check(destination)

def extract_public_3(destination):
    import build_public
    expected=build_public.payload()
    path=REPO/"distribution"/(NEW+".zip")
    if path.read_bytes()!=build_public.archive(expected):
        raise ValueError("Public.3 ZIP differs from deterministic public allowlist")
    extract_verified(path,destination,expected)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_local_links(path,text):
    """Resolve template links where the reviewed overlay will be installed."""
    targets=re.findall(r'\]\(([^\s)]+)\)',text) if path.suffix==".md" else re.findall(r'(?:href|src)="([^"]+)"',text)
    overlay_root=REPO/"tools/package_overrides"
    link_base=(REPO/"distribution"/NEW/path.relative_to(overlay_root)).parent if path.is_relative_to(overlay_root) else path.parent
    links=0
    for target in targets:
        if re.match(r"[a-z]+:|#",target):
            continue
        target=target.split("#",1)[0]
        if target and not (link_base/target).exists():
            raise RuntimeError("Missing public link: "+path.relative_to(REPO).as_posix()+" -> "+target)
        links+=1
    return links

def qualify(work):
    if os.name != "nt" or sys.version_info[:3] != (3,14,5):
        raise ValueError("This qualification surface is Windows PowerShell / CPython 3.14.5 only")
    package=work/"extracted package"
    output=work/"aeos first run"
    # Startup owns startup.log/build.json and the extracted demo. Qualification
    # requires new step evidence; saved summaries never substitute execution.
    prior_steps=[p for p in work.glob("*.log") if p.name!="startup.log"]
    prior_steps.extend(work/name for name in ("steps.json","public-safe-receipt.json","old extracted package","fresh shell continuation.ps1") if (work/name).exists())
    if prior_steps:
        raise ValueError("Prior qualification evidence is preserved; use a fresh work directory")
    checks=[]
    def run(name, command, cwd=package, expected=0, env=None):
        saved=work/(name+".log")
        if saved.exists():
            raise ValueError("Prior step log is preserved; use a fresh work directory")
        result=subprocess.run(command,cwd=cwd,capture_output=True,text=True,timeout=360,env=env)
        with saved.open("x",encoding="utf8") as f:
            f.write(result.stdout+"\n"+result.stderr)
        if result.returncode!=expected:
            raise RuntimeError(f"{name}: expected {expected}, got {result.returncode}; inspect local log")
        check={"name":name,"exit_code":result.returncode,"expected_exit_code":expected}
        count=re.search(r"Ran (\d+) tests?\b",result.stderr)
        if count:
            check["tests"]=int(count[1])
            skipped=re.search(r"skipped=(\d+)",result.stderr)
            check["skips"]=int(skipped[1]) if skipped else 0
        checks.append(check)
        (work/"steps.json").write_text(json.dumps(checks,indent=2)+"\n",encoding="utf8")
        return result
    py=[sys.executable,"-B"]
    run("runtime",py+["-c","import sys,yaml,jsonschema,importlib.metadata as m; print(sys.version); print(m.version('PyYAML')); print(m.version('jsonschema'))"])
    run("repeat-build",py+[str(REPO/"tools/build_public.py")],REPO)
    run("package",py+["scripts/check_package.py","."])
    run("package-optimized",py+["-O","scripts/check_package.py","."])
    run("package-env-optimized",py+["scripts/check_package.py","."],env={**os.environ,"PYTHONOPTIMIZE":"1"})
    suites={"handoff":"vault/09_TOOLS/agent_runner_v1/unified_handoff", "packet":"vault/09_TOOLS/agent_runner_v1/scripts/tests", "librarian":"vault/00_SYSTEM/AGENTIC_LIBRARIAN/tests", "integrity-and-first-run":"scripts"}
    for name,directory in suites.items():
        run("new-"+name,py+["-m","unittest","discover","-s",directory,"-p","test_*.py"])
    run("builder-tests",py+["-m","unittest","discover","-s","tests","-p","test_*.py"],REPO)
    old=work/"old extracted package"
    old_root=REPO/"distribution"/OLD
    import build_public
    build_public.checker().check(old_root)
    old_manifest=json.loads((old_root/"MANIFEST.json").read_text())
    old_expected={row["path"]:(old_root/row["path"]).read_bytes() for row in old_manifest["files"]}
    old_expected["MANIFEST.json"]=(old_root/"MANIFEST.json").read_bytes()
    extract_verified(REPO/"distribution"/(OLD+".zip"),old,old_expected)
    run("old-package",py+["scripts/check_package.py","."],old)
    rejected=run("old-literal-output-refusal",py+["scripts/demo.py","--output","../aeos-first-run"],old,expected=1)
    if "Parent traversal is forbidden" not in rejected.stderr or (work/"aeos-first-run").exists():
        raise RuntimeError("Old documented refusal was not reproduced before output creation")
    for name,directory in suites.items():
        run("old-"+name,py+["-m","unittest","discover","-s",directory,"-p","test_*.py"],old)
    start=(output/"START_HERE.md").read_text(encoding="utf8")
    command=re.search(r"```powershell\n(.*?)\n```",start,re.S).group(1)
    continuation=work/"fresh shell continuation.ps1"
    continuation.write_text("$ErrorActionPreference = 'Stop'\n"+command+"\nexit $LASTEXITCODE\n",encoding="utf8")
    review=run("fresh-shell-continuation",["powershell.exe","-NoProfile","-NonInteractive","-File",str(continuation)],work)
    receipt=json.loads((output/"RESULT.json").read_text())
    if not (receipt["owner_decision"]=="pending" and receipt["gold_applied"] is False
            and receipt["ai_worker_invoked"] is False and receipt["h3_verdict"] is None
            and receipt["stale_and_missing_refused"] is True and receipt["source_count_done"]==2):
        raise RuntimeError("Synthetic authority boundaries or fault checks differ")
    logs=json.loads((output/"commands.json").read_text())
    if len([r for r in logs if r["exit_code"]==2])!=2:
        raise RuntimeError("Expected separate stale and missing refusals")
    run("package-after-startup-and-tests",py+["scripts/check_package.py","."])
    zip_path=REPO/"distribution"/(NEW+".zip")
    with zipfile.ZipFile(zip_path) as z:
        names=z.namelist()
        files={p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()}
        if set(names)!=files or len(names)!=len(set(names)):
            raise RuntimeError("Archive/extraction exact set differs")
        for name in names:
            if z.read(name)!=(package/name).read_bytes():
                raise RuntimeError("Archive/extracted bytes differ")
            if "__pycache__" in name or Path(name).is_absolute() or ".." in Path(name).parts:
                raise RuntimeError("Unsafe archive entry")
    if sha(zip_path)!=sha(REPO/"site/downloads"/(NEW+".zip")):
        raise RuntimeError("Download copy differs")
    scan=[]
    for base in (REPO/"tools",REPO/"tests",REPO/".github",REPO/"distribution"/NEW):
        scan.extend(p for p in base.rglob("*") if p.is_file())
    scan.extend(REPO/p for p in ("README.md","docs/ARCHITECTURE.md","docs/FIRST_RUN_QUALIFICATION.md","site/index.html","site/first-run.html","site/verification.html","site/architecture.html","site/verification-public.3.json"))
    forbidden=re.compile(r"[A-Za-z]:[\\/]Users[\\/]|[\\/]home[\\/][^/]+[\\/]|sk-[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+",re.I)
    links=0
    for path in scan:
        if path.suffix.lower() not in {".md",".html",".json",".py",".ps1",".yml",".txt"}:
            continue
        text=path.read_text(encoding="utf8")
        if forbidden.search(text):
            raise RuntimeError("Public privacy pattern in "+path.relative_to(REPO).as_posix())
        if path.suffix in {".md",".html"}:
            links+=validate_local_links(path,text)
    first=(package/"FIRST_RUN.md").read_text(encoding="utf8")
    shared=(REPO/"tools/first_run_commands.ps1").read_text(encoding="utf8").rstrip()
    import html
    for path in [package/"FIRST_RUN.md",package/"ARCHITECTURE.md",REPO/"docs/ARCHITECTURE.md",REPO/"site/first-run.html",REPO/"site/architecture.html"]:
        if shared not in html.unescape(path.read_text(encoding="utf8")):
            raise RuntimeError("Current command definition drifted: "+path.name)
    result={"schema_version":3,"verified_date":"2026-10-09","result":"PUBLIC_FIRST_RUN_CANDIDATE_LOCAL_CHECKS_PASSED",
        "archive":{"file":"downloads/"+NEW+".zip","sha256":sha(zip_path),"manifest_sha256":sha(package/"MANIFEST.json"),"bytes":zip_path.stat().st_size,"file_count":len(names),"manifest_payload_entries":len(names)-1,"copies_identical":True,"fresh_extraction":True,"all_bytes_and_file_set_verified":True},
        "environment":{"os":"Windows","shell":"Windows PowerShell fresh -NoProfile process","python":"3.14.5","PyYAML":"6.0.3","jsonschema":"4.26.0","prerequisite_basis":"New virtual environment outside payload; documented pinned prerequisites installed through pip"},
        "tests":{"new_package":sum(c.get("tests",0) for c in checks if c["name"].startswith("new-")),"old_public_2":sum(c.get("tests",0) for c in checks if c["name"].startswith("old-")),"builder":sum(c.get("tests",0) for c in checks if c["name"]=="builder-tests"),"skips":sum(c.get("skips",0) for c in checks)},
        "first_run":{"shared_literal_commands_executed":True,"paths_with_spaces":True,"fresh_shell_exact_interpreter":True,"old_literal_parent_output_refused":True,"stale_and_missing_refused":True,"demo_result":"DEMO_LOCAL_PASSED","owner_decision":"pending","gold_applied":False,"ai_worker_invoked":False,"h3_verdict":None},
        "privacy":{"result":"BOUNDED_SCAN_AND_LINK_CHECK_PASSED","files_scanned":len(scan),"links_checked":links,"raw_logs":"Retained outside repository and payload","limit":"Bounded patterns and exact file-set review; not comprehensive credential detection"},
        "ci":{"status":"NOT_RUN","defined_surface":"Windows PowerShell / CPython 3.14.5","linux":"NOT_DEFINED_NOT_RUN","limits":"Synthetic-only; pinned actions, contents read permission, 20-minute timeout, no uploads, deployment, provider credentials or release"},
        "browser":{"status":"NOT_RUN_YET"},"independent_review":{"status":"NOT_INCLUDED_IN_WORKER_QUALIFICATION","basis":"Separate independent H3 review required; worker receipt supplies local H1/H2 evidence only"},
        "history":{"public_1_and_2":"Frozen folders, archives and receipts preserved byte-for-byte; old literal first-run failure reproduced"},
        "checks":checks,"limits":["No hosted CI run or push","Linux/macOS unverified","No live model/provider, native confinement, owner acceptance, production or Gold action"]}
    (work/"public-safe-receipt.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--work")
    group.add_argument("--extract-public-3")
    args=p.parse_args()
    if args.extract_public_3:
        extract_public_3(Path(args.extract_public_3).absolute())
    else:
        qualify(Path(args.work).absolute())
