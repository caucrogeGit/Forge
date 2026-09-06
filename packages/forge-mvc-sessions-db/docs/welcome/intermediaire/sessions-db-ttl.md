# Intermédiaire 3 : Une durée par nature de session

Objectif : qu'un panier anonyme et une session administrateur n'expirent pas au même rythme.

## Une seule durée ne convient pas

Une session authentifiée doit expirer vite : c'est elle qui donne accès.
Un panier anonyme, lui, gagne à durer, sinon le visiteur perd son contenu en allant chercher sa carte bancaire.

Une durée unique oblige à choisir le pire des deux.

| Nature | Défaut | Ce qu'elle porte |
|---|---|---|
| `anonymous` | 2 heures | un visiteur non connecté, un panier, un jeton CSRF |
| `authenticated` | 1 heure | une session ouverte par une connexion |
| `remembered` | 30 jours | un « se souvenir de moi » explicite |

```bash
SESSION_TTL_ANONYMOUS=7200
SESSION_TTL_AUTHENTICATED=3600
SESSION_TTL_REMEMBERED=2592000
```

```python
from forge_mvc_sessions_db import KIND_AUTHENTICATED, ttl_for

duree = ttl_for(KIND_AUTHENTICATED)
```

!!! info "La durée courte est celle de la session authentifiée"
    C'est l'inverse de l'intuition, et c'est délibéré : la session qui donne des droits est celle qui doit se refermer vite.

    Une session anonyme volée ne donne accès à rien.

!!! danger "Une nature inconnue est refusée, jamais devinée"
    `ttl_for("admin")` lève plutôt que de retomber sur une valeur par défaut.

    Retomber en silence donnerait à une session la durée d'une autre, et personne ne s'en apercevrait avant de chercher pourquoi des comptes restent ouverts la nuit.

!!! warning "L'authentification change la nature, donc la durée"
    Une session anonyme qui devient authentifiée reprend la durée de sa nouvelle nature.

    Sans cela, une session connectée garderait les deux heures de l'anonyme, et la durée courte ne servirait à rien.

## À retenir

- Trois natures, trois durées, réglables par l'environnement.
- La session authentifiée est la plus courte, parce qu'elle est la plus sensible.
- Une nature inconnue lève au lieu de deviner.

## Étape suivante

[Suivant : nettoyer les sessions expirées](sessions-db-cleanup.md)
