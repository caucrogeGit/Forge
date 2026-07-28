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

#: `forge-mvc-testing` est une infrastructure de développement (ADR-041) : elle
#: s'installe dans `requirements-dev.txt` et n'a rien à mettre en service.
SANS_MISE_EN_SERVICE = {"forge-mvc-testing"}


def _toutes_references() -> "list[tuple[str, Path]]":
    """Les 27 paquets, backends BDD compris, et non les seuls opt-ins catalogués."""
    return [
        (ref.parts[-3], ref)
        for ref in sorted(PROJECT_ROOT.glob("packages/*/docs/reference.md"))
        if ref.parts[-3] not in SANS_MISE_EN_SERVICE
    ]


def test_chaque_reference_a_son_chapitre_de_mise_en_service() -> None:
    """Installer et mettre en service sont deux gestes distincts, donc deux chapitres.

    Le chapitre « 2. Installation » répond à « comment obtenir le paquet ».
    Il ne répond pas à « qu'est-ce qu'il me reste à faire pour que ça marche »,
    question dont l'utilisateur devait reconstituer seul la réponse.

    Les backends de base de données sont concernés au même titre : leur
    séquence propre (`db:config`, accès, `db:init`, `doctor`) **est** une mise
    en service, et elle était noyée dans le chapitre d'installation.
    """
    offenders = [
        name for name, ref in _toutes_references()
        if '??? note "3. Mise en service"' not in ref.read_text(encoding="utf-8")
    ]

    assert offenders == [], (
        "Ces références n'ont pas de chapitre de mise en service distinct de "
        f"l'installation : {offenders}"
    )


@pytest.mark.parametrize("titre", [
    "#### 1. L'épingler",
    "#### 2. L'inscrire",
    "#### 3. Poser sa base",
    "#### 4. Le brancher là où il agit",
    "#### 5. Le prouver",
])
def test_le_chapitre_de_mise_en_service_couvre_les_cinq_points(titre: str) -> None:
    """Vaut pour les opt-ins catalogués.

    Un backend a sa propre séquence (`db:config`, accès, `db:init`, `doctor`) :
    seul l'épinglage lui est commun, le reste n'a pas d'équivalent.
    """
    offenders = [
        name for name, ref in _references()
        if titre not in ref.read_text(encoding="utf-8")
    ]

    assert offenders == [], f"point « {titre} » absent de : {offenders}"


def test_tout_chapitre_de_mise_en_service_commence_par_l_epinglage() -> None:
    """Le seul point commun aux opt-ins et aux backends."""
    offenders = [
        name for name, ref in _toutes_references()
        if "#### 1. L'épingler" not in ref.read_text(encoding="utf-8")
    ]

    assert offenders == [], offenders


def test_l_epinglage_n_est_pas_documente_en_double() -> None:
    """Il appartient à la mise en service, pas à l'installation (principe 11)."""
    offenders: list[str] = []
    for name, ref in _toutes_references():
        texte = ref.read_text(encoding="utf-8")
        if texte.count(f"{name}==<version de forge-mvc>") > 1:
            offenders.append(name)

    assert offenders == [], f"épinglage documenté deux fois : {offenders}"


def test_la_numerotation_des_chapitres_reste_continue() -> None:
    """L'insertion d'un chapitre renumérote les suivants, sans trou ni doublon."""
    offenders: list[str] = []
    for name, ref in _references():
        numeros = [
            int(n) for n in re.findall(r'^\?\?\? note "(\d+)\. ', ref.read_text(encoding="utf-8"), re.M)
        ]
        if numeros and numeros != list(range(1, len(numeros) + 1)):
            offenders.append(f"{name} : {numeros}")

    assert offenders == [], f"numérotation de chapitres cassée : {offenders}"


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

# ── Structure des chapitres : installer, mettre en service, désinstaller ─────

def test_le_chapitre_d_installation_ne_porte_plus_la_desinstallation() -> None:
    """Trois gestes distincts, trois chapitres.

    « 2. Installation et désinstallation » mélangeait l'obtention du paquet et
    son retrait, deux moments qui n'arrivent jamais ensemble.
    """
    offenders = [
        name for name, ref in _toutes_references()
        if '??? note "2. Installation et désinstallation"' in ref.read_text(encoding="utf-8")
    ]

    assert offenders == [], f"chapitre 2 encore mixte : {offenders}"


def test_la_desinstallation_a_son_chapitre_apres_la_mise_en_service() -> None:
    offenders = [
        name for name, ref in _toutes_references()
        if '??? note "4. Désinstallation"' not in ref.read_text(encoding="utf-8")
    ]

    assert offenders == [], f"pas de chapitre de désinstallation : {offenders}"


def test_les_chapitres_ne_sont_jamais_deplies_par_defaut() -> None:
    """`???+` ouvre l'accordéon au chargement ; la page en compte une dizaine."""
    offenders: list[str] = []
    for ref in sorted(PROJECT_ROOT.glob("packages/*/docs/reference.md")):
        for number, line in enumerate(ref.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("???+"):
                offenders.append(f"{ref.parts[-3]}:{number}")

    assert offenders == [], f"chapitres dépliés par défaut : {offenders}"


# ── Le prérequis de venv vaut pour les deux canaux d'installation ───────────

def test_le_prerequis_de_venv_est_hors_des_onglets() -> None:
    """PEP 668 ne dépend pas du canal, mais de l'endroit où `pip` s'exécute.

    L'avertissement vivait dans le seul onglet « Depuis Git », alors que la
    commande de l'onglet PyPI heurte le même verrou. Or PyPI est le premier
    onglet, donc celui affiché par défaut : l'avertissement était caché à la
    majorité des lecteurs.

    Il est désormais **avant** les deux canaux, et formulé en prérequis plutôt
    qu'en dépannage : mieux vaut éviter l'erreur que la réparer, la plupart de
    ceux qui échouent cherchant la réponse ailleurs que dans la page.
    """
    offenders: list[str] = []
    for reference in sorted(PROJECT_ROOT.glob("packages/*/docs/reference.md")):
        texte = reference.read_text(encoding="utf-8")
        if "externally-managed-environment" not in texte:
            offenders.append(f"{reference.parts[-3]} : avertissement absent")
            continue

        position_avertissement = texte.index("externally-managed-environment")
        premier_canal = texte.find("#### A. Depuis PyPI")
        if premier_canal == -1 or position_avertissement > premier_canal:
            offenders.append(f"{reference.parts[-3]} : après le premier canal")

    assert offenders == [], offenders


def test_le_prerequis_donne_la_commande_d_activation() -> None:
    """Un avertissement sans le geste qui l'évite ne sert à rien."""
    offenders = [
        ref.parts[-3] for ref in sorted(PROJECT_ROOT.glob("packages/*/docs/reference.md"))
        if "source .venv/bin/activate" not in ref.read_text(encoding="utf-8")
    ]

    assert offenders == [], offenders


# ── Plus d'onglets : ils rendaient les sections liables par URL ──────────────

def test_aucun_bloc_a_onglets_dans_les_references() -> None:
    """Les onglets de Material sont des **ancres**, pas des boutons.

    Lu dans le bundle du thème : chaque étiquette d'onglet voit son contenu
    remplacé par `<a href="#__tabbed_1_2">`, et le fragment d'URL sélectionne
    l'onglet en retour. Cliquer un onglet écrit donc ce fragment dans l'URL ;
    le fragment désignant un élément situé dans un `<details>`, le navigateur
    déplie et fait défiler pour le révéler.

    Le chapitre d'installation s'ouvrait ainsi tout seul, et l'effet se
    reproduisait à chaque changement d'onglet. Deux sous-titres suppriment le
    mécanisme, au lieu d'en contourner les effets : ils montrent en outre les
    deux canaux d'un coup, se trouvent au `Ctrl+F` et s'impriment.
    """
    offenders: list[str] = []
    for reference in sorted(PROJECT_ROOT.glob("packages/*/docs/reference.md")):
        for number, line in enumerate(reference.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().startswith('=== "'):
                offenders.append(f"{reference.parts[-3]}:{number}")

    assert offenders == [], (
        "Un bloc à onglets rend la section liable par URL et déplie le chapitre "
        f"qui la contient : {offenders}"
    )


def test_les_deux_canaux_sont_visibles_en_sous_titres() -> None:
    offenders: list[str] = []
    for reference in sorted(PROJECT_ROOT.glob("packages/*/docs/reference.md")):
        texte = reference.read_text(encoding="utf-8")
        for titre in ("#### A. Depuis PyPI (stable)", "#### B. Depuis Git (avant-garde)"):
            if titre not in texte:
                offenders.append(f"{reference.parts[-3]} : {titre}")

    assert offenders == [], offenders


def test_le_chapitre_d_installation_ne_reprend_pas_la_mise_en_service() -> None:
    """Chaque geste à un seul endroit (principe 11).

    Le chapitre 2 gardait `opt-in:enable` et les commandes `:init`, désormais
    portées par le chapitre 3. Placés après le canal Git, ils se lisaient de
    surcroît comme s'ils lui étaient propres.
    """
    offenders: list[str] = []
    for name, ref in _references():
        texte = ref.read_text(encoding="utf-8")
        chapitre = re.search(
            r'^\?\?\? note "2\. Installation"\n(.*?)^\?\?\? note "3\.', texte, re.M | re.S
        )
        if chapitre and re.search(r"opt-in:enable|migration:apply", chapitre.group(1)):
            offenders.append(name)

    assert offenders == [], f"mise en service encore dans le chapitre 2 : {offenders}"


def test_le_prerequis_precede_les_deux_canaux() -> None:
    """L'ordre qui compte : activer le venv avant de choisir un canal.

    Le prérequis vaut pour les deux canaux, il vient donc avant eux. C'est le
    seul invariant d'ordre à figer ; la façon d'introduire le choix, phrase
    d'annonce ou titre « Installer le paquet », est un choix de rédaction en
    cours d'essai sur la référence pilote (mariadb).
    """
    offenders: list[str] = []
    for reference in sorted(PROJECT_ROOT.glob("packages/*/docs/reference.md")):
        texte = reference.read_text(encoding="utf-8")
        prerequis = texte.index("externally-managed-environment")
        canal_a = texte.index("#### A. Depuis PyPI")
        if prerequis > canal_a:
            offenders.append(f"{reference.parts[-3]} : prérequis après le canal A")

    assert offenders == [], offenders
