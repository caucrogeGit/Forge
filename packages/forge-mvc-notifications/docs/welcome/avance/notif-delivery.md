# Périmètre et livraison

Objectif : comprendre que ce paquet ne fait que le stockage in-app, et comment livrer hors application.

**Ce que vous allez apprendre :** le périmètre V1 de `forge-mvc-notifications` se limite aux notifications in-app, c'est-à-dire des lignes en base, affichées dans l'IHM. La livraison hors application (email, push) reste applicative.
On peut la réaliser en combinant ce paquet avec `forge-mvc-jobs` et `forge-mvc-mail`.

Premier palier du **niveau avancé** de la progression Notifications.

!!! note "Module opt-in"
    Si `forge-mvc-notifications` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- le périmètre in-app du paquet ;
- comment livrer un email hors application en combinant avec d'autres opt-ins.

## Le périmètre in-app

```text
forge-mvc-notifications stocke des notifications in-app (lignes en base).
Il ne fait aucun envoi : ni email, ni push, ni SMS.
L'affichage des notifications se fait dans l'IHM de l'application.
```

Ce paquet ne fait **que** le stockage in-app.
La création, la lecture et l'état lu portent uniquement sur des lignes de la table `notifications`.

## Livrer par email hors application

La livraison hors application reste de la responsabilité de l'application.
Un schéma courant combine deux autres opt-ins :

```python
from forge_mvc_notifications import notify
# from forge_mvc_jobs import enqueue
# from forge_mvc_mail import send

# 1. Notification in-app, gérée par ce paquet.
notify("eleve.42", "Votre note est publiée", type="info")

# 2. Livraison email, gérée par l'application via une tâche de fond.
# enqueue("envoyer_email_note", {"recipient": "eleve.42"})
#   -> le job appelle send(...) de forge-mvc-mail
```

### Comprendre ce code

- `notify(...)` reste le seul appel relatif à `forge-mvc-notifications` : il stocke la notification in-app.
- L'application enfile un job avec `forge-mvc-jobs` pour traiter l'envoi en arrière-plan.
- Le job appelle `forge-mvc-mail` pour l'envoi effectif de l'email.
- Aucune de ces deux dernières étapes n'incombe à `forge-mvc-notifications`.

## À retenir

- Le périmètre V1 est strictement in-app : des lignes en base, affichées dans l'IHM.
- Ce paquet ne fait ni email, ni push : la livraison hors application est applicative.
- Un schéma type combine `forge-mvc-notifications`, `forge-mvc-jobs` et `forge-mvc-mail`.

## Après ce starter

Vous cernez le périmètre du paquet.
Voyons son indépendance vis-à-vis du cœur et ses points d'extension pour les tests.

[Indépendance du cœur](notif-independance.md)
