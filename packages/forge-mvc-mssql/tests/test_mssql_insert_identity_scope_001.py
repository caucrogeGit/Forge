# pyright: strict
"""MSSQL-INSERT-IDENTITY-SCOPE-001 — la détection de l'INSERT lit le SQL, pas son texte.

`MSSQL-INSERT-IDENTITY-001` lit l'identité dans le lot de l'INSERT, ce qui
suppose de reconnaître l'INSERT. La reconnaissance était textuelle : l'INSERT
devait commencer la chaîne, et le mot « output » n'importe où faisait renoncer.
Mesuré sur serveur réel, quatre formes sur sept perdaient donc leur identité en
silence, la ligne étant pourtant écrite :

    INSERT nu                              1
    indenté sur plusieurs lignes           3
    terminé par un point-virgule           7
    précédé d'un commentaire            None
    suivi d'un commentaire              None
    « output » dans un littéral         None
    « output » dans un commentaire      None

Le CRUD généré redirige vers `/show/{id}` avec cet identifiant, et le défaut
pénalisait exactement le SQL commenté que le principe 5 encourage.

La reconnaissance porte désormais sur un **squelette de mots-clés** : le
découpeur canonique du cœur (ADR-079) ôte les commentaires en respectant les
littéraux, puis littéraux et identifiants délimités sont vidés. Ce qui reste ne
contient que du code.

Curseur pyodbc factice : aucun pilote ODBC ni serveur requis. Le pendant sur
serveur réel est `tests/db/test_mssql_insert_identity_scope_real_server_001.py`.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_mssql")

from forge_mvc_mssql.backend import (  # noqa: E402
    _keyword_skeleton,
    _needs_identity_batch,
)

# Le curseur factice du ticket d'origine, réemployé plutôt que recopié : les
# deux tickets décrivent le même lot. Import non relatif, le dossier de tests
# n'étant pas un paquet (pytest insère son répertoire dans sys.path).
from test_mssql_adapter_lastrowid_001 import FakePyodbcCursor  # noqa: E402


# ── Les formes qui doivent être batchées ─────────────────────────────────────

@pytest.mark.parametrize("sql", [
    "INSERT INTO contact (nom) VALUES (?)",
    "insert into contact (nom) values (?)",
    "\n    INSERT INTO contact (nom)\n    VALUES (?)\n",
    "INSERT INTO contact (nom) VALUES (?);",
    "-- crée le contact\nINSERT INTO contact (nom) VALUES (?)",
    "/* crée le contact */ INSERT INTO contact (nom) VALUES (?)",
    "INSERT INTO contact (nom) VALUES (?) -- fin",
    "INSERT INTO contact (nom) VALUES (?) /* output attendu */",
    "INSERT INTO rapport (nom) VALUES ('output du script')",
    "INSERT INTO rapport ([output], nom) VALUES (?, ?)",
    'INSERT INTO rapport ("output", nom) VALUES (?, ?)',
])
def test_ces_formes_reclament_le_lot_d_identite(sql: str) -> None:
    assert _needs_identity_batch(sql) is True


# ── Les formes qui ne doivent pas l'être ─────────────────────────────────────

@pytest.mark.parametrize("sql", [
    "SELECT nom FROM contact",
    "UPDATE contact SET nom = ? WHERE id = ?",
    "DELETE FROM contact WHERE id = ?",
    "INSERT INTO contact (nom) OUTPUT INSERTED.id VALUES (?)",
    "INSERT INTO contact (nom) VALUES (?); SELECT SCOPE_IDENTITY()",
    "-- rien à insérer",
    "",
])
def test_ces_formes_sont_laissees_intactes(sql: str) -> None:
    assert _needs_identity_batch(sql) is False


def test_une_expression_de_table_commune_reste_hors_perimetre() -> None:
    """Limite assumée, écrite plutôt que découverte (règle B)."""
    sql = "WITH source AS (SELECT ? AS nom) INSERT INTO contact (nom) SELECT nom FROM source"

    assert _needs_identity_batch(sql) is False


# ── Le squelette de mots-clés ────────────────────────────────────────────────

def test_le_squelette_vide_les_commentaires() -> None:
    skeleton = _keyword_skeleton("INSERT INTO t (a) VALUES (?) -- output ici")

    assert "output" not in skeleton.lower()
    assert "INSERT" in skeleton


def test_le_squelette_vide_les_litteraux_sans_perdre_le_code() -> None:
    skeleton = _keyword_skeleton("INSERT INTO t (a) VALUES ('output du script')")

    assert "output" not in skeleton.lower()
    assert "INSERT INTO t (a) VALUES" in skeleton


def test_le_squelette_respecte_l_apostrophe_doublee() -> None:
    """Retour terrain 012 : l'apostrophe échappée ne doit pas décaler l'analyse."""
    skeleton = _keyword_skeleton("INSERT INTO t (a) VALUES ('l''output', ?)")

    assert "output" not in skeleton.lower()
    assert skeleton.count("?") == 1


def test_le_squelette_ne_confond_pas_un_apostrophe_de_commentaire() -> None:
    """Retour terrain 021 : une apostrophe en commentaire n'ouvre pas un littéral."""
    skeleton = _keyword_skeleton("-- l'insertion du contact\nINSERT INTO t (a) VALUES (?)")

    assert skeleton.lstrip().upper().startswith("INSERT")
    assert "?" in skeleton


def test_le_squelette_vide_les_identifiants_delimites() -> None:
    skeleton = _keyword_skeleton("INSERT INTO t ([output], [order]) VALUES (?, ?)")

    assert "output" not in skeleton.lower()
    assert "order" not in skeleton.lower()


def test_le_squelette_garde_la_clause_output_reelle() -> None:
    """Ce qui est du code doit rester : sinon on batcherait un statement à OUTPUT."""
    skeleton = _keyword_skeleton("INSERT INTO t (a) OUTPUT INSERTED.id VALUES (?)")

    assert "OUTPUT" in skeleton.upper()


# ── Le lot construit ─────────────────────────────────────────────────────────

def test_le_commentaire_de_fin_n_avale_plus_la_lecture_d_identite() -> None:
    """Collée à la suite, elle passait pour du commentaire et ne s'exécutait pas."""
    from forge_mvc_mssql.backend import _MsCursor

    fake = FakePyodbcCursor(identity=12)
    cur = _MsCursor(fake, dictionary=False)
    cur.execute("INSERT INTO contact (nom) VALUES (?) -- crée le contact", ("Ada",))

    envoye = fake.executed[0][0]
    ligne_identite = envoye.splitlines()[-1]

    assert ligne_identite.strip() == "; SELECT SCOPE_IDENTITY()"
    assert cur.lastrowid == 12


def test_le_texte_d_origine_est_conserve() -> None:
    """Forge n'améliore pas le SQL de l'appelant : il y ajoute, sans retrancher."""
    from forge_mvc_mssql.backend import _MsCursor

    fake = FakePyodbcCursor()
    cur = _MsCursor(fake, dictionary=False)
    origine = "-- crée le contact\nINSERT INTO contact (nom) VALUES (?)"
    cur.execute(origine, ("Ada",))

    assert fake.executed[0][0].startswith(origine)
