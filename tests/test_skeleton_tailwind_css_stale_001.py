"""`SKELETON-TAILWIND-CSS-STALE-001` — le CSS livré couvre les gabarits livrés.

Le squelette versionne `static/tailwind.css`, construit par Tailwind depuis ses
propres gabarits. Ce fichier avait dérivé : il lui manquait **quinze classes**
que les gabarits utilisent, dont `grid`, `grid-cols-2`, `sm:grid-cols-4`,
`flex-wrap`, `bg-red-600`, `hover:bg-red-700` et `text-white`.

La conséquence n'est visible que là où on ne regarde pas. `forge new` reconstruit
le CSS par `npm install && npm run build:css`, ce qui masquait la dérive. Mais
**npm peut être absent**, cas que Forge gère explicitement par un avertissement,
et le projet part alors avec le fichier versionné. Sa page « charte » perd sa
grille, et le bouton `danger` de `components/ui.html` perd son fond rouge et son
texte blanc : un geste destructeur qui ne se distingue plus d'un lien ordinaire.

L'avertissement dit « Node.js / npm absent », pas « votre mise en page sera
fausse ». Personne ne relie les deux.

## Comment les classes sont relevées

Deux sources, parce qu'une seule ne suffit pas.

D'abord les attributs `class="..."`, expressions Jinja retirées. Exact, sans
ambiguïté, mais **aveugle là où le risque est le plus grand** : les classes qui
comptent vivent souvent dans une table de variantes,
`{% set styles = {"danger": "text-white bg-red-600 ..."} %}`, et pas dans un
attribut. Ce sont précisément celles qui manquaient.

Ensuite les chaînes entre guillemets dont **tous** les jetons ont la forme d'un
utilitaire Tailwind **et** dont au moins un est déjà dans le CSS. Cette ancre
n'est pas décorative : sans elle, la prose française des gabarits fournissait
quatre-vingt-dix-huit faux positifs, « avec », « toute », « valeur ». Un relevé
qui accuse à tort se fait désactiver, et ne garde alors plus rien.

## Ce que ce garde-fou ne voit pas, et pourquoi c'est dit

Mesuré contre le fichier périmé, il retrouve **douze** des quinze classes
manquantes. Les trois autres, `bg-forge-dark`, `bg-muted` et `bg-ocre`, ne
vivent dans aucune de ces deux formes.

Une couverture complète demanderait de lancer Tailwind, donc `npm`, donc de
sauter le contrôle partout où npm manque. Un garde-fou sauté ne garde rien :
douze sur quinze, toujours joués, valent mieux que quinze parfois.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKELETON = PROJECT_ROOT / "skeleton" / "data"
CSS = SKELETON / "static" / "tailwind.css"

#: Une expression Jinja dans un attribut `class`. Ses parties littérales
#: comptent, son expression non : `class="btn {{ extra }}"` porte bien `btn`.
_JINJA = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.DOTALL)
#: Guillemets doubles seulement. Accepter l'apostrophe couperait la valeur sur
#: `{{ tones['forge'] }}` et laisserait traîner le `or` du Jinja.
_CLASS_ATTR = re.compile(r'class\s*=\s*"([^"]*)"')
_CHAINE = re.compile(r'"([^"\n]*)"')
#: Forme d'un utilitaire Tailwind : variantes, racine, segments, valeur libre.
_FORME = re.compile(
    r"^(?:[a-z][a-z0-9-]*:)*-?[a-z][a-z0-9]*(?:-[a-z0-9.]+)*(?:\[[^\]]+\])?$")
#: Un sélecteur de classe dans le CSS, échappements compris.
_SELECTEUR = re.compile(r"\.((?:\\.|[-\w])+)")


def _echappe(classe: str) -> str:
    """Nom de classe tel que Tailwind l'écrit dans le CSS."""
    return re.sub(r"([:.\[\]/%(),#])", r"\\\1", classe)


def _gabarits() -> "list[Path]":
    return [g for g in SKELETON.rglob("*.html")
            if "node_modules" not in g.as_posix()]


def _classes_du_css() -> "set[str]":
    return set(_SELECTEUR.findall(CSS.read_text(encoding="utf-8")))


def _classes_des_gabarits(presentes: "set[str]") -> "dict[str, set[str]]":
    """Classes utilisées par les gabarits, vers les fichiers qui les portent."""
    utilisees: "dict[str, set[str]]" = {}
    for gabarit in _gabarits():
        texte = gabarit.read_text(encoding="utf-8")
        nom = gabarit.relative_to(SKELETON).as_posix()

        for valeur in _CLASS_ATTR.findall(texte):
            for jeton in _JINJA.sub(" ", valeur).split():
                if _FORME.match(jeton):
                    utilisees.setdefault(jeton, set()).add(nom)

        for valeur in _CHAINE.findall(texte):
            jetons = valeur.split()
            if len(jetons) < 2 or not all(_FORME.match(j) for j in jetons):
                continue
            if not any(_echappe(j) in presentes for j in jetons):
                continue
            for jeton in jetons:
                utilisees.setdefault(jeton, set()).add(nom)
    return utilisees


_PRESENTES = _classes_du_css()
_UTILISEES = _classes_des_gabarits(_PRESENTES)


class TestReleve:
    """Un relevé sans entrée est un relevé qui ne relève rien."""

    def test_le_squelette_versionne_son_css(self) -> None:
        assert CSS.is_file(), (
            "un projet créé sans npm n'aurait alors aucune feuille de style")

    def test_des_gabarits_sont_lus(self) -> None:
        assert len(_gabarits()) > 10
        assert len(_UTILISEES) > 100, (
            f"{len(_UTILISEES)} classes relevées : le relevé ne lit plus les "
            f"gabarits")

    def test_des_regles_sont_lues(self) -> None:
        assert len(_PRESENTES) > 150, (
            f"{len(_PRESENTES)} sélecteurs lus : le CSS n'est plus analysé")

    def test_node_modules_est_ignore(self) -> None:
        """Un `node_modules` local noierait le relevé de faux positifs."""
        for fichiers in _UTILISEES.values():
            assert not any("node_modules" in f for f in fichiers)


class TestCouverture:

    def test_chaque_classe_relevee_a_sa_regle(self) -> None:
        """Le contrôle décisif."""
        absentes = {
            classe: fichiers for classe, fichiers in _UTILISEES.items()
            if _echappe(classe) not in _PRESENTES
        }

        assert not absentes, (
            "Le CSS livré par le squelette ne couvre plus ses propres "
            "gabarits.\n"
            "Un projet créé sans npm partira avec cette mise en page fausse, "
            "et l'avertissement « npm absent » ne le dira pas.\n"
            "Reconstruire depuis skeleton/data/ :\n"
            "  npm install && npm run build:css\n"
            "puis versionner static/tailwind.css.\n  "
            + "\n  ".join(
                f"{classe} — {', '.join(sorted(fichiers))}"
                for classe, fichiers in sorted(absentes.items())))

    @pytest.mark.parametrize(
        "classe,role",
        [
            ("grid", "mise en page de la page charte"),
            ("grid-cols-2", "mise en page de la page charte"),
            ("sm:grid-cols-4", "mise en page de la page charte"),
            ("flex-wrap", "mise en page de la page charte"),
            ("text-4xl", "titre de la page charte"),
            ("bg-red-600", "fond du bouton de suppression"),
            ("hover:bg-red-700", "survol du bouton de suppression"),
            ("text-white", "texte du bouton de suppression"),
        ],
    )
    def test_les_classes_qui_manquaient_sont_couvertes(
        self, classe: str, role: str
    ) -> None:
        """Nommées une à une, pour que la régression se lise sans enquête.

        Sans `bg-red-600` ni `text-white`, un geste destructeur ne se distingue
        plus d'un lien ordinaire.
        """
        assert classe in _UTILISEES, (
            f"{classe} ({role}) n'est plus relevée : retirer cette ligne "
            f"plutôt que de la laisser garder un usage disparu")
        assert _echappe(classe) in _PRESENTES, (
            f"{classe} ({role}) manque au CSS livré")


class TestMethode:
    """Le relevé doit être exact, sinon il se fait désactiver."""

    def test_une_expression_jinja_ne_devient_pas_une_classe(self) -> None:
        assert _JINJA.sub(" ", "btn {{ extra }} actif").split() == ["btn", "actif"]

    def test_un_attribut_a_apostrophe_interne_n_est_pas_coupe(self) -> None:
        """`{{ tones['forge'] }}` laissait traîner le `or` du Jinja."""
        attribut = '<span class="px-3 {{ tones.get(t) or tones[\'forge\'] }}">'
        valeur = _CLASS_ATTR.findall(attribut)[0]

        assert _JINJA.sub(" ", valeur).split() == ["px-3"]

    def test_les_classes_echappees_sont_reconnues(self) -> None:
        assert _echappe("sm:grid-cols-4") == "sm\\:grid-cols-4"
        assert _echappe("hover:bg-red-700") == "hover\\:bg-red-700"

    def test_une_table_de_variantes_jinja_est_relevee(self) -> None:
        """La forme qui portait les classes manquantes."""
        assert "bg-red-600" in _UTILISEES
        assert "mvc/views/components/ui.html" in _UTILISEES["bg-red-600"]

    def test_la_prose_francaise_n_est_pas_prise_pour_des_classes(self) -> None:
        """Sans l'ancre, quatre-vingt-dix-huit mots devenaient des classes."""
        for mot in ("avec", "toute", "valeur", "chaleureux", "recompilez"):
            assert mot not in _UTILISEES, (
                f"« {mot} » est de la prose, pas une classe Tailwind")
