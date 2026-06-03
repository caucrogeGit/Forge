# Téléverser un fichier

Objectif : recevoir un fichier envoyé par l'utilisateur et le **stocker** en
toute sécurité.

**Ce que vous allez apprendre :** un formulaire `multipart/form-data`, la
récupération du fichier reçu avec `request.file(...)`, et son stockage par
`core.uploads.save_upload`. Cette fonction **valide** le fichier (extension,
type MIME, taille) **avant** d'écrire sur le disque : Forge ne fait jamais
confiance aveuglément à ce que l'utilisateur envoie.

Palier 2 du **niveau avancé** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Relations entre tables](relations.md).

## Ce que ce starter montre

- un formulaire HTML en **`multipart/form-data`** ;
- la récupération du fichier reçu avec `request.file("document")` ;
- le stockage validé via `core.uploads.save_upload` ;
- l'affichage du nom et de la taille du fichier enregistré, ou de l'erreur si le
  fichier est refusé.

Aucune base de données : le fichier est stocké sur le disque, pas en base.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `request.file` | Récupérer le fichier reçu (`UploadedFile`). | [Request](../../../reference/api.md#corehttp) |
| `core.uploads.save_upload` | Valider puis stocker le fichier sur le disque. | [Uploads](../../../reference/api.md#coreuploads) |
| `BaseController.csrf_token` | Protéger le formulaire d'envoi. | [BaseController](../../../reference/api.md#coremvccontroller) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/file-upload`, choisissez un fichier autorisé et
cliquez **Envoyer** : le nom et la taille du fichier enregistré s'affichent. Un
fichier d'un type non autorisé déclenche un message d'erreur clair.

## Le contrôleur

```python
# mvc/controllers/file_upload_controller.py
from core.uploads import UploadError, save_upload


class FileUploadController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_upload/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def upload(request: Request) -> Response:
        uploaded = request.file("document")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucun fichier sélectionné."
            return BaseController.render("file_upload/index.html", context=context, request=request)
        try:
            saved = save_upload(uploaded, "documents")
        except UploadError as exc:
            context["error"] = str(exc)
            return BaseController.render("file_upload/index.html", context=context, request=request)
        context["saved"] = saved
        return BaseController.render("file_upload/index.html", context=context, request=request)
```

### Comprendre ce code

- `request.file("document")` renvoie un `UploadedFile` (ou `None` si rien n'a été
  envoyé) — on traite ce cas explicitement.
- `save_upload(uploaded, "documents")` **valide** extension, type MIME et taille,
  puis écrit le fichier sous la catégorie `documents`. En cas de refus, elle lève
  une `UploadError` que l'on attrape pour afficher un message clair.
- `SavedUpload` expose `original_name`, `size` et `path` (chemin de stockage
  relatif) — utiles pour confirmer l'enregistrement.

## La vue

```html
<!-- mvc/views/file_upload/index.html -->
{% if saved %}
<p data-level="success">
  Fichier enregistré : <strong>{{ saved.original_name }}</strong>
  ({{ saved.size }} octets) → <code>{{ saved.path }}</code>
</p>
{% endif %}

<form method="post" action="/file-upload" enctype="multipart/form-data">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <input type="file" name="document" required>
  <button type="submit">Envoyer</button>
</form>
```

### Comprendre ce code

- `enctype="multipart/form-data"` est **obligatoire** pour transmettre un
  fichier : sans lui, le navigateur n'envoie que le nom.
- Le formulaire reste protégé par **CSRF**, comme tout POST.

## À retenir

- Un upload de fichier passe par un formulaire `multipart/form-data`.
- `request.file(...)` récupère le fichier ; `save_upload` le **valide** avant de
  l'écrire — jamais d'écriture aveugle.
- Forge contrôle extension, type MIME et taille par défaut : la sécurité d'abord.

## Après ce starter

Vous savez recevoir et stocker un fichier. Faites le point dans le bilan du
niveau.

[Bilan du niveau avancé](bilan.md)
