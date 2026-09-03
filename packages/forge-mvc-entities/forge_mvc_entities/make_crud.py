# pyright: strict
# pyright: reportPrivateUsage=false
# pyright: reportUnusedImport=false
"""forge make:crud — génération scaffolding CRUD depuis une entité JSON Forge.

Génère pour une entité donnée (les vues sous le namespace APP_VIEWS_NAMESPACE
du projet, « app » par défaut ; ADR-073) :
    mvc/controllers/{snake}_controller.py
    mvc/models/{snake}_model.py
    mvc/forms/{snake}_form.py
    mvc/views/layouts/app.html
    mvc/views/app/{snake}/index.html
    mvc/views/app/{snake}/_table.html
    mvc/views/app/{snake}/_pagination.html
    mvc/views/app/{snake}/_results.html
    mvc/views/app/{snake}/show.html
    mvc/views/app/{snake}/form.html

Avec APP_VIEWS_NAMESPACE="" les vues sont écrites à plat (mvc/views/{snake}/...),
disposition historique. Les contrôleurs et includes générés portent le même
préfixe que les fichiers écrits (render()/loader inchangés, chemins littéraux).

Les fichiers existants ne sont jamais écrasés ([PRÉSERVÉ]).
Les routes sont affichées sur stdout, jamais injectées automatiquement.

Patterns présents dans les vues et contrôleurs générés (via les sous-modules) :
    - macro button de components/ui.html  (build_show_view, build_form_view, build_index_view)
    - "flash": get_flash(get_session_id(request))   (build_controller, rendu via la macro flash_messages)
    - hx-get, hx-post, hx-target     (build_pagination_partial, build_index_view, build_table_partial)
    - extends layouts/base.html       (build_index_view, build_show_view, build_form_view)
    - trans(                          (build_show_view, build_form_view, build_index_view)
"""

from __future__ import annotations
from typing import Any, cast

import json
from pathlib import Path

from forge_mvc_entities.canonical_model_normalizer import (
    CanonicalNormalizationError,
    normalize_canonical_entity_for_model_build,
)
from forge_mvc_entities.field_resolver import dialect
from forge_mvc_entities.relations import (
    EntityRelationsError,
)
from forge_mvc_entities.validation import (
    EntityDefinitionError,
    validate_entity_definition,
)
import cli._support.output as out
from cli._support.scaffold import CREATED, PRESERVED, write_if_new

# ── Re-exports from submodules (backward compatibility) ───────────────────────

from forge_mvc_entities.crud.routes_slug import slug_route_lines
from forge_mvc_entities.crud.context import (  # noqa: F401
    _RBAC_ACTION_TO_METHOD,
    _with_permission,
    MakeCrudResult,
    CrudManyToOneRelation,
    CrudManyToManyRelation,
)
from forge_mvc_entities.crud.utils import (  # noqa: F401
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
from forge_mvc_entities.crud.relations_loader import (  # noqa: F401
    _PREFERRED_LABEL_NAMES,
    _entity_definition_by_relation_name,
    _load_crud_many_to_one_relations,
    _load_crud_many_to_many_relations,
    _first_relation_label_field,
    _build_select_base,
    _unique_choice_relations,
    _unique_many_to_many_choice_relations,
)
from forge_mvc_entities.crud.form_builder import (  # noqa: F401
    _form_field_code,
    _form_imports,
    build_form,
)
from forge_mvc_entities.crud.model_builder import build_model  # noqa: F401
from forge_mvc_entities.crud.controller_builder import build_controller  # noqa: F401
from forge_mvc_entities.crud.views_builder import (  # noqa: F401
    build_form_errors_partial,
    build_index_view,
    build_results_partial,
    build_table_partial,
    build_pagination_partial,
    build_show_view,
    build_form_view,
    build_bulk_delete_confirm_view,
)
from forge_mvc_entities.crud.views_namespace import (
    entity_view_dir,
    resolve_app_views_namespace,
)


def build_routes_file(definition: dict[str, Any]) -> str:
    """Contenu de mvc/routes/<snake>_routes.py : register_<snake>_routes(router) (ADR-068)."""
    entity = definition["entity"]
    snake = _to_snake(entity)
    ctrl = f"{entity}Controller"

    slug_route = slug_route_lines(definition, snake, ctrl)

    return "\n".join([
        f'"""Routes du contrôleur {ctrl} (ADR-068)."""',
        "from core.http.router import Router",
        f"from mvc.controllers.{snake}_controller import {ctrl}",
        "",
        "",
        f"def register_{snake}_routes(router: Router) -> None:",
        "    # Routes protégées par défaut. Pour un test local sans authentification :",
        f'    #   with router.group("/{snake}", public=True, csrf=False) as g:',
        f'    with router.group("/{snake}") as g:',
        f'        g.add("GET", "", {ctrl}.index, name="{snake}-index")',
        f'        g.add("GET", "/new", {ctrl}.new, name="{snake}-new")',
        f'        g.add("POST", "/create", {ctrl}.create, name="{snake}-create")',
        f'        g.add("GET", "/show/{{id}}", {ctrl}.show, name="{snake}-show")',
        f'        g.add("GET", "/edit/{{id}}", {ctrl}.edit, name="{snake}-edit")',
        f'        g.add("POST", "/update/{{id}}", {ctrl}.update, name="{snake}-update")',
        f'        g.add("POST", "/destroy/{{id}}", {ctrl}.destroy, name="{snake}-destroy")',
        f'        g.add("POST", "/bulk-delete", {ctrl}.bulk_delete, name="{snake}-bulk_delete")',
        f'        g.add("POST", "/bulk-delete-confirm", {ctrl}.bulk_delete_confirm, name="{snake}-bulk_delete_confirm")',
        f'        g.add("GET", "/export-csv", {ctrl}.export_csv, name="{snake}-export_csv")',
        *slug_route,
        "",
    ])


def _route_block(definition: dict[str, Any]) -> str:
    """Deux lignes à brancher dans mvc/routes/__init__.py (ADR-068)."""
    snake = _to_snake(definition["entity"])
    return "\n".join([
        "Branchement à ajouter dans mvc/routes/__init__.py :",
        "─" * 70,
        f"  from mvc.routes.{snake}_routes import register_{snake}_routes",
        f"  register_{snake}_routes(router)",
    ])


# ── Écriture fichier ───────────────────────────────────────────────────────────

def _write_if_new(path: Path, content: str, result: MakeCrudResult, dry_run: bool) -> None:
    status = write_if_new(path, content, dry_run=dry_run)
    if status == CREATED:
        result.created.append(path)
    elif status == PRESERVED:
        result.preserved.append(path)
    else:  # WARNED : existant au contenu différent, jamais écrasé
        result.warnings.append(f"{path.as_posix()} existe et diffère du modèle, non touché.")


def _inject_relation_fk_fields(
    definition: dict[str, Any],
    relations: list[CrudManyToOneRelation],
) -> None:
    """Injecte un champ synthétique pour chaque FK many_to_one portée par la relation.

    Quand la colonne FK n'est pas déclarée comme champ d'entité (flux officiel,
    FORGE-12+), la colonne est créée par `relations.sql`. Pour que le CRUD généré la
    gère comme un champ ordinaire, on ajoute ici un champ à la définition : le
    formulaire produit alors un `RelationField` (select), et le modèle inclut la
    colonne dans INSERT/UPDATE (la valeur choisie est persistée).
    """
    existing = {f["name"] for f in definition["fields"]}
    for rel in relations:
        if rel.field_name in existing:
            continue
        definition["fields"].append({
            "name": rel.field_name,
            "column": rel.field_column,
            "forge_type": "foreign_key",
            "python_type": "int",
            # Repli dialectal : le type MariaDB en dur posait une colonne
            # invalide sur les autres backends (OPTIN-SQL-TYPE-BRANCHING-001,
            # meme correctif que FK-IDENTITY-STORAGE-TYPE-001).
            "sql_type": rel.fk_sql_type or dialect().identity_storage_type(),
            "nullable": rel.fk_nullable,
            "primary_key": False,
            "auto_increment": False,
            "constraints": {},
            "unique": False,
        })
        existing.add(rel.field_name)


# ── Entrée principale ─────────────────────────────────────────────────────────

def make_crud(
    entity_name: str,
    *,
    entities_root: Path,
    output_root: Path,
    dry_run: bool = False,
    views_namespace: str = "",
) -> MakeCrudResult:
    """Génère le scaffolding CRUD pour une entité Forge.

    Raises:
        SystemExit : si les contrats sont invalides, l'entité est introuvable ou le JSON invalide.
    """
    from forge_mvc_entities.entity_validate import collect_entity_validation_results
    results = collect_entity_validation_results(entities_root)
    if results is not None and results["errors"]:
        print(out.error("Les entités Forge sont invalides."))
        print("Conseil : lancez forge entity:validate pour obtenir le détail.")
        raise SystemExit(1)

    snake = _to_snake(entity_name)
    view_dir = entity_view_dir(snake, views_namespace)
    json_path = entities_root / snake / f"{snake}.json"

    if not json_path.exists():
        print(out.error(f"Entité introuvable : {json_path.as_posix()}"))
        raise SystemExit(1)

    try:
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and cast("dict[str, Any]", raw).get("format_version") == 1:
            print(out.error(
                f"Entité legacy refusée : {entity_name}.\n"
                "Le format format_version: 1 n'est plus accepté par make:crud.\n"
                'Utilisez schema_version: "1.0".'
            ))
            raise SystemExit(1)
        if not isinstance(raw, dict) or (cast("dict[str, Any]", raw).get("schema_version") != "1.0" and "entity" not in raw):
            print(out.error(
                f"Entité sans schema_version : {entity_name}.\n"
                'Ajoutez "schema_version": "1.0" à la racine du fichier JSON.\n'
                "Guide : docs/entities/migration-legacy-vers-canonique.md"
            ))
            raise SystemExit(1)
        is_legacy = cast("dict[str, Any]", raw).get("schema_version") != "1.0"
        if not is_legacy:
            raw = normalize_canonical_entity_for_model_build(cast("dict[str, Any]", raw))
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

    # FORGE-12+ : une FK portée par la relation (non déclarée comme champ) devient un
    # champ synthétique, pour que le formulaire (select) et le modèle la persistent.
    _inject_relation_fk_fields(definition, relations)

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
        build_controller(definition, relations, many_to_many_relations, views_namespace=views_namespace),
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
        mvc / "views" / "partials" / "form_errors.html",
        build_form_errors_partial(),
        result, dry_run,
    )
    rbac = definition.get("rbac")

    _write_if_new(
        mvc / "views" / view_dir / "index.html",
        build_index_view(definition, relations, many_to_many_relations, rbac=rbac, views_namespace=views_namespace),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / view_dir / "_table.html",
        build_table_partial(definition, relations, many_to_many_relations, rbac=rbac),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / view_dir / "_pagination.html",
        build_pagination_partial(definition),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / view_dir / "_results.html",
        build_results_partial(definition, views_namespace),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / view_dir / "show.html",
        build_show_view(definition, relations, many_to_many_relations, rbac=rbac),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / view_dir / "form.html",
        build_form_view(definition, relations, many_to_many_relations),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / view_dir / "bulk_delete_confirm.html",
        build_bulk_delete_confirm_view(definition),
        result, dry_run,
    )
    # ADR-068 : les routes du contrôleur vivent dans leur propre fichier ;
    # mvc/routes/__init__.py ne fait que les brancher (bloc affiché ci-dessous).
    _write_if_new(
        mvc / "routes" / f"{snake}_routes.py",
        build_routes_file(definition),
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
        views_namespace=resolve_app_views_namespace(),
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
