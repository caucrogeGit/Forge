# Guide de migration Forge

Ce guide explique comment passer d'une version Forge à une autre en toute sécurité.

Il complète :

- [Politique de release](release-policy.md) — règles MAJOR/MINOR/PATCH
- [Politique de dépréciation](deprecation-policy.md) — cycle annonce → retrait
- [Matrice de compatibilité](compatibility.md) — Python, MariaDB, Node.js
- [Contrat de stabilité](stability-contract.md) — ce qui est stable, interne, expérimental

---

## Objectif

Une migration Forge doit être :

- **explicite** — savoir ce qui change avant de migrer ;
- **vérifiable** — des commandes confirment que le projet fonctionne après ;
- **réversible** — un rollback propre doit être possible avant d'appliquer des migrations SQL ;
- **respectueuse du code utilisateur** — aucun fichier modifié manuellement ne doit être écrasé ;
- **accompagnée par les commandes DX** de Forge.

---

## Identifier la version actuelle

Avant toute migration, vérifier la version installée :

```bash
forge --version
```

Vérifier que le projet est dans un état propre :

```bash
git status
git log --oneline -5
```

**Ne jamais migrer avec un working tree sale.**

---

## Lire la politique de release

La politique de release Forge définit trois niveaux :

| Niveau | Quand | Impact |
|---|---|---|
| PATCH | Corrections, sécurité compatible | Aucune rupture attendue |
| MINOR | Nouvelles fonctionnalités compatibles | Opt-in, pas de rupture |
| MAJOR | Ruptures d'API stable | Migration explicite requise |

Lire [docs/release-policy.md](release-policy.md) avant toute migration.

---

## Lire la politique de dépréciation

Le cycle de dépréciation Forge garantit qu'une fonctionnalité stable ne disparaît jamais sans préavis :

```
Annonce en N.x → Maintien garanti jusqu'à fin de série N → Retrait possible en (N+1).0.0
```

Avant de migrer, vérifier les dépréciations actives dans `CHANGELOG.md` et [docs/deprecation-policy.md](deprecation-policy.md).

---

## Vérifier la compatibilité

Avant de migrer, vérifier que l'environnement reste compatible :

- **Python** : la version installée doit être dans la plage supportée.
- **MariaDB** : le connecteur `mariadb` doit rester compatible.
- **Node.js** : uniquement si le build CSS Tailwind est utilisé.

Consulter la [matrice de compatibilité](compatibility.md) pour les versions officielles.

---

## Sauvegarder le projet

Avant toute migration :

```bash
# Sauvegarder le code source
git commit -am "sauvegarde avant migration Forge X.Y.Z"
git push

# Sauvegarder la base de données
mysqldump -u utilisateur -p nom_base > sauvegarde_avant_migration.sql
```

Ne jamais appliquer de migration SQL (`db:init`, `db:apply`) sur une base de production sans sauvegarde préalable.

---

## Commandes de vérification avant migration

Lancer ces commandes avant de mettre à jour Forge :

```bash
forge --version           # version installée
forge doctor              # santé globale du projet
forge project:check       # cohérence structure
forge project:audit       # rapport détaillé
pytest                    # suite de tests du projet
python -m compileall -q . # intégrité des imports Python
```

Si l'une de ces commandes échoue, corriger avant de migrer.

---

## Mettre à jour Forge

### Depuis PyPI (installation officielle)

```bash
pipx upgrade forge-mvc
```

ou

```bash
pip install --upgrade forge-mvc
```

### Depuis GitHub (installation depuis les sources)

```bash
git pull origin main
pip install -e .
```

### Vérifier la mise à jour

```bash
forge --version
```

---

## Migration PATCH

Un PATCH corrige des bugs ou des problèmes de sécurité sans modifier les interfaces.

**Exemple :** `2.2.0 → 2.2.1`

### Ce qui peut changer

- Corrections de bugs sans modification d'API.
- Durcissements de sécurité sans changement d'interface.
- Corrections de documentation.
- Tests supplémentaires.

### Ce qui ne change pas

- Interface CLI documentée.
- Structure de projet générée.
- API Python publique.
- Clés `.env`.
- Fichiers générés existants.

### Validation après migration PATCH

```bash
forge --version
forge doctor
forge project:check
pytest
```

Un PATCH ne doit pas nécessiter d'intervention sur le projet existant.

---

## Migration MINOR

Un MINOR peut ajouter des fonctionnalités et de nouvelles commandes sans briser l'existant.

**Exemple :** `2.2.0 → 2.3.0`

### Ce qui peut changer

- Nouvelles commandes CLI (opt-in).
- Nouvelles options CLI.
- Nouveaux modules optionnels.
- Nouvelles conventions de fichiers générés (sans écraser l'existant).
- Nouvelles clés `.env` optionnelles.
- Nouvelles dépréciations annoncées.

### Ce qui ne change pas

- Les commandes CLI existantes documentées.
- Les fichiers déjà générés et modifiés.
- Les conventions de projet existantes.
- L'API Python publique existante.

### Validation après migration MINOR

```bash
forge --version
forge doctor
forge project:check
forge project:audit
pytest
python -m compileall -q .
```

Lire attentivement le `CHANGELOG.md` pour identifier les nouvelles dépréciations à noter.

---

## Migration MAJOR

Un MAJOR peut introduire des ruptures d'API stable. C'est le seul niveau qui autorise le retrait de fonctionnalités stables précédemment dépréciées.

**Exemple :** `2.x → 3.0.0`

### Avant de commencer

**Créer une branche de migration dans le projet applicatif :**

```bash
git checkout -b migration/forge-3.0
```

### Ce qui peut changer

- Suppression de commandes CLI dépréciées.
- Suppression d'options CLI dépréciées.
- Suppression d'API Python publiques dépréciées.
- Modification incompatible de la structure de projet générée.
- Renommage ou suppression de clés `.env` dépréciées.

### Ce qui ne change pas sans guide explicite

Un guide de migration spécifique est publié avec chaque version MAJOR. Aucune rupture non documentée n'est introduite en version MAJOR.

### Étapes d'une migration MAJOR

1. **Lire le guide de migration spécifique** fourni avec la version MAJOR.
2. **Identifier les dépréciations retirées** dans le CHANGELOG.
3. **Remplacer les fonctionnalités retirées** par leurs alternatives documentées.
4. **Comparer les fichiers générés** si la structure de projet a changé.
5. **Tester les routes, templates et modules**.
6. **Appliquer les migrations SQL** sur une base de test avant la production.

### Validation après migration MAJOR

```bash
forge --version
forge doctor
forge project:check
forge project:audit
python -m compileall -q .
ruff check .
pytest
mkdocs build --strict   # si le projet contient une documentation
git diff --check
```

---

## Fichiers générés et fichiers utilisateur

Forge distingue deux types de fichiers dans un projet :

### Fichiers régénérables (Forge peut les écraser)

Ces fichiers peuvent être régénérés sans perte :

| Fichier | Régénéré par |
|---|---|
| `mvc/entities/<E>/<E>_base.py` | `forge sync:entity` |
| `mvc/entities/<E>/<E>.sql` | `forge sync:entity` |

**`sync:entity` préserve le fichier modèle manuel** (`<E>.py`) et **écrase uniquement** `_base.py` et `.sql`.

### Fichiers préservés (Forge ne les écrase jamais)

Ces fichiers sont créés une fois puis jamais réécrasés par Forge :

| Fichier | Généré initialement par |
|---|---|
| `mvc/controllers/<E>_controller.py` | `forge make:crud` |
| `mvc/models/<E>.py` | `forge make:entity` |
| `mvc/forms/<E>_form.py` | `forge make:crud` |
| `mvc/views/<E>/*.html` | `forge make:crud` |
| `mvc/routes.py` | `forge new` |
| `static/` (fichiers utilisateur) | manuellement |

**Principe :** `make:entity` et `make:crud` refusent d'écraser un fichier existant. Cette garantie est couverte par les tests E2E (`E2E-NON-OVERWRITE-001`).

### Comportement lors d'une migration

Après une mise à jour de Forge :

- Les fichiers générés **existants** ne sont pas modifiés automatiquement.
- Les **nouveaux** projets créés après la mise à jour reçoivent les gabarits mis à jour.
- Si un gabarit de génération change, les fichiers existants restent inchangés.
- Si une migration de fichiers est nécessaire, elle est documentée dans le guide de migration MAJOR.

---

## Commandes de vérification après migration

Après avoir mis à jour Forge et adapté le projet :

```bash
# Santé globale
forge doctor

# Cohérence du projet
forge project:check

# Rapport détaillé
forge project:audit

# Tests du projet
pytest

# Intégrité des imports
python -m compileall -q .
```

---

## Gestion des dépréciations

### Repérer une dépréciation

Une fonctionnalité dépréciée peut se signaler de plusieurs façons :

**Commande CLI dépréciée :**

```
AVERTISSEMENT — forge old:command est dépréciée.
Utiliser désormais : forge new:command
Suppression prévue : prochaine version MAJOR.
```

**API Python dépréciée :**

```python
DeprecationWarning: ancienne_fonction() est dépréciée depuis Forge 2.4.0.
Utiliser nouvelle_fonction() à la place. Suppression prévue à la prochaine version MAJOR.
```

**Convention documentaire :**
- Note dans `docs/` + entrée `CHANGELOG.md`.

### Gérer une dépréciation

1. Identifier l'alternative recommandée dans le message ou la documentation.
2. Mettre à jour le code avant la version MAJOR de retrait.
3. Tester après la migration.

---

## Gestion des migrations SQL

Les migrations SQL Forge concernent les projets applicatifs, pas le framework lui-même.

### Règles à respecter

- **Ne jamais appliquer `db:init` ou `db:apply` sur une base de production sans sauvegarde.**
- Tester d'abord sur une base de staging ou sur une base dédiée aux tests (`forge_e2e_*`).
- Comparer les fichiers `.sql` générés avant et après `sync:entity`.
- En cas de doute, inspecter manuellement le SQL avant de l'appliquer.

### Commandes concernées

```bash
forge db:init          # crée la base et applique les entités
forge db:apply         # applique les migrations
forge sync:entity      # régénère _base.py et .sql depuis entity.json
```

**Forge ne fournit pas encore de système de migrations versionnées au sens strict** (type Alembic). Les fichiers SQL générés reflètent l'état courant des entités. Toute modification de schéma doit être gérée manuellement ou via des scripts SQL dédiés.

---

## Cas des starters

Les starters Forge sont des démonstrateurs, pas des templates applicatifs à synchroniser automatiquement.

Après une migration Forge :

- Les starters installés ne sont pas mis à jour automatiquement.
- Si le gabarit d'un starter change, le projet généré depuis ce starter existant n'est pas modifié.
- `forge project:audit` peut détecter des incohérences structurelles dans un projet généré depuis un ancien starter.

### Recommandation

```bash
forge project:audit
```

Corriger les avertissements relevés par `project:audit` avant de déployer en production.

---

## Cas des modules

Après une migration Forge :

- Les modules installés (`forge_modules.json`) restent en place.
- `forge project:check` vérifie la cohérence des modules déclarés.
- `forge project:audit` signale les incohérences de routes ou de fichiers.

```bash
forge project:check
forge project:audit
```

Si un module utilise une API Forge dépréciée, le mettre à jour avant la version MAJOR de retrait.

---

## Rollback

Si une migration échoue ou introduit une régression :

### Rollback du code

```bash
# Revenir au commit avant migration dans le projet applicatif
git checkout main     # ou la branche précédente
git log --oneline -5  # identifier le commit de référence
git checkout <commit-hash>
```

ou

```bash
git revert HEAD
```

### Rollback de Forge

```bash
pipx install forge-mvc==2.2.0 --force   # version précise
forge --version                          # vérifier
```

### Rollback de la base de données

Si une migration SQL a été appliquée de manière irréversible :

```bash
mysql -u utilisateur -p nom_base < sauvegarde_avant_migration.sql
```

**Ne jamais rollback partiellement le code sans rollback de la base si des migrations SQL incompatibles ont été appliquées.**

---

## Checklist de migration

Avant de migrer :

- [ ] Identifier la version actuelle (`forge --version`).
- [ ] Lire le `CHANGELOG.md` de la version cible.
- [ ] Lire les dépréciations actives dans `docs/deprecation-policy.md`.
- [ ] Vérifier la compatibilité dans `docs/compatibility.md`.
- [ ] Sauvegarder le code (`git commit`, `git push`).
- [ ] Sauvegarder la base de données (`mysqldump`).
- [ ] Vérifier l'état du projet (`forge doctor`, `forge project:check`, `pytest`).

Après la migration :

- [ ] Vérifier la version installée (`forge --version`).
- [ ] Lancer `forge doctor`.
- [ ] Lancer `forge project:check`.
- [ ] Lancer `forge project:audit`.
- [ ] Lancer `pytest`.
- [ ] Lancer `python -m compileall -q .`.
- [ ] Vérifier les avertissements de dépréciation.
- [ ] Tester les routes principales manuellement.
- [ ] Valider les migrations SQL sur base de staging avant production.

---

## Limites restantes

| Domaine | Limite |
|---|---|
| Migrations SQL versionnées | Pas de système type Alembic — SQL généré à état courant uniquement |
| Détection automatique des dépréciations | Pas d'outil de scan automatique — lecture manuelle du CHANGELOG |
| Tests E2E starters 2, 4, 5 | Partiellement couverts — vérifier `forge project:audit` |
| Rollback SQL automatique | Pas supporté — sauvegarde manuelle obligatoire |
| Guide MAJOR spécifique | À créer lors de la première migration 2.x → 3.0.0 |

---

## Ce que ce guide ne couvre pas encore

| Domaine | Ticket futur |
|---|---|
| Politique LTS (Long Term Support) | `RELEASE-LTS-001` |
| Guide de migration entre anciennes séries et trajectoire 1.0.0 | À créer avant la version stable `1.0.0` |
| Outil de détection automatique des dépréciations | post-roadmap |
| Migrations SQL versionnées | post-roadmap |

---

## Voir aussi

- [Vue d'ensemble Release et compatibilité](release-and-compatibility.md)
- [Politique de release](release-policy.md) — règles PATCH/MINOR/MAJOR
- [Politique de dépréciation](deprecation-policy.md) — cycle annonce → retrait
- [Matrice de compatibilité](compatibility.md) — versions supportées
- [Sécurité en production](production-security.md) — checklist avant déploiement

---

*Guide défini lors de RELEASE-MIGRATION-GUIDE-001 (Phase 8 — Release et compatibilité).*
