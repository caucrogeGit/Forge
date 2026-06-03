# Supprimer un enregistrement

Objectif : supprimer une ligne via une action **destructive sécurisée**.

**Ce que vous allez apprendre :** la dernière opération du CRUD — **supprimer**.
Une suppression ne se fait **jamais** par un simple lien `GET` : elle passe par
un **POST protégé par CSRF** et `core.database.db.execute("DELETE … WHERE id =
?")`.

Palier 6 du **niveau intermédiaire** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Modifier un enregistrement](update-record.md).

## Ce que ce starter montre

- une liste avec un **bouton supprimer** par ligne (mini-formulaire `POST`) ;
- le jeton **CSRF** sur chaque formulaire de suppression ;
- `execute("DELETE … WHERE id = ?")` **paramétré** ;
- après écriture, on **relit et on ré-affiche** la liste à jour.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | `request.route_param("id")`. | [Request](../../../reference/http.md#3-request-reference) |
| `Response` | Produite via `render(...)`. | [Response](../../../reference/http.md#4-response-reference) |
| `BaseController` | `render(...)` + `csrf_token(...)`. | [BaseController](../../../reference/api.md#coremvccontroller) |
| `core.database.db.execute` / `fetch_all` | Supprimer une ligne, relire la liste. | [Migrations SQL](../../../features/migrations.md) |

## Tester

```bash
forge migration:apply
forge run
```

Ouvrez `https://localhost:8000/delete-record`, cliquez **supprimer** sur une
ligne → elle disparaît de la liste.

## Le contrôleur

```python
# mvc/controllers/delete_record_controller.py
SELECT_ALL = "SELECT id, content FROM first_sql_messages ORDER BY id"
DELETE_ONE = "DELETE FROM first_sql_messages WHERE id = ?"


class DeleteRecordController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        messages = fetch_all(SELECT_ALL)
        return BaseController.render(
            "delete_record/index.html",
            context={"messages": messages, "csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def delete(request: Request) -> Response:
        record_id = int(request.route_param("id"))
        execute(DELETE_ONE, (record_id,))
        messages = fetch_all(SELECT_ALL)
        return BaseController.render(
            "delete_record/index.html",
            context={"messages": messages, "csrf_token": BaseController.csrf_token(request),
                     "deleted": True},
            request=request,
        )
```

### Comprendre ce code

- La suppression est un **POST** : une action qui modifie l'état n'est jamais
  un `GET` (un lien ou un robot ne doivent pas pouvoir supprimer).
- `execute(DELETE_ONE, (record_id,))` — l'`id` est un **paramètre lié**.
- Après l'écriture, on **relit** (`fetch_all`) et on ré-affiche la liste.

## La vue

```html
<!-- mvc/views/delete_record/index.html -->
{% for m in messages %}
<li>
  #{{ m.id }} — {{ m.content }}
  <form method="post" action="/delete-record/{{ m.id }}" style="display:inline">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button type="submit">supprimer</button>
  </form>
</li>
{% endfor %}
```

### Comprendre ce code

- Chaque ligne porte son **propre mini-formulaire** `POST` vers
  `/delete-record/{id}` avec le **jeton CSRF**.
- Pas de lien `GET` de suppression : on protège l'action destructive.

## À retenir

- Supprimer = `POST` + CSRF + `DELETE … WHERE id = ?` paramétré.
- Une action qui change l'état n'est **jamais** un `GET`.
- Après l'écriture, on relit la base pour ré-afficher l'état réel.

## Après ce starter

Passez au palier suivant : **Mémoriser un état en session** — garder un état
côté serveur entre les requêtes.

[Continuer avec Mémoriser un état en session](session-state.md)
