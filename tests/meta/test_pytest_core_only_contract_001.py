"""Garde-fou PYTEST-CORE-ONLY-DEPS-EXTRAS-001.

Vérifie que tout fichier de tests qui importe au top-level :
- un module Forge opt-in (forge_mvc_mfa, _rbac, _workflow, _stats)
- une dépendance Python d'un extra (ex: pyotp pour MFA)

déclare un pytest.importorskip() correspondant en tête de fichier,
après import pytest.

Sans cette garde, un test peut planter en collecte en environnement
core-only même si le module forge_mvc_* est lui-même bien gardé.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"

# Modules considérés comme « core » (toujours installés via requirements.txt)
CORE_DEPS = {
    "mariadb",
    "dotenv",       # python-dotenv
    "jinja2",
    "PIL",          # Pillow
    "argon2",       # argon2-cffi
    "markupsafe",   # dépendance Jinja2
    "yaml",         # PyYAML
    # Forge lui-même et fichiers applicatifs racine
    "core",
    "mvc",
    "forge",
    "forge_cli",
    "integrations",
    "tests",
    "tools",
    "app",      # app.py racine (fichier applicatif exemple)
    "config",   # config.py racine (configuration applicative exemple)
    # Utilitaires de test
    "_pytest",
    "pytest",
}

# Modules opt-in Forge et leurs dépendances connues
OPTIN_MODULES: dict[str, set[str]] = {
    "forge_mvc_mfa": {"pyotp"},
    "forge_mvc_rbac": set(),
    "forge_mvc_workflow": set(),
    "forge_mvc_stats": set(),
    "forge_mvc_media": set(),
}

EXCLUDED_DIRS = {"history", "audits"}


def _stdlib_modules() -> set[str]:
    return set(sys.stdlib_module_names)


def _test_files() -> list[Path]:
    files = []
    for f in TESTS_DIR.rglob("test_*.py"):
        if any(part in EXCLUDED_DIRS for part in f.parts):
            continue
        files.append(f)
    return sorted(files)


def _top_level_imports(text: str) -> set[str]:
    """Retourne les modules importés au top-level (premier composant uniquement)."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    modules = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                modules.add(node.module.split(".")[0])
    return modules


def _guarded_modules(text: str) -> set[str]:
    """Retourne l'ensemble des modules déclarés via pytest.importorskip()."""
    guarded = set()
    pattern = re.compile(r'importorskip\(\s*["\']([\w.]+)["\']\s*\)')
    for m in pattern.finditer(text):
        guarded.add(m.group(1).split(".")[0])
    return guarded


class TestPytestCoreOnlyContract:

    def test_all_optin_test_files_have_importorskip(self):
        """Tout test qui importe forge_mvc_* au top-level doit le garder."""
        offenders: list[str] = []
        for test_file in _test_files():
            text = test_file.read_text(encoding="utf-8")
            imports = _top_level_imports(text)
            guarded = _guarded_modules(text)
            for module in OPTIN_MODULES:
                if module in imports and module not in guarded:
                    offenders.append(
                        f"{test_file.relative_to(PROJECT_ROOT)} importe "
                        f"`{module}` sans pytest.importorskip"
                    )
        if offenders:
            raise AssertionError(
                f"{len(offenders)} fichier(s) opt-in non gardés :\n"
                + "\n".join(f"  - {o}" for o in offenders)
                + "\n\nAjouter pytest.importorskip(\"forge_mvc_xxx\") après import pytest."
            )

    def test_all_extra_deps_have_importorskip(self):
        """Toute dépendance d'extra (ex: pyotp) importée au top-level doit être gardée."""
        extra_deps: set[str] = set()
        for deps in OPTIN_MODULES.values():
            extra_deps |= deps

        offenders: list[str] = []
        stdlib = _stdlib_modules()
        for test_file in _test_files():
            text = test_file.read_text(encoding="utf-8")
            imports = _top_level_imports(text)
            guarded = _guarded_modules(text)
            for module in imports:
                if module in stdlib or module in CORE_DEPS:
                    continue
                if module in OPTIN_MODULES:
                    continue  # couvert par le test précédent
                if module in extra_deps and module not in guarded:
                    offenders.append(
                        f"{test_file.relative_to(PROJECT_ROOT)} importe "
                        f"`{module}` (dépendance d'extra) sans pytest.importorskip"
                    )

        if offenders:
            raise AssertionError(
                f"{len(offenders)} dépendance(s) d'extra non gardée(s) :\n"
                + "\n".join(f"  - {o}" for o in offenders)
                + "\n\nAjouter pytest.importorskip(\"<module>\") en tête de fichier."
            )

    def test_no_unknown_top_level_imports(self):
        """Détecte les imports top-level inconnus (ni stdlib, ni core, ni extra connu).

        Oblige à classer explicitement chaque dépendance de test dans CORE_DEPS
        ou OPTIN_MODULES. Cela ferme définitivement la catégorie de problème.
        """
        extra_deps: set[str] = set()
        for deps in OPTIN_MODULES.values():
            extra_deps |= deps
        stdlib = _stdlib_modules()
        known = stdlib | CORE_DEPS | set(OPTIN_MODULES.keys()) | extra_deps

        unknown: dict[str, list[str]] = {}
        for test_file in _test_files():
            text = test_file.read_text(encoding="utf-8")
            for module in _top_level_imports(text):
                if module not in known:
                    unknown.setdefault(module, []).append(
                        str(test_file.relative_to(PROJECT_ROOT))
                    )

        if unknown:
            msg = "Modules top-level inconnus dans les tests :\n"
            for module, files in sorted(unknown.items()):
                msg += f"  - {module} ({len(files)} fichier(s))\n"
            msg += (
                "\nClasser ces modules dans CORE_DEPS ou OPTIN_MODULES "
                "dans test_pytest_core_only_contract_001.py."
            )
            raise AssertionError(msg)
