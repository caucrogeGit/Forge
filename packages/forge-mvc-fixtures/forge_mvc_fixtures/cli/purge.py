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
    FixtureDiscoveryError,
    active_env,
    collect_callable_fixtures,
    collect_fixture_files,
    order_load_units,
)
from forge_mvc_fixtures.factory import Fixture

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
    """Affiche (et, si ``run``, exécute) le démontage des fixtures du projet.

    Démonte en ordre **inverse** du chargement : d'abord les fixtures callable
    (``Fixture.purge()``, défaut sur ``tables`` déclarées, ADR-078), puis les
    tables des ``.sql`` (``DELETE FROM`` en ordre inverse d'insertion).

    Codes de sortie : 0 succès ou affichage seul, 2 refus (prod sans ``--force``
    ou fixture illisible), 1 erreur d'exécution.
    """
    files = collect_fixture_files(root)
    try:
        callables = collect_callable_fixtures(root)
    except FixtureDiscoveryError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2

    if not files and not callables:
        print("Aucune fixture. Rien à purger (mvc/fixtures/ est vide ou absent).")
        return 0

    tables = collect_target_tables(files)
    # Ordre inverse d'insertion : supprimer les référençantes avant les référencées.
    statements = [f"DELETE FROM {table}" for table in reversed(tables)]
    # Callable démontées avant les .sql (elles en dépendent) : inverse du chargement.
    teardown = list(reversed(order_load_units(root, [], callables)))

    if not statements and not teardown:
        print(
            "Aucune table cible détectée dans les fixtures "
            "(aucun INSERT INTO relu, aucune fixture callable purgeable)."
        )
        return 0

    if run and env == "prod" and not force:
        print(
            f"Refus : purge de fixtures en environnement '{env}'. "
            "Ajoutez --force pour confirmer explicitement (ADR-074).",
            file=sys.stderr,
        )
        return 2

    print(
        f"Démontage des fixtures dans l'environnement '{env}' "
        f"({len(teardown)} fixture(s) Python, {len(tables)} table(s) SQL) :\n"
    )
    for unit in teardown:
        fixture_cls = unit.fixture
        if fixture_cls is None:
            continue
        if fixture_cls.purge is not Fixture.purge:
            print(f"-- {unit.path.name} : purge() personnalisé (démontage sur-mesure)")
        elif fixture_cls.tables:
            for table in reversed(fixture_cls.tables):
                print(f"DELETE FROM {table};  -- {unit.path.name}")
        else:
            print(f"-- {unit.path.name} : aucune table déclarée, non purgé automatiquement")
    for statement in statements:
        print(f"{statement};")
    print()

    if not run:
        print("Affichage seul. Relancez avec --run pour exécuter (charte §7).")
        return 0

    from core.database import db

    purged_callables = 0
    for unit in teardown:
        fixture_cls = unit.fixture
        if fixture_cls is None:
            continue
        try:
            fixture_cls().purge()
        except Exception as exc:  # noqa: BLE001 — on rapporte la cause précise
            print(
                f"Erreur en démontant la fixture {unit.path.name} : {exc}",
                file=sys.stderr,
            )
            return 1
        purged_callables += 1

    for statement in statements:
        try:
            db.execute(statement)
        except Exception as exc:  # noqa: BLE001 — on rapporte la cause précise
            print(
                f"Erreur en purgeant : {exc}\nInstruction : {statement}",
                file=sys.stderr,
            )
            return 1

    suffix = (
        f" et {purged_callables} fixture(s) Python démontée(s)" if purged_callables else ""
    )
    print(
        f"{STATUS_OK} {len(statements)} table(s) vidée(s){suffix} "
        f"dans l'environnement '{env}'."
    )
    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge fixtures:purge``."""
    argv = list(args or [])
    run = "--run" in argv
    force = "--force" in argv
    return purge_fixtures(Path.cwd(), run=run, force=force, env=active_env())
