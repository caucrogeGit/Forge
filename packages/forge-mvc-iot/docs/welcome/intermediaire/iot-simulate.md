# Simuler une mesure IoT

Objectif : **alimenter** la base d'événements sans capteur ni broker, pour travailler en local.

**Ce que vous allez apprendre :** composer une mesure, la **valider contre le contrat IoT** (`build_payload` + `parse_message`) puis l'insérer dans `iot_events` via `IotEventRepository.insert`.
C'est exactement la validation que le subscriber MQTT applique en production : on emprunte simplement un autre chemin d'entrée, **sans broker**.

Premier palier du **niveau intermédiaire** de la progression IoT, après le [niveau débutant](../debutant/bilan.md).

## Ce que ce starter montre

- un formulaire qui compose une mesure (site, capteur, type, valeur, unité) ;
- la construction d'un payload **conforme au contrat** (`build_payload`) ;
- la validation `parse_message` (topic + payload → `Measurement`) ;
- l'insertion via `IotEventRepository.insert` ;
- la boucle complète : **injecter** puis **relire** la liste, en local.

La table `iot_events` est créée par la migration livrée avec le starter.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `build_topic` / `build_payload` | Composer un topic et un payload conformes. | [Forge IoT : simulateur](../../listen-command.md) |
| `parse_message` | Valider topic + payload → `Measurement`. | [Forge IoT : contrat](../../storage-events.md) |
| `IotEventRepository.insert` | Écrire la mesure validée dans `iot_events`. | [Forge IoT : stockage](../../storage-events.md) |
| `BaseController.csrf_token` / `redirect` | Protéger le POST, rediriger (PRG). | BaseController |

## Tester

```bash
forge db:init
forge run
```

Ouvrez `https://localhost:8000/iot-simulate`, ajustez les champs et cliquez **Injecter la mesure** : elle apparaît dans la liste des derniers événements.
Vous venez d'alimenter `iot_events` **sans broker**.

## Le contrôleur

Créez le fichier ci-dessous, complet et copiable tel quel.

```python
# mvc/controllers/iot_simulate_controller.py
import json

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.cli.simulate import build_payload, build_topic, utc_timestamp
from forge_mvc_iot.mqtt.contract import ContractError, parse_message
from forge_mvc_iot.storage import IotEventRepository


class IotSimulateController(BaseController):
    """Starter pédagogique : injecter une mesure simulée, validée, sans broker."""

    @staticmethod
    def index(request: Request) -> Response:
        return IotSimulateController._page(request)

    @staticmethod
    def simulate(request: Request) -> Response:
        site = (request.form("site") or "atelier").strip()
        device_id = (request.form("device_id") or "capteur-1").strip()
        kind = (request.form("kind") or "temperature").strip()
        unit = (request.form("unit") or "C").strip()
        raw_value = (request.form("value") or "").strip()
        try:
            value = float(raw_value)
        except ValueError:
            return IotSimulateController._page(
                request, error="La valeur doit être un nombre."
            )
        try:
            topic = build_topic(site, device_id)
            payload = build_payload(
                kind=kind, value=value, unit=unit, timestamp=utc_timestamp()
            )
            measurement = parse_message(topic, json.dumps(payload))
            IotEventRepository().insert(measurement)
        except ContractError as exc:
            return IotSimulateController._page(request, error=str(exc))
        return BaseController.redirect("/iot-simulate")

    @staticmethod
    def _page(request: Request, error: str | None = None) -> Response:
        try:
            events = IotEventRepository().list_recent(limit=20)
        except Exception:
            events = []
        context = {
            "events": events,
            "csrf_token": BaseController.csrf_token(request),
        }
        if error:
            context["error"] = error
        return BaseController.render(
            "iot_simulate/index.html", context=context, request=request
        )
```

### Comprendre ce code

- `build_payload(...)` produit un payload **conforme** (champs `kind`, `value`, `unit`, `timestamp`).
  `parse_message` le **valide** et renvoie un `Measurement` typé ; une `ContractError` est levée si quelque chose ne respecte pas le contrat.
- `IotEventRepository().insert(measurement)` écrit la mesure validée.
  C'est le **même** repository qu'en lecture.
- En production, ce `Measurement` viendrait du broker via le subscriber ; ici, il vient du formulaire.
  Le reste du chemin est identique.

## La vue

Créez le gabarit ci-dessous : il porte le formulaire et la liste des derniers événements.

```html
<!-- mvc/views/iot_simulate/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Simuler une mesure IoT - Forge</title>
</head>
<body>
  <h1>Simuler une mesure IoT</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}

  <form method="post" action="/iot-simulate">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <label>Site <input type="text" name="site" value="atelier"></label>
    <label>Capteur <input type="text" name="device_id" value="capteur-1"></label>
    <label>Type <input type="text" name="kind" value="temperature"></label>
    <label>Valeur <input type="text" name="value" value="21.5"></label>
    <label>Unité <input type="text" name="unit" value="C"></label>
    <button type="submit">Injecter la mesure</button>
  </form>

  <h2>Derniers événements</h2>
  {% if events %}
  <ul>
    {% for e in events %}
    <li>{{ e.site }}/{{ e.device_id }} - {{ e.kind }} = {{ e.value }} {{ e.unit }}</li>
    {% endfor %}
  </ul>
  {% else %}
  <p>Aucun événement pour l'instant.</p>
  {% endif %}
</body>
</html>
```

## La route

Déclarez les deux routes (`GET` pour la page, `POST` pour l'injection) dans `mvc/routes.py`, à l'intérieur du groupe public.

```python
# mvc/routes.py
from mvc.controllers.iot_simulate_controller import IotSimulateController

with router.group("", public=True) as public:
    public.add("GET", "/iot-simulate", IotSimulateController.index, name="iot_simulate_index")
    public.add("POST", "/iot-simulate", IotSimulateController.simulate, name="iot_simulate_store")
```

## La migration

La simulation a besoin de la table `iot_events`.
Créez le fichier de migration ci-dessous (le nom commence par un horodatage), puis appliquez-le avec `forge db:init`.

```sql
-- mvc/migrations/20260601170000_create_iot_events.sql
CREATE TABLE IF NOT EXISTS iot_events (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    site          VARCHAR(64)     NOT NULL,
    device_id     VARCHAR(64)     NOT NULL,
    kind          VARCHAR(64)     NOT NULL,
    value         DOUBLE          NOT NULL,
    unit          VARCHAR(32)     NOT NULL,
    timestamp     VARCHAR(40)     NOT NULL,
    metadata_json TEXT            NULL,
    received_at   DATETIME(6)     NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_iot_events_site_device (site, device_id),
    INDEX idx_iot_events_received_at (received_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

`CREATE TABLE IF NOT EXISTS` rend la migration idempotente : elle est sûre même si un autre palier a déjà créé la table.

## À retenir

- On peut alimenter `iot_events` **sans broker**, via le contrat IoT.
- `parse_message` valide la mesure exactement comme en production.
- `IotEventRepository.insert` écrit ; `list_recent` relit : la boucle est bouclée en local.

## Après ce starter

Vous savez alimenter les données en local. La suite : exposer l'API HTTP JSON officielle.

[Exposer l'API IoT](iot-api.md)
