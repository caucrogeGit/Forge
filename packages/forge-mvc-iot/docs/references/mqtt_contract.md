# Le contrat MQTT dans Forge IoT

Ce document décrit le parsing et la validation des messages MQTT reçus.

Le fichier de code correspondant est `forge_mvc_iot/mqtt/contract.py`.

## 1. À quoi sert ce module ?

Un message MQTT brut (un topic et un payload) n'est pas fiable tel quel.
Ce module le **parse** et le **valide** en une `Measurement` propre et typée, prête à être persistée ou exposée.

## 2. L'objet `Measurement`

| Attribut | Contenu |
|---|---|
| `site`, `device_id` | provenance, extraits du topic |
| `kind` | type de mesure (température, humidité…) |
| `value`, `unit` | valeur numérique et unité |
| `timestamp` | horodatage de la mesure |
| `metadata` | données complémentaires optionnelles |

## 3. L'API

| Fonction | Comportement |
|---|---|
| `parse_topic(topic)` | retourne `(site, device_id)` extraits du topic |
| `parse_payload(payload)` | décode et parse le payload JSON ; retourne le dict brut |
| `parse_message(topic, payload)` | parse un message complet en `Measurement` |

```python
from forge_mvc_iot.mqtt.contract import parse_message

m = parse_message("forge/iot/atelier/capteur-1", b'{"kind":"temp","value":21.5,"unit":"C","timestamp":"..."}')
```

## 4. Les erreurs

`ContractError` (code + message) est levée quand le topic ou le payload ne respecte pas le contrat.

## 5. Contextes d'utilisation

- **Subscriber** : `parse_message` à chaque message reçu.
- **Tests** : valider le parsing à partir de messages figés.

## 6. Voir aussi

- [Le subscriber MQTT](mqtt_subscriber.md) : appelle ce parsing.
- [Le stockage des événements](storage_events.md) : persiste la `Measurement`.
- [Contrat MQTT (guide)](../mqtt-contract.md) : le format détaillé des messages.
