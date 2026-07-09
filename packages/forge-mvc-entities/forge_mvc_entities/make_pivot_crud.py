# pyright: strict
"""forge_mvc_entities/make_pivot_crud.py — Générateur de sous-CRUD Pivot advanced (opt-in).

Commande : forge make:pivot-crud <EntitéSource> <nomRelation> [--dry-run]

Analyse une relation many_to_many avec pivot.fields[] et génère une structure
dédiée minimale sans modifier make:crud.

Décision : PIVOT-ADVANCED-004.
Service runtime : forge_mvc_entities.PivotAdvancedService (PIVOT-ADVANCED-003).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any, cast

import cli._support.output as out

_SNAKE_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def _to_snake(name: str) -> str:
    return _SNAKE_RE.sub("_", name).lower()


def _as_dict(value: object) -> dict[str, Any] | None:
    """Vue typée d'une valeur JSON décodée si c'est un objet, None sinon.

    Isole le rétrécissement ``isinstance`` + ``cast`` à la frontière JSON
    (``json.loads`` renvoie ``Any``) pour garder le reste strict-clean.
    """
    return cast("dict[str, Any]", value) if isinstance(value, dict) else None


def _as_list(value: object) -> list[Any] | None:
    """Vue typée d'une valeur JSON décodée si c'est un tableau, None sinon."""
    return cast("list[Any]", value) if isinstance(value, list) else None


# ── Données de la relation résolue ────────────────────────────────────────────

@dataclass(frozen=True)
class ResolvedPivotRelation:
    from_entity: str
    to_entity: str
    relation_name: str
    pivot_table: str
    from_key: str
    to_key: str
    pivot_fields: tuple[str, ...]


# ── Résultat ──────────────────────────────────────────────────────────────────

@dataclass
class MakePivotCrudResult:
    created: list[Path] = dc_field(default_factory=list[Path])
    preserved: list[Path] = dc_field(default_factory=list[Path])
    dry_run: bool = False


# ── Résolution de la relation ─────────────────────────────────────────────────

def resolve_pivot_relation(
    source_entity: str,
    relation_name: str,
    *,
    relations_path: Path,
) -> ResolvedPivotRelation:
    """Charge relations.json et trouve la relation many_to_many cible.

    Raises SystemExit avec message clair pour tous les cas d'erreur.
    """
    if not relations_path.exists():
        print(out.error(
            "mvc/entities/relations.json introuvable.\n"
            "Créez d'abord vos relations avec forge make:relation."
        ))
        raise SystemExit(1)

    try:
        raw = _as_dict(json.loads(relations_path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        print(out.error(f"relations.json invalide (JSON malformé) : {exc}"))
        raise SystemExit(1)

    if raw is None or raw.get("schema_version") != "1.0":
        print(out.error('relations.json invalide : schema_version "1.0" attendu.'))
        raise SystemExit(1)

    relations = _as_list(raw.get("relations"))
    if relations is None:
        print(out.error("relations.json invalide : clé \"relations\" manquante ou invalide."))
        raise SystemExit(1)

    candidates: list[dict[str, Any]] = []
    for r in relations:
        rd = _as_dict(r)
        if (
            rd is not None
            and rd.get("type") == "many_to_many"
            and rd.get("from") == source_entity
            and rd.get("name") == relation_name
        ):
            candidates.append(rd)

    if not candidates:
        # Distinguer les cas d'erreur
        source_exists = any(
            (rd := _as_dict(r)) is not None and rd.get("from") == source_entity
            for r in relations
        )
        if not source_exists:
            print(out.error(f"Entité source inconnue : {source_entity!r} n'apparaît dans aucune relation."))
        else:
            print(out.error(
                f"Relation introuvable : {source_entity}.{relation_name}.\n"
                f"Vérifiez le nom de la relation (clé \"name\" dans relations.json)."
            ))
        raise SystemExit(1)

    if len(candidates) > 1:
        print(out.error(f"Relation ambiguë : plusieurs relations {source_entity}.{relation_name} trouvées."))
        raise SystemExit(1)

    rel = candidates[0]

    if rel.get("type") != "many_to_many":
        print(out.error(
            f"Relation {source_entity}.{relation_name} n'est pas many_to_many.\n"
            "make:pivot-crud est réservé aux relations many_to_many avec pivot.fields[]."
        ))
        raise SystemExit(1)

    pivot = _as_dict(rel.get("pivot"))
    if pivot is None:
        print(out.error(
            f"Relation {source_entity}.{relation_name} n'a pas de bloc pivot.\n"
            "make:pivot-crud est réservé aux pivots avec attributs."
        ))
        raise SystemExit(1)

    fields = _as_list(pivot.get("fields"))
    if fields is None or len(fields) == 0:
        print(out.error(
            f"Relation {source_entity}.{relation_name} : pivot.fields[] est absent ou vide.\n"
            "make:pivot-crud est réservé aux pivots avec attributs.\n"
            "Utilisez make:crud pour les pivots simples."
        ))
        raise SystemExit(1)

    field_names: list[str] = []
    for f in fields:
        fd = _as_dict(f)
        if fd is None:
            continue
        name = fd.get("name")
        if isinstance(name, str):
            field_names.append(name)
    pivot_field_names = tuple(field_names)

    return ResolvedPivotRelation(
        from_entity=source_entity,
        to_entity=rel.get("to", ""),
        relation_name=relation_name,
        pivot_table=pivot.get("table", ""),
        from_key=pivot.get("from_key", ""),
        to_key=pivot.get("to_key", ""),
        pivot_fields=pivot_field_names,
    )


# ── Contenu généré ────────────────────────────────────────────────────────────

def _build_controller(rel: ResolvedPivotRelation) -> str:
    src_snake = _to_snake(rel.from_entity)
    tgt_snake = _to_snake(rel.to_entity)
    fields_repr = repr(list(rel.pivot_fields))

    return f'''\
"""mvc/controllers/pivot/{src_snake}_{rel.relation_name}_pivot_controller.py

Sous-CRUD Pivot advanced pour {rel.from_entity}.{rel.relation_name}.
Généré par forge make:pivot-crud {rel.from_entity} {rel.relation_name}.

Ce contrôleur est opt-in — les routes (imbriquées sous la source) sont à
déclarer manuellement dans mvc/routes.py. Noms de routes au format ADR-029
(<contrôleur>-<méthode>) ; les identifiants sont lus depuis les paramètres
de route « source_id » et « target_id ».

Exemple de routes à ajouter :
    with router.group("") as g:
        g.add("GET",  "/{src_snake}s/{{source_id}}/{rel.relation_name}", controller.index, name="{src_snake}_{rel.relation_name}_pivot-index")
        g.add("GET",  "/{src_snake}s/{{source_id}}/{rel.relation_name}/add", controller.add_form, name="{src_snake}_{rel.relation_name}_pivot-add_form")
        g.add("POST", "/{src_snake}s/{{source_id}}/{rel.relation_name}/add", controller.add, name="{src_snake}_{rel.relation_name}_pivot-add")
        g.add("GET",  "/{src_snake}s/{{source_id}}/{rel.relation_name}/{{target_id}}/edit", controller.edit_form, name="{src_snake}_{rel.relation_name}_pivot-edit_form")
        g.add("POST", "/{src_snake}s/{{source_id}}/{rel.relation_name}/{{target_id}}/edit", controller.edit, name="{src_snake}_{rel.relation_name}_pivot-edit")
        g.add("POST", "/{src_snake}s/{{source_id}}/{rel.relation_name}/{{target_id}}/remove", controller.remove, name="{src_snake}_{rel.relation_name}_pivot-remove")
"""
from __future__ import annotations

from forge_mvc_entities import PivotAdvancedService, PivotConstraintError, pivot_error_to_form_error
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller import BaseController

_SERVICE = PivotAdvancedService(
    table={rel.pivot_table!r},
    source_key={rel.from_key!r},
    target_key={rel.to_key!r},
    pivot_fields={fields_repr},
)

_TEMPLATE_INDEX = "pivot/{src_snake}_{rel.relation_name}/index.html"
_TEMPLATE_FORM  = "pivot/{src_snake}_{rel.relation_name}/form.html"


class {rel.from_entity}{rel.relation_name.capitalize()}PivotController:

    @staticmethod
    def index(request: Request) -> Response:
        """Liste les associations {rel.pivot_table}."""
        {src_snake}_id = int(request.route("source_id"))
        rows = _SERVICE.list_for_source({src_snake}_id)
        return BaseController.render(_TEMPLATE_INDEX, context={{
            "{src_snake}_id": {src_snake}_id,
            "rows": rows,
        }}, request=request)

    @staticmethod
    def add_form(request: Request) -> Response:
        """Formulaire d'ajout d'une association."""
        {src_snake}_id = int(request.route("source_id"))
        return BaseController.render(_TEMPLATE_FORM, context={{
            "{src_snake}_id": {src_snake}_id,
            "row": None,
            "action": f"/{src_snake}s/{{{src_snake}_id}}/{rel.relation_name}/add",
            "error": None,
        }}, request=request)

    @staticmethod
    def add(request: Request) -> Response:
        """Crée une nouvelle association."""
        {src_snake}_id = int(request.route("source_id"))
        {tgt_snake}_id = int(request.form("{rel.to_key}"))
        pivot_data = {{
            field: request.form(field)
            for field in {fields_repr}
            if request.form(field) is not None
        }}
        try:
            _SERVICE.attach({src_snake}_id, {tgt_snake}_id, pivot_data)
            return BaseController.redirect(f"/{src_snake}s/{{{src_snake}_id}}/{rel.relation_name}", request=request)
        except Exception as exc:
            error = pivot_error_to_form_error(exc)
            return BaseController.render(_TEMPLATE_FORM, context={{
                "{src_snake}_id": {src_snake}_id,
                "row": None,
                "action": f"/{src_snake}s/{{{src_snake}_id}}/{rel.relation_name}/add",
                "error": error,
            }}, request=request)

    @staticmethod
    def edit_form(request: Request) -> Response:
        """Formulaire de modification d'une association."""
        {src_snake}_id = int(request.route("source_id"))
        {tgt_snake}_id = int(request.route("target_id"))
        row = _SERVICE.get({src_snake}_id, {tgt_snake}_id)
        if row is None:
            return BaseController.redirect(f"/{src_snake}s/{{{src_snake}_id}}/{rel.relation_name}", request=request)
        return BaseController.render(_TEMPLATE_FORM, context={{
            "{src_snake}_id": {src_snake}_id,
            "row": row,
            "action": f"/{src_snake}s/{{{src_snake}_id}}/{rel.relation_name}/{{{tgt_snake}_id}}/edit",
            "error": None,
        }}, request=request)

    @staticmethod
    def edit(request: Request) -> Response:
        """Modifie les attributs pivot d'une association."""
        {src_snake}_id = int(request.route("source_id"))
        {tgt_snake}_id = int(request.route("target_id"))
        pivot_data = {{
            field: request.form(field)
            for field in {fields_repr}
            if request.form(field) is not None
        }}
        try:
            _SERVICE.update({src_snake}_id, {tgt_snake}_id, pivot_data)
            return BaseController.redirect(f"/{src_snake}s/{{{src_snake}_id}}/{rel.relation_name}", request=request)
        except Exception as exc:
            error = pivot_error_to_form_error(exc)
            row = _SERVICE.get({src_snake}_id, {tgt_snake}_id)
            return BaseController.render(_TEMPLATE_FORM, context={{
                "{src_snake}_id": {src_snake}_id,
                "row": row,
                "action": f"/{src_snake}s/{{{src_snake}_id}}/{rel.relation_name}/{{{tgt_snake}_id}}/edit",
                "error": error,
            }}, request=request)

    @staticmethod
    def remove(request: Request) -> Response:
        """Supprime une association."""
        {src_snake}_id = int(request.route("source_id"))
        {tgt_snake}_id = int(request.route("target_id"))
        _SERVICE.detach({src_snake}_id, {tgt_snake}_id)
        return BaseController.redirect(f"/{src_snake}s/{{{src_snake}_id}}/{rel.relation_name}", request=request)


controller = {rel.from_entity}{rel.relation_name.capitalize()}PivotController()
'''


def _build_index_template(rel: ResolvedPivotRelation) -> str:
    src_snake = _to_snake(rel.from_entity)
    tgt_snake = _to_snake(rel.to_entity)
    field_headers = "".join(f"        <th>{f}</th>\n" for f in rel.pivot_fields)
    field_cells = "".join(
        f"            <td>{{{{ row.pivot_data.get('{f}', '') }}}}</td>\n"
        for f in rel.pivot_fields
    )

    return f"""\
{{% extends "layouts/app.html" %}}
{{% block content %}}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold text-gray-800">
        {rel.from_entity} #{{{ src_snake}_id}} — {rel.relation_name}
    </h1>
    <a href="/{src_snake}s/{{{{ {src_snake}_id }}}}/{rel.relation_name}/add"
       class="text-blue-600 hover:underline">Ajouter</a>
</div>

{{% if rows %}}
<table class="w-full bg-white shadow rounded">
    <thead>
        <tr>
        <th>{tgt_snake}</th>
{field_headers}        <th>Actions</th>
        </tr>
    </thead>
    <tbody>
    {{% for row in rows %}}
        <tr>
            <td>{{{{ row.target_id }}}}</td>
{field_cells}            <td>
                <a href="/{src_snake}s/{{{{ {src_snake}_id }}}}/{rel.relation_name}/{{{{ row.target_id }}}}/edit">Modifier</a>
                <form method="post" action="/{src_snake}s/{{{{ {src_snake}_id }}}}/{rel.relation_name}/{{{{ row.target_id }}}}/remove" style="display:inline">
                    <input type="hidden" name="csrf_token" value="{{{{ csrf_token }}}}">
                    <button type="submit">Retirer</button>
                </form>
            </td>
        </tr>
    {{% endfor %}}
    </tbody>
</table>
{{% else %}}
<p class="text-gray-500">Aucune association.</p>
{{% endif %}}
{{% endblock %}}
"""


def _build_form_template(rel: ResolvedPivotRelation) -> str:
    src_snake = _to_snake(rel.from_entity)
    tgt_snake = _to_snake(rel.to_entity)
    field_inputs = "".join(
        f"""<div>
    <label>{f}</label>
    <input type="text" name="{f}" value="{{{{ row.pivot_data.get('{f}', '') if row else '' }}}}">
</div>
"""
        for f in rel.pivot_fields
    )

    return f"""\
{{% extends "layouts/app.html" %}}
{{% block content %}}
<h1 class="text-2xl font-bold text-gray-800 mb-6">
    {{{{ "Modifier" if row else "Ajouter" }}}} — {rel.from_entity}.{rel.relation_name}
</h1>

{{% if error %}}
<div class="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded mb-4">
    {{{{ error.message }}}}
</div>
{{% endif %}}

<form method="post" action="{{{{ action }}}}">
    <input type="hidden" name="csrf_token" value="{{{{ csrf_token }}}}">

    {{% if not row %}}
    <div>
        <label>{tgt_snake}</label>
        <input type="number" name="{rel.to_key}" required>
    </div>
    {{% endif %}}

{field_inputs}
    <button type="submit">Enregistrer</button>
    <a href="/{src_snake}s/{{{{ {src_snake}_id }}}}/{rel.relation_name}">Annuler</a>
</form>
{{% endblock %}}
"""


# ── Écriture fichier ──────────────────────────────────────────────────────────

def _write_if_new(
    path: Path,
    content: str,
    result: MakePivotCrudResult,
    dry_run: bool,
) -> None:
    if path.exists():
        result.preserved.append(path)
    else:
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        result.created.append(path)


# ── Entrée principale ─────────────────────────────────────────────────────────

def make_pivot_crud(
    source_entity: str,
    relation_name: str,
    *,
    entities_root: Path,
    output_root: Path,
    dry_run: bool = False,
) -> MakePivotCrudResult:
    """Génère un sous-CRUD Pivot advanced pour une relation many_to_many."""
    relations_path = entities_root / "relations.json"
    rel = resolve_pivot_relation(
        source_entity,
        relation_name,
        relations_path=relations_path,
    )

    src_snake = _to_snake(rel.from_entity)
    controllers_dir = output_root / "mvc" / "controllers" / "pivot"
    templates_dir = output_root / "mvc" / "templates" / "pivot" / f"{src_snake}_{rel.relation_name}"

    controller_path = controllers_dir / f"{src_snake}_{rel.relation_name}_pivot_controller.py"
    index_path = templates_dir / "index.html"
    form_path = templates_dir / "form.html"

    result = MakePivotCrudResult(dry_run=dry_run)

    _write_if_new(controller_path, _build_controller(rel), result, dry_run)
    _write_if_new(index_path, _build_index_template(rel), result, dry_run)
    _write_if_new(form_path, _build_form_template(rel), result, dry_run)

    return result


def cmd_make_pivot_crud_main(args: list[str]) -> None:
    if len(args) < 2 or args[0].startswith("-"):
        print("Usage : forge make:pivot-crud EntitéSource nomRelation [--dry-run]")
        raise SystemExit(1)

    source_entity = args[0]
    relation_name = args[1]
    dry_run = "--dry-run" in args
    unknown = [a for a in args[2:] if a != "--dry-run"]
    if unknown:
        print(out.error(f"Arguments inconnus : {' '.join(unknown)}"))
        raise SystemExit(1)

    result = make_pivot_crud(
        source_entity,
        relation_name,
        entities_root=Path("mvc") / "entities",
        output_root=Path("."),
        dry_run=dry_run,
    )

    if dry_run:
        print(out.dry_run("Aucun fichier créé."))
        if result.created:
            print("Fichiers qui seraient générés :")
            for p in result.created:
                print(f"  - {p.as_posix()}")
    else:
        for p in result.created:
            print(out.created(p.as_posix()))
        for p in result.preserved:
            print(out.preserved(p.as_posix(), "← fichier existant, non touché"))

        if result.created:
            src_snake = _to_snake(source_entity)
            print()
            print(out.ok(f"Pivot advanced généré pour {source_entity}.{relation_name}"))
            print()
            ctrl_ref = f"{src_snake}_{relation_name}_ctrl"
            name_prefix = f"{src_snake}_{relation_name}_pivot"
            base = f"/{src_snake}s/{{source_id}}/{relation_name}"
            print("Routes à ajouter dans mvc/routes.py :")
            print(f'    # Pivot {source_entity}.{relation_name}')
            print(f'    from mvc.controllers.pivot.{src_snake}_{relation_name}_pivot_controller import controller as {ctrl_ref}')
            print('    with router.group("") as g:')
            print(f'        g.add("GET",  "{base}", {ctrl_ref}.index, name="{name_prefix}-index")')
            print(f'        g.add("GET",  "{base}/add", {ctrl_ref}.add_form, name="{name_prefix}-add_form")')
            print(f'        g.add("POST", "{base}/add", {ctrl_ref}.add, name="{name_prefix}-add")')
            print(f'        g.add("GET",  "{base}/{{target_id}}/edit", {ctrl_ref}.edit_form, name="{name_prefix}-edit_form")')
            print(f'        g.add("POST", "{base}/{{target_id}}/edit", {ctrl_ref}.edit, name="{name_prefix}-edit")')
            print(f'        g.add("POST", "{base}/{{target_id}}/remove", {ctrl_ref}.remove, name="{name_prefix}-remove")')
