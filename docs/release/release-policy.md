# Politique de release Forge

!!! note "Historique beta.5"
    `1.0.0-beta.5` reste le jalon historique de publication coordonnée initiale des opt-ins `rbac`, `workflow` et `stats`.

    Les tableaux de cette page décrivent l’état courant : les opt-ins publiés restent synchronisés avec la version du core.


Ce document définit comment Forge numérote, prépare, valide, tague et publie ses versions.

Il complète :

- [Procédure de release](release.md), checklist pas à pas avant chaque tag
- [Validation locale](release-local.md), procédure de test wheel locale
- [Contrat de stabilité](stability-contract.md), ce qui est stable, interne, expérimental

---

## Objectif

Rendre explicite :

- quand incrémenter `MAJOR`, `MINOR` ou `PATCH` ;
- comment préparer et valider une release ;
- comment taguer et documenter ;
- ce qui est stable, ce qui est expérimental ;
- ce qui ne doit pas être promis.

---

## Schéma de versionnement

Forge adopte **SemVer adapté** :

```
MAJOR.MINOR.PATCH
```

Exemples :

```
1.2.0   → 1.2.1   (correctif)
1.2.0   → 1.3.0   (fonctionnalité compatible)
1.x.y   → version majeure suivante   (rupture)
```

---

## PATCH

Incrémenter `PATCH` pour :

- corrections de bugs sans changement d'API ;
- corrections de documentation mineures ;
- durcissements de sécurité sans changement d'interface (headers, cookies, validation) ;
- tests supplémentaires sans modification du comportement observable ;
- corrections de lint ou de format sans impact fonctionnel.

**Exemples de tickets PATCH :** `SECURITY-HEADERS-001` (ajout Permissions-Policy sans changement API), `SECURITY-COOKIES-001` (audit sans modification de l'API de session).

**Règle d'or :** si un projet existant en Forge 1.x fonctionne sans modification après la mise à jour, c'est un PATCH.

---

## MINOR

Incrémenter `MINOR` pour :

- nouvelle fonctionnalité rétrocompatible ;
- nouvelle commande CLI documentée ;
- nouveau module optionnel ;
- nouvelle documentation structurante (sections majeures) ;
- amélioration DX sans rupture ;
- ajout d'API publique sans supprimer l'existante ;
- nouvelle brique optionnelle (ex. Auth/User, module Forge).

**Exemples de tickets MINOR :** `AUTH-MFA-002` (nouvelle fonctionnalité Auth), `MODULE-LIFECYCLE-001` (nouvelle commande `module:install`), `CRUD-HTMX-001` (comportement CRUD optionnel supplémentaire).

**Règle d'or :** si un projet existant fonctionne sans modification mais peut bénéficier des nouvelles fonctionnalités en opt-in, c'est un MINOR.

---

## MAJOR

Incrémenter `MAJOR` pour :

- rupture de compatibilité avec un élément stable (voir [Contrat de stabilité](stability-contract.md)) ;
- changement de structure de projet générée incompatible ;
- changement de comportement CLI incompatible pour les commandes stables ;
- suppression d'API publique documentée ;
- changement de convention incompatible (nommage de fichiers, format JSON entité) ;
- modification incompatible du schéma des fichiers générés (controllers, models, vues) ;
- changement de configuration incompatible (clés `.env` renommées ou supprimées).

**Règle d'or :** si un projet existant doit être modifié pour fonctionner après la mise à jour, c'est un MAJOR.

**Ce qui n'est PAS un MAJOR :**

- Modification d'une API interne ou expérimentale (voir [Contrat de stabilité](stability-contract.md)).
- Changement de comportement d'une commande expérimentale.
- Ajout de fonctionnalités sans supprimer l'existant.

---

## API publique et API interne

Se référer au [Contrat de stabilité Forge 1.x](stability-contract.md) pour la liste complète.

### Stable : garantie 1.x

- Commandes CLI documentées dans `docs/reference.md`.
- Structure projet générée par `forge new`.
- Format JSON canonique des entités (v1).
- Clés `.env` documentées.
- Imports publics de `core.http`, `core.auth`, `core.security` (session, CSRF, RBAC).
- `GET /health` → `200 {"status":"ok"}`.

### Interne : peut changer entre mineurs

- Fonctions et modules internes de `cli/`.
- Fonctions préfixées `_`.
- Contenu interne des tests Forge.
- Format interne des sessions côté serveur.

### Expérimental : stable en usage, interface peut évoluer

- `forge module:*`, `forge deploy:*`.
- Backends de session `FileSessionStore`, `MariaDbSessionStore`.
- Pages publiques (`make:public-*`).

---

## Stratégie de classification PyPI

> **Note RC** : en `{{forge_version}}` (release candidate), la **version** est une préversion finale, mais le classifier `Development Status` reste `4 - Beta`.
> PyPI ne propose pas de classifier « Release Candidate »
> distinct ; le signal RC passe donc par le numéro de version (PEP 440 `rc`), pas par le classifier.
> Le passage à `5 - Production/Stable` se fera avec la `1.0.0` stable.

Les classifiers `Development Status` reflètent la maturité réelle de chaque package publiable :

| Package | Classifier | Justification |
|---|---|---|
| `forge-mvc` (core) | `4 - Beta` | 1.0.0 en bêta, corrections post-audit, tests terrain et RC requis avant stable |
| `forge-mvc-rbac` | `4 - Beta` | API stable et testée, usage production externe encore limité |
| `forge-mvc-workflow` | `4 - Beta` | API stable et testée, usage production externe encore limité |
| `forge-mvc-stats` | `4 - Beta` | API stable et testée, usage production externe encore limité |
| `forge-mvc-mfa` | `4 - Beta` | Secret TOTP chiffré au repos (Fernet, `MFA-PYPI-READY-001`), publié sur PyPI depuis `1.0.0-beta.9` |
| `forge-mvc-images` | `4 - Beta` | Module image opt-in (traitement Pillow extrait du core, ADR-018) + couche médias applicative ; dépend de `forge-mvc-files`. Publié sur PyPI depuis `1.0.0-beta.13` |
| `forge-mvc-iot` | `4 - Beta` | Module IoT opt-in (MQTT → `iot_events` → API HTTP), publié sur PyPI depuis `1.0.0-beta.12` |
| `forge-mvc-video` | `4 - Beta` | Module vidéo opt-in : chaîne complète `video:upload` → `video:process` → lecture HTTP Range, + `video:cleanup` ; transcodage MP4 H.264/AAC. Publié sur PyPI depuis `1.0.0-beta.13` |
| `forge-mvc-audio` | `4 - Beta` | Module audio opt-in **sans état** : upload, sondage (`ffprobe`), transcodage MP3 (`ffmpeg`), lecture HTTP Range, `audio:doctor`. Pas de base de données. Publié sur PyPI depuis `1.0.0-beta.13` |
| `forge-mvc-files` | `4 - Beta` | Upload générique extrait du core (ADR-019) : écriture sécurisée, storage anti-traversal, service de fichiers, rate-limit. Publié sur PyPI depuis `1.0.0-beta.13` |
| `forge-mvc-mail` | `4 - Beta` | Email opt-in extrait du core (ADR-022) : composition, transports interchangeables, templates Jinja, CLI `mail:*`. Publié sur PyPI depuis `1.0.0-beta.13` |
| `forge-mvc-i18n` | `4 - Beta` | Internationalisation opt-in extraite du core (ADR-027) : catalogues JSON, locale par défaut et fallback, cache, helper `trans()` Jinja. Le noyau garde un repli no-op renvoyant la clé. Pas encore publié sur PyPI |
| `forge-mvc-admin` | `4 - Beta` | Back-office applicatif opt-in : CRUD générique sur les entités déclarées, sécurité par défaut (auth + CSRF), RBAC optionnel, `admin:init` / `admin:doctor`. Chantier clôturé (suite verte), non publié sur PyPI |
| `forge-mvc-qrcode` | `4 - Beta` | Génération de QR Codes opt-in (ADR-050) : PNG et SVG depuis du texte ou une URL, réponse HTTP servable depuis un contrôleur. Dépend de `segno` (pur Python). Non publié sur PyPI |
| `forge-mvc-settings` | `4 - Beta` | Paramètres applicatifs opt-in (ADR-052) : table `app_settings` clé/valeur typée, API `get_setting`/`set_setting`, migration fournie via `settings:init`. Dépend uniquement du cœur. Non publié sur PyPI |
| `forge-mvc-import-export` | `4 - Beta` | Échange CSV opt-in (ADR-052) : import (validation par champ, rapport d'erreurs, insertion via un callback) et export programmatique (`to_csv`). Pur stdlib, dépend uniquement du cœur. Non publié sur PyPI |
| `forge-mvc-audit` | `4 - Beta` | Journal d'audit applicatif opt-in (ADR-052) : table `audit_log`, `record_audit`/`get_audit_log`, migration via `audit:init`. Borné (pas un SIEM, cohérent ADR-008), dépend uniquement du cœur. Non publié sur PyPI |
| `forge-mvc-jobs` | `4 - Beta` | File de tâches de fond opt-in (ADR-052) : table `jobs`, `enqueue` + worker explicite (`drain`/`run_worker`), réservation atomique. Sans broker ni async, dépend uniquement du cœur. Non publié sur PyPI |
| `forge-mvc-notifications` | `4 - Beta` | Notifications in-app opt-in (ADR-052) : table `notifications`, `notify`/`get_notifications`/`mark_read`. Stockage in-app, livraison email/push à combiner avec jobs + mail. Dépend uniquement du cœur. Non publié sur PyPI |
| `forge-mvc-deploy` | `4 - Beta` | Outillage de déploiement opt-in extrait du cœur (ADR-053) : commandes `deploy:init` (gabarits Nginx/systemd/WSGI) et `deploy:check`. Opt-in CLI-only, sans API runtime ni migration. Dépend uniquement du cœur. Non publié sur PyPI |
| `forge-mvc-entities` | `4 - Beta` | Moteur d'entités opt-in extrait du cœur (ADR-070) : génération et modélisation (`make:entity`, `make:relation`, `build:model`, migrations, `make:crud`), provisioning `db:*`, pivot enrichi absorbé de `forge-mvc-pivot`. Dépend du contrat `Dialect` du cœur, indépendant des backends. Extraction en cours, non publié sur PyPI |
| `forge-mvc-testing` | `4 - Beta` | Infrastructure de test partagée (ADR-041) : `FakeRequest` + plugin pytest (fixtures autouse). Pour tester Forge et ses opt-ins, y compris par des tiers ; publiée pour l'écosystème avec la rc.1 |
| `forge-mvc-mariadb` | `4 - Beta` | Backend BDD MariaDB extrait du cœur (ADR-054) : pool de connexions, découvert par le cœur via entry point `forge_mvc.db_backend`. Le cœur est agnostique BDD ; ce backend fournit MariaDB (et le connecteur). Non publié sur PyPI |
| `forge-mvc-sqlite` | `4 - Beta` | Backend BDD SQLite (ADR-054) au-dessus de `sqlite3` (stdlib), sans dépendance externe ni serveur : chemin runtime (adaptateur lignes-dict, `?`, lastrowid). Idéal en développement et tests. Non publié sur PyPI |
| `forge-mvc-postgres` | `3 - Alpha` | Backend BDD PostgreSQL (ADR-054) au-dessus de `psycopg` : dialecte + traduction des paramètres `?` vers `%s`, testés unitairement. Statut Alpha : intégration serveur et provisioning CLI à valider/câbler. Non publié sur PyPI |
| `forge-mvc-mssql` | `3 - Alpha` | Backend BDD Microsoft SQL Server (ADR-054) au-dessus de `pyodbc` : dialecte Transact-SQL (IDENTITY, crochets, formes gardées IF OBJECT_ID), testé unitairement ; pyodbc utilise nativement les paramètres `?`. Statut Alpha : intégration serveur (pilote ODBC) et provisioning CLI à valider/câbler. Non publié sur PyPI |

Critères de passage Beta → Stable d'un module opt-in :

- Retours d'usage externe documentés
- Pas de modification d'API publique sur 1 cycle MINOR complet
- Documentation complète et exemples à jour
- Tests à 100 % des branches critiques

La règle s'applique de manière indépendante à chaque package : le passage de `forge-mvc` à Stable ne tire pas les opt-in avec lui.

---

## Règles Git et tags

### main doit rester stable

- `main` est la branche de référence.
  Elle doit toujours être dans un état déployable et testé.
- Les développements en cours peuvent être regroupés sur `main` entre les releases, à condition que chaque commit soit validé (tests passants).
- Un commit de release est distingué des commits de développement par un message `release: preparer forge x.y.z`.

### Format de tag

Les tags Git Forge suivent la convention **SemVer publique**, jamais la forme PEP 440 :

```
vX.Y.Z              # stable
vX.Y.Z-beta.N       # pre-release beta
vX.Y.Z-alpha.N      # pre-release alpha
vX.Y.Z-rc.N         # release candidate
```

Exemples :

```
v1.2.0
v1.3.0
v1.0.0-beta.9
v1.0.0-beta.10
```

- Les tags utilisent le préfixe `v` (minuscule).
- Les tags sont annotés (`git tag -a`).
- Le tag est créé sur le commit de release, après validation complète.
- **Ne PAS utiliser** la forme PEP 440 pour les tags (`v<major>.<minor>.<patch>bN` est interdit).
  Le tag suit toujours la forme publique lisible, la version PEP 440 reste limitée à `pyproject.toml`, `core/__init__.py`, `forge.py` et la publication PyPI.
  Voir `RELEASE-VALIDATE-PEP440-SEMVERSION-001`.

L'utilitaire `tools/release-validate.sh --convert semver <pep440>` produit le suffixe SemVer correspondant à la version PEP 440 courante, c'est la source de vérité pour construire le nom de tag depuis la version Python.

### Immuabilité des tags publiés

**Un tag publié (poussé sur GitHub) ne doit pas être déplacé ni supprimé.**

Si une erreur est détectée après publication :

- Corriger dans un nouveau commit.
- Créer un nouveau tag de correctif (ex. `v1.2.1`).
- Ne pas modifier le tag `v1.2.0`.

Seuls les tags locaux non poussés peuvent être corrigés.
Une fois poussé, le tag est immuable.

---

## Validation obligatoire

Ces commandes doivent passer sans erreur avant tout tag de release :

```bash
pytest
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
pip-audit -r requirements.txt
pip-audit -r requirements-dev.txt
npm audit --omit=dev
```

Aucune dérogation n'est tolérée.
Si une validation échoue, le ticket doit être corrigé avant le tag.

L'ensemble est aussi vérifié automatiquement par [`tools/release-validate.sh`](https://github.com/caucrogeGit/Forge/blob/main/tools/release-validate.sh) (sections 1 à 12).

Voir aussi [Procédure de release](release.md) pour la checklist complète incluant la construction de la wheel.

### Audits dépendances

Les audits de dépendances peuvent exister en surveillance continue, mais une release Forge ne doit être validée que si les audits Python et Node passent en mode **bloquant**.
Deux contextes coexistent :

| Contexte | Outil | Mode | Effet d'une CVE |
|---|---|---|---|
| Surveillance hebdomadaire | [`.github/workflows/dependency-audit.yml`](https://github.com/caucrogeGit/Forge/blob/main/.github/workflows/dependency-audit.yml) | **Informatif** (`continue-on-error: true`) | Rapport visible dans l'historique Actions, aucun blocage |
| Validation release | [`tools/release-validate.sh`](https://github.com/caucrogeGit/Forge/blob/main/tools/release-validate.sh), sections 8 (`pip-audit`) et 9 (`npm audit --omit=dev`) | **Bloquant** | Échec immédiat, release impossible |

Cette séparation évite de bloquer le développement quotidien sur une CVE transitoire (typiquement le délai entre la publication d'un avis et la disponibilité d'un patch upstream), tout en garantissant qu'aucune release Forge ne sort avec un audit dépendances rouge.

Aucun masquage par `|| true` ou `continue-on-error: true` n'est toléré
dans le chemin de validation release.
Si une CVE bloque, le ticket de correction dépendance doit être ouvert et résolu avant la release, pas contourné.

---

## Build wheel

Avant publication, construire la wheel :

```bash
rm -rf dist build *.egg-info
python -m build
ls dist/
```

Vérification minimale de la wheel installée :

```bash
pipx install dist/forge_mvc-X.Y.Z-py3-none-any.whl --force
forge --version
```

Voir [Validation locale](release-local.md) pour la procédure complète des parcours pédagogiques.

---

## Cohérence de version

Avant le tag, vérifier que la version est uniforme sur tous les fichiers :

| Fichier | Clé |
|---|---|
| `pyproject.toml` | `version = "x.y.z"` |
| `forge.py` | `__version__ = "x.y.z"` |
| `core/__init__.py` | `__version__ = "x.y.z"` |
| `README.md` | mentions de version |
| `CHANGELOG.md` | entrée `## [x.y.z]` |

---

## Publication GitHub

Niveaux de publication :

### Release locale (développement et validation)

Avant toute release, exécuter le script de validation :

```bash
bash tools/release-validate.sh <VERSION>
# ex. : bash tools/release-validate.sh {{forge_version}}
```

Ce script vérifie en une seule passe :

1. Cohérence de version (`pyproject.toml`, `core/__init__.py`, `forge.py`)
2. Entrée CHANGELOG présente
3. Tests (`pytest -x -q`)
4. Qualité de code (`ruff check`)
5. Compilation Python (`compileall`)
6. Documentation MkDocs (`mkdocs build --strict`)
7. État git propre (pas de modifications non commitées)
8. Whitespace (`git diff --check`)
9. Tag absent (pré-tag)

Le script quitte avec le code 1 si au moins un `[FAIL]` est détecté.

Checklist manuelle complémentaire :

- Tests OK.
- Version mise à jour sur tous les fichiers.
- Wheel buildée et installée localement.
- Validation CLI et starters OK.

### Release GitHub (publication officielle)

- Tag annoté créé sur le commit de release.
- Tag poussé : `git push origin vX.Y.Z`.
- Release GitHub rédigée depuis l'onglet *Releases* avec le contenu du CHANGELOG.
- Changelog disponible dans `CHANGELOG.md`.

Vérifications post-publication :

- Workflow CI (`tests.yml`) passe sur le tag poussé.
- Déploiement MkDocs (`pages.yml`) déclenché et OK.

### Publication PyPI

**État Forge {{forge_version}} :** le core `forge-mvc` est **publié sur PyPI** sous `forge-mvc=={{forge_version}}`.
`{{forge_version}}` est une préversion PEP 440 (release candidate), l'option `--pre` est nécessaire pour l'installer.

| Package | Publication PyPI | Notes |
|---|---|---|
| `forge-mvc` (core) | ✅ Publié, `{{forge_version}}` | `pip install --pre forge-mvc` |
| `forge-mvc-rbac` | ✅ Publié sur PyPI, version alignée avec le core | `pip install --pre forge-mvc-rbac` |
| `forge-mvc-workflow` | ✅ Publié sur PyPI, version alignée avec le core | `pip install --pre forge-mvc-workflow` |
| `forge-mvc-stats` | ✅ Publié sur PyPI, version alignée avec le core | `pip install --pre forge-mvc-stats` |
| `forge-mvc-mfa` | ✅ Publié sur PyPI depuis `1.0.0-beta.9`, version alignée avec le core | `pip install --pre forge-mvc-mfa` (Beta, `MFA-PYPI-READY-001`) |
| `forge-mvc-images` | ✅ Publié sur PyPI depuis `1.0.0-beta.13`, version alignée avec le core | `pip install --pre forge-mvc-images` (Beta, `MEDIA-PYPI-READY-002`) |

Tous les opt-ins officiels sont publiables directement depuis PyPI.

Procédure de publication (manuelle, délibérée) :

```bash
python -m build --wheel --sdist
twine upload --repository testpypi dist/forge_mvc-X.Y.Z*  # TestPyPI d'abord
twine upload dist/forge_mvc-X.Y.Z*                         # PyPI réel
```

Précautions spécifiques à PyPI :

- Un numéro de version publié sur PyPI **ne peut pas être republié** sous le même nom.
- Toujours tester avec TestPyPI avant toute publication.
- Ne jamais publier un build non validé localement.
- Mettre à jour `CHANGELOG.md` avant la publication.

PyPI n'est pas automatisé dans la procédure actuelle.
La publication reste manuelle et délibérée.

---

## Verrouillage packaging

### État actuel des packages (PACKAGE-LOCK-DOC-001)

| Package | Statut PyPI | Règle |
|---|---|---|
| `forge-mvc` (core) | ✅ Publié, `{{forge_version}}` | Publié dès `1.0.0-beta.1` |
| `forge-mvc-rbac` | ✅ Publié sur PyPI, version alignée avec le core | `pip install --pre forge-mvc-rbac` |
| `forge-mvc-workflow` | ✅ Publié sur PyPI, version alignée avec le core | `pip install --pre forge-mvc-workflow` |
| `forge-mvc-stats` | ✅ Publié sur PyPI, version alignée avec le core | `pip install --pre forge-mvc-stats` |
| `forge-mvc-mfa` | ✅ Publié sur PyPI depuis `1.0.0-beta.9`, version alignée avec le core | `pip install --pre forge-mvc-mfa` (statut Beta, `MFA-PYPI-READY-001`, `SEC-MFA-SECRET-ENCRYPTION-001` livré) |
| `forge-mvc-images` | ✅ Publié sur PyPI depuis `1.0.0-beta.13`, version alignée avec le core | `pip install --pre forge-mvc-images` (statut Beta ; dépend de `forge-mvc-files` ; voir `production-limits.md`) |
| `forge-mvc-files` | ✅ Publié sur PyPI depuis `1.0.0-beta.13`, version alignée avec le core | `pip install --pre forge-mvc-files` |
| `forge-mvc-audio` | ✅ Publié sur PyPI depuis `1.0.0-beta.13`, version alignée avec le core | `pip install --pre forge-mvc-audio` |
| `forge-mvc-video` | ✅ Publié sur PyPI depuis `1.0.0-beta.13`, version alignée avec le core | `pip install --pre forge-mvc-video` |
| `forge-mvc-iot` | ✅ Publié sur PyPI depuis `1.0.0-beta.12`, version alignée avec le core | `pip install --pre forge-mvc-iot` |
| `forge-mvc-mail` | ✅ Publié sur PyPI depuis `1.0.0-beta.13`, version alignée avec le core | `pip install --pre forge-mvc-mail` |
| `forge-mvc-i18n` | ⏳ Pas encore publié sur PyPI (extrait du core en `1.0.0-beta.15`, ADR-027) | `pip install --pre forge-mvc-i18n` (à la publication) |

### Règles de version

- **Jusqu'à `1.0.0-beta.4`** : seul le core `forge-mvc` était bumped à chaque release.
  Les opt-ins source-only conservaient leur version interne.
- Depuis `1.0.0-beta.9`, les opt-ins (`rbac`, `workflow`, `stats`, `mfa`) sont publiés sur PyPI et strictement synchronisés avec la version du core ; `iot` les a rejoints en `1.0.0-beta.12`, puis `files`, `images`, `audio`, `video`, `pivot` et `mail` en `1.0.0-beta.13`, et `i18n` (extrait en `1.0.0-beta.15`) ensuite.
  **Les opt-ins officiels** sont désormais publiés et synchronisés.

### Artefacts de build

Les répertoires `dist/`, `build/` et `*.egg-info/` sont des artefacts de validation locale.
Ils sont exclus de Git (`.gitignore`) et **ne doivent pas être commités**.

```bash
# Validation locale uniquement - ne publie rien
python -m build
twine check dist/*
```

`twine check` valide les métadonnées localement sans rien publier sur PyPI.
`twine upload` est l'opération de publication, réservée à un ticket release dédié.

### Règle générale

Toute publication PyPI est une action délibérée relevant d'un ticket de release dédié.
Aucune automatisation ne déclenche la publication.

---

## Politique de publication des opt-ins

### État actuel

`forge-mvc` (core) est publié sur PyPI depuis `1.0.0-beta.1`.
**Les opt-ins officiels** (voir `packages/` pour la liste à jour) sont publiés sur PyPI et synchronisés avec le core, de même que les backends de base de données (`forge-mvc-mariadb`, `-sqlite`, `-postgres`, `-mssql`).
Les règles applicables à chaque package restent documentées ici.

Cette politique est livrée par le ticket `OPTIN-PACKAGES-PUBLICATION-POLICY-001`.

### Core publié sur PyPI

`forge-mvc` était le seul package publié sur PyPI jusqu'à `1.0.0-beta.4` inclus.
Il est le point d'entrée officiel du framework.

### Opt-ins publiés sur PyPI

Les opt-ins officiels ont été publiés sur PyPI au fil des bêtas :

- `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats` (Bêta) : publication initiale en `1.0.0-beta.5` ;
- `forge-mvc-mfa` (Beta) : publication en `1.0.0-beta.9` ;
- `forge-mvc-iot` (Beta) : publication en `1.0.0-beta.12` ;
- `forge-mvc-files`, `forge-mvc-images`, `forge-mvc-audio`, `forge-mvc-video`, `forge-mvc-pivot`, `forge-mvc-mail` : publication en `1.0.0-beta.13` ;
- `forge-mvc-i18n` (Bêta) : extrait du core en `1.0.0-beta.15` (ADR-027), publié et synchronisé avec le core.

Les extras `forge-mvc[rbac]`, `forge-mvc[workflow]`, `forge-mvc[stats]` et `forge-mvc[all]` sont disponibles via `pip install --pre forge-mvc[all]`.
Les autres opt-ins ne sont pas déclarés comme extras : les installer directement avec `pip install --pre forge-mvc-<nom>`.

### Historique : opt-ins source-only avant publication PyPI

Avant leur publication PyPI, les opt-ins `forge-mvc-rbac`, `forge-mvc-workflow` et `forge-mvc-stats` étaient disponibles en **source-only** via GitHub :

- non publiés sur PyPI ;
- installables depuis le dépôt GitHub (voir `docs/install/github.md`) ;
- versionnés indépendamment du core jusqu'à la publication coordonnée.

### Opt-ins publiés et synchronisés

Les opt-ins officiels sont publiés sur PyPI avec une version synchronisée avec le core :

| Package | Publication | Statut | Prérequis |
|---|---|---|---|
| `forge-mvc-rbac` | PyPI depuis `1.0.0-beta.5` | Bêta | Version alignée avec le core |
| `forge-mvc-workflow` | PyPI depuis `1.0.0-beta.5` | Bêta | Version alignée avec le core |
| `forge-mvc-stats` | PyPI depuis `1.0.0-beta.5` | Bêta | Version alignée avec le core |
| `forge-mvc-mfa` | PyPI depuis `1.0.0-beta.9` | Bêta | `FORGE_MFA_SECRET_KEY` obligatoire au démarrage ; secret TOTP chiffré au repos (Fernet) |
| `forge-mvc-iot` | PyPI depuis `1.0.0-beta.12` | Bêta | Dépend de `paho-mqtt` ; API HTTP en lecture seule, token Bearer optionnel |
| `forge-mvc-files` | PyPI depuis `1.0.0-beta.13` | Bêta | Upload générique (storage anti-traversal, service HTTP Range, rate-limit) |
| `forge-mvc-images` | PyPI depuis `1.0.0-beta.13` | Bêta | Pillow ; dépend de `forge-mvc-files` ; voir `production-limits.md` |
| `forge-mvc-audio` | PyPI depuis `1.0.0-beta.13` | Bêta | `ffmpeg`/`ffprobe` requis ; module sans état |
| `forge-mvc-video` | PyPI depuis `1.0.0-beta.13` | Bêta | `ffmpeg` requis ; transcodage MP4 H.264/AAC |
| `forge-mvc-mail` | PyPI depuis `1.0.0-beta.13` | Bêta | Transports interchangeables (console, SMTP, log) |
| `forge-mvc-i18n` | Publication à venir (extrait en `1.0.0-beta.15`) | Bêta | Catalogues JSON, fallback, cache, helper `trans()` ; repli no-op du noyau |

La publication est strictement synchronisée : core et opt-ins portent la même version.

### Cas particulier : forge-mvc-mfa

`forge-mvc-mfa` est publié sur PyPI depuis `1.0.0-beta.9` au statut **Bêta**.

État après `MFA-PYPI-READY-001` :

- statut Beta (`Development Status :: 4 - Beta`) ;
- le secret TOTP est chiffré au repos via Fernet (`SEC-MFA-SECRET-ENCRYPTION-001`) ;
- `FORGE_MFA_SECRET_KEY` obligatoire au démarrage.

Le secret TOTP chiffré au repos et la clé obligatoire au démarrage sont les acquis qui ont permis le passage en Beta.
Voir auth-mfa pour la checklist.

### Extras PyPI

Les extras `forge-mvc[rbac]`, `forge-mvc[workflow]`, `forge-mvc[stats]` et `forge-mvc[all]` sont disponibles pour les opt-ins publiés.

Seuls `rbac`, `workflow` et `stats` sont déclarés comme extras de `forge-mvc[all]`.
Les autres opt-ins (`mfa`, `files`, `images`, `audio`, `video`, `iot`, `pivot`, `mail`) ne sont **pas déclarés** dans les extras PyPI : les installer directement avec `pip install --pre forge-mvc-<nom>`.

### Règles de version

- **Jusqu'à `1.0.0-beta.4`** : seul le core `forge-mvc` était versionné à chaque release.
- Depuis `1.0.0-beta.9`, le core et les opt-ins (`rbac`, `workflow`, `stats`, `mfa`) sont strictement synchronisés sur la même version PEP 440 ; `forge-mvc-iot` a rejoint cette synchronisation en `1.0.0-beta.12`, puis `files`, `images`, `audio`, `video`, `pivot` et `mail` en `1.0.0-beta.13`, et `i18n` ensuite (l'ensemble des opt-ins officiels).

### Ce qui reste interdit sans ticket de release dédié

- `twine upload` d'un nouveau package non encore publié, interdit sans ticket de release dédié ;
- déclarer `forge-mvc[mfa]`, `forge-mvc[images]` ou un autre opt-in hors `rbac`/`workflow`/`stats` dans les extras PyPI sans décision explicite (ces paquets s'installent directement) ;
- inclure `forge-mvc-mfa` dans `forge-mvc[all]` : exclusion volontaire (choix de sécurité explicite).

### Tickets liés

| Ticket | Description | État |
|---|---|---|
| `OPTIN-PACKAGES-PUBLICATION-POLICY-001` | Documenter la politique de publication des opt-ins | livré |
| `OPTIN-PYPI-NAMES-CHECK-001` | Vérifier la disponibilité des noms PyPI des opt-ins | livré |
| `OPTIN-PYPI-PUBLISH-PREPARE-001` | Préparer rbac/workflow/stats pour publication (dépendances relâchées, `Private :: Do Not Upload` retiré) | livré |
| `OPTIN-PYPI-PUBLISH-001` | Publication coordonnée des opt-ins publiables | historique / livré selon version cible |
| `SEC-MFA-SECRET-ENCRYPTION-001` | Chiffrement Fernet des secrets TOTP | livré |
| `MFA-PYPI-READY-001` | Requalification Alpha de forge-mvc-mfa | livré |

---

## Changelog

Chaque release doit avoir une entrée dans `CHANGELOG.md` avec la structure :

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Ajouté

- Nouvelle fonctionnalité (TICKET-001).

### Modifié

- Comportement modifié (TICKET-002).

### Corrigé

- Bug corrigé (TICKET-003).

### Sécurité

- Durcissement (TICKET-004).

### Documentation

- Guide ajouté (TICKET-005).

### Tests

- Tests ajoutés (TICKET-006).
```

Ne lister que les sections non vides.
Chaque entrée référence le ticket associé.

---

## Roadmap et tickets

La roadmap (`docs/roadmap/forge-roadmap.md`) est la source de vérité pour l'état d'avancement des tickets.

Règles :

- Un ticket livré doit être marqué `**livré**` dans la roadmap.
- La prochaine priorité doit être indiquée clairement dans la roadmap.
- Les limites restantes doivent être reportées dans les tickets futurs.
- Les tickets futurs doivent être bornés, ne pas créer de tickets ouverts sans critères d'acceptation.
- La roadmap ne doit pas lister des ambitions non bornées comme des tickets actifs.

---

## Ce que cette politique ne couvre pas encore

| Domaine | Ticket futur |
|---|---|
| Politique de dépréciation officielle, préavis, cycle de vie des APIs | `RELEASE-DEPRECATION-001`, voir [deprecation-policy.md](deprecation-policy.md) |
| Matrice de compatibilité Python / MariaDB / Node | `RELEASE-COMPAT-001` |
| Guide de migration entre versions majeures | `RELEASE-MIGRATION-GUIDE-001` |
| Politique LTS (Long Term Support) | `RELEASE-LTS-001` |
| Automatisation CI/CD release (wheel, PyPI, GitHub Release automatique) | post-roadmap |
| Versionnement des modules Forge indépendamment du core | post-roadmap |
| Semantic Release automatique basé sur les messages de commit | post-roadmap |

---

## Voir aussi

- [Vue d'ensemble Release et compatibilité](release-and-compatibility.md)
- [Politique de dépréciation](deprecation-policy.md), cycle annonce → retrait
- [Matrice de compatibilité](compatibility.md), Python, MariaDB, Node.js
- [Guide de migration](../features/migration-guide.md), passer d'une version à l'autre
- [Contrat de stabilité](stability-contract.md), API publique, interne, expérimentale

---

*Guide défini lors de RELEASE-POLICY-001 (Phase 8, Release et compatibilité).*
