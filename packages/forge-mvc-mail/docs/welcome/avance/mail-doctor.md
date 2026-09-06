# Diagnostiquer le module Mail

Exposer des contrôles non invasifs en JSON.
On vérifie si la configuration se charge, quel transport est utilisé et si l'envoi est activé.
Utile pour valider un déploiement sans envoyer le moindre email.

??? note "Contrôleur"
    Créez le fichier `mvc/controllers/mail_doctor_controller.py` :

    ```python
    # mvc/controllers/mail_doctor_controller.py
    from core.http.request import Request
    from core.http.response import Response
    from forge_mvc_mail import MailConfig
    from core.mvc.controller.base_controller import BaseController


    class MailDoctorController(BaseController):
        """Diagnostic non invasif du module mail, exposé en JSON."""

        @staticmethod
        def index(request: Request) -> Response:
            checks: dict = {}
            try:
                cfg = MailConfig.from_env()
                checks["config_loaded"] = True
                checks["enabled"] = cfg.enabled
                checks["transport"] = cfg.transport_name
                checks["from_email_set"] = bool(cfg.from_email)
            except Exception as exc:
                checks["config_loaded"] = False
                checks["error"] = str(exc)
            return Response.json(checks)
    ```

    | Élément | Rôle |
    |---|---|
    | `Response.json(...)` | Renvoie un corps JSON, sans vue HTML. |
    | `config_loaded` | Indique si la configuration s'est chargée. |
    | `from_email_set` | Présence d'un expéditeur, sans l'exposer. |

    Ce palier ne nécessite aucune vue : l'action retourne directement du JSON.

??? note "Route"
    Dans `mvc/routes/__init__.py`, ajoutez l'import puis la route à l'intérieur du groupe public :

    ```python
    # mvc/routes/__init__.py
    from mvc.controllers.mail_doctor_controller import MailDoctorController

    with router.group("", public=True) as public:
        public.add("GET", "/mail-doctor", MailDoctorController.index, name="mail_doctor_index")
    ```

## À retenir
- Un diagnostic reste non invasif : il n'envoie aucun email.
- `Response.json(...)` renvoie des données structurées, pratiques pour une sonde.
- Un contrôleur n'a pas toujours besoin d'une vue.

## Palier suivant
Reste à sortir l'envoi du chemin de la requête.

[Suivant : envoyer en file d'attente](mail-file.md)
