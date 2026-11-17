# Failure novelty experiment: v1 rejected for promotion

Date: 2026-11-02. Local deterministic synthetic replay on Windows, CPython 3.14.5.
Candidate experiment only; no operating vault, worker runtime, package, site,
external service or installed stopping policy changed.

## Result

The implementation works as specified, but the candidate does not meet the
experiment's promotion criterion. The held-out false-abandonment case is retained.

| Split | Cases | Baseline rounds | Candidate rounds | Unsolved rounds avoided | Added premature stops |
|---|---:|---:|---:|---:|---:|
| Development | 7 | 19 | 18 | 1 | 0 |
| Held out | 9 | 23 | 21 | 1 | 1 |

The held-out case `unreliable-no-progress-report` supplies identical failures and
unchanged, evidence-referenced progress at rounds one and two, with no reported
remaining action. The policy blocks at round two. The frozen counterfactual
trace passes at round three under the baseline. Evidence references are supplied
assertions, so the evaluator cannot tell that this no-progress report is wrong.
The omitted successful attempt is not counted as useful savings.

Time/cost-limit cases stop both policies before success. These inherited budget
stops are separate from the one additional abandonment introduced by v1.
A/B/A recurrence is classified at round three but saves no round within the cap.
The remaining cases exercise genuine progress under unchanged failures,
unknown progress, distinct justified retries, changing-error churn, and an
explicit authority blocker.

## Reproduction and evidence

Run these from `scratch/failure_novelty` with an existing Python interpreter:

```powershell
python -B -m unittest -v test_policy
python -B compare.py --output results/run-003
python -B policy.py results/run-003/sample-trace.json --format text
python -B policy.py results/run-003/sample-trace.json --format json
```

Use a new output directory. Prior runs are retained and must not be overwritten.
[Saved comparison](results/run-002/summary.json) contains code/fixture hashes,
per-case decisions and the rejection verdict. [Sample trace](results/run-002/sample-trace.json)
is a read-only CLI input showing a round-two stall with a resume condition.

Actual checks:

- 18 focused tests PASS, including normalization, cycles, progress/regression,
  unknown evidence, hard budgets, invalid coverage, continued terminal histories,
  CLI text/JSON parity and fresh-process repeatability.
- Eight existing repository regressions PASS.
- Sample CLI in text and JSON formats PASS; both return `blocked` / `stalled`
  at round two and the same resume condition.
- Sixteen fixed comparison cases executed; promotion result REJECT.
- Required full `scripts/validate_candidate.py` PASS on Windows CPython 3.14.5:
  deterministic unpublished candidate archive, extracted first-run journey,
  fresh-session continuation, 86 packaged regressions, eight repository
  regressions, 139 bounded text-file scans and 181 local links. This validates
  that existing candidate journey; it does not integrate the new experiment.

The comparison fixtures were authored before the first run; no policy threshold
was adjusted after observing their outcomes. Run 002 adds a missing-field
validation correction and regression test; fixture bytes and results are
unchanged. It is a replay of the same held-out cases, not a fresh evaluation
split. These are deliberately constructed
traces, not a statistical estimate or a live-agent benchmark. Hashes establish
artifact identity only. No real model, billing, elapsed-time enforcement,
attended human acceptance, H3 or hosted/production evaluation ran.

## Integration decision

Keep v1 advisory and outside the distributed runtime. Do not replace the
three-cycle cap or convert this result into installed-policy acceptance.
A future iteration should distinguish independently measured no-progress from
worker assertions and abstain when the evidence cannot support a stall. It must
use newly frozen held-out cases rather than retuning against this split.
Real-worker shadow evaluation is the next evidence level: record the decision
without stopping the worker, then compare with the remaining authorized rounds.
That work is proposed, not performed or enabled by this experiment.

For the capability contract, trust boundary and feature-standard gate limits,
see [README](README.md). In particular, authenticated authority and attended
human usability remain unverified; no feature-standard completion is claimed.
