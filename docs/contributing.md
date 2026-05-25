# Contribuer à Forge

Ce guide explique comment contribuer au framework Forge de façon correcte et
durable, en respectant la philosophie et les règles du projet.

---

## Objectif

Une contribution à Forge doit rendre le framework :

- **plus clair** — le comportement est lisible, pas inféré ;
- **plus testable** — le nouveau code est couvert et vérifiable ;
- **plus générique** — les briques restent indépendantes du métier ;
- **plus maintenable** — un autre développeur peut reprendre là où on s'est arrêté.

Une contribution ne doit pas rendre Forge :

- plus magique (comportement implicite difficile à déboguer) ;
- plus spécialisé (logique métier dans le cœur du framework) ;
- plus fragile (régressions non détectées) ;
- plus difficile à expliquer dans la documentation.

---

## Philosophie de contribution

Forge est un framework Python explicite, pédagogique et durable.

Quelques principes fondamentaux :

- **Un ticket = une responsabilité** — chaque contribution a un périmètre borné.
- **`main` doit rester stable** — les tests passent en permanence.
- **Les changements sont testés** — aucune brique sans couverture.
- **La documentation est mise à jour** — une fonctionnalité non documentée est incomplète.
- **Les limites restantes sont explicites** — ce qu'on ne couvre pas encore est dit.
- **Pas de transformation en application métier** — `core/` reste générique.
- **Pas de magie cachée** — le comportement est traçable dans le code.

---

## Préparer l'environnement

### Cloner le dépôt

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
```

### Créer un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate
```

### Installer les dépendances

```bash
# Dépendances de développement (inclut le runtime + pytest + ruff + mkdocs + pip-audit)
pip install -r requirements-dev.txt
```

### Vérifier l'installation

```bash
python -m pytest --tb=short -q
python -m compileall -q .
ruff check .
mkdocs build --strict
```

Un environnement sain passe les quatre contrôles sans erreur ni avertissement.

---

## Comprendre l'architecture

```text
core/          Briques génériques du framework : HTTP, sessions, sécurité, formulaires,
               templates, uploads, modules, authentification, base de données...
               Ne doit contenir aucune logique métier applicative.

forge_cli/     Commandes et générateurs Forge : make:entity, make:crud, sync:entity,
               starter:build, module:install, deploy:init, project:check...
               Orchestre les briques core/ et génère les fichiers projet.

mvc/           Squelette applicatif généré par forge new.
               Contient les entités, contrôleurs, modèles, formulaires et vues.
               Modifiable par l'utilisateur — certains fichiers sont préservés.

docs/          Documentation MkDocs complète du framework.
               Chaque fonctionnalité doit être documentée ici.

tests/         Suite de tests de non-régression.
               Couvre le runtime, les générateurs, les starters, les modules,
               la sécurité et la documentation.

starters/      Données des starters officiels Forge (dans forge_cli/starters/data/).
               Chaque starter inclut ses entités, ses routes et ses fichiers applicatifs.
```

Guides de référence pour comprendre les contrats :

- [Contrat de stabilité](stability-contract.md) — fichiers garantis préservés
- [Référence API et CLI](reference.md) — toutes les commandes disponibles
- [Guide de migration](migration-guide.md) — compatibilité entre versions
- [Politique de release](release-policy.md) — SemVer adapté à Forge
- [Politique de dépréciation](deprecation-policy.md) — cycle d'annonce et de retrait
- [Matrice de compatibilité](compatibility.md) — Python, MariaDB, dépendances

---

## Choisir un ticket

Avant de coder :

1. **Prenez un ticket borné** — un seul sujet, un seul périmètre.
2. **Ne mélangez pas plusieurs sujets** — une correction de bug et une refactorisation sont deux tickets distincts.
3. **Auditez l'existant** — lisez le code actuel avant de l'écrire.
4. **Identifiez les fichiers concernés** — notez ce qui sera créé, modifié ou lu.
5. **Explicitez ce qui est hors périmètre** — ce que le ticket ne fera pas.

Un bon ticket indique :

- l'objectif précis ;
- les fichiers probablement concernés ;
- les interdictions explicites ;
- les critères d'acceptation mesurables.

---

## Règle : un ticket = une responsabilité

Chaque ticket doit répondre à une seule question :

```text
Qu'est-ce que ce ticket change, ajoute ou corrige exactement ?
```

Si la réponse contient "et aussi", c'est probablement deux tickets.

**Exemples de périmètre correct :**

- Ajouter la validation de `MAJOR.MINOR.PATCH` dans le manifeste de module
- Documenter le guide de migration
- Ajouter les tests E2E du cycle module install → remove

**Exemples de périmètre trop large :**

- Refactoriser `core/` et ajouter les tests et mettre à jour la doc
- Corriger un bug et améliorer les performances et réécrire le tutoriel

---

## Modifier le code

Règles à respecter lors de toute modification :

- **Préserver les fichiers utilisateur** — les fichiers générés marqués comme préservés ne doivent jamais être écrasés sans `--force` explicite.
- **Ne pas casser les générateurs** — `make:entity`, `make:crud`, `sync:entity` doivent continuer à fonctionner.
- **Ne pas changer une convention stable** — un changement de convention (nommage, structure JSON, format de fichier) sans ticket de dépréciation est une rupture de contrat.
- **Ne pas ajouter de dépendance sans nécessité** — les dépendances runtime du core sont limitées à `mariadb`, `jinja2`, `python-dotenv`, `Pillow`, `argon2-cffi`. Les dépendances des modules opt-in (ex. `pyotp` pour MFA) ne font pas partie du core.
- **Ne pas modifier la version** — la version dans `pyproject.toml` / `forge.py` / `core/__init__.py` n'est modifiée que par un ticket release dédié.
- **Ne pas créer de tag manuellement** — les tags de version sont créés en suivant la [Procédure de release](release.md).

---

## Ajouter ou modifier les tests

Chaque nouvelle brique doit avoir ses tests. Forge distingue plusieurs types :

| Type | Localisation | Rôle |
|---|---|---|
| **Tests unitaires** | `tests/test_<module>.py` | Vérifient une fonction ou une classe isolée |
| **Tests comportementaux** | `tests/test_<module>.py` | Vérifient un flux runtime, une CLI, un générateur ou une intégration |
| **Tests E2E CLI** | `tests/test_e2e_cli.py` | Vérifient les commandes Forge dans un projet temporaire |
| **Tests E2E starters** | `tests/test_e2e_starter.py` | Vérifient le build complet d'un starter |
| **Tests E2E modules** | `tests/test_e2e_module.py` | Vérifient le cycle install → files → routes → remove d'un module |
| **Tests sécurité** | `tests/test_security_*.py` | Vérifient CSRF, cookies, headers, uploads, RBAC |
| **Tests MariaDB opt-in** | `tests/test_e2e_mariadb.py` | Nécessitent une base `forge_e2e_*` réelle |
| **Tests méta et garde-fous** | `tests/meta/test_<sujet>.py` | Vérifient docs, roadmap, packaging statique, frontières architecturales |
| **Tests documentaires** | `tests/meta/test_doc_<sujet>.py` | Vérifient qu'une page de documentation existe et contient les sections attendues |

### Tests MariaDB opt-in

Les tests E2E avec une vraie base MariaDB ne s'exécutent que si la variable
d'environnement `FORGE_E2E_MARIADB=1` est définie. La base doit avoir un
nom préfixé `forge_e2e_` pour éviter tout écrasement accidentel d'une base
de développement ou de production.

```bash
FORGE_E2E_MARIADB=1 pytest tests/test_e2e_mariadb.py
```

Ces tests ne sont pas requis dans la suite standard. Ils sont optionnels et
documentés dans la [Matrice de compatibilité](compatibility.md).

### Règles pour les tests

- Chaque test doit être autonome — pas de dépendance entre tests.
- Les fixtures `tmp_path` et `monkeypatch.chdir` isolent les tests CLI et E2E.
- `apply_model_sql` est moquée dans les tests E2E starters pour ne pas dépendre de MariaDB.
- Un test qui modifie `sys.path` ou l'état global doit nettoyer après lui.
- **Tests méta dans `tests/meta/`** — tout test qui lit principalement des fichiers de documentation, vérifie une roadmap, une version déclarée, un classifier, l'absence d'une chaîne interdite, une frontière d'import ou un invariant textuel doit vivre dans `tests/meta/`, pas à la racine de `tests/`. Chaque fichier `tests/meta/` doit porter `pytestmark = pytest.mark.meta`.

### Règle behavior-first

Un test méta vérifie une convention ou un invariant statique.
Un test comportemental exécute Forge.

Quand Forge expose une commande, une API, une génération ou un flux runtime,
le test prioritaire doit exécuter ce comportement réellement. Un test méta
peut compléter ce test, mais ne doit pas être la seule preuve du comportement.

Les tests méta restent adaptés :

- aux invariants documentaires (sections attendues dans un guide, une roadmap) ;
- aux politiques et frontières d'import (absences de symboles retirés) ;
- aux chaînes interdites ou aux vérifications de version dans les docstrings ;
- aux invariants impossibles à exécuter sans environnement externe (base de données,
  réseau, infra complète).

Quand un comportement peut être exécuté dans un test unitaire ou avec
`tmp_path`, il doit l'être. Un test comportemental fort rend son test méta
complémentaire optionnel — pas l'inverse.

**Exemples de tests déjà behavior-first dans Forge :**

- `test_forge_help_safe_flag_001.py` — vérifie via subprocess que `--help` n'exécute
  aucune logique métier ;
- `test_modules_explicit_routes_001.py` — génère réellement des routes dans un
  répertoire temporaire ;
- `test_doctor_mfa_warning_001.py` — appelle `check_mfa_dependency` avec un
  environnement contrôlé et vérifie le message retourné ;
- `test_module_routes_injection_remove_001.py` — appelle `install_module_manifest`
  et vérifie que `mvc/routes.py` n'est pas touché.

### Politique de rotation des tests méta

#### Pourquoi des tests méta ?

Les tests méta vérifient des invariants qui ne peuvent pas être couverts par des tests comportementaux : cohérence documentaire, absence d'une dépendance interdite, respect d'une frontière d'import, conformité d'un fichier de configuration statique. Ils protègent la lisibilité et la maintenabilité du projet sans exécuter de code runtime.

#### Tests méta permanents

Garder indéfiniment. Suppression possible uniquement si l'invariant disparaît de l'architecture :

- frontières d'import entre `core/` et les opt-ins (`ADR-004`, `ADR-011`) ;
- contrat de packaging (packages déclarés dans `pyproject.toml`) ;
- politique de sécurité documentée (`docs/production-security.md`, `docs/security.md`) ;
- politique de dépréciation documentée ;
- stabilité de l'API publique (`test_stability_contract_3_x_001.py`) ;
- isolation des tests méta (`test_tests_meta_isolate_001.py`) ;
- cohérence de version entre les fichiers (`test_release_current_version_001.py`).

#### Tests méta temporaires

Un test méta est temporaire s'il est créé pour empêcher la régression d'un ticket ponctuel (extraction, suppression, migration). Il doit mentionner dans son docstring le ticket ou la phase qui justifie son existence.

Exemples : suppression d'OIDC, extraction de MFA, migration de l'API FR→EN.

Critère : si le fichier a pour objet de vérifier qu'une transformation passée **n'est pas révoquée**, il est temporaire. Il peut être supprimé dans `META-TESTS-PRUNE-001` si l'invariant est couvert par un test comportemental plus fort, ou si la phase est définitivement close et la régression jugée improbable.

**Règle obligatoire** : tout fichier `tests/meta/` dont le nom contient `legacy`, `stale`, `migration` ou `deprecation` doit mentionner un ticket ou une référence de phase dans ses 20 premières lignes.

#### Tests méta release-snapshot

Ces tests vérifient une version ou un état courant. Ils sont valides mais doivent être mis à jour à chaque release :

- `test_release_current_version_001.py` — cohérence de la version dans tous les fichiers ;
- `test_pypi_classifiers_001.py` — classifiers PyPI alignés avec le statut réel.

La mise à jour est un acte délibéré, pas une anomalie.

#### Fusion ou suppression

Un test méta peut être **fusionné** si plusieurs fichiers vérifient le même invariant. Un test méta peut être **supprimé** uniquement :

1. dans un ticket dédié (`META-TESTS-PRUNE-001` ou équivalent) ;
2. avec validation que l'invariant reste couvert (par un autre test méta ou un test comportemental) ;
3. avec une entrée dans le rapport du ticket.

Jamais en passant une suppression dans un ticket non dédié aux tests.

#### Règle de sécurité

Un test méta de sécurité (frontière d'import, chaîne interdite, politique de stockage) ne doit jamais être supprimé sans validation explicite de sécurité. Le doute profite au maintien.

#### Lien avec les tests comportementaux

Un test comportemental est préférable à un test méta quand le comportement peut être exécuté directement. Si un test méta vérifie qu'une fonction existe dans le code source, et qu'un test comportemental l'appelle et vérifie son résultat, le test méta est candidat à suppression.

Un test méta reste pertinent quand : (a) l'invariant est purement textuel ou documentaire, (b) l'exécuter en runtime serait trop coûteux ou dépendant d'un environnement extérieur, (c) il protège une frontière architecturale indépendamment du comportement observable.

#### Ticket de nettoyage

`META-TESTS-PRUNE-001` est le ticket prévu pour la suppression et la fusion effectives. Il applique les critères définis ici. Ce ticket (8.2) définit la politique ; `META-TESTS-PRUNE-001` (8.3) l'applique.

---

## Sources documentaires et artefacts générés

Forge distingue **trois couches** dans sa documentation. Ne pas les
confondre — chacune a un rôle strict.

| Chemin | Rôle | Suivi Git ? | Modifier à la main ? |
|---|---|---|---|
| `docs/` | **Source documentaire canonique** (Markdown + assets) | ✅ Oui | ✅ Oui — c'est la source à éditer |
| `mvc/views/landing/index.html` | **Source canonique de la landing publique** | ✅ Oui | ✅ Oui — éditer ici puis synchroniser |
| `docs/index.html` | **Landing synchronisée** depuis `mvc/views/landing/index.html` | ✅ Oui | ❌ Non — régénéré par `forge sync:landing` |
| `site/` | **Artefact MkDocs** généré par `mkdocs build` | ❌ Non (ignoré par `.gitignore`) | ❌ Jamais — supprimable sans perte |

La chaîne complète à suivre quand on modifie la landing :

```bash
# 1. Éditer la source canonique
$EDITOR mvc/views/landing/index.html

# 2. Synchroniser docs/index.html depuis la source canonique
forge sync:landing

# 3. Régénérer le site MkDocs (zéro warning autorisé)
mkdocs build --strict

# 4. Vérifier l'état Git
git diff --check
```

`site/` est **supprimable sans perte** : c'est uniquement la sortie de
`mkdocs build`, jamais une référence. Si `site/` est suivi par Git par
erreur (commit accidentel), il faut le retirer de l'index — pas l'inverse.

Le contrat est verrouillé par
[`tests/meta/test_docs_site_artifact_policy_001.py`](https://github.com/caucrogeGit/Forge/blob/main/tests/meta/test_docs_site_artifact_policy_001.py).

---

## Mettre à jour la documentation

Une fonctionnalité non documentée est incomplète.

### Quand modifier `docs/reference.md`

Toute nouvelle commande CLI, tout nouveau paramètre ou tout changement de comportement
observable doit être reflété dans [Référence API et CLI](reference.md).

### Quand modifier un guide spécifique

Si la fonctionnalité est couverte par un guide existant, mettez-le à jour :

- [Architecture des entités](entity_architecture.md) — nouveaux champs ou générateurs
- [Relations entre entités](relations.md) — nouvelle syntaxe relationnelle
- [Auth/User](auth.md) — nouvelles briques d'authentification
- [Sécurité et RBAC](security.md) — nouveaux mécanismes de sécurité
- [Module média](media.md) — nouveaux comportements uploads

### Quand modifier la roadmap

Mettez à jour `docs/roadmap/forge-roadmap.md` :

- Marquez le ticket comme **livré** dans le tableau de la phase concernée.
- Mettez à jour le résumé "Phases terminées" dans la section de clôture.
- Indiquez la **prochaine priorité immédiate** dans le bloc `text`.

Mettez à jour `CHANGELOG.md` avec une entrée décrivant précisément ce qui a été fait.

### Quand modifier `mkdocs.yml`

Toute nouvelle page documentaire doit être ajoutée à la navigation dans `mkdocs.yml`.
Choisissez la section la plus logique selon le contenu.

### Quand modifier le contrat de stabilité

Si une nouvelle commande ou un nouveau fichier est garanti préservé (jamais écrasé
par Forge), ajoutez-le dans [Contrat de stabilité](stability-contract.md).

---

## Lancer les validations

### Validations obligatoires

Ces validations doivent toutes passer avant toute livraison :

```bash
pytest
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
```

| Commande | Ce qu'elle vérifie |
|---|---|
| `pytest` | Suite complète de tests (runtime, générateurs, doc, CLI, sécurité) |
| `python -m compileall -q .` | Absence d'erreurs de syntaxe Python |
| `ruff check .` | Lint et style — aucun avertissement toléré |
| `mkdocs build --strict` | Build doc sans erreur ni lien brisé |
| `git diff --check` | Absence d'espaces de fin de ligne ou de marqueurs de conflit |

### Validation optionnelle MariaDB

```bash
FORGE_E2E_MARIADB=1 pytest tests/test_e2e_mariadb.py
```

Uniquement si une instance MariaDB réelle est configurée avec une base
dont le nom commence par `forge_e2e_`. Non requis dans la suite standard.

---

## Qualité du résumé final

Chaque livraison de ticket doit inclure un résumé final structuré. Ce résumé
va dans `CHANGELOG.md`.

### Format attendu

```text
Résumé final — <TICKET-ID>

Branche        : main
Commit         : <hash>
Fichiers créés : docs/<fichier>.md, tests/meta/test_doc_<fichier>.py
Fichiers modifiés : mkdocs.yml, docs/roadmap/forge-roadmap.md, ...

Comportement ajouté :
  - Ce que la fonctionnalité fait concrètement
  - Ce qui change dans les générateurs ou le runtime

Tests ajoutés :
  - N tests dans tests/test_<sujet>.py
  - Couverture : classes TestXxx documentées

Limites restantes :
  - Ce que ce ticket ne couvre pas
  - Tickets futurs associés

Résultats :
  pytest       : N passed
  compileall   : OK
  ruff         : All checks passed
  mkdocs       : OK
  git diff     : OK

Prochaine priorité : <PROCHAIN-TICKET-ID>
```

---

## Roadmap et priorités

La feuille de route active est dans [Roadmap active](roadmap/forge-roadmap.md).

La priorité courante est toujours indiquée dans le bloc :

```text
Prochaine priorité immédiate :

```text
NOM-DU-TICKET
```
```

Ne sautez pas de ticket. Si un ticket bloque, documentez pourquoi et proposez
un ordre alternatif dans la roadmap.

Les phases sont regroupées par objectif :

| Phase | Contenu |
|---|---|
| Phase 4.5 | Auth/User avancée et sécurité moderne |
| Phase 5 | Relations avancées et CRUD enrichi |
| Phase 6 | Pages publiques génériques (terminée) |
| Phase 9 | Documentation avancée (terminée à ce ticket) |
| Post-roadmap | API JSON légère, audit 2.0, DX, performance |

---

## Ce qu'il ne faut pas faire

- **Mélanger plusieurs fonctionnalités** dans un seul ticket ou commit
- **Corriger en silence une dette hors périmètre** — ouvrez un ticket séparé
- **Casser `main`** — les tests doivent passer en permanence
- **Supprimer des fichiers utilisateur** sans vérification de modification
- **Ajouter une dépendance lourde** au runtime sans discussion et ticket dédié
- **Créer une abstraction magique** — le comportement doit rester traçable
- **Promettre une compatibilité non testée** — ne documentez que ce qui est vérifié
- **Modifier une politique de release** sans ticket dédié (`RELEASE-POLICY-*`)
- **Publier une release** sans suivre la [Procédure de release](release.md)
- **Modifier la version Forge** hors d'un ticket release
- **Créer un tag** manuellement sans validation locale préalable

---

## Checklist contributeur

```text
Checklist avant livraison

- [ ] Le ticket a une seule responsabilité clairement définie
- [ ] L'existant a été audité avant de coder
- [ ] Les fichiers modifiés sont limités au périmètre du ticket
- [ ] Les tests sont ajoutés ou mis à jour
- [ ] La documentation est mise à jour (reference.md, guide spécifique si besoin)
- [ ] mkdocs.yml est mis à jour si une nouvelle page est créée
- [ ] La roadmap est mise à jour (ticket marqué livré + prochaine priorité)
- [ ] Les limites restantes sont explicitées dans le résumé
- [ ] pytest passe (tous les tests)
- [ ] python -m compileall -q . passe
- [ ] ruff check . passe (zéro avertissement)
- [ ] mkdocs build --strict passe (zéro lien brisé)
- [ ] git diff --check passe
- [ ] Le résumé final est complet et versé dans la roadmap consolidation
```

---

## Exemple de contribution correcte

Voici le déroulé typique d'une contribution à Forge.

**Ticket** : `DOC-MODULE-AUTHOR-001` — guide de création d'un module Forge

**1. Auditer l'existant**

```bash
# Lire le code du système de modules
cat core/modules/manifest.py
cat core/modules/registry.py
cat core/modules/files.py
cat core/modules/routes.py
cat core/modules/remove.py
# Lire les tests E2E existants
cat tests/test_e2e_module.py
# Lire la référence
grep -n "module" docs/reference.md | head -20
```

**2. Créer la documentation**

```bash
# Créer docs/module-author-guide.md
# Ajouter dans mkdocs.yml (Modules et starters)
```

**3. Créer les tests documentaires**

```bash
# Créer tests/meta/test_doc_module_author.py
# Tester que les sections existent, les commandes sont mentionnées, etc.
```

**4. Mettre à jour la roadmap**

```bash
# Dans docs/roadmap/forge-roadmap.md : marquer DOC-MODULE-AUTHOR-001 livré
# Dans CHANGELOG.md : ajouter l'entrée complète du ticket
```

**5. Valider**

```bash
pytest tests/meta/test_doc_module_author.py --tb=short -q
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
```

**6. Committer**

```bash
git add docs/module-author-guide.md tests/meta/test_doc_module_author.py \
    mkdocs.yml docs/roadmap/forge-roadmap.md \
    CHANGELOG.md
git commit -m "feat: ajouter le guide de création de modules Forge"
```

---

## Limites actuelles

| Limite | État |
|---|---|
| Pas de CI automatique publique | Les validations sont manuelles en local |
| Tests MariaDB non automatisés en CI | `FORGE_E2E_MARIADB=1` requis, base séparée nécessaire |
| Pas de contribution externe formalisée | Forge est maintenu par Roger Lequette — toute contribution suit la cession de droits documentée dans `CONTRIBUTING.md` |
| Pas de bot de review automatique | La review est humaine |
| Pas de guide de contribution graphique | Forge Design est un projet séparé |

---

## Voir aussi

- [Politique de release](release-policy.md) — SemVer adapté, règles de publication
- [Politique de dépréciation](deprecation-policy.md) — cycle d'annonce et de retrait
- [Matrice de compatibilité](compatibility.md) — Python, MariaDB, dépendances
- [Guide de migration](migration-guide.md) — comment migrer entre versions
- [Contrat de stabilité](stability-contract.md) — fichiers garantis préservés
- [Procédure de release](release.md) — étapes de publication d'une version
- [Validation locale](release-local.md) — checklist de validation avant release
- [Référence API et CLI](reference.md) — toutes les commandes Forge
