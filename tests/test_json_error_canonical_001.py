"""CORE-API-ERROR-CANONICAL-001 : une seule fabrique de réponse d'erreur JSON.

Forge portait deux formes d'erreur JSON, l'enveloppe déclarée dans
`core/http/helpers.py` et une forme plate qu'aucun document ne décrivait. Un
client recevait l'une ou l'autre selon la route touchée. L'ADR-088 a tranché
pour la forme plate, celle que les trois opt-ins exposant du JSON avaient
choisie seuls.

Ce fichier verrouille deux choses.

La **forme** rendue par `json_error`, qui est désormais le contrat public.

Et surtout le **garde-fou de convergence** : aucun module ne construit une
réponse d'erreur JSON ailleurs que par cette fabrique. Sans lui la divergence
recommencerait, puisque c'est exactement ainsi qu'elle est née, chaque paquet
ayant réinventé sa forme faute d'en trouver une.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from core.http import json_error

_RACINE = Path(__file__).resolve().parent.parent

#: Seul module autorisé à composer un corps d'erreur JSON.
_FABRIQUE = "core/http/helpers.py"

_EXCLUS = ("/build/", "/dist/", "/__pycache__/", ".egg-info", "/official-site/", "/tests/")


# ── La forme rendue ──────────────────────────────────────────────────────────


def test_la_forme_est_plate() -> None:
    reponse = json_error("not_found", 404)

    assert json.loads(reponse.body.decode("utf-8")) == {"error": "not_found"}
    assert reponse.status == 404
    assert reponse.content_type.startswith("application/json")


def test_le_message_est_absent_par_defaut() -> None:
    """Un refus qui explique à quelle étape il a eu lieu renseigne l'attaquant."""
    corps = json.loads(json_error("unauthorized", 401).body.decode("utf-8"))

    assert corps == {"error": "unauthorized"}
    assert "message" not in corps


def test_le_message_accompagne_une_erreur_de_validation() -> None:
    """Seul cas prévu : le client a besoin de savoir quoi corriger."""
    corps = json.loads(
        json_error("invalid_limit", 400, message="limit doit être >= 1").body.decode("utf-8")
    )

    assert corps == {"error": "invalid_limit", "message": "limit doit être >= 1"}


def test_il_n_y_a_pas_d_enveloppe_de_succes_en_regard() -> None:
    """Une réponse de succès rend la ressource, le code HTTP dit le succès."""
    corps = json.loads(json_error("x", 500).body.decode("utf-8"))

    assert "success" not in corps
    assert "data" not in corps


@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 422, 500, 503])
def test_le_statut_est_celui_demande(status: int) -> None:
    assert json_error("x", status).status == status


# ── Le garde-fou de convergence ──────────────────────────────────────────────


def _fichiers_production() -> list[Path]:
    trouves: list[Path] = []
    trouves.extend((_RACINE / "core").rglob("*.py"))
    for paquet in sorted((_RACINE / "packages").glob("forge-mvc-*")):
        for module in paquet.glob("forge_mvc_*"):
            if module.is_dir():
                trouves.extend(module.rglob("*.py"))
    return sorted(
        c for c in trouves if not any(f in c.as_posix() for f in _EXCLUS)
    )


def _compose_une_erreur(noeud: ast.Call) -> bool:
    """L'appel construit-il un corps JSON portant une clé `error` ?

    On ne juge que les dictionnaires **littéraux** : une clé calculée ne se lit
    pas statiquement, et un garde-fou qui devine produit des faux positifs, donc
    finit désactivé.
    """
    fonction = noeud.func
    nom = fonction.attr if isinstance(fonction, ast.Attribute) else getattr(fonction, "id", "")
    if nom not in ("json", "json_response"):
        return False
    if not noeud.args:
        return False
    premier = noeud.args[0]
    if not isinstance(premier, ast.Dict):
        return False
    return any(
        isinstance(cle, ast.Constant) and cle.value == "error"
        for cle in premier.keys
        if cle is not None
    )


def test_le_balayage_trouve_bien_du_code() -> None:
    """Un balayage qui ne lit rien passerait toujours, donc ne prouverait rien."""
    assert len(_fichiers_production()) > 150


def test_aucune_erreur_json_n_est_composee_hors_de_la_fabrique() -> None:
    """La divergence est née de l'absence d'un endroit unique. Il y en a un.

    Le correctif est toujours le même : appeler `core.http.json_error`.
    """
    fautes: list[str] = []
    for chemin in _fichiers_production():
        relatif = chemin.relative_to(_RACINE).as_posix()
        if relatif == _FABRIQUE:
            continue
        try:
            arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Call) and _compose_une_erreur(noeud):
                fautes.append(f"{relatif}:{noeud.lineno}")

    assert not fautes, (
        "corps d'erreur JSON composé hors de core.http.json_error :\n  "
        + "\n  ".join(fautes)
        + "\n\nAppeler json_error(code, status, message=...) à la place."
    )


def test_les_trois_opt_ins_json_passent_par_la_fabrique() -> None:
    """Contrôle nommé : ce sont eux qui avaient divergé, ils doivent converger."""
    for paquet in ("iot", "video", "audio"):
        chemin = _RACINE / "packages" / f"forge-mvc-{paquet}" / f"forge_mvc_{paquet}" / "http.py"
        if not chemin.is_file():
            continue
        source = chemin.read_text(encoding="utf-8")
        assert "json_error" in source, f"{paquet} n'emploie pas la fabrique canonique"
