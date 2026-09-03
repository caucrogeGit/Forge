# pyright: strict
"""Facteur obligatoire pour un rôle (`MFA-REQUIRED-BY-ROLE-001`).

Le paquet savait dire si un utilisateur **a** un facteur actif. Il ne savait
pas dire s'il **devrait** en avoir un.

L'application écrivait donc, dans chaque contrôleur sensible, un « si cet
utilisateur est administrateur et n'a pas de MFA, alors refuser ». Elle
l'écrivait bien la première fois, et l'oubliait au troisième écran
d'administration ajouté six mois plus tard.

## La politique est déclarée une fois

`MFA_REQUIRED_ROLES=admin,comptable` dans l'environnement, ou une liste passée
au code. Un seul endroit dit qui doit avoir un second facteur, et le contrôle
se pose là où il compte.

## Ce que la politique ne fait pas

Elle n'**active** rien. Rendre un facteur obligatoire ne peut pas le créer à la
place de l'utilisateur : il faut son téléphone, et son consentement. La
politique dit qu'un accès doit être refusé tant que le facteur manque ; c'est à
l'application de conduire l'utilisateur vers l'inscription.

Elle ne connaît pas non plus `forge-mvc-rbac`. Aucun opt-in n'importe un autre :
les rôles sont lus dans la session, où l'authentification les a rangés, et la
politique n'a pas besoin de savoir d'où ils viennent.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, cast

__all__ = [
    "MfaPolicyError",
    "ENV_REQUIRED_ROLES",
    "MfaRequirement",
    "required_roles",
    "roles_of",
    "is_mfa_required_for",
    "check_mfa_requirement",
]

#: Rôles pour lesquels un second facteur est obligatoire, séparés par virgule.
ENV_REQUIRED_ROLES = "MFA_REQUIRED_ROLES"


class MfaPolicyError(ValueError):
    """Politique mal déclarée."""


@dataclass(frozen=True)
class MfaRequirement:
    """Verdict de la politique pour un utilisateur donné."""

    required: bool
    satisfied: bool
    matching_roles: "tuple[str, ...]" = ()

    @property
    def must_enroll(self) -> bool:
        """Vrai si l'accès doit être refusé faute de facteur.

        C'est la seule question que se pose un contrôleur : le nom dit ce
        qu'il faut faire, là où `required and not satisfied` demande de
        reconstruire le raisonnement à chaque appel.
        """
        return self.required and not self.satisfied

    @property
    def reason(self) -> str:
        """Motif lisible, destiné à l'écran qui conduit vers l'inscription."""
        if not self.must_enroll:
            return ""
        roles = ", ".join(self.matching_roles)
        return (
            "un second facteur d'authentification est obligatoire pour le rôle "
            f"{roles}" if len(self.matching_roles) == 1 else
            "un second facteur d'authentification est obligatoire pour les rôles "
            f"{roles}"
        )


def required_roles(*, env: "dict[str, str] | None" = None) -> "frozenset[str]":
    """Rôles soumis à l'obligation, lus de l'environnement.

    Les noms sont normalisés en minuscules et débarrassés de leurs espaces :
    `MFA_REQUIRED_ROLES=Admin, comptable` et `admin,comptable` désignent la
    même chose, et les distinguer ferait échouer une politique pour une
    majuscule.

    Sans déclaration, l'ensemble est vide et rien n'est obligatoire : le paquet
    n'impose pas une politique que personne n'a demandée.
    """
    source = env if env is not None else dict(os.environ)
    brut = (source.get(ENV_REQUIRED_ROLES) or "").strip()
    if not brut:
        return frozenset()
    noms = {morceau.strip().lower() for morceau in brut.split(",") if morceau.strip()}
    if not noms:
        raise MfaPolicyError(
            f"{ENV_REQUIRED_ROLES} ne déclare aucun rôle exploitable. "
            "Retirez la variable pour ne rien imposer."
        )
    return frozenset(noms)


def roles_of(session: "dict[str, Any] | None") -> "frozenset[str]":
    """Rôles de l'utilisateur, lus dans la session.

    Trois emplacements sont acceptés, `user.roles`, `roles` à la racine, et
    `user.role` au singulier : les applications les emploient toutes les trois,
    et n'en reconnaître qu'un ferait échouer la politique en silence, ce qui est
    la pire issue pour un contrôle de sécurité.
    """
    if not session:
        return frozenset()

    candidats: list[Any] = []
    utilisateur = session.get("user")
    if isinstance(utilisateur, dict):
        donnees = cast("dict[str, Any]", utilisateur)
        candidats.append(donnees.get("roles"))
        candidats.append(donnees.get("role"))
    candidats.append(session.get("roles"))

    noms: set[str] = set()
    for candidat in candidats:
        if isinstance(candidat, str):
            noms.add(candidat.strip().lower())
        elif isinstance(candidat, (list, tuple, set, frozenset)):
            for element in list(cast("Any", candidat)):
                if isinstance(element, str):
                    noms.add(element.strip().lower())
    return frozenset(nom for nom in noms if nom)


def is_mfa_required_for(
    roles: "frozenset[str] | set[str] | list[str] | tuple[str, ...]",
    *,
    env: "dict[str, str] | None" = None,
    policy: "frozenset[str] | None" = None,
) -> bool:
    """Vrai si l'un des rôles impose un second facteur."""
    obligatoires = policy if policy is not None else required_roles(env=env)
    portes = {str(role).strip().lower() for role in roles}
    return bool(portes & obligatoires)


def check_mfa_requirement(
    session: "dict[str, Any] | None",
    factors: Any,
    *,
    env: "dict[str, str] | None" = None,
    policy: "frozenset[str] | None" = None,
) -> MfaRequirement:
    """Verdict de la politique pour la session et les facteurs donnés.

    `factors` est la liste de facteurs de l'utilisateur, telle que
    `is_mfa_enabled` la lit. Le paquet ne va pas la chercher : la persistance
    des facteurs appartient à l'application, et l'aller chercher ici imposerait
    une connexion à un module qui n'en a pas besoin.

    Ne lève **jamais**. Un contrôle de sécurité qui échoue en levant sur une
    session mal formée priverait d'accès un utilisateur légitime ; il rend un
    verdict, et l'appelant décide.
    """
    from forge_mvc_mfa.mfa import is_mfa_enabled

    obligatoires = policy if policy is not None else required_roles(env=env)
    portes = roles_of(session)
    concernes = tuple(sorted(portes & obligatoires))

    return MfaRequirement(
        required=bool(concernes),
        satisfied=bool(is_mfa_enabled(factors)),
        matching_roles=concernes,
    )
