# Fixtures et isolation

Objectif : profiter des fixtures du plugin pytest pour des tests propres.

**Ce que vous allez apprendre :** le plugin configure le noyau et nettoie l'état entre les tests, automatiquement.

Premier palier du **niveau intermédiaire**.

## Le plugin pytest

Installé, le paquet enregistre un plugin pytest (point d'entrée `pytest11`) : aucune ligne de `conftest` à écrire.

## Fixtures fournies

| Fixture | Portée | Rôle |
|---|---|---|
| `configure_forge_kernel` | session, autouse | configure le noyau pour les tests |
| `clear_sessions` | autouse | sessions vidées entre tests |
| `clear_rate_limits` / `clear_upload_rate_limits` | autouse | rate-limits réinitialisés |
| `fake_request` | fonction | fabrique une `FakeRequest` |

## Utiliser la fixture fake_request

```python
def test_liste(fake_request):
    req = fake_request("GET", "/clients")
    ...
```

Les fixtures autouse s'appliquent sans être nommées : chaque test démarre d'un état propre.

!!! note "Isolation par défaut"
    Sans ces nettoyages, un test laissant une session ou un rate-limit pourrait fausser le suivant.

    Le plugin garantit l'indépendance des tests.

## Après cette étape

[Palier suivant : Tester un contrôleur](testing-controller.md)
