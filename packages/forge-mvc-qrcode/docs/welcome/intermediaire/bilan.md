# Bilan, niveau intermédiaire (QR Code)

Récapitulatif du **niveau intermédiaire** de la progression QR Code.
Ce niveau relie le générateur au web : servir un QR Code en HTTP depuis un
contrôleur.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1, [Servir depuis un contrôleur](qrcode-controller.md) | Renvoyer un PNG avec `QrCodeResponse.from_text`. |
| 2, [Servir un SVG](qrcode-svg-response.md) | Servir un SVG avec `fmt="svg"`. |
| 3, [Types MIME](qrcode-mime.md) | Connaître `PNG_MIME` / `SVG_MIME` et le `content_type`. |

Vous savez servir un QR Code en PNG ou en SVG depuis une route Forge.

## Et ensuite

Place au niveau **avancé** : gérer les erreurs d'entrée, régler les options de
rendu, et comprendre l'indépendance du cœur.

[Niveau avancé : Gérer les erreurs](../avance/qrcode-errors.md)
