"""Tests — CRUD-FILTER-DOC-001 : conformité documentaire des filtres CRUD.

Vérifie que docs/reference/crud.md documente :

- la convention list.filter=true ;
- les types SQL supportés ;
- les types SQL refusés ;
- les filtres relationnels many_to_one ;
- la recherche q ;
- la pagination ;
- le tri ;
- la compatibilité HTMX ;
- le fallback sans HTMX ;
- la whitelist SQL ;
- les placeholders SQL ;
- les limites explicites des filtres CRUD.

Et que la roadmap est cohérente avec la Phase 13.
"""
from __future__ import annotations

import pathlib
import pytest

pytestmark = pytest.mark.docs

REFERENCE = pathlib.Path("docs/reference/crud.md")
ROADMAP = pathlib.Path("docs/roadmap/forge-roadmap.md")
TUTORIAL = pathlib.Path("docs/guide/app-complete-tutorial.md")


def _ref():
    return REFERENCE.read_text(encoding="utf-8")


def _roadmap():
    return ROADMAP.read_text(encoding="utf-8")


def _tutorial():
    return TUTORIAL.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Convention list.filter
# ---------------------------------------------------------------------------

class TestConventionListFilter:
    def test_list_filter_mentionne(self):
        assert "list.filter" in _ref()

    def test_filter_true_mentionne(self):
        r = _ref()
        assert '"filter": true' in r or "filter: true" in r or "filter=true" in r

    def test_convention_json_documentee(self):
        r = _ref()
        assert '"list"' in r and '"filter"' in r

    def test_section_filtres_simples_presente(self):
        r = _ref()
        assert "filtres simples" in r.lower()


# ---------------------------------------------------------------------------
# Types supportés et refusés
# ---------------------------------------------------------------------------

class TestTypesFiltres:
    def test_varchar_supporte_documente(self):
        assert "VARCHAR" in _ref()

    def test_int_supporte_documente(self):
        r = _ref()
        assert "INT" in r or "Entiers" in r

    def test_bool_supporte_documente(self):
        r = _ref()
        assert "BOOL" in r or "Booléens" in r

    def test_text_refuse_documente(self):
        assert "TEXT" in _ref()

    def test_date_refuse_documente(self):
        assert "DATE" in _ref()

    def test_datetime_refuse_documente(self):
        assert "DATETIME" in _ref()

    def test_decimal_refuse_documente(self):
        assert "DECIMAL" in _ref()

    def test_float_refuse_documente(self):
        assert "FLOAT" in _ref()

    def test_types_refuses_clairement_documentes(self):
        r = _ref()
        assert "non supportés" in r or "refusés" in r or "non supporté" in r


# ---------------------------------------------------------------------------
# Filtres relationnels many_to_one
# ---------------------------------------------------------------------------

class TestFiltresRelationnels:
    def test_many_to_one_filtre_mentionne(self):
        r = _ref()
        assert "many_to_one" in r

    def test_filtres_relationnels_section_presente(self):
        r = _ref()
        assert "filtres relationnels" in r.lower() or "relationnels" in r.lower()

    def test_select_genere_pour_relation_documente(self):
        r = _ref()
        assert "<select" in r and "many_to_one" in r


# ---------------------------------------------------------------------------
# Compatibilité recherche q / tri / pagination
# ---------------------------------------------------------------------------

class TestCompatibiliteQTriPagination:
    def test_q_mentionne(self):
        r = _ref()
        assert "pagination.q" in r or 'paramètre `q`' in r or 'paramètre GET `q`' in r

    def test_pagination_mentionne(self):
        r = _ref()
        assert "pagination" in r.lower()

    def test_tri_mentionne(self):
        r = _ref()
        assert "tri" in r.lower() or "sort" in r

    def test_filtres_conserves_dans_pagination(self):
        r = _ref()
        assert "pagination.filters" in r or "conservés" in r


# ---------------------------------------------------------------------------
# Compatibilité HTMX
# ---------------------------------------------------------------------------

class TestCompatibiliteHTMX:
    def test_htmx_mentionne_dans_section_filtres(self):
        r = _ref()
        # La section filtres simples doit mentionner HTMX
        idx_filtres = r.find("filtres simples")
        assert idx_filtres != -1
        bloc = r[idx_filtres: idx_filtres + 3000]
        assert "HTMX" in bloc or "hx-" in bloc

    def test_hx_get_documente(self):
        r = _ref()
        assert "hx-get" in r

    def test_hx_target_documente(self):
        r = _ref()
        assert "hx-target" in r

    def test_hx_push_url_documente(self):
        r = _ref()
        assert "hx-push-url" in r

    def test_reinitialiser_documente(self):
        r = _ref()
        assert "Réinitialiser" in r

    def test_condition_pagination_filters_documentee(self):
        r = _ref()
        assert "pagination.filters" in r and "pagination.q" in r


# ---------------------------------------------------------------------------
# Fallback sans HTMX
# ---------------------------------------------------------------------------

class TestFallbackSansHTMX:
    def test_fallback_sans_htmx_mentionne(self):
        r = _ref()
        assert "sans HTMX" in r or "sans JavaScript" in r or "HTMX n'est pas obligatoire" in r

    def test_pas_de_js_personnalise_mentionne(self):
        r = _ref()
        assert "JavaScript personnalisé" in r or "JS" in r

    def test_pas_de_recherche_live_mentionnee(self):
        r = _ref()
        assert "recherche live" in r or "live" in r


# ---------------------------------------------------------------------------
# Garanties SQL
# ---------------------------------------------------------------------------

class TestGarantiesSQL:
    def test_whitelist_mentionnee(self):
        r = _ref()
        assert "whitelist" in r.lower() or "_ALLOWED_FILTERS" in r or "allowlist" in r.lower()

    def test_placeholders_mentionnes(self):
        r = _ref()
        assert "paramètres" in r or "?" in r or "paramétr" in r

    def test_injection_impossible_mentionnee(self):
        r = _ref()
        # La doc doit dire qu'une clé inconnue lève une erreur
        assert "ValueError" in r or "Filtre interdit" in r or "injection" in r.lower()

    def test_sql_parametre_mentionne(self):
        r = _ref()
        assert "paramétré" in r or "paramétrées" in r or "aucune concaténation" in r


# ---------------------------------------------------------------------------
# Limites explicites
# ---------------------------------------------------------------------------

class TestLimitesExplicites:
    def test_section_limites_filtres_presente(self):
        r = _ref()
        idx = r.find("Limites des filtres CRUD")
        assert idx != -1, "La section 'Limites des filtres CRUD' doit être présente"

    def test_operateurs_avances_mentionnes(self):
        r = _ref()
        idx = r.find("Limites des filtres CRUD")
        assert idx != -1
        bloc = r[idx: idx + 800]
        assert ">" in bloc or "BETWEEN" in bloc or "opérateurs" in bloc.lower()

    def test_multi_valeurs_mentionnes(self):
        r = _ref()
        idx = r.find("Limites des filtres CRUD")
        assert idx != -1
        bloc = r[idx: idx + 800]
        assert "multi" in bloc.lower() or "valeurs" in bloc.lower()

    def test_plages_dates_mentionnees(self):
        r = _ref()
        idx = r.find("Limites des filtres CRUD")
        assert idx != -1
        bloc = r[idx: idx + 800]
        assert "date" in bloc.lower() or "plage" in bloc.lower()

    def test_pas_de_debounce_mentionne(self):
        r = _ref()
        assert "debounce" in r

    def test_pas_de_recherche_live_mentionne(self):
        r = _ref()
        assert "live" in r or "recherche live" in r


# ---------------------------------------------------------------------------
# Roadmap — Phase 13 et cohérence
# ---------------------------------------------------------------------------

class TestRoadmapPhase13:
    def test_crud_filter_doc_001_livre(self):
        r = _roadmap()
        assert "CRUD-FILTER-DOC-001" in r
        idx = r.find("CRUD-FILTER-DOC-001")
        assert "livré" in r[idx: idx + 80]

    def test_crud_filter_001_livre(self):
        r = _roadmap()
        assert "CRUD-FILTER-001" in r
        idx = r.find("CRUD-FILTER-001")
        assert "livré" in r[idx: idx + 80]

    def test_crud_filter_htmx_001_livre(self):
        r = _roadmap()
        assert "CRUD-FILTER-HTMX-001" in r
        idx = r.find("CRUD-FILTER-HTMX-001")
        assert "livré" in r[idx: idx + 80]

    def test_phase_13_presente(self):
        assert "Phase 13" in _roadmap()

    def test_prochaine_priorite_crud_bulk_actions(self):
        r = _roadmap()
        idx = r.find("Prochaine priorité immédiate")
        assert idx != -1
        bloc = r[idx: idx + 200]
        assert "FORGE-DESIGN-ROADMAP-001" in bloc


# ---------------------------------------------------------------------------
# Tutoriel — mention filtres
# ---------------------------------------------------------------------------

class TestTutoriel:
    def test_tutorial_mentionne_filtres_crud(self):
        t = _tutorial()
        assert "list.filter" in t or "Filtres de liste CRUD" in t or "filtr" in t.lower()
