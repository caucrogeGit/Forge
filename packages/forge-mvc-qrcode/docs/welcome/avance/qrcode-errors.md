# Gérer les erreurs

Objectif : réagir proprement à une entrée invalide.

**Ce que vous allez apprendre :** le paquet lève `QrCodeError` dans deux cas, un texte vide (ou composé uniquement d'espaces) et un format de sortie inconnu.
`QrCodeError` hérite de `ValueError` : un contrôleur peut la rattraper comme une erreur d'entrée ordinaire.

Premier palier du **niveau avancé**.

## Ce que ce starter montre

- déclencher `QrCodeError` sur un texte vide ;
- rattraper l'erreur dans un contrôleur pour renvoyer une réponse claire.

## 1. Les cas d'erreur

```python
from forge_mvc_qrcode import QrCode, QrCodeResponse, QrCodeError

try:
    QrCode.from_text("")            # texte vide
except QrCodeError as erreur:
    print(erreur)

try:
    QrCodeResponse.from_text("ok", fmt="pdf")   # format inconnu
except QrCodeError as erreur:
    print(erreur)
```

### Comprendre ce code

- Un texte vide ou seulement composé d'espaces est refusé : un QR Code vide n'a pas de sens.
- Un `fmt` autre que `"png"` ou `"svg"` est refusé.
- Le message d'erreur indique la cause de façon explicite.

## 2. Rattraper dans un contrôleur

```python
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_qrcode import QrCodeResponse, QrCodeError


class QrCodeController(BaseController):

    @staticmethod
    def show(request: Request) -> Response:
        cible = request.query("url", "")
        try:
            return QrCodeResponse.from_text(cible)
        except QrCodeError:
            return Response.text("URL manquante ou invalide.", status=400)
```

### Comprendre ce code

- L'application lit l'URL à encoder, ici depuis la requête.
- Si elle est vide, `QrCodeResponse.from_text` lève `QrCodeError`.
- Le contrôleur renvoie alors une réponse `400` explicite plutôt qu'une erreur serveur.

## À retenir

- `QrCodeError` couvre le texte vide et le format inconnu.
- Elle hérite de `ValueError`, donc se rattrape comme une erreur d'entrée.

## Après ce starter

Les erreurs sont sous contrôle.
Réglons maintenant les options de rendu.

[Options de rendu](qrcode-options.md)
