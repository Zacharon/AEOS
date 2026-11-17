# File and session conventions

Use numbered areas to make routing predictable: system rules, project records, role definitions, skills, references, prompts, outputs, logs, templates and tools. Numbering is navigation, not priority or authority. Application code belongs in its own repository; project notes point to it.

Prefer descriptive Markdown names, lowercase words with underscores for ordinary notes, and readable underscore-separated project names. Preserve established control filenames and existing links. Use kebab-case for repository skill folders, matching their frontmatter name. Avoid renaming imported evidence without an approved migration.

## Decisions have a validity interval

Record a decision date using `YYYY-MM-DD`, its scope, rationale and effective interval. Preserve superseded text and connect both ends with supersedes/superseded-by references; partial overrides name their scope. Only an owner-recorded decision changes owner-controlled status. A later summary cannot silently replace the decision.

## Start, end and resume

At entry, read applicable instructions, identify the named boundary, inspect current locks and select the minimum sources. Read project index, state and next actions when continuation depends on them; a self-contained task uses its own relevant sources. Record the allowed work and expected evidence before editing.

At close, report changed artifacts, actual checks, unknowns, remaining decisions and the next authorized action. Update only designated records whose facts changed, with evidence links and a concise session entry where required. Do not produce dashboard activity merely to show work.

On resume, reread current authority and check saved evidence against live sources. Prior chat and generated packs are snapshots. Keep session continuity separate from a new authorization to execute. Start from the [blank templates](../templates/session-log.md), which carry no completed history or approval.
