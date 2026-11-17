# Complete isolated recovery cycle

**Observed failure, corrected behavior, stale historical evidence and eligible
replacement evidence are all recorded. Synthetic development stops here.**
The existing checker and all earlier experiment files are preserved.

| Requirement | Implementation behavior | Check result | Receipt status |
|---|---|---|---|
| Count all items | Original counts 3 | Earlier rehearsal passed, exit 0 | Earlier eligible result retained as history |
| Count active items | Original still counts 3 | Newly observed failure: expected 2, actual 3, exit 1 | Original receipt cannot support revised intent |
| Count active items | Corrected copy returns 2, 0 and 0 on the three cases | All three passed, suite exit 0 | Original receipt stale; replacement eligible |

## 1. Predicted failure became an observation

Before changing the implementation, the capture script invoked the actual
original check from the preserved `rehearsal-001` directory:

```text
<interpreter> -I -B check_count.py --expected 2
```

[Actual stdout](initial-failure.stdout.txt):

```text
Command: <interpreter> -I -B count_items.py inputs/items.json
Source stdout: {"count": 3}
Source exit: 0
FAIL expected=2 actual=3
```

The check exited **1**, with empty stderr. There was no discrepancy to investigate.
[initial-failure.json](initial-failure.json) records command, original working
directory, timestamp, duration, actual exit, source/input/requirement hashes and
environment. The capture helper exited 0 because it observed the expected failure;
that helper status is not the behavior-check status.

## 2. Separate corrected copy

Only the new `replay/` copy changed. Its counter now sums items whose `active`
field is explicitly `true`. The copied check gained an input-path argument so
the same check can run against three small files. No testing framework was added.
`check_recovery.py` simply runs those three commands and fails the suite if any
child check fails.

From `replay/`, the captured suite command was:

```text
<interpreter> -I -B check_recovery.py
```

The actual child commands and results were:

```text
<interpreter> -I -B check_count.py --input inputs/items.json --expected 2
PASS expected=2 actual=2
Check exit: 0

<interpreter> -I -B check_count.py --input inputs/none-active.json --expected 0
PASS expected=0 actual=0
Check exit: 0

<interpreter> -I -B check_count.py --input inputs/empty.json --expected 0
PASS expected=0 actual=0
Check exit: 0

Cases passed: 3/3
```

The [complete suite stdout](replay/suite.stdout.txt) retains child commands,
executable stdout and exit codes. [suite.execution.json](replay/suite.execution.json)
records the suite's exit **0**, empty stderr, raw-output digests and timing.
Source and inputs were unchanged during execution. Malformed records and nonboolean
`active` values are outside the requested examples; broader correctness is untested.

## 3. Historical and replacement evidence

The original receipt was copied byte for byte to
[historical-receipt.json](replay/historical-receipt.json). Its original referenced
`check.stdout.txt` was also copied byte for byte into the new assessment root;
the original stderr and current requirement were retained too. No receipt path or
historical digest was edited to accommodate relocation.

The [replacement receipt](replay/replacement-receipt.json) covers **all three
cases** executed by `CHECK-active-count-suite`, not only the mixed input. It binds
the actual corrected source snapshot, six declared source/input dependencies,
current specification, environment, suite command, exit code and new raw output.
[source-manifest.json](source-manifest.json) records the hashes. Snapshot identity
uses SHA-256 over sorted compact JSON of the three Python source-file hashes,
the same convention as the earlier rehearsal; it is not a Git commit.

Both receipts were assessed against the same [current state](replay/current.json),
using the unchanged checker and `exact-source-v1` policy. From `replay/`:

```text
<interpreter> -I -B ../../../checker.py --root . --current current.json --format text --receipt historical-receipt.json
<interpreter> -I -B ../../../checker.py --root . --current current.json --format text --receipt replacement-receipt.json
```

The [historical assessment](replay/historical-assessment.stdout.txt) exited **1**:

```text
Outcome: stale
- requirement_revision_changed
- source_revision_changed
- environment_changed
- check_id_changed
- command_changed
- dependency_set_incomplete
- dependency_changed:check_count.py
- dependency_changed:count_items.py
- specification_bytes_changed
Synthetic applicability only; no acceptance or execution permission is granted.
```

The environment reason reflects the changed check configuration (three cases
instead of expected=3), not an OS/interpreter change. The old receipt also lacks
coverage for the additional suite dependencies. No missing-file or evidence-integrity
error caused this decision: its original output is present and its digest matches.

The [replacement assessment](replay/replacement-assessment.stdout.txt) exited **0**:

```text
Outcome: eligible
- applicability_rules_satisfied_only
Synthetic applicability only; no acceptance or execution permission is granted.
```

## Observations, declarations and preservation

Observed: real commands, stdout/stderr, exits, file digests, checker decisions,
and runtime identifiers. The runtime was **Windows 10.0.19045, CPython 3.14.5**;
the interpreter binary digest and flags are recorded in [environment.json](environment.json).
Public commands use `<interpreter>` in place of the personal installation path.

Supplied declarations: desired behavior and expected counts; stable task/claim
identifiers; intent revision; the suite as the required check; dependency membership
and scoped completeness; current local-review authority; pending owner acceptance.
The six declared inputs are the three source scripts and three input JSON files.
Specification is separately bound, runtime is represented by observed identifiers,
and exhaustive OS/standard-library dependency coverage is not asserted. As before,
these declarations are not authenticated by the checker.

The recovery helpers are fixed local evidence-capture scripts. They do not execute
commands read from a receipt, alter checker rules, create a worker/runtime or
integrate the experiment anywhere. The original source, receipts, outputs and
fixtures remain untouched. The final scope receipt compares **308 pre-existing
tracked or visible untracked files**, verifies historical copies, and confines
all additions to this new recovery directory. The checker retains SHA-256
`e95287196005e5eebf52c3a653538a8fefa73bd361e3dbea466d1d7f3de531e8`.

Preparation and reviewer minutes remain unmeasured, not zero; see [result.json](result.json).
No human pilot, independent H3, owner acceptance, real-handoff execution or
productivity comparison occurred. Broad package tests were not rerun because
package/checker code did not change. This is real execution on synthetic inputs,
with bounded behavioral support and applicability evidence, not general correctness.

## One real-handoff candidate; not started

**Candidate: a maintainer-to-reviewer handoff asking which acceptance claims for
the consolidated AEOS issue-handoff implementation are currently supported.**
This reviews real engineering work already present in the repository. It does
not launch another synthetic worker or execute an ordinary issue through a
prototype that explicitly permits only fixed synthetic execution.

Read-only provenance reconciliation found:

- The experiment host remains `main` at
  `5a5f8a80519036372fb6d639ef136d198b569bfb`.
- A registered, clean worktree on `acceptance/real-worker-20261101` is at
  `88e8aea5ddea99aebcc1212bf5bd5aaac68e8931`. The experiment host is its ancestor,
  15 commits behind. No branch, checkout or remote was changed.
- That newer local source contains `prototypes/issue_handoff/README.md`,
  `docs/ADOPTING-AEOS.md`, `docs/ISSUE_HANDOFF_REVIEW.md`, and the implementation.
  Their earlier absence was specific to the old checkout.
- Its tracked `prototypes/issue_handoff/local-verification.json` describes
  October 31 Linux/CPython 3.12.14 implementer verification. All four listed
  source hashes currently match their files. This supports file identity only.
- That receipt lists target Windows execution, manual provider return,
  independent H3 and owner integration acceptance as unverified. The accompanying
  review still discusses pre-merge disposition, while local Git history includes
  the consolidation merge. Therefore its remaining-work text is historical
  evidence, not proof those items are still open today.

The latest remote revision, later acceptance records and the current controlling
task/owner decision were **not verified**. The newer local worktree is a candidate
source, not an automatically authorized integration target.

Before the real walkthrough, reconcile those current controls and pin the exact
chosen source revision plus any worktree changes. Gather the ordinary requirement
and claim, retained command outputs, environment, worker return/patch and
independent/owner decisions where they exist. Preserve missing evidence as NOT RUN
or unknown. A recorded `upstream_commit` is a base revision, not automatically the
exact tested head. Matching four file hashes does not prove complete dependencies
or native Windows/provider execution.

Preparation burden is mainly locating current acceptance records, mapping one
narrow claim to its required checks, inspecting dependency coverage, and preparing
bounded evidence copies without exposing private runtime paths. Then fill the
existing receipt, read its text output and record preparation/review minutes,
missing information and whether it changes the decision. Keep dependency coverage
unknown if it cannot be justified. Do not invent an effort estimate; none was
collected here. This first real review should answer whether the added record
helps distinguish supported claims from outstanding checks, or merely duplicates
the existing handoff verifier.

No receipt for that real case was assembled, no provider/worker was dispatched,
and no handoff command was run. Synthetic development ends with this recovery.
