# API HTTP Forge IoT

> **Statut** : première API JSON de **lecture** des événements IoT.
> L'API d'ingestion (POST), l'authentification Bearer et le dashboard
> sont **hors périmètre** à ce ticket — voir
> [Architecture Forge IoT](architecture.md#tickets-suivants).

## Routes

| Méthode | URL | Repository |
|---------|-----|------------|
| `GET` | `/api/iot/events` | `IotEventRepository.list_recent` |
| `GET` | `/api/iot/events/{site}/{device_id}` | `IotEventRepository.find_by_device` |
| `GET` | `/api/iot/devices/{site}/{device_id}/count` | `IotEventRepository.count_by_device` |

Toutes les routes sont :

- `public=True` — pas d'authentification à ce ticket (la lecture des
  mesures est volontairement ouverte tant qu'un Bearer token n'est pas
  ajouté) ;
- `csrf=False` — méthodes GET, sans état modifié ;
- `api=True` — marquées comme routes API par Forge.

## Branchement explicite

Le module IoT reste **opt-in** : Forge Core n'enregistre rien
automatiquement. L'application déclare les routes elle-même depuis son
`mvc/routes.py` :

```python
# mvc/routes.py
from forge_mvc_iot import register_iot_routes

def setup_routes(router):
    register_iot_routes(router)
    # … vos autres routes …
```

`register_iot_routes` accepte un argument optionnel `repository=` pour
injecter une instance préconstruite (utile pour les tests ou pour
partager un repository entre plusieurs composants) :

```python
from forge_mvc_iot.storage import IotEventRepository
from forge_mvc_iot import register_iot_routes

repo = IotEventRepository()
register_iot_routes(router, repository=repo)
```

Si `repository` n'est pas fourni, un `IotEventRepository()` par défaut
est instancié (utilise `core.database.db` comme adapter).

## `GET /api/iot/events`

Retourne les **N derniers** événements toutes sources confondues,
ordre `received_at DESC`.

### Paramètres

| Paramètre | Défaut | Plage | Comportement hors plage |
|-----------|--------|-------|-------------------------|
| `?limit=` | `100` | `1..1000` | `400 invalid_limit` |

### Exemple

```bash
curl https://forge.example.com/api/iot/events?limit=2
```

```json
{
  "events": [
    {
      "id": 1,
      "site": "atelier",
      "device_id": "esp32-001",
      "kind": "temperature",
      "value": 22.4,
      "unit": "°C",
      "timestamp": "2026-05-28T10:00:00Z",
      "metadata": {"room": "atelier"},
      "received_at": "2026-05-28T10:00:05Z"
    },
    {
      "id": 2,
      "site": "atelier",
      "device_id": "esp32-001",
      "kind": "humidity",
      "value": 47,
      "unit": "%",
      "timestamp": "2026-05-28T10:00:05Z",
      "metadata": null,
      "received_at": "2026-05-28T10:00:10Z"
    }
  ]
}
```

## `GET /api/iot/events/{site}/{device_id}`

Retourne les événements d'un device précis, ordre `received_at DESC`.

```bash
curl https://forge.example.com/api/iot/events/atelier/esp32-001?limit=50
```

Format de réponse identique à `/api/iot/events` (clé `events`).

## `GET /api/iot/devices/{site}/{device_id}/count`

Retourne le nombre d'événements enregistrés pour un device.

```bash
curl https://forge.example.com/api/iot/devices/atelier/esp32-001/count
```

```json
{
  "site": "atelier",
  "device_id": "esp32-001",
  "count": 42
}
```

## Sérialisation `received_at`

Côté repository, `received_at` est un `datetime` Python. L'API le
convertit en chaîne ISO 8601 UTC avec suffixe `Z` :

| Entrée (repository) | Sortie JSON |
|---------------------|-------------|
| `datetime(2026, 5, 28, 10, 0, 5, tzinfo=UTC)` | `"2026-05-28T10:00:05Z"` |
| `datetime(2026, 5, 28, 12, 0, 5, tzinfo=+02:00)` (Paris) | `"2026-05-28T10:00:05Z"` (converti en UTC) |
| `datetime(2026, 5, 28, 10, 0, 5)` (naïf) | `"2026-05-28T10:00:05Z"` (assumé UTC) |

Tous les autres fuseaux sont **convertis en UTC** avant sérialisation —
la sortie n'expose jamais un offset autre que `Z`. C'est cohérent avec
le contrat MQTT, qui exige déjà `Z` côté payload.

## `metadata` et `metadata_json`

`metadata_json` est un détail **interne** de stockage. Il n'apparaît
jamais dans les réponses HTTP :

- `metadata` (objet ou `null`) est la seule clé exposée ;
- la conversion JSON ↔ dict est déjà faite côté repository ;
- même si un consommateur indiscipliné fait fuiter `metadata_json`
  dans son dict, le sérialiseur HTTP le supprime explicitement
  (vérifié par `test_metadata_json_key_never_present`).

## Format des erreurs

### Limit invalide — `400 Bad Request`

```json
{
  "error": "invalid_limit",
  "message": "limit doit être un entier (vu : 'abc')"
}
```

Cas couverts :

- non convertible en `int` (`?limit=abc`) ;
- nul ou négatif (`?limit=0`, `?limit=-1`) ;
- au-dessus de `MAX_LIMIT` (`?limit=1001`).

Le repository n'est pas appelé — la validation est purement côté
contrôleur.

### Erreur DB — `500 Internal Server Error`

```json
{"error": "internal_server_error"}
```

Réponse **sobre** : aucun message SQL, aucun stacktrace, aucun détail
qui pourrait fuiter de l'information. Le détail est logué côté serveur
sur le logger `forge_mvc_iot.http` (niveau `ERROR` via
`logger.exception`).

## Utilisation directe du contrôleur

Pour un usage avancé (composer une route personnalisée, ajouter un
middleware spécifique), `IotHttpController` est exposé :

```python
from forge_mvc_iot.http import IotHttpController
from forge_mvc_iot.storage import IotEventRepository

controller = IotHttpController(IotEventRepository())
router.add(
    "GET", "/custom/events", controller.list_events,
    name="custom_events_list",
    public=True, csrf=False, api=True,
)
```

## Hors périmètre de ce ticket

- pas d'authentification (Bearer token, session) ;
- pas de POST/ingestion HTTP — l'ingestion se fait par MQTT
  (subscriber) ;
- pas de pagination par offset (`?offset=`) ;
- pas de filtres temporels (`?since=`, `?until=`) ;
- pas d'agrégation (`avg`, `min`, `max` sur une fenêtre) ;
- pas de dashboard HTML, pas d'intégration Forge Design ;
- pas de downlink Forge → capteur.

Ces points feront chacun l'objet d'un ticket dédié.
