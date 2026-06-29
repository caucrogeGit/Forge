# Décisions d'architecture (ADR)

Les *Architecture Decision Records* documentent les décisions structurantes
de Forge. Chaque ADR a **force décisionnelle** : à lire avant toute
proposition qui le concerne. Un nouvel ADR est requis pour toute décision
structurante (`docs/adr/<numéro>-<sujet>.md`).

| Numéro | Sujet |
|---|---|
| [ADR-001](001-auth-strategy.md) | Stratégie d'authentification |
| [ADR-002](002-session-strategy.md) | Stockage de session |
| [ADR-003](003-language-convention.md) | API publique en anglais |
| [ADR-004](004-core-perimeter.md) | Périmètre du core minimal strict |
| [ADR-005](005-packaging.md) | Packaging hybride monorepo + multi-distributions PyPI |
| [ADR-006](006-python-version.md) | Python 3.12+ minimum |
| [ADR-007](007-charter-v2-adoption.md) | Adoption formelle de la charte v2 |
| [ADR-008](008-auth-audit-architecture.md) | Audit auth : logging fourni, persistance applicative |
| [ADR-009](009-stability-policy-terrain.md) | Politique de stabilité : audits, bêta consolidée, tests terrain |
| [ADR-010](010-auth-session-canonical-api.md) | API canonique auth/session |
| [ADR-011](011-auth-audit-vocab-perimeter.md) | Périmètre du vocabulaire d'audit auth |
| [ADR-012](012-legacy-format-deprecation-policy.md) | Politique de dépréciation du format legacy |
| [ADR-013](013-nullable-required-contract-policy.md) | Politique nullable / required des contrats |
| [ADR-014](014-rbac-contract-location.md) | Emplacement du contrat RBAC |
| [ADR-015](015-dev-tls-handshake-per-thread.md) | Handshake TLS par thread (dev-server) |
| [ADR-016](016-opt-in-unification.md) | Unification du modèle opt-in : concept unique, cycle install/enable à 4 verbes |
| [ADR-017](017-slug-type.md) | Type `slug` et module URL-slug canonique (`core/http/slug.py`) |
| [ADR-018](018-image-module-extraction.md) | Extraction du traitement d'image hors du core : `forge-mvc-images` (proposé) |
| [ADR-019](019-upload-extraction.md) | Extraction de l'upload générique hors du core : `forge-mvc-files` (proposé) |
| [ADR-020](020-files-media-storage-primitives.md) | Périmètre de `forge-mvc-files` : primitives de stockage média génériques (proposé) |
| [ADR-021](021-pivot-extraction.md) | Extraction de pivot advanced hors du core : `forge-mvc-pivot` (accepté) |
| [ADR-022](022-mail-extraction.md) | Extraction de l'email hors du core : `forge-mvc-mail` (accepté) |
| [ADR-023](023-starter-build-canonical.md) | `forge starter:build` comme seule façon de construire un starter ; `forge new` produit un projet nu (accepté) |
| [ADR-024](024-skeleton-bootstrap.md) | Bootstrap par squelette dédié et dépendance core via pip (accepté) |
| [ADR-025](025-welcome-forge-continuous-tutorial.md) | welcome-forge : tutoriel continu manuel au lieu de starters par palier (accepté) |
| [ADR-026](026-request-param-naming.md) | Accesseurs de Request nommés par leur source : `query` et `route` (accepté) |
| [ADR-027](027-i18n-extraction.md) | Extraction de l'i18n vers `forge-mvc-i18n`, repli no-op conservé dans le noyau (accepté) |
| [ADR-028](028-welcome-forge-tutorial-per-level.md) | welcome-forge : tutoriel continu manuel sur les trois niveaux, un mini-projet par niveau (accepté) |
| [ADR-029](029-route-naming-convention.md) | Convention de route : chemin `/contrôleur/méthode` (index nu), nom `contrôleur-méthode` (accepté) |
| [ADR-030](030-explicit-route-injection.md) | Injection de routes dans `mvc/routes.py` par commande explicite et portée de la règle 4.3 (accepté) |
| [ADR-031](031-mail-core-decoupling.md) | Découplage complet du mail hors de `core.forge` ; `forge-mvc-mail` lit sa config depuis l'environnement (accepté) |
| [ADR-032](032-upload-config-perimeter.md) | Périmètre de la config upload : seul `upload_max_size` est du core, le reste va aux opt-ins files/images (accepté) |
| [ADR-033](033-migrations-admin-credentials.md) | `forge db:apply` applique les migrations avec `DB_ADMIN_*` (et non `DB_APP_*`) : `forge_app` reste DML strict (accepté) |
| [ADR-034](034-generated-db-identifier-naming.md) | `forge new` génère `DB_NAME` / `DB_APP_LOGIN` à partir du nom normalisé du projet, sans suffixes `_db`/`_app` (accepté) |
| [ADR-035](035-starters-manual-not-generated.md) | Modèle pédagogique unique : parcours réalisés à la main depuis la doc, retrait de `starter:build`/`starter:list` et de la génération (accepté) |
| [ADR-036](036-core-static-typing.md) | Typage statique du cœur vérifié en CI (Pyright), `py.typed`, strictness par cliquet en commençant par l'API publique (accepté) |
| [ADR-037](037-stats-aggregation.md) | Agrégation par comptage dans `forge-mvc-stats` (accepté) |
| [ADR-038](038-optin-docs-embedded-per-package.md) | Documentation des opt-ins embarquée par paquet (`packages/<paquet>/docs/`), agrégée dans le site unique ; slug d'URL = nom sans `forge-mvc-` (accepté, pilote stats validé) |
| [ADR-039](039-docs-information-architecture.md) | Refonte de l'architecture d'information de `docs/` (cœur) : un sujet = un emplacement canonique, tronc « Opt-ins officiels », dédoublonnages (proposé) |
| [ADR-040](040-per-package-test-surface.md) | Surface de test par paquet opt-in : modèle hybride (transversal à la racine, smoke + unitaire dans le paquet), `testpaths = tests packages`, `importorskip` (accepté) |
| [ADR-041](041-shared-test-support.md) | Infrastructure de test partagée (`forge-mvc-testing` dev-only, plugin pytest + `FakeRequest`) pour rendre les tests de paquet autonomes (accepté) |
| [ADR-042](042-doc-core-optins-decoupling.md) | Découpler la documentation du cœur et celle des opt-ins (accepté) |
| [ADR-043](043-core-cli-doc-embedding.md) | Documentation embarquée du cœur et du CLI ; renommage `forge_cli` → `cli` (accepté) |
| [ADR-044](044-framework-only-repo.md) | Le dépôt Forge ne porte que le framework ; application racine relocalisée (accepté) |
| [ADR-045](045-official-site-integration.md) | Intégrer la publication du site officiel dans Forge (accepté) |
| [ADR-046](046-optin-jinja-template-loaders.md) | Registre de loaders de templates Jinja pour les opt-ins (accepté) |
| [ADR-047](047-app-agent-guidance-layer.md) | Couche de guidance agent IA dans les applications Forge (accepté) |
| [ADR-048](048-skeleton-welcome-projet.md) | Parcours d'accueil « welcome-projet » dans le squelette (annulé) |
| [ADR-049](049-positioning-production-auditable.md) | Repositionnement : framework de production auditable (accepté) |
| [ADR-050](050-qrcode-optin.md) | Opt-in QR Code `forge-mvc-qrcode` (accepté) |
| [ADR-051](051-public-page-controller-insertion.md) | Insertion d'une méthode dans le contrôleur des pages publiques (`make:public-page`), explicite, idempotente, fail-safe et ciblée (proposé) |
| [ADR-052](052-optin-strategy.md) | Stratégie et critères des opt-ins : deux filtres d'admission (runtime WSGI, charte), classification des candidats, ordre recommandé (proposé) |
| [ADR-053](053-deploy-extraction.md) | Extraction du déploiement (`deploy:init`/`deploy:check` + gabarits + doc) dans un opt-in CLI-only `forge-mvc-deploy` (proposé) |
| [ADR-054](054-database-backend-optins.md) | Cœur agnostique BDD : backends (MariaDB, SQLite, PostgreSQL, SQL Server) en opt-ins exclusifs, découverts par entry points (proposé) |
| [ADR-055](055-optin-categories.md) | Classification des opt-ins par destination : champ `category` au catalogue, taxonomie unique (CLI + docs), sans renommer les paquets (proposé) |
