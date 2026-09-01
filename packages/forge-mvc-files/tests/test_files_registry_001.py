"""FILES-METADATA-TABLE-001 : le registre des fichiers écrits (ADR-094).

`forge-mvc-files` écrivait des fichiers sans garder trace de ce qu'il avait
écrit. Sans registre, aucun quota n'est calculable, aucun orphelin n'est
repérable, et le nom d'origine ne survit pas au mode UUID, qui l'efface du
chemin par sécurité.

Le registre porte ce que le **stockage** sait, jamais une notion métier.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_files")

from forge_mvc_files.registry import (  # noqa: E402
    FileRegistryError,
    forget_file,
    get_file_record,
    list_all_paths,
    list_paths_for_owner,
    owner_file_count,
    owner_usage_bytes,
    record_file,
)
from forge_mvc_files.tables import FILES, FILES_TABLE_NAME  # noqa: E402


class _FauxDb:
    """Base en mémoire, fidèle aux colonnes de la table."""

    def __init__(self) -> None:
        self.lignes: list[dict[str, Any]] = []
        self.sql: list[str] = []

    def execute(self, sql: str, params: Any = ()) -> int:
        self.sql.append(sql)
        if sql.strip().upper().startswith("INSERT"):
            chemin = params[0]
            if any(l["path"] == chemin for l in self.lignes):
                raise RuntimeError("contrainte d'unicité sur path")
            self.lignes.append({
                "path": params[0], "original_name": params[1], "mime_type": params[2],
                "size_bytes": params[3], "owner_kind": params[4], "owner_id": params[5],
                "created_at": "2026-09-01 00:00:00",
            })
            return 1
        if sql.strip().upper().startswith("DELETE"):
            avant = len(self.lignes)
            self.lignes = [l for l in self.lignes if l["path"] != params[0]]
            return avant - len(self.lignes)
        return 0

    def fetch_one(self, sql: str, params: Any = ()) -> "dict[str, Any] | None":
        self.sql.append(sql)
        haut = sql.upper()
        if "SUM(" in haut:
            total = sum(
                l["size_bytes"] for l in self.lignes
                if l["owner_kind"] == params[0] and l["owner_id"] == params[1]
            )
            return {"total": total}
        if "COUNT(" in haut:
            total = sum(
                1 for l in self.lignes
                if l["owner_kind"] == params[0] and l["owner_id"] == params[1]
            )
            return {"total": total}
        return next((l for l in self.lignes if l["path"] == params[0]), None)

    def fetch_all(self, sql: str, params: Any = ()) -> "list[dict[str, Any]]":
        self.sql.append(sql)
        if "WHERE owner_kind" in sql:
            vises = [
                l for l in self.lignes
                if l["owner_kind"] == params[0] and l["owner_id"] == params[1]
            ]
        else:
            vises = list(self.lignes)
        return [{"path": l["path"]} for l in sorted(vises, key=lambda l: l["path"])]


@pytest.fixture
def db() -> _FauxDb:
    return _FauxDb()


class TestInscription:
    def test_un_fichier_inscrit_est_retrouve(self, db: _FauxDb) -> None:
        record_file("2026/09/a1b2.pdf", "Rapport annuel.pdf", 1024,
                    mime_type="application/pdf", db=db)

        ligne = get_file_record("2026/09/a1b2.pdf", db=db)
        assert ligne is not None
        assert ligne["original_name"] == "Rapport annuel.pdf"
        assert ligne["size_bytes"] == 1024

    def test_le_nom_d_origine_survit_au_mode_uuid(self, db: _FauxDb) -> None:
        """Le chemin UUID efface le nom : c'est la raison d'être de la colonne."""
        record_file("a1b2c3d4.pdf", "Facture cliente 2026.pdf", 512, db=db)

        ligne = get_file_record("a1b2c3d4.pdf", db=db)
        assert ligne is not None
        assert ligne["original_name"] == "Facture cliente 2026.pdf"

    def test_un_chemin_absent_rend_none(self, db: _FauxDb) -> None:
        assert get_file_record("jamais/vu.pdf", db=db) is None

    @pytest.mark.parametrize(
        ("path", "nom", "taille"),
        [("", "a.pdf", 1), ("   ", "a.pdf", 1), ("a.pdf", "", 1),
         ("a.pdf", "   ", 1), ("a.pdf", "a.pdf", -1)],
    )
    def test_les_entrees_invalides_sont_refusees(
        self, path: str, nom: str, taille: int, db: _FauxDb
    ) -> None:
        with pytest.raises(FileRegistryError):
            record_file(path, nom, taille, db=db)

    def test_une_taille_qui_n_est_pas_un_entier_est_refusee(self, db: _FauxDb) -> None:
        with pytest.raises(FileRegistryError):
            record_file("a.pdf", "a.pdf", "1024", db=db)  # type: ignore[arg-type]


class TestProprietaire:
    def test_les_deux_colonnes_vont_de_pair(self, db: _FauxDb) -> None:
        """Un identifiant sans nature ne désigne personne, et l'inverse non plus."""
        with pytest.raises(FileRegistryError, match="vont de pair"):
            record_file("a.pdf", "a.pdf", 1, owner_id=7, db=db)
        with pytest.raises(FileRegistryError, match="vont de pair"):
            record_file("a.pdf", "a.pdf", 1, owner_kind="user", db=db)

    def test_un_fichier_sans_proprietaire_est_permis(self, db: _FauxDb) -> None:
        record_file("a.pdf", "a.pdf", 1, db=db)
        ligne = get_file_record("a.pdf", db=db)
        assert ligne is not None
        assert ligne["owner_kind"] is None

    def test_l_identifiant_est_rendu_en_texte(self, db: _FauxDb) -> None:
        """Entier ou chaîne, la colonne est la même sur les quatre backends."""
        record_file("a.pdf", "a.pdf", 1, owner_kind="user", owner_id=7, db=db)
        ligne = get_file_record("a.pdf", db=db)
        assert ligne is not None
        assert ligne["owner_id"] == "7"


class TestQuota:
    def test_la_somme_des_tailles_est_le_socle_du_quota(self, db: _FauxDb) -> None:
        for n, taille in enumerate([100, 250, 650]):
            record_file(f"u7/{n}.pdf", "x.pdf", taille,
                        owner_kind="user", owner_id=7, db=db)

        assert owner_usage_bytes("user", 7, db=db) == 1000
        assert owner_file_count("user", 7, db=db) == 3

    def test_les_fichiers_des_autres_ne_comptent_pas(self, db: _FauxDb) -> None:
        record_file("u7/a.pdf", "a.pdf", 100, owner_kind="user", owner_id=7, db=db)
        record_file("u9/b.pdf", "b.pdf", 900, owner_kind="user", owner_id=9, db=db)

        assert owner_usage_bytes("user", 7, db=db) == 100

    def test_un_proprietaire_sans_fichier_consomme_zero(self, db: _FauxDb) -> None:
        assert owner_usage_bytes("user", 404, db=db) == 0
        assert owner_file_count("user", 404, db=db) == 0

    def test_les_fichiers_sans_proprietaire_ne_comptent_pour_personne(
        self, db: _FauxDb
    ) -> None:
        record_file("libre.pdf", "libre.pdf", 5000, db=db)
        assert owner_usage_bytes("user", 7, db=db) == 0


class TestPurgeDesOrphelins:
    def test_tous_les_chemins_sont_listables(self, db: _FauxDb) -> None:
        """Le rapprochement avec le disque appartient à l'appelant."""
        record_file("b.pdf", "b.pdf", 1, db=db)
        record_file("a.pdf", "a.pdf", 1, db=db)

        assert list_all_paths(db=db) == ["a.pdf", "b.pdf"]

    def test_les_chemins_d_un_proprietaire_sont_listables(self, db: _FauxDb) -> None:
        record_file("u7/a.pdf", "a.pdf", 1, owner_kind="user", owner_id=7, db=db)
        record_file("u9/b.pdf", "b.pdf", 1, owner_kind="user", owner_id=9, db=db)

        assert list_paths_for_owner("user", 7, db=db) == ["u7/a.pdf"]

    def test_oublier_un_fichier_le_retire_du_quota(self, db: _FauxDb) -> None:
        record_file("a.pdf", "a.pdf", 500, owner_kind="user", owner_id=7, db=db)

        assert forget_file("a.pdf", db=db) is True
        assert owner_usage_bytes("user", 7, db=db) == 0
        assert get_file_record("a.pdf", db=db) is None

    def test_oublier_un_inconnu_ne_leve_pas(self, db: _FauxDb) -> None:
        assert forget_file("jamais/vu.pdf", db=db) is False

    def test_le_registre_ne_touche_jamais_au_disque(self, tmp_path, db: _FauxDb) -> None:
        """L'appelant décide de l'ordre entre disque et registre."""
        fichier = tmp_path / "a.pdf"
        fichier.write_bytes(b"contenu")
        record_file("a.pdf", "a.pdf", 7, db=db)

        forget_file("a.pdf", db=db)

        assert fichier.exists(), "le registre ne doit rien supprimer sur disque"


class TestSchema:
    def test_le_chemin_est_unique(self) -> None:
        """Deux lignes pour un même fichier rendraient tout quota faux."""
        colonne = next(c for c in FILES.columns if c.name == "path")
        assert colonne.unique

    def test_le_couple_proprietaire_est_indexe(self) -> None:
        """Le quota compte par propriétaire."""
        assert any(i.column_list == "owner_kind, owner_id" for i in FILES.indexes)

    def test_la_table_ne_porte_aucune_notion_metier(self) -> None:
        """Rôle, position et texte alternatif restent à `media` (ADR-094)."""
        noms = {c.name for c in FILES.columns}
        assert not (noms & {"role", "position", "alt_text", "entity_name", "entity_id"})

    def test_le_nom_de_table_est_prefixe(self) -> None:
        """`forge_files` et non `files` : le nom nu heurterait une table applicative."""
        assert FILES_TABLE_NAME == "forge_files"
        assert FILES.name == FILES_TABLE_NAME


class TestSansBase:
    def test_le_paquet_reste_importable_sans_backend(self) -> None:
        """Le registre est explicite : qui ne veut que des primitives n'a pas de base."""
        import forge_mvc_files

        assert hasattr(forge_mvc_files, "save_upload")
        assert hasattr(forge_mvc_files, "record_file")

    def test_ecrire_un_fichier_n_inscrit_rien(self, db: _FauxDb) -> None:
        """`save_upload` ne touche pas au registre (principe 3)."""
        from pathlib import Path as _P

        source = _P(__import__("forge_mvc_files.manager", fromlist=["x"]).__file__)
        texte = source.read_text(encoding="utf-8")
        assert "record_file" not in texte, (
            "save_upload ne doit pas inscrire de soi même : l'appel reste explicite"
        )
