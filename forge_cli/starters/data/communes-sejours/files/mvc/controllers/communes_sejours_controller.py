from core.i18n import trans
from core.mail import Mailer
from core.mail.templates import MailTemplateRenderer
from core.mvc.controller import BaseController
from mvc.forms.demande_sejour_form import DemandeSejourForm

_GESTIONNAIRE_EMAIL = "contact@example.test"

_HEBERGEMENTS = [
    {
        "slug": "mas-des-cigales",
        "titre": "Mas des Cigales",
        "commune": "Saint-Rémy-de-Provence",
        "capacite": 6,
        "description": "Mas provençal au calme, jardin ombragé et piscine.",
        "adresse": "Route de Maillane, 13210 Saint-Rémy-de-Provence",
        "proprietaire": "Marie Dupont",
        "is_published": True,
    },
    {
        "slug": "gite-du-luberon",
        "titre": "Gîte du Luberon",
        "commune": "Apt",
        "capacite": 4,
        "description": "Gîte en pierre au cœur du Luberon, à deux pas des sentiers de randonnée.",
        "adresse": "Chemin des Ocres, 84400 Apt",
        "proprietaire": "Jean Martin",
        "is_published": True,
    },
    {
        "slug": "chambre-hotes-camargue",
        "titre": "Chambre d'hôtes Camargue",
        "commune": "Saintes-Maries-de-la-Mer",
        "capacite": 2,
        "description": "Chambre d'hôtes au bord des étangs, idéale pour observer les flamants roses.",
        "adresse": "Lieu-dit Les Salins, 13460 Saintes-Maries-de-la-Mer",
        "proprietaire": "Sophie Blanc",
        "is_published": True,
    },
]


def _find_hebergement(slug):
    return next((h for h in _HEBERGEMENTS if h["slug"] == slug), None)


def send_demande_sejour_notifications(
    hebergement: dict,
    form_data: dict,
    *,
    mailer: Mailer | None = None,
    renderer: MailTemplateRenderer | None = None,
) -> None:
    """Envoie les notifications mail suite à une demande de séjour valide.

    Paramètres injectables pour les tests (mailer, renderer).
    En production, utilise Mailer.from_config() et le dossier mail_templates_dir.
    """
    if mailer is None:
        mailer = Mailer.from_config()
    if renderer is None:
        renderer = MailTemplateRenderer()

    context = {
        "nom": form_data.get("nom", ""),
        "email": form_data.get("email", ""),
        "telephone": form_data.get("telephone") or "",
        "date_arrivee": str(form_data.get("date_arrivee", "")),
        "date_depart": str(form_data.get("date_depart", "")),
        "nombre_personnes": form_data.get("nombre_personnes", ""),
        "message": form_data.get("message") or "",
        "hebergement_titre": hebergement["titre"],
        "hebergement_commune": hebergement["commune"],
        "trans": trans,
    }

    msg_visiteur = renderer.render(
        "communes_sejours/demande_visiteur",
        context,
        to=form_data["email"],
    )
    mailer.send(msg_visiteur, message_type="demande_visiteur", related_entity="hebergement")

    msg_proprietaire = renderer.render(
        "communes_sejours/demande_proprietaire",
        context,
        to=_GESTIONNAIRE_EMAIL,
        reply_to=form_data["email"],
    )
    mailer.send(msg_proprietaire, message_type="demande_proprietaire", related_entity="hebergement")


class CommunesSejoursController:
    @staticmethod
    def index(request):
        return BaseController.render(
            "public/communes_sejours/home.html",
            context={},
            request=request,
        )

    @staticmethod
    def hebergements_index(request):
        return BaseController.render(
            "public/communes_sejours/hebergements_index.html",
            context={"hebergements": _HEBERGEMENTS},
            request=request,
        )

    @staticmethod
    def hebergements_show(request):
        slug = request.route_params.get("slug")
        hebergement = _find_hebergement(slug)
        if hebergement is None:
            return BaseController.not_found()
        return BaseController.render(
            "public/communes_sejours/hebergements_show.html",
            context={"hebergement": hebergement, "form": DemandeSejourForm()},
            request=request,
        )

    @staticmethod
    def hebergements_demande(request):
        slug = request.route_params.get("slug")
        hebergement = _find_hebergement(slug)
        if hebergement is None:
            return BaseController.not_found()
        form = DemandeSejourForm.from_request(request)
        if not form.is_valid():
            return BaseController.validation_error(
                "public/communes_sejours/hebergements_show.html",
                context={"hebergement": hebergement, "form": form},
                request=request,
            )
        send_demande_sejour_notifications(hebergement, form.cleaned_data)
        return BaseController.redirect_with_flash(
            request,
            f"/communes-sejours/hebergements/{slug}",
            trans("starter.cs.request.sent"),
        )
