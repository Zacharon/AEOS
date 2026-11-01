# Bounded issue handoff

One controller, one fixed synthetic task, one candidate awaiting independent H3. This consolidation uses PR #10's public.4 handoff/rationale/patch pipeline and PR #11's issue parsing, inventory checks and portability matrix. See [the engineering comparison](../../docs/ISSUE_HANDOFF_REVIEW.md) and [verification receipt](local-verification.json).

The task writes exactly one synthetic document, `01_PROJECTS/IssueDemo/output.md`, and returns a source-hashed issue inventory as a bundle artifact. Issue text, labels and URLs are untrusted data. They never select commands, paths, scope, authority, providers or acceptance criteria. No autonomous worker, scheduler, authenticated approval system or live GitHub fetch is implemented.

## Requirements and boundaries

Use Git 2.28+ and CPython 3.11+. Only the Python standard library is needed. Windows 10 is a compatibility target; hosted Windows evidence does not establish execution on the operator's Windows 10 machine. Docker, paid APIs, accounts and API keys are not required. Frozen public.4 distribution/archive/site bytes are unchanged.

Keep the source checkout and disposable run separate. Use a new absolute sibling destination with an existing parent and no parent traversal. Writes are exclusive. A rejection, timeout, missing result or stale source stops progress without automatic repair or redispatch. Preserve failed runs; reconcile manually and choose a fresh destination. AEOS's three-cycle maximum remains a stop rule, not an automated loop.

A Git worktree is not an OS sandbox. Enforce worker filesystem/network/credential restrictions in the operator/tool environment. Keep controller records and source code outside worker write access. Hashes detect drift relative to retained trusted records; a process able to rewrite those records can forge them. CLI opt-in records authorization for this fixed local synthetic task, without authenticating a person. It grants no authority for real-task execution or consequential actions.

## Local demonstration (PowerShell)

Run from the source checkout. Inspect the draft and context before invoking the authorization switch:

```powershell
$ErrorActionPreference = 'Stop'
$repo = (Get-Location).Path
$py = (Get-Command python).Source
$adapter = Join-Path $repo 'prototypes/issue_handoff/issue_handoff.py'
$fixture = Join-Path $repo 'prototypes/issue_handoff/synthetic-issue.json'
$run = Join-Path (Split-Path $repo -Parent) 'aeos-issue-demo-001'
& $py -B $adapter prepare --issue $fixture --output $run
if ($LASTEXITCODE -ne 0) { throw 'Prepare stopped' }
Get-Content (Join-Path $run 'worktree/runs/issue/task_packet.scoped-draft.md')
Get-Content (Join-Path $run 'worktree/01_PROJECTS/IssueDemo/ISSUE_DATA.md')

# Authorize only this disposable fixed synthetic task.
& $py -B $adapter handoff --run $run --allow-synthetic-local-execution
if ($LASTEXITCODE -ne 0) { throw 'Handoff stopped' }
# Deterministic Python fixture; no model or independent reviewer.
& $py -B $adapter synthetic-worker --run $run
if ($LASTEXITCODE -ne 0) { throw 'Fixture stopped' }
& $py -B $adapter verify --run $run
if ($LASTEXITCODE -ne 0) { throw 'Verification stopped' }
Get-Content (Join-Path $run 'controller/verification-0000.json')
```

On Bash, use the same four commands with an explicit Python interpreter, absolute adapter/fixture paths and a fresh absolute sibling run path; stop after any nonzero exit. No background process is installed.

Expected state: `candidate_checks_passed_awaiting_independent_h3`. The receipt leaves `h3_verdict: null`, owner acceptance unrecorded and `pr_created: false`. The candidate output stays uncommitted. The verifier checks the generated patch with `git apply --check` against the unchanged seed and records the result. A conflicting seed file prevents a success receipt.

## Local GitHub export inspection

With an already authenticated GitHub CLI, an operator may export an explicitly selected public issue:

```powershell
gh issue view <issue-number> --repo <owner/repository> --json number,title,body,url,labels | Out-File -Encoding utf8 issue-export.json
if ($LASTEXITCODE -ne 0) { throw 'Export stopped' }
& $py -B $adapter inspect-export --issue (Join-Path $repo 'issue-export.json')
if ($LASTEXITCODE -ne 0) { throw 'Inspection stopped' }
```

The explicit UTF-8 encoding also supports Windows PowerShell 5. This command only parses the local export and prints the number, label count and source hashes. It creates no run, packet or authorization; it does not fetch or follow links. Do not commit runtime exports.

The export schema has exactly `number,title,body,url,labels`. It rejects duplicate JSON keys, oversized input, malformed/mismatched GitHub issue URLs, invalid label names and likely secret markers. Only label names survive normalization. Text is serialized with Markdown/HTML delimiters escaped.

`prepare` additionally requires `synthetic: true`, an explicit human classification assertion. It still runs the same fixed task regardless of what the exported issue asks for. Do not add this flag to ordinary work to bypass the synthetic-only execution boundary. General issue execution and authenticated authorization remain future work.

## Execution contract

| Transition | Implemented behavior | Remaining human boundary |
|---|---|---|
| Prepare | Validate input, create synthetic project/worktree, call public.4 `build_task_packet.py`, retain original/scoped drafts, pin controller and prepared file hashes | Inspect the fixed packet and selected context; no dispatch yet |
| Handoff | Require CLI opt-in, reject prepared-tree drift before staging, freeze HEAD/branch, run public.4 `build`/`check`, retain manifest/full-file/rationale baselines | Transport approved context to the selected worker manually |
| Worker | Optional deterministic fixture writes exact bytes, inventory, rationale and result template | No provider launched; manual T3/assistant route remains untested |
| Verify | Check package/controller/locator/branch/source integrity, reject unexpected paths before reading them, include ignored/untracked files, validate actual scope/result/artifacts, recompute acceptance and inventory, run `review`/`complete`, check patch applyability | Mechanical H1/H2 evidence only; independent H3 and owner integration decision remain pending |

Git subprocesses have no stdin or shell, a 60-second timeout, captured events, no ambient `GIT_*` variables/global/system config/template hooks, and explicit hooks/signing/line-ending/fsmonitor settings. These are defense in depth for a local fixture, not containment of hostile native code. No child agents, commit of candidate output, push, PR creation, merge, deploy, publish, send, spend or Gold/canonical writeback is implemented or authorized by the prototype.

## Manual worker return

Use `prepare` and authorized `handoff`, then omit `synthetic-worker`. Read generated `HANDOFF.md`, the bundle's full `execution_brief.md`, packet and four selected snapshots. Immediately before transport, run the public.4 checker:

```powershell
$tools = Join-Path $repo 'distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff'
$bundle = Join-Path $run 'bundle'
$worktree = Join-Path $run 'worktree'
& $py -B (Join-Path $tools 'handoff.py') check --bundle $bundle --vault-root $worktree
if ($LASTEXITCODE -ne 0) { throw 'Context is not current' }
```

Root the manual worker at the disposable worktree. Its only writable worktree path is the exact output file, with UTF-8/LF bytes and a final newline:

```text
# Synthetic issue handoff

The bounded local handoff produced this candidate.
```

Return `bundle/worker_result.json` using the existing template, with `execution_state: ready_for_review`, the exact declared output path, passing captured checks, and no proposed writeback/H3/approval claims. Include and hash these artifacts:

- `artifacts/acceptance.json`: captured output from `issue_handoff.py acceptance --run <run>`.
- `artifacts/inventory.json`: exactly `issue_number`, `label_count` and `source_sha256`; derive values from the pinned `ISSUE_DATA.md` snapshot, citing its manifest SHA-256. The controller independently compares all three fields.
- `artifacts/report.md`: existing AEOS `code-rationale` fence. Use the retained rationale baseline digest from `controller/handoff.json` and `code_rationale.py changes --root <worktree> --baseline <baseline> --baseline-sha256 <digest>` to derive coverage. Follow public.4 [CODE_RATIONALE.md](../../distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/CODE_RATIONALE.md).

The controller runs `verify` after return. Never invoke the deterministic fixture to repair or overwrite a partially executed manual task.

## Evidence and acceptance

`controller/` retains issue export/normalized data, original scaffold, draft/controller/Git-locator hashes, authorization record, frozen Git identity, manifest and file/rationale baselines, started/completed command events, candidate patches and fresh verification receipts. `bundle/` contains existing public.4 context/result contracts and returned artifacts. Runtime logs include absolute paths; keep them local. Commit only public-safe synthetic summaries.

A separate reviewer who did not implement the consolidation must inspect packet/scope, reproduce all acceptance checks, inspect actual changes/patch, check every claim and record VERIFIED, PARTIAL or FAIL separately. The implementer cannot give its own result H3. Do not merge because CI is green. Owner acceptance is a separate decision. Manual provider return, local Windows 10 execution and independent H3 remain acceptance requirements.

## Reproducible implementation checks

```powershell
python -B -m unittest discover -s tests -p 'test_*.py' -v
python -B -m unittest discover -s distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff -p 'test_*.py' -v
python -B distribution/agentic-engineering-os-2026.10.17-public.4/scripts/check_package.py
python -B -m unittest discover -s scripts -p 'test_check_public_boundary.py' -v
python -B scripts/check_public_boundary.py
python -B scripts/check_public_boundary.py --history
python -B scripts/validate_candidate.py
git diff --cached --check
```

Check each exit code. Stage new files before the tracked-file scan. Label a shallow history scan as incomplete; hosted boundary CI checks full reachable history. `validate_candidate.py` requires Windows CPython 3.14.5 and separately validates the unpublished repair candidate; it does not substitute for the new prototype/public.4 matrix. The new matrix covers Windows and Ubuntu 24.04 on Python 3.11 and 3.14.5. Symlink tests may skip on Windows configurations without link-creation rights; report actual skips.
