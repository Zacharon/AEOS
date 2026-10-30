# Bounded GitHub issue → AEOS handoff proof of concept

This executable slice imports one **local GitHub issue JSON export**, creates an
isolated Git worktree, scaffolds a schema-v1.2 task packet with AEOS's existing
builder, and packages/checks/validates the return with public.4's existing
`handoff.py`. It performs one read-only issue inventory, not code implementation.
The deterministic synthetic demonstration stops at `candidate_needs_independent_H3`.
It never supplies independent H3, owner acceptance or integration authority.

Source baseline: public AEOS commit `f8b6258af5ed421c5c6803473ac92233378e701c`,
tree `e8c16c0ab018a979c3ca5711b08c42c60e0e2ca4`. The frozen distribution and
archives are unchanged. The adapter imports public.4's path, JSON and packet
checks and invokes the original packet-builder and handoff CLIs in fresh
processes. It does not introduce a replacement packet/result schema or verifier.

## Implemented, manual and proposed boundaries

| Transition | Status in this slice |
|---|---|
| GitHub → saved issue export | **Manual**: optional read-only `gh issue view`; not invoked by this adapter or synthetic test |
| Local export → bounded draft | **Implemented**: strict fields/size checks; issue text stays data; fixed R0 scope, Human transport, full H3 |
| New source repo → isolated issue worktree | **Implemented** using local Git; existing output paths are refused |
| Draft → actual Gate A authorization | **Manual**: human inspects scope/context and records the actual decision; default `prepare` cannot dispatch a draft |
| Synthetic fixture assignment | **Test only**: `demo` uses only the shipped fixture; its assigned status is explicitly not human approval |
| Packet → bounded context bundle | **Implemented** through AEOS `build` + `check`; hashes and live source checks preserved |
| Bundle → T3 Code/agent session | **Manual file transport**; no T3 API, provider login or subscription runtime integration |
| Synthetic worker → candidate result | **Implemented deterministic data inventory only**, no AI agent |
| Returned evidence → mechanical candidate checks | **Implemented**: `check`, `validate-result`, `review`, immutable-attempt records, inventory comparison and worktree baseline comparison |
| Independent H3 → owner acceptance/integration | **Manual and still pending**; no automatic promotion, writeback, push, merge, deployment or Gold application |
| Webhooks, issue polling, scheduling, coding agents, sandboxes, provider adapters | **Proposed, absent** |

## Requirements and local synthetic run

Python 3.11+ and Git 2.28+ on PATH. The new code and its tests use only the Python
standard library; no Docker, dependency install, model API, provider credential,
paid call, background service or network access is needed for this run. A
checkout of this repository supplies the frozen public.4 tools. No private
vault is copied or read.

From the repository root in PowerShell, choose an **absent** sibling output name:

```powershell
$ErrorActionPreference = 'Stop'
$Python = (Get-Command python).Source
$Repo = (Get-Location).Path
$Poc = Join-Path $Repo 'prototypes/issue_handoff/issue_handoff.py'
$Run = Join-Path (Split-Path $Repo -Parent) 'aeos-issue-demo-new'
& $Python -B $Poc demo --output $Run
if ($LASTEXITCODE -ne 0) { throw 'Stopped; inspect preserved audit evidence' }
& $Python -B $Poc verify --run $Run
if ($LASTEXITCODE -ne 0) { throw 'Verification stopped; do not retry automatically' }
& $Python -B -m unittest discover -s prototypes/issue_handoff -p 'test_*.py' -v
if ($LASTEXITCODE -ne 0) { throw 'Prototype tests failed' }
```

The two-label fixture includes malicious-looking scope headings, a shell
substitution, a link-fetch request and a demand to claim H3/merge. They remain
quoted JSON data. The task goal, read/write scope, executor and commands never
come from those strings. No links or attachments are followed. The test proves
this adapter does not promote those strings into commands or packet authority;
it does **not** establish that an LLM is immune to prompt injection.

Expected inventory: issue `900001`, label count `2`, exact source SHA-256. Expected
receipt: `synthetic: true`, `ai_worker_invoked: false`, `h3_verdict: null`,
`owner_acceptance: pending`, `external_actions: false`.

On Bash, the equivalent first run is:

```bash
python -B prototypes/issue_handoff/issue_handoff.py demo --output ../aeos-issue-demo-new
python -B prototypes/issue_handoff/issue_handoff.py verify --run ../aeos-issue-demo-new
```

## Saved evidence and stop behavior

| Run-relative path | Purpose |
|---|---|
| `intake.json` | Import identity, synthetic flag, issue/context hashes and tool fingerprints |
| `source/` | Newly created controller fixture repository; no pre-existing repository is modified |
| `worktree/` | Separate `issue-inventory` branch; contains only neutral project scope, issue data and packet |
| `worktree/09_TOOLS/agent_runner_v1/runs/issue/task_packet.md` | Builder-generated and scoped packet; draft in ordinary `prepare` |
| `handoff/` | Original AEOS brief, packet/context snapshots, manifest and worker-result template |
| `handoff/worker_result.json`, `handoff/artifacts/report.json` | Candidate return and hashed inventory evidence |
| `baseline.json` | Exact worktree file hashes, including `.git` pointer, plus original manifest fingerprint |
| `audit/NNNN.json` | Actual command vector, times, exit code and stdout/stderr; each file created exclusively |
| `verification/NNNN.json` | Successful mechanical observations, inventory, result/manifest fingerprints and pending H3/owner status |
| `RESULT.json` | Synthetic demo summary; successful demo only |

Any command rejection stops immediately, preserving its command event; a
60-second timeout also stops. Wrapper precondition failures are returned as
structured stderr with exit 2; preserve that output with the run if investigating
a refusal. Missing result means stop/reconcile, never redispatch. No automatic
repair loop exists; the packet retains the three-cycle cap, and there are zero
repair cycles in the demonstration. A fresh `verify` is read-only for task
sources and appends new observation/audit files; it does not rerun the worker.

The adapter also refuses output collisions, draft packets, changed tools,
missing/stale context, manifest drift, snapshot/artifact tampering, failed checks,
fabricated worker H3 fields, out-of-scope declared writes and unexpected worktree
files/changes. Existing AEOS structural validation is followed by a narrow,
source-derived inventory check, since valid JSON and hashes alone do not prove a
correct outcome. No new success observation is written when verification fails.
An older `RESULT.json` records a past demo, not current freshness; inspect the
latest command outcome and run a fresh verification before continuing.

These are point-in-time checks. Git worktrees isolate working files and branches,
**not processes, filesystem permissions or network access**. A same-user process
can rewrite controller records. Hashes are not signatures, append-only audit
files are not tamper-proof storage, and recorded approval is not authenticated
identity. Enforce real worker access and reviewer separation outside this script.
No reviewer or approval service is implemented.

## Manual Gate A and T3 Code handoff

To exercise the real draft boundary, use the same synthetic export with `prepare`
and a different absent output name:

```powershell
$Run = Join-Path (Split-Path $Repo -Parent) 'aeos-issue-manual-new'
& $Python -B $Poc prepare --issue-json (Join-Path $Repo 'prototypes/issue_handoff/synthetic_issue.json') --output $Run
if ($LASTEXITCODE -ne 0) { throw 'Intake stopped' }
```

For a future **separately authorized** issue, a human can save the exact supported
GitHub export shape. This read-only command is documented, not tested here:

```powershell
gh issue view 123 --repo OWNER/REPO --json number,title,body,url,labels --jq '.'
```

Save its UTF-8 JSON output locally (PowerShell 5.1 example below); review it for
data authorization before passing it to `prepare`. The URL is provenance, not
proof that the file came from GitHub. The prototype doesn't re-fetch the issue,
comments or labels or resolve concurrent changes. Live acquisition remains unrun.

```powershell
$IssueJson = gh issue view 123 --repo OWNER/REPO --json number,title,body,url,labels --jq '.'
if ($LASTEXITCODE -ne 0) { throw 'Issue export failed' }
[System.IO.File]::WriteAllText((Join-Path $Repo 'issue.local.json'), ($IssueJson -join "`n"), [System.Text.UTF8Encoding]::new($false))
```

Keep live exports and all run directories outside commits. Use a sibling path
instead of the repository-root example above when saving actual business data.
The prototype supports only a read-only inventory, even for a live export; it
cannot turn an issue into arbitrary executable instructions.

1. **Human Gate A:** inspect the entire draft, fixed read-only scope, selected
   context, live locks and worktree. Only the actual authorizing human changes
   `status: draft` to `status: approved` and records who, when and the exact local
   inventory scope in section 12. Leave H3 null and lifecycle pending. Do not
   turn a synthetic fixture status into a real approval record.
2. Run `bundle` below. It invokes AEOS build/check and records the baseline. Run
   the explicit original `check` immediately before carrying the files to T3.
3. **Manual worker handoff:** provide `execution_brief.md`, the complete packet,
   selected snapshots and result template to an approved T3 Code/agent session.
   Human is the AEOS transport label, not a claim that a provider was launched.
   Give only approved files; separately restrict the worker's actual tools.
4. Worker returns `worker_result.json` plus `artifacts/report.json`. Copy the
   template to a new result, preserving schema/run/task/worker fields. The report
   must contain exactly `issue_number`, `label_count`, `source_sha256` (the issue
   snapshot hash from the manifest). Declare its hash as an artifact and cite it
   in a passed check. `changed_paths` and `proposed_writeback` remain empty.
   Worker must not supply H3/owner fields. Do not overwrite any previous result.
5. Run `verify`. Passing means candidate evidence is current and consistent,
   **not independent H3 or permission to integrate**.

```powershell
& $Python -B $Poc bundle --run $Run
if ($LASTEXITCODE -ne 0) { throw 'Bundle stopped' }
$Hand = Join-Path $Repo 'distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py'
& $Python -B $Hand check --bundle (Join-Path $Run 'handoff') --vault-root (Join-Path $Run 'worktree')
if ($LASTEXITCODE -ne 0) { throw 'Fresh context check stopped' }
# Manual T3/agent handoff and return occur here, outside this script.
& $Python -B $Poc verify --run $Run
if ($LASTEXITCODE -ne 0) { throw 'Return verification stopped' }
```

Gate A/assignment/locks are procedural checks, not authenticated by the CLI.
Before integration, an **independent read-only H3 reviewer** inspects the packet,
baseline, exact candidate diff/result, context freshness, actual command evidence,
inventory calculation, refusals and remaining risks. Record reviewer identity,
scope, candidate fingerprint, findings, verdict and unrun checks separately. The
worker cannot fill that role. Human Gate C accepts/rejects that exact candidate;
any publishing, sending, spending, account change, deletion or deployment still
needs its own actual human authorization. There is no integration command here.

## Reviewable draft pull request

The implementation goes on a normal branch in the **public source repository**;
the issue worktree inside a demo run is disposable task isolation, not the PR
branch. Retain only authored fixtures and public-safe evidence in the PR. Do not
commit run directories, private exports, absolute local command logs or vault
contents. Include:

- adapter, synthetic fixture, boundary tests and Windows/Linux CI workflow;
- the compact [verification receipt](evidence.json), with actual environments,
  source/tool hashes, synthetic result and test output;
- independent H3 status and owner gate status, explicitly pending unless done;
- known limitations and the smallest next step: one manually reviewed T3 return
  against the same read-only synthetic task before attempting coding automation.

Exact checks from a normal checkout, with the required Python for each command:

```powershell
python -B -m unittest discover -s prototypes/issue_handoff -p 'test_*.py' -v
python -B -m unittest discover -s tests -p 'test_*.py'
python -B -m unittest discover -s scripts -p 'test_check_public_boundary.py'
git add prototypes/issue_handoff .github/workflows/issue-handoff.yml
python -B scripts/check_public_boundary.py
python -B scripts/check_public_boundary.py --history
git diff --cached --check
# Separately, on Windows with CPython 3.14.5 (the existing repository validator):
python -B scripts/validate_candidate.py
```

Stop on any failure. The existing validator is Windows/3.14.5-specific; a Linux
refusal is not a passed package check. It tests an older unpublished candidate;
the new workflow separately runs this prototype's synthetic tests on Windows and
Ubuntu with Python 3.11 and 3.14.5. Planned CI is not evidence until its run passes.
The full-history scan needs a normal full-history checkout. A reconstructed
snapshot cannot establish upstream history safety.

After public-boundary review and the applicable human authorization for uploading
the exact candidate, the operator can create a draft (never merge automatically):

```powershell
git switch -c prototype/issue-handoff
git commit -m 'Add bounded issue intake around existing AEOS handoff contracts'
git push -u origin prototype/issue-handoff
gh pr create --repo OWNER/REPO --base main --head prototype/issue-handoff --draft --title 'Add bounded issue-to-AEOS handoff prototype' --body-file PR_BODY.md
```

Create `PR_BODY.md` from the concrete changes and receipt, explicitly recording
H3 as pending. Use an existing feature branch instead of `git switch -c` when
already on one. No command above authorizes merging, releasing or deploying.
