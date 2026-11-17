# Synthetic retrieval fusion workbench

Bounded, offline source-preview candidate. All documents, query vectors and
relevance judgments here are newly authored synthetic fixtures. They are not
user records or human acceptance labels. Neural retrieval is NOT RUN: an
installed embedding library alone is insufficient without an available local
sentence model. No network, model downloads or billing occur in this workbench.

## Capability contract, fixed before measurement

`synthetic-retrieval-diagnostic/v1` reads only this directory's frozen fixture
allowlist. Human controls are a terminal workbench; agent controls are JSON
requests to the same command handler. Inputs: operation (`benchmark` or `query`),
query ID for inspection, and optional output basename. Outputs: typed JSON
rankings, authored relevance metrics, development-only policy and provenance.
The default human display and JSON invocation share `execute(request)`.

The authoritative inputs are `fixtures/manifest.json` and its SHA-256 pins.
Readers validate these pins on every invocation. Rankings are suggestions;
they do not expand a handoff's authorized read set, resolve conflicting versions,
mint an approval or apply trusted knowledge. There is no authenticated principal
or multi-user service. OS process access is the boundary of this local fixture
diagnostic; scoped user grants and expiry are not implemented.

`benchmark` measures development first, freezes a single global selection,
then opens held-out queries for scoring. Selection never accepts held-out labels.
No query-specific oracle routing. The strongest development component (BM25 or
vector fixture; lexical wins ties) is the no-fusion default. A fusion candidate
must improve development nDCG@3 by at least 0.02, harm neither component on any
answerable development query, preserve multi-hop completeness and not increase
no-answer false positives. Candidates and cutoffs are fixed before the first run:
RRF constant 60; interpolation vector weights 0.3, 0.5, 0.7; component depths
1, 3, 6; context cutoffs 1, 3, 5; primary depth 6 and cutoff 3.

Execution is synchronous, CPU-only and bounded. Interrupting cancels computation;
no external jobs exist. Results are printed unless an explicit new output
basename is supplied. Existing outputs are refused, preserving previous runs.
Local generated benchmark evidence is the only write effect; no application or
user data is changed. Retry by rereading the saved JSON or use a new basename;
there is no user-data Undo or receipt transaction. Authenticated product parity,
hosted behavior, human acceptance and independent review remain separate gates.

## Source seam

The preview documents manual selection, not automatic search, in
`docs/ARCHITECTURE.md`. The current public.4 handoff module exposes read-only
`safe_relative`, `within`, `markdown_bytes` and `digest` helpers. The experiment
imports those helpers by file location to validate synthetic Markdown and emit
path/hash suggestions. It never calls the handoff builder or changes the package.
This is an adapter diagnostic, not an existing retrieval backend replacement.

## Run without AI

From the repository root, with Python 3.11+ and no additional dependencies:

```powershell
python -B experiments/arxiv-20261113-retrieval/benchmark.py benchmark
python -B experiments/arxiv-20261113-retrieval/benchmark.py query h-version-1
python -B experiments/arxiv-20261113-retrieval/benchmark.py benchmark --output my-results.json
python -B -m unittest discover -s experiments/arxiv-20261113-retrieval -p 'test_*.py' -v
```

`--output` resolves a **new basename inside this experiment**, regardless of the
caller's current directory. `results.json` already contains the final recorded
measurement, so rerunning that exact output name refuses it. Omit `--output` for
readable stdout, or choose a new basename to preserve another measurement.
Inspect a case before trusting a rank: the version example shows an obsolete
document moved above the current one by fusion. Use Ctrl+C to stop a run.

The agent JSON invocation uses the same handler and fixture guards:

```powershell
'{"operation":"query","query_id":"h-version-1"}' | python -B experiments/arxiv-20261113-retrieval/benchmark.py json
'{"operation":"benchmark","output":"agent-results.json"}' | python -B experiments/arxiv-20261113-retrieval/benchmark.py json
```

JSON requests reject unknown fields, duplicate keys, malformed requests,
unknown query IDs and outputs outside this directory. They return JSON on stdout;
refusals return `{"status":"REFUSED","error":"..."}` on stderr and exit 2.
There are no endpoints, accounts, remote indexes or background services.

For a reusable in-process adapter, import `FixtureAdapter` from `benchmark.py`
with this directory on the module search path, then use `search_method` and
`select_from_development` from `retrieval.py`. Supply vectors explicitly;
the vector adapter never generates or fetches embeddings. The exported
`selection.json` contains the fixed development policy and fixture/policy hashes.
For a selected-method lookup use `search_method(policy['selected_method'],
adapter.lexical, adapter.vector, text, supplied_vector, depth=6)`.
Arbitrary text may be searched through that Python API; the inspection CLI only
accepts frozen case IDs so it never pretends to encode an unseen query.

## Interpret the measurements

`results.json` contains all ranks/scores, authored qrels, per-query metrics,
candidate-depth sweeps (1/3/6), context cutoffs (1/3/5), whole-document word budgets
(30/60/120), no-answer false positives, and repeated latency samples. Answerable
queries alone enter Recall, MRR and nDCG averages; no-answer metrics are `null`
and their false-positive rate is separate. Relevance grades are 1 or 2; nDCG uses
`2^grade-1` gain and logarithmic discount. Multi-hop completeness requires every
authored relevant document. MRR is truncated at each reported cutoff.

Harm is a lower nDCG@3 than each named reference, with a tolerance of 1e-12.
The `better_component` reference is a **diagnostic oracle only** and never
controls selection. Positive `fusion_tax` means harm. Both helped and hurt cases,
conditional loss/gain and worst loss are retained. Word budgets count whitespace
words, preserve a whole-document prefix and stop at the first document that does
not fit. They are not a tokenizer, reranker or answer-generation evaluation.

See [REPORT.md](REPORT.md) for measured findings, source-method links, individual
feature gates and remaining integration prerequisites. [FILES.json](FILES.json)
lists the exact experiment files and their hashes; it does not certify behavior.
Prior measurements, the failed exact-repeat comparison and successful correction
are retained under `evidence/`. Do not tune the held-out cases; use a separately
authored future split for any new retrieval policy.
