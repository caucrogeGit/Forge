# pyright: strict
"""Refus de droit sur le levier de contraintes (FIXTURES-PG-FK-PRIVILEGE-001).

`fixtures:load --no-fk-checks` et `fixtures:purge` encadrent leur travail par le
levier du dialecte, `foreign_key_checks_ddl`. Sur PostgreSQL ce levier est
`SET session_replication_role`, qui **exige un rôle superutilisateur**, alors
que le compte applicatif d'un projet Forge n'en est pas un (ADR-033).

Avant ce module, le refus se rendait « Erreur en chargeant (chargement annulé) »
suivi du message du serveur, traduit selon sa langue. La commande échouait donc
proprement, mais rien ne disait qu'il s'agissait d'un droit, ni quoi faire.

Le module est partagé par les deux commandes, qui empruntent le même chemin.
Un correctif posé sur une seule d'entre elles n'aurait réparé qu'un jumeau, ce
que Forge a déjà payé ailleurs (`TWIN-ERROR-PAGE-PARITY-001`).
"""
from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import de typage seulement
    from core.database.transaction import Transaction


class PrivilegeRefuse(Exception):
    """Le serveur a refusé le levier de contraintes, faute de droit."""

    def __init__(self, instruction: str, cause: Exception) -> None:
        super().__init__(str(cause))
        self.instruction = instruction
        self.cause = cause


def executer_levier(
    db: ModuleType, instructions: list[str], tx: "Transaction"
) -> None:
    """Émet le levier de contraintes, en qualifiant un refus de droit.

    Toute autre erreur repart telle quelle : la stricture du prédicat veut que
    seul un refus reconnu soit présenté comme tel.
    """
    from core.database.backend import get_backend

    for instruction in instructions:
        try:
            db.execute(instruction, tx=tx)
        except Exception as exc:  # noqa: BLE001 — reclassée puis relancée
            if get_backend().is_insufficient_privilege_error(exc):
                raise PrivilegeRefuse(instruction, exc) from exc
            raise


def message_refus(refus: PrivilegeRefuse, *, commande: str) -> str:
    """Message rendu à l'exploitant, nommant le levier et les deux issues.

    Il nomme l'instruction refusée plutôt que de citer le texte du serveur comme
    cause : ce texte est traduit, donc il varie avec la langue du serveur.
    """
    return (
        f"{commande} : le serveur a refusé « {refus.instruction} », "
        "votre compte n'ayant pas ce droit.\n"
        "Sur PostgreSQL ce levier demande un rôle superutilisateur, que le "
        "compte applicatif d'un projet Forge n'est pas (ADR-033).\n"
        "Deux issues : ordonner les fixtures par leurs dépendances, ce que "
        "`fixtures:load` fait seul quand le jeu est triable, ou lancer le "
        "chargement avec un compte qui possède ce droit.\n"
        f"Réponse du serveur : {refus.cause}"
    )
