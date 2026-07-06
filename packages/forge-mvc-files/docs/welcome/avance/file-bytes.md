# Écrire des octets générés

Objectif : écrire un fichier **produit côté serveur** (rapport, export) avec la primitive `save_bytes`, sans passer par un upload HTTP.

**Ce que vous allez apprendre :** tout n'arrive pas d'un formulaire.
`save_bytes` range des octets dans la zone d'upload, avec un nom sûr et la même garde anti-traversal. C'est la brique d'écriture bas niveau sur laquelle `save_upload` lui-même est bâti (ADR-020).

Troisième palier du **niveau avancé** de la progression files.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-files` installé (palier « Installation »).

## Ce que ce starter montre

- un formulaire de saisie de contenu (CSRF) ;
- `save_bytes(data, original_name=..., category=..., root=...)` ;
- l'écriture d'un fichier **sans upload**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_files.save_bytes` | Écrire des octets dans la zone d'upload, nom sûr. | Médias |
| `forge_mvc_files.upload_root` | Racine de stockage cible. | Médias |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/file-bytes`, saisissez un contenu : un fichier `documents/rapport-….txt` est créé.

## Le contrôleur

```python
# mvc/controllers/file_bytes_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import save_bytes, upload_root


class FileBytesController(BaseController):
    """Starter pédagogique : écrire un fichier généré côté serveur."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_bytes/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def generate(request: Request) -> Response:
        content = request.form("content") or "Fichier généré par Forge."
        context = {"csrf_token": BaseController.csrf_token(request)}
        try:
            path = save_bytes(
                content.encode("utf-8"),
                original_name="rapport.txt",
                category="documents",
                root=upload_root(),
            )
        except Exception as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "file_bytes/index.html", context=context, request=request
            )
        context["generated_name"] = path.name
        return BaseController.render(
            "file_bytes/index.html", context=context, request=request
        )
```

## La vue

```html
<!-- mvc/views/file_bytes/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Écrire des octets générés - Forge</title>
</head>
<body>
  <h1>Écrire des octets générés</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}
  {% if generated_name %}
  <p data-level="success">Fichier généré : <code>documents/{{ generated_name }}</code></p>
  {% endif %}

  <form method="post" action="/file-bytes">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <textarea name="content" rows="4" cols="50" placeholder="Contenu du fichier…"></textarea>
    <br>
    <button type="submit">Générer le fichier</button>
  </form>

  <p>Le contenu saisi est écrit par <code>save_bytes</code> sous un nom sûr, sans
  passer par un upload : la même primitive d'écriture que <code>save_upload</code>.</p>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.file_bytes_controller import FileBytesController

with router.group("", public=True) as public:
    public.add("GET", "/file-bytes", FileBytesController.index, name="file_bytes_index")
    public.add("POST", "/file-bytes", FileBytesController.generate, name="file_bytes_generate")
```

### Comprendre ce code

- `save_bytes` prend des **octets** (pas un fichier HTTP) : idéal pour un contenu généré (CSV, PDF, JSON exporté).
- Le nom est rendu **sûr** et **unique** : pas de collision, pas de traversée.
- C'est la **même primitive d'écriture** que `save_upload` utilise après validation, d'où la vision ADR-020 : files = des primitives, chaque opt-in compose.

## À retenir

- `save_bytes` écrit un contenu **généré** côté serveur, en sécurité.
- Même garde (nom sûr, anti-traversal) que pour un upload.
- C'est la fondation : `save_upload` = valider **puis** `save_bytes`.

## Après ce starter

Vous avez parcouru toute la progression files : du premier contact aux primitives.

[Bilan du niveau avancé](bilan.md)
