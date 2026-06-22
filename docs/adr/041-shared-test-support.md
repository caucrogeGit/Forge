# ADR-041 : Infrastructure de test partagée pour les paquets opt-in

## Statut

Proposé, Forge 1.0.0-beta.x (ticket `OPTIN-TEST-SUPPORT-001`).

Débloque l'ADR-040 (surface de test par paquet) : quatre paquets ont pu migrer
leurs tests unitaires (`stats`, `workflow`, `audio`, `mail`), mais les huit
autres en sont empêchés par une dépendance à l'infrastructure de test partagée
du `tests/` racine.

---

## Date

2026-06-21

---

## Contexte

Migrer les tests unitaires d'un opt-in vers `packages/<paquet>/tests/`
(ADR-040) suppose qu'ils soient **autonomes**. Or `tests/conftest.py` fournit
une infrastructure partagée dont dépendent **61 fichiers** de test, opt-ins
inclus :

- des fixtures **autouse** qui configurent le noyau Forge pour chaque test :
  `configure_forge_kernel` (vues + SQL en `tmp_path`, `UPLOAD_ROOT` isolé),
  `clear_sessions`, `clear_rate_limits`, `clear_upload_rate_limits` ;
- la fixture `fake_request` et la classe `FakeRequest` (`tests/fake_request.py`)
  pour simuler une requête de contrôleur.

Déplacés tels quels dans un paquet, ces tests perdent l'accès à ces fixtures
(`conftest.py` racine ne s'applique qu'au sous-arbre `tests/`) et échouent en
masse (« fixture not found »). Tentative mesurée : 100 échecs. Le filtre
« n'importe pas `cli`/`mvc` » est donc insuffisant : le vrai couplage est
l'infrastructure de test, pas le code applicatif.

Incident à noter : `tests/conftest.py` mentionne `forge_mvc_workflow` et a été
faussement déplacé par un filtre trop large, ce qui casse toute la racine.
Tout futur déplacement doit exclure `conftest.py` et tracer l'usage de fixtures.

---

## Décision (proposée)

Extraire l'infrastructure de test partagée dans un **paquet de test-support
dédié, réservé au développement** : `packages/forge-mvc-testing/`
(module `forge_mvc_testing`).

Il fournit :

1. `FakeRequest` (importable : `from forge_mvc_testing import FakeRequest`) ;
2. un **plugin pytest** (point d'entrée `pytest11`) exposant les fixtures
   partagées (`configure_forge_kernel` autouse, `clear_*`, `fake_request`).
   Quand le paquet est installé dans l'environnement de test, ses fixtures sont
   disponibles **partout**, racine comme paquets, sans `conftest.py` dupliqué.

Conséquences de câblage :

- `forge-mvc-testing` est une **dépendance de développement uniquement**
  (déclarée dans `requirements-dev.txt` et dans l'extra `[test]` de chaque
  opt-in). Il n'est **jamais** une dépendance runtime, **jamais** installé par
  les utilisateurs : leurs suites de tests ne sont pas polluées par les fixtures
  autouse de Forge.
- `tests/conftest.py` racine se réduit à presque rien (le plugin fournit tout) ;
  `tests/fake_request.py` est supprimé au profit de `forge_mvc_testing`.
- Une fois en place, les huit paquets restants (`mfa`, `rbac`, `files`,
  `images`, `iot`, `video`, `pivot`, `i18n`) migrent leurs tests unitaires
  propres, qui ne dépendent plus que de `forge_mvc_<paquet>` + `core` +
  `forge_mvc_testing` (présent en dev).

---

## Alternatives écartées

- **Plugin pytest porté par le `core`** (`core.testing` + `pytest11`) : rejeté.
  Le core est une dépendance runtime de tous les opt-ins ; un plugin autouse
  dans le core s'activerait dans la suite de tests **de l'utilisateur**, et
  `configure_forge_kernel` reconfigurerait son noyau. Trop intrusif (contraire
  au principe 8 : pas d'effet caché côté utilisateur).
- **Réplication du `conftest.py` dans chaque paquet** : rejeté. ~90 lignes de
  fixtures dupliquées sur huit paquets, avec dérive garantie (contraire au
  principe 11 : une seule façon officielle).
- **Laisser ces tests à la racine** : possible, mais les huit paquets restent
  alors non autovérifiables, ce que l'ADR-040 visait à corriger.

---

## Plan d'exécution séquencé

1. Créer `packages/forge-mvc-testing/` : `FakeRequest` + plugin pytest
   (fixtures déplacées depuis `tests/conftest.py`). Pas publié sur PyPI (ou en
   dev-only), `pyproject.toml` minimal.
2. Brancher : `requirements-dev.txt` + extra `[test]` des opt-ins ; réduire
   `tests/conftest.py` à un repli ; supprimer `tests/fake_request.py`.
3. Vérifier la racine inchangée (suite complète verte) — le plugin remplace le
   conftest sans régression.
4. Migrer les huit paquets, un par un, en ne déplaçant que les tests
   **réellement propres** (exclure `conftest.py`, vérifier l'absence de
   `from tests[.]` et de fixtures hors `forge_mvc_testing`), run racine **et**
   autonome verts à chaque paquet.

---

## Conséquences

**Positives :**

- Les douze opt-ins peuvent porter leurs tests unitaires, autovérifiables et
  exécutables en autonome.
- Une seule source pour `FakeRequest` et les fixtures (principe 11).
- Les suites de test des utilisateurs ne sont pas affectées (test-support
  dev-only).

**Négatives / coûts :**

- Un paquet de plus à maintenir (mais de test, simple, non publié).
- Migration en deux temps (infra d'abord, puis les huit paquets).

---

## Charte appliquée

- Principe 11 — une seule façon officielle (infra de test unique).
- Principe 8 — noyau minimal (l'infra de test ne va **pas** dans le core).
- Principe 6 — tester avant d'élargir (racine validée avant de migrer les huit).

---

## ADR liés

- **Débloque l'ADR-040** (surface de test par paquet).
- **Cohérent avec l'ADR-005** (packaging hybride monorepo + multi-distributions).
