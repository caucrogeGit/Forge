"""L'empreinte de contrat des fichiers engendrés (GENERATED-CONTRACT-MARKER-001, ADR-090).

Forge engendre du code puis ne le retouche plus, et c'est le principe 9.
La conséquence est qu'un correctif livré dans un générateur **n'atteint aucune
application déjà engendrée**, et que son auteur ne l'apprend pas.

Le cycle en cours le démontre plutôt que de le supposer : `AUTH-CASE-ASYMMETRY-001`
a rouvert la connexion sur SQLite, `AUTH-IDENTITY-CONTACT-001` a renommé la
colonne d'identité, et les deux vivent dans `cli/security/make_auth.py`.
La seule application Forge existante porte une copie du contrôleur d'avant.

Ce fichier vérifie que l'écart se voit, et surtout qu'il ne se voit **pas** dans
les cas où le signaler serait du bruit.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli._support.generated_marker import (
    CONTRATS,
    contrat_du_fichier,
    ligne_de_marqueur,
    montees_manquees,
)
from cli.project.doctor import check_generated_contracts

pytestmark = pytest.mark.meta


def _projet(tmp_path: Path, *, controleur: "str | None") -> Path:
    """Projet minimal portant, ou non, un contrôleur d'authentification."""
    dossier = tmp_path / "mvc" / "controllers"
    dossier.mkdir(parents=True)
    if controleur is not None:
        (dossier / "auth_controller.py").write_text(controleur, encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# Le format de l'empreinte
# ---------------------------------------------------------------------------


def test_le_generateur_emet_son_empreinte() -> None:
    """Un fichier engendré aujourd'hui porte le contrat courant."""
    from cli.security.make_auth import AUTH_CONTROLLER, AUTH_USER_MODEL

    marqueur = ligne_de_marqueur("make:auth")
    for gabarit in (AUTH_CONTROLLER, AUTH_USER_MODEL):
        rendu = gabarit.replace("{marqueur}", marqueur)
        assert rendu.splitlines()[0] == marqueur


def test_l_empreinte_se_relit() -> None:
    """Ce que le générateur écrit, le contrôle doit savoir le lire."""
    chemin = Path(__file__).parent / "__inexistant__"
    assert contrat_du_fichier(chemin) is None


def test_l_empreinte_ne_porte_ni_condensat_ni_version_de_framework() -> None:
    """C'est la décision qui fait tenir tout le reste (ADR-090).

    Un condensat du contenu serait faux dès la première ligne ajoutée par
    l'auteur, un fichier engendré étant fait pour être édité. La version du
    framework ferait crier à chaque montée, y compris celles qui n'ont rien
    changé au générateur concerné.
    """
    import inspect

    from cli._support import generated_marker

    source = inspect.getsource(generated_marker)

    assert "hashlib" not in source and "sha256" not in source
    assert "__version__" not in source


# ---------------------------------------------------------------------------
# Les trois issues du contrôle
# ---------------------------------------------------------------------------


def test_un_fichier_a_jour_ne_dit_rien(tmp_path: Path) -> None:
    """Le silence est la réponse la plus fréquente, et la plus importante.

    Un contrôle qui parle à chaque passage s'apprend à être ignoré.
    """
    racine = _projet(tmp_path, controleur=ligne_de_marqueur("make:auth") + "\n# du code\n")

    resultat = check_generated_contracts(racine)

    assert resultat.status == "ok"


def test_un_fichier_en_retard_est_nomme_et_explique(tmp_path: Path) -> None:
    """« En retard » sans dire de quoi se désapprend en trois semaines."""
    racine = _projet(tmp_path, controleur="# forge:generated make:auth contrat=1\n# du code\n")

    resultat = check_generated_contracts(racine)

    assert resultat.status in ("warn", "fail")
    assert "auth_controller.py" in resultat.detail
    assert "login" in resultat.detail, "le message doit dire CE QUI a changé"
    assert "ne réécrit pas" in resultat.detail, "le geste attendu doit être donné"


def test_une_montee_de_securite_est_signalee_comme_telle(tmp_path: Path) -> None:
    """Un correctif de sécurité non reporté n'est pas un simple retard."""
    racine = _projet(tmp_path, controleur="# forge:generated make:auth contrat=1\n")

    resultat = check_generated_contracts(racine)

    assert "SÉCURITÉ" in resultat.detail
    assert resultat.status == "fail"


def test_une_empreinte_absente_ne_fait_pas_accusation(tmp_path: Path) -> None:
    """Le contrôle dit qu'il ne sait pas, ce qui est vrai.

    Toutes les applications antérieures à l'ADR-090 sont dans ce cas, et un
    fichier dont l'auteur a effacé l'en-tête aussi. Les accuser d'être en
    retard serait faux dans les deux cas.
    """
    racine = _projet(tmp_path, controleur='"""Mon contrôleur à moi."""\n')

    resultat = check_generated_contracts(racine)

    assert resultat.status == "warn"
    assert "inconnue" in resultat.detail
    assert "retard" not in resultat.detail


def test_un_projet_sans_authentification_ne_dit_rien(tmp_path: Path) -> None:
    """Un fichier absent n'est pas un fichier en retard."""
    racine = _projet(tmp_path, controleur=None)

    assert check_generated_contracts(racine).status == "ok"


def test_un_fichier_largement_modifie_ne_declenche_rien(tmp_path: Path) -> None:
    """C'est tout l'intérêt du write-if-new : le fichier est fait pour être édité.

    Tant que le générateur n'a pas bougé, l'auteur peut le réécrire de fond en
    comble sans que le contrôle ait quoi que ce soit à dire.
    """
    corps = ligne_de_marqueur("make:auth") + "\n" + "\n".join(
        f"def ma_fonction_{i}(): ..." for i in range(60)
    )
    racine = _projet(tmp_path, controleur=corps)

    assert check_generated_contracts(racine).status == "ok"


# ---------------------------------------------------------------------------
# Le registre des contrats
# ---------------------------------------------------------------------------


def test_chaque_montee_est_decrite() -> None:
    """Un contrat sans registre rend l'avertissement intraduisible en geste."""
    for commande, contrat in CONTRATS.items():
        numeros = {m.contrat for m in contrat.montees}
        attendus = set(range(2, contrat.contrat + 1))
        assert numeros == attendus, (
            f"{commande} : contrat {contrat.contrat} mais montées décrites {sorted(numeros)}"
        )
        for montee in contrat.montees:
            assert len(montee.resume) > 40, f"{commande} v{montee.contrat} : résumé trop court"


def test_montees_manquees_est_vide_quand_a_jour() -> None:
    for commande, contrat in CONTRATS.items():
        assert montees_manquees(commande, contrat.contrat) == ()


def test_un_generateur_inconnu_ne_fait_pas_echouer() -> None:
    """Un fichier engendré par un générateur retiré ne doit pas casser le contrôle."""
    assert montees_manquees("make:disparu", 1) == ()


# ---------------------------------------------------------------------------
# La dette listée (ADR-090, point 5)
# ---------------------------------------------------------------------------

#: Modules qui écrivent du code utilisateur sans porter encore d'empreinte.
#: Une exclusion muette rendrait le relevé rassurant et faux.
_DETTE_CONNUE = {
    "cli/public/_shared.py": "générateurs de pages publiques (make:public-list, show, form)",
    "cli/_support/scaffold.py": "squelette de projet posé par forge new",
    "cli/agents/emit.py": "fichiers de briefing agent, déjà couverts par agents:init --check",
    "cli/security/auth.py": "fichiers SQL de auth:init, pas du code Python",
    "packages/forge-mvc-entities/forge_mvc_entities/make_crud.py": "CRUD engendré",
    "packages/forge-mvc-entities/forge_mvc_entities/make_pivot_crud.py": "CRUD de pivot",
    "packages/forge-mvc-entities/forge_mvc_entities/model.py": "modèle d'entité",
    "packages/forge-mvc-admin/forge_mvc_admin/cli/init.py": "back-office",
    "packages/forge-mvc-deploy/forge_mvc_deploy/cli/deploy.py": "unités systemd et nginx",
}


def test_la_dette_est_nommee_et_ses_fichiers_existent() -> None:
    """Un cliquet : une entrée dont le fichier a disparu doit être retirée.

    Sans lui, la liste ne ferait que grandir et le relevé se viderait de son
    sens, exactement comme les cliquets DDL et DML de ce dépôt.
    """
    racine = Path(__file__).resolve().parent.parent
    absents = [rel for rel in _DETTE_CONNUE if not (racine / rel).is_file()]

    assert not absents, (
        "Ces modules n'existent plus : retirez-les de _DETTE_CONNUE.\n  "
        + "\n  ".join(absents)
    )
