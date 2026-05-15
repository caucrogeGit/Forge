"""Tests documentaires — DOC-MODULE-AUTHOR-001 : guide créer un module Forge."""

from pathlib import Path

DOC = Path("docs/module-author-guide.md")
MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text():
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/module-author-guide.md introuvable"

    def test_fichier_non_vide(self):
        assert len(_text()) > 1000

    def test_titre_principal(self):
        text = _text()
        assert "module" in text.lower() and "Forge" in text


# ---------------------------------------------------------------------------
# Sections obligatoires
# ---------------------------------------------------------------------------


class TestSections:
    def test_section_objectif(self):
        assert "Objectif" in _text()

    def test_section_ce_quest_un_module(self):
        text = _text().lower()
        assert "module forge" in text

    def test_section_ce_que_nest_pas_un_module(self):
        text = _text().lower()
        assert "ne doit pas" in text or "ne pas" in text

    def test_section_structure(self):
        text = _text().lower()
        assert "structure" in text

    def test_section_manifeste(self):
        text = _text().lower()
        assert "manifeste" in text

    def test_section_fichiers_installables(self):
        text = _text().lower()
        assert "installable" in text or "fichiers installables" in text

    def test_section_routes(self):
        text = _text().lower()
        assert "routes" in text

    def test_section_templates(self):
        text = _text().lower()
        assert "template" in text or "vue" in text

    def test_section_installation(self):
        text = _text().lower()
        assert "installation" in text

    def test_section_suppression(self):
        text = _text().lower()
        assert "suppression" in text

    def test_section_preservation(self):
        text = _text().lower()
        assert "préservation" in text or "préservé" in text or "conservé" in text

    def test_section_verification(self):
        text = _text().lower()
        assert "vérif" in text

    def test_section_tests(self):
        text = _text().lower()
        assert "tester" in text or "test" in text

    def test_section_bonnes_pratiques(self):
        text = _text().lower()
        assert "bonnes pratiques" in text or "bonne pratique" in text

    def test_section_limites(self):
        text = _text().lower()
        assert "limite" in text

    def test_section_exemple(self):
        text = _text().lower()
        assert "exemple" in text


# ---------------------------------------------------------------------------
# Distinction module / starter / application
# ---------------------------------------------------------------------------


class TestDistinctionTypes:
    def test_module_defini(self):
        text = _text().lower()
        assert "module" in text and "starter" in text

    def test_starter_defini(self):
        text = _text().lower()
        assert "starter" in text

    def test_application_definie(self):
        text = _text().lower()
        assert "application" in text

    def test_difference_expliquee(self):
        text = _text().lower()
        assert "brique" in text or "extension" in text


# ---------------------------------------------------------------------------
# Manifeste
# ---------------------------------------------------------------------------


class TestManifeste:
    def test_module_json_mentionne(self):
        assert "module.json" in _text()

    def test_champ_name_mentionne(self):
        assert '"name"' in _text()

    def test_champ_label_mentionne(self):
        assert '"label"' in _text()

    def test_champ_version_mentionne(self):
        assert '"version"' in _text()

    def test_champ_description_mentionne(self):
        assert '"description"' in _text()

    def test_champ_provides_mentionne(self):
        assert '"provides"' in _text()

    def test_champ_paths_mentionne(self):
        assert '"paths"' in _text()

    def test_valeur_controllers_mentionnee(self):
        assert '"controllers"' in _text()

    def test_valeur_views_mentionnee(self):
        assert '"views"' in _text()

    def test_valeur_routes_mentionnee(self):
        assert '"routes"' in _text()

    def test_valeur_entities_mentionnee(self):
        assert '"entities"' in _text()

    def test_format_version_semver(self):
        text = _text()
        assert "MAJOR.MINOR.PATCH" in text or "0.1.0" in text

    def test_snake_case_name(self):
        text = _text().lower()
        assert "snake_case" in text or "snake" in text


# ---------------------------------------------------------------------------
# Registre et fichiers Forge
# ---------------------------------------------------------------------------


class TestRegistreEtFichiers:
    def test_forge_modules_json_mentionne(self):
        assert "forge_modules.json" in _text()

    def test_module_routes_py_mentionne(self):
        assert "module_routes.py" in _text() or "mvc/module_routes" in _text()

    def test_routes_py_mentionne(self):
        assert "routes.py" in _text()

    def test_marqueurs_routes_mentionnes(self):
        text = _text()
        assert "forge-module-routes" in text or "marqueur" in text.lower()


# ---------------------------------------------------------------------------
# Commandes module
# ---------------------------------------------------------------------------


class TestCommandesModule:
    def test_module_list(self):
        assert "forge module:list" in _text()

    def test_module_install(self):
        assert "forge module:install" in _text()

    def test_module_files(self):
        assert "forge module:files" in _text()

    def test_module_routes(self):
        assert "forge module:routes" in _text()

    def test_module_remove(self):
        assert "forge module:remove" in _text()

    def test_dry_run_mentionne(self):
        assert "--dry-run" in _text()

    def test_project_check_mentionne(self):
        assert "forge project:check" in _text()

    def test_project_audit_mentionne(self):
        assert "forge project:audit" in _text()


# ---------------------------------------------------------------------------
# Installation et suppression
# ---------------------------------------------------------------------------


class TestInstallationSuppression:
    def test_cycle_installation_explique(self):
        text = _text().lower()
        assert "install" in text and "files" in text and "routes" in text

    def test_double_installation_refusee(self):
        text = _text().lower()
        assert "déjà installé" in text or "double installation" in text

    def test_conflit_fichier_existant(self):
        text = _text().lower()
        assert "existe déjà" in text or "conflit" in text

    def test_suppression_regle_centrale(self):
        text = _text().lower()
        assert "supprime" in text and "modif" in text

    def test_fichier_modifie_conserve(self):
        text = _text().lower()
        assert "modifié" in text and "conservé" in text


# ---------------------------------------------------------------------------
# Préservation fichiers utilisateur
# ---------------------------------------------------------------------------


class TestPreservation:
    def test_sha256_ou_hash_mentionne(self):
        text = _text().lower()
        assert "sha256" in text or "hash" in text

    def test_e2e_non_overwrite_ou_test_preservation(self):
        text = _text()
        assert "TestModuleRemovePreservesModified" in text or "préservé" in text.lower()


# ---------------------------------------------------------------------------
# Limites
# ---------------------------------------------------------------------------


class TestLimites:
    def test_pas_de_marketplace(self):
        text = _text().lower()
        assert "marketplace" in text

    def test_pas_de_telechargement_distant(self):
        text = _text().lower()
        assert "distant" in text or "téléchargement" in text

    def test_static_non_copie_auto(self):
        text = _text().lower()
        assert "static" in text

    def test_migrations_hors_perimetre(self):
        text = _text().lower()
        assert "migration" in text


# ---------------------------------------------------------------------------
# Mkdocs
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_guide_dans_nav(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "module-author-guide.md" in mkdocs

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
        assert "DOC-MODULE-AUTHOR-001" in text

    def test_ticket_marque_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "DOC-MODULE-AUTHOR-001" in line:
                assert "livré" in line.lower() or "terminé" in line.lower(), (
                    f"DOC-MODULE-AUTHOR-001 non marqué comme livré : {line}"
                )
                break

    def test_prochaine_priorite_doc_starter_author(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-STARTER-AUTHOR-001" in text
