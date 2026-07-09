# Référence des commandes Forge

Catalogue des commandes du CLI `forge`, par famille.
Chaque commande renvoie vers sa page de référence détaillée (usage, options, exemples).

Trois modes d'invocation équivalents :

```bash
forge <commande>           # via entry point pip (recommandé)
python -m forge <commande> # via module Python
python forge.py <commande> # script direct (développement)
```

Aide intégrée : `forge --help` (et `forge --version`).

---

## Parcours rapides

Scénarios d'enchaînement des commandes, copiables tels quels.

### Créer une application minimale

```bash
forge new GestionVentes
cd GestionVentes
forge doctor
forge run
```

`forge new` génère le squelette ; `forge doctor` valide la configuration locale ; `forge run` démarre le serveur de développement.

### Créer une entité et générer un CRUD

```bash
forge make:entity Produit
forge entity:validate
forge build:model
forge make:crud Produit
forge routes:list
```

`make:entity` crée le JSON de l'entité ; `entity:validate` vérifie la conformité au schéma ; `build:model` régénère les modèles Python ; `make:crud` génère contrôleurs et vues ; `routes:list` confirme les nouvelles routes.

### Vérifier un projet avant commit

```bash
forge doctor
forge project:check
forge project:audit
```

`doctor` reste tolérant (lecture seule) ; `project:check` est CI-ready (échec si convention violée) ; `project:audit` produit un rapport détaillé non destructif.

### Gérer les migrations

```bash
forge migration:status
forge migration:make
forge migration:apply
forge migration:status
```

Le `status` final confirme que toutes les migrations sont appliquées.

### Ajouter une page publique

```bash
forge make:public-page accueil
forge routes:list
```

---

## Projet et exécution

| Commande | Rôle | Détail |
|---|---|---|
| `forge new` | crée un nouveau projet à partir du squelette | [Démarrer](../guide/getting-started.md) |
| `forge skeleton:upgrade` | ajoute les fichiers du squelette manquants (write-if-new) | [skeleton:upgrade](../cli-commands/skeleton_upgrade.md) |
| `forge run` | serveur de développement (HTTPS, autoreload) | [run](../cli-project/run.md) |
| `forge update` | met à jour Forge dans le projet | [update](../cli-project/update.md) |
| `forge doctor` | diagnostic large, lecture seule | [doctor](../cli-project/doctor.md) |
| `forge project:check` | contrôle strict, prêt pour la CI | [project:check](../cli-project/project_check.md) |
| `forge project:audit` | rapport d'audit détaillé, non destructif | [project:audit](../cli-project/project_audit.md) |
| `forge routes:list` | liste les routes déclarées | (sortie console) |

## Entités et modèles

| Commande | Rôle | Détail |
|---|---|---|
| `forge make:entity` | crée le JSON d'une entité | [make:entity](../entities/modules/make_entity.md) |
| `forge entity:validate` | valide les contrats JSON d'entités | [entity:validate](../entities/modules/entity_validate.md) |
| `forge entity:doc` | documente entités et relations (Markdown + Mermaid) | [entity:doc](../entities/modules/entity_doc.md) |
| `forge build:model` | génère les modèles Python depuis le JSON | [build:model](../entities/modules/model.md) |
| `forge sync:entity` | synchronise entité et modèle généré | [modèle](../entities/modules/model.md) |
| `forge make:relation` | déclare une relation entre entités | [make:relation](../entities/modules/make_relation.md) |
| `forge check:model` | vérifie la cohérence des modèles | [build:model](../entities/modules/model.md) |
| `forge sync:relations` | régénère `relations.sql` | [make:relation](../entities/modules/make_relation.md) |

## CRUD et pages publiques

| Commande | Rôle | Détail |
|---|---|---|
| `forge make:crud` | CRUD complet (contrôleur, vues, routes) | [make:crud](../entities/modules/make_crud.md) |
| `forge make:auth` | flux de connexion (contrôleur, vue, routes) | [make:auth](../cli-security/make_auth.md) |
| `forge make:pivot-crud` | CRUD pour table pivot enrichie (opt-in pivot) | [catalogue opt-ins](../optins/index.md) |
| `forge make:public-page` | page publique simple | [pages publiques](../cli-public/public_page.md) |
| `forge make:public-list` | liste paginée | [liste publique](../cli-public/public_list.md) |
| `forge make:public-show` | fiche de détail | [fiche publique](../cli-public/public_show.md) |
| `forge make:public-form` | formulaire | [formulaire public](../cli-public/public_form.md) |
| `forge make:public-contact` | page de contact | [contact public](../cli-public/public_contact.md) |

## Base de données

| Commande | Rôle | Détail |
|---|---|---|
| `forge db:config` | amorce les variables d'environnement du backend | [db:config](../entities/modules/db_config.md) |
| `forge db:init` | provisionne la base et le compte applicatif | [db:init](../entities/modules/db_init.md) |
| `forge db:apply` | applique le schéma des entités (DDL) | [db:apply](../entities/modules/db_apply.md) |
| `forge migration:status` | état des migrations SQL | [migrations](../entities/modules/migrations.md) |
| `forge migration:make` | crée une migration | [migrations](../entities/modules/migrations.md) |
| `forge migration:apply` | applique les migrations | [migrations](../entities/modules/migrations.md) |
| `forge migration:diff` | génère le SQL depuis une modification d'entité | [migrations](../entities/modules/migrations.md) |

Choix du moteur (SQLite, MariaDB, PostgreSQL, SQL Server) : [Bases de données](../guide/bases-de-donnees.md).

## Authentification

| Commande | Rôle | Détail |
|---|---|---|
| `forge auth:init` | initialise l'authentification | [auth](../cli-security/auth.md) |
| `forge auth:user:create` | crée un utilisateur | [auth](../cli-security/auth.md) |
| `forge auth:user:list` | liste les utilisateurs | [auth](../cli-security/auth.md) |
| `forge auth:doctor` | diagnostic de l'authentification | [auth](../cli-security/auth.md) |
| `forge auth:status` | état de la configuration auth | [auth](../cli-security/auth.md) |
| `forge auth:list-sql` | affiche les fichiers SQL d'authentification | [auth](../cli-security/auth.md) |
| `forge auth:user:show` | affiche les détails d'un compte utilisateur | [auth](../cli-security/auth.md) |
| `forge auth:user:disable` | désactive un compte utilisateur | [auth](../cli-security/auth.md) |
| `forge auth:user:enable` | réactive un compte utilisateur | [auth](../cli-security/auth.md) |
| `forge auth:user:password` | modifie le mot de passe d'un compte | [auth](../cli-security/auth.md) |
| `forge auth:user:roles` | affiche les rôles d'un utilisateur | [auth](../cli-security/auth.md) |
| `forge auth:user:role:add` | assigne un rôle à un utilisateur | [auth](../cli-security/auth.md) |
| `forge auth:user:role:remove` | retire un rôle d'un utilisateur | [auth](../cli-security/auth.md) |

## Médias et front

| Commande | Rôle | Détail |
|---|---|---|
| `forge upload:init` | prépare le stockage des uploads (opt-in files) | [uploads](../cli-assets/uploads.md) |
| `forge media:init` | prépare le stockage des médias (opt-in images) | [uploads](../cli-assets/uploads.md) |
| `forge js:init` | installe HTMX / Alpine.js | [front](../cli-assets/front.md) |
| `forge i18n:init` | initialise les catalogues d'i18n (opt-in i18n) | [i18n](../cli-assets/i18n.md) |
| `forge i18n:check` | vérifie les catalogues d'i18n | [i18n](../cli-assets/i18n.md) |

## Schémas, documentation, agent IA

| Commande | Rôle | Détail |
|---|---|---|
| `forge schema:doctor` | diagnostique les schémas JSON | [schema:doctor](../cli-schemas/schema_doctor.md) |
| `forge schema:list` | liste les schémas JSON | [schema:list](../cli-schemas/schema_list.md) |
| `forge docs:pdf` | génère le PDF de la documentation | [docs:pdf](../cli-docs/quarkdown.md) |

### Guidance agent IA { #forge-agentsinit }

| Commande | Rôle | Détail |
|---|---|---|
| `forge agents:init` | crée ou rafraîchit la couche de guidance agent (write-if-new) | [Guidance agent IA](../features/agents.md) |

## Déploiement (opt-in)

| Commande | Rôle | Détail |
|---|---|---|
| `forge deploy:init` | génère les gabarits Nginx / systemd / WSGI | [Déploiement](../deploy/reference.md) |
| `forge deploy:check` | vérifie la configuration de déploiement | [Déploiement](../deploy/reference.md) |

## Gestion des modules optionnels { #opt-ins-branchement-projet }

<a id="commandes-forge-iot"></a>

Forge fournit dans son cœur une famille de commandes pour gérer le cycle de vie des modules optionnels (mécanisme générique, ADR-016).
Les commandes propres à un module (par exemple `forge iot:*`) sont documentées dans l'espace de ce module (ADR-042), pas ici.

| Commande | Rôle | Détail |
|---|---|---|
| `forge module:list` | liste les modules déclarés | [modules](../cli-deploy/modules.md) |
| `forge module:install` | installe déclarativement un module | [modules](../cli-deploy/modules.md) |
| `forge module:files` | installe les fichiers d'un module | [modules](../cli-deploy/modules.md) |
| `forge module:routes` | affiche les routes d'un module à coller | [modules](../cli-deploy/modules.md) |
| `forge module:remove` | retire un module | [modules](../cli-deploy/modules.md) |
| `forge opt-in:install` | affiche la commande `pip` d'installation d'un opt-in | [install](../cli-optins/install.md) |
| `forge opt-in:remove` | affiche la commande de désinstallation | [remove](../cli-optins/remove.md) |
| `forge opt-in:enable` | branche un opt-in dans le projet (`optins/`) | [enable](../cli-optins/enable.md) |
| `forge opt-in:disable` | débranche un opt-in du projet | [disable](../cli-optins/disable.md) |
| `forge opt-in:list` | état des opt-ins officiels (lecture seule) | [list](../cli-optins/list.md) |

Catalogue complet des opt-ins : [Opt-ins officiels](../optins/index.md).

## Utilitaires

| Commande | Rôle |
|---|---|
| `forge --version` | affiche la version de Forge |
| `forge --help` | affiche l'aide du CLI |
