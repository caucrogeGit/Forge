# pyright: strict
"""Journaliser les refus d'accès de `forge-mvc-rbac` (AUDIT-RBAC-DENIALS-BRIDGE-001).

`forge-mvc-rbac` annonce ses refus à qui veut les entendre, et sa documentation
donnait la recette du branchement en une ligne :

    on_permission_denied(lambda refus: record_audit(
        "acces.refuse", actor=refus.actor, details=refus.permission,
    ))

Elle marche, et elle perd trois choses sur cinq. `path` et `method` disent
**ce qui** a été tenté, et `source` nomme la garde qui a refusé, distinction que
`DenialEvent` déclare décisive : un refus contractuel et un refus de permissions
chargées en base ne se corrigent pas au même endroit. Un journal qui les jette
répond « quelqu'un a été refusé » et rien de plus, ce qui ne sert ni à voir une
énumération de droits, ni à corriger une permission mal attribuée.

Ce module livre le branchement complet, et une seule fois : le brancher deux
fois doublerait chaque ligne, et compter les refus donnerait alors le double.

## La dépendance ne va que dans un sens

`forge-mvc-rbac` n'importe rien d'ici, et l'import de `forge_mvc_rbac` est
différé jusqu'à l'appel. Un projet qui a l'audit sans le RBAC n'en paie donc
rien, et celui qui appelle le branchement sans avoir le RBAC l'apprend au
câblage plutôt qu'au premier refus.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from forge_mvc_audit.errors import AuditError

__all__ = [
    "DENIAL_ACTION",
    "DENIAL_TARGET_TYPE",
    "audit_permission_denials",
    "denial_details",
    "permission_denials_audited",
    "reset_denial_bridge",
]

logger = logging.getLogger(__name__)

#: Verbe porté par les lignes de refus. Fixé ici pour que la relecture d'un
#: journal soit une requête et non une recherche de texte.
DENIAL_ACTION = "acces.refuse"

#: Nature de la cible d'un refus. La permission tient dans `target_id`, ce qui
#: rend `get_audit_log(target_type="permission")` suffisant pour tous les lister.
DENIAL_TARGET_TYPE = "permission"

#: Observateur posé, ou `None`. Sert l'idempotence et la lecture de l'état.
_observateur: "Callable[[Any], None] | None" = None


def permission_denials_audited() -> bool:
    """Vrai si le branchement est en place dans ce processus."""
    return _observateur is not None


def denial_details(event: Any) -> str:
    """Texte d'une ligne de refus : ce qui a été tenté, et par quelle garde.

    Rendu séparément pour qu'un projet qui préfère son propre observateur garde
    le même format, plutôt que d'en réinventer un moins complet.

    Un attribut absent est **omis** et non rendu « None » : les doubles de test
    et les requêtes réduites n'en portent pas tous, et un journal ne doit pas
    afficher le mot None là où il n'y avait rien.
    """
    methode = getattr(event, "method", None)
    chemin = getattr(event, "path", None)
    source = getattr(event, "source", "") or ""

    tentative = " ".join(str(p) for p in (methode, chemin) if p)
    if source:
        return f"{tentative} (garde : {source})".strip()
    return tentative


def audit_permission_denials(
    *, action: str = DENIAL_ACTION, db: Any = None
) -> "Callable[[Any], None]":
    """Branche le journal d'audit sur les refus d'accès, et rend l'observateur.

    À appeler une fois au câblage de l'application. Rien n'est journalisé tant
    que ce branchement n'a pas été demandé, `forge-mvc-rbac` laissant le choix
    du destinataire.

    Le second appel ne rebranche pas : il rend l'observateur déjà posé. Deux
    branchements écriraient deux lignes par refus, et un compte de refus
    donnerait le double sans que rien ne le signale.

    Args:
        action: verbe des lignes engendrées, si le projet nomme ses actions
            autrement.
        db: exécuteur injecté, comme pour `record_audit`. Laissé à `None`, la
            base du projet est employée.

    Raises:
        AuditError: `forge-mvc-rbac` n'est pas installé. L'erreur tombe au
            câblage, moment où elle se corrige, et non au premier refus, où
            elle serait avalée par l'isolation des observateurs.
    """
    global _observateur  # noqa: PLW0603 — un processus, un branchement

    if _observateur is not None:
        return _observateur

    try:
        from forge_mvc_rbac import on_permission_denied
    except ImportError as exc:
        raise AuditError(
            "Journaliser les refus d'accès demande forge-mvc-rbac, qui n'est "
            "pas installé. Installez-le, ou retirez cet appel."
        ) from exc

    from forge_mvc_audit.store import record_audit

    def _journaliser(event: Any) -> None:
        record_audit(
            action,
            actor=getattr(event, "actor", None),
            target_type=DENIAL_TARGET_TYPE,
            target_id=getattr(event, "permission", None),
            details=denial_details(event) or None,
            db=db,
        )

    on_permission_denied(_journaliser)
    _observateur = _journaliser
    logger.info("Refus d'accès RBAC journalisés dans l'audit (action %r).", action)
    return _journaliser


def reset_denial_bridge() -> None:
    """Oublie le branchement posé, pour pouvoir le reposer.

    Publique comme l'est `clear_denial_observers` côté `forge-mvc-rbac`, et
    pour la même raison : sans elle, un test qui branche rendrait tous les
    suivants dépendants de son ordre d'exécution.

    Sans cela, un test qui branche rendrait tous les suivants dépendants de son
    ordre d'exécution. Retirer l'observateur de `forge-mvc-rbac` reste à la
    charge de l'appelant, `clear_denial_observers` étant sa porte.
    """
    global _observateur  # noqa: PLW0603
    _observateur = None
