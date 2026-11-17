# Theo's tstack: adoption assessment

Research date: 2026-11-02 Eastern; retrieval 2026-11-03 03:01 UTC.
Public-source research, not an installation or accepted AEOS policy.
No skills, provider settings, accounts, PRs or published files were changed.

## Primary sources examined

- [Theo's site](https://t3.gg/) links his T3 Code, channel, GitHub and other work.
- [These 3 skills changed my life](https://www.youtube.com/watch?v=5Bmp9cz1JN8),
  Theo - t3.gg, published 2026-10-26. Direct YouTube metadata and English
  automatic captions retrieved (566543 bytes), selected timestamped cues read
  in memory; no transcript copied into this repository.
- [So my workflow has changed a lot...](https://www.youtube.com/watch?v=SY_woOjzlW4),
  same channel, published 2026-10-14. Direct metadata and English automatic
  captions retrieved (4539482 bytes); selected workflow cues examined, not the
  complete stream. No transcript copied into this repository.
- [tstack source at inspected revision](https://github.com/t3dotgg/tstack/tree/1085050f3baed1ac724caa4a8166145fb2ac88af),
  current commit observed through GitHub API: 1085050f3baed1ac724caa4a8166145fb2ac88af,
  dated 2026-10-28. README and five relevant skill files read from main;
  commit recorded after those reads, not a byte manifest for each retrieval.
- [T3 Code composer documentation](https://github.com/pingdotgg/t3code/blob/53e168fef5efa6141c89c1775e0630d6dc488f49/docs/user/composer.md).
  Main read during research; observed repository commit
  53e168fef5efa6141c89c1775e0630d6dc488f49. Upstream evolves quickly.

## What the source actually provides

[Sol Loop](https://github.com/t3dotgg/tstack/blob/1085050f3baed1ac724caa4a8166145fb2ac88af/skills/sol-loop/SKILL.md)
uses one GPT Sol reviewer, three rounds by default, an issue ledger and early
exit for minor suggestions. Later passes focus on changed code and unresolved
findings. A new review is not automatic after every edit. It still supplies the
base diff, so narrowed instructions do not guarantee lower input-token usage.
There is no enforced token budget or published cost benchmark in this file.

[Full Stop](https://github.com/t3dotgg/tstack/blob/1085050f3baed1ac724caa4a8166145fb2ac88af/skills/full-stop/SKILL.md)
prepares and verifies a PR but reserves merging for the user.
[Full Send](https://github.com/t3dotgg/tstack/blob/1085050f3baed1ac724caa4a8166145fb2ac88af/skills/full-send/SKILL.md)
continues through merge when its gate passes. Both require more than a reviewer
opinion. The latter authorizes significant branch/PR actions and must be invoked
deliberately; neither is being invoked by researching it here.

[Babysit PR](https://github.com/t3dotgg/tstack/blob/1085050f3baed1ac724caa4a8166145fb2ac88af/skills/babysit-pr/SKILL.md)
uses event-driven PR waiting in T3 Code rather than repeated model polling.
[Council](https://github.com/t3dotgg/tstack/blob/1085050f3baed1ac724caa4a8166145fb2ac88af/skills/council/SKILL.md)
uses three strong models from distinct providers. Its satisfaction loop lacks an
explicit round/token ceiling. That is a potentially expensive escalation, not
the starting point for reducing tokens. Parallel work can reduce elapsed time
while increasing total consumption. This cost assessment is an inference from
the workflow, not a measured comparison.

## Useful video locations

In the October 26 video, around [5:19](https://www.youtube.com/watch?v=5Bmp9cz1JN8&t=319s)
Theo explains the review loop and scope discipline;
[6:05](https://www.youtube.com/watch?v=5Bmp9cz1JN8&t=365s) covers one reviewer
without nested reviewers. Around [19:17](https://www.youtube.com/watch?v=5Bmp9cz1JN8&t=1157s)
he reports 27 of 32 Full Send requests merging without further intervention.
This is a practitioner report about autonomous completion, not an independently
controlled accuracy, token-cost or human-team comparison.
Around [21:03](https://www.youtube.com/watch?v=5Bmp9cz1JN8&t=1263s) he introduces
the Full Stop merge boundary. Around [28:00](https://www.youtube.com/watch?v=5Bmp9cz1JN8&t=1680s)
he discusses prompt duplication with manual invocation in his Claude Code setup.
Treat that as configuration-specific; do not generalize it to every current
T3/provider integration. Automatic captions can mistranscribe model/skill names.

The October 14 stream contains an earlier, longer version of this workflow,
including the skill discussion around 1:04 onward. The focused later video is
the more efficient starting point; the stream is useful for seeing context.

## Recommended adaptation for AEOS

Use the existing packet, context boundary, verification and factual writeback.
Do not install a second task ledger or let a model change the acceptance checks.
Proposed default: one implementer, one independent Sol reviewer, Full Stop for
PR delivery. For trivial changes, use covering checks and human inspection;
do not automatically purchase a multi-model review for every text edit.

The implementation brief should name the outcome, narrow scope, out-of-scope
work, acceptance commands, relevant source entry points and action permissions.
The reviewer receives the exact base/head, scoped diff, relevant callers, test
results and open findings, not the entire conversation or operating vault.
Follow-up review gets changed behavior and the findings ledger, with access to
required surrounding context. Keep the final accepted behavior tied to its
reviewed revision. Do not mistake two models agreeing for executable proof.

Retain applicable security/authority/data-loss and H3 gates. The generic skill's
aggressive treatment of rare cases as minor suggestions should not downgrade an
in-scope authorization bypass or consequential recovery failure. Owner-only
release/publication decisions remain separate from ordinary PR preparation.
The previous failure-novelty experiment remains advisory: repeated findings
should trigger explanation/escalation within the review budget, not an automatic
claim of impossibility or completion.

## Getting the skills into the user's workflow

The relevant skill names are not exposed in this session. The
[upstream README](https://github.com/t3dotgg/tstack/blob/1085050f3baed1ac724caa4a8166145fb2ac88af/README.md)
documents cloning and copying the skills, an authenticated GitHub CLI, and a
route to the required reviewer models. For this Workspace, install provider-neutral
skills once under `~/.agents/skills/` and expose them through the host's supported
discovery route; avoid competing copies in multiple provider directories.
Review and pin upstream before installation. Preserve its MIT notice.

Full Stop depends on Full Send, Sol Loop, File PR and Babysit PR; supporting PR
skills also use Leaving PR Comments. Resolve that dependency closure rather
than copying only a single file. Use the existing T3 delegate and PR watcher
tools. Do not invent a provider route or silently substitute an unavailable
requested reviewer. Upstream's Unix `python3` script requirement needs checking
on Windows if used outside T3's native watcher path.

T3's composer documentation supports skill selection with `$`, restarting the
agent session after changing skills, and `/compact` where the provider supports
it. Compact after writing durable task state and evidence; it is context
management, not a guarantee of preserved reasoning or lower total cost.

## Measurement before scaling

Proposed pilot: ten representative bounded tasks, using comparable isolated
copies of the same starting revision. Compare the current process with the
bounded review workflow under matching model/version/effort/tool conditions.
Freeze acceptance checks first; randomize ordering and repeat tasks where
practical. Count failed/abandoned attempts rather than excluding them.

Record total input/output/cached/reasoning usage when the provider exposes it,
including implementer, reviewers, repair turns and orchestration. Unknown
telemetry stays unknown. Also record elapsed time, human attention, accepted
results, reopened defects and out-of-scope edits. Cache accounting varies by
provider; do not manufacture a uniform cost from subscriptions or token totals.

Optimize cost per independently accepted task and time to accepted result.
Reduced parent-thread tokens alone can conceal expensive delegates. A human-team
superiority claim needs an actual matched human baseline with the same acceptance
criteria. Exact model output need not repeat; reproducibility means the code,
environment, checks and evidence let another operator verify the result.

No such comparison, installation or real PR trial was performed in this research.
