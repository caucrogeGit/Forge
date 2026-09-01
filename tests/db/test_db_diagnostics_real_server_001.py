"""DB-DOCTOR-001 — le diagnostic dit ce que le serveur répond vraiment.

`forge doctor` ne disait que « connexion OK », et cela ne suffit pas : une
version trop ancienne, un jeu de caractères qui n'est pas de l'UTF-8, ou une
connexion établie sous un compte inattendu sont des pannes à venir qu'aucune
connexion réussie ne signale.

Les requêtes de diagnostic sont propres à chaque SGBD. Les comparer à des
chaînes ne prouverait rien : seul le serveur dit si elles s'exécutent.

Marqué `db` : sauté sans serveur, requis en CI via FORGE_REQUIRE_DB=1.
"""
from __future__ import annotations

import pytest

from core.database.backend import get_backend

pytestmark = pytest.mark.db


def test_les_requetes_de_diagnostic_s_executent(real_backend_db: str) -> None:
    """Chacune doit rendre une ligne, une colonne, sur le serveur réel."""
    backend = get_backend()
    requetes = backend.dialect.server_diagnostics_sql()
    assert requetes, f"{real_backend_db} ne déclare aucun diagnostic"

    connexion = backend.get_connection()
    try:
        for libelle, requete in requetes.items():
            curseur = connexion.cursor()
            try:
                curseur.execute(requete)
                ligne = curseur.fetchone()
            finally:
                curseur.close()
            assert ligne is not None, f"{libelle} n'a rien rendu sur {real_backend_db}"
    finally:
        backend.close_connection(connexion)


def test_le_diagnostic_rend_une_ligne_lisible(real_backend_db: str) -> None:
    from cli.project.doctor import _server_diagnostics  # pyright: ignore[reportPrivateUsage]

    backend = get_backend()
    connexion = backend.get_connection()
    try:
        details = _server_diagnostics(backend, connexion)
    finally:
        backend.close_connection(connexion)

    assert details, f"aucun détail rendu pour {real_backend_db}"
    assert "version" in details
    # Une seule ligne : le `@@VERSION` de SQL Server en compte plusieurs.
    assert "\n" not in details


def test_un_backend_muet_ne_fait_pas_echouer_le_diagnostic(real_backend_db: str) -> None:
    """Un backend qui ne sait rien dire reste correct : le diagnostic se tait."""
    from cli.project.doctor import _server_diagnostics  # pyright: ignore[reportPrivateUsage]

    class _Muet:
        class dialect:  # noqa: N801 — imite l'attribut du backend
            @staticmethod
            def server_diagnostics_sql() -> dict[str, str]:
                return {}

    assert _server_diagnostics(_Muet(), None) == ""


def test_une_requete_refusee_est_omise_et_non_propagee(real_backend_db: str) -> None:
    """Le compte applicatif est en DML strict : un refus est normal, pas une panne."""
    from cli.project.doctor import _server_diagnostics  # pyright: ignore[reportPrivateUsage]

    backend = get_backend()

    class _Bancal:
        dialect = type(
            "d", (),
            {"server_diagnostics_sql": staticmethod(lambda: {
                "version": backend.dialect.server_diagnostics_sql()["version"],
                "interdit": "SELECT value FROM table_qui_n_existe_pas",
            })},
        )()

    connexion = backend.get_connection()
    try:
        details = _server_diagnostics(_Bancal(), connexion)
    finally:
        backend.close_connection(connexion)

    assert "version" in details
    assert "interdit" not in details
