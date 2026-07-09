"""CRUD-FILTER-WHITELIST-001 — Whitelist des filtres CRUD générés.

Vérifie que :
- _ALLOWED_FILTERS est généré dans le modèle ;
- il mappe les noms de champs vers les colonnes SQL (qualifiées si relations) ;
- les clés inconnues lèvent ValueError dans les fonctions count/find ;
- le contrôleur utilise les noms de champs comme clés _filters.
"""
from __future__ import annotations

import pytest

from forge_mvc_entities.make_crud import (
    CrudManyToOneRelation,
    build_controller,
    build_model,
)
from forge_mvc_entities.validation import normalize_entity_definition


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _entity(extra_fields=None):
    fields = [
        {"name": "id", "sql_type": "INT", "python_type": "int",
         "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
    ]
    fields.extend(extra_fields or [])
    return normalize_entity_definition({
        "entity": "Contact", "table": "contact",
        "description": "", "fields": fields,
    }, source="test.json")


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
# _ALLOWED_FILTERS présent dans le modèle généré
# ---------------------------------------------------------------------------

class TestAllowedFiltersGeneres:

    def test_allowed_filters_present_dans_modele(self):
        entity = _entity([_field("statut", "VARCHAR(50)", "str", list_meta={"filter": True})])
        code = build_model(entity)
        assert "_ALLOWED_FILTERS" in code

    def test_allowed_filters_contient_champ_filtre(self):
        entity = _entity([_field("statut", "VARCHAR(50)", "str", list_meta={"filter": True})])
        code = build_model(entity)
        assert '"statut": "Statut"' in code

    def test_allowed_filters_sans_filtre_vide(self):
        entity = _entity([_field("nom", "VARCHAR(100)", "str")])
        code = build_model(entity)
        assert "_ALLOWED_FILTERS = {}" in code

    def test_allowed_filters_relation_qualifiee(self):
        entity = _entity([_field("ville_id", "INT", "int")])
        code = build_model(entity, [_ville_relation()])
        assert '"ville_id": "contact.VilleId"' in code

    def test_allowed_filters_plusieurs_champs(self):
        entity = _entity([
            _field("statut", "VARCHAR(50)", "str", list_meta={"filter": True}),
            _field("actif", "BOOL", "bool", list_meta={"filter": True}),
        ])
        code = build_model(entity)
        assert '"statut": "Statut"' in code
        assert '"actif": "Actif"' in code

    def test_whitelist_utilise_get_dans_boucle(self):
        entity = _entity([_field("statut", "VARCHAR(50)", "str", list_meta={"filter": True})])
        code = build_model(entity)
        assert "_ALLOWED_FILTERS.get(key)" in code

    def test_cle_inconnue_leve_value_error(self):
        entity = _entity([_field("statut", "VARCHAR(50)", "str", list_meta={"filter": True})])
        code = build_model(entity)
        assert 'raise ValueError(f"Filtre interdit : {key}")' in code

    def test_iteration_utilise_key_val(self):
        entity = _entity([_field("statut", "VARCHAR(50)", "str", list_meta={"filter": True})])
        code = build_model(entity)
        assert "for key, val in (filters or {}).items():" in code


# ---------------------------------------------------------------------------
# Injection attempt — les clés malicieuses levènt ValueError à l'exécution
# ---------------------------------------------------------------------------

class TestInjectionRejete:

    def _make_model_globals(self, entity, relations=None):
        code = build_model(entity, relations)
        ns: dict = {}
        exec(compile(code, "<generated>", "exec"), ns)  # noqa: S102
        return ns

    def _inject_fake_db(self, ns, fetchone_result=None):
        ns["fetch_one"] = lambda sql, params=(): fetchone_result

    def test_cle_inconnue_count_leve_value_error(self):
        entity = _entity([_field("statut", "VARCHAR(50)", "str", list_meta={"filter": True})])
        ns = self._make_model_globals(entity)
        self._inject_fake_db(ns, fetchone_result={"total": 0})
        count_fn = ns["count_contacts"]
        with pytest.raises(ValueError, match="Filtre interdit"):
            count_fn(filters={"1=1; DROP TABLE contact; --": "x"})

    def test_cle_connue_count_ne_leve_pas(self):
        entity = _entity([_field("statut", "VARCHAR(50)", "str", list_meta={"filter": True})])
        ns = self._make_model_globals(entity)
        self._inject_fake_db(ns, fetchone_result={"total": 3})
        count_fn = ns["count_contacts"]
        result = count_fn(filters={"statut": "actif"})
        assert result == 3


# ---------------------------------------------------------------------------
# Contrôleur : clés _filters utilisent les noms de champs
# ---------------------------------------------------------------------------

class TestControleurClesChamps:

    def test_filtre_simple_cle_nom_champ(self):
        entity = _entity([_field("statut", "VARCHAR(50)", "str", list_meta={"filter": True})])
        code = build_controller(entity)
        assert '_filters["statut"] = statut_f' in code
        assert '"Statut"' not in code.split("_filters")[1].split("\n")[0]

    def test_filtre_bool_cle_nom_champ(self):
        entity = _entity([_field("actif", "BOOL", "bool", list_meta={"filter": True})])
        code = build_controller(entity)
        assert '_filters["actif"] = actif_f' in code

    def test_filtre_relation_cle_nom_champ(self):
        entity = _entity([_field("ville_id", "INT", "int")])
        code = build_controller(entity, [_ville_relation()])
        assert '_filters["ville_id"] = ville_id_f' in code
        assert '"contact.VilleId"' not in code

    def test_filtre_relation_cle_ne_contient_pas_point(self):
        entity = _entity([_field("ville_id", "INT", "int")])
        code = build_controller(entity, [_ville_relation()])
        import re
        filters_assignments = re.findall(r'_filters\["([^"]+)"\]', code)
        assert all("." not in k for k in filters_assignments)
