"""Tests — CRUD-HTMX-001 : consolidation de l'expérience HTMX globale des CRUD générés.

Vérifie la cohérence de l'intégration HTMX sur l'ensemble des composants :
- formulaire de recherche / filtres ;
- lien Réinitialiser ;
- liens de tri ;
- liens de pagination ;
- formulaire de suppression unitaire ;
- formulaire de suppression groupée (intentionnellement HTML classique) ;
- fragment #crud-results ;
- `_results.html` sans layout complet ;
- fallback HTML classique pour chaque élément ;
- aucun JavaScript personnalisé ;
- conservation cohérente des paramètres q / filtres / sort / direction.
"""
from __future__ import annotations

from forge_cli.entities.crud.views_builder import (
    build_index_view,
    build_table_partial,
    build_pagination_partial,
    build_results_partial,
)
from forge_cli.entities.validation import normalize_entity_definition


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mk_field(name, sql_type, python_type="str", nullable=False, list_meta=None):
    f = {
        "name": name, "sql_type": sql_type, "python_type": python_type,
        "nullable": nullable, "primary_key": False, "auto_increment": False,
        "constraints": {},
    }
    if list_meta is not None:
        f["list"] = list_meta
    return f


def _norm(fields=None):
    raw = {
        "entity": "Contact", "table": "contact",
        "description": "", "fields": [
            {"name": "id", "sql_type": "INT", "python_type": "int",
             "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
        ] + (fields or [
            _mk_field("nom", "VARCHAR(80)"),
            _mk_field("email", "VARCHAR(120)"),
        ]),
    }
    return normalize_entity_definition(raw, source="test.json")


def _entity_simple():
    return _norm()


def _entity_avec_filtre():
    return _norm([
        _mk_field("nom", "VARCHAR(80)"),
        _mk_field("statut", "VARCHAR(50)", list_meta={"filter": True}),
    ])


# ---------------------------------------------------------------------------
# Structure de #crud-results dans index.html
# ---------------------------------------------------------------------------

class TestCrudResultsDiv:
    def test_div_crud_results_present(self):
        html = build_index_view(_entity_simple())
        assert 'id="crud-results"' in html

    def test_results_inclus_dans_div(self):
        html = build_index_view(_entity_simple())
        idx_div = html.find('id="crud-results"')
        idx_inc = html.find("_results.html", idx_div)
        idx_close = html.find("</div>", idx_div)
        assert idx_div < idx_inc < idx_close

    def test_results_partial_sans_extends(self):
        html = build_results_partial(_entity_simple())
        assert "{% extends" not in html

    def test_results_partial_inclut_table(self):
        html = build_results_partial(_entity_simple())
        assert "_table.html" in html

    def test_results_partial_inclut_pagination(self):
        html = build_results_partial(_entity_simple())
        assert "_pagination.html" in html


# ---------------------------------------------------------------------------
# Formulaire recherche / filtres — cohérence HTMX
# ---------------------------------------------------------------------------

class TestFormRechercheFiltresHTMX:
    def test_form_method_get_fallback(self):
        html = build_index_view(_entity_simple())
        assert 'method="get"' in html

    def test_form_hx_get(self):
        html = build_index_view(_entity_simple())
        assert 'hx-get="/contact"' in html

    def test_form_hx_target_crud_results(self):
        html = build_index_view(_entity_simple())
        idx = html.find('hx-get="/contact"')
        bloc = html[max(0, idx - 20): idx + 100]
        assert 'hx-target="#crud-results"' in bloc

    def test_form_hx_swap_innerhtml(self):
        html = build_index_view(_entity_simple())
        idx = html.find('hx-get="/contact"')
        bloc = html[max(0, idx - 20): idx + 100]
        assert 'hx-swap="innerHTML"' in bloc

    def test_form_hx_push_url(self):
        html = build_index_view(_entity_simple())
        idx = html.find('hx-get="/contact"')
        bloc = html[max(0, idx - 20): idx + 100]
        assert 'hx-push-url="true"' in bloc

    def test_input_q_present(self):
        html = build_index_view(_entity_simple())
        assert 'name="q"' in html

    def test_bouton_submit_present(self):
        html = build_index_view(_entity_simple())
        assert 'type="submit"' in html


# ---------------------------------------------------------------------------
# Lien Réinitialiser — cohérence HTMX
# ---------------------------------------------------------------------------

class TestResetHTMX:
    def test_reset_href_absolu(self):
        html = build_index_view(_entity_simple())
        assert 'href="/contact"' in html

    def test_reset_hx_get(self):
        html = build_index_view(_entity_simple())
        assert 'hx-get="/contact"' in html

    def test_reset_hx_target(self):
        html = build_index_view(_entity_simple())
        idx = html.find("Réinitialiser")
        bloc = html[max(0, idx - 200): idx + 30]
        assert 'hx-target="#crud-results"' in bloc

    def test_reset_hx_swap(self):
        html = build_index_view(_entity_simple())
        idx = html.find("Réinitialiser")
        bloc = html[max(0, idx - 200): idx + 30]
        assert 'hx-swap="innerHTML"' in bloc

    def test_reset_hx_push_url(self):
        html = build_index_view(_entity_simple())
        idx = html.find("Réinitialiser")
        bloc = html[max(0, idx - 200): idx + 30]
        assert 'hx-push-url="true"' in bloc

    def test_reset_conditionne_par_q_ou_filtres(self):
        html = build_index_view(_entity_simple())
        assert "pagination.q or pagination.filters" in html


# ---------------------------------------------------------------------------
# Liens de tri — cohérence HTMX
# ---------------------------------------------------------------------------

class TestTriHTMX:
    def test_sort_href_present(self):
        html = build_table_partial(_entity_simple())
        assert 'href="?sort=nom' in html

    def test_sort_hx_get_present(self):
        html = build_table_partial(_entity_simple())
        assert 'hx-get="?sort=nom' in html

    def test_sort_href_et_hx_get_meme_url(self):
        html = build_table_partial(_entity_simple())
        idx_href = html.find('href="?sort=nom')
        idx_hxget = html.find('hx-get="?sort=nom', idx_href)
        # Les deux sont dans le même <th>
        th_end = html.find("</th>", idx_href)
        assert idx_href < idx_hxget < th_end

    def test_sort_hx_target(self):
        html = build_table_partial(_entity_simple())
        idx = html.find('?sort=nom')
        th_end = html.find("</th>", idx)
        bloc = html[idx: th_end]
        assert 'hx-target="#crud-results"' in bloc

    def test_sort_hx_swap(self):
        html = build_table_partial(_entity_simple())
        idx = html.find('?sort=nom')
        th_end = html.find("</th>", idx)
        bloc = html[idx: th_end]
        assert 'hx-swap="innerHTML"' in bloc

    def test_sort_hx_push_url(self):
        html = build_table_partial(_entity_simple())
        idx = html.find('?sort=nom')
        th_end = html.find("</th>", idx)
        bloc = html[idx: th_end]
        assert 'hx-push-url="true"' in bloc

    def test_sort_conserve_q_dans_url(self):
        html = build_table_partial(_entity_simple())
        idx = html.find('?sort=nom')
        th_end = html.find("</th>", idx)
        bloc = html[idx: th_end]
        assert "pagination.q" in bloc

    def test_sort_conserve_filtres_dans_url(self):
        defn = _entity_avec_filtre()
        html = build_table_partial(defn)
        idx = html.find('?sort=nom')
        th_end = html.find("</th>", idx)
        bloc = html[idx: th_end]
        assert "pagination.filters" in bloc

    def test_sort_ne_conserve_pas_page(self):
        html = build_table_partial(_entity_simple())
        idx = html.find('?sort=nom')
        th_end = html.find("</th>", idx)
        bloc = html[idx: th_end]
        assert "pagination.page" not in bloc


# ---------------------------------------------------------------------------
# Pagination — cohérence HTMX
# ---------------------------------------------------------------------------

class TestPaginationHTMX:
    def test_pagination_href_prev(self):
        html = build_pagination_partial(_entity_simple())
        assert "href=" in html

    def test_pagination_hx_get(self):
        html = build_pagination_partial(_entity_simple())
        assert "hx-get=" in html

    def test_pagination_hx_target(self):
        html = build_pagination_partial(_entity_simple())
        assert 'hx-target="#crud-results"' in html

    def test_pagination_hx_swap(self):
        html = build_pagination_partial(_entity_simple())
        assert 'hx-swap="innerHTML"' in html

    def test_pagination_hx_push_url(self):
        html = build_pagination_partial(_entity_simple())
        assert 'hx-push-url="true"' in html

    def test_pagination_conserve_q(self):
        html = build_pagination_partial(_entity_simple())
        assert "pagination.q" in html

    def test_pagination_conserve_sort(self):
        html = build_pagination_partial(_entity_simple())
        assert "pagination.sort" in html

    def test_pagination_conserve_direction(self):
        html = build_pagination_partial(_entity_simple())
        assert "pagination.direction" in html

    def test_pagination_conserve_filtres(self):
        html = build_pagination_partial(_entity_simple())
        assert "pagination.filters" in html


# ---------------------------------------------------------------------------
# Suppression unitaire — cohérence HTMX
# ---------------------------------------------------------------------------

class TestSuppressionUnitaireHTMX:
    def test_form_post_fallback(self):
        html = build_table_partial(_entity_simple())
        assert 'method="post"' in html

    def test_hx_post_sur_suppression(self):
        html = build_table_partial(_entity_simple())
        assert "hx-post=" in html

    def test_hx_target_sur_suppression(self):
        html = build_table_partial(_entity_simple())
        idx = html.find("hx-post=")
        end = html.find(">", idx)
        bloc = html[idx: end]
        assert 'hx-target="#crud-results"' in bloc

    def test_hx_swap_sur_suppression(self):
        html = build_table_partial(_entity_simple())
        idx = html.find("hx-post=")
        end = html.find(">", idx)
        bloc = html[idx: end]
        assert 'hx-swap="innerHTML"' in bloc

    def test_hx_confirm_sur_suppression(self):
        html = build_table_partial(_entity_simple())
        assert "hx-confirm=" in html

    def test_onsubmit_confirm_fallback(self):
        html = build_table_partial(_entity_simple())
        assert "onsubmit=" in html

    def test_csrf_dans_form_suppression(self):
        html = build_table_partial(_entity_simple())
        assert 'name="csrf_token"' in html


# ---------------------------------------------------------------------------
# Suppression groupée — HTML classique intentionnel
# ---------------------------------------------------------------------------

class TestSuppressionGroupeeSansHTMX:
    def test_form_post_classique(self):
        html = build_table_partial(_entity_simple())
        assert 'id="bulk-delete-form"' in html
        idx = html.find('id="bulk-delete-form"')
        form_start = html.rfind("<form", 0, idx)
        form_tag_end = html.find(">", form_start)
        form_tag = html[form_start: form_tag_end + 1]
        assert 'method="post"' in form_tag

    def test_pas_de_hx_post_sur_bulk_form(self):
        html = build_table_partial(_entity_simple())
        idx_bulk = html.find('id="bulk-delete-form"')
        form_end = html.find("</form>", idx_bulk)
        bulk_form = html[html.rfind("<form", 0, idx_bulk): form_end]
        assert "hx-post" not in bulk_form
        assert "hx-get" not in bulk_form

    def test_pas_de_hx_trigger_sur_bulk(self):
        html = build_table_partial(_entity_simple())
        assert "hx-trigger" not in html

    def test_csrf_dans_bulk_form(self):
        html = build_table_partial(_entity_simple())
        idx_bulk = html.find('id="bulk-delete-form"')
        form_start = html.rfind("<form", 0, idx_bulk)
        form_end = html.find("</form>", idx_bulk)
        bulk_section = html[form_start: form_end]
        assert 'name="csrf_token"' in bulk_section

    def test_checkbox_form_attribute_html5(self):
        html = build_table_partial(_entity_simple())
        assert 'form="bulk-delete-form"' in html


# ---------------------------------------------------------------------------
# Cohérence globale — cible HTMX unique
# ---------------------------------------------------------------------------

class TestCoherenceGlobale:
    def test_toutes_les_cibles_htmx_sont_crud_results(self):
        index_html = build_index_view(_entity_simple())
        table_html = build_table_partial(_entity_simple())
        pag_html = build_pagination_partial(_entity_simple())
        for html in [index_html, table_html, pag_html]:
            if "hx-target=" in html:
                assert 'hx-target="#crud-results"' in html, (
                    "Toutes les cibles HTMX doivent être #crud-results"
                )

    def test_toutes_les_swap_sont_innerhtml(self):
        index_html = build_index_view(_entity_simple())
        table_html = build_table_partial(_entity_simple())
        pag_html = build_pagination_partial(_entity_simple())
        for html in [index_html, table_html, pag_html]:
            if "hx-swap=" in html:
                assert 'hx-swap="innerHTML"' in html, (
                    "Tous les hx-swap doivent être innerHTML"
                )

    def test_pas_de_hx_target_autre_que_crud_results(self):
        index_html = build_index_view(_entity_simple())
        table_html = build_table_partial(_entity_simple())
        pag_html = build_pagination_partial(_entity_simple())
        for html in [index_html, table_html, pag_html]:
            import re
            targets = re.findall(r'hx-target="([^"]+)"', html)
            for t in targets:
                assert t == "#crud-results", f"cible inattendue : {t!r}"


# ---------------------------------------------------------------------------
# Interdictions — pas de JavaScript, keyup, debounce
# ---------------------------------------------------------------------------

class TestInterdictions:
    def test_pas_de_script_index(self):
        assert "<script" not in build_index_view(_entity_simple())

    def test_pas_de_script_table(self):
        assert "<script" not in build_table_partial(_entity_simple())

    def test_pas_de_script_pagination(self):
        assert "<script" not in build_pagination_partial(_entity_simple())

    def test_pas_de_keyup(self):
        html = build_index_view(_entity_simple()) + build_table_partial(_entity_simple())
        assert "keyup" not in html

    def test_pas_de_debounce(self):
        html = build_index_view(_entity_simple()) + build_table_partial(_entity_simple())
        assert "debounce" not in html

    def test_pas_de_hx_trigger_sur_recherche(self):
        html = build_index_view(_entity_simple())
        assert "hx-trigger" not in html

    def test_pas_de_hx_delete(self):
        html = build_table_partial(_entity_simple())
        assert "hx-delete" not in html

    def test_pas_de_auto_submit(self):
        html = build_index_view(_entity_simple())
        assert "addEventListener" not in html
        assert "oninput" not in html
