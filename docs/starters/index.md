# Starters Forge

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Forge · Parcours applicatifs</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:2rem;line-height:1.15;color:#0F172A;">Apprendre Forge, palier par palier</h2>
  <p style="margin:0;color:#334155;font-size:1.05rem;max-width:880px;">Un parcours progressif que vous construisez à la main : du premier affichage texte jusqu'à une API JSON protégée.</p>
</div>

## Qu'est-ce qu'un starter ?

Un **starter** est un parcours d'apprentissage que l'on réalise **à la main** en suivant la documentation.
Chaque palier montre le contrôleur, la vue et la route à créer pour comprendre une mécanique du framework.
Un starter n'est pas un profil : voir [Profil ou starter ?](#difference-entre-profil-et-starter).

!!! tip "Par où commencer"
    Suivez les paliers **dans l'ordre**, en commençant par [Bonjour Forge](welcome-forge/debutant/welcome.md).
    Ne sautez pas directement aux notions SQL : les paliers HTTP préparent l'accès à la base sereinement.

## Progression recommandée

Le niveau débutant est un **tutoriel continu** : vous construisez un seul projet qui grandit palier après palier (un contrôleur qui s'enrichit, un `mvc/routes.py` qui s'accumule).
Les **11 paliers**, dans l'ordre :

1. **Bonjour Forge** : afficher une réponse texte avec `Response.text(...)`. [Suivre](welcome-forge/debutant/welcome.md)
2. **Paramètres d'URL** : lire une valeur avec `request.query(...)`. [Suivre](welcome-forge/debutant/query-params.md)
3. **Première vue HTML** : rendre une page avec `BaseController.render(...)`. [Suivre](welcome-forge/debutant/first-html-view.md)
4. **Route dynamique** : lire un paramètre de route comme `/articles/{id}`. [Suivre](welcome-forge/debutant/dynamic-route.md)
5. **Inspecter une requête** : explorer `request.data` avec `Response.debug(...)`. [Suivre](welcome-forge/debutant/request-debug.md)
6. **Réponse JSON** : retourner des données avec `Response.json(...)`. [Suivre](welcome-forge/debutant/json-response.md)
7. **Le jeton CSRF** : comprendre la protection CSRF des formulaires. [Suivre](welcome-forge/debutant/csrf.md)
8. **Premier formulaire POST** : envoyer des données depuis un formulaire HTML. [Suivre](welcome-forge/debutant/form-post.md)
9. **Validation serveur** : refuser ou accepter les données reçues. [Suivre](welcome-forge/debutant/server-validation.md)
10. **Première base SQL** : lire une donnée (MariaDB, migrations, SQL visible). [Suivre](welcome-forge/debutant/first-sql.md)
11. **Écrire en base** : insérer une ligne depuis un formulaire avec `db.insert(...)`. [Suivre](welcome-forge/debutant/first-sql-write.md)

Une fois ces 11 paliers acquis, le niveau débutant est terminé : enchaînez sur les niveaux suivants.

## Niveaux suivants

### Intermédiaire (8 paliers)

Listes, gabarits, filtres, pagination, modification, suppression, flash et session.

- [Lister des enregistrements](welcome-forge/intermediaire/list-records.md)
- [Héritage de gabarit](welcome-forge/intermediaire/layout-template.md)
- [Rechercher / filtrer](welcome-forge/intermediaire/filter-list.md)
- [Paginer une liste](welcome-forge/intermediaire/pagination.md)
- [Modifier un enregistrement](welcome-forge/intermediaire/update-record.md)
- [Supprimer un enregistrement](welcome-forge/intermediaire/delete-record.md)
- [Messages flash](welcome-forge/intermediaire/flash-messages.md)
- [Mémoriser un état en session](welcome-forge/intermediaire/session-state.md)

### Avancé (3 paliers)

Relations, transactions et API JSON protégée.

- [Relations entre tables](welcome-forge/avance/relations.md)
- [Écritures transactionnelles](welcome-forge/avance/db-transaction.md)
- [API JSON protégée](welcome-forge/avance/json-api.md)

## Profil ou starter ? { #difference-entre-profil-et-starter }

Un **profil** définit la base technique d'un projet créé avec `forge new` (`forge new MonProjet --profile standard`).
Un **starter** fournit un exemple applicatif que l'on construit *après* la création du projet.

Ils sont indépendants : un profil ne remplace pas un starter, un starter ne modifie pas le profil, et un starter peut illustrer un ou plusieurs profils.
Pour choisir un profil : [Profils de projet](../features/profiles.md).

## Comment suivre un starter

Un starter se suit **à la main**, palier par palier : chaque palier indique le contrôleur, la vue et la route à créer dans le projet.

!!! note "Les starters ne se génèrent pas"
    Forge ne génère pas les starters et n'écrit jamais dans votre `mvc/routes.py`.
    Vous créez vous-même chaque fichier et ajoutez chaque route, en suivant la documentation du palier (voir [ADR-035](../adr/035-starters-manual-not-generated.md)).
