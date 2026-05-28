# Contrat MQTT Forge IoT

> **Statut** : contrat **documentaire** — aucun subscriber MQTT n'existe
> encore dans Forge. Cette page fige le format des topics et du payload
> JSON que `forge-mvc-iot` acceptera dans son itération 1, avant
> qu'un code de réception soit écrit (voir
> [Architecture Forge IoT](architecture.md) et le ticket
> `IOT-MQTT-SUBSCRIBER-001`).

## Objectif

Répondre à une seule question : quand un capteur publie un message MQTT,
quel topic et quel JSON Forge IoT accepte-t-il ?

Le contrat doit rester :

- explicite (on lit le topic et le payload, on sait ce qui est attendu) ;
- simple (un seul message = une seule mesure ponctuelle) ;
- routable (le topic identifie naturellement la source) ;
- testable (les exemples valides et invalides figurent dans cette page
  et sont vérifiés par un test méta).

## Topic officiel

Forme canonique :

```text
forge/{site}/{device_id}/telemetry
```

| Segment | Rôle | Contrainte |
|---------|------|------------|
| `forge` | Racine fixe du namespace Forge IoT | littéral `forge` |
| `{site}` | Identifiant du site / atelier / salle | slug `[a-z0-9-]+` |
| `{device_id}` | Identifiant unique du périphérique | slug `[a-z0-9-]+` |
| `telemetry` | Type de flux | littéral `telemetry` |

Exemple :

```text
forge/atelier/esp32-001/telemetry
```

Le slug ne contient ni espaces, ni accents, ni majuscules, ni segments
vides. Les `+` et `#` (wildcards MQTT) sont interdits dans la publication.

## Payload officiel

Le payload est un objet JSON UTF-8 sur une seule mesure ponctuelle.

### Champs obligatoires

| Champ | Type JSON | Description |
|-------|-----------|-------------|
| `kind` | `string` | Nature de la mesure (`"temperature"`, `"humidity"`, `"pressure"`…). Slug `[a-z0-9_-]+`. |
| `value` | `number` | Valeur numérique mesurée (`int` ou `float`). |
| `unit` | `string` | Unité telle qu'affichable (`"°C"`, `"%"`, `"hPa"`, `"lux"`…). |
| `timestamp` | `string` | Date/heure de la mesure au format ISO 8601 UTC, suffixe `Z` obligatoire. |

### Champs optionnels

| Champ | Type JSON | Description |
|-------|-----------|-------------|
| `metadata` | `object` | Métadonnées libres clé/valeur (chaînes courtes). Aucun champ imposé. |

Tout champ supplémentaire en dehors de cette liste est **ignoré** par
Forge IoT lors de la réception. Les ajouts au contrat se feront par
ticket dédié, jamais en douce.

## Décision : `device_id` et `site` viennent du topic, pas du payload

En MQTT, le topic sert naturellement à router et à identifier la source.
Faire figurer `device_id` ou `site` dans le payload **en plus** ouvre la
porte aux contradictions silencieuses :

```text
topic   : forge/atelier/esp32-001/telemetry
payload : {"device_id": "esp32-999", ...}
```

Pour l'itération 1, le contrat est sans ambiguïté :

- `site` vient du topic ;
- `device_id` vient du topic ;
- `kind`, `value`, `unit`, `timestamp` viennent du payload.

Conséquences :

- un payload qui contient quand même un champ `device_id` ou `site` ne
  fait pas échouer le message, mais sa valeur **est ignorée** — la
  vérité est dans le topic ;
- si un capteur veut envoyer plusieurs mesures de natures différentes,
  il publie plusieurs messages, pas un payload composite.

## Exemples valides

### Mesure minimale

Topic :

```text
forge/atelier/esp32-001/telemetry
```

Payload :

```json
{
  "kind": "temperature",
  "value": 22.4,
  "unit": "°C",
  "timestamp": "2026-05-28T10:00:00Z"
}
```

### Mesure avec métadonnées

Topic :

```text
forge/atelier/esp32-001/telemetry
```

Payload :

```json
{
  "kind": "temperature",
  "value": 22.4,
  "unit": "°C",
  "timestamp": "2026-05-28T10:00:00Z",
  "metadata": {
    "room": "atelier",
    "sensor": "dht22"
  }
}
```

### Mesure entière (humidité)

Topic :

```text
forge/salle-tp/raspi-04/telemetry
```

Payload :

```json
{
  "kind": "humidity",
  "value": 47,
  "unit": "%",
  "timestamp": "2026-05-28T10:00:05Z"
}
```

## Exemples invalides

Chaque exemple ci-dessous est refusé. La colonne « Raison » indique la
règle qu'il viole.

### Topic mal formé

| Topic | Raison |
|-------|--------|
| `atelier/esp32-001/telemetry` | racine `forge/` manquante |
| `forge/Atelier/esp32-001/telemetry` | majuscule dans `site` |
| `forge/atelier/esp32 001/telemetry` | espace dans `device_id` |
| `forge/atelier/esp32-001/data` | suffixe doit être `telemetry` |
| `forge/+/esp32-001/telemetry` | wildcard interdit en publication |
| `forge//esp32-001/telemetry` | segment `site` vide |

### Payload mal formé

Champ manquant :

```json
{
  "kind": "temperature",
  "value": 22.4,
  "unit": "°C"
}
```

Raison : `timestamp` est obligatoire.

Type incorrect :

```json
{
  "kind": "temperature",
  "value": "22.4",
  "unit": "°C",
  "timestamp": "2026-05-28T10:00:00Z"
}
```

Raison : `value` doit être un `number`, pas une chaîne.

Timestamp non UTC :

```json
{
  "kind": "temperature",
  "value": 22.4,
  "unit": "°C",
  "timestamp": "2026-05-28 12:00:00"
}
```

Raison : format ISO 8601 avec suffixe `Z` obligatoire (pas
d'espace séparateur, pas de fuseau implicite).

JSON invalide :

```text
{"kind": "temperature", "value": 22.4,
```

Raison : non parsable.

`kind` mal formé :

```json
{
  "kind": "Température",
  "value": 22.4,
  "unit": "°C",
  "timestamp": "2026-05-28T10:00:00Z"
}
```

Raison : `kind` doit être un slug `[a-z0-9_-]+` — `"Température"`
contient des majuscules et des accents.

## Erreurs de contrat — taxonomie

À l'usage du futur subscriber et de ses tests, les violations sont
classées comme suit :

| Code | Sens | Action attendue côté Forge IoT |
|------|------|-------------------------------|
| `TOPIC_PATTERN` | Topic ne respecte pas `forge/{site}/{device_id}/telemetry` | refus, log warning |
| `PAYLOAD_PARSE` | JSON non parsable | refus, log warning |
| `PAYLOAD_FIELD_MISSING` | Champ obligatoire absent | refus, log warning |
| `PAYLOAD_FIELD_TYPE` | Champ présent mais type incorrect | refus, log warning |
| `PAYLOAD_VALUE_FORMAT` | Champ correct côté type mais mal formé (`kind` non slug, `timestamp` non ISO 8601 UTC, etc.) | refus, log warning |

Les codes ci-dessus sont des **identifiants stables** : ils figureront
tels quels dans les logs et dans les tests du subscriber. Ils ne sont
pas exposés publiquement par une API Python à ce stade — c'est un
contrat documentaire.

## Limites de l'itération 1

Sont explicitement **hors périmètre** de cette première version du
contrat :

- pas de batch — un message MQTT = une seule mesure ;
- pas de mesures composites (par exemple `{"temperature": …, "humidity":
  …}` dans le même payload) ;
- pas de topics commandes (downlink Forge → capteur) ;
- pas de topics de configuration (`forge/{site}/{device_id}/config`) ;
- pas de topics d'événement (`forge/{site}/{device_id}/event`) ;
- pas de politique QoS imposée — Forge IoT acceptera ce que le broker
  délivre ;
- pas de politique `retain` imposée ;
- pas de schéma versionné dans le payload (`schema_version`) — l'évolution
  passera par un nouveau ticket de contrat.

Toute extension de ce contrat passera par un ticket
`IOT-MQTT-CONTRACT-NNN` ultérieur. Une fois l'itération 1 figée, **les
champs obligatoires ne peuvent plus changer rétroactivement** sans
rupture explicite documentée.

## Tickets suivants

Ce contrat débloque :

- `IOT-MQTT-SUBSCRIBER-001` — implémentation du subscriber `paho-mqtt`
  qui consomme exactement ces topics et payloads ;
- `IOT-CONFIG-001` — variables d'environnement broker (host, port, TLS,
  login) ;
- `IOT-STORAGE-EVENTS-001` — table SQL des événements IoT, dont les
  colonnes seront alignées sur les champs du contrat.

Voir [Architecture Forge IoT](architecture.md#tickets-suivants) pour
la liste complète des jalons.
