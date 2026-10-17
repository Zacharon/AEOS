---
name: aeos-independent-review
description: Use when acting as the independent (H3) verifier of another worker's AEOS result; never for reviewing your own work.
---

# Independent review (H3)

H1 and H2 are the worker's own checks. H3 is a review by a different role that did not do the work. If you produced the result, you cannot give it H3; say so and hand it on.

## Inputs

The task packet, the handoff bundle, the returned `worker_result.json`, its artifacts and the live sources. Read nothing outside the packet's allowed reads.

## Steps

1. Run `handoff.py review --bundle <bundle> --vault-root <vault>`. Stale or missing sources end the review at FAIL or PARTIAL; do not repair them yourself.
2. Compare what changed with the packet's allowed writes. Anything outside scope is a finding.
3. Re-run every acceptance check yourself. Do not trust pasted output.
4. Check each claim in the result against an artifact, a command output or a file. Unsupported claims are findings.
5. Confirm that nothing required owner approval that it did not get.

## Verdict

One of:

- **VERIFIED**: every acceptance check reproduced and every claim is backed.
- **PARTIAL**: some checks pass; list exactly what is missing or unproven.
- **FAIL**: a check fails, scope was exceeded, or sources are stale.

Write each finding as what you checked, what you expected and what you saw. A worker never sets `h3_verdict`; new handoffs start at `pending` or `needs-review` with `h3_verdict: null`. `blocked` is an execution state and `pending`, `needs-review` and `complete` are lifecycle states; none of them is a verdict. After three unsuccessful repair cycles, stop and escalate to the owner.

A VERIFIED verdict is not owner acceptance and is not permission to publish, merge or deploy.
