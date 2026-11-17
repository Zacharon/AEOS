# Local evidence-freshness experiment report

## Result and limits

Implemented and ran the standalone conservative baseline. All **12/12 authored
fixture expectations**, **12/12 focused regression tests** and **8/8 existing
repository regression tests** passed, with zero skips or failures. This is worker
verification of a bounded synthetic demonstrator, not feature certification,
independent H3, product correctness, owner acceptance or productivity evidence.

The baseline rejects stale requirement/source/environment bindings, detects absent
or altered raw evidence, keeps context reads separate from declared dependencies,
and prevents historical success from overriding a current synthetic denial. It
does not infer complete dependencies, authenticate execution or enforce real
permissions. The consistent-forgery test deliberately gets an eligible result
after both example output and its digest are changed: that establishes the
documented authenticity limit, not a claim that the forged statement is true.

## Provenance and scope

The verified host checkout is the public setup source preview, branch `main`,
HEAD `5a5f8a80519036372fb6d639ef136d198b569bfb`. Identity was established from
Git root/branch/HEAD/worktree inspection and its own README, architecture and
public-boundary instructions. Remote publication visibility was not audited.
The pre-existing untracked `CLAUDE.md` was preserved byte for byte. No tracked
file or Git metadata was changed.

Owner-designated source-of-truth controls and current handoff rules were consulted
read-only. They are separate from this public project. Private provenance details
remain in the session response; no private control text, source snapshots or
research attachments were copied here. The eight named read-first materials were
available; long routing/index output was inspected through relevant excerpts
after console truncation, not treated as a whole-vault audit. The current handoff
documentation already separates byte integrity, source freshness and approval.

`README.md` and `docs/ARCHITECTURE.md` exist in the host checkout and were read.
The proposed `docs/ADOPTING-AEOS.md` and `prototypes/issue_handoff/README.md` do not
exist there. Existing task-packet and handoff code was located through current
architecture links under the packaged public.4 vault. No adapter was changed.
The research's source counts and external claims were not independently audited;
the implementation follows the supplied experiment specification.

The requested isolated-checkout path was replaced by the explicitly permitted
standalone scratch alternative `scratch/evidence_freshness/`. This stays inside
the session's writable root and leaves branch/PR integration unresolved. It is
not an isolated Git worktree. No production workflow, package, archive, website,
vault source, remote setting or unrelated file was edited. No model API, package
installation, infrastructure, push, merge, publication or messaging was used.

## Files

- `checker.py`: read-only applicability and containment checks; text/JSON CLI.
- `run_fixtures.py`: evaluates fixture inputs and separately authored expectations.
- `fixtures/current.json`, `receipt.json`, `cases.json`, `expected.json`: common
  records, 12 case overrides and authored expectations/rationales.
- `fixtures/inputs/` and `fixtures/raw/`: six synthetic inputs and two explicitly
  authored example outputs.
- `test_freshness.py`: focused transition, containment and trust-boundary tests.
- `verify.py`: repeatable bounded checks with new-only evidence directories.
- `pilot_log.csv`: blank header-only pilot template; no participant observations.
- `README.md`, this report and `results/`: instructions and public-safe local evidence.

## Actual verification

Executed on **Windows**, reported release **10**, **CPython 3.14.5**. No inference
about another OS or Windows edition is made. The shell's generic `python` alias
was unusable, so commands were invoked with the existing interpreter's absolute
path. No interpreter or dependency was installed. Public records use
`<interpreter>` instead of embedding a personal installation path.

From the experiment directory:

```powershell
<interpreter> -B verify.py --output results/run-001
```

The wrapper ran and retained these commands and outputs:

| Command | Working directory | Exit | Observed result |
|---|---|---:|---|
| `<interpreter> -B run_fixtures.py --format json` | experiment | 0 | 12 expected outcomes/reasons matched |
| `<interpreter> -B -m unittest -v test_freshness` | experiment | 0 | 12 tests, no skips |
| `<interpreter> -B -m unittest discover -s tests -p "test_*.py"` | host repository | 0 | 8 tests, no skips |

See [machine-readable execution summary](results/run-001/summary.json),
[fixture decisions](results/run-001/fixtures.stdout.txt),
[focused test output](results/run-001/focused-tests.stderr.txt), and
[repository test output](results/run-001/repository-regressions.stderr.txt).
The README's runtime-support wording was subsequently narrowed to the tested
version; tested Python/fixture bytes remain unchanged. The final boundary receipt
records the final artifact manifest separately from execution-time hashes.

The required negative scenarios all produced their intended denials. Native
Windows junction redirection, including a linked fixture root, was exercised and
rejected. Lexical traversal, absolute/UNC references, stream syntax, reserved
aliases and malformed records were rejected. Repeated assessment produced identical
decisions/reasons and left input records/files unchanged. Both CLI formats use
the same handler; an eligible record returns exit 0, a refused record exit 1.

No failing implementation attempts were discarded. There were no meaningful
test failures during this run. The initial interpreter-alias problem was an
environment lookup issue, resolved by the available explicit interpreter.

The repository's full `scripts/validate_candidate.py` installation journey was
**NOT RUN**: it creates a virtual environment and installs unrelated dependencies.
The task permits a standard-library experiment and asks for checks of concrete
experiment risks only. Existing package regressions were run; this is not a new
full package or release-validation claim. Other operating systems and interpreter
versions, CI, hosted/native application integration and independent H3 are **NOT RUN**.

## Fixture decisions

1. Unchanged evidence: **eligible**; owner acceptance remains pending.
2. Changed requirement: **stale**.
3. Withdrawn requirement: **stale**, with current action authority unchanged.
4. Modified declared dependency: **stale**.
5. Earlier source revision: **stale**, even with identical dependency bytes.
6. Missing raw evidence: **insufficient**.
7. Raw evidence digest mismatch: **invalid**.
8. Context-only reference change: **eligible**, under explicit synthetic independence.
9. True dependency counterpart: **stale**.
10. Relevant environment change: **stale**.
11. Declared unrun check: **insufficient**.
12. Revoked action authority: **blocked**, while evidence applicability stays eligible.

These are deterministic classification results. Authored fixtures and tests are
not independent evidence that the underlying requirements are the right ones.

## Feature-standard disposition

This remains a candidate experiment, not an accepted installed capability.

- Shared capabilities: **PASS locally**. Text and JSON CLI paths invoke the same
  assessor; parity and refusal exits were exercised.
- Shared state: **PASS for read-only snapshots**. Fresh CLI processes read the
  same files and produce the same decision. No mutable product state is offered.
- Scoped authority: **PARTIAL**. Current synthetic denial is respected, but there
  is no authenticated principal, ownership, grant or expiry resolver. Do not use
  this as a real action authorization service.
- Human usability: **PASS for local CLI smoke checks**. Help, readable decisions
  and error outcomes are available with AI disabled. Owner usability acceptance
  and review-time measurements are **NOT RUN**.
- Visible supervision, safe recovery and atomic action receipts: **NOT APPLICABLE**
  to the read-only assessor, which performs no user-data write or external action.
  The test harness writes local evidence only; it is not a product mutation API.

No automatic approval rejection occurred and no authorized local implementation
step remains blocked. Real integration, authenticated authority, owner acceptance
and any human pilot remain outside this completed synthetic stage.

## Baseline and next decision

Only the competent conservative baseline was implemented: explicit current intent,
source/specification/dependency/environment bindings, conservative task rechecks,
honest missing evidence and separate current authority. No orchestration,
selective reuse, candidate arm or comparative productivity experiment was added.

All pilot measurements remain blank. Fixture runtime is not active reviewer time.
There is no measured time saving, cost saving, reliability rate or market result.
The smallest next step is owner review of these results, followed, if approved,
by matched review packets using identical facts in both conditions and hidden
expected labels. The pilot protocol and stop rules are in the README. Repository
integration and owner acceptance remain outstanding.
