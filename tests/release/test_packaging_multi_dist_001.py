"""Tests PACKAGING-MULTI-DIST-001 : infrastructure multi-distributions PyPI.

Verifie que :
- le repertoire packages/ contient les 4 distributions optionnelles ;
- chaque distribution optionnelle a un pyproject.toml valide ;
- forge-mvc (pyproject.toml racine) declare les bons extras optionnels ;
- les 4 distributions optionnelles ont leur package placeholder __init__.py ;
- le pyproject.toml racine est a jour (version, optional-dependencies).

Note T2b : depuis PACKAGING-WHEEL-CONTENT-001, forge-mvc est publie
depuis le pyproject.toml racine (plus de packages/forge-mvc/pyproject.toml).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest


PACKAGES_DIR = Path("packages")
ROOT_PYPROJECT = Path("pyproject.toml")
VERSION = tomllib.loads(ROOT_PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]

OPTIONAL_DISTS = [
    "forge-mvc-mfa",
    "forge-mvc-rbac",
    "forge-mvc-workflow",
    "forge-mvc-stats",
]
OPTIONAL_MODULES = [
    "forge_mvc_mfa",
    "forge_mvc_rbac",
    "forge_mvc_workflow",
    "forge_mvc_stats",
]
ALL_DISTS = OPTIONAL_DISTS


# ---------------------------------------------------------------------------
# Classe 1 — Structure du répertoire packages/
# ---------------------------------------------------------------------------


class TestPackagesDirStructure:

    def test_packages_dir_exists(self):
        assert PACKAGES_DIR.is_dir(), "Le répertoire packages/ doit exister"

    @pytest.mark.parametrize("dist", ALL_DISTS)
    def test_dist_dir_exists(self, dist):
        assert (PACKAGES_DIR / dist).is_dir(), f"packages/{dist}/ doit exister"

    @pytest.mark.parametrize("dist", ALL_DISTS)
    def test_dist_has_pyproject_toml(self, dist):
        assert (PACKAGES_DIR / dist / "pyproject.toml").is_file(), (
            f"packages/{dist}/pyproject.toml doit exister"
        )

    @pytest.mark.parametrize("module", OPTIONAL_MODULES)
    def test_optional_dist_has_init(self, module):
        dist = module.replace("_", "-")
        init = PACKAGES_DIR / dist / module / "__init__.py"
        assert init.is_file(), f"packages/{dist}/{module}/__init__.py doit exister"


# ---------------------------------------------------------------------------
# Classe 2 — Métadonnées des pyproject.toml
# ---------------------------------------------------------------------------


class TestPyprojectMetadata:

    def _load(self, dist: str) -> dict:
        path = PACKAGES_DIR / dist / "pyproject.toml"
        return tomllib.loads(path.read_text(encoding="utf-8"))

    @pytest.mark.parametrize("dist", ALL_DISTS)
    def test_name_correct(self, dist):
        data = self._load(dist)
        assert data["project"]["name"] == dist

    @pytest.mark.parametrize("dist", ALL_DISTS)
    def test_version_correct(self, dist):
        data = self._load(dist)
        assert data["project"]["version"] == VERSION

    @pytest.mark.parametrize("dist", ALL_DISTS)
    def test_requires_python_312(self, dist):
        data = self._load(dist)
        assert "3.12" in data["project"]["requires-python"]

    @pytest.mark.parametrize("dist", ALL_DISTS)
    def test_build_system_setuptools(self, dist):
        data = self._load(dist)
        backend = data["build-system"]["build-backend"]
        assert "setuptools" in backend

    @pytest.mark.parametrize("dist", ALL_DISTS)
    def test_description_not_empty(self, dist):
        data = self._load(dist)
        assert data["project"].get("description", "").strip()


# ---------------------------------------------------------------------------
# Classe 3 — Distribution forge-mvc (pyproject.toml racine depuis T2b)
# ---------------------------------------------------------------------------


class TestForgeMvcPackage:
    """forge-mvc est publié depuis le pyproject.toml racine (T2b — T2b)."""

    def _load(self) -> dict:
        return tomllib.loads(ROOT_PYPROJECT.read_text(encoding="utf-8"))

    def test_root_source_uses_where_dot(self):
        data = self._load()
        where = data["tool"]["setuptools"]["packages"]["find"]["where"]
        assert "." in where, "pyproject.toml racine : where doit contenir '.' (build depuis la racine)"

    def test_includes_core(self):
        data = self._load()
        include = data["tool"]["setuptools"]["packages"]["find"]["include"]
        assert any("core" in p for p in include)

    def test_includes_forge_cli(self):
        data = self._load()
        include = data["tool"]["setuptools"]["packages"]["find"]["include"]
        assert any("forge_cli" in p for p in include)

    def test_publishable_extras_declared(self):
        """Apres VERSION-SYNC-OPTIN-EXTRAS-001, les extras rbac/workflow/stats/all sont declares.

        forge-mvc-mfa et forge-mvc-media restent exclus (non publiables).
        """
        data = self._load()
        opts = data["project"].get("optional-dependencies", {})
        for extra in ("rbac", "workflow", "stats", "all"):
            assert extra in opts, (
                f"L'extra [{extra}] doit etre present dans pyproject.toml "
                f"(VERSION-SYNC-OPTIN-EXTRAS-001)."
            )
        for extra in ("mfa", "media"):
            assert extra not in opts, (
                f"L'extra [{extra}] ne doit pas etre present — package non publiable."
            )

    def test_publishable_extras_pin_current_version(self):
        """Les extras publiables épinglent forge-mvc-<nom> sur la version
        courante avec la borne unifiée (OPTIN-DEPS-PIN-B13-001)."""
        data = self._load()
        opts = data["project"].get("optional-dependencies", {})
        for extra in ("rbac", "workflow", "stats"):
            deps = opts.get(extra, [])
            assert any(VERSION in d and ">=" in d for d in deps), (
                f"L'extra [{extra}] doit épingler la version courante "
                f"{VERSION} (forme >=...,<2)."
            )

    def test_has_forge_entrypoint(self):
        data = self._load()
        scripts = data["project"].get("scripts", {})
        assert "forge" in scripts


# ---------------------------------------------------------------------------
# Classe 4 — Placeholders des distributions optionnelles
# ---------------------------------------------------------------------------


class TestOptionalDistPlaceholders:

    @pytest.mark.parametrize("module", OPTIONAL_MODULES)
    def test_init_not_empty(self, module):
        dist = module.replace("_", "-")
        init = PACKAGES_DIR / dist / module / "__init__.py"
        content = init.read_text(encoding="utf-8")
        assert len(content) > 20, f"{module}/__init__.py ne doit pas être vide"

    @pytest.mark.parametrize("module", OPTIONAL_MODULES)
    def test_init_has_docstring(self, module):
        dist = module.replace("_", "-")
        init = PACKAGES_DIR / dist / module / "__init__.py"
        content = init.read_text(encoding="utf-8")
        assert '"""' in content, f"{module}/__init__.py doit avoir une docstring"


# ---------------------------------------------------------------------------
# Classe 5 — Racine pyproject.toml mise à jour
# ---------------------------------------------------------------------------


class TestRootPyprojectUpdated:

    def _load(self) -> dict:
        return tomllib.loads(ROOT_PYPROJECT.read_text(encoding="utf-8"))

    def test_version_bumped(self):
        data = self._load()
        assert data["project"]["version"] == VERSION

    def test_optional_dependencies_declared_for_publishable(self):
        """Apres VERSION-SYNC-OPTIN-EXTRAS-001, [project.optional-dependencies] est present."""
        data = self._load()
        assert "optional-dependencies" in data["project"], (
            "[project.optional-dependencies] doit etre present dans pyproject.toml racine "
            "(extras rbac/workflow/stats/all — VERSION-SYNC-OPTIN-EXTRAS-001)."
        )

    def test_all_extra_excludes_alpha_optins(self):
        """[all] ne tire que rbac/workflow/stats — mfa/media/iot/video exclus
        (Alpha et/ou dépendances spéciales : MQTT, FFmpeg)."""
        data = self._load()
        all_deps = data["project"].get("optional-dependencies", {}).get("all", [])
        for excluded in (
            "forge-mvc-mfa", "forge-mvc-media", "forge-mvc-iot", "forge-mvc-video",
        ):
            assert not any(excluded in d for d in all_deps), (
                f"{excluded} ne doit pas être dans l'extra [all]."
            )

    def test_requires_python_312(self):
        data = self._load()
        assert ">=3.12" in data["project"]["requires-python"]
