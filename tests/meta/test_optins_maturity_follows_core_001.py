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

## Ce que ce garde-fou fige

La fin : la version d'un opt-in est celle du cœur, et aucune documentation de
paquet ne lui prête un cycle de maturité propre.

Il ne fige ni le numéro de version, qui change à chaque publication, ni le
classifieur, qui est une décision de release.
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


def _version(pyproject: Path) -> "str | None":
    trouve = re.search(r'^version\s*=\s*"([^"]+)"', 
                       pyproject.read_text(encoding="utf-8"), re.MULTILINE)
    return trouve.group(1) if trouve else None


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
_VERSION_COEUR = _version(PROJECT_ROOT / "pyproject.toml")


def test_le_releve_a_des_entrees() -> None:
    """Un garde-fou sans entrée est un garde-fou qui ne garde rien."""
    assert len(_PAQUETS) > 20, f"{len(_PAQUETS)} paquets trouvés"
    assert _VERSION_COEUR, "la version du cœur n'est plus lisible"


class TestVersion:

    @pytest.mark.parametrize(
        "paquet", _PAQUETS, ids=[p.name for p in _PAQUETS])
    def test_l_optin_porte_la_version_du_coeur(self, paquet: Path) -> None:
        """Un opt-in publié à une version différente laisserait croire à un
        cycle de vie séparé, et obligerait à tenir une matrice de
        compatibilité que Forge n'entretient pas."""
        assert _version(paquet / "pyproject.toml") == _VERSION_COEUR, (
            f"{paquet.name} ne suit pas la version du cœur "
            f"({_VERSION_COEUR}) : les opt-ins n'ont pas de cycle propre.")


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
