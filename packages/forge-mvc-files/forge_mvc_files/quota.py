# pyright: strict
"""Quota de stockage par propriétaire (`FILES-QUOTA-001`).

Le registre de l'[ADR-094](../../../docs/adr/094-files-metadata-registry.md)
sait ce qu'un propriétaire a déposé. Il ne disait pas ce qu'il a le **droit** de
déposer, si bien qu'un compte pouvait remplir le disque un fichier valide à la
fois : chaque upload passait la taille maximale, et rien ne regardait la somme.

Le quota porte sur le couple propriétaire, une nature et un identifiant. Deux
natures ont donc deux quotas, ce qui est le sens de « par utilisateur et par
ressource » : `user` et `article` ne se règlent pas ensemble.

## Ce que le quota n'est pas

Ce n'est **pas** une borne infranchissable, et le prétendre serait faux.

Le contrôle lit la somme inscrite, puis l'appelant écrit : deux uploads
simultanés peuvent passer tous les deux. Le dépassement est alors borné par
`upload_max_size` et par le nombre de requêtes concurrentes, jamais illimité.

Fermer cette fenêtre demanderait de verrouiller le propriétaire pendant
l'écriture, donc de sérialiser les uploads d'un même compte pour une garantie
que personne n'a demandée. La borne dure contre l'épuisement du disque reste la
taille maximale d'un envoi, appliquée avant toute lecture du corps.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from core.forms.upload_exceptions import UploadError

from forge_mvc_files.registry import DbLike, owner_file_count, owner_usage_bytes

__all__ = [
    "FilesQuotaError",
    "QuotaExceededError",
    "Quota",
    "QuotaUsage",
    "quota_for",
    "quota_usage",
    "check_quota",
]


class FilesQuotaError(ValueError):
    """Quota mal déclaré dans l'environnement."""


class QuotaExceededError(UploadError):
    """Le dépôt ferait dépasser le quota du propriétaire.

    Descend d'`UploadError` : une application qui entoure déjà `save_upload`
    d'un `except UploadError` traite le refus de quota sans changer une ligne,
    et le message est destiné à être montré à l'utilisateur.
    """


@dataclass(frozen=True)
class Quota:
    """Ce qu'un propriétaire a le droit d'occuper.

    `None` veut dire « sans limite », `0` veut dire « rien ». Les confondre
    ouvrirait grand un quota qu'on croyait fermer.
    """

    max_bytes: "int | None" = None
    max_files: "int | None" = None

    @property
    def is_unlimited(self) -> bool:
        return self.max_bytes is None and self.max_files is None


@dataclass(frozen=True)
class QuotaUsage:
    """État d'un propriétaire face à son quota, de quoi afficher une jauge."""

    owner_kind: str
    owner_id: str
    used_bytes: int
    file_count: int
    quota: Quota

    @property
    def remaining_bytes(self) -> "int | None":
        """Octets restants, ou `None` si le quota est sans limite de taille.

        Jamais négatif : un quota abaissé après coup laisse des propriétaires
        au dessus, et une valeur négative se propagerait dans un affichage.
        """
        if self.quota.max_bytes is None:
            return None
        return max(0, self.quota.max_bytes - self.used_bytes)

    @property
    def remaining_files(self) -> "int | None":
        if self.quota.max_files is None:
            return None
        return max(0, self.quota.max_files - self.file_count)

    @property
    def is_exceeded(self) -> bool:
        """Vrai si le propriétaire est **déjà** au delà, sans rien déposer."""
        return (
            self.quota.max_bytes is not None and self.used_bytes > self.quota.max_bytes
        ) or (
            self.quota.max_files is not None and self.file_count > self.quota.max_files
        )


def _env_suffix(owner_kind: str) -> str:
    """Nature transformée en fragment de nom de variable.

    `user` donne `USER`, `blog-post` donne `BLOG_POST` : un nom de variable
    d'environnement ne porte ni tiret ni point.
    """
    return "".join(c if c.isalnum() else "_" for c in owner_kind).upper()


def _read_positive_int(nom: str) -> "int | None":
    """Entier positif lu dans l'environnement, ou `None` si non déclaré.

    Une valeur illisible **lève** au lieu d'être ignorée. Un quota est une
    limite : la retomber en silence sur « aucune limite » à cause d'une faute
    de frappe irait exactement dans le mauvais sens, et personne ne le verrait
    avant que le disque soit plein.
    """
    brut = (os.getenv(nom) or "").strip()
    if not brut:
        return None
    try:
        valeur = int(brut)
    except ValueError:
        raise FilesQuotaError(
            f"{nom} doit être un nombre d'octets entier. Reçu : {brut!r}. "
            "Les suffixes comme « 50MB » ne sont pas lus, écrire 52428800."
        ) from None
    if valeur < 0:
        raise FilesQuotaError(f"{nom} ne peut pas être négatif. Reçu : {valeur}.")
    return valeur


def quota_for(owner_kind: str) -> Quota:
    """Quota applicable à une nature de propriétaire, lu de l'environnement.

    Deux niveaux, du plus précis au plus général :

    - `FILES_QUOTA_USER_BYTES` et `FILES_QUOTA_USER_FILES`, propres à `user` ;
    - `FILES_QUOTA_BYTES` et `FILES_QUOTA_FILES`, communs à toutes les natures.

    Sans aucune des deux, le quota est sans limite : le paquet ne borne rien
    tant que l'exploitant n'a rien demandé.

    Raises:
        FilesQuotaError: nature vide, ou valeur d'environnement illisible.
    """
    nature = (owner_kind or "").strip()
    if not nature:
        raise FilesQuotaError("owner_kind ne peut pas être vide.")

    suffixe = _env_suffix(nature)
    octets = _read_positive_int(f"FILES_QUOTA_{suffixe}_BYTES")
    if octets is None:
        octets = _read_positive_int("FILES_QUOTA_BYTES")
    fichiers = _read_positive_int(f"FILES_QUOTA_{suffixe}_FILES")
    if fichiers is None:
        fichiers = _read_positive_int("FILES_QUOTA_FILES")
    return Quota(max_bytes=octets, max_files=fichiers)


def quota_usage(
    owner_kind: str,
    owner_id: object,
    *,
    quota: "Quota | None" = None,
    db: "DbLike | None" = None,
) -> QuotaUsage:
    """État courant d'un propriétaire, pour l'afficher sans rien refuser."""
    applicable = quota if quota is not None else quota_for(owner_kind)
    return QuotaUsage(
        owner_kind=(owner_kind or "").strip(),
        owner_id="" if owner_id is None else str(owner_id).strip(),
        used_bytes=owner_usage_bytes(owner_kind, owner_id, db=db),
        file_count=owner_file_count(owner_kind, owner_id, db=db),
        quota=applicable,
    )


def check_quota(
    owner_kind: str,
    owner_id: object,
    incoming_bytes: int,
    *,
    quota: "Quota | None" = None,
    db: "DbLike | None" = None,
) -> QuotaUsage:
    """Refuse le dépôt qui ferait dépasser le quota. Rend l'état courant sinon.

    À appeler **avant** d'écrire. Contrôler après coup obligerait à supprimer un
    fichier déjà posé, et laisserait une trace sur disque en cas d'incident
    entre les deux gestes.

    `incoming_bytes` est la taille de ce qui va être déposé. La longueur du
    corps de la requête convient et surestime un peu, l'enveloppe multipart y
    étant comptée : pour un quota, l'erreur va dans le bon sens.

    Un quota sans limite ne touche pas la base : rien à comparer, donc rien à
    lire, et un déploiement sans quota ne paye pas une requête par upload.

    Raises:
        QuotaExceededError: le dépôt ferait dépasser la taille ou le nombre.
        FilesQuotaError: taille négative, ou quota mal déclaré.
    """
    if not isinstance(incoming_bytes, int) or isinstance(incoming_bytes, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise FilesQuotaError(
            f"incoming_bytes doit être un entier. Reçu : {incoming_bytes!r}."
        )
    if incoming_bytes < 0:
        raise FilesQuotaError(
            f"incoming_bytes ne peut pas être négatif. Reçu : {incoming_bytes}."
        )

    applicable = quota if quota is not None else quota_for(owner_kind)
    if applicable.is_unlimited:
        return QuotaUsage(
            owner_kind=(owner_kind or "").strip(),
            owner_id="" if owner_id is None else str(owner_id).strip(),
            used_bytes=0,
            file_count=0,
            quota=applicable,
        )

    etat = quota_usage(owner_kind, owner_id, quota=applicable, db=db)

    if applicable.max_bytes is not None:
        apres = etat.used_bytes + incoming_bytes
        if apres > applicable.max_bytes:
            raise QuotaExceededError(
                "Quota de stockage dépassé : "
                f"{etat.used_bytes} octets déjà utilisés sur {applicable.max_bytes}, "
                f"et ce dépôt en ajoute {incoming_bytes}."
            )

    if applicable.max_files is not None:
        if etat.file_count + 1 > applicable.max_files:
            raise QuotaExceededError(
                "Nombre de fichiers dépassé : "
                f"{etat.file_count} déjà déposés sur {applicable.max_files} autorisés."
            )

    return etat
