# Sortie PNG

Objectif : comprendre ce que renvoie `to_png` et comment ajuster le rendu.

**Ce que vous allez apprendre :** `to_png` renvoie des **octets** (`bytes`), pas
un fichier.
Deux options simples, `scale` et `border`, contrôlent la taille des modules et
la marge blanche autour du code.

Deuxième palier du **niveau débutant**.

## Ce que ce starter montre

- lire le type de retour de `to_png` (`bytes`) ;
- ajuster `scale` (taille d'un module) et `border` (marge).

## 1. Les octets PNG

```python
from forge_mvc_qrcode import QrCode

png = QrCode.from_text("https://forgemvc.com").to_png()

print(type(png))            # <class 'bytes'>
print(png[:8])              # signature PNG : b'\x89PNG\r\n\x1a\n'
```

### Comprendre ce code

- Le retour est une suite d'octets, reconnaissable à sa signature PNG.
- Ces octets peuvent être écrits sur disque, servis en HTTP, ou mis en cache.

## 2. Ajuster la taille et la marge

```python
qr = QrCode.from_text("https://forgemvc.com")

petit = qr.to_png(scale=2)            # modules plus petits
grand = qr.to_png(scale=8)            # modules plus grands
sans_marge = qr.to_png(border=0)      # aucune marge blanche
```

### Comprendre ce code

- `scale` multiplie la taille de chaque module du QR Code.
- `border` est l'épaisseur de la marge claire, en nombre de modules.
- Les valeurs par défaut (`scale=4`, `border=4`) conviennent à la plupart des usages.

## À retenir

- `to_png()` renvoie des `bytes`.
- `scale` règle la taille, `border` règle la marge.

## Après ce starter

Le PNG est une image binaire.
Voyons la sortie SVG, qui est du texte.

[Sortie SVG](qrcode-svg.md)
