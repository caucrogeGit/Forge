# Installation de forge-mvc-qrcode

Objectif : installer l'opt-in QR Code et vérifier qu'il est prêt.

Le parcours qui suit montre, en trois niveaux, comment générer un QR Code, le
servir depuis un contrôleur, puis gérer les erreurs et les options de rendu.

## Installer le paquet

```bash
pip install --pre forge-mvc-qrcode
```

Le paquet dépend du cœur `forge-mvc` et de `segno`, une bibliothèque de
génération de QR Codes en pur Python.
`segno` n'a aucune dépendance et n'utilise pas Pillow.

## Vérifier l'installation

```python
from forge_mvc_qrcode import QrCode

png = QrCode.from_text("https://forgemvc.com").to_png()
print(len(png), "octets PNG")
```

Si ce script affiche un nombre d'octets non nul, l'opt-in fonctionne.

## Après cette étape

Place au niveau débutant : générer votre premier QR Code.

[Niveau débutant : Premier QR Code](debutant/qrcode-welcome.md)
