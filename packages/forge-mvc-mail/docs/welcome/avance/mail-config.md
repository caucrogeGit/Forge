# Configurer l'envoi

## Niveau avancé

Charger la configuration mail depuis l'environnement avec `MailConfig.from_env` et l'inspecter.
On lit le transport, l'hôte, le port et l'expéditeur.
Le mot de passe n'est jamais affiché, seule sa présence est indiquée.

??? note "Contrôleur"
    Créez le fichier `mvc/controllers/mail_config_controller.py` :

    ```python
    # mvc/controllers/mail_config_controller.py
    from core.http.request import Request
    from core.http.response import Response
    from forge_mvc_mail import MailConfig
    from core.mvc.controller.base_controller import BaseController


    class MailConfigController(BaseController):
        """Charger et inspecter la configuration mail, mot de passe masqué."""

        @staticmethod
        def index(request: Request) -> Response:
            context = {}
            try:
                cfg = MailConfig.from_env()
                context.update({
                    "enabled": cfg.enabled,
                    "transport": cfg.transport_name,
                    "host": cfg.host or "(non défini)",
                    "port": cfg.port,
                    "from_email": cfg.from_email or "(non défini)",
                    "password_set": bool(cfg.password),
                })
            except Exception as exc:
                context["error"] = str(exc)
            return BaseController.render(
                "mail_config/index.html", context=context, request=request
            )
    ```

    | Élément | Rôle |
    |---|---|
    | `MailConfig.from_env()` | Charge la configuration mail depuis l'environnement. |
    | `cfg.transport_name` | Nom du transport configuré. |
    | `bool(cfg.password)` | Présence d'un mot de passe, sans l'exposer. |

??? note "Vue"
    Créez le fichier `mvc/views/mail_config/index.html` :

    ```html
    {# mvc/views/mail_config/index.html #}
    {% extends "layouts/base.html" %}
    {% block content %}
    <h1>Configurer l'envoi</h1>
    {% if error %}
    <p>Configuration indisponible : {{ error }}</p>
    {% else %}
    <ul>
      <li>Active : {{ enabled }}</li>
      <li>Transport : {{ transport }}</li>
      <li>Hôte : {{ host }}</li>
      <li>Port : {{ port }}</li>
      <li>Expéditeur : {{ from_email }}</li>
      <li>Mot de passe défini : {{ password_set }}</li>
    </ul>
    {% endif %}
    {% endblock %}
    ```

??? note "Route"
    Dans `mvc/routes/__init__.py`, ajoutez l'import puis la route à l'intérieur du groupe public :

    ```python
    # mvc/routes/__init__.py
    from mvc.controllers.mail_config_controller import MailConfigController

    with router.group("", public=True) as public:
        public.add("GET", "/mail-config", MailConfigController.index, name="mail_config_index")
    ```

## À retenir
- La configuration mail se charge depuis l'environnement, jamais en dur.
- Un secret comme le mot de passe ne s'affiche pas : on montre seulement sa présence.
- `MailConfig.from_env` centralise la lecture de la configuration.

## Palier suivant
Vous allez exposer un diagnostic du module mail en JSON.

[Continuer avec Diagnostiquer le module Mail](mail-doctor.md)
