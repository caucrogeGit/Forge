"""Tests documentaires — DOC-APP-COMPLETE-001 : tutoriel application complète."""

from pathlib import Path
import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/guide/app-complete-tutorial.md")
MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text():
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/guide/app-complete-tutorial.md introuvable"

    def test_fichier_non_vide(self):
        assert len(_text()) > 1000

    def test_titre_principal(self):
        text = _text()
        assert "Tutoriel" in text and "Forge" in text

    def test_application_complete_mentionnee(self):
        text = _text().lower()
        assert "application" in text and ("complète" in text or "complet" in text)


# ---------------------------------------------------------------------------
# Sections obligatoires
# ---------------------------------------------------------------------------


class TestSections:
    def test_section_objectif(self):
        assert "Objectif" in _text()

    def test_section_ce_que_tu_vas_construire(self):
        text = _text().lower()
        assert "construire" in text

    def test_section_prerequis(self):
        text = _text().lower()
        assert "prérequis" in text or "requis" in text

    def test_section_creer_projet(self):
        text = _text().lower()
        assert "créer le projet" in text or "créer un projet" in text

    def test_section_verifier_projet(self):
        text = _text().lower()
        assert "vérif" in text

    def test_section_creer_entite_ville(self):
        text = _text().lower()
        assert "entité ville" in text or "l'entité ville" in text or "entity ville" in text.lower()

    def test_section_creer_entite_contact(self):
        text = _text().lower()
        assert "entité contact" in text or "l'entité contact" in text

    def test_section_relation(self):
        text = _text().lower()
        assert "relation" in text

    def test_section_generer_crud(self):
        text = _text().lower()
        assert "crud" in text and ("générer" in text or "génération" in text)

    def test_section_verifier_structure(self):
        text = _text().lower()
        assert "structure" in text and "vérif" in text

    def test_section_fichiers_generes(self):
        text = _text().lower()
        assert "fichier" in text and "généré" in text

    def test_section_fichiers_preserves(self):
        text = _text().lower()
        assert "préservé" in text

    def test_section_lancer_application(self):
        text = _text().lower()
        assert "lancer" in text and "application" in text

    def test_section_limites(self):
        text = _text().lower()
        assert "limite" in text

    def test_section_aller_plus_loin(self):
        text = _text().lower()
        assert "aller plus loin" in text or "voir aussi" in text or "ensuite" in text


# ---------------------------------------------------------------------------
# Entités documentées
# ---------------------------------------------------------------------------


class TestEntites:
    def test_entite_ville_mentionnee(self):
        assert "Ville" in _text()

    def test_entite_contact_mentionnee(self):
        assert "Contact" in _text()

    def test_json_ville_mentionne(self):
        assert "ville.json" in _text()

    def test_json_contact_mentionne(self):
        assert "contact.json" in _text()

    def test_sql_ville_mentionne(self):
        assert "ville.sql" in _text()

    def test_sql_contact_mentionne(self):
        assert "contact.sql" in _text()

    def test_base_py_ville_mentionne(self):
        assert "ville_base.py" in _text()

    def test_base_py_contact_mentionne(self):
        assert "contact_base.py" in _text()

    def test_champ_ville_id_mentionne(self):
        assert "ville_id" in _text()

    def test_table_villes_mentionnee(self):
        assert "villes" in _text()

    def test_table_contacts_mentionnee(self):
        assert "contacts" in _text()


# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------


class TestRelations:
    def test_relations_json_mentionne(self):
        assert "relations.json" in _text()

    def test_relations_sql_mentionne(self):
        assert "relations.sql" in _text()

    def test_many_to_one_mentionne(self):
        assert "many_to_one" in _text()

    def test_from_canonique_mentionne(self):
        assert '"from"' in _text() or "'from'" in _text() or "source (`from`)" in _text()

    def test_to_canonique_mentionne(self):
        assert '"to"' in _text() or "'to'" in _text() or "cible (`to`)" in _text()

    def test_foreign_key_mentionne(self):
        text = _text().lower()
        assert "foreign_key" in text or "clé étrangère" in text

    def test_on_delete_mentionne(self):
        assert "on_delete" in _text() or "ON DELETE" in _text()


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

    def test_forge_project_audit(self):
        assert "forge project:audit" in _text()

    def test_forge_make_entity_ville(self):
        assert "forge make:entity Ville" in _text()

    def test_forge_make_entity_contact(self):
        assert "forge make:entity Contact" in _text()

    def test_forge_build_model(self):
        # Workflow canonique (ADR : make:entity -> build:model -> db:init -> make:crud).
        assert "forge build:model" in _text()

    def test_forge_make_relation(self):
        assert "forge make:relation" in _text()

    def test_forge_sync_relations_mentionnee(self):
        # sync:relations reste citée comme variante de régénération ciblée.
        assert "forge sync:relations" in _text()

    def test_forge_make_crud_ville(self):
        assert "forge make:crud Ville" in _text()

    def test_forge_make_crud_contact(self):
        assert "forge make:crud Contact" in _text()

    def test_forge_db_init(self):
        assert "forge db:init" in _text()

    def test_forge_run(self):
        assert "forge run" in _text()

    def test_no_input_flag(self):
        assert "--no-input" in _text()


# ---------------------------------------------------------------------------
# Fichiers générés vs préservés
# ---------------------------------------------------------------------------


class TestFichiersGeneresPreserves:
    def test_regle_centrale_presente(self):
        text = _text()
        assert "sync:entity" in text and "régénérable" in text

    def test_sync_relations_explique(self):
        assert "sync:relations" in _text()

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

    def test_formulaire_mentionne(self):
        text = _text().lower()
        assert "formulaire" in text or "form" in text

    def test_complementarite_check_audit_expliquee(self):
        text = _text().lower()
        assert "project:check" in text and "project:audit" in text and "complément" in text


# ---------------------------------------------------------------------------
# Limites
# ---------------------------------------------------------------------------


class TestLimites:
    def test_auth_mentionne_comme_limite(self):
        text = _text().lower()
        assert "auth" in text

    def test_deploiement_hors_scope(self):
        text = _text().lower()
        assert "déploiement" in text or "production" in text

    def test_api_json_hors_scope(self):
        text = _text().lower()
        assert "api" in text

    def test_mariadb_requis_mentionne(self):
        text = _text().lower()
        assert "mariadb" in text

    def test_stability_contract_reference(self):
        text = _text()
        assert "stability-contract.md" in text or "Contrat de stabilité" in text


# ---------------------------------------------------------------------------
# Mkdocs
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_tutoriel_dans_nav(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "app-complete-tutorial.md" in mkdocs

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
        assert "DOC-APP-COMPLETE-001" in text

    def test_ticket_marque_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "DOC-APP-COMPLETE-001" in line:
                assert "livré" in line.lower() or "terminé" in line.lower(), (
                    f"DOC-APP-COMPLETE-001 non marqué comme livré : {line}"
                )
                break

    def test_prochaine_priorite_doc_module_author(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-MODULE-AUTHOR-001" in text
