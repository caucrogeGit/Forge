# Simuler une mesure IoT

Objectif : **alimenter** la base d'événements sans capteur ni broker, pour
travailler en local.

**Ce que vous allez apprendre :** composer une mesure, la **valider contre le
contrat IoT** (`build_payload` + `parse_message`) puis l'insérer dans
`iot_events` via `IotEventRepository.insert`. C'est exactement la validation que
le subscriber MQTT applique en production — on emprunte simplement un autre
chemin d'entrée, **sans broker**.

Premier palier du **niveau intermédiaire** de la progression IoT, après le
[niveau débutant](../debutant/bilan.md).

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
| `build_topic` / `build_payload` | Composer un topic et un payload conformes. | [Forge IoT — simulateur](../../../iot/listen-command.md) |
| `parse_message` | Valider topic + payload → `Measurement`. | [Forge IoT — contrat](../../../iot/storage-events.md) |
| `IotEventRepository.insert` | Écrire la mesure validée dans `iot_events`. | [Forge IoT — stockage](../../../iot/storage-events.md) |
| `BaseController.csrf_token` / `redirect` | Protéger le POST, rediriger (PRG). | [BaseController](../../../reference/api.md#coremvccontroller) |

## Tester

```bash
forge db:init
forge run
```

Ouvrez `https://localhost:8000/iot-simulate`, ajustez les champs et cliquez
**Injecter la mesure** : elle apparaît dans la liste des derniers événements. Vous
venez d'alimenter `iot_events` **sans broker**.

## Le contrôleur

```python
# mvc/controllers/iot_simulate_controller.py
import json
from forge_mvc_iot.cli.simulate import build_payload, build_topic, utc_timestamp
from forge_mvc_iot.mqtt.contract import ContractError, parse_message
from forge_mvc_iot.storage import IotEventRepository


class IotSimulateController(BaseController):

    @staticmethod
    def simulate(request: Request) -> Response:
        site = (request.form("site") or "atelier").strip()
        device_id = (request.form("device_id") or "capteur-1").strip()
        kind = (request.form("kind") or "temperature").strip()
        unit = (request.form("unit") or "C").strip()
        try:
            value = float((request.form("value") or "").strip())
        except ValueError:
            return IotSimulateController._page(request, error="La valeur doit être un nombre.")
        try:
            topic = build_topic(site, device_id)
            payload = build_payload(kind=kind, value=value, unit=unit, timestamp=utc_timestamp())
            measurement = parse_message(topic, json.dumps(payload))
            IotEventRepository().insert(measurement)
        except ContractError as exc:
            return IotSimulateController._page(request, error=str(exc))
        return BaseController.redirect("/iot-simulate")
```

### Comprendre ce code

- `build_payload(...)` produit un payload **conforme** (champs `kind`, `value`,
  `unit`, `timestamp`). `parse_message` le **valide** et renvoie un `Measurement`
  typé — une `ContractError` est levée si quelque chose ne respecte pas le
  contrat.
- `IotEventRepository().insert(measurement)` écrit la mesure validée. C'est le
  **même** repository qu'en lecture.
- En production, ce `Measurement` viendrait du broker via le subscriber ; ici, il
  vient du formulaire. Le reste du chemin est identique.

## À retenir

- On peut alimenter `iot_events` **sans broker**, via le contrat IoT.
- `parse_message` valide la mesure exactement comme en production.
- `IotEventRepository.insert` écrit ; `list_recent` relit : la boucle est
  bouclée en local.

## Après ce starter

Vous savez alimenter les données en local. La suite : exposer l'API HTTP JSON
officielle.

[Exposer l'API IoT](iot-api.md)
