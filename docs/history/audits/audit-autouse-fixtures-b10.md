# Audit fixtures autouse — B10

**Ticket :** `TESTS-AUTOUSE-FIXTURES-AUDIT-001`
**Date :** 2026-05-25
**Périmètre :** toutes les fixtures `pytest` déclarées avec `autouse=True`
dans `tests/`, avec une attention particulière à celles définies hors
`tests/conftest.py`.

## Résumé

**Décision : GO B10** — l'audit conclut qu'**aucun blocage** ne reste
avant `beta.10`. Les 56 fixtures `autouse=True` du dépôt sont
**toutes classées en risque faible** sur les critères de contamination
d'état global :

* aucune ne modifie `os.environ` en direct (toutes utilisent `monkeypatch.setenv`) ;
* aucune ne touche `sys.path` ;
* aucune n'utilise `os.chdir` ;
* aucune ne déclare de `global` ;
* les fixtures à scope `session`/`module` sont au nombre de 2 et leurs
  effets sont contenus (configuration ponctuelle de Forge, nettoyage d'une
  table de test).

## Méthode

1. Énumération AST : pour chaque module Python sous `tests/`, on parcourt
   les `FunctionDef` et on retient les décorateurs `pytest.fixture(...)`
   portant `autouse=True`.
2. Pour chaque fixture, on collecte :
   * fichier et numéro de ligne ;
   * portée déclarée (`scope=...`, défaut `"function"`) ;
   * présence d'un `yield` (teardown explicite) ;
   * argument `monkeypatch` (restauration automatique pytest) ;
   * argument `tmp_path` / `tmp_path_factory` ;
   * recherche textuelle dans `ast.unparse(node)` de motifs à risque :
     `os.environ[...]=`, `sys.path`, `chdir`, `global `.
3. Classification :
   * **Risque faible** — modifie uniquement un état local au test (attributs
     `self.*`, variables locales, données chargées en mémoire), OU utilise
     `monkeypatch`/`tmp_path` (restauration automatique pytest), OU possède
     un `yield` avec restauration explicite.
   * **Risque moyen** — modifie un état global mais avec teardown
     observable et testé.
   * **Risque élevé** — modifie un état global SANS teardown clair, ou
     écrit dans `os.environ` directement, ou modifie `sys.path` sans
     restauration.

## Nombre de fixtures autouse trouvées

| Localisation | Compte |
|---|---:|
| `tests/conftest.py` | 4 |
| Hors `tests/conftest.py` | 52 |
| **Total** | **56** |

## Classement

### Risque faible — 56 / 56

#### Helpers de setup local (instance / lecture fichier) — 23 fixtures

Ces fixtures attachent un état à `self.*` ou chargent une donnée en mémoire
locale au test. Aucun état global modifié.

| Fichier | Fixture | Motif |
|---|---|---|
| `tests/meta/test_claude_md_001.py` (×3) | `_load` | Lecture en mémoire d'un fichier `CLAUDE.md`. |
| `tests/test_e2e_module.py` (×7) | `_setup` | Initialise `self.root` à partir d'une fixture `module_project` (tmp_path). |
| `tests/test_e2e_mariadb.py` (×3) | `_setup` | Idem — tmp_path scoped. |
| `tests/test_e2e_starter.py` (×2) | `_build` | Initialise `self.root` + appelle `build()` sur tmp_path. |
| `tests/test_starter_*_canonical.py` (×5) | `_build` | Idem (5 starters). |
| `tests/test_templating.py` (×2) | `_setup` | Configure un renderer local. |

#### Fixtures utilisant `monkeypatch` (restauration auto) — 11 fixtures

`monkeypatch` est conçu pour restaurer automatiquement l'état modifié à la
fin du test (`setenv`, `setattr`, etc.). Aucune intervention manuelle requise.

| Fichier | Fixture | Modification |
|---|---|---|
| `tests/meta/test_auth_mfa_secret_naming_001.py` | `_mfa_key` | `monkeypatch.setenv("FORGE_MFA_SECRET_KEY", …)` |
| `tests/test_auth_audit_controller.py` | `_mfa_secret_key` | idem |
| `tests/test_auth_mfa_challenge.py` | `_mfa_secret_key` | idem |
| `tests/test_auth_mfa_login_challenge.py` | `_mfa_secret_key` | idem |
| `tests/test_auth_mfa_ratelimit_001.py` | `_mfa_secret_key` | idem |
| `tests/test_auth_mfa_revalidation.py` | `_mfa_secret_key` | idem |
| `tests/test_auth_mfa_revalidation_identity_001.py` | `_mfa_secret_key` | idem |
| `tests/test_auth_mfa_totp.py` | `_mfa_secret_key` | idem |
| `tests/test_auth_mfa_totp_replay_001.py` | `_mfa_secret_key` | idem |
| `tests/test_auth_session_hardening.py` | `_mfa_secret_key` | idem |
| `tests/test_mfa_secret_crypto.py` | `_set_key` | idem |
| `tests/test_mail.py` | `_mail_config` | `monkeypatch.setenv` (mail params) |
| `tests/test_wsgi_production_smoke_001.py` | `_restore_state` | `monkeypatch.setenv("APP_ENV", "prod")` |

#### Fixtures avec yield + teardown explicite — 18 fixtures

Modifient un état observable, restaurent via `yield`.

| Fichier | Fixture | Restauration |
|---|---|---|
| `tests/conftest.py` | `clear_sessions` | `purge_all()` avant + après yield |
| `tests/conftest.py` | `clear_rate_limits` | purge rate-limits + replay + audit failure |
| `tests/conftest.py` | `clear_upload_rate_limits` | clear compteurs uploads |
| `tests/test_auth_app.py` | `_views` | restaure `template_manager._renderer` |
| `tests/test_auth_audit_controller.py` | `_views` | idem |
| `tests/test_auth_cli_to_login_e2e.py` | `_views` | idem |
| `tests/test_auth_hash_migration_001.py` | `_views` | idem |
| `tests/test_auth_mfa_ratelimit_001.py` | `purge_rl` | reset rate-limit |
| `tests/test_auth_mfa_totp_replay_001.py` | `reset_replay` | reset replay store |
| `tests/test_auth_session_compat_bridge_001.py` | `isolated_store` | reset session store |
| `tests/test_auth_session_legacy_deprecation_001.py` | `isolated_store` | idem |
| `tests/test_configurable_session_store_001.py` | `reset_session_store` | `set_session_store(None)` avant + après |
| `tests/test_i18n_cache_001.py` | `reset_cache` | reset cache i18n |
| `tests/test_security_cookies.py` | `_views` | restaure renderer |
| `tests/test_security_cookies_host_prefix.py` | `_views` | idem |
| `tests/test_sql_loader.py` | `reset_sql_cache` | reset SQL cache |
| `tests/test_wsgi_app_factory_config_001.py` | `_restore_renderer_and_proxies` | save/restore renderer + trusted_proxies |
| `tests/test_wsgi_entrypoint_001.py` | `_stub_renderer` | save/restore renderer |
| `tests/test_wsgi_prod_warnings_001.py` | `_restore_state` | force `set_session_store(None)` — voir [Recommandations](#recommandations) |

#### Setup de session — 2 fixtures (scopes module/session)

| Fichier | Fixture | Scope | Risque |
|---|---|---|---|
| `tests/conftest.py` | `configure_forge_kernel` | session | **Faible** — initialisation Forge unique pour tous les tests, paramètres figés et idempotents. |
| `tests/test_e2e_mariadb.py` | `_cleanup_contact` | module | **Faible** — yield présent, nettoyage d'une table de test après le module. |

### Risque moyen — 0 / 56

### Risque élevé — 0 / 56

## Corrections appliquées dans ce ticket

**1 correction simple appliquée**, révélée par le test méta livré au cours
du ticket :

* `tests/test_templating.py::TestVuesReelles::_setup` modifiait
  `forge._cfg["views_dir"]` et appelait `template_manager.register(...)`
  **sans `yield` ni teardown** — les tests exécutés après dans la même
  session pytest voyaient `views_dir` pointer sur le répertoire `mvc/views/`
  du dépôt au lieu de leur propre `tmp_path`. Correction : sauvegarde des
  valeurs précédentes (`prev_views`, `prev_renderer`) avant modification,
  `yield`, puis restauration. Pattern aligné sur celui de
  `tests/test_wsgi_app_factory_config_001.py::_restore_renderer_and_proxies`.

Les 55 autres fixtures auditées étaient déjà classées risque faible et
respectent l'une de ces conventions :

* utilisation de `monkeypatch` (restauration auto pytest) ;
* `yield` avec restauration explicite ;
* setup purement local (attributs `self.*` sur instance de classe test).

Le test méta `tests/meta/test_autouse_fixtures_audit_001.py` (ajouté par ce
ticket) verrouille cette propriété pour empêcher une future régression :
toute nouvelle fixture `autouse=True` ne respectant aucune de ces
conventions fera échouer la collecte.

## Corrections reportées

**Aucune.** Aucun cas complexe ou risqué n'a été identifié — pas de ticket
de suivi nécessaire.

## Recommandations

1. **Conserver le pattern « force reset » au teardown des fixtures
   session_store.** Les fixtures `_restore_state` de
   `test_wsgi_prod_warnings_001.py` et `test_wsgi_production_smoke_001.py`
   ne tentent volontairement PAS de restaurer la valeur précédente du
   store — elles forcent `set_session_store(None)`. La raison documentée
   (commentaire en place) : un test précédent
   (`test_configurable_session_store_001`) peut avoir laissé
   `forge._cfg["session_store"]` désynchronisé du manager ; restaurer
   `prev_store` propagerait l'état corrompu. **Ne pas revenir en arrière
   sur ce choix sans ticket dédié.**

2. **Ne pas ajouter d'écriture directe `os.environ[KEY] = VALUE`** dans une
   fixture autouse. Utiliser systématiquement `monkeypatch.setenv` —
   garanti par le test méta.

3. **Ne pas modifier `sys.path` ni utiliser `os.chdir`** dans une fixture
   autouse — garanti par le test méta.

4. **Pour les nouvelles fixtures autouse à scope `session` ou `module`** :
   exiger soit `yield` + teardown explicite, soit une justification
   documentaire dans la docstring (idempotence du setup).

## Décision

**GO B10** — aucun blocage détecté avant `beta.10`. Le système de tests
Forge gère proprement la contamination d'état global ; les conventions
existantes (`monkeypatch`, `yield` + restauration, force-reset documenté)
sont robustes et désormais verrouillées par un test méta dédié.
