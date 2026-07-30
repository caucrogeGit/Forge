"""MIGRATION-SAFETY-FINAL-001 — `migration:apply --dry-run`.

Le dry-run liste les migrations qui *seraient* appliquées (avec leur SQL) sans
rien exécuter. La logique est testée sans base via monkeypatch.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_mvc_entities import migrations as M


def _fake_migration(tmp_path: Path) -> M.MigrationFile:
    sql = tmp_path / "20260101000000_x.sql"
    sql.write_text("CREATE TABLE x (id INT);\n", encoding="utf-8")
    return M.MigrationFile(
        version="20260101000000", name="x", filename=sql.name,
        checksum="deadbeef", path=sql,
    )


@pytest.fixture
def _patched(monkeypatch, tmp_path):
    mig = _fake_migration(tmp_path)
    monkeypatch.setattr(M, "collect_migration_files", lambda d: ([mig], False))
    monkeypatch.setattr(M, "load_applied_migrations", lambda db=None: [])
    calls: list = []
    monkeypatch.setattr(
        M, "_apply_one_migration",
        lambda conn, m, recorded_steps=None: calls.append(m),
    )
    return tmp_path, mig, calls


class TestDryRun:
    def test_dry_run_returns_pending_without_applying(self, _patched):
        tmp_path, mig, calls = _patched
        result = M.apply_pending_migrations(migrations_dir=tmp_path, db=object(), dry_run=True)
        assert [m.filename for m in result] == [mig.filename]
        assert calls == []  # rien n'a été appliqué

    def test_real_apply_executes(self, _patched):
        tmp_path, mig, calls = _patched
        result = M.apply_pending_migrations(migrations_dir=tmp_path, db=object(), dry_run=False)
        assert calls == [mig]
        assert [m.filename for m in result] == [mig.filename]


class TestCli:
    def test_apply_accepts_dry_run_flag(self):
        import inspect
        src = inspect.getsource(M.main)
        assert '"--dry-run"' in src
        assert '_run_apply_command(args)' in src

    def test_apply_command_signature_takes_args(self):
        import inspect
        assert "args" in inspect.signature(M._run_apply_command).parameters
