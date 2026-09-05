"""DEPLOY-CHECK-STORAGE-WRITABLE-001 : le stockage est-il inscriptible ?

Le pré-vol vérifiait que `storage/` et `storage/uploads/` **existent**, jamais
qu'ils soient inscriptibles par le compte qui fera l'écriture. Les deux se
séparent très facilement : le dossier est créé par celui qui déploie, souvent
root, et le service tourne sous un compte dédié.

La panne ne se voit alors ni au démarrage ni dans aucun contrôle. Elle attend
le **premier téléversement** d'un utilisateur, en production, et se présente
comme une erreur cinq cents sans rapport apparent avec le déploiement.

Deux causes distinctes donnent ce même symptôme, et les deux sont couvertes :
le propriétaire et le mode du dossier, puis le durcissement
`ProtectSystem=strict`, qui remonte le disque en lecture seule et rend le
dossier inscriptible pour personne quels que soient ses droits.
"""
from __future__ import annotations

import getpass
from pathlib import Path

import pytest

from forge_mvc_deploy.cli.deploy import (
    ECRIRE_DOSSIER,
    LIRE,
    _peut_acceder,
    _verifier_stockage_inscriptible,
)

MOI = getpass.getuser()


@pytest.fixture(autouse=True)
def _rendre_les_dossiers_effacables(tmp_path: Path):
    """Rend les droits avant le nettoyage de pytest.

    Un test laisse volontairement un dossier en `500`. Sans cette remise en
    état, pytest ne peut plus le vider et avertit à la fin de la session, bruit
    qui finirait par masquer un vrai problème.
    """
    yield
    for chemin in tmp_path.rglob("*"):
        if chemin.is_dir():
            chemin.chmod(0o755)


def _projet(tmp_path: Path, unite: str, mode: int = 0o755) -> "tuple[Path, Path]":
    (tmp_path / "deploy" / "systemd").mkdir(parents=True)
    (tmp_path / "storage" / "uploads").mkdir(parents=True)
    (tmp_path / "storage" / "uploads").chmod(mode)
    chemin_unite = tmp_path / "deploy" / "systemd" / "forge-app.service"
    chemin_unite.write_text(unite, encoding="utf-8")
    return tmp_path, chemin_unite


BASE = "[Service]\nUser={u}\nWorkingDirectory=/srv/app\n"


class TestDroitsDuDossier:

    def test_un_dossier_inscriptible_passe(self, tmp_path: Path) -> None:
        racine, unite = _projet(tmp_path, BASE.format(u=MOI), 0o755)

        resultat = _verifier_stockage_inscriptible(racine, unite)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_un_dossier_en_lecture_seule_est_une_erreur(self, tmp_path: Path) -> None:
        racine, unite = _projet(tmp_path, BASE.format(u=MOI), 0o500)

        resultat = _verifier_stockage_inscriptible(racine, unite)

        assert resultat is not None
        assert resultat.status == "error"

    def test_l_ecriture_sans_traversee_est_refusee(self, tmp_path: Path) -> None:
        """Mode 600 : le bit d'écriture est là, entrer dans le dossier non.

        Ne vérifier que l'écriture rendrait ici un « autorisé » que la création
        du fichier démentirait.
        """
        racine, unite = _projet(tmp_path, BASE.format(u=MOI), 0o600)

        resultat = _verifier_stockage_inscriptible(racine, unite)

        assert resultat is not None
        assert resultat.status == "error"

    def test_le_message_nomme_le_geste_juste(self, tmp_path: Path) -> None:
        """La sortie de secours évidente, le 777, est celle qu'il ne faut pas."""
        racine, unite = _projet(tmp_path, BASE.format(u=MOI), 0o500)

        resultat = _verifier_stockage_inscriptible(racine, unite)

        assert resultat is not None
        assert "chown" in resultat.detail
        assert "777" in resultat.detail

    def test_le_message_dit_quand_la_panne_surviendra(self, tmp_path: Path) -> None:
        racine, unite = _projet(tmp_path, BASE.format(u=MOI), 0o500)

        resultat = _verifier_stockage_inscriptible(racine, unite)

        assert resultat is not None
        assert "téléversement" in resultat.detail


class TestDurcissementSystemd:

    def test_protect_system_strict_sans_le_chemin_est_une_erreur(
        self, tmp_path: Path
    ) -> None:
        """Les droits peuvent être parfaits : le disque est en lecture seule."""
        racine, unite = _projet(
            tmp_path, BASE.format(u=MOI) + "ProtectSystem=strict\n", 0o755)

        resultat = _verifier_stockage_inscriptible(racine, unite)

        assert resultat is not None
        assert resultat.status == "error"
        assert "ReadWritePaths" in resultat.detail

    def test_protect_system_strict_avec_le_chemin_passe(self, tmp_path: Path) -> None:
        racine, unite = _projet(tmp_path, BASE.format(u=MOI), 0o755)
        unite.write_text(
            BASE.format(u=MOI)
            + f"ProtectSystem=strict\nReadWritePaths={racine / 'storage'}\n",
            encoding="utf-8")

        resultat = _verifier_stockage_inscriptible(racine, unite)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_sans_durcissement_seuls_les_droits_comptent(self, tmp_path: Path) -> None:
        racine, unite = _projet(tmp_path, BASE.format(u=MOI), 0o755)

        resultat = _verifier_stockage_inscriptible(racine, unite)

        assert resultat is not None
        assert resultat.status == "ok"


class TestQuestionsNonTranchables:
    """Le pré-vol se lance souvent ailleurs qu'en production."""

    def test_un_compte_inconnu_avertit_sans_accuser(self, tmp_path: Path) -> None:
        racine, unite = _projet(tmp_path, BASE.format(u="forge-app-inexistant"), 0o755)

        resultat = _verifier_stockage_inscriptible(racine, unite)

        assert resultat is not None
        assert resultat.status == "warn"

    def test_sans_unite_le_controle_se_tait(self, tmp_path: Path) -> None:
        (tmp_path / "storage" / "uploads").mkdir(parents=True)

        assert _verifier_stockage_inscriptible(
            tmp_path, tmp_path / "absent.service") is None

    def test_sans_utilisateur_declare_le_controle_se_tait(self, tmp_path: Path) -> None:
        racine, unite = _projet(tmp_path, "[Service]\nWorkingDirectory=/srv/app\n")

        assert _verifier_stockage_inscriptible(racine, unite) is None

    def test_sans_dossier_le_controle_se_tait(self, tmp_path: Path) -> None:
        """Son absence est déjà signalée ailleurs ; deux lignes vaudraient moins."""
        (tmp_path / "deploy" / "systemd").mkdir(parents=True)
        unite = tmp_path / "deploy" / "systemd" / "forge-app.service"
        unite.write_text(BASE.format(u=MOI), encoding="utf-8")

        assert _verifier_stockage_inscriptible(tmp_path, unite) is None


class TestPrimitiveDeDroits:

    def test_un_compte_absent_de_la_machine_rend_indecidable(
        self, tmp_path: Path
    ) -> None:
        """La primitive raisonne sur un **nom de compte**, pas sur le processus.

        Une implémentation par `os.access` répondrait ici du compte qui lance
        le pré-vol, souvent root ou celui qui déploie, c'est à dire à une autre
        question que celle posée.
        """
        assert _peut_acceder(tmp_path, "compte-inexistant-xyz", droits=LIRE) is None

    @pytest.mark.parametrize("mode,attendu", [
        (0o700, True), (0o500, False), (0o600, False), (0o300, True),
    ])
    def test_ecrire_dans_un_dossier_demande_ecriture_et_traversee(
        self, tmp_path: Path, mode: int, attendu: bool
    ) -> None:
        cible = tmp_path / "d"
        cible.mkdir()
        cible.chmod(mode)

        assert _peut_acceder(cible, MOI, droits=ECRIRE_DOSSIER) is attendu
