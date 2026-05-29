# Évaluation Arduino R4 pour Forge IoT

> **Statut** : page d'**évaluation**, pas de support. Elle examine si
> l'Arduino R4 doit devenir une cible officiellement documentée pour
> Forge IoT, ou rester une note secondaire derrière l'ESP32. Aucun
> sketch complet n'est fourni ici : une cible officielle exige une
> validation matérielle réelle.

## Objectif

Décider, **avant** d'écrire un exemple complet, si l'Arduino R4 est une
cible MQTT fiable pour Forge IoT. On vérifie le modèle exact, la
connectivité réseau, la compatibilité des bibliothèques MQTT et l'intérêt
pédagogique — pour éviter de publier une documentation fragile ou fausse
selon la variante de carte.

## Pourquoi ESP32 reste la cible de référence

L'[exemple ESP32](esp32-example.md) reste la **cible de référence** Forge
IoT pour MQTT :

- Wi-Fi **intégré** et mature ;
- pile réseau bien supportée par `PubSubClient` et les bibliothèques MQTT
  courantes ;
- abondamment documenté pour un usage MQTT en BTS CIEL ;
- coût faible et disponibilité large.

Toute évaluation d'une autre carte se compare à cette référence.

## Identifier le modèle Arduino R4 exact

« Arduino R4 » recouvre plusieurs réalités. Avant tout test, identifier
précisément la variante :

- **Arduino UNO R4 WiFi** : intègre un module Wi-Fi (ESP32-S3 dédié à la
  connectivité). C'est la seule variante R4 pertinente pour MQTT sans
  matériel additionnel ;
- **Arduino UNO R4 Minima** (et variantes **sans Wi-Fi**) : pas de
  connectivité réseau intégrée — inadaptée à MQTT sans shield/module
  réseau externe.

La distinction est décisive : une bonne partie des « Arduino R4 » en
circulation **n'ont pas** de Wi-Fi.

## Cas Arduino R4 WiFi

Le modèle **UNO R4 WiFi** est, sur le papier, capable de :

- se connecter à un réseau Wi-Fi 2,4 GHz ;
- ouvrir une connexion TCP vers un broker MQTT ;
- publier sur un topic du contrat Forge IoT.

Mais la pile réseau diffère de l'ESP32 (bibliothèque `WiFiS3` côté R4),
et la compatibilité des bibliothèques MQTT doit être **vérifiée sur le
matériel réel** avant toute promesse.

## Cas Arduino R4 sans Wi-Fi

Les variantes **sans Wi-Fi** ne peuvent pas faire de MQTT directement :
MQTT exige une connectivité réseau. Sans module réseau externe, elles
sont **hors sujet** pour ce parcours. Pour ces cartes, on reste sur le
simulateur `forge iot:simulate` ou sur l'ESP32.

## Contraintes MQTT

Quelle que soit la carte, le contrat Forge IoT impose les mêmes règles :

- **MQTT nécessite une connectivité réseau** (Wi-Fi ou Ethernet) ;
- depuis la carte, **`localhost` ne désigne jamais le PC** : `localhost`
  désignerait la carte elle-même. L'adresse du broker doit être
  l'**adresse IP** du PC ou serveur qui héberge Mosquitto (ex.
  `192.168.1.222`) ;
- la **bibliothèque MQTT** doit être compatible avec la pile réseau
  utilisée (`WiFiS3` sur R4 WiFi, ≠ pile ESP32) ;
- le topic doit respecter `forge/{site}/{device_id}/telemetry`, par
  exemple :

```text
forge/atelier/arduino-r4-001/telemetry
```

avec un payload conforme :

```json
{
  "kind": "temperature",
  "value": 22.4,
  "unit": "°C",
  "timestamp": "2026-05-29T10:00:00Z"
}
```

## Ce qui est faisable

- tester ponctuellement un **UNO R4 WiFi** vers Mosquitto local ;
- réutiliser le **contrat** et le **flux Forge** identiques à l'ESP32
  (`forge iot:listen`, `forge iot:doctor --mqtt`, `/api/iot/events`) —
  côté serveur, rien ne change selon la carte émettrice.

## Ce qui est déconseillé

- promettre un support R4 **sans** validation matérielle réelle ;
- documenter un sketch R4 **complet** tant que la compatibilité MQTT +
  `WiFiS3` n'est pas vérifiée sur la carte ;
- viser les variantes R4 **sans Wi-Fi** pour du MQTT direct.

## Décision provisoire

- l'**ESP32 reste la cible de référence** Forge IoT pour MQTT ;
- l'**Arduino R4 peut être testé**, mais **ne devient pas encore une
  cible officielle** : Forge ne le supporte pas officiellement à ce jour ;
- un **exemple Arduino R4 complet** nécessite une **validation matérielle
  réelle** (UNO R4 WiFi + Mosquitto), pas seulement une lecture de
  documentation.

## Prochaines étapes possibles

- si un **UNO R4 WiFi** réel est validé contre Mosquitto avec une
  bibliothèque MQTT compatible → ticket `IOT-ARDUINO-R4-EXAMPLE-001`
  (exemple complet, sur le modèle de l'ESP32) ;
- sinon → conserver cette page comme **note pédagogique** et rester sur
  l'ESP32 et le simulateur.

Ce ticket **n'ajoute aucune dépendance Arduino à Forge** et ne modifie
aucun code fonctionnel : il pose seulement la décision.
