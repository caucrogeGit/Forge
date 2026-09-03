"""OPTIN-DML-DIALECT-001 : plus aucune construction MariaDB en dur dans la DML.

Le pendant sur serveurs réels est
`tests/db/test_optin_dml_portability_real_server_001.py`, qui exerce les
opérations. Ici on fige le contrat et l'absence, qui se vérifient sans base.

Deux traits seulement rejoignent `Dialect`, et c'est délibéré. L'horodatage
courant et le décalage temporel n'ont aucune écriture commune aux quatre
serveurs. L'upsert et la réservation d'une ligne unique en ont une, bâtie sur
ce que le contrat offre déjà : écrire puis insérer sous garde d'unicité pour le
premier, choisir puis réserver sous garde de statut pour le second. Un noyau
minimal ne gagne pas à porter ce qu'on peut exprimer sans lui (principe 8).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from core.database.backend import Dialect

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKAGES = PROJECT_ROOT / "packages"

_BACKENDS = [
    ("forge_mvc_mariadb.dialect", "MariaDBDialect"),
    ("forge_mvc_sqlite.dialect", "SQLiteDialect"),
    ("forge_mvc_postgres.dialect", "PostgreSQLDialect"),
    ("forge_mvc_mssql.dialect", "MSSQLDialect"),
]


# ── Le contrat ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("methode", ["now_expression", "interval_seconds_expression"])
def test_le_contrat_porte_le_trait(methode: str) -> None:
    assert hasattr(Dialect, methode)


@pytest.mark.parametrize(("module", "classe"), _BACKENDS)
def test_les_quatre_dialectes_repondent(module: str, classe: str) -> None:
    dialecte = getattr(pytest.importorskip(module), classe)()

    assert isinstance(dialecte.now_expression(), str)
    assert isinstance(dialecte.interval_seconds_expression("X"), str)


@pytest.mark.parametrize(("module", "classe"), _BACKENDS)
def test_le_decalage_porte_exactement_un_marqueur(module: str, classe: str) -> None:
    """Un marqueur de plus ou de moins décalerait tous les paramètres suivants."""
    dialecte = getattr(pytest.importorskip(module), classe)()

    assert dialecte.interval_seconds_expression("BASE").count("?") == 1


@pytest.mark.parametrize(("module", "classe"), _BACKENDS)
def test_le_decalage_reprend_la_base_qu_on_lui_donne(module: str, classe: str) -> None:
    dialecte = getattr(pytest.importorskip(module), classe)()

    assert "BASE" in dialecte.interval_seconds_expression("BASE")


@pytest.mark.parametrize(("module", "classe"), _BACKENDS)
def test_l_horodatage_coincide_avec_la_clause_default(module: str, classe: str) -> None:
    """La contrainte qui compte : deux lignes doivent rester comparables.

    Une ligne insérée avec le défaut de la colonne et une ligne insérée avec
    l'expression doivent porter la même horloge. SQL Server pose ses défauts en
    UTC (`SYSUTCDATETIME`), là où son `CURRENT_TIMESTAMP` rend l'heure locale.
    """
    dialecte = getattr(pytest.importorskip(module), classe)()

    defaut = dialecte.timestamp_default_clause(on_update=False)
    assert dialecte.now_expression() in defaut


# ── L'absence, dans les opt-ins ──────────────────────────────────────────────

_NON_PORTABLE = re.compile(
    r"\bNOW\(\)|ON DUPLICATE KEY|INTERVAL \?|\bLIMIT\b", re.IGNORECASE
)

#: Une chaîne qui porte des titres Markdown est un DOCUMENT, pas du SQL.
#:
#: Le relevé classe comme SQL toute chaîne contenant un mot de `_MOTS_SQL`,
#: volontairement large : le SQL de Forge s'assemble par fragments, et un
#: fragment comme `" WHERE id = ?"` n'a pas de verbe. Resserrer sur « verbe plus
#: clause » écarterait 261 chaînes sur 387, donc du vrai SQL.
#:
#: Cette largeur a un revers, mesuré : le gabarit du guide de déploiement,
#: deux cents lignes de Markdown, contient `--delete` dans son tableau des
#: gestes périodiques, ce qui le classait SQL, puis `RATE-LIMIT-001` dans un
#: code de ticket, ce qui le déclarait non portable. Deux mots de prose.
#:
#: Contourner en renommant la section aurait été céder au détecteur plutôt que
#: le corriger. Le critère retenu est net : aucune instruction SQL ne contient
#: de titre Markdown. Mesuré, il n'exclut qu'une chaîne sur 387, celle là.
_DOCUMENT_MARKDOWN = re.compile(r"^#{1,6} \S", re.MULTILINE)

#: Mots qui font d'une chaîne une instruction SQL, `DELETE` compris.
#: Il manquait, et `DELETE FROM ... LIMIT 1` échappait donc au relevé.
_MOTS_SQL = ("SELECT", "UPDATE", "INSERT", "VALUES", "DELETE")

#: Dette connue, à payer, et **listée plutôt que cachée**.
#:
#: Même principe que le cliquet DDL : une exclusion muette rendrait le relevé
#: rassurant et faux. Chaque entrée porte son motif et son ticket, et le test
#: `test_le_cliquet_dml_se_resserre` échoue dès qu'une entrée devient propre,
#: ce qui oblige à la retirer au lieu de la laisser dormir.
#: Dette listée : fichiers dont le SQL non portable est connu et assumé, le
#: temps d'un ticket dédié. Une exclusion muette rendrait le relevé rassurant
#: et faux ; le cliquet ci-dessous échoue dès qu'une entrée devient propre.
#:
#: Vide depuis `VIDEO-DML-PORTABLE-001`. La seule entrée qu'elle ait portée
#: décrivait d'ailleurs le défaut de travers : elle affirmait que PostgreSQL
#: accepte `%s` nativement, alors que le cœur y **double** tout `%` littéral,
#: si bien que `%s` y devenait `%%s`, un texte et non un marqueur. Vérifié
#: contre les serveurs plutôt que déduit du pilote.
_DETTE_CONNUE: "dict[str, str]" = {}


def _fichiers_sql_des_optins() -> "list[Path]":
    """Modules des opt-ins applicatifs, hors backends et hors code généré."""
    fichiers: "list[Path]" = []
    for paquet in sorted(PACKAGES.iterdir()):
        if not paquet.is_dir() or paquet.name in {
            "forge-mvc-mariadb", "forge-mvc-postgres",
            "forge-mvc-mssql", "forge-mvc-sqlite",
        }:
            continue
        for module in paquet.rglob("forge_mvc_*/**/*.py"):
            if "build/" in module.as_posix() or "__pycache__" in module.as_posix():
                continue
            fichiers.append(module)
    return fichiers


def _lignes_de_docstring(arbre: ast.Module) -> "set[int]":
    """Lignes occupées par les docstrings, à ne pas juger.

    Une docstring cite volontiers la forme qu'elle bannit, pour expliquer
    pourquoi. La reconnaître par « la ligne commence par trois guillemets » est
    faux dès la deuxième ligne, ce qui obligeait le relevé à garder un motif
    étroit pour éviter les faux positifs (`OPTIN-DML-PORTABILITY-WIDEN-001`).
    """
    occupees: "set[int]" = set()
    porteurs = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, porteurs):
            continue
        corps = getattr(noeud, "body", None)
        if not corps:
            continue
        premier = corps[0]
        if (isinstance(premier, ast.Expr)
                and isinstance(premier.value, ast.Constant)
                and isinstance(premier.value.value, str)):
            occupees.update(range(premier.lineno, (premier.end_lineno or premier.lineno) + 1))
    return occupees


def _chaines_sql(module: "Path") -> "list[tuple[int, str]]":
    """Chaînes littérales du module qui ressemblent à du SQL.

    L'analyse syntaxique remplace le balayage ligne à ligne : elle ne voit que
    de vraies chaînes, jamais un commentaire ni une docstring, et elle lit les
    fragments littéraux d'une f-string comme le reste.
    """
    try:
        arbre = ast.parse(module.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):  # pragma: no cover — défensif
        return []
    docs = _lignes_de_docstring(arbre)
    trouvees: "list[tuple[int, str]]" = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Constant) or not isinstance(noeud.value, str):
            continue
        if noeud.lineno in docs:
            continue
        texte = noeud.value
        if _DOCUMENT_MARKDOWN.search(texte):
            continue
        if any(mot in texte.upper() for mot in _MOTS_SQL):
            trouvees.append((noeud.lineno, texte))
    return trouvees


def test_aucune_construction_mariadb_en_dur_dans_la_dml() -> None:
    """Les chaînes SQL des opt-ins ne doivent nommer aucune forme propriétaire.

    Les commentaires et docstrings y ont droit : ils expliquent justement
    pourquoi la forme est bannie. Seules les chaînes de code comptent, et
    l'analyse syntaxique le garantit au lieu de l'approcher.

    `LIMIT` est banni en entier, plus seulement sous la forme
    `ORDER BY <col> LIMIT <chiffre>`. Ce motif étroit laissait passer
    `WHERE id = ? LIMIT 1`, `DELETE ... LIMIT 1` et `... LIMIT ?`, qui cassaient
    respectivement `jobs.get_job`, le back-office et la liste de `stats` sur les
    backends sans `LIMIT` (`ADMIN-JOBS-LIMIT-PORTABLE-001`). La borne appartient
    au dialecte, par `limit_clause()` ou `pagination_clause()`.
    """
    fautes: "list[str]" = []
    for module in _fichiers_sql_des_optins():
        relatif = module.relative_to(PACKAGES).as_posix()
        if relatif in _DETTE_CONNUE:
            continue
        for numero, texte in _chaines_sql(module):
            if _NON_PORTABLE.search(texte):
                extrait = " ".join(texte.split())[:80]
                fautes.append(f"{module.relative_to(PROJECT_ROOT)}:{numero} : {extrait}")

    assert not fautes, (
        "SQL non portable dans un opt-in (OPTIN-DML-DIALECT-001) : passez par "
        "`dialect.now_expression()`, `interval_seconds_expression()` ou "
        "`limit_clause()`, ou par un motif portable.\n  " + "\n  ".join(fautes)
    )


def test_l_audit_regarde_bien_quelque_chose() -> None:
    """Un balayage qui ne trouve aucun fichier passerait pour toujours vert."""
    assert len(_fichiers_sql_des_optins()) > 100


def test_sessions_db_reste_le_modele_du_sans_fonction_serveur() -> None:
    """Ce paquet calcule ses horodatages en Python : sa garde ne doit pas bouger.

    C'est l'autre réponse valable, et la meilleure quand l'horloge de référence
    peut être celle de l'application.
    """
    garde = (PACKAGES / "forge-mvc-sessions-db" / "tests" / "test_db_store_001.py")

    assert 'assert "NOW()" not in sql' in garde.read_text(encoding="utf-8")


def test_le_cliquet_dml_se_resserre() -> None:
    """Une entrée corrigée, ou disparue, doit être retirée de la dette.

    Sans ce contrôle, la liste ne ferait que grandir et le relevé se viderait
    de son sens. Un fichier qui n'a plus de construction non portable n'a plus
    rien à faire ici.

    Écrit en boucle et non en `parametrize` : une paramétrisation vide rend un
    test **sauté**, donc invisible, alors que la dette vide est justement l'état
    qu'on veut voir tenir. Un saut n'est pas un succès.
    """
    a_retirer: "list[str]" = []
    for relatif in sorted(_DETTE_CONNUE):
        module = PACKAGES / relatif
        if not module.exists():
            a_retirer.append(f"{relatif} n'existe plus")
            continue
        if not [t for _, t in _chaines_sql(module) if _NON_PORTABLE.search(t)]:
            a_retirer.append(f"{relatif} n'a plus de SQL non portable")

    assert not a_retirer, (
        "Retirez ces entrées de _DETTE_CONNUE pour que le relevé les surveille "
        "de nouveau :\n  " + "\n  ".join(a_retirer)
    )


# ── L'exclusion des documents reste étroite ──────────────────────────────────

class TestExclusionDesDocuments:
    """`DEPLOY-NGINX-RATE-LIMIT-001` a révélé un faux positif du relevé.

    Le gabarit du guide de déploiement, deux cents lignes de Markdown, était
    classé SQL parce qu'il contient `--delete`, puis déclaré non portable parce
    qu'un code de ticket contient `RATE-LIMIT-001`.

    L'exclusion qui répare cela doit rester étroite : elle ne vaut que pour ce
    qui est manifestement un document, jamais pour du SQL qui contiendrait un
    caractère `#`.
    """

    def _releve(self, source: str, tmp_path: Path) -> list:
        module = tmp_path / "m.py"
        module.write_text(source, encoding="utf-8")
        return _chaines_sql(module)

    def test_un_document_markdown_n_est_pas_du_sql(self, tmp_path: Path) -> None:
        source = 'DOC = """\\n# Titre\\n\\nUn tableau citant --delete et LIMIT.\\n"""\n'

        assert self._releve(source, tmp_path) == []

    def test_du_sql_portant_un_commentaire_diese_reste_examine(
        self, tmp_path: Path
    ) -> None:
        """`#` seul ne fait pas un titre. Un SQL commenté doit rester jugé."""
        source = 'SQL = "SELECT id FROM t # commentaire\\nWHERE n = ? LIMIT 1"\n'
        releve = self._releve(source, tmp_path)

        assert len(releve) == 1
        assert _NON_PORTABLE.search(releve[0][1])

    def test_du_sql_multiligne_ordinaire_reste_examine(self, tmp_path: Path) -> None:
        source = 'SQL = """\\nSELECT id\\nFROM t\\nORDER BY n LIMIT 10\\n"""\n'
        releve = self._releve(source, tmp_path)

        assert len(releve) == 1

    def test_l_exclusion_ne_touche_qu_une_chaine_du_depot(self) -> None:
        """Mesuré : 387 chaînes classées SQL avant, 386 après.

        Si ce compte s'effondre un jour, l'exclusion sera devenue large, et le
        relevé rassurant plutôt que vrai.
        """
        avec, sans = 0, 0
        for module in _fichiers_sql_des_optins():
            arbre = ast.parse(module.read_text(encoding="utf-8"))
            docs = _lignes_de_docstring(arbre)
            for noeud in ast.walk(arbre):
                if not isinstance(noeud, ast.Constant) or not isinstance(noeud.value, str):
                    continue
                if noeud.lineno in docs:
                    continue
                if not any(mot in noeud.value.upper() for mot in _MOTS_SQL):
                    continue
                avec += 1
                if not _DOCUMENT_MARKDOWN.search(noeud.value):
                    sans += 1

        assert avec - sans <= 5, (
            f"{avec - sans} chaînes écartées comme documents : l'exclusion "
            f"devait n'en écarter qu'une poignée, elle est devenue large")
