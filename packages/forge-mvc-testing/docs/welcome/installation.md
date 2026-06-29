# Installation de forge-mvc-testing

Objectif : installer l'outillage de test et vérifier que le plugin pytest s'active.

Le parcours qui suit montre, en trois niveaux, comment écrire un premier test avec `FakeRequest`, utiliser les fixtures et l'isolation, puis tester vos propres opt-ins.

## Installer le paquet (en développement)

```bash
pip install --pre forge-mvc-testing
```

Déclarez-le comme dépendance de **développement** (par exemple dans `requirements-dev`), jamais dans les dépendances du projet.

## Vérifier l'activation du plugin

```bash
pytest -p no:cacheprovider --fixtures | grep fake_request
```

Si `fake_request` apparaît, le plugin pytest est bien actif (point d'entrée `pytest11`).

## Vérifier FakeRequest

```python
from forge_mvc_testing import FakeRequest

req = FakeRequest("GET", "/clients?id=7")
print(req.query("id"))     # "7"
```

!!! note "Dev-only"
    Ce paquet n'est jamais importé par l'application en production (ADR-041).

## Après cette étape

[Niveau débutant : Premier test](debutant/testing-welcome.md)
