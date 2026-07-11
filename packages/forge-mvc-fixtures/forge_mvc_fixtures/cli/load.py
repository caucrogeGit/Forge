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

import os
import sys
from pathlib import Path

STATUS_OK = "[OK]"

__all__ = [
    "STATUS_OK",
    "active_env",
    "collect_fixture_files",
    "split_sql_statements",
    "load_fixtures",
    "main",
]


def active_env() -> str:
    """Nom de l'environnement actif (``APP_ENV``, défaut ``dev``)."""
    return os.getenv("APP_ENV", "dev")


def collect_fixture_files(root: Path) -> list[Path]:
    """Fichiers ``mvc/fixtures/*.sql`` du projet, triés par nom."""
    fixtures_dir = root / "mvc" / "fixtures"
    if not fixtures_dir.is_dir():
        return []
    return sorted(fixtures_dir.glob("*.sql"), key=lambda path: path.name)


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


def load_fixtures(root: Path, *, run: bool, force: bool, env: str) -> int:
    """Affiche (et, si ``run``, exécute) les fixtures du projet.

    Retourne le code de sortie : 0 succès ou affichage seul, 2 refus (prod sans
    ``--force``), 1 erreur d'exécution SQL.
    """
    files = collect_fixture_files(root)
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

    executed = 0
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
    return load_fixtures(Path.cwd(), run=run, force=force, env=active_env())
