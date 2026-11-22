# Operating guide

Read AGENTS and the session router. Select one project and its index/state/next actions. Use the existing packet builder to describe a bounded task, then the handoff CLI to copy only selected sources. Give that brief to your assistant manually. Capture its actual output, run the specified tests, and obtain independent review where required. The controller writes the verified result and next action into the project's current records.

The handoff's `check` compares live source bytes. `validate-result` checks a candidate's structure and evidence hashes. `review` combines source freshness with saved-result inspection. None of them authenticates approval, executes a model or issues H3.

Librarian ingests source evidence into Bronze and prepares Silver proposals. Only an owner-approved, verified proposal can be applied to Gold through its separate command and Git checkpoint. Pending knowledge can be read as candidate context with its status clearly stated.

See the package FIRST_RUN.md for exact commands, worked example, dependency versions and recovery instructions.
