# Bonjour Forge i18n

Objectif : premier contact avec le module **opt-in** `forge-mvc-i18n`.

**Ce que vous allez apprendre :** l'internationalisation de Forge repose sur des
**catalogues JSON** (un fichier par locale) et un helper `trans(clé, locale)`.
Sans catalogue ni module, le noyau dégrade en **no-op** : `trans` retourne la
clé. Avec l'opt-in et un catalogue, `trans` retourne la traduction.

Premier palier du **niveau débutant** de la progression i18n
(vue d'ensemble des starters).

!!! note "Module opt-in : repli no-op"
    Si `forge-mvc-i18n` n'est pas installé, `trans("welcome.title")` renvoie
    `"welcome.title"`. L'application ne casse jamais ; elle n'est simplement pas
    traduite.

## Ce que ce starter montre

- créer un premier catalogue `translations/fr.json` ;
- traduire une clé avec `trans(clé, locale="fr")` dans une route.

## Classes Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `forge_mvc_i18n.trans(key, locale)` | Retourne la traduction d'une clé pour une locale. | Opt-ins |

## 1. Créer le catalogue français

```json
// translations/fr.json
{
  "welcome.title": "Bonjour Forge i18n"
}
```

## 2. Le contrôleur

```python
# mvc/controllers/i18n_welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_i18n import trans


class I18nWelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        titre = trans("welcome.title", locale="fr")
        return Response.text(titre)
```

### Comprendre ce code

- `trans("welcome.title", locale="fr")` lit `translations/fr.json` et retourne
  `"Bonjour Forge i18n"`.
- Le catalogue est un simple objet JSON `clé → texte` : rien de magique, le
  stockage est visible et éditable.
- Sans le module opt-in, la même ligne renverrait `"welcome.title"` (repli no-op).

## La route

```python
# mvc/routes.py
from mvc.controllers.i18n_welcome_controller import I18nWelcomeController

with router.group("", public=True) as public:
    public.add("GET", "/i18n-welcome", I18nWelcomeController.index, name="i18n_welcome_index")
```

## À retenir

- L'i18n Forge = catalogues JSON + helper `trans(clé, locale)`.
- Sans module ni catalogue, `trans` dégrade en no-op (retourne la clé).
- Le catalogue est un simple `clé → texte`, à SQL/stockage visible.

## Après ce starter

Premier mot traduit. Voyons la structure d'un **catalogue** avec deux langues.

[Écrire un catalogue](i18n-catalog.md)
