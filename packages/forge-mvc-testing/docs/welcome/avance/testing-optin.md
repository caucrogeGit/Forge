# Tester un opt-in

Objectif : utiliser `forge-mvc-testing` pour tester votre propre opt-in.

**Ce que vous allez apprendre :** l'outillage sert aussi à tester les briques opt-in, avec un exécuteur de base factice.

Premier palier du **niveau avancé**.

## Contrôleurs d'opt-in

Un opt-in à routes (par exemple QR Code) s'appuie sur des contrôleurs : testez-les avec `FakeRequest`, comme les contrôleurs de l'application.

```python
from forge_mvc_testing import FakeRequest
from forge_mvc_qrcode import QrCodeResponse


def test_qr_png():
    req = FakeRequest("GET", "/qr?url=https://forgemvc.com")
    resp = QrCodeResponse.from_text(req.query("url"), fmt="png")
    assert resp.content_type == "image/png"
```

## Opt-ins à exécuteur injecté

Beaucoup d'opt-ins (settings, audit, stats...) reçoivent un exécuteur SQL injecté. En test, passez un **faux exécuteur** pour vérifier les requêtes sans base :

```python
def fake_execute(sql, params):
    captured.append((sql, params))
    return 1

set_setting("k", "v", db=FakeDb(execute=fake_execute))
```

!!! note "Frontière de test"
    Les fixtures du plugin couvrent le noyau ; pour la base, injectez un faux exécuteur (ou une base SQLite jetable avec `forge-mvc-sqlite`).

## Après cette étape

[Palier suivant : Pourquoi dev-only](testing-devonly.md)
