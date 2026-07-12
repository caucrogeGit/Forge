# Anatomie d'une app Forge

Une application Forge ne se résume pas à son dossier `mvc/`.
`mvc/` porte le gros du travail (contrôleurs, modèles, formulaires, vues, routes, entités), mais l'application dépend de plusieurs points d'intégration qui vivent **hors** de `mvc/`, et qui sont à vous.

Ce document décrit cette surface d'intégration, et pourquoi on **monte un projet en place** plutôt que de copier `mvc/` d'un projet à l'autre.

## Ce que porte `mvc/`

`mvc/` contient le code que vous écrivez pour chaque fonctionnalité :

- `mvc/controllers/`, `mvc/models/`, `mvc/forms/`, `mvc/views/`, `mvc/routes/` : la couche MVC ;
- `mvc/entities/` : les contrats d'entités (opt-in `forge-mvc-entities`) ;
- `mvc/migrations/` : les migrations de schéma (les fichiers, pas les données) ;
- `mvc/helpers/`, `mvc/services/` : vos utilitaires et services applicatifs.

## Ce qui vit hors `mvc/` (la surface d'intégration)

Ces fichiers ne sont pas dans `mvc/`, mais sans eux l'application ne fonctionne pas, ou pas comme prévu.

| Élément | Rôle | Pourquoi c'est critique |
|---|---|---|
| `app.py` | Point d'entrée : c'est **ici** que se câblent les middlewares (auth, RBAC, CSRF). | Un projet nu a `Application(router)` sans middleware. Perdre ce câblage retire vos protections : les routes protégées deviennent accessibles. |
| `config.py` + `env/` | Configuration et **secrets** (identifiants BDD, clés). `env/dev`/`env/prod` sont ignorés par git. | Sans `env/<APP_ENV>`, pas de connexion BDD ni de clés (MFA, etc.). À recréer sur chaque déploiement. |
| `optins/registry.py` | Les opt-ins **activés** dans le projet et le backend BDD choisi (ADR-061). | C'est ce que reconstruit `forge opt-in:enable <nom> --apply`. |
| `requirements.txt` / `requirements-dev.txt` | Épinglage de `forge-mvc` et des opt-ins (source et version). | Détermine la version exacte de Forge utilisée. |
| La base de données | `mvc/migrations/` porte le schéma, pas les **données**. | Il faut provisionner (`forge db:init`) puis `forge migration:apply`, et charger vos données (fixtures, seed). |
| `static/`, `storage/` | Assets front et stockage (uploads, logs). | Les fichiers déposés vivent là, hors git. |

À cela s'ajoutent d'éventuels **chemins lus au runtime par votre code applicatif** (un schéma JSON, un référentiel) : ils vivent où votre code les cherche, souvent hors `mvc/`.

## Porter ou reconstruire : montez en place, ne copiez pas

La tentation est de copier `mvc/` dans un squelette neuf et de réinstaller les opt-ins.
Ça marche presque, mais c'est **fragile** : on oublie vite `app.py` (donc les protections RBAC), un chemin de schéma lu au runtime, ou une clé d'`env/`.

La voie recommandée est la **montée en place** :

```bash
forge skeleton:upgrade
```

`skeleton:upgrade` ajoute au projet les fichiers du squelette **manquants** en mode write-if-new : il ne touche ni votre `app.py`, ni votre `env/`, ni votre base, ni votre `optins/registry.py`.
Vous récupérez les nouveautés du squelette sans perdre vos points d'intégration, et sans le risque de la copie.

!!! warning "Le câblage des middlewares est dans app.py"
    Auth et RBAC (par exemple `AuthMiddleware` et `PrefixPermissionMiddleware`) se branchent dans `app.py`, pas dans `mvc/`.
    Copier seulement `mvc/` les perdrait, et retirerait silencieusement vos protections.
    C'est le premier point à vérifier après toute reconstruction.

## Checklist de reconstruction

Si vous reconstruisez malgré tout un projet à partir de `mvc/`, vérifiez :

1. `app.py` : les middlewares (auth, RBAC) sont bien câblés ;
2. `env/<APP_ENV>` : recréé, avec les secrets (BDD, clés) ;
3. `optins/registry.py` : les opt-ins activés et le backend (`forge opt-in:enable`) ;
4. `requirements*.txt` : `forge-mvc` et les opt-ins épinglés à la bonne version ;
5. la base : `forge db:init` puis `forge migration:apply`, et vos données ;
6. les chemins lus au runtime par votre code (schémas, référentiels).

## Voir aussi

- [Démarrer avec Forge](getting-started.md) : créer un projet.
- [Vue d'ensemble des concepts](concepts.md) : l'architecture MVC de Forge.
