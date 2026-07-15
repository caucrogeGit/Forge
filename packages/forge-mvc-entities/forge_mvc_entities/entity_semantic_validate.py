# pyright: strict
"""Validation sémantique Forge des entités et relations JSON canoniques.

Cette couche s'exécute après la validation JSON Schema (structurelle) et
vérifie la cohérence que JSON Schema ne peut pas garantir seul :

- doublons de champs dans une entité ;
- noms de champs réservés Python ;
- doublons de table entre entités ;
- index pointant vers un champ inexistant ;
- relations many_to_one vers des entités inconnues ;
- collision entre clé étrangère déduite et champ métier existant ;
- incohérence set_null / nullable ;
- relations many_to_many vers des entités inconnues ;
- collision de table pivot avec une table d'entité ;
- pivot.from_key == pivot.to_key ;
- pivot.fields redéclarant des noms réservés (id, from_key, to_key) ;
- relation many_to_many déclarée deux fois en sens inverse.

Cette couche ne vérifie pas encore :
- la cohérence SQL complète des types ;
- l'unicité des noms de contraintes SQL ;
- les cycles de dépendances entre entités.
"""

from __future__ import annotations
from typing import Any, cast

import keyword
from dataclasses import dataclass
from datetime import date, datetime

from forge_mvc_entities.entity_validation_errors import (
    FORGE_ENTITY_DUPLICATE_FIELD,
    FORGE_ENTITY_DUPLICATE_TABLE,
    FORGE_ENTITY_INVALID_DEFAULT,
    FORGE_ENTITY_INVALID_INDEX,
    FORGE_ENTITY_INVALID_SLUG_SOURCE,
    FORGE_ENTITY_RESERVED_PYTHON_NAME,
    FORGE_ENTITY_RESERVED_SQL_NAME,
    FORGE_PIVOT_KEY_COLLISION,
    FORGE_PIVOT_RESERVED_FIELD,
    FORGE_PIVOT_TABLE_COLLISION,
    FORGE_RELATION_DUPLICATE,
    FORGE_RELATION_FK_COLLISION,
    FORGE_RELATION_INVALID_ON_DELETE,
    FORGE_RELATION_UNKNOWN_ENTITY,
)
from forge_mvc_entities.field_resolver import SIMPLE_PYTHON_TYPE, nullable_of

# Mots réservés SQL refusés comme nom de table ou d'entité (relocalisé de
# validation.py, ADR-086). La colonne d'un champ métier est dérivée en
# PascalCase donc jamais réservée ; seul le nom snake_case d'une clé étrangère
# pourrait l'être, cas couvert par le contrôle sur les champs.
SQL_RESERVED_WORDS = {
    "add", "alter", "and", "by", "create", "delete", "drop", "from", "group",
    "index", "insert", "into", "join", "key", "order", "primary", "references",
    "select", "table", "update", "user", "where",
}


def _canonical_python_type(forge_type: str) -> str | None:
    """Type Python d'un type Forge canonique, sans dépendance au dialecte."""
    if forge_type == "string":
        return "str"
    if forge_type == "decimal":
        return "float"
    if forge_type == "foreign_key":
        return "int"
    return SIMPLE_PYTHON_TYPE.get(forge_type)


def _is_iso_date_string(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _is_iso_datetime_string(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _default_matches_type(python_type: str, value: Any) -> bool:
    if python_type == "str":
        return isinstance(value, str)
    if python_type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if python_type == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if python_type == "bool":
        return isinstance(value, bool)
    if python_type == "date":
        return _is_iso_date_string(value)
    if python_type == "datetime":
        return _is_iso_datetime_string(value)
    return True


@dataclass(frozen=True)
class SemanticError:
    code: str
    file: str
    path: str
    message: str
    hint: str = ""


def _check_field_default(
    errors: list[SemanticError], source: str, index: int, field: dict[str, Any]
) -> None:
    """Vérifie qu'une valeur `default` est compatible avec le type du champ."""
    value = field["default"]
    fname = field.get("name", "?")
    path = f"$.fields[{index}].default"

    if value is None:
        if not nullable_of(field):
            errors.append(SemanticError(
                code=FORGE_ENTITY_INVALID_DEFAULT,
                file=source,
                path=path,
                message=f"la valeur par défaut null du champ \"{fname}\" n'est autorisée que si le champ est nullable.",
                hint="Rendez le champ nullable ou remplacez la valeur par défaut.",
            ))
        return

    python_type = _canonical_python_type(str(field.get("type", "")))
    if python_type is None:
        return  # type Forge inconnu : déjà signalé par le JSON Schema en amont.
    if not _default_matches_type(python_type, value):
        errors.append(SemanticError(
            code=FORGE_ENTITY_INVALID_DEFAULT,
            file=source,
            path=path,
            message=f"la valeur par défaut du champ \"{fname}\" est incompatible avec le type \"{field.get('type')}\".",
            hint="Alignez la valeur par défaut sur le type du champ.",
        ))


def validate_semantic(
    valid_entities: list[tuple[str, dict[str, Any]]],
    valid_relations: dict[str, Any] | None,
) -> list[SemanticError]:
    """Valide la cohérence sémantique des entités et relations structurellement valides.

    Args:
        valid_entities: liste de (label_source, entity_data) — seuls les fichiers
                        ayant passé JSON Schema doivent être passés ici.
        valid_relations: contenu de relations.json si structurellement valide, sinon None.

    Returns:
        Liste d'erreurs sémantiques. Vide si tout est cohérent.
    """
    errors: list[SemanticError] = []

    entity_by_name: dict[str, dict[str, Any]] = {}
    table_to_entity: dict[str, str] = {}  # table_name → entity_name

    # ── Contrôles par entité ──────────────────────────────────────────────────

    for source, entity in valid_entities:
        name = entity.get("name", "?")
        table = entity.get("table", "")
        fields = entity.get("fields", [])

        field_names = [cast("dict[str, Any]", f).get("name", "") for f in fields if isinstance(f, dict)]

        # 1. Doublons de champs
        seen: set[str] = set()
        for i, fname in enumerate(field_names):
            if fname in seen:
                errors.append(SemanticError(
                    code=FORGE_ENTITY_DUPLICATE_FIELD,
                    file=source,
                    path=f"$.fields[{i}].name",
                    message=f"le champ \"{fname}\" est déclaré deux fois dans l'entité {name}.",
                    hint="Supprimez ou renommez le champ en doublon.",
                ))
            seen.add(fname)

        # 2. Noms réservés Python
        reserved = set(keyword.kwlist)
        for i, fname in enumerate(field_names):
            if fname in reserved:
                errors.append(SemanticError(
                    code=FORGE_ENTITY_RESERVED_PYTHON_NAME,
                    file=source,
                    path=f"$.fields[{i}].name",
                    message=f"le champ \"{fname}\" est un mot réservé Python.",
                    hint="Choisissez un nom différent pour éviter les conflits de génération de code.",
                ))

        # 3. Doublons de table
        if table:
            if table in table_to_entity:
                other = table_to_entity[table]
                errors.append(SemanticError(
                    code=FORGE_ENTITY_DUPLICATE_TABLE,
                    file=source,
                    path="$.table",
                    message=f"la table \"{table}\" est déjà utilisée par l'entité {other}.",
                    hint="Chaque entité doit avoir une table SQL unique.",
                ))
            else:
                table_to_entity[table] = name

        # 4. Index pointant vers des champs inexistants
        field_name_set = set(field_names)
        for idx_i, index in enumerate(entity.get("indexes", [])):
            if not isinstance(index, dict):
                continue
            index = cast("dict[str, Any]", index)
            for col_i, col in enumerate(index.get("fields", [])):
                if col not in field_name_set:
                    errors.append(SemanticError(
                        code=FORGE_ENTITY_INVALID_INDEX,
                        file=source,
                        path=f"$.indexes[{idx_i}].fields[{col_i}]",
                        message=(
                            f"le champ \"{col}\" est utilisé par l'index "
                            f"\"{index.get('name', '?')}\" mais n'existe pas dans l'entité {name}."
                        ),
                        hint="Ajoutez le champ ou retirez-le de l'index.",
                    ))

        # 5. Nom de table ou d'entité = mot réservé SQL (relocalisé, ADR-086)
        if table and table.lower() in SQL_RESERVED_WORDS:
            errors.append(SemanticError(
                code=FORGE_ENTITY_RESERVED_SQL_NAME,
                file=source,
                path="$.table",
                message=f"la table \"{table}\" est un mot réservé SQL.",
                hint="Choisissez un nom de table qui n'est pas un mot réservé SQL.",
            ))
        if name and name.lower() in SQL_RESERVED_WORDS:
            errors.append(SemanticError(
                code=FORGE_ENTITY_RESERVED_SQL_NAME,
                file=source,
                path="$.name",
                message=f"le nom d'entité \"{name}\" est un mot réservé SQL.",
                hint="Choisissez un nom d'entité qui n'est pas un mot réservé SQL.",
            ))

        # 6. Slug auto-généré : `source` référence un champ existant, jamais soi-même
        for i, f in enumerate(fields):
            if not isinstance(f, dict):
                continue
            fdict = cast("dict[str, Any]", f)
            if fdict.get("type") != "slug" or "source" not in fdict:
                continue
            src = fdict.get("source")
            own = fdict.get("name", "")
            if src == own:
                errors.append(SemanticError(
                    code=FORGE_ENTITY_INVALID_SLUG_SOURCE,
                    file=source,
                    path=f"$.fields[{i}].source",
                    message=f"le slug \"{own}\" ne peut pas se référencer lui-même comme source.",
                    hint="Indiquez un autre champ comme source du slug.",
                ))
            elif src not in field_name_set:
                errors.append(SemanticError(
                    code=FORGE_ENTITY_INVALID_SLUG_SOURCE,
                    file=source,
                    path=f"$.fields[{i}].source",
                    message=f"la source \"{src}\" du slug \"{own}\" ne correspond à aucun champ de l'entité {name}.",
                    hint="Vérifiez le nom du champ source.",
                ))

        # 7. Valeur par défaut cohérente avec le type du champ
        for i, f in enumerate(fields):
            if not isinstance(f, dict):
                continue
            fdict = cast("dict[str, Any]", f)
            if "default" in fdict:
                _check_field_default(errors, source, i, fdict)

        entity_by_name[name] = entity

    # ── Contrôles sur les relations ───────────────────────────────────────────

    if not valid_relations:
        return errors

    known_names = set(entity_by_name.keys())
    m2m_pairs: set[frozenset[str]] = set()

    for rel_i, relation in enumerate(valid_relations.get("relations", [])):
        if not isinstance(relation, dict):
            continue
        relation = cast("dict[str, Any]", relation)

        rel_type = relation.get("type", "")
        rel_from = relation.get("from", "")
        rel_to = relation.get("to", "")
        rel_name = relation.get("name", "?")
        rel_path = f"$.relations[{rel_i}]"

        if rel_type == "many_to_one":
            _check_many_to_one(
                errors, relation, rel_i, rel_path,
                rel_from, rel_to, rel_name, known_names, entity_by_name,
            )

        elif rel_type == "many_to_many":
            _check_many_to_many(
                errors, relation, rel_i, rel_path,
                rel_from, rel_to, known_names, table_to_entity, m2m_pairs,
            )

    return errors


def _check_many_to_one(
    errors: list[SemanticError],
    relation: dict[str, Any],
    rel_i: int,
    rel_path: str,
    rel_from: str,
    rel_to: str,
    rel_name: str,
    known_names: set[str],
    entity_by_name: dict[str, dict[str, Any]],
) -> None:
    source = "relations.json"

    # 5. from → entité inconnue
    if rel_from and rel_from not in known_names:
        errors.append(SemanticError(
            code=FORGE_RELATION_UNKNOWN_ENTITY,
            file=source,
            path=f"{rel_path}.from",
            message=f"l'entité source \"{rel_from}\" n'est pas déclarée dans les entités validées.",
            hint="Vérifiez le nom de l'entité ou créez le fichier d'entité manquant.",
        ))

    # 6. to → entité inconnue
    if rel_to and rel_to not in known_names:
        errors.append(SemanticError(
            code=FORGE_RELATION_UNKNOWN_ENTITY,
            file=source,
            path=f"{rel_path}.to",
            message=f"l'entité cible \"{rel_to}\" n'est pas déclarée dans les entités validées.",
            hint="Vérifiez le nom de l'entité ou créez le fichier d'entité manquant.",
        ))

    # 7. Collision clé étrangère / champ métier
    if rel_from in entity_by_name:
        from_entity = entity_by_name[rel_from]
        # ADR-069 : un champ de type `foreign_key` est une clé étrangère DÉCLARÉE
        # (make:relation l'injecte comme champ de première classe), pas une
        # collision avec un champ métier. On ne signale une collision que si le
        # champ existant du même nom est d'un AUTRE type.
        field_types = {
            cast("dict[str, Any]", f).get("name", ""): cast("dict[str, Any]", f).get("type", "")
            for f in from_entity.get("fields", [])
            if isinstance(f, dict)
        }
        fk = relation.get("foreign_key") or f"{rel_name}_id"
        if fk in field_types and field_types[fk] != "foreign_key":
            errors.append(SemanticError(
                code=FORGE_RELATION_FK_COLLISION,
                file=source,
                path=f"{rel_path}.foreign_key",
                message=(
                    f"la clé étrangère \"{fk}\" (relation {rel_name}) collisionne avec "
                    f"un champ métier déclaré dans l'entité {rel_from}."
                ),
                hint="Déclarez explicitement foreign_key avec un nom différent.",
            ))

    # 8. set_null incompatible avec nullable=false
    on_delete = relation.get("on_delete", "")
    nullable = relation.get("nullable", True)
    if on_delete == "set_null" and nullable is False:
        errors.append(SemanticError(
            code=FORGE_RELATION_INVALID_ON_DELETE,
            file=source,
            path=f"{rel_path}.on_delete",
            message=(
                f"on_delete=\"set_null\" est incompatible avec nullable=false "
                f"pour la relation {rel_name} (impossible de mettre NULL dans une colonne NOT NULL)."
            ),
            hint="Passez nullable=true ou choisissez une autre politique on_delete.",
        ))


def _check_many_to_many(
    errors: list[SemanticError],
    relation: dict[str, Any],
    rel_i: int,
    rel_path: str,
    rel_from: str,
    rel_to: str,
    known_names: set[str],
    table_to_entity: dict[str, str],
    m2m_pairs: set[frozenset[str]],
) -> None:
    source = "relations.json"
    pivot: dict[str, Any] = cast("dict[str, Any]", relation.get("pivot")) if isinstance(relation.get("pivot"), dict) else {}

    # 9. from → entité inconnue
    if rel_from and rel_from not in known_names:
        errors.append(SemanticError(
            code=FORGE_RELATION_UNKNOWN_ENTITY,
            file=source,
            path=f"{rel_path}.from",
            message=f"l'entité source \"{rel_from}\" n'est pas déclarée dans les entités validées.",
            hint="Vérifiez le nom de l'entité ou créez le fichier d'entité manquant.",
        ))

    # 10. to → entité inconnue
    if rel_to and rel_to not in known_names:
        errors.append(SemanticError(
            code=FORGE_RELATION_UNKNOWN_ENTITY,
            file=source,
            path=f"{rel_path}.to",
            message=f"l'entité cible \"{rel_to}\" n'est pas déclarée dans les entités validées.",
            hint="Vérifiez le nom de l'entité ou créez le fichier d'entité manquant.",
        ))

    # 11. self-relation
    if rel_from and rel_to and rel_from == rel_to:
        errors.append(SemanticError(
            code=FORGE_RELATION_UNKNOWN_ENTITY,
            file=source,
            path=f"{rel_path}.from",
            message=f"une relation many_to_many ne peut pas lier une entité à elle-même ({rel_from}).",
            hint="Les auto-relations many_to_many ne sont pas supportées en Forge 1.x.",
        ))

    # 12. pivot.table collisionne avec table d'entité
    pivot_table = pivot.get("table", "")
    if pivot_table and pivot_table in table_to_entity:
        owner = table_to_entity[pivot_table]
        errors.append(SemanticError(
            code=FORGE_PIVOT_TABLE_COLLISION,
            file=source,
            path=f"{rel_path}.pivot.table",
            message=(
                f"la table pivot \"{pivot_table}\" est déjà utilisée par l'entité {owner}."
            ),
            hint="Choisissez un nom de table pivot différent des tables d'entité.",
        ))

    # 13. pivot.from_key == pivot.to_key
    from_key = pivot.get("from_key", "")
    to_key = pivot.get("to_key", "")
    if from_key and to_key and from_key == to_key:
        errors.append(SemanticError(
            code=FORGE_PIVOT_KEY_COLLISION,
            file=source,
            path=f"{rel_path}.pivot.from_key",
            message=f"pivot.from_key et pivot.to_key sont identiques (\"{from_key}\").",
            hint="Les deux clés étrangères de la table pivot doivent avoir des noms différents.",
        ))

    # 14. pivot.fields redéclarant des noms réservés
    reserved_pivot: set[str] = {"id"} | ({from_key} if from_key else set[str]()) | ({to_key} if to_key else set[str]())
    for fi, pf in enumerate(pivot.get("fields", [])):
        if not isinstance(pf, dict):
            continue
        pf = cast("dict[str, Any]", pf)
        pf_name = pf.get("name", "")
        if pf_name in reserved_pivot:
            errors.append(SemanticError(
                code=FORGE_PIVOT_RESERVED_FIELD,
                file=source,
                path=f"{rel_path}.pivot.fields[{fi}].name",
                message=f"le champ pivot \"{pf_name}\" est réservé par Forge (id, from_key ou to_key).",
                hint="Retirez ce champ de pivot.fields — il est géré automatiquement.",
            ))

    # 15. many_to_many déclaré deux fois en sens inverse
    pair = frozenset({rel_from, rel_to})
    if pair in m2m_pairs and rel_from and rel_to:
        errors.append(SemanticError(
            code=FORGE_RELATION_DUPLICATE,
            file=source,
            path=f"{rel_path}.from",
            message=(
                f"la relation many_to_many entre \"{rel_from}\" et \"{rel_to}\" est "
                f"déclarée deux fois (dans les deux sens)."
            ),
            hint="Déclarez la relation une seule fois dans un sens unique.",
        ))
    else:
        m2m_pairs.add(pair)
