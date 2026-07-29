"""DIALECT-QUOTE-IDENTIFIER-ESCAPE-001 : le délimiteur doit être doublé.

Les quatre dialectes interpolaient le nom sans toucher au délimiteur :

    MariaDB      a`b  ->  `a`b`
    SQLite       a"b  ->  "a"b"
    PostgreSQL   a"b  ->  "a"b"
    SQL Server   a]b  ->  [a]b]

Dans chaque cas la citation se referme au premier délimiteur rencontré et la
fin du nom devient de la syntaxe.

Ce défaut n'est **pas atteignable** par le chemin normal de Forge : les
identifiants sont contraints en amont par `^[a-z][a-z0-9_]*$` dans les
schémas JSON et par `_IDENTIFIER_RE` dans `forge_mvc_entities.service`. Le
correctif relève de la défense en profondeur et du principe 10, une API
publique engageant sa complétude pour toute entrée, pas seulement pour celles
qu'un appelant bien élevé lui présente.

Le contrat `Dialect` gagne au passage `supports_transactional_ddl`, qui vit
dans le même voisinage : voir `test_migration_failure_report_001.py`.
"""
from __future__ import annotations

import pytest

from core.database.backend import Dialect


def _dialects() -> "list[tuple[str, object]]":
    """Les dialectes installés, sautés individuellement si le paquet manque."""
    trouves: "list[tuple[str, object]]" = []
    for nom, module, classe in [
        ("mariadb", "forge_mvc_mariadb.dialect", "MariaDBDialect"),
        ("sqlite", "forge_mvc_sqlite.dialect", "SQLiteDialect"),
        ("postgres", "forge_mvc_postgres.dialect", "PostgreSQLDialect"),
        ("mssql", "forge_mvc_mssql.dialect", "MSSQLDialect"),
    ]:
        try:
            importe = __import__(module, fromlist=[classe])
        except ImportError:  # pragma: no cover - dépend des paquets installés
            continue
        trouves.append((nom, getattr(importe, classe)()))
    return trouves


DIALECTES = _dialects()
IDS = [nom for nom, _ in DIALECTES]

# Par dialecte : délimiteur ouvrant, délimiteur fermant, forme doublée du
# fermant. Seul SQL Server est asymétrique, et seul son crochet **fermant**
# referme la citation ; l'ouvrant est ordinaire à l'intérieur.
DELIMITEURS = {
    "mariadb": ("`", "`", "``"),
    "sqlite": ('"', '"', '""'),
    "postgres": ('"', '"', '""'),
    "mssql": ("[", "]", "]]"),
}


def _decite(nom: str, rendu: str) -> str:
    """Retire la citation et défait le doublement : l'inverse exact attendu."""
    ouvrant, fermant, double = DELIMITEURS[nom]
    assert rendu.startswith(ouvrant) and rendu.endswith(fermant), (
        f"{nom} n'a pas produit une citation bien formée : {rendu!r}"
    )
    return rendu[1:-1].replace(double, fermant)


# ── Le défaut corrigé ────────────────────────────────────────────────────────

@pytest.mark.parametrize(("nom", "dialecte"), DIALECTES, ids=IDS)
def test_le_delimiteur_est_double(nom: str, dialecte: object) -> None:
    _, fermant, double = DELIMITEURS[nom]

    rendu: str = dialecte.quote_identifier(f"a{fermant}b")  # pyright: ignore[reportAttributeAccessIssue]

    assert double in rendu, f"{nom} laisse son délimiteur refermer la citation"


@pytest.mark.parametrize(("nom", "dialecte"), DIALECTES, ids=IDS)
@pytest.mark.parametrize("motif", ["a{d}b", "a{d}b{d}c", "{d}debut", "fin{d}", "{d}{d}{d}"])
def test_la_citation_se_defait_exactement(
    nom: str, dialecte: object, motif: str,
) -> None:
    """L'invariant : décite puis dédouble doit rendre le nom d'origine.

    Compter les délimiteurs ne marcherait pas, la forme doublée en étant
    elle-même faite. C'est l'aller-retour qui prouve que la citation est bien
    formée et que rien n'a fui hors d'elle.
    """
    _, fermant, _ = DELIMITEURS[nom]
    nom_source = motif.format(d=fermant)

    rendu: str = dialecte.quote_identifier(nom_source)  # pyright: ignore[reportAttributeAccessIssue]

    assert _decite(nom, rendu) == nom_source


# ── Ce qui ne doit pas changer ───────────────────────────────────────────────

@pytest.mark.parametrize(("nom", "dialecte"), DIALECTES, ids=IDS)
@pytest.mark.parametrize("identifiant", ["users", "created_at", "t2", "a_b_c"])
def test_les_identifiants_ordinaires_sont_inchanges(
    nom: str, dialecte: object, identifiant: str,
) -> None:
    rendu: str = dialecte.quote_identifier(identifiant)  # pyright: ignore[reportAttributeAccessIssue]

    assert rendu[1:-1] == identifiant


@pytest.mark.parametrize(("nom", "dialecte"), DIALECTES, ids=IDS)
def test_les_delimiteurs_des_autres_dialectes_sont_ordinaires(
    nom: str, dialecte: object,
) -> None:
    """Doubler le délimiteur d'un voisin corromprait le nom.

    SQL Server est le cas instructif : à l'intérieur de `[...]`, le crochet
    **ouvrant** n'a rien de spécial, seul le fermant referme la citation.
    """
    _, fermant, _ = DELIMITEURS[nom]
    etrangers = [c for c in ("`", '"', "]", "[") if c != fermant]

    for caractere in etrangers:
        rendu: str = dialecte.quote_identifier(f"a{caractere}b")  # pyright: ignore[reportAttributeAccessIssue]
        assert rendu[1:-1] == f"a{caractere}b", (
            f"{nom} a touché à {caractere!r}, qui ne lui appartient pas"
        )


# ── Le contrat ───────────────────────────────────────────────────────────────

def test_le_contrat_exige_le_doublement() -> None:
    """La règle vit dans le contrat, sinon un cinquième backend la manquerait."""
    doc = Dialect.quote_identifier.__doc__ or ""

    assert "doublé" in doc
