# Modifier un enregistrement

Objectif : éditer une ligne existante via un formulaire pré-rempli.

**Ce que vous allez apprendre :** après *créer* (insert) et *lire*, on complète
le CRUD avec **modifier**. Le formulaire est chargé avec la valeur courante
(`fetch_one`), puis l'enregistrement passe par `core.database.db.execute("UPDATE
… WHERE id = ?")`, en POST **protégé par CSRF**.

Palier 5 du **niveau intermédiaire** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Héritage de gabarit](layout-template.md).

## Ce que ce starter montre

- trois routes : liste, formulaire pré-rempli (`/update-record/{id}/edit`),
  POST de mise à jour (`/update-record/{id}`) ;
- un formulaire **pré-rempli** avec la valeur courante ;
- `execute("UPDATE … SET content = ? WHERE id = ?")` **paramétré** ;
- après écriture, on **relit et on ré-affiche** (pas de redirection ici ; dans
  une vraie app, on ferait un *POST-Redirect-GET*).

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | `request.route_param("id")`, `request.form("content")`. | [Request](../../../reference/http.md#3-request-reference) |
| `Response` | `render(...)`, ou `Response.text(..., status=404/422)`. | [Response](../../../reference/http.md#4-response-reference) |
| `BaseController` | `render(...)` + `csrf_token(...)`. | [BaseController](../../../reference/api.md#coremvccontroller) |
| `core.database.db.execute` / `fetch_one` | Modifier une ligne, recharger la valeur. | [Migrations SQL](../../../features/migrations.md) |

## Tester

```bash
forge migration:apply
forge run
```

Ouvrez `https://localhost:8000/update-record`, cliquez **éditer**, changez le
texte, **Enregistrer** → le message est modifié et ré-affiché.

## Le contrôleur

```python
# mvc/controllers/update_record_controller.py
SELECT_ONE = "SELECT id, content FROM first_sql_messages WHERE id = ?"
UPDATE_ONE = "UPDATE first_sql_messages SET content = ? WHERE id = ?"


class UpdateRecordController(BaseController):

    @staticmethod
    def edit(request: Request) -> Response:
        record_id = int(request.route_param("id"))
        message = fetch_one(SELECT_ONE, (record_id,))
        if message is None:
            return Response.text("Enregistrement introuvable.", status=404)
        return BaseController.render(
            "update_record/edit.html",
            context={"message": message, "csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def update(request: Request) -> Response:
        record_id = int(request.route_param("id"))
        content = request.form("content", default="").strip()
        if not content:
            return Response.text("Le contenu est obligatoire.", status=422)
        execute(UPDATE_ONE, (content, record_id))
        message = fetch_one(SELECT_ONE, (record_id,))
        return BaseController.render(
            "update_record/edit.html",
            context={"message": message, "csrf_token": BaseController.csrf_token(request),
                     "updated": True},
            request=request,
        )
```

### Comprendre ce code

- `edit` **pré-remplit** le formulaire : on lit la valeur courante avec
  `fetch_one` avant d'afficher le champ.
- `update` valide d'abord (refus `422` si vide), puis `execute(UPDATE_ONE, …)` :
  l'`id` et le contenu sont des **paramètres liés**.
- Après l'écriture, on **relit** (`fetch_one`) et on ré-affiche la valeur à jour.

## La vue d'édition

```html
<!-- mvc/views/update_record/edit.html -->
{% if updated %}<p><strong>Message mis à jour.</strong></p>{% endif %}

<form method="post" action="/update-record/{{ message.id }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <input type="text" name="content" value="{{ message.content }}">
  <button type="submit">Enregistrer</button>
</form>
```

### Comprendre ce code

- Le `<form>` est en `method="post"` et embarque le **jeton CSRF** : toute
  écriture est protégée.
- `value="{{ message.content }}"` réaffiche la valeur courante : c'est le
  **pré-remplissage**.

## À retenir

- Modifier = pré-remplir (`fetch_one`) + `UPDATE … WHERE id = ?` paramétré.
- L'`id` vient de la **route** (`request.route_param("id")`).
- Toute écriture est en `POST` **avec CSRF**.

## Après ce starter

Passez au palier suivant : **Supprimer un enregistrement**, l'action
destructive sécurisée par CSRF.

[Continuer avec Supprimer un enregistrement](delete-record.md)
