# Intermédiaire 3 : Priorité et idempotence

Objectif : qu'un courriel de réinitialisation ne dorme pas derrière mille vignettes.

## Deux options à l'enfilage

```python
from forge_mvc_jobs import enqueue

enqueue("mail.envoyer", {"a": "eleve@exemple.fr"},
        priority=10,
        idempotency_key=f"reset:{utilisateur.id}")
```

| Option | Ce qu'elle change |
|---|---|
| `priority` | les tâches de priorité haute sortent en premier, à égalité c'est l'ordre d'arrivée |
| `idempotency_key` | une clé déjà en file n'enfile pas une seconde fois |

## La priorité règle un ordre, pas une urgence

Une file unique traite dans l'ordre d'arrivée : mille vignettes enfilées à midi font attendre le courriel de midi une seconde.

```python
enqueue("image.vignette", {...}, priority=0)    # le tout-venant
enqueue("mail.envoyer", {...}, priority=10)     # ce qu'un humain attend
```

!!! warning "La priorité ne préempte rien"
    Une tâche déjà en cours va au bout, quelle que soit la priorité de ce qui arrive derrière.

    Si une tâche longue bloque les urgentes, la réponse est une file séparée et son propre worker, pas une priorité plus haute.

## L'idempotence évite le double envoi

Un utilisateur qui clique trois fois sur « réinitialiser mon mot de passe » enfile trois courriels.

```python
enqueue("mail.reset", {...}, idempotency_key=f"reset:{utilisateur.id}")
```

!!! danger "La clé ne vaut que tant que la tâche est en file"
    Une fois traitée, la même clé enfile de nouveau.

    C'est voulu : sinon un utilisateur ne pourrait jamais redemander une réinitialisation. Si vous voulez un verrou durable, il vous appartient.

!!! info "Choisissez une clé qui décrit l'intention"
    `reset:42` dit « une réinitialisation pour l'utilisateur 42 ».

    Une clé aléatoire n'empêche rien, et une clé trop large, comme `reset`, empêcherait deux utilisateurs différents.

## À retenir

- `priority` ordonne la sortie de file, sans jamais interrompre une tâche en cours.
- `idempotency_key` empêche le doublon **en file**, pas après traitement.
- Une file séparée règle ce que la priorité ne règle pas.

## Étape suivante

[Suivant : le bail et le battement](jobs-bail.md)
