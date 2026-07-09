# Premier QR Code

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-qrcode` avant de commencer : voir sa [référence](../../reference.md).

Objectif : premier contact avec le module **opt-in** `forge-mvc-qrcode`.

**Ce que vous allez apprendre :** la génération de QR Codes repose sur une classe `QrCode`.
On la construit depuis du texte ou une URL avec `QrCode.from_text`, puis on rend le code en PNG avec `to_png`.
Le module ne sait rien de ce qu'il encode : l'application décide du contenu.

Premier palier du **niveau débutant** de la progression QR Code.

!!! note "Module opt-in"
    Si `forge-mvc-qrcode` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- construire un QR Code depuis une URL avec `QrCode.from_text` ;
- obtenir les octets PNG avec `to_png` et les écrire dans un fichier.

## Classes Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `QrCode.from_text(text)` | Construit un QR Code depuis du texte ou une URL. | Opt-ins |
| `QrCode.to_png()` | Rend le QR Code en octets PNG. | Opt-ins |

## 1. Générer et enregistrer un PNG

```python
from forge_mvc_qrcode import QrCode

qr = QrCode.from_text("https://forgemvc.com")
png_bytes = qr.to_png()

with open("forgemvc.png", "wb") as fichier:
    fichier.write(png_bytes)
```

### Comprendre ce code

- `QrCode.from_text("https://forgemvc.com")` construit le QR Code à partir de l'URL.
- `to_png()` renvoie les octets bruts du PNG, prêts à être écrits ou servis.
- Rien n'est stocké automatiquement : vous décidez où vont les octets.

## À retenir

- Un QR Code se construit avec `QrCode.from_text(texte)`.
- `to_png()` renvoie des octets PNG.
- L'objet est réutilisable : on peut rappeler `to_png()` ou `to_svg()` ensuite.

## Après ce starter

Vous avez un premier PNG.
Regardons de plus près la sortie PNG et ses options.

[Sortie PNG](qrcode-png.md)
