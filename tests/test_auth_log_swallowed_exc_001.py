"""AUTH-LOG-SWALLOWED-EXC-001.

Une exception levée par le `user_loader` applicatif (base injoignable, bug du
loader) ne doit plus être avalée silencieusement : elle est journalisée en
WARNING avec sa trace, et reste DISTINCTE d'un échec d'authentification normal
(utilisateur inconnu), qui lui ne produit aucun log.
"""
from __future__ import annotations

import logging

from core.auth.session import authenticate_user


def _raising_loader(_email):
    raise RuntimeError("base injoignable")


def _unknown_user_loader(_email):
    return None


def test_loader_exception_logged_as_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="core.auth.session"):
        result = authenticate_user("user@example.test", "secret", _raising_loader)

    assert result is None
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings, "une exception du user_loader doit produire un WARNING"
    assert any("user_loader" in r.getMessage() for r in warnings)
    # La trace de l'exception d'infrastructure est attachée (exc_info).
    assert any(r.exc_info is not None for r in warnings)


def test_unknown_user_is_not_logged(caplog):
    with caplog.at_level(logging.WARNING, logger="core.auth.session"):
        result = authenticate_user("user@example.test", "secret", _unknown_user_loader)

    assert result is None
    assert not [r for r in caplog.records if r.levelno == logging.WARNING], (
        "un échec d'auth normal (utilisateur inconnu) ne doit pas être journalisé"
    )
