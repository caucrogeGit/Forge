# La réponse HTTP

Ce document explique comment `forge_mvc_qrcode` sert un QR Code depuis un contrôleur Forge.

Le fichier de code correspondant est `forge_mvc_qrcode/response.py`.

## 1. À quoi sert ce module ?

Le module fournit `QrCodeResponse`, une fabrique de réponses HTTP.
`QrCodeResponse.from_text` renvoie une `core.http.Response` ordinaire : le contrôleur la retourne telle quelle.

La dépendance va de l'opt-in vers le cœur (`core.http.Response`), jamais l'inverse.

## 2. Construire une réponse (`from_text`)

```python
@staticmethod
def from_text(
    text: str,
    *,
    fmt: str = "png",
    scale: int = 4,
    border: int = 4,
    headers: dict[str, str] | None = None,
) -> Response
```

`from_text` génère le QR Code de `text` et renvoie la réponse correspondante.

| Argument | Rôle |
|---|---|
| `fmt` | `"png"` (défaut, `image/png`) ou `"svg"` (`image/svg+xml`) |
| `scale`, `border` | taille des modules et marge, transmis au rendu |
| `headers` | en-têtes HTTP additionnels, fusionnés à la réponse |

Un texte vide lève `QrCodeError`.
Un `fmt` autre que `"png"` ou `"svg"` lève aussi `QrCodeError`.

## 3. Servir un QR Code

```python
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_qrcode import QrCodeResponse


class QrCodeController(BaseController):

    @staticmethod
    def show(request: Request) -> Response:
        return QrCodeResponse.from_text("https://forgemvc.com")
```

Par défaut, la réponse est un PNG (`Content-Type: image/png`).
Pour servir un SVG :

```python
return QrCodeResponse.from_text("https://forgemvc.com", fmt="svg")
```

## 4. Ce que la réponse ne fait pas

- Elle n'écrit aucun fichier et ne stocke rien.
- Elle n'impose aucune route : l'application choisit l'URL.
- Elle ne contient aucune logique métier (badge, ticket, inventaire).

## 5. Voir aussi

- [La génération de QR Codes](generator.md) : `QrCode`, `to_png`, `to_svg`.
- [Les erreurs](errors.md) : `QrCodeError`.
- [Progression pédagogique QR Code](../welcome/installation.md) : apprendre le module pas à pas.
