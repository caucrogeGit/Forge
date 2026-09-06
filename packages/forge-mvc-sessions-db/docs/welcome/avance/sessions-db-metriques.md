# Avancé 3 : Compter les sessions

Objectif : savoir combien de personnes sont connectées, et si la purge suit.

## Deux nombres qui ne disent pas la même chose

```python
from forge_mvc_sessions_db import active_sessions, session_metrics

combien = active_sessions()
mesures = session_metrics()
```

| Ce que porte `SessionMetrics` | Ce que cela dit |
|---|---|
| `active` | des personnes sont là, maintenant |
| `expired` | ce que `forge sessions:gc` n'a pas encore balayé |
| `by_kind` | ce qui distingue une session authentifiée d'un panier anonyme |

`active_sessions()` rend le premier nombre seul, pour une sonde qui n'a besoin que de lui.

!!! warning "Une part d'expirées qui grossit annonce une purge à l'arrêt"
    Les lignes expirées ne gênent personne tant qu'elles sont rares.

    Passé la moitié de la table, chaque lecture les traverse quand même : la table grossit, les requêtes ralentissent, et rien d'autre ne le montre. Le panneau du back-office signale ce seuil.

!!! danger "Ne publiez pas ces nombres sans protection"
    Le nombre de connectés d'un site est une information commerciale, et sa variation en dit long sur une organisation.

    Une route de métrique se protège comme un écran d'administration.

!!! info "Aucun identifiant n'est exposé"
    Ces fonctions comptent, elles n'énumèrent pas.

    Un identifiant de session **est** le moyen de se faire passer pour son titulaire : un compteur n'a aucune raison d'en montrer un.

## Le voir sans écrire de code

Le back-office de `forge-mvc-admin` porte un panneau `/admin/_sessions` qui rend ces mêmes nombres.

## À retenir

- `active_sessions()` pour une sonde, `session_metrics()` pour un tableau.
- Une part d'expirées élevée est le signe d'une purge qui ne tourne plus.
- Ces fonctions comptent et n'exposent aucun identifiant.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
