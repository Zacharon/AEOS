# Issue handoff consolidation engineering review

Reviewed 2026-10-31 against main `f8b6258af5ed421c5c6803473ac92233378e701c`, PR #10 head `823c4479c437e1d1e349c3b39a06d3e73240ec48` and PR #11 head `6032ae0ef87762e73ecd1b37a1e5c67f9f4c0e12`. Every changed local file's Git blob hash matched the corresponding live PR file record before review. Main was rechecked through the connected GitHub workflow. No private AEOS installation or personal vault was read.

This review is independent of the two original implementations. The reviewer subsequently implemented the consolidation, so this document is **not independent H3 acceptance of the consolidated result**. Final H3 must come from a separate reviewer.

## Recommendation

Use PR #10's file-changing synthetic candidate pipeline as the only execution architecture. Bring in PR #11's stricter export parsing, source-hashed inventory and four-job portability matrix. Keep export inspection a pure read-only operation; do not retain a second packet/bundle/worker lifecycle or general live-task execution path.

| Area | PR #10 | PR #11 | Consolidated decision |
|---|---|---|---|
| Fixed task | One exact new synthetic file and change rationale | Read-only issue number/label inventory | One fixed file candidate plus inventory as a bundle artifact |
| Authority | Explicit synthetic-local CLI opt-in, immutable scoped-draft hash | Human edits packet approval; demo assigns fixture status | Retain explicit opt-in and immutable draft; no fixture auto-assignment shortcut |
| Intake | Synthetic assertion, strict fields/duplicate keys/size/secret checks; URL is arbitrary text | GitHub URL/number consistency, field/label caps, escaped issue markup | Retain synthetic-only task execution; adopt strict URL/label/text validation and pure export inspection |
| State/evidence | Frozen branch/HEAD, manifest/full-file/rationale digests, package check, replay refusal | Tool/context/manifest/file fingerprints, immutable bundle/audit | Retain stronger #10 lifecycle; add controller/locator/prepared-tree pins and reject unknown paths before reading |
| Acceptance | Exact bytes, actual worktree delta, result/artifact/rationale checks; patch generated | Recomputes inventory against source, including rehashed false-report test | Keep both independent mechanical comparisons; check patch applies during `verify` |
| Tests | 16 prototype tests in repository suite; Windows package workflow | 20 dedicated prototype tests; Windows/Ubuntu × Python 3.11/3.14.5 | One repository test suite, expanded refusal coverage, explicit prototype/public.4 matrix |
| Delivery | Candidate patch; no remote/service execution | No patch needed for read-only task | One reviewable patch and receipt; no automatic integration |

Duplicated packet builders, branch layouts, result envelopes, demo entry points and verification receipts are redundant. Retaining both would create competing authority/acceptance models and an unnecessary mode switch. The synthetic controller is deliberately narrow; package contracts remain the existing public.4 implementation. No framework, dependency, API integration, Docker runtime or authentication service is added.

## Findings and corrections

1. **PR #10 pre-handoff freeze accepts unexpected files.** Reproduced against the pinned original: after `prepare`, create `worktree/extra.txt`; authorized `handoff` succeeds and `git ls-files extra.txt` confirms the unexpected file was committed. `git add --all` precedes the original full-file baseline. The consolidated controller pins the prepared file set/hashes and checks them before any approval record or staging. Unexpected files/directories fail before their contents are read. This closes an intake-to-freeze integrity gap; it does not create a native sandbox.
2. **PR #10 patch applyability is only a test assertion.** The original happy-path test runs `git apply --check`, but production `verify` only writes a patch. The consolidated verifier performs the check itself against the unchanged seed before writing a success receipt; a patch-conflict regression reproduces refusal.
3. **PR #11 provides stronger schema/semantic checks but a narrower result.** Its URL/number/label validation and independent inventory comparison are useful. Its read-only pipeline omits change-rationale/patch delivery by design, so replacing #10 wholesale would lose the file-changing proof. Its Git wrapper disables hooks/signing but retains inherited `GIT_*` routing and global/system config; retain #10's sanitized environment and explicitly disable signing, CRLF conversion and fsmonitor for all Git calls.
4. **PR #10 intake and return can be more precise.** Adopt #11's escaped serialized context, bounded label parsing and strict GitHub issue URL shape. Independently verify the returned inventory even if the worker recomputes its artifact hash. Require the fixed declared change and no proposed canonical writeback. Pin the controller source and worktree Git locator to detect phase-to-phase drift relative to trusted controller records.
5. **Both share non-goals that must remain explicit.** Same-account file hashes are not tamper-proof storage; a worktree is not a security boundary; self-reported checks are not H3; assignment/status is not authenticated authorization; green CI is not owner acceptance. Neither implementation performs autonomous model execution. No approval, identity or production-readiness claim is promoted.

## Verification evidence

Original pinned implementations were rerun on Linux CPython 3.12.14: #10's 16 prototype tests passed and #11's 20 prototype tests passed, without skips. The pre-handoff finding above was also reproduced outside either checkout in a disposable repository.

Hosted source evidence was rechecked, separately from consolidated-code evidence:

- [PR #10 Windows validator](https://github.com/Zacharon/AEOS/actions/runs/41136202250): successful Windows/Python 3.14.5 job.
- [PR #11 prototype matrix](https://github.com/Zacharon/AEOS/actions/runs/41136441308): all four Windows/Ubuntu and Python 3.11/3.14.5 jobs successful.
- Original boundary workflow runs `41136202251` and `41136441224` reported success. They apply to the original heads only.

Actual consolidated test/scan results, source hashes and environment are recorded in [local-verification.json](../prototypes/issue_handoff/local-verification.json). New hosted CI applies only to the new PR head; consult that PR's checks. The Windows-only package validator cannot be locally completed on Linux. It validates the older unpublished candidate separately from the frozen public.4 contract suite.

The initial broader matrix also ran the entire repository suite. Ubuntu/Python 3.14.5 passed all 26 prototype tests but failed the historical candidate ZIP's deterministic-byte comparison ([run](https://github.com/Zacharon/AEOS/actions/runs/41248192681)). That archive, builder and test are unchanged from main. This indicates an existing archive/toolchain portability limit, not a demonstrated prototype failure. The dedicated matrix now runs the prototype and public.4 contracts; full repository regression coverage stays in the existing Windows package workflow, with Linux 3.12 local evidence recorded separately. The archive failure is retained as a known uncorrected limitation; no frozen archive is rebuilt or test removed.

Initial Windows jobs also exposed a test-fixture attribute difference. Making the locator writable alone did not resolve Windows hidden-file create/truncate behavior. The regression now opens its disposable locator in existing-file update mode before corrupting it, so Windows exercises controller digest refusal rather than failing while arranging the test. The production safeguard is unchanged. [Microsoft documents the existing hidden-file creation restriction](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

## Remaining acceptance and original PR disposition

Deliver the consolidation as one draft PR targeting main. Supersede and close #10/#11 without merging, preserving their branches/history and linking this review from the consolidation. Closing originals is housekeeping, not acceptance of the replacement. No merge, release, archive rebuild, site deployment or provider action is authorized by this document.

Before integration: obtain a different reviewer's H3 decision against the exact consolidated head; reproduce the documented manual T3/assistant return; run the documented commands on the target Windows 10 setup; inspect hosted prototype/public.4 matrix and full-history boundary results; record a separate owner integration decision. An unavailable or failed acceptance check remains explicitly unverified and must not be converted into a passing claim.
