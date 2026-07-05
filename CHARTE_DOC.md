# Charte philosophique de Forge

> **Document canonique.** Cette charte est la source unique de référence
> pour les principes philosophiques de Forge. Toute documentation qui
> mentionne la charte pointe vers ce fichier. La copie navigable dans
> `docs/charter.md` est un alias léger qui renvoie ici.
>
> Adoption formelle : voir [ADR-007](docs/adr/007-charter-v2-adoption.md).

**Version 2 — adoptée en mai 2026 (Forge 2.4 / phase 14)**

> Cette charte définit l'âme et les contraintes de Forge.
> Elle est le cadre de référence pour toute évolution du framework :
> chaque ticket, chaque PR, chaque décision d'architecture doit pouvoir
> s'y rattacher.

---

## Phrase directrice

Forge est un framework web Python explicite, pédagogique, testable et durable.

Son noyau reste minimal et son écosystème grandit par modules, sans jamais
mélanger framework générique et application métier, ni masquer ce qui se passe
au développeur.

Forge peut devenir riche par ses briques, mais il doit rester petit dans son
cœur, clair dans ses générateurs, fortement documenté et très testé.

---

## 1. Principes non négociables

### 1. Séparer framework et application métier

Forge fournit une structure, des primitives et des générateurs pour construire
des applications. Il ne doit pas devenir lui-même une application métier.

Les starters, démonstrateurs et exemples servent à valider Forge, pas à
orienter tout le cœur du framework vers un cas d'usage particulier.

### 2. Avancer par petits tickets

Un ticket = une responsabilité. Chaque ticket doit être testable, documenté
et borné.

Un ticket correct doit indiquer :

- ce qu'il fait ;
- ce qu'il ne fait pas ;
- les fichiers concernés ;
- les validations attendues ;
- les limites restantes.

### 3. Refuser la magie cachée

Le développeur doit pouvoir comprendre ce que Forge fait.

- Les conventions doivent être visibles.
- Les fichiers générés doivent être lisibles.
- Les comportements implicites doivent être limités, documentés et justifiés.

Forge ne doit pas impressionner par de la magie. Il doit convaincre par sa
clarté.

### 4. Préserver le code utilisateur

Forge peut générer du code, proposer du code, afficher des instructions, lire
de la configuration.

Mais Forge ne doit pas écraser silencieusement un fichier que l'utilisateur
considère comme sien.

La règle de génération est : `write-if-new`, jamais d'écrasement invisible.

Tout fichier manuel doit rester sous le contrôle du développeur.

### 5. Garder SQL visible

Forge peut générer du SQL, mais ne doit pas cacher la base de données derrière
un ORM opaque.

Le SQL doit rester :

- lisible ;
- auditable ;
- exécutable ;
- compréhensible par le développeur.

Tant qu'un ORM n'est pas une décision assumée, testée et documentée, Forge
garde une approche SQL explicite.

### 6. Tester avant d'élargir

Aucune brique ne doit devenir plus ambitieuse avant d'être couverte par des
tests suffisants.

Les tests doivent vérifier le comportement réel du framework, pas seulement
l'existence de documents ou de mentions dans la roadmap.

### 7. Sécuriser par défaut

Forge doit fournir des garde-fous simples, lisibles et vérifiables pour :

- CSRF ;
- sessions ;
- uploads ;
- chemins fichiers ;
- headers de sécurité (CSP, HSTS, X-Frame-Options, etc.) ;
- mots de passe ;
- mail en développement ;
- routes sensibles.

La sécurité ne doit pas être une couche décorative ajoutée après coup.

### 8. Noyau minimal, briques opt-in

Le noyau de Forge doit rester minimal. Toute fonctionnalité spécialisée,
avancée ou dépendante d'un cas d'usage vit en module, pas dans `core/`.

Le `core/` conserve uniquement les primitives générales nécessaires au
fonctionnement d'un framework web.

Le test pour décider est : *"Si je retire cette brique du `core/`, est-ce
qu'une app Forge basique peut encore tourner ?"*. Si oui → module. Si non →
core.

Sortir une fonctionnalité du noyau vers un module n'est pas une régression :
c'est un allègement.

### 9. Pas d'écriture invisible dans le code utilisateur

Forge suit trois modes d'action acceptables :

- Forge **génère** un fichier (avec write-if-new).
- Forge **affiche** sur stdout du code à copier.
- Forge **lit** un fichier de configuration.

Forge ne réécrit jamais silencieusement un fichier applicatif manuel.

Toute modification proposée à un fichier utilisateur doit être explicite,
visible et validable.

Exemple correct :

```text
Voici les routes à copier dans mvc/routes.py
```

Exemple à éviter :

```text
Forge modifie automatiquement mvc/routes.py sans intervention claire.
```

### 10. Une API publique est un contrat de complétude

Une API publique doit correspondre à un comportement réellement utilisable.

Pas d'export public d'API à moitié faite. Le code expérimental, partiel ou
incomplet doit rester :

- privé ;
- interne ;
- ou explicitement marqué comme expérimental (sous-package `experimental/`,
  documentation des limites, refus d'export depuis le `__init__.py` public).

Un développeur ne doit jamais croire qu'une fonctionnalité est complète parce
qu'elle est exposée publiquement.

### 11. Une seule façon officielle de faire chaque chose

Pour chaque besoin, Forge doit proposer une API officielle claire.

Les anciennes API peuvent exister temporairement pour compatibilité, mais
elles doivent être :

- marquées comme legacy ;
- datées (avec leur version de retrait planifiée) ;
- documentées ;
- absentes du code livré comme exemple principal.

Le legacy ne doit pas devenir une deuxième manière permanente de faire la
même chose.

---

## 2. Périmètre du noyau

Le noyau de Forge contient uniquement les primitives générales du framework :

- HTTP : `Request`, `Response`
- routing : `Router`, groupes de routes, middlewares
- application et dispatcher
- configuration (`core/forge.py`)
- templating (Jinja, helpers, contexte global)
- base de données : couche `core.database.db` (`fetch_one`, `fetch_all`,
  `execute`, `insert`)
- sessions et store contractuel
- forms et validation
- uploads (taille, type MIME, chemin sécurisé)
- mail (transports, templates)
- authentification mot de passe basique (Argon2id, login/logout, sessions
  authentifiées)
- sécurité minimale : CSRF, CSP, headers, hashing
- système de modules (chargement, registry, manifest)
- outils de génération non destructifs

Tout ce qui ajoute une logique avancée, optionnelle, spécialisée ou proche
d'un cas métier doit être placé en module ou en starter.

Exemples de briques qui relèvent d'un module :

- MFA avancé (TOTP, recovery codes)
- OIDC complet
- RBAC fin (rôles, permissions, helpers Jinja, décorateurs admin)
- Workflow applicatif (statuts, transitions)
- Statistiques orientées événements
- Audit log avancé (au-delà du logging Python)
- Paiement, réservation, marketplace, SaaS multi-tenant
- Forge Design
- Toute fonctionnalité propre à un démonstrateur (Communes & Séjours,
  Carnet de contacts, etc.)

---

## 3. Règles d'évolution

### A. On ne change pas l'âme

Forge doit rester explicite, pédagogique, testable et durable.

Une évolution est acceptable si elle rend Forge plus clair, plus fiable ou
plus modulaire.

Une évolution est suspecte si elle rend Forge plus magique, plus lourd ou
plus difficile à expliquer.

Sortir une fonctionnalité du `core/` vers un module est un **allègement**,
pas une régression.

### B. Une dérive se traite en retirant la cause

Si une fonctionnalité a grossi au mauvais endroit, il ne faut pas ajouter une
couche pour masquer le problème.

Il faut identifier la cause de la dérive, puis :

- réduire ;
- déplacer ;
- clarifier ;
- documenter ;
- ou supprimer.

Pas de sucre par-dessus une dérive existante.

### C. Toute rupture d'API publique passe par une release majeure

Une rupture d'API publique doit être assumée. Elle nécessite :

- une release majeure ;
- des aliases dépréciés quand c'est possible ;
- un guide de migration ;
- une période de transition claire avec date de retrait des aliases.

### D. Les tests testent le code, pas la documentation

La suite `pytest` standard doit tester le comportement du framework.

Les contrôles de documentation, roadmap, release, changelog et cohérence
projet peuvent exister, mais ils doivent vivre dans :

- `tools/` ;
- une commande dédiée ;
- un hook pre-commit ;
- ou une suite CI séparée (`tests/meta/` ou `tests/release/`).

Ils ne doivent pas encombrer indéfiniment les tests fonctionnels du
framework.

---

## 4. Règles de génération

Forge peut générer :

- des entités et leur SQL ;
- des modèles base régénérables (`*_base.py`) ;
- des contrôleurs et des modèles ;
- des vues ;
- des routes à copier (affichées sur stdout) ;
- des fichiers de configuration initiaux ;
- des starters complets.

Forge respecte trois règles strictes :

### 4.1 Les fichiers régénérables sont identifiés

Un fichier régénérable doit être clairement reconnaissable, par convention
de nom (par exemple suffixe `_base.py`).

### 4.2 Les fichiers manuels sont préservés

Un fichier manuel ne doit pas être écrasé. Si Forge doit proposer une
modification, il doit l'afficher (stdout) ou créer un fichier nouveau, jamais
modifier le fichier de l'utilisateur.

### 4.3 Les routes applicatives restent sous contrôle humain

Forge peut afficher les routes à ajouter. Forge peut générer un fichier de
routes séparé. Forge peut documenter l'intégration.

Mais le fichier principal de routes applicatives (`mvc/routes.py`) reste
sous le contrôle explicite du développeur. Pas de marqueurs commentaires
auto-injectés, pas de réécriture automatique.

---

## 5. Règles de sécurité

Forge sécurise par défaut sans cacher les mécanismes.

### 5.1 Sessions

Les sessions passent par un contrat public de store (`SessionStore`).
Aucun helper ne doit dépendre d'attributs privés d'un store particulier.

Les implémentations (`MemorySessionStore`, `FileSessionStore`,
`MariaDbSessionStore`) doivent toutes respecter le même contrat public et
être effectivement supportées en production.

### 5.2 CSRF

Les comparaisons de jetons sensibles utilisent `hmac.compare_digest()`
(constant-time).

Le middleware CSRF est la référence ; les contrôleurs ne doivent pas dupliquer
inutilement la logique de sécurité.

### 5.3 MFA et secrets

Un secret TOTP n'est pas un hash. S'il doit être stocké, son nom doit refléter
sa nature réelle (`totp_secret`, pas `secret_hash`).

Toute limitation de sécurité doit être explicitement documentée et un
avertissement runtime émis si la sécurité fournie est partielle (par exemple
secret en clair sans chiffrement applicatif).

Le rate-limit et l'anti-replay sont des défenses obligatoires sur les
vérifications MFA.

### 5.4 OIDC

Un socle OIDC partiel ne doit pas être présenté comme une authentification
OIDC complète.

Une API OIDC publique doit être complète (token exchange, validation JWT,
JWKS, validation des claims, liaison utilisateur) ou ne pas être publique.

### 5.5 Uploads et chemins

Aucun chemin absolu ne doit être stocké pour les médias applicatifs.

Les chemins doivent être relatifs à la racine contrôlée. Les protections
contre le path traversal (rejet `..`, schémas URI, validation `commonpath`
après `resolve()`) sont obligatoires.

### 5.6 Mail en développement

Aucun vrai mail ne doit partir involontairement en environnement de
développement. Les transports fake, console ou log doivent être privilégiés
par défaut.

### 5.7 Audit

Les événements d'audit doivent être résilients (pas de propagation
d'exception qui casse une vérification de sécurité) **et** observables (les
échecs sont loggés et comptés, pas avalés silencieusement).

---

## 6. Règles de documentation

Une fonctionnalité non documentée est incomplète.

Mais la documentation ne doit pas devenir un substitut à la simplicité du
code.

La documentation doit expliquer :

- l'objectif ;
- l'usage ;
- les limites ;
- les risques ;
- les choix assumés ;
- les comportements non fournis.

Les roadmaps doivent rester consolidées : une seule roadmap active fait
autorité. Les anciennes roadmaps peuvent être archivées dans `docs/history/`,
mais ne doivent pas créer de divergence.

---

## 7. Règles Git et release

`main` doit rester stable.

Une release doit être construite depuis un état propre, testé et documenté.

### Trois environnements d'usage et de validation

Forge est conçu pour fonctionner dans trois contextes distincts. Chaque
contexte a ses propres prérequis et son propre contrat. Ne pas les confondre.

#### A. Runtime core-only

L'utilisateur utilise Forge pour démarrer ou gérer un projet, sans installer
de modules opt-in.

**Installation** :
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

**Doit fonctionner** : `forge --version`, `forge --help`, `forge new`,
`forge routes:list`, `forge project:check`, `forge doctor`.

**Ne fonctionne pas** (attendu) : `pytest`, `mkdocs`, toute commande dépendant
d'un module opt-in.

#### B. Test core-only

Le contributeur valide Forge sans installer les modules opt-in. Les tests
opt-in sont automatiquement sautés (`SKIPPED` via `pytest.importorskip`).
La suite se termine sans erreur.

Le contrat de la charte — les 5 commandes de validation — se réfère à ce contexte.

**Installation** :
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pip install pytest ruff build
python -m pip install -r requirements-docs.txt
```

**Doit fonctionner** :
```bash
pytest                  # 0 erreur, skips propres pour les tests opt-in
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
```

#### C. Test complet

Le contributeur valide Forge avec tous les modules opt-in.

**Installation** :
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` inclut les modules opt-in en éditable depuis le
monorepo (`forge-mvc-mfa`, `forge-mvc-rbac`, `forge-mvc-workflow`,
`forge-mvc-stats`) et toutes les dépendances de test.

**Doit fonctionner** : les 5 commandes de validation, sans skips `forge_mvc_*`.
Tous les tests opt-in s'exécutent. Tout ce qui marche en B marche en C.

### Avant chaque release

Les validations minimales attendues sont les 5 commandes listées dans
l'environnement B, exécutées en **environnement C (Test complet)**.

La promesse complémentaire est qu'elles passent **également** en environnement B
(Test core-only), prouvée par la suite méta (voir
`tests/meta/test_pytest_core_only_contract_001.py`).

### Ordre canonique des imports dans un fichier de tests opt-in

```python
"""Docstring du fichier."""
from __future__ import annotations

# 1. Stdlib
from datetime import datetime

# 2. pytest (toujours avant les importorskip)
import pytest

# 3. importorskip pour modules opt-in et leurs dépendances
pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("pyotp")

# 4. Autres imports (core, opt-in, deps)
import pyotp
from forge_mvc_mfa import ...
```

Toute dépendance d'extra (ex : `pyotp` pour MFA) doit avoir son propre
`pytest.importorskip`, distinct de celui du module Forge opt-in.
Le test méta `tests/meta/test_pytest_core_only_contract_001.py` garantit
ce contrat et oblige à classifier explicitement chaque dépendance de test.

### Tags et release

Un tag de release est une version figée. Un tag publié ne doit pas être
déplacé sauf cas exceptionnel et explicitement justifié.

Une release doit vérifier :

- la version dans le code ;
- la version dans `pyproject.toml` (racine et chaque paquet du monorepo) ;
- la version dans la documentation (via `{{forge_version}}`) ;
- le changelog daté ;
- la construction des wheels (toutes les distributions) ;
- l'installation locale ;
- le résultat de `forge --version`.

---

## 8. Questions de contrôle avant chaque décision

Avant d'ajouter, modifier ou déplacer une brique, poser ces questions :

1. Est-ce une primitive générale du framework ou une logique métier ?
2. Cette brique appartient-elle vraiment au `core/` ?
3. Peut-elle devenir un module opt-in ?
4. Le comportement est-il explicite pour le développeur ?
5. Le code utilisateur est-il préservé ?
6. Le SQL, les fichiers et les chemins restent-ils lisibles ?
7. L'API exposée est-elle complète ?
8. Existe-t-il déjà une autre API qui fait la même chose ?
9. La sécurité minimale est-elle couverte (CSRF, sessions, uploads,
   audit) ?
10. Les tests vérifient-ils le comportement réel ?
11. La documentation explique-t-elle aussi les limites ?
12. Cette évolution rend-elle Forge plus clair ou seulement plus gros ?

---

## 9. Formule de décision finale

> Si une proposition rend Forge plus explicite, plus testable, plus
> générique, plus maîtrisable et ne grossit pas le `core/` par réflexe,
> elle va dans le bon sens.
>
> Si elle ajoute de la magie, mélange métier et framework, expose une API
> incomplète, écrit dans le code utilisateur ou empile du sucre par-dessus
> une dérive existante, elle est refusée, réduite ou repoussée.

Forge doit rester une forge : un outil qui aide à fabriquer des
applications, pas une machine qui confisque le travail du développeur.

---

## Historique

- **v2** (mai 2026, phase 14.1-14.2) — révision majeure pour préparer
  Forge 3.0. Ajout des principes 8 (noyau minimal, briques opt-in),
  9 (pas d'écriture invisible), 10 (API publique = contrat de complétude),
  11 (une seule façon de faire). Ajout des règles d'évolution A-D et de la
  formule de décision finale.

- **v1** (2025) — première charte, règles documentaires. Archivée dans
  `docs/history/charte-v1.md`.
