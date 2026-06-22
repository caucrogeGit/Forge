"""forge make:crud — génération scaffolding CRUD depuis une entité JSON Forge.

Génère pour une entité donnée :
    mvc/controllers/{snake}_controller.py
    mvc/models/{snake}_model.py
    mvc/forms/{snake}_form.py
    mvc/views/layouts/app.html
    mvc/views/{snake}/index.html
    mvc/views/{snake}/_table.html
    mvc/views/{snake}/_pagination.html
    mvc/views/{snake}/_results.html
    mvc/views/{snake}/show.html
    mvc/views/{snake}/form.html

Les fichiers existants ne sont jamais écrasés ([PRÉSERVÉ]).
Les routes sont affichées sur stdout, jamais injectées automatiquement.

Patterns présents dans les vues et contrôleurs générés (via les sous-modules) :
    - components/button.html          (build_layout, build_show_view, build_form_view, build_index_view)
    - "flash_html": render_flash_html(request)   (build_controller)
    - hx-get, hx-post, hx-target     (build_pagination_partial, build_index_view, build_table_partial)
    - /static/tailwind.css            (build_layout)
    - trans(                          (build_show_view, build_form_view, build_index_view)
"""

from __future__ import annotations

import json
from pathlib import Path

from cli.entities.canonical_model_normalizer import (
    CanonicalNormalizationError,
    normalize_canonical_entity_for_model_build,
)
from cli.entities.relations import (
    EntityRelationsError,
)
from cli.entities.validation import (
    EntityDefinitionError,
    validate_entity_definition,
)
import cli.output as out

# ── Re-exports from submodules (backward compatibility) ───────────────────────

from cli.entities.crud.context import (  # noqa: F401
    _RBAC_ACTION_TO_METHOD,
    _with_permission,
    MakeCrudResult,
    CrudManyToOneRelation,
    CrudManyToManyRelation,
)
from cli.entities.crud.utils import (  # noqa: F401
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
from cli.entities.crud.relations_loader import (  # noqa: F401
    _PREFERRED_LABEL_NAMES,
    _entity_definition_by_relation_name,
    _load_crud_many_to_one_relations,
    _load_crud_many_to_many_relations,
    _first_relation_label_field,
    _build_select_base,
    _unique_choice_relations,
    _unique_many_to_many_choice_relations,
)
from cli.entities.crud.form_builder import (  # noqa: F401
    _form_field_code,
    _form_imports,
    build_form,
)
from cli.entities.crud.model_builder import build_model  # noqa: F401
from cli.entities.crud.controller_builder import build_controller  # noqa: F401
from cli.entities.crud.views_builder import (  # noqa: F401
    build_layout,
    build_form_errors_partial,
    build_index_view,
    build_results_partial,
    build_table_partial,
    build_pagination_partial,
    build_show_view,
    build_form_view,
    build_bulk_delete_confirm_view,
)


def _route_block(definition: dict) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    ctrl = f"{entity}Controller"

    return "\n".join([
        "Routes à ajouter dans mvc/routes.py :",
        "─" * 70,
        f"  from mvc.controllers.{snake}_controller import {ctrl}",
        "",
        "  # Routes protégées par défaut.",
        "  # Pour un test local sans authentification :",
        f'  # with router.group("/{snake}", public=True, csrf=False) as g:',
        f'  with router.group("/{snake}") as g:',
        f'      g.add("GET",  "",                       {ctrl}.index,               name="{snake}-index")',
        f'      g.add("GET",  "/new",                   {ctrl}.new,                 name="{snake}-new")',
        f'      g.add("POST", "/create",                {ctrl}.create,              name="{snake}-create")',
        f'      g.add("GET",  "/show/{{id}}",             {ctrl}.show,                name="{snake}-show")',
        f'      g.add("GET",  "/edit/{{id}}",             {ctrl}.edit,                name="{snake}-edit")',
        f'      g.add("POST", "/update/{{id}}",           {ctrl}.update,              name="{snake}-update")',
        f'      g.add("POST", "/destroy/{{id}}",          {ctrl}.destroy,             name="{snake}-destroy")',
        f'      g.add("POST", "/bulk-delete",           {ctrl}.bulk_delete,         name="{snake}-bulk_delete")',
        f'      g.add("POST", "/bulk-delete-confirm",   {ctrl}.bulk_delete_confirm, name="{snake}-bulk_delete_confirm")',
        f'      g.add("GET",  "/export-csv",             {ctrl}.export_csv,          name="{snake}-export_csv")',
    ])


# ── Écriture fichier ───────────────────────────────────────────────────────────

def _write_if_new(path: Path, content: str, result: MakeCrudResult, dry_run: bool) -> None:
    if path.exists():
        result.preserved.append(path)
    else:
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        result.created.append(path)


# ── Entrée principale ─────────────────────────────────────────────────────────

def make_crud(
    entity_name: str,
    *,
    entities_root: Path,
    output_root: Path,
    dry_run: bool = False,
) -> MakeCrudResult:
    """Génère le scaffolding CRUD pour une entité Forge.

    Raises:
        SystemExit : si les contrats sont invalides, l'entité est introuvable ou le JSON invalide.
    """
    from cli.entities.entity_validate import collect_entity_validation_results
    results = collect_entity_validation_results(entities_root)
    if results is not None and results["errors"]:
        print(out.error("Les entités Forge sont invalides."))
        print("Conseil : lancez forge entity:validate pour obtenir le détail.")
        raise SystemExit(1)

    snake = _to_snake(entity_name)
    json_path = entities_root / snake / f"{snake}.json"

    if not json_path.exists():
        print(out.error(f"Entité introuvable : {json_path.as_posix()}"))
        raise SystemExit(1)

    try:
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and raw.get("format_version") == 1:
            print(out.error(
                f"Entité legacy refusée : {entity_name}.\n"
                "Le format format_version: 1 n'est plus accepté par make:crud.\n"
                'Utilisez schema_version: "1.0".'
            ))
            raise SystemExit(1)
        if not isinstance(raw, dict) or (raw.get("schema_version") != "1.0" and "entity" not in raw):
            print(out.error(
                f"Entité sans schema_version : {entity_name}.\n"
                'Ajoutez "schema_version": "1.0" à la racine du fichier JSON.\n'
                "Guide : docs/entities/migration-legacy-vers-canonique.md"
            ))
            raise SystemExit(1)
        is_legacy = raw.get("schema_version") != "1.0"
        if not is_legacy:
            raw = normalize_canonical_entity_for_model_build(raw)
        definition = validate_entity_definition(raw, source=str(json_path))
    except (json.JSONDecodeError, ValueError, CanonicalNormalizationError) as exc:
        print(out.error(str(exc)))
        raise SystemExit(1)

    try:
        relations = _load_crud_many_to_one_relations(definition, entities_root)
        many_to_many_relations = _load_crud_many_to_many_relations(definition, entities_root)
    except (json.JSONDecodeError, EntityRelationsError, EntityDefinitionError, ValueError) as exc:
        print(out.error(str(exc)))
        raise SystemExit(1)

    result = MakeCrudResult(dry_run=dry_run)

    if not _non_pk_fields(definition):
        result.warnings.append(
            f"Entité '{entity_name}' sans champ métier : "
            "formulaire vide, INSERT sans paramètre, UPDATE désactivé."
        )

    form_code, warnings = build_form(definition, relations)
    result.warnings.extend(warnings)

    mvc = output_root / "mvc"

    _write_if_new(
        mvc / "controllers" / f"{snake}_controller.py",
        build_controller(definition, relations, many_to_many_relations),
        result, dry_run,
    )
    _write_if_new(
        mvc / "models" / f"{snake}_model.py",
        build_model(definition, relations, many_to_many_relations),
        result, dry_run,
    )
    _write_if_new(
        mvc / "forms" / "__init__.py",
        '"""Formulaires applicatifs — conversion HTTP → cleaned_data."""\n',
        result, dry_run,
    )
    _write_if_new(
        mvc / "forms" / f"{snake}_form.py",
        form_code,
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / "layouts" / "app.html",
        build_layout(),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / "partials" / "form_errors.html",
        build_form_errors_partial(),
        result, dry_run,
    )
    rbac = definition.get("rbac")

    _write_if_new(
        mvc / "views" / snake / "index.html",
        build_index_view(definition, relations, many_to_many_relations, rbac=rbac),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / snake / "_table.html",
        build_table_partial(definition, relations, many_to_many_relations, rbac=rbac),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / snake / "_pagination.html",
        build_pagination_partial(definition),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / snake / "_results.html",
        build_results_partial(definition),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / snake / "show.html",
        build_show_view(definition, many_to_many_relations, rbac=rbac),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / snake / "form.html",
        build_form_view(definition, relations, many_to_many_relations),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / snake / "bulk_delete_confirm.html",
        build_bulk_delete_confirm_view(definition),
        result, dry_run,
    )

    result.route_block = _route_block(definition)
    return result


def cmd_make_crud_main(args: list[str]) -> None:
    if not args or args[0].startswith("-"):
        print("Usage : forge make:crud NomEntite [--dry-run]")
        raise SystemExit(1)

    entity_name = args[0]
    dry_run = "--dry-run" in args
    unknown = [a for a in args[1:] if a != "--dry-run"]
    if unknown:
        print(out.error(f"Arguments inconnus : {' '.join(unknown)}"))
        raise SystemExit(1)

    result = make_crud(
        entity_name,
        entities_root=Path("mvc") / "entities",
        output_root=Path("."),
        dry_run=dry_run,
    )

    for path in result.created:
        print(out.created(path.as_posix()))
    for path in result.preserved:
        print(out.preserved(path.as_posix(), "← fichier existant, non touché"))
    for warn in result.warnings:
        print(out.warn(warn))

    if dry_run:
        print(out.dry_run("Aucun fichier modifié."))

    print()
    print(result.route_block)
    print()
