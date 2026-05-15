"""forge_cli.entities.crud — CRUD generator submodules.

Re-exports all public symbols for backward compatibility.
"""

from __future__ import annotations

from forge_cli.entities.crud.context import (
    _RBAC_ACTION_TO_METHOD,
    _with_permission,
    MakeCrudResult,
    CrudManyToOneRelation,
    CrudManyToManyRelation,
)
from forge_cli.entities.crud.utils import (
    _FORM_FIELD_CLASS_MAP,
    _FORM_FIELD_STR_CONSTRAINTS,
    _HTML_TYPE_FROM_FORM_FIELD,
    _to_snake,
    _humanize,
    _pk_field,
    _non_pk_fields,
    _is_textarea,
    _html_input_type,
    _text_search_fields,
    _text_label_fields,
    _is_bool_sql,
    _filter_fields,
    _media_form_fields,
    _relation_by_field,
)
from forge_cli.entities.crud.relations_loader import (
    _PREFERRED_LABEL_NAMES,
    _entity_definition_by_relation_name,
    _load_crud_many_to_one_relations,
    _load_crud_many_to_many_relations,
    _first_relation_label_field,
    _build_select_base,
    _unique_choice_relations,
    _unique_many_to_many_choice_relations,
)
from forge_cli.entities.crud.form_builder import (
    _form_field_code,
    _form_imports,
    build_form,
)
from forge_cli.entities.crud.model_builder import build_model
from forge_cli.entities.crud.controller_builder import build_controller
from forge_cli.entities.crud.views_builder import (
    build_layout,
    build_form_errors_partial,
    build_index_view,
    build_results_partial,
    build_table_partial,
    build_pagination_partial,
    build_show_view,
    build_form_view,
)

__all__ = [
    # context
    "_RBAC_ACTION_TO_METHOD",
    "_with_permission",
    "MakeCrudResult",
    "CrudManyToOneRelation",
    "CrudManyToManyRelation",
    # utils
    "_FORM_FIELD_CLASS_MAP",
    "_FORM_FIELD_STR_CONSTRAINTS",
    "_HTML_TYPE_FROM_FORM_FIELD",
    "_to_snake",
    "_humanize",
    "_pk_field",
    "_non_pk_fields",
    "_is_textarea",
    "_html_input_type",
    "_text_search_fields",
    "_text_label_fields",
    "_is_bool_sql",
    "_filter_fields",
    "_media_form_fields",
    "_relation_by_field",
    # relations_loader
    "_PREFERRED_LABEL_NAMES",
    "_entity_definition_by_relation_name",
    "_load_crud_many_to_one_relations",
    "_load_crud_many_to_many_relations",
    "_first_relation_label_field",
    "_build_select_base",
    "_unique_choice_relations",
    "_unique_many_to_many_choice_relations",
    # form_builder
    "_form_field_code",
    "_form_imports",
    "build_form",
    # model_builder
    "build_model",
    # controller_builder
    "build_controller",
    # views_builder
    "build_layout",
    "build_form_errors_partial",
    "build_index_view",
    "build_results_partial",
    "build_table_partial",
    "build_pagination_partial",
    "build_show_view",
    "build_form_view",
]
