"""Tests documentaires — RELEASE-MIGRATION-GUIDE-001 : guide de migration Forge."""

from pathlib import Path
import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/features/migration-guide.md")
MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text():
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/features/migration-guide.md introuvable"

    def test_fichier_non_vide(self):
        assert len(_text()) > 1000

    def test_titre_principal(self):
        assert "Guide de migration" in _text()


# ---------------------------------------------------------------------------
# Sections obligatoires
# ---------------------------------------------------------------------------


class TestSections:
    def test_section_objectif(self):
        assert "## Objectif" in _text()

    def test_section_avant_de_migrer(self):
        text = _text()
        assert "Avant" in text and "migr" in text.lower()

    def test_section_version_actuelle(self):
        text = _text().lower()
        assert "version actuelle" in text or "identifier la version" in text

    def test_section_politique_release(self):
        text = _text().lower()
        assert "politique de release" in text or "release-policy" in text

    def test_section_politique_depreciation(self):
        text = _text().lower()
        assert "dépréciation" in text

    def test_section_compatibilite(self):
        text = _text().lower()
        assert "compatibilité" in text

    def test_section_sauvegarde(self):
        text = _text().lower()
        assert "sauvegarde" in text or "sauvegarder" in text

    def test_section_patch(self):
        assert "## Migration PATCH" in _text() or "PATCH" in _text()

    def test_section_minor(self):
        assert "## Migration MINOR" in _text() or "MINOR" in _text()

    def test_section_major(self):
        assert "## Migration MAJOR" in _text() or "MAJOR" in _text()

    def test_section_fichiers_generes(self):
        text = _text().lower()
        assert "fichier" in text and "généré" in text

    def test_section_fichiers_utilisateur(self):
        text = _text().lower()
        assert "fichier" in text and ("utilisateur" in text or "préservé" in text)

    def test_section_verifications_avant(self):
        text = _text().lower()
        assert "avant" in text and ("vérif" in text or "commandes" in text)

    def test_section_verifications_apres(self):
        text = _text().lower()
        assert "après" in text and ("vérif" in text or "commandes" in text)

    def test_section_depreciation(self):
        text = _text().lower()
        assert "dépréciation" in text

    def test_section_migrations_sql(self):
        text = _text().lower()
        assert "sql" in text and "migr" in text

    def test_section_starters(self):
        text = _text().lower()
        assert "starter" in text

    def test_section_modules(self):
        text = _text().lower()
        assert "module" in text

    def test_section_rollback(self):
        text = _text().lower()
        assert "rollback" in text

    def test_section_checklist(self):
        text = _text().lower()
        assert "checklist" in text

    def test_section_limites(self):
        text = _text().lower()
        assert "limit" in text


# ---------------------------------------------------------------------------
# Commandes DX
# ---------------------------------------------------------------------------


class TestCommandesDX:
    def test_forge_version(self):
        assert "forge --version" in _text()

    def test_forge_doctor(self):
        assert "forge doctor" in _text()

    def test_forge_project_check(self):
        assert "forge project:check" in _text()

    def test_forge_project_audit(self):
        assert "forge project:audit" in _text()

    def test_pytest(self):
        assert "pytest" in _text()

    def test_compileall(self):
        assert "compileall" in _text()

    def test_ruff(self):
        assert "ruff check" in _text()

    def test_git_status(self):
        assert "git status" in _text()


# ---------------------------------------------------------------------------
# Niveaux de migration
# ---------------------------------------------------------------------------


class TestNiveauxMigration:
    def test_patch_explique(self):
        text = _text()
        assert "PATCH" in text and ("correction" in text.lower() or "bug" in text.lower())

    def test_minor_explique(self):
        text = _text()
        assert "MINOR" in text and (
            "fonctionnalité" in text.lower() or "compatible" in text.lower()
        )

    def test_major_explique(self):
        text = _text()
        assert "MAJOR" in text and "rupture" in text.lower()

    def test_exemple_patch(self):
        text = _text()
        # Harmonisé sur la série 1.x, comme les exemples MINOR et MAJEUR :
        # illustrer un PATCH avec 2.2.0 laissait croire à une version 2 de Forge.
        assert "1.2.0" in text and "1.2.1" in text

    def test_exemple_minor(self):
        text = _text()
        assert "1.2.0" in text and "1.3.0" in text

    def test_exemple_major(self):
        text = _text()
        assert "version majeure" in text.lower()

    def test_patch_validation_doctor(self):
        text = _text()
        assert "PATCH" in text and "forge doctor" in text

    def test_minor_validation_audit(self):
        text = _text()
        assert "MINOR" in text and "project:audit" in text

    def test_major_branche_recommandee(self):
        text = _text()
        assert "MAJOR" in text and ("branche" in text.lower() or "branch" in text.lower())


# ---------------------------------------------------------------------------
# Fichiers générés vs préservés
# ---------------------------------------------------------------------------


class TestFichiersGeneres:
    def test_base_py_regenerable(self):
        assert "_base.py" in _text()

    def test_sql_regenerable(self):
        text = _text()
        assert ".sql" in text

    def test_sync_entity_mentionne(self):
        assert "sync:entity" in _text()

    def test_make_crud_preserve(self):
        assert "make:crud" in _text()

    def test_routes_preservees(self):
        text = _text()
        assert "mvc/routes/__init__.py" in text

    def test_non_overwrite_mentionne(self):
        text = _text().lower()
        assert "préserv" in text or "non-overwrite" in text.lower() or "écras" in text

    def test_e2e_non_overwrite_reference(self):
        text = _text()
        assert "E2E-NON-OVERWRITE-001" in text or "non_overwrite" in text.lower()


# ---------------------------------------------------------------------------
# Sauvegarde
# ---------------------------------------------------------------------------


class TestSauvegarde:
    def test_git_commit_mentionne(self):
        text = _text()
        assert "git commit" in text

    def test_mysqldump_mentionne(self):
        text = _text()
        assert "mysqldump" in text

    def test_sauvegarde_avant_sql(self):
        text = _text().lower()
        assert "sauvegarde" in text and "sql" in text

    def test_working_tree_mentionne(self):
        text = _text().lower()
        assert "working tree" in text or "git status" in text


# ---------------------------------------------------------------------------
# Dépréciations
# ---------------------------------------------------------------------------


class TestDepreciations:
    def test_avertissement_cli(self):
        text = _text()
        assert "AVERTISSEMENT" in text or "avertissement" in text.lower()

    def test_deprecation_warning_python(self):
        text = _text()
        assert "DeprecationWarning" in text

    def test_cycle_depreciation(self):
        text = _text().lower()
        assert "annonce" in text and ("maintien" in text or "retrait" in text)

    def test_alternative_recommandee(self):
        text = _text().lower()
        assert "alternative" in text


# ---------------------------------------------------------------------------
# Compatibilité
# ---------------------------------------------------------------------------


class TestCompatibilite:
    def test_python_mentionne(self):
        text = _text()
        assert "Python" in text

    def test_mariadb_mentionne(self):
        text = _text()
        assert "MariaDB" in text

    def test_nodejs_mentionne(self):
        text = _text()
        assert "Node" in text

    def test_lien_matrice_compat(self):
        text = _text()
        assert "compatibility.md" in text or "compatibilité" in text.lower()


# ---------------------------------------------------------------------------
# SQL et rollback
# ---------------------------------------------------------------------------


class TestSqlEtRollback:
    def test_db_init_mentionne(self):
        assert "db:init" in _text()

    def test_db_apply_mentionne(self):
        assert "db:apply" in _text()

    def test_rollback_code(self):
        text = _text().lower()
        assert "rollback" in text

    def test_rollback_base(self):
        text = _text().lower()
        assert "rollback" in text and ("base" in text or "sql" in text)

    def test_rollback_partiel_interdit(self):
        text = _text().lower()
        assert "partiellement" in text or "partiel" in text

    def test_pas_de_rollback_auto_sql(self):
        text = _text().lower()
        assert "manuelle" in text or "manuellement" in text


# ---------------------------------------------------------------------------
# Checklist
# ---------------------------------------------------------------------------


class TestChecklist:
    def test_checklist_avant(self):
        text = _text().lower()
        assert "checklist" in text and "avant" in text

    def test_checklist_apres(self):
        text = _text().lower()
        assert "checklist" in text and "après" in text

    def test_cases_a_cocher(self):
        assert "- [ ]" in _text()

    def test_forge_version_dans_checklist(self):
        text = _text()
        assert "checklist" in text.lower() and "forge --version" in text

    def test_mysqldump_dans_checklist(self):
        text = _text()
        assert "mysqldump" in text


# ---------------------------------------------------------------------------
# Mkdocs
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_migration_guide_dans_nav(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "migration-guide.md" in mkdocs

    def test_mkdocs_build_strict(self, tmp_path):
        import subprocess

        result = subprocess.run(
            ["mkdocs", "build", "--strict", "-d", str(tmp_path / "site")],
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
        assert "RELEASE-MIGRATION-GUIDE-001" in text

    def test_ticket_marque_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        lines = text.splitlines()
        for line in lines:
            if "RELEASE-MIGRATION-GUIDE-001" in line:
                assert "livré" in line.lower() or "terminé" in line.lower(), (
                    f"RELEASE-MIGRATION-GUIDE-001 non marqué comme livré : {line}"
                )
                break

    def test_lts_prochaine_priorite(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "RELEASE-LTS-001" in text
