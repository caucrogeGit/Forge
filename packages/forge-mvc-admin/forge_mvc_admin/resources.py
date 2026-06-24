# pyright: strict
"""Contrat d'une ressource administrable par Forge Admin (ADMIN-RESOURCE-CONTRACT-001).

Une ressource admin décrit COMMENT une entité d'un projet Forge est administrée :
quelle entité, sous quel slug d'URL, avec quels libellés, et quels champs sont
montrés en liste et éditables en formulaire.

Le contrat est volontairement déclaratif et auto-portant : il ne lit ni le
contrat d'entité ni la base. Le rapprochement avec le contrat d'entité réel
(existence de l'entité, des champs) relèvera d'une vérification ultérieure
(`forge admin:doctor`). Voir `docs/roadmap/forge-admin-roadmap.md`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from forge_mvc_admin.exceptions import AdminResourceError

# Slug d'URL sous /admin/ : minuscules, chiffres et tirets, commençant par une lettre.
_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
# Nom d'entité canonique : PascalCase (cf. contrat d'entité, clé `name`).
_ENTITY_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
# Nom de champ : snake_case (cf. champs du contrat d'entité).
_FIELD_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class AdminResource:
    """Déclaration d'une entité administrable.

    Attributs :
        entity : nom canonique de l'entité (PascalCase), tel que déclaré dans son
            contrat (clé `name`). Exemple : ``"Article"``.
        slug : segment d'URL sous ``/admin/`` (minuscules, chiffres, tirets).
            Exemple : ``"articles"``.
        label : libellé singulier pour l'interface. Exemple : ``"Article"``.
        plural_label : libellé pluriel. Exemple : ``"Articles"``.
        list_fields : noms de champs affichés en liste (au moins un, snake_case).
        form_fields : noms de champs éditables en formulaire (au moins un).
        table : nom de la table physique (snake_case). Non dérivable du nom
            d'entité, donc déclaré explicitement. Exemple : ``"articles"``.
        order_by : colonne de tri par défaut de la liste (snake_case). Vide par
            défaut : le premier champ de ``list_fields`` est alors utilisé.
        pk : colonne de clé primaire (snake_case), utilisée par la vue détail
            (``WHERE <pk> = ?``). Défaut : ``"id"``.

    Le contrat valide sa propre forme à la construction et lève
    `AdminResourceError` en cas d'incohérence. Il ne vérifie pas que l'entité, la
    table ou les champs existent réellement : c'est le rôle d'une vérification
    ultérieure (`admin:doctor`).
    """

    entity: str
    slug: str
    label: str
    plural_label: str
    list_fields: tuple[str, ...]
    form_fields: tuple[str, ...]
    table: str
    order_by: str = ""
    pk: str = "id"

    def __post_init__(self) -> None:
        if not _ENTITY_RE.match(self.entity):
            raise AdminResourceError(
                f"entity invalide : {self.entity!r} (PascalCase attendu, ex. 'Article')."
            )
        if not _SLUG_RE.match(self.slug):
            raise AdminResourceError(
                f"slug invalide : {self.slug!r} (minuscules, chiffres et tirets, "
                "commençant par une lettre, ex. 'articles')."
            )
        if not self.label:
            raise AdminResourceError("label vide.")
        if not self.plural_label:
            raise AdminResourceError("plural_label vide.")
        _validate_fields("list_fields", self.list_fields)
        _validate_fields("form_fields", self.form_fields)
        if not _FIELD_RE.match(self.table):
            raise AdminResourceError(
                f"table invalide : {self.table!r} (snake_case attendu, ex. 'articles')."
            )
        if self.order_by and not _FIELD_RE.match(self.order_by):
            raise AdminResourceError(
                f"order_by invalide : {self.order_by!r} (snake_case attendu)."
            )
        if not _FIELD_RE.match(self.pk):
            raise AdminResourceError(
                f"pk invalide : {self.pk!r} (snake_case attendu, ex. 'id')."
            )


def _validate_fields(kind: str, names: tuple[str, ...]) -> None:
    """Valide une liste de noms de champs : non vide, snake_case, sans doublon."""
    if not names:
        raise AdminResourceError(f"{kind} : au moins un champ est requis.")
    seen: set[str] = set()
    for name in names:
        if not _FIELD_RE.match(name):
            raise AdminResourceError(
                f"{kind} : nom de champ invalide {name!r} (snake_case attendu)."
            )
        if name in seen:
            raise AdminResourceError(f"{kind} : champ en double {name!r}.")
        seen.add(name)
