# Premier test

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
