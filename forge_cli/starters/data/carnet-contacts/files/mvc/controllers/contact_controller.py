from core.mvc.controller import BaseController
from mvc.forms.contact_form import ContactForm
from mvc.models.contact_model import (
    add_contact,
    delete_contact,
    get_contact_by_id,
    get_contacts,
    update_contact,
)
from mvc.models.ville_model import get_villes


def _ville_choices(villes: list[dict]) -> list[tuple[int, str]]:
    return [
        (
            ville["VilleId"],
            f"{ville['Nom']} ({ville['CodePostal']})" if ville.get("CodePostal") else ville["Nom"],
        )
        for ville in villes
    ]


def _form_data_from_contact(contact: dict) -> dict:
    return {
        "nom": contact.get("Nom"),
        "prenom": contact.get("Prenom"),
        "email": contact.get("Email"),
        "telephone": contact.get("Telephone"),
        "ville_id": contact.get("VilleId") or "",
    }


def _form_context(request, form, *, action: str, titre: str) -> dict:
    villes = get_villes()
    return {
        "form": form,
        "action": action,
        "titre": titre,
        "villes": villes,
        "ville_choices": _ville_choices(villes),
        "csrf_token": BaseController.csrf_token(request),
    }


class ContactController(BaseController):
    @staticmethod
    def index(request):
        contacts = get_contacts()
        return BaseController.render(
            "contact/index.html",
            context={"contacts": contacts},
            request=request,
        )

    @staticmethod
    def new(request):
        form = ContactForm()
        return BaseController.render(
            "contact/form.html",
            context=_form_context(request, form, action="/contacts", titre="Nouveau contact"),
            request=request,
        )

    @staticmethod
    def create(request):
        villes = get_villes()
        form = ContactForm.from_request(request, ville_choices=_ville_choices(villes))
        if not form.is_valid():
            return BaseController.validation_error(
                "contact/form.html",
                context={
                    "form": form,
                    "action": "/contacts",
                    "titre": "Nouveau contact",
                    "villes": villes,
                    "ville_choices": _ville_choices(villes),
                },
                request=request,
            )

        contact_id = add_contact(form.cleaned_data)
        return BaseController.redirect(f"/contacts/{contact_id}")

    @staticmethod
    def show(request):
        contact_id = int(request.route_params["id"])
        contact = get_contact_by_id(contact_id)
        if contact is None:
            return BaseController.not_found()
        return BaseController.render(
            "contact/show.html",
            context={"contact": contact},
            request=request,
        )

    @staticmethod
    def edit(request):
        contact_id = int(request.route_params["id"])
        contact = get_contact_by_id(contact_id)
        if contact is None:
            return BaseController.not_found()

        form = ContactForm(_form_data_from_contact(contact))
        return BaseController.render(
            "contact/form.html",
            context=_form_context(
                request,
                form,
                action=f"/contacts/{contact_id}",
                titre="Modifier contact",
            ),
            request=request,
        )

    @staticmethod
    def update(request):
        contact_id = int(request.route_params["id"])
        if get_contact_by_id(contact_id) is None:
            return BaseController.not_found()

        villes = get_villes()
        form = ContactForm.from_request(request, ville_choices=_ville_choices(villes))
        if not form.is_valid():
            return BaseController.validation_error(
                "contact/form.html",
                context={
                    "form": form,
                    "action": f"/contacts/{contact_id}",
                    "titre": "Modifier contact",
                    "villes": villes,
                    "ville_choices": _ville_choices(villes),
                },
                request=request,
            )

        update_contact(contact_id, form.cleaned_data)
        return BaseController.redirect(f"/contacts/{contact_id}")

    @staticmethod
    def destroy(request):
        contact_id = int(request.route_params["id"])
        delete_contact(contact_id)
        return BaseController.redirect("/contacts")
