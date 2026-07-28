"""DOC-OPTIN-INSTALL-PROCEDURE-001 : la mise en service d'un opt-in est documentée.

Retour de terrain : après avoir installé un opt-in, un utilisateur devait
reconstituer seul la suite des gestes qui le rendent **opérationnel**. La
documentation portait l'information, mais dispersée, et deux défauts la
rendaient trompeuse.

Le premier est le plus grave. Les références écrivaient :

    forge opt-in:enable <nom>

Or `opt-in:enable` est en **dry-run par défaut** : sans `--apply`, rien n'est
écrit. Mesuré avant correctif, **19 références sur 22** donnaient cette
instruction qui ne fait rien, laissant croire l'opt-in activé alors que
`optins/registry.py` restait inchangé.

Le second : deux des cinq gestes n'étaient documentés nulle part, l'épinglage
dans `requirements.txt` et la preuve par un usage réel. Un opt-in installé sans
épinglage n'existe que sur la machine de celui qui l'a installé.

La procédure canonique vit désormais dans `docs/install/opt-ins.md`, et chaque
référence d'opt-in y renvoie plutôt que de la redire (principe 11).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CANONICAL = PROJECT_ROOT / "docs" / "install" / "opt-ins.md"
ANCHOR = "#rendre-un-opt-in-operationnel-les-cinq-points"

#: Paquets hors catalogue d'opt-ins : les backends BDD se choisissent par
#: `DB_BACKEND` et non par le registre (ADR-054), et `forge-mvc-testing` est
#: réservé au développement (ADR-041). Chacun porte sa propre procédure.
HORS_CATALOGUE = {
    "forge-mvc-mariadb",
    "forge-mvc-sqlite",
    "forge-mvc-postgres",
    "forge-mvc-mssql",
    "forge-mvc-testing",
}


def _catalogue() -> "dict[str, object]":
    from cli.optins.catalog import OFFICIAL_OPTINS

    return dict(OFFICIAL_OPTINS)


def _references() -> "list[tuple[str, Path]]":
    couples: list[tuple[str, Path]] = []
    for name, optin in sorted(_catalogue().items()):
        ref = PROJECT_ROOT / "packages" / optin.package_dist / "docs" / "reference.md"  # type: ignore[attr-defined]
        if ref.is_file():
            couples.append((name, ref))
    return couples


# ── Le défaut principal : une commande documentée qui ne fait rien ───────────

def test_aucune_reference_ne_documente_enable_sans_apply() -> None:
    """`opt-in:enable` sans `--apply` est une simulation : rien n'est écrit."""
    offenders: list[str] = []
    for name, ref in _references():
        for number, line in enumerate(ref.read_text(encoding="utf-8").splitlines(), 1):
            for match in re.finditer(r"forge opt-in:enable\s+([a-z][a-z0-9-]*)", line):
                reste = line[match.end():]
                if not reste.lstrip().startswith("--apply"):
                    offenders.append(f"{name} ({ref.relative_to(PROJECT_ROOT)}:{number})")

    assert offenders == [], (
        "`opt-in:enable` est en dry-run par défaut : sans `--apply`, la commande "
        f"documentée n'écrit rien et l'opt-in n'est pas activé. {offenders}"
    )


def test_le_contrat_dry_run_est_toujours_celui_du_code() -> None:
    """Le garde-fou ci-dessus ne vaut que si `--apply` reste nécessaire."""
    source = (PROJECT_ROOT / "cli" / "optins" / "enable.py").read_text(encoding="utf-8")

    assert "dry-run par défaut" in source
    assert "``--apply``" in source


# ── La procédure canonique existe et couvre les cinq points ─────────────────

def test_la_procedure_canonique_existe() -> None:
    texte = CANONICAL.read_text(encoding="utf-8")

    assert "## Rendre un opt-in opérationnel" in texte


@pytest.mark.parametrize(
    ("titre", "raison"),
    [
        ("### 1. L’épingler", "sans épinglage, l'opt-in n'existe que sur une machine"),
        ("### 2. L’inscrire", "le registre rend l'opt-in visible du projet"),
        ("### 3. Poser sa base", "l'oubli ne se voit qu'au premier appel"),
        ("### 4. Le brancher là où il agit", "le branchement dépend du type d'opt-in"),
        ("### 5. Le prouver", "présent n'est pas opérationnel"),
    ],
)
def test_chacun_des_cinq_points_est_documente(titre: str, raison: str) -> None:
    texte = CANONICAL.read_text(encoding="utf-8")

    assert titre in texte, f"point manquant ({raison}) : {titre}"


def test_la_procedure_dit_que_la_migration_appliquee_ne_se_supprime_pas() -> None:
    """L'exception de la désinstallation, celle qui casse une base si on l'ignore."""
    texte = CANONICAL.read_text(encoding="utf-8")

    assert "La migration déjà appliquée ne se supprime pas" in texte


# ── Chaque référence renvoie à la procédure, sans la redire ─────────────────

def test_chaque_reference_renvoie_a_la_procedure_canonique() -> None:
    offenders = [
        name for name, ref in _references()
        if ANCHOR not in ref.read_text(encoding="utf-8")
    ]

    assert offenders == [], (
        "Ces références n'orientent pas vers la procédure de mise en service ; "
        f"leur lecteur doit la reconstituer seul : {offenders}"
    )


def test_toute_reference_documente_l_epinglage() -> None:
    """Le geste qui manquait, et le plus coûteux à découvrir tard.

    Un paquet installé sans être épinglé n'existe que sur la machine de celui
    qui l'a installé. Le cas des backends BDD est le plus grave : sans pilote,
    l'application n'atteint aucune base, et la panne se produit chez le
    collègue, sur le serveur ou en intégration continue, jamais chez l'auteur.

    Les backends et `forge-mvc-testing` sont hors catalogue mais **pas hors
    règle** : seul le fichier d'épinglage change, `requirements-dev.txt` pour
    l'infrastructure de test réservée au développement (ADR-041).
    """
    offenders: list[str] = []
    for reference in sorted(PROJECT_ROOT.glob("packages/*/docs/reference.md")):
        texte = reference.read_text(encoding="utf-8")
        if "requirements.txt" not in texte and "requirements-dev.txt" not in texte:
            offenders.append(reference.parts[-3])

    assert offenders == [], (
        "Ces références n'indiquent pas d'épingler le paquet ; leur lecteur "
        f"obtient une installation qui ne survit pas à un clone : {offenders}"
    )


def test_les_paquets_hors_catalogue_sont_bien_ceux_attendus() -> None:
    """Garde la liste d'exclusion honnête : un nouveau paquet ne s'y glisse pas."""
    distributions = {p.parts[-1] for p in PROJECT_ROOT.glob("packages/*") if p.is_dir()}
    catalogues = {optin.package_dist for optin in _catalogue().values()}  # type: ignore[attr-defined]

    assert distributions - catalogues == HORS_CATALOGUE


def test_le_catalogue_et_les_references_se_correspondent() -> None:
    """Un opt-in du catalogue sans page de référence n'est pas documenté."""
    manquantes = [
        name for name, optin in sorted(_catalogue().items())
        if not (PROJECT_ROOT / "packages" / optin.package_dist / "docs" / "reference.md").is_file()  # type: ignore[attr-defined]
    ]

    assert manquantes == [], f"opt-ins sans page de référence : {manquantes}"


# ── Provisionnement : la commande existe, et elle est citée ─────────────────

def test_tout_opt_in_posant_des_tables_documente_sa_commande_init() -> None:
    """ADR-071 : un opt-in à tables expose `<nom>:init`, et sa page le dit.

    C'est le geste le plus souvent oublié, et son oubli ne se manifeste qu'au
    premier appel, par une erreur SQL sur une table absente.
    """
    offenders: list[str] = []
    for name, optin in sorted(_catalogue().items()):
        package = PROJECT_ROOT / "packages" / optin.package_dist  # type: ignore[attr-defined]
        module = package / optin.package_import  # type: ignore[attr-defined]
        if not (module / "tables.py").is_file():
            continue

        commands = module / "commands.py"
        declared = re.findall(r'"([a-z0-9_-]+:[a-z0-9_-]+)"', commands.read_text(encoding="utf-8"))
        init = [c for c in declared if c.endswith(":init")]
        if not init:
            offenders.append(f"{name} : aucune commande :init (ADR-071)")
            continue

        reference = (package / "docs" / "reference.md").read_text(encoding="utf-8")
        if init[0] not in reference:
            offenders.append(f"{name} : `{init[0]}` absente de sa page de référence")

    assert offenders == [], offenders


def test_aucune_reference_ne_fait_copier_du_ddl_a_la_main() -> None:
    """Le DDL se pose par `<nom>:init`, rendu pour le backend installé.

    La référence RBAC faisait copier trente lignes de `CREATE TABLE ...
    ENGINE=InnoDB`, syntaxe propre à MariaDB, alors que `rbac:init` produit un
    DDL portable sur les quatre backends (ADR-054).
    """
    offenders: list[str] = []
    for name, ref in _references():
        texte = ref.read_text(encoding="utf-8")
        if "ENGINE=InnoDB" in texte and "CREATE TABLE" in texte:
            offenders.append(name)

    assert offenders == [], (
        "Ces références font copier du DDL MariaDB à la main, inutilisable sur "
        f"les autres backends : {offenders}"
    )
