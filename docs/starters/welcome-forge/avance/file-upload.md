# Téléverser un fichier

Objectif : recevoir un fichier envoyé par l'utilisateur, le **stocker** en toute
sécurité, et l'attacher à un article.

**Ce que vous allez apprendre :** un formulaire `multipart/form-data`, la
récupération du fichier avec `request.file(...)`, et son stockage par
`forge_mvc_files.save_upload`. Cette fonction **valide** le fichier (extension,
type MIME, taille) **avant** d'écrire sur le disque.

!!! info "Opt-in forge-mvc-files"
    Ce palier utilise le module opt-in `forge-mvc-files`. Installez-le dans le
    projet : `pip install --pre forge-mvc-files`.

## Là où nous en sommes

Le catalogue sait lister et créer des articles. Nous permettons d'**attacher un
document** à un article. Il faut d'abord ajouter une colonne `document_path` à la
table `articles` (migration incrémentale), puis recevoir et stocker le fichier.

## L'ajout

### La migration incrémentale

Créez une nouvelle migration `mvc/migrations/<timestamp>_add_document_path.sql` :

```sql
ALTER TABLE articles ADD COLUMN document_path VARCHAR(255) NULL;
```

Appliquez-la avec `forge migration:apply`.

### Le contrôleur

Complétez les imports et ajoutez les deux méthodes dans
`mvc/controllers/article_controller.py` :

```python
from core.database.db import execute, fetch_all, fetch_one
from forge_mvc_files import UploadError, save_upload

SELECT_ONE = "SELECT id, title FROM articles WHERE id = ?"
SET_DOCUMENT = "UPDATE articles SET document_path = ? WHERE id = ?"


class ArticleController(BaseController):

    # … index / create / store inchangés …

    @staticmethod
    def attach(request: Request) -> Response:
        article = fetch_one(SELECT_ONE, (int(request.route("id")),))
        if article is None:
            return Response.text("Article introuvable.", status=404)
        session_id, csrf_token = ArticleController._start_session(request)
        response = BaseController.render(
            "article/attach.html",
            request=request,
            context={"article": article, "csrf_token": csrf_token},
        )
        set_session_cookie(response, session_id)
        return response

    @staticmethod
    def attach_store(request: Request) -> Response:
        record_id = int(request.route("id"))
        uploaded = request.file("document")
        if uploaded is None:
            return Response.text("Aucun fichier sélectionné.", status=422)
        try:
            saved = save_upload(uploaded, "documents")
        except UploadError as exc:
            return Response.text(str(exc), status=422)
        execute(SET_DOCUMENT, (saved.path, record_id))
        return BaseController.redirect("/articles", request=request, flash="Document attaché.")
```

Créez la vue `mvc/views/article/attach.html` :

```html
<!-- mvc/views/article/attach.html -->
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><title>Attacher un document</title></head>
<body>
    <h1>Attacher un document à « {{ article.title }} »</h1>
    <form method="post" action="/articles/{{ article.id }}/attach" enctype="multipart/form-data">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input type="file" name="document" required>
        <button type="submit">Envoyer</button>
    </form>
    <p><a href="/articles">Retour au catalogue</a></p>
</body>
</html>
```

Ajoutez un lien « attacher » par article dans `mvc/views/article/index.html` :

```html
<li>#{{ a.id }} : {{ a.title }} <em>({{ a.category }})</em>
    <a href="/articles/{{ a.id }}/attach">attacher</a></li>
```

Puis déclarez les deux routes dans `mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.article_controller import ArticleController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET",  "/", HomeController.index, name="home_index")
    pub.add("GET",  "/articles", ArticleController.index, name="articles_index")
    pub.add("GET",  "/articles/new", ArticleController.create, name="articles_new")
    pub.add("POST", "/articles", ArticleController.store, name="articles_store")
    pub.add("GET",  "/articles/{id}/attach", ArticleController.attach, name="articles_attach")
    pub.add("POST", "/articles/{id}/attach", ArticleController.attach_store, name="articles_attach_store")
```

## Comprendre ce code

- `enctype="multipart/form-data"` est **obligatoire** pour transmettre un fichier ;
  sans lui, le navigateur n'envoie que le nom.
- `request.file("document")` renvoie un `UploadedFile` (ou `None` si rien n'a été
  envoyé), traité explicitement.
- `save_upload(uploaded, "documents")` **valide** extension, type MIME et taille,
  puis écrit le fichier ; en cas de refus elle lève une `UploadError`. On stocke
  ensuite le chemin (`saved.path`) dans `articles.document_path`.
- Le formulaire reste protégé par **CSRF**, comme tout POST.

## Tester dans le navigateur

| Action | Résultat |
|---|---|
| Attacher un fichier autorisé à un article | retour au catalogue, « Document attaché. » |
| Envoyer un type non autorisé | erreur `422` claire, rien n'est stocké |

## À retenir

- Un upload passe par un formulaire `multipart/form-data`.
- `request.file(...)` récupère le fichier ; `save_upload` le **valide** avant de
  l'écrire : jamais d'écriture aveugle.
- Forge contrôle extension, type MIME et taille par défaut : la sécurité d'abord.

Au palier suivant, nous exposons le catalogue en API JSON protégée.

[Continuer avec API JSON protégée](json-api.md)
