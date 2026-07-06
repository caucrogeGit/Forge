# Première tâche en file

Objectif : premier contact avec le module **opt-in** `forge-mvc-jobs`.

**Ce que vous allez apprendre :** on enfile une tâche avec `enqueue`.
La fonction écrit une ligne dans la table `jobs` et renvoie son identifiant.
La requête HTTP n'attend pas le traitement : elle répond tout de suite, le travail sera fait plus tard par un worker.

Premier palier du **niveau débutant** de la progression Jobs.

!!! note "Module opt-in"
    Si `forge-mvc-jobs` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- enfiler une tâche avec `enqueue` depuis un contrôleur ;
- comprendre que la requête répond immédiatement, sans faire le travail.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `enqueue(task, payload)` | Écrit une tâche dans la file et renvoie son identifiant. | Opt-ins |

## 1. Enfiler une tâche depuis un contrôleur

```python
# mvc/controllers/inscription_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_jobs import enqueue


class InscriptionController(BaseController):

    @staticmethod
    def store(request: Request) -> Response:
        job_id = enqueue("email.envoi", {"to": "client@exemple.fr"})
        return Response.text(f"Inscription reçue, tâche {job_id} en file")
```

### Comprendre ce code

- `enqueue("email.envoi", {"to": "client@exemple.fr"})` écrit une tâche dans la table `jobs`.
- Le premier argument, `"email.envoi"`, est le **nom de la tâche** : il dira plus tard quel gestionnaire l'exécute.
- Le second argument est la **charge utile**, un dict sérialisé en JSON.
- `enqueue` renvoie l'identifiant de la tâche (`int`), utile pour la suivre.
- La requête répond aussitôt : aucun email n'est envoyé pendant cette requête.

## À retenir

- `enqueue(nom, charge)` enfile une tâche et renvoie son identifiant.
- La charge utile est un dict, sérialisé en JSON.
- Enfiler ne traite pas la tâche : la requête HTTP reste rapide.

## Après ce starter

Vous savez enfiler une tâche.
Voyons maintenant qui la traite, et comment.

[Définir un gestionnaire](jobs-handler.md)
