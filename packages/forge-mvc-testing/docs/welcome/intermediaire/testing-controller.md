# Tester un contrôleur

Objectif : écrire un test complet d'une action de contrôleur.

**Ce que vous allez apprendre :** appeler une action avec une `FakeRequest` et vérifier la `Response`.

Deuxième palier du **niveau intermédiaire**.

## Le principe

Un contrôleur Forge est une fonction `action(request) -> Response`.
Pour le tester, on lui passe une `FakeRequest` et on inspecte la `Response`.

## Exemple

```python
from forge_mvc_testing import FakeRequest
from mvc.controllers.article import create


def test_create_ok():
    req = FakeRequest("POST", "/article/create", body={"title": "Bonjour"})
    response = create(req)
    assert response.status == 200


def test_create_refuse_titre_vide():
    req = FakeRequest("POST", "/article/create", body={"title": ""})
    response = create(req)
    assert response.status == 400
```

## Inspecter la réponse

`response.status`, `response.body` et `response.content_type` permettent des assertions précises, sans rendu HTTP réel.

!!! note "Test fidèle"
    On teste la vraie logique du contrôleur : seul le transport HTTP est simulé.

## Après cette étape

[Suivant : le client de test](testing-client.md)
