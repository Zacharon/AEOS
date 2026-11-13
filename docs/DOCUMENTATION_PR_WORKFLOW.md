# Documentation and PR workflow

Use this local recipe for a bounded change in the source checkout. It extends
the existing task packet and public.4 handoff/rationale validators; it does not
run a model, open a PR or update an operating vault. The packaged download and
the fixed synthetic issue demonstration remain separate routes.

## Authority and task inputs

Read the target's instructions, current requirements, contribution rules, issue
context and related changes. Operator-approved requirements govern intent;
current source and reproducible checks establish implemented behavior. Live
receipts establish deployed behavior. Report disagreements explicitly. Timestamps
and generated summaries cannot decide authority.

The controller supplies the repository/worktree and baseline, a v1.2 packet,
bounded reads and writes, acceptance criteria, both complete return contracts,
artifact names, required checks and an independent reviewer when applicable.
The [worker contract](../prototypes/issue_handoff/WORKER_CONTRACT.md) describes
the frozen schemas and [example packet](../prototypes/issue_handoff/documentation-task.md)
shows the local documentation pilot. The example's status records the local
exercise's scope; it does not grant a future user permission to execute it.

## Select and prepare

Put a single `context-selection` JSON fence in the existing task packet.
Each source names a relative path, logical scope, authority/purpose, lifecycle
status, replacement (or null), and exact required references. Only active
sources enter an ordinary bundle. Supersession requires a named active
replacement for the same scope. History remains accessible by named lookup.

`contracts` names the selected return and rationale documents. `dependencies`
names additional files whose changed bytes invalidate the run. `documentation`
maps changed paths to documents requiring review. `required_artifacts` and
`required_checks` name the worker's obligations. These fields are per-task
selection metadata, not another project registry. Keep stable inputs separate
from allowed outputs; an input change needs reconciliation before more work.

From the source checkout, with an approved packet and a new absolute run path
outside it:

```powershell
$root = (Get-Location).Path
$packet = 'prototypes/issue_handoff/documentation-task.md'
$workflow = 'prototypes/issue_handoff/documentation_workflow.py'
$run = Join-Path (Split-Path $root -Parent) 'aeos-doc-task-001'
python -B $workflow lint --root $root --packet $packet
if ($LASTEXITCODE -ne 0) { throw 'Resolve packet findings' }
python -B $workflow prepare --root $root --packet $packet --output $run
if ($LASTEXITCODE -ne 0) { throw 'Preparation stopped; preserve the attempt' }
python -B $workflow check --run $run
if ($LASTEXITCODE -ne 0) { throw 'Do not dispatch stale context' }
```

Read the bundle's entire execution brief, packet, selected snapshots and result
template. Use the controller-held baseline digest for the rationale report.
Give the worker only its authorized task and accessible contract files. For
native code work, use the host's bound worktree, and keep workers' write scopes
disjoint. The adapter does not create, bind or dispatch an agent session.

## Return, verify and draft

The worker implements the bounded change and updates affected documentation.
Its `artifacts/report.md` includes changed behavior, affected authorities,
evidence, unknowns and the existing `code-rationale` fence. Every changed path
has rationale or a specific `documentation-not-needed` explanation.
For a mapped no-documentation-change disposition, name each affected relative
path in that entry's `why` text so the explanation is tied to the reviewed scope.
Record checks as actually run, failed, blocked or not run; preserve negative attempts.

The controller independently reruns the prescribed checks, compares the actual
diff and artifacts, and then runs:

```powershell
python -B $workflow verify --run $run
if ($LASTEXITCODE -ne 0) { throw 'Return is incomplete or stale' }
python -B $workflow check --run $run
if ($LASTEXITCODE -ne 0) { throw 'Evidence is no longer current' }
```

Mechanical completion remains `needs-review`, with no H3 verdict. Ask a separate
reviewer to challenge the evidence and reproduce material checks. Apply the
target's H3 rules without turning worker success into independent review. Only
the controller updates authorized current-state files, after comparing claims
with evidence; retain historical reports and branch-specific limitations.

Prepare the PR title/body from the final diff: problem, resulting behavior,
checks actually run, failures and unrun checks, material limits, and appropriate
public evidence/issue links. Follow the target's title, issue-first and AI
disclosure rules. A local draft body is not an opened PR. Keep private evidence,
machine paths and owner data out of public text. Publication is a separate gate.

## Troubleshooting

- `Complete return and rationale contracts must be selected` or
  `Incomplete or unsupported worker contract`: stop before dispatch. Have the
  controller select the complete supported contract for both roles, then lint
  and prepare a new bundle; a link or headings alone cannot supply the schema.
- `Selected source or dependency changed; reconcile in a fresh run` or
  `Verification receipt is stale; reconcile in a fresh run`: inspect the drift,
  preserve the old run and evidence, and have the controller prepare a fresh
  authorized run and rerun affected checks. Never repair stored hashes or dates.
- `Task report needs exactly one code-rationale fence`: return one complete
  rationale object covering every actual changed path against the original
  controller baseline. For `Stale reference`, re-read the document and re-verify
  its claims before recording its current hash and heading; preserve prior evidence.
- `Missing or nonpassing required check`: capture the prescribed command's output
  and exit status. Missing, failed, blocked and `not_run` required checks prevent
  verification; stop and reconcile with the controller before retrying. Keep failed
  attempts, and leave optional unrun checks as `not_run` with null evidence.
  The adapter validates claims; the controller must independently rerun checks.

## Design and limits

The existing packet owns selection, the bundle owns hashed snapshots, and the
existing task report owns rationale and documentation delta. Adding a second
registry or editing frozen distribution bytes would create competing authority.
The adapter therefore composes the frozen validators and validates a bounded
selection fence in the packet. The full public worker contract is selected and
checked by bytes; a heading or README link cannot supply a missing schema.

Dependency mappings identify likely review needs, not semantic correctness or
complete dependency discovery. Hashes establish identity, not truthful prose,
authenticated approval or proof that a worker ran a command. Controller checks
and independent review supply those additional observations. Root-relative path
guards reject traversal and links but are not a hostile same-user sandbox.

Read-only checks do not create new verification claims. An unchanged successful
verification reuses its receipt. Changed inputs, outputs, contracts or evidence
invalidate that receipt. Inspect the difference, preserve the old run, prepare
a fresh authorized packet and rerun affected checks. Updating a stored date or
expected digest is not reconciliation or re-verification.

Root instructions stay in `AGENTS.md`; tool-specific files are thin pointers.
Confirm the installed host actually loads them before relying on an adapter.
Neither `.gitignore` nor an archive directory prevents an agent from reading
files. This workflow demonstrates exclusion from default selected context only.
