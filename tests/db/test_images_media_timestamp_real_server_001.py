"""L'horodatage des médias est en UTC, posé par Python (IMAGES-MEDIA-TIMESTAMP-UTC-001).

`forge-mvc-images` écrivait `CreatedAt` avec `CURRENT_TIMESTAMP`, une expression
SQL. C'est le moteur qui décidait donc de la valeur, ce que l'ADR-081 refuse
explicitement au motif que cela introduit une double horloge.

Mesuré avant correctif, sur les serveurs réels :

    mariadb   écrit=13:52:52          utc=11:52:52     écart = 7199 s
    mssql     écrit=11:52:53.090      utc=11:52:53.089  écart = 0 s

Sur MariaDB, `CURRENT_TIMESTAMP` rend l'heure **locale du serveur** : un média
enregistré à midi UTC était daté de 14 h, dans une base où tout le reste est en
UTC. Deux référentiels horaires coexistaient donc, et lequel s'appliquait
dépendait du backend.

Ce fichier est aussi la première épreuve de `forge-mvc-images` contre un serveur
réel : le paquet écrivait en base sans qu'aucun test ne l'exerce ailleurs qu'en
mémoire.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

pytest.importorskip("forge_mvc_images")

from forge_mvc_images.media_repository import (
    create_media_record,
    get_media_record,
    list_media_for_entity,
)

from forge_mvc_testing.real_db import tables_temporaires

#: Deux minutes : large pour une horloge de conteneur, mille fois trop étroit
#: pour laisser passer un décalage de fuseau, qui vaut au moins une heure.
_TOLERANCE_SECONDES = 120


@pytest.fixture
def table(real_backend_db: str):
    from forge_mvc_images.tables import MEDIA

    with tables_temporaires(MEDIA) as db:
        yield db


def _creer(db: Any, chemin: str = "articles/1/photo.jpg") -> int:
    return create_media_record(
        entity_name="article",
        entity_id=1,
        path=chemin,
        original_name="photo.jpg",
        mime_type="image/jpeg",
        size=1024,
        db=db,
    )


def test_l_horodatage_est_en_utc(table: Any) -> None:
    """LE test du ticket : deux heures d'écart sur MariaDB avant correctif."""
    avant = datetime.now(timezone.utc).replace(tzinfo=None)

    _creer(table)

    # Alias entre guillemets : sans lui, PostgreSQL replie `CreatedAt` en
    # `createdat` et la clé lue n'existe pas (`CRUD-PG-COLUMN-CASE-001`).
    ligne = table.fetch_one('SELECT CreatedAt AS "CreatedAt" FROM media', ())
    assert ligne is not None
    ecrit = ligne["CreatedAt"]
    if isinstance(ecrit, str):
        ecrit = datetime.fromisoformat(ecrit)
    ecart = abs((ecrit - avant).total_seconds())

    assert ecart < _TOLERANCE_SECONDES, (
        f"l'horodatage du média s'écarte de {ecart:.0f} s de l'UTC : il n'est "
        "pas dans le même référentiel que le reste de la base"
    )


def test_l_insertion_ne_delegue_plus_au_moteur() -> None:
    """Contrôle direct : plus d'expression SQL dans la requête.

    Une seule ligne suffisait à rouvrir le défaut, et elle avait l'air
    inoffensive.
    """
    import inspect

    from forge_mvc_images import media_repository

    # Les lignes de COMMENTAIRE sont écartées : elles citent l'expression pour
    # dire qu'elle n'est plus employée, et les juger reviendrait à juger de la
    # prose. Le même piège s'est produit deux fois dans ce cycle.
    source = "\n".join(
        ligne for ligne in inspect.getsource(media_repository.create_media_record).splitlines()
        if not ligne.lstrip().startswith("#")
    )

    assert "CURRENT_TIMESTAMP" not in source, (
        "l'horodatage est de nouveau délégué au moteur : l'autorité appartient "
        "à Python (ADR-081)"
    )


def test_la_surface_publique_traverse_le_moteur(table: Any) -> None:
    """Première épreuve réelle du paquet : il écrivait sans être exercé en base.

    Les clés rendues sont normalisées en snake_case par le dépôt lui-même, ce
    qui le protège du repli de casse de PostgreSQL.
    """
    identifiant = _creer(table)

    lu = get_media_record(identifiant, db=table)
    liste = list_media_for_entity("article", 1, db=table)

    assert lu is not None
    assert lu["path"] == "articles/1/photo.jpg"
    assert lu["mime_type"] == "image/jpeg"
    assert [m["id"] for m in liste] == [identifiant]
