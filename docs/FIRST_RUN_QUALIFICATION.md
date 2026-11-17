# Public.3 first-run qualification candidate

The public.2 instructions supplied a literal parent-traversal output path that the package correctly refused. Its generated continuation also used bare Python, so a fresh shell could miss the installed prerequisites. Public.3 keeps the path protections and resolves a new sibling output to an absolute path, explicitly invokes the same virtual-environment interpreter, and records quoted absolute paths in local START_HERE.md. Space-containing sibling names are part of the qualification.

The shared command block in `tools/first_run_commands.ps1` is rendered verbatim into FIRST_RUN.md, both architecture guides and the website first-run page. The demo makes local deterministic calls only; source knowledge stays pending, owner decisions are unchanged, no Gold target is written and no model or independent reviewer is simulated.

## Reproduce locally

On Windows PowerShell with installed CPython 3.14.5, from the repository root, choose a new absent directory outside the payload:

```powershell
& ./tools/qualify_public.ps1 -WorkRoot ([IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $PWD.Path) 'AEOS qualification')))
```

The command builds only the frozen public.2 allowlist plus reviewed public overlays, checks the entire ZIP member set and every byte before extraction, creates a fresh environment, installs the documented pinned prerequisites, runs the same guide block, executes both package revisions' regression suites, reproduces the old literal-path refusal and runs generated continuation in a new PowerShell process without activation. Raw logs, environments and generated machine paths stay outside the release payload. The builder refuses conflicting files; an explicit `--refresh` may update only a fully byte-verified public.3 candidate and its exact matching archive copies. It never changes old versions.

## Evidence and limits

See [the public-safe receipt](../site/verification-public.3.json) for the final archive identity and actual local counts. The reported local evidence contains 91 historically captured new-package cases, 86 historically captured public.2 cases and 12 current builder/tool cases rerun after the tool-only repair: 189 test case executions across the reported versions/suites, zero skips. The unchanged package suites were not replayed after that repair. The final ZIP was extracted into a fresh path with spaces; a new sibling virtual environment installed the documented requirements, the exact shared startup commands passed, and generated continuation passed in a new PowerShell process without activation. Stale/missing context refused; original source bytes were restored. Checks also passed under -O and PYTHONOPTIMIZE=1. Public.1/public.2 folders, archives, receipts and the root LICENSE are frozen.

The GitHub Actions definition uses Windows PowerShell, CPython 3.14.5, read-only contents permission, pinned checkout/setup actions and a 20-minute timeout. No hosted CI run, push, deployment, release, provider credential, upload or self-hosted runner is authorized or claimed. Linux/macOS are not defined or run. Action tag SHAs were checked directly in the official [checkout repository](https://github.com/actions/checkout/tree/11bd71901bbe5b1630ceea73d27597364c9af683) and [setup-python repository](https://github.com/actions/setup-python/tree/a26af69be951a213d495a4c3e4e4022e16d87065).

Independent H3 review is not included in this worker qualification receipt and is required separately. Owner acceptance remains separate. This remains a public source preview. Pricing, commercial rights and support terms are unchanged.

## Exact candidate identity

- Version: `2026.10.09-public.3`
- Archive SHA-256: `5fd48062e579e4f15c712e82b4abbf3592cac81566c7a1550102babca836d079`
- Manifest SHA-256: `81710bf2478a1ca8db6774a069d045b5fb9a8b00f8f9eac5f61d2708061ff2fe`
- Archive: 97,714 bytes; 43 files, 42 payload manifest entries; distribution and site/downloads copies identical.
- 86 frozen old assets rehashed unchanged, including both historical release folders, all old archive copies, both historical receipts and the root LICENSE.
- Desktop (1365 × 900) and mobile (390 × 844) browser checks covered the first-run and architecture pages. Body widths matched viewports; long commands scrolled inside their code blocks. These are local in-app browser captures, not physical-device evidence.

Raw first-attempt outputs remain local historical evidence. During preparation, earlier extractions ceased to match a revised candidate ZIP; their final exact-byte gate correctly refused them. Only the final immutable ZIP qualification is counted here. The current runtime safeguards are explicit conditional failures and remain enforced under optimized Python. Mechanical H1/H2 evidence is recorded here; independent H3 is required separately and is not included in this worker qualification receipt.

The final immutable ZIP package suite logs were retained after a tooling overlay link-base failure. After that surface-only correction, the builder/surface suite was rerun with a regression that accepts generated-destination links and still refuses a genuinely missing target. Final integrity, continuation, links and privacy were rerun; unchanged package suites were not claimed as rerun after the repair. Shared literal startup passed both PowerShell 7.6.5 and, separately, Windows PowerShell 5.1.19041.7725 in new disposable extractions/environments.

## Tool-only retained-log repair

A later tool review reproduced that saved OK summaries could substitute for actual command execution without binding archive, source, interpreter, dependencies and prior run identity. The reusable resume option and all retained-log code have been removed. The public qualifier requires fresh step evidence, executes every command, rejects prior qualification logs/receipts before running commands and creates new step logs exclusively. A new regression supplies an unrelated OK log and stale receipt, checks CLI rejection and verifies direct qualification refusal before subprocess execution while preserving both files.

After this tool-only repair, the 12-case builder/tool suite was freshly rerun with zero skips. The 91 new-package and 86 public.2 package cases remain captured historical evidence for the unchanged final ZIP; no full pipeline or unchanged package suites are claimed as replayed. The earlier 11-case builder/surface rerun followed the overlay link-context repair and was not a pre-link-failure result. This one-off external evidence retention is an honest historical record, not a reusable public qualification feature. The current tool/source identities are pinned in the public receipt. Archive/copy/old-asset integrity, current metadata, logical links and privacy were rechecked. Independent H3 remains separate from this worker receipt.
