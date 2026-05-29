# Mosquitto local pour Forge IoT

> **Statut** : page pédagogique. Elle explique comment installer, lancer
> et **tester** un broker Mosquitto **local** pour faire tourner le flux
> Forge IoT de bout en bout. Le broker est volontairement **en clair sur
> `localhost:1883`**, sans TLS ni authentification — voir
> [Limites](#limites).

## Objectif

Mettre en place le broker MQTT manquant, puis dérouler le flux complet
désormais disponible :

```text
Mosquitto local
   ↓
forge iot:doctor --mqtt     # le broker répond ?
   ↓
forge iot:listen            # écouter et stocker (terminal 1)
   ↓
forge iot:simulate          # publier des mesures (terminal 2)
   ↓
iot_events                  # stockage
   ↓
/api/iot/events             # lecture HTTP (terminal 3)
```

Cette page cible un poste **Linux / WSL / Debian / Ubuntu**. Pour
dérouler ce flux d'un coup, voir le
[smoke test local](local-smoke-test.md).

## Installer Mosquitto

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
```

Le paquet `mosquitto` fournit le broker ; `mosquitto-clients` fournit
`mosquitto_pub` et `mosquitto_sub`, utiles pour publier et écouter à la
main.

## Démarrer le service

```bash
sudo systemctl enable --now mosquitto
sudo systemctl status mosquitto
```

`enable --now` active Mosquitto au démarrage **et** le lance tout de
suite. `status` doit afficher `active (running)`.

## Vérifier que Mosquitto écoute

Mosquitto écoute par défaut sur le port **1883** :

```bash
ss -tulpn | grep 1883
```

Une ligne contenant `127.0.0.1:1883` (ou `0.0.0.0:1883`) confirme l'écoute.
Si **rien ne sort**, Mosquitto n'écoute pas — voir
[Erreurs fréquentes](#erreurs-frequentes).

## Vérifier Forge IoT avec doctor

```bash
forge iot:doctor          # package, config, migration, API HTTP
forge iot:doctor --mqtt   # connexion brève au broker
```

Quand Mosquitto tourne :

```text
  [OK]    broker MQTT — connexion réussie à localhost:1883
```

Détail : [Diagnostic Forge IoT](doctor.md).

## Initialiser la table IoT

Le subscriber stocke les mesures dans `iot_events`. Crée la table une
fois pour toutes :

```bash
forge iot:init            # copie la migration vers mvc/migrations/
forge migration:apply     # crée la table iot_events en base
forge iot:doctor --db     # confirme que la table est lisible
```

Détail : [Initialisation (iot:init)](init-command.md).

## Lancer l'écoute Forge

Dans un **premier terminal**, lance l'écoute (laisse tourner) :

```bash
forge iot:listen
```

Forge s'abonne au topic configuré et insère chaque mesure reçue.
Détail : [Écoute (iot:listen)](listen-command.md).

## Publier une mesure simulée

Dans un **second terminal**, publie des mesures factices conformes :

```bash
forge iot:simulate --count 3 --interval 1
```

Trois lignes `[OK]` doivent apparaître dans le terminal `forge iot:listen`.
Détail : [Simulateur (iot:simulate)](simulator.md).

## Lire les événements via l'API HTTP

Dans un **troisième terminal** (l'application Forge tournant via
`forge run`), relis les mesures stockées :

```bash
curl http://localhost:8000/api/iot/events
```

Détail : [API HTTP IoT](http-api.md).

## Tester avec `mosquitto_sub`

Pour observer le trafic MQTT brut, sans Forge, abonne-toi au motif de
topic et laisse tourner :

```bash
mosquitto_sub -h localhost -t 'forge/+/+/telemetry' -v
```

- les `+` sont des jokers MQTT (un niveau chacun) : n'importe quel `site`
  et `device_id` ;
- `-v` affiche le topic **et** le payload de chaque message.

## Publier manuellement avec `mosquitto_pub`

Pour comprendre exactement ce que Forge publie, envoie un message à la
main :

```bash
mosquitto_pub -h localhost \
  -t 'forge/atelier/esp32-001/telemetry' \
  -m '{"kind":"temperature","value":22.4,"unit":"°C","timestamp":"2026-05-29T10:00:00Z"}'
```

Le message doit apparaître dans `mosquitto_sub` **et**, si
`forge iot:listen` tourne, être inséré dans `iot_events`. Pour publier
depuis un vrai microcontrôleur, voir l'[exemple ESP32](esp32-example.md).

## Erreurs fréquentes

### Broker arrêté (`ConnectionRefusedError`)

Si `forge iot:doctor --mqtt`, `forge iot:listen` ou `forge iot:simulate`
échoue avec une connexion refusée, le broker n'est pas démarré :

```bash
sudo systemctl start mosquitto
```

### Port 1883 absent

```bash
ss -tulpn | grep 1883
```

Si rien ne sort, Mosquitto **n'écoute pas** : vérifie
`sudo systemctl status mosquitto` et `journalctl -u mosquitto`.

### Table IoT absente (`iot_storage_not_ready`)

Si `forge iot:listen` ou l'API HTTP signale que le stockage n'est pas
prêt, la table n'existe pas encore :

```bash
forge iot:init
forge migration:apply
forge iot:doctor --db
```

### Topic invalide

Le contrat impose **exactement** :

```text
forge/{site}/{device_id}/telemetry
```

Exemples **refusés** par le subscriber et par `forge iot:simulate` :

```text
forge/atelier/esp32-001            # niveau /telemetry manquant
atelier/esp32-001/telemetry        # préfixe forge/ manquant
forge/Atelier/esp32-001/telemetry  # majuscule interdite
```

Exemple **correct** :

```text
forge/atelier/esp32-001/telemetry
```

Voir le [contrat MQTT](mqtt-contract.md).

### Payload invalide

Le payload JSON doit contenir au minimum les quatre champs obligatoires :

- `kind` (type de mesure) ;
- `value` (nombre) ;
- `unit` (unité) ;
- `timestamp` (ISO 8601 UTC, suffixe `Z`).

Un champ manquant ou un `timestamp` sans `Z` est rejeté. Le champ
`metadata` est optionnel.

## Limites

Cette page documente **uniquement** un broker local pédagogique. Les
sujets suivants sont **hors périmètre** de cette page et feront l'objet
de tickets ultérieurs :

- **TLS** (chiffrement du transport, port 8883) — non couvert ici, hors périmètre ;
- **authentification** Mosquitto (utilisateurs, mots de passe, ACL) — non couverte ici, hors périmètre ;
- brokers **cloud** MQTT, Docker Compose, VPN Tailscale, capteurs ESP32 / Arduino, Forge Design — hors périmètre.

Le broker décrit ici écoute en clair sur `localhost:1883`, sans TLS ni auth ni cloud — adapté à un atelier local, pas à une mise en production.

Cette page reste **volontairement sans TLS ni authentification** : le chiffrement TLS et son certificat CA sont **hors périmètre** ici, et restent désactivés par défaut côté Forge ; pour un broker exposé, voir [Configuration Forge IoT — TLS MQTT](configuration.md#tls-mqtt-preparation).
