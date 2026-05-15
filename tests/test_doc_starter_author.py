"""Tests documentaires — DOC-STARTER-AUTHOR-001 : guide créer un starter Forge."""

from pathlib import Path

DOC = Path("docs/starter-author-guide.md")
MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text():
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/starter-author-guide.md introuvable"

    def test_fichier_non_vide(self):
        assert len(_text()) > 1000

    def test_titre_principal(self):
        text = _text()
        assert "starter" in text.lower() and "Forge" in text


# ---------------------------------------------------------------------------
# Sections obligatoires
# ---------------------------------------------------------------------------


class TestSections:
    def test_section_objectif(self):
        assert "Objectif" in _text()

    def test_section_ce_quest_un_starter(self):
        text = _text().lower()
        assert "starter" in text

    def test_section_difference_types(self):
        text = _text().lower()
        assert "module" in text and "starter" in text and "application" in text

    def test_section_ce_que_nest_pas_un_starter(self):
        text = _text().lower()
        assert "ne doit pas" in text or "ne pas" in text

    def test_section_types_starters(self):
        text = _text().lower()
        assert "kind" in text or "type" in text

    def test_section_structure(self):
        text = _text().lower()
        assert "structure" in text

    def test_section_metadonnees(self):
        text = _text().lower()
        assert "métadonnée" in text or "starter.json" in text

    def test_section_entites(self):
        text = _text().lower()
        assert "entité" in text

    def test_section_relations(self):
        text = _text().lower()
        assert "relation" in text

    def test_section_routes(self):
        text = _text().lower()
        assert "route" in text

    def test_section_templates(self):
        text = _text().lower()
        assert "template" in text or "vue" in text

    def test_section_build(self):
        text = _text().lower()
        assert "build" in text

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
# Distinction starter / module / application
# ---------------------------------------------------------------------------


class TestDistinctionTypes:
    def test_module_et_starter_distingues(self):
        text = _text().lower()
        assert "module" in text and "starter" in text

    def test_application_mentionnee(self):
        text = _text().lower()
        assert "application" in text

    def test_difference_clairement_expliquee(self):
        text = _text().lower()
        assert "brique" in text or "base" in text or "reproductible" in text


# ---------------------------------------------------------------------------
# Types de starters
# ---------------------------------------------------------------------------


class TestTypesStarters:
    def test_kind_crud(self):
        assert "crud" in _text().lower() or '"crud"' in _text()

    def test_kind_application(self):
        assert '"application"' in _text() or "kind=application" in _text()

    def test_kind_skeleton(self):
        assert '"skeleton"' in _text() or "kind=skeleton" in _text()


# ---------------------------------------------------------------------------
# Métadonnées starter.json
# ---------------------------------------------------------------------------


class TestMetadonnees:
    def test_starter_json_mentionne(self):
        assert "starter.json" in _text()

    def test_champ_id_mentionne(self):
        assert '"id"' in _text()

    def test_champ_number_mentionne(self):
        assert '"number"' in _text()

    def test_champ_name_mentionne(self):
        assert '"name"' in _text()

    def test_champ_kind_mentionne(self):
        assert '"kind"' in _text()

    def test_champ_aliases_mentionne(self):
        assert '"aliases"' in _text()

    def test_champ_status_mentionne(self):
        assert '"status"' in _text()

    def test_champ_requires_db_mentionne(self):
        assert '"requires_db"' in _text()

    def test_champ_routes_marker_mentionne(self):
        assert '"routes_marker"' in _text()

    def test_champ_check_paths_mentionne(self):
        assert '"check_paths"' in _text()

    def test_champ_home_route_mentionne(self):
        assert '"home_route"' in _text()

    def test_champ_entities_mentionne(self):
        assert '"entities"' in _text()


# ---------------------------------------------------------------------------
# Entités et relations
# ---------------------------------------------------------------------------


class TestEntitesRelations:
    def test_json_canonique_mentionne(self):
        text = _text().lower()
        assert "json canonique" in text or "canonique" in text

    def test_relations_json_mentionne(self):
        assert "relations.json" in _text()

    def test_many_to_one_mentionne(self):
        assert "many_to_one" in _text()

    def test_format_v1_mentionne(self):
        text = _text()
        assert "format_version" in text or "V1" in text


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


class TestRoutes:
    def test_routes_snippet_mentionne(self):
        assert "routes.py.snippet" in _text() or "snippet" in _text().lower()

    def test_marqueurs_routes_mentionnes(self):
        text = _text()
        assert "forge-starter" in text

    def test_routes_marker_unique(self):
        text = _text().lower()
        assert "unique" in text and ("marqueur" in text or "routes_marker" in text)


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------


class TestCommandes:
    def test_starter_list(self):
        assert "forge starter:list" in _text()

    def test_starter_build(self):
        assert "forge starter:build" in _text()

    def test_dry_run(self):
        assert "--dry-run" in _text()

    def test_force(self):
        assert "--force" in _text()

    def test_init_db(self):
        assert "--init-db" in _text()

    def test_project_check(self):
        assert "forge project:check" in _text()

    def test_project_audit(self):
        assert "forge project:audit" in _text()


# ---------------------------------------------------------------------------
# Limites
# ---------------------------------------------------------------------------


class TestLimites:
    def test_pas_de_marketplace(self):
        text = _text().lower()
        assert "marketplace" in text

    def test_pas_de_starter_remove(self):
        text = _text().lower()
        assert "suppression" in text or "remove" in text or "désinstall" in text

    def test_pas_de_mariadb_dans_tests(self):
        text = _text().lower()
        assert "mariadb" in text or "mock" in text or "moquée" in text

    def test_force_ecrase_sans_protection(self):
        text = _text().lower()
        assert "--force" in text and ("écraser" in text or "écrase" in text or "protection" in text)


# ---------------------------------------------------------------------------
# Mkdocs
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_guide_dans_nav(self):
        mkdocs = MKDOCS.read_text(encoding="utf-8")
        assert "starter-author-guide.md" in mkdocs

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
        assert "DOC-STARTER-AUTHOR-001" in text

    def test_ticket_marque_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "DOC-STARTER-AUTHOR-001" in line:
                assert "livré" in line.lower() or "terminé" in line.lower(), (
                    f"DOC-STARTER-AUTHOR-001 non marqué comme livré : {line}"
                )
                break

    def test_prochaine_priorite_doc_deploy_advanced(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-DEPLOY-ADVANCED-001" in text
