# AEOS ecosystem: what belongs, what does not, and why

Reviewed 2026-10-09. This is a source-backed design assessment, not an installation plan accepted by a buyer or evidence that unbuilt capabilities work. [Architecture](ARCHITECTURE.md) describes the shipped preview; [designed visual](../site/architecture.html) explains its handoffs. [Source observations](research/source-checks.json) record exact current revisions and license/readme hashes. Current upstream revisions are observation pins, not AEOS dependency versions.

## The integration decision

Keep a small file-based coordination system: project facts → selected context → bounded handoff → returned evidence → independent review where required → authorized writeback. Knowledge acquisition is a separate governed path: source bytes → candidate synthesis → exact owner decision → controlled application. Skills help a participant perform a stage; they do not own the project queue, permissions, knowledge store or release decision.

The public repository should contain reusable commands, neutral project/instruction templates, synthetic examples, accurate diagrams, source credits and reproducible integrity checks. Include methods selectively when their actual artifacts improve this loop. Do not bundle entire competing agent harnesses, an unrestricted memory writer, host configuration, creator operating notes, real project examples or unsupported connectors. A larger plugin inventory is not evidence of a better system.

The public.2 preview already supplies routing documents, packet scaffolding, explicit file selection, hashed handoff snapshots, result/review checks, Librarian staging/application controls and a deterministic demo. It does **not** dispatch models, run a background Wiki service, enforce skill selection or automatically format assistant responses. The public archive has its own frozen manifest; these repository research pages and the new visual are companion documentation, not newly added archive payloads.

## Correcting the proposed fusion

| Proposal | Source reality and AEOS decision |
|---|---|
| ICM replaces every multi-agent/RAG system and drastically reduces tokens | [Van Clief and McDermott's paper, v2](https://arxiv.org/abs/2603.16021v2) and [reference repository](https://github.com/RinDig/Interpretable-Context-Methodology) support staged filesystem context. AEOS borrows selective context and readable contracts. AEOS has not reproduced the paper's comparisons or measured token savings. A folder name alone does not enforce stage execution. |
| Wiki eliminates retrieval and gives the LLM complete control | [Karpathy's idea file](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) proposes maintained synthesis and still includes querying/search. AEOS combines readable knowledge with retrieval; Librarian requires explicit approval for Gold. Generated synthesis can be wrong, stale or contradictory. No unattended knowledge promotion. |
| Matt's whole skill suite should be installed | [Pocock v1.3.1](https://github.com/mattpocock/skills/releases/tag/v1.3.1) is the examined workflow reference. Borrow bounded specifications, dependency readiness, separate review axes and evidence-based PRs. Keep AEOS's existing task authority; no automatic push, merge, issue closure or second tracker. Skill bodies are absent from public.2. |
| Superpowers guarantees one branch per agent and automatic correct merges | [Superpowers](https://github.com/obra/superpowers) supplies engineering workflow skills. Branching, dispatch and review behavior depends on the selected workflow and host. Use debugging, meaningful tests and completion evidence as methods; do not claim an installed framework or treat a review as release permission. |
| ECC means Engineering Content and Continuity | [Affaan Mustafa's ECC](https://github.com/affaan-m/ECC) was named Everything Claude Code; its [migration guide](https://github.com/affaan-m/ECC/blob/main/docs/MIGRATION-1X-TO-2.0.md) records the rename. Select retrieval, evaluation and continuity ideas. Observers, hooks and self-learning require separate compatibility/authority trials; none are public preview features. |
| ADHD guidance should rewrite every output automatically | [Ayoub Ghriss's skill](https://github.com/ayghri/i-have-adhd) is presentation guidance. Use clear outcomes, short steps when useful and a concrete next action without assuming a reader's diagnosis. Preserve exact commands/evidence. No text postprocessor is installed. |
| Diagram Design becomes a runtime engine | [Cathryn Lavery's Diagram Design](https://github.com/cathrynlavery/diagram-design) informs the newly authored offline HTML/SVG companion. Diagrams are derived explanations with accessible text and explicit statuses; they do not select tasks or change state. No upstream scripts or skill body are shipped. See [notice](THIRD_PARTY_DIAGRAM_NOTICE.txt). |

## Wider approaches worth comparing

These candidates were inspected through original project documentation. None is added as a runtime dependency by this assessment.

| Approach | Useful contribution | Why it stays optional |
|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Explicit stateful execution and durable workflow mechanics | Consider only when manual transport is the demonstrated bottleneck. Its checkpoints do not replace AEOS owner approval or canonical project facts. AEOS should not claim other frameworks inherently have rigid sequences. |
| [Microsoft AutoGen](https://github.com/microsoft/autogen) | Programmatic agent coordination | Its README says maintenance mode and directs new users to Microsoft Agent Framework; treat AutoGen as a historical comparison, not a new-install recommendation. More agents introduce coordination cost and authority questions. Its documented split is CC-BY-4.0 for documentation and MIT for code; dependencies still require inspection. |
| [DSPy](https://github.com/stanfordnlp/dspy) | Evaluate and optimize a bounded model program against examples | Useful after a measurable task and held-out cases exist. Optimize the candidate operation, not permissions or canonical truth. Requires a separately configured model environment. |
| [QMD](https://github.com/tobi/qmd) | Local search over Markdown using lexical/semantic methods | Candidate read-only retrieval adapter if file selection becomes slow. Benchmark against simple filename/content search first; no automatic whole-vault indexing, model/cache distribution or implied zero network activity. |
| [Meta-Harness paper](https://arxiv.org/abs/2603.28052v1) and [official code](https://github.com/stanford-iris-lab/meta-harness) | Evaluate harness candidates using saved traces and scores | Research direction after fixed tests and recovery controls. Paper gains belong to its authors' experiments; AEOS has not reproduced them. No automatic harness/policy rewrite or promotion. |

## The architecture should grow at its seams

1. **Explain and measure the existing loop first.** Keep the current entry point, commands and saved artifacts. A task receipt should say which context was selected, which checks ran and which transitions remain manual. This documentation/visual pass is implemented; comparative benchmarks remain proposed.
2. **Try a read-only retrieval adapter only after a selection problem appears.** Return source paths, hashes, dates and reasons to the existing handoff builder. Never let retrieval silently expand the approved read set or declare conflicting facts resolved.
3. **Add a dependency-ready task projection only for real parallel work.** Each task names dependencies, allowed writes and required evidence. A predecessor becomes usable after verified integration into the worker's actual checkout. Parent ownership and existing records remain authoritative.
4. **Improve continuity before adding observers.** A new session must recover the correct state and next action from saved files alone. Proposed retrospectives can suggest instruction changes; they cannot silently install hooks, edit policies or promote knowledge.
5. **Add provider transport last.** Define identity, cancellation, timeout, result correlation and permission boundaries, with a manual fallback. Test a synthetic run before making integration claims. Provider credentials and commercial decisions belong to the installing owner.

## Proposed evaluation contract

Do not advertise AEOS as faster, cheaper or more accurate until a dated comparison supports that particular claim. The integrity suite and deterministic demo verify different properties from model task performance.

| Evaluation | Controlled comparison and measurement | Acceptance proposed for the first pilot |
|---|---|---|
| Context selection | Same synthetic corpus/questions: title/content search versus selected files versus optional search adapter. Score required-source recall, irrelevant files, bytes and source citations. | All mandatory authority/lock sources retained; no out-of-scope source. Report accuracy trade-offs. Bytes are not token telemetry. |
| Engineering task | Same bounded tasks, model/version/effort and permissions across baseline and AEOS; at least three runs per condition, held-out tasks, order variation. | Correctness against independent acceptance tests; report failures, human interventions, time and uncertainty. No winner inferred from one demo. |
| Source → useful knowledge | Plant contradictory, stale and missing synthetic sources. Check citations and whether candidate context is labeled. | No approval bypass; conflicts/unknowns explicit; source drift refused; no unintended Gold writes. |
| Continuity | Fresh worker receives only entry instructions and saved files. Include interrupted and stale-result cases. | Correct current state, evidence status, remaining gate and next action; no chat-summary dependence. |
| Recovery and boundaries | Existing alias, altered backup, full-diff, optimized checker and ignored-evidence negatives plus round-trip restoration fixtures. | Invalid operations refuse with protected bytes/evidence preserved. This is local integrity, not hostile same-user isolation. |
| Usability | Attended first-run tasks on tested environment; record wrong turns and number of manual handoffs. | Owner completes the documented flow and recognizes pending/verified/approved states. No testimonials inferred. |

Token/cost comparisons require actual provider telemetry with cached versus uncached usage separated. Account subscriptions are not equivalent to API list prices. Dataset, evaluator, model revision, prompts, environment, failed attempts and results must be saved. Independent review should inspect the held-out results and report unsupported conclusions.

## Implementation briefs for subsequent bounded work

- **Retrieval experiment:** extend the existing handoff CLI with an explicitly selected read-only adapter, preserving `--read` scope and manifest hashes. Use only a synthetic corpus; compare against the current manual/content-search baseline; no private index export or default model downloads.
- **Dependency experiment:** add an opt-in task dependency schema beside existing packet/result contracts; reject cycles, missing predecessors and changed integration revisions. Preserve single-task operation. Never dispatch, merge or close external tickets automatically.
- **Continuity experiment:** use the current `handoff.py review` entry point with fresh workers and fixtures for missing/stale evidence. Save the recovered next action and compare it to fixture truth. Add a general recovery service only after a demonstrated unmet requirement.
- **Benchmark experiment:** create a separate synthetic evaluation directory; freeze tasks, acceptance checks and splits before trials. Record real usage when available and `UNKNOWN` otherwise. Optimizers can write candidate copies only; promotion uses existing review gates.

These are implementation-ready scopes, not authorization for public releases, paid integrations, account changes or unrestricted data access. The smallest next step is a repeatable fresh-session/context-selection trial on the existing synthetic sample.

## Attribution and coverage

The new designed companion was rendered locally in Brave at 1440×1100, 820×1180 and 390×844. Desktop/mobile screenshots were inspected; checks found no horizontal overflow, page errors or external asset requests. Both standalone SVGs match their inline versions and include accessible descriptions. This validates these local explanation files; it does not claim hosted-site or model-workflow performance. The frozen public.2 runtime/archive bytes remain unchanged and retain their separately recorded verification scope.

The byte-hash metadata inventory covers eleven named repositories. The ICM/Meta-Harness papers and Karpathy gist were separately read and linked above; their bodies are not in that JSON inventory. This is not an exhaustive framework survey, dependency audit or reproduction of research results. MIT identifiers in API results were checked at the recorded revisions; an API `NOASSERTION` requires manual reading. Diagram Design's recorded LICENSE is MIT; AutoGen's root LICENSE is CC-BY-4.0 and its separate [LICENSE-CODE](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/LICENSE-CODE) is MIT. Karpathy's idea file has no identified standalone redistribution license, so it is linked/paraphrased. Paper licenses do not license unrelated implementations.

This pass redistributes no upstream code, skill bodies, paper/gist bodies, model weights or framework installations. The retained Diagram Design MIT notice applies to its credited method material, not a new license for AEOS. Any later copied/adapted implementation requires its exact notices, component licenses and manifest. Existing AEOS ownership and source-preview terms remain unchanged; no endorsement is implied.
