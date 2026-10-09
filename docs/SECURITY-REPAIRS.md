# Public.2 integrity repair candidate

This revision repairs six local integrity/recovery findings reported against runtime commit `8f997ef5c73b09a04124e0d13067d7adb6c468dc`. Root ownership notice commit `cedcb0ea968f8d1f49c546b43f91d2ad1a5dc391` is preserved, and the new package includes the exact root LICENSE. The rights position is unchanged.

The public.1 directory, both ZIP copies and its verification receipt are frozen historical artifacts. Public.2 is a new candidate revision, not replacement bytes or retrospective verification of public.1. Existing public.1 downloads retain the reported defects.

| Finding | Candidate change | Regression evidence required |
|---|---|---|
| AEOS-SEC-01: aliases reach protected/outside paths | Check lexical ancestors and Windows reparse entries, hardlinks, storage trees, artifact/control paths and destinations. Use exclusive owned staging files. | Protected target, temporary path, Bronze/Silver/control/backup aliases refuse without unintended writes; native junction cases. |
| AEOS-SEC-02: unchecked rollback backup | Require exact proposal backup path, ordinary identity and recorded original hash before successful dry-run or mutation; stage restoration atomically. | Missing, altered and aliased backups refuse while Gold and prior evidence remain unchanged; valid update/rollback still works. |
| AEOS-SEC-03: incomplete saved comparison | Compare complete UTF-8 text including line-ending/EOF changes; clip only the displayed preview. Hash the full artifact inside verification. | Changed tail beyond 12,000 characters appears in the full artifact; newline-only changes are visible; diff tampering invalidates verification. |
| AEOS-SEC-04: unmanifested directory links | Validate every extracted tree entry and its ancestors, exact directory/file sets and regular identities before demo copying. | Extra directory aliases and unexpected directories refuse; failed package validation creates no demo output. |
| AEOS-SEC-05: optimized execution skips checks | Replace runtime enforcement assertions with explicit conditional failures in checker and demo. | Invalid bytes, unsafe paths and extra entries fail under normal Python, `-O` and `PYTHONOPTIMIZE=1`. |
| AEOS-SEC-06: ignored evidence absent from checkpoint | Match required proposal, source registry/source bytes, payload, full diff, ledger and applicable target/backup against regular Git HEAD blobs. | Ignored/missing/changed required artifacts refuse even with clean ordinary status; no automatic staging. |

## Use and compatibility

Verification fingerprints now bind the full diff. Older pending proposals require renewed verification; approved records require a fresh superseding proposal and a new owner decision before applying. This change never reapproves them automatically. Preserve prior records and inspect the new review. Do not edit hashes or historical decisions to bypass drift. Already-applied legacy proposals can fail the new verification check during rollback; preserve their backups and obtain a separate, explicitly reviewed recovery plan rather than changing their lifecycle fields. This repair does not migrate those records or authorize recovery writes.

A clean Git status alone is insufficient. Required checkpoint bytes must equal the working evidence; line-ending conversion or filters can prevent that. Use a deliberate byte-preserving policy for governed evidence and inspect the actual checkpoint. The scripts never stage the whole vault or change global Git settings.

The preview remains manually invoked. Source text is untrusted evidence; workers cannot approve knowledge or issue their own independent H3. Apply/rollback regressions use disposable synthetic repositories, not an operating vault. The deterministic demo stops at pending Silver.

Independent candidate review also reproduced two missed public cases: an ignored ledger was absent from HEAD but apply succeeded, and unregistered leftover Bronze/Silver files could be overwritten after an interrupted capture. The candidate now checkpoints the ledger and exclusively creates intake/payload files. Separate regressions check refused dry-run/apply and preservation of those leftover bytes. The negative review evidence was retained; the initial candidate archive was rebuilt before publication.

## Verification record

The current [public.2 receipt](../site/verification-public.2.json) records the final archive/manifest hashes, exact environment, freshly run suites, clean extraction and demonstration, bounded privacy checks and independent review. Detailed tests are shipped in the new package. Do not inherit prior Windows/browser results as newly executed checks.

These guards are point-in-time local integrity checks, not hostile same-user confinement or authenticated approval. Filesystem races, power-loss durability, Linux/macOS execution, live provider handoffs, deployment, customer outcomes, exhaustive credential detection and dependency source auditing are outside this repair's evidence. No compromise of a personal vault is inferred from the synthetic failures. Private operating context is not included in this repository or its report.

Public changes are submitted for review through a feature branch/PR. This document does not authorize merging, deployment, a paid release or new commercial-use rights.
