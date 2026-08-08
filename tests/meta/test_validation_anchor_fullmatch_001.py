"""Garde-fou VALIDATION-ANCHOR-FULLMATCH-001.

Une liste blanche ancrée doit refuser ce qu'elle prétend interdire.

En Python, `$` n'ancre pas tout à fait la fin de la chaîne.
Il accepte aussi la position qui précède un saut de ligne final.
Mesuré, `re.compile(r"^[a-z]+$").match("ab\\n")` retourne un objet `Match`,
alors que la même expression avec `fullmatch()` retourne `None`.

Conséquence, tout validateur écrit en `^...$` puis appelé avec `match()` laisse
passer sa valeur suffixée d'un saut de ligne.
Aucun cas exploitable n'a été trouvé dans le dépôt, rien ne peut suivre ce saut
de ligne, mais plusieurs de ces valeurs servent ensuite à composer un chemin de
fichier ou un identifiant SQL.
Une défense en profondeur ne se juge pas à son exploitabilité du jour.

Une partie des sites était déjà couverte par accident.
`core/modules/manifest.py`, `core/sessions/access.py`, `forge_mvc_stats` et
`forge_mvc_workflow` appliquent un `.strip()` avant de valider, ce qui retirait
le saut de ligne avant qu'il atteigne l'expression.
Leur conversion reste utile, la protection ne doit pas dépendre d'un nettoyage
que l'appelant suivant pourrait ne pas faire.
Six validateurs, eux, laissaient réellement passer la valeur suffixée.

Le dépôt employait les deux formes.
`core/forms/fields.py`, `forge_mvc_files/storage.py` et `forge_mvc_entities`
appelaient déjà `fullmatch()`, les autres couches appelaient `match()`.
Le ticket a retenu `fullmatch()` partout, principe 11.

Ce garde-fou ne porte aucune liste de sites.
Il relit le dépôt et détecte l'idiome, donc un site nouveau le fait échouer
sans que personne ait à penser à l'inscrire ici.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

_REPO_ROOT = Path(__file__).resolve().parents[2]

#: Racines de code de production balayées par le garde-fou.
_RACINES = ("core", "cli", "tools", "skeleton")

#: Fragments de chemin exclus, ce sont des copies ou du code hors production.
_EXCLUS = ("/build/", "/tests/", "/__pycache__/", ".egg-info", "/official-site/",
           "/node_modules/", "/dist/")


def _fichiers_python() -> list[Path]:
    """Fichiers de production du dépôt, paquets opt-in compris."""
    trouves: list[Path] = []
    for racine in _RACINES:
        trouves.extend((_REPO_ROOT / racine).rglob("*.py"))
    for paquet in sorted((_REPO_ROOT / "packages").glob("forge-mvc-*")):
        for module in paquet.glob("forge_mvc_*"):
            if module.is_dir():
                trouves.extend(module.rglob("*.py"))
    forge_py = _REPO_ROOT / "forge.py"
    if forge_py.is_file():
        trouves.append(forge_py)
    return sorted(
        chemin for chemin in trouves
        if not any(fragment in chemin.as_posix() for fragment in _EXCLUS)
    )


def _est_multiline(appel: ast.Call) -> bool:
    """Vrai si l'appel `re.compile` porte le drapeau `MULTILINE`.

    Sous ce drapeau, `$` ancre volontairement une fin de ligne et non une fin
    de chaîne.
    Ces expressions analysent du texte multiligne, elles ne valident rien.
    """
    for noeud in list(appel.args[1:]) + [kw.value for kw in appel.keywords]:
        for sous_noeud in ast.walk(noeud):
            if isinstance(sous_noeud, ast.Attribute) and sous_noeud.attr in {"MULTILINE", "M"}:
                return True
            if isinstance(sous_noeud, ast.Name) and sous_noeud.id in {"MULTILINE", "M"}:
                return True
    return False


def _est_re_compile(appel: ast.Call) -> bool:
    fonction = appel.func
    if isinstance(fonction, ast.Attribute):
        return fonction.attr == "compile"
    return isinstance(fonction, ast.Name) and fonction.id == "compile"


def _validateurs_ancres(arbre: ast.Module) -> set[str]:
    """Noms des variables affectées à une expression ancrée par `^` et `$`."""
    noms: set[str] = set()
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Assign) or len(noeud.targets) != 1:
            continue
        cible = noeud.targets[0]
        if not isinstance(cible, ast.Name):
            continue
        valeur = noeud.value
        if not isinstance(valeur, ast.Call) or not _est_re_compile(valeur):
            continue
        if not valeur.args:
            continue
        motif = valeur.args[0]
        if not isinstance(motif, ast.Constant) or not isinstance(motif.value, str):
            continue
        if not (motif.value.startswith("^") and motif.value.endswith("$")):
            continue
        if _est_multiline(valeur):
            continue
        noms.add(cible.id)
    return noms


def _appels_match(arbre: ast.Module, noms: set[str]) -> list[tuple[str, int]]:
    """Appels `<nom>.match(...)` portant sur un validateur ancré."""
    fautifs: list[tuple[str, int]] = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Call):
            continue
        fonction = noeud.func
        if not isinstance(fonction, ast.Attribute) or fonction.attr != "match":
            continue
        receveur = fonction.value
        if isinstance(receveur, ast.Name) and receveur.id in noms:
            fautifs.append((receveur.id, noeud.lineno))
    return fautifs


def test_le_piege_du_dollar_est_reel() -> None:
    """Sans ce constat, le reste du garde-fou n'a pas de raison d'être."""
    motif = re.compile(r"^[a-z]+$")

    assert motif.match("ab\n") is not None
    assert motif.fullmatch("ab\n") is None
    assert motif.fullmatch("ab") is not None


def test_le_balayage_trouve_bien_du_code() -> None:
    """Un balayage qui ne lit rien passerait toujours, donc ne prouverait rien."""
    fichiers = _fichiers_python()

    assert len(fichiers) > 200, f"balayage suspect, {len(fichiers)} fichiers seulement"


def test_aucun_validateur_ancre_n_est_appele_avec_match() -> None:
    """Aucune liste blanche ancrée ne doit être consultée par `match()`.

    Le correctif est toujours le même, remplacer `match(` par `fullmatch(`.
    Si l'expression analyse du texte multiligne et non une valeur, lui poser le
    drapeau `re.MULTILINE` la sort du périmètre, ce qui est également correct.
    """
    fautes: list[str] = []
    for chemin in _fichiers_python():
        try:
            arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        noms = _validateurs_ancres(arbre)
        if not noms:
            continue
        for nom, ligne in _appels_match(arbre, noms):
            relatif = chemin.relative_to(_REPO_ROOT).as_posix()
            fautes.append(f"{relatif}:{ligne} — {nom}.match(), attendu {nom}.fullmatch()")

    assert not fautes, "validateurs ancrés consultés par match() :\n" + "\n".join(fautes)


def test_l_identifiant_de_session_refuse_un_saut_de_ligne_final(tmp_path: Path) -> None:
    """L'identifiant sert à composer `<dossier>/<identifiant>.json`.

    Un saut de ligne est un caractère légal dans un nom de fichier POSIX, donc
    la valeur tolérée atteignait bien le disque.
    """
    from core.sessions.file_store import FileSessionStore

    magasin = FileSessionStore(sessions_dir=tmp_path)
    valide = "a" * 64

    assert magasin._valid(valide) is True  # pyright: ignore[reportPrivateUsage]
    assert magasin._valid(valide + "\n") is False  # pyright: ignore[reportPrivateUsage]


def test_l_identifiant_sql_de_l_admin_refuse_un_saut_de_ligne_final() -> None:
    """Cas d'origine du ticket, la valeur est interpolée dans le SELECT."""
    pytest.importorskip("forge_mvc_admin")
    from forge_mvc_admin.exceptions import AdminResourceError
    from forge_mvc_admin.query import _ident  # pyright: ignore[reportPrivateUsage]

    assert _ident("titre") == "titre"
    with pytest.raises(AdminResourceError):
        _ident("titre\n")


def test_la_cle_de_parametre_refuse_un_saut_de_ligne_final() -> None:
    """Cas de forge-mvc-settings, aucun nettoyage n'a lieu avant la validation."""
    pytest.importorskip("forge_mvc_settings")
    from forge_mvc_settings.store import _validate_key  # pyright: ignore[reportPrivateUsage]
    from forge_mvc_settings.errors import SettingsError

    _validate_key("site.nom")
    with pytest.raises(SettingsError):
        _validate_key("site.nom\n")


def test_l_identifiant_d_entite_refuse_un_saut_de_ligne_final() -> None:
    """Cas de forge-mvc-entities, la valeur nomme une table ou une colonne."""
    pytest.importorskip("forge_mvc_entities")
    from forge_mvc_entities.service import _safe_identifier  # pyright: ignore[reportPrivateUsage]

    assert _safe_identifier("clients", "table") == "clients"
    with pytest.raises(ValueError):
        _safe_identifier("clients\n", "table")


def test_la_locale_i18n_refuse_un_saut_de_ligne_final() -> None:
    """La locale compose `<dossier>/<locale>.json`, son filtre dit interdire les chemins.

    Le validateur est vérifié au niveau de l'expression, la fonction appelante
    étant mise en cache par `lru_cache` et liée à un dossier de catalogues.
    """
    pytest.importorskip("forge_mvc_i18n")
    from forge_mvc_i18n.translator import _LOCALE_RE  # pyright: ignore[reportPrivateUsage]

    assert _LOCALE_RE.fullmatch("fr") is not None
    assert _LOCALE_RE.fullmatch("fr\n") is None
