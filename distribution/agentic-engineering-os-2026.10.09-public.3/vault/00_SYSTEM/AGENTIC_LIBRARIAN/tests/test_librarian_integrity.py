"""Disposable synthetic regressions for Librarian integrity."""
import importlib.util
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("public_librarian", Path(__file__).parents[1] / "librarian.py")
lib = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lib)


class IntegrityTests(unittest.TestCase):
    def test_ledger_must_be_exactly_checkpointed_without_hidden_drift(self):
        for mode in ('ignored', 'skip', 'assume'):
            with self.subTest(mode=mode):
                self.vault = self.base / mode
                (self.vault / 'docs').mkdir(parents=True)
                proposal, _ = self.fixture()
                self.approve(proposal)
                self.checkpoint()
                relative = (lib.SYSTEM_RELATIVE / 'ledger/artifact_ledger.jsonl').as_posix()
                if mode == 'ignored':
                    (self.vault / '.gitignore').write_text(relative + '\n')
                    self.git('rm', '--cached', '--', relative)
                    self.checkpoint()
                else:
                    self.git('update-index', '--skip-worktree' if mode == 'skip' else '--assume-unchanged', '--', relative)
                    ledger = self.vault / relative
                    ledger.write_bytes(ledger.read_bytes() + b'\n')
                self.assertEqual(self.git('status', '--porcelain'), b'')
                before = self.snapshot()
                for suffix in (('--dry-run',), ()):
                    with self.assertRaises(lib.LibrarianError):
                        self.command('apply', proposal['proposal_id'], *suffix)
                    self.assertEqual(self.snapshot(), before)

    def test_leftover_bronze_bytes_are_not_overwritten(self):
        source = self.base / 's.md'
        source.write_text('new synthetic evidence')
        destination = self.vault / lib.SYSTEM_RELATIVE / 'bronze/sources' / f'SRC-{lib.utc_now()[:4]}-000001__s.md'
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b'prior interrupted capture')
        before = self.snapshot()
        with self.assertRaises(lib.LibrarianError):
            self.command('ingest', str(source), '--project', 'Test')
        self.assertEqual(self.snapshot(), before)

    def test_leftover_silver_payload_bytes_are_not_overwritten(self):
        source = self.base / 's.md'
        source.write_text('synthetic evidence')
        row = self.command('ingest', str(source), '--project', 'Test')
        candidate = self.base / 'c.md'
        candidate.write_text('new candidate')
        destination = self.vault / lib.SYSTEM_RELATIVE / 'silver/payloads' / f'PROP-{lib.utc_now()[:4]}-000001.md'
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b'prior interrupted candidate')
        before = self.snapshot()
        with self.assertRaises(lib.LibrarianError):
            self.command('propose', '--project', 'Test', '--proposal-type', 'CREATE_KNOWLEDGE',
                         '--risk', 'low', '--confidence', 'high', '--title', 'Synthetic',
                         '--summary', 'Synthetic regression', '--target', 'docs/n.md',
                         '--source-id', row['source_id'], '--proposed-file', str(candidate))
        self.assertEqual(self.snapshot(), before)

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="li-"))
        self.vault = self.base / "v"
        (self.vault / "docs").mkdir(parents=True)

    def tearDown(self):
        def clean(fn, path, exc):
            Path(path).chmod(stat.S_IWRITE)
            fn(path)
        shutil.rmtree(self.base, onexc=clean)

    def command(self, *words):
        args = lib.build_parser().parse_args(["--vault-root", str(self.vault), *words])
        fn = {"verify": lib.verify_proposal, "apply": lib.apply_proposal,
              "rollback": lib.rollback_proposal}.get(args.command, getattr(lib, args.command, None))
        return fn(self.vault, args)

    def fixture(self, old="old\n", new="new\n", target="docs/n.md"):
        source = self.base / "s.md"
        source.write_text("synthetic evidence\n", encoding="utf8")
        candidate = self.base / "c.md"
        candidate.write_text(new, encoding="utf8")
        if old is not None:
            (self.vault / target).write_text(old, encoding="utf8")
        row = self.command("ingest", str(source), "--project", "Test")
        proposal = self.command("propose", "--project", "Test", "--proposal-type",
                                "CREATE_KNOWLEDGE" if old is None else "UPDATE_KNOWLEDGE",
                                "--risk", "low", "--confidence", "high", "--title", "Synthetic",
                                "--summary", "Synthetic regression", "--target", target,
                                "--source-id", row["source_id"], "--proposed-file", str(candidate))
        return proposal, row

    def approve(self, proposal):
        self.command("verify", proposal["proposal_id"])
        p = self.vault / proposal["proposal_path"]
        meta, body = lib.read_proposal(p)
        meta.update(status="approved", owner_decision="approved", owner_decision_by="owner",
                    owner_decision_at=meta["verified_at"])
        lib.write_proposal(p, meta, body)
        return meta

    def git(self, *words):
        return subprocess.run(["git", "-C", str(self.vault), *words], check=True,
                              capture_output=True).stdout

    def checkpoint(self):
        if not (self.vault / ".git").exists():
            self.git("init", "-b", "main")
            self.git("config", "user.name", "Synthetic")
            self.git("config", "user.email", "synthetic@example.invalid")
            self.git("config", "core.autocrlf", "false")
        self.git("add", "-A")
        self.git("commit", "-m", "synthetic checkpoint")

    def link(self, source, target, directory=False):
        try:
            source.symlink_to(target, target_is_directory=directory)
        except OSError as exc:
            self.skipTest(f"Symlink unavailable: {exc}")

    def snapshot(self):
        return {p.relative_to(self.base).as_posix(): p.read_bytes() for p in self.base.rglob("*")
                if p.is_file() and ".git" not in p.parts}

    def test_protected_target_alias_is_refused(self):
        protected = self.vault / "00_SYSTEM/AGENTIC_OS_RISK_REGISTER.md"
        protected.parent.mkdir()
        protected.write_text("SYNTHETIC protected sentinel", encoding="utf8")
        self.link(self.vault / "docs/n.md", protected)
        with self.assertRaises(lib.LibrarianError):
            lib.target_path(self.vault, {"target_path": "docs/n.md"})

    def test_temporary_alias_is_refused_without_outside_write(self):
        proposal, _ = self.fixture(old=None)
        self.approve(proposal)
        outside = self.base / "outside"
        outside.write_bytes(b"sentinel")
        temp = self.vault / "docs" / f".n.md.{proposal['proposal_id']}.tmp"
        self.link(temp, outside)
        self.checkpoint()
        before = self.snapshot()
        for suffix in [("--dry-run",), ()]:
            with self.assertRaises(lib.LibrarianError):
                self.command("apply", proposal["proposal_id"], *suffix)
            self.assertEqual(self.snapshot(), before)

    def test_altered_backup_refused_in_dry_run_and_apply(self):
        proposal, _ = self.fixture()
        self.approve(proposal)
        self.checkpoint()
        self.command("apply", proposal["proposal_id"])
        meta, _ = lib.read_proposal(self.vault / proposal["proposal_path"])
        (self.vault / meta["backup_path"]).write_bytes(b"altered")
        self.checkpoint()
        before = self.snapshot()
        for suffix in [("--dry-run",), ()]:
            with self.assertRaises(lib.LibrarianError):
                self.command("rollback", proposal["proposal_id"], "--confirm-proposal-id", proposal["proposal_id"], *suffix)
            self.assertEqual(self.snapshot(), before)

    def test_tail_change_is_in_saved_and_displayed_diff(self):
        prefix = "same line\n" * 1400
        proposal, _ = self.fixture(prefix + "OLD_TAIL\n", prefix + "NEW_TAIL\n")
        self.command("verify", proposal["proposal_id"])
        meta, body = lib.read_proposal(self.vault / proposal["proposal_path"])
        self.assertIn("+NEW_TAIL", (self.vault / meta["diff_path"]).read_text(encoding="utf8"))
        self.assertIn("+NEW_TAIL", body)
        self.assertIn("OLD_TAIL", body)

    def test_ignored_evidence_cannot_satisfy_checkpoint(self):
        proposal, _ = self.fixture()
        self.approve(proposal)
        (self.vault / ".gitignore").write_text("00_SYSTEM/\n", encoding="utf8")
        self.checkpoint()
        before = self.snapshot()
        for suffix in [("--dry-run",), ()]:
            with self.assertRaises(lib.LibrarianError):
                self.command("apply", proposal["proposal_id"], *suffix)
            self.assertEqual(self.snapshot(), before)

    def test_clean_update_apply_and_rollback(self):
        proposal, _ = self.fixture()
        self.approve(proposal)
        self.checkpoint()
        self.command("apply", proposal["proposal_id"], "--dry-run")
        self.command("apply", proposal["proposal_id"])
        self.checkpoint()
        self.command("rollback", proposal["proposal_id"], "--confirm-proposal-id", proposal["proposal_id"], "--dry-run")
        self.command("rollback", proposal["proposal_id"], "--confirm-proposal-id", proposal["proposal_id"])
        self.assertEqual((self.vault / "docs/n.md").read_text(), "old\n")

    def junction(self, link, target):
        if os.name != "nt":
            self.skipTest("Native Windows junction test")
        made = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
        if made.returncode:
            self.fail("Native junction creation failed: " + made.stderr.decode(errors="replace"))
        self.assertTrue(link.is_junction())

    def test_native_junction_bronze_refuses_before_outside_write(self):
        store = self.vault / lib.SYSTEM_RELATIVE
        store.mkdir(parents=True)
        outside = self.base / "out"
        outside.mkdir()
        (outside / "sentinel").write_bytes(b"unchanged")
        self.junction(store / "bronze", outside)
        source = self.base / "s.md"
        source.write_bytes(b"synthetic")
        before = self.snapshot()
        with self.assertRaises(lib.LibrarianError):
            self.command("ingest", str(source), "--project", "Test")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual({p.name for p in outside.iterdir()}, {"sentinel"})

    def test_native_junction_vault_ancestor_refused(self):
        alias = self.base / "alias"
        self.junction(alias, self.vault)
        before = self.snapshot()
        with self.assertRaises(lib.LibrarianError):
            lib.target_path(alias, {"target_path": "docs/n.md"})
        self.assertEqual(self.snapshot(), before)

    def test_hardlinked_target_refused(self):
        outside = self.base / "out"
        outside.write_bytes(b"synthetic")
        os.link(outside, self.vault / "docs/n.md")
        with self.assertRaises(lib.LibrarianError):
            lib.target_path(self.vault, {"target_path": "docs/n.md"})
        self.assertEqual(outside.read_bytes(), b"synthetic")

    def test_store_file_aliases_refuse_without_mutation(self):
        proposal, row = self.fixture()
        meta = self.approve(proposal)
        paths = [proposal["proposal_path"], row["stored_path"], meta["proposed_content_path"], meta["diff_path"],
                 (lib.SYSTEM_RELATIVE / "bronze/source_registry.jsonl").as_posix(),
                 (lib.SYSTEM_RELATIVE / "ledger/artifact_ledger.jsonl").as_posix()]
        for relative in paths:
            with self.subTest(relative=relative):
                p = self.vault / relative
                raw = p.read_bytes()
                outside = self.base / "outside"
                outside.write_bytes(raw)
                p.unlink()
                self.link(p, outside)
                before = self.snapshot()
                try:
                    with self.assertRaises(lib.LibrarianError):
                        self.command("apply", proposal["proposal_id"], "--dry-run")
                    self.assertEqual(self.snapshot(), before)
                finally:
                    p.unlink()
                    p.write_bytes(raw)

    def test_saved_diff_tamper_refuses_after_clean_recheckpoint(self):
        proposal, _ = self.fixture()
        meta = self.approve(proposal)
        (self.vault / meta["diff_path"]).write_bytes(b"altered review artifact")
        self.checkpoint()
        before = self.snapshot()
        for suffix in [("--dry-run",), ()]:
            with self.assertRaises(lib.LibrarianError):
                self.command("apply", proposal["proposal_id"], *suffix)
            self.assertEqual(self.snapshot(), before)

    def test_each_ignored_evidence_class_refuses(self):
        proposal, row = self.fixture()
        meta = self.approve(proposal)
        paths = [proposal["proposal_path"], row["stored_path"], meta["proposed_content_path"], meta["diff_path"],
                 (lib.SYSTEM_RELATIVE / "bronze/source_registry.jsonl").as_posix()]
        self.checkpoint()
        for relative in paths:
            with self.subTest(relative=relative):
                (self.vault / ".gitignore").write_text(relative + "\n", encoding="utf8")
                self.git("rm", "--cached", "--", relative)
                self.checkpoint()
                before = self.snapshot()
                with self.assertRaises(lib.LibrarianError):
                    self.command("apply", proposal["proposal_id"], "--dry-run")
                self.assertEqual(self.snapshot(), before)
                (self.vault / ".gitignore").write_bytes(b"")
                self.checkpoint()

    def test_filtered_and_skipped_evidence_refuse(self):
        proposal, _ = self.fixture()
        meta = self.approve(proposal)
        payload = meta["proposed_content_path"]
        self.checkpoint()
        self.git("update-index", "--skip-worktree", "--", payload)
        with self.assertRaises(lib.LibrarianError):
            self.command("apply", proposal["proposal_id"], "--dry-run")
        self.git("update-index", "--no-skip-worktree", "--", payload)
        self.git("update-index", "--assume-unchanged", "--", payload)
        with self.assertRaises(lib.LibrarianError):
            self.command("apply", proposal["proposal_id"], "--dry-run")
        self.git("update-index", "--no-assume-unchanged", "--", payload)
        (self.vault / ".gitattributes").write_text(payload + " filter=cat\n", encoding="utf8")
        self.git("config", "filter.cat.clean", "cat")
        self.git("config", "filter.cat.smudge", "cat")
        self.checkpoint()
        before = self.snapshot()
        with self.assertRaises(lib.LibrarianError):
            self.command("apply", proposal["proposal_id"], "--dry-run")
        self.assertEqual(self.snapshot(), before)

    def test_rollback_missing_aliased_or_wrong_backup_refuses(self):
        proposal, _ = self.fixture()
        self.approve(proposal)
        self.checkpoint()
        self.command("apply", proposal["proposal_id"])
        p = self.vault / proposal["proposal_path"]
        meta, body = lib.read_proposal(p)
        backup = self.vault / meta["backup_path"]
        raw = backup.read_bytes()
        outside = self.base / "out"
        outside.write_bytes(raw)
        backup.unlink()
        self.link(backup, outside)
        self.checkpoint()
        before = self.snapshot()
        with self.assertRaises(lib.LibrarianError):
            self.command("rollback", proposal["proposal_id"], "--confirm-proposal-id", proposal["proposal_id"], "--dry-run")
        self.assertEqual(self.snapshot(), before)
        backup.unlink()
        self.checkpoint()
        with self.assertRaises(lib.LibrarianError):
            self.command("rollback", proposal["proposal_id"], "--confirm-proposal-id", proposal["proposal_id"])

    def test_preexisting_regular_temp_preserved(self):
        proposal, _ = self.fixture()
        self.approve(proposal)
        temporary = self.vault / "docs" / f".n.md.{proposal['proposal_id']}.tmp"
        temporary.write_bytes(b"existing evidence")
        self.checkpoint()
        before = self.snapshot()
        for suffix in [("--dry-run",), ()]:
            with self.assertRaises(lib.LibrarianError):
                self.command("apply", proposal["proposal_id"], *suffix)
            self.assertEqual(self.snapshot(), before)

    def test_eof_and_crlf_changes_have_complete_review_and_restore(self):
        for old, new in [(b"same", b"same\n"), (b"same\r\n", b"same\n")]:
            with self.subTest(old=old, new=new):
                target = "docs/ending" + str(len(old)) + ".md"
                proposal, _ = self.fixture(old=None, new="temporary", target=target)
                p = self.vault / proposal["proposal_path"]
                meta, body = lib.read_proposal(p)
                meta["proposal_type"] = "UPDATE_KNOWLEDGE"
                (self.vault / target).write_bytes(old)
                payload = self.vault / meta["proposed_content_path"]
                payload.write_bytes(new)
                meta["proposed_content_sha256"] = lib.sha256_file(payload)
                lib.write_proposal(p, meta, body)
                self.approve(proposal)
                meta, body = lib.read_proposal(p)
                diff = (self.vault / meta["diff_path"]).read_bytes().decode("utf8")
                self.assertNotIn("(no content difference)", diff)
                self.assertIn("-same", diff)
                self.assertIn("+same", diff)
                if not old.endswith(b"\n"):
                    self.assertIn("\\ No newline at end of file", diff)
                else:
                    self.assertIn("Current line endings: CRLF=1, LF=0", diff)
                    self.assertIn("Proposed line endings: CRLF=0, LF=1", diff)
                self.assertIn(diff, body)
                self.checkpoint()
                self.command("apply", proposal["proposal_id"])
                self.assertEqual((self.vault / target).read_bytes(), new)
                self.checkpoint()
                self.command("rollback", proposal["proposal_id"], "--confirm-proposal-id", proposal["proposal_id"])
                self.assertEqual((self.vault / target).read_bytes(), old)


if __name__ == "__main__":
    unittest.main()
