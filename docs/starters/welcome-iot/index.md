# Bonjour IoT

Premier contact avec **Forge IoT**, le module opt-in `forge-mvc-iot`.

Le starter affiche une page d'accueil texte, expose la configuration
IoT lue (mot de passe masqué), et donne deux endpoints de lecture des
événements `iot_events` — pédagogiques même quand la table n'existe
pas encore.

Identifiant : `welcome-iot` (alias `bonjour-iot` / `iot` / `15`).

## Ce que ce starter installe

- une route `/welcome-iot` (texte)
- une route `/welcome-iot/inspect` (JSON, mot de passe masqué)
- une route `/welcome-iot/events` (JSON, lecture si table prête)
- une route `/welcome-iot/device/{site}/{device_id}` (JSON)
- l'API HTTP IoT officielle, branchée via la couche **`optins/`** (voir
  [Branchement opt-in](#branchement-opt-in-optins))
- un contrôleur `WelcomeIotController` (4 méthodes)
- une couche `optins/` (registre explicite + branchement IoT local)
- aucune vue HTML
- aucune base de données requise pour la page d'accueil
- aucun broker MQTT lancé

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Reçue par chaque méthode, sert à lire `route_param`. | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Construire les réponses texte et JSON. | [Response](../../reference/http.md#4-response-reference) |
| `BaseController` | Classe parente du contrôleur. | [BaseController](../../reference/api.md#coremvccontroller) |
| `IotConfig` | Lue via `load_iot_config()` pour `inspect`. | [Configuration](../../iot/configuration.md) |
| `IotEventRepository` | Lit les événements pour `events` / `find_by_device`. | [Stockage des événements](../../iot/storage-events.md) |

## Avant de tester — `forge iot:doctor`

Avant de lancer l'application, exécuter le diagnostic statique :

```bash
forge iot:doctor
```

Quatre `[OK]` attendus (package, configuration, migration, API HTTP) et
deux `[SKIP]` informatifs (broker MQTT et base — non testés à ce
ticket). Si quelque chose ne passe pas, voir
[Diagnostic Forge IoT](../../iot/doctor.md).

## Tester dans le navigateur

| URL | Résultat |
|-----|----------|
| `http://localhost:8000/welcome-iot` | `Bonjour Forge IoT` |
| `http://localhost:8000/welcome-iot/inspect` | JSON de la configuration (password masqué) |
| `http://localhost:8000/welcome-iot/events` | JSON des derniers événements (ou message pédagogique) |
| `http://localhost:8000/welcome-iot/device/atelier/esp32-001` | JSON des événements d'un device |

L'API HTTP officielle est branchée en parallèle :

| URL | Repository appelé |
|-----|-------------------|
| `http://localhost:8000/api/iot/events` | `IotEventRepository.list_recent` |
| `http://localhost:8000/api/iot/events/{site}/{device_id}` | `IotEventRepository.find_by_device` |
| `http://localhost:8000/api/iot/devices/{site}/{device_id}/count` | `IotEventRepository.count_by_device` |

Voir [API HTTP Forge IoT](../../iot/http-api.md) pour le détail.

### Page d'accueil — `/welcome-iot`

Réponse texte simple :

```text
Bonjour Forge IoT
```

C'est le premier contact équivalent à `/welcome` du starter
[Bonjour Forge](../welcome/index.md), mais ciblé sur l'écosystème IoT.

### Inspection de la configuration — `/welcome-iot/inspect`

```json
{
  "mqtt_host": "localhost",
  "mqtt_port": 1883,
  "mqtt_topic": "forge/+/+/telemetry",
  "mqtt_client_id": "forge-iot",
  "mqtt_username": null,
  "mqtt_password": "***"
}
```

Le mot de passe est **toujours** affiché comme `"***"` quand il est
défini, et `null` sinon — jamais en clair. Mêmes valeurs par défaut
que [`load_iot_config()`](../../iot/configuration.md).

Pour changer la configuration, ajuster les variables `FORGE_IOT_MQTT_*`
dans `env/dev` (voir [Configuration Forge IoT](../../iot/configuration.md)).

### Lecture d'événements — `/welcome-iot/events`

Si la table `iot_events` est disponible :

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
      "metadata": null,
      "received_at": "2026-05-28T10:00:05+00:00"
    }
  ]
}
```

Sinon — table absente, base non configurée, etc. — réponse
**pédagogique** (HTTP 503) :

```json
{
  "error": "iot_storage_not_ready",
  "message": "La table iot_events n'est pas encore disponible. Applique la migration Forge IoT avant de lire les événements."
}
```

Pour activer le stockage :

```bash
forge iot:init          # copie la migration vers mvc/migrations/ (idempotent)
forge migration:apply   # crée la table iot_events en base
```

Voir [`forge iot:init`](../../iot/init-command.md) pour le détail.

### Lecture par device — `/welcome-iot/device/{site}/{device_id}`

```json
{
  "site": "atelier",
  "device_id": "esp32-001",
  "events": [...]
}
```

Même comportement de fallback `iot_storage_not_ready` si la table
n'est pas prête.

## Code essentiel

```python
# mvc/controllers/welcome_iot_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.config import load_iot_config
from forge_mvc_iot.storage import IotEventRepository


class WelcomeIotController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge IoT")

    @staticmethod
    def inspect(request: Request) -> Response:
        cfg = load_iot_config()
        return Response.json({
            "mqtt_host": cfg.mqtt_host,
            "mqtt_port": cfg.mqtt_port,
            "mqtt_topic": cfg.mqtt_topic,
            "mqtt_client_id": cfg.mqtt_client_id,
            "mqtt_username": cfg.mqtt_username,
            "mqtt_password": "***" if cfg.mqtt_password else None,
        })
    # ...
```

### Comprendre ce code

- Le contrôleur importe **explicitement** `forge_mvc_iot.config` et
  `forge_mvc_iot.storage` — le starter est opt-in, Forge Core n'embarque
  rien de cette dépendance.
- `inspect` reconstruit le dict de configuration en masquant le mot de
  passe — même politique que `IotConfig.__repr__` mais en JSON.
- `events` et `find_by_device` instancient un `IotEventRepository`
  fresh à chaque appel ; en cas d'erreur DB (table absente, connexion
  refusée), elles retournent un 503 lisible plutôt qu'une trace
  technique.
- Aucun subscriber MQTT n'est lancé par le starter — c'est de la
  **lecture seule** côté HTTP.

## Branchement opt-in (`optins/`)

`welcome-iot` est aussi l'**exemple de référence** de la convention
[structure des opt-ins](../../architecture/optins-project-structure.md) :
le paquet `forge-mvc-iot` reste distribué, et le projet le **branche
localement** via un dossier `optins/`, sans découverte automatique.

```text
optins/
├── __init__.py
├── registry.py          # register_optins(router) — registre explicite
└── iot/
    ├── __init__.py
    ├── routes.py        # register(router) -> register_iot_routes(router)
    ├── README.md        # mode d'emploi local court
    └── migrations/
        └── README.md
```

Le branchement est **explicite et lisible** — trois sauts, aucun magie :

```python
# mvc/routes.py
from optins.registry import register_optins

register_optins(router)
```

```python
# optins/registry.py
def register_optins(router):
    from optins.iot.routes import register as register_iot

    register_iot(router)
```

```python
# optins/iot/routes.py
from forge_mvc_iot import register_iot_routes

def register(router):
    register_iot_routes(router)   # /api/iot/events, etc.
```

Le code métier reste dans le paquet `forge-mvc-iot` ; `optins/iot/` ne
fait que le câblage. `optins/iot/README.md` reste court et renvoie vers
la [doc IoT officielle](../../iot/http-api.md) plutôt que de la dupliquer.

## À retenir

- Le starter fonctionne **sans broker**, **sans table**, **sans
  capteur**. La page `/welcome-iot` répond immédiatement.
- `inspect` est le bon endroit pour vérifier la configuration en
  un coup d'œil, sans craindre de fuiter le mot de passe.
- Les routes événements détectent et signalent gentiment l'absence de
  table — c'est le bon signal pédagogique « tu n'as pas encore
  appliqué la migration ».
- L'API officielle `/api/iot/...` est branchée en parallèle via la
  couche `optins/` (`register_optins(router)` → `optins/iot/routes.py` →
  `register_iot_routes(router)`) — même module, même repository, mais
  branchement explicite et localisé.

## Après ce starter

Pour aller plus loin avec Forge IoT :

- lancer un broker [Mosquitto local](../../iot/mosquitto-local.md) et
  publier des messages selon le
  [contrat MQTT](../../iot/mqtt-contract.md) — sans capteur, le
  [simulateur `forge iot:simulate`](../../iot/simulator.md) publie des
  mesures factices conformes au contrat ;
- ingérer les mesures en base avec [`forge iot:listen`](../../iot/listen-command.md),
  qui branche le [subscriber MQTT](../../iot/mqtt-subscriber.md) sur le
  repository ;
- consommer l'[API HTTP officielle](../../iot/http-api.md) depuis une
  interface de votre choix.

Parcours de test complet, une fois la table `iot_events` créée :

```bash
forge iot:doctor --mqtt                     # le broker répond ?
forge iot:listen                            # écouter et stocker (laisser tourner)
# … dans un autre terminal :
forge iot:simulate --count 3 --interval 1   # publier 3 mesures factices
curl http://localhost:8000/api/iot/events   # relire les mesures stockées
```

Pour un usage en classe (Bac Pro / BTS CIEL), voir
[Forge IoT pour Bac Pro / BTS CIEL](../../iot/bts-ciel.md) : flux
expliqué et activités prêtes à l'emploi.

[Architecture Forge IoT](../../iot/architecture.md) liste les tickets
restants (capteurs simulés, dashboard, downlink, …).
