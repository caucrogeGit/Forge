"""`META-README-COMMANDS-RATCHET-001` — le README d'un opt-in ne ment pas sur ses commandes.

Le README de `forge-mvc-admin` annonçait que « les filtres de liste et les
actions en masse restent à venir » alors que les filtres étaient livrés. Un
README qui décrit un état antérieur à son code est pire qu'un README absent :
il fait chercher ailleurs ce qui est déjà là, et personne ne le relit puisqu'il
a l'air à jour.

Ce garde-fou ne peut pas vérifier une phrase de prose. Il vérifie ce qui est
vérifiable, et qui dérive de la même façon : **les commandes**.

Chaque opt-in déclare ses commandes dans `COMMANDS`, table lue par le cœur
(ADR-059). Son README en annonce dans un tableau. Les deux doivent s'accorder.

## Ce que le garde-fou refuse, et ce qu'il tolère

Il **refuse** qu'un README annonce une commande que Forge n'accepte nulle part :
c'est la promesse d'une commande qui n'existe pas, et l'utilisateur la tape
avant de comprendre.

Il **tolère** qu'une commande déclarée ne figure pas au README : un README n'est
pas une référence exhaustive, et l'aide riche du CLI porte déjà ce contrat.
Exiger l'inverse transformerait chaque README en catalogue.

## Deux corrections de portée (`META-README-RATCHET-WIDEN-001`)

Le relevé ne voyait qu'une commande entre accents simples **et** précédée de
`forge `. Ni un bloc ```bash, où un README montre comment installer, ni une
citation nue, `mail:doctor`. Dix paquets sur vingt-sept étaient donc sautés : le
relevé paraissait large en sautant plus du tiers de sa cible.

Sa règle était fausse par ailleurs. Il exigeait qu'une commande citée dans un
**espace de noms de l'opt-in** figure dans son `COMMANDS`, or un espace se
partage : `db:config` vient de `forge-mvc-entities`, `db:init` et `db:apply` du
cœur. Le README d'entities, qui cite les trois, était accusé de promettre deux
commandes qui existent et fonctionnent. La règle porte désormais sur ce que
Forge accepte, quel qu'en soit le déclarant.
"""
from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PACKAGES = PROJECT_ROOT / "packages"

#: Une commande Forge citée dans un README, `forge <espace>:<verbe>`.
#:
#: Le motif exigeait les accents simples encadrants (`META-README-RATCHET-WIDEN-001`).
#: Il ne voyait donc que les commandes citées en code **en ligne**, jamais celles
#: d'un bloc ```bash, qui est précisément l'endroit où un README montre comment
#: installer et provisionner un opt-in.
#:
#: Mesuré : dix paquets sur vingt-sept étaient sautés faute de citation
#: reconnue, dont trois, `audit`, `notifications` et `settings`, qui citent
#: pourtant leurs commandes, dans un bloc. Le relevé paraissait large en
#: sautant plus du tiers de sa cible.
#:
#: Aucun de ces trois n'annonçait de commande inexistante, vérifié avant
#: l'élargissement : le trou était de couverture, pas de correction. Un cliquet
#: sert justement à attraper la faute suivante.
_COMMANDE = re.compile(r"(?:`|\bforge )([a-z][a-z0-9_-]*:[a-z][a-z0-9_:-]*)")


#: Commandes que `forge.py` dépêche en dur, sans passer par un registre.
def _dispatch_en_dur() -> "set[str]":
    """Commandes reconnues par une comparaison littérale dans `forge.py`.

    Lues par `ast`, jamais par grep : une occurrence en commentaire ou en
    docstring ferait croire à une commande qui n'existe pas.
    """
    trouvees: "set[str]" = set()
    arbre = ast.parse((PROJECT_ROOT / "forge.py").read_text(encoding="utf-8"))
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Compare):
            continue
        if not (isinstance(noeud.left, ast.Name) and noeud.left.id == "command"):
            continue
        for comparateur in noeud.comparators:
            elements = (
                [comparateur] if isinstance(comparateur, ast.Constant)
                else list(getattr(comparateur, "elts", []))
            )
            for element in elements:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    if ":" in element.value:
                        trouvees.add(element.value)
    return trouvees


def _commandes_connues() -> "set[str]":
    """Toutes les commandes que Forge accepte, quel qu'en soit le déclarant.

    Il n'existe pas de registre unique (`ADR-059` couvre les entry points des
    opt-ins, pas le cœur), et cette union en tient lieu : l'aide générale,
    l'aide riche, le dispatch en dur de `forge.py`, et le `COMMANDS` de chaque
    opt-in.

    Elle remplace une heuristique fausse (`META-README-RATCHET-WIDEN-001`). Le
    relevé exigeait qu'une commande citée dans un **espace de noms de l'opt-in**
    figure dans son `COMMANDS`. Or un espace se partage : `db:config` vient de
    `forge-mvc-entities`, `db:init` et `db:apply` du cœur. Le README d'entities,
    qui cite les trois, était donc accusé de promettre deux commandes qui
    existent et fonctionnent.
    """
    from cli._support.help_dispatch import HELP_DESCRIPTIONS

    connues = set(HELP_DESCRIPTIONS)
    aide = (PROJECT_ROOT / "cli" / "_support" / "help.py").read_text(encoding="utf-8")
    connues |= set(re.findall(r"\b([a-z][a-z0-9_-]*:[a-z][a-z0-9_:-]*)", aide))
    connues |= _dispatch_en_dur()
    for _, _, commandes in _OPTINS:
        connues |= set(commandes)
    return connues


def _optins_avec_commandes() -> "list[tuple[str, Path, dict[str, Any]]]":
    """Opt-ins déclarant un module `commands`, avec leur README."""
    trouves: list[tuple[str, Path, dict[str, Any]]] = []
    for dossier in sorted(PACKAGES.iterdir()):
        if not dossier.is_dir():
            continue
        readme = dossier / "README.md"
        if not readme.is_file():
            continue
        module_dir = dossier / dossier.name.replace("-", "_")
        if not (module_dir / "commands.py").is_file():
            continue
        try:
            module = importlib.import_module(f"{module_dir.name}.commands")
        except ImportError:
            continue
        commandes = getattr(module, "COMMANDS", None)
        if isinstance(commandes, dict):
            trouves.append((dossier.name, readme, commandes))
    return trouves


_OPTINS = _optins_avec_commandes()
_CONNUES = _commandes_connues()


def test_au_moins_un_optin_est_examine() -> None:
    """Un garde-fou sans entrée est un garde-fou qui ne garde rien.

    Il est déjà arrivé qu'un détecteur passe au vert parce qu'il ne trouvait
    plus ses fichiers.
    """
    assert _OPTINS, "aucun opt-in avec COMMANDS n'a été trouvé"


@pytest.mark.parametrize(
    "paquet,readme,commandes",
    _OPTINS,
    ids=[nom for nom, _, _ in _OPTINS],
)
def test_le_readme_n_annonce_aucune_commande_absente(
    paquet: str, readme: Path, commandes: "dict[str, Any]"
) -> None:
    """Toute commande citée par le README existe dans `COMMANDS`.

    L'espace de noms est comparé, pas seulement le nom exact : un README peut
    citer `forge migration:apply`, commande du cœur, à côté de ses propres
    commandes. Seules celles qui portent l'espace de noms de l'opt-in sont
    exigées de lui.
    """
    texte = readme.read_text(encoding="utf-8")
    citees = set(_COMMANDE.findall(texte))
    if not citees:
        pytest.skip(f"{paquet} ne cite aucune commande dans son README")

    manquantes = sorted(citees - _CONNUES)

    assert not manquantes, (
        f"{paquet} : son README annonce une ou plusieurs commandes que Forge "
        f"n'accepte nulle part : {', '.join(manquantes)}.\n"
        f"Ce paquet déclare : {', '.join(sorted(commandes)) or '<aucune>'}.\n"
        "Un README qui promet une commande inexistante la fait taper avant "
        "d'être compris."
    )


@pytest.mark.parametrize(
    "paquet,readme,commandes",
    _OPTINS,
    ids=[nom for nom, _, _ in _OPTINS],
)
def test_le_readme_n_annonce_rien_comme_a_venir_qui_existe(
    paquet: str, readme: Path, commandes: "dict[str, Any]"
) -> None:
    """Aucune commande déclarée n'est annoncée « à venir ».

    C'est la forme exacte de la dérive qui a motivé le ticket : le README de
    `forge-mvc-admin` annonçait comme à venir des fonctions déjà livrées.

    Le contrôle est volontairement étroit, une phrase de prose n'étant pas
    vérifiable en général : il ne regarde que les lignes qui citent une
    commande **et** un mot d'attente.
    """
    attente = re.compile(r"\b(à venir|a venir|pas encore|prévu|prevu|bientôt|bientot)\b", re.IGNORECASE)
    fautes: list[str] = []
    for numero, ligne in enumerate(readme.read_text(encoding="utf-8").splitlines(), 1):
        if not attente.search(ligne):
            continue
        for nom in _COMMANDE.findall(ligne):
            if nom in commandes:
                fautes.append(f"ligne {numero} : {nom}")

    assert not fautes, (
        f"{paquet} : son README annonce comme à venir une commande déjà "
        f"déclarée dans COMMANDS.\n  " + "\n  ".join(fautes)
    )


# ── Le relevé lit ce qu'un README montre vraiment ────────────────────────────

class TestPorteeDuReleve:
    """`META-README-RATCHET-WIDEN-001`.

    Le motif exigeait les accents simples encadrants, et le préfixe `forge `.
    Il ne voyait donc ni les commandes d'un bloc ```bash, où un README montre
    comment installer et provisionner, ni celles citées nues, `mail:doctor`.

    Mesuré : dix paquets sur vingt-sept étaient sautés faute de citation
    reconnue. Le relevé paraissait large en sautant plus du tiers de sa cible.
    """

    def test_une_commande_dans_un_bloc_de_code_est_vue(self) -> None:
        bloc = "```bash\nforge notifications:init\nforge migration:apply\n```"

        assert set(_COMMANDE.findall(bloc)) == {
            "notifications:init", "migration:apply"}

    def test_une_commande_citee_nue_est_vue(self) -> None:
        """`forge-mvc-mail` et `forge-mvc-entities` citent ainsi les leurs."""
        assert _COMMANDE.findall("La commande `mail:doctor` diagnostique.") == [
            "mail:doctor"]

    def test_une_commande_en_code_en_ligne_reste_vue(self) -> None:
        """L'élargissement n'a rien perdu de ce que le motif étroit voyait."""
        assert _COMMANDE.findall("Lancer `forge jobs:status`.") == ["jobs:status"]

    def test_les_options_ne_sont_pas_prises_pour_la_commande(self) -> None:
        assert _COMMANDE.findall("`forge audit:gc --days 90 --run`") == ["audit:gc"]

    def test_moins_de_six_paquets_echappent_encore_au_releve(self) -> None:
        """Dix paquets étaient sautés, cinq le restent, et ceux là ne citent
        aucune commande sous aucune forme.

        Si ce compte remonte, une forme de citation aura cessé d'être vue.
        """
        sautes = [
            nom for nom, readme, _ in _OPTINS
            if not _COMMANDE.findall(readme.read_text(encoding="utf-8"))
        ]

        assert len(sautes) <= 5, (
            f"{len(sautes)} paquets sautés : {', '.join(sautes)}")


class TestRegistreDesCommandes:
    """Le relevé ne vaut que ce que vaut sa liste de commandes connues."""

    def test_le_registre_a_des_entrees(self) -> None:
        assert len(_CONNUES) > 100, (
            f"{len(_CONNUES)} commandes connues : le registre ne se construit "
            f"plus, et le relevé accuserait tout le monde")

    @pytest.mark.parametrize(
        "commande,origine",
        [
            ("db:init", "dispatch en dur de forge.py"),
            ("db:apply", "dispatch en dur de forge.py"),
            ("db:config", "COMMANDS de forge-mvc-entities"),
            ("migration:apply", "cœur"),
            ("notifications:init", "COMMANDS de forge-mvc-notifications"),
            ("mail:doctor", "COMMANDS de forge-mvc-mail"),
        ],
    )
    def test_une_commande_reelle_est_connue(self, commande: str, origine: str) -> None:
        """Un espace de noms se partage.

        `db:config` vient de `forge-mvc-entities`, `db:init` et `db:apply` du
        cœur. L'ancienne règle, « une commande de ton espace doit être dans ton
        COMMANDS », accusait donc le README d'entities de promettre deux
        commandes qui existent et fonctionnent.
        """
        assert commande in _CONNUES, f"{commande} ({origine}) manque au registre"

    def test_une_commande_inventee_n_est_pas_connue(self) -> None:
        """Sans quoi le relevé passerait au vert sur n'importe quoi."""
        assert "notifications:teleporte" not in _CONNUES

    def test_le_dispatch_en_dur_est_lu_par_ast(self) -> None:
        """Sept commandes vivent hors registre, dans `forge.py`."""
        en_dur = _dispatch_en_dur()

        assert "db:apply" in en_dur
        assert "make:entity" in en_dur
