# pyright: strict
"""Commande ``forge fixtures:load`` — charge des fixtures SQL (ADR-074).

Charge les fichiers ``mvc/fixtures/*.sql`` du projet dans la base de
**l'environnement actif** (``APP_ENV``, défaut ``dev``), via la connexion
applicative ``core.database.db``.

À la manière de ``forge db:init`` (charte §7), la commande **affiche** le SQL
par défaut : on voit ce qui va être écrit avant que ce soit écrit. Il faut
``--run`` pour exécuter. En ``APP_ENV=prod``, ``--run`` seul refuse : charger
des fixtures en production exige le geste explicite ``--run --force``.

Frontière (ADR-074, principe 11) : cet opt-in peuple des tables déjà
provisionnées avec des données de démo/test rejouables. Le référentiel permanent
reste une migration appliquée par ``forge migration:apply``.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, cast

STATUS_OK = "[OK]"

__all__ = [
    "STATUS_OK",
    "active_env",
    "collect_fixture_files",
    "order_fixture_files",
    "split_sql_statements",
    "load_fixtures",
    "main",
]

_INSERT_INTO = re.compile(r"INSERT\s+INTO\s+[`\"\[]?(\w+)", re.IGNORECASE)


def active_env() -> str:
    """Nom de l'environnement actif (``APP_ENV``, défaut ``dev``)."""
    return os.getenv("APP_ENV", "dev")


def collect_fixture_files(root: Path) -> list[Path]:
    """Fichiers ``mvc/fixtures/*.sql`` du projet, triés par nom."""
    fixtures_dir = root / "mvc" / "fixtures"
    if not fixtures_dir.is_dir():
        return []
    return sorted(fixtures_dir.glob("*.sql"), key=lambda path: path.name)


def _table_of_file(path: Path) -> str | None:
    """Table ciblée par le fichier (premier ``INSERT INTO``), sinon le nom de fichier."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = _INSERT_INTO.search(text)
    if match:
        return match.group(1)
    return path.stem


def _entity_tables(root: Path) -> dict[str, str]:
    """Table de chaque entité (``<entity>.json`` -> ``table``), indexée par nom PascalCase."""
    entities_dir = root / "mvc" / "entities"
    mapping: dict[str, str] = {}
    if not entities_dir.is_dir():
        return mapping
    for contract in entities_dir.glob("*/*.json"):
        if contract.stem != contract.parent.name:
            continue
        try:
            data = json.loads(contract.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        entity = cast("dict[str, Any]", data)
        name = entity.get("name")
        table = entity.get("table")
        if isinstance(name, str) and isinstance(table, str) and name and table:
            mapping[name] = table
    return mapping


def _fk_dependencies(root: Path) -> dict[str, set[str]] | None:
    """Graphe de dépendances FK entre entités (``from`` dépend de ``to``).

    Déduit des relations ``many_to_one`` de ``relations.json``. Renvoie ``None``
    si le fichier est absent ou illisible (pas d'ordre à imposer).
    """
    path = root / "mvc" / "entities" / "relations.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    relations = cast("dict[str, Any]", data).get("relations")
    if not isinstance(relations, list):
        return None
    deps: dict[str, set[str]] = {}
    for rel_obj in cast("list[Any]", relations):
        if not isinstance(rel_obj, dict):
            continue
        rel = cast("dict[str, Any]", rel_obj)
        if rel.get("type") != "many_to_one":
            continue
        source = rel.get("from")
        target = rel.get("to")
        if isinstance(source, str) and isinstance(target, str) and source != target:
            deps.setdefault(source, set()).add(target)
            deps.setdefault(target, set())
    return deps


def _topological_order(deps: dict[str, set[str]]) -> list[str] | None:
    """Ordre topologique des entités (dépendances chargées d'abord). ``None`` si cycle."""
    remaining = {node: set(edges) for node, edges in deps.items()}
    ordered: list[str] = []
    while remaining:
        ready = sorted(node for node, edges in remaining.items() if not edges)
        if not ready:
            return None  # cycle
        for node in ready:
            ordered.append(node)
            del remaining[node]
        for edges in remaining.values():
            edges.difference_update(ready)
    return ordered


def order_fixture_files(root: Path, files: list[Path]) -> list[Path]:
    """Ordonne les fichiers pour respecter les dépendances de clés étrangères (F44).

    Tri topologique du graphe déduit de ``relations.json`` : une entité est
    chargée après celles qu'elle référence. Repli sur l'ordre par nom de fichier
    si ``relations.json`` est absent, si une table est inconnue, ou en cas de
    cycle (le préfixe numérique ``01_`` reste un ordre déclaratif de secours).
    """
    by_name = sorted(files, key=lambda path: path.name)
    deps = _fk_dependencies(root)
    if deps is None:
        return by_name
    topo = _topological_order(deps)
    if topo is None:
        return by_name
    rank = {entity: index for index, entity in enumerate(topo)}

    tables = _entity_tables(root)
    table_to_entity = {table: entity for entity, table in tables.items()}
    unknown_rank = len(topo)

    def sort_key(path: Path) -> tuple[int, str]:
        table = _table_of_file(path)
        entity = table_to_entity.get(table) if table else None
        return (rank.get(entity, unknown_rank) if entity else unknown_rank, path.name)

    return sorted(by_name, key=sort_key)


def _strip_line_comments(sql: str) -> str:
    """Retire les lignes de commentaire ``--`` (le SQL affiché les garde)."""
    return "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )


def split_sql_statements(sql: str) -> list[str]:
    """Découpe un script SQL en instructions, en respectant les chaînes ``'...'``.

    Un ``;`` à l'intérieur d'un littéral chaîne (par exemple une donnée de
    fixture contenant un point-virgule) n'est pas un séparateur. Les guillemets
    simples doublés (``''``) sont l'échappement SQL standard.
    """
    statements: list[str] = []
    current: list[str] = []
    in_string = False
    i = 0
    n = len(sql)
    while i < n:
        char = sql[i]
        if in_string:
            current.append(char)
            if char == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    current.append(sql[i + 1])
                    i += 2
                    continue
                in_string = False
            i += 1
            continue
        if char == "'":
            in_string = True
            current.append(char)
        elif char == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)
        i += 1
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def load_fixtures(
    root: Path, *, run: bool, force: bool, env: str, no_fk_checks: bool = False
) -> int:
    """Affiche (et, si ``run``, exécute) les fixtures du projet.

    Les fichiers sont ordonnés par dépendances de clés étrangères (F44). Avec
    ``no_fk_checks``, le chargement est encadré par la désactivation des
    contraintes du dialecte (jeux non triables, cycles).

    Retourne le code de sortie : 0 succès ou affichage seul, 2 refus (prod sans
    ``--force``), 1 erreur d'exécution SQL.
    """
    files = order_fixture_files(root, collect_fixture_files(root))
    if not files:
        print(
            "Aucune fixture à charger. "
            "Créez des fichiers .sql dans mvc/fixtures/ (SQL visible, relu)."
        )
        return 0

    if run and env == "prod" and not force:
        print(
            f"Refus : chargement de fixtures en environnement '{env}'. "
            "Ajoutez --force pour confirmer explicitement (ADR-074).",
            file=sys.stderr,
        )
        return 2

    print(f"Fixtures pour l'environnement '{env}' ({len(files)} fichier(s)) :\n")
    for path in files:
        print(f"-- {path.name}")
        print(path.read_text(encoding="utf-8").strip())
        print()

    if not run:
        print("Affichage seul. Relancez avec --run pour exécuter (charte §7).")
        return 0

    from core.database import db

    disable_ddl: list[str] = []
    enable_ddl: list[str] = []
    if no_fk_checks:
        from core.database.backend import get_backend

        dialect = get_backend().dialect
        disable_ddl = dialect.foreign_key_checks_ddl(enabled=False)
        enable_ddl = dialect.foreign_key_checks_ddl(enabled=True)
        if not disable_ddl:
            print(
                "Note : ce backend n'expose pas de désactivation FK de session ; "
                "le chargement s'appuie sur l'ordre topologique seul."
            )

    executed = 0
    try:
        for statement in disable_ddl:
            db.execute(statement)
        for path in files:
            statements = split_sql_statements(_strip_line_comments(
                path.read_text(encoding="utf-8")
            ))
            for statement in statements:
                try:
                    db.execute(statement)
                except Exception as exc:  # noqa: BLE001 — on rapporte la cause précise
                    print(
                        f"Erreur en chargeant {path.name} : {exc}\n"
                        f"Instruction : {statement}",
                        file=sys.stderr,
                    )
                    return 1
                executed += 1
    finally:
        for statement in enable_ddl:
            db.execute(statement)

    print(
        f"{STATUS_OK} {len(files)} fichier(s), {executed} instruction(s) "
        f"chargée(s) dans l'environnement '{env}'."
    )
    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge fixtures:load``."""
    argv = list(args or [])
    run = "--run" in argv
    force = "--force" in argv
    no_fk_checks = "--no-fk-checks" in argv
    return load_fixtures(
        Path.cwd(), run=run, force=force, env=active_env(), no_fk_checks=no_fk_checks
    )
