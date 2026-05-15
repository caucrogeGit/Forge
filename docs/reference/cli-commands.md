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

## Commandes de projet

### `forge new`

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
| `contact-simple` | CRUD simple de contacts |
| `utilisateurs-auth` | Login, sessions, routes protégées, CSRF |
| `carnet-contacts` | Carnet relationnel avec relations SQL |
| `suivi-comportement-eleves` | Auth, dashboard, entités liées |
| `communes-sejours` | Pages publiques, formulaire, mail |
| `auth-mfa` | Auth + MFA TOTP (nécessite forge-mvc-mfa) |

**Exemple :**

```bash
forge new GestionVentes
forge new MonAppli --profile auth-mfa
```

**Voir aussi :** [Profils de projet](profils.md)

---

### `forge doctor`

Diagnostic large et tolérant de l'environnement courant (lecture seule).

```bash
forge doctor
```

Vérifie : version Python, chargement `.env`, structure `mvc/`, entités, migrations, i18n, templates.

---

### `forge project:check`

Contrôle strict des conventions — conçu pour la CI.

```bash
forge project:check
```

Retourne code de sortie non-nul si le projet ne respecte pas les conventions Forge.
Doit être lancé depuis la racine d'un projet Forge.

---

### `forge project:audit`

Rapport d'audit détaillé non destructif.

```bash
forge project:audit
```

Inspecte la structure complète du projet et produit un rapport humain lisible.
Doit être lancé depuis la racine d'un projet Forge.

---

### `forge routes:list`

Affiche toutes les routes déclarées dans `mvc/routes.py`.

```bash
forge routes:list
```

---

## Commandes d'entités

### `forge make:entity`

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

---

### `forge make:crud`

Génère un CRUD complet : liste, fiche, formulaires de création, modification et suppression.

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

---

### `forge make:relation`

Déclare une relation entre deux entités dans `mvc/entities/relations.json`.

```bash
forge make:relation
```

Mode interactif : pose les questions sur les deux entités et le type de relation.

---

### `forge sync:entity`

Régénère les fichiers modèles d'une entité depuis son JSON.

```bash
forge sync:entity <NomEntite>
```

---

### `forge sync:relations`

Régénère `mvc/entities/relations.sql` depuis `relations.json`.

```bash
forge sync:relations
```

---

### `forge build:model`

Régénère tous les modèles Python depuis leurs entités JSON.

```bash
forge build:model
forge build:model --dry-run
```

---

### `forge check:model`

Vérifie la cohérence des modèles : JSON valide, champs requis, types reconnus.

```bash
forge check:model
```

---

## Commandes de pages publiques

Ces commandes génèrent des pages accessibles sans authentification.

### `forge make:public-page`

Génère une page statique publique.

```bash
forge make:public-page <NomPage>
```

---

### `forge make:public-list`

Génère une liste publique paginée pour une entité.

```bash
forge make:public-list <NomEntite>
```

---

### `forge make:public-show`

Génère une fiche publique détaillée pour une entité.

```bash
forge make:public-show <NomEntite>
```

---

### `forge make:public-form`

Génère un formulaire public pour une entité.

```bash
forge make:public-form <NomEntite>
```

---

### `forge make:public-contact`

Génère une page de contact publique.

```bash
forge make:public-contact <NomPage>
```

**Voir aussi :** [Pages publiques](pages-publiques.md)

---

## Commandes de base de données

### `forge db:init`

Crée la base de données depuis les entités définies.

```bash
forge db:init
```

Requiert les variables `DB_ADMIN_*` dans `env/dev`.
Crée la base, les tables, et insère les données initiales si présentes.

---

### `forge db:apply`

Applique le schéma SQL courant.

```bash
forge db:apply
```

---

### `forge migration:status`

Affiche le statut des migrations : appliquées, en attente.

```bash
forge migration:status
```

---

### `forge migration:apply`

Applique les migrations SQL en attente dans `mvc/migrations/`.

```bash
forge migration:apply
```

---

### `forge migration:make`

Crée un nouveau fichier de migration SQL horodaté.

```bash
forge migration:make <nom>
```

Crée `mvc/migrations/<timestamp>_<nom>.sql`.

---

### `forge migration:diff`

Génère un diff SQL entre la définition d'une entité et la base de données actuelle.

```bash
forge migration:diff --entity <NomEntite>
```

---

## Commandes de starters et modules

### `forge starter:list`

Liste les starter apps disponibles avec leur statut et leur URL de documentation.

```bash
forge starter:list
```

---

### `forge starter:build`

Génère un starter app dans le projet courant.

```bash
forge starter:build <nom>
```

---

### `forge module:list`

Liste les modules Forge disponibles.

```bash
forge module:list
```

---

### `forge module:install`

Installe un module Forge dans le projet.

```bash
forge module:install <nom>
forge module:install <nom> --path <chemin>
forge module:install <nom> --dry-run
```

---

### `forge module:files`

Copie les fichiers d'un module dans le projet sans modifier les routes.

```bash
forge module:files <nom>
```

---

### `forge module:routes`

Injecte les routes d'un module dans `mvc/routes.py`.

```bash
forge module:routes <nom>
```

---

## Commandes d'authentification

### `forge auth:init`

Initialise les tables et fichiers d'authentification du projet.

```bash
forge auth:init
```

Crée les fichiers SQL (`users.sql`, `sessions.sql`, etc.), les contrôleurs
et les formulaires d'authentification.

**Voir aussi :** [Auth](../auth.md)

---

### `forge auth:doctor`

Diagnostic du système d'authentification.

```bash
forge auth:doctor
```

---

### `forge auth:status`

Affiche l'état des briques d'authentification installées (modules disponibles, contrats vérifiés).

```bash
forge auth:status
```

---

### `forge auth:list-sql`

Affiche les fichiers SQL optionnels du système d'authentification et leur statut (présent / absent).

```bash
forge auth:list-sql
```

---

### `forge auth:user:show`

Affiche les détails d'un compte utilisateur.

```bash
forge auth:user:show --id <id>
forge auth:user:show --email <email>
```

---

### `forge auth:user:create`

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

---

### `forge auth:user:list`

Liste les comptes utilisateurs.

```bash
forge auth:user:list
```

---

### `forge auth:user:disable`

Désactive un compte utilisateur.

```bash
forge auth:user:disable --email <email>
```

---

### `forge auth:user:enable`

Réactive un compte utilisateur désactivé.

```bash
forge auth:user:enable --email <email>
```

---

### `forge auth:user:password`

Modifie le mot de passe d'un compte.

```bash
forge auth:user:password --email <email> --password <mdp>
forge auth:user:password --email <email> --password-prompt
```

---

### `forge auth:user:role:add`

Assigne un rôle à un utilisateur.

```bash
forge auth:user:role:add --email <email> --role <role>
```

---

### `forge auth:user:role:remove`

Retire un rôle d'un utilisateur.

```bash
forge auth:user:role:remove --email <email> --role <role>
```

---

### `forge auth:user:roles`

Affiche les rôles d'un utilisateur.

```bash
forge auth:user:roles --email <email>
```

---

## Commandes mail

### `forge mail:init`

Initialise la configuration mail du projet.

```bash
forge mail:init
```

---

### `forge mail:test`

Envoie un mail de test pour vérifier la configuration.

```bash
forge mail:test
```

---

### `forge mail:render`

Rend un template de mail en HTML pour prévisualisation.

```bash
forge mail:render <template>
```

---

### `forge mail:doctor`

Diagnostic de la configuration mail.

```bash
forge mail:doctor
```

---

### `forge mail:logs`

Affiche les derniers logs d'envoi mail.

```bash
forge mail:logs
```

---

## Commandes médias et JavaScript

### `forge upload:init`

Configure le stockage des fichiers uploadés.

```bash
forge upload:init
```

Crée `storage/uploads/` et ses sous-dossiers (`images`, `documents`, `tmp`).

---

### `forge media:init`

Configure le stockage des médias avec génération de vignettes.

```bash
forge media:init
```

Crée `storage/uploads/` avec sous-dossiers `images/thumbnail` et `images/medium`.

---

### `forge js:init`

Installe une bibliothèque JavaScript dans le projet.

```bash
forge js:init htmx
forge js:init alpine
forge js:init htmx-alpine
```

---

## Commandes d'internationalisation

### `forge i18n:init`

Initialise la configuration i18n du projet.

```bash
forge i18n:init
```

Crée `translations/fr.json` si absent.

---

### `forge i18n:check`

Vérifie la cohérence des catalogues i18n.

```bash
forge i18n:check
```

---

## Commandes de déploiement

### `forge deploy:init`

Initialise les fichiers de configuration de déploiement.

```bash
forge deploy:init
```

Crée `deploy/nginx/forge-app.conf`, `deploy/systemd/forge-app.service` et
`deploy/README_DEPLOY.md`.

---

### `forge deploy:check`

Vérifie la configuration de déploiement et l'environnement cible.

```bash
forge deploy:check
```

---

## Commandes de synchronisation

### `forge sync:landing`

Synchronise la landing page source vers `docs/index.html`.

```bash
forge sync:landing
```

Copie `mvc/views/landing/index.html` → `docs/index.html` et `static/` → `docs/static/`.
À utiliser après toute modification de la landing page source.

---

## Commandes de documentation

### `forge docs:pdf`

Génère un PDF depuis la documentation du projet.

```bash
forge docs:pdf
```

---

## Utilitaires

### `forge --version`

Affiche la version courante de Forge.

```bash
$ forge --version
Forge {{forge_version}}
```

### `forge --help`

Affiche l'aide générale avec toutes les commandes disponibles.

```bash
forge --help
forge help
forge -h
```
