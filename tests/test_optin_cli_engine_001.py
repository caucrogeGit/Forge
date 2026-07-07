"""OPTIN-CLI-ENGINE-001 — palier 3b : moteur opt-in:remove / opt-in:disable.

- `opt-in:remove` : axe présence (−), affiche la désinstallation (les 6).
- `opt-in:disable` : axe activation (−), inverse exact d'`enable` pour iot,
  dry-run par défaut, garde §9 (un fichier modifié à la main est conservé).

`enable`/`disable` restent iot-only jusqu'à l'adaptateur (ticket 4).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.optins import disable, remove
from cli.optins.enable import SUPPORTED_OPTINS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FORGE_PY = (PROJECT_ROOT / "forge.py").read_text(encoding="utf-8")

ALL = ["mfa", "rbac", "workflow", "stats", "images", "iot"]


def _setup_enabled_iot(root: Path) -> Path:
    """Recrée l'état produit par `enable iot`, sans dépendre du package."""
    from cli.optins.enable import (
        REGISTRY,
        _SHARED_FILES,
        _register_in_registry,
    )

    for rel, content in (*_SHARED_FILES, *SUPPORTED_OPTINS["iot"]["files"]):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    registry, _ = _register_in_registry(REGISTRY, "iot")
    (root / "optins" / "registry.py").write_text(registry, encoding="utf-8")
    routes = root / "mvc" / "routes" / "__init__.py"
    routes.parent.mkdir(parents=True, exist_ok=True)
    routes.write_text(
        "from core.http.router import Router\n"
        "from optins.registry import register_optins\n\n"
        "router = Router()\n"
        "register_optins(router)\n",
        encoding="utf-8",
    )
    return routes


# ── opt-in:remove (affichage, n'exécute rien) ────────────────────────────────

class TestOptInRemove:
    @pytest.mark.parametrize("name", ALL)
    def test_remove_shows_uninstall(self, name, capsys):
        rc = remove.main([name])
        out = capsys.readouterr().out
        assert rc == 0
        assert f"forge-mvc-{name}" in out
        assert "uninstall" in out or "uninject" in out

    def test_unknown_exits_2(self, capsys):
        assert remove.main(["nope"]) == 2

    def test_missing_name_exits_2(self, capsys):
        assert remove.main([]) == 2

    def test_does_not_execute(self):
        source = (PROJECT_ROOT / "cli" / "optins" / "remove.py").read_text(encoding="utf-8")
        assert "subprocess" not in source and "os.system" not in source


# ── opt-in:disable (inverse de enable, iot) ──────────────────────────────────

class TestOptInDisable:
    def test_dry_run_removes_nothing(self, tmp_path, capsys):
        routes = _setup_enabled_iot(tmp_path)
        rc = disable.disable_optin("iot", apply=False, project_root=tmp_path)
        assert rc == 0
        assert (tmp_path / "optins" / "iot" / "routes.py").exists()
        assert "register_optins(router)" in routes.read_text(encoding="utf-8")

    def test_apply_reverses_enable(self, tmp_path):
        routes = _setup_enabled_iot(tmp_path)
        rc = disable.disable_optin("iot", apply=True, project_root=tmp_path)
        assert rc == 0
        # ADR-061 : le registre est permanent — seul optins/iot/ et le câblage
        # iot sont retirés ; optins/registry.py et le hook routes.py restent.
        assert not (tmp_path / "optins" / "iot").exists()
        assert (tmp_path / "optins" / "registry.py").exists()
        content = routes.read_text(encoding="utf-8")
        assert "register_optins(router)" in content  # hook générique conservé
        assert "router = Router()" in content        # code utilisateur préservé
        reg = (tmp_path / "optins" / "registry.py").read_text(encoding="utf-8")
        assert "optins.iot.routes" not in reg        # câblage iot retiré

    def test_idempotent_when_absent(self, tmp_path):
        assert disable.disable_optin("iot", apply=True, project_root=tmp_path) == 0

    def test_non_iot_exits_2(self, tmp_path):
        assert disable.disable_optin("mfa", apply=True, project_root=tmp_path) == 2

    def test_missing_name_exits_2(self):
        assert disable.main([]) == 2

    def test_modified_file_is_preserved(self, tmp_path):
        """Garde §9 : un fichier optins/ modifié à la main n'est pas supprimé."""
        _setup_enabled_iot(tmp_path)
        modified = tmp_path / "optins" / "iot" / "routes.py"
        modified.write_text("# édité à la main\n", encoding="utf-8")
        disable.disable_optin("iot", apply=True, project_root=tmp_path)
        assert modified.exists()
        assert modified.read_text(encoding="utf-8") == "# édité à la main\n"


# ── Dispatch + aide ──────────────────────────────────────────────────────────

class TestDispatchAndHelp:
    @pytest.mark.parametrize("command", ["opt-in:remove", "opt-in:disable"])
    def test_routed_in_forge_py(self, command):
        # ADR-059 : routage via la table CORE_COMMANDS de forge.py.
        from forge import CORE_COMMANDS

        assert command in CORE_COMMANDS

    @pytest.mark.parametrize("command", ["opt-in:remove", "opt-in:disable"])
    def test_has_description_and_rich(self, command):
        from cli._support.help_dispatch import HELP_DESCRIPTIONS, HELP_TEXTS_RICH
        assert command in HELP_DESCRIPTIONS
        assert command in HELP_TEXTS_RICH
