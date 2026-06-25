# Aide-mémoire QR Code

Synthèse de l'API de `forge-mvc-qrcode`, à garder sous la main.

## Génération

| Appel | Résultat |
|-------|----------|
| `QrCode.from_text(texte)` | Construit un QR Code (lève `QrCodeError` si vide). |
| `QrCode.from_text(texte, error="h")` | Choisit la robustesse (`l`, `m`, `q`, `h`). |
| `qr.to_png(scale=4, border=4)` | Octets PNG (`bytes`). |
| `qr.to_svg(scale=4, border=4)` | Document SVG (`str`). |

## Réponse HTTP

| Appel | Résultat |
|-------|----------|
| `QrCodeResponse.from_text(texte)` | `Response` PNG (`Content-Type: image/png`). |
| `QrCodeResponse.from_text(texte, fmt="svg")` | `Response` SVG (`Content-Type: image/svg+xml`). |

## Constantes et erreurs

| Nom | Valeur ou rôle |
|-----|----------------|
| `PNG_MIME` | `image/png` |
| `SVG_MIME` | `image/svg+xml` |
| `QrCodeError` | Levée sur texte vide ou format inconnu (hérite de `ValueError`). |

## Rappel

Forge Core ne dépend pas du paquet.
L'application décide de ce qu'elle encode et de l'endroit où elle sert le QR Code.
