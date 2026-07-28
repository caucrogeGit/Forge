# Composer un message

Construire un `MailMessage` riche : destinataire, copie (`cc`), sujet, corps texte et corps HTML.
On inspecte les champs du message composé, sans l'envoyer.

??? note "Contrôleur"
    Créez le fichier `mvc/controllers/mail_message_controller.py` :

    ```python
    # mvc/controllers/mail_message_controller.py
    from core.http.request import Request
    from core.http.response import Response
    from forge_mvc_mail import MailMessage
    from core.mvc.controller.base_controller import BaseController


    class MailMessageController(BaseController):
        """Composer un MailMessage et inspecter ses champs, sans envoi."""

        @staticmethod
        def index(request: Request) -> Response:
            message = MailMessage(
                subject="Bienvenue sur Forge",
                to="alice@example.test",
                cc="equipe@example.test",
                body_text="Bonjour Alice, ceci est un message de démonstration.",
                body_html="<p>Bonjour Alice, ceci est un message de <strong>démonstration</strong>.</p>",
                from_email="noreply@example.test",
            )
            return BaseController.render(
                "mail_message/index.html",
                context={
                    "subject": message.subject,
                    "to": message.to,
                    "cc": message.cc,
                    "has_html": message.body_html is not None,
                },
                request=request,
            )
    ```

    | Champ | Rôle |
    |---|---|
    | `to` | Destinataire principal. |
    | `cc` | Destinataire en copie. |
    | `body_text` | Corps en texte brut. |
    | `body_html` | Corps en HTML, optionnel. |

??? note "Vue"
    Créez le fichier `mvc/views/mail_message/index.html` :

    ```html
    {% extends "layouts/app.html" %}
    {% block content %}
    <h1>Composer un message</h1>
    <p>Un <code>MailMessage</code> a été composé (sans envoi) :</p>
    <ul>
      <li>Sujet : {{ subject }}</li>
      <li>Destinataire : {{ to }}</li>
      <li>Copie : {{ cc }}</li>
      <li>Version HTML : {{ "oui" if has_html else "non" }}</li>
    </ul>
    {% endblock %}
    ```

??? note "Route"
    Dans `mvc/routes/__init__.py`, ajoutez l'import puis la route à l'intérieur du groupe public :

    ```python
    # mvc/routes/__init__.py
    from mvc.controllers.mail_message_controller import MailMessageController

    with router.group("", public=True) as public:
        public.add("GET", "/mail-message", MailMessageController.index, name="mail_message_index")
    ```

## À retenir
- Un `MailMessage` accepte un corps texte et un corps HTML.
- Les champs `to` et `cc` distinguent destinataire principal et copie.
- Composer un message ne l'envoie pas : l'envoi passe par un `Mailer`.

## Palier suivant
Vous faites le bilan du niveau débutant.

[Continuer avec le Bilan débutant](bilan.md)
