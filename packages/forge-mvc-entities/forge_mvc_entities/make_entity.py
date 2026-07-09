#!/usr/bin/env python3
# pyright: strict
# pyright: reportUnusedFunction=false
"""
Genere l'arborescence d'une entite Forge.

Usage :
    forge make:entity
    forge make:entity Contact
    forge make:entity Contact --no-input
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

import cli._support.output as out
from forge_mvc_entities.validation import (
    EntityDefinitionError,
    normalize_entity_definition,
    validate_entity_definition,
)

FORGE_TYPES = (
    "string",
    "text",
    "integer",
    "big_integer",
    "float",
    "decimal",
    "boolean",
    "date",
    "datetime",
    "email",
    "password",
    "json",
)


def project_root() -> Path:
    return Path.cwd()


def entities_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "mvc" / "entities"


def to_snake(name: str) -> str:
    name = name.replace("-", "_")
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
    return name.lower()


def validate_entity_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name):
        raise ValueError(
            "Le nom d'entite doit etre un identifiant PascalCase valide "
            "(lettres et chiffres uniquement, sans espace ni underscore)."
        )
    return name[0].upper() + name[1:]


def build_entity_json_canonical(entity_name: str, table: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "name": entity_name,
        "table": table or to_snake(entity_name),
        "fields": [
            {"name": "title", "type": "string", "max_length": 255, "required": True},
        ],
        "options": {"timestamps": False, "soft_delete": False},
    }


def _prompt_text(
    label: str,
    *,
    default: str | None = None,
    allow_empty: bool = False,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    if input_fn is None:
        input_fn = input
    prompt = f"{label}"
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


def _prompt_optional_int(
    label: str,
    *,
    input_fn: Callable[[str], str] | None = None,
) -> int | None:
    if input_fn is None:
        input_fn = input
    while True:
        value = input_fn(f"{label} [vide = aucun] : ").strip()
        if not value:
            return None
        if value.isdigit():
            return int(value)
        print("Valeur attendue : entier positif ou vide.")


def _prompt_required_int(
    label: str,
    *,
    input_fn: Callable[[str], str] | None = None,
) -> int:
    if input_fn is None:
        input_fn = input
    while True:
        value = input_fn(f"{label} : ").strip()
        if value.isdigit():
            return int(value)
        print("Valeur attendue : entier positif.")


def _prompt_optional_number(
    label: str,
    *,
    input_fn: Callable[[str], str] | None = None,
) -> int | float | None:
    if input_fn is None:
        input_fn = input
    while True:
        value = input_fn(f"{label} [vide = aucun] : ").strip()
        if not value:
            return None
        try:
            number = float(value) if "." in value else int(value)
        except ValueError:
            print("Valeur attendue : nombre ou vide.")
            continue
        return number


def _prompt_forge_type(
    label: str,
    *,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    help_label = (
        f"{label} "
        "[string, text, integer, big_integer, float, decimal, "
        "boolean, date, datetime, email, password, json]"
    )
    while True:
        raw_value = _prompt_text(help_label, input_fn=input_fn)
        normalized = raw_value.strip().lower()
        if normalized in FORGE_TYPES:
            return normalized
        print(
            "Type invalide. Valeurs attendues : "
            "string, text, integer, big_integer, float, decimal, "
            "boolean, date, datetime, email, password, json."
        )


def _build_canonical_field(*, input_fn: Callable[[str], str] | None = None) -> dict[str, Any]:
    field_name = _prompt_text("Nom du champ", input_fn=input_fn)
    forge_type = _prompt_forge_type("Type Forge", input_fn=input_fn)

    field: dict[str, object] = {"name": field_name, "type": forge_type}

    if forge_type == "string":
        max_length = _prompt_optional_int("max_length", input_fn=input_fn)
        if max_length is not None:
            field["max_length"] = max_length
    elif forge_type == "decimal":
        field["precision"] = _prompt_required_int("Précision", input_fn=input_fn)
        field["scale"] = _prompt_required_int("Échelle", input_fn=input_fn)

    field["required"] = _prompt_yes_no("Champ requis ?", default=True, input_fn=input_fn)
    field["nullable"] = _prompt_yes_no("Autoriser NULL ?", default=False, input_fn=input_fn)
    field["unique"] = _prompt_yes_no("Champ unique ?", default=False, input_fn=input_fn)

    return field


def build_entity_json_interactively(
    entity_name: str | None = None,
    *,
    input_fn: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    if input_fn is None:
        input_fn = input
    if entity_name is None:
        while True:
            try:
                entity_name = validate_entity_name(_prompt_text("Nom de l'entité", input_fn=input_fn))
                break
            except ValueError as exc:
                print(exc)

    default_table = to_snake(entity_name)
    table_name = _prompt_text(
        "Nom de la table (Entrée = convention par défaut)",
        allow_empty=True,
        input_fn=input_fn,
    ) or default_table

    fields = [_build_canonical_field(input_fn=input_fn)]
    while _prompt_yes_no("Ajouter un autre champ ?", default=False, input_fn=input_fn):
        fields.append(_build_canonical_field(input_fn=input_fn))

    timestamps = _prompt_yes_no(
        "Activer timestamps (created_at / updated_at) ?", default=False, input_fn=input_fn
    )
    soft_delete = _prompt_yes_no(
        "Activer soft_delete (deleted_at) ?", default=False, input_fn=input_fn
    )

    return {
        "schema_version": "1.0",
        "name": entity_name,
        "table": table_name,
        "fields": fields,
        "options": {"timestamps": timestamps, "soft_delete": soft_delete},
    }


def _render_entity_summary(entity_definition: dict[str, Any]) -> str:
    lines = [
        f"Entité : {entity_definition['name']}",
        f"Table : {entity_definition['table']}",
        "Champs :",
    ]
    for field in entity_definition["fields"]:
        parts = [field["name"], field["type"]]
        if field.get("required"):
            parts.append("required")
        if field.get("nullable"):
            parts.append("NULL")
        if field.get("unique"):
            parts.append("UNIQUE")
        if field.get("max_length") is not None:
            parts.append(f"max_length={field['max_length']}")
        if field.get("precision") is not None:
            parts.append(f"precision={field['precision']},scale={field.get('scale')}")
        lines.append(f"- {' | '.join(str(part) for part in parts)}")
    opts = entity_definition.get("options", {})
    if opts.get("timestamps"):
        lines.append("Options : timestamps")
    if opts.get("soft_delete"):
        lines.append("Options : soft_delete")
    return "\n".join(lines)


def _parse_args(args: list[str]) -> tuple[str | None, bool]:
    entity_name: str | None = None
    interactive = True

    for arg in args:
        if arg in {"-h", "--help"}:
            print((__doc__ or "").strip())
            raise SystemExit(0)
        if arg == "--no-input":
            interactive = False
            continue
        if arg == "--interactive":
            interactive = True
            continue
        if entity_name is None:
            entity_name = arg.strip()
            continue
        print((__doc__ or "").strip())
        raise SystemExit(1)

    return entity_name, interactive


def _write_entity_files(
    entity_definition: dict[str, Any],
    normalized_definition: dict[str, Any],
    *,
    root: Path | None = None,
) -> tuple[str, str, list[Path], list[Path]]:
    entity_name = entity_definition.get("name") or entity_definition.get("entity", "")
    snake = to_snake(entity_name)
    root = root or project_root()
    target_entities_dir = entities_dir(root)
    entity_dir = target_entities_dir / snake

    created: list[Path] = []
    skipped: list[Path] = []

    ensure_file(target_entities_dir / "__init__.py", "", created, skipped)
    ensure_file(
        target_entities_dir / "relations.json",
        json.dumps({"schema_version": "1.0", "relations": []}, indent=2, ensure_ascii=True) + "\n",
        created,
        skipped,
    )
    ensure_file(target_entities_dir / "relations.sql", "", created, skipped)
    ensure_file(
        entity_dir / f"{snake}.json",
        json.dumps(entity_definition, indent=2, ensure_ascii=True) + "\n",
        created,
        skipped,
    )
    ensure_file(entity_dir / f"{snake}.sql", build_entity_sql(normalized_definition), created, skipped)
    ensure_file(entity_dir / f"{snake}_base.py", build_entity_base(normalized_definition), created, skipped)
    ensure_file(entity_dir / f"{snake}.py", build_entity_manual(entity_name, snake), created, skipped)
    ensure_file(entity_dir / "__init__.py", build_entity_init(entity_name), created, skipped)
    return entity_name, snake, created, skipped


def sql_default_literal(field: dict[str, Any]) -> str | None:
    if "default" not in field:
        return None
    value = field["default"]
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return str(value)


def build_entity_sql(entity_definition: dict[str, Any]) -> str:
    from core.database.backend import get_backend

    dialect = get_backend().dialect
    entity_definition = normalize_entity_definition(entity_definition)
    table = entity_definition["table"]
    fields = entity_definition["fields"]

    lines = [f"{dialect.create_table_opening(table)} ("]
    body_lines: list[str] = []
    primary_key_column = None

    for field in fields:
        if field["auto_increment"]:
            # PK auto-incrémentée : la forme exacte dépend du dialecte
            # (MariaDB ajoute une clause PRIMARY KEY séparée ; SQLite la porte
            # sur la colonne).
            body_lines.append(
                "    " + dialect.auto_increment_column_ddl(field["column"], field["sql_type"])
            )
        else:
            parts = [f"    {field['column']} {field['sql_type']}"]
            parts.append("NULL" if field["nullable"] else "NOT NULL")
            if field.get("unique") is True and dialect.unique_is_column_constraint():
                parts.append("UNIQUE")
            default_literal = sql_default_literal(field)
            if default_literal is not None:
                parts.append(f"DEFAULT {default_literal}")
            body_lines.append(" ".join(parts))

        if field["primary_key"]:
            primary_key_column = field["column"]
        if field.get("unique") is True and not dialect.unique_is_column_constraint():
            body_lines.append(
                "    " + dialect.unique_constraint_ddl(table, field["name"], field["column"])
            )

    if primary_key_column is not None and dialect.emits_separate_primary_key():
        body_lines.append(f"    PRIMARY KEY ({primary_key_column})")

    lines.append(",\n".join(body_lines))
    lines.append(")" + dialect.table_suffix() + ";")
    return "\n".join(lines) + "\n"


def _python_default_literal(field: dict[str, Any]) -> str | None:
    if "default" in field:
        python_type = field["python_type"]
        if python_type == "date":
            return f"date.fromisoformat({field['default']!r})"
        if python_type == "datetime":
            return f"datetime.fromisoformat({field['default']!r})"
        return repr(field["default"])
    if field["nullable"] or field["auto_increment"]:
        return "None"
    return None


def _is_required_in_init(field: dict[str, Any]) -> bool:
    return (
        not field["nullable"]
        and "default" not in field
        and not field["auto_increment"]
    )


def _decorators_for_field(field: dict[str, Any]) -> list[str]:
    decorators = [f"@typed({_python_runtime_type(field['python_type'])})"]
    if field["nullable"] or field["auto_increment"]:
        decorators.append("@nullable")

    constraints = field.get("constraints", {})
    if constraints.get("not_empty"):
        decorators.append("@not_empty")
    if "min_length" in constraints:
        decorators.append(f"@min_length({constraints['min_length']})")
    if "max_length" in constraints:
        decorators.append(f"@max_length({constraints['max_length']})")
    if "min_value" in constraints:
        decorators.append(f"@min_value({constraints['min_value']})")
    if "max_value" in constraints:
        decorators.append(f"@max_value({constraints['max_value']})")
    if "pattern" in constraints:
        decorators.append(f"@pattern({constraints['pattern']!r})")

    return decorators


def _python_runtime_type(python_type: str) -> str:
    if python_type == "date":
        return "date"
    if python_type == "datetime":
        return "datetime"
    return python_type


def _validation_imports(fields: list[dict[str, Any]]) -> list[str]:
    imports = {"typed"}
    for field in fields:
        if field["nullable"] or field["auto_increment"]:
            imports.add("nullable")

        constraints = field.get("constraints", {})
        if constraints.get("not_empty"):
            imports.add("not_empty")
        if "min_length" in constraints:
            imports.add("min_length")
        if "max_length" in constraints:
            imports.add("max_length")
        if "min_value" in constraints:
            imports.add("min_value")
        if "max_value" in constraints:
            imports.add("max_value")
        if "pattern" in constraints:
            imports.add("pattern")
        if not field["nullable"] and not field["auto_increment"]:
            imports.add("ValidationError")

    order = [
        "ValidationError",
        "max_length",
        "max_value",
        "min_length",
        "min_value",
        "not_empty",
        "nullable",
        "pattern",
        "typed",
    ]
    return [name for name in order if name in imports]


def _datetime_imports(fields: list[dict[str, Any]]) -> list[str]:
    imports: list[str] = []
    python_types = {field["python_type"] for field in fields}
    if "date" in python_types:
        imports.append("date")
    if "datetime" in python_types:
        imports.append("datetime")
    return imports


def _render_init_signature(fields: list[dict[str, Any]]) -> str:
    ordered_fields = sorted(fields, key=lambda field: (not _is_required_in_init(field),))
    params = ["self"]
    for field in ordered_fields:
        default_literal = _python_default_literal(field)
        if default_literal is None:
            params.append(field["name"])
        else:
            params.append(f"{field['name']}={default_literal}")
    return ", ".join(params)


def _render_init_body(fields: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"        self.{field['name']} = {field['name']}"
        for field in sorted(fields, key=lambda field: (not _is_required_in_init(field),))
    )


def _render_property(field: dict[str, Any]) -> str:
    name = field["name"]
    decorators = _decorators_for_field(field)
    decorator_lines = "\n".join(f"    {decorator}" for decorator in decorators)
    allow_none = field["nullable"] or field["auto_increment"]
    none_guard = [
        "        if value is None:",
    ]
    if allow_none:
        none_guard.extend(
            [
                f"            self._{name} = None",
                "            return",
            ]
        )
    else:
        none_guard.append(f'            raise ValidationError("{name}", \'La propriété "{name}" ne peut pas être nulle.\')')

    return (
        f"    @property\n"
        f"    def {name}(self):\n"
        f"        return self._{name}\n\n"
        f"    @{name}.setter\n"
        f"{decorator_lines}\n"
        f"    def {name}(self, value):\n"
        f"{chr(10).join(none_guard)}\n"
        f"        self._{name} = value\n"
    )


def _render_to_dict(fields: list[dict[str, Any]]) -> str:
    lines = ["    def to_dict(self) -> dict:", "        return {"]
    for field in fields:
        name = field["name"]
        python_type = field["python_type"]
        if python_type in {"date", "datetime"}:
            lines.append(
                f'            "{name}": None if self.{name} is None else self.{name}.isoformat(),'
            )
        else:
            lines.append(f'            "{name}": self.{name},')
    lines.extend(["        }", ""])
    return "\n".join(lines)


def _render_from_dict(entity_name: str, fields: list[dict[str, Any]]) -> str:
    lines = [
        "    @classmethod",
        f'    def from_dict(cls, data: dict[str, Any]) -> "{entity_name}Base":',
        "        return cls(",
    ]
    for field in fields:
        name = field["name"]
        python_type = field["python_type"]
        if python_type == "date":
            lines.append(
                f'            {name}=cls._coerce_date(data.get("{name}")),'
            )
        elif python_type == "datetime":
            lines.append(
                f'            {name}=cls._coerce_datetime(data.get("{name}")),'
            )
        else:
            # Accès direct (from_dict attend un dict complet) : renvoie Any, donc
            # assignable au type du champ sans reportArgumentType (FORGE-6).
            lines.append(f'            {name}=data["{name}"],')
    lines.extend(["        )", ""])
    return "\n".join(lines)


def _render_repr(entity_name: str, fields: list[dict[str, Any]]) -> str:
    parts = ", ".join(f"{field['name']}={{self.{field['name']}!r}}" for field in fields)
    return (
        "    def __repr__(self) -> str:\n"
        f'        return f"{entity_name}Base({parts})"\n'
    )


def _render_datetime_helpers(fields: list[dict[str, Any]]) -> str:
    python_types = {field["python_type"] for field in fields}
    blocks: list[str] = []

    if "date" in python_types:
        blocks.append(
            "    @staticmethod\n"
            "    def _coerce_date(value):\n"
            "        if value is None or isinstance(value, date):\n"
            "            return value\n"
            "        return date.fromisoformat(value)\n"
        )

    if "datetime" in python_types:
        blocks.append(
            "    @staticmethod\n"
            "    def _coerce_datetime(value):\n"
            "        if value is None or isinstance(value, datetime):\n"
            "            return value\n"
            "        return datetime.fromisoformat(value)\n"
        )

    if not blocks:
        return ""
    return "\n".join(blocks) + "\n"


def build_entity_base(entity_definition: dict[str, Any]) -> str:
    entity_definition = normalize_entity_definition(entity_definition)
    entity_name = entity_definition["entity"]
    fields = entity_definition["fields"]
    imports = _validation_imports(fields)
    import_block = "\n".join(f"    {name}," for name in imports)
    datetime_imports = _datetime_imports(fields)
    datetime_import_block = ""
    if datetime_imports:
        datetime_import_block = (
            "from datetime import " + ", ".join(datetime_imports) + "\n\n"
        )

    return (
        '"""FICHIER GENERE PAR FORGE.\n'
        f"Base regenerable de l'entite {entity_name}.\n"
        "Ne pas y ajouter de logique metier manuelle.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "from typing import Any\n\n"
        f"{datetime_import_block}"
        "from core.validation import (\n"
        f"{import_block}\n"
        ")\n\n\n"
        f"class {entity_name}Base:\n"
        f'    """Classe de base regenerable de {entity_name}."""\n\n'
        f"    def __init__({_render_init_signature(fields)}):\n"
        f"{_render_init_body(fields)}\n\n"
        f"{_render_datetime_helpers(fields)}"
        f"{chr(10).join(_render_property(field) for field in fields)}\n"
        f"{_render_to_dict(fields)}\n"
        f"{_render_from_dict(entity_name, fields)}\n"
        f"{_render_repr(entity_name, fields)}\n"
    )


def build_entity_manual(entity_name: str, snake: str) -> str:
    return (
        f'"""Classe metier manuelle pour {entity_name}."""\n\n'
        f"from .{snake}_base import {entity_name}Base\n\n\n"
        f"class {entity_name}({entity_name}Base):\n"
        f'    """Point d\'extension metier pour {entity_name}."""\n\n'
        f"    pass\n"
    )


def build_entity_init(entity_name: str) -> str:
    # Alias redondant `as` : ré-export explicite (PEP 484), reconnu par ruff, donc
    # pas de F401 « imported but unused » dans le __init__.py d'entité (FORGE-7).
    snake = to_snake(entity_name)
    return f"from .{snake} import {entity_name} as {entity_name}\n"


def ensure_file(path: Path, content: str, created: list[Path], skipped: list[Path]) -> None:
    if path.exists():
        skipped.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path)


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    entity_name_arg, interactive = _parse_args(args)

    if not interactive and entity_name_arg is None:
        print("Usage : forge make:entity Contact --no-input")
        raise SystemExit(1)

    try:
        if interactive:
            validated_name = None
            if entity_name_arg is not None:
                validated_name = validate_entity_name(entity_name_arg)
            entity_definition = build_entity_json_interactively(validated_name)
        else:
            entity_definition = build_entity_json_canonical(validate_entity_name(entity_name_arg or ""))
    except ValueError as exc:
        print(out.error(str(exc)))
        raise SystemExit(1)

    entity_name = entity_definition["name"]
    snake = to_snake(entity_name)
    root = project_root()
    entity_dir = entities_dir(root) / snake
    json_source = str(entity_dir / f"{snake}.json")

    try:
        from forge_mvc_entities.canonical_model_normalizer import normalize_canonical_entity_for_model_build
        legacy = normalize_canonical_entity_for_model_build(entity_definition)
        normalized_definition = validate_entity_definition(legacy, source=json_source)
    except (EntityDefinitionError, ValueError) as exc:
        print(out.error(str(exc)))
        raise SystemExit(1)

    if interactive:
        print("Résumé avant écriture")
        print(_render_entity_summary(entity_definition))
        print("")
        print("JSON auteur généré :")
        print(json.dumps(entity_definition, indent=2, ensure_ascii=True))
        print("")
        if not _prompt_yes_no("Confirmer l'écriture des fichiers ?", default=True):
            print("Aucune écriture effectuée.")
            raise SystemExit(0)

    entity_name, snake, created, skipped = _write_entity_files(
        entity_definition,
        normalized_definition,
        root=root,
    )

    if not created:
        print(out.error(f"L'entite {entity_name} existe deja, aucun fichier cree."))
        raise SystemExit(1)

    print(f"Entite {entity_name} initialisee dans mvc/entities/{snake}/")
    for path in created:
        print(out.created(str(path.relative_to(root))))
    for path in skipped:
        print(out.preserved(str(path.relative_to(root))))
    print(out.info(f"Vous pouvez encore modifier mvc/entities/{snake}/{snake}.json manuellement si besoin."))


if __name__ == "__main__":
    main()
