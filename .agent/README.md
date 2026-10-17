# Agent skills

Instructions for any AI assistant or agent working with AEOS, whatever tool runs it. Each skill is a plain Markdown file at `.agent/skills/<name>/SKILL.md` with `name` and `description` frontmatter, followed by the steps. Read the description to decide whether a skill applies, then read only that skill.

Start with the repository [AGENTS.md](../AGENTS.md). Its boundary rules outrank every skill here.

| Skill | Use it when |
|---|---|
| [aeos-start-session](skills/aeos-start-session/SKILL.md) | Beginning any session in an AEOS vault: find the project and the minimum files to read |
| [aeos-task-packet](skills/aeos-task-packet/SKILL.md) | Turning a goal into a bounded, reviewable task packet |
| [aeos-handoff](skills/aeos-handoff/SKILL.md) | Building, checking, returning and resuming a handoff bundle |
| [aeos-knowledge-librarian](skills/aeos-knowledge-librarian/SKILL.md) | Ingesting a source or proposing new knowledge (Bronze, Silver, Gold) |
| [aeos-independent-review](skills/aeos-independent-review/SKILL.md) | Reviewing someone else's result as an independent (H3) verifier |
| [aeos-close-session](skills/aeos-close-session/SKILL.md) | Ending a session: authorized writeback and an honest report |
| [aeos-data-handling](skills/aeos-data-handling/SKILL.md) | Before passing business records, customer data or datasets to an assistant |
| [aeos-repo-maintenance](skills/aeos-repo-maintenance/SKILL.md) | Changing this public repository: boundary, validation and owner-only decisions |

The first seven describe the workflow shipped in the package `vault/`. Paths in them are relative to that vault unless they say otherwise. The last one is about this repository itself.

## Using these with a specific tool

The files are tool-neutral. To expose them to a tool that looks elsewhere, point it here instead of copying: for example a line in that tool's own instruction file saying "Skills live in `.agent/skills/*/SKILL.md`; read `.agent/README.md` first". Copies drift; one source does not.

The package handoff CLI only accepts skills from `.codex/skills/<name>/SKILL.md` or `03_SKILLS/skills/*.md` inside a vault. These repository skills are not vault content and are not passed with `--skill`.

## Adding a skill

1. Create `.agent/skills/<kebab-name>/SKILL.md`. The folder name and `name` field match.
2. Write a one-line `description` that says when to use it.
3. Keep the body short and imperative. Name real commands and files; mark anything manual as manual.
4. Add a row to the table above.
5. Keep it public-safe: neutral template material only, no personal vault content, private paths, account identifiers, credentials, pricing, licence or support terms.
