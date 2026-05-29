# Audit de clôture Forge IoT

> Ticket : `IOT-CLOSING-AUDIT-001`. Audit **documentaire** de fin de phase —
> aucun code fonctionnel n'est ajouté. Instantané pris à la fin de la
> série de tickets IoT (dernier commit IoT : `f91be08`,
> `IOT-CLI-COMMANDS-DOCS-REFERENCE-001`).

## Verdict

**La phase Forge IoT est clôturable.** Le module opt-in `forge-mvc-iot`
fournit un flux local complet et testé :

```text
capteur / simulateur → MQTT (Mosquitto) → forge iot:listen → iot_events → API HTTP JSON
```

Toutes les briques prévues sont livrées, documentées et couvertes par des
tests. Les manques restants sont **assumés et explicites** (pas de
dashboard, pas de rétention, pas de downlink…) et relèvent de phases
ultérieures. Le seul chantier structurel identifié,
`OPTINS-PROJECT-STRUCTURE-001`, est **volontairement reporté** après cette
clôture.

## Résumé exécutif

- **30 tickets IoT livrés** (architecture → contrat MQTT → config →
  subscriber → stockage → API HTTP → CLI → docs pédagogiques → TLS →
  référence CLI), tous commités sur `main`.
- **4 commandes CLI** : `forge iot:doctor`, `forge iot:init`,
  `forge iot:listen`, `forge iot:simulate` (options `--db`, `--mqtt`,
  `--profile`).
- **3 routes HTTP JSON** en lecture, avec **Bearer token** optionnel.
- **MQTT over TLS** configurable et réellement branché dans les clients.
- **756 tests IoT** verts (fichiers `tests/test_iot_*.py` +
  `tests/meta/test_iot_*.py`).
- Forge Core **ne dépend pas** de `forge-mvc-iot` ; l'inverse est vrai.

## Tickets livrés

| Ticket | Commit | Sujet |
|---|---|---|
| `IOT-ARCHITECTURE-001` | `b805e8a` | Page fondatrice : périmètre et dépendances |
| `IOT-PACKAGE-SCAFFOLD-001` | `e99c97d` | Scaffold du paquet `forge-mvc-iot` |
| `IOT-MQTT-CONTRACT-001` | `6a1433f` | Contrat topic + payload |
| `IOT-CONFIG-001` | `2d6ac76` | Contrat de configuration (`IotConfig`) |
| `IOT-MQTT-SUBSCRIBER-001` | `af91147` | `MqttSubscriber` (paho) |
| `IOT-STORAGE-EVENTS-001` | `c2d83cb` | Contrat SQL des événements |
| `IOT-STORAGE-MIGRATION-001` | `dd6ef68` | Migration `iot_events` |
| `IOT-STORAGE-REPOSITORY-001` | `ec47e37` | `IotEventRepository.insert` |
| `IOT-STORAGE-REPOSITORY-READ-001` | `bd6fd79` | Méthodes de lecture |
| `IOT-HTTP-API-001` | `b859bec` | API HTTP JSON en lecture |
| `IOT-DOCTOR-001` | `a84084f` | Diagnostic statique |
| `IOT-PACKAGE-DATA-MIGRATIONS-001` | `97cf433` | Migrations packagées |
| `STARTER-WELCOME-IOT-001` | `ac00b2f` | Starter pédagogique `welcome-iot` |
| `IOT-INIT-COMMAND-001` | `42454fb` | `forge iot:init` |
| `IOT-DOCTOR-DB-001` | `32d7f95` | `forge iot:doctor --db` |
| `IOT-DOCTOR-MQTT-001` | `3fe852f` | `forge iot:doctor --mqtt` |
| `IOT-SIMULATOR-001` | `ce60b0a` | `forge iot:simulate` |
| `IOT-SUBSCRIBER-CLI-001` | `906a4ad` | `forge iot:listen` |
| `IOT-MOSQUITTO-LOCAL-DOCS-001` | `fda86ff` | Guide Mosquitto local |
| `IOT-END-TO-END-LOCAL-SMOKE-001` | `e21262f` | Smoke test local |
| `IOT-BTS-CIEL-DOCS-001` | `4718a05` | Guide pédagogique BTS CIEL |
| `IOT-ESP32-EXAMPLE-001` | `fb8ce2c` | Exemple ESP32 |
| `IOT-ARDUINO-R4-ASSESSMENT-001` | `6e85c78` | Évaluation Arduino R4 |
| `IOT-HTTP-API-AUTH-001` | `d39324c` | Bearer token optionnel |
| `IOT-DOCTOR-SCHEMA-001` | `b8b6eb3` | Vérification du schéma `iot_events` |
| `IOT-LISTEN-RESILIENCE-001` | `fcce5be` | Robustesse de `forge iot:listen` |
| `IOT-SIMULATOR-PROFILES-001` | `5c709d5` | Profils de simulation |
| `IOT-CONFIG-TLS-001` | `32fb5e1` | Configuration TLS |
| `IOT-MQTT-TLS-CLIENTS-001` | `c4f4c78` | TLS branché dans les clients |
| `IOT-CLI-COMMANDS-DOCS-REFERENCE-001` | `f91be08` | Référence CLI des commandes IoT |

Le présent ticket `IOT-CLOSING-AUDIT-001` n'ajoute que cet audit et ses
garde-fous.

## Architecture obtenue

Décisions verrouillées par `IOT-ARCHITECTURE-001` et tenues sur toute la
phase (vérifiées par les garde-fous `test_no_core_module_imports_forge_mvc_iot`
présents dans la plupart des suites IoT) :

- **Forge Core ne dépend pas de `forge-mvc-iot`** : aucun fichier de
  `core/` n'importe ni ne mentionne `forge_mvc_iot`.
- **`forge-mvc-iot` dépend de Forge Core** (et de lui seul côté Forge) ;
  `paho-mqtt` est sa seule dépendance runtime supplémentaire, importée
  **paresseusement**.
- **Forge Design ne lit pas MQTT directement** : il consommera l'**API
  HTTP JSON** Forge IoT (jamais le broker). Ce point reste théorique tant
  que le dashboard n'existe pas (voir limites).
- SQL visible (charte v2 §5), API publique = contrat de complétude
  (charte v2 §10), noyau minimal + brique opt-in (charte v2 §8).

Structure du paquet :

```text
packages/forge-mvc-iot/forge_mvc_iot/
  config.py          # IotConfig + load_iot_config
  http.py            # contrôleur + register_iot_routes
  migrations/        # *_create_iot_events.sql (package data)
  mqtt/  contract.py subscriber.py tls.py
  cli/   doctor.py init.py listen.py simulate.py
  storage/ events.py repository.py
```

## Commandes disponibles

| Commande | Rôle | Options |
|---|---|---|
| `forge iot:doctor` | diagnostic statique (package, config, migration, `register_iot_routes`) | `--db` (table + schéma `iot_events`), `--mqtt` (broker, TLS si activé) |
| `forge iot:init` | copie la migration packagée vers `mvc/migrations/` (idempotent, n'applique pas) | — |
| `forge iot:listen` | écoute MQTT et insère via `IotEventRepository` (dev/pédagogie) | — |
| `forge iot:simulate` | publie des mesures factices conformes au contrat | `--profile temperature\|humidity\|presence\|energy`, `--site`, `--device`, `--kind`, `--value`, `--unit`, `--count`, `--interval` |

Documentées dans [référence CLI](../../reference/cli-commands.md#commandes-forge-iot)
(garde-fou `test_forge_help_coverage_001`).

## API HTTP disponible

Trois routes JSON en **lecture** (`register_iot_routes`) :

- `GET /api/iot/events` — derniers événements ;
- `GET /api/iot/events/{site}/{device_id}` — événements d'un capteur ;
- `GET /api/iot/devices/{site}/{device_id}/count` — compteur.

**Bearer token** optionnel (`FORGE_IOT_API_TOKEN`) : absent/vide → API
**ouverte** (mode pédagogique) ; défini → `Authorization: Bearer <token>`
exigé, réponse `401 {"error":"unauthorized"}` sobre. L'auth vit dans le
module (`forge_mvc_iot/http.py`), jamais dans Forge Core.

## Stockage et migrations

- Migration `*_create_iot_events.sql` **packagée** comme donnée du paquet
  et copiée par `forge iot:init` ; appliquée par `forge migration:apply`.
- Table `iot_events` : `id`, `site`, `device_id`, `kind`, `value`,
  `unit`, `timestamp`, `metadata_json`, `received_at` (+ deux index).
- `IotEventRepository` : `insert` + méthodes de lecture (SQL visible).
- `forge iot:doctor --db` vérifie l'**accès** ET la **conformité du
  schéma** (colonnes, types, nullabilité, `AUTO_INCREMENT`).
- **Hors périmètre** : pas de rétention, pas d'agrégation, pas de
  downsampling.

## MQTT, TLS et sécurité

- Contrat topic : `forge/{site}/{device_id}/telemetry`.
- Payload : `kind`, `value`, `unit`, `timestamp` (ISO 8601 UTC `Z`),
  `metadata` optionnel ; taxonomie d'erreurs stable (`ContractError`).
- `MqttSubscriber` (uplink), `forge iot:listen` et `forge iot:simulate`
  opérationnels ; broker recommandé : **Mosquitto** local.
- **TLS** : `FORGE_IOT_MQTT_TLS_ENABLED` / `FORGE_IOT_MQTT_TLS_CA_FILE`,
  branchés via `forge_mvc_iot/mqtt/tls.py` (`client.tls_set` avant
  `connect`) dans le subscriber, `doctor --mqtt` et `simulate`. Port non
  forcé (l'utilisateur configure `FORGE_IOT_MQTT_PORT=8883`).
- Mot de passe et chemin CA **jamais** affichés (masqués dans
  `repr(IotConfig)` et absents des sorties).
- **Hors périmètre** : pas de downlink (Forge → capteur), pas de mTLS
  (certificat client), pas de `tls_insecure_set`, pas de broker cloud
  documenté.

## Starters et pédagogie

- Starter **`welcome-iot`** (`STARTER-WELCOME-IOT-001`) : parcours guidé
  doctor → init → migration:apply → run.
- Guide **BTS CIEL** / Bac Pro (`docs/iot/bts-ciel.md`) : rôle capteur /
  MQTT / stockage / API, exercices sans capteur via profils du
  simulateur.
- Exemple **ESP32** (`docs/iot/esp32-example.md`) : sketch de référence
  pédagogique.
- **Arduino R4** : **évalué, non supporté officiellement** — l'ESP32
  reste la cible de référence ; un UNO R4 WiFi *peut* être testé mais
  aucun exemple complet n'est garanti sans validation matérielle réelle.

## Documentation disponible

Pages présentes sous `docs/iot/` :

`architecture.md`, `configuration.md`, `mqtt-contract.md`,
`mqtt-subscriber.md`, `storage-events.md`, `http-api.md`, `doctor.md`,
`init-command.md`, `listen-command.md`, `simulator.md`,
`mosquitto-local.md`, `local-smoke-test.md`, `bts-ciel.md`,
`esp32-example.md`, `arduino-r4-assessment.md`.

Référence CLI : section « Commandes Forge IoT » dans
[`docs/reference/cli-commands.md`](../../reference/cli-commands.md).

## Tests et validations

- **756 tests IoT** verts : `tests/test_iot_*.py` (unitaires/intégration)
  + `tests/meta/test_iot_*.py` (garde-fous docs).
- Garde-fous transverses : `core/` n'importe pas IoT ; imports paho/paresseux ;
  cohérence CLI ↔ doc (`test_forge_help_coverage_001`,
  `test_cli_help_flags_closing_audit_001`).
- Validations standard vertes : `compileall`, `ruff check .`,
  `mkdocs build --strict`, `git diff --check`.

### Baseline connue (non IoT)

`tests/meta/test_docs_imports_validity_sweep_001.py` présente **26
échecs préexistants** (blocs d'import Python dans certaines pages docs,
dont `iot/mqtt-subscriber.md`, `iot/configuration.md`, `index.md`). Ces
échecs **précèdent la phase IoT close ici** (constatés identiques sur le
`HEAD` antérieur lors des tickets précédents) et relèvent de la
consolidation documentaire générale, **pas** d'une régression IoT. À
traiter hors phase IoT.

## Limites assumées

Forge IoT n'est **pas** une solution « production complète ». Sont
volontairement absents :

- pas de **dashboard Forge Design** (le cockpit de visualisation viendra
  au-dessus de l'API HTTP) ;
- pas de **downlink** Forge → capteur ;
- pas de **rétention** automatique, pas d'**agrégation** / downsampling ;
- pas de **service systemd** officiel, pas de **queue durable**, pas de
  **retry/backoff** de production (`forge iot:listen` reste dev/pédagogie) ;
- pas de **multi-tenant** avancé ;
- pas de **mTLS**, pas de **broker cloud** documenté ;
- **Arduino R4 non supporté officiellement** ; **ESP32** fourni comme
  **exemple pédagogique**.

## Dettes restantes

- Baseline documentaire `test_docs_imports_validity_sweep_001` (26
  échecs, voir ci-dessus) — à nettoyer hors phase IoT.
- Forge Design IoT (lecture de l'API HTTP) : non commencé, dépend d'un
  futur chantier dashboard.

## Tickets reportés

- `OPTINS-PROJECT-STRUCTURE-001` (voir section suivante) — **reporté**.
- `FORGE-DESIGN-IOT-READ-API-001` — dashboard lisant l'API HTTP IoT.
- `IOT-STORAGE-RETENTION-001` — rétention / purge (si besoin réel).
- `IOT-ARDUINO-R4-EXAMPLE-001` — uniquement si un UNO R4 WiFi réel est
  validé.

## Préparation du chantier optins/

`OPTINS-PROJECT-STRUCTURE-001` — **réorganisation future de la structure
opt-in côté projet utilisateur** :

- les **packages restent** dans `packages/forge-mvc-*` (source de
  vérité, distribution PyPI) ;
- un futur dossier **`optins/`** servirait de **couche de branchement
  local** côté projet généré : routes, migrations, README, docs locales
  minimales, starters opt-in ;
- objectif : rendre l'activation d'un opt-in (IoT, RBAC, MFA…) lisible et
  reproductible dans un projet utilisateur, sans écriture invisible dans
  le code applicatif (charte v2 §9).

**Ce chantier est volontairement reporté après la clôture IoT.** Il n'est
pas commencé ; cet audit se contente de l'identifier.

## Décision de clôture

**Phase Forge IoT : CLÔTURÉE.** Les critères sont remplis — briques
livrées, testées, documentées ; limites explicites ; dette structurelle
isolée dans un ticket reporté. Le prochain chantier recommandé est
`OPTINS-PROJECT-STRUCTURE-001`, à n'ouvrir **qu'après** validation de cet
audit.
