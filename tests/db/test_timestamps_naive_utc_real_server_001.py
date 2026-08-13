"""Les horodatages gérés sont écrits en UTC sur les trois moteurs (TIMESTAMPS-NAIVE-UTC-001).

L'ADR-081 a tranché que l'autorité sur les horodatages est Python, jamais le
moteur. Il n'avait pas dit sous quelle **forme** la valeur devait être passée, et
cette omission a coûté deux heures.

Les colonnes de Forge sont des `DATETIME` **sans fuseau**. Passer un `datetime`
conscient du fuseau y laisse le pilote décider, et chaque pilote décide
autrement. Mesuré avant correctif, serveur en UTC+2 :

    mariadb     aware -> 12:14:07  (écart 0 s)      naïf -> 12:14:07  (0 s)
    postgres    aware -> 14:14:07  (écart 7200 s)   naïf -> 12:14:07  (0 s)
    mssql       aware -> 12:14:07  (écart 0 s)      naïf -> 12:14:07  (0 s)

PostgreSQL convertit vers l'heure locale du serveur. Une base portait donc deux
référentiels horaires selon le backend, sans que rien ne le signale : la valeur
est plausible, seulement fausse de deux heures.

Tous les écrivains d'horodatage de Forge passaient la forme consciente : le
socle d'authentification, le back-office, le dépôt de médias, et le modèle
engendré par `make:crud`. Le défaut précède ce cycle pour le dernier.

Ce fichier vérifie la propriété **là où elle se joue**, contre les trois
serveurs, et non sur la forme du code.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from core.database.table_ddl import Column, TableDefinition
from core.database.timestamps import utc_now
from forge_mvc_testing.real_db import tables_temporaires

pytestmark = pytest.mark.db

#: Deux minutes : large pour l'horloge d'un conteneur, mille fois trop étroit
#: pour laisser passer un décalage de fuseau, qui vaut au moins une heure.
_TOLERANCE_SECONDES = 120

TABLE = TableDefinition(
    name="horodatage_sonde",
    columns=[Column("id", "identity"), Column("quand", "datetime")],
    primary_key=["id"],
)


@pytest.fixture
def table(real_backend_db: str):
    with tables_temporaires(TABLE) as db:
        yield db


def _ecart_a_l_utc(valeur: Any) -> float:
    if isinstance(valeur, str):
        valeur = datetime.fromisoformat(valeur)
    return abs((valeur - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())


def test_utc_now_traverse_le_moteur_sans_decalage(table: Any) -> None:
    """LE test du ticket : deux heures d'écart sur PostgreSQL avant correctif."""
    table.execute("INSERT INTO horodatage_sonde (quand) VALUES (?)", (utc_now(),))

    ligne = table.fetch_one("SELECT quand FROM horodatage_sonde", ())
    assert ligne is not None
    ecart = _ecart_a_l_utc(ligne["quand"])

    assert ecart < _TOLERANCE_SECONDES, (
        f"l'horodatage relu s'écarte de {ecart:.0f} s de l'UTC : le pilote a "
        "converti la valeur, donc la base porte un autre référentiel"
    )


def test_la_forme_consciente_est_bien_celle_qui_derape(table: Any) -> None:
    """Le contre-exemple, conservé pour que la règle ne soit pas prise pour un rite.

    Sans lui, `utc_now()` ressemblerait à une précaution superstitieuse. Ce test
    ne juge pas le résultat, il l'enregistre : sur les moteurs qui ne
    convertissent pas, les deux formes coïncident, et c'est bien pour cela que
    le défaut a pu vivre.
    """
    consciente = datetime.now(timezone.utc)
    table.execute("INSERT INTO horodatage_sonde (quand) VALUES (?)", (consciente,))
    table.execute("INSERT INTO horodatage_sonde (quand) VALUES (?)", (utc_now(),))

    lignes = table.fetch_all("SELECT quand FROM horodatage_sonde ORDER BY id", ())
    naif = lignes[1]["quand"]

    assert _ecart_a_l_utc(naif) < _TOLERANCE_SECONDES, (
        "la forme naïve doit traverser sans conversion sur TOUS les moteurs"
    )


def test_utc_now_ne_porte_pas_de_fuseau() -> None:
    """La propriété tient sans base : c'est elle qui rend le reste vrai."""
    valeur = utc_now()

    assert valeur.tzinfo is None
    # Et c'est bien de l'UTC, pas l'heure locale du poste.
    assert abs((valeur - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds()) < 5


def test_aucun_ecrivain_ne_pose_la_forme_consciente() -> None:
    """Une seule façon officielle (principe 11), et un relevé qui le tient.

    Le piège est que la forme consciente **paraît plus juste**, puisqu'elle
    porte l'information de fuseau. Elle l'est en Python, pas au passage du
    pilote.
    """
    import ast
    from pathlib import Path

    racine = Path(__file__).resolve().parent.parent.parent
    fautes: list[str] = []
    cibles = [
        racine / "cli" / "security" / "auth.py",
        racine / "packages" / "forge-mvc-admin" / "forge_mvc_admin" / "query.py",
        racine / "packages" / "forge-mvc-images" / "forge_mvc_images" / "media_repository.py",
        racine / "packages" / "forge-mvc-entities" / "forge_mvc_entities" / "crud" / "model_builder.py",
    ]
    for chemin in cibles:
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        for noeud in ast.walk(arbre):
            # Appel `datetime.now(...)` : seul `utc_now()` doit subsister.
            if (
                isinstance(noeud, ast.Call)
                and isinstance(noeud.func, ast.Attribute)
                and noeud.func.attr == "now"
                and isinstance(noeud.func.value, ast.Name)
                and noeud.func.value.id == "datetime"
            ):
                fautes.append(f"{chemin.relative_to(racine)}:{noeud.lineno}")
    assert not fautes, (
        "Ces écrivains posent `datetime.now(...)` au lieu de `utc_now()` : la "
        "valeur sera convertie par le pilote sur PostgreSQL.\n  "
        + "\n  ".join(fautes)
    )
