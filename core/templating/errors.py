# pyright: strict
"""Exceptions et formatage d'erreurs du moteur de rendu Forge.

Ticket : DX-RENDER-ERROR-001.

`TemplateNotFoundError` est l'exception Forge interne levée par le renderer
(Jinja2 aujourd'hui) quand un template demandé via `BaseController.render(...)`
n'existe pas dans `mvc/views/`. Le formatage du message d'erreur reste
côté CLI/HTTP — ce module définit seulement le contrat.

Le format pédagogique du message (dev) est volontairement en `text/plain` :

  - distingue clairement le cas du rendu d'une vraie page d'erreur HTML
    (errors/404.html, errors/500.html) ;
  - reste lisible dans tous les contextes (curl, journal, navigateur).

En `APP_ENV=prod`, le message est minimal — voir `format_missing_template_body()`.
"""

from __future__ import annotations


class TemplateNotFoundError(LookupError):
    """Levée quand un template demandé est introuvable côté renderer.

    Attributs publics :
        template (str)    : chemin du template (tel que demandé par l'appelant).
        views_dir (str | None) : dossier `mvc/views/` configuré, si connu.

    Hérite de `LookupError` (et non `Exception` brut) pour rester
    catchable par des helpers génériques qui filtrent sur la famille
    "ressource introuvable".
    """

    def __init__(self, template: str, views_dir: str | None = None) -> None:
        self.template = template
        self.views_dir = views_dir
        if views_dir:
            super().__init__(f"Template introuvable : {template} (vues : {views_dir}).")
        else:
            super().__init__(f"Template introuvable : {template}.")


# ── Formatage des messages d'erreur ─────────────────────────────────────────


def format_missing_template_dev(template: str, views_dir: str | None) -> str:
    """Message pédagogique imprimé en `APP_ENV=dev` quand un template manque.

    Doit citer le nom de la vue, expliquer le rôle de `render()`, montrer
    un exemple valide, et proposer les alternatives `Response.text(...)`
    et `Response.debug(...)`.
    """
    lookup = f"  {views_dir.rstrip('/')}/{template}" if views_dir else f"  mvc/views/{template}"
    return (
        f"Vue introuvable : {template}\n"
        f"\n"
        f"BaseController.render() attend un chemin de template relatif à mvc/views/.\n"
        f"\n"
        f"Forge a cherché une vue correspondant à :\n"
        f"{lookup}\n"
        f"\n"
        f"Exemples valides :\n"
        f"  BaseController.render(\"landing/index.html\", request=request)\n"
        f"  BaseController.render(\"welcome/index.html\", request=request)\n"
        f"\n"
        f"Si vous voulez retourner du texte brut :\n"
        f"  Response.text({template!r})\n"
        f"\n"
        f"Si vous voulez inspecter un objet :\n"
        f"  Response.debug(obj)\n"
    )


def format_missing_template_prod() -> str:
    """Message court en `APP_ENV=prod` — aucune fuite de chemin interne."""
    return "Erreur serveur.\n"
