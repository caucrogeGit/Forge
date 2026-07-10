# Décisions d'architecture (ADR)

Les *Architecture Decision Records* documentent les décisions structurantes de Forge.
Chaque ADR a **force décisionnelle** : à lire avant toute proposition qui le concerne.
Un nouvel ADR est requis pour toute décision structurante (`docs/adr/<numéro>-<sujet>.md`).

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
| [ADR-056](056-rbac-contract-tooling-extraction.md) | Extraction du contrat (schéma) et de l'outillage RBAC (`rbac:validate`/`rbac:audit`) du cœur vers l'opt-in `forge-mvc-rbac` (proposé) |
| [ADR-057](057-pivot-schema-decoupling.md) | Découplage du schéma pivot : `relations` (cœur) cesse de référencer `pivot` (bloc opaque), `pivot.schema.json` extrait vers `forge-mvc-pivot` (proposé) |
| [ADR-058](058-schemas-single-source.md) | Source unique des schémas JSON : `cli/schemas/` canonique, suppression de la copie racine `schemas/`, squelette et embeds opt-in = copies dérivées gardées (proposé) |
| [ADR-059](059-cli-command-dispatch-registry.md) | Registre de dispatch des commandes CLI : tables de dispatch opt-in et cœur, découverte par entry points `forge_mvc.commands` (accepté) |
| [ADR-060](060-backend-free-skeleton.md) | Squelette livré sans backend BDD : `requirements.txt` ne pin que `forge-mvc`, la config BDD quitte le squelette pour le backend installé (accepté) |
| [ADR-061](061-optin-project-registry.md) | Registre d'opt-ins visible et unifié (`optins/registry.py`, à la `config/bundles.php` de Symfony) : une ligne par opt-in utilisé, tous `kind` + backend, code toujours dans le `.venv` (accepté) |
| [ADR-062](062-forge-new-install-source.md) | `forge new` épingle le projet généré sur la source dont provient le CLI : Git (`forge-mvc @ git+…@commit`) si installé depuis GitHub, PyPI sinon ; détection via `direct_url.json` PEP 610 (accepté) |
| [ADR-063](063-skeleton-quality-enforcement-config.md) | Le squelette livre par défaut l'apparat qualité Forge complet (typage `# pyright: strict`, `ruff`, socle `pytest` + smoke, `mkdocs`, CI, `make check`, scaffold ADR, `.editorconfig`, `CHANGELOG`) et garde le noyau applicatif minimal ; échappatoire `forge new --bare` ; révise la portée de « nu » d'ADR-024 (acceptée) |
| [ADR-064](064-db-config-env-scaffold.md) | `forge db:config` amorce les variables d'environnement du backend BDD dans `env/example`, `env/dev` et `env/prod` (write-if-missing, annoncé, sans secret) ; le contrat `DatabaseBackend` porte `env_template` ; `db:init` reste focalisé sur le provisioning (acceptée) |
| [ADR-065](065-skeleton-top-level-package.md) | Le squelette de projet passe de `cli/skeleton/` à `skeleton/` à la racine, en restant un paquet Python (`packages += skeleton*`, `package-data` re-clés) : plus découvrable, toujours empaqueté dans le wheel ; imports `cli.skeleton` → `skeleton` (acceptée) |
| [ADR-066](066-db-host-port-unification.md) | Le contrat d'environnement des backends BDD unifie l'adresse serveur : `DB_HOST`/`DB_PORT` partagés par les connexions applicative et d'administration, seuls les identifiants restant distingués (`DB_APP_*`/`DB_ADMIN_*`) ; `DB_APP_HOST`/`DB_ADMIN_HOST` et leurs ports disparaissent (acceptée) |
| [ADR-067](067-db-init-provisioning-sql.md) | `forge db:init` génère et affiche par défaut le SQL de provisioning dérivé de `env/` (base + comptes scellés à `DB_NAME`), à exécuter dans une session d'administration ; `--run` exécute (opt-in) ; plus aucun root serveur exigé dans `env/` ; `DB_ADMIN_*` = propriétaire de la base du projet (acceptée) |
| [ADR-068](068-per-controller-routes-package.md) | Les routes applicatives passent d'un `mvc/routes.py` monolithique à un package `mvc/routes/` : `__init__.py` branche explicitement chaque `register_<controleur>_routes(router)`, un fichier `mvc/routes/<snake>_routes.py` par contrôleur ; `make:crud`/`make:auth`/`make:public-page` génèrent le fichier et affichent le branchement ; pas d'auto-découverte (proposée) |
| [ADR-069](069-foreign-key-field-type.md) | La clé étrangère devient un champ de première classe de l'entité source (type `foreign_key` + `references`, normalisé au type de la PK visée, colonne snake_case) ; `make:relation` l'injecte dans le JSON d'entité ; `relations.sql` ne pose plus que la contrainte |
| [ADR-070](070-entities-engine-extraction.md) | Le moteur d'entités (génération et modélisation : `make:entity`, `make:relation`, normaliseur, validation, `build:model`, migrations, `make:crud`, provisioning `db:*`) est extrait du cœur vers un opt-in `forge-mvc-entities` qui absorbe `forge-mvc-pivot` ; le cœur ne garde que la couture runtime `core/database` ; dépend du contrat `Dialect`, indépendant des backends (acceptée) |
| [ADR-071](071-optin-db-provisioning-convention.md) | Convention unique de provisioning des opt-ins adossés à la base : la commande `<opt-in>:init` dépose une migration dans `mvc/migrations/`, appliquée par `forge migration:apply` (déjà suivie par 7 opt-ins) ; `mvc/models/sql/` + `db:apply` reste réservé au modèle applicatif (socle auth) ; `forge-mvc-sessions-db` réaligné (acceptée) |
| [ADR-072](072-optin-cli-command-contract.md) | Contrat des commandes CLI des opt-ins : `dispatch_optin` intercepte `-h`/`--help` avant tout effet (F40) et amorce la config projet (`env/dev` via `load_project_config`) pour les commandes déclarant `config: True` dans leur table `COMMANDS` (F39, `sessions:gc`), comme le cœur le fait pour `migration:apply` ; clé additive rétro-compatible (acceptée) |
