# pyright: strict
"""Commande ``forge fixtures:purge`` — vide les tables ciblées par les fixtures (ADR-074).

Repart d'un état propre : supprime les lignes des tables que les fixtures du
projet (``mvc/fixtures/*.sql``) peuplent. Les tables cibles sont **dérivées** des
``INSERT INTO`` des fixtures, puis vidées par des ``DELETE FROM`` en ordre inverse
(pour respecter d'éventuelles clés étrangères : on supprime les tables
référençantes avant les référencées).

Comme ``fixtures:load`` (charte §7) : la commande **affiche** les ``DELETE`` par
défaut (rien de caché, principe 3), ``--run`` exécute, et ``--run --force`` est
requis en ``APP_ENV=prod``.

Frontière (ADR-074) : ne touche pas au schéma. C'est une remise à zéro des
données de démo/test, pas un ``DROP``.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from forge_mvc_fixtures.cli.load import (
    STATUS_OK,
    active_env,
    collect_fixture_files,
)

__all__ = ["collect_target_tables", "purge_fixtures", "main"]

# `INSERT INTO <table>` avec backticks optionnels ; identifiant SQL simple.
_INSERT_RE = re.compile(r"\bINSERT\s+INTO\s+`?([A-Za-z_][A-Za-z0-9_]*)`?", re.IGNORECASE)


def _strip_line_comments(sql: str) -> str:
    return "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )


def collect_target_tables(files: list[Path]) -> list[str]:
    """Tables peuplées par les fixtures, dans leur ordre de première apparition."""
    seen: list[str] = []
    for path in files:
        text = _strip_line_comments(path.read_text(encoding="utf-8"))
        for match in _INSERT_RE.finditer(text):
            table = match.group(1)
            if table not in seen:
                seen.append(table)
    return seen


def purge_fixtures(root: Path, *, run: bool, force: bool, env: str) -> int:
    """Affiche (et, si ``run``, exécute) les ``DELETE`` de purge des tables cibles.

    Codes de sortie : 0 succès ou affichage seul, 2 refus (prod sans ``--force``),
    1 erreur d'exécution SQL.
    """
    files = collect_fixture_files(root)
    if not files:
        print("Aucune fixture. Rien à purger (mvc/fixtures/ est vide ou absent).")
        return 0

    tables = collect_target_tables(files)
    if not tables:
        print(
            "Aucune table cible détectée dans les fixtures "
            "(aucun INSERT INTO relu dans mvc/fixtures/*.sql)."
        )
        return 0

    # Ordre inverse d'insertion : supprimer les référençantes avant les référencées.
    statements = [f"DELETE FROM {table}" for table in reversed(tables)]

    if run and env == "prod" and not force:
        print(
            f"Refus : purge de fixtures en environnement '{env}'. "
            "Ajoutez --force pour confirmer explicitement (ADR-074).",
            file=sys.stderr,
        )
        return 2

    print(
        f"Purge des tables ciblées par les fixtures dans l'environnement "
        f"'{env}' ({len(tables)} table(s)) :\n"
    )
    for statement in statements:
        print(f"{statement};")
    print()

    if not run:
        print("Affichage seul. Relancez avec --run pour exécuter (charte §7).")
        return 0

    from core.database import db

    for statement in statements:
        try:
            db.execute(statement)
        except Exception as exc:  # noqa: BLE001 — on rapporte la cause précise
            print(
                f"Erreur en purgeant : {exc}\nInstruction : {statement}",
                file=sys.stderr,
            )
            return 1

    print(
        f"{STATUS_OK} {len(statements)} table(s) vidée(s) dans l'environnement '{env}'."
    )
    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge fixtures:purge``."""
    argv = list(args or [])
    run = "--run" in argv
    force = "--force" in argv
    return purge_fixtures(Path.cwd(), run=run, force=force, env=active_env())
