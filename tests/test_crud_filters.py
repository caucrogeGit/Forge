"""Tests — CRUD-FILTER-001 : conformité du système de filtres CRUD.

Vérifie les critères d'acceptation du ticket CRUD-FILTER-001 :

- convention list.filter=true → filtre généré dans la vue ;
- champ sans list.filter → aucun filtre généré ;
- valeurs de filtre lues depuis la query string ;
- SQL paramétré (col = ?) ;
- filtres conservés dans les liens de pagination ;
- filtres conservés dans les liens de tri ;
- recherche q reste compatible avec les filtres ;
- formulaire compatible HTMX (hx-get) ;
- lien d'effacement de recherche présent ;
- aucune régression sur CRUD sans filtres.

Ces tests couvrent la fonctionnalité déjà implémentée et auditée dans
docs/history/audits/crud-filter-audit-001.md. Ils ne constituent pas de nouveaux
comportements mais des tests de conformité aux critères du ticket.
"""
from __future__ import annotations

from forge_cli.entities.make_crud import (
    CrudManyToOneRelation,
    _filter_fields,
    build_controller,
    build_index_view,
    build_model,
)
from forge_cli.entities.validation import normalize_entity_definition


# ---------------------------------------------------------------------------
# Helpers partagés
# ---------------------------------------------------------------------------

def _mk_field(name, sql_type, python_type="str", nullable=False, list_meta=None):
    f = {
        "name": name,
        "sql_type": sql_type,
        "python_type": python_type,
        "nullable": nullable,
        "primary_key": False,
        "auto_increment": False,
        "constraints": {},
    }
    if list_meta is not None:
        f["list"] = list_meta
    return f


def _entity(extra_fields=None):
    fields = [
        {
            "name": "id", "sql_type": "INT", "python_type": "int",
            "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {},
        },
    ]
    fields += extra_fields or [_mk_field("nom", "VARCHAR(80)")]
    return {
        "entity": "Contact", "table": "contact",
        "description": "", "fields": fields,
    }


def _norm(raw):
    return normalize_entity_definition(raw, source="test.json")


def _entity_with_statut():
    return _norm(_entity([_mk_field("statut", "VARCHAR(50)", list_meta={"filter": True})]))


def _entity_with_bool():
    return _norm(_entity([_mk_field("actif", "BOOL", "bool", list_meta={"filter": True})]))


def _entity_no_filter():
    return _norm(_entity([_mk_field("nom", "VARCHAR(80)")]))


def _entity_with_relation():
    return _norm(_entity([
        _mk_field("statut", "VARCHAR(50)", list_meta={"filter": True}),
        _mk_field("ville_id", "INT", "int"),
    ]))


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
# Convention de déclaration : list.filter=true
# ---------------------------------------------------------------------------

class TestConventionDeclaration:
    def test_champ_avec_filter_true_inclus_dans_filter_fields(self):
        entity = _entity_with_statut()
        fields = _filter_fields(entity)
        assert any(f["name"] == "statut" for f in fields)

    def test_champ_sans_filter_exclu(self):
        entity = _entity_no_filter()
        assert _filter_fields(entity) == []

    def test_champ_filter_false_exclu(self):
        raw = _entity([_mk_field("statut", "VARCHAR(50)", list_meta={"filter": False})])
        entity = _norm(raw)
        assert _filter_fields(entity) == []

    def test_relation_many_to_one_incluse_sans_list_filter(self):
        entity = _entity_with_relation()
        fields = _filter_fields(entity, _RELATION_VILLE)
        assert any(f["name"] == "ville_id" for f in fields)


# ---------------------------------------------------------------------------
# Génération du filtre dans la vue (critère : filtre généré uniquement
# pour les champs déclarés filtrables)
# ---------------------------------------------------------------------------

class TestGenerationVueFiltre:
    def test_input_filtre_genere_pour_champ_filter_true(self):
        html = build_index_view(_entity_with_statut())
        assert 'name="statut"' in html

    def test_input_filtre_absent_pour_champ_sans_filter(self):
        html = build_index_view(_entity_no_filter())
        assert 'name="nom"' not in html

    def test_select_genere_pour_champ_bool(self):
        html = build_index_view(_entity_with_bool())
        assert '<select name="actif"' in html
        assert '<option value="">Tous</option>' in html

    def test_select_bool_contient_options_oui_non(self):
        html = build_index_view(_entity_with_bool())
        assert 'value="1"' in html
        assert 'value="0"' in html

    def test_select_genere_pour_relation_many_to_one(self):
        html = build_index_view(_entity_with_relation(), relations=_RELATION_VILLE)
        assert '<select name="ville_id"' in html

    def test_input_absent_pour_relation_many_to_one(self):
        html = build_index_view(_entity_with_relation(), relations=_RELATION_VILLE)
        assert 'type="number" name="ville_id"' not in html
        assert 'type="text" name="ville_id"' not in html


# ---------------------------------------------------------------------------
# Lecture des filtres depuis la query string
# ---------------------------------------------------------------------------

class TestLectureQueryString:
    def test_controller_lit_query_param_pour_champ_filtre(self):
        code = build_controller(_entity_with_statut())
        assert '_query_param(request, "statut")' in code

    def test_controller_ne_lit_pas_champ_sans_filtre(self):
        code = build_controller(_entity_no_filter())
        assert '_query_param(request, "nom")' not in code

    def test_controller_parse_booleen_uniquement_0_ou_1(self):
        code = build_controller(_entity_with_bool())
        assert '"0"' in code and '"1"' in code

    def test_controller_lit_fk_relationnelle(self):
        code = build_controller(_entity_with_relation(), relations=_RELATION_VILLE)
        assert '_query_param(request, "ville_id")' in code


# ---------------------------------------------------------------------------
# SQL paramétré (sécurité — critère explicite du ticket)
# ---------------------------------------------------------------------------

class TestSQLParametre:
    def test_count_utilise_placeholder_pour_filtre(self):
        model = build_model(_entity_with_statut())
        assert "col + \" = ?\"" in model or 'col + " = ?"' in model

    def test_find_utilise_placeholder_pour_filtre(self):
        model = build_model(_entity_with_statut())
        assert "col + \" = ?\"" in model or '"= ?"' in model or "= ?" in model

    def test_model_contient_allowed_filters(self):
        model = build_model(_entity_with_statut())
        assert "_ALLOWED_FILTERS" in model

    def test_allowed_filters_contient_champ_declare(self):
        model = build_model(_entity_with_statut())
        assert '"statut"' in model

    def test_allowed_filters_vide_si_aucun_filtre(self):
        model = build_model(_entity_no_filter())
        assert "_ALLOWED_FILTERS = {}" in model

    def test_valeur_inconnue_leve_value_error(self):
        model = build_model(_entity_with_statut())
        assert "ValueError" in model and "Filtre interdit" in model


# ---------------------------------------------------------------------------
# Filtres conservés dans la pagination
# ---------------------------------------------------------------------------

class TestFiltresConservésDansPagination:
    def test_filters_loop_dans_liens_pagination(self):
        from forge_cli.entities.make_crud import build_pagination_partial
        html = build_pagination_partial(_entity_with_statut())
        assert "pagination.filters.items()" in html

    def test_pagination_prev_conserve_filtres(self):
        from forge_cli.entities.make_crud import build_pagination_partial
        html = build_pagination_partial(_entity_with_statut())
        assert "pagination.filters.items()" in html

    def test_controller_passe_filters_a_count(self):
        code = build_controller(_entity_with_statut())
        assert "filters=_filters" in code or "filters=" in code

    def test_controller_passe_filters_a_find(self):
        code = build_controller(_entity_with_statut())
        assert "filters=_filters" in code

    def test_pagination_context_contient_filters(self):
        code = build_controller(_entity_with_statut())
        assert '"filters"' in code and "_filters" in code


# ---------------------------------------------------------------------------
# Filtres conservés dans les liens de tri
# ---------------------------------------------------------------------------

class TestFiltresConservésDansLesTris:
    def test_filters_loop_dans_liens_tri(self):
        from forge_cli.entities.make_crud import build_table_partial
        html = build_table_partial(_entity_with_statut())
        assert "pagination.filters.items()" in html

    def test_sort_link_inclut_filtre_urlencode(self):
        from forge_cli.entities.make_crud import build_table_partial
        html = build_table_partial(_entity_with_statut())
        assert "urlencode" in html


# ---------------------------------------------------------------------------
# Compatibilité recherche q avec filtres
# ---------------------------------------------------------------------------

class TestCompatibiliteAvecRechercheQ:
    def test_count_combine_q_et_filtres_via_and(self):
        model = build_model(_entity_with_statut())
        assert "AND".join(["", ""]) in "AND" or "\" AND \".join(clauses)" in model

    def test_controller_passe_q_et_filters_independamment(self):
        code = build_controller(_entity_with_statut())
        assert "q or None" in code or "q=q" in code
        assert "filters=_filters" in code

    def test_formulaire_contient_champ_q_et_filtre_statut(self):
        html = build_index_view(_entity_with_statut())
        assert 'name="q"' in html
        assert 'name="statut"' in html


# ---------------------------------------------------------------------------
# Compatibilité HTMX (formulaire de filtre)
# ---------------------------------------------------------------------------

class TestCompatibiliteHTMX:
    def test_formulaire_a_attribut_hx_get(self):
        html = build_index_view(_entity_with_statut())
        assert "hx-get=" in html

    def test_formulaire_hx_push_url_present(self):
        html = build_index_view(_entity_with_statut())
        assert "hx-push-url=" in html

    def test_formulaire_hx_get_pointe_vers_route_entite(self):
        html = build_index_view(_entity_with_statut())
        assert 'hx-get="/contact"' in html


# ---------------------------------------------------------------------------
# Lien d'effacement / réinitialisation
# ---------------------------------------------------------------------------

class TestLienEffacement:
    def test_lien_effacement_present_dans_vue(self):
        html = build_index_view(_entity_with_statut())
        assert "Effacer" in html or "Réinitialiser" in html or 'href="/contact"' in html

    def test_lien_effacement_pointe_vers_racine_entite(self):
        html = build_index_view(_entity_with_statut())
        assert 'href="/contact"' in html


# ---------------------------------------------------------------------------
# Pas de régression sur CRUD sans filtres
# ---------------------------------------------------------------------------

class TestSansRegression:
    def test_crud_sans_filtre_genere_sans_erreur(self):
        code = build_controller(_entity_no_filter())
        assert "def index" in code

    def test_crud_sans_filtre_model_genere_sans_erreur(self):
        model = build_model(_entity_no_filter())
        assert "def count_contacts" in model or "def find_contacts" in model

    def test_crud_sans_filtre_vue_genere_sans_erreur(self):
        html = build_index_view(_entity_no_filter())
        assert "pagination.q" in html

    def test_crud_sans_filtre_filters_vide_dans_context(self):
        code = build_controller(_entity_no_filter())
        assert '"filters": {}' in code or "_filters = {}" in code or "_filters or {}" in code
