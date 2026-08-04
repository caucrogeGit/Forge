# Procédure de release Forge

Ce document est la checklist officielle à suivre avant chaque tag de release.
Il est destiné au mainteneur du framework.

---

## Objectif

Garantir que chaque version publiée de Forge est :

- validée par les tests automatiques ;
- cohérente en version sur tous les fichiers concernés ;
- documentée dans `CHANGELOG.md` ;
- construite proprement sous forme de wheel ;
- poussée avec un tag annoté versionné.

---

## Quand créer une release

Une release est créée :

- à la fin d'un sprint de la roadmap post-1.0 (ex. : v1.0.2 après sprint 2) ;
- pour une correction critique de sécurité (release corrective, ex. v1.0.x) ;
- pour une version de consolidation ou d'élargissement (ex. v1.1.0).

Une release **ne mélange pas** le travail de développement en cours avec la finalisation d'un sprint.
Si des tickets du sprint suivant sont déjà ouverts, ils restent en branche ou en liste d'attente.

---

## Checklist avant release

Les points 1 à 7 sont automatisés par un seul script :

```bash
bash tools/release-validate.sh <VERSION>
```

Il accepte la version en SemVer (`{{forge_tag}}` sans le `v`) comme en PEP 440 (`{{forge_version}}`), et enchaîne la cohérence de version, les tests, Ruff, `compileall`, MkDocs strict et `pip-audit`.
Il se termine par `RÉSULTAT : OK - prêt à releaser.`

Les points ci-dessous détaillent ce qu'il contrôle, et servent à diagnostiquer un échec.

### 1. Working tree propre

```bash
git status
```

Le working tree doit être propre. Aucun fichier modifié non commité.

### 2. Tests automatiques

```bash
python -m pytest
```

Tous les tests doivent passer. Aucune régression tolérée.

### 3. Validation compilation

```bash
python -m compileall -q .
```

Aucune erreur de syntaxe Python.

### 4. Documentation MkDocs

```bash
mkdocs build --strict
```

Aucune ancre cassée, aucun lien interne invalide.

### 5. Espaces blancs et fin de ligne

```bash
git diff --check
```

Aucun espace de fin de ligne, aucune erreur de formatage.

### 6. Lint Python (Ruff)

```bash
ruff check .
```

Aucune erreur de lint (règles E, F). Les règles E501, E741, E402 sont ignorées délibérément.
Si de nouvelles violations apparaissent, les corriger avant de publier.

### 7. Audit des dépendances

```bash
pip-audit -r requirements.txt
pip-audit -r requirements-dev.txt
```

Aucune vulnérabilité critique connue dans les dépendances.
Si `pip-audit` signale un problème, créer un ticket `DEPENDENCY-FIX-XXX` avant de publier.

### 8. Construction des distributions

Forge n'est pas une distribution mais un jeu de distributions.
Le cœur `forge-mvc` et chaque opt-in de `packages/` ont leur propre `pyproject.toml`.
Un `python -m build` lancé à la racine ne construit que le cœur, et laisse les opt-ins à leur version précédente sur PyPI.

Construire l'ensemble avec le script dédié :

```bash
bash tools/release-build.sh
```

Il construit toutes les distributions dans `dist/`, puis passe `twine check`.
Il ne publie rien.

Le compte attendu n'est pas écrit ici : il a valu 13, puis 25, puis 28.
C'est `tools/release-build.sh` qui l'établit à chaque passage, et le garde-fou `RELEASE-PYPI-COMPLETENESS-GUARD-001` qui refuse qu'un paquet neuf soit oublié.

---

## Validation CLI installée

Après construction, valider la wheel installée localement.
Voir [Validation locale](release-local.md) pour la procédure détaillée.

Résumé minimal :

```bash
pipx install dist/forge_mvc-<version>-py3-none-any.whl --force
forge --version
```

`forge --version` doit afficher la version installée sans erreur.

Pour la validation des parcours pédagogiques, voir la procédure dans [Validation locale](release-local.md).

---

## Contrôle de cohérence de version

Avant de créer le tag, vérifier que la version est uniforme sur tous les fichiers :

| Fichier | Clé |
|---|---|
| `pyproject.toml` | `version = "x.y.z"` |
| `forge.py` | `__version__ = "x.y.z"` |
| `core/__init__.py` | `__version__ = "x.y.z"` |
| `README.md` | badge et mentions de version |
| `CHANGELOG.md` | entrée `## [x.y.z] - YYYY-MM-DD` |
| `docs/roadmap/forge-roadmap.md` | tag recommandé et état actuel |

Commande de recherche rapide :

```bash
grep -rn "x\.y\.z\|vx\.y\.z" pyproject.toml forge.py core/__init__.py README.md CHANGELOG.md docs/ || true
```

Adapter `x.y.z` et `vx.y.z` à la version cible (ex. `2\.0\.2` et `v2\.0\.2`).

> **Numéros brûlés** : avant de figer la version cible, vérifier qu'elle
> n'est pas dans la liste des [numéros de version brûlés](burned-version-numbers.md).
> Les versions `1.0.1` et `1.1.0` ont été supprimées de PyPI et ne pourront
> jamais être republiées : ne pas les bumper ni les taguer.

---

## CHANGELOG

`CHANGELOG.md` doit être mis à jour **avant** le commit de release.

Structure attendue pour chaque entrée :

```markdown
## [x.y.z] - YYYY-MM-DD

### Ajouté

- ...

### Modifié

- ...

### Corrigé

- ...

### Sécurité

- ...

### Documentation

- ...

### Tests

- ...
```

Ne lister que les sections non vides. Chaque ligne doit référencer le ticket correspondant entre parenthèses.

---

## Commit de release

```bash
git status
git add pyproject.toml forge.py core/__init__.py CHANGELOG.md docs/
git commit -m "release: preparer forge x.y.z"
```

Les fichiers exacts dépendent de la release. Le message de commit commence toujours par `release:`.

Vérifier après commit :

```bash
git log --oneline -3
git diff --check
```

---

## Push GitHub

```bash
git push origin main
```

Le tag n'est pas poussé ici. Il vient en dernier, une fois la publication faite.

Laisser la CI confirmer sur `main` avant de publier.

---

## Publication PyPI

```bash
bash tools/publish.sh
```

Sans option, le script est en simulation. Il construit, vérifie et affiche l'ordre de publication, sans rien envoyer.

Quand la séquence affichée est la bonne :

```bash
bash tools/publish.sh --upload
```

Le cœur `forge-mvc` part en premier, les opt-ins en dépendent.
Chaque envoi passe `--skip-existing`, ce qui rend le script reprenable.
PyPI limite la création de projets neufs et répond parfois 429 : dans ce cas, attendre puis relancer la même commande, elle saute les distributions déjà publiées.

---

## Création du tag

Le tag vient **après** la publication, et il se pose sur le commit publié.

C'est l'ordre qui a manqué à la `v1.0.0-rc.3`.
Le tag avait été posé avant la fin du travail, puis un correctif de sécurité est parti sur `main` : le tag désignait un code que personne n'avait publié, et il a fallu le déplacer.
Un tag déplacé est un tag que d'autres ont déjà pu récupérer.

```bash
git tag -a vx.y.z -m "Forge x.y.z"
git tag --points-at HEAD
git push origin vx.y.z
```

Vérifier que le tag est visible sur GitHub avant de créer la release.

---

## Après publication

1. Créer la release GitHub depuis l'onglet *Releases* avec le contenu du CHANGELOG.
2. Mettre à jour la roadmap : marquer le sprint terminé, positionner la prochaine priorité.
3. Vérifier que le workflow CI (`tests.yml`) passe sur le tag poussé.
4. Vérifier que le déploiement MkDocs (`pages.yml`) s'est bien déclenché.

---

## Ce que la release ne doit pas faire

- Introduire un nouveau comportement fonctionnel non prévu dans le sprint.
- Corriger un bug non planifié (créer un ticket, corriger dans le prochain sprint ou une release corrective dédiée).
- Mélanger release et développement dans le même commit.
- Déplacer ou supprimer un tag déjà publié.
- Ignorer une validation cassée (`pytest`, `mkdocs`, `compileall`).
- Publier si le working tree n'est pas propre.
- Publier sans entrée dans `CHANGELOG.md`.
