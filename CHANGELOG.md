# Changelog


## [Non publié]

> Le niveau débutant du parcours `welcome-forge` devient un tutoriel continu
> manuel : un seul projet qui grandit, au lieu de starters indépendants par
> palier (ADR-025).

### Modifié

- **welcome-forge débutant : tutoriel continu manuel** (ADR-025,
  `STARTER-WELCOME-FORGE-DOC-CONTINUITY-001`). Les 11 paliers (de « Bonjour
  Forge » à « Écrire en base ») se construisent désormais à la main dans un
  seul projet qui grandit : un `WelcomeController` accumule les paliers HTTP
  (1 à 9), puis un `MessageController` porte les paliers SQL (10 et 11), avec
  un `mvc/routes.py` cumulatif montré à chaque étape. Pages francisées (retrait
  des tirets cadratins). Préambule d'installation sans `forge starter:build`.

### Retiré

- **Les 11 starters buildables du niveau débutant welcome-forge** sont retirés
  de `forge_cli/starters/data/` et du contrat public gelé, ramené de 107 à 96
  starters (ADR-025, `STARTER-WELCOME-FORGE-DROP-DATA-001`). Les niveaux
  intermédiaire et avancé, ainsi que tous les parcours opt-in, restent des
  starters `forge starter:build`. La numérotation des starters n'est plus une
  plage dense `1..N` (unicité seule).


## [1.0.0-beta.14] — 2026-06-07

> Bootstrap par squelette dédié : `forge new` produit enfin un projet
> réellement nu (ADR-024).

### Modifié

- **`forge new` matérialise un squelette de projet dédié** au lieu de cloner le
  dépôt Forge (ADR-024, `NEW-MATERIALIZE-001`). Le projet généré ne contient
  plus le framework (`core/`, `forge_cli/`, `packages/`, `tests/`, `docs/`) : il
  dépend de `forge-mvc` et récupère le `core` depuis le paquet installé. Le
  squelette curé est embarqué dans `forge_cli/skeleton/data/` et distribué en
  package-data (`SKELETON-TREE-001`, `SKELETON-PKGDATA-001`,
  `SKELETON-REGISTRY-001`).
- **`forge new` ne clone plus le dépôt** : le flag `--ref`, la constante
  `_FORGE_REPO` et la dépendance réseau/git pour les fichiers disparaissent
  (`NEW-MATERIALIZE-001`, `NEW-CLI-CLEANUP-001`). `git` reste requis pour le
  `git init` du projet.
- **`forge new` produit toujours un projet nu** : le flag `--starter` est retiré ;
  `forge starter:build` devient la seule façon officielle de construire un
  starter (ADR-023, `CLI-NEW-DROP-STARTER-001`).

### Corrigé

- Alignement de la documentation sur `forge starter:build` et retrait du bloc
  « raccourci » des pages de palier (`DOC-STARTER-BUILD-ALIGN-001`).
- Test des liens production de la landing aligné sur la réorganisation
  `docs/deployment/` (`LANDING-WSGI-LINK-TEST-FIX-001`).

### Documentation

- ADR-023 (`forge starter:build` canonique) et ADR-024 (bootstrap par squelette
  dédié) ajoutés ; index ADR et navigation MkDocs mis à jour. Documentation
  d'installation et de référence nettoyée des mentions `forge new --ref`.

### Tests

- Garde-fous ajoutés : `test_skeleton_tree_001`, `test_skeleton_pkgdata_001`,
  `test_skeleton_registry_001`, `test_new_core_dep_001`, `test_skeleton_guard_001`
  (squelette nu, distribution wheel/sdist, matérialisation, neutralité, projet
  généré sans `core/`).


## [1.0.0-beta.13] — 2026-06-06

> Dernière beta **fonctionnelle** (consolidation post-beta.12).
> Roadmap : [`docs/roadmap/beta13-roadmap.md`](docs/roadmap/beta13-roadmap.md).

### Unification du modèle opt-in (ADR-016)

- Famille de commandes canonique **`forge opt-in:install / remove / enable /
  disable / list`** (à tiret). `opt-in:install`/`remove` affichent la commande
  pip/pipx sans rien exécuter ; `enable`/`disable` sont *kind-aware* (câblage
  réel pour les opt-ins routiers — iot ; informatif pour bibliothèques et
  transversaux). Anciennes commandes `optin:enable` / `optin:list` **retirées**
  (rupture assumée pré-1.0, sans alias).
- **Squelette neutre** : `mvc/routes.py` livré par défaut n'expose plus que
  `GET /` → landing ; auth, MFA et le starter `welcome` ne sont plus
  pré-câblés (relocalisés dans leurs starters/opt-ins).
- Vocabulaire unifié : « module officiel » → **« opt-in »** (glossaire
  `docs/reference/vocabulaire-opt-in.md`) ; « package » = véhicule de
  distribution. Le système `module:*` (module **local**) reste distinct
  (cycle de vie d'auteur — ADR-016 A2).

### Refonte des starters — un parcours welcome par opt-in

- **107 starters** numérotés de façon contiguë, organisés en **parcours
  pédagogiques par niveau** : la progression cœur `welcome-forge` (11 paliers
  débutant → avancé) plus **un parcours `welcome-<module>` pour chacun des 10
  opt-ins dotés d'un parcours** (iot, video, images, files, audio, mfa, rbac,
  workflow, stats, mail). Préambule d'installation en tête de chaque parcours
  (`pip install --pre forge-mvc-<module>` + `forge starter:build`).
- **Nettoyage** (`STARTERS-DROP-OBSOLETE-001`) : retrait des starters obsolètes
  (`first-crud`, `first-crud-generated`, `users-core-auth`, mono-démos
  `welcome-optin-iot/mfa/video`) et de leurs docs ; archives métier lourdes
  retirées. Le starter d'email a été relocalisé de `welcome-forge` vers le
  parcours `welcome-mail` (`mail-welcome`).

### Slugs canoniques (feature phare)

- **Type de slug canonique** (`core/http/slug.py`) : `slugify` déterministe,
  `is_valid_slug` (contrat de validation unique), génération depuis une colonne
  `source`. Une seule façon officielle de produire un slug (principe 11).
- **SQL/CRUD auto-généré** prenant en charge le slug (colonne, index unique,
  lookup `get_<entité>_by_slug`) et **routing public par slug**.
- **Documentation** dédiée et **une application réelle construite avec** (Phase
  dogfood) pour valider le parcours de bout en bout.

### Forge Video — nouvel opt-in `forge-mvc-video`

- Opt-in **`forge-mvc-video`** (**Beta**) : chaîne complète upload → traitement
  → lecture. Stockage uuid-based, extraction de métadonnées (`ffprobe`),
  **transcodage MP4 (H.264/AAC)**, génération de poster, **lecture en streaming
  HTTP Range**.
- Commandes CLI : `video:doctor` (diagnostic), `video:init` (migration `videos`),
  **`video:upload <fichier> [--title]`** (entrée d'upload officielle),
  `video:process` (worker de transcodage), **`video:cleanup`** (purge des vidéos
  `failed` / fichiers orphelins, dry-run par défaut, anti-traversal).
- FFmpeg/ffprobe traités comme **binaires système** (pas de dépendance pip) ;
  le module se branche sans eux (mode serveur de médias), `video:doctor`
  signale leur absence. Publié sur PyPI avec les autres distributions.

### Dégraissage du core vers des opt-ins

- **`forge-mvc-pivot`** (ADR-021, `PIVOT-EXTRACT-001`) : le service « pivot
  advanced » (associations `many_to_many` enrichies) et le générateur
  `make:pivot-crud` sont extraits du core vers un opt-in dédié.
- **`forge-mvc-mail`** (ADR-022, `MAIL-EXTRACT-001`) : l'email (composition,
  transports interchangeables, templates Jinja, CLI `mail:*`) est extrait du
  core vers un opt-in, accompagné de son parcours `welcome-mail`.
- **Réorganisation de la racine de `core/`** (`CORE-REORG-001`) : regroupement
  en sous-paquets `core/app/` (application, factory WSGI, dev-server,
  prod-warnings) et `core/errors/` (gestion des erreurs runtime) ; `slug`
  rejoint `core/http/`. Racine réduite à `forge.py` + `__init__.py`, sans
  changement de comportement (entrée Gunicorn : `core.app.wsgi:create_configured_wsgi_app`).

### Robustesse & production

- **`forge run` survit aux crashes** de l'application (relance automatique +
  garde anti-boucle après crashes rapides répétés).
- Sécurité uploads : vérification du **contenu réel des images** avant écriture.
- Sécurité uploads : **plafond anti-décompression-bomb** sur les images
  (`upload_max_image_pixels`, défaut 24 Mpx) — la surface est contrôlée dès
  l'en-tête, avant décodage/écriture, et `DecompressionBombError` est désormais
  capturé proprement à la génération des variantes (SEC-UPLOAD-DECOMPRESSION-BOMB-001).
- **Production-readiness** : `forge doctor` durci, `forge migration:apply
  --dry-run`, endpoint de *health*, `forge update` robuste, et **checklist de
  déploiement** documentée.
- **Dogfood MariaDB** : parcours réel exécuté sur MariaDB (go/no-go de clôture)
  validant slugs + CRUD généré.

### Packaging & documentation

- **Dépendance `forge-mvc` des opt-ins unifiée** à `>=1.0.0b13,<2` sur les
  onze opt-ins (fin de la cohabitation `==1.0.0b13` / `>=1.0.0b5` — une seule
  politique de borne, principe 11).
- `requirements-dev.txt` installe désormais **`forge-mvc-video` en éditable** :
  sa suite de tests n'est plus silencieusement skippée (`importorskip`) en CI.
- `tools/release-validate.sh` : correction d'un bug `set -e` qui masquait
  silencieusement un échec d'audit ; l'audit `pip-audit` des dépendances de dev
  distingue désormais une **vulnérabilité** (bloquante) d'une **résolution
  impossible avant publication** (œuf-poule, non bloquante) ; nouveau mode
  opt-in **`--with-packages`** qui build les 12 distributions + `twine check` en
  local (RELEASE-VALIDATE-PACKAGES-001).
- Documentation du contrat CLI : `forge migration:apply --dry-run` documenté
  dans l'aide intégrée et `docs/reference/cli-commands.md`
  (DOCS-MIGRATION-DRY-RUN-001).
- Cadrage Alpha de `forge-mvc-iot` (installation séparée, exclu de
  `forge-mvc[all]`).
- Distribution : exclusion des tests du sdist, exclusion du bytecode des
  artefacts ; build CI étendu à `forge-mvc-iot` et `forge-mvc-video`.
- `BETA13-CLOSING-AUDIT-001` **vert**, versions bumpées **b13** sur le core et
  les onze opt-ins.
- Réorganisation de la documentation (`docs/guide/`, `features/`,
  `philosophy/`, `reference/`, `release/`, `deployment/`), index des ADR,
  URLs harmonisées vers `forgemvc.com`.


## [1.0.0-beta.12] — 2026-05-29

### Forge IoT — nouveau module opt-in `forge-mvc-iot`

- Module IoT opt-in complet : contrat MQTT `forge/{site}/{device_id}/telemetry`,
  subscriber `paho-mqtt`, stockage `iot_events` (migration packagée,
  repository), et API HTTP JSON en lecture
  (`/api/iot/events`, `/api/iot/events/{site}/{device_id}`,
  `/api/iot/devices/{site}/{device_id}/count`).
- CLI : `forge iot:doctor` (diagnostic statique ; `--db` table + schéma,
  `--mqtt` broker), `forge iot:init` (copie la migration), `forge iot:listen`
  (écoute + insère, arrêt propre + résumé), `forge iot:simulate`
  (mesures factices ; profils `temperature`/`humidity`/`presence`/`energy`).
- Sécurité : **TLS MQTT** (`FORGE_IOT_MQTT_TLS_ENABLED`,
  `FORGE_IOT_MQTT_TLS_CA_FILE`) branché dans les clients ; **Bearer token**
  optionnel sur l'API HTTP (`FORGE_IOT_API_TOKEN`).
- Pédagogie : guides Mosquitto local, smoke test local, Bac Pro / BTS CIEL,
  exemple ESP32, évaluation Arduino R4 ; starter `welcome-iot`.
- `forge-mvc-iot` publié sur PyPI (statut Alpha) au même titre que les
  autres opt-ins.

### Opt-ins côté projet utilisateur — structure `optins/`

- Convention `optins/` : couche de branchement local explicite des opt-ins
  (registre `optins/registry.py`, pas de découverte automatique) ; les
  paquets restent distribués dans `packages/forge-mvc-*`.
- `forge optin:enable iot` (dry-run par défaut, `--apply` ; branche
  prudemment `mvc/routes.py` si la structure est reconnue) et
  `forge optin:list` (lecture seule, états absent/partiel/activé).
- Le starter `welcome-iot` génère cette structure `optins/iot/`.

### Qualité

- Référence CLI complétée (commandes IoT + opt-ins).
- Suite de tests complète revenue à **0 échec** avant release
  (corrections de garde-fous méta et de références de doc obsolètes,
  sans affaiblir les garde-fous).


## [1.0.0-beta.11] — 2026-05-27

### Expérience développeur — point d'entrée unifié et inspectabilité

- `forge run` officialise le point d'entrée du serveur de développement
  (FORGE-RUN-COMMAND-001) — refus du serveur intégré en `APP_ENV=prod`
  avec message WSGI clair, délégation à `scripts/dev-server.sh` ou
  `python app.py` en `dev`.
- Superviseur d'autoreload `forge_cli.dev_reloader`
  (DEV-SERVER-AUTORELOAD-001) — polling `stat()` sur `app.py`,
  `config.py`, `env/dev`, `mvc/**/*.{py,html,json,sql}`, `core/**/*.py`,
  stdlib uniquement. Désactivable via `--no-reload`.
- Convention d'inspection des classes API publiques
  (API-INSPECTABLE-OBJECTS-CONVENTION-001) — `Request` et `Response`
  exposent `.data` avec masquage automatique
  (Authorization/Cookie/password/csrf/token/api_key/secret) ; helpers
  `text/html/json/debug` côté `Response` ; convention documentée dans
  `docs/reference/http.md`.
- Squelettes générés typés (DX-TYPED-SKELETONS-001) — imports
  `Request`/`Response` automatiques et annotations
  `def action(request: Request) -> Response:` sur toutes les actions
  publiques du starter `welcome`, des générateurs `make:crud`,
  `make:public-*` et des 6 starters officiels.
- Erreur développeur claire quand `BaseController.render(...)` cible une
  vue inexistante (DX-RENDER-ERROR-001) — `TemplateNotFoundError`
  pédagogique en `dev`, réponse minimale en `prod`, aucun stacktrace.
- Rendu HTML pédagogique pour `Response.debug(obj)`
  (DX-DEBUG-DUMP-HTML-001) — `core.http.debug_dumper` (masquage des clés
  sensibles, profondeur bornée, détection des cycles) ; comportement
  prod inchangé (404 minimal, aucune fuite).

### Starter d'entrée — Bonjour Forge

- Refonte pédagogique du starter `welcome` (STARTER-BONJOUR-FORGE-001) —
  alias `bonjour` / `bonjour-forge` / `bienvenue` / `7`. Progression :
  `index` retourne `Response.text("Bonjour Forge")`, puis
  `/welcome/greet?name=…` (`request.param(...)`),
  `/welcome/inspect` (`Response.debug(request.data)`), enfin
  `/welcome/cycle` introduit `BaseController.render(...)`. Vue
  `welcome/index.html` retirée.

### Documentation, installation et landing

- Clôture documentaire « Bonjour Forge » (DX-DOCS-BONJOUR-FORGE-CLOSE-001)
  — renommage `docs/15-minutes.md` → `docs/bonjour-forge.md`, refonte
  autour du parcours développeur livré.
- Guide officiel d'installation Windows + WSL (INSTALL-WSL-DOCS-001 +
  INSTALL-WSL-DOCS-FIELD-FIX-001) — `docs/install/windows-wsl.md`,
  parcours WSL Ubuntu 24.04 + VS Code Remote WSL + pipx + Node 20 +
  MariaDB avec compte `forge_admin@localhost` dédié.
- Section « Installer Forge selon votre usage » de la landing
  (LANDING-INSTALL-CARDS-001) — 4 cards homogènes
  (`windows-wsl`, `pipx-user`, `core-dev`, `production`).
- Consolidation `docs/install/core-dev.md`
  (INSTALL-CORE-DEV-DOCS-AUDIT-001) — 9 sections couvrant l'installation
  éditable, les 5 validations canoniques avant commit, Tailwind, opt-ins.
- Réorganisation `docs/install/` (INSTALL-DOCS-STRUCTURE-001) —
  `git mv` des 7 pages d'installation sous `docs/install/{index,pipx,
  core-dev,mariadb,vm-debian,windows,github,production}.md`, mise à jour
  des liens internes et de la nav MkDocs.
- Réalignement de la landing canonique sur son contrat public actuel
  (LANDING-PUBLIC-CONTRACT-REALIGN-001) — décisions de suppression
  assumées (5e card Installation, FAQ, Stack technos, compteur tests) ;
  tests landing réalignés.

### Audit

- `BETA11-POST-DOCS-CONSOLIDATION-AUDIT-001` — audit de l'état réel
  après tous les tickets DX/docs/install/landing ; décision OK pour
  lancer `BETA11-DX-CLOSING-AUDIT-001`.
- `BETA11-DX-CLOSING-AUDIT-001` — découpe et commit du WIP en
  5 commits cohérents, suite complète à 15 051 tests passants
  (6 skipped), décision GO pour `RELEASE-BETA11-001`.
- `RELEASE-BETA11-001` (ce ticket) — bump version `1.0.0b10` →
  `1.0.0b11`, validations release, build distributions, twine check,
  tag SemVer `v1.0.0-beta.11`.

### Notes

- Forge core reste autonome ; les opt-ins (`forge-mvc-rbac`,
  `forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-mfa`,
  `forge-mvc-media`) restent indépendants.
- La production publique reste WSGI + Gunicorn + reverse proxy.
  `forge run` reste explicitement un outil de développement.


## [1.0.0-beta.10] — 2026-05-25

### Stabilisation B10

- Alignement des tests de durcissement session avec le contrat courant `first_name` / `last_name` + alias legacy `prenom` / `nom`.
- Validation release robuste SemVer ↔ PEP 440 (`tools/release-validate.sh` : mode `--convert`, validation explicite des deux formes en entrée).
- Validation release indépendante du `PATH` : interpréteur Python explicite via `PYTHON_BIN="${PYTHON:-python3}"`, modules invoqués par `python -m <module>`.
- Statut PyPI des opt-ins officiel aligné dans la documentation (5 opt-ins publiés depuis beta.9).
- Headers de sécurité appliqués aussi au chemin WSGI (helper partagé `core/security/headers.py`, HSTS conditionné à `wsgi.url_scheme == "https"`).
- Tests opt-in protégés par `pytest.importorskip(...)` pour les environnements core-only.
- Workflow GitHub Pages passé en `mkdocs build --strict`.
- Audits dépendances (`pip-audit`, `npm audit`) bloquants en validation release ; workflow informatif distinct conservé.
- Défense symlinks uploads/statics verrouillée par tests (`realpath` + `commonpath` + 3 garde-fous source-level sur `app.py`).
- Validation explicite de `FORGE_MFA_SECRET_KEY` au boot côté opt-in MFA (refus des placeholders : `change-me`, `default`, `dev`, etc.).
- Garde `python app.py` contre exposition publique en production (`APP_ENV=prod` + `APP_HOST` ∈ `{0.0.0.0, ::, [::]}` → refus de démarrer).
- Référence CLI restructurée avec parcours rapides + index alphabétique de 63 commandes.
- Imports documentaires validés par tests méta AST (378 tests, 0 import framework invalide).
- Audit fixtures `autouse=True` et correction d'isolation `tests/test_templating.py::_setup`.
- Landing : section contact statique `mailto:forgemvc@gmail.com` (pas de route `/contact`, pas de `ContactController`) ; identité publique alignée sur Roger Lequette / forgemvc@gmail.com.
- Politique `docs/` source canonique vs `site/` artefact MkDocs documentée + verrouillée par tests méta.
- Politique `DB_ADMIN_*` réservée au provisioning CLI documentée ; runtime applicatif sur `DB_APP_*` uniquement ; protection `env/*.local` dans `.gitignore`.
- Roadmap B10 consolidée en 5 sections (Bloquants / Critiques / Durcissement / Cohérence release / Clôture), compteurs fragiles retirés, audit pré-release validé `GO`.
- Convention de tag Git alignée : SemVer publique (`v1.0.0-beta.10`), jamais PEP 440 (`v1.0.0b10`).

### Sécurité

- 0 vulnérabilité détectée par `pip-audit` (runtime + dev) et `npm audit --omit=dev`.
- Renforcement WSGI (headers partagés app.py/WSGI), MFA (validation clé Fernet au boot), uploads/statics (défense symlinks vérifiée), `app.py` prod guard, release validation (Python explicite, audits bloquants).

### Notes

- Forge core reste autonome.
- Les opt-ins (`forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-mfa`, `forge-mvc-media`) restent optionnels et publiés séparément sur PyPI.
- La production publique reste recommandée via WSGI + Gunicorn + reverse proxy. `python app.py` reste un serveur de développement.


## [1.0.0-beta.9] — 2026-05-24

### Added / Changed

- Phase B9 close — release de consolidation production encadrée.
- CLI: `--help`/`-h` interceptés au dispatcher avant exécution métier (12 tickets `CLI-HELP-FLAGS-*`, série close).
- WSGI: `core.app.wsgi.create_configured_wsgi_app()` — factory configurée partagée avec `app.py` via `core.app.app_factory.build_application()`.
- WSGI: warnings production émis à la construction de l'application (`MemorySessionStore` en `APP_ENV=prod`).
- HTTP: `APP_TRUSTED_PROXIES` + `resolve_client_ip()` — `X-Real-IP` honoré uniquement derrière proxy fiable, validation `ipaddress`.
- Sessions: helpers centralisés `core.security.cookies.set_session_cookie()` / `clear_session_cookie()`, migration des contrôleurs Auth et MFA.
- Sessions: `MemorySessionStore.cleanup_expired()` aligné sur File/MariaDb, retourne `int`.
- Sessions: dédomainisation `_normalize_legacy_user()` — `first_name`/`last_name` canoniques (alias FR conservés temporairement).
- Sécurité: `core/security/api_auth.py` utilise `hmac.compare_digest` (comparaison constant-time du token Bearer).
- Sécurité MFA: dépendance `cryptography>=46.0.7,<47` (sortie de la plage vulnérable `>=42,<46`).
- CI: `forge-mvc-media` ajouté à la matrice de build des opt-ins.
- Documentation: nouvelles pages [Déploiement WSGI minimal](wsgi-deployment.md) et [Limites de production](production-limits.md).
- Landing: nav enrichie (`CRUD` + `API`), section Aperçu beta.9, section API à 6 cartes, formule de continuité.

### Packaging

- Tous les packages alignés en `1.0.0b9`.
- `package.json` et `package-lock.json` alignés en `1.0.0-beta.9` (garde-fou méta verrouille la cohérence).
- Pas de changement de dépendance runtime côté core.
- Aucun upload PyPI effectué dans cette release de préparation.

### Security

- `X-Real-IP` ne peut plus être falsifié par un client direct (proxy fiable obligatoire).
- Token API Bearer comparé en temps constant.
- `cryptography` MFA hors zone vulnérable.

## [1.0.0-beta.8] — 2026-05-22

### Added / Changed

- Requalification de `forge-mvc-media` en Alpha.
- Requalification de `forge-mvc-mfa` en Alpha.
- Chiffrement des secrets TOTP MFA au repos via Fernet.
- Documentation opt-ins alignée.
- Préparation des packages `media` et `mfa` pour publication future.

### Security

- Les secrets TOTP MFA ne sont plus stockés en clair.
- `FORGE_MFA_SECRET_KEY` devient obligatoire pour le module MFA.

### Packaging

- Tous les packages sont alignés en `1.0.0b8`.
- Aucun upload PyPI effectué dans cette release de préparation.

## [1.0.0-beta.7] — 2026-05-22

Release documentation pédagogique — Premier pas refondu, logo MkDocs, cycles MVC visuels.

- refonte pédagogique du starter Welcome : diagrammes ASCII, cycles HTML/JSON Mermaid, tables route→concept (DOC-PREMIER-PAS-PEDAGOGY-001) ;
- agrandissement logo MkDocs via CSS dédié (DOCS-NAV-LOGO-SIZE-001) ;
- vues du starter visibles par défaut : `<details open>` (DOC-PREMIER-PAS-CODE-VISIBLE-001) ;
- onglets Cycle HTML/JSON remplacés par diagrammes Mermaid + admonitions (DOC-PREMIER-PAS-CYCLES-TABS-VISUAL-001) ;
- nettoyage final documentation Premier pas (DOC-PREMIER-PAS-FINAL-CLEANUP-001).

Non publié dans cette release :

- `forge-mvc-media`, encore source-only ;
- `forge-mvc-mfa`, encore Pre-Alpha (SEC-MFA-SECRET-ENCRYPTION-001) ;
- packages opt-ins `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats` : publication prévue dans PYPI-OPTINS-001.


## [1.0.0-beta.6] — 2026-05-21

Release post-corrections terrain — RBAC contractuel, Pivot advanced, DX, test terrain et corrections.

- JSON Schema contractuel pour entités, relations, RBAC, pivot (ENTITY-CONTRACT-*) ;
- RBAC déclaratif opt-in : rbac:validate, rbac:audit, make:crud intégration (RBAC-*) ;
- Pivot advanced : PivotAdvancedService, contraintes, erreurs UX (PIVOT-ADVANCED-*) ;
- make:pivot-crud : générateur opt-in de sous-CRUD pivot (PIVOT-CRUD-*) ;
- test terrain FIELD-TEST-APP-001 : flux complet validé ;
- correction F-001 : clé canonique `"name"` documentée clairement (FIELD-FIX-001) ;
- correction F-002 : structure `mvc/entities/<nom>/<nom>.json` documentée (FIELD-FIX-001) ;
- correction F-003 : garde make:crud limité au côté source de la relation (FIELD-FIX-M2M-GUARD-001) ;
- audit post-corrections terrain validé (RELEASE-AUDIT-002).

Non publié dans cette release :

- `forge-mvc-media`, encore source-only ;
- `forge-mvc-mfa`, encore Pre-Alpha (SEC-MFA-SECRET-ENCRYPTION-001) ;
- packages opt-ins `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats` : publication prévue dans PYPI-OPTINS-001.


## [1.0.0-beta.5] — 2026-05-17

Release de consolidation de la Phase 12 — Sécurité, résilience et préparation PyPI opt-ins.

- audit auth : logger best-effort et résilience documentée (AUTH-AUDIT-LOGGER-RESILIENCE-001) ;
- contrat des en-têtes de sécurité documenté et verrouillé (SECURITY-HEADERS-DOC-LOCK-001) ;
- audit des noms PyPI des opt-ins réalisé (OPTIN-PYPI-NAMES-CHECK-001) ;
- préparation locale des opt-ins publiables (OPTIN-PYPI-PUBLISH-PREPARE-001) ;
- extras optionnels `rbac`, `workflow`, `stats` et `all` synchronisés (VERSION-SYNC-OPTIN-EXTRAS-001) ;
- publication groupée du core et des opt-ins publiables `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`.

Non publié dans cette release :

- `forge-mvc-media`, encore source-only après extraction Phase 11 ;
- `forge-mvc-mfa`, encore Pre-Alpha, bloqué par `SEC-MFA-SECRET-ENCRYPTION-001`.


## [1.0.0-beta.4] — 2026-05-17

Release de consolidation des phases 7 à 10.

- clarification du périmètre audit/auth/MFA/RBAC ;
- warning `forge doctor` pour MFA opt-in manquant ;
- politique de stockage des secrets MFA documentée ;
- politique de publication des opt-ins documentée ;
- tests méta réorganisés, politique de rotation définie, prune prudent appliqué ;
- règle behavior-first documentée ;
- audit des doublons d'API publique réalisé ;
- langage des starters normalisé côté Python / SQL ;
- conventions de langage des starters documentées ;
- surface publique de `BaseController` auditée et documentée.


## [1.0.0-beta.3] — 2026-05-16

Corrections post-audit Phase 2 — sécurité CSRF, routes modules explicites.

### Sécurité

- `tests/meta/test_security_meta_no_csrf_inequality_001.py` : garde-fou méta
  empêchant toute comparaison naïve de tokens CSRF (`==` ou `!=`) dans les
  fichiers canoniques de sécurité (ticket SECURITY-META-NO-CSRF-INEQUALITY-001).

### Modules

- `core/modules/routes.py` : suppression du mécanisme d'injection automatique
  de routes (`prepare_module_route_injection`, `ModuleRouteInjectionResult`,
  `ModuleRoutesAlreadyInjectedError`, `_build_injection_block`, `_module_marker`).
  `generate_module_routes()` reste le seul mécanisme — explicite
  (ticket MODULE-ROUTES-INJECTION-REMOVE-001).
- `docs/module-author-guide.md`, `docs/reference/modules.md` : documentation
  du contrat explicite de branchement de routes de modules
  (ticket MODULE-ROUTES-EXPLICIT-DOC-001).

### Métriques

- Tests : 9 909 passed, 3 skipped (suite complète validée)


## [1.0.0-beta.2] — 2026-05-16

Corrections post-audit Phase 1 et infrastructure release Phase 2.

### Documentation

- `README.md` : retrait de `pyotp` de la liste des dépendances runtime du core
  (ticket README-RUNTIME-DEPS-CLEANUP-001) — PyOTP est une dépendance de `forge-mvc-mfa`,
  pas du core.
- `docs/contributing.md` : même correction sur la liste des dépendances runtime.
- `docs/release-policy.md` : alignement du classifier PyPI `forge-mvc` sur
  `4 - Beta` (ticket PYPI-CLASSIFIER-BETA-ALIGN-001) ; ajout section
  « Verrouillage packaging » (ticket PACKAGE-LOCK-DOC-001).
- `docs/release-local.md` : section « Environnement de validation release »
  documentant la procédure reproductible (ticket RELEASE-VALIDATION-ENV-LOCK-001).
- `docs/positioning.md` : mention de version mise à jour.

### Infrastructure

- `scripts/release_check.sh` : nouveau script de validation release locale
  (ticket RELEASE-CHECK-SCRIPT-001). Mode standard (pytest, compileall, mkdocs
  --strict, git diff --check, git status) et mode `--full` (+ build wheel +
  twine check). Ne publie rien, ne crée aucun tag.

### Packaging

- `pyproject.toml` : classifier `Development Status :: 5 - Production/Stable`
  corrigé en `4 - Beta` (ticket PYPI-CLASSIFIER-BETA-ALIGN-001).


## [1.0.0-beta.1] — 2026-05-15

Première publication publique du code source de Forge et publication sur PyPI.

### Infrastructure PyPI

- Publication PyPI réalisée : `forge-mvc==1.0.0b1` disponible sur [PyPI](https://pypi.org/project/forge-mvc/1.0.0b1/).
- TestPyPI validé avant PyPI — artefacts `twine check` PASSED.
- Installation pip validée : `python -m pip install --pre forge-mvc`.
- Installation pipx validée : `pipx install --pip-args="--pre" forge-mvc`.
- `--pre` est nécessaire car `1.0.0b1` est une préversion bêta PEP 440.
- Extras `[rbac]`, `[workflow]`, `[stats]`, `[all]`, `[mfa]` non publiés — modules opt-in en mode source-only via GitHub (`OPTIN-PYPI-PUBLISH-001`).

### Documentation

- `docs/installation-pipx.md` : note sur l'état de publication des opt-in.
- `docs/installation.md` : section « Modèle de packages » mise à jour.
- `docs/release-policy.md` : table de publication PyPI par package ajoutée.
- `packages/forge-mvc-mfa/README.md` : instructions d'install alignées sur
  le mode source-only (extras PyPI temporairement indisponibles).

### Métriques

- Tests : 9685 passed, 3 skipped (suite complète validée)

---

> **Historique de développement pré-publication.** Les sections ci-dessous
> documentent l'historique des itérations de consolidation interne de Forge
> avant sa première publication publique (1.0.0-beta.1). Elles sont conservées
> à titre de référence. La version publique actuelle est **Forge 1.0.0-beta.1**.

## [3.0.5] — 2026-05-14

Articles de la landing page rendus cliquables (lien vers la doc correspondante).
Aucune rupture d'API publique. Aucune nouvelle fonctionnalité framework.

### Frontend

- `LANDING-ARTICLES-CLICKABLE-001` : 21 articles de la landing page wrappés dans
  `<a href="...">` pointant vers la page de documentation correspondante. Effet
  `group-hover:` sur le titre et la bordure de la carte.

### Tests

- `LANDING-ARTICLES-CLICKABLE-001` : nouveau garde-fou `test_landing_articles_clickable_001.py`
  (22 tests : 21 articles wrappés, hrefs vers docs existantes, cursor-pointer, group-hover h3).

### Métriques

- Tests : 9670 (3.0.4) → 9693 (3.0.5)
- Garde-fous méta : +1 nouveau

## [3.0.4] — 2026-05-14

Consolidation post-audit ChatGPT 3.0.3 (mini-Scénario D, 4 tickets). Aucune
rupture d'API publique. Aucune nouvelle fonctionnalité.

### Documentation

- `ROADMAP-3.0.3-CURRENT-STATE-001` : roadmap reflète l'état courant (3.0.4),
  Scénario D ajouté avec les 4 tickets ciblés.
- `PYTEST-CORE-ONLY-CONTRACT-CLARIFY-001` : CHARTE_DOC.md section 7 réécrite avec
  3 environnements nommés (A. Runtime core-only, B. Test core-only, C. Test complet).
- `DEV-INSTALL-CONTRACT-FIX-001` : ordre canonique `pip install -e .` avant
  `requirements-dev.txt` aligné dans installation.md, installation-github.md,
  README.md et CONTRIBUTING.md. Section « modules PyPI » du README corrigée
  (mode source-only).

### Tests

- `RELEASE-TESTS-CURRENT-VERSION-001` : tests de release version-agnostiques
  (lisent pyproject.toml, plus de version hardcodée). `test_release_3_0_0_stable_001`
  et `test_release_3_0_2_patch_stable_001` remplacés par
  `test_release_current_version_001`. `test_roadmap_3_0_consistency_001` rendu
  dynamique.
- `DEV-INSTALL-CONTRACT-FIX-001` : nouveau garde-fou `test_install_contract_001.py`.
- `PYTEST-CORE-ONLY-CONTRACT-CLARIFY-001` : nouveau garde-fou
  `test_pytest_core_only_contract_clarified_001.py`.

### Métriques

- Tests : 9663 (3.0.3) → 9670 (3.0.4)
- Garde-fous méta : +3 nouveaux, 2 anciens supprimés (remplacés)

## [3.0.3] — 2026-05-14

Consolidation post-audit renforcé (11 tickets de qualité). Aucune rupture
d'API publique. Aucune nouvelle fonctionnalité.

### Documentation

- `DOCS-AUTH-RBAC-IMPORTS-001` : 6 imports MFA/RBAC corrigés dans auth.md
  et rbac.md (ImportError à la copie-colle)
- `DOCS-REFERENCE-API-SYMBOLS-001` : 10+ symboles français alignés sur le
  code anglais réel dans reference/api.md
- `DOCS-VERSION-VARIABLE-001` : hook mkdocs lit pyproject.toml ; 20+ fichiers
  passés à `{{forge_version}}`, `{{forge_tag}}`, `{{python_min}}`
- `DOCS-COMPAT-OPTIONAL-DEPS-001` : pyotp clarifié comme dépendance d'extra
  `[mfa]`, retirée du tableau runtime
- `PACKAGES-OPTIN-INSTALL-001` : 11 mentions install corrigées vers le mode
  source-only, 4 packages opt-in marqués `Private :: Do Not Upload`
- `ROADMAP-ANCHOR-FIX-001` : ancre cassée corrigée dans la roadmap
- `CLI-HELP-HIDDEN-COMMANDS-001` : 8 commandes CLI sorties de l'ombre

### Tests et garde-fous (7 nouveaux tests méta)

- `DOCS-SYMBOL-VALIDATION-001` : vérifie que chaque bloc python de la doc
  s'importe vraiment (révélation : 4 imports doc cassés supplémentaires)
- `PYTEST-DEFAULT-ENV-CONTRACT-001` : contrat charte 'pytest en core-only'
  restauré, 28 fichiers reçoivent pytest.importorskip
- `PYTEST-CORE-ONLY-DEPS-EXTRAS-001` : extension aux deps d'extras (pyotp),
  9 fichiers réorganisés, validation en venv core-only : 8394 passed, 0 errors
- `PACKAGING-CLASSIFIER-STABLE-001` : forge-mvc core passe
  `5 - Production/Stable`

### Métriques

- Tests : 9628 (3.0.2) → 9678 (3.0.3)
- Garde-fous méta : +7 nouveaux tests
- Imports doc cassés : 16+ → 0 (vérifié par garde-fou)
- Mentions versions obsolètes : 20+ fichiers → 0 (variabilisé)
- Commandes CLI cachées : 8 → 0 (vérifié par garde-fou)
- `pytest` en core-only : 30 errors → 0

## [3.0.2] — 2026-05-13

Scénario C — consolidation production-ready (12 tickets livrés, série en cours).

### Stabilisé — Packaging et distribution

- `PACKAGING-SRC-LAYOUT-001` (T2) : migration vers une structure `src/` pour
  l'isolation des packages. `forge-mvc` et les 4 modules utilisent désormais
  `packages/<dist>/src/` comme root — évite les imports parasites depuis la
  racine lors des builds.
  Garde-fou : `tests/meta/test_packaging_src_layout_001.py`.

- `PACKAGING-WHEEL-CONTENT-001` (T2b) : vérification du contenu des 5 wheels
  post-restructuration. Chaque wheel déclaré dans `packages/` contient exactement
  les modules attendus — aucun fichier de développement ou test embarqué.
  Garde-fou : `tests/meta/test_wheel_content_001.py`.

### Stabilisé — Tests et reproductibilité

- `PYTEST-REPRODUCIBLE-001` (T1) : `pyproject.toml` fixe `addopts = "--tb=short"`
  et seed aléatoire stable pour garantir un ordre de collecte pytest reproductible
  entre machines. Garde-fou : `tests/meta/test_pytest_reproducible_001.py`.

### Stabilisé — MFA

- `MFA-SECRET-HASH-DEPRECATION-RESOLVE-001` (T4) : retrait définitif de la propriété
  dépréciée `AuthMfaFactor.secret_hash` (introduite en SEC-MFA-SECRET-NAMING-001).
  `totp_secret` est désormais le seul accès. Aucun consommateur interne trouvé.
  Garde-fou : `tests/meta/test_mfa_secret_hash_remove_001.py`.

- `MFA-PRODUCTION-DECISION-001` (T3) : décision documentée — `forge-mvc-mfa` reste
  en **Pre-Alpha** pour Forge 3.x. La production requiert un audit tiers (secret TOTP
  stocké en clair, absence de chiffrement au repos). Section "Limites MFA Production"
  ajoutée à `docs/stability-contract.md`.
  Garde-fou : `tests/meta/test_mfa_production_decision_001.py`.

### Stabilisé — OIDC et RBAC

- `OIDC-EXCEPTIONS-CLEANUP-001` (T15) : retrait des constantes `AUTH_EVENT_OIDC_*`
  (6 constantes) de `core.auth.exceptions` — vestiges post-ADR-004. Plus aucun code
  productif OIDC dans le core.
  Garde-fou : `tests/meta/test_oidc_exceptions_cleanup_001.py`.

- `CORE-RBAC-PLUGIN-MECHANISM-001` (T14) : mécanisme de plugin Jinja —
  `register_jinja_context_provider(provider_fn)` dans `core.mvc.controller`.
  Permet aux modules opt-in d'injecter du contexte Jinja sans que le core ne les
  nomme. Respecte ADR-004 (périmètre core strict) et le principe 8 (noyau minimal).
  Garde-fou : `tests/meta/test_core_rbac_plugin_mechanism_001.py`.

### Documentation — Cohérence série 3.x

- `DOCS-3.0.1-VERSION-SWEEP-001` (T7) : balayage de toutes les mentions de version
  dans la documentation. Références `2.x` et `3.0.0` non pertinentes remplacées par
  `3.0.1` ou `3.x` selon le contexte.
  Garde-fou : `tests/meta/test_docs_no_stale_versions_001.py`.

- `STABILITY-CONTRACT-3.0-REFRESH-001` (T8) : refonte de `docs/stability-contract.md`
  — titre et garanties actifs alignés sur la série 3.x. Ajout sections modules opt-in
  (RBAC Beta, Workflow Beta, Stats Beta, MFA Pre-Alpha) et mécanisme
  `register_jinja_context_provider`.
  Garde-fou : `tests/meta/test_stability_contract_3_x_001.py`.

- `CLAUDE-MD-3.0.2-REFRESH-001` (T9) : `CLAUDE.md` mis à jour de Forge 2.10.0 →
  Forge 3.0.2. Série 3.x explicite, note `packages/` reformulée pour refléter l'état
  post-T2/T2b, section 10 refondue.
  Garde-fou : `tests/meta/test_claude_md_3_0_2_001.py`.

- `SESSION-KEYS-DOCSTRING-001` (T19) : docstring `core/sessions/keys.py` corrigé —
  "avant Forge 3.1" → "avant Forge 3.0.1". La version de livraison de la migration
  FR→EN était incorrecte. Garde-fou : `tests/meta/test_session_keys_docstring_001.py`.

- `ADR-TITLES-3.0-REFRESH-001` (T17) : décision documentée de conserver les titres
  ADR-001 ("Forge 2.x") et ADR-002 ("Forge 2.x") — ces ADR sont des archives
  historiques, pas des documents actifs (Principe 11 — archives datées). Garde-fou
  de cohérence titre ↔ warning historique ajouté.
  Garde-fou : `tests/meta/test_adr_historical_warnings_001.py`.

## [3.0.1] — 2026-05-12

Phase G — consolidation pré-publication (15 tickets livrés).

### Stabilisé — Sessions

- `SESSIONS-LANG-ALIGN-001` (G1) : migration FR→EN des clés de session internes
  (`authentifie` → `authenticated`, `utilisateur` → `user`). Fallback de lecture
  sur les anciennes clés pour les sessions existantes. Les clés legacy seront
  retirées en Forge 4.0. Garde-fou : `tests/meta/test_sessions_lang_align_001.py`.

- `SESSION-LIMITS-STATUS-AUDIT-001` : audit et documentation des limites du
  `MemorySessionStore` en production (pas de persistence entre redémarrages, pas
  de partage multi-processus). Clarification du statut "développement/test uniquement"
  dans `docs/reference/sessions.md`.

### Stabilisé — CLI et packaging

- `CLI-AUTH-INIT-OIDC-SQL-001` (G8) : retrait des instructions SQL OIDC
  (`auth_oidc_accounts.sql`, `auth_oidc_identities.sql`) de la commande
  `forge auth:init`. Cohérence avec ADR-004 (OIDC supprimé du core).
  Garde-fou : `tests/meta/test_cli_auth_init_oidc_sql_001.py`.

- `PACKAGING-FORGE-MODULE-001` (G6) : restructuration de `forge.py` (module
  racine plat) vers un package `forge/`. Prépare l'installation pip fiable —
  `forge.py` causait des problèmes en mode édition (`pip install -e .`).
  Garde-fou : `tests/meta/test_packaging_forge_module_001.py`.

### Décision documentée

- `AUTH-EXTRA-EXTRACT-DECISION-001` (G2) : décision documentée sur l'extraction
  `auth_extra` — les helpers avancés (reset mot de passe, invitations) restent dans
  `core/auth/` pour Forge 3.x. L'extraction est déférée à Forge 4.0.
  Garde-fou : `tests/meta/test_auth_extra_extract_decision_001.py`.

### Documentation

- `DOCS-V1-V2-TERMINOLOGY-001` (G4) : nettoyage des références terminologiques
  v1/v2 dans la documentation. Mentions "Forge 1.x" actives remplacées par "Forge 3.x"
  dans les guides courants. Garde-fou : `tests/meta/test_docs_v1_v2_terminology_001.py`.

- `DOCS-GETTING-STARTED-CONSOLIDATE-001` (G5) : consolidation des parcours
  getting-started — doublons supprimés, exemples alignés sur Forge 3.0.
  Garde-fou : `tests/meta/test_docs_getting_started_consolidate_001.py`.

- `DOCS-RELEASE-SECTION-AUDIT-001` (G3) : audit de la section release —
  `docs/release.md` enrichi de la procédure de release 3.x, checklist PyPI
  multi-distributions mise à jour.
  Garde-fou : `tests/meta/test_docs_release_section_audit_001.py`.

- `STARTER-AUTH-MFA-PROFILE-001` (G7) : page profil MFA ajoutée au starter
  `utilisateurs-auth` — activation TOTP, codes de récupération, désactivation
  MFA depuis le profil. Garde-fou : `tests/meta/test_starter_auth_mfa_profile_001.py`.

### Correctifs documentation pré-publication (PR1–PR5)

- `DOCS-CLI-COMMANDS-REFERENCE-001` (PR1) : nouvelle section "Référence des commandes
  CLI" avec toutes les commandes `forge` annotées.
  Garde-fou : `tests/meta/test_docs_cli_commands_reference_001.py`.

- `DOCS-INSTALLATION-WINDOWS-001` (PR2) : documentation de l'installation sur
  Windows (MariaDB via Chocolatey/winget, Python 3.12 via winget, gestion chemins).
  Garde-fou : `tests/meta/test_docs_installation_windows_001.py`.

- `LANDING-SEARCH-BAR-001` (PR3) : ajout d'une barre de recherche dans la landing.
  Garde-fou : `tests/meta/test_landing_search_bar_001.py`.

- `LANDING-POSITIONNEMENT-VISIBILITY-001` (PR4) : amélioration de la visibilité
  du positionnement Forge dans la landing (titre hero, section d'encart).
  Garde-fou : `tests/meta/test_landing_positionnement_visibility_001.py`.

- `DOCS-RELEASE-LOCAL-STARTERS-COUNT-001` (PR5) : correction du compteur de
  starters locaux dans la documentation de release.
  Garde-fou : `tests/meta/test_docs_release_local_starters_001.py`.

### Publié

- `RELEASE-3.0.1-PATCH-STABLE-001` : bump coordonné vers `3.0.1` — 6 fichiers
  `pyproject.toml`, `forge/version.py`, `core/__init__.py`. Tag git `v3.0.1`.
  Build des 5 wheels `3.0.1`.

## [3.0.0] — 2026-05-12

### Corrigé — Synchronisation CSS de la landing

- `PRE-RELEASE-FIX-LANDING-CSS-SYNC-001` : correction de trois sujets
  liés à la génération de la landing page.

  **`forge sync:landing` étendue** : la commande synchronise désormais
  `static/` (CSS, JS, images) vers `docs/static/`, en plus du HTML.
  Auparavant, seul `mvc/views/landing/index.html` → `docs/index.html`
  était copié. Ajout de `sync_static()` dans `forge_cli/sync_landing.py`.

  **`package.json build:css` corrigé** : Tailwind v4 a déplacé le
  binaire CLI dans `@tailwindcss/cli`. Le script utilise désormais
  `npx @tailwindcss/cli` pour invoquer la bonne commande.

  **`CONTRIBUTING.md` enrichi** : section "Modifier la landing page"
  documentant le workflow complet (édition HTML, régénération CSS,
  synchronisation vers `docs/`).

  Justification : sans cette correction, modifier des classes Tailwind
  dans la landing causait des bugs visuels silencieux (dropdowns non
  stylés, texte invisible) parce que `docs/static/tailwind.css` restait
  sur l'ancienne version.

## [3.0.0rc1] — 2026-05-12

Release candidate 1 pour Forge 3.0. Fenêtre d'observation interne de 48h
avant le tag stable (`v3.0.0`). Pas de publication PyPI à cette étape.

### Publié — RELEASE-3.0.0-RC1-001

- Bump coordonné des versions vers `3.0.0rc1` :
  `pyproject.toml` racine, `packages/forge-mvc/pyproject.toml`,
  4 modules (`forge-mvc-mfa`, `forge-mvc-rbac`, `forge-mvc-workflow`,
  `forge-mvc-stats`), `forge.py` (`_FORGE_VERSION`, `_FORGE_DEFAULT_REF`),
  `core/__init__.py`.
- Optional-dependencies du core bumpées vers `==3.0.0rc1`.
- `docs/reference.md` : version API actualisée à `3.0.0rc1`.
- Build des 5 wheels `3.0.0rc1` (core + 4 modules).
- Validation locale : `forge --version` → `Forge 3.0.0rc1`.
- Tag git : `v3.0.0-rc1`.

**Découverte non listée** : `packages/forge-mvc/pyproject.toml` (miroir
setuptools tracké git) contenait aussi `2.5.0` — bumped en `3.0.0rc1`.

### Documenté — Synchronisation venv/source

- `PRE-RELEASE-FIX-VENV-STALE-001` : ajout dans `CONTRIBUTING.md`
  d'une section sur la synchronisation du venv local et de l'installation
  pipx avec le code source actuel.

  **Contexte** : l'audit pré-release avait révélé que `forge --version`
  affichait `Forge 2.3.0` alors que le code source était à 2.5.0 — le
  venv et pipx pointaient vers un wheel précompilé jamais régénéré.

  **Correctif appliqué** : wheel 2.5.0 reconstruit depuis le code actuel
  (`python -m build --wheel`) et réinstallé dans le venv local et via pipx.
  `forge --version` retourne maintenant `Forge 2.5.0` dans les deux
  environnements.

  **Procédure documentée** :

  ```bash
  python -m build --wheel
  pip install --force-reinstall --no-deps dist/forge_mvc-X.Y.Z-py3-none-any.whl
  pipx install --force dist/forge_mvc-X.Y.Z-py3-none-any.whl
  ```

  **Cause structurelle** : Forge utilise `py-modules = ["forge"]` qui ne
  supporte pas le mode édition fiable. La restructuration vers un package
  `forge/` est planifiée en post-3.0 (`PACKAGING-FORGE-MODULE-001`).

### Corrigé — Liens cassés dans la landing page

- `PRE-RELEASE-FIX-LANDING-LINKS-001` : correction de 5 URLs cassées
  dans la landing page identifiées par l'audit pré-release.

  **4 liens starters** : préfixe `starter-app-` retiré, regroupés sous
  `/starters/`. Le starter 01 a aussi été renommé (`contacts` →
  `contact-simple`).

  | Avant | Après |
  |---|---|
  | `starter-app-01-contacts/` | `starters/01-contact-simple/` |
  | `starter-app-02-utilisateurs-auth/` | `starters/02-utilisateurs-auth/` |
  | `starter-app-03-carnet-contacts/` | `starters/03-carnet-contacts/` |
  | `starter-app-04-suivi-comportement-eleves/` | `starters/04-suivi-comportement-eleves/` |

  **1 lien roadmap** : la section Roadmap n'a pas d'`index.md`, le slug
  `/roadmap/` ne résolvait rien. Corrigé en `/roadmap/forge-roadmap/`.

  **Source canonique** : `mvc/views/landing/index.html`. La version
  générée `docs/index.html` est régénérée via `forge sync:landing`.

  Tests garde-fous : `tests/meta/test_pre_release_fix_landing_links_001.py`
  (16 tests : absence des anciens slugs, présence des nouveaux, cohérence
  source ↔ généré).

### Corrigé — Alignement requires-python avec ADR-006

- `PRE-RELEASE-FIX-PYPROJECT-PYTHON-001` : `pyproject.toml` racine aligné sur
  Python 3.12+ conformément à ADR-006 :
  - `requires-python` : `>=3.11` → `>=3.12`
  - Classifier `Programming Language :: Python :: 3.11` retiré
  - `[tool.ruff] target-version` : `py311` → `py312`
  - 4 modules (`forge-mvc-mfa`, `forge-mvc-rbac`, `forge-mvc-stats`,
    `forge-mvc-workflow`) : ajout classifiers `Python :: 3.13` et `Python :: 3.14`
    pour cohérence avec le `pyproject.toml` racine

  Tests garde-fous : `tests/meta/test_pre_release_fix_pyproject_python_001.py`
  (11 tests : requires-python, classifiers 3.11 absent, target-version, 3.13/3.14 présents).

### Corrigé — Import top-level de module optionnel dans le code framework

- `PRE-RELEASE-FIX-RBAC-IMPORT-001` : suppression des 3 imports top-level de
  modules optionnels (`forge_mvc_rbac`, `forge_mvc_workflow`) dans le code
  framework qui rendaient la CLI inutilisable sans les extras :
  - `forge_cli/entities/crud/controller_builder.py` : import `normalize_permission_code`
    déplacé en lazy conditionnel (seulement si l'entité déclare des permissions RBAC)
  - `core/mvc/controller/base_controller.py` : import `make_auth_jinja_context, make_can`
    migré en `try/except ImportError` dans `render()` (dégradation gracieuse)
  - `integrations/jinja2/renderer.py` : import `make_workflow_jinja_helpers`
    migré en `try/except ImportError` dans `__init__()` (dégradation gracieuse)

  Tests garde-fous : `tests/meta/test_pre_release_fix_rbac_import_001.py`
  (6 tests : analyse AST des 3 racines framework + bootstrap CLI sans crash).

### Validé — Audit pré-release

- `PRE-RELEASE-AUDIT-3.0-001` : exécution d'un audit pré-release complet
  avant publication du RC. Six familles testées :
  - Install nouvel utilisateur (venv jetable)
  - Cycle complet d'un starter (bloqué — voir correctifs)
  - Lints stricts (pytest 8 920 passants, ruff ALL 22 155 violations cosmétiques,
    mkdocs --strict exit 0, compileall OK, git diff --check OK)
  - Cross-version Python (3.12 : 8 920 tests ✓ ; 3.14 : 1 764 tests ✓ ; 3.13 : non testé)
  - Audit dépendances/sécurité (urllib3 CVE — dépendance dev uniquement, non bloquant)
  - Documentation cohérente (5 liens cassés landing — voir correctifs)

  Rapport complet : `docs/audits/pre-release-3.0-audit-001.md`.

  **Trouvailles principales** :
  - Bloquant RC : `PRE-RELEASE-FIX-RBAC-IMPORT-001` — import top-level
    `forge_mvc_rbac` dans `forge_cli/entities/crud/controller_builder.py`
    rend `forge` inutilisable sans le module optionnel
  - Important : `PRE-RELEASE-FIX-LANDING-LINKS-001` — 5 liens cassés landing
    (4 starters anciens chemins + 1 roadmap sans index)
  - Important : `PRE-RELEASE-FIX-PYPROJECT-PYTHON-001` — `requires-python`
    déclaré `>=3.11` au lieu de `>=3.12` (ADR-006)
  - Important : `PRE-RELEASE-FIX-VENV-STALE-001` — copie figée `forge.py`
    2.3.0 dans `.venv` (ne touche pas les utilisateurs finaux)

  **Verdict** : audit demande corrections — RC non publiable en l'état.

### Documenté — Refonte de la landing page pour Forge 3.0

- `DOCS-LANDING-PAGE-3.0-001` : refonte intégrale de la landing page
  (`mvc/views/landing/index.html`, régénérée vers `docs/index.html`
  via `forge sync:landing`) pour refléter l'état Forge 3.0.

  **Navigation refondue** : 5 entrées principales + 2 dropdowns natifs
  (`<details>`/`<summary>`) : Forge / Installation / Starters / Documentation
  + Dropdown **Briques** (Core / Modules / CLI) + Dropdown **Projet** (Roadmap / GitHub).

  **Hero actualisé** : version strip `v3.0.0 · Python 3.12+ · MariaDB ·
  MVC serveur · Open source`, label encart terminal `workflow Forge 3.0.0`.

  **Section Core refondue** : H2 `L'écosystème Forge.`, structurée en
  deux sous-sections — **Le core Forge** (17 cartes) et **Modules officiels opt-in**
  (4 cartes : MFA, RBAC, Workflow, Stats — avec distributions PyPI et ancre `#modules`).

  **Section Stack** (NOUVELLE) : 6 cartes présentant les fondations techniques
  (Python 3.12+, MariaDB 11.x, Jinja2, HTMX, Alpine.js, Tailwind) avec liens
  vers la documentation officielle de chaque techno.

  **Section Workflow** : correction typo (`auditable` → `auditables`).

  **Section Installation** : note modules optionnels ajoutée après le terminal
  parcours utilisateur (`pipx install "forge-mvc[all]"`).

  **Section État** : refonte totale — bloc gauche `Forge 3.0.0` (ouverture open
  source, core minimal, 4 modules, 41 tickets) ; bloc droite `Après 3.0 /
  Stabilisation` remplace l'ancien `Auth/User avancée`.

  **Section Documentation** : `Plus de 8000 tests` (au lieu de 7000) + bouton
  **Charte** vers `CHARTE_DOC.md` sur GitHub.

  Tests garde-fous : `tests/meta/test_docs_landing_page_3_0_001.py` (53 tests).

## [2.10.0] — 2026-05-11

### Consolidation des roadmaps (DOCS-CONSOLIDATE-ROADMAPS-001)

Réduction de 5 fichiers roadmap à 2 actifs. Enrichissement de `forge-roadmap.md`
avec la section **Phase 14 — Refonte vers Forge 3.0**.

**Archivés vers `docs/history/`** (fichiers désormais obsolètes ou remplacés) :

- `forge_post_2_0_consolidation_roadmap.md` — journal de consolidation post-2.0,
  remplacé par la roadmap unifiée lors de `ROADMAP-UNIFIED-001`.
- `forge-roadmap-post-2.0.md` — feuille de route post-2.0 partielle, tickets livrés
  dans la roadmap unifiée.
- `forge-roadmap-ux.md` — phases 5-10 (DX, E2E, sécurité, release, doc, API JSON),
  toutes terminées et documentées dans la roadmap unifiée.

**Restent dans `docs/roadmap/`** :

- `forge-roadmap.md` — source unique de priorité
- `forge-design-roadmap.md` — roadmap du projet compagnon Forge Design

**Section Phase 14 ajoutée à `forge-roadmap.md`** : sous-phases 14.1
(durcissement pré-refonte — 13 tickets), 14.2 (infrastructure 3.0 — ADR-003/007,
packaging multi-distributions), 14.3 (reconstruction cœur minimal — 14 tickets
d'extractions et nettoyage), 14.4 (clôture pré-3.0, à venir) et déférés post-3.0.

**Autres corrections** :

- `CLAUDE.md` section 8 : `forge-roadmap-post-2.0.md` → `forge-roadmap.md`
- `docs/contributing.md` : références au fichier archivé remplacées par `CHANGELOG.md`
- `tests/test_roadmap_unified.py` et `tests/meta/test_module_lifecycle_doc_001.py` :
  chemins mis à jour (`docs/roadmap/` → `docs/history/`)
- `mkdocs.yml` : section Roadmap épurée (1 entrée en moins), archives ajoutées
  dans la section Historique

Guard-fou : `tests/meta/test_docs_consolidate_roadmaps_001.py` (18 tests).

### Actualisation des ressources d'entrée pour Forge 3.0 (GETTING-STARTED-3.0-001)

Chasse aux mentions obsolètes dans les 4 ressources d'entrée de Forge.

**README.md** :

- Titre : `2.5.0` → `3.0.0`
- ADR : ajout de ADR-001, ADR-002, ADR-008 (liste complète des 8 ADR)
- Nouvelle section "Modules officiels disponibles" : `forge-mvc-mfa`,
  `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats` avec
  installation via extras (`forge-mvc[all]`)
- `core/security/hashing.py` : mention clarifiée (legacy PBKDF2,
  vérification conservée pour compatibilité, création supprimée en 3.0)
- `cmd/` : section "déprécié" reécrite en "supprimé en Forge 3.0" ;
  arbre de fichiers nettoyé ; mentions d'exécution retirées
- Tableau "Ce que Forge n'est pas" : `cmd/make.py` → "supprimé en Forge 3.0"
- Références git clone : `v2.5.0` → `v3.0.0`
- Lien ADR-002 : label nettoyé (suppression de "Forge 2.x")

**docs/15-minutes.md, docs/guide.md, docs/app-complete-tutorial.md** :
propres — aucune mention obsolète trouvée à l'audit.

**Correction de tests** :

- `test_lang_migration_001.py` : exclusion de `test_getting_started_3_0_001.py`
  du grep (le garde-fou liste les noms français à des fins de vérification)
- `test_publication_2_0_version_001.py` : tests README/git-clone adaptés
  pour refléter l'anticipation de la version 3.0.0

Guard-fou : `tests/meta/test_getting_started_3_0_001.py` (73 tests).

### Conventions internes de Forge (DOCS-INTERNAL-CONVENTIONS-001)

Consolidation des 18 patterns émergents de la phase 14 dans
`docs/contributing/conventions.md`. Briefing opérationnel pour tout
contributeur (humain ou agent IA) sur les techniques de travail éprouvées.

**18 patterns documentés en 4 sections** :

- **A. Audit avant action** (5 patterns) : audit 5 racines, `.gitignore`,
  historique git, production interne, doc référencée par les tests
- **B. Tests : conventions et patterns** (6 patterns) : helpers locaux pour
  formats legacy, `module.__file__`, `PROJECT_ROOT` partagé, classification
  sémantique des `_001`, généraliser plutôt que supprimer, cohérence des
  noms de fonctions de tests
- **C. Code : architecture** (5 patterns) : lock + delegate,
  `register_<module>_routes`, note « Module extrait », garde-fous
  documentaires, word boundaries pour renommages
- **D. Documentation : structure** (3 patterns) : MkDocs strict + liens
  hors `docs/`, `docs/history/` comme mémoire brute, section « Historique »
  dans la nav

Chaque pattern : énoncé court + ticket d'origine + exemple ou règle pratique.

**CLAUDE.md section 9** : liste détaillée retirée, résumé thématique conservé,
pointer vers `docs/contributing/conventions.md` comme source canonique.

**`mkdocs.yml`** : entrée "Contribuer" restructurée en "Pour contribuer" avec
deux sous-entrées (Vue d'ensemble, Conventions de travail).

Guard-fou : `tests/meta/test_docs_internal_conventions_001.py` (29 tests).

### Une seule charte canonique (DOCS-CHARTER-DEDUP-001)

`CHARTE_DOC.md` (racine) et `docs/charter.md` étaient deux fichiers identiques
(473 lignes, 14 659 octets chacun). Application du principe 11 de la charte v2.

**Avant** : risque de divergence à la première édition d'un seul des deux fichiers.

**Après** :

- `CHARTE_DOC.md` (racine) est la **source canonique unique**. Note d'autorité
  ajoutée en tête.
- `docs/charter.md` est un **alias court** (~35 lignes) qui présente un aperçu
  des 11 principes et renvoie vers le fichier canonique.
- L'intégration MkDocs reste fonctionnelle (entrée "Philosophie > Charte v2"
  pointe toujours vers `docs/charter.md`).
- Les liens actifs dans `CLAUDE.md`, `README.md`, `docs/adr/007-*.md` pointaient
  déjà vers `CHARTE_DOC.md` — aucune modification nécessaire.

Guard-fou : `tests/meta/test_docs_charter_dedup_001.py` (8 tests).

### Découpage de docs/reference.md (DOCS-REFERENCE-SPLIT-001)

Refonte de la documentation de référence : `docs/reference.md` (4831 lignes)
découpé en 11 sous-fichiers thématiques dans `docs/reference/`.

**`docs/reference.md` devient un index** (≤ 108 lignes) avec le schéma Mermaid
et des liens vers les sous-fichiers.

**Sous-fichiers créés** :

- `reference/api.md` — API Forge complète (routes, entités, CRUD de base, CLI)
- `reference/workflow.md` — Statuts et transitions (module `forge-mvc-workflow`)
- `reference/stats.md` — Statistiques (module `forge-mvc-stats`)
- `reference/auth-mfa.md` — Challenge MFA (module `forge-mvc-mfa`)
- `reference/crud.md` — Relations avancées et CRUD enrichi
- `reference/pages-publiques.md` — Pages publiques sans authentification
- `reference/modules.md` — Modules Forge et intégration
- `reference/profils.md` — Profils de projet et endpoint `/health`
- `reference/tests-e2e.md` — Tests HTTP, MariaDB, CSRF
- `reference/sessions.md` — Sessions et concurrence
- `reference/audit-auth.md` — Audit auth, cookies, headers de sécurité, uploads

**Adaptations autorisées** dans chaque sous-fichier :

- Titre de niveau 1 (passage de `##` à `#`, suppression des mentions "Phase X")
- Note « Module extrait » en tête des fichiers `workflow.md`, `stats.md`, `auth-mfa.md`
- Liens internes corrigés pour le nouveau niveau d'arborescence

**Autres mises à jour** :

- `mkdocs.yml` : section Référence enrichie avec la hiérarchie des 11 sous-fichiers
- `docs/security.md` : lien `reference.md#coresecurity` → `reference/api.md#coresecurity`
- 8 fichiers de tests mis à jour pour pointer vers les bons sous-fichiers
  (`api.md`, `modules.md`, `profils.md`)
- `tests/test_docs_config.py` : label nav `"API et CLI"` → `"API Forge complète"`

Guard-fou : `tests/meta/test_docs_reference_split_001.py` (51 tests).

### forge module:routes n'écrit plus dans mvc/routes.py (MODULES-EXPLICIT-ROUTES-001)

Application du principe 9 de la charte v2 : « pas d'écritures invisibles dans
le code utilisateur ». `mvc/routes.py` est un fichier propriétaire du
développeur — Forge ne doit pas le modifier silencieusement.

**Changements de comportement :**

- `forge module:routes <nom>` génère `mvc/routes_<nom>.py` (write-if-new) et
  **affiche sur stdout** les lignes à ajouter manuellement dans `mvc/routes.py`.
- Si `mvc/routes_<nom>.py` existe déjà, la commande échoue avec un message
  explicite (`ModuleRoutesAlreadyGeneratedError`).
- `mvc/routes.py` n'est **jamais** modifié par Forge.
- `mvc/module_routes.py` n'est **plus** créé par `forge module:routes`.

**API Python :**

- `inject_module_routes` → **supprimée**, remplacée par `generate_module_routes`
- `APP_ROUTES_FILE` → **supprimée** de `core.modules`
- `_ensure_app_routes_bridge_content` → **supprimée**
- Nouveau : `generate_module_routes(module_name, *, registry_path, dry_run)`
- Nouveau : `ModuleRoutesAlreadyGeneratedError(ValueError)`
- Nouveau : `ModuleRouteGenerationResult` (dataclass)

**Migration :**

```python
# Avant
from core.modules import inject_module_routes
inject_module_routes("agenda")  # écrivait dans mvc/routes.py et mvc/module_routes.py

# Après
from core.modules import generate_module_routes
result = generate_module_routes("agenda")  # crée mvc/routes_agenda.py
# Ajouter manuellement dans mvc/routes.py les lignes affichées :
# from mvc.routes_agenda import register_agenda_routes
# register_agenda_routes(router)
```

### Modifie — Hashing PBKDF2 retiré de la création (HASHING-PBKDF2-REMOVE-001)

Suppression de `hacher_mot_de_passe()` et de la constante `ITERATIONS`.
`core/security/hashing.py` est desormais **lecture seule** — verification
des hashes PBKDF2 legacy uniquement.

**Supprime :**
- `hacher_mot_de_passe()` — plus de creation de nouveaux hashes PBKDF2
- Constante `ITERATIONS` (600 000) — retireee avec la fonction de creation

**Conserve pour retrocompatibilite :**
- `verifier_mot_de_passe()` — verification des hashes PBKDF2 existants en base
- `pbkdf2_needs_rehash()` — retourne desormais `True` pour tout hash PBKDF2
  (tous doivent migrer vers Argon2id)
- Rate limiting (`enregistrer_tentative`, `est_limite`) — inchange

**Migration transparente :** les hashes PBKDF2 existants continuent de fonctionner.
A chaque connexion reussie, le hash est automatiquement remplace par Argon2id
(mecanisme AUTH-HASH-MIGRATION-001). Suppression complete du module prevue
quand tous les hashes auront migre (HASHING-PBKDF2-DEFINITIVE-REMOVE-001, post-3.0).

**Pas de consommateurs productifs trouves** dans `core/`, `mvc/`, `forge_cli/`.
Les tests ont ete adaptes avec des helpers internes qui creent les hashes PBKDF2
directement via `hashlib.pbkdf2_hmac`.

Justification : principe 11 de la charte v2 (une seule facon de creer un hash :
Argon2id) et principe 8 (noyau minimal).

### Supprime — Dossier cmd/ legacy (CMD-LEGACY-REMOVE-001)

Suppression definitive du dossier `cmd/` (legacy depuis Forge 1.1.0).

**~2 006 lignes supprimees.** Le dossier contenait des generateurs obsoletes
(`cmd/make.py`, `cmd/mvc/`, `cmd/entities/`, `cmd/security/`, `cmd/sql/`,
`cmd/inspect/`) tous remplaces par les commandes modernes dans `forge_cli/`.

**Migration :** si vous utilisiez encore `python cmd/make.py ...`,
utilisez a la place `forge make:...` (voir `forge help`).

**Pas de shims** (charte v2, note pre-3.0). Les anciens scripts ne sont
plus disponibles.

Justification : application du principe 11 de la charte v2
(*une seule facon officielle de faire chaque chose*). Le dossier etait
declare legacy par son propre README depuis Forge 1.1.0.

Effet de bord positif : retire les usages PBKDF2 dans `cmd/security/`.
Le ticket `HASHING-PBKDF2-REMOVE-001` finalisera la suppression de PBKDF2
dans le reste du projet.

### Renommage API publique en anglais (LANG-MIGRATION-001)

Application de l'ADR-003 : l'API publique de Forge est en anglais.
17 symboles francais renommes dans `core/security/session.py`,
`core/security/hashing.py`, `core/uploads/rate_limit.py` et
`mvc/models/auth_model.py`.

**Correspondance complete :**

| Ancien nom (francais)        | Nouveau nom (anglais)         | Module                      |
|------------------------------|-------------------------------|-----------------------------|
| `DUREE_SESSION`              | `SESSION_DURATION`            | `core.security.session`     |
| `creer_session()`            | `create_session()`            | `core.security.session`     |
| `supprimer_session()`        | `delete_session()`            | `core.security.session`     |
| `regenerer_session()`        | `regenerate_session()`        | `core.security.session`     |
| `authentifier_session()`     | `authenticate_session()`      | `core.security.session`     |
| `est_authentifie()`          | `is_authenticated()`          | `core.security.session`     |
| `get_utilisateur()`          | `get_user()`                  | `core.security.session`     |
| `utilisateur_a_role()`       | `user_has_role()`             | `core.security.session`     |
| `verifier_mot_de_passe()`    | `verify_password_legacy()`    | `core.security.hashing`     |
| `enregistrer_tentative()`    | `record_attempt()`            | `core.security.hashing`     |
| `MAX_TENTATIVES`             | `MAX_ATTEMPTS`                | `core.security.hashing`     |
| `FENETRE_SECONDES`           | `RATE_LIMIT_WINDOW`           | `core.security.hashing`     |
| `est_limite()`               | `is_rate_limited()`           | `core.security.hashing`     |
| `est_limite_upload()`        | `is_upload_rate_limited()`    | `core.uploads.rate_limit`   |
| `enregistrer_upload()`       | `record_upload_attempt()`     | `core.uploads.rate_limit`   |
| `UPLOAD_FENETRE_SECONDES`    | `UPLOAD_RATE_LIMIT_WINDOW`    | `core.uploads.rate_limit`   |
| `utilisateur_id` (param.)    | `user_id`                     | `mvc.models.auth_model`     |

**Pas de shims** (charte v2, note pre-3.0). Migration directe, ~280 occurrences.

Guard-fou : `tests/test_lang_migration_001.py` (51 tests) garantit
l'absence de toute apparition des anciens noms en dehors de ce fichier.

### Réorganisation allégée des tests (TESTS-CLASSIFY-001)

Création de deux sous-dossiers dans `tests/` pour isoler les garde-fous et
les tests de release des tests fonctionnels.

**Nouveau** :
- `tests/meta/` — 41 garde-fous de tickets (`test_*_001.py` et fichiers assimilés)
  qui valident des contrats d'absence ou de migration suite à un ticket structurant
- `tests/release/` — 11 tests de cohérence release (versionning, packaging, publication)

**Inchangé** : les tests fonctionnels (~230 fichiers) restent à plat dans `tests/`.
**Aucun fichier modifié dans son contenu** — pure réorganisation, sauf 3 corrections
de `parents[1]` → `parents[2]` (profondeur +1 due au déplacement).

Pas d'affinage vers `unit/`, `integration/`, `generation/`. Ce découpage est déféré
à `TESTS-CLASSIFY-DEEP-001` (post-3.0).

Guard-fou : `tests/meta/test_tests_classify_001.py` (53 tests).

### Refonte de CLAUDE.md — briefing IA durable (CLAUDE-MD-UPDATE-001)

`CLAUDE.md` refondu intégralement pour refléter l'état Forge 2.10.0 et
survivre aux ticket-cycles.

**Avant** : fichier obsolète décrivant Forge 1.5.0 / 3964 tests / Phase 4.5.
Dangereux pour un agent IA qui s'en servait pour s'orienter.

**Après** : contenu stable par construction — architecture, charte v2 (11 principes),
ADR (001–008), conventions de tickets/tests/commits, patterns émergents, modes
d'action acceptables. Pointeurs vers les sources canoniques pour les informations
volatiles (version, compteur de tests, tickets en cours).

Test garde-fou : `tests/test_claude_md_001.py` (19 tests) vérifie que le fichier
mentionne les éléments structurants et ne contient pas de compteurs de tests précis.

**Prochaine mise à jour prévue** : tag 3.0.0.

### Supprimé — Shims de compat MFA (EXTRACTION-CLEANUP-SHIMS-001)

Suppression des trois shims créés à `MFA-EXTRACT-001` pour adoucir la transition :

- `core/auth/mfa.py` (shim)
- `core/auth/recovery.py` (shim)
- `core/auth/totp_replay.py` (shim)

**Migration :** tout import `from core.auth.mfa import X` (ou `.recovery`, `.totp_replay`)
doit devenir `from forge_mvc_mfa import X`.

**Justification :** pas d'utilisateurs externes à protéger (note pré-3.0). Les autres
extractions (Workflow, Stats, RBAC) ont été faites sans shims. Forge 3.0 sort sans aucun
shim de compat — cohérence du principe 11 de la charte v2.

`TestLegacyShims` dans `test_mfa_extract_001.py` remplacé par `TestShimsRemoved` et
`TestNoShimImportsRemain`. Supprime également un `DeprecationWarning` de la suite de tests.

### Architecture audit auth documentée (AUTH-AUDIT-CLARIFY-ARCHITECTURE-001)

**Pas de changement de code productif** — clarification documentaire pure.

L'architecture existait mais n'était pas documentée. Un développeur découvrant
la table SQL `auth_audit_log` sans documentation pouvait croire que Forge la
remplissait automatiquement.

**Ce que Forge fournit (trois briques distinctes)** :

- Contrat `AuthAuditEvent` : structure validée, 20+ types normalisés.
- Émission Python via `safe_log_auth_event` vers le logger `forge.auth.audit`.
  Le handler est configuré par l'application.
- Table SQL `auth_audit_log` (infrastructure latente, schéma prêt).

**Ce que Forge ne fait pas** : Forge n'écrit pas dans `auth_audit_log`.
La persistance est une décision applicative (rétention, backend, purge, RGPD).

**Nouveautés** :

- `docs/adr/008-auth-audit-architecture.md` — décision d'architecture avec trois
  approches typiques (handler logging SQL, wrapper applicatif, stream externe).
- Section "Architecture audit" dans `docs/auth.md` avec exemple d'intégration.
- Docstring de `core/auth/audit.py` enrichi pour pointer vers l'ADR-008.
- Guard-fou `tests/test_auth_audit_architecture_001.py` (13 tests).

Justification : principe 3 de la charte v2 (refuser la magie cachée) et
principe 1 (séparer framework et application métier).

## [2.9.0] — 2026-05-11

### Extraction RBAC dans forge-mvc-rbac (RBAC-EXTRACT-001)

Quatrieme et derniere extraction de la phase 14.3. RBAC deplace vers
le module separe `forge-mvc-rbac 2.5.0`.

**Fichiers deplaces :**

- `core/security/rbac.py` → `forge_mvc_rbac/rbac.py`
- `core/auth/user_rbac.py` → `forge_mvc_rbac/user_rbac.py`
- `core/auth/user_rbac_resolver.py` → `forge_mvc_rbac/resolver.py`
- `core/auth/authorization.py` → `forge_mvc_rbac/authorization.py`
- `core/auth/jinja.py` → `forge_mvc_rbac/jinja.py`
- `mvc/models/sql/rbac.sql` → `packages/forge-mvc-rbac/sql/rbac.sql`
- `mvc/models/sql/user_roles.sql` → `packages/forge-mvc-rbac/sql/user_roles.sql`

**Reste dans core/auth/** : l'auth basique (login, logout, sessions, password, AuthUser),
les mecanismes transversaux (audit, rate-limit, exceptions, tokens, email, reset).

**Migration :**
- `from core.security.rbac import X` → `from forge_mvc_rbac import X`
- `from core.auth.authorization import X` → `from forge_mvc_rbac import X`
- `from core.auth.user_rbac import X` → `from forge_mvc_rbac import X`
- `from core.auth.user_rbac_resolver import X` → `from forge_mvc_rbac import X`
- `from core.auth.jinja import X` → `from forge_mvc_rbac import X`

**Pas de shims de compat** (note pre-3.0). Les anciens imports levent `ImportError`.

**Installation :**

```bash
pip install forge-mvc-rbac
```

Justification : application de ADR-004. RBAC est un mecanisme metier optionnel.
Toutes les applications n'ont pas besoin de controle d'acces fin par permissions.

## [2.8.0] — 2026-05-11

### Extraction Stats dans forge-mvc-stats (STATS-EXTRACT-001)

Troisieme extraction de la phase 14.3. `core/stats/` deplace vers
le module separe `forge-mvc-stats 2.5.0`.

**Fichiers deplaces :**

- `core/stats/events.py` → `forge_mvc_stats/events.py`
- `core/stats/schema.py` → `forge_mvc_stats/schema.py`
- `core/stats/tracking.py` → `forge_mvc_stats/tracking.py`
- `core/stats/admin.py` → `forge_mvc_stats/admin.py`
- `core/stats/__init__.py` → `forge_mvc_stats/__init__.py` (refait)

**Migration :** `from core.stats import X` → `from forge_mvc_stats import X`

**Pas de shims de compat** (note pre-3.0). Les anciens imports levent `ImportError`.

**Installation :**

```bash
pip install forge-mvc-stats
```

Justification : application de ADR-004. Les statistiques generiques sont
un mecanisme metier optionnel, pas une primitive du framework.

## [2.7.0] — 2026-05-11

### Extraction Workflow dans forge-mvc-workflow (WORKFLOW-EXTRACT-001)

Deuxieme extraction de la phase 14.3. `core/workflow/` deplace vers
le module separe `forge-mvc-workflow 2.6.0`.

**Fichiers deplaces :**

- `core/workflow/status.py` → `forge_mvc_workflow/status.py`
- `core/workflow/transitions.py` → `forge_mvc_workflow/transitions.py`
- `core/workflow/jinja.py` → `forge_mvc_workflow/jinja.py`
- `core/workflow/__init__.py` → `forge_mvc_workflow/__init__.py` (refait)

**Migration :** `from core.workflow import X` → `from forge_mvc_workflow import X`

**Pas de shims de compat** (note pre-3.0). Les anciens imports levent `ImportError`.

**Installation :**

```bash
pip install forge-mvc-workflow
```

Justification : application de ADR-004. Workflow est un mecanisme metier
(cycles de vie applicatifs) optionnel, pas une primitive du framework.

## [2.6.0] — 2026-05-11

### Supprimé — OIDC (OIDC-REMOVE-OR-EXTRACT-001)

Suppression complete du code OIDC du depot. L'implementation etait partielle
(pas de token exchange, pas de validation JWT/JWKS, pas de validation des
claims, pas de liaison utilisateur) et incompatible avec la cible "release
publique stable" de Forge 3.0 (principe 10 de la charte v2 : API publique =
contrat de completude).

**Fichiers supprimes :**

- `core/auth/experimental/oidc.py` (~1 000 lignes) et `oidc_identity.py`
- `core/auth/oidc.py` et `oidc_identity.py` (shims de compat du ticket #7)
- `mvc/models/sql/auth_oidc_accounts.sql` et `auth_oidc_identities.sql`
- `tests/test_auth_oidc_*.py` (7 fichiers de tests)

**Constants retirees :**

- `AUTH_EVENT_OIDC_*` (6 constantes) de `core.auth.audit`
- `AUTH_RATE_LIMIT_OIDC_CALLBACK` de `core.auth.rate_limit`
- Exports OIDC de `core.auth.__init__`

**Recuperation possible :** le code reste dans l'historique git.

```bash
git show HEAD~:core/auth/experimental/oidc.py
```

Si OIDC devient une priorite, un ticket dedie `OIDC-IMPLEMENT-COMPLETE-001`
partira d'une page blanche. Justification : application stricte du principe 10
de la charte v2 et de la note pre-3.0. Decision finale ADR-004.

## [2.5.0] — 2026-05-10

### Extraction MFA dans forge-mvc-mfa (MFA-EXTRACT-001)

Pilote du plan d'extraction ADR-004 / ADR-005. Toute la brique MFA est
physiquement déplacée de `core/auth/` vers `packages/forge-mvc-mfa/`.

**Ce qui a changé :**

- `core/auth/mfa.py`, `core/auth/recovery.py`, `core/auth/totp_replay.py`
  deviennent des **shims de compatibilité** qui émettent `DeprecationWarning`
  et réexportent depuis `forge_mvc_mfa`. Ils seront retirés en Forge 3.0.
- `core.auth.__all__` ne réexporte plus les noms MFA
  (`AuthMfaFactor`, `MFA_FACTOR_TOTP`, `is_mfa_enabled`, etc.).
  Les exceptions `InvalidMfaFactorError` et `InvalidMfaRecoveryCodeError`
  restent dans `core.auth.exceptions` (transversales).
- `mvc/models/mfa_model.py` → `packages/forge-mvc-mfa/forge_mvc_mfa/model.py`.
- `mvc/models/sql/auth_mfa_factors.sql` et `auth_mfa_recovery_codes.sql`
  → `packages/forge-mvc-mfa/sql/`.
- `forge-mvc-mfa 2.5.0` publie l'API publique complète avec `pyotp>=2.9,<3`
  comme dépendance déclarée.

**Migration :**

```python
# Avant (déprécié — shim Forge 2.x)
from core.auth import AuthMfaFactor, is_mfa_enabled

# Après (Forge 2.5+)
from forge_mvc_mfa import AuthMfaFactor, is_mfa_enabled
```

Les projets existants continuent de fonctionner via les shims jusqu'à Forge 3.0.

## [2.4.0] — 2026-05-10

### Infrastructure multi-distributions PyPI (PACKAGING-MULTI-DIST-001)

Première étape de l'infrastructure de packaging multi-distributions préparée par ADR-005.

- Nouveau répertoire `packages/` contenant 5 distributions indépendantes :
  - `packages/forge-mvc/` — noyau complet, 3.0-ready (Python ≥ 3.12), référence le source racine via `where = ["../.."]`
  - `packages/forge-mvc-mfa/` — brique MFA (placeholder, distribuable)
  - `packages/forge-mvc-rbac/` — brique RBAC (placeholder, distribuable)
  - `packages/forge-mvc-workflow/` — brique workflow (placeholder, distribuable)
  - `packages/forge-mvc-stats/` — brique statistiques (placeholder, distribuable)
- `pyproject.toml` racine mis à jour : ajout de `[project.optional-dependencies]` (`mfa`, `rbac`, `workflow`, `stats`, `all`), version bump 2.3.0 → 2.4.0.
- `requirements-dev.txt` : ajout de `setuptools>=77.0.3` (nécessaire pour les builds `--no-isolation`).
- CI `.github/workflows/tests.yml` : ajout de l'étape "Build optional distributions" — toutes les distributions sont construites à chaque push.
- Documentation `docs/installation.md` : section "Modèle de packages" ajoutée.

Les distributions optionnelles sont des placeholders vides (`__init__.py` + `pyproject.toml`) qui ne seront peuplées que lors de la migration Forge 3.0. Chacune est buildable dès maintenant via `python -m build --no-isolation packages/<dist>/`.

### Charte philosophique et décisions architecturales (CHARTER-V2-ADOPTION-001)

- Adoption formelle de la charte philosophique v2 (`CHARTE_DOC.md`), qui remplace la charte documentaire v1 (archivée dans `docs/history/charte-v1.md`). La v2 ajoute 4 principes structurants (noyau minimal, pas d'écriture invisible, API publique = contrat de complétude, une seule façon officielle de faire chaque chose) et 4 règles d'évolution (A-D).
- 5 ADR publiés dans `docs/adr/` qui actent les décisions structurantes de Forge 3.0 :
  - ADR-003 : API publique en anglais
  - ADR-004 : périmètre du `core/` minimal strict (5 modules à extraire)
  - ADR-005 : packaging hybride monorepo, multi-distributions PyPI
  - ADR-006 : Python 3.12+ minimum
  - ADR-007 : adoption formelle de la charte v2

Ces décisions guideront la phase 14.3 (reconstruction) et la sortie de Forge 3.0.

### Sécurité — CSP complétée (SEC-CSP-COMPLETENESS-001)

- `img-src 'self' data:` : autorise les images encodées en `data:` URI (SVG inline, avatars, placeholders). Sans cette directive, `default-src 'self'` les bloquait silencieusement.
- `form-action 'self'` : limite la destination des `<form action>` à l'origine. Cette directive n'a pas de fallback sur `default-src` selon la spécification CSP — elle doit être déclarée explicitement.

Aucun impact sur les applications légitimes. La CSP passe de 6 à 8 directives.

### Audit — Propagation des erreurs dans log_auth_event (AUTH-AUDIT-PROPAGATE-001)

**Comportement modifié.**

- `log_auth_event()` propage désormais ses exceptions au lieu de les avaler silencieusement. En particulier, un `event_type` invalide (vide, None, espaces) lève `InvalidAuthAuditEventError`, et toute défaillance interne du logger est propagée.
- Ce changement rend effectif le mécanisme d'observabilité installé par `AUTH-AUDIT-RESILIENCE-001` : `safe_log_auth_event` peut maintenant observer des échecs réels en production, sans mock.
- Les 7 appels directs à `log_auth_event` dans `mvc/controllers/` migrés vers `safe_log_auth_event`.
- Les 6 blocs `try: log_auth_event(...) except: pass` dans `forge_cli/auth.py` remplacés par `safe_log_auth_event(...)`.

**Migration :** si votre code appelait `log_auth_event` directement dans un contexte métier, remplacer par `safe_log_auth_event`. Si vous l'appelez dans un contexte administratif et souhaitez connaître l'échec, entourer d'un `try/except` explicite et documenté.

### Audit — Résilience des appels log_auth_event (AUTH-AUDIT-RESILIENCE-001)

- Nouvelle fonction `safe_log_auth_event()` dans `core.auth.audit` : encapsule `log_auth_event` avec gestion d'exception, logging des échecs via le logger Python `forge.auth.audit` (niveau `WARNING`, traceback inclus), et compteur d'échecs observable via `get_audit_failure_count()`.
- `reset_audit_failure_count()` fourni pour les tests.
- Les 3 appels `try: log_auth_event(...) except: pass` dans `core/auth/mfa.py` remplacés par `safe_log_auth_event(...)`.
- `safe_log_auth_event`, `get_audit_failure_count`, `reset_audit_failure_count` exportés depuis `core.auth`.
- **Pas de rupture API** : `log_auth_event` reste disponible et inchangé.

### Sécurité — Vérification d'identité dans la revalidation MFA (SEC-MFA-REVALIDATION-IDENTITY-001)

**Rupture comportementale.**

- `verify_mfa_revalidation` et `mark_mfa_revalidated` vérifient désormais que la session courante est authentifiée et que son utilisateur correspond au `user_id` passé en paramètre.
- Sans cette vérification, un contrôleur mal formé pouvait appeler `verify_mfa_revalidation` avec un `user_id` arbitraire — revalidant un user différent de l'utilisateur de la session courante.
- Comportement en cas d'échec d'identité : `verify_mfa_revalidation` retourne `None`, `mark_mfa_revalidated` est un no-op silencieux. **Le rate-limit n'est pas incrémenté** (l'échec d'identité est distinct d'une tentative de code invalide).
- Nouvel événement audit `mfa.revalidation.identity_mismatch` (`AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH`) émis à chaque échec d'identité.

**Migration :** tout code appelant ces fonctions hors d'une session authentifiée doit être placé après la connexion. La session doit avoir `authentifie=True` et `utilisateur["id"] == user_id`.

### Modifié — Sécurité MFA (SEC-MFA-SECRET-NAMING-001)

- Renommage du champ `AuthMfaFactor.secret_hash` → `totp_secret` (nom plus précis, sans suggestion de hachage).
- Renommage de la colonne SQL `secret_hash` → `totp_secret` dans `auth_mfa_factors`.
- `AuthMfaFactor.secret_hash` reste disponible comme propriété dépréciée (émet `DeprecationWarning`) ; sera retiré en Forge 3.0.
- `create_totp_factor()` émet désormais un `UserWarning` unique par processus pour signaler que le secret TOTP est stocké en clair.
- Documentation mise à jour : section "Limites connues MFA" ajoutée à `docs/auth.md`.

### Changements cassants

- **Migration SQL requise** pour les bases existantes : `ALTER TABLE auth_mfa_factors RENAME COLUMN secret_hash TO totp_secret;`
- Tout code utilisant `AuthMfaFactor(secret_hash=...)` doit passer à `AuthMfaFactor(totp_secret=...)`.
- Tout code accédant à `factor.secret_hash` doit passer à `factor.totp_secret` (l'alias émet un `DeprecationWarning`).

### Sécurité

- `core/security/middleware.py` et `mvc/controllers/auth_controller.py` utilisent `hmac.compare_digest()` pour la comparaison des tokens CSRF (SEC-CSRF-CONSTANT-TIME-001).

### Backends de session

- Introduction d'un contrat de session pluggable (`SessionStore` Protocol) avec trois backends : `MemorySessionStore`, `FileSessionStore`, `MariaDbSessionStore` (SESSIONS-CONTRACT-001).
- `core/security/session.py` délègue toutes ses opérations au store actif via l'API publique ; les accès directs `_sessions`/`_lock` ont été supprimés.

### Rate-limit MFA (SEC-MFA-RATELIMIT-001)

- `verify_mfa_challenge` et `verify_mfa_revalidation` appliquent un rate-limit par utilisateur (5 tentatives/5 min pour le challenge, 3/5 min pour la revalidation).
- `core/auth/rate_limit.py` enrichi d'un store in-memory process-local (`record_attempt`, `is_locked_out`, `clear_attempts`, `purge_all_attempts`).
- Nouvel événement d'audit `AUTH_EVENT_MFA_RATE_LIMITED` ("mfa.rate_limited").
- Le lockout retourne la même réponse qu'un échec de code — pas de fuite d'information.

### Anti-replay TOTP (SEC-MFA-TOTP-REPLAY-001)

- `verify_mfa_challenge` et `verify_mfa_revalidation` appliquent RFC 6238 §5.2 : un code TOTP accepté ne peut pas être rejoué dans la même step (30 s).
- Nouveau module `core/auth/totp_replay.py` : store in-memory `factor_id → last_used_step`, thread-safe, avec purge opportuniste toutes les 100 opérations.
- Un replay est traité comme un échec normal (incrémente le rate-limit, pas de fuite d'information).

### Persistence de session MFA (MFA-SESSION-PERSISTENCE-001)

- Correction d'un bug silencieux : les mutations en place sur le dict retourné par `store.get()` étaient perdues pour `FileSessionStore` et `MariaDbSessionStore` (backends désérialisés), alors qu'elles persistaient pour `MemorySessionStore` (référence vivante).
- Nouveau helper `_persist_session_changes(request, *, set_keys, unset_keys)` dans `core/auth/mfa.py` : effectue un cycle read-modify-write explicite sur le store pour garantir la persistence sur tous les backends.
- Fonctions `start_mfa_challenge`, `clear_mfa_challenge`, `mark_mfa_revalidated`, `clear_mfa_revalidation` réécrites pour utiliser ce helper.
- Nouveau méthode `replace(session_id, data)` ajoutée au contrat `SessionStore` et aux trois backends (`MemorySessionStore`, `FileSessionStore`, `MariaDbSessionStore`) : remplace intégralement les données sans merge (contrairement à `set()`).
- `MemorySessionStore.replace()` opère sur le dict interne en place (préserve les références vivantes) via snapshot avant clear.

### Modèles applicatifs — API canonique (SQL-EXAMPLES-CANONICAL-001)

- Les modèles livrés (`mvc/models/auth_model.py`, `mvc/models/mfa_model.py`) et
  les modèles des starters (`carnet-contacts`, `suivi-comportement-eleves`,
  `utilisateurs-auth`) utilisent désormais exclusivement `core.database.db`
  (`fetch_one`, `fetch_all`, `execute`, `insert`).
- Le générateur CRUD (`forge_cli/entities/crud/model_builder.py`) produit
  maintenant du code utilisant l'API canonique. Les opérations M2M multi-statement
  utilisent `transaction()` de `core.database.transaction`.
- `core.database.connection` est documenté comme API interne dans son docstring
  et dans `docs/reference.md` — à n'utiliser que pour les cas avancés
  (transactions complexes, bulk).
- Le code généré par le builder passe de ~12 lignes par fonction à ~2 lignes,
  plus lisible et pédagogique (principe Forge n°11).

### Sécurité — durcissement CSP (SEC-CSP-HARDEN-001)

- Ajout de `object-src 'none'` à la Content Security Policy par défaut.
  Refuse le chargement de plugins legacy (`<object>`, `<embed>`, `<applet>`).
  `default-src 'self'` couvre partiellement ce cas mais `object-src` n'a pas
  de fallback garanti sur Firefox et Safari (certaines versions).
- Ajout de `base-uri 'none'` à la Content Security Policy par défaut.
  Empêche l'injection d'une balise `<base>` qui détournerait toutes les URLs
  relatives de la page (formulaires inclus). `default-src` ne couvre pas
  `base-uri`. Aucun impact sur les applications existantes (Forge n'utilise
  ni `<object>` ni `<base>`).

### OIDC déplacé vers core.auth.experimental (OIDC-SCOPE-CLARIFY-001)

- Les modules `oidc.py` et `oidc_identity.py` sont déplacés dans `core/auth/experimental/`.
- Toutes les classes et fonctions OIDC (`OidcProvider`, `OidcClientConfig`, `OidcExternalIdentity`, `AuthOidcAccount`, `build_oidc_authorization_url`, `validate_oidc_callback`, `start_oidc_login`, etc.) sont retirées de l'API publique `core.auth`.
- Les constantes d'audit `AUTH_EVENT_OIDC_*` restent dans `core.auth` (le mécanisme d'audit est indépendant).
- Un `UserWarning` est émis au premier import depuis `core.auth.experimental.oidc`.
- Les anciens chemins `core.auth.oidc` et `core.auth.oidc_identity` restent fonctionnels comme shims de compatibilité mais émettent un `DeprecationWarning` — ils seront supprimés en Forge 3.0.

**Migration :**
```python
# Avant (supprimé de core.auth)
from core.auth import OidcProvider, build_oidc_authorization_url

# Après
from core.auth.experimental.oidc import OidcProvider, build_oidc_authorization_url
```

**Pourquoi :** OIDC est incomplet (pas d'échange de code, pas de validation JWT/JWKS, pas de claims validation). Exposer du code partiel comme API publique serait trompeur — une API publique est un contrat de complétude (principe Forge n°10).

### Statistiques — suppression des constantes d'événements nommés (STATS-GENERIC-EVENTS-001)

**Rupture d'API publique.**

- Retrait de `core.stats` (et `core.stats.events`) : `PAGE_VIEW`, `CONTACT_CLICK`, `FORM_SUBMIT`, `DOWNLOAD_CLICK`, `EXTERNAL_LINK_CLICK`, `MEDIA_VIEW`, `is_known_event_name()`, `_KNOWN_EVENT_NAMES`.
- Les noms d'événements sont de simples chaînes `snake_case` définies par l'application — Forge ne préconise aucune liste.

**Migration :**
```python
# Avant
from core.stats import PAGE_VIEW, track_event
track_event(db.execute, PAGE_VIEW, label="Vue")

# Après
from core.stats import track_event
track_event(db.execute, "page_view", label="Vue")
```

**Pourquoi :** Nommer les événements applicatifs dans le framework viole le Principe 1 de la Charte Forge (le framework n'est pas l'application). Une application de gestion de communes ne partage aucun vocabulaire métier avec une boutique en ligne. Les chaînes restent valides comme noms d'événements, elles ne sont simplement plus des constantes exportées.

## [2.3.0] — 2026-05-10

### Ajouté — Phase 13 CRUD avancé (close)

- Filtres déclaratifs CRUD (`list.filter=true`) avec génération automatique de `<select>` et `<input>` (CRUD-FILTER-001, CRUD-FILTER-HTMX-001, CRUD-FILTER-DOC-001).
- Tri sécurisé par whitelist (`_ALLOWED_SORT`) avec liens HTMX progressifs et fallback `<a href>` (CRUD-SORT-001).
- Consolidation HTMX CRUD : cible unique `#crud-results`, `hx-swap="innerHTML"`, `hx-push-url="true"` cohérents sur pagination, tri, filtres et reset (CRUD-HTMX-001).
- Suppression groupée minimale : cases à cocher HTML5 (`form=`), confirmation, CSRF automatique, RBAC optionnel, SQL paramétrée `IN(?,?,?)` (CRUD-BULK-DELETE-001).
- Export CSV filtré : route `GET /{plural}/export.csv`, `_EXPORT_LIMIT=1000`, `_csv_escape` (protection injection CSV OWASP), `Cache-Control: no-store`, RBAC via permission `index`, lien `<a href>` classique sans HTMX (CRUD-EXPORT-CSV-001).
- Documentation `docs/reference.md` : sections tri, HTMX CRUD, suppression groupée, export CSV.

### Version figée

Forge 2.3.0 fige l'état post Phase 13 avant une refonte/consolidation profonde ultérieure.

## [2.2.0] — 2026-05-09

### Ajouté

- Tests HTTP E2E via subprocess sur un serveur réel (HTTP-E2E-TESTS-001) : 21 tests couvrant routes, en-têtes de sécurité, fichiers statiques, traversée de chemin, nonce CSP.
- Tests de concurrence sur `MemorySessionStore` et helpers legacy (CONCURRENCY-SESSION-TESTS-001) : 14 tests avec 50 threads concurrents.
- Endpoint de santé `GET /health` → `{"status": "ok"}` 200 JSON (HEALTH-ENDPOINT-001).
- Audit contractuel des profils de projet et tableau comparatif dans `docs/reference.md` (PROFILE-DIFFERENTIATION-001).

### Tests

- Ajout de `tests/test_http_e2e_001.py`.
- Ajout de `tests/_e2e_launcher.py`.
- Ajout de `tests/test_concurrency_session_001.py`.
- Ajout de `tests/test_health_endpoint_001.py`.
- Ajout de `tests/test_profile_differentiation_001.py`.

## [2.1.0] — 2026-05-09

### Modifié

- Dépréciation officielle du dossier legacy `cmd/` avec avertissement à l'exécution (CMD-LEGACY-DEPRECATION-001).
- Clarification de la frontière entre `core.auth` (API officielle) et `core.security` (compat/transversal) (AUTH-LEGACY-BOUNDARY-001).
- Découpage interne de `make_crud.py` (2396 lignes) en sous-modules `forge_cli/entities/crud/` sans changement fonctionnel (CRUD-GENERATOR-SPLIT-001).
- Ajout d'un cache `lru_cache` aux catalogues de traduction i18n, avec `clear_translation_cache()` (I18N-CACHE-001).
- Intégration de `ruff` (règles E+F) comme validation qualité Python dans la CI et la checklist de release (QUALITY-RUFF-001).

### Documentation

- Mise à jour de `cmd/README.md` avec tableau d'équivalences et notice de dépréciation.
- Mise à jour de `docs/auth.md` avec la section frontière API officielle / legacy.
- Mise à jour de `docs/reference.md` : cache i18n, `clear_translation_cache()`, frontière auth.
- Mise à jour de `docs/release.md` avec l'étape Ruff dans la checklist.

### Tests

- Ajout de `tests/test_cmd_legacy_deprecation_001.py`.
- Ajout de `tests/test_auth_legacy_boundary_001.py`.
- Ajout de `tests/test_crud_generator_split_001.py`.
- Ajout de `tests/test_i18n_cache_001.py`.
- Ajout de `tests/test_quality_ruff_001.py`.

## [2.0.2] — 2026-05-09

### Documentation

- Nettoyage des incohérences documentaires post-2.0.1 (POST-2.0-DOC-CLEANUP-001).
- Restructuration de la roadmap active post-2.0, extraction de l'historique dans `docs/history/` (POST-2.0-ROADMAP-RESTRUCTURE-001).
- Ajout d'une politique de sécurité publique `SECURITY.md` (SECURITY-MD-001).
- Ajout d'une checklist de release officielle `docs/release.md` (RELEASE-CHECKLIST-001).

### Sécurité

- Ajout d'un audit de dépendances Python avec `pip-audit` (DEPENDENCY-SCAN-001).
- Ajout d'un workflow GitHub Actions non bloquant pour le scan de dépendances hebdomadaire.

### Tests

- Ajout de tests documentaires liés à `SECURITY.md`, `pip-audit` et à la checklist de release.

---

## [2.0.1] — 2026-05-09

### Corrigé

- Alignement de l'authentification par défaut sur `core.auth` et Argon2id (AUTH-DEFAULT-ALIGN-001).
- Ajout d'un test de non-régression CLI Auth → login (AUTH-CLI-LOGIN-E2E-TEST-001).
- Audit et alignement Auth des starters — élimination des usages PBKDF2 legacy (STARTERS-AUTH-AUDIT-001).
- Whitelist des clés de filtres dans le CRUD généré — prévention injection SQL (CRUD-FILTER-WHITELIST-001).
- Durcissement du PBKDF2 legacy : format versionné, 600 000 itérations, fonction `pbkdf2_needs_rehash` (SECURITY-PBKDF2-HARDENING-001).
- Migration transparente PBKDF2 → Argon2id après login réussi (AUTH-HASH-MIGRATION-001).
- Documentation claire des limites des sessions mémoire et warning runtime (DEPLOY-SESSION-LIMITS-001).
- Formalisation des décisions d'architecture Auth et Session (ADR-001, ADR-002).

---

## 2.0.0

Version de publication officielle. Forge 2.0.0 marque la fin de la phase Alpha et l'entrée en Beta.

### Ajouté

- Phase 4.5 complète : authentification avancée (Auth/User, sessions, MFA TOTP, codes de récupération, OIDC, interface admin utilisateurs).
- Phase 6 complète : pages publiques génériques (`make:public-page`, `make:public-list`, `make:public-show`, `make:public-form`, `make:public-contact`).
- Starters intégrés dans le wheel : contacts, utilisateurs-auth, blog, portfolio, communes-séjours.
- Commande `forge starter:build` pour installer un starter en local sans réseau.

### Modifié

- `Development Status` PyPI : `3 - Alpha` → `4 - Beta`.
- Référence stable par défaut : `v1.5.0` → `v2.0.0`.

---

## 1.5.0

Version de stabilisation de la phase 3 : socle front léger, JavaScript optionnel, internationalisation simple et templates standardisés.

### Ajouté

- Structure JavaScript applicative standard avec `static/js/app.js`.
- Commandes :
  - `forge js:init htmx`
  - `forge js:init alpine`
  - `forge js:init htmx-alpine`
- Support local optionnel de HTMX et Alpine.js via `static/vendor/`.
- Zone `{% block scripts %}` dans les layouts.
- Documentation HTMX et Alpine.js.
- Socle i18n :
  - `core/i18n`
  - `translations/fr.json`
  - `trans()` côté Python
  - `trans()` dans Jinja
  - langue par défaut configurable
  - fallback i18n
- Commandes :
  - `forge i18n:init`
  - `forge i18n:check`
- Utilisation de clés i18n génériques dans les templates CRUD générés.
- Layouts standards :
  - `mvc/views/layouts/public.html`
  - `mvc/views/layouts/admin.html`
- Composants Jinja de base :
  - button
  - alert
  - form_field
  - table
  - badge
  - pagination
- Boutons CRUD standardisés.
- Messages flash standardisés.
- États vides dans les listes CRUD.
- Confirmations natives de suppression CRUD.

### Limites connues

- HTMX et Alpine.js sont préparés mais non injectés automatiquement.
- Les CRUD dynamiques HTMX viendront plus tard.
- Seul `translations/fr.json` est fourni.
- Pas encore de langue par session ou par requête.
- Les composants ne sont pas encore utilisés partout.
- RBAC non commencé.

## 1.4.0

### Ajouté
- Migrations SQL versionnées.
- Table technique `forge_migrations` créée par `forge db:init`.
- Commande `forge migration:status`.
- Commande `forge migration:apply`.
- Commande `forge migration:make <nom>`.
- Génération de migration depuis une entité avec `--from-entity`.
- Génération de migration depuis toutes les entités avec `--from-entities`.
- Diff de schéma en lecture seule avec `forge migration:diff --entity`.
- Génération prudente depuis diff avec `--from-diff`.
- Documentation dédiée `docs/migrations.md`.

### Sécurité / prudence
- Refus automatique des diffs risqués `COLUMN_CHANGED` et `COLUMN_EXTRA`.
- Pas de `DROP COLUMN`, `MODIFY COLUMN` ou `CHANGE COLUMN` automatique.
- Pas de rollback prétendu sur les DDL MariaDB.
- SQL visible et relu avant application.

## 1.3.0

Version mineure centrée sur la stabilisation complète de Média v2 côté serveur.

- Suppression automatique des médias liés lors du destroy d'une entité CRUD.
- Conservation du contexte média dans les vues edit et après erreur de validation.
- Ajout du champ alt_text générique aux médias.
- Gestion de alt_text dans le CRUD généré.
- Support des galeries multiple=true en lecture.
- Ajout append-only de médias dans une galerie.
- Suppression individuelle des médias de galerie.
- Ajout d'une position numérique et réorganisation simple des galeries.
- Support du multi-upload HTML multiple pour les galeries.
- Validation serveur de chaque fichier d'un multi-upload avant tout accès DB.
- Ajout d'un test d'intégration média complet avec storage temporaire.
- Documentation Média v2, CRUD et référence mises à jour.

## 1.2.1

Version corrective de stabilisation.

- Correction de `Form.from_request` pour transmettre `request.body` et `request.files`.
- Ajout de `Pillow>=10.0,<12` dans les dépendances projet (`requirements.txt` et `pyproject.toml`).
- Retrait du GIF des formats image acceptés par défaut (`ImageField`, `save_image`).
- Ajout de tests runtime pour le CRUD média généré (exécution réelle avec mocks).
- Documentation alignée avec l'état réel 1.2.1 (CRUD média, relations, roadmap).
- Nettoyage des règles `.gitignore` pour les artefacts `build/`, `.mypy_cache/`, `.ruff_cache/`.

## [1.2.0] - CRUD enrichi, formulaires avancés et mail générique

### Ajouté
- Stabilisation de `core.forms` et des champs avancés de formulaire.
- Métadonnée `form.field` dans les JSON d'entités pour piloter les champs générés.
- Génération CRUD avec `EmailField`, `PhoneField`, `UrlField`, `TextAreaField`, `SlugField`, `DateField` et `DateTimeField`.
- Recherche `q` dans les listes CRUD générées.
- Pagination `page` avec `per_page=20`.
- Filtres simples déclarés avec `list.filter`.
- Filtres relationnels `many_to_one` depuis `relations.json`.
- Select relationnels dans les listes CRUD, avec libellé déduit du premier champ textuel de l'entité liée.
- `MailMessage` — représentation d'un message (sujet, corps texte/HTML, destinataires multiples).
- `Mailer` — point d'entrée unique pour envoyer un message via le transport configuré.
- Transports interchangeables : `NullTransport`, `FakeTransport`, `ConsoleTransport`, `LogTransport`, `SmtpTransport`.
- `MailTemplateRenderer` — rendu Jinja2 de templates mail (`*_subject.txt`, `*_text.txt`, `*_html.html`).
- `MailLogger` et table SQL `mail_log` — journalisation optionnelle des envois (sans corps du message).
- Variables d'environnement : `MAIL_TRANSPORT`, `MAIL_LOG_ENABLED`, `MAIL_FROM_ADDRESS`, `MAIL_FROM_NAME`.
- Commandes CLI :
  - `forge mail:init` — crée `mvc/mail/templates/`, `storage/mail/` et génère `mail_log.sql`.
  - `forge mail:test --to <email>` — envoie un message de test via le transport configuré.
  - `forge mail:render <template> [--context ctx.json]` — affiche le rendu d'un template sans envoyer.
  - `forge mail:doctor` — vérifie la cohérence de la configuration mail.
  - `forge mail:logs [--limit N]` — affiche les derniers enregistrements de `mail_log`.

### Sécurité
- Protection contre l'injection de headers dans `MailMessage` (`_NEWLINE_RE`).
- `MAIL_ENABLED=false` par défaut dans `env/example` — aucun envoi réel sans activation explicite.
- `MAIL_TRANSPORT=log` par défaut — les mails de développement sont écrits en `.eml`, pas envoyés.

### Tests
- Suite mail : `tests/test_mail.py`, `tests/test_mail_transports.py`, `tests/test_mailer.py`,
  `tests/test_mail_templates.py`, `tests/test_mail_cli.py`, `tests/test_mail_log.py`.

### Compatibilité
- `SMTPMailer` (`core/mail/smtp.py`) conservé provisoirement. Le système recommandé est `Mailer + SmtpTransport`.
- `FileField` et `ImageField` existent dans `core.forms` ; leur intégration à `make:crud` est désormais assurée via la clé `"media"` dans `entity.json` (voir `[Unreleased] - Média v2`).

## [1.1.0] - Socle média

### Ajouté
- `save_image`, `MediaRecord`, `image_variant_paths` — service générique d'upload image.
- `forge media:init` — initialisation des dossiers variantes (`thumbnail/`, `medium/`).
- Documentation `docs/media.md`.

## [1.0.1] - Stabilisation

### Corrigé
- Alignement de la version Forge en 1.0.1.
- Inclusion complète des fichiers starters dans le package Python.
- Correction de la gestion des fichiers statiques pour éviter une erreur 500 sur `/static/`.
- Sécurisation de `forge new` : un échec du commit Git initial ne supprime plus le projet généré.
- Nettoyage de l'incohérence entre le layout Jinja réel et la documentation.

### Documentation
- Clarification de l'usage du layout Jinja.
- Mise à jour des références de version.

## 1.0.0

Version initiale stable de Forge.

Fonctionnalités principales :
- framework Python MVC minimal
- routeur HTTP
- contrôleurs / vues / modèles
- entités JSON canoniques
- génération SQL visible
- génération de CRUD
- sessions
- CSRF
- erreurs HTTP propres
- upload local sécurisé
- déploiement minimal guidé
- starter-apps
- documentation MkDocs avec recherche
