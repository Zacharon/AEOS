# Public.4 release-readiness reconciliation

Checked 2026-10-14 UTC (2026-10-13 in America/New_York). **Publication remains blocked.** This record reconciles the public repository and available Windows CI evidence; it does not grant release authorization or upgrade independent H3.

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

The three completed runs below were read directly, including job logs. Each reports Windows Server 2025, CPython 3.14.5, the exact public.4 archive/manifest hashes, 86 unchanged regressions and seven distribution regressions without skips. The validator also requires fresh virtual-environment installation, extraction into a path with spaces, the documented PowerShell first run, continuation, historical failure reproduction, traversal/existing-output refusal, pending owner decision and no Gold application. A missing dependency or failed command fails validation.

| Run | Input | Result |
| --- | --- | --- |
| [Corrected push](https://github.com/Zacharon/AEOS/actions/runs/38292130154) | Repair head `647d496` | SUCCESS |
| [Corrected PR](https://github.com/Zacharon/AEOS/actions/runs/38292135105) | Head `647d496`; checkout synthetic merge `80ace7e` with the same tree | SUCCESS |
| [Merged main](https://github.com/Zacharon/AEOS/actions/runs/38349304161) | Main `cacc52e` | SUCCESS |

The original [push failure](https://github.com/Zacharon/AEOS/actions/runs/38290656726) and [PR failure](https://github.com/Zacharon/AEOS/actions/runs/38290670060) at `65398bad` remain historical evidence. The corrected workflow canonicalizes runner-owned TEMP/TMP for the validation process; it does not weaken application path protection.

This pass's local environment is Linux/CPython 3.12.14, not the intended Windows environment. Static payload, digest, link and preservation checks passed. Recompression here with zlib 1.3.2 produced different ZIP bytes despite identical extracted payloads; `build_candidate.py --check` therefore failed in this unsupported environment. Deterministic rebuild evidence is bounded to the tested toolchain. No archive was regenerated or replaced, and no Windows execution is claimed for this local pass.

## Independent review and public.3

[PR #3's retained record](https://github.com/Zacharon/AEOS/pull/3) reports independent read-only review at `647d496`, including reproduction of the TEMP mismatch, corrected child environment, unchanged parent environment and failure before continuation when RUNNER_TEMP is missing. Its verdict remains **PARTIAL**, recorded before hosted completion. GitHub currently returns no review submissions or discussion comments for that PR. The original full independent report is not present in main or the accessible checkout; this reconciliation cannot determine all original review conditions or close them on the reviewer's behalf.

[PACKAGE-CANDIDATE.md](PACKAGE-CANDIDATE.md) documents a separate public.3 candidate outside main. The advertised branch heads and PRs do not expose its archive or acceptance record. Its exact version, archive path/hash and accepted/authorized/installed/published states remain **not retrieved**, rather than failed or revoked. Public.4 derives only from public.2; it does not incorporate, supersede or reset public.3's feature policy or acceptance history. Reconcile the original public.3 record before selecting a promotion lineage. Private installed milestones remain separate and untouched.

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
| Original independent report and completed H3 | PARTIAL; full report not retrieved | Obtain the original report; independent reviewer reconciles the successful hosted/main evidence against its conditions and records a verdict tied to exact archive/manifest hashes and final promotion diff. Implementer/CI cannot supply that verdict. |
| Separate public.3 lineage/acceptance reconciliation | Documented, original record not retrieved | Retrieve its version, archive/hash and owner/acceptance record. Preserve completed states and decide explicitly which candidate is being promoted. |
| Owner publication decision | Not recorded for public.4 | Owner names exact version/hash, permitted distribution scope, website destination and rollback. PR #3 merge authorized integration, not publication. |
| Required-check policy | No required status check configured | Current active [main ruleset](https://github.com/Zacharon/AEOS/rules/24798350) requires PRs, prevents deletion/force-push and resolves review threads; it has no required-status rule and requires zero approving reviews. An owner can separately require **Package validation (Windows CPython 3.14.5)**. This is a proposed owner control, not evidence that CI was enforced or a newly invented mandatory release prerequisite. |
| Versioned promotion PR | Not prepared as a download switch while blocked | After the decisions above, add a new versioned download and aligned README/homepage/first-run/evidence links. Preserve all historical paths, hashes, receipts and rights notices. Review and run Windows validation on the final diff. |
| Published website/download verification | NOT RUN; destination unknown | After authorized deployment, record final commit/deployment/URL; GET the actual primary download; check final URL, status, size, ZIP and manifest hashes and exact extracted file set; execute its extracted Windows setup and continuation. Preserve rollback to the existing public.2 link. |

Do not relabel the existing candidate by modifying its manifest or digest record in place. If an accepted release needs different embedded status/version or other payload bytes, build a new immutable version and repeat archive/manifest, Windows and independent review checks. Publication of unchanged reviewed candidate bytes, if explicitly selected by the owner, must retain their candidate labeling and use a separate version/hash-bound publication record.

No paid integrations, account changes, price, license grant or support commitment are part of this readiness task. The [existing package verification procedure](PACKAGE-CANDIDATE.md) remains the reproduction entry point. The smallest next step is to retrieve the original independent report and public.3 record for exact reconciliation; publication is not the next authorized action while those evidence and owner gates remain open.
