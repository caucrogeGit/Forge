# Les erreurs

Ce document décrit l'erreur levée par `forge_mvc_qrcode` en cas d'entrée invalide.

Le fichier de code correspondant est `forge_mvc_qrcode/errors.py`.

## 1. `QrCodeError`

```python
class QrCodeError(ValueError):
    ...
```

`QrCodeError` signale une entrée invalide pour la génération d'un QR Code.
Elle hérite de `ValueError` : un contrôleur peut la rattraper comme une erreur d'entrée ordinaire.

## 2. Quand est-elle levée ?

| Cause | Origine |
|---|---|
| Texte vide ou composé uniquement d'espaces | `QrCode.from_text` |
| Niveau de correction `error` inconnu (hors `l`, `m`, `q`, `h`) | `QrCode.from_text` |
| Texte trop long pour la capacité d'un QR Code | `QrCode.from_text` |
| `scale` < 1 ou `border` < 0 | `QrCode.to_png`, `QrCode.to_svg` |
| Format de sortie inconnu (autre que `"png"` ou `"svg"`) | `QrCodeResponse.from_text` |

Le message d'erreur indique la cause de façon explicite.

## 3. Rattraper l'erreur

```python
from forge_mvc_qrcode import QrCodeResponse, QrCodeError

try:
    return QrCodeResponse.from_text(request.query("url", ""))
except QrCodeError:
    return Response.text("URL manquante ou invalide.", status=400)
```

Comme `QrCodeError` dérive de `ValueError`, un `except ValueError` la rattrape aussi, mais un `except QrCodeError` reste plus explicite.

## 4. Voir aussi

- [La génération de QR Codes](generator.md) : `QrCode`, `to_png`, `to_svg`.
- [La réponse HTTP](response.md) : `QrCodeResponse`.
- [Progression pédagogique QR Code](../welcome/installation.md) : apprendre le module pas à pas.
