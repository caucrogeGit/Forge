# Audit pré-release Forge 1.0.0-beta.10

**Ticket :** `B10-CLOSING-AUDIT-001`
**Date :** 2026-05-25
**Périmètre :** clôture officielle de la Phase B10 avant `RELEASE-BETA10-001`.

---

## Résumé

| Axe | Statut |
|---|---|
| Suite de tests complète | ✅ **14 552 passed / 5 skipped / 0 failed** (après alignement test méta consistency) |
| Tests B10 ciblés (15 fichiers) | ✅ **1 025 passed / 0 failed** |
| Ruff | ✅ All checks passed |
| Compileall | ✅ silencieux |
| MkDocs `--strict` | ✅ built in 10.19 s |
| `git diff --check` | ✅ propre |
| `release-validate.sh 1.0.0-beta.9` | ✅ toutes sections vertes (seul WARN attendu : tag déjà existant) |
| Build 6 paquets (core + 5 opt-ins) | ✅ 12 distributions construites (6 wheels + 6 sdists) |
| `twine check` 12 distributions | ✅ tous PASSED |
| Tags Git `beta` | ✅ v1.0.0-beta.1 → v1.0.0-beta.9 présents, aucun beta.10 |
| Versions PEP 440 cohérentes | ✅ `1.0.0b9` partout (core + 5 opt-ins + package.json + CHANGELOG) |
| Identité publique | ✅ Roger Lequette / forgemvc@gmail.com (0 résidu de l'ancienne) |
| Roadmap B10 cohérente | ✅ 19 livrés / 2 restants (ce ticket + RELEASE-BETA10-001) |

---

## Verdict

**🟢 GO pour `RELEASE-BETA10-001`.**

Toutes les vérifications obligatoires de l'audit B10 sont vertes. Aucun
blocage technique, sécurité, ou documentaire ne reste avant la
préparation de la release `1.0.0-beta.10`.

---

## État Git

```
branche      : main
working tree : propre
HEAD         : 13abd96 test(release): align Git tag convention
tags beta    : v1.0.0-beta.1 → v1.0.0-beta.9 (9 tags présents)
tag beta.10  : aucun (correct — ce ticket ne crée pas de tag)
```

Les 15 derniers commits sont tous bien typés (`docs:`, `test:`,
`release:`, `security:`, `ci:`, `fix(app):`). Pas de bruit, pas de
commit obsolète, pas de fichier généré parasite suivi par Git.

---

## Versions

| Source | Valeur | Format |
|---|---|---|
| `pyproject.toml` (core) | `1.0.0b9` | PEP 440 ✅ |
| `core/__init__.py::__version__` | `1.0.0b9` | PEP 440 ✅ |
| `forge.py::_FORGE_VERSION` | `1.0.0b9` | PEP 440 ✅ |
| `packages/forge-mvc-{rbac,workflow,stats,mfa,media}` × 5 | `1.0.0b9` | PEP 440 ✅ |
| `package.json` | `1.0.0-beta.9` | SemVer ✅ |
| `package-lock.json` | `1.0.0-beta.9` | SemVer ✅ |
| `CHANGELOG.md` dernière entrée | `## [1.0.0-beta.9] — 2026-05-24` | SemVer ✅ |
| Tag Git le plus récent | `v1.0.0-beta.9` | SemVer ✅ |

**Aucune occurrence accidentelle de `1.0.0b10` ou `1.0.0-beta.10`** dans
le code/config/version. Les 3 mentions trouvées sont des références
légitimes : exemples de format de tag dans `docs/release-policy.md`,
mention du ticket `RELEASE-BETA10-001` dans la roadmap (intro et table).

---

## Roadmap B10

Structure validée par `tests/meta/test_roadmap_b10_consistency_001.py`
(40 tests) :

* `Bloquants immédiats` — 3/3 livrés
* `Critiques pré-RC` — 4/4 livrés
* `Durcissement et garde-fous` — 9/9 livrés
* `Cohérence release` — 3/3 livrés (incluant `RELEASE-TAG-CONVENTION-TEST-ALIGN-001`)
* `Clôture` — `B10-CLOSING-AUDIT-001` (ce ticket, à passer livré après ce rapport) puis `RELEASE-BETA10-001`
* `Corrections terrain hors-audit` — 2/2 livrés (`APP-PY-TLS-HANDSHAKE-PER-THREAD-001`, `APP-PY-TLS-HANDSHAKE-DOCS-001`)

Aucun compteur fragile (`(N tickets)`, `Total Phase B10 : N`, `15 tickets ci-dessus`) ne subsiste.

`B10-CLOSING-AUDIT-001` précède bien `RELEASE-BETA10-001` (on audite avant de releaser).

---

## Identité publique

* ancien nom propriétaire (chaîne `Roger·Cauchon` sans le séparateur) → **0 occurrence** dans le dépôt suivi (hors le test méta lui-même qui exclut son propre fichier)
* ancien email (chaîne `caucroge·@gmail.com` sans le séparateur) → **0 occurrence** idem
* `Roger Lequette` → présent dans README, LICENSE, mkdocs.yml, pyproject.toml × 6, landing canonique, docs publiques
* `forgemvc@gmail.com` → présent dans landing (section #contact + footer mailto), SECURITY.md, CONTRIBUTING.md, packages READMEs

Vérifié par `tests/meta/test_public_contact_identity_001.py::TestNoLegacyIdentityInTrackedFiles` (2 tests, `git ls-files` parcouru).

---

## Landing contact

* `Contact` placé en dernière position de la navigation ✅
* Section `<section id="contact">` présente ✅
* Formulaire `action="mailto:forgemvc@gmail.com"` (`method="post"`, `enctype="text/plain"`) ✅
* Bouton `Envoyer` présent ✅
* Aucune route `/contact` dans `mvc/routes.py` ✅
* Aucun `ContactController` dans `mvc/controllers/` ✅
* `mvc/views/landing/index.html` (source canonique) et `docs/index.html` (synchronisé) cohérents ✅
* `forge sync:landing` exécuté pendant cet audit n'a produit aucune divergence sur `docs/index.html` — le repo était déjà synchronisé ✅

Verrouillé par `tests/meta/test_public_contact_identity_001.py` (23 tests).

---

## Sécurité B10

| Brique | Test verrouillant | Statut |
|---|---|---|
| Headers HTTP (X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, CSP) partagés app.py/WSGI | `test_wsgi_security_headers_001.py` | ✅ 27 passed |
| HSTS conditionné HTTPS dans WSGI | idem (Option B Forge) | ✅ |
| Cookies de session `__Host-`, Secure, SameSite=Strict | `test_security_cookies*.py` | ✅ |
| Argon2id + verify_password_legacy PBKDF2 | core/security/hashing.py | ✅ |
| Path traversal symlinks (uploads + statics) | `test_uploads_symlink_defense_001.py` | ✅ 12 passed |
| Session hardening (rotation login + MFA) | `test_auth_session_hardening.py` | ✅ 36 passed |
| `python app.py` refuse 0.0.0.0/:: en prod | `test_app_py_prod_host_guard_001.py` | ✅ 54 passed |

---

## WSGI

* `core/wsgi.py::create_configured_wsgi_app()` documenté ✅
* `core/wsgi.py::_response_to_wsgi` injecte les headers de sécurité via
  `core/security/headers.py::apply_security_headers` ✅
* HSTS uniquement quand `environ["wsgi.url_scheme"] == "https"` ✅
* `docs/wsgi-deployment.md §4.1` documente la stratégie (Caddy + Nginx
  exemples, HSTS via reverse proxy) ✅
* `docs/wsgi-deployment.md §3` warning « python app.py refuse 0.0.0.0 en
  prod » ✅

---

## MFA

* `forge-mvc-mfa==1.0.0b9` publié sur PyPI depuis beta.9 (Alpha) ✅
* `validate_mfa_secret_key_config()` exposé publiquement ✅
* `FORGE_MFA_SECRET_KEY` requis au boot quand MFA actif, refus des
  placeholders (`change-me`, `default`, etc.) — 33 tests passent ✅
* Secret TOTP chiffré au repos via Fernet (`SEC-MFA-SECRET-ENCRYPTION-001`) ✅
* `docs/reference/auth-mfa.md` documente la validation au démarrage ✅
* `packages/forge-mvc-mfa/README.md` documente l'API + procédure ✅

---

## Uploads / statics / symlinks

* `core/uploads/storage.py` : `realpath()` + `commonpath()` chaîne de défense ✅
* `app.py::_serve_static` : même chaîne ✅
* Test `tests/test_uploads_symlink_defense_001.py` : 12 tests verrouillent
  les 4 vecteurs d'attaque (symlink fichier outside, symlink dir outside,
  path traversal `..`, fichier normal préservé) + 3 garde-fous source AST
  sur `app.py` ✅
* `docs/security.md` documente la défense ✅

---

## Documentation

* `docs/` source canonique / `site/` artefact MkDocs / `mvc/views/landing/index.html`
  source landing : politique 3-couches documentée dans `docs/contributing.md` ✅
* CLI restructurée : Vue d'ensemble + Commandes essentielles + Parcours rapides
  + Index alphabétique de 63 commandes ✅
* Imports doc validés : 378 tests AST verrouillent que tous les imports
  framework (`core.*`, `forge_mvc_*`) sont importables avec leurs symboles ✅
* ADR-015 documente le handshake TLS par thread ✅
* `docs/production-security.md §10` documente la séparation
  `DB_ADMIN_*` (provisioning) / `DB_APP_*` (runtime) ✅
* Format de tag SemVer publique documenté dans `docs/release-policy.md §178`
  (mise à jour `RELEASE-TAG-CONVENTION-TEST-ALIGN-001`) ✅

---

## CLI

* 63 commandes documentées et indexées alphabétiquement
* Aucune commande inventée — vérifiée contre `forge --help` réel
* Fiches enrichies pour les commandes principales (`make:crud`, `doctor`,
  `project:check`) : Rôle, Quand l'utiliser, Effets, À ne pas confondre
  avec, Statut
* Section « Modules opt-in » avec instructions `pip install --pre forge-mvc-X`
  pour les 5 opt-ins

---

## Politiques de release

* `tools/release-validate.sh` utilise `PYTHON_BIN="${PYTHON:-python3}"`
  configurable, avec validation `command -v` et message d'erreur explicite
  si introuvable (RELEASE-VALIDATE-PATH-ROBUSTNESS-001) ✅
* Mode `--convert pep440|semver|validate` fonctionnel ✅
* Conversion SemVer ↔ PEP 440 vérifiée bilatéralement (60 tests
  paramétrés dans `test_release_validate_version_formats_001.py`) ✅
* Tag Git attendu en SemVer (`v1.0.0-beta.9`, jamais `v1.0.0b9`) ✅
* `docs/release-policy.md` §178 explicite les 4 formes de tag, interdit
  la forme PEP 440 ✅

---

## Audits dépendances

| Audit | Mode | Résultat |
|---|---|---|
| `pip-audit -r requirements.txt` | Bloquant en release | ✅ 0 vulnérabilité |
| `pip-audit -r requirements-dev.txt` | Bloquant en release | ✅ 0 vulnérabilité |
| `npm audit --omit=dev` | Bloquant en release | ✅ 0 vulnérabilité |
| `.github/workflows/dependency-audit.yml` (hebdo) | Informatif (`continue-on-error: true`), commentaire d'annotation présent | ✅ politique séparée GUARD-001 |

---

## Build packages

Build effectué dans `/tmp/forge-b10-dist/` (hors arborescence repo) :

```
forge_mvc-1.0.0b9-py3-none-any.whl                 PASSED
forge_mvc-1.0.0b9.tar.gz                           PASSED
forge_mvc_rbac-1.0.0b9-py3-none-any.whl            PASSED
forge_mvc_rbac-1.0.0b9.tar.gz                      PASSED
forge_mvc_workflow-1.0.0b9-py3-none-any.whl        PASSED
forge_mvc_workflow-1.0.0b9.tar.gz                  PASSED
forge_mvc_stats-1.0.0b9-py3-none-any.whl           PASSED
forge_mvc_stats-1.0.0b9.tar.gz                     PASSED
forge_mvc_mfa-1.0.0b9-py3-none-any.whl             PASSED
forge_mvc_mfa-1.0.0b9.tar.gz                       PASSED
forge_mvc_media-1.0.0b9-py3-none-any.whl           PASSED
forge_mvc_media-1.0.0b9.tar.gz                     PASSED
```

**6 paquets × (wheel + sdist) = 12 distributions, toutes PASSED `twine check`.**

Aucune publication PyPI effectuée. Aucun fichier `dist/` ou `build/`
parasite ajouté au dépôt — le `.gitignore` ignore correctement.

---

## Résultats des validations

| Commande | Résultat |
|---|---|
| `pytest -q` (suite complète) | ✅ **14 552 passed, 5 skipped** en 4 min 28 s |
| `pytest -q` tests B10 ciblés (15 fichiers) | ✅ **1 025 passed** |
| `pytest -k "roadmap or release or version or audit"` | ✅ après alignement (cf points non bloquants) |
| `ruff check .` | ✅ All checks passed |
| `python -m compileall -q .` | ✅ silencieux |
| `mkdocs build --strict` | ✅ built in 10.19 s |
| `git diff --check` | ✅ propre |
| `bash tools/release-validate.sh 1.0.0-beta.9` | ✅ toutes sections OK |
| `python -m build` (core + 5 opt-ins) | ✅ 12 distributions |
| `python -m twine check` | ✅ 12 PASSED |

**Skipped restants (5)** — tous légitimes :
1. `test_e2e_mariadb.py` (1) — env-gated `FORGE_E2E_MARIADB=1`
2. `test_package_lock_sync_001` (3) — opt-ins rbac/workflow/stats ne pinent pas `forge-mvc==` (design choice)
3. `test_serve_static.py` (1) — cas Windows-only

Note : avant l'alignement du test méta, il y avait 14 551 passed + 1 failed. Le failure était `test_roadmap_b10_consistency_001::test_pending_ticket_marked_a_faire[RELEASE-TAG-CONVENTION-TEST-ALIGN-001]` — voir [Points non bloquants](#points-non-bloquants).

---

## Points non bloquants

### 1. Alignement intra-méta requis pendant l'audit (corrigé)

Le test `tests/meta/test_roadmap_b10_consistency_001.py` (livré par
`ROADMAP-B10-CONSISTENCY-SWEEP-001`) maintenait une liste hardcodée des
tickets attendus, listant `RELEASE-TAG-CONVENTION-TEST-ALIGN-001` comme
« à faire ». Le ticket précédent l'avait passé « livré » dans la
roadmap, donc le test échouait sur une attente obsolète.

**Correction appliquée** : `RELEASE-TAG-CONVENTION-TEST-ALIGN-001`
déplacé de `_EXPECTED_PENDING_B10` vers `_EXPECTED_DELIVERED_B10` dans
le test méta. C'est un alignement de liste d'attente, pas un bug runtime
ni un défaut release. Le ticket B10 explicite que les corrections de
cohérence intra-méta sont dans le périmètre de l'audit (« la roadmap
doit refléter exactement l'état réel »).

Test ré-vert après correction : **40/40 passed**.

### 2. Petites INFO MkDocs non bloquantes

`docs/starters/welcome/index.md` contient 2 liens relatifs `../` et
`../01-contact-simple/` que MkDocs signale en **INFO** (pas WARNING) :
*« unrecognized relative link, it was left as is »*. Le build strict
passe (les INFO ne sont pas bloquantes en `--strict`). À corriger un
jour mais hors scope B10.

### 3. Tag PEP 440 désormais aligné

Avant `RELEASE-TAG-CONVENTION-TEST-ALIGN-001`, le test
`test_release_current_version_001::test_current_version_tag_exists_locally`
cherchait `v1.0.0b9` (forme PEP 440) au lieu de `v1.0.0-beta.9` (SemVer,
convention Forge réelle) et était donc systématiquement skippé. **Corrigé** ; le test passe désormais sans skip.

### 4. Branche `fix/tls-per-thread-handshake`

Branche locale orpheline : 17 commits derrière main, 0 commit ahead.
Mergée logiquement par les commits `fc520cf` et `4ec1e1b` qui figurent
sur main. **Recommandation** : `git branch -d fix/tls-per-thread-handshake`.
Non bloquant pour la release — c'est juste de l'hygiène locale.

---

## Décision finale

**🟢 GO pour `RELEASE-BETA10-001`.**

La phase B10 est techniquement terminée :

* 19 tickets livrés (3 bloquants + 4 critiques + 9 durcissement + 3 cohérence release)
* 0 vulnérabilité dépendance (Python runtime + dev + Node prod)
* 0 régression test (14 552 passed)
* 0 fuite identité ancienne
* 0 résidu de version beta.10 prématurée
* 12 distributions buildables proprement (`twine check` 100%)
* Politiques release/sécurité documentées et verrouillées par tests méta

Le ticket `RELEASE-BETA10-001` peut être lancé immédiatement après que
le commit de cet audit + l'alignement du test méta de consistance soit
poussé.

Les recommandations terrain mineures (liens INFO MkDocs, suppression de
la branche locale obsolète) peuvent être traitées indépendamment et ne
bloquent pas la release.
