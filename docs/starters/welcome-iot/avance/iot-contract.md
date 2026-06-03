# Valider un message IoT

Objectif : comprendre le **contrat** qu'un message réel doit respecter avant
d'être accepté.

**Ce que vous allez apprendre :** `parse_message`. Un message arrivant d'un vrai
capteur (topic + payload JSON) doit respecter le contrat Forge IoT. `parse_message`
le **valide** et renvoie une `Measurement`, ou lève une `ContractError` portant un
**code** d'erreur. C'est exactement la validation que le subscriber applique en
production : ici on l'exerce à la main, sans broker.

Premier palier du **niveau avancé** de la progression IoT — la bascule vers le
**temps réel**. Après le [niveau intermédiaire](../intermediaire/bilan.md).

## Ce que ce starter montre

- le contrat de message : topic `forge/{site}/{device_id}/telemetry` + payload ;
- la validation `parse_message(topic, payload)` → `Measurement` ;
- la gestion d'une `ContractError` avec son **code** (ex. `TOPIC_PATTERN`,
  `PAYLOAD_FIELD_MISSING`) ;
- un formulaire pour tester un message valide **et** un message fautif.

Aucun broker, aucune base : on apprend les règles que les vrais messages doivent
respecter.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_iot.mqtt.contract.parse_message` | Valider topic + payload → `Measurement`. | [Forge IoT — contrat](../../../iot/storage-events.md) |
| `ContractError` | Erreur de contrat, porte un `code` exploitable. | [Forge IoT — contrat](../../../iot/storage-events.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/iot-contract`. Le formulaire est pré-rempli avec un
message valide → **Valider** affiche la `Measurement`. Modifiez le topic (par
exemple retirez `/telemetry`) ou un champ du payload → la page affiche le **code**
et le message de l'erreur de contrat.

## Le contrôleur

```python
# mvc/controllers/iot_contract_controller.py
from forge_mvc_iot.mqtt.contract import ContractError, parse_message


class IotContractController(BaseController):

    @staticmethod
    def validate(request: Request) -> Response:
        topic = (request.form("topic") or "").strip()
        payload = (request.form("payload") or "").strip()
        context = {"csrf_token": BaseController.csrf_token(request), "topic": topic, "payload": payload}
        try:
            measurement = parse_message(topic, payload)
        except ContractError as exc:
            context["error_code"] = exc.code
            context["error"] = exc.message
            return BaseController.render("iot_contract/index.html", context=context, request=request)
        context["measurement"] = {
            "site": measurement.site, "device_id": measurement.device_id,
            "kind": measurement.kind, "value": measurement.value,
            "unit": measurement.unit, "timestamp": measurement.timestamp,
        }
        return BaseController.render("iot_contract/index.html", context=context, request=request)
```

### Comprendre ce code

- `parse_message(topic, payload)` applique **tout** le contrat : forme du topic,
  JSON du payload, champs obligatoires, types, formats (timestamp ISO 8601 UTC…).
- Une violation lève une `ContractError` avec un `code` (ex. `TOPIC_PATTERN`,
  `PAYLOAD_PARSE`, `PAYLOAD_FIELD_MISSING`) — exploitable pour logs et tests.
- En production, ce même appel rejette les messages mal formés **avant** tout
  stockage. Vous venez d'exercer la porte d'entrée du système.

## À retenir

- Un message réel doit respecter le **contrat** : topic + payload conformes.
- `parse_message` valide et renvoie une `Measurement`, sinon une `ContractError`.
- `ContractError.code` identifie précisément la règle violée.

## Après ce starter

Vous connaissez le contrat. Faites le point dans le bilan du niveau.

[Bilan du niveau avancé](bilan.md)
