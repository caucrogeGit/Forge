# Servir un SVG

Objectif : renvoyer un QR Code SVG depuis un contrôleur.

**Ce que vous allez apprendre :** `QrCodeResponse.from_text` accepte un argument
`fmt`.
Avec `fmt="svg"`, la réponse porte l'en-tête `Content-Type: image/svg+xml` et son
corps est le document SVG.

Deuxième palier du **niveau intermédiaire**.

## Ce que ce starter montre

- demander un SVG avec `fmt="svg"` ;
- comprendre la différence d'en-tête entre PNG et SVG.

## 1. Le contrôleur SVG

```python
# mvc/controllers/qrcode_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_qrcode import QrCodeResponse


class QrCodeController(BaseController):

    @staticmethod
    def show_svg(request: Request) -> Response:
        return QrCodeResponse.from_text("https://forgemvc.com", fmt="svg")
```

### Comprendre ce code

- `fmt="svg"` demande une sortie SVG plutôt que PNG.
- L'en-tête `Content-Type` de la réponse devient `image/svg+xml`.
- `fmt="png"` (la valeur par défaut) reste disponible pour le PNG.

## 2. Choisir le format à la demande

```python
@staticmethod
def show(request: Request) -> Response:
    fmt = request.query("format", "png")
    return QrCodeResponse.from_text("https://forgemvc.com", fmt=fmt)
```

### Comprendre ce code

- L'application lit le format voulu, par exemple depuis la requête.
- Un format inconnu lèvera `QrCodeError` : nous verrons comment le gérer au niveau avancé.

## À retenir

- `fmt="svg"` sert un SVG (`image/svg+xml`), `fmt="png"` sert un PNG (`image/png`).
- Le choix du format reste explicite, décidé par l'application.

## Après ce starter

Les deux formats ont chacun leur type MIME.
Regardons ces types de plus près.

[Types MIME](qrcode-mime.md)
