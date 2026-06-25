# Options de rendu

Objectif : ajuster la taille, la marge et la robustesse du QR Code.

**Ce que vous allez apprendre :** `to_png` et `to_svg` acceptent `scale` et
`border`.
`QrCode.from_text` accepte `error`, le niveau de correction d'erreur, qui rend le
code lisible même partiellement abîmé.

Deuxième palier du **niveau avancé**.

## Ce que ce starter montre

- régler `scale` et `border` au rendu ;
- choisir un niveau de correction d'erreur avec `error`.

## 1. Taille et marge

```python
from forge_mvc_qrcode import QrCode

qr = QrCode.from_text("https://forgemvc.com")

grand = qr.to_png(scale=10, border=2)
svg_compact = qr.to_svg(scale=3, border=1)
```

### Comprendre ce code

- `scale` agrandit chaque module, `border` règle la marge claire.
- Ces options valent pour le PNG comme pour le SVG.

## 2. Niveau de correction d'erreur

```python
qr_robuste = QrCode.from_text("https://forgemvc.com", error="h")
```

### Comprendre ce code

- `error` vaut `"l"`, `"m"` (défaut), `"q"` ou `"h"`, du plus léger au plus robuste.
- Un niveau élevé permet de lire le code même s'il est partiellement masqué ou imprimé sur un support abîmé.
- En contrepartie, le QR Code contient plus de modules.

## À retenir

- `scale` et `border` règlent la taille et la marge, au rendu PNG ou SVG.
- `error` règle la robustesse, de `"l"` à `"h"`.

## Après ce starter

Vous maîtrisez le rendu.
Dernier palier : comprendre pourquoi le cœur reste indépendant.

[Indépendance du cœur](qrcode-independance.md)
