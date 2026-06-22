"""Tests documentaires — DOC-CONTRIBUTE-001 : guide de contribution à Forge."""

from pathlib import Path
import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/philosophy/contributing.md")
MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text():
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/philosophy/contributing.md introuvable"

    def test_fichier_non_vide(self):
        assert len(_text()) > 1000

    def test_titre_principal(self):
        text = _text().lower()
        assert "contribuer" in text and "forge" in text


# ---------------------------------------------------------------------------
# Sections obligatoires
# ---------------------------------------------------------------------------


class TestSections:
    def test_section_objectif(self):
        assert "Objectif" in _text()

    def test_section_philosophie(self):
        text = _text().lower()
        assert "philosophie" in text

    def test_section_environnement(self):
        text = _text().lower()
        assert "environnement" in text

    def test_section_architecture(self):
        text = _text().lower()
        assert "architecture" in text

    def test_section_choisir_ticket(self):
        text = _text().lower()
        assert "ticket" in text

    def test_section_modifier_code(self):
        text = _text().lower()
        assert "modifier le code" in text or "modifier" in text

    def test_section_tests(self):
        text = _text().lower()
        assert "tests" in text or "test" in text

    def test_section_documentation(self):
        text = _text().lower()
        assert "documentation" in text

    def test_section_validations(self):
        text = _text().lower()
        assert "validation" in text

    def test_section_resume_final(self):
        text = _text().lower()
        assert "résumé" in text and ("final" in text or "format" in text)

    def test_section_roadmap(self):
        text = _text().lower()
        assert "roadmap" in text

    def test_section_ce_quil_ne_faut_pas_faire(self):
        text = _text().lower()
        assert "ne faut pas" in text or "interdiction" in text or "à éviter" in text

    def test_section_checklist(self):
        text = _text().lower()
        assert "checklist" in text

    def test_section_exemple(self):
        text = _text().lower()
        assert "exemple" in text


# ---------------------------------------------------------------------------
# Philosophie
# ---------------------------------------------------------------------------


class TestPhilosophie:
    def test_un_ticket_une_responsabilite(self):
        assert "un ticket = une responsabilité" in _text().lower() or \
               "Un ticket = une responsabilité" in _text()

    def test_main_stable(self):
        assert "`main`" in _text() or "main doit rester stable" in _text().lower()

    def test_pas_de_magie(self):
        text = _text().lower()
        assert "magie" in text or "magic" in text or "implicite" in text

    def test_documentation_non_facultative(self):
        text = _text().lower()
        assert "documentée" in text or "non documentée" in text or "documentation est mise à jour" in text


# ---------------------------------------------------------------------------
# Architecture mentionnée
# ---------------------------------------------------------------------------


class TestArchitecture:
    def test_mention_core(self):
        assert "core/" in _text()

    def test_mention_forge_cli(self):
        assert "forge_cli/" in _text()

    def test_mention_docs(self):
        assert "docs/" in _text()

    def test_mention_tests(self):
        assert "tests/" in _text()

    def test_mention_mvc(self):
        assert "mvc/" in _text()


# ---------------------------------------------------------------------------
# Commandes de validation
# ---------------------------------------------------------------------------


class TestValidations:
    def test_pytest(self):
        assert "pytest" in _text()

    def test_compileall(self):
        assert "compileall" in _text()

    def test_ruff_check(self):
        assert "ruff check ." in _text()

    def test_mkdocs_strict(self):
        assert "mkdocs build --strict" in _text()

    def test_git_diff_check(self):
        assert "git diff --check" in _text()


# ---------------------------------------------------------------------------
# Tests MariaDB opt-in
# ---------------------------------------------------------------------------


class TestMariaDBOptIn:
    def test_forge_e2e_mariadb(self):
        assert "FORGE_E2E_MARIADB" in _text()

    def test_forge_e2e_prefix(self):
        assert "forge_e2e_" in _text()

    def test_opt_in_context(self):
        text = _text().lower()
        assert "opt-in" in text or "optionnel" in text or "facultatif" in text


# ---------------------------------------------------------------------------
# Types de tests documentés
# ---------------------------------------------------------------------------


class TestTypesTests:
    def test_tests_unitaires(self):
        text = _text().lower()
        assert "unitaire" in text

    def test_tests_documentaires(self):
        text = _text().lower()
        assert "documentaire" in text

    def test_tests_cli(self):
        text = _text().lower()
        assert "cli" in text

    def test_tests_e2e(self):
        text = _text().lower()
        assert "e2e" in text

    def test_tests_securite(self):
        text = _text().lower()
        assert "sécurité" in text


# ---------------------------------------------------------------------------
# Checklist contributeur
# ---------------------------------------------------------------------------


class TestChecklistContributeur:
    def test_format_checklist(self):
        assert "- [ ]" in _text()

    def test_checklist_tests(self):
        text = _text()
        assert "pytest" in text and "- [ ]" in text

    def test_checklist_roadmap(self):
        text = _text().lower()
        assert "roadmap" in text and "- [ ]" in _text()

    def test_checklist_mkdocs(self):
        text = _text()
        assert "mkdocs.yml" in text and "- [ ]" in text

    def test_checklist_ruff(self):
        text = _text()
        assert "ruff" in text and "- [ ]" in text


# ---------------------------------------------------------------------------
# Résumé final — format attendu
# ---------------------------------------------------------------------------


class TestResumeFormat:
    def test_champ_branche(self):
        assert "Branche" in _text()

    def test_champ_commit(self):
        assert "Commit" in _text()

    def test_champ_tests_ajoutes(self):
        assert "Tests" in _text()

    def test_champ_limites(self):
        assert "Limites" in _text()

    def test_champ_resultats(self):
        assert "Résultats" in _text()

    def test_champ_prochaine_priorite(self):
        assert "Prochaine priorité" in _text()


# ---------------------------------------------------------------------------
# Exemple de contribution
# ---------------------------------------------------------------------------


class TestExempleContribution:
    def test_exemple_doc_module(self):
        assert "DOC-MODULE-AUTHOR-001" in _text()

    def test_etapes_exemple(self):
        text = _text().lower()
        assert "auditer" in text or "audit" in text

    def test_commandes_exemple(self):
        assert "git add" in _text() or "git commit" in _text()


# ---------------------------------------------------------------------------
# Dépendances runtime
# ---------------------------------------------------------------------------


class TestDependancesRuntime:
    def test_mariadb_mentionnee(self):
        assert "mariadb" in _text().lower()

    def test_jinja2_mentionnee(self):
        assert "jinja2" in _text().lower()

    def test_argon2_mentionnee(self):
        text = _text().lower()
        assert "argon2" in text

    # ADR-042 : `pyotp` est une dépendance d'un module opt-in (MFA), pas du core.
    # La doc cœur ne la nomme plus ; le test pyotp a été retiré.


# ---------------------------------------------------------------------------
# Présence dans mkdocs.yml
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_contributing_dans_mkdocs(self):
        assert MKDOCS.exists()
        text = MKDOCS.read_text(encoding="utf-8")
        assert "contributing.md" in text

    def test_label_contribuer(self):
        text = MKDOCS.read_text(encoding="utf-8")
        assert "Contribuer" in text or "contributing" in text.lower()


# ---------------------------------------------------------------------------
# Roadmap — DOC-CONTRIBUTE-001 livré
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_roadmap_existe(self):
        assert ROADMAP.exists()

    def test_doc_contribute_livré(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-CONTRIBUTE-001" in text
        assert "livré" in text

    def test_prochaine_priorite_api_json(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "API-JSON-001" in text
