# pyright: strict
"""Export du journal d'audit (AUDIT-CSV-EXPORT-001).

Un journal d'audit se lit à l'écran, et s'exporte pour rendre des comptes. Deux
choses l'empêchaient.

`get_audit_log` rend des `AuditEntry`, quand un écrivain CSV attend des
dictionnaires : les deux ne se composaient pas, et chaque application
réinventait la conversion, avec son propre ordre de colonnes.

Surtout, `get_audit_log` **borne à mille entrées, en silence**. Un export
demandé sur cent mille lignes en rendait mille, sans rien dire. Pour un journal
qu'on exporte précisément parce qu'il fait foi, c'est le pire des défauts :
le fichier paraît complet.

## Ce module ne produit pas de CSV

Il rend des lignes, et `forge-mvc-import-export` les écrit. Aucun des deux
n'importe l'autre, et une application qui préfère du JSON ou un tableur passe
les mêmes lignes à son propre écrivain.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from forge_mvc_audit.errors import AuditError

__all__ = [
    "AUDIT_EXPORT_COLUMNS",
    "DEFAULT_BATCH_SIZE",
    "entry_to_row",
    "iter_audit_rows",
]

#: Colonnes de l'export, dans l'ordre. Figées ici pour que deux exports d'un
#: même journal se comparent, ce qu'un ordre laissé au hasard interdirait.
AUDIT_EXPORT_COLUMNS = (
    "id", "created_at", "actor", "action", "target_type", "target_id", "details",
)

#: Nombre d'entrées lues par aller-retour. Le journal peut être très grand, et
#: tout charger en mémoire pour l'écrire ligne à ligne serait absurde.
DEFAULT_BATCH_SIZE = 500


def entry_to_row(entry: Any) -> "dict[str, Any]":
    """Traduit une entrée d'audit en ligne exportable.

    Une valeur absente devient une chaîne vide et non `None` : dans un fichier
    destiné à être relu par un humain ou un tableur, `None` s'écrirait tel quel
    et se lirait comme une donnée.
    """
    return {
        colonne: ("" if getattr(entry, colonne, None) is None else getattr(entry, colonne))
        for colonne in AUDIT_EXPORT_COLUMNS
    }


def iter_audit_rows(
    *,
    actor: "str | None" = None,
    action: "str | None" = None,
    target_type: "str | None" = None,
    target_id: "str | int | None" = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    db: Any = None,
) -> "Iterator[dict[str, Any]]":
    """Parcourt **tout** le journal correspondant aux filtres, par lots.

    Contrairement à `get_audit_log`, aucune borne silencieuse : le parcours
    avance tant qu'il reste des entrées. C'est ce que demande un export, qui
    doit être complet ou ne pas exister.

    L'avance se fait par identifiant décroissant, et non par décalage. Un
    `OFFSET` sur une table qui reçoit des écritures pendant l'export sauterait
    ou répéterait des lignes, ce qui est exactement ce qu'un journal ne peut pas
    se permettre.

    Raises:
        AuditError: `batch_size` est nul ou négatif, ce qui ferait un parcours
            qui n'avance jamais.
    """
    if batch_size < 1:
        raise AuditError(f"batch_size doit être >= 1. Reçu : {batch_size}.")

    from forge_mvc_audit.store import get_audit_log

    avant: "int | None" = None
    while True:
        entrees = get_audit_log(
            limit=batch_size,
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            before_id=avant,
            db=db,
        )
        if not entrees:
            return
        for entree in entrees:
            yield entry_to_row(entree)
        avant = entrees[-1].id
