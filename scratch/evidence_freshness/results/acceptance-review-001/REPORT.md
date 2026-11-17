# Decision: resume the retained manual-return step

Reviewed public AEOS source **88e8aea5ddea99aebcc1212bf5bd5aaac68e8931**, the clean
worktree used to prepare the owner-directed manual-assistant acceptance attempt.
It is not current remote main, which is d94f23bec61c17500aa2bd8109e5f4ca9898fa42.
The source being reviewed and this older checkout storing the packet are separate.

**The selected claim is not supported: controller verification after a real
assistant return is explicitly unrun in the retained Windows 10 attempt.** Its
preparation and context-integrity checks succeeded. The worker was never launched
because the available delegation path could not bind to the prepared worktree.
No returned output, worker result, artifacts or verification receipt was found.
This is known nonexecution for this attempt, not an inference from an empty folder
alone, and not a claim that every target-machine check has never run.

The smallest next action is the documented **just-in-time context check before
resuming manual transport**, using the retained run and pinned controller source on
Windows 10. Do not rebuild the bundle or rerun every implementation suite merely
because an old document lists unfinished work.

Planned command only; NOT executed by this review. Resolve placeholders to the
already retained source, bundle and disposable worktree, not new copies:

```powershell
& <python-3.14.5> -B <source-checkout>/distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py check --bundle <retained-run>/bundle --vault-root <retained-run>/worktree
```

If that check passes, bind the manual assistant to that exact disposable worktree
and follow the existing manual-return instructions. If it fails, stop and reconcile
under the prototype's stop rule. Controller `verify` follows an actual return;
independent H3 and owner acceptance remain separate. This review does not dispatch
the worker or grant execution permission. The original acceptance task concerns a
real assistant executing the prototype's fixed synthetic task, not general issue
execution.

## Evidence that applies

The full ordinary table and source distinctions are in [EVIDENCE_TABLE.md](EVIDENCE_TABLE.md).
Important distinctions:

- Hosted Windows CI actually tested temporary merge **4ffac97d2162549012be92db7a883ab4490e21b1**,
  not the receipt's base f8b6258... or today's HEAD. Its complete tracked Git tree
  matches final PR head 507ea4d... and reviewed merge 88e8aea5.... The inspected job
  passed 27 prototype tests, 40 public.4 tests and the 42-file package check on
  **Windows Server 2025**, CPython 3.14.5. This is useful source-tree evidence,
  not target Windows 10 or exact-commit execution proof.
- Later Windows 10 preparation/context evidence supersedes a blanket reading of
  the older Windows-unverified list. It does not establish the full target-machine
  implementation checks. For those checks: **no retained evidence found; execution
  status unknown**. Seek an operator-retained exact-source execution log before
  deciding on a scoped rerun.
- The consolidation is merged and its final CI is successful, superseding old
  draft/pre-merge status and pending-final-CI statements. No applicable final H3
  or explicit owner integration acceptance was found in the bounded search.
  Merge itself does not satisfy the documented acceptance requirements.
- The source worktree, original rehearsal/recovery, checker, controller records
  and historical evidence were preserved. Runtime paths and raw local records
  remain local; this public-safe packet does not duplicate them.

## Existing checker: insufficient, with a format limitation

The ordinary table was written first. The same facts were then represented as a
current intended state and an explicitly partial record of known nonexecution.
No tested revision or environment was invented. Both dependency coverage fields
remain `unknown`. [REPRESENTATION.md](REPRESENTATION.md) explains the declarations,
omitted fields, authority scope and why this is not a historical execution receipt.

Actual unchanged checker text:

```text
Outcome: insufficient
- receipt.missing:environment,source_revision,specification_sha256
Synthetic applicability only; no acceptance or execution permission is granted.
```

Both text and JSON invocations exited **1**, the checker's normal non-eligible
result. No checker defect, acceptance-test failure or execution of the recorded
planned command is implied. Raw captured outputs are retained in
[checker.stdout.txt](checker.stdout.txt) and [checker.result.json](checker.result.json).

Commands ran from `scratch/evidence_freshness` using the observed CPython 3.14.5
interpreter on Windows 10 build 19045; the private executable location is omitted:

```text
python -I -B checker.py --root results/acceptance-review-001 --current current.json --receipt receipt.partial.json --format text
python -I -B checker.py --root results/acceptance-review-001 --current current.json --receipt receipt.partial.json --format json
```

The result's `allowed_by_synthetic_input` label is the existing checker's vocabulary
for a supplied condition. Here it applies only to reading evidence, not to worker
execution, acceptance, or authenticated authorization. The schema stops before it
can report the more useful known-unrun and unknown-coverage facts. **The extra
receipt discovered no additional consequential gap and gave a less clear explanation
than the ordinary evidence table.** It made the lack of tested provenance explicit,
but required extra annotation. Keep the ordinary table for this decision; no feature
change or larger comparison is justified by this one walkthrough.

## Effort and limits

Observed clock intervals: source reconstruction plus ordinary table, **602 seconds**;
partial-record preparation plus checker calls, **82 seconds**. These are wall-clock
phases including tool waits, reading, reasoning and writing, not active human
minutes. Reporting/preservation work followed. Active operator preparation, active
reviewer effort, setup/maintenance labor and time savings are **unknown**. The
existing pilot template remains blank. Familiarity and sequential presentation
prevent a time-saving inference. [results.json](results.json) preserves the timing
boundaries, commands and outputs. A packet-output capture initially hit a shell
quoting SyntaxError before writing; the stdin-based retry succeeded. This was not
an acceptance execution and did not modify prior evidence.

Only the freshness checker and read-only evidence/provenance inspection ran.
No issue-handoff acceptance commands, tests, synthetic workers, real workers,
integration, new branches, installs, H3 review, merge, push or publication ran.
The requested restraint was followed; no approval denial blocked this review.
The earlier worker-binding limitation belongs to the retained acceptance attempt.

Missing records remain uncertain outside the inspected evidence locations. The
research experiment's Windows runs concern a different program and supply no
issue-handoff acceptance proof. This packet establishes an evidence-backed next
action for the chosen source, not acceptance or productivity improvement.
