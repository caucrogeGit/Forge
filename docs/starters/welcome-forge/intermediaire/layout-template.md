# Héritage de gabarit

**Objectif**{ .intro-label } : factoriser l'enveloppe HTML commune (en-tête, pied, `<head>`) dans un **gabarit** partagé, au lieu de la répéter dans chaque page.

**Ce que vous allez apprendre :**{ .intro-label } une page peut **hériter** d'un gabarit avec `{% extends %}` et n'y injecter que son contenu via des `{% block %}`. C'est le principe DRY appliqué aux templates Jinja.

Le Carnet de notes a une page liste `note/index.html`, écrite comme un document HTML complet au palier précédent.

Nous allons en extraire l'enveloppe dans un gabarit, car les pages que nous ajouterons ensuite (édition, suppression) partageront la même structure.
Aucun changement de contrôleur ni de route à ce palier.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [Front et CSS](../../../features/front.md) | les layouts standards de Forge et l'usage des `{% block %}` |

??? note "Vues"
    Créez le gabarit `mvc/views/note/_layout.html` :

    ```html
    <!-- mvc/views/note/_layout.html -->
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="utf-8">
        <title>{% block title %}Carnet de notes{% endblock %}</title>
    </head>
    <body>
        <header><strong>Carnet de notes</strong></header>
        <main>
            {% block content %}{% endblock %}
        </main>
        <footer><small>Pied de page commun à toutes les pages.</small></footer>
    </body>
    </html>
    ```

    Puis remplacez le contenu de `mvc/views/note/index.html` par sa version héritée :

    ```html
    <!-- mvc/views/note/index.html -->
    {% extends "note/_layout.html" %}

    {% block title %}Mes notes{% endblock %}

    {% block content %}
    <h1>Mes notes</h1>

    {% if notes %}
    <ul>
        {% for note in notes %}
        <li>#{{ note.id }} : {{ note.content }}</li>
        {% endfor %}
    </ul>
    {% else %}
    <p>Aucune note en base.</p>
    {% endif %}
    {% endblock %}
    ```

    | Élément | Rôle |
    |---|---|
    | `{% extends "note/_layout.html" %}` | Déclare que la page **hérite** du gabarit ; elle n'écrit plus `<html>`, `<head>` ni `<body>`. |
    | `{% block X %}…{% endblock %}` | Chaque bloc de la page **remplit** le bloc de même nom déclaré dans le gabarit (`title`, `content`). |

    Le gabarit reste **un seul fichier** : modifier l'en-tête ou le pied le change pour toutes les pages qui en héritent.

??? note "Routes"
    Inchangé depuis le palier précédent : la factorisation ne touche que les vues.

    ```python
    # mvc/routes/__init__.py
    from core.http.router import Router
    from mvc.controllers.home_controller import HomeController
    from mvc.controllers.note_controller import NoteController

    router = Router()

    with router.group("", public=True) as public:
        public.add("GET", "/", HomeController.index, name="home-index")
        public.add("GET", "/note", NoteController.index, name="note-index")
    ```

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/note` | la liste, désormais entourée de l'en-tête et du pied du gabarit |

??? note "À retenir"
    - `{% extends %}` + `{% block %}` = factoriser l'enveloppe HTML.
    - Le gabarit définit la structure et des blocs ; la page remplit les blocs.
    - Une seule source pour l'en-tête et le pied, donc cohérence et maintenance simples.

Au palier suivant, nous ajoutons une recherche par mot-clé sur la liste.

[Continuer avec Rechercher / filtrer](filter-list.md)
