# pyright: strict
"""Commande ``forge fixtures:snapshot`` (`FIXTURES-SNAPSHOT-001`).

Rend l'état courant d'une table en `INSERT` relisibles, à ranger dans
`mvc/fixtures/`.

Affiche par défaut, écrit sur `--out`, et n'écrase jamais un fichier existant
(charte §7). Refuse en production sans `--force` : la sortie vient d'une base
réelle et finit dans un dépôt Git, où elle ne s'efface plus.
"""
from __future__ import annotations

import sys
from pathlib import Path

from core.app.env import is_prod, read_app_env

from forge_mvc_fixtures.snapshot import (
    DEFAULT_LIMIT,
    SnapshotError,
    render_snapshot,
    snapshot_table,
)

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"

__all__ = ["STATUS_OK", "STATUS_INFO", "STATUS_ERROR", "parse_options", "main"]


class _Options:
    def __init__(self) -> None:
        self.table: "str | None" = None
        self.limit = DEFAULT_LIMIT
        self.order_by: "str | None" = None
        self.out: "Path | None" = None
        self.force = False
        self.error: "str | None" = None


def _valeur(argv: list[str], index: int, argument: str) -> "tuple[str | None, int]":
    if "=" in argument:
        return argument.partition("=")[2], index
    if index + 1 >= len(argv):
        return None, index
    return argv[index + 1], index + 1


def parse_options(argv: list[str]) -> _Options:
    """Lit les arguments. Un argument inconnu est une erreur, jamais un silence."""
    options = _Options()
    positionnels: list[str] = []
    index = 0
    while index < len(argv):
        argument = argv[index]
        nom = argument.partition("=")[0]
        if nom in {"--limit", "--order-by", "--out"}:
            valeur, index = _valeur(argv, index, argument)
            if valeur is None or not valeur.strip():
                options.error = f"L'option {nom} attend une valeur."
                return options
            if nom == "--limit":
                try:
                    options.limit = int(valeur)
                except ValueError:
                    options.error = f"L'option --limit attend un entier. Reçu : {valeur!r}."
                    return options
            elif nom == "--order-by":
                options.order_by = valeur.strip()
            else:
                options.out = Path(valeur.strip())
        elif argument == "--force":
            options.force = True
        elif argument.startswith("-"):
            options.error = f"Option inconnue : {argument!r}."
            return options
        else:
            positionnels.append(argument)
        index += 1

    if len(positionnels) != 1:
        options.error = (
            "Usage : forge fixtures:snapshot TABLE [--limit N] [--order-by COL] "
            "[--out CHEMIN]"
        )
        return options
    options.table = positionnels[0]
    return options


def main(args: "list[str] | None" = None) -> int:
    options = parse_options(list(args or []))
    if options.error:
        print(f"{STATUS_ERROR} {options.error}", file=sys.stderr)
        return 1

    env = read_app_env()
    if is_prod(env) and not options.force:
        print(
            f"{STATUS_ERROR} Refus : instantané en environnement '{env}'. "
            "La sortie vient d'une base réelle et peut contenir des données "
            "personnelles. Ajoutez --force pour confirmer explicitement.",
            file=sys.stderr,
        )
        return 2

    assert options.table is not None
    try:
        from core.database.backend import get_backend

        dialecte = get_backend().dialect
        instantane = snapshot_table(
            options.table, limit=options.limit, order_by=options.order_by
        )
    except SnapshotError as exc:
        print(f"{STATUS_ERROR} {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - toute erreur de lecture est rapportée
        print(f"{STATUS_ERROR} Lecture impossible : {exc}", file=sys.stderr)
        return 1

    contenu = render_snapshot(instantane, dialecte)

    if options.out is None:
        print(contenu)
        print(
            f"{STATUS_INFO} Affichage seul. Ajoutez --out mvc/fixtures/xx.sql "
            "pour écrire (charte §7)."
        )
        return 0

    if options.out.exists():
        print(
            f"{STATUS_ERROR} Le fichier existe déjà : {options.out}. "
            "Forge n'écrase jamais un fichier applicatif (charte §9).",
            file=sys.stderr,
        )
        return 1

    options.out.parent.mkdir(parents=True, exist_ok=True)
    options.out.write_text(contenu, encoding="utf-8")
    print(f"{STATUS_OK} Écrit : {options.out} ({len(instantane.rows)} ligne(s))")
    if instantane.truncated:
        print(
            f"{STATUS_INFO} Instantané tronqué au plafond de {options.limit} "
            "lignes. Une fixture est une amorce, pas une sauvegarde."
        )
    print(
        f"{STATUS_INFO} RELISEZ ce fichier avant de le versionner : il vient "
        "d'une base réelle."
    )
    return 0
