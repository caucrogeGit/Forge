"""IOT-DOCTOR-MISSING-TABLE-001 — détection portable d'une table absente.

Un diagnostic doit distinguer deux situations que l'exploitant ne traite pas de
la même façon : la migration oubliée, qui se répare par `forge migration:apply`,
et la base injoignable, qui se répare ailleurs. Les confondre est pire qu'un
silence, puisque le diagnostic désigne alors la mauvaise cause.

Aucun signal n'est portable, mesuré sur les quatre backends :

    MariaDB      mariadb.ProgrammingError       errno 1146, sqlstate 42S02
    SQLite       sqlite3.OperationalError       message « no such table »
    PostgreSQL   psycopg.errors.UndefinedTable  sqlstate 42P01
    SQL Server   pyodbc.ProgrammingError        numéro natif 208

**Le message de PostgreSQL est traduit.** Un serveur en français rend « la
relation ... n'existe pas », un serveur en anglais « relation ... does not
exist ». Une détection par le texte dépendrait donc de la langue du serveur, ce
qui n'est pas une propriété du programme. C'est le piège précis dans lequel la
détection de `forge-mvc-iot` était tombée, en cherchant la locution anglaise
« doesn't exist » de MariaDB.

Ce fichier suit `test_unique_violation_contract_001.py`, dont il reprend la
forme : le signal appartient au **backend**, qui connaît son pilote, et non au
`Dialect`, qui ne décrit que du SQL.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from forge_mvc_testing.source_scan import code_sans_prose

PROJECT_ROOT = Path(__file__).parent.parent

#: Les quatre backends officiels (ADR-054, tous au niveau plein depuis l'ADR-084).
BACKENDS = ("mariadb", "sqlite", "postgres", "mssql")


# ── Contrat ──────────────────────────────────────────────────────────────────


def test_le_protocole_backend_declare_la_methode() -> None:
    """La détection fait partie du contrat, pas d'un opt-in isolé."""
    from core.database.backend import DatabaseBackend

    assert hasattr(DatabaseBackend, "is_undefined_table_error")


def test_la_detection_nest_pas_sur_le_dialecte() -> None:
    """Frontière du contrat : `Dialect` décrit du SQL, pas des exceptions de pilote."""
    from core.database.backend import Dialect

    assert not hasattr(Dialect, "is_undefined_table_error"), (
        "Reconnaître une exception relève du pilote, donc de DatabaseBackend."
    )


def test_le_coeur_expose_un_helper_de_qualification() -> None:
    """Le même point d'entrée que pour le doublon, une seule façon de demander."""
    from core.database import qualify

    assert hasattr(qualify, "is_undefined_table_error")


@pytest.mark.parametrize("backend", BACKENDS)
def test_chaque_backend_implemente_la_methode(backend: str) -> None:
    """Une méthode déclarée mais non implémentée rendrait faux, donc silencieuse.

    C'est le mode de défaillance de ce contrat : le helper enveloppe l'appel et
    rend faux si le backend ne répond pas. Un backend oublié ne lèverait donc
    aucune erreur, il classerait simplement toute migration oubliée comme une
    panne.
    """
    chemin = (
        PROJECT_ROOT / "packages" / f"forge-mvc-{backend}"
        / f"forge_mvc_{backend}" / "backend.py"
    )
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))

    methodes = {
        n.name
        for classe in arbre.body
        if isinstance(classe, ast.ClassDef)
        for n in classe.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert "is_undefined_table_error" in methodes, (
        f"forge-mvc-{backend} n'implémente pas la détection : une migration "
        "oubliée y sera classée comme une base injoignable, sans erreur visible"
    )


# ── Le piège de la traduction ────────────────────────────────────────────────


def test_postgres_ne_detecte_pas_par_le_message() -> None:
    """LE piège du ticket : le message de PostgreSQL dépend de la langue du serveur.

    Mesuré sur le serveur local, configuré en français :

        la relation « iot_events » n'existe pas

    La locution anglaise « does not exist » n'y figure pas. Une détection par
    le texte serait donc vraie ou fausse selon un réglage du serveur, ce qui
    n'est pas une propriété du programme.
    """
    import inspect

    from forge_mvc_postgres.backend import PostgreSQLBackend

    # La docstring cite les deux formulations pour expliquer le piège : seul le
    # code est jugé (voir `forge_mvc_testing.source_scan`).
    rendu = code_sans_prose(
        inspect.getsource(PostgreSQLBackend.is_undefined_table_error)
    )

    assert "does not exist" not in rendu and "n'existe pas" not in rendu, (
        "la détection PostgreSQL passe par le message, qui est traduit :\n" + rendu
    )
    assert "42P01" in rendu, "le SQLSTATE est le seul signal stable sur PostgreSQL"
    assert "sqlstate" in rendu.lower()


#: Tous les modules qui distinguent « table absente » d'une panne. La liste a
#: grandi après coup : le premier ticket n'avait converti que `forge-mvc-iot`,
#: et un audit de ses propres correctifs a trouvé deux adoptants oubliés
#: (`OPTIN-TIMESTAMP-WIDEN-001`). Réparer un seul site est le défaut que ce
#: relevé existe pour empêcher.
DETECTEURS = (
    "packages/forge-mvc-iot/forge_mvc_iot/cli/doctor.py",
    "packages/forge-mvc-iot/forge_mvc_iot/cli/listen.py",
    "packages/forge-mvc-rbac/forge_mvc_rbac/resolver.py",
    "packages/forge-mvc-mail/forge_mvc_mail/cli.py",
)


@pytest.mark.parametrize("chemin", DETECTEURS)
def test_chaque_detecteur_delegue_au_backend(chemin: str) -> None:
    """Une détection locale ne connaît que le pilote qu'on avait sous la main.

    Celle de `forge-mvc-rbac` se disait « robuste à la locale » et cherchait
    des locutions anglaises, que PostgreSQL en français ne produit pas. C'est
    le piège que le contrat existe pour fermer.
    """
    code = code_sans_prose((PROJECT_ROOT / chemin).read_text(encoding="utf-8"))

    assert "is_undefined_table_error" in code, (
        f"{chemin} qualifie une table absente sans demander au backend actif"
    )


def test_aucun_detecteur_ne_cherche_le_message_de_postgres() -> None:
    """Le repli sur le message reste permis, mais pas pour PostgreSQL.

    Son message est traduit : y chercher une locution serait vrai ou faux selon
    un réglage du serveur, ce qui n'est pas une propriété du programme.
    """
    fautes: list[str] = []
    for chemin in DETECTEURS:
        arbre = ast.parse((PROJECT_ROOT / chemin).read_text(encoding="utf-8"))
        for noeud in ast.walk(arbre):
            # Seules les COMPARAISONS sont jugées. Un message d'aide peut
            # légitimement écrire « la table n'existe pas encore » : il
            # s'adresse à un humain, il ne teste rien. Ce garde-fou l'avait
            # d'abord accusé, ce qui est la même erreur que juger la prose.
            if not isinstance(noeud, ast.Compare):
                continue
            if not any(isinstance(op, ast.In) for op in noeud.ops):
                continue
            if not (isinstance(noeud.left, ast.Constant) and isinstance(noeud.left.value, str)):
                continue
            cherche = noeud.left.value.lower()
            for locution in ("does not exist", "n'existe pas", "la relation"):
                if locution in cherche:
                    fautes.append(f"{chemin}:{noeud.lineno} compare à « {locution} »")

    assert not fautes, (
        "Ces comparaisons cherchent le message de PostgreSQL, qui est traduit :\n  "
        + "\n  ".join(fautes)
    )


def test_iot_ne_porte_plus_sa_propre_detection() -> None:
    """La détection dupliquée dans l'opt-in est remplacée par la délégation.

    Elle vivait à deux endroits, `doctor.py` et `listen.py`, et ne connaissait
    que MariaDB. Deux copies d'une règle fausse valent moins qu'une seule règle
    juste au bon endroit (principe 11).
    """
    pytest.importorskip("forge_mvc_iot")

    for module in ("doctor", "listen"):
        chemin = (
            PROJECT_ROOT / "packages" / "forge-mvc-iot"
            / "forge_mvc_iot" / "cli" / f"{module}.py"
        )
        code = code_sans_prose(chemin.read_text(encoding="utf-8"))

        assert "1146" not in code, (
            f"{module}.py teste encore l'errno MariaDB en propre, au lieu de "
            "déléguer au backend actif"
        )
        assert "is_undefined_table_error" in code, (
            f"{module}.py ne délègue pas la détection au backend"
        )
