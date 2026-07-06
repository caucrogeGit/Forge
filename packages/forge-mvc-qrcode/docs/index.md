# QR Code (forge-mvc-qrcode)

`forge-mvc-qrcode` est un opt-in qui génère des QR Codes PNG ou SVG depuis du texte ou une URL, et les sert via une réponse HTTP utilisable dans un contrôleur Forge.

Le cœur de Forge ignore tout des QR Codes.
Ce paquet fournit l'API.
L'application décide de ce qu'elle encode.

## Installation

```bash
pip install --pre forge-mvc-qrcode
```

Le paquet dépend du cœur `forge-mvc` et de `segno`, une bibliothèque de génération de QR Codes en pur Python, sans Pillow ni dépendance lourde.

## Génération PNG

`QrCode.from_text` construit le QR Code.
`to_png` renvoie les octets PNG.

```python
from forge_mvc_qrcode import QrCode

qr = QrCode.from_text("https://forgemvc.com")
png_bytes = qr.to_png()
```

Le type MIME attendu est `image/png`, exposé par la constante `PNG_MIME`.

## Génération SVG

`to_svg` renvoie le document SVG sous forme de texte.

```python
svg_text = QrCode.from_text("https://forgemvc.com").to_svg()
```

Le type MIME attendu est `image/svg+xml`, exposé par la constante `SVG_MIME`.

## Erreurs d'entrée

Un texte vide ou composé uniquement d'espaces lève `QrCodeError`.

```python
from forge_mvc_qrcode import QrCode, QrCodeError

try:
    QrCode.from_text("")
except QrCodeError:
    pass
```

## Usage depuis un contrôleur Forge

`QrCodeResponse.from_text` renvoie une réponse Forge ordinaire.
Le contrôleur la retourne telle quelle.

```python
from forge_mvc_qrcode import QrCodeResponse

def qrcode(request):
    return QrCodeResponse.from_text("https://forgemvc.com")
```

La réponse est un PNG par défaut, avec l'en-tête `Content-Type: image/png`.
Passer `fmt="svg"` produit un SVG avec `Content-Type: image/svg+xml`.

Aucun fichier n'est écrit, aucune route n'est imposée, rien n'est stocké en base.

## Limites actuelles

Ce socle se limite à générer et servir un QR Code.

Ne sont pas inclus dans ce paquet :

- commande CLI `forge qrcode:*` ;
- stockage dans `storage/` ;
- génération PDF ;
- scanner de QR Code ;
- logique métier (badge, ticket, inventaire, élève).

Ces sujets pourront faire l'objet de tickets ultérieurs.

## Indépendance du cœur

Forge Core ne dépend pas de `forge-mvc-qrcode`.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
Un projet qui n'installe pas le paquet ne voit aucune référence aux QR Codes.
