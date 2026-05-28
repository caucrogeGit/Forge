"""Repository d'insertion des événements IoT — IOT-STORAGE-REPOSITORY-001.

Premier branchement réel entre le contrat de stockage (``events.py``)
et la base de données Forge (``core.database.db``).

Le repository :

- prend une ``Measurement`` produite par le subscriber MQTT ;
- réutilise ``build_insert_iot_event_sql`` pour produire le SQL et les
  paramètres ;
- délègue l'exécution à un *adapter* injectable (par défaut
  ``core.database.db``, qui gère lui-même commit/rollback) ;
- ne **crée pas** la table — la migration ``iot_events`` doit avoir
  été appliquée au préalable.

Le ticket reste strictement scoped insertion : ni API HTTP, ni
déduplication, ni rétention, ni intégration automatique au subscriber.

Note sur la dépendance : c'est le premier endroit où
``forge-mvc-iot`` importe ``core.database``. C'est acceptable car le
sens des dépendances reste correct : ``forge-mvc-iot`` dépend de
``forge-mvc``, jamais l'inverse.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from forge_mvc_iot.mqtt.contract import Measurement
from forge_mvc_iot.storage.events import build_insert_iot_event_sql

__all__ = [
    "DbAdapter",
    "IotEventRepository",
]


class DbAdapter(Protocol):
    """Interface minimale attendue par ``IotEventRepository``.

    Conforme au module ``core.database.db`` de Forge : on attend une
    fonction/méthode ``execute(sql, params)`` qui exécute la requête et
    s'occupe de commit/rollback.
    """

    def execute(self, sql: str, params: tuple) -> Any:  # pragma: no cover - protocole
        ...


def _default_db_adapter() -> Any:
    """Importe paresseusement le module ``core.database.db`` de Forge.

    L'import est différé jusqu'à la construction du repository sans
    adapter explicite. ``core.database.db`` ne déclenche aucune
    connexion réseau à l'import (lazy pool — voir
    ``core/database/connection.py``), donc cet import reste sans effet
    de bord. Les tests qui injectent un adapter explicite n'ont jamais
    besoin de ``core.database``.
    """
    from core.database import db  # noqa: PLC0415

    return db


class IotEventRepository:
    """Insère les ``Measurement`` Forge IoT dans la table ``iot_events``.

    Parameters
    ----------
    db_adapter:
        Objet exposant ``execute(sql, params)``. Par défaut, le module
        ``core.database.db`` de Forge — qui gère le pool de connexions,
        le commit et le rollback automatiquement.

    Notes
    -----
    - Le repository ne crée pas la table ``iot_events``. La migration
      ``IOT-STORAGE-MIGRATION-001`` doit avoir été appliquée au
      préalable.
    - Les erreurs SQL sont propagées telles quelles : le repository
      n'intercepte rien silencieusement.
    - Le commit/rollback est délégué à l'adapter (par défaut, Forge
      gère ça dans ``db.execute``). Le repository n'effectue aucun
      `commit` ou `rollback` manuel.
    """

    def __init__(self, db_adapter: Any | None = None) -> None:
        if db_adapter is None:
            db_adapter = _default_db_adapter()
        self._db = db_adapter

    def insert(
        self,
        measurement: Measurement,
        *,
        received_at: datetime | None = None,
    ) -> Any:
        """Insère une mesure dans ``iot_events``.

        Parameters
        ----------
        measurement:
            Mesure validée par ``forge_mvc_iot.mqtt.contract.parse_message``.
        received_at:
            Horodatage serveur. Si ``None``, ``datetime.now(UTC)`` est
            utilisé par la sérialisation.

        Returns
        -------
        Retour brut de ``db_adapter.execute(sql, params)``. Avec
        ``core.database.db.execute``, c'est ``rowcount`` (int). Un
        adapter personnalisé peut décider de retourner autre chose
        (par exemple ``lastrowid`` en wrappant ``db.insert``).
        """
        sql, params = build_insert_iot_event_sql(
            measurement, received_at=received_at,
        )
        return self._db.execute(sql, params)
