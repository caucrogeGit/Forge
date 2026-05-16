"""Tests documentaires — DOC-15MIN-001 : tutoriel "15 minutes avec Forge"."""

from pathlib import Path
import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/15-minutes.md")
MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text():
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/15-minutes.md introuvable"

    def test_fichier_non_vide(self):
        assert len(_text()) > 500

    def test_titre_principal(self):
        text = _text()
        assert "15 minutes" in text and "Forge" in text


# ---------------------------------------------------------------------------
# Sections obligatoires
# ---------------------------------------------------------------------------


class TestSections:
    def test_section_objectif(self):
        text = _text().lower()
        assert "objectif" in text

    def test_section_ce_que_tu_vas_construire(self):
        text = _text().lower()
        assert "construire" in text or "va" in text

    def test_section_prerequis(self):
        text = _text().lower()
        assert "prérequis" in text or "requis" in text

    def test_section_creer_projet(self):
        text = _text().lower()
        assert "créer le projet" in text or "créer un projet" in text

    def test_section_verifier_projet(self):
        text = _text().lower()
        assert "vérif" in text

    def test_section_creer_entite(self):
        text = _text().lower()
        assert "entité" in text and ("créer" in text or "création" in text)

    def test_section_generer_crud(self):
        text = _text().lower()
        assert "crud" in text and ("générer" in text or "génération" in text)

    def test_section_verifier_resultat(self):
        text = _text().lower()
        assert "résultat" in text or "vérif" in text

    def test_section_fichiers_generes(self):
        text = _text().lower()
        assert "fichier" in text and "généré" in text

    def test_section_lancer_application(self):
        text = _text().lower()
        assert "lancer" in text and "application" in text

    def test_section_limites(self):
        text = _text().lower()
        assert "limite" in text

    def test_section_ou_aller_ensuite(self):
        text = _text().lower()
        assert "ensuite" in text or "suite" in text or "aller" in text


# ---------------------------------------------------------------------------
# Commandes Forge
# ---------------------------------------------------------------------------


class TestCommandesForge:
    def test_forge_new(self):
        assert "forge new" in _text()

    def test_forge_doctor(self):
        assert "forge doctor" in _text()

    def test_forge_project_check(self):
        assert "forge project:check" in _text()

    def test_forge_make_entity(self):
        assert "forge make:entity" in _text()

    def test_forge_make_crud(self):
        assert "forge make:crud" in _text()

    def test_forge_project_audit(self):
        assert "forge project:audit" in _text()

    def test_forge_sync_entity(self):
        assert "forge sync:entity" in _text()

    def test_forge_db_init(self):
        assert "forge db:init" in _text()

    def test_python_app_py(self):
        assert "python app.py" in _text()

    def test_no_input_flag(self):
        assert "--no-input" in _text()


# ---------------------------------------------------------------------------
# Entité Contact
# ---------------------------------------------------------------------------


class TestEntiteContact:
    def test_entite_contact_mentionnee(self):
        assert "Contact" in _text()

    def test_json_entite_mentionne(self):
        text = _text()
        assert "Contact.json" in text or ".json" in text

    def test_sql_genere_mentionne(self):
        text = _text()
        assert "Contact.sql" in text or ".sql" in text

    def test_base_py_mentionne(self):
        assert "_base.py" in _text()

    def test_modele_manuel_mentionne(self):
        text = _text().lower()
        assert "manuel" in text or "modèle" in text


# ---------------------------------------------------------------------------
# Fichiers générés vs préservés
# ---------------------------------------------------------------------------


class TestFichiersGeneresPreserves:
    def test_fichiers_generes_mentionnes(self):
        text = _text().lower()
        assert "généré" in text or "régénérable" in text

    def test_fichiers_preserves_mentionnes(self):
        text = _text().lower()
        assert "préservé" in text

    def test_sync_entity_explique(self):
        assert "sync:entity" in _text()

    def test_make_crud_preserve_explique(self):
        text = _text().lower()
        assert "make:crud" in text and "préserv" in text

    def test_json_source_verite(self):
        text = _text().lower()
        assert "source" in text and ("vérité" in text or "json" in text)

    def test_routes_py_mentionne(self):
        assert "routes.py" in _text()

    def test_controller_mentionne(self):
        text = _text().lower()
        assert "contrôleur" in text or "controller" in text

    def test_vues_mentionnees(self):
        text = _text().lower()
        assert "vue" in text or "views" in text or "template" in text


# ---------------------------------------------------------------------------
# Limites
# ---------------------------------------------------------------------------


class TestLimites:
    def test_auth_mentionne_comme_limite(self):
        text = _text().lower()
        assert "auth" in text

    def test_mariadb_requis_mentionne(self):
        text = _text().lower()
        assert "mariadb" in text

    def test_deploiement_hors_scope(self):
        text = _text().lower()
        assert "déploiement" in text or "production" in text

    def test_tutoriel_app_complete_annonce(self):
        text = _text()
        assert "DOC-APP-COMPLETE-001" in text or "application complète" in text.lower()


# ---------------------------------------------------------------------------
# Liens vers d'autres docs
# ---------------------------------------------------------------------------


class TestLiensDocs:
    def test_lien_vers_reference(self):
        text = _text()
        assert "reference.md" in text or "[Référence" in text or "API et CLI" in text

    def test_lien_vers_stability_contract(self):
        text = _text()
        assert "stability-contract.md" in text or "Contrat de stabilité" in text

    def test_lien_vers_deployment(self):
        text = _text()
        assert "deployment.md" in text or "Déploiement" in text

    def test_lien_vers_production_security(self):
        text = _text()
        assert "production-security.md" in text or "production" in text.lower()


# ---------------------------------------------------------------------------
# Mkdocs
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_tutoriel_dans_nav(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "15-minutes.md" in mkdocs

    def test_mkdocs_build_strict(self):
        import subprocess

        result = subprocess.run(
            ["mkdocs", "build", "--strict"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"mkdocs build --strict a échoué :\n{result.stderr}"


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_ticket_livre_dans_roadmap(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-15MIN-001" in text

    def test_ticket_marque_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "DOC-15MIN-001" in line:
                assert "livré" in line.lower() or "terminé" in line.lower(), (
                    f"DOC-15MIN-001 non marqué comme livré : {line}"
                )
                break

    def test_prochaine_priorite_doc_app_complete(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-APP-COMPLETE-001" in text
