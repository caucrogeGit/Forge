# Définir un gestionnaire

Objectif : écrire le code qui traite une tâche et vider la file.

**Ce que vous allez apprendre :** un gestionnaire est une fonction qui reçoit la charge utile (un dict).
On associe chaque nom de tâche à son gestionnaire dans un dict `handlers`, puis on traite toutes les tâches disponibles avec `drain`.

Deuxième palier du **niveau débutant** de la progression Jobs.

## Ce que ce starter montre

- définir une fonction gestionnaire qui reçoit la charge utile ;
- associer un nom de tâche à un gestionnaire dans un dict `handlers` ;
- traiter toutes les tâches disponibles en une passe avec `drain`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `drain(handlers)` | Traite toutes les tâches disponibles ; renvoie le nombre traité. | Opt-ins |

## 1. Écrire un gestionnaire et vider la file

```python
from forge_mvc_jobs import drain


def envoyer_email(payload):
    destinataire = payload["to"]
    print(f"Envoi d'un email à {destinataire}")


handlers = {
    "email.envoi": envoyer_email,
}

traitees = drain(handlers)
print(f"{traitees} tâche(s) traitée(s)")
```

### Comprendre ce code

- `envoyer_email(payload)` est le gestionnaire : il reçoit la charge utile passée à `enqueue`.
- `payload` est le dict enfilé plus tôt, par exemple `{"to": "client@exemple.fr"}`.
- Le dict `handlers` associe le nom de tâche `"email.envoi"` à sa fonction.
- `drain(handlers)` traite toutes les tâches disponibles de la file, en une seule passe.
- La valeur renvoyée est le nombre de tâches traitées (`int`).

## À retenir

- Un gestionnaire est une fonction `def gestionnaire(payload): ...`.
- Le dict `handlers` relie chaque nom de tâche à sa fonction.
- `drain(handlers)` vide la file disponible et renvoie le nombre traité.

## Après ce starter

Vous savez enfiler et traiter une tâche.
Faisons le point sur le niveau débutant.

[Bilan débutant](bilan.md)
