# Traduire une clé

Objectif : rendre la bonne langue selon la locale demandée.

**Ce que vous allez apprendre :** `trans(clé, locale)` choisit le catalogue de la locale et retourne la valeur de la clé.
En passant la locale depuis la requête, une même route sert la page en FR ou en EN.

!!! note "Module opt-in"
    La locale ne sert qu'à choisir un fichier `<locale>.json` : elle est validée (caractères de chemin interdits, vu au niveau avancé).

## Classes Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `trans(key, locale)` | Traduit une clé pour une locale donnée. | Opt-ins |

## Le contrôleur

```python
# mvc/controllers/i18n_trans_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_i18n import trans


class I18nTransController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        # ?lang=fr ou ?lang=en (fr par défaut)
        locale = request.query("lang", default="fr")
        return Response.json({
            "locale": locale,
            "title": trans("welcome.title", locale=locale),
            "greeting": trans("welcome.greeting", locale=locale),
        })
```

### Comprendre ce code

- `trans("welcome.title", locale="en")` lit `translations/en.json` et renvoie `"Hello Forge i18n"` ; avec `locale="fr"`, `"Welcome i18n"`.
- Une **seule** route sert les deux langues : c'est le catalogue qui varie, pas le code.
- La locale vient de l'utilisateur (`?lang=`), mais elle ne désigne qu'un fichier catalogue, jamais un chemin arbitraire.

## Tester

```bash
forge run
```

Ouvrez `/i18n-trans?lang=fr` puis `/i18n-trans?lang=en`.

## La route

```python
# mvc/routes/__init__.py
from mvc.controllers.i18n_trans_controller import I18nTransController

with router.group("", public=True) as public:
    public.add("GET", "/i18n-trans", I18nTransController.index, name="i18n_trans_index")
```

## À retenir

- `trans(clé, locale)` choisit le catalogue et retourne la traduction.
- Une route, deux langues : seul le catalogue change.
- La locale ne désigne qu'un fichier `<locale>.json`.

## Après ce starter

Vous traduisez à la demande.
Faisons le **bilan** du niveau débutant.

[Bilan du niveau débutant](bilan.md)
