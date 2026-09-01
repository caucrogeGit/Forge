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


#: Colonnes d'horodatage gérées par le framework (ADR-081), posées en Python.
_MANAGED_TIMESTAMP_COLUMNS = ("created_at", "updated_at")


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
        filter_fields : champs acceptant un filtre d'égalité en liste. Vide par
            défaut, la déclaration étant obligatoire.
        search_fields : champs balayés par la recherche plein texte. Vide par
            défaut, pour la même raison.

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
    #: La table porte les horodatages gérés de l'ADR-081, `created_at` et
    #: `updated_at`, `NOT NULL` et **sans défaut SQL** : l'autorité est Python.
    #:
    #: Déclaré et non deviné (principe 3). Le back-office ignorait ce mécanisme
    #: depuis l'ADR-081, si bien que créer un enregistrement échouait sur les
    #: quatre backends, et que modifier laissait `updated_at` figé
    #: (`ADMIN-MANAGED-TIMESTAMPS-001`).
    timestamps: bool = False
    #: Champs sur lesquels la liste accepte un filtre d'égalité.
    #:
    #: Vide par défaut : un filtre porte sur une colonne nommée dans l'URL, et
    #: accepter n'importe laquelle exposerait des colonnes que la liste
    #: n'affiche pas, un mot de passe haché par exemple. La déclaration est donc
    #: obligatoire, jamais déduite de `list_fields` (`ADMIN-LIST-FILTERS-001`).
    filter_fields: tuple[str, ...] = ()
    #: Champs balayés par la recherche plein texte, en `LIKE`.
    #:
    #: Vide par défaut, pour la même raison. Une recherche sur une colonne non
    #: déclarée permettrait de deviner son contenu caractère par caractère.
    search_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _ENTITY_RE.fullmatch(self.entity):
            raise AdminResourceError(
                f"entity invalide : {self.entity!r} (PascalCase attendu, ex. 'Article')."
            )
        if not _SLUG_RE.fullmatch(self.slug):
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
        if not _FIELD_RE.fullmatch(self.table):
            raise AdminResourceError(
                f"table invalide : {self.table!r} (snake_case attendu, ex. 'articles')."
            )
        if self.order_by and not _FIELD_RE.fullmatch(self.order_by):
            raise AdminResourceError(
                f"order_by invalide : {self.order_by!r} (snake_case attendu)."
            )
        if not isinstance(self.timestamps, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise AdminResourceError(
                f"timestamps invalide : {self.timestamps!r} (booléen attendu)."
            )
        for gere in _MANAGED_TIMESTAMP_COLUMNS:
            if self.timestamps and gere in self.form_fields:
                raise AdminResourceError(
                    f"{gere} est un horodatage géré : il ne peut pas figurer dans "
                    "form_fields, le framework le pose lui-même (ADR-081)."
                )
        if not _FIELD_RE.fullmatch(self.pk):
            raise AdminResourceError(
                f"pk invalide : {self.pk!r} (snake_case attendu, ex. 'id')."
            )
        # Filtre et recherche sont facultatifs, donc validés seulement s'ils
        # sont déclarés : `_validate_fields` refuse une liste vide.
        if self.filter_fields:
            _validate_fields("filter_fields", self.filter_fields)
        if self.search_fields:
            _validate_fields("search_fields", self.search_fields)


def _validate_fields(kind: str, names: tuple[str, ...]) -> None:
    """Valide une liste de noms de champs : non vide, snake_case, sans doublon."""
    if not names:
        raise AdminResourceError(f"{kind} : au moins un champ est requis.")
    seen: set[str] = set()
    for name in names:
        if not _FIELD_RE.fullmatch(name):
            raise AdminResourceError(
                f"{kind} : nom de champ invalide {name!r} (snake_case attendu)."
            )
        if name in seen:
            raise AdminResourceError(f"{kind} : champ en double {name!r}.")
        seen.add(name)
