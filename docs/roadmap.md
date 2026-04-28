# Roadmap Forge

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette roadmap est volontairement prudente. Elle décrit une trajectoire possible, sans transformer les idées futures en promesses immédiates.

---

## État actuel — V1.0 stable

Forge V1.0 fournit un socle MVC complet :

- modèle canonique JSON → projections SQL et Python générées
- `forge make:entity`, `forge build:model`, `forge db:init`, `forge db:apply`
- `forge make:crud` — scaffolding CRUD lisible et non destructif
- `forge routes:list`, `forge doctor`, `forge deploy:init`, `forge deploy:check`
- CSRF automatique sur `POST`, `PUT`, `PATCH`, `DELETE`
- method override `POST` → `PUT`, `PATCH`, `DELETE`
- formulaires (`Form`, `Field`, `ChoiceField`, `RelatedIdsField`) et erreurs
- flash + POST-Redirect-GET (`redirect_with_flash()`)
- erreurs HTTP standardisées dont `422`
- transactions explicites et helper DB léger
- `url_for` Jinja2 et `redirect_to_route()`
- pagination standardisée (`Pagination`)
- starter apps 1, 2 et 3 générables automatiquement (`forge starter:build`)
- déploiement Nginx + systemd documenté

---

## V1.4 — Confort applicatif

Objectif : rendre les écrans de gestion agréables.

Pistes possibles :

- recherche et tri sécurisé dans les listes
- templates de formulaire réutilisables
- `FormSet` simple pour pivots enrichis
- `forge model:show` — inspection du modèle en CLI
- fixtures / seeders

---

## V2 — Extensions lourdes

À repousser après stabilisation de la forme manuelle idéale.

- migrations de schéma avancées
- admin automatique
- permissions fines
- API REST complète avec documentation OpenAPI
- génération avancée de CRUD
- Forge Design (bibliothèque de composants)

---

## Hors roadmap

Ne sont pas prioritaires :

- ORM complet
- multi-tenant SaaS
- WebSocket / queue / workers
- plugin marketplace
- abstraction cloud lourde
