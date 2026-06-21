# Téléverser une image

Objectif : recevoir une image, **vérifier que c'en est vraiment une**, l'écrire
sur le disque et générer ses variantes — le tout avec `save_image_upload`.

**Ce que vous allez apprendre :** un upload d'image n'est pas un upload de
fichier comme un autre. `forge_mvc_images.save_image_upload` vérifie le
**contenu** (un PDF déguisé en `.jpg` est rejeté, garde anti-bombe incluse)
**avant** d'écrire, puis produit automatiquement les variantes `medium` et
`thumbnail`.

Deuxième palier du **niveau débutant** de la progression images.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-images` installé (palier « Installation » de
    ce parcours). L'upload brut générique appartient à `forge-mvc-files` ; le
    chemin **image-aware** appartient à `forge-mvc-images`.

## Ce que ce starter montre

- un formulaire `multipart/form-data` (avec CSRF) ;
- la récupération du fichier avec `request.file("image")` ;
- la vérification + écriture + génération des variantes via `save_image_upload` ;
- l'affichage du résultat (nom, taille, variantes) ou de l'erreur si l'image est
  refusée.

Aucune base de données : l'image et ses variantes vivent sur le disque.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.save_image_upload` | Vérifier le contenu, écrire, générer les variantes. | Médias |
| `forge_mvc_files.UploadError` | Erreur levée si l'image est refusée (format, taille, contenu). | Médias |
| `request.file(...)` | Récupérer le fichier envoyé. | Request |
| `BaseController.render` | Rendre la vue du formulaire. | BaseController |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/image-upload`, choisissez une image (`.jpg`,
`.png`, `.webp`) et envoyez : la page confirme l'enregistrement et liste les
variantes générées. Un fichier qui n'est pas une vraie image est refusé avec un
message d'erreur.

## Le contrôleur

```python
# mvc/controllers/image_upload_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError
from forge_mvc_images import save_image_upload


class ImageUploadController(BaseController):
    """Starter pédagogique : recevoir, vérifier et décliner une image en variantes."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "image_upload/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def upload(request: Request) -> Response:
        uploaded = request.file("image")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucune image sélectionnée."
            return BaseController.render(
                "image_upload/index.html", context=context, request=request
            )
        try:
            saved = save_image_upload(uploaded, "images")
        except UploadError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "image_upload/index.html", context=context, request=request
            )
        context["saved"] = saved
        return BaseController.render(
            "image_upload/index.html", context=context, request=request
        )
```

### Comprendre ce code

- `save_image_upload` fait trois choses dans l'ordre : **vérifier** le contenu
  (`verify_image_content`), **écrire** via l'upload générique du core, puis
  **générer** les variantes. La vérification précède toujours l'écriture.
- On ne fait **jamais** confiance à l'extension ou au `Content-Type` envoyés :
  c'est le contenu binaire réel qui décide.
- Toutes les erreurs (extension, MIME, taille, contenu non-image) héritent de
  `UploadError` — un seul `except` suffit à les présenter proprement.
- `saved.variants` est un dictionnaire `{"medium": ..., "thumbnail": ...}` des
  chemins générés.

## La vue

Le contrôleur rend `image_upload/index.html` : créez ce fichier.

```html
<!-- mvc/views/image_upload/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Téléverser une image — Forge</title>
</head>
<body>
  <h1>Téléverser une image</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}

  {% if saved %}
  <p data-level="success">
    Image enregistrée : <strong>{{ saved.original_name }}</strong>
    ({{ saved.size }} octets) → <code>{{ saved.path }}</code>
  </p>
  <ul>
    {% for name, variant_path in saved.variants.items() %}
    <li>Variante <strong>{{ name }}</strong> : <code>{{ variant_path }}</code></li>
    {% endfor %}
  </ul>
  {% endif %}

  <form method="post" action="/image-upload" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="file" name="image" accept="image/*" required>
    <button type="submit">Envoyer</button>
  </form>
</body>
</html>
```

## La route

Déclarez les deux routes dans `mvc/routes.py`, à l'intérieur du groupe public.

```python
# mvc/routes.py
from mvc.controllers.image_upload_controller import ImageUploadController

with router.group("", public=True) as public:
    public.add("GET", "/image-upload", ImageUploadController.index, name="image_upload_index")
    public.add("POST", "/image-upload", ImageUploadController.upload, name="image_upload_store")
```

## À retenir

- Un upload d'image **vérifie le contenu avant d'écrire** — défense contre les
  fichiers déguisés et les images-bombes.
- Les variantes (`medium`, `thumbnail`) sont générées **automatiquement**.
- L'upload brut est dans `forge-mvc-files` ; l'upload image-aware est dans
  `forge-mvc-images`.

## Après ce starter

L'image est stockée avec ses variantes. La suite : comprendre **où** vivent ces
variantes et comment construire leurs URL.

[Miniatures et variantes](image-variants.md)
