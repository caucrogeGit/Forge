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
    # CORE-DROP-PILLOW-001 (ADR-018) : Pillow a quitté les dépendances DÉCLARÉES
    # du core (pyproject/requirements) au profit de l'opt-in forge-mvc-images.
    # On garde néanmoins "PIL" comme module *disponible en environnement de
    # test* : dans le monorepo, forge-mvc-images (donc Pillow) est toujours sur
    # le sys.path via conftest.py. PIL n'est donc pas un module opt-in
    # susceptible d'être absent pendant `pytest` ; les tests qui construisent
    # des fixtures image peuvent l'importer sans importorskip.
    "PIL",
    "argon2",       # argon2-cffi
    "markupsafe",   # dépendance Jinja2
    "yaml",         # PyYAML
    # Forge lui-même et fichiers applicatifs racine
    "core",
    "mvc",
    "forge",
    "cli",
    "integrations",
    "skeleton",
    "tests",
    "forge_mvc_testing",  # infra de test partagée dev-only (ADR-041)
    # ADR-070 (extraction en cours) : le moteur d'entités a quitté `cli/entities`
    # pour l'opt-in `forge-mvc-entities`, installé en éditable dans le monorepo
    # (toujours sur le sys.path en test, comme PIL ci-dessus). Ses tests vivent
    # encore dans `tests/` ; ils migrent dans le paquet en phase 6, où
    # `forge_mvc_entities` sera reclassé en OPTIN_MODULES avec importorskip.
    "forge_mvc_entities",
    "tools",
    "app",      # app.py racine (fichier applicatif exemple)
    "config",   # config.py racine (configuration applicative exemple)
    # Utilitaires de test
    "_pytest",
    "pytest",
    # Validation JSON Schema (utilisé dans test_docs_json_examples_001.py)
    "jsonschema",
    "referencing",
}

# Modules opt-in Forge et leurs dépendances connues
OPTIN_MODULES: dict[str, set[str]] = {
    # `cryptography` est utilisé pour le chiffrement Fernet des secrets TOTP
    # (cf MFA-SECRET-KEY-BOOT-VALIDATION-001) ; les tests qui le tirent au
    # niveau module sont gardés par `pytest.importorskip("cryptography")`.
    "forge_mvc_mfa": {"pyotp", "cryptography"},
    "forge_mvc_rbac": set(),
    "forge_mvc_workflow": set(),
    "forge_mvc_stats": set(),
    # forge-mvc-images : opt-in propriétaire du traitement d'image (Pillow)
    # depuis IMAGES-MOVE-PROCESSING-001 (ADR-018). Pillow reste classé comme
    # module disponible en test (CORE_DEPS ci-dessus, cf. CORE-DROP-PILLOW-001) ;
    # pas d'extra à lister ici.
    "forge_mvc_images": set(),
    # forge-mvc-iot : opt-in au même titre que ses frères. Ses tests
    # gardent l'import via pytest.importorskip("forge_mvc_iot").
    # `paho-mqtt` n'est jamais importé au top-level des tests (clients
    # injectés / import paresseux), donc pas de dépendance d'extra à lister.
    "forge_mvc_iot": set(),
    # forge-mvc-video : opt-in. Ses tests gardent l'import via
    # pytest.importorskip("forge_mvc_video"). ffmpeg/ffprobe ne sont jamais
    # importés (binaires système, runners injectés), donc pas d'extra à lister.
    "forge_mvc_video": set(),
    # forge-mvc-audio : opt-in. Ses tests gardent l'import via
    # pytest.importorskip("forge_mvc_audio"). ffmpeg/ffprobe ne sont jamais
    # importés (binaires système, runners injectés), donc pas d'extra à lister.
    "forge_mvc_audio": set(),
    # forge-mvc-files : opt-in propriétaire de l'upload générique (ADR-019).
    # Squelette à ce stade ; ses tests gardent l'import via importorskip.
    "forge_mvc_files": set(),
    # forge-mvc-mail : mail extrait du core (ADR-022). jinja2 est une dep
    # core (templating), donc pas d'extra a lister ici.
    "forge_mvc_mail": set(),
    # forge-mvc-i18n : i18n extrait du core (ADR-027). aucune dep tierce.
    "forge_mvc_i18n": set(),
    # forge-mvc-sessions-db : store de session persistant (ADR-054). Ses tests
    # d'intégration gardent l'import via pytest.importorskip("forge_mvc_sessions_db")
    # et sont marqués `db` (sautés sans base). Adossé au backend BDD core, pas
    # d'extra tiers à lister.
    "forge_mvc_sessions_db": set(),
    # forge-mvc-fixtures : données de démo/test (ADR-074/076). Ses tests
    # d'intégration db gardent l'import via importorskip. Faker (dépendance de
    # l'opt-in) n'est jamais importé au top-level des tests du cœur (import
    # paresseux dans Factory), donc pas d'extra à lister.
    "forge_mvc_fixtures": set(),
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
