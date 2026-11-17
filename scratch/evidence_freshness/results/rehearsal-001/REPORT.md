# One executed evidence-freshness rehearsal

**Result: unchanged evidence was eligible; the preserved receipt became stale
after one requirement changed.** The original check actually executed once on
synthetic input. The checker, prior fixtures and prior results were not changed.
This is an isolated replay, not an actual product handoff or a usability study.

## What ran

The small executable [count_items.py](count_items.py) counts all supplied items.
[inputs/items.json](inputs/items.json) contains three items, two active and one
inactive. [check_count.py](check_count.py) launches that executable and compares
its output with a manually selected expected count.

The first [requirement](requirements-v1.txt) says to count all items. The check
really ran and returned count 3. Its output and exit code were captured before
the current-state record and receipt were assembled. The existing checker then
assessed [current-before.json](current-before.json) and [receipt.json](receipt.json).

Only after that eligible decision, a new [requirement](requirements-v2.txt) was
written: count active items only, so this same input should yield 2. The new
[current-after.json](current-after.json) changes exactly `requirement_revision`
and `specification`, both representing this single requirement change. Source,
inputs, runtime, check command, action authority, receipt and prior output stay
unchanged. The old check command deliberately remains visible as historical
coverage; its expected value must be revised before testing the new requirement.

## Commands and actual output

Working directory for every command: this rehearsal directory. `<interpreter>`
denotes the existing **CPython 3.14.5** executable, observed on **Windows
10.0.19045, AMD64**. The public records omit the personal installation path.
Its observed binary digest and runtime details are in [environment.json](environment.json).
`-I -B` disables Python environment/user-site injection and bytecode writes;
it does not provide an operating-system sandbox.

The capture driver was invoked as:

```text
<interpreter> -I -B rehearse.py
```

It executed this check, exit **0**, with empty stderr:

```text
<interpreter> -I -B check_count.py --expected 3
```

Actual [check stdout](check.stdout.txt):

```text
Command: <interpreter> -I -B count_items.py inputs/items.json
Source stdout: {"count": 3}
Source exit: 0
PASS expected=3 actual=3
```

Before, exit **0**, with empty stderr:

```text
<interpreter> -I -B ../../checker.py --root . --receipt receipt.json --format text --current current-before.json

Outcome: eligible
- applicability_rules_satisfied_only
Synthetic applicability only; no acceptance or execution permission is granted.
```

After, exit **1**, with empty stderr:

```text
<interpreter> -I -B ../../checker.py --root . --receipt receipt.json --format text --current current-after.json

Outcome: stale
- requirement_revision_changed
- specification_bytes_changed
Synthetic applicability only; no acceptance or execution permission is granted.
```

Exit 1 is the checker's expected stale/refusal result, not a failed rehearsal.
Unmodified stdout/stderr bytes, command arguments, working directory, start time,
exit status, elapsed duration and output digests are retained in the three
execution records: [check](check.execution.json), [before](before.execution.json)
and [after](after.execution.json). The top-level driver exited 0. There was one
behavior-check execution, two freshness assessments, and no retries.

## Observed facts versus supplied facts

**Observed:** subprocess return codes and stdout/stderr; actual interpreter and
OS identifiers; interpreter binary digest; hashes of source, input, specification
and output bytes; checker text; unchanged historical receipt/output/source after
the requirement revision. The source identifier is a digest of the two replay
source-file hashes, not a Git commit. [source-manifest.json](source-manifest.json)
documents the exact snapshot algorithm. `exact-source-v1` is unchanged.

**Manually supplied:** what the requirement should mean, the expected values 3
and 2, task/claim/check IDs, revision labels, which files count as dependencies,
the scoped `complete` coverage declaration, allowed local-review authority,
pending owner acceptance and absence of other required checks. These are explicit
replay choices, not conclusions authenticated by the checker. Actual user
authorization covers this local rehearsal; the record's `allowed` string does
not independently prove that authorization.

Dependency completeness was assessed by reading the two tiny scripts: the check
launches the source executable; the executable reads the one declared input.
Those three file inputs are hashed. Specification is bound separately. Runtime
and flags are recorded as environment. This is a bounded declaration for this
replay, not automatic dependency discovery or an exhaustive hash of the OS,
standard library and every ambient execution dependency. A real handoff with
uncertain coverage should use `unknown`, which prevents optimistic reuse.

## Preparation effort and practical friction

Preparation required authoring two small executable/check scripts, one three-item
input, the initial requirement and a fixed capture driver. The driver captures
the observed fields and fills the existing JSON format; it is not a new checker
feature or installed integration. Manual work still included choosing the oracle,
identifying dependencies, defining the claim/revision boundary and deciding what
authority and acceptance states to supply.

Automated record assembly took **0.0039708 seconds** in this run. That narrow
measurement includes constructing and writing the initial current/receipt JSON
only; it excludes design, instruction reads, authoring, command execution,
review and maintenance. The real check took **1.5687 seconds**, and the two
checker processes took **0.5399** and **0.6048 seconds**. These are process elapsed
times, not operator/reviewer effort or savings.

Total preparation time and active human operator/reviewer minutes were **not
measured** and remain null in [result.json](result.json). No participant data was
added to the blank pilot log. There is no defensible total-cost or productivity
conclusion from these timings.

The existing text explains *which binding changed*, but does not display the new
expected behavior or suggest a replacement command. A reviewer has to read the
requirement files to know that 2 is now expected. This is a concrete limitation
observed without changing the interface; human comprehension remains untested.

## Verification and next check

The driver's preservation check confirmed that the receipt, initial current
record, original requirement, raw check output, command record, source and input
retained their hashes. The existing checker hash still matches the original
tested baseline. The final scope audit compares all 285 pre-existing tracked or
visible untracked files and checks that additions are confined to this new
rehearsal directory. No vault, product, package or live handoff files were edited.

This establishes that real execution observations can populate the existing
format, and that a requirement-only revision makes the old evidence stale. It
does not establish correct updated behavior, authenticated execution, complete
real-world dependencies, owner acceptance, independent H3, or useful/cheap real
handoffs. Existing baseline tests were read as historical evidence; broad package
tests were not rerun for this unchanged-checker replay.

The next behavior check a reviewer needs is:

```text
<interpreter> -I -B check_count.py --expected 2
```

That command is **NOT RUN** in this rehearsal. Based on the unchanged source
which counts all items, it is expected to report 3 and fail the new expectation;
this is a prediction, not an observed result. Capture that future check in a new
evidence location, then decide whether to change the implementation. Do not
overwrite this receipt or relabel its original pass as support for the new intent.

Owner review of the explanation remains the next decision. No interface change,
integration, six-case comparison or human study was started.
