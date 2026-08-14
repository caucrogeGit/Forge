# Premier test

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-testing` avant de commencer : voir sa [référence](../../reference.md).

    ```bash
    pip install --pre forge-mvc-testing    # installe le paquet
    forge opt-in:enable testing          # le branche au projet
    ```

    Sans le paquet, l'application refuse de démarrer sur un `ModuleNotFoundError` au chargement des routes.

    `forge opt-in:install testing` **affiche** la commande d'installation adaptée à votre environnement, pipx compris ; il n'installe rien lui-même (ADR-016).

Objectif : premier contact avec l'outillage **dev-only** `forge-mvc-testing`.

**Ce que vous allez apprendre :** `FakeRequest` imite l'objet `Request` du cœur, ce qui permet d'appeler un contrôleur sans serveur HTTP.

Premier palier du **niveau débutant** de la progression Testing.

## Ce que ce palier montre

- construire une `FakeRequest` ;
- lire ses données avec les accesseurs habituels.

## 1. Construire une requête factice

```python
from forge_mvc_testing import FakeRequest

req = FakeRequest("GET", "/clients?ville=Lyon")
```

## 2. Lire avec les accesseurs

```python
req.query("ville")     # "Lyon"
req.method             # "GET"
req.path               # "/clients"
```

`FakeRequest` expose les mêmes accesseurs que `Request` (`query`, `form`, `json`, `file`, `header`), ce qui rend le test fidèle.

## Après cette étape

[Palier suivant : Corps et JSON](testing-body.md)
