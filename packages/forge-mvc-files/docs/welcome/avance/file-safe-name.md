# Assainir un nom de fichier

Objectif : transformer un nom de fichier utilisateur **arbitraire** en un nom
**sûr**, avec la primitive `secure_filename`.

**Ce que vous allez apprendre :** on entre dans les **primitives** de
`forge-mvc-files`, la boîte à outils que les opt-ins média composent (ADR-020).
`secure_filename` retire toute composante de répertoire et neutralise les caractères
dangereux : ce qui reste ne peut désigner qu'un fichier.

Premier palier du **niveau avancé** de la progression files.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-files` installé (palier « Installation »).

## Ce que ce starter montre

- `secure_filename(name)` appliqué à un nom piégé ;
- la disparition du chemin (`../Mon Dossier/`) et des caractères spéciaux ;
- une transformation **pure** (aucune écriture).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_files.secure_filename` | Assainir un nom de fichier utilisateur. | Médias |
| `request.query(...)` | Lire le nom à assainir. | Request |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/file-safe-name` et essayez
`../Mon Dossier/Rapport Final!.PDF` → `Rapport_Final_.PDF`.

## Le contrôleur

```python
# mvc/controllers/file_safe_name_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError, secure_filename

_DEMO_NAME = "../Mon Dossier/Rapport Final!.PDF"


def _safe_view(name: str) -> dict:
    try:
        return {"input": name, "safe": secure_filename(name), "error": None}
    except UploadError as exc:
        return {"input": name, "safe": None, "error": str(exc)}


class FileSafeNameController(BaseController):
    """Starter pédagogique : assainir un nom de fichier utilisateur."""

    @staticmethod
    def index(request: Request) -> Response:
        name = request.query("name") or _DEMO_NAME
        return BaseController.render(
            "file_safe_name/index.html", context=_safe_view(name), request=request
        )

    @staticmethod
    def inspect(request: Request) -> Response:
        name = request.query("name") or _DEMO_NAME
        return Response.json(_safe_view(name))
```

## La vue

```html
<!-- mvc/views/file_safe_name/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Assainir un nom de fichier - Forge</title>
</head>
<body>
  <h1>Assainir un nom de fichier</h1>

  <form method="get" action="/file-safe-name">
    <input type="text" name="name" value="{{ input }}" size="50">
    <button type="submit">Assainir</button>
  </form>

  <p>Entrée : <code>{{ input }}</code></p>
  {% if safe %}
  <p data-level="success">Nom sûr : <code>{{ safe }}</code></p>
  {% endif %}
  {% if error %}
  <p data-level="error">Refusé : {{ error }}</p>
  {% endif %}

  <p>Le chemin (<code>../Mon Dossier/</code>) disparaît, les caractères dangereux
  sont remplacés : ce qui reste ne peut plus désigner qu'un fichier, jamais un
  répertoire parent.</p>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.file_safe_name_controller import FileSafeNameController

with router.group("", public=True) as public:
    public.add("GET", "/file-safe-name", FileSafeNameController.index, name="file_safe_name_index")
    public.add("GET", "/file-safe-name/inspect", FileSafeNameController.inspect, name="file_safe_name_inspect")
```

### Comprendre ce code

- Le **nom** n'est jamais de confiance : il peut contenir `../`, des espaces, des
  caractères de contrôle. `secure_filename` le réduit à un nom de fichier inerte.
- Un nom qui devient **vide** après nettoyage est refusé (`UploadError`) plutôt que
  de produire un fichier sans nom.
- C'est une brique que `save_upload` utilise en interne ; ici on la voit isolée.

## À retenir

- Un nom de fichier utilisateur est **assaini** avant tout usage.
- `secure_filename` retire le chemin et neutralise les caractères dangereux.
- C'est une **primitive composable**, pas réservée à `save_upload`.

## Après ce starter

Le nom est sûr. La suite : juger la sûreté d'un **chemin** entier.

[Chemin anti-traversal](file-safe-path.md)
