# Starters Forge

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Forge · Parcours applicatifs</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:2rem;line-height:1.15;color:#0F172A;">Vue d'ensemble des starters</h2>
  <p style="margin:0;color:#334155;font-size:1.05rem;max-width:880px;">Des parcours progressifs pour apprendre Forge, reconstruire vite et adapter à un vrai projet.</p>
</div>

## Principe

Un **starter** Forge est un parcours d'apprentissage que l'on réalise à la main en suivant la documentation.
Chaque palier montre le contrôleur, la vue et la route à créer pour comprendre une mécanique du framework.
Un starter n'est pas un profil, voir
[Différence entre profil et starter](#difference-entre-profil-et-starter).

Profils recommandés selon le starter : `minimal` ou `standard` pour les paliers
avec base de données, aucun profil pour les paliers sans base.

## Catalogue

La progression cœur `welcome-forge` enseigne les fondamentaux du framework,
du niveau débutant au niveau avancé.

### Bonjour Forge : progression cœur (`welcome-forge`)

*Débutant, 11 paliers (tutoriel continu)* : [Bonjour Forge](welcome-forge/debutant/welcome.md) · [Paramètres d'URL](welcome-forge/debutant/query-params.md) · [Première vue HTML](welcome-forge/debutant/first-html-view.md) · [Route dynamique](welcome-forge/debutant/dynamic-route.md) · [Inspecter une requête](welcome-forge/debutant/request-debug.md) · [Réponse JSON](welcome-forge/debutant/json-response.md) · [Le jeton CSRF](welcome-forge/debutant/csrf.md) · [Premier formulaire POST](welcome-forge/debutant/form-post.md) · [Validation serveur](welcome-forge/debutant/server-validation.md) · [Première base SQL](welcome-forge/debutant/first-sql.md) · [Écrire en base](welcome-forge/debutant/first-sql-write.md)

*Intermédiaire, 8 paliers (tutoriel continu)* : [Lister des enregistrements](welcome-forge/intermediaire/list-records.md) · [Héritage de gabarit](welcome-forge/intermediaire/layout-template.md) · [Rechercher / filtrer](welcome-forge/intermediaire/filter-list.md) · [Paginer une liste](welcome-forge/intermediaire/pagination.md) · [Modifier un enregistrement](welcome-forge/intermediaire/update-record.md) · [Supprimer un enregistrement](welcome-forge/intermediaire/delete-record.md) · [Messages flash](welcome-forge/intermediaire/flash-messages.md) · [Mémoriser un état en session](welcome-forge/intermediaire/session-state.md)

*Avancé, 3 paliers (tutoriel continu)* : [Relations entre tables](welcome-forge/avance/relations.md) · [Écritures transactionnelles](welcome-forge/avance/db-transaction.md) · [API JSON protégée](welcome-forge/avance/json-api.md)

## Progression recommandée

Le niveau débutant `Bonjour Forge` est un **tutoriel continu** : vous
construisez à la main un seul projet qui grandit palier après palier (un
contrôleur qui s'enrichit, un `mvc/routes.py` qui s'accumule). **Ne sautez pas
directement aux notions SQL** : les paliers HTTP préparent l'accès base
sereinement. Les 11 paliers du niveau débutant :

1. **Bonjour Forge** : afficher une réponse texte avec `Response.text(...)`.
2. **Paramètres d'URL** : lire une valeur simple avec `request.query(...)`.
3. **Première vue HTML** : rendre une page avec `BaseController.render(...)`.
4. **Route dynamique** : lire un paramètre de route comme `/articles/{id}`.
5. **Inspecter une requête** : explorer `request.data` avec `Response.debug(...)` en développement.
6. **Réponse JSON** : retourner des données structurées avec `Response.json(...)`.
7. **Le jeton CSRF** : comprendre la protection CSRF des formulaires.
8. **Premier formulaire POST** : envoyer des données depuis un formulaire HTML.
9. **Validation serveur** : refuser ou accepter les données reçues.
10. **Première base SQL** : lire une donnée : MariaDB, migrations et SQL visible.
11. **Écrire en base** : insérer une ligne depuis un formulaire avec `db.insert(...)`.

Après le préambule d'installation, suivez les paliers dans l'ordre depuis
[Bonjour Forge](welcome-forge/debutant/welcome.md).

Une fois ces **11 paliers** acquis, vous avez terminé le niveau débutant de
découverte *Bonjour Forge*. Vous pouvez ensuite enchaîner les niveaux
intermédiaire et avancé de la progression cœur.

L'ordre d'apprentissage recommandé est celui des 11 paliers ci-dessus, puis
les niveaux intermédiaire et avancé.

## Différence entre profil et starter

Un **profil** définit la base technique d'un projet créé avec `forge new`
(`forge new MonProjet --profile standard`). Un **starter** fournit un exemple
applicatif générable *après* la création du projet. Ils sont indépendants : un
profil ne remplace pas un starter, un starter ne modifie pas le profil, et un
starter peut illustrer un ou plusieurs profils.

Pour choisir un profil : [Profils de projet](../features/profiles.md).

## Utiliser un starter

Un starter se suit **à la main**, palier par palier.
Chaque palier indique le contrôleur, la vue et la route à créer dans le projet.

!!! note "Les starters ne se génèrent pas"
    Forge ne génère pas les starters et n'écrit jamais dans votre `mvc/routes.py`.
    Vous créez vous-même chaque fichier et ajoutez chaque route, en suivant la documentation du palier (voir [ADR-035](../adr/035-starters-manual-not-generated.md)).
