# pyright: strict
"""Reconnaissance des secrets laissés à leur valeur d'amorçage.

`forge-mvc-mfa` refusait déjà les valeurs évidentes pour sa clé de chiffrement,
et il était le seul. Le pré-vol de déploiement en avait besoin pour les mots de
passe de base et les jetons d'API (`DEPLOY-CHECK-SECRETS-001`), et un opt-in ne
peut pas dépendre d'un autre : la liste remonte ici plutôt que d'être recopiée.

Ce module ne décide de rien et n'accède à rien. Il répond à une question, et
l'appelant décide s'il refuse, avertit ou passe.
"""
from __future__ import annotations

__all__ = [
    "PLACEHOLDER_VALUES",
    "SENSITIVE_NAME_MARKERS",
    "NON_SECRET_NAME_SUFFIXES",
    "looks_like_placeholder",
    "is_sensitive_name",
]

#: Valeurs d'amorçage évidentes, comparées en minuscules sur la chaîne complète.
#:
#: Elles peuplent les gabarits et les exemples, et ne doivent jamais atteindre
#: la production. La liste vise le manifeste, pas la force d'un secret : juger
#: de l'entropie d'une chaîne demanderait des règles arbitraires que Forge
#: n'impose pas.
PLACEHOLDER_VALUES: frozenset[str] = frozenset({
    "change-me",
    "changeme",
    "change_me",
    "a-changer",
    "à changer",
    "default",
    "secret",
    "dev",
    "development",
    "prod",
    "production",
    "test",
    "testing",
    "todo",
    "to-do",
    "placeholder",
    "example",
    "exemple",
    "password",
    "motdepasse",
    "xxx",
    "xxxx",
    "your-key-here",
    "your_key_here",
    "votre-cle-ici",
    "none",
    "null",
    "undefined",
})

#: Fragments qui, dans un nom de variable, désignent une valeur sensible.
#:
#: Le repérage porte sur le nom et non sur une liste figée de variables, pour
#: qu'un opt-in ajouté demain soit couvert sans que ce module change.
SENSITIVE_NAME_MARKERS: tuple[str, ...] = ("PASSWORD", "PWD", "SECRET", "TOKEN")

#: Suffixes qui désignent un chemin ou un drapeau, jamais un secret.
#:
#: `SSL_KEYFILE` nomme un fichier, pas une clé : sans cette exclusion, le
#: contrôle crierait sur une configuration correcte, et un contrôle qui crie à
#: tort finit désactivé.
NON_SECRET_NAME_SUFFIXES: tuple[str, ...] = ("_FILE", "_PATH", "_DIR", "_ENABLED", "_NAME")


def looks_like_placeholder(value: object) -> bool:
    """Vrai si `value` est une valeur d'amorçage évidente, ou vide.

    La comparaison se fait en minuscules, sur la chaîne complète débarrassée de
    ses blancs de bord. Une valeur absente ou vide compte comme un placeholder :
    dans les deux cas, aucun secret n'a été posé.
    """
    if value is None:
        return True
    texte = str(value).strip()
    if not texte:
        return True
    return texte.lower() in PLACEHOLDER_VALUES


def is_sensitive_name(name: str) -> bool:
    """Vrai si `name` désigne une variable d'environnement portant un secret.

    Repère `DB_APP_PWD`, `FORGE_MFA_SECRET_KEY`, `MAIL_PASSWORD` ou
    `FORGE_IOT_API_TOKEN`, et laisse `SSL_KEYFILE` ou `APP_CSP_NONCE_ENABLED`
    tranquilles.
    """
    majuscules = name.strip().upper()
    if majuscules.endswith(NON_SECRET_NAME_SUFFIXES):
        return False
    return any(marqueur in majuscules for marqueur in SENSITIVE_NAME_MARKERS)
