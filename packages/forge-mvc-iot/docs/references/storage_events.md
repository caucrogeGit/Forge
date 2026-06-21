# Le contrat SQL des événements IoT dans Forge

Ce document décrit la sérialisation d'une mesure vers la table `iot_events`.

Le fichier de code correspondant est `forge_mvc_iot/storage/events.py`.

## 1. À quoi sert ce module ?

Une `Measurement` validée doit être traduite en SQL pour être stockée.
Ce module produit la **requête d'insertion** et ses paramètres, sans accéder à la base : il garde le SQL visible et testable.

## 2. L'API

| Fonction | Comportement |
|---|---|
| `serialize_measurement_for_storage(measurement, *, received_at=None)` | sérialise une `Measurement` en dict prêt pour insertion |
| `build_insert_iot_event_sql(measurement, *, received_at=None)` | construit la requête SQL d'insertion et son tuple de paramètres |

```python
from forge_mvc_iot.storage.events import build_insert_iot_event_sql

sql, params = build_insert_iot_event_sql(measurement)
db.execute(sql, params)
```

`received_at` permet de fixer l'horodatage de réception (utile en test) ; à défaut, l'heure courante est utilisée.

## 3. Contextes d'utilisation

- **Insertion** : le [repository](storage_repository.md) appelle ces fonctions.
- **Migration** : la structure de `iot_events` est documentée dans le guide de stockage.

## 4. Voir aussi

- [Le repository d'événements](storage_repository.md) : exécute l'insertion.
- [Le contrat MQTT](mqtt_contract.md) : produit la `Measurement` sérialisée.
- [Stockage des événements (guide)](../storage-events.md).
