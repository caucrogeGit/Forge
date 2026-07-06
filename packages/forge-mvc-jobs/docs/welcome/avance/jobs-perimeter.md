# Quand utiliser Jobs

Objectif : savoir quand recourir à une file de tâches, et connaître les limites du modèle.

**Ce que vous allez apprendre :** une file de tâches sert à déporter un travail lourd hors de la requête HTTP.
Le modèle de `forge-mvc-jobs` reste volontairement simple : une table MariaDB et un worker explicite, sans broker ni code asynchrone.

Premier palier du **niveau avancé** de la progression Jobs.

!!! note "Module opt-in"
    Si `forge-mvc-jobs` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- les cas où une file de tâches est justifiée ;
- le modèle sans broker ni async, fidèle à la charte ;
- la limite de la version actuelle.

## Quand recourir à une file

Utilisez Jobs dès qu'un traitement risque de ralentir la requête HTTP.

```text
Envoi d'emails en nombre     ->  enqueue, traité par le worker
Transcodage audio ou vidéo   ->  enqueue, traité par le worker
Import massif de données      ->  enqueue, traité par le worker
```

- Quand un opt-in ferait un travail lourd pendant la requête, déportez-le dans la file.
- La requête répond vite ; le worker fait le travail à son rythme.
- Pour un calcul instantané, n'utilisez pas de file : c'est une complexité inutile.

## Le modèle sans broker ni async

```text
File de tâches  =  une table jobs (MariaDB)
Worker          =  une commande explicite lancée par l'application
Serveur web     =  synchrone (WSGI), il enfile et répond
```

- Il n'y a ni broker, ni Celery, ni Redis, ni code asynchrone.
- Le SQL reste visible : la file est une table que vous pouvez inspecter.
- Le worker est un process explicite, lancé par l'application, jamais caché.

Ce modèle suit la charte Forge : pas de magie cachée, SQL visible, brique opt-in.

## Limite de la version actuelle

```text
Crash du worker pendant une tâche  ->  la tâche reste en statut running
```

- Une tâche interrompue par un crash du worker reste en statut `running`.
- La version actuelle ne reprend pas automatiquement une telle tâche.
- À surveiller si vos tâches sont longues et le process worker peu fiable.

## À retenir

- Jobs sert à sortir un travail lourd de la requête HTTP.
- Le modèle reste simple : table MariaDB plus worker explicite, sans broker ni async.
- Limite actuelle : pas de reprise automatique d'une tâche restée `running` après un crash.

## Après ce starter

Vous savez quand et pourquoi utiliser une file.
Voyons l'indépendance du paquet vis-à-vis du cœur.

[Indépendance du cœur](jobs-independance.md)
