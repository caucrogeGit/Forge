# pyright: strict
"""MFA-REPLAY-SCOPE-DOC-001 : la portée de l'anti-rejeu est dite à l'exploitant.

Le registre des codes TOTP déjà utilisés vit en mémoire du processus. Derrière
gunicorn à plusieurs workers, chacun a le sien : un même code peut être accepté
une fois par worker. La limite était assumée dans une docstring du module, donc
visible du contributeur et invisible de celui qui déploie.

Une limite de sécurité connue et tue est plus dangereuse qu'une limite écrite :
l'exploitant qui ne la connaît pas ne peut pas décider. La règle B demande de
révéler, et ce garde-fou empêche la révélation de disparaître au prochain
remaniement de la doc.

Ce ticket ne change pas le comportement. Le remède, un magasin partagé, reste
au choix de l'exploitant selon son modèle de menace.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_mfa")

DOC = Path(__file__).resolve().parents[1] / "docs" / "reference.md"


def test_la_doc_existe() -> None:
    assert DOC.is_file()


def test_la_doc_dit_la_portee_par_processus() -> None:
    texte = DOC.read_text(encoding="utf-8")

    assert "par processus" in texte
    assert "worker" in texte


def test_la_doc_dit_le_remede() -> None:
    """Révéler sans dire quoi faire laisse l'exploitant devant un mur."""
    texte = DOC.read_text(encoding="utf-8")

    assert "un seul worker" in texte
    assert "partagé" in texte


def test_la_doc_borne_le_risque() -> None:
    """La fenêtre est courte : le dire évite la panique autant que l'aveuglement."""
    texte = DOC.read_text(encoding="utf-8")

    assert "trente secondes" in texte


def test_le_module_porte_toujours_la_meme_limite() -> None:
    """Si le code gagne un magasin partagé, cette doc devra changer avec lui."""
    import forge_mvc_mfa.totp_replay as module

    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "process-local" in source or "processus" in source, (
        "le module ne décrit plus une portée locale : la doc de référence "
        "doit être revue en même temps"
    )
