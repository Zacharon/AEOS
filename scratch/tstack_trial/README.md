# Tstack installation and first local workflow trial

Status: implementation checks PASS; independent Sol review APPROVE in one round.

Nine tstack skills installed on the host from upstream revision
`1085050f3baed1ac724caa4a8166145fb2ac88af`: full-send, full-stop, sol-loop,
file-pr, babysit-pr, leaving-pr-comments, council, takeover, modernize.
All 14 upstream payload files match the pinned archive. MIT notices are retained.
Shared skills have Claude junction adapters; the refreshed host catalog has
all nine shared entries and zero scan errors. A fresh reviewer session confirmed
Sol Loop and Full Stop in its enabled catalog before reading their source files.
All nine now also appear in the parent session's enabled skill catalog. Discovery
does not mean every installed workflow has been exercised end to end.
Host paths, account configuration and host catalog contents are not exported here.

## Trial

[Packet](PACKET.md) freezes acceptance and the allowed scope. Baseline and candidate
are isolated copies of public-safe experiment tooling, not Git worktrees. The
original experiment and unrelated working-tree files are unchanged.

- [Baseline evidence](evidence/baseline.json): existing output throws a traceback
  and exits 1; original/new-output and regression behavior otherwise works.
- [Candidate evidence](evidence/candidate.json): existing output exits 2 with an
  understandable refusal and unchanged bytes; new output works; 18 tests pass.
- Changed behavior: candidate/compare.py catches FileExistsError around exclusive
  directory creation. Diff: four additions, one deletion. No policy logic changes.
- [Source manifest](source-manifest.json) binds original bytes; both runs verify
  that the original source and the baseline copy remain unchanged.

Run `python -B trial.py --help` to inspect the shared human/agent command.
This evidence directory is retained; rerunning the same variant refuses reuse of
its fresh-output target. Prepare new isolated copies for another complete replay.
The focused suite can be rerun with `python -B -m unittest -v test_policy` from
candidate/. It uses temporary synthetic storage and no model/network calls.

## Evidence levels and limits

Actual local implementation/reproduction tests ran. This is not a ten-task
matched agent benchmark. Command timings do not establish model speed or token
efficiency. Parent/reviewer token usage and human attention remain UNKNOWN until
reported by the platform; there is no invented subscription cost.

Sol Loop completed with one reviewer, one round and no findings. The reviewer
used gpt-6.1-sol at medium effort, verified the exact candidate hash, reran all
18 regressions, and confirmed original/baseline preservation. Collision and
fresh-output checks were reviewed from saved evidence, not independently rerun.
The behavior diff stayed at four additions and one deletion. No follow-up review
was needed because the reviewer requested no behavior changes. See the
[review record](evidence/sol-round-1.json).

The local proof/review stages are only part of Full Stop. File PR, hosted CI,
PR watching, Full Send merging, a three-provider council, takeover, and modernize
have NOT RUN in this trial. No publication, default-branch push or merge occurred.
No autonomous installed AEOS stopping policy changed.

The upstream source and research context are in
[the workflow assessment](../../docs/research/TSTACK-WORKFLOW-2026-11-02.md).
This candidate is kept outside distributed packages. A real PR pilot and the
proposed ten-task comparison remain separate evidence levels.
