"""Tests pour la métadonnée list.filter dans les JSON d'entité et make:crud."""
import pytest

from forge_cli.entities.validation import (
    EntityDefinitionError,
    validate_entity_definition,
    normalize_entity_definition,
)
from forge_cli.entities.make_crud import (
    CrudManyToOneRelation,
    _filter_fields,
    _is_bool_sql,
    build_controller,
    build_index_view,
    build_model,
    build_pagination_partial,
    build_table_partial,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_entity(extra_field=None):
    fields = [
        {
            "name": "id",
            "sql_type": "INT",
            "python_type": "int",
            "nullable": False,
            "primary_key": True,
            "auto_increment": True,
            "constraints": {},
        },
        extra_field or {
            "name": "nom",
            "sql_type": "VARCHAR(100)",
            "python_type": "str",
            "nullable": False,
            "primary_key": False,
            "auto_increment": False,
            "constraints": {},
        },
    ]
    return {
        "entity": "Contact",
        "table": "contact",
        "description": "",
        "fields": fields,
    }


def _field(name, sql_type, python_type, nullable=False, list_meta=None):
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


def _entity_with_filter_field(name, sql_type, python_type, filter_val=True):
    return {
        "entity": "Contact",
        "table": "contact",
        "description": "",
        "fields": [
            {"name": "id", "sql_type": "INT", "python_type": "int",
             "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
            _field(name, sql_type, python_type, list_meta={"filter": filter_val}),
        ],
    }


def _ville_relation():
    return CrudManyToOneRelation(
        field_name="ville_id",
        field_column="VilleId",
        target_entity="Ville",
        target_table="ville",
        target_pk_column="Id",
        target_label_column="Nom",
        choices_function="get_ville_choices",
        choices_key="ville_id_choices",
    )


# ---------------------------------------------------------------------------
# _is_bool_sql
# ---------------------------------------------------------------------------

class TestIsBoolSql:

    def test_bool_detecte(self):
        assert _is_bool_sql("BOOL") is True

    def test_boolean_detecte(self):
        assert _is_bool_sql("BOOLEAN") is True

    def test_varchar_non_bool(self):
        assert _is_bool_sql("VARCHAR(10)") is False

    def test_int_non_bool(self):
        assert _is_bool_sql("INT") is False


# ---------------------------------------------------------------------------
# Validation JSON — list absent
# ---------------------------------------------------------------------------

class TestListAbsent:

    def test_list_absent_accepte(self):
        validate_entity_definition(_base_entity(), source="test.json")

    def test_champ_sans_list_accepte(self):
        entity = _base_entity()
        validate_entity_definition(entity, source="test.json")


# ---------------------------------------------------------------------------
# Validation JSON — list présent — structure
# ---------------------------------------------------------------------------

class TestListStructure:

    def _entity_with_list(self, list_value):
        entity = _base_entity()
        entity["fields"][1]["list"] = list_value
        return entity

    def test_list_objet_valide_accepte(self):
        validate_entity_definition(
            self._entity_with_list({"filter": True}), source="test.json"
        )

    def test_list_chaine_refuse(self):
        with pytest.raises(EntityDefinitionError, match="doit etre un objet"):
            validate_entity_definition(self._entity_with_list("filter"), source="test.json")

    def test_list_entier_refuse(self):
        with pytest.raises(EntityDefinitionError, match="doit etre un objet"):
            validate_entity_definition(self._entity_with_list(42), source="test.json")

    def test_list_liste_refuse(self):
        with pytest.raises(EntityDefinitionError, match="doit etre un objet"):
            validate_entity_definition(self._entity_with_list(["filter"]), source="test.json")

    def test_list_cle_inconnue_refuse(self):
        with pytest.raises(EntityDefinitionError, match="cle list non supportee"):
            validate_entity_definition(
                self._entity_with_list({"filter": True, "inconnu": True}),
                source="test.json",
            )

    def test_list_filter_non_booleen_refuse(self):
        with pytest.raises(EntityDefinitionError, match="doit etre un booleen"):
            validate_entity_definition(
                self._entity_with_list({"filter": "true"}), source="test.json"
            )

    def test_list_filter_entier_refuse(self):
        with pytest.raises(EntityDefinitionError, match="doit etre un booleen"):
            validate_entity_definition(
                self._entity_with_list({"filter": 1}), source="test.json"
            )


# ---------------------------------------------------------------------------
# Validation JSON — list.filter=true — types SQL supportés
# ---------------------------------------------------------------------------

class TestListFilterTypesSupportes:

    def test_varchar_supporte(self):
        validate_entity_definition(
            _entity_with_filter_field("statut", "VARCHAR(50)", "str"), source="test.json"
        )

    def test_char_supporte(self):
        validate_entity_definition(
            _entity_with_filter_field("code", "CHAR(2)", "str"), source="test.json"
        )

    def test_int_supporte(self):
        validate_entity_definition(
            _entity_with_filter_field("categorie", "INT", "int"), source="test.json"
        )

    def test_bigint_supporte(self):
        validate_entity_definition(
            _entity_with_filter_field("ref", "BIGINT", "int"), source="test.json"
        )

    def test_bool_supporte(self):
        validate_entity_definition(
            _entity_with_filter_field("actif", "BOOL", "bool"), source="test.json"
        )

    def test_boolean_supporte(self):
        validate_entity_definition(
            _entity_with_filter_field("publie", "BOOLEAN", "bool"), source="test.json"
        )

    def test_text_refuse(self):
        with pytest.raises(EntityDefinitionError, match="n'est pas supporte"):
            validate_entity_definition(
                _entity_with_filter_field("bio", "TEXT", "str"), source="test.json"
            )

    def test_date_refuse(self):
        with pytest.raises(EntityDefinitionError, match="n'est pas supporte"):
            validate_entity_definition(
                _entity_with_filter_field("debut", "DATE", "date"), source="test.json"
            )

    def test_datetime_refuse(self):
        with pytest.raises(EntityDefinitionError, match="n'est pas supporte"):
            validate_entity_definition(
                _entity_with_filter_field("cree_le", "DATETIME", "datetime"), source="test.json"
            )

    def test_timestamp_refuse(self):
        with pytest.raises(EntityDefinitionError, match="n'est pas supporte"):
            validate_entity_definition(
                _entity_with_filter_field("mis_a_jour", "TIMESTAMP", "datetime"), source="test.json"
            )

    def test_decimal_refuse(self):
        with pytest.raises(EntityDefinitionError, match="n'est pas supporte"):
            validate_entity_definition(
                _entity_with_filter_field("prix", "DECIMAL(10,2)", "float"), source="test.json"
            )

    def test_float_refuse(self):
        with pytest.raises(EntityDefinitionError, match="n'est pas supporte"):
            validate_entity_definition(
                _entity_with_filter_field("note", "FLOAT", "float"), source="test.json"
            )

    def test_list_filter_false_accepte_sans_restriction(self):
        validate_entity_definition(
            _entity_with_filter_field("bio", "TEXT", "str", filter_val=False),
            source="test.json",
        )


# ---------------------------------------------------------------------------
# Normalisation — list passé dans le champ normalisé
# ---------------------------------------------------------------------------

class TestNormalisation:

    def test_list_present_dans_champ_normalise(self):
        entity = _base_entity()
        entity["fields"][1]["list"] = {"filter": True}
        result = normalize_entity_definition(entity, source="test.json")
        assert result["fields"][1].get("list") == {"filter": True}

    def test_list_absent_pas_dans_champ_normalise(self):
        result = normalize_entity_definition(_base_entity(), source="test.json")
        assert "list" not in result["fields"][1]


# ---------------------------------------------------------------------------
# _filter_fields()
# ---------------------------------------------------------------------------

class TestFilterFields:

    def _entity(self, *extra_fields):
        fields = [
            {"name": "id", "sql_type": "INT", "python_type": "int",
             "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
        ]
        fields.extend(extra_fields)
        return {
            "entity": "Contact", "table": "contact",
            "description": "", "fields": fields,
        }

    def test_champ_avec_filter_true_inclus(self):
        entity = self._entity(_field("statut", "VARCHAR(50)", "str", list_meta={"filter": True}))
        result = _filter_fields(entity)
        assert len(result) == 1
        assert result[0]["name"] == "statut"

    def test_champ_sans_list_exclu(self):
        entity = self._entity(_field("nom", "VARCHAR(100)", "str"))
        assert _filter_fields(entity) == []

    def test_champ_filter_false_exclu(self):
        entity = self._entity(_field("nom", "VARCHAR(100)", "str", list_meta={"filter": False}))
        assert _filter_fields(entity) == []

    def test_fk_relationnel_inclus(self):
        entity = self._entity(_field("ville_id", "INT", "int", list_meta={"filter": True}))
        result = _filter_fields(entity, [_ville_relation()])
        assert len(result) == 1
        assert result[0]["name"] == "ville_id"

    def test_fk_relationnel_inclus_sans_list_filter(self):
        entity = self._entity(_field("ville_id", "INT", "int"))
        result = _filter_fields(entity, [_ville_relation()])
        assert len(result) == 1
        assert result[0]["name"] == "ville_id"

    def test_int_non_relationnel_pas_filtre_automatique(self):
        entity = self._entity(_field("ville_id", "INT", "int"))
        assert _filter_fields(entity) == []

    def test_plusieurs_filtres(self):
        entity = self._entity(
            _field("statut", "VARCHAR(50)", "str", list_meta={"filter": True}),
            _field("actif", "BOOL", "bool", list_meta={"filter": True}),
            _field("nom", "VARCHAR(100)", "str"),
        )
        result = _filter_fields(entity)
        assert [f["name"] for f in result] == ["statut", "actif"]


# ---------------------------------------------------------------------------
# build_model() — count et find avec filters
# ---------------------------------------------------------------------------

class TestBuildModelFilters:

    def _entity(self, extra_field):
        raw = {
            "entity": "Contact", "table": "contact",
            "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                extra_field,
            ],
        }
        return normalize_entity_definition(raw, source="test.json")

    def test_count_accepte_filters_param(self):
        entity = self._entity(_field("nom", "VARCHAR(100)", "str"))
        code = build_model(entity)
        assert "def count_contacts(q=None, filters=None):" in code

    def test_find_accepte_filters_param(self):
        entity = self._entity(_field("nom", "VARCHAR(100)", "str"))
        code = build_model(entity)
        assert "def find_contacts_paginated(q=None, sort=None, direction=\"asc\", limit=10, offset=0, filters=None):" in code

    def test_count_utilise_clauses_and(self):
        entity = self._entity(_field("nom", "VARCHAR(100)", "str"))
        code = build_model(entity)
        assert '" AND ".join(clauses)' in code

    def test_find_utilise_clauses_and(self):
        entity = self._entity(_field("nom", "VARCHAR(100)", "str"))
        code = build_model(entity)
        assert '" AND ".join(clauses)' in code

    def test_count_itere_filters(self):
        entity = self._entity(_field("nom", "VARCHAR(100)", "str"))
        code = build_model(entity)
        assert "for key, val in (filters or {}).items():" in code

    def test_find_itere_filters(self):
        entity = self._entity(_field("nom", "VARCHAR(100)", "str"))
        code = build_model(entity)
        lines = code.split("\n")
        filter_loop_count = sum(1 for l in lines if "for key, val in (filters or {}).items():" in l)
        assert filter_loop_count >= 2

    def test_filtre_relationnel_combine_avec_q_via_and(self):
        entity = normalize_entity_definition({
            "entity": "Contact", "table": "contact",
            "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                _field("nom", "VARCHAR(100)", "str"),
                _field("ville_id", "INT", "int"),
            ],
        }, source="test.json")
        code = build_model(entity, [_ville_relation()])
        assert 'clauses.append("(" + " OR ".join(c + " LIKE ?" for c in _SEARCH_COLS) + ")")' in code
        assert '_ALLOWED_FILTERS.get(key)' in code
        assert 'clauses.append(col + " = ?")' in code
        assert '" AND ".join(clauses)' in code

    def test_filtre_relationnel_utilise_parametre_sql(self):
        entity = normalize_entity_definition({
            "entity": "Contact", "table": "contact",
            "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                _field("ville_id", "INT", "int"),
            ],
        }, source="test.json")
        code = build_model(entity, [_ville_relation()])
        assert '_ALLOWED_FILTERS.get(key)' in code
        assert 'clauses.append(col + " = ?")' in code
        assert "params.append(val)" in code
        assert " + val" not in code


# ---------------------------------------------------------------------------
# build_controller() — index avec filter fields
# ---------------------------------------------------------------------------

class TestBuildControllerFilters:

    def _entity_with_statut(self):
        raw = {
            "entity": "Contact", "table": "contact",
            "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                _field("statut", "VARCHAR(50)", "str", list_meta={"filter": True}),
                _field("nom", "VARCHAR(100)", "str"),
            ],
        }
        return normalize_entity_definition(raw, source="test.json")

    def _entity_with_bool_filter(self):
        raw = {
            "entity": "Contact", "table": "contact",
            "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                _field("actif", "BOOL", "bool", list_meta={"filter": True}),
            ],
        }
        return normalize_entity_definition(raw, source="test.json")

    def _entity_no_filter(self):
        raw = {
            "entity": "Contact", "table": "contact",
            "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                _field("nom", "VARCHAR(100)", "str"),
            ],
        }
        return normalize_entity_definition(raw, source="test.json")

    def _entity_with_relation(self):
        raw = {
            "entity": "Contact", "table": "contact",
            "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                _field("statut", "VARCHAR(50)", "str", list_meta={"filter": True}),
                _field("ville_id", "INT", "int"),
            ],
        }
        return normalize_entity_definition(raw, source="test.json")

    def test_filtre_varchar_lit_query_param(self):
        code = build_controller(self._entity_with_statut())
        assert '_query_param(request, "statut")' in code

    def test_filtre_varchar_ajoute_dans_filters_dict(self):
        code = build_controller(self._entity_with_statut())
        assert '"Statut"' in code or '"statut"' in code.lower()
        assert "_filters" in code

    def test_filtre_bool_utilise_condition_01(self):
        code = build_controller(self._entity_with_bool_filter())
        assert 'in ("0", "1")' in code

    def test_filters_passe_a_count(self):
        code = build_controller(self._entity_with_statut())
        assert "filters=_filters" in code

    def test_filters_passe_a_find(self):
        code = build_controller(self._entity_with_statut())
        assert "filters=_filters" in code

    def test_pagination_contient_filters(self):
        code = build_controller(self._entity_with_statut())
        assert '"filters"' in code

    def test_sans_filter_field_filters_vide_dans_pagination(self):
        code = build_controller(self._entity_no_filter())
        assert '"filters": {}' in code

    def test_sans_filter_field_pas_de_filters_param_dans_count(self):
        code = build_controller(self._entity_no_filter())
        assert "filters=_filters" not in code

    def test_relation_many_to_one_lit_query_param(self):
        code = build_controller(self._entity_with_relation(), [_ville_relation()])
        assert '_query_param(request, "ville_id")' in code

    def test_relation_many_to_one_parse_entier(self):
        code = build_controller(self._entity_with_relation(), [_ville_relation()])
        assert "ville_id_f = int(ville_id_raw)" in code
        assert "except (TypeError, ValueError):" in code

    def test_relation_many_to_one_valeur_vide_ignoree(self):
        code = build_controller(self._entity_with_relation(), [_ville_relation()])
        assert 'ville_id_f = ""' in code
        assert 'if ville_id_f != "":' in code

    def test_relation_many_to_one_filtre_colonne_qualifiee(self):
        code = build_controller(self._entity_with_relation(), [_ville_relation()])
        assert '_filters["ville_id"] = ville_id_f' in code

    def test_relation_many_to_one_combinee_avec_filtre_simple(self):
        code = build_controller(self._entity_with_relation(), [_ville_relation()])
        assert '_filters["statut"] = statut_f' in code
        assert '_filters["ville_id"] = ville_id_f' in code

    def test_relation_many_to_one_pagination_conserve_filtre(self):
        code = build_controller(self._entity_with_relation(), [_ville_relation()])
        assert '"ville_id": ville_id_f' in code

    def test_relation_many_to_one_controller_charge_options_index(self):
        code = build_controller(self._entity_with_relation(), [_ville_relation()])
        assert '"relation_filters": relation_filters' in code
        assert 'relation_filters["ville_id"]' in code
        assert '"options": [{"id": value, "label": label} for value, label in get_ville_choices()]' in code


# ---------------------------------------------------------------------------
# build_index_view() — filter inputs et preservation
# ---------------------------------------------------------------------------

class TestBuildIndexViewFilters:

    def _entity_with_varchar_filter(self):
        raw = {
            "entity": "Contact", "table": "contact",
            "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                _field("statut", "VARCHAR(50)", "str", list_meta={"filter": True}),
            ],
        }
        return normalize_entity_definition(raw, source="test.json")

    def _entity_with_bool_filter(self):
        raw = {
            "entity": "Contact", "table": "contact",
            "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                _field("actif", "BOOL", "bool", list_meta={"filter": True}),
            ],
        }
        return normalize_entity_definition(raw, source="test.json")

    def _entity_no_filter(self):
        raw = {
            "entity": "Contact", "table": "contact",
            "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                _field("nom", "VARCHAR(100)", "str"),
            ],
        }
        return normalize_entity_definition(raw, source="test.json")

    def _entity_with_relation(self):
        raw = {
            "entity": "Contact", "table": "contact",
            "description": "",
            "fields": [
                {"name": "id", "sql_type": "INT", "python_type": "int",
                 "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
                _field("ville_id", "INT", "int"),
            ],
        }
        return normalize_entity_definition(raw, source="test.json")

    def test_varchar_filter_genere_input_text(self):
        html = build_index_view(self._entity_with_varchar_filter())
        assert 'name="statut"' in html
        assert 'type="text"' in html

    def test_bool_filter_genere_select(self):
        html = build_index_view(self._entity_with_bool_filter())
        assert 'name="actif"' in html
        assert "<select" in html
        assert "trans('common.yes')" in html
        assert "trans('common.no')" in html

    def test_filters_loop_dans_sort_links(self):
        html = build_table_partial(self._entity_with_varchar_filter())
        assert "pagination.filters.items()" in html

    def test_filters_loop_dans_pagination_prev(self):
        html = build_pagination_partial(self._entity_with_varchar_filter())
        assert "pagination.filters.items()" in html

    def test_sans_filter_field_pas_dinput_filtre(self):
        html = build_index_view(self._entity_no_filter())
        assert 'name="statut"' not in html

    def test_filters_loop_toujours_present_meme_sans_filtres(self):
        html = build_pagination_partial(self._entity_no_filter())
        assert "pagination.filters.items()" in html

    def test_bool_filter_valeur_preselection(self):
        html = build_index_view(self._entity_with_bool_filter())
        assert "pagination.filters.actif" in html

    def test_relation_many_to_one_genere_select(self):
        html = build_index_view(self._entity_with_relation(), [_ville_relation()])
        assert "<select" in html
        assert 'name="ville_id"' in html
        assert "relation_filters.ville_id.options" in html
        assert "pagination.filters.ville_id" in html

    def test_relation_many_to_one_ne_genere_plus_input_number(self):
        html = build_index_view(self._entity_with_relation(), [_ville_relation()])
        assert 'type="number"' not in html

    def test_relation_many_to_one_select_option_vide(self):
        html = build_index_view(self._entity_with_relation(), [_ville_relation()])
        assert '<option value="">Tous les Ville</option>' in html

    def test_relation_many_to_one_select_conserve_valeur_selectionnee(self):
        html = build_index_view(self._entity_with_relation(), [_ville_relation()])
        assert "pagination.filters.ville_id|string == option.id|string" in html
        assert "{{ option.label }}" in html

    def test_relation_many_to_one_conserve_dans_liens_tri(self):
        html = build_table_partial(self._entity_with_relation(), [_ville_relation()])
        assert "pagination.filters.items()" in html
        assert "&amp;{{ key }}={{ val | urlencode }}" in html

    def test_relation_many_to_one_conserve_dans_pagination(self):
        html = build_pagination_partial(self._entity_with_relation())
        assert "page={{ pagination.page - 1 }}" in html
        assert "pagination.filters.items()" in html
