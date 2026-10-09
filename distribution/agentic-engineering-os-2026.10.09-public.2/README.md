# Agentic Engineering OS setup package

A local, file-based starting point for independent builders coordinating ongoing work with AI. Keep current project state, give an assistant bounded context, preserve its result, and review evidence before changing the source of truth.

This is a **public source preview**, version 2026.10.09-public.2. Start with [FIRST_RUN.md](FIRST_RUN.md). It includes reusable vault templates, the existing Runner packet builder and handoff tools, Agentic Librarian code and schemas, focused tests, manual adapter templates, and a deterministic synthetic demonstration. It does not contain personal projects, credentials or operating history.

The portable core prepares and checks files. You invoke your assistant and bring its output back. No model API, native worker sandbox, paid service, scheduler or external connector is installed. Native worker sandboxes, visual navigation and experimental retrieval/model tools are **not included**.

## Requirements

- CPython 3.14.5; this revision tested on Windows with existing prerequisites with CPython 3.14.5, PyYAML 6.0.3 and jsonschema 4.26.0.
- Git 2.x for Librarian apply/rollback; source intake and demonstration do not need Git or a network connection after dependencies are installed.
- Any Markdown editor; Obsidian is optional. An assistant able to read local files is useful but not needed for the deterministic demo.
- Other operating systems and other dependency versions are unverified. The portable handoff core uses only Python's standard library; Librarian needs [requirements.txt](requirements.txt).

## What you receive

`vault/` mirrors the small reusable part of the working OS. `examples/` holds authored synthetic inputs. `scripts/` runs and checks the example. `config/adapters.json` describes manual handoffs. [MANIFEST.json](MANIFEST.json) lists every file, hash and original component path. [SOURCES.md](SOURCES.md), [LICENSE](LICENSE) and [TERMS-DRAFT.md](TERMS-DRAFT.md) record attribution, reserved rights and pending commercial terms.

## Updates and removal

Extract each new version beside the previous one. Verify the manifest, run its demo, review changes, then copy only chosen templates/tools into your own vault after a backup. Never overwrite a populated vault wholesale. Keep existing run packets and evidence. Roll back only files you changed, after checking their current hashes against your install receipt; a concurrent edit needs manual reconciliation. Stop invoking the scripts to disable them. There is no service, account, registry change or automatic task to remove. Preserve your vault and run outputs before removing an extracted package.

This source preview carries no price, promised support level or performance guarantee. Commercial license and distribution terms remain unset.

[Architecture and usage](ARCHITECTURE.md) · [Integrity repairs and compatibility](SECURITY-REPAIRS.md). This is a reviewable repair candidate, not a merged release.
