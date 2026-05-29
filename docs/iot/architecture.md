# Architecture Forge IoT

> **Statut** : document fondateur. Aucun code IoT n'existe encore dans
> Forge. Cette page fige le périmètre et la séparation des rôles avant
> tout développement MQTT, dans l'esprit de la charte v2 §8 « Noyau
> minimal, briques opt-in ».

## Objectif

Permettre à Forge de devenir une brique utile pour des projets IoT
(notamment BTS CIEL, capteurs ESP32/Arduino, applications domotiques
éducatives) **sans transformer le framework en plateforme IoT
monolithique**.

Pour une entrée pédagogique orientée enseignement, voir
[Forge IoT pour Bac Pro / BTS CIEL](bts-ciel.md).

Forge IoT doit rester :

- explicite (pas de magie cachée derrière les messages MQTT) ;
- pédagogique (un lecteur doit pouvoir suivre le trajet d'un message
  capteur → broker → Forge → interface) ;
- opt-in (Forge Core ne dépend jamais d'un broker MQTT) ;
- durable (la décision de protocole n'enferme pas l'architecture).

## Positionnement

| Brique | Type | Statut |
|--------|------|--------|
| Forge Core (`forge-mvc`) | Framework MVC HTTP générique | existe |
| `forge-mvc-iot` | Module officiel opt-in (futur) | à créer |
| Mosquitto | Broker MQTT local recommandé | externe |
| Broker MQTT cloud | Alternative possible (HiveMQ, EMQX, AWS IoT, …) | externe, non prioritaire |
| Forge Design IoT | Interface de lecture (futur) | à créer |

Forge IoT est un **module opt-in** au même titre que `forge-mvc-rbac`,
`forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-mfa`,
`forge-mvc-media`. Voir [ADR-004 — Périmètre core](../adr/004-core-perimeter.md)
et [ADR-005 — Packaging](../adr/005-packaging.md).

## Architecture générale

```text
ESP32 / Arduino / capteurs
        │
        │  publish MQTT
        ▼
   Mosquitto  ou  broker MQTT cloud
        │
        │  subscribe MQTT
        ▼
   forge-mvc-iot
        │
        │  écrit / lit
        ▼
   Forge Core
   ├── stockage (MariaDB via core.database)
   ├── API HTTP JSON (routes exposées par le module IoT)
   └── diagnostics (forge doctor, logs)
        │
        │  lit via HTTP JSON
        ▼
   Forge Design IoT
   ├── liste des devices
   ├── flux d'événements
   ├── tableau de bord
   └── diagnostics
```

## Rôle de Forge Core

Forge Core (`forge-mvc`) :

- fournit le runtime HTTP, le routeur, les middlewares, les sessions,
  l'accès base de données (`core.database.db.fetch_one` / `fetch_all` /
  `execute` / `insert`) ;
- expose les conventions (entités, modèles, vues, contrôleurs) que le
  module IoT réutilisera ;
- **ne contient aucune logique IoT spécifique** : pas de connaissance
  de MQTT, pas de table d'événements capteur, pas de notion de
  « device », pas de dépendance à `paho-mqtt`.

Forge Core ne dépend jamais de `forge-mvc-iot`.

## Rôle du module `forge-mvc-iot`

Le futur paquet `forge-mvc-iot` (à scaffolder dans le ticket
[IOT-PACKAGE-SCAFFOLD-001](#tickets-suivants)) :

- déclare ses propres dépendances runtime (au minimum `paho-mqtt`) ;
- expose un **subscriber MQTT** qui se branche sur un broker configuré ;
- définit le **contrat de message** (topics, payload JSON, champs
  attendus) — voir [IOT-MQTT-CONTRACT-001](#tickets-suivants) ;
- persiste les événements reçus dans une table dédiée gérée par le
  module (pas dans une table inventée côté Forge Core) ;
- expose des **routes HTTP JSON** Forge pour lire devices et événements ;
- fournit éventuellement une commande CLI `forge iot:*` (diagnostics,
  test de connexion broker, etc.) ;
- s'installe via `pip install forge-mvc-iot` — Forge Core reste
  utilisable sans cette dépendance.

`forge-mvc-iot` dépend de Forge Core, jamais l'inverse.

## Rôle du broker MQTT

Le broker MQTT est le **transport** entre les capteurs et le serveur :

- il reçoit les messages publiés par les périphériques (ESP32, Arduino,
  Raspberry Pi, simulateurs) ;
- il les distribue aux abonnés (`forge-mvc-iot`, mais aussi tout autre
  client compatible) ;
- il **ne devient pas la source métier officielle** — c'est-à-dire que
  la vérité affichable côté interface n'est pas « ce qu'il y a en ce
  moment sur le broker », mais « ce que Forge a accepté, persisté et
  exposé via son API ».

Cette distinction est volontaire : le broker peut perdre des messages,
être redémarré, ou héberger plusieurs systèmes. La source canonique
exploitable côté Forge Design IoT est l'**API Forge**, pas le broker.

## Rôle de Mosquitto

Mosquitto est le broker MQTT recommandé en environnement local :

- libre, léger, installable sur Linux (`apt install mosquitto`), Windows
  (via WSL ou natif), macOS, Raspberry Pi, ESP32 (côté client) ;
- adapté aux usages pédagogiques BTS CIEL : pas de compte cloud à créer,
  pas de quota, exécution sur la machine du formateur ou un Raspberry
  partagé ;
- documentation et outillage matures (`mosquitto_pub`, `mosquitto_sub`,
  configuration TLS facultative).

Forge IoT documentera comment configurer Mosquitto pour un atelier
type ; il **ne l'intégrera pas comme dépendance Python**.

## Broker cloud : option possible mais non prioritaire

Les brokers MQTT hébergés (HiveMQ Cloud, EMQX Cloud, AWS IoT Core,
Azure IoT Hub, Adafruit IO, …) restent **utilisables** : `forge-mvc-iot`
acceptera une configuration broker générique (host, port, TLS, login,
mot de passe).

Ils ne sont **pas la cible prioritaire** parce que :

- ils introduisent un compte externe, un quota, parfois un coût ;
- ils compliquent les ateliers BTS CIEL (latence Internet, filtrage
  réseau lycée, comptes formateurs à gérer) ;
- la doctrine Forge privilégie un poste de travail autonome.

Le module IoT doit fonctionner identiquement avec Mosquitto local ou un
broker cloud — c'est un contrat de configuration, pas un branchement
spécial.

## Rôle de Forge Design IoT

Forge Design IoT est la future interface graphique de lecture du flux
IoT. Décision verrouillée par ce ticket :

> **Forge Design IoT ne lit pas directement le broker MQTT.
> Forge Design IoT consomme uniquement les API HTTP JSON exposées par
> Forge (via `forge-mvc-iot`).**

Conséquences :

- Forge Design IoT n'embarque pas de client MQTT ;
- Forge Design IoT n'a pas besoin des identifiants du broker ;
- la définition des contrats de données (devices, événements, types de
  mesure) reste pilotée par `forge-mvc-iot`, pas par Forge Design ;
- Forge Design IoT peut être réécrit, remplacé, ou doublé d'une autre
  interface sans changer le périmètre Forge.

## Flux de données

Trajectoire d'un message capteur :

1. Un capteur ESP32 publie sur un topic MQTT (ex. `forge/iot/devices/esp32-01/temp`).
2. Le broker (Mosquitto local ou broker cloud) reçoit le message.
3. Le subscriber de `forge-mvc-iot` est abonné aux topics pertinents ;
   il reçoit le payload JSON.
4. `forge-mvc-iot` valide le payload contre le contrat de message
   ([IOT-MQTT-CONTRACT-001](#tickets-suivants)).
5. Si valide, l'événement est persisté en base via les API Forge
   (`core.database.db.insert(...)`).
6. Une route HTTP JSON Forge expose la lecture des événements et des
   devices.
7. Forge Design IoT (ou tout autre client HTTP) interroge cette route,
   pas le broker.

## Règles de séparation

Règles non négociables, à verrouiller par les tickets suivants :

1. **Forge Core ne dépend pas de `forge-mvc-iot`.**
   Forge sans IoT reste fonctionnel à 100 %.
2. **`forge-mvc-iot` dépend de Forge Core.**
   Le module réutilise routeur, contrôleurs, accès base, conventions.
3. **`forge-mvc-iot` est opt-in.**
   Installation explicite ; aucun extra automatique sur `forge-mvc`.
4. **Forge Design IoT lit l'API Forge.**
   Pas de client MQTT côté interface ; pas d'accès direct au broker.
5. **Le broker MQTT n'est pas la source métier.**
   La source canonique exploitable côté interface est l'API Forge.
6. **Pas de logique IoT spécifique dans `core/`.**
   Aucune table « device », aucun champ MQTT, aucun constant capteur.
7. **Le SQL reste visible.**
   Conformément à la charte v2 §5 « Garder SQL visible », la table
   d'événements et ses requêtes restent lisibles, pas générées
   silencieusement par un ORM.
8. **Une API publique est un contrat de complétude.**
   Charte v2 §10 — le contrat MQTT et les routes HTTP IoT seront
   spécifiés explicitement avant écriture du code.

## Limites assumées

Ce ticket fixe le cadre. Il **n'aborde pas** :

- les protocoles autres que MQTT (CoAP, HTTP direct depuis capteur,
  LoRaWAN, Modbus, OPC-UA) — peuvent être traités par des modules
  séparés ultérieurs, hors `forge-mvc-iot` ;
- la sécurité réseau (TLS, certificats client, ACL Mosquitto) — sera
  spécifiée dans [IOT-CONFIG-001](#tickets-suivants) ;
- l'agrégation, le downsampling et la rétention long terme — à arbitrer
  après [IOT-STORAGE-EVENTS-001](#tickets-suivants) ;
- les commandes descendantes (Forge → capteur via MQTT publish) — la
  première itération est en lecture seule (capteurs → Forge) ;
- les graphiques temps réel côté Forge Design IoT — dépendent de
  [FORGE-DESIGN-IOT-READ-API-001](#tickets-suivants).

## Tickets suivants

La suite logique de cette trajectoire IoT, dans l'ordre recommandé :

| Ticket | Sujet |
|--------|-------|
| `IOT-PACKAGE-SCAFFOLD-001` | Création de `packages/forge-mvc-iot/` (`pyproject.toml`, `__init__.py`, structure conforme à ADR-005) |
| `IOT-MQTT-CONTRACT-001` | Contrat de message MQTT : topics, payload JSON, champs requis |
| `IOT-MQTT-SUBSCRIBER-001` | Subscriber `paho-mqtt`, gestion reconnexion, intégration boucle Forge |
| `IOT-CONFIG-001` | Variables d'environnement (`IOT_BROKER_HOST`, TLS, login/mot de passe), schéma `env/example` |
| `IOT-STORAGE-EVENTS-001` | Table SQL des événements IoT, migration versionnée, modèle applicatif |
| `IOT-HTTP-API-001` | Routes HTTP JSON Forge : liste devices, lecture événements, filtres |
| `IOT-DOCTOR-001` | `forge iot:doctor` — vérification config broker, ping, sub test |
| `IOT-STARTER-MQTT-HELLO-001` | Starter pédagogique « Hello MQTT » : ESP32 simulé + lecture côté Forge |
| `FORGE-DESIGN-IOT-READ-API-001` | Forge Design IoT consomme uniquement l'API Forge — pas le broker |

Aucun de ces tickets n'est ouvert par le présent document. Ils servent
de jalons et de garde-fous : tant qu'ils n'ont pas été livrés et
documentés, `forge-mvc-iot` n'existe pas.
