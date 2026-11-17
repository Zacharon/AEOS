# Human and agent feature acceptance

This is a prospective design standard, not certification of existing features. Human controls and documented agent capabilities should reach the same application commands, rules and durable state, within their respective privileges.

| Gate | Acceptance requirement |
|---|---|
| 1. Shared capabilities | Equivalent authorized requests use the same command and validation and yield equivalent results. Document the human control and agent invocation. |
| 2. Shared state | Changes become visible through both interfaces after refresh or reconnect and survive restart with authoritative revision context. |
| 3. Scoped authority | The application resolves identity, ownership, grants and expiry before effects. Human-only decisions stay with humans. |
| 4. Human usability | Essential tasks remain usable with AI disabled, through ordinary navigation, controls and understandable errors. |
| 5. Visible supervision | People can inspect proposals, active work, outcomes and failures, and deny, cancel or take over at documented boundaries where supported. |
| 6. Safe recovery | Matching scoped retries produce one effect; changed payloads or stale revisions refuse. Recovery preserves newer valid edits and identifies irreversible or uncertain outcomes. |
| 7. Receipts | State and evidence commit consistently, recording actor, operation, target, revisions, result and recovery without sensitive payloads or hidden reasoning. |

Gates 1-4 apply to new or materially changed features. Gates 5-7 apply when user data is written or an external effect occurs. Record PASS, FAIL, PARTIAL, NOT RUN or NOT APPLICABLE with a reason and evidence for each relevant capability; failed or missing applicable proof prevents a completion claim.

Before implementation, specify typed inputs and outputs, shared handler, storage, verified principal, scope, revision checks, retry behavior, approval boundary, cancellation, receipt and recovery limits. A copied approval field or an API alone proves none of these gates. Test synthetic workflows through both interfaces and challenge denied access, stale writes, retries and interrupted outcomes. Documentation-only work can justify inapplicability individually; it does not certify the software described.
