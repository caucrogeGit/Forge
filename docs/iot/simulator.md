# Simulateur Forge IoT — `forge iot:simulate`

> **Statut** : outil **pédagogique**. Il publie des mesures factices
> mais **conformes au contrat MQTT Forge IoT** vers le broker configuré,
> sans capteur physique. Il ne lance pas le subscriber, n'écrit pas en
> base et n'appelle pas l'API HTTP.

## Objectif

Permettre de tester le **flux complet** sans matériel :

```text
forge iot:doctor --mqtt   # 1. le broker répond ?
        ↓
forge iot:simulate        # 2. publier des mesures factices
        ↓
subscriber MQTT           # 3. consommer (à brancher côté application)
        ↓
iot_events                # 4. stockage
        ↓
/api/iot/events           # 5. lecture HTTP
```

Le simulateur couvre **uniquement l'étape 2** : la publication. Les
étapes 3 à 5 relèvent du subscriber, du stockage et de l'API HTTP, déjà
documentés ailleurs dans cette section.

## Usage

```bash
forge iot:simulate
```

Publie **une** mesure par défaut sur le topic
`forge/atelier/esp32-001/telemetry` :

```json
{
  "kind": "temperature",
  "value": 22.4,
  "unit": "°C",
  "timestamp": "2026-05-29T10:00:00Z",
  "metadata": {
    "source": "forge-iot-simulator"
  }
}
```

Le `timestamp` est toujours en UTC avec suffixe `Z`, généré à la
publication.

Aide via :

```bash
forge iot:simulate --help
```

## Options

| Option | Défaut | Description |
|--------|--------|-------------|
| `--profile <nom>` | _(aucun)_ | Profil pédagogique : `temperature`, `humidity`, `presence`, `energy`. Fournit des défauts `kind`/`value`/`unit`. |
| `--site <slug>` | `atelier` | Site (slug `[a-z0-9-]+`). |
| `--device <slug>` | `esp32-001` | Identifiant capteur (slug `[a-z0-9-]+`). |
| `--kind <slug>` | `temperature` | Type de mesure (slug `[a-z0-9_-]+`). |
| `--value <nombre>` | `22.4` | Valeur mesurée. |
| `--unit <texte>` | `°C` | Unité. |
| `--count <n>` | `1` | Nombre de messages, borné **1..1000**. |
| `--interval <s>` | `1` | Délai entre messages, borné **0..60** s. |

Exemples :

```bash
forge iot:simulate --site atelier --device esp32-001
forge iot:simulate --kind humidity --value 55 --unit %
forge iot:simulate --count 10 --interval 1
```

## Profils de simulation

Plutôt que de retenir les bonnes valeurs `--kind`/`--value`/`--unit` pour
chaque type de mesure, un **profil** les fournit d'un coup. Pratique pour
construire des exercices sans capteur réel :

```bash
forge iot:simulate --profile temperature --count 5
forge iot:simulate --profile humidity --count 5
forge iot:simulate --profile presence --count 5
forge iot:simulate --profile energy --count 5
```

| Profil | `kind` | `value` | `unit` | Note |
|--------|--------|---------|--------|------|
| `temperature` | `temperature` | `22.4` | `°C` | température ambiante |
| `humidity` | `humidity` | `55.0` | `%` | humidité relative |
| `presence` | `presence` | `1.0` | `state` | `0` = absence, `1` = présence |
| `energy` | `energy` | `120.5` | `W` | puissance instantanée |

Quand un profil est actif, le payload porte `metadata.profile` :

```json
{
  "kind": "temperature",
  "value": 22.4,
  "unit": "°C",
  "timestamp": "2026-05-29T10:00:00Z",
  "metadata": {
    "source": "forge-iot-simulator",
    "profile": "temperature"
  }
}
```

Un profil ne fournit que des **défauts** : `--kind`, `--value` et
`--unit` peuvent encore les surcharger explicitement, quel que soit leur
ordre :

```bash
forge iot:simulate --profile temperature --value 24.8
forge iot:simulate --profile humidity --unit "g/m³"
```

Un profil inconnu est rejeté (exit code 2) :

```text
[ERREUR] Profil inconnu : unknown
Profils disponibles : temperature, humidity, presence, energy
```

Sans `--profile`, le comportement est **inchangé** (température simple,
`metadata` sans `profile`).

## Conformité au contrat

Le simulateur valide chaque message contre le contrat
[`forge/{site}/{device_id}/telemetry`](mqtt-contract.md) **avant** de se
connecter au broker. Une option hors slug est donc rejetée proprement,
sans ouvrir de socket :

```text
[ERREUR] message non conforme au contrat MQTT — Topic invalide : 'forge/Atelier/esp32-001/telemetry' (...)
```

C'est volontaire : on ne publie **que** des messages que le subscriber
Forge IoT saura parser.

## Sortie exemple

```text
[INFO] publication de 3 mesure(s) vers localhost:1883
[OK] publié 1/3 → forge/atelier/esp32-001/telemetry (temperature=22.4°C)
[OK] publié 2/3 → forge/atelier/esp32-001/telemetry (temperature=22.4°C)
[OK] publié 3/3 → forge/atelier/esp32-001/telemetry (temperature=22.4°C)
[OK] 3 mesure(s) publiée(s).
```

Le mot de passe MQTT n'apparaît **jamais** dans la sortie, même quand un
username/password est configuré (il est transmis au broker, pas affiché).

## Connexion TLS

`forge iot:simulate` consomme la configuration TLS : si
`FORGE_IOT_MQTT_TLS_ENABLED=true`, le client appelle `client.tls_set(...)`
avant de se connecter (`ca_certs` = `FORGE_IOT_MQTT_TLS_CA_FILE` si
fourni, sinon les certificats système). Pense à configurer aussi le port
TLS du broker (généralement `8883`) :

```bash
export FORGE_IOT_MQTT_HOST="mqtt.example.net"
export FORGE_IOT_MQTT_PORT="8883"
export FORGE_IOT_MQTT_TLS_ENABLED="true"
export FORGE_IOT_MQTT_TLS_CA_FILE="/etc/ssl/certs/mosquitto-ca.crt"

forge iot:simulate --profile temperature --count 3
```

Le chemin du CA n'apparaît jamais dans la sortie. Détails :
[Configuration — TLS MQTT](configuration.md#tls-mqtt-preparation).

## Codes de sortie

| Code | Signification |
|------|---------------|
| `0` | Publication réussie. |
| `2` | Option invalide (valeur manquante, hors plage, message non conforme). |
| `1` | Configuration invalide ou échec de connexion / publication. |

En cas d'échec de connexion, le message reste sobre (type d'erreur, pas
de stacktrace) — lance d'abord `forge iot:doctor --mqtt` pour
diagnostiquer le broker.

## Parcours recommandé

Besoin d'un broker pour ces commandes ? Voir
[Mosquitto local](mosquitto-local.md) pour l'installer et le lancer.

```bash
forge iot:doctor --mqtt              # 1. confirmer que le broker répond
forge iot:simulate --count 3 --interval 1   # 2. publier 3 mesures
```

Côté consommation, lance [`forge iot:listen`](listen-command.md) dans un
autre terminal : il écoute le broker et insère les mesures reçues dans
`iot_events`. Tu peux ensuite les relire via `GET /api/iot/events`.

## Limites (hors périmètre)

- ne lance **pas** le subscriber, n'écrit **pas** en base, n'appelle
  **pas** l'API HTTP ;
- pas de `retain`, pas de QoS avancé, pas de downlink ;
- pas de capteur réel, pas de code embarqué ;
- QoS 0 uniquement — un message peut être perdu si le broker est
  saturé (acceptable pour un simulateur pédagogique).

## Tickets suivants

- `IOT-MOSQUITTO-LOCAL-DOCS-001` : documenter le lancement d'un
  Mosquitto local pour exécuter ce flux de bout en bout.
