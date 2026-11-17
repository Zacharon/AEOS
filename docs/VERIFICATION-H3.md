# Verification and independent H3

H1 establishes mechanics: files, parsing, hashes, links, command results and changed scope. H2 assesses meaning: requirements, behavior, architecture, locks and consistency with authoritative facts. Workers may perform both. H3 independently challenges operational claims, including those checks, recovery, permissions and proposed writeback.

Use a different reviewer who did not implement or repair the result. Give that reviewer the approved scope, diff and reproducible evidence, with only the reads needed to test the claims. The reviewer remains read-only and preserves negative results. Required material reviews include security, money, authority, deployment, schema, release and closure claims; explicit task requirements also apply.

## Report the actual conclusion

| Verdict | Meaning |
|---|---|
| VERIFIED | Required claims and applicable acceptance checks are supported within the reported scope |
| PARTIAL | Evidence supports only part of the claim; identify each gap |
| FAIL | A requirement, boundary or check is contradicted |

When missing prerequisites prevent any supported verdict, leave verification pending or needing review and name the missing evidence. `blocked` describes execution, never an H3 verdict.

A report includes the requirement, inspected before-state, reason for the change, changed artifacts, exact checks and observed results, environment, preserved behavior, findings, limits, recovery and next decision. Use the [case](../templates/h3-case.md) and [report](../templates/verification-report.md) worksheets.

Repair only defects that have been reproduced and attributed. Count each targeted repair plus its rerun; stop after three unsuccessful cycles in total. Request independent re-review of a repaired candidate. A clean local scan establishes only its bounded scan result, and a local test establishes only its tested environment. Neither establishes hosted operation, owner acceptance or permission for external effects.
