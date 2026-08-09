"""Intégration du store de paramètres sur les trois serveurs (SETTINGS-DB-INTEGRATION-001).

Vérifie le contrat SQL réel face au moteur, là où les tests unitaires passent par
un adaptateur en mémoire.

## Ce qui a changé (`TEST-PACKAGE-INTEGRATION-REAL-LAYER-001`)

Ce fichier montait auparavant sa propre connexion MariaDB et l'enveloppait dans
un adaptateur écrit à la main. Deux conséquences, aucune voulue.

Il ne tournait que sur **MariaDB**, alors que l'ADR-084 donne les quatre
backends au niveau plein. Et l'adaptateur court-circuitait la **vraie couche
d'accès** `core.database.db`, donc la qualification d'erreur de Forge : une
violation d'unicité y remontait sous sa forme pilote et non sous la forme
portable `UniqueViolationError`. C'est précisément cet écart qui a caché deux
défauts du magasin anti-rejeu MFA pendant tout un cycle.

Les tests passent désormais par `real_backend_db`, donc par la couche réelle,
et chacun s'exécute **trois fois**, une par serveur.
"""
from __future__ import annotations

from collections.abc import Iterator

import pytest

pytest.importorskip("forge_mvc_settings")

from forge_mvc_settings import (
    delete_setting,
    get_all_settings,
    get_setting,
    set_setting,
)

from forge_mvc_testing.real_db import tables_temporaires


@pytest.fixture
def settings_db(real_backend_db: str) -> Iterator[None]:
    """Table des paramètres créée par sa DDL dialectale, sur le serveur du cas."""
    from forge_mvc_settings.tables import APP_SETTINGS

    with tables_temporaires(APP_SETTINGS):
        yield


@pytest.mark.usefixtures("settings_db")
def test_la_ddl_est_acceptee_par_le_moteur() -> None:
    """La table a été créée par la fixture ; un set/get prouve que le moteur l'accepte."""
    set_setting("etablissement.nom", "Collège X")
    assert get_setting("etablissement.nom") == "Collège X"


@pytest.mark.usefixtures("settings_db")
def test_l_upsert_et_les_types_traversent_le_moteur() -> None:
    """Écrire deux fois la même clé la met à jour, sans doublon ni erreur.

    C'est l'opération que `ON DUPLICATE KEY UPDATE`, propre à MySQL et MariaDB,
    rendait autrefois non portable.
    """
    set_setting("qcm.duree", 30)
    set_setting("qcm.duree", 45)
    set_setting("maintenance", True)
    assert get_setting("qcm.duree") == 45
    assert get_setting("maintenance") is True
    assert get_all_settings() == {"maintenance": True, "qcm.duree": 45}


@pytest.mark.usefixtures("settings_db")
def test_la_suppression_traverse_le_moteur() -> None:
    set_setting("temp", "x")
    assert delete_setting("temp") is True
    assert get_setting("temp") is None
