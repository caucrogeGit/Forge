# Contrat de stabilité Forge 1.x

> **Note** : Ce document est aligné sur la trajectoire publique `1.x` (`1.0.0-beta` → `rc` → `1.0.0`).

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Ce document définit ce que Forge considère comme stable, interne, expérimental ou garanti pour les projets construits sur Forge 1.x.

Il ne décrit pas de nouvelles fonctionnalités. Il explicite les promesses implicites présentes dans le code, les générateurs et la documentation pour la série 1.x. Pour les changements entre versions majeures, voir le guide de migration.

---

## Objectif du contrat

Forge 1.x garantit la stabilité de son interface publique : commandes CLI documentées, structure projet générée, conventions `mvc/`, fichiers d'entités JSON, helpers publics et clés de configuration documentées.

Le contrat couvre également :

- Les douze modules opt-in officiels selon leur niveau de maturité (Stable / Bêta / Alpha). La grille de maturité à jour fait foi dans [release-policy.md](release-policy.md) (source unique) ; ce contrat ne la duplique pas pour éviter toute dérive.
- Le mécanisme de plugins pour étendre le contexte Jinja (`core.mvc.controller.register_jinja_context_provider`).
- L'absence de dépendance nominale du core sur les modules opt-in.

Ce qui n'est pas listé ici comme stable peut changer entre versions mineures sans notice préalable.

---

## Ce que Forge considère comme stable

Les éléments suivants sont garantis pour toute la série 1.x :

- Les commandes CLI listées dans la section [Commandes CLI stables](#commandes-cli-stables).
- La structure de projet générée par `forge new` (dossiers `mvc/`, `env/`, `static/`, `app.py`, `forge_profile.txt`).
- Le format JSON canonique des entités (`mvc/entities/<entite>/<entite>.json`, v1).
- Les clés de configuration `.env` documentées dans `docs/reference.md`.
- Le comportement des fichiers générés et préservés décrit plus bas.
- Les imports publics documentés de `core.http`, `core.auth`, `core.security` (session, CSRF, décorateurs RBAC).
- L'endpoint `GET /health` → `200 {"status": "ok"}`.
- Les noms de routes applicatives écrits dans `mvc/routes.py` par le développeur.
- Le mécanisme de plugins `core.mvc.controller.register_jinja_context_provider` pour les modules opt-in.
- L'API des modules opt-in stables (`forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`).
- La compatibilité ascendante des migrations SQL générées.

---

## Ce qui est public

| Domaine | Éléments publics garantis |
|---|---|
| CLI | Commandes et options listées dans `docs/reference.md` |
| Structure projet | `mvc/`, `env/`, `static/`, `app.py`, `forge_profile.txt` |
| Entités | Format JSON v1 (`entity`, `table`, `primary_key`, `fields`, `constraints`) |
| Modèles | `*_base.py` (interface), `*.py` manuel (classe métier) |
| Routes | `mvc/routes.py`, conventions déclaratives |
| Helpers | `core.http.helpers.html()`, `core.http.response.Response`, `core.http.request.Request` |
| Auth | `core.auth.login`, `core.auth.logout`, `core.auth.current_user`, `core.auth.is_authenticated`, `@login_required` |
| RBAC | `@require_role`, `@require_auth`, `@require_csrf` |
| Session | `core.security.session` (API documentée) |
| Config | Clés `APP_*`, `DB_*`, `MAIL_*` documentées dans `docs/reference.md` |
| Santé | `GET /health` → `200 {"status": "ok"}` |

---

## Ce qui est interne

Les éléments suivants peuvent changer sans notice entre versions mineures de Forge 1.x :

- Fonctions et modules internes de `cli/` (générateurs, parseurs, builders).
- Fonctions préfixées `_` dans tout le code source Forge.
- Structure interne des générateurs (`cli/entities/crud/`, `cli/entities/model/`, etc.).
- Helpers non référencés dans `docs/reference.md`.
- Contenu interne des tests Forge (fichiers `tests/`).
- Modules internes non exposés dans la documentation (`core/templating/` internals, `core/forge.py` registry).
- Format interne des fichiers de session stockés côté serveur.
- Structure interne de `forge_modules.json`.

---

## Ce qui est expérimental

Les éléments suivants sont disponibles mais peuvent évoluer dans leur interface ou leur comportement :

| Domaine | Statut |
|---|---|
| `forge module:*` (list, install, files, routes) | Expérimental, interface susceptible d'évoluer |
| `forge check:model` | Expérimental |
| `forge deploy:init`, `forge deploy:check` | Expérimental |
| Pages publiques (`make:public-*`) | Disponible, interface stable, comportement peut s'affiner |
| Backends de session FileStore / MariaDbStore | Disponible, API stable, options de configuration susceptibles d'évoluer |
| `forge-mvc-mfa` (Alpha) | Secret TOTP chiffré au repos via Fernet (`FORGE_MFA_SECRET_KEY`). Publié sur PyPI depuis `1.0.0-beta.9`. Passage Alpha → Beta à venir. |
| `forge-mvc-iot` (Alpha) | Subscriber MQTT, stockage `iot_events`, API HTTP en lecture seule. Publié sur PyPI depuis `1.0.0-beta.12`. API en stabilisation. |
| `forge-mvc-video` (Beta) | Chaîne complète `video:upload` → `video:process` → lecture HTTP Range, + `video:cleanup`. Transcodage MP4 (H.264/AAC). Publié sur PyPI depuis `1.0.0-beta.13`. |
| OIDC | Retiré du core (ADR-004). Si réintroduit via `forge-mvc-oidc`, sera expérimental jusqu'à Beta confirmée. |

---

## Fichiers générés

### Régénérables : Forge peut les écraser

Ces fichiers sont entièrement pilotés par le JSON canonique. Toute modification manuelle sera perdue à la prochaine régénération.

| Fichier | Commande source |
|---|---|
| `mvc/entities/<e>/<e>_base.py` | `forge build:model`, `forge sync:entity` |
| `mvc/entities/<e>/<e>.sql` | `forge build:model`, `forge sync:entity` |
| `mvc/entities/relations.sql` | `forge sync:relations` |

### Sources canoniques : à éditer, jamais régénérées

| Fichier | Règle |
|---|---|
| `mvc/entities/<e>/<e>.json` | Source unique de vérité pour l'entité |
| `mvc/entities/relations.json` | Source unique de vérité pour les relations |

### Générés une fois : Forge ne réécrit pas si le fichier existe

Ces fichiers sont créés par un générateur lors de la première exécution. Forge vérifie leur existence avant d'écrire et ne les écrase jamais sans action explicite (`--force` si disponible).

| Fichier | Commande créatrice |
|---|---|
| `mvc/controllers/<e>_controller.py` | `forge make:crud` |
| `mvc/models/<e>_model.py` | `forge make:crud` |
| `mvc/forms/<e>_form.py` | `forge make:crud` |
| `mvc/views/<e>/list.html`, `show.html`, etc. | `forge make:crud` |
| `mvc/views/public/<nom>*.html` | `forge make:public-*` |
| `mvc/controllers/public/<nom>_controller.py` | `forge make:public-*` |
| `mvc/entities/<e>/<e>.py` | `forge make:entity` |
| `mvc/entities/<e>/__init__.py` | `forge make:entity` |

---

## Fichiers utilisateur préservés

Forge ne modifie jamais ces fichiers sans action explicite du développeur :

- `mvc/routes.py`
- `mvc/controllers/*.py` (après génération initiale)
- `mvc/models/*.py` (hors `*_base.py`)
- `mvc/views/**/*.html` (après génération initiale)
- `mvc/forms/*.py`
- `mvc/validators/*.py`
- `mvc/entities/<e>/<e>.py` (modèle manuel)
- `mvc/entities/<e>/__init__.py`
- `static/` (tout le contenu)
- `env/dev`, `env/prod`, `env/example`
- `mvc/migrations/` (SQL applicatifs)
- `app.py` (après génération initiale)

---

## Commandes CLI stables

Ces commandes et leurs options documentées sont garanties pour Forge 1.x.

### Projet

| Commande | Rôle |
|---|---|
| `forge new NomProjet [--profile PROFIL]` | Crée un projet |
| `forge doctor` | Diagnostique l'environnement (tolérant, lecture seule) |
| `forge project:check` | Contrôle strict des conventions (CI-ready) |
| `forge project:audit` | Rapport d'audit détaillé non destructif |
| `forge --version` | Affiche la version |
| `forge help` | Affiche l'aide |

### Entités et modèles

| Commande | Rôle |
|---|---|
| `forge make:entity NomEntite` | Crée le JSON canonique |
| `forge build:model [--dry-run]` | Génère `*_base.py` et SQL |
| `forge sync:entity NomEntite` | Régénère depuis le JSON |
| `forge sync:relations` | Régénère `relations.sql` |
| `forge make:relation` | Assistant de relation |

### CRUD et pages

| Commande | Rôle |
|---|---|
| `forge make:crud NomEntite [--dry-run]` | Génère le CRUD complet |
| `forge make:public-page <nom>` | Page publique simple |
| `forge make:public-list <Entite>` | Liste publique |
| `forge make:public-show <Entite>` | Fiche publique |
| `forge make:public-form <Entite>` | Formulaire public |
| `forge make:public-contact` | Page contact |

### Base de données

| Commande | Rôle |
|---|---|
| `forge db:init` | Prépare MariaDB |
| `forge db:apply` | Applique le SQL généré |
| `forge migration:status` | État des migrations |
| `forge migration:make [nom]` | Crée une migration vide |
| `forge migration:apply` | Applique les migrations en attente |

### Auth

| Commande | Rôle |
|---|---|
| `forge auth:init` | Prépare les SQL Auth/User |
| `forge auth:doctor` | Vérifie les briques Auth |
| `forge auth:status` | État des briques Auth |
| `forge auth:user:create` | Crée un utilisateur |
| `forge auth:user:list` | Liste les utilisateurs |
| `forge auth:user:disable` / `enable` | Active / désactive un compte |
| `forge auth:user:password` | Change le mot de passe |
| `forge auth:user:role:add` / `remove` / `roles` | Gestion des rôles RBAC |

### Mail et médias

| Commande | Rôle |
|---|---|
| `forge mail:init` | Prépare le système mail |
| `forge mail:doctor` | Vérifie la config mail |
| `forge mail:test --to <email>` | Envoie un mail de test |
| `forge upload:init` | Prépare les uploads |
| `forge media:init` | Prépare les médias |
| `forge js:init htmx` / `alpine` | Installe HTMX ou Alpine |

### Routes

| Commande | Rôle |
|---|---|
| `forge routes:list` | Liste les routes |

---

## Format de l'aide CLI

`forge help`, `forge --help`, `forge -h` et `forge` (sans argument) affichent une aide groupée par famille de commandes. Ce comportement est stable sur Forge 1.x.

| Élément | Comportement |
|---|---|
| `forge help` / `--help` / `-h` | Affiche l'aide groupée sur stdout, code 0. |
| `forge` (sans argument) | Identique à `forge help`. |
| Module source de l'aide | `cli/_support/help.py`, `build_help(version: str)` |

La distinction entre `forge doctor` (tolérant) et `forge project:check` (strict) est documentée dans l'aide générale.

---

## Format des messages d'erreur CLI et conseils de récupération

Les erreurs de dispatch CLI (commande inconnue, argument manquant, hors-projet) suivent la convention :

```
Erreur : <message>
Conseil : <suggestion>   # optionnel
```

- Sortie sur **stderr**, code de sortie **1**.
- Ce format est stable sur Forge 1.x.
- Les tags `[ERREUR]` dans les sorties de génération d'artefacts sont distincts et non concernés.

Les conseils (`Conseil :`) indiquent une action simple à essayer. Ils n'appliquent jamais de correction automatique. Les détails des rapports `forge doctor` et `forge project:check` suivent le même principe : ils ajoutent une piste d'action à la fin du message de diagnostic.

---

## Commandes CLI expérimentales

Ces commandes sont disponibles mais leur interface peut évoluer :

| Commande | Note |
|---|---|
| `forge module:list` / `install` / `files` / `routes` | Système de modules, jeune |
| `forge check:model` | Vérification cohérence modèles |
| `forge deploy:init` / `check` | Déploiement |
| `forge migration:diff` | Comparaison entité / MariaDB |

---

## Compatibilité attendue sur Forge 1.x

Pour tout projet généré avec Forge 1.x :

- La structure `mvc/` générée reste compatible entre versions 1.x.
- Les options CLI documentées restent compatibles.
- Le format JSON d'entité v1 reste lisible et générateur.
- Les imports publics documentés de `core.*` restent stables.
- Les clés `.env` documentées restent valides.
- Les fichiers `*_base.py` existants restent compatibles (la régénération est optionnelle).
- L'upgrade entre versions mineures de la série `1.0.x` ne requiert aucune modification du code applicatif pour les API stables.
- L'upgrade `1.x → 2.0` peut introduire des ruptures documentées dans un guide de migration dédié.

Les imports internes de `cli.*` ne sont pas garantis entre versions mineures.

---

## Politiques désormais documentées

Les garanties suivantes, autrefois en attente, sont désormais livrées :

- [Politique de dépréciation](deprecation-policy.md) ;
- [Politique de versionnement sémantique](release-policy.md) ;
- [Matrice de compatibilité Python / MariaDB / Node](compatibility.md) ;
- [Guide de migration entre versions majeures](../features/migration-guide.md) ;
- [Politique LTS](lts-policy.md).

## Ce que ce contrat ne garantit pas encore

Les points suivants seront traités dans des tickets dédiés :

- Promesse sur l'API JSON future (`API-JSON-001` et suivants).
- Garantie sur les modules internes non documentés.
- Garantie sur les starters (code généré, non versionnés dans les projets utilisateur).
- Garantie sur les backends de session expérimentaux (FileStore, MariaDbStore).
- La rétrocompatibilité du module `forge-mvc-mfa` tant qu'il reste Alpha, les API peuvent évoluer avant Beta.
- Les API privées préfixées par `_` peuvent changer entre versions mineures sans notice.

---

## Règles pratiques pour les futurs tickets

Ce contrat doit servir de référence dans les tickets suivants :

- **DX** (`DX-DOCTOR-001`, etc.) : `forge doctor` doit vérifier uniquement les éléments listés comme stables ou contractuels.
- **E2E** (`E2E-CLI-001`, `E2E-NON-OVERWRITE-001`, etc.) : les tests couvrent les commandes stables, les fichiers préservés et les fichiers régénérables.
- **Sécurité** (`SECURITY-AUDIT-001`, etc.) : distinguer bug, limite connue et comportement non garanti selon ce document.
- **Release policy** (`RELEASE-POLICY-001`, etc.) : s'appuyer sur ce contrat pour définir ce qui constitue un breaking change.
- **API JSON** : toute API ajoutée doit être classée stable ou expérimentale dès son introduction.

Un breaking change est toute modification d'un élément listé comme stable dans ce document.
