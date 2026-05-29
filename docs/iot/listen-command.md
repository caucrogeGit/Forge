# Écoute Forge IoT — `forge iot:listen`

> **Statut** : commande de **développement / pédagogie**. Elle écoute le
> broker MQTT configuré et **insère** chaque mesure reçue dans la table
> `iot_events`. Ce n'est **pas** un service de production (pas de daemon,
> pas de retry, pas de batch).

## Objectif

Relier les briques Forge IoT en un flux local réellement utilisable :

```text
Mosquitto
   ↓
forge iot:listen
   ↓
MqttSubscriber
   ↓
IotEventRepository.insert()
   ↓
iot_events
```

Jusqu'ici, `forge iot:simulate` publiait des mesures, mais Forge n'avait
pas de commande simple pour **écouter et stocker**. C'est ce que comble
`forge iot:listen`.

## Usage

```bash
forge iot:listen
```

Aucune option pour ce premier ticket. Aide via :

```bash
forge iot:listen --help
```

La commande reste active jusqu'à `Ctrl+C`, puis s'arrête proprement.

## Sortie exemple

```text
Forge IoT listen

[INFO] Broker MQTT : localhost:1883
[INFO] Topic       : forge/+/+/telemetry
[INFO] Stockage    : table iot_events via IotEventRepository
[INFO] En écoute. Ctrl+C pour arrêter.

[OK] atelier/esp32-001 temperature=22.4 °C
[OK] atelier/esp32-001 humidity=55 %
^C
[INFO] Arrêt demandé.
[OK] Écoute MQTT arrêtée proprement.

Résumé :
  mesures reçues       : 2
  mesures stockées     : 2
  erreurs de contrat   : 0
  erreurs de stockage  : 0
```

Chaque ligne `[OK]` correspond à une mesure validée par le
[contrat MQTT](mqtt-contract.md) **et** insérée dans `iot_events`.

### Arrêt propre

Sur `Ctrl+C`, la commande affiche `[INFO] Arrêt demandé.` puis, une fois
la connexion fermée, `[OK] Écoute MQTT arrêtée proprement.`. La
déconnexion du broker (`disconnect`) est **toujours** effectuée, même si
l'écoute s'est interrompue sur une erreur.

### Résumé de session

À l'arrêt, un petit résumé récapitule la session — utile en classe et
pour le debug :

```text
Résumé :
  mesures reçues       : 3
  mesures stockées     : 3
  erreurs de contrat   : 0
  erreurs de stockage  : 0
```

- **mesures reçues** : messages conformes au [contrat MQTT](mqtt-contract.md) ;
- **mesures stockées** : insertions réussies dans `iot_events` ;
- **erreurs de contrat** : messages MQTT ignorés (payload ou topic invalide) ;
- **erreurs de stockage** : échecs d'insertion en base.

### Message MQTT invalide

Un message qui ne respecte pas le contrat (topic mal formé, champ
manquant, type incorrect…) est **ignoré sans arrêter l'écoute** :

```text
[WARN] Message MQTT ignoré — PAYLOAD_FIELD_MISSING
```

Le code affiché (`TOPIC_PATTERN`, `PAYLOAD_PARSE`,
`PAYLOAD_FIELD_MISSING`, `PAYLOAD_FIELD_TYPE`, `PAYLOAD_VALUE_FORMAT`)
vient de la taxonomie du [contrat MQTT](mqtt-contract.md). Le compteur
`erreurs de contrat` est incrémenté. Contrairement à une erreur base, un
message invalide **ne fait pas tomber** la commande : on continue
d'écouter.

## Parcours complet

`forge iot:listen` est le maillon central d'un flux qui réutilise toutes
les commandes IoT déjà disponibles :

```bash
forge iot:doctor          # package, config, migration, API HTTP
forge iot:init            # copier la migration vers mvc/migrations/
forge migration:apply     # créer la table iot_events
forge iot:doctor --db     # confirmer que la table est lisible
forge iot:doctor --mqtt   # confirmer que le broker répond
forge iot:listen          # écouter et stocker (laisser tourner)
```

Dans un **second terminal**, publie des mesures :

```bash
forge iot:simulate --count 3 --interval 1
```

Les mesures apparaissent dans le terminal `forge iot:listen` (`[OK] …`),
puis sont lisibles via l'[API HTTP](http-api.md) :

```bash
curl http://localhost:8000/api/iot/events
```

## Gestion des erreurs

### Configuration invalide

```text
[ERREUR] Configuration IoT invalide : FORGE_IOT_MQTT_HOST ne peut pas être vide
```

Exit code 1. Voir [Configuration Forge IoT](configuration.md).

### Broker inaccessible

```text
[ERREUR] Connexion MQTT impossible : [Errno 111] Connection refused
```

Exit code 1. Le broker n'est pas démarré ou l'hôte/port est faux —
diagnostique avec `forge iot:doctor --mqtt`. Pour installer et lancer un
broker local, voir [Mosquitto local](mosquitto-local.md).

### Erreurs base

La commande **s'arrête au premier échec base** (exit code 1) —
volontairement simple et pédagogique — et distingue trois cas, message
**sobre** (jamais de stacktrace) :

**Table `iot_events` absente :**

```text
[ERREUR] Table iot_events absente.
Conseil : lance forge iot:init puis forge migration:apply.
```

Crée la table (`forge iot:init` puis `forge migration:apply`) puis
relance `forge iot:listen`.

**Connexion base impossible** (MariaDB arrêté, mauvais identifiants, base
inconnue…) :

```text
[ERREUR] Connexion base impossible.
Conseil : vérifie forge db:init et forge iot:doctor --db.
```

**Autre erreur SQL** (cas générique) :

```text
[ERREUR] Stockage IoT impossible.
```

## Connexion TLS

`forge iot:listen` bénéficie du TLS **via le `MqttSubscriber`** : si
`FORGE_IOT_MQTT_TLS_ENABLED=true`, le subscriber appelle
`client.tls_set(...)` avant de se connecter (`ca_certs` =
`FORGE_IOT_MQTT_TLS_CA_FILE` si fourni, sinon les certificats système).
Pense à configurer aussi le port TLS du broker (généralement `8883`) :

```bash
export FORGE_IOT_MQTT_HOST="mqtt.example.net"
export FORGE_IOT_MQTT_PORT="8883"
export FORGE_IOT_MQTT_TLS_ENABLED="true"
export FORGE_IOT_MQTT_TLS_CA_FILE="/etc/ssl/certs/mosquitto-ca.crt"

forge iot:listen
```

Sans TLS (défaut), la connexion reste en clair — adapté au
[Mosquitto local](mosquitto-local.md). Détails :
[Configuration — TLS MQTT](configuration.md#tls-mqtt-preparation).

## Limites

`forge iot:listen` est conçue pour le **développement et la
pédagogie**, pas pour la production. Sont **hors périmètre** :

- pas de daemon systemd ni de mode service ;
- pas de file d'attente, de retry/backoff, ni de batch insert ;
- pas de stockage multi-thread ;
- pas de TLS ni d'authentification avancée ;
- ne lance pas le simulateur (voir [`forge iot:simulate`](simulator.md)) ;
- ne modifie ni l'[API HTTP](http-api.md) ni le
  [contrat MQTT](mqtt-contract.md).

Pour un déploiement réel, on brancherait `MqttSubscriber` dans un
processus supervisé de l'application — ce qui dépasse ce ticket.
