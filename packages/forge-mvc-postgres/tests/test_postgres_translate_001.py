"""POSTGRES-TRANSLATE-001 — traduction des paramètres ? -> %s (ADR-054)."""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_postgres")
from forge_mvc_postgres.translate import translate_placeholders as t  # noqa: E402


def test_placeholders_simples() -> None:
    assert t("SELECT * FROM contact WHERE id = ?") == "SELECT * FROM contact WHERE id = %s"
    assert t("INSERT INTO t (a, b) VALUES (?, ?)") == "INSERT INTO t (a, b) VALUES (%s, %s)"


def test_pourcent_litteral_double() -> None:
    assert t("WHERE nom LIKE '%a%'") == "WHERE nom LIKE '%%a%%'"
    assert t("WHERE x = ? AND y LIKE ?") == "WHERE x = %s AND y LIKE %s"


def test_point_interrogation_dans_chaine_preserve() -> None:
    # Un « ? » à l'intérieur d'un littéral chaîne n'est pas un paramètre.
    assert t("SELECT 'a?b' WHERE id = ?") == "SELECT 'a?b' WHERE id = %s"


def test_apostrophe_echappee_dans_chaine() -> None:
    assert t("WHERE nom = 'O''Brien' AND id = ?") == "WHERE nom = 'O''Brien' AND id = %s"
