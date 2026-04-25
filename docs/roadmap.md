# Roadmap Forge

Cette roadmap est volontairement prudente. Elle décrit une trajectoire possible, sans transformer les idées futures en promesses immédiates.

## V1.2 — Stabilisation du socle

Objectif : rendre Forge fiable.

Inclus :

- packaging Python ;
- `forge check:model` ;
- booléens cohérents ;
- documentation MkDocs stricte ;
- starter app clarifié ;
- validation globale du modèle d'entités.

## Socle CRUD explicite

Objectif : pouvoir écrire une vraie application de gestion sans bricoler à chaque formulaire.

Forge vise à rendre possible un CRUD applicatif complet, explicite et lisible, sans ORM implicite : formulaires, validation, CSRF automatique, messages flash, redirections, erreurs de formulaire et modèles applicatifs SQL structurés.

Doctrine associée :

- Forge ne génère pas de repository magique.
- Forge ne cache pas le SQL.
- Forge fournit une structure stable pour organiser le CRUD.
- Le développeur reste propriétaire du modèle applicatif.

Inclus :

- CSRF automatique sur `POST`, `PUT`, `PATCH`, `DELETE` ;
- method override `POST` vers `PUT`, `PATCH`, `DELETE` ;
- exemption CSRF explicite via `csrf=False` ;
- métadonnées de route `public`, `csrf`, `api` ;
- `core/forms/` pour `Form`, `Field`, `ChoiceField`, `cleaned_data` et erreurs ;
- `mvc/forms/` pour les formulaires applicatifs ;
- `RelatedIdsField` pour les sélections liées autour d'une entité pivot explicite ;
- documentation "Formulaires de pivot explicite" ;
- flash + redirection via `redirect_with_flash()` ;
- erreurs HTTP standardisées, dont `422` ;
- transactions explicites ;
- helper DB léger compatible `tx` ;
- `url_for` dans Jinja2 et `redirect_to_route()` ;
- pagination standardisée avec `limit` et `offset` ;
- diagnostic `forge routes:list`.

Surveillé mais non obligatoire dans le socle CRUD :

- `FormSet` simple pour pivots enrichis, à repousser en V1.4 si le socle devient trop lourd.

## V1.4 — Confort applicatif

Objectif : rendre les écrans de gestion agréables.

Pistes possibles :

- recherche ;
- tri sécurisé ;
- uploads simples ;
- templates de formulaire réutilisables.

## V1.1 — Outillage développeur

Objectif : aider le développeur à comprendre son application.

Pistes possibles :

- `forge doctor` ;
- `forge model:show` ;
- fixtures / seeders ;
- aide au diagnostic DB ;
- tests applicatifs guidés.

## V2 — Extensions lourdes

À repousser clairement :

- migrations avancées ;
- admin automatique ;
- permissions fines ;
- API REST complète ;
- Forge Design ;
- génération avancée de CRUD.

Ces sujets peuvent devenir utiles, mais seulement après stabilisation de la forme manuelle idéale.

## Hors roadmap immédiate

Ne sont pas prioritaires à court terme :

- ORM complet ;
- admin automatique type Django Admin ;
- multi-tenant SaaS ;
- WebSocket ;
- queue / workers ;
- plugin marketplace ;
- abstraction cloud lourde.
