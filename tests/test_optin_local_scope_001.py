"""OPTIN-LOCAL-SCOPE-001 — clôture ADR-016 (ticket 4b).

Décision A2 : la famille `opt-in:*` couvre les opt-ins **officiels** ; le
système `module:*` reste l'outil distinct du workflow d'auteur de **module
local**. Pas de fusion. Sur un nom inconnu, `opt-in:*` oriente vers
`forge module:install`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_cli.optins import disable, enable, install, remove
from forge_cli.optins.catalog import LOCAL_MODULE_HINT

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FORGE_PY = (PROJECT_ROOT / "forge.py").read_text(encoding="utf-8")
ADR = (PROJECT_ROOT / "docs" / "adr" / "016-opt-in-unification.md").read_text(encoding="utf-8")
GLOSSARY = (PROJECT_ROOT / "docs" / "reference" / "vocabulaire-opt-in.md").read_text(encoding="utf-8")


# ── module:* reste un namespace distinct (pas fusionné) ──────────────────────

class TestModuleCommandsKept:
    @pytest.mark.parametrize("command", [
        "module:list", "module:install", "module:files", "module:routes",
    ])
    def test_module_command_still_routed(self, command):
        assert f'"{command}"' in FORGE_PY


# ── opt-in:* oriente vers module:install sur un nom local inconnu ─────────────

class TestUnknownNameHintsLocalModule:
    def test_hint_constant_points_to_module_install(self):
        assert "module:install" in LOCAL_MODULE_HINT

    def test_install_unknown_hints_module(self, capsys):
        rc = install.main(["mon-module-local"])
        err = capsys.readouterr().err
        assert rc == 2
        assert "module:install" in err

    def test_remove_unknown_hints_module(self, capsys):
        rc = remove.main(["mon-module-local"])
        err = capsys.readouterr().err
        assert rc == 2
        assert "module:install" in err

    def test_enable_unknown_hints_module(self, capsys):
        rc = enable.main(["mon-module-local"])
        out = capsys.readouterr().out
        assert rc == 2
        assert "module:install" in out

    def test_disable_unknown_hints_module(self, capsys):
        rc = disable.main(["mon-module-local"])
        out = capsys.readouterr().out
        assert rc == 2
        assert "module:install" in out


# ── Décision documentée ──────────────────────────────────────────────────────

class TestDecisionDocumented:
    def test_adr_has_amendment_a2(self):
        assert "### A2" in ADR
        assert "ne pas fusionner" in ADR.lower()

    def test_glossary_clarifies_module_commands(self):
        assert "module:install" in GLOSSARY
