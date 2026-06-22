# Le gestionnaire de gabarits dans Forge

Ce document décrit le moteur de rendu de gabarits.

Le fichier de code correspondant est `core/templating/manager.py`.

## 1. À quoi sert ce module ?

Forge rend ses vues avec Jinja2.
Ce module fournit le `TemplateManager` qui charge et rend les gabarits, et une instance partagée `template_manager`.

## 2. L'API

| Élément | Rôle |
|---|---|
| `TemplateManager()` | moteur de rendu : charge le dossier de vues et rend un gabarit |
| `template_manager` | instance partagée prête à l'emploi |

Le rendu est généralement appelé via `BaseController.render(...)` plutôt que directement.

## 3. Contextes d'utilisation

- **Vue** : `BaseController.render("page.html", context=...)` s'appuie sur ce gestionnaire.
- **Rendu direct** : `template_manager` pour un rendu hors contrôleur.

## 4. Voir aussi

- [Le contrat de rendu](contracts.md) : l'interface `Renderer`.
- [Les erreurs de gabarit](errors.md) : `TemplateNotFoundError`.
