# Faithful partial representation

The ordinary table was completed first. Its selected claim is the prepared manual
attempt's controller verification on target Windows 10, which is explicitly unrun
in that retained attempt. This is narrower than all target-machine implementation
checks, whose execution status is unknown where no retained evidence was found.

`current.json` describes the intended source and target environment. Task/claim/
requirement/check identifiers and the specification summary are manually supplied
audit labels. The command is the documented planned command with neutral location
placeholders, not a command observed running. The only allowed action in this input
is evidence review. It does not represent current worker or integration permission.

`receipt.partial.json` is an audit-created partial record of known nonexecution,
not a recovered historical receipt and not a claim that a verification ran. It omits
`source_revision`, `environment` and `specification_sha256`: no completed verification
observed those values. Substituting today's HEAD, the intended source, a prepared
environment, or the new summary's digest would falsely turn intention into tested
provenance. The existing format has no nullable tested-source field. No invented
fields or sentinel revisions are used. The expected schema response is insufficient.

Both dependency mappings are empty because this audit has not established the full
dependency set. Both coverage fields are explicitly unknown, not complete. Four
matching source hashes and even a complete tracked Git tree do not resolve unknown
runtime, configuration or untracked dependencies.

The checker validates all required schema fields before inspecting the execution
and dependency fields. Therefore a missing-field result cannot also explain the
more useful known-unrun reason; those facts remain visible in the ordinary table.
The trust boundary stays unchanged: supplied records are not authenticated, hashes
prove byte identity only, and eligibility would not grant H3 or owner acceptance.

The partial record is deliberate. A fully faithful, schema-complete historical
execution receipt cannot be produced for a verification that did not occur. This
walkthrough records the format limitation instead of modifying the checker.
