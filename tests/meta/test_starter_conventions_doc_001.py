"""Garde-fou STARTER-CONVENTIONS-DOC-001.

Vérifie que docs/philosophy/starter-author-guide.md documente les conventions de langage
des starters Forge :
- SQL français possible ;
- API Python en anglais ;
- labels UI en français acceptables ;
- pont SQL → Python explicite ;
- AuthUser et user_loader / build_auth_user ;
- frontière core / starter ;
- référence aux tickets STARTER-CONVENTIONS-DOC-001 et STARTER-LANG-NORMALIZE-001.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GUIDE = PROJECT_ROOT / "docs" / "philosophy" / "starter-author-guide.md"


@pytest.fixture(scope="module")
def guide() -> str:
    assert GUIDE.exists(), f"docs/philosophy/starter-author-guide.md introuvable : {GUIDE}"
    return GUIDE.read_text(encoding="utf-8")


class TestGuideExists:

    def test_fichier_existe(self):
        assert GUIDE.exists()

    def test_fichier_non_vide(self, guide):
        assert len(guide) > 5000

    def test_section_conventions_langage(self, guide):
        assert "Conventions de langage" in guide


class TestSQLFrancaisAutorise:

    def test_sql_francais_mentionne(self, guide):
        lower = guide.lower()
        assert "sql" in lower
        assert "français" in lower or "francais" in lower or "domaine" in lower

    def test_colonnes_sql_non_renommees(self, guide):
        lower = guide.lower()
        assert "renommer" in lower or "migration sql" in lower or "schéma" in lower or "schema" in lower

    def test_exemple_colonne_sql(self, guide):
        assert "UtilisateurId" in guide or "Login" in guide


class TestAPIPythonAnglais:

    def test_api_python_anglais(self, guide):
        lower = guide.lower()
        assert "anglais" in lower

    def test_build_auth_user_mentionne(self, guide):
        assert "build_auth_user" in guide

    def test_normalize_auth_user_mentionne(self, guide):
        assert "normalize_auth_user" in guide

    def test_get_user_by_id_mentionne(self, guide):
        assert "get_user_by_id" in guide


class TestLabelsUI:

    def test_labels_ui_francais_acceptables(self, guide):
        lower = guide.lower()
        assert (
            "label" in lower
            or "interface" in lower
            or "texte" in lower
            or "ui" in lower
        )

    def test_ui_francais_non_interdit(self, guide):
        lower = guide.lower()
        assert (
            "connexion" in lower
            or "mot de passe" in lower
            or "libellé" in lower
            or "label" in lower
        )


class TestPontSQLPython:

    def test_pont_mentionne(self, guide):
        lower = guide.lower()
        assert "pont" in lower or "bridge" in lower or "mapping" in lower or "adaptateur" in lower

    def test_build_auth_user_exemple(self, guide):
        assert "def build_auth_user" in guide

    def test_normalize_auth_user_exemple(self, guide):
        assert "normalize_auth_user" in guide


class TestAuthUserUserLoader:

    def test_auth_user_mentionne(self, guide):
        assert "AuthUser" in guide

    def test_login_user_mentionne(self, guide):
        assert "login_user" in guide

    def test_user_loader_ou_build_auth_user(self, guide):
        assert "user_loader" in guide or "build_auth_user" in guide

    def test_get_authenticated_user_id_mentionne(self, guide):
        assert "get_authenticated_user_id" in guide


class TestFrontiereCoreStarter:

    def test_core_ne_connait_pas_noms_metier(self, guide):
        lower = guide.lower()
        assert "core" in lower
        assert (
            "ne doit" in lower
            or "ne connaît" in lower
            or "ne connait" in lower
            or "générique" in lower
            or "generique" in lower
        )

    def test_motdepasse_non_dans_core(self, guide):
        assert "MotDePasse" in guide or "MotDePasse" in guide

    def test_starter_possede_son_mapping(self, guide):
        lower = guide.lower()
        assert "auth_model" in lower or "modèle" in lower or "model" in lower


class TestTicketsReferences:

    def test_starter_conventions_doc_001(self, guide):
        assert "STARTER-CONVENTIONS-DOC-001" in guide

    def test_starter_lang_normalize_001(self, guide):
        assert "STARTER-LANG-NORMALIZE-001" in guide
