"""Surface base des opt-ins non exercée jusqu'ici (OPTIN-SURFACE-COVERAGE-001).

Le pré-mortem d'avant rc6 a mesuré, opt-in par opt-in, la part de la surface
touchant la base réellement **exécutée** contre un serveur. Le relevé était net :

    rbac        15 fonctions,  0 exercée
    admin       15 fonctions,  9 exercées
    images       8 fonctions,  3 exercées

C'est cette mesure qui a mené au défaut de création du back-office
(`ADMIN-MANAGED-TIMESTAMPS-001`) et à celui de l'horodatage des médias
(`IMAGES-MEDIA-TIMESTAMP-UTC-001`), tous deux invisibles d'une suite verte
parce que les tests des paquets exerçaient la **construction** du SQL et jamais
son effet.

Ce fichier ferme les trous restants. Il ne rapporte aucun défaut, et c'est un
résultat en soi : ces chemins se comportent à l'identique sur les trois
serveurs. Il existe pour que cela le reste.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from core.database.table_ddl import Column, TableDefinition
from core.database.timestamps import utc_now
from forge_mvc_testing.real_db import tables_temporaires

# ---------------------------------------------------------------------------
# forge-mvc-admin : lecture, pagination, comptage, suppression
# ---------------------------------------------------------------------------

ARTICLE = TableDefinition(
    name="article_couverture",
    columns=[
        Column("id", "identity"),
        Column("titre", "string", length=120),
        Column("created_at", "datetime"),
        Column("updated_at", "datetime"),
    ],
    primary_key=["id"],
)


def _ressource() -> Any:
    from forge_mvc_admin.resources import AdminResource

    return AdminResource(
        entity="Article",
        slug="articles",
        label="Article",
        plural_label="Articles",
        list_fields=("titre",),
        form_fields=("titre",),
        table="article_couverture",
        timestamps=True,
    )


@pytest.fixture
def articles(real_backend_db: str):
    pytest.importorskip("forge_mvc_admin")
    with tables_temporaires(ARTICLE) as db:
        maintenant = utc_now()
        for titre in ("Alpha", "Beta", "Gamma"):
            db.execute(
                "INSERT INTO article_couverture (titre, created_at, updated_at) "
                "VALUES (?, ?, ?)",
                (titre, maintenant, maintenant),
            )
        yield db


def test_admin_compte_pagine_lit_et_supprime(articles: Any) -> None:
    """Les quatre lectures du back-office, contre un vrai moteur.

    La pagination compte double : sa clause vient du dialecte, et T-SQL exige
    un `ORDER BY` que MariaDB tolère absent.
    """
    from forge_mvc_admin.query import count_rows, delete_row, get_row, list_rows

    fetch_one = lambda sql, params: articles.fetch_one(sql, tuple(params))  # noqa: E731
    fetch_all = lambda sql, params: articles.fetch_all(sql, tuple(params))  # noqa: E731
    execute = lambda sql, params: articles.execute(sql, tuple(params))  # noqa: E731

    assert count_rows(_ressource(), fetch_one) == 3
    assert len(list_rows(_ressource(), fetch_all, limit=2, offset=0)) == 2

    ligne = get_row(_ressource(), fetch_one, pk_value=1)
    assert ligne is not None and ligne["titre"] == "Alpha"

    assert delete_row(_ressource(), execute, pk_value=1) == 1
    assert count_rows(_ressource(), fetch_one) == 2


# ---------------------------------------------------------------------------
# forge-mvc-images : rattachement, position, texte alternatif, suppression
# ---------------------------------------------------------------------------


@pytest.fixture
def medias(real_backend_db: str):
    pytest.importorskip("forge_mvc_images")
    from forge_mvc_images.tables import MEDIA

    with tables_temporaires(MEDIA) as db:
        yield db


def test_images_attache_ordonne_decrit_et_supprime(medias: Any) -> None:
    """Les cinq fonctions du dépôt de médias qui n'avaient jamais tourné en base."""
    from forge_mvc_images.media_repository import (
        attach_media_to_entity,
        create_media_record,
        delete_media_record,
        get_media_record,
        list_media_for_entity,
        update_media_alt_text,
        update_media_position,
    )

    premier = create_media_record(
        entity_name="article", entity_id=1, path="a/1.jpg",
        original_name="1.jpg", mime_type="image/jpeg", size=10, db=medias,
    )
    update_media_alt_text(premier, "Une photo", db=medias)
    update_media_position(premier, 5, db=medias)

    # `attach_media_to_entity` attend un objet de téléversement, pas un chemin.
    televerse = SimpleNamespace(
        path="a/2.jpg", original_name="2.jpg", mime_type="image/png", size=20
    )
    second = attach_media_to_entity(
        televerse, entity_name="article", entity_id=2, db=medias
    )

    lu = get_media_record(premier, db=medias)
    assert lu is not None
    assert lu["alt_text"] == "Une photo"
    assert lu["position"] == 5

    attaches = list_media_for_entity("article", 2, db=medias)
    assert [m["id"] for m in attaches] == [second]

    assert delete_media_record(premier, db=medias) is True
    assert get_media_record(premier, db=medias) is None
