"""Garde-fou FORGE-HELP-SAFE-FLAG-001.

Vérifie que `forge <cmd> --help` n'exécute aucune logique métier :
- pas de création de fichier SQL parasite
- pas de tentative de connexion DB
- pas de message "Arguments inconnus"
- exit 0

Origine : audit post-T11 — `forge migration:make --help` créait un fichier
.sql parasite (YYYYMMDDHHMMSS_help.sql) car --help était traité comme le
nom de la migration avant la détection de flag.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


def _run_forge(args: list[str], *, cwd: str | None = None, timeout: int = 10):
    try:
        return subprocess.run(
            ["forge"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("forge non disponible dans le PATH du test")


class TestMigrationMakeHelp:
    """forge migration:make --help ne doit pas créer de fichier SQL."""

    def test_exits_zero(self):
        result = _run_forge(["migration:make", "--help"])
        assert result.returncode == 0, (
            f"forge migration:make --help a retourné exit {result.returncode}. "
            f"Stdout: {result.stdout[:200]!r}"
        )

    def test_no_sql_file_created(self):
        """--help ne crée aucun fichier .sql parasite dans le répertoire courant."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _run_forge(["migration:make", "--help"], cwd=tmpdir)
            sql_files = list(Path(tmpdir).rglob("*.sql"))
            assert not sql_files, (
                f"forge migration:make --help a créé des fichiers SQL parasites : "
                f"{[str(p) for p in sql_files]}"
            )

    def test_output_contains_usage(self):
        result = _run_forge(["migration:make", "--help"])
        output = result.stdout + result.stderr
        assert "usage" in output.lower() or "forge migration:make" in output.lower(), (
            f"forge migration:make --help ne contient pas d'indication d'usage. "
            f"Sortie : {output[:300]!r}"
        )


class TestModuleListHelp:
    """forge module:list --help ne doit pas retourner 'Arguments inconnus'."""

    def test_exits_zero(self):
        result = _run_forge(["module:list", "--help"])
        assert result.returncode == 0, (
            f"forge module:list --help a retourné exit {result.returncode}. "
            f"Stdout: {result.stdout[:200]!r}"
        )

    def test_no_unknown_args_error(self):
        result = _run_forge(["module:list", "--help"])
        output = result.stdout + result.stderr
        assert "arguments inconnus" not in output.lower(), (
            f"forge module:list --help a retourné 'Arguments inconnus'. "
            f"Sortie : {output[:300]!r}"
        )

    def test_output_contains_usage(self):
        result = _run_forge(["module:list", "--help"])
        output = result.stdout + result.stderr
        assert "usage" in output.lower() or "forge module:list" in output.lower(), (
            f"forge module:list --help ne contient pas d'indication d'usage. "
            f"Sortie : {output[:300]!r}"
        )


class TestDbApplyHelp:
    """forge db:apply --help ne doit pas tenter une connexion DB."""

    def test_exits_zero(self):
        result = _run_forge(["db:apply", "--help"])
        assert result.returncode == 0, (
            f"forge db:apply --help a retourné exit {result.returncode}. "
            f"Stdout: {result.stdout[:200]!r}"
        )

    def test_no_db_connection_error(self):
        result = _run_forge(["db:apply", "--help"])
        output = result.stdout + result.stderr
        assert "connexion mariadb applicative impossible" not in output.lower(), (
            f"forge db:apply --help a tenté une connexion MariaDB. "
            f"Sortie : {output[:300]!r}"
        )

    def test_output_contains_usage(self):
        result = _run_forge(["db:apply", "--help"])
        output = result.stdout + result.stderr
        assert "usage" in output.lower() or "forge db:apply" in output.lower(), (
            f"forge db:apply --help ne contient pas d'indication d'usage. "
            f"Sortie : {output[:300]!r}"
        )


class TestStarterBuildHelp:
    """forge starter:build --help ne doit pas traiter --help comme un identifiant."""

    def test_exits_zero(self):
        result = _run_forge(["starter:build", "--help"])
        assert result.returncode == 0, (
            f"forge starter:build --help a retourné exit {result.returncode}. "
            f"Stdout: {result.stdout[:200]!r}"
        )

    def test_no_starter_not_found_error(self):
        result = _run_forge(["starter:build", "--help"])
        output = result.stdout + result.stderr
        assert "introuvable" not in output.lower(), (
            f"forge starter:build --help a traité --help comme un identifiant. "
            f"Sortie : {output[:300]!r}"
        )

    def test_output_contains_usage(self):
        result = _run_forge(["starter:build", "--help"])
        output = result.stdout + result.stderr
        assert "usage" in output.lower() or "forge starter:build" in output.lower(), (
            f"forge starter:build --help ne contient pas d'indication d'usage. "
            f"Sortie : {output[:300]!r}"
        )
