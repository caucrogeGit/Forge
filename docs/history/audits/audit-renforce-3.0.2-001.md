# Audit renforcé Forge 3.0.2 — AUDIT-RENFORCE-3.0.2-001

**Date d'exécution** : 2026-05-13  
**Version auditée** : 3.0.2 (tag `v3.0.2`)  
**Suite de tests** : 9651 passés, 2 skippés (suite complète, `requirements-dev.txt`)  
**Périmètre** : 6 sections — environnement core-only, API docs, versions, angles morts, CLI, packaging

---

## Section 1 — Environnement core-only (`requirements.txt` seul)

**Protocole** : venv neuf `/tmp/audit-core-v2`, `pip install -r requirements.txt pytest`, puis `python -m pytest -q`.

### Résultats

| Commande | Résultat |
|---|---|
| `forge --version` | exit 0 — `Forge 3.0.2` |
| `forge routes:list` | exit 0 |
| `forge project:check` | exit 0 |
| `python -m compileall -q .` | exit 0 — aucune erreur de syntaxe |
| `ruff check .` | exit 0 |
| `mkdocs build --strict` | exit 0 (utilise le venv complet via PATH) |
| **`python -m pytest -q`** | **exit 2 — 30 erreurs de collecte** |

### Verdict section 1 — BLOCANT

`pytest` en environnement core-only (`requirements.txt` seul) produit 30 erreurs de collecte et retourne exit 2. Les 30 fichiers concernés importent des modules des paquets opt-in (`forge_mvc_mfa`, `forge_mvc_rbac`, `forge_mvc_workflow`, `forge_mvc_stats`) qui ne sont pas installés dans ce contexte.

**Fichiers en erreur (extrait)** : `test_auth_mfa_*.py` (×11), `test_auth_user_rbac.py`, `test_stats_*.py` (×3), `test_workflow_*.py` (×3), `test_auth_audit_controller.py`, `test_auth_session_hardening.py`, `tests/meta/test_auth_mfa_secret_naming_001.py`...

**Cause** : Ces tests importent directement des modules opt-in sans garde (`pytest.importorskip`). Ils présupposent l'environnement de développement complet (`requirements-dev.txt` avec `-e ./packages/*`).

**Conséquence** : Toute CI utilisant uniquement `pip install -r requirements.txt` verra une suite pytest rouge avant même l'exécution d'un test. Le contrat de la charte §7 ("tester avant d'élargir") n'est pas satisfait hors environnement de développement. La cause est documentée dans `requirements-dev.txt` (commentaire explicite sur les `-e ./packages/*`), ce qui signale que le problème est connu — mais l'exit 2 reste un risque opérationnel pour une CI naïve.

**Recommandation** : Ajouter `pytest.importorskip("forge_mvc_mfa")` en tête de chaque fichier test opt-in, ou créer un `conftest.py` racine qui skip automatiquement les modules absents. L'exit code passerait alors à 0 (0 passed, N skipped), ce qui est accepté par tout outil de CI standard.

---

## Section 2 — Validité des imports documentés (API reference)

**Protocole** : extraction de tous les `from <module> import <symbole>` dans `docs/auth.md`, `docs/reference.md`, `docs/api-json.md` et `docs/**/*.md`, puis exécution de chaque import dans l'environnement complet.

**Bilan** : 15 imports échouent sur les modules `core.*` réels (hors mvc.controllers qui sont applicatifs, hors erreurs de troncature du regex).

### Groupe A — Symboles MFA dans `core.auth` (5 échecs)

Ces symboles sont des wrappers de façade documentés dans `docs/auth.md` comme importables directement depuis `core.auth`. Ils ont été extraits dans `forge-mvc-mfa` lors de MFA-EXTRACT-001 et ne sont plus réexportés par `core/auth/__init__.py`.

```
from core.auth import is_mfa_enabled        # ImportError
from core.auth import start_mfa_challenge   # ImportError
from core.auth import verify_mfa_challenge  # ImportError
from core.auth import require_user_permission  # ImportError
from core.auth import require_recent_mfa    # ImportError
```

**Fichier source** : `docs/auth.md` lignes 1204, 1223, 1270, 1290.

### Groupe B — Symboles RBAC dans `core.auth` (3 échecs)

```
from core.auth import get_user_permissions  # ImportError
from core.auth import get_user_role_ids     # ImportError
from core.auth import user_has_permission   # ImportError
```

**Fichier source** : `docs/auth.md` ligne 1315 (bloc multi-import tronqué).

### Groupe C — API française dans `core.security.session` (2 échecs)

```
from core.security.session import authentifier_session  # ImportError
from core.security.session import creer_session         # ImportError
```

Ces noms français étaient l'ancienne API. LANG-MIGRATION-001 a renommé les fonctions en anglais (`authenticate_session`, `create_session`). La documentation active (`docs/security.md`, `docs/rbac.md`, `docs/auth.md`) référence encore l'ancienne API.

**Fichiers sources** : `docs/security.md:81`, `docs/rbac.md:245,538,616,648`, `docs/auth.md:265`.

### Groupe D — API française dans `core.uploads.rate_limit` (2 échecs)

```
from core.uploads.rate_limit import est_limite_upload    # ImportError
from core.uploads.rate_limit import enregistrer_upload   # ImportError
```

### Groupe E — API française dans `core.security.hashing` (3 échecs)

```
from core.security.hashing import hacher_mot_de_passe   # ImportError
from core.security.hashing import enregistrer_tentative  # ImportError
from core.security.hashing import est_limite             # ImportError
```

**Fichiers sources** : `docs/history/audits/starters-auth-audit-001.md` (historique, donc acceptable), `docs/adr/001-auth-strategy.md` (mention historique, également acceptable).

### Verdict section 2

**Groupe A + B (8 imports) — DOCUMENTATION_INCORRECTE** : `docs/auth.md` présente des exemples d'imports `from core.auth import <symbole_mfa_ou_rbac>` qui échouent en pratique. Ces symboles requièrent les paquets opt-in (`forge-mvc-mfa`, `forge-mvc-rbac`). Les exemples de code devraient soit utiliser `from forge_mvc_mfa.auth import ...`, soit documenter la condition préalable (`pip install forge-mvc-mfa`).

**Groupe C (2 imports) — DOCUMENTATION_OBSOLÈTE_ACTIVE** : `docs/security.md` et `docs/rbac.md` utilisent les noms français supprimés par LANG-MIGRATION-001. Ces fichiers sont dans la documentation active (nav MkDocs), pas dans `docs/history/`.

**Groupe D + E (5 imports) — HISTORIQUE** : les références françaises dans `docs/history/` et `docs/adr/` sont des mentions historiques intentionnelles, non des exemples exécutables.

---

## Section 3 — Cohérence des versions dans la documentation

**Protocole** : `grep -rn "v3\.0\.1\|3\.0\.1"` dans `docs/` en excluant `history/`, `adr/`, `roadmap/`, `CHANGELOG.md`.

### Références v3.0.1 dans la documentation active (3 OBSOLÈTES_BLOQUANTS)

| Fichier | Ligne | Contenu |
|---|---|---|
| `docs/guide.md:38` | `git clone --branch v3.0.1 ...` | Commande d'installation |
| `docs/installation-github.md:11` | `git clone --branch v3.0.1 ...` | Commande d'installation |
| `docs/installation-github.md:21` | `based on Forge 3.0.1` | Commentaire de commit type |

Fichiers additionnels contenant `3.0.1` (non-bloquants — contexte de liste de versions) :  
`docs/release-local.md:39,50,351` — commandes de test avec l'ancien wheel, à mettre à jour avant release publique.  
`docs/reference/cli-commands.md:656` — exemple de sortie CLI.  
`docs/profiles.md:28` — `--ref v3.0.1` dans un exemple.  
`docs/installation-windows.md:67,125` — références Windows.

### Mentions Python 3.11 dans les guides actifs (10 occurrences — DÉRIVE)

`pyproject.toml` impose `python_requires = ">=3.12"` (ADR-006). Les guides suivants indiquent encore "Python 3.11 ou plus" :

- `docs/15-minutes.md:42`
- `docs/app-complete-tutorial.md:42`
- `docs/starters/01-contact-simple/index.md:48`
- `docs/starters/02-utilisateurs-auth/index.md:46`
- `docs/starters/03-carnet-contacts/index.md:49`
- `docs/starters/04-suivi-comportement-eleves/index.md:51`
- `docs/deploy-advanced.md:53`
- `docs/deployment.md:82`
- `docs/reference/api.md:1807`
- `docs/lts-policy.md:120`

### Verdict section 3

**3 occurrences BLOQUANTES** (git clone avec `v3.0.1` dans les guides d'installation principaux). Un utilisateur qui suit `docs/installation-github.md` clonera l'ancien tag.

**10 occurrences Python 3.11** : dérive documentaire. Non-bloquant pour le fonctionnement, mais contredit la politique ADR-006.

---

## Section 4 — Angles morts de la suite de tests

**Protocole** : `pytest tests/meta/test_docs_no_phantom_modules_001.py -v` → passe. Puis `python -c "from core.<module> import <symbole>"` sur 5 imports directs testés par ce garde-fou.

### Comportement réel du garde-fou `test_docs_no_phantom_modules_001.py`

Le test vérifie que certains **noms de modules** (`core.workflow`, `core.stats`, etc.) n'apparaissent pas dans les exemples de docs comme s'ils étaient dans core. Il passe (3/3 checks verts).

**Ce que le test ne vérifie pas** : la validité des symboles importés depuis les modules réels. Cinq imports directs dans les docs passent à travers le garde-fou et échouent en runtime :

```python
from core.auth import is_mfa_enabled        # dans docs/auth.md — ImportError
from core.auth import require_user_permission  # dans docs/auth.md — ImportError
from core.security.session import authentifier_session  # dans docs/security.md — ImportError
from core.uploads.rate_limit import est_limite_upload   # ImportError
from core.security.hashing import hacher_mot_de_passe  # ImportError (historique)
```

### Verdict section 4

Le garde-fou `test_docs_no_phantom_modules_001.py` remplit son contrat (détecter les modules fantômes), mais laisse un angle mort sur les **symboles obsolètes dans les modules réels**. La suite verte ne garantit pas la cohérence code/docs au niveau des fonctions exportées. Un test `test_docs_imports_executable_001.py` couvrirait cet angle.

---

## Section 5 — Couverture CLI (aide vs code)

**Protocole** : comparaison `forge --help` avec `grep "if command ==" forge.py`.

### Commandes présentes dans le code mais absentes de `forge --help`

| Commande | Localisation forge.py | Raison probable |
|---|---|---|
| `sync:landing` | ligne 502 | Commande interne — copie `mvc/views/landing/` → `docs/index.html` |
| `docs:pdf` | ligne 560 | Commande expérimentale non stabilisée |
| `i18n:init` | ligne 514 | Module i18n non documenté |
| `i18n:check` | ligne 514 | Module i18n non documenté |
| `auth:user:show` | ligne 525 (liste d'exclusion) | Intentionnellement masqué — marqué dans la liste `_UNDOCUMENTED` |
| `mail:render` | ligne 536 | Commande de débogage mail |

### Verdict section 5

**4 commandes réellement cachées** (`sync:landing`, `docs:pdf`, `i18n:init`, `i18n:check`, `mail:render`) — certaines fonctionnelles, d'autres expérimentales. `auth:user:show` est dans la liste d'exclusion explicite du code, donc intentionnellement masqué.

Aucune régression détectée par rapport à la version précédente. La situation est stable mais mériterait soit une documentation dans `docs/contributing/conventions.md`, soit un retrait du code si ces commandes sont réellement abandonnées.

---

## Section 6 — Isolation packaging opt-in

**Protocole** : venv neuf `/tmp/audit-pkg-v2`, sans `forge-mvc` installé.  
`pip install ./packages/forge-mvc-rbac` vs `pip install --no-deps ./packages/forge-mvc-rbac`.

### Résultats

```
$ pip install ./packages/forge-mvc-rbac
ERROR: No matching distribution found for forge-mvc==3.0.2
```

```
$ pip install --no-deps ./packages/forge-mvc-rbac
Successfully installed forge-mvc-rbac-3.0.2  ✓
```

### Analyse

`forge-mvc==3.0.2` n'existe pas sur PyPI (seules les versions 1.0.1 et 1.1.0 y sont publiées). L'installation standard d'un paquet opt-in échoue donc pour tout utilisateur externe qui tenterait `pip install forge-mvc-rbac` depuis PyPI — ce n'est pas une regression Forge 3.0.2, c'est l'état connu pré-publication.

Le workflow monorepo (`requirements-dev.txt` avec `-e ./packages/*`) fonctionne correctement. L'installation `--no-deps` dans un contexte où `forge-mvc` est déjà installé (cas d'un utilisateur qui installe via la roue locale) fonctionne également.

### Verdict section 6

**BLOQUANT PRÉ-PUBLICATION PyPI.** Avant toute publication publique des paquets opt-in, `forge-mvc==3.0.2` doit être publié sur PyPI en premier. L'ordre de publication est :  
1. `forge-mvc==3.0.2` (paquet core)  
2. `forge-mvc-mfa==3.0.2`, `forge-mvc-rbac==3.0.2`, `forge-mvc-workflow==3.0.2`, `forge-mvc-stats==3.0.2` (paquets opt-in)

Ce blocage est connu et documenté dans le plan de release. Il ne bloque pas l'usage local ni la série 3.x de développement.

---

## Section 7 — Verdict consolidé

| Section | Niveau | Résumé |
|---|---|---|
| §1 — Core-only pytest | BLOQUANT | 30 erreurs de collecte, exit 2 — CI naïve échoue |
| §2 — Imports API | BLOQUANT (partiel) | 8 imports MFA/RBAC documentés depuis `core.auth` échouent ; 2 sessions en français obsolètes dans docs actives |
| §3 — Versions | BLOQUANT | 3 git clone avec `v3.0.1` dans guides d'installation ; 10 mentions Python 3.11 contradictoires |
| §4 — Angles morts | MINEUR | Garde-fou phantom passe ; symboles obsolètes non détectés |
| §5 — CLI coverage | INFO | 5–6 commandes non documentées ; situation stable |
| §6 — Packaging PyPI | BLOQUANT PRÉ-PUB | `forge-mvc==3.0.2` absent de PyPI ; monorepo OK |

**Aucun des bloquants ci-dessus ne remet en cause la stabilité interne de Forge 3.0.2.** Les 9651 tests passent. Le code est correct. Les bloquants sont documentaires (§2 §3), opérationnels en CI (§1), et liés à la publication PyPI (§6).

---

## Section 8 — Recommandations avant publication publique

**Priorité 1 — Obligatoire avant annonce publique**

1. **Publier `forge-mvc==3.0.2` sur PyPI** avant les paquets opt-in (§6).
2. **Corriger les 3 git clone `v3.0.1`** dans `docs/guide.md` et `docs/installation-github.md` → `v3.0.2` (§3).
3. **Corriger les examples `from core.auth import <mfa/rbac>`** dans `docs/auth.md` — indiquer le paquet correct (`forge-mvc-mfa`, `forge-mvc-rbac`) et la commande d'installation (§2 groupes A+B).

**Priorité 2 — Amélioration qualité**

4. **Corriger `authentifier_session` / `creer_session`** dans `docs/security.md` et `docs/rbac.md` → `authenticate_session` / `create_session` (§2 groupe C).
5. **Harmoniser Python 3.12** dans les 10 fichiers guides indiquant "Python 3.11" (§3).
6. **Ajouter `pytest.importorskip`** dans les 30 fichiers tests opt-in pour obtenir exit 0 en core-only (§1).

**Priorité 3 — Angle mort à couvrir**

7. **Créer `tests/meta/test_docs_imports_executable_001.py`** vérifiant que les imports des exemples de code dans les docs sont exécutables (§4).

---

*Audit exécuté localement sur Forge 3.0.2, commit `75b6700`, 2026-05-13.*
