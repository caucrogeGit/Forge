"""Tests — LANDING-POST-2.2-REFRESH-001 : landing page Forge après phases 5 à 10."""

import pathlib

SOURCE_PATH = pathlib.Path("mvc/views/landing/index.html")
DOCS_PATH = pathlib.Path("docs/index.html")


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
    def test_version_3_0_0_presente(self):
        assert "1.0.0-beta.1" in _src()

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
        assert "RBAC" in _src()

    def test_auth_user(self):
        assert "Auth/User" in _src()

    def test_media(self):
        assert "Médias" in _src() or "médias" in _src()

    def test_mail(self):
        assert "Mail" in _src()

    def test_api_json(self):
        assert "API JSON" in _src()

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

    def test_api_json_detail(self):
        src = _src()
        assert "Bearer" in src or "json_response" in src or "endpoints JSON" in src

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
    def test_forge_3_0_0_etat(self):
        assert "Forge 1.0.0-beta.1" in _src()

    def test_phases_recentes_mentionnees(self):
        src = _src()
        assert ("DX" in src or "E2E" in src or "sécurité renforcée" in src
                or "documentation avancée" in src)

    def test_prochaine_priorite_auth(self):
        src = _src()
        assert "Auth/User" in src

    def test_mfa_ou_oidc_mentionne(self):
        src = _src()
        assert "MFA" in src or "OIDC" in src


# ---------------------------------------------------------------------------
# Liens vers documentation
# ---------------------------------------------------------------------------


class TestLiens:
    def test_lien_15min(self):
        assert "15-minutes" in _src() or "15 min" in _src()

    def test_lien_app_complete(self):
        assert "app-complete-tutorial" in _src() or "application complète" in _src().lower()

    def test_lien_reference(self):
        assert "reference" in _src() or "référence" in _src().lower()

    def test_lien_api_json(self):
        assert "api-json" in _src()

    def test_lien_securite_production(self):
        assert "production-security" in _src() or "sécurité production" in _src().lower()

    def test_lien_release(self):
        assert "release-policy" in _src() or "Release" in _src()

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
