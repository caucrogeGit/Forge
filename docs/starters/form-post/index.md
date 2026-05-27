# Premier formulaire POST

Objectif : envoyer une valeur depuis un formulaire HTML et la lire
côté contrôleur.

Palier 6 de la
[progression officielle des starters](../index.md#progression-recommandee),
après [Inspecter une requête](../request-debug/index.md).

## Ce que ce starter montre

- une route `GET /form-post`
- une route `POST /form-post`
- une vue HTML avec un formulaire minimal
- une méthode de contrôleur qui lit la valeur envoyée
- une réponse texte avec `Response.text(...)`

Aucune base de données.
Aucune validation serveur avancée.
Aucun CRUD.

## Tester

Depuis le projet Forge déjà créé avec ce starter :

```bash
forge run
```

Ouvrez :

```
http://localhost:8000/form-post
```

Saisissez `Roger`, envoyez le formulaire.

Résultat attendu :

```
Bonjour Roger
```

## Code essentiel

```python
# mvc/controllers/form_post_controller.py
class FormPostController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "form_post/index.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )

    @staticmethod
    def submit(request: Request) -> Response:
        name = request.form("name", default="Forge")
        return Response.text(f"Bonjour {name}")
```

```html
<!-- mvc/views/form_post/index.html -->
<form method="post" action="/form-post">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <label for="name">Prénom</label>
  <input id="name" name="name" type="text" value="Forge">
  <button type="submit">Envoyer</button>
</form>
```

## À retenir

- `GET /form-post` affiche le formulaire.
- `POST /form-post` reçoit les données.
- Le contrôleur lit la valeur envoyée avec `request.form("name", ...)`.
- Le champ caché `csrf_token` est exigé par Forge sur toute requête
  POST (protection contre les soumissions cross-site). Il est
  généré par `BaseController.csrf_token(request)` et vérifié
  automatiquement par le middleware.
- La validation serveur complète viendra dans le starter suivant
  (palier 7).

## Après ce starter

Passez au palier suivant : **Validation serveur**.

Vous y apprendrez à refuser une valeur vide avec un statut HTTP
explicite :

```python
return Response.text("Le prénom est obligatoire", status=422)
```

[Continuer avec Validation serveur](../server-validation/index.md)
