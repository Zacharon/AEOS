# Worker input and return contract

This guide describes the existing public.4 validators, not a new result schema.
The approved task packet remains v1.2; the handoff manifest and worker result
remain v1.0. A status label is not authenticated approval. The controller supplies
the repository, branch, baseline, exact reads/writes, acceptance checks, artifact
names and this guide before dispatch. Stop if any required input is absent.

## Worker result v1.0

Use the generated `worker_result.template.json`. Its exact top-level keys are
`schema_version`, `run_id`, `task_id`, `worker`, `execution_state`, `summary`,
`artifacts`, `changed_paths`, `checks`, `risks`, `proposed_writeback`, `next_action`.
Keep `schema_version` equal to `"1.0"` and preserve the template identities.
Execution state is `ready_for_review`, `blocked`, `failed` or `cancelled`.

- Artifact: exactly `path`, `sha256`, `description`. Paths are unique ignoring
  case and start with `artifacts/`. SHA-256 is 64 lowercase hexadecimal digits
  matching the saved file bytes.
- Check: exactly `name`, `command`, `outcome`, `evidence`. Outcome is `passed`,
  `failed`, `blocked` or `not_run`. Evidence names a declared artifact; only a
  `not_run` check may have null evidence. Record unrun checks explicitly.
- Proposed writeback: exactly `target`, `artifact`, `rationale`. The target
  must be authorized in Allowed Writes and the artifact must be declared.
  This is a proposal, never an applied state change or approval.
- Changed paths are unique, root-relative paths within Allowed Writes.
  All five list fields have at most 100 items. A ready return needs at least one
  check and artifact. Summary, next action, risks, descriptions, check names and
  commands, and writeback rationale are nonempty strings without `REPLACE:`.

Unknown fields and duplicate JSON keys are rejected. Result JSON is limited to
128 KiB, artifacts to 8 MiB each. Use UTF-8. Do not add an H3, approval, completion
or owner-acceptance field to a worker result.

## Rationale coverage

The controller captures task-start bytes using frozen public.4
`code_rationale.py snapshot` and retains the baseline SHA-256 outside worker
writes. Do not regenerate that baseline to make a check pass. Obtain the current
change digest with `code_rationale.py changes` using that baseline and digest.

The report has exactly one fenced `code-rationale` JSON object with exactly
`task_id`, `baseline_sha256`, `changes_sha256`, `entries`.
Each entry has exactly `paths`, `disposition`, `why`, `where_to_edit`,
`constraints`, `verification`, `references`.

- `paths` is a nonempty list. All entries together cover every actual changed
  path exactly once: additions, modifications and deletions, including ignored
  and untracked paths inside the frozen scope. A rename covers both paths.
- `disposition` is `documented` or `documentation-not-needed`. The latter needs
  a concrete reason in `why`, tied to this change rather than a blanket waiver.
- `why`, `where_to_edit`, `constraints`, and `verification` are nonempty strings
  without `REPLACE:`. Explain decisions and constraints rather than syntax.
- `references` is a list of exact objects with `path`, `sha256`, `contains`.
  A documented entry requires a reference. Its relative file path must exist,
  its SHA-256 must match current bytes, and `contains` must be a nonempty current
  heading or symbol substring. Include every durable reference used as evidence.

The task ID and baseline digest must match the controller baseline. The changes
digest hashes the actual delta serialized by `handoff.json_bytes`: sorted keys,
two-space indentation, unescaped Unicode, trailing newline, UTF-8. Prefer the
validator's output to reimplementing this calculation.

The report lives outside the frozen editing scope and is declared as a hashed
result artifact. For `handoff.py complete`, frozen scopes equal all packet
Allowed Writes and declared changed paths equal actual rationale-covered paths.
Missing fields, stale references, incomplete coverage and changed control files
reject completion. Do not update a hash to conceal missing re-verification.

## Documentation delta and delivery

Use the task report to state changed behavior, affected authoritative documents,
captured checks and remaining unknowns. An impact mapping identifies review
needs; it does not establish semantic truth. A controller compares explanations
against the actual diff and reruns applicable checks before writing current state.

Follow the target's contribution rules, issue and related-work context, AI policy,
title and test requirements. Prepare a local PR body from the verified diff:
problem, resulting behavior, checks actually run, failures/unrun checks, material
limits and public-safe evidence links. Keep private paths and evidence out of it.
Opening a PR, publishing, merging and deploying require their own authorization.

Structural completion and rationale coverage do not prove execution or explanation
quality. Independent H3 and owner acceptance remain separate. Context exclusion
is not a filesystem sandbox. Paths retain the frozen validators' traversal,
symlink/junction, hardlink, private-name and size restrictions.

## Runtime authorities

- [Result and bundle validator](../../distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py)
- [Rationale validator](../../distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/code_rationale.py)
- [Frozen rationale rule](../../distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/CODE_RATIONALE.md)
