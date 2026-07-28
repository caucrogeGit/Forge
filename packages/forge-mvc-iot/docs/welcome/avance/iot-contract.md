# Valider un message IoT

Objectif : comprendre le **contrat** qu'un message réel doit respecter avant d'être accepté.

**Ce que vous allez apprendre :** `parse_message`.
Un message arrivant d'un vrai capteur (topic + payload JSON) doit respecter le contrat Forge IoT.
`parse_message` le **valide** et renvoie une `Measurement`, ou lève une `ContractError` portant un **code** d'erreur.
C'est exactement la validation que le subscriber applique en production : ici on l'exerce à la main, sans broker.

Premier palier du **niveau avancé** de la progression IoT : la bascule vers le **temps réel**.
Après le [niveau intermédiaire](../intermediaire/bilan.md).

## Ce que ce starter montre

- le contrat de message : topic `forge/{site}/{device_id}/telemetry` + payload ;
- la validation `parse_message(topic, payload)` → `Measurement` ;
- la gestion d'une `ContractError` avec son **code** (ex. `TOPIC_PATTERN`, `PAYLOAD_FIELD_MISSING`) ;
- un formulaire pour tester un message valide **et** un message fautif.

Aucun broker, aucune base : on apprend les règles que les vrais messages doivent respecter.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_iot.mqtt.contract.parse_message` | Valider topic + payload → `Measurement`. | [Forge IoT : contrat](../../storage-events.md) |
| `ContractError` | Erreur de contrat, porte un `code` exploitable. | [Forge IoT : contrat](../../storage-events.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/iot-contract`.
Le formulaire est pré-rempli avec un message valide → **Valider** affiche la `Measurement`.
Modifiez le topic (par exemple retirez `/telemetry`) ou un champ du payload → la page affiche le **code** et le message de l'erreur de contrat.

## Le contrôleur

Créez le fichier ci-dessous, complet et copiable tel quel.

```python
# mvc/controllers/iot_contract_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.mqtt.contract import ContractError, parse_message


_DEFAULT_TOPIC = "forge/atelier/capteur-1/telemetry"
_DEFAULT_PAYLOAD = '{"kind": "temperature", "value": 21.5, "unit": "C", "timestamp": "2026-06-01T10:00:00Z"}'


class IotContractController(BaseController):
    """Starter pédagogique : valider un message contre le contrat IoT."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "iot_contract/index.html",
            context={
                "csrf_token": BaseController.csrf_token(request),
                "topic": _DEFAULT_TOPIC,
                "payload": _DEFAULT_PAYLOAD,
            },
            request=request,
        )

    @staticmethod
    def validate(request: Request) -> Response:
        topic = (request.form("topic") or "").strip()
        payload = (request.form("payload") or "").strip()
        context = {
            "csrf_token": BaseController.csrf_token(request),
            "topic": topic,
            "payload": payload,
        }
        try:
            measurement = parse_message(topic, payload)
        except ContractError as exc:
            context["error_code"] = exc.code
            context["error"] = exc.message
            return BaseController.render(
                "iot_contract/index.html", context=context, request=request
            )
        context["measurement"] = {
            "site": measurement.site,
            "device_id": measurement.device_id,
            "kind": measurement.kind,
            "value": measurement.value,
            "unit": measurement.unit,
            "timestamp": measurement.timestamp,
        }
        return BaseController.render(
            "iot_contract/index.html", context=context, request=request
        )
```

### Comprendre ce code

- `parse_message(topic, payload)` applique **tout** le contrat : forme du topic, JSON du payload, champs obligatoires, types, formats (timestamp ISO 8601 UTC…).
- Une violation lève une `ContractError` avec un `code` (ex. `TOPIC_PATTERN`, `PAYLOAD_PARSE`, `PAYLOAD_FIELD_MISSING`), exploitable pour logs et tests.
- En production, ce même appel rejette les messages mal formés **avant** tout stockage.
  Vous venez d'exercer la porte d'entrée du système.

## La vue

Créez le gabarit ci-dessous : formulaire de saisie, affichage de la `Measurement` valide ou du code d'erreur.

```html
<!-- mvc/views/iot_contract/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Valider un message IoT - Forge</title>
</head>
<body>
  <h1>Valider un message IoT</h1>

  {% if error %}
  <p data-level="error"><strong>[{{ error_code }}]</strong> {{ error }}</p>
  {% endif %}

  {% if measurement %}
  <p data-level="success">Message valide :</p>
  <ul>
    <li>Site : {{ measurement.site }}</li>
    <li>Capteur : {{ measurement.device_id }}</li>
    <li>Type : {{ measurement.kind }}</li>
    <li>Valeur : {{ measurement.value }} {{ measurement.unit }}</li>
    <li>Horodatage : {{ measurement.timestamp }}</li>
  </ul>
  {% endif %}

  <form method="post" action="/iot-contract">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <label>Topic <input type="text" name="topic" value="{{ topic }}" size="50"></label>
    <label>Payload (JSON)
      <textarea name="payload" rows="4" cols="60">{{ payload }}</textarea>
    </label>
    <button type="submit">Valider</button>
  </form>
</body>
</html>
```

## La route

Déclarez les deux routes (`GET` pour la page, `POST` pour la validation) dans `mvc/routes/__init__.py`, à l'intérieur du groupe public.

```python
# mvc/routes/__init__.py
from mvc.controllers.iot_contract_controller import IotContractController

with router.group("", public=True) as public:
    public.add("GET", "/iot-contract", IotContractController.index, name="iot_contract_index")
    public.add("POST", "/iot-contract", IotContractController.validate, name="iot_contract_validate")
```

## À retenir

- Un message réel doit respecter le **contrat** : topic + payload conformes.
- `parse_message` valide et renvoie une `Measurement`, sinon une `ContractError`.
- `ContractError.code` identifie précisément la règle violée.

## Après ce starter

Vous connaissez le contrat.
La suite : recevoir ces messages d'un **vrai broker**.

[Le subscriber MQTT](iot-subscriber.md)
