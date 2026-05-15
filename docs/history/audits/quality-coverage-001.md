# Audit QUALITY-COVERAGE-001 — Couverture qualité Forge

**Date :** 9 mai 2026  
**Version Forge :** 2.2.0  
**Commit de référence :** `0bb69c8`

---

## Objectif

Réaliser un audit qualitatif de la couverture de tests après la phase E2E (tickets E2E-CLI-001 à E2E-MARIADB-001).  
Identifier les zones bien couvertes, partiellement couvertes, non couvertes, les tests fragiles et les risques avant la phase sécurité.

---

## Résumé exécutif

Forge 2.2.0 dispose de **215 fichiers de test** pour **~6031 tests collectés** (5772 fonctions test, le delta vient des fixtures et de la paramétrisation).  
La couverture est **forte sur le cœur fonctionnel** (auth, CRUD, CLI) et **faible sur les scénarios réels end-to-end** (HTTP avec formulaires, MariaDB en CI, déploiement).  
La phase sécurité peut commencer, mais elle doit prioriser les flux HTTP réels avant les tests unitaires supplémentaires.

---

## État global des tests

| Métrique | Valeur |
|---|---|
| Fichiers de test | 215 |
| Tests collectés (pytest) | 6031 |
| Tests skipped | 2 (1 legacy + E2E MariaDB module entier) |
| Tests opt-in (MariaDB) | 14 |
| Tests documentaires estimés | ~400 |
| Tests fortement mockés | ~7 fichiers significatifs |
| Fichiers de support | 4 (`conftest.py`, `_e2e_launcher.py`, `fake_request.py`, `__init__.py`) |

---

## Couverture par famille

| Famille | Fichiers | Tests | Niveau |
|---|---|---|---|
| Auth / RBAC / MFA / OIDC | 46 | 1452 | Fort |
| CRUD (générateurs + pages publiques) | 30 | 799 | Fort |
| CLI (doctor, check, audit, help, errors) | 17 | 591 | Fort |
| Stats / Workflow | 7 | 256 | Fort |
| Starters | 2 (+3 CLI) | 243 | Fort (partiel E2E) |
| Modules | 9 | 220 | Fort |
| Templates / Front | 9 | 209 | Moyen |
| Mail | 6 | 192 | Moyen |
| Uploads / Média | 8 | 171 | Moyen |
| Runtime errors (JSONL/MD) | 4 | 164 | Fort |
| Release / Packaging | 12 | 167 | Documentaire |
| Docs / Consolidation | 7 | 110 | Documentaire |
| Session | 4 | 100 | Moyen |
| Entités | 11 | 240 | Moyen |
| Migrations / DB | 4 | 115 | Faible (mocks) |
| i18n | 3 | 67 | Moyen |
| Relations | 3 | 67 | Faible (pas d'E2E) |
| HTTP / Router | 7 | 74 | Faible (pas de formulaires) |
| Sécurité (TLS, CSP, hachage) | 4 | 75 | Partiel |
| **E2E dédiés** | **6** | **151** | Voir ci-dessous |

---

## Zones fortement couvertes

### Auth / RBAC / MFA / OIDC (1452 tests)
La zone la mieux couverte du projet. Contrats d'interface, tables SQL, sessions, tokens, hachage, email verification, reset password, MFA (TOTP, codes de récupération, revalidation, challenge), OIDC (flux complet, state/nonce/PKCE, association compte), admin CLI, rate limiting, RBAC routes/templates/SQL/Jinja. Tests unitaires denses avec une bonne séparation des responsabilités.

### CRUD generators (799 tests)
Génération de contrôleur, modèle, formulaire, vues, pages publiques, pagination, recherche, tri, HTMX (suppression, pagination, recherche), médias (galerie, alt, multiupload, ordre), M2M. Tests de génération de code couverts unitairement et par contrats de fichiers.

### CLI (591 tests)
`forge doctor`, `project:check`, `project:audit`, aide, erreurs, récupération, entrypoint, starters CLI, modules CLI, mail CLI, i18n CLI, deploy CLI. Bonne couverture des messages et des codes de sortie.

### Modules (220 tests)
Manifeste (validation, sécurité, chemins), registre, découverte, installation, fichiers, routes, suppression, cycle de vie documenté, CLI. Complété par `test_e2e_module.py` (29 tests E2E).

### Runtime errors JSONL/Markdown (164 tests)
Schéma documenté, collecteur JSONL, rendu Markdown, audit des erreurs. Couverture complète du pipeline.

---

## Zones partiellement couvertes

### Entités (240 tests)
Validation JSON, formulaires, filtres de liste, médias déclarés — bons. Mais `make:entity` et `sync:entity` en interactif sont peu testés (8 tests dans `test_make_entity_command.py`, fortement mockés). Pas d'E2E pour l'entité seule hors `test_e2e_cli.py`.

### Migrations (115 tests)
`test_migrations.py` (63 tests) est fortement mocké (9 références mock/monkeypatch). La vraie application sur MariaDB n'est testée qu'en opt-in (`test_e2e_mariadb.py`). `migration:diff` (comparaison entité/MariaDB) reste non testée en conditions réelles.

### Starters (243 tests)
Starters 1 et 3 testés en génération E2E complète avec `project:check` et `project:audit`. Les starters 2, 4, 5 ne sont testés qu'en CLI (existence, métadonnées, résolution) et en consolidation (contrats documentaires) — aucun build E2E complet pour ces starters.

### Sécurité HTTP (75 tests dédiés + épars)
CSP nonce (26 tests), TLS par défaut (19 tests), hachage argon2 (24 tests) — couverts. Mais :
- Headers de sécurité validés en E2E réel (`test_http_e2e_001.py`) uniquement sur une app de test minimale ;
- Cookies de session (HttpOnly, SameSite, Secure) testés partiellement dans session/middleware ;
- CSRF testé en unitaire, mais aucun flux HTTP complet avec soumission de formulaire et vérification du token.

### Templates / Front (209 tests)
Rendu Jinja (37 tests), composants, layouts, flash, doc templates — couverts unitairement. Mais aucun test de rendu avec données réelles via HTTP. Les vues CRUD générées ne sont jamais chargées dans un contexte HTTP réel.

### Session (100 tests)
Contrat store, FileStore (41 tests), MemoryStore (20 tests), concurrence (14 tests), MariaDbStore mocké (40 tests). Les backends FileStore et MariaDbStore ne sont pas testés avec un vrai système de fichiers ou une vraie MariaDB en CI.

### Uploads / Média (171 tests)
Galerie, repository, route, delete, attach — bien couverts unitairement. Mais `test_media_integration.py` ne contient que 5 tests. Aucun parcours HTTP complet d'upload d'un fichier (multipart form → stockage → retour URL).

---

## Zones non couvertes ou insuffisantes

### MariaDB réelle en CI
`test_e2e_mariadb.py` est opt-in (`FORGE_E2E_MARIADB=1`). La vérification que le SQL généré par Forge est réellement applicable à MariaDB ne s'exécute pas en CI standard.

### Starters 2, 4, 5 en build complet
Les starters 2 (gestion bibliothèque), 4 (portfolio) et 5 (communes et séjours — couvert séparément dans `test_starter_communes_sejours.py` mais sans `project:check` après build) n'ont pas de test E2E de génération complète equivalent à `TestStarter1Crud` et `TestStarter3Application`.

### HTTP avec formulaires réels
Aucun test ne soumet un vrai formulaire HTTP via le serveur Forge. Les tests CRUD mockent les requêtes via `fake_request.py`. La validation CSRF ne traverse jamais un vrai cycle HTTP dans les tests.

### Auth login/logout/MFA via HTTP réel
`test_auth_cli_to_login_e2e.py` ne contient que 6 tests, focalisés sur le flux CLI. Aucun test de login/logout/MFA via le serveur HTTP démarré réellement.

### `forge deploy:init` / `forge deploy:check` en conditions réelles
`test_deploy_cli.py` contient 24 tests mais 6 références monkeypatch. Aucun vrai déploiement n'est testé.

### `migration:diff`
La commande `forge migration:diff` (comparaison entité JSON / colonnes MariaDB réelles) n'est testée qu'en CLI moqué. Jamais testée contre une vraie MariaDB.

### Path traversal et injection SQL dans les modèles
Le filtre whitelist CRUD est testé (`test_crud_filter_whitelist_001.py`). Les modules testent l'injection de routes. Mais les modèles générés (`*_model.py`) ne sont jamais testés contre de vraies requêtes SQL paramétrées.

---

## Tests E2E existants

| Ticket | Fichier | Tests | Activation |
|---|---|---|---|
| E2E-CLI-001 | `test_e2e_cli.py` | 27 | Standard |
| E2E-NON-OVERWRITE-001 | `test_e2e_non_overwrite.py` | 20 | Standard |
| E2E-STARTER-001 | `test_e2e_starter.py` | 42 | Standard (DB mockée) |
| E2E-MODULE-001 | `test_e2e_module.py` | 29 | Standard |
| E2E-MARIADB-001 | `test_e2e_mariadb.py` | 14 | Opt-in (`FORGE_E2E_MARIADB=1`) |
| HTTP-E2E-TESTS-001 | `test_http_e2e_001.py` | 21 | Standard (serveur auto-démarré) |

**Total E2E : 153 tests (139 standard + 14 opt-in)**

---

## Tests E2E manquants

| Scénario | Priorité | Ticket suggéré |
|---|---|---|
| Build complet starters 2, 4, 5 + project:check | Haute | `E2E-STARTER-002` |
| Login/logout/MFA via HTTP réel | Haute | `E2E-AUTH-HTTP-001` |
| Upload fichier via HTTP réel (multipart) | Moyenne | `E2E-UPLOAD-HTTP-001` |
| CRUD formulaire via HTTP réel (soumission + CSRF) | Moyenne | `E2E-CRUD-HTTP-001` |
| Migration appliquée sur MariaDB réelle en cycle CLI | Basse | Extension de `E2E-MARIADB-001` |

---

## Tests opt-in

| Fichier | Condition | Raison |
|---|---|---|
| `test_e2e_mariadb.py` | `FORGE_E2E_MARIADB=1` | MariaDB non disponible en CI standard |
| `test_http_e2e_001.py` | Auto (serveur démarré) | Peut être lent ou échouer si port occupé |
| `test_health_endpoint_001.py` | Partiel skip | Dépend du serveur disponible |
| `test_serve_static.py` | 1 skip | Cas d'environnement spécifique |

---

## Tests fragiles ou à surveiller

| Fichier | Fragilité | Références mock |
|---|---|---|
| `test_cli_entrypoint.py` | Dispatcher entièrement mocké | 43 |
| `test_forge_new.py` | `forge new` entièrement mocké, pas de projet réel | 38 |
| `test_auth_admin_cli.py` | Admin CLI mocké | 27 |
| `test_mail_log.py` | Log mail mocké | 19 |
| `test_module_cli.py` | CLI modules mocké (séparé de l'E2E) | 18 |
| `test_cli_recovery.py` | Recovery entièrement mocké | 15 |
| `test_migrations.py` | Migrations mockées (pas de vraie DB) | 9 |
| `test_module_lifecycle_doc_001.py` | 19/19 tests documentaires sur `docs/reference.md` | — |
| `test_consolidation_starter_001.py` | 51 tests documentaires sur présence de fichiers | — |

**Risque principal :** Les tests fortement mockés valident le chemin heureux du code mais ne détectent pas les régressions de l'interface réelle (messages d'erreur exact, comportement en mode interactif, saisie utilisateur). Ils peuvent casser si les mocks ne sont pas synchronisés avec les refactorings internes.

---

## Risques qualité avant la phase sécurité

1. **CSRF non testé en HTTP réel.** Le token CSRF est validé unitairement mais aucun test ne vérifie qu'un formulaire généré contient un token valide et qu'une requête sans token est rejetée avec un vrai serveur.

2. **Headers de sécurité vérifiés sur une app minimale.** `test_http_e2e_001.py` démarre une app de test, pas une vraie app Forge générée avec entités/CRUD. Un bug dans les headers sur un contrôleur métier peut passer inaperçu.

3. **Cookies de session non audités sur toutes les routes.** HttpOnly et SameSite sont vérifiés à la création de session, pas sur chaque réponse avec un cookie présent.

4. **Migrations mockées.** Un bug de SQL réel (type incompatible, index en double, contrainte FK) ne sera détecté qu'en opt-in. La phase sécurité pourrait introduire des migrations SQL (`user_roles`, `auth_audit`) qui ne sont jamais testées.

5. **Starters 2/4/5 sans E2E complet.** Si un refactoring casse le générateur de starter, les starters non couverts en E2E ne seraient détectés qu'à l'exécution manuelle.

6. **Upload HTTP complet non testé.** Un audit sécurité upload (MIME spoofing, path traversal, taille) nécessite un vrai cycle HTTP multipart que les tests actuels ne fournissent pas.

7. **Module OIDC : contrat fort mais flux HTTP absent.** OIDC est très bien testé unitairement (197 tests) mais aucun serveur OAuth/OIDC de test n'est utilisé dans les tests.

---

## Recommandations

### Priorité 1 — Avant SECURITY-AUDIT-001

1. **Vérifier CSRF sur un cycle HTTP réel minimal** (ajout à `test_http_e2e_001.py` ou nouveau ticket `E2E-CSRF-001`).
2. **Tester les headers de sécurité sur une app avec contrôleur CRUD** (pas seulement une app vide).
3. **Lancer `test_e2e_mariadb.py` en CI** pour les branches de migration, ou créer une issue de CI.

### Priorité 2 — Avant la prochaine phase E2E

4. **Ajouter un E2E complet pour les starters 2 et 4** (`E2E-STARTER-002`).
5. **Tester un login/logout Auth via HTTP réel** (`E2E-AUTH-HTTP-001`).
6. **Ajouter un test d'upload via HTTP réel** (`E2E-UPLOAD-HTTP-001`).

### Priorité 3 — Dette technique à surveiller

7. **Réduire les mocks dans `test_forge_new.py`** en utilisant la même approche d'échafaudage que `test_e2e_cli.py`.
8. **Synchroniser les tests documentaires** avec la documentation (risque de faux positifs si les textes changent).
9. **Activer coverage.py** (non présent actuellement) si un audit de couverture ligne est décidé.

---

## Tickets proposés

| Ticket | Priorité | Description |
|---|---|---|
| `SECURITY-AUDIT-001` | P1 | Audit de sécurité global (prochaine étape) |
| `E2E-CSRF-001` | P1 | Test CSRF sur cycle HTTP réel |
| `E2E-STARTER-002` | P2 | Build E2E complet starters 2 et 4 |
| `E2E-AUTH-HTTP-001` | P2 | Login/logout/MFA via serveur HTTP démarré |
| `E2E-UPLOAD-HTTP-001` | P3 | Upload fichier via HTTP réel |
| `E2E-CRUD-HTTP-001` | P3 | CRUD formulaire via HTTP réel |
| `QUALITY-COVERAGE-002` | P3 | Réduire mocks dans forge_new et cli_entrypoint |

---

*Rapport généré dans le cadre du ticket QUALITY-COVERAGE-001 — Forge 2.2.0 — 2026-05-09.*
