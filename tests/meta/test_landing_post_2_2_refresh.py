"""Tests — LANDING-POST-2.2-REFRESH-001 : landing page Forge après phases 5 à 10."""

import pathlib
import tomllib
import pytest

pytestmark = pytest.mark.meta

SOURCE_PATH = pathlib.Path("mvc/views/landing/index.html")
DOCS_PATH = pathlib.Path("docs/index.html")

def _current_semver() -> str:
    import re
    v = tomllib.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    return re.sub(r"(\d+\.\d+\.\d+)b(\d+)$", r"\1-beta.\2", v)


def _src():
    return SOURCE_PATH.read_text(encoding="utf-8")


def _docs():
    return DOCS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Source canonique — existence et cohérence
# ---------------------------------------------------------------------------


class TestSourceCanonique:
    def test_source_existe(self):
        assert SOURCE_PATH.exists()

    def test_docs_existe(self):
        assert DOCS_PATH.exists()

    def test_docs_est_genere_depuis_source(self):
        assert "FICHIER GENERE PAR forge sync:landing" in _docs()


# ---------------------------------------------------------------------------
# Slogan et positionnement
# ---------------------------------------------------------------------------


class TestSlogan:
    def test_slogan_principal(self):
        assert "Une forge pour les créer toutes" in _src()

    def test_sous_titre_framework(self):
        assert "Framework web applicatif" in _src()


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
        # Section starter utilisateurs/auth remplace l'ancienne carte Auth/User
        assert "utilisateurs-auth" in _src()

    def test_securite(self):
        assert "Sécurité" in _src() or "sécurité" in _src()

    def test_deploiement(self):
        assert "Déploiement" in _src() or "déploiement" in _src()


# ---------------------------------------------------------------------------
# Apports phases 5 à 10
# ---------------------------------------------------------------------------


class TestApportsRecents:
    def test_securite_renforcee(self):
        src = _src()
        assert "CSRF" in src or "headers" in src or "audit" in src

    def test_auth_user_detail(self):
        src = _src()
        assert "MFA" in src or "argon2" in src or "login" in src

    def test_modules_opt_in_mentionne(self):
        # Les modules opt-in remplacent les briques API JSON / Médias / Mail
        src = _src()
        assert "forge-mvc-mfa" in src or "forge-mvc-rbac" in src

    def test_tests_mentionnes(self):
        src = _src()
        assert "7000" in src or "tests" in src

    def test_documentation_avancee(self):
        src = _src()
        assert "documentation" in src.lower()

    def test_deploiement_avance(self):
        src = _src()
        assert "Nginx" in src or "systemd" in src


# ---------------------------------------------------------------------------
# État actuel mis à jour
# ---------------------------------------------------------------------------


class TestEtatActuel:
    def test_forge_etat_actuel(self):
        assert f"Forge {_current_semver()}" in _src(), (
            f"'Forge {_current_semver()}' doit apparaître dans la landing page."
        )

    def test_phases_recentes_mentionnees(self):
        """Apports phases récentes — phrasing aligné sur la section
        « Aperçu Forge 1.0.0-beta.10 » de la landing actuelle
        (LANDING-PUBLIC-CONTRACT-REALIGN-001)."""
        src = _src()
        assert (
            "CLI plus sûre" in src
            or "Production encadrée" in src
            or "X-Real-IP" in src
            or "Cookies et stores renforcés" in src
            or "Limites explicites" in src
            or "Core autonome préservé" in src
        )

    def test_prochaine_priorite_auth(self):
        # Le starter auth remplace l'ancienne prochaine-priorité Auth/User
        src = _src()
        assert "utilisateurs-auth" in src or "authentification" in src.lower()

    def test_mfa_mentionne(self):
        # forge-mvc-mfa remplace la mention "MFA" ou "OIDC" (OIDC retiré — ADR-004)
        src = _src()
        assert "forge-mvc-mfa" in src


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

    def test_lien_roadmap(self):
        # Lien roadmap remplace "release-policy"
        assert "roadmap" in _src()

    def test_lien_contributing(self):
        assert "contributing" in _src() or "Contribuer" in _src()

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
