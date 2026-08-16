"""AUTH-DDL-TESTS-SOURCE-001 : la fixture SQL du projet d'exemple suit la source.

Le DDL du socle Auth existe en trois copies.
La spec déclarative de `cli.security.auth_sql`, que `auth:init` rend par
dialecte ; la constante canonique de `cli.security.auth` ; et la fixture
`tests/fixtures/app/mvc/models/sql/`, écrite à la main.

Les deux premières sont déjà verrouillées l'une à l'autre par la parité stricte
de `test_auth_init_dialect_ddl_001`. La troisième ne l'était par rien, et elle a
dérivé : `users.sql` a gardé `email NOT NULL UNIQUE` et `last_login_at` alors que
l'ADR-089 a déplacé l'identité vers `login` et que l'ADR-091 a retiré la colonne.
Neuf assertions affirmaient le contrat de la table en lisant cette copie, dont
deux affirmaient l'inverse de la règle en vigueur.

Ce garde-fou ferme la dérive pour toute la famille, pas pour le seul cas trouvé.
Le relevé vient du système de fichiers et la résolution d'une convention de nom,
jamais d'une liste écrite à la main : un fichier ajouté demain est couvert sans
qu'on y pense.

Portée : le dialecte MariaDB, seul que la fixture porte. Les trois autres restent
couverts par la parité dialectale de `test_auth_init_dialect_ddl_001`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.security import auth


PROJECT_ROOT = Path(__file__).parent.parent
FIXTURE_SQL_DIR = PROJECT_ROOT / "tests" / "fixtures" / "app" / "mvc" / "models" / "sql"

# Fichiers de la fixture qui n'ont pas de constante dans `cli.security.auth`,
# avec la raison. Une exemption est une dette écrite, pas un silence.
EXEMPTIONS: dict[str, str] = {
    "mail_log.sql": (
        "Le DDL du journal d'emails appartient à l'opt-in forge-mvc-mail depuis "
        "son extraction du cœur (ADR-022) ; le socle Auth n'en porte pas la "
        "constante. Plus aucun test ne lit ce fichier : à résoudre contre le "
        "paquet mail, ou à retirer, dans un ticket de l'opt-in."
    ),
}


def _constant_name(sql_filename: str) -> str:
    """`users.sql` donne `USERS_SQL`, la convention des constantes du socle."""
    return sql_filename.removesuffix(".sql").upper() + "_SQL"


def _resolve(sql_filename: str) -> str | None:
    constant = getattr(auth, _constant_name(sql_filename), None)
    return constant if isinstance(constant, str) else None


def _fixture_files() -> list[Path]:
    return sorted(FIXTURE_SQL_DIR.glob("*.sql"))


def test_le_dossier_de_fixture_existe_et_porte_du_sql() -> None:
    # Sans ce contrôle, un dossier déplacé rendrait tous les tests paramétrés
    # ci-dessous vides, donc verts, et le garde-fou disparaîtrait en silence.
    assert FIXTURE_SQL_DIR.is_dir()
    assert _fixture_files()


@pytest.mark.parametrize("sql_file", [item.filename for item in auth.AUTH_SQL_FILES])
def test_la_convention_de_nom_resout_les_constantes_du_socle(sql_file: str) -> None:
    """La résolution par convention vaut pour les sept fichiers de `auth:init`.

    C'est ce qui autorise à ne pas écrire la table de correspondance à la main.
    Renommer une constante sans renommer son fichier casse ici, au bon endroit.
    """
    assert _resolve(sql_file) is not None, (
        f"{sql_file} ne se résout pas en {_constant_name(sql_file)} : "
        "la convention de nom des constantes du socle est rompue."
    )


def test_chaque_fichier_de_la_fixture_est_resolu_ou_exempte() -> None:
    """Rien ne saute en silence, et c'est le point.

    Un fichier que le garde-fou ne sait pas rattacher doit faire échouer, sinon
    il serait ignoré tout en paraissant couvert.
    """
    orphelins = [
        path.name
        for path in _fixture_files()
        if _resolve(path.name) is None and path.name not in EXEMPTIONS
    ]
    assert not orphelins, (
        f"Fichiers SQL de la fixture ni résolus ni exemptés : {orphelins}. "
        "Ajouter la constante correspondante, ou une exemption motivée."
    )


def test_les_exemptions_visent_des_fichiers_existants() -> None:
    """Une exemption dont le fichier a disparu est une dette morte, à retirer."""
    presents = {path.name for path in _fixture_files()}
    perimees = sorted(set(EXEMPTIONS) - presents)
    assert not perimees, (
        f"Exemptions devenues inutiles : {perimees}. Les retirer de EXEMPTIONS."
    )


@pytest.mark.parametrize(
    "sql_file",
    [path.name for path in _fixture_files() if _resolve(path.name) is not None],
)
def test_parite_stricte_fixture_egal_constante(sql_file: str) -> None:
    """La fixture est une copie exacte de la constante canonique.

    Égalité stricte et non normalisée : une copie se corrige en recopiant, et
    une tolérance aux espaces laisserait passer une divergence de mise en forme
    qu'un projet réel n'aurait pas.
    """
    constant = _resolve(sql_file)
    assert constant is not None  # garanti par le paramétrage
    actual = (FIXTURE_SQL_DIR / sql_file).read_text(encoding="utf-8")
    assert actual == constant, (
        f"{sql_file} de la fixture a dérivé de la constante canonique "
        f"{_constant_name(sql_file)}. Recopier la constante dans la fixture."
    )
