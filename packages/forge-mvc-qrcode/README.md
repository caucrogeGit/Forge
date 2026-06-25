# forge-mvc-qrcode

Opt-in Forge de génération de QR Codes.

Produire un QR Code PNG ou SVG depuis du texte ou une URL, et le servir via une
réponse HTTP utilisable dans un contrôleur Forge.

Le cœur de Forge ignore tout des QR Codes.
Ce paquet fournit l'API.
L'application décide de ce qu'elle encode.

## Installation

```bash
pip install --pre forge-mvc-qrcode
```

Dépendances : `forge-mvc` (cœur) et `segno` (génération pur Python, sans Pillow).

## Génération PNG et SVG

```python
from forge_mvc_qrcode import QrCode

qr = QrCode.from_text("https://forgemvc.com")

png_bytes = qr.to_png()   # octets PNG
svg_text = qr.to_svg()    # document SVG (texte)
```

Un texte vide lève `QrCodeError`.

## Réponse HTTP depuis un contrôleur

```python
from forge_mvc_qrcode import QrCodeResponse

def qrcode(request):
    return QrCodeResponse.from_text("https://forgemvc.com")
```

La réponse est un PNG par défaut (`Content-Type: image/png`).
Passer `fmt="svg"` pour un SVG (`Content-Type: image/svg+xml`).

## Limites de ce socle

Ce paquet ne fait que générer et servir un QR Code.
Pas de commande CLI, pas de stockage, pas de scanner, pas de PDF, pas de logique
métier (badge, ticket, inventaire). Ces usages restent à la charge de
l'application ou de tickets ultérieurs.
