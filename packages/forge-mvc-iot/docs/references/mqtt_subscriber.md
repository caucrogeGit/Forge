# Le subscriber MQTT dans Forge IoT

Ce document décrit le pont entre le broker MQTT et Forge.

Le fichier de code correspondant est `forge_mvc_iot/mqtt/subscriber.py`.

## 1. À quoi sert ce module ?

Le **subscriber** se connecte au broker MQTT, écoute le topic configuré, et transmet chaque mesure validée à un callback applicatif.
C'est le pont vers la bibliothèque `paho-mqtt`.

## 2. Le `MqttSubscriber`

```python
from forge_mvc_iot.mqtt.subscriber import MqttSubscriber

def on_measurement(measurement):
    repository.insert(measurement)

subscriber = MqttSubscriber(config, on_measurement=on_measurement)
```

| Paramètre | Rôle |
|---|---|
| `config` | l'`IotConfig` (broker, topic, TLS) |
| `on_measurement` | callback appelé pour chaque `Measurement` valide |
| `on_contract_error` | callback optionnel pour les messages invalides |
| `client_factory` | fabrique de client injectable (tests sans broker réel) |

## 3. Le découplage

Le subscriber **ne décide pas** quoi faire de la mesure : il la valide (via [le contrat](mqtt_contract.md)) puis délègue au callback.
C'est l'application qui choisit de la persister, de l'exposer, ou de l'ignorer.

## 4. Contextes d'utilisation

- **Service d'écoute** : lancé par la commande `iot:listen`.
- **Tests** : injecter un `client_factory` simulant les messages.

## 5. Voir aussi

- [Le contrat MQTT](mqtt_contract.md) : la validation appliquée à chaque message.
- [La configuration TLS](mqtt_tls.md) : sécurise la connexion du subscriber.
- [Subscriber MQTT (guide)](../mqtt-subscriber.md) et [Écoute (iot:listen)](../listen-command.md).
