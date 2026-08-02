# Rendre un template

Produire un email à partir d'un template Jinja avec `MailTemplateRenderer`.
Un template `welcome.txt` et un contexte donnent un `MailMessage` prêt à envoyer.
La page dégrade proprement si le template est absent.

??? note "Template"
    Créez le fichier `mail_templates/welcome.txt` à la racine du projet :

    ```text
    Sujet: Bienvenue {{ name }}

    Bonjour {{ name }}, bienvenue sur Forge.
    ```

    La première ligne `Sujet:` devient le sujet du message, le reste devient le corps texte.

??? note "Contrôleur"
    Créez le fichier `mvc/controllers/mail_template_controller.py` :

    ```python
    # mvc/controllers/mail_template_controller.py
    from core.http.request import Request
    from core.http.response import Response
    from forge_mvc_mail import MailTemplateError, MailTemplateRenderer
    from core.mvc.controller.base_controller import BaseController


    class MailTemplateController(BaseController):
        """Rendre un email depuis un template Jinja via MailTemplateRenderer."""

        @staticmethod
        def index(request: Request) -> Response:
            context = {}
            try:
                renderer = MailTemplateRenderer("mail_templates")
                message = renderer.render(
                    "welcome.txt",
                    {"name": "Alice"},
                    to="alice@example.test",
                )
                context["subject"] = message.subject
                context["body"] = message.body_text
            except MailTemplateError as exc:
                context["error"] = str(exc)
            return BaseController.render(
                "mail_template/index.html", context=context, request=request
            )
    ```

    | Élément | Rôle |
    |---|---|
    | `MailTemplateRenderer("mail_templates")` | Charge les templates depuis le dossier `mail_templates`. |
    | `renderer.render("welcome.txt", {...}, to=...)` | Rend le template avec son contexte et retourne un `MailMessage`. |
    | `MailTemplateError` | Erreur levée si le template est introuvable ou invalide. |

??? note "Vue"
    Créez le fichier `mvc/views/mail_template/index.html` :

    ```html
    {# mvc/views/mail_template/index.html #}
    {% extends "layouts/base.html" %}
    {% block content %}
    <h1>Rendre un template</h1>
    {% if error %}
    <p>Template introuvable : {{ error }}</p>
    <p>Vérifiez que <code>mail_templates/welcome.txt</code> existe à la racine du projet.</p>
    {% else %}
    <p>Email rendu depuis le template <code>mail_templates/welcome.txt</code> :</p>
    <ul>
      <li>Sujet : {{ subject }}</li>
      <li>Corps : {{ body }}</li>
    </ul>
    {% endif %}
    {% endblock %}
    ```

??? note "Route"
    Dans `mvc/routes/__init__.py`, ajoutez l'import puis la route à l'intérieur du groupe public :

    ```python
    # mvc/routes/__init__.py
    from mvc.controllers.mail_template_controller import MailTemplateController

    with router.group("", public=True) as public:
        public.add("GET", "/mail-template", MailTemplateController.index, name="mail_template_index")
    ```

## À retenir
- Un template d'email est un fichier texte Jinja dans `mail_templates`.
- La ligne `Sujet:` du template fixe le sujet du message.
- `MailTemplateRenderer.render` retourne un `MailMessage` prêt à envoyer.

## Palier suivant
Vous faites le bilan du niveau intermédiaire.

[Continuer avec le Bilan intermédiaire](bilan.md)
