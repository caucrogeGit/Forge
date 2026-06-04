"""OPTIN-CLI-VERBS-001 — palier 3a : surface des commandes opt-in:*.

Introduit les verbes canoniques `opt-in:install` / `opt-in:enable` /
`opt-in:list` (ADR-016). Ce palier livre uniquement les verbes *complets*
(§10 — une API publique est un contrat de complétude) : `install` (affichage)
et les délégations `enable`/`list`. `disable`/`remove` arrivent au palier 3b
avec leur moteur.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_cli.optins import install
from forge_cli.optins.catalog import OFFICIAL_OPTINS, optin_names

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FORGE_PY = (PROJECT_ROOT / "forge.py").read_text(encoding="utf-8")


# ── Catalogue canonique ──────────────────────────────────────────────────────

class TestCatalog:
    def test_official_optins(self):
        assert optin_names() == [
            "audio", "iot", "media", "mfa", "rbac", "stats", "video", "workflow",
        ]

    @pytest.mark.parametrize("name", ["mfa", "rbac", "workflow", "stats", "media", "iot", "video", "audio"])
    def test_dist_and_import_naming(self, name):
        optin = OFFICIAL_OPTINS[name]
        assert optin.package_dist == f"forge-mvc-{name}"
        assert optin.package_import == f"forge_mvc_{name}"
        assert optin.summary


# ── opt-in:install (affichage, n'exécute rien) ───────────────────────────────

class TestOptInInstall:
    @pytest.mark.parametrize("name", ["mfa", "rbac", "workflow", "stats", "media", "iot", "video", "audio"])
    def test_install_shows_package_and_succeeds(self, name, capsys):
        rc = install.main([name])
        out = capsys.readouterr().out
        assert rc == 0
        assert f"forge-mvc-{name}" in out
        assert f"forge opt-in:enable {name}" in out

    def test_install_does_not_execute(self):
        """install affiche une commande pip/pipx, ne l'exécute pas (pas de subprocess)."""
        source = (PROJECT_ROOT / "forge_cli" / "optins" / "install.py").read_text(encoding="utf-8")
        assert "subprocess" not in source
        assert "os.system" not in source

    def test_unknown_optin_exits_2(self, capsys):
        rc = install.main(["does-not-exist"])
        err = capsys.readouterr().err
        assert rc == 2
        assert "inconnu" in err.lower()

    def test_missing_name_exits_2(self, capsys):
        rc = install.main([])
        assert rc == 2

    def test_help_exits_0(self, capsys):
        rc = install.main(["--help"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "opt-in:install" in out


# ── Dispatch + aide ──────────────────────────────────────────────────────────

class TestDispatchAndHelp:
    @pytest.mark.parametrize("command", [
        "opt-in:install",
        "opt-in:enable",
        "opt-in:list",
    ])
    def test_command_routed_in_forge_py(self, command):
        assert f'command == "{command}"' in FORGE_PY, (
            f"{command} doit être routé dans forge.py."
        )

    @pytest.mark.parametrize("command", [
        "opt-in:install",
        "opt-in:enable",
        "opt-in:list",
    ])
    def test_command_has_short_description(self, command):
        from forge_cli.help_dispatch import HELP_DESCRIPTIONS
        assert command in HELP_DESCRIPTIONS

    def test_install_has_rich_help(self):
        from forge_cli.help_dispatch import HELP_TEXTS_RICH
        assert "opt-in:install" in HELP_TEXTS_RICH


# ── Legacy retiré (OPTIN-CLI-REMOVE-LEGACY-001, palier 3c) ───────────────────

class TestLegacyRemoved:
    @pytest.mark.parametrize("command", ["optin:enable", "optin:list"])
    def test_legacy_optin_commands_removed(self, command):
        # Rupture franche pré-1.0 : les anciens noms ne sont plus dispatchés.
        assert f'command == "{command}"' not in FORGE_PY
