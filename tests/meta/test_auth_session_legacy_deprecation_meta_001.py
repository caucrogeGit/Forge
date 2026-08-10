"""Garde-fou documentaire AUTH-SESSION-LEGACY-DEPRECATION-001.

Vérifie que :
- les fonctions legacy dépréciées contiennent bien un appel warnings.warn(DeprecationWarning) ;
- les fonctions infrastructure ne contiennent pas de DeprecationWarning ;
- le message de chaque warning référence l'API canonique à utiliser.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
SECURITY_SESSION = PROJECT_ROOT / "core" / "security" / "session.py"


def _source() -> str:
    assert SECURITY_SESSION.exists(), (
        f"{SECURITY_SESSION} introuvable : corrigez la cible du garde-fou au "
        "lieu de le laisser se taire."
    )
    return SECURITY_SESSION.read_text(encoding="utf-8")


def _source_de(nom: str) -> str:
    """Source réelle d'une fonction exposée par `core.security.session`.

    Suit les réexportations : une fonction déplacée vers un autre module reste
    jugée, là où une recherche de `def <nom>` dans le fichier la perdrait.
    """
    import inspect

    from core.security import session as module

    fonction = getattr(module, nom, None)
    assert fonction is not None, (
        f"core.security.session n'expose plus {nom} : retirez-la de la liste "
        "au lieu de laisser ce contrôle se taire."
    )
    return inspect.getsource(fonction)


_DEPRECATED_FUNCTIONS = [
    "create_session",
    "authenticate_session",
    "is_authenticated",
    "get_user",
]

_INFRASTRUCTURE_FUNCTIONS = [
    "get_session_id",
    "get_session",
    "delete_session",
    "regenerate_session",
    "user_has_role",
    "set_flash",
    "get_flash",
]


class TestDeprecatedFunctionsHaveWarnings:
    """Chaque fonction dépréciée contient un appel warnings.warn(DeprecationWarning)."""

    @pytest.mark.parametrize("func_name", _DEPRECATED_FUNCTIONS)
    def test_function_has_deprecation_warn(self, func_name):
        """La fonction {func_name} contient un appel warnings.warn(..., DeprecationWarning, ...)."""
        source = _source()
        assert f"def {func_name}" in source, f"{func_name} introuvable dans le fichier"

        # Extraire le bloc de la fonction jusqu'à la prochaine définition de fonction
        start = source.index(f"def {func_name}")
        rest = source[start:]
        next_def = rest.find("\ndef ", 4)
        func_body = rest[:next_def] if next_def != -1 else rest

        assert "DeprecationWarning" in func_body, (
            f"{func_name} ne contient pas DeprecationWarning"
        )
        assert "warnings.warn" in func_body, (
            f"{func_name} ne contient pas warnings.warn"
        )

    @pytest.mark.parametrize("func_name", _DEPRECATED_FUNCTIONS)
    def test_deprecation_message_references_canonical(self, func_name):
        """Le message de dépréciation de {func_name} mentionne 'core.auth.session' ou 'get_session_store'."""
        source = _source()
        start = source.index(f"def {func_name}")
        rest = source[start:]
        next_def = rest.find("\ndef ", 4)
        func_body = rest[:next_def] if next_def != -1 else rest

        has_canonical_ref = (
            "core.auth.session" in func_body
            or "get_session_store" in func_body
        )
        assert has_canonical_ref, (
            f"Le message de dépréciation de {func_name} doit mentionner "
            "'core.auth.session' ou 'get_session_store'"
        )


class TestInfrastructureFunctionsNoWarnings:
    """Les fonctions infrastructure ne doivent pas émettre de DeprecationWarning."""

    @pytest.mark.parametrize("func_name", _INFRASTRUCTURE_FUNCTIONS)
    def test_function_has_no_deprecation_warn(self, func_name):
        """La fonction {func_name} ne contient pas de DeprecationWarning.

        La source est résolue par l'**objet fonction**, non par une recherche
        de `def <nom>` dans le fichier (`TESTS-DEAD-SKIPS-REVIVE-001`).
        `get_session` et `get_session_id` ont été déplacées vers
        `core/sessions/access.py` puis réexportées : la recherche textuelle ne
        les trouvait plus et **sautait**, laissant deux fonctions
        d'infrastructure sans surveillance. Passer par l'objet suit la
        réexportation, et échoue franchement si le nom disparaît.
        """
        func_body = _source_de(func_name)

        assert "DeprecationWarning" not in func_body, (
            f"{func_name} ne devrait pas contenir DeprecationWarning — "
            "c'est une fonction infrastructure"
        )


class TestModuleStructure:
    """Vérifications structurelles de core/security/session.py."""

    def test_import_warnings_present(self):
        """Le module importe 'warnings' au niveau module."""
        source = _source()
        assert "import warnings" in source, (
            "core/security/session.py doit importer warnings pour les DeprecationWarning"
        )

    def test_stacklevel_2_present(self):
        """Les appels warnings.warn utilisent stacklevel=2."""
        source = _source()
        assert "stacklevel=2" in source, (
            "Les DeprecationWarning doivent utiliser stacklevel=2 "
            "pour pointer vers le code appelant"
        )
