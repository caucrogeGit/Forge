"""Tests — CORE-SESSION-DEDOMAIN-001.

Verrouille la dédomainisation de `core/security/session.py` :

  * `_normalize_legacy_user()` expose des noms canoniques anglais
    (`first_name`, `last_name`) en sortie, en plus des clés génériques
    déjà présentes (`id`, `login`, `email`, `roles`) ;
  * les alias FR `prenom`/`nom` sont conservés explicitement pour
    compatibilité avec les starters historiques (`carnet-contacts`,
    `suivi-comportement-eleves`) qui les consomment ;
  * le module `core/security/session.py` ne dépend pas de `mvc/`
    (pas de logique applicative dans le cœur Forge) ;
  * les contrats de session existants restent intacts.

Origine : ADR-003 (API publique en anglais). Le cœur Forge ne doit pas
exposer de noms applicatifs/francophones non justifiés. Les alias FR
restent par compatibilité bornée — à retirer dans Forge 2.0.
"""
from __future__ import annotations

import inspect
from pathlib import Path

from core.security import session as session_module


# Fixture utilisateur volontairement legacy : noms PascalCase d'une
# ancienne application Forge. Le normaliseur doit traduire vers
# l'API générique en sortie.
_LEGACY_USER = {
    "UtilisateurId": 1,
    "Login": "jdupont",
    "Prenom": "Jean",
    "Nom": "Dupont",
    "Email": "jdupont@test.fr",
    "roles": ["admin", "vendeur"],
}


# ── 1. Sortie générique en anglais ──────────────────────────────────────────


class TestNormalizedUserExposesCanonicalKeys:
    def test_first_name_present(self):
        normalized = session_module._normalize_legacy_user(_LEGACY_USER)
        assert normalized["first_name"] == "Jean"

    def test_last_name_present(self):
        normalized = session_module._normalize_legacy_user(_LEGACY_USER)
        assert normalized["last_name"] == "Dupont"

    def test_canonical_keys_present(self):
        normalized = session_module._normalize_legacy_user(_LEGACY_USER)
        for key in ("id", "login", "first_name", "last_name", "email", "roles"):
            assert key in normalized, f"clé canonique `{key}` manquante"

    def test_id_normalized(self):
        normalized = session_module._normalize_legacy_user(_LEGACY_USER)
        assert normalized["id"] == 1

    def test_login_normalized(self):
        normalized = session_module._normalize_legacy_user(_LEGACY_USER)
        assert normalized["login"] == "jdupont"

    def test_roles_normalized(self):
        normalized = session_module._normalize_legacy_user(_LEGACY_USER)
        assert normalized["roles"] == ["admin", "vendeur"]


# ── 2. Compatibilité bornée : alias FR conservés ────────────────────────────


class TestLegacyAliasesPreserved:
    """Les starters historiques lisent encore `prenom`/`nom` — à retirer en 2.0."""

    def test_prenom_alias_matches_first_name(self):
        normalized = session_module._normalize_legacy_user(_LEGACY_USER)
        assert normalized["prenom"] == normalized["first_name"] == "Jean"

    def test_nom_alias_matches_last_name(self):
        normalized = session_module._normalize_legacy_user(_LEGACY_USER)
        assert normalized["nom"] == normalized["last_name"] == "Dupont"


# ── 3. Priorité des sources d'entrée ────────────────────────────────────────


class TestInputPriority:
    """`first_name`/`last_name` (canoniques EN) priment sur les sources legacy."""

    def test_first_name_wins_over_prenom_and_pascal(self):
        user = {"first_name": "Alice", "prenom": "Bob", "Prenom": "Charlie"}
        normalized = session_module._normalize_legacy_user(user)
        assert normalized["first_name"] == "Alice"
        assert normalized["prenom"] == "Alice"  # alias suit la valeur canonique

    def test_last_name_wins_over_nom_and_pascal(self):
        user = {"last_name": "Smith", "nom": "Dupont", "Nom": "Martin"}
        normalized = session_module._normalize_legacy_user(user)
        assert normalized["last_name"] == "Smith"
        assert normalized["nom"] == "Smith"

    def test_empty_when_no_name_provided(self):
        normalized = session_module._normalize_legacy_user({"id": 1})
        assert normalized["first_name"] == ""
        assert normalized["last_name"] == ""
        assert normalized["prenom"] == ""
        assert normalized["nom"] == ""


# ── 4. Pas de dépendance vers mvc/ dans le cœur session ────────────────────


class TestCoreSessionDoesNotImportMvc:
    def test_no_mvc_import(self):
        source = Path(inspect.getsourcefile(session_module)).read_text(encoding="utf-8")
        offending = [
            line for line in source.splitlines()
            if line.lstrip().startswith(("from mvc", "import mvc"))
        ]
        assert not offending, (
            f"core/security/session.py doit rester indépendant de mvc/. "
            f"Imports interdits trouvés : {offending}"
        )


# ── 5. Sanity : contrats existants préservés ────────────────────────────────


class TestContractsPreserved:
    def test_session_cookie_name_unchanged(self):
        assert session_module.SESSION_COOKIE_NAME == "__Host-session_id"

    def test_session_duration_unchanged(self):
        assert session_module.SESSION_DURATION == 3600

    def test_public_functions_still_exposed(self):
        for name in (
            "create_session", "get_session", "delete_session",
            "regenerate_session", "authenticate_session", "get_session_id",
            "is_authenticated", "get_user", "user_has_role",
            "set_flash", "get_flash",
        ):
            assert callable(getattr(session_module, name, None)), (
                f"`{name}` doit rester exposé par core.security.session"
            )
