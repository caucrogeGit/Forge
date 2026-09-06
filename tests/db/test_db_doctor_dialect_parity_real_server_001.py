"""DB-DOCTOR-DIALECT-PARITY-001, mesure sur serveurs réels.

`forge doctor` rend une ligne « version, encodage, collation, base, compte » :
une connexion réussie ne dit pas qu'une version est assez récente, que le jeu
de caractères est de l'UTF-8, ni sous quel compte on est réellement entré
(`DB-DOCTOR-001`).

Trois de ces lignes disaient autre chose que ce que leur libellé annonce, et
seul un serveur réel pouvait le montrer.

`compte` interrogeait `CURRENT_USER` sur SQL Server, qui y est l'utilisateur de
**base** et non le compte de connexion : la mesure rendait `dbo` alors que la
session était ouverte en `sa`. Le diagnostic existe pour révéler un compte
inattendu, et il rendait la seule valeur qui ne peut jamais l'être.

`collation` y interrogeait le **serveur** et non la base, qui peut porter la
sienne, et c'est elle qui décide du tri des textes qu'elle contient.

`encodage` y manquait. SQL Server n'a pas de réglage d'encodage : c'est la page
de codes de la collation qui décide, et le serveur de test s'est révélé en page
1252, où tout caractère non représentable devient « ? » dans les colonnes
`VARCHAR`. Le taire laissait croire à un serveur en UTF-8.

PostgreSQL, lui, ne donnait pas de collation là où les deux autres en donnent.
"""
from __future__ import annotations

from typing import Any

import pytest

#: Diagnostics qu'un serveur doit savoir rendre, tous backends confondus.
#:
#: SQLite n'y figure pas : sans compte ni base nommée, la question n'a pas de
#: sens pour un backend fichier, et exiger la ligne la ferait inventer.
ATTENDUS = ("version", "encodage", "collation", "base", "compte")


def _diagnostics() -> "dict[str, str]":
    from core.database.backend import get_backend

    return get_backend().dialect.server_diagnostics_sql()


def _mesure(libelle: str) -> Any:
    from core.database.backend import get_backend

    backend = get_backend()
    connexion = backend.get_connection()
    try:
        curseur = connexion.cursor()
        try:
            curseur.execute(_diagnostics()[libelle])
            ligne = curseur.fetchone()
        finally:
            curseur.close()
    finally:
        backend.close_connection(connexion)
    if ligne is None:
        return None
    return ligne.get("value") if isinstance(ligne, dict) else ligne[0]


@pytest.mark.parametrize("libelle", ATTENDUS)
def test_chaque_serveur_declare_les_cinq_diagnostics(
    real_backend_db: str, libelle: str
) -> None:
    """L'un en déclarait quatre, l'autre quatre autres."""
    assert libelle in _diagnostics(), f"{real_backend_db} ne déclare pas « {libelle} »"


@pytest.mark.parametrize("libelle", ATTENDUS)
def test_chaque_diagnostic_rend_une_valeur(real_backend_db: str, libelle: str) -> None:
    """Une requête déclarée mais refusée par le pilote ne servirait à rien.

    C'est le cas qu'un test unitaire ne peut pas voir : `COLLATIONPROPERTY`
    rend un `sql_variant` que le pilote ODBC ne sait pas convertir, et la ligne
    disparaissait en silence de la sortie de `doctor`.
    """
    valeur = _mesure(libelle)

    assert valeur is not None and str(valeur).strip(), (
        f"{real_backend_db} ne rend rien pour « {libelle} »")


class TestCompte:

    def test_le_compte_rendu_est_celui_de_la_connexion(
        self, real_backend_db: str
    ) -> None:
        """Sur SQL Server, `dbo` était rendu pour tout administrateur.

        La comparaison porte sur le début du nom : MariaDB rend
        `root@localhost`, où l'hôte n'est pas dans la configuration.
        """
        import os

        attendu = os.environ.get("DB_APP_LOGIN", "")
        rendu = str(_mesure("compte"))

        assert attendu, "la configuration de test doit nommer le compte"
        assert rendu.split("@")[0].lower() == attendu.lower(), (
            f"{real_backend_db} rend « {rendu} » pour une connexion « {attendu} »")

    def test_le_compte_rendu_n_est_pas_un_role_generique(
        self, real_backend_db: str
    ) -> None:
        """`dbo` ne distingue personne : c'est ce que tout sysadmin y devient."""
        assert str(_mesure("compte")).lower() != "dbo"


class TestEncodage:

    def test_l_encodage_est_nomme_et_non_devine(self, real_backend_db: str) -> None:
        """Un serveur qui n'est pas en UTF-8 doit le dire, pas se taire."""
        rendu = str(_mesure("encodage")).lower()

        assert "utf" in rendu or "page de codes" in rendu, (
            f"{real_backend_db} rend un encodage indéchiffrable : {rendu!r}")
