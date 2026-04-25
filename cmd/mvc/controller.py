#!/usr/bin/env python3
"""
Génère un contrôleur MVC générique.

Usage :
    python cmd/make.py controller <NomEntite> [--force]

Options :
    --force, -f   Écrase le fichier s'il existe déjà

Exemple :
    python cmd/make.py controller Produit
    python cmd/make.py controller Employe --force
    → mvc/controllers/produit_controller.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import to_snake, parse_all_args, validate_name

ROOT = Path(__file__).resolve().parent.parent.parent

TEMPLATE = '''\
from core.mvc.controller.base_controller import BaseController
from core.mvc.model.exceptions import DoublonError
from core.mvc.view.pagination import Pagination
from mvc.helpers.flash import render_flash_html
from mvc.helpers.form_errors import render_errors_html
from core.security.decorators import require_auth, require_csrf
from mvc.validators.{snake}_validator import {Nom}Validator
from mvc.models.{snake}_model import (
    count_{snake}s, get_{snake}s_page, get_{snake}_by_id,
    add_{snake}, update_{snake}, delete_{snake},
)


class {Nom}Controller(BaseController):

    PARTIAL  = "{slug}/partials/fields.html"
    REDIRECT = "/{slug}"
    PAR_PAGE = 10

    @staticmethod
    @require_auth
    def list(request):
        pagination = Pagination(request, count_{snake}s(), {Nom}Controller.PAR_PAGE)
        csrf       = BaseController.csrf_token(request)
        lignes     = BaseController.render_rows(
            "{slug}/partials/row.html",
            get_{snake}s_page(pagination.page, {Nom}Controller.PAR_PAGE),
            {{"csrf_token": csrf}},
        )
        return BaseController.render("{slug}/index.html", context={{
            "lignes": lignes,
            "flash" : render_flash_html(request),
            **pagination.context,
        }}, request=request)

    @staticmethod
    @require_auth
    def add_form(request):
        return BaseController.render_form("{slug}/create.html", request,
                                          {{}}, {Nom}Controller.PARTIAL)

    @staticmethod
    @require_auth
    def show(request):
        {snake}_id = request.route_params.get("id")
        {snake}    = get_{snake}_by_id({snake}_id) if {snake}_id else None
        if not {snake}:
            return BaseController.not_found()
        return BaseController.render("{slug}/show.html", context={{{snake}: {snake}}}, request=request)

    @staticmethod
    @require_auth
    def edit_form(request):
        {snake}_id = request.params.get("id", [None])[0]
        {snake}    = get_{snake}_by_id({snake}_id) if {snake}_id else None
        if not {snake}:
            return BaseController.not_found()
        return BaseController.render_form("{slug}/edit.html", request,
                                          {snake}, {Nom}Controller.PARTIAL)

    @staticmethod
    def _save(request, template, model_fn, flash_msg, *, is_new=False):
        {snake}   = BaseController.body(request)
        validator = {Nom}Validator({snake})
        if not validator.is_valid():
            return BaseController.render_form(template, request,
                                              {snake}, {Nom}Controller.PARTIAL, 400,
                                              render_errors_html(validator.errors()))
        if is_new:
            try:
                model_fn({snake})
            except DoublonError as e:
                validator.add_error(f"Cet identifiant « {{e}} » existe déjà.")
                return BaseController.render_form(template, request,
                                                  {snake}, {Nom}Controller.PARTIAL, 400,
                                                  render_errors_html(validator.errors()))
        else:
            model_fn({snake})
        BaseController.set_flash(request, flash_msg)
        return BaseController.redirect({Nom}Controller.REDIRECT)

    @staticmethod
    @require_auth
    @require_csrf
    def add(request):
        return {Nom}Controller._save(request, "{slug}/create.html",
                                      add_{snake}, "{Nom} ajouté avec succès.", is_new=True)

    @staticmethod
    @require_auth
    @require_csrf
    def edit(request):
        return {Nom}Controller._save(request, "{slug}/edit.html",
                                      update_{snake}, "{Nom} modifié avec succès.")

    @staticmethod
    @require_auth
    @require_csrf
    def delete(request):
        # TODO: adapter au vrai nom de la clé primaire (ex: "{Nom}Id", "id"…)
        {snake}_id = BaseController.body(request).get("{Nom}Id")
        if not {snake}_id:
            return BaseController.not_found()
        delete_{snake}({snake}_id)
        BaseController.set_flash(request, "{Nom} supprimé.", level="error")
        return BaseController.redirect({Nom}Controller.REDIRECT)
'''


def main():
    args, force, plural = parse_all_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom   = validate_name(args[0].strip())
    snake = to_snake(nom)
    slug  = plural if plural else f"{snake}s"
    dest  = ROOT / "mvc" / "controllers" / f"{snake}_controller.py"

    if dest.exists() and not force:
        print(f"[ERREUR] {dest.relative_to(ROOT)} existe déjà. Utilisez --force pour écraser.")
        sys.exit(1)

    was_new = not dest.exists()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(TEMPLATE.format(Nom=nom, snake=snake, slug=slug), encoding="utf-8")
    print(f"[OK] {dest.relative_to(ROOT)} {'créé' if was_new else 'régénéré'}.")

    if was_new:
        manquants = []
        if not (ROOT / "mvc" / "validators" / f"{snake}_validator.py").exists():
            manquants.append(f"  mvc/validators/{snake}_validator.py")
        if not (ROOT / "mvc" / "models" / f"{snake}_model.py").exists():
            manquants.append(f"  mvc/models/{snake}_model.py")
        if not (ROOT / "mvc" / "views" / f"{snake}s").exists():
            manquants.append(f"  mvc/views/{snake}s/")
        if manquants:
            print("     Fichiers manquants à créer :")
            for m in manquants:
                print(f"    [!] {m}")


if __name__ == "__main__":
    main()
