#!/usr/bin/env python3
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
from typing import Callable

import forge_cli.output as out
from forge_cli.entities.validation import (
    EntityDefinitionError,
    normalize_entity_definition,
    validate_entity_definition,
)

SUPPORTED_SQL_BASE_TYPES = (
    "INT",
    "BIGINT",
    "VARCHAR",
    "CHAR",
    "TEXT",
    "DATE",
    "DATETIME",
    "BOOLEAN",
    "DECIMAL",
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


def build_entity_json(entity_name: str) -> dict:
    return {
        "entity": entity_name,
        "fields": [
            {
                "name": "id",
                "sql_type": "INT",
                "primary_key": True,
                "auto_increment": True,
            }
        ],
    }


def _sql_family_for_prompt(sql_type: str) -> str | None:
    normalized = sql_type.strip().upper()
    if normalized == "DATE":
        return "date"
    if normalized in {"DATETIME", "TIMESTAMP"}:
        return "datetime"
    if normalized in {"BOOL", "BOOLEAN"}:
        return "bool"
    for prefix in ("INT", "BIGINT", "SMALLINT", "TINYINT", "MEDIUMINT"):
        if normalized.startswith(prefix):
            return "int"
    for prefix in ("FLOAT", "DOUBLE", "REAL", "DECIMAL", "NUMERIC"):
        if normalized.startswith(prefix):
            return "float"
    for prefix in ("CHAR", "VARCHAR", "TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT"):
        if normalized.startswith(prefix):
            return "str"
    return None


def _is_supported_sql_type(sql_type: str) -> bool:
    normalized = sql_type.strip().upper()
    if normalized.startswith("VARCHAR(") and normalized.endswith(")"):
        return True
    if normalized.startswith("CHAR(") and normalized.endswith(")"):
        return True
    if normalized.startswith("DECIMAL(") and normalized.endswith(")"):
        return True
    return normalized in {
        "INT",
        "BIGINT",
        "SMALLINT",
        "TINYINT",
        "MEDIUMINT",
        "FLOAT",
        "DOUBLE",
        "REAL",
        "DECIMAL",
        "NUMERIC",
        "VARCHAR",
        "CHAR",
        "TEXT",
        "TINYTEXT",
        "MEDIUMTEXT",
        "LONGTEXT",
        "DATE",
        "DATETIME",
        "TIMESTAMP",
        "BOOL",
        "BOOLEAN",
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


def _prompt_sql_type(
    label: str,
    *,
    default: str | None = None,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    help_label = (
        f"{label} "
        "[INT, BIGINT, VARCHAR, CHAR, TEXT, DATE, DATETIME, BOOLEAN, DECIMAL]"
    )
    while True:
        raw_value = _prompt_text(help_label, default=default, input_fn=input_fn)
        normalized = raw_value.strip().upper()

        if not _is_supported_sql_type(normalized):
            print(
                "Type SQL invalide. Valeurs courantes attendues : "
                "INT, BIGINT, VARCHAR, CHAR, TEXT, DATE, DATETIME, BOOLEAN, DECIMAL."
            )
            continue

        if "(" in normalized and normalized.endswith(")"):
            return normalized

        if normalized in {"VARCHAR", "CHAR"}:
            length = _prompt_required_int("Longueur SQL", input_fn=input_fn)
            return f"{normalized}({length})"

        if normalized == "DECIMAL":
            precision = _prompt_required_int("Precision SQL", input_fn=input_fn)
            scale = _prompt_required_int("Echelle SQL", input_fn=input_fn)
            return f"DECIMAL({precision},{scale})"

        return normalized


def _build_primary_field(entity_name: str, *, input_fn: Callable[[str], str] | None = None) -> dict:
    default_name = "id"
    field_name = _prompt_text("Nom du champ primaire", default=default_name, input_fn=input_fn)
    sql_type = _prompt_sql_type("Type SQL du champ primaire", default="INT", input_fn=input_fn)

    field = {
        "name": field_name,
        "sql_type": sql_type,
        "primary_key": True,
    }

    if _sql_family_for_prompt(sql_type) == "int":
        if _prompt_yes_no("Auto increment ?", default=True, input_fn=input_fn):
            field["auto_increment"] = True
    return field


def _build_additional_field(*, input_fn: Callable[[str], str] | None = None) -> dict:
    field_name = _prompt_text("Nom du champ", input_fn=input_fn)
    sql_type = _prompt_sql_type("Type SQL", input_fn=input_fn)
    field_family = _sql_family_for_prompt(sql_type)

    field: dict[str, object] = {
        "name": field_name,
        "sql_type": sql_type,
    }

    if _prompt_yes_no("Autoriser NULL ?", default=False, input_fn=input_fn):
        field["nullable"] = True

    if _prompt_yes_no("Champ unique ?", default=False, input_fn=input_fn):
        field["unique"] = True

    constraints: dict[str, object] = {}
    if field_family == "str":
        if not field.get("nullable") and _prompt_yes_no("Ajouter not_empty ?", default=False, input_fn=input_fn):
            constraints["not_empty"] = True
        min_length = _prompt_optional_int("min_length", input_fn=input_fn)
        if min_length is not None:
            constraints["min_length"] = min_length
        max_length = _prompt_optional_int("max_length", input_fn=input_fn)
        if max_length is not None:
            constraints["max_length"] = max_length
        pattern = _prompt_text(
            "Validation regex [vide = aucune, ex: ^[A-Z]+$ ou ^[^@]+@[^@]+\\.[^@]+$]",
            allow_empty=True,
            input_fn=input_fn,
        )
        if pattern:
            constraints["pattern"] = pattern
    elif field_family in {"int", "float"}:
        min_value = _prompt_optional_number("min_value", input_fn=input_fn)
        if min_value is not None:
            constraints["min_value"] = min_value
        max_value = _prompt_optional_number("max_value", input_fn=input_fn)
        if max_value is not None:
            constraints["max_value"] = max_value

    if constraints:
        field["constraints"] = constraints
    return field


def build_entity_json_interactively(
    entity_name: str | None = None,
    *,
    input_fn: Callable[[str], str] | None = None,
) -> dict:
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
    )

    fields = [_build_primary_field(entity_name, input_fn=input_fn)]
    while _prompt_yes_no("Ajouter un autre champ ?", default=False, input_fn=input_fn):
        fields.append(_build_additional_field(input_fn=input_fn))

    entity_definition: dict[str, object] = {
        "entity": entity_name,
        "fields": fields,
    }
    if table_name and table_name != default_table:
        entity_definition["table"] = table_name
    return entity_definition


def _render_entity_summary(entity_definition: dict) -> str:
    lines = [
        f"Entité : {entity_definition['entity']}",
        f"Table : {entity_definition.get('table', to_snake(entity_definition['entity']))}",
        "Champs :",
    ]
    for field in entity_definition["fields"]:
        parts = [field["name"], field["sql_type"]]
        if field.get("primary_key"):
            parts.append("PK")
        if field.get("auto_increment"):
            parts.append("AUTO_INCREMENT")
        if field.get("nullable"):
            parts.append("NULL")
        if field.get("unique"):
            parts.append("UNIQUE")
        constraints = field.get("constraints")
        if constraints:
            parts.append(f"constraints={constraints}")
        lines.append(f"- {' | '.join(str(part) for part in parts)}")
    return "\n".join(lines)


def _parse_args(args: list[str]) -> tuple[str | None, bool]:
    entity_name: str | None = None
    interactive = True

    for arg in args:
        if arg in {"-h", "--help"}:
            print(__doc__.strip())
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
        print(__doc__.strip())
        raise SystemExit(1)

    return entity_name, interactive


def _write_entity_files(
    entity_definition: dict,
    normalized_definition: dict,
    *,
    root: Path | None = None,
) -> tuple[str, str, list[Path], list[Path]]:
    entity_name = entity_definition["entity"]
    snake = to_snake(entity_name)
    root = root or project_root()
    target_entities_dir = entities_dir(root)
    entity_dir = target_entities_dir / snake

    created: list[Path] = []
    skipped: list[Path] = []

    ensure_file(target_entities_dir / "__init__.py", "", created, skipped)
    ensure_file(
        target_entities_dir / "relations.json",
        json.dumps({"format_version": 1, "relations": []}, indent=2, ensure_ascii=True) + "\n",
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


def _sql_default_literal(field: dict) -> str | None:
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


def build_entity_sql(entity_definition: dict) -> str:
    entity_definition = normalize_entity_definition(entity_definition)
    table = entity_definition["table"]
    fields = entity_definition["fields"]

    lines = [f"CREATE TABLE IF NOT EXISTS {table} ("]
    body_lines: list[str] = []
    primary_key_column = None

    for field in fields:
        parts = [f"    {field['column']} {field['sql_type']}"]
        parts.append("NULL" if field["nullable"] else "NOT NULL")
        if field["auto_increment"]:
            parts.append("AUTO_INCREMENT")
        default_literal = _sql_default_literal(field)
        if default_literal is not None:
            parts.append(f"DEFAULT {default_literal}")
        body_lines.append(" ".join(parts))

        if field["primary_key"]:
            primary_key_column = field["column"]
        if field.get("unique") is True:
            body_lines.append(f"    UNIQUE KEY uk_{table}_{field['name']} ({field['column']})")

    if primary_key_column is not None:
        body_lines.append(f"    PRIMARY KEY ({primary_key_column})")

    lines.append(",\n".join(body_lines))
    lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;")
    return "\n".join(lines) + "\n"


def _python_default_literal(field: dict) -> str | None:
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


def _is_required_in_init(field: dict) -> bool:
    return (
        not field["nullable"]
        and "default" not in field
        and not field["auto_increment"]
    )


def _decorators_for_field(field: dict) -> list[str]:
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


def _validation_imports(fields: list[dict]) -> list[str]:
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


def _datetime_imports(fields: list[dict]) -> list[str]:
    imports: list[str] = []
    python_types = {field["python_type"] for field in fields}
    if "date" in python_types:
        imports.append("date")
    if "datetime" in python_types:
        imports.append("datetime")
    return imports


def _render_init_signature(fields: list[dict]) -> str:
    ordered_fields = sorted(fields, key=lambda field: (not _is_required_in_init(field),))
    params = ["self"]
    for field in ordered_fields:
        default_literal = _python_default_literal(field)
        if default_literal is None:
            params.append(field["name"])
        else:
            params.append(f"{field['name']}={default_literal}")
    return ", ".join(params)


def _render_init_body(fields: list[dict]) -> str:
    return "\n".join(
        f"        self.{field['name']} = {field['name']}"
        for field in sorted(fields, key=lambda field: (not _is_required_in_init(field),))
    )


def _render_property(field: dict) -> str:
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


def _render_to_dict(fields: list[dict]) -> str:
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


def _render_from_dict(entity_name: str, fields: list[dict]) -> str:
    lines = [
        "    @classmethod",
        f'    def from_dict(cls, data: dict) -> "{entity_name}Base":',
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
            lines.append(f'            {name}=data.get("{name}"),')
    lines.extend(["        )", ""])
    return "\n".join(lines)


def _render_repr(entity_name: str, fields: list[dict]) -> str:
    parts = ", ".join(f"{field['name']}={{self.{field['name']}!r}}" for field in fields)
    return (
        "    def __repr__(self) -> str:\n"
        f'        return f"{entity_name}Base({parts})"\n'
    )


def _render_datetime_helpers(fields: list[dict]) -> str:
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


def build_entity_base(entity_definition: dict) -> str:
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
    return f"from .{to_snake(entity_name)} import {entity_name}\n"


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
            entity_definition = build_entity_json(validate_entity_name(entity_name_arg or ""))
    except ValueError as exc:
        print(out.error(str(exc)))
        raise SystemExit(1)

    entity_name = entity_definition["entity"]
    snake = to_snake(entity_name)
    root = project_root()
    entity_dir = entities_dir(root) / snake
    json_source = str(entity_dir / f"{snake}.json")

    try:
        normalized_definition = validate_entity_definition(entity_definition, source=json_source)
    except EntityDefinitionError as exc:
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
