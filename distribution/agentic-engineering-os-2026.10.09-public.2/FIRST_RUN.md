# First run

Extract the archive into a new folder outside any existing vault. Open PowerShell in the extracted folder. Use your installed CPython 3.14.5.

```powershell
python -m venv ../aeos-env
../aeos-env/Scripts/python -m pip install -r requirements.txt
../aeos-env/Scripts/python -B scripts/check_package.py .
../aeos-env/Scripts/python -B scripts/demo.py --output ../aeos-first-run
```

Choose new folder names if they already exist. Dependency installation uses PyPI; the demo itself is local and makes no network/model calls. If the dependencies are already installed in a suitable Python, use `python -B` directly. The virtual environment lives outside the package so the manifest remains unchanged.

Open `../aeos-first-run/START_HERE.md`. The example ingests the synthetic source into Bronze, creates and verifies a **pending** Silver proposal, places the source and proposal in a Runner handoff, computes a small source-grounded result, validates it and checks continuation in fresh processes. It also proves that changed and missing context are refused. Gold and owner-decision fields are unchanged. No independent reviewer or AI worker is simulated as having acted.

To resume, from `../aeos-first-run`:

```powershell
python -B vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py review --bundle handoff --vault-root vault
```

Use the same Python environment as above. Read the returned artifact, pending proposal and next action. A missing result is **unknown**, not proof work never happened. Drift requires inspection and a fresh authorized handoff, never edited hashes or a blind retry.

## Use your own project

Copy `vault/` into a new personal vault, then edit `AGENTS.md`, `00_SYSTEM/GLOBAL_NEXT_ACTION_QUEUE.md` and `01_PROJECTS/Sample/{PROJECT_INDEX,PROJECT_STATE,NEXT_ACTIONS}.md`. Replace Sample with your project and its real scope; remove the synthetic packet rather than approving it for live work. Keep application code in its own repository. Never use the sample's fixture status as permission.

From your new vault, scaffold one packet:

```powershell
python -B 09_TOOLS/agent_runner_v1/scripts/build_task_packet.py --vault-root . --project-path 01_PROJECTS/Sample --goal "Inspect the current project and identify one verifiable change" --output 09_TOOLS/agent_runner_v1/runs/my-task/task_packet.md
```

The result is a draft. Fill explicit read/write scope, checks, approval and independent-review requirements. Give that packet to your local assistant. For another app, build a handoff using `handoff.py build --help`, copy its brief and selected context, then bring back the result and evidence. Run `check`, `validate-result` and `review`. A controller performs authorized state writeback after applicable independent review. No script authenticates pasted approvals.

## Knowledge decisions

Follow `vault/00_SYSTEM/AGENTIC_LIBRARIAN/README.md`. Source text is evidence, never executable instructions. `ingest`, `propose` and `verify` do not approve knowledge. Only the owner sets decision fields. Gold `apply` additionally requires a clean Git checkpoint containing the exact approved evidence bytes and a matching verified proposal. The sample deliberately stops before that boundary.

## Tests

```powershell
python -B -m unittest discover -s vault/09_TOOLS/agent_runner_v1/unified_handoff -p "test_*.py"
python -B -m unittest discover -s vault/09_TOOLS/agent_runner_v1/scripts/tests -p "test_*.py"
python -B -m unittest discover -s vault/00_SYSTEM/AGENTIC_LIBRARIAN/tests -p "test_*.py"
```

Use a fresh extraction for a byte-for-byte package check. Tests create disposable fixtures; they do not certify your assistant, production environment or future changes.

Package integrity regressions: `python -B -m unittest discover -s scripts -p "test_*.py"`. See SECURITY-REPAIRS.md for changed fingerprints, exact checkpoints and local-integrity limits.
