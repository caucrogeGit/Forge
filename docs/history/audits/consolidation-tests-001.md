# Audit CONSOLIDATION-TESTS-001 — Couverture et zones fragiles des tests Forge

## Objectif

Auditer la cohérence globale de la suite de tests Forge avant publication. Identifier les zones bien couvertes, partiellement couvertes ou absentes. Ne rien corriger.

---

## Synthèse

**Verdict : la suite de tests Forge est robuste et fiable.**

168 fichiers de tests, 4824 tests passés, 1 skipped. Couverture fonctionnelle très complète sur Auth, CRUD, modules et pages publiques. Les générateurs sont bien testés. Les profils et starters sont couverts. La non-régression CLI est assurée.

Deux zones méritent attention avant publication : le non-écrasement du code utilisateur est couvert de façon diffuse (via la propriété `preserved` dans les retours des générateurs) sans fichier de test dédié et sans scénario end-to-end complet ; les limites des modules (rollback, `module:remove`, `module:update`) ne sont pas testées car ces fonctionnalités n'existent pas.

Aucune zone critique non couverte. Aucun test fragile (temps, aléatoire) identifié.

---

## Méthode d'audit

- Inventaire des fichiers de tests (`find tests -maxdepth 1 -name "test_*.py"`)
- Comptage des fonctions `def test_` et des tests collectés par pytest
- Comptage croisé par famille (auth, crud, modules, starters, profils, etc.)
- Recherche de patterns fragiles (sleep, random, datetime.now, subprocess)
- Recherche des patterns de non-écrasement (overwrite, preserve, _base)
- Lecture des fichiers tests clés

---

## Volume global de tests

| Indicateur | Valeur |
|------------|--------|
| Fichiers de tests | 168 |
| Fonctions `def test_` | 4 577 |
| Tests collectés par pytest | 4 825 (avec paramétrisations) |
| Tests passés | 4 824 |
| Tests skipped | 1 |
| Tests en échec | 0 |

Les 248 tests supplémentaires (4825 − 4577) proviennent de `@pytest.mark.parametrize`.

---

## Familles de tests auditées

| Famille | Fichiers dédiés | Fichiers avec contenu | Total estimé |
|---------|----------------|----------------------|--------------|
| Auth / User | 36 fichiers `test_auth_*` | 57 fichiers au total | ~800 tests |
| RBAC | couplé auth | 26 fichiers | — |
| CRUD | 22 fichiers `test_make_crud_*` | 43 fichiers | 659 tests |
| Modules | 7 fichiers `test_module_*` | 58 fichiers | 188 tests |
| Starters | 2 fichiers `test_starter_*` | 8 fichiers | 310 tests |
| Pages publiques | 7 fichiers `test_make_public_*` | 9 fichiers | 164 tests |
| Profils | 2 fichiers dédiés | 8 fichiers | ~35 tests |
| Sécurité / sessions | — | 68 fichiers | — |
| Migrations / DB | 7 fichiers | 7 fichiers | — |
| Front / i18n | — | 24 fichiers | — |
| Entités / modèles | 5 fichiers | 5 fichiers | — |
| Non-écrasement | diffus | 70 fichiers | — |
| Documentation | 4 fichiers | — | ~55 tests |

---

## Couverture Core

**HTTP / Router :** testé dans `test_router.py`, `test_request_body.py`, `test_response.py`, `test_serve_static.py`. Routing, parsing de requête, réponses HTTP couverts.

**Templating Jinja2 :** couvert via les tests de générateurs (chaque générateur vérifie le contenu des templates produits).

**Validation :** `test_validator.py`, `test_validation_decorators.py` — couverture suffisante pour un module à 3 fichiers.

**Application startup :** `test_application.py` — présent.

**Conclusion :** le core est bien couvert par les tests des briques qui s'appuient dessus (generateurs, auth, CRUD).

---

## Couverture CLI

**CLI générale :** `test_cli_entrypoint.py` — entrée CLI testée.

**forge doctor :** `test_doctor.py` — présent.

**forge new :** `test_forge_new.py` — création de projet avec profils testée.

**forge routes:list :** couvert dans les tests de générateurs (routes injectées).

**Non-régression :** les tests de chaque commande vérifient les fichiers générés et les messages de sortie.

**Conclusion :** couverture CLI correcte. Les commandes récentes (`forge new --profile`, `auth:user:role:*`, `module:*`) sont testées dans leurs modules respectifs.

---

## Couverture Entités / Modèles

5 fichiers dédiés :
- `test_make_entity_command.py` — 8 tests (génération entité)
- `test_entity_json_schema.py`, `test_entity_model.py`, `test_entity_db_init.py`, `test_entity_db_apply.py`
- `test_make_relation_command.py` — 5 tests (relations)
- `test_sync_landing.py` — 8 tests (sync landing page)

**Couverture :** suffisante pour les briques make:entity / sync:entity. `build:model` et `check:model` sont moins visibles dans les noms de fichiers — à vérifier dans CONSOLIDATION-CLI-001 (hors périmètre ici).

---

## Couverture CRUD

**22 fichiers, 659 tests. Couverture exceptionnelle.**

| Aspect | Fichier | Tests |
|--------|---------|-------|
| CRUD de base | test_make_crud.py | 172 |
| Médias / galeries | test_make_crud_media.py | 157 |
| RBAC intégré | test_make_crud_rbac.py | 34 |
| Multiupload galerie | test_make_crud_media_gallery_multiupload.py | 40 |
| Many-to-many | test_make_crud_many_to_many.py | 11 |
| Pagination | test_make_crud_pagination.py | 13 |
| HTMX delete | test_make_crud_htmx_delete.py | 9 |
| HTMX pagination | test_make_crud_htmx_pagination.py | 8 |
| HTMX search | test_make_crud_htmx_search.py | 9 |
| Recherche | test_make_crud_search.py | 9 |
| Tri | test_make_crud_sort.py | 13 |
| États vides | test_make_crud_empty_states.py | 15 |
| Partials | test_make_crud_partials.py | 6 |
| (+ 9 autres) | — | — |

---

## Couverture Auth / User

**36 fichiers dédiés. Couverture très complète.**

| Aspect | Fichier(s) | Tests |
|--------|-----------|-------|
| OIDC flow | test_auth_oidc_flow.py | 100 |
| OIDC contrat | test_auth_oidc_contract.py | 97 |
| MFA codes récupération | test_auth_mfa_recovery_codes.py | 84 |
| MFA revalidation | test_auth_mfa_revalidation.py | 73 |
| MFA challenge | test_auth_mfa_challenge.py | 65 |
| MFA TOTP | test_auth_mfa_totp.py | 64 |
| MFA contrat | test_auth_mfa_contract.py | 50 |
| Admin CLI | test_auth_admin_cli.py | 40 |
| Contrat utilisateur | test_auth_user_contract.py | 39 |
| Reset password | test_auth_password_reset.py | 45 |
| Session / helpers | test_auth_session.py, test_auth_session_helpers.py | — |
| Tokens | test_auth_tokens.py, test_auth_token_table.py | — |
| Rate-limiting | test_auth_rate_limit.py, test_auth_rate_limit_table.py | — |
| Audit auth | test_auth_audit.py, test_auth_audit_table.py | — |
| Email vérification | test_auth_email_verification.py | — |
| RBAC utilisateur | test_auth_user_rbac.py, test_auth_user_rbac_resolver.py, test_auth_user_rbac_route.py | — |
| Rôles CLI | test_auth_admin_roles_cli.py | — |
| OIDC account | test_auth_oidc_account.py, test_auth_oidc_account_table.py, test_auth_oidc_identity.py | — |

**Couverture MFA :** TOTP, codes de récupération, challenge, revalidation — tous couverts.
**Couverture OIDC :** flow complet, contrat, association compte — couvert.
**Couverture sessions :** login, logout, `@login_required`, `current_user` — couvert.

---

## Couverture RBAC

Couverture RBAC présente dans 26 fichiers — intégrée dans les tests auth et CRUD :

- `test_rbac.py`, `test_rbac_middleware.py` — couverture core RBAC.
- `test_make_crud_rbac.py` (34 tests) — RBAC injecté dans les générateurs CRUD.
- `test_auth_user_rbac.py`, `test_auth_user_rbac_resolver.py`, `test_auth_user_rbac_route.py` — RBAC côté Auth/User.

**Helpers Jinja** (`can(...)`) : couverts dans les tests de templates CRUD.

---

## Couverture Migrations / DB

7 fichiers :
- `test_migrations.py`, `test_entity_db_init.py`, `test_entity_db_apply.py`
- `test_sql_loader.py`, `test_entity_db_relations.py`, `test_entity_db_schema.py`, `test_entity_json.py`

Couverture suffisante pour les migrations versionnées et `db:init` / `db:apply`.

---

## Couverture Modules

**7 fichiers, 188 tests.**

| Fichier | Tests | Couverture |
|---------|-------|------------|
| test_module_manifest.py | 54 | Format manifests, validation |
| test_module_cli.py | 45 | module:list, module:install, module:files, module:routes |
| test_module_registry.py | 32 | Découverte, registry |
| test_module_discovery.py | 20 | Détection modules valides/invalides |
| test_module_files.py | 17 | Copie fichiers, sécurité symlinks |
| test_module_install.py | 11 | Installation complète |
| test_module_routes.py | 9 | Injection routes |

**Sécurité symlinks testée :**
- `test_symlink_dans_provides_refuse` — symlinks dans provides refusés
- `test_symlink_interne_aussi_refuse` — symlinks internes refusés
- `test_symlink_arrete_avant_toute_copie` — arrêt avant copie sur symlink
- `file:///tmp/entities` — URL `file://` refusée

**Limites non testées (fonctionnalités inexistantes) :**
- Rollback d'installation — non testé car non implémenté
- `module:remove` — non testé car non implémenté
- `module:update` — non testé car non implémenté
- Installations partielles — non testées (détection non implémentée)

Ces absences ne sont pas des lacunes de tests : elles reflètent des fonctionnalités non livrées, documentées comme telles dans l'audit CONSOLIDATION-001.

---

## Couverture Profils

**test_project_profiles.py (35 tests) + test_forge_new.py.**

- Profils `minimal`, `standard`, `dynamic`, `multilingual` — tous testés.
- Ordre de préférence des profils testé.
- `standard` comme défaut confirmé.
- `--profile minimal` via CLI testé.
- `forge_profile.txt` généré et vérifié.
- Profil invalide → message d'erreur clair testé.

**Couverture profils : complète.**

---

## Couverture Starters

**2 fichiers, 310 tests.**

`test_starter_cli.py` (118 tests) couvre :
- Existence des 5 starters (niveaux 1–5)
- Résolution des alias (`contacts`, `carnet`, etc.)
- Affichage `starter:list`
- `doc_url` des starters 1, 3, 4 (nouveau format `starters/0N-*/`)
- Statut `available` de chaque starter
- Structure des starter.json
- Pages de documentation associées (présence index.md, rebuild.md)

`test_starter_communes_sejours.py` (192 tests) couvre :
- Starter 5 (Communes & Séjours) — entités, médias, pages publiques, formulaires, mail, i18n, seed

**Lacune :** `doc_url` des starters 2 et 5 ne sont pas testés avec le nouveau format (identifié dans CONSOLIDATION-001, à corriger dans CONSOLIDATION-STARTER-001).

---

## Couverture Front / i18n

24 fichiers avec contenu front/i18n :
- `test_front_css.py`, `test_front_layout.py`, `test_front_js.py` — contrats CSS/JS
- `test_i18n.py`, `test_i18n_cli.py`, `test_i18n_jinja.py` — i18n core et CLI
- `test_make_public_i18n.py` (26 tests) — pages publiques + i18n
- i18n couvert dans les tests CRUD et publics

**Couverture légère identifiée :**
- Tests de contrats (présence de fichiers) mais pas de tests E2E.
- Pluralisation i18n et fallback non testés explicitement.
- Comportement `js:init` sur profil `minimal` non testé.

---

## Couverture Documentation

4 fichiers documentaires :
- `test_consolidation_001.py` (7 tests) — audit architecture
- `test_consolidation_cli_001.py` (9 tests) — audit CLI
- `test_consolidation_doc_001.py` (14 tests) — audit documentation
- `test_docs_config.py` — navigation MkDocs et liens

109 références à des fichiers docs dans les tests.

Ces tests vérifient la cohérence structurelle (existence des fichiers, mentions dans la roadmap) — utiles pour éviter les régressions documentaires.

---

## Tests de non-écrasement utilisateur

**Mécanisme principal :** la propriété `preserved` dans les retours des générateurs.

- `test_make_public_form.py` : `test_preserve_template_existant` — vérifie que `result.preserved` est vrai quand un template existe déjà.
- `test_auth_rate_limit_table.py` : `test_preserve_auth_rate_limit_attempts_sql_existant` — idem pour un fichier SQL existant.
- `test_output.py` : fonctions `preserved()` pour tracking des fichiers manuels.
- 70 fichiers contiennent des patterns `overwrite / preserve / _base / non_cras`.

**Ce qui n'existe pas :**
- Pas de fichier `test_*overwrite*.py` ou `test_*preserve*.py` dédié.
- Pas de scénario end-to-end "générer dans un projet existant avec modifications manuelles".
- Pas de test couvrant le cas : starter rebuild dans un projet avec code modifié.

**Évaluation :** la protection est présente et testée localement dans chaque générateur, mais il n'y a pas de test de régression global qui simulerait un workflow complet de reconstruction.

---

## Tests fragiles ou à surveiller

**Patterns fragiles :** aucun `sleep`, `time.time`, `datetime.now`, `random.`, `uuid.`, `subprocess.`, `os.chdir` détecté dans les tests.

**Isolation :** 3507 usages de `monkeypatch` / `tmp_path` — très bonne isolation via fixtures pytest.

**Conclusion : aucun test fragile détecté.** La suite est robuste.

---

## Zones bien protégées

1. **Auth/User** : 36 fichiers, couverture MFA/OIDC/sessions/tokens/reset/rate-limit/admin/audit très complète.
2. **CRUD** : 22 fichiers, 659 tests — pagination, tri, search, HTMX, médias, RBAC, many-to-many, états vides.
3. **Sécurité modules** : symlinks refusés, `file://` refusé — testés explicitement.
4. **Profils** : 4 profils testés, défaut standard confirmé, profil invalide testé.
5. **Starters 1–4** : struct, alias, doc_url (nouveaux formats), documentation associée.
6. **Pages publiques** : 164 tests — page, liste, show, formulaire, contact, i18n, médias.

---

## Zones partiellement protégées

| Zone | Couverture | Lacune |
|------|------------|--------|
| Non-écrasement | Diffuse via `preserved` | Pas de scénario end-to-end global |
| i18n | Fonctionnel couvert | Pluralisation / fallback non testés |
| Front (js:init) | Contrats présence fichiers | Pas de test par profil |
| Starters doc_url | Starters 1, 3, 4 testés | Starters 2 et 5 encore avec ancien format |
| build:model / check:model | Présents dans CLI | Peu visibles dans les tests dédiés |

---

## Zones critiques avant publication

Ces zones méritent attention avant Forge 2.0. Elles ne sont pas des blocages immédiats mais des risques de régression.

### 1. Non-écrasement utilisateur — risque MOYEN

La philosophie Forge garantit que les générateurs ne surprennent pas le code utilisateur. Cette garantie est testée localement (propriété `preserved`) mais pas via un scénario de bout en bout.

**Risque :** un changement dans un générateur pourrait supprimer la protection sans que les tests l'attrapent si le test local est insuffisamment précis.

**Recommandation :** CONSOLIDATION-NON-OVERWRITE-001 doit ajouter un test de scénario complet : générer, modifier manuellement, régénérer, vérifier que les modifications sont préservées.

### 2. doc_url starters 2 et 5 — risque FAIBLE

Identifié dans CONSOLIDATION-001 et CONSOLIDATION-STARTER-001. Les tests vérifient les starters 1, 3, 4 mais pas 2 et 5. Risque de lien cassé dans `starter:list`.

### 3. Limites modules non testées — risque FAIBLE (fonctionnalités inexistantes)

Rollback, `module:remove`, `module:update` ne sont pas testés car non implémentés. Tant que ces commandes n'existent pas, le risque est nul. À documenter clairement dans `docs/modules.md` (CONSOLIDATION-DOC-MODULES-001).

### 4. i18n pluralisation et fallback — risque FAIBLE

Le module i18n est léger (3 fichiers). Les cas de pluralisation et de fallback sur clé absente ne sont pas testés. Risque d'erreur silencieuse sur des traductions manquantes.

---

## Recommandations

Ces recommandations concernent les tickets suivants. Ne pas corriger dans CONSOLIDATION-TESTS-001.

### CONSOLIDATION-NON-OVERWRITE-001 (prochain ticket)

Ajouter un test de scénario complet :
- Générer une entité + CRUD dans un projet de test.
- Modifier manuellement un fichier généré.
- Régénérer.
- Vérifier que le fichier modifié n'a pas été écrasé.

Vérifier également pour :
- `sync:entity` sur une entité déjà générée.
- `make:public-*` sur un template existant.
- `starter:build` dans un projet avec code existant.
- `module:install` dans un projet avec routes existantes.

### Post-consolidation : i18n fallback

Ajouter des tests sur :
- Clé de traduction absente → comportement de fallback.
- Clé pluralisée avec compte 0, 1, n.

### Post-consolidation : scénarios E2E front

Ajouter des tests vérifiant que `js:init htmx` fonctionne sur un profil `minimal` (pas uniquement `standard`).

---

## Tickets futurs proposés

| Ticket | Objectif |
|--------|---------|
| CONSOLIDATION-NON-OVERWRITE-001 | Scénario complet de non-écrasement |
| CONSOLIDATION-MODULES-001 | Vérifier cycle complet des modules |
| CONSOLIDATION-PROFILES-001 | Vérifier cohérence des profils générés |
| CONSOLIDATION-FRONT-001 | Vérifier Tailwind / HTMX / Alpine / templates |
| CONSOLIDATION-STARTER-001 | Vérifier doc_url starters 2 et 5 |
| CONSOLIDATION-ROADMAP-001 | Décider Forge 2.0 / Forge Design / post-roadmap |
| CONSOLIDATION-DOC-MODULES-001 | Créer docs/modules.md |
| DOC-FIX-MINOR-001 | Corrections cosmétiques documentaires |

---

## Verdict final

**La suite de tests Forge est robuste et fiable pour poursuivre vers Forge 2.0.**

168 fichiers, 4824 tests passés. Couverture fonctionnelle très complète sur Auth (MFA, OIDC, sessions, reset, rate-limiting, admin), CRUD (659 tests), modules (sécurité symlinks), starters, profils et pages publiques. Aucun test fragile. Isolation robuste via fixtures pytest.

Deux points à traiter avant publication : le non-écrasement utilisateur manque d'un scénario de bout en bout (CONSOLIDATION-NON-OVERWRITE-001) ; les `doc_url` des starters 2 et 5 ne sont pas encore couverts par des assertions (CONSOLIDATION-STARTER-001).

---

*Audit réalisé le 2026-05-08. Forge post-1.5.0. 4824 tests passés, 1 skipped.*
