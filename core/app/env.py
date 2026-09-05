# pyright: strict
"""Lecture canonique de `APP_ENV` (ENV-APP-ENV-NORMALISATION-001).

Trois normalisations coexistaient dans le dépôt pour la même variable : aucune
(`os.getenv("APP_ENV", "dev")`), `.lower()` seul, et `.strip().lower()`. Le
principe 11 en veut une, et les deux premières laissaient passer ce que la
troisième bloque.

La conséquence n'était pas cosmétique. `APP_ENV=Prod` ou `APP_ENV="prod "`
comparé brut à `"prod"` rend la comparaison fausse, si bien que deux gardes de
sécurité cessaient de se déclencher : l'API IoT s'enregistrait sans jeton en
production, et `fixtures:load --run` acceptait de peupler la base de production
sans `--force`.

Toute lecture de `APP_ENV` passe désormais par ce module, et le garde-fou
`tests/meta/test_app_env_normalisation_001.py` refuse qu'une nouvelle lecture
brute apparaisse.
"""
from __future__ import annotations

import os
from collections.abc import Mapping

__all__ = [
    "APP_ENV_VAR",
    "DEFAULT_APP_ENV",
    "PROD",
    "PROD_SPELLINGS",
    "normalize_app_env",
    "read_app_env",
    "is_prod",
]

#: Nom de la variable d'environnement portant l'environnement actif.
APP_ENV_VAR = "APP_ENV"

#: Environnement retenu quand la variable est absente, vide ou blanche.
DEFAULT_APP_ENV = "dev"

#: Valeur normalisée désignant la production, forme canonique.
PROD = "prod"

#: Orthographes qui désignent la production sans ambiguïté
#: (`ENV-APP-ENV-PRODUCTION-SPELLING-001`).
#:
#: `production` s'écrit au moins aussi naturellement que `prod`, et ne valait
#: pas production : `is_prod("production")` rendait **faux**. Les mêmes gardes
#: que `Prod` avait désarmées l'étaient donc encore, à une orthographe près.
#: `fixtures:purge --run` supprimait les données sans exiger `--force`, et
#: l'application servait ses pages d'erreur en mode développement, pile
#: d'exception comprise.
#:
#: La liste s'arrête là, et ce n'est pas un oubli. `staging`, `preprod` ou
#: `ci` sont des environnements distincts, que leurs exploitants ne veulent pas
#: voir traités comme la production. Accepter tout ce qui n'est pas connu
#: rendrait le refus si fréquent qu'on le désactiverait.
#:
#: `forge deploy:check` continue d'exiger la forme canonique `prod` dans
#: `env/prod` : ceci défend contre une faute, cela pousse vers la convention.
PROD_SPELLINGS = frozenset({PROD, "production"})


def normalize_app_env(value: object) -> str:
    """Forme canonique d'une valeur d'environnement.

    Retire les blancs de bord et met en minuscules. Une valeur absente, vide ou
    entièrement blanche vaut `DEFAULT_APP_ENV`, ce qui est le côté sûr : un
    environnement inconnu ne doit pas être pris pour la production.

    Accepte `object` parce que la valeur peut venir du registre `core.forge`,
    qui n'est pas typé, et non seulement de l'environnement du processus.
    """
    if value is None:
        return DEFAULT_APP_ENV
    normalized = str(value).strip().lower()
    return normalized or DEFAULT_APP_ENV


def read_app_env(environ: Mapping[str, str] | None = None) -> str:
    """Environnement actif, lu depuis l'environnement du processus.

    `environ` permet de lire une autre source que `os.environ`, ce dont les
    tests ont besoin sans toucher au processus.
    """
    source = os.environ if environ is None else environ
    return normalize_app_env(source.get(APP_ENV_VAR))


def is_prod(value: object) -> bool:
    """Vrai si `value` désigne la production, une fois normalisée.

    À préférer à une comparaison écrite à la main : c'est l'écriture à la main
    qui avait laissé passer `Prod`.

    Reconnaît `prod` et `production` (`ENV-APP-ENV-PRODUCTION-SPELLING-001`).
    La seconde ne valait pas production, si bien que les gardes désarmées par
    `Prod` l'étaient encore à une orthographe près.
    """
    return normalize_app_env(value) in PROD_SPELLINGS
