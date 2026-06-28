# Préambule : le système de design du projet

**Objectif** : apprendre, palier après palier, à utiliser le système de design
livré par `forge new` : une charte graphique centralisée et une bibliothèque de
composants réutilisables.

**Ce que vous allez apprendre :** où vit la charte, comment la personnaliser en
un seul endroit, et comment composer une vraie page avec les composants
(boutons, cartes, formulaires, tableaux, modale...), du plus simple au plus
riche.

!!! info "Le fil rouge du parcours"
    Comme les autres progressions `welcome-*`, ce parcours suit un **fil rouge**
    unique : une page de démonstration `showcase` qui grandit à chaque palier.
    Elle part d'une page vide et devient un petit écran d'annuaire complet :
    en-tête, cartes, formulaire validé, tableau paginé, modale de confirmation.

## Ce que le squelette fournit déjà

Un projet créé par `forge new` contient le système de design :

| Emplacement | Rôle |
|---|---|
| `static/src/input.css` | la charte graphique (bloc `@theme` Tailwind v4) |
| `mvc/views/layouts/base.html` | le gabarit partagé qui applique la charte |
| `mvc/views/components/` | la bibliothèque de composants (macros Jinja) |

## Le confort : le mode watch

Ouvrez un second terminal et lancez Tailwind en surveillance :

```bash
npm run watch:css
```

Il reconstruit `static/tailwind.css` à chaque sauvegarde d'un template ou de la
charte. Rafraîchissez le navigateur (`Ctrl+Shift+R` si le CSS semble en cache).

## Mettre en place la page du fil rouge

Si les notions de route et de contrôleur sont nouvelles, faites d'abord le
[Parcours Welcome Forge](../welcome-forge/index.md).

Créez un contrôleur `mvc/controllers/showcase_controller.py` :

```python
# mvc/controllers/showcase_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class ShowcaseController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render("showcase/index.html", request=request)
```

Déclarez la route dans `mvc/routes.py` (groupe public) :

```python
public.add("GET", "/showcase", ShowcaseController.index, name="showcase-index")
```

Créez la vue `mvc/views/showcase/index.html`, qui étend le gabarit :

```jinja
{% extends "layouts/base.html" %}
{% block title %}Annuaire · {{ app_name }}{% endblock %}
{% block content %}
<p class="text-muted">Notre page de démonstration grandira ici.</p>
{% endblock %}
```

Ouvrez `https://localhost:8000/showcase` : une page vide, déjà habillée par la
charte (fond crème, police Figtree). Les paliers vont la remplir.

## Les trois niveaux

| Niveau | Vous construisez | Composants découverts |
|---|---|---|
| [Débutant](debutant/charte.md) | l'habillage de la page | charte, gabarit, `page_header`, `navbar`, `breadcrumb` |
| [Intermédiaire](intermediaire/cartes.md) | le contenu | `button`, `card`, `badge`, `stat`, `alert`, formulaires et validation |
| [Avancé](avance/tableaux.md) | données et interactivité | `table`, `pagination`, `empty_state`, `modal`, `accordion`, `dropdown` |

[Commencer le niveau débutant](debutant/charte.md)
