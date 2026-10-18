---
name: aeos-repo-maintenance
description: Use when changing this public AEOS repository itself (docs, site, scripts, distribution); covers the public boundary, validation and owner-only decisions.
---

# Maintain this repository

This repository is a public source preview of reusable code, neutral templates, a synthetic sample and public-safe evidence. It is separate from anyone's personal operating vault. Read [AGENTS.md](../../../AGENTS.md) first; it wins over this file.

## Boundary

- Never add personal vault documents, project state, run history, private paths, account identifiers, credentials or browser/system data. When in doubt, leave it out and ask.
- Only `site/` is the website publication root. Site pages must not link outside it.
- Preserve the distinctions between synthetic, manual, verified and unverified claims. Do not describe features the package does not ship.

## Owner-only decisions

Do not make or imply any of these; open them as questions for the owner:

- publishing a release, archive or website deployment,
- promoting the unpublished candidate,
- pricing, licence, distribution terms or support commitments,
- paid integrations or accounts.

## Distribution folders

The current source-preview package is `2026.10.17-public.4`, derived from frozen public.3; `scripts/build_public4.py` builds it. Preserve all committed package/archive bytes during documentation work. Public.1, public.2 and public.3 archives and receipts are historical. The separate `2026.10.12-public.4-candidate.1` is an unpublished public.2-lineage repair candidate, built by `scripts/build_candidate.py`; its candidate/readiness documents are historical, not the current onboarding route. Do not hand-edit generated distribution content. Read the relevant builder and package records before packaging changes.

## Validate before proposing a change

With CPython 3.14.5 (the version CI uses):

```powershell
python -B scripts/validate_candidate.py
python -B -m unittest discover -s tests -p "test_*.py"
```

The Windows validator executes the unpublished repair candidate's extracted package and first run, not the current public.4 journey. Its link/privacy scan also inspects current public.4 files. Current public.4 has separate local Windows 3.11.15/3.14.5 evidence in `site/verification-public.4.json`; do not describe candidate CI as a current-release Python matrix.

For the repository-wide bounded marker/name scanner (separate Ubuntu CI):

```powershell
python -B -m unittest discover -s scripts -p "test_check_public_boundary.py"
python -B scripts/check_public_boundary.py
```

These checks are not exhaustive security verification, authenticated approval or independent H3. Report the actual environment, skips and unrun checks. Keep independent review and owner-controlled integration separate from implementer verification.

## How to change it

Work on a branch and open a pull request. Do not push to `main`, merge, tag or release without the owner's explicit word.
