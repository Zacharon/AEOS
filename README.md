# AEOS — Agentic Engineering OS

A source preview for independent builders coordinating ongoing work with AI. Keep current project facts in files, prepare bounded context, inspect the returned evidence and continue in a fresh session.

This repository contains neutral templates, reusable tools and an authored synthetic sample. It contains no personal operating vault, private project context, account configuration or user history.

## Try it

Download the [setup archive](site/downloads/agentic-engineering-os-2026.10.09-public.2.zip), or use the [unpacked package](distribution/agentic-engineering-os-2026.10.09-public.2/README.md). Follow its FIRST_RUN.md. The demo ingests a source, creates a pending knowledge proposal, prepares a handoff, checks a sample result and rejects stale or missing context. It makes no model calls and does not apply Gold knowledge.

CPython 3.14.5 is required; Windows with CPython 3.14.5 is tested. Install the package's documented requirements into a fresh virtual environment. Git is needed for the Librarian's approved apply/rollback path. Other platforms and provider handoffs are unverified.

## Explore the system

- [Architecture and usage flow](docs/ARCHITECTURE.md) — real file contracts, commands and manual handoffs
- [First run](site/first-run.html)
- [Capabilities and verification](site/verification.html)
- [Source credits](site/sources.html)
- [Public-safe verification receipt](site/verification-public.2.json)

To view the site locally, run `python -m http.server 4396 --bind 127.0.0.1 --directory site` from this repository and open http://127.0.0.1:4396. Serve only site/, never a personal workspace. The HTML files also open locally.

The tools prepare and check files; assistant handoffs are manual. No autonomous team, model runtime, provider authentication, native sandbox or hosted service is installed. Mechanical verification, independent review, owner acceptance and release remain distinct.

This is a public source preview, not a paid product release. Pricing, commercial license/distribution terms and support are unset. No open-source license or support commitment is asserted. See the package TERMS-DRAFT.md and SOURCES.md. The repository publication does not deploy the website.

## Authorship and rights

Created by Zachary Hatch. Copyright (c) 2026 Zachary Hatch. All rights reserved.

See [LICENSE](LICENSE) for the copyright and rights notice. Source credits identify influences and separately installed third-party dependencies; they do not transfer authorship of AEOS or imply endorsement.
