# La génération de QR Codes

Ce document explique comment `forge_mvc_qrcode` produit un QR Code en PNG ou en SVG, depuis du texte ou une URL.

Le fichier de code correspondant est `forge_mvc_qrcode/generator.py`.

## 1. À quoi sert ce module ?

Le module fournit la classe `QrCode`, qui enveloppe la bibliothèque `segno` (pur Python, sans Pillow).
Il ne sait rien de ce qu'il encode : l'application décide du contenu.
Aucun fichier n'est écrit, aucune route n'est imposée.

## 2. Construire un QR Code (`from_text`)

```python
@classmethod
def from_text(cls, text: str, *, error: str = "m") -> QrCode
```

`from_text` construit un QR Code depuis `text`.
`error` est le niveau de correction d'erreur : `"l"`, `"m"` (défaut), `"q"` ou `"h"`, du plus léger au plus robuste.

Un texte vide ou composé uniquement d'espaces lève `QrCodeError`.

```python
from forge_mvc_qrcode import QrCode

qr = QrCode.from_text("https://forgemvc.com")
qr_robuste = QrCode.from_text("https://forgemvc.com", error="h")
```

## 3. Rendre en PNG (`to_png`)

```python
def to_png(self, *, scale: int = 4, border: int = 4) -> bytes
```

`to_png` renvoie les octets bruts du PNG (`bytes`), reconnaissables à leur signature `b"\x89PNG\r\n\x1a\n"`.
`scale` multiplie la taille de chaque module, `border` règle la marge claire en nombre de modules.

```python
png = QrCode.from_text("https://forgemvc.com").to_png(scale=8, border=2)
```

## 4. Rendre en SVG (`to_svg`)

```python
def to_svg(self, *, scale: int = 4, border: int = 4) -> str
```

`to_svg` renvoie le document SVG sous forme de texte (`str`), commençant par une balise `<svg`.
Le SVG est vectoriel : net à toutes les tailles, utile pour l'impression.

```python
svg = QrCode.from_text("https://forgemvc.com").to_svg()
```

Une instance de `QrCode` est réutilisable : on peut appeler `to_png` puis `to_svg` sur le même objet.

## 5. Les types MIME

| Constante | Valeur |
|---|---|
| `PNG_MIME` | `image/png` |
| `SVG_MIME` | `image/svg+xml` |

Ces constantes sont les en-têtes `Content-Type` posés par la réponse HTTP (voir [La réponse HTTP](response.md)).

## 6. Voir aussi

- [La réponse HTTP](response.md) : `QrCodeResponse`, servir un QR Code depuis un contrôleur.
- [Les erreurs](errors.md) : `QrCodeError`.
- [Progression pédagogique QR Code](../welcome/installation.md) : apprendre le module pas à pas.
