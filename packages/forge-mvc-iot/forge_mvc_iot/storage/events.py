"""Contrat SQL des événements IoT — IOT-STORAGE-EVENTS-001.

Module **pur** : ne se connecte à aucune base de données, n'applique
aucune migration. Fournit :

- la table cible et l'ordre canonique des colonnes ;
- une fonction de sérialisation d'une ``Measurement`` en dict prêt
  pour insertion SQL ;
- un constructeur de requête ``INSERT`` paramétrée avec ses paramètres.

L'insertion réelle est traitée par ``IOT-STORAGE-REPOSITORY-001`` ;
la migration versionnée par ``IOT-STORAGE-MIGRATION-001``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from forge_mvc_iot.mqtt.contract import Measurement

__all__ = [
    "TABLE_NAME",
    "COLUMNS",
    "INSERT_IOT_EVENT_SQL",
    "serialize_measurement_for_storage",
    "build_insert_iot_event_sql",
]


TABLE_NAME = "iot_events"

# Ordre canonique des colonnes utilisé pour la sérialisation et le
# placeholder positionnel `?`. La colonne `id` est exclue car générée
# par la base (BIGINT UNSIGNED AUTO_INCREMENT).
COLUMNS: tuple[str, ...] = (
    "site",
    "device_id",
    "kind",
    "value",
    "unit",
    "timestamp",
    "metadata_json",
    "received_at",
)


# Requête SQL exposée explicitement — Forge garde le SQL visible
# (charte v2 §5). Utilise les placeholders qmark `?` attendus par le
# connecteur MariaDB natif de Forge.
INSERT_IOT_EVENT_SQL = (
    f"INSERT INTO {TABLE_NAME} "
    f"({', '.join(COLUMNS)}) "
    f"VALUES ({', '.join('?' for _ in COLUMNS)})"
)


def serialize_measurement_for_storage(
    measurement: Measurement,
    *,
    received_at: datetime | None = None,
) -> dict[str, object]:
    """Sérialise une ``Measurement`` en dict prêt pour insertion SQL.

    Parameters
    ----------
    measurement:
        Mesure validée et parsée par ``forge_mvc_iot.mqtt.contract``.
    received_at:
        Horodatage côté serveur (réception par le subscriber). Si
        ``None``, ``datetime.now(UTC)`` est utilisé. Toujours en UTC :
        on évite tout fuseau implicite côté stockage.

    Notes
    -----
    - ``metadata`` est sérialisé en JSON string (``metadata_json``) ;
      ``None`` si la mesure n'a pas de métadonnées.
    - ``timestamp`` reste la chaîne ISO 8601 UTC reçue dans le payload —
      la conversion en ``DATETIME`` est laissée au schéma SQL ou au
      consommateur.
    - L'ordre des clés du dict retourné n'est pas garanti — utiliser
      ``COLUMNS`` pour produire un tuple positionnel ordonné.
    """
    if received_at is None:
        received_at = datetime.now(UTC)

    metadata_json: str | None
    if measurement.metadata is None:
        metadata_json = None
    else:
        # sort_keys + ensure_ascii=False : sortie déterministe et
        # compatible UTF-8 (les valeurs de metadata peuvent contenir
        # des accents).
        metadata_json = json.dumps(
            measurement.metadata,
            sort_keys=True,
            ensure_ascii=False,
        )

    return {
        "site": measurement.site,
        "device_id": measurement.device_id,
        "kind": measurement.kind,
        "value": measurement.value,
        "unit": measurement.unit,
        "timestamp": measurement.timestamp,
        "metadata_json": metadata_json,
        "received_at": received_at,
    }


def build_insert_iot_event_sql(
    measurement: Measurement,
    *,
    received_at: datetime | None = None,
) -> tuple[str, tuple]:
    """Construit la requête SQL d'insertion et son tuple de paramètres.

    Retourne ``(sql, params)`` directement consommable par le futur
    repository (``IOT-STORAGE-REPOSITORY-001``) :

    >>> sql, params = build_insert_iot_event_sql(measurement)
    >>> # Plus tard :
    >>> # from core.database.db import execute
    >>> # execute(sql, params)

    La requête utilise un placeholder ``?`` par colonne ; les valeurs
    suivent l'ordre de ``COLUMNS``.
    """
    serialized = serialize_measurement_for_storage(
        measurement, received_at=received_at,
    )
    params = tuple(serialized[col] for col in COLUMNS)
    return INSERT_IOT_EVENT_SQL, params
