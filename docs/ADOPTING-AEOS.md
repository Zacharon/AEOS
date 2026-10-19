# Evaluating AEOS for a small business or team

This guide describes a controlled evaluation of the public source preview, not an enterprise-certified product or authorization for commercial use. Check the reserved-rights [LICENSE](../LICENSE) before business use; commercial licence, distribution and support terms remain unset. Start with synthetic data, then use only data and tools your organization has authorized.

The current package is **2026.10.17-public.4**, derived from frozen public.3. It requires CPython 3.11 or newer. Its [verification receipt](../site/verification-public.4.json) records local Windows PowerShell tests on CPython **3.11.15 and 3.14.5**, with PyYAML 6.0.3 and jsonschema 4.26.0. That is evidence for those configurations, not every Python 3.11+ environment. Linux/macOS package execution and live provider handoffs remain unverified.

## Start a bounded team evaluation

1. Download the current [public.4 archive](../site/downloads/agentic-engineering-os-2026.10.17-public.4.zip), extract into a new folder outside any existing vault, and follow [FIRST_RUN.md](../distribution/agentic-engineering-os-2026.10.17-public.4/FIRST_RUN.md) in PowerShell from that folder. Use its fresh sibling virtual environment, explicit interpreter, pinned requirements, manifest check and absolute output path. Choose absent sibling names; preserve existing evidence. Dependency installation uses PyPI; the synthetic demo makes no network or model calls and stops at pending Silver without applying Gold.
2. Create your team vault from the package `vault/` templates in a separate, backed-up location under version control. Never point AEOS at a folder that also holds credentials, synced personal files or browser data.
3. Decide who holds each role in [Roles and permissions](#roles-and-permissions) and write it in the vault's `AGENTS.md`. Follow FIRST_RUN's project edits, replace the Sample scope and remove the synthetic packet; sample status is not live authorization. Git 2.x is required for Librarian apply/rollback, not for the synthetic demo. Obsidian is optional.
4. Agree your data labels using the [data-handling skill](../.agent/skills/aeos-data-handling/SKILL.md) before the first real packet.
5. Scaffold one low-risk task with the documented packet builder. It creates a draft: fill scope, checks and approval requirements and obtain the applicable authorization before building a handoff. Run packet, bundle, `check`, result, `validate-result` and `review`, followed by applicable independent H3 and owner-controlled integration. Mechanical `review` is not independent H3.

Upgrades follow the [package README](../distribution/agentic-engineering-os-2026.10.17-public.4/README.md): extract each new version beside the old one, verify it, and copy only chosen tools into your vault after a backup. No service is installed; preserve vaults and run evidence when removing an extraction. Historical archives, including the separate unpublished public.2-lineage repair candidate, are not this setup route and must retain their original bytes.

## Using any model or assistant

The shipped tools do not call a model. They prepare bounded files for a manual handoff to an assistant or person approved by your organization. Check that the receiving tool can use the files and return the required result; no live model compatibility is established by the synthetic demo.

- **Manual model-neutral route:** scaffold the packet with `--worker-tool Human`, then complete and authorize it; build the bundle with `--executor human`. A person carries the approved brief and selected context to the receiving tool and brings back `worker_result.json` and evidence. See the [handoff skill](../.agent/skills/aeos-handoff/SKILL.md) for CLI paths and steps. This is file transport, not an API integration or a guarantee that every model can follow the contract.
- **Named presets:** `codex`, `grok-build`, `grok-fleet` and `hermes` exist as packaging presets. They are labels for the manual handoff, not integrations, and are not required.
- **Instructions for assistants:** this repository keeps one canonical [AGENTS.md](../AGENTS.md) and tool-neutral skills in [.agent/](../.agent/README.md). `CLAUDE.md` and `GEMINI.md` only point to `AGENTS.md`, so tools that look for those names read the same rules. Add the same one-line pointer for any other tool rather than copying text.

Before switching assistants, confirm data authorization and packet scope still apply and run `handoff.py check` against live sources. The executor must match the packet's `worker_tool`; changing that assignment requires a newly authorized packet and bundle. Do not relabel or edit saved evidence to bypass the check.

## Protections already in the package

These are local checks and behaviors in the current package, with regression evidence recorded in its receipt. Their scope matters:

- **Bounded context.** Handoff accepts one to eight selected UTF-8 Markdown context/skill files in addition to the packet. Each source is limited to 64 KiB; packet plus context is limited to 256 KiB. Selected context must fit Allowed Reads and include every Read First file. `check` verifies hashes and refuses changed or missing sources. These checks do not constrain an assistant's separate filesystem or network access.
- **Secret refusal (backstop).** The packet builder rejects selected secret-like project/output paths. Handoff has its own broader path exclusions and checks selected Markdown contents for specific credential patterns. The tools do not share one comprehensive detector; neither detects all secrets or confidential records. Review content before selection.
- **Path safety.** Parent traversal, symlinks, Windows junctions and hardlinks are refused for Librarian inputs, stores, targets and backups. Outputs refuse to overwrite existing evidence.
- **Untrusted sources.** Source and snapshot text is labelled as data, never instructions. This is a handling rule, not enforced prompt-injection isolation.
- **Recorded approval checks.** Handoff rejects draft packets and final H3 verdicts on new execution handoffs; returned worker results cannot claim H3 approval. Librarian apply requires recorded owner approval after verification, matching evidence fingerprints and a clean Git checkpoint containing the required bytes. Rollback checks the recorded backup. These checks validate records, not the identity of whoever edits them. Run the documented dry run before an authorized apply; the implementation does not require proof of a prior dry-run invocation.
- **No background activity.** No scheduler, service, account, registry change, network listener or credential configuration is installed.

The rules that workers must not approve their own work, reviewers must be independent and only the owner can authorize Gold remain mandatory procedures. Enforce access outside AEOS; a process with the same user's file permissions can edit these records. A passing check is not approval.

## Repository scanner and CI coverage

The repository's [boundary scanner](../scripts/check_public_boundary.py) is separate from the installed package. From this repository root, run `python -B scripts/check_public_boundary.py` (use your available Python 3 interpreter). By default it reads the working-tree bytes of Git-tracked files, including staged additions, and recursively reads ZIP members within each archive's bounds (500 non-directory members and 50,000,000 declared uncompressed bytes). Findings cause a non-zero exit. Optional positional paths narrow the scan; it is not automatically a Git hook or a scan of an arbitrary team repository.

It matches selected credential values, private-path text and suspicious basenames. Non-UTF-8 content is skipped apart from filename checks; untracked files (including ignored files that are not tracked), Git history, unknown secret formats and classification of personal/business data are outside its coverage. A clean result does not establish that a repository is safe to disclose. `.gitignore` only helps prevent accidental additions; it does not remove tracked secrets or enforce access control.

- [Boundary CI](../.github/workflows/boundary.yml) runs the nine scanner tests, the tracked-file scan and a full-history scan on Ubuntu. The history scan reads every file version reachable from the checked-out commit, so a credential committed and later deleted still fails. The tests cover synthetic marker matches, named secret assignments, neutral placeholders, selected filenames, ZIP contents, malformed ZIPs, tracked/untracked selection, a deleted secret in history and the current repository. Archive size/member limits, nested archives and binary-content skipping have no dedicated regressions in that suite. Cross-platform source compatibility is not a tested Windows/macOS scanner matrix.
- [Windows CI](../.github/workflows/validate.yml) runs `validate_candidate.py` on CPython 3.14.5. It executes the older unpublished repair candidate's journey and 86 package regressions plus repository tests. Its link/privacy checks also inspect current public.4 files, but it does **not** execute current public.4's first run or test a Python 3.11 matrix. Current public.4's Windows 3.11.15/3.14.5 results are the separate local receipt cited above.

Neither successful workflow is an exhaustive security audit or an independent H3 review. Require a separate review of the final change and record its scope, verdict and remaining checks before owner-controlled integration.

## Roles and permissions

AEOS records roles in files; it does not authenticate people. Enforce the roles with the access controls you already have (repository permissions, branch protection, required reviewers).

| Role | Does | Typical control |
|---|---|---|
| Owner | Sets owner-decision fields, approves Confidential data use, accepts results, approves Gold | Only role with merge rights on the vault's protected branch |
| Controller | Builds packets and bundles, writes back verified facts to project state | Write access via pull requests |
| Worker (assistant or person) | Does only what the packet allows and returns evidence | No direct vault write; returns `worker_result.json` |
| Independent reviewer (H3) | Reviews someone else's result | Required reviewer, never the worker |

Small businesses can have one person hold Owner and Controller, but keep the worker and the independent reviewer separate.

## Sequenced tasks and automation

AEOS work is a sequence of packets: one goal, one packet, one bundle, one result, one review, then the next. The project's `NEXT_ACTIONS.md` and the vault's global queue hold the order. Nothing runs on its own.

If you script around the CLIs (for example a CI job that checks bundles), keep the workflow intact:

- `handoff.py` prints JSON on success and exits 0; on rejection it prints `{"result": "rejected", "reason": ...}` to stderr and exits 2. Treat any non-zero exit as stop, not retry.
- Run `check` immediately before each handoff and `review` after each return. Drift means a new authorized bundle, never edited hashes.
- Keep owner decisions, independent H3 and authorized Gold application separate from unattended orchestration. This is a team procedure, not a scheduler or authenticated permission gate built into the CLIs. `verify`, `check`, `review` and `complete` are mechanical evidence only.
- Stop after three failed repair cycles and hand the task back to a person.

## Datasets and business records

Keep datasets in a separately approved environment and pass a minimal data dictionary and question by reference. Handoff's Markdown/size limits and Librarian's default 2 MiB source-read limit are resource bounds, not data-loss prevention: small sensitive extracts can still fit. Labels and redaction requirements are documented procedures, not enforced classification. A reference grants no access; separately authorize any actual dataset access in the receiving environment, and inspect returned artifacts for disclosure before storing them. Follow the [data-handling skill](../.agent/skills/aeos-data-handling/SKILL.md).

## Known limits

- Current public.4 has local Windows evidence on CPython 3.11.15 and 3.14.5 with the pinned dependencies; other package platforms remain unverified. Ubuntu scanner CI is separate evidence, not Linux package validation.
- Approvals are recorded, not authenticated. Filesystem checks are point-in-time and do not stop a hostile process running as the same user.
- No hosted service, single sign-on, audit log export, encryption at rest or data residency controls are provided; use your platform's.
- Live provider handoffs, deployment and customer outcomes are outside the package's evidence.
- Commercial licence, distribution and support terms are unset. The [LICENSE](../LICENSE) reserves all rights; check it before business use.
