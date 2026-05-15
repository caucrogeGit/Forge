# Audit PUBLICATION-2.0-PREP-001 — Préparation publication Forge 2.0

**Date :** 2026-05-09
**Périmètre :** version, README, documentation, packaging, checklist publication
**Ticket :** PUBLICATION-2.0-PREP-001

---

## Objectif

Préparer la publication de Forge 2.0 après la clôture de la Phase 9.5. Vérifier que le dépôt, la documentation, la version, le packaging et la trajectoire sont prêts pour une première version publique exploitable.

Ce ticket ne publie pas Forge 2.0.

---

## Synthèse

| Zone | État | Commentaire |
|---|---|---|
| Version | À corriger | `1.5.0` partout → `2.0.0` dans `PUBLICATION-2.0-VERSION-001` |
| Tag cible | Prêt | `v2.0.0` décidé — à créer dans `PUBLICATION-2.0-BUILD-001` |
| README | À corriger | Version `1.5.0` → `2.0.0`, contenu à enrichir |
| Documentation | Prête sauf version | MkDocs strict vert, mentions `1.5.0` à corriger |
| Packaging | Prêt | `pyproject.toml` cohérent, starters inclus, dépendances complètes |
| forge --version | À corriger | Affiche `1.5.0` → à corriger dans `PUBLICATION-2.0-VERSION-001` |
| Starters inclus | OK | `forge_cli/starters/data/**/*` inclus dans le wheel |
| Profils inclus | OK | `forge_cli/project_profiles.py` inclus |
| Modules inclus | OK | `core/modules/` inclus |
| Limites assumées | OK | Documentées dans CONSOLIDATION-ROADMAP-001 |
| Forge Design séparé | OK | Aucun couplage obligatoire |
| OIDC / admin utilisateurs | Clarifié | Livrés en Phase 4.5 — erreur corrigée dans ce ticket |
| Checklist release | Produite | Voir section dédiée |

---

## État initial

Au moment de l'ouverture de ce ticket :

- `pytest` : 5062 passed, 1 skipped
- `python -m compileall -q .` : OK
- `mkdocs build --strict` : OK
- `git diff --check` : OK
- Phase 9.5 : terminée
- Aucun tag créé depuis v1.5.0
- Version déclarée partout : `1.5.0`

---

## Fichiers audités

| Fichier | Rôle | État |
|---|---|---|
| `pyproject.toml` | Packaging, version, dépendances | Version `1.5.0` à corriger |
| `forge.py` | `_FORGE_VERSION`, `_FORGE_DEFAULT_REF`, CLI | Version `1.5.0` à corriger |
| `README.md` | Documentation principale | Mentions `1.5.0` à corriger |
| `CHANGELOG.md` | Historique des versions | Entrée `2.0.0` à créer |
| `LICENSE` | Licence projet | Présent |
| `mkdocs.yml` | Configuration documentation | Cohérent |
| `docs/forge-roadmap.md` | Roadmap | Phase 9.5 close, Phase 10 ouverte |
| `docs/index.html` | Page d'accueil docs | Mentionne `v1.5.0` — à corriger |
| `docs/reference.md` | Référence API | Mentionne `1.5.0` — à corriger |
| `docs/installation.md` | Installation | Mentionne `v1.5.0` — à corriger |
| `docs/guide.md` | Guide démarrage | Mentionne `v1.5.0` — à corriger |

---

## Version et tag cible

### Version cible

```text
2.0.0
```

Tag git :

```text
v2.0.0
```

### Points à corriger dans `PUBLICATION-2.0-VERSION-001`

| Fichier | Valeur actuelle | Valeur cible |
|---|---|---|
| `pyproject.toml` | `version = "1.5.0"` | `version = "2.0.0"` |
| `forge.py` | `_FORGE_VERSION = "1.5.0"` | `_FORGE_VERSION = "2.0.0"` |
| `forge.py` | `_FORGE_DEFAULT_REF = "v1.5.0"` | `_FORGE_DEFAULT_REF = "v2.0.0"` |
| `README.md` | `Forge 1.5.0` (titre, contenu, exemples) | `Forge 2.0` |
| `docs/index.html` | `v1.5.0` (3 occurrences) | `v2.0.0` |
| `docs/reference.md` | `1.5.0` (ligne 5, ligne 1383) | `2.0.0` |
| `docs/installation.md` | `v1.5.0` (exemples git clone, texte) | `v2.0.0` |
| `docs/guide.md` | `v1.5.0` (exemple git clone) | `v2.0.0` |
| `CHANGELOG.md` | Dernière entrée : `1.5.0` | Ajouter entrée `2.0.0` |
| `pyproject.toml` classifiers | `Development Status :: 3 - Alpha` | `Development Status :: 4 - Beta` |

---

## README

### État actuel

`README.md` mentionne actuellement :
- Titre : `# Forge — Framework MVC Python 1.5.0`
- Installation : `git clone --branch v1.5.0 ...`
- Commit initial : `based on Forge 1.5.0`
- Option `--profile` documentée ✅
- Section starters présente ✅
- Section `forge --version` présente ✅
- Section migrations SQL ✅
- Section HTMX absente (à compléter si souhaité)
- Section Auth/User absente (présence optionnelle)

### Points prêts

- Structure générale cohérente
- Installation claire pour clonage depuis GitHub
- Commandes principales présentes
- Starters documentés avec `forge starter:build`
- Profils documentés avec `--profile`

### Points à corriger dans `PUBLICATION-2.0-VERSION-001`

- Version dans le titre et les exemples : `1.5.0` → `2.0.0`
- Tag dans les exemples `git clone` : `v1.5.0` → `v2.0.0`
- Message commit init : `based on Forge 1.5.0` → `based on Forge 2.0`

---

## Documentation MkDocs

### État actuel

- `mkdocs build --strict` : **vert** ✅
- Navigation cohérente ✅
- Phase 9.5 fermée ✅
- Phase 10 ouverte ✅
- Forge Design séparé documenté ✅
- Limites assumées visibles ✅
- `docs/roadmap.md` absent ✅

### Points à corriger dans `PUBLICATION-2.0-VERSION-001`

- `docs/index.html` : 3 occurrences de `v1.5.0` / `Forge 1.5.0` → `v2.0.0` / `Forge 2.0`
- `docs/reference.md` : mentions `1.5.0` → `2.0.0`
- `docs/installation.md` : exemples git clone avec `v1.5.0` → `v2.0.0`
- `docs/guide.md` : exemple git clone avec `v1.5.0` → `v2.0.0`

---

## Packaging Python

### État actuel de `pyproject.toml`

```toml
name = "forge-mvc"
version = "1.5.0"               ← à corriger
requires-python = ">=3.11"
```

**Dépendances runtime :**

| Dépendance | Version | Rôle |
|---|---|---|
| `mariadb==1.1.14` | Fixée | Connecteur MariaDB |
| `python-dotenv==1.2.2` | Fixée | Variables d'environnement |
| `jinja2==3.1.6` | Fixée | Templates |
| `Pillow>=10.0,<13` | Plage | Médias/images |
| `argon2-cffi>=25.1,<26` | Plage | Hash mots de passe |
| `pyotp>=2.9,<3` | Plage | MFA TOTP |

**Packages inclus :** `core*`, `forge_cli*`, `integrations*`, `forge.py` (via `py-modules`)

**Package data :** `forge_cli/starters/data/**/*` (starters inclus dans le wheel)

**Console script :** `forge = "forge:cli_entrypoint"` ✅

**Compatibilité Python :** 3.11, 3.12, 3.13, 3.14 ✅

**LICENSE** : présent ✅

**MANIFEST.in** : absent — non nécessaire avec pyproject.toml moderne et setuptools ✅

### Architecture de distribution

`forge new` clone le dépôt GitHub (`_FORGE_REPO = "https://github.com/caucrogeGit/Forge.git"`) avec la référence `_FORGE_DEFAULT_REF`. Les templates `mvc/`, `static/` et squelettes ne sont donc pas dans le wheel pip — ils viennent du clone GitHub. C'est une **décision architecturale assumée** qui implique que `forge new` nécessite git et un accès réseau.

Les starters (`forge_cli/starters/data/`) sont eux dans le wheel — `forge starter:build` fonctionne sans réseau après l'installation pip. ✅

### Points à corriger dans `PUBLICATION-2.0-VERSION-001`

- `version = "1.5.0"` → `"2.0.0"`
- `Development Status :: 3 - Alpha` → `4 - Beta`

---

## Commande forge --version

### État actuel

```python
_FORGE_VERSION = "1.5.0"   # forge.py:117
_FORGE_DEFAULT_REF = "v1.5.0"  # forge.py:118
```

`forge --version` affiche : `Forge 1.5.0`

### À corriger dans `PUBLICATION-2.0-VERSION-001`

```python
_FORGE_VERSION = "2.0.0"
_FORGE_DEFAULT_REF = "v2.0.0"
```

---

## Starters inclus

Les starters sont inclus dans le wheel via :

```toml
[tool.setuptools.package-data]
"forge_cli" = ["starters/data/**/*"]
```

Fichiers présents dans `forge_cli/starters/data/` :
- `contact-simple/starter.json` ✅
- `utilisateurs-auth/starter.json` ✅
- `carnet-contacts/starter.json` ✅
- `suivi-comportement-eleves/starter.json` ✅
- `communes-sejours/starter.json`, `files/**`, `routes.py.snippet` ✅

`forge starter:list` et `forge starter:build` fonctionnent sans réseau. ✅

---

## Profils inclus

`forge_cli/project_profiles.py` est inclus dans le wheel (package `forge_cli*`).

Les 4 profils officiels (`minimal`, `standard`, `dynamic`, `multilingual`) sont déclarés, testés et documentés. ✅

---

## Modules inclus

`core/modules/` est inclus dans le wheel (package `core*`). Les 4 commandes `module:*` sont dans `forge_cli/modules.py` (inclus). ✅

---

## Limites assumées

Reprises de CONSOLIDATION-ROADMAP-001 (corrigé) :

| Limite | Ticket futur |
|---|---|
| Profils peu différenciés | `PROFILE-DIFFERENTIATION-001` |
| `module:remove` absent | Post-2.0 |
| Tests E2E réels MariaDB | `E2E-MARIADB-001` |
| `js:init` absent de `reference.md` | `CONSOLIDATION-DOC-FRONT-001` |
| `docs/modules.md` absent | `CONSOLIDATION-DOC-MODULES-001` |
| Styles d'aide CLI hétérogènes | `DX-HELP-001` |

---

## Clarification OIDC / admin utilisateurs

### Incohérence identifiée

Le document `docs/audits/consolidation-roadmap-001.md` listait initialement :
- `OIDC / OAuth` comme **Post-2.0** avec la mention « Tickets AUTH-OIDC-001 à 003 planifiés »
- `AUTH-ADMIN-001 à 003` dans les « Fonctionnalités futures » post-2.0

### Réalité vérifiée

La roadmap `docs/forge-roadmap.md` (Phase 4.5) liste :

| Ticket | État |
|---|---|
| AUTH-OIDC-001 | **terminé** — contrat OIDC |
| AUTH-OIDC-002 | **terminé** — login OIDC avec state, nonce, PKCE |
| AUTH-OIDC-003 | **terminé** — association compte local / OIDC |
| AUTH-ADMIN-001 | **terminé** — administration CLI utilisateurs minimale |
| AUTH-ADMIN-002 | **terminé** — activation/désactivation utilisateur |
| AUTH-ADMIN-003 | **terminé** — attribution des rôles |

### Décision

**OIDC et admin utilisateurs sont livrés dans Forge 2.0.**

Ce sont des fonctionnalités de Phase 4.5, toutes terminées. Les améliorations futures envisageables (OIDC multi-provider avancé, interface admin web) ont été renommées `AUTH-OIDC-ADVANCED-001` et `AUTH-ADMIN-ADVANCED-001` dans le document corrigé.

`docs/audits/consolidation-roadmap-001.md` a été corrigé dans ce ticket pour refléter cette réalité.

---

## Checklist de publication

La checklist complète est à exécuter dans `PUBLICATION-2.0-BUILD-001`.

### Pré-publication (PUBLICATION-2.0-VERSION-001)

- [ ] Mettre à jour `_FORGE_VERSION = "2.0.0"` dans `forge.py`
- [ ] Mettre à jour `_FORGE_DEFAULT_REF = "v2.0.0"` dans `forge.py`
- [ ] Mettre à jour `version = "2.0.0"` dans `pyproject.toml`
- [ ] Mettre à jour `Development Status :: 4 - Beta` dans `pyproject.toml`
- [ ] Mettre à jour README.md (titre, exemples, tag)
- [ ] Mettre à jour `docs/index.html` (3 occurrences `v1.5.0`)
- [ ] Mettre à jour `docs/reference.md` (mentions `1.5.0`)
- [ ] Mettre à jour `docs/installation.md` (exemples git clone)
- [ ] Mettre à jour `docs/guide.md` (exemples git clone)
- [ ] Créer l'entrée `2.0.0` dans `CHANGELOG.md`
- [ ] Exécuter pytest : tous les tests verts
- [ ] Exécuter `mkdocs build --strict`

### Build et release (PUBLICATION-2.0-BUILD-001)

```bash
pytest
python -m compileall -q .
mkdocs build --strict
git diff --check
git diff --cached --check
python -m build
pipx install dist/<wheel> --force
forge --version      # doit afficher "Forge 2.0.0"
forge help
forge doctor
forge starter:list
git tag v2.0.0
git push origin main
git push origin v2.0.0
```

---

## Points prêts

1. **Architecture** : core MVC en 3 couches, aucune dette critique.
2. **CLI** : 59 commandes, dispatch uniforme, script `forge` exposé dans le wheel.
3. **Tests** : 5062 passés, couverture exhaustive.
4. **Packaging** : `pyproject.toml` cohérent, starters inclus, dépendances complètes.
5. **Starters** : 5 starters dans le wheel, `forge starter:build` hors réseau.
6. **Documentation** : MkDocs strict vert, navigation propre, Phase 9.5 close.
7. **Limites** : documentées, non bloquantes, cohérentes avec la philosophie Forge.
8. **OIDC / admin** : livrés et clarifiés.
9. **Forge Design** : séparé, aucun couplage obligatoire.
10. **Communes & Séjours** : démonstrateur avancé dans le wheel, aucune logique métier dans `core/`.

---

## Points à corriger avant publication

Tous dans **PUBLICATION-2.0-VERSION-001** :

1. Version `1.5.0` → `2.0.0` dans `pyproject.toml`, `forge.py`, `README.md`, `docs/`
2. Tag ref `v1.5.0` → `v2.0.0` dans `forge.py`, `docs/`, `README.md`
3. Entrée `2.0.0` dans `CHANGELOG.md`
4. Classifier `Development Status :: 3 - Alpha` → `4 - Beta`

---

## Risques restants

| Risque | Niveau | Commentaire |
|---|---|---|
| Cohérence version partout | Modéré | 10+ fichiers à mettre à jour — ticket VERSION dédié |
| `forge new` nécessite git et réseau | Faible | Décision architecturale assumée, documentée |
| Tests E2E MariaDB réels absents | Modéré | Post-2.0, documenté |
| CHANGELOG entrée 2.0.0 vide | Faible | À créer dans VERSION ticket |

---

## Recommandations

1. **Lancer `PUBLICATION-2.0-VERSION-001`** immédiatement — verrouille les numéros, CHANGELOG et affichage CLI.
2. **Lancer `PUBLICATION-2.0-BUILD-001`** après — exécute la checklist complète et crée le tag.
3. **Ne pas mélanger** les deux tickets : version d'abord, puis build/tag.

---

## Ticket suivant proposé

**PUBLICATION-2.0-VERSION-001** — verrouiller la version Forge 2.0

Objectif : mettre à jour `_FORGE_VERSION`, `_FORGE_DEFAULT_REF`, `pyproject.toml`, `README.md`, `docs/`, `CHANGELOG.md` de `1.5.0` à `2.0.0`. Ajouter l'entrée CHANGELOG.

---

## Verdict final

**Le dépôt Forge est prêt à recevoir les tickets de publication Forge 2.0.**

Le packaging est cohérent, les tests sont verts, la documentation passe MkDocs strict, les starters sont inclus dans le wheel, les limites sont documentées, et l'incohérence OIDC/admin a été clarifiée.

**Un seul type d'action bloque la publication réelle : la mise à jour des numéros de version de `1.5.0` à `2.0.0`.** Tout le reste est prêt.

**Résultat :** PUBLICATION-2.0-PREP-001 — **VALIDÉ. Phase 10 ouverte.**
