# Failure novelty: candidate experiment

Standalone synthetic experiment, not an installed AEOS policy. No model calls,
dispatch, personal vault access, distribution changes or publication. The
three-round ceiling remains fixed. Time and cost ceilings remain independent.

## Frozen experiment contract

Capability `failure-novelty/v1` reads one JSON trace and returns a recommendation.
Humans use `python -B policy.py trace.json --format text`; agents use the same
command with `--format json`, or `assess(trace)`. Both invoke the same validation
and handler. Exit 0 means valid assessment, including blocked; exit 2 means invalid
input. No commands, paths or actions in the trace are executed or opened.

Run from this directory, using an existing Python 3.11+ interpreter:

```powershell
python -B -m unittest -v test_policy
python -B compare.py --output results/run-001
```

The fixture file contains compact cases rather than a single trace.
The comparator emits a usable `sample-trace.json`.
Then use `python -B policy.py results/run-001/sample-trace.json --format text`.
The comparator creates a new results directory, refusing overwrite. It records
fixture/code hashes and per-case outcomes. Saved JSON is the durable record;
there is no separate in-memory service, mutable session or authenticated actor.
Rereading the same trace in a fresh process yields the same assessment.

Inputs bind a fixed scope revision, required check IDs, positive time/cost limits
and up to three ordered observations. Every observation covers exactly the
required checks, declares failures, cumulative elapsed seconds/cost units,
progress (remaining-work measure plus evidence references), remaining justified
actions, and any explicit blocker. Cost units are synthetic, not dollars/tokens.
Metrics must keep the same definition and unit for the complete trace.

Failure identity is the sorted, deduplicated set of structured `check`, `category`,
`subject`, `expected`, `actual` strings. Whitespace is canonicalized; case and
semantic values remain significant. Optional `diagnostic` and `observed_at` fields
are preserved in input but excluded from identity. Producers must put volatile
timestamps/temporary paths there, not in semantic fields. No broad regex strips
potentially meaningful paths, numbers or identifiers. SHA-256 gives identity,
not truth. Different failure sets are not assumed to be progress.

Candidate v1 looks for a repeated nonempty failure signature within all three
rounds, including A/B/A. It recommends `blocked` / `stalled` only if every metric
since that signature first appeared is known, evidence-backed and unchanged,
and the current observation lists no justified remaining action. A changed
metric, including a regression, prevents an early stall classification. Unknown
progress does not establish no progress. At the limit it still returns blocked.
Success requires explicitly passed checks with no failures and evidence for
each required check. Blockers and exhausted time/cost budgets take precedence.
Nothing returns `impossible` or claims independent review/owner acceptance.

## Comparison and limitations

Development and held-out fixtures are authored and frozen before the first run.
They are deterministic counterfactual traces, not independent empirical samples.
The baseline continues until success, explicit blocker or hard ceiling; the
candidate adds recurrence/no-progress stopping. Both see only the observed prefix.
The evaluator never sees fixture `solvable_at` labels. The comparator uses those
labels to count premature abandonment and computes saved rounds. No latency,
token savings or real agent productivity is inferred from replayed rounds.

Promotion requires zero premature stops in each split and some saved rounds on
unsolved traces. An intentionally misleading no-progress report followed by
success tests the trust boundary; failure on that case must remain visible.
Do not tune away a held-out failure and report the same split as held out again.
New versions need new untouched cases and actual model trials before deployment.

Progress, check evidence, scope revision and remaining actions are supplied
assertions. This read-only evaluator does not authenticate them, read evidence
or establish actual task feasibility. A producer can forge a consistent trace.
No authenticated multiuser authority, sandbox, clock or billing enforcement is
provided. An eventual controller must collect and bind actual observations and
enforce budgets outside the model. This CLI is advisory only.

## Feature-standard evidence scope

Gates 1/2: shared handler and saved trace; unit tests compare CLI formats and
fresh-process results. Gate 3: PARTIAL for product use: read-only assessment has
no delegated effects but trusts supplied observations and has no identity layer.
Gate 4: CLI help, text errors and no-AI workflow are locally tested; attended
human acceptance NOT RUN. Gates 5-7: NOT APPLICABLE to the read-only evaluator;
the fixture runner writes new synthetic evidence only and refuses overwrite.
No installed feature completion or H3 acceptance is claimed.

## Integration seam and sources

Keep this directory outside frozen distributions. A later scoped integration can
attach failure observations as result artifacts and map recommendations to the
existing worker `blocked` state with reason and resume conditions. Do not add a
new completion state or relax `handoff.py`'s three-cycle check. Any schema/runtime
integration needs its own review and real-worker evidence.

- [Architecture study: loop guards](https://arxiv.org/html/2609.00006v1#S6.SS2)
- [Architecture study: inexpensive caps](https://arxiv.org/html/2609.00006v1#S16.SS9)
- [Verification study](https://arxiv.org/html/2610.34577v1#A5.SS5)

These motivate the experiment, not an experimentally validated AEOS policy.
