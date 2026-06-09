# Paginer une liste

Objectif : n'afficher qu'une **tranche** des lignes à la fois, avec une
navigation page par page, en conservant la recherche du palier précédent.

**Ce que vous allez apprendre :** lire un numéro de page avec `request.query`, le
traduire en `LIMIT ? OFFSET ?` **paramétré**, et utiliser un `COUNT(*)` pour
savoir s'il existe une page suivante.

## Là où nous en sommes

`NoteController.index` lit la liste, filtrée par `q` quand il est présent. Nous
allons le faire évoluer pour qu'il combine ce filtre avec une **pagination** : la
même page liste lit aussi un numéro de page et n'affiche qu'une tranche. La route
`/note` ne change toujours pas.

## L'ajout

Faites évoluer `mvc/controllers/note_controller.py`. On construit la clause
`WHERE` une seule fois et on l'applique au `COUNT(*)` comme au `SELECT` paginé :

```python
from core.database.db import fetch_all, fetch_one

PAGE_SIZE = 5
SELECT_BASE = "SELECT id, content FROM notes"
COUNT_BASE = "SELECT COUNT(*) AS total FROM notes"
WHERE_FILTER = " WHERE content LIKE ?"


def _page_number(raw: str) -> int:
    try:
        page = int(raw)
    except (TypeError, ValueError):
        return 1
    return page if page >= 1 else 1


class NoteController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        q = request.query("q", default="").strip()
        page = _page_number(request.query("page", default="1"))
        where = WHERE_FILTER if q else ""
        params = (f"%{q}%",) if q else ()
        total = fetch_one(COUNT_BASE + where, params)["total"]
        offset = (page - 1) * PAGE_SIZE
        notes = fetch_all(
            SELECT_BASE + where + " ORDER BY id LIMIT ? OFFSET ?",
            params + (PAGE_SIZE, offset),
        )
        return BaseController.render(
            "note/index.html",
            request=request,
            context={
                "notes": notes,
                "q": q,
                "page": page,
                "has_prev": page > 1,
                "has_next": page * PAGE_SIZE < total,
            },
        )
```

Ajoutez la navigation sous la liste, dans le bloc `content` de
`mvc/views/note/index.html` :

```html
<nav>
    {% if has_prev %}<a href="/note?q={{ q }}&page={{ page - 1 }}">← Précédent</a>{% endif %}
    {% if has_next %}<a href="/note?q={{ q }}&page={{ page + 1 }}">Suivant →</a>{% endif %}
</nav>
```

## Votre mvc/routes.py à ce stade

Inchangé : la pagination passe par la *query string* `?page=N` sur `/note`.

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.note_controller import NoteController

router = Router()

with router.group("", public=True) as public:
    public.add("GET", "/", HomeController.index, name="home-index")
    public.add("GET", "/note", NoteController.index, name="note-index")
```

## Comprendre ce code

- `LIMIT ? OFFSET ?` sont **paramétrés** : la taille de page et l'offset sont des
  valeurs liées, jamais concaténées. Seule la clause statique `WHERE_FILTER` est
  concaténée, jamais une valeur saisie.
- `offset = (page - 1) * PAGE_SIZE` : la page 1 commence à 0, la page 2 à
  `PAGE_SIZE`, etc.
- `COUNT(*)` (avec le même `WHERE`) donne le total filtré ; `has_next` dit s'il
  reste des lignes après la page courante.
- Les liens conservent `q` pour que la recherche survive au changement de page.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/note` | la première tranche + un lien Suivant si besoin |
| `?page=2` | la tranche suivante |

## À retenir

- Paginer, c'est `LIMIT`/`OFFSET` paramétrés plus un `COUNT(*)` pour les bornes.
- L'offset se calcule depuis le numéro de page : `(page - 1) * taille`.
- Toujours blinder la conversion d'un paramètre d'URL en entier.

Au palier suivant, nous ajoutons l'édition d'une note via un formulaire pré-rempli.

[Continuer avec Modifier un enregistrement](update-record.md)
