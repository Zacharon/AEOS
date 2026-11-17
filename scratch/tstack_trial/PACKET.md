# Tstack trial: clear refusal when results already exist

Status: local workflow pilot, not a full performance benchmark or release.
Use one implementer and one Sol reviewer. Maximum three review rounds. Do not
merge, publish, change accounts, call a council or widen scope.

## Goal and acceptance frozen before implementation

The failure-novelty comparator currently throws a traceback when its requested
output already exists. In the candidate copy only, turn an existing-directory
or existing-file collision into an understandable argparse error (exit 2),
preserving existing bytes. Continue using exclusive directory creation so the
refusal cannot overwrite prior evidence. New output must still work.

Allowed code writes: candidate/compare.py only. The separate trial runner and
report are evidence, not production changes. Baseline files, original experiment,
policy behavior, fixture labels and repository distribution/site are out of scope.
Input/cumulative budget logic is unchanged.

Acceptance:

1. Existing output directory: exit 2, clear error, no traceback, marker unchanged.
2. Existing output file: exit 2, clear error, no traceback, bytes unchanged.
3. New output: successful comparison with saved summary and sample trace.
4. Candidate's original 18 focused regressions pass.
5. Baseline and original source hashes remain unchanged.

Both copies start from the identical manifest in source-manifest.json. The
baseline runs the same acceptance checks without the fix. This is a real
local reproduction-and-repair trial on synthetic experiment tooling, not a
matched baseline-agent versus candidate-agent study. Do not infer token savings,
human productivity or team superiority from it.

## Capability route and evidence

Human: `python -B trial.py --variant candidate --output evidence/candidate.json`.
Agent: the same CLI writes JSON. `--variant baseline` demonstrates the original
failure using identical acceptance checks. The runner uses isolated copies,
never dispatches a model, and never operates on a personal vault. Evidence
destinations are new files under evidence/; existing evidence is refused.

Use T3 delegate_task for the Sol review. Its brief names exact paths and code
hashes and forbids edits/subagents. Record findings with severity and disposition.
No response, timeout or budget end counts as approval. New behavior changes
need a fresh review; minor documentation fixes do not.

Usage fields remain UNKNOWN unless returned by the platform. Record command
elapsed time separately from model time. This pilot does not run the proposed
ten-task benchmark, a human-team comparison, or Full Send. PR filing and watching
are separate real-service stages; local proof does not establish either one.
