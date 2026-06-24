# Référence des commandes Forge

Cette page liste toutes les commandes du CLI `forge`.
Trois modes d'invocation équivalents :

```bash
forge <commande>           # via entry point pip (recommandé)
python -m forge <commande> # via module Python
python forge.py <commande> # script direct (développement)
```

Pour l'aide complète d'une section : `forge --help`.

---

## Vue d'ensemble

La CLI Forge couvre quatre familles d'usages :

| Famille | Rôle | Sections de cette page |
|---|---|---|
| **Création de projet** | Démarrer un projet Forge à partir d'un profil starter | [Commandes de projet](#commandes-de-projet) |
| **Génération** | Créer entités, CRUD, pages publiques, migrations SQL | [Entités](#commandes-dentites), [Pages publiques](#commandes-de-pages-publiques), [Base de données](#commandes-de-base-de-donnees) |
| **Diagnostic** | Contrôler la santé du projet avant commit ou release | [`doctor`](#forge-doctor), [`project:check`](#forge-projectcheck), [`project:audit`](#forge-projectaudit) |
| **Configuration** | Initialiser auth, médias, déploiement | [Authentification](#commandes-dauthentification), [Médias et JavaScript](#commandes-medias-et-javascript) |

Toutes les commandes ci-dessous appartiennent au **core Forge** (`forge-mvc`).
Les commandes livrées par les modules optionnels sont documentées avec chaque
module, dans l'espace qui leur est dédié.

---

## Commandes essentielles

Tableau synthétique des commandes utilisées quotidiennement.

| Besoin | Commande | Statut |
|---|---|---|
| Créer un projet | [`forge new`](#forge-new) | Core |
| Lancer le projet (dev) | [`forge run`](#forge-run) | Core |
| Mettre à jour Forge | [`forge update`](#forge-update) | Core |
| Diagnostic large | [`forge doctor`](#forge-doctor) | Core |
| Contrôle strict (CI) | [`forge project:check`](#forge-projectcheck) | Core |
| Audit détaillé | [`forge project:audit`](#forge-projectaudit) | Core |
| Voir les routes | [`forge routes:list`](#forge-routeslist) | Core |
| Créer une entité | [`forge make:entity`](#forge-makeentity) | Core |
| Valider les entités JSON | [`forge entity:validate`](#forge-entityvalidate) | Core |
| Générer les modèles Python | [`forge build:model`](#forge-buildmodel) | Core |
| Générer un CRUD complet | [`forge make:crud`](#forge-makecrud) | Core |
| Voir le statut des migrations | [`forge migration:status`](#forge-migrationstatus) | Core |
| Créer une migration | [`forge migration:make`](#forge-migrationmake) | Core |
| Appliquer les migrations | [`forge migration:apply`](#forge-migrationapply) | Core |
| Initialiser l'auth | [`forge auth:init`](#forge-authinit) | Core |
| Créer un utilisateur | [`forge auth:user:create`](#forge-authusercreate) | Core |

---

## Parcours rapides

Scénarios d'enchaînement des commandes — copiables tels quels.

### Créer une application minimale

```bash
forge new GestionVentes
cd GestionVentes
forge doctor
forge run
```

`forge new` génère le squelette ; `forge doctor` valide la configuration
locale ; `forge run` démarre le serveur de développement
(point d'entrée officiel ; remplace `python app.py` et `scripts/dev-server.sh`).

### Créer une entité et générer un CRUD

```bash
forge make:entity Produit
forge entity:validate
forge build:model
forge make:crud Produit
forge routes:list
```

`make:entity` crée le JSON de l'entité ; `entity:validate` vérifie la
conformité au schéma ; `build:model` régénère les modèles Python ;
`make:crud` génère contrôleurs et vues ; `routes:list` confirme que les
nouvelles routes sont déclarées.

### Vérifier un projet avant commit

```bash
forge doctor
forge project:check
forge project:audit
```

`doctor` reste tolérant (lecture seule) ; `project:check` est CI-ready
(échec si convention violée) ; `project:audit` produit un rapport
détaillé non destructif.

### Gérer les migrations

```bash
forge migration:status
forge migration:make
forge migration:apply
forge migration:status
```

Le `status` final confirme que toutes les migrations sont appliquées.
`migration:diff` peut aider à générer le SQL à partir d'une modification
d'entité.

### Ajouter une page publique

```bash
forge make:public-page accueil
forge routes:list
```

Variantes : `make:public-list` (liste paginée), `make:public-show`
(fiche), `make:public-form` (formulaire), `make:public-contact` (page
de contact).

## Commandes de projet

<details markdown="1" id="forge-new">
<summary><code>forge new</code> - Crée un nouveau projet Forge à partir d'un profil starter</summary>

Crée un nouveau projet Forge à partir d'un profil starter.

```bash
forge new <NomProjet>
forge new <NomProjet> --profile <profil>
```

**Options :**

- `--profile <nom>` — profil à utiliser (défaut : `utilisateurs-auth`)

**Profils disponibles :**

| Profil | Description |
|---|---|
| `first-crud-generated` | CRUD généré sur une entité neutre |
| `utilisateurs-auth` | Login, sessions, routes protégées, CSRF |
| `auth-mfa` | Auth + MFA TOTP |

**Exemple :**

```bash
forge new GestionVentes
forge new MonAppli --profile auth-mfa
```

**Voir aussi :** [Profils de projet](profils.md)

</details>

<details markdown="1" id="forge-run">
<summary><code>forge run</code> - Point d'entrée officiel pour lancer Forge (dev + autoreload / refus prod)</summary>

**Rôle :** point d'entrée officiel pour lancer Forge. Remplace l'usage
direct de `python app.py` et `scripts/dev-server.sh`.

```bash
forge run
forge run --env dev
forge run --env prod
forge run --no-reload
```

**Comportement :**

- `APP_ENV=dev` (défaut) — superviseur d'autoreload :
  `forge run` spawne `python app.py` comme sous-processus, surveille
  les fichiers du projet (polling `stat()`) et redémarre automatiquement
  le serveur dès qu'un fichier surveillé change.
  Avec `--no-reload` : délégation à `scripts/dev-server.sh` (POSIX) ou
  fallback `python app.py`.
- `APP_ENV=prod` — refuse le serveur intégré et imprime la stratégie
  WSGI recommandée (Gunicorn + reverse proxy). Code de sortie non nul.

**Fichiers surveillés (dev, autoreload) :**

- `app.py`, `config.py`, `env/dev` ;
- `mvc/**/*.{py,html,json,sql}` ;
- `core/**/*.py`.

**Dossiers ignorés :** `.venv/`, `__pycache__/`, `.pytest_cache/`,
`.ruff_cache/`, `.mypy_cache/`, `storage/`, `logs/`, `site/`,
`node_modules/`, `.git/`, `build/`, `dist/`.

**Options :**

- `--env dev|prod` — force l'environnement (sinon lit `APP_ENV`, défaut `dev`).
- `--no-reload` — désactive l'autoreload (mode legacy : `dev-server.sh`).
- `-h`, `--help` — affiche l'aide sans rien exécuter.

**Prérequis :** lancé depuis la racine d'un projet Forge (`app.py` + `mvc/`).

**Limites :** autoreload par polling `stat()` (pas d'inotify) ; pas de
live reload navigateur ni de WebSocket ; ne lance pas Gunicorn
automatiquement en prod.

**Voir aussi :** [Déploiement WSGI minimal](../deployment/wsgi-deployment.md),
[Limites de production](../deployment/production-limits.md).

**Statut :** core.

</details>

<details markdown="1" id="forge-update">
<summary><code>forge update</code> - met à jour Forge dans l'environnement courant (.venv / pipx)</summary>

**Rôle :** met à jour le package `forge-mvc` dans l'environnement
Python courant (`sys.executable`). Cible le `.venv` du projet ou le
venv pipx isolé selon le contexte d'installation.

**Quand l'utiliser :** quand un projet a été créé avec une ancienne
beta et qu'il faut s'aligner sur la dernière version de Forge.

```bash
forge update            # pip install --upgrade forge-mvc
forge update --pre      # idem avec --pre (utile en beta)
forge update --check    # affiche version installée + commande, ne modifie rien
forge update --dry-run  # affiche la commande pip, ne l'exécute pas
```

**Modes :**

- défaut — lance `pip install --upgrade forge-mvc` via `sys.executable` ;
- `--pre` — ajoute `--pre` à la commande pip (versions de
  pré-release ; recommandé tant que Forge reste en beta) ;
- `--check` — mode lecture seule, affiche la version installée et
  la commande qui serait lancée ;
- `--dry-run` — affiche la commande pip sans l'exécuter.

**Cas pipx :** si Forge a été installé via `pipx install forge-mvc`,
`sys.executable` pointe vers `~/.local/share/pipx/venvs/forge-mvc/`.
Dans ce cas, `forge update` n'exécute **pas** `pip install` (qui ne
mettrait pas à jour l'install pipx globale) — la commande affiche
le bon `pipx upgrade forge-mvc` à lancer manuellement.

**Options :**

- `--pre` — autorise les versions de pré-release ;
- `--check` — mode vérification, lecture seule ;
- `--dry-run` — affiche la commande sans l'exécuter ;
- `-h`, `--help` — affiche l'aide sans rien exécuter.

**Hors périmètre :** aucune migration projet, aucun fichier `env/*`
touché, aucun fichier généré sous `mvc/` modifié, aucune mise à jour
du `pyproject.toml` du projet.

**Après mise à jour :** lancer `forge doctor` pour vérifier la
cohérence du projet.

**Statut :** core.

</details>

<details markdown="1" id="forge-doctor">
<summary><code>forge doctor</code> - diagnostic large et tolérant de l'environnement courant (lecture seule)</summary>

**Rôle :** diagnostic large et tolérant de l'environnement courant (lecture seule).

**Quand l'utiliser :** quotidien — première commande à lancer après `forge new`, et avant un commit.

```bash
forge doctor
```

Vérifie : version Python, chargement `.env`, structure `mvc/`, entités, migrations, i18n, templates.

**À ne pas confondre avec :**

- [`forge project:check`](#forge-projectcheck) — strict (échec si convention violée), pour la CI ;
- [`forge project:audit`](#forge-projectaudit) — rapport détaillé non destructif.

**Statut :** core.

</details>

<details markdown="1" id="forge-projectcheck">
<summary><code>forge project:check</code> - contrôle strict des conventions Forge — conçu pour la CI</summary>

**Rôle :** contrôle strict des conventions Forge — conçu pour la CI.

```bash
forge project:check
```

Retourne code de sortie non-nul si le projet ne respecte pas les conventions Forge.
Doit être lancé depuis la racine d'un projet Forge.

**À ne pas confondre avec :** `forge doctor` (tolérant, lecture seule).

**Statut :** core.

</details>

<details markdown="1" id="forge-projectaudit">
<summary><code>forge project:audit</code> - Rapport d'audit détaillé non destructif</summary>

Rapport d'audit détaillé non destructif.

```bash
forge project:audit
```

Inspecte la structure complète du projet et produit un rapport humain lisible.
Doit être lancé depuis la racine d'un projet Forge.

</details>

<details markdown="1" id="forge-routeslist">
<summary><code>forge routes:list</code> - Affiche toutes les routes déclarées dans mvc/routes.py</summary>

Affiche toutes les routes déclarées dans `mvc/routes.py`.

```bash
forge routes:list
```

</details>

## Commandes d'entités

<details markdown="1" id="forge-makeentity">
<summary><code>forge make:entity</code> - Génère une entité JSON et son modèle Python</summary>

Génère une entité JSON et son modèle Python.

```bash
forge make:entity
forge make:entity <NomEntite>
forge make:entity <NomEntite> --no-input
```

**Options :**

- `--no-input` — génère un gabarit minimal sans poser de questions

Crée `mvc/entities/<NomEntite>/<nomEntite>.json` et `mvc/entities/<NomEntite>/<nomEntite>.py`.

**Exemple :**

```bash
forge make:entity Contact
```

</details>

<details markdown="1" id="forge-makecrud">
<summary><code>forge make:crud</code> - générer un CRUD complet (liste, fiche, formulaires de création, modification, suppression) à partir d'une entité Forge déjà déclarée</summary>

**Rôle :** générer un CRUD complet (liste, fiche, formulaires de création, modification, suppression) à partir d'une entité Forge déjà déclarée.

**Quand l'utiliser :** après création et validation d'une entité via `make:entity` + `entity:validate`.

```bash
forge make:crud <NomEntite>
forge make:crud <NomEntite> --dry-run
```

**Options :**

- `--dry-run` — affiche les fichiers qui seraient créés sans écrire

**Exemple :**

```bash
forge make:entity Contact && forge make:crud Contact
```

**Effets :**

- génère les contrôleurs CRUD applicatifs, **typés** : import
  `Request`/`Response` et signatures `def <action>(request: Request) -> Response:`
  (DX-TYPED-SKELETONS-001) ;
- génère les vues HTML associées (liste, fiche, formulaires) ;
- préserve les fichiers utilisateurs déjà présents (write-if-new — voir charte §9).

**À ne pas confondre avec :**

- [`forge make:entity`](#forge-makeentity) — crée seulement le JSON d'entité, pas le CRUD ;
- [`forge make:pivot-crud`](#forge-makepivot-crud) — pour les pivots avec attributs ;
- [`forge build:model`](#forge-buildmodel) — régénère uniquement les modèles Python, pas les contrôleurs/vues.

**Statut :** core.

</details>

<details markdown="1" id="forge-makerelation">
<summary><code>forge make:relation</code> - Déclare une relation entre deux entités dans mvc/entities/relations.json</summary>

Déclare une relation entre deux entités dans `mvc/entities/relations.json`.

```bash
forge make:relation
```

Mode interactif : pose les questions sur les deux entités et le type de relation.

</details>

<details markdown="1" id="forge-makepivot-crud">
<summary><code>forge make:pivot-crud</code> - Génère un sous-CRUD dédié pour un pivot porteur d'attributs</summary>

Génère un sous-CRUD dédié pour un pivot porteur d'attributs.

```bash
forge make:pivot-crud <EntiteSource> <nom_relation>
```

À utiliser quand une relation many-to-many comporte des champs propres (date,
quantité, statut…) qui méritent leurs propres écrans d'édition.

</details>

<details markdown="1" id="forge-syncentity">
<summary><code>forge sync:entity</code> - Régénère les fichiers modèles d'une entité depuis son JSON</summary>

Régénère les fichiers modèles d'une entité depuis son JSON.

```bash
forge sync:entity <NomEntite>
```

</details>

<details markdown="1" id="forge-syncrelations">
<summary><code>forge sync:relations</code> - Régénère mvc/entities/relations.sql depuis relations.json</summary>

Régénère `mvc/entities/relations.sql` depuis `relations.json`.

```bash
forge sync:relations
```

</details>

<details markdown="1" id="forge-buildmodel">
<summary><code>forge build:model</code> - Régénère tous les modèles Python depuis leurs entités JSON</summary>

Régénère tous les modèles Python depuis leurs entités JSON.

```bash
forge build:model
forge build:model --dry-run
```

</details>

<details markdown="1" id="forge-checkmodel">
<summary><code>forge check:model</code> - Vérifie la cohérence des modèles : JSON valide, champs requis, types reconnus</summary>

Vérifie la cohérence des modèles : JSON valide, champs requis, types reconnus.

```bash
forge check:model
```

</details>

<details markdown="1" id="forge-entityvalidate">
<summary><code>forge entity:validate</code> - Valide les entités et les relations contre les schémas JSON Forge</summary>

Valide les entités (`mvc/entities/*.json`) et `relations.json` contre les
schémas JSON Forge.

```bash
forge entity:validate
```

Vérifie la structure JSON, les références entre fichiers et les types
reconnus. Sort en erreur si un fichier viole le schéma.

</details>

## Commandes de pages publiques

Ces commandes génèrent des pages accessibles sans authentification.

<details markdown="1" id="forge-makepublic-page">
<summary><code>forge make:public-page</code> - Génère une page statique publique</summary>

Génère une page statique publique.

```bash
forge make:public-page <NomPage>
```

</details>

<details markdown="1" id="forge-makepublic-list">
<summary><code>forge make:public-list</code> - Génère une liste publique paginée pour une entité</summary>

Génère une liste publique paginée pour une entité.

```bash
forge make:public-list <NomEntite>
```

</details>

<details markdown="1" id="forge-makepublic-show">
<summary><code>forge make:public-show</code> - Génère une fiche publique détaillée pour une entité</summary>

Génère une fiche publique détaillée pour une entité.

```bash
forge make:public-show <NomEntite>
```

</details>

<details markdown="1" id="forge-makepublic-form">
<summary><code>forge make:public-form</code> - Génère un formulaire public pour une entité</summary>

Génère un formulaire public pour une entité.

```bash
forge make:public-form <NomEntite>
```

</details>

<details markdown="1" id="forge-makepublic-contact">
<summary><code>forge make:public-contact</code> - Génère une page de contact publique</summary>

Génère une page de contact publique.

```bash
forge make:public-contact <NomPage>
```

**Voir aussi :** [Pages publiques](pages-publiques.md)

</details>

## Commandes de base de données

<details markdown="1" id="forge-dbinit">
<summary><code>forge db:init</code> - Crée la base de données depuis les entités définies</summary>

Crée la base de données depuis les entités définies.

```bash
forge db:init
```

Requiert les variables `DB_ADMIN_*` dans `env/dev`.
Crée la base, les tables, et insère les données initiales si présentes.

</details>

<details markdown="1" id="forge-dbapply">
<summary><code>forge db:apply</code> - Applique le schéma SQL courant</summary>

Applique le schéma SQL courant.

```bash
forge db:apply
```

</details>

<details markdown="1" id="forge-migrationstatus">
<summary><code>forge migration:status</code> - Affiche le statut des migrations : appliquées, en attente</summary>

Affiche le statut des migrations : appliquées, en attente.

```bash
forge migration:status
```

</details>

<details markdown="1" id="forge-migrationapply">
<summary><code>forge migration:apply</code> - Applique les migrations SQL en attente dans mvc/migrations/</summary>

Applique les migrations SQL en attente dans `mvc/migrations/`.

```bash
forge migration:apply              # applique réellement en base
forge migration:apply --dry-run    # liste + imprime le SQL, sans rien écrire
```

`--dry-run` affiche les migrations PENDING et leur SQL **sans rien appliquer
ni écrire en base** ; relancer sans `--dry-run` pour appliquer réellement.

</details>

<details markdown="1" id="forge-migrationmake">
<summary><code>forge migration:make</code> - Crée un nouveau fichier de migration SQL horodaté</summary>

Crée un nouveau fichier de migration SQL horodaté.

```bash
forge migration:make <nom>
```

Crée `mvc/migrations/<timestamp>_<nom>.sql`.

</details>

<details markdown="1" id="forge-migrationdiff">
<summary><code>forge migration:diff</code> - Génère un diff SQL entre la définition d'une entité et la base de données actuelle</summary>

Génère un diff SQL entre la définition d'une entité et la base de données actuelle.

```bash
forge migration:diff --entity <NomEntite>
```

</details>

## Commandes de starters et modules

<details markdown="1" id="forge-modulelist">
<summary><code>forge module:list</code> - Liste les modules Forge disponibles</summary>

Liste les modules Forge disponibles.

```bash
forge module:list
```

</details>

<details markdown="1" id="forge-moduleinstall">
<summary><code>forge module:install</code> - Installe un module Forge dans le projet</summary>

Installe un module Forge dans le projet.

```bash
forge module:install <nom>
forge module:install <nom> --path <chemin>
forge module:install <nom> --dry-run
```

</details>

<details markdown="1" id="forge-modulefiles">
<summary><code>forge module:files</code> - Copie les fichiers d'un module dans le projet sans modifier les routes</summary>

Copie les fichiers d'un module dans le projet sans modifier les routes.

```bash
forge module:files <nom>
```

</details>

<details markdown="1" id="forge-moduleroutes">
<summary><code>forge module:routes</code> - Injecte les routes d'un module dans mvc/routes.py</summary>

Injecte les routes d'un module dans `mvc/routes.py`.

```bash
forge module:routes <nom>
```

</details>

## Commandes d'authentification

<details markdown="1" id="forge-authinit">
<summary><code>forge auth:init</code> - Initialise les tables et fichiers d'authentification du projet</summary>

Initialise les tables et fichiers d'authentification du projet.

```bash
forge auth:init
```

Crée les fichiers SQL (`users.sql`, `sessions.sql`, etc.), les contrôleurs
et les formulaires d'authentification.

**Voir aussi :** [Auth](../features/auth.md)

</details>

<details markdown="1" id="forge-authdoctor">
<summary><code>forge auth:doctor</code> - Diagnostic du système d'authentification</summary>

Diagnostic du système d'authentification.

```bash
forge auth:doctor
```

</details>

<details markdown="1" id="forge-authstatus">
<summary><code>forge auth:status</code> - Affiche l'état des briques d'authentification installées (modules disponibles, contrats vérifiés)</summary>

Affiche l'état des briques d'authentification installées (modules disponibles, contrats vérifiés).

```bash
forge auth:status
```

</details>

<details markdown="1" id="forge-authlist-sql">
<summary><code>forge auth:list-sql</code> - Affiche les fichiers SQL optionnels du système d'authentification et leur statut (présent / absent)</summary>

Affiche les fichiers SQL optionnels du système d'authentification et leur statut (présent / absent).

```bash
forge auth:list-sql
```

</details>

<details markdown="1" id="forge-authusershow">
<summary><code>forge auth:user:show</code> - Affiche les détails d'un compte utilisateur</summary>

Affiche les détails d'un compte utilisateur.

```bash
forge auth:user:show --id <id>
forge auth:user:show --email <email>
```

</details>

<details markdown="1" id="forge-authusercreate">
<summary><code>forge auth:user:create</code> - Crée un compte utilisateur en base</summary>

Crée un compte utilisateur en base.

```bash
forge auth:user:create --email <email>
forge auth:user:create --email <email> --password <mot_de_passe>
forge auth:user:create --email <email> --password-prompt
```

**Options :**

- `--email <email>` — adresse email (requis)
- `--password <mdp>` — mot de passe en clair
- `--password-prompt` — saisie interactive sécurisée

</details>

<details markdown="1" id="forge-authuserlist">
<summary><code>forge auth:user:list</code> - Liste les comptes utilisateurs</summary>

Liste les comptes utilisateurs.

```bash
forge auth:user:list
```

</details>

<details markdown="1" id="forge-authuserdisable">
<summary><code>forge auth:user:disable</code> - Désactive un compte utilisateur</summary>

Désactive un compte utilisateur.

```bash
forge auth:user:disable --email <email>
```

</details>

<details markdown="1" id="forge-authuserenable">
<summary><code>forge auth:user:enable</code> - Réactive un compte utilisateur désactivé</summary>

Réactive un compte utilisateur désactivé.

```bash
forge auth:user:enable --email <email>
```

</details>

<details markdown="1" id="forge-authuserpassword">
<summary><code>forge auth:user:password</code> - Modifie le mot de passe d'un compte</summary>

Modifie le mot de passe d'un compte.

```bash
forge auth:user:password --email <email> --password <mdp>
forge auth:user:password --email <email> --password-prompt
```

</details>

<details markdown="1" id="forge-authuserroleadd">
<summary><code>forge auth:user:role:add</code> - Assigne un rôle à un utilisateur</summary>

Assigne un rôle à un utilisateur.

```bash
forge auth:user:role:add --email <email> --role <role>
```

</details>

<details markdown="1" id="forge-authuserroleremove">
<summary><code>forge auth:user:role:remove</code> - Retire un rôle d'un utilisateur</summary>

Retire un rôle d'un utilisateur.

```bash
forge auth:user:role:remove --email <email> --role <role>
```

</details>

<details markdown="1" id="forge-authuserroles">
<summary><code>forge auth:user:roles</code> - Affiche les rôles d'un utilisateur</summary>

Affiche les rôles d'un utilisateur.

```bash
forge auth:user:roles --email <email>
```

</details>

## Commandes médias et JavaScript

<details markdown="1" id="forge-uploadinit">
<summary><code>forge upload:init</code> - Configure le stockage des fichiers uploadés</summary>

Configure le stockage des fichiers uploadés.

```bash
forge upload:init
```

Crée `storage/uploads/` et ses sous-dossiers (`images`, `documents`, `tmp`).

</details>

<details markdown="1" id="forge-mediainit">
<summary><code>forge media:init</code> - Configure le stockage des médias avec génération de vignettes</summary>

Configure le stockage des médias avec génération de vignettes.

```bash
forge media:init
```

Crée `storage/uploads/` avec sous-dossiers `images/thumbnail` et `images/medium`.

</details>

<details markdown="1" id="forge-jsinit">
<summary><code>forge js:init</code> - Installe une bibliothèque JavaScript dans le projet</summary>

Installe une bibliothèque JavaScript dans le projet.

```bash
forge js:init htmx
forge js:init alpine
forge js:init htmx-alpine
```

</details>

## Commandes de déploiement

<details markdown="1" id="forge-deployinit">
<summary><code>forge deploy:init</code> - Initialise les fichiers de configuration de déploiement</summary>

Initialise les fichiers de configuration de déploiement.

```bash
forge deploy:init
```

Crée `deploy/nginx/forge-app.conf`, `deploy/systemd/forge-app.service` et
`deploy/README_DEPLOY.md`.

</details>

<details markdown="1" id="forge-deploycheck">
<summary><code>forge deploy:check</code> - Vérifie la configuration de déploiement et l'environnement cible</summary>

Vérifie la configuration de déploiement et l'environnement cible.

```bash
forge deploy:check
```

</details>

## Commandes de guidance agent IA

<details markdown="1" id="forge-agentsinit">
<summary><code>forge agents:init</code> - Génère ou rafraîchit la guidance agent IA du projet</summary>

Génère la couche de guidance agent IA d'une application Forge (ADR-047) :
`CLAUDE.md` et `AGENTS.md` (briefing distillé) et l'ADR d'amorçage
`docs/adr/001-adopter-forge.md`.

```bash
forge agents:init            # crée les fichiers manquants (write-if-new)
forge agents:init --check    # diagnostic en lecture seule
forge agents:init --force    # rafraîchit CLAUDE.md et AGENTS.md
forge agents:init --settings # ajoute aussi .claude/settings.json
```

Par défaut, aucun fichier existant n'est écrasé. `--force` réécrit le briefing
(`CLAUDE.md`, `AGENTS.md`) depuis la version de Forge installée, sans toucher
`docs/adr/001-adopter-forge.md` qui appartient au projet. `--check` signale les
fichiers absents ou un briefing divergé (code de sortie 1). `--settings` écrit en
plus `.claude/settings.json` (commandes pré-autorisées) ; c'est un choix opt-in,
non généré par `forge new`.

</details>

## Commandes de documentation

<details markdown="1" id="forge-docspdf">
<summary><code>forge docs:pdf</code> - Génère un PDF depuis la documentation du projet</summary>

Génère un PDF depuis la documentation du projet.

```bash
forge docs:pdf
```

</details>

## Commandes de schémas JSON

<details markdown="1" id="forge-schemalist">
<summary><code>forge schema:list</code> - Liste les schémas JSON Forge disponibles localement</summary>

Liste les schémas JSON Forge disponibles localement.

```bash
forge schema:list
```

Affiche les fichiers de schéma embarqués et leur version.

</details>

<details markdown="1" id="forge-schemadoctor">
<summary><code>forge schema:doctor</code> - Diagnostique les schémas JSON Forge : présence, validité, résolution des $ref</summary>

Diagnostique les schémas JSON Forge : présence, validité, résolution des `$ref`.

```bash
forge schema:doctor
```

À utiliser pour vérifier l'installation des schémas avant un `entity:validate`
ou un `rbac:validate`.

</details>

## Gestion des modules optionnels

Forge fournit dans son **cœur** une famille de commandes pour gérer le cycle de
vie des modules optionnels (mécanisme générique, ADR-016).
Ces commandes ne dépendent d'aucun module particulier : elles opèrent sur un
module désigné par son `<nom>`.

<details markdown="1" id="forge-opt-ininstall">
<summary><code>forge opt-in:install</code> - Affiche la commande d'installation du package d'un module optionnel</summary>

Affiche (sans l'exécuter) la commande `pip` d'installation du package d'un module optionnel.

```bash
forge opt-in:install <nom>
```

</details>

<details markdown="1" id="forge-opt-inremove">
<summary><code>forge opt-in:remove</code> - Affiche la commande de désinstallation du package d'un module optionnel</summary>

Miroir d'`opt-in:install` : affiche la commande de désinstallation du package.
Ne débranche pas le module du projet (voir `opt-in:disable`).

```bash
forge opt-in:remove <nom>
```

</details>

<details markdown="1" id="forge-opt-inenable">
<summary><code>forge opt-in:enable</code> - Branche un module optionnel dans le projet (optins/) — dry-run par défaut</summary>

Branche un module optionnel dans le projet (couche `optins/<nom>/`).
Dry-run par défaut ; `--apply` crée réellement les fichiers.

```bash
forge opt-in:enable <nom>            # dry-run : montre ce qui serait créé
forge opt-in:enable <nom> --apply    # crée réellement la couche projet
```

</details>

<details markdown="1" id="forge-opt-indisable">
<summary><code>forge opt-in:disable</code> - Débranche un module optionnel du projet (retire optins/) — dry-run par défaut</summary>

Inverse exact d'`opt-in:enable` : retire la couche projet `optins/<nom>/`.
Laisse le package installé (voir `opt-in:remove`).

```bash
forge opt-in:disable <nom>           # dry-run : montre ce qui serait retiré
forge opt-in:disable <nom> --apply   # retire la couche projet
```

</details>

<details markdown="1" id="forge-opt-inlist">
<summary><code>forge opt-in:list</code> - Affiche les modules optionnels officiels et leur état (lecture seule)</summary>

Liste, en lecture seule, les modules optionnels officiels et leur état
(installé, branché).

```bash
forge opt-in:list
```

</details>

## Utilitaires

<details markdown="1" id="forge-version">
<summary><code>forge --version</code> - Affiche la version courante de Forge</summary>

Affiche la version courante de Forge.

```bash
$ forge --version
Forge {{forge_version}}
```

</details>

<details markdown="1" id="forge-help">
<summary><code>forge --help</code> - Affiche l'aide générale avec toutes les commandes disponibles</summary>

Affiche l'aide générale avec toutes les commandes disponibles.

```bash
forge --help
forge help
forge -h
```

</details>

## Index alphabétique

Toutes les commandes documentées dans cette page.

| Commande | Domaine | Statut |
|---|---|---|
| [`forge auth:doctor`](#forge-authdoctor) | Authentification | Core |
| [`forge auth:init`](#forge-authinit) | Authentification | Core |
| [`forge auth:list-sql`](#forge-authlist-sql) | Authentification | Core |
| [`forge auth:status`](#forge-authstatus) | Authentification | Core |
| [`forge auth:user:create`](#forge-authusercreate) | Authentification | Core |
| [`forge auth:user:disable`](#forge-authuserdisable) | Authentification | Core |
| [`forge auth:user:enable`](#forge-authuserenable) | Authentification | Core |
| [`forge auth:user:list`](#forge-authuserlist) | Authentification | Core |
| [`forge auth:user:password`](#forge-authuserpassword) | Authentification | Core |
| [`forge auth:user:role:add`](#forge-authuserroleadd) | Authentification | Core |
| [`forge auth:user:role:remove`](#forge-authuserroleremove) | Authentification | Core |
| [`forge auth:user:roles`](#forge-authuserroles) | Authentification | Core |
| [`forge auth:user:show`](#forge-authusershow) | Authentification | Core |
| [`forge build:model`](#forge-buildmodel) | Entités | Core |
| [`forge check:model`](#forge-checkmodel) | Entités | Core |
| [`forge db:apply`](#forge-dbapply) | Base de données | Core |
| [`forge db:init`](#forge-dbinit) | Base de données | Core |
| [`forge deploy:check`](#forge-deploycheck) | Déploiement | Core |
| [`forge deploy:init`](#forge-deployinit) | Déploiement | Core |
| [`forge docs:pdf`](#forge-docspdf) | Documentation | Core |
| [`forge doctor`](#forge-doctor) | Diagnostic | Core |
| [`forge entity:validate`](#forge-entityvalidate) | Entités | Core |
| [`forge --help`](#forge-help) | Utilitaires | Core |
| [`forge js:init`](#forge-jsinit) | Médias et JavaScript | Core |
| [`forge make:crud`](#forge-makecrud) | Entités | Core |
| [`forge make:entity`](#forge-makeentity) | Entités | Core |
| [`forge make:pivot-crud`](#forge-makepivot-crud) | Entités | Core |
| [`forge make:public-contact`](#forge-makepublic-contact) | Pages publiques | Core |
| [`forge make:public-form`](#forge-makepublic-form) | Pages publiques | Core |
| [`forge make:public-list`](#forge-makepublic-list) | Pages publiques | Core |
| [`forge make:public-page`](#forge-makepublic-page) | Pages publiques | Core |
| [`forge make:public-show`](#forge-makepublic-show) | Pages publiques | Core |
| [`forge make:relation`](#forge-makerelation) | Entités | Core |
| [`forge media:init`](#forge-mediainit) | Médias et JavaScript | Core |
| [`forge migration:apply`](#forge-migrationapply) | Base de données | Core |
| [`forge migration:diff`](#forge-migrationdiff) | Base de données | Core |
| [`forge migration:make`](#forge-migrationmake) | Base de données | Core |
| [`forge migration:status`](#forge-migrationstatus) | Base de données | Core |
| [`forge module:files`](#forge-modulefiles) | Starters et modules | Core |
| [`forge module:install`](#forge-moduleinstall) | Starters et modules | Core |
| [`forge module:list`](#forge-modulelist) | Starters et modules | Core |
| [`forge module:routes`](#forge-moduleroutes) | Starters et modules | Core |
| [`forge new`](#forge-new) | Projet | Core |
| [`forge project:audit`](#forge-projectaudit) | Projet | Core |
| [`forge project:check`](#forge-projectcheck) | Projet | Core |
| [`forge routes:list`](#forge-routeslist) | Projet | Core |
| [`forge schema:doctor`](#forge-schemadoctor) | Schémas JSON | Core |
| [`forge schema:list`](#forge-schemalist) | Schémas JSON | Core |
| [`forge sync:entity`](#forge-syncentity) | Entités | Core |
| [`forge sync:relations`](#forge-syncrelations) | Entités | Core |
| [`forge upload:init`](#forge-uploadinit) | Médias et JavaScript | Core |
| [`forge --version`](#forge-version) | Utilitaires | Core |
