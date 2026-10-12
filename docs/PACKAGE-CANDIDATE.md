# First-run repair candidate

`2026.10.12-public.4-candidate.1` is an unpublished candidate derived exclusively from the immutable public.2 package at main `0bf301cd3de28c9dedd2ff68e4459ccd22b6bb81`. A separate public.3 candidate already exists outside main; its bytes and acceptance history are preserved. This candidate does not incorporate or supersede its unmerged feature policy.

Public.2 documents a literal `../aeos-first-run` destination, which the correct traversal guard rejects. The new FIRST_RUN resolves that destination to an absolute path in PowerShell. Package runtime/security code and all 86 tests are unchanged. Resume uses the installed sibling virtual environment, consistently with the website. Historical public.1/public.2 archives, extracted files, receipts and live download links remain unchanged.

The root README, package FIRST_RUN and site first-run command block agree. The site's existing public.2 download works with the absolute-path workaround shown there, but its bundled historical FIRST_RUN still contains the defect. Use the [new candidate instructions](../distribution/agentic-engineering-os-2026.10.12-public.4-candidate.1/FIRST_RUN.md) when testing the candidate. Publication requires a separate owner decision; this repair does not update site/downloads.

## Reproduce and verify

On Windows CPython 3.14.5, run `python -B scripts/validate_candidate.py --receipt <absolute-local-receipt.json>` from the repository. It verifies deterministic ZIP and manifest bytes, rejects unsafe archive entries before extraction, creates a disposable extraction with spaces in its path, reproduces the public.2 failure, and executes the candidate's actual published PowerShell steps. These steps create a fresh sibling virtual environment and install the declared pinned dependencies from PyPI. The demonstration itself makes no model/network calls, leaves Silver pending and Gold unapplied, and exercises stale/missing context refusal. It resumes from the demo output in a fresh process, verifies literal traversal/existing-output refusal, then runs the unchanged 86 regressions plus seven distribution regressions and public link/path checks.

`python -B scripts/build_candidate.py --check` checks reproducibility without writing. The builder refuses any existing candidate. ZIP metadata is deterministic. The adjacent `.sha256.json` records archive/manifest hashes and exact counts; the manifest authenticates bytes relative to its reviewed digest, not a trusted publisher signature. New findings require a new version, never silent replacement bytes.

## CI and owner controls

The workflow uses Windows and exact CPython 3.14.5 with pinned official actions, read-only repository permissions, a 20-minute limit and no production/private inputs. Installation/platform failures fail the check; they are not green runtime evidence. Proposed required check: **Package validation (Windows CPython 3.14.5)** from **Windows package validation**. An owner can add it to the existing PR ruleset after observing a successful run at the candidate SHA. No ruleset, Dependabot, secret scanning or CodeQL setting is changed. Existing main rules prevent deletion/force-push and require PRs but do not require this status yet.

Scope is the dependency pins and package runtime regressions, not a comprehensive transitive advisory audit, upstream HTTP health check, hostile same-user filesystem confinement, authenticated approvals, installed private OS certification, hosted usability or production release. H3 and owner acceptance remain separate from local/CI validation. Failed or missing results remain unknown; no accepted private milestone is reopened.

GitHub's [setup-python documentation](https://github.com/actions/setup-python) describes exact-version selection and downloading a missing tool-cache version. Availability of CPython 3.14.5 on the selected hosted runner is proved only by a successful candidate run.
