# Public.4 release-readiness reconciliation

Reconciled 2026-10-14 after retrieving the original independent reviews and separate public.3 records. **Publication remains owner-gated.** Private source reports and operating history remain outside this repository. Historical verdicts are preserved rather than upgraded by the implementer.

## Exact candidate and baseline

- Main: `cacc52e87f4f7b7c1dbef9ab808dc2590393b48b`, merge of [PR #3](https://github.com/Zacharon/AEOS/pull/3).
- Repair head: `647d496ce6f98d95b06984e0ab0801e6ff4b1142`.
- Main, repair head and the corrected PR synthetic merge have tree `f042d4d10b329e6124ac1227bd4272bc39c439e3`. Tree equality transfers the inspected bytes, not independent acceptance.
- Version: `2026.10.12-public.4-candidate.1`.
- [Archive](../distribution/agentic-engineering-os-2026.10.12-public.4-candidate.1.zip): 95,878 bytes; 42 entries including the manifest; 41 manifest payloads.
- ZIP SHA-256: `ac884a1173a75e36e5f419abf6c788c502d86048223a8a4127b3faf5c75b6c56`.
- Manifest SHA-256: `72a98770d3ab014058bd6b636225b17ff41816c5be50cf431a756823b905e815`.
- [Adjacent digest record](../distribution/agentic-engineering-os-2026.10.12-public.4-candidate.1.sha256.json) and manifest both retain `UNPUBLISHED_REVIEW_CANDIDATE`.

Fresh inspection found exact archive/unpacked-payload agreement and matching digest/count metadata. Relative to public.2, only `FIRST_RUN.md`, `README.md` and `MANIFEST.json` differ. Runtime Python and the original tests are byte-identical. The root, public.2 and public.4 LICENSE bytes match; reserved rights, source credits and draft commercial terms remain intact.

Historical public.1/public.2 distribution and site/downloads ZIP copies remain byte-identical to each other and to main. Their hashes remain:

| Archive | SHA-256 |
| --- | --- |
| public.1 | `fd336a7623ff2b68e1b77f27e48194a86f782104826ca1f9ce45476900075fd8` |
| public.2 | `cd67157da17a1bbdd738fa185755fad398e9c314bb4b816fd28ee7827ff1f807` |

## Windows evidence

The first three completed runs below were read directly, including job logs. Each reports Windows Server 2025, CPython 3.14.5, the exact public.4 archive/manifest hashes, 86 unchanged regressions and seven distribution regressions without skips. PR #4's full log additionally confirms the primary setup-guide regression (94 total tests). The validator also requires fresh virtual-environment installation, extraction into a path with spaces, the documented PowerShell first run, continuation, historical failure reproduction, traversal/existing-output refusal, pending owner decision and no Gold application. A missing dependency or failed command fails validation.

| Run | Input | Result |
| --- | --- | --- |
| [Corrected push](https://github.com/Zacharon/AEOS/actions/runs/38292130154) | Repair head `647d496` | SUCCESS |
| [Corrected PR](https://github.com/Zacharon/AEOS/actions/runs/38292135105) | Head `647d496`; checkout synthetic merge `80ace7e` with the same tree | SUCCESS |
| [Merged main](https://github.com/Zacharon/AEOS/actions/runs/38349304161) | Main `cacc52e` | SUCCESS |
| [Readiness PR #4](https://github.com/Zacharon/AEOS/actions/runs/38499426095) | Head `9ed45cd`; 86 packaged tests plus eight repository regressions, no skips; fresh setup/demo/continuation and 90 links | SUCCESS |

The original [push failure](https://github.com/Zacharon/AEOS/actions/runs/38290656726) and [PR failure](https://github.com/Zacharon/AEOS/actions/runs/38290670060) at `65398bad` remain historical evidence. The corrected workflow canonicalizes runner-owned TEMP/TMP for the validation process; it does not weaken application path protection.

The earlier readiness pass used Linux/CPython 3.12.14, outside the intended Windows environment. Static payload, digest, link and preservation checks passed. Recompression with zlib 1.3.2 produced different ZIP bytes despite identical extracted payloads; `build_candidate.py --check` failed in that unsupported environment. This negative evidence remains historical. Deterministic rebuild evidence is bounded to the tested toolchain; no archive was regenerated or replaced.

The 2026-10-14 reconciliation ran the current `validate_candidate.py --receipt` procedure on native Windows CPython 3.14.5. It passed deterministic archive/manifest verification, fresh extraction/venv installation, actual documented PowerShell demo and continuation, 86 unchanged packaged tests plus eight repository regressions without skips, traversal/existing-output refusal and 90 links. The receipt retains pending owner decision, Gold unapplied and null demo H3. This is local mechanical evidence, separate from the independent reviewer and owner/publication gates.

## Independent review and public.3

[PR #3's retained record](https://github.com/Zacharon/AEOS/pull/3) reports independent read-only review at `647d496`, including reproduction of the TEMP mismatch, corrected child environment, unchanged parent environment and failure before continuation when RUNNER_TEMP is missing. The full original reports have now been retrieved and inspected. Historical **PARTIAL** verdicts at `65398bad` and `647d496` remain unchanged: hosted execution had not yet passed when those reviews were issued, and the proposed required check was not enforced.

A later independent read-only recheck issued **VERIFIED for candidate code merge readiness only**, at `647d496ce6f98d95b06984e0ab0801e6ff4b1142`, tree `f042d4d10b329e6124ac1227bd4272bc39c439e3`. That reviewer inspected successful push/PR logs, exact archive/manifest identities, fresh journey/continuation, unchanged boundaries and historical hashes. The original hosted-CI condition is satisfied. The recheck expressly treats required-check configuration as a separate owner hardening decision. It grants no enforcement, publication, deployment, installation or owner acceptance. Main has the same reviewed tree; this historical verdict does not automatically certify PR #4's additional readiness changes.

Public.3's separate archive, manifest, verification receipt and independent closeout report have also been retrieved. Its identity is `2026.10.09-public.3`, based on `0bf301cd3de28c9dedd2ff68e4459ccd22b6bb81`: ZIP SHA-256 `5fd48062e579e4f15c712e82b4abbf3592cac81566c7a1550102babca836d079`, manifest SHA-256 `81710bf2478a1ca8db6774a069d045b5fb9a8b00f8f9eac5f61d2708061ff2fe`, 97,714 bytes, 43 archive entries and 42 payloads. Its saved public verification receipt has SHA-256 `b3392c7cf4c754dfd16b99aff5c31cee35f0b7c285ad8243c3912f03287b1bc8`. Current archive and manifest hashes match the original records.

Public.3's independent verdict is **VERIFIED for bounded local maintenance closeout**, including tool-only qualification-log repair and saved-entry recovery. Its records distinguish inherited 91 new-package and 86 old-package results from 12 freshly rerun tooling tests; they do not claim a full post-repair pipeline replay or hosted CI. Those records explicitly leave owner attendance/acceptance unobserved and installation/publication separately gated. The synthetic demo's pending owner decision and null H3 field are separate from the independent closeout verdict. No later owner publication decision was established by the retrieved records; an unavailable read would not constitute revocation or failure.

Public.4 derives only from public.2. It does not incorporate, supersede or reset public.3's feature policy or acceptance history. Retrieval closes the previous access gap; selecting a publication lineage remains an explicit owner decision. Accepted private installed milestones remain separate and untouched.

A separate independent read-only review on 2026-10-14 issued **VERIFIED for bounded local readiness reconciliation and frozen candidate verification only**. It checked the original records, exact candidate archive/manifest, preserved historical files, native Windows receipt, final documentation/privacy/link checks and private factual writeback. This verdict is separate from historical reviews and does not grant owner acceptance, publication or verification of a future promotion diff or amended-head CI.

## Downloads and website state

At inspected main, README, site/index.html, site/first-run.html and site/verification.html all retain public.2 download links. Public.4 is absent from site/downloads. Two direct HTTPS GETs returned HTTP 200 and matching archive bytes:

| Repository-hosted resource | Observed bytes/hash |
| --- | --- |
| [Current public.2 download](https://raw.githubusercontent.com/Zacharon/AEOS/main/site/downloads/agentic-engineering-os-2026.10.09-public.2.zip) | 95,573 bytes; `cd67157d…1f807` |
| [Unpublished candidate resource](https://raw.githubusercontent.com/Zacharon/AEOS/main/distribution/agentic-engineering-os-2026.10.12-public.4-candidate.1.zip) | 95,878 bytes; `ac884a11…b6c56` |

Public reachability of a candidate file does not promote it. Repository metadata reports no homepage and `has_pages: false`; the public deployments API returned an empty list, and the Pages API returned 404. These observations do not rule out an external host. No canonical deployed website URL or provider/deployment identity was established, so an actual website and its served download remain **NOT VERIFIED**. No deployment is claimed.

The primary README previously instructed readers to follow public.2's bundled FIRST_RUN despite its known failing relative-output command. This readiness change directs readers to the corrected companion guide; the homepage identifies the historical download and the same guide. A regression follows the primary README guide link and compares its actual first-run commands with the candidate's verified instructions. Download names/URLs and frozen package contents are preserved.

## Precise remaining promotion gates

| Gate | Current state | Evidence/action needed |
| --- | --- | --- |
| Original independent review reconciliation | Retrieved; historical PARTIAL preserved; later independent VERIFIED for code merge readiness; current bounded local readiness independently VERIFIED | Hosted-CI condition closed by the later independent recheck. Any future promotion diff needs its applicable review; CI/implementer cannot supply H3. Amended-head hosted CI is distinct from the existing head's successful run. |
| Separate public.3 lineage/acceptance reconciliation | Exact archive, manifest, receipt and bounded local VERIFIED report retrieved | Preserve its completed local scope and unobserved owner-acceptance fields. Owner selects publication lineage explicitly; public.4 does not supersede public.3. |
| Owner publication decision | Not established by inspected records | Owner names exact version/hash, permitted distribution scope, website destination and rollback. PR #3 merge authorized integration, not publication; the readiness handoff authorizes no release action. |
| Required-check policy | No required status check configured | Current active [main ruleset](https://github.com/Zacharon/AEOS/rules/24798350) requires PRs, prevents deletion/force-push and resolves review threads; it has no required-status rule and requires zero approving reviews. An owner can separately require **Package validation (Windows CPython 3.14.5)**. This is a proposed owner control, not evidence that CI was enforced or a newly invented mandatory release prerequisite. |
| Versioned promotion PR | Not prepared as a download switch while blocked | After the decisions above, add a new versioned download and aligned README/homepage/first-run/evidence links. Preserve all historical paths, hashes, receipts and rights notices. Review and run Windows validation on the final diff. |
| Published website/download verification | NOT RUN; destination unknown | After authorized deployment, record final commit/deployment/URL; GET the actual primary download; check final URL, status, size, ZIP and manifest hashes and exact extracted file set; execute its extracted Windows setup and continuation. Preserve rollback to the existing public.2 link. |

Do not relabel the existing candidate by modifying its manifest or digest record in place. If an accepted release needs different embedded status/version or other payload bytes, build a new immutable version and repeat archive/manifest, Windows and independent review checks. Publication of unchanged reviewed candidate bytes, if explicitly selected by the owner, must retain their candidate labeling and use a separate version/hash-bound publication record.

No paid integrations, account changes, price, license grant or support commitment are part of this readiness task. The [existing package verification procedure](PACKAGE-CANDIDATE.md) remains the reproduction entry point. The next release decision is the owner's exact candidate/lineage, scope, destination and rollback authorization, after final readiness review. This reconciliation alone authorizes no download promotion or external release action.
