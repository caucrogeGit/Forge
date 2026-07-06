# Servir un QR Code depuis un contrôleur

Objectif : renvoyer un QR Code en HTTP depuis un contrôleur Forge.

**Ce que vous allez apprendre :** `QrCodeResponse.from_text` renvoie une `core.http.Response` ordinaire.
Le contrôleur la retourne telle quelle, comme n'importe quelle réponse Forge.
Par défaut, la réponse est un PNG avec l'en-tête `Content-Type: image/png`.

Premier palier du **niveau intermédiaire**.

## Ce que ce starter montre

- construire une réponse PNG avec `QrCodeResponse.from_text` ;
- la servir depuis une route Forge.

## Classes Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `QrCodeResponse.from_text(text)` | Construit une `Response` servant le QR Code (PNG par défaut). | Opt-ins |

## 1. Le contrôleur

```python
# mvc/controllers/qrcode_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_qrcode import QrCodeResponse


class QrCodeController(BaseController):

    @staticmethod
    def show(request: Request) -> Response:
        return QrCodeResponse.from_text("https://forgemvc.com")
```

### Comprendre ce code

- `QrCodeResponse.from_text(...)` génère le QR Code et renvoie une `Response`.
- La réponse est un PNG : son en-tête `Content-Type` vaut `image/png`.
- Aucun fichier n'est écrit, aucune route n'est imposée par le paquet.

## 2. La route

```python
# mvc/routes.py
from mvc.controllers.qrcode_controller import QrCodeController

with router.group("", public=True) as public:
    public.add("GET", "/qrcode", QrCodeController.show, name="qrcode_show")
```

En visitant `/qrcode`, le navigateur affiche l'image du QR Code.

## À retenir

- `QrCodeResponse.from_text(texte)` renvoie une `Response` PNG prête à servir.
- Le contrôleur retourne cette réponse directement.

## Après ce starter

Vous servez un PNG.
Voyons comment servir un SVG à la place.

[Servir un SVG](qrcode-svg-response.md)
