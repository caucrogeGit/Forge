# Positionnement de Forge

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Forge est un framework web MVC Python orienté lisibilité, SQL explicite et génération déterministe du modèle. La V1.0 est stable.

Il n'a pas vocation à remplacer Django, Flask ou FastAPI dans tous leurs usages. Son intérêt est ailleurs : fournir un socle compréhensible, pédagogique et maîtrisable pour des applications web de gestion.

## Forge est adapté à

- back-offices simples ou moyens ;
- applications CRUD structurées ;
- outils internes d'entreprise ;
- applications pédagogiques ;
- gestion de contacts, clients, commandes ou stocks ;
- dashboards simples ;
- prototypes MVC propres ;
- projets où le SQL doit rester visible ;
- projets où le modèle doit rester lisible et régénérable.

Typiquement : applications de gestion.

## Forge n'est pas encore adapté à

- très grosses applications avec beaucoup de modules ;
- API REST complexes ;
- authentification avancée multi-rôles très fine ;
- temps réel / WebSocket ;
- upload massif de fichiers ;
- applications SaaS multi-tenant ;
- migrations de schéma avancées ;
- ORM riche ;
- écosystème de plugins ;
- admin automatique type Django Admin ;
- intégration lourde cloud / cache / queue / workers ;
- grosse montée en charge sans couche serveur mature autour.

## Différence avec Django

Django fournit un écosystème très complet : ORM, admin, migrations, auth avancée, formulaires, conventions fortes.

Forge prend une direction différente : moins de magie, moins d'abstraction, plus de SQL visible et un modèle canonique JSON explicitement régénérable.

## Différence avec Flask

Flask est minimal et très libre, mais laisse beaucoup de décisions d'architecture au développeur.

Forge impose davantage de structure MVC, tout en restant beaucoup plus léger qu'un framework complet.

## Différence avec FastAPI

FastAPI est excellent pour construire des API modernes avec typage, validation et documentation OpenAPI.

Forge vise d'abord les applications web MVC rendues côté serveur, avec templates Jinja2, SQL explicite et modèle d'entités lisible.

## Public visé

Forge vise principalement :

- développeurs Python qui veulent comprendre leur architecture ;
- enseignants et étudiants ;
- projets internes ;
- petites équipes ;
- développeurs qui veulent éviter un ORM lourd ;
- projets pédagogiques où chaque couche doit rester observable.
