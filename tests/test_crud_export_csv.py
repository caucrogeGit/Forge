"""Tests — CRUD-EXPORT-CSV-001 : export CSV minimal dans les listes CRUD générées."""
from __future__ import annotations

import pathlib
import pytest


from cli.entities.crud.context import CrudManyToOneRelation
from cli.entities.crud.controller_builder import build_controller
from cli.entities.crud.model_builder import build_model
from cli.entities.crud.views_builder import build_index_view
from cli.entities.make_crud import _route_block

ROADMAP = pathlib.Path("docs/roadmap/forge-roadmap.md")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity_simple():
    return {
        "entity": "Article",
        "table": "articles",
        "fields": [
            {"name": "id", "column": "id", "primary_key": True, "sql_type": "INT"},
            {"name": "titre", "column": "titre", "sql_type": "VARCHAR(255)"},
            {"name": "contenu", "column": "contenu", "sql_type": "TEXT"},
        ],
    }


def _entity_with_filter():
    return {
        "entity": "Article",
        "table": "articles",
        "fields": [
            {"name": "id", "column": "id", "primary_key": True, "sql_type": "INT"},
            {"name": "titre", "column": "titre", "sql_type": "VARCHAR(255)"},
            {"name": "statut", "column": "statut", "sql_type": "VARCHAR(50)", "list": {"filter": True}},
        ],
    }


def _entity_with_relation():
    return {
        "entity": "Contact",
        "table": "contacts",
        "fields": [
            {"name": "id", "column": "id", "primary_key": True, "sql_type": "INT"},
            {"name": "nom", "column": "nom", "sql_type": "VARCHAR(100)"},
            {"name": "client_id", "column": "client_id", "sql_type": "INT"},
        ],
    }


def _rel_client():
    return CrudManyToOneRelation(
        field_name="client_id",
        field_column="client_id",
        target_entity="Client",
        target_table="clients",
        target_pk_column="id",
        target_label_column="nom",
        choices_function="get_client_choices",
        choices_key="client_id_choices",
    )


def _entity_with_rbac():
    return {
        "entity": "Article",
        "table": "articles",
        "fields": [
            {"name": "id", "column": "id", "primary_key": True, "sql_type": "INT"},
            {"name": "titre", "column": "titre", "sql_type": "VARCHAR(255)"},
        ],
        "rbac": {"permissions": {"index": "article.index", "store": "article.store"}},
    }


def _ctrl(definition=None, relations=None):
    return build_controller(definition or _entity_simple(), relations=relations)


def _model(definition=None):
    return build_model(definition or _entity_simple())


def _index_html(definition=None, relations=None):
    return build_index_view(definition or _entity_simple(), relations=relations)


def _routes(definition=None):
    return _route_block(definition or _entity_simple())


def _roadmap():
    return ROADMAP.read_text(encoding="utf-8")


def _livre(ticket: str) -> bool:
    r = _roadmap()
    start = 0
    while True:
        idx = r.find(ticket, start)
        if idx == -1:
            return False
        if "livré" in r[idx: idx + 80]:
            return True
        start = idx + 1


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

class TestRoute:
    def test_route_export_csv_presente(self):
        assert "/export-csv" in _routes()

    def test_route_export_csv_methode_get(self):
        r = _routes()
        idx = r.find("/export-csv")
        bloc = r[max(0, idx - 30): idx + 60]
        assert "GET" in bloc

    def test_route_export_csv_appelle_export_csv(self):
        r = _routes()
        assert "export_csv" in r

    def test_route_export_csv_nom(self):
        r = _routes()
        assert "article-export_csv" in r


# ---------------------------------------------------------------------------
# Modèle : _EXPORT_LIMIT et find_{plural}_for_export
# ---------------------------------------------------------------------------

class TestModele:
    def test_export_limit_presente(self):
        assert "_EXPORT_LIMIT = 1000" in _model()

    def test_find_for_export_presente(self):
        assert "def find_articles_for_export" in _model()

    def test_find_for_export_reutilise_paginated(self):
        m = _model()
        idx = m.find("def find_articles_for_export")
        bloc = m[idx: idx + 300]
        assert "find_articles_paginated" in bloc

    def test_find_for_export_offset_zero(self):
        m = _model()
        idx = m.find("def find_articles_for_export")
        bloc = m[idx: idx + 300]
        assert "offset=0" in bloc

    def test_find_for_export_utilise_export_limit(self):
        m = _model()
        idx = m.find("def find_articles_for_export")
        bloc = m[idx: idx + 300]
        assert "_EXPORT_LIMIT" in bloc

    def test_find_for_export_accept_q_sort_direction_filters(self):
        m = _model()
        idx = m.find("def find_articles_for_export")
        signature = m[idx: idx + 100]
        assert "q=" in signature
        assert "sort=" in signature
        assert "direction=" in signature
        assert "filters=" in signature

    def test_export_limit_avant_find_for_export(self):
        m = _model()
        assert m.index("_EXPORT_LIMIT") < m.index("def find_articles_for_export")


# ---------------------------------------------------------------------------
# Contrôleur : imports
# ---------------------------------------------------------------------------

class TestControleurImports:
    def test_import_csv(self):
        assert "import csv" in _ctrl()

    def test_import_io(self):
        assert "import io" in _ctrl()

    def test_import_response(self):
        assert "from core.http.response import Response" in _ctrl()

    def test_import_find_for_export(self):
        assert "find_articles_for_export" in _ctrl()

    def test_imports_standards_avant_tiers(self):
        c = _ctrl()
        assert c.index("import csv") < c.index("from core.http.response")


# ---------------------------------------------------------------------------
# Contrôleur : _CSV_COLS
# ---------------------------------------------------------------------------

class TestCSVCols:
    def test_csv_cols_presente(self):
        assert "_CSV_COLS" in _ctrl()

    def test_csv_cols_contient_titre(self):
        c = _ctrl()
        idx = c.find("_CSV_COLS")
        bloc = c[idx: idx + 200]
        assert "Titre" in bloc

    def test_csv_cols_contient_contenu(self):
        c = _ctrl()
        idx = c.find("_CSV_COLS")
        bloc = c[idx: idx + 200]
        assert "Contenu" in bloc

    def test_csv_cols_pas_de_pk(self):
        c = _ctrl()
        idx = c.find("_CSV_COLS")
        bloc = c[idx: idx + 200]
        # 'id' field should not appear as a header — only non-PK fields
        # (note: 'id' could appear as part of other words, check pair format)
        assert "('Id'" not in bloc and '("Id"' not in bloc

    def test_csv_cols_relation_utilise_label(self):
        c = build_controller(_entity_with_relation(), relations=[_rel_client()])
        idx = c.find("_CSV_COLS")
        bloc = c[idx: idx + 200]
        assert "client_id_label" in bloc

    def test_csv_cols_champ_simple_utilise_colonne(self):
        c = _ctrl()
        idx = c.find("_CSV_COLS")
        bloc = c[idx: idx + 200]
        assert "'titre'" in bloc or '"titre"' in bloc

    def test_csv_cols_avant_classe(self):
        c = _ctrl()
        assert c.index("_CSV_COLS") < c.index("class ArticleController")


# ---------------------------------------------------------------------------
# Contrôleur : _csv_escape
# ---------------------------------------------------------------------------

class TestCSVEscape:
    def test_csv_escape_presente(self):
        assert "_csv_escape" in _ctrl()

    def test_csv_escape_prefixe_egal(self):
        c = _ctrl()
        idx = c.find("def _csv_escape")
        bloc = c[idx: idx + 300]
        assert '"="' in bloc or "'='" in bloc

    def test_csv_escape_prefixe_plus(self):
        c = _ctrl()
        idx = c.find("def _csv_escape")
        bloc = c[idx: idx + 300]
        assert '"+"' in bloc or "'+'" in bloc

    def test_csv_escape_prefixe_moins(self):
        c = _ctrl()
        idx = c.find("def _csv_escape")
        bloc = c[idx: idx + 300]
        assert '"-"' in bloc or "'-'" in bloc

    def test_csv_escape_prefixe_arobase(self):
        c = _ctrl()
        idx = c.find("def _csv_escape")
        bloc = c[idx: idx + 300]
        assert '"@"' in bloc or "'@'" in bloc

    def test_csv_escape_ajoute_apostrophe(self):
        c = _ctrl()
        idx = c.find("def _csv_escape")
        bloc = c[idx: idx + 300]
        assert "\"'\"" in bloc or "\"'\" +" in bloc


# ---------------------------------------------------------------------------
# Contrôleur : méthode export_csv
# ---------------------------------------------------------------------------

class TestExportCsvMethode:
    def test_export_csv_presente(self):
        assert "def export_csv" in _ctrl()

    def test_export_csv_appelle_find_for_export(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 800]
        assert "find_articles_for_export" in bloc

    def test_export_csv_utilise_csv_writer(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 800]
        assert "csv.writer" in bloc

    def test_export_csv_quote_all(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 800]
        assert "QUOTE_ALL" in bloc

    def test_export_csv_encode_utf8(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 800]
        assert 'encode("utf-8")' in bloc or "encode('utf-8')" in bloc

    def test_export_csv_retourne_response(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        # Fenêtre étendue pour absorber l'annotation `-> Response:` qui
        # rallonge la signature (DX-TYPED-SKELETONS-001).
        bloc = c[idx: idx + 1000]
        assert "return Response" in bloc

    def test_export_csv_content_type_csv(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 1000]
        assert "text/csv" in bloc

    def test_export_csv_content_disposition(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 1000]
        assert "Content-Disposition" in bloc
        assert "attachment" in bloc

    def test_export_csv_filename(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 1000]
        assert "articles.csv" in bloc

    def test_export_csv_cache_control_no_store(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 1200]
        assert "Cache-Control" in bloc
        assert "no-store" in bloc

    def test_export_csv_applique_csv_escape(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 1200]
        assert "_csv_escape" in bloc

    def test_export_csv_utilise_csv_cols(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 1200]
        assert "_CSV_COLS" in bloc

    def test_export_csv_ecrit_entetes(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 1200]
        assert "writerow" in bloc
        assert "header" in bloc

    def test_export_csv_itere_rows(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 1200]
        assert "for row in rows" in bloc


# ---------------------------------------------------------------------------
# Contrôleur : validation sort et direction
# ---------------------------------------------------------------------------

class TestExportCsvValidation:
    def test_export_csv_valide_sort_whitelist(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 600]
        assert "sort not in" in bloc

    def test_export_csv_valide_direction(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 600]
        assert '"asc"' in bloc and '"desc"' in bloc

    def test_export_csv_accepte_q(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 400]
        assert '"q"' in bloc


# ---------------------------------------------------------------------------
# Contrôleur : filtres dans export_csv
# ---------------------------------------------------------------------------

class TestExportCsvFiltres:
    def test_export_csv_avec_filtre_texte(self):
        c = build_controller(_entity_with_filter())
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 800]
        assert "statut_f" in bloc
        assert "_filters" in bloc

    def test_export_csv_avec_filtre_relation(self):
        c = build_controller(_entity_with_relation(), relations=[_rel_client()])
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 800]
        assert "client_id_f" in bloc
        assert "int(" in bloc

    def test_export_csv_sans_filtres_pas_de_filters_param(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        bloc = c[idx: idx + 800]
        # sans filter fields, filters ne doit pas passer un dict non vide
        assert "_filters" not in bloc or "or None" in bloc


# ---------------------------------------------------------------------------
# Contrôleur : RBAC
# ---------------------------------------------------------------------------

class TestExportCsvRBAC:
    def test_sans_rbac_pas_de_decorator(self):
        c = _ctrl()
        idx = c.find("def export_csv")
        # remonter pour chercher @require_permission juste avant
        avant = c[max(0, idx - 200): idx]
        assert "require_permission" not in avant

    def test_avec_rbac_index_decorator_presente(self):
        pytest.importorskip("forge_mvc_rbac")
        c = build_controller(_entity_with_rbac())
        idx = c.find("def export_csv")
        avant = c[max(0, idx - 200): idx]
        assert 'require_permission("article.index")' in avant

    def test_rbac_export_utilise_permission_index(self):
        pytest.importorskip("forge_mvc_rbac")
        c = build_controller(_entity_with_rbac())
        # la permission index doit protéger export_csv
        idx = c.find("def export_csv")
        avant = c[max(0, idx - 200): idx]
        assert "article.index" in avant


# ---------------------------------------------------------------------------
# Vue : lien export
# ---------------------------------------------------------------------------

class TestVueLienExport:
    def test_lien_export_present(self):
        assert "export-csv" in _index_html()

    def test_lien_export_href_classique(self):
        h = _index_html()
        idx = h.find("export-csv")
        # le lien doit être dans un <a href="...">
        avant = h[max(0, idx - 100): idx + 20]
        assert "href" in avant

    def test_lien_export_pas_de_hx_get(self):
        h = _index_html()
        idx = h.find("export-csv")
        bloc = h[max(0, idx - 100): idx + 300]
        assert "hx-get" not in bloc

    def test_lien_export_pas_de_hx_target(self):
        h = _index_html()
        idx = h.find("export-csv")
        bloc = h[max(0, idx - 100): idx + 300]
        assert "hx-target" not in bloc

    def test_lien_export_conserve_q(self):
        h = _index_html()
        idx = h.find("export-csv")
        bloc = h[idx: idx + 300]
        assert "pagination.q" in bloc

    def test_lien_export_conserve_sort(self):
        h = _index_html()
        idx = h.find("export-csv")
        bloc = h[idx: idx + 300]
        assert "pagination.sort" in bloc

    def test_lien_export_conserve_direction(self):
        h = _index_html()
        idx = h.find("export-csv")
        bloc = h[idx: idx + 300]
        assert "pagination.direction" in bloc

    def test_lien_export_conserve_filtres(self):
        h = _index_html()
        idx = h.find("export-csv")
        bloc = h[idx: idx + 400]
        assert "pagination.filters" in bloc

    def test_lien_export_pas_de_page(self):
        h = _index_html()
        idx = h.find("export-csv")
        bloc = h[idx: idx + 400]
        assert "pagination.page" not in bloc

    def test_lien_export_avant_crud_results(self):
        h = _index_html()
        assert h.index("export-csv") < h.index('id="crud-results"')

    def test_lien_export_apres_form(self):
        h = _index_html()
        assert h.index("</form>") < h.index("export-csv")

    def test_lien_export_texte_visible(self):
        h = _index_html()
        assert "Exporter CSV" in h

    def test_lien_export_encode_q(self):
        h = _index_html()
        idx = h.find("export-csv")
        bloc = h[idx: idx + 200]
        assert "urlencode" in bloc


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------

class TestRoadmap:
    def test_crud_export_csv_001_livre(self):
        assert _livre("CRUD-EXPORT-CSV-001")

    def test_prochaine_priorite_phase_13(self):
        r = _roadmap()
        idx = r.find("Prochaine priorité immédiate")
        assert idx != -1
        bloc = r[idx: idx + 200]
        assert "FORGE-DESIGN-ROADMAP-001" in bloc
