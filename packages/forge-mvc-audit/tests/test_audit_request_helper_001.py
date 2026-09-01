"""AUDIT-ACTION-HELPER-001 : prendre l'acteur dans la requête.

`record_audit` demande l'acteur en paramètre, et la documentation le montrait
écrit à la main. Dans un contrôleur il vient de la session, et chaque appel
devait l'en extraire.

L'oublier une fois donne une ligne sans acteur, c'est-à-dire un journal qui ne
répond plus à « qui a fait cela ». Rien ne le signale : la ligne existe, elle
est simplement inutile.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_audit")

from forge_mvc_audit import AuditError, record_request_audit  # noqa: E402


class _FauxDb:
    def __init__(self) -> None:
        self.lignes: list[Any] = []

    def insert(self, sql: str, params: Any) -> int:
        self.lignes.append(params)
        return len(self.lignes)


def _acteur(faux: _FauxDb) -> Any:
    """Premier paramètre de l'INSERT : la colonne `actor`."""
    return faux.lignes[0][0]


class TestExtractionDeLActeur:
    def test_l_acteur_vient_de_la_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import core.auth.session as session

        monkeypatch.setattr(session, "get_authenticated_user_id", lambda request: 42)
        faux = _FauxDb()

        record_request_audit(object(), "note.modifiee", db=faux)

        assert _acteur(faux) == "42"

    def test_l_acteur_est_rendu_en_texte(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """L'identité applicative peut être un entier comme un login."""
        import core.auth.session as session

        monkeypatch.setattr(session, "get_authenticated_user_id", lambda request: 7)
        faux = _FauxDb()

        record_request_audit(object(), "x", db=faux)

        assert isinstance(_acteur(faux), str)

    def test_un_visiteur_anonyme_donne_un_acteur_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """C'est une information, pas un manque : inventer « system » la masquerait."""
        import core.auth.session as session

        monkeypatch.setattr(session, "get_authenticated_user_id", lambda request: None)
        faux = _FauxDb()

        record_request_audit(object(), "page.vue", db=faux)

        assert _acteur(faux) is None

    def test_sans_requete_l_acteur_est_absent(self) -> None:
        """Une tâche de fond n'a pas d'auteur."""
        faux = _FauxDb()
        record_request_audit(None, "tache.terminee", db=faux)

        assert _acteur(faux) is None


class TestJournalNonBloquant:
    def test_une_session_illisible_ne_fait_pas_echouer_l_action(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un journal qui fait échouer l'action qu'il trace est pire que pas de journal."""
        import core.auth.session as session

        def casse(request: Any) -> Any:
            raise RuntimeError("session illisible")

        monkeypatch.setattr(session, "get_authenticated_user_id", casse)
        faux = _FauxDb()

        identifiant = record_request_audit(object(), "note.modifiee", db=faux)

        assert identifiant == 1
        assert _acteur(faux) is None


class TestMemeContratQueRecordAudit:
    def test_les_champs_de_cible_sont_transmis(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import core.auth.session as session

        monkeypatch.setattr(session, "get_authenticated_user_id", lambda request: 1)
        faux = _FauxDb()

        record_request_audit(
            object(), "note.modifiee",
            target_type="note", target_id=42, details="12 vers 14", db=faux,
        )

        acteur, action, type_cible, cible, details = faux.lignes[0]
        assert (action, type_cible, cible, details) == (
            "note.modifiee", "note", "42", "12 vers 14",
        )

    def test_une_action_vide_est_refusee(self) -> None:
        with pytest.raises(AuditError):
            record_request_audit(None, "   ", db=_FauxDb())

    def test_l_identifiant_ecrit_est_rendu(self) -> None:
        faux = _FauxDb()
        assert record_request_audit(None, "x", db=faux) == 1


class TestDocumentation:
    def test_la_reference_ne_montre_plus_un_acteur_ecrit_a_la_main_seul(self) -> None:
        """C'est cet exemple qui invitait à l'oubli."""
        from pathlib import Path

        reference = (
            Path(__file__).resolve().parent.parent / "docs" / "reference.md"
        ).read_text(encoding="utf-8")

        assert "record_request_audit" in reference
