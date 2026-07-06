# Sortie SVG

Objectif : générer un QR Code au format SVG.

**Ce que vous allez apprendre :** `to_svg` renvoie une **chaîne de texte** contenant un document SVG.
Le SVG est vectoriel : il reste net à toutes les tailles, ce qui est utile pour l'impression ou un affichage responsive.

Troisième palier du **niveau débutant**.

## Ce que ce starter montre

- obtenir un document SVG avec `to_svg` ;
- l'enregistrer dans un fichier `.svg`.

## 1. Générer et enregistrer un SVG

```python
from forge_mvc_qrcode import QrCode

svg = QrCode.from_text("https://forgemvc.com").to_svg()

print(type(svg))            # <class 'str'>
print("<svg" in svg)        # True

with open("forgemvc.svg", "w", encoding="utf-8") as fichier:
    fichier.write(svg)
```

### Comprendre ce code

- `to_svg()` renvoie une chaîne `str`, pas des octets.
- Le document commence par une balise `<svg`, c'est un fichier SVG valide.
- Les options `scale` et `border` existent aussi pour le SVG.

## PNG ou SVG ?

- Le **PNG** est une image matricielle, pratique pour un email ou une vignette.
- Le **SVG** est vectoriel, idéal pour l'impression ou un agrandissement.

## À retenir

- `to_svg()` renvoie un document SVG sous forme de texte.
- SVG vectoriel pour la netteté, PNG matriciel pour la simplicité.

## Après ce starter

Vous savez générer les deux formats.
Faisons le bilan du niveau débutant.

[Bilan débutant](bilan.md)
