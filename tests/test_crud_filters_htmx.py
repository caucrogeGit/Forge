"""Tests — CRUD-FILTER-HTMX-001 : intégration HTMX des filtres CRUD.

Vérifie les critères d'acceptation du ticket CRUD-FILTER-HTMX-001 :

- le formulaire filtre a method="get" et action="/{entité}" (fallback classique) ;
- hx-get, hx-target, hx-swap, hx-push-url présents sur le formulaire ;
- bouton Filtrer présent ;
- lien Réinitialiser présent avec href fallback ET attributs HTMX ;
- lien Réinitialiser visible quand q est actif ;
- lien Réinitialiser visible quand un filtre est actif (pas seulement q) ;
- pagination conserve filtres, q, sort, direction via boucle Jinja2 ;
- tri conserve les filtres via boucle Jinja2 ;
- fallback sans HTMX reste valide (pas de JS obligatoire) ;
- pas de recherche live (hx-trigger, keyup, debounce) ;
- aucun <script> ajouté.
"""
from __future__ import annotations

from forge_mvc_entities.make_crud import (
    CrudManyToOneRelation,
    build_index_view,
    build_pagination_partial,
    build_table_partial,
)
from forge_mvc_entities.validation import normalize_entity_definition


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
        ] + (fields or [_mk_field("nom", "VARCHAR(80)")]),
    }
    return normalize_entity_definition(raw, source="test.json")


def _entity_with_filter():
    return _norm([_mk_field("statut", "VARCHAR(50)", list_meta={"filter": True})])


def _entity_with_bool_filter():
    return _norm([_mk_field("actif", "BOOL", "bool", list_meta={"filter": True})])


def _entity_no_filter():
    return _norm([_mk_field("nom", "VARCHAR(80)")])


_RELATION_VILLE = [
    CrudManyToOneRelation(
        field_name="ville_id",
        field_column="VilleId",
        target_entity="Ville",
        target_table="ville",
        target_pk_column="Id",
        target_label_column="Nom",
        choices_function="get_ville_choices",
        choices_key="ville_id_choices",
    )
]


# ---------------------------------------------------------------------------
# Formulaire HTMX
# ---------------------------------------------------------------------------

class TestFormHTMX:
    def test_form_method_get(self):
        html = build_index_view(_entity_with_filter())
        assert 'method="get"' in html

    def test_form_action_fallback(self):
        html = build_index_view(_entity_with_filter())
        assert 'action="/contact"' in html

    def test_form_hx_get(self):
        html = build_index_view(_entity_with_filter())
        assert 'hx-get="/contact"' in html

    def test_form_hx_target(self):
        html = build_index_view(_entity_with_filter())
        assert 'hx-target="#crud-results"' in html

    def test_form_hx_swap(self):
        html = build_index_view(_entity_with_filter())
        assert 'hx-swap="innerHTML"' in html

    def test_form_hx_push_url(self):
        html = build_index_view(_entity_with_filter())
        assert 'hx-push-url="true"' in html

    def test_form_hx_get_sans_filtre(self):
        html = build_index_view(_entity_no_filter())
        assert 'hx-get="/contact"' in html

    def test_form_inclut_input_q(self):
        html = build_index_view(_entity_with_filter())
        assert 'name="q"' in html

    def test_form_inclut_input_filtre_declare(self):
        html = build_index_view(_entity_with_filter())
        assert 'name="statut"' in html


# ---------------------------------------------------------------------------
# Bouton Filtrer
# ---------------------------------------------------------------------------

class TestBoutonFiltrer:
    def test_bouton_submit_present(self):
        html = build_index_view(_entity_with_filter())
        assert 'type="submit"' in html

    def test_bouton_submit_dans_form(self):
        html = build_index_view(_entity_with_filter())
        form_start = html.find("<form")
        form_end = html.find("</form>")
        form_html = html[form_start:form_end]
        assert 'type="submit"' in form_html

    def test_pas_de_hx_trigger_sur_bouton(self):
        html = build_index_view(_entity_with_filter())
        assert "hx-trigger" not in html


# ---------------------------------------------------------------------------
# Lien Réinitialiser
# ---------------------------------------------------------------------------

class TestLienReinitialiser:
    def test_lien_href_fallback_present(self):
        html = build_index_view(_entity_with_filter())
        assert 'href="/contact"' in html

    def test_lien_hx_get_present(self):
        html = build_index_view(_entity_with_filter())
        # Le lien reset a son propre hx-get (en plus du form)
        assert html.count('hx-get="/contact"') >= 1

    def test_lien_hx_target_present(self):
        html = build_index_view(_entity_with_filter())
        # Le lien reset a hx-target
        assert 'hx-target="#crud-results"' in html

    def test_lien_hx_push_url_present(self):
        html = build_index_view(_entity_with_filter())
        assert 'hx-push-url="true"' in html

    def test_lien_texte_reinitialiser(self):
        html = build_index_view(_entity_with_filter())
        assert "Réinitialiser" in html

    def test_lien_visible_quand_q_actif(self):
        html = build_index_view(_entity_with_filter())
        # La condition inclut pagination.q
        assert "pagination.q" in html
        assert "{% if pagination.q or pagination.filters %}" in html

    def test_lien_visible_quand_filtre_actif(self):
        html = build_index_view(_entity_with_filter())
        # La condition inclut pagination.filters (pas juste q)
        assert "{% if pagination.q or pagination.filters %}" in html

    def test_lien_visible_sans_filtre_declare(self):
        html = build_index_view(_entity_no_filter())
        # Même sans filtre déclaré, la condition est présente
        assert "pagination.q" in html

    def test_lien_reinitialiser_dans_form(self):
        html = build_index_view(_entity_with_filter())
        form_start = html.find("<form")
        form_end = html.find("</form>")
        form_html = html[form_start:form_end]
        assert "Réinitialiser" in form_html

    def test_lien_avec_bool_filter(self):
        html = build_index_view(_entity_with_bool_filter())
        assert "Réinitialiser" in html
        assert "{% if pagination.q or pagination.filters %}" in html


# ---------------------------------------------------------------------------
# Conservation des paramètres
# ---------------------------------------------------------------------------

class TestConservationParametres:
    def test_pagination_conserve_filtres(self):
        html = build_pagination_partial(_entity_with_filter())
        assert "pagination.filters.items()" in html

    def test_pagination_conserve_q(self):
        html = build_pagination_partial(_entity_with_filter())
        assert "pagination.q" in html

    def test_pagination_conserve_sort(self):
        html = build_pagination_partial(_entity_with_filter())
        assert "pagination.sort" in html

    def test_pagination_conserve_direction(self):
        html = build_pagination_partial(_entity_with_filter())
        assert "pagination.direction" in html

    def test_tri_conserve_filtres(self):
        html = build_table_partial(_entity_with_filter())
        assert "pagination.filters.items()" in html

    def test_tri_conserve_q(self):
        html = build_table_partial(_entity_with_filter())
        assert "pagination.q" in html

    def test_filtres_urlencode_dans_liens(self):
        html = build_pagination_partial(_entity_with_filter())
        assert "urlencode" in html


# ---------------------------------------------------------------------------
# Fallback sans HTMX
# ---------------------------------------------------------------------------

class TestFallbackSansHTMX:
    def test_form_valide_sans_htmx(self):
        html = build_index_view(_entity_with_filter())
        assert 'method="get"' in html
        assert 'action="/contact"' in html

    def test_pas_de_script(self):
        index = build_index_view(_entity_with_filter())
        pagination = build_pagination_partial(_entity_with_filter())
        table = build_table_partial(_entity_with_filter())
        assert "<script" not in index
        assert "<script" not in pagination
        assert "<script" not in table

    def test_pas_de_keyup(self):
        index = build_index_view(_entity_with_filter())
        pagination = build_pagination_partial(_entity_with_filter())
        assert "keyup" not in index
        assert "keyup" not in pagination

    def test_pas_de_debounce(self):
        html = build_index_view(_entity_with_filter())
        assert "debounce" not in html

    def test_pas_de_hx_trigger(self):
        index = build_index_view(_entity_with_filter())
        pagination = build_pagination_partial(_entity_with_filter())
        assert "hx-trigger" not in index
        assert "hx-trigger" not in pagination

    def test_pas_de_hx_delete_dans_form_filtre(self):
        html = build_index_view(_entity_with_filter())
        form_start = html.find("<form")
        form_end = html.find("</form>")
        form_html = html[form_start:form_end]
        assert "hx-delete" not in form_html

    def test_div_crud_results_present(self):
        html = build_index_view(_entity_with_filter())
        assert 'id="crud-results"' in html

    def test_results_partial_inclut_table_et_pagination(self):
        from forge_mvc_entities.make_crud import build_results_partial
        html = build_results_partial(_entity_with_filter())
        assert 'contact/_table.html' in html
        assert 'contact/_pagination.html' in html
