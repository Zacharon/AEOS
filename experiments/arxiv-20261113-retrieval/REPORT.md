# Retrieval fusion diagnostic: bounded local candidate

The development-only selection retained **BM25 without fusion**. On the ten
answerable held-out queries, BM25 achieved nDCG@3 **0.9275** and RRF **0.8639**.
Recall@3 was 1.0 for both: coverage alone concealed ranking harm. RRF harmed two
queries versus BM25 and one versus the vector-fixture component. This supports
keeping fusion optional in this synthetic diagnostic, not a claim about neural
retrieval or a production recommendation to replace manual selection.

Source HEAD: `123fa34e60445ccfda36bf3a139f5b031b6c04a3`. The source remote and
dedicated experiment checkout were verified before writes; initial Git status was
clean. Absolute machine paths, account identifiers and branch/campaign metadata
are intentionally excluded from this public artifact. The entire write scope is
`experiments/arxiv-20261113-retrieval/`; [FILES.json](FILES.json) is its exact file
inventory. No production source, distribution, archive, site, approval or trusted
knowledge flow was changed. All evidence is local and implementer produced.

## Methods transferred from the papers

[The Fusion Tax, arXiv:2610.30612v1](https://arxiv.org/html/2610.30612v1),
sections III and IV-B/D: compare the fused ranking against each component and
the better component per query; report benefits alongside harm. Its setup uses
Anserini BM25, actual neural encoders, top-100 lists, RRF with constant 60 and
min-max score interpolation. This experiment adapts those comparisons to a flat
stdlib BM25 implementation and explicit concept vectors. It uses much smaller
candidate lists and development-only selection; it does not reproduce BEIR,
encoder results, learned routing or significance tests. The oracle better-component
comparison is solely a diagnostic. No held-out label decides how to serve a query.

[Scaling Retrieval Augmented Generation with RAG Fusion,
arXiv:2603.02153v1](https://arxiv.org/html/2603.02153v1), sections 4–6 and appendix
A.4–A.7: evaluate evidence after finite candidate and final context budgets,
retain source identities, and account for extra latency. The paper combines an
original and LLM-rewritten query, uses chunk-aware RRF and reranking, and scores
article-level hits. This experiment instead combines lexical and supplied-vector
signals over whole synthetic documents, then measures prefix/word truncation.
Query rewriting, cross-encoder reranking and generation are NOT RUN. Context
survival is an adaptation of its diagnostic question, not a reproduction of its
pipeline or evidence of answer quality.

## Frozen design and honest baselines

The fixture seal is
`cbffc1a4f238d002d6c19d6e62379fba1e29c3b4d3ac44fde1a4dc8424822289`.
It was created before any retrieval measurement. There are 24 newly authored
Markdown documents and two disjoint query sets of 12 each: two cases per set for
exact IDs, synonyms, conflicting versions, distractors, multi-hop and no-answer.
Development and held-out use different query IDs, document targets and topics.
They deliberately share case templates and the same corpus, so this is not a
blind or statistically independent real-user study. Paired paraphrases are
correlated. The implementer authored all relevance judgments and vectors;
none are owner-provided labels or external human acceptance.

The actual public.4 `handoff.py` is imported, with its source SHA recorded in
`results.json`. `safe_relative`, `within`, `markdown_bytes` and `digest` validate
fixture reads and emit source/hash suggestions. `docs/ARCHITECTURE.md:57`
documents manual retrieval and the absence of an automatic search service.
There is no production retrieval/parser API to plug into. These handoff read
helpers are the existing seam; this explicit adapter is the evidence limit.
It never calls build/apply or widens `--read` authorization.

The executable content-search baseline is unique query-term overlap. BM25 uses
positive Robertson IDF, k1=0.9, b=0.4, a single flattened title/body field and
identifier-preserving tokens, with document-ID tie breaks. It is not Lucene
multifield BM25. The vector comparator performs cosine search on frozen authored
vectors with deliberate identifier/version confusion. Neural retrieval is
**NOT RUN**: the bounded local availability check found no cached sentence model;
an installed embedding library alone did not establish a usable local retriever.
No download, model call or provider billing was attempted. Manual human file
selection is NOT RUN because no human selections were supplied.

The primary depth is six candidates per component, context k=3. RRF uses 60;
interpolation uses min-max scores and vector weights 0.3/0.5/0.7, missing scores
zero, and constant nonempty score lists normalized to one. Normalization happens
at the selected candidate depth. The global selector first chooses the stronger
development component, then permits fusion only with at least .02 nDCG@3 gain,
zero nDCG harm versus either component, no multi-hop completeness regression and
no new no-answer false positives. All four fusion configurations failed this
predeclared gate. Selection completed before held-out qrels were parsed; a test
asserts that order. No policy, weight, fixture or threshold was tuned afterward.

## Held-out measurements

These values come from the final [results.json](results.json), depth 6. Harm
counts use ten answerable queries and nDCG@3; no-answer rates use two separate
queries. Full MRR/Recall/nDCG at k=1/3/5, category slices, ranks, scores and harm
versus lexical/BM25/vector/better-component are retained in the JSON.

| Method | Recall@3 | MRR@3 | nDCG@3 | Hurt vs BM25 | Hurt vs vector | No-answer false positives |
|---|---:|---:|---:|---:|---:|---:|
| Lexical overlap | 1.0000 | .9500 | .9283 | 1 | 1 | 1/2 |
| BM25, selected without fusion | 1.0000 | .9500 | .9275 | 0 | 1 | 1/2 |
| Authored vector fixture | 1.0000 | .8500 | .8378 | 3 | 0 | 2/2 |
| RRF | 1.0000 | .9000 | .8639 | 2 | 1 | 2/2 |
| Interpolation, vector weight .3 | 1.0000 | .9500 | .9116 | 1 | 0 | 2/2 |
| Interpolation, vector weight .5 | 1.0000 | .9500 | .9116 | 1 | 0 | 2/2 |
| Interpolation, vector weight .7 | 1.0000 | .9000 | .8747 | 2 | 0 | 2/2 |

Lexical overlap narrowly beat the development-selected BM25 on held-out nDCG.
It remains an honest comparator; we did not retrospectively select it. None of
the fusion candidates beat either lexical baseline in aggregate on this split.
RRF helped one query versus BM25 but harmed two, with mean change −0.06365 and
worst query loss 0.36907. The paper-style better-component reference remains
an unattainable diagnostic bound, not a deployable baseline.

Concrete failures: for `h-version-1` and `h-version-2`, RRF placed obsolete
`pol-9-v2` above current `pol-9-v3`; BM25 put the current version first.
Interpolation .7 also harmed exact-ID case `h-exact-1`. Fusion improved the
multi-hop ordering of `h-hop-2`, yet its top three still included the obsolete
route. With a 60-word context, BM25 and RRF retained only half of the required
evidence for each held-out multi-hop query. Complete Recall@3 thus does not mean
a usable bounded evidence packet. For `h-none-2`, BM25 abstained with an empty
list while vector/fusion returned unrelated candidates. No method resolves
versions or certifies that an answer exists.

## Truncation and timing

| Held-out setting | BM25 recall | RRF recall | BM25 nDCG@3 | RRF nDCG@3 |
|---|---:|---:|---:|---:|
| Component depth 1, use all candidates | .8500 | .9000 | .8275 | .7711 |
| Component depth 6, context top 3 | 1.0000 | 1.0000 | .9275 | .8639 |

At depth 1, the extra component increased candidate recall while the resulting
ranking had lower nDCG. At depth 6, candidate recall is saturated. Truncating
those candidates to top one reduces mean recall to .85 for BM25 and .70 for RRF.
A whole-document 60-word prefix reduces both to .90; at 30 words they retain .85
and .70, and at 120 words both retain 1.0. These are whitespace-word budgets,
not model token counts; the diagnostic performs no semantic reranking.

| Method | Warm median ms | Warm p95 ms |
|---|---:|---:|
| Lexical overlap | .12965 | .2884 |
| BM25 | .11095 | .3252 |
| Vector fixture | .23390 | .3511 |
| RRF, including both searches | .42065 | .6929 |
| Interpolation .3, including both searches | .40555 | .6784 |
| Interpolation .5, including both searches | .40570 | .6640 |
| Interpolation .7, including both searches | .45910 | .6633 |

Each method has one warmup and nine timed repeats per query: 108 samples over 12
held-out queries per method. Runs are sequential, single-process CPU work on
Windows CPython 3.14.5. Timing includes required searches, vector validation and
fusion; it excludes imports, file reads, embedding inference and reranking.
The tiny corpus, fixed method order, scheduler noise and fixture-validation cost
make these overhead diagnostics, not deployment latency estimates. Repeated
samples are not 108 independent queries. No statistical significance is claimed.

## Actual execution and failures retained

The [README workbench](README.md#run-without-ai) gives complete human and JSON
commands sharing `execute(request)`. Saved command outputs are under `evidence/`.
The final implementation suite passed **16/16**, including arithmetic checks,
malformed vectors, duplicate ranks/JSON, absent evidence, output scope/refusal,
fixture tampering, development-only selection, subprocess hash seeds and
human/JSON parity across restart. A full benchmark was run four times; earlier
measurements remain under `evidence/results-run-01.json` through `03.json`.
Final run 04 is `results.json`; output names were moved after recording so no
previous measurement was overwritten. `selection.json` retains the identical
original development policy.

The first exact repeat comparison **FAILED** on raw scores differing by about
1e-15 because BM25 summed an unordered term set. The failure is preserved in
`evidence/reproducibility-run-01.json`. Sorting terms corrected numeric
repeatability without changing any case or selection rule. Full final-code
runs under process hash seeds 1 and 2 now match exactly on scores, ranks, metrics
and policy, excluding only measured timings
(`evidence/reproducibility-run-02.json`). Existing-output refusal intentionally
returns exit 2 and leaves saved bytes unchanged; it is an expected negative check.

Existing repository checks passed: distribution tests **7/7**, setup route **1/1**,
inline-image/link/privacy tests **4/4**, and safe scanner unit subset **7/7**.
The tracked-file boundary scan passed **273 files, zero findings**. A separate
explicit scan covers this untracked experiment; the default tracked scan does
not cover new files. See the final verification record for its exact count.

The full release validator is **NOT RUN**: its journey creates an environment
and invokes pip installation. The full repository/issue-handoff and scanner
history suites are **NOT RUN**: they create synthetic Git commits/worktrees.
Those actions exceed this experiment's dependency/Git restrictions. We ran the
permitted focused checks instead, without claiming the omitted suites passed.
No live model, hosted, human, independent H3, security or release closure was run.

## Feature-standard gates

| Gate | Status | Evidence and limit |
|---|---|---|
| 1. Shared capabilities | PASS, local diagnostic | Human command and JSON request call `execute`; subprocess test compares identical rankings/validation. |
| 2. Shared state | PASS, read-only fixture scope | Both load the same sealed fixture snapshot; query outputs and hashes agree after process restart. No application state mutation is implemented. |
| 3. Scoped authority | PARTIAL | Fixed synthetic allowlist and output boundary enforced using public handoff read guards. No verified user principal, cross-user grant or expiry service exists; process access is not authenticated product authorization. |
| 4. Human usability | PASS, terminal scope | Readable benchmark/query workflow works with AI disabled, documented JSON requests, understandable errors and Ctrl+C. Real-user acceptance and a product GUI are NOT RUN. |
| 5. Visible supervision | NOT APPLICABLE | Only synchronous read-only fixture diagnostics and generated local evidence; no delegation, user-data write or external effect. |
| 6. Safe recovery | NOT APPLICABLE | No user-data effect/Undo. Evidence outputs refuse overwrite; interruption has no external job. |
| 7. Receipts | NOT APPLICABLE | No user-data transaction or external effect. Saved measurements are experiment evidence, not authenticated product receipts. |

Gate 3 prevents claiming completed product compliance. This is an implemented,
executed candidate diagnostic, not an accepted product feature. Project/global
owner decisions, Gold approval and release gates retain their separate status.

## Integration recommendation and next step

Keep the preview's existing explicit manual selection. The code supplies an
optional read-only suggestion/selection seam, but this fixture experiment is
insufficient to activate a retrieval backend. Its adversarial vectors intentionally
create failure modes; their measured quality cannot predict a real dense encoder.
Small, templated splits, saturated Recall@3, authored grades and no true reranker
further limit transfer. No claim about real-user time saved or answer correctness
is supported.

A subsequent separately scoped proposal should supply an approved real local
retriever and independently authored fresh cases, retain identifier/version and
no-answer safeguards, measure the actual final context budget, then review
path/hash suggestions through the existing explicit `--read` handoff controls.
Recheck source hashes and authorized read scope at packaging time. Include
authenticated authority and relevant feature gates before calling it a product
integration. No source patch was applied or proposed outside this directory.
