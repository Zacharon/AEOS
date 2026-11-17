# Evidence freshness: standalone synthetic baseline

This is a deterministic, standard-library experiment. It is not integrated into
the setup package or any operating vault. It implements the competent conservative
baseline first: explicit current requirements, exact source binding, declared
check inputs, raw evidence integrity, and current action authority. No candidate
or human productivity comparison has run.

The output location is the authorized scratch equivalent `scratch/evidence_freshness/`,
instead of `experiments/evidence_freshness/` in an isolated Git checkout. It is a
new standalone directory inside the permitted write root; it is **not a worktree**.
Git metadata, production code, distributions, site files and other work are not
part of this change. Integration requires a later scoped task on a branch.

## Use without AI

Use the existing CPython 3.14.5 interpreter used for this run; other versions are
unverified. No dependencies need installing. From this directory:

```powershell
python -B run_fixtures.py
python -B checker.py --root fixtures --current current.json --receipt receipt.json --format text
python -B checker.py --root fixtures --current current.json --receipt receipt.json --format json
python -B -m unittest -v test_freshness
python -B verify.py --output results/run-002
```

Use a new results directory for each verification attempt. Existing evidence is
never overwritten by `verify.py`. The final command also runs the repository's
existing standard-library regression suite, locating the repository two levels
above this scratch directory. The checker and fixture commands are read-only;
`verify.py` writes transcripts and temporary synthetic test data inside the
experiment. A nonzero checker exit means the receipt is not eligible, not that
the experiment failed. The fixture runner exits nonzero only on an expectation
mismatch. Inspect both `evidence_outcome` and `action_outcome`.

## Capability and record contract

`evidence-freshness/v1` is a local read-only capability. Human controls are the
CLI's text output and `--help`; the agent adapter is the same CLI with JSON
output, or the `assess(current, receipt, root)` function. All use the same handler
and validation. It executes no command from a receipt and performs no action
described by `action`. Both inputs must be JSON objects with the required fields
declared in `CURRENT` and `RECEIPT` in [checker.py](checker.py). Unknown fields,
malformed values, duplicate JSON keys and unsupported policy versions are refused.
Missing required fields are insufficient evidence.

- [Current requirements and state](fixtures/current.json) bind task, claim,
  active/withdrawn requirements, specification bytes, exact source revision,
  declared dependency paths, coverage, runtime/configuration, check and action.
- [Historical receipt](fixtures/receipt.json) records the corresponding revision
  and digests, check command, execution status/exit code, raw-output reference,
  unresolved assumptions, unrun checks, historical status, past authority and
  owner acceptance. These historical fields are never rewritten by assessment.
- [Case definitions](fixtures/cases.json) replace whole fields of those common
  records. Context-read logs live outside the receipt and are not check inputs.
- [Expected answers](fixtures/expected.json) were hand-authored from the requested
  behavior, not generated from checker decisions. They are separate from case
  inputs and are read only by the evaluator. This is not independent H3 review.

The only policy supported is `exact-source-v1`. Any source revision change makes
the old receipt stale, even if dependency bytes match. Changed requirement IDs,
intent revision, specification bytes, declared inputs, check identity/command,
environment, or superseded receipt status also prevent reuse. Missing or unknown
dependency coverage, unresolved assumptions and unrun checks are insufficient.
There is no selective rerun optimizer: rerun the affected task's prescribed
checks after resolving applicability, under current authorization.

Outcomes are `eligible`, `stale`, `insufficient`, `invalid`, and `blocked`.
All detected evidence reasons are retained; evidence precedence is invalid,
then stale, then insufficient, then eligible. A current authority denial yields
overall `blocked` while preserving the separate evidence classification. Unknown
authority prevents eligibility. A withdrawn requirement is stale intent, not
revoked action authority. Owner acceptance is never inferred or changed.

## Trust boundary

All supplied fixtures, requirements, permission states, source labels and example
execution records are synthetic. Files under `fixtures/raw/` are **authored
example outputs**, not transcripts of checks that ran. Actual checker/test
transcripts are under `results/`. Eligibility means only that these applicability
and integrity rules passed; it does not mean correct software, owner approval,
H3 acceptance, permission to execute, or permission to deploy.

Current-state facts must come from a trusted operator/controller in any future
integration. This prototype does not authenticate a principal, owner decision,
execution, source label, requirement revision, environment, timestamp or dependency
inventory. A malicious producer can fabricate output and its digest together,
omit a real dependency while declaring coverage complete, or forge the supplied
current state. The consistent-forgery regression deliberately demonstrates this
limit. Hashes prove byte identity, not truth. `allowed_by_synthetic_input` is
not authenticated authorization. No real authority enforcement is claimed.

Paths must be relative to the selected synthetic root. Traversal, absolute paths,
Windows streams/reserved aliases, and filesystem symlinks/junctions (including
linked roots) are rejected. This is not a sandbox against an adversary changing
the filesystem between validation and reading. The synthetic directory must be
under exclusive local control during a check. Whole-tree concurrent atomicity
and adversarial resource-exhaustion resistance are outside this small experiment.

Case 08 explicitly places a context-only reference outside the source snapshot
and dependency set. Case 09 makes the same reference type a declared dependency.
The fixtures supply this distinction; the checker does not discover semantic
dependencies. A stricter real project rule still wins.

## Later pilot, not executed

[pilot_log.csv](pilot_log.csv) is header-only. Blank means unmeasured, never zero.
Record setup and maintenance separately from per-case work. An attempt is a full
processing/review from the declared starting snapshot; a retry is a new attempt
after failure or intervention. Keep all attempts and failures, and do not count
retries as independent tasks. Record observed subscription usage only; do not
invent dollar costs or infer costs from plan limits.

After owner review, the smallest next step is 6–12 matched review packets comparing
the competent baseline with the same facts plus a freshness result. Both receive
current requirements, identical source/specification/evidence and resource budgets,
conservative rerun rules, and ordinary independent behavioral review. Preserve
allocation and order; do not show the same exact case twice to one reviewer. Hide
`expected.json` until review ends. Record familiarity bias if the author reviews.
This tests the combined receipt/decision aid, not orchestration or presentation
alone. To isolate presentation, give both arms identical derived decisions too.

Require no false eligible decisions on declared critical negatives, unchanged
authority/revision rules, equal or better accuracy and measured total effort.
The suggested 20% lower median active reviewer time is an owner decision to adopt
or change, not a scientific constant. Include setup, maintenance, retries and
rework. Stop, simplify or reject the candidate if the baseline does equally well,
accuracy drops, or total effort increases. Do not add agents or a router to rescue
the hypothesis. No pilot is automatically started by these commands.

See [REPORT.md](REPORT.md) for observed verification, provenance limits and gates.
