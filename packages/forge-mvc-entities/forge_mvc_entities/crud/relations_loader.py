# pyright: strict
# pyright: reportPrivateUsage=false
# pyright: reportUnusedFunction=false
"""Relation loading helpers for the CRUD generator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from forge_mvc_entities.relations import (
    ValidatedCanonicalManyToManyRelation,
    load_entity_definitions,
    validate_relations_definition,
)
from forge_mvc_entities.crud.context import (
    CrudManyToOneRelation,
    CrudManyToManyRelation,
)
from forge_mvc_entities.crud.utils import (
    _pk_field,
    _to_snake,
    _text_label_fields,
)


_PREFERRED_LABEL_NAMES = ("name", "nom", "title", "titre", "label", "libelle")


def _entity_definition_by_relation_name(entity_map: dict[str, dict[str, Any]], name: str) -> dict[str, Any] | None:
    needle = name.lower()
    for definition in entity_map.values():
        if definition["entity"].lower() == needle:
            return definition
        if definition["table"].lower() == needle:
            return definition
        if _to_snake(definition["entity"]) == needle:
            return definition
    return None


def _load_crud_many_to_one_relations(
    definition: dict[str, Any],
    entities_root: Path,
) -> list[CrudManyToOneRelation]:
    relations_path = entities_root / "relations.json"
    if not relations_path.exists():
        return []

    raw = json.loads(relations_path.read_text(encoding="utf-8"))
    validated_relations = validate_relations_definition(
        raw,
        source=str(relations_path),
        entities_root=entities_root,
    )
    if not validated_relations:
        return []

    entity_map = load_entity_definitions(entities_root)
    current_entity = definition["entity"]
    current_fields = {field["name"]: field for field in definition["fields"]}
    crud_relations: list[CrudManyToOneRelation] = []

    for relation in validated_relations:
        # Les relations m2m canoniques n'ont pas de from_field/from_column : on ne
        # traite ici que les many_to_one (type ValidatedRelation après ce filtre).
        if isinstance(relation, ValidatedCanonicalManyToManyRelation):
            continue
        if relation.relation_type != "many_to_one" or relation.from_entity != current_entity:
            continue

        target = entity_map[relation.to_entity]
        label_field = _first_relation_label_field(target)
        source_field = current_fields.get(relation.from_field)
        # For canonical relations, the FK column may not be declared as an entity field.
        # Fall back to relation.from_column (= foreign_key for canonical).
        field_column = source_field["column"] if source_field is not None else relation.from_column
        target_snake = _to_snake(relation.to_entity)
        field_name = relation.from_field
        crud_relations.append(
            CrudManyToOneRelation(
                field_name=field_name,
                field_column=field_column,
                target_entity=relation.to_entity,
                target_table=relation.to_table,
                target_pk_column=relation.to_column,
                target_label_column=label_field["column"],
                choices_function=f"get_{target_snake}_choices",
                choices_key=f"{field_name}_choices",
                fk_nullable=relation.fk_nullable,
                fk_sql_type=relation.from_column_sql_type,
            )
        )
    return crud_relations


def _load_crud_many_to_many_relations(
    definition: dict[str, Any],
    entities_root: Path,
) -> list[CrudManyToManyRelation]:
    relations_path = entities_root / "relations.json"
    if not relations_path.exists():
        return []

    raw = json.loads(relations_path.read_text(encoding="utf-8"))
    validated_relations = validate_relations_definition(
        raw,
        source=str(relations_path),
        entities_root=entities_root,
    )
    if not validated_relations:
        return []

    entity_map = load_entity_definitions(entities_root)
    current_entity = definition["entity"]
    current_names = {current_entity.lower(), definition["table"].lower(), _to_snake(current_entity)}
    snake = _to_snake(current_entity)
    crud_relations: list[CrudManyToManyRelation] = []

    for relation in validated_relations:
        if not isinstance(relation, ValidatedCanonicalManyToManyRelation):
            continue

        m2m_source = relation.from_entity
        m2m_target = relation.to_entity
        m2m_pivot_table = relation.pivot_table
        m2m_source_key = relation.from_key
        m2m_target_key = relation.to_key
        m2m_order_column = None

        if m2m_source.lower() not in current_names:
            continue

        incompatible = [pf.name for pf in relation.pivot_fields if not pf.nullable]
        if incompatible:
            field_list = ", ".join(incompatible)
            raise ValueError(
                f"Relation many_to_many incompatible avec make:crud : "
                f"{relation.from_entity} → {relation.to_entity} "
                f"(pivot {relation.pivot_table}).\n"
                f"Le pivot {relation.pivot_table} contient des champs obligatoires "
                f"non gérés par le CRUD simple : {field_list}.\n"
                f"make:crud synchronise uniquement les identifiants.\n"
                f"Rendez ces champs nullable ou utilisez make:pivot-crud "
                f"pour générer le sous-CRUD pivot dédié."
            )

        target = _entity_definition_by_relation_name(entity_map, m2m_target)
        if target is None:
            raise ValueError(
                f"Entité cible many_to_many introuvable pour {m2m_target!r} "
                f"dans {relations_path.as_posix()}"
            )

        target_snake = _to_snake(target["entity"])
        target_pk = _pk_field(target)
        label_field = _first_relation_label_field(target)
        field_name = f"{target_snake}_ids"
        crud_relations.append(
            CrudManyToManyRelation(
                source=m2m_source,
                target=m2m_target,
                pivot_table=m2m_pivot_table,
                source_key=m2m_source_key,
                target_key=m2m_target_key,
                target_entity=target["entity"],
                target_table=target["table"],
                target_pk_column=target_pk["column"],
                target_label_column=label_field["column"],
                field_name=field_name,
                choices_function=f"get_{target_snake}_choices",
                choices_key=f"{target_snake}_choices",
                selected_function=f"get_{snake}_{field_name}",
                add_function=f"add_{snake}_{field_name}",
                sync_function=f"sync_{snake}_{field_name}",
                list_labels_function=f"get_{snake}_{target_snake}_labels_by_{snake}_id",
                show_labels_function=f"get_{snake}_{target_snake}_labels",
                list_context_key=f"{target_snake}s_by_{snake}_id",
                selected_key=f"{field_name}_selected",
                show_context_key=f"{target_snake}_labels",
                order_column=m2m_order_column,
            )
        )
    return crud_relations


def _first_relation_label_field(definition: dict[str, Any]) -> dict[str, Any]:
    """Retourne le champ label de l'entité cible : nom préféré, puis premier texte, puis PK."""
    text_fields = _text_label_fields(definition)
    for preferred in _PREFERRED_LABEL_NAMES:
        for f in text_fields:
            if f["name"].lower() == preferred:
                return f
    if text_fields:
        return text_fields[0]
    return _pk_field(definition)


def _build_select_base(
    table: str,
    relations: list[CrudManyToOneRelation] | None,
    columns: list[str] | None = None,
) -> str:
    """Génère la clause SELECT...FROM...LEFT JOIN pour les requêtes de liste.

    Les colonnes sont **nommées et aliasées entre guillemets** quand elles sont
    fournies (`CRUD-PG-COLUMN-CASE-001`). C'est ce qui préserve leur casse.

    PostgreSQL replie tout identifiant non protégé en minuscules : une colonne
    déclarée `Nom` s'y relit `nom`. Le `SELECT *` d'avant rendait donc des clés
    minuscules là où les vues engendrées lisent `{{ contact.Nom }}`, et Jinja
    ne lève pas sur un attribut absent : le tableau s'affichait **entièrement
    vide**, lignes et boutons présents, contenu manquant, sans une ligne de
    journal. MariaDB et SQL Server conservent la casse, si bien que le défaut
    ne se voyait que sur un backend, promu au niveau plein depuis l'ADR-084.

    L'alias entre guillemets est accepté par les quatre backends, vérifié sur
    serveurs réels. Nommer les colonnes rend au passage le SQL plus lisible,
    conformément au principe 5.
    """
    projection = (
        ", ".join(f'{table}.{col} AS \\"{col}\\"' for col in columns)
        if columns
        else f"{table}.*"
    )
    if not relations:
        return f"SELECT {projection} FROM {table}"
    join_cols = ", ".join(
        f"{rel.target_table}.{rel.target_label_column} AS {rel.field_name}_label"
        for rel in relations
    )
    joins = " ".join(
        f"LEFT JOIN {rel.target_table}"
        f" ON {table}.{rel.field_column} = {rel.target_table}.{rel.target_pk_column}"
        for rel in relations
    )
    return f"SELECT {projection}, {join_cols} FROM {table} {joins}"


def _unique_choice_relations(
    relations: list[CrudManyToOneRelation] | None,
) -> list[CrudManyToOneRelation]:
    unique: dict[str, CrudManyToOneRelation] = {}
    for relation in relations or []:
        unique.setdefault(relation.choices_function, relation)
    return list(unique.values())


def _unique_many_to_many_choice_relations(
    relations: list[CrudManyToManyRelation] | None,
) -> list[CrudManyToManyRelation]:
    unique: dict[str, CrudManyToManyRelation] = {}
    for relation in relations or []:
        unique.setdefault(relation.choices_function, relation)
    return list(unique.values())
