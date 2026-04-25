"""Orchestration du modele d'entites Forge."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forge_cli.entities.make_entity import (
    build_entity_base,
    build_entity_init,
    build_entity_manual,
    build_entity_sql,
    to_snake,
    validate_entity_name,
)
import forge_cli.output as out
from forge_cli.entities.relations import (
    EntityRelationsError,
    ValidatedRelation,
    generate_relations_sql,
    validate_relations_definition,
)
from forge_cli.entities.validation import EntityDefinitionError, validate_entity_definition


@dataclass
class EntitySource:
    entity_dir: Path
    json_path: Path
    definition: dict[str, Any]


@dataclass
class BuildModelResult:
    written: list[Path]
    created: list[Path]
    preserved: list[Path]
    dry_run: bool = False


class ModelValidationError(ValueError):
    """Erreur globale de validation du modele."""

    def __init__(self, blocks: list[str]):
        self.blocks = blocks
        lines = [f"Modele invalide ({len(blocks)} bloc(s) d'erreurs)"]
        for block in blocks:
            lines.append("")
            lines.append(block)
        super().__init__("\n".join(lines))


def sync_relations(entities_root: Path) -> Path:
    relations_path = entities_root / "relations.json"
    relations_data = _read_json_file(relations_path)
    validated_relations = validate_relations_definition(
        relations_data,
        source=str(relations_path),
        entities_root=entities_root,
    )
    output_path = entities_root / "relations.sql"
    output_path.write_text(generate_relations_sql(validated_relations), encoding="utf-8")
    return output_path


def sync_entity(entities_root: Path, entity_name: str) -> tuple[Path, Path]:
    validated_name = validate_entity_name(entity_name)
    snake = to_snake(validated_name)
    entity_dir = entities_root / snake

    if not entity_dir.exists() or not entity_dir.is_dir():
        raise ValueError(f"Entite introuvable : {validated_name} ({entity_dir.as_posix()})")

    json_path = entity_dir / f"{snake}.json"
    if not json_path.exists():
        raise ValueError(f"JSON d'entite introuvable : {json_path.as_posix()}")

    definition = validate_entity_definition(_read_json_file(json_path), source=str(json_path))

    sql_path = entity_dir / f"{snake}.sql"
    base_path = entity_dir / f"{snake}_base.py"

    sql_path.write_text(build_entity_sql(definition), encoding="utf-8")
    base_path.write_text(build_entity_base(definition), encoding="utf-8")
    return sql_path, base_path


def build_model(entities_root: Path, *, dry_run: bool = False) -> BuildModelResult:
    entity_sources, validated_relations = _validate_model_or_raise(entities_root)

    written: list[Path] = []
    created: list[Path] = []
    preserved: list[Path] = []

    for source in entity_sources:
        snake = source.entity_dir.name
        sql_path = source.entity_dir / f"{snake}.sql"
        base_path = source.entity_dir / f"{snake}_base.py"

        if not dry_run:
            sql_path.write_text(build_entity_sql(source.definition), encoding="utf-8")
            base_path.write_text(build_entity_base(source.definition), encoding="utf-8")
        written.extend([sql_path, base_path])

        manual_path = source.entity_dir / f"{snake}.py"
        if manual_path.exists():
            preserved.append(manual_path)
        else:
            if not dry_run:
                manual_path.write_text(
                    build_entity_manual(source.definition["entity"], snake),
                    encoding="utf-8",
                )
            created.append(manual_path)

        init_path = source.entity_dir / "__init__.py"
        if init_path.exists():
            preserved.append(init_path)
        else:
            if not dry_run:
                init_path.write_text(
                    build_entity_init(source.definition["entity"]),
                    encoding="utf-8",
                )
            created.append(init_path)

    relations_path = entities_root / "relations.sql"
    if not dry_run:
        relations_path.write_text(generate_relations_sql(validated_relations), encoding="utf-8")
    written.append(relations_path)

    return BuildModelResult(written=written, created=created, preserved=preserved, dry_run=dry_run)


def check_model(entities_root: Path) -> tuple[list[EntitySource], list[ValidatedRelation]]:
    return _validate_model_or_raise(entities_root)


def main(argv: list[str] | None = None) -> None:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage : forge sync:entity NomEntite | forge sync:relations | forge build:model | forge check:model")
        raise SystemExit(1)

    command = args[0]
    entities_root = Path("mvc") / "entities"

    try:
        if command == "sync:entity":
            if len(args) != 2:
                print("Usage : forge sync:entity NomEntite")
                raise SystemExit(1)
            sql_path, base_path = sync_entity(entities_root, args[1])
            manual_path = sql_path.parent / f"{sql_path.stem}.py"
            print(out.written(sql_path.as_posix()))
            print(out.written(base_path.as_posix()))
            print(out.preserved(manual_path.as_posix(), "← fichier manuel, non touché"))
            return

        if command == "sync:relations":
            if len(args) != 1:
                print("Usage : forge sync:relations")
                raise SystemExit(1)
            output = sync_relations(entities_root)
            print(out.ok(f"{output.as_posix()} regenere."))
            return

        if command == "build:model":
            extra = [a for a in args[1:] if a != "--dry-run"]
            if extra:
                print("Usage : forge build:model [--dry-run]")
                raise SystemExit(1)
            dry_run = "--dry-run" in args
            result = build_model(entities_root, dry_run=dry_run)
            for path in result.written:
                print(out.written(path.as_posix()))
            for path in result.created:
                print(out.created(path.as_posix()))
            for path in result.preserved:
                print(out.preserved(path.as_posix()))
            print(
                f"\n{len(result.written)} régénéré(s), "
                f"{len(result.created)} créé(s), "
                f"{len(result.preserved)} préservé(s)."
            )
            if dry_run:
                print(out.dry_run("Aucun fichier modifié."))
            return

        if command != "check:model" or len(args) != 1:
            print("Usage : forge sync:entity NomEntite | forge sync:relations | forge build:model | forge check:model")
            raise SystemExit(1)

        check_model(entities_root)
        print(out.ok("Modele valide."))
    except (ModelValidationError, EntityRelationsError, EntityDefinitionError, ValueError) as exc:
        print(out.error(str(exc)))
        raise SystemExit(1)


def _validate_model_or_raise(entities_root: Path) -> tuple[list[EntitySource], list[ValidatedRelation]]:
    blocks: list[str] = []
    entity_sources = _load_all_entity_sources(entities_root, blocks)
    if not blocks:
        _validate_global_entity_consistency(entity_sources, blocks)

    relations_path = entities_root / "relations.json"
    validated_relations: list[ValidatedRelation] = []
    if not relations_path.exists():
        blocks.append(f"{relations_path}: fichier introuvable")
    else:
        try:
            relations_data = _read_json_file(relations_path)
        except ValueError as exc:
            blocks.append(str(exc))
        else:
            if blocks:
                blocks.append(
                    f"{relations_path}: validation des relations impossible tant que certaines entites sont invalides"
                )
            else:
                try:
                    validated_relations = validate_relations_definition(
                        relations_data,
                        source=str(relations_path),
                        entities_root=entities_root,
                    )
                except EntityRelationsError as exc:
                    blocks.append(str(exc))

    if blocks:
        raise ModelValidationError(blocks)
    return entity_sources, validated_relations


def _load_all_entity_sources(entities_root: Path, blocks: list[str]) -> list[EntitySource]:
    sources: list[EntitySource] = []
    for entity_dir in sorted(
        (
            path
            for path in entities_root.iterdir()
            if path.is_dir() and not path.name.startswith("__")
        ),
        key=lambda path: path.name,
    ):
        json_path = entity_dir / f"{entity_dir.name}.json"
        if not json_path.exists():
            blocks.append(f"{json_path}: fichier JSON d'entite introuvable")
            continue
        try:
            definition = validate_entity_definition(_read_json_file(json_path), source=str(json_path))
        except (ValueError, EntityDefinitionError) as exc:
            blocks.append(str(exc))
            continue
        sources.append(EntitySource(entity_dir=entity_dir, json_path=json_path, definition=definition))
    return sources


def _validate_global_entity_consistency(sources: list[EntitySource], blocks: list[str]) -> None:
    entity_names: dict[str, EntitySource] = {}
    table_names: dict[str, EntitySource] = {}

    for source in sources:
        entity = source.definition["entity"]
        table = source.definition["table"]
        folder = source.entity_dir.name

        previous_entity = entity_names.get(entity)
        if previous_entity is not None:
            blocks.append(
                f"{source.json_path}: entity {entity!r} deja declaree dans {previous_entity.json_path}"
            )
        else:
            entity_names[entity] = source

        previous_table = table_names.get(table)
        if previous_table is not None:
            blocks.append(
                f"{source.json_path}: table {table!r} deja declaree dans {previous_table.json_path}"
            )
        else:
            table_names[table] = source

        expected_folder = to_snake(entity)
        if folder != expected_folder:
            blocks.append(
                f"{source.json_path}: le dossier d'entite {folder!r} doit correspondre a l'entite {entity!r} ({expected_folder!r})"
            )


def _read_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"{path}: fichier introuvable")
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: JSON invalide ({exc.msg} a la ligne {exc.lineno}, colonne {exc.colno})")
