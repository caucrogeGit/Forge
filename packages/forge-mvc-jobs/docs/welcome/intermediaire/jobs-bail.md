# Intermédiaire 4 : Le bail, le battement et la reprise

Objectif : qu'une tâche perdue en vol reparte, sans jamais partir deux fois.

## Le problème d'une tâche prise et jamais rendue

Un worker prend une tâche, la marque `running`, et le serveur redémarre.
La tâche reste `running` pour toujours : aucun worker ne la reprend, et personne ne le voit.

Forge donne donc un **bail** : un jeton de prise, et une durée au delà de laquelle la prise est réputée perdue.

```bash
forge jobs:status
forge jobs:reclaim
```

| Élément | Rôle |
|---|---|
| `claim_token` | identifie **cette** prise, pas la tâche |
| bail (900 s par défaut) | au delà, la prise est considérée perdue |
| `jobs:reclaim` | remet en `pending` les tâches dont le bail a expiré |

## Le battement, pour les tâches longues

Une tâche qui dure plus que le bail serait reprise alors qu'elle travaille encore, et s'exécuterait deux fois.

```python
from forge_mvc_jobs import heartbeat

def transcoder(payload, claim_token):
    for morceau in morceaux:
        traiter(morceau)
        heartbeat(claim_token)
```

Chaque battement repousse l'échéance du bail.

!!! danger "Sans battement, une tâche longue s'exécute deux fois"
    Au delà du bail, `jobs:reclaim` la rend disponible, et un second worker la prend pendant que le premier travaille encore.

    C'est le cas le plus coûteux : deux transcodages, deux courriels, deux prélèvements.

!!! warning "`heartbeat` rend un booléen, et il faut le lire"
    Faux signifie que le bail est déjà perdu : quelqu'un d'autre a peut-être repris la tâche.

    Continuer alors, c'est travailler pour rien, ou pire, écrire par-dessus.

!!! info "Planifiez la reprise, ne la lancez pas à la main"
    `jobs:reclaim` se met en minuterie, toutes les cinq minutes.

    Le guide de déploiement en donne la paire `.service` et `.timer` ; sans elle, une tâche perdue le reste.

## Voir l'état de la file

```bash
forge jobs:status
```

Il donne le compte par statut et par file : `pending`, `running`, `done`, `failed`.
Un `running` qui ne bouge pas est le signe d'un bail perdu, donc d'une reprise à planifier.

## À retenir

- Le bail borne une prise ; passé ce délai, la tâche est reprise.
- Une tâche longue doit battre, et lire ce que le battement répond.
- La reprise est une minuterie, pas un geste manuel.

## Étape suivante

[Bilan du niveau intermédiaire](bilan.md)
