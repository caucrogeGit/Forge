"""`META-DOC-ABSOLUTE-LINKS-001` — les liens absolus mènent quelque part.

`mkdocs build --strict` vérifie les liens **relatifs** et échoue sur un fichier
manquant. Il ne vérifie pas les liens **absolus** : il les signale d'une ligne
`INFO ... it was left as is` et poursuit, quelle que soit leur cible.

Ce n'est pas théorique. `DB-POOL-THREADS-DOC-001` a livré un lien vers
`/docs/forge/reference/database/connection/`, page qui n'existe pas, la vraie
étant `/docs/forge/core-database/connection/`. Le build strict l'a accepté sans
un mot, et la faute n'a été vue qu'en cherchant l'URL à la main.

Quarante-trois liens absolus vivent dans la documentation, dont vingt-six vers
une seule ancre. Une seule d'entre elles qui bouge casse vingt-six liens, en
silence, sur le site publié.

## Pourquoi reconstruire les URL plutôt que lire le site construit

Un contrôle qui exigerait `site/` se sauterait quand le dossier n'existe pas,
c'est à dire la plupart du temps, et un garde-fou sauté ne garde rien.

Les URL sont donc reconstruites depuis les sources, avec les mêmes règles que
MkDocs : le `docs_dir` de la racine, plus le `site_name` de chaque `!include`
qui sert de préfixe (`ADR-038`, `ADR-043`). La fonction de slug est **celle de
MkDocs**, importée et non réécrite : une réimplémentation approximative
inventerait des ancres fausses dans un sens comme dans l'autre.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from markdown.extensions.toc import slugify

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]

#: Préfixe d'URL du site publié. Un lien absolu qui ne le porte pas ne mène
#: nulle part depuis forgemvc.com.
PREFIXE_SITE = "/docs/forge/"

#: `](/chemin)` ou `](/chemin#ancre)`.
_LIEN_ABSOLU = re.compile(r"\]\((/[^)\s]+)\)")
_TITRE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
#: Ancre explicite d'`attr_list` : `## Titre {#mon-ancre}`.
_ANCRE_EXPLICITE = re.compile(r"\{#([^}]+)\}")

#: Racines de documentation lues. `official-site/` en est exclu : c'est un
#: vestige local, ni source ni intrant de publication.
_RACINES_SOURCE = ("docs", "packages", "core", "cli", "integrations")


def _valeur_yaml(texte: str, cle: str, defaut: str = "") -> str:
    """Valeur scalaire de premier niveau, sans dépendre d'un lecteur YAML."""
    trouve = re.search(rf"^{cle}:\s*(.+)$", texte, re.MULTILINE)
    return trouve.group(1).strip().strip("\"'") if trouve else defaut


def _pages(dossier_docs: Path, prefixe: str) -> "dict[str, Path]":
    """URL sans barres extrêmes vers le fichier source qui la produit."""
    rendu: "dict[str, Path]" = {}
    if not dossier_docs.is_dir():
        return rendu
    for markdown in dossier_docs.rglob("*.md"):
        parties = list(markdown.relative_to(dossier_docs).with_suffix("").parts)
        if parties and parties[-1] == "index":
            parties.pop()
        rendu["/".join(p for p in [prefixe, *parties] if p)] = markdown
    return rendu


def _urls_du_site() -> "dict[str, Path]":
    """Toutes les pages que MkDocs produira, reconstruites depuis les sources."""
    racine_yml = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    urls = _pages(PROJECT_ROOT / _valeur_yaml(racine_yml, "docs_dir", "docs"), "")
    for inclus in re.findall(r"'!include ([^']+)'", racine_yml):
        chemin = PROJECT_ROOT / inclus
        if not chemin.is_file():
            continue
        texte = chemin.read_text(encoding="utf-8")
        urls.update(_pages(
            chemin.parent / _valeur_yaml(texte, "docs_dir", "docs"),
            _valeur_yaml(texte, "site_name"),
        ))
    return urls


def _ancres(source: Path) -> "set[str]":
    texte = source.read_text(encoding="utf-8")
    trouvees: "set[str]" = set()
    for titre in _TITRE.findall(texte):
        explicite = _ANCRE_EXPLICITE.search(titre)
        if explicite is not None:
            trouvees.add(explicite.group(1))
            titre = _ANCRE_EXPLICITE.sub("", titre).strip()
        trouvees.add(slugify(titre, "-"))
    return trouvees


def _liens_absolus() -> "list[tuple[Path, str]]":
    releve: "list[tuple[Path, str]]" = []
    for racine in _RACINES_SOURCE:
        base = PROJECT_ROOT / racine
        if not base.is_dir():
            continue
        for markdown in base.rglob("*.md"):
            chemin = markdown.as_posix()
            if "official-site" in chemin or "/site/" in chemin or "/build/" in chemin:
                continue
            for lien in _LIEN_ABSOLU.findall(markdown.read_text(encoding="utf-8")):
                releve.append((markdown, lien))
    return releve


_LIENS = _liens_absolus()
_URLS = _urls_du_site()


def test_le_releve_a_des_entrees() -> None:
    """Un garde-fou sans entrée est un garde-fou qui ne garde rien.

    Il est déjà arrivé qu'un détecteur passe au vert parce qu'il ne trouvait
    plus ses fichiers.
    """
    assert _LIENS, "aucun lien absolu trouvé : le relevé ne lit plus les sources"
    assert len(_URLS) > 500, f"seulement {len(_URLS)} pages reconstruites"


def test_toute_page_reconstruite_existe_vraiment() -> None:
    """La reconstruction doit décrire le site, pas un site imaginaire."""
    for url, source in list(_URLS.items())[:50]:
        assert source.is_file(), f"{url} pointe un fichier absent"


class TestLiensAbsolus:

    @pytest.mark.parametrize(
        "source,lien",
        _LIENS,
        ids=[f"{s.relative_to(PROJECT_ROOT).as_posix()}->{c}" for s, c in _LIENS],
    )
    def test_chaque_lien_absolu_mene_a_une_page(self, source: Path, lien: str) -> None:
        chemin, _, ancre = lien.partition("#")
        relatif = source.relative_to(PROJECT_ROOT).as_posix()

        assert chemin.startswith(PREFIXE_SITE), (
            f"{relatif} : le lien absolu {chemin!r} ne porte pas le préfixe "
            f"{PREFIXE_SITE!r} et ne mènera nulle part depuis le site publié.")

        cible = chemin[len(PREFIXE_SITE):].strip("/")
        assert cible in _URLS, (
            f"{relatif} : {chemin} ne correspond à aucune page.\n"
            f"MkDocs strict accepte ce lien sans un mot : il ne vérifie que les "
            f"liens relatifs.\n"
            f"Le préfixe d'URL d'une doc embarquée est le `site_name` de son "
            f"mkdocs.yml, pas son chemin de fichier.")

        if ancre:
            assert ancre in _ancres(_URLS[cible]), (
                f"{relatif} : la page {chemin} existe, mais son ancre "
                f"#{ancre} n'y est pas.\n"
                f"Un titre reformulé change son ancre, et casse le lien en "
                f"silence.")


class TestLeDetecteurDetecte:
    """Un détecteur qu'on ne met jamais en défaut peut être creux."""

    def test_une_page_inexistante_est_vue(self) -> None:
        """Le lien exact qui a motivé ce garde-fou."""
        faux = "/docs/forge/reference/database/connection/"

        assert faux[len(PREFIXE_SITE):].strip("/") not in _URLS

    def test_la_page_reelle_est_vue(self) -> None:
        assert "core-database/connection" in _URLS

    def test_une_ancre_inventee_est_vue(self) -> None:
        source = _URLS["install/opt-ins"]

        assert "une-ancre-qui-n-existe-pas" not in _ancres(source)

    def test_l_ancre_des_vingt_six_liens_existe(self) -> None:
        """Une seule ancre porte la majorité des liens absolus du dépôt.

        La reformuler casserait vingt-six liens d'un coup, sans que le build
        strict n'en dise rien.
        """
        source = _URLS["install/opt-ins"]

        assert "rendre-un-opt-in-operationnel-les-cinq-points" in _ancres(source)
