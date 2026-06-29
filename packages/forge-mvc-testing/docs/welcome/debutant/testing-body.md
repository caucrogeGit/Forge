# Corps et JSON

Objectif : simuler un POST de formulaire ou un corps JSON.

**Ce que vous allez apprendre :** `FakeRequest` accepte un corps de formulaire (`body`) et un corps JSON (`json_body`).

Deuxième palier du **niveau débutant**.

## Corps de formulaire

```python
from forge_mvc_testing import FakeRequest

req = FakeRequest("POST", "/clients", body={"Nom": "Dupont"})
req.form("Nom")     # "Dupont"
```

## Corps JSON

```python
req = FakeRequest("POST", "/api/sync", json_body={"ids": [1, 2]})
req.json("ids")     # [1, 2]
```

## Fichiers et paramètres

`FakeRequest` accepte aussi `params` (query), `files` (téléversements) et `headers`, pour couvrir tous les cas d'un contrôleur.

!!! note "Surcharge de méthode"
    Comme une vraie requête, `FakeRequest` applique la surcharge `_method` (un POST avec `_method=DELETE` devient un DELETE).

## Après cette étape

[Bilan du niveau débutant](bilan.md)
