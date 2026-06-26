# forge-mvc-testing

Infrastructure de test partagée pour le framework Forge (ADR-041).

Ce paquet réservé au développement fournit de quoi tester Forge, ses opt-ins
officiels, et les opt-ins ou applications développés par des tiers :

- `FakeRequest` : une fausse requête HTTP pour tester contrôleurs et helpers sans serveur ;
- un plugin pytest (chargé automatiquement à l'installation) dont les fixtures
  autouse configurent le noyau Forge et réinitialisent l'état partagé entre
  tests (compteurs de tentatives, anti-replay, échecs d'audit).

## Statut

`forge-mvc-testing` est en `Development Status :: 4 - Beta`, aligné sur la
version du cœur. C'est un outil de **développement** : une application ne
l'importe jamais à l'exécution.

## Installation

```bash
pip install --pre forge-mvc-testing
```

En général comme dépendance de développement, par exemple dans
`requirements-dev.txt` :

```
forge-mvc-testing
```

## Utilisation

```python
from forge_mvc_testing import FakeRequest

def test_mon_controleur():
    request = FakeRequest(method="GET", query={"page": "2"})
    response = MonControleur.index(request)
    assert response.status == 200
```

Le plugin pytest s'active dès que le paquet est installé : ses fixtures autouse
préparent le noyau Forge et nettoient l'état partagé avant chaque test, sans
configuration.

## Licence

Distribué sous licence propriétaire Forge (`LicenseRef-Forge-Proprietary`),
comme le reste du framework. Voir `LICENSE`.
