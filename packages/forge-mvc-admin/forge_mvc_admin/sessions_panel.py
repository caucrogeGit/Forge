# pyright: strict
"""Panneau « sessions actives » du back-office (`ADMIN-SESSIONS-VIEW-001`).

`forge-mvc-sessions-db` compte les sessions, réparties par nature, et sait dire
si la purge suit. Personne ne regardait ce nombre : il fallait ouvrir un client
SQL, ou lire `forge sessions:gc` en aveugle.

## Le couplage est souple, comme pour le workflow et RBAC

`forge-mvc-admin` ne déclare pas `forge-mvc-sessions-db` en dépendance, et un
projet qui garde ses sessions en mémoire n'a pas à l'installer pour ouvrir son
back-office. L'import est donc paresseux, et son absence rend un panneau qui
**dit pourquoi il est vide** plutôt qu'une page en erreur.

## Aucun identifiant de session n'est affiché, et il n'y en a pas à afficher

La métrique rend des **agrégats**. C'est heureux : une liste de sessions montre
des identifiants, et un identifiant de session lu sur un écran, une capture ou
une épaule est une session volée. Le panneau ne pourrait donc pas en afficher,
même si on le voulait.

## Ce qu'il ne fait pas

Il ne révoque rien. Fermer une session depuis cet écran demanderait de désigner
laquelle, donc de l'identifier, donc de l'exposer. Fermer *toutes* celles d'un
utilisateur est possible sans cela, `delete_for_user` existe, mais c'est un
geste destructeur qui mérite sa page de confirmation et sa décision propre.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["SessionsPanel", "sessions_panel", "PURGE_ALERT_RATIO"]

#: Au delà de cette part de lignes mortes, la purge est annoncée en retard.
#: `SessionMetrics.purge_backlog_ratio` documente le même seuil : la table coûte
#: alors deux fois ce qu'elle devrait à chaque balayage.
PURGE_ALERT_RATIO = 0.5


@dataclass(frozen=True)
class SessionsPanel:
    """Ce que la page affiche, et rien de plus.

    `indisponible` porte le motif quand le panneau ne peut pas répondre. Rendre
    des zéros dans ce cas ferait lire « aucune session » là où la vraie réponse
    est « je ne sais pas », et les deux ne se corrigent pas au même endroit.
    """

    disponible: bool
    indisponible: str = ""
    actives: int = 0
    expirees: int = 0
    total: int = 0
    par_nature: "tuple[tuple[str, int], ...]" = ()
    part_a_purger: float = 0.0

    @property
    def purge_en_retard(self) -> bool:
        """La purge suit elle ?

        C'est la question que cette page existe pour répondre : une table qui
        grossit pendant que le nombre d'actives stagne signale un minuteur
        `sessions:gc` qui ne tourne pas.
        """
        return self.disponible and self.part_a_purger > PURGE_ALERT_RATIO


def sessions_panel(*, db: Any = None) -> SessionsPanel:
    """Photographie du magasin de sessions, ou le motif de son absence."""
    try:
        from forge_mvc_sessions_db import session_metrics  # type: ignore[import-not-found]
    except ImportError:
        return SessionsPanel(
            disponible=False,
            indisponible=(
                "L'opt-in forge-mvc-sessions-db n'est pas installé "
                "(pip install forge-mvc-sessions-db). Un projet dont les "
                "sessions vivent en mémoire n'a pas de table à compter."
            ),
        )

    try:
        mesures = session_metrics(db=db)
    except Exception as exc:  # noqa: BLE001 — le motif remonte à l'écran
        # Une table absente, un backend non configuré : le back-office doit
        # rester ouvert. Une page d'administration qui tombe parce qu'un
        # panneau ne répond pas retire l'accès à tout le reste.
        return SessionsPanel(
            disponible=False,
            indisponible=(
                f"Les sessions ne sont pas lisibles : {exc}. La table se "
                f"provisionne par forge sessions:init puis forge migration:apply."
            ),
        )

    return SessionsPanel(
        disponible=True,
        actives=mesures.active,
        expirees=mesures.expired,
        total=mesures.total,
        par_nature=tuple(sorted(mesures.by_kind.items())),
        part_a_purger=mesures.purge_backlog_ratio,
    )
