# How AEOS works

AEOS organizes collaboration around durable files: scope before work, evidence after work, and a separate decision before integration. These pages explain a reusable operating method. The implemented public subset and exact commands are in [Architecture](ARCHITECTURE.md); this documentation adds no runtime integration or package payload.

## Follow one bounded loop

1. Turn intent into one observable outcome. Read the applicable instructions and route to the smallest relevant project or stage context.
2. Recover the project brain: purpose, current facts, constraints and next actions. Select supporting evidence by relevance and authority.
3. Prepare a [task packet](../templates/task-packet.md). Name reads, writes, checks, risk, human gates and recovery. Review it before assigning a worker.
4. Give an attended worker only the authorized context and tools. Preserve unrelated work and return artifacts with actual check results.
5. Run mechanical H1 and semantic H2 checks. Obtain [independent H3](VERIFICATION-H3.md) when required.
6. An authorized controller integrates the result and updates only facts supported by evidence. The owner accepts the outcome separately.

A passed script does not supply human approval. After three unsuccessful repair cycles across the task, stop and return the evidence and remaining decision. Switching tools does not reset the count.

## Risk determines the gate

| Level | Typical scope | Required control |
|---|---|---|
| R0 | Inspection | Read-only scope and qualified conclusions |
| R1 | Narrow documentation or mechanical edit | Explicit write scope and proportionate checks |
| R2 | Bounded change across files | Before-state evidence, applicable checks, report and independent review when required |
| R3 | Destructive, privileged, structural or external action | Explicit human authorization for that exact action before execution |

An earlier approval remains valid within its scope. A task approval alone grants no additional authority to send, deploy, merge or modify accounts.

## Resolve authority before context

Current control files outrank project state and owner decisions; those outrank primary specifications, then verified implementation evidence, generated summaries, conversation memory and inference. Report conflicts instead of silently reconciling them. Summaries help navigation but may omit current locks or lose freshness.

## Keep state domains separate

Execution can be `blocked` when a prerequisite is unavailable. Verification progresses through `pending`, `needs-review` and `complete`. Only a separate verifier assigns the final verdict `VERIFIED`, `PARTIAL` or `FAIL`. Completing a review can yield a failing verdict. Owner acceptance remains another decision.

Continue with [stack roles](STACK.md), [Runner](RUNNER.md), [knowledge](KNOWLEDGE-MODEL.md), [feature gates](FEATURE-STANDARD.md) and [conventions](CONVENTIONS.md).
