# Écrire des octets générés

Objectif : écrire un fichier **produit côté serveur** (rapport, export) avec la
primitive `save_bytes`, sans passer par un upload HTTP.

**Ce que vous allez apprendre :** tout n'arrive pas d'un formulaire. `save_bytes`
range des octets dans la zone d'upload, avec un nom sûr et la même garde
anti-traversal. C'est la brique d'écriture bas niveau sur laquelle `save_upload`
lui-même est bâti (ADR-020).

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
| `forge_mvc_files.save_bytes` | Écrire des octets dans la zone d'upload, nom sûr. | [Médias](../../../features/media.md) |
| `forge_mvc_files.upload_root` | Racine de stockage cible. | [Médias](../../../features/media.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/file-bytes`, saisissez un contenu : un fichier
`documents/rapport-….txt` est créé.

## Le contrôleur

```python
# mvc/controllers/file_bytes_controller.py
from forge_mvc_files import save_bytes, upload_root


class FileBytesController(BaseController):

    @staticmethod
    def generate(request: Request) -> Response:
        content = request.form("content") or "Fichier généré par Forge."
        path = save_bytes(
            content.encode("utf-8"),
            original_name="rapport.txt",
            category="documents",
            root=upload_root(),
        )
        context = {"csrf_token": BaseController.csrf_token(request), "generated_name": path.name}
        return BaseController.render("file_bytes/index.html", context=context, request=request)
```

### Comprendre ce code

- `save_bytes` prend des **octets** (pas un fichier HTTP) : idéal pour un contenu
  généré (CSV, PDF, JSON exporté).
- Le nom est rendu **sûr** et **unique** : pas de collision, pas de traversée.
- C'est la **même primitive d'écriture** que `save_upload` utilise après validation
  — d'où la vision ADR-020 : files = des primitives, chaque opt-in compose.

## À retenir

- `save_bytes` écrit un contenu **généré** côté serveur, en sécurité.
- Même garde (nom sûr, anti-traversal) que pour un upload.
- C'est la fondation : `save_upload` = valider **puis** `save_bytes`.

## Après ce starter

Vous avez parcouru toute la progression files : du premier contact aux primitives.

[Bilan du niveau avancé](bilan.md)
