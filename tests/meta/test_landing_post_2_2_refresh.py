"""Tests — LANDING-POST-2.2-REFRESH-001 : landing page Forge après phases 5 à 10."""

import pathlib
import tomllib
import pytest

pytestmark = pytest.mark.meta

SOURCE_PATH = pathlib.Path("docs/index.html")
DOCS_PATH = pathlib.Path("docs/index.html")

def _current_semver() -> str:
    import re
    v = tomllib.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    v = re.sub(r"(\d+\.\d+\.\d+)a(\d+)$", r"\1-alpha.\2", v)
    v = re.sub(r"(\d+\.\d+\.\d+)b(\d+)$", r"\1-beta.\2", v)
    v = re.sub(r"(\d+\.\d+\.\d+)rc(\d+)$", r"\1-rc.\2", v)
    return v


def _src():
    return SOURCE_PATH.read_text(encoding="utf-8")


def _docs():
    return DOCS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Source canonique — existence et cohérence
# ---------------------------------------------------------------------------


class TestSourceCanonique:
    def test_docs_existe(self):
        assert DOCS_PATH.exists()


# ---------------------------------------------------------------------------
# Slogan et positionnement
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------


class TestVersion:
    def test_version_courante_presente(self):
        assert _current_semver() in _src(), (
            f"La version courante {_current_semver()!r} doit apparaître dans la landing page."
        )

    def test_version_1_5_absente(self):
        assert "1.5.0" not in _src()


# ---------------------------------------------------------------------------
# Briques du core
# ---------------------------------------------------------------------------


class TestBriquesCore:
    def test_mvc(self):
        assert "MVC" in _src()

    def test_crud(self):
        assert "CRUD" in _src()

    def test_rbac(self):
        # "forge-mvc-rbac" remplace la carte "RBAC" (LANDING-BETA6-MENU-001)
        assert "forge-mvc-rbac" in _src()

    def test_auth_user(self):
        # Refonte landing : la carte de fonctionnalité « Auth/User » représente
        # l'authentification (la carte starter users-core-auth a été retirée).
        assert "Auth/User" in _src()

    def test_securite(self):
        assert "Sécurité" in _src() or "sécurité" in _src()

    def test_deploiement(self):
        assert "Déploiement" in _src() or "déploiement" in _src()


# ---------------------------------------------------------------------------
# Liens vers documentation
# ---------------------------------------------------------------------------


class TestLiens:
    def test_lien_getting_started(self):
        # "getting-started" remplace les anciens liens "15-minutes" et "app-complete"
        assert "getting-started" in _src() or "guide" in _src()

    def test_lien_starters(self):
        # Section Starters progressive remplace "app-complete-tutorial"
        assert "starters" in _src()

    def test_lien_reference(self):
        assert "reference" in _src() or "référence" in _src().lower()

    def test_lien_deploiement(self):
        # Lien déploiement remplace "production-security" et "api-json"
        assert "deployment" in _src() or "déploiement" in _src().lower()

    # La landing n'expose plus de lien « Contribuer »/contributing depuis la
    # refonte des cartes (page d'entrée orientée usage, pas contribution).
    # Garde-fou retiré volontairement : voir LANDING-INSTALL-CARDS-001.

    def test_lien_github(self):
        assert "github.com/caucrogeGit/Forge" in _src()


# ---------------------------------------------------------------------------
# Roadmap — LANDING-POST-2.2-REFRESH-001 livré
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_ticket_livre(self):
        roadmap = pathlib.Path("docs/roadmap/forge-roadmap.md").read_text(encoding="utf-8")
        assert "LANDING-POST-2.2-REFRESH-001" in roadmap
        idx = roadmap.index("LANDING-POST-2.2-REFRESH-001")
        bloc = roadmap[idx: idx + 120]
        assert "livré" in bloc or "terminé" in bloc
