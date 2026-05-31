"""OPTIN-KIND-ADAPTER-001 — palier 4a : classification + enable/disable kind-aware.

Chaque opt-in officiel a un ``kind`` (route | library | crosscutting).
``opt-in:enable`` / ``opt-in:disable`` câblent réellement le kind ``route``
(iot) et **informent** pour les ``library`` / ``crosscutting`` (rien à écrire,
pas de cérémonie vide — §8).
"""
from __future__ import annotations

import pytest

from forge_cli.optins import disable, enable, list as optin_list
from forge_cli.optins.catalog import (
    KIND_CROSSCUTTING,
    KIND_LIBRARY,
    KIND_ROUTE,
    OFFICIAL_OPTINS,
)
from forge_cli.optins.guidance import disable_guidance, enable_guidance

LIBRARY = ["workflow", "stats", "media"]
CROSSCUTTING = ["mfa", "rbac"]


# ── Classification ───────────────────────────────────────────────────────────

class TestKindClassification:
    def test_iot_is_route(self):
        assert OFFICIAL_OPTINS["iot"].kind == KIND_ROUTE

    @pytest.mark.parametrize("name", LIBRARY)
    def test_libraries(self, name):
        assert OFFICIAL_OPTINS[name].kind == KIND_LIBRARY

    @pytest.mark.parametrize("name", CROSSCUTTING)
    def test_crosscutting(self, name):
        assert OFFICIAL_OPTINS[name].kind == KIND_CROSSCUTTING

    def test_exactly_one_route_kind(self):
        routes = [o for o in OFFICIAL_OPTINS.values() if o.kind == KIND_ROUTE]
        assert [o.name for o in routes] == ["iot"]

    def test_every_route_kind_has_enable_template(self):
        """Garde-fou anti-drift (OPTIN-AUDIT-FIX-001, F1).

        Tout opt-in de kind ``route`` doit avoir un template dans
        ``SUPPORTED_OPTINS`` ; sinon ``opt-in:enable`` planterait (main délègue
        au moteur route pour ces opt-ins). Empêche d'ajouter un futur opt-in
        routier au catalogue sans son câblage.
        """
        from forge_cli.optins.enable import SUPPORTED_OPTINS

        route_optins = {n for n, o in OFFICIAL_OPTINS.items() if o.kind == KIND_ROUTE}
        missing = route_optins - set(SUPPORTED_OPTINS)
        assert not missing, (
            f"Opt-ins kind=route sans template d'enable (SUPPORTED_OPTINS) : {missing}"
        )


# ── enable kind-aware (library/crosscutting = guidance, n'écrit rien) ────────

class TestEnableKindAware:
    @pytest.mark.parametrize("name", LIBRARY)
    def test_library_enable_is_informational(self, name, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        rc = enable.main([name])
        out = capsys.readouterr().out
        assert rc == 0
        assert "bibliothèque" in out
        assert not (tmp_path / "optins").exists()  # rien d'écrit

    @pytest.mark.parametrize("name", CROSSCUTTING)
    def test_crosscutting_enable_is_informational(self, name, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        rc = enable.main([name])
        out = capsys.readouterr().out
        assert rc == 0
        assert "transversal" in out
        assert not (tmp_path / "optins").exists()

    def test_unknown_exits_2(self, capsys):
        assert enable.main(["does-not-exist"]) == 2

    def test_mfa_guidance_points_to_starter(self):
        assert "welcome-optin-mfa" in enable_guidance(OFFICIAL_OPTINS["mfa"])

    def test_rbac_guidance_mentions_decorators(self):
        assert "require_permission" in enable_guidance(OFFICIAL_OPTINS["rbac"])


# ── disable kind-aware ───────────────────────────────────────────────────────

class TestDisableKindAware:
    @pytest.mark.parametrize("name", LIBRARY + CROSSCUTTING)
    def test_non_route_disable_is_informational(self, name, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        rc = disable.main([name])
        assert rc == 0
        assert OFFICIAL_OPTINS[name].name in capsys.readouterr().out

    def test_unknown_exits_2(self):
        assert disable.main(["nope"]) == 2

    def test_library_disable_guidance(self):
        assert "rien à débrancher" in disable_guidance(OFFICIAL_OPTINS["workflow"]).lower()


# ── list enrichi ─────────────────────────────────────────────────────────────

class TestListEnriched:
    def test_lists_all_optins(self, tmp_path, capsys):
        optin_list.list_optins(project_root=tmp_path)
        out = capsys.readouterr().out
        for name in ["iot", *LIBRARY, *CROSSCUTTING]:
            assert name in out
        assert "bibliothèque" in out
        assert "transversal" in out
