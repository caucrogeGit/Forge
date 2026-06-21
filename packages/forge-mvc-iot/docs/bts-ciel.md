# Forge IoT pour Bac Pro / BTS CIEL

> **Statut** : page **pédagogique**. Elle explique le sens du socle Forge
> IoT pour un usage en lycée professionnel (Bac Pro) et en BTS CIEL, et
> propose des activités simples exploitables en classe. Elle s'appuie sur
> les commandes déjà livrées, sans capteur physique obligatoire.

## Objectif pédagogique

Comprendre, de bout en bout, comment une **mesure** voyage d'un capteur
jusqu'à son exploitation :

```text
capteur
   → MQTT
   → Mosquitto
   → Forge IoT
   → base iot_events
   → API HTTP
   → exploitation / visualisation
```

L'élève peut dérouler tout ce flux **sans matériel**, grâce au
simulateur `forge iot:simulate`, puis remplacer plus tard le simulateur
par un vrai capteur.

## Compétences travaillées

- lire et décomposer un **topic MQTT** ;
- comprendre un **message JSON** et ses champs obligatoires ;
- distinguer les rôles **broker / producteur / consommateur** ;
- utiliser une **base de données** comme mémoire des événements ;
- consommer une **API HTTP** pour exploiter des données ;
- **diagnostiquer une panne** avec les bons outils.

## Architecture générale

| Brique | Rôle |
|--------|------|
| Capteur | produit une mesure (température, humidité…) |
| MQTT | protocole qui transporte la mesure |
| Mosquitto | broker : reçoit et redistribue les messages MQTT |
| Forge IoT | écoute, **valide**, **stocke** et **expose** les données |
| MariaDB (`iot_events`) | conserve les événements |
| API HTTP (`/api/iot/events`) | permet d'exploiter les mesures |
| Forge Design | futur cockpit de visualisation (à venir) |

## Rôle du capteur

Le capteur **produit** une mesure : une grandeur physique (température,
humidité, luminosité…) transformée en nombre. En classe, on le remplace
par `forge iot:simulate`, qui produit des mesures factices mais
réalistes.

Les **profils** du simulateur (`--profile temperature|humidity|presence|energy`)
permettent de construire des exercices sans capteur réel : chaque profil
fournit un `kind`, une `value` et une `unit` cohérents. Voir
[Simulateur — profils de simulation](simulator.md#profils-de-simulation).

```bash
forge iot:simulate --profile humidity --count 5
```

## Rôle de MQTT

MQTT est le **protocole de transport**. Une mesure est publiée sur un
**topic** — une adresse hiérarchique. Le contrat Forge IoT impose :

```text
forge/{site}/{device_id}/telemetry
```

Exemple :

```text
forge/atelier/esp32-001/telemetry
```

## Rôle de Mosquitto

Mosquitto est le **broker** : il reçoit les messages publiés et les
redistribue à tous les abonnés du topic. Il ne stocke pas les mesures à
long terme — il les fait circuler. Installation et démarrage :
[Mosquitto local](mosquitto-local.md).

## Rôle de Forge IoT

Forge IoT est le **consommateur** côté serveur. Avec `forge iot:listen`,
il :

1. **écoute** le topic configuré ;
2. **valide** chaque message contre le contrat (topic + JSON) ;
3. **stocke** la mesure dans la table `iot_events` ;
4. l'**expose** ensuite via l'API HTTP.

Un message qui ne respecte pas le contrat est rejeté : c'est ce qui
garantit des données propres en base.

## Rôle de la base de données

MariaDB conserve les événements dans la table `iot_events`. Chaque ligne
garde le `site`, le `device_id`, le `kind`, la `value`, l'`unit`, le
`timestamp` du capteur et un `received_at` (heure de réception serveur).
La base est la **mémoire** du système.

## Rôle de l'API HTTP

L'API HTTP `GET /api/iot/events` permet d'**exploiter** les mesures
stockées (les afficher, les analyser, les visualiser). C'est le point
d'entrée d'une future interface — sans dépendre du broker directement.
En classe, l'API reste **ouverte** ; pour un projet exposé sur le
réseau, on peut la protéger par un
[token Bearer](http-api.md#protection-par-bearer-token)
(`FORGE_IOT_API_TOKEN`).

## Exemple de message

Payload JSON publié sur le topic `forge/atelier/esp32-001/telemetry` :

```json
{
  "kind": "temperature",
  "value": 22.4,
  "unit": "°C",
  "timestamp": "2026-05-29T10:00:00Z"
}
```

Le flux concret, étape par étape :

```text
forge iot:simulate
   ↓  publie sur forge/atelier/esp32-001/telemetry
Mosquitto
   ↓
forge iot:listen
   ↓  INSERT
iot_events
   ↓
GET /api/iot/events
```

## Parcours de test local

À dérouler en salle (Mosquitto et MariaDB locaux) :

```bash
forge iot:doctor --mqtt                     # le broker répond ?
forge iot:listen                            # terminal 1 : écouter et stocker
forge iot:simulate --count 3 --interval 1   # terminal 2 : publier 3 mesures
curl http://localhost:8000/api/iot/events   # terminal 3 : relire les mesures
```

Le scénario complet encadré : [smoke test local](local-smoke-test.md).

## Activités possibles en classe

### Activité 1 — Comprendre le topic MQTT

À partir du topic `forge/atelier/esp32-001/telemetry`, répondre :

- quel est le **site** ?
- quel est l'**identifiant du capteur** (`device_id`) ?
- quel est le **type de message** (dernier niveau) ?

### Activité 2 — Valider un payload JSON

Parmi ces payloads, lesquels sont **valides** (champs obligatoires
`kind`, `value`, `unit`, `timestamp` ; `timestamp` en UTC suffixe `Z`) ?

```json
{"kind":"temperature","value":22.4,"unit":"°C","timestamp":"2026-05-29T10:00:00Z"}
{"kind":"temperature","value":22.4,"unit":"°C"}
{"value":22.4,"unit":"°C","timestamp":"2026-05-29T10:00:00Z"}
{"kind":"temperature","value":22.4,"unit":"°C","timestamp":"2026-05-29 10:00:00"}
```

### Activité 3 — Simuler une mesure

```bash
forge iot:doctor --mqtt
forge iot:listen
forge iot:simulate --count 3 --interval 1
```

Observer les lignes `[OK]` côté `forge iot:listen`.

### Activité 4 — Lire les données via l'API

```bash
curl http://localhost:8000/api/iot/events
```

Faire identifier dans la réponse : `site`, `device_id`, `kind`, `value`,
`unit`, `timestamp`, `received_at`.

### Activité 5 — Diagnostiquer une panne

Associer chaque panne à la commande utile :

| Panne | Commande de diagnostic / réparation |
|-------|-------------------------------------|
| Mosquitto arrêté | `forge iot:doctor --mqtt` |
| table `iot_events` absente | `forge iot:doctor --db`, puis `forge iot:init` + `forge migration:apply` |
| topic invalide | rappel du format `forge/{site}/{device_id}/telemetry` |
| payload invalide | rappel des champs obligatoires |

## Erreurs fréquentes

- **Mosquitto arrêté** → `ConnectionRefusedError` : démarrer le broker
  (voir [Mosquitto local](mosquitto-local.md)) ;
- **table absente** → `iot_storage_not_ready` : `forge iot:init` puis
  `forge migration:apply` ;
- **topic invalide** → le message est rejeté : respecter
  `forge/{site}/{device_id}/telemetry` ;
- **payload invalide** → champ obligatoire manquant ou `timestamp` sans
  `Z`.

## Limites

Cette page pose le cadre pédagogique général. Sont **hors périmètre** :

- en classe, on part du simulateur `forge iot:simulate` ; pour un
  capteur réel, voir l'[exemple ESP32](esp32-example.md) ;
- l'**Arduino R4** n'est pas couvert ici (hors périmètre) — l'exemple cible l'ESP32 ;
- pas de fiche élève PDF, pas de grille d'évaluation, pas de séquence
  pédagogique complète — pourront venir plus tard ;
- pas de cockpit de visualisation (Forge Design) — à venir ;
- pas de TLS ni d'authentification MQTT.

Les fiches élèves détaillées feront l'objet de tickets ultérieurs.
