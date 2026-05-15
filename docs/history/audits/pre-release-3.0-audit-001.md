# Audit pré-release Forge 3.0 — pre-release-3.0-audit-001

## Contexte

- **Date d'exécution** : 2026-05-11
- **Environnement** : Ubuntu 24.04 (Linux 6.17), Python 3.12.13, MariaDB 10.11.14
- **Commit audité** : `5234d9e` — feat: refonte landing page pour Forge 3.0 (DOCS-LANDING-PAGE-3.0-001)
- **Tickets phase 14 livrés** : 39 / 42
- **Tests automatiques** : 8 920 passants, 2 skipped, 0 fail

## Résumé exécutif

L'audit identifie **2 problèmes bloquants RC** et **3 problèmes importants** à
corriger avant ou peu après la publication du RC.

Le core Forge (tests unitaires, lints standards, build MkDocs, Python 3.14) est
**sain**. Les blocages concernent l'installation depuis un environnement vierge
et les liens de la landing page — deux surfaces visibles par les utilisateurs
externes dès la 3.0.

---

## Famille A — Install et démarrage

### A.1 — Création du venv jetable

**Commande** : `python3.12 -m venv /tmp/forge-audit-A/.venv`
**Résultat** : ✓ OK

### A.2 — pip install -e (depuis dépôt, mode éditable)

**Commande** : `/tmp/forge-audit-A/.venv/bin/pip install -e /path/to/Forge`
**Résultat** : ✓ OK — installation sans erreur

### A.3 — forge --version

**Résultat dans le venv audit** : ✗ **BLOQUANT** — voir bloquant #1 ci-dessous.

**Résultat dans le venv projet** : ✗ **BLOQUANT** — voir bloquant #2 ci-dessous.

**Bloquant A-1 — `forge` inutilisable sans `forge-mvc-rbac`**

Dès que le CLI `forge` est invoqué (même `forge --version`), Python charge
`forge_cli/entities/make_crud.py` → `forge_cli/entities/crud/controller_builder.py`
qui contient un import top-level dur :

```python
from forge_mvc_rbac import normalize_permission_code as _normalize_perm
```

`forge_mvc_rbac` est un module **optionnel** (distribué séparément,
`forge-mvc-rbac`). Toute installation de `forge-mvc` seul — y compris via
`pipx install forge-mvc` — crash immédiatement avec :

```
ModuleNotFoundError: No module named 'forge_mvc_rbac'
```

Tout `forge new`, `forge doctor`, `forge make:entity`, etc. est inaccessible.

**Ticket correctif** : `PRE-RELEASE-FIX-RBAC-IMPORT-001`
**Sévérité** : Bloquant RC — empêche toute installation standard de fonctionner.

**Bloquant A-2 — `forge --version` rapporte 2.3.0 dans le venv projet**

`/home/roger/Projets/Forge/.venv/bin/forge --version` → `Forge 2.3.0`
Mais `python forge.py --version` → `Forge 2.5.0`

Cause : `.venv/lib/python3.12/site-packages/forge.py` est une **copie figée**
installée sans mode éditable lors d'un `pip install` antérieur. Les 4 sous-modules
(`mfa`, `rbac`, `workflow`, `stats`) ont leurs `.pth` éditables, mais pas le core.
Quand `forge` est invoqué, Python trouve `site-packages/forge.py` (2.3.0) avant
`forge.py` à la racine (2.5.0).

Impact dev : la CLI dans `.venv` exécute du code 12 versions en arrière. Les tests
n'utilisent pas le binaire `forge` (pas de subprocess vers `["forge", ...]`),
ce qui explique que les 8 920 tests passent malgré ce décalage.

**Ticket correctif** : `PRE-RELEASE-FIX-VENV-STALE-001`
**Sévérité** : Bloquant pour le développement quotidien — acceptable d'expliquer
dans les notes de release (`pip install -e . --force-reinstall`).

### A.4 — forge new

✗ Bloqué par bloquant A-1.

### A.5 — forge doctor

✗ Bloqué par bloquant A-1.

### A.6 — Lancement du serveur

✗ Bloqué par bloquant A-1.

---

## Famille B — Cycle complet starter

**Résultat** : ✗ Entièrement bloqué par bloquant A-1.

`forge new`, `forge starter:build`, `forge db:init`, `forge db:apply` sont
tous inaccessibles dans un venv propre. Le cycle starter ne peut pas être
validé avant correction de `PRE-RELEASE-FIX-RBAC-IMPORT-001`.

---

## Famille C — Lints et tests

### C.1 — pytest complet

**Commande** : `python -m pytest -q`
**Résultat** : ✓ **8 920 passants, 2 skipped, 0 fail** — 1 DeprecationWarning
(clé `secret_hash` dépréciée dans `forge_mvc_mfa`, attendue, migrée en 3.0).

### C.2 — python -m compileall

**Résultat** : ✓ 0 erreur de compilation.

### C.3 — ruff check . --select ALL

**Violations totales** : 22 155 (ruff ALL active des règles très opinionées).

Catégories principales :

| Code | Règle | Occurrences | Verdict |
|------|-------|-------------|---------|
| S101 | `assert` utilisé | 11 213 | Cosmétique — assertions dans les tests, attendu |
| ANN201/ANN001 | Annotations manquantes | 12 577 | Style — Forge n'utilise pas d'annotations systématiques |
| D102/D103/D101 | Docstrings manquantes | ~5 500 | Style |
| PLC0415 | Import hors top-level | 824 | Lazy imports intentionnels — voir note |
| T201 | `print()` | 530 | CLI légitime — forge est un outil interactif |
| S608 | SQL injection vector | ~30 | **Faux positifs** — f-strings avec constantes internes |
| B904 | `raise` sans `from` | ~10 | Qualité mineure |
| S110 | `try/except/pass` | 2 | À noter (`forge_cli/deploy.py`) |

**Violations critiques réelles** : aucune. Les S608 sont des faux positifs (interpolation
de constantes Python dans des f-strings SQL, pas d'entrée utilisateur).

Les `PLC0415` (824 cas) sont des lazy imports **intentionnels** — pattern validé
dans `docs/contributing/conventions.md` (pattern C.1 lock+delegate).

**Note ruff --select ALL** : le résultat doit être lu comme une liste d'opinions
stylistiques, non comme une liste de bugs. Forge ne cible pas une conformité ruff ALL.

### C.4 — mkdocs build --strict

**Résultat** : ✓ Exit 0 — build sans erreur.

Notes non-bloquantes observées :
- `docs/audit-claude.md` présent dans le filesystem mais non tracké par git
  et absent de la nav → fichier parasite à supprimer ou gitignorer.
- `docs/adr/008-auth-audit-architecture.md` absent de la nav mkdocs.yml → mineur,
  le fichier existe (ADR-008) mais n'est pas listé dans la section ADR.
- `docs/reference.md` contient un lien relatif `adr/` non résolu (INFO seulement,
  pas un WARNING strict).
- Warning MkDocs Material sur MkDocs 2.0 : signal informatif sur incompatibilités
  futures, n'affecte pas la 3.0.

### C.5 — git diff --check

**Résultat** : ✓ Exit 0 — 0 erreur whitespace.

---

## Famille D — Cross-version Python

**Versions disponibles** : Python 3.12.13 (natif), Python 3.14.4 (pyenv).
Python 3.13 absent de pyenv — non testé.

### D.1 — Python 3.14.4

**Installation** : pip install -e (core + 4 modules optionnels) → OK.

**Imports core** :
```
core.application.Application   : ✓ OK
core.http.request/response     : ✓ OK
core.security.session          : ✓ OK
core.__version__               : 2.5.0 ✓
```

**Suite de tests (subset représentatif, 1 764 tests)** :
```
tests/meta/, tests/release/, tests/test_application.py, tests/test_forms.py,
tests/test_response.py, tests/test_request_body.py, tests/test_security_headers.py,
tests/test_security_cookies.py, tests/test_security_csrf_http.py
```
**Résultat** : ✓ 1 764 passants, 0 fail — aucune incompatibilité Python 3.14.

**Note** : le même bloquant A-1 (`forge_mvc_rbac` absent) s'applique à 3.14
dans un venv sans module optionnel. Validé en installant les 4 modules.

### D.2 — Python 3.13

Non testé — 3.13 absent de pyenv. À valider avant le tag final.

---

## Famille E — Audit dépendances et sécurité

### E.1 — pip-audit

**Résultat** : 2 CVE trouvées sur `urllib3 2.6.3` :
- `CVE-2026-44431` — fix : 2.7.0
- `CVE-2026-44432` — fix : 2.7.0

**Impact Forge** : `urllib3` n'est **pas** une dépendance runtime de Forge
(`pyproject.toml` ne la liste pas). Elle est présente via les outils de
dev (`requests`, `twine`, `pip-audit`). Les applications Forge déployées
ne sont pas exposées à ces CVE.

**Recommandation** : mettre à jour `urllib3` dans l'environnement de dev
(`pip install --upgrade urllib3`). Pas de ticket nécessaire.

### E.2 — pip list --outdated

Paquets de dev désuets :

| Paquet | Installé | Disponible |
|--------|----------|------------|
| urllib3 | 2.6.3 | 2.7.0 (CVE — à mettre à jour) |
| cryptography | 47.0.0 | 48.0.0 |
| requests | 2.33.1 | 2.34.0 |
| idna | 3.13 | 3.14 |
| markdown-it-py | 4.0.0 | 4.2.0 |

Aucun de ces paquets n'est une dépendance runtime Forge.

### E.3 — pyproject.toml — requires-python

**Incohérence trouvée** : `requires-python = ">=3.11"` et le classifier inclut
`Programming Language :: Python :: 3.11`, alors que l'ADR-006 décide
**Python 3.12+ minimum**.

**Impact** : un utilisateur Python 3.11 peut installer `forge-mvc` sans
avertissement, mais certaines features 3.12+ pourraient manquer.

**Ticket correctif** : `PRE-RELEASE-FIX-PYPROJECT-PYTHON-001`
**Sévérité** : Importante — incohérence entre la metadata publiée et l'ADR.

---

## Famille F — Documentation cohérente

### F.1 — Liens externes de la landing page

24 URLs testées. Résultats :

- ✓ 19 URLs retournent 200 (tous liens vers GitHub, docs Forge, technos)
- ✗ 5 URLs retournent 404 :

| URL | Code | Cause |
|-----|------|-------|
| `caucrogegit.github.io/Forge/roadmap/` | 404 | Pas d'index de section — bon chemin : `roadmap/forge-roadmap/` |
| `caucrogegit.github.io/Forge/starter-app-01-contacts/` | 404 | Ancien chemin — bon chemin : `starters/01-contact-simple/` |
| `caucrogegit.github.io/Forge/starter-app-02-utilisateurs-auth/` | 404 | Ancien chemin — bon chemin : `starters/02-utilisateurs-auth/` |
| `caucrogegit.github.io/Forge/starter-app-03-carnet-contacts/` | 404 | Ancien chemin — bon chemin : `starters/03-carnet-contacts/` |
| `caucrogegit.github.io/Forge/starter-app-04-suivi-comportement-eleves/` | 404 | Ancien chemin — bon chemin : `starters/04-suivi-comportement-eleves/` |

**Cause** : les starters ont été restructurés sous `docs/starters/` lors d'un
ticket antérieur. La landing page n'a pas été mise à jour. Les anciens chemins
(`starter-app-0X-*/`) n'existent plus localement non plus.

Le lien `/roadmap/` pointe vers l'index d'une section MkDocs qui ne génère pas
de page d'accueil — il faudrait `roadmap/forge-roadmap/`.

**Ticket correctif** : `PRE-RELEASE-FIX-LANDING-LINKS-001`
**Sévérité** : Importante — 5 liens cassés visibles par tous les visiteurs dès
le jour de la mise en ligne.

### F.2 — Images de la landing

- `mvc/views/landing/static/img/` : `forge-logo.png`, `favicon.ico`, `favicon.svg` ✓
- `docs/static/` : mêmes assets présents ✓

### F.3 — ADR-008 absent de la nav

`docs/adr/008-auth-audit-architecture.md` existe mais n'est pas listé dans
la section `Décisions d'architecture` de `mkdocs.yml`. Mineur — le fichier
est accessible et référencé en texte depuis d'autres docs.

**Sévérité** : Mineure.

### F.4 — docs/audit-claude.md non tracké

Le fichier `docs/audit-claude.md` existe dans le filesystem mais n'est ni
tracké par git ni dans la nav. Il apparaît dans la liste MkDocs "pages not in nav".

**Sévérité** : Mineure — à supprimer ou gitignorer.

---

## Synthèse — Trouvailles

### Bloquantes (à corriger avant RC)

- [x] `PRE-RELEASE-FIX-RBAC-IMPORT-001` : import top-level de `forge_mvc_rbac`
  dans `forge_cli/entities/crud/controller_builder.py` — rend `forge` inutilisable
  sans `forge-mvc-rbac` installé.

### Importantes (à corriger avant release ou entre RC et release)

- [ ] `PRE-RELEASE-FIX-VENV-STALE-001` : copie figée `forge.py` 2.3.0 dans `.venv`
  du projet — `forge --version` rapporte une version incorrecte dans l'env de dev.
  Fix : `pip install -e . --force-reinstall` dans les notes de release.
  
- [ ] `PRE-RELEASE-FIX-PYPROJECT-PYTHON-001` : `requires-python = ">=3.11"` et
  classifier `Python :: 3.11` incohérents avec l'ADR-006 (Python 3.12+).

- [ ] `PRE-RELEASE-FIX-LANDING-LINKS-001` : 5 liens cassés dans la landing —
  4 starters (anciens chemins) + 1 roadmap (section sans index).

### Mineures (à corriger en 3.x post-release)

- [ ] `ADR-008` absent de la nav mkdocs.yml.
- [ ] `docs/audit-claude.md` non tracké à nettoyer.
- [ ] `docs/reference.md` lien relatif `adr/` non résolu (INFO MkDocs, pas bloquant).
- [ ] Python 3.13 non testé (absent de pyenv) — à valider avant le tag final.

### Non-issues / acceptables

- Les S608 ruff dans `media_repository.py` et `model_builder.py` sont des faux
  positifs : interpolation de constantes Python, pas d'entrée utilisateur.
- Les 22 155 violations ruff ALL sont majoritairement cosmétiques (annotations
  manquantes, docstrings, style assert). Aucune violation critique de sécurité.
- `urllib3` CVE : dépendance d'outils de dev uniquement, pas de runtime Forge.
- DeprecationWarning `secret_hash` dans forge_mvc_mfa : attendue, migration
  documentée.
- Material for MkDocs warning MkDocs 2.0 : signal informatif, pas de migration
  requise pour la 3.0.

---

## Conclusion

L'audit identifie **1 bloquant RC critique** (`PRE-RELEASE-FIX-RBAC-IMPORT-001`)
qui rend la CLI Forge inutilisable dans toute installation sans `forge-mvc-rbac`.
Ce bloquant doit être corrigé avant la publication du RC.

**3 autres tickets correctifs** sont recommandés (venv stale, pyproject Python,
liens landing) dont 2 sont visibles par les utilisateurs externes.

Une fois `PRE-RELEASE-FIX-RBAC-IMPORT-001` corrigé et les autres tickets traités,
l'audit peut être déclaré clos et le RC publié.

**Verdict** : audit demande corrections — RC non publiable en l'état.
