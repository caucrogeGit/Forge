# Types MIME

Objectif : connaître les types MIME servis et où ils sont définis.

**Ce que vous allez apprendre :** le paquet expose deux constantes, `PNG_MIME` et `SVG_MIME`.
Elles valent `image/png` et `image/svg+xml`, et ce sont exactement les en-têtes `Content-Type` posés par `QrCodeResponse`.

Troisième palier du **niveau intermédiaire**.

## Ce que ce starter montre

- lire les constantes `PNG_MIME` et `SVG_MIME` ;
- vérifier le `content_type` d'une réponse.

## 1. Les constantes

```python
from forge_mvc_qrcode import PNG_MIME, SVG_MIME

print(PNG_MIME)   # image/png
print(SVG_MIME)   # image/svg+xml
```

## 2. Le type MIME de la réponse

```python
from forge_mvc_qrcode import QrCodeResponse

reponse_png = QrCodeResponse.from_text("https://forgemvc.com")
reponse_svg = QrCodeResponse.from_text("https://forgemvc.com", fmt="svg")

print(reponse_png.content_type)   # image/png
print(reponse_svg.content_type)   # image/svg+xml
```

### Comprendre ce code

- `QrCodeResponse` pose le bon `Content-Type` selon le format demandé.
- Les constantes évitent de réécrire les chaînes MIME à la main dans votre code.

## À retenir

- `PNG_MIME` vaut `image/png`, `SVG_MIME` vaut `image/svg+xml`.
- Ces valeurs sont les en-têtes `Content-Type` des réponses générées.

## Après ce starter

Vous maîtrisez les formats et leurs types.
Faisons le bilan du niveau intermédiaire.

[Bilan intermédiaire](bilan.md)
