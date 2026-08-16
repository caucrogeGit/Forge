#!/usr/bin/env python3
# pyright: strict
"""
Ajoute une relation Forge dans mvc/entities/relations.json.

Usage :
    forge make:relation
    forge make:relation --type many_to_one --from Eleve --to Classe
    forge make:relation --type many_to_many --from Article --to Tag

Donner `--from` et `--to` suffit a passer en mode non interactif : la relation
est alors decrite entierement par la ligne de commande, avec les memes defauts
que le dialogue (ENTITIES-NON-INTERACTIVE-002).

Options communes :
    --type many_to_one|many_to_many   defaut many_to_one
    --name <nom>                      defaut : cible en snake (+ « s » en m2m)
    --inverse-name <nom>              cote cible, facultatif
    --on-delete <action>              defaut restrict (m2o), cascade (m2m)

many_to_one :
    --foreign-key <colonne>           defaut <nom>_id
    --not-null                        la FK devient obligatoire (defaut nullable)
    --no-index                        pas d'index sur la FK (defaut : index)

many_to_many :
    --pivot-table <table>             defaut <source>_<cible>
    --from-key <colonne>              defaut <source>_id
    --to-key <colonne>                defaut <cible>_id
    --pivot-field <spec>              attribut du pivot, repetable

Attributs de pivot (ENTITIES-PIVOT-FIELDS-001) :

    forge make:relation --type many_to_many --from Article --to Tag         --pivot-field "position:integer"         --pivot-field "note:string:max_length=200,optional"

Meme grammaire que `make:entity --field` : nom:type[:attributs]. Une relation
qui porte au moins un attribut releve de `make:pivot-crud` et non de
`make:crud`. Sans option, le pivot reste simple, comme avant.

Deux des quatorze types d'entite ne s'appliquent pas a un pivot : `foreign_key`,
la cle etrangere etant deja portee par from_key et to_key, et `slug`, qui
designe une ressource et non un lien. Les noms `id`, from_key et to_key sont
geres par Forge et ne peuvent pas etre redeclares.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable, cast

from forge_mvc_entities.make_entity import entities_dir, to_snake
from forge_mvc_entities.relations import (
    ALLOWED_RELATION_TYPES,
    EntityRelationsError,
    load_entity_definitions,
    validate_relations_definition,
)
from forge_mvc_entities.validation import EntityDefinitionError

ALLOWED_ACTIONS_CANONICAL = {"restrict", "cascade", "set_null", "no_action"}

_CANONICAL_EMPTY: dict[str, Any] = {"schema_version": "1.0", "relations": []}


def _prompt_text(
    label: str,
    *,
    default: str | None = None,
    allow_empty: bool = False,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    if input_fn is None:
        input_fn = input
    prompt = label
    if default not in {None, ""}:
        prompt += f" [{default}]"
    prompt += " : "

    while True:
        value = input_fn(prompt).strip()
        if value:
            return value
        if default is not None:
            return default
        if allow_empty:
            return ""
        print("Une valeur est requise.")


def _prompt_yes_no(
    label: str,
    *,
    default: bool = False,
    input_fn: Callable[[str], str] | None = None,
) -> bool:
    if input_fn is None:
        input_fn = input
    suffix = "[O/n]" if default else "[o/N]"
    while True:
        value = input_fn(f"{label} {suffix} : ").strip().lower()
        if not value:
            return default
        if value in {"o", "oui", "y", "yes"}:
            return True
        if value in {"n", "non", "no"}:
            return False
        print("Réponse attendue : o ou n.")


def _prompt_relation_type(*, input_fn: Callable[[str], str] | None = None) -> str:
    if input_fn is None:
        input_fn = input
    default = "many_to_one"
    allowed_display = ", ".join(sorted(ALLOWED_RELATION_TYPES))
    help_text = f"Type de relation ({allowed_display})"
    while True:
        value = _prompt_text(help_text, default=default, input_fn=input_fn).strip().lower()
        if value in ALLOWED_RELATION_TYPES:
            return value
        print(f"Type de relation invalide. Valeurs supportées : {allowed_display}.")


def _prompt_entity(
    label: str,
    entity_names: list[str],
    *,
    default: str | None = None,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    help_label = f"{label} ({', '.join(entity_names)})"
    while True:
        value = _prompt_text(help_label, default=default, input_fn=input_fn)
        if value in entity_names:
            return value
        print(f"Entité inconnue. Valeurs disponibles : {', '.join(entity_names)}.")


def _prompt_action_canonical(
    label: str,
    *,
    default: str,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    allowed = sorted(ALLOWED_ACTIONS_CANONICAL)
    help_label = f"{label} ({', '.join(allowed)})"
    while True:
        value = _prompt_text(help_label, default=default, input_fn=input_fn).strip().lower()
        if value in ALLOWED_ACTIONS_CANONICAL:
            return value
        print(f"Valeur invalide. Valeurs supportées : {', '.join(allowed)}.")


def _load_relations_document(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": "1.0", "relations": []}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path.as_posix()}: JSON invalide ({exc.msg} à la ligne {exc.lineno}, colonne {exc.colno})"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"{path.as_posix()}: la racine doit être un objet JSON")
    if "relations" not in data:
        raise ValueError(f"{path.as_posix()}: relations manquant")
    if not isinstance(data["relations"], list):
        raise ValueError(f"{path.as_posix()}: relations doit être une liste")
    if "format_version" in data:
        raise ValueError(
            f"{path.as_posix()}: format_version: 1 n'est plus accepté pour relations.json. "
            'Utilisez schema_version: "1.0".'
        )
    if "schema_version" not in data:
        raise ValueError(f"{path.as_posix()}: schema_version manquant")
    return cast("dict[str, Any]", data)


def _prompt_pivot_fields(
    *,
    from_key: str,
    to_key: str,
    input_fn: Callable[[str], str] | None = None,
) -> "list[dict[str, Any]]":
    """Demande les attributs du pivot, un par ligne, jusqu'a une reponse vide.

    Le dialogue ne posait pas la question et ecrivait toujours une liste vide,
    si bien que `make:pivot-crud` restait hors d'atteinte des deux modes
    (ENTITIES-PIVOT-FIELDS-001).

    Repondre vide d'emblee rend exactement l'ancien comportement, un pivot
    simple : ouvrir des attributs par defaut ferait basculer vers l'autre
    generateur des relations qui n'ont rien demande.

    Une saisie fautive est signalee et **redemandee**, jamais fatale : le
    dialogue a deja pose huit reponses, les perdre pour une virgule serait
    payer cher une faute de frappe.
    """
    if input_fn is None:
        input_fn = input

    print(
        "Attributs du pivot, un par ligne, vide pour terminer.\n"
        "  Grammaire : nom:type[:attributs] — la meme que make:entity --field.\n"
        "  Exemple   : position:integer  ou  note:string:max_length=200,optional"
    )
    fields: list[dict[str, Any]] = []
    while True:
        spec = _prompt_text("Attribut du pivot", allow_empty=True, input_fn=input_fn)
        if not spec:
            return fields
        try:
            fields.append(
                parse_pivot_field_spec(spec, from_key=from_key, to_key=to_key)
            )
        except ValueError as exc:
            print(f"{exc} Reessayez.")


def _build_m2m_relation_interactively(
    entity_map: dict[str, dict[str, Any]],
    entity_names: list[str],
    *,
    input_fn: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    from_entity = _prompt_entity("Entité source", entity_names, input_fn=input_fn)
    to_entity = _prompt_entity("Entité cible", entity_names, input_fn=input_fn)

    from_snake = to_snake(from_entity)
    to_snake_name = to_snake(to_entity)

    default_name = to_snake_name + "s"
    relation_name = _prompt_text("Nom de la relation", default=default_name, input_fn=input_fn)

    inverse_name = _prompt_text(
        "Nom inverse (côté cible, optionnel)",
        allow_empty=True,
        input_fn=input_fn,
    )

    default_table = f"{from_snake}_{to_snake_name}"
    pivot_table = _prompt_text("Table pivot", default=default_table, input_fn=input_fn)

    default_from_key = f"{from_snake}_id"
    from_key = _prompt_text("Colonne source (from_key)", default=default_from_key, input_fn=input_fn)

    default_to_key = f"{to_snake_name}_id"
    to_key = _prompt_text("Colonne cible (to_key)", default=default_to_key, input_fn=input_fn)

    on_delete = _prompt_action_canonical("ON DELETE pivot", default="cascade", input_fn=input_fn)

    pivot_fields = _prompt_pivot_fields(
        from_key=from_key, to_key=to_key, input_fn=input_fn
    )

    relation: dict[str, Any] = {
        "type": "many_to_many",
        "from": from_entity,
        "to": to_entity,
        "name": relation_name,
    }
    if inverse_name:
        relation["inverse_name"] = inverse_name
    relation["pivot"] = {
        "table": pivot_table,
        "from_key": from_key,
        "to_key": to_key,
        "id": True,
        "unique_pair": True,
        "on_delete": on_delete,
        "fields": pivot_fields,
    }
    return relation


def _build_relation_interactively(
    entity_map: dict[str, dict[str, Any]],
    *,
    input_fn: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    entity_names = sorted(entity_map)
    relation_type = _prompt_relation_type(input_fn=input_fn)

    if relation_type == "many_to_many":
        return _build_m2m_relation_interactively(entity_map, entity_names, input_fn=input_fn)

    from_entity = _prompt_entity("Entité source (porte la FK)", entity_names, input_fn=input_fn)
    to_entity = _prompt_entity("Entité cible (porte la PK visée)", entity_names, input_fn=input_fn)

    default_name = to_snake(to_entity)
    relation_name = _prompt_text("Nom de la relation", default=default_name, input_fn=input_fn)

    inverse_name = _prompt_text(
        "Nom inverse (côté cible, optionnel)",
        allow_empty=True,
        input_fn=input_fn,
    )

    default_fk = f"{relation_name}_id"
    foreign_key = _prompt_text("Colonne clé étrangère", default=default_fk, input_fn=input_fn)

    nullable = _prompt_yes_no("FK nullable ?", default=True, input_fn=input_fn)
    on_delete = _prompt_action_canonical("Politique ON DELETE", default="restrict", input_fn=input_fn)
    index = _prompt_yes_no("Créer un index sur la FK ?", default=True, input_fn=input_fn)

    relation: dict[str, Any] = {
        "type": relation_type,
        "from": from_entity,
        "to": to_entity,
        "name": relation_name,
    }
    if inverse_name:
        relation["inverse_name"] = inverse_name
    relation["foreign_key"] = foreign_key
    relation["nullable"] = nullable
    relation["on_delete"] = on_delete
    relation["index"] = index

    return relation


def _relation_summary(relation: dict[str, Any]) -> str:
    lines = [
        f"Type : {relation['type']}",
        f"Source : {relation['from']}",
        f"Cible : {relation['to']}",
        f"Relation : {relation['name']}",
    ]
    if relation.get("inverse_name"):
        lines.append(f"Inverse : {relation['inverse_name']}")
    if relation.get("type") == "many_to_many" and isinstance(relation.get("pivot"), dict):
        pivot = relation["pivot"]
        lines += [
            f"Table pivot : {pivot.get('table', '')}",
            f"From key : {pivot.get('from_key', '')}",
            f"To key : {pivot.get('to_key', '')}",
            f"ON DELETE pivot : {pivot.get('on_delete', '')}",
        ]
    else:
        lines += [
            f"Clé étrangère : {relation.get('foreign_key', '')}",
            f"Nullable : {relation.get('nullable', True)}",
            f"ON DELETE : {relation.get('on_delete', '')}",
            f"Index : {relation.get('index', True)}",
        ]
    return "\n".join(lines)


def _ensure_no_obvious_duplicates(relations: list[dict[str, Any]], relation: dict[str, Any], *, source: str) -> None:
    new_name = relation.get("name")
    new_fk = relation.get("foreign_key")
    new_from = relation.get("from")
    new_pivot_table = relation.get("pivot", {}).get("table") if isinstance(relation.get("pivot"), dict) else None
    for existing in relations:
        # retour-011 : le nom (accesseur) et la clé étrangère (colonne) sont propres à
        # l'entité source ; on ne les compare qu'entre relations de même `from`.
        same_source = existing.get("from") == new_from
        if same_source and existing.get("name") == new_name:
            raise ValueError(f"{source}: une relation nommée {new_name!r} existe déjà sur {new_from}")
        existing_fk = existing.get("foreign_key")
        if same_source and new_fk and existing_fk and existing_fk == new_fk:
            raise ValueError(f"{source}: une clé étrangère nommée {new_fk!r} existe déjà sur {new_from}")
        existing_pivot = existing.get("pivot", {}).get("table") if isinstance(existing.get("pivot"), dict) else None
        if new_pivot_table and existing_pivot and existing_pivot == new_pivot_table:
            raise ValueError(f"{source}: une table pivot nommée {new_pivot_table!r} existe déjà")
        if "from" in relation and "from" in existing:
            if (
                existing.get("type") == relation.get("type")
                and existing.get("from") == relation.get("from")
                and existing.get("to") == relation.get("to")
            ):
                raise ValueError(f"{source}: cette relation existe déjà")


def _inject_fk_field_into_entity(
    entities_dir_path: Path,
    from_entity: str,
    foreign_key: str,
    references: str,
    *,
    nullable: bool,
) -> str | None:
    """Ajoute un champ `foreign_key` à l'entité source (ADR-069), de façon chirurgicale
    (écriture annoncée, préserve les autres champs). Retourne le chemin modifié, ou None
    si le champ existe déjà ou si le fichier d'entité est introuvable.
    """
    entity_path = entities_dir_path / to_snake(from_entity) / f"{to_snake(from_entity)}.json"
    if not entity_path.exists():
        return None
    data = cast("dict[str, Any]", json.loads(entity_path.read_text(encoding="utf-8")))
    raw_fields = data.get("fields")
    if not isinstance(raw_fields, list):
        return None
    fields = cast("list[dict[str, Any]]", raw_fields)
    if any(f.get("name") == foreign_key for f in fields):
        return None
    fk_field: dict[str, Any] = {"name": foreign_key, "type": "foreign_key", "references": references}
    if not nullable:
        fk_field["required"] = True
    fields.append(fk_field)
    entity_path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return entity_path.as_posix()


#: Types d'entite qui n'ont pas de sens sur une association
#: (ENTITIES-PIVOT-FIELDS-001). La cle etrangere est deja portee par `from_key`
#: et `to_key`, et un slug designe une ressource et non un lien. Mesure : les
#: types admis par le pivot sont les quatorze de l'entite moins ces deux-la.
_TYPES_HORS_PIVOT = frozenset({"foreign_key", "slug"})


def parse_pivot_field_spec(spec: str, *, from_key: str, to_key: str) -> "dict[str, Any]":
    """Traduit « nom:type:attributs » en attribut de pivot canonique.

    La grammaire est **celle de `make:entity --field`**, et le parseur est le
    meme : une seconde grammaire pour la meme intention contredirait le
    principe 11, et divergerait au premier attribut ajoute d'un cote.

    Deux refus viennent en plus, parce qu'un pivot n'est pas une entite. Ils
    tombent ici, a la commande, plutot qu'a la validation du document : celle-ci
    dirait « type invalide » sans dire que c'est le pivot qui le refuse.
    """
    from forge_mvc_entities.make_entity import parse_field_spec

    # Le type se lit AVANT le parsage : `parse_field_spec` exige `references=`
    # sur un `foreign_key` et rendrait ce reproche-la, qui n'est pas la raison.
    # Un type sans emploi ici doit s'entendre dire cela, et rien d'autre.
    parties = spec.split(":")
    demande = parties[1].strip().lower() if len(parties) > 1 else ""
    if demande in _TYPES_HORS_PIVOT:
        nom = parties[0].strip()
        raise ValueError(
            f"Le type «{demande}» ne s'applique pas a un attribut de pivot "
            f"(champ «{nom}»). La cle etrangere est deja portee par from_key "
            "et to_key, et un slug designe une ressource, pas un lien."
        )

    field = parse_field_spec(spec)
    reserves = {"id", from_key, to_key}
    if field["name"] in reserves:
        raise ValueError(
            f"«{field['name']}» est gere par Forge dans la table pivot "
            f"(reserves : {', '.join(sorted(reserves))}). Le redeclarer "
            "produirait une colonne en double."
        )
    return field


class _Options:
    """Ce que la ligne de commande a demande, sans defaut applique."""

    def __init__(self) -> None:
        self.type: str = "many_to_one"
        self.from_entity: str | None = None
        self.to_entity: str | None = None
        self.name: str | None = None
        self.inverse_name: str | None = None
        self.on_delete: str | None = None
        self.foreign_key: str | None = None
        self.nullable: bool = True
        self.index: bool = True
        self.pivot_table: str | None = None
        self.from_key: str | None = None
        self.to_key: str | None = None
        self.pivot_fields: list[str] = []


_AVEC_VALEUR = {
    "--type": "type", "--from": "from_entity", "--to": "to_entity",
    "--name": "name", "--inverse-name": "inverse_name", "--on-delete": "on_delete",
    "--foreign-key": "foreign_key", "--pivot-table": "pivot_table",
    "--from-key": "from_key", "--to-key": "to_key",
}


def parse_relation_args(args: list[str]) -> _Options:
    options = _Options()
    saute = False
    for index, arg in enumerate(args):
        if saute:
            saute = False
            continue
        if arg == "--pivot-field":
            # Repetable, contrairement aux options de _AVEC_VALEUR qui
            # ecrasent : l'ordre des attributs decide de celui des colonnes.
            if index + 1 >= len(args):
                raise ValueError("L'option --pivot-field attend une valeur.")
            options.pivot_fields.append(args[index + 1].strip())
            saute = True
            continue
        if arg in _AVEC_VALEUR:
            if index + 1 >= len(args):
                raise ValueError(f"L'option {arg} attend une valeur.")
            setattr(options, _AVEC_VALEUR[arg], args[index + 1].strip())
            saute = True
            continue
        if arg == "--not-null":
            options.nullable = False
            continue
        if arg == "--no-index":
            options.index = False
            continue
        raise ValueError(f"Option inconnue : {arg}.")
    return options


def build_relation_from_options(options: _Options) -> dict[str, Any]:
    """Meme structure que le dialogue, memes defauts, sans terminal.

    Les defauts comptent autant que les options : s'ils differaient, la meme
    intention produirait deux relations selon le mode employe.
    """
    if options.type not in ALLOWED_RELATION_TYPES:
        raise ValueError(
            f"Type de relation invalide «{options.type}». "
            f"Attendus : {', '.join(sorted(ALLOWED_RELATION_TYPES))}."
        )
    if not options.from_entity or not options.to_entity:
        raise ValueError("--from et --to sont requis en mode non interactif.")
    if options.pivot_fields and options.type != "many_to_many":
        # Accepter l'option sans pivot serait un silence : la relation partirait
        # sans les attributs demandes, et rien ne le dirait.
        raise ValueError(
            "--pivot-field ne vaut que pour une relation many_to_many : "
            f"le type demande est «{options.type}», qui n'a pas de table pivot."
        )

    from_snake = to_snake(options.from_entity)
    to_snake_name = to_snake(options.to_entity)

    relation: dict[str, Any] = {
        "type": options.type,
        "from": options.from_entity,
        "to": options.to_entity,
    }

    if options.type == "many_to_many":
        from_key = options.from_key or f"{from_snake}_id"
        to_key = options.to_key or f"{to_snake_name}_id"
        relation["name"] = options.name or f"{to_snake_name}s"
        if options.inverse_name:
            relation["inverse_name"] = options.inverse_name
        relation["pivot"] = {
            "table": options.pivot_table or f"{from_snake}_{to_snake_name}",
            "from_key": from_key,
            "to_key": to_key,
            "id": True,
            "unique_pair": True,
            "on_delete": options.on_delete or "cascade",
            "fields": [
                parse_pivot_field_spec(spec, from_key=from_key, to_key=to_key)
                for spec in options.pivot_fields
            ],
        }
        return relation

    relation["name"] = options.name or to_snake_name
    if options.inverse_name:
        relation["inverse_name"] = options.inverse_name
    relation["foreign_key"] = options.foreign_key or f"{relation['name']}_id"
    relation["nullable"] = options.nullable
    relation["on_delete"] = options.on_delete or "restrict"
    relation["index"] = options.index
    return relation


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in {"-h", "--help"}:
        print((__doc__ or "").strip())
        raise SystemExit(0)

    # Donner --from et --to suffit : exiger EN PLUS un drapeau ferait echouer la
    # forme evidente sur un detail, comme pour make:entity --field.
    options: _Options | None = None
    if args:
        try:
            options = parse_relation_args(args)
        except ValueError as exc:
            print(f"[ERREUR] {exc}")
            print((__doc__ or "").strip())
            raise SystemExit(1) from None

    try:
        target_entities_dir = entities_dir()
        entity_map = load_entity_definitions(target_entities_dir)
    except EntityDefinitionError as exc:
        print(f"[ERREUR] {exc}")
        raise SystemExit(1)

    if not entity_map:
        print("[ERREUR] Aucune entité disponible. Créez d'abord vos entités avec forge make:entity.")
        raise SystemExit(1)

    relations_path = target_entities_dir / "relations.json"
    try:
        document = _load_relations_document(relations_path)
        relation = (build_relation_from_options(options) if options is not None
                    else _build_relation_interactively(entity_map))
        _ensure_no_obvious_duplicates(document["relations"], relation, source=relations_path.as_posix())
        candidate = {
            "schema_version": "1.0",
            "relations": [*document["relations"], relation],
        }
        validate_relations_definition(candidate, source=str(relations_path), entities_root=target_entities_dir)
    except (ValueError, EntityRelationsError) as exc:
        print(f"[ERREUR] {exc}")
        raise SystemExit(1)

    print("Résumé avant écriture")
    print(_relation_summary(relation))
    print("")
    print("Objet relation ajouté :")
    print(json.dumps(relation, indent=2, ensure_ascii=True))
    print("")
    # La ligne de commande EST la confirmation : redemander sans terminal
    # rendrait le mode non interactif inutilisable.
    if options is None and not _prompt_yes_no(
        "Confirmer l'écriture de mvc/entities/relations.json ?", default=True
    ):
        print("Aucune écriture effectuée.")
        raise SystemExit(0)

    relations_path.parent.mkdir(parents=True, exist_ok=True)
    relations_path.write_text(json.dumps(candidate, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print("[OK] Relation ajoutée dans mvc/entities/relations.json")

    # ADR-069 : la FK devient un champ de première classe de l'entité source.
    if relation.get("type") == "many_to_one" and relation.get("foreign_key"):
        modified = _inject_fk_field_into_entity(
            target_entities_dir,
            relation["from"],
            relation["foreign_key"],
            relation["to"],
            nullable=bool(relation.get("nullable", True)),
        )
        if modified is not None:
            print(f"[MODIFIE] {modified} (champ foreign_key {relation['foreign_key']} ajouté)")
        else:
            print(f"[INFO] Le champ {relation['foreign_key']} existe déjà dans l'entité {relation['from']}.")

    print("[INFO] Régénérez ensuite : forge sync:entity <Entite> (colonne FK) puis")
    print("       forge sync:relations (contrainte + index).")


if __name__ == "__main__":
    main()
