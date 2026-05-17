# Politique de release Forge

Ce document définit comment Forge numérote, prépare, valide, tague et publie ses versions.

Il complète :

- [Procédure de release](release.md) — checklist pas à pas avant chaque tag
- [Validation locale](release-local.md) — procédure de test wheel locale
- [Contrat de stabilité](stability-contract.md) — ce qui est stable, interne, expérimental

---

## Objectif

Rendre explicite :

- quand incrémenter `MAJOR`, `MINOR` ou `PATCH` ;
- comment préparer et valider une release ;
- comment taguer et documenter ;
- ce qui est stable, ce qui est expérimental ;
- ce qui ne doit pas être promis.

---

## Schéma de versionnement

Forge adopte **SemVer adapté** :

```
MAJOR.MINOR.PATCH
```

Exemples :

```
2.2.0   → 2.2.1   (correctif)
2.2.0   → 2.3.0   (fonctionnalité compatible)
2.x.y   → 3.0.0   (rupture)
```

---

## PATCH

Incrémenter `PATCH` pour :

- corrections de bugs sans changement d'API ;
- corrections de documentation mineures ;
- durcissements de sécurité sans changement d'interface (headers, cookies, validation) ;
- tests supplémentaires sans modification du comportement observable ;
- corrections de lint ou de format sans impact fonctionnel.

**Exemples de tickets PATCH :**
`SECURITY-HEADERS-001` (ajout Permissions-Policy sans changement API),
`SECURITY-COOKIES-001` (audit sans modification de l'API de session).

**Règle d'or :** si un projet existant en Forge 2.x fonctionne sans modification
après la mise à jour, c'est un PATCH.

---

## MINOR

Incrémenter `MINOR` pour :

- nouvelle fonctionnalité rétrocompatible ;
- nouvelle commande CLI documentée ;
- nouveau module optionnel ;
- nouvelle documentation structurante (sections majeures) ;
- amélioration DX sans rupture ;
- ajout d'API publique sans supprimer l'existante ;
- nouvelle brique optionnelle (ex. Auth/User, module Forge).

**Exemples de tickets MINOR :**
`AUTH-MFA-002` (nouvelle fonctionnalité Auth),
`MODULE-LIFECYCLE-001` (nouvelle commande `module:install`),
`CRUD-HTMX-001` (comportement CRUD optionnel supplémentaire).

**Règle d'or :** si un projet existant fonctionne sans modification mais peut
bénéficier des nouvelles fonctionnalités en opt-in, c'est un MINOR.

---

## MAJOR

Incrémenter `MAJOR` pour :

- rupture de compatibilité avec un élément stable (voir [Contrat de stabilité](stability-contract.md)) ;
- changement de structure de projet générée incompatible ;
- changement de comportement CLI incompatible pour les commandes stables ;
- suppression d'API publique documentée ;
- changement de convention incompatible (nommage de fichiers, format JSON entité) ;
- modification incompatible du schéma des fichiers générés (controllers, models, vues) ;
- changement de configuration incompatible (clés `.env` renommées ou supprimées).

**Règle d'or :** si un projet existant doit être modifié pour fonctionner après
la mise à jour, c'est un MAJOR.

**Ce qui n'est PAS un MAJOR :**

- Modification d'une API interne ou expérimentale (voir [Contrat de stabilité](stability-contract.md)).
- Changement de comportement d'une commande expérimentale.
- Ajout de fonctionnalités sans supprimer l'existant.

---

## API publique et API interne

Se référer au [Contrat de stabilité Forge 2.x](stability-contract.md) pour la liste complète.

### Stable — garantie 2.x

- Commandes CLI documentées dans `docs/reference.md`.
- Structure projet générée par `forge new`.
- Format JSON canonique des entités (v1).
- Clés `.env` documentées.
- Imports publics de `core.http`, `core.auth`, `core.security` (session, CSRF, RBAC).
- `GET /health` → `200 {"status":"ok"}`.

### Interne — peut changer entre mineurs

- Fonctions et modules internes de `forge_cli/`.
- Fonctions préfixées `_`.
- Contenu interne des tests Forge.
- Format interne des sessions côté serveur.

### Expérimental — stable en usage, interface peut évoluer

- `forge module:*`, `forge deploy:*`, `forge starter:build`.
- Backends de session `FileSessionStore`, `MariaDbSessionStore`.
- Pages publiques (`make:public-*`).

---

## Stratégie de classification PyPI

Les classifiers `Development Status` reflètent la maturité réelle de
chaque package publiable :

| Package | Classifier | Justification |
|---|---|---|
| `forge-mvc` (core) | `4 - Beta` | 1.0.0 en bêta — corrections post-audit, tests terrain et RC requis avant stable |
| `forge-mvc-rbac` | `4 - Beta` | API stable et testée, usage production externe encore limité |
| `forge-mvc-workflow` | `4 - Beta` | API stable et testée, usage production externe encore limité |
| `forge-mvc-stats` | `4 - Beta` | API stable et testée, usage production externe encore limité |
| `forge-mvc-mfa` | `2 - Pre-Alpha` | Secret TOTP stocké en clair, ticket `SEC-MFA-SECRET-ENCRYPTION-001` requis avant Beta |

Critères de passage Beta → Stable d'un module opt-in :

- Retours d'usage externe documentés
- Pas de modification d'API publique sur 1 cycle MINOR complet
- Documentation complète et exemples à jour
- Tests à 100 % des branches critiques

La règle s'applique de manière indépendante à chaque package : le
passage de `forge-mvc` à Stable ne tire pas les opt-in avec lui.

---

## Règles Git et tags

### main doit rester stable

- `main` est la branche de référence. Elle doit toujours être dans un état
  déployable et testé.
- Les développements en cours peuvent être regroupés sur `main` entre les
  releases, à condition que chaque commit soit validé (tests passants).
- Un commit de release est distingué des commits de développement par un
  message `release: preparer forge x.y.z`.

### Format de tag

```
vX.Y.Z
```

Exemples :

```
v2.2.0
v2.2.1
v2.3.0
v3.0.0
```

- Les tags utilisent le préfixe `v` (minuscule).
- Les tags sont annotés (`git tag -a`).
- Le tag est créé sur le commit de release, après validation complète.

### Immuabilité des tags publiés

**Un tag publié (poussé sur GitHub) ne doit pas être déplacé ni supprimé.**

Si une erreur est détectée après publication :

- Corriger dans un nouveau commit.
- Créer un nouveau tag de correctif (ex. `v2.2.1`).
- Ne pas modifier le tag `v2.2.0`.

Seuls les tags locaux non poussés peuvent être corrigés. Une fois poussé,
le tag est immuable.

---

## Validation obligatoire

Ces commandes doivent passer sans erreur avant tout tag de release :

```bash
pytest
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
```

Aucune dérogation n'est tolérée. Si une validation échoue, le ticket doit
être corrigé avant le tag.

Voir aussi [Procédure de release](release.md) pour la checklist complète
incluant l'audit des dépendances et la construction de la wheel.

---

## Build wheel

Avant publication, construire la wheel :

```bash
rm -rf dist build *.egg-info
python -m build
ls dist/
```

Vérification minimale de la wheel installée :

```bash
pipx install dist/forge_mvc-X.Y.Z-py3-none-any.whl --force
forge --version
forge starter:list
```

Voir [Validation locale](release-local.md) pour la procédure complète avec
les quatre starters.

---

## Cohérence de version

Avant le tag, vérifier que la version est uniforme sur tous les fichiers :

| Fichier | Clé |
|---|---|
| `pyproject.toml` | `version = "x.y.z"` |
| `forge.py` | `__version__ = "x.y.z"` |
| `core/__init__.py` | `__version__ = "x.y.z"` |
| `README.md` | mentions de version |
| `CHANGELOG.md` | entrée `## [x.y.z]` |

---

## Publication GitHub

Niveaux de publication :

### Release locale (développement et validation)

Avant toute release, exécuter le script de validation :

```bash
bash tools/release-validate.sh <VERSION>
# ex. : bash tools/release-validate.sh {{forge_version}}
```

Ce script vérifie en une seule passe :

1. Cohérence de version (`pyproject.toml`, `core/__init__.py`, `forge.py`)
2. Entrée CHANGELOG présente
3. Tests (`pytest -x -q`)
4. Qualité de code (`ruff check`)
5. Compilation Python (`compileall`)
6. Documentation MkDocs (`mkdocs build --strict`)
7. État git propre (pas de modifications non commitées)
8. Whitespace (`git diff --check`)
9. Tag absent (pré-tag)

Le script quitte avec le code 1 si au moins un `[FAIL]` est détecté.

Checklist manuelle complémentaire :

- Tests OK.
- Version mise à jour sur tous les fichiers.
- Wheel buildée et installée localement.
- Validation CLI et starters OK.

### Release GitHub (publication officielle)

- Tag annoté créé sur le commit de release.
- Tag poussé : `git push origin vX.Y.Z`.
- Release GitHub rédigée depuis l'onglet *Releases* avec le contenu du CHANGELOG.
- Changelog disponible dans `CHANGELOG.md`.

Vérifications post-publication :

- Workflow CI (`tests.yml`) passe sur le tag poussé.
- Déploiement MkDocs (`pages.yml`) déclenché et OK.

### Publication PyPI

**État Forge {{forge_version}} :** le core `forge-mvc` est **publié sur PyPI** sous `forge-mvc=={{forge_version}}`.
`{{forge_version}}` est une préversion bêta PEP 440 — l'option `--pre` est nécessaire pour l'installer.

| Package | Publication PyPI | Notes |
|---|---|---|
| `forge-mvc` (core) | ✅ Publié — `{{forge_version}}` | `pip install --pre forge-mvc` |
| `forge-mvc-mfa` | Prévue après `SEC-MFA-SECRET-ENCRYPTION-001` | mode source-only |
| `forge-mvc-rbac` | Prévue à partir de `1.0.0-beta.5` (`OPTIN-PYPI-PUBLISH-001`) | mode source-only |
| `forge-mvc-workflow` | Prévue à partir de `1.0.0-beta.5` (`OPTIN-PYPI-PUBLISH-001`) | mode source-only |
| `forge-mvc-stats` | Prévue à partir de `1.0.0-beta.5` (`OPTIN-PYPI-PUBLISH-001`) | mode source-only |

Pour les modules opt-in, utiliser [Installation depuis GitHub](installation-github.md).

Procédure de publication (manuelle, délibérée) :

```bash
python -m build --wheel --sdist
twine upload --repository testpypi dist/forge_mvc-X.Y.Z*  # TestPyPI d'abord
twine upload dist/forge_mvc-X.Y.Z*                         # PyPI réel
```

Précautions spécifiques à PyPI :

- Un numéro de version publié sur PyPI **ne peut pas être republié** sous le même nom.
- Toujours tester avec TestPyPI avant toute publication.
- Ne jamais publier un build non validé localement.
- Mettre à jour `CHANGELOG.md` avant la publication.

PyPI n'est pas automatisé dans la procédure actuelle. La publication
reste manuelle et délibérée.

---

## Verrouillage packaging

### État actuel des packages (PACKAGE-LOCK-DOC-001)

| Package | Statut PyPI | Règle |
|---|---|---|
| `forge-mvc` (core) | ✅ Publié — `{{forge_version}}` | Publié dès `1.0.0-beta.1` |
| `forge-mvc-rbac` | Source-only jusqu'à `1.0.0-beta.5` — **prêt à publier** | Dépendance relâchée, `Private :: Do Not Upload` retiré (`OPTIN-PYPI-PUBLISH-PREPARE-001`) |
| `forge-mvc-workflow` | Source-only jusqu'à `1.0.0-beta.5` — **prêt à publier** | Dépendance relâchée, `Private :: Do Not Upload` retiré (`OPTIN-PYPI-PUBLISH-PREPARE-001`) |
| `forge-mvc-stats` | Source-only jusqu'à `1.0.0-beta.5` — **prêt à publier** | Dépendance relâchée, `Private :: Do Not Upload` retiré (`OPTIN-PYPI-PUBLISH-PREPARE-001`) |
| `forge-mvc-mfa` | Non publié PyPI en `1.0` | Pre-Alpha — `SEC-MFA-SECRET-ENCRYPTION-001` requis avant publication |
| `forge-mvc-media` | Source-only — squelette Phase 11 | Extraction en cours — non publié PyPI (`MEDIA-EXTRACT-PACKAGE-SCAFFOLD-001`) |

### Règles de version

- **Jusqu'à `1.0.0-beta.4`** : seul le core `forge-mvc` est bumped à chaque release. Les opt-ins source-only conservent leur version interne.
- **À partir de `1.0.0-beta.5`** : le core et les opt-ins publiés (`rbac`, `workflow`, `stats`) doivent être strictement synchronisés sur la même version.
- `forge-mvc-mfa` ne rejoindra pas ce flux en `1.0` — sa publication est conditionnée à `SEC-MFA-SECRET-ENCRYPTION-001`.

### Artefacts de build

Les répertoires `dist/`, `build/` et `*.egg-info/` sont des artefacts de validation locale.
Ils sont exclus de Git (`.gitignore`) et **ne doivent pas être commités**.

```bash
# Validation locale uniquement — ne publie rien
python -m build
twine check dist/*
```

`twine check` valide les métadonnées localement sans rien publier sur PyPI.
`twine upload` est l'opération de publication, réservée à un ticket release dédié.

### Règle générale

Toute publication PyPI est une action délibérée relevant d'un ticket de release dédié.
Aucune automatisation ne déclenche la publication.

---

## Politique de publication des opt-ins

### État actuel

`forge-mvc` (core) est publié sur PyPI depuis `1.0.0-beta.1`.
Les packages opt-in (`forge-mvc-rbac`, `-workflow`, `-stats`, `-mfa`) suivent des règles de publication distinctes documentées ici.

Cette politique est livrée par le ticket `OPTIN-PACKAGES-PUBLICATION-POLICY-001`.

### Core publié sur PyPI

`forge-mvc` est le seul package publié sur PyPI jusqu'à `1.0.0-beta.4` inclus.
Il est le point d'entrée officiel du framework.

### Opt-ins source-only avant beta.5

Les opt-ins `forge-mvc-rbac`, `forge-mvc-workflow` et `forge-mvc-stats` sont disponibles en **source-only** via GitHub jusqu'à `1.0.0-beta.5` :

- non publiés sur PyPI ;
- installables depuis le dépôt GitHub (voir `docs/installation-github.md`) ;
- versionnés indépendamment du core jusqu'à la publication coordonnée.

### Opt-ins publiables à partir de beta.5

À partir de `1.0.0-beta.5`, les trois opt-ins suivants rejoignent PyPI avec une publication coordonnée :

| Package | Publication | Prérequis |
|---|---|---|
| `forge-mvc-rbac` | PyPI à beta.5 | Publication coordonnée (`OPTIN-PYPI-PUBLISH-001`) |
| `forge-mvc-workflow` | PyPI à beta.5 | Publication coordonnée (`OPTIN-PYPI-PUBLISH-001`) |
| `forge-mvc-stats` | PyPI à beta.5 | Publication coordonnée (`OPTIN-PYPI-PUBLISH-001`) |

La publication est strictement synchronisée : core et opt-ins portent la même version.

### Cas particulier : forge-mvc-mfa

`forge-mvc-mfa` n'est **pas publié sur PyPI en série 1.0**.

Raisons :

- statut Pre-Alpha (`Development Status :: 2 - Pre-Alpha`) ;
- le secret TOTP est stocké en clair — non recommandé en production sans protection additionnelle ;
- le chiffrement applicatif (`SEC-MFA-SECRET-ENCRYPTION-001`) est requis avant toute publication PyPI.

Le module passe en Beta et rejoint PyPI uniquement après livraison de `SEC-MFA-SECRET-ENCRYPTION-001`.
En attendant, l'installation se fait depuis GitHub (source-only).

### Extras PyPI

Les extras `forge-mvc[rbac]`, `forge-mvc[workflow]`, `forge-mvc[stats]` ne sont disponibles qu'à partir de la publication coordonnée (`1.0.0-beta.5`).

`forge-mvc[mfa]` n'est **pas déclaré** dans les extras PyPI en série 1.0.
`forge-mvc[all]` n'inclut pas `forge-mvc-mfa`.

### Règles de version

- **Jusqu'à `1.0.0-beta.4`** : seul le core `forge-mvc` est versionné à chaque release.
- **À partir de `1.0.0-beta.5`** : core et opt-ins publiés (`rbac`, `workflow`, `stats`) sont strictement synchronisés sur la même version.
- `forge-mvc-mfa` ne rejoint pas ce flux en série 1.0.

### Ce qui est interdit avant publication coordonnée

- `twine upload` pour un opt-in source-only — interdit avant `beta.5` ;
- déclarer `forge-mvc[mfa]` dans les extras PyPI — interdit en série 1.0 ;
- inclure `forge-mvc-mfa` dans `forge-mvc[all]` — interdit tant que Pre-Alpha ;
- publier `forge-mvc-mfa` sans livrer `SEC-MFA-SECRET-ENCRYPTION-001` — interdit.

### Tickets liés

| Ticket | Description | État |
|---|---|---|
| `OPTIN-PACKAGES-PUBLICATION-POLICY-001` | Documenter la politique de publication des opt-ins | livré |
| `OPTIN-PYPI-NAMES-CHECK-001` | Vérifier la disponibilité des noms PyPI pour les 5 opt-ins | livré |
| `OPTIN-PYPI-PUBLISH-PREPARE-001` | Préparer rbac/workflow/stats pour publication (dépendances relâchées, `Private :: Do Not Upload` retiré) | livré |
| `OPTIN-PYPI-PUBLISH-001` | Publication coordonnée des opt-ins à beta.5 | conditionné à beta.5 |
| `SEC-MFA-SECRET-ENCRYPTION-001` | Chiffrement applicatif — prérequis à la publication de forge-mvc-mfa | post-1.0 |

---

## Changelog

Chaque release doit avoir une entrée dans `CHANGELOG.md` avec la structure :

```markdown
## [X.Y.Z] — YYYY-MM-DD

### Ajouté

- Nouvelle fonctionnalité (TICKET-001).

### Modifié

- Comportement modifié (TICKET-002).

### Corrigé

- Bug corrigé (TICKET-003).

### Sécurité

- Durcissement (TICKET-004).

### Documentation

- Guide ajouté (TICKET-005).

### Tests

- Tests ajoutés (TICKET-006).
```

Ne lister que les sections non vides. Chaque entrée référence le ticket associé.

---

## Roadmap et tickets

La roadmap (`docs/roadmap/forge-roadmap.md`) est la source de vérité
pour l'état d'avancement des tickets.

Règles :

- Un ticket livré doit être marqué `**livré**` dans la roadmap.
- La prochaine priorité doit être indiquée clairement dans la roadmap.
- Les limites restantes doivent être reportées dans les tickets futurs.
- Les tickets futurs doivent être bornés — ne pas créer de tickets ouverts sans
  critères d'acceptation.
- La roadmap ne doit pas lister des ambitions non bornées comme des tickets actifs.

---

## Ce que cette politique ne couvre pas encore

| Domaine | Ticket futur |
|---|---|
| Politique de dépréciation officielle — préavis, cycle de vie des APIs | `RELEASE-DEPRECATION-001` — voir [deprecation-policy.md](deprecation-policy.md) |
| Matrice de compatibilité Python / MariaDB / Node | `RELEASE-COMPAT-001` |
| Guide de migration entre versions majeures | `RELEASE-MIGRATION-GUIDE-001` |
| Politique LTS (Long Term Support) | `RELEASE-LTS-001` |
| Automatisation CI/CD release (wheel, PyPI, GitHub Release automatique) | post-roadmap |
| Versionnement des modules Forge indépendamment du core | post-roadmap |
| Semantic Release automatique basé sur les messages de commit | post-roadmap |

---

## Voir aussi

- [Vue d'ensemble Release et compatibilité](release-and-compatibility.md)
- [Politique de dépréciation](deprecation-policy.md) — cycle annonce → retrait
- [Matrice de compatibilité](compatibility.md) — Python, MariaDB, Node.js
- [Guide de migration](migration-guide.md) — passer d'une version à l'autre
- [Contrat de stabilité](stability-contract.md) — API publique, interne, expérimentale

---

*Guide défini lors de RELEASE-POLICY-001 (Phase 8 — Release et compatibilité).*
