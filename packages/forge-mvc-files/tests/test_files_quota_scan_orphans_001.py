"""FILES-QUOTA-001, FILES-SCAN-HOOK-001 et FILES-ORPHAN-PURGE-001.

Le registre de l'ADR-094 sait ce qu'un propriétaire a déposé. Trois gestes en
découlent, et chacun porte un piège qui ne se voit pas à l'usage courant.

- Un quota lu puis appliqué n'est pas atomique, et le prétendre serait faux.
- Une analyse antivirus en panne ne dit pas qu'un fichier est sain.
- Une purge d'orphelins sur un registre vide efface tout le dossier d'upload.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import pytest

from core.forms.upload_exceptions import UploadError
from forge_mvc_files.orphans import (
    DEFAULT_MIN_AGE_SECONDS,
    OrphanPurgeRefused,
    find_orphans,
    purge_orphans,
)
from forge_mvc_files.quota import (
    FilesQuotaError,
    Quota,
    QuotaExceededError,
    check_quota,
    quota_for,
    quota_usage,
)
from forge_mvc_files.registry import record_file
from forge_mvc_files.scan import (
    ScannerUnavailableError,
    ScanVerdict,
    UploadRejectedByScanError,
    clear_file_scanners,
    register_file_scanner,
    registered_scanners,
    scan_upload,
    unregister_file_scanner,
)


class _FauxDb:
    """Registre en mémoire, aux mêmes requêtes que le vrai."""

    def __init__(self) -> None:
        self.rows: dict[str, tuple[Any, ...]] = {}

    def execute(self, sql: str, params: Any) -> int:
        if "INSERT" in sql:
            self.rows[params[0]] = params
            return 1
        if "DELETE" in sql:
            return 1 if self.rows.pop(params[0], None) is not None else 0
        return 0

    def fetch_one(self, sql: str, params: Any) -> "dict[str, Any] | None":
        vises = [
            r for r in self.rows.values() if (r[4], r[5]) == (params[0], params[1])
        ]
        if "SUM" in sql:
            return {"total": sum(int(r[3]) for r in vises)}
        if "COUNT" in sql:
            return {"total": len(vises)}
        return None

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        return [{"path": k} for k in sorted(self.rows)]


@pytest.fixture
def db() -> _FauxDb:
    return _FauxDb()


@pytest.fixture(autouse=True)
def _env_propre(monkeypatch: pytest.MonkeyPatch):
    for nom in list(os.environ):
        if nom.startswith("FILES_QUOTA"):
            monkeypatch.delenv(nom, raising=False)
    yield


# ---------------------------------------------------------------- FILES-QUOTA


class TestQuotaLuDansEnvironnement:

    def test_sans_declaration_rien_n_est_borne(self) -> None:
        """Le paquet ne borne pas ce que l'exploitant n'a pas demandé."""
        assert quota_for("user").is_unlimited

    def test_une_nature_a_son_propre_quota(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """« Par utilisateur et par ressource » : deux natures, deux quotas."""
        monkeypatch.setenv("FILES_QUOTA_USER_BYTES", "1000")
        monkeypatch.setenv("FILES_QUOTA_ARTICLE_BYTES", "50")

        assert quota_for("user").max_bytes == 1000
        assert quota_for("article").max_bytes == 50

    def test_le_quota_general_sert_de_repli(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("FILES_QUOTA_BYTES", "777")

        assert quota_for("nimporte").max_bytes == 777

    def test_le_quota_precis_l_emporte(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FILES_QUOTA_BYTES", "777")
        monkeypatch.setenv("FILES_QUOTA_USER_BYTES", "10")

        assert quota_for("user").max_bytes == 10

    def test_une_nature_a_tirets_donne_un_nom_de_variable_valide(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("FILES_QUOTA_BLOG_POST_BYTES", "42")

        assert quota_for("blog-post").max_bytes == 42

    @pytest.mark.parametrize("valeur", ["50MB", "abc", "1.5", "-1"])
    def test_une_valeur_illisible_leve(
        self, monkeypatch: pytest.MonkeyPatch, valeur: str
    ) -> None:
        """Le point qui décide de tout.

        Ignorer une faute de frappe rendrait « aucune limite », c'est à dire
        l'inverse de ce que l'exploitant a écrit, et personne ne le verrait
        avant que le disque soit plein.
        """
        monkeypatch.setenv("FILES_QUOTA_BYTES", valeur)

        with pytest.raises(FilesQuotaError):
            quota_for("user")

    def test_le_message_nomme_la_variable_et_la_correction(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("FILES_QUOTA_BYTES", "50MB")

        with pytest.raises(FilesQuotaError, match="52428800"):
            quota_for("user")

    def test_zero_n_est_pas_illimite(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`0` veut dire « rien », `None` veut dire « sans limite »."""
        monkeypatch.setenv("FILES_QUOTA_BYTES", "0")

        quota = quota_for("user")
        assert quota.max_bytes == 0
        assert not quota.is_unlimited

    def test_une_nature_vide_est_refusee(self) -> None:
        with pytest.raises(FilesQuotaError):
            quota_for("  ")


class TestQuotaApplique:

    def test_un_depot_qui_tient_passe(self, db: _FauxDb) -> None:
        record_file("a.pdf", "a.pdf", 300, owner_kind="user", owner_id=42, db=db)

        etat = check_quota("user", 42, 400, quota=Quota(max_bytes=1000), db=db)

        assert etat.used_bytes == 300

    def test_un_depot_qui_deborde_est_refuse(self, db: _FauxDb) -> None:
        record_file("a.pdf", "a.pdf", 700, owner_kind="user", owner_id=42, db=db)

        with pytest.raises(QuotaExceededError):
            check_quota("user", 42, 400, quota=Quota(max_bytes=1000), db=db)

    def test_le_refus_est_un_upload_error(self, db: _FauxDb) -> None:
        """Une application qui entoure save_upload d'un except UploadError
        traite le refus de quota sans changer une ligne."""
        assert issubclass(QuotaExceededError, UploadError)

    def test_le_message_donne_les_trois_nombres(self, db: _FauxDb) -> None:
        """Un « quota dépassé » sans chiffre n'aide ni l'utilisateur ni le support."""
        record_file("a.pdf", "a.pdf", 700, owner_kind="user", owner_id=42, db=db)

        with pytest.raises(QuotaExceededError) as leve:
            check_quota("user", 42, 400, quota=Quota(max_bytes=1000), db=db)

        message = str(leve.value)
        assert "700" in message and "1000" in message and "400" in message

    def test_le_nombre_de_fichiers_borne_aussi(self, db: _FauxDb) -> None:
        for index in range(3):
            record_file(f"{index}.pdf", "a.pdf", 1, owner_kind="user", owner_id=42, db=db)

        with pytest.raises(QuotaExceededError, match="Nombre de fichiers"):
            check_quota("user", 42, 1, quota=Quota(max_files=3), db=db)

    def test_pile_a_la_limite_passe(self, db: _FauxDb) -> None:
        """Une borne stricte au lieu d'inclusive ferait perdre un octet à tous."""
        record_file("a.pdf", "a.pdf", 600, owner_kind="user", owner_id=42, db=db)

        check_quota("user", 42, 400, quota=Quota(max_bytes=1000), db=db)

    def test_un_quota_sans_limite_ne_lit_pas_la_base(self) -> None:
        """Un déploiement sans quota ne doit pas payer une requête par upload."""

        class _Interdite(_FauxDb):
            def fetch_one(self, sql: str, params: Any) -> "dict[str, Any] | None":
                raise AssertionError("la base ne doit pas être interrogée")

        check_quota("user", 42, 10_000, quota=Quota(), db=_Interdite())

    @pytest.mark.parametrize("taille", [-1, "10", 1.5, True])
    def test_une_taille_entrante_invalide_est_refusee(
        self, db: _FauxDb, taille: Any
    ) -> None:
        with pytest.raises(FilesQuotaError):
            check_quota("user", 42, taille, quota=Quota(max_bytes=10), db=db)


class TestJauge:

    def test_le_restant_ne_devient_jamais_negatif(self, db: _FauxDb) -> None:
        """Un quota abaissé après coup laisse des propriétaires au dessus."""
        record_file("a.pdf", "a.pdf", 900, owner_kind="user", owner_id=42, db=db)

        etat = quota_usage("user", 42, quota=Quota(max_bytes=100), db=db)

        assert etat.remaining_bytes == 0
        assert etat.is_exceeded is True

    def test_sans_limite_le_restant_est_indetermine(self, db: _FauxDb) -> None:
        """Zéro voudrait dire « plus rien », ce qui est le contraire."""
        etat = quota_usage("user", 42, quota=Quota(), db=db)

        assert etat.remaining_bytes is None
        assert etat.is_exceeded is False


# ------------------------------------------------------------ FILES-SCAN-HOOK


@pytest.fixture(autouse=True)
def _sans_analyseur():
    clear_file_scanners()
    yield
    clear_file_scanners()


def _sain(data: bytes, nom: str) -> ScanVerdict:
    return ScanVerdict.clean()


def _infecte(data: bytes, nom: str) -> ScanVerdict:
    return ScanVerdict.infected("EICAR-Test-File")


class TestPriseDAnalyse:

    def test_sans_analyseur_rien_ne_change(self) -> None:
        scan_upload(b"n'importe quoi", "a.pdf")

    def test_un_analyseur_satisfait_laisse_passer(self) -> None:
        register_file_scanner(_sain)

        scan_upload(b"x", "a.pdf")

    def test_un_refus_leve(self) -> None:
        register_file_scanner(_infecte)

        with pytest.raises(UploadRejectedByScanError):
            scan_upload(b"x", "a.pdf")

    def test_le_motif_technique_ne_fuit_pas_au_deposant(self) -> None:
        """Le nom d'une signature dit ce qui est détecté, donc ce qui ne l'est pas."""
        register_file_scanner(_infecte)

        with pytest.raises(UploadRejectedByScanError) as leve:
            scan_upload(b"x", "a.pdf")

        assert "EICAR" not in str(leve.value)

    def test_une_panne_refuse_le_depot(self) -> None:
        """Le point qui justifie ce ticket.

        Un analyseur qui lève ne dit pas que le fichier est sain, il ne dit
        rien. Traiter ce silence comme un feu vert est la faute classique : le
        jour où le service antivirus tombe, tout passe, sans un signal.
        """

        def en_panne(data: bytes, nom: str) -> ScanVerdict:
            raise ConnectionError("clamd injoignable")

        register_file_scanner(en_panne)

        with pytest.raises(ScannerUnavailableError):
            scan_upload(b"x", "a.pdf")

    @pytest.mark.parametrize("retour", [True, None, "clean", 1])
    def test_un_retour_non_conforme_refuse_le_depot(self, retour: Any) -> None:
        """Un analyseur qui rend `True` serait lu comme un objet vrai."""

        def bavard(data: bytes, nom: str) -> Any:
            return retour

        register_file_scanner(bavard)

        with pytest.raises(ScannerUnavailableError):
            scan_upload(b"x", "a.pdf")

    def test_panne_et_refus_ne_se_confondent_pas(self) -> None:
        """L'un se répare, l'autre s'explique au déposant."""
        assert not issubclass(ScannerUnavailableError, UploadRejectedByScanError)
        assert not issubclass(UploadRejectedByScanError, ScannerUnavailableError)
        assert issubclass(ScannerUnavailableError, UploadError)

    def test_le_premier_refus_arrete_la_serie(self) -> None:
        appels: list[str] = []

        def premier(data: bytes, nom: str) -> ScanVerdict:
            appels.append("premier")
            return ScanVerdict.infected("x")

        def second(data: bytes, nom: str) -> ScanVerdict:
            appels.append("second")
            return ScanVerdict.clean()

        register_file_scanner(premier)
        register_file_scanner(second)

        with pytest.raises(UploadRejectedByScanError):
            scan_upload(b"x", "a.pdf")

        assert appels == ["premier"]

    def test_l_ordre_d_enregistrement_est_l_ordre_d_appel(self) -> None:
        appels: list[str] = []

        def marque(nom: str):
            def analyseur(data: bytes, fichier: str) -> ScanVerdict:
                appels.append(nom)
                return ScanVerdict.clean()

            return analyseur

        register_file_scanner(marque("a"))
        register_file_scanner(marque("b"))
        scan_upload(b"x", "a.pdf")

        assert appels == ["a", "b"]

    def test_un_double_enregistrement_ne_double_pas_le_travail(self) -> None:
        """Un module importé deux fois ne doit pas analyser deux fois."""
        register_file_scanner(_sain)
        register_file_scanner(_sain)

        assert len(registered_scanners()) == 1

    def test_on_peut_debrancher(self) -> None:
        register_file_scanner(_infecte)

        assert unregister_file_scanner(_infecte) is True
        scan_upload(b"x", "a.pdf")

    def test_la_liste_rendue_ne_donne_pas_prise(self) -> None:
        register_file_scanner(_sain)

        assert isinstance(registered_scanners(), tuple)

    def test_un_analyseur_non_appelable_est_refuse(self) -> None:
        with pytest.raises(TypeError):
            register_file_scanner("clamav")  # type: ignore[arg-type]


class TestAnalyseAvantEcriture:

    def test_save_upload_consulte_avant_d_ecrire(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Un fichier analysé après avoir touché le disque y est déjà."""
        from forge_mvc_files import manager

        monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path))
        vus: list[str] = []

        def refuse_tout(data: bytes, nom: str) -> ScanVerdict:
            vus.append(nom)
            return ScanVerdict.infected("test")

        register_file_scanner(refuse_tout)

        class _Fichier:
            filename = "note.pdf"
            content_type = "application/pdf"

            def read(self) -> bytes:
                return b"%PDF-1.4\n" + b"0" * 100

        with pytest.raises(UploadRejectedByScanError):
            manager.save_upload(_Fichier(), category="documents")

        assert vus == ["note.pdf"]
        ecrits = [p for p in tmp_path.rglob("*") if p.is_file()]
        assert ecrits == [], f"le fichier refusé a été écrit : {ecrits}"


# --------------------------------------------------------- FILES-ORPHAN-PURGE


def _vieillir(chemin: Path, jours: int) -> None:
    instant = time.time() - jours * 86400
    os.utime(chemin, (instant, instant))


@pytest.fixture
def racine(tmp_path: Path) -> Path:
    (tmp_path / "documents").mkdir()
    return tmp_path


class TestGardeFouRegistreVide:

    def test_un_registre_vide_interrompt_tout(self, racine: Path, db: _FauxDb) -> None:
        """Le scénario le plus coûteux, atteint par la commande la plus banale.

        L'inscription est explicite (ADR-094) : une application qui n'appelle
        jamais record_file a un registre vide et des fichiers bien vivants.
        Sans ce refus, la première purge effacerait tous les uploads du projet.
        """
        (racine / "documents" / "a.pdf").write_bytes(b"x")

        with pytest.raises(OrphanPurgeRefused):
            find_orphans(root=racine, db=db)

    def test_le_message_dit_quoi_verifier(self, racine: Path, db: _FauxDb) -> None:
        (racine / "documents" / "a.pdf").write_bytes(b"x")

        with pytest.raises(OrphanPurgeRefused, match="record_file"):
            find_orphans(root=racine, db=db)

    def test_un_disque_vide_ne_declenche_pas_le_refus(
        self, racine: Path, db: _FauxDb
    ) -> None:
        """Rien à effacer, donc rien à craindre."""
        rapport = find_orphans(root=racine, db=db)

        assert rapport.is_empty

    def test_le_refus_se_leve_explicitement_pour_inspecter(
        self, racine: Path, db: _FauxDb
    ) -> None:
        (racine / "documents" / "a.pdf").write_bytes(b"x")
        _vieillir(racine / "documents" / "a.pdf", 10)

        rapport = find_orphans(root=racine, db=db, allow_empty_registry=True)

        assert rapport.on_disk_only == ("documents/a.pdf",)


class TestGardeFouAge:

    def test_un_depot_en_cours_n_est_pas_orphelin(
        self, racine: Path, db: _FauxDb
    ) -> None:
        """Entre l'écriture et l'inscription il s'écoule un instant."""
        record_file("documents/inscrit.pdf", "i.pdf", 1, db=db)
        (racine / "documents" / "inscrit.pdf").write_bytes(b"x")
        (racine / "documents" / "en_cours.pdf").write_bytes(b"x")

        rapport = find_orphans(root=racine, db=db)

        assert rapport.on_disk_only == ()
        assert rapport.skipped_too_recent == 1

    def test_un_vieux_fichier_est_candidat(self, racine: Path, db: _FauxDb) -> None:
        record_file("documents/inscrit.pdf", "i.pdf", 1, db=db)
        (racine / "documents" / "inscrit.pdf").write_bytes(b"x")
        (racine / "documents" / "vieux.pdf").write_bytes(b"x")
        _vieillir(racine / "documents" / "vieux.pdf", 10)

        rapport = find_orphans(root=racine, db=db)

        assert rapport.on_disk_only == ("documents/vieux.pdf",)

    def test_le_defaut_est_d_un_jour(self) -> None:
        assert DEFAULT_MIN_AGE_SECONDS == 86400

    def test_un_age_negatif_est_refuse(self, racine: Path, db: _FauxDb) -> None:
        with pytest.raises(ValueError):
            find_orphans(root=racine, db=db, min_age_seconds=-1)


class TestDeuxSortesDOrphelins:

    def test_inscrit_sans_fichier(self, racine: Path, db: _FauxDb) -> None:
        record_file("documents/disparu.pdf", "d.pdf", 1, db=db)

        rapport = find_orphans(root=racine, db=db)

        assert rapport.in_registry_only == ("documents/disparu.pdf",)

    def test_une_ligne_sans_fichier_n_attend_pas_l_age(
        self, racine: Path, db: _FauxDb
    ) -> None:
        """Il n'y a pas de fichier dont mesurer l'âge."""
        record_file("documents/disparu.pdf", "d.pdf", 1, db=db)

        rapport = find_orphans(root=racine, db=db, min_age_seconds=10**9)

        assert rapport.in_registry_only == ("documents/disparu.pdf",)

    def test_les_compteurs_disent_les_deux_cotes(
        self, racine: Path, db: _FauxDb
    ) -> None:
        record_file("documents/a.pdf", "a.pdf", 1, db=db)
        record_file("documents/disparu.pdf", "d.pdf", 1, db=db)
        (racine / "documents" / "a.pdf").write_bytes(b"x")

        rapport = find_orphans(root=racine, db=db)

        assert rapport.files_on_disk == 1
        assert rapport.files_in_registry == 2


class TestPurge:

    def test_elle_applique_le_rapport_et_rien_d_autre(
        self, racine: Path, db: _FauxDb
    ) -> None:
        """Le rapport est le contrat : un fichier déposé entre les deux gestes
        ne doit pas entrer dans la fournée."""
        record_file("documents/garde.pdf", "g.pdf", 1, db=db)
        record_file("documents/disparu.pdf", "d.pdf", 1, db=db)
        (racine / "documents" / "garde.pdf").write_bytes(b"x")
        (racine / "documents" / "orphelin.pdf").write_bytes(b"x")
        _vieillir(racine / "documents" / "orphelin.pdf", 10)

        rapport = find_orphans(root=racine, db=db)
        (racine / "documents" / "arrive_apres.pdf").write_bytes(b"x")
        _vieillir(racine / "documents" / "arrive_apres.pdf", 10)

        resultat = purge_orphans(rapport, root=racine, db=db)

        assert resultat.deleted_files == ("documents/orphelin.pdf",)
        assert resultat.forgotten_records == ("documents/disparu.pdf",)
        assert (racine / "documents" / "arrive_apres.pdf").exists()
        assert (racine / "documents" / "garde.pdf").exists()

    def test_un_echec_n_interrompt_pas_la_serie(
        self, racine: Path, db: _FauxDb, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un fichier verrouillé ne doit pas empêcher de nettoyer les suivants."""
        from forge_mvc_files import orphans as module
        from forge_mvc_files.orphans import OrphanReport

        def refuse(chemin: str, *, root: Any) -> bool:
            if "bloque" in chemin:
                raise OSError("verrouillé")
            return True

        monkeypatch.setattr(module.storage, "delete_file", refuse)
        rapport = OrphanReport(
            on_disk_only=("documents/bloque.pdf", "documents/suivant.pdf"),
            in_registry_only=(),
            files_on_disk=2,
            files_in_registry=1,
            skipped_too_recent=0,
        )

        resultat = purge_orphans(rapport, root=racine, db=db)

        assert resultat.deleted_files == ("documents/suivant.pdf",)
        assert len(resultat.failed) == 1

    def test_on_peut_ne_purger_qu_un_cote(self, racine: Path, db: _FauxDb) -> None:
        record_file("documents/disparu.pdf", "d.pdf", 1, db=db)
        record_file("documents/garde.pdf", "g.pdf", 1, db=db)
        (racine / "documents" / "garde.pdf").write_bytes(b"x")
        (racine / "documents" / "orphelin.pdf").write_bytes(b"x")
        _vieillir(racine / "documents" / "orphelin.pdf", 10)

        rapport = find_orphans(root=racine, db=db)
        resultat = purge_orphans(rapport, root=racine, db=db, delete_files=False)

        assert resultat.deleted_files == ()
        assert (racine / "documents" / "orphelin.pdf").exists()
        assert resultat.forgotten_records == ("documents/disparu.pdf",)


class TestCommandeCli:

    def test_elle_affiche_sans_supprimer_par_defaut(self) -> None:
        from forge_mvc_files.cli_orphans import parse_options

        assert parse_options([]).delete is False

    def test_une_option_inconnue_est_une_erreur(self) -> None:
        """Ignorer `--dlete` ferait afficher là où l'exploitant croyait supprimer."""
        from forge_mvc_files.cli_orphans import parse_options

        options = parse_options(["--dlete"])

        assert options.error is not None

    def test_le_registre_vide_est_refuse_avec_delete(self) -> None:
        """Les deux garde-fous ensemble effaceraient tout."""
        from forge_mvc_files.cli_orphans import parse_options

        options = parse_options(["--delete", "--allow-empty-registry"])

        assert options.error is not None

    def test_le_registre_vide_seul_reste_permis(self) -> None:
        from forge_mvc_files.cli_orphans import parse_options

        assert parse_options(["--allow-empty-registry"]).error is None

    @pytest.mark.parametrize("argv", [["--min-age", "60"], ["--min-age=60"]])
    def test_les_deux_ecritures_d_option_sont_lues(self, argv: list[str]) -> None:
        from forge_mvc_files.cli_orphans import parse_options

        assert parse_options(argv).min_age == 60

    def test_une_valeur_manquante_est_une_erreur(self) -> None:
        from forge_mvc_files.cli_orphans import parse_options

        assert parse_options(["--min-age"]).error is not None

    def test_le_rapport_dit_ce_qui_a_ete_ecarte(self) -> None:
        """Sans quoi une absence de la liste se lit comme « jugé sain »."""
        from forge_mvc_files.cli_orphans import render_report
        from forge_mvc_files.orphans import OrphanReport

        texte = render_report(
            OrphanReport(
                on_disk_only=(),
                in_registry_only=(),
                files_on_disk=5,
                files_in_registry=5,
                skipped_too_recent=3,
            )
        )

        assert "3 fichiers trop récents" in texte

    def test_une_longue_liste_est_tronquee(self) -> None:
        from forge_mvc_files.cli_orphans import APERCU, render_report
        from forge_mvc_files.orphans import OrphanReport

        texte = render_report(
            OrphanReport(
                on_disk_only=tuple(f"documents/{i}.pdf" for i in range(50)),
                in_registry_only=(),
                files_on_disk=50,
                files_in_registry=1,
                skipped_too_recent=0,
            )
        )

        assert f"et {50 - APERCU} autres" in texte
