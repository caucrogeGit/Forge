"""Tests GETTING-STARTED-3.0-001 : ressources d'entrée actualisées pour Forge."""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

ENTRY_FILES = [
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "docs" / "bonjour-forge.md",
    PROJECT_ROOT / "docs" / "guide.md",
    PROJECT_ROOT / "docs" / "app-complete-tutorial.md",
]


class TestStructureIntact:
    """Les 4 ressources d'entrée existent toujours et ont du contenu."""

    @pytest.mark.parametrize("entry_file", ENTRY_FILES, ids=lambda p: p.name)
    def test_entry_file_exists(self, entry_file):
        assert entry_file.exists(), f"{entry_file} doit exister (ressource d'entrée)"

    @pytest.mark.parametrize("entry_file", ENTRY_FILES, ids=lambda p: p.name)
    def test_entry_file_is_not_empty(self, entry_file):
        if not entry_file.exists():
            pytest.skip()
        content = entry_file.read_text(encoding="utf-8")
        assert len(content.strip()) > 100, (
            f"{entry_file} devrait avoir du contenu substantiel (>100 caractères)"
        )


class TestNoObsoletePythonAPI:
    """Les noms français de l'API (LANG-MIGRATION-001) absents des ressources d'entrée."""

    @pytest.mark.parametrize("entry_file", ENTRY_FILES, ids=lambda p: p.name)
    @pytest.mark.parametrize("forbidden", [
        "creer_session",
        "supprimer_session",
        "regenerer_session",
        "authentifier_session",
        "est_authentifie",
        "get_utilisateur",
        "utilisateur_a_role",
        "verifier_mot_de_passe",
        "hacher_mot_de_passe",
        "enregistrer_tentative",
        "DUREE_SESSION",
        "MAX_TENTATIVES",
        "FENETRE_SECONDES",
    ])
    def test_no_french_api_name(self, entry_file, forbidden):
        if not entry_file.exists():
            pytest.skip(f"{entry_file} n'existe pas")
        content = entry_file.read_text(encoding="utf-8")
        assert forbidden not in content, (
            f"{entry_file.name} contient encore '{forbidden}' "
            f"(API française supprimée en LANG-MIGRATION-001)"
        )

    @pytest.mark.parametrize("entry_file", ENTRY_FILES, ids=lambda p: p.name)
    def test_no_oidc_mention(self, entry_file):
        if not entry_file.exists():
            pytest.skip(f"{entry_file} n'existe pas")
        content = entry_file.read_text(encoding="utf-8")
        assert "OIDC" not in content and "oidc" not in content, (
            f"{entry_file.name} mentionne encore OIDC "
            f"(supprimé du dépôt en OIDC-REMOVE-OR-EXTRACT-001)"
        )

    @pytest.mark.parametrize("entry_file", ENTRY_FILES, ids=lambda p: p.name)
    def test_no_cmd_active_commands(self, entry_file):
        if not entry_file.exists():
            pytest.skip(f"{entry_file} n'existe pas")
        content = entry_file.read_text(encoding="utf-8")
        for pattern in ["python cmd/", "cmd/make.py", "cmd/mvc/"]:
            assert pattern not in content, (
                f"{entry_file.name} mentionne encore '{pattern}' "
                f"(cmd/ supprimé en CMD-LEGACY-REMOVE-001)"
            )


class TestModernAPIPresent:
    """README.md mentionne les modules officiels et les ADR attendus."""

    def test_readme_mentions_all_official_modules(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        for module in ["forge-mvc-mfa", "forge-mvc-rbac",
                       "forge-mvc-workflow", "forge-mvc-stats"]:
            assert module in readme, (
                f"README.md devrait mentionner le module {module}"
            )

    def test_readme_mentions_adr_004(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        assert "ADR-004" in readme or "004-core-perimeter" in readme, (
            "README.md devrait référencer ADR-004 (périmètre core minimal)"
        )

    def test_readme_mentions_adr_008(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        assert "ADR-008" in readme or "008-auth-audit" in readme, (
            "README.md devrait référencer ADR-008 (architecture audit)"
        )


class TestVersionBumped:
    """README.md mentionne la version courante et non plus une version 2.x dans le titre."""

    def test_readme_mentions_current_version(self):
        data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        version = data["project"]["version"]
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        major_minor = ".".join(version.split(".")[:2])
        assert major_minor in readme or version in readme, (
            f"README.md devrait mentionner la version courante ({version})"
        )

    def test_readme_title_not_2x(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        title_lines = [line for line in readme.splitlines() if line.startswith("# Forge")]
        for line in title_lines:
            assert "2.5.0" not in line and "2.10.0" not in line, (
                f"Ligne de titre ne doit pas mentionner d'ancienne version 2.x : '{line}'"
            )
