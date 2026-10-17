# Adopting AEOS in a small business or enterprise team

This guide is for a team that wants to run AEOS on real business work and real data. It describes what the current source preview already does, how to use it with any assistant, which protections exist and where your team has to add its own. It changes nothing in the package; every command below is the shipped one.

Results vary with your assistant, data and environment. Windows with CPython 3.14.5 is the only tested platform. Everything else listed as unverified below is exactly that.

## Plug-and-play setup for a team

1. Extract the package into a new folder and run its first run exactly as [FIRST_RUN.md](../distribution/agentic-engineering-os-2026.10.12-public.4-candidate.1/FIRST_RUN.md) shows. It makes no network or model calls once dependencies are installed.
2. Create your team vault from the package `vault/` templates in a separate, backed-up location under version control. Never point AEOS at a folder that also holds credentials, synced personal files or browser data.
3. Decide who holds each role in [Roles and permissions](#roles-and-permissions) and write it in the vault's `AGENTS.md`.
4. Agree your data labels using the [data-handling skill](../.agent/skills/aeos-data-handling/SKILL.md) before the first real packet.
5. Run one low-risk task end to end (packet, bundle, check, result, review) before relying on it.

Upgrades follow the package README: extract each new version beside the old one, verify it, and copy only chosen tools into your vault after a backup. Nothing is installed as a service, so nothing needs uninstalling.

## Using any model or assistant

AEOS never calls a model. It prepares a bounded bundle of files, and you give that bundle to whichever assistant your organization allows: a hosted chat assistant, a coding agent, a self-hosted or local model, or a person.

- **Any assistant:** build the packet with `--worker-tool Human` and the bundle with `--executor human`. A person carries the bundle to the approved assistant and brings back `worker_result.json`. This works with every model because the handoff is files, not an API.
- **Named presets:** `codex`, `grok-build`, `grok-fleet` and `hermes` exist as packaging presets. They are labels for the manual handoff, not integrations, and are not required.
- **Instructions for assistants:** this repository keeps one canonical [AGENTS.md](../AGENTS.md) and tool-neutral skills in [.agent/](../.agent/README.md). `CLAUDE.md` and `GEMINI.md` only point to `AGENTS.md`, so tools that look for those names read the same rules. Add the same one-line pointer for any other tool rather than copying text.

Switching models does not change the packet, the checks or the evidence. Re-run `handoff.py check` before giving a saved bundle to a different assistant.

## Protections already in the package

These are implemented and covered by the package's regression tests:

- **Bounded context.** A bundle carries one to eight selected files, each inside the packet's allowed reads, with hashes. `check` refuses changed or missing sources.
- **Secret refusal (backstop).** The packet and handoff tools refuse secret-like paths (`.env`, `.ssh`, `.aws`, `.azure`, `.gnupg`, names containing secret, credential, password, token, private) and common secret assignments in file contents.
- **Path safety.** Parent traversal, symlinks, Windows junctions and hardlinks are refused for Librarian inputs, stores, targets and backups. Outputs refuse to overwrite existing evidence.
- **Untrusted sources.** Source and snapshot text is labelled as data, never instructions.
- **Approval separation.** Agents cannot set owner-decision fields, issue their own independent review or promote knowledge to Gold. Gold changes require an owner decision checkpointed in Git, a dry run and exact evidence hashes; rollback requires a verified backup.
- **No background activity.** No scheduler, service, account, registry change, network listener or credential configuration is installed.

This repository adds a cross-platform [boundary scan](../scripts/check_public_boundary.py) that CI runs on every pull request. It checks every tracked file and every ZIP member for credential markers, private user paths and secret-bearing file names. Teams can run it on their own repositories as a pre-commit or CI step: `python3 -B scripts/check_public_boundary.py` exits non-zero on any finding. It is a bounded pattern scan, not a replacement for your organization's secret scanning.

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
- Never automate owner decisions, independent review or Gold application. `verify`, `check` and `complete` are mechanical evidence only.
- Stop after three failed repair cycles and hand the task back to a person.

## Datasets and business records

Bundles hold at most eight files and the Librarian refuses files over 2 MiB, so datasets do not travel inside AEOS. Pass a data dictionary and the question instead, let the assistant work in its own approved environment, and bring back results and evidence. Details are in the [data-handling skill](../.agent/skills/aeos-data-handling/SKILL.md).

## Known limits

- Tested only on Windows with CPython 3.14.5, PyYAML 6.0.3 and jsonschema 4.26.0. Linux and macOS are unverified.
- Approvals are recorded, not authenticated. Filesystem checks are point-in-time and do not stop a hostile process running as the same user.
- No hosted service, single sign-on, audit log export, encryption at rest or data residency controls are provided; use your platform's.
- Live provider handoffs, deployment and customer outcomes are outside the package's evidence.
- Commercial licence, distribution and support terms are unset. The [LICENSE](../LICENSE) reserves all rights; check it before business use.
