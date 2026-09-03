"""forge-mvc-testing — infrastructure de test partagée pour Forge (dev only).

Fournit :

- ``FakeRequest``, requête factice pour appeler un contrôleur directement ;
- ``ForgeTestClient``, client de test passant par le **vrai** callable WSGI,
  donc par le routeur et les middlewares (``TESTING-CLIENT-001``) ;
- ``login_as`` / ``logout``, authentification de test par le vrai magasin de
  sessions (``TESTING-LOGIN-AS-001``) ;
- des assertions de session et de jeton anti-rejeu (``TESTING-ASSERTIONS-001``) ;
- ``load_fixture_scenario``, chargement d'un scénario de `forge-mvc-fixtures`
  sans en réécrire une seconde implémentation (``TESTING-FIXTURES-ALIGN-001``) ;
- ``code_sans_prose``, lecture d'un source sans sa prose, pour les garde-fous
  de structure ;
- via un plugin pytest (point d'entrée ``pytest11``, voir
  ``forge_mvc_testing.plugin``), les fixtures partagées : configuration du
  noyau, nettoyage entre tests, ``fake_request``, ``client`` et
  ``fixtures_loader``.

Ce paquet n'est JAMAIS une dépendance runtime ; il n'est installé qu'en
développement (ADR-041).
"""
from __future__ import annotations

from forge_mvc_testing.assertions import (
    assert_authenticated,
    assert_no_session,
    assert_not_authenticated,
    assert_session_key,
    assert_session_rotated,
    assert_token_consumed,
    assert_token_valid,
)
from forge_mvc_testing.auth_helper import (
    DEFAULT_TTL_SECONDS,
    AuthHelperError,
    login_as,
    logout,
    session_of,
)
from forge_mvc_testing.client import (
    ClientResponse,
    ForgeTestClient,
    ClientError,
)
from forge_mvc_testing.fake_request import FakeRequest
from forge_mvc_testing.fixtures_support import (
    FixturesUnavailable,
    load_fixture_scenario,
)
from forge_mvc_testing.source_scan import code_sans_prose, lignes_de_prose

__all__ = [
    "FakeRequest",
    "code_sans_prose",
    "lignes_de_prose",
    # Client de test sur le vrai chemin WSGI (TESTING-CLIENT-001)
    "ForgeTestClient",
    "ClientResponse",
    "ClientError",
    # Authentification de test (TESTING-LOGIN-AS-001)
    "login_as",
    "logout",
    "session_of",
    "AuthHelperError",
    "DEFAULT_TTL_SECONDS",
    # Assertions (TESTING-ASSERTIONS-001)
    "assert_authenticated",
    "assert_not_authenticated",
    "assert_no_session",
    "assert_session_key",
    "assert_session_rotated",
    "assert_token_consumed",
    "assert_token_valid",
    # Fixtures alignées (TESTING-FIXTURES-ALIGN-001)
    "load_fixture_scenario",
    "FixturesUnavailable",
]
__version__ = "1.0.0rc7"
