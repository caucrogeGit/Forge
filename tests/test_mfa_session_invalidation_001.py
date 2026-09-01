"""MFA-SESSION-INVALIDATION-001 : activer un facteur ferme les sessions ouvertes.

Activer un second facteur ne protège rien tant que les sessions ouvertes
**avant** l'activation restent valides. Un accès obtenu avec le seul mot de
passe survivait au renforcement, ce qui vidait le geste de son sens.

Ces tests jouent le parcours complet, de la confirmation du facteur à la
révocation, sur les stores livrés. Ils exercent le code exact que la référence
de l'opt-in donne à copier, pour que la documentation ne puisse pas décrire un
geste qui ne marche pas.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_mfa")

from core.sessions.contract import SessionStore  # noqa: E402
from core.sessions.file_store import FileSessionStore  # noqa: E402
from core.sessions.keys import SESSION_KEY_AUTH_USER_ID as CLE  # noqa: E402
from core.sessions.memory_store import MemorySessionStore  # noqa: E402

UTILISATEUR = 42
AUTRE = 7


@pytest.fixture(params=["memoire", "fichier"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> SessionStore:
    if request.param == "memoire":
        return MemorySessionStore()
    return FileSessionStore(sessions_dir=tmp_path / "sessions")


@pytest.fixture
def cle_mfa(monkeypatch: pytest.MonkeyPatch) -> None:
    from cryptography.fernet import Fernet

    monkeypatch.setenv("FORGE_MFA_SECRET_KEY", Fernet.generate_key().decode())


class TestParcoursActivation:
    """De la confirmation du facteur à la révocation, comme la doc le montre."""

    def test_les_autres_sessions_tombent_et_la_courante_survit(
        self, store: SessionStore, cle_mfa: None
    ) -> None:
        from forge_mvc_mfa import (
            confirm_totp_factor,
            create_totp_factor,
            decrypt_totp_secret,
        )
        import pyotp

        # Trois sessions ouvertes avec le seul mot de passe.
        courante = store.create({CLE: UTILISATEUR})
        portable = store.create({CLE: UTILISATEUR})
        poste_partage = store.create({CLE: UTILISATEUR})

        # L'utilisateur enrôle et confirme son facteur.
        setup = create_totp_factor(UTILISATEUR, label="Authenticator")
        code = pyotp.TOTP(decrypt_totp_secret(setup.factor.totp_secret)).now()
        actif = confirm_totp_factor(setup.factor, code)
        assert actif is not None, "le facteur devait être confirmé"

        revoquees = store.delete_for_user(actif.user_id, except_session_id=courante)

        assert revoquees == 2
        assert store.get(courante) is not None, "celui qui active ne doit pas être déconnecté"
        assert store.get(portable) is None
        assert store.get(poste_partage) is None

    def test_les_sessions_des_autres_comptes_survivent(
        self, store: SessionStore, cle_mfa: None
    ) -> None:
        courante = store.create({CLE: UTILISATEUR})
        voisin = store.create({CLE: AUTRE})

        store.delete_for_user(UTILISATEUR, except_session_id=courante)

        assert store.get(voisin) is not None

    def test_sans_epargner_la_courante_l_utilisateur_se_deconnecte_lui_meme(
        self, store: SessionStore
    ) -> None:
        """Ce que `except_session_id` évite, énoncé explicitement."""
        courante = store.create({CLE: UTILISATEUR})

        store.delete_for_user(UTILISATEUR)

        assert store.get(courante) is None

    def test_un_facteur_refuse_ne_doit_rien_revoquer(
        self, store: SessionStore, cle_mfa: None
    ) -> None:
        """La révocation suit la confirmation, elle ne la précède pas."""
        from forge_mvc_mfa import confirm_totp_factor, create_totp_factor

        ouverte = store.create({CLE: UTILISATEUR})
        setup = create_totp_factor(UTILISATEUR, label="Authenticator")

        assert confirm_totp_factor(setup.factor, "000000") is None
        assert store.get(ouverte) is not None


class TestCodeDeLaDocumentation:
    """Le geste que la référence de l'opt-in donne à copier."""

    def test_la_reference_montre_le_parametre_qui_epargne(self) -> None:
        reference = (
            Path(__file__).resolve().parent.parent
            / "packages" / "forge-mvc-mfa" / "docs" / "reference.md"
        )
        texte = reference.read_text(encoding="utf-8")

        assert "delete_for_user" in texte
        assert "except_session_id" in texte, (
            "la référence doit montrer le paramètre qui épargne la session courante"
        )
