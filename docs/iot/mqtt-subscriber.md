# Subscriber MQTT Forge IoT

> **Statut** : implémentation initiale du subscriber, branchée sur
> [paho-mqtt](https://pypi.org/project/paho-mqtt/). Le module produit
> des objets `Measurement` parsés ; il **n'écrit encore rien en base**
> et **n'expose aucune route HTTP** — ces étapes appartiennent aux
> tickets suivants (`IOT-STORAGE-EVENTS-001`, `IOT-HTTP-API-001`).

## Objectif

Brancher Forge sur un broker MQTT pour recevoir les messages des
capteurs, **strictement selon le contrat figé** par
[IOT-MQTT-CONTRACT-001](mqtt-contract.md), et délivrer chaque mesure
valide à un callback applicatif.

## Architecture du module

Le code est volontairement scindé en deux modules :

| Module | Rôle | Dépend de paho-mqtt ? |
|--------|------|-----------------------|
| `forge_mvc_iot.mqtt.contract` | parsing et validation pure (topic + payload), construction de `Measurement` | non — testable hors ligne |
| `forge_mvc_iot.mqtt.subscriber` | pont vers `paho.mqtt.client.Client`, callbacks, abonnement, cycle de vie | oui |

Cette séparation permet de :

- tester l'intégralité du contrat sans installer ou simuler un broker ;
- réutiliser `parse_message` ailleurs (par exemple dans un test d'API
  HTTP qui injecte directement une mesure) ;
- changer plus tard de bibliothèque MQTT sans toucher au contrat.

## API publique

### `contract.parse_message(topic, payload)`

Parse un message complet et retourne une `Measurement`.

```python
from forge_mvc_iot.mqtt.contract import parse_message

m = parse_message(
    "forge/atelier/esp32-001/telemetry",
    b'{"kind":"temperature","value":22.4,"unit":"°C",'
    b'"timestamp":"2026-05-28T10:00:00Z"}',
)
# Measurement(site='atelier', device_id='esp32-001', kind='temperature',
#             value=22.4, unit='°C', timestamp='2026-05-28T10:00:00Z',
#             metadata=None)
```

`payload` accepte `str` ou `bytes`.

### `contract.Measurement`

Dataclass immuable (`frozen=True`) :

```python
@dataclass(frozen=True)
class Measurement:
    site: str
    device_id: str
    kind: str
    value: int | float
    unit: str
    timestamp: str             # ISO 8601 UTC, suffixe Z
    metadata: dict[str, str] | None
```

Le `timestamp` reste en chaîne ISO pour rester proche du payload reçu :
les consommateurs convertissent en `datetime` quand ils en ont besoin.

### `contract.ContractError`

Exception levée pour toute violation du contrat. Porte un attribut
`code` issu de la taxonomie stable :

| Constante | Valeur |
|-----------|--------|
| `CODE_TOPIC_PATTERN` | `"TOPIC_PATTERN"` |
| `CODE_PAYLOAD_PARSE` | `"PAYLOAD_PARSE"` |
| `CODE_PAYLOAD_FIELD_MISSING` | `"PAYLOAD_FIELD_MISSING"` |
| `CODE_PAYLOAD_FIELD_TYPE` | `"PAYLOAD_FIELD_TYPE"` |
| `CODE_PAYLOAD_VALUE_FORMAT` | `"PAYLOAD_VALUE_FORMAT"` |

Ces codes sont identiques à ceux documentés dans
[Contrat MQTT — Erreurs](mqtt-contract.md#erreurs-de-contrat-taxonomie).

```python
from forge_mvc_iot.mqtt.contract import ContractError, parse_message

try:
    parse_message("bad", b"{}")
except ContractError as exc:
    print(exc.code)     # 'TOPIC_PATTERN'
    print(exc.message)  # 'Topic invalide : ...'
```

### `subscriber.MqttSubscriber`

Pont avec `paho-mqtt`.

```python
from forge_mvc_iot.config import load_iot_config
from forge_mvc_iot.mqtt.subscriber import MqttSubscriber

cfg = load_iot_config()  # lit os.environ

def on_measurement(m):
    print(f"{m.site}/{m.device_id} → {m.kind}={m.value}{m.unit}")

sub = MqttSubscriber(cfg, on_measurement=on_measurement)
sub.connect()
sub.loop_forever()
```

#### Paramètres du constructeur

| Paramètre | Type | Rôle |
|-----------|------|------|
| `config` | `IotConfig` | configuration chargée par `load_iot_config` |
| `on_measurement` | `Callable[[Measurement], None]` | obligatoire — appelé pour chaque mesure valide |
| `on_contract_error` | `Callable[[ContractError, str, bytes], None] \| None` | optionnel — appelé pour chaque violation de contrat. Si `None`, l'erreur est uniquement loguée. |
| `client_factory` | `Callable[[IotConfig], Any] \| None` | optionnel — fabrique de client MQTT, utile pour les tests. Par défaut, instancie un `paho.mqtt.client.Client` configuré pour `CallbackAPIVersion.VERSION2`. |

#### Méthodes de cycle de vie

| Méthode | Effet |
|---------|-------|
| `connect()` | ouvre la connexion vers le broker |
| `disconnect()` | ferme la connexion |
| `loop_forever()` | boucle réseau bloquante |
| `loop_start()` | boucle réseau en thread séparé |
| `loop_stop()` | arrête la boucle démarrée par `loop_start` |
| `handle_message(topic, payload)` | point d'entrée testable — parse + dispatch |

## Exemple complet — script de réception

```python
import logging

from forge_mvc_iot.config import load_iot_config
from forge_mvc_iot.mqtt.contract import ContractError, Measurement
from forge_mvc_iot.mqtt.subscriber import MqttSubscriber

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("forge-iot-demo")


def on_measurement(m: Measurement) -> None:
    log.info(
        "%s/%s — %s = %s %s @ %s",
        m.site, m.device_id, m.kind, m.value, m.unit, m.timestamp,
    )


def on_contract_error(exc: ContractError, topic: str, payload: bytes) -> None:
    log.warning("Refusé [%s] sur %r : %s", exc.code, topic, exc.message)


def main() -> None:
    cfg = load_iot_config()
    sub = MqttSubscriber(cfg, on_measurement, on_contract_error)
    sub.connect()
    sub.loop_forever()


if __name__ == "__main__":
    main()
```

Avec un Mosquitto local qui tourne, on peut publier depuis un autre
terminal :

```bash
mosquitto_pub \
  -h localhost \
  -t forge/atelier/esp32-001/telemetry \
  -m '{"kind":"temperature","value":22.4,"unit":"°C","timestamp":"2026-05-28T10:00:00Z"}'
```

Le script affiche :

```text
INFO forge-iot-demo: atelier/esp32-001 — temperature = 22.4 °C @ 2026-05-28T10:00:00Z
```

## Tester sans broker

Tout le contrat est testable sans paho :

```python
from forge_mvc_iot.mqtt.contract import parse_message

m = parse_message("forge/atelier/esp32-001/telemetry", b'{...}')
assert m.kind == "temperature"
```

Le subscriber lui-même est testable en injectant un `client_factory` :

```python
from unittest.mock import MagicMock
from forge_mvc_iot.config import IotConfig
from forge_mvc_iot.mqtt.subscriber import MqttSubscriber

cfg = IotConfig(
    mqtt_host="localhost", mqtt_port=1883,
    mqtt_topic="forge/+/+/telemetry",
    mqtt_client_id="t",
    mqtt_username=None, mqtt_password=None,
)
sub = MqttSubscriber(
    cfg,
    on_measurement=lambda m: print(m),
    client_factory=lambda c: MagicMock(),
)
sub.handle_message(
    "forge/atelier/esp32-001/telemetry",
    b'{"kind":"temperature","value":22.4,"unit":"°C","timestamp":"2026-05-28T10:00:00Z"}',
)
```

C'est le pattern utilisé par la suite de tests
`tests/test_iot_mqtt_subscriber_001.py`.

## Comportement face aux erreurs

Pour chaque message reçu, le subscriber tente
`parse_message(topic, payload)` :

- **Succès** → `on_measurement(Measurement)` est appelé.
- **`ContractError`** :
  - un message `WARNING` est logué sur `forge_mvc_iot.mqtt.subscriber`
    avec le code d'erreur et le topic en cause ;
  - si `on_contract_error` est fourni, il est appelé avec
    `(exc, topic, payload)` ;
  - le subscriber **ne se déconnecte pas** — un message invalide ne
    casse pas la session MQTT.

Les erreurs de connexion broker (broker injoignable, identifiants
refusés) restent gérées par paho-mqtt. La reconnexion automatique se
fait via `loop_forever()` / `loop_start()`. Un raffinement (backoff,
politique de reconnexion personnalisée) sera abordé dans
`IOT-DOCTOR-001`.

## Décisions verrouillées

- **`site` et `device_id` viennent du topic.** Tout champ `site` ou
  `device_id` présent dans le payload est ignoré silencieusement
  (couvert par les tests).
- **Codes d'erreur stables.** La taxonomie est figée — un futur test
  du subscriber peut s'appuyer sur `exc.code == "PAYLOAD_PARSE"` sans
  craindre un renommage.
- **Pas d'imports paho dans `contract.py`.** La séparation est testée :
  `parse_message` reste utilisable même si paho-mqtt n'est pas installé.

## Hors périmètre de ce ticket

- pas de stockage SQL des mesures (futur `IOT-STORAGE-EVENTS-001`) ;
- pas de migration ;
- pas de route HTTP exposant les mesures (futur `IOT-HTTP-API-001`) ;
- pas de commande `forge iot:*` (futur `IOT-DOCTOR-001`) ;
- pas de dashboard, pas de Forge Design ;
- pas de TLS / ACL Mosquitto ;
- pas de downlink Forge → capteur.

Voir [Architecture Forge IoT](architecture.md#tickets-suivants) pour la
liste complète des jalons.
