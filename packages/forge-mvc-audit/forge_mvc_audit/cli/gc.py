# pyright: strict
"""Commande ``forge audit:gc`` — purge du journal d'audit par âge (AUDIT-RETENTION-001).

`audit_log` grossit à chaque action tracée et rien ne la bornait : la table
était la seule des opt-ins adossés à la base à n'avoir aucune politique de
rétention, alors que `sessions:gc` avait posé le précédent.

À brancher sur un ordonnanceur externe, cron ou minuteur systemd. Forge ne
fournit pas de planificateur, cette commande est le point d'entrée à
déclencher, comme `sessions:gc`.

## Pourquoi elle affiche avant d'effacer

`sessions:gc` supprime directement, et c'est justifié : une session expirée
n'est plus rien pour personne, son expiration est portée par la ligne
elle-même. Une entrée d'audit, au contraire, est un enregistrement délibéré,
souvent conservé pour rendre des comptes, et aucune date ne dit d'elle-même
qu'elle a cessé de valoir.

La commande **affiche** donc le nombre de lignes visées par défaut et n'efface
qu'avec ``--run``, motif déjà suivi par `fixtures:purge` et `db:init`
(charte §7, ADR-067). La rétention doit par ailleurs être **dite**, aucune
valeur par défaut n'étant supposée à la place de l'exploitant.
"""
from __future__ import annotations

import os
import sys

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"

#: Variable d'environnement portant la rétention, en jours.
ENV_KEEP_DAYS = "AUDIT_KEEP_DAYS"

__all__ = ["STATUS_OK", "STATUS_INFO", "STATUS_ERROR", "ENV_KEEP_DAYS", "resolve_keep_days", "main"]

_AIDE = (
    "Indiquez la rétention, en jours, par --days N ou par la variable "
    f"d'environnement {ENV_KEEP_DAYS}.\n"
    "  forge audit:gc --days 90          # affiche ce qui serait supprimé\n"
    "  forge audit:gc --days 90 --run    # supprime"
)


def resolve_keep_days(argv: list[str], env: "dict[str, str] | None" = None) -> "int | str":
    """Rétention retenue, ou un message d'erreur si elle est absente ou illisible.

    L'argument l'emporte sur l'environnement : une valeur tapée à la main dit
    une intention plus précise qu'une valeur héritée du déploiement.
    Retourne un `int` en cas de succès, un `str` décrivant le problème sinon,
    de sorte que l'appelant décide seul du code de sortie et du flux de sortie.
    """
    variables = os.environ if env is None else env

    brut: str | None = None
    for index, argument in enumerate(argv):
        if argument.startswith("--days="):
            brut = argument.partition("=")[2]
            break
        if argument == "--days":
            if index + 1 >= len(argv):
                return "L'option --days attend un nombre de jours."
            brut = argv[index + 1]
            break
    if brut is None:
        brut = variables.get(ENV_KEEP_DAYS)
    if brut is None or not brut.strip():
        return "Aucune rétention indiquée."

    try:
        jours = int(brut.strip())
    except ValueError:
        return f"Rétention illisible : {brut!r}. Un nombre entier de jours est attendu."
    if jours < 1:
        return (
            f"Rétention invalide : {jours}. "
            "Une rétention nulle ou négative viderait tout le journal."
        )
    return jours


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge audit:gc``."""
    from forge_mvc_audit.store import (
        count_audit_before,
        cutoff_for_days,
        purge_audit_before,
    )

    argv = list(args or [])
    jours = resolve_keep_days(argv)
    if isinstance(jours, str):
        print(f"{STATUS_ERROR} {jours}\n{_AIDE}", file=sys.stderr)
        return 1

    borne = cutoff_for_days(jours)
    vises = count_audit_before(borne)

    if "--run" not in argv:
        print(
            f"{STATUS_INFO} {vises} entrée(s) d'audit antérieure(s) au {borne} UTC "
            f"(rétention de {jours} jour(s)).\n"
            f"{STATUS_INFO} Rien n'a été supprimé. Relancez avec --run pour exécuter."
        )
        return 0

    supprimees = purge_audit_before(borne)
    print(
        f"{STATUS_OK} {supprimees} entrée(s) d'audit purgée(s), "
        f"antérieures au {borne} UTC (rétention de {jours} jour(s))."
    )
    return 0
