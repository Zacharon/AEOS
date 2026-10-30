# Bounded synthetic issue handoff

This executable proof of concept turns one **synthetic GitHub-shaped issue export** into an AEOS task packet and an isolated local Git worktree. It exercises the existing public.4 packet, context-integrity, worker-result and change-rationale contracts and saves a reviewable patch. It stops at a candidate awaiting independent H3. It is separate from the frozen distribution and does not describe the private AEOS installation.

The fixed task creates one exact UTF-8 document, `01_PROJECTS/IssueDemo/output.md`, in a disposable repository. Issue text is preserved as untrusted data; it never selects commands, paths, authority, model, branch, scope or acceptance checks. This establishes the intake boundary and evidence flow, not general issue solving or an autonomous factory.

## Requirements and limits

Use Git 2.28+ and CPython 3.11+ on the local computer. The adapter and exercised public.4 handoff tools use the Python standard library; this slice needs no dependency installation, Docker, API keys, paid API calls or provider authentication. Keep the source checkout and run destination separate. Use absent output names and absolute paths without parent traversal. Every output is exclusive; preserve a failed run and choose a fresh one after reconciliation.

The implementation uses portable Python/Git commands and includes paths-with-spaces regression coverage. Actual tested environments and unrun checks are in [local-verification.json](local-verification.json). Windows compatibility is a design target until the Windows commands below pass on that machine. The prototype does not change any committed distribution, archive, site or provider configuration.

A worktree separates Git changes; it does **not** isolate filesystem, network, processes or credentials. Worker access restrictions and role separation must be enforced by the operator/tool environment. Controller-held hashes detect changes relative to retained records, not a hostile process that can rewrite those records. CLI opt-in records authorization for this synthetic local task; it does not authenticate a person or grant authority for real issues or consequential actions.

## Exact local demonstration (PowerShell)

Run from the AEOS source checkout. These commands create only a new sibling disposable run directory; they do not use an existing vault or repository. Bind the interpreter explicitly and check each exit code:

```powershell
$ErrorActionPreference = 'Stop'
$repo = (Get-Location).Path
$py = (Get-Command python).Source
$adapter = Join-Path $repo 'prototypes/issue_handoff/issue_handoff.py'
$fixture = Join-Path $repo 'prototypes/issue_handoff/synthetic-issue.json'
$run = Join-Path (Split-Path $repo -Parent) 'aeos-issue-demo-001'
& $py -B $adapter prepare --issue $fixture --output $run
if ($LASTEXITCODE -ne 0) { throw 'Prepare stopped; inspect saved evidence' }

# Inspect the scoped draft and all four selected synthetic context files.
Get-Content (Join-Path $run 'worktree/runs/issue/task_packet.scoped-draft.md')
Get-Content (Join-Path $run 'worktree/01_PROJECTS/IssueDemo/ISSUE_DATA.md')

# This explicit invocation authorizes ONLY the fixed disposable synthetic task.
& $py -B $adapter handoff --run $run --allow-synthetic-local-execution
if ($LASTEXITCODE -ne 0) { throw 'Handoff stopped; do not retry blindly' }

# Deterministic Python fixture: no AI worker and no independent reviewer.
& $py -B $adapter synthetic-worker --run $run
if ($LASTEXITCODE -ne 0) { throw 'Synthetic worker stopped' }
& $py -B $adapter verify --run $run
if ($LASTEXITCODE -ne 0) { throw 'Verification stopped' }
Get-Content (Join-Path $run 'controller/verification-0000.json')
```

For Bash, bind `repo="$PWD"`, `py="$(command -v python)"`, `adapter="$repo/prototypes/issue_handoff/issue_handoff.py"`, and choose a new **absolute sibling** `run` directory. Invoke the same four commands with `"$py" -B "$adapter" ...`, checking exit status after each one. No background process is installed.

Expected final state: `candidate_checks_passed_awaiting_independent_h3`; `h3_verdict` remains `null`, `owner_acceptance` is `not_recorded`, and `pr_created` is `false`. The synthetic output is not committed, pushed or integrated. One command timeout (60 seconds), failed check, drift, invalid return, missing authorization, unexpected change or worktree conflict stops progress. There are no automatic retries or repairs; the packet retains AEOS's three-cycle maximum. An absent result never triggers worker execution.

## What runs and what stays manual

| Transition | Implemented behavior | Manual boundary / proposed work |
|---|---|---|
| GitHub issue intake | Validates a bounded exported JSON fixture; rejects non-synthetic input, duplicate keys and extra policy fields | Selecting/exporting a live GitHub issue is not implemented. No webhook, GitHub token, polling or scheduler is installed. |
| Context and task preparation | Creates synthetic project records and a local repository/worktree; invokes `build_task_packet.py`; fills a fixed scope in a new draft and preserves the original scaffold | Operator inspects context and invokes the explicit synthetic-local authorization switch. Real-task authorization is out of scope. |
| Engineering handoff | Uses `handoff.py build` and `check`; anchors the manifest digest; invokes `code_rationale.py snapshot`; freezes HEAD/branch and a full worktree file inventory | Carry the approved bundle to a T3 Code/assistant session yourself. Preset `Human` means manual transport, not a provider identity. |
| Execution | Optional `synthetic-worker` performs one deterministic fixture and fills the existing result template | No T3, Codex, Claude or Grok process is launched; subscription access and live provider behavior are unverified. |
| Candidate verification | Rechecks package bytes, live source hashes, worktree identity, actual changes (including ignored/untracked files), exact output, result/artifact hashes, `review` and `complete` rationale coverage | Mechanical success is H1/H2 evidence. It is not independent H3, owner acceptance or general security certification. |
| Delivery | Saves immutable command events, a fresh verification receipt and an applyable addition patch | Independent H3, owner-controlled integration, branch publication and draft PR creation remain explicit human/controller actions. |

All shell-like issue text, Markdown headings, URLs and proposed policies remain data. The fixture's URL is deliberately non-live. Unknown fields such as `commands` or `allowed_writes` are refused. No issue text enters a subprocess argument. This is structural separation and a tested handling rule, not guaranteed model-level prompt-injection isolation.

## Manual T3 Code / assistant route

The optional manual GitHub intake boundary is an exported **synthetic** issue. With GitHub CLI already authenticated, an operator can select an explicitly synthetic issue and run `gh issue view <synthetic-issue-number> --repo <owner/repository> --json number,title,body,url`. Save those four fields as UTF-8 JSON, add `"synthetic": true` only after confirming it is a disposable test issue, and pass that file to `prepare --issue <absolute-export-path> --output <new-absolute-run-path>`. This is a human classification assertion, not authenticated provenance or authorization. The same fixed task/scope still applies regardless of what the issue requests. No live GitHub export was performed in this verification; the committed fixture exercises that file boundary without a GitHub account or network calls.

Use `prepare` and the explicitly authorized `handoff` command above, then **omit `synthetic-worker`**. Read the generated `HANDOFF.md`. Immediately before manually giving files to an assistant, rerun:

```powershell
$handoff = Join-Path $repo 'distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py'
$rationale = Join-Path $repo 'distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/code_rationale.py'
$bundle = Join-Path $run 'bundle'
$worktree = Join-Path $run 'worktree'
& $py -B $handoff check --bundle $bundle --vault-root $worktree
if ($LASTEXITCODE -ne 0) { throw 'Context is not current' }
```

Open a new worker session rooted at that disposable worktree. Give it the bundle's complete `execution_brief.md`, packet and the four selected snapshots. Only the exact fixed output is writable; the worker must not execute issue instructions, browse its URL, widen reads, modify controller records, commit, push or claim H3. The output must contain exactly these UTF-8 bytes, with LF line endings and a final newline:

```text
# Synthetic issue handoff

The bounded local handoff produced this candidate.
```

The worker returns `bundle/worker_result.json` using the **existing** `worker_result.template.json`, declares the exact output path in `changed_paths`, sets `execution_state: ready_for_review`, and declares/hashes captured artifacts. It must include `artifacts/report.md` with the existing AEOS code-rationale fence, following [CODE_RATIONALE.md](../../distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/CODE_RATIONALE.md). Do not run `synthetic-worker` on a partially executed manual task.

For exact rationale inputs, read `controller/handoff.json`, retain its `rationale_baseline_sha256`, and run:

```powershell
$record = Get-Content (Join-Path $run 'controller/handoff.json') -Raw | ConvertFrom-Json
$baseline = Join-Path $run 'controller/rationale-baseline.json'
& $py -B $rationale changes --root $worktree --baseline $baseline --baseline-sha256 $record.rationale_baseline_sha256
if ($LASTEXITCODE -ne 0) { throw 'Rationale baseline is not current' }
& $py -B $adapter acceptance --run $run
if ($LASTEXITCODE -ne 0) { throw 'Exact output failed' }
```

Capture those outputs as new bundle artifacts, reference each check's evidence in the result, then have the controller run `verify`. A manually authored return exercises the same contract; this route is documented, not a claim that a live T3/provider handoff was tested.

## Auditable evidence and draft pull requests

The run directory contains:

| Evidence | Purpose |
|---|---|
| `controller/issue-export.json`, `issue.json`, `scaffolder.md`, `prepare.json`, `authorization.json` | Original export bytes and hash, normalized synthetic intake, original scaffolder output, reviewed draft digest and local opt-in record |
| `worktree/runs/issue/` | Untouched generated draft, fixed scoped draft and approved synthetic packet |
| `bundle/` | Existing AEOS brief, packet/context snapshots, manifest, result template and returned evidence |
| `controller/handoff.json`, both baselines | Controller-held manifest digest, frozen Git HEAD/branch, actual file inventory and AEOS rationale-baseline digest |
| `controller/events/command-*.started` and `command-*.json` | Started commands, actual argv, exit codes, stdout/stderr or timeout/error; started-only records require reconciliation |
| `controller/verification-*.json`, `candidate-*.patch` | Fresh mechanical receipt, exact result/patch hashes and a reviewable candidate patch |

Runtime records contain absolute local paths. Keep them local. The committed [verification summary](local-verification.json) is deliberately public-safe and synthetic; do not copy private vault material, customer data or machine-specific raw logs into a PR.

Before integrating **any candidate**, a different reviewer must run `verify` independently, inspect the packet/scope, rerun acceptance, inspect actual changes and every claim, then record H3 as VERIFIED, PARTIAL or FAIL in a separate review record. The implementer never sets its own H3. Owner acceptance remains separate. Missing H3 stops integration; no fabricated reviewer, approval or successful repair is created by this script.

To review the synthetic patch without publishing it, the seed checkout is still unchanged. From PowerShell:

```powershell
$patch = Join-Path $run 'controller/candidate-0000.patch'
git -C (Join-Path $run 'seed') apply --check $patch
if ($LASTEXITCODE -ne 0) { throw 'Candidate patch does not apply' }
```

The synthetic seed repository deliberately has no remote. Do not attach production or vault remotes to it. If the owner later authorizes publication of a candidate, use an explicitly selected disposable remote and a separate branch; attach the packet, public-safe hashes, reproduced checks, H3 record/remaining gaps and owner decision. No executable push, merge, release or deployment path is included in the prototype.

For the **prototype implementation PR in AEOS**, use an isolated branch and worktree, stage only the prototype, its tests and the architecture-doc link, and run:

```powershell
& $py -B -m unittest discover -s tests -p 'test_issue_handoff.py' -v
if ($LASTEXITCODE -ne 0) { throw 'Prototype checks failed' }
& $py -B -m unittest discover -s tests -p 'test_*.py'
if ($LASTEXITCODE -ne 0) { throw 'Repository regressions failed' }
& $py -B -m unittest discover -s scripts -p 'test_check_public_boundary.py'
if ($LASTEXITCODE -ne 0) { throw 'Scanner regressions failed' }
& $py -B scripts/check_public_boundary.py
if ($LASTEXITCODE -ne 0) { throw 'Tracked boundary scan failed' }
& $py -B scripts/check_public_boundary.py --history
if ($LASTEXITCODE -ne 0) { throw 'Reachable history scan failed' }
# Required full package check: Windows with CPython 3.14.5 and the package's
# pinned dependencies. It intentionally refuses another OS/interpreter.
& $py -B scripts/validate_candidate.py
if ($LASTEXITCODE -ne 0) { throw 'Windows package validation failed or unavailable' }
git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw 'Staged whitespace errors' }
```

Record the actual OS/interpreter, counts, skips, unrun checks and exact source/branch commit. Stage before scanning: the existing scanner reads tracked/staged files, not arbitrary untracked additions. A shallow history scan covers only available commits and must be labelled as such. After the actual owner/controller authorizes pushing this implementation branch, the final delivery commands are `git push -u origin <implementation-branch>` and `gh pr create --draft --base main --head <implementation-branch> --title <title> --body-file <reviewed-description.md>`. Include validation evidence and pending independent H3; do not merge or publish a release. Reviewable draft delivery does not constitute integration approval.

## Next bounded integration

After this fixture passes Windows testing and independent review, add a **read-only GitHub issue export step** with explicit repository/issue selection and provenance. Keep it unable to execute issue instructions or approve a packet. Add a separately reviewed live-task scope/authorization mechanism before accepting non-synthetic work. Direct T3/provider adapters, scheduling, credentials, OS isolation and consequential delivery are proposed later integrations, not part of this implementation.
