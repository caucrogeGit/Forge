# ADR-040 : Surface de test par paquet opt-in (modèle hybride)

## Statut

Accepté, Forge 1.0.0-beta.x (ticket `OPTIN-SMOKE-TESTS-001`).

Prolonge l'ADR-038 (doc embarquée par paquet) côté tests : après que la
documentation a rejoint chaque paquet, un socle de test minimal le rejoint
aussi, pour qu'un paquet publié sur PyPI soit autovérifiable.

---

## Date

2026-06-21

---

## Contexte

Avant cette décision, **aucun** paquet opt-in (`packages/forge-mvc-*`) ne porte
de test propre : toute la suite vit dans le `tests/` racine (`pytest.ini` :
`testpaths = tests`), y compris les tests du code des opt-ins. Conséquence pour
un framework distribué en douze paquets PyPI : un paquet publié n'embarque aucun
moyen de prouver qu'il fonctionne (`cd packages/forge-mvc-iot && pytest` ne
trouve rien).

Déplacer en bloc toute la suite vers les paquets serait coûteux et contraire à
la réalité : beaucoup de tests sont **transversaux** (méta, documentation,
intégration cœur + opt-ins, anti-dérive) et n'appartiennent à aucun paquet.

---

## Décision

Modèle **hybride** :

1. **Racine `tests/`** : conserve tout le transversal, méta, documentation,
   intégration cœur + opt-ins, anti-dérive, sweeps. Source de vérité du
   monorepo.
2. **`packages/<paquet>/tests/`** : chaque opt-in porte son propre socle de
   test, en commençant par un **test de fumée** (« smoke ») :
   - le paquet installé s'**importe** ;
   - son **API publique** (`__all__`) se résout entièrement ;
   - `__version__` est présent ;
   - `py.typed` est embarqué (PEP 561).
3. Les vrais tests unitaires **propres à un module** (ne dépendant que du paquet
   + cœur) pourront migrer vers leur paquet au fil de l'eau, sans date butoir.
4. Les tests de **documentation** restent à la racine : ils valident le site
   agrégé (concern monorepo, ADR-038), pas le paquet isolé.

Exécution (décision de câblage) :

- `pytest.ini` : `testpaths = tests packages`. Un seul `pytest` à la racine
  exécute **aussi** les smoke tests des paquets ; rien n'est orphelin.
- Chaque paquet reste testable **en autonome** : `cd packages/<paquet> && pytest`.
- Les smoke tests utilisent `pytest.importorskip(<module>)` : ils se **skippent
  proprement** si le paquet n'est pas installé (convention déjà en place dans
  `requirements-dev.txt`), sans casser le run partiel d'un contributeur.
- Nommage `test_smoke_<module>_001.py` pour éviter toute collision de nom de
  fichier entre paquets lors de la collecte racine.
- Marqueur `smoke` enregistré dans `pytest.ini`.

---

## Conséquences

**Positives :**

- Chaque paquet publié est **autovérifiable** (import + API + typage).
- La régression d'API publique d'un paquet (un nom de `__all__` cassé, un
  `py.typed` oublié) est détectée par son propre test.
- Câblage minimal : pas de CI par paquet imposée, le run racine couvre tout.

**Négatives / coûts :**

- La collecte racine scanne `packages/` (collection un peu plus longue).
- Un paquet non installé localement voit son smoke **skippé** : la couverture
  réelle dépend de l'environnement (CI canonique = les douze installés).
- Convention de nommage et marqueur à respecter pour les futurs paquets.

---

## Charte appliquée

- Principe 8, noyau minimal, briques opt-in (le paquet devient un citoyen
  testable de première classe).
- Principe 6, tester avant d'élargir (smoke d'abord, unitaire ensuite).
- Principe 11, une seule façon officielle (transversal à la racine, propre au
  paquet dans le paquet).

---

## ADR liés

- **Prolonge l'ADR-038** (doc embarquée par paquet) côté tests.
- **Précise l'ADR-005** (packaging hybride) : le test suit la frontière de
  distribution.
