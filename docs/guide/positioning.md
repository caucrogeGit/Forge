# Positionnement de Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Forge est un framework web MVC Python orienté lisibilité, SQL explicite et génération déterministe du modèle.
Il est disponible en bêta publique, sur la trajectoire 1.0.

Son pari : un framework que vous pouvez **lire en entier**.
Pas de magie cachée, du SQL visible, une sécurité par défaut et un runtime minimal, pour des applications de **production dont vous comprenez et auditez chaque ligne**.
Forge n'a pas vocation à remplacer Django, Flask ou FastAPI dans tous leurs usages : son intérêt est ailleurs, dans l'auditabilité et la maîtrise sur la durée.

## Forge est adapté à

- back-offices et outils internes d'entreprise ;
- applications métier durables : gestion de contacts, clients, commandes, stocks ;
- applications CRUD structurées et dashboards ;
- sites publics reliés à une administration interne ;
- contextes (sécurité, conformité, maintenance longue) où chaque ligne doit rester compréhensible et auditable ;
- projets où le SQL doit rester visible et le modèle lisible et régénérable.

Typiquement : des applications de gestion que l'on garde et fait évoluer pendant des années.

## Ce pour quoi Forge n'est pas fait

Certaines limites sont des choix d'architecture assumés (noyau minimal, voir ADR-004), d'autres ne sont pas encore couvertes :

- très grosses applications à très nombreux modules ;
- API REST complexes (Forge vise le rendu serveur, pas le moteur d'API) ;
- temps réel / WebSocket ;
- applications SaaS multi-tenant ;
- migrations de schéma avancées ;
- ORM riche et écosystème de plugins ;
- admin automatique type Django Admin ;
- intégration lourde cloud / cache / file d'attente / workers ;
- montée en charge massive sans couche serveur mature autour.

Annoncer clairement ces limites fait partie du contrat : vous savez quand Forge convient, et quand un autre outil sera plus adapté.

## Différence avec Django

Django fournit un écosystème très complet : ORM, admin, migrations, auth avancée, formulaires, conventions fortes.

Forge prend une direction inverse : moins de magie, moins d'abstraction, plus de SQL visible et un modèle canonique JSON explicitement régénérable.
Vous lisez et auditez tout le chemin d'une requête, sans couche cachée.

## Différence avec Flask

Flask est minimal et très libre, mais laisse beaucoup de décisions d'architecture au développeur, y compris la sécurité.

Forge impose une structure MVC et une sécurité par défaut (CSRF, sessions, hachage Argon2id), tout en restant beaucoup plus léger qu'un framework complet.

## Différence avec FastAPI

FastAPI est excellent pour construire des API modernes avec typage, validation et documentation OpenAPI.

Forge vise d'abord les applications web MVC rendues côté serveur, avec templates Jinja2, SQL explicite et modèle d'entités lisible.

## Public visé

Forge vise principalement :

- les équipes et développeurs qui mettent en production des applications web Python et veulent en maîtriser et auditer chaque ligne ;
- les petites équipes et les projets internes qui doivent durer ;
- les développeurs qui veulent éviter un ORM lourd et garder le SQL visible.

Forge sert aussi naturellement l'apprentissage : un code que l'on peut lire en entier est, de fait, un excellent support pour enseigner le web Python.
Les parcours d'accueil et les starters s'appuient sur cette qualité.
