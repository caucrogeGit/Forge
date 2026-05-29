# Configuration Forge IoT

> **Statut** : itération 1 — contrat de configuration sans connexion
> broker. Aucun subscriber MQTT n'est encore instancié à partir de cet
> objet ; voir [Architecture Forge IoT](architecture.md) et le ticket
> `IOT-MQTT-SUBSCRIBER-001` pour la suite.

## Objectif

Définir comment `forge-mvc-iot` lit sa configuration MQTT à partir de
l'environnement, **avant** d'écrire le subscriber. L'objectif est
d'isoler les questions « où va-t-on lire host/port/topic ? » des
questions « comment se connecter au broker ? ».

## Variables d'environnement

| Variable | Défaut | Vide accepté ? | Type cible |
|----------|--------|----------------|------------|
| `FORGE_IOT_MQTT_HOST` | `localhost` | non — `ValueError` | `str` |
| `FORGE_IOT_MQTT_PORT` | `1883` | oui (revient au défaut) | `int` (1..65535) |
| `FORGE_IOT_MQTT_TOPIC` | `forge/+/+/telemetry` | non — `ValueError` | `str` |
| `FORGE_IOT_MQTT_CLIENT_ID` | `forge-iot` | oui (revient au défaut) | `str` |
| `FORGE_IOT_MQTT_USERNAME` | `None` | oui (= `None`) | `str | None` |
| `FORGE_IOT_MQTT_PASSWORD` | `None` | oui (= `None`) | `str | None` |
| `FORGE_IOT_API_TOKEN` | `None` | oui (= `None`) | `str | None` |
| `FORGE_IOT_MQTT_TLS_ENABLED` | `false` | oui (= `false`) | `bool` |
| `FORGE_IOT_MQTT_TLS_CA_FILE` | `None` | oui (= `None`) | `str | None` |

`FORGE_IOT_API_TOKEN` protège l'[API HTTP](http-api.md#protection-par-bearer-token) :
**absent ou vide** → API ouverte (parcours local) ; **défini** →
`Authorization: Bearer <token>` exigé sur les routes `/api/iot/*`. Comme
le mot de passe MQTT, il est **masqué** dans `repr(IotConfig)`.

Les valeurs par défaut sont **locales et pédagogiques** : un
[Mosquitto](architecture.md#role-de-mosquitto) installé sur la même
machine (`localhost:1883`) écoute sur tous les topics compatibles avec
le [contrat MQTT](mqtt-contract.md).

Le topic par défaut `forge/+/+/telemetry` utilise les wildcards MQTT
`+` (single-level) pour s'abonner à *toutes* les paires
`site`/`device_id` sous `forge/.../telemetry`. C'est l'inverse du
contrat de publication, où `+` est interdit.

## TLS MQTT (préparation)

Deux variables préparent **MQTT over TLS** (port broker `8883` en usage
réel, certificat CA) :

| Variable | Rôle |
|----------|------|
| `FORGE_IOT_MQTT_TLS_ENABLED` | active TLS — `true`/`1`/`yes`/`on` (insensible à la casse) → activé ; `false`/`0`/`no`/`off` ou vide → désactivé ; toute autre valeur → `ValueError`. |
| `FORGE_IOT_MQTT_TLS_CA_FILE` | chemin du certificat **CA** qui valide le broker (ex. `/etc/ssl/certs/mosquitto-ca.crt`). Optionnel au niveau config, **recommandé** en usage réel. Vide → `None`. |

Règles :

- **Pour un Mosquitto local pédagogique, TLS reste désactivé** (`false`,
  le défaut) : on continue d'utiliser `localhost:1883` en clair. Voir
  [Mosquitto local](mosquitto-local.md).
- **Pour un broker exposé sur le réseau, TLS doit être préparé** :
  `FORGE_IOT_MQTT_TLS_ENABLED=true`, un `FORGE_IOT_MQTT_TLS_CA_FILE`
  pointant vers le CA du broker, et le port `8883`.
- Le chemin du fichier CA est **masqué** dans `repr(IotConfig)` (comme le
  mot de passe et le token), pour ne pas exposer de chemin sensible dans
  les logs ; les clients le lisent via l'attribut.

!!! success "TLS branché dans les clients (IOT-MQTT-TLS-CLIENTS-001)"
    `FORGE_IOT_MQTT_TLS_ENABLED=true` est désormais **réellement
    consommé** par `forge iot:doctor --mqtt`, `forge iot:listen` (via le
    `MqttSubscriber`) et `forge iot:simulate` : le client paho appelle
    `client.tls_set(...)` avant de se connecter (`ca_certs` = le fichier
    CA si fourni, sinon les certificats système). Le **port n'est pas
    forcé** : pour un broker TLS, configure aussi `FORGE_IOT_MQTT_PORT`
    (généralement `8883`). Hors périmètre : pas de certificat client
    (mTLS), pas de `tls_insecure_set`.

```env
# Broker exposé sur le réseau, MQTT over TLS
FORGE_IOT_MQTT_HOST=mqtt.example.net
FORGE_IOT_MQTT_PORT=8883
FORGE_IOT_MQTT_TLS_ENABLED=true
FORGE_IOT_MQTT_TLS_CA_FILE=/etc/ssl/certs/mosquitto-ca.crt
```

```bash
export FORGE_IOT_MQTT_HOST="mqtt.example.net"
export FORGE_IOT_MQTT_PORT="8883"
export FORGE_IOT_MQTT_TLS_ENABLED="true"
export FORGE_IOT_MQTT_TLS_CA_FILE="/etc/ssl/certs/mosquitto-ca.crt"

forge iot:doctor --mqtt
```

## API Python

### `IotConfig`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class IotConfig:
    mqtt_host: str
    mqtt_port: int
    mqtt_topic: str
    mqtt_client_id: str
    mqtt_username: str | None
    mqtt_password: str | None
    api_token: str | None = None
    mqtt_tls_enabled: bool = False
    mqtt_tls_ca_file: str | None = None
```

Les champs avec défaut (`api_token`, `mqtt_tls_enabled`,
`mqtt_tls_ca_file`) garantissent la **compatibilité ascendante** : les
instanciations historiques à 6 champs restent valides.

L'objet est immuable (`frozen=True`) — le subscriber qui le reçoit ne
peut pas le modifier par effet de bord.

### `load_iot_config()`

```python
from collections.abc import Mapping
from forge_mvc_iot.config import IotConfig, load_iot_config

# Lecture depuis os.environ
cfg: IotConfig = load_iot_config()

# Lecture depuis un mapping injecté (utile pour les tests)
cfg = load_iot_config({"FORGE_IOT_MQTT_HOST": "broker.lan"})
```

- `env=None` (défaut) → lit `os.environ`.
- `env=mapping` → lit le mapping fourni, sans toucher à
  `os.environ`. C'est le point d'injection pour les tests ; aucune
  variable d'environnement réelle n'est nécessaire.

### Erreurs levées

`load_iot_config` lève `ValueError` dans les cas suivants :

| Cas | Message indicatif |
|-----|-------------------|
| `FORGE_IOT_MQTT_HOST` présent mais vide | `FORGE_IOT_MQTT_HOST ne peut pas être vide` |
| `FORGE_IOT_MQTT_PORT` non convertible en entier | `FORGE_IOT_MQTT_PORT doit être un entier (vu : '...')` |
| `FORGE_IOT_MQTT_PORT` hors plage `1..65535` | `FORGE_IOT_MQTT_PORT hors plage 1-65535 (vu : ...)` |
| `FORGE_IOT_MQTT_TOPIC` présent mais vide | `FORGE_IOT_MQTT_TOPIC ne peut pas être vide` |

Les autres erreurs (broker indisponible, payload invalide, etc.)
n'appartiennent pas à ce contrat : elles seront traitées par le
subscriber.

## Masquage du mot de passe

Le `repr()` d'un `IotConfig` ne révèle jamais le mot de passe en
clair :

```python
>>> cfg = load_iot_config({
...     "FORGE_IOT_MQTT_USERNAME": "forge",
...     "FORGE_IOT_MQTT_PASSWORD": "s3cr3t",
... })
>>> repr(cfg)
"IotConfig(mqtt_host='localhost', mqtt_port=1883, mqtt_topic='forge/+/+/telemetry', mqtt_client_id='forge-iot', mqtt_username='forge', mqtt_password='***')"
```

Si le mot de passe est `None` (pas d'authentification), le champ
apparaît tel quel — il n'y a rien à protéger.

Cette protection couvre :

- les traces d'exception affichées au démarrage ;
- les logs qui sérialisent l'objet via `repr()` ou `f"{cfg!r}"` ;
- les sorties `pprint` et la plupart des outils de debug.

Elle ne couvre **pas** un accès direct à l'attribut
(`cfg.mqtt_password`) — c'est volontaire : le subscriber a besoin de
la valeur en clair pour s'authentifier.

## Exemples d'environnement

### Développement local (Mosquitto sans auth)

```env
# env/dev
FORGE_IOT_MQTT_HOST=localhost
FORGE_IOT_MQTT_PORT=1883
FORGE_IOT_MQTT_TOPIC=forge/+/+/telemetry
FORGE_IOT_MQTT_CLIENT_ID=forge-iot-dev
```

Pas d'identifiants nécessaires : Mosquitto local accepte les
connexions anonymes par défaut.

### Broker MQTT avec authentification

```env
FORGE_IOT_MQTT_HOST=broker.lan
FORGE_IOT_MQTT_PORT=1883
FORGE_IOT_MQTT_TOPIC=forge/atelier/+/telemetry
FORGE_IOT_MQTT_CLIENT_ID=forge-iot-atelier
FORGE_IOT_MQTT_USERNAME=forge
FORGE_IOT_MQTT_PASSWORD=motdepassefort
```

Le topic est ici restreint au site `atelier` — utile pour qu'une
instance Forge IoT n'écoute qu'un périmètre précis.

### Broker MQTT cloud

```env
FORGE_IOT_MQTT_HOST=mqtt.example.com
FORGE_IOT_MQTT_PORT=1883
FORGE_IOT_MQTT_TOPIC=forge/+/+/telemetry
FORGE_IOT_MQTT_CLIENT_ID=forge-iot-prod
FORGE_IOT_MQTT_USERNAME=forge-prod
FORGE_IOT_MQTT_PASSWORD=...
```

Aucun branchement spécial n'est nécessaire — le contrat est identique
à un broker local. Pour un broker exposé, ajoute la
[préparation TLS](#tls-mqtt-preparation) (`FORGE_IOT_MQTT_TLS_ENABLED`,
`FORGE_IOT_MQTT_TLS_CA_FILE`, port `8883`). Le câblage TLS effectif des
clients et les certificats client (mTLS) restent à venir
(voir [Limites](#limites-iteration-1)).

## Limites itération 1

Sont explicitement **hors périmètre** :

- pas de lecture automatique de `env/dev` ou `.env` — c'est l'appelant
  qui charge ces fichiers en amont (par exemple via `python-dotenv` ou
  `forge_cli.config.load_env()`) ;
- TLS est branché dans les clients (`IOT-MQTT-TLS-CLIENTS-001`) via
  `client.tls_set` ; restent **hors périmètre** : le certificat client
  (mTLS), la génération de certificats, `tls_insecure_set` et la
  configuration serveur Mosquitto TLS complète ;
- pas de ACL Mosquitto — gestion côté broker, hors Forge ;
- pas de gestion de secrets externes (Vault, AWS Secrets Manager) — la
  config se contente de lire un mapping `str → str` ;
- pas de validation runtime du topic vs contrat MQTT (le pattern
  `forge/+/+/telemetry` est accepté tel quel par Forge IoT, qui
  s'abonne « bêtement » au topic fourni) ;
- pas de connexion au broker — aucune dépendance `paho-mqtt`.

Toute extension passera par un ticket `IOT-CONFIG-NNN` ultérieur, sans
casser le contrat actuel.

## Tickets suivants

Ce contrat de configuration débloque :

- `IOT-MQTT-SUBSCRIBER-001` — le subscriber `paho-mqtt` reçoit un
  `IotConfig` en argument et n'a plus à connaître les variables
  d'environnement ;
- `IOT-DOCTOR-001` — `forge iot:doctor` affichera la configuration
  effective (avec mot de passe masqué) avant de tester la connexion ;
- `IOT-CONFIG-TLS-001` (**livré**) — a étendu `IotConfig` avec
  `mqtt_tls_enabled` / `mqtt_tls_ca_file`, sans changer les défauts
  existants (TLS désactivé par défaut) ;
- `IOT-MQTT-TLS-CLIENTS-001` (**livré**) — branche réellement TLS dans
  `forge iot:doctor --mqtt`, `forge iot:listen` et `forge iot:simulate`
  (via le helper `forge_mvc_iot.mqtt.tls.configure_tls` → `client.tls_set`,
  appelé avant `connect`).

Voir [Architecture Forge IoT](architecture.md#tickets-suivants) pour
la liste complète des jalons.
