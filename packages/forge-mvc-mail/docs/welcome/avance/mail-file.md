# Avancé 3 : Envoyer en file d'attente

Objectif : qu'une inscription ne dépende pas de la disponibilité du serveur SMTP.

## Ce qu'un envoi direct coûte

Envoyer depuis le contrôleur tient la requête ouverte pendant que le SMTP répond.
Un serveur lent fait une page lente ; un serveur en panne fait une inscription échouée alors que le compte est créé.

`forge-mvc-jobs` porte la file, `forge-mvc-mail` fournit de quoi y entrer.

```python
from forge_mvc_jobs import enqueue
from forge_mvc_mail import MAIL_JOB_TASK, message_to_payload

enqueue(MAIL_JOB_TASK, message_to_payload(message, message_type="bienvenue"))
```

Côté worker, un gestionnaire prêt à l'emploi :

```python
# worker.py
from forge_mvc_mail import MAIL_JOB_TASK
from forge_mvc_mail.queueing import make_mail_job_handler

HANDLERS = {MAIL_JOB_TASK: make_mail_job_handler()}
```

!!! danger "Un message avec pièce jointe est refusé à la mise en file"
    `message_to_payload` lève, en nommant les fichiers.

    La charge utile d'une tâche est du JSON stocké en base : y mettre un PDF ferait grossir la table à chaque envoi, et la lecture de la file en pâtirait. Un envoi avec pièce jointe reste direct, ou passe par une référence au fichier plutôt que par son contenu.

!!! warning "Les deux paquets restent indépendants"
    `forge-mvc-mail` n'importe pas `forge-mvc-jobs`, et l'inverse est vrai aussi.

    C'est votre application qui les compose, en trois lignes : sans cela, installer l'un imposerait l'autre.

!!! info "Le type de message voyage avec la charge"
    `message_type="bienvenue"` se retrouve dans le journal des envois.

    Sans lui, le journal dit qu'un courriel est parti, jamais lequel, et une plainte « je n'ai pas reçu mon lien » reste sans réponse.

## Ce que la file ne règle pas

Elle diffère l'envoi ; elle ne le garantit pas.
Une tâche qui échoue est réessayée selon `max_attempts`, et finit `failed` si le serveur reste injoignable. `forge jobs:status` le montre.

## À retenir

- La file découple la requête de la disponibilité du SMTP.
- Les pièces jointes sont refusées en file, délibérément.
- La composition est explicite : ni l'un ni l'autre paquet n'importe son voisin.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
