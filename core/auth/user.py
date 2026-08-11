# pyright: strict
"""Contrat utilisateur minimal Forge.

## Identité et contact (ADR-089)

Un utilisateur porte deux choses de natures différentes, et ce module les
sépare depuis `AUTH-IDENTITY-CONTACT-001`.

`login` est l'**identité** : ce que l'utilisateur saisit pour se connecter.
Elle est unique, obligatoire, sans contrainte de forme, et sa **casse lui
appartient**. Rien ici n'exige une adresse, et c'est délibéré : une application
y met légitimement un identifiant de classe comme `2TNE1-01` ou un nom de
compte comme `admin`.

`email` est le **contact**, facultatif. Il sert au dépannage, il change au fil
d'une carrière, et deux comptes peuvent partager la même adresse. Il n'a jamais
d'effet sur la façon de se connecter.

Avant cet ADR, une seule colonne `email` portait les deux, si bien que poser
son adresse changeait son identifiant. Le nom a d'ailleurs produit du
comportement : une fonction de la CLI abaissait la casse de l'identité parce
qu'on normalise une adresse, ce qui fermait la connexion sur SQLite
(`AUTH-CASE-ASYMMETRY-001`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from core.auth.exceptions import InvalidAuthUserError


@dataclass(frozen=True)
class AuthUser:
    """Representation Python minimale d'un utilisateur authentifiable."""

    id: int
    login: str
    password_hash: str
    is_active: bool = True
    #: Contact facultatif (ADR-089). `None` signifie « pas d'adresse connue »,
    #: ce qui est un compte valide : un élève mineur n'en a pas.
    email: str | None = None
    created_at: Any | None = None
    updated_at: Any | None = None


def _validate_fields(
    user_id: Any,
    login: Any,
    password_hash: Any,
    is_active: Any,
    email: Any = None,
) -> None:
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise InvalidAuthUserError("id doit etre un entier strictement positif")

    if not isinstance(login, str) or not login.strip():
        raise InvalidAuthUserError("login doit etre une chaine non vide")

    if not isinstance(password_hash, str) or not password_hash:
        raise InvalidAuthUserError("password_hash doit etre une chaine non vide")

    # Le contact est FACULTATIF (ADR-089). Absent, il vaut None ; présent, il
    # doit être une chaîne non vide, une chaîne blanche ne désignant personne.
    if email is not None:
        if not isinstance(email, str) or not email.strip():
            raise InvalidAuthUserError("email doit etre une chaine non vide ou absent")

    # Les backends SQL (MariaDB, SQLite) renvoient une colonne BOOLEAN / tinyint(1)
    # sous forme d'entier 0/1 : on l'accepte ici, la normalisation coerce en bool.
    if not (isinstance(is_active, bool) or (isinstance(is_active, int) and is_active in (0, 1))):
        raise InvalidAuthUserError("is_active doit etre un booleen ou un entier 0/1")


def validate_auth_user_contract(data: Any) -> None:
    """Valide le contrat AuthUser minimal.

    Accepte un AuthUser deja construit ou un dict brut contenant les champs
    minimaux. Le helper ne cree aucune session et ne lit aucune base de donnees.
    """
    if isinstance(data, AuthUser):
        _validate_fields(
            data.id, data.login, data.password_hash, data.is_active, data.email
        )
        return

    if not isinstance(data, dict):
        raise InvalidAuthUserError("les donnees utilisateur doivent etre un AuthUser ou un dict")

    missing = sorted(k for k in ("id", "login", "password_hash") if k not in data)
    if missing:
        raise InvalidAuthUserError(f"champs obligatoires manquants : {', '.join(missing)}")

    data = cast("dict[str, Any]", data)
    _validate_fields(
        data["id"],
        data["login"],
        data["password_hash"],
        data.get("is_active", True),
        data.get("email"),
    )


def normalize_auth_user(data: Any) -> AuthUser:
    """Valide et normalise un dict brut en AuthUser.

    Le helper leve InvalidAuthUserError si les donnees sont incompletes ou
    invalides.
    """
    if not isinstance(data, dict):
        raise InvalidAuthUserError("les donnees utilisateur doivent etre un dict")

    validate_auth_user_contract(data)

    data = cast("dict[str, Any]", data)
    contact = data.get("email")
    return AuthUser(
        id=data["id"],
        # L'espacement de bordure est retiré, la CASSE est conservée : elle
        # appartient à l'identité (ADR-089).
        login=data["login"].strip(),
        password_hash=data["password_hash"],
        # Coerce l'entier 0/1 des backends SQL en bool (voir _validate_fields).
        is_active=bool(data.get("is_active", True)),
        # Le contact, lui, est normalisé en minuscules : c'est une adresse.
        email=contact.strip().lower() if isinstance(contact, str) else None,
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


def is_valid_auth_user(user: Any) -> bool:
    """Retourne True si user est un AuthUser structurellement valide."""
    try:
        validate_auth_user_contract(user)
    except InvalidAuthUserError:
        return False
    return isinstance(user, AuthUser)
