# Préambule : le système de design du projet

**Objectif** : apprendre, palier après palier, à utiliser le système de design livré par `forge new`, dans une **vraie page servie par une route et un contrôleur** qui passe des données.

**Ce que vous allez apprendre :** où vit la charte, comment composer une page avec les composants, et comment un contrôleur passe ses données aux composants (liste, recherche, pagination, validation, flash).

!!! info "Le fil rouge du parcours"
    Comme les autres progressions `welcome-*`, ce parcours suit un **fil rouge** unique : un mini-écran d'annuaire `showcase`, servi par un vrai contrôleur, qui grandit à chaque palier jusqu'à une page complète (en-tête, cartes, formulaire validé, tableau paginé, modale).

## Ce que le squelette fournit déjà

| Emplacement | Rôle |
|---|---|
| `static/src/input.css` | la charte graphique (bloc `@theme` Tailwind v4) |
| `mvc/views/layouts/base.html` | le gabarit partagé qui applique la charte |
| `mvc/views/components/` | la bibliothèque de composants (macros Jinja) |

Deux références à garder sous la main : la [Charte graphique](charte-graphique.md) (palette, typographie, usages) et le [Récapitulatif des composants](recapitulatif.md).

## Le confort : le mode watch

Ouvrez un second terminal :

```bash
npm run watch:css
```

Tailwind reconstruit `static/tailwind.css` à chaque sauvegarde.
Rafraîchissez le navigateur (`Ctrl+Shift+R` si le CSS semble en cache).

## Le contrôleur et ses données

Si les notions de route et de contrôleur sont nouvelles, faites d'abord le [Parcours Welcome Forge](../welcome-forge/index.md).

Créez `mvc/controllers/showcase_controller.py`.
Pour rester concentré sur le design, les données vivent **en mémoire** (une vraie application utiliserait la base, voir Welcome Forge) :

```python
# mvc/controllers/showcase_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.session import get_flash, get_session_id

_CONTACTS = [
    {"nom": "Ada Lovelace",  "email": "ada@exemple.fr",   "academie": "Paris", "statut": "actif"},
    {"nom": "Alan Turing",   "email": "alan@exemple.fr",  "academie": "Lyon",  "statut": "actif"},
    {"nom": "Grace Hopper",  "email": "grace@exemple.fr", "academie": "Lille", "statut": "actif"},
    {"nom": "Katherine Johnson", "email": "kj@exemple.fr", "academie": "Paris", "statut": "archive"},
]


class ShowcaseController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        flash = get_flash(get_session_id(request))
        return BaseController.render(
            "showcase/index.html",
            request=request,
            context={"contacts": _CONTACTS, "total": len(_CONTACTS), "flash": flash},
        )
```

Déclarez la route dans `mvc/routes/__init__.py` (groupe public) :

```python
public.add("GET", "/showcase", ShowcaseController.index, name="showcase-index")
```

Créez la vue `mvc/views/showcase/index.html` :

```jinja
{% extends "layouts/base.html" %}
{% block title %}Annuaire · {{ app_name }}{% endblock %}
{% block content %}
  <p class="text-muted">{{ total }} contacts dans l'annuaire.</p>
{% endblock %}
```

Ouvrez `https://localhost:8000/showcase` : le contrôleur passe `total`, la vue l'affiche, et la charte habille déjà la page.
Les paliers vont enrichir cette boucle contrôleur, données, composants.

## Les trois niveaux

| Niveau | Vous construisez | Composants découverts |
|---|---|---|
| [Débutant](debutant/charte.md) | l'habillage de la page | charte, gabarit, `page_header`, `navbar`, `breadcrumb` |
| [Intermédiaire](intermediaire/cartes.md) | le contenu | `card`, `badge`, `stat`, formulaire et validation |
| [Avancé](avance/tableaux.md) | données et interactivité | `table`, `pagination`, `modal`, `accordion`, `dropdown` |

[Commencer le niveau débutant](debutant/charte.md)
