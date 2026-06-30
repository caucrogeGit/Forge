"""Tests — OPTINS-CLI-LIST-001.

Vérifie la commande **lecture seule** `forge opt-in:list` :

- `--help` fonctionne ; `forge help` liste `opt-in:list` ;
- projet sans opt-ins → `iot absent` ;
- `optins/iot/` présent mais `mvc/routes.py` non branché → `partiel` ;
- `optins/iot/` + `register_optins(router)` → `activé` ;
- la commande ne crée et ne modifie **aucun** fichier ;
- elle n'importe pas `forge_mvc_iot` ; pas de discovery ;
- `core/` n'importe toujours pas les opt-ins.

Tests unitaires via `list_optins(project_root=tmp)` / `detect_iot_state`
— aucun fichier réel du dépôt n'est touché.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from cli.optins.list import (
    STATE_ABSENT,
    STATE_ACTIVE,
    STATE_PARTIAL,
    detect_iot_state,
    list_optins,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
FORGE_PY = _REPO_ROOT / "forge.py"
HELP_FILE = _REPO_ROOT / "cli" / "_support" / "help.py"
LIST_FILE = _REPO_ROOT / "cli" / "optins" / "list.py"
CORE_DIR = _REPO_ROOT / "core"

_RECOGNIZED_ROUTES = (
    "from core.http.router import Router\n"
    "\n"
    "router = Router()\n"
)


def _make_optins_iot(root: Path) -> None:
    """Crée une structure optins/iot/ minimale (pour les tests)."""
    iot = root / "optins" / "iot"
    iot.mkdir(parents=True)
    (root / "optins" / "__init__.py").write_text("", encoding="utf-8")
    (root / "optins" / "registry.py").write_text(
        "def register_optins(router):\n"
        "    from optins.iot.routes import register as register_iot\n"
        "    register_iot(router)\n",
        encoding="utf-8",
    )
    (iot / "__init__.py").write_text("", encoding="utf-8")
    (iot / "routes.py").write_text(
        "from forge_mvc_iot import register_iot_routes\n"
        "def register(router):\n"
        "    register_iot_routes(router)\n",
        encoding="utf-8",
    )
    (iot / "README.md").write_text("# Opt-in Forge IoT\n", encoding="utf-8")


def _make_routes(root: Path, content: str) -> None:
    mvc = root / "mvc"
    mvc.mkdir(exist_ok=True)
    (mvc / "routes.py").write_text(content, encoding="utf-8")


# ── Détection d'état ─────────────────────────────────────────────────────────


class TestDetectState:
    def test_absent_when_no_optins(self, tmp_path):
        info = detect_iot_state(tmp_path)
        assert info["state"] == STATE_ABSENT
        assert info["structure_present"] is False

    def test_partial_when_structure_but_routes_not_branched(self, tmp_path):
        _make_optins_iot(tmp_path)
        _make_routes(tmp_path, _RECOGNIZED_ROUTES)
        info = detect_iot_state(tmp_path)
        assert info["state"] == STATE_PARTIAL
        assert info["structure_present"] is True
        assert info["routes_branched"] is False

    def test_partial_when_no_routes_file(self, tmp_path):
        _make_optins_iot(tmp_path)  # pas de mvc/routes.py
        info = detect_iot_state(tmp_path)
        assert info["state"] == STATE_PARTIAL

    def test_active_when_routes_branched(self, tmp_path):
        _make_optins_iot(tmp_path)
        _make_routes(tmp_path, _RECOGNIZED_ROUTES + "\nregister_optins(router)\n")
        info = detect_iot_state(tmp_path)
        assert info["state"] == STATE_ACTIVE
        assert info["routes_branched"] is True


# ── Sortie ───────────────────────────────────────────────────────────────────


class TestOutput:
    def test_absent_output(self, tmp_path, capsys):
        rc = list_optins(project_root=tmp_path)
        out = capsys.readouterr().out
        assert rc == 0
        assert "Forge opt-ins" in out
        assert "iot       absent" in out
        assert "forge opt-in:enable iot --apply" in out
        assert "Aucune modification effectuée." in out

    def test_partial_output(self, tmp_path, capsys):
        _make_optins_iot(tmp_path)
        _make_routes(tmp_path, _RECOGNIZED_ROUTES)
        rc = list_optins(project_root=tmp_path)
        out = capsys.readouterr().out
        assert rc == 0
        assert "iot       partiel" in out
        assert "optins/iot/" in out
        assert "absent de mvc/routes.py" in out

    def test_active_output(self, tmp_path, capsys):
        _make_optins_iot(tmp_path)
        _make_routes(tmp_path, _RECOGNIZED_ROUTES + "\nregister_optins(router)\n")
        rc = list_optins(project_root=tmp_path)
        out = capsys.readouterr().out
        assert rc == 0
        assert "iot       activé" in out
        assert "register_optins(router) présent" in out


# ── Lecture seule (aucune écriture) ──────────────────────────────────────────


class TestReadOnly:
    def test_does_not_create_optins(self, tmp_path, capsys):
        list_optins(project_root=tmp_path)
        capsys.readouterr()
        assert not (tmp_path / "optins").exists()

    def test_does_not_modify_routes(self, tmp_path, capsys):
        _make_optins_iot(tmp_path)
        _make_routes(tmp_path, _RECOGNIZED_ROUTES)
        before = (tmp_path / "mvc" / "routes.py").read_text(encoding="utf-8")
        list_optins(project_root=tmp_path)
        capsys.readouterr()
        after = (tmp_path / "mvc" / "routes.py").read_text(encoding="utf-8")
        assert before == after

    def test_does_not_modify_registry(self, tmp_path, capsys):
        _make_optins_iot(tmp_path)
        before = (tmp_path / "optins" / "registry.py").read_text(encoding="utf-8")
        list_optins(project_root=tmp_path)
        capsys.readouterr()
        after = (tmp_path / "optins" / "registry.py").read_text(encoding="utf-8")
        assert before == after


# ── Garde-fous périmètre ─────────────────────────────────────────────────────


class TestScopeGuards:
    def test_command_does_not_import_forge_mvc_iot(self):
        import ast

        src = LIST_FILE.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("forge_mvc_iot")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("forge_mvc_iot")

    def test_no_magic_discovery(self):
        src = LIST_FILE.read_text(encoding="utf-8")
        for forbidden in ("pkgutil", "iter_modules", "walk_packages", "find_spec"):
            assert forbidden not in src, forbidden

    def test_no_write_apis_in_source(self):
        # Lecture seule : pas d'écriture de fichiers.
        src = LIST_FILE.read_text(encoding="utf-8")
        for forbidden in ("write_text", "write_bytes", "mkdir", "open("):
            assert forbidden not in src, forbidden

    def test_core_does_not_import_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(_REPO_ROOT))
        assert not offenders, offenders


# ── Enregistrement CLI ───────────────────────────────────────────────────────


class TestCliRegistration:
    def test_forge_py_dispatches_optin_list(self):
        # ADR-059 : opt-in:list est dispatchée via la table CORE_COMMANDS.
        from forge import CORE_COMMANDS

        assert "opt-in:list" in CORE_COMMANDS

    def test_help_py_lists_optin_list(self):
        assert "opt-in:list" in HELP_FILE.read_text(encoding="utf-8")

    def test_help_renders(self):
        result = subprocess.run(
            [sys.executable, str(FORGE_PY), "opt-in:list", "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "opt-in:list" in result.stdout
        assert "lecture seule" in result.stdout.lower()

    def test_forge_help_lists_optin_list(self):
        result = subprocess.run(
            [sys.executable, str(FORGE_PY), "help"],
            capture_output=True, text=True, timeout=30,
        )
        assert "opt-in:list" in result.stdout
