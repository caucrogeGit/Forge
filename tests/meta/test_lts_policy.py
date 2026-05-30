"""Tests documentaires — RELEASE-LTS-001 : politique LTS Forge."""

from pathlib import Path
import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/release/lts-policy.md")
MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text():
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/release/lts-policy.md introuvable"

    def test_fichier_non_vide(self):
        assert len(_text()) > 500

    def test_titre_principal(self):
        text = _text()
        assert "LTS" in text and "Forge" in text


# ---------------------------------------------------------------------------
# Sections obligatoires
# ---------------------------------------------------------------------------


class TestSections:
    def test_section_objectif(self):
        assert "## Objectif" in _text()

    def test_section_ce_quest_lts(self):
        text = _text().lower()
        assert "lts" in text and ("ce qu" in text or "définition" in text or "implique" in text)

    def test_section_implications(self):
        text = _text().lower()
        assert "implique" in text

    def test_section_etat_actuel(self):
        text = _text().lower()
        assert "état actuel" in text or "actuel" in text

    def test_section_arguments_pour(self):
        text = _text().lower()
        assert "pour" in text and ("argument" in text or "avantage" in text or "favorable" in text)

    def test_section_arguments_contre(self):
        text = _text().lower()
        assert "contre" in text and ("argument" in text or "limite" in text or "inconvénient" in text)

    def test_section_scenarios(self):
        text = _text().lower()
        assert "scénario" in text

    def test_section_criteres(self):
        text = _text().lower()
        assert "critère" in text

    def test_section_duree_support(self):
        text = _text().lower()
        assert "durée" in text and "support" in text

    def test_section_ce_qui_serait_supporte(self):
        text = _text().lower()
        assert "supporté" in text or "support" in text

    def test_section_ce_qui_serait_exclu(self):
        text = _text().lower()
        assert "exclu" in text

    def test_section_recommandation(self):
        text = _text().lower()
        assert "recommandation" in text

    def test_section_decision(self):
        text = _text().lower()
        assert "décision" in text

    def test_section_tickets_avant_lts(self):
        text = _text().lower()
        assert "ticket" in text and "avant" in text and "lts" in text


# ---------------------------------------------------------------------------
# Contenu LTS
# ---------------------------------------------------------------------------


class TestContenuLts:
    def test_mention_support_long_terme(self):
        text = _text().lower()
        assert "long term" in text or "long terme" in text or "support prolongé" in text

    def test_mention_securite(self):
        text = _text().lower()
        assert "sécurité" in text

    def test_mention_bugs_critiques(self):
        text = _text().lower()
        assert "critique" in text or "bug" in text

    def test_mention_stabilite(self):
        text = _text().lower()
        assert "stabilité" in text or "stable" in text

    def test_mention_fin_de_support(self):
        text = _text().lower()
        assert "fin" in text and "support" in text or "eol" in text.lower()

    def test_mention_maintenance(self):
        text = _text().lower()
        assert "maintenance" in text


# ---------------------------------------------------------------------------
# Arguments pour
# ---------------------------------------------------------------------------


class TestArgumentsPour:
    def test_forge_2_2_0_mentionne(self):
        assert "2.2.0" in _text()

    def test_tests_nombreux_mentionnes(self):
        text = _text()
        assert "test" in text.lower() and ("6 722" in text or "6722" in text)

    def test_politique_release_mentionnee(self):
        text = _text().lower()
        assert "politique de release" in text or "release-policy" in text

    def test_compatibilite_documentee(self):
        text = _text().lower()
        assert "compatibilité" in text and "document" in text


# ---------------------------------------------------------------------------
# Arguments contre
# ---------------------------------------------------------------------------


class TestArgumentsContre:
    def test_api_json_absente(self):
        text = _text().lower()
        assert "api json" in text or "api" in text

    def test_documentation_avancee(self):
        text = _text().lower()
        assert "documentation" in text and ("avancé" in text or "restructur" in text)

    def test_dettes_securite_mentionnees(self):
        text = _text()
        assert "SECURITY-CACHE-001" in text or "CRUD-RBAC-UI-001" in text

    def test_mariadb_ci_absent(self):
        text = _text().lower()
        assert "mariadb" in text and "ci" in text

    def test_sql_versionne_absent(self):
        text = _text().lower()
        assert "sql" in text and ("versionné" in text or "migration" in text)


# ---------------------------------------------------------------------------
# Scénarios
# ---------------------------------------------------------------------------


class TestScenarios:
    def test_au_moins_deux_scenarios(self):
        text = _text()
        count = text.count("Scénario")
        assert count >= 2, f"Moins de 2 scénarios trouvés : {count}"

    def test_scenario_pas_de_lts(self):
        text = _text().lower()
        assert "pas de lts" in text or "scénario a" in text or "pas encore" in text

    def test_scenario_lts_future(self):
        text = _text().lower()
        assert "futur" in text or "candidate" in text

    def test_avantages_mentionnes(self):
        text = _text().lower()
        assert "avantage" in text

    def test_inconvenients_mentionnes(self):
        text = _text().lower()
        assert "inconvénient" in text


# ---------------------------------------------------------------------------
# Décision
# ---------------------------------------------------------------------------


class TestDecision:
    def test_decision_explicite(self):
        text = _text().lower()
        assert "décision" in text

    def test_forge_2_2_0_pas_lts(self):
        text = _text().lower()
        assert "ne déclare pas" in text or "pas encore" in text or "pas de lts" in text

    def test_decision_encadree(self):
        text = _text()
        assert "```" in text and "Décision" in text

    def test_conditions_future_lts(self):
        text = _text().lower()
        assert "après" in text and ("stabilisation" in text or "correction" in text or "création" in text)


# ---------------------------------------------------------------------------
# Tickets à terminer
# ---------------------------------------------------------------------------


class TestTicketsAvantLts:
    def test_doc_structure_mentionne(self):
        assert "DOC-STRUCTURE-001" in _text()

    def test_api_json_mentionne(self):
        assert "API-JSON-001" in _text()

    def test_security_cache_mentionne(self):
        assert "SECURITY-CACHE-001" in _text()

    def test_crud_rbac_ui_mentionne(self):
        assert "CRUD-RBAC-UI-001" in _text()

    def test_e2e_upload_http_mentionne(self):
        assert "E2E-UPLOAD-HTTP-001" in _text()


# ---------------------------------------------------------------------------
# Mkdocs
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_lts_policy_dans_nav(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "lts-policy.md" in mkdocs

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
        assert "RELEASE-LTS-001" in text

    def test_ticket_marque_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "RELEASE-LTS-001" in line:
                assert "livré" in line.lower() or "terminé" in line.lower(), (
                    f"RELEASE-LTS-001 non marqué comme livré : {line}"
                )
                break

    def test_prochaine_priorite_doc_structure(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-STRUCTURE-001" in text
