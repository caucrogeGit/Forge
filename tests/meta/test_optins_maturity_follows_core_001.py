"""`OPTINS-MATURITY-FOLLOWS-CORE-001` — un opt-in n'a pas de maturité propre.

Les vingt-sept opt-ins portent déjà la version du cœur, `pyproject.toml` par
`pyproject.toml`, et le même classifieur. Leur **prose** disait autre chose :
dix fichiers annonçaient un « Statut : Beta » par paquet, plusieurs adossé à
`1.0.0-beta.9` ou `1.0.0-beta.13`, séries closes depuis le renumérotage vers
1.0.

Ce n'est pas une coquette : une maturité annoncée par paquet **dérive**, et
elle avait dérivé. Le README de `forge-mvc-mfa`, module de sécurité, annonçait
que « la politique de rotation de la clé Fernet n'est pas encore formalisée »
alors que `MFA-KEY-ROTATION-001` l'avait livrée, et conseillait des **sticky
sessions** en multi-worker là où le paquet livre `DbTotpReplayStore`, magasin
partagé par tous les workers.

Un README qui décrit un état antérieur à son code est pire qu'un README absent :
il fait chercher ailleurs ce qui est déjà là, et personne ne le relit puisqu'il
a l'air à jour.

## Ce que ce garde-fou fige, et ce qu'il laisse à un autre

La fin qu'il garde : aucune documentation de paquet ne prête à un opt-in un
cycle de maturité propre.

Il ne garde **pas** les numéros de version. `tools/check_version_sync.py` le
fait depuis `PKG-VERSION-SYNC-CHECK-001`, sur soixante et un fichiers, et il
est joué par la suite de tests comme par `release-validate.sh`. Deux gardiens
de la même chose, c'est l'assurance que l'un des deux dérive.

Il ne fige pas non plus le classifieur, qui est une décision de release.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGES = PROJECT_ROOT / "packages"

#: Une déclaration de maturité propre à un paquet.
#:
#: Volontairement étroite : elle vise les formules qui **attribuent** un stade à
#: un paquet, pas toute occurrence du mot. Une page d'historique qui raconte une
#: publication passée est légitime, et le tableau des tickets de la roadmap
#: aussi.
_MATURITE = re.compile(
    r"[Ss]tatut\s*:\s*\**\s*(?:Beta|Bêta|Alpha)"
    r"|est\s+en\s+\**(?:Beta|Bêta|Alpha)\**"
    r"|API\s+encore\s+(?:beta|bêta)"
    r"|exigences?\s+Beta\s+restantes?",
)


def _paquets() -> "list[Path]":
    return sorted(d for d in PACKAGES.iterdir()
                  if d.is_dir() and (d / "pyproject.toml").is_file())


def _documents(paquet: Path) -> "list[Path]":
    docs = [paquet / "README.md"]
    dossier = paquet / "docs"
    if dossier.is_dir():
        docs += [p for p in dossier.rglob("*.md")
                 if "history" not in p.relative_to(dossier).parts]
    return [p for p in docs if p.is_file()]


_PAQUETS = _paquets()


def test_le_releve_a_des_entrees() -> None:
    """Un garde-fou sans entrée est un garde-fou qui ne garde rien."""
    assert len(_PAQUETS) > 20, f"{len(_PAQUETS)} paquets trouvés"
    assert any(_documents(p) for p in _PAQUETS), (
        "aucun document de paquet n'est lu : le relevé ne garde plus rien")


class TestUneSeuleAutorite:
    """La version est gardée ailleurs, et une seule fois.

    Ce module a d'abord vérifié lui même que chaque `pyproject.toml` d'opt-in
    portait la version du cœur. C'était un doublon : `tools/check_version_sync.py`
    le fait depuis `PKG-VERSION-SYNC-CHECK-001`, sur **soixante et un** fichiers
    et non vingt-sept, `__version__` des modules, pins `forge-mvc>=`, extras du
    pyproject racine, `core/__init__.py`, `forge.py`, pin du squelette et
    `package.json` compris.

    Deux gardiens de la même chose, c'est l'assurance que l'un des deux dérive,
    et le principe 11 refuse deux façons officielles de faire la même chose. Ce
    module ne garde donc que ce que l'autre ne regarde pas : la **prose**.
    """

    def test_l_outil_de_synchronisation_existe_toujours(self) -> None:
        outil = PROJECT_ROOT / "tools" / "check_version_sync.py"

        assert outil.is_file(), (
            "tools/check_version_sync.py est l'autorité sur la version "
            "(PKG-VERSION-SYNC-CHECK-001). S'il disparaît, plus rien ne "
            "garantit que les opt-ins suivent le cœur.")

    def test_il_est_joue_par_la_suite(self) -> None:
        """Un outil que personne ne lance ne garde rien."""
        appelant = PROJECT_ROOT / "tests" / "meta" / "test_version_sync_001.py"

        assert appelant.is_file()
        assert "check_version_sync.py" in appelant.read_text(encoding="utf-8")


class TestProse:

    @pytest.mark.parametrize(
        "paquet", _PAQUETS, ids=[p.name for p in _PAQUETS])
    def test_aucun_document_ne_prete_une_maturite_propre(
        self, paquet: Path
    ) -> None:
        fautes: "list[str]" = []
        for document in _documents(paquet):
            for numero, ligne in enumerate(
                document.read_text(encoding="utf-8").splitlines(), 1
            ):
                if _MATURITE.search(ligne):
                    relatif = document.relative_to(PROJECT_ROOT).as_posix()
                    fautes.append(f"{relatif}:{numero} : {ligne.strip()[:80]}")

        assert not fautes, (
            f"{paquet.name} s'attribue une maturité propre.\n"
            "Un opt-in suit la version du cœur : une maturité annoncée par "
            "paquet dérive, et elle avait dérivé.\n  " + "\n  ".join(fautes))


class TestLeDetecteurDetecte:
    """Un détecteur qu'on ne met jamais en défaut peut être creux."""

    @pytest.mark.parametrize(
        "ligne",
        [
            "## Statut : Beta — opt-in officiel",
            "Statut : **Beta**. Upload et transcodage sont livrés.",
            "`forge-mvc-mfa` est en **Beta** (publié sur PyPI).",
            "API encore bêta, voir les limites de production.",
            "clé Fernet ne sont pas encore formalisées (exigences Beta restantes).",
        ],
    )
    def test_une_declaration_de_maturite_est_vue(self, ligne: str) -> None:
        assert _MATURITE.search(ligne), f"non détecté : {ligne!r}"

    @pytest.mark.parametrize(
        "ligne",
        [
            "La version bêta publique 1.0 est close depuis longtemps.",
            "Le paquet a été publié sous une numérotation antérieure.",
            "beta_test = 3",
            "Voir docs/history/ pour la trace des séries beta.",
        ],
    )
    def test_une_mention_historique_n_est_pas_accusee(self, ligne: str) -> None:
        """Un relevé qui accuse à tort se fait désactiver, et ne garde plus rien."""
        assert not _MATURITE.search(ligne), f"faux positif : {ligne!r}"
