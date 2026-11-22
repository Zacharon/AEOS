# Code rationale and handoff — local candidate rule

Leave changed code understandable without the original conversation. Explain
non-obvious decisions, assumptions, business constraints, compatibility and
security boundaries, ordering, and failure behavior near the relevant code.
Describe meaningful public contracts, side effects and failures. Update or
remove stale explanations after each meaningful change. Explain why, not syntax;
never invent historical intent and label inferred rationale explicitly.

Keep implementation knowledge in the repository's existing README/development
guide. For multi-part behavior, identify actual editing paths and symbols,
affected layers, invariants and verification commands. Large decisions may need
a short record of the problem, choice, alternatives actually considered and
consequences. Small changes need no new decision document or inline comment.

Use the existing task report for what changed, why, constraints, where to edit,
alternatives when relevant, verification actually run and remaining uncertainty.
Link to current comments/guides/decision records. An explicit
`documentation-not-needed` disposition is legitimate for a simple change, with
a reason. Do not add line-by-line narration, model banners, chat transcripts,
unrelated rewrites, secrets or customer information.

Before review, inspect actual task-start-to-current changes, run the configured
coverage check, and have the independent reviewer compare rationale with code
and tests. Coverage does not prove explanation quality. Preserve H3 and owner
gates; a worker's report is not acceptance.

## Editing this capability

- Boundary/inventory and new/deleted files: `code_rationale.py`, `inventory` and
  `changes`. Do not switch to HEAD: dirty task-start bytes are the baseline.
- Record schema, links and freshness: `code_rationale.py`, `check`. The change
  digest covers exact before/after hashes; reference digests and text locators
  bind the editing guidance to current repository content.
- Runner completion: `code_rationale.py`, `complete`, and `handoff.py`, `main`.
  Preserve existing bundle/result/source checks. Require the frozen scopes to
  equal all packet Allowed Writes and actual paths to equal worker declarations.
- Tests: `test_code_rationale.py` and existing `test_handoff.py`. Run
  `python -B -m unittest discover -s <this-directory> -p "test_*.py" -v`.

## Trust and operating limits

The controller records the task-start baseline and its SHA-256 before work,
retains that digest independently, and pins these three control files outside
the worker's allowed writes. If they need changing, use a separate reviewed
candidate. Do not regenerate the baseline, narrow scope, or edit rules to pass.
The checker detects control drift against the baseline; it cannot police its
own malicious replacement or authenticate a caller-supplied digest. Same-user
filesystem access is not an adversarial security boundary.

Use a dedicated working directory and serialize editing with checks. Concurrent
writes can race filesystem reads; this is point-in-time coverage, not an atomic
snapshot or attribution of authorship. Each directory scope includes *all*
files, even Git-ignored ones; no source-extension allowlist. Known private paths,
links/junctions, hardlinks, or excessive input cause rejection. Limits are
10,000 entries, 8 MiB per file, 64 MiB total. Narrow authorized directory scopes
are supported; this does not discover out-of-scope edits elsewhere. Independent
review must verify scope and preserve unrelated work.

Renames require both deleted and added paths, including renames with edits.
No heuristic rename pairing can remove coverage. Reports live outside the
frozen editing boundary to avoid recursive self-hashing; references must be
real repository files with exact hashes and a current symbol/heading substring.
This is not a general Markdown-link or line-number validator. Every durable
reference claimed as evidence must be listed in the record.

No service, model call, hook installation, background job or automatic rewrite
is involved. The CLI runs once, exits 0 or 2, has no retries, and remains
interruptible. Native Stop/PostToolUse support for this installed client has not
been established; no hook adapter is prepared. Manual runner use remains manual.
