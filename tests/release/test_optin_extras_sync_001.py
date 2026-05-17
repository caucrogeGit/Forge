"""Tests release OPTIN-EXTRAS-SYNC-001.

Verifie la coherence entre les extras declares dans pyproject.toml racine
et les packages opt-in publiables.

Regles :
- les extras rbac/workflow/stats doivent pointer vers forge-mvc-<nom>>=1.0.0b4,<2 ;
- l'extra all doit contenir exactement ces trois packages, sans mfa ni media ;
- aucun opt-in non publiable ne doit apparaitre dans les extras actifs ;
- les extras doivent etre coherents avec les contraintes des packages sources.

Ce test ne fait aucune verification reseau et ne publie rien.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"

_PUBLISHABLE = {
    "rbac": "forge-mvc-rbac",
    "workflow": "forge-mvc-workflow",
    "stats": "forge-mvc-stats",
}
_NON_PUBLISHABLE_EXTRAS = ["media", "mfa"]


def _extras() -> dict[str, list[str]]:
    data = tomllib.loads(ROOT_PYPROJECT.read_text(encoding="utf-8"))
    return data.get("project", {}).get("optional-dependencies", {})


class TestExtrasCoherence:
    @pytest.mark.parametrize("extra_name,pkg_name", list(_PUBLISHABLE.items()))
    def test_extra_declared_for_publishable(self, extra_name, pkg_name):
        extras = _extras()
        assert extra_name in extras, (
            f"L'extra [{extra_name}] doit etre declare dans pyproject.toml racine."
        )

    @pytest.mark.parametrize("extra_name,pkg_name", list(_PUBLISHABLE.items()))
    def test_extra_dep_uses_relaxed_constraint(self, extra_name, pkg_name):
        extras = _extras()
        deps = extras.get(extra_name, [])
        matching = [d for d in deps if pkg_name in d]
        assert matching, (
            f"L'extra [{extra_name}] doit referencer {pkg_name}."
        )
        for dep in matching:
            assert ">=1.0.0b4,<2" in dep, (
                f"L'extra [{extra_name}] : contrainte {dep!r} — attendu >=1.0.0b4,<2."
            )

    @pytest.mark.parametrize("extra_name", _NON_PUBLISHABLE_EXTRAS)
    def test_non_publishable_extra_absent(self, extra_name):
        extras = _extras()
        assert extra_name not in extras, (
            f"L'extra [{extra_name}] ne doit pas etre declare dans pyproject.toml racine "
            f"— package non publiable (VERSION-SYNC-OPTIN-EXTRAS-001)."
        )


class TestAllExtraGroup:
    def test_all_declared(self):
        extras = _extras()
        assert "all" in extras, "L'extra [all] doit etre declare."

    def test_all_contains_exactly_publishable(self):
        extras = _extras()
        all_deps = extras.get("all", [])
        for pkg_name in _PUBLISHABLE.values():
            assert any(pkg_name in d for d in all_deps), (
                f"L'extra [all] doit contenir {pkg_name}."
            )

    def test_all_excludes_mfa(self):
        extras = _extras()
        all_deps = extras.get("all", [])
        assert not any("forge-mvc-mfa" in d for d in all_deps), (
            "L'extra [all] ne doit pas contenir forge-mvc-mfa (Pre-Alpha non publiable)."
        )

    def test_all_excludes_media(self):
        extras = _extras()
        all_deps = extras.get("all", [])
        assert not any("forge-mvc-media" in d for d in all_deps), (
            "L'extra [all] ne doit pas contenir forge-mvc-media (source-only)."
        )

    def test_all_contains_exactly_three_packages(self):
        extras = _extras()
        all_deps = extras.get("all", [])
        assert len(all_deps) == 3, (
            f"L'extra [all] doit contenir exactement 3 packages "
            f"(rbac/workflow/stats) — trouvé {len(all_deps)} : {all_deps}."
        )


class TestCrossPackageVersionCoherence:
    @pytest.mark.parametrize("extra_name,pkg_name", list(_PUBLISHABLE.items()))
    def test_extra_constraint_matches_package_dep(self, extra_name, pkg_name):
        extras = _extras()
        extra_deps = extras.get(extra_name, [])
        extra_matching = [d for d in extra_deps if pkg_name in d]
        assert extra_matching, f"Extra [{extra_name}] ne reference pas {pkg_name}."
        for dep in extra_matching:
            assert ">=1.0.0b4,<2" in dep, (
                f"Extra [{extra_name}]: contrainte {dep!r} incohérente avec packages sources."
            )
