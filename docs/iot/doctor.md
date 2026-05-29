# Diagnostic Forge IoT — `forge iot:doctor`

> **Statut** : diagnostic **statique par défaut** (`IOT-DOCTOR-001`).
> Deux options activent des vérifications réseau / base de manière
> **explicite** : `--db` (test de la table `iot_events`,
> `IOT-DOCTOR-DB-001`) et `--mqtt` (connexion au broker MQTT,
> `IOT-DOCTOR-MQTT-001`). Sans option, le doctor ne touche ni au broker
> ni à la base, et n'importe ni `paho` ni `core.database`.

## Objectif

Donner un signal **avant** d'exécuter quoi que ce soit côté broker ou
base de données :

- le module `forge-mvc-iot` est bien installé ;
- la configuration `load_iot_config()` est cohérente ;
- la migration `iot_events` est shippée avec le package ;
- l'API HTTP est enregistrable (`register_iot_routes`).

C'est l'étape recommandée **avant** un starter pédagogique
(`IOT-STARTER-MQTT-HELLO-001`) ou un déploiement.

## Usage

```bash
forge iot:doctor             # diagnostic statique (sans réseau ni base)
forge iot:doctor --db        # + connexion MariaDB et SELECT COUNT(*) FROM iot_events
forge iot:doctor --mqtt      # + connexion brève au broker MQTT
forge iot:doctor --db --mqtt # les deux options sont cumulables
```

Aide via :

```bash
forge iot:doctor --help
```

Les options `--db` et `--mqtt` sont **explicites** : tant qu'elles ne
sont pas passées, aucune connexion réseau ou base n'est tentée.

## Vérifications

| # | Vérification | Statut possible | Activée par |
|---|--------------|-----------------|-------------|
| 1 | Package `forge-mvc-iot` importable (et version) | `ok` / `fail` | toujours |
| 2 | `load_iot_config()` chargeable, mot de passe masqué | `ok` / `fail` | toujours |
| 3 | Migration `*_create_iot_events.sql` présente dans le package | `ok` / `warn` | toujours |
| 4 | `register_iot_routes` exposée | `ok` / `fail` | toujours |
| 5 | Broker MQTT joignable | `skip` / `ok` / `fail` | `--mqtt` |
| 6 | Base `iot_events` accessible | `skip` / `ok` / `warn` / `fail` | `--db` |
| 7 | Schéma `iot_events` conforme au contrat | `ok` / `warn` / `fail` | `--db` (si table accessible) |

### Codes de sortie

| Statut | Comptabilisé | Effet sur le code de sortie |
|--------|--------------|-----------------------------|
| `ok` | succès | aucun |
| `skip` | info | aucun |
| `warn` | avertissement | aucun |
| `fail` | erreur | **exit 1** |

Le doctor exit 0 dès qu'aucun `fail` n'est remonté — un `warn` ou un
`skip` ne casse pas la CI.

## Sortie exemple — diagnostic statique

```text
Forge IoT doctor

  [OK]    package forge-mvc-iot — installé (version {{forge_version}})
  [OK]    configuration IoT — chargée
           mqtt_host       : localhost
           mqtt_port       : 1883
           mqtt_topic      : forge/+/+/telemetry
           mqtt_client_id  : forge-iot
           mqtt_username   : (none)
           mqtt_password   : (none)
  [OK]    migration iot_events — présente (20260528120000_create_iot_events.sql)
  [OK]    API HTTP IoT — register_iot_routes disponible
  [SKIP]  broker MQTT — non testé par défaut — passe --mqtt pour vérifier le broker
  [SKIP]  base iot_events — non testée par défaut — passe --db pour vérifier l'accès à la table

0 avertissement(s), 0 erreur(s), 2 info(s).
```

## Sortie exemple — avec `--db`

Table présente et schéma conforme :

```text
  [OK]    base iot_events — table accessible (42 événement(s))
  [OK]    schéma iot_events — conforme
```

Le contrôle de schéma (ligne 7) n'est lancé **que** si la table est
accessible — voir [Vérification du schéma `iot_events`](#verification-du-schema-iot_events).

Table absente (migration pas appliquée) :

```text
  [WARN]  base iot_events — table absente ou migration non appliquée
           Conseil : lance forge iot:init puis forge migration:apply
```

Le `--db` traite l'absence de table comme un **`warn`** (pas un `fail`) :
le module est installé correctement, c'est juste l'étape « apply »
qui manque. Exit code 0.

Connexion MariaDB impossible :

```text
  [FAIL]  base iot_events — connexion MariaDB impossible — OperationalError: Can't connect to MySQL server on 'localhost' (111)
```

Cas typiques : MariaDB pas démarré, mauvais host/port, identifiants
refusés, base inexistante. Exit code 1. Le mot de passe n'est jamais
inclus dans le message — les drivers MariaDB n'incluent que `using
password: YES/NO`, sans la valeur.

## Vérification du schéma `iot_events`

> **Statut** : `IOT-DOCTOR-SCHEMA-001`.

`forge iot:doctor --db` vérifie deux choses :

1. que la table `iot_events` est **accessible** (`SELECT COUNT(*)`) ;
2. que ses **colonnes principales** correspondent au contrat Forge IoT
   (types SQL, nullabilité, `AUTO_INCREMENT` de `id`).

Le contrôle de schéma s'appuie sur `INFORMATION_SCHEMA.COLUMNS` (plus
propre et plus testable qu'un parsing de `SHOW CREATE TABLE`). Il n'est
lancé **que si la table est accessible** : table absente ou connexion
impossible sont déjà signalées par la ligne précédente, sans bruit
redondant.

### Contrat vérifié

| Colonne | Type attendu | Nullabilité |
|---------|--------------|-------------|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT` | `NOT NULL` |
| `site` | `VARCHAR(64)` | `NOT NULL` |
| `device_id` | `VARCHAR(64)` | `NOT NULL` |
| `kind` | `VARCHAR(64)` | `NOT NULL` |
| `value` | `DOUBLE` | `NOT NULL` |
| `unit` | `VARCHAR(32)` | `NOT NULL` |
| `timestamp` | `VARCHAR(40)` | `NOT NULL` |
| `metadata_json` | `TEXT` | `NULL` |
| `received_at` | `DATETIME(6)` | `NOT NULL` |

Une colonne **supplémentaire** (non prévue par le contrat) est
**tolérée** : une migration future peut en ajouter sans casser le
contrat actuel. Les colonnes manquantes ou incompatibles sont le vrai
problème.

### Exemple — schéma conforme

```bash
forge iot:doctor --db
```

```text
  [OK]    base iot_events — table accessible (0 événement(s))
  [OK]    schéma iot_events — conforme
```

Exit code 0.

### Exemple — colonne manquante

```text
  [WARN]  schéma iot_events — colonne manquante : metadata_json
           Conseil : vérifie la migration Forge IoT ou recrée la table dans un environnement de test.
```

### Exemple — type inattendu

```text
  [WARN]  schéma iot_events — type inattendu pour value : attendu DOUBLE, obtenu VARCHAR(255)
```

Une divergence (colonne manquante, type ou nullabilité inattendus, `id`
sans `AUTO_INCREMENT`) est un **`warn`**, jamais un `fail` : la base est
joignable, le problème est réparable. Le `fail` reste réservé aux
erreurs bloquantes — connexion impossible ou lecture
`INFORMATION_SCHEMA` impossible. Exit code 0 pour un `warn`.

> **Le doctor diagnostique, il ne répare pas.** Aucun `ALTER TABLE`,
> aucune migration ni recréation de table n'est déclenché — voir
> [Limites](#limites).

## Sortie exemple — avec `--mqtt`

L'option `--mqtt` établit une connexion **brève** au broker configuré :
ouverture TCP, attente du CONNACK, déconnexion immédiate. Pas
d'abonnement durable, pas de publication, pas de boucle bloquante. Le
but est de confirmer qu'un **vrai broker MQTT** (et pas seulement un
port ouvert) accepte la connexion — d'où l'usage de `paho-mqtt` plutôt
qu'un simple `socket` TCP.

Broker joignable :

```text
  [OK]    broker MQTT — connexion réussie à localhost:1883
```

Broker injoignable (Mosquitto pas démarré, mauvais host/port, réseau
coupé) :

```text
  [FAIL]  broker MQTT — connexion impossible à localhost:1883
```

Authentification refusée (mauvais username/password) :

```text
  [FAIL]  broker MQTT — authentification refusée
```

Exit code 1 dans les deux cas d'échec. Le mot de passe MQTT n'apparaît
**jamais** dans la sortie. L'import `paho` est paresseux : rien n'est
importé tant que `--mqtt` n'est pas passé.

### Connexion TLS

Si `FORGE_IOT_MQTT_TLS_ENABLED=true`, `--mqtt` se connecte en **TLS**
(`client.tls_set` appelé avant la connexion). Pense à configurer aussi le
port TLS du broker (généralement `8883`) :

```bash
export FORGE_IOT_MQTT_HOST="mqtt.example.net"
export FORGE_IOT_MQTT_PORT="8883"
export FORGE_IOT_MQTT_TLS_ENABLED="true"
export FORGE_IOT_MQTT_TLS_CA_FILE="/etc/ssl/certs/mosquitto-ca.crt"

forge iot:doctor --mqtt
```

Sans `FORGE_IOT_MQTT_TLS_CA_FILE`, paho utilise les certificats système.
Le chemin du CA n'apparaît jamais dans la sortie. Détails :
[Configuration — TLS MQTT](configuration.md#tls-mqtt-preparation).

> **Astuce ateliers** : si Mosquitto n'est pas lancé, `forge iot:doctor
> --mqtt` sort légitimement en `[FAIL]` avec un message clair — c'est le
> signal attendu avant de démarrer un subscriber ou un simulateur. Pour
> installer et lancer un broker local, voir
> [Mosquitto local](mosquitto-local.md).

## Parcours recommandé

```bash
forge iot:doctor          # 1. diagnostic statique
forge iot:init            # 2. copier la migration vers mvc/migrations/
forge migration:apply     # 3. créer la table iot_events en base
forge iot:doctor --db     # 4. confirmer que la table est lisible
forge iot:doctor --mqtt   # 5. confirmer que le broker répond
forge run                 # 6. démarrer
```

Chaque étape produit un signal clair avant la suivante — pas besoin
de deviner ce qui manque.

Avec un username/password configurés :

```text
  [OK]    configuration IoT — chargée
           …
           mqtt_username   : forge
           mqtt_password   : ***
```

Le mot de passe est **toujours masqué** par `***` — c'est le contrat
de [`IotConfig.__repr__`](configuration.md#masquage-du-mot-de-passe)
appliqué uniformément dans le doctor.

## Cas d'erreur typiques

### Configuration invalide

Si `FORGE_IOT_MQTT_HOST` est défini mais vide, par exemple :

```text
  [FAIL]  configuration IoT — FORGE_IOT_MQTT_HOST ne peut pas être vide
```

Idem pour un port hors plage, un topic vide, etc. Voir
[Configuration Forge IoT — erreurs](configuration.md#erreurs-levees).

### Migration manquante

Depuis `IOT-PACKAGE-DATA-MIGRATIONS-001`, le doctor lit la migration
via `importlib.resources.files("forge_mvc_iot") / "migrations"` — la
ressource est embarquée dans le package Python lui-même
(`forge_mvc_iot/migrations/`) et déclarée dans `pyproject.toml`
(`[tool.setuptools.package-data]`).

Si le doctor ne trouve plus la migration, c'est probablement le signe
d'une installation cassée :

```text
  [FAIL]  migration iot_events — aucun *_create_iot_events.sql sous
           forge_mvc_iot/migrations/ — vérifier l'installation
           (pip install -e packages/forge-mvc-iot) et
           [tool.setuptools.package-data] dans pyproject.toml
```

Solution : réinstaller le package (`pip install -e packages/forge-mvc-iot`
ou `pip install --force-reinstall forge-mvc-iot`).

Pour **copier ensuite** la migration dans le projet, voir
[`forge iot:init`](init-command.md) — copie idempotente vers
`mvc/migrations/`, sans exécuter le SQL.

### Module non installé

Si l'utilisateur tape `forge iot:doctor` sans avoir installé
`forge-mvc-iot` :

```text
Erreur : module forge-mvc-iot non installé.
indice : installe le module opt-in : pip install forge-mvc-iot
```

Forge Core reste fonctionnel sans le module — l'import est paresseux
côté dispatcher (`forge.py`).

## Limites

Sont volontairement **hors périmètre**, y compris pour `--mqtt` :

- aucun abonnement durable, aucune publication de mesure, aucun
  `loop_forever` — `--mqtt` ne fait qu'un connect / disconnect bref ;
- aucun subscriber lancé, aucun simulateur de capteur ;
- aucune écriture en base déclenchée par `--mqtt` ;
- pas de test de topic via `subscribe` / `publish` ;
- pas de vérification de la version du contrat MQTT déployé côté
  capteurs ;
- pas d'audit des permissions ACL Mosquitto avancées, pas de certificat
  client (mTLS). Le **TLS est désormais pris en charge** : si
  `FORGE_IOT_MQTT_TLS_ENABLED=true`, `--mqtt` se connecte en TLS
  (`client.tls_set`, `ca_certs` = `FORGE_IOT_MQTT_TLS_CA_FILE` si fourni)
  — voir [Configuration — TLS MQTT](configuration.md#tls-mqtt-preparation).
  Sinon, la connexion reste en clair (comportement par défaut).

Côté `--db` et contrôle de schéma, sont aussi **hors périmètre** :

- aucune réparation : pas d'`ALTER TABLE`, pas de migration ni de
  recréation de table déclenchée par le doctor ;
- pas de gestion multi-version du schéma, pas de comparaison de hash de
  migration ;
- pas d'audit SQL complet (collation, moteur, index secondaires
  au-delà du contrat de colonnes).

Chacun de ces points peut justifier sa propre option / commande pour
rester lisible et localement testable.

## Tickets suivants

La trilogie `doctor` est complète :

- `forge iot:doctor`        → diagnostic statique ;
- `forge iot:doctor --db`   → diagnostic table `iot_events` ;
- `forge iot:doctor --mqtt` → diagnostic broker MQTT.

Pistes ultérieures : `IOT-SIMULATOR-001` (script de publication MQTT
factice pour les ateliers) ou une intégration Forge Design IoT au-dessus
de l'API HTTP JSON.
