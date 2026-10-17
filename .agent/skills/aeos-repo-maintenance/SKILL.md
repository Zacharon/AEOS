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

`distribution/*-public.1` and `*-public.2` are frozen. The current candidate is built deterministically by `scripts/build_candidate.py` and must match its committed bytes; do not hand-edit files inside it. Read `docs/PACKAGE-CANDIDATE.md` before touching packaging.

## Validate before proposing a change

With CPython 3.14.5 (the version CI uses):

```powershell
python -B scripts/validate_candidate.py
python -B -m unittest discover -s tests -p "test_*.py"
```

These check the extracted package, the documented first run, regressions, and that local links resolve and no private path or credential marker appears in the scanned files. CI runs the same validation on Windows for every pull request.

## How to change it

Work on a branch and open a pull request. Do not push to `main`, merge, tag or release without the owner's explicit word.
