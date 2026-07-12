# pyright: strict
"""Commande ``forge fixtures:generate`` — génère un ``.sql`` depuis une factory (ADR-076).

Localise la factory de l'entité (``mvc/fixtures/factories/<entity>_factory.py``),
l'exécute, rend les lignes en ``INSERT INTO`` via ``dialect.render_literal`` (donc
correct pour le backend installé, ADR-075), **affiche** le SQL puis l'écrit dans
``mvc/fixtures/<table>.sql`` (write-if-new, charte §9 : jamais d'écrasement sans
``--force``).

Le chargement reste ``fixtures:load`` : la génération alimente la voie existante,
elle n'insère pas en base (principe 11).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from forge_mvc_fixtures.factory import Factory, FactoryError, FixtureReference

__all__ = [
    "load_factory",
    "render_value",
    "render_inserts",
    "generate_fixtures",
    "main",
]

DEFAULT_ROWS = 10


class GenerateError(Exception):
    """Erreur de génération (factory introuvable, entité invalide)."""


def load_factory(root: Path, entity: str) -> Factory:
    """Importe la factory de l'entité et l'instancie (sans seed)."""
    path = root / "mvc" / "fixtures" / "factories" / f"{entity}_factory.py"
    if not path.is_file():
        raise GenerateError(
            f"Factory introuvable : {path.as_posix()}. "
            f"Créez-la avec `forge fixtures:make-factory {entity}`."
        )
    spec = importlib.util.spec_from_file_location(f"_forge_factory_{entity}", path)
    if spec is None or spec.loader is None:
        raise GenerateError(f"Chargement impossible : {path.as_posix()}.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    candidates = [
        value
        for value in vars(module).values()
        if isinstance(value, type) and issubclass(value, Factory) and value is not Factory
    ]
    if not candidates:
        raise GenerateError(f"Aucune sous-classe de Factory dans {path.name}.")
    if len(candidates) > 1:
        preferred = f"{entity.capitalize()}Factory"
        named = [c for c in candidates if c.__name__ == preferred]
        if len(named) != 1:
            names = ", ".join(sorted(c.__name__ for c in candidates))
            raise GenerateError(
                f"Plusieurs factories dans {path.name} ({names}) ; "
                f"nommez-en une {preferred}."
            )
        candidates = named
    return candidates[0]()


def render_value(value: Any, dialect: Any) -> str:
    """Rend une valeur de colonne en SQL pour le dialecte donné.

    Un ``FixtureReference`` (ADR-077) devient une sous-requête résolue à la charge
    ``(SELECT Id FROM <table> WHERE <key_column> = <valeur> LIMIT 1)`` ; toute autre
    valeur passe par ``dialect.render_literal`` (littéral correct par backend, ADR-075).
    """
    if isinstance(value, FixtureReference):
        literal = dialect.render_literal(value.value)
        return (
            f"(SELECT Id FROM {value.table} "
            f"WHERE {value.key_column} = {literal} LIMIT 1)"
        )
    return dialect.render_literal(value)


def render_inserts(table: str, rows: list[dict[str, Any]], dialect: Any) -> str:
    """Rend les lignes en instructions ``INSERT INTO`` pour le dialecte donné."""
    if not rows:
        return f"-- Aucune ligne générée pour {table}.\n"
    columns = list(rows[0].keys())
    col_list = ", ".join(columns)
    lines = [
        f"-- Fixtures pour {table}, générées par forge fixtures:generate.",
        "-- Relire avant de charger (forge fixtures:load).",
    ]
    for row in rows:
        values = ", ".join(render_value(row[column], dialect) for column in columns)
        lines.append(f"INSERT INTO {table} ({col_list}) VALUES ({values});")
    return "\n".join(lines) + "\n"


def generate_fixtures(
    root: Path,
    entity: str,
    *,
    rows: int,
    seed: int | None,
    force: bool,
    dialect: Any,
) -> int:
    """Génère le ``.sql`` de l'entité. Codes : 0 écrit, 2 erreur, 1 fichier existant."""
    try:
        factory = load_factory(root, entity)
        factory_instance = type(factory)(seed=seed)
        built = factory_instance.build(rows)
    except (GenerateError, FactoryError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2

    table = factory_instance.table
    sql = render_inserts(table, built, dialect)

    print(sql)

    target = root / "mvc" / "fixtures" / f"{table}.sql"
    if target.exists() and not force:
        print(
            f"Fichier déjà présent, non écrit : {target.as_posix()}. "
            "Ajoutez --force pour le remplacer (charte §9).",
            file=sys.stderr,
        )
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(sql, encoding="utf-8")
    print(f"[OK] {len(built)} ligne(s) écrite(s) dans {target.as_posix()}.")
    return 0


def _parse_args(argv: list[str]) -> tuple[str, int, int | None, bool]:
    entity: str | None = None
    rows = DEFAULT_ROWS
    seed: int | None = None
    force = False
    items = list(argv)
    i = 0
    while i < len(items):
        arg = items[i]
        if arg == "--force":
            force = True
        elif arg == "--rows" or arg == "--seed":
            i += 1
            if i >= len(items):
                raise GenerateError(f"Valeur manquante après {arg}.")
            value = _parse_int(items[i], arg)
            if arg == "--rows":
                rows = value
            else:
                seed = value
        elif arg.startswith("--rows="):
            rows = _parse_int(arg.split("=", 1)[1], "--rows")
        elif arg.startswith("--seed="):
            seed = _parse_int(arg.split("=", 1)[1], "--seed")
        elif arg.startswith("-"):
            raise GenerateError(f"Option inconnue : {arg}.")
        elif entity is None:
            entity = arg
        else:
            raise GenerateError(f"Argument en trop : {arg}.")
        i += 1
    if entity is None:
        raise GenerateError("Entité manquante. Usage : forge fixtures:generate <entity>.")
    return entity, rows, seed, force


def _parse_int(raw: str, flag: str) -> int:
    try:
        return int(raw)
    except ValueError:
        raise GenerateError(f"{flag} attend un entier, reçu : {raw!r}.") from None


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge fixtures:generate``."""
    try:
        entity, rows, seed, force = _parse_args(list(args or []))
    except GenerateError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2

    from core.database.backend import get_backend

    try:
        dialect = get_backend().dialect
    except Exception as exc:  # noqa: BLE001 — message d'aide explicite
        print(
            f"Erreur : backend BDD indisponible ({exc}). "
            "Installez un backend (ex. pip install forge-mvc-sqlite).",
            file=sys.stderr,
        )
        return 2

    return generate_fixtures(
        Path.cwd(), entity, rows=rows, seed=seed, force=force, dialect=dialect
    )
